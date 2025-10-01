"""
Scenario Generators for Portfolio Analysis.

This module provides scenario generation functionality including
Monte Carlo simulations, parameter variations, and scenario creation
for portfolio rebalancing analysis.
"""

from __future__ import annotations

import logging

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
            RebalancingMethod.THRESHOLD_BASED,
            RebalancingMethod.CALENDAR_BASED,
            RebalancingMethod.VOLATILITY_BASED,
        ],
        description="Different rebalancing methods to test",
    )

    # Monte Carlo parameters
    num_simulations: int = Field(default=1000, description="Number of Monte Carlo simulations")
    time_horizon_days: int = Field(default=252, description="Time horizon for simulations in days")
    annual_volatility: float = Field(default=0.15, description="Annual volatility for simulations")
    annual_return: float = Field(default=0.08, description="Expected annual return for simulations")


class MonteCarloResult(BaseModel):
    """Result of Monte Carlo simulation."""

    model_config = ConfigDict(extra="forbid")

    # Simulation parameters
    num_simulations: int = Field(..., description="Number of simulations run")
    time_horizon_days: int = Field(..., description="Time horizon in days")
    annual_volatility: float = Field(..., description="Annual volatility used")
    annual_return: float = Field(..., description="Expected annual return used")

    # Results
    mean_rebalancing_frequency: float = Field(..., description="Average number of rebalancing events")
    std_rebalancing_frequency: float = Field(..., description="Standard deviation of rebalancing frequency")
    mean_transaction_costs: float = Field(..., description="Average transaction costs")
    std_transaction_costs: float = Field(..., description="Standard deviation of transaction costs")
    mean_final_value: float = Field(..., description="Average final portfolio value")
    std_final_value: float = Field(..., description="Standard deviation of final portfolio value")

    # Percentiles
    rebalancing_frequency_percentiles: dict[str, float] = Field(
        default_factory=dict, description="Percentiles of rebalancing frequency"
    )
    transaction_cost_percentiles: dict[str, float] = Field(default_factory=dict, description="Percentiles of transaction costs")
    final_value_percentiles: dict[str, float] = Field(default_factory=dict, description="Percentiles of final portfolio value")

    # Risk metrics
    probability_of_loss: float = Field(..., description="Probability of portfolio loss")
    value_at_risk_95: float = Field(..., description="95% Value at Risk")
    expected_shortfall_95: float = Field(..., description="95% Expected Shortfall")


class ScenarioGenerator:
    """
    Generator for portfolio analysis scenarios.

    This class provides methods to generate various scenarios for portfolio
    analysis including what-if scenarios, parameter variations, and Monte Carlo
    simulations.
    """

    def __init__(self) -> None:
        """Initialize the scenario generator."""
        self.logger = logging.getLogger(__name__)

    async def generate_what_if_scenarios(
        self,
        base_config: PortfolioConfiguration,
        parameters: ScenarioParameters,
    ) -> list[AlternativeScenario]:
        """
        Generate what-if scenarios based on parameter variations.

        Args:
            base_config: Base portfolio configuration
            parameters: Scenario parameters to vary

        Returns:
            List of alternative scenarios to analyze

        """
        scenarios = []

        # Capital amount scenarios
        for capital in parameters.capital_amounts:
            if capital != 0:  # Skip the base case (0 additional capital)
                scenario_config = base_config.model_copy(deep=True)
                scenario_config.additional_capital = capital

                scenarios.append(
                    AlternativeScenario(
                        name=f"Additional Capital: ${capital:,.0f}",
                        description=f"Portfolio with ${capital:,.0f} additional capital",
                        configuration=scenario_config,
                        expected_return=0.0,  # Will be calculated during analysis
                        expected_risk=0.0,  # Will be calculated during analysis
                        cost_difference=0.0,  # Will be calculated during analysis
                        risk_difference=0.0,  # Will be calculated during analysis
                    )
                )

        # Tolerance level scenarios
        for tolerance in parameters.tolerance_levels:
            if abs(tolerance - base_config.tolerance_band) > 0.001:  # Skip if same as base
                scenario_config = base_config.model_copy(deep=True)
                scenario_config.tolerance_band = tolerance

                scenarios.append(
                    AlternativeScenario(
                        name=f"Tolerance Band: {tolerance:.1%}",
                        description=f"Portfolio with {tolerance:.1%} tolerance band",
                        configuration=scenario_config,
                        expected_return=0.0,
                        expected_risk=0.0,
                        cost_difference=0.0,
                        risk_difference=0.0,
                    )
                )

        # Transaction cost scenarios
        for cost_rate in parameters.transaction_cost_rates:
            if abs(cost_rate - base_config.transaction_cost_rate) > 0.0001:  # Skip if same as base
                scenario_config = base_config.model_copy(deep=True)
                scenario_config.transaction_cost_rate = cost_rate

                scenarios.append(
                    AlternativeScenario(
                        name=f"Transaction Cost: {cost_rate:.2%}",
                        description=f"Portfolio with {cost_rate:.2%} transaction cost rate",
                        configuration=scenario_config,
                        expected_return=0.0,
                        expected_risk=0.0,
                        cost_difference=0.0,
                        risk_difference=0.0,
                    )
                )

        # Rebalancing method scenarios
        for method in parameters.rebalancing_methods:
            if method != base_config.rebalancing_method:  # Skip if same as base
                scenario_config = base_config.model_copy(deep=True)
                scenario_config.rebalancing_method = method

                scenarios.append(
                    AlternativeScenario(
                        name=f"Method: {method.value}",
                        description=f"Portfolio using {method.value} rebalancing method",
                        configuration=scenario_config,
                        expected_return=0.0,
                        expected_risk=0.0,
                        cost_difference=0.0,
                        risk_difference=0.0,
                    )
                )

        self.logger.info(f"Generated {len(scenarios)} what-if scenarios")
        return scenarios

    async def run_monte_carlo_simulation(
        self,
        base_config: PortfolioConfiguration,
        parameters: ScenarioParameters,
    ) -> MonteCarloResult:
        """
        Run Monte Carlo simulation for portfolio analysis.

        Args:
            base_config: Base portfolio configuration
            parameters: Simulation parameters

        Returns:
            MonteCarloResult with simulation statistics

        """
        self.logger.info(f"Starting Monte Carlo simulation with {parameters.num_simulations} iterations")

        # Initialize result arrays
        rebalancing_frequencies = []
        transaction_costs = []
        final_values = []

        # Run simulations
        for i in range(parameters.num_simulations):
            if i % 100 == 0:
                self.logger.debug(f"Running simulation {i + 1}/{parameters.num_simulations}")

            # Generate price path
            price_path = self._generate_price_path(
                parameters.time_horizon_days,
                parameters.annual_return,
                parameters.annual_volatility,
            )

            # Simulate rebalancing events
            rebalancing_days = self._simulate_rebalancing_events(price_path, base_config.tolerance_band)

            # Calculate metrics for this simulation
            num_rebalances = len(rebalancing_days)
            total_cost = num_rebalances * base_config.transaction_cost_rate * 10000  # Simplified cost calculation
            final_value = price_path[-1] * 10000  # Simplified final value calculation

            rebalancing_frequencies.append(num_rebalances)
            transaction_costs.append(total_cost)
            final_values.append(final_value)

        # Calculate statistics
        rebalancing_frequencies = np.array(rebalancing_frequencies)
        transaction_costs = np.array(transaction_costs)
        final_values = np.array(final_values)

        # Calculate percentiles
        rebalancing_percentiles = {
            "5th": float(np.percentile(rebalancing_frequencies, 5)),
            "25th": float(np.percentile(rebalancing_frequencies, 25)),
            "50th": float(np.percentile(rebalancing_frequencies, 50)),
            "75th": float(np.percentile(rebalancing_frequencies, 75)),
            "95th": float(np.percentile(rebalancing_frequencies, 95)),
        }

        cost_percentiles = {
            "5th": float(np.percentile(transaction_costs, 5)),
            "25th": float(np.percentile(transaction_costs, 25)),
            "50th": float(np.percentile(transaction_costs, 50)),
            "75th": float(np.percentile(transaction_costs, 75)),
            "95th": float(np.percentile(transaction_costs, 95)),
        }

        value_percentiles = {
            "5th": float(np.percentile(final_values, 5)),
            "25th": float(np.percentile(final_values, 25)),
            "50th": float(np.percentile(final_values, 50)),
            "75th": float(np.percentile(final_values, 75)),
            "95th": float(np.percentile(final_values, 95)),
        }

        # Calculate risk metrics
        initial_value = 10000  # Simplified initial value
        returns = (final_values - initial_value) / initial_value
        probability_of_loss = float(np.mean(returns < 0))
        value_at_risk_95 = float(np.percentile(returns, 5))
        expected_shortfall_95 = float(np.mean(returns[returns <= value_at_risk_95]))

        result = MonteCarloResult(
            num_simulations=parameters.num_simulations,
            time_horizon_days=parameters.time_horizon_days,
            annual_volatility=parameters.annual_volatility,
            annual_return=parameters.annual_return,
            mean_rebalancing_frequency=float(np.mean(rebalancing_frequencies)),
            std_rebalancing_frequency=float(np.std(rebalancing_frequencies)),
            mean_transaction_costs=float(np.mean(transaction_costs)),
            std_transaction_costs=float(np.std(transaction_costs)),
            mean_final_value=float(np.mean(final_values)),
            std_final_value=float(np.std(final_values)),
            rebalancing_frequency_percentiles=rebalancing_percentiles,
            transaction_cost_percentiles=cost_percentiles,
            final_value_percentiles=value_percentiles,
            probability_of_loss=probability_of_loss,
            value_at_risk_95=value_at_risk_95,
            expected_shortfall_95=expected_shortfall_95,
        )

        self.logger.info("Monte Carlo simulation completed")
        return result

    def _generate_price_path(self, days: int, annual_return: float, annual_volatility: float) -> np.ndarray:
        """
        Generate a geometric Brownian motion price path.

        Args:
            days: Number of days to simulate
            annual_return: Expected annual return
            annual_volatility: Annual volatility

        Returns:
            Array of price values

        """
        dt = 1 / 252  # Daily time step
        drift = annual_return - 0.5 * annual_volatility**2

        # Generate random shocks
        shocks = np.random.normal(0, 1, days)

        # Calculate log returns
        log_returns = drift * dt + annual_volatility * np.sqrt(dt) * shocks

        # Convert to price path (starting at 1.0)
        price_path = np.exp(np.cumsum(log_returns))
        price_path = np.insert(price_path, 0, 1.0)  # Add initial price

        return price_path

    def _simulate_rebalancing_events(self, price_path: np.ndarray, tolerance: float) -> list[int]:
        """
        Simulate when rebalancing events would occur.

        Args:
            price_path: Array of price values
            tolerance: Tolerance band for rebalancing

        Returns:
            List of days when rebalancing would occur

        """
        rebalancing_days = []

        # Simplified rebalancing logic - rebalance when price deviates by tolerance
        initial_price = price_path[0]

        for day, price in enumerate(price_path[1:], 1):
            deviation = abs(price - initial_price) / initial_price

            if deviation > tolerance:
                rebalancing_days.append(day)
                initial_price = price  # Reset reference after rebalancing

        return rebalancing_days
