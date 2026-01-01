"""
Scenario report section builders.

Extracted from ScenarioComparisonReportGenerator for focused section creation.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from finwiz.quantitative.scenario_analysis import ScenarioAnalysisReport


def create_summary_sections(report: "ScenarioAnalysisReport", extract_key_findings_fn) -> dict[str, Any]:
    """Create summary sections for the report."""
    return {
        "executive_summary": getattr(report, "executive_summary", "Comprehensive scenario analysis completed."),
        "analysis_metadata": {
            "timestamp": report.analysis_date.strftime("%Y-%m-%d %H:%M:%S"),
            "portfolio_id": getattr(report, "portfolio_id", "N/A"),
            "num_scenarios": len(report.scenarios),
            "num_sensitivity_params": len(report.sensitivity_results),
            "monte_carlo_simulations": report.monte_carlo_result.num_simulations if report.monte_carlo_result else 0,
        },
        "key_findings": extract_key_findings_fn(report),
    }


def create_comparison_tables(report: "ScenarioAnalysisReport") -> dict[str, Any]:
    """Create comparison tables for scenarios."""
    # What-if scenarios table
    what_if_table: dict[str, Any] = {
        "headers": ["Scenario", "Modified Parameters", "Cost Impact", "Risk Impact", "Projected Outcome"],
        "rows": [],
    }

    for scenario in report.scenarios:
        param_str = ", ".join([f"{k}: {v}" for k, v in scenario.modified_parameters.items()])
        cost_impact = f"${scenario.cost_difference:+,.0f}" if abs(scenario.cost_difference) >= 1 else "Minimal"
        risk_impact = f"{scenario.risk_difference:+.2f}" if abs(scenario.risk_difference) >= 0.01 else "Minimal"

        what_if_table["rows"].append([scenario.scenario_name, param_str, cost_impact, risk_impact, scenario.projected_outcome])

    # Scenario comparisons table
    comparison_table: dict[str, Any] = {
        "headers": ["Scenario 1", "Scenario 2", "Return Diff", "Risk Diff", "Cost Diff", "Recommendation"],
        "rows": [],
    }

    for comparison in report.scenario_comparisons:
        comparison_table["rows"].append(
            [
                comparison.scenario_1_name,
                comparison.scenario_2_name,
                f"{comparison.return_difference:+.2%}",
                f"{comparison.risk_difference:+.2f}",
                f"${comparison.cost_difference:+,.0f}",
                comparison.recommendation,
            ]
        )

    return {
        "what_if_scenarios": what_if_table,
        "scenario_comparisons": comparison_table,
    }


def create_sensitivity_charts(report: "ScenarioAnalysisReport") -> dict[str, Any]:
    """Create sensitivity analysis chart data."""
    charts = {}

    for result in report.sensitivity_results:
        # Calculate sensitivity metrics from the impact data
        cost_range = max(result.impact_on_cost) - min(result.impact_on_cost)

        # Calculate a simple sensitivity score based on cost impact
        sensitivity_score = cost_range / 100.0  # Normalize to reasonable scale

        # Find optimal value (minimize cost while maintaining reasonable return)
        min_cost_idx = result.impact_on_cost.index(min(result.impact_on_cost))
        optimal_value = result.parameter_values[min_cost_idx]

        # Create chart data for each sensitivity parameter
        chart_data = {
            "parameter_name": result.parameter_name.replace("_", " ").title(),
            "x_values": result.parameter_values,
            "y_values": result.impact_on_cost,
            "optimal_value": optimal_value,
            "sensitivity_score": sensitivity_score,
            "confidence_interval": (min(result.parameter_values), max(result.parameter_values)),
        }

        # Format values for display
        if "tolerance" in result.parameter_name.lower():
            chart_data["x_labels"] = [f"{v:.1%}" for v in result.parameter_values]
            chart_data["optimal_label"] = f"{optimal_value:.1%}"
        elif "cost" in result.parameter_name.lower():
            chart_data["x_labels"] = [f"{v:.2%}" for v in result.parameter_values]
            chart_data["optimal_label"] = f"{optimal_value:.2%}"
        else:
            chart_data["x_labels"] = [f"{v:,.0f}" for v in result.parameter_values]
            chart_data["optimal_label"] = f"{optimal_value:,.0f}"

        charts[result.parameter_name] = chart_data

    return charts


def create_monte_carlo_summary(report: "ScenarioAnalysisReport") -> dict[str, Any]:
    """Create Monte Carlo simulation summary."""
    mc_result = report.monte_carlo_result

    return {
        "simulation_params": {
            "num_simulations": f"{mc_result.num_simulations:,}",
            "time_horizon": f"{mc_result.time_horizon_days} days",
            "time_horizon_years": f"{mc_result.time_horizon_days / 252:.1f} years",
        },
        "portfolio_outcomes": {
            "mean_value": f"${mc_result.mean_final_value:,.0f}",
            "median_value": f"${mc_result.final_value_percentiles.get('50', mc_result.mean_final_value):,.0f}",
            "std_deviation": f"${mc_result.std_final_value:,.0f}",
        },
        "risk_metrics": {
            "probability_of_loss": f"{mc_result.probability_of_loss:.1%}",
            "value_at_risk_95": f"${mc_result.value_at_risk_95:,.0f}",
            "expected_shortfall_95": f"${mc_result.expected_shortfall_95:,.0f}",
        },
        "rebalancing_metrics": {
            "mean_frequency": f"{mc_result.mean_rebalancing_frequency:.1f} times/year",
            "mean_costs": f"${mc_result.mean_transaction_costs:,.0f}/year",
            "rebalancing_benefit": "N/A",
        },
        "percentiles": {f"{p}th percentile": f"${value:,.0f}" for p, value in mc_result.final_value_percentiles.items()},
    }


def create_recommendations_section(
    report: "ScenarioAnalysisReport",
    format_optimal_params_fn,
    extract_priority_actions_fn,
) -> dict[str, Any]:
    """Create recommendations section."""
    return {
        "optimal_parameters": format_optimal_params_fn(report.optimal_parameters),
        "risk_warnings": report.risk_warnings,
        "implementation_notes": report.implementation_notes,
        "priority_actions": extract_priority_actions_fn(report),
    }


def extract_key_findings(report: "ScenarioAnalysisReport") -> list[str]:
    """Extract key findings from the analysis."""
    findings = []

    # Monte Carlo findings
    mc = report.monte_carlo_result
    if mc and mc.probability_of_loss > 0.3:
        findings.append(f"High downside risk: {mc.probability_of_loss:.1%} probability of loss")

    if mc and hasattr(mc, "rebalancing_benefit") and mc.rebalancing_benefit > 0:
        findings.append(f"Rebalancing provides ${mc.rebalancing_benefit:,.0f} expected benefit")

    # Sensitivity findings - calculate sensitivity from cost impact
    high_sensitivity = []
    for r in report.sensitivity_results:
        cost_range = max(r.impact_on_cost) - min(r.impact_on_cost)
        if cost_range > 1000:
            high_sensitivity.append(r)

    if high_sensitivity:
        params = [r.parameter_name.replace("_", " ") for r in high_sensitivity]
        findings.append(f"High sensitivity to: {', '.join(params)}")

    # Scenario findings
    if report.scenario_comparisons:
        best_comparison = max(report.scenario_comparisons, key=lambda c: c.confidence_level)
        findings.append(f"Most efficient approach: {best_comparison.recommendation}")

    return findings


def format_optimal_parameters(optimal_params: dict[str, Any]) -> dict[str, str]:
    """Format optimal parameters for display."""
    formatted = {}

    for param, value in optimal_params.items():
        if "tolerance" in param.lower() and "cost" not in param.lower():
            formatted[param.replace("_", " ").title()] = f"{value:.1%}"
        elif "cost" in param.lower() and "rate" in param.lower():
            formatted[param.replace("_", " ").title()] = f"{value:.2%}"
        elif "frequency" in param.lower():
            formatted[param.replace("_", " ").title()] = f"{value:.1f} times/year"
        elif isinstance(value, float):
            formatted[param.replace("_", " ").title()] = f"{value:,.2f}"
        else:
            formatted[param.replace("_", " ").title()] = str(value)

    return formatted


def extract_priority_actions(report: "ScenarioAnalysisReport") -> list[str]:
    """Extract priority actions from the analysis."""
    actions = []

    # High-priority warnings
    if any("high" in warning.lower() for warning in report.risk_warnings):
        actions.append("Review risk management strategy - high risk detected")

    # Parameter optimization
    if "tolerance_band" in report.optimal_parameters:
        tolerance = report.optimal_parameters["tolerance_band"]
        actions.append(f"Adjust tolerance bands to {tolerance:.1%} for optimal performance")

    # Cost optimization
    if "transaction_cost_rate" in report.optimal_parameters:
        cost_rate = report.optimal_parameters["transaction_cost_rate"]
        actions.append(f"Consider brokers with transaction costs ≤ {cost_rate:.2%}")

    # Frequency optimization
    if "recommended_rebalancing_frequency" in report.optimal_parameters:
        freq = report.optimal_parameters["recommended_rebalancing_frequency"]
        actions.append(f"Implement rebalancing frequency of {freq:.1f} times per year")

    return actions
