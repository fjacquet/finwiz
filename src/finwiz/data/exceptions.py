"""
Data acquisition exceptions.

Defines error types for multi-source data acquisition with fallback strategies.
"""

from typing import Any


class DataAcquisitionError(Exception):
    """Base exception for data acquisition failures."""

    pass


class DataUnavailableError(DataAcquisitionError):
    """All data sources failed (Requirement 11.4)."""

    def __init__(self, ticker: str, field: str, sources_tried: list[str]) -> None:
        """
        Initialize DataUnavailableError.

        Args:
            ticker: Stock ticker symbol
            field: Field that could not be acquired
            sources_tried: List of data sources that were attempted

        """
        self.ticker = ticker
        self.field = field
        self.sources_tried = sources_tried
        super().__init__(f"Failed to acquire {field} for {ticker}. Tried sources: {', '.join(sources_tried)}")


class InvalidDataError(DataAcquisitionError):
    """Data validation failed (Requirement 11.7)."""

    def __init__(self, ticker: str, field: str, value: Any, reason: str) -> None:
        """
        Initialize InvalidDataError.

        Args:
            ticker: Stock ticker symbol
            field: Field that failed validation
            value: Invalid value
            reason: Reason for validation failure

        """
        self.ticker = ticker
        self.field = field
        self.value = value
        self.reason = reason
        super().__init__(f"Invalid {field} for {ticker}: {value} ({reason})")


class TimeoutError(DataAcquisitionError):
    """Data acquisition exceeded timeout (Requirement 11.6)."""

    def __init__(self, ticker: str, elapsed: float, timeout: float) -> None:
        """
        Initialize TimeoutError.

        Args:
            ticker: Stock ticker symbol
            elapsed: Time elapsed in seconds
            timeout: Timeout limit in seconds

        """
        self.ticker = ticker
        self.elapsed = elapsed
        self.timeout = timeout
        super().__init__(f"Data acquisition for {ticker} exceeded {timeout}s timeout (took {elapsed:.2f}s)")
