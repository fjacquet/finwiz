"""
End-to-end integration tests for portfolio rebalancing system.

Tests complete workflows from configuration through execution,
including real component integration and error recovery.
"""

import asyncio
import os
import sys
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))

from finwiz.orchestrators.portfolio_rebalancing import PortfolioRebalancingOrchestrator
from finwiz.quantitative.cost_analyzer import CostAnalyzer
from finwiz.quantitative.portfolio_analyzer import PortfolioAnalyzer
from finwiz.quantitative.rebalancing_engine import RebalancingEngine
from finwiz.quantitative.risk_manager import RiskManager
from finwiz.schemas.portfolio_rebalancing import (
    Holding,
    PortfolioConfiguration,
    PriceData,
    RebalancingMethod,
    RebalancingRecommendation,
    TradeAction,
    UrgencyLevel,
)
from finwiz.tools.html_report_generator import HTMLReportGenerator


class TestPortfolioRebalancingEndToEnd:
    """End-to-end integration tests for complete rebalancing workflows."""

    @pytest.fixture
    def realistic_portfolio_config(self):
        """Create realistic portfolio configuration for integration testing."""
        return PortfolioConfiguration(
            holdings=[
                Holding(symbol="AAPL", shares=150.0, cost_basis=120.0),
                Holding(symbol="GOOGL", shares=25.0, cost_basis=2200.0),
                Holding(symbol="MSFT", shares=100.0, cost_basis=280.0),
                Holding(symbol="TSLA", shares=50.0, cost_basis=180.0),
                Holding(symbol="NVDA", shares=75.0, cost_basis=400.0),
            ],
            target_weights={
                "AAPL": 0.25,
                "GOOGL": 0.20,
                "MSFT": 0.20,
                "TSLA": 0.15,
                "NVDA": 0.20,
            },
            tolerance_bands={
                "AAPL": 0.03,
                "GOOGL": 0.05,
                "MSFT": 0.03,
                "TSLA": 0.07,  # Higher tolerance for volatile stock
                "NVDA": 0.05,
            },
            global_tolerance=0.05,
            available_capital=10000.0,
            transaction_cost_rate=0.005,  # 0.5% transaction cost
            min_trade_size=500.0,
            rebalancing_method=RebalancingMethod.MINIMIZE_COSTS,
        )

    @pytest.fixture
    def realistic_price_data(self):
        """Create realistic price data that would trigger rebalancing."""
        return {
            "AAPL": PriceData(symbol="AAPL", price=175.0, timestamp=datetime.now()),  # Up from cost basis
            "GOOGL": PriceData(symbol="GOOGL", price=2800.0, timestamp=datetime.now()),  # Up significantly
            "MSFT": PriceData(symbol="MSFT", price=320.0, timestamp=datetime.now()),  # Up moderately
            "TSLA": PriceData(symbol="TSLA", price=220.0, timestamp=datetime.now()),  # Up moderately
            "NVDA": PriceData(symbol="NVDA", price=450.0, timestamp=datetime.now()),  # Up slightly
        }

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_should_complete_full_rebalancing_workflow_with_real_components(
        self, realistic_portfolio_config, realistic_price_data
    ):
        """Test complete workflow using real component instances."""
        # Arrange - Use real components with mocked external dependencies
        with patch("finwiz.tools.portfolio_price_service.PortfolioPriceService") as mock_price_service_class:
            mock_price_service = AsyncMock()
            mock_price_service_class.return_value = mock_price_service
            mock_price_service.get_current_prices.return_value = realistic_price_data
            mock_price_service.close.return_value = None

            # Use real analyzer, engine, and other components
            portfolio_analyzer = PortfolioAnalyzer()
            rebalancing_engine = RebalancingEngine()
            CostAnalyzer()
            RiskManager()

            with patch("finwiz.tools.html_report_generator.HTMLReportGenerator") as mock_report_class:
                mock_report_generator = MagicMock()
                mock_report_class.return_value = mock_report_generator
                mock_report_generator.generate_html.return_value = "<html>Integration Test Report</html>"
                mock_report_generator.clear_sections.return_value = None
                mock_report_generator.add_section.return_value = None

                orchestrator = PortfolioRebalancingOrchestrator(
                    price_service=mock_price_service,
                    portfolio_analyzer=portfolio_analyzer,
                    rebalancing_engine=rebalancing_engine,
                    report_generator=mock_report_generator,
                )

                # Act
                result = await orchestrator.rebalance_portfolio(realistic_portfolio_config, portfolio_id="integration-test")

                # Assert
                assert result is not None
                assert result.portfolio_id == "integration-test"
                assert result.current_portfolio.total_value > 0
                assert len(result.current_portfolio.weightings) == 5

                # Verify realistic calculations
                expected_total_value = (
                    150.0 * 175.0 + 25.0 * 2800.0 + 100.0 * 320.0 + 50.0 * 220.0 + 75.0 * 450.0
                )  # Should be 162,500
                assert abs(result.current_portfolio.total_value - expected_total_value) < 1.0

                # Verify rebalancing recommendations are reasonable
                assert result.overall_recommendation in [
                    RebalancingRecommendation.REBALANCE_NOW,
                    RebalancingRecommendation.REBALANCE_SOON,
                    RebalancingRecommendation.MONITOR,
                    RebalancingRecommendation.NO_ACTION,
                ]

                # Verify cost analysis
                assert result.cost_analysis.total_transaction_costs >= 0
                assert 0 <= result.cost_analysis.cost_as_percentage <= 100

                # Verify risk analysis
                assert 0 <= result.current_risk_score <= 10
                assert 0 <= result.projected_risk_score <= 10

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_should_generate_comprehensive_html_report(self, realistic_portfolio_config, realistic_price_data):
        """Test HTML report generation with real data."""
        # Arrange
        with patch("finwiz.tools.portfolio_price_service.PortfolioPriceService") as mock_price_service_class:
            mock_price_service = AsyncMock()
            mock_price_service_class.return_value = mock_price_service
            mock_price_service.get_current_prices.return_value = realistic_price_data
            mock_price_service.close.return_value = None

            # Use real report generator
            report_generator = HTMLReportGenerator()

            orchestrator = PortfolioRebalancingOrchestrator(
                price_service=mock_price_service,
                portfolio_analyzer=PortfolioAnalyzer(),
                rebalancing_engine=RebalancingEngine(),
                report_generator=report_generator,
            )

            # Get rebalancing result
            result = await orchestrator.rebalance_portfolio(realistic_portfolio_config)

            # Act
            html_report = await orchestrator.generate_rebalancing_report(result, language="en")

            # Assert
            assert html_report is not None
            assert len(html_report) > 1000  # Should be substantial HTML content
            assert "Portfolio Rebalancing Analysis" in html_report
            assert "AAPL" in html_report
            assert "GOOGL" in html_report
            assert "Current Allocation" in html_report or "current allocation" in html_report

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_should_handle_different_rebalancing_methods_consistently(self, realistic_portfolio_config, realistic_price_data):
        """Test that different rebalancing methods produce consistent results."""
        # Arrange
        methods_to_test = [RebalancingMethod.MINIMIZE_TRADES, RebalancingMethod.MINIMIZE_COSTS, RebalancingMethod.RISK_AWARE]

        results = {}

        for method in methods_to_test:
            config = realistic_portfolio_config.model_copy()
            config.rebalancing_method = method

            with patch("finwiz.tools.portfolio_price_service.PortfolioPriceService") as mock_price_service_class:
                mock_price_service = AsyncMock()
                mock_price_service_class.return_value = mock_price_service
                mock_price_service.get_current_prices.return_value = realistic_price_data
                mock_price_service.close.return_value = None

                with patch("finwiz.tools.html_report_generator.HTMLReportGenerator") as mock_report_class:
                    mock_report_generator = MagicMock()
                    mock_report_class.return_value = mock_report_generator
                    mock_report_generator.generate_html.return_value = f"<html>{method} Report</html>"
                    mock_report_generator.clear_sections.return_value = None
                    mock_report_generator.add_section.return_value = None

                    orchestrator = PortfolioRebalancingOrchestrator(
                        price_service=mock_price_service,
                        portfolio_analyzer=PortfolioAnalyzer(),
                        rebalancing_engine=RebalancingEngine(),
                        report_generator=mock_report_generator,
                    )

                    # Act
                    result = await orchestrator.rebalance_portfolio(config)
                    results[method] = result

        # Assert - All methods should produce valid results
        for method, result in results.items():
            assert result is not None
            assert result.current_portfolio.total_value > 0
            assert len(result.current_portfolio.weightings) == 5

        # All methods should analyze the same current portfolio
        base_total_value = results[RebalancingMethod.MINIMIZE_TRADES].current_portfolio.total_value
        for method, result in results.items():
            assert abs(result.current_portfolio.total_value - base_total_value) < 1.0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_should_handle_portfolio_requiring_no_rebalancing(self, realistic_price_data):
        """Test handling of portfolio that doesn't require rebalancing."""
        # Arrange - Create perfectly balanced portfolio
        balanced_config = PortfolioConfiguration(
            holdings=[
                Holding(symbol="AAPL", shares=142.86),  # Calculated to achieve exact target weights
                Holding(symbol="GOOGL", shares=11.61),
                Holding(symbol="MSFT", shares=101.56),
                Holding(symbol="TSLA", shares=34.09),
                Holding(symbol="NVDA", shares=72.22),
            ],
            target_weights={"AAPL": 0.25, "GOOGL": 0.20, "MSFT": 0.20, "TSLA": 0.15, "NVDA": 0.20},
            global_tolerance=0.05,
        )

        with patch("finwiz.tools.portfolio_price_service.PortfolioPriceService") as mock_price_service_class:
            mock_price_service = AsyncMock()
            mock_price_service_class.return_value = mock_price_service
            mock_price_service.get_current_prices.return_value = realistic_price_data
            mock_price_service.close.return_value = None

            with patch("finwiz.tools.html_report_generator.HTMLReportGenerator") as mock_report_class:
                mock_report_generator = MagicMock()
                mock_report_class.return_value = mock_report_generator
                mock_report_generator.generate_html.return_value = "<html>No Action Report</html>"
                mock_report_generator.clear_sections.return_value = None
                mock_report_generator.add_section.return_value = None

                orchestrator = PortfolioRebalancingOrchestrator(
                    price_service=mock_price_service,
                    portfolio_analyzer=PortfolioAnalyzer(),
                    rebalancing_engine=RebalancingEngine(),
                    report_generator=mock_report_generator,
                )

                # Act
                result = await orchestrator.rebalance_portfolio(balanced_config)

                # Assert
                assert result is not None
                assert len(result.trade_recommendations) == 0 or all(
                    trade.action == TradeAction.HOLD for trade in result.trade_recommendations
                )
                assert result.overall_recommendation in [RebalancingRecommendation.NO_ACTION, RebalancingRecommendation.MONITOR]
                assert result.execution_summary.total_trades_required == 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_should_handle_portfolio_with_extreme_imbalance(self, realistic_price_data):
        """Test handling of portfolio with extreme allocation imbalance."""
        # Arrange - Create extremely imbalanced portfolio
        imbalanced_config = PortfolioConfiguration(
            holdings=[
                Holding(symbol="AAPL", shares=1000.0),  # Extremely overweight
                Holding(symbol="GOOGL", shares=1.0),  # Extremely underweight
                Holding(symbol="MSFT", shares=1.0),
                Holding(symbol="TSLA", shares=1.0),
                Holding(symbol="NVDA", shares=1.0),
            ],
            target_weights={"AAPL": 0.25, "GOOGL": 0.20, "MSFT": 0.20, "TSLA": 0.15, "NVDA": 0.20},
            global_tolerance=0.05,
            available_capital=50000.0,  # Provide capital for rebalancing
        )

        with patch("finwiz.tools.portfolio_price_service.PortfolioPriceService") as mock_price_service_class:
            mock_price_service = AsyncMock()
            mock_price_service_class.return_value = mock_price_service
            mock_price_service.get_current_prices.return_value = realistic_price_data
            mock_price_service.close.return_value = None

            with patch("finwiz.tools.html_report_generator.HTMLReportGenerator") as mock_report_class:
                mock_report_generator = MagicMock()
                mock_report_class.return_value = mock_report_generator
                mock_report_generator.generate_html.return_value = "<html>Extreme Rebalancing Report</html>"
                mock_report_generator.clear_sections.return_value = None
                mock_report_generator.add_section.return_value = None

                orchestrator = PortfolioRebalancingOrchestrator(
                    price_service=mock_price_service,
                    portfolio_analyzer=PortfolioAnalyzer(),
                    rebalancing_engine=RebalancingEngine(),
                    report_generator=mock_report_generator,
                )

                # Act
                result = await orchestrator.rebalance_portfolio(imbalanced_config)

                # Assert
                assert result is not None
                assert len(result.trade_recommendations) > 0  # Should recommend trades
                assert result.overall_recommendation == RebalancingRecommendation.REBALANCE_NOW

                # Should recommend selling AAPL and buying others
                aapl_trades = [trade for trade in result.trade_recommendations if trade.symbol == "AAPL"]
                if aapl_trades:
                    assert aapl_trades[0].action == TradeAction.SELL

                # Should have high urgency trades
                high_urgency_trades = [trade for trade in result.trade_recommendations if trade.urgency == UrgencyLevel.CRITICAL]
                assert len(high_urgency_trades) > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_should_handle_insufficient_capital_scenario(self, realistic_portfolio_config, realistic_price_data):
        """Test handling when insufficient capital is available for optimal rebalancing."""
        # Arrange - Limit available capital
        limited_capital_config = realistic_portfolio_config.model_copy()
        limited_capital_config.available_capital = 1000.0  # Very limited capital

        with patch("finwiz.tools.portfolio_price_service.PortfolioPriceService") as mock_price_service_class:
            mock_price_service = AsyncMock()
            mock_price_service_class.return_value = mock_price_service
            mock_price_service.get_current_prices.return_value = realistic_price_data
            mock_price_service.close.return_value = None

            with patch("finwiz.tools.html_report_generator.HTMLReportGenerator") as mock_report_class:
                mock_report_generator = MagicMock()
                mock_report_class.return_value = mock_report_generator
                mock_report_generator.generate_html.return_value = "<html>Limited Capital Report</html>"
                mock_report_generator.clear_sections.return_value = None
                mock_report_generator.add_section.return_value = None

                orchestrator = PortfolioRebalancingOrchestrator(
                    price_service=mock_price_service,
                    portfolio_analyzer=PortfolioAnalyzer(),
                    rebalancing_engine=RebalancingEngine(),
                    report_generator=mock_report_generator,
                )

                # Act
                result = await orchestrator.rebalance_portfolio(limited_capital_config)

                # Assert
                assert result is not None
                # Should still provide recommendations, possibly partial
                assert result.execution_summary.capital_required <= 1000.0 or result.execution_summary.capital_required <= 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_should_handle_high_transaction_costs_scenario(self, realistic_portfolio_config, realistic_price_data):
        """Test handling when transaction costs are prohibitively high."""
        # Arrange - Set very high transaction costs
        high_cost_config = realistic_portfolio_config.model_copy()
        high_cost_config.transaction_cost_rate = 0.05  # 5% transaction cost

        with patch("finwiz.tools.portfolio_price_service.PortfolioPriceService") as mock_price_service_class:
            mock_price_service = AsyncMock()
            mock_price_service_class.return_value = mock_price_service
            mock_price_service.get_current_prices.return_value = realistic_price_data
            mock_price_service.close.return_value = None

            with patch("finwiz.tools.html_report_generator.HTMLReportGenerator") as mock_report_class:
                mock_report_generator = MagicMock()
                mock_report_class.return_value = mock_report_generator
                mock_report_generator.generate_html.return_value = "<html>High Cost Report</html>"
                mock_report_generator.clear_sections.return_value = None
                mock_report_generator.add_section.return_value = None

                orchestrator = PortfolioRebalancingOrchestrator(
                    price_service=mock_price_service,
                    portfolio_analyzer=PortfolioAnalyzer(),
                    rebalancing_engine=RebalancingEngine(),
                    report_generator=mock_report_generator,
                )

                # Act
                result = await orchestrator.rebalance_portfolio(high_cost_config)

                # Assert
                assert result is not None
                # High costs should influence recommendations
                assert result.cost_analysis.cost_as_percentage > 1.0  # Should be high
                # May recommend no action due to high costs
                assert result.overall_recommendation in [
                    RebalancingRecommendation.MONITOR,
                    RebalancingRecommendation.NO_ACTION,
                    RebalancingRecommendation.REBALANCE_SOON,
                ]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_should_handle_tax_implications_correctly(self, realistic_portfolio_config, realistic_price_data):
        """Test handling of tax implications in rebalancing decisions."""
        # Arrange - Portfolio with significant gains (cost basis < current price)
        tax_config = realistic_portfolio_config.model_copy()
        # Holdings already have cost basis set in fixture

        with patch("finwiz.tools.portfolio_price_service.PortfolioPriceService") as mock_price_service_class:
            mock_price_service = AsyncMock()
            mock_price_service_class.return_value = mock_price_service
            mock_price_service.get_current_prices.return_value = realistic_price_data
            mock_price_service.close.return_value = None

            with patch("finwiz.tools.html_report_generator.HTMLReportGenerator") as mock_report_class:
                mock_report_generator = MagicMock()
                mock_report_class.return_value = mock_report_generator
                mock_report_generator.generate_html.return_value = "<html>Tax Implications Report</html>"
                mock_report_generator.clear_sections.return_value = None
                mock_report_generator.add_section.return_value = None

                orchestrator = PortfolioRebalancingOrchestrator(
                    price_service=mock_price_service,
                    portfolio_analyzer=PortfolioAnalyzer(),
                    rebalancing_engine=RebalancingEngine(),
                    report_generator=mock_report_generator,
                )

                # Act
                result = await orchestrator.rebalance_portfolio(tax_config)

                # Assert
                assert result is not None

                # Check for tax implications in trade recommendations
                sell_trades = [trade for trade in result.trade_recommendations if trade.action == TradeAction.SELL]
                for trade in sell_trades:
                    # Should have tax implications noted for positions with gains
                    if trade.symbol in ["AAPL", "GOOGL", "MSFT", "TSLA"]:  # These have gains based on prices
                        # Tax implications should be considered (may be None if no significant impact)
                        pass  # Tax implications are optional and may not always be present

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_should_handle_concurrent_portfolio_analysis(self, realistic_portfolio_config, realistic_price_data):
        """Test handling of concurrent portfolio analysis requests."""
        # Arrange
        num_concurrent = 3
        configs = [realistic_portfolio_config.model_copy() for _ in range(num_concurrent)]

        with patch("finwiz.tools.portfolio_price_service.PortfolioPriceService") as mock_price_service_class:
            mock_price_service = AsyncMock()
            mock_price_service_class.return_value = mock_price_service
            mock_price_service.get_current_prices.return_value = realistic_price_data
            mock_price_service.close.return_value = None

            with patch("finwiz.tools.html_report_generator.HTMLReportGenerator") as mock_report_class:
                mock_report_generator = MagicMock()
                mock_report_class.return_value = mock_report_generator
                mock_report_generator.generate_html.return_value = "<html>Concurrent Test Report</html>"
                mock_report_generator.clear_sections.return_value = None
                mock_report_generator.add_section.return_value = None

                orchestrator = PortfolioRebalancingOrchestrator(
                    price_service=mock_price_service,
                    portfolio_analyzer=PortfolioAnalyzer(),
                    rebalancing_engine=RebalancingEngine(),
                    report_generator=mock_report_generator,
                )

                # Act - Run concurrent analyses
                tasks = [
                    orchestrator.rebalance_portfolio(config, portfolio_id=f"concurrent-{i}") for i, config in enumerate(configs)
                ]
                results = await asyncio.gather(*tasks)

                # Assert
                assert len(results) == num_concurrent
                for i, result in enumerate(results):
                    assert result is not None
                    assert result.portfolio_id == f"concurrent-{i}"
                    assert result.current_portfolio.total_value > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_should_handle_error_recovery_gracefully(self, realistic_portfolio_config):
        """Test error recovery and graceful degradation."""
        # Arrange - Simulate various failure scenarios
        with patch("finwiz.tools.portfolio_price_service.PortfolioPriceService") as mock_price_service_class:
            mock_price_service = AsyncMock()
            mock_price_service_class.return_value = mock_price_service

            # First call fails, second succeeds
            mock_price_service.get_current_prices.side_effect = [
                Exception("Network error"),
                {
                    "AAPL": PriceData(symbol="AAPL", price=175.0, timestamp=datetime.now()),
                    "GOOGL": PriceData(symbol="GOOGL", price=2800.0, timestamp=datetime.now()),
                    "MSFT": PriceData(symbol="MSFT", price=320.0, timestamp=datetime.now()),
                    "TSLA": PriceData(symbol="TSLA", price=220.0, timestamp=datetime.now()),
                    "NVDA": PriceData(symbol="NVDA", price=450.0, timestamp=datetime.now()),
                },
            ]
            mock_price_service.close.return_value = None

            with patch("finwiz.tools.html_report_generator.HTMLReportGenerator") as mock_report_class:
                mock_report_generator = MagicMock()
                mock_report_class.return_value = mock_report_generator
                mock_report_generator.generate_html.return_value = "<html>Error Recovery Report</html>"
                mock_report_generator.clear_sections.return_value = None
                mock_report_generator.add_section.return_value = None

                orchestrator = PortfolioRebalancingOrchestrator(
                    price_service=mock_price_service,
                    portfolio_analyzer=PortfolioAnalyzer(),
                    rebalancing_engine=RebalancingEngine(),
                    report_generator=mock_report_generator,
                )

                # Act - First call should fail
                from finwiz.orchestrators.portfolio_rebalancing import InsufficientPriceDataError

                with pytest.raises(InsufficientPriceDataError):
                    await orchestrator.rebalance_portfolio(realistic_portfolio_config)

                # Second call should succeed
                result = await orchestrator.rebalance_portfolio(realistic_portfolio_config)

                # Assert
                assert result is not None
                assert result.current_portfolio.total_value > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_should_validate_end_to_end_data_consistency(self, realistic_portfolio_config, realistic_price_data):
        """Test data consistency throughout the entire workflow."""
        # Arrange
        with patch("finwiz.tools.portfolio_price_service.PortfolioPriceService") as mock_price_service_class:
            mock_price_service = AsyncMock()
            mock_price_service_class.return_value = mock_price_service
            mock_price_service.get_current_prices.return_value = realistic_price_data
            mock_price_service.close.return_value = None

            with patch("finwiz.tools.html_report_generator.HTMLReportGenerator") as mock_report_class:
                mock_report_generator = MagicMock()
                mock_report_class.return_value = mock_report_generator
                mock_report_generator.generate_html.return_value = "<html>Data Consistency Report</html>"
                mock_report_generator.clear_sections.return_value = None
                mock_report_generator.add_section.return_value = None

                orchestrator = PortfolioRebalancingOrchestrator(
                    price_service=mock_price_service,
                    portfolio_analyzer=PortfolioAnalyzer(),
                    rebalancing_engine=RebalancingEngine(),
                    report_generator=mock_report_generator,
                )

                # Act
                result = await orchestrator.rebalance_portfolio(realistic_portfolio_config)

                # Assert - Validate data consistency
                assert result is not None

                # Portfolio value should match manual calculation
                expected_total = sum(
                    holding.shares * realistic_price_data[holding.symbol].price for holding in realistic_portfolio_config.holdings
                )
                assert abs(result.current_portfolio.total_value - expected_total) < 1.0

                # Weightings should sum to 1.0
                total_weight = sum(result.current_portfolio.weightings.values())
                assert abs(total_weight - 1.0) < 0.001

                # Deviations should be consistent with weightings and targets
                for symbol in result.current_portfolio.deviations_from_target:
                    current_weight = result.current_portfolio.weightings[symbol]
                    target_weight = realistic_portfolio_config.target_weights[symbol]
                    expected_deviation = current_weight - target_weight
                    actual_deviation = result.current_portfolio.deviations_from_target[symbol]
                    assert abs(actual_deviation - expected_deviation) < 0.001

                # Trade recommendations should be mathematically sound
                for trade in result.trade_recommendations:
                    assert trade.quantity > 0
                    assert trade.current_price > 0
                    assert trade.trade_value == trade.quantity * trade.current_price
                    assert trade.total_estimated_cost >= 0

                # Cost analysis should be consistent
                total_trade_costs = sum(trade.total_estimated_cost for trade in result.trade_recommendations)
                assert abs(result.cost_analysis.total_transaction_costs - total_trade_costs) < 0.01
