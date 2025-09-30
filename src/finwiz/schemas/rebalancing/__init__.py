"""
Portfolio Rebalancing Schemas Package.

Modular schema definitions for portfolio rebalancing functionality.
"""

# Import all classes for backward compatibility
from .analysis import (
    PerformanceAttribution,
    PortfolioAnalysis,
    PortfolioMetrics,
    RebalancingAnalytics,
    RebalancingNeed,
    TrendAnalysis,
)
from .core import Holding, PortfolioConfiguration, PriceData
from .enums import RebalancingMethod, RebalancingRecommendation, TradeAction, UrgencyLevel
from .results import PositionHistory, RebalancingHistoryEntry, RebalancingResult
from .trades import AlternativeScenario, CostAnalysis, ExecutionSummary, TradeRecommendation

# Export all classes for backward compatibility
__all__ = [
    # Enums
    "TradeAction",
    "UrgencyLevel",
    "RebalancingMethod",
    "RebalancingRecommendation",
    # Core models
    "Holding",
    "PortfolioConfiguration",
    "PriceData",
    # Trade models
    "TradeRecommendation",
    "CostAnalysis",
    "AlternativeScenario",
    "ExecutionSummary",
    # Analysis models
    "PortfolioAnalysis",
    "RebalancingNeed",
    "PortfolioMetrics",
    "PerformanceAttribution",
    "TrendAnalysis",
    "RebalancingAnalytics",
    # Results models
    "RebalancingResult",
    "RebalancingHistoryEntry",
    "PositionHistory",
]
