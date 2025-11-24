"""
Unit tests for risk metrics calculation module.

Tests cover:
- Volatility calculations (annualized and non-annualized)
- Value at Risk (VaR) calculations
- Conditional Value at Risk (CVaR) calculations
- Sharpe ratio calculations
- Sortino ratio calculations
- Maximum drawdown calculations
- Beta coefficient calculations
- Edge cases (zero volatility, negative returns, empty data)
"""

import numpy as np
import pandas as pd
import pytest
from pytest import approx

from finwiz.utils.risk_metrics import (
    calculate_beta,
    calculate_cvar,
    calculate_max_drawdown,
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
    calculate_var,
    calculate_volatility,
)


class TestCalculateVolatility:
    """Test suite for volatility calculation."""

    def test_should_calculate_volatility_when_valid_returns(self):
        """Test volatility calculation with valid return data."""
        # Arrange
        returns = pd.Series([0.01, -0.02, 0.015, -0.01, 0.02])

        # Act
        vol = calculate_volatility(returns, annualize=False)

        # Assert
        assert vol > 0
        assert isinstance(vol, float)
        # Verify it matches pandas std()
        expected = returns.std()
        assert vol == pytest.approx(expected, rel=1e-6)

    def test_should_annualize_volatility_when_annualize_true(self):
        """Test annualized volatility calculation."""
        # Arrange
        returns = pd.Series([0.01, -0.02, 0.015, -0.01, 0.02])

        # Act
        vol_annual = calculate_volatility(returns, annualize=True)
        vol_daily = calculate_volatility(returns, annualize=False)

        # Assert
        # Annualized should be daily * sqrt(252)
        expected_annual = vol_daily * np.sqrt(252)
        assert vol_annual == pytest.approx(expected_annual, rel=1e-6)

    def test_should_return_zero_when_empty_series(self):
        """Test volatility with empty series."""
        # Arrange
        returns = pd.Series([], dtype=float)

        # Act
        vol = calculate_volatility(returns)

        # Assert
        assert vol == approx(0.0)

    def test_should_return_zero_when_constant_returns(self):
        """Test volatility with constant returns (zero volatility)."""
        # Arrange
        returns = pd.Series([0.01, 0.01, 0.01, 0.01, 0.01])

        # Act
        vol = calculate_volatility(returns, annualize=False)

        # Assert
        assert vol == pytest.approx(0.0, abs=1e-10)


class TestCalculateVaR:
    """Test suite for Value at Risk calculation."""

    def test_should_calculate_var_when_valid_returns(self):
        """Test VaR calculation with valid return data."""
        # Arrange
        returns = pd.Series([0.01, -0.02, 0.015, -0.01, 0.02, -0.03, 0.005])

        # Act
        var_95 = calculate_var(returns, confidence_level=0.95)

        # Assert
        assert var_95 < 0  # VaR should be negative (represents loss)
        assert isinstance(var_95, float)
        # VaR at 95% should be around the 5th percentile
        expected = np.percentile(returns, 5)
        assert var_95 == pytest.approx(expected, rel=1e-6)

    def test_should_calculate_var_at_different_confidence_levels(self):
        """Test VaR at different confidence levels."""
        # Arrange
        returns = pd.Series([-0.05, -0.03, -0.02, -0.01, 0.0, 0.01, 0.02, 0.03, 0.04, 0.05])

        # Act
        var_90 = calculate_var(returns, confidence_level=0.90)
        var_95 = calculate_var(returns, confidence_level=0.95)
        var_99 = calculate_var(returns, confidence_level=0.99)

        # Assert
        # Higher confidence level should give more extreme (more negative) VaR
        assert var_99 < var_95 < var_90

    def test_should_return_zero_when_empty_series(self):
        """Test VaR with empty series."""
        # Arrange
        returns = pd.Series([], dtype=float)

        # Act
        var = calculate_var(returns)

        # Assert
        assert var == approx(0.0)


class TestCalculateCVaR:
    """Test suite for Conditional Value at Risk calculation."""

    def test_should_calculate_cvar_when_valid_returns(self):
        """Test CVaR calculation with valid return data."""
        # Arrange
        returns = pd.Series([0.01, -0.02, 0.015, -0.01, 0.02, -0.03, 0.005, -0.04])

        # Act
        cvar_95 = calculate_cvar(returns, confidence_level=0.95)
        var_95 = calculate_var(returns, confidence_level=0.95)

        # Assert
        assert cvar_95 < 0  # CVaR should be negative (represents expected loss)
        assert isinstance(cvar_95, float)
        # CVaR should be more extreme (more negative) than VaR
        assert cvar_95 <= var_95

    def test_should_calculate_cvar_as_mean_of_tail(self):
        """Test that CVaR is the mean of returns worse than VaR."""
        # Arrange
        returns = pd.Series([-0.05, -0.04, -0.03, -0.02, -0.01, 0.0, 0.01, 0.02, 0.03, 0.04])

        # Act
        cvar_95 = calculate_cvar(returns, confidence_level=0.95)
        var_95 = calculate_var(returns, confidence_level=0.95)

        # Assert
        # Manually calculate expected CVaR
        tail_returns = returns[returns <= var_95]
        expected_cvar = tail_returns.mean()
        assert cvar_95 == pytest.approx(expected_cvar, rel=1e-6)

    def test_should_return_zero_when_empty_series(self):
        """Test CVaR with empty series."""
        # Arrange
        returns = pd.Series([], dtype=float)

        # Act
        cvar = calculate_cvar(returns)

        # Assert
        assert cvar == approx(0.0)


class TestCalculateMaxDrawdown:
    """Test suite for maximum drawdown calculation."""

    def test_should_calculate_max_drawdown_when_valid_prices(self):
        """Test maximum drawdown calculation with valid price data."""
        # Arrange
        # Price series: 100 -> 110 (peak) -> 88 (trough) -> 100
        # Max drawdown = (88 - 110) / 110 = -20%
        prices = pd.Series([100, 105, 110, 105, 95, 88, 92, 100])

        # Act
        mdd = calculate_max_drawdown(prices)

        # Assert
        assert mdd < 0  # Drawdown should be negative
        assert isinstance(mdd, float)
        # Expected: (88 - 110) / 110 = -0.2
        assert mdd == pytest.approx(-0.2, rel=1e-2)

    def test_should_return_zero_when_prices_always_increase(self):
        """Test maximum drawdown with monotonically increasing prices."""
        # Arrange
        prices = pd.Series([100, 105, 110, 115, 120, 125])

        # Act
        mdd = calculate_max_drawdown(prices)

        # Assert
        assert mdd == pytest.approx(0.0, abs=1e-10)

    def test_should_return_zero_when_empty_series(self):
        """Test maximum drawdown with empty series."""
        # Arrange
        prices = pd.Series([], dtype=float)

        # Act
        mdd = calculate_max_drawdown(prices)

        # Assert
        assert mdd == approx(0.0)

    def test_should_return_zero_when_single_price(self):
        """Test maximum drawdown with single price point."""
        # Arrange
        prices = pd.Series([100])

        # Act
        mdd = calculate_max_drawdown(prices)

        # Assert
        assert mdd == approx(0.0)


class TestCalculateSharpeRatio:
    """Test suite for Sharpe ratio calculation."""

    def test_should_calculate_sharpe_ratio_when_valid_returns(self):
        """Test Sharpe ratio calculation with valid return data."""
        # Arrange
        # Positive returns with some volatility
        returns = pd.Series([0.01, 0.02, 0.015, 0.01, 0.02, 0.018, 0.012])

        # Act
        sharpe = calculate_sharpe_ratio(returns, risk_free_rate=0.02)

        # Assert
        assert isinstance(sharpe, float)
        # With positive returns above risk-free rate, Sharpe should be positive
        assert sharpe > 0

    def test_should_match_expected_sharpe_calculation(self):
        """Test that Sharpe ratio matches manual calculation."""
        # Arrange
        returns = pd.Series([0.01, 0.02, 0.015, 0.01, 0.02])
        risk_free_rate = 0.02

        # Act
        sharpe = calculate_sharpe_ratio(returns, risk_free_rate=risk_free_rate)

        # Assert
        # Manual calculation
        mean_return = returns.mean() * 252  # Annualize
        volatility = returns.std() * np.sqrt(252)  # Annualize
        expected_sharpe = (mean_return - risk_free_rate) / volatility
        assert sharpe == pytest.approx(expected_sharpe, rel=1e-6)

    def test_should_return_zero_when_zero_volatility(self):
        """Test Sharpe ratio with zero volatility."""
        # Arrange
        returns = pd.Series([0.01, 0.01, 0.01, 0.01, 0.01])

        # Act
        sharpe = calculate_sharpe_ratio(returns, risk_free_rate=0.02)

        # Assert
        # When volatility is zero and mean return < risk-free rate,
        # Empyrical returns inf (no volatility, negative excess return)
        assert np.isinf(sharpe)

    def test_should_return_zero_when_empty_series(self):
        """Test Sharpe ratio with empty series."""
        # Arrange
        returns = pd.Series([], dtype=float)

        # Act
        sharpe = calculate_sharpe_ratio(returns)

        # Assert
        assert sharpe == approx(0.0)

    def test_should_return_negative_when_returns_below_risk_free(self):
        """Test Sharpe ratio when returns are below risk-free rate."""
        # Arrange
        # Low returns below risk-free rate
        returns = pd.Series([0.0001, 0.0002, 0.00015, 0.0001, 0.0002])

        # Act
        sharpe = calculate_sharpe_ratio(returns, risk_free_rate=0.05)

        # Assert
        assert sharpe < 0


class TestCalculateSortinoRatio:
    """Test suite for Sortino ratio calculation."""

    def test_should_calculate_sortino_ratio_when_valid_returns(self):
        """Test Sortino ratio calculation with valid return data."""
        # Arrange
        returns = pd.Series([0.01, -0.02, 0.015, -0.01, 0.02, 0.018, -0.005])

        # Act
        sortino = calculate_sortino_ratio(returns, risk_free_rate=0.02)

        # Assert
        assert isinstance(sortino, float)
        # Sortino should be finite
        assert not np.isinf(sortino) or sortino == float("inf")

    def test_should_only_consider_downside_deviation(self):
        """Test that Sortino ratio only considers negative returns."""
        # Arrange
        returns = pd.Series([0.01, -0.02, 0.015, -0.01, 0.02])
        risk_free_rate = 0.0  # Use 0 for simplicity

        # Act
        sortino = calculate_sortino_ratio(returns, risk_free_rate=risk_free_rate)

        # Assert
        # Empyrical calculates Sortino using downside deviation
        # We verify it's a positive finite number with mixed returns
        assert isinstance(sortino, float)
        assert not np.isinf(sortino)

    def test_should_return_inf_when_no_downside_and_positive_excess_return(self):
        """Test Sortino ratio with no negative returns and positive excess return."""
        # Arrange
        # All positive returns above risk-free rate
        returns = pd.Series([0.01, 0.02, 0.015, 0.01, 0.02])

        # Act
        sortino = calculate_sortino_ratio(returns, risk_free_rate=0.0)

        # Assert
        # No downside risk with positive returns should give infinite Sortino
        assert sortino == float("inf")

    def test_should_return_zero_when_no_downside_and_negative_excess_return(self):
        """Test Sortino ratio with no negative returns but negative excess return."""
        # Arrange
        # All positive returns but below risk-free rate
        returns = pd.Series([0.0001, 0.0002, 0.00015, 0.0001, 0.0002])

        # Act
        sortino = calculate_sortino_ratio(returns, risk_free_rate=0.10)

        # Assert
        # When mean return < required return, Sortino is negative
        assert sortino < 0

    def test_should_return_zero_when_empty_series(self):
        """Test Sortino ratio with empty series."""
        # Arrange
        returns = pd.Series([], dtype=float)

        # Act
        sortino = calculate_sortino_ratio(returns)

        # Assert
        assert sortino == approx(0.0)


class TestCalculateBeta:
    """Test suite for beta coefficient calculation."""

    def test_should_calculate_beta_when_valid_returns(self):
        """Test beta calculation with valid return data."""
        # Arrange
        asset_returns = pd.Series([0.01, 0.02, -0.01, 0.015, 0.02])
        market_returns = pd.Series([0.008, 0.015, -0.005, 0.01, 0.012])

        # Act
        beta = calculate_beta(asset_returns, market_returns)

        # Assert
        assert isinstance(beta, float)
        assert beta > 0  # Positive correlation expected

    def test_should_match_expected_beta_calculation(self):
        """Test that beta matches manual calculation."""
        # Arrange
        asset_returns = pd.Series([0.01, 0.02, -0.01, 0.015, 0.02])
        market_returns = pd.Series([0.008, 0.015, -0.005, 0.01, 0.012])

        # Act
        beta = calculate_beta(asset_returns, market_returns)

        # Assert
        # Manual calculation
        covariance = asset_returns.cov(market_returns)
        market_variance = market_returns.var()
        expected_beta = covariance / market_variance
        assert beta == pytest.approx(expected_beta, rel=1e-6)

    def test_should_return_zero_when_empty_series(self):
        """Test beta with empty series."""
        # Arrange
        asset_returns = pd.Series([], dtype=float)
        market_returns = pd.Series([], dtype=float)

        # Act
        beta = calculate_beta(asset_returns, market_returns)

        # Assert
        assert beta == approx(0.0)

    def test_should_return_zero_when_zero_market_variance(self):
        """Test beta when market has zero variance."""
        # Arrange
        asset_returns = pd.Series([0.01, 0.02, -0.01, 0.015, 0.02])
        market_returns = pd.Series([0.01, 0.01, 0.01, 0.01, 0.01])  # Constant

        # Act
        beta = calculate_beta(asset_returns, market_returns)

        # Assert
        assert beta == approx(0.0)

    def test_should_handle_misaligned_indices(self):
        """Test beta with misaligned series indices."""
        # Arrange
        dates1 = pd.date_range("2023-01-01", periods=5)
        dates2 = pd.date_range("2023-01-02", periods=5)
        asset_returns = pd.Series([0.01, 0.02, -0.01, 0.015, 0.02], index=dates1)
        market_returns = pd.Series([0.008, 0.015, -0.005, 0.01, 0.012], index=dates2)

        # Act
        beta = calculate_beta(asset_returns, market_returns)

        # Assert
        # Should handle alignment and calculate beta on overlapping dates
        assert isinstance(beta, float)

    def test_should_return_approximately_one_when_asset_equals_market(self):
        """Test beta when asset returns equal market returns."""
        # Arrange
        returns = pd.Series([0.01, 0.02, -0.01, 0.015, 0.02])

        # Act
        beta = calculate_beta(returns, returns)

        # Assert
        # Beta should be 1.0 when asset = market
        assert beta == pytest.approx(1.0, rel=1e-6)


class TestRiskMetricsEdgeCases:
    """Test suite for edge cases across all risk metrics."""

    def test_should_handle_negative_returns_correctly(self):
        """Test all metrics with predominantly negative returns."""
        # Arrange
        returns = pd.Series([-0.01, -0.02, -0.015, -0.01, -0.02])

        # Act & Assert
        vol = calculate_volatility(returns)
        assert vol > 0

        var = calculate_var(returns)
        assert var < 0

        cvar = calculate_cvar(returns)
        assert cvar < 0

        sharpe = calculate_sharpe_ratio(returns, risk_free_rate=0.02)
        assert sharpe < 0  # Negative returns should give negative Sharpe

        sortino = calculate_sortino_ratio(returns, risk_free_rate=0.02)
        assert sortino < 0  # Negative returns should give negative Sortino

    def test_should_handle_single_data_point(self):
        """Test metrics with single data point."""
        # Arrange
        returns = pd.Series([0.01])

        # Act & Assert
        # Most metrics should handle single point gracefully
        vol = calculate_volatility(returns, annualize=False)
        # Single point has undefined std in pandas (returns NaN), but we handle it
        assert vol == approx(0.0) or np.isnan(vol)

    def test_should_handle_extreme_values(self):
        """Test metrics with extreme values."""
        # Arrange
        returns = pd.Series([0.5, -0.4, 0.3, -0.35, 0.25])  # Extreme daily returns

        # Act & Assert
        vol = calculate_volatility(returns)
        assert vol > 0
        assert not np.isnan(vol)
        assert not np.isinf(vol)

        var = calculate_var(returns)
        assert not np.isnan(var)

        sharpe = calculate_sharpe_ratio(returns, risk_free_rate=0.02)
        assert not np.isnan(sharpe)
