"""
Portfolio rebalancing report generation utilities.

This module contains report generation and formatting logic
for portfolio rebalancing operations.
"""

from typing import Any

from finwiz.schemas.portfolio_rebalancing import RebalancingResult
from finwiz.tools.html_report_generator import HTMLReportGenerator
from finwiz.tools.logger import get_logger
from finwiz.tools.rebalancing.rebalancing_html_builders import RebalancingHTMLBuilder

logger = get_logger(__name__)


class PortfolioRebalancingError(Exception):
    """Base exception for portfolio rebalancing reporting errors."""

    pass


class RebalancingReportGenerator:
    """Handles report generation for portfolio rebalancing operations."""

    def __init__(self, report_generator: HTMLReportGenerator | None = None) -> None:
        """
        Initialize the rebalancing report generator.

        Args:
            report_generator: HTML report generator instance

        """
        self.report_generator = report_generator or HTMLReportGenerator()
        self.logger = logger

    async def generate_rebalancing_report(self, result: RebalancingResult, language: str = "en") -> str:
        """
        Generate comprehensive HTML rebalancing report.

        Args:
            result: Rebalancing analysis result
            language: Report language (en/fr)

        Returns:
            HTML report content

        Raises:
            PortfolioRebalancingError: If report generation fails

        """
        self.logger.info("Generating rebalancing HTML report")

        try:
            # Clear any existing sections
            self.report_generator.clear_sections()

            # Add executive summary
            self._add_executive_summary_section(result)

            # Add current portfolio analysis
            self._add_current_portfolio_section(result)

            # Add trade recommendations
            self._add_trade_recommendations_section(result)

            # Add cost analysis
            self._add_cost_analysis_section(result)

            # Add risk analysis
            self._add_risk_analysis_section(result)

            # Add projected portfolio
            self._add_projected_portfolio_section(result)

            # Add French sections if required
            if language == "fr":
                self._add_french_sections(result)

            # Generate final HTML using unified template
            title = f"Portfolio Rebalancing Analysis - {result.analysis_timestamp.strftime('%Y-%m-%d')}"

            # Try to use unified HTML generator if available
            if hasattr(self.report_generator, "generate_unified_html"):
                html_content = self.report_generator.generate_unified_html(title=title, language=language)
            else:
                html_content = self.report_generator.generate_html(title=title, language=language)

            self.logger.info("Rebalancing report generated successfully")
            return html_content

        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")
            raise PortfolioRebalancingError(f"Report generation failed: {e}") from e

    def _add_executive_summary_section(self, result: RebalancingResult) -> None:
        """Add executive summary section to report."""
        summary_content = RebalancingHTMLBuilder.build_executive_summary(result)
        self.report_generator.add_section("Executive Summary", summary_content, "summary", order=1)

    def _add_current_portfolio_section(self, result: RebalancingResult) -> None:
        """Add current portfolio analysis section."""
        full_content = RebalancingHTMLBuilder.build_current_portfolio(result)
        self.report_generator.add_section("Current Portfolio", full_content, "portfolio", order=2)

    def _add_trade_recommendations_section(self, result: RebalancingResult) -> None:
        """Add trade recommendations section."""
        content = RebalancingHTMLBuilder.build_trade_recommendations(result)
        self.report_generator.add_section("Trade Recommendations", content, "data", order=3)

    def _add_cost_analysis_section(self, result: RebalancingResult) -> None:
        """Add cost analysis section."""
        cost_content = RebalancingHTMLBuilder.build_cost_analysis(result)
        self.report_generator.add_section("Cost Analysis", cost_content, "financial", order=4)

    def _add_risk_analysis_section(self, result: RebalancingResult) -> None:
        """Add risk analysis section."""
        risk_content = RebalancingHTMLBuilder.build_risk_analysis(result)
        self.report_generator.add_section("Risk Analysis", risk_content, "risk", order=5)

    def _add_projected_portfolio_section(self, result: RebalancingResult) -> None:
        """Add projected portfolio section."""
        projected_html = RebalancingHTMLBuilder.build_projected_portfolio(result)
        self.report_generator.add_section("Projected Portfolio", projected_html, "growth", order=6)

    def _add_french_sections(self, result: RebalancingResult) -> None:
        """Add required French sections."""
        french_summary = RebalancingHTMLBuilder.build_french_sections(result)
        self.report_generator.add_section("Synthèse 10-K", french_summary, "summary", order=7)

    def generate_summary_report(self, result: RebalancingResult) -> dict[str, Any]:
        """
        Generate a summary report in dictionary format.

        Args:
            result: Rebalancing analysis result

        Returns:
            Dictionary containing summary information

        """
        try:
            summary = {
                "analysis_timestamp": result.analysis_timestamp.isoformat(),
                "portfolio_id": result.portfolio_id,
                "overall_recommendation": result.overall_recommendation.value,
                "next_review_date": result.next_review_date.isoformat(),
                "execution_summary": {
                    "total_trades_required": result.execution_summary.total_trades_required,
                    "positions_requiring_action": result.execution_summary.positions_requiring_action,
                    "positions_within_tolerance": result.execution_summary.positions_within_tolerance,
                    "estimated_execution_time": result.execution_summary.estimated_execution_time,
                    "capital_required": result.execution_summary.capital_required,
                },
                "cost_analysis": {
                    "total_transaction_costs": result.cost_analysis.total_transaction_costs,
                    "cost_as_percentage": result.cost_analysis.cost_as_percentage,
                    "break_even_days": result.cost_analysis.break_even_days,
                },
                "risk_analysis": {
                    "current_risk_score": result.current_risk_score,
                    "projected_risk_score": result.projected_risk_score,
                    "risk_improvement": result.risk_improvement,
                },
                "portfolio_metrics": {
                    "total_value": result.current_portfolio.total_value,
                    "positions_count": len(result.current_portfolio.weightings),
                    "positions_needing_rebalancing": len(result.current_portfolio.positions_needing_rebalancing),
                },
            }

            return summary

        except Exception as e:
            self.logger.error(f"Error generating summary report: {e}")
            return {
                "error": str(e),
                "analysis_timestamp": result.analysis_timestamp.isoformat() if result.analysis_timestamp else None,
            }
