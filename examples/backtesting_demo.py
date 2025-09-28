#!/usr/bin/env python3
"""
Demo script showing BacktestingTool usage for investment discovery agents.

This example demonstrates how to use the BacktestingTool for comprehensive
historical validation with multi-regime analysis and risk-adjusted metrics.
"""

import asyncio
import json

from finwiz.tools.backtesting_tool import get_backtesting_tool


async def demo_basic_backtesting() -> None:
    """Demonstrate basic backtesting functionality."""
    print("=" * 60)
    print("BASIC BACKTESTING DEMO")
    print("=" * 60)

    # Create backtesting tool
    backtesting_tool = get_backtesting_tool()

    # Test with a well-known stock
    print("\n1. Testing AAPL with SMA Crossover Strategy")
    print("-" * 40)

    try:
        result_json = backtesting_tool._run(
            symbol="AAPL",
            strategy="sma_crossover",
            backtest_period_years=3,
            benchmark_symbol="SPY",
            initial_capital=100000.0,
            include_regime_analysis=True,
            strategy_params={"short_period": 20, "long_period": 50},
        )

        result = json.loads(result_json)

        print(f"Symbol: {result['symbol']}")
        print(f"Strategy: {result['strategy_name']}")
        print(f"Total Return: {result['total_return']:.2f}%")
        print(f"Annualized Return: {result['annualized_return']:.2f}%")
        print(f"Sharpe Ratio: {result['sharpe_ratio']:.2f}")
        print(f"Max Drawdown: {result['max_drawdown']:.2f}%")
        print(f"Win Rate: {result['win_rate']:.1%}")
        print(f"Validation Score: {result['validation_score']:.2f}")
        print(f"Validation Passed: {result['validation_passed']}")

        if result["regime_analysis"]:
            print(f"\nRegime Analysis ({len(result['regime_analysis'])} regimes):")
            for i, regime in enumerate(result["regime_analysis"]):
                print(
                    f"  {i + 1}. {regime['regime_type'].upper()} market: "
                    f"{regime['strategy_return']:.1f}% return, "
                    f"Sharpe: {regime['sharpe_ratio']:.2f}"
                )

        print("\nValidation Notes:")
        for note in result["validation_notes"]:
            print(f"  - {note}")

    except Exception as e:
        print(f"Error in backtesting: {e}")


async def demo_multi_asset_comparison() -> None:
    """Demonstrate multi-asset backtesting comparison."""
    print("\n" + "=" * 60)
    print("MULTI-ASSET COMPARISON DEMO")
    print("=" * 60)

    backtesting_tool = get_backtesting_tool()

    # Test multiple assets
    assets = ["AAPL", "MSFT", "GOOGL", "SPY", "QQQ"]
    results = {}

    print("\n2. Comparing Multiple Assets")
    print("-" * 40)

    for symbol in assets:
        try:
            print(f"\nTesting {symbol}...")

            result_json = backtesting_tool._run(
                symbol=symbol,
                strategy="sma_crossover",
                backtest_period_years=2,
                benchmark_symbol="SPY",
                initial_capital=100000.0,
                include_regime_analysis=False,  # Faster without regime analysis
                strategy_params={"short_period": 10, "long_period": 30},
            )

            result = json.loads(result_json)
            results[symbol] = result

            print(
                f"  Return: {result['total_return']:.1f}%, "
                f"Sharpe: {result['sharpe_ratio']:.2f}, "
                f"Validation: {'✓' if result['validation_passed'] else '✗'}"
            )

        except Exception as e:
            print(f"  Error testing {symbol}: {e}")
            continue

    # Summary comparison
    if results:
        print("\n3. Performance Summary")
        print("-" * 40)
        print(f"{'Asset':<8} {'Return':<8} {'Sharpe':<8} {'Drawdown':<10} {'Valid':<6}")
        print("-" * 40)

        for symbol, result in results.items():
            validation_mark = "✓" if result["validation_passed"] else "✗"
            print(
                f"{symbol:<8} {result['total_return']:>6.1f}% "
                f"{result['sharpe_ratio']:>6.2f}  "
                f"{result['max_drawdown']:>8.1f}%  "
                f"{validation_mark:>4}"
            )


async def demo_regime_analysis() -> None:
    """Demonstrate detailed regime analysis."""
    print("\n" + "=" * 60)
    print("DETAILED REGIME ANALYSIS DEMO")
    print("=" * 60)

    backtesting_tool = get_backtesting_tool()

    print("\n4. Detailed Regime Analysis for SPY")
    print("-" * 40)

    try:
        result_json = backtesting_tool._run(
            symbol="SPY",
            strategy="sma_crossover",
            backtest_period_years=5,
            benchmark_symbol="SPY",
            initial_capital=100000.0,
            include_regime_analysis=True,
            strategy_params={"short_period": 15, "long_period": 45},
        )

        result = json.loads(result_json)

        print("Overall Performance:")
        print(f"  Total Return: {result['total_return']:.2f}%")
        print(f"  Regime Consistency: {result['regime_consistency']:.2f}")
        print(f"  Validation Score: {result['validation_score']:.2f}")

        if result["regime_analysis"]:
            print("\nRegime Breakdown:")
            print(f"{'Regime':<12} {'Duration':<10} {'Market':<8} {'Strategy':<10} {'Outperf':<8} {'Sharpe':<8}")
            print("-" * 60)

            for regime in result["regime_analysis"]:
                print(
                    f"{regime['regime_type'].capitalize():<12} "
                    f"{regime['duration_days']:>7}d  "
                    f"{regime['market_return']:>6.1f}%  "
                    f"{regime['strategy_return']:>8.1f}%  "
                    f"{regime['outperformance']:>6.1f}%  "
                    f"{regime['sharpe_ratio']:>6.2f}"
                )

        # Risk metrics
        print("\nRisk Metrics:")
        print(f"  Volatility: {result['volatility']:.1f}%")
        print(f"  Max Drawdown: {result['max_drawdown']:.1f}%")
        print(f"  Sortino Ratio: {result['sortino_ratio']:.2f}")
        print(f"  Calmar Ratio: {result['calmar_ratio']:.2f}")
        if result["var_95"]:
            print(f"  VaR (95%): {result['var_95']:.2f}%")

    except Exception as e:
        print(f"Error in regime analysis: {e}")


async def demo_validation_criteria() -> None:
    """Demonstrate validation criteria and scoring."""
    print("\n" + "=" * 60)
    print("VALIDATION CRITERIA DEMO")
    print("=" * 60)

    backtesting_tool = get_backtesting_tool()

    print("\n5. Understanding Validation Criteria")
    print("-" * 40)
    print("Validation criteria for A+ investment candidates:")
    print("  • Minimum annual return: 8%")
    print("  • Minimum Sharpe ratio: 1.0")
    print("  • Maximum drawdown limit: -25%")
    print("  • Minimum win rate: 45%")
    print("  • Regime consistency: 60%")
    print("  • Overall validation threshold: 70%")

    # Test with different assets to show validation differences
    test_assets = ["AAPL", "TSLA", "BRK-B"]

    for symbol in test_assets:
        try:
            print(f"\n6. Validation Test: {symbol}")
            print("-" * 30)

            result_json = backtesting_tool._run(
                symbol=symbol, strategy="sma_crossover", backtest_period_years=3, include_regime_analysis=True
            )

            result = json.loads(result_json)

            # Show validation breakdown
            print("Performance Metrics:")
            print(f"  Annual Return: {result['annualized_return']:.1f}% ({'✓' if result['annualized_return'] >= 8 else '✗ <8%'})")
            print(f"  Sharpe Ratio: {result['sharpe_ratio']:.2f} ({'✓' if result['sharpe_ratio'] >= 1.0 else '✗ <1.0'})")
            print(f"  Max Drawdown: {result['max_drawdown']:.1f}% ({'✓' if result['max_drawdown'] >= -25 else '✗ <-25%'})")
            print(f"  Win Rate: {result['win_rate']:.1%} ({'✓' if result['win_rate'] >= 0.45 else '✗ <45%'})")
            print(
                f"  Regime Consistency: {result['regime_consistency']:.1%} "
                f"({'✓' if result['regime_consistency'] >= 0.6 else '✗ <60%'})"
            )

            print("\nValidation Result:")
            print(f"  Score: {result['validation_score']:.1%}")
            print(f"  Status: {'✓ PASSED' if result['validation_passed'] else '✗ FAILED'}")

            if not result["validation_passed"]:
                print(f"  Issues: {len([n for n in result['validation_notes'] if 'below' in n.lower()])} criteria failed")

        except Exception as e:
            print(f"Error testing {symbol}: {e}")


async def main() -> None:
    """Run all demo functions."""
    print("BacktestingTool Demo for Investment Discovery Agents")
    print("This demo shows comprehensive backtesting with multi-regime analysis")

    try:
        await demo_basic_backtesting()
        await demo_multi_asset_comparison()
        await demo_regime_analysis()
        await demo_validation_criteria()

        print("\n" + "=" * 60)
        print("DEMO COMPLETED")
        print("=" * 60)
        print("\nThe BacktestingTool provides:")
        print("✓ Historical validation with risk-adjusted metrics")
        print("✓ Multi-regime analysis (bull, bear, sideways markets)")
        print("✓ Comprehensive validation scoring")
        print("✓ Integration with quantitative analysis modules")
        print("✓ Professional-grade performance metrics")
        print("\nUse this tool to validate A+ investment candidates!")

    except Exception as e:
        print(f"Demo error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
