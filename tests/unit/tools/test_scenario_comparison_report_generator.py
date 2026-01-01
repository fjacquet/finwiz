"""
Unit tests for scenario comparison report generator.

Tests the generation of HTML reports for scenario analysis results
including side-by-side comparisons and visualizations.
"""

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

    def test_should_handle_no_risk_warnings_gracefully(self, report_generator, sample_scenario_report):
        # Arrange
        sample_scenario_report.risk_warnings = []

        # Act
        html_report = report_generator.generate_scenario_comparison_report(sample_scenario_report)

        # Assert
        assert isinstance(html_report, str)
        assert "Risk Warnings" not in html_report  # Should not include empty section

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
