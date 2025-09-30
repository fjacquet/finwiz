"""
HTML Formatters for Rebalancing Reports.

This module contains HTML formatting utilities and table generators
for portfolio rebalancing reports using BeautifulSoup for proper HTML generation.
"""

from typing import Any

from bs4 import BeautifulSoup

from finwiz.schemas.portfolio_rebalancing import TradeRecommendation


class RebalancingFormatters:
    """HTML formatting utilities for rebalancing reports."""

    @staticmethod
    def create_portfolio_table(
        weightings: dict[str, float],
        values: dict[str, float] | None = None,
        target_weights: dict[str, float] | None = None,
        is_french: bool = False,
        table_class: str = "portfolio-table",
    ) -> str:
        """
        Create a portfolio allocation table using BeautifulSoup.

        Args:
            weightings: Current portfolio weightings
            values: Portfolio values (optional)
            target_weights: Target weightings (optional)
            is_french: Whether to use French labels
            table_class: CSS class for the table

        Returns:
            HTML table string

        """
        if not weightings:
            soup = BeautifulSoup("", "html.parser")
            p = soup.new_tag("p")
            p.string = "Aucune donnée de portefeuille disponible." if is_french else "No portfolio data available."
            return str(p)

        # Create soup and table
        soup = BeautifulSoup("", "html.parser")
        table = soup.new_tag("table", **{"class": table_class})

        # Headers
        headers = []
        if is_french:
            headers = ["Actif", "Poids Actuel", "Valeur"]
            if target_weights:
                headers.extend(["Poids Cible", "Écart"])
        else:
            headers = ["Asset", "Current Weight", "Value"]
            if target_weights:
                headers.extend(["Target Weight", "Difference"])

        # Create thead
        thead = soup.new_tag("thead")
        tr_head = soup.new_tag("tr")
        for header in headers:
            th = soup.new_tag("th")
            th.string = header
            tr_head.append(th)
        thead.append(tr_head)
        table.append(thead)

        # Create tbody
        tbody = soup.new_tag("tbody")

        # Sort assets by weight (descending)
        sorted_assets = sorted(weightings.items(), key=lambda x: x[1], reverse=True)

        for asset, weight in sorted_assets:
            tr = soup.new_tag("tr")

            # Asset name
            td_asset = soup.new_tag("td")
            strong = soup.new_tag("strong")
            strong.string = asset
            td_asset.append(strong)
            tr.append(td_asset)

            # Current weight
            td_weight = soup.new_tag("td")
            td_weight.string = f"{weight:.1f}%"
            tr.append(td_weight)

            # Value column
            td_value = soup.new_tag("td")
            if values and asset in values:
                td_value.string = f"${values[asset]:,.0f}"
            else:
                td_value.string = "-"
            tr.append(td_value)

            # Target weight and difference columns
            if target_weights and asset in target_weights:
                target = target_weights[asset]
                difference = target - weight

                # Target weight
                td_target = soup.new_tag("td")
                td_target.string = f"{target:.1f}%"
                tr.append(td_target)

                # Difference with color coding
                td_diff = soup.new_tag("td")
                if abs(difference) < 0.5:
                    td_diff["class"] = "neutral"
                elif difference > 0:
                    td_diff["class"] = "positive"
                else:
                    td_diff["class"] = "negative"

                sign = "+" if difference > 0 else ""
                td_diff.string = f"{sign}{difference:.1f}%"
                tr.append(td_diff)

            tbody.append(tr)

        table.append(tbody)
        return str(table)

    @staticmethod
    def create_trades_table(trades: list[TradeRecommendation], is_french: bool = False, include_interactive: bool = True) -> str:
        """
        Create a trades recommendations table using BeautifulSoup.

        Args:
            trades: List of trade recommendations
            is_french: Whether to use French labels
            include_interactive: Whether to include interactive elements

        Returns:
            HTML table string

        """
        if not trades:
            soup = BeautifulSoup("", "html.parser")
            p = soup.new_tag("p")
            p.string = "Aucune recommandation de transaction." if is_french else "No trade recommendations."
            return str(p)

        # Create soup and table
        soup = BeautifulSoup("", "html.parser")
        table = soup.new_tag("table", **{"class": "trades-table"})

        # Headers
        if is_french:
            headers = ["Actif", "Action", "Quantité", "Prix Estimé", "Coût Total", "Priorité"]
        else:
            headers = ["Asset", "Action", "Quantity", "Estimated Price", "Total Cost", "Priority"]

        if include_interactive:
            headers.append("Exécuter" if is_french else "Execute")

        # Create thead
        thead = soup.new_tag("thead")
        tr_head = soup.new_tag("tr")
        for header in headers:
            th = soup.new_tag("th")
            th.string = header
            tr_head.append(th)
        thead.append(tr_head)
        table.append(thead)

        # Create tbody
        tbody = soup.new_tag("tbody")

        # Sort trades by priority (urgent first)
        sorted_trades = sorted(trades, key=lambda t: (t.priority != "urgent", t.estimated_cost), reverse=True)

        for trade in sorted_trades:
            tr = soup.new_tag("tr")

            # Add row class based on priority
            if trade.priority == "urgent":
                tr["class"] = "urgent-trade"
            elif trade.priority == "high":
                tr["class"] = "high-priority-trade"

            # Asset
            td_asset = soup.new_tag("td")
            strong = soup.new_tag("strong")
            strong.string = trade.symbol
            td_asset.append(strong)
            tr.append(td_asset)

            # Action with emoji
            td_action = soup.new_tag("td")
            action_emoji = "📈" if trade.action.lower() == "buy" else "📉"
            action_text = trade.action.upper()
            if is_french:
                action_text = "ACHETER" if trade.action.lower() == "buy" else "VENDRE"
            td_action.string = f"{action_emoji} {action_text}"
            tr.append(td_action)

            # Quantity
            td_quantity = soup.new_tag("td")
            if trade.quantity_type == "shares":
                quantity_text = f"{trade.quantity:.0f} {'actions' if is_french else 'shares'}"
            else:
                quantity_text = f"${trade.quantity:,.0f}"
            td_quantity.string = quantity_text
            tr.append(td_quantity)

            # Estimated Price
            td_price = soup.new_tag("td")
            td_price.string = f"${trade.estimated_price:.2f}"
            tr.append(td_price)

            # Total Cost
            td_cost = soup.new_tag("td")
            cost_class = "cost-positive" if trade.action.lower() == "sell" else "cost-negative"
            cost_sign = "+" if trade.action.lower() == "sell" else "-"
            td_cost["class"] = cost_class
            td_cost.string = f"{cost_sign}${abs(trade.estimated_cost):,.0f}"
            tr.append(td_cost)

            # Priority
            td_priority = soup.new_tag("td")
            priority_emoji = {"urgent": "🚨", "high": "⚠️", "medium": "📊", "low": "⏳"}.get(trade.priority, "📊")
            priority_text = trade.priority.upper()
            if is_french:
                priority_map = {"urgent": "URGENT", "high": "ÉLEVÉE", "medium": "MOYENNE", "low": "FAIBLE"}
                priority_text = priority_map.get(trade.priority, trade.priority.upper())
            td_priority.string = f"{priority_emoji} {priority_text}"
            tr.append(td_priority)

            # Interactive execute button
            if include_interactive:
                td_execute = soup.new_tag("td")
                button = soup.new_tag("button", **{"class": "execute-btn"})
                button["onclick"] = f"executeTrade('{trade.symbol}', '{trade.action}', {trade.quantity})"
                button_text = "Exécuter" if is_french else "Execute"
                button.string = f"⚡ {button_text}"
                td_execute.append(button)
                tr.append(td_execute)

            tbody.append(tr)

        table.append(tbody)
        return str(table)

    @staticmethod
    def create_before_after_table(
        current_weights: dict[str, float],
        projected_weights: dict[str, float],
        is_french: bool = False,
    ) -> str:
        """
        Create a before/after comparison table using BeautifulSoup.

        Args:
            current_weights: Current portfolio weights
            projected_weights: Projected portfolio weights after rebalancing
            is_french: Whether to use French labels

        Returns:
            HTML table string

        """
        if not current_weights or not projected_weights:
            soup = BeautifulSoup("", "html.parser")
            p = soup.new_tag("p")
            p.string = "Données insuffisantes pour la comparaison." if is_french else "Insufficient data for comparison."
            return str(p)

        # Create soup and table
        soup = BeautifulSoup("", "html.parser")
        table = soup.new_tag("table", **{"class": "before-after-table"})

        # Headers
        if is_french:
            headers = ["Actif", "Avant", "Après", "Changement"]
        else:
            headers = ["Asset", "Before", "After", "Change"]

        # Create thead
        thead = soup.new_tag("thead")
        tr_head = soup.new_tag("tr")
        for header in headers:
            th = soup.new_tag("th")
            th.string = header
            tr_head.append(th)
        thead.append(tr_head)
        table.append(thead)

        # Create tbody
        tbody = soup.new_tag("tbody")

        # Get all assets
        all_assets = set(current_weights.keys()) | set(projected_weights.keys())
        sorted_assets = sorted(all_assets)

        for asset in sorted_assets:
            current = current_weights.get(asset, 0.0)
            projected = projected_weights.get(asset, 0.0)
            change = projected - current

            tr = soup.new_tag("tr")

            # Asset name
            td_asset = soup.new_tag("td")
            strong = soup.new_tag("strong")
            strong.string = asset
            td_asset.append(strong)
            tr.append(td_asset)

            # Before
            td_before = soup.new_tag("td")
            td_before.string = f"{current:.1f}%"
            tr.append(td_before)

            # After
            td_after = soup.new_tag("td")
            td_after.string = f"{projected:.1f}%"
            tr.append(td_after)

            # Change with color coding and emoji
            td_change = soup.new_tag("td")
            if abs(change) < 0.1:
                td_change["class"] = "neutral"
                change_emoji = "⏸️"
            elif change > 0:
                td_change["class"] = "positive"
                change_emoji = "📈"
            else:
                td_change["class"] = "negative"
                change_emoji = "📉"

            sign = "+" if change > 0 else ""
            td_change.string = f"{change_emoji} {sign}{change:.1f}%"
            tr.append(td_change)

            tbody.append(tr)

        table.append(tbody)
        return str(table)

    @staticmethod
    def format_scenario_parameters(parameters: dict[str, Any], is_french: bool = False) -> str:
        """
        Format scenario parameters as HTML list items using BeautifulSoup.

        Args:
            parameters: Scenario parameters dictionary
            is_french: Whether to use French labels

        Returns:
            HTML list items string

        """
        soup = BeautifulSoup("", "html.parser")

        for key, value in parameters.items():
            if is_french:
                key_map = {
                    "risk_tolerance": "Tolérance au risque",
                    "rebalancing_threshold": "Seuil de rééquilibrage",
                    "transaction_costs": "Coûts de transaction",
                    "tax_considerations": "Considérations fiscales",
                    "time_horizon": "Horizon temporel",
                }
                display_key = key_map.get(key, key.replace("_", " ").title())
            else:
                display_key = key.replace("_", " ").title()

            # Format value based on type
            if isinstance(value, float):
                if "percentage" in key.lower() or "rate" in key.lower():
                    formatted_value = f"{value:.1f}%"
                elif "cost" in key.lower() or "fee" in key.lower():
                    formatted_value = f"${value:.2f}"
                else:
                    formatted_value = f"{value:.2f}"
            elif isinstance(value, bool):
                formatted_value = "Oui" if (value and is_french) else ("Yes" if value else ("Non" if is_french else "No"))
            else:
                formatted_value = str(value)

            # Create list item
            li = soup.new_tag("li")
            strong = soup.new_tag("strong")
            strong.string = f"{display_key}:"
            li.append(strong)
            li.append(f" {formatted_value}")
            soup.append(li)

        return str(soup)

    @staticmethod
    def get_risk_interpretation(risk_change: float, is_french: bool = False) -> str:
        """
        Get risk change interpretation.

        Args:
            risk_change: Risk change percentage
            is_french: Whether to use French text

        Returns:
            Risk interpretation string with emoji

        """
        if abs(risk_change) < 0.1:
            return " (stable)" if not is_french else " (stable)"
        elif risk_change < -0.5:
            return " (amélioration significative)" if is_french else " (significant improvement)"
        elif risk_change < 0:
            return " (amélioration)" if is_french else " (improvement)"
        elif risk_change > 0.5:
            return " (dégradation significative)" if is_french else " (significant deterioration)"
        else:
            return " (dégradation)" if is_french else " (deterioration)"
