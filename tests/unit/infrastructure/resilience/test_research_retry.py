"""Retry, throttle, cost recording and Perplexity fallback for research calls."""

from __future__ import annotations

import asyncio
import importlib
import threading
import time

import pytest
from pydantic import BaseModel

from finwiz.infrastructure.monitoring.litellm_callback import TokenMonitorCallback
from finwiz.infrastructure.research.openrouter_structured import Citation, ResearchResult
from finwiz.infrastructure.resilience import research_retry
from finwiz.infrastructure.resilience.research_retry import get_research_semaphore, research_with_retry

_CLIENT = "finwiz.infrastructure.resilience.research_retry.openrouter_structured"
_FALLBACK = "finwiz.infrastructure.resilience.research_retry.perplexity_with_retry"
_SLEEP = "finwiz.infrastructure.resilience.research_retry.asyncio.sleep"
_BACKOFF = "finwiz.infrastructure.resilience.research_retry.PerplexityFallbackManager.calculate_backoff_delay"


class _Payload(BaseModel):
    value: str


def _result(value: str = "ok", cost: float | None = 0.01) -> ResearchResult[_Payload]:
    return ResearchResult(data=_Payload(value=value), citations=(Citation(url="https://a"),), cost_usd=cost, prompt_tokens=100, completion_tokens=50)


@pytest.fixture(autouse=True)
def _keys(monkeypatch):
    """OpenRouter key present, Perplexity keys absent, unless a test says otherwise."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
    monkeypatch.delenv("PPLX_API_KEY", raising=False)


@pytest.fixture
def monitor(mocker) -> TokenMonitorCallback:
    cb = TokenMonitorCallback()
    mocker.patch("finwiz.infrastructure.monitoring.litellm_callback.get_token_monitor", return_value=cb)
    return cb


async def test_first_success_is_returned_and_costed(mocker, monitor):
    client = mocker.patch(_CLIENT, new=mocker.AsyncMock(return_value=_result()))
    sleep = mocker.patch(_SLEEP, new=mocker.AsyncMock())

    result = await research_with_retry(prompt="p", schema=_Payload, system="s", kind="swot")

    assert result == _result()
    assert client.await_count == 1
    assert sleep.await_count == 0
    crew = monitor.get_cost_summary()["per_crew"]["research_swot"]
    assert crew == {"cost": pytest.approx(0.01), "calls": 1, "tokens": {"prompt": 100, "completion": 50}, "cost_known": True}


async def test_recency_filter_is_forwarded_as_the_search_hint(mocker):
    client = mocker.patch(_CLIENT, new=mocker.AsyncMock(return_value=_result()))

    await research_with_retry(prompt="p", schema=_Payload, system="s", search_recency_filter="week", timeout=33.0)

    kwargs = client.await_args.kwargs
    assert kwargs["search"].recency_hint == "week"
    assert kwargs["timeout"] == 33.0
    assert kwargs["prompt"] == "p"
    assert kwargs["system"] == "s"
    assert kwargs["schema"] is _Payload


async def test_three_failures_then_success(mocker):
    client = mocker.patch(_CLIENT, new=mocker.AsyncMock(side_effect=[None, None, None, _result("late")]))
    sleep = mocker.patch(_SLEEP, new=mocker.AsyncMock())
    mocker.patch(_BACKOFF, return_value=0.5)

    result = await research_with_retry(prompt="p", schema=_Payload, system="s")

    assert result is not None and result.data.value == "late"
    assert client.await_count == 4
    assert [c.args[0] for c in sleep.await_args_list] == [0.5, 0.5, 0.5]


async def test_a_raise_counts_as_a_failed_attempt(mocker):
    client = mocker.patch(_CLIENT, new=mocker.AsyncMock(side_effect=RuntimeError("boom")))
    mocker.patch(_SLEEP, new=mocker.AsyncMock())
    fallback = mocker.patch(_FALLBACK, new=mocker.AsyncMock())

    assert await research_with_retry(prompt="p", schema=_Payload, system="s", max_attempts=2) is None
    assert client.await_count == 2
    fallback.assert_not_awaited()


async def test_exhaustion_without_perplexity_key_returns_none(mocker):
    mocker.patch(_CLIENT, new=mocker.AsyncMock(return_value=None))
    mocker.patch(_SLEEP, new=mocker.AsyncMock())
    fallback = mocker.patch(_FALLBACK, new=mocker.AsyncMock())

    assert await research_with_retry(prompt="p", schema=_Payload, system="s", max_attempts=2) is None
    fallback.assert_not_awaited()


async def test_exhaustion_with_perplexity_key_falls_back_once(mocker, monkeypatch, monitor):
    monkeypatch.setenv("PPLX_API_KEY", "test-pplx-key")
    mocker.patch(_CLIENT, new=mocker.AsyncMock(return_value=None))
    mocker.patch(_SLEEP, new=mocker.AsyncMock())
    fallback = mocker.patch(_FALLBACK, new=mocker.AsyncMock(return_value=_Payload(value="pplx")))

    result = await research_with_retry(prompt="p", schema=_Payload, system="s", search_recency_filter="week", timeout=20.0, max_attempts=2, kind="porter")

    assert result == ResearchResult(data=_Payload(value="pplx"), citations=(), cost_usd=None, prompt_tokens=0, completion_tokens=0)
    fallback.assert_awaited_once_with(prompt="p", schema=_Payload, system="s", search_recency_filter="week", timeout=20.0, max_attempts=1)
    crew = monitor.get_cost_summary()["per_crew"]["research_porter"]
    assert crew["calls"] == 1
    assert crew["cost_known"] is False


async def test_fallback_none_is_none(mocker, monkeypatch):
    monkeypatch.setenv("PERPLEXITY_API_KEY", "test-pplx-key")
    mocker.patch(_CLIENT, new=mocker.AsyncMock(return_value=None))
    mocker.patch(_SLEEP, new=mocker.AsyncMock())
    mocker.patch(_FALLBACK, new=mocker.AsyncMock(return_value=None))

    assert await research_with_retry(prompt="p", schema=_Payload, system="s", max_attempts=1) is None


async def test_no_openrouter_key_skips_straight_to_fallback(mocker, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("PPLX_API_KEY", "test-pplx-key")
    client = mocker.patch(_CLIENT, new=mocker.AsyncMock())
    fallback = mocker.patch(_FALLBACK, new=mocker.AsyncMock(return_value=_Payload(value="pplx")))

    result = await research_with_retry(prompt="p", schema=_Payload, system="s")

    assert result is not None and result.data.value == "pplx"
    client.assert_not_awaited()
    fallback.assert_awaited_once()


async def test_cost_recording_failure_never_breaks_the_call(mocker):
    mocker.patch(_CLIENT, new=mocker.AsyncMock(return_value=_result()))
    mocker.patch("finwiz.infrastructure.monitoring.litellm_callback.get_token_monitor", side_effect=RuntimeError("monitor down"))

    assert await research_with_retry(prompt="p", schema=_Payload, system="s") == _result()


class TestConcurrencyFloor:
    def _reload(self, monkeypatch, value: str | None) -> None:
        if value is None:
            monkeypatch.delenv("RESEARCH_CONCURRENCY", raising=False)
        else:
            monkeypatch.setenv("RESEARCH_CONCURRENCY", value)
        importlib.reload(research_retry)

    def test_zero_is_floored_to_one(self, monkeypatch):
        try:
            self._reload(monkeypatch, "0")
            assert research_retry.RESEARCH_CONCURRENCY == 1
        finally:
            self._reload(monkeypatch, None)

    def test_default_is_six(self, monkeypatch):
        try:
            self._reload(monkeypatch, None)
            assert research_retry.RESEARCH_CONCURRENCY == 6
        finally:
            self._reload(monkeypatch, None)


def test_throttle_is_a_loop_agnostic_process_singleton():
    assert get_research_semaphore() is get_research_semaphore()
    assert isinstance(get_research_semaphore(), threading.BoundedSemaphore)


def test_a_cap_of_one_serialises_two_threads_on_independent_loops(mocker, monkeypatch):
    """RESEARCH_CONCURRENCY=1: two holdings on two loops never overlap."""
    monkeypatch.setattr(research_retry, "RESEARCH_CONCURRENCY", 1)
    monkeypatch.setattr(research_retry, "_throttle", None)

    lock = threading.Lock()
    state = {"in_flight": 0, "max_in_flight": 0}

    async def fake_call(**_kwargs):
        with lock:
            state["in_flight"] += 1
            state["max_in_flight"] = max(state["max_in_flight"], state["in_flight"])
        try:
            await asyncio.sleep(0.05)
            return _result()
        finally:
            with lock:
                state["in_flight"] -= 1

    mocker.patch.object(research_retry, "openrouter_structured", new=fake_call)
    results: list[object] = []

    def worker() -> None:
        results.append(asyncio.run(research_with_retry(prompt="p", schema=_Payload, system="s", max_attempts=1)))

    threads = [threading.Thread(target=worker, daemon=True) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10.0)

    assert [t.name for t in threads if t.is_alive()] == []
    assert len(results) == 2 and all(r is not None for r in results)
    assert state["max_in_flight"] == 1


async def test_a_cap_of_one_serialises_two_coroutines_on_the_same_loop(mocker, monkeypatch):
    """RESEARCH_CONCURRENCY=1: the asyncio.gather shape gather_strategic_analysis
    uses -- two coroutines contending for one slot on the SAME event loop --
    must not deadlock, and the second call must not enter until the first has
    exited (serialised, not interleaved). Single-threaded, so the shared
    state needs no lock (unlike the cross-thread test above). Wrapped in
    asyncio.wait_for so a `threading.BoundedSemaphore` blocking the loop
    fails the test with a TimeoutError instead of hanging the suite."""
    monkeypatch.setattr(research_retry, "RESEARCH_CONCURRENCY", 1)
    monkeypatch.setattr(research_retry, "_throttle", None)

    events: list[tuple[str, float]] = []
    state = {"in_flight": 0, "max_in_flight": 0}

    async def fake_call(**_kwargs):
        events.append(("enter", time.monotonic()))
        state["in_flight"] += 1
        state["max_in_flight"] = max(state["max_in_flight"], state["in_flight"])
        try:
            await asyncio.sleep(0.05)
            return _result()
        finally:
            state["in_flight"] -= 1
            events.append(("exit", time.monotonic()))

    mocker.patch.object(research_retry, "openrouter_structured", new=fake_call)

    results = await asyncio.wait_for(
        asyncio.gather(
            research_with_retry(prompt="p", schema=_Payload, system="s", max_attempts=1),
            research_with_retry(prompt="p", schema=_Payload, system="s", max_attempts=1),
        ),
        timeout=5,
    )

    assert all(r is not None for r in results)
    assert state["max_in_flight"] == 1
    # Serialised, not interleaved: enter/exit/enter/exit, with the second
    # call's "enter" no earlier than the first call's "exit".
    assert [kind for kind, _ in events] == ["enter", "exit", "enter", "exit"]
    first_exit_at = events[1][1]
    second_enter_at = events[2][1]
    assert second_enter_at >= first_exit_at
