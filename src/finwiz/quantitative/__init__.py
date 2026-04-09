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

# Import models from centralized schemas
from finwiz.schemas.quantitative import (
    BacktestResult,
    Trade,
    TradeStatus,
    TradeType,
)

from .backtesting import BacktestingEngine, get_backtesting_engine
from .backtesting_models import (
    PositionSizingMethod,  # Keep local enums that aren't in schemas
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
    get_performance_analyzer,
)
from .performance_benchmarks import (
    PerformanceReport,
    PortfolioOptimizationResult,
)
from .performance_metrics import (
    PerformanceMetrics,
)
from .rebalancing_history_tracker import RebalancingHistoryTracker
from .risk_manager import RiskManager
from .risk_metrics import (
    ConcentrationLimits,
    RiskAssessment,
    RiskLevel,
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
    "BacktestConfig",
    "BacktestResult",
    "BacktestingEngine",
    "BrokerFeeStructure",
    "BrokerType",
    "CachedDataInfo",
    "ConcentrationLimits",
    "CostAnalyzer",
    "CostBenefitAnalysis",
    "DataQualityIssue",
    "DataQualityReport",
    "DataQualityValidator",
    "HistoricalDataManager",
    "MarketCapCategory",
    "MarketImpactEstimate",
    "PerformanceAnalyzer",
    "PerformanceMetrics",
    "PerformanceReport",
    "PortfolioOptimizationResult",
    "PositionSizingMethod",
    "QuantConfig",
    "RebalancingHistoryTracker",
    "RiskAssessment",
    "RiskLevel",
    "RiskManager",
    "RiskManagerConfig",
    "RiskWarning",
    "RiskWarningType",
    "ScreenerConfig",
    "SimpleMovingAverageStrategy",
    "SpreadEstimate",
    "StrategyFramework",
    "TaxLossHarvestingConfig",
    "Trade",
    "TradeStatus",
    "TradeType",
    "TurnoverLimits",
    "VolatilityThresholds",
    "get_backtesting_engine",
    "get_historical_data_manager",
    "get_performance_analyzer",
]
