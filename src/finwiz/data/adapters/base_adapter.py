"""Base adapter interface and error classes for data source adapters."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


class DataAcquisitionError(Exception):
    """Base exception for data acquisition failures."""

    pass


class InvalidDataError(DataAcquisitionError):
    """Exception for invalid data that fails validation."""

    pass


class TimeoutError(DataAcquisitionError):
    """Exception for data acquisition timeouts."""

    pass


@dataclass
class FundamentalData:
    """Standardized fundamental data structure."""

    ticker: str
    source: str
    timestamp: datetime
    confidence: float  # 0.0 to 1.0

    # Core financial metrics
    return_on_equity: float | None = None
    debt_to_equity: float | None = None
    revenue_growth: float | None = None
    profit_margin: float | None = None

    # Additional context
    raw_data: dict[str, Any] | None = None
    warnings: list[str] | None = None

    def __post_init__(self) -> None:
        """Validate data after initialization."""
        if self.warnings is None:
            self.warnings = []

        # Validate confidence
        if not 0.0 <= self.confidence <= 1.0:
            raise InvalidDataError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")

    def is_valid(self) -> bool:
        """Check if the fundamental data passes validation rules."""
        try:
            # ROE validation: Must be between -1.0 and 2.0
            if self.return_on_equity is not None:
                if not -1.0 <= self.return_on_equity <= 2.0:
                    return False

            # Debt/Equity validation: Must be >= 0 and < 10.0
            if self.debt_to_equity is not None:
                if not (self.debt_to_equity >= 0 and self.debt_to_equity < 10.0):
                    return False

            # Revenue Growth validation: Must be between -0.5 and 5.0
            if self.revenue_growth is not None:
                if not -0.5 <= self.revenue_growth <= 5.0:
                    return False

            # Profit Margin validation: Must be between -1.0 and 1.0
            if self.profit_margin is not None:
                if not -1.0 <= self.profit_margin <= 1.0:
                    return False

            return True

        except (TypeError, ValueError):
            return False

    def get_available_fields(self) -> list[str]:
        """Get list of fields that have non-None values."""
        fields = []
        if self.return_on_equity is not None:
            fields.append("return_on_equity")
        if self.debt_to_equity is not None:
            fields.append("debt_to_equity")
        if self.revenue_growth is not None:
            fields.append("revenue_growth")
        if self.profit_margin is not None:
            fields.append("profit_margin")
        return fields


class BaseDataAdapter(ABC):
    """Base class for all data source adapters."""

    def __init__(self, timeout_seconds: float = 3.0) -> None:
        """Initialize adapter with timeout.

        Args:
            timeout_seconds: Maximum time to wait for data acquisition (default 3.0)
        """
        self.timeout_seconds = timeout_seconds

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the name of this data source.

        Returns:
            String identifier for this data source
        """
        pass

    @abstractmethod
    async def get_fundamental_data(self, ticker: str) -> FundamentalData:
        """Get fundamental data for a ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            FundamentalData object with available metrics

        Raises:
            DataAcquisitionError: If data cannot be acquired
            InvalidDataError: If data fails validation
            TimeoutError: If request times out
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this data source is currently available.

        Returns:
            True if the data source can be used, False otherwise
        """
        pass

    def get_source_info(self) -> dict[str, Any]:
        """Get information about this data source.

        Returns:
            Dictionary with source metadata
        """
        return {"name": self.source_name, "timeout_seconds": self.timeout_seconds, "class": self.__class__.__name__}
