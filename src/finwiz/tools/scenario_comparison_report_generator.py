"""
Scenario comparison report generator for portfolio rebalancing.

This module generates comprehensive HTML reports comparing different
rebalancing scenarios with side-by-side analysis and visualizations.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from finwiz.quantitative.scenario_analyzer import ScenarioAnalysisReport
from finwiz.tools.html_report_generator import HTMLReportGenerator

logger = logging.getLogger(__name__)


class ScenarioComparisonReportGenerator(HTMLReportGenerator):
    """
    Generator for scenario comparison reports.

    Creates comprehensive HTML reports with side-by-side scenario comparisons,
    sensitivity analysis charts, Monte Carlo results, and implementation recommendations.
    """

    def __init__(self) -> None:
        """Initialize the scenario comparison report generator."""
        super().__init__()
        self.logger = logging.getLogger(__name__)

    def generate_scenario_comparison_report(
        self, scenario_report: ScenarioAnalysisReport, title: str = "Portfolio Rebalancing Scenario Analysis"
    ) -> str:
        """
        Generate comprehensive scenario comparison HTML report.

        Args:
            scenario_report: Complete scenario analysis results
            title: Report title

        Returns:
            HTML report string

        """
        self.logger.info("Generating scenario comparison report")

        # Prepare template data
        template_data = {
            "title": title,
            "report": scenario_report,
            "timestamp": datetime.now(),
            "base_currency": "USD",
            "summary_sections": self._create_summary_sections(scenario_report),
            "comparison_tables": self._create_comparison_tables(scenario_report),
            "sensitivity_charts": self._create_sensitivity_charts(scenario_report),
            "monte_carlo_summary": self._create_monte_carlo_summary(scenario_report),
            "recommendations": self._create_recommendations_section(scenario_report),
        }

        # Generate HTML content
        html_content = self._render_scenario_report_template(template_data)

        self.logger.info("Scenario comparison report generated successfully")
        return html_content

    def _create_summary_sections(self, report: ScenarioAnalysisReport) -> dict[str, Any]:
        """Create summary sections for the report."""
        return {
            "executive_summary": report.executive_summary,
            "analysis_metadata": {
                "timestamp": report.analysis_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "portfolio_id": report.portfolio_id or "N/A",
                "num_scenarios": len(report.what_if_scenarios),
                "num_sensitivity_params": len(report.sensitivity_results),
                "monte_carlo_simulations": report.monte_carlo_result.num_simulations,
            },
            "key_findings": self._extract_key_findings(report),
        }

    def _create_comparison_tables(self, report: ScenarioAnalysisReport) -> dict[str, Any]:
        """Create comparison tables for scenarios."""
        # What-if scenarios table
        what_if_table = {
            "headers": ["Scenario", "Modified Parameters", "Cost Impact", "Risk Impact", "Projected Outcome"],
            "rows": [],
        }

        for scenario in report.what_if_scenarios:
            param_str = ", ".join([f"{k}: {v}" for k, v in scenario.modified_parameters.items()])
            cost_impact = f"${scenario.cost_difference:+,.0f}" if abs(scenario.cost_difference) >= 1 else "Minimal"
            risk_impact = f"{scenario.risk_difference:+.2f}" if abs(scenario.risk_difference) >= 0.01 else "Minimal"

            what_if_table["rows"].append([scenario.scenario_name, param_str, cost_impact, risk_impact, scenario.projected_outcome])

        # Scenario comparisons table
        comparison_table = {
            "headers": ["Base Scenario", "Alternative", "Return Diff", "Risk Diff", "Cost Diff", "Preferred"],
            "rows": [],
        }

        for comparison in report.scenario_comparisons:
            comparison_table["rows"].append(
                [
                    comparison.base_scenario,
                    comparison.alternative_scenario,
                    f"{comparison.return_difference:+.2%}",
                    f"{comparison.risk_difference:+.2f}",
                    f"${comparison.cost_difference:+,.0f}",
                    comparison.preferred_scenario,
                ]
            )

        return {
            "what_if_scenarios": what_if_table,
            "scenario_comparisons": comparison_table,
        }

    def _create_sensitivity_charts(self, report: ScenarioAnalysisReport) -> dict[str, Any]:
        """Create sensitivity analysis chart data."""
        charts = {}

        for result in report.sensitivity_results:
            # Create chart data for each sensitivity parameter
            chart_data = {
                "parameter_name": result.parameter_name.replace("_", " ").title(),
                "x_values": result.parameter_values,
                "y_values": result.outcome_values,
                "optimal_value": result.optimal_value,
                "sensitivity_score": result.sensitivity_score,
                "confidence_interval": result.confidence_interval,
            }

            # Format values for display
            if "tolerance" in result.parameter_name.lower():
                chart_data["x_labels"] = [f"{v:.1%}" for v in result.parameter_values]
                chart_data["optimal_label"] = f"{result.optimal_value:.1%}"
            elif "cost" in result.parameter_name.lower():
                chart_data["x_labels"] = [f"{v:.2%}" for v in result.parameter_values]
                chart_data["optimal_label"] = f"{result.optimal_value:.2%}"
            else:
                chart_data["x_labels"] = [f"{v:,.0f}" for v in result.parameter_values]
                chart_data["optimal_label"] = f"{result.optimal_value:,.0f}"

            charts[result.parameter_name] = chart_data

        return charts

    def _create_monte_carlo_summary(self, report: ScenarioAnalysisReport) -> dict[str, Any]:
        """Create Monte Carlo simulation summary."""
        mc_result = report.monte_carlo_result

        return {
            "simulation_params": {
                "num_simulations": f"{mc_result.num_simulations:,}",
                "time_horizon": f"{mc_result.time_horizon_days} days",
                "time_horizon_years": f"{mc_result.time_horizon_days / 252:.1f} years",
            },
            "portfolio_outcomes": {
                "mean_value": f"${mc_result.mean_portfolio_value:,.0f}",
                "median_value": f"${mc_result.median_portfolio_value:,.0f}",
                "std_deviation": f"${mc_result.std_portfolio_value:,.0f}",
            },
            "risk_metrics": {
                "probability_of_loss": f"{mc_result.probability_of_loss:.1%}",
                "value_at_risk_95": f"${mc_result.value_at_risk_95:,.0f}",
                "expected_shortfall_95": f"${mc_result.expected_shortfall_95:,.0f}",
            },
            "rebalancing_metrics": {
                "mean_frequency": f"{mc_result.mean_rebalancing_frequency:.1f} times/year",
                "mean_costs": f"${mc_result.mean_transaction_costs:,.0f}/year",
                "rebalancing_benefit": f"${mc_result.rebalancing_benefit:,.0f}",
            },
            "percentiles": {f"{p}th percentile": f"${value:,.0f}" for p, value in mc_result.percentiles.items()},
        }

    def _create_recommendations_section(self, report: ScenarioAnalysisReport) -> dict[str, Any]:
        """Create recommendations section."""
        return {
            "optimal_parameters": self._format_optimal_parameters(report.optimal_parameters),
            "risk_warnings": report.risk_warnings,
            "implementation_notes": report.implementation_notes,
            "priority_actions": self._extract_priority_actions(report),
        }

    def _extract_key_findings(self, report: ScenarioAnalysisReport) -> list[str]:
        """Extract key findings from the analysis."""
        findings = []

        # Monte Carlo findings
        mc = report.monte_carlo_result
        if mc.probability_of_loss > 0.3:
            findings.append(f"High downside risk: {mc.probability_of_loss:.1%} probability of loss")

        if mc.rebalancing_benefit > 0:
            findings.append(f"Rebalancing provides ${mc.rebalancing_benefit:,.0f} expected benefit")

        # Sensitivity findings
        high_sensitivity = [r for r in report.sensitivity_results if r.sensitivity_score > 10]
        if high_sensitivity:
            params = [r.parameter_name.replace("_", " ") for r in high_sensitivity]
            findings.append(f"High sensitivity to: {', '.join(params)}")

        # Scenario findings
        if report.scenario_comparisons:
            best_comparison = max(report.scenario_comparisons, key=lambda c: c.efficiency_score)
            findings.append(f"Most efficient approach: {best_comparison.preferred_scenario}")

        return findings

    def _format_optimal_parameters(self, optimal_params: dict[str, Any]) -> dict[str, str]:
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

    def _extract_priority_actions(self, report: ScenarioAnalysisReport) -> list[str]:
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

    def _render_scenario_report_template(self, template_data: dict[str, Any]) -> str:
        """Render the scenario report HTML template."""
        # This is a simplified template - in practice, would use a proper template engine
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{template_data["title"]}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        .header {{ background: #f4f4f4; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .section {{ margin-bottom: 30px; }}
        .section h2 {{ color: #333; border-bottom: 2px solid #007acc; padding-bottom: 5px; }}
        .section h3 {{ color: #555; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; font-weight: bold; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; background: #f9f9f9; border-radius: 5px; }}
        .warning {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; border-radius: 5px; }}
        .recommendation {{ background: #d4edda; border: 1px solid #c3e6cb; padding: 10px; border-radius: 5px; }}
        .key-finding {{ background: #e2e3e5; padding: 8px; margin: 5px 0; border-radius: 3px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{template_data["title"]}</h1>
        <p><strong>Generated:</strong> {template_data["timestamp"].strftime("%Y-%m-%d %H:%M:%S")}</p>
        <p><strong>Portfolio ID:</strong> {template_data["summary_sections"]["analysis_metadata"]["portfolio_id"]}</p>
    </div>

    <div class="section">
        <h2>Executive Summary</h2>
        <p>{template_data["summary_sections"]["executive_summary"]}</p>

        <h3>Key Findings</h3>
        {"".join([f'<div class="key-finding">{finding}</div>' for finding in template_data["summary_sections"]["key_findings"]])}
    </div>

    <div class="section">
        <h2>Analysis Overview</h2>
        <div class="metric">
            <strong>Scenarios Analyzed:</strong> {template_data["summary_sections"]["analysis_metadata"]["num_scenarios"]}
        </div>
        <div class="metric">
            <strong>Sensitivity Parameters:</strong> {
            template_data["summary_sections"]["analysis_metadata"]["num_sensitivity_params"]
        }
        </div>
        <div class="metric">
            <strong>Monte Carlo Simulations:</strong> {
            template_data["summary_sections"]["analysis_metadata"]["monte_carlo_simulations"]:,}
        </div>
    </div>

    <div class="section">
        <h2>What-If Scenario Analysis</h2>
        <table>
            <thead>
                <tr>{
            "".join([f"<th>{header}</th>" for header in template_data["comparison_tables"]["what_if_scenarios"]["headers"]])
        }</tr>
            </thead>
            <tbody>
                {
            "".join(
                [
                    f"<tr>{''.join([f'<td>{cell}</td>' for cell in row])}</tr>"
                    for row in template_data["comparison_tables"]["what_if_scenarios"]["rows"]
                ]
            )
        }
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2>Monte Carlo Simulation Results</h2>
        <h3>Simulation Parameters</h3>
        {
            "".join(
                [
                    f'<div class="metric"><strong>{k}:</strong> {v}</div>'
                    for k, v in template_data["monte_carlo_summary"]["simulation_params"].items()
                ]
            )
        }

        <h3>Portfolio Outcomes</h3>
        {
            "".join(
                [
                    f'<div class="metric"><strong>{k}:</strong> {v}</div>'
                    for k, v in template_data["monte_carlo_summary"]["portfolio_outcomes"].items()
                ]
            )
        }

        <h3>Risk Metrics</h3>
        {
            "".join(
                [
                    f'<div class="metric"><strong>{k}:</strong> {v}</div>'
                    for k, v in template_data["monte_carlo_summary"]["risk_metrics"].items()
                ]
            )
        }

        <h3>Rebalancing Metrics</h3>
        {
            "".join(
                [
                    f'<div class="metric"><strong>{k}:</strong> {v}</div>'
                    for k, v in template_data["monte_carlo_summary"]["rebalancing_metrics"].items()
                ]
            )
        }
    </div>

    <div class="section">
        <h2>Sensitivity Analysis</h2>
        <p>The following parameters show the highest sensitivity to portfolio outcomes:</p>
        {
            "".join(
                [
                    f'''
        <h3>{chart_data["parameter_name"]}</h3>
        <p><strong>Optimal Value:</strong> {chart_data["optimal_label"]}</p>
        <p><strong>Sensitivity Score:</strong> {chart_data["sensitivity_score"]:.1f}</p>
        '''
                    for chart_data in template_data["sensitivity_charts"].values()
                ]
            )
        }
    </div>

    <div class="section">
        <h2>Recommendations</h2>

        <h3>Optimal Parameters</h3>
        {
            "".join(
                [
                    f'<div class="metric"><strong>{k}:</strong> {v}</div>'
                    for k, v in template_data["recommendations"]["optimal_parameters"].items()
                ]
            )
        }

        <h3>Priority Actions</h3>
        {
            "".join(
                [f'<div class="recommendation">{action}</div>' for action in template_data["recommendations"]["priority_actions"]]
            )
        }

        <h3>Implementation Notes</h3>
        {
            "".join(
                [f'<div class="recommendation">{note}</div>' for note in template_data["recommendations"]["implementation_notes"]]
            )
        }

        {
            "<h3>Risk Warnings</h3>"
            + "".join([f'<div class="warning">{warning}</div>' for warning in template_data["recommendations"]["risk_warnings"]])
            if template_data["recommendations"]["risk_warnings"]
            else ""
        }
    </div>

    <div class="section">
        <h2>Scenario Comparisons</h2>
        {
            "<table><thead><tr>"
            + "".join([f"<th>{header}</th>" for header in template_data["comparison_tables"]["scenario_comparisons"]["headers"]])
            + "</tr></thead><tbody>"
            + "".join(
                [
                    f"<tr>{''.join([f'<td>{cell}</td>' for cell in row])}</tr>"
                    for row in template_data["comparison_tables"]["scenario_comparisons"]["rows"]
                ]
            )
            + "</tbody></table>"
            if template_data["comparison_tables"]["scenario_comparisons"]["rows"]
            else "<p>No scenario comparisons available.</p>"
        }
    </div>

    <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 0.9em;">
        <p>Generated by FinWiz Portfolio Rebalancing Scenario Analyzer</p>
        <p>Report generated on {template_data["timestamp"].strftime("%Y-%m-%d at %H:%M:%S")}</p>
    </footer>
</body>
</html>
        """

        return html.strip()

    def export_scenario_report_to_html_file(
        self, scenario_report: ScenarioAnalysisReport, output_path: str, title: str = "Portfolio Rebalancing Scenario Analysis"
    ) -> str:
        """
        Export scenario comparison report to HTML file.

        Args:
            scenario_report: Complete scenario analysis results
            output_path: Path for HTML output
            title: Report title

        Returns:
            Path to generated HTML file

        """
        html_content = self.generate_scenario_comparison_report(scenario_report, title)

        # Write HTML content to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        self.logger.info(f"Scenario report exported to {output_path}")
        return output_path
