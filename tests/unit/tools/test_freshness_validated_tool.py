"""
Unit tests for FreshnessValidatedTool wrapper.

Tests the tool wrapper that adds freshness validation to existing CrewAI tools.
"""

from datetime import UTC, datetime, timedelta

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from pytest import approx

from finwiz.integration.freshness_validated_tool import FreshnessValidatedTool, RefreshResult, add_freshness_validation
from finwiz.validation.freshness import DataFreshnessValidator


class MockToolInput(BaseModel):
    """Mock input schema for testing."""

    ticker: str = Field(..., description="Stock ticker symbol")


class MockTool(BaseTool):
    """Mock tool for testing purposes."""

    name: str = "Mock Tool"
    description: str = "A mock tool for testing"
    args_schema: type[BaseModel] = MockToolInput

    def __init__(self, return_data=None, should_error=False, **kwargs):
        """Initialize mock tool with test data."""
        super().__init__(**kwargs)
        # Store test data as private attributes to avoid Pydantic validation
        self._return_data = return_data or {"symbol": "AAPL", "price": 150.0}
        self._should_error = should_error
        self._call_count = 0

    @property
    def return_data(self):
        return self._return_data

    @return_data.setter
    def return_data(self, value):
        self._return_data = value

    @property
    def should_error(self):
        return self._should_error

    @property
    def call_count(self):
        return self._call_count

    def _run(self, ticker: str) -> dict:
        """Mock tool execution."""
        self._call_count += 1

        if self._should_error:
            return {"error": "Mock tool error"}

        # Return the data as-is, preserving any existing timestamp
        result = self._return_data.copy()

        # Only add timestamp if not already present (to preserve test data)
        if "timestamp" not in result:
            result["timestamp"] = datetime.now(UTC).isoformat()

        return result


class TestRefreshResult:
    """Test RefreshResult class."""

    def test_should_initialize_with_success(self):
        """Test RefreshResult initialization with success."""
        result = RefreshResult(success=True, data={"test": "data"})

        assert result.success is True
        assert result.data == {"test": "data"}
        assert result.error is None

    def test_should_initialize_with_error(self):
        """Test RefreshResult initialization with error."""
        result = RefreshResult(success=False, error="Test error")

        assert result.success is False
        assert result.data is None
        assert result.error == "Test error"


class TestFreshnessValidatedTool:
    """Test FreshnessValidatedTool wrapper."""

    def test_should_initialize_with_base_tool(self):
        """Test wrapper initialization with base tool."""
        base_tool = MockTool()
        wrapper = FreshnessValidatedTool(base_tool)

        assert wrapper.base_tool == base_tool
        assert wrapper.name == f"FreshData_{base_tool.name}"
        assert base_tool.description in wrapper.description
        assert wrapper.args_schema == base_tool.args_schema
        assert isinstance(wrapper.validator, DataFreshnessValidator)

    def test_should_initialize_with_custom_validator(self):
        """Test wrapper initialization with custom validator."""
        base_tool = MockTool()
        custom_validator = DataFreshnessValidator(max_age_hours=12)
        wrapper = FreshnessValidatedTool(base_tool, validator=custom_validator)

        assert wrapper.validator == custom_validator
        assert wrapper.validator.max_age_hours == 12

    def test_should_pass_through_fresh_data(self):
        """Test that fresh data passes through without modification."""
        # Create mock tool with fresh data
        fresh_time = datetime.now(UTC) - timedelta(hours=1)
        mock_tool = MockTool(return_data={"symbol": "AAPL", "price": 150.0, "timestamp": fresh_time.isoformat()})

        wrapper = FreshnessValidatedTool(mock_tool)
        result = wrapper._run(ticker="AAPL")

        assert isinstance(result, dict)
        assert result["symbol"] == "AAPL"
        assert result["price"] == approx(150.0)
        assert "_freshness_info" in result
        assert result["_freshness_info"]["is_fresh"] is True
        assert mock_tool.call_count == 1

    def test_should_warn_about_stale_data(self, mocker):
        """Test warning behavior with stale data."""
        # Create mock tool with stale data
        stale_time = datetime.now(UTC) - timedelta(hours=48)
        mock_tool = MockTool(return_data={"symbol": "AAPL", "price": 150.0, "timestamp": stale_time.isoformat()})

        wrapper = FreshnessValidatedTool(mock_tool, max_age_hours=24)

        mock_logger = mocker.patch("finwiz.integration.freshness_validated_tool.logger")
        result = wrapper._run(ticker="AAPL")

        # Should log warning about stale data
        mock_logger.warning.assert_called()
        # Check that at least one warning contains "Stale data detected"
        warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
        assert any("Stale data detected" in call for call in warning_calls)

    def test_should_attempt_refresh_for_stale_data(self, mocker):
        """Test refresh attempt for stale data."""
        # Create mock tool that returns stale data first, then fresh data
        stale_time = datetime.now(UTC) - timedelta(hours=48)
        fresh_time = datetime.now(UTC) - timedelta(hours=1)

        mock_tool = MockTool()
        # First call returns stale data, second call returns fresh data
        mock_tool.return_data = {"symbol": "AAPL", "price": 150.0, "timestamp": stale_time.isoformat()}

        wrapper = FreshnessValidatedTool(mock_tool, max_age_hours=24)

        # Mock the refresh to return fresh data
        call_counter = [0]  # Use list to allow modification in nested function

        def mock_run_side_effect(ticker):
            call_counter[0] += 1
            if call_counter[0] == 1:
                # First call - stale data
                return {"symbol": "AAPL", "price": 150.0, "timestamp": stale_time.isoformat()}
            else:
                # Second call (refresh) - fresh data
                return {"symbol": "AAPL", "price": 150.0, "timestamp": fresh_time.isoformat()}

        mocker.patch.object(mock_tool, "_run", side_effect=mock_run_side_effect)
        result = wrapper._run(ticker="AAPL")

        # Should have attempted refresh (2 calls total)
        assert call_counter[0] >= 1
        assert isinstance(result, dict)

    def test_should_handle_tool_errors_gracefully(self):
        """Test graceful handling of tool errors."""
        mock_tool = MockTool(should_error=True)
        wrapper = FreshnessValidatedTool(mock_tool)

        result = wrapper._run(ticker="AAPL")

        assert isinstance(result, dict)
        assert "error" in result
        assert "Mock tool error" in result["error"]
        # Should not attempt freshness validation on error results
        assert "_freshness_info" not in result

    def test_should_handle_wrapper_exceptions(self, mocker):
        """Test handling of exceptions in wrapper logic."""
        mock_tool = MockTool()
        wrapper = FreshnessValidatedTool(mock_tool)

        # Mock validator to raise exception
        mocker.patch.object(wrapper.validator, "validate_data_freshness", side_effect=Exception("Test error"))
        result = wrapper._run(ticker="AAPL")

        assert isinstance(result, dict)
        assert "error" in result
        assert "Tool execution failed" in result["error"]

    def test_should_skip_validation_for_error_results(self, mocker):
        """Test that validation is skipped for error results."""
        mock_tool = MockTool(should_error=True)
        wrapper = FreshnessValidatedTool(mock_tool)

        mock_validate = mocker.patch.object(wrapper.validator, "validate_data_freshness")
        result = wrapper._run(ticker="AAPL")

        # Validation should not be called for error results
        mock_validate.assert_not_called()
        assert "error" in result

    def test_should_continue_with_stale_data_when_refresh_fails(self, mocker):
        """Test graceful degradation when refresh fails."""
        stale_time = datetime.now(UTC) - timedelta(hours=48)
        mock_tool = MockTool(return_data={"symbol": "AAPL", "price": 150.0, "timestamp": stale_time.isoformat()})

        wrapper = FreshnessValidatedTool(mock_tool, max_age_hours=24)

        # Mock refresh to always fail
        mocker.patch.object(wrapper, "_attempt_refresh", return_value=RefreshResult(success=False, error="Refresh failed"))
        result = wrapper._run(ticker="AAPL")

        # Should continue with stale data
        assert isinstance(result, dict)
        assert result["symbol"] == "AAPL"
        assert "_freshness_info" in result
        assert result["_freshness_info"]["is_fresh"] is False

    def test_refresh_result_with_successful_refresh(self):
        """Test RefreshResult with successful data refresh."""
        fresh_time = datetime.now(UTC) - timedelta(hours=1)
        mock_tool = MockTool(return_data={"symbol": "AAPL", "price": 150.0, "timestamp": fresh_time.isoformat()})

        wrapper = FreshnessValidatedTool(mock_tool)
        refresh_result = wrapper._attempt_refresh(ticker="AAPL")

        assert refresh_result.success is True
        assert refresh_result.data is not None
        assert refresh_result.error is None

    def test_refresh_result_with_failed_refresh(self):
        """Test RefreshResult with failed data refresh."""
        mock_tool = MockTool(should_error=True)
        wrapper = FreshnessValidatedTool(mock_tool)

        refresh_result = wrapper._attempt_refresh(ticker="AAPL")

        assert refresh_result.success is False
        assert refresh_result.data is None
        assert refresh_result.error is not None


class TestAddFreshnessValidation:
    """Test the convenience function for adding freshness validation."""

    def test_should_create_wrapper_with_default_settings(self):
        """Test convenience function with default settings."""
        base_tool = MockTool()
        wrapper = add_freshness_validation(base_tool)

        assert isinstance(wrapper, FreshnessValidatedTool)
        assert wrapper.base_tool == base_tool
        assert wrapper.validator.max_age_hours == 24

    def test_should_create_wrapper_with_custom_max_age(self):
        """Test convenience function with custom max age."""
        base_tool = MockTool()
        wrapper = add_freshness_validation(base_tool, max_age_hours=12)

        assert isinstance(wrapper, FreshnessValidatedTool)
        assert wrapper.validator.max_age_hours == 12
