"""
Quantitative analysis tool for FinWiz crews.

This tool provides quantitative analysis capabilities including backtesting,
technical analysis, and performance metrics calculation for integration
into Stock, ETF, and Crypto crews.

Delegates to specialized analyzer modules for each analysis type.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
from crewai.tools import BaseTool
from pydantic import BaseModel

from finwiz.quantitative.backtesting import get_backtesting_engine
from finwiz.quantitative.data import get_historical_data_manager
from finwiz.quantitative.performance import get_performance_analyzer
from finwiz.quantitative.technical import TechnicalAnalysisEngine
from finwiz.schemas.tools import QuantitativeAnalysisInput
from finwiz.tools.logger import get_logger
from finwiz.tools.quantitative_backtesting_analyzer import perform_backtesting
from finwiz.tools.quantitative_comprehensive_analyzer import perform_comprehensive_analysis
from finwiz.tools.quantitative_performance_analyzer import perform_performance_analysis
from finwiz.tools.quantitative_technical_analyzer import perform_technical_analysis


class QuantitativeAnalysisTool(BaseTool):
    """
    Tool for performing quantitative analysis on financial instruments.

    Provides comprehensive quantitative analysis including:
    - Technical analysis with multiple indicators
    - Strategy backtesting with performance metrics
    - Risk-adjusted performance analysis
    - Investment recommendations based on quantitative signals
    """

    name: str = "Quantitative Analysis Tool"
    description: str = (
        "Performs comprehensive quantitative analysis including technical analysis, "
        "backtesting, and performance metrics calculation. Supports stocks, ETFs, and cryptocurrencies. "
        "Use this tool to get data-driven investment insights and recommendations."
    )
    args_schema: type[BaseModel] = QuantitativeAnalysisInput

    def _run(
        self,
        symbol: str,
        asset_class: str,
        analysis_type: str = "comprehensive",
        timeframe: str = "1y",
        strategy: str = "sma_crossover",
        benchmark: str | None = None,
        prefetched_data: pd.DataFrame | None = None,
    ) -> str:
        """
        Execute quantitative analysis.

        Args:
            symbol: Symbol to analyze (e.g., AAPL, SPY, BTC-USD)
            asset_class: Asset class: 'stock', 'etf', or 'crypto'
            analysis_type: Type of analysis: 'technical', 'backtest', 'performance', or 'comprehensive'
            timeframe: Analysis timeframe (e.g., '1y', '2y', '5y')
            strategy: Strategy for backtesting
            benchmark: Benchmark symbol for comparison
            prefetched_data: Optional pre-fetched historical data from batch operation

        Returns:
            JSON string with quantitative analysis results

        """
        logger = get_logger(f"{__name__}.{self.__class__.__name__}")

        try:
            # Create input data object
            input_data = QuantitativeAnalysisInput(
                symbol=symbol,
                asset_class=asset_class,
                analysis_type=analysis_type,
                timeframe=timeframe,
                strategy=strategy,
                benchmark=benchmark,
            )

            logger.info(f"Starting quantitative analysis for {input_data.symbol}")

            # Determine date range
            end_date = datetime.now()
            start_date = self._calculate_start_date(input_data.timeframe, end_date)

            # Get historical data
            data = self._get_historical_data(input_data, start_date, end_date, prefetched_data, logger)
            if isinstance(data, str):
                return data  # Error message

            # Initialize analysis engines
            technical_engine = TechnicalAnalysisEngine()
            backtesting_engine = get_backtesting_engine()
            performance_analyzer = get_performance_analyzer()

            # Perform analysis based on type
            result = self._dispatch_analysis(
                input_data,
                data,
                start_date,
                end_date,
                technical_engine,
                backtesting_engine,
                performance_analyzer,
            )

            logger.info(f"Quantitative analysis completed for {input_data.symbol}")
            return result

        except Exception as e:
            logger.error(f"Error in quantitative analysis: {e}")
            return f"Error performing quantitative analysis: {str(e)}"

    def _calculate_start_date(self, timeframe: str, end_date: datetime) -> datetime:
        """Calculate start date based on timeframe."""
        timeframe_days = {"1y": 365, "2y": 730, "5y": 1825}
        days = timeframe_days.get(timeframe, 365)
        return end_date - timedelta(days=days)

    def _get_historical_data(
        self,
        input_data: QuantitativeAnalysisInput,
        start_date: datetime,
        end_date: datetime,
        prefetched_data: pd.DataFrame | None,
        logger,
    ) -> pd.DataFrame | str:
        """Get historical data from prefetch or API."""
        if prefetched_data is not None and not prefetched_data.empty:
            logger.debug(f"Using pre-fetched data for {input_data.symbol} (source: batch)")
            return prefetched_data

        logger.debug(f"Fetching live data for {input_data.symbol} (source: API)")
        data_manager = get_historical_data_manager()

        try:
            data = data_manager.fetch_historical_data(input_data.symbol, start_date, end_date)
            if data.empty:
                return f"No data available for {input_data.symbol}"
            return data
        except Exception as e:
            logger.error(f"Error fetching data for {input_data.symbol}: {e}")
            return f"Error fetching data: {str(e)}"

    def _dispatch_analysis(
        self,
        input_data: QuantitativeAnalysisInput,
        data: pd.DataFrame,
        start_date: datetime,
        end_date: datetime,
        technical_engine: TechnicalAnalysisEngine,
        backtesting_engine,
        performance_analyzer,
    ) -> str:
        """Dispatch to appropriate analysis function."""
        if input_data.analysis_type == "technical":
            return perform_technical_analysis(data, input_data, technical_engine)
        elif input_data.analysis_type == "backtest":
            return perform_backtesting(data, input_data, start_date, end_date, backtesting_engine)
        elif input_data.analysis_type == "performance":
            return perform_performance_analysis(data, input_data, performance_analyzer)
        else:  # comprehensive
            return perform_comprehensive_analysis(
                data,
                input_data,
                start_date,
                end_date,
                technical_engine,
                backtesting_engine,
                performance_analyzer,
            )


def get_quantitative_analysis_tool() -> QuantitativeAnalysisTool:
    """Create quantitative analysis tool."""
    return QuantitativeAnalysisTool()
