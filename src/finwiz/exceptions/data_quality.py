"""
Data quality exceptions for FinWiz.

These exceptions are raised when data quality issues are detected,
such as missing required fields, grade-score mismatches, or other
data integrity problems.
"""

from typing import Any


class DataQualityError(Exception):
    """
    Base exception for data quality issues.

    This is the parent class for all data quality-related exceptions.
    Use specific subclasses when possible for better error handling.
    """

    pass


class MissingRequiredFieldError(DataQualityError):
    """
    Raised when a required field is missing from analysis data.

    This exception indicates that critical data needed for analysis
    is not available, preventing accurate scoring or recommendations.

    Attributes:
        ticker: The ticker symbol being analyzed
        field: The name of the missing field
        context: Additional context about where the error occurred

    Example:
        >>> raise MissingRequiredFieldError(ticker="AAPL", field="volatility", context={"source": "quantitative_analysis"})

    """

    def __init__(self, ticker: str, field: str, context: dict[str, Any] | None = None) -> None:
        """
        Initialize MissingRequiredFieldError.

        Args:
            ticker: Ticker symbol being analyzed
            field: Name of the missing required field
            context: Optional dictionary with additional context

        """
        self.ticker = ticker
        self.field = field
        self.context = context or {}

        # Build detailed error message
        message = f"Missing required field '{field}' for {ticker}"

        # Add context information if available
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            message += f" ({context_str})"

        super().__init__(message)


class GradeScoreMismatchError(DataQualityError):
    """
    Raised when a grade doesn't match its corresponding composite score.

    This exception indicates a data integrity issue where the assigned
    letter grade is inconsistent with the numerical composite score
    according to the grading scale.

    Attributes:
        ticker: The ticker symbol being analyzed
        grade: The assigned letter grade
        score: The composite score (0.0-1.0)
        expected_grade: The grade that should match the score

    Example:
        >>> raise GradeScoreMismatchError(ticker="AAPL", grade="A+", score=0.65, expected_grade="B")

    """

    def __init__(self, ticker: str, grade: str, score: float, expected_grade: str) -> None:
        """
        Initialize GradeScoreMismatchError.

        Args:
            ticker: Ticker symbol being analyzed
            grade: The assigned letter grade
            score: The composite score (0.0-1.0)
            expected_grade: The grade that should match the score

        """
        self.ticker = ticker
        self.grade = grade
        self.score = score
        self.expected_grade = expected_grade

        message = (
            f"Grade mismatch for {ticker}: "
            f"grade={grade}, score={score:.3f}, expected={expected_grade}. "
            f"The assigned grade '{grade}' is inconsistent with the composite score {score:.3f}."
        )

        super().__init__(message)
