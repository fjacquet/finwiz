"""Report validation to catch hallucinations and data quality issues."""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ValidationIssue(BaseModel):
    """Single validation issue."""

    severity: str = Field(..., description="ERROR, WARNING, or INFO")
    category: str = Field(..., description="Category of issue")
    message: str = Field(..., description="Description of the issue")
    location: str | None = Field(None, description="Where in report the issue was found")


class ReportValidationResult(BaseModel):
    """Result of report validation."""

    is_valid: bool = Field(..., description="Whether report passes validation")
    issues: list[ValidationIssue] = Field(default_factory=list, description="List of issues found")
    warnings: list[ValidationIssue] = Field(default_factory=list, description="Non-critical warnings")
    stats: dict[str, Any] = Field(default_factory=dict, description="Validation statistics")


class ReportValidator:
    """Validates generated reports for hallucinations and data quality issues."""

    # Forbidden patterns that indicate hallucinations
    FORBIDDEN_PATTERNS = [
        "example.com",
        "test.com",
        "sample.com",
        "placeholder.com",
        "dummy.com",
        "fake.com",
        "mock.com",
    ]

    # Forbidden placeholder text
    FORBIDDEN_TEXT = [
        "TODO",
        "TBD",
        "FIXME",
        "XXX",
        "[à renseigner]",
        "[to be filled]",
        "[placeholder]",
    ]

    # Common hallucinated ticker patterns
    SUSPICIOUS_TICKERS = ["ABC", "XYZ", "LMN", "TEST", "SAMPLE", "EXAMPLE", "DEMO", "FAKE", "MOCK", "DUMMY"]

    def __init__(self) -> None:
        """Initialize validator."""
        self.current_date = datetime.now()

    def validate_html_report(
        self, html_content: str, validated_tickers: list[str], report_path: str | None = None
    ) -> ReportValidationResult:
        """
        Validate HTML report for hallucinations and data quality.

        Args:
            html_content: HTML content to validate
            validated_tickers: List of validated ticker symbols
            report_path: Optional path to report file

        Returns:
            ReportValidationResult with validation status and issues

        """
        issues = []
        warnings = []
        stats = {
            "total_checks": 0,
            "errors": 0,
            "warnings": 0,
            "tickers_found": 0,
            "urls_found": 0,
        }

        logger.info("Starting report validation...")

        # Check 1: Forbidden URL patterns
        url_issues = self._check_forbidden_urls(html_content)
        issues.extend(url_issues)
        stats["total_checks"] += 1

        # Check 2: Forbidden text patterns
        text_issues = self._check_forbidden_text(html_content)
        issues.extend(text_issues)
        stats["total_checks"] += 1

        # Check 3: Invalid tickers
        ticker_issues, ticker_count = self._check_invalid_tickers(html_content, validated_tickers)
        issues.extend(ticker_issues)
        stats["tickers_found"] = ticker_count
        stats["total_checks"] += 1

        # Check 4: Future dates
        date_issues = self._check_future_dates(html_content)
        warnings.extend(date_issues)
        stats["total_checks"] += 1

        # Check 5: Suspicious patterns
        suspicious_issues = self._check_suspicious_patterns(html_content)
        warnings.extend(suspicious_issues)
        stats["total_checks"] += 1

        # Check 6: URL validity
        url_validity_issues, url_count = self._check_url_validity(html_content)
        warnings.extend(url_validity_issues)
        stats["urls_found"] = url_count
        stats["total_checks"] += 1

        # Calculate stats
        stats["errors"] = len(issues)
        stats["warnings"] = len(warnings)

        is_valid = len(issues) == 0

        # Log results
        if is_valid:
            logger.info(f"✅ Report validation passed ({stats['warnings']} warnings)")
        else:
            logger.error(f"❌ Report validation failed with {stats['errors']} errors")
            for issue in issues:
                logger.error(f"  - {issue.category}: {issue.message}")

        return ReportValidationResult(is_valid=is_valid, issues=issues, warnings=warnings, stats=stats)

    def _check_forbidden_urls(self, html: str) -> list[ValidationIssue]:
        """Check for forbidden URL patterns."""
        issues = []

        for pattern in self.FORBIDDEN_PATTERNS:
            if pattern in html.lower():
                # Find context
                context = self._extract_context(html, pattern)
                issues.append(
                    ValidationIssue(
                        severity="ERROR",
                        category="HALLUCINATED_URL",
                        message=f"Found forbidden URL pattern: {pattern}",
                        location=context,
                    )
                )

        return issues

    def _check_forbidden_text(self, html: str) -> list[ValidationIssue]:
        """Check for forbidden placeholder text."""
        issues = []

        for text in self.FORBIDDEN_TEXT:
            if text in html:
                context = self._extract_context(html, text)
                issues.append(
                    ValidationIssue(
                        severity="ERROR", category="PLACEHOLDER_TEXT", message=f"Found placeholder text: {text}", location=context
                    )
                )

        return issues

    def _check_invalid_tickers(self, html: str, validated_tickers: list[str]) -> tuple[list[ValidationIssue], int]:
        """Check for invalid ticker symbols."""
        issues = []

        # Extract potential tickers (2-5 uppercase letters)
        ticker_pattern = r"\b([A-Z]{2,5})\b"
        found_tickers = set(re.findall(ticker_pattern, html))

        # Filter out common words that look like tickers
        common_words = {
            "HTML",
            "HTTP",
            "HTTPS",
            "JSON",
            "API",
            "URL",
            "USD",
            "EUR",
            "CHF",
            "ETF",
            "SEC",
            "VIX",
            "ROE",
            "EBIT",
            "EBITDA",
            "CEO",
            "CFO",
            "CTO",
            "USA",
            "NYSE",
            "NASDAQ",
            "PDF",
            "CSV",
            "XML",
            "SQL",
            "AWS",
            "GCP",
        }
        found_tickers = found_tickers - common_words

        # Check for suspicious tickers
        for ticker in found_tickers:
            if ticker in self.SUSPICIOUS_TICKERS:
                issues.append(
                    ValidationIssue(
                        severity="ERROR",
                        category="SUSPICIOUS_TICKER",
                        message=f"Found suspicious ticker: {ticker} (likely hallucinated)",
                        location=self._extract_context(html, ticker),
                    )
                )
            elif ticker not in validated_tickers:
                # This might be a false positive, so make it a warning
                issues.append(
                    ValidationIssue(
                        severity="WARNING",
                        category="UNVALIDATED_TICKER",
                        message=f"Found ticker not in validated list: {ticker}",
                        location=self._extract_context(html, ticker),
                    )
                )

        return issues, len(found_tickers)

    def _check_future_dates(self, html: str) -> list[ValidationIssue]:
        """Check for dates in the future."""
        issues = []

        # Extract dates in various formats
        date_patterns = [
            r"\b(\d{4})-(\d{2})-(\d{2})\b",  # YYYY-MM-DD
            r"\b(\d{2})/(\d{2})/(\d{4})\b",  # DD/MM/YYYY
            r"\b(\d{4})/(\d{2})/(\d{2})\b",  # YYYY/MM/DD
        ]

        for pattern in date_patterns:
            matches = re.finditer(pattern, html)
            for match in matches:
                try:
                    date_str = match.group(0)
                    # Try to parse date
                    if "-" in date_str:
                        parts = date_str.split("-")
                        date = datetime(int(parts[0]), int(parts[1]), int(parts[2]))
                    elif "/" in date_str:
                        parts = date_str.split("/")
                        if len(parts[0]) == 4:  # YYYY/MM/DD
                            date = datetime(int(parts[0]), int(parts[1]), int(parts[2]))
                        else:  # DD/MM/YYYY
                            date = datetime(int(parts[2]), int(parts[1]), int(parts[0]))

                    if date > self.current_date:
                        issues.append(
                            ValidationIssue(
                                severity="WARNING",
                                category="FUTURE_DATE",
                                message=f"Found future date: {date_str}",
                                location=self._extract_context(html, date_str),
                            )
                        )
                except (ValueError, IndexError):
                    # Invalid date format, skip
                    pass

        return issues

    def _check_suspicious_patterns(self, html: str) -> list[ValidationIssue]:
        """Check for suspicious patterns that might indicate hallucination."""
        issues = []

        # Check for suspiciously round numbers in financial data
        # e.g., exactly 100%, exactly 1.00, etc.
        suspicious_patterns = [
            (r"100\.0+%", "Suspiciously exact 100%"),
            (r"\b1\.0+\b", "Suspiciously exact 1.0"),
            (r"\b0\.0+\b", "Suspiciously exact 0.0"),
        ]

        for pattern, description in suspicious_patterns:
            matches = re.finditer(pattern, html)
            count = sum(1 for _ in matches)
            if count > 5:  # More than 5 occurrences is suspicious
                issues.append(
                    ValidationIssue(
                        severity="INFO",
                        category="SUSPICIOUS_PATTERN",
                        message=f"{description} appears {count} times (may indicate placeholder data)",
                        location=None,
                    )
                )

        return issues

    def _check_url_validity(self, html: str) -> tuple[list[ValidationIssue], int]:
        """Check URL validity (basic format check)."""
        issues = []

        # Extract URLs
        url_pattern = r'href=["\']([^"\']+)["\']'
        urls = re.findall(url_pattern, html)

        for url in urls:
            # Skip internal anchors
            if url.startswith("#"):
                continue

            # Check for malformed URLs
            if not url.startswith(("http://", "https://", "mailto:")):
                issues.append(
                    ValidationIssue(
                        severity="WARNING", category="MALFORMED_URL", message=f"Potentially malformed URL: {url}", location=None
                    )
                )

        return issues, len(urls)

    def _extract_context(self, html: str, pattern: str, context_length: int = 100) -> str:
        """Extract context around a pattern match."""
        try:
            index = html.lower().find(pattern.lower())
            if index == -1:
                return "Context not found"

            start = max(0, index - context_length)
            end = min(len(html), index + len(pattern) + context_length)
            context = html[start:end]

            # Clean up HTML tags for readability
            context = re.sub(r"<[^>]+>", "", context)
            context = context.strip()

            return f"...{context}..."
        except Exception:
            return "Could not extract context"


def validate_report_file(report_path: str | Path, validated_tickers: list[str]) -> ReportValidationResult:
    """
    Validate a report file.

    Args:
        report_path: Path to HTML report file
        validated_tickers: List of validated ticker symbols

    Returns:
        ReportValidationResult

    """
    report_path = Path(report_path)

    if not report_path.exists():
        return ReportValidationResult(
            is_valid=False,
            issues=[
                ValidationIssue(
                    severity="ERROR", category="FILE_NOT_FOUND", message=f"Report file not found: {report_path}", location=None
                )
            ],
            warnings=[],
            stats={"total_checks": 0, "errors": 1, "warnings": 0},
        )

    with open(report_path, encoding="utf-8") as f:
        html_content = f.read()

    validator = ReportValidator()
    return validator.validate_html_report(html_content, validated_tickers, str(report_path))
