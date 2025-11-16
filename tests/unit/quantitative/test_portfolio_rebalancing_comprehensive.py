"""
Comprehensive unit tests for portfolio rebalancing system.

This module provides additional test coverage for edge cases, error scenarios,
and performance testing to achieve 90%+ code coverage.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../src"))

from finwiz.orchestrators.portfolio_rebalancing import (
    InsufficientPriceDataError,
    OptimizationFailedError,
    PortfolioRebalancingError,
    PortfolioRebalancingOrchestrator,
)
from finwiz.quantitative.rebalancing_engine import RebalancingEngine
from finwiz.schemas.portfolio_rebalancing import (
    Holding,
    PortfolioConfiguration,
    PriceData,
)
from finwiz.tools.portfolio_price_service import PortfolioPriceService


class TestPortfolioRebalancingEdgeCases:
    """Test edge cases and boundary conditions for portfolio rebalancing."""

    @pytest.fixture
    def minimal_portfolio_config(self):
        """Create minimal portfolio configuration for edge case testing."""
        return PortfolioConfiguration(
            holdings=[Holding(symbol="AAPL", shares=1.0)],
            target_weights={"AAPL": 1.0},
        )

    @pytest.fixture
    def large_portfolio_config(self):
        """Create large portfolio configuration for performance testing."""
        holdings = [Holding(symbol=f"STOCK{i:03d}", shares=100.0) for i in range(100)]
        target_weights = {f"STOCK{i:03d}": 0.01 for i in range(100)}
        return PortfolioConfiguration(holdings=holdings, target_weights=target_weights)

    @pytest.fixture
    def mock_orchestrator_dependencies(self, mocker):
        """Create mocked dependencies for orchestrator testing."""
        price_service = mocker.AsyncMock(spec=PortfolioPriceService)
        rebalancing_engine = mocker.MagicMock(spec=RebalancingEngine)
        report_generator = mocker.MagicMock()
        risk_manager = mocker.MagicMock()

        # Set up default return values for risk manager methods (NOT async)
        risk_manager.assess_rebalancing_risks.return_value = {}
        risk_manager.validate_rebalancing_safety.return_value = (True, [])

        return {
            "price_service": price_service,
            "rebalancing_engine": rebalancing_engine,
            "report_generator": report_generator,
            "risk_manager": risk_manager,
        }

    def test_should_handle_empty_holdings_gracefully(self, mock_orchestrator_dependencies):
        """Test handling of empty holdings list."""
        # Arrange
        PortfolioRebalancingOrchestrator(**mock_orchestrator_dependencies)

        # Act & Assert - Should raise validation error during config creation
        with pytest.raises(ValueError):
            PortfolioConfiguration(holdings=[], target_weights={})

    def test_should_handle_mismatched_holdings_and_targets(self, mock_orchestrator_dependencies):
        """Test handling when holdings and target weights don't match."""
        # Arrange
        PortfolioRebalancingOrchestrator(**mock_orchestrator_dependencies)

        # This should be caught during configuration validation
        with pytest.raises(ValueError):
            PortfolioConfiguration(
                holdings=[Holding(symbol="AAPL", shares=100.0)],
                target_weights={"GOOGL": 1.0},  # Different symbol
            )

    @pytest.mark.asyncio
    async def test_should_handle_stale_price_data(self, mock_orchestrator_dependencies, mocker):
        """Test handling of stale price data."""
        # Arrange
        orchestrator = PortfolioRebalancingOrchestrator(**mock_orchestrator_dependencies)
        config = PortfolioConfiguration(holdings=[Holding(symbol="AAPL", shares=100.0)], target_weights={"AAPL": 1.0})

        # Mock stale price data (older than 1 hour)
        stale_timestamp = datetime.now() - timedelta(hours=2)
        mock_orchestrator_dependencies["price_service"].get_current_prices.return_value = {"AAPL": PriceData(symbol="AAPL", price=150.0, timestamp=stale_timestamp)}

        # Mock analyzer to return valid analysis
        from finwiz.schemas.portfolio_rebalancing import PortfolioAnalysis

        # Mock the portfolio analyzer on the utils object
        mocker.patch.object(
            orchestrator.utils.portfolio_analyzer,
            'analyze_current_portfolio',
            return_value=PortfolioAnalysis(
                total_value=15000.0,
                weightings={"AAPL": 1.0},
                deviations_from_target={"AAPL": 0.0},
                positions_needing_rebalancing=[],
                risk_metrics={"concentration_risk": 10.0},
            )
        )

        # Mock engine to return no trades needed
        mock_orchestrator_dependencies["rebalancing_engine"].generate_enhanced_trade_recommendations.return_value = (
            [],
            [],
        )

        # Act
        result = await orchestrator.rebalance_portfolio(config)

        # Assert
        assert result is not None
        # Should still work but may include warnings about stale data

    @pytest.mark.asyncio
    async def test_should_handle_network_timeout_gracefully(self, mock_orchestrator_dependencies):
        """Test handling of network timeouts during price retrieval."""
        # Arrange
        orchestrator = PortfolioRebalancingOrchestrator(**mock_orchestrator_dependencies)
        config = PortfolioConfiguration(holdings=[Holding(symbol="AAPL", shares=100.0)], target_weights={"AAPL": 1.0})

        # Mock network timeout
        mock_orchestrator_dependencies["price_service"].get_current_prices.side_effect = TimeoutError("Network timeout")

        # Act & Assert - TimeoutError is wrapped in PortfolioRebalancingError
        with pytest.raises(PortfolioRebalancingError):
            await orchestrator.rebalance_portfolio(config)

    @pytest.mark.asyncio
    async def test_should_handle_partial_price_data_failure(self, mock_orchestrator_dependencies):
        """Test handling when some but not all price data is available."""
        # Arrange
        orchestrator = PortfolioRebalancingOrchestrator(**mock_orchestrator_dependencies)
        config = PortfolioConfiguration(
            holdings=[
                Holding(symbol="AAPL", shares=100.0),
                Holding(symbol="GOOGL", shares=10.0),
                Holding(symbol="MSFT", shares=50.0),
            ],
            target_weights={"AAPL": 0.4, "GOOGL": 0.3, "MSFT": 0.3},
        )

        # Mock partial price data (missing MSFT)
        mock_orchestrator_dependencies["price_service"].get_current_prices.return_value = {
            "AAPL": PriceData(symbol="AAPL", price=150.0, timestamp=datetime.now()),
            "GOOGL": PriceData(symbol="GOOGL", price=2500.0, timestamp=datetime.now()),
        }

        # Mock fallback to fail for MSFT
        mock_orchestrator_dependencies["price_service"].get_price_with_fallback.side_effect = Exception("Price unavailable")

        # Act & Assert
        with pytest.raises(InsufficientPriceDataError) as exc_info:
            await orchestrator.rebalance_portfolio(config)

        assert "MSFT" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_should_handle_zero_price_data(self, mock_orchestrator_dependencies):
        """Test handling of zero or negative price data."""
        # Arrange
        PortfolioRebalancingOrchestrator(**mock_orchestrator_dependencies)
        PortfolioConfiguration(holdings=[Holding(symbol="AAPL", shares=100.0)], target_weights={"AAPL": 1.0})

        # Mock zero price data - this should fail at PriceData validation level
        with pytest.raises(ValueError):
            PriceData(symbol="AAPL", price=0.0, timestamp=datetime.now())

        # Test with negative price
        with pytest.raises(ValueError):
            PriceData(symbol="AAPL", price=-10.0, timestamp=datetime.now())

    @pytest.mark.asyncio
    async def test_should_handle_very_small_portfolio_values(self, mock_orchestrator_dependencies, mocker):
        """Test handling of very small portfolio values."""
        # Arrange
        orchestrator = PortfolioRebalancingOrchestrator(**mock_orchestrator_dependencies)
        config = PortfolioConfiguration(holdings=[Holding(symbol="AAPL", shares=0.001)], target_weights={"AAPL": 1.0})

        # Mock very small price
        mock_orchestrator_dependencies["price_service"].get_current_prices.return_value = {"AAPL": PriceData(symbol="AAPL", price=0.01, timestamp=datetime.now())}

        # Mock analyzer on the utils object
        from finwiz.schemas.portfolio_rebalancing import PortfolioAnalysis

        mocker.patch.object(
            orchestrator.utils.portfolio_analyzer,
            'analyze_current_portfolio',
            return_value=PortfolioAnalysis(
                total_value=0.00001,  # Very small value
                weightings={"AAPL": 1.0},
                deviations_from_target={"AAPL": 0.0},
                positions_needing_rebalancing=[],
                risk_metrics={"concentration_risk": 10.0},
            )
        )

        # Mock engine
        mock_orchestrator_dependencies["rebalancing_engine"].generate_enhanced_trade_recommendations.return_value = (
            [],
            [],
        )

        # Act
        result = await orchestrator.rebalance_portfolio(config)

        # Assert
        assert result is not None
        assert result.current_portfolio.total_value == 0.00001

    @pytest.mark.asyncio
    async def test_should_handle_fractional_shares_correctly(self, mock_orchestrator_dependencies, mocker):
        """Test handling of fractional share calculations."""
        # Arrange
        orchestrator = PortfolioRebalancingOrchestrator(**mock_orchestrator_dependencies)
        config = PortfolioConfiguration(
            holdings=[Holding(symbol="AAPL", shares=100.5)],  # Fractional shares
            target_weights={"AAPL": 1.0},
        )

        # Mock price data
        mock_orchestrator_dependencies["price_service"].get_current_prices.return_value = {"AAPL": PriceData(symbol="AAPL", price=150.0, timestamp=datetime.now())}

        # Mock analyzer on the utils object
        from finwiz.schemas.portfolio_rebalancing import PortfolioAnalysis

        mocker.patch.object(
            orchestrator.utils.portfolio_analyzer,
            'analyze_current_portfolio',
            return_value=PortfolioAnalysis(
                total_value=15075.0,  # 100.5 * 150
                weightings={"AAPL": 1.0},
                deviations_from_target={"AAPL": 0.0},
                positions_needing_rebalancing=[],
                risk_metrics={"concentration_risk": 10.0},
            )
        )

        # Mock engine
        mock_orchestrator_dependencies["rebalancing_engine"].generate_enhanced_trade_recommendations.return_value = (
            [],
            [],
        )

        # Act
        result = await orchestrator.rebalance_portfolio(config)

        # Assert
        assert result is not None
        assert result.current_portfolio.total_value == 15075.0

    @pytest.mark.asyncio
    async def test_should_handle_concurrent_rebalancing_requests(self, mock_orchestrator_dependencies, mocker):
        """Test handling of concurrent rebalancing requests."""
        # Arrange
        orchestrator = PortfolioRebalancingOrchestrator(**mock_orchestrator_dependencies)
        config = PortfolioConfiguration(holdings=[Holding(symbol="AAPL", shares=100.0)], target_weights={"AAPL": 1.0})

        # Mock dependencies
        mock_orchestrator_dependencies["price_service"].get_current_prices.return_value = {"AAPL": PriceData(symbol="AAPL", price=150.0, timestamp=datetime.now())}

        from finwiz.schemas.portfolio_rebalancing import PortfolioAnalysis

        mocker.patch.object(
            orchestrator.utils.portfolio_analyzer,
            'analyze_current_portfolio',
            return_value=PortfolioAnalysis(
                total_value=15000.0,
                weightings={"AAPL": 1.0},
                deviations_from_target={"AAPL": 0.0},
                positions_needing_rebalancing=[],
                risk_metrics={"concentration_risk": 10.0},
            )
        )

        mock_orchestrator_dependencies["rebalancing_engine"].generate_enhanced_trade_recommendations.return_value = (
            [],
            [],
        )

        # Act - Run multiple concurrent requests
        tasks = [orchestrator.rebalance_portfolio(config) for _ in range(5)]
        results = await asyncio.gather(*tasks)

        # Assert
        assert len(results) == 5
        for result in results:
            assert result is not None

    @pytest.mark.asyncio
    async def test_should_handle_memory_pressure_with_large_portfolio(self, mock_orchestrator_dependencies, large_portfolio_config, mocker):
        """Test handling of large portfolios that might cause memory pressure."""
        # Arrange
        orchestrator = PortfolioRebalancingOrchestrator(**mock_orchestrator_dependencies)

        # Mock price data for all 100 stocks
        price_data = {f"STOCK{i:03d}": PriceData(symbol=f"STOCK{i:03d}", price=100.0, timestamp=datetime.now()) for i in range(100)}
        mock_orchestrator_dependencies["price_service"].get_current_prices.return_value = price_data

        # Mock analyzer on the utils object
        from finwiz.schemas.portfolio_rebalancing import PortfolioAnalysis

        weightings = {f"STOCK{i:03d}": 0.01 for i in range(100)}
        mocker.patch.object(
            orchestrator.utils.portfolio_analyzer,
            'analyze_current_portfolio',
            return_value=PortfolioAnalysis(
                total_value=1000000.0,  # 100 stocks * 100 shares * $100
                weightings=weightings,
                deviations_from_target={symbol: 0.0 for symbol in weightings},
                positions_needing_rebalancing=[],
                risk_metrics={"concentration_risk": 1.0},  # Well diversified
            )
        )

        mock_orchestrator_dependencies["rebalancing_engine"].generate_enhanced_trade_recommendations.return_value = (
            [],
            [],
        )

        # Act
        result = await orchestrator.rebalance_portfolio(large_portfolio_config)

        # Assert
        assert result is not None
        assert len(result.current_portfolio.weightings) == 100

    def test_should_validate_configuration_constraints(self):
        """Test validation of portfolio configuration constraints."""
        # Test invalid target weights (sum > 100%)
        with pytest.raises(ValueError):
            PortfolioConfiguration(
                holdings=[
                    Holding(symbol="AAPL", shares=100.0),
                    Holding(symbol="GOOGL", shares=100.0),
                ],
                target_weights={"AAPL": 0.6, "GOOGL": 0.6},  # Sum = 120%
            )

        # Test negative shares
        with pytest.raises(ValueError):
            PortfolioConfiguration(holdings=[Holding(symbol="AAPL", shares=-100.0)], target_weights={"AAPL": 1.0})

        # Test negative target weights
        with pytest.raises(ValueError):
            PortfolioConfiguration(holdings=[Holding(symbol="AAPL", shares=100.0)], target_weights={"AAPL": -0.5})

    @pytest.mark.asyncio
    async def test_should_handle_api_rate_limiting(self, mock_orchestrator_dependencies):
        """Test handling of API rate limiting scenarios."""
        # Arrange
        orchestrator = PortfolioRebalancingOrchestrator(**mock_orchestrator_dependencies)
        config = PortfolioConfiguration(holdings=[Holding(symbol="AAPL", shares=100.0)], target_weights={"AAPL": 1.0})

        # Mock rate limiting error
        from requests.exceptions import HTTPError

        mock_orchestrator_dependencies["price_service"].get_current_prices.side_effect = HTTPError("429 Too Many Requests")

        # Act & Assert
        with pytest.raises(PortfolioRebalancingError):
            await orchestrator.rebalance_portfolio(config)

    @pytest.mark.asyncio
    async def test_should_handle_invalid_symbols_gracefully(self, mock_orchestrator_dependencies):
        """Test handling of invalid or delisted stock symbols."""
        # Arrange
        orchestrator = PortfolioRebalancingOrchestrator(**mock_orchestrator_dependencies)
        config = PortfolioConfiguration(holdings=[Holding(symbol="INVALID", shares=100.0)], target_weights={"INVALID": 1.0})

        # Mock invalid symbol response
        mock_orchestrator_dependencies["price_service"].get_current_prices.return_value = {}
        mock_orchestrator_dependencies["price_service"].get_price_with_fallback.side_effect = Exception("Symbol not found")

        # Act & Assert
        with pytest.raises(InsufficientPriceDataError) as exc_info:
            await orchestrator.rebalance_portfolio(config)

        assert "INVALID" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_should_handle_optimization_timeout(self, mock_orchestrator_dependencies, mocker):
        """Test handling of optimization timeout scenarios."""
        # Arrange
        orchestrator = PortfolioRebalancingOrchestrator(**mock_orchestrator_dependencies)
        config = PortfolioConfiguration(holdings=[Holding(symbol="AAPL", shares=100.0)], target_weights={"AAPL": 1.0})

        # Mock price data
        mock_orchestrator_dependencies["price_service"].get_current_prices.return_value = {"AAPL": PriceData(symbol="AAPL", price=150.0, timestamp=datetime.now())}

        # Mock analyzer on the utils object
        from finwiz.schemas.portfolio_rebalancing import PortfolioAnalysis

        mocker.patch.object(
            orchestrator.utils.portfolio_analyzer,
            'analyze_current_portfolio',
            return_value=PortfolioAnalysis(
                total_value=15000.0,
                weightings={"AAPL": 1.0},
                deviations_from_target={"AAPL": 0.0},
                positions_needing_rebalancing=[],
                risk_metrics={"concentration_risk": 10.0},
            )
        )

        # Mock optimization timeout
        mock_orchestrator_dependencies["rebalancing_engine"].generate_enhanced_trade_recommendations.side_effect = TimeoutError("Optimization timeout")

        # Act & Assert - TimeoutError is wrapped in OptimizationFailedError
        with pytest.raises(OptimizationFailedError):
            await orchestrator.rebalance_portfolio(config)


class TestPortfolioRebalancingErrorScenarios:
    """Test various error scenarios and failure modes."""

    @pytest.fixture
    def orchestrator_with_failing_dependencies(self, mocker):
        """Create orchestrator with dependencies that fail in various ways."""
        price_service = mocker.AsyncMock(spec=PortfolioPriceService)
        rebalancing_engine = mocker.MagicMock(spec=RebalancingEngine)
        report_generator = mocker.MagicMock()
        risk_manager = mocker.MagicMock()

        # Set up default return values for risk manager methods (NOT async)
        risk_manager.assess_rebalancing_risks.return_value = {}
        risk_manager.validate_rebalancing_safety.return_value = (True, [])

        return PortfolioRebalancingOrchestrator(
            price_service=price_service,
            rebalancing_engine=rebalancing_engine,
            report_generator=report_generator,
            risk_manager=risk_manager,
        )

    @pytest.mark.asyncio
    async def test_should_handle_price_service_connection_error(self, orchestrator_with_failing_dependencies):
        """Test handling of price service connection errors."""
        # Arrange
        config = PortfolioConfiguration(holdings=[Holding(symbol="AAPL", shares=100.0)], target_weights={"AAPL": 1.0})

        orchestrator_with_failing_dependencies.utils.price_service.get_current_prices.side_effect = ConnectionError("Connection failed")

        # Act & Assert - ConnectionError is wrapped in PortfolioRebalancingError
        with pytest.raises(PortfolioRebalancingError):
            await orchestrator_with_failing_dependencies.rebalance_portfolio(config)

    @pytest.mark.asyncio
    async def test_should_handle_analyzer_calculation_error(self, orchestrator_with_failing_dependencies, mocker):
        """Test handling of portfolio analyzer calculation errors."""
        # Arrange
        config = PortfolioConfiguration(holdings=[Holding(symbol="AAPL", shares=100.0)], target_weights={"AAPL": 1.0})

        # Mock successful price retrieval
        orchestrator_with_failing_dependencies.utils.price_service.get_current_prices.return_value = {"AAPL": PriceData(symbol="AAPL", price=150.0, timestamp=datetime.now())}

        # Mock analyzer failure on the utils object using mocker.patch.object
        from finwiz.quantitative.portfolio_analyzer import PortfolioAnalysisError

        mocker.patch.object(
            orchestrator_with_failing_dependencies.utils.portfolio_analyzer,
            'analyze_current_portfolio',
            side_effect=PortfolioAnalysisError("Calculation failed")
        )

        # Act & Assert
        with pytest.raises(PortfolioRebalancingError):
            await orchestrator_with_failing_dependencies.rebalance_portfolio(config)

    @pytest.mark.asyncio
    async def test_should_handle_optimization_engine_failure(self, orchestrator_with_failing_dependencies, mocker):
        """Test handling of optimization engine failures."""
        # Arrange
        config = PortfolioConfiguration(holdings=[Holding(symbol="AAPL", shares=100.0)], target_weights={"AAPL": 1.0})

        # Mock successful price retrieval
        orchestrator_with_failing_dependencies.utils.price_service.get_current_prices.return_value = {"AAPL": PriceData(symbol="AAPL", price=150.0, timestamp=datetime.now())}

        # Mock successful analysis on the utils object
        from finwiz.schemas.portfolio_rebalancing import PortfolioAnalysis

        mocker.patch.object(
            orchestrator_with_failing_dependencies.utils.portfolio_analyzer,
            'analyze_current_portfolio',
            return_value=PortfolioAnalysis(
                total_value=15000.0,
                weightings={"AAPL": 1.0},
                deviations_from_target={"AAPL": 0.0},
                positions_needing_rebalancing=[],
                risk_metrics={"concentration_risk": 10.0},
            )
        )

        # Mock optimization failure using mocker.patch.object
        mocker.patch.object(
            orchestrator_with_failing_dependencies.optimizer.rebalancing_engine,
            'generate_enhanced_trade_recommendations',
            side_effect=Exception("Optimization failed")
        )

        # Act & Assert - Exception is wrapped in OptimizationFailedError
        with pytest.raises(OptimizationFailedError):
            await orchestrator_with_failing_dependencies.rebalance_portfolio(config)

    @pytest.mark.asyncio
    async def test_should_handle_report_generation_failure(self, orchestrator_with_failing_dependencies, mocker):
        """Test handling of report generation failures."""
        # Arrange
        config = PortfolioConfiguration(holdings=[Holding(symbol="AAPL", shares=100.0)], target_weights={"AAPL": 1.0})

        # Mock successful dependencies using mocker.patch.object
        orchestrator_with_failing_dependencies.utils.price_service.get_current_prices.return_value = {"AAPL": PriceData(symbol="AAPL", price=150.0, timestamp=datetime.now())}

        from finwiz.schemas.portfolio_rebalancing import PortfolioAnalysis

        mocker.patch.object(
            orchestrator_with_failing_dependencies.utils.portfolio_analyzer,
            'analyze_current_portfolio',
            return_value=PortfolioAnalysis(
                total_value=15000.0,
                weightings={"AAPL": 1.0},
                deviations_from_target={"AAPL": 0.0},
                positions_needing_rebalancing=[],
                risk_metrics={"concentration_risk": 10.0},
            )
        )

        orchestrator_with_failing_dependencies.optimizer.rebalancing_engine.generate_enhanced_trade_recommendations.return_value = ([], [])

        # Get successful rebalancing result first
        result = await orchestrator_with_failing_dependencies.rebalance_portfolio(config)

        # Mock report generation failure using mocker.patch.object
        mocker.patch.object(
            orchestrator_with_failing_dependencies.report_generator_service,
            'generate_rebalancing_report',
            side_effect=Exception("Report generation failed")
        )

        # Act & Assert
        with pytest.raises(Exception, match="Report generation failed"):
            await orchestrator_with_failing_dependencies.generate_rebalancing_report(result)

    def test_should_handle_invalid_rebalancing_method(self):
        """Test handling of invalid rebalancing methods."""
        # This should be caught by Pydantic validation
        with pytest.raises(ValueError):
            PortfolioConfiguration(
                holdings=[Holding(symbol="AAPL", shares=100.0)],
                target_weights={"AAPL": 1.0},
                rebalancing_method="INVALID_METHOD",
            )

    def test_should_handle_extreme_tolerance_values(self):
        """Test handling of extreme tolerance values."""
        # Test very high tolerance (should be rejected by validation)
        with pytest.raises(ValueError):
            PortfolioConfiguration(
                holdings=[Holding(symbol="AAPL", shares=100.0)],
                target_weights={"AAPL": 1.0},
                global_tolerance=0.9,  # 90% tolerance - exceeds max of 0.5
            )

        # Test very low tolerance (should be accepted)
        config = PortfolioConfiguration(
            holdings=[Holding(symbol="AAPL", shares=100.0)],
            target_weights={"AAPL": 1.0},
            global_tolerance=0.001,  # 0.1% tolerance
        )
        assert config.global_tolerance == 0.001

    def test_should_handle_extreme_transaction_costs(self):
        """Test handling of extreme transaction cost rates."""
        # Test very high transaction costs
        config = PortfolioConfiguration(
            holdings=[Holding(symbol="AAPL", shares=100.0)],
            target_weights={"AAPL": 1.0},
            transaction_cost_rate=0.1,  # 10% transaction cost
        )
        assert config.transaction_cost_rate == 0.1

        # Test zero transaction costs
        config = PortfolioConfiguration(
            holdings=[Holding(symbol="AAPL", shares=100.0)],
            target_weights={"AAPL": 1.0},
            transaction_cost_rate=0.0,
        )
        assert config.transaction_cost_rate == 0.0

    @pytest.mark.asyncio
    async def test_should_handle_corrupted_price_data(self, orchestrator_with_failing_dependencies, mocker):
        """Test handling of corrupted or malformed price data."""
        # Arrange
        config = PortfolioConfiguration(holdings=[Holding(symbol="AAPL", shares=100.0)], target_weights={"AAPL": 1.0})

        # Mock corrupted price data - return empty dict (missing required data)
        orchestrator_with_failing_dependencies.utils.price_service.get_current_prices.return_value = {}

        # Mock fallback to also fail
        from finwiz.tools.portfolio_price_service import PriceDataUnavailableError
        orchestrator_with_failing_dependencies.utils.price_service.get_price_with_fallback = mocker.AsyncMock(
            side_effect=PriceDataUnavailableError(symbol="AAPL", reason="Price unavailable")
        )

        # Act & Assert - Missing price data should raise InsufficientPriceDataError
        with pytest.raises(InsufficientPriceDataError):
            await orchestrator_with_failing_dependencies.rebalance_portfolio(config)

    @pytest.mark.asyncio
    async def test_should_handle_resource_exhaustion(self, orchestrator_with_failing_dependencies):
        """Test handling of resource exhaustion scenarios."""
        # Arrange
        config = PortfolioConfiguration(holdings=[Holding(symbol="AAPL", shares=100.0)], target_weights={"AAPL": 1.0})

        # Mock memory error
        orchestrator_with_failing_dependencies.utils.price_service.get_current_prices.side_effect = MemoryError("Out of memory")

        # Act & Assert - MemoryError is wrapped in PortfolioRebalancingError
        with pytest.raises(PortfolioRebalancingError):
            await orchestrator_with_failing_dependencies.rebalance_portfolio(config)
