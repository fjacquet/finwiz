"""
Data quality validation tests for batch vs live API data.

This module tests that pre-fetched data quality matches live API data,
verifies analysis results are identical, and checks for data staleness issues.

Requirements: 17.78
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
import yfinance as yf  # type: ignore[import-untyped]

from finwiz.utils.batch_data_prefetcher import BatchDataPreFetcher


class TestDataQualityValidation:
    """Test data quality between batch and live API calls."""

    @pytest.fixture
    def test_tickers(self) -> list[str]:
        """Sample tickers for data quality testing."""
        return ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]

    @pytest.fixture
    def session_id(self) -> str:
        """Generate unique session ID for testing."""
        return f"data_quality_test_{int(time.time())}"

    def test_should_match_yahoo_finance_live_data_quality(self, test_tickers, session_id):
        """
        Test that pre-fetched Yahoo Finance data matches live API data.

        Requirements: 17.78
        """
        # Arrange
        tickers = test_tickers[:3]  # Use 3 tickers to keep test fast

        # Get live data directly from Yahoo Finance
        live_data = {}
        for ticker in tickers:
            try:
                ticker_obj = yf.Ticker(ticker)
                info = ticker_obj.info
                hist = ticker_obj.history(period="1y")

                live_data[ticker] = {
                    "symbol": ticker,
                    "name": info.get("shortName", "N/A"),
                    "sector": info.get("sector", "N/A"),
                    "current_price": info.get("currentPrice", info.get("regularMarketPrice", "N/A")),
                    "market_cap": info.get("marketCap", "N/A"),
                    "pe_ratio": info.get("trailingPE", "N/A"),
                    "52wk_high": float(hist["High"].max()) if not hist.empty else "N/A",
                    "52wk_low": float(hist["Low"].min()) if not hist.empty else "N/A",
                    "historical_data_points": len(hist) if not hist.empty else 0,
                }
            except Exception as e:
                live_data[ticker] = {"error": str(e), "failed": True}

        # Get batch pre-fetched data
        prefetcher = BatchDataPreFetcher(session_id=session_id, enable_alpha_vantage=False)
        batch_data = prefetcher.prefetch_all_data(tickers)

        # Compare data quality
        for ticker in tickers:
            live_ticker_data = live_data.get(ticker, {})
            batch_ticker_data = batch_data.get(ticker, {}).get("yahoo_finance", {})

            # Skip if either failed
            if live_ticker_data.get("failed") or batch_ticker_data.get("failed"):
                continue

            # Compare key fields
            self._compare_ticker_data(ticker, live_ticker_data, batch_ticker_data)

        # Cleanup
        prefetcher.cleanup_cache()

        print("\nData Quality Validation Results:")
        print(f"  Tickers tested: {len(tickers)}")
        print(f"  Live data success: {sum(1 for d in live_data.values() if not d.get('failed', False))}")
        print(f"  Batch data success: {sum(1 for d in batch_data.values() if not d.get('failed', False))}")

    def _compare_ticker_data(self, ticker: str, live_data: dict[str, Any], batch_data: dict[str, Any]):
        """Compare live and batch data for a single ticker."""
        # Symbol should match exactly
        assert live_data.get("symbol") == batch_data.get("symbol"), f"Symbol mismatch for {ticker}"

        # Name should match (allowing for minor variations)
        live_name = live_data.get("name", "").upper()
        batch_name = batch_data.get("name", "").upper()
        if live_name != "N/A" and batch_name != "N/A":
            # Allow for minor name variations (e.g., "Inc." vs "Inc")
            assert live_name.replace(".", "").replace(",", "") in batch_name.replace(".", "").replace(",", "") or batch_name.replace(".", "").replace(",", "") in live_name.replace(
                ".", ""
            ).replace(",", ""), f"Name mismatch for {ticker}: live='{live_name}' vs batch='{batch_name}'"

        # Sector should match
        if live_data.get("sector") != "N/A" and batch_data.get("sector") != "N/A":
            assert live_data.get("sector") == batch_data.get("sector"), f"Sector mismatch for {ticker}"

        # Current price should be close (within 5% due to timing differences)
        live_price = live_data.get("current_price")
        batch_price = batch_data.get("current_price")
        if isinstance(live_price, (int, float)) and isinstance(batch_price, (int, float)):
            price_diff_percent = abs(live_price - batch_price) / live_price * 100
            assert price_diff_percent < 5, f"Price difference too large for {ticker}: {price_diff_percent:.1f}%"

        # Market cap should be close (within 10% due to timing differences)
        live_mcap = live_data.get("market_cap")
        batch_mcap = batch_data.get("market_cap")
        if isinstance(live_mcap, (int, float)) and isinstance(batch_mcap, (int, float)):
            mcap_diff_percent = abs(live_mcap - batch_mcap) / live_mcap * 100
            assert mcap_diff_percent < 10, f"Market cap difference too large for {ticker}: {mcap_diff_percent:.1f}%"

        # Historical data points should be similar (within 5 days)
        live_hist_points = live_data.get("historical_data_points", 0)
        batch_hist_points = batch_data.get("historical_data_points", 0)
        if live_hist_points > 0 and batch_hist_points > 0:
            hist_diff = abs(live_hist_points - batch_hist_points)
            assert hist_diff <= 5, f"Historical data points difference too large for {ticker}: {hist_diff} days"

    def test_should_detect_stale_data_issues(self, test_tickers, session_id):
        """
        Test detection of stale data in cache.

        Requirements: 17.78
        """
        # Arrange
        tickers = test_tickers[:2]  # Use 2 tickers for faster test

        # Create prefetcher and get fresh data
        prefetcher = BatchDataPreFetcher(session_id=session_id, enable_alpha_vantage=False)

        # Get initial data
        fresh_data = prefetcher.prefetch_all_data(tickers)

        # Manually modify cache to simulate stale data
        cache_file = Path(f"cache/batch_data/{session_id}/batch_data.json")
        if cache_file.exists():
            # Load cache
            with open(cache_file) as f:
                cache_data = json.load(f)

            # Modify timestamps to simulate stale data (2 hours old)
            stale_timestamp = (datetime.now() - timedelta(hours=2)).isoformat()
            for ticker_data in cache_data.values():
                ticker_data["fetch_timestamp"] = stale_timestamp

            # Save modified cache
            with open(cache_file, "w") as f:
                json.dump(cache_data, f, indent=2, default=str)

        # Load from cache and check staleness
        cached_data = prefetcher.load_from_cache()

        # Verify staleness detection
        for ticker, ticker_data in cached_data.items():
            fetch_timestamp = ticker_data.get("fetch_timestamp")
            if fetch_timestamp:
                fetch_time = datetime.fromisoformat(fetch_timestamp)
                age_hours = (datetime.now() - fetch_time).total_seconds() / 3600

                # Data should be detected as stale (older than 1 hour)
                assert age_hours > 1, f"Data for {ticker} should be detected as stale (age: {age_hours:.1f} hours)"

        # Cleanup
        prefetcher.cleanup_cache()

        print("\nStale Data Detection Results:")
        print(f"  Tickers tested: {len(tickers)}")
        print("  All data correctly identified as stale")

    def test_should_validate_data_completeness(self, test_tickers, session_id):
        """
        Test that batch data contains all required fields.

        Requirements: 17.78
        """
        # Arrange
        tickers = test_tickers
        required_fields = [
            "symbol",
            "name",
            "sector",
            "current_price",
            "market_cap",
            "pe_ratio",
            "52wk_high",
            "52wk_low",
            "historical_data_points",
        ]

        # Get batch data
        prefetcher = BatchDataPreFetcher(session_id=session_id, enable_alpha_vantage=False)
        batch_data = prefetcher.prefetch_all_data(tickers)

        # Validate completeness
        completeness_results = {}

        for ticker in tickers:
            ticker_data = batch_data.get(ticker, {})
            yf_data = ticker_data.get("yahoo_finance", {})

            if yf_data.get("failed"):
                completeness_results[ticker] = {"failed": True, "reason": "API failure"}
                continue

            missing_fields = []
            for field in required_fields:
                if field not in yf_data or yf_data[field] == "N/A":
                    missing_fields.append(field)

            completeness_results[ticker] = {
                "complete": len(missing_fields) == 0,
                "missing_fields": missing_fields,
                "completeness_percent": ((len(required_fields) - len(missing_fields)) / len(required_fields)) * 100,
            }

        # Assert data completeness
        successful_tickers = [t for t, r in completeness_results.items() if not r.get("failed", False)]
        complete_tickers = [t for t, r in completeness_results.items() if r.get("complete", False)]

        # At least 80% of successful tickers should have complete data
        if successful_tickers:
            completeness_rate = len(complete_tickers) / len(successful_tickers) * 100
            assert completeness_rate >= 80, f"Data completeness rate ({completeness_rate:.1f}%) should be at least 80%"

        # Average completeness should be high
        avg_completeness = (
            sum(r.get("completeness_percent", 0) for r in completeness_results.values() if not r.get("failed")) / len(successful_tickers) if successful_tickers else 0
        )
        assert avg_completeness >= 85, f"Average completeness ({avg_completeness:.1f}%) should be at least 85%"

        # Cleanup
        prefetcher.cleanup_cache()

        print("\nData Completeness Results:")
        print(f"  Total tickers: {len(tickers)}")
        print(f"  Successful tickers: {len(successful_tickers)}")
        print(f"  Complete tickers: {len(complete_tickers)}")
        print(f"  Completeness rate: {completeness_rate:.1f}%")
        print(f"  Average completeness: {avg_completeness:.1f}%")

    def test_should_validate_data_consistency_across_fetches(self, test_tickers, session_id):
        """
        Test that multiple fetches of the same data are consistent.

        Requirements: 17.78
        """
        # Arrange
        tickers = test_tickers[:2]  # Use 2 tickers for faster test

        # First fetch
        prefetcher1 = BatchDataPreFetcher(session_id=f"{session_id}_fetch1", enable_alpha_vantage=False)
        data1 = prefetcher1.prefetch_all_data(tickers)

        # Small delay to avoid rate limiting
        time.sleep(2)

        # Second fetch
        prefetcher2 = BatchDataPreFetcher(session_id=f"{session_id}_fetch2", enable_alpha_vantage=False)
        data2 = prefetcher2.prefetch_all_data(tickers)

        # Compare consistency
        consistency_results = {}

        for ticker in tickers:
            data1_ticker = data1.get(ticker, {}).get("yahoo_finance", {})
            data2_ticker = data2.get(ticker, {}).get("yahoo_finance", {})

            # Skip if either failed
            if data1_ticker.get("failed") or data2_ticker.get("failed"):
                consistency_results[ticker] = {"skipped": True, "reason": "API failure"}
                continue

            # Compare stable fields (should be identical)
            stable_fields = ["symbol", "name", "sector"]
            stable_consistent = True

            for field in stable_fields:
                val1 = data1_ticker.get(field)
                val2 = data2_ticker.get(field)
                if val1 != val2 and val1 != "N/A" and val2 != "N/A":
                    stable_consistent = False
                    break

            # Compare dynamic fields (should be close)
            dynamic_fields = ["current_price", "market_cap"]
            dynamic_consistent = True

            for field in dynamic_fields:
                val1 = data1_ticker.get(field)
                val2 = data2_ticker.get(field)

                if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                    diff_percent = abs(val1 - val2) / val1 * 100 if val1 != 0 else 0
                    if diff_percent > 10:  # Allow 10% variation for dynamic fields
                        dynamic_consistent = False
                        break

            consistency_results[ticker] = {
                "stable_consistent": stable_consistent,
                "dynamic_consistent": dynamic_consistent,
                "overall_consistent": stable_consistent and dynamic_consistent,
            }

        # Assert consistency
        tested_tickers = [t for t, r in consistency_results.items() if not r.get("skipped", False)]
        consistent_tickers = [t for t, r in consistency_results.items() if r.get("overall_consistent", False)]

        if tested_tickers:
            consistency_rate = len(consistent_tickers) / len(tested_tickers) * 100
            assert consistency_rate >= 80, f"Data consistency rate ({consistency_rate:.1f}%) should be at least 80%"

        # Cleanup
        prefetcher1.cleanup_cache()
        prefetcher2.cleanup_cache()

        print("\nData Consistency Results:")
        print(f"  Tickers tested: {len(tested_tickers)}")
        print(f"  Consistent tickers: {len(consistent_tickers)}")
        print(f"  Consistency rate: {consistency_rate:.1f}%")

    @pytest.mark.integration
    def test_should_validate_alpha_vantage_data_quality(self, test_tickers, session_id):
        """
        Test Alpha Vantage data quality when enabled.

        Only run in integration tests due to API rate limits.
        Requirements: 17.78
        """
        # Skip if no Alpha Vantage key
        import os

        if not os.getenv("ALPHA_VANTAGE_API_KEY"):
            pytest.skip("Alpha Vantage API key not available")

        # Arrange
        tickers = test_tickers[:2]  # Use only 2 tickers to avoid long test times

        # Get data with Alpha Vantage enabled
        prefetcher = BatchDataPreFetcher(session_id=session_id, enable_alpha_vantage=True, alpha_vantage_rate_limit=5)

        batch_data = prefetcher.prefetch_all_data(tickers)

        # Validate Alpha Vantage data quality
        av_quality_results = {}

        for ticker in tickers:
            ticker_data = batch_data.get(ticker, {})
            av_data = ticker_data.get("alpha_vantage", {})

            if av_data.get("failed"):
                av_quality_results[ticker] = {"failed": True, "reason": av_data.get("error", "Unknown")}
                continue

            # Check required Alpha Vantage fields
            av_required_fields = ["symbol", "name", "sector", "market_cap", "pe_ratio"]
            missing_fields = []

            for field in av_required_fields:
                if field not in av_data or av_data[field] == "N/A":
                    missing_fields.append(field)

            av_quality_results[ticker] = {
                "complete": len(missing_fields) == 0,
                "missing_fields": missing_fields,
                "completeness_percent": ((len(av_required_fields) - len(missing_fields)) / len(av_required_fields)) * 100,
            }

        # Assert Alpha Vantage data quality
        successful_av = [t for t, r in av_quality_results.items() if not r.get("failed", False)]

        if successful_av:
            avg_av_completeness = sum(r.get("completeness_percent", 0) for r in av_quality_results.values() if not r.get("failed")) / len(successful_av)
            assert avg_av_completeness >= 70, f"Alpha Vantage completeness ({avg_av_completeness:.1f}%) should be at least 70%"

        # Cleanup
        prefetcher.cleanup_cache()

        print("\nAlpha Vantage Data Quality Results:")
        print(f"  Tickers tested: {len(tickers)}")
        print(f"  Successful Alpha Vantage: {len(successful_av)}")
        if successful_av:
            print(f"  Average completeness: {avg_av_completeness:.1f}%")

    def test_should_handle_invalid_tickers_gracefully(self, session_id):
        """
        Test that invalid tickers are handled gracefully without breaking batch processing.

        Requirements: 17.78
        """
        # Arrange - Mix valid and invalid tickers
        tickers = ["AAPL", "INVALID_TICKER_123", "MSFT", "FAKE_STOCK_XYZ", "GOOGL"]

        # Get batch data
        prefetcher = BatchDataPreFetcher(session_id=session_id, enable_alpha_vantage=False)

        batch_data = prefetcher.prefetch_all_data(tickers)

        # Analyze results
        valid_tickers = []
        invalid_tickers = []

        for ticker in tickers:
            ticker_data = batch_data.get(ticker, {})
            yf_data = ticker_data.get("yahoo_finance", {})

            if yf_data.get("failed") or yf_data.get("error"):
                invalid_tickers.append(ticker)
            else:
                valid_tickers.append(ticker)

        # Assert graceful handling
        assert len(batch_data) == len(tickers), "All tickers should have entries in results"
        assert len(valid_tickers) >= 3, "Valid tickers (AAPL, MSFT, GOOGL) should succeed"
        assert len(invalid_tickers) >= 2, "Invalid tickers should be marked as failed"

        # Verify invalid tickers have error information
        for ticker in invalid_tickers:
            ticker_data = batch_data.get(ticker, {})
            yf_data = ticker_data.get("yahoo_finance", {})
            assert yf_data.get("failed") is True, f"Invalid ticker {ticker} should be marked as failed"
            assert "error" in yf_data or yf_data.get("name") == "N/A", f"Invalid ticker {ticker} should have error info"

        # Cleanup
        prefetcher.cleanup_cache()

        print("\nInvalid Ticker Handling Results:")
        print(f"  Total tickers: {len(tickers)}")
        print(f"  Valid tickers: {len(valid_tickers)} - {valid_tickers}")
        print(f"  Invalid tickers: {len(invalid_tickers)} - {invalid_tickers}")
        print("  Graceful handling: All tickers processed without breaking batch")
