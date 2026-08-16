"""Tests for the Perplexity retry wrapper."""

import asyncio
import importlib
import threading

import pytest
from pydantic import BaseModel

from finwiz.infrastructure.resilience import perplexity_retry
from finwiz.infrastructure.resilience.perplexity_retry import (
    get_perplexity_semaphore,
    perplexity_with_retry,
)


def _reload_with_env(monkeypatch, value: str | None) -> None:
    """Reload perplexity_retry with PERPLEXITY_CONCURRENCY set to `value` (or unset).

    PERPLEXITY_CONCURRENCY is computed once at import time, so observing how a
    given env value resolves requires re-executing the module -- following the
    same pattern as test_timeout_headroom.py's CREW_TIMEOUT reload.
    """
    if value is None:
        monkeypatch.delenv("PERPLEXITY_CONCURRENCY", raising=False)
    else:
        monkeypatch.setenv("PERPLEXITY_CONCURRENCY", value)
    importlib.reload(perplexity_retry)


class _Payload(BaseModel):
    value: str


@pytest.fixture(autouse=True)
def _placeholder_api_key(monkeypatch):
    """Give every test in this module a placeholder Perplexity key.

    ``perplexity_with_retry`` short-circuits before its first attempt when
    neither PERPLEXITY_API_KEY nor PPLX_API_KEY is set, so the retry, backoff and
    throttle tests all need one present. They used to inherit it from the
    developer's ambient environment, which made this file red on any machine
    without it -- CI, a fresh clone. Pinning both names here makes the module
    independent of the environment in either direction: no real key is ever
    needed, and an ambient one can never change what these tests exercise.

    A test that wants the no-key path deletes these itself; ``monkeypatch`` is
    the same function-scoped instance, so the test's own call wins.
    """
    monkeypatch.setenv("PERPLEXITY_API_KEY", "test-perplexity-key")
    monkeypatch.delenv("PPLX_API_KEY", raising=False)


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
    # The wrapper delegates backoff math to PerplexityFallbackManager.calculate_backoff_delay
    # (src/finwiz/tools/perplexity_errors.py), which jitters via `random.random()` inside its
    # own local `import random` -- not `random.uniform`. Patching the real `random.random` to
    # 0.5 zeros the +/-25% jitter term (2 * 0.5 - 1 == 0), leaving pure base_delay * 2**attempt.
    inner = mocker.patch(
        "finwiz.infrastructure.resilience.perplexity_retry.perplexity_structured",
        new=mocker.AsyncMock(side_effect=[None, None, _Payload(value="late")]),
    )
    sleep = mocker.patch("finwiz.infrastructure.resilience.perplexity_retry.asyncio.sleep", new=mocker.AsyncMock())
    mocker.patch("random.random", return_value=0.5)

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
async def test_retries_and_returns_none_when_call_raises(mocker):
    # The vendored client's own try/except covers most failures, but a missing-key
    # ValueError from require_api_key() escapes it (raised before that try starts),
    # and any other unexpected raise outside its internal handling would too. The
    # wrapper must treat a raise exactly like a None result: retry, then give up
    # cleanly, never propagate.
    inner = mocker.patch(
        "finwiz.infrastructure.resilience.perplexity_retry.perplexity_structured",
        new=mocker.AsyncMock(side_effect=ValueError("boom")),
    )
    sleep = mocker.patch("finwiz.infrastructure.resilience.perplexity_retry.asyncio.sleep", new=mocker.AsyncMock())

    result = await perplexity_with_retry(prompt="p", schema=_Payload, system="s", max_attempts=3)

    assert result is None
    assert inner.await_count == 3
    assert sleep.await_count == 2


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


class TestConcurrencyFloor:
    """PERPLEXITY_CONCURRENCY must never resolve to a value that breaks the throttle.

    0 makes BoundedSemaphore(0).acquire(blocking=False) always return False, so
    _throttle_slot()'s poll loop spins forever with no timeout. A negative value
    raises ValueError out of BoundedSemaphore's own constructor, which the retry
    wrapper's broad `except Exception` launders into a generic per-holding
    failure instead of surfacing the real (config) cause. Both must be floored
    to 1 instead.
    """

    def test_zero_is_floored_to_one(self, monkeypatch):
        try:
            _reload_with_env(monkeypatch, "0")
            assert perplexity_retry.PERPLEXITY_CONCURRENCY == 1
        finally:
            _reload_with_env(monkeypatch, None)

    def test_negative_is_floored_to_one(self, monkeypatch):
        try:
            _reload_with_env(monkeypatch, "-3")
            assert perplexity_retry.PERPLEXITY_CONCURRENCY == 1
        finally:
            _reload_with_env(monkeypatch, None)

    def test_default_is_unaffected(self, monkeypatch):
        """A sane value (including the unset default) is not clamped away."""
        try:
            _reload_with_env(monkeypatch, None)
            assert perplexity_retry.PERPLEXITY_CONCURRENCY == 4
        finally:
            _reload_with_env(monkeypatch, None)


def test_throttle_is_a_loop_agnostic_process_singleton():
    # Replaces the former `test_semaphore_is_a_process_singleton`, which asserted the
    # throttle was an `asyncio.Semaphore`. That is the very property that broke it:
    # an asyncio primitive binds to the first event loop that contends on it and
    # raises RuntimeError for every other one. Production runs one holding per
    # worker thread, each on its own fresh loop (deep_analysis_orchestrator ->
    # run_in_executor -> fetch_fact_pack_sync -> asyncio.run), so the throttle must
    # be a plain threading primitive that belongs to no loop at all.
    assert get_perplexity_semaphore() is get_perplexity_semaphore()
    assert isinstance(get_perplexity_semaphore(), threading.BoundedSemaphore)


def test_throttle_caps_concurrent_calls_across_independent_event_loops(mocker, monkeypatch):
    """More threads than the cap, each on its own loop: no RuntimeError, real ceiling.

    This is the production topology at production numbers: the deep-analysis
    orchestrator hands each holding to a ThreadPoolExecutor worker, the worker has
    no running loop, so ``fetch_fact_pack_sync`` takes its bare ``asyncio.run``
    branch -- a fresh event loop per holding, per thread. A loop-bound throttle
    fails every thread but the first with a swallowed ``RuntimeError`` (which the
    wrapper logs as an attempt failure and turns into a ``None`` result) and can
    park a thread forever on a future belonging to a dead loop.
    """
    cap = 4  # PERPLEXITY_CONCURRENCY's production default.
    monkeypatch.setattr(perplexity_retry, "PERPLEXITY_CONCURRENCY", cap)
    monkeypatch.setattr(perplexity_retry, "_throttle", None)

    thread_count = cap + 2
    lock = threading.Lock()
    state = {"in_flight": 0, "max_in_flight": 0}
    reached_cap = threading.Event()
    warnings: list[str] = []

    async def fake_call(**_kwargs):
        with lock:
            state["in_flight"] += 1
            state["max_in_flight"] = max(state["max_in_flight"], state["in_flight"])
            if state["in_flight"] >= cap:
                reached_cap.set()
        try:
            # Hold the slot until `cap` calls are genuinely concurrent, so the observed
            # ceiling is deterministic instead of a timing race. Off-loop so a waiting
            # task on this thread's loop is never blocked by a holder on it.
            await asyncio.to_thread(reached_cap.wait, 5.0)
            return _Payload(value="ok")
        finally:
            with lock:
                state["in_flight"] -= 1

    mocker.patch.object(perplexity_retry, "perplexity_structured", new=fake_call)
    mocker.patch.object(perplexity_retry.logger, "warning", new=lambda msg, *a, **k: warnings.append(str(msg)))

    results: list[object] = []

    def worker() -> None:
        results.append(asyncio.run(perplexity_with_retry(prompt="p", schema=_Payload, system="s", max_attempts=1)))

    # daemon=True so a thread parked on a dead loop's future cannot wedge the suite.
    threads = [threading.Thread(target=worker, daemon=True) for _ in range(thread_count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=15.0)

    assert [t.name for t in threads if t.is_alive()] == [], "thread(s) deadlocked inside asyncio.run"
    assert warnings == [], "the throttle made calls fail (the wrapper swallows the raise into a warning)"
    assert results == [_Payload(value="ok")] * thread_count
    assert state["max_in_flight"] == cap, f"expected the throttle to admit exactly {cap} concurrent calls, saw {state['max_in_flight']}"
