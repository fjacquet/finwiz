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


# ---------------------------------------------------------------------------
# XSS hardening (v0.4.1) — defense in depth
# ---------------------------------------------------------------------------


def test_holding_row_escapes_script_tags_in_name() -> None:
    """A name containing a <script> tag must not produce executable HTML."""
    holding = _build_holding(grade="B", confidence="high")
    holding.name = "<script>alert(1)</script>Evil"
    html = _render_holding_row(holding)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_holding_row_escapes_quote_in_rationale() -> None:
    """A rationale with quotes does not break out of a context — use the analyzed branch."""
    holding = _build_holding(grade="B", confidence="high")
    holding.rationale_bullets = ['He said "buy now" <img src=x onerror=alert(1)>']
    html = _render_holding_row(holding)
    assert "<img" not in html
    assert "onerror" not in html or "&" in html  # only as escaped entity
    assert "&lt;img" in html


def test_holding_row_pending_branch_escapes_name() -> None:
    """Pending (N/A) row must also escape the operator-supplied name."""
    holding = _build_holding(grade="N/A", confidence="high")
    holding.name = "<svg/onload=alert(1)>"
    html = _render_holding_row(holding)
    assert "<svg" not in html
    assert "&lt;svg" in html


def test_holding_decision_rejects_malicious_ticker() -> None:
    """Schema field_validator rejects tickers with characters outside [A-Z0-9:.\\-^=]."""
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError) as excinfo:
        HoldingDecision(
            ticker='AAPL" onmouseover="alert(1)',
            name="Apple",
            asset_class="stock",
            currency="USD",
            decision="KEEP",
            composite_score=0.7,
            grade="A",
            grade_description="A",
            recommended_action="HOLD",
            risk=_make_risk(),
            confidence="high",
        )
    assert "ticker" in str(excinfo.value).lower()


def test_holding_decision_accepts_typical_ticker_formats() -> None:
    """Yahoo / Kraken format tickers must still validate (regression)."""
    for ticker in ("AAPL", "BRK.B", "BTC-USD", "^GSPC", "ES=F", "VOO"):
        h = HoldingDecision(
            ticker=ticker,
            name="Test",
            asset_class="stock",
            currency="USD",
            decision="KEEP",
            composite_score=0.7,
            grade="A",
            grade_description="A",
            recommended_action="HOLD",
            risk=_make_risk(),
            confidence="high",
        )
        assert h.ticker == ticker
