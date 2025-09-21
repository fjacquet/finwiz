"""
Stock screening module for FinWiz quantitative analysis.

This module provides comprehensive stock screening capabilities for fundamental
analysis, technical filtering, and multi-criteria stock selection based on
various financial metrics and market indicators.
"""

from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np
from pydantic import BaseModel, Field, validator

from finwiz.quantitative.config import ScreeningCriteria, get_screener_config
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


class ScreeningResult(BaseModel):
    """Result of stock screening."""

    symbol: str = Field(..., description="Stock symbol")
    company_name: str = Field(..., description="Company name")
    sector: str = Field(..., description="Sector")
    industry: str = Field(..., description="Industry")
    stock_data: StockData = Field(..., description="Complete stock data")
    screening_score: ScreeningScore = Field(..., description="Screening score")
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
    screening_criteria: list[ScreeningFilter] = Field(..., description="Applied screening criteria")
    execution_time: float = Field(..., description="Screening execution time")

    class Config:
        """Pydantic configuration."""

        extra = "forbid"


class StockScreener:
    """
    Professional stock screening engine for fundamental analysis.

    Provides comprehensive screening capabilities with multiple criteria,
    scoring systems, and ranking algorithms for stock selection.
    """

    def __init__(self) -> None:
        """Initialize the stock screener."""
        self.config = get_screener_config()
        self._data_cache = {}
        self._universe_cache = {}

        # Stock universe mappings
        self.universe_symbols = {
            ScreeningUniverse.SP500: self._get_sp500_symbols(),
            ScreeningUniverse.NASDAQ100: self._get_nasdaq100_symbols(),
            ScreeningUniverse.RUSSELL2000: self._get_russell2000_symbols(),
            ScreeningUniverse.DOW30: self._get_dow30_symbols(),
        }

    def screen_stocks(
        self,
        filters: list[ScreeningFilter],
        universe: ScreeningUniverse = ScreeningUniverse.SP500,
        custom_symbols: list[str] | None = None,
        max_results: int = 50,
        sort_by: str = "total_score",
        sort_order: SortOrder = SortOrder.DESCENDING,
    ) -> tuple[list[ScreeningResult], ScreeningSummary]:
        """
        Screen stocks based on specified criteria.

        Args:
            filters: List of screening filters
            universe: Stock universe to screen
            custom_symbols: Custom list of symbols (if universe is CUSTOM)
            max_results: Maximum number of results to return
            sort_by: Field to sort results by
            sort_order: Sort order (ascending or descending)

        Returns:
            Tuple of (screening_results, summary)

        """
        start_time = datetime.now()

        try:
            # Get stock universe
            if universe == ScreeningUniverse.CUSTOM and custom_symbols:
                symbols = custom_symbols
            else:
                symbols = self.universe_symbols.get(universe, [])

            if not symbols:
                raise ValueError(f"No symbols found for universe {universe}")

            logger.info(f"Screening {len(symbols)} stocks with {len(filters)} criteria")

            # Fetch stock data
            stock_data_list = self._fetch_stock_data(symbols)

            # Apply screening filters
            filtered_stocks = self._apply_filters(stock_data_list, filters)

            # Calculate screening scores
            scored_stocks = self._calculate_scores(filtered_stocks, filters)

            # Sort and rank results
            sorted_stocks = self._sort_and_rank(scored_stocks, sort_by, sort_order)

            # Limit results
            final_results = sorted_stocks[:max_results]

            # Generate screening results
            screening_results = []
            for stock_data, score in final_results:
                recommendation = self._generate_recommendation(stock_data, score)

                result = ScreeningResult(
                    symbol=stock_data.symbol,
                    company_name=stock_data.company_name,
                    sector=stock_data.sector,
                    industry=stock_data.industry,
                    stock_data=stock_data,
                    screening_score=score,
                    recommendation=recommendation,
                )
                screening_results.append(result)

            # Generate summary
            execution_time = (datetime.now() - start_time).total_seconds()
            summary = self._generate_summary(len(symbols), len(filtered_stocks), filters, execution_time, screening_results)

            logger.info(f"Screening completed in {execution_time:.2f}s, found {len(screening_results)} results")

            return screening_results, summary

        except Exception as e:
            logger.error(f"Stock screening failed: {e}")
            raise

    def _fetch_stock_data(self, symbols: list[str]) -> list[StockData]:
        """Fetch stock data for screening."""
        # In a real implementation, this would fetch data from APIs
        # For now, we'll generate mock data
        stock_data_list = []

        for symbol in symbols:
            try:
                # Generate mock data (in real implementation, fetch from APIs)
                stock_data = self._generate_mock_stock_data(symbol)
                stock_data_list.append(stock_data)

            except Exception as e:
                logger.warning(f"Failed to fetch data for {symbol}: {e}")
                continue

        return stock_data_list

    def _generate_mock_stock_data(self, symbol: str) -> StockData:
        """Generate mock stock data for testing."""
        import random

        # Mock company data
        sectors = ["Technology", "Healthcare", "Financial", "Consumer", "Industrial", "Energy"]
        industries = ["Software", "Biotechnology", "Banking", "Retail", "Manufacturing", "Oil & Gas"]

        return StockData(
            symbol=symbol,
            company_name=f"{symbol} Corporation",
            sector=random.choice(sectors),
            industry=random.choice(industries),
            market_cap=random.uniform(1e9, 500e9),
            price=random.uniform(10, 500),
            pe_ratio=random.uniform(5, 50) if random.random() > 0.1 else None,
            pb_ratio=random.uniform(0.5, 10) if random.random() > 0.1 else None,
            ps_ratio=random.uniform(0.5, 20) if random.random() > 0.1 else None,
            dividend_yield=random.uniform(0, 0.08) if random.random() > 0.3 else None,
            roe=random.uniform(-0.2, 0.4) if random.random() > 0.1 else None,
            roa=random.uniform(-0.1, 0.2) if random.random() > 0.1 else None,
            debt_to_equity=random.uniform(0, 2) if random.random() > 0.1 else None,
            current_ratio=random.uniform(0.5, 5) if random.random() > 0.1 else None,
            quick_ratio=random.uniform(0.3, 3) if random.random() > 0.1 else None,
            revenue_growth=random.uniform(-0.3, 0.5) if random.random() > 0.1 else None,
            earnings_growth=random.uniform(-0.5, 1.0) if random.random() > 0.1 else None,
            eps_growth=random.uniform(-0.5, 1.0) if random.random() > 0.1 else None,
            rsi=random.uniform(20, 80) if random.random() > 0.1 else None,
            price_change_1m=random.uniform(-0.3, 0.3) if random.random() > 0.1 else None,
            price_change_3m=random.uniform(-0.5, 0.5) if random.random() > 0.1 else None,
            price_change_1y=random.uniform(-0.8, 1.5) if random.random() > 0.1 else None,
            volume_avg_3m=random.uniform(100000, 10000000) if random.random() > 0.1 else None,
            beta=random.uniform(0.3, 2.5) if random.random() > 0.1 else None,
            analyst_rating=random.uniform(1, 5) if random.random() > 0.2 else None,
            price_target=random.uniform(10, 600) if random.random() > 0.2 else None,
        )

    def _apply_filters(self, stock_data_list: list[StockData], filters: list[ScreeningFilter]) -> list[StockData]:
        """Apply screening filters to stock data."""
        filtered_stocks = []

        for stock_data in stock_data_list:
            passes_all_filters = True

            for filter_criteria in filters:
                if not self._passes_filter(stock_data, filter_criteria):
                    passes_all_filters = False
                    break

            if passes_all_filters:
                filtered_stocks.append(stock_data)

        return filtered_stocks

    def _passes_filter(self, stock_data: StockData, filter_criteria: ScreeningFilter) -> bool:
        """Check if stock passes individual filter."""
        criteria = filter_criteria.criteria
        min_val = filter_criteria.min_value
        max_val = filter_criteria.max_value

        # Get the value for the criteria
        value = self._get_criteria_value(stock_data, criteria)

        if value is None:
            return False  # Missing data fails the filter

        # Check min value
        if min_val is not None and value < min_val:
            return False

        # Check max value
        if max_val is not None and value > max_val:
            return False

        return True

    def _get_criteria_value(self, stock_data: StockData, criteria: ScreeningCriteria) -> float | None:
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

    def _calculate_scores(
        self, stock_data_list: list[StockData], filters: list[ScreeningFilter]
    ) -> list[tuple[StockData, ScreeningScore]]:
        """Calculate screening scores for stocks."""
        scored_stocks = []

        for stock_data in stock_data_list:
            criteria_scores = {}
            total_score = 0.0
            total_weight = 0.0

            for filter_criteria in filters:
                score = self._calculate_criteria_score(stock_data, filter_criteria)
                criteria_scores[filter_criteria.criteria.value] = score

                weighted_score = score * filter_criteria.weight
                total_score += weighted_score
                total_weight += filter_criteria.weight

            # Normalize total score
            if total_weight > 0:
                total_score = total_score / total_weight

            screening_score = ScreeningScore(
                symbol=stock_data.symbol,
                total_score=total_score,
                criteria_scores=criteria_scores,
                rank=0,  # Will be set during ranking
                percentile=0.0,  # Will be set during ranking
            )

            scored_stocks.append((stock_data, screening_score))

        return scored_stocks

    def _calculate_criteria_score(self, stock_data: StockData, filter_criteria: ScreeningFilter) -> float:
        """Calculate score for individual criteria."""
        value = self._get_criteria_value(stock_data, filter_criteria.criteria)

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

    def _sort_and_rank(
        self, scored_stocks: list[tuple[StockData, ScreeningScore]], sort_by: str, sort_order: SortOrder
    ) -> list[tuple[StockData, ScreeningScore]]:
        """Sort and rank screening results."""
        # Sort by specified field
        if sort_by == "total_score":

            def key_func(x: tuple[StockData, ScreeningScore]) -> float:
                return x[1].total_score
        else:
            # Sort by stock data field
            def key_func(x: tuple[StockData, ScreeningScore]) -> float:
                return getattr(x[0], sort_by, 0) or 0

        reverse = sort_order == SortOrder.DESCENDING
        sorted_stocks = sorted(scored_stocks, key=key_func, reverse=reverse)

        # Update ranks and percentiles
        total_stocks = len(sorted_stocks)
        for i, (stock_data, score) in enumerate(sorted_stocks):
            score.rank = i + 1
            score.percentile = ((total_stocks - i) / total_stocks) * 100

        return sorted_stocks

    def _generate_recommendation(self, stock_data: StockData, score: ScreeningScore) -> str:
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

    def _generate_summary(
        self,
        total_screened: int,
        passed_filters: int,
        filters: list[ScreeningFilter],
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

    def create_custom_screen(self, name: str, filters: list[ScreeningFilter], description: str = "") -> dict[str, Any]:
        """Create a custom screening configuration."""
        return {
            "name": name,
            "description": description,
            "filters": [filter_obj.dict() for filter_obj in filters],
            "created_at": datetime.now().isoformat(),
        }

    def get_predefined_screens(self) -> dict[str, list[ScreeningFilter]]:
        """Get predefined screening configurations."""
        return {
            "value_stocks": [
                ScreeningFilter(criteria=ScreeningCriteria.PE_RATIO, min_value=5, max_value=15),
                ScreeningFilter(criteria=ScreeningCriteria.PB_RATIO, min_value=0.5, max_value=2.0),
                ScreeningFilter(criteria=ScreeningCriteria.DEBT_TO_EQUITY, max_value=0.5),
                ScreeningFilter(criteria=ScreeningCriteria.ROE, min_value=0.15),
            ],
            "growth_stocks": [
                ScreeningFilter(criteria=ScreeningCriteria.REVENUE_GROWTH, min_value=0.15),
                ScreeningFilter(criteria=ScreeningCriteria.EARNINGS_GROWTH, min_value=0.20),
                ScreeningFilter(criteria=ScreeningCriteria.ROE, min_value=0.20),
                ScreeningFilter(criteria=ScreeningCriteria.PE_RATIO, max_value=30),
            ],
            "dividend_stocks": [
                ScreeningFilter(criteria=ScreeningCriteria.DIVIDEND_YIELD, min_value=0.03),
                ScreeningFilter(criteria=ScreeningCriteria.PE_RATIO, max_value=20),
                ScreeningFilter(criteria=ScreeningCriteria.DEBT_TO_EQUITY, max_value=0.6),
                ScreeningFilter(criteria=ScreeningCriteria.ROE, min_value=0.12),
            ],
            "quality_stocks": [
                ScreeningFilter(criteria=ScreeningCriteria.ROE, min_value=0.15),
                ScreeningFilter(criteria=ScreeningCriteria.ROA, min_value=0.08),
                ScreeningFilter(criteria=ScreeningCriteria.DEBT_TO_EQUITY, max_value=0.4),
                ScreeningFilter(criteria=ScreeningCriteria.MARKET_CAP, min_value=5e9),
            ],
        }

    def _get_sp500_symbols(self) -> list[str]:
        """Get S&P 500 symbols (mock implementation)."""
        # In real implementation, fetch from reliable source
        return ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "BRK.B", "UNH", "JNJ"]

    def _get_nasdaq100_symbols(self) -> list[str]:
        """Get NASDAQ 100 symbols (mock implementation)."""
        return ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX", "ADBE", "CRM"]

    def _get_russell2000_symbols(self) -> list[str]:
        """Get Russell 2000 symbols (mock implementation)."""
        return ["AMC", "GME", "BBBY", "CLOV", "WISH", "PLTR", "SOFI", "HOOD", "RIVN", "LCID"]

    def _get_dow30_symbols(self) -> list[str]:
        """Get Dow 30 symbols (mock implementation)."""
        return ["AAPL", "MSFT", "UNH", "GS", "HD", "CAT", "AMGN", "CRM", "V", "BA"]

    def analyze_screening_performance(self, results: list[ScreeningResult], time_period: int = 30) -> dict[str, Any]:
        """
        Analyze historical performance of screening results.

        Args:
            results: Screening results to analyze
            time_period: Time period in days for performance analysis

        Returns:
            Performance analysis results

        """
        # Mock performance analysis
        # In real implementation, would fetch historical price data

        total_return = np.random.normal(0.05, 0.15)  # Mock 5% average return
        win_rate = np.random.uniform(0.4, 0.7)  # Mock win rate
        sharpe_ratio = np.random.uniform(0.5, 2.0)  # Mock Sharpe ratio

        return {
            "total_return": total_return,
            "annualized_return": total_return * (365 / time_period),
            "win_rate": win_rate,
            "sharpe_ratio": sharpe_ratio,
            "number_of_stocks": len(results),
            "analysis_period_days": time_period,
            "best_performer": results[0].symbol if results else None,
            "worst_performer": results[-1].symbol if results else None,
        }
