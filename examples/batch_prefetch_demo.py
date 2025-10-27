#!/usr/bin/env python
"""
Batch Data Pre-Fetch Demo.

This example demonstrates the batch data pre-fetching system with
Yahoo Finance as the primary data source.

Key Points:
- Yahoo Finance is ALWAYS used (primary source)
- Alpha Vantage is OPTIONAL and DISABLED by default
- Yahoo Finance provides all essential data in ~2-5 seconds for 66 tickers
- Alpha Vantage adds ~13 minutes with minimal benefit

Usage:
    # Recommended: Yahoo Finance only (fast)
    python examples/batch_prefetch_demo.py

    # Optional: Enable Alpha Vantage (slow)
    ENABLE_ALPHA_VANTAGE=true python examples/batch_prefetch_demo.py
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from finwiz.utils.batch_data_prefetcher import BatchDataPreFetcher


def main() -> None:
    """Run batch pre-fetch demo."""
    print("=" * 80)
    print("BATCH DATA PRE-FETCH DEMO")
    print("=" * 80)
    print()

    # Sample tickers for demo
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "BRK.B", "JPM", "V"]

    print(f"Demo: Pre-fetching data for {len(tickers)} tickers")
    print(f"Tickers: {', '.join(tickers)}")
    print()

    # Check Alpha Vantage configuration
    alpha_vantage_enabled = os.getenv("ENABLE_ALPHA_VANTAGE", "false").lower() in {"true", "1", "yes", "on"}

    print("Configuration:")
    print("  PRIMARY SOURCE: Yahoo Finance (ALWAYS ENABLED)")
    av_status = "ENABLED" if alpha_vantage_enabled else "DISABLED"
    print(f"  OPTIONAL SOURCE: Alpha Vantage ({av_status})")
    print()

    if alpha_vantage_enabled:
        print("⚠️  WARNING: Alpha Vantage is enabled")
        print("⚠️  This will add significant time (~13 minutes for 66 tickers)")
        print("⚠️  Yahoo Finance already provides all essential data")
        print("⚠️  Recommendation: Disable Alpha Vantage for optimal performance")
        print()
    else:
        print("✓ Optimal configuration: Yahoo Finance only")
        print("✓ Fast performance: ~2-5 seconds for 66 tickers")
        print()

    # Create prefetcher
    print("Creating batch data prefetcher...")
    prefetcher = BatchDataPreFetcher(
        session_id="demo-session",
        enable_alpha_vantage=alpha_vantage_enabled,  # Disabled by default
    )
    print()

    # Pre-fetch data
    print("Starting batch pre-fetch...")
    print()
    data = prefetcher.prefetch_all_data(tickers)
    print()

    # Display results
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()

    successful = sum(1 for v in data.values() if not v.get("failed", False))
    print(f"Successfully fetched: {successful}/{len(tickers)} tickers")
    print()

    # Show sample data for first ticker
    if tickers and tickers[0] in data:
        sample_ticker = tickers[0]
        sample_data = data[sample_ticker]

        print(f"Sample data for {sample_ticker}:")
        yf_status = "✓ Available" if sample_data.get("yahoo_finance") else "✗ Missing"
        av_status = "✓ Available" if sample_data.get("alpha_vantage") else "✗ Not fetched"
        print(f"  Yahoo Finance data: {yf_status}")
        print(f"  Alpha Vantage data: {av_status}")

        if sample_data.get("yahoo_finance"):
            yf_data = sample_data["yahoo_finance"]
            print()
            print("  Yahoo Finance provides:")
            print(f"    - Company name: {yf_data.get('name', 'N/A')}")
            print(f"    - Sector: {yf_data.get('sector', 'N/A')}")
            print(f"    - Current price: ${yf_data.get('current_price', 'N/A')}")
            market_cap = yf_data.get("market_cap", "N/A")
            if isinstance(market_cap, (int, float)):
                print(f"    - Market cap: ${market_cap:,}")
            else:
                print(f"    - Market cap: {market_cap}")
            print(f"    - P/E ratio: {yf_data.get('pe_ratio', 'N/A')}")
            print(f"    - Historical data points: {yf_data.get('historical_data_points', 0)}")
            print()
            print("  ✓ Yahoo Finance provides ALL essential data!")

    print()

    # Get memory metrics
    print("=" * 80)
    print("MEMORY METRICS")
    print("=" * 80)
    memory_metrics = prefetcher.get_memory_metrics()
    print(f"  Initial memory: {memory_metrics['initial_memory_mb']} MB")
    print(f"  Peak memory: {memory_metrics['peak_memory_mb']} MB")
    print(f"  Final memory: {memory_metrics['final_memory_mb']} MB")
    print(f"  Memory increase: {memory_metrics['memory_increase_mb']} MB")
    print(f"  Within limit: {'✓ Yes' if memory_metrics['within_limit'] else '✗ No'}")
    print()

    # Validate memory constraints
    if prefetcher.validate_memory_constraints():
        print("✓ Memory constraints validated")
    else:
        print("✗ Memory constraints violated")
    print()

    # Clean up
    print("=" * 80)
    print("CLEANUP")
    print("=" * 80)
    cleanup_result = prefetcher.cleanup_cache()
    print(f"  Files removed: {cleanup_result['files_removed']}")
    print(f"  Disk freed: {cleanup_result['disk_freed_mb']} MB")
    print(f"  Success: {'✓ Yes' if cleanup_result['success'] else '✗ No'}")
    print()

    print("=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    print()
    print("Key Takeaways:")
    print("  1. Yahoo Finance is the PRIMARY data source (always used)")
    print("  2. Yahoo Finance provides ALL essential data")
    print("  3. Yahoo Finance is FAST (~2-5 seconds for 66 tickers)")
    print("  4. Alpha Vantage is OPTIONAL and DISABLED by default")
    print("  5. Alpha Vantage adds ~13 minutes with minimal benefit")
    print("  6. Recommendation: Use Yahoo Finance only for optimal performance")
    print()


if __name__ == "__main__":
    main()
