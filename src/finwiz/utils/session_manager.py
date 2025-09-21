"""
Session management system for persistent financial planning.

This module provides the SessionManager class for loading, parsing, and managing
financial planning sessions from HTML reports.
"""

import re
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from bs4 import BeautifulSoup
from pydantic import ValidationError

from finwiz.schemas.session import AnalysisRecord, ClientProfile, FinancialPlan, SessionMetadata
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class SessionParsingError(Exception):
    """Raised when session parsing fails."""

    pass


class SessionManager:
    """
    Manages financial planning sessions with HTML report persistence.

    This class handles loading existing HTML reports, parsing their content
    into structured FinancialPlan objects, and managing session state.
    """

    def __init__(self, report_path: str = "report/finwiz_family_financial_plan.html") -> None:
        """
        Initialize the SessionManager.

        Args:
            report_path: Path to the HTML report file

        """
        self.report_path = Path(report_path)
        self.logger = get_logger(self.__class__.__name__)

    def load_existing_session(self) -> FinancialPlan | None:
        """
        Load an existing financial plan from HTML report.

        Returns:
            FinancialPlan if successfully loaded, None if file doesn't exist

        Raises:
            SessionParsingError: If the file exists but cannot be parsed

        """
        if not self.report_path.exists():
            self.logger.info(f"No existing session found at {self.report_path}")
            return None

        try:
            metadata = self._get_session_metadata()
            if metadata.is_corrupted:
                self.logger.error(f"Session file is corrupted: {metadata.corruption_reason}")
                raise SessionParsingError(f"Corrupted session file: {metadata.corruption_reason}")

            html_content = self.report_path.read_text(encoding="utf-8")
            financial_plan = self.parse_html_report(html_content)

            self.logger.info(f"Successfully loaded existing session from {self.report_path}")
            self.logger.info(f"Session created: {financial_plan.created_at}, last updated: {financial_plan.last_updated}")

            return financial_plan

        except Exception as e:
            self.logger.error(f"Failed to load existing session: {str(e)}")
            raise SessionParsingError(f"Failed to load session: {str(e)}") from e

    def create_new_session(self) -> FinancialPlan:
        """
        Create a new financial plan session.

        Returns:
            New FinancialPlan instance

        """
        now = datetime.now()
        plan_id = str(uuid4())

        financial_plan = FinancialPlan(
            plan_id=plan_id,
            created_at=now,
            last_updated=now,
            client_profile=ClientProfile(),
            analysis_history=[],
            current_portfolio_data={},
            current_recommendations={},
        )

        self.logger.info(f"Created new financial plan session with ID: {plan_id}")
        return financial_plan

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

    def validate_session_integrity(self, plan: FinancialPlan) -> tuple[bool, list[str]]:
        """
        Validate the integrity of a financial plan session.

        Args:
            plan: FinancialPlan to validate

        Returns:
            Tuple of (is_valid, list_of_issues)

        """
        issues = []

        try:
            # Validate Pydantic model
            plan.model_validate(plan.model_dump())
        except ValidationError as e:
            issues.append(f"Pydantic validation failed: {str(e)}")

        # Check required fields
        if not plan.plan_id:
            issues.append("Missing plan_id")

        if not plan.created_at:
            issues.append("Missing created_at timestamp")

        if not plan.last_updated:
            issues.append("Missing last_updated timestamp")

        # Check timestamp consistency
        if plan.created_at > plan.last_updated:
            issues.append("created_at is after last_updated")

        # Check analysis history
        if not plan.analysis_history:
            issues.append("No analysis history found")

        is_valid = len(issues) == 0

        if is_valid:
            self.logger.info("Session integrity validation passed")
        else:
            self.logger.warning(f"Session integrity issues found: {issues}")

        return is_valid, issues

    def _get_session_metadata(self) -> SessionMetadata:
        """Get metadata about the session file."""
        try:
            stat = self.report_path.stat()

            # Basic corruption check - file size
            if stat.st_size == 0:
                return SessionMetadata(
                    file_path=str(self.report_path),
                    file_size=stat.st_size,
                    last_modified=datetime.fromtimestamp(stat.st_mtime),
                    is_corrupted=True,
                    corruption_reason="File is empty",
                )

            # Try to read content to check if it's valid HTML
            try:
                with open(self.report_path, encoding="utf-8") as f:
                    content = f.read().strip().lower()
                    if not ("<!doctype html>" in content or "<html" in content):
                        return SessionMetadata(
                            file_path=str(self.report_path),
                            file_size=stat.st_size,
                            last_modified=datetime.fromtimestamp(stat.st_mtime),
                            is_corrupted=True,
                            corruption_reason="File does not appear to be valid HTML",
                        )
            except UnicodeDecodeError:
                return SessionMetadata(
                    file_path=str(self.report_path),
                    file_size=stat.st_size,
                    last_modified=datetime.fromtimestamp(stat.st_mtime),
                    is_corrupted=True,
                    corruption_reason="File encoding is not UTF-8",
                )

            return SessionMetadata(
                file_path=str(self.report_path),
                file_size=stat.st_size,
                last_modified=datetime.fromtimestamp(stat.st_mtime),
                is_corrupted=False,
            )

        except Exception as e:
            return SessionMetadata(
                file_path=str(self.report_path),
                file_size=0,
                last_modified=datetime.now(),
                is_corrupted=True,
                corruption_reason=f"Error accessing file: {str(e)}",
            )

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
                rows = (
                    allocation_table.find("tbody").find_all("tr")
                    if allocation_table.find("tbody")
                    else allocation_table.find_all("tr")[1:]
                )

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

    def recover_corrupted_session(self) -> FinancialPlan:
        """
        Attempt to recover from a corrupted session file.

        Returns:
            New FinancialPlan if recovery successful, otherwise creates new session

        Raises:
            SessionParsingError: If recovery fails completely

        """
        try:
            self.logger.warning("Attempting to recover corrupted session")

            # Try to find backup files
            backup_plan = self._try_load_backup()
            if backup_plan:
                self.logger.info("Successfully recovered from backup file")
                return backup_plan

            # Try partial recovery from corrupted file
            if self.report_path.exists():
                try:
                    partial_plan = self._attempt_partial_recovery()
                    if partial_plan:
                        self.logger.info("Successfully performed partial recovery")
                        return partial_plan
                except Exception as e:
                    self.logger.warning(f"Partial recovery failed: {str(e)}")

            # Last resort: create new session
            self.logger.warning("Creating new session as recovery fallback")
            return self.create_new_session()

        except Exception as e:
            self.logger.error(f"Session recovery failed completely: {str(e)}")
            raise SessionParsingError(f"Recovery failed: {str(e)}") from e

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

    def _try_load_backup(self) -> FinancialPlan | None:
        """Try to load from backup files."""
        self.report_path.with_suffix(".backup_*.html")
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

    def _attempt_partial_recovery(self) -> FinancialPlan | None:
        """Attempt to recover partial data from corrupted file."""
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
        # This is a simplified HTML generator - in production you'd want a proper template engine
        html_template = f"""<!doctype html>
<html lang="{plan.report_language}">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <meta name="plan-id" content="{plan.plan_id}" />
    <meta name="created-at" content="{plan.created_at.isoformat()}" />
    <meta name="last-updated" content="{plan.last_updated.isoformat()}" />
    <title>Plan Financier Familial — Rapport Complet ({plan.last_updated.strftime("%d %B %Y")})</title>
    <style>
        :root {{
            --bg: #f7fafc;
            --card: #ffffff;
            --accent: #0b69ff;
            --muted: #6b7280;
            font-family: system-ui, -apple-system, Segoe UI, Roboto, "Helvetica Neue", Arial;
        }}
        body {{
            background: var(--bg);
            color: #0f172a;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 980px;
            margin: 0 auto;
        }}
        .card {{
            background: var(--card);
            border-radius: 12px;
            padding: 18px;
            margin-bottom: 14px;
            box-shadow: 0 6px 20px rgba(2, 6, 23, 0.06);
        }}
        h1, h2 {{ margin: 0 0 8px 0; }}
        .meta {{
            color: var(--muted);
            font-size: 13px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Plan Financier Familial — Rapport Complet</h1>
            <div class="meta">
                Client: {plan.client_profile.name or "Non spécifié"}
                {f", {plan.client_profile.age} ans" if plan.client_profile.age else ""}
                • Dernière mise à jour: {plan.last_updated.strftime("%d %B %Y")}
            </div>
        </header>

        <section class="card">
            <h2>📊 Informations de Session</h2>
            <p><strong>ID du Plan:</strong> {plan.plan_id}</p>
            <p><strong>Créé le:</strong> {plan.created_at.strftime("%d %B %Y à %H:%M")}</p>
            <p><strong>Dernière mise à jour:</strong> {plan.last_updated.strftime("%d %B %Y à %H:%M")}</p>
            <p><strong>Nombre d'analyses:</strong> {len(plan.analysis_history)}</p>
        </section>

        {self._generate_client_profile_section(plan.client_profile)}
        {self._generate_portfolio_section(plan.current_portfolio_data)}
        {self._generate_recommendations_section(plan.current_recommendations)}

        <footer>
            <p style="text-align: center; color: var(--muted); font-size: 12px; margin-top: 20px;">
                Généré par FinWiz • Version {plan.version} • {plan.last_updated.strftime("%d/%m/%Y %H:%M")}
            </p>
        </footer>
    </div>
</body>
</html>"""

        return html_template

    def _generate_client_profile_section(self, profile: ClientProfile) -> str:
        """Generate HTML section for client profile."""
        if not any([profile.name, profile.age, profile.investment_horizon, profile.monthly_budget]):
            return ""

        return f"""
        <section class="card">
            <h2>👤 Profil Client</h2>
            {f"<p><strong>Nom:</strong> {profile.name}</p>" if profile.name else ""}
            {f"<p><strong>Âge:</strong> {profile.age} ans</p>" if profile.age else ""}
            {
            f"<p><strong>Horizon d'investissement:</strong> {profile.investment_horizon}</p>" if profile.investment_horizon else ""
        }
            {f"<p><strong>Budget mensuel:</strong> {profile.monthly_budget}</p>" if profile.monthly_budget else ""}
            {f"<p><strong>Devise:</strong> {profile.currency}</p>" if profile.currency != "CHF" else ""}
        </section>"""

    def _generate_portfolio_section(self, portfolio_data: dict[str, any]) -> str:
        """Generate HTML section for portfolio data."""
        if not portfolio_data:
            return ""

        html = '<section class="card"><h2>📦 Données de Portefeuille</h2>'

        # Generate holdings table if available
        if "holdings" in portfolio_data and portfolio_data["holdings"]:
            html += '<h3>Positions</h3><table style="width: 100%; border-collapse: collapse;">'
            html += "<thead><tr><th>Nom</th><th>Ticker</th><th>Décision</th><th>Score</th></tr></thead><tbody>"

            for holding in portfolio_data["holdings"][:10]:  # Limit to first 10
                html += f"""<tr>
                    <td>{holding.get("name", "N/A")}</td>
                    <td>{holding.get("ticker", "N/A")}</td>
                    <td>{holding.get("decision", "N/A")}</td>
                    <td>{holding.get("composite_score", "N/A")}</td>
                </tr>"""

            html += "</tbody></table>"

        # Add other portfolio data as key-value pairs
        for key, value in portfolio_data.items():
            if key != "holdings" and value:
                html += f"<p><strong>{key.replace('_', ' ').title()}:</strong> {str(value)[:100]}</p>"

        html += "</section>"
        return html

    def _generate_recommendations_section(self, recommendations: dict[str, any]) -> str:
        """Generate HTML section for recommendations."""
        if not recommendations:
            return ""

        html = '<section class="card"><h2>💎 Recommandations</h2>'

        for category, items in recommendations.items():
            if items:
                html += f"<h3>{category.title()}</h3><ul>"
                for item in items[:5]:  # Limit to first 5
                    html += f"<li>{item}</li>"
                html += "</ul>"

        html += "</section>"
        return html
