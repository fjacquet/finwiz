"""
Rebalancing Report Generator for FinWiz portfolio rebalancing reports.

This module extends the existing HTML report framework to generate comprehensive
rebalancing analysis reports with interactive elements and PDF export functionality.
"""

import logging
from pathlib import Path
from typing import Any

from finwiz.schemas.portfolio_rebalancing import (
    RebalancingResult,
    TradeRecommendation,
)
from finwiz.tools.html_report_generator import HTMLReportGenerator

logger = logging.getLogger(__name__)


class RebalancingReportGenerator(HTMLReportGenerator):
    """
    Generates comprehensive HTML reports for portfolio rebalancing analysis.

    Extends the existing HTMLReportGenerator with rebalancing-specific functionality
    including interactive trade execution elements and scenario comparison tables.
    """

    # Rebalancing-specific emoji mappings
    REBALANCING_EMOJI_MAP = {
        "rebalancing": "⚖️",
        "trade": "💱",
        "buy": "📈",
        "sell": "📉",
        "hold": "⏸️",
        "urgent": "🚨",
        "cost": "💰",
        "improvement": "✅",
        "warning": "⚠️",
        "target": "🎯",
        "current": "📊",
        "projected": "🔮",
        "scenario": "🎭",
        "execution": "⚡",
    }

    def __init__(self, template_path: str | None = None) -> None:
        """Initialize the rebalancing report generator."""
        super().__init__(template_path)
        # Add rebalancing-specific emojis to the base emoji map
        self.EMOJI_MAP.update(self.REBALANCING_EMOJI_MAP)

    def generate_rebalancing_report(
        self,
        result: RebalancingResult,
        title: str = "Portfolio Rebalancing Analysis",
        language: str = "en",
        include_interactive: bool = True,
    ) -> str:
        """
        Generate a comprehensive rebalancing report.

        Args:
            result: Rebalancing analysis result
            title: Report title
            language: Report language (en/fr)
            include_interactive: Whether to include interactive elements

        Returns:
            Complete HTML report as string

        """
        # Clear any existing sections
        self.clear_sections()

        # Add executive summary
        self._add_executive_summary(result, language)

        # Add current portfolio analysis
        self._add_current_portfolio_section(result, language)

        # Add trade recommendations
        self._add_trade_recommendations_section(result, language, include_interactive)

        # Add projected portfolio analysis
        self._add_projected_portfolio_section(result, language)

        # Add cost analysis
        self._add_cost_analysis_section(result, language)

        # Add risk analysis
        self._add_risk_analysis_section(result, language)

        # Add alternative scenarios
        if result.alternative_scenarios:
            self._add_alternative_scenarios_section(result, language)

        # Add execution summary
        self._add_execution_summary_section(result, language)

        # Generate the HTML report
        html_content = self.generate_html(title, language)

        # Add rebalancing-specific CSS and JavaScript if interactive elements are included
        if include_interactive:
            html_content = self._add_interactive_elements(html_content)

        logger.info(f"Generated rebalancing report with {len(self.sections)} sections")
        return html_content

    def _add_executive_summary(self, result: RebalancingResult, language: str) -> None:
        """Add executive summary section."""
        is_french = language == "fr"

        title = "Résumé Exécutif" if is_french else "Executive Summary"

        # Determine overall status
        total_trades = result.execution_summary.total_trades_required
        positions_needing_action = result.execution_summary.positions_requiring_action

        if total_trades == 0:
            status_text = "Aucune action requise" if is_french else "No action required"
            status_emoji = "✅"
        elif positions_needing_action <= 2:
            status_text = "Rééquilibrage mineur recommandé" if is_french else "Minor rebalancing recommended"
            status_emoji = "⚖️"
        else:
            status_text = "Rééquilibrage significatif requis" if is_french else "Significant rebalancing required"
            status_emoji = "🚨"

        content = f"""
        <div class="executive-summary">
            <div class="status-indicator {result.overall_recommendation.value.lower()}">
                <h3>{status_emoji} {status_text}</h3>
                <p><strong>{"Recommandation" if is_french else "Recommendation"}:</strong> {result.overall_recommendation.value}</p>
            </div>

            <div class="summary-metrics">
                <div class="metric-card">
                    <h4>{"Transactions Requises" if is_french else "Trades Required"}</h4>
                    <span class="metric-value">{total_trades}</span>
                </div>
                <div class="metric-card">
                    <h4>{"Positions à Ajuster" if is_french else "Positions to Adjust"}</h4>
                    <span class="metric-value">{positions_needing_action}</span>
                </div>
                <div class="metric-card">
                    <h4>{"Coûts Estimés" if is_french else "Estimated Costs"}</h4>
                    <span class="metric-value">${result.cost_analysis.total_transaction_costs:,.2f}</span>
                </div>
                <div class="metric-card">
                    <h4>{"Amélioration du Risque" if is_french else "Risk Improvement"}</h4>
                    <span class="metric-value {"positive" if result.risk_improvement > 0 else "negative"}">
                        {result.risk_improvement:+.2f}
                    </span>
                </div>
            </div>
        </div>
        """

        self.add_section(title, content, "rebalancing", order=1)

    def _add_current_portfolio_section(self, result: RebalancingResult, language: str) -> None:
        """Add current portfolio analysis section."""
        is_french = language == "fr"
        title = "Analyse du Portefeuille Actuel" if is_french else "Current Portfolio Analysis"

        current = result.current_portfolio

        # Create holdings table
        holdings_table = self._create_portfolio_table(
            current.weightings, current.deviations_from_target, result.trade_recommendations, is_french, table_type="current"
        )

        content = f"""
        <div class="portfolio-overview">
            <div class="portfolio-stats">
                <p><strong>{"Valeur Totale" if is_french else "Total Value"}:</strong> ${current.total_value:,.2f}</p>
                <p><strong>{"Nombre de Positions" if is_french else "Number of Positions"}:</strong> {len(current.weightings)}</p>
                <p><strong>{"Positions Hors Tolérance" if is_french else "Positions Outside Tolerance"}:</strong> {len(current.positions_needing_rebalancing)}</p>
            </div>

            <h4>{"Répartition Actuelle" if is_french else "Current Allocation"}</h4>
            {holdings_table}
        </div>
        """

        self.add_section(title, content, "current", order=2)

    def _add_trade_recommendations_section(self, result: RebalancingResult, language: str, include_interactive: bool) -> None:
        """Add trade recommendations section."""
        is_french = language == "fr"
        title = "Recommandations de Trading" if is_french else "Trade Recommendations"

        if not result.trade_recommendations:
            content = f"""
            <div class="no-trades">
                <p>✅ {"Aucune transaction requise. Votre portefeuille est bien équilibré." if is_french else "No trades required. Your portfolio is well balanced."}</p>
            </div>
            """
        else:
            # Sort recommendations by priority
            sorted_trades = sorted(result.trade_recommendations, key=lambda x: x.priority)

            trades_table = self._create_trades_table(sorted_trades, is_french, include_interactive)

            content = f"""
            <div class="trade-recommendations">
                <p><strong>{"Transactions Recommandées" if is_french else "Recommended Trades"}:</strong> {len(sorted_trades)}</p>
                {trades_table}
            </div>
            """

        self.add_section(title, content, "trade", order=3)

    def _add_projected_portfolio_section(self, result: RebalancingResult, language: str) -> None:
        """Add projected portfolio analysis section."""
        is_french = language == "fr"
        title = "Portefeuille Projeté Après Rééquilibrage" if is_french else "Projected Portfolio After Rebalancing"

        projected = result.projected_portfolio

        # Create comparison table
        comparison_table = self._create_before_after_table(
            result.current_portfolio.weightings, projected.weightings, result.trade_recommendations, is_french
        )

        content = f"""
        <div class="projected-portfolio">
            <div class="portfolio-stats">
                <p><strong>{"Valeur Totale Projetée" if is_french else "Projected Total Value"}:</strong> ${projected.total_value:,.2f}</p>
                <p><strong>{"Positions Hors Tolérance" if is_french else "Positions Outside Tolerance"}:</strong> {len(projected.positions_needing_rebalancing)}</p>
            </div>

            <h4>{"Comparaison Avant/Après" if is_french else "Before/After Comparison"}</h4>
            {comparison_table}
        </div>
        """

        self.add_section(title, content, "projected", order=4)

    def _add_cost_analysis_section(self, result: RebalancingResult, language: str) -> None:
        """Add cost analysis section."""
        is_french = language == "fr"
        title = "Analyse des Coûts" if is_french else "Cost Analysis"

        cost = result.cost_analysis

        content = f"""
        <div class="cost-analysis">
            <div class="cost-breakdown">
                <div class="cost-item">
                    <span class="cost-label">{"Commissions" if is_french else "Commissions"}:</span>
                    <span class="cost-value">${cost.commission_costs:,.2f}</span>
                </div>
                <div class="cost-item">
                    <span class="cost-label">{"Écarts Bid-Ask" if is_french else "Bid-Ask Spreads"}:</span>
                    <span class="cost-value">${cost.spread_costs:,.2f}</span>
                </div>
                <div class="cost-item">
                    <span class="cost-label">{"Impact Marché" if is_french else "Market Impact"}:</span>
                    <span class="cost-value">${cost.market_impact_costs:,.2f}</span>
                </div>
                <div class="cost-item total">
                    <span class="cost-label"><strong>{"Total" if is_french else "Total"}:</strong></span>
                    <span class="cost-value"><strong>${cost.total_transaction_costs:,.2f}</strong></span>
                </div>
            </div>

            <div class="cost-metrics">
                <p><strong>{"Coûts en % du Portefeuille" if is_french else "Costs as % of Portfolio"}:</strong> {cost.cost_as_percentage:.3f}%</p>
                {f"<p><strong>{'Jours pour Rentabiliser' if is_french else 'Break-even Days'}:</strong> {cost.break_even_days}</p>" if cost.break_even_days else ""}
            </div>
        </div>
        """

        self.add_section(title, content, "cost", order=5)

    def _add_risk_analysis_section(self, result: RebalancingResult, language: str) -> None:
        """Add risk analysis section."""
        is_french = language == "fr"
        title = "Analyse des Risques" if is_french else "Risk Analysis"

        risk_change = result.risk_improvement
        risk_direction = "improvement" if risk_change > 0 else "deterioration" if risk_change < 0 else "neutral"

        content = f"""
        <div class="risk-analysis">
            <div class="risk-scores">
                <div class="risk-score current">
                    <h4>{"Score de Risque Actuel" if is_french else "Current Risk Score"}</h4>
                    <span class="score-value">{result.current_risk_score:.1f}/10</span>
                </div>
                <div class="risk-arrow">
                    {"→" if risk_change == 0 else "↓" if risk_change > 0 else "↑"}
                </div>
                <div class="risk-score projected">
                    <h4>{"Score de Risque Projeté" if is_french else "Projected Risk Score"}</h4>
                    <span class="score-value">{result.projected_risk_score:.1f}/10</span>
                </div>
            </div>

            <div class="risk-improvement {risk_direction}">
                <p><strong>{"Changement de Risque" if is_french else "Risk Change"}:</strong> 
                   <span class="risk-value">{risk_change:+.2f}</span>
                   {self._get_risk_interpretation(risk_change, is_french)}
                </p>
            </div>
        </div>
        """

        self.add_section(title, content, "risk", order=6)

    def _add_alternative_scenarios_section(self, result: RebalancingResult, language: str) -> None:
        """Add alternative scenarios section."""
        is_french = language == "fr"
        title = "Scénarios Alternatifs" if is_french else "Alternative Scenarios"

        scenarios_html = ""
        for i, scenario in enumerate(result.alternative_scenarios, 1):
            scenarios_html += f"""
            <div class="scenario-card">
                <h4>{"Scénario" if is_french else "Scenario"} {i}: {scenario.scenario_name}</h4>
                <p><strong>{"Paramètres Modifiés" if is_french else "Modified Parameters"}:</strong></p>
                <ul>
                    {self._format_scenario_parameters(scenario.modified_parameters, is_french)}
                </ul>
                <p><strong>{"Résultat Attendu" if is_french else "Expected Outcome"}:</strong> {scenario.projected_outcome}</p>
                <div class="scenario-metrics">
                    <span class="metric">{"Différence de Coût" if is_french else "Cost Difference"}: 
                        <span class="{"positive" if scenario.cost_difference < 0 else "negative"}">${scenario.cost_difference:+,.2f}</span>
                    </span>
                    <span class="metric">{"Différence de Risque" if is_french else "Risk Difference"}: 
                        <span class="{"positive" if scenario.risk_difference < 0 else "negative"}">{scenario.risk_difference:+.2f}</span>
                    </span>
                </div>
            </div>
            """

        content = f"""
        <div class="alternative-scenarios">
            <p>{"Voici des approches alternatives pour le rééquilibrage:" if is_french else "Here are alternative approaches to rebalancing:"}</p>
            {scenarios_html}
        </div>
        """

        self.add_section(title, content, "scenario", order=7)

    def _add_execution_summary_section(self, result: RebalancingResult, language: str) -> None:
        """Add execution summary section."""
        is_french = language == "fr"
        title = "Résumé d'Exécution" if is_french else "Execution Summary"

        execution = result.execution_summary

        content = f"""
        <div class="execution-summary">
            <div class="execution-stats">
                <div class="stat-item">
                    <span class="stat-label">{"Transactions Totales" if is_french else "Total Trades"}:</span>
                    <span class="stat-value">{execution.total_trades_required}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">{"Temps d'Exécution Estimé" if is_french else "Estimated Execution Time"}:</span>
                    <span class="stat-value">{execution.estimated_execution_time}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">{"Capital Requis" if is_french else "Capital Required"}:</span>
                    <span class="stat-value {"positive" if execution.capital_required < 0 else "negative"}">
                        ${execution.capital_required:+,.2f}
                    </span>
                </div>
            </div>

            <div class="next-steps">
                <h4>{"Prochaines Étapes" if is_french else "Next Steps"}</h4>
                <ol>
                    <li>{"Examiner les recommandations de trading ci-dessus" if is_french else "Review the trade recommendations above"}</li>
                    <li>{"Vérifier les coûts de transaction avec votre courtier" if is_french else "Verify transaction costs with your broker"}</li>
                    <li>{"Exécuter les transactions par ordre de priorité" if is_french else "Execute trades in priority order"}</li>
                    <li>{"Surveiller l'exécution et ajuster si nécessaire" if is_french else "Monitor execution and adjust if needed"}</li>
                </ol>
                <p><strong>{"Prochaine Révision" if is_french else "Next Review"}:</strong> {result.next_review_date.strftime("%Y-%m-%d")}</p>
            </div>
        </div>
        """

        self.add_section(title, content, "execution", order=8)

    def _create_portfolio_table(
        self,
        weightings: dict[str, float],
        deviations: dict[str, float],
        trade_recommendations: list[TradeRecommendation],
        is_french: bool,
        table_type: str = "current",
    ) -> str:
        """Create a portfolio holdings table."""
        # Create a mapping of symbols to trade recommendations
        trade_map = {trade.symbol: trade for trade in trade_recommendations}

        headers = [
            "Symbole" if is_french else "Symbol",
            "Poids Actuel" if is_french else "Current Weight",
            "Déviation" if is_french else "Deviation",
            "Action" if is_french else "Action",
        ]

        rows = []
        for symbol in sorted(weightings.keys()):
            weight = weightings[symbol]
            deviation = deviations.get(symbol, 0.0)
            trade = trade_map.get(symbol)

            # Determine action and styling
            if trade:
                action = trade.action.value
                action_class = f"action-{trade.action.value.lower()}"
            else:
                action = "HOLD"
                action_class = "action-hold"

            # Style deviation based on magnitude
            deviation_class = (
                "deviation-high" if abs(deviation) > 0.05 else "deviation-medium" if abs(deviation) > 0.02 else "deviation-low"
            )

            rows.append(f"""
                <tr>
                    <td class="symbol">{symbol}</td>
                    <td class="weight">{weight:.1%}</td>
                    <td class="deviation {deviation_class}">{deviation:+.1%}</td>
                    <td class="action {action_class}">{action}</td>
                </tr>
            """)

        return f"""
        <table class="portfolio-table">
            <thead>
                <tr>
                    {"".join(f"<th>{header}</th>" for header in headers)}
                </tr>
            </thead>
            <tbody>
                {"".join(rows)}
            </tbody>
        </table>
        """

    def _create_trades_table(self, trades: list[TradeRecommendation], is_french: bool, include_interactive: bool) -> str:
        """Create a trades recommendations table."""
        if not trades:
            return ""

        headers = [
            "Priorité" if is_french else "Priority",
            "Symbole" if is_french else "Symbol",
            "Action" if is_french else "Action",
            "Quantité" if is_french else "Quantity",
            "Prix" if is_french else "Price",
            "Valeur" if is_french else "Value",
            "Coût" if is_french else "Cost",
            "Urgence" if is_french else "Urgency",
        ]

        if include_interactive:
            headers.append("Exécuter" if is_french else "Execute")

        rows = []
        for trade in trades:
            urgency_class = f"urgency-{trade.urgency.value.lower()}"
            action_class = f"action-{trade.action.value.lower()}"

            row = f"""
                <tr class="trade-row" data-symbol="{trade.symbol}">
                    <td class="priority">{trade.priority}</td>
                    <td class="symbol">{trade.symbol}</td>
                    <td class="action {action_class}">{trade.action.value}</td>
                    <td class="quantity">{trade.quantity:,.0f}</td>
                    <td class="price">${trade.current_price:.2f}</td>
                    <td class="value">${trade.trade_value:,.2f}</td>
                    <td class="cost">${trade.total_estimated_cost:.2f}</td>
                    <td class="urgency {urgency_class}">{trade.urgency.value}</td>
            """

            if include_interactive:
                row += f"""
                    <td class="execute">
                        <button class="execute-btn" onclick="executeTradeDialog('{trade.symbol}', '{trade.action.value}', {trade.quantity}, {trade.current_price})">
                            {"Exécuter" if is_french else "Execute"}
                        </button>
                    </td>
                """

            row += "</tr>"

            # Add rationale and warnings as a separate row
            if trade.rationale or trade.market_impact_warning or trade.tax_implications:
                details_row = f"""
                    <tr class="trade-details">
                        <td colspan="{len(headers)}" class="trade-rationale">
                            <div class="rationale-content">
                                <strong>{"Justification" if is_french else "Rationale"}:</strong> {trade.rationale}
                """

                if trade.market_impact_warning:
                    details_row += f"""
                                <div class="market-warning">
                                    <strong>⚠️ {"Avertissement" if is_french else "Warning"}:</strong> {trade.market_impact_warning}
                                </div>
                    """

                if trade.tax_implications:
                    details_row += f"""
                                <div class="tax-implications">
                                    <strong>💰 {"Implications Fiscales" if is_french else "Tax Implications"}:</strong> {trade.tax_implications}
                                </div>
                    """

                details_row += """
                            </div>
                        </td>
                    </tr>
                """
                rows.append(row)
                rows.append(details_row)
            else:
                rows.append(row)

        return f"""
        <table class="trades-table">
            <thead>
                <tr>
                    {"".join(f"<th>{header}</th>" for header in headers)}
                </tr>
            </thead>
            <tbody>
                {"".join(rows)}
            </tbody>
        </table>
        """

    def _create_before_after_table(
        self,
        current_weights: dict[str, float],
        projected_weights: dict[str, float],
        trades: list[TradeRecommendation],
        is_french: bool,
    ) -> str:
        """Create a before/after comparison table."""
        trade_map = {trade.symbol: trade for trade in trades}

        headers = [
            "Symbole" if is_french else "Symbol",
            "Avant" if is_french else "Before",
            "Après" if is_french else "After",
            "Changement" if is_french else "Change",
            "Action" if is_french else "Action",
        ]

        rows = []
        for symbol in sorted(current_weights.keys()):
            current = current_weights[symbol]
            projected = projected_weights.get(symbol, current)
            change = projected - current
            trade = trade_map.get(symbol)

            change_class = "positive" if change > 0.001 else "negative" if change < -0.001 else "neutral"
            action = trade.action.value if trade else "HOLD"
            action_class = f"action-{action.lower()}"

            rows.append(f"""
                <tr>
                    <td class="symbol">{symbol}</td>
                    <td class="weight-before">{current:.1%}</td>
                    <td class="weight-after">{projected:.1%}</td>
                    <td class="weight-change {change_class}">{change:+.1%}</td>
                    <td class="action {action_class}">{action}</td>
                </tr>
            """)

        return f"""
        <table class="comparison-table">
            <thead>
                <tr>
                    {"".join(f"<th>{header}</th>" for header in headers)}
                </tr>
            </thead>
            <tbody>
                {"".join(rows)}
            </tbody>
        </table>
        """

    def _format_scenario_parameters(self, parameters: dict[str, Any], is_french: bool) -> str:
        """Format scenario parameters as HTML list items."""
        items = []
        for key, value in parameters.items():
            if isinstance(value, float):
                if key.endswith("_rate") or key.endswith("_tolerance") or key == "tolerance":
                    formatted_value = f"{value:.1%}"
                else:
                    formatted_value = f"{value:.2f}"
            else:
                formatted_value = str(value)

            # Translate common parameter names
            param_translations = {
                "tolerance": "tolérance" if is_french else "tolerance",
                "global_tolerance": "tolérance globale" if is_french else "global tolerance",
                "capital": "capital" if is_french else "capital",
                "method": "méthode" if is_french else "method",
                "cost_rate": "taux de coût" if is_french else "cost rate",
            }

            translated_key = param_translations.get(key, key)
            items.append(f"<li><strong>{translated_key}:</strong> {formatted_value}</li>")

        return "".join(items)

    def _get_risk_interpretation(self, risk_change: float, is_french: bool) -> str:
        """Get risk change interpretation."""
        if abs(risk_change) < 0.1:
            return " (négligeable)" if is_french else " (negligible)"
        elif risk_change > 0.5:
            return " (amélioration significative)" if is_french else " (significant improvement)"
        elif risk_change > 0:
            return " (amélioration)" if is_french else " (improvement)"
        elif risk_change < -0.5:
            return " (dégradation significative)" if is_french else " (significant deterioration)"
        else:
            return " (dégradation)" if is_french else " (deterioration)"

    def _add_interactive_elements(self, html_content: str) -> str:
        """Add interactive CSS and JavaScript to the HTML content."""
        # Enhanced CSS for rebalancing reports
        enhanced_css = """
        <style>
        /* Rebalancing-specific styles */
        .executive-summary {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }

        .status-indicator {
            text-align: center;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
        }

        .status-indicator.rebalance_now {
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
        }

        .status-indicator.no_action {
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
        }

        .summary-metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }

        .metric-card {
            background: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .metric-card h4 {
            margin: 0 0 10px 0;
            font-size: 0.9em;
            color: #666;
            border: none;
        }

        .metric-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #2c3e50;
        }

        .metric-value.positive {
            color: #27ae60;
        }

        .metric-value.negative {
            color: #e74c3c;
        }

        /* Table styles */
        .portfolio-table, .trades-table, .comparison-table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .portfolio-table th, .trades-table th, .comparison-table th {
            background: #34495e;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }

        .portfolio-table td, .trades-table td, .comparison-table td {
            padding: 10px 12px;
            border-bottom: 1px solid #eee;
        }

        .portfolio-table tr:hover, .trades-table tr:hover, .comparison-table tr:hover {
            background-color: #f8f9fa;
        }

        /* Action styling */
        .action-buy {
            color: #27ae60;
            font-weight: bold;
        }

        .action-sell {
            color: #e74c3c;
            font-weight: bold;
        }

        .action-hold {
            color: #7f8c8d;
        }

        /* Deviation styling */
        .deviation-high {
            color: #e74c3c;
            font-weight: bold;
        }

        .deviation-medium {
            color: #f39c12;
            font-weight: bold;
        }

        .deviation-low {
            color: #27ae60;
        }

        /* Urgency styling */
        .urgency-critical {
            background-color: #e74c3c;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
        }

        .urgency-high {
            background-color: #f39c12;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
        }

        .urgency-medium {
            background-color: #3498db;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
        }

        .urgency-low {
            background-color: #95a5a6;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
        }

        /* Interactive elements */
        .execute-btn {
            background: #3498db;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.8em;
            transition: background-color 0.3s;
        }

        .execute-btn:hover {
            background: #2980b9;
        }

        .execute-btn:disabled {
            background: #bdc3c7;
            cursor: not-allowed;
        }

        /* Trade details */
        .trade-details {
            background-color: #f8f9fa;
        }

        .trade-rationale {
            padding: 15px;
            font-size: 0.9em;
            border-top: 1px solid #dee2e6;
        }

        .rationale-content {
            line-height: 1.4;
        }

        .market-warning {
            margin-top: 8px;
            padding: 8px;
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 4px;
            color: #856404;
        }

        .tax-implications {
            margin-top: 8px;
            padding: 8px;
            background-color: #d1ecf1;
            border: 1px solid #bee5eb;
            border-radius: 4px;
            color: #0c5460;
        }

        /* Risk analysis */
        .risk-scores {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 30px;
            margin: 20px 0;
        }

        .risk-score {
            text-align: center;
            padding: 15px;
            border-radius: 8px;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .risk-score h4 {
            margin: 0 0 10px 0;
            font-size: 0.9em;
            color: #666;
            border: none;
        }

        .score-value {
            font-size: 2em;
            font-weight: bold;
            color: #2c3e50;
        }

        .risk-arrow {
            font-size: 2em;
            color: #3498db;
        }

        .risk-improvement {
            text-align: center;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
        }

        .risk-improvement.improvement {
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
        }

        .risk-improvement.deterioration {
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
        }

        .risk-improvement.neutral {
            background-color: #e2e3e5;
            border: 1px solid #d6d8db;
        }

        /* Cost analysis */
        .cost-breakdown {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
        }

        .cost-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }

        .cost-item.total {
            border-top: 2px solid #34495e;
            border-bottom: none;
            margin-top: 10px;
            padding-top: 15px;
        }

        .cost-label {
            color: #666;
        }

        .cost-value {
            font-weight: bold;
            color: #2c3e50;
        }

        /* Scenario cards */
        .scenario-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .scenario-metrics {
            display: flex;
            gap: 20px;
            margin-top: 15px;
        }

        .scenario-metrics .metric {
            padding: 8px 12px;
            background: #f8f9fa;
            border-radius: 4px;
            font-size: 0.9em;
        }

        /* Execution summary */
        .execution-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 15px 0;
        }

        .stat-item {
            display: flex;
            justify-content: space-between;
            padding: 10px 15px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .stat-label {
            color: #666;
        }

        .stat-value {
            font-weight: bold;
            color: #2c3e50;
        }

        .next-steps {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin-top: 20px;
        }

        .next-steps h4 {
            margin-top: 0;
            color: #2c3e50;
            border: none;
        }

        .next-steps ol {
            padding-left: 20px;
        }

        .next-steps li {
            margin-bottom: 8px;
            padding-left: 0;
        }

        .next-steps li::before {
            display: none;
        }

        /* Responsive design */
        @media (max-width: 768px) {
            .summary-metrics {
                grid-template-columns: 1fr;
            }

            .risk-scores {
                flex-direction: column;
                gap: 15px;
            }

            .scenario-metrics {
                flex-direction: column;
                gap: 10px;
            }

            .execution-stats {
                grid-template-columns: 1fr;
            }
        }

        /* Print styles */
        @media print {
            .execute-btn {
                display: none;
            }

            .section {
                break-inside: avoid;
            }
        }
        </style>
        """

        # JavaScript for interactive elements
        interactive_js = """
        <script>
        function executeTradeDialog(symbol, action, quantity, price) {
            const message = `Execute ${action} order for ${quantity} shares of ${symbol} at $${price.toFixed(2)}?`;

            if (confirm(message)) {
                // In a real implementation, this would integrate with a broker API
                alert(`Trade order submitted for ${symbol}. This is a demo - no actual trade was executed.`);

                // Disable the button to prevent duplicate orders
                event.target.disabled = true;
                event.target.textContent = 'Submitted';
                event.target.style.backgroundColor = '#95a5a6';
            }
        }

        // Add click handlers for scenario comparison
        document.addEventListener('DOMContentLoaded', function() {
            const scenarioCards = document.querySelectorAll('.scenario-card');
            scenarioCards.forEach(card => {
                card.addEventListener('click', function() {
                    // Toggle selection
                    this.classList.toggle('selected');

                    // Update styling
                    if (this.classList.contains('selected')) {
                        this.style.borderLeft = '4px solid #3498db';
                        this.style.backgroundColor = '#f8f9fa';
                    } else {
                        this.style.borderLeft = 'none';
                        this.style.backgroundColor = 'white';
                    }
                });
            });
        });
        </script>
        """

        # Insert the enhanced CSS and JavaScript before the closing </head> tag
        head_close_index = html_content.find("</head>")
        if head_close_index != -1:
            html_content = html_content[:head_close_index] + enhanced_css + interactive_js + html_content[head_close_index:]

        return html_content

    def export_to_pdf(self, html_content: str, output_path: str) -> None:
        """
        Export HTML report to PDF format.

        Args:
            html_content: HTML content to convert
            output_path: Path where to save the PDF file

        Note:
            This is a placeholder implementation. In production, you would use
            a library like weasyprint, pdfkit, or playwright for PDF generation.

        """
        try:
            # For now, we'll save the HTML content with a note about PDF conversion
            pdf_note = """
            <!-- PDF Export Note -->
            <!-- This HTML report can be converted to PDF using tools like: -->
            <!-- - weasyprint: pip install weasyprint -->
            <!-- - pdfkit: pip install pdfkit (requires wkhtmltopdf) -->
            <!-- - playwright: pip install playwright -->
            <!-- Example: weasyprint report.html report.pdf -->
            """

            html_with_note = html_content.replace("</head>", f"{pdf_note}</head>")

            # Save HTML file that can be converted to PDF
            html_path = output_path.replace(".pdf", ".html") if output_path.endswith(".pdf") else f"{output_path}.html"

            output_file = Path(html_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(html_with_note, encoding="utf-8")

            logger.info(f"HTML report saved to {html_path} (ready for PDF conversion)")

            # TODO: Implement actual PDF conversion
            # Example with weasyprint:
            # import weasyprint
            # weasyprint.HTML(string=html_content).write_pdf(output_path)

        except Exception as e:
            logger.error(f"Error exporting to PDF: {e}")
            raise
