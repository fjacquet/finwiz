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
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


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
        self, portfolio_review: PortfolioReview, deep_analysis_results: dict[str, Any] | None = None, session_id: str = "default", discovery_results: dict[str, Any] | None = None
    ) -> str:
        """
        Generate comprehensive family financial plan HTML report.

        Args:
            portfolio_review: Portfolio review data
            deep_analysis_results: Deep analysis results (if available)
            session_id: Session identifier
            discovery_results: A+ discovery results (if available)

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

        avg_score = total_score / len(holdings) if holdings else 0.0

        return {
            "total_holdings": len(holdings),
            "asset_counts": asset_counts,
            "grade_counts": grade_counts,
            "recommendation_counts": recommendation_counts,
            "average_score": avg_score,
            "a_plus_count": len(a_plus_holdings),
            "underperforming_count": len(underperforming_holdings),
            "a_plus_holdings": a_plus_holdings[:10],  # Top 10
            "underperforming_holdings": underperforming_holdings[:10],  # Bottom 10
            "portfolio_grade": self._calculate_portfolio_grade(avg_score),
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
    ) -> str:
        """Generate complete HTML report."""
        # Generate timestamp
        timestamp = datetime.now().strftime("%d %B %Y à %H:%M")

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
    <h1>📊 Plan financier familial — Rapport FinWiz</h1>
    <div class="muted">Généré le {timestamp} • Session: {session_id}</div>
    <div class="muted">⚡ Analyse Python ultra-rapide • 0 appels LLM • Coût: $0</div>
  </header>

  {self._generate_executive_summary(portfolio_stats)}

  {self._generate_portfolio_overview(portfolio_review, portfolio_stats)}

  {self._generate_holdings_analysis(portfolio_review.holdings)}

  {self._generate_recommendations(portfolio_stats, discovery_results)}

  {self._generate_discovery_section(discovery_results)}

  {self._generate_deep_analysis_section(deep_analysis_results)}

  {self._generate_performance_metrics(deep_analysis_results)}

  <footer>
    <p>📋 Rapport généré par FinWiz • Analyse Python déterministe</p>
    <p class="small">⚡ Performance: Analyse complète en quelques secondes • 100% réduction des coûts LLM</p>
  </footer>
</body>
</html>"""

        return html

    def _get_css_styles(self) -> str:
        """Get CSS styles for the report (delegates to module)."""
        from finwiz.reporting.css_styles import get_report_css

        return get_report_css()

    def _generate_executive_summary(self, portfolio_stats: dict[str, Any]) -> str:
        """Generate executive summary section (delegates to module)."""
        from finwiz.reporting.section_generators import generate_executive_summary

        return generate_executive_summary(portfolio_stats)

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

    # NOTE: _generate_individual_deep_analysis_reports() removed - DEAD CODE
    # Individual reports are now generated on-the-fly by
    # DeepAnalysisOrchestrator._store_enriched_analysis()

    def _generate_individual_report_html(self, ticker: str, result: dict[str, Any]) -> str:
        """Generate HTML for individual deep analysis report (delegates to module)."""
        from finwiz.reporting.individual_report_generator import generate_individual_report_html

        return generate_individual_report_html(ticker, result)

    def _generate_detailed_scores_section(self, result: dict[str, Any]) -> str:
        """Generate detailed score breakdown section (delegates to module)."""
        from finwiz.reporting.individual_report_generator import generate_detailed_scores_section

        return str(generate_detailed_scores_section(result))

    def _generate_fundamental_details(self, result: dict[str, Any]) -> str:
        """Generate fundamental analysis details (delegates to module)."""
        from finwiz.reporting.individual_report_generator import generate_fundamental_details

        return str(generate_fundamental_details(result))

    def _generate_technical_details(self, result: dict[str, Any]) -> str:
        """Generate technical analysis details (delegates to module)."""
        from finwiz.reporting.individual_report_generator import generate_technical_details

        return str(generate_technical_details(result))

    def _generate_risk_details(self, result: dict[str, Any]) -> str:
        """Generate risk analysis details (delegates to module)."""
        from finwiz.reporting.individual_report_generator import generate_risk_details

        return str(generate_risk_details(result))


def generate_python_report(
    portfolio_review: PortfolioReview, deep_analysis_results: dict[str, Any] | None = None, session_id: str = "default", discovery_results: dict[str, Any] | None = None
) -> str:
    """
    Convenience function to generate Python-based report.

    This replaces AI-based report generation with fast template-based HTML.
    """
    generator = PythonReportGenerator()
    return generator.generate_family_financial_plan(
        portfolio_review=portfolio_review, deep_analysis_results=deep_analysis_results, session_id=session_id, discovery_results=discovery_results
    )
