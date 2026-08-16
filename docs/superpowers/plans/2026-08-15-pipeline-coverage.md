# Pipeline Coverage & Discovery Integrity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make a `crewai flow kickoff` run analyze every holding it can, refuse by name the ones it genuinely cannot, and stop discovery from either fabricating opportunities or searching a universe too small to contain any.

**Architecture:** Three independent defect clusters in the deep-analysis pipeline and the discovery pipeline. Cluster 1 (fact_pack) is a resilience gap: one un-retried HTTP call per holding, no backoff, and a `RuntimeError` the retry layer treats as non-transient. Cluster 2 (volatility) is an ordering bug: the critical-field gate runs before the fallback that would fill the field. Cluster 3 (discovery) is a correctness hazard: a hardcoded mock fallback that injects invented A+ tickers, plus a universe of 11 candidates and a factor formula that cannot reach the actionability floor.

**Tech Stack:** Python 3.13, Pydantic v2, httpx (async), pandas, empyrical, pytest + pytest-mock + pytest-socket, uv, ruff.

**Spec:** `docs/superpowers/specs/2026-08-15-report-rethink-design.md` (§4 — Coverage fixes). This plan implements §4 only. §1, §2, §3, §5 (the report rebuild) are Plan B, written after this plan executes.

## Global Constraints

- **Line length 180** — `pyproject.toml:61` `[tool.ruff] line-length = 180`.
- **New files ≤300 lines** — enforced by `scripts/check_new_file_size.py:15` (`MAX_LINES = 300`) via `make check-file-size`.
- **`unittest.mock` is BANNED.** Use pytest-mock's `mocker` only. Enforced by ruff `flake8-tidy-imports` (`pyproject.toml:141-147`) and `make check-unittest-mock` (`Makefile:147-157`).
- **No network in unit tests.** `tests/conftest.py:56-73` installs an autouse pytest-socket guard allowing only `127.0.0.1`, `::1`, `localhost`. Mock the seam; never widen the allow-list.
- **`json.dumps` always with `default=str`.**
- **All Pydantic models live in `src/finwiz/schemas/`**, not in domain folders.
- **AI Minimalism** — every change in this plan is deterministic Python. No task here adds an LLM call.
- **Test command:** `make test` runs `uv run pytest --cov --cov-report=xml --cov-report=term-missing -m "not integration" -q -n auto --dist=loadscope` (`Makefile:75-76`).
- **Target Python:** 3.13 (`pyproject.toml:61` `target-version = "py313"`).

## Known-Broken Ground (read before starting)

Verified during planning. Do not be surprised by these; do not fix them in this plan unless a task says so.

- `tests/conftest.py` lines 306-707 (~57% of the file) are **dead** — they import `finwiz.flows.hybrid_analysis_flow`, which does not exist (`ModuleNotFoundError`). Two fixtures also raise `ImportError` on names that no longer exist (`DataQualityMetrics` from `finwiz.schemas.integration.models` at :581; `InvestmentThesis`/`RiskAssessment` from `finwiz.schemas.hybrid_analysis.qualitative` at :617-622). No test requests them. **Do not build on any fixture defined after line 306.** Usable fixtures are lines 119-303.
- `tests/conftest_unittest_blocker.py` is **never wired in** — no import, no `-p` flag. Project CLAUDE.md claims it blocks `unittest.mock` at runtime; it does not. Enforcement is ruff + the Makefile grep only.
- **No snapshot-testing library is installed** (no syrupy, pytest-snapshot, approvaltests — confirmed absent from both `pyproject.toml` and `uv.lock`). Plan B will need one; this plan does not.
- There is **no `fail_under`** anywhere in `pyproject.toml` — `[tool.coverage.run]` at :401-426 has no `[tool.coverage.report]` section. The "65% minimum" in CLAUDE.md is not enforced by config.
- **`logs/finwiz_error.log` accumulates across runs.** Only 40 of its 226 lines are from the 2026-08-15 run. Always filter by date (`grep "2026-08-15" logs/finwiz_error.log`) before attributing an error to the current run. The spec's §4.5 list was written without this filter and over-attributes two error classes — see Task 15.

**Errors confirmed present in the 2026-08-15 run** (the only ones this plan treats as live):

| Count | Error |
|---|---|
| 3 | `HTTP Error 404` — `Quote not found for symbol: XTSLA` |
| 2+2 | `index N is out of bounds for axis 0 with size N` — `quantitative_comprehensive_analyzer.py`, `backtesting.py` |
| 1 | `list index out of range` — `quantitative_comprehensive_analyzer.py` |
| 2 | `Error saving cache metadata: dictionary changed size during iteration` — `data_processors.py` |
| 2 each | `possibly delisted; no price data found` — XTSLA, UNI-USD, S-USD, POL-USD, IMX-USD, GRT-USD, COMP-USD |

**Errors from the 2026-07-15 run only — do NOT chase these:** `cannot convert float NaN to integer`, `1 validation error for _QualitativeInsightsRaw` (doubled opening brace: `'{\n{"sec_insights": …'`), `JSON repair failed: Expecting property name enclosed in double quotes`. They did not occur on 2026-08-15. The doubled-brace repair rule is already tracked as a separate follow-up.

---

## File Structure

**New files**

| Path | Responsibility |
|---|---|
| `src/finwiz/infrastructure/resilience/perplexity_retry.py` | Async retry-with-backoff wrapper around the vendored `perplexity_structured`, plus a process-wide concurrency semaphore. Shared by fact_pack and strategic research. |
| `tests/unit/infrastructure/test_perplexity_retry.py` | Unit tests for the retry wrapper. |
| `tests/unit/analysis/test_fact_pack_stage.py` | Unit tests for the fact_pack stage's cache/fetch/refusal behavior. |
| `tests/unit/scoring/test_volatility_fallback.py` | Unit tests for volatility derivation and scale normalization. |
| `tests/unit/discovery/test_universe_provider_selection.py` | Unit tests for seed selection, hygiene, and the universe floor. |

**Modified files**

| Path | Change |
|---|---|
| `src/finwiz/analysis/fact_pack_research.py:183-189` | Route the Perplexity call through the retry wrapper. |
| `src/finwiz/analysis/stages/fact_pack.py:74` | Raise a transient-classified error so `@stage(retries=1)` is reachable. |
| `src/finwiz/analysis/stages/_resilience.py:53-62` | Teach `_is_transient` about the new error type. |
| `src/finwiz/schemas/hybrid_analysis/fact_pack.py:45-53` | Widen the stale window so an old cache can still serve a rate-limited run. |
| `src/finwiz/scoring/technical_fallback.py` | Add a volatility branch using the existing `calculate_volatility`. |
| `src/finwiz/scoring/deep_analysis_scorer.py:96-100` | Run the fallback before the critical-field gate. |
| `src/finwiz/config/critical_fields_config.py:162` | Normalize percent-scaled volatility instead of rejecting it. |
| `src/finwiz/discovery/universe_provider.py:71,74` | Fix the operator-precedence bug and the `except (ValueError, Exception)` catch-all; apply ticker hygiene; enforce a universe floor. |
| `src/finwiz/scoring/etf_analyzer.py`, `stock_analyzer.py`, `crypto_analyzer.py` | Delete the fabricated legacy fallback. |
| `src/finwiz/tools/alternative_finder_tool.py:179`, `src/finwiz/orchestrators/extraction/engine.py:169,192`, `src/finwiz/infrastructure/json/to_html_converter.py:38-39` | Point at `consolidated_discovery.json`; retire the `discovery_latest.json` name. |
| `src/finwiz/scoring/discovery/pipeline.py:105,121` | Persist the pre-filter scored list before filtering. |

---

## Task 1: Perplexity retry wrapper

The vendored client at `.venv/.../crewai_custom_tools/tools/web/perplexity_structured.py:148-176` catches every failure and returns `None` — a 429, a timeout, a missing API key and an unparseable body are indistinguishable to the caller. It issues exactly one `client.post` with no retry, no backoff, no jitter.

Because status codes are not observable through that surface, this wrapper retries **by outcome** (`None`), not by status. It fails fast on a missing API key so a misconfiguration does not burn four attempts.

**Files:**

- Create: `src/finwiz/infrastructure/resilience/perplexity_retry.py`
- Test: `tests/unit/infrastructure/test_perplexity_retry.py`

**Interfaces:**

- Consumes: `perplexity_structured` from `crewai_custom_tools` (async, keyword-only: `prompt`, `schema`, `system`, `model`, `search_recency_filter`, `timeout`, `api_key`).
- Produces: `async def perplexity_with_retry(*, prompt: str, schema: type[T], system: str, search_recency_filter: str | None = "month", timeout: float = 15.0, max_attempts: int = 4, base_delay: float = 1.0) -> T | None` and `PERPLEXITY_CONCURRENCY` / `get_perplexity_semaphore() -> asyncio.Semaphore`. Tasks 2 and 12 consume both.

- [ ] **Step 1: Write the failing test**

Create `tests/unit/infrastructure/test_perplexity_retry.py`:

```python
"""Tests for the Perplexity retry wrapper."""

import asyncio

import pytest
from pydantic import BaseModel

from finwiz.infrastructure.resilience.perplexity_retry import (
    get_perplexity_semaphore,
    perplexity_with_retry,
)


class _Payload(BaseModel):
    value: str


@pytest.mark.asyncio
async def test_returns_payload_on_first_success(mocker):
    inner = mocker.patch(
        "finwiz.infrastructure.resilience.perplexity_retry.perplexity_structured",
        new=mocker.AsyncMock(return_value=_Payload(value="ok")),
    )
    sleep = mocker.patch("finwiz.infrastructure.resilience.perplexity_retry.asyncio.sleep", new=mocker.AsyncMock())

    result = await perplexity_with_retry(prompt="p", schema=_Payload, system="s")

    assert result == _Payload(value="ok")
    assert inner.await_count == 1
    assert sleep.await_count == 0


@pytest.mark.asyncio
async def test_retries_until_success_and_backs_off(mocker):
    inner = mocker.patch(
        "finwiz.infrastructure.resilience.perplexity_retry.perplexity_structured",
        new=mocker.AsyncMock(side_effect=[None, None, _Payload(value="late")]),
    )
    sleep = mocker.patch("finwiz.infrastructure.resilience.perplexity_retry.asyncio.sleep", new=mocker.AsyncMock())
    mocker.patch("finwiz.infrastructure.resilience.perplexity_retry.random.uniform", return_value=0.0)

    result = await perplexity_with_retry(prompt="p", schema=_Payload, system="s", base_delay=2.0)

    assert result == _Payload(value="late")
    assert inner.await_count == 3
    assert [c.args[0] for c in sleep.await_args_list] == [2.0, 4.0]


@pytest.mark.asyncio
async def test_gives_up_after_max_attempts(mocker):
    inner = mocker.patch(
        "finwiz.infrastructure.resilience.perplexity_retry.perplexity_structured",
        new=mocker.AsyncMock(return_value=None),
    )
    mocker.patch("finwiz.infrastructure.resilience.perplexity_retry.asyncio.sleep", new=mocker.AsyncMock())

    result = await perplexity_with_retry(prompt="p", schema=_Payload, system="s", max_attempts=3)

    assert result is None
    assert inner.await_count == 3


@pytest.mark.asyncio
async def test_missing_api_key_fails_fast_without_retrying(mocker, monkeypatch):
    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
    monkeypatch.delenv("PPLX_API_KEY", raising=False)
    inner = mocker.patch(
        "finwiz.infrastructure.resilience.perplexity_retry.perplexity_structured",
        new=mocker.AsyncMock(return_value=None),
    )

    result = await perplexity_with_retry(prompt="p", schema=_Payload, system="s")

    assert result is None
    assert inner.await_count == 0


def test_semaphore_is_a_process_singleton():
    assert get_perplexity_semaphore() is get_perplexity_semaphore()
    assert isinstance(get_perplexity_semaphore(), asyncio.Semaphore)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/infrastructure/test_perplexity_retry.py -v -p no:randomly`
Expected: FAIL — `ModuleNotFoundError: No module named 'finwiz.infrastructure.resilience.perplexity_retry'`

- [ ] **Step 3: Write minimal implementation**

Create `src/finwiz/infrastructure/resilience/perplexity_retry.py`:

```python
"""Retry-with-backoff and concurrency control for Perplexity structured calls.

The vendored ``perplexity_structured`` client swallows every failure and returns
``None`` (see ``crewai_custom_tools/tools/web/perplexity_structured.py``), so a
429, a timeout and an unparseable body are indistinguishable here. This wrapper
therefore retries **by outcome**, not by status code, with exponential backoff
and jitter.

A missing API key is the one failure we can detect up front, so it fails fast
rather than burning the whole attempt budget on a misconfiguration.
"""

from __future__ import annotations

import asyncio
import os
import random
from typing import TypeVar

from crewai_custom_tools import perplexity_structured
from pydantic import BaseModel

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)

# Perplexity rate-limits aggressively; a full portfolio fans out far wider than
# the account allows. This caps in-flight requests process-wide.
PERPLEXITY_CONCURRENCY = int(os.getenv("PERPLEXITY_CONCURRENCY", "4"))

_semaphore: asyncio.Semaphore | None = None


def get_perplexity_semaphore() -> asyncio.Semaphore:
    """Return the process-wide Perplexity concurrency semaphore."""
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(PERPLEXITY_CONCURRENCY)
    return _semaphore


def _has_api_key() -> bool:
    return bool(os.getenv("PERPLEXITY_API_KEY") or os.getenv("PPLX_API_KEY"))


async def perplexity_with_retry(
    *,
    prompt: str,
    schema: type[T],
    system: str,
    search_recency_filter: str | None = "month",
    timeout: float = 15.0,
    max_attempts: int = 4,
    base_delay: float = 1.0,
) -> T | None:
    """Call ``perplexity_structured`` with bounded retries and exponential backoff.

    Args:
        prompt: User prompt forwarded to Perplexity.
        schema: Pydantic model the response must validate against.
        system: System prompt forwarded to Perplexity.
        search_recency_filter: Perplexity recency window, or None to omit.
        timeout: Per-attempt httpx timeout in seconds.
        max_attempts: Total attempts, including the first. Must be >= 1.
        base_delay: Seconds before the second attempt; doubles each retry.

    Returns:
        The validated model, or None when every attempt failed.
    """
    if not _has_api_key():
        logger.warning(f"Perplexity call for {schema.__name__} skipped: no PERPLEXITY_API_KEY/PPLX_API_KEY configured")
        return None

    delay = base_delay
    for attempt in range(1, max_attempts + 1):
        async with get_perplexity_semaphore():
            result = await perplexity_structured(
                prompt=prompt,
                schema=schema,
                system=system,
                search_recency_filter=search_recency_filter,
                timeout=timeout,
            )
        if result is not None:
            if attempt > 1:
                logger.info(f"Perplexity call for {schema.__name__} succeeded on attempt {attempt}/{max_attempts}")
            return result

        if attempt < max_attempts:
            jittered = delay + random.uniform(0.0, delay * 0.25)
            logger.warning(f"Perplexity call for {schema.__name__} returned no result (attempt {attempt}/{max_attempts}); retrying in {jittered:.1f}s")
            await asyncio.sleep(jittered)
            delay *= 2.0

    logger.warning(f"Perplexity call for {schema.__name__} exhausted {max_attempts} attempts")
    return None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/infrastructure/test_perplexity_retry.py -v -p no:randomly`
Expected: PASS — 5 passed

Note: the backoff assertion expects `[2.0, 4.0]` because `random.uniform` is patched to return `0.0`, removing jitter.

- [ ] **Step 5: Commit**

```bash
git add src/finwiz/infrastructure/resilience/perplexity_retry.py tests/unit/infrastructure/test_perplexity_retry.py
git commit -m "feat(resilience): add Perplexity retry wrapper with backoff and concurrency cap"
```

---

## Task 2: Route fact_pack through the retry wrapper

`fact_pack_research.py:183-189` calls `perplexity_structured` directly, exactly once. This is the call that failed 28 times in the 2026-08-15 run (20 transport timeouts, 8 HTTP 429s) and cost 22 holdings.

**Files:**

- Modify: `src/finwiz/analysis/fact_pack_research.py:15` (import), `:183-189` (call site)
- Test: `tests/unit/analysis/test_fact_pack_stage.py`

**Interfaces:**

- Consumes: `perplexity_with_retry` from Task 1.
- Produces: no signature change — `fetch_fact_pack` and `fetch_fact_pack_sync` keep their exact existing signatures (`fetch_fact_pack_sync(ticker: str, company_name: str, sector: str | None = None, industry: str | None = None, *, timeout: float = 15.0) -> FactPack | None`).

- [ ] **Step 1: Write the failing test**

Create `tests/unit/analysis/test_fact_pack_stage.py`:

```python
"""Tests for fact_pack fetching and stage behavior."""

import pytest

from finwiz.analysis.fact_pack_research import fetch_fact_pack


@pytest.mark.asyncio
async def test_fetch_fact_pack_uses_retry_wrapper(mocker):
    called = mocker.patch(
        "finwiz.analysis.fact_pack_research.perplexity_with_retry",
        new=mocker.AsyncMock(return_value=None),
    )

    result = await fetch_fact_pack("NVDA", "NVIDIA Corp", "Technology", "Semiconductors")

    assert result is None
    assert called.await_count == 1
    assert called.await_args.kwargs["schema"].__name__ == "_FactPackRaw"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/analysis/test_fact_pack_stage.py -v -p no:randomly`
Expected: FAIL — `AttributeError: <module 'finwiz.analysis.fact_pack_research'> does not have the attribute 'perplexity_with_retry'`

- [ ] **Step 3: Write minimal implementation**

In `src/finwiz/analysis/fact_pack_research.py`, replace the import at line 15:

```python
from finwiz.infrastructure.resilience.perplexity_retry import perplexity_with_retry
```

(Delete `from crewai_custom_tools import perplexity_structured` if `perplexity_structured` has no other use in the file; keep it otherwise.)

Then replace the call at lines 183-189:

```python
        raw = await perplexity_with_retry(
            prompt=prompt,
            schema=_FactPackRaw,
            system=_SYSTEM_FR,
            search_recency_filter="month",
            timeout=timeout,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/analysis/test_fact_pack_stage.py -v -p no:randomly`
Expected: PASS — 1 passed

- [ ] **Step 5: Commit**

```bash
git add src/finwiz/analysis/fact_pack_research.py tests/unit/analysis/test_fact_pack_stage.py
git commit -m "fix(fact_pack): retry Perplexity fetches instead of failing on first error"
```

---

## Task 3: Make the fact_pack failure retryable at the stage layer

`@stage(name="fact_pack", timeout_s=60, retries=1)` at `fact_pack.py:77` declares one retry, but it is unreachable. `_is_transient` (`_resilience.py:53-62`) returns `False` for `RuntimeError`, and `_fact_pack_inner` raises exactly that at `fact_pack.py:74`. So the stage gives up after one attempt with `retries_used=0` — which is what the ledger recorded for all 22 failures.

Introduce a dedicated exception the resilience layer recognises, so the declared retry actually happens.

**Files:**

- Modify: `src/finwiz/analysis/stages/fact_pack.py:74`
- Modify: `src/finwiz/analysis/stages/_resilience.py:46-62`
- Test: `tests/unit/analysis/test_fact_pack_stage.py` (append)

**Interfaces:**

- Produces: `class TransientStageError(RuntimeError)` in `src/finwiz/analysis/stages/_resilience.py`, exported for any stage body that wants its declared `retries` to be reachable.

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/analysis/test_fact_pack_stage.py`:

```python
from finwiz.analysis.stages._resilience import TransientStageError, _is_transient


def test_transient_stage_error_is_classified_transient():
    assert _is_transient(TransientStageError("rate limited")) is True


def test_plain_runtime_error_is_not_transient():
    assert _is_transient(RuntimeError("bad state")) is False


def test_fact_pack_inner_raises_transient_error_when_no_cache_and_no_fetch(mocker):
    from finwiz.analysis.stages import fact_pack as fact_pack_module

    cache = mocker.Mock()
    cache.get.return_value = None
    mocker.patch.object(fact_pack_module, "_get_cache", return_value=cache)
    mocker.patch.object(fact_pack_module, "fetch_fact_pack_sync", return_value=None)

    with pytest.raises(TransientStageError, match="fact_pack unavailable for NVDA"):
        fact_pack_module._fact_pack_inner("NVDA", "NVIDIA Corp", "Technology", "Semiconductors")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/analysis/test_fact_pack_stage.py -v -p no:randomly`
Expected: FAIL — `ImportError: cannot import name 'TransientStageError' from 'finwiz.analysis.stages._resilience'`

- [ ] **Step 3: Write minimal implementation**

In `src/finwiz/analysis/stages/_resilience.py`, add the class after the `_TRANSIENT_HTTP_TYPES` block (after line 50):

```python
class TransientStageError(RuntimeError):
    """A stage failure that is worth retrying (rate limit, upstream unavailable).

    Plain RuntimeError stays non-transient: it signals a programming or state
    error where a retry would only repeat the same wrong thing.
    """
```

Then in `_is_transient`, add the check immediately after the `ValidationError`/`AssertionError` guard (after line 55):

```python
    if isinstance(exc, TransientStageError):
        return True
```

In `src/finwiz/analysis/stages/fact_pack.py`, add to the imports at line 14:

```python
from finwiz.analysis.stages._resilience import StageContext, TransientStageError, stage
```

and change line 74 from `raise RuntimeError(...)` to:

```python
    raise TransientStageError(f"fact_pack unavailable for {ticker}: no cache and Perplexity fetch failed")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/analysis/test_fact_pack_stage.py -v -p no:randomly`
Expected: PASS — 4 passed

- [ ] **Step 5: Verify no stage-contract regression**

Run: `make check-stage-contract && uv run pytest tests/unit/analysis -q`
Expected: contract check passes; no new failures.

- [ ] **Step 6: Commit**

```bash
git add src/finwiz/analysis/stages/_resilience.py src/finwiz/analysis/stages/fact_pack.py tests/unit/analysis/test_fact_pack_stage.py
git commit -m "fix(stages): classify fact_pack unavailability as transient so the declared retry runs"
```

---

## Task 3b: Let an old cache still rescue a rate-limited run

Spec §4.1: "Cache warm survives across runs, so a rate-limited run degrades to stale rather than to nothing."

It currently does not. `FactPack.derive_freshness` (`schemas/hybrid_analysis/fact_pack.py:45-53`) raises `ValueError` beyond 15 days:

```python
        if age < timedelta(days=3):
            return "fresh"
        if age < timedelta(days=7):
            return "recent"
        if age < timedelta(days=15):
            return "stale"
        raise ValueError(f"FactPack older than 14 days (age={age}); cache should have evicted")
```

`FactPackCache.get()` catches that at `cache/fact_pack_cache.py:66` and returns `None`. So a 16-day-old cache entry is indistinguishable from no cache at all, and the stale-fallback branch at `stages/fact_pack.py:69-71` never fires. On a rate-limited run that is the difference between a stale answer and a dead holding.

Corporate structure and leadership do not turn over in a fortnight. Widen the stale band and let the payload's own `freshness` label carry the caveat — which is exactly the trust-spine design ("staleness is a payload field, NOT a stage outcome", `fact_pack.py:3-5`).

**Files:**

- Modify: `src/finwiz/schemas/hybrid_analysis/fact_pack.py:45-53`
- Test: `tests/unit/analysis/test_fact_pack_stage.py` (append)

**Interfaces:**

- Produces: `FactPack.derive_freshness(fetched_at: datetime) -> str` — unchanged signature, wider stale band, raising only beyond the new horizon.

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/analysis/test_fact_pack_stage.py`:

```python
from datetime import UTC, datetime, timedelta

from finwiz.schemas.hybrid_analysis.fact_pack import FactPack


def _ago(days: int) -> datetime:
    return datetime.now(UTC) - timedelta(days=days)


def test_freshness_bands_at_the_short_end():
    assert FactPack.derive_freshness(_ago(1)) == "fresh"
    assert FactPack.derive_freshness(_ago(5)) == "recent"
    assert FactPack.derive_freshness(_ago(10)) == "stale"


def test_month_old_pack_is_stale_not_an_error():
    assert FactPack.derive_freshness(_ago(30)) == "stale"


def test_ancient_pack_still_raises():
    with pytest.raises(ValueError, match="older than"):
        FactPack.derive_freshness(_ago(120))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/analysis/test_fact_pack_stage.py -v -p no:randomly -k freshness or month_old or ancient`
Expected: FAIL on `test_month_old_pack_is_stale_not_an_error` — `ValueError: FactPack older than 14 days (age=30 days...)`

- [ ] **Step 3: Write minimal implementation**

Replace lines 45-53 of `src/finwiz/schemas/hybrid_analysis/fact_pack.py`:

```python
        now = datetime.now(UTC)
        age = now - fetched_at
        if age < timedelta(days=3):
            return "fresh"
        if age < timedelta(days=7):
            return "recent"
        # Corporate structure and leadership do not turn over in a fortnight.
        # A 15-day cliff meant a rate-limited run had no cache to fall back on
        # and killed the holding outright — worse than a labelled stale answer.
        # Staleness is a payload field, not a stage outcome (see stages/fact_pack.py).
        if age < timedelta(days=_STALE_HORIZON_DAYS):
            return "stale"
        raise ValueError(f"FactPack older than {_STALE_HORIZON_DAYS} days (age={age}); cache should have evicted")
```

Add the module constant above the class:

```python
# Beyond this, a cached fact pack is not merely stale — it predates any
# reporting cycle we would defend, so the cache evicts rather than serve it.
_STALE_HORIZON_DAYS = 90
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/analysis/test_fact_pack_stage.py -v -p no:randomly`
Expected: PASS — 7 passed

- [ ] **Step 5: Check for dependent assertions**

Run: `grep -rn "14 days\|derive_freshness\|days=15" src/ tests/ | grep -v __pycache__`
Expected: update any test or docstring asserting the old 14/15-day boundary. `cache/fact_pack_cache.py:66` catches `ValueError` generically and needs no change.

- [ ] **Step 6: Commit**

```bash
git add src/finwiz/schemas/hybrid_analysis/fact_pack.py tests/unit/analysis/test_fact_pack_stage.py
git commit -m "fix(fact_pack): widen the stale window so an old cache can still rescue a rate-limited run"
```

---

## Task 4: Derive volatility in the technical fallback

`technical_fallback.py` fills MA50/MA200/RSI/MACD/beta from `price_history` but has **no volatility branch** (grep for "volatility" in that file returns nothing). Meanwhile `calculate_volatility(returns: pd.Series, annualize: bool = True) -> float` already exists at `quantitative/risk/risk_metrics.py:19`, built on empyrical's `annual_volatility`. `raw_data["price_history"]` is a `pandas.Series` of daily closes set at `deep_analysis_data_collector.py:436`.

**Files:**

- Modify: `src/finwiz/scoring/technical_fallback.py`
- Test: `tests/unit/scoring/test_volatility_fallback.py`

**Interfaces:**

- Consumes: `calculate_volatility` from `finwiz.quantitative.risk.risk_metrics`.
- Produces: `calculate_missing_technical_indicators(data: dict[str, Any], price_history: pd.Series | None = None) -> dict[str, Any]` — unchanged signature, now also sets `data["volatility"]` when absent and `price_history` has ≥2 points.

- [ ] **Step 1: Write the failing test**

Create `tests/unit/scoring/test_volatility_fallback.py`:

```python
"""Tests for volatility derivation in the technical fallback."""

import pandas as pd

from finwiz.scoring.technical_fallback import calculate_missing_technical_indicators


def _price_series() -> pd.Series:
    return pd.Series([100.0, 101.5, 99.8, 102.3, 101.1, 103.4, 102.0, 104.2, 103.1, 105.0])


def test_derives_volatility_from_price_history_when_missing():
    data = {"current_price": 105.0}

    result = calculate_missing_technical_indicators(data, _price_series())

    assert "volatility" in result
    assert 0.0 < result["volatility"] < 5.0


def test_does_not_overwrite_existing_volatility():
    data = {"current_price": 105.0, "volatility": 0.42}

    result = calculate_missing_technical_indicators(data, _price_series())

    assert result["volatility"] == 0.42


def test_leaves_volatility_absent_when_no_price_history():
    data = {"current_price": 105.0}

    result = calculate_missing_technical_indicators(data, None)

    assert "volatility" not in result


def test_leaves_volatility_absent_when_history_too_short():
    data = {"current_price": 105.0}

    result = calculate_missing_technical_indicators(data, pd.Series([100.0]))

    assert "volatility" not in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/scoring/test_volatility_fallback.py -v -p no:randomly`
Expected: FAIL — `AssertionError: assert 'volatility' in {...}` on the first test.

- [ ] **Step 3: Write minimal implementation**

In `src/finwiz/scoring/technical_fallback.py`, add the import near the top:

```python
from finwiz.quantitative.risk.risk_metrics import calculate_volatility
```

Add this helper at module level:

```python
def _fill_volatility(data: dict[str, Any], price_history: pd.Series | None) -> None:
    """Derive annualized volatility from price history when the quant tool did not supply it.

    Mutates ``data`` in place. Never overwrites a value the quant tool already
    produced, and stays silent when there is not enough history to be meaningful.
    """
    if data.get("volatility") is not None:
        return
    if price_history is None or len(price_history) < 2:
        return

    returns = price_history.pct_change().dropna()
    if returns.empty:
        return

    data["volatility"] = calculate_volatility(returns, annualize=True)
    logger.debug(f"Derived volatility={data['volatility']:.4f} from {len(returns)} return observations")
```

Call it inside `calculate_missing_technical_indicators`, immediately **before** the `current_price` early-return guard at line 33-37, so a missing price does not also suppress volatility:

```python
    _fill_volatility(data, price_history)

    current_price = data.get("current_price")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/scoring/test_volatility_fallback.py -v -p no:randomly`
Expected: PASS — 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/finwiz/scoring/technical_fallback.py tests/unit/scoring/test_volatility_fallback.py
git commit -m "feat(scoring): derive volatility from price history in the technical fallback"
```

---

## Task 5: Run the fallback before the critical-field gate

This is the ordering bug. In `deep_analysis_scorer.calculate_composite_score`:

- line 97 — Step 2: `self._validate_critical_fields(...)` — raises `CriticalFieldError`
- line 100 — Step 3: `self._calculate_component_scores(...)`, which calls `calculate_missing_technical_indicators` at line 222

So no fallback can ever rescue a critical field: the raise has already fired. This is why `beta` (critical for stocks, `critical_fields_config.py:18`) can never be rescued by the existing `data["beta"] = 1.0` fallback at `technical_fallback.py:50-51` either. Task 4 is inert until this task lands.

**Files:**

- Modify: `src/finwiz/scoring/deep_analysis_scorer.py:92-100`
- Test: `tests/unit/scoring/test_volatility_fallback.py` (append)

**Interfaces:**

- Consumes: `calculate_missing_technical_indicators` (Task 4).
- Produces: no signature change to `calculate_composite_score`.

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/scoring/test_volatility_fallback.py`:

```python
import pytest

from finwiz.config.critical_fields_config import CriticalFieldError
from finwiz.scoring.deep_analysis_scorer import DeepAnalysisScorer


def _etf_data_without_volatility() -> dict:
    return {
        "current_price": 105.0,
        "expense_ratio": 0.07,
        "price_history": _price_series(),
    }


def test_volatility_is_recovered_before_the_critical_gate():
    scorer = DeepAnalysisScorer()

    result = scorer.calculate_composite_score(ticker="VUSA.L", asset_class="etf", data=_etf_data_without_volatility())

    assert result.composite_score >= 0.0


def test_gate_still_fires_when_nothing_can_be_recovered():
    scorer = DeepAnalysisScorer()

    with pytest.raises(CriticalFieldError) as exc:
        scorer.calculate_composite_score(ticker="XTSLA", asset_class="etf", data={"expense_ratio": 0.07})

    assert "current_price" in str(exc.value)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/scoring/test_volatility_fallback.py -v -p no:randomly -k "critical_gate or recovered"`
Expected: FAIL — `CriticalFieldError: Cannot analyze VUSA.L (etf): Missing critical fields: volatility (missing)` on the first test.

- [ ] **Step 3: Write minimal implementation**

In `src/finwiz/scoring/deep_analysis_scorer.py`, insert a recovery step between Step 1 and Step 2 (between lines 94 and 97):

```python
            # Step 1b: Recover derivable fields BEFORE the gate.
            # The gate is fail-fast by design, but failing fast on a field we can
            # compute from data already in hand is a false negative, not honesty.
            self._recover_derivable_fields(data)
```

Add the method next to `_validate_critical_fields` (after line 216):

```python
    def _recover_derivable_fields(self, data: dict[str, Any]) -> None:
        """Fill fields derivable from collected data before the critical-field gate runs.

        Only touches fields that are absent; never overwrites collected values.
        """
        from finwiz.scoring.technical_fallback import calculate_missing_technical_indicators

        price_history = data.get("price_history")
        calculate_missing_technical_indicators(data, price_history)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/scoring/test_volatility_fallback.py -v -p no:randomly`
Expected: PASS — 6 passed

- [ ] **Step 5: Run the full scorer suite for regressions**

Run: `uv run pytest tests/unit/scoring -q`
Expected: no new failures. `tests/unit/scoring/test_deep_analysis_scorer.py` has 12 `mocker.patch("finwiz.scoring.deep_analysis_scorer.is_feature_enabled", ...)` call sites; none of them patch the new method, so they should be unaffected.

- [ ] **Step 6: Commit**

```bash
git add src/finwiz/scoring/deep_analysis_scorer.py tests/unit/scoring/test_volatility_fallback.py
git commit -m "fix(scoring): recover derivable fields before the critical-field gate"
```

---

## Task 6: Normalize percent-scaled volatility

Two producers disagree on units. `performance_metrics.py:90` emits fractional volatility (`returns.std() * np.sqrt(252)` → 0.25). `backtesting_performance.py:246` emits percent (`float(annualized_vol * 100)` → 25.0). Both can reach the flat `volatility` key: the explicit block at `deep_analysis_data_collector.py:464-471` takes `performance_metrics.volatility`, but when that is absent or None, `_flatten_recursive` (`:588`, guard `if key not in target` at `:596`) hoists `backtest_result.volatility` instead.

The gate bound is `v > 5.0` (`critical_fields_config.py:162`), so a percent-scaled 25.3 is rejected as `volatility (invalid value: 25.3)` — a units bug reported as missing data.

**Files:**

- Modify: `src/finwiz/config/critical_fields_config.py`
- Test: `tests/unit/scoring/test_volatility_fallback.py` (append)

**Interfaces:**

- Produces: `normalize_volatility(value: float | int | None) -> float | None` in `finwiz.config.critical_fields_config`.

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/scoring/test_volatility_fallback.py`:

```python
from finwiz.config.critical_fields_config import normalize_volatility


def test_fractional_volatility_passes_through():
    assert normalize_volatility(0.25) == 0.25


def test_percent_scaled_volatility_is_rescaled():
    assert normalize_volatility(25.3) == pytest.approx(0.253)


def test_absurd_volatility_is_rejected():
    assert normalize_volatility(900.0) is None


def test_none_stays_none():
    assert normalize_volatility(None) is None


def test_zero_is_preserved_not_treated_as_missing():
    assert normalize_volatility(0.0) == 0.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/scoring/test_volatility_fallback.py -v -p no:randomly -k volatility`
Expected: FAIL — `ImportError: cannot import name 'normalize_volatility' from 'finwiz.config.critical_fields_config'`

- [ ] **Step 3: Write minimal implementation**

In `src/finwiz/config/critical_fields_config.py`, add above the `SANITY_CHECKS` dict:

```python
# Annualized volatility above this is not a real reading — it is a units error
# or corrupt data. Below it, values > 5.0 are treated as percent-scaled and
# divided by 100 (two producers in-tree disagree on units; see
# quantitative/performance_metrics.py:90 vs quantitative/backtesting_performance.py:246).
_VOLATILITY_ABSURD_CEILING = 500.0


def normalize_volatility(value: float | int | None) -> float | None:
    """Coerce a volatility reading to the fractional scale, or None if unusable.

    Args:
        value: Raw volatility, fractional (0.25) or percent-scaled (25.0).

    Returns:
        Fractional volatility, or None when the value is missing, negative, or absurd.
    """
    if value is None:
        return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if v < 0.0 or v > _VOLATILITY_ABSURD_CEILING:
        return None
    if v > 5.0:
        return v / 100.0
    return v
```

Then, in the validation loop at lines 172-185, normalize before the sanity check. Replace the loop body's opening with:

```python
    for field in critical_fields:
        value = data.get(field)

        if field == "volatility":
            value = normalize_volatility(value)
            if value is not None:
                data[field] = value

        # Check if field is missing or None
        if field not in data or value is None:
            missing_fields.append(f"{field} (missing)")
            continue
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/scoring/test_volatility_fallback.py -v -p no:randomly`
Expected: PASS — 11 passed

- [ ] **Step 5: Commit**

```bash
git add src/finwiz/config/critical_fields_config.py tests/unit/scoring/test_volatility_fallback.py
git commit -m "fix(validation): normalize percent-scaled volatility instead of rejecting it"
```

---

## Task 7: Apply ticker hygiene to the discovery universe

`discovery/ticker_hygiene.py` exists and blocklists `XTSLA` by name at `:30` ("BlackRock cash-sweep placeholder, not a tradable ticker"), exposing `is_tradable()` at `:44` and `sanitize_symbols()` at `:49`. It is applied in `market_data.py:85` and `:175` — but `universe_provider.py`, `breakout_detector.py` and `momentum_scanner.py` contain zero references to it. That is why `XTSLA` entered the universe and produced nine `Quote not found for symbol: XTSLA` errors in the run.

**Files:**

- Modify: `src/finwiz/discovery/universe_provider.py:87`
- Test: `tests/unit/discovery/test_universe_provider_selection.py`

**Interfaces:**

- Consumes: `sanitize_symbols` from `finwiz.discovery.ticker_hygiene`.
- Produces: `DynamicUniverseProvider.get_universe(asset_class: str, exclude_tickers: list[str] | None = None) -> list[str]` — unchanged signature, now hygiene-filtered.

- [ ] **Step 1: Write the failing test**

Create `tests/unit/discovery/test_universe_provider_selection.py`:

```python
"""Tests for universe selection, hygiene and the candidate floor."""

from finwiz.discovery.universe_provider import DynamicUniverseProvider


def test_untradable_placeholders_are_filtered_out(mocker):
    provider = DynamicUniverseProvider()
    mocker.patch.object(provider, "_mine_etf_holdings", return_value=["AAPL", "XTSLA", "MSFT"])

    result = provider.get_universe("etf")

    assert "XTSLA" not in result
    assert "AAPL" in result
    assert "MSFT" in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/discovery/test_universe_provider_selection.py -v -p no:randomly`
Expected: FAIL — `AssertionError: assert 'XTSLA' not in ['AAPL', 'MSFT', 'XTSLA']`

- [ ] **Step 3: Write minimal implementation**

In `src/finwiz/discovery/universe_provider.py`, add the import:

```python
from finwiz.discovery.ticker_hygiene import sanitize_symbols
```

Replace line 87:

```python
        result = sorted(set(sanitize_symbols(tickers)) - exclude_set)
```

`sanitize_symbols` already upper-cases; confirm by reading `ticker_hygiene.py:49` before relying on it. If it does not, keep the `.upper()` in the comprehension.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/discovery/test_universe_provider_selection.py -v -p no:randomly`
Expected: PASS — 1 passed

- [ ] **Step 5: Commit**

```bash
git add src/finwiz/discovery/universe_provider.py tests/unit/discovery/test_universe_provider_selection.py
git commit -m "fix(discovery): apply ticker hygiene to the mined universe"
```

---

## Task 8: Fix the seed-ETF selection bug

`universe_provider.py:71` reads:

```python
seed_etfs = self._seed_etfs or self.DEFAULT_STOCK_SEED_ETFS if asset_class == "stock" else self.DEFAULT_ETF_SEED_ETFS
```

Python binds this as `(self._seed_etfs or self.DEFAULT_STOCK_SEED_ETFS) if asset_class == "stock" else self.DEFAULT_ETF_SEED_ETFS`, so the constructor's `seed_etfs` override is **unreachable for ETFs** — the ETF path always uses `DEFAULT_ETF_SEED_ETFS = ["VT", "AOA", "AOR"]`. Line 74's `except (ValueError, Exception)` is also a catch-all whose first member is dead (`ValueError` is an `Exception`).

**Files:**

- Modify: `src/finwiz/discovery/universe_provider.py:71,74`
- Test: `tests/unit/discovery/test_universe_provider_selection.py` (append)

- [ ] **Step 1: Write the failing test**

Append:

```python
def test_seed_override_is_honored_for_etfs(mocker):
    provider = DynamicUniverseProvider(seed_etfs=["SPY"])
    mine = mocker.patch.object(provider, "_mine_etf_holdings", return_value=["AAPL"])

    provider.get_universe("etf")

    assert mine.call_args.args[0] == ["SPY"]


def test_seed_override_is_honored_for_stocks(mocker):
    provider = DynamicUniverseProvider(seed_etfs=["QQQ"])
    mine = mocker.patch.object(provider, "_mine_etf_holdings", return_value=["AAPL"])

    provider.get_universe("stock")

    assert mine.call_args.args[0] == ["QQQ"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/discovery/test_universe_provider_selection.py -v -p no:randomly -k seed_override`
Expected: FAIL on `test_seed_override_is_honored_for_etfs` — `assert ['VT', 'AOA', 'AOR'] == ['SPY']`

- [ ] **Step 3: Write minimal implementation**

Replace lines 71-80:

```python
            default_seeds = self.DEFAULT_STOCK_SEED_ETFS if asset_class == "stock" else self.DEFAULT_ETF_SEED_ETFS
            seed_etfs = self._seed_etfs or default_seeds
            try:
                tickers = self._mine_etf_holdings(seed_etfs)
            except Exception:
                self._logger.warning(
                    "Dynamic universe failed for %s, falling back to static",
                    asset_class,
                )
                tickers = self._fallback_static_universe(asset_class)
                source = "static"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/discovery/test_universe_provider_selection.py -v -p no:randomly`
Expected: PASS — 3 passed

- [ ] **Step 5: Commit**

```bash
git add src/finwiz/discovery/universe_provider.py tests/unit/discovery/test_universe_provider_selection.py
git commit -m "fix(discovery): honor seed-ETF override for ETFs and drop the dead catch-all"
```

---

## Task 9: Enforce a universe floor

Spec §4.3: at least 50 candidates per asset class must survive exclusion, and a shortfall must be logged rather than silently scanned.

Measured on 2026-08-15: `VT`(10) ∪ `AOA`(8) ∪ `AOR`(8) = 18 unique; 7 already held; 11 remained. The static fallback returns far more — `ScreeningUtils().get_screening_universe(...)` yields 50 for `etf`, 66 for `stock`, 39 for `crypto` (verified by execution). So the fix is to union the static universe in when mining falls short, not to replace mining.

**Files:**

- Modify: `src/finwiz/discovery/universe_provider.py`
- Test: `tests/unit/discovery/test_universe_provider_selection.py` (append)

**Interfaces:**

- Produces: module constant `MIN_UNIVERSE_SIZE = 50` in `finwiz.discovery.universe_provider`.

- [ ] **Step 1: Write the failing test**

Append:

```python
from finwiz.discovery.universe_provider import MIN_UNIVERSE_SIZE


def test_static_universe_is_unioned_in_when_mining_falls_short(mocker):
    provider = DynamicUniverseProvider()
    mocker.patch.object(provider, "_mine_etf_holdings", return_value=["AAPL", "MSFT"])
    mocker.patch.object(provider, "_fallback_static_universe", return_value=[f"T{i}" for i in range(MIN_UNIVERSE_SIZE)])

    result = provider.get_universe("etf")

    assert len(result) >= MIN_UNIVERSE_SIZE
    assert "AAPL" in result


def test_shortfall_is_logged_when_floor_cannot_be_met(mocker):
    provider = DynamicUniverseProvider()
    mocker.patch.object(provider, "_mine_etf_holdings", return_value=["AAPL"])
    mocker.patch.object(provider, "_fallback_static_universe", return_value=["MSFT"])
    warn = mocker.patch.object(provider._logger, "warning")

    result = provider.get_universe("etf")

    assert len(result) == 2
    assert any("below the floor" in str(c.args[0]) for c in warn.call_args_list)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/discovery/test_universe_provider_selection.py -v -p no:randomly -k "floor or short"`
Expected: FAIL — `ImportError: cannot import name 'MIN_UNIVERSE_SIZE'`

- [ ] **Step 3: Write minimal implementation**

Add near the top of `src/finwiz/discovery/universe_provider.py`:

```python
# A universe smaller than this is not a search. Measured 2026-08-15: mining three
# seed ETFs yielded 18 unique names, 11 after excluding the portfolio — every one
# of which graded below the actionability floor. Discovery reported "0
# opportunities" when the honest statement was "we looked at 11 candidates".
MIN_UNIVERSE_SIZE = 50
```

Replace the deduplicate/filter/sort block (line 87, after Task 7's change) with:

```python
        result = sorted(set(sanitize_symbols(tickers)) - exclude_set)

        if len(result) < MIN_UNIVERSE_SIZE and asset_class != "crypto":
            static = sanitize_symbols(self._fallback_static_universe(asset_class))
            result = sorted(set(result) | (set(static) - exclude_set))
            source = f"{source}+static"

        if len(result) < MIN_UNIVERSE_SIZE:
            self._logger.warning(
                "Universe for %s has %d tickers, below the floor of %d — discovery coverage is limited this run",
                asset_class,
                len(result),
                MIN_UNIVERSE_SIZE,
            )
```

The `asset_class != "crypto"` guard exists because the crypto branch already goes straight to static at line 68.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/discovery/test_universe_provider_selection.py -v -p no:randomly`
Expected: PASS — 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/finwiz/discovery/universe_provider.py tests/unit/discovery/test_universe_provider_selection.py
git commit -m "feat(discovery): enforce a minimum universe size and log shortfalls"
```

---

## Task 10: Delete the fabricated legacy discovery fallback

`scoring/etf_analyzer.py:35-38` wraps the whole pipeline in `except Exception` and falls back to `_legacy_etf_analysis`, which returns **hardcoded invented opportunities**: `VTI` grade `A+` score `0.93`, `VXUS` grade `A` `0.86`, `BND` grade `A` `0.82` (lines 46-71), labelled `"method": "python_analysis"` as though computed. `stock_analyzer.py` and `crypto_analyzer.py` have the same shape.

Any pipeline exception therefore injects invented A+ tickers into `a_plus_*.json` and into the family report. This is the single largest correctness hazard in the discovery area, and it is exactly the failure mode the spec exists to eliminate: presenting fabricated output as authoritative.

**Files:**

- Modify: `src/finwiz/scoring/etf_analyzer.py`, `src/finwiz/scoring/stock_analyzer.py`, `src/finwiz/scoring/crypto_analyzer.py`
- Test: `tests/unit/scoring/test_discovery_analyzers.py`

**Interfaces:**

- Produces: `analyze_etf_opportunities(session_id: str) -> dict[str, Any]` (and stock/crypto twins) — unchanged signature. On pipeline failure it now returns an empty, honestly-labelled result instead of invented data.

- [ ] **Step 1: Write the failing test**

Create `tests/unit/scoring/test_discovery_analyzers.py`:

```python
"""Discovery analyzers must never fabricate opportunities."""

from finwiz.scoring.etf_analyzer import analyze_etf_opportunities


def test_pipeline_failure_yields_no_opportunities(mocker):
    mocker.patch("finwiz.config.features.flags.is_feature_enabled", return_value=True)
    mocker.patch(
        "finwiz.scoring.discovery.pipeline.NewcomerDiscoveryPipeline",
        side_effect=RuntimeError("universe fetch exploded"),
    )

    result = analyze_etf_opportunities("test-session")

    assert result["opportunities"] == []
    assert result["performance_metrics"]["opportunities_found"] == 0
    assert result["performance_metrics"]["method"] == "newcomer_discovery_failed"


def test_no_hardcoded_tickers_remain_in_module():
    import inspect

    from finwiz.scoring import etf_analyzer

    source = inspect.getsource(etf_analyzer)
    for invented in ("VTI", "VXUS", "BND"):
        assert invented not in source
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/scoring/test_discovery_analyzers.py -v -p no:randomly`
Expected: FAIL — the first test gets three fabricated opportunities; the second finds `"VTI"` in the source.

- [ ] **Step 3: Write minimal implementation**

Replace the whole body of `src/finwiz/scoring/etf_analyzer.py` below the imports:

```python
def analyze_etf_opportunities(session_id: str) -> dict[str, Any]:
    """Analyze ETF opportunities using pure Python.

    Routes through ``NewcomerDiscoveryPipeline``. A pipeline failure yields an
    empty, honestly-labelled result — never fabricated candidates. Inventing
    A-grade tickers to fill a gap is worse than reporting the gap.
    """
    start_time = time.time()

    try:
        logger.info("Using NewcomerDiscoveryPipeline for etf discovery")
        from finwiz.scoring.discovery.pipeline import NewcomerDiscoveryPipeline

        pipeline = NewcomerDiscoveryPipeline("etf")
        result = pipeline.discover(session_id)
        return pipeline._to_legacy_format(result, start_time)
    except Exception as e:
        logger.error("Newcomer discovery pipeline failed for etf: %s", e)
        return {
            "opportunities": [],
            "analysis_summary": f"ETF discovery unavailable this run: {e}",
            "performance_metrics": {
                "execution_time_seconds": time.time() - start_time,
                "opportunities_found": 0,
                "cost_usd": 0.0,
                "llm_calls_made": 0,
                "method": "newcomer_discovery_failed",
                "error": str(e),
            },
        }
```

Delete `_legacy_etf_analysis` entirely, and delete the now-unused `is_feature_enabled` import. Apply the identical shape to `stock_analyzer.py` and `crypto_analyzer.py`, substituting the asset class in the pipeline constructor, the log messages, and the summary string.

**Note on the removed flag:** the `newcomer_discovery` gate disappears with the fallback, because the only alternative branch was the fabricated one. Per the project rule "remove the switch, not the surface", keep any `newcomer_discovery` entry in `config/features/definitions.py` as a no-op if other code reads it — grep before deleting.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/scoring/test_discovery_analyzers.py -v -p no:randomly`
Expected: PASS — 2 passed

- [ ] **Step 5: Add the same guard for stock and crypto**

Append to `tests/unit/scoring/test_discovery_analyzers.py`:

```python
import pytest


@pytest.mark.parametrize(
    ("module_name", "invented"),
    [
        ("finwiz.scoring.stock_analyzer", ("AAPL", "MSFT", "NVDA")),
        ("finwiz.scoring.crypto_analyzer", ("BTC-USD", "ETH-USD")),
    ],
)
def test_other_analyzers_have_no_hardcoded_tickers(module_name, invented):
    import importlib
    import inspect

    source = inspect.getsource(importlib.import_module(module_name))
    hardcoded = [t for t in invented if f'"{t}"' in source]
    assert hardcoded == []
```

Run: `uv run pytest tests/unit/scoring/test_discovery_analyzers.py -v -p no:randomly`
Expected: PASS — 4 passed

- [ ] **Step 6: Commit**

```bash
git add src/finwiz/scoring/etf_analyzer.py src/finwiz/scoring/stock_analyzer.py src/finwiz/scoring/crypto_analyzer.py tests/unit/scoring/test_discovery_analyzers.py
git commit -m "fix(discovery): stop fabricating A+ opportunities when the pipeline fails"
```

---

## Task 11: Retire the `discovery_latest.json` name

Verified: `discovery_latest.json` has **three readers and zero writers** anywhere in the repo. Readers are `tools/alternative_finder_tool.py:179`, `orchestrators/extraction/engine.py:169` and `:192`. `to_html_converter.py:38-39` maps both `discovery_output_*.json` and `discovery_latest.json` to the same output name. Discovery actually writes `consolidated_discovery.json` (`discovery_orchestrator.py:367`).

This is why every holding logged "No discovery crew output found at output/discovery/discovery_latest.json" and alternatives were empty portfolio-wide.

Spec §4.4 resolution: point the readers at the real file, retire the dead name.

**Files:**

- Modify: `src/finwiz/tools/alternative_finder_tool.py:179,181`
- Modify: `src/finwiz/orchestrators/extraction/engine.py:169,192`
- Modify: `src/finwiz/infrastructure/json/to_html_converter.py:38-39`
- Test: `tests/unit/tools/test_alternative_finder_tool.py` (existing — it fabricates `discovery_latest.json` at :86, :249, :284, :443, :594 and must be updated)

- [ ] **Step 1: Write the failing test**

Create `tests/unit/discovery/test_discovery_paths.py`:

```python
"""The discovery artifact name must be consistent between writer and readers."""

from pathlib import Path

SRC = Path("src/finwiz")


def test_no_source_file_references_the_retired_name():
    offenders = []
    for path in SRC.rglob("*.py"):
        if "discovery_latest.json" in path.read_text(encoding="utf-8"):
            offenders.append(str(path))
    assert offenders == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/discovery/test_discovery_paths.py -v -p no:randomly`
Expected: FAIL — offenders lists `alternative_finder_tool.py`, `extraction/engine.py`, `to_html_converter.py`.

- [ ] **Step 3: Write minimal implementation**

In `src/finwiz/tools/alternative_finder_tool.py`, replace line 179:

```python
        latest_file = self.discovery_output_dir / "consolidated_discovery.json"
```

and update the warning text at line 181 to name the same file.

In `src/finwiz/orchestrators/extraction/engine.py`, replace both `:169` and `:192`:

```python
            discovery_file = self.discovery_dir / "consolidated_discovery.json"
```

In `src/finwiz/infrastructure/json/to_html_converter.py`, delete the dead line 39 (`"discovery_latest.json": "discovery_latest.html",`), keeping the `discovery_output_*.json` glob at line 38.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/discovery/test_discovery_paths.py -v -p no:randomly`
Expected: PASS — 1 passed

- [ ] **Step 5: Update the existing alternative-finder tests**

`tests/unit/tools/test_alternative_finder_tool.py` writes fixture files named `discovery_latest.json` at lines 86, 249, 284, 443, 594. Rename each to `consolidated_discovery.json`.

Run: `uv run pytest tests/unit/tools/test_alternative_finder_tool.py -q`
Expected: PASS — no failures.

- [ ] **Step 6: Commit**

```bash
git add src/finwiz/tools/alternative_finder_tool.py src/finwiz/orchestrators/extraction/engine.py src/finwiz/infrastructure/json/to_html_converter.py tests/unit/discovery/test_discovery_paths.py tests/unit/tools/test_alternative_finder_tool.py
git commit -m "fix(discovery): read the artifact discovery actually writes"
```

---

## Task 12: Persist the pre-filter scored candidates

`_filter_actionable` runs at `scoring/discovery/pipeline.py:105`; `_persist_result` runs at `:121`. So `newcomer_*.json` only ever contains post-filter survivors, and the 29/42/10 candidates dropped on 2026-08-15 are unrecoverable from this run's outputs. That contradicts the stated rationale at `candidate_scorer.py:40-42` ("callers that legitimately need the full scored list (diagnostics, tests)") and makes Task 13's calibration unverifiable against real data.

**Files:**

- Modify: `src/finwiz/scoring/discovery/pipeline.py:105,121`
- Test: `tests/unit/scoring/discovery/test_pipeline.py` (existing — append)

**Interfaces:**

- Produces: `output/discovery/scored_{asset_class}.json` with shape `{"asset_class": str, "scored": list[dict], "actionable_count": int}`.

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/scoring/discovery/test_pipeline.py`:

```python
def test_scored_candidates_are_persisted_before_filtering(tmp_path, mocker, monkeypatch):
    from finwiz.scoring.discovery import pipeline as pipeline_module
    from finwiz.scoring.discovery.pipeline import NewcomerDiscoveryPipeline

    monkeypatch.chdir(tmp_path)
    mocker.patch.object(NewcomerDiscoveryPipeline, "_load_portfolio_tickers", return_value=None)
    pipeline = NewcomerDiscoveryPipeline("etf")

    scored = [
        pipeline_module.NewcomerCandidate(ticker="AAA", composite_score=0.72, grade="C+"),
        pipeline_module.NewcomerCandidate(ticker="BBB", composite_score=0.40, grade="F"),
    ]
    pipeline._persist_scored(scored, actionable_count=1)

    written = json.loads((tmp_path / "output" / "discovery" / "scored_etf.json").read_text(encoding="utf-8"))
    assert len(written["scored"]) == 2
    assert written["actionable_count"] == 1
    assert {c["ticker"] for c in written["scored"]} == {"AAA", "BBB"}
```

Add `import json` at the top of the test file if absent.

`NewcomerCandidate` requires more than three fields — read `src/finwiz/schemas/newcomer_discovery.py` and supply whatever is mandatory. If constructing one is noisy, use `NewcomerCandidate.model_construct(...)` with just the three fields the assertions read.

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/scoring/discovery/test_pipeline.py -v -p no:randomly -k persisted`
Expected: FAIL — `AttributeError: 'NewcomerDiscoveryPipeline' object has no attribute '_persist_scored'`

- [ ] **Step 3: Write minimal implementation**

Add the method to `NewcomerDiscoveryPipeline` in `src/finwiz/scoring/discovery/pipeline.py`, next to `_persist_result` (line 436). Note the class has **no** `self.discovery_dir` and **no** `self._logger` — `_persist_result` builds the path locally and uses the module-level `logger`. Mirror that exactly:

```python
    def _persist_scored(self, scored: list[NewcomerCandidate], actionable_count: int) -> None:
        """Write the full scored candidate list before actionability filtering.

        Without this, every dropped candidate is unrecoverable and "0
        opportunities" is indistinguishable from "we scored 10 and rejected all
        10". Diagnostics need the distinction.
        """
        try:
            discovery_dir = Path("output") / "discovery"
            discovery_dir.mkdir(parents=True, exist_ok=True)
            out = discovery_dir / f"scored_{self.asset_class}.json"
            payload = {
                "asset_class": self.asset_class,
                "scored": [c.model_dump() for c in scored],
                "actionable_count": actionable_count,
            }
            with open(out, "w") as f:
                json.dump(payload, f, indent=2, default=str)
            logger.info("Persisted %d scored %s candidates (%d actionable) to %s", len(scored), self.asset_class, actionable_count, out)
        except OSError as e:
            logger.warning("Failed to write scored candidates: %s", e)
```

Then at line 105, capture the pre-filter list before filtering rebinds `candidates`:

```python
        scored_before_filter = list(candidates)
        candidates = self._filter_actionable(candidates)
        self._persist_scored(scored_before_filter, actionable_count=len(candidates))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/scoring/discovery/test_pipeline.py -v -p no:randomly`
Expected: PASS — no failures.

- [ ] **Step 5: Commit**

```bash
git add src/finwiz/scoring/discovery/pipeline.py tests/unit/scoring/discovery/test_pipeline.py
git commit -m "feat(discovery): persist the full scored candidate list before filtering"
```

---

## Task 13: Calibrate the factor score against the grade ladder

Widening the universe (Task 9) is necessary but not sufficient. `factor_score_from_returns` (`discovery/market_data.py:207-228`) computes `0.7 * logistic(4 * cumulative) + 0.3 * vol_score`, where the logistic is centered at 0.5 for zero cumulative return and `vol_score = 1 - daily_vol * 20`. Typical standalone factors land in 0.50-0.65 — **below** the actionability floor before any portfolio-fit multiplier is applied. The C grade requires ≥0.65 (`grading_system.py:39-90`, effective floor 0.65).

So a genuinely strong candidate cannot currently reach C. That is the real reason all 81 scored candidates were dropped, not the universe size alone.

The floor stays at C — noise stays out, per the project rule that discovery scanners exclude weak signals rather than emitting them with D/F grades. What changes is the formula's dynamic range, so that a strong performer can actually clear the bar.

**Files:**

- Modify: `src/finwiz/discovery/market_data.py:207-228`
- Test: `tests/unit/discovery/test_factor_score.py`

**Interfaces:**

- Produces: `factor_score_from_returns(returns: list[float] | None) -> float | None` — exact current signature at `market_data.py:207`, preserved. It takes a **plain list of floats**, not a pandas Series, and returns `None` for series shorter than 5 points.

- [ ] **Step 1: Write the failing test**

Create `tests/unit/discovery/test_factor_score.py`:

```python
"""The factor score must be able to reach the actionability floor."""

from finwiz.discovery.market_data import factor_score_from_returns
from finwiz.scoring.grading_system import score_to_grade

ACTIONABLE_FLOOR = 0.65


def _returns(daily: float, days: int = 126) -> list[float]:
    return [daily] * days


def test_strong_low_volatility_performer_clears_the_actionable_floor():
    # ~+30% over six months with modest daily moves — an unambiguously good candidate.
    score = factor_score_from_returns(_returns(0.0021))

    assert score is not None
    assert score >= ACTIONABLE_FLOOR
    assert score_to_grade(score) in {"C", "C+", "B", "B+", "A", "A+"}


def test_flat_performer_stays_below_the_floor():
    score = factor_score_from_returns(_returns(0.0))

    assert score is not None
    assert score < ACTIONABLE_FLOOR


def test_declining_performer_scores_low():
    score = factor_score_from_returns(_returns(-0.002))

    assert score is not None
    assert score < 0.5


def test_short_series_returns_none():
    assert factor_score_from_returns([0.01, 0.01]) is None
    assert factor_score_from_returns(None) is None


def test_score_stays_in_unit_range():
    for daily in (-0.05, -0.001, 0.0, 0.001, 0.05):
        score = factor_score_from_returns(_returns(daily))
        assert score is not None
        assert 0.0 <= score <= 1.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/discovery/test_factor_score.py -v -p no:randomly`
Expected: FAIL on `test_strong_low_volatility_performer_clears_the_actionable_floor` — the score lands around 0.6.

- [ ] **Step 3: Write minimal implementation**

The current body (`market_data.py:216-228`) is:

```python
    if not returns or len(returns) < 5:
        return None

    import numpy as np

    arr = np.asarray(returns, dtype=float)
    cumulative = float(np.prod(1.0 + arr) - 1.0)
    momentum = 1.0 / (1.0 + np.exp(-4.0 * cumulative))  # cumulative 0 -> 0.5
    daily_vol = float(arr.std())
    vol_score = max(0.0, min(1.0, 1.0 - daily_vol * 20.0))  # ~5% daily vol -> 0
    score = 0.7 * momentum + 0.3 * vol_score
    return max(0.0, min(1.0, float(score)))
```

With gain 4, a +30% six-month run gives `momentum = 1/(1+e^-1.2) = 0.769`; with a flat-ish `vol_score ≈ 0.96` the blend is `0.7*0.769 + 0.3*0.96 = 0.826` — which does clear 0.65. The compression bites on realistic series, where `vol_score` is far lower: at 2% daily vol, `vol_score = 0.6`, and a +10% run gives `momentum = 0.599`, blending to `0.599*0.7 + 0.6*0.3 = 0.60` — below the floor.

Add module constants above the function and re-center the logistic:

```python
# Calibration target: a candidate up ~15%+ over the window with ordinary
# volatility must be able to reach the C floor (0.65, grading_system.py:39-90).
# The original gain of 4 centered at zero return compressed realistic candidates
# into 0.50-0.65, so the grade ladder was unreachable and discovery reported
# "0 opportunities" for a universe it had graded rather than searched.
# The floor itself stays at C — weak signals are excluded, never low-graded.
_MOMENTUM_GAIN = 9.0
_MOMENTUM_CENTER = 0.05
_VOL_PENALTY = 12.0
```

and replace the two scoring lines:

```python
    momentum = 1.0 / (1.0 + np.exp(-_MOMENTUM_GAIN * (cumulative - _MOMENTUM_CENTER)))
    daily_vol = float(arr.std())
    vol_score = max(0.0, min(1.0, 1.0 - daily_vol * _VOL_PENALTY))
```

Run the tests; if `test_flat_performer_stays_below_the_floor` and the strong-performer test cannot both pass, adjust `_MOMENTUM_CENTER` upward (widening the gap) before touching `_MOMENTUM_GAIN`. Record the final values in the constant comment.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/discovery/test_factor_score.py -v -p no:randomly`
Expected: PASS — 4 passed

- [ ] **Step 5: Check for regressions in dependent tests**

Run: `uv run pytest tests/unit/discovery tests/unit/scoring/discovery -q`
Expected: no new failures. `tests/unit/scoring/discovery/` has 7 test files; 6 use `mocker`.

- [ ] **Step 6: Commit**

```bash
git add src/finwiz/discovery/market_data.py tests/unit/discovery/test_factor_score.py
git commit -m "fix(discovery): calibrate factor score so strong candidates can reach the actionable floor"
```

---

## Task 14: Fix the cache-metadata race

`DataProcessor.save_cache_metadata` at `src/finwiz/quantitative/data_processors.py:132-138` serializes a dict it does not own while another thread mutates it:

```python
    def save_cache_metadata(self, cache_metadata: dict[str, Any], cache_metadata_file: Path) -> None:
        """Save cache metadata to disk."""
        try:
            with open(cache_metadata_file, "w") as f:
                json.dump(cache_metadata, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving cache metadata: {e}")
```

Two occurrences on 2026-08-15. Every one silently loses a cache write — and a cold cache is exactly what turns a Perplexity rate-limit into a dead holding (Tasks 2-3). The `json.dump` also omits `default=str`, violating the project rule.

**Files:**

- Modify: `src/finwiz/quantitative/data_processors.py:132-138`
- Test: `tests/unit/quantitative/test_cache_metadata.py`

**Interfaces:**

- Produces: `DataProcessor.save_cache_metadata(cache_metadata: dict[str, Any], cache_metadata_file: Path) -> None` — unchanged signature.

- [ ] **Step 1: Write the failing test**

Create `tests/unit/quantitative/test_cache_metadata.py`:

```python
"""Cache metadata saving must tolerate concurrent mutation of the caller's dict."""

import json
import threading

from finwiz.quantitative.config import QuantConfig
from finwiz.quantitative.data_processors import DataProcessor


def test_save_survives_concurrent_mutation(tmp_path):
    processor = DataProcessor(QuantConfig())
    metadata = {f"seed{i}": i for i in range(500)}
    target = tmp_path / "cache_metadata.json"
    stop = threading.Event()
    errors: list[BaseException] = []

    def churn():
        i = 0
        while not stop.is_set():
            metadata[f"k{i}"] = i
            i += 1

    writer = threading.Thread(target=churn, daemon=True)
    writer.start()
    try:
        for _ in range(50):
            try:
                processor.save_cache_metadata(metadata, target)
            except BaseException as exc:  # noqa: BLE001 - the test is the assertion
                errors.append(exc)
    finally:
        stop.set()
        writer.join(timeout=2.0)

    assert errors == []
    assert json.loads(target.read_text(encoding="utf-8"))


def test_non_serializable_values_do_not_break_the_save(tmp_path):
    from datetime import datetime

    processor = DataProcessor(QuantConfig())
    target = tmp_path / "cache_metadata.json"

    processor.save_cache_metadata({"fetched_at": datetime.now()}, target)

    assert "fetched_at" in json.loads(target.read_text(encoding="utf-8"))
```

`QuantConfig()` may require arguments — read `src/finwiz/quantitative/config.py` and construct it however that module expects. If it needs a populated config, use the existing `tests/unit/quantitative/conftest.py` (28 lines) fixture instead.

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/quantitative/test_cache_metadata.py -v -p no:randomly`
Expected: FAIL — the first test's `errors` list is non-empty, or the file is truncated; the second raises `TypeError: Object of type datetime is not JSON serializable` (currently swallowed into a log line, leaving no file at all).

- [ ] **Step 3: Write minimal implementation**

Replace lines 132-138:

```python
    def save_cache_metadata(self, cache_metadata: dict[str, Any], cache_metadata_file: Path) -> None:
        """Save cache metadata to disk.

        The caller owns ``cache_metadata`` and may mutate it from another thread,
        so snapshot before serializing — iterating the live dict raised
        "dictionary changed size during iteration" and silently dropped the write.
        """
        try:
            snapshot = dict(cache_metadata)
            with open(cache_metadata_file, "w") as f:
                json.dump(snapshot, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Error saving cache metadata: {e}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/quantitative/test_cache_metadata.py -v -p no:randomly`
Expected: PASS — 2 passed

Note: `dict(cache_metadata)` is itself an iteration and can still race in principle. It is a single C-level copy rather than an interleaved serialization, which closes the observed window. If the test still flakes, the caller must own a lock — find it via `grep -rn "save_cache_metadata" src/` and add the lock there.

- [ ] **Step 5: Commit**

```bash
git add src/finwiz/quantitative/data_processors.py tests/unit/quantitative/test_cache_metadata.py
git commit -m "fix(quantitative): snapshot cache metadata before serializing"
```

---

## Task 15: Fix the out-of-bounds indexing in quantitative analysis

Confirmed in the 2026-08-15 run: `index N is out of bounds for axis 0 with size N` twice in `tools/quantitative_comprehensive_analyzer.py` and twice in `quantitative/backtesting.py`, plus one `list index out of range`. Each one drops a holding's whole quantitative payload — which is where `volatility` comes from — so these feed the Task 4/5 cluster directly.

`quantitative_comprehensive_analyzer.py:104` catches every one with a bare `except Exception` and logs `Error in comprehensive analysis: {e}`, so the crash site is not in the log. It must be located by reproduction.

**Do not** also chase `cannot convert float NaN to integer` or the `_QualitativeInsightsRaw` failures — those are 2026-07-15 only. See "Known-Broken Ground".

**Files:**

- Modify: `src/finwiz/tools/quantitative_comprehensive_analyzer.py`, `src/finwiz/quantitative/backtesting.py`
- Test: `tests/unit/quantitative/test_short_series_handling.py`

- [ ] **Step 1: Reproduce with a real traceback**

The bare `except Exception` hides the frame. Temporarily re-raise to find it:

```bash
uv run python - <<'EOF'
import logging, traceback
logging.basicConfig(level=logging.DEBUG)

from finwiz.quantitative.backtesting import BacktestingEngine
import pandas as pd

# A frame far shorter than the strategy's lookback window — the shape that
# produced "index N is out of bounds for axis 0 with size N" in the real run.
short = pd.DataFrame(
    {"Open": [1.0, 1.1], "High": [1.2, 1.3], "Low": [0.9, 1.0], "Close": [1.05, 1.15], "Volume": [100, 120]},
    index=pd.date_range("2026-01-01", periods=2),
)
engine = BacktestingEngine()
try:
    engine.run_strategy_backtest(data=short, symbol="TEST")
except Exception:
    traceback.print_exc()
EOF
```

Adjust the `run_strategy_backtest` call to its real signature (read it first). Record the file:line the traceback names — that is the site to guard.

- [ ] **Step 2: Write the failing test**

Create `tests/unit/quantitative/test_short_series_handling.py`, using the file:line found in Step 1 to target the right entry point:

```python
"""Quantitative analysis must degrade on short series, not crash."""

import pandas as pd
import pytest

from finwiz.quantitative.backtesting import BacktestingEngine


def _frame(rows: int) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Open": [1.0 + i * 0.01 for i in range(rows)],
            "High": [1.2 + i * 0.01 for i in range(rows)],
            "Low": [0.9 + i * 0.01 for i in range(rows)],
            "Close": [1.05 + i * 0.01 for i in range(rows)],
            "Volume": [100 + i for i in range(rows)],
        },
        index=pd.date_range("2026-01-01", periods=rows),
    )


@pytest.mark.parametrize("rows", [0, 1, 2, 5, 20])
def test_short_series_returns_a_result_or_none_but_never_raises(rows):
    engine = BacktestingEngine()

    result = engine.run_strategy_backtest(data=_frame(rows), symbol="TEST")

    assert result is None or hasattr(result, "total_return")


def test_sufficient_series_still_produces_a_backtest():
    engine = BacktestingEngine()

    result = engine.run_strategy_backtest(data=_frame(300), symbol="TEST")

    assert result is not None
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/unit/quantitative/test_short_series_handling.py -v -p no:randomly`
Expected: FAIL — `IndexError: index N is out of bounds for axis 0 with size N` on the small `rows` cases.

- [ ] **Step 4: Write minimal implementation**

At the site found in Step 1, guard the length before indexing and return `None` when the series is too short:

```python
        if data is None or len(data) < self.MIN_BARS_FOR_BACKTEST:
            logger.info("Skipping backtest for %s: %d bars, need %d", symbol, 0 if data is None else len(data), self.MIN_BARS_FOR_BACKTEST)
            return None
```

Define `MIN_BARS_FOR_BACKTEST` from the strategy's longest lookback (`SimpleMovingAverageStrategy` uses a slow MA — read its period and use that, plus one bar). Return `None`, never a zero-filled result: a metric that could not be computed must stay absent so the critical-field gate and Plan B's `Evidence` can see the gap.

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/unit/quantitative -q`
Expected: PASS — no failures.

- [ ] **Step 6: Commit**

```bash
git add src/finwiz/tools/quantitative_comprehensive_analyzer.py src/finwiz/quantitative/backtesting.py tests/unit/quantitative/test_short_series_handling.py
git commit -m "fix(quantitative): skip backtests on series shorter than the strategy lookback"
```

---

## Task 16: Full-run verification

Everything above is unit-tested against fixtures. This task proves it on the real pipeline — the only way to verify the coverage claim.

- [ ] **Step 1: Run the full quality gate**

Run: `make check`
Expected: lint, tests, unittest.mock check, docs validation, complexity and dead-code all pass.

Note: `make check` invokes the docs-validation hook, which runs `uv sync` and can drop the `docs` dependency group. If `mkdocs` then fails with `No module named 'mermaid2'`, restore with `uv sync --group docs`.

- [ ] **Step 2: Run the real flow**

Run: `crewai flow kickoff`
Expected: completes without an unhandled exception.

- [ ] **Step 3: Verify coverage from the ledger, not from the report**

```bash
python3 - <<'EOF'
import json, glob, os, collections
f = max(glob.glob('output/run_ledger/*.jsonl'), key=os.path.getmtime)
rows = [json.loads(l) for l in open(f) if l.strip()]
print(f, len(rows))
print(collections.Counter((r['stage'], r['outcome']) for r in rows))
failed = {r['ticker'] for r in rows if r['outcome'] == 'failed'}
print('failed tickers:', len(failed), sorted(failed))
EOF
```

Expected: `('emit', 'ok')` count equals the total ticker count minus genuinely-delisted names. The 2026-08-15 baseline was 39 emitted of 64, with 25 failed. Any remaining failure must be a delisted ticker (`XTSLA`, `UNI-USD`, `POL-USD`, `S-USD`, `IMX-USD`, `GRT-USD`, `COMP-USD`) and must appear by name.

- [ ] **Step 4: Verify discovery actually searched**

```bash
grep -E "Universe for (stock|etf|crypto)|filter_actionable_candidates" logs/finwiz.log | tail -10
cat output/discovery/scored_etf.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d['scored']), 'scored,', d['actionable_count'], 'actionable')"
```

Expected: each universe ≥50 tickers (or a logged shortfall). `scored_*.json` exists and is non-empty. A zero actionable count is now an honest finding backed by a visible scored list — not an unexplained "0".

- [ ] **Step 5: Verify no fabricated tickers reached the artifacts**

```bash
grep -l "VTI\|VXUS\|BND" output/discovery/a_plus_*.json || echo "clean: no fabricated tickers"
```

Expected: `clean: no fabricated tickers`.

- [ ] **Step 6: Commit the verification evidence**

```bash
git add -A
git commit -m "chore: record full-run coverage verification for the pipeline plan"
```

---

## Done when

- `make check` passes.
- A real `crewai flow kickoff` emits for every ticker except genuinely-delisted ones, and those are named.
- No `TransientStageError: fact_pack unavailable` for a ticker with a reachable Perplexity endpoint and any cache entry under 90 days old.
- No `Error saving cache metadata` and no `index N is out of bounds` in `grep "$(date +%Y-%m-%d)" logs/finwiz_error.log`.
- No `CriticalFieldError` naming `volatility` for any ticker whose `price_history` is present.
- Every asset class searched a universe of ≥50 candidates, or logged why it could not.
- `output/discovery/scored_*.json` exists, so a zero-opportunity result is backed by a visible scored list.
- `grep -r "discovery_latest.json" src/` returns nothing.
- `grep -r "VTI\|VXUS\|BND" src/finwiz/scoring/*_analyzer.py` returns nothing.

## Not in this plan

Spec §1, §2, §3 and §5 — the two-artifact split, view models and `Evidence`, the qualitative `verdict`/`detail` contract, and cost truth — are Plan B. Plan B is written after this plan executes, so its fixtures come from a full-coverage run rather than the degraded 39/64 one.
