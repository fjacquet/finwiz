"""
Tests for Investment Discovery schemas integration with grading system.

This module tests the A+ discovery schemas to ensure proper integration
with the existing FinWiz grading system and validation.
"""

from pytest import approx
from datetime import datetime

import pytest

from finwiz.schemas.common import RiskAssessmentStandardized
from finwiz.schemas.investment_discovery import (
    APlusAnalysis,
    APlusCriteria,
    APlusDiscoveryResult,
    InvestmentCandidate,
    MarketRegime,
    OptimizationResult,
    PortfolioImprovement,
)


class TestInvestmentCandidate:
    """Test InvestmentCandidate schema with grading system integration."""

    def test_should_create_valid_investment_candidate_with_grade(self):
        """Test creating investment candidate with proper grade integration."""
        # Arrange & Act
        candidate = InvestmentCandidate(
            symbol="AAPL",
            name="Apple Inc.",
            asset_type="stock",
            current_price=150.0,
            market_cap=2.5e12,
            preliminary_score=0.96,
            final_score=0.97,
            grade="A+",
            grade_description="Excellent - Champion du portefeuille",
            recommended_action="Augmentez l'allocation si possible",
            data_source="Yahoo Finance",
            risk_assessment=RiskAssessmentStandardized(score=2.5, level="Medium", risk_factors=["Market volatility", "Tech sector concentration"]),
        )

        # Assert
        assert candidate.symbol == "AAPL"
        assert candidate.grade == "A+"
        assert candidate.final_score >= 0.95  # A+ candidate check
        assert candidate.risk_assessment.score == approx(2.5)
        assert candidate.risk_assessment.level == "Medium"

    def test_should_validate_grade_enum(self):
        """Test that grade field validates against Grade enum."""
        # Arrange & Act & Assert
        with pytest.raises(ValueError):
            InvestmentCandidate(
                symbol="TEST",
                name="Test Company",
                asset_type="stock",
                current_price=100.0,
                preliminary_score=0.8,
                final_score=0.8,
                grade="INVALID",  # Invalid grade
                grade_description="Test",
                recommended_action="Test",
                data_source="Test",
            )

    def test_should_handle_optional_fields(self):
        """Test that optional fields work correctly."""
        # Arrange & Act
        candidate = InvestmentCandidate(
            symbol="BTC-USD",
            name="Bitcoin",
            asset_type="crypto",
            current_price=45000.0,
            preliminary_score=0.85,
            final_score=0.87,
            grade="A",
            grade_description="Très bon - Investissement de qualité",
            recommended_action="Maintenez et continuez le DCA",
            data_source="CoinMarketCap",
            # market_cap and risk_assessment are optional
        )

        # Assert
        assert candidate.market_cap is None
        assert candidate.risk_assessment is None
        assert candidate.grade == "A"


class TestMarketRegime:
    """Test MarketRegime schema."""

    def test_should_create_valid_market_regime(self):
        """Test creating valid market regime assessment."""
        # Arrange & Act
        regime = MarketRegime(regime_type="bull", vix_level=15.5, inflation_rate=3.2, interest_rate_trend="rising", market_stress_level="low")

        # Assert
        assert regime.regime_type == "bull"
        assert regime.vix_level == approx(15.5)
        assert regime.market_stress_level == "low"
        assert isinstance(regime.assessment_date, datetime)


class TestAPlusCriteria:
    """Test APlusCriteria schema."""

    def test_should_create_default_criteria(self):
        """Test creating criteria with default values."""
        # Arrange & Act
        criteria = APlusCriteria()

        # Assert
        assert criteria.etf_max_expense_ratio == approx(0.15)
        assert criteria.stock_min_roe == approx(20.0)  # Percentage format: 20 = 20%
        assert criteria.crypto_min_market_cap == 10e9
        assert not criteria.regime_adjusted

    def test_should_create_custom_criteria(self):
        """Test creating criteria with custom values."""
        # Arrange & Act
        criteria = APlusCriteria(
            etf_max_expense_ratio=0.10,
            stock_min_roe=0.25,
            regime_adjusted=True,
            adjustment_rationale="Tightened for bear market conditions",
        )

        # Assert
        assert criteria.etf_max_expense_ratio == approx(0.10)
        assert criteria.stock_min_roe == approx(0.25)
        assert criteria.regime_adjusted
        assert "bear market" in criteria.adjustment_rationale


class TestAPlusAnalysis:
    """Test APlusAnalysis schema."""

    def test_should_create_complete_analysis(self):
        """Test creating complete A+ analysis."""
        # Arrange
        candidate = InvestmentCandidate(
            symbol="SPY",
            name="SPDR S&P 500 ETF",
            asset_type="etf",
            current_price=400.0,
            preliminary_score=0.96,
            final_score=0.97,
            grade="A+",
            grade_description="Excellent - Champion du portefeuille",
            recommended_action="Augmentez l'allocation si possible",
            data_source="Yahoo Finance",
        )

        market_regime = MarketRegime(regime_type="bull", vix_level=18.0, inflation_rate=2.8, interest_rate_trend="stable", market_stress_level="low")

        criteria = APlusCriteria()

        # Act
        analysis = APlusAnalysis(
            candidate=candidate,
            fundamental_score=0.95,
            technical_score=0.92,
            quality_score=0.98,
            risk_score=0.88,
            composite_score=0.97,
            confidence_level=0.85,
            is_a_plus_candidate=True,
            rationale=["Ultra-low expense ratio", "Excellent tracking", "High liquidity"],
            key_metrics={"expense_ratio": 0.09, "aum": 400e9},
            competitive_advantages=["Market leader", "Broad diversification"],
            risk_factors=["Market risk", "Interest rate sensitivity"],
            market_context=market_regime,
            criteria_used=criteria,
        )

        # Assert
        assert analysis.candidate.symbol == "SPY"
        assert analysis.composite_score == approx(0.97)
        assert analysis.is_a_plus_candidate
        assert analysis.confidence_level == approx(0.85)
        assert len(analysis.rationale) == 3
        assert analysis.market_context.regime_type == "bull"


class TestPortfolioImprovement:
    """Test PortfolioImprovement schema with grading integration."""

    def test_should_create_replacement_improvement(self):
        """Test creating portfolio improvement for replacement."""
        # Arrange & Act
        improvement = PortfolioImprovement(
            current_holding="VTI",
            current_grade="B+",
            recommended_investment="SPY",
            recommended_grade="A+",
            improvement_type="replacement",
            expected_grade_improvement=0.15,
            grade_improvement_description="Upgrade from B+ to A+ with lower costs",
            allocation_percentage=25.0,
            implementation_priority="high",
            rationale="Lower expense ratio and better tracking",
            risk_impact=RiskAssessmentStandardized(score=2.0, level="Low", risk_factors=["Minimal tracking difference"]),
            cost_analysis={"transaction_cost": 0.0, "tax_impact": 150.0},
            expected_annual_benefit=0.05,
        )

        # Assert
        assert improvement.current_grade == "B+"
        assert improvement.recommended_grade == "A+"
        assert improvement.improvement_type == "replacement"
        assert improvement.expected_grade_improvement == approx(0.15)
        assert improvement.risk_impact.level == "Low"


class TestAPlusDiscoveryResult:
    """Test APlusDiscoveryResult schema."""

    def test_should_create_complete_discovery_result(self):
        """Test creating complete discovery result."""
        # Arrange
        criteria = APlusCriteria()
        market_regime = MarketRegime(regime_type="bull", vix_level=16.0, inflation_rate=3.0, interest_rate_trend="stable", market_stress_level="low")

        candidate = InvestmentCandidate(
            symbol="VTI",
            name="Vanguard Total Stock Market ETF",
            asset_type="etf",
            current_price=220.0,
            preliminary_score=0.96,
            final_score=0.97,
            grade="A+",
            grade_description="Excellent - Champion du portefeuille",
            recommended_action="Augmentez l'allocation si possible",
            data_source="Yahoo Finance",
        )

        analysis = APlusAnalysis(
            candidate=candidate,
            fundamental_score=0.95,
            technical_score=0.92,
            quality_score=0.98,
            risk_score=0.88,
            composite_score=0.97,
            confidence_level=0.85,
            is_a_plus_candidate=True,
            rationale=["Ultra-low expense ratio", "Excellent diversification"],
        )

        # Act
        result = APlusDiscoveryResult(
            asset_type="etf",
            total_screened=500,
            candidates_found=12,
            discovery_criteria=criteria,
            market_context=market_regime,
            a_plus_candidates=[analysis],
            average_score=0.96,
            grade_distribution={"A+": 12, "A": 25, "B+": 45},
            a_plus_percentage=2.4,
            ucits_compliant_count=8,
            ucits_compliant_symbols=["VTI", "SPY", "IVV"],
            top_recommendations=["VTI", "SPY", "IVV"],
            implementation_notes=["Consider tax implications", "Gradual implementation"],
            high_confidence_count=10,
            screening_efficiency=15.2,
        )

        # Assert
        assert result.asset_type == "etf"
        assert result.total_screened == 500
        assert result.candidates_found == 12
        assert result.a_plus_percentage == approx(2.4)
        assert len(result.a_plus_candidates) == 1
        assert result.grade_distribution["A+"] == 12
        assert result.high_confidence_count == 10
        assert isinstance(result.discovery_timestamp, datetime)


class TestOptimizationResult:
    """Test OptimizationResult schema with grading integration."""

    def test_should_create_optimization_result_with_grades(self):
        """Test creating optimization result with proper grade integration."""
        # Arrange
        improvement = PortfolioImprovement(
            recommended_investment="SPY",
            recommended_grade="A+",
            improvement_type="addition",
            expected_grade_improvement=0.10,
            grade_improvement_description="Adding A+ ETF to portfolio",
            allocation_percentage=20.0,
            implementation_priority="high",
            rationale="Excellent diversification and low costs",
            risk_impact=RiskAssessmentStandardized(score=2.0, level="Low", risk_factors=["Market risk only"]),
        )

        # Act
        result = OptimizationResult(
            current_portfolio_grade="B+",
            optimized_portfolio_grade="A",
            grade_improvement=0.12,
            grade_improvement_description="Portfolio upgraded from B+ to A with A+ additions",
            improvements=[improvement],
            current_metrics={"average_score": 0.78, "risk_score": 3.2},
            projected_metrics={"average_score": 0.85, "risk_score": 3.0},
            risk_impact_analysis={"overall_risk": "slightly reduced"},
            diversification_impact={"sectors": "improved"},
            implementation_timeline={"phase1": "immediate", "phase2": "3 months"},
            total_transaction_costs=25.0,
            expected_annual_benefit=0.08,
            constraints_met=["Risk tolerance", "Diversification requirements"],
            implementation_notes=["Tax-efficient implementation", "Dollar-cost averaging"],
        )

        # Assert
        assert result.current_portfolio_grade == "B+"
        assert result.optimized_portfolio_grade == "A"
        assert result.grade_improvement == approx(0.12)
        assert len(result.improvements) == 1
        assert result.improvements[0].recommended_grade == "A+"
        assert result.expected_annual_benefit == approx(0.08)


class TestSchemaIntegration:
    """Test integration between schemas and grading system."""

    def test_should_integrate_with_existing_grading_system(self):
        """Test that schemas properly integrate with existing grading system."""
        # This test verifies that the Grade enum from portfolio_review
        # is properly used in investment discovery schemas

        # Arrange & Act
        candidate = InvestmentCandidate(
            symbol="TEST",
            name="Test Investment",
            asset_type="stock",
            current_price=100.0,
            preliminary_score=0.96,
            final_score=0.97,
            grade="A+",  # This should validate against the Grade enum
            grade_description="Excellent - Champion du portefeuille",
            recommended_action="Augmentez l'allocation si possible",
            data_source="Test",
        )

        improvement = PortfolioImprovement(
            recommended_investment="TEST",
            recommended_grade="A+",  # This should also validate
            improvement_type="addition",
            expected_grade_improvement=0.10,
            grade_improvement_description="Test improvement",
            allocation_percentage=10.0,
            implementation_priority="medium",
            rationale="Test rationale",
            risk_impact=RiskAssessmentStandardized(score=2.0, level="Low", risk_factors=["Test risk"]),
        )

        # Assert
        assert candidate.grade == "A+"
        assert improvement.recommended_grade == "A+"
        # Both should be valid Grade enum values
        assert candidate.grade in ["A+", "A", "B+", "B", "C+", "C", "D", "F"]
        assert improvement.recommended_grade in ["A+", "A", "B+", "B", "C+", "C", "D", "F"]