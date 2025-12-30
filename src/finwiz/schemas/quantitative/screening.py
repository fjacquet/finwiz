"""Screening models for quantitative analysis."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ScreeningFilter(BaseModel):
    """Individual screening filter."""

    field: str = Field(..., description="Field to filter on")
    operator: Literal["gt", "lt", "gte", "lte", "eq", "ne", "in", "not_in"] = Field(..., description="Comparison operator")
    value: Any = Field(..., description="Value to compare against")
    weight: float = Field(1.0, description="Weight of this filter in scoring")


class StockData(BaseModel):
    """Stock data for screening."""

    symbol: str = Field(..., description="Stock symbol")
    name: str = Field(..., description="Company name")
    sector: str | None = Field(None, description="Sector")
    industry: str | None = Field(None, description="Industry")
    market_cap: float | None = Field(None, description="Market capitalization")

    # Valuation metrics
    pe_ratio: float | None = Field(None, description="Price-to-earnings ratio")
    pb_ratio: float | None = Field(None, description="Price-to-book ratio")
    ps_ratio: float | None = Field(None, description="Price-to-sales ratio")
    peg_ratio: float | None = Field(None, description="Price/earnings to growth ratio")

    # Financial metrics
    revenue_growth: float | None = Field(None, description="Revenue growth rate")
    earnings_growth: float | None = Field(None, description="Earnings growth rate")
    roe: float | None = Field(None, description="Return on equity")
    roa: float | None = Field(None, description="Return on assets")
    debt_to_equity: float | None = Field(None, description="Debt-to-equity ratio")

    # Market metrics
    beta: float | None = Field(None, description="Beta coefficient")
    dividend_yield: float | None = Field(None, description="Dividend yield")
    volume: int | None = Field(None, description="Average trading volume")


class ScreeningScore(BaseModel):
    """Screening score for a stock."""

    symbol: str = Field(..., description="Stock symbol")
    total_score: float = Field(..., description="Total screening score")
    component_scores: dict[str, float] = Field(..., description="Individual component scores")
    rank: int | None = Field(None, description="Rank among screened stocks")
    percentile: float | None = Field(None, description="Percentile ranking")


class ScreeningResult(BaseModel):
    """Result of stock screening."""

    filters_applied: list[ScreeningFilter] = Field(..., description="Filters that were applied")
    total_universe: int = Field(..., description="Total number of stocks in universe")
    filtered_count: int = Field(..., description="Number of stocks passing filters")

    # Results
    stocks: list[StockData] = Field(..., description="Stocks that passed screening")
    scores: list[ScreeningScore] = Field(..., description="Screening scores")

    # Metadata
    screening_date: datetime = Field(..., description="Date when screening was performed")
    execution_time: float = Field(..., description="Execution time in seconds")


class ScreeningSummary(BaseModel):
    """Summary of screening results."""

    total_screened: int = Field(..., description="Total number of stocks screened")
    passed_filters: int = Field(..., description="Number passing all filters")
    top_performers: list[str] = Field(..., description="Top performing symbols")

    # Statistics
    avg_score: float = Field(..., description="Average screening score")
    score_std: float = Field(..., description="Standard deviation of scores")
    score_range: tuple[float, float] = Field(..., description="Score range (min, max)")
