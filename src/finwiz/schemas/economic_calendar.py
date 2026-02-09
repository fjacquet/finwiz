"""Economic calendar schemas for Phase 16 Report Enrichment.

Pydantic models for upcoming economic events and earnings dates from Finnhub.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "EarningsEvent",
    "EconomicCalendar",
    "EconomicEvent",
]


class EconomicEvent(BaseModel):
    """A single economic calendar event (e.g., FOMC, CPI release)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    event: str = Field(..., min_length=1, description="Event name (e.g., 'FOMC Meeting', 'CPI Release')")
    country: str = Field(..., min_length=1, description="Country code (e.g., 'US')")
    date: str = Field(..., min_length=1, description="Event date (YYYY-MM-DD)")
    impact: str | None = Field(None, description="Expected impact level (high, medium, low)")
    actual: float | None = Field(None, description="Actual value (if released)")
    estimate: float | None = Field(None, description="Consensus estimate")
    prev: float | None = Field(None, description="Previous value")


class EarningsEvent(BaseModel):
    """A single earnings calendar event for a ticker."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    symbol: str = Field(..., min_length=1, max_length=10, description="Ticker symbol")
    date: str = Field(..., min_length=1, description="Earnings date (YYYY-MM-DD)")
    eps_estimate: float | None = Field(None, description="EPS consensus estimate")
    eps_actual: float | None = Field(None, description="Actual EPS (if reported)")
    revenue_estimate: float | None = Field(None, description="Revenue consensus estimate")


class EconomicCalendar(BaseModel):
    """Combined economic and earnings calendar."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    economic_events: list[EconomicEvent] = Field(default_factory=list, description="Upcoming economic events")
    earnings_events: list[EarningsEvent] = Field(default_factory=list, description="Upcoming earnings events")
    fetched_at: datetime = Field(default_factory=datetime.now, description="When calendar data was fetched")
    days_ahead: int = Field(default=30, ge=1, description="Number of days ahead covered")
