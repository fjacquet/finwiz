"""
Session state management for financial planning.

This module provides the main SessionManager class for managing
financial planning session state and coordinating persistence and validation.
"""

from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from finwiz.schemas.session import ClientProfile, FinancialPlan
from finwiz.tools.logger import get_logger
from finwiz.utils.session_persistence import SessionParsingError, SessionPersistence
from finwiz.utils.session_validation import SessionValidator


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

        # Initialize components
        self.persistence = SessionPersistence(self.report_path)
        self.validator = SessionValidator(self.report_path)

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
            metadata = self.validator.get_session_metadata()
            if metadata.is_corrupted:
                self.logger.error(f"Session file is corrupted: {metadata.corruption_reason}")
                raise SessionParsingError(f"Corrupted session file: {metadata.corruption_reason}")

            html_content = self.persistence.load_html_content()
            if html_content is None:
                return None

            financial_plan = self.persistence.parse_html_report(html_content)

            # Validate the loaded plan
            is_valid, issues = self.validator.validate_session_integrity(financial_plan)
            if not is_valid:
                self.logger.warning(f"Loaded session has validation issues: {issues}")

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

    def save_session(self, plan: FinancialPlan, backup: bool = True) -> None:
        """
        Save a financial plan session.

        Args:
            plan: FinancialPlan to save
            backup: Whether to create a backup of existing file

        Raises:
            SessionParsingError: If saving fails

        """
        # Validate before saving
        is_valid, issues = self.validator.validate_session_integrity(plan)
        if not is_valid:
            self.logger.warning(f"Saving session with validation issues: {issues}")

        self.persistence.save_financial_plan(plan, backup)

    def validate_session_integrity(self, plan: FinancialPlan) -> tuple[bool, list[str]]:
        """
        Validate the integrity of a financial plan session.

        Args:
            plan: FinancialPlan to validate

        Returns:
            Tuple of (is_valid, list_of_issues)

        """
        return self.validator.validate_session_integrity(plan)

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
            backup_plan = self.persistence.try_load_backup()
            if backup_plan:
                self.logger.info("Successfully recovered from backup file")
                return backup_plan

            # Try partial recovery from corrupted file
            if self.report_path.exists():
                try:
                    partial_plan = self.persistence.attempt_partial_recovery()
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

    def get_session_status(self) -> dict[str, Any]:
        """
        Get current session status information.

        Returns:
            Dictionary with session status details

        """
        status = {
            "file_exists": self.report_path.exists(),
            "file_path": str(self.report_path),
        }

        if self.report_path.exists():
            metadata = self.validator.get_session_metadata()
            status.update(
                {
                    "file_size": metadata.file_size,
                    "last_modified": metadata.last_modified,
                    "is_corrupted": metadata.is_corrupted,
                    "corruption_reason": metadata.corruption_reason,
                }
            )

            # Try to get basic session info
            try:
                html_content = self.persistence.load_html_content()
                if html_content:
                    is_valid_html, html_issues = self.validator.validate_html_content(html_content)
                    status.update(
                        {
                            "html_valid": is_valid_html,
                            "html_issues": html_issues,
                        }
                    )

                    if is_valid_html:
                        plan = self.persistence.parse_html_report(html_content)
                        status.update(
                            {
                                "plan_id": plan.plan_id,
                                "created_at": plan.created_at,
                                "last_updated": plan.last_updated,
                                "client_name": plan.client_profile.name,
                                "analysis_count": len(plan.analysis_history),
                            }
                        )
            except Exception as e:
                status["parse_error"] = str(e)

        return status

    def create_backup(self) -> None:
        """Create a backup of the current session file."""
        self.persistence.create_backup()

    def check_file_corruption(self) -> tuple[bool, str | None]:
        """
        Check if the session file is corrupted.

        Returns:
            Tuple of (is_corrupted, corruption_reason)

        """
        return self.validator.check_file_corruption()

    def update_session(self, plan: FinancialPlan, **updates: Any) -> FinancialPlan:
        """
        Update session with new data.

        Args:
            plan: Current FinancialPlan
            **updates: Fields to update

        Returns:
            Updated FinancialPlan

        """
        # Update timestamp
        plan.last_updated = datetime.now()

        # Apply updates
        for key, value in updates.items():
            if hasattr(plan, key):
                setattr(plan, key, value)
            else:
                self.logger.warning(f"Unknown field in update: {key}")

        # Validate updated plan
        is_valid, issues = self.validator.validate_session_integrity(plan)
        if not is_valid:
            self.logger.warning(f"Updated session has validation issues: {issues}")

        return plan

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
        return self.persistence.parse_html_report(html_content)

    def save_financial_plan(self, plan: FinancialPlan, backup: bool = True) -> None:
        """
        Save a financial plan to HTML format.

        Args:
            plan: FinancialPlan to save
            backup: Whether to create a backup of existing file

        Raises:
            SessionParsingError: If saving fails

        """
        self.persistence.save_financial_plan(plan, backup)

    def _get_session_metadata(self) -> Any:
        """Get session metadata."""
        return self.validator.get_session_metadata()

    def _extract_client_profile(self, soup: Any) -> ClientProfile:
        """Extract client profile from BeautifulSoup object."""
        return self.persistence._extract_client_profile(soup)

    def _extract_portfolio_data(self, soup: Any) -> dict[str, Any]:
        """Extract portfolio data from BeautifulSoup object."""
        return self.persistence._extract_portfolio_data(soup)

    def _extract_recommendations(self, soup: Any) -> dict[str, Any]:
        """Extract recommendations from BeautifulSoup object."""
        return self.persistence._extract_recommendations(soup)

    def _extract_plan_id_from_raw(self, content: str) -> str | None:
        """Extract plan ID from raw content."""
        return self.persistence._extract_plan_id_from_raw(content)

    def _extract_client_name_from_raw(self, content: str) -> str | None:
        """Extract client name from raw content."""
        return self.persistence._extract_client_name_from_raw(content)
