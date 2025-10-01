"""
Historical data loading system for FinWiz quantitative analysis.

This module provides comprehensive data loading capabilities including:
- Multi-provider data fetching with fallback support
- Intelligent caching with configurable retention policies
- Data quality validation integration
- Provider-specific data fetching implementations
"""

import pickle
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf
from pydantic import BaseModel, Field

from finwiz.quantitative.config import DataProvider, QuantConfig, get_quant_config
from finwiz.quantitative.data_processors import DataProcessor
from finwiz.quantitative.data_validators import DataQualityReport, DataQualityValidator
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class CachedDataInfo(BaseModel):
    """Information about cached data."""

    symbol: str = Field(..., description="Stock symbol")
    start_date: datetime = Field(..., description="Start date of cached data")
    end_date: datetime = Field(..., description="End date of cached data")
    cache_timestamp: datetime = Field(..., description="When data was cached")
    data_provider: DataProvider = Field(..., description="Data provider used")
    file_path: Path = Field(..., description="Path to cached data file")
    file_size_bytes: int = Field(..., description="Size of cached file in bytes")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Quality score of cached data")

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat(), Path: lambda v: str(v)}


class HistoricalDataManager:
    """
    Manages historical OHLCV data downloading, caching, and quality validation.

    Features:
    - Multi-provider support with fallback mechanisms
    - Intelligent caching with configurable TTL
    - Comprehensive data quality validation
    - Automatic data cleaning and preprocessing
    - Performance optimization for large datasets
    """

    def __init__(self, config: QuantConfig | None = None) -> None:
        """
        Initialize historical data manager.

        Args:
            config: Quantitative analysis configuration

        """
        self.config = config or get_quant_config()
        self.cache_dir = self.config.cache_config.cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.data_validator = DataQualityValidator(self.config)
        self.data_processor = DataProcessor(self.config)
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

        # Initialize cache metadata
        self.cache_metadata_file = self.cache_dir / "cache_metadata.json"
        self.cache_metadata = self.data_processor.load_cache_metadata(self.cache_metadata_file)

    def fetch_historical_data(
        self, symbol: str, start_date: datetime, end_date: datetime, interval: str = "1d", force_refresh: bool = False
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data with caching and quality validation.

        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'MSFT')
            start_date: Start date for data
            end_date: End date for data
            interval: Data interval ('1d', '1h', '5m', etc.)
            force_refresh: Force refresh from data source, ignore cache

        Returns:
            DataFrame with OHLCV data

        Raises:
            ValueError: If symbol is invalid or date range is invalid
            RuntimeError: If data cannot be fetched from any provider

        """
        self.logger.info(f"Fetching historical data for {symbol} from {start_date} to {end_date}")

        # Validate inputs
        self.data_processor.validate_inputs(symbol, start_date, end_date, interval)

        # Check cache first (unless force refresh)
        if not force_refresh:
            cached_data = self._get_cached_data(symbol, start_date, end_date, interval)
            if cached_data is not None:
                self.logger.info(f"Using cached data for {symbol}")
                return cached_data

        # Fetch from data providers
        data = self._fetch_from_providers(symbol, start_date, end_date, interval)

        # Clean the data
        data = self.data_processor.clean_data(data, symbol)

        # Validate data quality
        quality_report = self.data_validator.validate_data_quality(data, symbol, start_date, end_date)

        if not quality_report.is_valid:
            self.logger.warning(f"Data quality issues detected for {symbol}: {len(quality_report.issues)} issues")
            if self.config.strict_validation:
                critical_issues = [issue for issue in quality_report.issues if issue.severity == "critical"]
                if critical_issues:
                    raise RuntimeError(
                        f"Critical data quality issues for {symbol}: {[issue.description for issue in critical_issues]}"
                    )

        # Cache the data
        self._cache_data(symbol, start_date, end_date, interval, data, quality_report.quality_score)

        self.logger.info(
            f"Successfully fetched {len(data)} rows of data for {symbol} (quality score: {quality_report.quality_score:.2f})"
        )
        return data

    def get_data_quality_report(
        self, symbol: str, start_date: datetime, end_date: datetime, interval: str = "1d"
    ) -> DataQualityReport:
        """
        Get data quality report for specified symbol and date range.

        Args:
            symbol: Stock symbol
            start_date: Start date for analysis
            end_date: End date for analysis
            interval: Data interval

        Returns:
            Comprehensive data quality report

        """
        data = self.fetch_historical_data(symbol, start_date, end_date, interval)
        return self.data_validator.validate_data_quality(data, symbol, start_date, end_date)

    def clear_cache(self, symbol: str | None = None, older_than_days: int | None = None) -> int:
        """
        Clear cached data based on criteria.

        Args:
            symbol: Clear cache for specific symbol (None = all symbols)
            older_than_days: Clear cache older than specified days (None = all ages)

        Returns:
            Number of cache entries cleared

        """
        cleared_count = 0
        cutoff_date = datetime.now() - timedelta(days=older_than_days) if older_than_days else None

        for cache_key, cache_info in list(self.cache_metadata.items()):
            should_clear = True

            if symbol and cache_info.get("symbol") != symbol:
                should_clear = False

            if cutoff_date and datetime.fromisoformat(cache_info.get("cache_timestamp", "1970-01-01")) > cutoff_date:
                should_clear = False

            if should_clear:
                cache_file = self.cache_dir / f"{cache_key}.pkl"
                if cache_file.exists():
                    cache_file.unlink()
                    cleared_count += 1

                del self.cache_metadata[cache_key]

        self.data_processor.save_cache_metadata(self.cache_metadata, self.cache_metadata_file)
        self.logger.info(f"Cleared {cleared_count} cache entries")
        return cleared_count

    def get_cache_info(self) -> list[CachedDataInfo]:
        """
        Get information about all cached data.

        Returns:
            List of cached data information

        """
        cache_info_list = []

        for cache_key, metadata in self.cache_metadata.items():
            try:
                cache_info = CachedDataInfo(
                    symbol=metadata["symbol"],
                    start_date=datetime.fromisoformat(metadata["start_date"]),
                    end_date=datetime.fromisoformat(metadata["end_date"]),
                    cache_timestamp=datetime.fromisoformat(metadata["cache_timestamp"]),
                    data_provider=DataProvider(metadata["data_provider"]),
                    file_path=self.cache_dir / f"{cache_key}.pkl",
                    file_size_bytes=metadata.get("file_size_bytes", 0),
                    quality_score=metadata.get("quality_score", 0.0),
                )
                cache_info_list.append(cache_info)
            except (KeyError, ValueError) as e:
                self.logger.warning(f"Invalid cache metadata for {cache_key}: {e}")

        return cache_info_list

    def _get_cached_data(self, symbol: str, start_date: datetime, end_date: datetime, interval: str) -> pd.DataFrame | None:
        """Retrieve data from cache if available and valid."""
        cache_key = self.data_processor.generate_cache_key(symbol, start_date, end_date, interval)

        if cache_key not in self.cache_metadata:
            return None

        cache_info = self.cache_metadata[cache_key]
        cache_timestamp = datetime.fromisoformat(cache_info["cache_timestamp"])

        # Check if cache is still valid based on TTL
        ttl_minutes = self.config.cache_config.price_data_ttl_minutes
        if datetime.now() - cache_timestamp > timedelta(minutes=ttl_minutes):
            self.logger.debug(f"Cache expired for {symbol}")
            return None

        # Load cached data
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        if not cache_file.exists():
            self.logger.warning(f"Cache file missing for {cache_key}")
            del self.cache_metadata[cache_key]
            return None

        try:
            with open(cache_file, "rb") as f:
                data = pickle.load(f)

            self.logger.debug(f"Loaded cached data for {symbol}: {len(data)} rows")
            return data

        except Exception as e:
            self.logger.error(f"Error loading cached data for {cache_key}: {e}")
            # Remove corrupted cache
            cache_file.unlink(missing_ok=True)
            if cache_key in self.cache_metadata:
                del self.cache_metadata[cache_key]
            return None

    def _fetch_from_providers(self, symbol: str, start_date: datetime, end_date: datetime, interval: str) -> pd.DataFrame:
        """Fetch data from available providers with fallback support."""
        providers_to_try = [self.config.primary_data_provider] + self.config.fallback_data_providers

        for provider in providers_to_try:
            if not self.config.is_provider_available(provider):
                continue

            try:
                self.logger.debug(f"Trying to fetch data from {provider} for {symbol}")
                data = self._fetch_from_provider(provider, symbol, start_date, end_date, interval)

                if not data.empty:
                    self.logger.info(f"Successfully fetched data from {provider} for {symbol}")
                    return data

            except Exception as e:
                self.logger.warning(f"Failed to fetch data from {provider} for {symbol}: {e}")
                continue

        raise RuntimeError(f"Failed to fetch data for {symbol} from all available providers")

    def _fetch_from_provider(
        self, provider: DataProvider, symbol: str, start_date: datetime, end_date: datetime, interval: str
    ) -> pd.DataFrame:
        """Fetch data from specific provider."""
        if provider == DataProvider.YFINANCE:
            return self._fetch_from_yfinance(symbol, start_date, end_date, interval)
        else:
            raise NotImplementedError(f"Provider {provider} not yet implemented")

    def _fetch_from_yfinance(self, symbol: str, start_date: datetime, end_date: datetime, interval: str) -> pd.DataFrame:
        """Fetch data from yfinance."""
        ticker = yf.Ticker(symbol)

        # Download historical data
        data = ticker.history(
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d"),
            interval=interval,
            auto_adjust=True,
            prepost=False,
            threads=True,
        )

        if data.empty:
            raise RuntimeError(f"No data returned from yfinance for {symbol}")

        # Ensure we have the required columns
        required_columns = ["Open", "High", "Low", "Close", "Volume"]
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            raise RuntimeError(f"Missing required columns from yfinance: {missing_columns}")

        return data

    def _cache_data(
        self, symbol: str, start_date: datetime, end_date: datetime, interval: str, data: pd.DataFrame, quality_score: float
    ) -> None:
        """Cache data to disk with metadata."""
        cache_key = self.data_processor.generate_cache_key(symbol, start_date, end_date, interval)
        cache_file = self.cache_dir / f"{cache_key}.pkl"

        try:
            # Save data to pickle file
            with open(cache_file, "wb") as f:
                pickle.dump(data, f)

            # Update metadata
            metadata_entry = self.data_processor.create_cache_metadata_entry(
                symbol, start_date, end_date, interval, data, quality_score, cache_file
            )
            self.cache_metadata[cache_key] = metadata_entry

            self.data_processor.save_cache_metadata(self.cache_metadata, self.cache_metadata_file)
            self.logger.debug(f"Cached data for {symbol} at {cache_file}")

        except Exception as e:
            self.logger.error(f"Error caching data for {symbol}: {e}")
            cache_file.unlink(missing_ok=True)

    def _validate_inputs(self, symbol: str, start_date: datetime, end_date: datetime, interval: str) -> None:
        """Validate input parameters (wrapper for backward compatibility)."""
        return self.data_processor.validate_inputs(symbol, start_date, end_date, interval)

    def _generate_cache_key(self, symbol: str, start_date: datetime, end_date: datetime, interval: str) -> str:
        """Generate unique cache key for data request (wrapper for backward compatibility)."""
        return self.data_processor.generate_cache_key(symbol, start_date, end_date, interval)


def get_historical_data_manager(config: QuantConfig | None = None) -> HistoricalDataManager:
    """
    Get a configured historical data manager instance.

    Args:
        config: Optional quantitative analysis configuration

    Returns:
        Configured HistoricalDataManager instance

    """
    return HistoricalDataManager(config)
