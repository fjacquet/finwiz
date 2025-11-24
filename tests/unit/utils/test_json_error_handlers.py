"""
Unit tests for JSON error handlers.

Tests JSON parsing error handling, schema validation error handling,
and sanitized logging functionality.
"""

from pytest import approx
import json
import logging

import pytest
from pydantic import BaseModel, Field

from finwiz.utils.json_error_handlers import (
    JSONParsingError,
    SchemaValidationError,
    format_validation_summary,
    handle_missing_fields,
    handle_type_mismatches,
    parse_json_file,
    parse_json_string,
    validate_schema,
)


# Test schema for validation tests
class TestSchema(BaseModel):
    """Test schema for validation."""

    ticker: str = Field(..., description="Stock ticker")
    price: float = Field(..., ge=0.0, description="Stock price")
    volume: int = Field(..., ge=0, description="Trading volume")
    recommendation: str = Field(..., pattern="^(BUY|HOLD|SELL)$")
    optional_field: str | None = None


class TestJSONParsingError:
    """Test suite for JSONParsingError."""

    def test_should_create_error_with_all_details(self):
        """Test creating error with file path, line, column, and message."""
        # Arrange & Act
        error = JSONParsingError(
            file_path="/path/to/file.json",
            line_number=5,
            column=12,
            message="Expecting property name enclosed in double quotes",
        )

        # Assert
        assert error.file_path == "/path/to/file.json"
        assert error.line_number == 5
        assert error.column == 12
        assert "Line: 5" in str(error)
        assert "Column: 12" in str(error)
        assert "Expecting property name" in str(error)

    def test_should_create_error_without_line_column(self):
        """Test creating error without line and column numbers."""
        # Arrange & Act
        error = JSONParsingError(file_path="/path/to/file.json", line_number=None, column=None, message="Invalid JSON")

        # Assert
        assert error.file_path == "/path/to/file.json"
        assert error.line_number is None
        assert error.column is None
        assert "Line:" not in str(error)
        assert "Column:" not in str(error)
        assert "Invalid JSON" in str(error)

    def test_should_format_message_correctly(self):
        """Test error message formatting."""
        # Arrange & Act
        error = JSONParsingError(file_path="test.json", line_number=10, column=5, message="Unexpected token")

        # Assert
        message = str(error)
        assert "JSON parsing failed" in message
        assert "File: test.json" in message
        assert "Line: 10" in message
        assert "Column: 5" in message
        assert "Unexpected token" in message


class TestSchemaValidationError:
    """Test suite for SchemaValidationError."""

    def test_should_create_error_with_validation_details(self):
        """Test creating error with field-level validation details."""
        # Arrange
        errors = [
            {"loc": ("ticker",), "type": "missing", "msg": "Field required"},
            {"loc": ("price",), "type": "float_parsing", "msg": "Input should be a valid number"},
        ]

        # Act
        error = SchemaValidationError(schema_name="TestSchema", errors=errors)

        # Assert
        assert error.schema_name == "TestSchema"
        assert len(error.errors) == 2
        assert "TestSchema" in str(error)
        assert "ticker" in str(error)
        assert "price" in str(error)

    def test_should_format_nested_field_paths(self):
        """Test formatting of nested field paths."""
        # Arrange
        errors = [
            {
                "loc": ("holdings", 0, "ticker"),
                "type": "missing",
                "msg": "Field required",
            }
        ]

        # Act
        error = SchemaValidationError(schema_name="PortfolioSchema", errors=errors)

        # Assert
        message = str(error)
        assert "holdings -> 0 -> ticker" in message

    def test_should_include_error_count(self):
        """Test that error message includes total error count."""
        # Arrange
        errors = [
            {"loc": ("field1",), "type": "missing", "msg": "Required"},
            {"loc": ("field2",), "type": "missing", "msg": "Required"},
            {"loc": ("field3",), "type": "type_error", "msg": "Invalid type"},
        ]

        # Act
        error = SchemaValidationError(schema_name="TestSchema", errors=errors)

        # Assert
        assert "Total errors: 3" in str(error)


class TestParseJSONFile:
    """Test suite for parse_json_file function."""

    def test_should_parse_valid_json_file(self, tmp_path):
        """Test parsing valid JSON file."""
        # Arrange
        json_file = tmp_path / "test.json"
        test_data = {"ticker": "AAPL", "price": 150.0}
        json_file.write_text(json.dumps(test_data))

        # Act
        result = parse_json_file(json_file)

        # Assert
        assert result == test_data
        assert result["ticker"] == "AAPL"
        assert result["price"] == approx(150.0)

    def test_should_raise_error_for_invalid_json(self, tmp_path):
        """Test error handling for invalid JSON syntax."""
        # Arrange
        json_file = tmp_path / "invalid.json"
        json_file.write_text('{"ticker": "AAPL", "price": }')  # Invalid JSON

        # Act & Assert
        with pytest.raises(JSONParsingError) as exc_info:
            parse_json_file(json_file)

        error = exc_info.value
        assert str(json_file) in error.file_path
        assert error.line_number is not None
        assert error.column is not None

    def test_should_raise_error_for_missing_file(self, tmp_path):
        """Test error handling for non-existent file."""
        # Arrange
        json_file = tmp_path / "nonexistent.json"

        # Act & Assert
        with pytest.raises(FileNotFoundError) as exc_info:
            parse_json_file(json_file)

        assert "not found" in str(exc_info.value)

    def test_should_handle_path_object(self, tmp_path):
        """Test that function accepts Path objects."""
        # Arrange
        json_file = tmp_path / "test.json"
        test_data = {"key": "value"}
        json_file.write_text(json.dumps(test_data))

        # Act
        result = parse_json_file(json_file)

        # Assert
        assert result == test_data

    def test_should_handle_string_path(self, tmp_path):
        """Test that function accepts string paths."""
        # Arrange
        json_file = tmp_path / "test.json"
        test_data = {"key": "value"}
        json_file.write_text(json.dumps(test_data))

        # Act
        result = parse_json_file(str(json_file))

        # Assert
        assert result == test_data

    def test_should_log_sanitized_error(self, tmp_path, caplog):
        """Test that error logging excludes file contents."""
        # Arrange
        json_file = tmp_path / "invalid.json"
        json_file.write_text('{"invalid": }')

        # Act
        with caplog.at_level(logging.ERROR):
            with pytest.raises(JSONParsingError):
                parse_json_file(json_file)

        # Assert
        assert len(caplog.records) > 0
        log_record = caplog.records[0]
        # Verify sanitized logging (no file contents)
        assert "file_path" in log_record.__dict__
        assert "line_number" in log_record.__dict__
        assert "column" in log_record.__dict__
        # Ensure actual JSON content is not in logs
        assert '{"invalid": }' not in caplog.text


class TestParseJSONString:
    """Test suite for parse_json_string function."""

    def test_should_parse_valid_json_string(self):
        """Test parsing valid JSON string."""
        # Arrange
        json_str = '{"ticker": "AAPL", "price": 150.0}'

        # Act
        result = parse_json_string(json_str)

        # Assert
        assert result["ticker"] == "AAPL"
        assert result["price"] == approx(150.0)

    def test_should_raise_error_for_invalid_json_string(self):
        """Test error handling for invalid JSON string."""
        # Arrange
        json_str = '{"ticker": "AAPL", "price": }'

        # Act & Assert
        with pytest.raises(JSONParsingError) as exc_info:
            parse_json_string(json_str)

        error = exc_info.value
        assert error.line_number is not None
        assert error.column is not None

    def test_should_use_custom_source_name(self):
        """Test using custom source name for error reporting."""
        # Arrange
        json_str = '{"invalid": }'
        source_name = "task_output"

        # Act & Assert
        with pytest.raises(JSONParsingError) as exc_info:
            parse_json_string(json_str, source_name=source_name)

        error = exc_info.value
        assert source_name in error.file_path

    def test_should_log_sanitized_error(self, caplog):
        """Test that error logging excludes JSON contents."""
        # Arrange
        json_str = '{"sensitive": "data", "invalid": }'

        # Act
        with caplog.at_level(logging.ERROR):
            with pytest.raises(JSONParsingError):
                parse_json_string(json_str, source_name="test_source")

        # Assert
        assert len(caplog.records) > 0
        log_record = caplog.records[0]
        # Verify sanitized logging
        assert "source" in log_record.__dict__
        assert "line_number" in log_record.__dict__
        # Ensure actual JSON content is not in logs
        assert "sensitive" not in caplog.text
        assert "data" not in caplog.text


class TestValidateSchema:
    """Test suite for validate_schema function."""

    def test_should_validate_correct_data(self):
        """Test validation of data that conforms to schema."""
        # Arrange
        data = {
            "ticker": "AAPL",
            "price": 150.0,
            "volume": 1000000,
            "recommendation": "BUY",
        }

        # Act
        result = validate_schema(data, TestSchema)

        # Assert
        assert isinstance(result, TestSchema)
        assert result.ticker == "AAPL"
        assert result.price == approx(150.0)
        assert result.volume == 1000000
        assert result.recommendation == "BUY"

    def test_should_raise_error_for_missing_fields(self):
        """Test validation error for missing required fields."""
        # Arrange
        data = {"ticker": "AAPL"}  # Missing price, volume, recommendation

        # Act & Assert
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_schema(data, TestSchema)

        error = exc_info.value
        assert error.schema_name == "TestSchema"
        assert len(error.errors) >= 3  # At least 3 missing fields

    def test_should_raise_error_for_type_mismatch(self):
        """Test validation error for type mismatches."""
        # Arrange
        data = {
            "ticker": "AAPL",
            "price": "not_a_number",  # Should be float
            "volume": 1000000,
            "recommendation": "BUY",
        }

        # Act & Assert
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_schema(data, TestSchema)

        error = exc_info.value
        assert "price" in str(error)

    def test_should_raise_error_for_pattern_violation(self):
        """Test validation error for pattern constraint violation."""
        # Arrange
        data = {
            "ticker": "AAPL",
            "price": 150.0,
            "volume": 1000000,
            "recommendation": "INVALID",  # Not BUY/HOLD/SELL
        }

        # Act & Assert
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_schema(data, TestSchema)

        error = exc_info.value
        assert "recommendation" in str(error)

    def test_should_use_custom_schema_name(self):
        """Test using custom schema name for error reporting."""
        # Arrange
        data = {"ticker": "AAPL"}  # Missing fields
        custom_name = "CustomTestSchema"

        # Act & Assert
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_schema(data, TestSchema, schema_name=custom_name)

        error = exc_info.value
        assert error.schema_name == custom_name

    def test_should_log_sanitized_error(self, caplog):
        """Test that error logging excludes data values."""
        # Arrange
        data = {
            "ticker": "SENSITIVE_TICKER",
            "price": "invalid",
            "volume": 1000000,
            "recommendation": "BUY",
        }

        # Act
        with caplog.at_level(logging.ERROR):
            with pytest.raises(SchemaValidationError):
                validate_schema(data, TestSchema)

        # Assert
        assert len(caplog.records) > 0
        log_record = caplog.records[0]
        # Verify sanitized logging (field names but not values)
        assert "schema" in log_record.__dict__
        assert "error_count" in log_record.__dict__
        assert "field_errors" in log_record.__dict__
        # Ensure actual data values are not in logs
        assert "SENSITIVE_TICKER" not in caplog.text


class TestHandleMissingFields:
    """Test suite for handle_missing_fields function."""

    def test_should_extract_missing_fields(self):
        """Test extraction of missing field names."""
        # Arrange
        errors = [
            {"loc": ("ticker",), "type": "missing", "msg": "Field required"},
            {"loc": ("price",), "type": "missing", "msg": "Field required"},
            {"loc": ("volume",), "type": "float_parsing", "msg": "Invalid"},
        ]

        # Act
        missing = handle_missing_fields(errors)

        # Assert
        assert len(missing) == 2
        assert "ticker" in missing
        assert "price" in missing
        assert "volume" not in missing

    def test_should_handle_nested_field_paths(self):
        """Test extraction of nested missing fields."""
        # Arrange
        errors = [
            {"loc": ("holdings", 0, "ticker"), "type": "missing", "msg": "Required"},
            {"loc": ("metadata", "date"), "type": "missing", "msg": "Required"},
        ]

        # Act
        missing = handle_missing_fields(errors)

        # Assert
        assert len(missing) == 2
        assert "holdings -> 0 -> ticker" in missing
        assert "metadata -> date" in missing

    def test_should_return_empty_list_when_no_missing_fields(self):
        """Test that empty list is returned when no missing fields."""
        # Arrange
        errors = [
            {"loc": ("price",), "type": "float_parsing", "msg": "Invalid"},
            {"loc": ("volume",), "type": "int_parsing", "msg": "Invalid"},
        ]

        # Act
        missing = handle_missing_fields(errors)

        # Assert
        assert len(missing) == 0


class TestHandleTypeMismatches:
    """Test suite for handle_type_mismatches function."""

    def test_should_extract_type_errors(self):
        """Test extraction of type mismatch errors."""
        # Arrange
        errors = [
            {"loc": ("price",), "type": "float_parsing", "msg": "Invalid number"},
            {"loc": ("volume",), "type": "int_parsing", "msg": "Invalid integer"},
            {"loc": ("ticker",), "type": "missing", "msg": "Required"},
        ]

        # Act
        type_errors = handle_type_mismatches(errors)

        # Assert
        assert len(type_errors) == 2
        assert any(e["field"] == "price" for e in type_errors)
        assert any(e["field"] == "volume" for e in type_errors)

    def test_should_include_error_details(self):
        """Test that type errors include field, type, and message."""
        # Arrange
        errors = [
            {"loc": ("price",), "type": "float_parsing", "msg": "Invalid number"},
        ]

        # Act
        type_errors = handle_type_mismatches(errors)

        # Assert
        assert len(type_errors) == 1
        error = type_errors[0]
        assert "field" in error
        assert "error_type" in error
        assert "message" in error
        assert error["field"] == "price"
        assert error["error_type"] == "float_parsing"

    def test_should_handle_nested_field_paths(self):
        """Test extraction of nested type errors."""
        # Arrange
        errors = [
            {
                "loc": ("holdings", 0, "price"),
                "type": "float_parsing",
                "msg": "Invalid",
            }
        ]

        # Act
        type_errors = handle_type_mismatches(errors)

        # Assert
        assert len(type_errors) == 1
        assert type_errors[0]["field"] == "holdings -> 0 -> price"

    def test_should_return_empty_list_when_no_type_errors(self):
        """Test that empty list is returned when no type errors."""
        # Arrange
        errors = [
            {"loc": ("ticker",), "type": "missing", "msg": "Required"},
            {"loc": ("recommendation",), "type": "string_pattern_mismatch", "msg": "Invalid"},
        ]

        # Act
        type_errors = handle_type_mismatches(errors)

        # Assert
        assert len(type_errors) == 0


class TestFormatValidationSummary:
    """Test suite for format_validation_summary function."""

    def test_should_format_missing_fields_section(self):
        """Test formatting of missing fields section."""
        # Arrange
        errors = [
            {"loc": ("ticker",), "type": "missing", "msg": "Field required"},
            {"loc": ("price",), "type": "missing", "msg": "Field required"},
        ]

        # Act
        summary = format_validation_summary(errors)

        # Assert
        assert "Missing required fields:" in summary
        assert "ticker" in summary
        assert "price" in summary

    def test_should_format_type_mismatches_section(self):
        """Test formatting of type mismatches section."""
        # Arrange
        errors = [
            {"loc": ("price",), "type": "float_parsing", "msg": "Invalid number"},
            {"loc": ("volume",), "type": "int_parsing", "msg": "Invalid integer"},
        ]

        # Act
        summary = format_validation_summary(errors)

        # Assert
        assert "Type mismatches:" in summary
        assert "price" in summary
        assert "volume" in summary

    def test_should_format_other_errors_section(self):
        """Test formatting of other validation errors."""
        # Arrange
        errors = [
            {
                "loc": ("recommendation",),
                "type": "string_pattern_mismatch",
                "msg": "String should match pattern",
            }
        ]

        # Act
        summary = format_validation_summary(errors)

        # Assert
        assert "Other validation errors:" in summary
        assert "recommendation" in summary

    def test_should_format_all_sections_together(self):
        """Test formatting with all error types present."""
        # Arrange
        errors = [
            {"loc": ("ticker",), "type": "missing", "msg": "Required"},
            {"loc": ("price",), "type": "float_parsing", "msg": "Invalid number"},
            {
                "loc": ("recommendation",),
                "type": "string_pattern_mismatch",
                "msg": "Invalid pattern",
            },
        ]

        # Act
        summary = format_validation_summary(errors)

        # Assert
        assert "Missing required fields:" in summary
        assert "Type mismatches:" in summary
        assert "Other validation errors:" in summary
        assert "ticker" in summary
        assert "price" in summary
        assert "recommendation" in summary

    def test_should_use_bullet_points(self):
        """Test that summary uses bullet points for readability."""
        # Arrange
        errors = [
            {"loc": ("ticker",), "type": "missing", "msg": "Required"},
            {"loc": ("price",), "type": "missing", "msg": "Required"},
        ]

        # Act
        summary = format_validation_summary(errors)

        # Assert
        assert "•" in summary  # Bullet point character

    def test_should_handle_empty_errors_list(self):
        """Test formatting with empty errors list."""
        # Arrange
        errors = []

        # Act
        summary = format_validation_summary(errors)

        # Assert
        assert summary == ""