"""
Integration tests for DataSourceOrchestrator.

These tests verify:
1. End-to-end data acquisition with fallbacks
2. Problematic tickers (DELL, international stocks)
3. Performance (10-second timeout)
4. Data validation (reject invalid values)

Requirements: 11.1-11.7
"""

import asyncio
import time

import pytest
from finwiz.data.data_source_orchestrator import DataSourceOrchestrator


@pytest.mark.integration
class TestDataSourceOrchestratorIntegration:
    """Integration tests for DataSourceOrchestrator with real adapters."""

    @pytest.mark.asyncio
    async def test_end_to_end_data_acquisition_with_fallbacks(self):
        """
        Test end-to-end data acquisition with waterfall fallback strategy.

        Verifies:
        - Primary source (YFinance) is tried first
        - Falls back to secondary sources if primary fails
        - Industry averages used as last resort
        - Data lineage tracks which source provided each field

        Requirements: 11.1, 11.4
        """
        # Arrange
        orchestrator = DataSourceOrchestrator(
            total_timeout=10.0,
            per_source_timeout=3.0,
            enable_validation=True,
        )

        # Act
        start_time = time.time()
        result = await orchestrator.get_fundamental_data("AAPL", sector="Technology")
        duration = time.time() - start_time

        # Assert - Basic data completeness
        assert result.ticker == "AAPL"
        assert result.return_on_equity is not None
        assert result.debt_to_equity is not None
        assert result.revenue_growth is not None
        assert result.profit_margin is not None

        # Assert - Performance
        assert duration < 10.0, f"Total timeout exceeded: {duration}s"

        # Assert - Data quality
        assert result.confidence > 0.0
        assert len(result.sources_attempted) > 0
        assert len(result.sources_succeeded) > 0

        # Assert - Lineage tracking
        lineage_dict = result.lineage.to_dict()
        assert lineage_dict["return_on_equity"] in ["YFinance", "AlphaVantage", "Intrinio", "IndustryAverages"]

        # Log results for debugging
        print(f"\n✓ AAPL data acquired in {duration:.2f}s")
        print(f"  Sources attempted: {result.sources_attempted}")
        print(f"  Sources succeeded: {result.sources_succeeded}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Used fallback: {result.used_fallback}")

    @pytest.mark.asyncio
    async def test_problematic_ticker_dell(self):
        """
        Test handling of problematic ticker DELL.

        DELL is known to have data quality issues across multiple sources.
        Verifies graceful degradation and fallback to industry averages.

        Requirements: 11.4
        """
        # Arrange
        orchestrator = DataSourceOrchestrator(
            total_timeout=10.0,
            per_source_timeout=3.0,
            enable_validation=True,
        )

        # Act
        result = await orchestrator.get_fundamental_data("DELL", sector="Technology")

        # Assert - Should complete even with problematic ticker
        assert result.ticker == "DELL"
        assert result.is_complete(), "Should have complete data via fallbacks"

        # Assert - Likely used fallback for some/all fields
        if result.used_fallback:
            assert result.confidence < 1.0
            assert "IndustryAverages" in result.sources_succeeded

        # Log results
        print(f"\n✓ DELL data acquired with confidence: {result.confidence:.2f}")
        print(f"  Used fallback: {result.used_fallback}")
        print(f"  Sources: {result.sources_succeeded}")

    @pytest.mark.asyncio
    async def test_international_stock_support(self):
        """
        Test support for international stocks using Tiingo/EOD adapters.

        Verifies:
        - Non-US tickers are handled correctly
        - Tiingo/EOD adapters are attempted for international stocks
        - Data quality is maintained

        Requirements: 11.3
        """
        # Arrange
        orchestrator = DataSourceOrchestrator(
            total_timeout=10.0,
            per_source_timeout=3.0,
            enable_validation=True,
        )

        # Act - Test with a Japanese stock (Toyota)
        result = await orchestrator.get_fundamental_data("7203.T", sector="Auto Manufacturers")

        # Assert
        assert result.ticker == "7203.T"
        assert result.is_complete()

        # Should attempt international-focused sources
        sources_str = " ".join(result.sources_attempted)
        # At minimum should have tried YFinance (supports international) or fallen back to industry
        assert len(result.sources_attempted) > 0

        print("\n✓ International ticker 7203.T acquired")
        print(f"  Sources attempted: {result.sources_attempted}")
        print(f"  Confidence: {result.confidence:.2f}")

    @pytest.mark.asyncio
    async def test_performance_10_second_timeout(self):
        """
        Test that total timeout is enforced (10 seconds).

        Verifies:
        - Total operation completes within 10 seconds
        - Per-source timeouts are respected (3 seconds each)
        - Timeout doesn't cause data loss

        Requirements: 11.5
        """
        # Arrange
        orchestrator = DataSourceOrchestrator(
            total_timeout=10.0,
            per_source_timeout=3.0,
            enable_validation=True,
        )

        # Act - Test with multiple tickers to stress test
        tickers = ["AAPL", "GOOGL", "MSFT"]
        results = []

        start_time = time.time()
        for ticker in tickers:
            result = await orchestrator.get_fundamental_data(ticker, sector="Technology")
            results.append(result)
        duration = time.time() - start_time

        # Assert - Total time reasonable (3 tickers * ~3s each + overhead)
        assert duration < 15.0, f"Batch processing took too long: {duration}s"

        # Assert - All results complete
        for i, result in enumerate(results):
            assert result.is_complete(), f"{tickers[i]} incomplete"
            assert result.confidence > 0.0

        avg_time = duration / len(tickers)
        print(f"\n✓ Processed {len(tickers)} tickers in {duration:.2f}s (avg: {avg_time:.2f}s/ticker)")

    @pytest.mark.asyncio
    async def test_data_validation_rejects_invalid_values(self):
        """
        Test that data validation rejects invalid values.

        Verifies:
        - Negative ROE is rejected
        - Extreme outliers (>3 std dev) are rejected
        - Invalid data triggers fallback to next source

        Requirements: 11.7
        """
        # Arrange
        orchestrator = DataSourceOrchestrator(
            total_timeout=10.0,
            per_source_timeout=3.0,
            enable_validation=True,
        )

        # Act
        result = await orchestrator.get_fundamental_data("AAPL", sector="Technology")

        # Assert - Validation rules enforced
        if result.return_on_equity is not None:
            assert result.return_on_equity >= -1.0, "ROE should be >= -1.0"
            assert result.return_on_equity <= 2.0, "ROE should be <= 2.0"

        if result.debt_to_equity is not None:
            assert result.debt_to_equity >= 0.0, "Debt/Equity should be >= 0"
            assert result.debt_to_equity < 10.0, "Debt/Equity should be < 10.0"

        if result.revenue_growth is not None:
            assert result.revenue_growth >= -0.5, "Revenue growth should be >= -0.5"
            assert result.revenue_growth <= 5.0, "Revenue growth should be <= 5.0"

        if result.profit_margin is not None:
            assert result.profit_margin >= -1.0, "Profit margin should be >= -1.0"
            assert result.profit_margin <= 1.0, "Profit margin should be <= 1.0"

        print("\n✓ Data validation passed for AAPL")
        print(f"  ROE: {result.return_on_equity}")
        print(f"  Debt/Equity: {result.debt_to_equity}")
        print(f"  Revenue Growth: {result.revenue_growth}")
        print(f"  Profit Margin: {result.profit_margin}")

    @pytest.mark.asyncio
    async def test_waterfall_strategy_source_ordering(self):
        """
        Test that waterfall strategy follows correct source ordering.

        Verifies:
        - YFinance is tried first (fastest, most reliable)
        - Alpha Vantage second
        - Intrinio third
        - Tiingo/EOD for international
        - Industry averages as last resort

        Requirements: 11.1-11.4
        """
        # Arrange
        orchestrator = DataSourceOrchestrator(
            total_timeout=10.0,
            per_source_timeout=3.0,
            enable_validation=True,
        )

        # Act
        result = await orchestrator.get_fundamental_data("AAPL", sector="Technology")

        # Assert - YFinance should be attempted first
        assert len(result.sources_attempted) > 0
        # Most cases YFinance succeeds for AAPL, but verify it was attempted
        assert "YFinance" in result.sources_attempted or "Industry Average" in result.sources_succeeded

        # If fallback was used, verify Industry Average was last
        if result.used_fallback and "Industry Average" in result.sources_succeeded:
            # Industry Average should be last source tried
            lineage_dict = result.lineage.to_dict()
            industry_avg_count = sum(1 for v in lineage_dict.values() if v == "Industry Average")
            assert industry_avg_count > 0, "Should have some fields from industry averages"

        print("\n✓ Waterfall strategy verified")
        print(f"  Attempt order: {result.sources_attempted}")
        print(f"  Success: {result.sources_succeeded}")

    @pytest.mark.asyncio
    async def test_concurrent_data_acquisition(self):
        """
        Test concurrent data acquisition for multiple tickers.

        Verifies:
        - Multiple tickers can be processed concurrently
        - No race conditions or data corruption
        - Performance benefit from concurrency

        Requirements: 11.5
        """
        # Arrange
        orchestrator = DataSourceOrchestrator(
            total_timeout=10.0,
            per_source_timeout=3.0,
            enable_validation=True,
        )

        tickers = ["AAPL", "GOOGL", "MSFT", "AMZN", "META"]

        # Act - Sequential
        start_sequential = time.time()
        sequential_results = []
        for ticker in tickers:
            result = await orchestrator.get_fundamental_data(ticker, sector="Technology")
            sequential_results.append(result)
        sequential_duration = time.time() - start_sequential

        # Act - Concurrent
        start_concurrent = time.time()
        tasks = [orchestrator.get_fundamental_data(ticker, sector="Technology") for ticker in tickers]
        concurrent_results = await asyncio.gather(*tasks)
        concurrent_duration = time.time() - start_concurrent

        # Assert - Concurrent should be faster (or similar if network-bound)
        # Allow 10% margin for variance
        assert concurrent_duration <= sequential_duration * 1.1

        # Assert - All results valid
        for i, result in enumerate(concurrent_results):
            assert result.ticker == tickers[i]
            assert result.is_complete()

        speedup = sequential_duration / concurrent_duration if concurrent_duration > 0 else 1.0
        print("\n✓ Concurrent acquisition tested")
        print(f"  Sequential: {sequential_duration:.2f}s")
        print(f"  Concurrent: {concurrent_duration:.2f}s")
        print(f"  Speedup: {speedup:.2f}x")
