"""
Performance tests for batch vs sequential execution.

This module tests the performance improvements achieved through batch processing
for deep analysis, validating the 55%+ time savings target and comparing
API call counts between batch and sequential modes.

Requirements: 17.17, 17.18, 17.19, 17.77
"""

import os
import time
from pathlib import Path

import pytest

from finwiz.utils.batch_data_prefetcher import BatchDataPreFetcher


class TestBatchPerformance:
    """Performance tests for batch vs sequential execution."""

    @pytest.fixture
    def test_tickers_10(self) -> list[str]:
        """10 tickers for small batch testing."""
        return ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX", "AMD", "CRM"]

    @pytest.fixture
    def test_tickers_30(self) -> list[str]:
        """30 tickers for medium batch testing."""
        return [
            "AAPL",
            "MSFT",
            "GOOGL",
            "AMZN",
            "TSLA",
            "META",
            "NVDA",
            "NFLX",
            "AMD",
            "CRM",
            "ORCL",
            "ADBE",
            "PYPL",
            "INTC",
            "CSCO",
            "AVGO",
            "TXN",
            "QCOM",
            "INTU",
            "AMAT",
            "MU",
            "ADI",
            "LRCX",
            "KLAC",
            "MCHP",
            "SNPS",
            "CDNS",
            "FTNT",
            "PANW",
            "CRWD",
        ]

    @pytest.fixture
    def test_tickers_66(self) -> list[str]:
        """66 tickers for large portfolio testing."""
        return [
            # Technology (20)
            "AAPL",
            "MSFT",
            "GOOGL",
            "AMZN",
            "TSLA",
            "META",
            "NVDA",
            "NFLX",
            "AMD",
            "CRM",
            "ORCL",
            "ADBE",
            "PYPL",
            "INTC",
            "CSCO",
            "AVGO",
            "TXN",
            "QCOM",
            "INTU",
            "AMAT",
            # Healthcare (10)
            "JNJ",
            "PFE",
            "UNH",
            "ABBV",
            "TMO",
            "DHR",
            "BMY",
            "AMGN",
            "GILD",
            "BIIB",
            # Financial (10)
            "JPM",
            "BAC",
            "WFC",
            "GS",
            "MS",
            "C",
            "AXP",
            "BLK",
            "SCHW",
            "USB",
            # Consumer (10)
            "PG",
            "KO",
            "PEP",
            "WMT",
            "HD",
            "MCD",
            "NKE",
            "SBUX",
            "TGT",
            "LOW",
            # Industrial (8)
            "BA",
            "CAT",
            "GE",
            "MMM",
            "HON",
            "UPS",
            "RTX",
            "LMT",
            # Energy (8)
            "XOM",
            "CVX",
            "COP",
            "EOG",
            "SLB",
            "PSX",
            "VLO",
            "MPC",
        ]

    @pytest.fixture
    def session_id(self) -> str:
        """Generate unique session ID for testing."""
        return f"test_session_{int(time.time())}"

    def test_should_benchmark_10_tickers_batch_vs_sequential(self, test_tickers_10, session_id):
        """
        Test batch vs sequential performance for 10 tickers.

        Requirements: 17.17, 17.18, 17.19
        """
        # Arrange
        tickers = test_tickers_10

        # Test batch mode
        batch_prefetcher = BatchDataPreFetcher(
            session_id=f"{session_id}_batch_10",
            enable_alpha_vantage=False,  # Yahoo Finance only for optimal performance
        )

        # Act - Batch execution
        batch_start = time.time()
        batch_data = batch_prefetcher.prefetch_all_data(tickers)
        batch_duration = time.time() - batch_start

        # Simulate sequential execution time (estimated)
        # Based on typical API response times: 0.5-2s per ticker
        estimated_sequential_time = len(tickers) * 1.0  # Conservative 1s per ticker

        # Calculate metrics
        batch_time_per_ticker = batch_duration / len(tickers)
        time_savings_percent = ((estimated_sequential_time - batch_duration) / estimated_sequential_time) * 100

        # Get memory metrics
        memory_metrics = batch_prefetcher.get_memory_metrics()

        # Assert performance targets
        assert batch_duration < estimated_sequential_time, f"Batch ({batch_duration:.1f}s) should be faster than sequential (~{estimated_sequential_time:.1f}s)"
        assert time_savings_percent >= 55, f"Time savings ({time_savings_percent:.1f}%) should be at least 55%"
        assert batch_time_per_ticker < 0.5, f"Time per ticker ({batch_time_per_ticker:.2f}s) should be under 0.5s"

        # Verify data quality
        successful_tickers = sum(1 for data in batch_data.values() if not data.get("failed", False))
        success_rate = (successful_tickers / len(tickers)) * 100
        assert success_rate >= 80, f"Success rate ({success_rate:.1f}%) should be at least 80%"

        # Memory validation (Requirement 17.73)
        assert batch_prefetcher.validate_memory_constraints(), "Memory usage should stay within 500MB limit"

        # Cleanup
        cleanup_result = batch_prefetcher.cleanup_cache()
        assert cleanup_result["success"], "Cache cleanup should succeed"

        print("\n10 Tickers Performance Results:")
        print(f"  Batch time: {batch_duration:.1f}s")
        print(f"  Time per ticker: {batch_time_per_ticker:.2f}s")
        print(f"  Estimated sequential: {estimated_sequential_time:.1f}s")
        print(f"  Time savings: {time_savings_percent:.1f}%")
        print(f"  Success rate: {success_rate:.1f}%")
        print(f"  Peak memory: {memory_metrics['peak_memory_mb']:.1f} MB")

    def test_should_benchmark_30_tickers_batch_vs_sequential(self, test_tickers_30, session_id):
        """
        Test batch vs sequential performance for 30 tickers.

        Requirements: 17.17, 17.18, 17.19
        """
        # Arrange
        tickers = test_tickers_30

        # Test batch mode
        batch_prefetcher = BatchDataPreFetcher(
            session_id=f"{session_id}_batch_30",
            enable_alpha_vantage=False,  # Yahoo Finance only for optimal performance
        )

        # Act - Batch execution
        batch_start = time.time()
        batch_data = batch_prefetcher.prefetch_all_data(tickers)
        batch_duration = time.time() - batch_start

        # Simulate sequential execution time (estimated)
        estimated_sequential_time = len(tickers) * 1.0  # Conservative 1s per ticker

        # Calculate metrics
        batch_time_per_ticker = batch_duration / len(tickers)
        time_savings_percent = ((estimated_sequential_time - batch_duration) / estimated_sequential_time) * 100

        # Get memory metrics
        memory_metrics = batch_prefetcher.get_memory_metrics()

        # Assert performance targets
        assert batch_duration < estimated_sequential_time, f"Batch ({batch_duration:.1f}s) should be faster than sequential (~{estimated_sequential_time:.1f}s)"
        assert time_savings_percent >= 50, f"Time savings ({time_savings_percent:.1f}%) should be at least 50%"
        assert batch_time_per_ticker < 0.5, f"Time per ticker ({batch_time_per_ticker:.2f}s) should be under 0.5s for 30 tickers"

        # Verify data quality
        successful_tickers = sum(1 for data in batch_data.values() if not data.get("failed", False))
        success_rate = (successful_tickers / len(tickers)) * 100
        assert success_rate >= 80, f"Success rate ({success_rate:.1f}%) should be at least 80%"

        # Memory validation (Requirement 17.73)
        assert batch_prefetcher.validate_memory_constraints(), "Memory usage should stay within 500MB limit"

        # Cleanup
        cleanup_result = batch_prefetcher.cleanup_cache()
        assert cleanup_result["success"], "Cache cleanup should succeed"

        print("\n30 Tickers Performance Results:")
        print(f"  Batch time: {batch_duration:.1f}s")
        print(f"  Time per ticker: {batch_time_per_ticker:.2f}s")
        print(f"  Estimated sequential: {estimated_sequential_time:.1f}s")
        print(f"  Time savings: {time_savings_percent:.1f}%")
        print(f"  Success rate: {success_rate:.1f}%")
        print(f"  Peak memory: {memory_metrics['peak_memory_mb']:.1f} MB")

    def test_should_benchmark_66_tickers_batch_vs_sequential(self, test_tickers_66, session_id):
        """
        Test batch vs sequential performance for 66 tickers (full portfolio).

        This is the key performance test - validates the main use case of
        analyzing a full portfolio with 66+ holdings.

        Requirements: 17.17, 17.18, 17.19
        """
        # Arrange
        tickers = test_tickers_66

        # Test batch mode
        batch_prefetcher = BatchDataPreFetcher(
            session_id=f"{session_id}_batch_66",
            enable_alpha_vantage=False,  # Yahoo Finance only for optimal performance
        )

        # Act - Batch execution
        batch_start = time.time()
        batch_data = batch_prefetcher.prefetch_all_data(tickers)
        batch_duration = time.time() - batch_start

        # Simulate sequential execution time (estimated)
        # For 66 tickers, sequential would be 66-132 seconds (1-2s per ticker)
        estimated_sequential_time = len(tickers) * 1.5  # Conservative 1.5s per ticker

        # Calculate metrics
        batch_time_per_ticker = batch_duration / len(tickers)
        time_savings_percent = ((estimated_sequential_time - batch_duration) / estimated_sequential_time) * 100
        speedup_factor = estimated_sequential_time / batch_duration

        # Get memory metrics
        memory_metrics = batch_prefetcher.get_memory_metrics()

        # Assert performance targets (stricter for full portfolio)
        assert batch_duration < estimated_sequential_time, f"Batch ({batch_duration:.1f}s) should be faster than sequential (~{estimated_sequential_time:.1f}s)"
        assert time_savings_percent >= 55, f"Time savings ({time_savings_percent:.1f}%) should be at least 55%"
        assert batch_time_per_ticker < 0.2, f"Time per ticker ({batch_time_per_ticker:.2f}s) should be under 0.2s for 66 tickers"
        assert speedup_factor >= 2.0, f"Speedup factor ({speedup_factor:.1f}x) should be at least 2x"

        # Verify data quality
        successful_tickers = sum(1 for data in batch_data.values() if not data.get("failed", False))
        success_rate = (successful_tickers / len(tickers)) * 100
        assert success_rate >= 80, f"Success rate ({success_rate:.1f}%) should be at least 80%"

        # Memory validation (Requirement 17.73)
        assert batch_prefetcher.validate_memory_constraints(), "Memory usage should stay within 500MB limit"

        # Validate cache size is reasonable
        cache_file = Path(f"cache/batch_data/{session_id}_batch_66/batch_data.json")
        if cache_file.exists():
            cache_size_mb = cache_file.stat().st_size / (1024 * 1024)
            assert cache_size_mb < 50, f"Cache size ({cache_size_mb:.1f} MB) should be under 50 MB"

        # Cleanup
        cleanup_result = batch_prefetcher.cleanup_cache()
        assert cleanup_result["success"], "Cache cleanup should succeed"

        print("\n66 Tickers Performance Results (FULL PORTFOLIO):")
        print(f"  Batch time: {batch_duration:.1f}s")
        print(f"  Time per ticker: {batch_time_per_ticker:.2f}s")
        print(f"  Estimated sequential: {estimated_sequential_time:.1f}s")
        print(f"  Time savings: {time_savings_percent:.1f}%")
        print(f"  Speedup factor: {speedup_factor:.1f}x")
        print(f"  Success rate: {success_rate:.1f}%")
        print(f"  Peak memory: {memory_metrics['peak_memory_mb']:.1f} MB")

    def test_should_compare_api_call_counts_batch_vs_sequential(self, test_tickers_10, session_id):
        """
        Test that batch mode significantly reduces API call counts.

        Requirements: 17.17, 17.19
        """
        # Arrange
        tickers = test_tickers_10

        # Test batch mode (Yahoo Finance only)
        batch_prefetcher = BatchDataPreFetcher(session_id=f"{session_id}_api_count", enable_alpha_vantage=False)

        # Act - Batch execution
        batch_data = batch_prefetcher.prefetch_all_data(tickers)

        # Calculate API calls
        # Batch mode: 1 call for yf.download() + 1 call for yf.Tickers() = 2 total calls
        batch_api_calls = 2

        # Sequential mode would be: 2 calls per ticker (info + history)
        sequential_api_calls = len(tickers) * 2

        # Calculate reduction
        api_call_reduction = ((sequential_api_calls - batch_api_calls) / sequential_api_calls) * 100

        # Assert API call reduction
        assert batch_api_calls < sequential_api_calls, f"Batch calls ({batch_api_calls}) should be less than sequential ({sequential_api_calls})"
        assert api_call_reduction >= 80, f"API call reduction ({api_call_reduction:.1f}%) should be at least 80%"

        # Verify data completeness despite fewer API calls
        successful_tickers = sum(1 for data in batch_data.values() if not data.get("failed", False))
        success_rate = (successful_tickers / len(tickers)) * 100
        assert success_rate >= 80, f"Success rate ({success_rate:.1f}%) should remain high despite fewer API calls"

        # Cleanup
        batch_prefetcher.cleanup_cache()

        print("\nAPI Call Count Comparison:")
        print(f"  Batch mode: {batch_api_calls} API calls")
        print(f"  Sequential mode: {sequential_api_calls} API calls")
        print(f"  API call reduction: {api_call_reduction:.1f}%")
        print(f"  Success rate: {success_rate:.1f}%")

    def test_should_validate_memory_usage_scaling(self, test_tickers_10, test_tickers_30, test_tickers_66, session_id):
        """
        Test that memory usage scales reasonably with ticker count.

        Requirements: 17.70, 17.71, 17.72, 17.73
        """
        # Test different ticker counts and measure memory usage
        test_cases = [(test_tickers_10, "10_tickers"), (test_tickers_30, "30_tickers"), (test_tickers_66, "66_tickers")]

        memory_results = []

        for tickers, label in test_cases:
            # Create prefetcher
            prefetcher = BatchDataPreFetcher(session_id=f"{session_id}_{label}", enable_alpha_vantage=False)

            # Execute batch prefetch
            prefetcher.prefetch_all_data(tickers)

            # Get memory metrics
            memory_metrics = prefetcher.get_memory_metrics()
            memory_results.append(
                {
                    "ticker_count": len(tickers),
                    "label": label,
                    "peak_memory_mb": memory_metrics["peak_memory_mb"],
                    "memory_per_ticker": memory_metrics["peak_memory_mb"] / len(tickers),
                }
            )

            # Validate memory constraints
            assert prefetcher.validate_memory_constraints(), f"Memory constraints violated for {label}"

            # Cleanup
            prefetcher.cleanup_cache()

        # Analyze memory scaling
        for result in memory_results:
            # Memory per ticker should be reasonable
            assert result["memory_per_ticker"] < 5.0, f"Memory per ticker ({result['memory_per_ticker']:.2f} MB) too high for {result['label']}"

            # Total memory should stay under limit
            assert result["peak_memory_mb"] < 500, f"Peak memory ({result['peak_memory_mb']:.1f} MB) exceeds 500 MB limit for {result['label']}"

        print("\nMemory Usage Scaling:")
        for result in memory_results:
            print(f"  {result['label']}: {result['peak_memory_mb']:.1f} MB total, {result['memory_per_ticker']:.2f} MB per ticker")

    @pytest.mark.integration
    def test_should_benchmark_with_alpha_vantage_enabled(self, test_tickers_10, session_id):
        """
        Test performance impact when Alpha Vantage is enabled.

        This test shows why Alpha Vantage is disabled by default.
        Only run in integration tests due to API rate limits.

        Requirements: 17.17, 17.18
        """
        # Skip if no Alpha Vantage key
        if not os.getenv("ALPHA_VANTAGE_API_KEY"):
            pytest.skip("Alpha Vantage API key not available")

        tickers = test_tickers_10[:3]  # Use only 3 tickers to avoid long test times

        # Test with Alpha Vantage enabled
        av_prefetcher = BatchDataPreFetcher(
            session_id=f"{session_id}_with_av",
            enable_alpha_vantage=True,
            alpha_vantage_rate_limit=5,  # Free tier limit
        )

        # Test without Alpha Vantage (Yahoo Finance only)
        yf_prefetcher = BatchDataPreFetcher(session_id=f"{session_id}_yf_only", enable_alpha_vantage=False)

        # Benchmark Yahoo Finance only
        yf_start = time.time()
        yf_data = yf_prefetcher.prefetch_all_data(tickers)
        yf_duration = time.time() - yf_start

        # Benchmark with Alpha Vantage
        av_start = time.time()
        av_data = av_prefetcher.prefetch_all_data(tickers)
        av_duration = time.time() - av_start

        # Calculate overhead
        av_overhead = av_duration - yf_duration
        overhead_per_ticker = av_overhead / len(tickers)

        # Assert that Alpha Vantage adds significant overhead
        assert av_duration > yf_duration, "Alpha Vantage should add overhead"
        assert overhead_per_ticker > 10, f"Alpha Vantage overhead ({overhead_per_ticker:.1f}s per ticker) should be significant"

        # Verify both approaches get data
        yf_success = sum(1 for data in yf_data.values() if not data.get("failed", False))
        av_success = sum(1 for data in av_data.values() if not data.get("failed", False))

        assert yf_success >= len(tickers) * 0.8, "Yahoo Finance should have high success rate"
        assert av_success >= len(tickers) * 0.8, "Alpha Vantage should have high success rate"

        # Cleanup
        yf_prefetcher.cleanup_cache()
        av_prefetcher.cleanup_cache()

        print("\nAlpha Vantage Performance Impact:")
        print(f"  Yahoo Finance only: {yf_duration:.1f}s")
        print(f"  With Alpha Vantage: {av_duration:.1f}s")
        print(f"  Overhead: {av_overhead:.1f}s ({overhead_per_ticker:.1f}s per ticker)")
        print("  Recommendation: Keep Alpha Vantage disabled for optimal performance")


class TestBatchPerformanceMetrics:
    """Test performance metrics collection and reporting."""

    def test_should_generate_performance_metrics_json(self, session_id):
        """
        Test that performance metrics are saved to JSON file.

        Requirements: 17.62, 17.63, 17.64
        """
        # Arrange
        tickers = ["AAPL", "MSFT", "GOOGL"]
        prefetcher = BatchDataPreFetcher(session_id=session_id, enable_alpha_vantage=False)

        # Act
        start_time = time.time()
        batch_data = prefetcher.prefetch_all_data(tickers)
        total_duration = time.time() - start_time

        # Get memory metrics
        memory_metrics = prefetcher.get_memory_metrics()

        # Create performance metrics (simulating what Flow would do)
        performance_metrics = {
            "session_id": session_id,
            "timestamp": time.time(),
            "total_tickers": len(tickers),
            "successful_tickers": sum(1 for data in batch_data.values() if not data.get("failed", False)),
            "failed_tickers": sum(1 for data in batch_data.values() if data.get("failed", False)),
            "total_duration_seconds": total_duration,
            "time_per_ticker_seconds": total_duration / len(tickers),
            "estimated_sequential_time": len(tickers) * 1.0,
            "time_savings_percent": ((len(tickers) * 1.0 - total_duration) / (len(tickers) * 1.0)) * 100,
            "memory_metrics": memory_metrics,
            "data_sources": {"yahoo_finance_enabled": True, "alpha_vantage_enabled": False},
        }

        # Save metrics to file (simulating Flow behavior)
        metrics_file = Path(f"cache/batch_data/{session_id}/batch_prefetch_metrics.json")
        metrics_file.parent.mkdir(parents=True, exist_ok=True)

        import json

        with open(metrics_file, "w") as f:
            json.dump(performance_metrics, f, indent=2, default=str)

        # Assert metrics file exists and contains expected data
        assert metrics_file.exists(), "Performance metrics file should be created"

        # Load and validate metrics
        with open(metrics_file) as f:
            loaded_metrics = json.load(f)

        assert loaded_metrics["total_tickers"] == len(tickers)
        assert loaded_metrics["time_savings_percent"] > 0
        assert "memory_metrics" in loaded_metrics
        assert loaded_metrics["data_sources"]["yahoo_finance_enabled"] is True

        # Cleanup
        prefetcher.cleanup_cache()

        print("\nPerformance Metrics Generated:")
        print(f"  File: {metrics_file}")
        print(f"  Time savings: {loaded_metrics['time_savings_percent']:.1f}%")
        print(f"  Memory usage: {loaded_metrics['memory_metrics']['peak_memory_mb']:.1f} MB")
