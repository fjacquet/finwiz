"""
Perplexity Performance Benchmarking Utility.

Provides utilities for benchmarking Perplexity API performance, validating
response time requirements, and generating operational monitoring reports.
"""

from __future__ import annotations

import asyncio
import statistics
import time
from typing import Any, Literal, cast

from finwiz.tools.logger import get_logger
from finwiz.tools.perplexity_analysis_integration import (
    PerplexityAnalysisIntegration,
    PerplexityPerformanceMonitor,
)

logger = get_logger(__name__)


class PerplexityBenchmarkResult:
    """Results from a Perplexity performance benchmark."""

    def __init__(self, test_name: str) -> None:
        """Initialize benchmark results for a test."""
        self.test_name = test_name
        self.response_times: list[int] = []
        self.success_count = 0
        self.failure_count = 0
        self.start_time = time.time()
        self.end_time: float | None = None
        self.errors: list[str] = []

    def add_result(self, response_time_ms: int, success: bool, error: str | None = None) -> None:
        """Add a benchmark result."""
        self.response_times.append(response_time_ms)
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
            if error:
                self.errors.append(error)

    def finalize(self) -> None:
        """Finalize the benchmark results."""
        self.end_time = time.time()

    @property
    def total_requests(self) -> int:
        """Total number of requests made."""
        return self.success_count + self.failure_count

    @property
    def success_rate(self) -> float:
        """Success rate as a percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.success_count / self.total_requests) * 100

    @property
    def failure_rate(self) -> float:
        """Failure rate as a percentage."""
        return 100.0 - self.success_rate

    @property
    def duration_seconds(self) -> float:
        """Total benchmark duration in seconds."""
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time

    def get_performance_summary(self) -> dict[str, Any]:
        """Get comprehensive performance summary."""
        if not self.response_times:
            return {
                "test_name": self.test_name,
                "total_requests": self.total_requests,
                "success_count": self.success_count,
                "failure_count": self.failure_count,
                "success_rate": self.success_rate,
                "failure_rate": self.failure_rate,
                "duration_seconds": self.duration_seconds,
                "error": "No response times recorded",
            }

        # Calculate statistics
        avg_time = statistics.mean(self.response_times)
        median_time = statistics.median(self.response_times)
        min_time = min(self.response_times)
        max_time = max(self.response_times)

        # Calculate percentiles
        sorted_times = sorted(self.response_times)
        n = len(sorted_times)
        p95 = sorted_times[int(n * 0.95)] if n > 1 else sorted_times[0]
        p99 = sorted_times[int(n * 0.99)] if n > 1 else sorted_times[0]

        # Check compliance with requirements
        baseline_ms = PerplexityPerformanceMonitor.BASELINE_RESPONSE_TIME_MS
        max_acceptable_ms = PerplexityPerformanceMonitor.MAX_ACCEPTABLE_RESPONSE_TIME_MS
        compliant_responses = sum(1 for t in self.response_times if t <= max_acceptable_ms)
        compliance_rate = compliant_responses / len(self.response_times)

        return {
            "test_name": self.test_name,
            "total_requests": self.total_requests,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": round(self.success_rate, 2),
            "failure_rate": round(self.failure_rate, 2),
            "duration_seconds": round(self.duration_seconds, 2),
            "avg_response_time_ms": round(avg_time, 2),
            "median_response_time_ms": median_time,
            "min_response_time_ms": min_time,
            "max_response_time_ms": max_time,
            "p95_response_time_ms": p95,
            "p99_response_time_ms": p99,
            "baseline_ms": baseline_ms,
            "max_acceptable_ms": max_acceptable_ms,
            "compliance_rate": round(compliance_rate, 4),
            "meets_2x_baseline_requirement": compliance_rate >= 0.95,  # 95% of requests should meet requirement
            "avg_performance_ratio": round(avg_time / baseline_ms, 2),
            "error_types": list(set(self.errors)) if self.errors else [],
        }


class PerplexityPerformanceBenchmark:
    """Performance benchmarking utility for Perplexity integration."""

    def __init__(self, integration: PerplexityAnalysisIntegration | None = None) -> None:
        """Initialize the benchmark utility."""
        self.integration = integration or PerplexityAnalysisIntegration()

    async def benchmark_response_times(
        self,
        test_cases: list[dict[str, Any]],
        iterations: int = 5,
        concurrent_requests: int = 1,
    ) -> PerplexityBenchmarkResult:
        """
        Benchmark Perplexity API response times.

        Args:
            test_cases: List of test case dictionaries with query parameters
            iterations: Number of iterations per test case
            concurrent_requests: Number of concurrent requests to make

        Returns:
            PerplexityBenchmarkResult with performance metrics

        """
        result = PerplexityBenchmarkResult("response_time_benchmark")

        logger.info(f"Starting Perplexity response time benchmark: {len(test_cases)} test cases, {iterations} iterations, {concurrent_requests} concurrent requests")

        for test_case in test_cases:
            ticker = test_case.get("ticker", "AAPL")
            query = test_case.get("query", f"{ticker} financial news")
            asset_type = test_case.get("asset_type", "stock")
            analysis_type = test_case.get("analysis_type", "sentiment")

            logger.info(f"Benchmarking test case: {ticker} ({analysis_type})")

            for iteration in range(iterations):
                if concurrent_requests == 1:
                    # Sequential requests
                    await self._execute_single_benchmark(result, query, ticker, asset_type, analysis_type)
                else:
                    # Concurrent requests
                    tasks = [self._execute_single_benchmark(result, query, ticker, asset_type, analysis_type) for _ in range(concurrent_requests)]
                    await asyncio.gather(*tasks, return_exceptions=True)

        result.finalize()

        # Log summary
        summary = result.get_performance_summary()
        logger.info(f"Benchmark completed: {summary}")

        return result

    async def _execute_single_benchmark(self, result: PerplexityBenchmarkResult, query: str, ticker: str, asset_type: str, analysis_type: str) -> None:
        """Execute a single benchmark request."""
        start_time = PerplexityPerformanceMonitor.start_operation_timer()

        try:
            search_result = await self.integration.search_financial_news(
                query=query,
                ticker=ticker,
                asset_type=cast(Literal["stock", "etf", "crypto"], asset_type),
                analysis_type=cast(Literal["sentiment", "technical", "fundamental", "general"], analysis_type),
                max_results=5,
            )

            response_time_ms = PerplexityPerformanceMonitor.calculate_operation_time(start_time)
            success = search_result.success

            result.add_result(response_time_ms, success, search_result.error_message if not success else None)

        except Exception as e:
            response_time_ms = PerplexityPerformanceMonitor.calculate_operation_time(start_time)
            result.add_result(response_time_ms, False, str(e))

    async def validate_performance_requirements(self, sample_size: int = 20, max_failure_rate: float = 0.05) -> dict[str, Any]:
        """
        Validate that Perplexity integration meets performance requirements.

        Args:
            sample_size: Number of requests to test
            max_failure_rate: Maximum acceptable failure rate (default 5%)

        Returns:
            Validation results with pass/fail status

        """
        logger.info(f"Validating Perplexity performance requirements with {sample_size} requests")

        # Define test cases for validation
        test_cases = [
            {"ticker": "AAPL", "query": "Apple financial news", "asset_type": "stock", "analysis_type": "sentiment"},
            {"ticker": "SPY", "query": "SPY ETF analysis", "asset_type": "etf", "analysis_type": "technical"},
            {"ticker": "BTC-USD", "query": "Bitcoin market analysis", "asset_type": "crypto", "analysis_type": "fundamental"},
        ]

        # Run benchmark
        benchmark_result = await self.benchmark_response_times(test_cases=test_cases, iterations=sample_size // len(test_cases), concurrent_requests=1)

        summary = benchmark_result.get_performance_summary()

        # Validate requirements
        meets_response_time_req = summary["meets_2x_baseline_requirement"]
        meets_failure_rate_req = summary["failure_rate"] <= (max_failure_rate * 100)

        validation_result = {
            "validation_passed": meets_response_time_req and meets_failure_rate_req,
            "response_time_requirement_met": meets_response_time_req,
            "failure_rate_requirement_met": meets_failure_rate_req,
            "performance_summary": summary,
            "requirements": {
                "max_response_time_ms": PerplexityPerformanceMonitor.MAX_ACCEPTABLE_RESPONSE_TIME_MS,
                "max_failure_rate_percent": max_failure_rate * 100,
                "baseline_response_time_ms": PerplexityPerformanceMonitor.BASELINE_RESPONSE_TIME_MS,
            },
            "validation_timestamp": time.time(),
        }

        # Log validation results
        if validation_result["validation_passed"]:
            logger.info("✅ Perplexity performance validation PASSED")
        else:
            logger.warning("❌ Perplexity performance validation FAILED")
            if not meets_response_time_req:
                logger.warning(f"Response time requirement failed: {summary['compliance_rate']} < 0.95")
            if not meets_failure_rate_req:
                logger.warning(f"Failure rate requirement failed: {summary['failure_rate']}% > {max_failure_rate * 100}%")

        return validation_result

    def generate_performance_report(self, benchmark_results: list[PerplexityBenchmarkResult]) -> dict[str, Any]:
        """
        Generate a comprehensive performance report from multiple benchmark results.

        Args:
            benchmark_results: List of benchmark results to analyze

        Returns:
            Comprehensive performance report

        """
        if not benchmark_results:
            return {"error": "No benchmark results provided"}

        # Aggregate all response times
        all_response_times = []
        total_requests = 0
        total_successes = 0
        total_failures = 0
        all_errors = []

        for result in benchmark_results:
            all_response_times.extend(result.response_times)
            total_requests += result.total_requests
            total_successes += result.success_count
            total_failures += result.failure_count
            all_errors.extend(result.errors)

        if not all_response_times:
            return {"error": "No response times recorded in benchmark results"}

        # Calculate aggregate statistics
        overall_summary = PerplexityPerformanceMonitor.get_performance_summary(all_response_times)

        # Add aggregate metrics
        overall_summary.update(
            {
                "total_benchmark_runs": len(benchmark_results),
                "aggregate_success_rate": round((total_successes / total_requests) * 100, 2) if total_requests > 0 else 0,
                "aggregate_failure_rate": round((total_failures / total_requests) * 100, 2) if total_requests > 0 else 0,
                "unique_error_types": list(set(all_errors)) if all_errors else [],
                "report_generated_at": time.time(),
            }
        )

        # Individual benchmark summaries
        individual_summaries = [result.get_performance_summary() for result in benchmark_results]

        return {
            "overall_performance": overall_summary,
            "individual_benchmarks": individual_summaries,
            "recommendations": self._generate_performance_recommendations(overall_summary),
        }

    def _generate_performance_recommendations(self, summary: dict[str, Any]) -> list[str]:
        """Generate performance improvement recommendations based on results."""
        recommendations = []

        # Response time recommendations
        if summary.get("compliance_rate", 0) < 0.95:
            recommendations.append(f"Response time compliance is {summary.get('compliance_rate', 0):.1%}. Consider optimizing query complexity or implementing request caching.")

        if summary.get("avg_performance_ratio", 0) > 1.5:
            recommendations.append(
                f"Average response time is {summary.get('avg_performance_ratio', 0):.1f}x baseline. Consider reducing query complexity or implementing parallel processing."
            )

        # Failure rate recommendations
        failure_rate = summary.get("aggregate_failure_rate", 0)
        if failure_rate > 5:
            recommendations.append(f"Failure rate is {failure_rate:.1f}%, exceeding 5% threshold. Review error handling and implement more robust retry mechanisms.")

        # Performance variability recommendations
        p99_time = summary.get("p99_response_time_ms", 0)
        avg_time = summary.get("avg_response_time_ms", 0)
        if p99_time > avg_time * 3:
            recommendations.append("High response time variability detected. Consider implementing request timeout optimization and load balancing.")

        if not recommendations:
            recommendations.append("Performance meets all requirements. Continue monitoring for consistency.")

        return recommendations
