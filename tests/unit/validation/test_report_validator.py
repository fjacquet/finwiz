"""Tests for validation/report_validator.py module."""

from datetime import datetime, timedelta

from finwiz.validation.report_validator import (
    ReportValidationResult,
    ReportValidator,
    ValidationIssue,
    validate_report_file,
)


class TestValidationIssue:
    """Tests for ValidationIssue model."""

    def test_should_create_issue_with_all_fields(self):
        """Test creating a ValidationIssue with all fields."""
        issue = ValidationIssue(
            severity="ERROR",
            category="TEST_CATEGORY",
            message="Test message",
            location="Line 42",
        )

        assert issue.severity == "ERROR"
        assert issue.category == "TEST_CATEGORY"
        assert issue.message == "Test message"
        assert issue.location == "Line 42"

    def test_should_create_issue_without_location(self):
        """Test creating a ValidationIssue without location."""
        issue = ValidationIssue(
            severity="WARNING",
            category="TEST",
            message="No location",
        )

        assert issue.location is None


class TestReportValidationResult:
    """Tests for ReportValidationResult model."""

    def test_should_create_valid_result(self):
        """Test creating a valid result."""
        result = ReportValidationResult(
            is_valid=True,
            issues=[],
            warnings=[],
            stats={"total_checks": 5},
        )

        assert result.is_valid is True
        assert len(result.issues) == 0
        assert len(result.warnings) == 0
        assert result.stats["total_checks"] == 5

    def test_should_create_invalid_result_with_issues(self):
        """Test creating an invalid result with issues."""
        issue = ValidationIssue(
            severity="ERROR", category="TEST", message="Error"
        )
        result = ReportValidationResult(
            is_valid=False,
            issues=[issue],
            warnings=[],
            stats={},
        )

        assert result.is_valid is False
        assert len(result.issues) == 1


class TestReportValidatorInit:
    """Tests for ReportValidator initialization."""

    def test_should_initialize_with_current_date(self):
        """Test that validator initializes with current date."""
        validator = ReportValidator()

        assert validator.current_date is not None
        assert isinstance(validator.current_date, datetime)

    def test_should_have_forbidden_patterns(self):
        """Test that validator has forbidden URL patterns."""
        validator = ReportValidator()

        assert len(validator.FORBIDDEN_PATTERNS) > 0
        assert "example.com" in validator.FORBIDDEN_PATTERNS

    def test_should_have_forbidden_text(self):
        """Test that validator has forbidden text patterns."""
        validator = ReportValidator()

        assert len(validator.FORBIDDEN_TEXT) > 0
        assert "TODO" in validator.FORBIDDEN_TEXT

    def test_should_have_suspicious_tickers(self):
        """Test that validator has suspicious ticker list."""
        validator = ReportValidator()

        assert len(validator.SUSPICIOUS_TICKERS) > 0
        assert "TEST" in validator.SUSPICIOUS_TICKERS


class TestCheckForbiddenUrls:
    """Tests for _check_forbidden_urls method."""

    def test_should_detect_forbidden_url_pattern(self):
        """Test detection of forbidden URL patterns."""
        validator = ReportValidator()
        html = '<a href="https://example.com/test">Link</a>'

        issues = validator._check_forbidden_urls(html)

        assert len(issues) == 1
        assert issues[0].severity == "ERROR"
        assert issues[0].category == "HALLUCINATED_URL"
        assert "example.com" in issues[0].message

    def test_should_detect_multiple_forbidden_patterns(self):
        """Test detection of multiple forbidden patterns."""
        validator = ReportValidator()
        html = '<a href="https://example.com">X</a><a href="https://test.com">Y</a>'

        issues = validator._check_forbidden_urls(html)

        assert len(issues) == 2

    def test_should_return_empty_for_valid_html(self):
        """Test that valid HTML returns no issues."""
        validator = ReportValidator()
        html = '<a href="https://finance.yahoo.com/AAPL">Apple</a>'

        issues = validator._check_forbidden_urls(html)

        assert len(issues) == 0


class TestCheckForbiddenText:
    """Tests for _check_forbidden_text method."""

    def test_should_detect_todo_text(self):
        """Test detection of TODO placeholder."""
        validator = ReportValidator()
        html = "<p>TODO: Add analysis here</p>"

        issues = validator._check_forbidden_text(html)

        assert len(issues) == 1
        assert issues[0].category == "PLACEHOLDER_TEXT"
        assert "TODO" in issues[0].message

    def test_should_detect_tbd_text(self):
        """Test detection of TBD placeholder."""
        validator = ReportValidator()
        html = "<p>Status: TBD</p>"

        issues = validator._check_forbidden_text(html)

        assert len(issues) == 1

    def test_should_detect_fixme_text(self):
        """Test detection of FIXME placeholder."""
        validator = ReportValidator()
        html = "<p>FIXME: Fix this later</p>"

        issues = validator._check_forbidden_text(html)

        assert len(issues) == 1

    def test_should_return_empty_for_clean_html(self):
        """Test that clean HTML returns no issues."""
        validator = ReportValidator()
        html = "<p>Apple Inc. is a leading technology company.</p>"

        issues = validator._check_forbidden_text(html)

        assert len(issues) == 0


class TestCheckInvalidTickers:
    """Tests for _check_invalid_tickers method."""

    def test_should_detect_suspicious_ticker(self):
        """Test detection of suspicious tickers."""
        validator = ReportValidator()
        html = "<p>Analyzing TEST stock for potential</p>"

        issues, count = validator._check_invalid_tickers(html, ["AAPL", "MSFT"])

        assert any(i.category == "SUSPICIOUS_TICKER" for i in issues)
        assert any("TEST" in i.message for i in issues)

    def test_should_detect_unvalidated_ticker(self):
        """Test detection of unvalidated tickers."""
        validator = ReportValidator()
        html = "<p>NVDA shows strong growth</p>"

        issues, count = validator._check_invalid_tickers(html, ["AAPL", "MSFT"])

        # NVDA is not suspicious but not in validated list
        assert any(i.category == "UNVALIDATED_TICKER" for i in issues)

    def test_should_accept_validated_tickers(self):
        """Test that validated tickers don't raise issues."""
        validator = ReportValidator()
        html = "<p>AAPL and MSFT show strong fundamentals</p>"

        issues, count = validator._check_invalid_tickers(html, ["AAPL", "MSFT"])

        # Should not have issues for validated tickers
        ticker_issues = [i for i in issues if "AAPL" in i.message or "MSFT" in i.message]
        assert len(ticker_issues) == 0

    def test_should_filter_common_words(self):
        """Test that common words are filtered out."""
        validator = ReportValidator()
        html = "<p>The JSON API returns data in USD format from NYSE</p>"

        issues, count = validator._check_invalid_tickers(html, [])

        # JSON, API, USD, NYSE should be filtered
        for issue in issues:
            assert "JSON" not in issue.message
            assert "API" not in issue.message
            assert "USD" not in issue.message
            assert "NYSE" not in issue.message

    def test_should_return_ticker_count(self):
        """Test that ticker count is returned."""
        validator = ReportValidator()
        html = "<p>Analyzing AAPL MSFT GOOG</p>"

        issues, count = validator._check_invalid_tickers(html, ["AAPL", "MSFT", "GOOG"])

        assert count == 3


class TestCheckFutureDates:
    """Tests for _check_future_dates method."""

    def test_should_detect_future_date_yyyy_mm_dd(self):
        """Test detection of future date in YYYY-MM-DD format."""
        validator = ReportValidator()
        future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        html = f"<p>Report date: {future_date}</p>"

        issues = validator._check_future_dates(html)

        assert len(issues) == 1
        assert issues[0].category == "FUTURE_DATE"

    def test_should_detect_future_date_yyyy_slash(self):
        """Test detection of future date in YYYY/MM/DD format."""
        validator = ReportValidator()
        future_date = (datetime.now() + timedelta(days=30)).strftime("%Y/%m/%d")
        html = f"<p>Report date: {future_date}</p>"

        issues = validator._check_future_dates(html)

        assert len(issues) == 1

    def test_should_accept_past_dates(self):
        """Test that past dates don't raise issues."""
        validator = ReportValidator()
        past_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        html = f"<p>Report date: {past_date}</p>"

        issues = validator._check_future_dates(html)

        assert len(issues) == 0

    def test_should_handle_invalid_date_format(self):
        """Test handling of invalid date formats."""
        validator = ReportValidator()
        html = "<p>Date: 9999-99-99</p>"

        issues = validator._check_future_dates(html)

        # Should not raise exception, just skip invalid dates
        assert issues is not None


class TestCheckSuspiciousPatterns:
    """Tests for _check_suspicious_patterns method."""

    def test_should_detect_many_exact_100_percent(self):
        """Test detection of many exact 100% values."""
        validator = ReportValidator()
        html = "<p>" + "100.00% " * 10 + "</p>"

        issues = validator._check_suspicious_patterns(html)

        assert any(i.category == "SUSPICIOUS_PATTERN" for i in issues)

    def test_should_detect_many_exact_zeros(self):
        """Test detection of many exact 0.0 values."""
        validator = ReportValidator()
        html = "<p>" + "0.00 " * 10 + "</p>"

        issues = validator._check_suspicious_patterns(html)

        assert any(i.category == "SUSPICIOUS_PATTERN" for i in issues)

    def test_should_accept_few_occurrences(self):
        """Test that few occurrences don't raise issues."""
        validator = ReportValidator()
        html = "<p>100.00% ROI</p>"

        issues = validator._check_suspicious_patterns(html)

        # Less than 5 occurrences is OK
        assert len(issues) == 0


class TestCheckUrlValidity:
    """Tests for _check_url_validity method."""

    def test_should_detect_malformed_url(self):
        """Test detection of malformed URLs."""
        validator = ReportValidator()
        html = '<a href="not-a-valid-url">Link</a>'

        issues, count = validator._check_url_validity(html)

        assert len(issues) == 1
        assert issues[0].category == "MALFORMED_URL"

    def test_should_accept_valid_http_url(self):
        """Test that valid HTTP URLs pass."""
        validator = ReportValidator()
        html = '<a href="https://finance.yahoo.com">Yahoo</a>'

        issues, count = validator._check_url_validity(html)

        assert len(issues) == 0

    def test_should_accept_mailto_url(self):
        """Test that mailto URLs pass."""
        validator = ReportValidator()
        html = '<a href="mailto:test@example.com">Email</a>'

        issues, count = validator._check_url_validity(html)

        assert len(issues) == 0

    def test_should_skip_anchor_links(self):
        """Test that anchor links are skipped."""
        validator = ReportValidator()
        html = '<a href="#section1">Jump to section</a>'

        issues, count = validator._check_url_validity(html)

        assert len(issues) == 0

    def test_should_return_url_count(self):
        """Test that URL count is returned."""
        validator = ReportValidator()
        html = '<a href="https://a.com">A</a><a href="https://b.com">B</a>'

        issues, count = validator._check_url_validity(html)

        assert count == 2


class TestExtractContext:
    """Tests for _extract_context method."""

    def test_should_extract_context_around_pattern(self):
        """Test extracting context around a pattern."""
        validator = ReportValidator()
        html = "This is a test with example.com in the middle of text"

        context = validator._extract_context(html, "example.com")

        assert "example.com" in context.lower()
        assert "..." in context

    def test_should_handle_pattern_not_found(self):
        """Test handling when pattern is not found."""
        validator = ReportValidator()
        html = "This is some HTML content"

        context = validator._extract_context(html, "notfound")

        assert "not found" in context.lower()

    def test_should_handle_pattern_at_start(self):
        """Test handling pattern at start of content."""
        validator = ReportValidator()
        html = "example.com is at the start"

        context = validator._extract_context(html, "example.com", context_length=10)

        assert "example.com" in context.lower()

    def test_should_clean_html_tags(self):
        """Test that HTML tags are cleaned from context."""
        validator = ReportValidator()
        html = "<p><strong>example.com</strong></p>"

        context = validator._extract_context(html, "example.com")

        assert "<p>" not in context
        assert "<strong>" not in context


class TestValidateHtmlReport:
    """Tests for validate_html_report method."""

    def test_should_validate_clean_report(self):
        """Test validating a clean report."""
        validator = ReportValidator()
        html = """
        <html>
        <head><title>Financial Report</title></head>
        <body>
        <h1>Analysis of AAPL</h1>
        <p>Apple Inc. shows strong fundamentals with a P/E ratio of 28.5.</p>
        <a href="https://finance.yahoo.com/quote/AAPL">Yahoo Finance</a>
        </body>
        </html>
        """

        result = validator.validate_html_report(html, ["AAPL"])

        assert result.is_valid is True
        assert result.stats["errors"] == 0

    def test_should_fail_on_forbidden_url(self):
        """Test that forbidden URLs cause validation failure."""
        validator = ReportValidator()
        html = '<a href="https://example.com">Link</a>'

        result = validator.validate_html_report(html, ["AAPL"])

        assert result.is_valid is False
        assert result.stats["errors"] > 0

    def test_should_fail_on_placeholder_text(self):
        """Test that placeholder text causes validation failure."""
        validator = ReportValidator()
        html = "<p>TODO: Add analysis</p>"

        result = validator.validate_html_report(html, ["AAPL"])

        assert result.is_valid is False

    def test_should_track_all_checks(self):
        """Test that all checks are tracked in stats."""
        validator = ReportValidator()
        html = "<p>Clean content</p>"

        result = validator.validate_html_report(html, ["AAPL"])

        assert result.stats["total_checks"] == 6

    def test_should_count_tickers_and_urls(self):
        """Test that tickers and URLs are counted."""
        validator = ReportValidator()
        html = """
        <p>AAPL and MSFT analysis</p>
        <a href="https://a.com">A</a>
        <a href="https://b.com">B</a>
        """

        result = validator.validate_html_report(html, ["AAPL", "MSFT"])

        assert result.stats["tickers_found"] >= 2
        assert result.stats["urls_found"] == 2


class TestValidateReportFile:
    """Tests for validate_report_file function."""

    def test_should_return_error_for_nonexistent_file(self, tmp_path):
        """Test that nonexistent file returns error."""
        fake_path = tmp_path / "nonexistent.html"

        result = validate_report_file(fake_path, ["AAPL"])

        assert result.is_valid is False
        assert len(result.issues) == 1
        assert result.issues[0].category == "FILE_NOT_FOUND"

    def test_should_validate_existing_file(self, tmp_path):
        """Test validating an existing file."""
        report_path = tmp_path / "report.html"
        report_path.write_text("<p>AAPL analysis shows strong growth</p>")

        result = validate_report_file(report_path, ["AAPL"])

        assert result.is_valid is True

    def test_should_accept_path_string(self, tmp_path):
        """Test that string paths work."""
        report_path = tmp_path / "report.html"
        report_path.write_text("<p>Valid content</p>")

        result = validate_report_file(str(report_path), ["AAPL"])

        assert result.is_valid is True


class TestIntegration:
    """Integration tests for report validation."""

    def test_should_validate_complex_report(self):
        """Test validation of a complex report."""
        validator = ReportValidator()
        past_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        html = f"""
        <html>
        <head><title>Portfolio Analysis Report</title></head>
        <body>
        <h1>Financial Analysis - {past_date}</h1>
        <h2>Stock Analysis</h2>
        <p>AAPL: Strong buy with P/E of 28.5, revenue growth of 15.3%</p>
        <p>MSFT: Hold with stable fundamentals</p>
        <h2>ETF Allocation</h2>
        <p>VTI shows broad market exposure</p>
        <a href="https://finance.yahoo.com/quote/AAPL">Apple Quote</a>
        <a href="https://finance.yahoo.com/quote/MSFT">Microsoft Quote</a>
        </body>
        </html>
        """

        result = validator.validate_html_report(html, ["AAPL", "MSFT", "VTI"])

        assert result.is_valid is True
        assert result.stats["total_checks"] == 6

    def test_should_detect_multiple_issues(self):
        """Test detection of multiple issues."""
        validator = ReportValidator()
        future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        html = f"""
        <p>TODO: Complete analysis</p>
        <a href="https://example.com">Test link</a>
        <p>Report date: {future_date}</p>
        <p>Analyzing TEST stock</p>
        """

        result = validator.validate_html_report(html, ["AAPL"])

        assert result.is_valid is False
        # Should have multiple errors
        assert result.stats["errors"] >= 2
        # Should have warnings for future date
        assert result.stats["warnings"] >= 1
