"""
Portfolio rebalancing report generation utilities.

This module contains report generation and formatting logic
for portfolio rebalancing operations.
"""

from typing import Any

from finwiz.schemas.portfolio_rebalancing import RebalancingResult
from finwiz.tools.html_report_generator import HTMLReportGenerator
from finwiz.tools.logger import get_logger

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
        summary_content = f"""
        <div class="executive-summary">
            <h3>Portfolio Rebalancing Summary</h3>
            <p><strong>Analysis Date:</strong> {result.analysis_timestamp.strftime("%Y-%m-%d %H:%M")}</p>
            <p><strong>Overall Recommendation:</strong> {result.overall_recommendation.value}</p>
            <p><strong>Total Trades Required:</strong> {result.execution_summary.total_trades_required}</p>
            <p><strong>Total Transaction Costs:</strong> ${result.cost_analysis.total_transaction_costs:.2f}</p>
            <p><strong>Risk Score:</strong> {result.current_risk_score:.1f}/10 → {result.projected_risk_score:.1f}/10</p>
            <p><strong>Next Review Date:</strong> {result.next_review_date.strftime("%Y-%m-%d")}</p>
        </div>
        """
        self.report_generator.add_section("Executive Summary", summary_content, "summary", order=1)

    def _add_current_portfolio_section(self, result: RebalancingResult) -> None:
        """Add current portfolio analysis section."""
        weightings_html = "<div class='portfolio-weightings'><h4>Current Allocations</h4><ul>"
        for symbol, weight in result.current_portfolio.weightings.items():
            deviation = result.current_portfolio.deviations_from_target.get(symbol, 0.0)
            deviation_class = "over-weight" if deviation > 0 else "under-weight" if deviation < 0 else "on-target"
            weightings_html += f"""
            <li class="{deviation_class}">
                <span class="symbol">{symbol}</span>: 
                <span class="weight">{weight:.1%}</span>
                <span class="deviation">({deviation:+.1%})</span>
            </li>
            """
        weightings_html += "</ul></div>"

        # Add portfolio metrics
        metrics_html = f"""
        <div class="portfolio-metrics">
            <h4>Portfolio Metrics</h4>
            <p><strong>Total Value:</strong> ${result.current_portfolio.total_value:,.2f}</p>
            <p><strong>Positions Needing Rebalancing:</strong> {len(result.current_portfolio.positions_needing_rebalancing)}</p>
            <p><strong>Risk Score:</strong> {result.current_risk_score:.1f}/10</p>
        </div>
        """

        full_content = weightings_html + metrics_html
        self.report_generator.add_section("Current Portfolio", full_content, "portfolio", order=2)

    def _add_trade_recommendations_section(self, result: RebalancingResult) -> None:
        """Add trade recommendations section."""
        if not result.trade_recommendations:
            content = """
            <div class="no-trades">
                <p>✅ <strong>No trades required</strong> - portfolio is within tolerance bands.</p>
                <p>Your portfolio allocation is well-balanced and no rebalancing is needed at this time.</p>
            </div>
            """
        else:
            content = """
            <div class="trade-recommendations">
                <table class="trades-table">
                    <thead>
                        <tr>
                            <th>Symbol</th>
                            <th>Action</th>
                            <th>Shares</th>
                            <th>Trade Value</th>
                            <th>Current Weight</th>
                            <th>Target Weight</th>
                            <th>Projected Weight</th>
                        </tr>
                    </thead>
                    <tbody>
            """

            for trade in result.trade_recommendations:
                action_class = trade.action.value.lower()
                content += f"""
                <tr class="trade-{action_class}">
                    <td class="symbol">{trade.symbol}</td>
                    <td class="action {action_class}">{trade.action.value}</td>
                    <td class="shares">{trade.shares:,}</td>
                    <td class="trade-value">${trade.trade_value:,.2f}</td>
                    <td class="current-weight">{getattr(trade, "current_weight", 0):.1%}</td>
                    <td class="target-weight">{getattr(trade, "target_weight", 0):.1%}</td>
                    <td class="projected-weight">{getattr(trade, "projected_weight_after_trade", 0):.1%}</td>
                </tr>
                """

            content += """
                    </tbody>
                </table>
            </div>
            """

        self.report_generator.add_section("Trade Recommendations", content, "data", order=3)

    def _add_cost_analysis_section(self, result: RebalancingResult) -> None:
        """Add cost analysis section."""
        cost_content = f"""
        <div class="cost-analysis">
            <h4>Transaction Cost Breakdown</h4>
            <div class="cost-metrics">
                <div class="cost-item">
                    <span class="label">Commission Costs:</span>
                    <span class="value">${result.cost_analysis.commission_costs:.2f}</span>
                </div>
                <div class="cost-item">
                    <span class="label">Spread Costs:</span>
                    <span class="value">${result.cost_analysis.spread_costs:.2f}</span>
                </div>
                <div class="cost-item total">
                    <span class="label">Total Transaction Costs:</span>
                    <span class="value">${result.cost_analysis.total_transaction_costs:.2f}</span>
                </div>
                <div class="cost-item">
                    <span class="label">Cost as % of Portfolio:</span>
                    <span class="value">{result.cost_analysis.cost_as_percentage:.3f}%</span>
                </div>
                <div class="cost-item">
                    <span class="label">Break-even Days:</span>
                    <span class="value">{result.cost_analysis.break_even_days or "N/A"}</span>
                </div>
            </div>
        </div>
        """
        self.report_generator.add_section("Cost Analysis", cost_content, "financial", order=4)

    def _add_risk_analysis_section(self, result: RebalancingResult) -> None:
        """Add risk analysis section."""
        risk_improvement_class = (
            "improvement" if result.risk_improvement > 0 else "degradation" if result.risk_improvement < 0 else "neutral"
        )

        risk_content = f"""
        <div class="risk-analysis">
            <h4>Risk Assessment</h4>
            <div class="risk-metrics">
                <div class="risk-item">
                    <span class="label">Current Risk Score:</span>
                    <span class="value risk-score">{result.current_risk_score:.1f}/10</span>
                </div>
                <div class="risk-item">
                    <span class="label">Projected Risk Score:</span>
                    <span class="value risk-score">{result.projected_risk_score:.1f}/10</span>
                </div>
                <div class="risk-item {risk_improvement_class}">
                    <span class="label">Risk Change:</span>
                    <span class="value">{result.risk_improvement:+.1f}</span>
                </div>
            </div>

            <div class="risk-interpretation">
                <h5>Risk Interpretation</h5>
        """

        if result.risk_improvement > 0.5:
            risk_content += (
                "<p>✅ <strong>Significant Risk Reduction:</strong> Rebalancing will meaningfully reduce portfolio risk.</p>"
            )
        elif result.risk_improvement > 0:
            risk_content += "<p>🟡 <strong>Modest Risk Reduction:</strong> Rebalancing will slightly reduce portfolio risk.</p>"
        elif result.risk_improvement < -0.5:
            risk_content += "<p>⚠️ <strong>Risk Increase:</strong> Rebalancing may increase portfolio risk. Consider carefully.</p>"
        else:
            risk_content += "<p>➡️ <strong>Neutral Risk Impact:</strong> Rebalancing will have minimal impact on portfolio risk.</p>"

        risk_content += """
            </div>
        </div>
        """

        self.report_generator.add_section("Risk Analysis", risk_content, "risk", order=5)

    def _add_projected_portfolio_section(self, result: RebalancingResult) -> None:
        """Add projected portfolio section."""
        projected_html = """
        <div class="projected-portfolio">
            <h4>Projected Allocations After Rebalancing</h4>
            <ul class="projected-weightings">
        """

        for symbol, weight in result.projected_portfolio.weightings.items():
            target_weight = result.current_portfolio.weightings.get(symbol, 0.0)  # This should be target weight
            deviation = weight - target_weight
            deviation_class = "on-target" if abs(deviation) < 0.01 else "close-to-target"

            projected_html += f"""
            <li class="{deviation_class}">
                <span class="symbol">{symbol}</span>: 
                <span class="weight">{weight:.1%}</span>
                <span class="deviation">({deviation:+.1%} from current)</span>
            </li>
            """

        projected_html += f"""
            </ul>
            <div class="projected-metrics">
                <p><strong>Projected Positions Within Tolerance:</strong> {result.execution_summary.positions_within_tolerance}</p>
                <p><strong>Projected Risk Score:</strong> {result.projected_risk_score:.1f}/10</p>
            </div>
        </div>
        """

        self.report_generator.add_section("Projected Portfolio", projected_html, "growth", order=6)

    def _add_french_sections(self, result: RebalancingResult) -> None:
        """Add required French sections."""
        # Synthèse 10-K (Portfolio Summary in French)
        french_summary = f"""
        <div class="synthese-10k">
            <h3>Synthèse du Rééquilibrage de Portefeuille</h3>
            <div class="synthese-content">
                <p><strong>Date d'analyse:</strong> {result.analysis_timestamp.strftime("%Y-%m-%d %H:%M")}</p>
                <p><strong>Recommandation globale:</strong> {
            self._translate_recommendation(result.overall_recommendation.value)
        }</p>
                <p><strong>Nombre total de transactions:</strong> {result.execution_summary.total_trades_required}</p>
                <p><strong>Coûts de transaction totaux:</strong> {result.cost_analysis.total_transaction_costs:.2f} $</p>
                <p><strong>Score de risque:</strong> {result.current_risk_score:.1f}/10 → {result.projected_risk_score:.1f}/10</p>
                <p><strong>Prochaine révision:</strong> {result.next_review_date.strftime("%Y-%m-%d")}</p>
            </div>

            <div class="recommandations-francais">
                <h4>Recommandations Principales</h4>
        """

        if result.execution_summary.total_trades_required == 0:
            french_summary += "<p>Aucune transaction requise - le portefeuille est bien équilibré.</p>"
        else:
            french_summary += f"""
            <p>Exécuter {result.execution_summary.total_trades_required} transactions pour optimiser l'allocation.</p>
            <p>Temps d'exécution estimé: {result.execution_summary.estimated_execution_time}</p>
            """

        french_summary += """
            </div>
        </div>
        """

        self.report_generator.add_section("Synthèse 10-K", french_summary, "summary", order=7)

    def _translate_recommendation(self, recommendation: str) -> str:
        """Translate recommendation to French."""
        translations = {
            "REBALANCE_NOW": "Rééquilibrer maintenant",
            "REBALANCE_SOON": "Rééquilibrer bientôt",
            "MONITOR": "Surveiller",
            "NO_ACTION": "Aucune action requise",
        }
        return translations.get(recommendation, recommendation)

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
