"""Unit tests for Portfolio Holdings HTML Generator."""

from datetime import datetime

import pytest

from finwiz.schemas.common import RiskAssessmentStandardized
from finwiz.schemas.portfolio_review import (
    Alternative,
    APlusOpportunitySection,
    HoldingDecision,
    PortfolioReview,
    PositionSizeRecommendation,
    PriceTargets,
)
from finwiz.tools.portfolio_holdings_html_generator import (
    PortfolioHoldingsHTMLGenerator,
    generate_portfolio_holdings_report,
)


class TestPortfolioHoldingsHTMLGenerator:
    """Test suite for PortfolioHoldingsHTMLGenerator."""

    @pytest.fixture
    def sample_portfolio_review(self):
        """Create sample portfolio review for testing."""
        # Create sample holdings
        holdings = [
            HoldingDecision(
                asset_class="stock",
                name="Apple Inc.",
                ticker="AAPL",
                currency="USD",
                decision="KEEP",
                composite_score=0.85,
                grade="A+",
                grade_description="Excellent investment",
                recommended_action="Continue holding",
                risk=RiskAssessmentStandardized(
                    score=2.5,
                    level="Low",
                    risk_factors=["Market volatility"],
                ),
                rationale_bullets=["Strong fundamentals", "Market leader"],
                citations=["Yahoo Finance", "SEC 10-K"],
                price_targets=PriceTargets(
                    current_price=150.0,
                    currency="USD",
                    fair_value_estimate=180.0,
                    buy_target_primary=140.0,
                    sell_target_primary=200.0,
                    stop_loss_level=130.0,
                    buy_rationale="Good entry point",
                    sell_rationale="Take profits",
                    calculation_method="DCF",
                    confidence_level=0.8,
                    data_as_of=datetime.now(),
                    data_sources=["Yahoo Finance"],
                ),
                position_sizing=PositionSizeRecommendation(
                    current_size_pct=5.0,
                    recommended_size_pct=7.0,
                    sizing_action="add",
                    sizing_rationale="Underweight position",
                    risk_contribution=3.0,
                    correlation_with_portfolio=0.5,
                ),
                alternatives=[],
            ),
            HoldingDecision(
                asset_class="stock",
                name="IBM Corporation",
                ticker="IBM",
                currency="USD",
                decision="SELL",
                composite_score=0.55,
                grade="D",
                grade_description="Poor investment",
                recommended_action="Consider selling",
                risk=RiskAssessmentStandardized(
                    score=4.0,
                    level="High",
                    risk_factors=["Declining revenue"],
                ),
                rationale_bullets=["Weak fundamentals", "Declining market share"],
                citations=["Yahoo Finance"],
                alternatives=[
                    Alternative(
                        ticker="MSFT",
                        name="Microsoft Corporation",
                        asset_class="stock",
                        composite_score=0.90,
                        grade="A+",
                        grade_description="Excellent alternative",
                        recommended_action="Strong buy",
                        risk_score_standardized=2.0,
                        is_a_plus_candidate=True,
                        transition_strategy="Gradual swap over 2 months",
                        swap_timing="gradual",
                    )
                ],
            ),
        ]

        # Create portfolio review
        return PortfolioReview(
            as_of=datetime.now(),
            base_currency="CHF",
            holdings=holdings,
            current_a_plus_holdings_count=1,
            potential_a_plus_holdings_count=2,
            a_plus_opportunities=APlusOpportunitySection(
                total_opportunities_found=1,
                high_priority_opportunities=1,
                expected_portfolio_grade_improvement=0.15,
                top_recommendations=["MSFT"],
            ),
        )

    @pytest.fixture
    def generator(self, tmp_path):
        """Create generator instance with temp directory."""
        return PortfolioHoldingsHTMLGenerator(output_dir=str(tmp_path))

    def test_should_generate_html_report_when_valid_portfolio_provided(self, generator, sample_portfolio_review):
        """Test HTML report generation with valid portfolio."""
        # Act
        html_content = generator.generate_report(sample_portfolio_review)

        # Assert
        assert html_content is not None
        assert "<!DOCTYPE html>" in html_content
        assert 'lang="fr"' in html_content
        assert 'charset="UTF-8"' in html_content
        assert "Analyse de Portefeuille FinWiz" in html_content
        assert "AAPL" in html_content
        assert "IBM" in html_content

    def test_should_include_dashboard_metrics_when_generating_report(self, generator, sample_portfolio_review):
        """Test that dashboard metrics are included."""
        # Act
        html_content = generator.generate_report(sample_portfolio_review)

        # Assert
        assert "Tableau de Bord du Portefeuille" in html_content
        assert "Total des Positions" in html_content
        assert "Positions A+" in html_content
        assert "Score Moyen" in html_content

    def test_should_include_holdings_table_when_generating_report(self, generator, sample_portfolio_review):
        """Test that holdings table is included."""
        # Act
        html_content = generator.generate_report(sample_portfolio_review)

        # Assert
        assert "Analyse Détaillée des Positions" in html_content
        assert "holdings-table" in html_content
        assert "Apple Inc." in html_content
        assert "IBM Corporation" in html_content

    def test_should_include_price_targets_when_available(self, generator, sample_portfolio_review):
        """Test that price targets are displayed."""
        # Act
        html_content = generator.generate_report(sample_portfolio_review)

        # Assert
        assert "Objectifs de Prix" in html_content
        assert "Prix actuel" in html_content
        assert "150.00" in html_content  # Current price
        assert "180.00" in html_content  # Fair value

    def test_should_include_alternatives_when_available(self, generator, sample_portfolio_review):
        """Test that alternatives are displayed."""
        # Act
        html_content = generator.generate_report(sample_portfolio_review)

        # Assert
        assert "Alternatives Recommandées" in html_content
        assert "MSFT" in html_content
        assert "Microsoft Corporation" in html_content

    def test_should_include_aplus_roadmap_when_opportunities_exist(self, generator, sample_portfolio_review):
        """Test that A+ roadmap is included."""
        # Act
        html_content = generator.generate_report(sample_portfolio_review)

        # Assert
        assert "Feuille de Route d'Amélioration A+" in html_content
        assert "opportunités A+ identifiées" in html_content

    def test_should_save_report_to_file_when_requested(self, generator, sample_portfolio_review, tmp_path):
        """Test saving report to file."""
        # Act
        output_path = generator.save_report(sample_portfolio_review)

        # Assert
        assert output_path.exists()
        assert output_path.name == "portfolio_review_fr.html"
        content = output_path.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content

    def test_should_use_color_coded_grades_when_displaying_holdings(self, generator, sample_portfolio_review):
        """Test that grades are color-coded."""
        # Act
        html_content = generator.generate_report(sample_portfolio_review)

        # Assert
        assert "#27ae60" in html_content  # A+ color (green)
        assert "#e74c3c" in html_content  # D color (red)

    def test_should_include_emojis_when_generating_report(self, generator, sample_portfolio_review):
        """Test that emojis are included for visual appeal."""
        # Act
        html_content = generator.generate_report(sample_portfolio_review)

        # Assert
        assert "📊" in html_content
        assert "📈" in html_content
        assert "💰" in html_content
        assert "✅" in html_content
        assert "❌" in html_content

    def test_should_be_print_friendly_when_generating_report(self, generator, sample_portfolio_review):
        """Test that report includes print-friendly CSS."""
        # Act
        html_content = generator.generate_report(sample_portfolio_review)

        # Assert
        assert "@media print" in html_content

    def test_should_be_responsive_when_generating_report(self, generator, sample_portfolio_review):
        """Test that report includes responsive CSS."""
        # Act
        html_content = generator.generate_report(sample_portfolio_review)

        # Assert
        assert "@media (max-width: 768px)" in html_content

    def test_should_handle_empty_portfolio_when_generating_report(self, generator):
        """Test handling of empty portfolio."""
        # Arrange
        empty_portfolio = PortfolioReview(
            as_of=datetime.now(),
            base_currency="CHF",
            holdings=[],
        )

        # Act
        html_content = generator.generate_report(empty_portfolio)

        # Assert
        assert html_content is not None
        assert "<!DOCTYPE html>" in html_content
        assert "0" in html_content  # Should show 0 holdings

    def test_convenience_function_should_generate_and_save_report(self, tmp_path, sample_portfolio_review):
        """Test convenience function for generating report."""
        # Act
        output_path = generate_portfolio_holdings_report(
            portfolio_review=sample_portfolio_review,
            output_dir=str(tmp_path),
        )

        # Assert
        assert output_path.exists()
        assert output_path.name == "portfolio_review_fr.html"
