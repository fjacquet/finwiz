"""
Quantitative analysis framework for FinWiz.

This module provides comprehensive quantitative analysis capabilities including:
- Historical data management with quality validation
- Technical analysis using TA-Lib and native implementations
- Strategy backtesting with Backtrader framework
- Performance analysis with Pyfolio integration
- Portfolio optimization with PyPortfolioOpt
- Derivatives pricing with QuantLib
- Stock screening and fundamental analysis
"""

from .backtesting import (
    BacktestingEngine,
    BacktestResult,
    PositionSizingMethod,
    SimpleMovingAverageStrategy,
    StrategyFramework,
    Trade,
    TradeStatus,
    TradeType,
    get_backtesting_engine,
)
from .config import BacktestConfig, QuantConfig, ScreenerConfig
from .data import (
    CachedDataInfo,
    DataQualityIssue,
    DataQualityReport,
    DataQualityValidator,
    HistoricalDataManager,
    get_historical_data_manager,
)
from .performance import (
    PerformanceAnalyzer,
    PerformanceMetrics,
    PerformanceReport,
    PortfolioOptimizationResult,
    get_performance_analyzer,
)

__all__ = [
    "QuantConfig",
    "BacktestConfig",
    "ScreenerConfig",
    "HistoricalDataManager",
    "DataQualityValidator",
    "DataQualityReport",
    "DataQualityIssue",
    "CachedDataInfo",
    "get_historical_data_manager",
    "BacktestingEngine",
    "StrategyFramework",
    "SimpleMovingAverageStrategy",
    "BacktestResult",
    "Trade",
    "TradeType",
    "TradeStatus",
    "PositionSizingMethod",
    "get_backtesting_engine",
    "PerformanceAnalyzer",
    "PerformanceMetrics",
    "PerformanceReport",
    "PortfolioOptimizationResult",
    "get_performance_analyzer",
]
