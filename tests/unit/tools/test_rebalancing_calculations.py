"""Tests for tools/rebalancing_calculations.py module."""

import pytest

from finwiz.tools.rebalancing_calculations import RebalancingCalculations


class TestCalculateRiskImprovement:
    """Tests for calculate_risk_improvement method."""

    def test_should_calculate_positive_improvement(self):
        """Test risk improvement when risk decreases."""
        result = RebalancingCalculations.calculate_risk_improvement(current_risk=0.8, projected_risk=0.5)
        assert result == pytest.approx(0.3)

    def test_should_calculate_negative_improvement(self):
        """Test risk improvement when risk increases."""
        result = RebalancingCalculations.calculate_risk_improvement(current_risk=0.5, projected_risk=0.8)
        assert result == pytest.approx(-0.3)

    def test_should_return_zero_for_no_change(self):
        """Test risk improvement when no change."""
        result = RebalancingCalculations.calculate_risk_improvement(current_risk=0.5, projected_risk=0.5)
        assert result == pytest.approx(0.0)

    def test_should_handle_zero_values(self):
        """Test with zero risk values."""
        result = RebalancingCalculations.calculate_risk_improvement(current_risk=0.0, projected_risk=0.0)
        assert result == pytest.approx(0.0)


class TestCalculateDeviationSeverity:
    """Tests for calculate_deviation_severity method."""

    def test_should_return_high_for_large_deviation(self):
        """Test high severity for deviation > 5%."""
        assert RebalancingCalculations.calculate_deviation_severity(0.06) == "high"
        assert RebalancingCalculations.calculate_deviation_severity(0.10) == "high"
        assert RebalancingCalculations.calculate_deviation_severity(0.5) == "high"

    def test_should_return_medium_for_moderate_deviation(self):
        """Test medium severity for deviation between 2% and 5%."""
        assert RebalancingCalculations.calculate_deviation_severity(0.03) == "medium"
        assert RebalancingCalculations.calculate_deviation_severity(0.04) == "medium"
        assert RebalancingCalculations.calculate_deviation_severity(0.05) == "medium"

    def test_should_return_low_for_small_deviation(self):
        """Test low severity for deviation <= 2%."""
        assert RebalancingCalculations.calculate_deviation_severity(0.01) == "low"
        assert RebalancingCalculations.calculate_deviation_severity(0.02) == "low"
        assert RebalancingCalculations.calculate_deviation_severity(0.0) == "low"

    def test_should_handle_negative_deviations(self):
        """Test that negative deviations are handled by absolute value."""
        assert RebalancingCalculations.calculate_deviation_severity(-0.06) == "high"
        assert RebalancingCalculations.calculate_deviation_severity(-0.03) == "medium"
        assert RebalancingCalculations.calculate_deviation_severity(-0.01) == "low"

    def test_should_handle_boundary_values(self):
        """Test boundary values between severity levels."""
        # Just above 5% - high
        assert RebalancingCalculations.calculate_deviation_severity(0.0501) == "high"
        # Just above 2% - medium
        assert RebalancingCalculations.calculate_deviation_severity(0.0201) == "medium"


class TestCalculateTotalTransactionCosts:
    """Tests for calculate_total_transaction_costs method."""

    def test_should_sum_all_costs(self):
        """Test that all costs are summed correctly."""
        result = RebalancingCalculations.calculate_total_transaction_costs(
            commission_costs=100.0,
            spread_costs=50.0,
            market_impact_costs=25.0,
        )
        assert result == pytest.approx(175.0)

    def test_should_handle_zero_costs(self):
        """Test with all zero costs."""
        result = RebalancingCalculations.calculate_total_transaction_costs(
            commission_costs=0.0,
            spread_costs=0.0,
            market_impact_costs=0.0,
        )
        assert result == pytest.approx(0.0)

    def test_should_handle_partial_zero_costs(self):
        """Test with some zero costs."""
        result = RebalancingCalculations.calculate_total_transaction_costs(
            commission_costs=100.0,
            spread_costs=0.0,
            market_impact_costs=0.0,
        )
        assert result == pytest.approx(100.0)

    def test_should_handle_large_costs(self):
        """Test with large cost values."""
        result = RebalancingCalculations.calculate_total_transaction_costs(
            commission_costs=10000.0,
            spread_costs=5000.0,
            market_impact_costs=2500.0,
        )
        assert result == pytest.approx(17500.0)


class TestCalculateCostPercentage:
    """Tests for calculate_cost_percentage method."""

    def test_should_calculate_correct_percentage(self):
        """Test basic percentage calculation."""
        result = RebalancingCalculations.calculate_cost_percentage(
            total_costs=100.0,
            portfolio_value=10000.0,
        )
        assert result == pytest.approx(1.0)  # 100/10000 * 100 = 1%

    def test_should_return_zero_for_zero_portfolio(self):
        """Test that zero portfolio value returns zero."""
        result = RebalancingCalculations.calculate_cost_percentage(
            total_costs=100.0,
            portfolio_value=0.0,
        )
        assert result == pytest.approx(0.0)

    def test_should_return_zero_for_negative_portfolio(self):
        """Test that negative portfolio value returns zero."""
        result = RebalancingCalculations.calculate_cost_percentage(
            total_costs=100.0,
            portfolio_value=-1000.0,
        )
        assert result == pytest.approx(0.0)

    def test_should_handle_zero_costs(self):
        """Test with zero costs."""
        result = RebalancingCalculations.calculate_cost_percentage(
            total_costs=0.0,
            portfolio_value=10000.0,
        )
        assert result == pytest.approx(0.0)

    def test_should_handle_small_percentage(self):
        """Test small cost percentage."""
        result = RebalancingCalculations.calculate_cost_percentage(
            total_costs=10.0,
            portfolio_value=100000.0,
        )
        assert result == pytest.approx(0.01)  # 10/100000 * 100 = 0.01%


class TestCalculateBreakEvenDays:
    """Tests for calculate_break_even_days method."""

    def test_should_calculate_break_even_days(self):
        """Test basic break-even calculation."""
        result = RebalancingCalculations.calculate_break_even_days(
            total_costs=100.0,
            expected_daily_return_improvement=1.0,  # 1%
            portfolio_value=10000.0,
        )
        assert result == 1  # 100 / (0.01 * 10000) = 1 day

    def test_should_return_none_for_zero_improvement(self):
        """Test that zero improvement returns None."""
        result = RebalancingCalculations.calculate_break_even_days(
            total_costs=100.0,
            expected_daily_return_improvement=0.0,
            portfolio_value=10000.0,
        )
        assert result is None

    def test_should_return_none_for_negative_improvement(self):
        """Test that negative improvement returns None."""
        result = RebalancingCalculations.calculate_break_even_days(
            total_costs=100.0,
            expected_daily_return_improvement=-0.5,
            portfolio_value=10000.0,
        )
        assert result is None

    def test_should_return_none_for_zero_portfolio(self):
        """Test that zero portfolio value returns None."""
        result = RebalancingCalculations.calculate_break_even_days(
            total_costs=100.0,
            expected_daily_return_improvement=1.0,
            portfolio_value=0.0,
        )
        assert result is None

    def test_should_return_none_for_negative_portfolio(self):
        """Test that negative portfolio value returns None."""
        result = RebalancingCalculations.calculate_break_even_days(
            total_costs=100.0,
            expected_daily_return_improvement=1.0,
            portfolio_value=-10000.0,
        )
        assert result is None

    def test_should_return_integer_value(self):
        """Test that result is always an integer."""
        result = RebalancingCalculations.calculate_break_even_days(
            total_costs=150.0,
            expected_daily_return_improvement=1.0,  # 1%
            portfolio_value=10000.0,
        )
        assert isinstance(result, int)
        assert result == 1  # 150 / (0.01 * 10000) = 1.5 -> 1

    def test_should_handle_large_break_even_period(self):
        """Test with long break-even period."""
        result = RebalancingCalculations.calculate_break_even_days(
            total_costs=1000.0,
            expected_daily_return_improvement=0.01,  # 0.01%
            portfolio_value=10000.0,
        )
        assert result == 1000  # 1000 / (0.0001 * 10000) = 1000 days


class TestCalculateUrgencyScore:
    """Tests for calculate_urgency_score method."""

    def test_should_calculate_basic_urgency(self):
        """Test basic urgency score calculation."""
        result = RebalancingCalculations.calculate_urgency_score(
            deviation=0.5,  # 50%
            volatility=0.0,
            market_conditions="normal",
        )
        assert result == pytest.approx(5.0)  # 0.5 * 10 * 1.0 * 1.0 = 5.0

    def test_should_adjust_for_volatility(self):
        """Test that volatility increases urgency score."""
        result = RebalancingCalculations.calculate_urgency_score(
            deviation=0.5,
            volatility=50.0,  # 50% volatility
            market_conditions="normal",
        )
        assert result == pytest.approx(7.5)  # 0.5 * 10 * 1.5 * 1.0 = 7.5

    def test_should_adjust_for_volatile_market(self):
        """Test that volatile market increases urgency score."""
        result = RebalancingCalculations.calculate_urgency_score(
            deviation=0.5,
            volatility=0.0,
            market_conditions="volatile",
        )
        assert result == pytest.approx(7.5)  # 0.5 * 10 * 1.0 * 1.5 = 7.5

    def test_should_adjust_for_bearish_market(self):
        """Test that bearish market increases urgency score."""
        result = RebalancingCalculations.calculate_urgency_score(
            deviation=0.5,
            volatility=0.0,
            market_conditions="bearish",
        )
        assert result == pytest.approx(6.5)  # 0.5 * 10 * 1.0 * 1.3 = 6.5

    def test_should_adjust_for_bullish_market(self):
        """Test that bullish market decreases urgency score."""
        result = RebalancingCalculations.calculate_urgency_score(
            deviation=0.5,
            volatility=0.0,
            market_conditions="bullish",
        )
        assert result == pytest.approx(4.0)  # 0.5 * 10 * 1.0 * 0.8 = 4.0

    def test_should_adjust_for_stable_market(self):
        """Test that stable market decreases urgency score."""
        result = RebalancingCalculations.calculate_urgency_score(
            deviation=0.5,
            volatility=0.0,
            market_conditions="stable",
        )
        assert result == pytest.approx(3.5)  # 0.5 * 10 * 1.0 * 0.7 = 3.5

    def test_should_cap_at_10(self):
        """Test that score is capped at 10."""
        result = RebalancingCalculations.calculate_urgency_score(
            deviation=2.0,  # 200% deviation - very extreme
            volatility=100.0,
            market_conditions="volatile",
        )
        assert result == pytest.approx(10.0)

    def test_should_handle_unknown_market_condition(self):
        """Test that unknown market condition defaults to normal."""
        result = RebalancingCalculations.calculate_urgency_score(
            deviation=0.5,
            volatility=0.0,
            market_conditions="unknown",
        )
        assert result == pytest.approx(5.0)  # Uses default multiplier of 1.0

    def test_should_handle_case_insensitive_market_condition(self):
        """Test that market condition matching is case insensitive."""
        result = RebalancingCalculations.calculate_urgency_score(
            deviation=0.5,
            volatility=0.0,
            market_conditions="VOLATILE",
        )
        assert result == pytest.approx(7.5)


class TestDetermineActionPriority:
    """Tests for determine_action_priority method."""

    def test_should_return_urgent_for_high_score(self):
        """Test urgent priority for score >= 8."""
        assert RebalancingCalculations.determine_action_priority(8.0) == "urgent"
        assert RebalancingCalculations.determine_action_priority(9.0) == "urgent"
        assert RebalancingCalculations.determine_action_priority(10.0) == "urgent"

    def test_should_return_high_for_moderate_high_score(self):
        """Test high priority for score between 6 and 8."""
        assert RebalancingCalculations.determine_action_priority(6.0) == "high"
        assert RebalancingCalculations.determine_action_priority(7.0) == "high"
        assert RebalancingCalculations.determine_action_priority(7.9) == "high"

    def test_should_return_medium_for_moderate_score(self):
        """Test medium priority for score between 3 and 6."""
        assert RebalancingCalculations.determine_action_priority(3.0) == "medium"
        assert RebalancingCalculations.determine_action_priority(4.5) == "medium"
        assert RebalancingCalculations.determine_action_priority(5.9) == "medium"

    def test_should_return_low_for_low_score(self):
        """Test low priority for score < 3."""
        assert RebalancingCalculations.determine_action_priority(0.0) == "low"
        assert RebalancingCalculations.determine_action_priority(1.5) == "low"
        assert RebalancingCalculations.determine_action_priority(2.9) == "low"

    def test_should_handle_boundary_values(self):
        """Test boundary values between priorities."""
        assert RebalancingCalculations.determine_action_priority(7.99) == "high"
        assert RebalancingCalculations.determine_action_priority(8.0) == "urgent"
        assert RebalancingCalculations.determine_action_priority(5.99) == "medium"
        assert RebalancingCalculations.determine_action_priority(6.0) == "high"
        assert RebalancingCalculations.determine_action_priority(2.99) == "low"
        assert RebalancingCalculations.determine_action_priority(3.0) == "medium"


class TestCalculateScenarioImpact:
    """Tests for calculate_scenario_impact method."""

    def test_should_return_base_values_with_empty_params(self):
        """Test that empty parameters return base values."""
        result = RebalancingCalculations.calculate_scenario_impact(
            base_costs=1000.0,
            base_risk=0.5,
            scenario_parameters={},
        )
        assert result["cost_difference"] == pytest.approx(0.0)
        assert result["risk_difference"] == pytest.approx(0.0)
        assert result["cost_multiplier"] == pytest.approx(1.0)
        assert result["risk_multiplier"] == pytest.approx(1.0)

    def test_should_adjust_for_tolerance(self):
        """Test adjustment based on tolerance parameter."""
        result = RebalancingCalculations.calculate_scenario_impact(
            base_costs=1000.0,
            base_risk=0.5,
            scenario_parameters={"tolerance": 0.5},  # 50% tolerance
        )
        # cost_multiplier = 1 - 0.5 * 0.5 = 0.75
        # risk_multiplier = 1 + 0.5 * 0.2 = 1.1
        assert result["cost_multiplier"] == pytest.approx(0.75)
        assert result["risk_multiplier"] == pytest.approx(1.1)
        assert result["cost_difference"] == pytest.approx(-250.0)  # 1000 * 0.75 - 1000
        assert result["risk_difference"] == pytest.approx(0.05)  # 0.5 * 1.1 - 0.5

    def test_should_adjust_for_transaction_cost_rate(self):
        """Test adjustment based on transaction_cost_rate parameter."""
        result = RebalancingCalculations.calculate_scenario_impact(
            base_costs=1000.0,
            base_risk=0.5,
            scenario_parameters={"transaction_cost_rate": 0.5},  # +50%
        )
        assert result["cost_multiplier"] == pytest.approx(1.5)
        assert result["cost_difference"] == pytest.approx(500.0)

    def test_should_adjust_for_threshold_rebalancing(self):
        """Test adjustment for threshold rebalancing method."""
        result = RebalancingCalculations.calculate_scenario_impact(
            base_costs=1000.0,
            base_risk=0.5,
            scenario_parameters={"rebalancing_method": "threshold"},
        )
        assert result["cost_multiplier"] == pytest.approx(0.8)
        assert result["risk_multiplier"] == pytest.approx(1.1)

    def test_should_adjust_for_calendar_rebalancing(self):
        """Test adjustment for calendar rebalancing method."""
        result = RebalancingCalculations.calculate_scenario_impact(
            base_costs=1000.0,
            base_risk=0.5,
            scenario_parameters={"rebalancing_method": "calendar"},
        )
        assert result["cost_multiplier"] == pytest.approx(1.2)
        assert result["risk_multiplier"] == pytest.approx(0.9)

    def test_should_combine_multiple_parameters(self):
        """Test combination of multiple parameters."""
        result = RebalancingCalculations.calculate_scenario_impact(
            base_costs=1000.0,
            base_risk=0.5,
            scenario_parameters={
                "tolerance": 0.2,
                "transaction_cost_rate": 0.1,
                "rebalancing_method": "threshold",
            },
        )
        # cost_multiplier = (1 - 0.2 * 0.5) * (1 + 0.1) * 0.8 = 0.9 * 1.1 * 0.8 = 0.792
        # risk_multiplier = (1 + 0.2 * 0.2) * 1.1 = 1.04 * 1.1 = 1.144
        assert result["cost_multiplier"] == pytest.approx(0.792)
        assert result["risk_multiplier"] == pytest.approx(1.144)


class TestCalculatePortfolioMetrics:
    """Tests for calculate_portfolio_metrics method."""

    def test_should_calculate_total_value(self):
        """Test total value calculation."""
        result = RebalancingCalculations.calculate_portfolio_metrics(
            weightings={"AAPL": 0.3, "GOOGL": 0.3, "MSFT": 0.4},
            values={"AAPL": 3000.0, "GOOGL": 3000.0, "MSFT": 4000.0},
            target_weights={"AAPL": 0.33, "GOOGL": 0.33, "MSFT": 0.34},
        )
        assert result["total_value"] == pytest.approx(10000.0)

    def test_should_calculate_deviations(self):
        """Test deviation calculation for each asset."""
        result = RebalancingCalculations.calculate_portfolio_metrics(
            weightings={"AAPL": 0.5, "GOOGL": 0.5},
            values={"AAPL": 5000.0, "GOOGL": 5000.0},
            target_weights={"AAPL": 0.6, "GOOGL": 0.4},
        )
        assert result["deviations"]["AAPL"] == pytest.approx(-0.1)
        assert result["deviations"]["GOOGL"] == pytest.approx(0.1)

    def test_should_calculate_max_deviation(self):
        """Test max deviation calculation."""
        result = RebalancingCalculations.calculate_portfolio_metrics(
            weightings={"AAPL": 0.3, "GOOGL": 0.7},
            values={"AAPL": 3000.0, "GOOGL": 7000.0},
            target_weights={"AAPL": 0.5, "GOOGL": 0.5},
        )
        assert result["max_deviation"] == pytest.approx(0.2)

    def test_should_calculate_average_deviation(self):
        """Test average deviation calculation."""
        result = RebalancingCalculations.calculate_portfolio_metrics(
            weightings={"AAPL": 0.3, "GOOGL": 0.7},
            values={"AAPL": 3000.0, "GOOGL": 7000.0},
            target_weights={"AAPL": 0.5, "GOOGL": 0.5},
        )
        # Deviations: -0.2 and 0.2, avg of abs = 0.2
        assert result["avg_deviation"] == pytest.approx(0.2)

    def test_should_count_positions_outside_tolerance(self):
        """Test counting positions outside tolerance."""
        result = RebalancingCalculations.calculate_portfolio_metrics(
            weightings={"AAPL": 0.3, "GOOGL": 0.35, "MSFT": 0.35},
            values={"AAPL": 3000.0, "GOOGL": 3500.0, "MSFT": 3500.0},
            target_weights={"AAPL": 0.33, "GOOGL": 0.33, "MSFT": 0.34},
        )
        # AAPL: -0.03, GOOGL: 0.02, MSFT: 0.01
        # Only AAPL is outside 2% tolerance
        assert result["positions_outside_tolerance"] == 1

    def test_should_calculate_concentration_index(self):
        """Test Herfindahl concentration index calculation."""
        # Equal weights = low concentration
        result_equal = RebalancingCalculations.calculate_portfolio_metrics(
            weightings={"A": 0.25, "B": 0.25, "C": 0.25, "D": 0.25},
            values={"A": 2500.0, "B": 2500.0, "C": 2500.0, "D": 2500.0},
            target_weights={"A": 0.25, "B": 0.25, "C": 0.25, "D": 0.25},
        )
        # 4 * 0.25^2 = 4 * 0.0625 = 0.25
        assert result_equal["concentration_index"] == pytest.approx(0.25)

        # Concentrated weights
        result_concentrated = RebalancingCalculations.calculate_portfolio_metrics(
            weightings={"A": 0.9, "B": 0.1},
            values={"A": 9000.0, "B": 1000.0},
            target_weights={"A": 0.5, "B": 0.5},
        )
        # 0.9^2 + 0.1^2 = 0.81 + 0.01 = 0.82
        assert result_concentrated["concentration_index"] == pytest.approx(0.82)

    def test_should_count_positions(self):
        """Test position count."""
        result = RebalancingCalculations.calculate_portfolio_metrics(
            weightings={"A": 0.2, "B": 0.3, "C": 0.5},
            values={"A": 2000.0, "B": 3000.0, "C": 5000.0},
            target_weights={"A": 0.33, "B": 0.33, "C": 0.34},
        )
        assert result["number_of_positions"] == 3

    def test_should_handle_empty_portfolio(self):
        """Test with empty portfolio."""
        result = RebalancingCalculations.calculate_portfolio_metrics(
            weightings={},
            values={},
            target_weights={},
        )
        assert result["total_value"] == pytest.approx(0.0)
        assert result["max_deviation"] == pytest.approx(0.0)
        assert result["avg_deviation"] == pytest.approx(0.0)
        assert result["positions_outside_tolerance"] == 0
        assert result["concentration_index"] == pytest.approx(0.0)
        assert result["number_of_positions"] == 0

    def test_should_handle_missing_target_weights(self):
        """Test when target weights are missing for some assets."""
        result = RebalancingCalculations.calculate_portfolio_metrics(
            weightings={"AAPL": 0.5, "GOOGL": 0.5},
            values={"AAPL": 5000.0, "GOOGL": 5000.0},
            target_weights={"AAPL": 0.5},  # Missing GOOGL
        )
        # GOOGL deviation = 0.5 - 0.0 = 0.5
        assert result["deviations"]["GOOGL"] == pytest.approx(0.5)


class TestEdgeCases:
    """Edge case tests for RebalancingCalculations."""

    def test_should_handle_float_precision(self):
        """Test handling of floating point precision."""
        result = RebalancingCalculations.calculate_cost_percentage(
            total_costs=1.0,
            portfolio_value=3.0,
        )
        # 1/3 * 100 = 33.333...
        assert result == pytest.approx(33.333333, rel=1e-5)

    def test_should_handle_very_small_values(self):
        """Test handling of very small values."""
        result = RebalancingCalculations.calculate_deviation_severity(0.0001)
        assert result == "low"

    def test_should_handle_very_large_values(self):
        """Test handling of very large values."""
        result = RebalancingCalculations.calculate_total_transaction_costs(
            commission_costs=1e10,
            spread_costs=1e10,
            market_impact_costs=1e10,
        )
        assert result == pytest.approx(3e10)


class TestIntegration:
    """Integration tests combining multiple calculations."""

    def test_should_calculate_complete_rebalancing_scenario(self):
        """Test a complete rebalancing calculation scenario."""
        calc = RebalancingCalculations

        # Portfolio metrics
        metrics = calc.calculate_portfolio_metrics(
            weightings={"AAPL": 0.4, "GOOGL": 0.35, "MSFT": 0.25},
            values={"AAPL": 4000.0, "GOOGL": 3500.0, "MSFT": 2500.0},
            target_weights={"AAPL": 0.33, "GOOGL": 0.33, "MSFT": 0.34},
        )

        # Calculate urgency for max deviation
        urgency = calc.calculate_urgency_score(
            deviation=metrics["max_deviation"],
            volatility=20.0,
            market_conditions="normal",
        )

        # Determine priority
        priority = calc.determine_action_priority(urgency)

        # Calculate costs
        total_costs = calc.calculate_total_transaction_costs(
            commission_costs=50.0,
            spread_costs=25.0,
            market_impact_costs=10.0,
        )

        cost_pct = calc.calculate_cost_percentage(
            total_costs=total_costs,
            portfolio_value=metrics["total_value"],
        )

        break_even = calc.calculate_break_even_days(
            total_costs=total_costs,
            expected_daily_return_improvement=0.1,
            portfolio_value=metrics["total_value"],
        )

        # Verify complete scenario results
        assert metrics["total_value"] == pytest.approx(10000.0)
        assert priority in ["low", "medium", "high", "urgent"]
        assert total_costs == pytest.approx(85.0)
        assert cost_pct == pytest.approx(0.85)
        assert break_even is not None
        assert break_even > 0
