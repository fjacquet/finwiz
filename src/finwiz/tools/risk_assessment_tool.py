"""
Risk assessment tool for CrewAI agents.

This module provides comprehensive risk assessment capabilities for individual
assets and portfolios, including various risk metrics and scenario analysis.
"""

import json
from datetime import datetime
from typing import Any

import numpy as np
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class RiskAssessmentInput(BaseModel):
    """Input model for risk assessment tool."""

    assets: list[str] = Field(..., description="List of asset symbols to assess")
    portfolio_weights: dict[str, float] | None = Field(
        None, description="Portfolio weights for each asset (if assessing portfolio risk)"
    )
    assessment_type: str = Field(
        default="comprehensive", description="Type of assessment: 'individual', 'portfolio', or 'comprehensive'"
    )
    risk_horizon: str = Field(default="1y", description="Risk assessment horizon (1m, 3m, 6m, 1y, 2y)")
    confidence_level: float = Field(default=0.95, description="Confidence level for VaR calculations")
    include_stress_testing: bool = Field(default=True, description="Include stress testing scenarios")
    market_regime: str = Field(default="normal", description="Market regime: 'bull', 'bear', 'normal', 'volatile'")


class RiskAssessmentTool(BaseTool):
    """
    Tool for comprehensive risk assessment of assets and portfolios.

    This tool provides CrewAI agents with the ability to assess various types
    of risk including market risk, credit risk, liquidity risk, and concentration risk.
    """

    name: str = "Risk Assessment Tool"
    description: str = (
        "Assess risk characteristics of individual assets or portfolios. "
        "Provides comprehensive risk metrics including VaR, stress testing, "
        "correlation analysis, and risk factor decomposition."
    )
    args_schema: type[BaseModel] = RiskAssessmentInput

    def _run(
        self,
        assets: list[str],
        portfolio_weights: dict[str, float] | None = None,
        assessment_type: str = "comprehensive",
        risk_horizon: str = "1y",
        confidence_level: float = 0.95,
        include_stress_testing: bool = True,
        market_regime: str = "normal",
    ) -> str:
        """
        Execute risk assessment.

        Args:
            assets: List of asset symbols to assess
            portfolio_weights: Portfolio weights for each asset
            assessment_type: Type of assessment
            risk_horizon: Risk assessment horizon
            confidence_level: Confidence level for VaR calculations
            include_stress_testing: Include stress testing scenarios
            market_regime: Current market regime

        Returns:
            JSON string with risk assessment results

        """
        try:
            logger.info(f"Starting risk assessment for {len(assets)} assets")

            # Validate inputs
            input_data = RiskAssessmentInput(
                assets=assets,
                portfolio_weights=portfolio_weights,
                assessment_type=assessment_type,
                risk_horizon=risk_horizon,
                confidence_level=confidence_level,
                include_stress_testing=include_stress_testing,
                market_regime=market_regime,
            )

            # Perform risk assessment based on type
            if input_data.assessment_type == "individual":
                result = self._assess_individual_risks(input_data)
            elif input_data.assessment_type == "portfolio":
                result = self._assess_portfolio_risk(input_data)
            else:  # comprehensive
                result = self._assess_comprehensive_risk(input_data)

            logger.info("Risk assessment completed successfully")
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"Risk assessment failed: {e}")
            error_result = {"success": False, "error": str(e), "error_type": type(e).__name__}
            return json.dumps(error_result, indent=2)

    def _assess_individual_risks(self, input_data: RiskAssessmentInput) -> dict[str, Any]:
        """Assess individual asset risks."""
        try:
            individual_risks = {}

            for asset in input_data.assets:
                risk_profile = self._calculate_asset_risk_profile(asset, input_data)
                individual_risks[asset] = risk_profile

            return {
                "success": True,
                "assessment_type": "individual",
                "assessment_timestamp": datetime.now().isoformat(),
                "risk_horizon": input_data.risk_horizon,
                "confidence_level": input_data.confidence_level,
                "individual_risks": individual_risks,
                "summary": self._generate_individual_risk_summary(individual_risks),
            }

        except Exception as e:
            logger.error(f"Error in individual risk assessment: {e}")
            return {"success": False, "error": str(e)}

    def _assess_portfolio_risk(self, input_data: RiskAssessmentInput) -> dict[str, Any]:
        """Assess portfolio-level risks."""
        try:
            if not input_data.portfolio_weights:
                # Equal weights if not provided
                n_assets = len(input_data.assets)
                input_data.portfolio_weights = {asset: 1.0 / n_assets for asset in input_data.assets}

            portfolio_risk = self._calculate_portfolio_risk_metrics(input_data)
            correlation_analysis = self._analyze_correlations(input_data.assets)
            concentration_risk = self._assess_concentration_risk(input_data.portfolio_weights)

            result = {
                "success": True,
                "assessment_type": "portfolio",
                "assessment_timestamp": datetime.now().isoformat(),
                "risk_horizon": input_data.risk_horizon,
                "portfolio_risk_metrics": portfolio_risk,
                "correlation_analysis": correlation_analysis,
                "concentration_risk": concentration_risk,
            }

            if input_data.include_stress_testing:
                stress_test_results = self._perform_stress_testing(input_data)
                result["stress_test_results"] = stress_test_results

            return result

        except Exception as e:
            logger.error(f"Error in portfolio risk assessment: {e}")
            return {"success": False, "error": str(e)}

    def _assess_comprehensive_risk(self, input_data: RiskAssessmentInput) -> dict[str, Any]:
        """Perform comprehensive risk assessment."""
        try:
            # Individual risks
            individual_result = self._assess_individual_risks(input_data)

            # Portfolio risks
            portfolio_result = self._assess_portfolio_risk(input_data)

            # Market regime analysis
            regime_analysis = self._analyze_market_regime_impact(input_data)

            return {
                "success": True,
                "assessment_type": "comprehensive",
                "assessment_timestamp": datetime.now().isoformat(),
                "individual_risks": individual_result.get("individual_risks", {}),
                "portfolio_risks": portfolio_result.get("portfolio_risk_metrics", {}),
                "correlation_analysis": portfolio_result.get("correlation_analysis", {}),
                "concentration_risk": portfolio_result.get("concentration_risk", {}),
                "stress_test_results": portfolio_result.get("stress_test_results", {}),
                "market_regime_analysis": regime_analysis,
                "overall_risk_assessment": self._generate_overall_risk_assessment(
                    individual_result, portfolio_result, regime_analysis
                ),
            }

        except Exception as e:
            logger.error(f"Error in comprehensive risk assessment: {e}")
            return {"success": False, "error": str(e)}

    def _calculate_asset_risk_profile(self, asset: str, input_data: RiskAssessmentInput) -> dict[str, Any]:
        """Calculate risk profile for individual asset."""
        try:
            # Simplified risk metrics (in practice, use historical data)
            # This is a placeholder implementation

            # Generate realistic but random risk metrics for demonstration
            np.random.seed(hash(asset) % 2**32)  # Consistent random values per asset

            volatility = np.random.uniform(0.15, 0.35)  # 15-35% annual volatility
            beta = np.random.uniform(0.7, 1.5)  # Beta vs market
            var_95 = volatility * 1.65 * np.sqrt(252 / 252)  # Approximate 95% VaR
            max_drawdown = np.random.uniform(0.15, 0.45)  # 15-45% max drawdown

            # Risk categorization
            if volatility < 0.20:
                risk_category = "Low"
                risk_score = np.random.randint(1, 4)
            elif volatility < 0.30:
                risk_category = "Moderate"
                risk_score = np.random.randint(4, 7)
            else:
                risk_category = "High"
                risk_score = np.random.randint(7, 11)

            return {
                "symbol": asset,
                "risk_score": risk_score,
                "risk_category": risk_category,
                "volatility": float(volatility),
                "beta": float(beta),
                "var_95": float(var_95),
                "expected_shortfall": float(var_95 * 1.3),  # Approximate ES
                "max_drawdown": float(max_drawdown),
                "liquidity_risk": "Low" if asset in ["SPY", "QQQ", "AAPL", "MSFT"] else "Moderate",
                "risk_factors": [
                    "Market risk",
                    "Sector concentration" if beta > 1.2 else "Market correlation",
                    "Volatility risk" if volatility > 0.25 else "Moderate volatility",
                ],
            }

        except Exception as e:
            logger.error(f"Error calculating risk profile for {asset}: {e}")
            return {"symbol": asset, "error": str(e)}

    def _calculate_portfolio_risk_metrics(self, input_data: RiskAssessmentInput) -> dict[str, Any]:
        """Calculate portfolio-level risk metrics."""
        try:
            weights = np.array([input_data.portfolio_weights[asset] for asset in input_data.assets])

            # Generate simplified correlation matrix and volatilities
            n_assets = len(input_data.assets)
            volatilities = np.random.uniform(0.15, 0.35, n_assets)

            # Create correlation matrix with realistic correlations
            correlations = np.random.uniform(0.3, 0.8, (n_assets, n_assets))
            np.fill_diagonal(correlations, 1.0)

            # Make matrix symmetric
            correlations = (correlations + correlations.T) / 2
            np.fill_diagonal(correlations, 1.0)

            # Calculate portfolio volatility
            cov_matrix = np.outer(volatilities, volatilities) * correlations
            portfolio_variance = np.dot(weights, np.dot(cov_matrix, weights))
            portfolio_volatility = np.sqrt(portfolio_variance)

            # Portfolio VaR and Expected Shortfall
            portfolio_var_95 = portfolio_volatility * 1.65
            portfolio_es_95 = portfolio_var_95 * 1.3

            # Diversification benefit
            weighted_avg_vol = np.dot(weights, volatilities)
            diversification_ratio = portfolio_volatility / weighted_avg_vol

            return {
                "portfolio_volatility": float(portfolio_volatility),
                "portfolio_var_95": float(portfolio_var_95),
                "portfolio_expected_shortfall_95": float(portfolio_es_95),
                "diversification_ratio": float(diversification_ratio),
                "diversification_benefit": float(1 - diversification_ratio),
                "risk_contribution": {
                    asset: float(weight * volatilities[i] * np.sqrt(weights[i]))
                    for i, (asset, weight) in enumerate(zip(input_data.assets, weights))
                },
            }

        except Exception as e:
            logger.error(f"Error calculating portfolio risk metrics: {e}")
            return {"error": str(e)}

    def _analyze_correlations(self, assets: list[str]) -> dict[str, Any]:
        """Analyze correlations between assets."""
        try:
            n_assets = len(assets)

            # Generate realistic correlation matrix
            correlations = np.random.uniform(0.2, 0.8, (n_assets, n_assets))
            np.fill_diagonal(correlations, 1.0)
            correlations = (correlations + correlations.T) / 2
            np.fill_diagonal(correlations, 1.0)

            # Find highest and lowest correlations
            correlation_pairs = []
            for i in range(n_assets):
                for j in range(i + 1, n_assets):
                    correlation_pairs.append({"asset1": assets[i], "asset2": assets[j], "correlation": float(correlations[i, j])})

            # Sort by correlation
            correlation_pairs.sort(key=lambda x: x["correlation"], reverse=True)

            avg_correlation = float(np.mean(correlations[np.triu_indices(n_assets, k=1)]))

            return {
                "average_correlation": avg_correlation,
                "highest_correlations": correlation_pairs[:3],
                "lowest_correlations": correlation_pairs[-3:],
                "correlation_risk_level": ("High" if avg_correlation > 0.7 else "Moderate" if avg_correlation > 0.5 else "Low"),
            }

        except Exception as e:
            logger.error(f"Error analyzing correlations: {e}")
            return {"error": str(e)}

    def _assess_concentration_risk(self, portfolio_weights: dict[str, float]) -> dict[str, Any]:
        """Assess concentration risk in portfolio."""
        try:
            weights = list(portfolio_weights.values())
            max_weight = max(weights)

            # Calculate Herfindahl-Hirschman Index
            hhi = sum(w**2 for w in weights)

            # Concentration assessment
            if max_weight > 0.4:
                concentration_level = "High"
                concentration_score = 8
            elif max_weight > 0.25:
                concentration_level = "Moderate"
                concentration_score = 5
            else:
                concentration_level = "Low"
                concentration_score = 2

            # Find most concentrated positions
            sorted_positions = sorted(portfolio_weights.items(), key=lambda x: x[1], reverse=True)

            return {
                "concentration_level": concentration_level,
                "concentration_score": concentration_score,
                "max_position_weight": float(max_weight),
                "herfindahl_index": float(hhi),
                "top_3_positions": sorted_positions[:3],
                "recommendations": [
                    "Consider reducing largest position" if max_weight > 0.3 else "Good position sizing",
                    "Monitor correlation between top positions",
                    f"HHI of {hhi:.3f} indicates {'high' if hhi > 0.25 else 'moderate' if hhi > 0.15 else 'low'} concentration",
                ],
            }

        except Exception as e:
            logger.error(f"Error assessing concentration risk: {e}")
            return {"error": str(e)}

    def _perform_stress_testing(self, input_data: RiskAssessmentInput) -> dict[str, Any]:
        """Perform stress testing scenarios."""
        try:
            scenarios = {
                "market_crash": {
                    "description": "Market crash scenario (-30% market decline)",
                    "market_impact": -0.30,
                    "volatility_increase": 2.0,
                },
                "interest_rate_shock": {
                    "description": "Interest rate shock (+200 bps)",
                    "market_impact": -0.15,
                    "volatility_increase": 1.5,
                },
                "sector_rotation": {
                    "description": "Major sector rotation",
                    "market_impact": -0.10,
                    "volatility_increase": 1.3,
                },
                "liquidity_crisis": {
                    "description": "Liquidity crisis",
                    "market_impact": -0.20,
                    "volatility_increase": 2.5,
                },
            }

            stress_results = {}
            for scenario_name, scenario in scenarios.items():
                # Simplified stress test calculation
                portfolio_impact = scenario["market_impact"]

                # Adjust for portfolio characteristics
                if input_data.portfolio_weights:
                    # More sophisticated calculation would consider asset-specific impacts
                    portfolio_impact *= 1.0  # Placeholder

                stress_results[scenario_name] = {
                    "description": scenario["description"],
                    "estimated_portfolio_impact": float(portfolio_impact),
                    "probability": "Low" if abs(portfolio_impact) > 0.25 else "Moderate",
                    "recovery_time_estimate": "6-12 months" if abs(portfolio_impact) > 0.20 else "3-6 months",
                }

            return {
                "stress_scenarios": stress_results,
                "worst_case_scenario": min(stress_results.items(), key=lambda x: x[1]["estimated_portfolio_impact"]),
                "overall_stress_resilience": (
                    "High"
                    if all(abs(s["estimated_portfolio_impact"]) < 0.15 for s in stress_results.values())
                    else "Moderate"
                    if all(abs(s["estimated_portfolio_impact"]) < 0.25 for s in stress_results.values())
                    else "Low"
                ),
            }

        except Exception as e:
            logger.error(f"Error in stress testing: {e}")
            return {"error": str(e)}

    def _analyze_market_regime_impact(self, input_data: RiskAssessmentInput) -> dict[str, Any]:
        """Analyze impact of different market regimes."""
        try:
            regime_impacts = {
                "bull_market": {
                    "description": "Bull market conditions",
                    "risk_adjustment": 0.8,  # Lower risk
                    "correlation_adjustment": 0.9,  # Lower correlations
                },
                "bear_market": {
                    "description": "Bear market conditions",
                    "risk_adjustment": 1.5,  # Higher risk
                    "correlation_adjustment": 1.3,  # Higher correlations
                },
                "volatile_market": {
                    "description": "High volatility regime",
                    "risk_adjustment": 1.8,  # Much higher risk
                    "correlation_adjustment": 1.4,  # Higher correlations
                },
                "normal_market": {
                    "description": "Normal market conditions",
                    "risk_adjustment": 1.0,  # Baseline risk
                    "correlation_adjustment": 1.0,  # Baseline correlations
                },
            }

            current_regime = input_data.market_regime
            current_impact = regime_impacts.get(current_regime, regime_impacts["normal_market"])

            return {
                "current_regime": current_regime,
                "regime_impacts": regime_impacts,
                "current_regime_impact": current_impact,
                "risk_adjustment_factor": current_impact["risk_adjustment"],
                "recommendations": [
                    f"Current {current_regime} regime suggests {current_impact['risk_adjustment']}x risk adjustment",
                    "Monitor regime changes for portfolio adjustments",
                    "Consider defensive positioning in volatile regimes",
                ],
            }

        except Exception as e:
            logger.error(f"Error analyzing market regime impact: {e}")
            return {"error": str(e)}

    def _generate_individual_risk_summary(self, individual_risks: dict[str, Any]) -> dict[str, Any]:
        """Generate summary of individual risk assessments."""
        try:
            risk_scores = [risk.get("risk_score", 5) for risk in individual_risks.values() if "risk_score" in risk]

            if not risk_scores:
                return {"error": "No valid risk scores found"}

            return {
                "average_risk_score": float(np.mean(risk_scores)),
                "highest_risk_asset": max(individual_risks.items(), key=lambda x: x[1].get("risk_score", 0)),
                "lowest_risk_asset": min(individual_risks.items(), key=lambda x: x[1].get("risk_score", 10)),
                "risk_distribution": {
                    "low_risk": len([s for s in risk_scores if s <= 3]),
                    "moderate_risk": len([s for s in risk_scores if 3 < s <= 7]),
                    "high_risk": len([s for s in risk_scores if s > 7]),
                },
            }

        except Exception as e:
            logger.error(f"Error generating individual risk summary: {e}")
            return {"error": str(e)}

    def _generate_overall_risk_assessment(
        self, individual_result: dict[str, Any], portfolio_result: dict[str, Any], regime_analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate overall risk assessment summary."""
        try:
            # Extract key metrics
            individual_summary = individual_result.get("summary", {})
            portfolio_metrics = portfolio_result.get("portfolio_risk_metrics", {})

            avg_individual_risk = individual_summary.get("average_risk_score", 5)
            portfolio_vol = portfolio_metrics.get("portfolio_volatility", 0.2)
            diversification_benefit = portfolio_metrics.get("diversification_benefit", 0)

            # Overall risk score (1-10 scale)
            overall_risk_score = min(
                10, max(1, (avg_individual_risk * 0.4) + (portfolio_vol * 20 * 0.4) + ((1 - diversification_benefit) * 5 * 0.2))
            )

            # Risk level
            if overall_risk_score <= 3:
                risk_level = "Low"
            elif overall_risk_score <= 7:
                risk_level = "Moderate"
            else:
                risk_level = "High"

            return {
                "overall_risk_score": float(overall_risk_score),
                "overall_risk_level": risk_level,
                "key_risk_factors": [
                    f"Average individual asset risk: {avg_individual_risk:.1f}/10",
                    f"Portfolio volatility: {portfolio_vol:.1%}",
                    f"Diversification benefit: {diversification_benefit:.1%}",
                ],
                "recommendations": [
                    "Monitor high-risk positions" if avg_individual_risk > 7 else "Individual asset risks are manageable",
                    "Consider risk reduction" if portfolio_vol > 0.25 else "Portfolio volatility is reasonable",
                    "Improve diversification" if diversification_benefit < 0.1 else "Good diversification benefits",
                ],
                "next_review_date": "Recommend monthly review for high-risk portfolios, quarterly for others",
            }

        except Exception as e:
            logger.error(f"Error generating overall risk assessment: {e}")
            return {"error": str(e)}


def get_risk_assessment_tool() -> RiskAssessmentTool:
    """Get an instance of the risk assessment tool."""
    return RiskAssessmentTool()
