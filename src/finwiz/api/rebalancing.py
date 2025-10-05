"""
Portfolio rebalancing API endpoints.

This module provides REST API endpoints for portfolio rebalancing functionality,
including analysis, recommendations, and monitoring capabilities.
"""

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from finwiz.orchestrators.portfolio_rebalancing import PortfolioRebalancingOrchestrator
from finwiz.schemas.api import RebalancingRequest, RebalancingResponse
from finwiz.tools.logger import get_logger
from finwiz.utils.feature_flags import is_feature_enabled

logger = get_logger(__name__)

router = APIRouter(prefix="/rebalancing", tags=["Portfolio Rebalancing"])


class PortfolioAnalysisResponse(BaseModel):
    """Response model for portfolio analysis."""

    total_value: float = Field(..., description="Total portfolio value")
    weightings: dict[str, float] = Field(..., description="Current position weightings")
    deviations_from_target: dict[str, float] = Field(..., description="Deviations from target weights")
    positions_needing_rebalancing: list[str] = Field(..., description="Positions requiring rebalancing")

    model_config = {"extra": "forbid"}


@router.post("/analyze", response_model=RebalancingResponse)
async def analyze_portfolio_rebalancing(request: RebalancingRequest) -> RebalancingResponse:
    """
    Analyze portfolio and generate rebalancing recommendations.

    This endpoint performs a comprehensive portfolio rebalancing analysis,
    including current position analysis, optimization, and trade recommendations.
    """
    if not is_feature_enabled("portfolio_rebalancing"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Portfolio rebalancing feature is currently disabled"
        )

    try:
        logger.info("Starting portfolio rebalancing analysis via API")

        # Initialize orchestrator
        orchestrator = PortfolioRebalancingOrchestrator()

        # Perform rebalancing analysis
        result = await orchestrator.rebalance_portfolio(
            portfolio_config=request.portfolio_config, available_capital=request.available_capital
        )

        logger.info("Portfolio rebalancing analysis completed successfully")

        return RebalancingResponse(success=True, result=result)

    except Exception as e:
        logger.error(f"Portfolio rebalancing analysis failed: {e}", exc_info=True)
        return RebalancingResponse(success=False, error=str(e))


@router.get("/portfolio/{portfolio_id}/analysis", response_model=PortfolioAnalysisResponse)
async def get_portfolio_analysis(
    portfolio_id: str, include_recommendations: bool = Query(False, description="Include rebalancing recommendations")
) -> PortfolioAnalysisResponse:
    """
    Get current portfolio analysis for a specific portfolio.

    This endpoint provides current portfolio composition analysis,
    including weightings and deviations from targets.
    """
    if not is_feature_enabled("portfolio_rebalancing"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Portfolio rebalancing feature is currently disabled"
        )

    try:
        logger.info(f"Getting portfolio analysis for portfolio {portfolio_id}")

        # This would be implemented to load portfolio data and analyze it
        # For now, return a placeholder response
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Portfolio analysis endpoint not yet implemented")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Portfolio analysis failed for {portfolio_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during portfolio analysis"
        )


@router.post("/portfolio/{portfolio_id}/simulate")
async def simulate_rebalancing_scenario(portfolio_id: str, scenario_config: RebalancingRequest) -> RebalancingResponse:
    """
    Simulate rebalancing under different scenarios.

    This endpoint allows testing different rebalancing scenarios
    without affecting the actual portfolio configuration.
    """
    if not is_feature_enabled("portfolio_rebalancing"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Portfolio rebalancing feature is currently disabled"
        )

    try:
        logger.info(f"Simulating rebalancing scenario for portfolio {portfolio_id}")

        # This would be implemented to simulate rebalancing scenarios
        # For now, return a placeholder response
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Rebalancing simulation endpoint not yet implemented"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rebalancing simulation failed for {portfolio_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during rebalancing simulation"
        )


@router.get("/status")
async def get_rebalancing_status() -> dict[str, bool]:
    """
    Get status of rebalancing features and capabilities.

    This endpoint provides information about which rebalancing
    features are currently enabled and available.
    """
    return {
        "portfolio_rebalancing": is_feature_enabled("portfolio_rebalancing"),
        "rebalancing_monitoring": is_feature_enabled("rebalancing_monitoring"),
        "rebalancing_api": is_feature_enabled("rebalancing_api"),
    }
