"""
Stock filtering and data models for stock screening.

This module provides stock data models, filtering logic, and result structures
for the stock screening engine.
"""

from enum import Enum

from pydantic import BaseModel, Field

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class ScreeningUniverse(str, Enum):
    """Stock screening universes."""

    SP500 = "SP500"
    NASDAQ100 = "NASDAQ100"
    RUSSELL2000 = "RUSSELL2000"
    DOW30 = "DOW30"
    CUSTOM = "CUSTOM"
    ALL_US = "ALL_US"


class SortOrder(str, Enum):
    """Sort order for screening results."""

    ASCENDING = "asc"
    DESCENDING = "desc"


class StockData(BaseModel):
    """Stock data for screening."""

    symbol: str = Field(..., description="Stock symbol")
    company_name: str = Field(..., description="Company name")
    sector: str = Field(..., description="Sector")
    industry: str = Field(..., description="Industry")
    market_cap: float = Field(..., description="Market capitalization")
    price: float = Field(..., description="Current stock price")

    # Fundamental metrics
    pe_ratio: float | None = Field(None, description="Price-to-earnings ratio")
    pb_ratio: float | None = Field(None, description="Price-to-book ratio")
    ps_ratio: float | None = Field(None, description="Price-to-sales ratio")
    dividend_yield: float | None = Field(None, description="Dividend yield")
    roe: float | None = Field(None, description="Return on equity")
    roa: float | None = Field(None, description="Return on assets")
    debt_to_equity: float | None = Field(None, description="Debt-to-equity ratio")
    current_ratio: float | None = Field(None, description="Current ratio")
    quick_ratio: float | None = Field(None, description="Quick ratio")

    # Growth metrics
    revenue_growth: float | None = Field(None, description="Revenue growth rate")
    earnings_growth: float | None = Field(None, description="Earnings growth rate")
    eps_growth: float | None = Field(None, description="EPS growth rate")

    # Technical metrics
    rsi: float | None = Field(None, description="RSI indicator")
    price_change_1m: float | None = Field(None, description="1-month price change")
    price_change_3m: float | None = Field(None, description="3-month price change")
    price_change_1y: float | None = Field(None, description="1-year price change")
    volume_avg_3m: float | None = Field(None, description="3-month average volume")
    beta: float | None = Field(None, description="Beta coefficient")

    # Additional metrics
    analyst_rating: float | None = Field(None, description="Average analyst rating")
    price_target: float | None = Field(None, description="Average price target")

    class Config:
        """Pydantic configuration."""

        extra = "forbid"


class ScreeningResult(BaseModel):
    """Result of stock screening."""

    symbol: str = Field(..., description="Stock symbol")
    company_name: str = Field(..., description="Company name")
    sector: str = Field(..., description="Sector")
    industry: str = Field(..., description="Industry")
    stock_data: StockData = Field(..., description="Complete stock data")
    screening_score: "ScreeningScore" = Field(..., description="Screening score")
    recommendation: str = Field(..., description="Screening recommendation")

    class Config:
        """Pydantic configuration."""

        extra = "forbid"


class ScreeningSummary(BaseModel):
    """Summary of screening results."""

    total_stocks_screened: int = Field(..., description="Total stocks screened")
    stocks_passed: int = Field(..., description="Stocks that passed screening")
    pass_rate: float = Field(..., description="Pass rate percentage")
    top_sectors: list[str] = Field(..., description="Top performing sectors")
    screening_criteria: list["ScreeningFilter"] = Field(..., description="Applied screening criteria")
    execution_time: float = Field(..., description="Screening execution time")

    class Config:
        """Pydantic configuration."""

        extra = "forbid"


class StockFilter:
    """Filters stocks based on screening criteria."""

    @staticmethod
    def apply_filters(stock_data_list: list[StockData], filters: list["ScreeningFilter"]) -> list[StockData]:
        """Apply screening filters to stock data."""
        from finwiz.quantitative.screening_criteria import CriteriaEvaluator

        filtered_stocks = []

        for stock_data in stock_data_list:
            passes_all_filters = True

            for filter_criteria in filters:
                if not CriteriaEvaluator.passes_filter(stock_data, filter_criteria):
                    passes_all_filters = False
                    break

            if passes_all_filters:
                filtered_stocks.append(stock_data)

        return filtered_stocks

    @staticmethod
    def sort_and_rank(scored_stocks: list[tuple[StockData, "ScreeningScore"]], sort_by: str, sort_order: SortOrder) -> list[tuple[StockData, "ScreeningScore"]]:
        """Sort and rank screening results."""
        # Sort by specified field
        if sort_by == "total_score":

            def key_func(x: tuple[StockData, "ScreeningScore"]) -> float:
                return x[1].total_score
        else:
            # Sort by stock data field
            def key_func(x: tuple[StockData, "ScreeningScore"]) -> float:
                return getattr(x[0], sort_by, 0) or 0

        reverse = sort_order == SortOrder.DESCENDING
        sorted_stocks = sorted(scored_stocks, key=key_func, reverse=reverse)

        # Update ranks and percentiles
        total_stocks = len(sorted_stocks)
        for i, (stock_data, score) in enumerate(sorted_stocks):
            score.rank = i + 1
            score.percentile = ((total_stocks - i) / total_stocks) * 100

        return sorted_stocks

    @staticmethod
    def generate_recommendation(stock_data: StockData, score: "ScreeningScore") -> str:
        """Generate recommendation based on screening score."""
        if score.total_score >= 80:
            return "STRONG BUY"
        elif score.total_score >= 60:
            return "BUY"
        elif score.total_score >= 40:
            return "HOLD"
        elif score.total_score >= 20:
            return "WEAK HOLD"
        else:
            return "AVOID"

    @staticmethod
    def generate_summary(
        total_screened: int,
        passed_filters: int,
        filters: list["ScreeningFilter"],
        execution_time: float,
        results: list[ScreeningResult],
    ) -> ScreeningSummary:
        """Generate screening summary."""
        pass_rate = (passed_filters / total_screened) * 100 if total_screened > 0 else 0

        # Get top sectors
        sector_counts = {}
        for result in results:
            sector = result.sector
            sector_counts[sector] = sector_counts.get(sector, 0) + 1

        top_sectors = sorted(sector_counts.keys(), key=lambda x: sector_counts[x], reverse=True)[:5]

        return ScreeningSummary(
            total_stocks_screened=total_screened,
            stocks_passed=passed_filters,
            pass_rate=pass_rate,
            top_sectors=top_sectors,
            screening_criteria=filters,
            execution_time=execution_time,
        )


# Import for type hints
from finwiz.quantitative.screening_criteria import ScreeningFilter, ScreeningScore  # noqa: E402, F401
