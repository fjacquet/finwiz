"""Report section generators for Python report generation.

This module is a backward-compatible facade. The section generators were split
into focused submodules under :mod:`finwiz.reporting.sections` (by report area)
to keep each file within the 300-line norm. All public ``generate_*`` functions
— and the few private helpers that tests import directly — are re-exported here
so existing imports (``from finwiz.reporting.section_generators import ...``)
keep working unchanged.
"""

from __future__ import annotations

from finwiz.reporting.sections.analysis import (
    generate_deep_analysis_section,
    generate_performance_metrics,
    generate_stress_test_section,
)
from finwiz.reporting.sections.discovery import (
    generate_discovery_section,
    generate_gap_fill_shortlist_section,
)
from finwiz.reporting.sections.factpack import _fact_pack_provenance_footer
from finwiz.reporting.sections.holdings import (
    _confidence_badge,
    _get_recommendation_badge,
    _render_holding_row,
    generate_holdings_analysis,
    generate_recommendations,
)
from finwiz.reporting.sections.insights import (
    generate_cost_summary_section,
    generate_holdings_insight_cards,
)
from finwiz.reporting.sections.macro import (
    generate_economic_calendar_section,
    generate_macro_dashboard_section,
)
from finwiz.reporting.sections.portfolio_summary import (
    generate_allocation_section,
    generate_executive_summary,
    generate_portfolio_overview,
    generate_strategic_posture_section,
)
from finwiz.reporting.sections.sentiment import generate_sentiment_section

__all__ = [
    "_confidence_badge",
    "_fact_pack_provenance_footer",
    "_get_recommendation_badge",
    "_render_holding_row",
    "generate_allocation_section",
    "generate_cost_summary_section",
    "generate_deep_analysis_section",
    "generate_discovery_section",
    "generate_economic_calendar_section",
    "generate_executive_summary",
    "generate_gap_fill_shortlist_section",
    "generate_holdings_analysis",
    "generate_holdings_insight_cards",
    "generate_macro_dashboard_section",
    "generate_performance_metrics",
    "generate_portfolio_overview",
    "generate_recommendations",
    "generate_sentiment_section",
    "generate_stress_test_section",
    "generate_strategic_posture_section",
]
