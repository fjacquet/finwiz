"""
Performance benchmark for portfolio holdings analysis.

Demonstrates the performance improvements from caching, rate limiting,
and parallel processing optimizations.
"""

import asyncio
import time
from datetime import datetime

from finwiz.tools.holding_analyzer_orchestrator import HoldingAnalyzerOrchestrator


async def benchmark_parallel_processing() -> None:
    """Benchmark parallel processing performance."""
    print("=" * 80)
    print("Portfolio Holdings Analysis - Performance Benchmark")
    print("=" * 80)
    print()

    # Create test portfolio with varying sizes
    portfolio_sizes = [10, 25, 50]

    for size in portfolio_sizes:
        print(f"\n📊 Testing with {size} holdings...")
        print("-" * 80)

        # Create sample holdings
        holdings = [
            {
                "ticker": f"TEST{i:03d}",
                "asset_class": "stock" if i % 3 == 0 else ("etf" if i % 3 == 1 else "crypto"),
                "currency": "USD",
                "name": f"Test Company {i}",
            }
            for i in range(size)
        ]

        # Test with caching and parallel processing enabled
        orchestrator_optimized = HoldingAnalyzerOrchestrator(
            enable_caching=True,
            enable_rate_limiting=True,
            parallel_batch_size=10,
        )

        start_time = time.time()
        results_optimized = await orchestrator_optimized.analyze_holdings_parallel(holdings)
        elapsed_optimized = time.time() - start_time

        print(f"✅ Optimized (caching + parallel): {elapsed_optimized:.2f}s")
        print(f"   - Holdings analyzed: {len(results_optimized)}")
        print(f"   - Average per holding: {elapsed_optimized / len(results_optimized):.3f}s")
        print(f"   - Batch size: {orchestrator_optimized.parallel_batch_size}")

        # Test without optimizations (sequential)
        orchestrator_basic = HoldingAnalyzerOrchestrator(
            enable_caching=False,
            enable_rate_limiting=False,
            parallel_batch_size=1,  # Sequential processing
        )

        start_time = time.time()
        results_basic = await orchestrator_basic.analyze_holdings_parallel(holdings)
        elapsed_basic = time.time() - start_time

        print(f"⚠️  Basic (no cache, sequential): {elapsed_basic:.2f}s")
        print(f"   - Holdings analyzed: {len(results_basic)}")
        print(f"   - Average per holding: {elapsed_basic / len(results_basic):.3f}s")

        # Calculate improvement
        improvement = ((elapsed_basic - elapsed_optimized) / elapsed_basic) * 100
        print(f"\n💡 Performance improvement: {improvement:.1f}%")
        print(f"   - Time saved: {elapsed_basic - elapsed_optimized:.2f}s")

        # Performance targets
        if size < 20:
            target = 300  # 5 minutes
            target_label = "Small portfolio (< 20 holdings)"
        elif size < 50:
            target = 900  # 15 minutes
            target_label = "Medium portfolio (20-50 holdings)"
        else:
            target = 1800  # 30 minutes
            target_label = "Large portfolio (50-100 holdings)"

        print(f"\n🎯 Target: {target_label} < {target}s")
        if elapsed_optimized < target:
            print(f"   ✅ PASSED - Completed in {elapsed_optimized:.2f}s")
        else:
            print(f"   ❌ EXCEEDED - Took {elapsed_optimized:.2f}s")


async def benchmark_caching() -> None:
    """Benchmark caching effectiveness."""
    print("\n" + "=" * 80)
    print("Caching Performance Benchmark")
    print("=" * 80)
    print()

    orchestrator = HoldingAnalyzerOrchestrator(
        enable_caching=True,
        enable_rate_limiting=False,
    )

    # First run - cold cache
    print("🔵 First run (cold cache)...")
    holdings = [
        {"ticker": "AAPL", "asset_class": "stock", "currency": "USD", "name": "Apple Inc."},
        {"ticker": "MSFT", "asset_class": "stock", "currency": "USD", "name": "Microsoft"},
        {"ticker": "GOOGL", "asset_class": "stock", "currency": "USD", "name": "Google"},
    ]

    start_time = time.time()
    results_cold = await orchestrator.analyze_holdings_parallel(holdings)
    elapsed_cold = time.time() - start_time

    print(f"   Time: {elapsed_cold:.2f}s")
    print(f"   Holdings: {len(results_cold)}")

    # Second run - warm cache
    print("\n🟢 Second run (warm cache)...")
    start_time = time.time()
    results_warm = await orchestrator.analyze_holdings_parallel(holdings)
    elapsed_warm = time.time() - start_time

    print(f"   Time: {elapsed_warm:.2f}s")
    print(f"   Holdings: {len(results_warm)}")

    # Calculate cache effectiveness
    speedup = elapsed_cold / elapsed_warm if elapsed_warm > 0 else 1
    print(f"\n💡 Cache speedup: {speedup:.1f}x faster")
    print(f"   - Time saved: {elapsed_cold - elapsed_warm:.2f}s")

    # Get cache statistics
    if orchestrator.cache_manager:
        stats = orchestrator.cache_manager.get_stats()
        print("\n📊 Cache Statistics:")
        print(f"   - Hit rate: {stats['hit_rate']:.1%}")
        print(f"   - Hits: {stats['hits']}")
        print(f"   - Misses: {stats['misses']}")
        print(f"   - Entries: {stats['entry_count']}")
        print(f"   - Memory usage: {stats['total_size_mb']:.2f} MB")


async def benchmark_rate_limiting() -> None:
    """Benchmark rate limiting behavior."""
    print("\n" + "=" * 80)
    print("Rate Limiting Benchmark")
    print("=" * 80)
    print()

    orchestrator = HoldingAnalyzerOrchestrator(
        enable_caching=False,
        enable_rate_limiting=True,
    )

    print("🚦 Testing rate limiting with rapid requests...")
    holdings = [{"ticker": f"TEST{i}", "asset_class": "stock", "currency": "USD", "name": f"Test {i}"} for i in range(5)]

    start_time = time.time()
    results = await orchestrator.analyze_holdings_parallel(holdings)
    elapsed = time.time() - start_time

    print(f"   Time: {elapsed:.2f}s")
    print(f"   Holdings: {len(results)}")
    print(f"   Average delay: {elapsed / len(results):.2f}s per holding")

    # Get rate limiter statistics
    if orchestrator.rate_limiter:
        from finwiz.utils.rate_limiter import APIProvider

        stats = orchestrator.rate_limiter.get_stats(APIProvider.YAHOO_FINANCE)
        print("\n📊 Rate Limiter Statistics:")
        print(f"   - Requests last minute: {stats['requests_last_minute']}")
        print(f"   - Requests last hour: {stats['requests_last_hour']}")
        print(f"   - Limit per minute: {stats['limit_per_minute']}")
        print(f"   - Total requests: {stats['total_requests']}")


async def main() -> None:
    """Run all benchmarks."""
    print("\n🚀 Starting Performance Benchmarks")
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        # Run benchmarks
        await benchmark_parallel_processing()
        await benchmark_caching()
        await benchmark_rate_limiting()

        print("\n" + "=" * 80)
        print("✅ All benchmarks completed successfully!")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
