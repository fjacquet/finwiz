"""
Unit tests for regime performance analysis in BacktestingDataExtractor.

Tests regime-specific performance extraction including bull/bear/sideways market analysis,
consistency scores, and performance comparison tables.
"""

import logging

import pytest

from finwiz.integration.backtesting_extractor import BacktestingDataExtractor, RegimePerformance
from finwiz.schemas.investment_discovery import ValidationResult


class TestRegimePerformanceAnalysis:
    """Test suite for regime performance analysis."""

    @pytest.fixture
    def extractor(self) -> BacktestingDataExtractor:
        """Create extractor instance for testing."""
        logger = logging.getLogger("test")
        return BacktestingDataExtractor(logger=logger)

    @pytest.fixture
    def multi_regime_validation_result(self) -> ValidationResult:
        """Create validation result with multiple market regimes."""
        return ValidationResult(
            total_candidates=3,
            passed_validation=3,
            failed_validation=0,
            validation_details=[
                {
                    "symbol": "SPY",
                    "annualized_return": 12.5,
                    "sharpe_ratio": 1.5,
                    "max_drawdown": -15.0,
                    "win_rate": 0.60,
                    "regime_performance": {
                        "bull": {
                            "annualized_return": 20.0,
                            "sharpe_ratio": 2.0,
                            "max_drawdown": -8.0,
                            "win_rate": 0.75,
                        },
                        "bear": {
                            "annualized_return": -5.0,
                            "sharpe_ratio": 0.5,
                            "max_drawdown": -25.0,
                            "win_rate": 0.35,
                        },
                        "sideways": {
                            "annualized_return": 8.0,
                            "sharpe_ratio": 1.2,
                            "max_drawdown": -12.0,
                            "win_rate": 0.55,
                        },
                        "volatile": {
                            "annualized_return": 15.0,
                            "sharpe_ratio": 1.0,
                            "max_drawdown": -20.0,
                            "win_rate": 0.50,
                        },
                    },
                }
            ],
            backtest_period_years=10,
            market_regimes_tested=["bull", "bear", "sideways", "volatile"],
            average_sharpe_ratio=1.5,
            average_max_drawdown=-15.0,
            average_sortino_ratio=2.0,
        )

    def test_should_extract_all_regime_types(
        self, extractor: BacktestingDataExtractor, multi_regime_validation_result: ValidationResult
    ) -> None:
        """Test extraction of all market regime types."""
        # Act
        regime_perf = extractor.extract_regime_performance(multi_regime_validation_result)

        # Assert
        assert len(regime_perf) == 4
        assert "bull" in regime_perf
        assert "bear" in regime_perf
        assert "sideways" in regime_perf
        assert "volatile" in regime_perf

    def test_should_create_regime_performance_models(
        self, extractor: BacktestingDataExtractor, multi_regime_validation_result: ValidationResult
    ) -> None:
        """Test that RegimePerformance models are created correctly."""
        # Act
        regime_perf = extractor.extract_regime_performance(multi_regime_validation_result)

        # Assert
        for regime_type, perf in regime_perf.items():
            assert isinstance(perf, RegimePerformance)
            assert perf.regime_type == regime_type
            assert hasattr(perf, "annualized_return")
            assert hasattr(perf, "sharpe_ratio")
            assert hasattr(perf, "max_drawdown")
            assert hasattr(perf, "win_rate")
            assert hasattr(perf, "consistency_score")

    def test_should_show_bull_market_outperformance(
        self, extractor: BacktestingDataExtractor, multi_regime_validation_result: ValidationResult
    ) -> None:
        """Test that bull market shows highest returns."""
        # Act
        regime_perf = extractor.extract_regime_performance(multi_regime_validation_result)

        # Assert
        bull_return = regime_perf["bull"].annualized_return
        bear_return = regime_perf["bear"].annualized_return
        sideways_return = regime_perf["sideways"].annualized_return

        assert bull_return > sideways_return
        assert bull_return > bear_return

    def test_should_show_bear_market_underperformance(
        self, extractor: BacktestingDataExtractor, multi_regime_validation_result: ValidationResult
    ) -> None:
        """Test that bear market shows lowest returns."""
        # Act
        regime_perf = extractor.extract_regime_performance(multi_regime_validation_result)

        # Assert
        bear_return = regime_perf["bear"].annualized_return
        bull_return = regime_perf["bull"].annualized_return
        sideways_return = regime_perf["sideways"].annualized_return

        assert bear_return < bull_return
        assert bear_return < sideways_return

    def test_should_calculate_consistency_scores_for_all_regimes(
        self, extractor: BacktestingDataExtractor, multi_regime_validation_result: ValidationResult
    ) -> None:
        """Test consistency score calculation for all regimes."""
        # Act
        regime_perf = extractor.extract_regime_performance(multi_regime_validation_result)

        # Assert
        for regime, perf in regime_perf.items():
            assert 0 <= perf.consistency_score <= 1
            # Bull market should have highest consistency (high win rate + high Sharpe)
            if regime == "bull":
                assert perf.consistency_score > 0.6

    def test_should_show_higher_consistency_for_better_performance(
        self, extractor: BacktestingDataExtractor, multi_regime_validation_result: ValidationResult
    ) -> None:
        """Test that better performing regimes have higher consistency scores."""
        # Act
        regime_perf = extractor.extract_regime_performance(multi_regime_validation_result)

        # Assert
        bull_consistency = regime_perf["bull"].consistency_score
        bear_consistency = regime_perf["bear"].consistency_score

        # Bull market (win_rate=0.75, sharpe=2.0) should have higher consistency
        # than bear market (win_rate=0.35, sharpe=0.5)
        assert bull_consistency > bear_consistency

    def test_should_extract_max_drawdown_for_each_regime(
        self, extractor: BacktestingDataExtractor, multi_regime_validation_result: ValidationResult
    ) -> None:
        """Test max drawdown extraction for each regime."""
        # Act
        regime_perf = extractor.extract_regime_performance(multi_regime_validation_result)

        # Assert
        for regime, perf in regime_perf.items():
            assert perf.max_drawdown <= 0  # Drawdown should be negative
            # Bear market should have worst drawdown
            if regime == "bear":
                assert perf.max_drawdown == -25.0

    def test_should_extract_win_rates_for_each_regime(
        self, extractor: BacktestingDataExtractor, multi_regime_validation_result: ValidationResult
    ) -> None:
        """Test win rate extraction for each regime."""
        # Act
        regime_perf = extractor.extract_regime_performance(multi_regime_validation_result)

        # Assert
        for regime, perf in regime_perf.items():
            assert 0 <= perf.win_rate <= 1
            # Bull market should have highest win rate
            if regime == "bull":
                assert perf.win_rate == 0.75

    def test_should_generate_performance_comparison_table_data(
        self, extractor: BacktestingDataExtractor, multi_regime_validation_result: ValidationResult
    ) -> None:
        """Test generation of data suitable for performance comparison tables."""
        # Act
        regime_perf = extractor.extract_regime_performance(multi_regime_validation_result)

        # Assert - Data should be suitable for table generation
        comparison_data = []
        for regime, perf in regime_perf.items():
            row = {
                "regime": regime,
                "return": perf.annualized_return,
                "sharpe": perf.sharpe_ratio,
                "drawdown": perf.max_drawdown,
                "win_rate": perf.win_rate,
                "consistency": perf.consistency_score,
            }
            comparison_data.append(row)

        assert len(comparison_data) == 4
        # Verify all required fields are present
        for row in comparison_data:
            assert "regime" in row
            assert "return" in row
            assert "sharpe" in row
            assert "drawdown" in row
            assert "win_rate" in row
            assert "consistency" in row

    def test_should_handle_missing_regime_data_gracefully(self, extractor: BacktestingDataExtractor) -> None:
        """Test handling when regime data is missing for some regimes."""
        # Arrange - Result with only partial regime data
        result = ValidationResult(
            total_candidates=1,
            passed_validation=1,
            failed_validation=0,
            validation_details=[
                {
                    "symbol": "TEST",
                    "regime_performance": {
                        "bull": {
                            "annualized_return": 15.0,
                            "sharpe_ratio": 1.5,
                            "max_drawdown": -10.0,
                            "win_rate": 0.65,
                        }
                        # Missing bear, sideways, volatile
                    },
                }
            ],
            backtest_period_years=5,
            market_regimes_tested=["bull", "bear", "sideways"],
            average_sharpe_ratio=1.5,
            average_max_drawdown=-10.0,
            average_sortino_ratio=2.0,
        )

        # Act
        regime_perf = extractor.extract_regime_performance(result)

        # Assert - Should only extract available regime
        assert len(regime_perf) == 1
        assert "bull" in regime_perf
        assert "bear" not in regime_perf

    def test_should_calculate_consistency_from_win_rate_and_sharpe(
        self, extractor: BacktestingDataExtractor
    ) -> None:
        """Test consistency score calculation formula."""
        # Arrange
        regime_data = {
            "annualized_return": 15.0,
            "sharpe_ratio": 2.0,  # Normalized to 1.0 (2.0/2.0)
            "max_drawdown": -10.0,
            "win_rate": 0.8,
        }

        # Act
        consistency = extractor._calculate_consistency_score(regime_data)

        # Assert
        # Consistency = (win_rate + normalized_sharpe) / 2
        # = (0.8 + 1.0) / 2 = 0.9
        assert abs(consistency - 0.9) < 0.01

    def test_should_cap_normalized_sharpe_at_one(self, extractor: BacktestingDataExtractor) -> None:
        """Test that normalized Sharpe is capped at 1.0 for consistency calculation."""
        # Arrange - Very high Sharpe ratio
        regime_data = {
            "annualized_return": 30.0,
            "sharpe_ratio": 5.0,  # Very high, should be capped at 1.0 after normalization
            "max_drawdown": -5.0,
            "win_rate": 0.6,
        }

        # Act
        consistency = extractor._calculate_consistency_score(regime_data)

        # Assert
        # Consistency = (0.6 + 1.0) / 2 = 0.8 (Sharpe capped at 1.0)
        assert consistency <= 1.0
        assert abs(consistency - 0.8) < 0.01

    def test_should_handle_negative_sharpe_in_consistency(self, extractor: BacktestingDataExtractor) -> None:
        """Test consistency calculation with negative Sharpe ratio."""
        # Arrange
        regime_data = {
            "annualized_return": -10.0,
            "sharpe_ratio": -0.5,  # Negative Sharpe
            "max_drawdown": -30.0,
            "win_rate": 0.3,
        }

        # Act
        consistency = extractor._calculate_consistency_score(regime_data)

        # Assert
        # Negative Sharpe should result in 0 for normalized component
        # Consistency = (0.3 + 0.0) / 2 = 0.15
        assert consistency >= 0
        assert consistency <= 0.5  # Should be low due to poor performance

    def test_should_aggregate_regime_performance_across_multiple_candidates(
        self, extractor: BacktestingDataExtractor
    ) -> None:
        """Test aggregation of regime performance across multiple candidates."""
        # Arrange - Two validation results with different regime performance
        result1 = ValidationResult(
            total_candidates=1,
            passed_validation=1,
            failed_validation=0,
            validation_details=[
                {
                    "symbol": "AAPL",
                    "regime_performance": {
                        "bull": {
                            "annualized_return": 20.0,
                            "sharpe_ratio": 2.0,
                            "max_drawdown": -8.0,
                            "win_rate": 0.70,
                        }
                    },
                }
            ],
            backtest_period_years=5,
            market_regimes_tested=["bull"],
            average_sharpe_ratio=2.0,
            average_max_drawdown=-8.0,
            average_sortino_ratio=2.5,
        )

        result2 = ValidationResult(
            total_candidates=1,
            passed_validation=1,
            failed_validation=0,
            validation_details=[
                {
                    "symbol": "MSFT",
                    "regime_performance": {
                        "bull": {
                            "annualized_return": 24.0,
                            "sharpe_ratio": 2.2,
                            "max_drawdown": -6.0,
                            "win_rate": 0.75,
                        }
                    },
                }
            ],
            backtest_period_years=5,
            market_regimes_tested=["bull"],
            average_sharpe_ratio=2.2,
            average_max_drawdown=-6.0,
            average_sortino_ratio=2.8,
        )

        # Act
        aggregated = extractor._aggregate_regime_performance([result1, result2])

        # Assert
        assert "bull" in aggregated
        bull_perf = aggregated["bull"]
        # Should be average of 20.0 and 24.0
        assert abs(bull_perf.annualized_return - 22.0) < 0.01
        # Should be average of 2.0 and 2.2
        assert abs(bull_perf.sharpe_ratio - 2.1) < 0.01

    def test_should_preserve_regime_type_in_aggregation(self, extractor: BacktestingDataExtractor) -> None:
        """Test that regime type is preserved during aggregation."""
        # Arrange
        result = ValidationResult(
            total_candidates=1,
            passed_validation=1,
            failed_validation=0,
            validation_details=[
                {
                    "symbol": "TEST",
                    "regime_performance": {
                        "sideways": {
                            "annualized_return": 8.0,
                            "sharpe_ratio": 1.2,
                            "max_drawdown": -12.0,
                            "win_rate": 0.55,
                        }
                    },
                }
            ],
            backtest_period_years=5,
            market_regimes_tested=["sideways"],
            average_sharpe_ratio=1.2,
            average_max_drawdown=-12.0,
            average_sortino_ratio=1.5,
        )

        # Act
        aggregated = extractor._aggregate_regime_performance([result])

        # Assert
        assert "sideways" in aggregated
        assert aggregated["sideways"].regime_type == "sideways"
