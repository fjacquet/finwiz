"""
Scenario comparison report generator for portfolio rebalancing.

This module generates comprehensive HTML reports comparing different
rebalancing scenarios with side-by-side analysis and visualizations
using BeautifulSoup4 for secure HTML generation.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from bs4 import BeautifulSoup

from finwiz.quantitative.scenario_analysis import ScenarioAnalysisReport
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

    def generate_scenario_comparison_report(self, scenario_report: ScenarioAnalysisReport, title: str = "Portfolio Rebalancing Scenario Analysis") -> str:
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
            "executive_summary": getattr(report, "executive_summary", "Comprehensive scenario analysis completed."),
            "analysis_metadata": {
                "timestamp": report.analysis_date.strftime("%Y-%m-%d %H:%M:%S"),
                "portfolio_id": getattr(report, "portfolio_id", "N/A"),
                "num_scenarios": len(report.scenarios),
                "num_sensitivity_params": len(report.sensitivity_results),
                "monte_carlo_simulations": report.monte_carlo_result.num_simulations if report.monte_carlo_result else 0,
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

        for scenario in report.scenarios:
            # Use the modified_parameters field from AlternativeScenario
            param_str = ", ".join([f"{k}: {v}" for k, v in scenario.modified_parameters.items()])
            cost_impact = f"${scenario.cost_difference:+,.0f}" if abs(scenario.cost_difference) >= 1 else "Minimal"
            risk_impact = f"{scenario.risk_difference:+.2f}" if abs(scenario.risk_difference) >= 0.01 else "Minimal"

            what_if_table["rows"].append([scenario.scenario_name, param_str, cost_impact, risk_impact, scenario.projected_outcome])

        # Scenario comparisons table
        comparison_table = {
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

    def _create_sensitivity_charts(self, report: ScenarioAnalysisReport) -> dict[str, Any]:
        """Create sensitivity analysis chart data."""
        charts = {}

        for result in report.sensitivity_results:
            # Calculate sensitivity metrics from the impact data
            cost_range = max(result.impact_on_cost) - min(result.impact_on_cost)
            risk_range = max(result.impact_on_risk) - min(result.impact_on_risk)
            return_range = max(result.impact_on_return) - min(result.impact_on_return)

            # Calculate a simple sensitivity score based on cost impact
            sensitivity_score = cost_range / 100.0  # Normalize to reasonable scale

            # Find optimal value (minimize cost while maintaining reasonable return)
            min_cost_idx = result.impact_on_cost.index(min(result.impact_on_cost))
            optimal_value = result.parameter_values[min_cost_idx]

            # Create chart data for each sensitivity parameter
            chart_data = {
                "parameter_name": result.parameter_name.replace("_", " ").title(),
                "x_values": result.parameter_values,
                "y_values": result.impact_on_cost,  # Use cost impact as primary metric
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
                "rebalancing_benefit": "N/A",  # Not available in current schema
            },
            "percentiles": {f"{p}th percentile": f"${value:,.0f}" for p, value in mc_result.final_value_percentiles.items()},
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
        if mc and mc.probability_of_loss > 0.3:
            findings.append(f"High downside risk: {mc.probability_of_loss:.1%} probability of loss")

        if mc and hasattr(mc, "rebalancing_benefit") and mc.rebalancing_benefit > 0:
            findings.append(f"Rebalancing provides ${mc.rebalancing_benefit:,.0f} expected benefit")

        # Sensitivity findings - calculate sensitivity from cost impact
        high_sensitivity = []
        for r in report.sensitivity_results:
            cost_range = max(r.impact_on_cost) - min(r.impact_on_cost)
            if cost_range > 1000:  # High cost sensitivity threshold
                high_sensitivity.append(r)

        if high_sensitivity:
            params = [r.parameter_name.replace("_", " ") for r in high_sensitivity]
            findings.append(f"High sensitivity to: {', '.join(params)}")

        # Scenario findings
        if report.scenario_comparisons:
            best_comparison = max(report.scenario_comparisons, key=lambda c: c.confidence_level)
            findings.append(f"Most efficient approach: {best_comparison.recommendation}")

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
        """Render the scenario report HTML template using BeautifulSoup4."""
        # Create HTML document using BeautifulSoup4
        soup = BeautifulSoup("", "html.parser")

        # Create HTML structure
        html = soup.new_tag("html", lang="en")

        # Create head
        head = soup.new_tag("head")

        # Meta tags
        charset_meta = soup.new_tag("meta")
        charset_meta["charset"] = "UTF-8"
        viewport_meta = soup.new_tag("meta")
        viewport_meta["name"] = "viewport"
        viewport_meta["content"] = "width=device-width, initial-scale=1.0"
        title_tag = soup.new_tag("title")
        title_tag.string = template_data["title"]

        # CSS styles
        style_tag = soup.new_tag("style")
        style_tag.string = """
        body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
        .header { background: #f4f4f4; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .section { margin-bottom: 30px; }
        .section h2 { color: #333; border-bottom: 2px solid #007acc; padding-bottom: 5px; }
        .section h3 { color: #555; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; font-weight: bold; }
        .metric { display: inline-block; margin: 10px; padding: 10px; background: #f9f9f9; border-radius: 5px; }
        .warning { background: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; border-radius: 5px; }
        .recommendation { background: #d4edda; border: 1px solid #c3e6cb; padding: 10px; border-radius: 5px; }
        .key-finding { background: #e2e3e5; padding: 8px; margin: 5px 0; border-radius: 3px; }
        """

        head.append(charset_meta)
        head.append(viewport_meta)
        head.append(title_tag)
        head.append(style_tag)

        # Create body
        body = soup.new_tag("body")

        # Header section
        header_div = soup.new_tag("div")
        header_div["class"] = "header"
        header_h1 = soup.new_tag("h1")
        header_h1.string = template_data["title"]
        header_div.append(header_h1)

        # Generated timestamp
        gen_p = soup.new_tag("p")
        gen_strong = soup.new_tag("strong")
        gen_strong.string = "Generated:"
        gen_p.append(gen_strong)
        gen_p.append(f" {template_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        header_div.append(gen_p)

        # Portfolio ID
        portfolio_p = soup.new_tag("p")
        portfolio_strong = soup.new_tag("strong")
        portfolio_strong.string = "Portfolio ID:"
        portfolio_p.append(portfolio_strong)
        portfolio_p.append(f" {template_data['summary_sections']['analysis_metadata']['portfolio_id']}")
        header_div.append(portfolio_p)

        body.append(header_div)

        # Executive Summary section
        exec_section = soup.new_tag("div")
        exec_section["class"] = "section"
        exec_h2 = soup.new_tag("h2")
        exec_h2.string = "Executive Summary"
        exec_section.append(exec_h2)

        exec_p = soup.new_tag("p")
        exec_p.string = template_data["summary_sections"]["executive_summary"]
        exec_section.append(exec_p)

        # Key Findings
        findings_h3 = soup.new_tag("h3")
        findings_h3.string = "Key Findings"
        exec_section.append(findings_h3)

        for finding in template_data["summary_sections"]["key_findings"]:
            finding_div = soup.new_tag("div")
            finding_div["class"] = "key-finding"
            finding_div.string = finding
            exec_section.append(finding_div)

        body.append(exec_section)

        # Analysis Overview section
        overview_section = soup.new_tag("div")
        overview_section["class"] = "section"
        overview_h2 = soup.new_tag("h2")
        overview_h2.string = "Analysis Overview"
        overview_section.append(overview_h2)

        # Metrics
        metadata = template_data["summary_sections"]["analysis_metadata"]

        scenarios_metric = soup.new_tag("div")
        scenarios_metric["class"] = "metric"
        scenarios_strong = soup.new_tag("strong")
        scenarios_strong.string = "Scenarios Analyzed:"
        scenarios_metric.append(scenarios_strong)
        scenarios_metric.append(f" {metadata['num_scenarios']}")
        overview_section.append(scenarios_metric)

        sensitivity_metric = soup.new_tag("div")
        sensitivity_metric["class"] = "metric"
        sensitivity_strong = soup.new_tag("strong")
        sensitivity_strong.string = "Sensitivity Parameters:"
        sensitivity_metric.append(sensitivity_strong)
        sensitivity_metric.append(f" {metadata['num_sensitivity_params']}")
        overview_section.append(sensitivity_metric)

        mc_metric = soup.new_tag("div")
        mc_metric["class"] = "metric"
        mc_strong = soup.new_tag("strong")
        mc_strong.string = "Monte Carlo Simulations:"
        mc_metric.append(mc_strong)
        mc_metric.append(f" {metadata['monte_carlo_simulations']:,}")
        overview_section.append(mc_metric)

        body.append(overview_section)

        # What-If Scenario Analysis section
        whatif_section = soup.new_tag("div")
        whatif_section["class"] = "section"
        whatif_h2 = soup.new_tag("h2")
        whatif_h2.string = "What-If Scenario Analysis"
        whatif_section.append(whatif_h2)

        # Create table
        whatif_table = soup.new_tag("table")
        whatif_thead = soup.new_tag("thead")
        whatif_header_row = soup.new_tag("tr")

        for header in template_data["comparison_tables"]["what_if_scenarios"]["headers"]:
            th = soup.new_tag("th")
            th.string = header
            whatif_header_row.append(th)

        whatif_thead.append(whatif_header_row)
        whatif_table.append(whatif_thead)

        whatif_tbody = soup.new_tag("tbody")
        for row in template_data["comparison_tables"]["what_if_scenarios"]["rows"]:
            tr = soup.new_tag("tr")
            for cell in row:
                td = soup.new_tag("td")
                td.string = str(cell)
                tr.append(td)
            whatif_tbody.append(tr)

        whatif_table.append(whatif_tbody)
        whatif_section.append(whatif_table)
        body.append(whatif_section)

        # Monte Carlo section
        mc_section = soup.new_tag("div")
        mc_section["class"] = "section"
        mc_h2 = soup.new_tag("h2")
        mc_h2.string = "Monte Carlo Simulation Results"
        mc_section.append(mc_h2)

        # Simulation Parameters
        sim_h3 = soup.new_tag("h3")
        sim_h3.string = "Simulation Parameters"
        mc_section.append(sim_h3)

        for k, v in template_data["monte_carlo_summary"]["simulation_params"].items():
            metric_div = soup.new_tag("div")
            metric_div["class"] = "metric"
            metric_strong = soup.new_tag("strong")
            metric_strong.string = f"{k}:"
            metric_div.append(metric_strong)
            metric_div.append(f" {v}")
            mc_section.append(metric_div)

        # Portfolio Outcomes
        outcomes_h3 = soup.new_tag("h3")
        outcomes_h3.string = "Portfolio Outcomes"
        mc_section.append(outcomes_h3)

        for k, v in template_data["monte_carlo_summary"]["portfolio_outcomes"].items():
            metric_div = soup.new_tag("div", **{"class": "metric"})
            metric_strong = soup.new_tag("strong")
            metric_strong.string = f"{k}:"
            metric_div.append(metric_strong)
            metric_div.append(f" {v}")
            mc_section.append(metric_div)

        # Risk Metrics
        risk_h3 = soup.new_tag("h3")
        risk_h3.string = "Risk Metrics"
        mc_section.append(risk_h3)

        for k, v in template_data["monte_carlo_summary"]["risk_metrics"].items():
            metric_div = soup.new_tag("div", **{"class": "metric"})
            metric_strong = soup.new_tag("strong")
            metric_strong.string = f"{k}:"
            metric_div.append(metric_strong)
            metric_div.append(f" {v}")
            mc_section.append(metric_div)

        # Rebalancing Metrics
        rebal_h3 = soup.new_tag("h3")
        rebal_h3.string = "Rebalancing Metrics"
        mc_section.append(rebal_h3)

        for k, v in template_data["monte_carlo_summary"]["rebalancing_metrics"].items():
            metric_div = soup.new_tag("div", **{"class": "metric"})
            metric_strong = soup.new_tag("strong")
            metric_strong.string = f"{k}:"
            metric_div.append(metric_strong)
            metric_div.append(f" {v}")
            mc_section.append(metric_div)

        body.append(mc_section)

        # Sensitivity Analysis section
        sens_section = soup.new_tag("div", **{"class": "section"})
        sens_h2 = soup.new_tag("h2")
        sens_h2.string = "Sensitivity Analysis"
        sens_section.append(sens_h2)

        sens_p = soup.new_tag("p")
        sens_p.string = "The following parameters show the highest sensitivity to portfolio outcomes:"
        sens_section.append(sens_p)

        for chart_data in template_data["sensitivity_charts"].values():
            chart_h3 = soup.new_tag("h3")
            chart_h3.string = chart_data["parameter_name"]
            sens_section.append(chart_h3)

            optimal_p = soup.new_tag("p")
            optimal_strong = soup.new_tag("strong")
            optimal_strong.string = "Optimal Value:"
            optimal_p.append(optimal_strong)
            optimal_p.append(f" {chart_data['optimal_label']}")
            sens_section.append(optimal_p)

            score_p = soup.new_tag("p")
            score_strong = soup.new_tag("strong")
            score_strong.string = "Sensitivity Score:"
            score_p.append(score_strong)
            score_p.append(f" {chart_data['sensitivity_score']:.1f}")
            sens_section.append(score_p)

        body.append(sens_section)

        # Recommendations section
        rec_section = soup.new_tag("div", **{"class": "section"})
        rec_h2 = soup.new_tag("h2")
        rec_h2.string = "Recommendations"
        rec_section.append(rec_h2)

        # Optimal Parameters
        opt_h3 = soup.new_tag("h3")
        opt_h3.string = "Optimal Parameters"
        rec_section.append(opt_h3)

        for k, v in template_data["recommendations"]["optimal_parameters"].items():
            metric_div = soup.new_tag("div", **{"class": "metric"})
            metric_strong = soup.new_tag("strong")
            metric_strong.string = f"{k}:"
            metric_div.append(metric_strong)
            metric_div.append(f" {v}")
            rec_section.append(metric_div)

        # Priority Actions
        actions_h3 = soup.new_tag("h3")
        actions_h3.string = "Priority Actions"
        rec_section.append(actions_h3)

        for action in template_data["recommendations"]["priority_actions"]:
            action_div = soup.new_tag("div", **{"class": "recommendation"})
            action_div.string = action
            rec_section.append(action_div)

        # Implementation Notes
        impl_h3 = soup.new_tag("h3")
        impl_h3.string = "Implementation Notes"
        rec_section.append(impl_h3)

        for note in template_data["recommendations"]["implementation_notes"]:
            note_div = soup.new_tag("div", **{"class": "recommendation"})
            note_div.string = note
            rec_section.append(note_div)

        # Risk Warnings (if any)
        if template_data["recommendations"]["risk_warnings"]:
            warnings_h3 = soup.new_tag("h3")
            warnings_h3.string = "Risk Warnings"
            rec_section.append(warnings_h3)

            for warning in template_data["recommendations"]["risk_warnings"]:
                warning_div = soup.new_tag("div", **{"class": "warning"})
                warning_div.string = warning
                rec_section.append(warning_div)

        body.append(rec_section)

        # Scenario Comparisons section
        comp_section = soup.new_tag("div", **{"class": "section"})
        comp_h2 = soup.new_tag("h2")
        comp_h2.string = "Scenario Comparisons"
        comp_section.append(comp_h2)

        if template_data["comparison_tables"]["scenario_comparisons"]["rows"]:
            # Create comparison table
            comp_table = soup.new_tag("table")
            comp_thead = soup.new_tag("thead")
            comp_header_row = soup.new_tag("tr")

            for header in template_data["comparison_tables"]["scenario_comparisons"]["headers"]:
                th = soup.new_tag("th")
                th.string = header
                comp_header_row.append(th)

            comp_thead.append(comp_header_row)
            comp_table.append(comp_thead)

            comp_tbody = soup.new_tag("tbody")
            for row in template_data["comparison_tables"]["scenario_comparisons"]["rows"]:
                tr = soup.new_tag("tr")
                for cell in row:
                    td = soup.new_tag("td")
                    td.string = str(cell)
                    tr.append(td)
                comp_tbody.append(tr)

            comp_table.append(comp_tbody)
            comp_section.append(comp_table)
        else:
            no_comp_p = soup.new_tag("p")
            no_comp_p.string = "No scenario comparisons available."
            comp_section.append(no_comp_p)

        body.append(comp_section)

        # Footer
        footer = soup.new_tag("footer", style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 0.9em;")

        footer_p1 = soup.new_tag("p")
        footer_p1.string = "Generated by FinWiz Portfolio Rebalancing Scenario Analyzer"
        footer.append(footer_p1)

        footer_p2 = soup.new_tag("p")
        footer_p2.string = f"Report generated on {template_data['timestamp'].strftime('%Y-%m-%d at %H:%M:%S')}"
        footer.append(footer_p2)

        body.append(footer)

        # Assemble document
        html.append(head)
        html.append(body)
        soup.append(html)

        # Generate final HTML with proper DOCTYPE
        return "<!DOCTYPE html>\n" + soup.prettify(formatter="html")

    def export_scenario_report_to_html_file(self, scenario_report: ScenarioAnalysisReport, output_path: str, title: str = "Portfolio Rebalancing Scenario Analysis") -> str:
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
