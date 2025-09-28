"""
Data Freshness Validation for FinWiz Tools.

This module provides validation to ensure that all market data used in analysis
is no older than 24 hours, with graceful degradation when data is stale.
"""

import logging
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class FreshnessResult(BaseModel):
    """Result of data freshness validation."""

    is_fresh: bool = Field(..., description="Whether data meets freshness requirements")
    age_hours: float | None = Field(None, description="Age of data in hours")
    effective_age_hours: float | None = Field(None, description="Market-adjusted age")
    data_source: str = Field(..., description="Source of the data")
    validated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    warning: str | None = Field(None, description="Freshness warning message")
    should_refresh: bool = Field(False, description="Whether data should be refreshed")


class MarketCalendar:
    """Simple market calendar for weekend/holiday adjustments."""

    def is_weekend(self, dt: datetime) -> bool:
        """Check if date is a weekend."""
        return dt.weekday() >= 5  # Saturday = 5, Sunday = 6

    def is_holiday(self, dt: datetime) -> bool:
        """Check if date is a market holiday (simplified implementation)."""
        # For now, just return False - can be enhanced with actual holiday calendar
        return False


class DataFreshnessValidator:
    """
    Validates that all market data is within acceptable age limits.

    Ensures data freshness requirements are met while providing graceful
    degradation when data is stale.
    """

    def __init__(self, max_age_hours: int = 24):
        """
        Initialize the validator.

        Args:
            max_age_hours: Maximum acceptable age for data in hours (default: 24)

        """
        self.max_age_hours = max_age_hours
        self.market_calendar = MarketCalendar()

    def validate_data_freshness(self, data: dict[str, Any] | list[dict[str, Any]], data_source: str) -> FreshnessResult:
        """
        Validate data freshness considering market hours and weekends.

        Args:
            data: The data to validate (dict or list of dicts)
            data_source: Name of the data source for logging

        Returns:
            FreshnessResult with validation details

        """
        try:
            timestamp = self._extract_timestamp(data)
            if not timestamp:
                logger.warning(f"No timestamp found in data from {data_source}")
                return FreshnessResult(
                    is_fresh=False,
                    age_hours=None,
                    warning="No timestamp found in data",
                    should_refresh=True,
                    data_source=data_source,
                )

            age_hours = self._calculate_age_hours(timestamp)

            # Adjust for market hours and weekends
            effective_age = self._adjust_for_market_schedule(age_hours, timestamp)

            is_fresh = effective_age <= self.max_age_hours

            if not is_fresh:
                logger.warning(
                    f"Stale data detected from {data_source}: {age_hours:.1f} hours old (effective: {effective_age:.1f}h)"
                )

            return FreshnessResult(
                is_fresh=is_fresh,
                age_hours=age_hours,
                effective_age_hours=effective_age,
                warning=None if is_fresh else f"Data is {age_hours:.1f} hours old",
                should_refresh=not is_fresh,
                data_source=data_source,
            )

        except Exception as e:
            logger.error(f"Freshness validation failed for {data_source}: {e}")
            return FreshnessResult(
                is_fresh=False, age_hours=None, warning=f"Validation error: {str(e)}", should_refresh=True, data_source=data_source
            )

    def _extract_timestamp(self, data: dict[str, Any] | list[dict[str, Any]]) -> datetime | None:
        """
        Extract timestamp from data structure.

        Looks for common timestamp fields in various formats.
        """
        if isinstance(data, list):
            # For list data, check the first item
            if not data:
                return None
            data = data[0]

        if not isinstance(data, dict):
            return None

        # Common timestamp field names
        timestamp_fields = [
            "timestamp",
            "date",
            "datetime",
            "time",
            "last_updated",
            "updated_at",
            "created_at",
            "quote_time",
            "market_time",
            "data_time",
        ]

        for field in timestamp_fields:
            if field in data:
                return self._parse_timestamp(data[field])

        # Check for nested timestamp in common structures
        if "meta" in data and isinstance(data["meta"], dict):
            for field in timestamp_fields:
                if field in data["meta"]:
                    return self._parse_timestamp(data["meta"][field])

        return None

    def _parse_timestamp(self, timestamp_value: Any) -> datetime | None:
        """Parse various timestamp formats into datetime object."""
        if isinstance(timestamp_value, datetime):
            # Ensure timezone awareness
            if timestamp_value.tzinfo is None:
                return timestamp_value.replace(tzinfo=UTC)
            return timestamp_value

        if isinstance(timestamp_value, str):
            # Try ISO format first (most common)
            try:
                # Handle ISO format with timezone info
                if timestamp_value.endswith("Z"):
                    timestamp_value = timestamp_value[:-1] + "+00:00"
                return datetime.fromisoformat(timestamp_value)
            except ValueError:
                pass

            # Try common timestamp formats
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%dT%H:%M:%S.%fZ",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%d",
                "%m/%d/%Y",
                "%d/%m/%Y",
            ]

            for fmt in formats:
                try:
                    dt = datetime.strptime(timestamp_value, fmt)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=UTC)
                    return dt
                except ValueError:
                    continue

        if isinstance(timestamp_value, (int, float)):
            # Assume Unix timestamp
            try:
                return datetime.fromtimestamp(timestamp_value, tz=UTC)
            except (ValueError, OSError):
                pass

        return None

    def _calculate_age_hours(self, timestamp: datetime) -> float:
        """Calculate age of data in hours."""
        now = datetime.now(UTC)
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=UTC)

        age_delta = now - timestamp
        return age_delta.total_seconds() / 3600

    def _adjust_for_market_schedule(self, age_hours: float, timestamp: datetime) -> float:
        """
        Adjust age calculation for weekends and market holidays.

        Weekend data can be considered "fresher" since markets are closed.
        """
        if self.market_calendar.is_weekend(timestamp):
            # Weekend data can be older - reduce effective age by 30%
            return age_hours * 0.7

        if self.market_calendar.is_holiday(timestamp):
            # Holiday data can be older - reduce effective age by 20%
            return age_hours * 0.8

        return age_hours

    def add_freshness_metadata(self, data: dict[str, Any], freshness_result: FreshnessResult) -> dict[str, Any]:
        """
        Add freshness metadata to data structure.

        Args:
            data: Original data dictionary
            freshness_result: Result from freshness validation

        Returns:
            Data with added freshness metadata

        """
        if not isinstance(data, dict):
            return data

        # Add freshness info without modifying original data
        enhanced_data = data.copy()
        enhanced_data["_freshness_info"] = {
            "is_fresh": freshness_result.is_fresh,
            "age_hours": freshness_result.age_hours,
            "effective_age_hours": freshness_result.effective_age_hours,
            "validated_at": freshness_result.validated_at.isoformat(),
            "data_source": freshness_result.data_source,
            "warning": freshness_result.warning,
        }

        return enhanced_data
