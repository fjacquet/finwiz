"""
Scenario Analysis for Portfolio Rebalancing.

This module provides scenario analysis functionality including
sensitivity analysis, scenario comparison, and comprehensive
analysis reporting for portfolio rebalancing decisions.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from finwiz.quantitative.scenario_generators import MonteCarloResult, ScenarioParameters
from finwiz.schemas.portfolio_rebalancing import (
    AlternativeScenario,
    PortfolioConfiguration,
)

logger = logging.getLogger(__name__)


class SensitivityResult(BaseModel):
    """Result of sensitivity analysis for a single parameter."""

    model_config = ConfigDict(extra="forbid")

    parameter_name: str = Field(..., description="Name of the parameter analyzed")
    parameter_values: list[float] = Field(..., description="Parameter values tested")
    impact_on_return: list[float] = Field(..., description="Impact on expected return")
    impact_on_risk: list[float] = Field(..., description="Impact on risk")
    impact_on_cost: list[float] = Field(..., description="Impact on transaction costs")


class ScenarioComparison(BaseModel):
    """Comparison between different scenarios."""

    model_config = ConfigDict(extra="forbid")

    scenario_1_name: str = Field(..., description="Name of first scenario")
    scenario_2_name: str = Field(..., description="Name of second scenario")
    return_difference: float = Field(..., description="Difference in expected return")
    risk_difference: float = Field(..., description="Difference in risk")
    cost_difference: float = Field(..., description="Difference in costs")
    recommendation: str = Field(..., description="Which scenario is recommended")
    confidence_level: float = Field(..., description="Confidence in recommendation (0-1)")


class ScenarioAnalysisReport(BaseModel):
    """Comprehensive scenario analysis report."""

    model_config = ConfigDict(extra="forbid")

    # Analysis metadata
    analysis_date: datetime = Field(default_factory=datetime.now, description="When analysis was performed")
    base_configuration: PortfolioConfiguration = Field(..., description="Base portfolio configuration")

    # Analysis results
    scenarios: list[AlternativeScenario] = Field(default_factory=list, description="Alternative scenarios analyzed")
    sensitivity_results: list[SensitivityResult] = Field(default_factory=list, description="Sensitivity analysis results")
    monte_carlo_result: MonteCarloResult | None = Field(None, description="Monte Carlo simulation results")
    scenario_comparisons: list[ScenarioComparison] = Field(default_factory=list, description="Scenario comparisons")

    # Recommendations
    optimal_parameters: dict[str, Any] = Field(default_factory=dict, description="Recommended optimal parameters")
    risk_warnings: list[str] = Field(default_factory=list, description="Risk warnings and considerations")
    implementation_notes: list[str] = Field(default_factory=list, description="Implementation recommendations")
    executive_summary: str = Field(..., description="Executive summary of findings")


class ScenarioAnalysisEngine:
    """
    Engine for comprehensive scenario analysis.

    This class provides methods for analyzing scenarios, performing sensitivity
    analysis, and generating comprehensive reports for portfolio rebalancing
    decisions.
    """

    def __init__(self) -> None:
        """Initialize the scenario analysis engine."""
        self.logger = logging.getLogger(__name__)

    async def analyze_single_scenario(
        self,
        scenario_name: str,
        scenario_config: PortfolioConfiguration,
        base_config: PortfolioConfiguration,
    ) -> AlternativeScenario:
        """
        Analyze a single scenario configuration.

        Args:
            scenario_name: Name of the scenario
            scenario_config: Scenario configuration to analyze
            base_config: Base configuration for comparison

        Returns:
            AlternativeScenario with calculated metrics

        """
        self.logger.debug(f"Analyzing scenario: {scenario_name}")

        # Simplified analysis - in practice, this would involve complex calculations
        # For now, we'll use placeholder calculations

        # Calculate expected return (simplified)
        expected_return = 0.08  # Base return
        if hasattr(scenario_config, "additional_capital") and scenario_config.additional_capital:
            expected_return += scenario_config.additional_capital * 0.00001  # Small impact

        # Calculate expected risk (simplified)
        expected_risk = 0.15  # Base risk
        if scenario_config.tolerance_band != base_config.tolerance_band:
            expected_risk *= 1 + (scenario_config.tolerance_band - base_config.tolerance_band)

        # Calculate cost difference (simplified)
        base_cost = base_config.transaction_cost_rate * 100  # Simplified cost calculation
        scenario_cost = scenario_config.transaction_cost_rate * 100
        cost_difference = scenario_cost - base_cost

        # Calculate risk difference
        base_risk = 0.15  # Simplified base risk
        risk_difference = expected_risk - base_risk

        return AlternativeScenario(
            name=scenario_name,
            description=f"Analysis of {scenario_name}",
            configuration=scenario_config,
            expected_return=expected_return,
            expected_risk=expected_risk,
            cost_difference=cost_difference,
            risk_difference=risk_difference,
        )

    async def run_sensitivity_analysis(
        self,
        base_config: PortfolioConfiguration,
        parameters: ScenarioParameters,
    ) -> list[SensitivityResult]:
        """
        Run sensitivity analysis on key parameters.

        Args:
            base_config: Base portfolio configuration
            parameters: Parameters to analyze

        Returns:
            List of sensitivity analysis results

        """
        self.logger.info("Running sensitivity analysis")
        sensitivity_results = []

        # Analyze tolerance band sensitivity
        tolerance_result = await self._analyze_parameter_sensitivity(
            "tolerance_band",
            parameters.tolerance_levels,
            base_config,
            lambda config, value: setattr(config, "tolerance_band", value),
        )
        sensitivity_results.append(tolerance_result)

        # Analyze transaction cost sensitivity
        cost_result = await self._analyze_parameter_sensitivity(
            "transaction_cost_rate",
            parameters.transaction_cost_rates,
            base_config,
            lambda config, value: setattr(config, "transaction_cost_rate", value),
        )
        sensitivity_results.append(cost_result)

        self.logger.info(f"Completed sensitivity analysis for {len(sensitivity_results)} parameters")
        return sensitivity_results

    async def _analyze_parameter_sensitivity(
        self,
        parameter_name: str,
        parameter_values: list[float],
        base_config: PortfolioConfiguration,
        setter_func: Callable[..., Any],
    ) -> SensitivityResult:
        """
        Analyze sensitivity for a single parameter.

        Args:
            parameter_name: Name of the parameter
            parameter_values: Values to test
            base_config: Base configuration
            setter_func: Function to set the parameter value

        Returns:
            SensitivityResult with analysis results

        """
        impact_on_return = []
        impact_on_risk = []
        impact_on_cost = []

        for value in parameter_values:
            # Create modified configuration
            test_config = base_config.model_copy(deep=True)
            setter_func(test_config, value)

            # Analyze scenario (simplified calculations)
            scenario = await self.analyze_single_scenario(f"{parameter_name}_{value}", test_config, base_config)

            impact_on_return.append(scenario.expected_return)
            impact_on_risk.append(scenario.expected_risk)
            impact_on_cost.append(scenario.cost_difference)

        return SensitivityResult(
            parameter_name=parameter_name,
            parameter_values=parameter_values,
            impact_on_return=impact_on_return,
            impact_on_risk=impact_on_risk,
            impact_on_cost=impact_on_cost,
        )

    def determine_optimal_parameters(self, sensitivity_results: list[SensitivityResult], monte_carlo_result: MonteCarloResult) -> dict[str, Any]:
        """
        Determine optimal parameters based on analysis results.

        Args:
            sensitivity_results: Results from sensitivity analysis
            monte_carlo_result: Results from Monte Carlo simulation

        Returns:
            Dictionary with optimal parameter recommendations

        """
        optimal_params: dict[str, Any] = {}

        # Analyze each parameter's sensitivity
        for result in sensitivity_results:
            if result.parameter_name == "tolerance_band":
                # Find tolerance that minimizes cost while maintaining reasonable risk
                min_cost_idx = result.impact_on_cost.index(min(result.impact_on_cost))
                optimal_params["tolerance_band"] = result.parameter_values[min_cost_idx]

            elif result.parameter_name == "transaction_cost_rate":
                # This is typically externally determined, but we can note the impact
                optimal_params["transaction_cost_sensitivity"] = max(result.impact_on_cost) - min(result.impact_on_cost)

        # Use Monte Carlo results to inform recommendations
        if monte_carlo_result:
            optimal_params["expected_rebalancing_frequency"] = monte_carlo_result.mean_rebalancing_frequency
            optimal_params["risk_tolerance_recommendation"] = "Conservative" if monte_carlo_result.probability_of_loss > 0.3 else "Moderate"

        return optimal_params

    def generate_risk_warnings(self, monte_carlo_result: MonteCarloResult, sensitivity_results: list[SensitivityResult]) -> list[str]:
        """
        Generate risk warnings based on analysis results.

        Args:
            monte_carlo_result: Monte Carlo simulation results
            sensitivity_results: Sensitivity analysis results

        Returns:
            List of risk warnings

        """
        warnings = []

        if monte_carlo_result:
            if monte_carlo_result.probability_of_loss > 0.25:
                warnings.append(f"High probability of loss: {monte_carlo_result.probability_of_loss:.1%}")

            if monte_carlo_result.std_rebalancing_frequency > monte_carlo_result.mean_rebalancing_frequency:
                warnings.append("High variability in rebalancing frequency - consider more stable parameters")

            if monte_carlo_result.value_at_risk_95 < -0.15:
                warnings.append(f"Significant downside risk: 95% VaR = {monte_carlo_result.value_at_risk_95:.1%}")

        # Check sensitivity results for high parameter sensitivity
        for result in sensitivity_results:
            cost_range = max(result.impact_on_cost) - min(result.impact_on_cost)
            if cost_range > 1000:  # Arbitrary threshold
                warnings.append(f"High sensitivity to {result.parameter_name} - small changes have large cost impact")

        return warnings

    def create_executive_summary(
        self,
        optimal_parameters: dict[str, Any],
        monte_carlo_result: MonteCarloResult,
        scenario_comparisons: list[ScenarioComparison],
        risk_warnings: list[str],
    ) -> str:
        """
        Create executive summary of scenario analysis.

        Args:
            optimal_parameters: Optimal parameters
            monte_carlo_result: Monte Carlo results
            scenario_comparisons: Scenario comparisons
            risk_warnings: Risk warnings

        Returns:
            Executive summary string

        """
        summary_parts = []

        # Overview
        summary_parts.append("SCENARIO ANALYSIS EXECUTIVE SUMMARY")
        summary_parts.append("=" * 40)

        # Key findings
        if monte_carlo_result:
            summary_parts.append(f"Expected rebalancing frequency: {monte_carlo_result.mean_rebalancing_frequency:.1f} times per year")
            summary_parts.append(f"Expected transaction costs: ${monte_carlo_result.mean_transaction_costs:.0f}")
            summary_parts.append(f"Probability of loss: {monte_carlo_result.probability_of_loss:.1%}")

        # Optimal parameters
        if optimal_parameters:
            summary_parts.append("\nRECOMMENDED PARAMETERS:")
            for param, value in optimal_parameters.items():
                if isinstance(value, float):
                    summary_parts.append(f"- {param}: {value:.3f}")
                else:
                    summary_parts.append(f"- {param}: {value}")

        # Risk warnings
        if risk_warnings:
            summary_parts.append(f"\nRISK CONSIDERATIONS ({len(risk_warnings)} items):")
            for warning in risk_warnings[:3]:  # Show top 3 warnings
                summary_parts.append(f"- {warning}")

        # Scenario recommendations
        high_confidence_scenarios = [comp for comp in scenario_comparisons if comp.confidence_level > 0.7]
        if high_confidence_scenarios:
            summary_parts.append(f"\nHIGH-CONFIDENCE RECOMMENDATIONS: {len(high_confidence_scenarios)} scenarios identified")

        summary_parts.append("\nRecommendation: Proceed with suggested parameters and monitor performance quarterly.")

        return "\n".join(summary_parts)
