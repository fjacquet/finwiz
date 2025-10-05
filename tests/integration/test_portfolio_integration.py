"""
Integration tests for portfolio review and rebalancing integration.

Tests the seamless integration between portfolio review and rebalancing
components, including shared caching and unified reporting.
"""

import json
from pathlib import Path

import pytest

from finwiz.orchestrators.portfolio_review import EnhancedPortfolioReviewOrchestrator
from finwiz.tools.portfolio_cache_service import PortfolioCacheService


class TestPortfolioIntegration:
    """Test integration between portfolio review and rebalancing systems."""

    @pytest.fixture
    def mock_portfolio_data(self):
        """Mock portfolio data for testing."""
        return {
            "holdings": [
                {
                    "ticker": "AAPL",
                    "name": "Apple Inc.",
                    "asset_class": "stock",
                    "decision": "KEEP",
                    "composite_score": 0.85,
                    "risk": {"score": 3.0, "level": "Medium"},
                },
                {
                    "ticker": "GOOGL",
                    "name": "Alphabet Inc.",
                    "asset_class": "stock",
                    "decision": "KEEP",
                    "composite_score": 0.78,
                    "risk": {"score": 4.0, "level": "Medium"},
                },
                {
                    "ticker": "TSLA",
                    "name": "Tesla Inc.",
                    "asset_class": "stock",
                    "decision": "SELL",
                    "composite_score": 0.45,
                    "risk": {"score": 7.0, "level": "High"},
                },
            ]
        }

    @pytest.fixture
    def mock_rebalancing_result(self):
        """Mock rebalancing result for testing."""
        return {
            "analysis_timestamp": "2025-01-01T12:00:00",
            "portfolio_id": "test_portfolio",
            "current_portfolio": {
                "total_value": 100000.0,
                "weightings": {"AAPL": 0.40, "GOOGL": 0.35, "MSFT": 0.25},
                "deviations_from_target": {"AAPL": 0.10, "GOOGL": -0.05, "MSFT": -0.05},
            },
            "trade_recommendations": [
                {
                    "symbol": "AAPL",
                    "action": "SELL",
                    "quantity": 50.0,
                    "current_price": 150.0,
                    "trade_value": 7500.0,
                    "total_estimated_cost": 15.0,
                    "priority": 1,
                }
            ],
            "execution_summary": {
                "total_trades_required": 1,
                "positions_requiring_action": 1,
                "positions_within_tolerance": 2,
                "estimated_execution_time": "5-10 minutes",
            },
            "cost_analysis": {
                "total_transaction_costs": 15.0,
                "commission_costs": 10.0,
                "spread_costs": 5.0,
            },
            "overall_recommendation": "REBALANCE_SOON",
        }

    @pytest.fixture
    def target_weights(self):
        """Target weights for rebalancing."""
        return {"AAPL": 0.30, "GOOGL": 0.40, "MSFT": 0.30}

    def test_should_initialize_enhanced_orchestrator_successfully(self):
        """Test that enhanced orchestrator initializes correctly."""
        # Act
        orchestrator = EnhancedPortfolioReviewOrchestrator()

        # Assert
        assert orchestrator is not None
        assert orchestrator.cache_manager is not None

    @pytest.mark.asyncio
    async def test_should_run_comprehensive_analysis_when_valid_inputs_provided(
        self, mocker, target_weights, mock_portfolio_data, mock_rebalancing_result
    ):
        """Test comprehensive analysis with valid inputs."""
        # Arrange
        orchestrator = EnhancedPortfolioReviewOrchestrator()

        # Mock the run_with_rebalancing function
        mock_run_with_rebalancing = mocker.patch("finwiz.orchestrators.portfolio_review.run_with_rebalancing")
        mock_run_with_rebalancing.return_value = (
            Path("/tmp/portfolio_review.json"),
            mocker.MagicMock(model_dump=lambda: mock_rebalancing_result),
        )

        # Mock file reading
        mocker.patch("pathlib.Path.read_text", return_value=json.dumps(mock_portfolio_data))

        # Act
        result = await orchestrator.run_comprehensive_analysis(target_weights=target_weights, available_capital=10000.0)

        # Assert
        assert result is not None
        assert "portfolio_review" in result
        assert "rebalancing_analysis" in result
        assert "analysis_timestamp" in result
        assert result["has_rebalancing_recommendations"] is True
        mock_run_with_rebalancing.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_use_caching_when_enabled(self, mocker, target_weights):
        """Test that caching is used when enabled."""
        # Arrange
        orchestrator = EnhancedPortfolioReviewOrchestrator()
        cached_result = {"cached": True, "portfolio_review": {}, "rebalancing_analysis": None}

        # Mock cache manager
        mock_cache_get = mocker.patch.object(orchestrator.cache_manager, "get")
        mock_cache_get.return_value = cached_result

        # Act
        result = await orchestrator.run_comprehensive_analysis(target_weights=target_weights, enable_caching=True)

        # Assert
        assert result == cached_result
        mock_cache_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_generate_unified_report_when_valid_data_provided(
        self, mocker, mock_portfolio_data, mock_rebalancing_result
    ):
        """Test unified report generation."""
        # Arrange
        orchestrator = EnhancedPortfolioReviewOrchestrator()
        analysis_result = {
            "portfolio_review": mock_portfolio_data,
            "rebalancing_analysis": mock_rebalancing_result,
            "has_rebalancing_recommendations": True,
        }

        # Mock HTML generator
        mock_generator = mocker.MagicMock()
        mock_generator.generate_unified_html.return_value = "<html>Test Report</html>"
        mock_generator.generate_html_fallback.return_value = "<html>Test Report</html>"
        mocker.patch("finwiz.tools.html_report_generator.HTMLReportGenerator", return_value=mock_generator)

        # Act
        html_report = await orchestrator.generate_unified_report(analysis_result)

        # Assert
        assert html_report == "<html>Test Report</html>"
        mock_generator.add_section.assert_called()

    @pytest.mark.asyncio
    async def test_should_handle_rebalancing_failure_gracefully(self, mocker, target_weights):
        """Test graceful handling of rebalancing failures."""
        # Arrange
        orchestrator = EnhancedPortfolioReviewOrchestrator()

        # Mock run_with_rebalancing to raise an exception
        mock_run_with_rebalancing = mocker.patch("finwiz.orchestrators.portfolio_review.run_with_rebalancing")
        mock_run_with_rebalancing.side_effect = Exception("Rebalancing failed")

        # Mock cache manager to return None (no cached result)
        mock_cache_get = mocker.patch.object(orchestrator.cache_manager, "get")
        mock_cache_get.return_value = None

        # Act & Assert - should not raise exception but should handle gracefully
        with pytest.raises(Exception, match="Rebalancing failed"):
            await orchestrator.run_comprehensive_analysis(target_weights=target_weights)


class TestPortfolioCacheService:
    """Test portfolio cache service functionality."""

    @pytest.fixture
    def cache_service(self, mocker):
        """Create cache service with mocked cache manager."""
        mock_cache_manager = mocker.MagicMock()
        mock_cache_manager.get = mocker.AsyncMock()
        mock_cache_manager.set = mocker.AsyncMock()
        mock_cache_manager.clear = mocker.AsyncMock()

        return PortfolioCacheService(cache_manager=mock_cache_manager)

    @pytest.mark.asyncio
    async def test_should_cache_price_data_successfully(self, cache_service):
        """Test price data caching."""
        # Arrange
        symbol = "AAPL"
        price_data = {"price": 150.0, "timestamp": "2025-01-01T12:00:00"}

        # Act
        await cache_service.set_price_data(symbol, price_data)

        # Assert
        cache_service.cache_manager.set.assert_called_once()
        call_args = cache_service.cache_manager.set.call_args
        assert call_args[0][0] == ["price_data", symbol]
        assert call_args[0][1] == price_data

    @pytest.mark.asyncio
    async def test_should_retrieve_cached_price_data(self, cache_service):
        """Test price data retrieval from cache."""
        # Arrange
        symbol = "AAPL"
        cached_data = {"price": 150.0, "timestamp": "2025-01-01T12:00:00"}
        cache_service.cache_manager.get.return_value = cached_data

        # Act
        result = await cache_service.get_price_data(symbol)

        # Assert
        assert result == cached_data
        cache_service.cache_manager.get.assert_called_once_with(["price_data", symbol])

    @pytest.mark.asyncio
    async def test_should_cache_portfolio_analysis_successfully(self, cache_service):
        """Test portfolio analysis caching."""
        # Arrange
        portfolio_hash = "abc123"
        analysis_result = {"total_value": 100000.0, "weightings": {"AAPL": 0.5}}

        # Act
        await cache_service.set_portfolio_analysis(portfolio_hash, analysis_result)

        # Assert
        cache_service.cache_manager.set.assert_called_once()
        call_args = cache_service.cache_manager.set.call_args
        assert call_args[0][0] == ["portfolio_analysis", portfolio_hash]
        assert call_args[0][1] == analysis_result

    @pytest.mark.asyncio
    async def test_should_warm_cache_for_multiple_symbols(self, cache_service, mocker):
        """Test cache warming for multiple symbols."""
        # Arrange
        symbols = ["AAPL", "GOOGL", "MSFT"]

        # Mock price service
        mock_price_service = mocker.MagicMock()
        mock_price_data = mocker.MagicMock()
        mock_price_data.model_dump.return_value = {"price": 150.0}
        mock_price_service.get_price_with_fallback = mocker.AsyncMock(return_value=mock_price_data)

        mocker.patch(
            "finwiz.tools.portfolio_price_service.PortfolioPriceService",
            return_value=mock_price_service,
        )

        # Mock get_price_data to return None (not cached)
        cache_service.get_price_data = mocker.AsyncMock(return_value=None)
        cache_service.set_price_data = mocker.AsyncMock()

        # Act
        await cache_service.warm_portfolio_cache(symbols)

        # Assert
        assert mock_price_service.get_price_with_fallback.call_count == len(symbols)
        assert cache_service.set_price_data.call_count == len(symbols)

    @pytest.mark.asyncio
    async def test_should_invalidate_market_data_cache(self, cache_service):
        """Test market data cache invalidation."""
        # Arrange
        cache_service.cache_manager.clear.return_value = 5

        # Act
        result = await cache_service.invalidate_market_data()

        # Assert
        assert result == 5
        cache_service.cache_manager.clear.assert_called_once_with(tags={"price_data", "market_data"})

    def test_should_get_cache_stats_successfully(self, cache_service):
        """Test cache statistics retrieval."""
        # Arrange
        base_stats = {"hits": 100, "misses": 20, "hit_rate": 0.83}
        cache_service.cache_manager.get_stats.return_value = base_stats

        # Act
        stats = cache_service.get_cache_stats()

        # Assert
        assert "hits" in stats
        assert "cache_ttl_settings" in stats
        assert "cache_effectiveness" in stats
        assert stats["cache_effectiveness"]["hit_rate_good"] is True


class TestSharedCachingIntegration:
    """Test shared caching between portfolio review and rebalancing."""

    @pytest.mark.asyncio
    async def test_should_share_price_data_between_components(self, mocker):
        """Test that price data is shared between portfolio review and rebalancing."""
        # Arrange
        from finwiz.tools.portfolio_price_service import PortfolioPriceService

        # Mock shared cache service
        mock_cache_service = mocker.MagicMock()
        mock_cache_service.get_price_data = mocker.AsyncMock(return_value={"price": 150.0})
        mock_cache_service.set_price_data = mocker.AsyncMock()

        mocker.patch(
            "finwiz.tools.portfolio_price_service.get_portfolio_cache_service",
            return_value=mock_cache_service,
        )

        # Mock Yahoo Finance tool
        mock_yahoo_tool = mocker.MagicMock()
        mocker.patch(
            "finwiz.tools.portfolio_price_service.YahooFinanceTickerInfoTool",
            return_value=mock_yahoo_tool,
        )

        price_service = PortfolioPriceService()

        # Act
        await price_service.get_current_price("AAPL")

        # Assert
        mock_cache_service.get_price_data.assert_called_once_with("AAPL")

    @pytest.mark.asyncio
    async def test_should_cache_portfolio_analysis_results(self, mocker):
        """Test that portfolio analysis results are cached."""
        # Arrange
        orchestrator = EnhancedPortfolioReviewOrchestrator()

        # Mock cache manager
        mock_cache_set = mocker.patch.object(orchestrator.cache_manager, "set")
        mock_cache_get = mocker.patch.object(orchestrator.cache_manager, "get")
        mock_cache_get.return_value = None  # No cached result

        # Mock run_with_rebalancing
        mock_run_with_rebalancing = mocker.patch("finwiz.orchestrators.portfolio_review.run_with_rebalancing")
        mock_run_with_rebalancing.return_value = (Path("/tmp/test.json"), None)

        # Mock file reading
        mocker.patch("pathlib.Path.read_text", return_value=json.dumps({"test": "data"}))

        # Act
        await orchestrator.run_comprehensive_analysis(enable_caching=True)

        # Assert
        mock_cache_set.assert_called_once()
        # Verify cache key includes the parameters
        cache_key = mock_cache_set.call_args[0][0]
        assert "portfolio_analysis" in cache_key

    @pytest.mark.asyncio
    async def test_should_handle_cache_failures_gracefully(self, mocker):
        """Test graceful handling of cache failures."""
        # Arrange
        from finwiz.tools.portfolio_cache_service import with_portfolio_cache

        # Mock function that will be cached
        async def test_function():
            return {"result": "success"}

        # Mock cache service to raise exception
        mock_cache_service = mocker.MagicMock()
        mock_cache_service.cache_manager.get = mocker.AsyncMock(side_effect=Exception("Cache error"))
        mock_cache_service.cache_manager.set = mocker.AsyncMock(side_effect=Exception("Cache error"))

        mocker.patch(
            "finwiz.tools.portfolio_cache_service.get_portfolio_cache_service",
            return_value=mock_cache_service,
        )

        # Act - should not raise exception
        result = await with_portfolio_cache("test_key", test_function)

        # Assert
        assert result == {"result": "success"}
