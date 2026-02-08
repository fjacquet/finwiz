"""
Portfolio Rebalancing Enums.

Basic enumeration types for portfolio rebalancing operations.
"""

from enum import StrEnum


class TradeAction(StrEnum):
    """Trade action enumeration."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class UrgencyLevel(StrEnum):
    """Trade urgency level enumeration."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RebalancingMethod(StrEnum):
    """Rebalancing optimization method enumeration."""

    MINIMIZE_TRADES = "MINIMIZE_TRADES"
    MINIMIZE_COSTS = "MINIMIZE_COSTS"
    RISK_AWARE = "RISK_AWARE"
    TAX_EFFICIENT = "TAX_EFFICIENT"


class RebalancingRecommendation(StrEnum):
    """Overall rebalancing recommendation enumeration."""

    REBALANCE_NOW = "REBALANCE_NOW"
    REBALANCE_SOON = "REBALANCE_SOON"
    MONITOR = "MONITOR"
    NO_ACTION = "NO_ACTION"
