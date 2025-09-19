"""
Derivatives pricing module for FinWiz quantitative analysis.

This module provides comprehensive derivatives pricing capabilities using QuantLib
for professional-grade financial instrument valuation including options, bonds,
and other derivative instruments.
"""

import math
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from finwiz.quantitative.config import get_quant_config
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class OptionType(str, Enum):
    """Option types for derivatives pricing."""

    CALL = "call"
    PUT = "put"


class ExerciseStyle(str, Enum):
    """Exercise styles for options."""

    EUROPEAN = "european"
    AMERICAN = "american"
    BERMUDAN = "bermudan"


class PricingModel(str, Enum):
    """Pricing models for derivatives."""

    BLACK_SCHOLES = "black_scholes"
    BINOMIAL = "binomial"
    MONTE_CARLO = "monte_carlo"
    FINITE_DIFFERENCE = "finite_difference"


class OptionParameters(BaseModel):
    """Parameters for option pricing."""

    underlying_price: float = Field(..., gt=0, description="Current price of underlying asset")
    strike_price: float = Field(..., gt=0, description="Strike price of the option")
    time_to_expiry: float = Field(..., gt=0, description="Time to expiry in years")
    risk_free_rate: float = Field(..., ge=0, description="Risk-free interest rate")
    volatility: float = Field(..., gt=0, description="Implied volatility of underlying")
    dividend_yield: float = Field(default=0.0, ge=0, description="Dividend yield of underlying")
    option_type: OptionType = Field(..., description="Type of option (call or put)")
    exercise_style: ExerciseStyle = Field(default=ExerciseStyle.EUROPEAN, description="Exercise style")

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        extra = "forbid"


class OptionGreeks(BaseModel):
    """Option Greeks for risk management."""

    delta: float = Field(..., description="Price sensitivity to underlying price")
    gamma: float = Field(..., description="Delta sensitivity to underlying price")
    theta: float = Field(..., description="Price sensitivity to time decay")
    vega: float = Field(..., description="Price sensitivity to volatility")
    rho: float = Field(..., description="Price sensitivity to interest rate")

    class Config:
        """Pydantic configuration."""

        extra = "forbid"


class OptionPricingResult(BaseModel):
    """Result of option pricing calculation."""

    option_price: float = Field(..., description="Theoretical option price")
    greeks: OptionGreeks = Field(..., description="Option Greeks")
    implied_volatility: float | None = Field(None, description="Implied volatility if calculated")
    pricing_model: PricingModel = Field(..., description="Pricing model used")
    calculation_time: float = Field(..., description="Calculation time in seconds")

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        extra = "forbid"


class BondParameters(BaseModel):
    """Parameters for bond pricing."""

    face_value: float = Field(default=100.0, gt=0, description="Face value of the bond")
    coupon_rate: float = Field(..., ge=0, description="Annual coupon rate")
    years_to_maturity: float = Field(..., gt=0, description="Years to maturity")
    yield_to_maturity: float = Field(..., ge=0, description="Yield to maturity")
    coupon_frequency: int = Field(default=2, gt=0, description="Coupon payments per year")

    class Config:
        """Pydantic configuration."""

        extra = "forbid"


class BondPricingResult(BaseModel):
    """Result of bond pricing calculation."""

    bond_price: float = Field(..., description="Bond price")
    duration: float = Field(..., description="Modified duration")
    convexity: float = Field(..., description="Convexity")
    yield_to_maturity: float = Field(..., description="Yield to maturity")
    accrued_interest: float = Field(..., description="Accrued interest")

    class Config:
        """Pydantic configuration."""

        extra = "forbid"


class DerivativesPricer:
    """
    Professional derivatives pricing engine using QuantLib integration.

    Provides comprehensive pricing capabilities for options, bonds, and other
    derivative instruments with multiple pricing models and risk analytics.
    """

    def __init__(self):
        """Initialize the derivatives pricer."""
        self.config = get_quant_config()
        self._quantlib_available = self._check_quantlib_availability()

        if not self._quantlib_available:
            logger.warning("QuantLib not available, using fallback implementations")

    def _check_quantlib_availability(self) -> bool:
        """Check if QuantLib is available for advanced pricing."""
        try:
            import QuantLib as ql

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
                result = self._price_option_quantlib(parameters, model)
            else:
                result = self._price_option_black_scholes(parameters)

            calculation_time = (datetime.now() - start_time).total_seconds()
            result.calculation_time = calculation_time

            logger.info(f"Option priced successfully using {model} model in {calculation_time:.3f}s")
            return result

        except Exception as e:
            logger.error(f"Option pricing failed: {e}")
            raise

    def _price_option_black_scholes(self, params: OptionParameters) -> OptionPricingResult:
        """Price option using Black-Scholes model."""
        S = params.underlying_price
        K = params.strike_price
        T = params.time_to_expiry
        r = params.risk_free_rate
        sigma = params.volatility
        q = params.dividend_yield

        # Calculate d1 and d2
        d1 = (math.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)

        # Standard normal CDF
        def norm_cdf(x):
            return 0.5 * (1 + math.erf(x / math.sqrt(2)))

        # Standard normal PDF
        def norm_pdf(x):
            return math.exp(-0.5 * x**2) / math.sqrt(2 * math.pi)

        # Calculate option price
        if params.option_type == OptionType.CALL:
            option_price = S * math.exp(-q * T) * norm_cdf(d1) - K * math.exp(-r * T) * norm_cdf(d2)
        else:  # PUT
            option_price = K * math.exp(-r * T) * norm_cdf(-d2) - S * math.exp(-q * T) * norm_cdf(-d1)

        # Calculate Greeks
        delta = self._calculate_delta(S, K, T, r, sigma, q, params.option_type, d1)
        gamma = self._calculate_gamma(S, T, sigma, q, d1)
        theta = self._calculate_theta(S, K, T, r, sigma, q, params.option_type, d1, d2)
        vega = self._calculate_vega(S, T, sigma, q, d1)
        rho = self._calculate_rho(K, T, r, params.option_type, d2)

        greeks = OptionGreeks(delta=delta, gamma=gamma, theta=theta, vega=vega, rho=rho)

        return OptionPricingResult(
            option_price=option_price,
            greeks=greeks,
            pricing_model=PricingModel.BLACK_SCHOLES,
            calculation_time=0.0,  # Will be set by caller
        )

    def _price_option_quantlib(self, params: OptionParameters, model: PricingModel) -> OptionPricingResult:
        """Price option using QuantLib (if available)."""
        if not self._quantlib_available:
            raise RuntimeError("QuantLib not available for advanced pricing models")

        try:
            import QuantLib as ql

            # Set up QuantLib calculation date
            ql.Settings.instance().evaluationDate = ql.Date.todaysDate()

            # Create option
            payoff = ql.PlainVanillaPayoff(
                ql.Option.Call if params.option_type == OptionType.CALL else ql.Option.Put, params.strike_price
            )

            # Create exercise
            if params.exercise_style == ExerciseStyle.EUROPEAN:
                expiry_date = ql.Date.todaysDate() + int(params.time_to_expiry * 365)
                exercise = ql.EuropeanExercise(expiry_date)
            else:
                # For American options
                expiry_date = ql.Date.todaysDate() + int(params.time_to_expiry * 365)
                exercise = ql.AmericanExercise(ql.Date.todaysDate(), expiry_date)

            option = ql.VanillaOption(payoff, exercise)

            # Set up market data
            underlying = ql.SimpleQuote(params.underlying_price)
            volatility = ql.BlackConstantVol(ql.Date.todaysDate(), ql.TARGET(), params.volatility, ql.Actual365Fixed())
            risk_free_rate = ql.FlatForward(ql.Date.todaysDate(), params.risk_free_rate, ql.Actual365Fixed())
            dividend_yield = ql.FlatForward(ql.Date.todaysDate(), params.dividend_yield, ql.Actual365Fixed())

            # Create Black-Scholes process
            process = ql.BlackScholesMertonProcess(
                ql.QuoteHandle(underlying),
                ql.YieldTermStructureHandle(dividend_yield),
                ql.YieldTermStructureHandle(risk_free_rate),
                ql.BlackVolTermStructureHandle(volatility),
            )

            # Set pricing engine based on model
            if model == PricingModel.BINOMIAL:
                engine = ql.BinomialVanillaEngine(process, "crr", 100)
            elif model == PricingModel.MONTE_CARLO:
                engine = ql.MCEuropeanEngine(process, "pseudorandom", timeSteps=252, requiredSamples=10000)
            else:
                engine = ql.AnalyticEuropeanEngine(process)

            option.setPricingEngine(engine)

            # Calculate price and Greeks
            option_price = option.NPV()
            delta = option.delta()
            gamma = option.gamma()
            theta = option.theta()
            vega = option.vega()
            rho = option.rho()

            greeks = OptionGreeks(
                delta=delta,
                gamma=gamma,
                theta=theta / 365,  # Convert to daily theta
                vega=vega / 100,  # Convert to 1% volatility change
                rho=rho / 100,  # Convert to 1% rate change
            )

            return OptionPricingResult(
                option_price=option_price,
                greeks=greeks,
                pricing_model=model,
                calculation_time=0.0,  # Will be set by caller
            )

        except Exception as e:
            logger.error(f"QuantLib option pricing failed: {e}")
            # Fallback to Black-Scholes
            return self._price_option_black_scholes(params)

    def _calculate_delta(
        self, S: float, K: float, T: float, r: float, sigma: float, q: float, option_type: OptionType, d1: float
    ) -> float:
        """Calculate option delta."""

        def norm_cdf(x):
            return 0.5 * (1 + math.erf(x / math.sqrt(2)))

        if option_type == OptionType.CALL:
            return math.exp(-q * T) * norm_cdf(d1)
        else:
            return math.exp(-q * T) * (norm_cdf(d1) - 1)

    def _calculate_gamma(self, S: float, T: float, sigma: float, q: float, d1: float) -> float:
        """Calculate option gamma."""

        def norm_pdf(x):
            return math.exp(-0.5 * x**2) / math.sqrt(2 * math.pi)

        return (math.exp(-q * T) * norm_pdf(d1)) / (S * sigma * math.sqrt(T))

    def _calculate_theta(
        self, S: float, K: float, T: float, r: float, sigma: float, q: float, option_type: OptionType, d1: float, d2: float
    ) -> float:
        """Calculate option theta (time decay)."""

        def norm_cdf(x):
            return 0.5 * (1 + math.erf(x / math.sqrt(2)))

        def norm_pdf(x):
            return math.exp(-0.5 * x**2) / math.sqrt(2 * math.pi)

        term1 = -(S * math.exp(-q * T) * norm_pdf(d1) * sigma) / (2 * math.sqrt(T))

        if option_type == OptionType.CALL:
            term2 = q * S * math.exp(-q * T) * norm_cdf(d1)
            term3 = -r * K * math.exp(-r * T) * norm_cdf(d2)
        else:
            term2 = -q * S * math.exp(-q * T) * norm_cdf(-d1)
            term3 = r * K * math.exp(-r * T) * norm_cdf(-d2)

        return (term1 + term2 + term3) / 365  # Convert to daily theta

    def _calculate_vega(self, S: float, T: float, sigma: float, q: float, d1: float) -> float:
        """Calculate option vega."""

        def norm_pdf(x):
            return math.exp(-0.5 * x**2) / math.sqrt(2 * math.pi)

        return (S * math.exp(-q * T) * norm_pdf(d1) * math.sqrt(T)) / 100  # Per 1% vol change

    def _calculate_rho(self, K: float, T: float, r: float, option_type: OptionType, d2: float) -> float:
        """Calculate option rho."""

        def norm_cdf(x):
            return 0.5 * (1 + math.erf(x / math.sqrt(2)))

        if option_type == OptionType.CALL:
            return (K * T * math.exp(-r * T) * norm_cdf(d2)) / 100  # Per 1% rate change
        else:
            return (-K * T * math.exp(-r * T) * norm_cdf(-d2)) / 100

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
                return self._price_bond_quantlib(parameters)
            else:
                return self._price_bond_simple(parameters)

        except Exception as e:
            logger.error(f"Bond pricing failed: {e}")
            raise

    def _price_bond_simple(self, params: BondParameters) -> BondPricingResult:
        """Price bond using simple present value calculation."""
        face_value = params.face_value
        coupon_rate = params.coupon_rate
        years_to_maturity = params.years_to_maturity
        ytm = params.yield_to_maturity
        frequency = params.coupon_frequency

        # Calculate coupon payment
        coupon_payment = (coupon_rate * face_value) / frequency

        # Calculate number of periods
        num_periods = int(years_to_maturity * frequency)

        # Calculate bond price using present value formula
        bond_price = 0.0

        # Present value of coupon payments
        for period in range(1, num_periods + 1):
            pv_coupon = coupon_payment / ((1 + ytm / frequency) ** period)
            bond_price += pv_coupon

        # Present value of face value
        pv_face_value = face_value / ((1 + ytm / frequency) ** num_periods)
        bond_price += pv_face_value

        # Calculate modified duration (approximation)
        duration = self._calculate_modified_duration(params)

        # Calculate convexity (approximation)
        convexity = self._calculate_convexity(params)

        return BondPricingResult(
            bond_price=bond_price,
            duration=duration,
            convexity=convexity,
            yield_to_maturity=ytm,
            accrued_interest=0.0,  # Simplified - assume no accrued interest
        )

    def _price_bond_quantlib(self, params: BondParameters) -> BondPricingResult:
        """Price bond using QuantLib (if available)."""
        if not self._quantlib_available:
            return self._price_bond_simple(params)

        try:
            import QuantLib as ql

            # Set calculation date
            ql.Settings.instance().evaluationDate = ql.Date.todaysDate()

            # Create bond schedule
            issue_date = ql.Date.todaysDate()
            maturity_date = issue_date + int(params.years_to_maturity * 365)

            schedule = ql.Schedule(
                issue_date,
                maturity_date,
                ql.Period(int(12 / params.coupon_frequency), ql.Months),
                ql.TARGET(),
                ql.Unadjusted,
                ql.Unadjusted,
                ql.DateGeneration.Backward,
                False,
            )

            # Create fixed rate bond
            bond = ql.FixedRateBond(
                0,  # settlement days
                params.face_value,
                schedule,
                [params.coupon_rate],
                ql.Actual360(),
            )

            # Set up yield curve
            yield_curve = ql.FlatForward(issue_date, params.yield_to_maturity, ql.Actual360())

            bond_engine = ql.DiscountingBondEngine(ql.YieldTermStructureHandle(yield_curve))
            bond.setPricingEngine(bond_engine)

            # Calculate metrics
            bond_price = bond.cleanPrice()
            duration = ql.BondFunctions.duration(bond, params.yield_to_maturity, ql.Actual360(), ql.Compounded, ql.Annual)
            convexity = ql.BondFunctions.convexity(bond, params.yield_to_maturity, ql.Actual360(), ql.Compounded, ql.Annual)
            accrued_interest = bond.accruedAmount()

            return BondPricingResult(
                bond_price=bond_price,
                duration=duration,
                convexity=convexity,
                yield_to_maturity=params.yield_to_maturity,
                accrued_interest=accrued_interest,
            )

        except Exception as e:
            logger.error(f"QuantLib bond pricing failed: {e}")
            return self._price_bond_simple(params)

    def _calculate_modified_duration(self, params: BondParameters) -> float:
        """Calculate modified duration approximation."""
        # Simplified calculation for modified duration
        ytm = params.yield_to_maturity
        frequency = params.coupon_frequency
        years = params.years_to_maturity

        # Macaulay duration approximation
        macaulay_duration = (1 + ytm / frequency) / (ytm / frequency) - (
            1 + ytm / frequency + frequency * years * (params.coupon_rate / frequency - ytm / frequency)
        ) / (frequency * ((1 + ytm / frequency) ** (frequency * years) - 1) + ytm / frequency)

        # Modified duration
        modified_duration = macaulay_duration / (1 + ytm / frequency)

        return modified_duration

    def _calculate_convexity(self, params: BondParameters) -> float:
        """Calculate convexity approximation."""
        # Simplified convexity calculation
        ytm = params.yield_to_maturity
        frequency = params.coupon_frequency
        years = params.years_to_maturity

        # Approximate convexity
        convexity = (2 * years * (years + 1)) / ((1 + ytm) ** 2)

        return convexity

    def calculate_implied_volatility(
        self, market_price: float, parameters: OptionParameters, tolerance: float = 1e-6, max_iterations: int = 100
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
            result = self._price_option_black_scholes(test_params)
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

    def calculate_option_portfolio_greeks(self, positions: list[tuple[OptionParameters, float]]) -> OptionGreeks:
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
            result = self.price_option(params)
            greeks = result.greeks

            total_delta += greeks.delta * position_size
            total_gamma += greeks.gamma * position_size
            total_theta += greeks.theta * position_size
            total_vega += greeks.vega * position_size
            total_rho += greeks.rho * position_size

        return OptionGreeks(delta=total_delta, gamma=total_gamma, theta=total_theta, vega=total_vega, rho=total_rho)

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
