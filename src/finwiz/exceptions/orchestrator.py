"""
Orchestrator exceptions for FinWiz.

These exceptions are raised during orchestration operations,
including portfolio rebalancing, analysis, and optimization.
"""


class PortfolioRebalancingError(Exception):
    """Base exception for portfolio rebalancing errors.

    Use this for all rebalancing-related errors including:
    - Calculation failures
    - Constraint violations
    - Reporting issues
    - Utility operation failures
    """

    pass


class InsufficientPriceDataError(PortfolioRebalancingError):
    """Raised when insufficient price data is available for rebalancing calculations."""

    def __init__(self, missing_symbols: list[str] | None = None, message: str | None = None) -> None:
        """
        Initialize with list of missing symbols.

        Args:
            missing_symbols: List of symbols with missing price data
            message: Optional custom message

        """
        self.missing_symbols = missing_symbols or []
        if message:
            super().__init__(message)
        elif missing_symbols:
            super().__init__(f"Insufficient price data for symbols: {', '.join(missing_symbols)}")
        else:
            super().__init__("Insufficient price data available")


class OptimizationFailedError(Exception):
    """Raised when portfolio optimization fails to find a valid solution."""

    pass
