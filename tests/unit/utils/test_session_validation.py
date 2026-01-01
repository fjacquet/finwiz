"""Tests for session_validation module."""

from datetime import datetime


class TestSessionValidator:
    """Tests for SessionValidator class."""

    def test_init(self, tmp_path):
        """Test SessionValidator initialization."""
        from finwiz.utils.session_validation import SessionValidator

        report_path = tmp_path / "report.html"
        validator = SessionValidator(report_path)

        assert validator.report_path == report_path
        assert validator.logger is not None

    def test_validate_session_integrity_valid(self, tmp_path, mocker):
        """Test validating a valid session."""
        from finwiz.utils.session_validation import SessionValidator

        # Mock FinancialPlan
        mock_plan = mocker.MagicMock()
        mock_plan.plan_id = "test-plan-123"
        mock_plan.created_at = datetime(2025, 1, 1, 10, 0, 0)
        mock_plan.last_updated = datetime(2025, 1, 2, 10, 0, 0)
        mock_plan.analysis_history = [{"date": "2025-01-01"}]
        mock_plan.model_dump.return_value = {"plan_id": "test"}
        mock_plan.model_validate.return_value = mock_plan

        # Mock client profile
        mock_plan.client_profile = mocker.MagicMock()
        mock_plan.client_profile.age = 35
        mock_plan.client_profile.investment_horizon = "long term"
        mock_plan.client_profile.currency = "USD"

        # Mock portfolio data
        mock_plan.current_portfolio_data = {}

        # Mock recommendations
        mock_plan.current_recommendations = {}

        report_path = tmp_path / "report.html"
        validator = SessionValidator(report_path)

        is_valid, issues = validator.validate_session_integrity(mock_plan)

        assert is_valid is True
        assert len(issues) == 0

    def test_validate_session_integrity_missing_plan_id(self, tmp_path, mocker):
        """Test validating session with missing plan_id."""
        from finwiz.utils.session_validation import SessionValidator

        mock_plan = mocker.MagicMock()
        mock_plan.plan_id = None
        mock_plan.created_at = datetime(2025, 1, 1)
        mock_plan.last_updated = datetime(2025, 1, 2)
        mock_plan.analysis_history = [{}]
        mock_plan.model_dump.return_value = {}
        mock_plan.model_validate.return_value = mock_plan
        mock_plan.client_profile = mocker.MagicMock()
        mock_plan.client_profile.age = None
        mock_plan.client_profile.investment_horizon = None
        mock_plan.client_profile.currency = None
        mock_plan.current_portfolio_data = {}
        mock_plan.current_recommendations = {}

        validator = SessionValidator(tmp_path / "report.html")
        is_valid, issues = validator.validate_session_integrity(mock_plan)

        assert is_valid is False
        assert any("plan_id" in issue.lower() for issue in issues)

    def test_validate_session_integrity_timestamp_order(self, tmp_path, mocker):
        """Test validating session with invalid timestamp order."""
        from finwiz.utils.session_validation import SessionValidator

        mock_plan = mocker.MagicMock()
        mock_plan.plan_id = "test"
        mock_plan.created_at = datetime(2025, 1, 10)  # After last_updated
        mock_plan.last_updated = datetime(2025, 1, 1)
        mock_plan.analysis_history = [{}]
        mock_plan.model_dump.return_value = {}
        mock_plan.model_validate.return_value = mock_plan
        mock_plan.client_profile = mocker.MagicMock()
        mock_plan.client_profile.age = None
        mock_plan.client_profile.investment_horizon = None
        mock_plan.client_profile.currency = None
        mock_plan.current_portfolio_data = {}
        mock_plan.current_recommendations = {}

        validator = SessionValidator(tmp_path / "report.html")
        is_valid, issues = validator.validate_session_integrity(mock_plan)

        assert is_valid is False
        assert any("after" in issue.lower() for issue in issues)

    def test_validate_session_integrity_no_history(self, tmp_path, mocker):
        """Test validating session with no analysis history."""
        from finwiz.utils.session_validation import SessionValidator

        mock_plan = mocker.MagicMock()
        mock_plan.plan_id = "test"
        mock_plan.created_at = datetime(2025, 1, 1)
        mock_plan.last_updated = datetime(2025, 1, 2)
        mock_plan.analysis_history = []  # Empty history
        mock_plan.model_dump.return_value = {}
        mock_plan.model_validate.return_value = mock_plan
        mock_plan.client_profile = mocker.MagicMock()
        mock_plan.client_profile.age = None
        mock_plan.client_profile.investment_horizon = None
        mock_plan.client_profile.currency = None
        mock_plan.current_portfolio_data = {}
        mock_plan.current_recommendations = {}

        validator = SessionValidator(tmp_path / "report.html")
        is_valid, issues = validator.validate_session_integrity(mock_plan)

        assert is_valid is False
        assert any("history" in issue.lower() for issue in issues)

    def test_validate_session_integrity_pydantic_error(self, tmp_path, mocker):
        """Test validating session with Pydantic validation error."""
        from pydantic import ValidationError

        from finwiz.utils.session_validation import SessionValidator

        mock_plan = mocker.MagicMock()
        mock_plan.plan_id = "test"
        mock_plan.created_at = datetime(2025, 1, 1)
        mock_plan.last_updated = datetime(2025, 1, 2)
        mock_plan.analysis_history = [{}]
        mock_plan.model_dump.return_value = {}
        mock_plan.model_validate.side_effect = ValidationError.from_exception_data(
            "TestModel", []
        )
        mock_plan.client_profile = mocker.MagicMock()
        mock_plan.client_profile.age = None
        mock_plan.client_profile.investment_horizon = None
        mock_plan.client_profile.currency = None
        mock_plan.current_portfolio_data = {}
        mock_plan.current_recommendations = {}

        validator = SessionValidator(tmp_path / "report.html")
        is_valid, issues = validator.validate_session_integrity(mock_plan)

        assert is_valid is False
        assert any("pydantic" in issue.lower() for issue in issues)

    def test_get_session_metadata_valid_file(self, tmp_path):
        """Test getting metadata for valid HTML file."""
        from finwiz.utils.session_validation import SessionValidator

        report_path = tmp_path / "report.html"
        report_path.write_text("<!DOCTYPE html><html><head></head><body></body></html>")

        validator = SessionValidator(report_path)
        metadata = validator.get_session_metadata()

        assert metadata.file_path == str(report_path)
        assert metadata.file_size > 0
        assert metadata.is_corrupted is False
        assert metadata.corruption_reason is None

    def test_get_session_metadata_empty_file(self, tmp_path):
        """Test getting metadata for empty file."""
        from finwiz.utils.session_validation import SessionValidator

        report_path = tmp_path / "report.html"
        report_path.write_text("")

        validator = SessionValidator(report_path)
        metadata = validator.get_session_metadata()

        assert metadata.is_corrupted is True
        assert "empty" in metadata.corruption_reason.lower()

    def test_get_session_metadata_not_html(self, tmp_path):
        """Test getting metadata for non-HTML file."""
        from finwiz.utils.session_validation import SessionValidator

        report_path = tmp_path / "report.html"
        report_path.write_text("This is plain text, not HTML")

        validator = SessionValidator(report_path)
        metadata = validator.get_session_metadata()

        assert metadata.is_corrupted is True
        assert "html" in metadata.corruption_reason.lower()

    def test_get_session_metadata_nonexistent_file(self, tmp_path):
        """Test getting metadata for nonexistent file."""
        from finwiz.utils.session_validation import SessionValidator

        report_path = tmp_path / "nonexistent.html"

        validator = SessionValidator(report_path)
        metadata = validator.get_session_metadata()

        assert metadata.is_corrupted is True
        assert "error" in metadata.corruption_reason.lower()

    def test_get_session_metadata_unicode_error(self, tmp_path):
        """Test getting metadata for file with encoding issues."""
        from finwiz.utils.session_validation import SessionValidator

        report_path = tmp_path / "report.html"
        # Write binary content that's not valid UTF-8
        report_path.write_bytes(b"\x80\x81\x82\x83")

        validator = SessionValidator(report_path)
        metadata = validator.get_session_metadata()

        assert metadata.is_corrupted is True
        assert "utf-8" in metadata.corruption_reason.lower()

    def test_validate_html_content_valid(self, tmp_path):
        """Test validating valid HTML content."""
        from finwiz.utils.session_validation import SessionValidator

        html_content = """<!DOCTYPE html>
        <html>
        <head>
            <title>Report</title>
            <meta name="plan-id" content="test">
            <meta name="created-at" content="2025-01-01">
            <meta name="last-updated" content="2025-01-02">
        </head>
        <body>Content</body>
        </html>"""

        validator = SessionValidator(tmp_path / "report.html")
        is_valid, issues = validator.validate_html_content(html_content)

        assert is_valid is True
        assert len(issues) == 0

    def test_validate_html_content_empty(self, tmp_path):
        """Test validating empty HTML content."""
        from finwiz.utils.session_validation import SessionValidator

        validator = SessionValidator(tmp_path / "report.html")
        is_valid, issues = validator.validate_html_content("")

        assert is_valid is False
        assert any("empty" in issue.lower() for issue in issues)

    def test_validate_html_content_not_html(self, tmp_path):
        """Test validating non-HTML content."""
        from finwiz.utils.session_validation import SessionValidator

        validator = SessionValidator(tmp_path / "report.html")
        is_valid, issues = validator.validate_html_content("Just plain text")

        assert is_valid is False
        assert any("html" in issue.lower() for issue in issues)

    def test_validate_html_content_missing_meta_tags(self, tmp_path):
        """Test validating HTML with missing meta tags."""
        from finwiz.utils.session_validation import SessionValidator

        html_content = """<!DOCTYPE html>
        <html>
        <head><title>Report</title></head>
        <body>Content</body>
        </html>"""

        validator = SessionValidator(tmp_path / "report.html")
        is_valid, issues = validator.validate_html_content(html_content)

        assert is_valid is False
        assert any("meta" in issue.lower() for issue in issues)

    def test_validate_html_content_missing_elements(self, tmp_path):
        """Test validating HTML with missing required elements."""
        from finwiz.utils.session_validation import SessionValidator

        html_content = "<html><div>No head or body</div></html>"

        validator = SessionValidator(tmp_path / "report.html")
        is_valid, issues = validator.validate_html_content(html_content)

        assert is_valid is False
        assert any("head" in issue.lower() or "body" in issue.lower() for issue in issues)

    def test_validate_client_profile_valid(self, tmp_path, mocker):
        """Test validating valid client profile."""
        from finwiz.utils.session_validation import SessionValidator

        mock_profile = mocker.MagicMock()
        mock_profile.age = 35
        mock_profile.investment_horizon = "long term"
        mock_profile.currency = "USD"

        validator = SessionValidator(tmp_path / "report.html")
        issues = validator._validate_client_profile(mock_profile)

        assert len(issues) == 0

    def test_validate_client_profile_invalid_age(self, tmp_path, mocker):
        """Test validating client profile with invalid age."""
        from finwiz.utils.session_validation import SessionValidator

        mock_profile = mocker.MagicMock()
        mock_profile.age = 150  # Too old
        mock_profile.investment_horizon = None
        mock_profile.currency = None

        validator = SessionValidator(tmp_path / "report.html")
        issues = validator._validate_client_profile(mock_profile)

        assert any("age" in issue.lower() for issue in issues)

    def test_validate_client_profile_too_young(self, tmp_path, mocker):
        """Test validating client profile with too young age."""
        from finwiz.utils.session_validation import SessionValidator

        mock_profile = mocker.MagicMock()
        mock_profile.age = 10  # Too young
        mock_profile.investment_horizon = None
        mock_profile.currency = None

        validator = SessionValidator(tmp_path / "report.html")
        issues = validator._validate_client_profile(mock_profile)

        assert any("age" in issue.lower() for issue in issues)

    def test_validate_client_profile_invalid_currency(self, tmp_path, mocker):
        """Test validating client profile with invalid currency."""
        from finwiz.utils.session_validation import SessionValidator

        mock_profile = mocker.MagicMock()
        mock_profile.age = None
        mock_profile.investment_horizon = None
        mock_profile.currency = "INVALID"  # Not 3 chars

        validator = SessionValidator(tmp_path / "report.html")
        issues = validator._validate_client_profile(mock_profile)

        assert any("currency" in issue.lower() for issue in issues)

    def test_validate_portfolio_data_empty(self, tmp_path):
        """Test validating empty portfolio data."""
        from finwiz.utils.session_validation import SessionValidator

        validator = SessionValidator(tmp_path / "report.html")
        issues = validator._validate_portfolio_data({})

        assert len(issues) == 0

    def test_validate_portfolio_data_valid_holdings(self, tmp_path):
        """Test validating valid portfolio holdings."""
        from finwiz.utils.session_validation import SessionValidator

        portfolio_data = {
            "holdings": [
                {"name": "Apple Inc", "ticker": "AAPL"},
                {"name": "Microsoft", "ticker": "MSFT"},
            ]
        }

        validator = SessionValidator(tmp_path / "report.html")
        issues = validator._validate_portfolio_data(portfolio_data)

        assert len(issues) == 0

    def test_validate_portfolio_data_invalid_holdings_type(self, tmp_path):
        """Test validating portfolio with invalid holdings type."""
        from finwiz.utils.session_validation import SessionValidator

        portfolio_data = {"holdings": "not a list"}

        validator = SessionValidator(tmp_path / "report.html")
        issues = validator._validate_portfolio_data(portfolio_data)

        assert any("list" in issue.lower() for issue in issues)

    def test_validate_portfolio_data_missing_required_fields(self, tmp_path):
        """Test validating portfolio holdings with missing fields."""
        from finwiz.utils.session_validation import SessionValidator

        portfolio_data = {
            "holdings": [
                {"name": "Apple Inc"},  # Missing ticker
                {"ticker": "MSFT"},  # Missing name
            ]
        }

        validator = SessionValidator(tmp_path / "report.html")
        issues = validator._validate_portfolio_data(portfolio_data)

        assert len(issues) >= 2
        assert any("ticker" in issue.lower() for issue in issues)
        assert any("name" in issue.lower() for issue in issues)

    def test_validate_portfolio_data_invalid_holding_type(self, tmp_path):
        """Test validating portfolio with invalid holding type."""
        from finwiz.utils.session_validation import SessionValidator

        portfolio_data = {"holdings": ["not a dict", "also not a dict"]}

        validator = SessionValidator(tmp_path / "report.html")
        issues = validator._validate_portfolio_data(portfolio_data)

        assert any("dictionary" in issue.lower() for issue in issues)

    def test_validate_portfolio_data_allocations(self, tmp_path):
        """Test validating target allocations."""
        from finwiz.utils.session_validation import SessionValidator

        portfolio_data = {
            "target_allocations": [
                {"category": "Stocks", "target_allocation": "60%"},
                {"category": "Bonds", "target_allocation": "40%"},
            ]
        }

        validator = SessionValidator(tmp_path / "report.html")
        issues = validator._validate_portfolio_data(portfolio_data)

        assert len(issues) == 0

    def test_validate_portfolio_data_unreasonable_allocations(self, tmp_path):
        """Test validating unreasonable total allocations."""
        from finwiz.utils.session_validation import SessionValidator

        portfolio_data = {
            "target_allocations": [
                {"category": "Stocks", "target_allocation": "150%"},
            ]
        }

        validator = SessionValidator(tmp_path / "report.html")
        issues = validator._validate_portfolio_data(portfolio_data)

        assert any("unreasonable" in issue.lower() for issue in issues)

    def test_validate_recommendations_empty(self, tmp_path):
        """Test validating empty recommendations."""
        from finwiz.utils.session_validation import SessionValidator

        validator = SessionValidator(tmp_path / "report.html")
        issues = validator._validate_recommendations({})

        assert len(issues) == 0

    def test_validate_recommendations_valid(self, tmp_path):
        """Test validating valid recommendations."""
        from finwiz.utils.session_validation import SessionValidator

        recommendations = {
            "buy": ["AAPL", "MSFT"],
            "sell": ["IBM"],
            "hold": ["GOOG"],
        }

        validator = SessionValidator(tmp_path / "report.html")
        issues = validator._validate_recommendations(recommendations)

        assert len(issues) == 0

    def test_validate_recommendations_not_list(self, tmp_path):
        """Test validating recommendations with non-list category."""
        from finwiz.utils.session_validation import SessionValidator

        recommendations = {"buy": "AAPL"}  # Should be list

        validator = SessionValidator(tmp_path / "report.html")
        issues = validator._validate_recommendations(recommendations)

        assert any("list" in issue.lower() for issue in issues)

    def test_validate_recommendations_empty_category(self, tmp_path):
        """Test validating recommendations with empty category."""
        from finwiz.utils.session_validation import SessionValidator

        recommendations = {"buy": []}

        validator = SessionValidator(tmp_path / "report.html")
        issues = validator._validate_recommendations(recommendations)

        assert any("empty" in issue.lower() for issue in issues)

    def test_validate_recommendations_non_string_items(self, tmp_path):
        """Test validating recommendations with non-string items."""
        from finwiz.utils.session_validation import SessionValidator

        recommendations = {"buy": [123, {"ticker": "AAPL"}]}

        validator = SessionValidator(tmp_path / "report.html")
        issues = validator._validate_recommendations(recommendations)

        assert any("string" in issue.lower() for issue in issues)

    def test_validate_recommendations_empty_string_items(self, tmp_path):
        """Test validating recommendations with empty string items."""
        from finwiz.utils.session_validation import SessionValidator

        recommendations = {"buy": ["AAPL", "", "  "]}

        validator = SessionValidator(tmp_path / "report.html")
        issues = validator._validate_recommendations(recommendations)

        assert any("empty" in issue.lower() for issue in issues)

    def test_check_file_corruption_not_corrupted(self, tmp_path):
        """Test check_file_corruption for valid file."""
        from finwiz.utils.session_validation import SessionValidator

        report_path = tmp_path / "report.html"
        report_path.write_text("<!DOCTYPE html><html><head></head><body></body></html>")

        validator = SessionValidator(report_path)
        is_corrupted, reason = validator.check_file_corruption()

        assert is_corrupted is False
        assert reason is None

    def test_check_file_corruption_corrupted(self, tmp_path):
        """Test check_file_corruption for corrupted file."""
        from finwiz.utils.session_validation import SessionValidator

        report_path = tmp_path / "report.html"
        report_path.write_text("")  # Empty file is corrupted

        validator = SessionValidator(report_path)
        is_corrupted, reason = validator.check_file_corruption()

        assert is_corrupted is True
        assert reason is not None
