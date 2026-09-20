"""strategic_research must route every research call through research_with_retry.

The 2026-08-16 end-to-end run hit Perplexity 429s eight times against the
strategic frameworks and lost both for two holdings (DIS, ORCL), because
``strategic_research.py`` called the client directly instead of going through
the retry wrapper. The wrapper is now ``research_with_retry`` (OpenRouter
primary, Perplexity fallback); the invariant is the same: no direct client call.
"""

from __future__ import annotations

import pytest

from finwiz.infrastructure.research.openrouter_structured import ResearchResult

_CLIENT = "finwiz.infrastructure.resilience.research_retry.openrouter_structured"
_SEAM = "finwiz.analysis.strategic_research.research_with_retry"


def _wrap(model):
    return ResearchResult(data=model, citations=(), cost_usd=0.01, prompt_tokens=1, completion_tokens=1)


@pytest.mark.asyncio
async def test_a_transient_failure_does_not_lose_a_framework(mocker, monkeypatch):
    """One failed attempt then success must yield the analysis, not None."""
    from finwiz.analysis import strategic_research

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    calls = {"n": 0}

    async def flaky(*, prompt, schema, system, **kw):
        calls["n"] += 1
        if calls["n"] <= 2:  # first attempt of each of the two frameworks
            return None
        return _wrap(schema.model_construct(strategic_score=0.6, confidence=0.7))

    mocker.patch(_CLIENT, side_effect=flaky)
    mocker.patch("finwiz.infrastructure.resilience.research_retry.PerplexityFallbackManager.calculate_backoff_delay", return_value=0.0)

    result = await strategic_research.gather_strategic_analysis(ticker="ORCL", sector="Tech", industry="Software", description="desc")

    assert result is not None
    assert calls["n"] > 2


@pytest.mark.asyncio
async def test_strategic_calls_go_through_the_retry_wrapper(mocker):
    """Regression: a direct client import bypassed retry and throttle."""
    from finwiz.analysis import strategic_research

    wrapper = mocker.patch(_SEAM, new=mocker.AsyncMock(return_value=None))

    await strategic_research.gather_strategic_analysis(ticker="ORCL", sector="Tech", industry="Software", description="desc")

    assert wrapper.await_count == 2
    assert sorted(c.kwargs["kind"] for c in wrapper.await_args_list) == ["porter", "swot"]


@pytest.mark.asyncio
async def test_frameworks_are_unwrapped_from_the_research_result(mocker):
    from finwiz.analysis import strategic_research
    from finwiz.schemas.hybrid_analysis.strategic import FiveForcesAnalysis, SwotAnalysis

    async def answer(*, schema, **kw):
        return _wrap(schema.model_construct(strategic_score=0.6, confidence=0.7))

    mocker.patch(_SEAM, side_effect=answer)

    result = await strategic_research.gather_strategic_analysis(ticker="ORCL")

    assert result is not None
    assert isinstance(result.swot, SwotAnalysis)
    assert isinstance(result.five_forces, FiveForcesAnalysis)


@pytest.mark.asyncio
async def test_portfolio_posture_uses_kind_posture_and_unwraps(mocker):
    from finwiz.analysis import strategic_research
    from finwiz.schemas.hybrid_analysis.strategic import PortfolioPostureNarrative, StrategicAnalysis, SwotAnalysis

    narrative = PortfolioPostureNarrative(competitive_verdict="Position concurrentielle solide.", swot_verdict="Forces dominantes.", strategic_score=0.5, confidence=0.5)
    wrapper = mocker.patch(_SEAM, new=mocker.AsyncMock(return_value=_wrap(narrative)))
    holdings = {"ORCL": StrategicAnalysis(swot=SwotAnalysis(strategic_score=0.6, confidence=0.7), five_forces=None)}

    posture = await strategic_research.synthesize_portfolio_posture(holdings, holdings_covered=1, holdings_total=1, value_covered_pct=100.0)

    assert wrapper.await_args.kwargs["kind"] == "posture"
    assert posture is not None
    assert posture.holdings_covered == 1
