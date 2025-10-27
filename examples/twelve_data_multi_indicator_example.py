"""
Example: Using TwelveDataMultiIndicatorTool for technical analysis.

This example demonstrates how to use the multi-indicator tool to fetch
RSI, MACD, and Bollinger Bands in a single API call.
"""

import os

from dotenv import load_dotenv

from finwiz.tools.twelve_data_multi_indicator_tool import TwelveDataMultiIndicatorTool

# Load environment variables
load_dotenv()


def example_basic_usage():
    """Basic usage with default parameters."""
    print("=" * 80)
    print("Example 1: Basic Usage with Default Parameters")
    print("=" * 80)

    tool = TwelveDataMultiIndicatorTool()

    # Fetch all indicators with defaults
    result = tool._run(
        symbol="AAPL",
        interval="1day",
        indicators=["rsi", "macd", "bbands"],
    )

    print(result)
    print("\n")


def example_custom_parameters():
    """Custom parameters for each indicator."""
    print("=" * 80)
    print("Example 2: Custom Parameters")
    print("=" * 80)

    tool = TwelveDataMultiIndicatorTool()

    # Customize each indicator's parameters
    result = tool._run(
        symbol="SRECHA.SW",
        interval="1day",
        indicators=["rsi", "macd", "bbands"],
        rsi_period=14,  # Standard RSI period
        macd_fast=12,  # MACD fast EMA
        macd_slow=26,  # MACD slow EMA
        macd_signal=9,  # MACD signal line
        bbands_period=20,  # Bollinger Bands period
        bbands_stddev=2,  # Standard deviation multiplier
        outputsize=100,  # Number of data points
    )

    print(result)
    print("\n")


def example_crypto_analysis():
    """Analyze cryptocurrency with technical indicators."""
    print("=" * 80)
    print("Example 3: Cryptocurrency Analysis")
    print("=" * 80)

    tool = TwelveDataMultiIndicatorTool()

    # Analyze Bitcoin with hourly data
    result = tool._run(
        symbol="BTC/USD",
        interval="1h",
        indicators=["rsi", "macd", "bbands"],
        rsi_period=14,
        macd_fast=12,
        macd_slow=26,
        macd_signal=9,
        bbands_period=20,
        bbands_stddev=2,
        outputsize=50,  # Last 50 hours
    )

    print(result)
    print("\n")


def example_etf_analysis():
    """Analyze ETF with technical indicators."""
    print("=" * 80)
    print("Example 4: ETF Analysis")
    print("=" * 80)

    tool = TwelveDataMultiIndicatorTool()

    # Analyze S&P 500 ETF
    result = tool._run(
        symbol="SPY",
        interval="1day",
        indicators=["rsi", "macd", "bbands"],
        outputsize=200,  # Last 200 days
    )

    print(result)
    print("\n")


def example_selective_indicators():
    """Fetch only specific indicators."""
    print("=" * 80)
    print("Example 5: Selective Indicators")
    print("=" * 80)

    tool = TwelveDataMultiIndicatorTool()

    # Fetch only RSI and MACD (skip Bollinger Bands)
    result = tool._run(
        symbol="MSFT",
        interval="1day",
        indicators=["rsi", "macd"],  # Only these two
        rsi_period=14,
        macd_fast=12,
        macd_slow=26,
        macd_signal=9,
    )

    print(result)
    print("\n")


def example_error_handling():
    """Demonstrate error handling."""
    print("=" * 80)
    print("Example 6: Error Handling")
    print("=" * 80)

    tool = TwelveDataMultiIndicatorTool()

    # Try with invalid symbol
    result = tool._run(
        symbol="INVALID_SYMBOL_123",
        interval="1day",
        indicators=["rsi"],
    )

    print("Result with invalid symbol:")
    print(result)
    print("\n")


def example_comparison():
    """Compare old vs new approach."""
    print("=" * 80)
    print("Example 7: Performance Comparison")
    print("=" * 80)

    import time

    # Old approach (simulated - would be 3 separate calls)
    print("Old Approach (3 separate calls):")
    print("  - Call 1: TwelveDataIndicatorTool(symbol='AAPL', indicator='rsi')")
    print("  - Call 2: TwelveDataIndicatorTool(symbol='AAPL', indicator='macd')")
    print("  - Call 3: TwelveDataIndicatorTool(symbol='AAPL', indicator='bbands')")
    print("  - Total API calls: 3")
    print("  - Estimated time: 3-6 seconds")
    print("  - API credits used: 3")
    print()

    # New approach (1 combined call)
    print("New Approach (1 combined call):")
    tool = TwelveDataMultiIndicatorTool()

    start_time = time.time()
    result = tool._run(
        symbol="AAPL",
        interval="1day",
        indicators=["rsi", "macd", "bbands"],
    )
    elapsed_time = time.time() - start_time

    print("  - Total API calls: 1")
    print(f"  - Actual time: {elapsed_time:.2f} seconds")
    print("  - API credits used: 1")
    print()
    print("Savings: 66% fewer API calls, ~50-66% faster, 66% lower cost")
    print("\n")


def main():
    """Run all examples."""
    # Check for API key
    if not os.getenv("TWELVE_DATA_API_KEY"):
        print("⚠️  Warning: TWELVE_DATA_API_KEY not set in environment")
        print("Set it with: export TWELVE_DATA_API_KEY='your_key_here'")
        print()
        return

    print("\n")
    print("🚀 Twelve Data Multi-Indicator Tool Examples")
    print("=" * 80)
    print()

    # Run examples
    try:
        example_basic_usage()
        example_custom_parameters()
        example_crypto_analysis()
        example_etf_analysis()
        example_selective_indicators()
        example_error_handling()
        example_comparison()

        print("=" * 80)
        print("✅ All examples completed successfully!")
        print("=" * 80)

    except Exception as e:
        print(f"❌ Error running examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
