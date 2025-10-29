"""
Unit tests for data quality exceptions.

Tests the custom exception classes used for data quality error handling.
"""

import pytest

from finwiz.exceptions.data_quality import (
    DataQualityError,
    GradeScoreMismatchError,
    MissingRequiredFieldError,
)


class TestMissingRequiredFieldError:
    """Test cases for MissingRequiredFieldError."""

    def test_should_create_error_with_ticker_and_field(self):
        """Test basic error creation with ticker and field."""
        # Arrange & Act
        error = MissingRequiredFieldError(ticker="AAPL", field="volatility")

        # Assert
        assert error.ticker == "AAPL"
        assert error.field == "volatility"
        assert "AAPL" in str(error)
        assert "volatility" in str(error)

    def test_should_include_context_in_error_message(self):
        """Test that context is included in error message."""
        # Arrange & Act
        error = MissingRequiredFieldError(
            ticker="AAPL", field="volatility", context={"source": "quantitative_analysis", "attempt": 1}
        )

        # Assert
        assert error.context == {"source": "quantitative_analysis", "attempt": 1}
        assert "source=quantitative_analysis" in str(error)
        assert "attempt=1" in str(error)

    def test_should_inherit_from_data_quality_error(self):
        """Test that MissingRequiredFieldError inherits from DataQualityError."""
        # Arrange & Act
        error = MissingRequiredFieldError(ticker="AAPL", field="volatility")

        # Assert
        assert isinstance(error, DataQualityError)
        assert isinstance(error, Exception)


class TestGradeScoreMismatchError:
    """Test cases for GradeScoreMismatchError."""

    def test_should_create_error_with_grade_score_mismatch(self):
        """Test error creation with grade-score mismatch."""
        # Arrange & Act
        error = GradeScoreMismatchError(ticker="AAPL", grade="A+", score=0.65, expected_grade="B")

        # Assert
        assert error.ticker == "AAPL"
        assert error.grade == "A+"
        assert error.score == 0.65
        assert error.expected_grade == "B"

    def test_should_include_all_details_in_error_message(self):
        """Test that error message includes all relevant details."""
        # Arrange & Act
        error = GradeScoreMismatchError(ticker="AAPL", grade="A+", score=0.65, expected_grade="B")

        # Assert
        error_msg = str(error)
        assert "AAPL" in error_msg
        assert "A+" in error_msg
        assert "0.65" in error_msg or "0.650" in error_msg
        assert "B" in error_msg
        assert "mismatch" in error_msg.lower()

    def test_should_inherit_from_data_quality_error(self):
        """Test that GradeScoreMismatchError inherits from DataQualityError."""
        # Arrange & Act
        error = GradeScoreMismatchError(ticker="AAPL", grade="A+", score=0.65, expected_grade="B")

        # Assert
        assert isinstance(error, DataQualityError)
        assert isinstance(error, Exception)


class TestDataQualityError:
    """Test cases for base DataQualityError."""

    def test_should_be_catchable_as_exception(self):
        """Test that DataQualityError can be caught as Exception."""
        # Arrange & Act & Assert
        with pytest.raises(Exception):
            raise DataQualityError("Test error")

    def test_should_be_catchable_as_data_quality_error(self):
        """Test that DataQualityError can be caught specifically."""
        # Arrange & Act & Assert
        with pytest.raises(DataQualityError):
            raise DataQualityError("Test error")

    def test_should_catch_subclass_errors(self):
        """Test that DataQualityError catches its subclasses."""
        # Arrange & Act & Assert
        with pytest.raises(DataQualityError):
            raise MissingRequiredFieldError(ticker="AAPL", field="volatility")

        with pytest.raises(DataQualityError):
            raise GradeScoreMismatchError(ticker="AAPL", grade="A+", score=0.65, expected_grade="B")
