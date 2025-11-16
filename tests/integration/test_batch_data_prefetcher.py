"""
Unit tests for BatchDataPreFetcher.

Tests batch data pre-fetching functionality including:
- Yahoo Finance batch download
- Alpha Vantage rate limiting
- Cache save/load functionality
- Error handling for failed tickers
- Memory management

Requirements: 17.75, 17.76
"""

import json
from pathlib import Path

import pandas as pd
import pytest

from finwiz.utils.batch_data_prefetcher import BatchDataPreFetcher


class TestBatchDataPreFetcher:
    """Test suite for BatchDataPreFetcher class."""

    @pytest.fixture
    def session_id(self):
        """Provide test session ID."""
        return "test-session-123"

    @pytest.fixture
    def prefetcher(self, session_id, tmp_path):
        """Create BatchDataPreFetcher instance with temp directory."""
        # Create prefetcher with real cache directory in tmp_path
        prefetcher = BatchDataPreFetcher(session_id=session_id, enable_alpha_vantage=False)
        # Override cache_dir to use tmp_path
        prefetcher.cache_dir = tmp_path / "cache"
        prefetcher.cache_dir.mkdir(parents=True, exist_ok=True)
        return prefetcher

    @pytest.fixture
    def prefetcher_with_av(self, session_id, tmp_path, mocker):
        """Create BatchDataPreFetcher with Alpha Vantage enabled."""
        mocker.patch.dict("os.environ", {"ALPHA_VANTAGE_API_KEY": "test_key"})
        prefetcher = BatchDataPreFetcher(session_id=session_id, enable_alpha_vantage=True, alpha_vantage_rate_limit=5)
        # Override cache_dir to use tmp_path
        prefetcher.cache_dir = tmp_path / "cache"
        prefetcher.cache_dir.mkdir(parents=True, exist_ok=True)
        return prefetcher

    @pytest.fixture
    def sample_tickers(self):
        """Provide sample ticker list."""
        return ["AAPL", "MSFT", "GOOGL"]

    @pytest.fixture
    def mock_yf_data(self):
        """Provide mock Yahoo Finance data."""
        return {
            "AAPL": {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "sector": "Technology",
                "current_price": 150.0,
                "market_cap": 2500000000000,
                "pe_ratio": 25.5,
                "52wk_high": 180.0,
                "52wk_low": 120.0,
                "historical_data_points": 252,
                "failed": False,
            },
            "MSFT": {
                "symbol": "MSFT",
                "name": "Microsoft Corporation",
                "sector": "Technology",
                "current_price": 300.0,
                "market_cap": 2200000000000,
                "pe_ratio": 30.0,
                "52wk_high": 320.0,
                "52wk_low": 250.0,
                "historical_data_points": 252,
                "failed": False,
            },
        }

    @pytest.fixture
    def mock_av_data(self):
        """Provide mock Alpha Vantage data."""
        return {
            "AAPL": {
                "symbol": "AAPL",
                "name": "Apple Inc",
                "sector": "TECHNOLOGY",
                "market_cap": "2500000000000",
                "pe_ratio": "25.5",
                "eps": "6.00",
                "revenue_ttm": "400000000000",
                "failed": False,
            },
            "MSFT": {
                "symbol": "MSFT",
                "name": "Microsoft Corporation",
                "sector": "TECHNOLOGY",
                "market_cap": "2200000000000",
                "pe_ratio": "30.0",
                "eps": "10.00",
                "revenue_ttm": "200000000000",
                "failed": False,
            },
        }

    def test_should_initialize_with_yahoo_finance_only(self, session_id):
        """Test initialization with Yahoo Finance only (default)."""
        # Act
        prefetcher = BatchDataPreFetcher(session_id=session_id, enable_alpha_vantage=False)

        # Assert
        assert prefetcher.session_id == session_id
        assert prefetcher.enable_alpha_vantage is False
        assert prefetcher.alpha_vantage_key is None
        assert prefetcher.rate_limiter is None

    def test_should_initialize_with_alpha_vantage_enabled(self, session_id, mocker):
        """Test initialization with Alpha Vantage enabled."""
        # Arrange
        mocker.patch.dict("os.environ", {"ALPHA_VANTAGE_API_KEY": "test_key"})

        # Act
        prefetcher = BatchDataPreFetcher(session_id=session_id, enable_alpha_vantage=True, alpha_vantage_rate_limit=10)

        # Assert
        assert prefetcher.enable_alpha_vantage is True
        assert prefetcher.alpha_vantage_key == "test_key"
        assert prefetcher.alpha_vantage_rate_limit == 10
        assert prefetcher.rate_limiter is not None

    def test_should_create_cache_directory(self, session_id, tmp_path, mocker):
        """Test that cache directory is created on initialization."""
        # Arrange
        mock_mkdir = mocker.patch.object(Path, "mkdir")

        # Act
        prefetcher = BatchDataPreFetcher(session_id=session_id)

        # Assert
        mock_mkdir.assert_called_once()

    def test_should_fetch_yahoo_finance_batch_successfully(self, prefetcher, sample_tickers, mocker):
        """Test successful Yahoo Finance batch data fetch."""
        # Arrange
        mock_download = mocker.patch("yfinance.download")
        mock_tickers = mocker.patch("yfinance.Tickers")

        # Mock historical data
        mock_hist_data = pd.DataFrame({"High": [180.0, 175.0, 170.0], "Low": [120.0, 125.0, 130.0], "Volume": [1000000, 1100000, 1200000]})
        mock_download.return_value = {"AAPL": mock_hist_data, "MSFT": mock_hist_data, "GOOGL": mock_hist_data}

        # Mock ticker info
        mock_ticker_obj = mocker.Mock()
        mock_ticker_obj.info = {
            "shortName": "Apple Inc.",
            "sector": "Technology",
            "currentPrice": 150.0,
            "marketCap": 2500000000000,
            "trailingPE": 25.5,
        }
        mock_tickers.return_value.tickers = {"AAPL": mock_ticker_obj, "MSFT": mock_ticker_obj, "GOOGL": mock_ticker_obj}

        # Act
        result = prefetcher._fetch_yahoo_finance_batch(sample_tickers)

        # Assert
        assert len(result) == 3
        assert "AAPL" in result
        assert result["AAPL"]["symbol"] == "AAPL"
        assert result["AAPL"]["failed"] is False
        assert result["AAPL"]["current_price"] == 150.0
        mock_download.assert_called_once()

    def test_should_handle_yahoo_finance_partial_failures(self, prefetcher, sample_tickers, mocker):
        """Test handling of partial failures in Yahoo Finance batch fetch."""
        # Arrange
        mock_download = mocker.patch("yfinance.download")
        mock_tickers = mocker.patch("yfinance.Tickers")

        # Mock historical data - GOOGL fails
        mock_hist_data = pd.DataFrame({"High": [180.0], "Low": [120.0], "Volume": [1000000]})
        mock_download.return_value = {"AAPL": mock_hist_data, "MSFT": mock_hist_data, "GOOGL": pd.DataFrame()}

        # Mock ticker info - GOOGL raises exception
        mock_ticker_obj = mocker.Mock()
        mock_ticker_obj.info = {"shortName": "Apple Inc.", "currentPrice": 150.0}

        mock_failing_ticker = mocker.Mock()
        # Use side_effect on the property access
        type(mock_failing_ticker).info = mocker.PropertyMock(side_effect=Exception("No data available"))

        mock_tickers_obj = mocker.Mock()
        mock_tickers_obj.tickers = {"AAPL": mock_ticker_obj, "MSFT": mock_ticker_obj, "GOOGL": mock_failing_ticker}
        mock_tickers.return_value = mock_tickers_obj

        # Act
        result = prefetcher._fetch_yahoo_finance_batch(sample_tickers)

        # Assert
        assert len(result) == 3
        assert result["AAPL"]["failed"] is False
        assert result["MSFT"]["failed"] is False
        assert result["GOOGL"]["failed"] is True
        assert "error" in result["GOOGL"]

    def test_should_handle_yahoo_finance_complete_failure(self, prefetcher, sample_tickers, mocker):
        """Test handling of complete Yahoo Finance batch failure."""
        # Arrange
        mock_download = mocker.patch("yfinance.download", side_effect=Exception("Network error"))

        # Act
        result = prefetcher._fetch_yahoo_finance_batch(sample_tickers)

        # Assert
        assert len(result) == 3
        for ticker in sample_tickers:
            assert result[ticker]["failed"] is True
            assert "error" in result[ticker]

    @pytest.mark.asyncio
    async def test_should_fetch_alpha_vantage_batch_with_rate_limiting(self, prefetcher_with_av, sample_tickers, mocker):
        """Test Alpha Vantage batch fetch with rate limiting."""
        # Arrange
        mock_session = mocker.Mock()
        mock_response = mocker.Mock()
        mock_response.json = mocker.AsyncMock(
            return_value={
                "Symbol": "AAPL",
                "Name": "Apple Inc",
                "Sector": "TECHNOLOGY",
                "MarketCapitalization": "2500000000000",
                "PERatio": "25.5",
            }
        )
        mock_session.get = mocker.Mock(return_value=mocker.AsyncMock(__aenter__=mocker.AsyncMock(return_value=mock_response)))

        mocker.patch("aiohttp.ClientSession", return_value=mocker.AsyncMock(__aenter__=mocker.AsyncMock(return_value=mock_session)))

        # Mock rate limiter
        mock_rate_limiter = mocker.Mock()
        mock_rate_limiter.wait_for_availability = mocker.AsyncMock()
        prefetcher_with_av.rate_limiter = mock_rate_limiter

        # Act
        result = await prefetcher_with_av._fetch_alpha_vantage_batch(sample_tickers)

        # Assert
        assert len(result) == 3
        assert mock_rate_limiter.wait_for_availability.call_count == 3

    @pytest.mark.asyncio
    async def test_should_handle_alpha_vantage_partial_failures(self, prefetcher_with_av, sample_tickers, mocker):
        """Test handling of partial failures in Alpha Vantage batch fetch."""
        # Arrange
        call_count = 0

        async def mock_json_response():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {"Symbol": "AAPL", "Name": "Apple Inc"}
            elif call_count == 2:
                return {}  # No data for MSFT
            else:
                raise Exception("Network error")  # GOOGL fails

        mock_session = mocker.Mock()
        mock_response = mocker.Mock()
        mock_response.json = mock_json_response
        mock_session.get = mocker.Mock(return_value=mocker.AsyncMock(__aenter__=mocker.AsyncMock(return_value=mock_response)))

        mocker.patch("aiohttp.ClientSession", return_value=mocker.AsyncMock(__aenter__=mocker.AsyncMock(return_value=mock_session)))

        mock_rate_limiter = mocker.Mock()
        mock_rate_limiter.wait_for_availability = mocker.AsyncMock()
        prefetcher_with_av.rate_limiter = mock_rate_limiter

        # Act
        result = await prefetcher_with_av._fetch_alpha_vantage_batch(sample_tickers)

        # Assert
        assert result["AAPL"]["failed"] is False
        assert result["MSFT"]["failed"] is True
        assert result["GOOGL"]["failed"] is True

    @pytest.mark.asyncio
    async def test_should_handle_missing_alpha_vantage_key(self, prefetcher, sample_tickers):
        """Test handling when Alpha Vantage API key is not set."""
        # Arrange
        prefetcher.enable_alpha_vantage = True
        prefetcher.alpha_vantage_key = None

        # Act
        result = await prefetcher._fetch_alpha_vantage_batch(sample_tickers)

        # Assert
        for ticker in sample_tickers:
            assert result[ticker]["failed"] is True
            assert "API key not set" in result[ticker]["error"]

    def test_should_save_data_to_cache(self, prefetcher, mock_yf_data):
        """Test saving pre-fetched data to cache."""
        # Arrange
        # Ensure cache directory exists
        prefetcher.cache_dir.mkdir(parents=True, exist_ok=True)

        combined_data = {
            ticker: {
                "ticker": ticker,
                "yahoo_finance": data,
                "alpha_vantage": {},
                "fetch_timestamp": "2025-01-25T10:00:00",
                "failed": False,
            }
            for ticker, data in mock_yf_data.items()
        }

        # Act
        prefetcher._save_to_cache(combined_data)

        # Assert
        cache_file = prefetcher.cache_dir / "batch_data.json"
        assert cache_file.exists()

        loaded_data = json.loads(cache_file.read_text())
        assert len(loaded_data) == 2
        assert "AAPL" in loaded_data
        assert loaded_data["AAPL"]["ticker"] == "AAPL"

    def test_should_load_data_from_cache(self, prefetcher, mock_yf_data):
        """Test loading pre-fetched data from cache."""
        # Arrange
        combined_data = {
            ticker: {
                "ticker": ticker,
                "yahoo_finance": data,
                "alpha_vantage": {},
                "fetch_timestamp": "2025-01-25T10:00:00",
                "failed": False,
            }
            for ticker, data in mock_yf_data.items()
        }
        prefetcher._save_to_cache(combined_data)

        # Act
        loaded_data = prefetcher.load_from_cache()

        # Assert
        assert len(loaded_data) == 2
        assert "AAPL" in loaded_data
        assert loaded_data["AAPL"]["ticker"] == "AAPL"
        assert loaded_data["AAPL"]["yahoo_finance"]["symbol"] == "AAPL"

    def test_should_return_empty_dict_when_cache_missing(self, prefetcher):
        """Test loading from cache when cache file doesn't exist."""
        # Act
        loaded_data = prefetcher.load_from_cache()

        # Assert
        assert loaded_data == {}

    def test_should_handle_cache_load_error(self, prefetcher, mocker):
        """Test handling of cache load errors."""
        # Arrange
        cache_file = prefetcher.cache_dir / "batch_data.json"
        cache_file.write_text("invalid json content")

        # Act
        loaded_data = prefetcher.load_from_cache()

        # Assert
        assert loaded_data == {}

    def test_should_prefetch_all_data_yahoo_only(self, prefetcher, sample_tickers, mock_yf_data, mocker):
        """Test complete prefetch_all_data flow with Yahoo Finance only."""
        # Arrange
        mocker.patch.object(prefetcher, "_fetch_yahoo_finance_batch", return_value=mock_yf_data)
        mocker.patch.object(prefetcher, "_save_to_cache")

        # Act
        result = prefetcher.prefetch_all_data(sample_tickers)

        # Assert
        assert len(result) == 3  # All 3 tickers (AAPL, MSFT from mock, GOOGL as failed)
        assert "AAPL" in result
        assert result["AAPL"]["ticker"] == "AAPL"
        assert result["AAPL"]["yahoo_finance"]["symbol"] == "AAPL"
        assert "fetch_timestamp" in result["AAPL"]

    def test_should_prefetch_all_data_with_alpha_vantage(self, prefetcher_with_av, sample_tickers, mock_yf_data, mock_av_data, mocker):
        """Test complete prefetch_all_data flow with Alpha Vantage enabled."""
        # Arrange
        mocker.patch.object(prefetcher_with_av, "_fetch_yahoo_finance_batch", return_value=mock_yf_data)
        mocker.patch.object(prefetcher_with_av, "_fetch_alpha_vantage_batch", return_value=mocker.AsyncMock(return_value=mock_av_data))
        mocker.patch.object(prefetcher_with_av, "_save_to_cache")

        # Mock asyncio.run
        mocker.patch("asyncio.run", return_value=mock_av_data)

        # Act
        result = prefetcher_with_av.prefetch_all_data(sample_tickers)

        # Assert
        assert len(result) == 3  # All 3 tickers
        assert result["AAPL"]["yahoo_finance"]["symbol"] == "AAPL"
        assert result["AAPL"]["alpha_vantage"]["symbol"] == "AAPL"

    def test_should_track_failed_tickers_in_prefetch(self, prefetcher, sample_tickers, mocker):
        """Test that failed tickers are properly tracked in prefetch_all_data."""
        # Arrange
        mock_yf_data = {
            "AAPL": {"symbol": "AAPL", "failed": False},
            "MSFT": {"symbol": "MSFT", "failed": True, "error": "No data"},
            "GOOGL": {"symbol": "GOOGL", "failed": False},
        }
        mocker.patch.object(prefetcher, "_fetch_yahoo_finance_batch", return_value=mock_yf_data)
        mocker.patch.object(prefetcher, "_save_to_cache")

        # Act
        result = prefetcher.prefetch_all_data(sample_tickers)

        # Assert
        assert result["AAPL"]["failed"] is False
        assert result["MSFT"]["failed"] is True
        assert result["GOOGL"]["failed"] is False

    def test_should_get_memory_metrics(self, prefetcher, mocker):
        """Test getting memory metrics from memory manager."""
        # Arrange
        mock_metrics = {"peak_memory_mb": 100.5, "initial_memory_mb": 50.0, "final_memory_mb": 75.0}
        mocker.patch.object(prefetcher.memory_manager, "get_memory_metrics", return_value=mock_metrics)

        # Act
        metrics = prefetcher.get_memory_metrics()

        # Assert
        assert metrics == mock_metrics
        assert metrics["peak_memory_mb"] == 100.5

    def test_should_cleanup_cache(self, prefetcher, mocker):
        """Test cache cleanup functionality."""
        # Arrange
        mock_cleanup_result = {"disk_freed_mb": 25.5, "memory_freed_mb": 10.0}
        mocker.patch.object(prefetcher.memory_manager, "cleanup_cache", return_value=mock_cleanup_result)

        # Act
        result = prefetcher.cleanup_cache()

        # Assert
        assert result == mock_cleanup_result
        assert result["disk_freed_mb"] == 25.5

    def test_should_validate_memory_constraints(self, prefetcher, mocker):
        """Test memory constraints validation."""
        # Arrange
        mocker.patch.object(prefetcher.memory_manager, "validate_memory_constraints", return_value=True)

        # Act
        result = prefetcher.validate_memory_constraints()

        # Assert
        assert result is True

    def test_should_monitor_memory_during_prefetch(self, prefetcher, sample_tickers, mock_yf_data, mocker):
        """Test that memory is monitored at key points during prefetch."""
        # Arrange
        mocker.patch.object(prefetcher, "_fetch_yahoo_finance_batch", return_value=mock_yf_data)
        mocker.patch.object(prefetcher, "_save_to_cache")
        mock_monitor = mocker.patch.object(prefetcher.memory_manager, "monitor_memory")

        # Act
        prefetcher.prefetch_all_data(sample_tickers)

        # Assert
        # Should monitor at: start, yahoo-complete, cache-save-complete
        assert mock_monitor.call_count >= 3
        mock_monitor.assert_any_call("pre-fetch-start")
        mock_monitor.assert_any_call("yahoo-finance-complete")
        mock_monitor.assert_any_call("cache-save-complete")


class TestBatchDataPreFetcherEdgeCases:
    """Test edge cases and error scenarios."""

    def test_should_handle_empty_ticker_list(self, mocker):
        """Test handling of empty ticker list."""
        # Arrange
        prefetcher = BatchDataPreFetcher(session_id="test")
        mocker.patch.object(prefetcher, "_fetch_yahoo_finance_batch", return_value={})
        mocker.patch.object(prefetcher, "_save_to_cache")
        # Mock memory manager to avoid division by zero
        mocker.patch.object(prefetcher.memory_manager, "monitor_memory")

        # Act
        result = prefetcher.prefetch_all_data([])

        # Assert
        assert result == {}

    def test_should_handle_single_ticker(self, mocker):
        """Test handling of single ticker."""
        # Arrange
        prefetcher = BatchDataPreFetcher(session_id="test")
        mock_data = {"AAPL": {"symbol": "AAPL", "failed": False}}
        mocker.patch.object(prefetcher, "_fetch_yahoo_finance_batch", return_value=mock_data)
        mocker.patch.object(prefetcher, "_save_to_cache")

        # Act
        result = prefetcher.prefetch_all_data(["AAPL"])

        # Assert
        assert len(result) == 1
        assert "AAPL" in result

    def test_should_handle_large_ticker_list(self, mocker):
        """Test handling of large ticker list (66+ tickers)."""
        # Arrange
        prefetcher = BatchDataPreFetcher(session_id="test")
        tickers = [f"TICK{i}" for i in range(70)]
        mock_data = {ticker: {"symbol": ticker, "failed": False} for ticker in tickers}
        mocker.patch.object(prefetcher, "_fetch_yahoo_finance_batch", return_value=mock_data)
        mocker.patch.object(prefetcher, "_save_to_cache")

        # Act
        result = prefetcher.prefetch_all_data(tickers)

        # Assert
        assert len(result) == 70

    def test_should_handle_cache_save_failure(self, mocker, tmp_path):
        """Test handling of cache save failure."""
        # Arrange
        prefetcher = BatchDataPreFetcher(session_id="test")
        prefetcher.cache_dir = tmp_path / "cache"
        prefetcher.cache_dir.mkdir(parents=True, exist_ok=True)

        sample_tickers = ["AAPL", "MSFT"]
        mock_yf_data = {"AAPL": {"symbol": "AAPL", "failed": False}, "MSFT": {"symbol": "MSFT", "failed": False}}

        mocker.patch.object(prefetcher, "_fetch_yahoo_finance_batch", return_value=mock_yf_data)

        # Mock the file write to raise an exception
        mock_path = mocker.patch("pathlib.Path.write_text", side_effect=Exception("Disk full"))

        # Act & Assert - Should not raise exception (error is caught and logged)
        result = prefetcher.prefetch_all_data(sample_tickers)
        assert len(result) == 2  # Data still returned even if cache save fails
