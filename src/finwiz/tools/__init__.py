"""
The tools sub-package for the FinWiz application.

This package is intended to house custom tools developed for use by
CrewAI agents within the FinWiz project. It may include tools for
specific data retrieval, analysis, or other specialized tasks.
"""

# Removed quantitative_analysis_tool import to avoid circular dependency
# Import directly from the module when needed

# Lazy imports to avoid circular dependencies
# Import directly from the modules when needed

from .portfolio_analysis_tool import PortfolioAnalysisTool

__all__ = ["BacktestingTool", "PortfolioAnalysisTool"]


def __getattr__(name: str) -> type:
    """Lazy import for tools to avoid circular imports."""
    if name == "BacktestingTool":
        from .backtesting_tool import BacktestingTool

        return BacktestingTool
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
