"""
Pure Python Report Generator.

Replaces AI-based report generation with fast, template-based HTML generation.
Implements deterministic, consistent reporting without LLM calls.
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Any

from finwiz.schemas.portfolio_review import HoldingDecision, PortfolioReview
from finwiz.schemas.run_ledger import CoverageSummary, TrustBanner
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

_BANNER_CSS_CLASS: dict[str, str] = {
    "green": "trust-banner-green",
    "amber": "trust-banner-amber",
    "red": "trust-banner-red",
    "blocked": "trust-banner-blocked",
}


def render_trust_banner(banner: TrustBanner) -> str:
    """Render the trust banner verbatim from the TrustBanner Pydantic model.

    No threshold logic here — TrustBanner.from_coverage already encoded it.
    """
    cls = _BANNER_CSS_CLASS[banner.state]
    return (
        f'<div class="{cls}" data-block-decisions="{str(banner.block_decisions).lower()}">'
        f"<strong>Couverture:</strong> {banner.analyzed}/{banner.total} "
        f"({banner.degraded} dégradés, {banner.failed} échoués). "
        f"{banner.message}"
        f"</div>"
    )


class PythonReportGenerator:
    """
    Pure Python report generator using templates.

    Replaces AI-based report generation with deterministic HTML templates
    for consistent, fast report generation.
    """

    def __init__(self, output_dir: str = "output"):
        """Initialize the report generator."""
        self.output_dir = Path(output_dir)
        self.logger = logger

    def generate_family_financial_plan(
        self,
        portfolio_review: PortfolioReview,
        deep_analysis_results: dict[str, Any] | None = None,
        session_id: str = "default",
        discovery_results: dict[str, Any] | None = None,
        stress_test_results: list[dict[str, Any]] | None = None,
        holdings_sentiment: dict[str, dict] | None = None,
        macro_snapshot: dict | None = None,
        economic_calendar: dict | None = None,
        portfolio_strategic_posture: dict | None = None,
        run_ledger: Any = None,
        deep_analysis_coverage: tuple[int, int] | None = None,
        holdings_insights: dict[str, dict] | None = None,
        opportunity_shortlist: Any = None,
        cost_summary: dict[str, Any] | None = None,
    ) -> str:
        """
        Generate comprehensive family financial plan HTML report.

        Args:
            portfolio_review: Portfolio review data
            deep_analysis_results: Deep analysis results (if available)
            session_id: Session identifier
            discovery_results: A+ discovery results (if available)
            stress_test_results: Stress test results (if available)
            holdings_sentiment: Per-holding sentiment data (if available)
            macro_snapshot: Portfolio-level macro snapshot (if available)
            economic_calendar: Economic calendar data (if available)
            run_ledger: Active RunLedger instance (preferred source for trust banner)
            deep_analysis_coverage: Legacy (analyzed, total) tuple for backwards compat

        Returns:
            Path to generated HTML report

        """
        start_time = time.time()

        self.logger.info("Generating family financial plan with Python templates")

        # Analyze portfolio data
        portfolio_stats = self._analyze_portfolio_stats(portfolio_review)

        # NOTE: Individual HTML reports are generated on-the-fly by
        # DeepAnalysisOrchestrator._store_enriched_analysis() immediately after each analysis.
        # No need to regenerate them here at the end.

        # Generate HTML content
        html_content = self._generate_html_report(
            portfolio_review=portfolio_review,
            portfolio_stats=portfolio_stats,
            deep_analysis_results=deep_analysis_results,
            discovery_results=discovery_results,
            session_id=session_id,
            stress_test_results=stress_test_results,
            holdings_sentiment=holdings_sentiment,
            macro_snapshot=macro_snapshot,
            economic_calendar=economic_calendar,
            portfolio_strategic_posture=portfolio_strategic_posture,
            run_ledger=run_ledger,
            deep_analysis_coverage=deep_analysis_coverage,
            holdings_insights=holdings_insights,
            opportunity_shortlist=opportunity_shortlist,
            cost_summary=cost_summary,
        )

        # Write to file
        self.output_dir.mkdir(parents=True, exist_ok=True)
        report_path = self.output_dir / "finwiz_family_financial_plan.html"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        generation_time = time.time() - start_time

        self.logger.info(f"📊 Generated family financial plan in {generation_time:.2f}s at {report_path}")

        return str(report_path)

    def _analyze_portfolio_stats(self, portfolio_review: PortfolioReview) -> dict[str, Any]:
        """Analyze portfolio statistics."""
        holdings = portfolio_review.holdings

        # Count by asset class
        asset_counts = {"stock": 0, "etf": 0, "crypto": 0}
        grade_counts = {"A+": 0, "A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        recommendation_counts = {"BUY": 0, "HOLD": 0, "SELL": 0}

        total_score = 0.0
        a_plus_holdings = []
        underperforming_holdings = []

        for holding in holdings:
            # Asset class counts
            if holding.asset_class in asset_counts:
                asset_counts[holding.asset_class] += 1

            # Grade counts
            if holding.grade in grade_counts:
                grade_counts[holding.grade] += 1

            # Recommendation counts
            if "BUY" in holding.recommended_action:
                recommendation_counts["BUY"] += 1
            elif "SELL" in holding.recommended_action:
                recommendation_counts["SELL"] += 1
            else:
                recommendation_counts["HOLD"] += 1

            # Score analysis
            total_score += holding.composite_score

            # A+ opportunities
            if holding.grade in ["A+", "A"]:
                a_plus_holdings.append(holding)

            # Underperforming holdings
            if holding.grade in ["D", "F"]:
                underperforming_holdings.append(holding)

        # Coverage = how many holdings actually got deep analysis vs. fell back
        # to the "Analyse en attente" placeholder. Surfaced as a banner in the
        # executive summary so users see the truth at a glance.
        # Indicator is `grade != "N/A"` because both merge paths (merge.py and
        # reporting_orchestrator._merge_deep_analysis_into_portfolio) set the
        # grade authoritatively, while crew_analysis_used is only populated by
        # one of them (PR #21 P1 fix).
        def _is_analyzed(h: Any) -> bool:
            g = getattr(h, "grade", None)
            return g not in (None, "N/A")

        analyzed = sum(1 for h in holdings if _is_analyzed(h))
        total = len(holdings)
        # Average score should ignore N/A / pending holdings so a kickoff that
        # only analyzed 1/63 doesn't mask the gap with a fabricated portfolio score.
        analyzed_holdings = [h for h in holdings if _is_analyzed(h)]
        if analyzed_holdings:
            avg_score = sum(h.composite_score for h in analyzed_holdings) / len(analyzed_holdings)
        else:
            avg_score = 0.0

        return {
            "total_holdings": total,
            "asset_counts": asset_counts,
            "grade_counts": grade_counts,
            "recommendation_counts": recommendation_counts,
            "average_score": avg_score,
            "a_plus_count": len(a_plus_holdings),
            "underperforming_count": len(underperforming_holdings),
            "a_plus_holdings": a_plus_holdings[:10],  # Top 10
            "underperforming_holdings": underperforming_holdings[:10],  # Bottom 10
            "portfolio_grade": self._calculate_portfolio_grade(avg_score) if analyzed_holdings else "N/A",
            "coverage": {"analyzed": analyzed, "total": total},
        }

    def _calculate_portfolio_grade(self, avg_score: float) -> str:
        """Calculate overall portfolio grade."""
        if avg_score >= 0.85:
            return "A+"
        elif avg_score >= 0.75:
            return "A"
        elif avg_score >= 0.65:
            return "B"
        elif avg_score >= 0.55:
            return "C"
        elif avg_score >= 0.45:
            return "D"
        else:
            return "F"

    def _generate_html_report(
        self,
        portfolio_review: PortfolioReview,
        portfolio_stats: dict[str, Any],
        deep_analysis_results: dict[str, Any] | None,
        discovery_results: dict[str, Any] | None,
        session_id: str,
        stress_test_results: list[dict[str, Any]] | None = None,
        holdings_sentiment: dict[str, dict] | None = None,
        macro_snapshot: dict | None = None,
        economic_calendar: dict | None = None,
        portfolio_strategic_posture: dict | None = None,
        run_ledger: Any = None,
        deep_analysis_coverage: tuple[int, int] | None = None,
        holdings_insights: dict[str, dict] | None = None,
        opportunity_shortlist: Any = None,
        cost_summary: dict[str, Any] | None = None,
    ) -> str:
        """Generate complete HTML report."""
        # Generate timestamp
        timestamp = datetime.now().strftime("%d %B %Y à %H:%M")

        # Build trust banner HTML from TrustBanner model (single source of truth).
        # run_ledger takes precedence; fall back to legacy deep_analysis_coverage tuple.
        trust_banner_html = ""
        if run_ledger is not None:
            trust_banner_html = render_trust_banner(run_ledger.to_banner())
        elif deep_analysis_coverage is not None:
            analyzed, total = deep_analysis_coverage
            summary = CoverageSummary(
                analyzed=analyzed,
                degraded=0,
                failed=max(total - analyzed, 0),
                total=total,
            )
            trust_banner_html = render_trust_banner(TrustBanner.from_coverage(summary))

        # Header cost line: real LLM spend when available, neutral text otherwise.
        # The deterministic Python scoring + HTML rendering remain $0 regardless.
        cost_header = self._format_cost_header(cost_summary)
        cost_footer = self._format_cost_footer(cost_summary)

        # Build HTML content
        html = f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Plan financier familial — Rapport FinWiz</title>
  <style>
    {self._get_css_styles()}
  </style>
</head>
<body>
  <header>
    <h1>Plan financier familial -- Rapport FinWiz</h1>
    <div class="muted">Genere le {timestamp} -- Session: {session_id}</div>
    <div class="muted">{cost_header}</div>
  </header>

  {self._generate_executive_summary(portfolio_stats, trust_banner_html=trust_banner_html)}

  {self._generate_strategic_posture_section(portfolio_strategic_posture)}

  {self._generate_macro_dashboard_section(macro_snapshot)}

  {self._generate_portfolio_overview(portfolio_review, portfolio_stats)}

  {self._generate_holdings_analysis(portfolio_review.holdings)}

  {self._generate_holdings_insight_cards(holdings_insights, portfolio_review.holdings)}

  {self._generate_sentiment_section(holdings_sentiment)}

  {self._generate_recommendations(portfolio_stats, discovery_results)}

  {self._generate_gap_fill_shortlist_section(opportunity_shortlist)}

  {self._generate_discovery_section(discovery_results)}

  {self._generate_deep_analysis_section(deep_analysis_results)}

  {self._generate_performance_metrics(deep_analysis_results)}

  {self._generate_cost_summary_section(cost_summary)}

  {self._generate_stress_test_section(stress_test_results)}

  {self._generate_economic_calendar_section(economic_calendar)}

  <footer>
    <p>Rapport genere par FinWiz -- Analyse Python deterministe</p>
    <p class="small">{cost_footer}</p>
  </footer>
</body>
</html>"""

        return html

    def _get_css_styles(self) -> str:
        """Get CSS styles for the report (delegates to module)."""
        from finwiz.reporting.css_styles import get_report_css

        return get_report_css()

    def _generate_executive_summary(self, portfolio_stats: dict[str, Any], trust_banner_html: str = "") -> str:
        """Generate executive summary section (delegates to module)."""
        from finwiz.reporting.section_generators import generate_executive_summary

        return generate_executive_summary(portfolio_stats, trust_banner_html=trust_banner_html)

    def _generate_portfolio_overview(self, portfolio_review: PortfolioReview, portfolio_stats: dict[str, Any]) -> str:
        """Generate portfolio overview section (delegates to module)."""
        from finwiz.reporting.section_generators import generate_portfolio_overview

        return generate_portfolio_overview(portfolio_review, portfolio_stats)

    def _generate_holdings_analysis(self, holdings: list[HoldingDecision]) -> str:
        """Generate detailed holdings analysis (delegates to module)."""
        from finwiz.reporting.section_generators import generate_holdings_analysis

        return generate_holdings_analysis(holdings)

    def _generate_recommendations(
        self,
        portfolio_stats: dict[str, Any],
        discovery_results: dict[str, Any] | None = None,
    ) -> str:
        """Generate recommendations section (delegates to module)."""
        from finwiz.reporting.section_generators import generate_recommendations

        return generate_recommendations(portfolio_stats, discovery_results)

    def _generate_deep_analysis_section(self, deep_analysis_results: dict[str, Any] | None) -> str:
        """Generate deep analysis section (delegates to module)."""
        from finwiz.reporting.section_generators import (
            generate_deep_analysis_section,
        )

        return generate_deep_analysis_section(deep_analysis_results)

    def _generate_performance_metrics(self, deep_analysis_results: dict[str, Any] | None) -> str:
        """Generate performance metrics section (delegates to module)."""
        from finwiz.reporting.section_generators import (
            generate_performance_metrics,
        )

        return generate_performance_metrics(deep_analysis_results)

    def _generate_discovery_section(self, discovery_results: dict[str, Any] | None) -> str:
        """Generate A+ discovery opportunities section (delegates to module)."""
        from finwiz.reporting.section_generators import (
            generate_discovery_section,
        )

        return generate_discovery_section(discovery_results)

    def _generate_holdings_insight_cards(self, holdings_insights: dict[str, dict] | None, holdings: list[HoldingDecision]) -> str:
        """Generate per-holding quintessence cards (delegates to module)."""
        from finwiz.reporting.section_generators import generate_holdings_insight_cards

        return generate_holdings_insight_cards(holdings_insights, holdings)

    def _generate_gap_fill_shortlist_section(self, opportunity_shortlist: Any) -> str:
        """Generate the gap-fill shortlist block (delegates to module)."""
        from finwiz.reporting.section_generators import generate_gap_fill_shortlist_section

        return generate_gap_fill_shortlist_section(opportunity_shortlist)

    def _generate_cost_summary_section(self, cost_summary: dict[str, Any] | None) -> str:
        """Generate the real LLM cost summary section (delegates to module)."""
        from finwiz.reporting.section_generators import generate_cost_summary_section

        return generate_cost_summary_section(cost_summary)

    @staticmethod
    def _cost_total_and_calls(cost_summary: dict[str, Any] | None) -> tuple[float, int] | None:
        """Best-effort (total_cost, call_count) from a token-monitor summary, or None."""
        if not isinstance(cost_summary, dict):
            return None
        try:
            total = float(cost_summary.get("total_cost", 0.0) or 0.0)
        except (TypeError, ValueError):
            return None
        try:
            calls = int(cost_summary.get("call_count", 0) or 0)
        except (TypeError, ValueError):
            calls = 0
        if calls <= 0:
            per_crew = cost_summary.get("per_crew")
            if isinstance(per_crew, dict):
                calls = sum(int(d.get("calls", 0) or 0) for d in per_crew.values() if isinstance(d, dict))
        if total <= 0 and calls <= 0:
            return None
        return total, calls

    def _format_cost_header(self, cost_summary: dict[str, Any] | None) -> str:
        """Header cost line: real LLM spend when available, neutral text otherwise."""
        parsed = self._cost_total_and_calls(cost_summary)
        if parsed is None:
            return "Scoring quantitatif Python -- $0 -- recherche IA qualitative séparée"
        total, calls = parsed
        return f"Scoring Python: $0 -- Recherche IA qualitative: ${total:.2f} sur {calls} appels LLM"

    def _format_cost_footer(self, cost_summary: dict[str, Any] | None) -> str:
        """Footer cost line: replace the misleading '100% reduction' claim with the truth."""
        parsed = self._cost_total_and_calls(cost_summary)
        if parsed is None:
            return "Performance: Analyse complete en quelques secondes -- scoring et rendu 100% Python"
        total, _calls = parsed
        return f"Performance: scoring et rendu 100% Python ($0) -- recherche IA qualitative: ${total:.2f}"

    def _generate_stress_test_section(self, stress_test_results: list[dict[str, Any]] | None) -> str:
        """Generate stress test analysis section (delegates to module)."""
        from finwiz.reporting.section_generators import (
            generate_stress_test_section,
        )

        return generate_stress_test_section(stress_test_results)

    def _generate_strategic_posture_section(self, portfolio_strategic_posture: dict | None) -> str:
        """Generate portfolio-level strategic posture section (delegates to module)."""
        from finwiz.reporting.section_generators import generate_strategic_posture_section

        return generate_strategic_posture_section(portfolio_strategic_posture)

    def _generate_sentiment_section(self, holdings_sentiment: dict[str, dict] | None) -> str:
        """Generate sentiment summary section (delegates to module)."""
        from finwiz.reporting.section_generators import generate_sentiment_section

        return generate_sentiment_section(holdings_sentiment)

    def _generate_macro_dashboard_section(self, macro_snapshot: dict | None) -> str:
        """Generate macro dashboard section (delegates to module)."""
        from finwiz.reporting.section_generators import generate_macro_dashboard_section

        return generate_macro_dashboard_section(macro_snapshot)

    def _generate_economic_calendar_section(self, economic_calendar: dict | None) -> str:
        """Generate economic calendar section (delegates to module)."""
        from finwiz.reporting.section_generators import generate_economic_calendar_section

        return generate_economic_calendar_section(economic_calendar)

    # NOTE: _generate_individual_deep_analysis_reports() removed - DEAD CODE
    # Individual reports are now generated on-the-fly by
    # DeepAnalysisOrchestrator._store_enriched_analysis()


def generate_python_report(
    portfolio_review: PortfolioReview,
    deep_analysis_results: dict[str, Any] | None = None,
    session_id: str = "default",
    discovery_results: dict[str, Any] | None = None,
    stress_test_results: list[dict[str, Any]] | None = None,
    holdings_sentiment: dict[str, dict] | None = None,
    macro_snapshot: dict | None = None,
    economic_calendar: dict | None = None,
    portfolio_strategic_posture: dict | None = None,
    run_ledger: Any = None,
    deep_analysis_coverage: tuple[int, int] | None = None,
    holdings_insights: dict[str, dict] | None = None,
    opportunity_shortlist: Any = None,
    cost_summary: dict[str, Any] | None = None,
) -> str:
    """
    Convenience function to generate Python-based report.

    This replaces AI-based report generation with fast template-based HTML.
    """
    generator = PythonReportGenerator()
    return generator.generate_family_financial_plan(
        portfolio_review=portfolio_review,
        deep_analysis_results=deep_analysis_results,
        session_id=session_id,
        discovery_results=discovery_results,
        stress_test_results=stress_test_results,
        holdings_sentiment=holdings_sentiment,
        macro_snapshot=macro_snapshot,
        economic_calendar=economic_calendar,
        portfolio_strategic_posture=portfolio_strategic_posture,
        run_ledger=run_ledger,
        deep_analysis_coverage=deep_analysis_coverage,
        holdings_insights=holdings_insights,
        opportunity_shortlist=opportunity_shortlist,
        cost_summary=cost_summary,
    )
