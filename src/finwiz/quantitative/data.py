"""
Historical data management system for FinWiz quantitative analysis.

This module provides comprehensive data management capabilities including:
- Historical OHLCV data downloading using yfinance
- Data quality validation and completeness checks
- Intelligent caching with configurable retention policies
- Multi-provider fallback support
- Data integrity validation and error handling
"""

# Import all classes and functions from the split modules for backward compatibility
from finwiz.quantitative.data_loaders import (
    CachedDataInfo,
    HistoricalDataManager,
    get_historical_data_manager,
)
from finwiz.quantitative.data_processors import DataProcessor
from finwiz.quantitative.data_validators import (
    DataQualityIssue,
    DataQualityReport,
    DataQualityValidator,
)

# Re-export all classes for backward compatibility
__all__ = [
    "DataQualityIssue",
    "DataQualityReport",
    "DataQualityValidator",
    "CachedDataInfo",
    "HistoricalDataManager",
    "DataProcessor",
    "get_historical_data_manager",
]
