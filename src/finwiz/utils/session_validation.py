"""
Session validation utilities for financial planning.

This module provides functionality for validating session integrity,
checking file corruption, and ensuring data consistency.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from finwiz.schemas.session import FinancialPlan, SessionMetadata
from finwiz.tools.logger import get_logger


class SessionValidator:
    """Handles validation operations for financial planning sessions."""

    def __init__(self, report_path: Path) -> None:
        """
        Initialize the session validator.

        Args:
            report_path: Path to the HTML report file

        """
        self.report_path = report_path
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

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

        # Validate client profile
        profile_issues = self._validate_client_profile(plan.client_profile)
        issues.extend(profile_issues)

        # Validate portfolio data
        portfolio_issues = self._validate_portfolio_data(plan.current_portfolio_data)
        issues.extend(portfolio_issues)

        # Validate recommendations
        rec_issues = self._validate_recommendations(plan.current_recommendations)
        issues.extend(rec_issues)

        is_valid = len(issues) == 0

        if is_valid:
            self.logger.info("Session integrity validation passed")
        else:
            self.logger.warning(f"Session integrity issues found: {issues}")

        return is_valid, issues

    def get_session_metadata(self) -> SessionMetadata:
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

    def validate_html_content(self, html_content: str) -> tuple[bool, list[str]]:
        """
        Validate HTML content structure and format.

        Args:
            html_content: HTML content to validate

        Returns:
            Tuple of (is_valid, list_of_issues)

        """
        issues = []

        # Basic validation of HTML content
        if not html_content.strip():
            issues.append("HTML content is empty")
            return False, issues

        # Check if content looks like HTML
        if not ("<html" in html_content.lower() or "<!doctype" in html_content.lower()):
            issues.append("Content does not appear to be HTML")

        # Check for required meta tags
        required_meta_tags = ["plan-id", "created-at", "last-updated"]
        for tag in required_meta_tags:
            if f'name="{tag}"' not in html_content and f"name='{tag}'" not in html_content:
                issues.append(f"Missing required meta tag: {tag}")

        # Check for basic HTML structure
        required_elements = ["<head>", "<body>", "<title>"]
        for element in required_elements:
            if element not in html_content.lower():
                issues.append(f"Missing required HTML element: {element}")

        is_valid = len(issues) == 0
        return is_valid, issues

    def _validate_client_profile(self, profile: Any) -> list[str]:
        """Validate client profile data."""
        issues = []

        # Check for reasonable age range
        if profile.age is not None:
            if profile.age < 18 or profile.age > 120:
                issues.append(f"Client age {profile.age} is outside reasonable range (18-120)")

        # Validate investment horizon format
        if profile.investment_horizon:
            valid_horizons = ["court terme", "moyen terme", "long terme", "short term", "medium term", "long term"]
            if not any(horizon in profile.investment_horizon.lower() for horizon in valid_horizons):
                issues.append("Investment horizon format may be invalid")

        # Validate currency format
        if profile.currency and len(profile.currency) != 3:
            issues.append(f"Currency code '{profile.currency}' should be 3 characters")

        return issues

    def _validate_portfolio_data(self, portfolio_data: dict) -> list[str]:
        """Validate portfolio data structure."""
        issues = []

        if not portfolio_data:
            return issues

        # Validate holdings structure
        if "holdings" in portfolio_data:
            holdings = portfolio_data["holdings"]
            if not isinstance(holdings, list):
                issues.append("Holdings should be a list")
            else:
                for i, holding in enumerate(holdings):
                    if not isinstance(holding, dict):
                        issues.append(f"Holding {i} should be a dictionary")
                        continue

                    # Check required fields
                    required_fields = ["name", "ticker"]
                    for field in required_fields:
                        if field not in holding or not holding[field]:
                            issues.append(f"Holding {i} missing required field: {field}")

        # Validate target allocations
        if "target_allocations" in portfolio_data:
            allocations = portfolio_data["target_allocations"]
            if not isinstance(allocations, list):
                issues.append("Target allocations should be a list")
            else:
                total_percentage = 0
                for i, allocation in enumerate(allocations):
                    if not isinstance(allocation, dict):
                        issues.append(f"Allocation {i} should be a dictionary")
                        continue

                    # Try to extract percentage for validation
                    if "target_allocation" in allocation:
                        try:
                            # Extract percentage from strings like "30%" or "30.5%"
                            import re

                            match = re.search(r"(\d+(?:\.\d+)?)", allocation["target_allocation"])
                            if match:
                                total_percentage += float(match.group(1))
                        except (ValueError, AttributeError):
                            pass

                # Check if total allocation is reasonable (allowing some tolerance)
                if total_percentage > 0 and (total_percentage < 90 or total_percentage > 110):
                    issues.append(f"Total allocation percentage ({total_percentage}%) seems unreasonable")

        return issues

    def _validate_recommendations(self, recommendations: dict) -> list[str]:
        """Validate recommendations structure."""
        issues = []

        if not recommendations:
            return issues

        # Check that recommendations contain lists
        for category, items in recommendations.items():
            if not isinstance(items, list):
                issues.append(f"Recommendations category '{category}' should contain a list")
            elif not items:
                issues.append(f"Recommendations category '{category}' is empty")
            else:
                # Check that items are strings
                for i, item in enumerate(items):
                    if not isinstance(item, str):
                        issues.append(f"Recommendation item {i} in category '{category}' should be a string")
                    elif not item.strip():
                        issues.append(f"Recommendation item {i} in category '{category}' is empty")

        return issues

    def check_file_corruption(self) -> tuple[bool, str | None]:
        """
        Check if the session file is corrupted.

        Returns:
            Tuple of (is_corrupted, corruption_reason)

        """
        metadata = self.get_session_metadata()
        return metadata.is_corrupted, metadata.corruption_reason
