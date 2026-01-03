"""
Performance analysis functions for quantitative analysis tool.

Extracted from quantitative_analysis_tool.py for modularity.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING

from finwiz.schemas.quantitative_crew import QuantitativePerformanceMetrics
from finwiz.tools.logger import get_logger

if TYPE_CHECKING:
    import pandas as pd

    from finwiz.quantitative.performance import PerformanceAnalyzer
    from finwiz.schemas.tools import QuantitativeAnalysisInput


def perform_performance_analysis(
    data: pd.DataFrame,
    input_data: QuantitativeAnalysisInput,
    performance_analyzer: PerformanceAnalyzer,
) -> str:
    """
    Perform performance analysis on price data.

    Args:
        data: Historical price data DataFrame
        input_data: Analysis input parameters
        performance_analyzer: Performance analyzer instance

    Returns:
        JSON string with performance analysis results

    """
    logger = get_logger(__name__)

    try:
        # Calculate returns
        returns = data["Close"].pct_change().dropna()

        # Run performance analysis
        perf_report = performance_analyzer.analyze_performance(returns, strategy_name=f"{input_data.symbol}_analysis")

        # Convert to simplified schema
        metrics = perf_report.strategy_metrics
        quant_perf = QuantitativePerformanceMetrics(
            symbol=input_data.symbol,
            total_return=metrics.total_return,
            annualized_return=metrics.annualized_return,
            sharpe_ratio=metrics.sharpe_ratio,
            sortino_ratio=metrics.sortino_ratio,
            calmar_ratio=metrics.calmar_ratio,
            max_drawdown=metrics.max_drawdown,
            volatility=metrics.volatility,
            var_95=metrics.var_95,
            skewness=metrics.skewness,
            kurtosis=metrics.kurtosis,
            alpha=metrics.alpha if metrics.alpha is not None else 0.0,
            beta=metrics.beta if metrics.beta is not None else 1.0,
            information_ratio=metrics.information_ratio if metrics.information_ratio is not None else 0.0,
            start_date=datetime.now(),
            end_date=datetime.now(),
            total_days=len(returns),
        )

        # Convert to dict for adding ETF-specific fields
        perf_dict = json.loads(quant_perf.model_dump_json())

        # Add ETF-specific metrics
        if input_data.asset_class == "etf":
            perf_dict = add_etf_metrics(perf_dict, input_data.symbol, logger)

        return json.dumps(perf_dict, indent=2, default=str)

    except Exception as e:
        logger.error(f"Error in performance analysis: {e}")
        return f"Performance analysis error: {str(e)}"


def add_etf_metrics(perf_dict: dict, symbol: str, logger) -> dict:
    """
    Add ETF-specific metrics to performance data.

    Args:
        perf_dict: Performance metrics dictionary
        symbol: ETF symbol
        logger: Logger instance

    Returns:
        Updated performance dictionary with ETF metrics

    """
    try:
        import yfinance as yf

        ticker = yf.Ticker(symbol)
        info = ticker.info

        # Fetch expense ratio (try multiple fields)
        expense_ratio = info.get("netExpenseRatio") or info.get("annualReportExpenseRatio")
        if expense_ratio is not None:
            expense_ratio_decimal = float(expense_ratio) / 100.0
            perf_dict["expense_ratio"] = expense_ratio_decimal
            logger.info(f"✅ Fetched expense_ratio for {symbol}: {expense_ratio}% → {expense_ratio_decimal:.6f} (as decimal)")
        else:
            perf_dict = _add_fallback_expense_ratio(perf_dict, symbol, logger)

        # Fetch AUM (totalAssets)
        total_assets = info.get("totalAssets")
        if total_assets is not None:
            perf_dict["aum"] = float(total_assets)
            logger.info(f"✅ Fetched AUM for {symbol}: ${total_assets:,.0f}")
        else:
            logger.warning(f"⚠️ No AUM available for {symbol}")

        # Calculate tracking error
        perf_dict = _add_tracking_error(perf_dict, ticker, info, symbol, logger)

    except Exception as e:
        logger.error(f"Error fetching ETF-specific data for {symbol}: {e}")

    return perf_dict


def _add_fallback_expense_ratio(perf_dict: dict, symbol: str, logger) -> dict:
    """Add fallback expense ratio if Yahoo Finance doesn't have it."""
    from finwiz.quantitative.etf.etf_expense_fallback import get_fallback_expense_ratio

    fallback_ratio = get_fallback_expense_ratio(symbol)
    if fallback_ratio is not None:
        perf_dict["expense_ratio"] = fallback_ratio
        logger.info(f"✅ Using fallback expense_ratio for {symbol}: {fallback_ratio:.6f} (as decimal)")
    else:
        logger.warning(f"⚠️ No expense_ratio available for {symbol} (Yahoo Finance or fallback)")

    return perf_dict


def _add_tracking_error(perf_dict: dict, ticker, info: dict, symbol: str, logger) -> dict:
    """Calculate and add tracking error to performance data."""
    try:
        import yfinance as yf

        # Determine appropriate benchmark based on ETF category
        category = info.get("category", "").lower()

        # Map ETF category to benchmark
        benchmark_map = {
            "large blend": "SPY",
            "large growth": "QQQ",
            "large value": "IVE",
            "mid-cap blend": "MDY",
            "small blend": "IJR",
            "foreign large blend": "VEA",
            "diversified emerging mkts": "VWO",
            "intermediate core bond": "AGG",
        }

        benchmark_symbol = benchmark_map.get(category, "SPY")
        logger.info(f"Calculating tracking error for {symbol} vs {benchmark_symbol} (category: {category or 'unknown'})")

        # Fetch benchmark data
        benchmark = yf.Ticker(benchmark_symbol)

        # Get 1 year of historical data for both
        etf_hist = ticker.history(period="1y")
        benchmark_hist = benchmark.history(period="1y")

        if not etf_hist.empty and not benchmark_hist.empty:
            # Calculate daily returns
            etf_returns = etf_hist["Close"].pct_change().dropna()
            benchmark_returns = benchmark_hist["Close"].pct_change().dropna()

            # Align dates (in case of different trading days)
            aligned_etf, aligned_benchmark = etf_returns.align(benchmark_returns, join="inner")

            if len(aligned_etf) > 20:  # Need at least 20 days of data
                # Calculate tracking difference
                tracking_diff = aligned_etf - aligned_benchmark

                # Annualized tracking error (standard deviation of tracking difference)
                tracking_error = tracking_diff.std() * (252**0.5)

                perf_dict["tracking_error"] = float(tracking_error)
                logger.info(f"✅ Calculated tracking_error for {symbol}: {tracking_error:.4f} ({tracking_error * 100:.2f}%)")
            else:
                logger.warning(f"⚠️ Insufficient aligned data for tracking error calculation: {len(aligned_etf)} days")
        else:
            logger.warning("⚠️ No historical data available for tracking error calculation")

    except Exception as e:
        logger.error(f"Error calculating tracking error for {symbol}: {e}")

    return perf_dict
