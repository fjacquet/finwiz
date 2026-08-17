"""Tests for PortfolioStrategicPosture's coverage fields and required scores.

The 2026-08-16 report printed "Score Stratégique Global 71% / Confiance 83%"
from a posture synthesized off 1 of 64 holdings. Two defects made that lie
reportable: the schema had no coverage field at all, and strategic_score /
confidence defaulted to 0.5 — a posture built from nothing still reported a
confident midpoint. These tests pin both fixes.
"""

import pytest
from pydantic import ValidationError

from finwiz.schemas.hybrid_analysis.strategic import (
    MAX_PORTFOLIO_PROSE_CHARS,
    MAX_VERDICT_CHARS,
    PortfolioStrategicPosture,
)


def _valid_kwargs(**overrides: object) -> dict:
    base = {
        "holdings_covered": 64,
        "holdings_total": 64,
        "value_covered_pct": 100.0,
        "competitive_verdict": "Moats solides sur la majorité des positions.",
        "swot_verdict": "Forces largement supérieures aux faiblesses.",
        "strategic_score": 0.71,
        "confidence": 0.83,
    }
    base.update(overrides)
    return base


def test_posture_cannot_be_built_without_stating_its_coverage():
    """A portfolio-level number must carry what it covers, inseparably."""
    with pytest.raises(ValidationError):
        PortfolioStrategicPosture(strategic_score=0.71, confidence=0.83)


def test_posture_score_has_no_plausible_default():
    """No score must mean no score — never a confident midpoint."""
    with pytest.raises(ValidationError):
        PortfolioStrategicPosture(
            holdings_covered=64,
            holdings_total=64,
            value_covered_pct=100.0,
            competitive_verdict="c",
            swot_verdict="s",
        )


def test_confidence_has_no_plausible_default():
    with pytest.raises(ValidationError):
        PortfolioStrategicPosture(
            holdings_covered=64,
            holdings_total=64,
            value_covered_pct=100.0,
            competitive_verdict="c",
            swot_verdict="s",
            strategic_score=0.71,
        )


def test_verdicts_are_required():
    """The verdicts must not be silently omitted."""
    kwargs = _valid_kwargs()
    del kwargs["competitive_verdict"]
    with pytest.raises(ValidationError):
        PortfolioStrategicPosture(**kwargs)


def test_overlong_verdict_is_truncated_not_rejected():
    """A 201+ char verdict must be clamped, never cost the whole posture.

    max_length would raise ValidationError on one over-long sentence and lose
    every field of the synthesis — the single most expensive call in the run.
    """
    posture = PortfolioStrategicPosture(
        **_valid_kwargs(
            competitive_verdict="c" * 250,
            swot_verdict="s" * 250,
        )
    )
    assert len(posture.competitive_verdict) == MAX_VERDICT_CHARS
    assert len(posture.swot_verdict) == MAX_VERDICT_CHARS


def test_portfolio_prose_fields_are_clamped():
    """The wall-of-prose symptom the user opened this work with, capped."""
    posture = PortfolioStrategicPosture(
        **_valid_kwargs(
            competitive_landscape_summary="b" * 5000,
            overall_assessment="c" * 5000,
        )
    )
    assert len(posture.competitive_landscape_summary) <= MAX_PORTFOLIO_PROSE_CHARS
    assert len(posture.overall_assessment) <= MAX_PORTFOLIO_PROSE_CHARS


def test_uncovered_tickers_defaults_to_empty_list():
    posture = PortfolioStrategicPosture(**_valid_kwargs())
    assert posture.uncovered_tickers == []


def test_uncovered_tickers_can_be_named():
    # Counts must agree with the named gaps: 62 covered + 2 named = 64 total.
    # This test previously passed 64/64 alongside two named uncovered tickers —
    # a self-contradictory posture the schema now rejects.
    posture = PortfolioStrategicPosture(**_valid_kwargs(holdings_covered=62, uncovered_tickers=["MSFT", "TSLA"]))
    assert posture.uncovered_tickers == ["MSFT", "TSLA"]
    assert posture.holdings_covered == 62


def test_valid_posture_constructs():
    posture = PortfolioStrategicPosture(**_valid_kwargs())
    assert posture.holdings_covered == 64
    assert posture.holdings_total == 64
    assert posture.value_covered_pct == 100.0
    assert posture.strategic_score == 0.71
    assert posture.confidence == 0.83


def test_coverage_counts_must_agree_with_the_named_gaps():
    """A posture cannot claim a coverage count its own gap list contradicts.

    ``holdings_covered`` is derivable — it is always
    ``holdings_total - len(uncovered_tickers)`` — but it is stored, because the
    renderers and the JSON export read it as a field. Storing a derivable value
    lets it drift from the list it summarises. "26 of 64 covered" printed beside
    three named gaps is precisely the quietly-wrong number this schema exists to
    make impossible.
    """
    with pytest.raises(ValidationError, match="coverage counts disagree"):
        PortfolioStrategicPosture(
            **_valid_kwargs(
                holdings_covered=26,
                holdings_total=64,
                uncovered_tickers=["MSFT", "TSLA", "SAP"],
            )
        )


def test_coverage_counts_agree_when_consistent():
    """The identity holding is not an error — 61 covered, 3 named, 64 total."""
    posture = PortfolioStrategicPosture(
        **_valid_kwargs(
            holdings_covered=61,
            holdings_total=64,
            uncovered_tickers=["MSFT", "TSLA", "SAP"],
        )
    )

    assert posture.holdings_covered == 61
    assert len(posture.uncovered_tickers) == 3


def test_unnamed_gaps_are_still_allowed():
    """An empty uncovered_tickers is ambiguous, so the identity is not enforced.

    Either coverage is complete, or the gaps were never enumerated. Rejecting
    the ambiguous case would break callers that legitimately know the counts
    without listing the tickers.
    """
    posture = PortfolioStrategicPosture(**_valid_kwargs(holdings_covered=26, holdings_total=64))

    assert posture.holdings_covered == 26
    assert posture.uncovered_tickers == []


def test_covered_cannot_exceed_total():
    """Coverage above 100% is not a rounding artefact, it is a broken caller."""
    with pytest.raises(ValidationError, match="exceeds holdings_total"):
        PortfolioStrategicPosture(**_valid_kwargs(holdings_covered=65, holdings_total=64))
