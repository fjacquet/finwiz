"""Tests for ReporterInput validation functionality."""

from datetime import date

from finwiz.validation import ValidationManager, ValidationMode
from tests.fixtures.reporter_test_data import get_complete_input


class TestReporterInputValidation:
    """Test ReporterInput validation functionality."""

    def test_should_validate_complete_reporter_input(self):
        # Arrange
        manager = ValidationManager()
        manager.set_strictness_mode(ValidationMode.ERROR)

        complete_input = get_complete_input()

        # Act
        result = manager.validate_reporter_input(complete_input)

        # Assert
        assert result.is_valid is True
        assert result.has_errors is False
        assert result.sanitized_data is not None
        assert isinstance(result.sanitized_data["as_of"], date)

    def test_should_validate_minimal_reporter_input(self):
        # Arrange
        manager = ValidationManager()
        manager.set_strictness_mode(ValidationMode.ERROR)

        minimal_input = {
            "schema_version": 1,
            "ten_k_insights": [],
            "stock_sentiments": [],
            "stock_risks": [],
            "etf_factsheets": [],
            "etf_holdings": [],
            "etf_risks": [],
            "crypto_theses": [],
            "crypto_risks": [],
            "as_of": "2025-01-01",
        }

        # Act
        result = manager.validate_reporter_input(minimal_input)

        # Assert
        assert result.is_valid is True
        assert result.has_errors is False
        assert result.sanitized_data is not None

    def test_should_reject_reporter_input_with_missing_required_fields(self):
        # Arrange
        manager = ValidationManager()
        manager.set_strictness_mode(ValidationMode.ERROR)

        incomplete_input = {
            "schema_version": 1,
            "ten_k_insights": [],
            # Missing other required fields
        }

        # Act
        result = manager.validate_reporter_input(incomplete_input)

        # Assert
        assert result.is_valid is False
        assert result.has_errors is True
        # Should have both contract validation errors and schema validation errors

    def test_should_reject_reporter_input_with_extra_fields(self):
        # Arrange
        manager = ValidationManager()
        manager.set_strictness_mode(ValidationMode.ERROR)

        input_with_extra = {
            "schema_version": 1,
            "ten_k_insights": [],
            "stock_sentiments": [],
            "stock_risks": [],
            "etf_factsheets": [],
            "etf_holdings": [],
            "etf_risks": [],
            "crypto_theses": [],
            "crypto_risks": [],
            "as_of": "2025-01-01",
            "extra_field": "should_be_rejected",  # This should cause validation to fail
            "another_extra": "also_rejected",
        }

        # Act
        result = manager.validate_reporter_input(input_with_extra)

        # Assert
        assert result.is_valid is False
        assert result.has_errors is True
        assert any("extra_forbidden" in error.error_type for error in result.errors)

    def test_should_reject_reporter_input_with_invalid_field_types(self):
        # Arrange
        manager = ValidationManager()
        manager.set_strictness_mode(ValidationMode.ERROR)

        input_with_wrong_types = {
            "schema_version": "should_be_int",  # Wrong type
            "ten_k_insights": "should_be_list",  # Wrong type
            "stock_sentiments": [],
            "stock_risks": [],
            "etf_factsheets": [],
            "etf_holdings": [],
            "etf_risks": [],
            "crypto_theses": [],
            "crypto_risks": [],
            "as_of": "invalid_date_format",  # Wrong format
        }

        # Act
        result = manager.validate_reporter_input(input_with_wrong_types)

        # Assert
        assert result.is_valid is False
        assert result.has_errors is True
        assert len(result.errors) > 0

    def test_should_validate_nested_schema_items_in_reporter_input(self):
        # Arrange
        manager = ValidationManager()
        manager.set_strictness_mode(ValidationMode.ERROR)

        input_with_invalid_nested = {
            "schema_version": 1,
            "ten_k_insights": [
                {
                    "schema_version": 1,
                    "ticker": "AAPL",
                    "filing_url": "invalid_url",  # Invalid URL format
                    "filed_at": "invalid_date",  # Invalid date format
                    "section": "Invalid Section",  # Not in allowed enum
                    "excerpt": "Too short",  # Below minimum length
                    "sec_citation": "10-K (2024), Item 1A, p. 17",
                }
            ],
            "stock_sentiments": [],
            "stock_risks": [],
            "etf_factsheets": [],
            "etf_holdings": [],
            "etf_risks": [],
            "crypto_theses": [],
            "crypto_risks": [],
            "as_of": "2025-01-01",
        }

        # Act
        result = manager.validate_reporter_input(input_with_invalid_nested)

        # Assert
        assert result.is_valid is False
        assert result.has_errors is True
        # Should have multiple validation errors for the nested TenKInsight

    def test_should_handle_validation_modes_for_reporter_input(self):
        # Arrange
        manager = ValidationManager()

        invalid_input = {
            "schema_version": 1,
            "ten_k_insights": [],
            "stock_sentiments": [],
            "stock_risks": [],
            "etf_factsheets": [],
            "etf_holdings": [],
            "etf_risks": [],
            "crypto_theses": [],
            "crypto_risks": [],
            "as_of": "2025-01-01",
            "extra_field": "should_cause_issues",
        }

        # Test OFF mode - should ignore validation errors
        manager.set_strictness_mode(ValidationMode.OFF)
        result_off = manager.validate_reporter_input(invalid_input)
        assert result_off.is_valid is True

        # Test WARN mode - should warn but continue
        manager.set_strictness_mode(ValidationMode.WARN)
        result_warn = manager.validate_reporter_input(invalid_input)
        assert result_warn.is_valid is True
        assert result_warn.has_warnings is True

        # Test ERROR mode - should fail
        manager.set_strictness_mode(ValidationMode.ERROR)
        result_error = manager.validate_reporter_input(invalid_input)
        assert result_error.is_valid is False
        assert result_error.has_errors is True

    def test_should_validate_standardized_contract_keys_in_reporter_input(self):
        # Arrange
        manager = ValidationManager()
        manager.set_strictness_mode(ValidationMode.ERROR)

        # Input with correct contract keys but using old naming
        input_with_old_keys = {
            "schema_version": 1,
            "ten_k_insights": [],
            "market_sentiment": [],  # Should be stock_sentiments
            "risk_score_standardized": [],  # Should be stock_risks, etf_risks, crypto_risks
            "etf_factsheets": [],
            "etf_holdings": [],
            "crypto_theses": [],
            "as_of": "2025-01-01",
        }

        # Act
        result = manager.validate_reporter_input(input_with_old_keys)

        # Assert
        assert result.is_valid is False
        assert result.has_errors is True
        # Should fail contract validation for missing required keys

    def test_should_validate_date_field_formats(self):
        # Arrange
        manager = ValidationManager()
        manager.set_strictness_mode(ValidationMode.ERROR)

        # Test various date formats
        test_cases = [
            ("2025-01-01", True),  # ISO format - should work
            ("01/01/2025", False),  # US format - should fail
            ("2025-13-01", False),  # Invalid month - should fail
            ("not_a_date", False),  # Invalid format - should fail
        ]

        for date_value, should_be_valid in test_cases:
            input_data = {
                "schema_version": 1,
                "ten_k_insights": [],
                "stock_sentiments": [],
                "stock_risks": [],
                "etf_factsheets": [],
                "etf_holdings": [],
                "etf_risks": [],
                "crypto_theses": [],
                "crypto_risks": [],
                "as_of": date_value,
            }

            # Act
            result = manager.validate_reporter_input(input_data)

            # Assert
            if should_be_valid:
                assert result.is_valid is True, f"Date {date_value} should be valid"
            else:
                assert result.is_valid is False, f"Date {date_value} should be invalid"

    def test_should_validate_schema_version_field(self):
        # Arrange
        manager = ValidationManager()
        manager.set_strictness_mode(ValidationMode.ERROR)

        # Test with missing schema_version (should use default)
        input_without_version = {
            "ten_k_insights": [],
            "stock_sentiments": [],
            "stock_risks": [],
            "etf_factsheets": [],
            "etf_holdings": [],
            "etf_risks": [],
            "crypto_theses": [],
            "crypto_risks": [],
            "as_of": "2025-01-01",
        }

        # Act
        result = manager.validate_reporter_input(input_without_version)

        # Assert
        assert result.is_valid is True
        assert result.sanitized_data["schema_version"] == 1  # Should use default

        # Test with invalid schema_version type
        input_with_invalid_version = {
            "schema_version": "not_an_int",
            "ten_k_insights": [],
            "stock_sentiments": [],
            "stock_risks": [],
            "etf_factsheets": [],
            "etf_holdings": [],
            "etf_risks": [],
            "crypto_theses": [],
            "crypto_risks": [],
            "as_of": "2025-01-01",
        }

        # Act
        result = manager.validate_reporter_input(input_with_invalid_version)

        # Assert
        assert result.is_valid is False
        assert result.has_errors is True
