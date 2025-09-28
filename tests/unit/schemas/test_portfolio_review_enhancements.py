"""
Tests for enhanced portfolio review schemas with A+ investment discovery support.

This module tests the enhanced HoldingDecision and PortfolioReview schemas
that include A+ improvement suggestions and opportunity tracking.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from finwiz.schemas.common import RiskAssessmentStandardized
from finwiz.schemas.portfolio_review import (
    Alternative,
    APlusImprovementSuggestion,
    APlusOpportunitySection,
    HoldingDecision,
    PortfolioReview,
)


class TestAPlusImprovementSuggestion:
    """Test A+ improvement suggestion model."""

    def test_should_create_valid_improvement_suggestion(self):
        """Test creating a valid A+ improvement suggestion."""
        suggestion = APlusImprovementSuggestion(
            improvement_type="replacement",
            recommended_symbol="VTI",
            recommended_name="Vanguard Total Stock Market ETF",
            recommended_grade="A+",
            expected_grade_improvement=0.15,
            grade_improvement_description="Upgrade from B+ to A+ with lower fees",
            allocation_percentage=25.0,
            implementation_priority="high",
            rationale="Lower expense ratio (0.03% vs 0.75%) with broader diversification",
            risk_impact_description="Slightly reduced risk due to broader diversification",
            cost_analysis={"transaction_fee": 0.0, "bid_ask_spread": 0.01},
            implementation_notes=["Consider tax implications", "Execute during market hours"],
        )

        assert suggestion.improvement_type == "replacement"
        assert suggestion.recommended_symbol == "VTI"
        assert suggestion.recommended_grade == "A+"
        assert suggestion.expected_grade_improvement == 0.15
        assert suggestion.allocation_percentage == 25.0
        assert suggestion.implementation_priority == "high"
        assert len(suggestion.implementation_notes) == 2

    def test_should_validate_improvement_type_enum(self):
        """Test that improvement type must be valid enum value."""
        with pytest.raises(ValidationError) as exc_info:
            APlusImprovementSuggestion(
                improvement_type="invalid_type",
                recommended_symbol="VTI",
                recommended_name="Test ETF",
                recommended_grade="A+",
                expected_grade_improvement=0.1,
                grade_improvement_description="Test improvement",
                allocation_percentage=25.0,
                implementation_priority="high",
                rationale="Test rationale",
                risk_impact_description="Test risk impact",
            )

        assert "improvement_type" in str(exc_info.value)

    def test_should_validate_allocation_percentage_range(self):
        """Test that allocation percentage must be within valid range."""
        with pytest.raises(ValidationError) as exc_info:
            APlusImprovementSuggestion(
                improvement_type="replacement",
                recommended_symbol="VTI",
                recommended_name="Test ETF",
                recommended_grade="A+",
                expected_grade_improvement=0.1,
                grade_improvement_description="Test improvement",
                allocation_percentage=150.0,  # Invalid: > 100%
                implementation_priority="high",
                rationale="Test rationale",
                risk_impact_description="Test risk impact",
            )

        assert "allocation_percentage" in str(exc_info.value)


class TestAPlusOpportunitySection:
    """Test A+ opportunity section model."""

    def test_should_create_empty_opportunity_section(self):
        """Test creating an empty A+ opportunity section."""
        section = APlusOpportunitySection()

        assert section.total_opportunities_found == 0
        assert section.high_priority_opportunities == 0
        assert section.expected_portfolio_grade_improvement == 0.0
        assert section.grade_improvement_description == ""
        assert section.replacement_opportunities == 0
        assert section.addition_opportunities == 0
        assert section.rebalancing_opportunities == 0
        assert section.top_recommendations == []
        assert section.implementation_timeline == ""
        assert section.total_expected_annual_benefit == 0.0
        assert section.last_discovery_date is None
        assert section.discovery_coverage == []
        assert section.market_conditions_note == ""

    def test_should_create_populated_opportunity_section(self):
        """Test creating a populated A+ opportunity section."""
        discovery_date = datetime.now()

        section = APlusOpportunitySection(
            total_opportunities_found=5,
            high_priority_opportunities=2,
            expected_portfolio_grade_improvement=0.25,
            grade_improvement_description="Significant improvement from B+ to A- average",
            replacement_opportunities=3,
            addition_opportunities=1,
            rebalancing_opportunities=1,
            top_recommendations=["VTI", "VXUS", "BND"],
            implementation_timeline="Implement over 3 months",
            total_expected_annual_benefit=1.5,
            last_discovery_date=discovery_date,
            discovery_coverage=["etf", "stock"],
            market_conditions_note="Favorable market conditions for implementation",
        )

        assert section.total_opportunities_found == 5
        assert section.high_priority_opportunities == 2
        assert section.expected_portfolio_grade_improvement == 0.25
        assert len(section.top_recommendations) == 3
        assert section.last_discovery_date == discovery_date
        assert "etf" in section.discovery_coverage
        assert "stock" in section.discovery_coverage

    def test_should_limit_top_recommendations_count(self):
        """Test that top recommendations are limited to 5 items."""
        with pytest.raises(ValidationError) as exc_info:
            APlusOpportunitySection(
                top_recommendations=["VTI", "VXUS", "BND", "VEA", "VWO", "VTEB"]  # 6 items
            )

        assert "top_recommendations" in str(exc_info.value)
        assert "at most 5 items" in str(exc_info.value)


class TestEnhancedAlternative:
    """Test enhanced Alternative model with A+ fields."""

    def test_should_create_alternative_with_a_plus_fields(self):
        """Test creating alternative with A+ enhancement fields."""
        alternative = Alternative(
            ticker="VTI",
            name="Vanguard Total Stock Market ETF",
            asset_class="etf",
            composite_score=0.95,
            grade="A+",
            grade_description="Excellent low-cost broad market exposure",
            recommended_action="Strong Buy",
            risk_score_standardized=2.5,
            key_metrics={"expense_ratio": 0.03, "aum": 1.3e12},
            thesis_bullets=["Ultra-low fees", "Broad diversification"],
            citations=["Morningstar ETF Report 2024"],
            is_a_plus_candidate=True,
            discovery_source="investment_discovery_crew",
            confidence_level=0.92,
            expected_annual_benefit=0.8,
        )

        assert alternative.is_a_plus_candidate is True
        assert alternative.discovery_source == "investment_discovery_crew"
        assert alternative.confidence_level == 0.92
        assert alternative.expected_annual_benefit == 0.8
        assert alternative.asset_class == "etf"

    def test_should_support_crypto_asset_class(self):
        """Test that alternative supports crypto asset class."""
        alternative = Alternative(
            ticker="BTC-USD",
            name="Bitcoin",
            asset_class="crypto",
            composite_score=0.85,
            grade="A",
            grade_description="Leading cryptocurrency",
            recommended_action="Buy",
            risk_score_standardized=4.5,
            is_a_plus_candidate=False,
        )

        assert alternative.asset_class == "crypto"

    def test_should_have_default_a_plus_fields(self):
        """Test that A+ fields have appropriate defaults."""
        alternative = Alternative(
            ticker="AAPL",
            name="Apple Inc.",
            asset_class="stock",
            composite_score=0.88,
            grade="A",
            grade_description="High-quality growth stock",
            recommended_action="Buy",
            risk_score_standardized=3.0,
        )

        assert alternative.is_a_plus_candidate is False
        assert alternative.discovery_source is None
        assert alternative.confidence_level is None
        assert alternative.expected_annual_benefit is None


class TestEnhancedHoldingDecision:
    """Test enhanced HoldingDecision model with A+ improvement suggestions."""

    def test_should_create_holding_with_a_plus_suggestions(self):
        """Test creating holding decision with A+ improvement suggestions."""
        risk_assessment = RiskAssessmentStandardized(
            score=3.0, level="Medium", risk_factors=["Market volatility", "Sector concentration"]
        )

        improvement_suggestion = APlusImprovementSuggestion(
            improvement_type="replacement",
            recommended_symbol="VTI",
            recommended_name="Vanguard Total Stock Market ETF",
            recommended_grade="A+",
            expected_grade_improvement=0.2,
            grade_improvement_description="Upgrade from B+ to A+",
            allocation_percentage=30.0,
            implementation_priority="high",
            rationale="Lower fees and broader diversification",
            risk_impact_description="Reduced concentration risk",
        )

        holding = HoldingDecision(
            asset_class="etf",
            name="SPDR S&P 500 ETF",
            ticker="SPY",
            currency="USD",
            decision="KEEP",
            composite_score=0.75,
            grade="B+",
            grade_description="Good broad market exposure but higher fees",
            recommended_action="Consider alternatives",
            risk=risk_assessment,
            a_plus_improvement_suggestions=[improvement_suggestion],
            has_a_plus_opportunities=True,
            current_grade_potential="Could improve to A+ with lower-cost alternative",
        )

        assert len(holding.a_plus_improvement_suggestions) == 1
        assert holding.has_a_plus_opportunities is True
        assert holding.current_grade_potential is not None
        assert holding.a_plus_improvement_suggestions[0].recommended_symbol == "VTI"

    def test_should_limit_improvement_suggestions_count(self):
        """Test that improvement suggestions are limited to 5 items."""
        risk_assessment = RiskAssessmentStandardized(score=2.0, level="Low")

        # Create 6 improvement suggestions
        suggestions = []
        for i in range(6):
            suggestion = APlusImprovementSuggestion(
                improvement_type="replacement",
                recommended_symbol=f"ETF{i}",
                recommended_name=f"Test ETF {i}",
                recommended_grade="A+",
                expected_grade_improvement=0.1,
                grade_improvement_description="Test improvement",
                allocation_percentage=10.0,
                implementation_priority="medium",
                rationale="Test rationale",
                risk_impact_description="Test risk impact",
            )
            suggestions.append(suggestion)

        with pytest.raises(ValidationError) as exc_info:
            HoldingDecision(
                asset_class="etf",
                name="Test ETF",
                ticker="TEST",
                currency="USD",
                decision="KEEP",
                composite_score=0.7,
                grade="B",
                grade_description="Test grade",
                recommended_action="Test action",
                risk=risk_assessment,
                a_plus_improvement_suggestions=suggestions,
            )

        assert "a_plus_improvement_suggestions" in str(exc_info.value)
        assert "at most 5 items" in str(exc_info.value)

    def test_should_support_crypto_asset_class_in_holding(self):
        """Test that holding decision supports crypto asset class."""
        risk_assessment = RiskAssessmentStandardized(score=4.5, level="Very High")

        holding = HoldingDecision(
            asset_class="crypto",
            name="Bitcoin",
            ticker="BTC-USD",
            currency="USD",
            decision="KEEP",
            composite_score=0.8,
            grade="A",
            grade_description="Leading cryptocurrency",
            recommended_action="Hold",
            risk=risk_assessment,
        )

        assert holding.asset_class == "crypto"


class TestEnhancedPortfolioReview:
    """Test enhanced PortfolioReview model with A+ opportunities."""

    def test_should_create_portfolio_with_a_plus_opportunities(self):
        """Test creating portfolio review with A+ opportunities."""
        risk_assessment = RiskAssessmentStandardized(score=2.5, level="Medium")

        holding = HoldingDecision(
            asset_class="etf",
            name="Test ETF",
            ticker="TEST",
            currency="USD",
            decision="KEEP",
            composite_score=0.8,
            grade="A",
            grade_description="Good ETF",
            recommended_action="Keep",
            risk=risk_assessment,
        )

        opportunities = APlusOpportunitySection(
            total_opportunities_found=3,
            high_priority_opportunities=1,
            expected_portfolio_grade_improvement=0.15,
            grade_improvement_description="Improvement from A- to A",
            top_recommendations=["VTI", "VXUS"],
        )

        portfolio = PortfolioReview(
            as_of=datetime.now(),
            base_currency="CHF",
            holdings=[holding],
            a_plus_opportunities=opportunities,
            current_a_plus_holdings_count=1,
            potential_a_plus_holdings_count=3,
            portfolio_grade_improvement_potential=0.2,
            schema_version="2.0",
            has_a_plus_analysis=True,
        )

        assert portfolio.a_plus_opportunities.total_opportunities_found == 3
        assert portfolio.current_a_plus_holdings_count == 1
        assert portfolio.potential_a_plus_holdings_count == 3
        assert portfolio.portfolio_grade_improvement_potential == 0.2
        assert portfolio.schema_version == "2.0"
        assert portfolio.has_a_plus_analysis is True

    def test_should_have_default_a_plus_fields(self):
        """Test that A+ fields have appropriate defaults."""
        portfolio = PortfolioReview(as_of=datetime.now(), holdings=[])

        assert portfolio.a_plus_opportunities.total_opportunities_found == 0
        assert portfolio.current_a_plus_holdings_count == 0
        assert portfolio.potential_a_plus_holdings_count == 0
        assert portfolio.portfolio_grade_improvement_potential == 0.0
        assert portfolio.schema_version == "2.0"
        assert portfolio.has_a_plus_analysis is False

    def test_should_validate_required_fields(self):
        """Test that required fields are validated."""
        with pytest.raises(ValidationError) as exc_info:
            PortfolioReview()  # Missing required 'as_of' field

        assert "as_of" in str(exc_info.value)


class TestSchemaCompatibility:
    """Test schema compatibility and validation."""

    def test_should_maintain_backward_compatibility_structure(self):
        """Test that enhanced schemas maintain backward compatibility."""
        # Create a portfolio review with all new fields
        portfolio = PortfolioReview(
            as_of=datetime.now(), base_currency="CHF", holdings=[], schema_version="2.0", has_a_plus_analysis=True
        )

        # Should be able to serialize and deserialize
        data = portfolio.model_dump()
        reconstructed = PortfolioReview.model_validate(data)

        assert reconstructed.schema_version == "2.0"
        assert reconstructed.has_a_plus_analysis is True

    def test_should_handle_missing_optional_fields(self):
        """Test that optional A+ fields can be missing."""
        # Create minimal holding decision without A+ fields
        risk_assessment = RiskAssessmentStandardized(score=2.0, level="Low")

        holding_data = {
            "asset_class": "stock",
            "name": "Test Stock",
            "ticker": "TEST",
            "currency": "USD",
            "decision": "KEEP",
            "composite_score": 0.8,
            "grade": "A",
            "grade_description": "Good stock",
            "recommended_action": "Keep",
            "risk": risk_assessment.model_dump(),
        }

        holding = HoldingDecision.model_validate(holding_data)

        assert holding.has_a_plus_opportunities is False
        assert len(holding.a_plus_improvement_suggestions) == 0
        assert holding.current_grade_potential is None
