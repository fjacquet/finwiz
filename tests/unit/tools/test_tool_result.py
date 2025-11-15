"""
Unit tests for ToolResult standardization.

Tests the ToolResult dataclass for consistent error handling across tools.
"""

import pytest

from finwiz.tools.tool_result import ToolResult


class TestToolResult:
    """Test suite for ToolResult dataclass."""

    def test_should_create_success_result(self):
        """Test creating a successful ToolResult."""
        # Arrange
        data = {"ticker": "AAPL", "price": 150.0}

        # Act
        result = ToolResult.success_result(data)

        # Assert
        assert result.success is True
        assert result.data == data
        assert result.error is None

    def test_should_create_error_result(self):
        """Test creating an error ToolResult."""
        # Arrange
        error_msg = "API connection failed"

        # Act
        result = ToolResult.error_result(error_msg)

        # Assert
        assert result.success is False
        assert result.data == {}
        assert result.error == error_msg

    def test_should_create_error_result_with_partial_data(self):
        """Test creating an error ToolResult with partial data."""
        # Arrange
        error_msg = "Validation failed"
        partial_data = {"ticker": "AAPL", "validated": False}

        # Act
        result = ToolResult.error_result(error_msg, partial_data)

        # Assert
        assert result.success is False
        assert result.data == partial_data
        assert result.error == error_msg

    def test_should_convert_to_dict(self):
        """Test converting ToolResult to dictionary."""
        # Arrange
        data = {"ticker": "AAPL", "price": 150.0}
        result = ToolResult.success_result(data)

        # Act
        result_dict = result.to_dict()

        # Assert
        assert isinstance(result_dict, dict)
        assert result_dict["success"] is True
        assert result_dict["data"] == data
        assert result_dict["error"] is None

    def test_should_convert_error_to_dict(self):
        """Test converting error ToolResult to dictionary."""
        # Arrange
        error_msg = "API connection failed"
        result = ToolResult.error_result(error_msg)

        # Act
        result_dict = result.to_dict()

        # Assert
        assert isinstance(result_dict, dict)
        assert result_dict["success"] is False
        assert result_dict["data"] == {}
        assert result_dict["error"] == error_msg

    def test_should_have_consistent_structure(self):
        """Test that all ToolResults have consistent structure."""
        # Arrange
        success_result = ToolResult.success_result({"key": "value"})
        error_result = ToolResult.error_result("error message")

        # Act
        success_dict = success_result.to_dict()
        error_dict = error_result.to_dict()

        # Assert - Both should have same keys
        assert set(success_dict.keys()) == set(error_dict.keys())
        assert set(success_dict.keys()) == {"success", "data", "error"}


class TestToolResultUsagePatterns:
    """Test common usage patterns for ToolResult."""

    def test_should_handle_empty_data(self):
        """Test ToolResult with empty data dictionary."""
        # Arrange & Act
        result = ToolResult.success_result({})

        # Assert
        assert result.success is True
        assert result.data == {}
        assert result.error is None

    def test_should_handle_complex_data(self):
        """Test ToolResult with complex nested data."""
        # Arrange
        complex_data = {
            "ticker": "AAPL",
            "analysis": {
                "fundamental": {"roe": 0.25, "debt": 0.3},
                "technical": {"rsi": 65, "macd": 1.2},
            },
            "recommendation": "BUY",
        }

        # Act
        result = ToolResult.success_result(complex_data)

        # Assert
        assert result.success is True
        assert result.data == complex_data
        assert result.data["analysis"]["fundamental"]["roe"] == 0.25

    def test_should_preserve_data_types(self):
        """Test that ToolResult preserves data types."""
        # Arrange
        data = {
            "string": "value",
            "integer": 42,
            "float": 3.14,
            "boolean": True,
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
        }

        # Act
        result = ToolResult.success_result(data)
        result_dict = result.to_dict()

        # Assert
        assert isinstance(result_dict["data"]["string"], str)
        assert isinstance(result_dict["data"]["integer"], int)
        assert isinstance(result_dict["data"]["float"], float)
        assert isinstance(result_dict["data"]["boolean"], bool)
        assert isinstance(result_dict["data"]["list"], list)
        assert isinstance(result_dict["data"]["dict"], dict)


class TestToolResultErrorHandling:
    """Test error handling scenarios with ToolResult."""

    def test_should_handle_exception_message(self):
        """Test ToolResult with exception message."""
        # Arrange
        try:
            raise ValueError("Invalid ticker format")
        except ValueError as e:
            error_msg = str(e)

        # Act
        result = ToolResult.error_result(error_msg)

        # Assert
        assert result.success is False
        assert result.error == "Invalid ticker format"

    def test_should_handle_multiple_error_types(self):
        """Test ToolResult with different error types."""
        # Arrange
        errors = [
            "Connection timeout",
            "Invalid API key",
            "Rate limit exceeded",
            "Data not found",
        ]

        # Act & Assert
        for error in errors:
            result = ToolResult.error_result(error)
            assert result.success is False
            assert result.error == error
            assert result.data == {}

    def test_should_include_context_in_error_data(self):
        """Test ToolResult error with contextual data."""
        # Arrange
        error_msg = "Validation failed"
        context = {
            "ticker": "INVALID",
            "reason": "Ticker not found",
            "attempted_at": "2025-01-01T00:00:00Z",
        }

        # Act
        result = ToolResult.error_result(error_msg, context)

        # Assert
        assert result.success is False
        assert result.error == error_msg
        assert result.data["ticker"] == "INVALID"
        assert result.data["reason"] == "Ticker not found"
