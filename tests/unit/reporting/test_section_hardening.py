"""Regression tests for pre-existing section-generator issues fixed per PR #45 review.

Covers HTML escaping (injection), failure-status labeling, string-numeric
tolerance, asset-class bucketing, and cascade-aware discovery counts.
"""

from __future__ import annotations

from finwiz.reporting.sections.analysis import generate_deep_analysis_section
from finwiz.reporting.sections.discovery import (
    generate_discovery_section,
    generate_gap_fill_shortlist_section,
)
from finwiz.reporting.sections.holdings import generate_recommendations
from finwiz.reporting.sections.insights import generate_cost_summary_section
from finwiz.reporting.sections.macro import _format_macro_value, generate_economic_calendar_section


def test_discovery_section_escapes_injection() -> None:
    html = generate_discovery_section({"opportunities": [{"ticker": "<script>x</script>", "name": "<b>n</b>", "grade": '"><img>', "composite_score": 0.9}]})
    assert "<script>x</script>" not in html
    assert "&lt;script&gt;" in html
    assert '"><img>' not in html  # grade neither rendered nor breaks the class attr


def test_deep_analysis_failure_not_labeled_no_action_needed() -> None:
    html = generate_deep_analysis_section({"successful_analyses": 0, "failed_analyses": 3, "total_holdings": 3})
    assert "No Deep Analysis Needed" not in html
    assert "Failed" in html


def test_macro_value_tolerates_string_input() -> None:
    assert _format_macro_value("vix", "20.5") == "20.5"  # no TypeError on string feed
    assert _format_macro_value("vix", None) == "N/A"


def test_economic_calendar_tolerates_string_numbers() -> None:
    html = generate_economic_calendar_section(
        {
            "economic_events": [{"date": "2026-01-01", "event": "CPI", "impact": "high", "estimate": "3.1", "prev": None}],
            "earnings_events": [{"date": "2026-01-02", "symbol": "AAPL", "eps_estimate": "1.23"}],
        }
    )
    assert "3.10" in html
    assert "1.23" in html


def test_discovery_buckets_by_explicit_asset_class() -> None:
    # 'NVDA' would hit the stock heuristic, but explicit asset_class wins.
    html = generate_discovery_section({"opportunities": [{"ticker": "NVDA", "name": "N", "grade": "A", "composite_score": 0.9, "asset_class": "crypto"}]})
    assert "<strong>Crypto:</strong> 1 opportunities" in html
    assert "<strong>Stocks:</strong> 0 opportunities" in html


def test_recommendations_counts_opportunity_shortlist() -> None:
    stats = {
        "recommendation_counts": {"SELL": 1},
        "a_plus_count": 2,
        "a_plus_holdings": [],
    }
    html = generate_recommendations(stats, {"opportunity_shortlist": [{"ticker": "X"}, {"ticker": "Y"}]})
    assert "2 actionable candidates" in html


def test_discovery_table_has_fit_and_gap_columns() -> None:
    html = generate_discovery_section(
        {
            "opportunities": [
                {"ticker": "NVDA", "name": "Nvidia", "grade": "A", "composite_score": 0.9, "portfolio_fit_score": 0.72, "gap_filled": "Semiconductors"},
                {"ticker": "VWO", "name": "Emerging", "grade": "B", "composite_score": 0.7},  # no fit/gap → —
            ]
        }
    )
    assert "Portfolio Fit" in html
    assert "Fills Gap" in html
    assert "72%" in html
    assert "Semiconductors" in html
    assert "—" in html  # missing fit/gap rendered as em dash


def test_discovery_gap_column_escapes_injection() -> None:
    html = generate_discovery_section({"opportunities": [{"ticker": "X", "name": "n", "grade": "A", "composite_score": 0.9, "gap_filled": "<script>x</script>"}]})
    assert "<script>x</script>" not in html
    assert "&lt;script&gt;" in html


def test_gap_fill_shortlist_renders_and_ranks() -> None:
    shortlist = {
        "shortlist": [
            {"ticker": "AAA", "grade": "B", "composite_score": 0.6, "portfolio_fit_score": 0.5, "gap_filled": "Energy"},
            {"ticker": "BBB", "grade": "A", "composite_score": 0.9, "portfolio_fit_score": 0.8, "gap_filled": "Healthcare"},
        ],
        "size": 2,
    }
    html = generate_gap_fill_shortlist_section(shortlist)
    # Highest composite score ranked first.
    assert html.index("BBB") < html.index("AAA")
    assert "Healthcare" in html
    assert "80%" in html
    assert "🎯" in html


def test_gap_fill_shortlist_accepts_bare_list() -> None:
    html = generate_gap_fill_shortlist_section([{"ticker": "Z", "grade": "A", "composite_score": 0.9}])
    assert "Z" in html


def test_gap_fill_shortlist_empty_returns_empty() -> None:
    assert generate_gap_fill_shortlist_section(None) == ""
    assert generate_gap_fill_shortlist_section({"shortlist": []}) == ""
    assert generate_gap_fill_shortlist_section([]) == ""


def test_cost_summary_section_degrades_when_unavailable() -> None:
    assert generate_cost_summary_section(None) == ""
