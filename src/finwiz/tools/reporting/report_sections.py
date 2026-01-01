"""
Report section builders for HTML report generation.

This module provides classes for building and managing report sections
with support for portfolio overview, rebalancing summaries, and trade recommendations.
"""

import logging
from operator import attrgetter
from typing import Any

from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ReportSection(BaseModel):
    """Represents a section in the HTML report."""

    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Section content in HTML format")
    emoji: str | None = Field(None, description="Optional emoji for the section")
    order: int = Field(default=0, description="Display order of the section")


class ReportSectionBuilder:
    """Builds HTML report sections using BeautifulSoup4."""

    # Standard emoji mappings for financial content
    EMOJI_MAP = {
        "growth": "📈",
        "decline": "📉",
        "analysis": "🔍",
        "global": "🌐",
        "opportunity": "🚀",
        "risk": "⚠️",
        "financial": "💰",
        "time": "⏱️",
        "data": "📊",
        "defensive": "🛡️",
        "management": "👨‍💼",
        "innovation": "💡",
        "report": "📋",
        "summary": "📝",
        "portfolio": "💼",
        "market": "🏪",
    }

    # Required French sections
    FRENCH_SECTIONS = {"synthese_10k": "Synthèse 10-K", "sentiment_marche": "Sentiment du Marché"}

    def __init__(self) -> None:
        """Initialize the report section builder."""
        self.sections: list[ReportSection] = []

    def add_section(self, title: str, content: str, emoji_key: str | None = None, order: int = 0) -> None:
        """
        Add a section to the report.

        Args:
            title: Section title
            content: Section content in HTML format
            emoji_key: Key for emoji from EMOJI_MAP
            order: Display order (lower numbers appear first)

        """
        emoji = self.EMOJI_MAP.get(emoji_key, "") if emoji_key else ""
        section = ReportSection(title=title, content=content, emoji=emoji, order=order)
        self.sections.append(section)
        logger.debug(f"Added section: {title}")

    def add_french_section(self, section_key: str, content: str) -> None:
        """
        Add a required French section to the report.

        Args:
            section_key: Key from FRENCH_SECTIONS
            content: Section content in HTML format

        Raises:
            ValueError: If section_key is not a valid French section

        """
        if section_key not in self.FRENCH_SECTIONS:
            raise ValueError(f"Invalid French section key: {section_key}")

        title = self.FRENCH_SECTIONS[section_key]
        self.add_section(title, content, order=100)  # French sections at end

    def add_rebalancing_section(self, title: str, content: str, order: int = 0) -> None:
        """
        Add a rebalancing-specific section to the report.

        Args:
            title: Section title
            content: Section content in HTML format
            order: Display order

        """
        self.add_section(title, content, emoji_key="portfolio", order=order)

    def add_portfolio_overview_section(self, portfolio_data: dict[str, Any]) -> None:
        """
        Add portfolio overview section with key metrics.

        Args:
            portfolio_data: Portfolio analysis data

        """
        # Extract key metrics
        total_value = portfolio_data.get("total_value", 0)
        positions_count = len(portfolio_data.get("weightings", {}))
        risk_score = portfolio_data.get("risk_metrics", {}).get("concentration_risk", 0)

        # Create HTML using BeautifulSoup4
        soup = BeautifulSoup("", "html.parser")

        # Main container
        overview_div = soup.new_tag("div", attrs={"class": "portfolio-overview"})
        metrics_grid = soup.new_tag("div", attrs={"class": "metrics-grid"})

        # Total Portfolio Value card
        value_card = soup.new_tag("div", attrs={"class": "metric-card"})
        value_h4 = soup.new_tag("h4")
        value_h4.string = "💰 Total Portfolio Value"
        value_p = soup.new_tag("p", attrs={"class": "metric-value"})
        value_p.string = f"${total_value:,.2f}"
        value_card.append(value_h4)
        value_card.append(value_p)

        # Number of Positions card
        positions_card = soup.new_tag("div", attrs={"class": "metric-card"})
        positions_h4 = soup.new_tag("h4")
        positions_h4.string = "📊 Number of Positions"
        positions_p = soup.new_tag("p", attrs={"class": "metric-value"})
        positions_p.string = str(positions_count)
        positions_card.append(positions_h4)
        positions_card.append(positions_p)

        # Risk Score card
        risk_card = soup.new_tag("div", attrs={"class": "metric-card"})
        risk_h4 = soup.new_tag("h4")
        risk_h4.string = "⚠️ Risk Score"
        risk_p = soup.new_tag("p", attrs={"class": "metric-value"})
        risk_p.string = f"{risk_score:.1f}/10"
        risk_card.append(risk_h4)
        risk_card.append(risk_p)

        # Assemble the structure
        metrics_grid.append(value_card)
        metrics_grid.append(positions_card)
        metrics_grid.append(risk_card)
        overview_div.append(metrics_grid)

        # Convert to string
        content = str(overview_div)
        self.add_section("Portfolio Overview", content, emoji_key="portfolio", order=1)

    def add_rebalancing_summary_section(self, rebalancing_data: dict[str, Any]) -> None:
        """
        Add rebalancing summary section.

        Args:
            rebalancing_data: Rebalancing analysis data

        """
        execution_summary = rebalancing_data.get("execution_summary", {})
        cost_analysis = rebalancing_data.get("cost_analysis", {})
        recommendation = rebalancing_data.get("overall_recommendation", "MONITOR")

        # Determine recommendation emoji and color
        rec_emoji = "🚀" if recommendation == "REBALANCE_NOW" else "👀" if recommendation == "MONITOR" else "⏰"
        rec_class = recommendation.lower().replace("_", "-")

        # Create HTML using BeautifulSoup4
        soup = BeautifulSoup("", "html.parser")

        # Main container
        summary_div = soup.new_tag("div", attrs={"class": "rebalancing-summary"})

        # Recommendation banner
        banner_div = soup.new_tag("div", attrs={"class": f"recommendation-banner {rec_class}"})
        banner_h3 = soup.new_tag("h3")
        banner_h3.string = f"{rec_emoji} Recommendation: {recommendation.replace('_', ' ').title()}"
        banner_div.append(banner_h3)

        # Metrics grid
        metrics_grid = soup.new_tag("div", attrs={"class": "metrics-grid"})

        # Trades Required card
        trades_card = soup.new_tag("div", attrs={"class": "metric-card"})
        trades_h4 = soup.new_tag("h4")
        trades_h4.string = "🔄 Trades Required"
        trades_p = soup.new_tag("p", attrs={"class": "metric-value"})
        trades_p.string = str(execution_summary.get("total_trades_required", 0))
        trades_card.append(trades_h4)
        trades_card.append(trades_p)

        # Transaction Costs card
        costs_card = soup.new_tag("div", attrs={"class": "metric-card"})
        costs_h4 = soup.new_tag("h4")
        costs_h4.string = "💸 Transaction Costs"
        costs_p = soup.new_tag("p", attrs={"class": "metric-value"})
        costs_p.string = f"${cost_analysis.get('total_transaction_costs', 0):.2f}"
        costs_card.append(costs_h4)
        costs_card.append(costs_p)

        # Execution Time card
        time_card = soup.new_tag("div", attrs={"class": "metric-card"})
        time_h4 = soup.new_tag("h4")
        time_h4.string = "⏱️ Execution Time"
        time_p = soup.new_tag("p", attrs={"class": "metric-value"})
        time_p.string = execution_summary.get("estimated_execution_time", "N/A")
        time_card.append(time_h4)
        time_card.append(time_p)

        # Assemble the structure
        metrics_grid.append(trades_card)
        metrics_grid.append(costs_card)
        metrics_grid.append(time_card)
        summary_div.append(banner_div)
        summary_div.append(metrics_grid)

        # Convert to string
        content = str(summary_div)
        self.add_section("Rebalancing Summary", content, emoji_key="financial", order=2)

    def add_trade_recommendations_section(self, trades: list[dict[str, Any]]) -> None:
        """
        Add trade recommendations section.

        Args:
            trades: List of trade recommendations

        """
        # Create HTML using BeautifulSoup4
        soup = BeautifulSoup("", "html.parser")

        if not trades:
            # Simple paragraph for no trades
            p = soup.new_tag("p")
            p.string = "No trades required - portfolio is within tolerance bands."
            content = str(p)
        else:
            # Sort trades by priority
            sorted_trades = sorted(trades, key=lambda x: x.get("priority", 10))

            # Create trades container
            container_div = soup.new_tag("div", attrs={"class": "trades-container"})
            table = soup.new_tag("table", attrs={"class": "trades-table"})

            # Create table header
            thead = soup.new_tag("thead")
            header_row = soup.new_tag("tr")
            headers = ["Symbol", "Action", "Quantity", "Price", "Trade Value", "Est. Cost", "Priority"]

            for header_text in headers:
                th = soup.new_tag("th")
                th.string = header_text
                header_row.append(th)

            thead.append(header_row)
            table.append(thead)

            # Create table body
            tbody = soup.new_tag("tbody")

            for trade in sorted_trades:
                action = trade.get("action", "HOLD")
                action_emoji = "🟢" if action == "BUY" else "🔴" if action == "SELL" else "⚪"
                action_class = action.lower()

                # Create row
                tr = soup.new_tag("tr", attrs={"class": f"trade-row {action_class}"})

                # Symbol cell
                symbol_td = soup.new_tag("td")
                symbol_td.string = f"{action_emoji} {trade.get('symbol', 'N/A')}"
                tr.append(symbol_td)

                # Action cell
                action_td = soup.new_tag("td", attrs={"class": "action-cell"})
                action_td.string = action
                tr.append(action_td)

                # Quantity cell
                quantity_td = soup.new_tag("td", attrs={"class": "number-cell"})
                quantity_td.string = f"{trade.get('quantity', 0):.2f}"
                tr.append(quantity_td)

                # Price cell
                price_td = soup.new_tag("td", attrs={"class": "currency-cell"})
                price_td.string = f"${trade.get('current_price', 0):.2f}"
                tr.append(price_td)

                # Trade Value cell
                value_td = soup.new_tag("td", attrs={"class": "currency-cell"})
                value_td.string = f"${trade.get('trade_value', 0):,.2f}"
                tr.append(value_td)

                # Est. Cost cell
                cost_td = soup.new_tag("td", attrs={"class": "currency-cell"})
                cost_td.string = f"${trade.get('total_estimated_cost', 0):.2f}"
                tr.append(cost_td)

                # Priority cell
                priority_td = soup.new_tag("td", attrs={"class": "priority-cell"})
                priority_td.string = str(trade.get("priority", "N/A"))
                tr.append(priority_td)

                tbody.append(tr)

            table.append(tbody)
            container_div.append(table)
            content = str(container_div)

        self.add_section("Trade Recommendations", content, emoji_key="opportunity", order=3)

    def clear_sections(self) -> None:
        """Clear all sections from the report."""
        self.sections.clear()
        logger.debug("Cleared all report sections")

    def get_sorted_sections(self) -> list[ReportSection]:
        """Get sections sorted by order (FP pattern: attrgetter)."""
        return sorted(self.sections, key=attrgetter("order"))
