"""
Portfolio Rebalancing Enums.

Basic enumeration types for portfolio rebalancing operations.
"""

from enum import Enum


class TradeAction(str, Enum):
    """Trade action enumeration."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class UrgencyLevel(str, Enum):
    """Trade urgency level enumeration."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RebalancingMethod(str, Enum):
    """Rebalancing optimization method enumeration."""

    MINIMIZE_TRADES = "MINIMIZE_TRADES"
    MINIMIZE_COSTS = "MINIMIZE_COSTS"
    RISK_AWARE = "RISK_AWARE"
    TAX_EFFICIENT = "TAX_EFFICIENT"


class RebalancingRecommendation(str, Enum):
    """Overall rebalancing recommendation enumeration."""

    REBALANCE_NOW = "REBALANCE_NOW"
    REBALANCE_SOON = "REBALANCE_SOON"
    MONITOR = "MONITOR"
    NO_ACTION = "NO_ACTION"
