"""strategic_research must route every Perplexity call through the retry wrapper.

The 2026-08-16 end-to-end run hit Perplexity 429s eight times against the
strategic frameworks and lost all three for two holdings (DIS, ORCL), because
``strategic_research.py`` called ``perplexity_structured`` directly instead of
going through ``perplexity_with_retry`` — the same wrapper
``fact_pack_research.py`` already uses, which hit 24 transport errors in the
same run and lost nothing. This is a reuse defect: the retry/backoff/
concurrency-throttle infrastructure already existed, strategic research just
didn't call it.
"""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_a_transient_failure_does_not_lose_a_framework(mocker, monkeypatch):
    """One 429 then success must yield the analysis, not None."""
    from finwiz.analysis import strategic_research

    # perplexity_with_retry short-circuits to None when no key is configured, so
    # without this the test asserts nothing on a machine without one and fails on
    # a machine with one removed. PERPLEXITY_API_KEY is not in REQUIRED_API_KEYS,
    # so conftest's isolation fixture does not clear it — it leaked in from the
    # developer's .env via load_dotenv, which is why this passed locally and
    # failed in CI.
    monkeypatch.setenv("PERPLEXITY_API_KEY", "test-perplexity-key-not-a-real-secret")

    calls = {"n": 0}

    async def flaky(*, prompt, schema, system, **kw):
        calls["n"] += 1
        if calls["n"] <= 3:  # first attempt of each of the three frameworks
            return None
        return schema.model_construct(strategic_score=0.6, confidence=0.7)

    mocker.patch("finwiz.infrastructure.resilience.perplexity_retry.perplexity_structured", side_effect=flaky)
    mocker.patch("finwiz.infrastructure.resilience.perplexity_retry.PerplexityFallbackManager.calculate_backoff_delay", return_value=0.0)

    result = await strategic_research.gather_strategic_analysis(ticker="ORCL", sector="Tech", industry="Software", description="desc")

    assert result is not None
    assert calls["n"] > 3  # it retried rather than giving up on the first None


@pytest.mark.asyncio
async def test_strategic_calls_go_through_the_retry_wrapper(mocker):
    """Regression: the direct perplexity_structured import bypassed retry and throttle."""
    from finwiz.analysis import strategic_research

    wrapper = mocker.patch(
        "finwiz.analysis.strategic_research.perplexity_with_retry",
        new=mocker.AsyncMock(return_value=None),
    )

    await strategic_research.gather_strategic_analysis(ticker="ORCL", sector="Tech", industry="Software", description="desc")

    assert wrapper.await_count == 3
    for call in wrapper.await_args_list:
        assert call.kwargs["schema"] is not None
        assert "prompt" in call.kwargs and "system" in call.kwargs
        # Both were deliberate: the recency window keeps the frameworks from
        # citing stale news, and the attempt cap keeps a retry storm inside the
        # holding's remaining 900 s budget. Neither is the wrapper's default.
        assert call.kwargs["search_recency_filter"] == "month"
        assert call.kwargs["max_attempts"] == 3
