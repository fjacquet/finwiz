"""
Portfolio rebalancing schemas for FinWiz.

This module provides Pydantic models for portfolio rebalancing functionality,
including portfolio configuration, holdings, trade recommendations, and
comprehensive validation logic.

DEPRECATED: This module has been refactored into a modular package.
Use: from finwiz.schemas.rebalancing import <ClassName>
"""

# Re-export all classes from the new modular structure for backward compatibility
from finwiz.schemas.rebalancing import (
    AlternativeScenario,
    CostAnalysis,
    ExecutionSummary,
    Holding,
    PerformanceAttribution,
    PortfolioAnalysis,
    PortfolioConfiguration,
    PortfolioMetrics,
    PositionHistory,
    PriceData,
    RebalancingAnalytics,
    RebalancingHistoryEntry,
    RebalancingMethod,
    RebalancingNeed,
    RebalancingRecommendation,
    RebalancingResult,
    TradeAction,
    TradeRecommendation,
    TrendAnalysis,
    UrgencyLevel,
)

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
