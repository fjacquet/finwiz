"""
Data processing and transformation utilities for FinWiz quantitative analysis.

This module provides data processing capabilities including:
- Data cleaning and preprocessing
- Data transformation and normalization
- Cache key generation and metadata handling
- Data format conversions
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from finwiz.quantitative.config import QuantConfig
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class DataProcessor:
    """
    Handles data processing and transformation operations.

    Provides utilities for:
    - Data cleaning and preprocessing
    - Cache key generation
    - Data format conversions
    - Metadata management
    """

    def __init__(self, config: QuantConfig) -> None:
        """
        Initialize data processor.

        Args:
            config: Quantitative analysis configuration

        """
        self.config = config
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    def generate_cache_key(self, symbol: str, start_date: datetime, end_date: datetime, interval: str) -> str:
        """Generate unique cache key for data request."""
        key_data = f"{symbol}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}_{interval}"
        return hashlib.md5(key_data.encode(), usedforsecurity=False).hexdigest()

    def validate_inputs(self, symbol: str, start_date: datetime, end_date: datetime, interval: str) -> None:
        """Validate input parameters."""
        from finwiz.infrastructure.time.datetime_utils import normalize_to_naive

        if not symbol or not symbol.strip():
            raise ValueError("Symbol cannot be empty")

        # Normalize datetimes to timezone-naive for comparison
        # This handles cases where input dates might be timezone-aware
        start_naive = normalize_to_naive(start_date)
        end_naive = normalize_to_naive(end_date)
        now_naive = datetime.now()

        if start_naive >= end_naive:
            # Add debugging info to help diagnose the issue
            self.logger.error(
                f"Date validation failed for {symbol}: "
                f"start_date={start_date} (naive: {start_naive}), "
                f"end_date={end_date} (naive: {end_naive}), "
                f"start >= end: {start_naive >= end_naive}"
            )
            raise ValueError(f"Start date must be before end date (start: {start_naive}, end: {end_naive})")

        if end_naive > now_naive:
            raise ValueError("End date cannot be in the future")

        valid_intervals = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"]
        if interval not in valid_intervals:
            raise ValueError(f"Invalid interval: {interval}. Valid intervals: {valid_intervals}")

    def clean_data(self, data: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        Clean and preprocess data.

        Args:
            data: Raw OHLCV data
            symbol: Stock symbol

        Returns:
            Cleaned data

        """
        if data.empty:
            return data

        # Remove any rows with all NaN values
        data = data.dropna(how="all")

        # Forward fill missing values (common for financial data)
        data = data.ffill()

        # Remove any remaining NaN values
        data = data.dropna()

        # Ensure positive prices
        price_columns = ["Open", "High", "Low", "Close"]
        for col in price_columns:
            if col in data.columns:
                data = data[data[col] > 0]

        # Ensure volume is non-negative
        if "Volume" in data.columns:
            data = data[data["Volume"] >= 0]

        self.logger.debug(f"Cleaned data for {symbol}: {len(data)} rows remaining")
        return data

    def load_cache_metadata(self, cache_metadata_file: Path) -> dict[str, Any]:
        """Load cache metadata from disk."""
        if not cache_metadata_file.exists():
            return {}

        try:
            with open(cache_metadata_file) as f:
                result: dict[str, Any] = json.load(f)
                return result
        except Exception as e:
            self.logger.warning(f"Error loading cache metadata: {e}")
            return {}

    def save_cache_metadata(self, cache_metadata: dict[str, Any], cache_metadata_file: Path) -> None:
        """Save cache metadata to disk.

        The caller owns ``cache_metadata`` and may mutate it from another
        thread, so snapshot before serializing -- iterating the live dict
        raised "dictionary changed size during iteration" and silently
        dropped the write. ``default=str`` covers values (e.g. ``datetime``)
        that are not natively JSON-serializable.

        A cache write is a best-effort side effect, never worth aborting a
        production run over, so every failure here is swallowed. But the two
        kinds of failure are handled differently: an ``OSError`` (disk full,
        permission denied, missing directory) is a routine I/O hiccup and is
        logged at its usual one-line severity. Anything else means the
        snapshot still couldn't be serialized despite ``default=str`` -- a
        programming error, not a transient hiccup -- so it is logged with a
        full traceback (``logger.exception``) instead of disappearing into
        the same one-line message the original bug hid behind.
        """
        try:
            snapshot = dict(cache_metadata)
            with open(cache_metadata_file, "w") as f:
                json.dump(snapshot, f, indent=2, default=str)
        except OSError as e:
            self.logger.error(f"Error saving cache metadata: {e}")
        except Exception:
            self.logger.exception("Error saving cache metadata")

    def create_cache_metadata_entry(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str,
        data: pd.DataFrame,
        quality_score: float,
        cache_file: Path,
    ) -> dict[str, Any]:
        """Create cache metadata entry for a data request."""
        return {
            "symbol": symbol,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "interval": interval,
            "cache_timestamp": datetime.now().isoformat(),
            "data_provider": self.config.primary_data_provider.value,
            "file_size_bytes": cache_file.stat().st_size if cache_file.exists() else 0,
            "quality_score": quality_score,
            "row_count": len(data),
        }
