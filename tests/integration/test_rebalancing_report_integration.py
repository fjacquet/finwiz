"""
Integration tests for rebalancing report generation.

Tests the complete workflow from rebalancing result to HTML report generation
with various portfolio scenarios and configurations.
"""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

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


class TestRebalancingReportIntegration:
    """Integration tests for rebalancing report generation."""

    @pytest.fixture
    def comprehensive_rebalancing_result(self) -> RebalancingResult:
        """Create a comprehensive rebalancing result for integration testing."""
        current_portfolio = PortfolioAnalysis(
            total_value=250000.0,
            weightings={"AAPL": 0.35, "GOOGL": 0.25, "MSFT": 0.20, "TSLA": 0.15, "NVDA": 0.05},
            deviations_from_target={"AAPL": 0.05, "GOOGL": -0.08, "MSFT": 0.03, "TSLA": 0.10, "NVDA": -0.10},
            positions_needing_rebalancing=["AAPL", "GOOGL", "TSLA", "NVDA"],
            risk_metrics={"volatility": 0.18, "sharpe_ratio": 1.15, "max_drawdown": 0.12, "beta": 1.05},
        )

        projected_portfolio = PortfolioAnalysis(
            total_value=250000.0,
            weightings={"AAPL": 0.30, "GOOGL": 0.33, "MSFT": 0.17, "TSLA": 0.05, "NVDA": 0.15},
            deviations_from_target={"AAPL": 0.0, "GOOGL": 0.0, "MSFT": 0.0, "TSLA": 0.0, "NVDA": 0.0},
            positions_needing_rebalancing=[],
            risk_metrics={"volatility": 0.16, "sharpe_ratio": 1.25, "max_drawdown": 0.10, "beta": 0.98},
        )

        trade_recommendations = [
            TradeRecommendation(
                symbol="AAPL",
                action=TradeAction.SELL,
                quantity=83,
                current_price=150.0,
                trade_value=12450.0,
                estimated_commission=12.45,
                estimated_spread_cost=6.23,
                total_estimated_cost=18.68,
                current_weight=0.35,
                target_weight=0.30,
                weight_deviation=0.05,
                projected_weight_after_trade=0.30,
                priority=1,
                urgency=UrgencyLevel.HIGH,
                rationale="Reduce overweight position to target allocation and improve diversification",
            ),
            TradeRecommendation(
                symbol="GOOGL",
                action=TradeAction.BUY,
                quantity=8,
                current_price=2500.0,
                trade_value=20000.0,
                estimated_commission=20.00,
                estimated_spread_cost=10.00,
                total_estimated_cost=30.00,
                current_weight=0.25,
                target_weight=0.33,
                weight_deviation=-0.08,
                projected_weight_after_trade=0.33,
                priority=2,
                urgency=UrgencyLevel.MEDIUM,
                rationale="Increase underweight position to target allocation",
            ),
            TradeRecommendation(
                symbol="TSLA",
                action=TradeAction.SELL,
                quantity=125,
                current_price=200.0,
                trade_value=25000.0,
                estimated_commission=25.00,
                estimated_spread_cost=12.50,
                total_estimated_cost=37.50,
                current_weight=0.15,
                target_weight=0.05,
                weight_deviation=0.10,
                projected_weight_after_trade=0.05,
                priority=3,
                urgency=UrgencyLevel.CRITICAL,
                rationale="Significantly reduce overweight position due to high volatility and concentration risk",
                market_impact_warning="Large trade size may impact market price",
            ),
            TradeRecommendation(
                symbol="NVDA",
                action=TradeAction.BUY,
                quantity=28,
                current_price=900.0,
                trade_value=25200.0,
                estimated_commission=25.20,
                estimated_spread_cost=12.60,
                total_estimated_cost=37.80,
                current_weight=0.05,
                target_weight=0.15,
                weight_deviation=-0.10,
                projected_weight_after_trade=0.15,
                priority=4,
                urgency=UrgencyLevel.LOW,
                rationale="Increase underweight position to capture AI growth opportunities",
            ),
        ]

        cost_analysis = CostAnalysis(
            total_transaction_costs=123.98,
            commission_costs=82.65,
            spread_costs=41.33,
            market_impact_costs=0.0,
            cost_as_percentage=0.050,
            break_even_days=45,
        )

        execution_summary = ExecutionSummary(
            total_trades_required=4,
            positions_requiring_action=4,
            positions_within_tolerance=1,
            estimated_execution_time="15-20 minutes",
            capital_required=12750.0,
        )

        alternative_scenarios = [
            AlternativeScenario(
                scenario_name="Conservative Rebalancing",
                modified_parameters={"global_tolerance": 0.10, "rebalancing_method": "MINIMIZE_TRADES"},
                projected_outcome="Fewer trades with wider tolerance bands, lower transaction costs",
                cost_difference=-45.50,
                risk_difference=0.15,
            ),
            AlternativeScenario(
                scenario_name="Tax-Efficient Rebalancing",
                modified_parameters={"rebalancing_method": "TAX_EFFICIENT", "min_trade_size": 1000.0},
                projected_outcome="Minimize tax implications by avoiding short-term capital gains",
                cost_difference=25.75,
                risk_difference=-0.05,
            ),
            AlternativeScenario(
                scenario_name="Gradual Rebalancing",
                modified_parameters={"capital": 5000.0, "rebalancing_method": "MINIMIZE_COSTS"},
                projected_outcome="Partial rebalancing with available capital, spread over multiple periods",
                cost_difference=-78.25,
                risk_difference=0.25,
            ),
        ]

        return RebalancingResult(
            analysis_timestamp=datetime.now(),
            portfolio_id="integration_test_portfolio",
            current_portfolio=current_portfolio,
            trade_recommendations=trade_recommendations,
            projected_portfolio=projected_portfolio,
            cost_analysis=cost_analysis,
            current_risk_score=7.2,
            projected_risk_score=6.1,
            risk_improvement=1.1,
            execution_summary=execution_summary,
            alternative_scenarios=alternative_scenarios,
            overall_recommendation=RebalancingRecommendation.REBALANCE_NOW,
            next_review_date=datetime.now() + timedelta(days=30),
        )

    def test_should_generate_complete_interactive_report(self, comprehensive_rebalancing_result):
        """Test generation of complete interactive rebalancing report."""
        # Arrange
        generator = RebalancingReportGenerator()

        # Act
        html_report = generator.generate_rebalancing_report(
            comprehensive_rebalancing_result,
            title="Comprehensive Portfolio Rebalancing Analysis",
            language="en",
            include_interactive=True,
        )

        # Assert
        # Check report structure
        assert "Comprehensive Portfolio Rebalancing Analysis" in html_report
        assert "Executive Summary" in html_report
        assert "Current Portfolio Analysis" in html_report
        assert "Trade Recommendations" in html_report
        assert "Projected Portfolio After Rebalancing" in html_report
        assert "Cost Analysis" in html_report
        assert "Risk Analysis" in html_report
        assert "Alternative Scenarios" in html_report
        assert "Execution Summary" in html_report

        # Check specific data points
        assert "$250,000.00" in html_report  # Portfolio value
        assert "4" in html_report  # Number of trades
        assert "$123.98" in html_report  # Total costs
        assert "AAPL" in html_report and "SELL" in html_report
        assert "GOOGL" in html_report and "BUY" in html_report
        assert "TSLA" in html_report and "CRITICAL" in html_report
        assert "NVDA" in html_report

        # Check interactive elements
        assert "execute-btn" in html_report
        assert "executeTradeDialog" in html_report
        assert "scenario-card" in html_report

        # Check risk improvement
        assert "+1.1" in html_report or "1.1" in html_report

        # Check alternative scenarios
        assert "Conservative Rebalancing" in html_report
        assert "Tax-Efficient Rebalancing" in html_report
        assert "Gradual Rebalancing" in html_report

    def test_should_generate_french_report_with_all_sections(self, comprehensive_rebalancing_result):
        """Test generation of French language report with all sections."""
        # Arrange
        generator = RebalancingReportGenerator()

        # Act
        html_report = generator.generate_rebalancing_report(
            comprehensive_rebalancing_result,
            title="Analyse Complète de Rééquilibrage de Portefeuille",
            language="fr",
            include_interactive=True,
        )

        # Assert
        assert 'lang="fr"' in html_report
        assert "Analyse Complète de Rééquilibrage de Portefeuille" in html_report
        assert "Résumé Exécutif" in html_report
        assert "Analyse du Portefeuille Actuel" in html_report
        assert "Recommandations de Trading" in html_report
        assert "Analyse des Coûts" in html_report
        assert "Analyse des Risques" in html_report
        assert "Scénarios Alternatifs" in html_report
        assert "Résumé d'Exécution" in html_report

        # Check French-specific content
        assert "Transactions Requises" in html_report
        assert "Coûts Estimés" in html_report
        assert "Amélioration du Risque" in html_report
        assert "Exécuter" in html_report  # Execute button in French

    def test_should_save_report_to_file_successfully(self, comprehensive_rebalancing_result):
        """Test saving generated report to file."""
        # Arrange
        generator = RebalancingReportGenerator()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "rebalancing_report.html"

            # Act
            html_report = generator.generate_rebalancing_report(comprehensive_rebalancing_result)
            generator.save_report(html_report, str(output_path))

            # Assert
            assert output_path.exists()

            # Read and verify content
            saved_content = output_path.read_text(encoding="utf-8")
            assert "Portfolio Rebalancing Analysis" in saved_content
            assert "Executive Summary" in saved_content
            assert "$250,000.00" in saved_content

    def test_should_export_pdf_placeholder_successfully(self, comprehensive_rebalancing_result):
        """Test PDF export placeholder functionality."""
        # Arrange
        generator = RebalancingReportGenerator()

        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "rebalancing_report.pdf"

            # Act
            html_report = generator.generate_rebalancing_report(comprehensive_rebalancing_result)
            generator.export_to_pdf(html_report, str(pdf_path))

            # Assert
            # Should create HTML file ready for PDF conversion
            html_path = Path(temp_dir) / "rebalancing_report.html"
            assert html_path.exists()

            # Check PDF conversion note is included
            saved_content = html_path.read_text(encoding="utf-8")
            assert "PDF Export Note" in saved_content
            assert "weasyprint" in saved_content

    def test_should_handle_no_action_scenario_gracefully(self):
        """Test handling of scenario where no rebalancing is needed."""
        # Arrange
        generator = RebalancingReportGenerator()

        # Create no-action scenario
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

        no_action_result = RebalancingResult(
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

        # Act
        html_report = generator.generate_rebalancing_report(no_action_result)

        # Assert
        assert "No action required" in html_report or "well balanced" in html_report
        assert "no-trades" in html_report
        assert "$0.00" in html_report  # Zero costs

    def test_should_validate_generated_html_structure(self, comprehensive_rebalancing_result):
        """Test that generated HTML has proper structure and compliance."""
        # Arrange
        generator = RebalancingReportGenerator()

        # Act
        html_report = generator.generate_rebalancing_report(comprehensive_rebalancing_result)
        validation_result = generator.validate_html_output(html_report)

        # Assert
        assert validation_result["has_utf8"]
        assert validation_result["has_emojis"]

        # Check HTML structure
        assert html_report.startswith("<!DOCTYPE html>")
        assert "<html" in html_report
        assert "<head>" in html_report
        assert "<body>" in html_report
        assert "</html>" in html_report

        # Check CSS and JavaScript inclusion
        assert "<style>" in html_report
        assert "<script>" in html_report
        assert "executeTradeDialog" in html_report

    def test_should_handle_large_portfolio_with_many_positions(self):
        """Test handling of large portfolio with many positions."""
        # Arrange
        generator = RebalancingReportGenerator()

        # Create large portfolio (20 positions)
        symbols = [f"STOCK{i:02d}" for i in range(1, 21)]
        weightings = {symbol: 0.05 for symbol in symbols}
        deviations = {symbol: 0.01 * (i % 10 - 5) for i, symbol in enumerate(symbols)}

        # Create some trade recommendations
        trades = []
        for i, symbol in enumerate(symbols[:5]):  # First 5 need rebalancing
            action = TradeAction.BUY if deviations[symbol] < 0 else TradeAction.SELL
            trades.append(
                TradeRecommendation(
                    symbol=symbol,
                    action=action,
                    quantity=100,
                    current_price=50.0,
                    trade_value=5000.0,
                    estimated_commission=5.0,
                    estimated_spread_cost=2.5,
                    total_estimated_cost=7.5,
                    current_weight=weightings[symbol],
                    target_weight=0.05,
                    weight_deviation=deviations[symbol],
                    projected_weight_after_trade=0.05,
                    priority=i + 1,
                    urgency=UrgencyLevel.MEDIUM,
                    rationale=f"Rebalance {symbol} to target allocation",
                )
            )

        large_portfolio = PortfolioAnalysis(
            total_value=1000000.0,
            weightings=weightings,
            deviations_from_target=deviations,
            positions_needing_rebalancing=symbols[:5],
            risk_metrics={"volatility": 0.12, "sharpe_ratio": 1.4},
        )

        cost_analysis = CostAnalysis(total_transaction_costs=37.5, commission_costs=25.0, spread_costs=12.5, cost_as_percentage=0.004)

        execution_summary = ExecutionSummary(
            total_trades_required=5,
            positions_requiring_action=5,
            positions_within_tolerance=15,
            estimated_execution_time="10-15 minutes",
            capital_required=0.0,
        )

        large_result = RebalancingResult(
            current_portfolio=large_portfolio,
            trade_recommendations=trades,
            projected_portfolio=large_portfolio,
            cost_analysis=cost_analysis,
            current_risk_score=5.5,
            projected_risk_score=5.0,
            risk_improvement=0.5,
            execution_summary=execution_summary,
            overall_recommendation=RebalancingRecommendation.REBALANCE_SOON,
            next_review_date=datetime.now() + timedelta(days=30),
        )

        # Act
        html_report = generator.generate_rebalancing_report(large_result)

        # Assert
        assert "$1,000,000.00" in html_report
        assert "STOCK01" in html_report
        assert "STOCK05" in html_report
        assert "5" in html_report  # Number of trades
        assert len(html_report) > 10000  # Should be a substantial report

    def test_should_handle_high_urgency_critical_trades(self, comprehensive_rebalancing_result):
        """Test proper handling and display of critical urgency trades."""
        # Arrange
        generator = RebalancingReportGenerator()

        # Act
        html_report = generator.generate_rebalancing_report(comprehensive_rebalancing_result)

        # Assert
        # Check that TSLA trade (marked as CRITICAL) is properly highlighted
        assert "CRITICAL" in html_report
        assert "urgency-critical" in html_report
        assert "Large trade size may impact market price" in html_report

        # Check priority ordering (TSLA should be priority 3)
        tsla_index = html_report.find("TSLA")
        critical_index = html_report.find("CRITICAL")
        assert tsla_index < critical_index  # TSLA should appear before CRITICAL in the same row

    def test_should_generate_report_with_custom_template_path(self, comprehensive_rebalancing_result):
        """Test report generation with custom template path."""
        # Arrange
        custom_template_path = "src/finwiz/templates/rebalancing_template.html"
        generator = RebalancingReportGenerator(custom_template_path)

        # Act
        html_report = generator.generate_rebalancing_report(comprehensive_rebalancing_result)

        # Assert
        assert generator.template_path == custom_template_path
        assert "Portfolio Rebalancing Analysis" in html_report
        assert len(html_report) > 5000  # Should be a substantial report
