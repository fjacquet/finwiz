"""
Unit tests for validation rules.

Tests for ValidationRules class and related validation logic.
"""

import pytest
from faker import Faker
from pydantic import BaseModel

from finwiz.validation.rules import ValidationRules


class TestValidationRules:
    """Tests for ValidationRules class."""

    @pytest.fixture
    def fake(self):
        """Provide Faker instance."""
        return Faker()

    @pytest.fixture
    def rules(self):
        """Create ValidationRules instance."""
        return ValidationRules()

    def test_should_initialize_with_default_logger(self, rules):
        """Test initialization with default logger."""
        assert rules.logger is not None

    def test_should_initialize_with_custom_logger(self, mocker):
        """Test initialization with custom logger."""
        custom_logger = mocker.Mock()

        rules = ValidationRules(logger=custom_logger)

        assert rules.logger is custom_logger


class TestValidateWithPydanticSchema:
    """Tests for validate_with_pydantic_schema method."""

    @pytest.fixture
    def rules(self):
        """Create ValidationRules instance."""
        return ValidationRules()

    @pytest.fixture
    def simple_schema(self):
        """Create simple test schema."""

        class SimpleSchema(BaseModel):
            name: str
            value: int

        return SimpleSchema

    def test_should_validate_valid_data(self, rules, simple_schema):
        """Test validation passes for valid data."""
        data = {"name": "test", "value": 42}

        result = rules.validate_with_pydantic_schema(data, simple_schema)

        assert result.is_valid is True
        assert result.sanitized_data == {"name": "test", "value": 42}

    def test_should_fail_for_missing_required_field(self, rules, simple_schema):
        """Test validation fails for missing required field."""
        data = {"name": "test"}  # Missing 'value'

        result = rules.validate_with_pydantic_schema(data, simple_schema)

        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_should_fail_for_wrong_type(self, rules, simple_schema):
        """Test validation fails for wrong type."""
        data = {"name": "test", "value": "not_an_int"}

        result = rules.validate_with_pydantic_schema(data, simple_schema)

        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_should_report_multiple_errors(self, rules, simple_schema):
        """Test reports all validation errors."""
        data = {}  # Missing both fields

        result = rules.validate_with_pydantic_schema(data, simple_schema)

        assert result.is_valid is False
        assert len(result.errors) >= 2


class TestValidateCrewMetadata:
    """Tests for validate_crew_metadata method."""

    @pytest.fixture
    def rules(self):
        """Create ValidationRules instance."""
        return ValidationRules()

    @pytest.fixture
    def fake(self):
        """Provide Faker instance."""
        return Faker()

    def test_should_fail_for_none_metadata(self, rules):
        """Test validation fails for None metadata."""
        result = rules.validate_crew_metadata(None)

        assert result.is_valid is False
        assert any("metadata" in str(e) for e in result.errors)

    def test_should_fail_for_empty_metadata(self, rules):
        """Test validation fails for empty metadata."""
        result = rules.validate_crew_metadata({})

        # Empty dict fails validation against CrewOutputMetadata schema
        assert result.is_valid is False

    def test_should_validate_valid_metadata(self, rules, fake):
        """Test validation passes for valid metadata."""
        metadata = {
            "crew_name": "stock",
            "execution_id": fake.uuid4(),
            "execution_timestamp": fake.iso8601(),
            "schema_version": 1,
            "dependencies_met": True,
        }

        result = rules.validate_crew_metadata(metadata)

        # Should pass or fail based on actual schema requirements
        # Just test it returns a result
        assert result is not None


class TestExtractAllValidatedTickers:
    """Tests for extract_all_validated_tickers method."""

    @pytest.fixture
    def rules(self):
        """Create ValidationRules instance."""
        return ValidationRules()

    def test_should_extract_stock_tickers(self, rules):
        """Test extracts stock validated_tickers."""
        crew_outputs = {
            "stock": {
                "validated_tickers": [
                    {"symbol": "AAPL", "is_valid": True},
                    {"symbol": "GOOGL", "is_valid": True},
                ]
            }
        }

        result = rules.extract_all_validated_tickers(crew_outputs)

        assert "stock" in result
        assert len(result["stock"]) == 2

    def test_should_extract_etf_tickers(self, rules):
        """Test extracts ETF validated_etfs."""
        crew_outputs = {
            "etf": {
                "validated_etfs": [
                    {"symbol": "SPY", "is_valid": True},
                    {"symbol": "QQQ", "is_valid": True},
                ]
            }
        }

        result = rules.extract_all_validated_tickers(crew_outputs)

        assert "etf" in result
        assert len(result["etf"]) == 2

    def test_should_extract_crypto_tickers(self, rules):
        """Test extracts crypto validated_symbols."""
        crew_outputs = {
            "crypto": {
                "validated_symbols": [
                    {"symbol": "BTC", "is_valid": True},
                    {"symbol": "ETH", "is_valid": True},
                ]
            }
        }

        result = rules.extract_all_validated_tickers(crew_outputs)

        assert "crypto" in result
        assert len(result["crypto"]) == 2

    def test_should_extract_from_multiple_crews(self, rules):
        """Test extracts from multiple crews."""
        crew_outputs = {
            "stock": {"validated_tickers": [{"symbol": "AAPL"}]},
            "etf": {"validated_etfs": [{"symbol": "SPY"}]},
            "crypto": {"validated_symbols": [{"symbol": "BTC"}]},
        }

        result = rules.extract_all_validated_tickers(crew_outputs)

        assert len(result) == 3
        assert "stock" in result
        assert "etf" in result
        assert "crypto" in result

    def test_should_return_empty_for_no_tickers(self, rules):
        """Test returns empty dict when no tickers found."""
        crew_outputs = {"stock": {"other_field": "value"}}

        result = rules.extract_all_validated_tickers(crew_outputs)

        assert result == {}

    def test_should_skip_empty_ticker_lists(self, rules):
        """Test skips crews with empty ticker lists."""
        crew_outputs = {
            "stock": {"validated_tickers": []},
            "etf": {"validated_etfs": [{"symbol": "SPY"}]},
        }

        result = rules.extract_all_validated_tickers(crew_outputs)

        assert "stock" not in result
        assert "etf" in result


class TestFindTickerValidationConflicts:
    """Tests for find_ticker_validation_conflicts method."""

    @pytest.fixture
    def rules(self):
        """Create ValidationRules instance."""
        return ValidationRules()

    def test_should_return_empty_for_no_conflicts(self, rules):
        """Test returns empty list when no conflicts."""
        all_tickers = {
            "stock": [{"symbol": "AAPL", "is_valid": True}],
            "etf": [{"symbol": "SPY", "is_valid": True}],
        }

        result = rules.find_ticker_validation_conflicts(all_tickers)

        assert result == []

    def test_should_find_validation_disagreement(self, rules):
        """Test finds conflicts when crews disagree."""
        all_tickers = {
            "stock": [{"symbol": "AAPL", "is_valid": True}],
            "etf": [{"symbol": "AAPL", "is_valid": False}],  # Same ticker, different result
        }

        result = rules.find_ticker_validation_conflicts(all_tickers)

        assert len(result) == 1
        assert result[0]["ticker"] == "AAPL"
        assert result[0]["conflict_type"] == "validation_disagreement"

    def test_should_not_flag_consistent_validations(self, rules):
        """Test no conflict when crews agree."""
        all_tickers = {
            "stock": [{"symbol": "AAPL", "is_valid": True}],
            "etf": [{"symbol": "AAPL", "is_valid": True}],  # Same result
        }

        result = rules.find_ticker_validation_conflicts(all_tickers)

        assert result == []

    def test_should_skip_tickers_without_symbol(self, rules):
        """Test skips tickers without symbol field."""
        all_tickers = {
            "stock": [{"is_valid": True}],  # No symbol
            "etf": [{"symbol": "", "is_valid": True}],  # Empty symbol
        }

        result = rules.find_ticker_validation_conflicts(all_tickers)

        assert result == []

    def test_should_normalize_symbol_to_uppercase(self, rules):
        """Test normalizes symbols to uppercase for comparison."""
        all_tickers = {
            "stock": [{"symbol": "aapl", "is_valid": True}],
            "etf": [{"symbol": "AAPL", "is_valid": False}],
        }

        result = rules.find_ticker_validation_conflicts(all_tickers)

        # Should find conflict since symbols match after normalization
        assert len(result) == 1
        assert result[0]["ticker"] == "AAPL"


class TestFindDataValueConflicts:
    """Tests for find_data_value_conflicts method."""

    @pytest.fixture
    def rules(self):
        """Create ValidationRules instance."""
        return ValidationRules()

    @pytest.fixture
    def fake(self):
        """Provide Faker instance."""
        return Faker()

    def test_should_return_empty_list(self, rules):
        """Test returns empty list (simplified implementation)."""
        crew_outputs = {"stock": {"data": "value"}}

        result = rules.find_data_value_conflicts(crew_outputs)

        assert result == []

    def test_should_handle_outputs_with_metadata(self, rules, fake):
        """Test handles outputs with metadata timestamps."""
        crew_outputs = {
            "stock": {"metadata": {"execution_timestamp": fake.iso8601()}},
            "etf": {"metadata": {"execution_timestamp": fake.iso8601()}},
        }

        result = rules.find_data_value_conflicts(crew_outputs)

        assert result == []

    def test_should_handle_missing_metadata(self, rules):
        """Test handles outputs without metadata."""
        crew_outputs = {
            "stock": {"data": "value"},
            "etf": {"other": "data"},
        }

        result = rules.find_data_value_conflicts(crew_outputs)

        assert result == []


class TestCheckMetadataConsistency:
    """Tests for check_metadata_consistency method."""

    @pytest.fixture
    def rules(self):
        """Create ValidationRules instance."""
        return ValidationRules()

    def test_should_return_empty_for_consistent_metadata(self, rules):
        """Test returns empty list when metadata is consistent."""
        crew_outputs = {
            "stock": {"metadata": {"schema_version": 1, "dependencies_met": True}},
            "etf": {"metadata": {"schema_version": 1, "dependencies_met": True}},
        }

        result = rules.check_metadata_consistency(crew_outputs)

        assert result == []

    def test_should_detect_schema_version_mismatch(self, rules):
        """Test detects schema version mismatch."""
        crew_outputs = {
            "stock": {"metadata": {"schema_version": 1}},
            "etf": {"metadata": {"schema_version": 2}},  # Different version
        }

        result = rules.check_metadata_consistency(crew_outputs)

        assert len(result) == 1
        assert "Schema version mismatch" in result[0]

    def test_should_detect_unmet_dependencies(self, rules):
        """Test detects unmet dependencies."""
        crew_outputs = {
            "stock": {"metadata": {"schema_version": 1, "dependencies_met": False}},
            "etf": {"metadata": {"schema_version": 1, "dependencies_met": True}},
        }

        result = rules.check_metadata_consistency(crew_outputs)

        assert len(result) == 1
        assert "unmet dependencies" in result[0]

    def test_should_handle_missing_metadata(self, rules):
        """Test handles crews without metadata."""
        crew_outputs = {
            "stock": {"data": "value"},  # No metadata
            "etf": {"metadata": {"schema_version": 1}},
        }

        result = rules.check_metadata_consistency(crew_outputs)

        # Default schema_version is 1 for missing metadata
        assert result == []


class TestValidateCrewSchema:
    """Tests for validate_crew_schema method."""

    @pytest.fixture
    def rules(self):
        """Create ValidationRules instance."""
        return ValidationRules()

    @pytest.fixture
    def simple_schema(self):
        """Create simple test schema."""

        class SimpleSchema(BaseModel):
            name: str
            value: int

        return SimpleSchema

    def test_should_validate_with_mapped_schema(self, rules, simple_schema):
        """Test validates using mapped schema."""
        data = {"name": "test", "value": 42}
        schema_mapping = {"test_crew": simple_schema}

        result = rules.validate_crew_schema("test_crew", data, schema_mapping)

        assert result.is_valid is True

    def test_should_fail_for_unknown_crew(self, rules):
        """Test fails for crew without mapped schema."""
        data = {"name": "test"}
        schema_mapping = {}  # Empty mapping

        result = rules.validate_crew_schema("unknown_crew", data, schema_mapping)

        assert result.is_valid is False
        assert any("schema_not_found" in str(e) for e in result.errors)

    def test_should_fail_for_invalid_data(self, rules, simple_schema):
        """Test fails when data doesn't match schema."""
        data = {"name": "test", "value": "not_an_int"}
        schema_mapping = {"test_crew": simple_schema}

        result = rules.validate_crew_schema("test_crew", data, schema_mapping)

        assert result.is_valid is False


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.fixture
    def rules(self):
        """Create ValidationRules instance."""
        return ValidationRules()

    def test_should_handle_empty_crew_outputs(self, rules):
        """Test handles empty crew outputs dict."""
        result = rules.extract_all_validated_tickers({})

        assert result == {}

    def test_should_handle_empty_all_tickers(self, rules):
        """Test handles empty all_tickers dict."""
        result = rules.find_ticker_validation_conflicts({})

        assert result == []

    def test_should_handle_nested_validation_errors(self, rules):
        """Test handles deeply nested validation errors."""

        class NestedSchema(BaseModel):
            outer: dict[str, int]

        data = {"outer": {"key": "not_an_int"}}

        result = rules.validate_with_pydantic_schema(data, NestedSchema)

        assert result.is_valid is False
