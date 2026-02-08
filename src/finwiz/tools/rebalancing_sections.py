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
        main_div = soup.new_tag("div", attrs={"class": "executive-summary"})

        # Status indicator
        status_div = soup.new_tag("div", attrs={"class": f"status-indicator {result.overall_recommendation.value.lower()}"})

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
        metrics_div = soup.new_tag("div", attrs={"class": "summary-metrics"})

        # Create metric cards
        metrics_data = [
            ("Transactions Requises" if is_french else "Trades Required", str(total_trades)),
            ("Positions à Ajuster" if is_french else "Positions to Adjust", str(positions_needing_action)),
            ("Coûts Estimés" if is_french else "Estimated Costs", f"${result.cost_analysis.total_transaction_costs:,.2f}"),
            ("Amélioration du Risque" if is_french else "Risk Improvement", f"{result.risk_improvement:+.2f}"),
        ]

        for i, (label, value) in enumerate(metrics_data):
            card_div = soup.new_tag("div", attrs={"class": "metric-card"})

            card_h4 = soup.new_tag("h4")
            card_h4.string = label
            card_div.append(card_h4)

            card_span = soup.new_tag("span", attrs={"class": "metric-value"})
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
        main_div = soup.new_tag("div", attrs={"class": "portfolio-overview"})

        # Portfolio stats
        stats_div = soup.new_tag("div", attrs={"class": "portfolio-stats"})

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
        holdings_table_html = self.formatters.create_portfolio_table(current.weightings, is_french=is_french, table_class="portfolio-table")

        # Parse the table HTML and append to main div
        table_soup = BeautifulSoup(holdings_table_html, "html.parser")
        table_tag = table_soup.find()
        if table_tag is not None:
            main_div.append(table_tag)

        soup.append(main_div)
        return str(soup)

    def generate_trade_recommendations_content(self, result: "RebalancingResult", language: str, include_interactive: bool) -> str:
        """Generate trade recommendations section content using BeautifulSoup."""
        is_french = language == "fr"

        # Create soup and main container
        soup = BeautifulSoup("", "html.parser")

        if not result.trade_recommendations:
            no_trades_div = soup.new_tag("div", attrs={"class": "no-trades"})
            p = soup.new_tag("p")
            message = "Aucune transaction requise. Votre portefeuille est bien équilibré." if is_french else "No trades required. Your portfolio is well balanced."
            p.string = f"✅ {message}"
            no_trades_div.append(p)
            soup.append(no_trades_div)
        else:
            trades_div = soup.new_tag("div", attrs={"class": "trade-recommendations"})

            # Add summary paragraph
            p = soup.new_tag("p")
            strong = soup.new_tag("strong")
            strong.string = "Transactions Recommandées" if is_french else "Recommended Trades"
            p.append(strong)
            p.append(f": {len(result.trade_recommendations)}")
            trades_div.append(p)

            # Use formatters to create trades table and parse it
            trades_table_html = self.formatters.create_trades_table(result.trade_recommendations, is_french=is_french, include_interactive=include_interactive)

            # Parse the table HTML and append to trades div
            table_soup = BeautifulSoup(trades_table_html, "html.parser")
            table_tag = table_soup.find()
            if table_tag is not None:
                trades_div.append(table_tag)

            soup.append(trades_div)

        return str(soup)

    def generate_projected_portfolio_content(self, result: "RebalancingResult", language: str) -> str:
        """Generate projected portfolio analysis section content."""
        is_french = language == "fr"
        projected = result.projected_portfolio

        # Use formatters to create comparison table
        comparison_table = self.formatters.create_before_after_table(result.current_portfolio.weightings, projected.weightings, is_french=is_french)

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
        main_div = soup.new_tag("div", attrs={"class": "cost-analysis"})

        # Cost breakdown section
        breakdown_div = soup.new_tag("div", attrs={"class": "cost-breakdown"})

        cost_items = [
            ("Commissions" if is_french else "Commissions", cost.commission_costs, False),
            ("Écarts Bid-Ask" if is_french else "Bid-Ask Spreads", cost.spread_costs, False),
            ("Impact Marché" if is_french else "Market Impact", cost.market_impact_costs, False),
            ("Total" if is_french else "Total", cost.total_transaction_costs, True),
        ]

        for label, amount, is_total in cost_items:
            item_div = soup.new_tag("div", attrs={"class": "cost-item total" if is_total else "cost-item"})

            # Label span
            label_span = soup.new_tag("span", attrs={"class": "cost-label"})
            if is_total:
                strong = soup.new_tag("strong")
                strong.string = f"{label}:"
                label_span.append(strong)
            else:
                label_span.string = f"{label}:"
            item_div.append(label_span)

            # Value span
            value_span = soup.new_tag("span", attrs={"class": "cost-value"})
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
        metrics_div = soup.new_tag("div", attrs={"class": "cost-metrics"})

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

        # Create soup and main container
        soup = BeautifulSoup("", "html.parser")
        main_div = soup.new_tag("div", attrs={"class": "alternative-scenarios"})

        # Add intro paragraph
        intro_p = soup.new_tag("p")
        if is_french:
            intro_text = "Voici des approches alternatives pour le rééquilibrage:"
        else:
            intro_text = "Here are alternative approaches to rebalancing:"
        intro_p.string = intro_text
        main_div.append(intro_p)

        # Generate scenario cards
        for i, scenario in enumerate(result.alternative_scenarios, 1):
            scenario_div = soup.new_tag("div", attrs={"class": "scenario-card"})

            # Scenario title
            title = soup.new_tag("h4")
            scenario_label = "Scénario" if is_french else "Scenario"
            title.string = f"{scenario_label} {i}: {scenario.scenario_name}"
            scenario_div.append(title)

            # Modified parameters section
            params_p = soup.new_tag("p")
            params_strong = soup.new_tag("strong")
            params_label = "Paramètres Modifiés" if is_french else "Modified Parameters"
            params_strong.string = f"{params_label}:"
            params_p.append(params_strong)
            scenario_div.append(params_p)

            # Parameters list
            params_ul = soup.new_tag("ul")
            params_html = self.formatters.format_scenario_parameters(scenario.modified_parameters, is_french)
            params_soup = BeautifulSoup(params_html, "html.parser")
            for item in params_soup.find_all():
                params_ul.append(item)
            scenario_div.append(params_ul)

            # Expected outcome
            outcome_p = soup.new_tag("p")
            outcome_strong = soup.new_tag("strong")
            outcome_label = "Résultat Attendu" if is_french else "Expected Outcome"
            outcome_strong.string = f"{outcome_label}:"
            outcome_p.append(outcome_strong)
            outcome_p.append(f" {scenario.projected_outcome}")
            scenario_div.append(outcome_p)

            # Metrics div
            metrics_div = soup.new_tag("div", attrs={"class": "scenario-metrics"})

            # Cost difference metric
            cost_span = soup.new_tag("span", attrs={"class": "metric"})
            cost_label = "Différence de Coût" if is_french else "Cost Difference"
            cost_span.append(f"{cost_label}: ")

            cost_value_class = "positive" if scenario.cost_difference < 0 else "negative"
            cost_value_span = soup.new_tag("span", attrs={"class": cost_value_class})
            cost_value_span.string = f"${scenario.cost_difference:+,.2f}"
            cost_span.append(cost_value_span)
            metrics_div.append(cost_span)

            # Risk difference metric
            risk_span = soup.new_tag("span", attrs={"class": "metric"})
            risk_label = "Différence de Risque" if is_french else "Risk Difference"
            risk_span.append(f"{risk_label}: ")

            risk_value_class = "positive" if scenario.risk_difference < 0 else "negative"
            risk_value_span = soup.new_tag("span", attrs={"class": risk_value_class})
            risk_value_span.string = f"{scenario.risk_difference:+.2f}"
            risk_span.append(risk_value_span)
            metrics_div.append(risk_span)

            scenario_div.append(metrics_div)
            main_div.append(scenario_div)

        return str(main_div)

    def generate_execution_summary_content(self, result: "RebalancingResult", language: str) -> str:
        """Generate execution summary section content using BeautifulSoup."""
        is_french = language == "fr"
        execution = result.execution_summary

        # Create soup and main container
        soup = BeautifulSoup("", "html.parser")
        main_div = soup.new_tag("div", attrs={"class": "execution-summary"})

        # Execution stats section
        stats_div = soup.new_tag("div", attrs={"class": "execution-stats"})

        # Total trades stat
        trades_div = soup.new_tag("div", attrs={"class": "stat-item"})
        trades_label = soup.new_tag("span", attrs={"class": "stat-label"})
        trades_label_text = "Transactions Totales" if is_french else "Total Trades"
        trades_label.string = f"{trades_label_text}:"
        trades_value = soup.new_tag("span", attrs={"class": "stat-value"})
        trades_value.string = str(execution.total_trades_required)
        trades_div.append(trades_label)
        trades_div.append(trades_value)
        stats_div.append(trades_div)

        # Execution time stat
        time_div = soup.new_tag("div", attrs={"class": "stat-item"})
        time_label = soup.new_tag("span", attrs={"class": "stat-label"})
        time_label_text = "Temps d'Exécution Estimé" if is_french else "Estimated Execution Time"
        time_label.string = f"{time_label_text}:"
        time_value = soup.new_tag("span", attrs={"class": "stat-value"})
        time_value.string = execution.estimated_execution_time
        time_div.append(time_label)
        time_div.append(time_value)
        stats_div.append(time_div)

        # Capital required stat
        capital_div = soup.new_tag("div", attrs={"class": "stat-item"})
        capital_label = soup.new_tag("span", attrs={"class": "stat-label"})
        capital_label_text = "Capital Requis" if is_french else "Capital Required"
        capital_label.string = f"{capital_label_text}:"
        capital_value_class = "positive" if execution.capital_required < 0 else "negative"
        capital_value = soup.new_tag("span", attrs={"class": f"stat-value {capital_value_class}"})
        capital_value.string = f"${execution.capital_required:+,.2f}"
        capital_div.append(capital_label)
        capital_div.append(capital_value)
        stats_div.append(capital_div)

        main_div.append(stats_div)

        # Next steps section
        steps_div = soup.new_tag("div", attrs={"class": "next-steps"})

        # Steps title
        steps_title = soup.new_tag("h4")
        steps_title_text = "Prochaines Étapes" if is_french else "Next Steps"
        steps_title.string = steps_title_text
        steps_div.append(steps_title)

        # Steps list
        steps_ol = soup.new_tag("ol")

        step_texts = [
            ("Examiner les recommandations de trading ci-dessus", "Review the trade recommendations above"),
            ("Vérifier les coûts de transaction avec votre courtier", "Verify transaction costs with your broker"),
            ("Exécuter les transactions par ordre de priorité", "Execute trades in priority order"),
            ("Surveiller l'exécution et ajuster si nécessaire", "Monitor execution and adjust if needed"),
        ]

        for french_text, english_text in step_texts:
            step_li = soup.new_tag("li")
            step_text = french_text if is_french else english_text
            step_li.string = step_text
            steps_ol.append(step_li)

        steps_div.append(steps_ol)

        # Next review date
        review_p = soup.new_tag("p")
        review_strong = soup.new_tag("strong")
        review_label = "Prochaine Révision" if is_french else "Next Review"
        review_strong.string = f"{review_label}:"
        review_p.append(review_strong)
        review_p.append(f" {result.next_review_date.strftime('%Y-%m-%d')}")
        steps_div.append(review_p)

        main_div.append(steps_div)

        return str(main_div)
