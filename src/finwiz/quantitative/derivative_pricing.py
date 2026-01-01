"""
Derivatives pricing models for FinWiz quantitative analysis.

This module provides pricing models for options and bonds using Black-Scholes
and QuantLib integration for professional-grade financial instrument valuation.
"""

import math
from enum import Enum

from pydantic import BaseModel, Field

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


class BlackScholesCalculator:
    """Black-Scholes option pricing calculator."""

    @staticmethod
    def norm_cdf(x: float) -> float:
        """Standard normal cumulative distribution function."""
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    @staticmethod
    def norm_pdf(x: float) -> float:
        """Standard normal probability density function."""
        return math.exp(-0.5 * x**2) / math.sqrt(2 * math.pi)

    @staticmethod
    def calculate_d1_d2(S: float, K: float, T: float, r: float, sigma: float, q: float) -> tuple[float, float]:
        """Calculate d1 and d2 for Black-Scholes formula."""
        d1 = (math.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        return d1, d2

    @classmethod
    def price_option(cls, params: OptionParameters) -> OptionPricingResult:
        """Price option using Black-Scholes model."""
        S = params.underlying_price
        K = params.strike_price
        T = params.time_to_expiry
        r = params.risk_free_rate
        sigma = params.volatility
        q = params.dividend_yield

        # Calculate d1 and d2
        d1, d2 = cls.calculate_d1_d2(S, K, T, r, sigma, q)

        # Calculate option price
        if params.option_type == OptionType.CALL:
            option_price = S * math.exp(-q * T) * cls.norm_cdf(d1) - K * math.exp(-r * T) * cls.norm_cdf(d2)
        else:  # PUT
            option_price = K * math.exp(-r * T) * cls.norm_cdf(-d2) - S * math.exp(-q * T) * cls.norm_cdf(-d1)

        # Calculate Greeks
        delta = cls._calculate_delta(S, K, T, r, sigma, q, params.option_type, d1)
        gamma = cls._calculate_gamma(S, T, sigma, q, d1)
        theta = cls._calculate_theta(S, K, T, r, sigma, q, params.option_type, d1, d2)
        vega = cls._calculate_vega(S, T, sigma, q, d1)
        rho = cls._calculate_rho(K, T, r, params.option_type, d2)

        greeks = OptionGreeks(delta=delta, gamma=gamma, theta=theta, vega=vega, rho=rho)

        return OptionPricingResult(
            option_price=option_price,
            greeks=greeks,
            pricing_model=PricingModel.BLACK_SCHOLES,
            calculation_time=0.0,  # Will be set by caller
        )

    @classmethod
    def _calculate_delta(cls, S: float, K: float, T: float, r: float, sigma: float, q: float, option_type: OptionType, d1: float) -> float:
        """Calculate option delta."""
        if option_type == OptionType.CALL:
            return math.exp(-q * T) * cls.norm_cdf(d1)
        else:
            return math.exp(-q * T) * (cls.norm_cdf(d1) - 1)

    @classmethod
    def _calculate_gamma(cls, S: float, T: float, sigma: float, q: float, d1: float) -> float:
        """Calculate option gamma."""
        return (math.exp(-q * T) * cls.norm_pdf(d1)) / (S * sigma * math.sqrt(T))

    @classmethod
    def _calculate_theta(cls, S: float, K: float, T: float, r: float, sigma: float, q: float, option_type: OptionType, d1: float, d2: float) -> float:
        """Calculate option theta (time decay)."""
        term1 = -(S * math.exp(-q * T) * cls.norm_pdf(d1) * sigma) / (2 * math.sqrt(T))

        if option_type == OptionType.CALL:
            term2 = q * S * math.exp(-q * T) * cls.norm_cdf(d1)
            term3 = -r * K * math.exp(-r * T) * cls.norm_cdf(d2)
        else:
            term2 = -q * S * math.exp(-q * T) * cls.norm_cdf(-d1)
            term3 = r * K * math.exp(-r * T) * cls.norm_cdf(-d2)

        return (term1 + term2 + term3) / 365  # Convert to daily theta

    @classmethod
    def _calculate_vega(cls, S: float, T: float, sigma: float, q: float, d1: float) -> float:
        """Calculate option vega."""
        return (S * math.exp(-q * T) * cls.norm_pdf(d1) * math.sqrt(T)) / 100  # Per 1% vol change

    @classmethod
    def _calculate_rho(cls, K: float, T: float, r: float, option_type: OptionType, d2: float) -> float:
        """Calculate option rho."""
        if option_type == OptionType.CALL:
            return (K * T * math.exp(-r * T) * cls.norm_cdf(d2)) / 100  # Per 1% rate change
        else:
            return (-K * T * math.exp(-r * T) * cls.norm_cdf(-d2)) / 100


class QuantLibPricer:
    """QuantLib-based derivatives pricer."""

    def __init__(self, quantlib_available: bool) -> None:
        """Initialize QuantLib pricer."""
        self._quantlib_available = quantlib_available

    def price_option(self, params: OptionParameters, model: PricingModel) -> OptionPricingResult:
        """Price option using QuantLib (if available)."""
        if not self._quantlib_available:
            raise RuntimeError("QuantLib not available for advanced pricing models")

        try:
            import QuantLib as ql  # QuantLib has no official type stubs

            # Set up QuantLib calculation date
            ql.Settings.instance().evaluationDate = ql.Date.todaysDate()

            # Create option
            payoff = ql.PlainVanillaPayoff(ql.Option.Call if params.option_type == OptionType.CALL else ql.Option.Put, params.strike_price)

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
            return BlackScholesCalculator.price_option(params)

    def price_bond(self, params: BondParameters) -> BondPricingResult:
        """Price bond using QuantLib (if available)."""
        if not self._quantlib_available:
            raise RuntimeError("QuantLib not available for bond pricing")

        try:
            import QuantLib as ql  # QuantLib has no official type stubs

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
            raise


class SimpleBondPricer:
    """Simple bond pricing calculator using present value."""

    @staticmethod
    def price_bond(params: BondParameters) -> BondPricingResult:
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
        duration = SimpleBondPricer._calculate_modified_duration(params)

        # Calculate convexity (approximation)
        convexity = SimpleBondPricer._calculate_convexity(params)

        return BondPricingResult(
            bond_price=bond_price,
            duration=duration,
            convexity=convexity,
            yield_to_maturity=ytm,
            accrued_interest=0.0,  # Simplified - assume no accrued interest
        )

    @staticmethod
    def _calculate_modified_duration(params: BondParameters) -> float:
        """Calculate modified duration approximation."""
        # Simplified calculation for modified duration
        ytm = params.yield_to_maturity
        frequency = params.coupon_frequency
        years = params.years_to_maturity

        # Macaulay duration approximation
        macaulay_duration = (1 + ytm / frequency) / (ytm / frequency) - (1 + ytm / frequency + frequency * years * (params.coupon_rate / frequency - ytm / frequency)) / (
            frequency * ((1 + ytm / frequency) ** (frequency * years) - 1) + ytm / frequency
        )

        # Modified duration
        modified_duration = macaulay_duration / (1 + ytm / frequency)

        return float(modified_duration)

    @staticmethod
    def _calculate_convexity(params: BondParameters) -> float:
        """Calculate convexity approximation."""
        # Simplified convexity calculation
        ytm = params.yield_to_maturity
        years = params.years_to_maturity

        # Approximate convexity
        convexity = (2 * years * (years + 1)) / ((1 + ytm) ** 2)

        return convexity
