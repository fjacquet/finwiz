"""
Unit tests for price target calculation module.

Tests cover:
- DCF valuation with sample cash flows
- P/E target calculations
- Technical target calculations (Fibonacci, MA projection, trend channel)
- Support/resistance target calculations
- Consensus target calculations
- Confidence level validation
- Edge cases (empty data, invalid inputs, zero values)
"""

from pytest import approx
import pandas as pd
import pytest

from finwiz.utils.price_targets import (
    PriceTarget,
    calculate_consensus_target,
    calculate_dcf_target,
    calculate_pe_target,
    calculate_support_resistance_targets,
    calculate_technical_target,
)


class TestPriceTarget:
    """Test suite for PriceTarget class."""

    def test_should_create_price_target_with_upside(self):
        """Test PriceTarget creation with upside calculation."""
        # Arrange & Act
        target = PriceTarget(
            target_price=110.0,
            current_price=100.0,
            confidence=0.7,
            method="test",
        )

        # Assert
        assert target.target_price == approx(110.0)
        assert target.current_price == approx(100.0)
        assert target.confidence == approx(0.7)
        assert target.method == "test"
        assert target.upside_pct == pytest.approx(10.0, rel=1e-6)
        assert target.downside_pct == approx(0.0)

    def test_should_create_price_target_with_downside(self):
        """Test PriceTarget creation with downside calculation."""
        # Arrange & Act
        target = PriceTarget(
            target_price=90.0,
            current_price=100.0,
            confidence=0.6,
            method="test",
        )

        # Assert
        assert target.target_price == approx(90.0)
        assert target.upside_pct == pytest.approx(-10.0, rel=1e-6)
        assert target.downside_pct == pytest.approx(10.0, rel=1e-6)

    def test_should_create_price_target_without_current_price(self):
        """Test PriceTarget creation without current price."""
        # Arrange & Act
        target = PriceTarget(
            target_price=110.0,
            confidence=0.7,
            method="test",
        )

        # Assert
        assert target.target_price == approx(110.0)
        assert target.current_price is None
        assert target.upside_pct == approx(0.0)
        assert target.downside_pct == approx(0.0)

    def test_should_convert_to_dict(self):
        """Test PriceTarget to_dict conversion."""
        # Arrange
        target = PriceTarget(
            target_price=110.0,
            current_price=100.0,
            confidence=0.7,
            method="test",
            assumptions={"key": "value"},
        )

        # Act
        result = target.to_dict()

        # Assert
        assert result["target_price"] == approx(110.0)
        assert result["current_price"] == approx(100.0)
        assert result["upside_pct"] == pytest.approx(10.0, rel=1e-6)
        assert result["confidence"] == approx(0.7)
        assert result["method"] == "test"
        assert result["assumptions"] == {"key": "value"}

    def test_should_have_string_representation(self):
        """Test PriceTarget string representation."""
        # Arrange
        target = PriceTarget(
            target_price=110.0,
            current_price=100.0,
            confidence=0.7,
            method="test",
        )

        # Act
        result = repr(target)

        # Assert
        assert "PriceTarget" in result
        assert "110.00" in result
        assert "10.0%" in result
        assert "0.70" in result
        assert "test" in result


class TestCalculateDCFTarget:
    """Test suite for DCF valuation."""

    def test_should_calculate_dcf_target_with_valid_cash_flows(self):
        """Test DCF calculation with valid cash flow projections."""
        # Arrange
        cash_flows = [100, 110, 121, 133]
        discount_rate = 0.10
        terminal_growth = 0.03

        # Act
        target = calculate_dcf_target(
            cash_flows=cash_flows,
            discount_rate=discount_rate,
            terminal_growth=terminal_growth,
        )

        # Assert
        assert target.target_price > 0
        assert target.method == "dcf"
        assert target.confidence > 0.3
        assert target.confidence <= 0.7
        assert "discount_rate" in target.assumptions
        assert "terminal_growth" in target.assumptions
        assert target.assumptions["projection_years"] == 4

    def test_should_calculate_dcf_per_share_value(self):
        """Test DCF calculation with shares outstanding."""
        # Arrange
        cash_flows = [100, 110, 121, 133]
        discount_rate = 0.10
        terminal_growth = 0.03
        shares_outstanding = 1000
        current_price = 50.0

        # Act
        target = calculate_dcf_target(
            cash_flows=cash_flows,
            discount_rate=discount_rate,
            terminal_growth=terminal_growth,
            shares_outstanding=shares_outstanding,
            current_price=current_price,
        )

        # Assert
        assert target.target_price > 0
        assert target.current_price == approx(50.0)
        assert target.upside_pct != 0.0  # Should calculate upside
        assert target.assumptions["shares_outstanding"] == 1000

    def test_should_match_expected_dcf_calculation(self):
        """Test that DCF matches manual calculation."""
        # Arrange
        cash_flows = [100, 110]
        discount_rate = 0.10
        terminal_growth = 0.03

        # Act
        target = calculate_dcf_target(
            cash_flows=cash_flows,
            discount_rate=discount_rate,
            terminal_growth=terminal_growth,
        )

        # Assert
        # Manual calculation
        pv_cf1 = 100 / (1.10**1)  # 90.91
        pv_cf2 = 110 / (1.10**2)  # 90.91
        terminal_value = (110 * 1.03) / (0.10 - 0.03)  # 1621.43
        pv_terminal = terminal_value / (1.10**2)  # 1340.19
        expected_ev = pv_cf1 + pv_cf2 + pv_terminal  # ~1522.01

        assert target.target_price == pytest.approx(expected_ev, rel=1e-2)

    def test_should_decrease_confidence_with_longer_projections(self):
        """Test that confidence decreases with longer projection periods."""
        # Arrange
        short_cf = [100, 110, 121]
        long_cf = [100, 110, 121, 133, 146, 161, 177, 195]

        # Act
        short_target = calculate_dcf_target(short_cf, 0.10, 0.03)
        long_target = calculate_dcf_target(long_cf, 0.10, 0.03)

        # Assert
        assert long_target.confidence < short_target.confidence

    def test_should_return_zero_when_empty_cash_flows(self):
        """Test DCF with empty cash flows."""
        # Arrange
        cash_flows = []

        # Act
        target = calculate_dcf_target(cash_flows, 0.10, 0.03)

        # Assert
        assert target.target_price == approx(0.0)
        assert target.confidence == approx(0.0)

    def test_should_return_zero_when_discount_rate_less_than_growth(self):
        """Test DCF when discount rate <= terminal growth."""
        # Arrange
        cash_flows = [100, 110, 121]

        # Act
        target = calculate_dcf_target(
            cash_flows=cash_flows,
            discount_rate=0.03,
            terminal_growth=0.05,  # Growth > discount
        )

        # Assert
        assert target.target_price == approx(0.0)
        assert target.confidence == approx(0.0)

    def test_should_handle_negative_cash_flows(self):
        """Test DCF with negative cash flows."""
        # Arrange
        cash_flows = [-50, 100, 110, 121]

        # Act
        target = calculate_dcf_target(cash_flows, 0.10, 0.03)

        # Assert
        # Should still calculate, but value will be lower
        assert isinstance(target.target_price, float)
        assert target.method == "dcf"


class TestCalculatePETarget:
    """Test suite for P/E multiple valuation."""

    def test_should_calculate_pe_target_with_valid_inputs(self):
        """Test P/E target calculation with valid EPS and P/E ratio."""
        # Arrange
        eps = 5.50
        target_pe = 20.0

        # Act
        target = calculate_pe_target(
            earnings_per_share=eps,
            target_pe_ratio=target_pe,
        )

        # Assert
        assert target.target_price == pytest.approx(110.0, rel=1e-6)
        assert target.method == "pe_multiple"
        assert target.confidence > 0.3
        assert target.assumptions["earnings_per_share"] == approx(5.50)
        assert target.assumptions["target_pe_ratio"] == approx(20.0)

    def test_should_calculate_pe_target_with_current_price(self):
        """Test P/E target with current price for upside calculation."""
        # Arrange
        eps = 5.50
        target_pe = 20.0
        current_price = 95.0

        # Act
        target = calculate_pe_target(
            earnings_per_share=eps,
            target_pe_ratio=target_pe,
            current_price=current_price,
        )

        # Assert
        assert target.target_price == pytest.approx(110.0, rel=1e-6)
        assert target.current_price == approx(95.0)
        assert target.upside_pct > 0

    def test_should_adjust_confidence_based_on_sector_pe(self):
        """Test that confidence adjusts based on sector P/E comparison."""
        # Arrange
        eps = 5.50
        target_pe = 20.0
        sector_avg_pe = 18.5

        # Act
        target_close = calculate_pe_target(eps, target_pe, sector_avg_pe=sector_avg_pe)
        target_far = calculate_pe_target(eps, 30.0, sector_avg_pe=sector_avg_pe)

        # Assert
        # Target P/E close to sector average should have higher confidence
        assert target_close.confidence > target_far.confidence

    def test_should_match_expected_pe_calculation(self):
        """Test that P/E target matches manual calculation."""
        # Arrange
        eps = 5.50
        target_pe = 20.0

        # Act
        target = calculate_pe_target(eps, target_pe)

        # Assert
        expected_price = eps * target_pe  # 5.50 * 20.0 = 110.0
        assert target.target_price == pytest.approx(expected_price, rel=1e-6)

    def test_should_return_zero_when_negative_eps(self):
        """Test P/E target with negative EPS."""
        # Arrange
        eps = -2.50
        target_pe = 20.0

        # Act
        target = calculate_pe_target(eps, target_pe)

        # Assert
        assert target.target_price == approx(0.0)
        assert target.confidence == approx(0.0)

    def test_should_return_zero_when_zero_eps(self):
        """Test P/E target with zero EPS."""
        # Arrange
        eps = 0.0
        target_pe = 20.0

        # Act
        target = calculate_pe_target(eps, target_pe)

        # Assert
        assert target.target_price == approx(0.0)
        assert target.confidence == approx(0.0)

    def test_should_return_zero_when_negative_pe_ratio(self):
        """Test P/E target with negative P/E ratio."""
        # Arrange
        eps = 5.50
        target_pe = -10.0

        # Act
        target = calculate_pe_target(eps, target_pe)

        # Assert
        assert target.target_price == approx(0.0)
        assert target.confidence == approx(0.0)


class TestCalculateTechnicalTarget:
    """Test suite for technical analysis targets."""

    def test_should_calculate_fibonacci_target(self):
        """Test Fibonacci retracement/extension target."""
        # Arrange
        # Need at least 10 data points for technical analysis
        prices = pd.Series([100, 105, 110, 108, 115, 120, 118, 122, 125, 130, 128, 135])

        # Act
        target = calculate_technical_target(prices, method="fibonacci")

        # Assert
        assert target.target_price > 0
        assert target.method == "technical_fibonacci"
        assert target.confidence == pytest.approx(0.5, rel=1e-6)
        assert "swing_high" in target.assumptions
        assert "swing_low" in target.assumptions
        assert "fibonacci_level" in target.assumptions

    def test_should_calculate_ma_projection_target(self):
        """Test moving average projection target."""
        # Arrange
        # Create uptrending prices
        prices = pd.Series(range(100, 150))

        # Act
        target = calculate_technical_target(prices, method="ma_projection")

        # Assert
        assert target.target_price > 0
        assert target.method == "technical_ma_projection"
        assert target.confidence == pytest.approx(0.5, rel=1e-6)
        assert "ma_period" in target.assumptions
        assert "projection_periods" in target.assumptions

    def test_should_calculate_trend_channel_target(self):
        """Test trend channel projection target."""
        # Arrange
        prices = pd.Series([100, 105, 110, 108, 115, 120, 118, 122, 125, 130] * 3)

        # Act
        target = calculate_technical_target(prices, method="trend_channel")

        # Assert
        assert target.target_price > 0
        assert target.method == "technical_trend_channel"
        assert target.confidence == pytest.approx(0.5, rel=1e-6)
        assert "channel_period" in target.assumptions

    def test_should_use_last_price_when_current_price_not_provided(self):
        """Test that last price is used when current_price not provided."""
        # Arrange
        # Need at least 10 data points
        prices = pd.Series([100, 105, 110, 115, 120, 118, 122, 125, 123, 128, 130])

        # Act
        target = calculate_technical_target(prices, method="fibonacci")

        # Assert
        assert target.current_price == pytest.approx(130.0, rel=1e-6)

    def test_should_use_provided_current_price(self):
        """Test that provided current_price is used."""
        # Arrange
        prices = pd.Series([100, 105, 110, 115, 120])
        current_price = 118.0

        # Act
        target = calculate_technical_target(prices, method="fibonacci", current_price=current_price)

        # Assert
        assert target.current_price == approx(118.0)

    def test_should_return_zero_when_insufficient_data(self):
        """Test technical target with insufficient price data."""
        # Arrange
        prices = pd.Series([100, 105])  # Only 2 points

        # Act
        target = calculate_technical_target(prices, method="fibonacci")

        # Assert
        assert target.target_price == approx(0.0)
        assert target.confidence == approx(0.0)

    def test_should_return_current_price_when_unknown_method(self):
        """Test technical target with unknown method."""
        # Arrange
        # Need at least 10 data points
        prices = pd.Series([100, 105, 110, 115, 120, 118, 122, 125, 123, 128, 130])
        current_price = 130.0

        # Act
        target = calculate_technical_target(prices, method="unknown_method", current_price=current_price)

        # Assert
        assert target.target_price == current_price
        assert target.confidence == approx(0.0)


class TestCalculateSupportResistanceTargets:
    """Test suite for support/resistance target calculations."""

    def test_should_calculate_support_and_resistance_levels(self):
        """Test support and resistance level identification."""
        # Arrange
        # Price series with clear support at 95 and resistance at 125
        prices = pd.Series([100, 105, 110, 108, 95, 100, 105, 110, 115, 120, 125, 120, 115, 110, 105, 100, 105, 110, 115, 120])

        # Act
        targets = calculate_support_resistance_targets(prices)

        # Assert
        assert "resistance" in targets
        assert "support" in targets
        assert targets["resistance"].target_price > 0
        assert targets["support"].target_price > 0
        assert targets["resistance"].method == "support_resistance"
        assert targets["support"].method == "support_resistance"

    def test_should_have_resistance_above_current_price(self):
        """Test that resistance is above current price."""
        # Arrange
        # Need at least 20 data points for S/R
        prices = pd.Series([100, 105, 110, 108, 115, 120, 118, 122, 125, 120, 115, 118, 122, 119, 116, 120, 123, 121, 118, 115, 117, 120])
        current_price = 115.0

        # Act
        targets = calculate_support_resistance_targets(prices, current_price=current_price)

        # Assert
        assert targets["resistance"].target_price >= current_price

    def test_should_have_support_below_current_price(self):
        """Test that support is below current price."""
        # Arrange
        prices = pd.Series([100, 105, 110, 108, 115, 120, 118, 122, 125, 120, 115])
        current_price = 115.0

        # Act
        targets = calculate_support_resistance_targets(prices, current_price=current_price)

        # Assert
        assert targets["support"].target_price <= current_price

    def test_should_use_last_price_when_current_price_not_provided(self):
        """Test that last price is used when current_price not provided."""
        # Arrange
        # Need at least 20 data points
        prices = pd.Series([100, 105, 110, 115, 120, 118, 122, 125, 123, 128, 130, 127, 132, 129, 126, 130, 133, 131, 128, 125, 127, 130])

        # Act
        targets = calculate_support_resistance_targets(prices)

        # Assert
        assert targets["resistance"].current_price == pytest.approx(130.0, rel=1e-6)
        assert targets["support"].current_price == pytest.approx(130.0, rel=1e-6)

    def test_should_return_zero_when_insufficient_data(self):
        """Test S/R targets with insufficient price data."""
        # Arrange
        prices = pd.Series([100, 105, 110])  # Only 3 points

        # Act
        targets = calculate_support_resistance_targets(prices)

        # Assert
        assert targets["resistance"].target_price == approx(0.0)
        assert targets["support"].target_price == approx(0.0)
        assert targets["resistance"].confidence == approx(0.0)
        assert targets["support"].confidence == approx(0.0)

    def test_should_have_moderate_confidence(self):
        """Test that S/R targets have moderate confidence."""
        # Arrange
        prices = pd.Series([100, 105, 110, 108, 115, 120, 118, 122, 125, 120, 115] * 2)

        # Act
        targets = calculate_support_resistance_targets(prices)

        # Assert
        assert targets["resistance"].confidence == pytest.approx(0.55, rel=1e-6)
        assert targets["support"].confidence == pytest.approx(0.55, rel=1e-6)


class TestCalculateConsensusTarget:
    """Test suite for consensus target calculation."""

    def test_should_calculate_consensus_from_multiple_targets(self):
        """Test consensus calculation from multiple valuation methods."""
        # Arrange
        dcf_target = PriceTarget(120.0, 100.0, 0.7, "dcf")
        pe_target = PriceTarget(110.0, 100.0, 0.65, "pe_multiple")
        tech_target = PriceTarget(115.0, 100.0, 0.5, "technical")

        # Act
        consensus = calculate_consensus_target([dcf_target, pe_target, tech_target])

        # Assert
        assert consensus.target_price > 0
        assert consensus.method == "consensus"
        assert consensus.confidence > 0
        assert "methods" in consensus.assumptions
        assert len(consensus.assumptions["methods"]) == 3

    def test_should_weight_by_confidence_when_no_weights_provided(self):
        """Test that consensus uses confidence-based weights by default."""
        # Arrange
        high_conf_target = PriceTarget(120.0, 100.0, 0.9, "method1")
        low_conf_target = PriceTarget(80.0, 100.0, 0.1, "method2")

        # Act
        consensus = calculate_consensus_target([high_conf_target, low_conf_target])

        # Assert
        # Consensus should be closer to high confidence target
        assert consensus.target_price > 110.0
        assert consensus.target_price < 120.0

    def test_should_use_provided_weights(self):
        """Test consensus calculation with explicit weights."""
        # Arrange
        target1 = PriceTarget(120.0, 100.0, 0.7, "method1")
        target2 = PriceTarget(80.0, 100.0, 0.7, "method2")
        weights = [0.75, 0.25]  # 75% weight on first target

        # Act
        consensus = calculate_consensus_target([target1, target2], weights=weights)

        # Assert
        # Consensus should be closer to first target
        expected = (120.0 * 0.75) + (80.0 * 0.25)  # 110.0
        assert consensus.target_price == pytest.approx(expected, rel=1e-6)

    def test_should_filter_out_zero_targets(self):
        """Test that zero targets are filtered out."""
        # Arrange
        valid_target = PriceTarget(120.0, 100.0, 0.7, "valid")
        zero_target = PriceTarget(0.0, 100.0, 0.0, "invalid")

        # Act
        consensus = calculate_consensus_target([valid_target, zero_target])

        # Assert
        # Should only use valid target
        assert consensus.target_price == pytest.approx(120.0, rel=1e-6)

    def test_should_return_zero_when_no_valid_targets(self):
        """Test consensus with no valid targets."""
        # Arrange
        zero_target1 = PriceTarget(0.0, 100.0, 0.0, "invalid1")
        zero_target2 = PriceTarget(0.0, 100.0, 0.0, "invalid2")

        # Act
        consensus = calculate_consensus_target([zero_target1, zero_target2])

        # Assert
        assert consensus.target_price == approx(0.0)
        assert consensus.confidence == approx(0.0)

    def test_should_return_zero_when_empty_target_list(self):
        """Test consensus with empty target list."""
        # Arrange
        targets = []

        # Act
        consensus = calculate_consensus_target(targets)

        # Assert
        assert consensus.target_price == approx(0.0)
        assert consensus.confidence == approx(0.0)

    def test_should_calculate_weighted_average_confidence(self):
        """Test that consensus confidence is weighted average."""
        # Arrange
        target1 = PriceTarget(120.0, 100.0, 0.8, "method1")
        target2 = PriceTarget(110.0, 100.0, 0.6, "method2")
        weights = [0.5, 0.5]

        # Act
        consensus = calculate_consensus_target([target1, target2], weights=weights)

        # Assert
        expected_confidence = (0.8 * 0.5) + (0.6 * 0.5)  # 0.7
        assert consensus.confidence == pytest.approx(expected_confidence, rel=1e-6)


class TestPriceTargetConfidenceLevels:
    """Test suite for confidence level validation across all methods."""

    def test_dcf_confidence_should_be_reasonable(self):
        """Test that DCF confidence levels are in reasonable range."""
        # Arrange
        cash_flows = [100, 110, 121, 133]

        # Act
        target = calculate_dcf_target(cash_flows, 0.10, 0.03)

        # Assert
        assert 0.3 <= target.confidence <= 0.7

    def test_pe_confidence_should_be_reasonable(self):
        """Test that P/E confidence levels are in reasonable range."""
        # Arrange
        eps = 5.50
        target_pe = 20.0

        # Act
        target = calculate_pe_target(eps, target_pe)

        # Assert
        assert 0.3 <= target.confidence <= 0.7

    def test_technical_confidence_should_be_moderate(self):
        """Test that technical analysis confidence is moderate."""
        # Arrange
        prices = pd.Series(range(100, 150))

        # Act
        target = calculate_technical_target(prices, method="fibonacci")

        # Assert
        assert target.confidence == pytest.approx(0.5, rel=1e-6)

    def test_support_resistance_confidence_should_be_moderate(self):
        """Test that S/R confidence is moderate."""
        # Arrange
        prices = pd.Series([100, 105, 110, 108, 115, 120, 118, 122, 125, 120, 115] * 2)

        # Act
        targets = calculate_support_resistance_targets(prices)

        # Assert
        assert targets["resistance"].confidence == pytest.approx(0.55, rel=1e-6)
        assert targets["support"].confidence == pytest.approx(0.55, rel=1e-6)

    def test_consensus_confidence_should_reflect_inputs(self):
        """Test that consensus confidence reflects input confidences."""
        # Arrange
        high_conf = PriceTarget(120.0, 100.0, 0.9, "method1")
        low_conf = PriceTarget(110.0, 100.0, 0.3, "method2")

        # Act
        consensus = calculate_consensus_target([high_conf, low_conf])

        # Assert
        # Consensus confidence should be between input confidences
        assert 0.3 < consensus.confidence < 0.9


class TestPriceTargetEdgeCases:
    """Test suite for edge cases across all price target methods."""

    def test_should_handle_extreme_discount_rates(self):
        """Test DCF with extreme discount rates."""
        # Arrange
        cash_flows = [100, 110, 121]

        # Act
        high_rate = calculate_dcf_target(cash_flows, 0.50, 0.03)
        low_rate = calculate_dcf_target(cash_flows, 0.05, 0.03)

        # Assert
        # Higher discount rate should give lower valuation
        assert high_rate.target_price < low_rate.target_price

    def test_should_handle_extreme_pe_ratios(self):
        """Test P/E target with extreme P/E ratios."""
        # Arrange
        eps = 5.50

        # Act
        low_pe = calculate_pe_target(eps, 5.0)
        high_pe = calculate_pe_target(eps, 50.0)

        # Assert
        assert low_pe.target_price < high_pe.target_price
        assert low_pe.target_price == pytest.approx(27.5, rel=1e-6)
        assert high_pe.target_price == pytest.approx(275.0, rel=1e-6)

    def test_should_handle_volatile_price_series(self):
        """Test technical targets with highly volatile prices."""
        # Arrange
        # Create volatile price series with enough data points
        prices = pd.Series([100, 120, 90, 130, 85, 125, 95, 135, 80, 140, 75, 145, 70, 150, 65, 155, 60, 160, 55, 165, 50, 170, 45, 175])

        # Act
        fib_target = calculate_technical_target(prices, method="fibonacci")
        sr_targets = calculate_support_resistance_targets(prices)

        # Assert
        assert fib_target.target_price > 0
        assert sr_targets["resistance"].target_price > 0
        assert sr_targets["support"].target_price > 0

    def test_should_handle_flat_price_series(self):
        """Test technical targets with flat prices."""
        # Arrange
        prices = pd.Series([100.0] * 30)

        # Act
        target = calculate_technical_target(prices, method="fibonacci")

        # Assert
        # Should still calculate, though target may be close to current
        assert target.target_price > 0

    def test_should_handle_single_target_consensus(self):
        """Test consensus with single target."""
        # Arrange
        single_target = PriceTarget(120.0, 100.0, 0.7, "method")

        # Act
        consensus = calculate_consensus_target([single_target])

        # Assert
        assert consensus.target_price == pytest.approx(120.0, rel=1e-6)
        assert consensus.confidence == pytest.approx(0.7, rel=1e-6)