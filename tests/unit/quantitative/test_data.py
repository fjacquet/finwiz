"""
Unit tests for quantitative data management system.

Tests cover:
- HistoricalDataManager functionality
- DataQualityValidator validation logic
- Caching mechanisms and TTL handling
- Error handling and fallback scenarios
- Data quality reporting and scoring
"""

import pickle
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest
from faker import Faker

from finwiz.quantitative.config import DataProvider, QuantConfig
from finwiz.quantitative.data import (
    CachedDataInfo,
    DataQualityIssue,
    DataQualityReport,
    DataQualityValidator,
    HistoricalDataManager,
    get_historical_data_manager,
)

fake = Faker()


class TestDataQualityValidator:
    """Test suite for DataQualityValidator class."""

    @pytest.fixture
    def validator(self):
        """Create a DataQualityValidator instance for testing."""
        config = QuantConfig(min_data_points=20)
        return DataQualityValidator(config)

    def generate_stock_symbol(self):
        """Generate realistic stock symbol using Faker."""
        # Generate 3-5 character stock symbols like real tickers
        length = fake.random_int(min=3, max=5)
        return fake.lexify(text="?" * length, letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ")

    @pytest.fixture
    def valid_ohlcv_data(self):
        """Create valid OHLCV data for testing using Faker."""
        dates = pd.date_range(start="2023-01-01", end="2023-12-31", freq="D")
        num_dates = len(dates)

        # Use Faker to generate realistic financial data
        fake.seed_instance(42)  # For reproducible tests

        # Generate base price using Faker's financial data
        base_price = fake.pyfloat(min_value=100, max_value=200, right_digits=2)

        # Create realistic price series with controlled volatility
        prices = []
        current_price = base_price

        for _ in range(num_dates):
            # Use Faker to generate realistic daily returns (typically -1% to +1%)
            daily_return = fake.pyfloat(min_value=-0.01, max_value=0.01, right_digits=4)
            current_price = current_price * (1 + daily_return)
            prices.append(round(current_price, 2))

        # Generate OHLC data with proper relationships using Faker
        ohlc_data = []
        for close_price in prices:
            # Generate intraday volatility using Faker
            volatility = fake.pyfloat(min_value=0.005, max_value=0.015, right_digits=4)

            # High is close + some upward movement
            high = close_price * (1 + fake.pyfloat(min_value=0, max_value=volatility, right_digits=4))

            # Low is close - some downward movement
            low = close_price * (1 - fake.pyfloat(min_value=0, max_value=volatility, right_digits=4))

            # Open is somewhere between low and high
            open_price = fake.pyfloat(min_value=low, max_value=high, right_digits=2)

            # Ensure close is also between low and high
            close_price = max(low, min(high, close_price))

            ohlc_data.append(
                {
                    "Open": round(open_price, 2),
                    "High": round(high, 2),
                    "Low": round(low, 2),
                    "Close": round(close_price, 2),
                    "Volume": fake.pyint(min_value=1000000, max_value=10000000),
                }
            )

        return pd.DataFrame(ohlc_data, index=dates)

    @pytest.fixture
    def invalid_ohlcv_data(self):
        """Create invalid OHLCV data for testing."""
        dates = pd.date_range(start="2023-01-01", end="2023-01-10", freq="D")
        data = pd.DataFrame(
            {
                "Open": [100, 110, 0, 120, 130, -10, 140, 150, 160, 170],  # Contains zero and negative
                "High": [105, 115, 125, 125, 135, 145, 145, 155, 165, 175],
                "Low": [95, 105, 115, 115, 125, 135, 135, 145, 155, 165],
                "Close": [102, 112, 122, 122, 132, 142, 142, 152, 162, 172],
                "Volume": [1000000, 0, 2000000, 3000000, 4000000, 5000000, 6000000, 7000000, 8000000, 9000000],
            },
            index=dates,
        )

        # Create OHLC violations
        data.iloc[2, data.columns.get_loc("High")] = 50  # High < Low
        data.iloc[3, data.columns.get_loc("Low")] = 200  # Low > High

        return data

    def test_should_validate_valid_data_successfully(self, validator, valid_ohlcv_data):
        """Test validation of high-quality data."""
        symbol = self.generate_stock_symbol()
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)

        report = validator.validate_data_quality(valid_ohlcv_data, symbol, start_date, end_date)

        assert isinstance(report, DataQualityReport)
        assert report.symbol == symbol
        assert report.start_date == start_date
        assert report.end_date == end_date
        assert report.total_rows == len(valid_ohlcv_data)
        assert report.is_valid is True
        assert report.quality_score > 0.8
        assert report.completeness_score > 0.9
        assert report.consistency_score > 0.9
        assert report.accuracy_score > 0.9

    def test_should_detect_missing_columns(self, validator):
        """Test detection of missing required columns."""
        symbol = self.generate_stock_symbol()
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)

        # Create data missing required columns
        incomplete_data = pd.DataFrame(
            {
                "Open": [100, 110, 120],
                "High": [105, 115, 125],
                # Missing Low, Close, Volume
            }
        )

        report = validator.validate_data_quality(incomplete_data, symbol, start_date, end_date)

        assert report.is_valid is False
        missing_column_issues = [issue for issue in report.issues if issue.issue_type == "missing_columns"]
        assert len(missing_column_issues) > 0
        assert missing_column_issues[0].severity == "critical"

    def test_should_detect_empty_dataset(self, validator):
        """Test detection of empty dataset."""
        symbol = self.generate_stock_symbol()
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)

        empty_data = pd.DataFrame()

        report = validator.validate_data_quality(empty_data, symbol, start_date, end_date)

        assert report.is_valid is False
        empty_issues = [issue for issue in report.issues if issue.issue_type == "empty_dataset"]
        assert len(empty_issues) > 0
        assert empty_issues[0].severity == "critical"

    def test_should_detect_insufficient_data(self, validator):
        """Test detection of insufficient data points."""
        symbol = self.generate_stock_symbol()
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)

        # Create data with fewer rows than minimum required
        insufficient_data = pd.DataFrame(
            {"Open": [100, 110], "High": [105, 115], "Low": [95, 105], "Close": [102, 112], "Volume": [1000000, 2000000]}
        )

        report = validator.validate_data_quality(insufficient_data, symbol, start_date, end_date)

        assert report.is_valid is False
        insufficient_issues = [issue for issue in report.issues if issue.issue_type == "insufficient_data"]
        assert len(insufficient_issues) > 0
        assert insufficient_issues[0].severity == "high"

    def test_should_detect_missing_data(self, validator):
        """Test detection of missing values in data."""
        symbol = fake.pystr(min_chars=3, max_chars=5).upper()
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)

        # Create data with missing values
        data_with_nulls = pd.DataFrame(
            {
                "Open": [100, None, 120, 130, 140],
                "High": [105, 115, None, 135, 145],
                "Low": [95, 105, 115, None, 135],
                "Close": [102, 112, 122, 132, None],
                "Volume": [1000000, 2000000, 3000000, 4000000, 5000000],
            }
        )

        report = validator.validate_data_quality(data_with_nulls, symbol, start_date, end_date)

        missing_issues = [issue for issue in report.issues if issue.issue_type == "missing_data"]
        if missing_issues:  # Only check if missing data exceeds threshold
            assert missing_issues[0].severity in ["medium", "high", "critical"]

        assert report.missing_data_pct > 0

    def test_should_detect_ohlc_violations(self, validator, invalid_ohlcv_data):
        """Test detection of OHLC relationship violations."""
        symbol = fake.pystr(min_chars=3, max_chars=5).upper()
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 10)

        report = validator.validate_data_quality(invalid_ohlcv_data, symbol, start_date, end_date)

        ohlc_issues = [issue for issue in report.issues if issue.issue_type == "ohlc_violations"]
        assert len(ohlc_issues) > 0
        assert ohlc_issues[0].severity == "high"

    def test_should_detect_invalid_prices(self, validator, invalid_ohlcv_data):
        """Test detection of zero or negative prices."""
        symbol = fake.pystr(min_chars=3, max_chars=5).upper()
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 10)

        report = validator.validate_data_quality(invalid_ohlcv_data, symbol, start_date, end_date)

        invalid_price_issues = [issue for issue in report.issues if issue.issue_type == "invalid_prices"]
        assert len(invalid_price_issues) > 0
        assert invalid_price_issues[0].severity == "critical"

    def test_should_detect_extreme_price_moves(self, validator):
        """Test detection of unrealistic price movements."""
        symbol = fake.pystr(min_chars=3, max_chars=5).upper()
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 5)

        # Create data with extreme price movement
        extreme_data = pd.DataFrame(
            {
                "Open": [100, 110, 120, 130, 140],
                "High": [105, 115, 125, 135, 145],
                "Low": [95, 105, 115, 125, 135],
                "Close": [102, 300, 122, 132, 142],  # 300% jump on day 2
                "Volume": [1000000, 2000000, 3000000, 4000000, 5000000],
            }
        )

        report = validator.validate_data_quality(extreme_data, symbol, start_date, end_date)

        extreme_move_issues = [issue for issue in report.issues if issue.issue_type == "extreme_price_moves"]
        assert len(extreme_move_issues) > 0
        assert extreme_move_issues[0].severity in ["medium", "high"]

    def test_should_calculate_quality_scores_correctly(self, validator, valid_ohlcv_data):
        """Test quality score calculation logic."""
        symbol = fake.pystr(min_chars=3, max_chars=5).upper()
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)

        report = validator.validate_data_quality(valid_ohlcv_data, symbol, start_date, end_date)

        # All scores should be between 0 and 1
        assert 0.0 <= report.quality_score <= 1.0
        assert 0.0 <= report.completeness_score <= 1.0
        assert 0.0 <= report.consistency_score <= 1.0
        assert 0.0 <= report.accuracy_score <= 1.0

        # Quality score should be reasonable for good data
        assert report.quality_score > 0.7


class TestHistoricalDataManager:
    """Test suite for HistoricalDataManager class."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def config(self, temp_cache_dir):
        """Create test configuration with temporary cache directory."""
        from finwiz.quantitative.config import CacheConfig

        cache_config = CacheConfig(cache_dir=temp_cache_dir, price_data_ttl_minutes=30, enabled=True)

        return QuantConfig(cache_config=cache_config, min_data_points=20, strict_validation=False)

    @pytest.fixture
    def data_manager(self, config):
        """Create HistoricalDataManager instance for testing."""
        return HistoricalDataManager(config)

    @pytest.fixture
    def sample_yfinance_data(self):
        """Create sample yfinance data for mocking using Faker."""
        dates = pd.date_range(start="2023-01-01", end="2023-01-31", freq="D")
        num_dates = len(dates)

        # Use Faker to generate realistic financial data
        fake.seed_instance(123)  # Different seed for variety

        # Generate base price using Faker
        base_price = fake.pyfloat(min_value=140, max_value=160, right_digits=2)

        # Create realistic price series
        prices = []
        current_price = base_price

        for _ in range(num_dates):
            # Use Faker for daily returns with lower volatility for sample data
            daily_return = fake.pyfloat(min_value=-0.005, max_value=0.005, right_digits=4)
            current_price = current_price * (1 + daily_return)
            prices.append(round(current_price, 2))

        # Generate OHLC data using Faker
        ohlc_data = []
        for close_price in prices:
            # Use Faker for intraday volatility
            volatility = fake.pyfloat(min_value=0.002, max_value=0.008, right_digits=4)

            # Generate high/low using Faker
            high = close_price * (1 + fake.pyfloat(min_value=0, max_value=volatility, right_digits=4))
            low = close_price * (1 - fake.pyfloat(min_value=0, max_value=volatility, right_digits=4))

            # Generate open price using Faker
            open_price = fake.pyfloat(min_value=low, max_value=high, right_digits=2)

            # Ensure close is within range
            close_price = max(low, min(high, close_price))

            # Generate volume using Faker with realistic distribution
            volume = fake.pyint(min_value=2000000, max_value=8000000)

            ohlc_data.append(
                {
                    "Open": round(open_price, 2),
                    "High": round(high, 2),
                    "Low": round(low, 2),
                    "Close": round(close_price, 2),
                    "Volume": volume,
                }
            )

        return pd.DataFrame(ohlc_data, index=dates)

    def test_should_validate_inputs_correctly(self, data_manager):
        """Test input validation for fetch_historical_data."""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 31)

        # Test empty symbol
        with pytest.raises(ValueError, match="Symbol cannot be empty"):
            data_manager._validate_inputs("", start_date, end_date, "1d")

        # Test invalid date range
        with pytest.raises(ValueError, match="Start date must be before end date"):
            data_manager._validate_inputs("AAPL", end_date, start_date, "1d")

        # Test future end date
        future_date = datetime.now() + timedelta(days=30)
        with pytest.raises(ValueError, match="End date cannot be in the future"):
            data_manager._validate_inputs("AAPL", start_date, future_date, "1d")

        # Test invalid interval
        with pytest.raises(ValueError, match="Invalid interval"):
            data_manager._validate_inputs("AAPL", start_date, end_date, "invalid")

    def test_should_fetch_data_from_yfinance_successfully(self, data_manager, sample_yfinance_data, mocker):
        """Test successful data fetching from yfinance."""
        symbol = fake.pystr(min_chars=3, max_chars=5).upper()
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 31)

        # Mock yfinance response
        mock_ticker = mocker.patch("yfinance.Ticker")
        mock_ticker_instance = mocker.MagicMock()
        mock_ticker_instance.history.return_value = sample_yfinance_data
        mock_ticker.return_value = mock_ticker_instance

        result = data_manager.fetch_historical_data(symbol, start_date, end_date)

        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0
        assert all(col in result.columns for col in ["Open", "High", "Low", "Close", "Volume"])

        # Verify yfinance was called correctly
        mock_ticker.assert_called_once_with(symbol)
        mock_ticker_instance.history.assert_called_once()

    def test_should_cache_data_after_fetching(self, data_manager, sample_yfinance_data, mocker):
        """Test that data is cached after successful fetch."""
        symbol = fake.pystr(min_chars=3, max_chars=5).upper()
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 31)

        # Mock yfinance response
        mock_ticker = mocker.patch("yfinance.Ticker")
        mock_ticker_instance = mocker.MagicMock()
        mock_ticker_instance.history.return_value = sample_yfinance_data
        mock_ticker.return_value = mock_ticker_instance

        # First fetch should call yfinance
        data_manager.fetch_historical_data(symbol, start_date, end_date)

        # Verify cache file was created
        cache_key = data_manager._generate_cache_key(symbol, start_date, end_date, "1d")
        cache_file = data_manager.cache_dir / f"{cache_key}.pkl"
        assert cache_file.exists()

        # Verify metadata was updated
        assert cache_key in data_manager.cache_metadata
        metadata = data_manager.cache_metadata[cache_key]
        assert metadata["symbol"] == symbol
        assert metadata["row_count"] == len(sample_yfinance_data)

    def test_should_use_cached_data_when_available(self, data_manager, sample_yfinance_data, mocker):
        """Test that cached data is used when available and valid."""
        symbol = fake.pystr(min_chars=3, max_chars=5).upper()
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 31)

        # Mock yfinance response
        mock_ticker = mocker.patch("yfinance.Ticker")
        mock_ticker_instance = mocker.MagicMock()
        mock_ticker_instance.history.return_value = sample_yfinance_data
        mock_ticker.return_value = mock_ticker_instance

        # First fetch should call yfinance and cache data
        result1 = data_manager.fetch_historical_data(symbol, start_date, end_date)

        # Reset mock to verify second call doesn't hit yfinance
        mock_ticker.reset_mock()
        mock_ticker_instance.reset_mock()

        # Second fetch should use cache
        result2 = data_manager.fetch_historical_data(symbol, start_date, end_date)

        # Verify yfinance was not called again
        mock_ticker.assert_not_called()
        mock_ticker_instance.history.assert_not_called()

        # Results should be identical
        pd.testing.assert_frame_equal(result1, result2)

    def test_should_force_refresh_when_requested(self, data_manager, sample_yfinance_data, mocker):
        """Test force refresh bypasses cache."""
        symbol = fake.pystr(min_chars=3, max_chars=5).upper()
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 31)

        # Manually create cache entry
        cache_key = data_manager._generate_cache_key(symbol, start_date, end_date, "1d")
        cache_file = data_manager.cache_dir / f"{cache_key}.pkl"

        with open(cache_file, "wb") as f:
            pickle.dump(sample_yfinance_data, f)

        data_manager.cache_metadata[cache_key] = {
            "symbol": symbol,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "cache_timestamp": datetime.now().isoformat(),
            "data_provider": DataProvider.YFINANCE.value,
            "quality_score": 0.9,
        }

        mock_ticker = mocker.patch("yfinance.Ticker")
        mock_ticker_instance = mocker.MagicMock()
        mock_ticker_instance.history.return_value = sample_yfinance_data
        mock_ticker.return_value = mock_ticker_instance

        # Force refresh should call yfinance despite cache
        data_manager.fetch_historical_data(symbol, start_date, end_date, force_refresh=True)

        mock_ticker.assert_called_once_with(symbol)

    def test_should_handle_expired_cache(self, data_manager, sample_yfinance_data, mocker):
        """Test that expired cache entries are ignored."""
        symbol = fake.pystr(min_chars=3, max_chars=5).upper()
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 31)

        # Create expired cache entry
        cache_key = data_manager._generate_cache_key(symbol, start_date, end_date, "1d")
        cache_file = data_manager.cache_dir / f"{cache_key}.pkl"

        with open(cache_file, "wb") as f:
            pickle.dump(sample_yfinance_data, f)

        # Set cache timestamp to 2 hours ago (beyond TTL)
        expired_timestamp = datetime.now() - timedelta(hours=2)
        data_manager.cache_metadata[cache_key] = {
            "symbol": symbol,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "cache_timestamp": expired_timestamp.isoformat(),
            "data_provider": DataProvider.YFINANCE.value,
            "quality_score": 0.9,
        }

        mock_ticker = mocker.patch("yfinance.Ticker")
        mock_ticker_instance = mocker.MagicMock()
        mock_ticker_instance.history.return_value = sample_yfinance_data
        mock_ticker.return_value = mock_ticker_instance

        # Should fetch from yfinance due to expired cache
        data_manager.fetch_historical_data(symbol, start_date, end_date)

        mock_ticker.assert_called_once_with(symbol)

    def test_should_handle_yfinance_errors_gracefully(self, data_manager, mocker):
        """Test error handling when yfinance fails."""
        symbol = fake.pystr(min_chars=3, max_chars=5).upper()
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 31)

        # Mock yfinance to raise exception
        mock_ticker = mocker.patch("yfinance.Ticker")
        mock_ticker_instance = mocker.MagicMock()
        mock_ticker_instance.history.side_effect = Exception("Network error")
        mock_ticker.return_value = mock_ticker_instance

        with pytest.raises(RuntimeError, match="Failed to fetch data"):
            data_manager.fetch_historical_data(symbol, start_date, end_date)

    def test_should_handle_empty_yfinance_response(self, data_manager, mocker):
        """Test handling of empty response from yfinance."""
        symbol = fake.pystr(min_chars=3, max_chars=5).upper()
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 31)

        # Mock yfinance to return empty DataFrame
        mock_ticker = mocker.patch("yfinance.Ticker")
        mock_ticker_instance = mocker.MagicMock()
        mock_ticker_instance.history.return_value = pd.DataFrame()
        mock_ticker.return_value = mock_ticker_instance

        with pytest.raises(RuntimeError, match="Failed to fetch data"):
            data_manager.fetch_historical_data(symbol, start_date, end_date)

    def test_should_clear_cache_by_symbol(self, data_manager, sample_yfinance_data):
        """Test clearing cache for specific symbol."""
        symbol1 = fake.pystr(min_chars=3, max_chars=5).upper()
        symbol2 = fake.pystr(min_chars=3, max_chars=5).upper()
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 31)

        # Create cache entries for both symbols
        for symbol in [symbol1, symbol2]:
            cache_key = data_manager._generate_cache_key(symbol, start_date, end_date, "1d")
            cache_file = data_manager.cache_dir / f"{cache_key}.pkl"

            with open(cache_file, "wb") as f:
                pickle.dump(sample_yfinance_data, f)

            data_manager.cache_metadata[cache_key] = {
                "symbol": symbol,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "cache_timestamp": datetime.now().isoformat(),
                "data_provider": DataProvider.YFINANCE.value,
                "quality_score": 0.9,
            }

        # Clear cache for symbol1 only
        cleared_count = data_manager.clear_cache(symbol=symbol1)

        assert cleared_count == 1

        # Verify symbol1 cache is gone but symbol2 remains
        symbol1_key = data_manager._generate_cache_key(symbol1, start_date, end_date, "1d")
        symbol2_key = data_manager._generate_cache_key(symbol2, start_date, end_date, "1d")

        assert symbol1_key not in data_manager.cache_metadata
        assert symbol2_key in data_manager.cache_metadata

    def test_should_clear_cache_by_age(self, data_manager, sample_yfinance_data):
        """Test clearing cache older than specified days."""
        symbol = fake.pystr(min_chars=3, max_chars=5).upper()
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 31)

        # Create old cache entry
        cache_key = data_manager._generate_cache_key(symbol, start_date, end_date, "1d")
        cache_file = data_manager.cache_dir / f"{cache_key}.pkl"

        with open(cache_file, "wb") as f:
            pickle.dump(sample_yfinance_data, f)

        # Set cache timestamp to 10 days ago
        old_timestamp = datetime.now() - timedelta(days=10)
        data_manager.cache_metadata[cache_key] = {
            "symbol": symbol,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "cache_timestamp": old_timestamp.isoformat(),
            "data_provider": DataProvider.YFINANCE.value,
            "quality_score": 0.9,
        }

        # Clear cache older than 5 days
        cleared_count = data_manager.clear_cache(older_than_days=5)

        assert cleared_count == 1
        assert cache_key not in data_manager.cache_metadata

    def test_should_get_cache_info(self, data_manager, sample_yfinance_data):
        """Test getting cache information."""
        symbol = fake.pystr(min_chars=3, max_chars=5).upper()
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 31)

        # Create cache entry
        cache_key = data_manager._generate_cache_key(symbol, start_date, end_date, "1d")
        cache_file = data_manager.cache_dir / f"{cache_key}.pkl"

        with open(cache_file, "wb") as f:
            pickle.dump(sample_yfinance_data, f)

        data_manager.cache_metadata[cache_key] = {
            "symbol": symbol,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "cache_timestamp": datetime.now().isoformat(),
            "data_provider": DataProvider.YFINANCE.value,
            "file_size_bytes": cache_file.stat().st_size,
            "quality_score": 0.9,
        }

        cache_info_list = data_manager.get_cache_info()

        assert len(cache_info_list) == 1
        cache_info = cache_info_list[0]
        assert isinstance(cache_info, CachedDataInfo)
        assert cache_info.symbol == symbol
        assert cache_info.data_provider == DataProvider.YFINANCE
        assert cache_info.quality_score == 0.9

    def test_should_generate_data_quality_report(self, data_manager, sample_yfinance_data, mocker):
        """Test data quality report generation."""
        symbol = fake.pystr(min_chars=3, max_chars=5).upper()
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 31)

        # Mock yfinance response
        mock_ticker = mocker.patch("yfinance.Ticker")
        mock_ticker_instance = mocker.MagicMock()
        mock_ticker_instance.history.return_value = sample_yfinance_data
        mock_ticker.return_value = mock_ticker_instance

        report = data_manager.get_data_quality_report(symbol, start_date, end_date)

        assert isinstance(report, DataQualityReport)
        assert report.symbol == symbol
        assert report.start_date == start_date
        assert report.end_date == end_date
        assert 0.0 <= report.quality_score <= 1.0

    def test_should_generate_cache_key_consistently(self, data_manager):
        """Test cache key generation consistency."""
        symbol = fake.pystr(min_chars=3, max_chars=5).upper()
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 31)
        interval = "1d"

        key1 = data_manager._generate_cache_key(symbol, start_date, end_date, interval)
        key2 = data_manager._generate_cache_key(symbol, start_date, end_date, interval)

        assert key1 == key2
        assert len(key1) == 32  # MD5 hash length
        assert key1.isalnum()


class TestDataQualityIssue:
    """Test suite for DataQualityIssue model."""

    def test_should_create_valid_issue(self):
        """Test creation of valid DataQualityIssue."""
        issue = DataQualityIssue(
            issue_type="missing_data",
            severity="high",
            description="10% of data is missing",
            affected_columns=["Close", "Volume"],
            affected_rows=50,
            suggested_action="Fill missing values or use alternative source",
        )

        assert issue.issue_type == "missing_data"
        assert issue.severity == "high"
        assert issue.description == "10% of data is missing"
        assert issue.affected_columns == ["Close", "Volume"]
        assert issue.affected_rows == 50
        assert "alternative source" in issue.suggested_action


class TestDataQualityReport:
    """Test suite for DataQualityReport model."""

    def test_should_create_valid_report(self):
        """Test creation of valid DataQualityReport."""
        symbol = fake.pystr(min_chars=3, max_chars=5).upper()
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)

        report = DataQualityReport(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            total_rows=252,
            is_valid=True,
            quality_score=0.85,
            completeness_score=0.95,
            missing_data_pct=0.05,
            consistency_score=0.80,
            outlier_count=5,
            accuracy_score=0.90,
            suspicious_values_count=2,
        )

        assert report.symbol == symbol
        assert report.start_date == start_date
        assert report.end_date == end_date
        assert report.total_rows == 252
        assert report.is_valid is True
        assert report.quality_score == 0.85
        assert report.completeness_score == 0.95
        assert report.missing_data_pct == 0.05
        assert report.consistency_score == 0.80
        assert report.outlier_count == 5
        assert report.accuracy_score == 0.90
        assert report.suspicious_values_count == 2


class TestCachedDataInfo:
    """Test suite for CachedDataInfo model."""

    def test_should_create_valid_cached_info(self):
        """Test creation of valid CachedDataInfo."""
        symbol = fake.pystr(min_chars=3, max_chars=5).upper()
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
        cache_timestamp = datetime.now()
        file_path = Path("/tmp/cache/test.pkl")

        info = CachedDataInfo(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            cache_timestamp=cache_timestamp,
            data_provider=DataProvider.YFINANCE,
            file_path=file_path,
            file_size_bytes=1024,
            quality_score=0.9,
        )

        assert info.symbol == symbol
        assert info.start_date == start_date
        assert info.end_date == end_date
        assert info.cache_timestamp == cache_timestamp
        assert info.data_provider == DataProvider.YFINANCE
        assert info.file_path == file_path
        assert info.file_size_bytes == 1024
        assert info.quality_score == 0.9


class TestGetHistoricalDataManager:
    """Test suite for get_historical_data_manager function."""

    def test_should_return_manager_instance(self):
        """Test that function returns HistoricalDataManager instance."""
        manager = get_historical_data_manager()

        assert isinstance(manager, HistoricalDataManager)
        assert manager.config is not None
        assert manager.data_validator is not None

    def test_should_use_provided_config(self):
        """Test that function uses provided configuration."""
        custom_config = QuantConfig(min_data_points=100)
        manager = get_historical_data_manager(custom_config)

        assert isinstance(manager, HistoricalDataManager)
        assert manager.config.min_data_points == 100
