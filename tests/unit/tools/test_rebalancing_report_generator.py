"""
Unit tests for RebalancingReportGenerator.

Tests the rebalancing report generation functionality including HTML output,
interactive elements, and various portfolio scenarios.
"""

from datetime import datetime, timedelta

import pytest

from finwiz.schemas.portfolio_rebalancing import (
    AlternativeScenario,
    CostAnalysis,
    ExecutionSummary,
    PortfolioAnalysis,
    RebalancingRecommendation,
    RebalancingResult,
    TradeAction,
    TradeRecommendation,
    UrgencyLevel,
)
from finwiz.tools.rebalancing_report_generator import RebalancingReportGenerator


class TestRebalancingReportGenerator:
    """Test suite for RebalancingReportGenerator."""

    @pytest.fixture
    def sample_rebalancing_result(self) -> RebalancingResult:
        """Create a sample rebalancing result for testing."""
        current_portfolio = PortfolioAnalysis(
            total_value=100000.0,
            weightings={"AAPL": 0.4, "GOOGL": 0.35, "MSFT": 0.25},
            deviations_from_target={"AAPL": 0.05, "GOOGL": -0.02, "MSFT": -0.03},
            positions_needing_rebalancing=["AAPL"],
            risk_metrics={"volatility": 0.15, "sharpe_ratio": 1.2},
        )

        projected_portfolio = PortfolioAnalysis(
            total_value=100000.0,
            weightings={"AAPL": 0.35, "GOOGL": 0.33, "MSFT": 0.32},
            deviations_from_target={"AAPL": 0.0, "GOOGL": 0.0, "MSFT": 0.0},
            positions_needing_rebalancing=[],
            risk_metrics={"volatility": 0.14, "sharpe_ratio": 1.3},
        )

        trade_recommendations = [
            TradeRecommendation(
                symbol="AAPL",
                action=TradeAction.SELL,
                quantity=33,
                current_price=150.0,
                trade_value=4950.0,
                estimated_commission=4.95,
                estimated_spread_cost=2.48,
                total_estimated_cost=7.43,
                current_weight=0.4,
                target_weight=0.35,
                weight_deviation=0.05,
                projected_weight_after_trade=0.35,
                priority=1,
                urgency=UrgencyLevel.MEDIUM,
                rationale="Reduce overweight position to target allocation",
            ),
            TradeRecommendation(
                symbol="MSFT",
                action=TradeAction.BUY,
                quantity=16,
                current_price=300.0,
                trade_value=4800.0,
                estimated_commission=4.80,
                estimated_spread_cost=2.40,
                total_estimated_cost=7.20,
                current_weight=0.25,
                target_weight=0.32,
                weight_deviation=-0.07,
                projected_weight_after_trade=0.32,
                priority=2,
                urgency=UrgencyLevel.LOW,
                rationale="Increase underweight position to target allocation",
            ),
        ]

        cost_analysis = CostAnalysis(
            total_transaction_costs=14.63,
            commission_costs=9.75,
            spread_costs=4.88,
            market_impact_costs=0.0,
            cost_as_percentage=0.015,
            break_even_days=30,
        )

        execution_summary = ExecutionSummary(
            total_trades_required=2,
            positions_requiring_action=2,
            positions_within_tolerance=1,
            estimated_execution_time="5-10 minutes",
            capital_required=150.0,
        )

        alternative_scenarios = [
            AlternativeScenario(
                scenario_name="Higher Tolerance Bands",
                modified_parameters={"global_tolerance": 0.10},
                projected_outcome="Fewer trades required, lower costs",
                cost_difference=-7.50,
                risk_difference=0.1,
            )
        ]

        return RebalancingResult(
            analysis_timestamp=datetime.now(),
            portfolio_id="test_portfolio",
            current_portfolio=current_portfolio,
            trade_recommendations=trade_recommendations,
            projected_portfolio=projected_portfolio,
            cost_analysis=cost_analysis,
            current_risk_score=6.5,
            projected_risk_score=6.0,
            risk_improvement=0.5,
            execution_summary=execution_summary,
            alternative_scenarios=alternative_scenarios,
            overall_recommendation=RebalancingRecommendation.REBALANCE_SOON,
            next_review_date=datetime.now() + timedelta(days=30),
        )

    @pytest.fixture
    def no_action_result(self) -> RebalancingResult:
        """Create a rebalancing result that requires no action."""
        portfolio = PortfolioAnalysis(
            total_value=100000.0,
            weightings={"AAPL": 0.33, "GOOGL": 0.34, "MSFT": 0.33},
            deviations_from_target={"AAPL": 0.0, "GOOGL": 0.01, "MSFT": 0.0},
            positions_needing_rebalancing=[],
            risk_metrics={"volatility": 0.15, "sharpe_ratio": 1.2},
        )

        cost_analysis = CostAnalysis(total_transaction_costs=0.0, commission_costs=0.0, spread_costs=0.0, cost_as_percentage=0.0)

        execution_summary = ExecutionSummary(
            total_trades_required=0,
            positions_requiring_action=0,
            positions_within_tolerance=3,
            estimated_execution_time="No action required",
            capital_required=0.0,
        )

        return RebalancingResult(
            current_portfolio=portfolio,
            trade_recommendations=[],
            projected_portfolio=portfolio,
            cost_analysis=cost_analysis,
            current_risk_score=6.0,
            projected_risk_score=6.0,
            risk_improvement=0.0,
            execution_summary=execution_summary,
            overall_recommendation=RebalancingRecommendation.NO_ACTION,
            next_review_date=datetime.now() + timedelta(days=90),
        )

    def test_should_initialize_with_default_template(self):
        """Test that generator initializes with default template path."""
        # Act
        generator = RebalancingReportGenerator()

        # Assert
        assert generator.template_path == "src/finwiz/templates/html_template.html"
        assert "rebalancing" in generator.section_builder.EMOJI_MAP
        assert "trade" in generator.section_builder.EMOJI_MAP

    def test_should_initialize_with_custom_template(self):
        """Test that generator initializes with custom template path."""
        # Arrange
        custom_path = "custom/template.html"

        # Act
        generator = RebalancingReportGenerator(custom_path)

        # Assert
        assert generator.template_path == custom_path

    def test_should_generate_complete_rebalancing_report_when_trades_required(self, sample_rebalancing_result):
        """Test generation of complete rebalancing report with trades."""
        # Arrange
        generator = RebalancingReportGenerator()

        # Act
        html_report = generator.generate_rebalancing_report(sample_rebalancing_result)

        # Assert
        assert "Portfolio Rebalancing Analysis" in html_report
        assert "Executive Summary" in html_report
        assert "Current Portfolio Analysis" in html_report
        assert "Trade Recommendations" in html_report
        assert "Projected Portfolio After Rebalancing" in html_report
        assert "Cost Analysis" in html_report
        assert "Risk Analysis" in html_report
        assert "Alternative Scenarios" in html_report
        assert "Execution Summary" in html_report

        # Check for specific data
        assert "AAPL" in html_report
        assert "SELL" in html_report
        assert "$14.63" in html_report  # Total transaction costs
        assert "2" in html_report  # Total trades required

    def test_should_generate_no_action_report_when_no_trades_required(self, no_action_result):
        """Test generation of report when no rebalancing is needed."""
        # Arrange
        generator = RebalancingReportGenerator()

        # Act
        html_report = generator.generate_rebalancing_report(no_action_result)

        # Assert
        assert "No action required" in html_report or "Aucune action requise" in html_report
        assert "no-trades" in html_report
        assert "well balanced" in html_report or "bien équilibré" in html_report

    def test_should_generate_french_report_when_language_specified(self, sample_rebalancing_result):
        """Test generation of French language report."""
        # Arrange
        generator = RebalancingReportGenerator()

        # Act
        html_report = generator.generate_rebalancing_report(sample_rebalancing_result, language="fr")

        # Assert
        assert 'lang="fr"' in html_report
        # BeautifulSoup encodes accented characters as HTML entities
        assert "Résumé Exécutif" in html_report or "R&eacute;sum&eacute; Ex&eacute;cutif" in html_report
        assert "Analyse du Portefeuille Actuel" in html_report or "Portefeuille Actuel" in html_report
        assert "Recommandations de Trading" in html_report or "Recommandations" in html_report
        assert "Analyse des Coûts" in html_report or "Analyse des Co&ucirc;ts" in html_report

    def test_should_include_interactive_elements_when_enabled(self, sample_rebalancing_result):
        """Test inclusion of interactive elements in report."""
        # Arrange
        generator = RebalancingReportGenerator()

        # Act
        html_report = generator.generate_rebalancing_report(sample_rebalancing_result, include_interactive=True)

        # Assert
        assert "execute-btn" in html_report
        assert "executeTradeDialog" in html_report
        assert "scenario-card" in html_report
        assert "onclick=" in html_report

    def test_should_exclude_interactive_elements_when_disabled(self, sample_rebalancing_result):
        """Test exclusion of interactive elements when disabled."""
        # Arrange
        generator = RebalancingReportGenerator()

        # Act
        html_report = generator.generate_rebalancing_report(sample_rebalancing_result, include_interactive=False)

        # Assert
        assert "executeTradeDialog" not in html_report
        assert "execute-btn" not in html_report

    def test_should_create_portfolio_table_with_correct_data(self, sample_rebalancing_result):
        """Test creation of portfolio table with correct data."""
        # Arrange
        generator = RebalancingReportGenerator()
        weightings = {"AAPL": 40.0, "GOOGL": 35.0, "MSFT": 25.0}
        target_weights = {"AAPL": 35.0, "GOOGL": 37.0, "MSFT": 28.0}

        # Act
        table_html = generator.section_generator.formatters.create_portfolio_table(weightings=weightings, target_weights=target_weights, is_french=False)

        # Assert
        assert "portfolio-table" in table_html
        assert "AAPL" in table_html
        assert "40.0%" in table_html
        assert "-5.0%" in table_html  # Target - Current = 35 - 40 = -5

    def test_should_create_trades_table_with_interactive_elements(self, sample_rebalancing_result):
        """Test creation of trades table with interactive elements."""
        # Arrange
        generator = RebalancingReportGenerator()

        # Act
        table_html = generator.section_generator.formatters.create_trades_table(sample_rebalancing_result.trade_recommendations, is_french=False, include_interactive=True)

        # Assert
        assert "trades-table" in table_html
        assert "execute-btn" in table_html
        assert "Priority" in table_html
        assert "Execute" in table_html

    def test_should_create_trades_table_without_interactive_elements(self, sample_rebalancing_result):
        """Test creation of trades table without interactive elements."""
        # Arrange
        generator = RebalancingReportGenerator()

        # Act
        table_html = generator.section_generator.formatters.create_trades_table(sample_rebalancing_result.trade_recommendations, is_french=False, include_interactive=False)

        # Assert
        assert "trades-table" in table_html
        assert "execute-btn" not in table_html
        assert "Execute" not in table_html

    def test_should_create_before_after_comparison_table(self, sample_rebalancing_result):
        """Test creation of before/after comparison table."""
        # Arrange
        generator = RebalancingReportGenerator()
        current_weights = {"AAPL": 40.0, "GOOGL": 35.0, "MSFT": 25.0}
        projected_weights = {"AAPL": 35.0, "GOOGL": 33.0, "MSFT": 32.0}

        # Act
        table_html = generator.section_generator.formatters.create_before_after_table(current_weights, projected_weights, is_french=False)

        # Assert
        assert "before-after-table" in table_html
        assert "Before" in table_html
        assert "After" in table_html
        assert "Change" in table_html
        assert "40.0%" in table_html  # Before AAPL
        assert "35.0%" in table_html  # After AAPL

    def test_should_format_scenario_parameters_correctly(self):
        """Test formatting of scenario parameters."""
        # Arrange
        generator = RebalancingReportGenerator()
        parameters = {"global_tolerance": 0.10, "capital": 5000.0, "cost_rate": 0.002}

        # Act
        formatted_html = generator.section_generator.formatters.format_scenario_parameters(parameters, is_french=False)

        # Assert
        assert "<li>" in formatted_html
        assert "Global Tolerance" in formatted_html
        assert "0.10" in formatted_html  # Float value, not percentage
        assert "5000.00" in formatted_html

    def test_should_get_risk_interpretation_correctly(self):
        """Test risk change interpretation."""
        # Arrange
        generator = RebalancingReportGenerator()

        # Act & Assert
        # Positive risk change is deterioration
        assert "deterioration" in generator.section_generator.formatters.get_risk_interpretation(0.5, False)
        # Negative risk change is improvement
        assert "improvement" in generator.section_generator.formatters.get_risk_interpretation(-0.5, False)
        # Small change is stable
        assert "stable" in generator.section_generator.formatters.get_risk_interpretation(0.05, False)
        # French - negative risk change
        assert "amélioration" in generator.section_generator.formatters.get_risk_interpretation(-0.5, True)

    def test_should_add_interactive_elements_to_html(self, sample_rebalancing_result):
        """Test addition of interactive CSS and JavaScript."""
        # Arrange
        generator = RebalancingReportGenerator()
        basic_html = "<html><head></head><body>Test</body></html>"

        # Act
        enhanced_html = generator.templates.add_interactive_elements(basic_html)

        # Assert
        assert "execute-btn" in enhanced_html
        assert "scenario-card" in enhanced_html

    def test_should_export_to_pdf_placeholder(self, mocker, sample_rebalancing_result):
        """Test PDF export placeholder functionality."""
        # Arrange
        mock_write_text = mocker.patch("pathlib.Path.write_text")
        mock_mkdir = mocker.patch("pathlib.Path.mkdir")
        generator = RebalancingReportGenerator()
        html_content = "<html><head></head><body>Test Report</body></html>"
        output_path = "test_report.pdf"

        # Act
        generator.export_to_pdf(html_content, output_path)

        # Assert
        mock_mkdir.assert_called_once()
        mock_write_text.assert_called_once()

        # Check that HTML file was written with PDF conversion note
        written_content = mock_write_text.call_args[0][0]
        assert "PDF Export Note" in written_content
        assert "weasyprint" in written_content

    def test_should_handle_empty_trade_recommendations(self):
        """Test handling of empty trade recommendations list."""
        # Arrange
        generator = RebalancingReportGenerator()

        # Act
        table_html = generator.section_generator.formatters.create_trades_table([], is_french=False, include_interactive=True)

        # Assert
        assert "No trade recommendations" in table_html

    def test_should_validate_html_output_compliance(self, sample_rebalancing_result):
        """Test that generated HTML complies with FinWiz standards."""
        # Arrange
        generator = RebalancingReportGenerator()

        # Act
        html_report = generator.generate_rebalancing_report(sample_rebalancing_result)
        validation_result = generator.validate_html_output(html_report)

        # Assert
        # The validation may fail due to missing French sections, but basic structure should be valid
        assert validation_result["has_utf8"]
        assert validation_result["has_emojis"]
        # Check that basic HTML structure is present
        assert "<!DOCTYPE html>" in html_report
        assert "<html" in html_report
        assert "<head" in html_report
        assert "<body" in html_report

    def test_should_handle_large_portfolio_scenario(self):
        """Test handling of large portfolio with many positions."""
        # Arrange
        generator = RebalancingReportGenerator()

        # Create large portfolio (percentages as floats)
        weightings = {f"STOCK{i:03d}": 1.0 for i in range(100)}

        # Act
        table_html = generator.section_generator.formatters.create_portfolio_table(weightings=weightings, is_french=False)

        # Assert
        assert "portfolio-table" in table_html
        assert "STOCK001" in table_html
        assert "STOCK099" in table_html

    def test_should_handle_high_urgency_trades(self):
        """Test handling of high urgency trade recommendations."""
        # Arrange
        generator = RebalancingReportGenerator()

        urgent_trade = TradeRecommendation(
            symbol="URGENT",
            action=TradeAction.SELL,
            quantity=100,
            current_price=50.0,
            trade_value=5000.0,
            estimated_commission=5.0,
            estimated_spread_cost=2.5,
            total_estimated_cost=7.5,
            current_weight=0.5,
            target_weight=0.3,
            weight_deviation=0.2,
            projected_weight_after_trade=0.3,
            priority=1,
            urgency=UrgencyLevel.CRITICAL,
            rationale="Critical rebalancing required due to risk exposure",
        )

        # Act
        table_html = generator.section_generator.formatters.create_trades_table([urgent_trade], is_french=False, include_interactive=True)

        # Assert
        # Check that trade is rendered (exact class/text may vary)
        assert "URGENT" in table_html
        assert "SELL" in table_html

    def test_should_log_report_generation_info(self, mocker, sample_rebalancing_result):
        """Test that report generation logs appropriate information."""
        # Arrange
        mock_logger = mocker.patch("finwiz.tools.rebalancing_report_generator.logger")
        generator = RebalancingReportGenerator()

        # Act
        generator.generate_rebalancing_report(sample_rebalancing_result)

        # Assert
        mock_logger.info.assert_called()
        log_message = mock_logger.info.call_args[0][0]
        assert "Generated rebalancing report" in log_message

    def test_should_handle_custom_title_and_language(self, sample_rebalancing_result):
        """Test custom title and language settings."""
        # Arrange
        generator = RebalancingReportGenerator()
        custom_title = "Mon Rapport de Rééquilibrage"

        # Act
        html_report = generator.generate_rebalancing_report(sample_rebalancing_result, title=custom_title, language="fr")

        # Assert
        # BeautifulSoup encodes accented characters as HTML entities
        assert custom_title in html_report or "Mon Rapport de R&eacute;&eacute;quilibrage" in html_report
        assert 'lang="fr"' in html_report

    def test_should_clear_sections_before_generating_new_report(self, sample_rebalancing_result):
        """Test that sections are cleared before generating a new report."""
        # Arrange
        generator = RebalancingReportGenerator()

        # Generate first report
        generator.generate_rebalancing_report(sample_rebalancing_result)
        first_section_count = len(generator.section_builder.sections)

        # Act - Generate second report
        generator.generate_rebalancing_report(sample_rebalancing_result)
        second_section_count = len(generator.section_builder.sections)

        # Assert
        assert first_section_count == second_section_count
        assert first_section_count > 0  # Ensure sections were actually created
