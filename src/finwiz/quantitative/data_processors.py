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
        return hashlib.md5(key_data.encode()).hexdigest()

    def validate_inputs(self, symbol: str, start_date: datetime, end_date: datetime, interval: str) -> None:
        """Validate input parameters."""
        if not symbol or not symbol.strip():
            raise ValueError("Symbol cannot be empty")

        if start_date >= end_date:
            raise ValueError("Start date must be before end date")

        if end_date > datetime.now():
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
                return json.load(f)
        except Exception as e:
            self.logger.warning(f"Error loading cache metadata: {e}")
            return {}

    def save_cache_metadata(self, cache_metadata: dict[str, Any], cache_metadata_file: Path) -> None:
        """Save cache metadata to disk."""
        try:
            with open(cache_metadata_file, "w") as f:
                json.dump(cache_metadata, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving cache metadata: {e}")

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
