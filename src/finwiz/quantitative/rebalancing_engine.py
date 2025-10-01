"""
Portfolio rebalancing optimization engine for FinWiz.

This module provides the main interface for portfolio rebalancing functionality,
delegating to specialized modules for optimization, trade generation, and execution.
"""

from __future__ import annotations

from finwiz.quantitative.execution_engine import RebalancingEngine
from finwiz.quantitative.optimization_algorithms import (
    MinimizeCostsStrategy,
    MinimizeTradesStrategy,
    OptimizationConstraint,
    OptimizationStrategy,
    OptimizedTrades,
    RiskAwareStrategy,
)

# Re-export main classes for backward compatibility
__all__ = [
    "RebalancingEngine",
    "OptimizationConstraint",
    "OptimizationStrategy",
    "OptimizedTrades",
    "MinimizeCostsStrategy",
    "MinimizeTradesStrategy",
    "RiskAwareStrategy",
]
