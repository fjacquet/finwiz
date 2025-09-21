"""
Unit tests for derivatives pricing module.

Tests the DerivativesPricer class and related functionality for option pricing,
bond pricing, and risk analytics using both Black-Scholes and QuantLib models.
"""

import math
from unittest.mock import MagicMock, patch

import pytest

from finwiz.quantitative.derivatives import (
    BondParameters,
    BondPricingResult,
    DerivativesPricer,
    ExerciseStyle,
    OptionGreeks,
    OptionParameters,
    OptionPricingResult,
    OptionType,
    PricingModel,
)


class TestDerivativesPricer:
    """Test cases for DerivativesPricer class."""

    @pytest.fixture
    def pricer(self):
        """Create a derivatives pricer instance."""
        return DerivativesPricer()

    @pytest.fixture
    def call_option_params(self):
        """Create call option parameters for testing."""
        return OptionParameters(
            underlying_price=100.0,
            strike_price=105.0,
            time_to_expiry=0.25,  # 3 months
            risk_free_rate=0.05,
            volatility=0.20,
            dividend_yield=0.02,
            option_type=OptionType.CALL,
            exercise_style=ExerciseStyle.EUROPEAN,
        )

    @pytest.fixture
    def put_option_params(self):
        """Create put option parameters for testing."""
        return OptionParameters(
            underlying_price=100.0,
            strike_price=95.0,
            time_to_expiry=0.5,  # 6 months
            risk_free_rate=0.05,
            volatility=0.25,
            dividend_yield=0.0,
            option_type=OptionType.PUT,
            exercise_style=ExerciseStyle.EUROPEAN,
        )

    @pytest.fixture
    def bond_params(self):
        """Create bond parameters for testing."""
        return BondParameters(
            face_value=1000.0, coupon_rate=0.05, years_to_maturity=5.0, yield_to_maturity=0.04, coupon_frequency=2
        )

    def test_pricer_initialization(self, pricer):
        """Test derivatives pricer initialization."""
        assert pricer is not None
        assert hasattr(pricer, "config")
        assert hasattr(pricer, "_quantlib_available")

    def test_check_quantlib_availability(self, pricer):
        """Test QuantLib availability check."""
        # Test with QuantLib not available (default case)
        with patch("finwiz.quantitative.derivatives.logger"):
            availability = pricer._check_quantlib_availability()
            assert isinstance(availability, bool)

    def test_price_call_option_black_scholes(self, pricer, call_option_params):
        """Test call option pricing using Black-Scholes model."""
        result = pricer.price_option(call_option_params, PricingModel.BLACK_SCHOLES)

        assert isinstance(result, OptionPricingResult)
        assert result.option_price > 0
        assert result.pricing_model == PricingModel.BLACK_SCHOLES
        assert isinstance(result.greeks, OptionGreeks)
        assert result.calculation_time >= 0

        # Check Greeks are reasonable
        assert 0 < result.greeks.delta < 1  # Call delta should be positive
        assert result.greeks.gamma > 0  # Gamma should be positive
        assert result.greeks.theta < 0  # Theta should be negative (time decay)
        assert result.greeks.vega > 0  # Vega should be positive

    def test_price_put_option_black_scholes(self, pricer, put_option_params):
        """Test put option pricing using Black-Scholes model."""
        result = pricer.price_option(put_option_params, PricingModel.BLACK_SCHOLES)

        assert isinstance(result, OptionPricingResult)
        assert result.option_price > 0
        assert result.pricing_model == PricingModel.BLACK_SCHOLES

        # Check Greeks are reasonable for put
        assert -1 < result.greeks.delta < 0  # Put delta should be negative
        assert result.greeks.gamma > 0  # Gamma should be positive
        assert result.greeks.theta < 0  # Theta should be negative
        assert result.greeks.vega > 0  # Vega should be positive

    def test_option_pricing_with_quantlib_unavailable(self, pricer, call_option_params):
        """Test option pricing when QuantLib is not available."""
        pricer._quantlib_available = False

        result = pricer.price_option(call_option_params, PricingModel.BINOMIAL)

        # Should fallback to Black-Scholes
        assert result.pricing_model == PricingModel.BLACK_SCHOLES
        assert result.option_price > 0

    @patch("finwiz.quantitative.derivatives.logger")
    def test_option_pricing_quantlib_mock(self, mock_logger, pricer, call_option_params):
        """Test option pricing with mocked QuantLib."""
        # Mock QuantLib availability
        pricer._quantlib_available = True

        # Mock QuantLib modules
        mock_ql = MagicMock()
        mock_ql.Settings.instance.return_value.evaluationDate = MagicMock()
        mock_ql.Date.todaysDate.return_value = MagicMock()
        mock_ql.PlainVanillaPayoff.return_value = MagicMock()
        mock_ql.Option.Call = 1
        mock_ql.EuropeanExercise.return_value = MagicMock()
        mock_ql.VanillaOption.return_value = MagicMock()

        # Mock option methods
        mock_option = MagicMock()
        mock_option.NPV.return_value = 5.0
        mock_option.delta.return_value = 0.6
        mock_option.gamma.return_value = 0.02
        mock_option.theta.return_value = -10.0
        mock_option.vega.return_value = 20.0
        mock_option.rho.return_value = 15.0

        mock_ql.VanillaOption.return_value = mock_option

        with patch.dict("sys.modules", {"QuantLib": mock_ql}):
            result = pricer._price_option_quantlib(call_option_params, PricingModel.BINOMIAL)

            assert isinstance(result, OptionPricingResult)
            assert result.option_price == 5.0
            assert result.greeks.delta == 0.6

    def test_bond_pricing_simple(self, pricer, bond_params):
        """Test bond pricing using simple present value calculation."""
        result = pricer.price_bond(bond_params)

        assert isinstance(result, BondPricingResult)
        assert result.bond_price > 0
        assert result.duration > 0
        assert result.convexity >= 0
        assert result.yield_to_maturity == bond_params.yield_to_maturity
        assert result.accrued_interest >= 0

    def test_bond_pricing_with_quantlib_unavailable(self, pricer, bond_params):
        """Test bond pricing when QuantLib is not available."""
        pricer._quantlib_available = False

        result = pricer._price_bond_simple(bond_params)

        assert isinstance(result, BondPricingResult)
        assert result.bond_price > 0
        # Bond should trade at premium when YTM < coupon rate
        assert result.bond_price > bond_params.face_value

    def test_calculate_implied_volatility(self, pricer, call_option_params):
        """Test implied volatility calculation."""
        # First get theoretical price
        theoretical_result = pricer.price_option(call_option_params)
        market_price = theoretical_result.option_price

        # Calculate implied volatility
        implied_vol = pricer.calculate_implied_volatility(market_price, call_option_params)

        assert isinstance(implied_vol, float)
        assert implied_vol > 0
        # Should be close to original volatility
        assert abs(implied_vol - call_option_params.volatility) < 0.01

    def test_calculate_implied_volatility_convergence(self, pricer, call_option_params):
        """Test implied volatility calculation with different market prices."""
        # Test with higher market price (should give higher implied vol)
        high_market_price = 10.0
        high_implied_vol = pricer.calculate_implied_volatility(high_market_price, call_option_params)

        # Test with lower market price (should give lower implied vol)
        low_market_price = 1.0
        low_implied_vol = pricer.calculate_implied_volatility(low_market_price, call_option_params)

        assert high_implied_vol > low_implied_vol
        assert high_implied_vol > 0
        assert low_implied_vol > 0

    def test_calculate_portfolio_greeks(self, pricer, call_option_params, put_option_params):
        """Test portfolio Greeks calculation."""
        positions = [
            (call_option_params, 100),  # Long 100 calls
            (put_option_params, -50),  # Short 50 puts
        ]

        portfolio_greeks = pricer.calculate_option_portfolio_greeks(positions)

        assert isinstance(portfolio_greeks, OptionGreeks)
        # Portfolio delta should be positive (net long calls)
        assert portfolio_greeks.delta > 0
        assert portfolio_greeks.gamma != 0
        assert portfolio_greeks.theta != 0
        assert portfolio_greeks.vega != 0
        assert portfolio_greeks.rho != 0

    def test_get_pricing_models(self, pricer):
        """Test getting available pricing models."""
        models = pricer.get_pricing_models()

        assert isinstance(models, list)
        assert PricingModel.BLACK_SCHOLES in models

        # When QuantLib is available, should have more models
        pricer._quantlib_available = True
        models_with_quantlib = pricer.get_pricing_models()
        assert len(models_with_quantlib) >= len(models)

    def test_validate_option_parameters_valid(self, pricer, call_option_params):
        """Test option parameter validation with valid parameters."""
        is_valid = pricer.validate_option_parameters(call_option_params)
        assert is_valid is True

    def test_validate_option_parameters_invalid(self, pricer):
        """Test option parameter validation with invalid parameters."""
        # Test negative underlying price
        invalid_params = OptionParameters(
            underlying_price=-100.0,
            strike_price=105.0,
            time_to_expiry=0.25,
            risk_free_rate=0.05,
            volatility=0.20,
            option_type=OptionType.CALL,
        )

        is_valid = pricer.validate_option_parameters(invalid_params)
        assert is_valid is False

    def test_validate_option_parameters_extreme_values(self, pricer):
        """Test option parameter validation with extreme values."""
        # Test very high volatility
        extreme_params = OptionParameters(
            underlying_price=100.0,
            strike_price=105.0,
            time_to_expiry=0.25,
            risk_free_rate=0.05,
            volatility=10.0,  # 1000% volatility
            option_type=OptionType.CALL,
        )

        is_valid = pricer.validate_option_parameters(extreme_params)
        assert is_valid is False

    def test_option_pricing_error_handling(self, pricer):
        """Test error handling in option pricing."""
        # Test with invalid parameters
        invalid_params = OptionParameters(
            underlying_price=0.0,  # Invalid
            strike_price=105.0,
            time_to_expiry=0.25,
            risk_free_rate=0.05,
            volatility=0.20,
            option_type=OptionType.CALL,
        )

        with pytest.raises(Exception):
            pricer.price_option(invalid_params)

    def test_bond_pricing_error_handling(self, pricer):
        """Test error handling in bond pricing."""
        # Test with invalid parameters
        invalid_params = BondParameters(
            face_value=-1000.0,  # Invalid
            coupon_rate=0.05,
            years_to_maturity=5.0,
            yield_to_maturity=0.04,
            coupon_frequency=2,
        )

        with pytest.raises(Exception):
            pricer.price_bond(invalid_params)

    def test_greeks_calculation_accuracy(self, pricer, call_option_params):
        """Test accuracy of Greeks calculations."""
        result = pricer.price_option(call_option_params)
        greeks = result.greeks

        # Test delta is between 0 and 1 for call
        assert 0 <= greeks.delta <= 1

        # Test gamma is positive
        assert greeks.gamma > 0

        # Test theta is negative (time decay)
        assert greeks.theta < 0

        # Test vega is positive
        assert greeks.vega > 0

        # Test reasonable magnitudes
        assert abs(greeks.delta) < 1
        assert abs(greeks.gamma) < 1
        assert abs(greeks.theta) < 100  # Daily theta shouldn't be too large
        assert abs(greeks.vega) < 100  # Vega per 1% vol change
        assert abs(greeks.rho) < 100  # Rho per 1% rate change

    def test_put_call_parity(self, pricer):
        """Test put-call parity relationship."""
        # Create matching call and put options
        S = 100.0
        K = 100.0
        T = 0.25
        r = 0.05
        sigma = 0.20
        q = 0.02

        call_params = OptionParameters(
            underlying_price=S,
            strike_price=K,
            time_to_expiry=T,
            risk_free_rate=r,
            volatility=sigma,
            dividend_yield=q,
            option_type=OptionType.CALL,
        )

        put_params = OptionParameters(
            underlying_price=S,
            strike_price=K,
            time_to_expiry=T,
            risk_free_rate=r,
            volatility=sigma,
            dividend_yield=q,
            option_type=OptionType.PUT,
        )

        call_result = pricer.price_option(call_params)
        put_result = pricer.price_option(put_params)

        # Put-call parity: C - P = S*e^(-q*T) - K*e^(-r*T)
        call_price = call_result.option_price
        put_price = put_result.option_price

        left_side = call_price - put_price
        right_side = S * math.exp(-q * T) - K * math.exp(-r * T)

        # Should be approximately equal (within small tolerance)
        assert abs(left_side - right_side) < 0.01

    def test_bond_duration_calculation(self, pricer, bond_params):
        """Test bond duration calculation."""
        result = pricer._price_bond_simple(bond_params)

        # Duration should be positive and less than time to maturity
        assert result.duration > 0
        assert result.duration < bond_params.years_to_maturity

        # For bonds trading at par, duration should be reasonable
        expected_duration = bond_params.years_to_maturity * 0.8  # Rough approximation
        assert abs(result.duration - expected_duration) < bond_params.years_to_maturity

    def test_bond_convexity_calculation(self, pricer, bond_params):
        """Test bond convexity calculation."""
        result = pricer._price_bond_simple(bond_params)

        # Convexity should be positive
        assert result.convexity > 0

        # Convexity should be reasonable relative to duration
        assert result.convexity > result.duration
