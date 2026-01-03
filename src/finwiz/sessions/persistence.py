"""
Session persistence utilities for financial planning.

This module provides functionality for saving, loading, and backing up
financial planning sessions from HTML reports.

This is a re-export layer for backward compatibility. The actual implementation
is split across:
- persistence_strategies.py: Backup and recovery strategies
- session_storage.py: HTML storage and file I/O operations
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from bs4 import BeautifulSoup, Tag

from finwiz.schemas.session import AnalysisRecord, ClientProfile, FinancialPlan
from finwiz.sessions.persistence_strategies import BackupStrategy, RecoveryStrategy, SessionParsingError
from finwiz.sessions.storage import SessionStorage
from finwiz.tools.logger import get_logger

# Re-export for backward compatibility
__all__ = ["SessionParsingError", "SessionPersistence"]


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

        # Initialize strategy components
        self.storage = SessionStorage(report_path)
        self.backup_strategy = BackupStrategy(report_path)
        self.recovery_strategy = RecoveryStrategy(report_path)

    def load_html_content(self) -> str | None:
        """
        Load HTML content from the report file.

        Returns:
            HTML content as string, or None if file doesn't exist

        Raises:
            SessionParsingError: If the file exists but cannot be read

        """
        return self.storage.load_html_content()

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
        self.storage.save_financial_plan(plan, backup=backup)

    def create_backup(self) -> None:
        """Create a backup of the current session file."""
        self.backup_strategy.create_backup()

    def try_load_backup(self) -> FinancialPlan | None:
        """
        Try to load from backup files.

        Returns:
            FinancialPlan from backup if successful, None otherwise

        """
        return self.recovery_strategy.try_load_backup(self.parse_html_report)

    def attempt_partial_recovery(self) -> FinancialPlan | None:
        """
        Attempt to recover partial data from corrupted file.

        Returns:
            FinancialPlan with recovered data if successful, None otherwise

        """
        return self.recovery_strategy.attempt_partial_recovery()

    def _extract_plan_id_from_raw(self, content: str) -> str | None:
        """Extract plan ID from raw content using regex."""
        return self.recovery_strategy._extract_plan_id_from_raw(content)

    def _extract_client_name_from_raw(self, content: str) -> str | None:
        """Extract client name from raw content using regex."""
        return self.recovery_strategy._extract_client_name_from_raw(content)

    def _extract_plan_id(self, soup: BeautifulSoup) -> str:
        """Extract or generate plan ID from HTML."""
        # Try to find existing plan ID in meta tags or comments
        meta_tag = soup.find("meta", {"name": "plan-id"})
        if meta_tag and isinstance(meta_tag, Tag) and meta_tag.get("content"):
            return cast(str, meta_tag["content"])

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

        if created_meta and isinstance(created_meta, Tag) and created_meta.get("content"):
            try:
                created_at = datetime.fromisoformat(cast(str, created_meta["content"]))
            except ValueError:
                self.logger.warning("Invalid created-at timestamp in meta tag")

        if updated_meta and isinstance(updated_meta, Tag) and updated_meta.get("content"):
            try:
                last_updated = datetime.fromisoformat(cast(str, updated_meta["content"]))
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

    def _extract_portfolio_data(self, soup: BeautifulSoup) -> dict[str, Any]:
        """Extract portfolio data from HTML tables and sections."""
        portfolio_data: dict[str, Any] = {}

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
                rows = table.find("tbody").find_all("tr") if table.find("tbody") else table.find_all("tr")[1:]

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

        # Extract allocation data by finding h2 headers
        allocation_section: Tag | None = None
        h2_elements = soup.find_all("h2")
        for h2 in h2_elements:
            if isinstance(h2, Tag) and "Allocation de Portefeuille" in h2.get_text():
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

    def _extract_recommendations(self, soup: BeautifulSoup) -> dict:
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
