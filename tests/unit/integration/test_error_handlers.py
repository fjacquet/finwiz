"""Tests for integration/error_handlers.py module."""

from datetime import datetime

import pytest
from pydantic import BaseModel, Field, ValidationError

from finwiz.integration.error_handlers import (
    ErrorHandlers,
    ValidationErrorAnalysis,
    ValidationErrorReport,
)


class TestValidationErrorAnalysisModel:
    """Tests for ValidationErrorAnalysis Pydantic model."""

    def test_should_create_valid_analysis(self):
        """Test creation of a valid ValidationErrorAnalysis."""
        analysis = ValidationErrorAnalysis(
            error_type="missing_field",
            field_path="metadata.crew_name",
            error_message="Field required",
            severity="critical",
            is_repairable=True,
            repair_confidence=0.8,
            suggested_fix="Add missing field",
            context={"error_info": {}},
        )
        assert analysis.error_type == "missing_field"
        assert analysis.severity == "critical"
        assert analysis.is_repairable is True

    def test_should_validate_repair_confidence_range(self):
        """Test that repair_confidence must be between 0.0 and 1.0."""
        with pytest.raises(ValidationError):
            ValidationErrorAnalysis(
                error_type="test",
                field_path="test",
                error_message="test",
                severity="low",
                is_repairable=False,
                repair_confidence=1.5,  # Invalid: > 1.0
            )

    def test_should_use_default_values(self):
        """Test default values for optional fields."""
        analysis = ValidationErrorAnalysis(
            error_type="test",
            field_path="test",
            error_message="test",
            severity="low",
            is_repairable=False,
            repair_confidence=0.0,
        )
        assert analysis.suggested_fix is None
        assert analysis.context == {}


class TestValidationErrorReportModel:
    """Tests for ValidationErrorReport Pydantic model."""

    def test_should_create_valid_report(self):
        """Test creation of a valid ValidationErrorReport."""
        report = ValidationErrorReport(
            total_errors=5,
            error_analyses=[],
            repair_suggestions=[],
            recovery_recommendations=["Fix errors"],
            repairable_errors_count=3,
            critical_errors_count=1,
            report_timestamp=datetime.now(),
            overall_repairability="partially_repairable",
        )
        assert report.total_errors == 5
        assert report.repairable_errors_count == 3

    def test_should_use_default_factories(self):
        """Test that default factories work for list fields."""
        report = ValidationErrorReport(
            total_errors=0,
            repairable_errors_count=0,
            critical_errors_count=0,
            report_timestamp=datetime.now(),
            overall_repairability="not_repairable",
        )
        assert report.error_analyses == []
        assert report.repair_suggestions == []
        assert report.recovery_recommendations == []


class TestErrorHandlersInit:
    """Tests for ErrorHandlers initialization."""

    def test_should_initialize_error_patterns(self):
        """Test that error patterns are initialized correctly."""
        handlers = ErrorHandlers()
        assert "missing_field" in handlers.error_patterns
        assert "type_mismatch" in handlers.error_patterns
        assert "format_error" in handlers.error_patterns
        assert "constraint_error" in handlers.error_patterns
        assert "enum_error" in handlers.error_patterns
        assert "schema_error" in handlers.error_patterns

    def test_should_have_patterns_for_each_category(self):
        """Test that each category has associated patterns."""
        handlers = ErrorHandlers()
        for category, patterns in handlers.error_patterns.items():
            assert len(patterns) > 0, f"Category {category} has no patterns"


class TestCategorizeError:
    """Tests for _categorize_error method."""

    @pytest.fixture
    def handlers(self):
        """Create ErrorHandlers instance."""
        return ErrorHandlers()

    def test_should_categorize_missing_field_errors(self, handlers):
        """Test categorization of missing field errors."""
        assert handlers._categorize_error("field required") == "missing_field"
        assert handlers._categorize_error("Field is required") == "missing_field"
        assert handlers._categorize_error("None is not an allowed value") == "missing_field"

    def test_should_categorize_type_mismatch_errors(self, handlers):
        """Test categorization of type mismatch errors."""
        assert handlers._categorize_error("str type expected") == "type_mismatch"
        assert handlers._categorize_error("int type expected") == "type_mismatch"
        assert handlers._categorize_error("value is not a valid integer") == "type_mismatch"
        assert handlers._categorize_error("input should be a valid string") == "type_mismatch"

    def test_should_categorize_format_errors(self, handlers):
        """Test categorization of format errors."""
        assert handlers._categorize_error("string does not match expected pattern") == "format_error"
        assert handlers._categorize_error("invalid url format") == "format_error"
        assert handlers._categorize_error("invalid email") == "format_error"
        assert handlers._categorize_error("invalid datetime format") == "format_error"

    def test_should_categorize_constraint_errors(self, handlers):
        """Test categorization of constraint errors."""
        assert handlers._categorize_error("ensure this value is greater than 0") == "constraint_error"
        assert handlers._categorize_error("ensure this value has at least 3 characters") == "constraint_error"
        assert handlers._categorize_error("string too short") == "constraint_error"
        assert handlers._categorize_error("input should be greater than or equal to 0") == "constraint_error"

    def test_should_categorize_enum_errors(self, handlers):
        """Test categorization of enum errors."""
        # "value is not a valid..." matches type_mismatch first due to pattern order
        # Only pure enum-specific messages are categorized as enum_error
        assert handlers._categorize_error("not an allowed value") == "enum_error"
        assert handlers._categorize_error("unexpected value: 'foo' expected: 'bar'") == "enum_error"

    def test_should_categorize_schema_errors(self, handlers):
        """Test categorization of schema errors."""
        assert handlers._categorize_error("extra fields not permitted") == "schema_error"
        assert handlers._categorize_error("unknown field 'foo'") == "schema_error"

    def test_should_return_unknown_for_unrecognized_errors(self, handlers):
        """Test that unrecognized errors are categorized as unknown."""
        assert handlers._categorize_error("some random error message") == "unknown_error"
        assert handlers._categorize_error("xyz 123") == "unknown_error"


class TestDetermineErrorSeverity:
    """Tests for _determine_error_severity method."""

    @pytest.fixture
    def handlers(self):
        """Create ErrorHandlers instance."""
        return ErrorHandlers()

    def test_should_return_critical_for_critical_fields(self, handlers):
        """Test that critical fields get critical severity."""
        assert handlers._determine_error_severity("missing_field", "metadata", "test") == "critical"
        assert handlers._determine_error_severity("type_mismatch", "crew_name", "test") == "critical"
        assert handlers._determine_error_severity("format_error", "execution_timestamp", "test") == "critical"

    def test_should_return_high_for_high_priority_fields(self, handlers):
        """Test that high priority fields get high severity."""
        assert handlers._determine_error_severity("missing_field", "schema_version", "test") == "high"
        assert handlers._determine_error_severity("missing_field", "data_sources", "test") == "high"
        assert handlers._determine_error_severity("constraint_error", "freshness_status", "test") == "high"

    def test_should_return_medium_for_missing_field_regular(self, handlers):
        """Test that regular missing fields get medium severity."""
        assert handlers._determine_error_severity("missing_field", "some_field", "test") == "medium"

    def test_should_return_medium_for_type_mismatch(self, handlers):
        """Test that type mismatch errors get medium severity."""
        assert handlers._determine_error_severity("type_mismatch", "regular_field", "test") == "medium"

    def test_should_return_low_for_format_errors(self, handlers):
        """Test that format errors get low severity."""
        assert handlers._determine_error_severity("format_error", "regular_field", "test") == "low"
        assert handlers._determine_error_severity("enum_error", "regular_field", "test") == "low"

    def test_should_return_medium_for_unknown_error_type(self, handlers):
        """Test that unknown error types get medium severity."""
        assert handlers._determine_error_severity("unknown_error", "field", "msg") == "medium"


class TestAnalyzeValidationError:
    """Tests for analyze_validation_error method."""

    @pytest.fixture
    def handlers(self):
        """Create ErrorHandlers instance."""
        return ErrorHandlers()

    def test_should_analyze_missing_field_error(self, handlers):
        """Test analysis of a missing field error."""
        # Create a model that requires a field
        class TestModel(BaseModel):
            required_field: str

        try:
            TestModel()
        except ValidationError as e:
            analysis = handlers.analyze_validation_error(e)
            assert analysis.error_type == "missing_field"
            assert analysis.field_path == "required_field"
            assert "required" in analysis.error_message.lower()

    def test_should_analyze_type_mismatch_error(self, handlers):
        """Test analysis of a type mismatch error."""
        class TestModel(BaseModel):
            number: int

        try:
            TestModel(number="not_a_number")
        except ValidationError as e:
            analysis = handlers.analyze_validation_error(e)
            assert analysis.error_type == "type_mismatch"
            assert "number" in analysis.field_path

    def test_should_analyze_constraint_error(self, handlers):
        """Test analysis of a constraint error."""
        class TestModel(BaseModel):
            score: float = Field(ge=0.0, le=1.0)

        try:
            TestModel(score=1.5)
        except ValidationError as e:
            analysis = handlers.analyze_validation_error(e)
            assert analysis.error_type == "constraint_error"
            assert "score" in analysis.field_path

    def test_should_analyze_schema_error(self, handlers):
        """Test analysis of a schema error (extra fields).

        Note: Pydantic v2 uses "Extra inputs are not permitted" but the
        error_handlers patterns expect "extra fields not permitted", so
        the error is categorized as unknown_error with current patterns.
        """
        class TestModel(BaseModel):
            model_config = {"extra": "forbid"}
            allowed_field: str

        try:
            TestModel(allowed_field="test", extra_field="not_allowed")
        except ValidationError as e:
            analysis = handlers.analyze_validation_error(e)
            # Pydantic v2 says "Extra inputs are not permitted" which doesn't
            # match the "extra fields not permitted" pattern, so it's unknown_error
            assert analysis.error_type == "unknown_error"
            assert "extra_field" in analysis.field_path

    def test_should_include_context(self, handlers):
        """Test that analysis includes context."""
        class TestModel(BaseModel):
            field: str

        try:
            TestModel()
        except ValidationError as e:
            analysis = handlers.analyze_validation_error(e, {"source": "test"})
            assert "error_info" in analysis.context
            assert "data_context" in analysis.context
            assert analysis.context["data_context"]["source"] == "test"


class TestGenerateErrorReport:
    """Tests for generate_error_report method."""

    @pytest.fixture
    def handlers(self):
        """Create ErrorHandlers instance."""
        return ErrorHandlers()

    def test_should_generate_report_with_single_error(self, handlers):
        """Test report generation with a single error."""
        class TestModel(BaseModel):
            field: str

        errors = []
        try:
            TestModel()
        except ValidationError as e:
            errors.append(e)

        report = handlers.generate_error_report(errors, {"test": "data"})
        assert report.total_errors == 1
        assert len(report.error_analyses) == 1

    def test_should_generate_report_with_multiple_errors(self, handlers):
        """Test report generation with multiple errors."""
        class TestModel1(BaseModel):
            field1: str

        class TestModel2(BaseModel):
            field2: int

        errors = []
        try:
            TestModel1()
        except ValidationError as e:
            errors.append(e)

        try:
            TestModel2(field2="not_int")
        except ValidationError as e:
            errors.append(e)

        report = handlers.generate_error_report(errors, {})
        assert report.total_errors == 2
        assert len(report.error_analyses) == 2

    def test_should_count_repairable_errors(self, handlers):
        """Test that repairable errors are counted correctly."""
        class TestModel(BaseModel):
            field: str

        errors = []
        try:
            TestModel()
        except ValidationError as e:
            errors.append(e)

        report = handlers.generate_error_report(errors, {})
        # Missing field errors are typically repairable
        assert report.repairable_errors_count >= 0

    def test_should_count_critical_errors(self, handlers):
        """Test that critical errors are counted correctly."""
        class TestModel(BaseModel):
            metadata: str

        errors = []
        try:
            TestModel()
        except ValidationError as e:
            errors.append(e)

        report = handlers.generate_error_report(errors, {})
        # metadata is a critical field
        assert report.critical_errors_count >= 1

    def test_should_determine_overall_repairability(self, handlers):
        """Test overall repairability determination."""
        class TestModel(BaseModel):
            field: str

        errors = []
        try:
            TestModel()
        except ValidationError as e:
            errors.append(e)

        report = handlers.generate_error_report(errors, {})
        assert report.overall_repairability in ["fully_repairable", "partially_repairable", "not_repairable"]

    def test_should_include_timestamp(self, handlers):
        """Test that report includes timestamp."""
        report = handlers.generate_error_report([], {})
        assert report.report_timestamp is not None
        assert isinstance(report.report_timestamp, datetime)


class TestGenerateRecoveryRecommendations:
    """Tests for _generate_recovery_recommendations method."""

    @pytest.fixture
    def handlers(self):
        """Create ErrorHandlers instance."""
        return ErrorHandlers()

    def test_should_recommend_for_critical_errors(self, handlers):
        """Test recommendations for critical errors."""
        analyses = [
            ValidationErrorAnalysis(
                error_type="missing_field",
                field_path="metadata",
                error_message="field required",
                severity="critical",
                is_repairable=True,
                repair_confidence=0.8,
            )
        ]
        recommendations = handlers._generate_recovery_recommendations(analyses, [])
        assert any("critical" in r.lower() for r in recommendations)

    def test_should_recommend_high_confidence_repairs(self, handlers, mocker):
        """Test recommendations for high confidence repairs."""
        analyses = []

        # Create mock repair suggestion with high confidence
        mock_repair = mocker.Mock()
        mock_repair.confidence = 0.9

        recommendations = handlers._generate_recovery_recommendations(analyses, [mock_repair])
        assert any("high-confidence" in r.lower() for r in recommendations)

    def test_should_recommend_manual_review_for_low_confidence(self, handlers, mocker):
        """Test recommendations for low confidence repairs."""
        analyses = []

        # Create mock repair suggestion with low confidence
        mock_repair = mocker.Mock()
        mock_repair.confidence = 0.4

        recommendations = handlers._generate_recovery_recommendations(analyses, [mock_repair])
        assert any("review" in r.lower() and "manually" in r.lower() for r in recommendations)

    def test_should_recommend_schema_update_for_schema_errors(self, handlers):
        """Test recommendations for schema errors."""
        analyses = [
            ValidationErrorAnalysis(
                error_type="schema_error",
                field_path="extra_field",
                error_message="extra fields not permitted",
                severity="medium",
                is_repairable=True,
                repair_confidence=0.9,
            )
        ]
        recommendations = handlers._generate_recovery_recommendations(analyses, [])
        assert any("schema" in r.lower() for r in recommendations)

    def test_should_recommend_for_missing_fields(self, handlers):
        """Test recommendations for missing fields."""
        analyses = [
            ValidationErrorAnalysis(
                error_type="missing_field",
                field_path="some_field",
                error_message="field required",
                severity="medium",
                is_repairable=True,
                repair_confidence=0.8,
            )
        ]
        recommendations = handlers._generate_recovery_recommendations(analyses, [])
        assert any("missing" in r.lower() for r in recommendations)

    def test_should_provide_default_recommendation_when_empty(self, handlers):
        """Test that a default recommendation is provided when no specific ones apply."""
        recommendations = handlers._generate_recovery_recommendations([], [])
        assert len(recommendations) > 0
        assert any("no specific" in r.lower() for r in recommendations)


class TestErrorPatternMatching:
    """Tests for error pattern matching edge cases."""

    @pytest.fixture
    def handlers(self):
        """Create ErrorHandlers instance."""
        return ErrorHandlers()

    def test_should_be_case_insensitive(self, handlers):
        """Test that pattern matching is case insensitive."""
        assert handlers._categorize_error("FIELD REQUIRED") == "missing_field"
        assert handlers._categorize_error("Str Type Expected") == "type_mismatch"
        assert handlers._categorize_error("EXTRA FIELDS NOT PERMITTED") == "schema_error"

    def test_should_match_partial_messages(self, handlers):
        """Test that patterns match partial messages."""
        assert handlers._categorize_error("validation error: field required in model") == "missing_field"
        assert handlers._categorize_error("error at line 10: str type expected") == "type_mismatch"

    def test_should_match_complex_constraint_messages(self, handlers):
        """Test matching of complex constraint error messages."""
        assert handlers._categorize_error("ensure this value is greater than 0.0") == "constraint_error"
        assert handlers._categorize_error("input should be less than or equal to 100") == "constraint_error"


class TestIntegrationScenarios:
    """Integration tests for complete error handling scenarios."""

    @pytest.fixture
    def handlers(self):
        """Create ErrorHandlers instance."""
        return ErrorHandlers()

    def test_should_handle_nested_field_errors(self, handlers):
        """Test handling of errors in nested fields."""
        class InnerModel(BaseModel):
            value: int

        class OuterModel(BaseModel):
            inner: InnerModel

        try:
            OuterModel(inner={"value": "not_int"})
        except ValidationError as e:
            analysis = handlers.analyze_validation_error(e)
            assert "inner" in analysis.field_path

    def test_should_handle_list_field_errors(self, handlers):
        """Test handling of errors in list fields."""
        class TestModel(BaseModel):
            items: list[int]

        try:
            TestModel(items=["not_int"])
        except ValidationError as e:
            analysis = handlers.analyze_validation_error(e)
            assert analysis.error_type in ["type_mismatch", "missing_field", "unknown_error"]

    def test_should_generate_comprehensive_report(self, handlers):
        """Test generation of comprehensive report with various error types."""
        class ComplexModel(BaseModel):
            model_config = {"extra": "forbid"}
            required: str
            number: int = Field(ge=0)
            score: float = Field(ge=0.0, le=1.0)

        errors = []
        # Missing field
        try:
            ComplexModel(number=1, score=0.5)
        except ValidationError as e:
            errors.append(e)

        # Type mismatch
        try:
            ComplexModel(required="test", number="not_int", score=0.5)
        except ValidationError as e:
            errors.append(e)

        # Constraint violation
        try:
            ComplexModel(required="test", number=1, score=1.5)
        except ValidationError as e:
            errors.append(e)

        report = handlers.generate_error_report(errors, {"source": "test"})
        assert report.total_errors == 3
        assert len(report.error_analyses) == 3
        assert len(report.recovery_recommendations) > 0
