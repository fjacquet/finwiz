"""
Derivatives risk calculations for FinWiz quantitative analysis.

This module provides risk analytics for derivatives including Greeks calculations,
implied volatility computation, and portfolio risk aggregation.
"""

from finwiz.quantitative.derivative_pricing import (
    BlackScholesCalculator,
    OptionGreeks,
    OptionParameters,
)
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class ImpliedVolatilityCalculator:
    """Implied volatility calculator using Newton-Raphson method."""

    @staticmethod
    def calculate(
        market_price: float,
        parameters: OptionParameters,
        tolerance: float = 1e-6,
        max_iterations: int = 100,
    ) -> float:
        """
        Calculate implied volatility using Newton-Raphson method.

        Args:
            market_price: Market price of the option
            parameters: Option parameters (volatility will be ignored)
            tolerance: Convergence tolerance
            max_iterations: Maximum number of iterations

        Returns:
            Implied volatility

        """
        # Initial guess
        vol = 0.2

        for i in range(max_iterations):
            # Create parameters with current volatility guess
            test_params = parameters.copy()
            test_params.volatility = vol

            # Calculate theoretical price and vega
            result = BlackScholesCalculator.price_option(test_params)
            theoretical_price = result.option_price
            vega = result.greeks.vega * 100  # Convert back to absolute vega

            # Calculate price difference
            price_diff = theoretical_price - market_price

            # Check convergence
            if abs(price_diff) < tolerance:
                return vol

            # Newton-Raphson update
            if abs(vega) > 1e-10:  # Avoid division by zero
                vol = vol - price_diff / vega
            else:
                break

            # Ensure volatility stays positive
            vol = max(vol, 0.001)

        logger.warning(f"Implied volatility calculation did not converge after {max_iterations} iterations")
        return vol


class PortfolioGreeksCalculator:
    """Portfolio Greeks calculator for multiple option positions."""

    @staticmethod
    def calculate_portfolio_greeks(positions: list[tuple[OptionParameters, float]]) -> OptionGreeks:
        """
        Calculate portfolio Greeks for multiple option positions.

        Args:
            positions: List of (option_parameters, position_size) tuples

        Returns:
            Portfolio Greeks

        """
        total_delta = 0.0
        total_gamma = 0.0
        total_theta = 0.0
        total_vega = 0.0
        total_rho = 0.0

        for params, position_size in positions:
            result = BlackScholesCalculator.price_option(params)
            greeks = result.greeks

            total_delta += greeks.delta * position_size
            total_gamma += greeks.gamma * position_size
            total_theta += greeks.theta * position_size
            total_vega += greeks.vega * position_size
            total_rho += greeks.rho * position_size

        return OptionGreeks(
            delta=total_delta,
            gamma=total_gamma,
            theta=total_theta,
            vega=total_vega,
            rho=total_rho,
        )


class OptionParameterValidator:
    """Validator for option parameters."""

    @staticmethod
    def validate(parameters: OptionParameters) -> bool:
        """
        Validate option parameters for pricing.

        Args:
            parameters: Option parameters to validate

        Returns:
            True if parameters are valid

        """
        try:
            # Check for reasonable parameter ranges
            if parameters.underlying_price <= 0:
                logger.error("Underlying price must be positive")
                return False

            if parameters.strike_price <= 0:
                logger.error("Strike price must be positive")
                return False

            if parameters.time_to_expiry <= 0:
                logger.error("Time to expiry must be positive")
                return False

            if parameters.time_to_expiry > 10:
                logger.warning("Time to expiry is very long (>10 years)")

            if parameters.volatility <= 0 or parameters.volatility > 5:
                logger.error("Volatility must be positive and reasonable (<500%)")
                return False

            if parameters.risk_free_rate < -0.1 or parameters.risk_free_rate > 0.5:
                logger.warning("Risk-free rate seems unusual")

            return True

        except Exception as e:
            logger.error(f"Parameter validation failed: {e}")
            return False
