"""
Unit tests for API rebalancing endpoints.

Tests for the FastAPI rebalancing API endpoints including analysis,
simulation, and status functionality.
"""

import pytest
from datetime import datetime

# Check if FastAPI is available
try:
    import fastapi  # noqa: F401

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

pytestmark = pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")

if FASTAPI_AVAILABLE:
    from finwiz.api.rebalancing import (
        PortfolioAnalysisResponse,
        analyze_portfolio_rebalancing,
        get_portfolio_analysis,
        simulate_rebalancing_scenario,
        get_rebalancing_status,
    )


class TestPortfolioAnalysisResponse:
    """Test PortfolioAnalysisResponse model validation."""

    def test_should_validate_response_model(self):
        """Test PortfolioAnalysisResponse validation."""
        response = PortfolioAnalysisResponse(
            total_value=100000.0,
            weightings={"AAPL": 0.3, "MSFT": 0.25, "GOOGL": 0.45},
            deviations_from_target={"AAPL": 0.05, "MSFT": -0.05, "GOOGL": 0.0},
            positions_needing_rebalancing=["AAPL", "MSFT"],
        )

        assert response.total_value == 100000.0
        assert response.weightings["AAPL"] == 0.3
        assert len(response.positions_needing_rebalancing) == 2


class TestAnalyzePortfolioRebalancing:
    """Test the /rebalancing/analyze endpoint."""

    @pytest.mark.asyncio
    async def test_should_create_orchestrator_instance(self, mocker):
        """Test that orchestrator is instantiated when analyzing."""
        mocker.patch(
            "finwiz.api.rebalancing.is_feature_enabled",
            return_value=True,
        )

        mock_orchestrator = mocker.MagicMock()

        async def mock_rebalance(*args, **kwargs):
            raise ValueError("Portfolio analysis not available")

        mock_orchestrator.rebalance_portfolio = mock_rebalance

        mock_orchestrator_class = mocker.patch(
            "finwiz.api.rebalancing.PortfolioRebalancingOrchestrator",
            return_value=mock_orchestrator,
        )

        mock_request = mocker.MagicMock()
        mock_request.portfolio_config = {"symbol": "AAPL", "target_weight": 0.3}

        await analyze_portfolio_rebalancing(mock_request)

        # Verify orchestrator was instantiated
        mock_orchestrator_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_raise_503_when_feature_disabled(self, mocker):
        """Test that 503 error is raised when feature is disabled."""
        mocker.patch(
            "finwiz.api.rebalancing.is_feature_enabled",
            return_value=False,
        )

        from fastapi import HTTPException

        mock_request = mocker.MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await analyze_portfolio_rebalancing(mock_request)

        assert exc_info.value.status_code == 503
        assert "disabled" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_should_handle_orchestrator_errors(self, mocker):
        """Test that orchestrator errors are handled gracefully."""
        mocker.patch(
            "finwiz.api.rebalancing.is_feature_enabled",
            return_value=True,
        )

        mock_orchestrator = mocker.MagicMock()

        async def mock_rebalance_error(*args, **kwargs):
            raise ValueError("Invalid portfolio configuration")

        mock_orchestrator.rebalance_portfolio = mock_rebalance_error

        mocker.patch(
            "finwiz.api.rebalancing.PortfolioRebalancingOrchestrator",
            return_value=mock_orchestrator,
        )

        mock_request = mocker.MagicMock()
        mock_request.portfolio_config = {}

        result = await analyze_portfolio_rebalancing(mock_request)

        assert result.success is False
        assert "Invalid portfolio configuration" in result.message
        assert result.result is None


class TestGetPortfolioAnalysis:
    """Test the /rebalancing/portfolio/{portfolio_id}/analysis endpoint."""

    @pytest.mark.asyncio
    async def test_should_raise_503_when_feature_disabled(self, mocker):
        """Test that 503 error is raised when feature is disabled."""
        mocker.patch(
            "finwiz.api.rebalancing.is_feature_enabled",
            return_value=False,
        )

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await get_portfolio_analysis("portfolio-123")

        assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_should_raise_501_not_implemented(self, mocker):
        """Test that endpoint returns 501 Not Implemented."""
        mocker.patch(
            "finwiz.api.rebalancing.is_feature_enabled",
            return_value=True,
        )

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await get_portfolio_analysis("portfolio-123")

        assert exc_info.value.status_code == 501
        assert "not yet implemented" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_should_accept_include_recommendations_parameter(self, mocker):
        """Test that include_recommendations parameter is accepted."""
        mocker.patch(
            "finwiz.api.rebalancing.is_feature_enabled",
            return_value=True,
        )

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await get_portfolio_analysis("portfolio-123", include_recommendations=True)

        assert exc_info.value.status_code == 501


class TestSimulateRebalancingScenario:
    """Test the /rebalancing/portfolio/{portfolio_id}/simulate endpoint."""

    @pytest.mark.asyncio
    async def test_should_raise_503_when_feature_disabled(self, mocker):
        """Test that 503 error is raised when feature is disabled."""
        mocker.patch(
            "finwiz.api.rebalancing.is_feature_enabled",
            return_value=False,
        )

        from fastapi import HTTPException

        mock_request = mocker.MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await simulate_rebalancing_scenario("portfolio-123", mock_request)

        assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_should_raise_501_not_implemented(self, mocker):
        """Test that endpoint returns 501 Not Implemented."""
        mocker.patch(
            "finwiz.api.rebalancing.is_feature_enabled",
            return_value=True,
        )

        from fastapi import HTTPException

        mock_request = mocker.MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await simulate_rebalancing_scenario("portfolio-123", mock_request)

        assert exc_info.value.status_code == 501
        assert "not yet implemented" in exc_info.value.detail.lower()


class TestGetRebalancingStatus:
    """Test the /rebalancing/status endpoint."""

    @pytest.mark.asyncio
    async def test_should_return_feature_status(self, mocker):
        """Test that endpoint returns feature status dict."""
        mocker.patch(
            "finwiz.api.rebalancing.is_feature_enabled",
            side_effect=lambda feature: feature in ["portfolio_rebalancing", "rebalancing_api"],
        )

        result = await get_rebalancing_status()

        assert isinstance(result, dict)
        assert "portfolio_rebalancing" in result
        assert "rebalancing_monitoring" in result
        assert "rebalancing_api" in result

    @pytest.mark.asyncio
    async def test_should_reflect_enabled_features(self, mocker):
        """Test that status reflects enabled features."""
        mocker.patch(
            "finwiz.api.rebalancing.is_feature_enabled",
            return_value=True,
        )

        result = await get_rebalancing_status()

        assert result["portfolio_rebalancing"] is True
        assert result["rebalancing_monitoring"] is True
        assert result["rebalancing_api"] is True

    @pytest.mark.asyncio
    async def test_should_reflect_disabled_features(self, mocker):
        """Test that status reflects disabled features."""
        mocker.patch(
            "finwiz.api.rebalancing.is_feature_enabled",
            return_value=False,
        )

        result = await get_rebalancing_status()

        assert result["portfolio_rebalancing"] is False
        assert result["rebalancing_monitoring"] is False
        assert result["rebalancing_api"] is False
