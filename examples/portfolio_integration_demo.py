#!/usr/bin/env python3
"""
Portfolio Integration Demo.

Demonstrates the integration between portfolio review and rebalancing
components with shared caching and unified reporting.
"""

import asyncio
import json
from pathlib import Path

from finwiz.orchestrators.portfolio_review_enhanced import EnhancedPortfolioReviewOrchestrator
from finwiz.tools.portfolio_cache_service import get_portfolio_cache_service


async def demo_portfolio_integration() -> None:
    """Demonstrate portfolio integration features."""
    print("🚀 Portfolio Integration Demo")
    print("=" * 50)

    # Initialize the enhanced orchestrator
    orchestrator = EnhancedPortfolioReviewOrchestrator()
    cache_service = get_portfolio_cache_service()

    print("\n📊 1. Cache Service Statistics")
    print("-" * 30)
    stats = cache_service.get_cache_stats()
    print(f"Hit Rate: {stats.get('hit_rate', 0):.2%}")
    print(f"Cache Entries: {stats.get('entry_count', 0)}")
    print(f"Memory Usage: {stats.get('memory_usage_mb', 0):.2f} MB")

    # Example target weights for demonstration
    target_weights = {
        "AAPL": 0.25,  # Apple Inc.
        "GOOGL": 0.20,  # Alphabet Inc.
        "MSFT": 0.20,  # Microsoft Corp.
        "TSLA": 0.15,  # Tesla Inc.
        "SPY": 0.20,  # SPDR S&P 500 ETF
    }

    print("\n🎯 2. Target Portfolio Allocation")
    print("-" * 30)
    for symbol, weight in target_weights.items():
        print(f"{symbol}: {weight:.1%}")

    print("\n💰 3. Available Capital: $10,000")

    try:
        print("\n🔄 4. Running Comprehensive Analysis...")
        print("-" * 30)

        # Run comprehensive analysis with caching
        result = await orchestrator.run_comprehensive_analysis(target_weights=target_weights, available_capital=10000.0, enable_caching=True)

        print("✅ Analysis completed successfully!")

        # Display key results
        portfolio_review = result.get("portfolio_review", {})
        rebalancing_analysis = result.get("rebalancing_analysis")

        print("\n📋 5. Portfolio Review Summary")
        print("-" * 30)
        holdings = portfolio_review.get("holdings", [])
        keep_count = sum(1 for h in holdings if h.get("decision") == "KEEP")
        sell_count = sum(1 for h in holdings if h.get("decision") == "SELL")

        print(f"Total Holdings: {len(holdings)}")
        print(f"Keep Recommendations: {keep_count}")
        print(f"Sell Recommendations: {sell_count}")

        if rebalancing_analysis:
            print("\n⚖️ 6. Rebalancing Summary")
            print("-" * 30)

            execution_summary = rebalancing_analysis.get("execution_summary", {})
            cost_analysis = rebalancing_analysis.get("cost_analysis", {})
            recommendation = rebalancing_analysis.get("overall_recommendation", "N/A")

            print(f"Recommendation: {recommendation}")
            print(f"Trades Required: {execution_summary.get('total_trades_required', 0)}")
            print(f"Transaction Costs: ${cost_analysis.get('total_transaction_costs', 0):.2f}")
            print(f"Execution Time: {execution_summary.get('estimated_execution_time', 'N/A')}")

            # Show trade recommendations
            trades = rebalancing_analysis.get("trade_recommendations", [])
            if trades:
                print("\n📈 7. Trade Recommendations")
                print("-" * 30)
                for i, trade in enumerate(trades[:5], 1):  # Show first 5 trades
                    action = trade.get("action", "N/A")
                    symbol = trade.get("symbol", "N/A")
                    quantity = trade.get("quantity", 0)
                    value = trade.get("trade_value", 0)

                    print(f"{i}. {action} {quantity:.2f} shares of {symbol} (${value:,.2f})")
        else:
            print("\n⚠️ 6. Rebalancing Analysis")
            print("-" * 30)
            print("No rebalancing analysis available (likely due to missing data)")

        print("\n📄 8. Generating Unified Report...")
        print("-" * 30)

        # Generate unified HTML report
        html_report = await orchestrator.generate_unified_report(result, language="en")

        # Save report to file
        output_dir = Path("output/portfolio")
        output_dir.mkdir(parents=True, exist_ok=True)

        report_file = output_dir / "integration_demo_report.html"
        report_file.write_text(html_report, encoding="utf-8")

        print(f"✅ Report saved to: {report_file}")
        print(f"📊 Report size: {len(html_report):,} characters")

        # Save analysis data as JSON
        json_file = output_dir / "integration_demo_data.json"
        json_file.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
        print(f"💾 Analysis data saved to: {json_file}")

        print("\n🎉 Demo completed successfully!")

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("This is expected if you don't have API keys configured or test data available.")

        # Show what the integration would provide
        print("\n🔧 Integration Features Demonstrated:")
        print("- Shared caching between portfolio review and rebalancing")
        print("- Unified HTML report generation")
        print("- Seamless data flow between components")
        print("- Error handling and graceful degradation")
        print("- Performance monitoring and statistics")


async def demo_cache_warming() -> None:
    """Demonstrate cache warming functionality."""
    print("\n🔥 Cache Warming Demo")
    print("=" * 30)

    cache_service = get_portfolio_cache_service()

    # Example symbols to warm cache for
    symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "SPY"]

    print(f"Warming cache for symbols: {', '.join(symbols)}")

    try:
        await cache_service.warm_portfolio_cache(symbols)
        print("✅ Cache warming completed")

        # Show updated stats
        stats = cache_service.get_cache_stats()
        print(f"Cache entries after warming: {stats.get('entry_count', 0)}")

    except Exception as e:
        print(f"❌ Cache warming failed: {e}")
        print("This is expected without proper API configuration")


async def demo_shared_caching() -> None:
    """Demonstrate shared caching between components."""
    print("\n🔄 Shared Caching Demo")
    print("=" * 30)

    cache_service = get_portfolio_cache_service()

    # Simulate caching price data
    test_symbol = "AAPL"
    test_price_data = {"price": 150.0, "timestamp": "2025-01-01T12:00:00", "volume": 1000000, "change": 2.5}

    print(f"Caching price data for {test_symbol}...")
    await cache_service.set_price_data(test_symbol, test_price_data)

    # Retrieve cached data
    cached_data = await cache_service.get_price_data(test_symbol)

    if cached_data:
        print("✅ Successfully retrieved cached data:")
        print(f"   Price: ${cached_data['price']}")
        print(f"   Timestamp: {cached_data['timestamp']}")
    else:
        print("❌ Failed to retrieve cached data")

    # Show cache statistics
    stats = cache_service.get_cache_stats()
    print("\nCache Statistics:")
    print(f"   Hit Rate: {stats.get('hit_rate', 0):.2%}")
    print(f"   Entries: {stats.get('entry_count', 0)}")


if __name__ == "__main__":

    async def main() -> None:
        """Run all portfolio integration demos."""
        await demo_portfolio_integration()
        await demo_cache_warming()
        await demo_shared_caching()

    asyncio.run(main())
