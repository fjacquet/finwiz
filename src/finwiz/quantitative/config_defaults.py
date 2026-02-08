"""
Default configurations and constants for quantitative analysis.

This module provides default values, enums, and dataclasses for configuration.
"""

import os
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from finwiz.config.endpoints import ALPHA_VANTAGE_BASE, TWELVE_DATA_BASE


class TechnicalIndicator(StrEnum):
    """Supported technical indicators."""

    SMA = "sma"
    EMA = "ema"
    RSI = "rsi"
    MACD = "macd"
    BOLLINGER_BANDS = "bollinger_bands"
    STOCHASTIC = "stochastic"
    ATR = "atr"
    ADX = "adx"
    CCI = "cci"
    WILLIAMS_R = "williams_r"
    FIBONACCI = "fibonacci"
    ICHIMOKU = "ichimoku"
    MOMENTUM = "momentum"
    ROC = "roc"
    TRIX = "trix"
    DMI = "dmi"
    AROON = "aroon"
    MFI = "mfi"
    PARABOLIC_SAR = "parabolic_sar"
    ULTIMATE_OSCILLATOR = "ultimate_oscillator"


class DataProvider(StrEnum):
    """Supported data providers for quantitative analysis."""

    YFINANCE = "yfinance"
    ALPHA_VANTAGE = "alpha_vantage"
    TWELVE_DATA = "twelve_data"
    QUANDL = "quandl"
    IEX_CLOUD = "iex_cloud"


class BacktestFramework(StrEnum):
    """Supported backtesting frameworks."""

    BACKTRADER = "backtrader"
    ZIPLINE = "zipline"
    VECTORBT = "vectorbt"
    CUSTOM = "custom"


class OptimizationMethod(StrEnum):
    """Portfolio optimization methods."""

    MEAN_VARIANCE = "mean_variance"
    BLACK_LITTERMAN = "black_litterman"
    RISK_PARITY = "risk_parity"
    HIERARCHICAL_RISK_PARITY = "hrp"
    CRITICAL_LINE_ALGORITHM = "cla"
    EFFICIENT_FRONTIER = "efficient_frontier"


class ScreeningCriteria(StrEnum):
    """Stock screening criteria."""

    MARKET_CAP = "market_cap"
    PE_RATIO = "pe_ratio"
    PB_RATIO = "pb_ratio"
    DIVIDEND_YIELD = "dividend_yield"
    ROE = "roe"
    ROA = "roa"
    DEBT_TO_EQUITY = "debt_to_equity"
    REVENUE_GROWTH = "revenue_growth"
    EARNINGS_GROWTH = "earnings_growth"
    PRICE_MOMENTUM = "price_momentum"
    VOLUME = "volume"
    BETA = "beta"


@dataclass
class DataProviderConfig:
    """Configuration for data providers."""

    provider: DataProvider
    api_key: str | None = None
    rate_limit_per_minute: int = 60
    timeout_seconds: int = 30
    retry_attempts: int = 3
    cache_ttl_minutes: int = 60
    base_url: str | None = None
    additional_params: dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheConfig:
    """Configuration for data caching."""

    enabled: bool = True
    cache_dir: Path = Path("cache/quantitative")
    max_cache_size_mb: int = 1000
    default_ttl_minutes: int = 60
    price_data_ttl_minutes: int = 15
    fundamental_data_ttl_hours: int = 24
    news_data_ttl_minutes: int = 30
    cleanup_interval_hours: int = 6


def get_default_provider_configs() -> dict[DataProvider, DataProviderConfig]:
    """Get default configurations for data providers."""
    return {
        DataProvider.YFINANCE: DataProviderConfig(
            provider=DataProvider.YFINANCE,
            rate_limit_per_minute=2000,  # yfinance is quite permissive
            timeout_seconds=30,
            retry_attempts=3,
            cache_ttl_minutes=15,
        ),
        DataProvider.ALPHA_VANTAGE: DataProviderConfig(
            provider=DataProvider.ALPHA_VANTAGE,
            api_key=os.getenv("ALPHA_VANTAGE_API_KEY"),
            rate_limit_per_minute=5,  # Free tier limit
            timeout_seconds=30,
            retry_attempts=2,
            cache_ttl_minutes=60,
            base_url=ALPHA_VANTAGE_BASE,
        ),
        DataProvider.TWELVE_DATA: DataProviderConfig(
            provider=DataProvider.TWELVE_DATA,
            api_key=os.getenv("TWELVE_DATA_API_KEY"),
            rate_limit_per_minute=8,  # Free tier limit
            timeout_seconds=30,
            retry_attempts=2,
            cache_ttl_minutes=30,
            base_url=TWELVE_DATA_BASE,
        ),
    }


def get_default_indicator_params() -> dict[TechnicalIndicator, dict[str, Any]]:
    """Get default parameters for technical indicators."""
    return {
        TechnicalIndicator.SMA: {"periods": [20, 50, 200]},
        TechnicalIndicator.EMA: {"periods": [12, 26, 50]},
        TechnicalIndicator.RSI: {"period": 14, "overbought": 70, "oversold": 30},
        TechnicalIndicator.MACD: {"fast": 12, "slow": 26, "signal": 9},
        TechnicalIndicator.BOLLINGER_BANDS: {"period": 20, "std_dev": 2},
    }


def get_default_screening_criteria() -> dict[ScreeningCriteria, dict[str, Any]]:
    """Get default screening criteria."""
    return {
        ScreeningCriteria.PE_RATIO: {"min": 5, "max": 25},
        ScreeningCriteria.PB_RATIO: {"min": 0.5, "max": 3.0},
        ScreeningCriteria.ROE: {"min": 0.15},
        ScreeningCriteria.DEBT_TO_EQUITY: {"max": 0.5},
        ScreeningCriteria.REVENUE_GROWTH: {"min": 0.05},
    }


def get_default_technical_filters() -> dict[str, Any]:
    """Get default technical filters."""
    return {
        "rsi_range": {"min": 30, "max": 70},
        "price_above_sma": {"period": 50},
        "volume_spike": {"threshold": 1.5},
    }
