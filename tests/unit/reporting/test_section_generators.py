"""Tests for the confidence badge and holding-row rendering in section_generators."""

from finwiz.reporting.section_generators import _confidence_badge, _render_holding_row
from finwiz.schemas.common import RiskAssessmentStandardized
from finwiz.schemas.portfolio_review import HoldingDecision


def _make_risk() -> RiskAssessmentStandardized:
    return RiskAssessmentStandardized(score=2.5, level="Medium")


def _build_holding(grade: str, confidence: str) -> HoldingDecision:
    """Build a minimal valid HoldingDecision with the requested grade and confidence."""
    return HoldingDecision(
        ticker="AAPL",
        name="Apple Inc.",
        asset_class="stock",
        currency="USD",
        decision="KEEP",
        composite_score=0.7,
        grade=grade,
        grade_description=f"Grade {grade}",
        recommended_action="HOLD",
        risk=_make_risk(),
        confidence=confidence,
    )


def test_holding_row_renders_amber_badge_when_confidence_low() -> None:
    """When confidence is low, the row HTML contains the 'Insight IA indisponible' badge."""
    holding = _build_holding(grade="B", confidence="low")
    html = _render_holding_row(holding)
    assert "Insight IA indisponible" in html
    assert "badge-amber" in html


def test_holding_row_no_badge_for_high_confidence() -> None:
    """When confidence is high, no amber badge is rendered."""
    holding = _build_holding(grade="A", confidence="high")
    html = _render_holding_row(holding)
    assert "Insight IA indisponible" not in html
    assert "badge-amber" not in html


def test_pending_holding_row_never_renders_amber_badge() -> None:
    """Grade N/A (pending) rows never show the amber badge — they show 'Analyse en attente'."""
    holding = _build_holding(grade="N/A", confidence="low")
    html = _render_holding_row(holding)
    assert "Analyse en attente" in html
    assert "badge-amber" not in html


def test_confidence_badge_returns_empty_for_high() -> None:
    """_confidence_badge returns empty string for high-confidence holdings."""
    holding = _build_holding(grade="A", confidence="high")
    assert _confidence_badge(holding) == ""


def test_confidence_badge_returns_html_for_low() -> None:
    """_confidence_badge returns non-empty HTML for low-confidence holdings."""
    holding = _build_holding(grade="B", confidence="low")
    badge = _confidence_badge(holding)
    assert "badge-amber" in badge
    assert "Insight IA indisponible" in badge
