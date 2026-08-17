"""Tests for the coverage seam in synthesize_portfolio_posture.

Task 6 made PortfolioStrategicPosture require holdings_covered/holdings_total/
value_covered_pct/uncovered_tickers. An LLM cannot supply those, so
synthesize_portfolio_posture must request only the narrative fields from
Perplexity (PortfolioPostureNarrative) and merge Python-computed coverage in
*before* the full PortfolioStrategicPosture is constructed and validated.
Validating the full schema straight off the LLM response would raise on
every call — the model never has coverage to give.
"""

import pytest

from finwiz.schemas.hybrid_analysis.strategic import (
    FiveForcesAnalysis,
    PestelAnalysis,
    PortfolioPostureNarrative,
    PortfolioStrategicPosture,
    StrategicAnalysis,
    SwotAnalysis,
)


def _one_holding() -> dict[str, StrategicAnalysis]:
    return {
        "AAPL": StrategicAnalysis(
            pestel=PestelAnalysis(strategic_score=0.6, confidence=0.7),
            swot=SwotAnalysis(strategic_score=0.5, confidence=0.6),
            five_forces=FiveForcesAnalysis(strategic_score=0.4, confidence=0.5),
        )
    }


def _narrative(**overrides: object) -> PortfolioPostureNarrative:
    base = {
        "competitive_verdict": "Moats solides.",
        "swot_verdict": "Forces dominantes.",
        "strategic_score": 0.71,
        "confidence": 0.83,
    }
    base.update(overrides)
    return PortfolioPostureNarrative(**base)


@pytest.mark.asyncio
async def test_coverage_is_merged_before_constructing_the_full_posture(mocker):
    """The LLM supplies only narrative fields; Python injects coverage before validation."""
    from finwiz.analysis import strategic_research

    mocker.patch.object(strategic_research, "perplexity_with_retry", new=mocker.AsyncMock(return_value=_narrative()))

    posture = await strategic_research.synthesize_portfolio_posture(
        _one_holding(),
        holdings_covered=1,
        holdings_total=3,
        value_covered_pct=33.3,
        uncovered_tickers=["MSFT", "TSLA"],
    )

    assert isinstance(posture, PortfolioStrategicPosture)
    assert posture.holdings_covered == 1
    assert posture.holdings_total == 3
    assert posture.value_covered_pct == 33.3
    assert posture.uncovered_tickers == ["MSFT", "TSLA"]
    # Narrative fields from the LLM response survive the merge.
    assert posture.strategic_score == 0.71
    assert posture.confidence == 0.83
    assert posture.competitive_verdict == "Moats solides."


@pytest.mark.asyncio
async def test_llm_schema_never_asked_for_coverage(mocker):
    """perplexity_with_retry must be called with the narrative-only schema, not the full posture."""
    from finwiz.analysis import strategic_research

    called = mocker.patch.object(strategic_research, "perplexity_with_retry", new=mocker.AsyncMock(return_value=_narrative()))

    await strategic_research.synthesize_portfolio_posture(
        _one_holding(),
        holdings_covered=1,
        holdings_total=1,
        value_covered_pct=100.0,
    )

    assert called.await_args.kwargs["schema"] is PortfolioPostureNarrative


@pytest.mark.asyncio
async def test_uncovered_tickers_defaults_to_empty_when_omitted(mocker):
    from finwiz.analysis import strategic_research

    mocker.patch.object(strategic_research, "perplexity_with_retry", new=mocker.AsyncMock(return_value=_narrative()))

    posture = await strategic_research.synthesize_portfolio_posture(
        _one_holding(),
        holdings_covered=1,
        holdings_total=1,
        value_covered_pct=100.0,
    )

    assert posture is not None
    assert posture.uncovered_tickers == []


@pytest.mark.asyncio
async def test_returns_none_when_perplexity_returns_none(mocker):
    """A failed/unparseable LLM call must still yield None, not a half-built posture."""
    from finwiz.analysis import strategic_research

    mocker.patch.object(strategic_research, "perplexity_with_retry", new=mocker.AsyncMock(return_value=None))

    posture = await strategic_research.synthesize_portfolio_posture(
        _one_holding(),
        holdings_covered=1,
        holdings_total=1,
        value_covered_pct=100.0,
    )

    assert posture is None


def _analysis(score: float, strength: str, threat: str):
    from finwiz.schemas.hybrid_analysis.strategic import FiveForcesAnalysis, StrategicAnalysis, SwotAnalysis

    return StrategicAnalysis(
        swot=SwotAnalysis(strengths=[strength], threats=[threat], strategic_score=score),
        five_forces=FiveForcesAnalysis(strategic_score=score),
    )


def test_the_payload_is_aggregates_and_extremes_not_every_holding():
    import json

    from finwiz.analysis.strategic_research import _serialize_holdings

    holdings = {f"T{i}": _analysis(i / 100, f"force {i}", f"menace {i}") for i in range(60)}

    payload = json.loads(_serialize_holdings(holdings))

    assert payload["n"] == 60
    assert len(payload["weakest"]) == 5
    assert len(payload["strongest"]) == 5
    assert payload["weakest"][0]["t"] == "T0"
    assert payload["strongest"][-1]["t"] == "T59"
    # The 50 mid-pack holdings are represented by the distribution, not by name.
    assert "T30" not in _serialize_holdings(holdings)


def test_the_payload_does_not_grow_with_portfolio_size():
    from finwiz.analysis.strategic_research import _serialize_holdings

    small = {f"T{i}": _analysis(i / 100, "force", "menace") for i in range(20)}
    large = {f"T{i}": _analysis(i / 200, "force", "menace") for i in range(200)}

    assert len(_serialize_holdings(large)) < 2 * len(_serialize_holdings(small))


def test_an_empty_portfolio_serializes_without_raising():
    import json

    from finwiz.analysis.strategic_research import _serialize_holdings

    payload = json.loads(_serialize_holdings({}))

    assert payload["n"] == 0
    assert payload["weakest"] == []
    assert payload["strongest"] == []
