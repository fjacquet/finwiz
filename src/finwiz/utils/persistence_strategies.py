"""
Persistence strategies for session backup and recovery.

This module provides backup and recovery strategies for financial planning sessions,
including backup creation, recovery from backups, and partial recovery from corrupted files.
"""

import re
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from finwiz.schemas.session import ClientProfile, FinancialPlan
from finwiz.tools.logger import get_logger


class SessionParsingError(Exception):
    """Raised when session parsing fails."""

    pass


class BackupStrategy:
    """Handles backup creation and management for session files."""

    def __init__(self, report_path: Path) -> None:
        """
        Initialize the backup strategy.

        Args:
            report_path: Path to the HTML report file

        """
        self.report_path = report_path
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    def create_backup(self) -> None:
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


class RecoveryStrategy:
    """Handles recovery from backup files and corrupted sessions."""

    def __init__(self, report_path: Path) -> None:
        """
        Initialize the recovery strategy.

        Args:
            report_path: Path to the HTML report file

        """
        self.report_path = report_path
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    def try_load_backup(self, parse_html_report_func) -> FinancialPlan | None:
        """
        Try to load from backup files.

        Args:
            parse_html_report_func: Function to parse HTML report content

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
                return parse_html_report_func(html_content)
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
