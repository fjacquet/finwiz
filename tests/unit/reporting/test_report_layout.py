"""Tests for the consolidated report's folded / reordered layout.

Covers the section registry (TOC + anchors + expand/collapse script), the
asset-class grouping of allocation and holdings, the grade buckets of the
quintessence cards, and the folded per-holding stress tables. Deterministic
Python rendering only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from finwiz.reporting.python_report_generator import PythonReportGenerator, _with_anchor
from finwiz.reporting.sections.analysis import generate_stress_test_section
from finwiz.reporting.sections.common import GRADE_ORDER, group_by_asset_class
from finwiz.reporting.sections.holdings import generate_holdings_analysis
from finwiz.reporting.sections.insights import generate_holdings_insight_cards
from finwiz.reporting.sections.portfolio_summary import generate_allocation_section
from finwiz.schemas.common import RiskAssessmentStandardized
from finwiz.schemas.portfolio_review import HoldingDecision, PortfolioReview


def _make_holding(
    ticker: str,
    asset_class: str = "stock",
    grade: str = "B",
    score: float = 0.7,
    weight: float | None = None,
    eur_value: float | None = None,
) -> HoldingDecision:
    return HoldingDecision(
        ticker=ticker,
        name=f"{ticker} Inc.",
        asset_class=asset_class,
        currency="USD",
        decision="KEEP",
        composite_score=score,
        grade=grade,
        grade_description=f"Grade {grade}",
        recommended_action="HOLD",
        risk=RiskAssessmentStandardized(score=2.5, level="Medium"),
        rationale_bullets=["Solid"],
        crew_analysis_used="DeepAnalysisCrew",
        weight=weight,
        eur_value=eur_value,
    )


def _review() -> PortfolioReview:
    holdings = [
        _make_holding("AAPL", "stock", "A", 0.9, weight=0.40, eur_value=4000.0),
        _make_holding("MSFT", "stock", "D", 0.3, weight=0.20, eur_value=2000.0),
        _make_holding("VWCE", "etf", "B", 0.7, weight=0.30, eur_value=3000.0),
        _make_holding("BTC-USD", "crypto", "C", 0.5, weight=0.10, eur_value=1000.0),
    ]
    return PortfolioReview(as_of=datetime.now(), holdings=holdings, total_value_eur=10000.0)


# --- common helpers ---------------------------------------------------------


def test_grade_order_is_worst_first_and_na_last() -> None:
    assert GRADE_ORDER[0] == "F"
    assert GRADE_ORDER[-1] == "N/A"
    assert GRADE_ORDER.index("D") < GRADE_ORDER.index("C") < GRADE_ORDER.index("A+")


def test_group_by_asset_class_keeps_only_present_classes() -> None:
    groups = group_by_asset_class(_review().holdings)
    assert [g.key for g in groups] == ["stock", "etf", "crypto"]
    assert groups[0].label == "Actions"
    assert [h.ticker for h in groups[0].items] == ["AAPL", "MSFT"]


def test_group_by_asset_class_unknown_class_falls_back_to_other_bucket() -> None:
    @dataclass
    class _Loose:
        ticker: str
        asset_class: str | None

    groups = group_by_asset_class([_Loose("X", None), _Loose("Y", "stock")])
    assert [g.key for g in groups] == ["stock", "other"]


# --- allocation -------------------------------------------------------------


def test_allocation_groups_by_asset_class_with_subtotals() -> None:
    html = generate_allocation_section(_review())
    assert html.count('<details class="group"') == 3
    # Class subtotal (weight + EUR) sits in the summary line.
    assert "Actions" in html and "60.0%" in html and "6 000 €" in html
    assert "ETF" in html and "30.0%" in html
    # Groups start closed: the collapsed view is the by-class digest.
    assert '<details class="group" open' not in html


def test_allocation_groups_ordered_by_class_weight_then_rows_by_weight() -> None:
    html = generate_allocation_section(_review())
    # stock (60%) before etf (30%) before crypto (10%); AAPL before MSFT inside stock.
    assert html.index("AAPL") < html.index("MSFT") < html.index("VWCE") < html.index("BTC-USD")


# --- holdings ---------------------------------------------------------------


def test_holdings_table_grouped_by_class_with_recommendation_counts() -> None:
    html = generate_holdings_analysis(_review().holdings)
    assert html.count('<details class="group"') == 3
    # Stock group: AAPL (A -> BUY) + MSFT (D -> SELL).
    assert "1 SELL" in html and "1 BUY" in html
    assert "2 positions" in html
    assert '<details class="group" open' not in html


def test_holdings_table_empty_still_renders_section() -> None:
    html = generate_holdings_analysis([])
    assert "Detailed Holdings Analysis" in html
    assert "<details" not in html


# --- quintessence -----------------------------------------------------------


@dataclass
class _Holding:
    ticker: str
    grade: str


def _insight(rec: str = "HOLD") -> dict:
    return {"thesis": "Thesis text.", "final_recommendation": rec}


def test_quintessence_buckets_by_grade_worst_first_and_opens_worst() -> None:
    insights = {"AAPL": _insight("BUY"), "MSFT": _insight("SELL"), "VWCE": _insight()}
    holdings = [_Holding("AAPL", "A"), _Holding("MSFT", "D"), _Holding("VWCE", "B")]
    html = generate_holdings_insight_cards(insights, holdings)
    assert html.count('<details class="group"') == 3
    d_pos = html.index("Grade D")
    b_pos = html.index("Grade B")
    a_pos = html.index("Grade A")
    assert d_pos < b_pos < a_pos
    # Only the D bucket is open by default.
    assert '<details class="group" open><summary>Grade D' in html
    assert '<details class="group"><summary>Grade B' in html
    assert '<details class="group"><summary>Grade A' in html
    assert "1 position" in html


def test_quintessence_unknown_grade_goes_last() -> None:
    insights = {"ZZZ": _insight(), "MSFT": _insight()}
    holdings = [_Holding("ZZZ", "N/A"), _Holding("MSFT", "C")]
    html = generate_holdings_insight_cards(insights, holdings)
    assert html.index("Grade C") < html.index("Grade N/A")


# --- stress test ------------------------------------------------------------


def test_stress_per_holding_table_is_folded() -> None:
    result = {
        "scenario": {"name": "Crash", "description": "d"},
        "total_portfolio_impact_pct": -0.1,
        "total_projected_pnl": -100.0,
        "holding_impacts": [{"ticker": "AAPL", "sector": "Tech", "beta": 1.0, "projected_change_pct": -0.2, "sensitivity_label": "HIGH"}],
        "most_affected": ["AAPL"],
        "least_affected": [],
    }
    html = generate_stress_test_section([result])
    assert "<details><summary>Impact par position (1)</summary>" in html
    assert "AAPL" in html


# --- registry / TOC ---------------------------------------------------------


def test_with_anchor_tags_first_section_div_only() -> None:
    html = '<div class="section"><h2>A</h2></div><div class="section"><h2>B</h2></div>'
    out = _with_anchor(html, "alpha")
    assert out.count('id="alpha"') == 1
    assert out.startswith('<div class="section" id="alpha">')


def test_with_anchor_leaves_empty_fragment_empty() -> None:
    assert _with_anchor("  \n", "alpha") == "  \n"


def _render(tmp_path, **kwargs) -> str:
    gen = PythonReportGenerator(output_dir=str(tmp_path))
    gen.generate_family_financial_plan(portfolio_review=_review(), **kwargs)
    return (tmp_path / "finwiz_family_financial_plan.html").read_text(encoding="utf-8")


def test_toc_lists_only_rendered_sections(tmp_path) -> None:
    html = _render(tmp_path)  # no sentiment, no stress, no insights
    assert '<nav class="toc"' in html
    assert 'href="#allocation"' in html and 'id="allocation"' in html
    assert 'href="#holdings"' in html and 'id="holdings"' in html
    assert 'href="#sentiment"' not in html
    assert 'href="#quintessence"' not in html


def test_toc_includes_sentiment_when_rendered(tmp_path) -> None:
    sentiment = {"AAPL": {"score": 0.5, "confidence": 0.8, "article_count": 3}}
    html = _render(tmp_path, holdings_sentiment=sentiment)
    assert 'href="#sentiment"' in html and 'id="sentiment"' in html


def test_sections_follow_decision_first_order(tmp_path) -> None:
    insights = {"AAPL": _insight("BUY")}
    sentiment = {"AAPL": {"score": 0.5, "confidence": 0.8, "article_count": 3}}
    html = _render(tmp_path, holdings_insights=insights, holdings_sentiment=sentiment)
    body = html[html.index("</nav>") :]
    order = [body.index(f'id="{a}"') for a in ("allocation", "posture", "recommandations", "holdings", "overview", "quintessence", "sentiment", "deep-analysis")]
    assert order == sorted(order)


def test_expand_collapse_script_present(tmp_path) -> None:
    html = _render(tmp_path)
    assert html.count("<script") == 1
    assert "Tout déplier" in html and "Tout replier" in html
    assert "querySelectorAll('details')" in html
