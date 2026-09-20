"""fetch_missing_events asks research_with_retry once and never raises."""

from __future__ import annotations

from finwiz.analysis.fact_pack.sources import research_source
from finwiz.analysis.fact_pack_research import _FactPackRaw
from finwiz.infrastructure.research.openrouter_structured import ResearchResult

_SEAM = "finwiz.infrastructure.resilience.research_retry.research_with_retry"


def test_events_are_unwrapped_capped_and_truncated(mocker):
    # _FactPackRaw.recent_events carries its own max_length=10 field constraint
    # (fact_pack_research.py), so a normal constructor call with 12 items would
    # raise ValidationError before this test's assertions -- which exist to
    # verify research_source's OWN _MAX_EVENTS/_EVENT_MAX_CHARS capping, not
    # _FactPackRaw's. model_construct bypasses that field validation so the
    # 12-item, over-length input this test needs actually reaches the module
    # under test.
    raw = _FactPackRaw.model_construct(recent_events=[f"event {i} " + "x" * 300 for i in range(12)])
    wrapper = mocker.patch(_SEAM, new=mocker.AsyncMock(return_value=ResearchResult(data=raw, citations=(), cost_usd=0.01, prompt_tokens=1, completion_tokens=1)))

    events = research_source.fetch_missing_events("AIR.PA", "Airbus SE", "Industrials", "Aerospace")

    assert wrapper.await_args.kwargs["kind"] == "factpack"
    assert wrapper.await_args.kwargs["schema"] is _FactPackRaw
    assert len(events) == 10
    assert all(len(e) <= 200 for e in events)


def test_none_from_research_is_an_empty_tuple(mocker):
    mocker.patch(_SEAM, new=mocker.AsyncMock(return_value=None))

    assert research_source.fetch_missing_events("AIR.PA", "Airbus SE", None, None) == ()


def test_a_raise_is_an_empty_tuple(mocker):
    mocker.patch(_SEAM, new=mocker.AsyncMock(side_effect=RuntimeError("HTTP 401")))

    assert research_source.fetch_missing_events("AIR.PA", "Airbus SE", None, None) == ()


def test_outer_timeout_layers_over_max_attempts_and_backoff(mocker):
    """The outer _run_coroutine_sync cap must exceed the inner budget: up to
    _GAP_FILL_ATTEMPTS OpenRouter attempts at `timeout` each, plus one
    Perplexity fallback attempt of `timeout`, plus backoff between retries
    (the PR #66 timeout-layering lesson: an outer cap shorter than the inner
    budget silently discards completed work while the thread keeps spending).
    """
    retry_mock = mocker.patch(_SEAM, new=mocker.AsyncMock(return_value=None))
    run_sync = mocker.patch("finwiz.analysis.fact_pack_research._run_coroutine_sync", return_value=None)

    research_source.fetch_missing_events("AIR.PA", "Airbus SE", None, None, timeout=15.0)

    assert run_sync.call_args.kwargs["timeout"] == 70.0
    assert retry_mock.call_args.kwargs["max_attempts"] == research_source._GAP_FILL_ATTEMPTS
    # Close the coroutine _run_coroutine_sync was mocked out from under, so it
    # doesn't sit un-awaited.
    run_sync.call_args.args[0].close()
