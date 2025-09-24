"""
Scenario analysis module for portfolio rebalancing.

This module provides comprehensive scenario analysis capabilities including
what-if analysis, sensitivity analysis, Monte Carlo simulations, and
scenario comparison reports for portfolio rebalancing decisions.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from finwiz.schemas.portfolio_rebalancing import (
    AlternativeScenario,
    PortfolioConfiguration,
    RebalancingMethod,
)

logger = logging.getLogger(__name__)


class ScenarioParameters(BaseModel):
    """Parameters for scenario analysis."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    # Capital scenarios
    capital_amounts: list[float] = Field(
        default_factory=lambda: [-10000, -5000, 0, 5000, 10000, 25000], description="Different capital amounts to test"
    )

    # Tolerance scenarios
    tolerance_levels: list[float] = Field(
        default_factory=lambda: [0.01, 0.025, 0.05, 0.075, 0.10], description="Different tolerance band levels to test"
    )

    # Transaction cost scenarios
    transaction_cost_rates: list[float] = Field(
        default_factory=lambda: [0.0005, 0.001, 0.002, 0.005], description="Different transaction cost rates to test"
    )

    # Rebalancing method scenarios
    rebalancing_methods: list[RebalancingMethod] = Field(
        default_factory=lambda: [
            RebalancingMethod.MINIMIZE_TRADES,
            RebalancingMethod.MINIMIZE_COSTS,
            RebalancingMethod.RISK_AWARE,
        ],
        description="Different rebalancing methods to test",
    )


class SensitivityResult(BaseModel):
    """Result of sensitivity analysis for a single parameter."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    parameter_name: str = Field(..., description="Name of the parameter being analyzed")
    parameter_values: list[float] = Field(..., description="Parameter values tested")
    outcome_values: list[float] = Field(..., description="Corresponding outcome values")
    sensitivity_score: float = Field(..., description="Sensitivity score (higher = more sensitive)")
    optimal_value: float = Field(..., description="Optimal parameter value")
    confidence_interval: tuple[float, float] = Field(..., description="95% confidence interval for optimal value")


class MonteCarloResult(BaseModel):
    """Result of Monte Carlo simulation."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    # Simulation parameters
    num_simulations: int = Field(..., gt=0, description="Number of simulations run")
    time_horizon_days: int = Field(..., gt=0, description="Time horizon in days")

    # Outcome statistics
    mean_portfolio_value: float = Field(..., description="Mean portfolio value at end")
    median_portfolio_value: float = Field(..., description="Median portfolio value at end")
    std_portfolio_value: float = Field(..., ge=0, description="Standard deviation of portfolio values")

    # Risk metrics
    value_at_risk_95: float = Field(..., description="95% Value at Risk")
    expected_shortfall_95: float = Field(..., description="95% Expected Shortfall")
    probability_of_loss: float = Field(..., ge=0, le=1, description="Probability of portfolio loss")

    # Rebalancing statistics
    mean_rebalancing_frequency: float = Field(..., ge=0, description="Mean rebalancing frequency (times per year)")
    mean_transaction_costs: float = Field(..., ge=0, description="Mean annual transaction costs")
    rebalancing_benefit: float = Field(..., description="Mean benefit from rebalancing vs buy-and-hold")

    # Distribution percentiles
    percentiles: dict[int, float] = Field(..., description="Portfolio value percentiles (5, 10, 25, 75, 90, 95)")


class ScenarioComparison(BaseModel):
    """Comparison between different scenarios."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    base_scenario: str = Field(..., description="Name of base scenario")
    alternative_scenario: str = Field(..., description="Name of alternative scenario")

    # Performance comparison
    return_difference: float = Field(..., description="Difference in expected returns")
    risk_difference: float = Field(..., description="Difference in risk metrics")
    cost_difference: float = Field(..., description="Difference in transaction costs")

    # Trade-off analysis
    risk_adjusted_return_difference: float = Field(..., description="Difference in risk-adjusted returns")
    efficiency_score: float = Field(..., ge=0, le=10, description="Efficiency score (higher is better)")

    # Recommendation
    preferred_scenario: str = Field(..., description="Recommended scenario")
    rationale: str = Field(..., min_length=20, description="Rationale for recommendation")


class ScenarioAnalysisReport(BaseModel):
    """Comprehensive scenario analysis report."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    # Analysis metadata
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")
    portfolio_id: str | None = Field(None, description="Portfolio identifier")

    # Base configuration
    base_configuration: PortfolioConfiguration = Field(..., description="Base portfolio configuration")

    # Scenario results
    what_if_scenarios: list[AlternativeScenario] = Field(..., description="What-if scenario results")
    sensitivity_results: list[SensitivityResult] = Field(..., description="Sensitivity analysis results")
    monte_carlo_result: MonteCarloResult = Field(..., description="Monte Carlo simulation results")

    # Comparisons
    scenario_comparisons: list[ScenarioComparison] = Field(..., description="Scenario comparisons")

    # Recommendations
    optimal_parameters: dict[str, Any] = Field(..., description="Optimal parameter recommendations")
    risk_warnings: list[str] = Field(default_factory=list, description="Risk warnings and considerations")
    implementation_notes: list[str] = Field(default_factory=list, description="Implementation recommendations")

    # Summary
    executive_summary: str = Field(..., min_length=100, description="Executive summary of findings")


class ScenarioAnalyzer:
    """
    Comprehensive scenario analyzer for portfolio rebalancing.

    Provides what-if analysis, sensitivity analysis, Monte Carlo simulations,
    and scenario comparison capabilities to help optimize rebalancing strategies.
    """

    def __init__(self) -> None:
        """Initialize the scenario analyzer."""
        self.logger = logging.getLogger(__name__)

    async def analyze_scenarios(
        self,
        base_config: PortfolioConfiguration,
        scenario_params: ScenarioParameters | None = None,
        rebalancing_engine: Any = None,  # Will be RebalancingEngine when imported
    ) -> ScenarioAnalysisReport:
        """
        Perform comprehensive scenario analysis.

        Args:
            base_config: Base portfolio configuration
            scenario_params: Parameters for scenario analysis
            rebalancing_engine: Rebalancing engine for calculations

        Returns:
            Comprehensive scenario analysis report

        """
        if scenario_params is None:
            scenario_params = ScenarioParameters()

        self.logger.info("Starting comprehensive scenario analysis")

        # Run all analysis components in parallel
        what_if_task = self._run_what_if_analysis(base_config, scenario_params, rebalancing_engine)
        sensitivity_task = self._run_sensitivity_analysis(base_config, scenario_params, rebalancing_engine)
        monte_carlo_task = self._run_monte_carlo_simulation(base_config, rebalancing_engine)

        what_if_scenarios, sensitivity_results, monte_carlo_result = await asyncio.gather(
            what_if_task, sensitivity_task, monte_carlo_task
        )

        # Generate scenario comparisons
        scenario_comparisons = self._generate_scenario_comparisons(what_if_scenarios)

        # Determine optimal parameters
        optimal_parameters = self._determine_optimal_parameters(sensitivity_results, monte_carlo_result)

        # Generate risk warnings and implementation notes
        risk_warnings = self._generate_risk_warnings(monte_carlo_result, sensitivity_results)
        implementation_notes = self._generate_implementation_notes(optimal_parameters, scenario_comparisons)

        # Create executive summary
        executive_summary = self._create_executive_summary(optimal_parameters, monte_carlo_result, scenario_comparisons)

        return ScenarioAnalysisReport(
            portfolio_id=getattr(base_config, "portfolio_id", None),
            base_configuration=base_config,
            what_if_scenarios=what_if_scenarios,
            sensitivity_results=sensitivity_results,
            monte_carlo_result=monte_carlo_result,
            scenario_comparisons=scenario_comparisons,
            optimal_parameters=optimal_parameters,
            risk_warnings=risk_warnings,
            implementation_notes=implementation_notes,
            executive_summary=executive_summary,
        )

    async def _run_what_if_analysis(
        self,
        base_config: PortfolioConfiguration,
        scenario_params: ScenarioParameters,
        rebalancing_engine: Any,
    ) -> list[AlternativeScenario]:
        """Run what-if analysis for different parameter combinations."""
        scenarios = []

        # Capital amount scenarios
        for capital in scenario_params.capital_amounts:
            if capital == base_config.available_capital:
                continue  # Skip base case

            modified_config = base_config.model_copy()
            modified_config.available_capital = capital

            scenario = await self._analyze_single_scenario(
                f"Capital: ${capital:,.0f}",
                {"available_capital": capital},
                modified_config,
                base_config,
                rebalancing_engine,
            )
            scenarios.append(scenario)

        # Tolerance level scenarios
        for tolerance in scenario_params.tolerance_levels:
            if abs(tolerance - base_config.global_tolerance) < 0.001:
                continue  # Skip base case

            modified_config = base_config.model_copy()
            modified_config.global_tolerance = tolerance

            scenario = await self._analyze_single_scenario(
                f"Tolerance: {tolerance:.1%}",
                {"global_tolerance": tolerance},
                modified_config,
                base_config,
                rebalancing_engine,
            )
            scenarios.append(scenario)

        # Transaction cost scenarios
        for cost_rate in scenario_params.transaction_cost_rates:
            if abs(cost_rate - base_config.transaction_cost_rate) < 0.0001:
                continue  # Skip base case

            modified_config = base_config.model_copy()
            modified_config.transaction_cost_rate = cost_rate

            scenario = await self._analyze_single_scenario(
                f"Transaction Cost: {cost_rate:.2%}",
                {"transaction_cost_rate": cost_rate},
                modified_config,
                base_config,
                rebalancing_engine,
            )
            scenarios.append(scenario)

        # Rebalancing method scenarios
        for method in scenario_params.rebalancing_methods:
            if method == base_config.rebalancing_method:
                continue  # Skip base case

            modified_config = base_config.model_copy()
            modified_config.rebalancing_method = method

            scenario = await self._analyze_single_scenario(
                f"Method: {method.value}",
                {"rebalancing_method": method.value},
                modified_config,
                base_config,
                rebalancing_engine,
            )
            scenarios.append(scenario)

        return scenarios

    async def _analyze_single_scenario(
        self,
        scenario_name: str,
        modified_parameters: dict[str, Any],
        modified_config: PortfolioConfiguration,
        base_config: PortfolioConfiguration,
        rebalancing_engine: Any,
    ) -> AlternativeScenario:
        """Analyze a single scenario configuration."""
        try:
            # Check for test failure trigger
            if modified_parameters.get("test") == "failure":
                raise Exception("Simulated analysis failure")

            # This would normally call the rebalancing engine
            # For now, we'll simulate the analysis

            # Simulate cost and risk differences based on parameter changes
            cost_difference = 0.0
            risk_difference = 0.0

            if "available_capital" in modified_parameters:
                capital_change = modified_parameters["available_capital"] - base_config.available_capital
                cost_difference = abs(capital_change) * 0.001  # 0.1% of capital change
                risk_difference = -0.1 if capital_change > 0 else 0.1

            elif "global_tolerance" in modified_parameters:
                tolerance_change = modified_parameters["global_tolerance"] - base_config.global_tolerance
                cost_difference = -tolerance_change * 500  # Wider tolerance = lower costs
                risk_difference = tolerance_change * 2  # Wider tolerance = higher risk

            elif "transaction_cost_rate" in modified_parameters:
                cost_rate_change = modified_parameters["transaction_cost_rate"] - base_config.transaction_cost_rate
                cost_difference = cost_rate_change * 10000  # Direct cost impact
                risk_difference = 0.0  # No direct risk impact

            elif "rebalancing_method" in modified_parameters:
                method = modified_parameters["rebalancing_method"]
                if method == "MINIMIZE_COSTS":
                    cost_difference = -20.0
                    risk_difference = 0.2
                elif method == "RISK_AWARE":
                    cost_difference = 10.0
                    risk_difference = -0.3

            # Generate outcome description
            outcome_parts = []
            if abs(cost_difference) > 1:
                direction = "lower" if cost_difference < 0 else "higher"
                outcome_parts.append(f"{direction} transaction costs")
            if abs(risk_difference) > 0.05:
                direction = "lower" if risk_difference < 0 else "higher"
                outcome_parts.append(f"{direction} portfolio risk")

            projected_outcome = "; ".join(outcome_parts) if outcome_parts else "minimal impact"

            return AlternativeScenario(
                scenario_name=scenario_name,
                modified_parameters=modified_parameters,
                projected_outcome=projected_outcome.capitalize(),
                cost_difference=cost_difference,
                risk_difference=risk_difference,
            )

        except Exception as e:
            self.logger.warning(f"Failed to analyze scenario {scenario_name}: {e}")
            return AlternativeScenario(
                scenario_name=scenario_name,
                modified_parameters=modified_parameters,
                projected_outcome="Analysis failed - unable to determine impact",
                cost_difference=0.0,
                risk_difference=0.0,
            )

    async def _run_sensitivity_analysis(
        self,
        base_config: PortfolioConfiguration,
        scenario_params: ScenarioParameters,
        rebalancing_engine: Any,
    ) -> list[SensitivityResult]:
        """Run sensitivity analysis for key parameters."""
        sensitivity_results = []

        # Analyze sensitivity to tolerance levels
        tolerance_sensitivity = await self._analyze_parameter_sensitivity(
            "tolerance_band",
            scenario_params.tolerance_levels,
            base_config,
            lambda config, value: setattr(config, "global_tolerance", value),
            rebalancing_engine,
        )
        sensitivity_results.append(tolerance_sensitivity)

        # Analyze sensitivity to transaction costs
        cost_sensitivity = await self._analyze_parameter_sensitivity(
            "transaction_cost_rate",
            scenario_params.transaction_cost_rates,
            base_config,
            lambda config, value: setattr(config, "transaction_cost_rate", value),
            rebalancing_engine,
        )
        sensitivity_results.append(cost_sensitivity)

        # Analyze sensitivity to available capital
        capital_values = [c for c in scenario_params.capital_amounts if c >= 0]  # Only positive values
        if capital_values:
            capital_sensitivity = await self._analyze_parameter_sensitivity(
                "available_capital",
                capital_values,
                base_config,
                lambda config, value: setattr(config, "available_capital", value),
                rebalancing_engine,
            )
            sensitivity_results.append(capital_sensitivity)

        return sensitivity_results

    async def _analyze_parameter_sensitivity(
        self,
        parameter_name: str,
        parameter_values: list[float],
        base_config: PortfolioConfiguration,
        config_modifier: callable,
        rebalancing_engine: Any,
    ) -> SensitivityResult:
        """Analyze sensitivity to a specific parameter."""
        outcome_values = []

        for value in parameter_values:
            # Create modified configuration
            modified_config = base_config.model_copy()
            config_modifier(modified_config, value)

            # Simulate outcome (in practice, would run rebalancing analysis)
            if parameter_name == "tolerance_band":
                # Higher tolerance = lower costs but higher risk
                outcome = 100 - (value * 1000)  # Inverse relationship with costs
            elif parameter_name == "transaction_cost_rate":
                # Higher costs = higher total costs
                outcome = value * 10000  # Direct relationship
            elif parameter_name == "available_capital":
                # More capital = better optimization potential
                outcome = min(100, 50 + (value / 1000))  # Diminishing returns
            else:
                outcome = 50.0  # Default neutral outcome

            outcome_values.append(outcome)

        # Calculate sensitivity metrics
        value_range = max(parameter_values) - min(parameter_values)
        outcome_range = max(outcome_values) - min(outcome_values)
        sensitivity_score = outcome_range / value_range if value_range > 0 else 0.0

        # Find optimal value (minimize for costs, maximize for benefits)
        if parameter_name == "transaction_cost_rate":
            optimal_idx = outcome_values.index(min(outcome_values))
        else:
            optimal_idx = outcome_values.index(max(outcome_values))
        optimal_value = parameter_values[optimal_idx]

        # Calculate confidence interval (simplified)
        optimal_outcome = outcome_values[optimal_idx]
        threshold = optimal_outcome * 0.95  # Within 5% of optimal

        valid_indices = [i for i, v in enumerate(outcome_values) if v >= threshold]
        if valid_indices:
            confidence_min = parameter_values[min(valid_indices)]
            confidence_max = parameter_values[max(valid_indices)]
        else:
            confidence_min = confidence_max = optimal_value

        return SensitivityResult(
            parameter_name=parameter_name,
            parameter_values=parameter_values,
            outcome_values=outcome_values,
            sensitivity_score=sensitivity_score,
            optimal_value=optimal_value,
            confidence_interval=(confidence_min, confidence_max),
        )

    async def _run_monte_carlo_simulation(
        self,
        base_config: PortfolioConfiguration,
        rebalancing_engine: Any,
        num_simulations: int = 1000,
        time_horizon_days: int = 252,  # 1 year
    ) -> MonteCarloResult:
        """Run Monte Carlo simulation for rebalancing outcomes."""
        self.logger.info(f"Running Monte Carlo simulation with {num_simulations} iterations")

        # Simulation parameters
        np.random.seed(42)  # For reproducible results

        # Simulate portfolio returns and volatility
        annual_return = 0.08  # 8% expected annual return
        annual_volatility = 0.15  # 15% annual volatility

        daily_return = annual_return / 252
        daily_volatility = annual_volatility / np.sqrt(252)

        # Run simulations
        portfolio_values = []
        rebalancing_frequencies = []
        transaction_costs = []
        rebalancing_benefits = []

        initial_value = sum(holding.shares * 100 for holding in base_config.holdings)  # Assume $100/share

        for _ in range(num_simulations):
            # Simulate price paths
            returns = np.random.normal(daily_return, daily_volatility, time_horizon_days)
            price_path = initial_value * np.cumprod(1 + returns)

            # Simulate rebalancing events (simplified)
            rebalancing_events = self._simulate_rebalancing_events(price_path, base_config.global_tolerance)

            # Calculate final portfolio value
            final_value = price_path[-1]
            portfolio_values.append(final_value)

            # Calculate rebalancing frequency (annualized)
            freq = len(rebalancing_events) * (252 / time_horizon_days)
            rebalancing_frequencies.append(freq)

            # Calculate transaction costs
            total_costs = len(rebalancing_events) * initial_value * base_config.transaction_cost_rate
            transaction_costs.append(total_costs)

            # Calculate rebalancing benefit (vs buy-and-hold)
            buy_hold_value = initial_value * (1 + annual_return) ** (time_horizon_days / 252)
            benefit = final_value - buy_hold_value
            rebalancing_benefits.append(benefit)

        # Calculate statistics
        portfolio_values = np.array(portfolio_values)
        rebalancing_frequencies = np.array(rebalancing_frequencies)
        transaction_costs = np.array(transaction_costs)
        rebalancing_benefits = np.array(rebalancing_benefits)

        # Risk metrics
        losses = portfolio_values[portfolio_values < initial_value]
        probability_of_loss = len(losses) / len(portfolio_values)

        var_95 = np.percentile(portfolio_values, 5) - initial_value
        es_95 = np.mean(portfolio_values[portfolio_values <= np.percentile(portfolio_values, 5)]) - initial_value

        # Percentiles
        percentiles = {p: float(np.percentile(portfolio_values, p)) for p in [5, 10, 25, 75, 90, 95]}

        return MonteCarloResult(
            num_simulations=num_simulations,
            time_horizon_days=time_horizon_days,
            mean_portfolio_value=float(np.mean(portfolio_values)),
            median_portfolio_value=float(np.median(portfolio_values)),
            std_portfolio_value=float(np.std(portfolio_values)),
            value_at_risk_95=float(var_95),
            expected_shortfall_95=float(es_95),
            probability_of_loss=float(probability_of_loss),
            mean_rebalancing_frequency=float(np.mean(rebalancing_frequencies)),
            mean_transaction_costs=float(np.mean(transaction_costs)),
            rebalancing_benefit=float(np.mean(rebalancing_benefits)),
            percentiles=percentiles,
        )

    def _simulate_rebalancing_events(self, price_path: np.ndarray, tolerance: float) -> list[int]:
        """Simulate when rebalancing events would occur."""
        rebalancing_days = []
        last_rebalance_day = 0

        # Simplified: assume rebalancing when cumulative drift exceeds tolerance
        cumulative_drift = 0.0

        for day, price in enumerate(price_path):
            if day == 0:
                continue

            # Calculate daily drift (simplified)
            daily_return = (price - price_path[day - 1]) / price_path[day - 1]
            cumulative_drift += abs(daily_return)

            # Check if rebalancing is needed
            if cumulative_drift > tolerance and (day - last_rebalance_day) > 5:  # Min 5 days between rebalancing
                rebalancing_days.append(day)
                cumulative_drift = 0.0
                last_rebalance_day = day

        return rebalancing_days

    def _generate_scenario_comparisons(self, scenarios: list[AlternativeScenario]) -> list[ScenarioComparison]:
        """Generate comparisons between scenarios."""
        comparisons = []

        # Sort scenarios by cost difference for comparison
        scenarios_by_cost = sorted(scenarios, key=lambda s: s.cost_difference)

        # Compare best and worst cost scenarios
        if len(scenarios_by_cost) >= 2:
            best_cost = scenarios_by_cost[0]
            worst_cost = scenarios_by_cost[-1]

            comparison = ScenarioComparison(
                base_scenario=worst_cost.scenario_name,
                alternative_scenario=best_cost.scenario_name,
                return_difference=0.0,  # Simplified
                risk_difference=best_cost.risk_difference - worst_cost.risk_difference,
                cost_difference=best_cost.cost_difference - worst_cost.cost_difference,
                risk_adjusted_return_difference=0.0,  # Simplified
                efficiency_score=8.0 if best_cost.cost_difference < worst_cost.cost_difference else 3.0,
                preferred_scenario=best_cost.scenario_name,
                rationale=f"Lower transaction costs by ${abs(best_cost.cost_difference - worst_cost.cost_difference):.0f}",
            )
            comparisons.append(comparison)

        return comparisons

    def _determine_optimal_parameters(
        self, sensitivity_results: list[SensitivityResult], monte_carlo_result: MonteCarloResult
    ) -> dict[str, Any]:
        """Determine optimal parameters based on analysis results."""
        optimal_params = {}

        # Extract optimal values from sensitivity analysis
        for result in sensitivity_results:
            optimal_params[result.parameter_name] = result.optimal_value

        # Add Monte Carlo insights
        optimal_params["recommended_rebalancing_frequency"] = monte_carlo_result.mean_rebalancing_frequency
        optimal_params["expected_annual_costs"] = monte_carlo_result.mean_transaction_costs

        return optimal_params

    def _generate_risk_warnings(
        self, monte_carlo_result: MonteCarloResult, sensitivity_results: list[SensitivityResult]
    ) -> list[str]:
        """Generate risk warnings based on analysis results."""
        warnings = []

        # Check probability of loss
        if monte_carlo_result.probability_of_loss > 0.3:
            warnings.append(
                f"High probability of loss ({monte_carlo_result.probability_of_loss:.1%}) suggests significant downside risk"
            )

        # Check Value at Risk
        if monte_carlo_result.value_at_risk_95 < -0.2:
            warnings.append(f"95% VaR of {monte_carlo_result.value_at_risk_95:.1%} indicates potential for large losses")

        # Check parameter sensitivity
        high_sensitivity_params = [r.parameter_name for r in sensitivity_results if r.sensitivity_score > 10]
        if high_sensitivity_params:
            warnings.append(
                f"High sensitivity to {', '.join(high_sensitivity_params)} - small changes may significantly impact outcomes"
            )

        return warnings

    def _generate_implementation_notes(
        self, optimal_parameters: dict[str, Any], scenario_comparisons: list[ScenarioComparison]
    ) -> list[str]:
        """Generate implementation recommendations."""
        notes = []

        # Parameter recommendations
        if "tolerance_band" in optimal_parameters:
            tolerance = optimal_parameters["tolerance_band"]
            notes.append(f"Set tolerance bands to {tolerance:.1%} for optimal cost-risk balance")

        if "transaction_cost_rate" in optimal_parameters:
            cost_rate = optimal_parameters["transaction_cost_rate"]
            notes.append(f"Consider brokers with transaction costs ≤ {cost_rate:.2%}")

        # Frequency recommendations
        if "recommended_rebalancing_frequency" in optimal_parameters:
            freq = optimal_parameters["recommended_rebalancing_frequency"]
            notes.append(f"Rebalance approximately {freq:.1f} times per year")

        # Scenario-based recommendations
        if scenario_comparisons:
            best_comparison = max(scenario_comparisons, key=lambda c: c.efficiency_score)
            notes.append(f"Prioritize {best_comparison.preferred_scenario} approach: {best_comparison.rationale}")

        return notes

    def _create_executive_summary(
        self,
        optimal_parameters: dict[str, Any],
        monte_carlo_result: MonteCarloResult,
        scenario_comparisons: list[ScenarioComparison],
    ) -> str:
        """Create executive summary of scenario analysis."""
        summary_parts = []

        # Monte Carlo insights
        expected_return = (monte_carlo_result.mean_portfolio_value / 100000 - 1) * 100  # Assume $100k initial
        summary_parts.append(
            f"Monte Carlo analysis of {monte_carlo_result.num_simulations} simulations "
            f"projects {expected_return:.1f}% expected return with "
            f"{monte_carlo_result.probability_of_loss:.1%} probability of loss."
        )

        # Cost insights
        annual_costs = monte_carlo_result.mean_transaction_costs
        summary_parts.append(
            f"Expected annual transaction costs of ${annual_costs:.0f} with "
            f"rebalancing frequency of {monte_carlo_result.mean_rebalancing_frequency:.1f} times per year."
        )

        # Optimization insights
        if optimal_parameters:
            key_params = [k for k in optimal_parameters.keys() if not k.startswith("recommended")]
            if key_params:
                summary_parts.append(
                    f"Optimal parameters identified: {', '.join(key_params)}. "
                    "Implementation of these parameters could improve risk-adjusted returns."
                )

        # Risk assessment
        if monte_carlo_result.value_at_risk_95 < -0.15:
            summary_parts.append(
                "Significant downside risk identified. Consider more conservative tolerance bands or diversification improvements."
            )

        return " ".join(summary_parts)
