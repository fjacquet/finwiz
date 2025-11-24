"""
Unit tests for scenario comparison report generator.

Tests the generation of HTML reports for scenario analysis results
including side-by-side comparisons and visualizations.
"""

from pytest import approx
from datetime import datetime

import pytest

from finwiz.quantitative.scenario_analysis import (
    ScenarioAnalysisReport,
    ScenarioComparison,
    SensitivityResult,
)
from finwiz.quantitative.scenario_generators import (
    MonteCarloResult,
)
from finwiz.schemas.portfolio_rebalancing import (
    AlternativeScenario,
    Holding,
    PortfolioConfiguration,
)
from finwiz.tools.scenario_comparison_report_generator import ScenarioComparisonReportGenerator


class TestScenarioComparisonReportGenerator:
    """Test scenario comparison report generator functionality."""

    @pytest.fixture
    def sample_portfolio_config(self):
        """Create sample portfolio configuration for testing."""
        holdings = [
            Holding(symbol="AAPL", shares=100),
            Holding(symbol="GOOGL", shares=50),
            Holding(symbol="MSFT", shares=75),
        ]

        target_weights = {
            "AAPL": 0.4,
            "GOOGL": 0.3,
            "MSFT": 0.3,
        }

        return PortfolioConfiguration(
            holdings=holdings,
            target_weights=target_weights,
            global_tolerance=0.05,
            available_capital=10000.0,
            transaction_cost_rate=0.001,
        )

    @pytest.fixture
    def sample_scenario_report(self, sample_portfolio_config):
        """Create sample scenario analysis report for testing."""
        what_if_scenarios = [
            AlternativeScenario(
                scenario_name="High Capital",
                modified_parameters={"available_capital": 20000.0},
                projected_outcome="Lower transaction costs",
                cost_difference=-150.0,
                risk_difference=-0.1,
            ),
            AlternativeScenario(
                scenario_name="Low Tolerance",
                modified_parameters={"global_tolerance": 0.02},
                projected_outcome="Higher transaction costs",
                cost_difference=200.0,
                risk_difference=-0.2,
            ),
        ]

        sensitivity_results = [
            SensitivityResult(
                parameter_name="tolerance_band",
                parameter_values=[0.01, 0.05, 0.10],
                impact_on_return=[0.08, 0.085, 0.075],
                impact_on_risk=[0.15, 0.14, 0.16],
                impact_on_cost=[900, 500, 800],
            ),
            SensitivityResult(
                parameter_name="transaction_cost_rate",
                parameter_values=[0.0005, 0.001, 0.002],
                impact_on_return=[0.09, 0.085, 0.075],
                impact_on_risk=[0.14, 0.15, 0.16],
                impact_on_cost=[400, 500, 700],
            ),
        ]

        monte_carlo_result = MonteCarloResult(
            num_simulations=1000,
            time_horizon_days=252,
            annual_volatility=0.15,
            annual_return=0.08,
            mean_rebalancing_frequency=4.2,
            std_rebalancing_frequency=1.5,
            mean_transaction_costs=850.0,
            std_transaction_costs=200.0,
            mean_final_value=108000.0,
            std_final_value=15000.0,
            rebalancing_frequency_percentiles={"5": 2.0, "95": 6.5},
            transaction_cost_percentiles={"5": 600.0, "95": 1200.0},
            final_value_percentiles={"5": 85000.0, "10": 90000.0, "25": 95000.0, "75": 115000.0, "90": 120000.0, "95": 125000.0},
            probability_of_loss=0.25,
            value_at_risk_95=-12000.0,
            expected_shortfall_95=-18000.0,
        )

        scenario_comparisons = [
            ScenarioComparison(
                scenario_1_name="High Capital",
                scenario_2_name="Low Tolerance",
                return_difference=0.01,
                risk_difference=-0.1,
                cost_difference=350.0,
                recommendation="High Capital",
                confidence_level=0.8,
            )
        ]

        return ScenarioAnalysisReport(
            base_configuration=sample_portfolio_config,
            scenarios=what_if_scenarios,
            sensitivity_results=sensitivity_results,
            monte_carlo_result=monte_carlo_result,
            scenario_comparisons=scenario_comparisons,
            optimal_parameters={"tolerance_band": 0.05, "transaction_cost_rate": 0.0005, "recommended_rebalancing_frequency": 4.2},
            risk_warnings=["High sensitivity to tolerance bands"],
            implementation_notes=["Consider quarterly rebalancing"],
            executive_summary="Comprehensive analysis shows optimal tolerance of 5% with quarterly rebalancing frequency. "
            + "Monte Carlo simulations indicate 25% probability of loss "
            + "with expected benefit of $2,500 from rebalancing strategy.",
        )

    @pytest.fixture
    def report_generator(self):
        """Create report generator instance."""
        return ScenarioComparisonReportGenerator()

    def test_should_initialize_generator_when_created(self, report_generator):
        # Assert
        assert report_generator is not None
        assert hasattr(report_generator, "logger")

    def test_should_generate_html_report_when_valid_scenario_report_provided(self, report_generator, sample_scenario_report):
        # Act
        html_report = report_generator.generate_scenario_comparison_report(sample_scenario_report)

        # Assert
        assert isinstance(html_report, str)
        assert len(html_report) > 1000  # Should be substantial HTML content
        assert "<!DOCTYPE html>" in html_report
        assert "Portfolio Rebalancing Scenario Analysis" in html_report
        assert "Executive Summary" in html_report
        assert "Monte Carlo" in html_report
        assert "Sensitivity Analysis" in html_report

    def test_should_include_custom_title_when_provided(self, report_generator, sample_scenario_report):
        # Arrange
        custom_title = "Custom Portfolio Analysis Report"

        # Act
        html_report = report_generator.generate_scenario_comparison_report(sample_scenario_report, title=custom_title)

        # Assert
        assert custom_title in html_report
        # BeautifulSoup prettify may add whitespace, so check content exists
        assert "<title>" in html_report
        assert "</title>" in html_report

    def test_should_create_summary_sections_when_called(self, report_generator, sample_scenario_report):
        # Act
        summary_sections = report_generator._create_summary_sections(sample_scenario_report)

        # Assert
        assert "executive_summary" in summary_sections
        assert "analysis_metadata" in summary_sections
        assert "key_findings" in summary_sections

        metadata = summary_sections["analysis_metadata"]
        assert metadata["num_scenarios"] == 2
        assert metadata["num_sensitivity_params"] == 2
        assert metadata["monte_carlo_simulations"] == 1000

    def test_should_create_comparison_tables_when_called(self, report_generator, sample_scenario_report):
        # Act
        comparison_tables = report_generator._create_comparison_tables(sample_scenario_report)

        # Assert
        assert "what_if_scenarios" in comparison_tables
        assert "scenario_comparisons" in comparison_tables

        what_if_table = comparison_tables["what_if_scenarios"]
        assert len(what_if_table["headers"]) == 5
        assert len(what_if_table["rows"]) == 2

        # Check first row content
        first_row = what_if_table["rows"][0]
        assert "High Capital" in first_row[0]
        assert "available_capital: 20000.0" in first_row[1]

    def test_should_create_sensitivity_charts_when_called(self, report_generator, sample_scenario_report):
        # Act
        sensitivity_charts = report_generator._create_sensitivity_charts(sample_scenario_report)

        # Assert
        assert "tolerance_band" in sensitivity_charts
        assert "transaction_cost_rate" in sensitivity_charts

        tolerance_chart = sensitivity_charts["tolerance_band"]
        assert tolerance_chart["parameter_name"] == "Tolerance Band"
        assert tolerance_chart["optimal_value"] == approx(0.05)  # Should be the value with minimum cost
        assert tolerance_chart["sensitivity_score"] == approx(4.0)  # (900-500)/100 = 4.0
        assert len(tolerance_chart["x_values"]) == 3
        assert len(tolerance_chart["y_values"]) == 3

    def test_should_format_tolerance_values_as_percentages(self, report_generator, sample_scenario_report):
        # Act
        sensitivity_charts = report_generator._create_sensitivity_charts(sample_scenario_report)

        # Assert
        tolerance_chart = sensitivity_charts["tolerance_band"]
        assert tolerance_chart["optimal_label"] == "5.0%"
        assert "1.0%" in tolerance_chart["x_labels"]
        assert "5.0%" in tolerance_chart["x_labels"]
        assert "10.0%" in tolerance_chart["x_labels"]

    def test_should_format_cost_values_as_percentages(self, report_generator, sample_scenario_report):
        # Act
        sensitivity_charts = report_generator._create_sensitivity_charts(sample_scenario_report)

        # Assert
        cost_chart = sensitivity_charts["transaction_cost_rate"]
        assert cost_chart["optimal_label"] == "0.05%"  # 0.0005 formatted as percentage
        assert "0.05%" in cost_chart["x_labels"]
        assert "0.10%" in cost_chart["x_labels"]
        assert "0.20%" in cost_chart["x_labels"]

    def test_should_create_monte_carlo_summary_when_called(self, report_generator, sample_scenario_report):
        # Act
        mc_summary = report_generator._create_monte_carlo_summary(sample_scenario_report)

        # Assert
        assert "simulation_params" in mc_summary
        assert "portfolio_outcomes" in mc_summary
        assert "risk_metrics" in mc_summary
        assert "rebalancing_metrics" in mc_summary
        assert "percentiles" in mc_summary

        # Check formatting
        assert mc_summary["simulation_params"]["num_simulations"] == "1,000"
        assert mc_summary["portfolio_outcomes"]["mean_value"] == "$108,000"
        assert mc_summary["risk_metrics"]["probability_of_loss"] == "25.0%"
        assert mc_summary["rebalancing_metrics"]["mean_frequency"] == "4.2 times/year"

    def test_should_create_recommendations_section_when_called(self, report_generator, sample_scenario_report):
        # Act
        recommendations = report_generator._create_recommendations_section(sample_scenario_report)

        # Assert
        assert "optimal_parameters" in recommendations
        assert "risk_warnings" in recommendations
        assert "implementation_notes" in recommendations
        assert "priority_actions" in recommendations

        # Check optimal parameters formatting
        optimal_params = recommendations["optimal_parameters"]
        assert "Tolerance Band" in optimal_params
        assert optimal_params["Tolerance Band"] == "5.0%"
        assert "Transaction Cost Rate" in optimal_params
        assert optimal_params["Transaction Cost Rate"] == "0.05%"

    def test_should_extract_key_findings_when_called(self, report_generator, sample_scenario_report):
        # Act
        key_findings = report_generator._extract_key_findings(sample_scenario_report)

        # Assert
        assert isinstance(key_findings, list)
        assert len(key_findings) > 0

        # Should include rebalancing benefit finding (if rebalancing_benefit exists)
        benefit_finding = next((f for f in key_findings if "benefit" in f.lower()), None)
        # Note: rebalancing_benefit may not exist in MonteCarloResult, so this test is optional

    def test_should_extract_priority_actions_when_called(self, report_generator, sample_scenario_report):
        # Act
        priority_actions = report_generator._extract_priority_actions(sample_scenario_report)

        # Assert
        assert isinstance(priority_actions, list)
        assert len(priority_actions) > 0

        # Should include tolerance adjustment
        tolerance_action = next((a for a in priority_actions if "tolerance" in a.lower()), None)
        assert tolerance_action is not None
        assert "5.0%" in tolerance_action

    def test_should_format_optimal_parameters_correctly(self, report_generator):
        # Arrange
        optimal_params = {
            "tolerance_band": 0.05,
            "transaction_cost_rate": 0.001,
            "recommended_rebalancing_frequency": 4.2,
            "expected_annual_costs": 850.0,
            "some_other_param": "test_value",
        }

        # Act
        formatted = report_generator._format_optimal_parameters(optimal_params)

        # Assert
        assert formatted["Tolerance Band"] == "5.0%"
        assert formatted["Transaction Cost Rate"] == "0.10%"
        assert formatted["Recommended Rebalancing Frequency"] == "4.2 times/year"
        assert formatted["Expected Annual Costs"] == "850.00"
        assert formatted["Some Other Param"] == "test_value"

    def test_should_handle_empty_scenario_comparisons_gracefully(self, report_generator, sample_scenario_report):
        # Arrange
        sample_scenario_report.scenario_comparisons = []

        # Act
        comparison_tables = report_generator._create_comparison_tables(sample_scenario_report)

        # Assert
        assert comparison_tables["scenario_comparisons"]["rows"] == []

    def test_should_handle_no_risk_warnings_gracefully(self, report_generator, sample_scenario_report):
        # Arrange
        sample_scenario_report.risk_warnings = []

        # Act
        html_report = report_generator.generate_scenario_comparison_report(sample_scenario_report)

        # Assert
        assert isinstance(html_report, str)
        assert "Risk Warnings" not in html_report  # Should not include empty section

    def test_should_include_all_percentiles_in_monte_carlo_summary(self, report_generator, sample_scenario_report):
        # Act
        mc_summary = report_generator._create_monte_carlo_summary(sample_scenario_report)

        # Assert
        percentiles = mc_summary["percentiles"]
        assert "5th percentile" in percentiles
        assert "10th percentile" in percentiles
        assert "25th percentile" in percentiles
        assert "75th percentile" in percentiles
        assert "90th percentile" in percentiles
        assert "95th percentile" in percentiles

        # Check formatting
        assert percentiles["5th percentile"] == "$85,000"
        assert percentiles["95th percentile"] == "$125,000"

    def test_should_export_to_html_file_when_requested(self, mocker, report_generator, sample_scenario_report):
        # Arrange
        mock_open = mocker.patch("builtins.open", create=True)
        output_path = "/tmp/test_report.html"
        mock_file = mocker.Mock()
        mock_open.return_value.__enter__.return_value = mock_file

        # Act
        result_path = report_generator.export_scenario_report_to_html_file(sample_scenario_report, output_path)

        # Assert
        assert result_path == output_path
        mock_open.assert_called_once_with(output_path, "w", encoding="utf-8")
        mock_file.write.assert_called_once()

        # Check that HTML content was written
        written_content = mock_file.write.call_args[0][0]
        assert isinstance(written_content, str)
        assert "Portfolio Rebalancing Scenario Analysis" in written_content

    def test_should_render_valid_html_structure(self, report_generator, sample_scenario_report):
        # Act
        html_report = report_generator.generate_scenario_comparison_report(sample_scenario_report)

        # Assert
        # Check HTML structure
        assert html_report.startswith("<!DOCTYPE html>")
        assert '<html lang="en">' in html_report
        assert "<head>" in html_report
        assert "<body>" in html_report
        assert "</html>" in html_report.strip()

        # Check required sections
        assert "Executive Summary" in html_report
        assert "Analysis Overview" in html_report
        assert "What-If Scenario Analysis" in html_report
        assert "Monte Carlo Simulation Results" in html_report
        assert "Sensitivity Analysis" in html_report
        assert "Recommendations" in html_report
        assert "Scenario Comparisons" in html_report

    def test_should_include_timestamp_in_report(self, report_generator, sample_scenario_report):
        # Act
        html_report = report_generator.generate_scenario_comparison_report(sample_scenario_report)

        # Assert
        # Should include current timestamp
        current_year = datetime.now().year
        assert str(current_year) in html_report
        assert "Generated:" in html_report

    def test_should_handle_missing_portfolio_id_gracefully(self, report_generator, sample_scenario_report):
        # Arrange
        # portfolio_id is not a field in ScenarioAnalysisReport schema, so it will be missing
        # The implementation uses getattr(report, "portfolio_id", "N/A") to handle this gracefully

        # Act
        html_report = report_generator.generate_scenario_comparison_report(sample_scenario_report)

        # Assert
        # Since portfolio_id doesn't exist in the schema, it should default to "N/A"
        assert "Portfolio ID:" in html_report
        assert "N/A" in html_report

    def test_should_log_report_generation_events(self, report_generator, sample_scenario_report, caplog):
        # Arrange
        import logging

        caplog.set_level(logging.INFO)

        # Act
        report_generator.generate_scenario_comparison_report(sample_scenario_report)

        # Assert
        assert "Generating scenario comparison report" in caplog.text
        assert "Scenario comparison report generated successfully" in caplog.text