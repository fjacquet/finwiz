"""
Portfolio analysis tool for CrewAI agents.

This module provides comprehensive portfolio analysis capabilities including
composition analysis, performance metrics, and diversification assessment.
"""

import json
from datetime import datetime
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel

from finwiz.quantitative.performance import get_performance_analyzer
from finwiz.quantitative.portfolio_analyzer import PortfolioAnalyzer
from finwiz.schemas.tools import PortfolioAnalysisInput
from finwiz.tools.logger import get_logger


class PortfolioAnalysisTool(BaseTool):
    """
    Tool for comprehensive portfolio analysis.

    This tool provides CrewAI agents with the ability to analyze portfolio
    composition, performance metrics, risk characteristics, and diversification.
    """

    name: str = "Portfolio Analysis Tool"
    description: str = (
        "Analyze portfolio composition, performance, and risk characteristics. "
        "Provides detailed insights into portfolio diversification, sector allocation, "
        "performance metrics, and risk-adjusted returns compared to benchmarks."
    )
    args_schema: type[BaseModel] = PortfolioAnalysisInput

    def _run(
        self,
        holdings: list[dict[str, Any]],
        benchmark: str = "SPY",
        analysis_period: str = "1y",
        include_risk_metrics: bool = True,
        include_diversification: bool = True,
    ) -> str:
        """
        Execute portfolio analysis.

        Args:
            holdings: List of portfolio holdings with symbol, shares, and optional cost_basis
            benchmark: Benchmark symbol for comparison
            analysis_period: Analysis period (1y, 2y, 5y)
            include_risk_metrics: Include risk analysis
            include_diversification: Include diversification analysis

        Returns:
            JSON string with portfolio analysis results

        """
        try:
            logger.info("Starting portfolio analysis")

            # Validate inputs
            input_data = PortfolioAnalysisInput(
                holdings=holdings,
                benchmark=benchmark,
                analysis_period=analysis_period,
                include_risk_metrics=include_risk_metrics,
                include_diversification=include_diversification,
            )

            # Initialize analyzers
            portfolio_analyzer = PortfolioAnalyzer()
            performance_analyzer = get_performance_analyzer()

            # Calculate portfolio composition
            composition_analysis = self._analyze_composition(input_data.holdings)

            # Calculate performance metrics
            performance_analysis = self._analyze_performance(input_data.holdings, input_data.benchmark, input_data.analysis_period, performance_analyzer)

            # Risk analysis (if requested)
            risk_analysis = None
            if input_data.include_risk_metrics:
                risk_analysis = self._analyze_risk(input_data.holdings, portfolio_analyzer)

            # Diversification analysis (if requested)
            diversification_analysis = None
            if input_data.include_diversification:
                diversification_analysis = self._analyze_diversification(input_data.holdings)

            # Compile results
            analysis_result = {
                "analysis_timestamp": datetime.now().isoformat(),
                "portfolio_composition": composition_analysis,
                "performance_analysis": performance_analysis,
                "risk_analysis": risk_analysis,
                "diversification_analysis": diversification_analysis,
                "summary": self._generate_summary(composition_analysis, performance_analysis, risk_analysis),
            }

            logger.info("Portfolio analysis completed successfully")
            return json.dumps(analysis_result, indent=2)

        except Exception as e:
            logger.error(f"Portfolio analysis failed: {e}")
            error_result = {"success": False, "error": str(e), "error_type": type(e).__name__}
            return json.dumps(error_result, indent=2)

    def _analyze_composition(self, holdings: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze portfolio composition."""
        try:
            total_value = 0
            position_values = {}
            symbols = []

            # Calculate position values (simplified - would need real-time prices)
            for holding in holdings:
                symbol = holding["symbol"]
                shares = holding["shares"]
                # Use cost_basis if available, otherwise estimate
                price = holding.get("cost_basis", 100.0)  # Placeholder
                value = shares * price
                position_values[symbol] = value
                total_value += value
                symbols.append(symbol)

            # Calculate weights
            weights = {symbol: value / total_value for symbol, value in position_values.items()}

            return {
                "total_positions": len(holdings),
                "total_value": total_value,
                "position_weights": weights,
                "position_values": position_values,
                "symbols": symbols,
                "largest_position": max(weights.items(), key=lambda x: x[1]) if weights else None,
                "concentration_risk": max(weights.values()) if weights else 0,
            }

        except Exception as e:
            logger.error(f"Error in composition analysis: {e}")
            return {"error": str(e)}

    def _analyze_performance(self, holdings: list[dict[str, Any]], benchmark: str, period: str, performance_analyzer: Any) -> dict[str, Any]:
        """Analyze portfolio performance."""
        try:
            # This is a simplified implementation
            # In a real implementation, you would fetch historical data and calculate returns
            return {
                "period": period,
                "benchmark": benchmark,
                "total_return": 0.0,  # Placeholder
                "annualized_return": 0.0,  # Placeholder
                "volatility": 0.0,  # Placeholder
                "sharpe_ratio": 0.0,  # Placeholder
                "max_drawdown": 0.0,  # Placeholder
                "beta": 1.0,  # Placeholder
                "alpha": 0.0,  # Placeholder
                "note": "Performance analysis requires historical price data integration",
            }

        except Exception as e:
            logger.error(f"Error in performance analysis: {e}")
            return {"error": str(e)}

    def _analyze_risk(self, holdings: list[dict[str, Any]], portfolio_analyzer: PortfolioAnalyzer) -> dict[str, Any]:
        """Analyze portfolio risk characteristics."""
        try:
            # Simplified risk analysis
            num_positions = len(holdings)

            # Basic risk assessment based on diversification
            if num_positions < 5:
                risk_level = "High"
                risk_score = 8
            elif num_positions < 15:
                risk_level = "Moderate"
                risk_score = 5
            else:
                risk_level = "Low"
                risk_score = 3

            return {
                "overall_risk_score": risk_score,
                "risk_level": risk_level,
                "concentration_risk": "High" if num_positions < 5 else "Moderate" if num_positions < 15 else "Low",
                "diversification_score": min(10, num_positions),
                "risk_factors": [
                    "Concentration risk" if num_positions < 10 else "Well diversified",
                    "Market risk exposure",
                    "Sector concentration risk" if num_positions < 20 else "Good sector diversification",
                ],
                "recommendations": [
                    "Consider adding more positions for better diversification" if num_positions < 10 else "Good diversification level",
                    "Monitor correlation between holdings",
                    "Consider adding defensive positions",
                ],
            }

        except Exception as e:
            logger.error(f"Error in risk analysis: {e}")
            return {"error": str(e)}

    def _analyze_diversification(self, holdings: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze portfolio diversification."""
        try:
            symbols = [holding["symbol"] for holding in holdings]
            num_positions = len(symbols)

            # Basic diversification metrics
            diversification_score = min(10, num_positions)

            # Sector analysis would require additional data
            # This is a simplified implementation
            return {
                "number_of_positions": num_positions,
                "diversification_score": diversification_score,
                "diversification_level": ("Poor" if num_positions < 5 else "Fair" if num_positions < 10 else "Good" if num_positions < 20 else "Excellent"),
                "recommendations": [
                    "Add more positions" if num_positions < 10 else "Good position count",
                    "Consider sector diversification",
                    "Monitor geographic exposure",
                    "Consider asset class diversification",
                ],
                "note": "Detailed sector and geographic analysis requires additional market data",
            }

        except Exception as e:
            logger.error(f"Error in diversification analysis: {e}")
            return {"error": str(e)}

    def _generate_summary(self, composition: dict[str, Any], performance: dict[str, Any], risk: dict[str, Any]) -> dict[str, Any]:
        """Generate portfolio analysis summary."""
        try:
            summary = {
                "total_positions": composition.get("total_positions", 0),
                "concentration_risk": composition.get("concentration_risk", 0),
                "overall_assessment": "Requires detailed analysis with market data",
            }

            if risk:
                summary["risk_level"] = risk.get("risk_level", "Unknown")
                summary["risk_score"] = risk.get("overall_risk_score", 0)

            # Generate key insights
            insights = []
            if composition.get("total_positions", 0) < 10:
                insights.append("Portfolio may benefit from additional diversification")
            if composition.get("concentration_risk", 0) > 0.3:
                insights.append("High concentration in single position detected")

            summary["key_insights"] = insights

            return summary

        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {"error": str(e)}


def get_portfolio_analysis_tool() -> PortfolioAnalysisTool:
    """Get an instance of the portfolio analysis tool."""
    return PortfolioAnalysisTool()


logger = get_logger(__name__)
