"""
Session persistence utilities for financial planning.

This module provides functionality for saving, loading, and backing up
financial planning sessions from HTML reports.
"""

import re
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from bs4 import BeautifulSoup

from finwiz.schemas.session import AnalysisRecord, ClientProfile, FinancialPlan
from finwiz.tools.logger import get_logger


class SessionParsingError(Exception):
    """Raised when session parsing fails."""

    pass


class SessionPersistence:
    """Handles persistence operations for financial planning sessions."""

    def __init__(self, report_path: Path) -> None:
        """
        Initialize the session persistence handler.

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

    def parse_html_report(self, html_content: str) -> FinancialPlan:
        """
        Parse HTML report content into a FinancialPlan object.

        Args:
            html_content: Raw HTML content of the report

        Returns:
            Parsed FinancialPlan object

        Raises:
            SessionParsingError: If parsing fails

        """
        try:
            # Basic validation of HTML content
            if not html_content.strip():
                raise SessionParsingError("HTML content is empty")

            # Check if content looks like HTML
            if not ("<html" in html_content.lower() or "<!doctype" in html_content.lower()):
                raise SessionParsingError("Content does not appear to be HTML")

            soup = BeautifulSoup(html_content, "html.parser")

            # Extract metadata from HTML
            plan_id = self._extract_plan_id(soup)
            created_at, last_updated = self._extract_timestamps(soup)
            client_profile = self._extract_client_profile(soup)
            portfolio_data = self._extract_portfolio_data(soup)
            recommendations = self._extract_recommendations(soup)

            # Create analysis record from current content
            analysis_record = AnalysisRecord(timestamp=last_updated, analysis_type="full_analysis", portfolio_data=portfolio_data)

            financial_plan = FinancialPlan(
                plan_id=plan_id,
                created_at=created_at,
                last_updated=last_updated,
                client_profile=client_profile,
                analysis_history=[analysis_record],
                current_portfolio_data=portfolio_data,
                current_recommendations=recommendations,
            )

            return financial_plan

        except Exception as e:
            self.logger.error(f"Failed to parse HTML report: {str(e)}")
            raise SessionParsingError(f"HTML parsing failed: {str(e)}") from e

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
                self._create_backup()

            # Update the last_updated timestamp
            plan.last_updated = datetime.now()

            # Generate HTML content
            html_content = self._generate_html_report(plan)

            # Ensure directory exists
            self.report_path.parent.mkdir(parents=True, exist_ok=True)

            # Write to file with proper encoding
            self.report_path.write_text(html_content, encoding="utf-8")

            self.logger.info(f"Successfully saved financial plan to {self.report_path}")

        except Exception as e:
            self.logger.error(f"Failed to save financial plan: {str(e)}")
            raise SessionParsingError(f"Failed to save session: {str(e)}") from e

    def create_backup(self) -> None:
        """Create a backup of the current session file."""
        self._create_backup()

    def try_load_backup(self) -> FinancialPlan | None:
        """
        Try to load from backup files.

        Returns:
            FinancialPlan from backup if successful, None otherwise

        """
        backup_dir = self.report_path.parent

        # Find all backup files
        backup_files = list(backup_dir.glob(f"{self.report_path.stem}.backup_*.html"))

        if not backup_files:
            return None

        # Sort by modification time (newest first)
        backup_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        for backup_file in backup_files:
            try:
                self.logger.info(f"Trying to load backup: {backup_file}")
                html_content = backup_file.read_text(encoding="utf-8")
                return self.parse_html_report(html_content)
            except Exception as e:
                self.logger.warning(f"Backup {backup_file} is also corrupted: {str(e)}")
                continue

        return None

    def attempt_partial_recovery(self) -> FinancialPlan | None:
        """
        Attempt to recover partial data from corrupted file.

        Returns:
            FinancialPlan with recovered data if successful, None otherwise

        """
        try:
            # Read raw content
            raw_content = self.report_path.read_text(encoding="utf-8", errors="ignore")

            # Try to extract basic information even from corrupted HTML
            plan_id = self._extract_plan_id_from_raw(raw_content)
            client_name = self._extract_client_name_from_raw(raw_content)

            # Create minimal plan with recovered data
            now = datetime.now()
            plan = FinancialPlan(
                plan_id=plan_id or str(uuid4()),
                created_at=now,
                last_updated=now,
                client_profile=ClientProfile(name=client_name),
                analysis_history=[],
                current_portfolio_data={},
                current_recommendations={},
            )

            return plan

        except Exception:
            return None

    def _create_backup(self) -> None:
        """Create a backup of the current session file."""
        if not self.report_path.exists():
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.report_path.with_suffix(f".backup_{timestamp}.html")

        try:
            backup_path.write_bytes(self.report_path.read_bytes())
            self.logger.info(f"Created backup at {backup_path}")
        except Exception as e:
            self.logger.warning(f"Failed to create backup: {str(e)}")

    def _extract_plan_id(self, soup: BeautifulSoup) -> str:
        """Extract or generate plan ID from HTML."""
        # Try to find existing plan ID in meta tags or comments
        meta_tag = soup.find("meta", {"name": "plan-id"})
        if meta_tag and meta_tag.get("content"):
            return meta_tag["content"]

        # Look for plan ID in comments
        for comment in soup.find_all(string=lambda text: isinstance(text, str) and "plan-id:" in text):
            match = re.search(r"plan-id:\s*([a-f0-9-]+)", comment)
            if match:
                return match.group(1)

        # Generate new plan ID if not found
        plan_id = str(uuid4())
        self.logger.info(f"No existing plan ID found, generated new ID: {plan_id}")
        return plan_id

    def _extract_timestamps(self, soup: BeautifulSoup) -> tuple[datetime, datetime]:
        """Extract creation and update timestamps from HTML."""
        now = datetime.now()

        # Try to extract from meta tags
        created_meta = soup.find("meta", {"name": "created-at"})
        updated_meta = soup.find("meta", {"name": "last-updated"})

        created_at = now
        last_updated = now

        if created_meta and created_meta.get("content"):
            try:
                created_at = datetime.fromisoformat(created_meta["content"])
            except ValueError:
                self.logger.warning("Invalid created-at timestamp in meta tag")

        if updated_meta and updated_meta.get("content"):
            try:
                last_updated = datetime.fromisoformat(updated_meta["content"])
            except ValueError:
                self.logger.warning("Invalid last-updated timestamp in meta tag")

        # Try to extract from report date in title or header
        if created_at == now:  # If we didn't find it in meta tags
            title = soup.find("title")
            if title:
                # Look for date patterns in title
                date_match = re.search(r"(\d{1,2}\s+\w+\s+\d{4})", title.get_text())
                if date_match:
                    try:
                        # Parse French date format like "10 août 2025"
                        date_str = date_match.group(1)
                        # This is a simplified parser - in production you'd want more robust date parsing
                        self.logger.info(f"Found date in title: {date_str}")
                    except Exception:
                        pass

        return created_at, last_updated

    def _extract_client_profile(self, soup: BeautifulSoup) -> ClientProfile:
        """Extract client profile information from HTML."""
        profile = ClientProfile()

        # Look for client information in the header meta section
        meta_div = soup.find("div", class_="meta")
        if meta_div:
            meta_text = meta_div.get_text()

            # Extract age
            age_match = re.search(r"(\d+)\s+ans", meta_text)
            if age_match:
                try:
                    profile.age = int(age_match.group(1))
                except ValueError:
                    pass

            # Extract investment horizon
            horizon_match = re.search(r"Horizon:\s*([^•]+)", meta_text)
            if horizon_match:
                profile.investment_horizon = horizon_match.group(1).strip()

            # Extract monthly budget
            budget_match = re.search(r"Budget mensuel[^:]*:\s*([^•]+)", meta_text)
            if budget_match:
                profile.monthly_budget = budget_match.group(1).strip()

            # Extract risk tolerance
            risk_match = re.search(r"Tolérance au risque[^:]*:\s*([^•]+)", meta_text)
            if risk_match:
                profile.risk_tolerance = risk_match.group(1).strip()

            # Extract client name/role (remove age from name)
            client_match = re.search(r"Client:\s*([^•]+)", meta_text)
            if client_match:
                client_name = client_match.group(1).strip()
                # Remove age pattern from name (e.g., "Jean Dupont, 45 ans" -> "Jean Dupont")
                name_without_age = re.sub(r",\s*\d+\s+ans", "", client_name).strip()
                profile.name = name_without_age

        return profile

    def _extract_portfolio_data(self, soup: BeautifulSoup) -> dict[str, any]:
        """Extract portfolio data from HTML tables and sections."""
        portfolio_data = {}

        # Find portfolio data section
        portfolio_section = None
        h2_elements = soup.find_all("h2")
        for h2 in h2_elements:
            h2_text = h2.get_text()
            if "Données de Portefeuille" in h2_text or "Revue du portefeuille" in h2_text:
                portfolio_section = h2.find_parent("section")
                break

        if portfolio_section:
            # Extract holdings table data
            table = portfolio_section.find("table")
            if table:
                holdings = []
                rows = table.find("tbody").find_all("tr") if table.find("tbody") else table.find_all("tr")[1:]  # Skip header

                for row in rows:
                    cells = row.find_all(["td", "th"])
                    if len(cells) >= 4:
                        holding = {
                            "name": cells[0].get_text().strip(),
                            "ticker": cells[1].get_text().strip(),
                            "decision": cells[2].get_text().strip(),
                            "composite_score": cells[3].get_text().strip(),
                        }
                        if len(cells) > 4:
                            holding["risk_info"] = cells[4].get_text().strip()
                        holdings.append(holding)

                if holdings:
                    portfolio_data["holdings"] = holdings

            # Extract other portfolio data from paragraphs
            paragraphs = portfolio_section.find_all("p")
            for p in paragraphs:
                text = p.get_text()
                if ":" in text and "holdings" in text.lower():
                    # This is a simple way to detect portfolio data in paragraph form
                    portfolio_data["holdings_info"] = text.strip()

        # Extract allocation data
        allocation_section = soup.find("section", string=lambda text: text and "Allocation de Portefeuille" in text)
        if not allocation_section:
            h2_elements = soup.find_all("h2")
            for h2 in h2_elements:
                if "Allocation de Portefeuille" in h2.get_text():
                    allocation_section = h2.find_parent("section")
                    break

        if allocation_section:
            allocation_table = allocation_section.find("table")
            if allocation_table:
                allocations = []
                rows = allocation_table.find("tbody").find_all("tr") if allocation_table.find("tbody") else allocation_table.find_all("tr")[1:]

                for row in rows:
                    cells = row.find_all(["td", "th"])
                    if len(cells) >= 3:
                        allocation = {
                            "asset_class": cells[0].get_text().strip(),
                            "target_allocation": cells[1].get_text().strip(),
                            "monthly_amount": cells[2].get_text().strip(),
                        }
                        allocations.append(allocation)

                portfolio_data["target_allocations"] = allocations

        return portfolio_data

    def _extract_recommendations(self, soup: BeautifulSoup) -> dict[str, any]:
        """Extract investment recommendations from HTML."""
        recommendations = {}

        # Extract recommendations from the recommendations section
        rec_section = None
        h2_elements = soup.find_all("h2")
        for h2 in h2_elements:
            h2_text = h2.get_text()
            if "Recommandations" in h2_text:
                rec_section = h2.find_parent("section")
                break

        if rec_section:
            # Extract recommendations by finding all h3 + ul pairs
            h3_elements = rec_section.find_all("h3")
            for h3 in h3_elements:
                category_name = h3.get_text().strip().lower()
                next_ul = h3.find_next_sibling("ul")

                if next_ul:
                    items = []
                    for li in next_ul.find_all("li"):
                        items.append(li.get_text().strip())

                    # Map category names to standard keys
                    if "action" in category_name or "stock" in category_name:
                        recommendations["stocks"] = items
                    elif "etf" in category_name:
                        recommendations["etfs"] = items
                    elif "crypto" in category_name:
                        recommendations["crypto"] = items
                    else:
                        # Use the category name as-is for other categories
                        recommendations[category_name] = items

        return recommendations

    def _extract_plan_id_from_raw(self, content: str) -> str | None:
        """Extract plan ID from raw content using regex."""
        # Look for plan ID in meta tags or comments
        patterns = [
            r'<meta[^>]*name=["\']plan-id["\'][^>]*content=["\']([^"\']+)["\']',
            r"plan-id:\s*([a-f0-9-]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _extract_client_name_from_raw(self, content: str) -> str | None:
        """Extract client name from raw content using regex."""
        # Look for client name patterns
        patterns = [
            r"Client:\s*([^•\n<]+)",
            r"<title>[^<]*([A-Z][a-z]+\s+[A-Z][a-z]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Clean up the name
                name = re.sub(r",\s*\d+\s+ans", "", name).strip()
                if name and len(name) > 2:
                    return name

        return None

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

    def _generate_client_profile_section(self, profile: ClientProfile, soup: BeautifulSoup) -> BeautifulSoup | None:
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

    def _generate_portfolio_section(self, portfolio_data: dict[str, any], soup: BeautifulSoup) -> BeautifulSoup | None:
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

    def _generate_recommendations_section(self, recommendations: dict[str, any], soup: BeautifulSoup) -> BeautifulSoup | None:
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
