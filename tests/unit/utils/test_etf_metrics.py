"""
Unit tests for ETF metrics calculation module.

Tests cover:
- Tracking error calculations
- Correlation calculations
- Expense impact calculations
- Liquidity scoring
- Concentration risk calculations
- ETF efficiency score calculations
- Edge cases (empty data, zero values, extreme values)
"""

from pytest import approx
import numpy as np
import pandas as pd
import pytest

from finwiz.utils.etf_metrics import (
    calculate_concentration_risk,
    calculate_correlation,
    calculate_etf_efficiency_score,
    calculate_expense_impact,
    calculate_liquidity_score,
    calculate_tracking_error,
)


class TestCalculateTrackingError:
    """Test suite for tracking error calculation."""

    def test_should_calculate_tracking_error_when_valid_returns(self):
        """Test tracking error calculation with valid return data."""
        # Arrange
        etf_returns = pd.Series([0.01, 0.02, -0.01, 0.015, 0.02])
        benchmark_returns = pd.Series([0.011, 0.019, -0.009, 0.014, 0.021])

        # Act
        te = calculate_tracking_error(etf_returns, benchmark_returns, annualize=False)

        # Assert
        assert te > 0
        assert isinstance(te, float)
        # Tracking error should be small for closely tracking ETF
        assert te < 0.01  # Less than 1% for this example

    def test_should_annualize_tracking_error_when_annualize_true(self):
        """Test annualized tracking error calculation."""
        # Arrange
        etf_returns = pd.Series([0.01, 0.02, -0.01, 0.015, 0.02])
        benchmark_returns = pd.Series([0.011, 0.019, -0.009, 0.014, 0.021])

        # Act
        te_annual = calculate_tracking_error(etf_returns, benchmark_returns, annualize=True)
        te_daily = calculate_tracking_error(etf_returns, benchmark_returns, annualize=False)

        # Assert
        # Annualized should be daily * sqrt(252)
        expected_annual = te_daily * np.sqrt(252)
        assert te_annual == pytest.approx(expected_annual, rel=1e-6)

    def test_should_return_zero_when_perfect_tracking(self):
        """Test tracking error when ETF perfectly tracks benchmark."""
        # Arrange
        returns = pd.Series([0.01, 0.02, -0.01, 0.015, 0.02])

        # Act
        te = calculate_tracking_error(returns, returns, annualize=False)

        # Assert
        assert te == pytest.approx(0.0, abs=1e-10)

    def test_should_return_zero_when_empty_series(self):
        """Test tracking error with empty series."""
        # Arrange
        etf_returns = pd.Series([], dtype=float)
        benchmark_returns = pd.Series([], dtype=float)

        # Act
        te = calculate_tracking_error(etf_returns, benchmark_returns)

        # Assert
        assert te == approx(0.0)

    def test_should_return_zero_when_insufficient_data(self):
        """Test tracking error with single data point."""
        # Arrange
        etf_returns = pd.Series([0.01])
        benchmark_returns = pd.Series([0.011])

        # Act
        te = calculate_tracking_error(etf_returns, benchmark_returns)

        # Assert
        assert te == approx(0.0)

    def test_should_handle_misaligned_indices(self):
        """Test tracking error with misaligned series indices."""
        # Arrange
        dates1 = pd.date_range("2023-01-01", periods=5)
        dates2 = pd.date_range("2023-01-02", periods=5)
        etf_returns = pd.Series([0.01, 0.02, -0.01, 0.015, 0.02], index=dates1)
        benchmark_returns = pd.Series([0.011, 0.019, -0.009, 0.014, 0.021], index=dates2)

        # Act
        te = calculate_tracking_error(etf_returns, benchmark_returns)

        # Assert
        # Should handle alignment and calculate on overlapping dates
        assert isinstance(te, float)
        assert te >= 0


class TestCalculateCorrelation:
    """Test suite for correlation calculation."""

    def test_should_calculate_correlation_when_valid_returns(self):
        """Test correlation calculation with valid return data."""
        # Arrange
        etf_returns = pd.Series([0.01, 0.02, -0.01, 0.015, 0.02])
        benchmark_returns = pd.Series([0.011, 0.019, -0.009, 0.014, 0.021])

        # Act
        corr = calculate_correlation(etf_returns, benchmark_returns)

        # Assert
        assert isinstance(corr, float)
        assert -1.0 <= corr <= 1.0
        # Should have high positive correlation for tracking ETF
        assert corr > 0.9

    def test_should_return_one_when_perfect_correlation(self):
        """Test correlation when ETF perfectly correlates with benchmark."""
        # Arrange
        returns = pd.Series([0.01, 0.02, -0.01, 0.015, 0.02])

        # Act
        corr = calculate_correlation(returns, returns)

        # Assert
        assert corr == pytest.approx(1.0, rel=1e-6)

    def test_should_return_negative_when_inverse_correlation(self):
        """Test correlation with inverse relationship."""
        # Arrange
        etf_returns = pd.Series([0.01, 0.02, -0.01, 0.015, 0.02])
        benchmark_returns = pd.Series([-0.01, -0.02, 0.01, -0.015, -0.02])

        # Act
        corr = calculate_correlation(etf_returns, benchmark_returns)

        # Assert
        assert corr < 0  # Negative correlation

    def test_should_return_zero_when_empty_series(self):
        """Test correlation with empty series."""
        # Arrange
        etf_returns = pd.Series([], dtype=float)
        benchmark_returns = pd.Series([], dtype=float)

        # Act
        corr = calculate_correlation(etf_returns, benchmark_returns)

        # Assert
        assert corr == approx(0.0)

    def test_should_return_zero_when_insufficient_data(self):
        """Test correlation with single data point."""
        # Arrange
        etf_returns = pd.Series([0.01])
        benchmark_returns = pd.Series([0.011])

        # Act
        corr = calculate_correlation(etf_returns, benchmark_returns)

        # Assert
        assert corr == approx(0.0)

    def test_should_handle_misaligned_indices(self):
        """Test correlation with misaligned series indices."""
        # Arrange
        dates1 = pd.date_range("2023-01-01", periods=5)
        dates2 = pd.date_range("2023-01-02", periods=5)
        etf_returns = pd.Series([0.01, 0.02, -0.01, 0.015, 0.02], index=dates1)
        benchmark_returns = pd.Series([0.011, 0.019, -0.009, 0.014, 0.021], index=dates2)

        # Act
        corr = calculate_correlation(etf_returns, benchmark_returns)

        # Assert
        # Should handle alignment and calculate on overlapping dates
        assert isinstance(corr, float)
        assert -1.0 <= corr <= 1.0


class TestCalculateExpenseImpact:
    """Test suite for expense impact calculation."""

    def test_should_calculate_expense_impact_when_valid_data(self):
        """Test expense impact calculation with valid data."""
        # Arrange
        returns = pd.Series([0.08, 0.10, 0.12, 0.09, 0.11])
        expense_ratio = 0.0050  # 0.50%

        # Act
        impact = calculate_expense_impact(returns, expense_ratio, years=10)

        # Assert
        assert isinstance(impact, dict)
        assert "annual_drag" in impact
        assert "cumulative_cost" in impact
        assert "return_reduction_pct" in impact
        assert impact["annual_drag"] == expense_ratio
        assert impact["cumulative_cost"] > 0
        assert impact["return_reduction_pct"] > 0

    def test_should_show_higher_cost_for_higher_expense_ratio(self):
        """Test that higher expense ratios result in higher costs."""
        # Arrange
        returns = pd.Series([0.08, 0.10, 0.12, 0.09, 0.11])
        low_expense = 0.0020  # 0.20%
        high_expense = 0.0100  # 1.00%

        # Act
        impact_low = calculate_expense_impact(returns, low_expense, years=10)
        impact_high = calculate_expense_impact(returns, high_expense, years=10)

        # Assert
        assert impact_high["cumulative_cost"] > impact_low["cumulative_cost"]
        assert impact_high["return_reduction_pct"] > impact_low["return_reduction_pct"]

    def test_should_show_higher_cost_for_longer_periods(self):
        """Test that longer time periods result in higher cumulative costs."""
        # Arrange
        returns = pd.Series([0.08, 0.10, 0.12, 0.09, 0.11])
        expense_ratio = 0.0050

        # Act
        impact_5yr = calculate_expense_impact(returns, expense_ratio, years=5)
        impact_20yr = calculate_expense_impact(returns, expense_ratio, years=20)

        # Assert
        assert impact_20yr["cumulative_cost"] > impact_5yr["cumulative_cost"]

    def test_should_return_zero_impact_when_zero_expense_ratio(self):
        """Test expense impact with zero expense ratio."""
        # Arrange
        returns = pd.Series([0.08, 0.10, 0.12, 0.09, 0.11])

        # Act
        impact = calculate_expense_impact(returns, expense_ratio=0.0, years=10)

        # Assert
        assert impact["annual_drag"] == approx(0.0)
        assert impact["cumulative_cost"] == pytest.approx(0.0, abs=1e-10)

    def test_should_return_zero_when_empty_returns(self):
        """Test expense impact with empty returns series."""
        # Arrange
        returns = pd.Series([], dtype=float)

        # Act
        impact = calculate_expense_impact(returns, expense_ratio=0.0050, years=10)

        # Assert
        assert impact["annual_drag"] == approx(0.0)
        assert impact["cumulative_cost"] == approx(0.0)


class TestCalculateLiquidityScore:
    """Test suite for liquidity score calculation."""

    def test_should_calculate_liquidity_score_when_valid_data(self):
        """Test liquidity score calculation with valid data."""
        # Arrange
        avg_daily_volume = 5_000_000
        bid_ask_spread_pct = 0.05
        market_cap = 10_000_000_000

        # Act
        score = calculate_liquidity_score(avg_daily_volume, bid_ask_spread_pct, market_cap)

        # Assert
        assert isinstance(score, dict)
        assert "liquidity_score" in score
        assert "volume_score" in score
        assert "spread_score" in score
        assert "size_score" in score
        assert "liquidity_rating" in score
        assert 0 <= score["liquidity_score"] <= 100
        assert score["liquidity_rating"] in ["Excellent", "Good", "Fair", "Poor"]

    def test_should_give_excellent_rating_for_highly_liquid_etf(self):
        """Test liquidity score for highly liquid ETF."""
        # Arrange
        avg_daily_volume = 10_000_000  # High volume
        bid_ask_spread_pct = 0.03  # Tight spread
        market_cap = 20_000_000_000  # Large cap

        # Act
        score = calculate_liquidity_score(avg_daily_volume, bid_ask_spread_pct, market_cap)

        # Assert
        assert score["liquidity_score"] >= 80
        assert score["liquidity_rating"] == "Excellent"

    def test_should_give_poor_rating_for_illiquid_etf(self):
        """Test liquidity score for illiquid ETF."""
        # Arrange
        avg_daily_volume = 50_000  # Low volume
        bid_ask_spread_pct = 0.80  # Wide spread
        market_cap = 50_000_000  # Small cap

        # Act
        score = calculate_liquidity_score(avg_daily_volume, bid_ask_spread_pct, market_cap)

        # Assert
        assert score["liquidity_score"] < 40
        assert score["liquidity_rating"] == "Poor"

    def test_should_weight_volume_and_spread_more_than_size(self):
        """Test that volume and spread have higher weight than market cap."""
        # Arrange - Excellent volume and spread, poor size
        score1 = calculate_liquidity_score(
            avg_daily_volume=10_000_000,
            bid_ask_spread_pct=0.03,
            market_cap=50_000_000,  # Small cap
        )

        # Arrange - Poor volume and spread, excellent size
        score2 = calculate_liquidity_score(
            avg_daily_volume=50_000,
            bid_ask_spread_pct=0.80,
            market_cap=20_000_000_000,  # Large cap
        )

        # Act & Assert
        # Good volume/spread should score higher than good size alone
        assert score1["liquidity_score"] > score2["liquidity_score"]

    def test_should_handle_zero_values(self):
        """Test liquidity score with zero values."""
        # Arrange
        avg_daily_volume = 0
        bid_ask_spread_pct = 0
        market_cap = 0

        # Act
        score = calculate_liquidity_score(avg_daily_volume, bid_ask_spread_pct, market_cap)

        # Assert
        assert isinstance(score, dict)
        assert score["liquidity_score"] >= 0


class TestCalculateConcentrationRisk:
    """Test suite for concentration risk calculation."""

    def test_should_calculate_concentration_risk_when_valid_holdings(self):
        """Test concentration risk calculation with valid holdings."""
        # Arrange
        holdings = [
            {"ticker": "AAPL", "weight": 0.07},
            {"ticker": "MSFT", "weight": 0.06},
            {"ticker": "GOOGL", "weight": 0.04},
            {"ticker": "AMZN", "weight": 0.03},
            {"ticker": "NVDA", "weight": 0.03},
            {"ticker": "META", "weight": 0.02},
            {"ticker": "TSLA", "weight": 0.02},
            {"ticker": "BRK.B", "weight": 0.02},
            {"ticker": "JPM", "weight": 0.015},
            {"ticker": "V", "weight": 0.015},
        ]

        # Act
        risk = calculate_concentration_risk(holdings, top_n=10)

        # Assert
        assert isinstance(risk, dict)
        assert "top_n_concentration" in risk
        assert "herfindahl_index" in risk
        assert "effective_n_holdings" in risk
        assert "concentration_rating" in risk
        assert 0 <= risk["top_n_concentration"] <= 1.0
        assert risk["herfindahl_index"] > 0
        assert risk["effective_n_holdings"] > 0

    def test_should_give_low_rating_for_diversified_holdings(self):
        """Test concentration risk for well-diversified ETF."""
        # Arrange - Many small holdings
        holdings = [{"ticker": f"STOCK{i}", "weight": 0.01} for i in range(100)]

        # Act
        risk = calculate_concentration_risk(holdings, top_n=10)

        # Assert
        assert risk["top_n_concentration"] < 0.25
        assert risk["concentration_rating"] == "Low"

    def test_should_give_high_rating_for_concentrated_holdings(self):
        """Test concentration risk for concentrated ETF."""
        # Arrange - Few large holdings
        holdings = [
            {"ticker": "AAPL", "weight": 0.30},
            {"ticker": "MSFT", "weight": 0.25},
            {"ticker": "GOOGL", "weight": 0.20},
            {"ticker": "AMZN", "weight": 0.15},
            {"ticker": "NVDA", "weight": 0.10},
        ]

        # Act
        risk = calculate_concentration_risk(holdings, top_n=5)

        # Assert
        assert risk["top_n_concentration"] >= 0.60
        assert risk["concentration_rating"] in ["High", "Very High"]

    def test_should_calculate_herfindahl_index_correctly(self):
        """Test that Herfindahl index is calculated correctly."""
        # Arrange
        holdings = [
            {"ticker": "A", "weight": 0.50},
            {"ticker": "B", "weight": 0.30},
            {"ticker": "C", "weight": 0.20},
        ]

        # Act
        risk = calculate_concentration_risk(holdings)

        # Assert
        # HHI = 0.50^2 + 0.30^2 + 0.20^2 = 0.25 + 0.09 + 0.04 = 0.38
        expected_hhi = 0.50**2 + 0.30**2 + 0.20**2
        assert risk["herfindahl_index"] == pytest.approx(expected_hhi, rel=1e-6)

    def test_should_calculate_effective_n_holdings_correctly(self):
        """Test that effective number of holdings is calculated correctly."""
        # Arrange
        holdings = [
            {"ticker": "A", "weight": 0.50},
            {"ticker": "B", "weight": 0.30},
            {"ticker": "C", "weight": 0.20},
        ]

        # Act
        risk = calculate_concentration_risk(holdings)

        # Assert
        # Effective N = 1 / HHI
        expected_hhi = 0.50**2 + 0.30**2 + 0.20**2
        expected_effective_n = 1.0 / expected_hhi
        assert risk["effective_n_holdings"] == pytest.approx(expected_effective_n, rel=1e-6)

    def test_should_return_zero_when_empty_holdings(self):
        """Test concentration risk with empty holdings list."""
        # Arrange
        holdings = []

        # Act
        risk = calculate_concentration_risk(holdings)

        # Assert
        assert risk["top_n_concentration"] == approx(0.0)
        assert risk["herfindahl_index"] == approx(0.0)
        assert risk["effective_n_holdings"] == approx(0.0)
        assert risk["concentration_rating"] == "Unknown"

    def test_should_handle_holdings_without_weight_key(self):
        """Test concentration risk with holdings missing weight key."""
        # Arrange
        holdings = [
            {"ticker": "AAPL"},  # Missing weight
            {"ticker": "MSFT", "weight": 0.05},
        ]

        # Act
        risk = calculate_concentration_risk(holdings)

        # Assert
        # Should handle gracefully, treating missing weights as 0
        assert isinstance(risk, dict)

    def test_should_filter_zero_weights(self):
        """Test that zero weights are filtered out."""
        # Arrange
        holdings = [
            {"ticker": "AAPL", "weight": 0.50},
            {"ticker": "MSFT", "weight": 0.30},
            {"ticker": "GOOGL", "weight": 0.20},
            {"ticker": "ZERO", "weight": 0.0},  # Should be filtered
        ]

        # Act
        risk = calculate_concentration_risk(holdings)

        # Assert
        # Total holdings should be 3, not 4
        assert risk["total_holdings"] == 3


class TestCalculateETFEfficiencyScore:
    """Test suite for ETF efficiency score calculation."""

    def test_should_calculate_efficiency_score_when_valid_data(self):
        """Test efficiency score calculation with valid data."""
        # Arrange
        tracking_error = 0.0015  # 0.15%
        expense_ratio = 0.0020  # 0.20%
        liquidity_score = 85.0

        # Act
        score = calculate_etf_efficiency_score(tracking_error, expense_ratio, liquidity_score)

        # Assert
        assert isinstance(score, dict)
        assert "efficiency_score" in score
        assert "tracking_score" in score
        assert "cost_score" in score
        assert "liquidity_component" in score
        assert "efficiency_rating" in score
        assert 0 <= score["efficiency_score"] <= 100
        assert score["efficiency_rating"] in ["Excellent", "Good", "Fair", "Poor"]

    def test_should_give_excellent_rating_for_efficient_etf(self):
        """Test efficiency score for highly efficient ETF."""
        # Arrange
        tracking_error = 0.0010  # Low tracking error
        expense_ratio = 0.0010  # Low expense ratio
        liquidity_score = 95.0  # High liquidity

        # Act
        score = calculate_etf_efficiency_score(tracking_error, expense_ratio, liquidity_score)

        # Assert
        assert score["efficiency_score"] >= 80
        assert score["efficiency_rating"] == "Excellent"

    def test_should_give_poor_rating_for_inefficient_etf(self):
        """Test efficiency score for inefficient ETF."""
        # Arrange
        tracking_error = 0.0300  # High tracking error
        expense_ratio = 0.0150  # High expense ratio
        liquidity_score = 25.0  # Low liquidity

        # Act
        score = calculate_etf_efficiency_score(tracking_error, expense_ratio, liquidity_score)

        # Assert
        assert score["efficiency_score"] < 40
        assert score["efficiency_rating"] == "Poor"

    def test_should_weight_tracking_highest(self):
        """Test that tracking error has highest weight (40%)."""
        # Arrange - Excellent tracking, poor cost and liquidity
        score1 = calculate_etf_efficiency_score(tracking_error=0.0010, expense_ratio=0.0150, liquidity_score=25.0)

        # Arrange - Poor tracking, excellent cost and liquidity
        score2 = calculate_etf_efficiency_score(tracking_error=0.0300, expense_ratio=0.0010, liquidity_score=95.0)

        # Act & Assert
        # Good tracking should have significant impact
        assert score1["tracking_score"] > score2["tracking_score"]

    def test_should_handle_zero_values(self):
        """Test efficiency score with zero values."""
        # Arrange
        tracking_error = 0.0
        expense_ratio = 0.0
        liquidity_score = 0.0

        # Act
        score = calculate_etf_efficiency_score(tracking_error, expense_ratio, liquidity_score)

        # Assert
        assert isinstance(score, dict)
        # Zero tracking and expense should give high scores
        assert score["tracking_score"] == approx(100.0)
        assert score["cost_score"] == approx(100.0)


class TestETFMetricsEdgeCases:
    """Test suite for edge cases across all ETF metrics."""

    def test_should_handle_extreme_tracking_error(self):
        """Test metrics with extreme tracking error."""
        # Arrange
        etf_returns = pd.Series([0.01, 0.02, -0.01, 0.015, 0.02])
        benchmark_returns = pd.Series([0.05, 0.10, -0.05, 0.08, 0.12])  # Very different

        # Act
        te = calculate_tracking_error(etf_returns, benchmark_returns, annualize=False)
        corr = calculate_correlation(etf_returns, benchmark_returns)

        # Assert
        assert te > 0
        assert not np.isnan(te)
        assert not np.isinf(te)
        assert -1.0 <= corr <= 1.0

    def test_should_handle_extreme_expense_ratios(self):
        """Test expense impact with extreme expense ratios."""
        # Arrange
        returns = pd.Series([0.08, 0.10, 0.12, 0.09, 0.11])
        extreme_expense = 0.05  # 5% expense ratio (very high)

        # Act
        impact = calculate_expense_impact(returns, extreme_expense, years=10)

        # Assert
        assert impact["cumulative_cost"] > 0
        assert not np.isnan(impact["cumulative_cost"])
        assert not np.isinf(impact["cumulative_cost"])

    def test_should_handle_extreme_concentration(self):
        """Test concentration risk with single holding."""
        # Arrange
        holdings = [{"ticker": "AAPL", "weight": 1.0}]

        # Act
        risk = calculate_concentration_risk(holdings)

        # Assert
        assert risk["top_n_concentration"] == approx(1.0)
        assert risk["herfindahl_index"] == approx(1.0)
        assert risk["effective_n_holdings"] == pytest.approx(1.0, rel=1e-6)
        assert risk["concentration_rating"] == "Very High"

    def test_should_handle_nan_values_in_returns(self):
        """Test metrics with NaN values in return series."""
        # Arrange
        etf_returns = pd.Series([0.01, np.nan, -0.01, 0.015, 0.02])
        benchmark_returns = pd.Series([0.011, 0.019, np.nan, 0.014, 0.021])

        # Act
        te = calculate_tracking_error(etf_returns, benchmark_returns)
        corr = calculate_correlation(etf_returns, benchmark_returns)

        # Assert
        # Should handle NaN by dropping them
        assert isinstance(te, float)
        assert isinstance(corr, float)
        assert not np.isnan(te)
        assert not np.isnan(corr)

    def test_should_handle_negative_weights_in_holdings(self):
        """Test concentration risk with negative weights (short positions)."""
        # Arrange
        holdings = [
            {"ticker": "AAPL", "weight": 0.60},
            {"ticker": "MSFT", "weight": 0.40},
            {"ticker": "SHORT", "weight": -0.10},  # Short position
        ]

        # Act
        risk = calculate_concentration_risk(holdings)

        # Assert
        # Should handle gracefully (negative weights filtered out)
        assert isinstance(risk, dict)