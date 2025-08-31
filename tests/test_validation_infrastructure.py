"""Tests for core validation infrastructure."""

from finwiz.validation import (
    SchemaRegistry,
    ValidationManager,
    ValidationMode,
    ValidationResult,
)


class TestValidationResult:
    """Test ValidationResult functionality."""

    def test_should_create_empty_result_as_valid(self):
        # Arrange & Act
        result = ValidationResult(is_valid=True)

        # Assert
        assert result.is_valid is True
        assert result.has_errors is False
        assert result.has_warnings is False
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_should_add_error_and_mark_invalid(self):
        # Arrange
        result = ValidationResult(is_valid=True)

        # Act
        result.add_error("field.path", "type_error", "Test error message", "invalid_value")

        # Assert
        assert result.is_valid is False
        assert result.has_errors is True
        assert len(result.errors) == 1
        assert result.errors[0].field_path == "field.path"
        assert result.errors[0].error_type == "type_error"
        assert result.errors[0].message == "Test error message"
        assert result.errors[0].input_value == "invalid_value"

    def test_should_add_warning_without_affecting_validity(self):
        # Arrange
        result = ValidationResult(is_valid=True)

        # Act
        result.add_warning("field.path", "Test warning", "warning_value")

        # Assert
        assert result.is_valid is True
        assert result.has_warnings is True
        assert len(result.warnings) == 1
        assert result.warnings[0].field_path == "field.path"
        assert result.warnings[0].message == "Test warning"
        assert result.warnings[0].input_value == "warning_value"


class TestSchemaRegistry:
    """Test SchemaRegistry functionality."""

    def test_should_register_and_retrieve_schema(self):
        # Arrange
        from finwiz.schemas.validation import ValidatedTicker

        registry = SchemaRegistry()

        # Act
        registry.register_schema("test_schema", ValidatedTicker)
        retrieved = registry.get_schema("test_schema")

        # Assert
        assert retrieved is ValidatedTicker

    def test_should_register_and_retrieve_crew_schema(self):
        # Arrange
        from finwiz.schemas.common import RiskAssessmentStandardized

        registry = SchemaRegistry()

        # Act
        registry.register_crew_schema("test_crew", "risk", RiskAssessmentStandardized)
        retrieved = registry.get_crew_schema("test_crew", "risk")

        # Assert
        assert retrieved is RiskAssessmentStandardized

    def test_should_return_none_for_unknown_schema(self):
        # Arrange
        registry = SchemaRegistry()

        # Act & Assert
        assert registry.get_schema("unknown_schema") is None
        assert registry.get_crew_schema("unknown_crew", "unknown_type") is None

    def test_should_list_registered_schemas(self):
        # Arrange
        from finwiz.schemas.validation import ValidatedTicker

        registry = SchemaRegistry()
        registry.register_schema("test_schema", ValidatedTicker)

        # Act
        schemas = registry.list_schemas()

        # Assert
        assert "test_schema" in schemas
        assert "ValidatedTicker" in schemas  # From default initialization


class TestValidationManager:
    """Test ValidationManager functionality."""

    def test_should_validate_valid_reporter_input(self):
        # Arrange
        manager = ValidationManager()
        valid_data = {
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
        result = manager.validate_reporter_input(valid_data)

        # Assert
        assert result.is_valid is True
        assert result.has_errors is False
        assert result.sanitized_data is not None

    def test_should_reject_invalid_reporter_input_in_error_mode(self):
        # Arrange
        manager = ValidationManager()
        manager.set_strictness_mode(ValidationMode.ERROR)
        invalid_data = {
            "schema_version": "invalid",  # Should be int
            "unknown_field": "should_be_rejected",  # extra='forbid'
        }

        # Act
        result = manager.validate_reporter_input(invalid_data)

        # Assert
        assert result.is_valid is False
        assert result.has_errors is True
        assert len(result.errors) > 0

    def test_should_warn_for_invalid_data_in_warn_mode(self):
        # Arrange
        manager = ValidationManager()
        manager.set_strictness_mode(ValidationMode.WARN)
        invalid_data = {"schema_version": "invalid", "unknown_field": "should_warn"}

        # Act
        result = manager.validate_reporter_input(invalid_data)

        # Assert
        assert result.is_valid is True  # Continues processing in warn mode
        assert result.has_warnings is True
        assert result.sanitized_data is not None

    def test_should_ignore_validation_in_off_mode(self):
        # Arrange
        manager = ValidationManager()
        manager.set_strictness_mode(ValidationMode.OFF)
        invalid_data = {"completely": "invalid", "data": "structure"}

        # Act
        result = manager.validate_reporter_input(invalid_data)

        # Assert
        assert result.is_valid is True
        assert result.has_errors is False
        assert result.sanitized_data == invalid_data

    def test_should_read_validation_mode_from_environment(self, mocker):
        # Arrange & Act
        mocker.patch.dict("os.environ", {"VALIDATION_STRICTNESS": "error"})
        manager = ValidationManager()

        # Assert
        assert manager.get_strictness_mode() == ValidationMode.ERROR

    def test_should_validate_crew_output_with_registered_schema(self):
        # Arrange
        manager = ValidationManager()
        # Use existing registered schema
        valid_risk_data = {
            "scale": "0_5",
            "score": 2.5,
            "level": "Medium",
            "risk_factors": ["Market volatility", "Regulatory risk"],
        }

        # Act
        result = manager.validate_crew_output(valid_risk_data, "stock", "risk_assessment")

        # Assert
        assert result.is_valid is True
        assert result.sanitized_data is not None

    def test_should_warn_for_unknown_crew_schema(self):
        # Arrange
        manager = ValidationManager()
        manager.set_strictness_mode(ValidationMode.WARN)

        # Act
        result = manager.validate_crew_output({}, "unknown_crew", "unknown_type")

        # Assert
        assert result.is_valid is True
        assert result.has_warnings is True
        assert any("No schema registered" in w.message for w in result.warnings)
