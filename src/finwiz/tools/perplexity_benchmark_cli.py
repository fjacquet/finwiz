#!/usr/bin/env python3
"""
Perplexity Performance Benchmark CLI.

Command-line tool for benchmarking Perplexity API performance and validating
that it meets the ≤2× baseline response time and <5% failure rate requirements.
"""

import argparse
import asyncio
import json
import os
import sys
from typing import Any

from finwiz.tools.logger import get_logger
from finwiz.tools.perplexity_analysis_integration import PerplexityAnalysisIntegration
from finwiz.tools.perplexity_performance_benchmark import PerplexityPerformanceBenchmark

logger = get_logger(__name__)


async def run_performance_benchmark(
    test_cases: list[dict[str, Any]], iterations: int = 5, concurrent_requests: int = 1
) -> dict[str, Any]:
    """Run performance benchmark with specified parameters."""
    # Check API key availability
    api_key = os.getenv("PPLX_API_KEY")
    if not api_key:
        logger.error("PPLX_API_KEY environment variable not found")
        return {"error": "Missing PPLX_API_KEY environment variable"}

    # Initialize benchmark
    integration = PerplexityAnalysisIntegration()
    benchmark = PerplexityPerformanceBenchmark(integration)

    logger.info(f"Starting Perplexity performance benchmark with {len(test_cases)} test cases")
    logger.info(f"Parameters: {iterations} iterations, {concurrent_requests} concurrent requests")

    try:
        # Run benchmark
        result = await benchmark.benchmark_response_times(
            test_cases=test_cases, iterations=iterations, concurrent_requests=concurrent_requests
        )

        # Generate summary
        summary = result.get_performance_summary()

        # Log results
        logger.info("Benchmark completed successfully")
        logger.info(f"Total requests: {summary['total_requests']}")
        logger.info(f"Success rate: {summary['success_rate']:.1f}%")
        logger.info(f"Average response time: {summary['avg_response_time_ms']:.1f}ms")
        logger.info(f"Compliance rate: {summary['compliance_rate']:.1%}")

        return {
            "success": True,
            "benchmark_result": summary,
            "meets_requirements": summary.get("meets_2x_baseline_requirement", False),
        }

    except Exception as e:
        logger.error(f"Benchmark failed: {str(e)}")
        return {"error": str(e)}


async def validate_performance_requirements(sample_size: int = 20) -> dict[str, Any]:
    """Validate that Perplexity integration meets performance requirements."""
    # Check API key availability
    api_key = os.getenv("PPLX_API_KEY")
    if not api_key:
        logger.error("PPLX_API_KEY environment variable not found")
        return {"error": "Missing PPLX_API_KEY environment variable"}

    # Initialize benchmark
    integration = PerplexityAnalysisIntegration()
    benchmark = PerplexityPerformanceBenchmark(integration)

    logger.info(f"Validating Perplexity performance requirements with {sample_size} requests")

    try:
        # Run validation
        validation_result = await benchmark.validate_performance_requirements(
            sample_size=sample_size,
            max_failure_rate=0.05,  # 5% threshold
        )

        # Log results
        if validation_result["validation_passed"]:
            logger.info("✅ Performance validation PASSED")
        else:
            logger.warning("❌ Performance validation FAILED")

        logger.info(f"Response time requirement: {'✅ PASS' if validation_result['response_time_requirement_met'] else '❌ FAIL'}")
        logger.info(f"Failure rate requirement: {'✅ PASS' if validation_result['failure_rate_requirement_met'] else '❌ FAIL'}")

        return validation_result

    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        return {"error": str(e)}


def create_default_test_cases() -> list[dict[str, Any]]:
    """Create default test cases for benchmarking."""
    return [
        {"ticker": "AAPL", "query": "Apple financial news earnings", "asset_type": "stock", "analysis_type": "sentiment"},
        {"ticker": "SPY", "query": "SPY ETF performance analysis", "asset_type": "etf", "analysis_type": "technical"},
        {
            "ticker": "BTC-USD",
            "query": "Bitcoin market analysis regulatory",
            "asset_type": "crypto",
            "analysis_type": "fundamental",
        },
    ]


async def main() -> None:
    """Run CLI entry point."""
    parser = argparse.ArgumentParser(description="Benchmark Perplexity API performance and validate requirements")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Benchmark command
    benchmark_parser = subparsers.add_parser("benchmark", help="Run performance benchmark")
    benchmark_parser.add_argument("--iterations", "-i", type=int, default=3, help="Number of iterations per test case (default: 3)")
    benchmark_parser.add_argument("--concurrent", "-c", type=int, default=1, help="Number of concurrent requests (default: 1)")
    benchmark_parser.add_argument("--output", "-o", type=str, help="Output file for results (JSON format)")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate performance requirements")
    validate_parser.add_argument(
        "--sample-size", "-s", type=int, default=15, help="Number of requests for validation (default: 15)"
    )
    validate_parser.add_argument("--output", "-o", type=str, help="Output file for results (JSON format)")

    # Quick test command
    quick_parser = subparsers.add_parser("quick", help="Quick performance test")
    quick_parser.add_argument("--ticker", "-t", type=str, default="AAPL", help="Ticker symbol to test (default: AAPL)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Set up logging
    import logging

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    try:
        if args.command == "benchmark":
            test_cases = create_default_test_cases()
            result = await run_performance_benchmark(
                test_cases=test_cases, iterations=args.iterations, concurrent_requests=args.concurrent
            )

            if args.output:
                with open(args.output, "w") as f:
                    json.dump(result, f, indent=2)
                logger.info(f"Results saved to {args.output}")
            else:
                print(json.dumps(result, indent=2))

        elif args.command == "validate":
            result = await validate_performance_requirements(sample_size=args.sample_size)

            if args.output:
                with open(args.output, "w") as f:
                    json.dump(result, f, indent=2)
                logger.info(f"Results saved to {args.output}")
            else:
                print(json.dumps(result, indent=2))

        elif args.command == "quick":
            # Quick single test
            integration = PerplexityAnalysisIntegration()

            if not integration.is_available:
                logger.error("Perplexity integration not available (check PPLX_API_KEY)")
                sys.exit(1)

            logger.info(f"Running quick test for {args.ticker}")

            start_time = asyncio.get_event_loop().time()
            result = await integration.search_financial_news(
                query=f"{args.ticker} financial news",
                ticker=args.ticker,
                asset_type="stock",
                analysis_type="sentiment",
                max_results=5,
            )
            end_time = asyncio.get_event_loop().time()

            response_time_ms = int((end_time - start_time) * 1000)

            print(f"Quick test results for {args.ticker}:")
            print(f"  Success: {result.success}")
            print(f"  Response time: {response_time_ms}ms")
            print(f"  Results count: {len(result.results)}")
            print(f"  Meets 2x baseline: {response_time_ms <= 2000}")

            if result.success and result.results:
                print(f"  Sample result: {result.results[0].title[:100]}...")

    except KeyboardInterrupt:
        logger.info("Benchmark interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Benchmark failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
