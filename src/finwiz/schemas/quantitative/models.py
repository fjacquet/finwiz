"""
Quantitative analysis models for FinWiz.

This module re-exports all quantitative models from domain-specific files.
For new code, prefer importing directly from the domain modules:
- finwiz.schemas.quantitative.enums
- finwiz.schemas.quantitative.backtesting
- finwiz.schemas.quantitative.technical
- finwiz.schemas.quantitative.portfolio
- finwiz.schemas.quantitative.screening
- finwiz.schemas.quantitative.risk
- finwiz.schemas.quantitative.data
"""

# Enums
# Backtesting and Performance Models
from finwiz.schemas.quantitative.backtesting import (
    BacktestResult,
    MarketRegime,
    PerformanceMetrics,
    Trade,
)

# Data Models
from finwiz.schemas.quantitative.data import (
    CachedDataInfo,
    PriceData,
)
from finwiz.schemas.quantitative.enums import (
    MarketRegimeType,
    SignalType,
    TradeStatus,
    TradeType,
)

# Portfolio Optimization Models
from finwiz.schemas.quantitative.portfolio import (
    EfficientFrontierPoint,
    OptimizationConstraint,
    OptimizationResult,
    PortfolioInputs,
    PortfolioMetrics,
)

# Risk Management and Scenario Analysis Models
from finwiz.schemas.quantitative.risk import (
    ConcentrationLimits,
    MonteCarloResult,
    RiskAssessment,
    RiskManagerConfig,
    RiskWarning,
    ScenarioParameters,
    TurnoverLimits,
    VolatilityThresholds,
)

# Screening Models
from finwiz.schemas.quantitative.screening import (
    ScreeningFilter,
    ScreeningResult,
    ScreeningScore,
    ScreeningSummary,
    StockData,
)

# Technical Analysis Models
from finwiz.schemas.quantitative.technical import (
    ConfluenceZone,
    FibonacciLevels,
    IndicatorSignal,
    SupportResistance,
    TechnicalAnalysisResult,
    TechnicalIndicatorSummary,
    TechnicalIndicatorValue,
    TechnicalSignal,
)

__all__ = [
    # Enums
    "TradeType",
    "TradeStatus",
    "MarketRegimeType",
    "SignalType",
    # Backtesting
    "Trade",
    "MarketRegime",
    "BacktestResult",
    "PerformanceMetrics",
    # Technical
    "TechnicalSignal",
    "IndicatorSignal",
    "ConfluenceZone",
    "FibonacciLevels",
    "SupportResistance",
    "TechnicalIndicatorValue",
    "TechnicalIndicatorSummary",
    "TechnicalAnalysisResult",
    # Portfolio
    "OptimizationConstraint",
    "PortfolioInputs",
    "PortfolioMetrics",
    "OptimizationResult",
    "EfficientFrontierPoint",
    # Screening
    "ScreeningFilter",
    "StockData",
    "ScreeningScore",
    "ScreeningResult",
    "ScreeningSummary",
    # Risk
    "RiskWarning",
    "ConcentrationLimits",
    "TurnoverLimits",
    "VolatilityThresholds",
    "RiskManagerConfig",
    "RiskAssessment",
    # Scenario
    "ScenarioParameters",
    "MonteCarloResult",
    # Data
    "PriceData",
    "CachedDataInfo",
]
