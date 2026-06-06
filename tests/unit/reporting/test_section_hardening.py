"""Regression tests for pre-existing section-generator issues fixed per PR #45 review.

Covers HTML escaping (injection), failure-status labeling, string-numeric
tolerance, asset-class bucketing, and cascade-aware discovery counts.
"""

from __future__ import annotations

from finwiz.reporting.sections.analysis import generate_deep_analysis_section
from finwiz.reporting.sections.discovery import generate_discovery_section
from finwiz.reporting.sections.holdings import generate_recommendations
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
