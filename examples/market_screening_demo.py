#!/usr/bin/env python3
"""
Market Screening Tool Demo.

This script demonstrates the Market Screening Tool functionality for discovering
A+ investment opportunities across ETFs, stocks, and cryptocurrencies.
"""

import json
from datetime import datetime

from finwiz.tools.market_screening_tool import MarketScreeningTool


def print_separator(title: str) -> None:
    """Print a formatted separator."""
    print(f"\n{'=' * 60}")
    print(f" {title}")
    print(f"{'=' * 60}")


def print_screening_summary(result: dict) -> None:
    """Print screening summary."""
    summary = result.get("summary", {})
    print(f"Asset Type: {summary.get('asset_type', 'Unknown')}")
    print(f"Total Screened: {summary.get('total_screened', 0)}")
    print(f"Candidates Found: {summary.get('candidates_found', 0)}")
    print(f"A+ Candidates: {summary.get('a_plus_candidates', 0)}")
    print(f"Success Rate: {summary.get('success_rate', '0.0%')}")


def print_top_candidates(result: dict, limit: int = 5) -> None:
    """Print top candidates."""
    candidates = result.get("top_candidates", [])[:limit]

    if not candidates:
        print("No candidates found.")
        return

    print(f"\nTop {len(candidates)} Candidates:")
    print("-" * 80)
    print(f"{'Symbol':<8} {'Name':<25} {'Score':<6} {'A+':<4} {'Rationale'}")
    print("-" * 80)

    for candidate in candidates:
        symbol = candidate.get("symbol", "")[:7]
        name = candidate.get("name", "")[:24]
        score = f"{candidate.get('score', 0):.2f}"
        a_plus = "✓" if candidate.get("a_plus", False) else "✗"
        rationale = candidate.get("rationale", "")[:40] + "..."

        print(f"{symbol:<8} {name:<25} {score:<6} {a_plus:<4} {rationale}")


def demo_etf_screening() -> None:
    """Demonstrate ETF screening."""
    print_separator("ETF Screening Demo")

    tool = MarketScreeningTool()

    # Screen US ETFs with default criteria
    print("Screening US ETFs with default A+ criteria...")
    result = tool._run(asset_type="etf", market_region="us", max_candidates=10, min_a_plus_score=0.80)

    print_screening_summary(result)
    print_top_candidates(result)

    # Screen with custom criteria (stricter)
    print("\n" + "-" * 40)
    print("Screening with stricter criteria...")

    custom_criteria = {
        "max_expense_ratio": 0.10,  # Very low fees only
        "min_aum": 5e9,  # Large ETFs only
    }

    result = tool._run(asset_type="etf", screening_criteria=custom_criteria, market_region="us", max_candidates=5, min_a_plus_score=0.85)

    print_screening_summary(result)
    print_top_candidates(result)


def demo_stock_screening() -> None:
    """Demonstrate stock screening."""
    print_separator("Stock Screening Demo")

    tool = MarketScreeningTool()

    # Screen US stocks with default criteria
    print("Screening US stocks with A+ growth criteria...")
    result = tool._run(asset_type="stock", market_region="us", max_candidates=10, min_a_plus_score=0.75)

    print_screening_summary(result)
    print_top_candidates(result)

    # Screen with custom criteria (quality focus)
    print("\n" + "-" * 40)
    print("Screening for high-quality stocks...")

    custom_criteria = {
        "min_roe": 0.25,  # Very high ROE
        "min_revenue_growth": 0.20,  # High growth
        "max_debt_to_equity": 0.20,  # Low debt
    }

    result = tool._run(asset_type="stock", screening_criteria=custom_criteria, market_region="us", max_candidates=5, min_a_plus_score=0.85)

    print_screening_summary(result)
    print_top_candidates(result)


def demo_crypto_screening() -> None:
    """Demonstrate crypto screening."""
    print_separator("Crypto Screening Demo")

    tool = MarketScreeningTool()

    # Screen cryptocurrencies with default criteria
    print("Screening cryptocurrencies with A+ criteria...")
    result = tool._run(
        asset_type="crypto",
        market_region="global",
        max_candidates=10,
        min_a_plus_score=0.70,  # Lower threshold for crypto
    )

    print_screening_summary(result)
    print_top_candidates(result)

    # Screen with custom criteria (institutional focus)
    print("\n" + "-" * 40)
    print("Screening for institutional-grade crypto...")

    custom_criteria = {
        "min_market_cap": 50e9,  # Very large cap only
        "min_daily_volume": 2e9,  # High liquidity
        "require_institutional_adoption": True,
    }

    result = tool._run(asset_type="crypto", screening_criteria=custom_criteria, market_region="global", max_candidates=5, min_a_plus_score=0.80)

    print_screening_summary(result)
    print_top_candidates(result)


def demo_detailed_analysis() -> None:
    """Demonstrate detailed A+ analysis."""
    print_separator("Detailed A+ Analysis Demo")

    tool = MarketScreeningTool()

    print("Running detailed A+ analysis on ETF candidates...")
    result = tool._run(
        asset_type="etf",
        market_region="us",
        max_candidates=3,
        min_a_plus_score=0.80,
        include_detailed_analysis=True,  # Enable detailed A+ scoring
    )

    print_screening_summary(result)

    # Show detailed screening result
    screening_result = result.get("screening_result", {})
    candidates = screening_result.get("candidates", [])

    if candidates:
        print("\nDetailed Analysis of Top Candidate:")
        print("-" * 50)
        top_candidate = candidates[0]

        print(f"Symbol: {top_candidate.get('symbol')}")
        print(f"Name: {top_candidate.get('name')}")
        print(f"Score: {top_candidate.get('preliminary_score'):.3f}")
        print(f"A+ Status: {'Yes' if top_candidate.get('meets_a_plus_criteria') else 'No'}")
        print(f"Key Metrics: {json.dumps(top_candidate.get('key_metrics', {}), indent=2)}")
        print(f"Rationale: {top_candidate.get('screening_rationale')}")
        print(f"Screened At: {top_candidate.get('screened_at')}")


def demo_market_regions() -> None:
    """Demonstrate different market regions."""
    print_separator("Market Region Comparison Demo")

    tool = MarketScreeningTool()

    regions = ["us", "eu", "global"]

    for region in regions:
        print(f"\nScreening {region.upper()} stock market...")
        result = tool._run(asset_type="stock", market_region=region, max_candidates=5, min_a_plus_score=0.75)

        summary = result.get("summary", {})
        print(f"  Total screened: {summary.get('total_screened', 0)}")
        print(f"  Candidates found: {summary.get('candidates_found', 0)}")
        print(f"  A+ candidates: {summary.get('a_plus_candidates', 0)}")


def demo_performance_metrics() -> None:
    """Demonstrate performance and efficiency."""
    print_separator("Performance Metrics Demo")

    tool = MarketScreeningTool()

    # Time the screening process
    start_time = datetime.now()

    result = tool._run(asset_type="stock", market_region="global", max_candidates=20, min_a_plus_score=0.70)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    summary = result.get("summary", {})
    screening_result = result.get("screening_result", {})

    print("Screening Performance:")
    print(f"  Duration: {duration:.2f} seconds")
    print(f"  Symbols processed: {summary.get('total_screened', 0)}")
    print(f"  Processing rate: {summary.get('total_screened', 0) / max(duration, 0.1):.1f} symbols/second")
    print(f"  Data sources: {', '.join(screening_result.get('data_sources', []))}")
    print("  Cache efficiency: Available for subsequent runs")


def main() -> None:
    """Run all demos."""
    print("Market Screening Tool Demo")
    print("=" * 60)
    print("This demo showcases the Market Screening Tool's ability to discover")
    print("A+ investment opportunities across different asset classes.")

    try:
        # Run all demos
        demo_etf_screening()
        demo_stock_screening()
        demo_crypto_screening()
        demo_detailed_analysis()
        demo_market_regions()
        demo_performance_metrics()

        print_separator("Demo Complete")
        print("The Market Screening Tool successfully demonstrated:")
        print("✓ Multi-asset screening (ETF, Stock, Crypto)")
        print("✓ Customizable A+ criteria")
        print("✓ Market region filtering")
        print("✓ Detailed A+ analysis integration")
        print("✓ Performance optimization")
        print("✓ Comprehensive candidate evaluation")

        print("\nNext Steps:")
        print("- Integrate with CrewAI agents for automated discovery")
        print("- Connect to real-time market data APIs")
        print("- Implement backtesting validation")
        print("- Add portfolio optimization integration")

    except Exception as e:
        print(f"\nDemo Error: {e}")
        print("This is expected in a demo environment without real API connections.")


if __name__ == "__main__":
    main()
