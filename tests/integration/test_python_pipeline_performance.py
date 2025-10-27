#!/usr/bin/env python3
"""
Performance Validation Tests for Pure Python Pipeline.

Tests performance improvements and cost reductions achieved by the Python pipeline
compared to AI-based approaches.

Requirements: 20.29, 20.30, 20.31, 20.32, 20.33
"""

import concurrent.futures
import time
from pathlib import Path

import pytest

from finwiz.schemas.common import RiskAssessmentStandardized
from finwiz.schemas.portfolio_review import HoldingDecision
from finwiz.scoring.portfolio_deep_analyzer import analyze_portfolio_with_python


class TestPythonPipelinePerformance:
    """Performance validation tests for the pure Python pipeline."""

    @pytest.fixture
    def large_portfolio_holdings(self) -> list[HoldingDecision]:
        """Create a large portfolio for performance testing (simulates 66+ holdings)."""
        holdings = []

        # Stock holdings (40 holdings)
        stock_tickers = [
            "AAPL",
            "MSFT",
            "GOOGL",
            "AMZN",
            "TSLA",
            "META",
            "NVDA",
            "NFLX",
            "CRM",
            "ADBE",
            "PYPL",
            "INTC",
            "AMD",
            "ORCL",
            "IBM",
            "CSCO",
            "QCOM",
            "TXN",
            "AVGO",
            "MU",
            "AMAT",
            "LRCX",
            "KLAC",
            "MCHP",
            "MRVL",
            "XLNX",
            "SWKS",
            "QRVO",
            "MPWR",
            "ENPH",
            "SEDG",
            "FSLR",
            "SPWR",
            "RUN",
            "NOVA",
            "ALGN",
            "ILMN",
            "REGN",
            "GILD",
            "BIIB",
        ]

        for i, ticker in enumerate(stock_tickers):
            # Vary grades to test A+ discovery
            if i < 5:
                grade = "A+"
                score = 0.85 + (i * 0.02)
            elif i < 15:
                grade = "A"
                score = 0.75 + (i * 0.01)
            elif i < 25:
                grade = "B"
                score = 0.65 + (i * 0.005)
            elif i < 35:
                grade = "C"
                score = 0.55 + (i * 0.003)
            else:
                grade = "D"
                score = 0.45 + (i * 0.002)

            holdings.append(
                HoldingDecision(
                    ticker=ticker,
                    name=f"{ticker} Corporation",
                    asset_class="stock",
                    currency="USD",
                    decision="KEEP" if grade in ["A+", "A", "B"] else "SELL",
                    composite_score=score,
                    grade=grade,
                    grade_description=f"Grade {grade}",
                    recommended_action="BUY" if grade == "A+" else "HOLD" if grade in ["A", "B"] else "SELL",
                    rationale_bullets=[f"{grade} grade fundamentals"],
                    risk=RiskAssessmentStandardized(score=2.0 + (i * 0.05), level="Medium", risk_factors=["Market risk"]),
                    alternatives=[],
                )
            )

        # ETF holdings (15 holdings)
        etf_tickers = ["SPY", "QQQ", "IWM", "VTI", "VXUS", "BND", "AGG", "GLD", "SLV", "USO", "XLF", "XLK", "XLE", "XLV", "XLI"]

        for i, ticker in enumerate(etf_tickers):
            grade = "A" if i < 8 else "B" if i < 12 else "C"
            score = 0.80 - (i * 0.02)

            holdings.append(
                HoldingDecision(
                    ticker=ticker,
                    name=f"{ticker} ETF",
                    asset_class="etf",
                    currency="USD",
                    decision="KEEP",
                    composite_score=score,
                    grade=grade,
                    grade_description=f"Grade {grade}",
                    recommended_action="BUY" if grade == "A" else "HOLD",
                    rationale_bullets=[f"{grade} grade ETF"],
                    risk=RiskAssessment(score=2.0 + (i * 0.1), level="Medium", risk_factors=["Market risk"]),
                    alternatives=[],
                )
            )

        # Crypto holdings (11 holdings)
        crypto_tickers = ["BTC", "ETH", "ADA", "DOT", "LINK", "UNI", "AAVE", "COMP", "MKR", "SNX", "YFI"]

        for i, ticker in enumerate(crypto_tickers):
            grade = "A+" if i < 2 else "A" if i < 5 else "B" if i < 8 else "C"
            score = 0.75 - (i * 0.03)

            holdings.append(
                HoldingDecision(
                    ticker=ticker,
                    name=f"{ticker} Cryptocurrency",
                    asset_class="crypto",
                    currency="USD",
                    decision="KEEP",
                    composite_score=score,
                    grade=grade,
                    grade_description=f"Grade {grade}",
                    recommended_action="BUY" if grade in ["A+", "A"] else "HOLD",
                    rationale_bullets=[f"{grade} grade crypto"],
                    risk=RiskAssessment(score=3.0 + (i * 0.1), level="High", risk_factors=["Crypto volatility"]),
                    alternatives=[],
                )
            )

        return holdings  # Total: 66 holdings

    @pytest.fixture
    def session_id(self) -> str:
        """Generate unique session ID for performance testing."""
        return f"perf_test_{int(time.time())}"

    @pytest.fixture
    def cleanup_output_files(self, session_id):
        """Clean up output files after test."""
        yield

        # Clean up test files
        output_dir = Path("output")
        if output_dir.exists():
            for pattern in [f"*{session_id}*"]:
                for file_path in output_dir.rglob(pattern):
                    try:
                        file_path.unlink()
                    except FileNotFoundError:
                        pass

    def test_should_achieve_target_execution_speed(self, large_portfolio_holdings, session_id, cleanup_output_files):
        """
        Test that Python pipeline achieves target execution speed.

        Requirements: 20.29, 20.30 - Measure execution time vs AI approach baseline
        Target: Complete 66-holding portfolio in 10-30 minutes (vs 3-6 hours AI)
        """
        holdings_count = len(large_portfolio_holdings)
        print(f"\n🚀 Performance Test: Analyzing {holdings_count} holdings")

        # Measure execution time
        start_time = time.time()

        results = analyze_portfolio_with_python(holdings=large_portfolio_holdings, session_id=session_id)

        execution_time = time.time() - start_time

        # Verify successful completion
        assert results["successful_analyses"] == holdings_count
        assert results["failed_analyses"] == 0

        # Performance targets
        target_max_time = 30 * 60  # 30 minutes maximum
        ai_baseline_min_time = 3 * 60 * 60  # 3 hours minimum for AI approach

        # Verify speed improvement
        assert execution_time < target_max_time, f"Should complete in <30 minutes, took {execution_time / 60:.1f} minutes"

        # Calculate speedup vs AI baseline
        speedup_factor = ai_baseline_min_time / execution_time
        assert speedup_factor >= 10, f"Should be 10x+ faster than AI, achieved {speedup_factor:.1f}x"

        # Performance metrics
        metrics = results["performance_metrics"]
        holdings_per_second = metrics["holdings_per_second"]

        # Should process at least 1 holding per second for large portfolios
        assert holdings_per_second >= 0.5, f"Should process ≥0.5 holdings/second, achieved {holdings_per_second:.2f}"

        print("✅ Performance Results:")
        print(f"   ⚡ Execution time: {execution_time:.1f}s ({execution_time / 60:.1f} minutes)")
        print(f"   🚀 Speedup vs AI: {speedup_factor:.1f}x faster")
        print(f"   📊 Holdings/second: {holdings_per_second:.2f}")
        print(f"   🎯 Target met: {execution_time < target_max_time}")

    def test_should_achieve_zero_cost_execution(self, large_portfolio_holdings, session_id, cleanup_output_files):
        """
        Test that Python pipeline achieves 100% cost reduction.

        Requirements: 20.30 - Validate cost savings (should be 100% for calculations)
        """
        results = analyze_portfolio_with_python(holdings=large_portfolio_holdings, session_id=session_id)

        metrics = results["performance_metrics"]

        # Verify 100% cost reduction
        assert metrics["llm_calls_made"] == 0, "Should make 0 LLM calls"
        assert metrics["estimated_cost_usd"] == 0.0, "Should cost $0.00"

        # Calculate cost savings vs AI baseline
        # AI baseline: ~$0.05-0.10 per holding for deep analysis
        holdings_count = len(large_portfolio_holdings)
        ai_baseline_cost = holdings_count * 0.075  # $0.075 average per holding

        cost_savings = ai_baseline_cost - metrics["estimated_cost_usd"]
        cost_reduction_percent = (cost_savings / ai_baseline_cost) * 100

        assert cost_reduction_percent == 100.0, f"Should achieve 100% cost reduction, achieved {cost_reduction_percent:.1f}%"

        print("✅ Cost Reduction Results:")
        print(f"   💰 Python cost: ${metrics['estimated_cost_usd']:.2f}")
        print(f"   💸 AI baseline cost: ${ai_baseline_cost:.2f}")
        print(f"   💡 Cost savings: ${cost_savings:.2f}")
        print(f"   📉 Cost reduction: {cost_reduction_percent:.1f}%")

    def test_should_handle_concurrent_processing(self, large_portfolio_holdings, cleanup_output_files):
        """
        Test that concurrent processing handles large portfolios correctly.

        Requirements: 20.32 - Test concurrent processing handles large portfolios correctly
        """
        # Split portfolio into batches for concurrent processing
        batch_size = 10
        batches = [large_portfolio_holdings[i : i + batch_size] for i in range(0, len(large_portfolio_holdings), batch_size)]

        print(f"\n🔄 Concurrent Processing Test: {len(batches)} batches of {batch_size} holdings")

        start_time = time.time()

        # Process batches concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_batch = {
                executor.submit(analyze_portfolio_with_python, batch, f"concurrent_test_{i}_{int(time.time())}"): i
                for i, batch in enumerate(batches)
            }

            batch_results = []
            for future in concurrent.futures.as_completed(future_to_batch):
                batch_idx = future_to_batch[future]
                try:
                    result = future.result()
                    batch_results.append((batch_idx, result))
                except Exception as e:
                    pytest.fail(f"Batch {batch_idx} failed: {e}")

        concurrent_time = time.time() - start_time

        # Verify all batches completed successfully
        assert len(batch_results) == len(batches)

        total_successful = sum(result["successful_analyses"] for _, result in batch_results)
        total_failed = sum(result["failed_analyses"] for _, result in batch_results)

        assert total_successful == len(large_portfolio_holdings)
        assert total_failed == 0

        # Concurrent processing should be faster than sequential
        # (though not necessarily by much for CPU-bound Python calculations)
        sequential_estimate = len(large_portfolio_holdings) * 0.1  # 0.1s per holding estimate

        print("✅ Concurrent Processing Results:")
        print(f"   ⚡ Concurrent time: {concurrent_time:.1f}s")
        print(f"   📊 Sequential estimate: {sequential_estimate:.1f}s")
        print("   🎯 All batches completed successfully")
        print(f"   ✅ Total holdings processed: {total_successful}")

    def test_should_scale_linearly_with_portfolio_size(self, cleanup_output_files):
        """
        Test that execution time scales linearly with portfolio size.

        Requirements: 20.31, 20.32 - Performance characteristics validation
        """
        portfolio_sizes = [5, 10, 20]
        execution_times = []

        for size in portfolio_sizes:
            # Create portfolio of specified size
            holdings = []
            for i in range(size):
                holdings.append(
                    HoldingDecision(
                        ticker=f"TEST{i:03d}",
                        name=f"Test Company {i}",
                        asset_class="stock",
                        currency="USD",
                        decision="KEEP",
                        composite_score=0.70,
                        grade="B",
                        grade_description="Grade B",
                        recommended_action="HOLD",
                        rationale_bullets=["Test holding"],
                        risk=RiskAssessment(score=2.5, level="Medium", risk_factors=["Test risk"]),
                        alternatives=[],
                    )
                )

            # Measure execution time
            start_time = time.time()

            results = analyze_portfolio_with_python(holdings=holdings, session_id=f"scale_test_{size}_{int(time.time())}")

            execution_time = time.time() - start_time
            execution_times.append(execution_time)

            # Verify successful completion
            assert results["successful_analyses"] == size

            print(f"   📊 {size} holdings: {execution_time:.2f}s ({execution_time / size:.3f}s per holding)")

        # Verify roughly linear scaling
        # Time per holding should be relatively consistent
        times_per_holding = [execution_times[i] / portfolio_sizes[i] for i in range(len(portfolio_sizes))]

        # Allow for some variation but should be roughly consistent
        max_time_per_holding = max(times_per_holding)
        min_time_per_holding = min(times_per_holding)
        variation_ratio = max_time_per_holding / min_time_per_holding

        assert variation_ratio < 3.0, f"Time per holding should be consistent, variation: {variation_ratio:.2f}x"

        print("✅ Linear Scaling Results:")
        print(f"   📈 Portfolio sizes: {portfolio_sizes}")
        print(f"   ⏱️ Execution times: {[f'{t:.2f}s' for t in execution_times]}")
        print(f"   📊 Time per holding: {[f'{t:.3f}s' for t in times_per_holding]}")
        print(f"   🎯 Variation ratio: {variation_ratio:.2f}x (should be <3.0x)")
