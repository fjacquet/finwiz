"""
Unit tests for PerformanceMetricsAggregator.

Tests aggregation logic for performance metrics by asset type and regime,
portfolio impact calculations, and comprehensive report generation.
"""

from datetime import datetime

import pytest
from pytest import approx

from finwiz.infrastructure.monitoring.performance_metrics_aggregator import (
    PerformanceMetricsAggregator,
    PortfolioImpactMetrics,
)
from finwiz.orchestrators.extraction.backtesting import BacktestingDataExtractor, RegimePerformance
from finwiz.schemas.investment_discovery import ValidationResult


class TestPerformanceMetricsAggregator:
    """Test suite for PerformanceMetricsAggregator."""

    @pytest.fixture
    def mock_backtesting_extractor(self, mocker):
        """Create mock backtesting extractor."""
        extractor = mocker.Mock(spec=BacktestingDataExtractor)
        return extractor

    @pytest.fixture
    def aggregator(self, mock_backtesting_extractor):
        """Create aggregator instance."""
        return PerformanceMetricsAggregator(mock_backtesting_extractor)

    @pytest.fixture
    def sample_validation_result(self):
        """Create sample validation result."""
        return ValidationResult(
            total_candidates=3,
            passed_validation=3,
            failed_validation=0,
            average_sharpe_ratio=1.5,
            average_sortino_ratio=1.8,
            average_max_drawdown=-0.15,
            backtest_period_years=5,
            market_regimes_tested=["bull", "bear", "sideways"],
            validation_details=[
                {
                    "symbol": "AAPL",
                    "annualized_return": 15.0,
                    "sharpe_ratio": 1.6,
                    "max_drawdown": -0.12,
                    "win_rate": 0.65,
                },
                {
                    "symbol": "MSFT",
                    "annualized_return": 18.0,
                    "sharpe_ratio": 1.8,
                    "max_drawdown": -0.10,
                    "win_rate": 0.70,
                },
                {
                    "symbol": "GOOGL",
                    "annualized_return": 12.0,
                    "sharpe_ratio": 1.2,
                    "max_drawdown": -0.18,
                    "win_rate": 0.60,
                },
            ],
        )

    @pytest.fixture
    def asset_type_map(self):
        """Create asset type mapping."""
        return {"AAPL": "stock", "MSFT": "stock", "GOOGL": "stock", "QQQ": "etf", "BTC": "crypto"}

    def test_should_initialize_aggregator(self, mock_backtesting_extractor):
        """Test aggregator initialization."""
        aggregator = PerformanceMetricsAggregator(mock_backtesting_extractor)

        assert aggregator.backtesting_extractor == mock_backtesting_extractor
        assert aggregator.logger is not None

    def test_should_aggregate_by_asset_type_when_single_type(self, aggregator, sample_validation_result, asset_type_map):
        """Test aggregation by asset type with single asset type."""
        # Act
        result = aggregator.aggregate_by_asset_type([sample_validation_result], asset_type_map)

        # Assert
        assert "stock" in result
        assert "all" in result

        stock_metrics = result["stock"]
        assert stock_metrics.asset_type == "stock"
        assert stock_metrics.count == 3
        assert stock_metrics.average_return == pytest.approx(15.0, rel=0.1)  # (15+18+12)/3
        assert stock_metrics.average_sharpe == pytest.approx(1.53, rel=0.1)  # (1.6+1.8+1.2)/3
        assert stock_metrics.best_performer == "MSFT"  # Highest Sharpe
        assert stock_metrics.worst_performer == "GOOGL"  # Lowest Sharpe

    def test_should_aggregate_by_asset_type_when_multiple_types(self, aggregator, asset_type_map):
        """Test aggregation by asset type with multiple asset types."""
        # Arrange
        validation_results = [
            ValidationResult(
                total_candidates=2,
                passed_validation=2,
                failed_validation=0,
                average_sharpe_ratio=1.5,
                average_sortino_ratio=1.7,
                average_max_drawdown=-0.15,
                backtest_period_years=5,
                market_regimes_tested=["bull", "bear"],
                validation_details=[
                    {
                        "symbol": "AAPL",
                        "annualized_return": 15.0,
                        "sharpe_ratio": 1.6,
                        "max_drawdown": -0.12,
                        "win_rate": 0.65,
                    },
                    {
                        "symbol": "QQQ",
                        "annualized_return": 12.0,
                        "sharpe_ratio": 1.4,
                        "max_drawdown": -0.10,
                        "win_rate": 0.60,
                    },
                ],
            )
        ]

        # Act
        result = aggregator.aggregate_by_asset_type(validation_results, asset_type_map)

        # Assert
        assert "stock" in result
        assert "etf" in result
        assert "all" in result

        assert result["stock"].count == 1
        assert result["etf"].count == 1
        assert result["all"].count == 2

    def test_should_handle_empty_validation_results_for_asset_type(self, aggregator, asset_type_map):
        """Test aggregation with empty validation results."""
        # Act
        result = aggregator.aggregate_by_asset_type([], asset_type_map)

        # Assert
        assert result == {}

    def test_should_aggregate_by_regime_when_multiple_regimes(self, aggregator, mock_backtesting_extractor, sample_validation_result):
        """Test aggregation by market regime."""
        # Arrange
        mock_regime_perf = {
            "bull": RegimePerformance(
                regime_type="bull",
                annualized_return=20.0,
                sharpe_ratio=1.8,
                max_drawdown=-0.10,
                win_rate=0.75,
                consistency_score=0.85,
            ),
            "bear": RegimePerformance(
                regime_type="bear",
                annualized_return=5.0,
                sharpe_ratio=0.8,
                max_drawdown=-0.25,
                win_rate=0.45,
                consistency_score=0.60,
            ),
        }
        mock_backtesting_extractor.extract_regime_performance.return_value = mock_regime_perf

        # Act
        result = aggregator.aggregate_by_regime([sample_validation_result])

        # Assert
        assert "bull" in result
        assert "bear" in result

        bull_metrics = result["bull"]
        assert bull_metrics.count == 1
        assert bull_metrics.average_return == approx(20.0)
        assert bull_metrics.average_sharpe == approx(1.8)

        bear_metrics = result["bear"]
        assert bear_metrics.count == 1
        assert bear_metrics.average_return == approx(5.0)
        assert bear_metrics.average_sharpe == approx(0.8)

    def test_should_handle_empty_validation_results_for_regime(self, aggregator):
        """Test regime aggregation with empty validation results."""
        # Act
        result = aggregator.aggregate_by_regime([])

        # Assert
        assert result == {}

    def test_should_calculate_portfolio_impact_when_high_quality_opportunities(self, aggregator, sample_validation_result):
        """Test portfolio impact calculation with high-quality opportunities."""
        # Act
        result = aggregator.calculate_portfolio_impact([sample_validation_result], current_portfolio_grade=0.70)

        # Assert
        assert isinstance(result, PortfolioImpactMetrics)
        assert result.total_opportunities == 3
        assert result.high_confidence_count == 2  # AAPL and MSFT have Sharpe > 1.5
        assert result.expected_grade_improvement > 0  # Should improve from 0.70
        assert result.expected_return_improvement > 0  # Should improve from baseline
        assert result.risk_impact == "reduced"  # High Sharpe ratios
        assert result.diversification_impact == "neutral"  # 3 opportunities
        assert result.implementation_complexity == "low"  # <= 3 opportunities

    def test_should_calculate_portfolio_impact_when_low_quality_opportunities(self, aggregator):
        """Test portfolio impact calculation with low-quality opportunities."""
        # Arrange
        low_quality_result = ValidationResult(
            total_candidates=1,
            passed_validation=1,
            failed_validation=0,
            average_sharpe_ratio=0.5,
            average_sortino_ratio=0.6,
            average_max_drawdown=-0.30,
            backtest_period_years=5,
            market_regimes_tested=["bull"],
            validation_details=[
                {
                    "symbol": "RISKY",
                    "annualized_return": 8.0,
                    "sharpe_ratio": 0.5,
                    "max_drawdown": -0.30,
                    "win_rate": 0.40,
                }
            ],
        )

        # Act
        result = aggregator.calculate_portfolio_impact([low_quality_result], current_portfolio_grade=0.70)

        # Assert
        assert result.total_opportunities == 1
        assert result.high_confidence_count == 0  # No Sharpe > 1.5
        assert result.risk_impact == "increased"  # Sharpe < 0.8
        assert result.diversification_impact == "reduced"  # Only 1 opportunity
        assert result.implementation_complexity == "low"

    def test_should_handle_empty_validation_results_for_portfolio_impact(self, aggregator):
        """Test portfolio impact calculation with empty validation results."""
        # Act
        result = aggregator.calculate_portfolio_impact([])

        # Assert
        assert result.total_opportunities == 0
        assert result.high_confidence_count == 0
        assert result.expected_grade_improvement == approx(0.0)
        assert result.expected_return_improvement == approx(0.0)
        assert result.risk_impact == "neutral"
        assert result.diversification_impact == "neutral"
        assert result.implementation_complexity == "low"

    def test_should_generate_comprehensive_performance_report(self, aggregator, mock_backtesting_extractor, sample_validation_result, asset_type_map):
        """Test comprehensive performance report generation."""
        # Arrange
        mock_regime_perf = {
            "bull": RegimePerformance(
                regime_type="bull",
                annualized_return=20.0,
                sharpe_ratio=1.8,
                max_drawdown=-0.10,
                win_rate=0.75,
                consistency_score=0.85,
            )
        }
        mock_backtesting_extractor.extract_regime_performance.return_value = mock_regime_perf

        # Act
        result = aggregator.generate_performance_report([sample_validation_result], asset_type_map, current_portfolio_grade=0.70)

        # Assert
        assert result.total_candidates_analyzed == 3
        assert len(result.by_asset_type) > 0
        assert len(result.by_regime) > 0
        assert isinstance(result.portfolio_impact, PortfolioImpactMetrics)
        assert len(result.top_opportunities) <= 5
        assert result.data_quality_score > 0
        assert isinstance(result.report_timestamp, datetime)

    def test_should_identify_top_opportunities_correctly(self, aggregator, mock_backtesting_extractor, sample_validation_result):
        """Test identification of top opportunities by composite score."""
        # Arrange - Mock regime performance to return empty dict
        mock_backtesting_extractor.extract_regime_performance.return_value = {}

        # Act
        result = aggregator.generate_performance_report([sample_validation_result], {"AAPL": "stock", "MSFT": "stock", "GOOGL": "stock"})

        # Assert
        assert len(result.top_opportunities) == 3  # Only 3 candidates
        # MSFT should be first (highest Sharpe * return composite)
        assert result.top_opportunities[0] == "MSFT"

    def test_should_calculate_data_quality_score_correctly(self, aggregator, mock_backtesting_extractor, sample_validation_result):
        """Test data quality score calculation."""
        # Arrange - Mock regime performance to return empty dict
        mock_backtesting_extractor.extract_regime_performance.return_value = {}

        # Act
        result = aggregator.generate_performance_report([sample_validation_result], {"AAPL": "stock", "MSFT": "stock", "GOOGL": "stock"})

        # Assert
        # High quality: all passed validation, complete data, multiple regimes
        assert result.data_quality_score > 0.8
        assert result.data_quality_score <= 1.0

    def test_should_handle_multiple_validation_results(self, aggregator, mock_backtesting_extractor, asset_type_map):
        """Test aggregation with multiple validation results."""
        # Arrange
        validation_results = [
            ValidationResult(
                total_candidates=2,
                passed_validation=2,
                failed_validation=0,
                average_sharpe_ratio=1.5,
                average_sortino_ratio=1.7,
                average_max_drawdown=-0.15,
                backtest_period_years=5,
                market_regimes_tested=["bull", "bear"],
                validation_details=[
                    {
                        "symbol": "AAPL",
                        "annualized_return": 15.0,
                        "sharpe_ratio": 1.6,
                        "max_drawdown": -0.12,
                        "win_rate": 0.65,
                    },
                    {
                        "symbol": "MSFT",
                        "annualized_return": 18.0,
                        "sharpe_ratio": 1.8,
                        "max_drawdown": -0.10,
                        "win_rate": 0.70,
                    },
                ],
            ),
            ValidationResult(
                total_candidates=1,
                passed_validation=1,
                failed_validation=0,
                average_sharpe_ratio=1.4,
                average_sortino_ratio=1.6,
                average_max_drawdown=-0.12,
                backtest_period_years=5,
                market_regimes_tested=["bull", "bear"],
                validation_details=[
                    {
                        "symbol": "QQQ",
                        "annualized_return": 12.0,
                        "sharpe_ratio": 1.4,
                        "max_drawdown": -0.10,
                        "win_rate": 0.60,
                    }
                ],
            ),
        ]

        mock_backtesting_extractor.extract_regime_performance.return_value = {}

        # Act
        result = aggregator.generate_performance_report(validation_results, asset_type_map)

        # Assert
        assert result.total_candidates_analyzed == 3
        assert "stock" in result.by_asset_type
        assert "etf" in result.by_asset_type

    def test_should_assess_implementation_complexity_correctly(self, aggregator):
        """Test implementation complexity assessment based on opportunity count."""
        # Test low complexity (1-3 opportunities)
        low_result = ValidationResult(
            total_candidates=2,
            passed_validation=2,
            failed_validation=0,
            average_sharpe_ratio=1.5,
            average_sortino_ratio=1.7,
            average_max_drawdown=-0.15,
            backtest_period_years=5,
            market_regimes_tested=["bull"],
            validation_details=[
                {"symbol": "A", "annualized_return": 15.0, "sharpe_ratio": 1.6, "max_drawdown": -0.12, "win_rate": 0.65},
                {"symbol": "B", "annualized_return": 18.0, "sharpe_ratio": 1.8, "max_drawdown": -0.10, "win_rate": 0.70},
            ],
        )

        impact = aggregator.calculate_portfolio_impact([low_result])
        assert impact.implementation_complexity == "low"

        # Test medium complexity (4-7 opportunities)
        medium_result = ValidationResult(
            total_candidates=5,
            passed_validation=5,
            failed_validation=0,
            average_sharpe_ratio=1.5,
            average_sortino_ratio=1.7,
            average_max_drawdown=-0.15,
            backtest_period_years=5,
            market_regimes_tested=["bull"],
            validation_details=[{"symbol": f"SYM{i}", "annualized_return": 15.0, "sharpe_ratio": 1.6, "max_drawdown": -0.12, "win_rate": 0.65} for i in range(5)],
        )

        impact = aggregator.calculate_portfolio_impact([medium_result])
        assert impact.implementation_complexity == "medium"

        # Test high complexity (8+ opportunities)
        high_result = ValidationResult(
            total_candidates=10,
            passed_validation=10,
            failed_validation=0,
            average_sharpe_ratio=1.5,
            average_sortino_ratio=1.7,
            average_max_drawdown=-0.15,
            backtest_period_years=5,
            market_regimes_tested=["bull"],
            validation_details=[{"symbol": f"SYM{i}", "annualized_return": 15.0, "sharpe_ratio": 1.6, "max_drawdown": -0.12, "win_rate": 0.65} for i in range(10)],
        )

        impact = aggregator.calculate_portfolio_impact([high_result])
        assert impact.implementation_complexity == "high"
