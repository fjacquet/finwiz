"""Data models for quantitative analysis."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class PriceData(BaseModel):
    """Price data structure for technical analysis."""

    symbol: str = Field(..., description="Symbol for the price data")
    timestamp: datetime = Field(..., description="Timestamp of the data point")

    # OHLCV data
    open: float = Field(..., description="Opening price")
    high: float = Field(..., description="High price")
    low: float = Field(..., description="Low price")
    close: float = Field(..., description="Closing price")
    volume: int = Field(..., description="Trading volume")

    # Adjusted prices (optional)
    adj_close: float | None = Field(None, description="Adjusted closing price")

    # Additional fields
    dividend: float | None = Field(None, description="Dividend amount")
    split_ratio: float | None = Field(None, description="Stock split ratio")

    @field_validator("high")
    @classmethod
    def validate_high_price(cls, v: float, info: Any) -> float:
        """Validate high price is >= low price."""
        if hasattr(info, "data") and "low" in info.data and v < info.data["low"]:
            raise ValueError("High price must be >= low price")
        return v

    @field_validator("volume")
    @classmethod
    def validate_volume_positive(cls, v: int) -> int:
        """Validate volume is non-negative."""
        if v < 0:
            raise ValueError("Volume must be non-negative")
        return v


class CachedDataInfo(BaseModel):
    """Information about cached data."""

    cache_key: str = Field(..., description="Cache key identifier")
    data_type: str = Field(..., description="Type of cached data")
    created_at: datetime = Field(..., description="When data was cached")
    expires_at: datetime | None = Field(None, description="When data expires")
    size_bytes: int = Field(..., description="Size of cached data in bytes")
    hit_count: int = Field(0, description="Number of cache hits")
    last_accessed: datetime | None = Field(None, description="Last access time")
