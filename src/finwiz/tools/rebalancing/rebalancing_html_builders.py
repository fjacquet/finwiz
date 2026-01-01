"""
HTML generation helpers for portfolio rebalancing reports.

This module contains HTML generation utilities extracted from
RebalancingReportGenerator to maintain file size constraints.
"""

from bs4 import BeautifulSoup

from finwiz.schemas.portfolio_rebalancing import RebalancingResult


class RebalancingHTMLBuilder:
    """Builds HTML sections for rebalancing reports."""

    @staticmethod
    def build_executive_summary(result: RebalancingResult) -> str:
        """Build executive summary HTML section."""
        soup = BeautifulSoup("", "html.parser")
        div = soup.new_tag("div", attrs={"class": "executive-summary"})

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

        return str(div)

    @staticmethod
    def build_current_portfolio(result: RebalancingResult) -> str:
        """Build current portfolio HTML section."""
        soup = BeautifulSoup("", "html.parser")

        # Weightings section
        weightings_div = soup.new_tag("div", attrs={"class": "portfolio-weightings"})
        h4 = soup.new_tag("h4")
        h4.string = "Current Allocations"
        weightings_div.append(h4)

        ul = soup.new_tag("ul")
        for symbol, weight in result.current_portfolio.weightings.items():
            deviation = result.current_portfolio.deviations_from_target.get(symbol, 0.0)
            deviation_class = "over-weight" if deviation > 0 else "under-weight" if deviation < 0 else "on-target"

            li = soup.new_tag("li", attrs={"class": deviation_class})
            symbol_span = soup.new_tag("span", attrs={"class": "symbol"})
            symbol_span.string = symbol
            li.append(symbol_span)
            li.append(": ")

            weight_span = soup.new_tag("span", attrs={"class": "weight"})
            weight_span.string = f"{weight:.1%}"
            li.append(weight_span)
            li.append(" ")

            deviation_span = soup.new_tag("span", attrs={"class": "deviation"})
            deviation_span.string = f"({deviation:+.1%})"
            li.append(deviation_span)
            ul.append(li)

        weightings_div.append(ul)

        # Portfolio metrics section
        metrics_div = soup.new_tag("div", attrs={"class": "portfolio-metrics"})
        h4 = soup.new_tag("h4")
        h4.string = "Portfolio Metrics"
        metrics_div.append(h4)

        p = soup.new_tag("p")
        strong = soup.new_tag("strong")
        strong.string = "Total Value:"
        p.append(strong)
        p.append(f" ${result.current_portfolio.total_value:,.2f}")
        metrics_div.append(p)

        p = soup.new_tag("p")
        strong = soup.new_tag("strong")
        strong.string = "Positions Needing Rebalancing:"
        p.append(strong)
        p.append(f" {len(result.current_portfolio.positions_needing_rebalancing)}")
        metrics_div.append(p)

        p = soup.new_tag("p")
        strong = soup.new_tag("strong")
        strong.string = "Risk Score:"
        p.append(strong)
        p.append(f" {result.current_risk_score:.1f}/10")
        metrics_div.append(p)

        return str(weightings_div) + str(metrics_div)

    @staticmethod
    def build_trade_recommendations(result: RebalancingResult) -> str:
        """Build trade recommendations HTML section."""
        soup = BeautifulSoup("", "html.parser")

        if not result.trade_recommendations:
            div = soup.new_tag("div", attrs={"class": "no-trades"})
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
            return str(div)

        div = soup.new_tag("div", attrs={"class": "trade-recommendations"})
        table = soup.new_tag("table", attrs={"class": "trades-table"})

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
            tr = soup.new_tag("tr", attrs={"class": f"trade-{action_class}"})

            td = soup.new_tag("td", attrs={"class": "symbol"})
            td.string = trade.symbol
            tr.append(td)

            td = soup.new_tag("td", attrs={"class": f"action {action_class}"})
            td.string = trade.action.value
            tr.append(td)

            td = soup.new_tag("td", attrs={"class": "shares"})
            td.string = f"{trade.shares:,}"
            tr.append(td)

            td = soup.new_tag("td", attrs={"class": "trade-value"})
            td.string = f"${trade.trade_value:,.2f}"
            tr.append(td)

            td = soup.new_tag("td", attrs={"class": "current-weight"})
            td.string = f"{getattr(trade, 'current_weight', 0):.1%}"
            tr.append(td)

            td = soup.new_tag("td", attrs={"class": "target-weight"})
            td.string = f"{getattr(trade, 'target_weight', 0):.1%}"
            tr.append(td)

            td = soup.new_tag("td", attrs={"class": "projected-weight"})
            td.string = f"{getattr(trade, 'projected_weight_after_trade', 0):.1%}"
            tr.append(td)

            tbody.append(tr)

        table.append(tbody)
        div.append(table)
        return str(div)

    @staticmethod
    def build_cost_analysis(result: RebalancingResult) -> str:
        """Build cost analysis HTML section."""
        soup = BeautifulSoup("", "html.parser")
        div = soup.new_tag("div", attrs={"class": "cost-analysis"})

        h4 = soup.new_tag("h4")
        h4.string = "Transaction Cost Breakdown"
        div.append(h4)

        metrics_div = soup.new_tag("div", attrs={"class": "cost-metrics"})

        # Commission Costs
        item_div = soup.new_tag("div", attrs={"class": "cost-item"})
        label_span = soup.new_tag("span", attrs={"class": "label"})
        label_span.string = "Commission Costs:"
        item_div.append(label_span)
        value_span = soup.new_tag("span", attrs={"class": "value"})
        value_span.string = f"${result.cost_analysis.commission_costs:.2f}"
        item_div.append(value_span)
        metrics_div.append(item_div)

        # Spread Costs
        item_div = soup.new_tag("div", attrs={"class": "cost-item"})
        label_span = soup.new_tag("span", attrs={"class": "label"})
        label_span.string = "Spread Costs:"
        item_div.append(label_span)
        value_span = soup.new_tag("span", attrs={"class": "value"})
        value_span.string = f"${result.cost_analysis.spread_costs:.2f}"
        item_div.append(value_span)
        metrics_div.append(item_div)

        # Total Transaction Costs
        item_div = soup.new_tag("div", attrs={"class": "cost-item total"})
        label_span = soup.new_tag("span", attrs={"class": "label"})
        label_span.string = "Total Transaction Costs:"
        item_div.append(label_span)
        value_span = soup.new_tag("span", attrs={"class": "value"})
        value_span.string = f"${result.cost_analysis.total_transaction_costs:.2f}"
        item_div.append(value_span)
        metrics_div.append(item_div)

        # Cost as % of Portfolio
        item_div = soup.new_tag("div", attrs={"class": "cost-item"})
        label_span = soup.new_tag("span", attrs={"class": "label"})
        label_span.string = "Cost as % of Portfolio:"
        item_div.append(label_span)
        value_span = soup.new_tag("span", attrs={"class": "value"})
        value_span.string = f"{result.cost_analysis.cost_as_percentage:.3f}%"
        item_div.append(value_span)
        metrics_div.append(item_div)

        # Break-even Days
        item_div = soup.new_tag("div", attrs={"class": "cost-item"})
        label_span = soup.new_tag("span", attrs={"class": "label"})
        label_span.string = "Break-even Days:"
        item_div.append(label_span)
        value_span = soup.new_tag("span", attrs={"class": "value"})
        value_span.string = str(result.cost_analysis.break_even_days or "N/A")
        item_div.append(value_span)
        metrics_div.append(item_div)

        div.append(metrics_div)
        return str(div)

    @staticmethod
    def build_risk_analysis(result: RebalancingResult) -> str:
        """Build risk analysis HTML section."""
        soup = BeautifulSoup("", "html.parser")
        risk_improvement_class = "improvement" if result.risk_improvement > 0 else "degradation" if result.risk_improvement < 0 else "neutral"

        div = soup.new_tag("div", attrs={"class": "risk-analysis"})
        h4 = soup.new_tag("h4")
        h4.string = "Risk Assessment"
        div.append(h4)

        metrics_div = soup.new_tag("div", attrs={"class": "risk-metrics"})

        # Current Risk Score
        item_div = soup.new_tag("div", attrs={"class": "risk-item"})
        label_span = soup.new_tag("span", attrs={"class": "label"})
        label_span.string = "Current Risk Score:"
        item_div.append(label_span)
        value_span = soup.new_tag("span", attrs={"class": "value risk-score"})
        value_span.string = f"{result.current_risk_score:.1f}/10"
        item_div.append(value_span)
        metrics_div.append(item_div)

        # Projected Risk Score
        item_div = soup.new_tag("div", attrs={"class": "risk-item"})
        label_span = soup.new_tag("span", attrs={"class": "label"})
        label_span.string = "Projected Risk Score:"
        item_div.append(label_span)
        value_span = soup.new_tag("span", attrs={"class": "value risk-score"})
        value_span.string = f"{result.projected_risk_score:.1f}/10"
        item_div.append(value_span)
        metrics_div.append(item_div)

        # Risk Change
        item_div = soup.new_tag("div", attrs={"class": f"risk-item {risk_improvement_class}"})
        label_span = soup.new_tag("span", attrs={"class": "label"})
        label_span.string = "Risk Change:"
        item_div.append(label_span)
        value_span = soup.new_tag("span", attrs={"class": "value"})
        value_span.string = f"{result.risk_improvement:+.1f}"
        item_div.append(value_span)
        metrics_div.append(item_div)

        div.append(metrics_div)

        # Risk Interpretation
        interp_div = soup.new_tag("div", attrs={"class": "risk-interpretation"})
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
        return str(div)

    @staticmethod
    def build_projected_portfolio(result: RebalancingResult) -> str:
        """Build projected portfolio HTML section."""
        soup = BeautifulSoup("", "html.parser")
        div = soup.new_tag("div", attrs={"class": "projected-portfolio"})

        h4 = soup.new_tag("h4")
        h4.string = "Projected Allocations After Rebalancing"
        div.append(h4)

        ul = soup.new_tag("ul", attrs={"class": "projected-weightings"})
        for symbol, weight in result.projected_portfolio.weightings.items():
            target_weight = result.current_portfolio.weightings.get(symbol, 0.0)
            deviation = weight - target_weight
            deviation_class = "on-target" if abs(deviation) < 0.01 else "close-to-target"

            li = soup.new_tag("li", attrs={"class": deviation_class})
            symbol_span = soup.new_tag("span", attrs={"class": "symbol"})
            symbol_span.string = symbol
            li.append(symbol_span)
            li.append(": ")

            weight_span = soup.new_tag("span", attrs={"class": "weight"})
            weight_span.string = f"{weight:.1%}"
            li.append(weight_span)
            li.append(" ")

            deviation_span = soup.new_tag("span", attrs={"class": "deviation"})
            deviation_span.string = f"({deviation:+.1%} from current)"
            li.append(deviation_span)
            ul.append(li)

        div.append(ul)

        # Projected metrics
        metrics_div = soup.new_tag("div", attrs={"class": "projected-metrics"})
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
        return str(div)

    @staticmethod
    def build_french_sections(result: RebalancingResult) -> str:
        """Build French summary sections."""
        soup = BeautifulSoup("", "html.parser")
        div = soup.new_tag("div", attrs={"class": "synthese-10k"})

        h3 = soup.new_tag("h3")
        h3.string = "Synthèse du Rééquilibrage de Portefeuille"
        div.append(h3)

        content_div = soup.new_tag("div", attrs={"class": "synthese-content"})

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
        translations = {
            "REBALANCE_NOW": "Rééquilibrer maintenant",
            "REBALANCE_SOON": "Rééquilibrer bientôt",
            "MONITOR": "Surveiller",
            "NO_ACTION": "Aucune action requise",
        }
        p.append(f" {translations.get(result.overall_recommendation.value, result.overall_recommendation.value)}")
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
        rec_div = soup.new_tag("div", attrs={"class": "recommandations-francais"})
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
        return str(div)
