"""
The tools sub-package for the FinWiz application.

This package is intended to house custom tools developed for use by
CrewAI agents within the FinWiz project. It may include tools for
specific data retrieval, analysis, or other specialized tasks.
"""

# Removed quantitative_analysis_tool import to avoid circular dependency
# Import directly from the module when needed

from .a_plus_scoring_tool import APlusScoringTool

# BacktestingTool imported lazily to avoid circular imports
from .optimization_tool import OptimizationTool
from .portfolio_analysis_tool import PortfolioAnalysisTool
from .risk_assessment_tool import RiskAssessmentTool

__all__ = ["APlusScoringTool", "BacktestingTool", "OptimizationTool", "PortfolioAnalysisTool", "RiskAssessmentTool"]


def __getattr__(name):
    """Lazy import for BacktestingTool to avoid circular imports."""
    if name == "BacktestingTool":
        from .backtesting_tool import BacktestingTool

        return BacktestingTool
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
