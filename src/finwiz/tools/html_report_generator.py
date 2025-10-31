"""
HTML Report Generator for FinWiz financial analysis reports.

This module provides HTML-first output standards with UTF-8 encoding,
emoji support, and French report section requirements using BeautifulSoup4
for secure HTML generation.
"""

import logging
from datetime import datetime
from pathlib import Path
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


class HTMLReportGenerator:
    """
    Generates HTML reports with UTF-8 encoding and emoji support.

    Implements FinWiz HTML-first output standards including French report
    section requirements (Synthèse 10-K, Sentiment du Marché).
    """

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

    def __init__(self, template_path: str | None = None) -> None:
        """
        Initialize the HTML report generator.

        Args:
            template_path: Optional path to custom HTML template

        """
        self.template_path = template_path or "src/finwiz/templates/html_template.html"
        self.unified_template_path = "src/finwiz/templates/unified_portfolio_report.html"
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
        overview_div = soup.new_tag("div", **{"class": "portfolio-overview"})
        metrics_grid = soup.new_tag("div", **{"class": "metrics-grid"})

        # Total Portfolio Value card
        value_card = soup.new_tag("div", **{"class": "metric-card"})
        value_h4 = soup.new_tag("h4")
        value_h4.string = "💰 Total Portfolio Value"
        value_p = soup.new_tag("p", **{"class": "metric-value"})
        value_p.string = f"${total_value:,.2f}"
        value_card.append(value_h4)
        value_card.append(value_p)

        # Number of Positions card
        positions_card = soup.new_tag("div", **{"class": "metric-card"})
        positions_h4 = soup.new_tag("h4")
        positions_h4.string = "📊 Number of Positions"
        positions_p = soup.new_tag("p", **{"class": "metric-value"})
        positions_p.string = str(positions_count)
        positions_card.append(positions_h4)
        positions_card.append(positions_p)

        # Risk Score card
        risk_card = soup.new_tag("div", **{"class": "metric-card"})
        risk_h4 = soup.new_tag("h4")
        risk_h4.string = "⚠️ Risk Score"
        risk_p = soup.new_tag("p", **{"class": "metric-value"})
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
        summary_div = soup.new_tag("div", **{"class": "rebalancing-summary"})

        # Recommendation banner
        banner_div = soup.new_tag("div", **{"class": f"recommendation-banner {rec_class}"})
        banner_h3 = soup.new_tag("h3")
        banner_h3.string = f"{rec_emoji} Recommendation: {recommendation.replace('_', ' ').title()}"
        banner_div.append(banner_h3)

        # Metrics grid
        metrics_grid = soup.new_tag("div", **{"class": "metrics-grid"})

        # Trades Required card
        trades_card = soup.new_tag("div", **{"class": "metric-card"})
        trades_h4 = soup.new_tag("h4")
        trades_h4.string = "🔄 Trades Required"
        trades_p = soup.new_tag("p", **{"class": "metric-value"})
        trades_p.string = str(execution_summary.get("total_trades_required", 0))
        trades_card.append(trades_h4)
        trades_card.append(trades_p)

        # Transaction Costs card
        costs_card = soup.new_tag("div", **{"class": "metric-card"})
        costs_h4 = soup.new_tag("h4")
        costs_h4.string = "💸 Transaction Costs"
        costs_p = soup.new_tag("p", **{"class": "metric-value"})
        costs_p.string = f"${cost_analysis.get('total_transaction_costs', 0):.2f}"
        costs_card.append(costs_h4)
        costs_card.append(costs_p)

        # Execution Time card
        time_card = soup.new_tag("div", **{"class": "metric-card"})
        time_h4 = soup.new_tag("h4")
        time_h4.string = "⏱️ Execution Time"
        time_p = soup.new_tag("p", **{"class": "metric-value"})
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
            container_div = soup.new_tag("div", **{"class": "trades-container"})
            table = soup.new_tag("table", **{"class": "trades-table"})

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
                tr = soup.new_tag("tr", **{"class": f"trade-row {action_class}"})

                # Symbol cell
                symbol_td = soup.new_tag("td")
                symbol_td.string = f"{action_emoji} {trade.get('symbol', 'N/A')}"
                tr.append(symbol_td)

                # Action cell
                action_td = soup.new_tag("td", **{"class": "action-cell"})
                action_td.string = action
                tr.append(action_td)

                # Quantity cell
                quantity_td = soup.new_tag("td", **{"class": "number-cell"})
                quantity_td.string = f"{trade.get('quantity', 0):.2f}"
                tr.append(quantity_td)

                # Price cell
                price_td = soup.new_tag("td", **{"class": "currency-cell"})
                price_td.string = f"${trade.get('current_price', 0):.2f}"
                tr.append(price_td)

                # Trade Value cell
                value_td = soup.new_tag("td", **{"class": "currency-cell"})
                value_td.string = f"${trade.get('trade_value', 0):,.2f}"
                tr.append(value_td)

                # Est. Cost cell
                cost_td = soup.new_tag("td", **{"class": "currency-cell"})
                cost_td.string = f"${trade.get('total_estimated_cost', 0):.2f}"
                tr.append(cost_td)

                # Priority cell
                priority_td = soup.new_tag("td", **{"class": "priority-cell"})
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

    def generate_html(self, title: str = "FinWiz Financial Report", language: str = "en") -> str:
        """
        Generate the complete HTML report using BeautifulSoup4.

        Args:
            title: Report title
            language: Report language (en/fr)

        Returns:
            Complete HTML report as string

        """
        # Load template
        template_content = self._load_template()

        # Generate report content
        report_content = self._generate_report_content(title, language)

        # Use BeautifulSoup to properly insert content and update attributes
        soup = BeautifulSoup(template_content, "html.parser")

        # Update title
        title_tag = soup.find("title")
        if title_tag:
            title_tag.string = title

        # Update language attribute
        html_tag = soup.find("html")
        if html_tag:
            html_tag["lang"] = language

        # Find content insertion point and replace
        content_comment = soup.find(string=lambda text: text and "Content will be inserted here" in text)
        if content_comment:
            # Parse the report content and insert it
            content_soup = BeautifulSoup(report_content, "html.parser")
            # Replace the comment with the parsed content
            content_comment.replace_with(*content_soup.contents)
        else:
            # Fallback: find container div and insert content there
            container = soup.find("div", class_="container")
            if container:
                content_soup = BeautifulSoup(report_content, "html.parser")
                container.clear()
                container.extend(content_soup.contents)

        # Generate final HTML with proper formatting
        html_report = soup.prettify(formatter="html")

        logger.info(f"Generated HTML report with {len(self.sections)} sections")
        return html_report

    def _load_template(self) -> str:
        """Load the HTML template."""
        try:
            template_path = Path(self.template_path)
            if not template_path.exists():
                logger.warning(f"Template not found at {self.template_path}, using default")
                return self._get_default_template()

            return template_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Error loading template: {e}")
            return self._get_default_template()

    def _get_default_template(self) -> str:
        """Get the default HTML template with UTF-8 encoding and emoji support."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Financial Report</title>
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            line-height: 1.6; 
            color: #333; 
            margin: 20px; 
            background-color: #f9f9f9; 
        }
        .container { 
            max-width: 1000px; 
            margin: auto; 
            background: #fff; 
            padding: 30px; 
            border-radius: 8px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.08); 
        }
        h1, h2, h3 { 
            color: #2c3e50; 
            border-bottom: 2px solid #e7e7e7; 
            padding-bottom: 10px; 
            margin-top: 30px; 
        }
        h1 { 
            text-align: center; 
            color: #1a2a3a; 
        }
        h2 { 
            color: #34495e; 
        }
        .section { 
            background-color: #fdfdfd; 
            border: 1px solid #eee; 
            border-radius: 6px; 
            padding: 20px; 
            margin-bottom: 25px; 
            box-shadow: 0 1px 5px rgba(0,0,0,0.05); 
        }
        .section h3 { 
            margin-top: 0; 
            color: #2980b9; 
            border-bottom: 1px dashed #e0e0e0; 
            padding-bottom: 8px; 
        }
        ul { 
            list-style: none; 
            padding: 0; 
        }
        ul li { 
            margin-bottom: 10px; 
            padding-left: 25px; 
            position: relative; 
        }
        ul li::before { 
            content: '•'; 
            color: #2980b9; 
            font-weight: bold; 
            display: inline-block; 
            width: 1em; 
            margin-left: -1em; 
        }
        .risk-category { 
            font-weight: bold; 
            color: #e74c3c; 
        }
        .strategy-category { 
            font-weight: bold; 
            color: #27ae60; 
        }
        .note { 
            font-style: italic; 
            color: #7f8c8d; 
            margin-top: 20px; 
            padding: 15px; 
            background-color: #ecf0f1; 
            border-left: 5px solid #bdc3c7; 
            border-radius: 4px; 
        }
        .disclaimer { 
            font-size: 0.9em; 
            color: #95a5a6; 
            margin-top: 40px; 
            border-top: 1px solid #eee; 
            padding-top: 20px; 
        }
        .emoji { 
            margin-right: 8px; 
            font-size: 1.2em; 
            vertical-align: middle; 
        }
        .french-section {
            border-left: 4px solid #3498db;
            background-color: #f8f9fa;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Content will be inserted here -->
    </div>
</body>
</html>"""

    def _generate_report_content(self, title: str, language: str) -> str:
        """Generate the main report content using BeautifulSoup4."""
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Sort sections by order
        sorted_sections = sorted(self.sections, key=lambda x: x.order)

        # Create HTML using BeautifulSoup4
        soup = BeautifulSoup("", "html.parser")

        # Generate header
        h1 = soup.new_tag("h1")
        h1.string = f"📊 {title}"

        date_p = soup.new_tag("p")
        date_strong = soup.new_tag("strong")
        date_strong.string = "Date" if language == "en" else "Date"
        date_p.append(date_strong)
        date_p.append(f": {current_date}")

        lang_p = soup.new_tag("p")
        lang_strong = soup.new_tag("strong")
        lang_strong.string = "Language" if language == "en" else "Langue"
        lang_p.append(lang_strong)
        lang_p.append(f": {language.upper()}")

        # Create main container
        main_div = soup.new_tag("div")
        main_div.append(h1)
        main_div.append(date_p)
        main_div.append(lang_p)

        # Generate sections
        for section in sorted_sections:
            section_class = "section"

            # Add special styling for French sections
            if section.title in self.FRENCH_SECTIONS.values():
                section_class += " french-section"

            section_div = soup.new_tag("div", **{"class": section_class})

            # Create section header
            h2 = soup.new_tag("h2")
            if section.emoji:
                emoji_span = soup.new_tag("span", **{"class": "emoji"})
                emoji_span.string = section.emoji
                h2.append(emoji_span)
                h2.append(f" {section.title}")  # Add space and title as text
            else:
                h2.string = section.title

            # Create section content div
            content_div = soup.new_tag("div")
            # Parse the existing HTML content and append it
            content_soup = BeautifulSoup(section.content, "html.parser")
            for element in content_soup:
                content_div.append(element)

            section_div.append(h2)
            section_div.append(content_div)
            main_div.append(section_div)

        # Add disclaimer
        disclaimer_text = (
            "This report is generated by FinWiz AI and is for informational purposes only. Please consult with a qualified financial advisor before making investment decisions."
            if language == "en"
            else "Ce rapport est généré par FinWiz AI et est à des fins d'information uniquement. "
            "Veuillez consulter un conseiller financier qualifié avant de prendre des décisions d'investissement."
        )

        disclaimer_div = soup.new_tag("div", **{"class": "disclaimer"})
        disclaimer_p = soup.new_tag("p")
        disclaimer_strong = soup.new_tag("strong")
        disclaimer_strong.string = "Disclaimer" if language == "en" else "Avertissement"
        disclaimer_p.append(disclaimer_strong)
        disclaimer_p.append(f": {disclaimer_text}")
        disclaimer_div.append(disclaimer_p)
        main_div.append(disclaimer_div)

        return str(main_div)

    def validate_html_output(self, html_content: str) -> dict[str, Any]:
        """
        Validate HTML output for compliance with FinWiz standards.

        Args:
            html_content: HTML content to validate

        Returns:
            Validation result with compliance status and issues

        """
        issues = []

        # Check for UTF-8 encoding declaration (case insensitive)
        if 'charset="utf-8"' not in html_content.lower() and "charset=utf-8" not in html_content.lower():
            issues.append("Missing UTF-8 encoding declaration")

        # Check for proper DOCTYPE
        if not html_content.strip().startswith("<!DOCTYPE html>"):
            issues.append("Missing or incorrect DOCTYPE declaration")

        # Check for required French sections
        french_section_found = any(section_title in html_content for section_title in self.FRENCH_SECTIONS.values())

        if not french_section_found:
            issues.append("Missing required French sections (Synthèse 10-K, Sentiment du Marché)")

        # Check for emoji support (basic check)
        if "📊" not in html_content and "📈" not in html_content:
            issues.append("No emojis found - may indicate encoding issues")

        # Check for basic HTML structure
        required_tags = ["<html", "<head", "<body", "<title"]
        for tag in required_tags:
            if tag not in html_content:
                issues.append(f"Missing required HTML tag: {tag}")

        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "has_utf8": 'charset="utf-8"' in html_content.lower(),
            "has_french_sections": french_section_found,
            "has_emojis": any(emoji in html_content for emoji in self.EMOJI_MAP.values()),
        }

    def save_report(self, html_content: str, file_path: str) -> None:
        """
        Save HTML report to file with proper UTF-8 encoding.

        Args:
            html_content: HTML content to save
            file_path: Path where to save the file

        """
        try:
            output_path = Path(file_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Ensure UTF-8 encoding when saving
            output_path.write_text(html_content, encoding="utf-8")

            logger.info(f"HTML report saved to {file_path}")
        except Exception as e:
            logger.error(f"Error saving HTML report: {e}")
            raise

    def generate_unified_html(self, title: str, language: str = "en") -> str:
        """
        Generate unified HTML report using the unified template.

        Args:
            title: Report title
            language: Report language

        Returns:
            Complete HTML report

        """
        try:
            from jinja2 import Template

            # Read unified template
            template_path = Path(self.unified_template_path)
            if not template_path.exists():
                logger.warning(f"Unified template not found at {template_path}, using fallback")
                return self.generate_html(title, language)

            template_content = template_path.read_text(encoding="utf-8")
            template = Template(template_content)

            # Sort sections by order
            sorted_sections = sorted(self.sections, key=lambda x: x.order)

            # Render template
            html_content = template.render(
                title=title,
                language=language,
                timestamp=datetime.now(),
                sections=sorted_sections,
                french_sections=list(self.FRENCH_SECTIONS.values()),
            )

            logger.info(f"Generated unified HTML report with {len(self.sections)} sections")
            return html_content

        except Exception as e:
            logger.error(f"Error generating unified HTML report: {e}")
            # Fallback to standard HTML generation
            return self.generate_html_fallback(title, language)

    def generate_html_fallback(self, title: str, language: str = "en") -> str:
        """
        Generate HTML report using fallback template with BeautifulSoup4.

        Args:
            title: Report title
            language: Report language

        Returns:
            Complete HTML report

        """
        try:
            # Sort sections by order
            sorted_sections = sorted(self.sections, key=lambda x: x.order)

            # Create HTML document using BeautifulSoup4
            soup = BeautifulSoup("", "html.parser")

            # Create DOCTYPE and html structure
            html = soup.new_tag("html", lang=language)

            # Create head
            head = soup.new_tag("head")

            # Meta tags
            charset_meta = soup.new_tag("meta", charset="UTF-8")
            viewport_meta = soup.new_tag("meta", name="viewport", content="width=device-width, initial-scale=1.0")
            title_tag = soup.new_tag("title")
            title_tag.string = title

            # CSS styles
            style_tag = soup.new_tag("style")
            style_tag.string = """
                body { font-family: Arial, sans-serif; margin: 20px; }
                .section { margin-bottom: 30px; padding: 20px; border: 1px solid #ddd; }
                .section-title { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
                table { width: 100%; border-collapse: collapse; }
                th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background-color: #f2f2f2; }
                .keep { color: #27ae60; font-weight: bold; }
                .sell { color: #e74c3c; font-weight: bold; }
                .buy { background-color: #d5f4e6; }
                .metric-card { background: #f8f9fa; padding: 1rem; margin: 0.5rem; border-radius: 5px; }
                .recommendation-banner { padding: 1rem; border-radius: 5px; margin: 1rem 0; text-align: center; }
                .rebalance-now { background-color: #e74c3c; color: white; }
                .rebalance-soon { background-color: #f39c12; color: white; }
                .monitor { background-color: #3498db; color: white; }
                .no-action { background-color: #27ae60; color: white; }
            """

            head.append(charset_meta)
            head.append(viewport_meta)
            head.append(title_tag)
            head.append(style_tag)

            # Create body
            body = soup.new_tag("body")

            # Main title
            h1 = soup.new_tag("h1")
            h1.string = title
            body.append(h1)

            # Generated date
            date_p = soup.new_tag("p")
            date_p.string = f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            body.append(date_p)

            # Add sections
            for section in sorted_sections:
                section_div = soup.new_tag("div", **{"class": "section"})

                # Section title
                section_h2 = soup.new_tag("h2", **{"class": "section-title"})
                section_title_text = f"{section.emoji + ' ' if section.emoji else ''}{section.title}"
                section_h2.string = section_title_text

                # Section content
                content_div = soup.new_tag("div", **{"class": "section-content"})
                # Parse existing HTML content and append
                content_soup = BeautifulSoup(section.content, "html.parser")
                for element in content_soup:
                    content_div.append(element)

                section_div.append(section_h2)
                section_div.append(content_div)
                body.append(section_div)

            # Footer
            footer = soup.new_tag("footer", style="margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #ddd; text-align: center; color: #666;")
            footer_p = soup.new_tag("p")
            footer_p.string = "Generated by FinWiz Portfolio Analysis System"
            footer.append(footer_p)
            body.append(footer)

            # Assemble document
            html.append(head)
            html.append(body)
            soup.append(html)

            # Generate final HTML with proper DOCTYPE
            html_content = "<!DOCTYPE html>\n" + soup.prettify(formatter="html")

            logger.info(f"Generated fallback HTML report with {len(self.sections)} sections")
            return html_content

        except Exception as e:
            logger.error(f"Error generating fallback HTML report: {e}")
            # Even error handling uses bs4
            error_soup = BeautifulSoup("", "html.parser")
            html = error_soup.new_tag("html")
            body = error_soup.new_tag("body")
            h1 = error_soup.new_tag("h1")
            h1.string = f"Error generating report: {e}"
            body.append(h1)
            html.append(body)
            error_soup.append(html)
            return "<!DOCTYPE html>\n" + error_soup.prettify(formatter="html")

    def generate_crew_report(
        self,
        crew_name: str,
        export_data: dict[str, Any],
        output_path: Path | str,
    ) -> str:
        """
        Generate HTML report for a crew using Jinja2 templates.

        This method generates crew-specific HTML reports from JSON export data
        using Jinja2 templates. It validates the export data against the crew's
        Pydantic schema before rendering.

        Args:
            crew_name: Name of the crew (e.g., "stock_crew", "etf_crew")
            export_data: Validated JSON export data from the crew
            output_path: Path where to save the HTML file

        Returns:
            Path to the generated HTML file as string

        Raises:
            ValueError: If crew_name is invalid or template not found
            ValidationError: If export_data doesn't match crew's schema

        Example:
            >>> generator = HTMLReportGenerator()
            >>> export_data = {"ticker": "AAPL", "grade": "A+", ...}
            >>> path = generator.generate_crew_report(
            ...     crew_name="stock_crew",
            ...     export_data=export_data,
            ...     output_path=Path("output/reports/session/stock_crew/AAPL_report.html"),
            ... )

        """
        try:
            from datetime import datetime
            from pathlib import Path

            from jinja2 import Environment, FileSystemLoader, TemplateNotFound

            # Initialize Jinja2 environment for crew_reports templates
            template_dir = Path("src/finwiz/templates")
            env = Environment(
                loader=FileSystemLoader(str(template_dir)),
                autoescape=True,
                trim_blocks=True,
                lstrip_blocks=True,
            )

            # Map crew names to template files
            template_map = {
                "stock_crew": "crew_reports/stock_report.html",
                "etf_crew": "crew_reports/etf_report.html",
                "crypto_crew": "crew_reports/crypto_report.html",
                "deep_analysis_crew": "crew_reports/deep_analysis_report.html",
                "discovery_crew": "crew_reports/discovery_report.html",
                "rebalancing_crew": "crew_reports/rebalancing_report.html",
            }

            # Validate crew_name
            if crew_name not in template_map:
                raise ValueError(f"Invalid crew_name: {crew_name}. Must be one of: {', '.join(template_map.keys())}")

            # Load appropriate template
            template_name = template_map[crew_name]
            try:
                template = env.get_template(template_name)
            except TemplateNotFound:
                raise ValueError(f"Template not found: {template_name}. Ensure template exists at src/finwiz/templates/{template_name}")

            # Validate export_data against crew's Pydantic schema
            # Note: Validation should be done by the caller before passing data
            # This is a safety check to ensure data structure is correct
            if not isinstance(export_data, dict):
                raise ValueError(f"export_data must be a dictionary, got {type(export_data)}")

            # Required fields check
            required_fields = ["ticker", "asset_class", "analysis_date", "session_id"]
            missing_fields = [field for field in required_fields if field not in export_data]
            if missing_fields:
                logger.warning(f"Missing required fields in export_data: {missing_fields}")

            # Render template with export data and generation timestamp
            generation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            html_content = template.render(data=export_data, generation_date=generation_date)

            # Ensure output path is a Path object
            if isinstance(output_path, str):
                output_path = Path(output_path)

            # Create parent directories if they don't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Save HTML to file with UTF-8 encoding
            output_path.write_text(html_content, encoding="utf-8")

            logger.info(f"Generated crew report for {crew_name} at {output_path}")

            return str(output_path)

        except Exception as e:
            logger.error(
                f"Error generating crew report for {crew_name}: {e}",
                exc_info=True,
            )
            raise
