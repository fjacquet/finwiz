"""
Unit tests for ValidationErrorRecovery class.

Tests validation error analysis, data repair suggestions, and recovery recommendations
with fully mocked validation scenarios.
"""

from datetime import datetime

import pytest
from pydantic import BaseModel, Field, ValidationError

from finwiz.integration.validation_error_recovery import (
    DataRepairSuggestion,
    ValidationErrorAnalysis,
    ValidationErrorRecovery,
    ValidationErrorReport,
)


# Test models for validation scenarios
class MockMetadata(BaseModel):
    crew_name: str = Field(..., min_length=1)
    execution_timestamp: datetime
    schema_version: int = Field(..., ge=1)
    is_valid: bool


class MockCrewOutput(BaseModel):
    metadata: MockMetadata
    validated_tickers: list = Field(default_factory=list)
    risk_score: int = Field(..., ge=1, le=10)
    confidence: float = Field(..., ge=0.0, le=1.0)


class TestValidationErrorRecovery:
    """Test suite for ValidationErrorRecovery class."""

    @pytest.fixture
    def recovery_system(self):
        """Create ValidationErrorRecovery instance."""
        return ValidationErrorRecovery()

    def test_should_initialize_error_patterns_and_repair_strategies(self, recovery_system):
        """Test that recovery system initializes with error patterns and repair strategies."""
        # Check error patterns are initialized
        assert len(recovery_system.error_patterns) > 0
        assert "missing_field" in recovery_system.error_patterns
        assert "type_mismatch" in recovery_system.error_patterns
        assert "format_error" in recovery_system.error_patterns

        # Check repair strategies are initialized
        assert len(recovery_system.repair_strategies) > 0
        assert "missing_field" in recovery_system.repair_strategies
        assert "type_mismatch" in recovery_system.repair_strategies

        # Check default values are initialized
        assert len(recovery_system.default_values) > 0
        assert "str" in recovery_system.default_values
        assert "int" in recovery_system.default_values

    def test_should_categorize_missing_field_error_correctly(self, recovery_system):
        """Test categorization of missing field validation errors."""
        error_messages = ["field required", "missing required field", "none is not an allowed value", "field crew_name is required"]

        for message in error_messages:
            error_type = recovery_system._categorize_error(message)
            assert error_type == "missing_field"

    def test_should_categorize_type_mismatch_error_correctly(self, recovery_system):
        """Test categorization of type mismatch validation errors."""
        error_messages = [
            "value is not a valid integer",
            "str type expected",
            "int type expected",
            "float type expected",
            "bool type expected",
        ]

        for message in error_messages:
            error_type = recovery_system._categorize_error(message)
            assert error_type == "type_mismatch"

    def test_should_categorize_format_error_correctly(self, recovery_system):
        """Test categorization of format validation errors."""
        error_messages = [
            "string does not match expected pattern",
            "invalid url format",
            "does not match regex",
            "invalid datetime format",
        ]

        for message in error_messages:
            error_type = recovery_system._categorize_error(message)
            assert error_type == "format_error"

    def test_should_determine_critical_severity_for_important_fields(self, recovery_system):
        """Test that critical fields get critical severity."""
        critical_test_cases = [
            ("metadata.crew_name", "missing_field", "field required"),
            ("execution_timestamp", "missing_field", "field required"),
            ("validation_status", "type_mismatch", "dict type expected"),
        ]

        for field_path, error_type, error_message in critical_test_cases:
            severity = recovery_system._determine_error_severity(error_type, field_path, error_message)
            assert severity == "critical"

    def test_should_determine_appropriate_severity_for_different_fields(self, recovery_system):
        """Test that different fields get appropriate severity levels."""
        test_cases = [
            ("some_field", "missing_field", "field required", ["critical", "high", "medium", "low"]),
            ("another_field", "type_mismatch", "int type expected", ["critical", "high", "medium", "low"]),
            ("format_field", "format_error", "invalid format", ["critical", "high", "medium", "low"]),
        ]

        for field_path, error_type, error_message, valid_severities in test_cases:
            severity = recovery_system._determine_error_severity(error_type, field_path, error_message)
            assert severity in valid_severities

    def test_should_assess_missing_field_as_repairable(self, recovery_system):
        """Test that missing field errors are assessed as repairable."""
        error_info = {"msg": "field required", "loc": ["crew_name"]}

        is_repairable, confidence = recovery_system._assess_repairability("missing_field", error_info)

        assert is_repairable is True
        assert confidence > 0.5

    def test_should_assess_schema_error_as_highly_repairable(self, recovery_system):
        """Test that schema errors are assessed as highly repairable."""
        error_info = {"msg": "extra fields not permitted", "loc": ["extra_field"]}

        is_repairable, confidence = recovery_system._assess_repairability("schema_error", error_info)

        assert is_repairable is True
        assert confidence > 0.8

    def test_should_generate_appropriate_suggested_fix_for_missing_field(self, recovery_system):
        """Test generation of suggested fixes for missing field errors."""
        error_info = {"msg": "field required", "loc": ["metadata", "crew_name"]}

        suggested_fix = recovery_system._generate_suggested_fix("missing_field", error_info, None)

        assert suggested_fix is not None
        assert "missing field" in suggested_fix.lower()
        assert "metadata.crew_name" in suggested_fix

    def test_should_generate_appropriate_suggested_fix_for_type_mismatch(self, recovery_system):
        """Test generation of suggested fixes for type mismatch errors."""
        error_info = {"msg": "int type expected", "loc": ["risk_score"], "input": "5.5"}

        suggested_fix = recovery_system._generate_suggested_fix("type_mismatch", error_info, None)

        assert suggested_fix is not None
        assert "convert" in suggested_fix.lower()
        assert "5.5" in suggested_fix
        assert "integer" in suggested_fix

    def test_should_analyze_validation_error_comprehensively(self, recovery_system):
        """Test comprehensive analysis of a validation error."""
        # Create a validation error
        try:
            MockCrewOutput(
                metadata={
                    "crew_name": "",  # Too short
                    "execution_timestamp": "invalid_date",
                    "schema_version": 0,  # Below minimum
                    "is_valid": "not_a_bool",
                },
                risk_score=15,  # Above maximum
                confidence=1.5,  # Above maximum
            )
        except ValidationError as e:
            analysis = recovery_system.analyze_validation_error(e)

            assert isinstance(analysis, ValidationErrorAnalysis)
            # The error type should be recognized or be unknown_error
            assert analysis.error_type in list(recovery_system.error_patterns.keys()) + ["unknown_error"]
            assert analysis.severity in ["critical", "high", "medium", "low"]
            assert isinstance(analysis.is_repairable, bool)
            assert 0.0 <= analysis.repair_confidence <= 1.0

    def test_should_get_nested_value_correctly(self, recovery_system):
        """Test getting nested values from dictionaries."""
        test_data = {"metadata": {"crew_name": "test_crew", "nested": {"deep_value": 42}}, "list_field": [1, 2, 3]}

        # Test simple nested access
        assert recovery_system._get_nested_value(test_data, "metadata.crew_name") == "test_crew"

        # Test deep nested access
        assert recovery_system._get_nested_value(test_data, "metadata.nested.deep_value") == 42

        # Test list access
        assert recovery_system._get_nested_value(test_data, "list_field.1") == 2

        # Test non-existent path
        assert recovery_system._get_nested_value(test_data, "nonexistent.path") is None

    def test_should_get_appropriate_default_values_for_fields(self, recovery_system):
        """Test getting appropriate default values for different field types."""
        test_cases = [
            ("crew_name", "unknown"),
            ("schema_version", 1),
            ("is_valid", False),
            ("validation_errors", []),
            ("age_hours", 999.0),
            ("some_timestamp", str),  # Should be datetime string
            ("some_count", 0),
            ("some_list", []),
            ("some_status", "unknown"),
        ]

        for field_path, expected_type in test_cases:
            default_value = recovery_system._get_default_value_for_field(field_path)

            if expected_type is str:
                assert isinstance(default_value, str)
            else:
                assert default_value == expected_type

    def test_should_convert_value_types_correctly(self, recovery_system):
        """Test type conversion for different value types."""
        # String conversion
        assert recovery_system._convert_value_type(123, "str type expected") == "123"

        # Integer conversion
        assert recovery_system._convert_value_type("42", "int type expected") == 42
        assert recovery_system._convert_value_type("42.7", "int type expected") == 42

        # Float conversion
        assert recovery_system._convert_value_type("3.14", "float type expected") == 3.14

        # Boolean conversion
        assert recovery_system._convert_value_type("true", "bool type expected") is True
        assert recovery_system._convert_value_type("false", "bool type expected") is False
        assert recovery_system._convert_value_type(1, "bool type expected") is True

        # List conversion
        assert recovery_system._convert_value_type(None, "list type expected") == []
        assert recovery_system._convert_value_type("item", "list type expected") == ["item"]

        # Dict conversion
        assert recovery_system._convert_value_type(None, "dict type expected") == {}

    def test_should_adjust_values_for_constraints_correctly(self, recovery_system):
        """Test value adjustment for constraint violations."""
        # Greater than constraint
        adjusted = recovery_system._adjust_value_for_constraints(5, "ensure this value is greater than 10")
        assert adjusted > 10

        # Less than constraint
        adjusted = recovery_system._adjust_value_for_constraints(15, "ensure this value is less than 10")
        assert adjusted < 10

        # String length - at least
        adjusted = recovery_system._adjust_value_for_constraints("hi", "ensure this value has at least 5 characters")
        assert len(adjusted) >= 5

        # String length - at most
        adjusted = recovery_system._adjust_value_for_constraints("very long string", "ensure this value has at most 5 characters")
        assert len(adjusted) <= 5

    def test_should_create_repair_suggestion_for_missing_field(self, recovery_system):
        """Test creation of repair suggestions for missing fields."""
        analysis = ValidationErrorAnalysis(
            error_type="missing_field",
            field_path="metadata.crew_name",
            error_message="field required",
            severity="critical",
            is_repairable=True,
            repair_confidence=0.8,
            suggested_fix="Add missing field",
            context={},
        )

        original_data = {"metadata": {}}

        suggestion = recovery_system._create_repair_suggestion(analysis, original_data)

        assert suggestion is not None
        assert suggestion.repair_type == "set_default"
        assert suggestion.field_path == "metadata.crew_name"
        assert suggestion.current_value is None
        assert suggestion.suggested_value == "unknown"
        assert suggestion.confidence == 0.8

    def test_should_create_repair_suggestion_for_type_mismatch(self, recovery_system):
        """Test creation of repair suggestions for type mismatches."""
        analysis = ValidationErrorAnalysis(
            error_type="type_mismatch",
            field_path="risk_score",
            error_message="int type expected",
            severity="medium",
            is_repairable=True,
            repair_confidence=0.7,
            suggested_fix="Convert to integer",
            context={},
        )

        original_data = {"risk_score": "5"}

        suggestion = recovery_system._create_repair_suggestion(analysis, original_data)

        assert suggestion is not None
        assert suggestion.repair_type == "convert_type"
        assert suggestion.field_path == "risk_score"
        assert suggestion.current_value == "5"
        assert suggestion.suggested_value == 5
        assert suggestion.confidence == 0.7

    def test_should_suggest_data_repairs_sorted_by_confidence(self, recovery_system):
        """Test that data repair suggestions are sorted by confidence."""
        error_analyses = [
            ValidationErrorAnalysis(
                error_type="missing_field",
                field_path="field1",
                error_message="field required",
                severity="medium",
                is_repairable=True,
                repair_confidence=0.5,
                suggested_fix="Add field1",
                context={},
            ),
            ValidationErrorAnalysis(
                error_type="schema_error",
                field_path="field2",
                error_message="extra field",
                severity="low",
                is_repairable=True,
                repair_confidence=0.9,
                suggested_fix="Remove field2",
                context={},
            ),
            ValidationErrorAnalysis(
                error_type="type_mismatch",
                field_path="field3",
                error_message="int expected",
                severity="medium",
                is_repairable=True,
                repair_confidence=0.7,
                suggested_fix="Convert field3",
                context={},
            ),
        ]

        original_data = {"field1": None, "field2": "extra", "field3": "123"}

        suggestions = recovery_system.suggest_data_repairs(error_analyses, original_data)

        # Should be sorted by confidence (highest first)
        assert len(suggestions) == 3
        assert suggestions[0].confidence == 0.9  # schema_error
        assert suggestions[1].confidence == 0.7  # type_mismatch
        assert suggestions[2].confidence == 0.5  # missing_field

    def test_should_generate_comprehensive_error_report(self, recovery_system):
        """Test generation of comprehensive validation error report."""
        # Create validation errors
        validation_errors = []
        try:
            MockCrewOutput(
                metadata={
                    "crew_name": "",  # Too short - critical
                    "execution_timestamp": datetime.now(),
                    "schema_version": 0,  # Below minimum - high
                    "is_valid": True,
                },
                risk_score=15,  # Above maximum - medium
                confidence=1.5,  # Above maximum - medium
            )
        except ValidationError as e:
            validation_errors.append(e)

        original_data = {
            "metadata": {"crew_name": "", "execution_timestamp": datetime.now().isoformat(), "schema_version": 0, "is_valid": True},
            "risk_score": 15,
            "confidence": 1.5,
        }

        report = recovery_system.generate_error_report(validation_errors, original_data)

        assert isinstance(report, ValidationErrorReport)
        assert report.total_errors > 0
        assert len(report.error_analyses) == report.total_errors
        assert len(report.repair_suggestions) >= 0
        assert len(report.recovery_recommendations) > 0
        assert report.overall_repairability in ["fully_repairable", "partially_repairable", "not_repairable"]
        assert isinstance(report.report_timestamp, datetime)

    def test_should_generate_appropriate_recovery_recommendations(self, recovery_system):
        """Test generation of appropriate recovery recommendations."""
        error_analyses = [
            ValidationErrorAnalysis(
                error_type="missing_field",
                field_path="metadata.crew_name",
                error_message="field required",
                severity="critical",
                is_repairable=True,
                repair_confidence=0.8,
                suggested_fix="Add field",
                context={},
            ),
            ValidationErrorAnalysis(
                error_type="schema_error",
                field_path="extra_field",
                error_message="extra field not permitted",
                severity="low",
                is_repairable=True,
                repair_confidence=0.9,
                suggested_fix="Remove field",
                context={},
            ),
        ]

        repair_suggestions = [
            DataRepairSuggestion(
                repair_type="set_default",
                field_path="metadata.crew_name",
                current_value=None,
                suggested_value="unknown",
                repair_description="Set default value",
                confidence=0.8,
                side_effects=[],
                validation_after_repair=True,
            ),
            DataRepairSuggestion(
                repair_type="remove_field",
                field_path="extra_field",
                current_value="extra",
                suggested_value=None,
                repair_description="Remove extra field",
                confidence=0.9,
                side_effects=[],
                validation_after_repair=True,
            ),
        ]

        recommendations = recovery_system._generate_recovery_recommendations(error_analyses, repair_suggestions)

        assert len(recommendations) > 0

        # Should mention critical errors
        critical_mentioned = any("critical" in rec.lower() for rec in recommendations)
        assert critical_mentioned

        # Should mention high-confidence repairs
        high_confidence_mentioned = any("high-confidence" in rec.lower() for rec in recommendations)
        assert high_confidence_mentioned

    def test_should_attempt_data_repair_successfully(self, recovery_system):
        """Test successful data repair using repair suggestions."""
        corrupted_data = {
            "metadata": {"execution_timestamp": datetime.now().isoformat(), "schema_version": 1, "is_valid": True},
            "risk_score": "5",  # Wrong type
            "confidence": 0.8,
        }

        repair_suggestions = [
            DataRepairSuggestion(
                repair_type="set_default",
                field_path="metadata.crew_name",
                current_value=None,
                suggested_value="unknown",
                repair_description="Set missing crew_name",
                confidence=0.8,
                side_effects=[],
                validation_after_repair=True,
            ),
            DataRepairSuggestion(
                repair_type="convert_type",
                field_path="risk_score",
                current_value="5",
                suggested_value=5,
                repair_description="Convert risk_score to integer",
                confidence=0.7,
                side_effects=[],
                validation_after_repair=True,
            ),
        ]

        repaired_data = recovery_system.attempt_data_repair(corrupted_data, repair_suggestions)

        assert repaired_data is not None
        assert repaired_data["metadata"]["crew_name"] == "unknown"
        assert repaired_data["risk_score"] == 5
        assert isinstance(repaired_data["risk_score"], int)

    def test_should_skip_low_confidence_repairs(self, recovery_system):
        """Test that low-confidence repairs are skipped during data repair."""
        corrupted_data = {"field1": "value1"}

        repair_suggestions = [
            DataRepairSuggestion(
                repair_type="set_default",
                field_path="field2",
                current_value=None,
                suggested_value="default",
                repair_description="Low confidence repair",
                confidence=0.3,  # Below threshold
                side_effects=[],
                validation_after_repair=True,
            )
        ]

        repaired_data = recovery_system.attempt_data_repair(corrupted_data, repair_suggestions)

        assert repaired_data is not None
        # Low confidence repair should be skipped
        assert "field2" not in repaired_data

    def test_should_set_and_remove_nested_values_correctly(self, recovery_system):
        """Test setting and removing nested values in dictionaries."""
        test_data = {"level1": {"level2": {"level3": "value"}}}

        # Test setting nested value
        recovery_system._set_nested_value(test_data, ["level1", "level2", "new_field"], "new_value")
        assert test_data["level1"]["level2"]["new_field"] == "new_value"

        # Test removing nested value
        recovery_system._remove_nested_field(test_data, ["level1", "level2", "level3"])
        assert "level3" not in test_data["level1"]["level2"]

        # Test removing non-existent field (should not crash)
        recovery_system._remove_nested_field(test_data, ["nonexistent", "field"])
        # Should not raise an exception

    def test_should_handle_unknown_error_types_gracefully(self, recovery_system):
        """Test that unknown error types are handled gracefully."""
        unknown_error_message = "completely unknown validation error"

        error_type = recovery_system._categorize_error(unknown_error_message)
        assert error_type == "unknown_error"

        # Should not be repairable
        is_repairable, confidence = recovery_system._assess_repairability("unknown_error", {})
        assert is_repairable is False
        assert confidence == 0.0
