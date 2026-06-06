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
    PortfolioConfiguration,
    RebalancingMethod,
)

logger = logging.getLogger(__name__)


class ScenarioParameters(BaseModel):
    """Parameters for scenario analysis."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    # Capital scenarios
    capital_amounts: list[float] = Field(default_factory=lambda: [-10000.0, -5000.0, 0.0, 5000.0, 10000.0, 25000.0], description="Different capital amounts to test")

    # Tolerance scenarios
    tolerance_levels: list[float] = Field(default_factory=lambda: [0.01, 0.025, 0.05, 0.075, 0.10], description="Different tolerance band levels to test")

    # Transaction cost scenarios
    transaction_cost_rates: list[float] = Field(default_factory=lambda: [0.0005, 0.001, 0.002, 0.005], description="Different transaction cost rates to test")

    # Rebalancing method scenarios
    rebalancing_methods: list[RebalancingMethod] = Field(
        default_factory=lambda: [
            RebalancingMethod.MINIMIZE_TRADES,
            RebalancingMethod.MINIMIZE_COSTS,
            RebalancingMethod.RISK_AWARE,
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
    rebalancing_frequency_percentiles: dict[str, float] = Field(default_factory=dict, description="Percentiles of rebalancing frequency")
    transaction_cost_percentiles: dict[str, float] = Field(default_factory=dict, description="Percentiles of transaction costs")
    final_value_percentiles: dict[str, float] = Field(default_factory=dict, description="Percentiles of final portfolio value")

    # Risk metrics
    probability_of_loss: float = Field(..., ge=0.0, le=1.0, description="Probability of portfolio loss (0-1)")
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

        # Calculate statistics - convert to numpy arrays with new variable names
        rebalancing_freq_arr = np.array(rebalancing_frequencies)
        transaction_cost_arr = np.array(transaction_costs)
        final_val_arr = np.array(final_values)

        # Calculate percentiles
        rebalancing_percentiles = {
            "5th": float(np.percentile(rebalancing_freq_arr, 5)),
            "25th": float(np.percentile(rebalancing_freq_arr, 25)),
            "50th": float(np.percentile(rebalancing_freq_arr, 50)),
            "75th": float(np.percentile(rebalancing_freq_arr, 75)),
            "95th": float(np.percentile(rebalancing_freq_arr, 95)),
        }

        cost_percentiles = {
            "5th": float(np.percentile(transaction_cost_arr, 5)),
            "25th": float(np.percentile(transaction_cost_arr, 25)),
            "50th": float(np.percentile(transaction_cost_arr, 50)),
            "75th": float(np.percentile(transaction_cost_arr, 75)),
            "95th": float(np.percentile(transaction_cost_arr, 95)),
        }

        value_percentiles = {
            "5th": float(np.percentile(final_val_arr, 5)),
            "25th": float(np.percentile(final_val_arr, 25)),
            "50th": float(np.percentile(final_val_arr, 50)),
            "75th": float(np.percentile(final_val_arr, 75)),
            "95th": float(np.percentile(final_val_arr, 95)),
        }

        # Calculate risk metrics
        initial_value = 10000  # Simplified initial value
        returns = (final_val_arr - initial_value) / initial_value
        probability_of_loss = float(np.mean(returns < 0))
        value_at_risk_95 = float(np.percentile(returns, 5))
        expected_shortfall_95 = float(np.mean(returns[returns <= value_at_risk_95]))

        result = MonteCarloResult(
            num_simulations=parameters.num_simulations,
            time_horizon_days=parameters.time_horizon_days,
            annual_volatility=parameters.annual_volatility,
            annual_return=parameters.annual_return,
            mean_rebalancing_frequency=float(np.mean(rebalancing_freq_arr)),
            std_rebalancing_frequency=float(np.std(rebalancing_freq_arr)),
            mean_transaction_costs=float(np.mean(transaction_cost_arr)),
            std_transaction_costs=float(np.std(transaction_cost_arr)),
            mean_final_value=float(np.mean(final_val_arr)),
            std_final_value=float(np.std(final_val_arr)),
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
