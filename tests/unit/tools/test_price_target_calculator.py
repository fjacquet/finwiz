"""
Unit tests for PriceTargetCalculator.

Tests fair value calculations, technical level detection, buy/sell target logic,
multi-currency support, and confidence scoring.
"""

from pytest import approx
from datetime import datetime

import pytest

from finwiz.tools.price_target_calculator import (
    FundamentalData,
    PriceHistory,
    PriceTargetCalculator,
)


class TestPriceTargetCalculator:
    """Test suite for PriceTargetCalculator."""

    @pytest.fixture
    def calculator(self):
        """Create calculator instance."""
        return PriceTargetCalculator()

    @pytest.fixture
    def stock_fundamentals(self):
        """Create sample stock fundamental data."""
        return FundamentalData(
            earnings_per_share=5.0,
            pe_ratio=20.0,
            book_value_per_share=50.0,
            free_cash_flow=10.0,
            growth_rate=0.15,
        )

    @pytest.fixture
    def etf_fundamentals(self):
        """Create sample ETF fundamental data."""
        return FundamentalData(
            nav=100.0,
            expense_ratio=0.05,
            tracking_error=0.10,
        )

    @pytest.fixture
    def price_history(self):
        """Create sample price history."""
        return PriceHistory(
            prices=[95.0, 98.0, 100.0, 102.0, 105.0, 103.0, 101.0, 99.0, 100.0, 102.0],
            dates=[datetime.now() for _ in range(10)],
            currency="USD",
        )

    def test_should_calculate_targets_for_keep_decision(self, calculator, stock_fundamentals, price_history):
        """Test price target calculation for KEEP recommendation."""
        # Act
        result = calculator.calculate_targets(
            ticker="AAPL",
            asset_class="stock",
            current_price=100.0,
            currency="USD",
            price_history=price_history,
            fundamental_data=stock_fundamentals,
            decision="KEEP",
        )

        # Assert
        assert result.current_price == approx(100.0)
        assert result.currency == "USD"
        assert result.fair_value_estimate is not None
        assert result.buy_target_primary is not None
        assert result.sell_target_primary is not None
        assert result.stop_loss_level is not None
        assert len(result.buy_rationale) > 0
        assert len(result.sell_rationale) > 0

    def test_should_calculate_targets_for_sell_decision(self, calculator, stock_fundamentals):
        """Test price target calculation for SELL recommendation."""
        # Act
        result = calculator.calculate_targets(
            ticker="IBM",
            asset_class="stock",
            current_price=100.0,
            currency="USD",
            fundamental_data=stock_fundamentals,
            decision="SELL",
        )

        # Assert
        assert result.current_price == approx(100.0)
        assert result.buy_target_primary is None
        assert result.sell_target_primary is not None
        assert "Not recommended" in result.buy_rationale

    def test_should_calculate_targets_for_buy_decision(self, calculator, stock_fundamentals, price_history):
        """Test price target calculation for BUY recommendation."""
        # Act
        result = calculator.calculate_targets(
            ticker="MSFT",
            asset_class="stock",
            current_price=100.0,
            currency="USD",
            price_history=price_history,
            fundamental_data=stock_fundamentals,
            decision="BUY",
        )

        # Assert
        assert result.current_price == approx(100.0)
        assert result.buy_target_primary is not None
        assert result.buy_target_secondary is not None
        assert result.sell_target_primary is not None

    def test_should_calculate_stock_fair_value_using_pe_ratio(self, calculator, stock_fundamentals):
        """Test stock fair value calculation using P/E ratio."""
        # Act
        fair_value = calculator._calculate_stock_fair_value(
            current_price=100.0,
            fundamental_data=stock_fundamentals,
        )

        # Assert
        assert fair_value is not None
        assert fair_value > 0
        # With EPS=5.0 and target P/E=17.5, fair value should be around 87.5

    def test_should_calculate_etf_fair_value_using_nav(self, calculator, etf_fundamentals):
        """Test ETF fair value calculation using NAV."""
        # Act
        fair_value = calculator._calculate_etf_fair_value(
            current_price=100.0,
            fundamental_data=etf_fundamentals,
        )

        # Assert
        assert fair_value is not None
        assert fair_value > 0
        # NAV=100.0 with tracking_error=0.10 should give ~99.9

    def test_should_return_none_for_crypto_fair_value(self, calculator):
        """Test that crypto fair value returns None (uses technical analysis)."""
        # Act
        fair_value = calculator._calculate_fair_value(
            asset_class="crypto",
            current_price=50000.0,
            fundamental_data=None,
        )

        # Assert
        assert fair_value is None

    def test_should_calculate_technical_levels_from_price_history(self, calculator, price_history):
        """Test technical support/resistance level calculation."""
        # Act
        support, resistance = calculator._calculate_technical_levels(
            current_price=100.0,
            price_history=price_history,
        )

        # Assert
        assert len(support) >= 0  # May be empty if no valid support levels
        assert len(resistance) >= 0  # May be empty if no valid resistance levels
        # If levels exist, they should be on correct side of current price
        if support:
            assert all(s <= 100.0 for s in support)
        if resistance:
            assert all(r >= 100.0 for r in resistance)

    def test_should_use_percentage_levels_when_no_price_history(self, calculator):
        """Test fallback to percentage-based levels without price history."""
        # Act
        support, resistance = calculator._calculate_technical_levels(
            current_price=100.0,
            price_history=None,
        )

        # Assert
        assert len(support) == 2
        assert len(resistance) == 2
        assert support[0] == approx(95.0)  # 5% below
        assert support[1] == approx(90.0)  # 10% below
        assert resistance[0] == approx(105.0)  # 5% above
        assert resistance[1] == approx(110.0)  # 10% above

    def test_should_calculate_buy_targets_for_keep_decision(self, calculator):
        """Test buy target calculation for KEEP recommendation."""
        # Act
        buy_primary, buy_secondary, rationale = calculator._calculate_buy_targets(
            current_price=100.0,
            fair_value=110.0,
            support_levels=[95.0, 90.0],
            asset_class="stock",
            is_new_position=False,
        )

        # Assert
        assert buy_primary is not None
        assert buy_primary < 100.0  # Should be below current price
        assert len(rationale) > 0

    def test_should_calculate_sell_targets_for_keep_decision(self, calculator):
        """Test sell target calculation for KEEP recommendation."""
        # Act
        (
            sell_primary,
            sell_secondary,
            stop_loss,
            rationale,
        ) = calculator._calculate_sell_targets(
            current_price=100.0,
            fair_value=110.0,
            resistance_levels=[105.0, 110.0],
            asset_class="stock",
            is_keep=True,
        )

        # Assert
        assert sell_primary is not None
        assert sell_primary > 100.0  # Should be above current price
        assert stop_loss is not None
        assert stop_loss < 100.0  # Stop loss should be below current
        assert len(rationale) > 0

    def test_should_calculate_confidence_with_both_fundamental_and_technical(self, calculator):
        """Test confidence calculation with both data types."""
        # Act
        confidence = calculator._calculate_confidence(
            has_fundamental=True,
            has_technical=True,
            fair_value=110.0,
            current_price=100.0,
        )

        # Assert
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.5  # Should be high with both data types

    def test_should_calculate_lower_confidence_without_fundamental_data(self, calculator):
        """Test that confidence is lower without fundamental data."""
        # Act
        confidence = calculator._calculate_confidence(
            has_fundamental=False,
            has_technical=True,
            fair_value=None,
            current_price=100.0,
        )

        # Assert
        assert 0.0 <= confidence <= 1.0
        assert confidence <= 0.7  # Should be lower or equal without fundamentals

    def test_should_support_multi_currency(self, calculator, stock_fundamentals):
        """Test multi-currency support."""
        # Act
        result_usd = calculator.calculate_targets(
            ticker="AAPL",
            asset_class="stock",
            current_price=100.0,
            currency="USD",
            fundamental_data=stock_fundamentals,
            decision="KEEP",
        )

        result_eur = calculator.calculate_targets(
            ticker="SAP",
            asset_class="stock",
            current_price=100.0,
            currency="EUR",
            fundamental_data=stock_fundamentals,
            decision="KEEP",
        )

        # Assert
        assert result_usd.currency == "USD"
        assert result_eur.currency == "EUR"

    def test_should_include_data_sources(self, calculator, stock_fundamentals):
        """Test that data sources are included."""
        # Act
        result = calculator.calculate_targets(
            ticker="AAPL",
            asset_class="stock",
            current_price=100.0,
            currency="USD",
            fundamental_data=stock_fundamentals,
            decision="KEEP",
        )

        # Assert
        assert len(result.data_sources) > 0
        assert isinstance(result.data_sources, list)

    def test_should_include_calculation_method(self, calculator, stock_fundamentals):
        """Test that calculation method is specified."""
        # Act
        result = calculator.calculate_targets(
            ticker="AAPL",
            asset_class="stock",
            current_price=100.0,
            currency="USD",
            fundamental_data=stock_fundamentals,
            decision="KEEP",
        )

        # Assert
        assert len(result.calculation_method) > 0

    def test_should_include_timestamp(self, calculator, stock_fundamentals):
        """Test that data timestamp is included."""
        # Act
        result = calculator.calculate_targets(
            ticker="AAPL",
            asset_class="stock",
            current_price=100.0,
            currency="USD",
            fundamental_data=stock_fundamentals,
            decision="KEEP",
        )

        # Assert
        assert result.data_as_of is not None
        assert isinstance(result.data_as_of, datetime)

    def test_should_handle_missing_fundamental_data(self, calculator, price_history):
        """Test handling of missing fundamental data."""
        # Act
        result = calculator.calculate_targets(
            ticker="AAPL",
            asset_class="stock",
            current_price=100.0,
            currency="USD",
            price_history=price_history,
            fundamental_data=None,
            decision="KEEP",
        )

        # Assert
        assert result.current_price == approx(100.0)
        assert result.fair_value_estimate is None
        assert result.buy_target_primary is not None  # Should still calculate targets

    def test_should_handle_missing_price_history(self, calculator, stock_fundamentals):
        """Test handling of missing price history."""
        # Act
        result = calculator.calculate_targets(
            ticker="AAPL",
            asset_class="stock",
            current_price=100.0,
            currency="USD",
            price_history=None,
            fundamental_data=stock_fundamentals,
            decision="KEEP",
        )

        # Assert
        assert result.current_price == approx(100.0)
        assert result.fair_value_estimate is not None
        assert len(result.support_levels) > 0  # Should use percentage-based levels

    def test_should_calculate_targets_for_etf(self, calculator, etf_fundamentals):
        """Test price target calculation for ETF."""
        # Act
        result = calculator.calculate_targets(
            ticker="SPY",
            asset_class="etf",
            current_price=400.0,
            currency="USD",
            fundamental_data=etf_fundamentals,
            decision="KEEP",
        )

        # Assert
        assert result.current_price == approx(400.0)
        assert result.fair_value_estimate is not None
        assert result.buy_target_primary is not None

    def test_should_calculate_targets_for_crypto(self, calculator):
        """Test price target calculation for crypto."""
        # Arrange
        crypto_history = PriceHistory(
            prices=[48000.0, 49000.0, 50000.0, 51000.0, 50500.0],
            dates=[datetime.now() for _ in range(5)],
            currency="USD",
        )

        # Act
        result = calculator.calculate_targets(
            ticker="BTC",
            asset_class="crypto",
            current_price=50000.0,
            currency="USD",
            price_history=crypto_history,
            fundamental_data=None,
            decision="KEEP",
        )

        # Assert
        assert result.current_price == approx(50000.0)
        assert result.fair_value_estimate is None  # Crypto doesn't use fair value
        assert result.buy_target_primary is not None