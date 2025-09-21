#!/usr/bin/env python3

"""
Quantitative Analysis Demo.

This example demonstrates the quantitative analysis capabilities of FinWiz,
including backtesting, technical analysis, and performance metrics.

Usage:
    uv run python examples/quantitative_analysis_demo.py
"""

import asyncio
from datetime import datetime, timedelta

from finwiz.quantitative import (
    SimpleMovingAverageStrategy,
    get_backtesting_engine,
    get_historical_data_manager,
    get_performance_analyzer,
)
from finwiz.quantitative.technical import TechnicalAnalysisEngine, TechnicalIndicator
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


async def demo_technical_analysis() -> None:
    """Demonstrate technical analysis capabilities."""
    print("\n" + "=" * 60)
    print("TECHNICAL ANALYSIS DEMO")
    print("=" * 60)

    try:
        # Initialize components
        data_manager = get_historical_data_manager()
        technical_engine = TechnicalAnalysisEngine()

        # Fetch data
        symbol = "AAPL"
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        print(f"Fetching data for {symbol}...")
        data = data_manager.fetch_historical_data(symbol, start_date, end_date)

        if data.empty:
            print(f"No data available for {symbol}")
            return

        print(f"Analyzing {len(data)} data points...")

        # Perform technical analysis
        indicators = [TechnicalIndicator.RSI, TechnicalIndicator.MACD, TechnicalIndicator.BOLLINGER_BANDS, TechnicalIndicator.SMA]

        result = technical_engine.analyze_symbol(data, symbol, "1d", indicators)

        # Display results
        print(f"\nTechnical Analysis Results for {symbol}:")
        print(f"Overall Signal: {result.overall_signal.value}")
        print(f"Confidence: {result.overall_confidence:.2f}")
        print(f"Signal Strength: {result.signal_strength.value}")
        print(f"Bullish Signals: {result.bullish_signals_count}")
        print(f"Bearish Signals: {result.bearish_signals_count}")
        print(f"Neutral Signals: {result.neutral_signals_count}")

        # Show individual indicator results
        print("\nIndicator Details:")
        for indicator_name, indicator_result in result.indicator_results.items():
            print(f"\n{indicator_name}:")
            if indicator_result.signals:
                for signal in indicator_result.signals[:2]:  # Show first 2 signals
                    print(f"  - {signal.signal_type.value}: {signal.description}")
                    print(f"    Confidence: {signal.confidence:.2f}")

    except Exception as e:
        logger.error(f"Technical analysis demo failed: {e}")
        print(f"Error: {e}")


async def demo_backtesting() -> None:
    """Demonstrate backtesting capabilities."""
    print("\n" + "=" * 60)
    print("BACKTESTING DEMO")
    print("=" * 60)

    try:
        # Initialize backtesting engine
        engine = get_backtesting_engine()

        # Run backtest
        symbol = "AAPL"
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2024, 1, 1)

        print(f"Running backtest for {symbol} from {start_date.date()} to {end_date.date()}...")

        result = engine.run_strategy_backtest(
            strategy_class=SimpleMovingAverageStrategy,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            strategy_params={"short_period": 20, "long_period": 50},
        )

        # Display results
        print(f"\nBacktest Results for {symbol}:")
        print(f"Strategy: {result.strategy_name}")
        print(f"Initial Capital: ${result.initial_capital:,.2f}")
        print(f"Final Value: ${result.final_value:,.2f}")
        print(f"Total Return: {result.total_return:.2f}%")
        print(f"Annualized Return: {result.annualized_return:.2f}%")
        print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
        print(f"Maximum Drawdown: {result.max_drawdown:.2f}%")
        print(f"Total Trades: {result.total_trades}")
        print(f"Win Rate: {result.win_rate:.2%}")
        print(f"Volatility: {result.volatility:.2f}%")

        if result.var_95:
            print(f"VaR (95%): {result.var_95:.2f}%")
        if result.cvar_95:
            print(f"CVaR (95%): {result.cvar_95:.2f}%")

        # Show some trades
        if result.trades:
            print("\nSample Trades (showing first 3):")
            for i, trade in enumerate(result.trades[:3]):
                print(f"  Trade {i + 1}: {trade.trade_type.value} {trade.quantity} shares")
                print(f"    Entry: ${trade.entry_price:.2f} on {trade.entry_date.date()}")
                if trade.exit_price and trade.exit_date:
                    print(f"    Exit: ${trade.exit_price:.2f} on {trade.exit_date.date()}")
                    if trade.pnl:
                        print(f"    P&L: ${trade.pnl:.2f} ({trade.pnl_percent:.2f}%)")

    except Exception as e:
        logger.error(f"Backtesting demo failed: {e}")
        print(f"Error: {e}")


async def demo_performance_analysis() -> None:
    """Demonstrate performance analysis capabilities."""
    print("\n" + "=" * 60)
    print("PERFORMANCE ANALYSIS DEMO")
    print("=" * 60)

    try:
        # Initialize performance analyzer
        analyzer = get_performance_analyzer()

        # Generate sample returns data
        import numpy as np
        import pandas as pd

        # Create sample strategy returns (daily)
        np.random.seed(42)
        dates = pd.date_range(start="2023-01-01", end="2023-12-31", freq="D")
        strategy_returns = pd.Series(
            np.random.normal(0.001, 0.02, len(dates)),  # 0.1% daily return, 2% volatility
            index=dates,
            name="strategy_returns",
        )

        # Create sample benchmark returns
        benchmark_returns = pd.Series(
            np.random.normal(0.0008, 0.015, len(dates)),  # 0.08% daily return, 1.5% volatility
            index=dates,
            name="benchmark_returns",
        )

        print("Analyzing performance with sample data...")

        # Perform performance analysis
        report = analyzer.analyze_performance(
            returns=strategy_returns,
            benchmark_returns=benchmark_returns,
            strategy_name="Sample Strategy",
            benchmark_name="Sample Benchmark",
        )

        # Display results
        metrics = report.performance_metrics
        print("\nPerformance Analysis Results:")
        print(f"Strategy: {report.strategy_name}")
        print(f"Period: {metrics.start_date.date()} to {metrics.end_date.date()}")
        print(f"Trading Days: {metrics.trading_days}")

        print("\nReturn Metrics:")
        print(f"Total Return: {metrics.total_return:.2%}")
        print(f"Annualized Return: {metrics.annualized_return:.2%}")
        print(f"Daily Return (Mean): {metrics.daily_return_mean:.4f}")
        print(f"Daily Return (Std): {metrics.daily_return_std:.4f}")

        print("\nRisk-Adjusted Metrics:")
        print(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
        print(f"Sortino Ratio: {metrics.sortino_ratio:.2f}")
        print(f"Calmar Ratio: {metrics.calmar_ratio:.2f}")

        print("\nRisk Metrics:")
        print(f"Volatility: {metrics.volatility:.2%}")
        print(f"Maximum Drawdown: {metrics.max_drawdown:.2%}")
        print(f"Max DD Duration: {metrics.max_drawdown_duration} days")
        print(f"VaR (95%): {metrics.var_95:.2%}")
        print(f"CVaR (95%): {metrics.cvar_95:.2%}")

        print("\nStatistical Metrics:")
        print(f"Skewness: {metrics.skewness:.2f}")
        print(f"Kurtosis: {metrics.kurtosis:.2f}")

        # Benchmark comparison
        if report.benchmark_metrics and report.relative_performance:
            print("\nBenchmark Comparison:")
            bench_metrics = report.benchmark_metrics
            rel_perf = report.relative_performance

            print(f"Benchmark Return: {bench_metrics.annualized_return:.2%}")
            print(f"Excess Return: {rel_perf['excess_return']:.2%}")
            print(f"Information Ratio: {rel_perf['information_ratio']:.2f}")
            print(f"Tracking Error: {rel_perf['tracking_error']:.2%}")

    except Exception as e:
        logger.error(f"Performance analysis demo failed: {e}")
        print(f"Error: {e}")


async def main() -> None:
    """Run all quantitative analysis demos."""
    print("FinWiz Quantitative Analysis Demo")
    print("This demo showcases the quantitative analysis capabilities.")
    print("\nNote: This demo uses sample data and mock calculations.")
    print("In production, real market data would be used.")

    # Run demos
    await demo_technical_analysis()
    await demo_backtesting()
    await demo_performance_analysis()

    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print("\nFor more information, see:")
    print("- docs/quantitative_analysis.md")
    print("- docs/reference.md")
    print("- tests/unit/quantitative/ for test examples")


if __name__ == "__main__":
    asyncio.run(main())
