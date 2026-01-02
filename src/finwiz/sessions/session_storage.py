"""
Session storage operations for HTML report persistence.

This module provides functionality for saving, loading, and managing
HTML report storage for financial planning sessions.
"""

from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup

from finwiz.schemas.session import FinancialPlan
from finwiz.tools.logger import get_logger
from finwiz.utils.persistence_strategies import SessionParsingError


class SessionStorage:
    """Handles storage operations for financial planning sessions."""

    def __init__(self, report_path: Path) -> None:
        """
        Initialize the session storage handler.

        Args:
            report_path: Path to the HTML report file

        """
        self.report_path = report_path
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    def load_html_content(self) -> str | None:
        """
        Load HTML content from the report file.

        Returns:
            HTML content as string, or None if file doesn't exist

        Raises:
            SessionParsingError: If the file exists but cannot be read

        """
        if not self.report_path.exists():
            self.logger.info(f"No existing session found at {self.report_path}")
            return None

        try:
            return self.report_path.read_text(encoding="utf-8")
        except Exception as e:
            self.logger.error(f"Failed to read HTML content: {str(e)}")
            raise SessionParsingError(f"Failed to read session file: {str(e)}") from e

    def save_html_content(self, html_content: str) -> None:
        """
        Save HTML content to the report file.

        Args:
            html_content: HTML content to save

        Raises:
            SessionParsingError: If saving fails

        """
        try:
            # Ensure directory exists
            self.report_path.parent.mkdir(parents=True, exist_ok=True)

            # Write to file with proper encoding
            self.report_path.write_text(html_content, encoding="utf-8")

            self.logger.info(f"Successfully saved HTML content to {self.report_path}")

        except Exception as e:
            self.logger.error(f"Failed to save HTML content: {str(e)}")
            raise SessionParsingError(f"Failed to save session: {str(e)}") from e

    def save_financial_plan(self, plan: FinancialPlan, backup: bool = True) -> None:
        """
        Save a financial plan to HTML format.

        Args:
            plan: FinancialPlan to save
            backup: Whether to create a backup of existing file

        Raises:
            SessionParsingError: If saving fails

        """
        try:
            # Create backup if requested and file exists
            if backup and self.report_path.exists():
                from finwiz.utils.persistence_strategies import BackupStrategy

                backup_strategy = BackupStrategy(self.report_path)
                backup_strategy.create_backup()

            # Update the last_updated timestamp
            plan.last_updated = datetime.now()

            # Generate HTML content
            html_content = self._generate_html_report(plan)

            # Save the HTML content
            self.save_html_content(html_content)

        except SessionParsingError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to save financial plan: {str(e)}")
            raise SessionParsingError(f"Failed to save session: {str(e)}") from e

    def _generate_html_report(self, plan: FinancialPlan) -> str:
        """
        Generate HTML report content from a FinancialPlan.

        Args:
            plan: FinancialPlan to convert to HTML

        Returns:
            HTML content as string

        """
        soup = BeautifulSoup("", "html.parser")

        # Create DOCTYPE and HTML structure
        doctype = "<!DOCTYPE html>"
        html = soup.new_tag("html")
        html["lang"] = plan.report_language

        # Create head section
        head = soup.new_tag("head")

        # Meta tags
        charset_meta = soup.new_tag("meta")
        charset_meta["charset"] = "utf-8"
        head.append(charset_meta)

        viewport_meta = soup.new_tag("meta")
        viewport_meta["name"] = "viewport"
        viewport_meta["content"] = "width=device-width,initial-scale=1"
        head.append(viewport_meta)

        plan_id_meta = soup.new_tag("meta")
        plan_id_meta["name"] = "plan-id"
        plan_id_meta["content"] = plan.plan_id
        head.append(plan_id_meta)

        created_meta = soup.new_tag("meta")
        created_meta["name"] = "created-at"
        created_meta["content"] = plan.created_at.isoformat()
        head.append(created_meta)

        updated_meta = soup.new_tag("meta")
        updated_meta["name"] = "last-updated"
        updated_meta["content"] = plan.last_updated.isoformat()
        head.append(updated_meta)

        # Title
        title = soup.new_tag("title")
        title.string = f"Plan Financier Familial — Rapport Complet ({plan.last_updated.strftime('%d %B %Y')})"
        head.append(title)

        # CSS styles
        style = soup.new_tag("style")
        style.string = """
        :root {
            --bg: #f7fafc;
            --card: #ffffff;
            --accent: #0b69ff;
            --muted: #6b7280;
            font-family: system-ui, -apple-system, Segoe UI, Roboto, "Helvetica Neue", Arial;
        }
        body {
            background: var(--bg);
            color: #0f172a;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 980px;
            margin: 0 auto;
        }
        .card {
            background: var(--card);
            border-radius: 12px;
            padding: 18px;
            margin-bottom: 14px;
            box-shadow: 0 6px 20px rgba(2, 6, 23, 0.06);
        }
        h1, h2 { margin: 0 0 8px 0; }
        .meta {
            color: var(--muted);
            font-size: 13px;
        }
        """
        head.append(style)

        # Create body section
        body = soup.new_tag("body")

        # Container div
        container = soup.new_tag("div")
        container["class"] = "container"

        # Header
        header = soup.new_tag("header")
        h1 = soup.new_tag("h1")
        h1.string = "Plan Financier Familial — Rapport Complet"
        header.append(h1)

        meta_div = soup.new_tag("div")
        meta_div["class"] = "meta"
        client_text = f"Client: {plan.client_profile.name or 'Non spécifié'}"
        if plan.client_profile.age:
            client_text += f", {plan.client_profile.age} ans"
        client_text += f" • Dernière mise à jour: {plan.last_updated.strftime('%d %B %Y')}"
        meta_div.string = client_text
        header.append(meta_div)

        container.append(header)

        # Session info section
        session_section = soup.new_tag("section")
        session_section["class"] = "card"
        session_h2 = soup.new_tag("h2")
        session_h2.string = "📊 Informations de Session"
        session_section.append(session_h2)

        # Plan ID
        plan_id_p = soup.new_tag("p")
        plan_id_strong = soup.new_tag("strong")
        plan_id_strong.string = "ID du Plan:"
        plan_id_p.append(plan_id_strong)
        plan_id_p.append(f" {plan.plan_id}")
        session_section.append(plan_id_p)

        # Created date
        created_p = soup.new_tag("p")
        created_strong = soup.new_tag("strong")
        created_strong.string = "Créé le:"
        created_p.append(created_strong)
        created_p.append(f" {plan.created_at.strftime('%d %B %Y à %H:%M')}")
        session_section.append(created_p)

        # Last updated
        updated_p = soup.new_tag("p")
        updated_strong = soup.new_tag("strong")
        updated_strong.string = "Dernière mise à jour:"
        updated_p.append(updated_strong)
        updated_p.append(f" {plan.last_updated.strftime('%d %B %Y à %H:%M')}")
        session_section.append(updated_p)

        # Analysis count
        analysis_p = soup.new_tag("p")
        analysis_strong = soup.new_tag("strong")
        analysis_strong.string = "Nombre d'analyses:"
        analysis_p.append(analysis_strong)
        analysis_p.append(f" {len(plan.analysis_history)}")
        session_section.append(analysis_p)

        container.append(session_section)

        # Add other sections
        client_section = self._generate_client_profile_section(plan.client_profile, soup)
        if client_section:
            container.append(client_section)

        portfolio_section = self._generate_portfolio_section(plan.current_portfolio_data, soup)
        if portfolio_section:
            container.append(portfolio_section)

        recommendations_section = self._generate_recommendations_section(plan.current_recommendations, soup)
        if recommendations_section:
            container.append(recommendations_section)

        # Footer
        footer = soup.new_tag("footer")
        footer_p = soup.new_tag("p")
        footer_p["style"] = "text-align: center; color: var(--muted); font-size: 12px; margin-top: 20px;"
        footer_p.string = f"Généré par FinWiz • Version {plan.version} • {plan.last_updated.strftime('%d/%m/%Y %H:%M')}"
        footer.append(footer_p)
        container.append(footer)

        body.append(container)
        html.append(head)
        html.append(body)
        soup.append(html)

        return doctype + "\n" + soup.prettify(formatter="minimal")

    def _generate_client_profile_section(self, profile, soup: BeautifulSoup):
        """Generate HTML section for client profile."""
        if not any([profile.name, profile.age, profile.investment_horizon, profile.monthly_budget]):
            return None

        section = soup.new_tag("section")
        section["class"] = "card"

        # Section header
        h2 = soup.new_tag("h2")
        h2.string = "👤 Profil Client"
        section.append(h2)

        # Name
        if profile.name:
            name_p = soup.new_tag("p")
            name_strong = soup.new_tag("strong")
            name_strong.string = "Nom:"
            name_p.append(name_strong)
            name_p.append(f" {profile.name}")
            section.append(name_p)

        # Age
        if profile.age:
            age_p = soup.new_tag("p")
            age_strong = soup.new_tag("strong")
            age_strong.string = "Âge:"
            age_p.append(age_strong)
            age_p.append(f" {profile.age} ans")
            section.append(age_p)

        # Investment horizon
        if profile.investment_horizon:
            horizon_p = soup.new_tag("p")
            horizon_strong = soup.new_tag("strong")
            horizon_strong.string = "Horizon d'investissement:"
            horizon_p.append(horizon_strong)
            horizon_p.append(f" {profile.investment_horizon}")
            section.append(horizon_p)

        # Monthly budget
        if profile.monthly_budget:
            budget_p = soup.new_tag("p")
            budget_strong = soup.new_tag("strong")
            budget_strong.string = "Budget mensuel:"
            budget_p.append(budget_strong)
            budget_p.append(f" {profile.monthly_budget}")
            section.append(budget_p)

        # Currency (only if not CHF)
        if profile.currency and profile.currency != "CHF":
            currency_p = soup.new_tag("p")
            currency_strong = soup.new_tag("strong")
            currency_strong.string = "Devise:"
            currency_p.append(currency_strong)
            currency_p.append(f" {profile.currency}")
            section.append(currency_p)

        return section

    def _generate_portfolio_section(self, portfolio_data: dict, soup: BeautifulSoup):
        """Generate HTML section for portfolio data."""
        if not portfolio_data:
            return None

        section = soup.new_tag("section")
        section["class"] = "card"

        # Section header
        h2 = soup.new_tag("h2")
        h2.string = "📦 Données de Portefeuille"
        section.append(h2)

        # Generate holdings table if available
        if "holdings" in portfolio_data and portfolio_data["holdings"]:
            h3 = soup.new_tag("h3")
            h3.string = "Positions"
            section.append(h3)

            table = soup.new_tag("table")
            table["style"] = "width: 100%; border-collapse: collapse;"

            # Table header
            thead = soup.new_tag("thead")
            header_row = soup.new_tag("tr")

            headers = ["Nom", "Ticker", "Décision", "Score"]
            for header_text in headers:
                th = soup.new_tag("th")
                th.string = header_text
                header_row.append(th)

            thead.append(header_row)
            table.append(thead)

            # Table body
            tbody = soup.new_tag("tbody")

            for holding in portfolio_data["holdings"][:10]:  # Limit to first 10
                row = soup.new_tag("tr")

                # Name cell
                name_td = soup.new_tag("td")
                name_td.string = holding.get("name", "N/A")
                row.append(name_td)

                # Ticker cell
                ticker_td = soup.new_tag("td")
                ticker_td.string = holding.get("ticker", "N/A")
                row.append(ticker_td)

                # Decision cell
                decision_td = soup.new_tag("td")
                decision_td.string = holding.get("decision", "N/A")
                row.append(decision_td)

                # Score cell
                score_td = soup.new_tag("td")
                score_td.string = holding.get("composite_score", "N/A")
                row.append(score_td)

                tbody.append(row)

            table.append(tbody)
            section.append(table)

        # Add other portfolio data as key-value pairs
        for key, value in portfolio_data.items():
            if key != "holdings" and value:
                p = soup.new_tag("p")
                strong = soup.new_tag("strong")
                strong.string = f"{key.replace('_', ' ').title()}:"
                p.append(strong)
                p.append(f" {str(value)[:100]}")
                section.append(p)

        return section

    def _generate_recommendations_section(self, recommendations: dict, soup: BeautifulSoup):
        """Generate HTML section for recommendations."""
        if not recommendations:
            return None

        section = soup.new_tag("section")
        section["class"] = "card"

        # Section header
        h2 = soup.new_tag("h2")
        h2.string = "💎 Recommandations"
        section.append(h2)

        for category, items in recommendations.items():
            if items:
                # Category header
                h3 = soup.new_tag("h3")
                h3.string = category.title()
                section.append(h3)

                # Items list
                ul = soup.new_tag("ul")
                for item in items[:5]:  # Limit to first 5
                    li = soup.new_tag("li")
                    li.string = str(item)
                    ul.append(li)
                section.append(ul)

        return section
