"""
Unit tests for BacktestingDataExtractor.
"""

from pytest import approx
import logging

import pytest

from finwiz.integration.backtesting_extractor import (
    BacktestingDataExtractor,
    BacktestingMetrics,
)
from finwiz.schemas.investment_discovery import ValidationResult


class TestBacktestingDataExtractor:
    """Test suite for BacktestingDataExtractor."""

    @pytest.fixture
    def extractor(self):
        """Create extractor instance."""
        return BacktestingDataExtractor(logger=logging.getLogger("test"))

    @pytest.fixture
    def complete_validation_result(self):
        """Create validation result with all metrics available."""
        return ValidationResult(
            total_candidates=10,
            passed_validation=8,
            failed_validation=2,
            average_sharpe_ratio=1.5,
            average_sortino_ratio=1.8,
            average_max_drawdown=-0.15,
            backtest_period_years=5,
            market_regimes_tested=["bull", "bear", "sideways"],
            validation_details=[
                {
                    "symbol": "AAPL",
                    "annualized_return": 12.5,
                    "sharpe_ratio": 1.5,
                    "win_rate": 0.65,
                    "total_trades": 100,
                },
                {
                    "symbol": "MSFT",
                    "annualized_return": 15.0,
                    "sharpe_ratio": 1.8,
                    "win_rate": 0.70,
                    "total_trades": 120,
                },
            ],
        )

    @pytest.fixture
    def incomplete_validation_result(self):
        """Create validation result with missing metrics."""
        return ValidationResult(
            total_candidates=5,
            passed_validation=3,
            failed_validation=2,
            average_sharpe_ratio=0.0,  # Use 0.0 instead of None since schema doesn't allow None
            average_sortino_ratio=0.0,
            average_max_drawdown=0.0,
            backtest_period_years=5,
            market_regimes_tested=["bull"],
            validation_details=[],
        )

    def test_should_extract_all_metrics_when_data_complete(self, extractor, complete_validation_result):
        """Test extraction of all metrics when data is complete."""
        # Act
        metrics = extractor.extract_backtesting_metrics(complete_validation_result)

        # Assert
        assert metrics is not None
        assert metrics.annualized_return is not None
        assert metrics.sharpe_ratio == approx(1.5)
        assert metrics.sortino_ratio == approx(1.8)
        assert metrics.max_drawdown == approx(-0.15)
        assert metrics.win_rate is not None
        assert metrics.calmar_ratio is not None
        assert metrics.backtest_period_years == 5

    def test_should_return_none_for_missing_metrics(self, extractor, incomplete_validation_result):
        """Test that missing metrics are set to None when validation details are empty."""
        # Act
        metrics = extractor.extract_backtesting_metrics(incomplete_validation_result)

        # Assert
        assert metrics is not None
        # When validation_details is empty, calculated metrics should be None
        assert metrics.annualized_return is None
        assert metrics.win_rate is None
        # Schema-provided values will be present (0.0 in this case)
        # but our extractor will convert them appropriately
        assert metrics.sharpe_ratio == approx(0.0)  # From schema
        assert metrics.sortino_ratio == approx(0.0)  # From schema
        assert metrics.max_drawdown == approx(0.0)  # From schema

    def test_should_log_missing_metrics(self, extractor, incomplete_validation_result, caplog):
        """Test that missing metrics are logged."""
        # Arrange
        caplog.set_level(logging.WARNING)

        # Act
        extractor.extract_backtesting_metrics(incomplete_validation_result)

        # Assert
        assert "Missing metrics" in caplog.text

    def test_should_handle_zero_as_missing_data(self, extractor):
        """Test that zero values are treated as missing data when appropriate."""
        # Arrange
        validation_result = ValidationResult(
            total_candidates=1,
            passed_validation=1,
            failed_validation=0,
            average_sharpe_ratio=0.0,  # Zero value indicating missing data
            average_sortino_ratio=1.5,
            average_max_drawdown=-0.10,
            backtest_period_years=5,
            market_regimes_tested=["bull"],
            validation_details=[],
        )

        # Act
        metrics = extractor.extract_backtesting_metrics(validation_result)

        # Assert
        assert metrics is not None
        # Zero sharpe ratio is valid (though poor performance)
        assert metrics.sharpe_ratio == approx(0.0)
        assert metrics.sortino_ratio == approx(1.5)  # Valid value preserved

    def test_get_available_metrics_should_return_dict_with_none_values(self, extractor):
        """Test get_available_metrics returns dict with None for missing values."""
        # Arrange
        metrics = BacktestingMetrics(
            annualized_return=12.5,
            sharpe_ratio=1.5,
            sortino_ratio=None,
            calmar_ratio=None,
            max_drawdown=-0.15,
            win_rate=0.65,
            backtest_period_years=5,
            total_trades=100,
        )

        # Act
        result = extractor.get_available_metrics(metrics)

        # Assert
        assert result["annualized_return"] == approx(12.5)
        assert result["sharpe_ratio"] == approx(1.5)
        assert result["sortino_ratio"] is None
        assert result["calmar_ratio"] is None
        assert result["max_drawdown"] == approx(-0.15)
        assert result["win_rate"] == approx(0.65)

    def test_get_available_metrics_should_handle_none_input(self, extractor):
        """Test get_available_metrics handles None input."""
        # Act
        result = extractor.get_available_metrics(None)

        # Assert
        assert all(v is None for v in result.values())
        assert "annualized_return" in result
        assert "sharpe_ratio" in result
        assert "sortino_ratio" in result

    def test_format_for_display_should_show_not_calculated_for_none(self, extractor):
        """Test format_for_display shows 'Not calculated' for None values."""
        # Arrange
        metrics = BacktestingMetrics(
            annualized_return=12.5,
            sharpe_ratio=None,
            sortino_ratio=1.8,
            calmar_ratio=None,
            max_drawdown=-0.15,
            win_rate=None,
            backtest_period_years=5,
            total_trades=100,
        )

        # Act
        result = extractor.format_for_display(metrics)

        # Assert
        assert "Annualized Return: 12.50%" in result
        assert "Sharpe Ratio: Not calculated" in result
        assert "Sortino Ratio: 1.80" in result
        assert "Calmar Ratio: Not calculated" in result
        assert "Max Drawdown: -0.15%" in result
        assert "Win Rate: Not calculated" in result
        assert "Total Trades: 100" in result

    def test_format_for_display_should_handle_none_input(self, extractor):
        """Test format_for_display handles None input."""
        # Act
        result = extractor.format_for_display(None)

        # Assert
        assert result == "Backtesting data not available"

    def test_should_calculate_calmar_ratio_correctly(self, extractor, complete_validation_result):
        """Test Calmar ratio calculation."""
        # Act
        metrics = extractor.extract_backtesting_metrics(complete_validation_result)

        # Assert
        assert metrics is not None
        assert metrics.calmar_ratio is not None
        # Calmar = annualized_return / abs(max_drawdown)
        expected_calmar = metrics.annualized_return / abs(metrics.max_drawdown)
        assert abs(metrics.calmar_ratio - expected_calmar) < 0.01

    def test_should_return_none_for_calmar_when_drawdown_zero(self, extractor):
        """Test Calmar ratio returns None when max drawdown is zero."""
        # Arrange
        validation_result = ValidationResult(
            total_candidates=1,
            passed_validation=1,
            failed_validation=0,
            average_sharpe_ratio=1.5,
            average_sortino_ratio=1.8,
            average_max_drawdown=0.0,  # Zero drawdown
            backtest_period_years=5,
            market_regimes_tested=["bull"],
            validation_details=[
                {
                    "symbol": "AAPL",
                    "annualized_return": 12.5,
                    "win_rate": 0.65,
                }
            ],
        )

        # Act
        metrics = extractor.extract_backtesting_metrics(validation_result)

        # Assert
        assert metrics is not None
        assert metrics.calmar_ratio is None

    def test_should_extract_risk_adjusted_metrics(self, extractor, complete_validation_result):
        """Test extraction of risk-adjusted metrics."""
        # Act
        metrics = extractor.extract_risk_adjusted_metrics(complete_validation_result)

        # Assert
        assert metrics is not None
        assert metrics.sharpe_ratio == approx(1.5)
        assert metrics.sortino_ratio == approx(1.8)
        assert metrics.calmar_ratio is not None

    def test_should_log_available_and_missing_metrics(self, extractor, complete_validation_result, caplog):
        """Test that available and missing metrics are logged."""
        # Arrange
        caplog.set_level(logging.INFO)

        # Act
        extractor.extract_backtesting_metrics(complete_validation_result)

        # Assert
        assert "available" in caplog.text.lower()

    def test_should_handle_invalid_float_values(self, extractor):
        """Test handling of invalid float values."""
        # Note: Pydantic will reject inf values at schema level, so we test with very large values
        # Arrange
        validation_result = ValidationResult(
            total_candidates=1,
            passed_validation=1,
            failed_validation=0,
            average_sharpe_ratio=1e15,  # Extremely large value
            average_sortino_ratio=1.5,
            average_max_drawdown=-0.10,
            backtest_period_years=5,
            market_regimes_tested=["bull"],
            validation_details=[],
        )

        # Act
        metrics = extractor.extract_backtesting_metrics(validation_result)

        # Assert
        assert metrics is not None
        assert metrics.sharpe_ratio is None  # Invalid value converted to None
        assert metrics.sortino_ratio == approx(1.5)  # Valid value preserved

    def test_should_calculate_win_rate_from_validation_details(self, extractor, complete_validation_result):
        """Test win rate calculation from validation details."""
        # Act
        metrics = extractor.extract_backtesting_metrics(complete_validation_result)

        # Assert
        assert metrics is not None
        assert metrics.win_rate is not None
        # Average of 0.65 and 0.70
        assert abs(metrics.win_rate - 0.675) < 0.01

    def test_should_return_none_when_no_validation_details(self, extractor, incomplete_validation_result):
        """Test that None is returned for metrics when no validation details."""
        # Act
        metrics = extractor.extract_backtesting_metrics(incomplete_validation_result)

        # Assert
        assert metrics is not None
        assert metrics.annualized_return is None
        assert metrics.win_rate is None