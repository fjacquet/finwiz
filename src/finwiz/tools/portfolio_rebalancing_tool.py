"""
Portfolio rebalancing tool for CrewAI agents.

This module provides a tool interface for portfolio rebalancing functionality
that can be used by CrewAI agents to perform portfolio analysis and optimization.
"""

import asyncio
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel

from finwiz.orchestrators.portfolio_rebalancing import PortfolioRebalancingOrchestrator
from finwiz.schemas.portfolio_rebalancing import Holding, PortfolioConfiguration
from finwiz.schemas.tools import PortfolioRebalancingInput
from finwiz.tools.logger import get_logger
from finwiz.tools.run_helpers import json_error, json_ok


class PortfolioRebalancingTool(BaseTool):
    """
    Tool for portfolio rebalancing analysis and optimization.

    This tool provides CrewAI agents with the ability to analyze portfolio
    composition, generate rebalancing recommendations, and optimize trade execution.
    """

    name: str = "Portfolio Rebalancing Tool"
    description: str = (
        "Analyze portfolio composition and generate optimal rebalancing recommendations. "
        "Provide portfolio holdings, target weights, and constraints to get detailed "
        "trade recommendations with cost analysis and risk assessment."
    )
    args_schema: type[BaseModel] = PortfolioRebalancingInput

    def _run(
        self,
        holdings: list[dict[str, Any]],
        target_weights: dict[str, float],
        tolerance_bands: dict[str, float] | None = None,
        available_capital: float = 0.0,
        global_tolerance: float = 0.05,
    ) -> str:
        """
        Execute portfolio rebalancing analysis.

        Args:
            holdings: List of portfolio holdings with symbol and shares
            target_weights: Target percentage weights for each symbol
            tolerance_bands: Optional tolerance bands for each position
            available_capital: Available capital for rebalancing
            global_tolerance: Default tolerance band

        Returns:
            JSON string with rebalancing analysis results

        """
        try:
            logger.info("Starting portfolio rebalancing analysis")

            # Initialize orchestrator
            orchestrator = PortfolioRebalancingOrchestrator()

            # Validate inputs
            input_data = PortfolioRebalancingInput(
                holdings=holdings,
                target_weights=target_weights,
                tolerance_bands=tolerance_bands,
                available_capital=available_capital,
                global_tolerance=global_tolerance,
            )

            # Convert holdings to Holding objects
            portfolio_holdings = []
            for holding_data in input_data.holdings:
                holding = Holding(
                    symbol=holding_data["symbol"],
                    shares=holding_data["shares"],
                    cost_basis=holding_data.get("cost_basis"),
                    acquisition_date=holding_data.get("acquisition_date"),
                )
                portfolio_holdings.append(holding)

            # Create portfolio configuration
            config = PortfolioConfiguration(
                holdings=portfolio_holdings,
                target_weights=input_data.target_weights,
                tolerance_bands=input_data.tolerance_bands or {},
                global_tolerance=input_data.global_tolerance,
                available_capital=input_data.available_capital,
            )

            # Run rebalancing analysis
            result = asyncio.run(orchestrator.rebalance_portfolio(config))

            # Format result for agent consumption
            formatted_result = {
                "success": True,
                "analysis_timestamp": result.analysis_timestamp.isoformat(),
                "current_portfolio": {
                    "total_value": result.current_portfolio.total_value,
                    "weightings": result.current_portfolio.weightings,
                    "deviations_from_target": result.current_portfolio.deviations_from_target,
                    "positions_needing_rebalancing": result.current_portfolio.positions_needing_rebalancing,
                },
                "trade_recommendations": [
                    {
                        "symbol": trade.symbol,
                        "action": trade.action.value,
                        "quantity": trade.quantity,
                        "current_price": trade.current_price,
                        "trade_value": trade.trade_value,
                        "total_estimated_cost": trade.total_estimated_cost,
                        "priority": trade.priority,
                        "rationale": trade.rationale,
                        "current_weight": trade.current_weight,
                        "target_weight": trade.target_weight,
                        "weight_deviation": trade.weight_deviation,
                    }
                    for trade in result.trade_recommendations
                ],
                "projected_portfolio": {
                    "total_value": result.projected_portfolio.total_value,
                    "weightings": result.projected_portfolio.weightings,
                    "risk_metrics": result.projected_portfolio.risk_metrics,
                },
                "cost_analysis": {
                    "total_transaction_costs": result.total_transaction_costs,
                    "cost_benefit_ratio": result.cost_benefit_ratio,
                    "break_even_analysis": result.break_even_analysis,
                },
                "risk_analysis": {
                    "current_risk_score": result.current_risk_score,
                    "projected_risk_score": result.projected_risk_score,
                    "risk_improvement": result.risk_improvement,
                },
                "execution_summary": {
                    "total_trades_required": result.total_trades_required,
                    "positions_requiring_action": result.positions_requiring_action,
                    "positions_within_tolerance": result.positions_within_tolerance,
                },
                "overall_recommendation": result.overall_recommendation.value,
                "next_review_date": result.next_review_date.isoformat(),
            }

            logger.info("Portfolio rebalancing analysis completed successfully")
            return json_ok(formatted_result)

        except Exception as e:
            logger.error(f"Portfolio rebalancing analysis failed: {e}")
            return json_error(e)


def get_portfolio_rebalancing_tool() -> PortfolioRebalancingTool:
    """Get an instance of the portfolio rebalancing tool."""
    return PortfolioRebalancingTool()


logger = get_logger(__name__)
