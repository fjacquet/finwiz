"""
Section content generators for rebalancing reports.

This module contains methods to generate content for different sections
of portfolio rebalancing reports using BeautifulSoup for proper HTML generation.
"""

import logging
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup

if TYPE_CHECKING:
    from finwiz.schemas.portfolio_rebalancing import RebalancingResult

from finwiz.tools.rebalancing_formatters import RebalancingFormatters

logger = logging.getLogger(__name__)


class RebalancingSections:
    """Content generators for rebalancing report sections."""

    def __init__(self) -> None:
        """Initialize the sections generator."""
        self.formatters = RebalancingFormatters()

    def generate_executive_summary_content(self, result: "RebalancingResult", language: str) -> str:
        """Generate executive summary section content using BeautifulSoup."""
        is_french = language == "fr"

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

        # Create soup and main container
        soup = BeautifulSoup("", "html.parser")
        main_div = soup.new_tag("div", **{"class": "executive-summary"})

        # Status indicator
        status_div = soup.new_tag("div", **{"class": f"status-indicator {result.overall_recommendation.value.lower()}"})

        status_h3 = soup.new_tag("h3")
        status_h3.string = f"{status_emoji} {status_text}"
        status_div.append(status_h3)

        status_p = soup.new_tag("p")
        status_strong = soup.new_tag("strong")
        status_strong.string = "Recommandation" if is_french else "Recommendation"
        status_p.append(status_strong)
        status_p.append(f": {result.overall_recommendation.value}")
        status_div.append(status_p)

        main_div.append(status_div)

        # Summary metrics
        metrics_div = soup.new_tag("div", **{"class": "summary-metrics"})

        # Create metric cards
        metrics_data = [
            ("Transactions Requises" if is_french else "Trades Required", str(total_trades)),
            ("Positions à Ajuster" if is_french else "Positions to Adjust", str(positions_needing_action)),
            ("Coûts Estimés" if is_french else "Estimated Costs", f"${result.cost_analysis.total_transaction_costs:,.2f}"),
            ("Amélioration du Risque" if is_french else "Risk Improvement", f"{result.risk_improvement:+.2f}"),
        ]

        for i, (label, value) in enumerate(metrics_data):
            card_div = soup.new_tag("div", **{"class": "metric-card"})

            card_h4 = soup.new_tag("h4")
            card_h4.string = label
            card_div.append(card_h4)

            card_span = soup.new_tag("span", **{"class": "metric-value"})
            if i == 3:  # Risk improvement - add positive/negative class
                card_span["class"] = f"metric-value {'positive' if result.risk_improvement > 0 else 'negative'}"
            card_span.string = value
            card_div.append(card_span)

            metrics_div.append(card_div)

        main_div.append(metrics_div)
        soup.append(main_div)

        return str(soup)

    def generate_current_portfolio_content(self, result: "RebalancingResult", language: str) -> str:
        """Generate current portfolio analysis section content using BeautifulSoup."""
        is_french = language == "fr"
        current = result.current_portfolio

        # Create soup and main container
        soup = BeautifulSoup("", "html.parser")
        main_div = soup.new_tag("div", **{"class": "portfolio-overview"})

        # Portfolio stats
        stats_div = soup.new_tag("div", **{"class": "portfolio-stats"})

        stats_data = [
            ("Valeur Totale" if is_french else "Total Value", f"${current.total_value:,.2f}"),
            ("Nombre de Positions" if is_french else "Number of Positions", str(len(current.weightings))),
            (
                "Positions Hors Tolérance" if is_french else "Positions Outside Tolerance",
                str(len(current.positions_needing_rebalancing)),
            ),
        ]

        for label, value in stats_data:
            p = soup.new_tag("p")
            strong = soup.new_tag("strong")
            strong.string = f"{label}:"
            p.append(strong)
            p.append(f" {value}")
            stats_div.append(p)

        main_div.append(stats_div)

        # Section title
        h4 = soup.new_tag("h4")
        h4.string = "Répartition Actuelle" if is_french else "Current Allocation"
        main_div.append(h4)

        # Use formatters to create holdings table and parse it
        holdings_table_html = self.formatters.create_portfolio_table(
            current.weightings, is_french=is_french, table_class="portfolio-table"
        )

        # Parse the table HTML and append to main div
        table_soup = BeautifulSoup(holdings_table_html, "html.parser")
        if table_soup.find():
            main_div.append(table_soup.find())

        soup.append(main_div)
        return str(soup)

    def generate_trade_recommendations_content(self, result: "RebalancingResult", language: str, include_interactive: bool) -> str:
        """Generate trade recommendations section content using BeautifulSoup."""
        is_french = language == "fr"

        # Create soup and main container
        soup = BeautifulSoup("", "html.parser")

        if not result.trade_recommendations:
            no_trades_div = soup.new_tag("div", **{"class": "no-trades"})
            p = soup.new_tag("p")
            message = (
                "Aucune transaction requise. Votre portefeuille est bien équilibré."
                if is_french
                else "No trades required. Your portfolio is well balanced."
            )
            p.string = f"✅ {message}"
            no_trades_div.append(p)
            soup.append(no_trades_div)
        else:
            trades_div = soup.new_tag("div", **{"class": "trade-recommendations"})

            # Add summary paragraph
            p = soup.new_tag("p")
            strong = soup.new_tag("strong")
            strong.string = "Transactions Recommandées" if is_french else "Recommended Trades"
            p.append(strong)
            p.append(f": {len(result.trade_recommendations)}")
            trades_div.append(p)

            # Use formatters to create trades table and parse it
            trades_table_html = self.formatters.create_trades_table(
                result.trade_recommendations, is_french=is_french, include_interactive=include_interactive
            )

            # Parse the table HTML and append to trades div
            table_soup = BeautifulSoup(trades_table_html, "html.parser")
            if table_soup.find():
                trades_div.append(table_soup.find())

            soup.append(trades_div)

        return str(soup)

    def generate_projected_portfolio_content(self, result: "RebalancingResult", language: str) -> str:
        """Generate projected portfolio analysis section content."""
        is_french = language == "fr"
        projected = result.projected_portfolio

        # Use formatters to create comparison table
        comparison_table = self.formatters.create_before_after_table(
            result.current_portfolio.weightings, projected.weightings, is_french=is_french
        )

        return f"""
        <div class="projected-portfolio">
            <div class="portfolio-stats">
                <p><strong>{"Valeur Totale Projetée" if is_french else "Projected Total Value"}:</strong> 
                   ${projected.total_value:,.2f}</p>
                <p><strong>{"Positions Hors Tolérance" if is_french else "Positions Outside Tolerance"}:</strong> 
                   {len(projected.positions_needing_rebalancing)}</p>
            </div>
            <h4>{"Comparaison Avant/Après" if is_french else "Before/After Comparison"}</h4>
            {comparison_table}
        </div>
        """

    def generate_cost_analysis_content(self, result: "RebalancingResult", language: str) -> str:
        """Generate cost analysis section content using BeautifulSoup."""
        is_french = language == "fr"
        cost = result.cost_analysis

        # Create soup and main container
        soup = BeautifulSoup("", "html.parser")
        main_div = soup.new_tag("div", **{"class": "cost-analysis"})

        # Cost breakdown section
        breakdown_div = soup.new_tag("div", **{"class": "cost-breakdown"})

        cost_items = [
            ("Commissions" if is_french else "Commissions", cost.commission_costs, False),
            ("Écarts Bid-Ask" if is_french else "Bid-Ask Spreads", cost.spread_costs, False),
            ("Impact Marché" if is_french else "Market Impact", cost.market_impact_costs, False),
            ("Total" if is_french else "Total", cost.total_transaction_costs, True),
        ]

        for label, amount, is_total in cost_items:
            item_div = soup.new_tag("div", **{"class": "cost-item total" if is_total else "cost-item"})

            # Label span
            label_span = soup.new_tag("span", **{"class": "cost-label"})
            if is_total:
                strong = soup.new_tag("strong")
                strong.string = f"{label}:"
                label_span.append(strong)
            else:
                label_span.string = f"{label}:"
            item_div.append(label_span)

            # Value span
            value_span = soup.new_tag("span", **{"class": "cost-value"})
            value_text = f"${amount:,.2f}"
            if is_total:
                strong = soup.new_tag("strong")
                strong.string = value_text
                value_span.append(strong)
            else:
                value_span.string = value_text
            item_div.append(value_span)

            breakdown_div.append(item_div)

        main_div.append(breakdown_div)

        # Cost metrics section
        metrics_div = soup.new_tag("div", **{"class": "cost-metrics"})

        # Percentage paragraph
        p1 = soup.new_tag("p")
        strong1 = soup.new_tag("strong")
        strong1.string = "Coûts en % du Portefeuille" if is_french else "Costs as % of Portfolio"
        p1.append(strong1)
        p1.append(f": {cost.cost_as_percentage:.3f}%")
        metrics_div.append(p1)

        # Break-even days paragraph (if available)
        if cost.break_even_days:
            p2 = soup.new_tag("p")
            strong2 = soup.new_tag("strong")
            strong2.string = "Jours pour Rentabiliser" if is_french else "Break-even Days"
            p2.append(strong2)
            p2.append(f": {cost.break_even_days}")
            metrics_div.append(p2)

        main_div.append(metrics_div)
        soup.append(main_div)

        return str(soup)

    def generate_risk_analysis_content(self, result: "RebalancingResult", language: str) -> str:
        """Generate risk analysis section content."""
        is_french = language == "fr"
        risk_change = result.risk_improvement
        risk_direction = "improvement" if risk_change > 0 else "deterioration" if risk_change < 0 else "neutral"

        return f"""
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
                   {self.formatters.get_risk_interpretation(risk_change, is_french)}
                </p>
            </div>
        </div>
        """

    def generate_alternative_scenarios_content(self, result: "RebalancingResult", language: str) -> str:
        """Generate alternative scenarios section content."""
        is_french = language == "fr"

        scenarios_html = ""
        for i, scenario in enumerate(result.alternative_scenarios, 1):
            scenarios_html += f"""
            <div class="scenario-card">
                <h4>{"Scénario" if is_french else "Scenario"} {i}: {scenario.scenario_name}</h4>
                <p><strong>{"Paramètres Modifiés" if is_french else "Modified Parameters"}:</strong></p>
                <ul>
                    {self.formatters.format_scenario_parameters(scenario.modified_parameters, is_french)}
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

        return f"""
        <div class="alternative-scenarios">
            <p>{"Voici des approches alternatives pour le rééquilibrage:" if is_french else "Here are alternative approaches to rebalancing:"}</p>
            {scenarios_html}
        </div>
        """

    def generate_execution_summary_content(self, result: "RebalancingResult", language: str) -> str:
        """Generate execution summary section content."""
        is_french = language == "fr"
        execution = result.execution_summary

        return f"""
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
