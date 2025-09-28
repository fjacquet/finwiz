"""
Integration tests for A+ Investment Monitoring System.

Tests the complete monitoring workflow including service integration,
discovery result processing, portfolio integration, and end-to-end
monitoring scenarios.
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from finwiz.schemas.investment_discovery import (
    APlusAnalysis,
    APlusDiscoveryResult,
    InvestmentCandidate,
    MarketRegime,
)
from finwiz.schemas.portfolio_review import Holding, PortfolioReview
from finwiz.services.a_plus_monitoring_service import APlusMonitoringService
from finwiz.utils.a_plus_monitoring import get_monitoring_system


class TestAPlusMonitoringIntegration:
    """Integration tests for A+ monitoring system."""

    @pytest.fixture
    def monitoring_service(self):
        """Create monitoring service for testing."""
        return APlusMonitoringService()

    @pytest.fixture
    def sample_discovery_result(self):
        """Create sample discovery result with A+ candidates."""
        # Create sample candidates
        candidates = []
        for i, symbol in enumerate(["AAPL", "MSFT", "GOOGL"]):
            candidate = InvestmentCandidate(
                symbol=symbol,
                name=f"{symbol} Inc.",
                asset_type="stock",
                current_price=150.0 + i * 10,
                market_cap=2e12 + i * 1e11,
                preliminary_score=0.96 - i * 0.01,
                final_score=0.96 - i * 0.01,
                grade="A+",
                grade_description="Excellent - Champion du portefeuille",
                recommended_action="Augmentez l'allocation si possible",
                data_source="test_discovery",
            )

            analysis = APlusAnalysis(
                candidate=candidate,
                fundamental_score=0.95 - i * 0.01,
                technical_score=0.92 - i * 0.01,
                quality_score=0.98 - i * 0.01,
                risk_score=0.90 - i * 0.01,
                composite_score=0.96 - i * 0.01,
                confidence_level=0.85 - i * 0.02,
                is_a_plus_candidate=True,
                rationale=[f"Strong fundamentals for {symbol}", f"Market leadership in {symbol}"],
            )
            candidates.append(analysis)

        return APlusDiscoveryResult(
            asset_type="stock",
            total_screened=1000,
            candidates_found=3,
            discovery_criteria=MagicMock(),
            market_context=MarketRegime(
                regime_type="bull",
                vix_level=15.0,
                inflation_rate=2.5,
                interest_rate_trend="stable",
                market_stress_level="low",
            ),
            a_plus_candidates=candidates,
            average_score=0.95,
            grade_distribution={"A+": 3},
            a_plus_percentage=0.3,
            top_recommendations=["AAPL", "MSFT", "GOOGL"],
        )

    @pytest.fixture
    def sample_portfolio_review(self):
        """Create sample portfolio review with holdings."""
        holdings = [
            Holding(
                symbol="AAPL",
                name="Apple Inc.",
                asset_type="stock",
                quantity=100,
                current_price=150.0,
                market_value=15000.0,
                weight=0.15,
                grade="A+",
                composite_score=0.96,
                recommendation="HOLD",
            ),
            Holding(
                symbol="TSLA",
                name="Tesla Inc.",
                asset_type="stock",
                quantity=50,
                current_price=200.0,
                market_value=10000.0,
                weight=0.10,
                grade="B+",
                composite_score=0.82,
                recommendation="HOLD",
            ),
            Holding(
                symbol="SPY",
                name="SPDR S&P 500 ETF",
                asset_type="etf",
                quantity=200,
                current_price=400.0,
                market_value=80000.0,
                weight=0.75,
                grade="A",
                composite_score=0.88,
                recommendation="HOLD",
            ),
        ]

        return PortfolioReview(
            portfolio_id="test_portfolio",
            analysis_date=datetime.now(),
            total_value=105000.0,
            holdings=holdings,
            portfolio_grade="A",
            average_score=0.89,
            recommendations=["Maintain current allocation"],
        )

    @pytest.mark.asyncio
    async def test_should_start_and_stop_service_successfully(self, monitoring_service):
        """Test service lifecycle management."""
        # Test start
        await monitoring_service.start_service()
        assert monitoring_service._service_started is True

        # Test stop
        await monitoring_service.stop_service()
        assert monitoring_service._service_started is False

    @pytest.mark.asyncio
    async def test_should_process_discovery_results_and_add_to_monitoring(self, monitoring_service, sample_discovery_result):
        """Test processing discovery results and adding candidates to monitoring."""
        # Arrange
        await monitoring_service.start_service()

        # Act
        result = await monitoring_service.process_discovery_results(sample_discovery_result)

        # Assert
        assert result["total_candidates"] == 3
        assert result["added_to_monitoring"] == 3
        assert result["failed_to_add"] == 0
        assert result["monitoring_active"] is True

        # Verify investments were added to monitoring system
        monitoring_system = get_monitoring_system()
        active_investments = monitoring_system.get_active_investments()
        assert len(active_investments) == 3
        assert "AAPL" in active_investments
        assert "MSFT" in active_investments
        assert "GOOGL" in active_investments

        # Cleanup
        await monitoring_service.stop_service()

    @pytest.mark.asyncio
    async def test_should_integrate_with_portfolio_review_successfully(
        self, monitoring_service, sample_portfolio_review, sample_discovery_result
    ):
        """Test integration with portfolio review system."""
        # Arrange
        await monitoring_service.start_service()

        # Add some investments to monitoring first
        await monitoring_service.process_discovery_results(sample_discovery_result)

        # Act
        integration_result = await monitoring_service.integrate_with_portfolio_review(sample_portfolio_review)

        # Assert
        assert "existing_a_plus_holdings" in integration_result
        assert "monitoring_recommendations" in integration_result
        assert "portfolio_monitoring_health" in integration_result

        # Should find AAPL as existing monitored holding
        existing_holdings = integration_result["existing_a_plus_holdings"]
        aapl_holding = next((h for h in existing_holdings if h["symbol"] == "AAPL"), None)
        assert aapl_holding is not None
        assert aapl_holding["current_grade"] == "A+"

        # Should recommend monitoring SPY (A grade)
        recommendations = integration_result["monitoring_recommendations"]
        spy_recommendation = next((r for r in recommendations if r["symbol"] == "SPY"), None)
        assert spy_recommendation is not None
        assert spy_recommendation["recommendation"] == "Add to A+ monitoring"

        # Cleanup
        await monitoring_service.stop_service()

    @pytest.mark.asyncio
    async def test_should_generate_comprehensive_monitoring_dashboard(self, monitoring_service, sample_discovery_result):
        """Test monitoring dashboard generation."""
        # Arrange
        await monitoring_service.start_service()
        await monitoring_service.process_discovery_results(sample_discovery_result)

        # Act
        dashboard = await monitoring_service.get_monitoring_dashboard()

        # Assert
        assert "service_status" in dashboard
        assert "performance_summary" in dashboard
        assert "alerts" in dashboard
        assert "investments" in dashboard
        assert "recommendations" in dashboard

        # Service status
        service_status = dashboard["service_status"]
        assert service_status["is_running"] is True
        assert service_status["monitoring_active"] is True

        # Performance summary
        perf_summary = dashboard["performance_summary"]
        assert perf_summary["total_investments"] == 3
        assert perf_summary["a_plus_count"] == 3
        assert perf_summary["monitoring_health"] == "healthy"

        # Investments
        investments = dashboard["investments"]
        assert investments["total_monitored"] == 3
        assert investments["needs_attention"] == 0
        assert len(investments["details"]) == 3

        # Cleanup
        await monitoring_service.stop_service()

    @pytest.mark.asyncio
    async def test_should_handle_grade_degradation_scenario(self, monitoring_service, sample_discovery_result, mocker):
        """Test complete grade degradation scenario."""
        # Arrange
        await monitoring_service.start_service()
        await monitoring_service.process_discovery_results(sample_discovery_result)

        # Mock scoring tool to return degraded score for AAPL
        monitoring_system = get_monitoring_system()
        mock_scoring_tool = mocker.patch.object(monitoring_system.scoring_tool, "_run")
        mock_scoring_tool.return_value = {
            "symbol": "AAPL",
            "composite_score": 0.78,  # Degraded from 0.96 to 0.78
            "grade": "B+",
            "is_a_plus_candidate": False,
            "analysis_summary": {
                "component_scores": {
                    "fundamental": 0.75,
                    "technical": 0.80,
                    "quality": 0.78,
                    "risk": 0.80,
                },
                "confidence": 0.70,
                "top_strengths": ["Still decent fundamentals"],
            },
        }

        # Act - Force evaluation to trigger degradation
        evaluation_result = await monitoring_service.force_evaluation_all()

        # Assert
        assert evaluation_result["total_evaluated"] >= 1
        assert evaluation_result["degraded_count"] >= 1

        # Check that alert was generated
        alerts = monitoring_system.get_degradation_alerts(hours_back=1)
        assert len(alerts) >= 1

        degradation_alert = next((a for a in alerts if a.symbol == "AAPL"), None)
        assert degradation_alert is not None
        assert degradation_alert.previous_grade == "A+"
        assert degradation_alert.current_grade == "B+"
        assert degradation_alert.score_change < 0

        # Check dashboard reflects degradation
        dashboard = await monitoring_service.get_monitoring_dashboard()
        assert dashboard["alerts"]["total_recent"] >= 1

        # Cleanup
        await monitoring_service.stop_service()

    @pytest.mark.asyncio
    async def test_should_cleanup_inactive_investments(self, monitoring_service, sample_discovery_result, mocker):
        """Test cleanup of inactive/degraded investments."""
        # Arrange
        await monitoring_service.start_service()
        await monitoring_service.process_discovery_results(sample_discovery_result)

        # Simulate degraded investment that's been inactive
        monitoring_system = get_monitoring_system()
        aapl_metrics = monitoring_system.monitored_investments["AAPL"]
        aapl_metrics.current_score = 0.70  # Below B+ threshold
        aapl_metrics.current_grade = "C+"
        aapl_metrics.last_evaluation = datetime.now() - timedelta(days=35)  # Old evaluation

        # Act
        cleanup_result = await monitoring_service.cleanup_inactive_investments(days_inactive=30)

        # Assert
        assert cleanup_result["removed_count"] == 1
        assert "AAPL" in cleanup_result["removed_symbols"]
        assert cleanup_result["remaining_monitored"] == 2

        # Verify AAPL is marked inactive
        assert monitoring_system.monitored_investments["AAPL"].is_active is False

        # Cleanup
        await monitoring_service.stop_service()

    @pytest.mark.asyncio
    async def test_should_handle_market_regime_changes(self, monitoring_service, sample_discovery_result):
        """Test handling of market regime changes."""
        # Arrange
        await monitoring_service.start_service()
        await monitoring_service.process_discovery_results(sample_discovery_result)

        monitoring_system = get_monitoring_system()

        # Set initial regime
        initial_regime = MarketRegime(
            regime_type="bull",
            vix_level=15.0,
            inflation_rate=2.0,
            interest_rate_trend="stable",
            market_stress_level="low",
        )
        await monitoring_system.update_market_regime(initial_regime)

        # Act - Change to bear market
        bear_regime = MarketRegime(
            regime_type="bear",
            vix_level=35.0,
            inflation_rate=5.0,
            interest_rate_trend="rising",
            market_stress_level="high",
        )
        await monitoring_system.update_market_regime(bear_regime)

        # Assert - All investments should be marked for re-evaluation
        active_investments = monitoring_system.get_active_investments()
        for metrics in active_investments.values():
            assert metrics.needs_reevaluation is True

        # Cleanup
        await monitoring_service.stop_service()

    @pytest.mark.asyncio
    async def test_should_handle_concurrent_evaluations(self, monitoring_service, sample_discovery_result, mocker):
        """Test handling of concurrent investment evaluations."""
        # Arrange
        await monitoring_service.start_service()
        await monitoring_service.process_discovery_results(sample_discovery_result)

        # Mock scoring tool with delay to test concurrency
        monitoring_system = get_monitoring_system()
        original_run = monitoring_system.scoring_tool._run

        async def delayed_run(*args, **kwargs):
            await asyncio.sleep(0.1)  # Small delay
            return original_run(*args, **kwargs)

        mocker.patch.object(monitoring_system.scoring_tool, "_run", side_effect=delayed_run)

        # Act - Force evaluation of all investments concurrently
        start_time = datetime.now()
        result = await monitoring_service.force_evaluation_all()
        end_time = datetime.now()

        # Assert - Should complete in reasonable time (concurrent, not sequential)
        execution_time = (end_time - start_time).total_seconds()
        assert execution_time < 1.0  # Should be much faster than 3 * 0.1 seconds
        assert result["total_evaluated"] == 3

        # Cleanup
        await monitoring_service.stop_service()

    @pytest.mark.asyncio
    async def test_should_persist_monitoring_data_across_restarts(self, monitoring_service, sample_discovery_result):
        """Test that monitoring data persists across service restarts."""
        # Arrange - Start service and add investments
        await monitoring_service.start_service()
        await monitoring_service.process_discovery_results(sample_discovery_result)

        # Verify investments are monitored
        monitoring_system = get_monitoring_system()
        initial_count = len(monitoring_system.get_active_investments())
        assert initial_count == 3

        # Act - Stop and restart service
        await monitoring_service.stop_service()
        await monitoring_service.start_service()

        # Assert - Data should still be there (in-memory for this test)
        final_count = len(monitoring_system.get_active_investments())
        assert final_count == initial_count

        # Cleanup
        await monitoring_service.stop_service()

    @pytest.mark.asyncio
    async def test_should_handle_service_errors_gracefully(self, monitoring_service, sample_discovery_result, mocker):
        """Test graceful handling of service errors."""
        # Arrange
        await monitoring_service.start_service()

        # Mock scoring tool to raise exception
        monitoring_system = get_monitoring_system()
        mocker.patch.object(monitoring_system.scoring_tool, "_run", side_effect=Exception("Simulated scoring error"))

        # Act - Try to process discovery results
        result = await monitoring_service.process_discovery_results(sample_discovery_result)

        # Assert - Should handle errors gracefully
        assert result["total_candidates"] == 3
        assert result["failed_to_add"] == 3  # All should fail due to mocked error
        assert result["added_to_monitoring"] == 0

        # Service should still be running
        assert monitoring_service._service_started is True

        # Cleanup
        await monitoring_service.stop_service()

    @pytest.mark.asyncio
    async def test_should_export_monitoring_data_correctly(self, monitoring_service, sample_discovery_result):
        """Test monitoring data export functionality."""
        # Arrange
        await monitoring_service.start_service()
        await monitoring_service.process_discovery_results(sample_discovery_result)

        # Act
        dashboard = await monitoring_service.get_monitoring_dashboard()

        # Assert - Dashboard should contain exportable data
        assert "service_status" in dashboard
        assert "performance_summary" in dashboard
        assert "investments" in dashboard

        # Investment details should be complete
        investment_details = dashboard["investments"]["details"]
        assert len(investment_details) == 3

        for investment in investment_details:
            assert "symbol" in investment
            assert "asset_type" in investment
            assert "current_grade" in investment
            assert "current_score" in investment
            assert "days_monitored" in investment
            assert "last_evaluation" in investment

        # Cleanup
        await monitoring_service.stop_service()

    @pytest.mark.asyncio
    async def test_should_handle_empty_discovery_results(self, monitoring_service):
        """Test handling of empty discovery results."""
        # Arrange
        await monitoring_service.start_service()

        empty_discovery = APlusDiscoveryResult(
            asset_type="stock",
            total_screened=1000,
            candidates_found=0,
            discovery_criteria=MagicMock(),
            market_context=MarketRegime(
                regime_type="bear",
                vix_level=35.0,
                inflation_rate=5.0,
                interest_rate_trend="rising",
                market_stress_level="high",
            ),
            a_plus_candidates=[],  # Empty list
            average_score=0.0,
            grade_distribution={},
            a_plus_percentage=0.0,
            top_recommendations=[],
        )

        # Act
        result = await monitoring_service.process_discovery_results(empty_discovery)

        # Assert
        assert result["total_candidates"] == 0
        assert result["added_to_monitoring"] == 0
        assert result["failed_to_add"] == 0

        # Monitoring system should be empty
        monitoring_system = get_monitoring_system()
        assert len(monitoring_system.get_active_investments()) == 0

        # Cleanup
        await monitoring_service.stop_service()
