"""Data source adapters for multi-source financial data acquisition."""

from .alpha_vantage_adapter import AlphaVantageAdapter
from .base_adapter import (
    BaseDataAdapter,
    DataAcquisitionError,
    FundamentalData,
    InvalidDataError,
    TimeoutError,
)
from .eod_adapter import EODAdapter
from .industry_averages import IndustryAveragesAdapter
from .intrinio_adapter import IntrinioAdapter
from .tiingo_adapter import TiingoAdapter
from .yfinance_adapter import YFinanceAdapter

__all__ = [
    "BaseDataAdapter",
    "FundamentalData",
    "DataAcquisitionError",
    "InvalidDataError",
    "TimeoutError",
    "YFinanceAdapter",
    "AlphaVantageAdapter",
    "IntrinioAdapter",
    "TiingoAdapter",
    "EODAdapter",
    "IndustryAveragesAdapter",
]
