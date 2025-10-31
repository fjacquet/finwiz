"""
Portfolio rebalancing utility functions.

This module contains utility functions for portfolio rebalancing operations
including price data retrieval, portfolio analysis, and rebalancing needs identification.
"""

from typing import Any

from finwiz.quantitative.portfolio_analyzer import PortfolioAnalysisError, PortfolioAnalyzer
from finwiz.schemas.portfolio_rebalancing import PortfolioConfiguration
from finwiz.tools.logger import get_logger
from finwiz.tools.portfolio_price_service import PortfolioPriceService, PriceDataUnavailableError

logger = get_logger(__name__)


class PortfolioRebalancingError(Exception):
    """Base exception for portfolio rebalancing utility errors."""

    pass


class InsufficientPriceDataError(PortfolioRebalancingError):
    """Raised when insufficient price data is available for rebalancing."""

    def __init__(self, missing_symbols: list[str]) -> None:
        """Initialize with list of missing symbols."""
        super().__init__(f"Insufficient price data for symbols: {', '.join(missing_symbols)}")
        self.missing_symbols = missing_symbols


class RebalancingUtils:
    """Utility functions for portfolio rebalancing operations."""

    def __init__(
        self,
        price_service: PortfolioPriceService | None = None,
        portfolio_analyzer: PortfolioAnalyzer | None = None,
    ) -> None:
        """
        Initialize the rebalancing utilities.

        Args:
            price_service: Price data service instance
            portfolio_analyzer: Portfolio analyzer instance

        """
        self.price_service = price_service or PortfolioPriceService()
        self.portfolio_analyzer = portfolio_analyzer or PortfolioAnalyzer()
        self.logger = logger

    async def get_portfolio_prices(self, symbols: list[str]) -> dict[str, Any]:
        """
        Get current prices for all portfolio symbols.

        Args:
            symbols: List of symbols to get prices for

        Returns:
            Dictionary of symbol to price data

        Raises:
            InsufficientPriceDataError: If price data is unavailable
            PortfolioRebalancingError: If price retrieval fails

        """
        try:
            price_data = await self.price_service.get_current_prices(symbols)

            # Check for missing price data
            missing_symbols = [symbol for symbol in symbols if symbol not in price_data]
            if missing_symbols:
                self.logger.warning(f"Missing price data for symbols: {missing_symbols}")

                # Try to get individual prices with fallback
                for symbol in missing_symbols:
                    try:
                        fallback_price = await self.price_service.get_price_with_fallback(symbol)
                        price_data[symbol] = fallback_price
                        self.logger.info(f"Retrieved fallback price for {symbol}")
                    except (PriceDataUnavailableError, Exception):
                        self.logger.error(f"Could not retrieve price for {symbol} from any source")

                # Final check for missing data
                still_missing = [symbol for symbol in symbols if symbol not in price_data]
                if still_missing:
                    raise InsufficientPriceDataError(still_missing)

            return price_data

        except Exception as e:
            if isinstance(e, InsufficientPriceDataError):
                raise
            self.logger.error(f"Error retrieving portfolio prices: {e}")
            raise PortfolioRebalancingError(f"Price retrieval failed: {e}") from e

    async def analyze_current_portfolio(self, config: PortfolioConfiguration, price_data: dict[str, Any]) -> Any:
        """
        Analyze current portfolio composition.

        Args:
            config: Portfolio configuration
            price_data: Current price data

        Returns:
            Portfolio analysis result

        Raises:
            PortfolioRebalancingError: If analysis fails

        """
        try:
            analysis = self.portfolio_analyzer.analyze_current_portfolio(holdings=config.holdings, prices=price_data, target_weights=config.target_weights)
            return analysis

        except PortfolioAnalysisError as e:
            self.logger.error(f"Portfolio analysis failed: {e}")
            raise PortfolioRebalancingError(f"Portfolio analysis failed: {e}") from e

    def identify_rebalancing_needs(self, config: PortfolioConfiguration, current_analysis: Any) -> list[Any]:
        """
        Identify positions requiring rebalancing.

        Args:
            config: Portfolio configuration
            current_analysis: Current portfolio analysis

        Returns:
            List of rebalancing needs

        Raises:
            PortfolioRebalancingError: If identification fails

        """
        try:
            rebalancing_needs = self.portfolio_analyzer.identify_rebalancing_needs(
                current_weights=current_analysis.weightings,
                target_weights=config.target_weights,
                tolerance_bands=config.tolerance_bands,
                global_tolerance=config.global_tolerance,
            )

            positions_needing_action = sum(1 for need in rebalancing_needs if need.exceeds_tolerance)
            self.logger.info(f"Identified {positions_needing_action} positions needing rebalancing")

            return rebalancing_needs

        except Exception as e:
            self.logger.error(f"Error identifying rebalancing needs: {e}")
            raise PortfolioRebalancingError(f"Failed to identify rebalancing needs: {e}") from e

    def validate_portfolio_configuration(self, config: PortfolioConfiguration) -> tuple[bool, list[str]]:
        """
        Validate portfolio configuration.

        Args:
            config: Portfolio configuration to validate

        Returns:
            Tuple of (is_valid, list_of_errors)

        """
        errors = []

        try:
            # Check if holdings exist
            if not config.holdings:
                errors.append("Portfolio must have at least one holding")

            # Check if target weights exist and sum to 1.0
            if not config.target_weights:
                errors.append("Portfolio must have target weights defined")
            else:
                total_weight = sum(config.target_weights.values())
                if abs(total_weight - 1.0) > 0.01:  # Allow 1% tolerance
                    errors.append(f"Target weights sum to {total_weight:.3f}, should be 1.0")

            # Check if all holdings have target weights
            holding_symbols = {holding.symbol for holding in config.holdings}
            target_symbols = set(config.target_weights.keys())

            missing_targets = holding_symbols - target_symbols
            if missing_targets:
                errors.append(f"Missing target weights for symbols: {', '.join(missing_targets)}")

            extra_targets = target_symbols - holding_symbols
            if extra_targets:
                errors.append(f"Target weights defined for non-held symbols: {', '.join(extra_targets)}")

            # Check tolerance settings
            if config.global_tolerance <= 0 or config.global_tolerance > 0.5:
                errors.append(f"Global tolerance {config.global_tolerance:.1%} should be between 0% and 50%")

            # Check minimum trade size
            if config.min_trade_size <= 0:
                errors.append("Minimum trade size must be positive")

            is_valid = len(errors) == 0
            return is_valid, errors

        except Exception as e:
            self.logger.error(f"Error validating portfolio configuration: {e}")
            return False, [f"Configuration validation error: {str(e)}"]

    def calculate_portfolio_summary(self, analysis: Any) -> dict[str, Any]:
        """
        Calculate portfolio summary statistics.

        Args:
            analysis: Portfolio analysis result

        Returns:
            Dictionary of summary statistics

        """
        try:
            summary = {
                "total_value": analysis.total_value,
                "position_count": len(analysis.weightings),
                "positions_needing_rebalancing": len(analysis.positions_needing_rebalancing),
                "largest_position": max(analysis.weightings.values()) if analysis.weightings else 0.0,
                "smallest_position": min(analysis.weightings.values()) if analysis.weightings else 0.0,
                "total_deviation": sum(abs(dev) for dev in analysis.deviations_from_target.values()),
                "max_deviation": (max(abs(dev) for dev in analysis.deviations_from_target.values()) if analysis.deviations_from_target else 0.0),
            }

            # Calculate concentration metrics
            if analysis.weightings:
                weights = list(analysis.weightings.values())
                summary["concentration_ratio"] = sum(w**2 for w in weights)
                summary["diversification_score"] = 1.0 - summary["concentration_ratio"]

            return summary

        except Exception as e:
            self.logger.error(f"Error calculating portfolio summary: {e}")
            return {
                "total_value": getattr(analysis, "total_value", 0.0),
                "position_count": 0,
                "positions_needing_rebalancing": 0,
                "largest_position": 0.0,
                "smallest_position": 0.0,
                "total_deviation": 0.0,
                "max_deviation": 0.0,
                "concentration_ratio": 0.0,
                "diversification_score": 0.0,
                "error": str(e),
            }

    def format_rebalancing_summary(self, needs: list[Any]) -> dict[str, Any]:
        """
        Format rebalancing needs into a summary.

        Args:
            needs: List of rebalancing needs

        Returns:
            Dictionary with rebalancing summary

        """
        try:
            summary = {
                "total_positions": len(needs),
                "positions_needing_action": sum(1 for need in needs if need.exceeds_tolerance),
                "positions_within_tolerance": sum(1 for need in needs if not need.exceeds_tolerance),
                "high_urgency_positions": sum(1 for need in needs if getattr(need, "urgency_score", 0) >= 0.7),
                "medium_urgency_positions": sum(1 for need in needs if 0.3 <= getattr(need, "urgency_score", 0) < 0.7),
                "low_urgency_positions": sum(1 for need in needs if getattr(need, "urgency_score", 0) < 0.3),
            }

            # Calculate urgency distribution
            if summary["positions_needing_action"] > 0:
                summary["urgency_distribution"] = {
                    "high": summary["high_urgency_positions"] / summary["positions_needing_action"],
                    "medium": summary["medium_urgency_positions"] / summary["positions_needing_action"],
                    "low": summary["low_urgency_positions"] / summary["positions_needing_action"],
                }
            else:
                summary["urgency_distribution"] = {"high": 0.0, "medium": 0.0, "low": 0.0}

            return summary

        except Exception as e:
            self.logger.error(f"Error formatting rebalancing summary: {e}")
            return {
                "total_positions": len(needs),
                "positions_needing_action": 0,
                "positions_within_tolerance": len(needs),
                "high_urgency_positions": 0,
                "medium_urgency_positions": 0,
                "low_urgency_positions": 0,
                "urgency_distribution": {"high": 0.0, "medium": 0.0, "low": 0.0},
                "error": str(e),
            }
