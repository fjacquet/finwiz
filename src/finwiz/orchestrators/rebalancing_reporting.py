"""
Portfolio rebalancing report generation utilities.

This module contains report generation and formatting logic
for portfolio rebalancing operations.
"""

from typing import Any

from bs4 import BeautifulSoup

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
        soup = BeautifulSoup("", "html.parser")

        div = soup.new_tag("div", **{"class": "executive-summary"})

        h3 = soup.new_tag("h3")
        h3.string = "Portfolio Rebalancing Summary"
        div.append(h3)

        # Analysis Date
        p = soup.new_tag("p")
        strong = soup.new_tag("strong")
        strong.string = "Analysis Date:"
        p.append(strong)
        p.append(f" {result.analysis_timestamp.strftime('%Y-%m-%d %H:%M')}")
        div.append(p)

        # Overall Recommendation
        p = soup.new_tag("p")
        strong = soup.new_tag("strong")
        strong.string = "Overall Recommendation:"
        p.append(strong)
        p.append(f" {result.overall_recommendation.value}")
        div.append(p)

        # Total Trades Required
        p = soup.new_tag("p")
        strong = soup.new_tag("strong")
        strong.string = "Total Trades Required:"
        p.append(strong)
        p.append(f" {result.execution_summary.total_trades_required}")
        div.append(p)

        # Total Transaction Costs
        p = soup.new_tag("p")
        strong = soup.new_tag("strong")
        strong.string = "Total Transaction Costs:"
        p.append(strong)
        p.append(f" ${result.cost_analysis.total_transaction_costs:.2f}")
        div.append(p)

        # Risk Score
        p = soup.new_tag("p")
        strong = soup.new_tag("strong")
        strong.string = "Risk Score:"
        p.append(strong)
        p.append(f" {result.current_risk_score:.1f}/10 → {result.projected_risk_score:.1f}/10")
        div.append(p)

        # Next Review Date
        p = soup.new_tag("p")
        strong = soup.new_tag("strong")
        strong.string = "Next Review Date:"
        p.append(strong)
        p.append(f" {result.next_review_date.strftime('%Y-%m-%d')}")
        div.append(p)

        summary_content = str(div)
        self.report_generator.add_section("Executive Summary", summary_content, "summary", order=1)

    def _add_current_portfolio_section(self, result: RebalancingResult) -> None:
        """Add current portfolio analysis section."""
        soup = BeautifulSoup("", "html.parser")

        # Weightings section
        weightings_div = soup.new_tag("div", **{"class": "portfolio-weightings"})
        h4 = soup.new_tag("h4")
        h4.string = "Current Allocations"
        weightings_div.append(h4)

        ul = soup.new_tag("ul")
        for symbol, weight in result.current_portfolio.weightings.items():
            deviation = result.current_portfolio.deviations_from_target.get(symbol, 0.0)
            deviation_class = "over-weight" if deviation > 0 else "under-weight" if deviation < 0 else "on-target"

            li = soup.new_tag("li", **{"class": deviation_class})

            symbol_span = soup.new_tag("span", **{"class": "symbol"})
            symbol_span.string = symbol
            li.append(symbol_span)
            li.append(": ")

            weight_span = soup.new_tag("span", **{"class": "weight"})
            weight_span.string = f"{weight:.1%}"
            li.append(weight_span)
            li.append(" ")

            deviation_span = soup.new_tag("span", **{"class": "deviation"})
            deviation_span.string = f"({deviation:+.1%})"
            li.append(deviation_span)

            ul.append(li)

        weightings_div.append(ul)

        # Portfolio metrics section
        metrics_div = soup.new_tag("div", **{"class": "portfolio-metrics"})
        h4 = soup.new_tag("h4")
        h4.string = "Portfolio Metrics"
        metrics_div.append(h4)

        # Total Value
        p = soup.new_tag("p")
        strong = soup.new_tag("strong")
        strong.string = "Total Value:"
        p.append(strong)
        p.append(f" ${result.current_portfolio.total_value:,.2f}")
        metrics_div.append(p)

        # Positions Needing Rebalancing
        p = soup.new_tag("p")
        strong = soup.new_tag("strong")
        strong.string = "Positions Needing Rebalancing:"
        p.append(strong)
        p.append(f" {len(result.current_portfolio.positions_needing_rebalancing)}")
        metrics_div.append(p)

        # Risk Score
        p = soup.new_tag("p")
        strong = soup.new_tag("strong")
        strong.string = "Risk Score:"
        p.append(strong)
        p.append(f" {result.current_risk_score:.1f}/10")
        metrics_div.append(p)

        full_content = str(weightings_div) + str(metrics_div)
        self.report_generator.add_section("Current Portfolio", full_content, "portfolio", order=2)

    def _add_trade_recommendations_section(self, result: RebalancingResult) -> None:
        """Add trade recommendations section."""
        soup = BeautifulSoup("", "html.parser")

        if not result.trade_recommendations:
            div = soup.new_tag("div", **{"class": "no-trades"})

            p = soup.new_tag("p")
            p.append("✅ ")
            strong = soup.new_tag("strong")
            strong.string = "No trades required"
            p.append(strong)
            p.append(" - portfolio is within tolerance bands.")
            div.append(p)

            p = soup.new_tag("p")
            p.string = "Your portfolio allocation is well-balanced and no rebalancing is needed at this time."
            div.append(p)

            content = str(div)
        else:
            div = soup.new_tag("div", **{"class": "trade-recommendations"})
            table = soup.new_tag("table", **{"class": "trades-table"})

            # Table header
            thead = soup.new_tag("thead")
            tr = soup.new_tag("tr")
            for header in ["Symbol", "Action", "Shares", "Trade Value", "Current Weight", "Target Weight", "Projected Weight"]:
                th = soup.new_tag("th")
                th.string = header
                tr.append(th)
            thead.append(tr)
            table.append(thead)

            # Table body
            tbody = soup.new_tag("tbody")
            for trade in result.trade_recommendations:
                action_class = trade.action.value.lower()
                tr = soup.new_tag("tr", **{"class": f"trade-{action_class}"})

                # Symbol
                td = soup.new_tag("td", **{"class": "symbol"})
                td.string = trade.symbol
                tr.append(td)

                # Action
                td = soup.new_tag("td", **{"class": f"action {action_class}"})
                td.string = trade.action.value
                tr.append(td)

                # Shares
                td = soup.new_tag("td", **{"class": "shares"})
                td.string = f"{trade.shares:,}"
                tr.append(td)

                # Trade Value
                td = soup.new_tag("td", **{"class": "trade-value"})
                td.string = f"${trade.trade_value:,.2f}"
                tr.append(td)

                # Current Weight
                td = soup.new_tag("td", **{"class": "current-weight"})
                td.string = f"{getattr(trade, 'current_weight', 0):.1%}"
                tr.append(td)

                # Target Weight
                td = soup.new_tag("td", **{"class": "target-weight"})
                td.string = f"{getattr(trade, 'target_weight', 0):.1%}"
                tr.append(td)

                # Projected Weight
                td = soup.new_tag("td", **{"class": "projected-weight"})
                td.string = f"{getattr(trade, 'projected_weight_after_trade', 0):.1%}"
                tr.append(td)

                tbody.append(tr)

            table.append(tbody)
            div.append(table)
            content = str(div)

        self.report_generator.add_section("Trade Recommendations", content, "data", order=3)

    def _add_cost_analysis_section(self, result: RebalancingResult) -> None:
        """Add cost analysis section."""
        soup = BeautifulSoup("", "html.parser")

        div = soup.new_tag("div", **{"class": "cost-analysis"})

        h4 = soup.new_tag("h4")
        h4.string = "Transaction Cost Breakdown"
        div.append(h4)

        metrics_div = soup.new_tag("div", **{"class": "cost-metrics"})

        # Commission Costs
        item_div = soup.new_tag("div", **{"class": "cost-item"})
        label_span = soup.new_tag("span", **{"class": "label"})
        label_span.string = "Commission Costs:"
        item_div.append(label_span)
        value_span = soup.new_tag("span", **{"class": "value"})
        value_span.string = f"${result.cost_analysis.commission_costs:.2f}"
        item_div.append(value_span)
        metrics_div.append(item_div)

        # Spread Costs
        item_div = soup.new_tag("div", **{"class": "cost-item"})
        label_span = soup.new_tag("span", **{"class": "label"})
        label_span.string = "Spread Costs:"
        item_div.append(label_span)
        value_span = soup.new_tag("span", **{"class": "value"})
        value_span.string = f"${result.cost_analysis.spread_costs:.2f}"
        item_div.append(value_span)
        metrics_div.append(item_div)

        # Total Transaction Costs
        item_div = soup.new_tag("div", **{"class": "cost-item total"})
        label_span = soup.new_tag("span", **{"class": "label"})
        label_span.string = "Total Transaction Costs:"
        item_div.append(label_span)
        value_span = soup.new_tag("span", **{"class": "value"})
        value_span.string = f"${result.cost_analysis.total_transaction_costs:.2f}"
        item_div.append(value_span)
        metrics_div.append(item_div)

        # Cost as % of Portfolio
        item_div = soup.new_tag("div", **{"class": "cost-item"})
        label_span = soup.new_tag("span", **{"class": "label"})
        label_span.string = "Cost as % of Portfolio:"
        item_div.append(label_span)
        value_span = soup.new_tag("span", **{"class": "value"})
        value_span.string = f"{result.cost_analysis.cost_as_percentage:.3f}%"
        item_div.append(value_span)
        metrics_div.append(item_div)

        # Break-even Days
        item_div = soup.new_tag("div", **{"class": "cost-item"})
        label_span = soup.new_tag("span", **{"class": "label"})
        label_span.string = "Break-even Days:"
        item_div.append(label_span)
        value_span = soup.new_tag("span", **{"class": "value"})
        value_span.string = str(result.cost_analysis.break_even_days or "N/A")
        item_div.append(value_span)
        metrics_div.append(item_div)

        div.append(metrics_div)
        cost_content = str(div)
        self.report_generator.add_section("Cost Analysis", cost_content, "financial", order=4)

    def _add_risk_analysis_section(self, result: RebalancingResult) -> None:
        """Add risk analysis section."""
        soup = BeautifulSoup("", "html.parser")

        risk_improvement_class = (
            "improvement" if result.risk_improvement > 0 else "degradation" if result.risk_improvement < 0 else "neutral"
        )

        div = soup.new_tag("div", **{"class": "risk-analysis"})

        h4 = soup.new_tag("h4")
        h4.string = "Risk Assessment"
        div.append(h4)

        metrics_div = soup.new_tag("div", **{"class": "risk-metrics"})

        # Current Risk Score
        item_div = soup.new_tag("div", **{"class": "risk-item"})
        label_span = soup.new_tag("span", **{"class": "label"})
        label_span.string = "Current Risk Score:"
        item_div.append(label_span)
        value_span = soup.new_tag("span", **{"class": "value risk-score"})
        value_span.string = f"{result.current_risk_score:.1f}/10"
        item_div.append(value_span)
        metrics_div.append(item_div)

        # Projected Risk Score
        item_div = soup.new_tag("div", **{"class": "risk-item"})
        label_span = soup.new_tag("span", **{"class": "label"})
        label_span.string = "Projected Risk Score:"
        item_div.append(label_span)
        value_span = soup.new_tag("span", **{"class": "value risk-score"})
        value_span.string = f"{result.projected_risk_score:.1f}/10"
        item_div.append(value_span)
        metrics_div.append(item_div)

        # Risk Change
        item_div = soup.new_tag("div", **{"class": f"risk-item {risk_improvement_class}"})
        label_span = soup.new_tag("span", **{"class": "label"})
        label_span.string = "Risk Change:"
        item_div.append(label_span)
        value_span = soup.new_tag("span", **{"class": "value"})
        value_span.string = f"{result.risk_improvement:+.1f}"
        item_div.append(value_span)
        metrics_div.append(item_div)

        div.append(metrics_div)

        # Risk Interpretation
        interp_div = soup.new_tag("div", **{"class": "risk-interpretation"})
        h5 = soup.new_tag("h5")
        h5.string = "Risk Interpretation"
        interp_div.append(h5)

        p = soup.new_tag("p")
        if result.risk_improvement > 0.5:
            p.append("✅ ")
            strong = soup.new_tag("strong")
            strong.string = "Significant Risk Reduction:"
            p.append(strong)
            p.append(" Rebalancing will meaningfully reduce portfolio risk.")
        elif result.risk_improvement > 0:
            p.append("🟡 ")
            strong = soup.new_tag("strong")
            strong.string = "Modest Risk Reduction:"
            p.append(strong)
            p.append(" Rebalancing will slightly reduce portfolio risk.")
        elif result.risk_improvement < -0.5:
            p.append("⚠️ ")
            strong = soup.new_tag("strong")
            strong.string = "Risk Increase:"
            p.append(strong)
            p.append(" Rebalancing may increase portfolio risk. Consider carefully.")
        else:
            p.append("➡️ ")
            strong = soup.new_tag("strong")
            strong.string = "Neutral Risk Impact:"
            p.append(strong)
            p.append(" Rebalancing will have minimal impact on portfolio risk.")

        interp_div.append(p)
        div.append(interp_div)

        risk_content = str(div)
        self.report_generator.add_section("Risk Analysis", risk_content, "risk", order=5)

    def _add_projected_portfolio_section(self, result: RebalancingResult) -> None:
        """Add projected portfolio section."""
        soup = BeautifulSoup("", "html.parser")

        div = soup.new_tag("div", **{"class": "projected-portfolio"})

        h4 = soup.new_tag("h4")
        h4.string = "Projected Allocations After Rebalancing"
        div.append(h4)

        ul = soup.new_tag("ul", **{"class": "projected-weightings"})

        for symbol, weight in result.projected_portfolio.weightings.items():
            target_weight = result.current_portfolio.weightings.get(symbol, 0.0)  # This should be target weight
            deviation = weight - target_weight
            deviation_class = "on-target" if abs(deviation) < 0.01 else "close-to-target"

            li = soup.new_tag("li", **{"class": deviation_class})

            symbol_span = soup.new_tag("span", **{"class": "symbol"})
            symbol_span.string = symbol
            li.append(symbol_span)
            li.append(": ")

            weight_span = soup.new_tag("span", **{"class": "weight"})
            weight_span.string = f"{weight:.1%}"
            li.append(weight_span)
            li.append(" ")

            deviation_span = soup.new_tag("span", **{"class": "deviation"})
            deviation_span.string = f"({deviation:+.1%} from current)"
            li.append(deviation_span)

            ul.append(li)

        div.append(ul)

        # Projected metrics
        metrics_div = soup.new_tag("div", **{"class": "projected-metrics"})

        p = soup.new_tag("p")
        strong = soup.new_tag("strong")
        strong.string = "Projected Positions Within Tolerance:"
        p.append(strong)
        p.append(f" {result.execution_summary.positions_within_tolerance}")
        metrics_div.append(p)

        p = soup.new_tag("p")
        strong = soup.new_tag("strong")
        strong.string = "Projected Risk Score:"
        p.append(strong)
        p.append(f" {result.projected_risk_score:.1f}/10")
        metrics_div.append(p)

        div.append(metrics_div)

        projected_html = str(div)
        self.report_generator.add_section("Projected Portfolio", projected_html, "growth", order=6)

    def _add_french_sections(self, result: RebalancingResult) -> None:
        """Add required French sections."""
        soup = BeautifulSoup("", "html.parser")

        div = soup.new_tag("div", **{"class": "synthese-10k"})

        h3 = soup.new_tag("h3")
        h3.string = "Synthèse du Rééquilibrage de Portefeuille"
        div.append(h3)

        content_div = soup.new_tag("div", **{"class": "synthese-content"})

        # Date d'analyse
        p = soup.new_tag("p")
        strong = soup.new_tag("strong")
        strong.string = "Date d'analyse:"
        p.append(strong)
        p.append(f" {result.analysis_timestamp.strftime('%Y-%m-%d %H:%M')}")
        content_div.append(p)

        # Recommandation globale
        p = soup.new_tag("p")
        strong = soup.new_tag("strong")
        strong.string = "Recommandation globale:"
        p.append(strong)
        p.append(f" {self._translate_recommendation(result.overall_recommendation.value)}")
        content_div.append(p)

        # Nombre total de transactions
        p = soup.new_tag("p")
        strong = soup.new_tag("strong")
        strong.string = "Nombre total de transactions:"
        p.append(strong)
        p.append(f" {result.execution_summary.total_trades_required}")
        content_div.append(p)

        # Coûts de transaction totaux
        p = soup.new_tag("p")
        strong = soup.new_tag("strong")
        strong.string = "Coûts de transaction totaux:"
        p.append(strong)
        p.append(f" {result.cost_analysis.total_transaction_costs:.2f} $")
        content_div.append(p)

        # Score de risque
        p = soup.new_tag("p")
        strong = soup.new_tag("strong")
        strong.string = "Score de risque:"
        p.append(strong)
        p.append(f" {result.current_risk_score:.1f}/10 → {result.projected_risk_score:.1f}/10")
        content_div.append(p)

        # Prochaine révision
        p = soup.new_tag("p")
        strong = soup.new_tag("strong")
        strong.string = "Prochaine révision:"
        p.append(strong)
        p.append(f" {result.next_review_date.strftime('%Y-%m-%d')}")
        content_div.append(p)

        div.append(content_div)

        # Recommandations Principales
        rec_div = soup.new_tag("div", **{"class": "recommandations-francais"})
        h4 = soup.new_tag("h4")
        h4.string = "Recommandations Principales"
        rec_div.append(h4)

        if result.execution_summary.total_trades_required == 0:
            p = soup.new_tag("p")
            p.string = "Aucune transaction requise - le portefeuille est bien équilibré."
            rec_div.append(p)
        else:
            p = soup.new_tag("p")
            p.string = f"Exécuter {result.execution_summary.total_trades_required} transactions pour optimiser l'allocation."
            rec_div.append(p)

            p = soup.new_tag("p")
            p.string = f"Temps d'exécution estimé: {result.execution_summary.estimated_execution_time}"
            rec_div.append(p)

        div.append(rec_div)

        french_summary = str(div)
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
