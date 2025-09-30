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

from .backtesting import BacktestingEngine, get_backtesting_engine
from .backtesting_models import (
    BacktestResult,
    PositionSizingMethod,
    Trade,
    TradeStatus,
    TradeType,
)
from .backtesting_strategies import (
    SimpleMovingAverageStrategy,
    StrategyFramework,
)
from .config import BacktestConfig, QuantConfig, ScreenerConfig
from .cost_analyzer import (
    BrokerFeeStructure,
    BrokerType,
    CostAnalyzer,
    CostBenefitAnalysis,
    MarketCapCategory,
    MarketImpactEstimate,
    SpreadEstimate,
)
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
from .rebalancing_history_tracker import RebalancingHistoryTracker
from .risk_manager import (
    ConcentrationLimits,
    RiskAssessment,
    RiskLevel,
    RiskManager,
    RiskManagerConfig,
    RiskWarning,
    RiskWarningType,
    TaxLossHarvestingConfig,
    TurnoverLimits,
    VolatilityThresholds,
)

# Removed portfolio_analyzer import to avoid circular dependency
# Import directly from the module when needed

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
    "CostAnalyzer",
    "BrokerType",
    "MarketCapCategory",
    "BrokerFeeStructure",
    "SpreadEstimate",
    "MarketImpactEstimate",
    "CostBenefitAnalysis",
    "RebalancingHistoryTracker",
    "RiskManager",
    "RiskManagerConfig",
    "RiskAssessment",
    "RiskWarning",
    "RiskLevel",
    "RiskWarningType",
    "ConcentrationLimits",
    "TurnoverLimits",
    "VolatilityThresholds",
    "TaxLossHarvestingConfig",
]
