"""
Backtesting functions for quantitative analysis tool.

Extracted from quantitative_analysis_tool.py for modularity.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from finwiz.quantitative.backtesting import SimpleMovingAverageStrategy
from finwiz.schemas.quantitative_crew import QuantitativeBacktestResult
from finwiz.tools.logger import get_logger

if TYPE_CHECKING:
    import pandas as pd

    from finwiz.quantitative.backtesting import BacktestingEngine
    from finwiz.schemas.tools import QuantitativeAnalysisInput


def perform_backtesting(
    data: pd.DataFrame,
    input_data: QuantitativeAnalysisInput,
    start_date: datetime,
    end_date: datetime,
    backtesting_engine: BacktestingEngine,
) -> str:
    """
    Perform backtesting analysis on price data.

    Args:
        data: Historical price data DataFrame
        input_data: Analysis input parameters
        start_date: Backtest start date
        end_date: Backtest end date
        backtesting_engine: Backtesting engine instance

    Returns:
        JSON string with backtesting results

    """
    logger = get_logger(__name__)

    try:
        # Run backtest with simple moving average strategy
        backtest_result = backtesting_engine.run_strategy_backtest(
            SimpleMovingAverageStrategy,
            input_data.symbol,
            start_date,
            end_date,
            strategy_params={"short_period": 20, "long_period": 50},
        )

        # Convert to simplified schema
        quant_backtest = QuantitativeBacktestResult(
            symbol=input_data.symbol,
            strategy_name=backtest_result.strategy_name,
            total_return=backtest_result.total_return,
            annualized_return=backtest_result.annualized_return,
            sharpe_ratio=backtest_result.sharpe_ratio,
            max_drawdown=backtest_result.max_drawdown,
            total_trades=backtest_result.total_trades,
            win_rate=backtest_result.win_rate,
            volatility=backtest_result.volatility,
            var_95=backtest_result.var_95,
            backtest_start_date=backtest_result.start_date,
            backtest_end_date=backtest_result.end_date,
            initial_capital=backtest_result.initial_capital,
            final_value=backtest_result.final_value,
        )

        return quant_backtest.model_dump_json(indent=2)

    except Exception as e:
        logger.error(f"Error in backtesting: {e}")
        return f"Backtesting error: {e!s}"
