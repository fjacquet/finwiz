"""@stage decorator: timeout, retry, exception capture, ledger record."""

from __future__ import annotations

import asyncio
import inspect
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from functools import wraps
from typing import Any, ParamSpec, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from finwiz.analysis.stages._ledger import RunLedger
from finwiz.schemas.run_ledger import RunLedgerEntry
from finwiz.schemas.stage_contract import (
    StageName,
    StageOutcome,
    StageProvenance,
    StageResult,
)

# httpcore is an httpx transitive — guard import to keep optional surface small.
try:  # pragma: no cover - import guard
    import httpcore  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover
    httpcore = None  # type: ignore[assignment]


@dataclass
class StageContext:
    """Per-holding context threaded through every stage call."""

    ticker: str
    run_id: str
    ledger: RunLedger
    extras: dict[str, Any] = field(default_factory=dict)


P = ParamSpec("P")
T = TypeVar("T", bound=BaseModel)

_TRANSIENT_EXC: tuple[type[BaseException], ...]
_TRANSIENT_EXC = (OSError, asyncio.TimeoutError)
_TRANSIENT_HTTP_TYPES: tuple[type[BaseException], ...] = (httpx.HTTPStatusError,)
if httpcore is not None:  # pragma: no branch
    _TRANSIENT_HTTP_TYPES = (*_TRANSIENT_HTTP_TYPES, httpcore.RemoteProtocolError)


def _is_transient(exc: BaseException) -> bool:
    if isinstance(exc, (ValidationError, AssertionError)):
        return False
    if isinstance(exc, _TRANSIENT_EXC):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code >= 500
    if any(isinstance(exc, t) for t in _TRANSIENT_HTTP_TYPES):
        return True
    return False


def stage(
    *,
    name: StageName,
    timeout_s: float,
    retries: int,
    allow_degrade: bool = False,
) -> Callable[[Callable[P, T | StageResult[T]]], Callable[P, StageResult[T]]]:
    """Decorate a stage function with timeout, retry, capture, and ledger record.

    Stage bodies must be idempotent: retries re-execute the full body.

    Note: timeout_s is enforced for async stages via asyncio.wait_for.  Sync stages should
    be CPU-bound work that completes synchronously; the per-holding wait_for in the
    orchestrator provides the outer cap for sync stages.

    Raises:
        ValueError at decoration time if allow_degrade=True for a non-qualify stage.
    """
    if allow_degrade and name != "qualify":
        raise ValueError(f"allow_degrade=True is only valid for stage 'qualify', got '{name}'")

    def deco(fn: Callable[P, T | StageResult[T]]) -> Callable[P, StageResult[T]]:
        if inspect.iscoroutinefunction(fn):

            @wraps(fn)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> StageResult[T]:  # type: ignore[return-value]
                ctx = _extract_context(args)
                started = datetime.now(UTC)
                t0 = time.perf_counter()
                attempt = 0
                while attempt <= retries:
                    try:
                        coro = fn(*args, **kwargs)
                        raw = await asyncio.wait_for(coro, timeout=timeout_s)
                        result = _coerce_to_stage_result(raw, name=name, t0=t0, attempt=attempt)
                        if not allow_degrade and result.provenance.outcome == StageOutcome.DEGRADED:
                            raise ValueError(f"stage '{name}' returned DEGRADED but allow_degrade=False")
                        _record(ctx, result, started, name)
                        return result
                    except (ValidationError, AssertionError):
                        raise
                    except BaseException as exc:
                        if not _is_transient(exc) or attempt == retries:
                            result = _failed_result(name, t0, attempt, exc)
                            _record(ctx, result, started, name)
                            return result
                        attempt += 1
                raise RuntimeError("unreachable")  # pragma: no cover

            return async_wrapper  # type: ignore[return-value]

        @wraps(fn)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> StageResult[T]:
            # timeout_s is NOT enforced here — threading-based interrupts are unsafe (GIL,
            # signal restrictions on non-main threads, thread leaks on cancel).  Sync stages
            # must be CPU-bound and short; the per-holding asyncio.wait_for in the orchestrator
            # is the effective cap.
            ctx = _extract_context(args)
            started = datetime.now(UTC)
            t0 = time.perf_counter()
            attempt = 0
            last_exc: BaseException | None = None

            while attempt <= retries:
                try:
                    raw = fn(*args, **kwargs)
                    result = _coerce_to_stage_result(raw, name=name, t0=t0, attempt=attempt)
                    if not allow_degrade and result.provenance.outcome == StageOutcome.DEGRADED:
                        raise ValueError(f"stage '{name}' returned DEGRADED but allow_degrade=False")
                    _record(ctx, result, started, name)
                    return result
                except (ValidationError, AssertionError):
                    raise
                except BaseException as exc:
                    last_exc = exc
                    if not _is_transient(exc) or attempt == retries:
                        result = _failed_result(name, t0, attempt, exc)
                        _record(ctx, result, started, name)
                        return result
                    attempt += 1

            # unreachable: loop always returns
            assert last_exc is not None
            raise last_exc  # pragma: no cover

        return sync_wrapper

    return deco


def _extract_context(args: tuple[Any, ...]) -> StageContext:
    for a in args:
        if isinstance(a, StageContext):
            return a
    raise TypeError("stage function must receive a StageContext as positional arg")


def _coerce_to_stage_result(raw: Any, *, name: StageName, t0: float, attempt: int) -> StageResult[Any]:
    if isinstance(raw, StageResult):
        # Patch retries_used and duration_ms if not set by the body.
        prov = raw.provenance.model_copy(
            update={
                "retries_used": max(raw.provenance.retries_used, attempt),
                "duration_ms": raw.provenance.duration_ms or _ms_since(t0),
            }
        )
        return StageResult(payload=raw.payload, provenance=prov)
    return StageResult(
        payload=raw,
        provenance=StageProvenance(
            stage=name,
            outcome=StageOutcome.OK,
            duration_ms=_ms_since(t0),
            retries_used=attempt,
        ),
    )


def _failed_result(name: StageName, t0: float, attempt: int, exc: BaseException) -> StageResult[Any]:
    return StageResult(
        payload=None,
        provenance=StageProvenance(
            stage=name,
            outcome=StageOutcome.FAILED,
            reason=f"{type(exc).__name__}: {exc}",
            duration_ms=_ms_since(t0),
            retries_used=attempt,
        ),
    )


def _record(
    ctx: StageContext,
    result: StageResult[Any],
    started: datetime,
    name: StageName,
) -> None:
    ctx.ledger.record(
        RunLedgerEntry(
            run_id=ctx.run_id,
            ticker=ctx.ticker,
            started_at=started,
            finished_at=datetime.now(UTC),
            stage=name,
            outcome=result.provenance.outcome,
            reason=result.provenance.reason,
            fallback_used=result.provenance.fallback_used,
            retries_used=result.provenance.retries_used,
        )
    )


def _ms_since(t0: float) -> int:
    return int((time.perf_counter() - t0) * 1000)
