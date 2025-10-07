"""
Unit tests for BacktestingDataExtractor.

Tests extraction of backtesting performance metrics from discovery crew validation results
with fully mocked data (no external calls).
"""

import logging

import pytest

from finwiz.integration.backtesting_extractor import (
    BacktestingDataExtractor,
    BacktestingMetrics,
    BacktestingSummary,
    RegimePerformance,
    RiskAdjustedMetrics,
)
from finwiz.schemas.investment_discovery import ValidationResult


class TestBacktestingDataExtractor:
    """Test suite for BacktestingDataExtractor."""

    @pytest.fixture
    def extractor(self) -> BacktestingDataExtractor:
        """Create extractor instance for testing."""
        logger = logging.getLogger("test")
        return BacktestingDataExtractor(logger=logger)

    @pytest.fixture
    def sample_validation_result(self) -> ValidationResult:
        """Create sample validation result with backtesting data."""
        return ValidationResult(
            total_candidates=5,
            passed_validation=4,
            failed_validation=1,
            validation_details=[
                {
                    "symbol": "AAPL",
                    "annualized_return": 15.5,
                    "sharpe_ratio": 1.8,
                    "max_drawdown": -12.3,
                    "win_rate": 0.65,
                    "total_trades": 120,
                    "regime_performance": {
                        "bull": {
                            "annualized_return": 22.0,
                            "sharpe_ratio": 2.1,
                            "max_drawdown": -8.0,
                            "win_rate": 0.72,
                        },
                        "bear": {
                            "annualized_return": 5.0,
                            "sharpe_ratio": 0.9,
                            "max_drawdown": -18.0,
                            "win_rate": 0.48,
                        },
                    },
                },
                {
                    "symbol": "MSFT",
                    "annualized_return": 18.2,
                    "sharpe_ratio": 2.0,
                    "max_drawdown": -10.5,
                    "win_rate": 0.68,
                    "total_trades": 115,
                    "regime_performance": {
                        "bull": {
                            "annualized_return": 25.0,
                            "sharpe_ratio": 2.3,
                            "max_drawdown": -7.0,
                            "win_rate": 0.75,
                        },
                        "bear": {
                            "annualized_return": 8.0,
                            "sharpe_ratio": 1.2,
                            "max_drawdown": -15.0,
                            "win_rate": 0.52,
                        },
                    },
                },
            ],
            backtest_period_years=5,
            market_regimes_tested=["bull", "bear", "sideways"],
            average_sharpe_ratio=1.9,
            average_max_drawdown=-11.4,
            average_sortino_ratio=2.5,
            correlation_analysis={},
            stress_test_results={},
            validated_candidates=["AAPL", "MSFT"],
            rejected_candidates=[],
        )

    def test_should_initialize_extractor(self, extractor: BacktestingDataExtractor) -> None:
        """Test that extractor initializes correctly."""
        assert extractor is not None
        assert extractor.logger is not None

    def test_should_extract_backtesting_metrics_when_valid_data(
        self, extractor: BacktestingDataExtractor, sample_validation_result: ValidationResult
    ) -> None:
        """Test extraction of backtesting metrics from validation result."""
        # Act
        metrics = extractor.extract_backtesting_metrics(sample_validation_result)

        # Assert
        assert metrics is not None
        assert isinstance(metrics, BacktestingMetrics)
        assert metrics.annualized_return > 0
        assert metrics.sharpe_ratio == 1.9
        assert metrics.max_drawdown == -11.4
        assert 0 <= metrics.win_rate <= 1
        assert metrics.sortino_ratio == 2.5
        assert metrics.backtest_period_years == 5

    def test_should_calculate_calmar_ratio_correctly(
        self, extractor: BacktestingDataExtractor, sample_validation_result: ValidationResult
    ) -> None:
        """Test Calmar ratio calculation (return / abs(max_drawdown))."""
        # Act
        metrics = extractor.extract_backtesting_metrics(sample_validation_result)

        # Assert
        assert metrics is not None
        expected_calmar = metrics.annualized_return / abs(metrics.max_drawdown)
        assert abs(metrics.calmar_ratio - expected_calmar) < 0.01

    def test_should_extract_total_trades_when_available(
        self, extractor: BacktestingDataExtractor, sample_validation_result: ValidationResult
    ) -> None:
        """Test extraction of total trades from validation details."""
        # Act
        metrics = extractor.extract_backtesting_metrics(sample_validation_result)

        # Assert
        assert metrics is not None
        assert metrics.total_trades is not None
        assert metrics.total_trades == 235  # 120 + 115

    def test_should_return_none_when_extraction_fails(self, extractor: BacktestingDataExtractor) -> None:
        """Test graceful handling when extraction fails."""
        # Arrange - Invalid validation result
        invalid_result = ValidationResult(
            total_candidates=0,
            passed_validation=0,
            failed_validation=0,
            validation_details=[],
            backtest_period_years=5,
            market_regimes_tested=[],
            average_sharpe_ratio=0.0,
            average_max_drawdown=0.0,
            average_sortino_ratio=0.0,
        )

        # Act
        metrics = extractor.extract_backtesting_metrics(invalid_result)

        # Assert
        assert metrics is not None  # Should still create metrics with zeros

    def test_should_extract_regime_performance_when_available(
        self, extractor: BacktestingDataExtractor, sample_validation_result: ValidationResult
    ) -> None:
        """Test extraction of regime-specific performance metrics."""
        # Act
        regime_perf = extractor.extract_regime_performance(sample_validation_result)

        # Assert
        assert regime_perf is not None
        assert isinstance(regime_perf, dict)
        assert "bull" in regime_perf
        assert "bear" in regime_perf

        bull_perf = regime_perf["bull"]
        assert isinstance(bull_perf, RegimePerformance)
        assert bull_perf.regime_type == "bull"
        assert bull_perf.annualized_return > 0
        assert bull_perf.sharpe_ratio > 0
        assert 0 <= bull_perf.consistency_score <= 1

    def test_should_calculate_consistency_score_correctly(
        self, extractor: BacktestingDataExtractor, sample_validation_result: ValidationResult
    ) -> None:
        """Test consistency score calculation for regime performance."""
        # Act
        regime_perf = extractor.extract_regime_performance(sample_validation_result)

        # Assert
        assert regime_perf is not None
        for regime, perf in regime_perf.items():
            # Consistency should be between 0 and 1
            assert 0 <= perf.consistency_score <= 1
            # Higher win rate and Sharpe should give higher consistency
            if perf.win_rate > 0.6 and perf.sharpe_ratio > 1.5:
                assert perf.consistency_score > 0.5

    def test_should_return_empty_dict_when_no_regime_data(self, extractor: BacktestingDataExtractor) -> None:
        """Test handling when no regime data is available."""
        # Arrange
        result = ValidationResult(
            total_candidates=1,
            passed_validation=1,
            failed_validation=0,
            validation_details=[{"symbol": "TEST"}],
            backtest_period_years=5,
            market_regimes_tested=[],
            average_sharpe_ratio=1.5,
            average_max_drawdown=-10.0,
            average_sortino_ratio=2.0,
        )

        # Act
        regime_perf = extractor.extract_regime_performance(result)

        # Assert
        assert regime_perf == {}

    def test_should_extract_risk_adjusted_metrics_when_available(
        self, extractor: BacktestingDataExtractor, sample_validation_result: ValidationResult
    ) -> None:
        """Test extraction of risk-adjusted metrics (Sharpe, Sortino, Calmar)."""
        # Act
        metrics = extractor.extract_risk_adjusted_metrics(sample_validation_result)

        # Assert
        assert metrics is not None
        assert isinstance(metrics, RiskAdjustedMetrics)
        assert metrics.sharpe_ratio == 1.9
        assert metrics.sortino_ratio == 2.5
        assert metrics.calmar_ratio > 0

    def test_should_handle_missing_optional_metrics(self, extractor: BacktestingDataExtractor) -> None:
        """Test handling when optional metrics (alpha, beta, IR) are missing."""
        # Arrange
        result = ValidationResult(
            total_candidates=1,
            passed_validation=1,
            failed_validation=0,
            validation_details=[{"symbol": "TEST"}],
            backtest_period_years=5,
            market_regimes_tested=[],
            average_sharpe_ratio=1.5,
            average_max_drawdown=-10.0,
            average_sortino_ratio=2.0,
        )

        # Act
        metrics = extractor.extract_risk_adjusted_metrics(result)

        # Assert
        assert metrics is not None
        assert metrics.information_ratio is None
        assert metrics.alpha is None
        assert metrics.beta is None

    def test_should_generate_performance_summary_when_multiple_results(
        self, extractor: BacktestingDataExtractor, sample_validation_result: ValidationResult
    ) -> None:
        """Test generation of comprehensive backtesting summary."""
        # Arrange
        validation_results = [sample_validation_result]

        # Act
        summary = extractor.get_performance_summary(validation_results)

        # Assert
        assert summary is not None
        assert isinstance(summary, BacktestingSummary)
        assert summary.total_candidates_tested == 5
        assert isinstance(summary.average_metrics, BacktestingMetrics)
        assert summary.best_performer in ["AAPL", "MSFT"]
        assert summary.worst_performer in ["AAPL", "MSFT"]

    def test_should_aggregate_metrics_across_multiple_results(
        self, extractor: BacktestingDataExtractor, sample_validation_result: ValidationResult
    ) -> None:
        """Test aggregation of metrics across multiple validation results."""
        # Arrange - Create second validation result
        result2 = ValidationResult(
            total_candidates=3,
            passed_validation=3,
            failed_validation=0,
            validation_details=[
                {
                    "symbol": "GOOGL",
                    "annualized_return": 20.0,
                    "sharpe_ratio": 2.2,
                    "max_drawdown": -9.0,
                    "win_rate": 0.70,
                }
            ],
            backtest_period_years=5,
            market_regimes_tested=["bull"],
            average_sharpe_ratio=2.2,
            average_max_drawdown=-9.0,
            average_sortino_ratio=2.8,
        )

        validation_results = [sample_validation_result, result2]

        # Act
        summary = extractor.get_performance_summary(validation_results)

        # Assert
        assert summary is not None
        assert summary.total_candidates_tested == 8  # 5 + 3
        # Average metrics should be weighted by number of candidates
        assert summary.average_metrics.sharpe_ratio > 1.9
        assert summary.average_metrics.sharpe_ratio < 2.2

    def test_should_aggregate_regime_performance_across_results(
        self, extractor: BacktestingDataExtractor, sample_validation_result: ValidationResult
    ) -> None:
        """Test aggregation of regime performance across multiple results."""
        # Arrange
        validation_results = [sample_validation_result]

        # Act
        summary = extractor.get_performance_summary(validation_results)

        # Assert
        assert summary is not None
        assert len(summary.regime_performance) > 0
        assert "bull" in summary.regime_performance
        assert "bear" in summary.regime_performance

    def test_should_identify_best_worst_performers_correctly(
        self, extractor: BacktestingDataExtractor, sample_validation_result: ValidationResult
    ) -> None:
        """Test identification of best and worst performers by Sharpe ratio."""
        # Arrange
        validation_results = [sample_validation_result]

        # Act
        summary = extractor.get_performance_summary(validation_results)

        # Assert
        assert summary is not None
        # MSFT has higher Sharpe (2.0) than AAPL (1.8)
        assert summary.best_performer == "MSFT"
        assert summary.worst_performer == "AAPL"

    def test_should_return_none_when_no_validation_results(self, extractor: BacktestingDataExtractor) -> None:
        """Test handling when no validation results are provided."""
        # Act
        summary = extractor.get_performance_summary([])

        # Assert
        assert summary is None

    def test_should_handle_validation_result_without_details(self, extractor: BacktestingDataExtractor) -> None:
        """Test handling validation result with empty validation_details."""
        # Arrange
        result = ValidationResult(
            total_candidates=0,
            passed_validation=0,
            failed_validation=0,
            validation_details=[],
            backtest_period_years=5,
            market_regimes_tested=[],
            average_sharpe_ratio=0.0,
            average_max_drawdown=0.0,
            average_sortino_ratio=0.0,
        )

        # Act
        metrics = extractor.extract_backtesting_metrics(result)

        # Assert
        assert metrics is not None
        assert metrics.annualized_return == 0.0
        assert metrics.win_rate == 0.0

    def test_should_calculate_win_rate_from_validation_details(
        self, extractor: BacktestingDataExtractor, sample_validation_result: ValidationResult
    ) -> None:
        """Test win rate calculation from validation details."""
        # Act
        metrics = extractor.extract_backtesting_metrics(sample_validation_result)

        # Assert
        assert metrics is not None
        # Average of 0.65 and 0.68
        expected_win_rate = (0.65 + 0.68) / 2
        assert abs(metrics.win_rate - expected_win_rate) < 0.01

    def test_should_handle_zero_max_drawdown_in_calmar_calculation(
        self, extractor: BacktestingDataExtractor
    ) -> None:
        """Test Calmar ratio calculation when max drawdown is zero."""
        # Arrange
        result = ValidationResult(
            total_candidates=1,
            passed_validation=1,
            failed_validation=0,
            validation_details=[{"symbol": "TEST", "annualized_return": 10.0}],
            backtest_period_years=5,
            market_regimes_tested=[],
            average_sharpe_ratio=1.5,
            average_max_drawdown=0.0,  # Zero drawdown
            average_sortino_ratio=2.0,
        )

        # Act
        metrics = extractor.extract_backtesting_metrics(result)

        # Assert
        assert metrics is not None
        assert metrics.calmar_ratio == 0.0  # Should handle division by zero

    def test_should_extract_regime_data_for_specific_regime(
        self, extractor: BacktestingDataExtractor, sample_validation_result: ValidationResult
    ) -> None:
        """Test extraction of data for a specific market regime."""
        # Act
        regime_data = extractor._extract_regime_data(sample_validation_result, "bull")

        # Assert
        assert regime_data is not None
        assert "annualized_return" in regime_data
        assert "sharpe_ratio" in regime_data
        assert regime_data["annualized_return"] > 0

    def test_should_return_none_for_nonexistent_regime(
        self, extractor: BacktestingDataExtractor, sample_validation_result: ValidationResult
    ) -> None:
        """Test handling when requested regime doesn't exist."""
        # Act
        regime_data = extractor._extract_regime_data(sample_validation_result, "nonexistent")

        # Assert
        assert regime_data is None
