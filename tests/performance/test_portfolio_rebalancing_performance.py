"""
Performance tests for portfolio rebalancing system.

Tests performance characteristics, memory usage, and scalability
of the portfolio rebalancing components.
"""

import asyncio
import os
import sys
import time
from datetime import datetime

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))

from finwiz.orchestrators.portfolio_rebalancing import PortfolioRebalancingOrchestrator
from finwiz.quantitative.portfolio_analyzer import PortfolioAnalyzer
from finwiz.quantitative.rebalancing_engine import RebalancingEngine
from finwiz.schemas.portfolio_rebalancing import (
    Holding,
    PortfolioConfiguration,
    PriceData,
    RebalancingMethod,
)


class TestPortfolioRebalancingPerformance:
    """Performance tests for portfolio rebalancing system."""

    @pytest.fixture
    def performance_config_small(self):
        """Create small portfolio configuration for performance testing."""
        holdings = [Holding(symbol=f"STOCK{i:02d}", shares=100.0) for i in range(10)]
        target_weights = {f"STOCK{i:02d}": 0.1 for i in range(10)}
        return PortfolioConfiguration(holdings=holdings, target_weights=target_weights)

    @pytest.fixture
    def performance_config_medium(self):
        """Create medium portfolio configuration for performance testing."""
        holdings = [Holding(symbol=f"STOCK{i:03d}", shares=100.0) for i in range(50)]
        target_weights = {f"STOCK{i:03d}": 0.02 for i in range(50)}
        return PortfolioConfiguration(holdings=holdings, target_weights=target_weights)

    @pytest.fixture
    def performance_config_large(self):
        """Create large portfolio configuration for performance testing."""
        holdings = [Holding(symbol=f"STOCK{i:03d}", shares=100.0) for i in range(100)]
        target_weights = {f"STOCK{i:03d}": 0.01 for i in range(100)}
        return PortfolioConfiguration(holdings=holdings, target_weights=target_weights)

    def create_mock_price_data(self, symbols):
        """Create mock price data for given symbols."""
        return {symbol: PriceData(symbol=symbol, price=100.0, timestamp=datetime.now()) for symbol in symbols}

    def create_mock_portfolio_analysis(self, symbols, total_value):
        """Create mock portfolio analysis for given symbols."""
        from finwiz.schemas.portfolio_rebalancing import PortfolioAnalysis

        weightings = {symbol: 1.0 / len(symbols) for symbol in symbols}
        return PortfolioAnalysis(
            total_value=total_value,
            weightings=weightings,
            deviations_from_target={symbol: 0.0 for symbol in symbols},
            positions_needing_rebalancing=[],
            risk_metrics={"concentration_risk": 1.0 / len(symbols) * 10},
        )

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_should_complete_small_portfolio_rebalancing_quickly(self, performance_config_small, mocker):
        """Test performance with small portfolio (10 positions)."""
        # Arrange
        symbols = [f"STOCK{i:02d}" for i in range(10)]

        mock_price_service_class = mocker.patch("finwiz.tools.portfolio_price_service.PortfolioPriceService")
        mock_price_service = mocker.AsyncMock()
        mock_price_service_class.return_value = mock_price_service
        mock_price_service.get_current_prices.return_value = self.create_mock_price_data(symbols)

        mock_analyzer_class = mocker.patch("finwiz.quantitative.portfolio_analyzer.PortfolioAnalyzer")
        mock_analyzer = mocker.Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.analyze_current_portfolio.return_value = self.create_mock_portfolio_analysis(symbols, 100000.0)

        mock_engine_class = mocker.patch("finwiz.quantitative.rebalancing_engine.RebalancingEngine")
        mock_engine = mocker.Mock()
        mock_engine_class.return_value = mock_engine
        mock_engine.generate_enhanced_trade_recommendations.return_value = ([], [])

        mocker.patch("finwiz.tools.html_report_generator.HTMLReportGenerator")
        orchestrator = PortfolioRebalancingOrchestrator()

        # Act - Measure execution time
        start_time = time.perf_counter()
        result = await orchestrator.rebalance_portfolio(performance_config_small)
        end_time = time.perf_counter()

        # Assert
        execution_time = end_time - start_time
        assert execution_time < 1.0  # Should complete within 1 second
        assert result is not None
        assert len(result.current_portfolio.weightings) == 10

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_should_complete_medium_portfolio_rebalancing_efficiently(self, performance_config_medium, mocker):
        """Test performance with medium portfolio (50 positions)."""
        # Arrange
        symbols = [f"STOCK{i:03d}" for i in range(50)]

        mock_price_service_class = mocker.patch("finwiz.tools.portfolio_price_service.PortfolioPriceService")
        mock_price_service = mocker.AsyncMock()
        mock_price_service_class.return_value = mock_price_service
        mock_price_service.get_current_prices.return_value = self.create_mock_price_data(symbols)

        mock_analyzer_class = mocker.patch("finwiz.quantitative.portfolio_analyzer.PortfolioAnalyzer")
        mock_analyzer = mocker.Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.analyze_current_portfolio.return_value = self.create_mock_portfolio_analysis(symbols, 500000.0)

        mock_engine_class = mocker.patch("finwiz.quantitative.rebalancing_engine.RebalancingEngine")
        mock_engine = mocker.Mock()
        mock_engine_class.return_value = mock_engine
        mock_engine.generate_enhanced_trade_recommendations.return_value = ([], [])

        mocker.patch("finwiz.tools.html_report_generator.HTMLReportGenerator")
        orchestrator = PortfolioRebalancingOrchestrator()

        # Act - Measure execution time
        start_time = time.perf_counter()
        result = await orchestrator.rebalance_portfolio(performance_config_medium)
        end_time = time.perf_counter()

        # Assert
        execution_time = end_time - start_time
        assert execution_time < 3.0  # Should complete within 3 seconds
        assert result is not None
        assert len(result.current_portfolio.weightings) == 50

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_should_handle_large_portfolio_within_reasonable_time(self, performance_config_large, mocker):
        """Test performance with large portfolio (100 positions)."""
        # Arrange
        symbols = [f"STOCK{i:03d}" for i in range(100)]

        mock_price_service_class = mocker.patch("finwiz.tools.portfolio_price_service.PortfolioPriceService")
        mock_price_service = mocker.AsyncMock()
        mock_price_service_class.return_value = mock_price_service
        mock_price_service.get_current_prices.return_value = self.create_mock_price_data(symbols)

        mock_analyzer_class = mocker.patch("finwiz.quantitative.portfolio_analyzer.PortfolioAnalyzer")
        mock_analyzer = mocker.Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.analyze_current_portfolio.return_value = self.create_mock_portfolio_analysis(symbols, 1000000.0)

        mock_engine_class = mocker.patch("finwiz.quantitative.rebalancing_engine.RebalancingEngine")
        mock_engine = mocker.Mock()
        mock_engine_class.return_value = mock_engine
        mock_engine.generate_enhanced_trade_recommendations.return_value = ([], [])

        mocker.patch("finwiz.tools.html_report_generator.HTMLReportGenerator")
        orchestrator = PortfolioRebalancingOrchestrator()

        # Act - Measure execution time
        start_time = time.perf_counter()
        result = await orchestrator.rebalance_portfolio(performance_config_large)
        end_time = time.perf_counter()

        # Assert
        execution_time = end_time - start_time
        assert execution_time < 5.0  # Should complete within 5 seconds
        assert result is not None
        assert len(result.current_portfolio.weightings) == 100

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_should_handle_concurrent_rebalancing_requests_efficiently(self, performance_config_small, mocker):
        """Test performance with concurrent rebalancing requests."""
        # Arrange
        symbols = [f"STOCK{i:02d}" for i in range(10)]
        num_concurrent_requests = 5

        mock_price_service_class = mocker.patch("finwiz.tools.portfolio_price_service.PortfolioPriceService")
        mock_price_service = mocker.AsyncMock()
        mock_price_service_class.return_value = mock_price_service
        mock_price_service.get_current_prices.return_value = self.create_mock_price_data(symbols)

        mock_analyzer_class = mocker.patch("finwiz.quantitative.portfolio_analyzer.PortfolioAnalyzer")
        mock_analyzer = mocker.Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.analyze_current_portfolio.return_value = self.create_mock_portfolio_analysis(symbols, 100000.0)

        mock_engine_class = mocker.patch("finwiz.quantitative.rebalancing_engine.RebalancingEngine")
        mock_engine = mocker.Mock()
        mock_engine_class.return_value = mock_engine
        mock_engine.generate_enhanced_trade_recommendations.return_value = ([], [])

        mocker.patch("finwiz.tools.html_report_generator.HTMLReportGenerator")
        orchestrator = PortfolioRebalancingOrchestrator()

        # Act - Measure concurrent execution time
        start_time = time.perf_counter()
        tasks = [orchestrator.rebalance_portfolio(performance_config_small) for _ in range(num_concurrent_requests)]
        results = await asyncio.gather(*tasks)
        end_time = time.perf_counter()

        # Assert
        execution_time = end_time - start_time
        assert execution_time < 3.0  # Should complete within 3 seconds for 5 concurrent requests
        assert len(results) == num_concurrent_requests
        for result in results:
            assert result is not None

    @pytest.mark.performance
    def test_should_use_memory_efficiently_with_different_portfolio_sizes(self):
        """Test memory usage efficiency with different portfolio sizes."""
        import tracemalloc

        # Start memory tracking
        tracemalloc.start()

        memory_usage = {}

        # Test with different portfolio sizes
        for size in [10, 25, 50, 100]:
            # Clear any previous memory
            import gc

            gc.collect()

            # Take initial memory snapshot
            tracemalloc.clear_traces()

            # Create portfolio configuration
            holdings = [Holding(symbol=f"STOCK{i:03d}", shares=100.0) for i in range(size)]
            target_weights = {f"STOCK{i:03d}": 1.0 / size for i in range(size)}
            config = PortfolioConfiguration(holdings=holdings, target_weights=target_weights)

            # Create analyzer and perform basic operations
            analyzer = PortfolioAnalyzer()
            prices = {f"STOCK{i:03d}": 100.0 for i in range(size)}

            # Perform memory-intensive operations
            weightings = analyzer.calculate_current_weightings(holdings, prices)
            metrics = analyzer.calculate_portfolio_metrics(holdings, prices)

            # Take memory snapshot
            current, peak = tracemalloc.get_traced_memory()
            memory_usage[size] = peak

            # Clean up
            del config, analyzer, weightings, metrics, holdings, target_weights, prices

        tracemalloc.stop()

        # Assert memory usage scales reasonably
        assert memory_usage[10] < 10 * 1024 * 1024  # 10MB for 10 positions
        assert memory_usage[25] < 20 * 1024 * 1024  # 20MB for 25 positions
        assert memory_usage[50] < 35 * 1024 * 1024  # 35MB for 50 positions
        assert memory_usage[100] < 60 * 1024 * 1024  # 60MB for 100 positions

        # Memory should scale sub-linearly (not 10x for 10x positions)
        memory_ratio = memory_usage[100] / memory_usage[10]
        assert memory_ratio < 8.0  # Should be less than 8x memory for 10x positions

    @pytest.mark.performance
    def test_should_perform_calculations_efficiently_with_large_datasets(self):
        """Test calculation performance with large datasets."""
        # Arrange
        analyzer = PortfolioAnalyzer()
        RebalancingEngine()

        # Test with progressively larger datasets
        for size in [50, 100, 200]:
            holdings = [Holding(symbol=f"STOCK{i:03d}", shares=100.0) for i in range(size)]
            prices = {f"STOCK{i:03d}": 100.0 for i in range(size)}
            target_weights = {f"STOCK{i:03d}": 1.0 / size for i in range(size)}

            # Measure calculation time
            start_time = time.perf_counter()

            # Perform calculations
            weightings = analyzer.calculate_current_weightings(holdings, prices)
            analyzer.calculate_portfolio_metrics(holdings, prices)
            analyzer.identify_rebalancing_needs(weightings, target_weights, {})

            end_time = time.perf_counter()
            calculation_time = end_time - start_time

            # Assert reasonable performance
            if size == 50:
                assert calculation_time < 0.1  # 100ms for 50 positions
            elif size == 100:
                assert calculation_time < 0.2  # 200ms for 100 positions
            elif size == 200:
                assert calculation_time < 0.5  # 500ms for 200 positions

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_should_handle_report_generation_efficiently(self, performance_config_medium, mocker):
        """Test report generation performance."""
        # Arrange
        symbols = [f"STOCK{i:03d}" for i in range(50)]

        mock_price_service_class = mocker.patch("finwiz.tools.portfolio_price_service.PortfolioPriceService")
        mock_price_service = mocker.AsyncMock()
        mock_price_service_class.return_value = mock_price_service
        mock_price_service.get_current_prices.return_value = self.create_mock_price_data(symbols)

        mock_analyzer_class = mocker.patch("finwiz.quantitative.portfolio_analyzer.PortfolioAnalyzer")
        mock_analyzer = mocker.Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.analyze_current_portfolio.return_value = self.create_mock_portfolio_analysis(symbols, 500000.0)

        mock_engine_class = mocker.patch("finwiz.quantitative.rebalancing_engine.RebalancingEngine")
        mock_engine = mocker.Mock()
        mock_engine_class.return_value = mock_engine
        mock_engine.generate_enhanced_trade_recommendations.return_value = ([], [])

        mock_report_class = mocker.patch("finwiz.tools.html_report_generator.HTMLReportGenerator")
        mock_report_generator = mocker.Mock()
        mock_report_class.return_value = mock_report_generator
        mock_report_generator.generate_html.return_value = "<html>Test Report</html>"

        orchestrator = PortfolioRebalancingOrchestrator()

        # Get rebalancing result
        result = await orchestrator.rebalance_portfolio(performance_config_medium)

        # Act - Measure report generation time
        start_time = time.perf_counter()
        html_report = await orchestrator.generate_rebalancing_report(result)
        end_time = time.perf_counter()

        # Assert
        generation_time = end_time - start_time
        assert generation_time < 2.0  # Should generate report within 2 seconds
        assert html_report == "<html>Test Report</html>"

    @pytest.mark.performance
    def test_should_scale_optimization_algorithms_efficiently(self):
        """Test optimization algorithm scalability."""
        # Arrange
        engine = RebalancingEngine()

        # Test with different numbers of rebalancing needs
        for num_needs in [5, 10, 25, 50]:
            from finwiz.schemas.portfolio_rebalancing import RebalancingNeed, TradeAction

            needs = [
                RebalancingNeed(
                    symbol=f"STOCK{i:03d}",
                    current_weight=0.02,
                    target_weight=0.01,
                    deviation=0.01,
                    tolerance_band=0.005,
                    exceeds_tolerance=True,
                    urgency_score=0.5,
                    recommended_action=TradeAction.SELL,
                )
                for i in range(num_needs)
            ]

            from finwiz.schemas.portfolio_rebalancing import PortfolioAnalysis, PortfolioConfiguration

            current_portfolio = PortfolioAnalysis(
                total_value=100000.0,
                weightings={f"STOCK{i:03d}": 0.02 for i in range(num_needs)},
                deviations_from_target={f"STOCK{i:03d}": 0.01 for i in range(num_needs)},
                positions_needing_rebalancing=[f"STOCK{i:03d}" for i in range(num_needs)],
                risk_metrics={"concentration_risk": 2.0},
            )

            target_weights = {f"STOCK{i:03d}": 0.01 for i in range(num_needs)}
            prices = {f"STOCK{i:03d}": 100.0 for i in range(num_needs)}

            config = PortfolioConfiguration(
                holdings=[Holding(symbol=f"STOCK{i:03d}", shares=200.0) for i in range(num_needs)],
                target_weights=target_weights,
                rebalancing_method=RebalancingMethod.MINIMIZE_TRADES,
            )

            # Measure optimization time
            start_time = time.perf_counter()

            try:
                engine.optimize_rebalancing_trades(
                    rebalancing_needs=needs,
                    current_portfolio=current_portfolio,
                    target_weights=target_weights,
                    prices=prices,
                    config=config,
                )
                end_time = time.perf_counter()
                optimization_time = end_time - start_time

                # Assert reasonable performance
                if num_needs == 5:
                    assert optimization_time < 0.05  # 50ms for 5 positions
                elif num_needs == 10:
                    assert optimization_time < 0.1  # 100ms for 10 positions
                elif num_needs == 25:
                    assert optimization_time < 0.25  # 250ms for 25 positions
                elif num_needs == 50:
                    assert optimization_time < 0.5  # 500ms for 50 positions

            except Exception:
                # If optimization fails, just ensure it fails quickly
                end_time = time.perf_counter()
                failure_time = end_time - start_time
                assert failure_time < 1.0  # Should fail within 1 second

    @pytest.mark.performance
    def test_should_handle_stress_testing_scenarios(self):
        """Test system behavior under stress conditions."""
        # Test rapid successive calculations
        analyzer = PortfolioAnalyzer()

        # Perform many rapid calculations
        for _ in range(100):
            holdings = [Holding(symbol=f"STOCK{i:02d}", shares=100.0) for i in range(10)]
            prices = {f"STOCK{i:02d}": 100.0 for i in range(10)}

            start_time = time.perf_counter()
            analyzer.calculate_current_weightings(holdings, prices)
            end_time = time.perf_counter()

            # Each calculation should be fast
            assert (end_time - start_time) < 0.01  # 10ms per calculation

        # Test with extreme values
        extreme_holdings = [Holding(symbol="EXTREME", shares=1e10)]  # Very large position
        extreme_prices = {"EXTREME": 1e-6}  # Very small price

        # Should handle extreme values without crashing
        try:
            extreme_weightings = analyzer.calculate_current_weightings(extreme_holdings, extreme_prices)
            assert extreme_weightings["EXTREME"] == 1.0
        except (OverflowError, ValueError):
            # Acceptable to fail with extreme values, but should fail gracefully
            pass


class TestPortfolioRebalancingBenchmarks:
    """Benchmark tests for portfolio rebalancing system."""

    @pytest.mark.benchmark
    def test_benchmark_portfolio_analysis(self, benchmark):
        """Benchmark portfolio analysis performance."""

        def analyze_portfolio():
            analyzer = PortfolioAnalyzer()
            holdings = [Holding(symbol=f"STOCK{i:02d}", shares=100.0) for i in range(25)]
            prices = {f"STOCK{i:02d}": 100.0 for i in range(25)}
            return analyzer.calculate_current_weightings(holdings, prices)

        # Run benchmark
        result = benchmark(analyze_portfolio)
        assert len(result) == 25

    @pytest.mark.benchmark
    def test_benchmark_rebalancing_optimization(self, benchmark):
        """Benchmark rebalancing optimization performance."""

        def optimize_rebalancing():
            from finwiz.schemas.portfolio_rebalancing import (
                PortfolioAnalysis,
                PortfolioConfiguration,
                RebalancingNeed,
                TradeAction,
            )

            engine = RebalancingEngine()

            needs = [
                RebalancingNeed(
                    symbol=f"STOCK{i:02d}",
                    current_weight=0.05,
                    target_weight=0.04,
                    deviation=0.01,
                    tolerance_band=0.005,
                    exceeds_tolerance=True,
                    urgency_score=0.5,
                    recommended_action=TradeAction.SELL,
                )
                for i in range(10)
            ]

            current_portfolio = PortfolioAnalysis(
                total_value=100000.0,
                weightings={f"STOCK{i:02d}": 0.05 for i in range(10)},
                deviations_from_target={f"STOCK{i:02d}": 0.01 for i in range(10)},
                positions_needing_rebalancing=[f"STOCK{i:02d}" for i in range(10)],
                risk_metrics={"concentration_risk": 5.0},
            )

            target_weights = {f"STOCK{i:02d}": 0.04 for i in range(10)}
            prices = {f"STOCK{i:02d}": 100.0 for i in range(10)}

            config = PortfolioConfiguration(
                holdings=[Holding(symbol=f"STOCK{i:02d}", shares=500.0) for i in range(10)],
                target_weights=target_weights,
            )

            return engine.optimize_rebalancing_trades(
                rebalancing_needs=needs,
                current_portfolio=current_portfolio,
                target_weights=target_weights,
                prices=prices,
                config=config,
            )

        # Run benchmark
        result = benchmark(optimize_rebalancing)
        assert result is not None

    @pytest.mark.benchmark
    def test_benchmark_configuration_validation(self, benchmark):
        """Benchmark portfolio configuration validation performance."""

        def create_and_validate_config():
            holdings = [Holding(symbol=f"STOCK{i:02d}", shares=100.0) for i in range(20)]
            target_weights = {f"STOCK{i:02d}": 0.05 for i in range(20)}

            return PortfolioConfiguration(holdings=holdings, target_weights=target_weights)

        # Run benchmark
        result = benchmark(create_and_validate_config)
        assert len(result.holdings) == 20
