"""
Unit tests for CrewDataExtractor.

Tests the data extraction and validation utilities for crew outputs.
"""

import json

import pytest
from pytest import approx

from finwiz.exceptions.data_quality import MissingRequiredFieldError
from finwiz.utils.data_extractor import CrewDataExtractor


class TestExtractQuantitativeMetrics:
    """Test cases for extract_quantitative_metrics method."""

    def test_should_extract_metrics_from_dict(self):
        """Test extracting metrics from dictionary input."""
        # Arrange
        extractor = CrewDataExtractor()
        crew_output = {"performance_metrics": {"volatility": 0.25, "max_drawdown": -0.15, "beta": 1.2}}

        # Act
        result = extractor.extract_quantitative_metrics(crew_output, "AAPL")

        # Assert
        assert result["volatility"] == approx(0.25)
        assert result["max_drawdown"] == approx(-0.15)
        assert result["beta"] == approx(1.2)

    def test_should_extract_metrics_from_json_string(self):
        """Test extracting metrics from JSON string input."""
        # Arrange
        extractor = CrewDataExtractor()
        crew_output = json.dumps({"performance_metrics": {"volatility": 0.30, "max_drawdown": -0.20}})

        # Act
        result = extractor.extract_quantitative_metrics(crew_output, "AAPL")

        # Assert
        assert result["volatility"] == approx(0.30)
        assert result["max_drawdown"] == approx(-0.20)

    def test_should_raise_error_when_volatility_missing(self):
        """Test that error is raised when volatility is missing."""
        # Arrange
        extractor = CrewDataExtractor()
        crew_output = {"performance_metrics": {"max_drawdown": -0.15}}  # Missing volatility

        # Act & Assert
        with pytest.raises(MissingRequiredFieldError) as exc_info:
            extractor.extract_quantitative_metrics(crew_output, "AAPL")

        assert exc_info.value.ticker == "AAPL"
        assert "volatility" in exc_info.value.field

    def test_should_raise_error_when_max_drawdown_missing(self):
        """Test that error is raised when max_drawdown is missing."""
        # Arrange
        extractor = CrewDataExtractor()
        crew_output = {"performance_metrics": {"volatility": 0.25}}  # Missing max_drawdown

        # Act & Assert
        with pytest.raises(MissingRequiredFieldError) as exc_info:
            extractor.extract_quantitative_metrics(crew_output, "AAPL")

        assert exc_info.value.ticker == "AAPL"
        assert "max_drawdown" in exc_info.value.field

    def test_should_handle_optional_beta_field(self):
        """Test that beta is optional and returns None if missing."""
        # Arrange
        extractor = CrewDataExtractor()
        crew_output = {"performance_metrics": {"volatility": 0.25, "max_drawdown": -0.15}}

        # Act
        result = extractor.extract_quantitative_metrics(crew_output, "AAPL")

        # Assert
        assert result["beta"] is None

    def test_should_raise_error_when_performance_metrics_missing(self):
        """Test that error is raised when performance_metrics section is missing."""
        # Arrange
        extractor = CrewDataExtractor()
        crew_output = {"other_data": {"some": "value"}}  # No performance_metrics

        # Act & Assert
        with pytest.raises(MissingRequiredFieldError):
            extractor.extract_quantitative_metrics(crew_output, "AAPL")


class TestExtractGradeAndScore:
    """Test cases for extract_grade_and_score method."""

    def test_should_extract_grade_and_score_from_dict(self):
        """Test extracting grade and score from dictionary."""
        # Arrange
        extractor = CrewDataExtractor()
        crew_output = {"grade": "A", "composite_score": 0.85}

        # Act
        result = extractor.extract_grade_and_score(crew_output, "AAPL")

        # Assert
        assert result["grade"] == "A"
        assert result["composite_score"] == approx(0.85)

    def test_should_extract_grade_and_score_from_json_string(self):
        """Test extracting grade and score from JSON string."""
        # Arrange
        extractor = CrewDataExtractor()
        crew_output = json.dumps({"grade": "A+", "composite_score": 0.92})

        # Act
        result = extractor.extract_grade_and_score(crew_output, "AAPL")

        # Assert
        assert result["grade"] == "A+"
        assert result["composite_score"] == approx(0.92)

    def test_should_fallback_to_final_grade_when_grade_missing(self):
        """Test fallback to final_grade when grade key is missing."""
        # Arrange
        extractor = CrewDataExtractor()
        crew_output = {"final_grade": "B+", "composite_score": 0.78}

        # Act
        result = extractor.extract_grade_and_score(crew_output, "AAPL")

        # Assert
        assert result["grade"] == "B+"
        assert result["composite_score"] == approx(0.78)

    def test_should_fallback_to_final_score_when_composite_score_missing(self):
        """Test fallback to final_score when composite_score key is missing."""
        # Arrange
        extractor = CrewDataExtractor()
        crew_output = {"grade": "A", "final_score": 0.88}

        # Act
        result = extractor.extract_grade_and_score(crew_output, "AAPL")

        # Assert
        assert result["grade"] == "A"
        assert result["composite_score"] == approx(0.88)

    def test_should_use_ai_crew_output_format_with_final_fields(self):
        """Test extraction from AI crew output format using final_grade and final_score."""
        # Arrange - This is the exact format AI crews produce
        extractor = CrewDataExtractor()
        crew_output = {
            "ticker": "IQQH",
            "final_grade": "C",
            "final_score": 0.55,
            "final_recommendation": "HOLD",
        }

        # Act
        result = extractor.extract_grade_and_score(crew_output, "IQQH")

        # Assert
        assert result["grade"] == "C"
        assert result["composite_score"] == approx(0.55)

    def test_should_raise_error_when_grade_missing(self):
        """Test that error is raised when grade is missing."""
        # Arrange
        extractor = CrewDataExtractor()
        crew_output = {"composite_score": 0.85}  # Missing grade

        # Act & Assert
        with pytest.raises(MissingRequiredFieldError) as exc_info:
            extractor.extract_grade_and_score(crew_output, "AAPL")

        assert exc_info.value.ticker == "AAPL"
        assert exc_info.value.field == "grade"

    def test_should_raise_error_when_composite_score_missing(self):
        """Test that error is raised when composite_score is missing."""
        # Arrange
        extractor = CrewDataExtractor()
        crew_output = {"grade": "A"}  # Missing composite_score

        # Act & Assert
        with pytest.raises(MissingRequiredFieldError) as exc_info:
            extractor.extract_grade_and_score(crew_output, "AAPL")

        assert exc_info.value.ticker == "AAPL"
        assert exc_info.value.field == "composite_score"

    def test_should_raise_error_when_grade_is_none(self):
        """Test that error is raised when grade is None."""
        # Arrange
        extractor = CrewDataExtractor()
        crew_output = {"grade": None, "composite_score": 0.85}

        # Act & Assert
        with pytest.raises(MissingRequiredFieldError):
            extractor.extract_grade_and_score(crew_output, "AAPL")

    def test_should_raise_error_when_composite_score_is_none(self):
        """Test that error is raised when composite_score is None."""
        # Arrange
        extractor = CrewDataExtractor()
        crew_output = {"grade": "A", "composite_score": None}

        # Act & Assert
        with pytest.raises(MissingRequiredFieldError):
            extractor.extract_grade_and_score(crew_output, "AAPL")


class TestValidateGradeScoreConsistency:
    """Test cases for validate_grade_score_consistency method."""

    def test_should_return_true_for_matching_a_plus_grade(self):
        """Test that A+ grade matches score >= 0.95."""
        # Arrange
        extractor = CrewDataExtractor()

        # Act & Assert
        assert extractor.validate_grade_score_consistency("A+", 0.96, "AAPL") is True
        assert extractor.validate_grade_score_consistency("A+", 0.95, "AAPL") is True

    def test_should_return_true_for_matching_a_grade(self):
        """Test that A grade matches score >= 0.85 and < 0.95."""
        # Arrange
        extractor = CrewDataExtractor()

        # Act & Assert
        assert extractor.validate_grade_score_consistency("A", 0.87, "AAPL") is True
        assert extractor.validate_grade_score_consistency("A", 0.85, "AAPL") is True

    def test_should_return_true_for_matching_b_grade(self):
        """Test that B grade matches score >= 0.75 and < 0.80."""
        # Arrange
        extractor = CrewDataExtractor()

        # Act & Assert
        assert extractor.validate_grade_score_consistency("B", 0.77, "AAPL") is True
        assert extractor.validate_grade_score_consistency("B", 0.75, "AAPL") is True

    def test_should_return_false_for_mismatched_grade(self):
        """Test that mismatched grade returns False."""
        # Arrange
        extractor = CrewDataExtractor()

        # Act & Assert
        assert extractor.validate_grade_score_consistency("A+", 0.65, "AAPL") is False
        assert extractor.validate_grade_score_consistency("B", 0.90, "AAPL") is False
        assert extractor.validate_grade_score_consistency("F", 0.85, "AAPL") is False

    def test_should_return_true_for_f_grade_with_low_score(self):
        """Test that F grade matches score < 0.50."""
        # Arrange
        extractor = CrewDataExtractor()

        # Act & Assert
        assert extractor.validate_grade_score_consistency("F", 0.30, "AAPL") is True
        assert extractor.validate_grade_score_consistency("F", 0.10, "AAPL") is True
