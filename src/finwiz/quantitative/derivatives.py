"""
Derivatives pricing module for FinWiz quantitative analysis.

This module provides comprehensive derivatives pricing capabilities using QuantLib
for professional-grade financial instrument valuation including options, bonds,
and other derivative instruments.

Re-exports from derivative_pricing and derivative_risk modules for backward compatibility.
"""

from datetime import datetime

from finwiz.quantitative.config import get_quant_config
from finwiz.quantitative.derivative_pricing import (
    BlackScholesCalculator,
    BondParameters,
    BondPricingResult,
    ExerciseStyle,
    OptionGreeks,
    OptionParameters,
    OptionPricingResult,
    OptionType,
    PricingModel,
    QuantLibPricer,
    SimpleBondPricer,
)
from finwiz.quantitative.derivative_risk import (
    ImpliedVolatilityCalculator,
    OptionParameterValidator,
    PortfolioGreeksCalculator,
)
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

# Re-export for backward compatibility
__all__ = [
    "OptionType",
    "ExerciseStyle",
    "PricingModel",
    "OptionParameters",
    "OptionGreeks",
    "OptionPricingResult",
    "BondParameters",
    "BondPricingResult",
    "DerivativesPricer",
]


class DerivativesPricer:
    """
    Professional derivatives pricing engine using QuantLib integration.

    Provides comprehensive pricing capabilities for options, bonds, and other
    derivative instruments with multiple pricing models and risk analytics.
    """

    def __init__(self) -> None:
        """Initialize the derivatives pricer."""
        self.config = get_quant_config()
        self._quantlib_available = self._check_quantlib_availability()
        self._quantlib_pricer = QuantLibPricer(self._quantlib_available)

        if not self._quantlib_available:
            logger.warning("QuantLib not available, using fallback implementations")

    def _check_quantlib_availability(self) -> bool:
        """Check if QuantLib is available for advanced pricing."""
        try:
            import QuantLib  # noqa: F401  # type: ignore[import-untyped]  # QuantLib has no official type stubs

            return True
        except ImportError:
            return False

    def price_option(self, parameters: OptionParameters, model: PricingModel = PricingModel.BLACK_SCHOLES) -> OptionPricingResult:
        """
        Price an option using specified pricing model.

        Args:
            parameters: Option parameters
            model: Pricing model to use

        Returns:
            Option pricing result with price and Greeks

        """
        start_time = datetime.now()

        try:
            if self._quantlib_available and model != PricingModel.BLACK_SCHOLES:
                result = self._quantlib_pricer.price_option(parameters, model)
            else:
                result = BlackScholesCalculator.price_option(parameters)

            calculation_time = (datetime.now() - start_time).total_seconds()
            result.calculation_time = calculation_time

            logger.info(f"Option priced successfully using {model} model in {calculation_time:.3f}s")
            return result

        except Exception as e:
            logger.error(f"Option pricing failed: {e}")
            raise

    def price_bond(self, parameters: BondParameters) -> BondPricingResult:
        """
        Price a bond and calculate risk metrics.

        Args:
            parameters: Bond parameters

        Returns:
            Bond pricing result with price and risk metrics

        """
        try:
            if self._quantlib_available:
                return self._quantlib_pricer.price_bond(parameters)
            else:
                return SimpleBondPricer.price_bond(parameters)

        except Exception as e:
            logger.error(f"Bond pricing failed: {e}")
            raise

    def calculate_implied_volatility(self, market_price: float, parameters: OptionParameters, tolerance: float = 1e-6, max_iterations: int = 100) -> float:
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
        return ImpliedVolatilityCalculator.calculate(market_price, parameters, tolerance, max_iterations)

    def calculate_option_portfolio_greeks(self, positions: list[tuple[OptionParameters, float]]) -> OptionGreeks:
        """
        Calculate portfolio Greeks for multiple option positions.

        Args:
            positions: List of (option_parameters, position_size) tuples

        Returns:
            Portfolio Greeks

        """
        return PortfolioGreeksCalculator.calculate_portfolio_greeks(positions)

    def get_pricing_models(self) -> list[PricingModel]:
        """Get available pricing models."""
        models = [PricingModel.BLACK_SCHOLES]

        if self._quantlib_available:
            models.extend([PricingModel.BINOMIAL, PricingModel.MONTE_CARLO, PricingModel.FINITE_DIFFERENCE])

        return models

    def validate_option_parameters(self, parameters: OptionParameters) -> bool:
        """
        Validate option parameters for pricing.

        Args:
            parameters: Option parameters to validate

        Returns:
            True if parameters are valid

        """
        return OptionParameterValidator.validate(parameters)
