"""
Integration tests for portfolio rebalancing orchestrator.

Tests the complete workflow from portfolio configuration through
trade recommendations and report generation.
"""

import asyncio
from datetime import datetime

import pytest

from finwiz.orchestrators.portfolio_rebalancing import (
    InsufficientPriceDataError,
    OptimizationFailedError,
    PortfolioRebalancingError,
    PortfolioRebalancingOrchestrator,
)
from finwiz.quantitative.portfolio_analyzer import PortfolioAnalyzer
from finwiz.quantitative.rebalancing_engine import OptimizedTrades, RebalancingEngine
from finwiz.schemas.portfolio_rebalancing import (
    Holding,
    PortfolioAnalysis,
    PortfolioConfiguration,
    PriceData,
    RebalancingMethod,
    RebalancingRecommendation,
    TradeAction,
    TradeRecommendation,
    UrgencyLevel,
)
from finwiz.tools.html_report_generator import HTMLReportGenerator
from finwiz.tools.portfolio_price_service import PortfolioPriceService


class TestPortfolioRebalancingIntegration:
    """Integration tests for portfolio rebalancing orchestrator."""

    @pytest.fixture
    def sample_portfolio_config(self):
        """Create sample portfolio configuration for testing."""
        return PortfolioConfiguration(
            holdings=[
                Holding(symbol="AAPL", shares=100.0),
                Holding(symbol="GOOGL", shares=10.0),
                Holding(symbol="MSFT", shares=50.0),
            ],
            target_weights={"AAPL": 0.4, "GOOGL": 0.35, "MSFT": 0.25},
            tolerance_bands={"AAPL": 0.05, "GOOGL": 0.05, "MSFT": 0.05},
            global_tolerance=0.05,
            available_capital=5000.0,
            transaction_cost_rate=0.001,
            min_trade_size=100.0,
            rebalancing_method=RebalancingMethod.MINIMIZE_TRADES,
        )

    @pytest.fixture
    def sample_price_data(self):
        """Create sample price data for testing."""
        return {
            "AAPL": PriceData(symbol="AAPL", price=150.0, timestamp=datetime.now()),
            "GOOGL": PriceData(symbol="GOOGL", price=2500.0, timestamp=datetime.now()),
            "MSFT": PriceData(symbol="MSFT", price=300.0, timestamp=datetime.now()),
        }

    @pytest.fixture
    def sample_portfolio_analysis(self):
        """Create sample portfolio analysis for testing."""
        return PortfolioAnalysis(
            total_value=55000.0,
            weightings={"AAPL": 0.273, "GOOGL": 0.455, "MSFT": 0.273},
            deviations_from_target={"AAPL": -0.127, "GOOGL": 0.105, "MSFT": 0.023},
            positions_needing_rebalancing=["AAPL", "GOOGL"],
            risk_metrics={"concentration_risk": 6.5, "diversification_ratio": 0.75},
        )

    @pytest.fixture
    def sample_trade_recommendations(self):
        """Create sample trade recommendations for testing."""
        return [
            TradeRecommendation(
                symbol="AAPL",
                action=TradeAction.BUY,
                quantity=46.67,
                current_price=150.0,
                trade_value=7000.5,  # Fixed to match quantity × price
                estimated_commission=7.0,
                estimated_spread_cost=7.0,
                total_estimated_cost=14.0,
                current_weight=0.273,
                target_weight=0.4,
                weight_deviation=-0.127,
                projected_weight_after_trade=0.4,
                priority=1,
                urgency=UrgencyLevel.HIGH,
                rationale="Rebalance AAPL from 27.3% to 40.0%",
            ),
            TradeRecommendation(
                symbol="GOOGL",
                action=TradeAction.SELL,
                quantity=2.31,
                current_price=2500.0,
                trade_value=5775.0,
                estimated_commission=5.78,
                estimated_spread_cost=5.78,
                total_estimated_cost=11.56,
                current_weight=0.455,
                target_weight=0.35,
                weight_deviation=0.105,
                projected_weight_after_trade=0.35,
                priority=2,
                urgency=UrgencyLevel.MEDIUM,
                rationale="Rebalance GOOGL from 45.5% to 35.0%",
            ),
        ]

    @pytest.fixture
    def mock_price_service(self, mocker, sample_price_data):
        """Create mock price service."""
        mock_service = mocker.AsyncMock(spec=PortfolioPriceService)
        mock_service.get_current_prices.return_value = sample_price_data
        mock_service.get_price_with_fallback.return_value = sample_price_data["AAPL"]
        mock_service.close.return_value = None
        return mock_service

    @pytest.fixture
    def mock_portfolio_analyzer(self, mocker, sample_portfolio_analysis):
        """Create mock portfolio analyzer."""
        mock_analyzer = mocker.MagicMock(spec=PortfolioAnalyzer)
        mock_analyzer.analyze_current_portfolio.return_value = sample_portfolio_analysis
        mock_analyzer.identify_rebalancing_needs.return_value = []
        return mock_analyzer

    @pytest.fixture
    def mock_rebalancing_engine(self, mocker, sample_trade_recommendations):
        """Create mock rebalancing engine."""
        mock_engine = mocker.MagicMock(spec=RebalancingEngine)
        mock_engine.optimize_rebalancing_trades.return_value = OptimizedTrades(
            trades=sample_trade_recommendations,
            total_cost=25.56,
            capital_used=1225.0,
            constraints_violated=[],
            optimization_score=0.85,
            method_used="MINIMIZE_TRADES",
        )
        # Mock the new enhanced recommendations method
        mock_engine.generate_enhanced_trade_recommendations.return_value = (
            sample_trade_recommendations,
            [],  # recommendations, validation_errors
        )
        return mock_engine

    @pytest.fixture
    def mock_report_generator(self, mocker):
        """Create mock report generator."""
        mock_generator = mocker.MagicMock(spec=HTMLReportGenerator)
        mock_generator.generate_html.return_value = "<html><body>Test Report</body></html>"
        mock_generator.clear_sections.return_value = None
        mock_generator.add_section.return_value = None
        return mock_generator

    @pytest.fixture
    def orchestrator(self, mock_price_service, mock_portfolio_analyzer, mock_rebalancing_engine, mock_report_generator):
        """Create orchestrator with mocked dependencies."""
        return PortfolioRebalancingOrchestrator(
            price_service=mock_price_service,
            portfolio_analyzer=mock_portfolio_analyzer,
            rebalancing_engine=mock_rebalancing_engine,
            report_generator=mock_report_generator,
        )

    @pytest.mark.asyncio
    async def test_should_complete_full_rebalancing_workflow_when_valid_input_provided(
        self, orchestrator, sample_portfolio_config, mock_price_service, mock_portfolio_analyzer, mock_rebalancing_engine, mocker
    ):
        """Test complete rebalancing workflow with valid inputs."""
        # Act
        result = await orchestrator.rebalance_portfolio(sample_portfolio_config, portfolio_id="test-portfolio")

        # Assert
        assert result is not None
        assert result.portfolio_id == "test-portfolio"
        assert result.current_portfolio.total_value == 55000.0
        assert len(result.trade_recommendations) == 2
        assert result.cost_analysis.total_transaction_costs > 0
        assert result.execution_summary.total_trades_required == 2
        assert result.overall_recommendation in [
            RebalancingRecommendation.REBALANCE_NOW,
            RebalancingRecommendation.REBALANCE_SOON,
            RebalancingRecommendation.MONITOR,
            RebalancingRecommendation.NO_ACTION,
        ]

        # Verify all components were called
        mock_price_service.get_current_prices.assert_called_once()
        mock_portfolio_analyzer.analyze_current_portfolio.assert_called_once()
        mock_rebalancing_engine.generate_enhanced_trade_recommendations.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_handle_missing_price_data_gracefully(
        self, orchestrator, sample_portfolio_config, mock_price_service, mocker
    ):
        """Test handling of missing price data with fallback."""
        # Arrange
        mock_price_service.get_current_prices.return_value = {
            "AAPL": PriceData(symbol="AAPL", price=150.0, timestamp=datetime.now())
        }
        mock_price_service.get_price_with_fallback.side_effect = [
            PriceData(symbol="GOOGL", price=2500.0, timestamp=datetime.now()),
            PriceData(symbol="MSFT", price=300.0, timestamp=datetime.now()),
        ]

        # Act
        result = await orchestrator.rebalance_portfolio(sample_portfolio_config)

        # Assert
        assert result is not None
        assert mock_price_service.get_price_with_fallback.call_count == 2

    @pytest.mark.asyncio
    async def test_should_raise_error_when_price_data_unavailable(
        self, orchestrator, sample_portfolio_config, mock_price_service, mocker
    ):
        """Test error handling when price data is completely unavailable."""
        # Arrange
        mock_price_service.get_current_prices.return_value = {}
        mock_price_service.get_price_with_fallback.side_effect = Exception("Price data unavailable")

        # Act & Assert
        with pytest.raises(InsufficientPriceDataError) as exc_info:
            await orchestrator.rebalance_portfolio(sample_portfolio_config)

        assert "AAPL" in str(exc_info.value)
        assert "GOOGL" in str(exc_info.value)
        assert "MSFT" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_should_handle_optimization_failure_gracefully(
        self, orchestrator, sample_portfolio_config, mock_rebalancing_engine, mocker
    ):
        """Test handling of optimization failures."""
        # Arrange
        mock_rebalancing_engine.optimize_rebalancing_trades.side_effect = Exception("Optimization failed")

        # Act & Assert
        with pytest.raises(OptimizationFailedError) as exc_info:
            await orchestrator.rebalance_portfolio(sample_portfolio_config)

        assert "Optimization failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_should_generate_html_report_successfully(
        self, orchestrator, sample_portfolio_config, mock_report_generator, mocker
    ):
        """Test HTML report generation."""
        # Arrange
        result = await orchestrator.rebalance_portfolio(sample_portfolio_config)

        # Act
        html_report = await orchestrator.generate_rebalancing_report(result, language="en")

        # Assert
        assert html_report == "<html><body>Test Report</body></html>"
        mock_report_generator.clear_sections.assert_called_once()
        assert mock_report_generator.add_section.call_count >= 5  # At least 5 sections
        mock_report_generator.generate_html.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_generate_french_report_when_requested(
        self, orchestrator, sample_portfolio_config, mock_report_generator, mocker
    ):
        """Test French report generation."""
        # Arrange
        result = await orchestrator.rebalance_portfolio(sample_portfolio_config)

        # Act
        html_report = await orchestrator.generate_rebalancing_report(result, language="fr")

        # Assert
        assert html_report == "<html><body>Test Report</body></html>"
        # Verify French language was passed to generator
        args, kwargs = mock_report_generator.generate_html.call_args
        assert kwargs["language"] == "fr"
        assert "Portfolio Rebalancing Analysis" in kwargs["title"]

    @pytest.mark.asyncio
    async def test_should_analyze_portfolio_without_trades(self, orchestrator, sample_portfolio_config, mocker):
        """Test portfolio analysis without generating trades."""
        # Act
        analysis = await orchestrator.analyze_current_portfolio(sample_portfolio_config)

        # Assert
        assert analysis is not None
        assert analysis.total_value == 55000.0
        assert len(analysis.weightings) == 3

    @pytest.mark.asyncio
    async def test_should_handle_empty_trade_recommendations(
        self, orchestrator, sample_portfolio_config, mock_rebalancing_engine, mocker
    ):
        """Test handling when no trades are recommended."""
        # Arrange
        mock_rebalancing_engine.optimize_rebalancing_trades.return_value = OptimizedTrades(
            trades=[],
            total_cost=0.0,
            capital_used=0.0,
            constraints_violated=[],
            optimization_score=1.0,
            method_used="MINIMIZE_TRADES",
        )

        # Act
        result = await orchestrator.rebalance_portfolio(sample_portfolio_config)

        # Assert
        assert result is not None
        assert len(result.trade_recommendations) == 0
        assert result.execution_summary.total_trades_required == 0
        assert result.cost_analysis.total_transaction_costs == 0.0
        assert result.overall_recommendation == RebalancingRecommendation.NO_ACTION

    @pytest.mark.asyncio
    async def test_should_handle_high_urgency_positions(
        self, orchestrator, sample_portfolio_config, mock_portfolio_analyzer, mocker
    ):
        """Test handling of high urgency rebalancing needs."""
        # Arrange
        from finwiz.schemas.portfolio_rebalancing import RebalancingNeed

        high_urgency_needs = [
            RebalancingNeed(
                symbol="AAPL",
                current_weight=0.1,
                target_weight=0.4,
                deviation=-0.3,
                tolerance_band=0.05,
                exceeds_tolerance=True,
                urgency_score=0.9,  # High urgency
                recommended_action=TradeAction.BUY,
            )
        ]
        mock_portfolio_analyzer.identify_rebalancing_needs.return_value = high_urgency_needs

        # Act
        result = await orchestrator.rebalance_portfolio(sample_portfolio_config)

        # Assert
        assert result.overall_recommendation == RebalancingRecommendation.REBALANCE_NOW

    @pytest.mark.asyncio
    async def test_should_handle_high_transaction_costs(
        self, orchestrator, sample_portfolio_config, mock_rebalancing_engine, mocker
    ):
        """Test handling when transaction costs are high relative to portfolio."""
        # Arrange
        mock_rebalancing_engine.optimize_rebalancing_trades.return_value = OptimizedTrades(
            trades=[
                TradeRecommendation(
                    symbol="AAPL",
                    action=TradeAction.BUY,
                    quantity=100.0,
                    current_price=150.0,
                    trade_value=15000.0,
                    estimated_commission=750.0,  # High cost
                    estimated_spread_cost=150.0,
                    total_estimated_cost=900.0,  # Very high total cost
                    current_weight=0.273,
                    target_weight=0.4,
                    weight_deviation=-0.127,
                    projected_weight_after_trade=0.4,
                    priority=1,
                    urgency=UrgencyLevel.LOW,
                    rationale="High cost trade",
                )
            ],
            total_cost=900.0,
            capital_used=15000.0,
            constraints_violated=[],
            optimization_score=0.5,
            method_used="MINIMIZE_TRADES",
        )

        # Act
        result = await orchestrator.rebalance_portfolio(sample_portfolio_config)

        # Assert
        assert result.cost_analysis.cost_as_percentage > 1.0  # High cost percentage
        assert result.overall_recommendation == RebalancingRecommendation.MONITOR

    @pytest.mark.asyncio
    async def test_should_handle_concurrent_operations(self, orchestrator, sample_portfolio_config, mocker):
        """Test handling of concurrent rebalancing operations."""
        # Act - Run multiple rebalancing operations concurrently
        tasks = [orchestrator.rebalance_portfolio(sample_portfolio_config) for _ in range(3)]
        results = await asyncio.gather(*tasks)

        # Assert
        assert len(results) == 3
        for result in results:
            assert result is not None
            assert result.current_portfolio.total_value == 55000.0

    @pytest.mark.asyncio
    async def test_should_cleanup_resources_properly(self, orchestrator, mock_price_service, mocker):
        """Test proper resource cleanup."""
        # Act
        await orchestrator.close()

        # Assert
        mock_price_service.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_handle_portfolio_analysis_error(
        self, orchestrator, sample_portfolio_config, mock_portfolio_analyzer, mocker
    ):
        """Test handling of portfolio analysis errors."""
        # Arrange
        from finwiz.quantitative.portfolio_analyzer import PortfolioAnalysisError

        mock_portfolio_analyzer.analyze_current_portfolio.side_effect = PortfolioAnalysisError("Analysis failed")

        # Act & Assert
        with pytest.raises(PortfolioRebalancingError) as exc_info:
            await orchestrator.rebalance_portfolio(sample_portfolio_config)

        assert "Analysis failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_should_validate_portfolio_configuration(self, orchestrator, mocker):
        """Test validation of invalid portfolio configuration."""
        # Arrange - Invalid configuration with mismatched holdings and targets
        PortfolioConfiguration(
            holdings=[Holding(symbol="AAPL", shares=100.0)],
            target_weights={"AAPL": 0.5, "GOOGL": 0.5},  # GOOGL not in holdings
        )

        # Act & Assert
        with pytest.raises(ValueError):  # Should raise validation error during config creation
            pass  # The error is raised during config creation above

    @pytest.mark.asyncio
    async def test_should_handle_different_rebalancing_methods(self, orchestrator, sample_portfolio_config, mocker):
        """Test different rebalancing methods."""
        # Test MINIMIZE_COSTS method
        sample_portfolio_config.rebalancing_method = RebalancingMethod.MINIMIZE_COSTS
        result_costs = await orchestrator.rebalance_portfolio(sample_portfolio_config)

        # Test RISK_AWARE method
        sample_portfolio_config.rebalancing_method = RebalancingMethod.RISK_AWARE
        result_risk = await orchestrator.rebalance_portfolio(sample_portfolio_config)

        # Assert
        assert result_costs is not None
        assert result_risk is not None
        # Both should produce valid results
        assert result_costs.execution_summary.total_trades_required >= 0
        assert result_risk.execution_summary.total_trades_required >= 0

    @pytest.mark.asyncio
    async def test_should_handle_large_portfolio(self, orchestrator, mocker):
        """Test handling of large portfolio with many positions."""
        # Arrange - Create large portfolio
        holdings = [Holding(symbol=f"STOCK{i:03d}", shares=100.0) for i in range(50)]
        target_weights = {f"STOCK{i:03d}": 0.02 for i in range(50)}  # Equal weights

        large_config = PortfolioConfiguration(holdings=holdings, target_weights=target_weights)

        # Mock price service to return prices for all symbols
        orchestrator.price_service.get_current_prices = mocker.AsyncMock(
            return_value={
                f"STOCK{i:03d}": PriceData(symbol=f"STOCK{i:03d}", price=100.0, timestamp=datetime.now()) for i in range(50)
            }
        )

        # Act
        result = await orchestrator.rebalance_portfolio(large_config)

        # Assert
        assert result is not None
        assert len(result.current_portfolio.weightings) == 50

    @pytest.mark.asyncio
    async def test_should_calculate_risk_scores_correctly(self, orchestrator, sample_portfolio_config):
        """Test risk score calculations."""
        # Act
        result = await orchestrator.rebalance_portfolio(sample_portfolio_config)

        # Assert
        assert 0.0 <= result.current_risk_score <= 10.0
        assert 0.0 <= result.projected_risk_score <= 10.0
        assert result.risk_improvement == result.current_risk_score - result.projected_risk_score

    @pytest.mark.asyncio
    async def test_should_handle_zero_available_capital(self, orchestrator, sample_portfolio_config):
        """Test handling when no additional capital is available."""
        # Arrange
        sample_portfolio_config.available_capital = 0.0

        # Act
        result = await orchestrator.rebalance_portfolio(sample_portfolio_config)

        # Assert
        assert result is not None
        # Should still be able to rebalance by selling overweight positions to buy underweight ones
        assert result.execution_summary.capital_required <= 0.0  # Should not require additional capital

    @pytest.mark.asyncio
    async def test_should_handle_negative_available_capital(self, orchestrator, sample_portfolio_config):
        """Test handling when capital needs to be withdrawn."""
        # Arrange
        sample_portfolio_config.available_capital = -5000.0  # Need to withdraw money

        # Act
        result = await orchestrator.rebalance_portfolio(sample_portfolio_config)

        # Assert
        assert result is not None
        # Should handle withdrawal requirement
        assert result.execution_summary.capital_required <= 0.0

    @pytest.mark.asyncio
    async def test_should_generate_execution_summary_correctly(self, orchestrator, sample_portfolio_config):
        """Test execution summary generation."""
        # Act
        result = await orchestrator.rebalance_portfolio(sample_portfolio_config)

        # Assert
        summary = result.execution_summary
        assert summary.total_trades_required >= 0
        assert summary.positions_requiring_action >= 0
        assert summary.positions_within_tolerance >= 0
        assert summary.estimated_execution_time is not None
        assert isinstance(summary.capital_required, (int, float))

        # Verify totals make sense
        total_positions = len(sample_portfolio_config.holdings)
        assert summary.positions_requiring_action + summary.positions_within_tolerance <= total_positions
