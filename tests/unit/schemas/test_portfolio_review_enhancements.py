"""Unit tests for portfolio review schema enhancements."""

from datetime import datetime

import pytest
from pydantic import ValidationError
from pytest import approx

from finwiz.schemas.common import RiskAssessmentStandardized
from finwiz.schemas.portfolio_review import (
    Alternative,
    HoldingDecision,
    PortfolioReview,
    PositionSizeRecommendation,
    PriceTargets,
)


class TestPriceTargets:
    """Test suite for PriceTargets model."""

    def test_should_create_price_targets_with_all_fields(self):
        """Test creating price targets with all fields."""
        # Arrange & Act
        price_targets = PriceTargets(
            current_price=150.0,
            currency="USD",
            fair_value_estimate=160.0,
            buy_target_primary=145.0,
            buy_target_secondary=140.0,
            buy_rationale="Strong support at $145",
            sell_target_primary=165.0,
            sell_target_secondary=170.0,
            stop_loss_level=135.0,
            sell_rationale="Resistance at $165",
            support_levels=[140.0, 145.0],
            resistance_levels=[165.0, 170.0],
            calculation_method="Technical analysis + DCF",
            confidence_level=0.8,
            data_as_of=datetime.now(),
            data_sources=["Yahoo Finance", "SEC EDGAR"],
        )

        # Assert
        assert price_targets.current_price == approx(150.0)
        assert price_targets.currency == "USD"
        assert price_targets.fair_value_estimate == approx(160.0)
        assert price_targets.buy_target_primary == approx(145.0)
        assert price_targets.confidence_level == approx(0.8)
        assert len(price_targets.support_levels) == 2
        assert len(price_targets.data_sources) == 2

    def test_should_create_price_targets_with_minimal_fields(self):
        """Test creating price targets with only required fields."""
        # Arrange & Act
        price_targets = PriceTargets(
            current_price=100.0,
            currency="EUR",
            data_as_of=datetime.now(),
        )

        # Assert
        assert price_targets.current_price == approx(100.0)
        assert price_targets.currency == "EUR"
        assert price_targets.fair_value_estimate is None
        assert price_targets.buy_target_primary is None
        assert price_targets.confidence_level == approx(0.5)  # Default

    def test_should_validate_confidence_level_range(self):
        """Test that confidence level must be between 0 and 1."""
        # Act & Assert
        with pytest.raises(ValidationError):
            PriceTargets(
                current_price=100.0,
                currency="USD",
                confidence_level=1.5,  # Invalid
                data_as_of=datetime.now(),
            )


class TestPositionSizeRecommendation:
    """Test suite for PositionSizeRecommendation model."""

    def test_should_create_position_size_recommendation(self):
        """Test creating position size recommendation."""
        # Arrange & Act
        position_sizing = PositionSizeRecommendation(
            current_size_pct=8.0,
            recommended_size_pct=5.0,
            sizing_action="trim",
            sizing_rationale="Overweight position with high correlation",
            risk_contribution=12.5,
            correlation_with_portfolio=0.75,
            concentration_limits_applied=True,
            risk_limits_applied=False,
        )

        # Assert
        assert position_sizing.current_size_pct == approx(8.0)
        assert position_sizing.recommended_size_pct == approx(5.0)
        assert position_sizing.sizing_action == "trim"
        assert position_sizing.concentration_limits_applied is True

    def test_should_validate_sizing_action_values(self):
        """Test that sizing action must be one of allowed values."""
        # Act & Assert
        with pytest.raises(ValidationError):
            PositionSizeRecommendation(
                current_size_pct=5.0,
                recommended_size_pct=5.0,
                sizing_action="invalid_action",  # Invalid
                sizing_rationale="Test",
            )

    def test_should_validate_percentage_ranges(self):
        """Test that percentages must be between 0 and 100."""
        # Act & Assert
        with pytest.raises(ValidationError):
            PositionSizeRecommendation(
                current_size_pct=150.0,  # Invalid
                recommended_size_pct=5.0,
                sizing_action="hold",
                sizing_rationale="Test",
            )


class TestAlternativeEnhancements:
    """Test suite for Alternative model enhancements."""

    def test_should_create_alternative_with_transition_strategy(self):
        """Test creating alternative with transition strategy fields."""
        # Arrange & Act
        alternative = Alternative(
            ticker="VUSA.L",
            name="Vanguard S&P 500 UCITS ETF",
            asset_class="etf",
            composite_score=0.85,
            grade="A+",
            grade_description="Excellent",
            recommended_action="BUY",
            risk_score_standardized=2.5,
            transition_strategy="Gradual swap over 3 months",
            swap_timing="gradual",
            tax_implications="No capital gains in tax-advantaged account",
            expected_cost_basis_impact=0.0,
            expense_ratio_savings=0.05,
        )

        # Assert
        assert alternative.transition_strategy == "Gradual swap over 3 months"
        assert alternative.swap_timing == "gradual"
        assert alternative.expense_ratio_savings == approx(0.05)

    def test_should_validate_swap_timing_values(self):
        """Test that swap timing must be one of allowed values."""
        # Act & Assert
        with pytest.raises(ValidationError):
            Alternative(
                ticker="TEST",
                name="Test",
                asset_class="stock",
                composite_score=0.8,
                grade="A",
                grade_description="Good",
                recommended_action="BUY",
                risk_score_standardized=3.0,
                swap_timing="invalid_timing",  # Invalid
            )


class TestHoldingDecisionEnhancements:
    """Test suite for HoldingDecision model enhancements."""

    def test_should_create_holding_decision_with_price_targets(self):
        """Test creating holding decision with price targets."""
        # Arrange
        risk = RiskAssessmentStandardized(
            score=3.5,
            level="Medium",
            risk_factors=["Market risk"],
        )

        price_targets = PriceTargets(
            current_price=150.0,
            currency="USD",
            fair_value_estimate=160.0,
            data_as_of=datetime.now(),
        )

        # Act
        holding = HoldingDecision(
            asset_class="stock",
            name="Apple Inc.",
            ticker="AAPL",
            currency="USD",
            decision="KEEP",
            composite_score=0.85,
            grade="A",
            grade_description="Strong fundamentals",
            recommended_action="Hold and accumulate on dips",
            risk=risk,
            price_targets=price_targets,
        )

        # Assert
        assert holding.price_targets is not None
        assert holding.price_targets.current_price == approx(150.0)
        assert holding.price_targets.fair_value_estimate == approx(160.0)

    def test_should_create_holding_decision_with_position_sizing(self):
        """Test creating holding decision with position sizing."""
        # Arrange
        risk = RiskAssessmentStandardized(
            score=3.5,
            level="Medium",
            risk_factors=["Market risk"],
        )

        position_sizing = PositionSizeRecommendation(
            current_size_pct=8.0,
            recommended_size_pct=5.0,
            sizing_action="trim",
            sizing_rationale="Overweight position",
        )

        # Act
        holding = HoldingDecision(
            asset_class="stock",
            name="Apple Inc.",
            ticker="AAPL",
            currency="USD",
            decision="KEEP",
            composite_score=0.85,
            grade="A",
            grade_description="Strong fundamentals",
            recommended_action="Trim to target weight",
            risk=risk,
            position_sizing=position_sizing,
        )

        # Assert
        assert holding.position_sizing is not None
        assert holding.position_sizing.sizing_action == "trim"
        assert holding.position_sizing.current_size_pct == approx(8.0)

    def test_should_create_holding_decision_with_data_freshness(self):
        """Test creating holding decision with data freshness tracking."""
        # Arrange
        risk = RiskAssessmentStandardized(
            score=3.5,
            level="Medium",
            risk_factors=["Market risk"],
        )

        # Act
        holding = HoldingDecision(
            asset_class="stock",
            name="Apple Inc.",
            ticker="AAPL",
            currency="USD",
            decision="KEEP",
            composite_score=0.85,
            grade="A",
            grade_description="Strong fundamentals",
            recommended_action="Hold",
            risk=risk,
            data_freshness="fresh",
            crew_analysis_used="stock_crew",
            analysis_date=datetime.now(),
        )

        # Assert
        assert holding.data_freshness == "fresh"
        assert holding.crew_analysis_used == "stock_crew"
        assert holding.analysis_date is not None


class TestPortfolioReviewEnhancements:
    """Test suite for PortfolioReview model enhancements."""

    def test_should_create_portfolio_review_with_schema_version_2_1(self):
        """Test that new portfolio reviews have schema version 2.1."""
        # Arrange & Act
        portfolio = PortfolioReview(
            as_of=datetime.now(),
            base_currency="CHF",
        )

        # Assert
        assert portfolio.schema_version == "2.1"
        assert portfolio.has_deep_analysis is False

    def test_should_track_deep_analysis_flag(self):
        """Test tracking of deep analysis completion."""
        # Arrange & Act
        portfolio = PortfolioReview(
            as_of=datetime.now(),
            base_currency="CHF",
            has_deep_analysis=True,
        )

        # Assert
        assert portfolio.has_deep_analysis is True

    def test_should_create_complete_portfolio_with_enhanced_holdings(self):
        """Test creating complete portfolio with enhanced holdings."""
        # Arrange
        risk = RiskAssessmentStandardized(
            score=3.5,
            level="Medium",
            risk_factors=["Market risk"],
        )

        price_targets = PriceTargets(
            current_price=150.0,
            currency="USD",
            data_as_of=datetime.now(),
        )

        position_sizing = PositionSizeRecommendation(
            current_size_pct=5.0,
            recommended_size_pct=5.0,
            sizing_action="hold",
            sizing_rationale="At target weight",
        )

        holding = HoldingDecision(
            asset_class="stock",
            name="Apple Inc.",
            ticker="AAPL",
            currency="USD",
            decision="KEEP",
            composite_score=0.85,
            grade="A",
            grade_description="Strong fundamentals",
            recommended_action="Hold",
            risk=risk,
            price_targets=price_targets,
            position_sizing=position_sizing,
            data_freshness="fresh",
            crew_analysis_used="stock_crew",
            analysis_date=datetime.now(),
        )

        # Act
        portfolio = PortfolioReview(
            as_of=datetime.now(),
            base_currency="CHF",
            holdings=[holding],
            has_deep_analysis=True,
        )

        # Assert
        assert len(portfolio.holdings) == 1
        assert portfolio.holdings[0].price_targets is not None
        assert portfolio.holdings[0].position_sizing is not None
        assert portfolio.holdings[0].data_freshness == "fresh"
        assert portfolio.schema_version == "2.1"


class TestAllocationFields:
    """Allocation/valuation fields on HoldingDecision and PortfolioReview."""

    def _risk(self):
        from finwiz.schemas.common import RiskAssessmentStandardized

        return RiskAssessmentStandardized(score=2.5, level="Medium", risk_factors=[])

    def test_holding_decision_allocation_fields_default_none(self):
        from finwiz.schemas.portfolio_review import HoldingDecision

        d = HoldingDecision(
            asset_class="stock",
            name="Apple",
            ticker="AAPL",
            currency="USD",
            decision="KEEP",
            composite_score=0.8,
            grade="A",
            grade_description="Strong",
            recommended_action="hold",
            risk=self._risk(),
        )

        assert d.quantity is None
        assert d.native_currency is None
        assert d.native_value is None
        assert d.eur_value is None
        assert d.weight is None

    def test_holding_decision_allocation_fields_assignable(self):
        from finwiz.schemas.portfolio_review import HoldingDecision

        d = HoldingDecision(
            asset_class="stock",
            name="Apple",
            ticker="AAPL",
            currency="USD",
            decision="KEEP",
            composite_score=0.8,
            grade="A",
            grade_description="Strong",
            recommended_action="hold",
            risk=self._risk(),
        )
        d.quantity = 10.0
        d.native_currency = "USD"
        d.native_value = 1500.0
        d.eur_value = 1380.0
        d.weight = 0.25

        assert d.quantity == 10.0
        assert d.native_currency == "USD"
        assert d.native_value == 1500.0
        assert d.eur_value == 1380.0
        assert d.weight == 0.25

    def test_weight_must_be_between_0_and_1(self):
        from pydantic import ValidationError

        from finwiz.schemas.portfolio_review import HoldingDecision

        with pytest.raises(ValidationError):
            HoldingDecision(
                asset_class="stock",
                name="Apple",
                ticker="AAPL",
                currency="USD",
                decision="KEEP",
                composite_score=0.8,
                grade="A",
                grade_description="Strong",
                recommended_action="hold",
                risk=self._risk(),
                weight=1.5,
            )

    def test_portfolio_review_total_value_eur_default_none(self):
        from datetime import UTC, datetime

        from finwiz.schemas.portfolio_review import PortfolioReview

        review = PortfolioReview(as_of=datetime.now(UTC))

        assert review.total_value_eur is None


class TestPortfolioReviewSchemaReexportShim:
    """Wave-3 Task 9: AssetClass/PositionSizeRecommendation/PriceTargets must be
    the SAME objects as crewai_custom_tools.models.analytics_models — finwiz
    re-exports rather than redefines them, so isinstance/validation stay coherent.
    """

    def test_asset_class_is_central_object(self):
        from crewai_custom_tools.models.analytics_models import AssetClass as CentralAssetClass

        import finwiz.schemas.portfolio_review as finwiz_portfolio_review

        assert finwiz_portfolio_review.AssetClass is CentralAssetClass

    def test_position_size_recommendation_is_central_class(self):
        from crewai_custom_tools.models.analytics_models import (
            PositionSizeRecommendation as CentralPositionSizeRecommendation,
        )

        import finwiz.schemas.portfolio_review as finwiz_portfolio_review

        assert finwiz_portfolio_review.PositionSizeRecommendation is CentralPositionSizeRecommendation

    def test_price_targets_is_central_class(self):
        from crewai_custom_tools.models.analytics_models import PriceTargets as CentralPriceTargets

        import finwiz.schemas.portfolio_review as finwiz_portfolio_review

        assert finwiz_portfolio_review.PriceTargets is CentralPriceTargets
