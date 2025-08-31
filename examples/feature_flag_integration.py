#!/usr/bin/env python
"""
Example demonstrating feature flag and configuration manager integration.

This example shows how to use the feature flag system and configuration manager
in a FinWiz application context with graceful degradation.
"""

import asyncio
import os
from typing import Any

from finwiz.utils.configuration_manager import get_configuration_manager
from finwiz.utils.feature_flags import execute_with_feature_flag, get_feature_flags
from finwiz.utils.graceful_degradation import execute_with_degradation, get_degradation_manager


async def enhanced_sentiment_analysis(ticker: str) -> dict[str, Any]:
    """Enhanced sentiment analysis with multiple data sources."""
    print(f"🔍 Performing enhanced sentiment analysis for {ticker}")

    # Simulate API calls to multiple sources
    await asyncio.sleep(0.1)  # Simulate network delay

    return {
        "sentiment_score": 0.75,
        "article_count": 25,
        "trending_topics": ["earnings", "growth", "innovation"],
        "sources": ["alpha_vantage", "yahoo_finance", "coinmarketcap"],
    }


async def basic_sentiment_analysis(ticker: str) -> dict[str, Any]:
    """Basic sentiment analysis fallback."""
    print(f"📊 Performing basic sentiment analysis for {ticker}")

    return {"sentiment_score": 0.5, "article_count": 5, "trending_topics": ["market"], "sources": ["yahoo_finance"]}


async def chart_analysis(ticker: str) -> dict[str, Any]:
    """Chart analysis with Chart-img API."""
    print(f"📈 Generating chart analysis for {ticker}")

    # Simulate potential API failure
    import random

    if random.random() < 0.3:  # 30% chance of failure
        raise Exception("Chart-img API temporarily unavailable")

    await asyncio.sleep(0.2)  # Simulate processing time

    return {
        "chart_url": f"https://chart-img.com/{ticker}.png",
        "pattern_insights": ["bullish_flag", "support_at_50ma"],
        "visual_analysis": "Strong upward trend with consolidation pattern",
    }


def chart_analysis_fallback(ticker: str) -> dict[str, Any]:
    """Fallback when chart analysis is unavailable."""
    print(f"⚠️  Chart analysis unavailable for {ticker}, using fallback")

    return {"chart_url": None, "pattern_insights": [], "visual_analysis": "Chart analysis temporarily unavailable"}


async def twelve_data_indicators(ticker: str) -> dict[str, Any]:
    """Technical indicators from Twelve Data API."""
    print(f"📊 Fetching technical indicators for {ticker}")

    # Simulate rate limiting
    import random

    if random.random() < 0.2:  # 20% chance of rate limit
        raise Exception("Rate limit exceeded (429)")

    await asyncio.sleep(0.15)

    return {
        "rsi": 65.4,
        "macd": {"macd": 2.1, "signal": 1.8, "histogram": 0.3},
        "bollinger_bands": {"upper": 155.2, "middle": 150.0, "lower": 144.8},
        "indicators_available": True,
    }


def twelve_data_fallback(ticker: str) -> dict[str, Any]:
    """Fallback for technical indicators."""
    print(f"⚠️  Technical indicators unavailable for {ticker}, using cached data")

    return {
        "rsi": None,
        "macd": None,
        "bollinger_bands": None,
        "indicators_available": False,
        "message": "Technical indicators temporarily unavailable",
    }


async def analyze_stock_with_feature_flags(ticker: str) -> dict[str, Any]:
    """
    Analyze stock using feature flags and graceful degradation.

    This function demonstrates how different analysis components can be
    enabled/disabled via feature flags and gracefully degrade on failures.
    """
    print(f"\n🚀 Starting analysis for {ticker}")
    print("=" * 50)

    results = {"ticker": ticker, "analysis_components": {}}

    # Enhanced sentiment analysis with feature flag
    sentiment_result = await execute_with_feature_flag(
        "enhanced_sentiment_analysis", enhanced_sentiment_analysis, basic_sentiment_analysis, ticker=ticker
    )
    results["analysis_components"]["sentiment"] = sentiment_result

    # Chart analysis with graceful degradation
    chart_result = await execute_with_degradation(
        "chart_img", chart_analysis, chart_analysis_fallback, cache_key=f"chart_{ticker}", ticker=ticker
    )
    results["analysis_components"]["chart"] = chart_result

    # Technical indicators with feature flag and degradation
    if get_feature_flags().is_enabled("twelve_data_integration"):
        indicators_result = await execute_with_degradation(
            "twelve_data", twelve_data_indicators, twelve_data_fallback, cache_key=f"indicators_{ticker}", ticker=ticker
        )
        results["analysis_components"]["technical_indicators"] = indicators_result
    else:
        print(f"📊 Twelve Data integration disabled for {ticker}")
        results["analysis_components"]["technical_indicators"] = {"enabled": False, "message": "Feature disabled via feature flag"}

    return results


async def demonstrate_circuit_breaker() -> None:
    """Demonstrate circuit breaker pattern with repeated failures."""
    print("\n🔧 Demonstrating Circuit Breaker Pattern")
    print("=" * 50)

    degradation_manager = get_degradation_manager()

    # Configure a service with low failure threshold for demo
    degradation_manager.update_service_config("demo_service", error_threshold=2, circuit_breaker_timeout=2)

    call_count = 0

    async def unreliable_service() -> str:
        nonlocal call_count
        call_count += 1
        print(f"📞 Service call #{call_count}")

        if call_count <= 3:  # First 3 calls fail
            raise Exception(f"Service failure #{call_count}")
        return f"Success after {call_count} attempts"

    def fallback_service() -> str:
        return "Circuit breaker fallback response"

    # Make several calls to trigger circuit breaker
    for i in range(5):
        try:
            result = await execute_with_degradation("demo_service", unreliable_service, fallback_service)
            print(f"✅ Call {i + 1}: {result}")
        except Exception as e:
            print(f"❌ Call {i + 1}: {e}")

        await asyncio.sleep(0.1)

    # Show service health
    health = degradation_manager.get_service_health("demo_service")
    if health:
        print(f"\n📊 Service Health: {health.status.value}")
        print(f"🔢 Error Count: {health.error_count}")
        print(f"✅ Success Count: {health.success_count}")


async def main() -> None:
    """Main demonstration function."""
    print("🎯 FinWiz Feature Flag & Configuration Demo")
    print("=" * 60)

    # Initialize configuration
    try:
        print("\n🔧 Initializing Configuration...")
        get_configuration_manager()

        # For demo purposes, we'll skip API key validation
        print("✅ Configuration manager initialized")

        # Show feature flag status
        feature_flags = get_feature_flags()
        print("\n🚩 Feature Flags Status:")
        for flag_name, status in feature_flags.list_all_flags().items():
            enabled = "✅" if status.get("enabled", False) else "❌"
            print(f"  {enabled} {flag_name}: {status.get('description', 'No description')}")

    except Exception as e:
        print(f"❌ Configuration error: {e}")
        print("📝 Note: This is expected in demo mode without real API keys")

    # Demonstrate stock analysis with feature flags
    test_tickers = ["AAPL", "GOOGL", "TSLA"]

    for ticker in test_tickers:
        try:
            analysis_result = await analyze_stock_with_feature_flags(ticker)

            print(f"\n📋 Analysis Summary for {ticker}:")
            for component, data in analysis_result["analysis_components"].items():
                if isinstance(data, dict) and "sentiment_score" in data:
                    print(f"  📊 {component}: Score {data['sentiment_score']}, Articles {data['article_count']}")
                elif isinstance(data, dict) and "chart_url" in data:
                    status = "✅ Available" if data["chart_url"] else "❌ Unavailable"
                    print(f"  📈 {component}: {status}")
                elif isinstance(data, dict) and "rsi" in data:
                    status = "✅ Available" if data["rsi"] else "❌ Unavailable"
                    print(f"  📊 {component}: {status}")
                else:
                    print(f"  🔧 {component}: {data.get('message', 'Processed')}")

        except Exception as e:
            print(f"❌ Error analyzing {ticker}: {e}")

    # Demonstrate circuit breaker
    await demonstrate_circuit_breaker()

    # Show system health summary
    degradation_manager = get_degradation_manager()
    health_summary = degradation_manager.get_system_health_summary()

    print("\n🏥 System Health Summary:")
    print(f"  Overall Health: {health_summary['overall_health']}")
    print(f"  Healthy Services: {health_summary['healthy_services']}/{health_summary['total_services']}")
    print(f"  Overall Degradation: {health_summary['overall_degradation']}")

    print("\n🎉 Demo completed successfully!")


if __name__ == "__main__":
    # Set some demo environment variables
    os.environ.update(
        {
            "FF_ENHANCED_SENTIMENT": "true",
            "FF_ENHANCED_SENTIMENT_ROLLOUT": "100.0",
            "FF_CHART_ANALYSIS": "true",
            "FF_TWELVE_DATA": "true",
            "FF_STRICT_VALIDATION": "true",
        }
    )

    asyncio.run(main())
