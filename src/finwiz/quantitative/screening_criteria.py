"""
Screening criteria definitions and filtering logic for stock screening.

This module provides the core criteria classes and filtering mechanisms
for the stock screening engine.
"""

from typing import Any

from pydantic import BaseModel, Field, validator

from finwiz.quantitative.config import ScreeningCriteria
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class ScreeningFilter(BaseModel):
    """Individual screening filter."""

    criteria: ScreeningCriteria = Field(..., description="Screening criteria")
    min_value: float | None = Field(None, description="Minimum value")
    max_value: float | None = Field(None, description="Maximum value")
    weight: float = Field(default=1.0, ge=0, description="Filter weight in scoring")

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        extra = "forbid"

    @validator("max_value")
    def validate_max_value(cls, v: float | None, values: dict[str, Any]) -> float | None:
        """Validate max_value is greater than min_value."""
        if v is not None and "min_value" in values:
            min_val = values.get("min_value")
            if min_val is not None and v <= min_val:
                raise ValueError("max_value must be greater than min_value")
        return v


class ScreeningScore(BaseModel):
    """Screening score for a stock."""

    symbol: str = Field(..., description="Stock symbol")
    total_score: float = Field(..., description="Total screening score")
    criteria_scores: dict[str, float] = Field(..., description="Individual criteria scores")
    rank: int = Field(..., description="Rank in screening results")
    percentile: float = Field(..., description="Percentile rank")

    class Config:
        """Pydantic configuration."""

        extra = "forbid"


class CriteriaEvaluator:
    """Evaluates individual screening criteria."""

    @staticmethod
    def get_criteria_value(stock_data: "StockData", criteria: ScreeningCriteria) -> float | None:
        """Get value for specific screening criteria."""
        criteria_mapping = {
            ScreeningCriteria.MARKET_CAP: stock_data.market_cap,
            ScreeningCriteria.PE_RATIO: stock_data.pe_ratio,
            ScreeningCriteria.PB_RATIO: stock_data.pb_ratio,
            ScreeningCriteria.DIVIDEND_YIELD: stock_data.dividend_yield,
            ScreeningCriteria.ROE: stock_data.roe,
            ScreeningCriteria.ROA: stock_data.roa,
            ScreeningCriteria.DEBT_TO_EQUITY: stock_data.debt_to_equity,
            ScreeningCriteria.REVENUE_GROWTH: stock_data.revenue_growth,
            ScreeningCriteria.EARNINGS_GROWTH: stock_data.earnings_growth,
            ScreeningCriteria.PRICE_MOMENTUM: stock_data.price_change_3m,
            ScreeningCriteria.VOLUME: stock_data.volume_avg_3m,
            ScreeningCriteria.BETA: stock_data.beta,
        }

        return criteria_mapping.get(criteria)

    @staticmethod
    def passes_filter(stock_data: "StockData", filter_criteria: ScreeningFilter) -> bool:
        """Check if stock passes individual filter."""
        criteria = filter_criteria.criteria
        min_val = filter_criteria.min_value
        max_val = filter_criteria.max_value

        # Get the value for the criteria
        value = CriteriaEvaluator.get_criteria_value(stock_data, criteria)

        if value is None:
            return False  # Missing data fails the filter

        # Check min value
        if min_val is not None and value < min_val:
            return False

        # Check max value
        if max_val is not None and value > max_val:
            return False

        return True

    @staticmethod
    def calculate_criteria_score(stock_data: "StockData", filter_criteria: ScreeningFilter) -> float:
        """Calculate score for individual criteria."""
        import numpy as np

        value = CriteriaEvaluator.get_criteria_value(stock_data, filter_criteria.criteria)

        if value is None:
            return 0.0

        # Normalize score based on criteria type
        criteria = filter_criteria.criteria

        if criteria in [
            ScreeningCriteria.ROE,
            ScreeningCriteria.ROA,
            ScreeningCriteria.REVENUE_GROWTH,
            ScreeningCriteria.EARNINGS_GROWTH,
            ScreeningCriteria.DIVIDEND_YIELD,
        ]:
            # Higher is better
            return min(max(value * 100, 0), 100)  # Scale to 0-100

        elif criteria in [ScreeningCriteria.PE_RATIO, ScreeningCriteria.PB_RATIO, ScreeningCriteria.DEBT_TO_EQUITY]:
            # Lower is better (within reason)
            if criteria == ScreeningCriteria.PE_RATIO:
                optimal_range = (10, 20)
            elif criteria == ScreeningCriteria.PB_RATIO:
                optimal_range = (1, 3)
            else:  # DEBT_TO_EQUITY
                optimal_range = (0, 0.5)

            if optimal_range[0] <= value <= optimal_range[1]:
                return 100
            elif value < optimal_range[0]:
                return 50 + (value / optimal_range[0]) * 50
            else:
                return max(100 - (value - optimal_range[1]) * 20, 0)

        elif criteria == ScreeningCriteria.MARKET_CAP:
            # Logarithmic scale for market cap
            return min(np.log10(value / 1e9) * 20, 100)

        else:
            # Default scoring
            return min(max(value * 50, 0), 100)


# Import StockData for type hints
from finwiz.quantitative.screening_filters import StockData  # noqa: E402, F401
