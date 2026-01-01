"""
Stock screening module for FinWiz quantitative analysis.

This module provides comprehensive stock screening capabilities for fundamental
analysis, technical filtering, and multi-criteria stock selection based on
various financial metrics and market indicators.

This is the main entry point that re-exports from specialized modules:
- screening_criteria: Criteria definitions and evaluation
- screening_filters: Stock data models and filtering logic
"""

from datetime import datetime
from typing import Any

from finwiz.quantitative.config import ScreeningCriteria, get_screener_config
from finwiz.quantitative.screening_criteria import ScreeningFilter, ScreeningScore
from finwiz.quantitative.screening_data_generator import MockDataGenerator
from finwiz.quantitative.screening_filters import (
    ScreeningResult,
    ScreeningSummary,
    ScreeningUniverse,
    SortOrder,
    StockData,
    StockFilter,
)
from finwiz.quantitative.screening_universes import UniverseProvider
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

# Re-export for backward compatibility
__all__ = [
    "ScreeningUniverse",
    "SortOrder",
    "ScreeningFilter",
    "StockData",
    "ScreeningScore",
    "ScreeningResult",
    "ScreeningSummary",
    "StockScreener",
]


class StockScreener:
    """
    Professional stock screening engine for fundamental analysis.

    Provides comprehensive screening capabilities with multiple criteria,
    scoring systems, and ranking algorithms for stock selection.
    """

    def __init__(self) -> None:
        """Initialize the stock screener."""
        self.config = get_screener_config()
        self._data_cache: dict[str, Any] = {}
        self._universe_cache: dict[str, Any] = {}

        # Stock universe mappings
        self.universe_symbols = {
            ScreeningUniverse.SP500: UniverseProvider.get_sp500_symbols(),
            ScreeningUniverse.NASDAQ100: UniverseProvider.get_nasdaq100_symbols(),
            ScreeningUniverse.RUSSELL2000: UniverseProvider.get_russell2000_symbols(),
            ScreeningUniverse.DOW30: UniverseProvider.get_dow30_symbols(),
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
        from finwiz.quantitative.screening_criteria import CriteriaEvaluator

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
            filtered_stocks = StockFilter.apply_filters(stock_data_list, filters)

            # Calculate screening scores
            scored_stocks = self._calculate_scores(filtered_stocks, filters, CriteriaEvaluator)

            # Sort and rank results
            sorted_stocks = StockFilter.sort_and_rank(scored_stocks, sort_by, sort_order)

            # Limit results
            final_results = sorted_stocks[:max_results]

            # Generate screening results
            screening_results = []
            for stock_data, score in final_results:
                recommendation = StockFilter.generate_recommendation(stock_data, score)

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
            summary = StockFilter.generate_summary(len(symbols), len(filtered_stocks), filters, execution_time, screening_results)

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
                stock_data = MockDataGenerator.generate_stock_data(symbol)
                stock_data_list.append(stock_data)

            except Exception as e:
                logger.warning(f"Failed to fetch data for {symbol}: {e}")
                continue

        return stock_data_list

    def _calculate_scores(self, stock_data_list: list[StockData], filters: list[ScreeningFilter], criteria_evaluator: Any) -> list[tuple[StockData, ScreeningScore]]:
        """Calculate screening scores for stocks."""
        scored_stocks = []

        for stock_data in stock_data_list:
            criteria_scores: dict[str, float] = {}
            total_score = 0.0
            total_weight = 0.0

            for filter_criteria in filters:
                score = criteria_evaluator.calculate_criteria_score(stock_data, filter_criteria)
                # Note: filter_criteria.criteria is already a string due to use_enum_values=True
                # Don't call .value on it
                criteria_key = filter_criteria.criteria if isinstance(filter_criteria.criteria, str) else filter_criteria.criteria.value
                criteria_scores[criteria_key] = score

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

    def analyze_screening_performance(self, results: list[ScreeningResult], time_period: int = 30) -> dict[str, Any]:
        """
        Analyze historical performance of screening results.

        Args:
            results: Screening results to analyze
            time_period: Time period in days for performance analysis

        Returns:
            Performance analysis results

        """
        import random

        # Mock performance analysis
        # In real implementation, would fetch historical price data

        total_return = random.gauss(0.05, 0.15)  # Mock 5% average return
        win_rate = random.uniform(0.4, 0.7)  # Mock win rate
        sharpe_ratio = random.uniform(0.5, 2.0)  # Mock Sharpe ratio

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
