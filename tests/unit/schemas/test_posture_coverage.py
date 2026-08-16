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
        "macro_verdict": "Macro favorable dans l'ensemble.",
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
            macro_verdict="m",
            competitive_verdict="c",
            swot_verdict="s",
        )


def test_confidence_has_no_plausible_default():
    with pytest.raises(ValidationError):
        PortfolioStrategicPosture(
            holdings_covered=64,
            holdings_total=64,
            value_covered_pct=100.0,
            macro_verdict="m",
            competitive_verdict="c",
            swot_verdict="s",
            strategic_score=0.71,
        )


def test_verdicts_are_required():
    """The three one-sentence verdicts must not be silently omitted."""
    kwargs = _valid_kwargs()
    del kwargs["macro_verdict"]
    with pytest.raises(ValidationError):
        PortfolioStrategicPosture(**kwargs)


def test_overlong_verdict_is_truncated_not_rejected():
    """A 201+ char verdict must be clamped, never cost the whole posture.

    max_length would raise ValidationError on one over-long sentence and lose
    every field of the synthesis — the single most expensive call in the run.
    """
    posture = PortfolioStrategicPosture(
        **_valid_kwargs(
            macro_verdict="m" * 250,
            competitive_verdict="c" * 250,
            swot_verdict="s" * 250,
        )
    )
    assert len(posture.macro_verdict) == MAX_VERDICT_CHARS
    assert len(posture.competitive_verdict) == MAX_VERDICT_CHARS
    assert len(posture.swot_verdict) == MAX_VERDICT_CHARS


def test_portfolio_prose_fields_are_clamped():
    """The wall-of-prose symptom the user opened this work with, capped."""
    posture = PortfolioStrategicPosture(
        **_valid_kwargs(
            macro_environment_summary="a" * 5000,
            competitive_landscape_summary="b" * 5000,
            overall_assessment="c" * 5000,
        )
    )
    assert len(posture.macro_environment_summary) <= MAX_PORTFOLIO_PROSE_CHARS
    assert len(posture.competitive_landscape_summary) <= MAX_PORTFOLIO_PROSE_CHARS
    assert len(posture.overall_assessment) <= MAX_PORTFOLIO_PROSE_CHARS


def test_uncovered_tickers_defaults_to_empty_list():
    posture = PortfolioStrategicPosture(**_valid_kwargs())
    assert posture.uncovered_tickers == []


def test_uncovered_tickers_can_be_named():
    posture = PortfolioStrategicPosture(**_valid_kwargs(uncovered_tickers=["MSFT", "TSLA"]))
    assert posture.uncovered_tickers == ["MSFT", "TSLA"]


def test_valid_posture_constructs():
    posture = PortfolioStrategicPosture(**_valid_kwargs())
    assert posture.holdings_covered == 64
    assert posture.holdings_total == 64
    assert posture.value_covered_pct == 100.0
    assert posture.strategic_score == 0.71
    assert posture.confidence == 0.83
