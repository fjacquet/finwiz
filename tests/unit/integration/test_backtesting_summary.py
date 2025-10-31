"""
Unit tests for backtesting summary generation in BacktestingDataExtractor.

Tests aggregation of backtesting results across all A+ candidates including
average metrics calculation, best/worst performer identification, and
structured output for report integration.
"""

import logging

import pytest

from finwiz.integration.backtesting_extractor import (
    BacktestingDataExtractor,
    BacktestingMetrics,
    BacktestingSummary,
)
from finwiz.schemas.investment_discovery import ValidationResult


class TestBacktestingSummaryGeneration:
    """Test suite for backtesting summary generation."""

    @pytest.fixture
    def extractor(self) -> BacktestingDataExtractor:
        """Create extractor instance for testing."""
        logger = logging.getLogger("test")
        return BacktestingDataExtractor(logger=logger)

    @pytest.fixture
    def multiple_validation_results(self) -> list[ValidationResult]:
        """Create multiple validation results for aggregation testing."""
        result1 = ValidationResult(
            total_candidates=3,
            passed_validation=3,
            failed_validation=0,
            validation_details=[
                {
                    "symbol": "AAPL",
                    "annualized_return": 18.0,
                    "sharpe_ratio": 1.8,
                    "max_drawdown": -12.0,
                    "win_rate": 0.65,
                    "total_trades": 120,
                },
                {
                    "symbol": "MSFT",
                    "annualized_return": 20.0,
                    "sharpe_ratio": 2.0,
                    "max_drawdown": -10.0,
                    "win_rate": 0.70,
                    "total_trades": 115,
                },
                {
                    "symbol": "GOOGL",
                    "annualized_return": 16.0,
                    "sharpe_ratio": 1.6,
                    "max_drawdown": -14.0,
                    "win_rate": 0.60,
                    "total_trades": 110,
                },
            ],
            backtest_period_years=5,
            market_regimes_tested=["bull", "bear"],
            average_sharpe_ratio=1.8,
            average_max_drawdown=-12.0,
            average_sortino_ratio=2.3,
        )

        result2 = ValidationResult(
            total_candidates=2,
            passed_validation=2,
            failed_validation=0,
            validation_details=[
                {
                    "symbol": "SPY",
                    "annualized_return": 12.0,
                    "sharpe_ratio": 1.5,
                    "max_drawdown": -15.0,
                    "win_rate": 0.58,
                    "total_trades": 100,
                },
                {
                    "symbol": "QQQ",
                    "annualized_return": 22.0,
                    "sharpe_ratio": 2.2,
                    "max_drawdown": -11.0,
                    "win_rate": 0.72,
                    "total_trades": 105,
                },
            ],
            backtest_period_years=5,
            market_regimes_tested=["bull", "bear"],
            average_sharpe_ratio=1.85,
            average_max_drawdown=-13.0,
            average_sortino_ratio=2.4,
        )

        return [result1, result2]

    def test_should_generate_summary_with_all_required_fields(self, extractor: BacktestingDataExtractor, multiple_validation_results: list[ValidationResult]) -> None:
        """Test that summary contains all required fields."""
        # Act
        summary = extractor.get_performance_summary(multiple_validation_results)

        # Assert
        assert summary is not None
        assert isinstance(summary, BacktestingSummary)
        assert hasattr(summary, "total_candidates_tested")
        assert hasattr(summary, "average_metrics")
        assert hasattr(summary, "regime_performance")
        assert hasattr(summary, "best_performer")
        assert hasattr(summary, "worst_performer")

    def test_should_calculate_total_candidates_correctly(self, extractor: BacktestingDataExtractor, multiple_validation_results: list[ValidationResult]) -> None:
        """Test total candidates calculation across multiple results."""
        # Act
        summary = extractor.get_performance_summary(multiple_validation_results)

        # Assert
        assert summary is not None
        # 3 candidates from result1 + 2 from result2 = 5 total
        assert summary.total_candidates_tested == 5

    def test_should_calculate_weighted_average_metrics(self, extractor: BacktestingDataExtractor, multiple_validation_results: list[ValidationResult]) -> None:
        """Test weighted average calculation based on number of candidates."""
        # Act
        summary = extractor.get_performance_summary(multiple_validation_results)

        # Assert
        assert summary is not None
        assert isinstance(summary.average_metrics, BacktestingMetrics)

        # Weighted average Sharpe: (1.8*3 + 1.85*2) / 5 = 1.82
        expected_sharpe = (1.8 * 3 + 1.85 * 2) / 5
        assert abs(summary.average_metrics.sharpe_ratio - expected_sharpe) < 0.01

        # Weighted average drawdown: (-12*3 + -13*2) / 5 = -12.4
        expected_drawdown = (-12.0 * 3 + -13.0 * 2) / 5
        assert abs(summary.average_metrics.max_drawdown - expected_drawdown) < 0.01

    def test_should_identify_best_performer_by_sharpe_ratio(self, extractor: BacktestingDataExtractor, multiple_validation_results: list[ValidationResult]) -> None:
        """Test identification of best performer by Sharpe ratio."""
        # Act
        summary = extractor.get_performance_summary(multiple_validation_results)

        # Assert
        assert summary is not None
        # QQQ has highest Sharpe ratio (2.2)
        assert summary.best_performer == "QQQ"

    def test_should_identify_worst_performer_by_sharpe_ratio(self, extractor: BacktestingDataExtractor, multiple_validation_results: list[ValidationResult]) -> None:
        """Test identification of worst performer by Sharpe ratio."""
        # Act
        summary = extractor.get_performance_summary(multiple_validation_results)

        # Assert
        assert summary is not None
        # SPY has lowest Sharpe ratio (1.5)
        assert summary.worst_performer == "SPY"

    def test_should_aggregate_regime_performance_across_results(self, extractor: BacktestingDataExtractor, multiple_validation_results: list[ValidationResult]) -> None:
        """Test aggregation of regime performance across multiple results."""
        # Arrange - Add regime performance to validation details
        for result in multiple_validation_results:
            for detail in result.validation_details:
                detail["regime_performance"] = {
                    "bull": {
                        "annualized_return": 20.0,
                        "sharpe_ratio": 2.0,
                        "max_drawdown": -8.0,
                        "win_rate": 0.70,
                    },
                    "bear": {
                        "annualized_return": 5.0,
                        "sharpe_ratio": 1.0,
                        "max_drawdown": -18.0,
                        "win_rate": 0.45,
                    },
                }

        # Act
        summary = extractor.get_performance_summary(multiple_validation_results)

        # Assert
        assert summary is not None
        assert len(summary.regime_performance) > 0
        assert "bull" in summary.regime_performance
        assert "bear" in summary.regime_performance

    def test_should_use_maximum_backtest_period(self, extractor: BacktestingDataExtractor, multiple_validation_results: list[ValidationResult]) -> None:
        """Test that summary uses the maximum backtest period from all results."""
        # Arrange - Set different backtest periods
        multiple_validation_results[0].backtest_period_years = 5
        multiple_validation_results[1].backtest_period_years = 7

        # Act
        summary = extractor.get_performance_summary(multiple_validation_results)

        # Assert
        assert summary is not None
        assert summary.average_metrics.backtest_period_years == 7

    def test_should_return_none_when_no_results_provided(self, extractor: BacktestingDataExtractor) -> None:
        """Test handling when no validation results are provided."""
        # Act
        summary = extractor.get_performance_summary([])

        # Assert
        assert summary is None

    def test_should_handle_single_validation_result(self, extractor: BacktestingDataExtractor) -> None:
        """Test summary generation with single validation result."""
        # Arrange
        single_result = ValidationResult(
            total_candidates=2,
            passed_validation=2,
            failed_validation=0,
            validation_details=[
                {
                    "symbol": "AAPL",
                    "annualized_return": 18.0,
                    "sharpe_ratio": 1.8,
                    "max_drawdown": -12.0,
                    "win_rate": 0.65,
                },
                {
                    "symbol": "MSFT",
                    "annualized_return": 20.0,
                    "sharpe_ratio": 2.0,
                    "max_drawdown": -10.0,
                    "win_rate": 0.70,
                },
            ],
            backtest_period_years=5,
            market_regimes_tested=["bull"],
            average_sharpe_ratio=1.9,
            average_max_drawdown=-11.0,
            average_sortino_ratio=2.5,
        )

        # Act
        summary = extractor.get_performance_summary([single_result])

        # Assert
        assert summary is not None
        assert summary.total_candidates_tested == 2
        assert summary.best_performer == "MSFT"
        assert summary.worst_performer == "AAPL"

    def test_should_calculate_average_return_from_validation_details(self, extractor: BacktestingDataExtractor, multiple_validation_results: list[ValidationResult]) -> None:
        """Test average return calculation from validation details."""
        # Act
        summary = extractor.get_performance_summary(multiple_validation_results)

        # Assert
        assert summary is not None
        # Should calculate weighted average of all returns
        assert summary.average_metrics.annualized_return > 0
        # Average should be between min and max returns
        assert 12.0 <= summary.average_metrics.annualized_return <= 22.0

    def test_should_calculate_average_win_rate_from_validation_details(self, extractor: BacktestingDataExtractor, multiple_validation_results: list[ValidationResult]) -> None:
        """Test average win rate calculation from validation details."""
        # Act
        summary = extractor.get_performance_summary(multiple_validation_results)

        # Assert
        assert summary is not None
        assert 0 <= summary.average_metrics.win_rate <= 1
        # Average should be between min and max win rates
        assert 0.58 <= summary.average_metrics.win_rate <= 0.72

    def test_should_calculate_calmar_ratio_in_average_metrics(self, extractor: BacktestingDataExtractor, multiple_validation_results: list[ValidationResult]) -> None:
        """Test Calmar ratio calculation in average metrics."""
        # Act
        summary = extractor.get_performance_summary(multiple_validation_results)

        # Assert
        assert summary is not None
        avg_return = summary.average_metrics.annualized_return
        avg_drawdown = abs(summary.average_metrics.max_drawdown)
        expected_calmar = avg_return / avg_drawdown if avg_drawdown > 0 else 0.0

        assert abs(summary.average_metrics.calmar_ratio - expected_calmar) < 0.01

    def test_should_create_structured_output_for_report_integration(self, extractor: BacktestingDataExtractor, multiple_validation_results: list[ValidationResult]) -> None:
        """Test that summary creates structured output suitable for report integration."""
        # Act
        summary = extractor.get_performance_summary(multiple_validation_results)

        # Assert
        assert summary is not None

        # Verify structure is suitable for report generation
        report_data = {
            "total_candidates": summary.total_candidates_tested,
            "average_return": summary.average_metrics.annualized_return,
            "average_sharpe": summary.average_metrics.sharpe_ratio,
            "average_drawdown": summary.average_metrics.max_drawdown,
            "average_win_rate": summary.average_metrics.win_rate,
            "best_performer": summary.best_performer,
            "worst_performer": summary.worst_performer,
            "regime_count": len(summary.regime_performance),
        }

        # All fields should be present and valid
        assert report_data["total_candidates"] > 0
        assert report_data["average_return"] > 0
        assert report_data["average_sharpe"] > 0
        assert report_data["average_drawdown"] < 0
        assert 0 <= report_data["average_win_rate"] <= 1
        assert report_data["best_performer"] != ""
        assert report_data["worst_performer"] != ""

    def test_should_handle_validation_results_with_different_metrics(self, extractor: BacktestingDataExtractor) -> None:
        """Test handling validation results with varying metric availability."""
        # Arrange - Results with different available metrics
        result1 = ValidationResult(
            total_candidates=1,
            passed_validation=1,
            failed_validation=0,
            validation_details=[
                {
                    "symbol": "AAPL",
                    "annualized_return": 18.0,
                    "sharpe_ratio": 1.8,
                    "max_drawdown": -12.0,
                    "win_rate": 0.65,
                    "information_ratio": 1.5,
                    "alpha": 0.05,
                    "beta": 1.1,
                }
            ],
            backtest_period_years=5,
            market_regimes_tested=[],
            average_sharpe_ratio=1.8,
            average_max_drawdown=-12.0,
            average_sortino_ratio=2.3,
        )

        result2 = ValidationResult(
            total_candidates=1,
            passed_validation=1,
            failed_validation=0,
            validation_details=[
                {
                    "symbol": "MSFT",
                    "annualized_return": 20.0,
                    "sharpe_ratio": 2.0,
                    "max_drawdown": -10.0,
                    "win_rate": 0.70,
                    # Missing optional metrics
                }
            ],
            backtest_period_years=5,
            market_regimes_tested=[],
            average_sharpe_ratio=2.0,
            average_max_drawdown=-10.0,
            average_sortino_ratio=2.5,
        )

        # Act
        summary = extractor.get_performance_summary([result1, result2])

        # Assert
        assert summary is not None
        assert summary.total_candidates_tested == 2
        # Should handle missing optional metrics gracefully

    def test_should_aggregate_sortino_ratio_correctly(self, extractor: BacktestingDataExtractor, multiple_validation_results: list[ValidationResult]) -> None:
        """Test Sortino ratio aggregation across results."""
        # Act
        summary = extractor.get_performance_summary(multiple_validation_results)

        # Assert
        assert summary is not None
        assert summary.average_metrics.sortino_ratio is not None
        # Weighted average: (2.3*3 + 2.4*2) / 5 = 2.34
        expected_sortino = (2.3 * 3 + 2.4 * 2) / 5
        assert abs(summary.average_metrics.sortino_ratio - expected_sortino) < 0.01

    def test_should_handle_empty_validation_details_gracefully(self, extractor: BacktestingDataExtractor) -> None:
        """Test handling when validation details are empty."""
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
        summary = extractor.get_performance_summary([result])

        # Assert
        assert summary is not None
        assert summary.total_candidates_tested == 0
        # Should handle empty details without crashing

    def test_should_provide_summary_suitable_for_comparison_tables(self, extractor: BacktestingDataExtractor, multiple_validation_results: list[ValidationResult]) -> None:
        """Test that summary provides data suitable for comparison tables."""
        # Act
        summary = extractor.get_performance_summary(multiple_validation_results)

        # Assert
        assert summary is not None

        # Create comparison table data
        comparison_table = {
            "headers": ["Metric", "Average", "Best", "Worst"],
            "rows": [
                [
                    "Annualized Return",
                    f"{summary.average_metrics.annualized_return:.2f}%",
                    summary.best_performer,
                    summary.worst_performer,
                ],
                [
                    "Sharpe Ratio",
                    f"{summary.average_metrics.sharpe_ratio:.2f}",
                    summary.best_performer,
                    summary.worst_performer,
                ],
                [
                    "Max Drawdown",
                    f"{summary.average_metrics.max_drawdown:.2f}%",
                    summary.best_performer,
                    summary.worst_performer,
                ],
            ],
        }

        # Verify table structure
        assert len(comparison_table["headers"]) == 4
        assert len(comparison_table["rows"]) == 3
        for row in comparison_table["rows"]:
            assert len(row) == 4
