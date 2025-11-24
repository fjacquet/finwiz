"""
Unit tests for DeepAnalysisResult schema validation.

Tests the enhanced DeepAnalysisResult Pydantic schema with all required fields,
validation rules, and the extra='forbid' configuration.
"""

from pytest import approx
from datetime import datetime

import pytest
from pydantic import ValidationError

from finwiz.flow_state import DeepAnalysisResult


class TestDeepAnalysisResultSchemaValidation:
    """Test suite for DeepAnalysisResult schema validation."""

    def test_should_validate_with_all_required_fields(self):
        """Test that schema validates successfully with all required fields."""
        # Arrange
        result_data = {
            "ticker": "AAPL",
            "asset_class": "stock",
            "crew_name": "DeepAnalysisCrew",
            "analysis_timestamp": datetime.now().isoformat(),
            "composite_score": 0.85,
            "grade": "A",
            "recommendation": "BUY",
            "rationale": "Strong fundamentals and technical indicators",
            "data_freshness_hours": 2.5,
            "confidence_level": 0.9,
        }

        # Act
        result = DeepAnalysisResult(**result_data)

        # Assert
        assert result.ticker == "AAPL"
        assert result.asset_class == "stock"
        assert result.crew_name == "DeepAnalysisCrew"
        assert result.composite_score == approx(0.85)
        assert result.grade == "A"
        assert result.data_freshness_hours == approx(2.5)
        assert result.confidence_level == approx(0.9)
        assert isinstance(result.analysis_timestamp, str)  # ISO format string
        assert result.warnings == []  # Default empty list
        assert result.cached is False  # Default value

    def test_should_reject_missing_required_fields(self):
        """Test that schema rejects data missing required fields."""
        # Arrange - Missing ticker
        incomplete_data = {
            "asset_class": "stock",
            "crew_name": "DeepAnalysisCrew",
            "composite_score": 0.85,
            "grade": "A",
            "data_freshness_hours": 2.5,
            "confidence_level": 0.9,
            "recommendation": "BUY",
            "rationale": "Strong fundamentals and technical indicators",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            DeepAnalysisResult(**incomplete_data)

        # Verify error mentions the missing field
        error_str = str(exc_info.value)
        assert "ticker" in error_str.lower()

    def test_should_reject_unknown_fields_with_extra_forbid(self):
        """Test that extra='forbid' rejects unknown fields."""
        # Arrange
        data_with_extra_field = {
            "ticker": "AAPL",
            "asset_class": "stock",
            "crew_name": "DeepAnalysisCrew",
            "analysis_timestamp": datetime.now().isoformat(),
            "composite_score": 0.85,
            "grade": "A",
            "data_freshness_hours": 2.5,
            "confidence_level": 0.9,
            "unknown_field": "should_be_rejected",  # Extra field
            "recommendation": "BUY",
            "rationale": "Strong fundamentals and technical indicators",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            DeepAnalysisResult(**data_with_extra_field)

        # Verify error mentions extra field
        error_str = str(exc_info.value)
        assert "unknown_field" in error_str.lower() or "extra" in error_str.lower()

    def test_should_validate_composite_score_range(self):
        """Test that composite_score must be between 0.0 and 1.0."""
        # Arrange - Valid range
        valid_data = {
            "ticker": "AAPL",
            "asset_class": "stock",
            "crew_name": "DeepAnalysisCrew",
            "composite_score": 0.5,
            "grade": "B",
            "recommendation": "BUY",
            "rationale": "Strong fundamentals and technical indicators",
            "data_freshness_hours": 1.0,
            "confidence_level": 0.8,
        }

        # Act
        result = DeepAnalysisResult(**valid_data)

        # Assert
        assert result.composite_score == approx(0.5)

    def test_should_reject_composite_score_below_zero(self):
        """Test that composite_score below 0.0 is rejected."""
        # Arrange
        invalid_data = {
            "ticker": "AAPL",
            "asset_class": "stock",
            "crew_name": "DeepAnalysisCrew",
            "composite_score": -0.1,  # Invalid
            "grade": "F",
            "data_freshness_hours": 1.0,
            "confidence_level": 0.8,
            "recommendation": "BUY",
            "rationale": "Strong fundamentals and technical indicators",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            DeepAnalysisResult(**invalid_data)

        error_str = str(exc_info.value)
        assert "composite_score" in error_str.lower()

    def test_should_reject_composite_score_above_one(self):
        """Test that composite_score above 1.0 is rejected."""
        # Arrange
        invalid_data = {
            "ticker": "AAPL",
            "asset_class": "stock",
            "crew_name": "DeepAnalysisCrew",
            "composite_score": 1.5,  # Invalid
            "grade": "A+",
            "data_freshness_hours": 1.0,
            "confidence_level": 0.8,
            "recommendation": "BUY",
            "rationale": "Strong fundamentals and technical indicators",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            DeepAnalysisResult(**invalid_data)

        error_str = str(exc_info.value)
        assert "composite_score" in error_str.lower()

    def test_should_validate_confidence_level_range(self):
        """Test that confidence_level must be between 0.0 and 1.0."""
        # Arrange - Valid range
        valid_data = {
            "ticker": "AAPL",
            "asset_class": "stock",
            "crew_name": "DeepAnalysisCrew",
            "composite_score": 0.85,
            "grade": "A",
            "data_freshness_hours": 1.0,
            "confidence_level": 0.95,
            "recommendation": "BUY",
            "rationale": "Strong fundamentals and technical indicators",
        }

        # Act
        result = DeepAnalysisResult(**valid_data)

        # Assert
        assert result.confidence_level == approx(0.95)

    def test_should_reject_confidence_level_below_zero(self):
        """Test that confidence_level below 0.0 is rejected."""
        # Arrange
        invalid_data = {
            "ticker": "AAPL",
            "asset_class": "stock",
            "crew_name": "DeepAnalysisCrew",
            "composite_score": 0.85,
            "grade": "A",
            "data_freshness_hours": 1.0,
            "confidence_level": -0.1,  # Invalid
            "recommendation": "BUY",
            "rationale": "Strong fundamentals and technical indicators",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            DeepAnalysisResult(**invalid_data)

        error_str = str(exc_info.value)
        assert "confidence_level" in error_str.lower()

    def test_should_reject_confidence_level_above_one(self):
        """Test that confidence_level above 1.0 is rejected."""
        # Arrange
        invalid_data = {
            "ticker": "AAPL",
            "asset_class": "stock",
            "crew_name": "DeepAnalysisCrew",
            "composite_score": 0.85,
            "grade": "A",
            "data_freshness_hours": 1.0,
            "confidence_level": 1.5,  # Invalid
            "recommendation": "BUY",
            "rationale": "Strong fundamentals and technical indicators",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            DeepAnalysisResult(**invalid_data)

        error_str = str(exc_info.value)
        assert "confidence_level" in error_str.lower()

    def test_should_validate_data_freshness_hours_non_negative(self):
        """Test that data_freshness_hours must be non-negative."""
        # Arrange - Valid non-negative value
        valid_data = {
            "ticker": "AAPL",
            "asset_class": "stock",
            "crew_name": "DeepAnalysisCrew",
            "composite_score": 0.85,
            "grade": "A",
            "data_freshness_hours": 0.0,  # Zero is valid
            "confidence_level": 0.9,
            "recommendation": "BUY",
            "rationale": "Strong fundamentals and technical indicators",
        }

        # Act
        result = DeepAnalysisResult(**valid_data)

        # Assert
        assert result.data_freshness_hours == approx(0.0)

    def test_should_reject_negative_data_freshness_hours(self):
        """Test that negative data_freshness_hours is rejected."""
        # Arrange
        invalid_data = {
            "ticker": "AAPL",
            "asset_class": "stock",
            "crew_name": "DeepAnalysisCrew",
            "composite_score": 0.85,
            "grade": "A",
            "data_freshness_hours": -1.0,  # Invalid
            "confidence_level": 0.9,
            "recommendation": "BUY",
            "rationale": "Strong fundamentals and technical indicators",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            DeepAnalysisResult(**invalid_data)

        error_str = str(exc_info.value)
        assert "data_freshness_hours" in error_str.lower()

    def test_should_validate_risk_score_range(self):
        """Test that risk_score (optional) must be between 0.0 and 5.0."""
        # Arrange - Valid range
        valid_data = {
            "ticker": "AAPL",
            "asset_class": "stock",
            "crew_name": "DeepAnalysisCrew",
            "composite_score": 0.85,
            "grade": "A",
            "data_freshness_hours": 1.0,
            "confidence_level": 0.9,
            "risk_score": 2.5,
            "recommendation": "BUY",
            "rationale": "Strong fundamentals and technical indicators",
        }

        # Act
        result = DeepAnalysisResult(**valid_data)

        # Assert
        assert result.risk_score == approx(2.5)

    def test_should_reject_risk_score_above_five(self):
        """Test that risk_score above 5.0 is rejected."""
        # Arrange
        invalid_data = {
            "ticker": "AAPL",
            "asset_class": "stock",
            "crew_name": "DeepAnalysisCrew",
            "composite_score": 0.85,
            "grade": "A",
            "data_freshness_hours": 1.0,
            "confidence_level": 0.9,
            "risk_score": 6.0,  # Invalid
            "recommendation": "BUY",
            "rationale": "Strong fundamentals and technical indicators",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            DeepAnalysisResult(**invalid_data)

        error_str = str(exc_info.value)
        assert "risk_score" in error_str.lower()

    def test_should_accumulate_warnings_list(self):
        """Test that warnings list can accumulate multiple warnings."""
        # Arrange
        data_with_warnings = {
            "ticker": "AAPL",
            "asset_class": "stock",
            "crew_name": "DeepAnalysisCrew",
            "composite_score": 0.85,
            "grade": "A",
            "data_freshness_hours": 25.0,  # Stale data
            "confidence_level": 0.7,  # Lower confidence
            "warnings": [
                "Data is 25 hours old",
                "Reduced confidence due to stale data",
                "Missing some technical indicators",
            ],
            "recommendation": "BUY",
            "rationale": "Strong fundamentals and technical indicators",
        }

        # Act
        result = DeepAnalysisResult(**data_with_warnings)

        # Assert
        assert len(result.warnings) == 3
        assert "Data is 25 hours old" in result.warnings
        assert "Reduced confidence due to stale data" in result.warnings
        assert "Missing some technical indicators" in result.warnings

    def test_should_default_to_empty_warnings_list(self):
        """Test that warnings defaults to empty list when not provided."""
        # Arrange
        data_without_warnings = {
            "ticker": "AAPL",
            "asset_class": "stock",
            "crew_name": "DeepAnalysisCrew",
            "composite_score": 0.85,
            "grade": "A",
            "data_freshness_hours": 1.0,
            "confidence_level": 0.9,
            "recommendation": "BUY",
            "rationale": "Strong fundamentals and technical indicators",
        }

        # Act
        result = DeepAnalysisResult(**data_without_warnings)

        # Assert
        assert result.warnings == []
        assert isinstance(result.warnings, list)

    def test_should_strip_whitespace_from_strings(self):
        """Test that str_strip_whitespace config strips whitespace."""
        # Arrange
        data_with_whitespace = {
            "ticker": "  AAPL  ",
            "asset_class": "  stock  ",
            "crew_name": "  DeepAnalysisCrew  ",
            "composite_score": 0.85,
            "grade": "  A  ",
            "data_freshness_hours": 1.0,
            "confidence_level": 0.9,
            "recommendation": "  BUY  ",
            "rationale": "  Strong fundamentals and technical indicators  ",
        }

        # Act
        result = DeepAnalysisResult(**data_with_whitespace)

        # Assert
        assert result.ticker == "AAPL"
        assert result.asset_class == "stock"
        assert result.crew_name == "DeepAnalysisCrew"
        assert result.grade == "A"
        assert result.recommendation == "BUY"
        assert result.rationale == "Strong fundamentals and technical indicators"

    def test_should_validate_optional_scores(self):
        """Test that optional score fields (fundamental, technical) validate correctly."""
        # Arrange
        data_with_optional_scores = {
            "ticker": "AAPL",
            "asset_class": "stock",
            "crew_name": "DeepAnalysisCrew",
            "composite_score": 0.85,
            "grade": "A",
            "data_freshness_hours": 1.0,
            "confidence_level": 0.9,
            "fundamental_score": 0.9,
            "technical_score": 0.8,
            "recommendation": "BUY",
            "rationale": "Strong fundamentals and technical indicators",
        }

        # Act
        result = DeepAnalysisResult(**data_with_optional_scores)

        # Assert
        assert result.fundamental_score == approx(0.9)
        assert result.technical_score == approx(0.8)

    def test_should_reject_invalid_optional_score_ranges(self):
        """Test that optional scores must be in valid range (0.0-1.0)."""
        # Arrange
        invalid_data = {
            "ticker": "AAPL",
            "asset_class": "stock",
            "crew_name": "DeepAnalysisCrew",
            "composite_score": 0.85,
            "grade": "A",
            "data_freshness_hours": 1.0,
            "confidence_level": 0.9,
            "fundamental_score": 1.5,  # Invalid
            "recommendation": "BUY",
            "rationale": "Strong fundamentals and technical indicators",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            DeepAnalysisResult(**invalid_data)

        error_str = str(exc_info.value)
        assert "fundamental_score" in error_str.lower()

    def test_should_handle_analysis_timestamp_correctly(self):
        """Test that analysis_timestamp is handled correctly."""
        # Arrange
        specific_time = "2025-01-15T10:30:00"
        data_with_timestamp = {
            "ticker": "AAPL",
            "asset_class": "stock",
            "crew_name": "DeepAnalysisCrew",
            "analysis_timestamp": specific_time,
            "composite_score": 0.85,
            "grade": "A",
            "data_freshness_hours": 1.0,
            "confidence_level": 0.9,
            "recommendation": "BUY",
            "rationale": "Strong fundamentals and technical indicators",
        }

        # Act
        result = DeepAnalysisResult(**data_with_timestamp)

        # Assert
        assert result.analysis_timestamp == specific_time
        assert isinstance(result.analysis_timestamp, str)

    def test_should_default_analysis_timestamp_to_now(self):
        """Test that analysis_timestamp defaults to current time."""
        # Arrange
        before_creation = datetime.now().isoformat()
        data_without_timestamp = {
            "ticker": "AAPL",
            "asset_class": "stock",
            "crew_name": "DeepAnalysisCrew",
            "composite_score": 0.85,
            "grade": "A",
            "data_freshness_hours": 1.0,
            "confidence_level": 0.9,
            "recommendation": "BUY",
            "rationale": "Strong fundamentals and technical indicators",
        }

        # Act
        result = DeepAnalysisResult(**data_without_timestamp)
        after_creation = datetime.now().isoformat()

        # Assert
        assert isinstance(result.analysis_timestamp, str)
        assert before_creation <= result.analysis_timestamp <= after_creation

    def test_should_validate_cached_flag(self):
        """Test that cached flag works correctly."""
        # Arrange
        cached_data = {
            "ticker": "AAPL",
            "asset_class": "stock",
            "crew_name": "DeepAnalysisCrew",
            "composite_score": 0.85,
            "grade": "A",
            "data_freshness_hours": 1.0,
            "confidence_level": 0.9,
            "cached": True,
            "recommendation": "BUY",
            "rationale": "Strong fundamentals and technical indicators",
        }

        # Act
        result = DeepAnalysisResult(**cached_data)

        # Assert
        assert result.cached is True

    def test_should_default_cached_to_false(self):
        """Test that cached defaults to False."""
        # Arrange
        data_without_cached = {
            "ticker": "AAPL",
            "asset_class": "stock",
            "crew_name": "DeepAnalysisCrew",
            "composite_score": 0.85,
            "grade": "A",
            "data_freshness_hours": 1.0,
            "confidence_level": 0.9,
            "recommendation": "BUY",
            "rationale": "Strong fundamentals and technical indicators",
        }

        # Act
        result = DeepAnalysisResult(**data_without_cached)

        # Assert
        assert result.cached is False

    def test_should_validate_complete_analysis_result(self):
        """Test validation of a complete analysis result with all fields."""
        # Arrange
        complete_data = {
            "ticker": "AAPL",
            "asset_class": "stock",
            "crew_name": "DeepAnalysisCrew",
            "analysis_timestamp": datetime.now().isoformat(),
            "composite_score": 0.87,
            "grade": "A",
            "fundamental_score": 0.9,
            "technical_score": 0.85,
            "risk_score": 2.3,
            "data_freshness_hours": 1.5,
            "confidence_level": 0.92,
            "warnings": [
                "Minor data delay",
                "Some indicators unavailable",
            ],
            "cached": False,
            "recommendation": "BUY",
            "rationale": "Strong fundamentals and technical indicators",
        }

        # Act
        result = DeepAnalysisResult(**complete_data)

        # Assert - Verify all fields
        assert result.ticker == "AAPL"
        assert result.asset_class == "stock"
        assert result.crew_name == "DeepAnalysisCrew"
        assert result.composite_score == approx(0.87)
        assert result.grade == "A"
        assert result.fundamental_score == approx(0.9)
        assert result.technical_score == approx(0.85)
        assert result.risk_score == approx(2.3)
        assert result.data_freshness_hours == approx(1.5)
        assert result.confidence_level == approx(0.92)
        assert len(result.warnings) == 2
        assert result.cached is False
        assert isinstance(result.analysis_timestamp, str)

    def test_should_serialize_to_dict_correctly(self):
        """Test that schema can be serialized to dict."""
        # Arrange
        data = {
            "ticker": "AAPL",
            "asset_class": "stock",
            "crew_name": "DeepAnalysisCrew",
            "composite_score": 0.85,
            "grade": "A",
            "data_freshness_hours": 1.0,
            "confidence_level": 0.9,
            "warnings": ["Test warning"],
            "recommendation": "BUY",
            "rationale": "Strong fundamentals and technical indicators",
        }
        result = DeepAnalysisResult(**data)

        # Act
        result_dict = result.model_dump()

        # Assert
        assert isinstance(result_dict, dict)
        assert result_dict["ticker"] == "AAPL"
        assert result_dict["asset_class"] == "stock"
        assert result_dict["composite_score"] == approx(0.85)
        assert result_dict["warnings"] == ["Test warning"]

    def test_should_serialize_to_json_correctly(self):
        """Test that schema can be serialized to JSON."""
        # Arrange
        data = {
            "ticker": "AAPL",
            "asset_class": "stock",
            "crew_name": "DeepAnalysisCrew",
            "composite_score": 0.85,
            "grade": "A",
            "data_freshness_hours": 1.0,
            "confidence_level": 0.9,
            "recommendation": "BUY",
            "rationale": "Strong fundamentals and technical indicators",
        }
        result = DeepAnalysisResult(**data)

        # Act
        result_json = result.model_dump_json()

        # Assert
        assert isinstance(result_json, str)
        assert "AAPL" in result_json
        assert "stock" in result_json
        assert "0.85" in result_json