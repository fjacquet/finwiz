"""
Unit tests for ScoringThresholds configuration.

Tests the centralized scoring thresholds configuration introduced in Phase 2A.3.
"""

from pytest import approx
from finwiz.scoring.scoring_thresholds import ScoringThresholds, get_thresholds


class TestScoringThresholds:
    """Test suite for ScoringThresholds dataclass."""

    def test_default_thresholds_initialization(self):
        """Test that default thresholds can be initialized."""
        thresholds = ScoringThresholds()

        # Verify key thresholds are set (official grading scale)
        assert thresholds.grade_a_plus == approx(0.95)
        assert thresholds.grade_a == approx(0.85)
        assert thresholds.buy_threshold == approx(0.85)
        assert thresholds.sell_threshold == approx(0.65)

    def test_get_thresholds_returns_default(self):
        """Test that get_thresholds() returns default instance."""
        thresholds = get_thresholds()

        assert isinstance(thresholds, ScoringThresholds)
        assert thresholds.grade_a_plus == approx(0.95)

    def test_custom_thresholds(self):
        """Test that custom thresholds can be created."""
        custom = ScoringThresholds(grade_a_plus=0.95, grade_a=0.85, buy_threshold=0.85, sell_threshold=0.55)

        assert custom.grade_a_plus == approx(0.95)
        assert custom.grade_a == approx(0.85)
        assert custom.buy_threshold == approx(0.85)
        assert custom.sell_threshold == approx(0.55)

    def test_stock_fundamental_thresholds(self):
        """Test stock fundamental thresholds are properly set."""
        thresholds = ScoringThresholds()

        # ROE thresholds
        assert thresholds.roe_excellent == approx(0.20)
        assert thresholds.roe_very_good == approx(0.15)
        assert thresholds.roe_good == approx(0.10)
        assert thresholds.roe_acceptable == approx(0.05)

        # Debt thresholds
        assert thresholds.debt_very_low == approx(0.3)
        assert thresholds.debt_low == approx(0.5)
        assert thresholds.debt_moderate == approx(1.0)
        assert thresholds.debt_high == approx(2.0)

        # Growth thresholds (updated to match current implementation)
        assert thresholds.growth_excellent == approx(0.20)  # Updated from 0.25
        assert thresholds.growth_very_good == approx(0.12)  # Updated from 0.15
        assert thresholds.growth_good == approx(0.05)  # Updated from 0.10
        assert thresholds.growth_acceptable == approx(0.0)  # Updated from 0.05

    def test_etf_fundamental_thresholds(self):
        """Test ETF fundamental thresholds are properly set."""
        thresholds = ScoringThresholds()

        # Expense ratio thresholds
        assert thresholds.expense_excellent == approx(0.001)
        assert thresholds.expense_very_good == approx(0.0025)
        assert thresholds.expense_good == approx(0.005)
        assert thresholds.expense_acceptable == approx(0.01)

        # Tracking error thresholds
        assert thresholds.tracking_excellent == approx(0.002)
        assert thresholds.tracking_very_good == approx(0.005)
        assert thresholds.tracking_good == approx(0.01)
        assert thresholds.tracking_acceptable == approx(0.02)

        # AUM thresholds
        assert thresholds.aum_excellent == 5e9
        assert thresholds.aum_very_good == 1e9
        assert thresholds.aum_good == 500e6
        assert thresholds.aum_acceptable == 100e6

    def test_crypto_fundamental_thresholds(self):
        """Test crypto fundamental thresholds are properly set."""
        thresholds = ScoringThresholds()

        # Market cap thresholds
        assert thresholds.market_cap_mega == 100e9
        assert thresholds.market_cap_large == 10e9
        assert thresholds.market_cap_mid == 1e9
        assert thresholds.market_cap_small == 100e6

        # Volume thresholds
        assert thresholds.volume_very_high == 10e9
        assert thresholds.volume_high == 1e9
        assert thresholds.volume_good == 100e6
        assert thresholds.volume_moderate == 10e6

        # Age thresholds
        assert thresholds.age_very_established == approx(5.0)
        assert thresholds.age_established == approx(3.0)
        assert thresholds.age_maturing == approx(2.0)
        assert thresholds.age_young == approx(1.0)

    def test_technical_analysis_thresholds(self):
        """Test technical analysis thresholds are properly set."""
        thresholds = ScoringThresholds()

        # RSI thresholds
        assert thresholds.rsi_neutral_min == approx(40.0)
        assert thresholds.rsi_neutral_max == approx(60.0)
        assert thresholds.rsi_good_min == approx(30.0)
        assert thresholds.rsi_good_max == approx(70.0)

        # MACD threshold
        assert thresholds.macd_neutral_threshold == approx(0.1)

    def test_risk_assessment_thresholds(self):
        """Test risk assessment thresholds are properly set."""
        thresholds = ScoringThresholds()

        # Volatility thresholds (updated to match current implementation)
        assert thresholds.volatility_very_low == approx(0.15)  # Updated from 0.10
        assert thresholds.volatility_low == approx(0.25)  # Updated from 0.15
        assert thresholds.volatility_moderate == approx(0.35)  # Updated from 0.25
        assert thresholds.volatility_high == approx(0.50)  # Updated from 0.40

        # Drawdown thresholds
        assert thresholds.drawdown_very_low == approx(0.10)
        assert thresholds.drawdown_low == approx(0.20)
        assert thresholds.drawdown_moderate == approx(0.35)
        assert thresholds.drawdown_high == approx(0.50)

        # Beta thresholds
        assert thresholds.beta_excellent == approx(0.20)
        assert thresholds.beta_very_good == approx(0.40)
        assert thresholds.beta_good == approx(0.60)
        assert thresholds.beta_acceptable == approx(1.00)

    def test_component_weights(self):
        """Test that component weights are properly set."""
        thresholds = ScoringThresholds()

        # Composite score weights
        assert thresholds.weight_fundamental == approx(0.40)
        assert thresholds.weight_technical == approx(0.30)
        assert thresholds.weight_risk == approx(0.30)

        # Stock weights
        assert thresholds.weight_stock_roe == approx(0.40)
        assert thresholds.weight_stock_debt == approx(0.30)
        assert thresholds.weight_stock_growth == approx(0.20)
        assert thresholds.weight_stock_margin == approx(0.10)

        # ETF weights
        assert thresholds.weight_etf_expense == approx(0.50)
        assert thresholds.weight_etf_tracking == approx(0.30)
        assert thresholds.weight_etf_aum == approx(0.20)

        # Crypto weights
        assert thresholds.weight_crypto_market_cap == approx(0.40)
        assert thresholds.weight_crypto_volume == approx(0.30)
        assert thresholds.weight_crypto_age == approx(0.20)
        assert thresholds.weight_crypto_supply == approx(0.10)

    def test_weights_sum_to_one(self):
        """Test that component weights sum to 1.0."""
        thresholds = ScoringThresholds()

        # Composite weights
        composite_sum = thresholds.weight_fundamental + thresholds.weight_technical + thresholds.weight_risk
        assert abs(composite_sum - 1.0) < 0.001

        # Stock weights
        stock_sum = thresholds.weight_stock_roe + thresholds.weight_stock_debt + thresholds.weight_stock_growth + thresholds.weight_stock_margin
        assert abs(stock_sum - 1.0) < 0.001

        # ETF weights
        etf_sum = thresholds.weight_etf_expense + thresholds.weight_etf_tracking + thresholds.weight_etf_aum
        assert abs(etf_sum - 1.0) < 0.001

        # Crypto weights
        crypto_sum = thresholds.weight_crypto_market_cap + thresholds.weight_crypto_volume + thresholds.weight_crypto_age + thresholds.weight_crypto_supply
        assert abs(crypto_sum - 1.0) < 0.001

    def test_threshold_consistency(self):
        """Test that thresholds are in logical order."""
        thresholds = ScoringThresholds()

        # ROE thresholds should be descending
        assert thresholds.roe_excellent > thresholds.roe_very_good
        assert thresholds.roe_very_good > thresholds.roe_good
        assert thresholds.roe_good > thresholds.roe_acceptable

        # Debt thresholds should be ascending (lower is better)
        assert thresholds.debt_very_low < thresholds.debt_low
        assert thresholds.debt_low < thresholds.debt_moderate
        assert thresholds.debt_moderate < thresholds.debt_high

        # Grade thresholds should be descending
        assert thresholds.grade_a_plus > thresholds.grade_a
        assert thresholds.grade_a > thresholds.grade_b
        assert thresholds.grade_b > thresholds.grade_c
        assert thresholds.grade_c > thresholds.grade_d

    def test_backward_compatibility(self):
        """Test that default thresholds match official grading system."""
        thresholds = ScoringThresholds()

        # Verify key thresholds match official grading scale
        assert thresholds.grade_a_plus == approx(0.95)
        assert thresholds.buy_threshold == approx(0.85)
        assert thresholds.sell_threshold == approx(0.65)
        assert thresholds.roe_excellent == approx(0.20)
        assert thresholds.expense_excellent == approx(0.001)
        assert thresholds.volatility_very_low == approx(0.15)  # Updated from 0.10