"""
Tests for schema migration utilities.

This module tests the migration functionality that ensures backward compatibility
when upgrading from v1 schemas (without A+ fields) to v2 schemas (with A+ fields).
"""

from pytest import approx
from datetime import datetime

import pytest
from pydantic import ValidationError

from finwiz.schemas.migration import (
    SchemaMigrationError,
    add_a_plus_opportunities_to_existing_review,
    ensure_backward_compatibility,
    get_schema_version,
    is_v1_schema,
    migrate_holding_decision_v1_to_v2,
    migrate_portfolio_review_if_needed,
    migrate_portfolio_review_v1_to_v2,
)
from finwiz.schemas.portfolio_review import APlusOpportunitySection, PortfolioReview


class TestHoldingDecisionMigration:
    """Test migration of HoldingDecision from v1 to v2."""

    def test_should_migrate_v1_holding_to_v2(self):
        """Test migrating a v1 holding decision to v2 format."""
        v1_holding = {
            "asset_class": "etf",
            "name": "SPDR S&P 500 ETF",
            "ticker": "SPY",
            "currency": "USD",
            "decision": "KEEP",
            "composite_score": 0.85,
            "grade": "A",
            "grade_description": "Good broad market exposure",
            "recommended_action": "Keep",
            "risk": {"score": 2.5, "level": "Medium", "risk_factors": ["Market volatility"]},
            "rationale_bullets": ["Strong performance", "Good liquidity"],
            "citations": ["Morningstar Report"],
            "alternatives": [
                {
                    "ticker": "VTI",
                    "name": "Vanguard Total Stock Market ETF",
                    "asset_class": "etf",
                    "composite_score": 0.92,
                    "grade": "A+",
                    "grade_description": "Excellent low-cost option",
                    "recommended_action": "Strong Buy",
                    "risk_score_standardized": 2.0,
                    "key_metrics": {"expense_ratio": 0.03},
                    "thesis_bullets": ["Ultra-low fees"],
                    "citations": ["Vanguard Prospectus"],
                }
            ],
        }

        migrated = migrate_holding_decision_v1_to_v2(v1_holding)

        # Check that v2 fields were added with defaults
        assert "a_plus_improvement_suggestions" in migrated
        assert migrated["a_plus_improvement_suggestions"] == []
        assert "has_a_plus_opportunities" in migrated
        assert migrated["has_a_plus_opportunities"] is False
        assert "current_grade_potential" in migrated
        assert migrated["current_grade_potential"] is None

        # Check that alternatives were migrated
        alternative = migrated["alternatives"][0]
        assert "is_a_plus_candidate" in alternative
        assert alternative["is_a_plus_candidate"] is False
        assert "discovery_source" in alternative
        assert alternative["discovery_source"] is None
        assert "confidence_level" in alternative
        assert alternative["confidence_level"] is None
        assert "expected_annual_benefit" in alternative
        assert alternative["expected_annual_benefit"] is None

        # Check that original fields are preserved
        assert migrated["ticker"] == "SPY"
        assert migrated["composite_score"] == approx(0.85)
        assert migrated["grade"] == "A"

    def test_should_handle_missing_alternatives(self):
        """Test migration when alternatives field is missing."""
        v1_holding = {
            "asset_class": "stock",
            "name": "Apple Inc.",
            "ticker": "AAPL",
            "currency": "USD",
            "decision": "KEEP",
            "composite_score": 0.9,
            "grade": "A+",
            "grade_description": "Excellent growth stock",
            "recommended_action": "Strong Buy",
            "risk": {"score": 3.0, "level": "Medium"},
        }

        migrated = migrate_holding_decision_v1_to_v2(v1_holding)

        # Should add v2 fields without errors
        assert "a_plus_improvement_suggestions" in migrated
        assert "has_a_plus_opportunities" in migrated
        assert "current_grade_potential" in migrated

    def test_should_handle_unknown_asset_class(self):
        """Test migration with unknown asset class."""
        v1_holding = {
            "asset_class": "unknown_type",
            "name": "Test Asset",
            "ticker": "TEST",
            "currency": "USD",
            "decision": "KEEP",
            "composite_score": 0.8,
            "grade": "B+",
            "grade_description": "Test asset",
            "recommended_action": "Hold",
            "risk": {"score": 2.0, "level": "Low"},
        }

        migrated = migrate_holding_decision_v1_to_v2(v1_holding)

        # Should default to 'stock' for unknown asset class
        assert migrated["asset_class"] == "stock"

    def test_should_raise_error_on_invalid_data(self):
        """Test that migration raises error for invalid data."""
        invalid_holding = None  # Completely invalid data

        with pytest.raises(SchemaMigrationError):
            migrate_holding_decision_v1_to_v2(invalid_holding)


class TestPortfolioReviewMigration:
    """Test migration of PortfolioReview from v1 to v2."""

    def test_should_migrate_v1_portfolio_to_v2(self):
        """Test migrating a v1 portfolio review to v2 format."""
        v1_portfolio = {
            "as_of": "2024-01-15T10:00:00",
            "base_currency": "CHF",
            "holdings": [
                {
                    "asset_class": "etf",
                    "name": "SPDR S&P 500 ETF",
                    "ticker": "SPY",
                    "currency": "USD",
                    "decision": "KEEP",
                    "composite_score": 0.85,
                    "grade": "A",
                    "grade_description": "Good ETF",
                    "recommended_action": "Keep",
                    "risk": {"score": 2.5, "level": "Medium"},
                    "alternatives": [],
                }
            ],
        }

        migrated = migrate_portfolio_review_v1_to_v2(v1_portfolio)

        # Check that v2 fields were added
        assert "a_plus_opportunities" in migrated
        assert migrated["a_plus_opportunities"]["total_opportunities_found"] == 0
        assert "current_a_plus_holdings_count" in migrated
        assert migrated["current_a_plus_holdings_count"] == 0
        assert "potential_a_plus_holdings_count" in migrated
        assert migrated["potential_a_plus_holdings_count"] == 0
        assert "portfolio_grade_improvement_potential" in migrated
        assert migrated["portfolio_grade_improvement_potential"] == approx(0.0)
        assert "schema_version" in migrated
        assert migrated["schema_version"] == "2.0"
        assert "has_a_plus_analysis" in migrated
        assert migrated["has_a_plus_analysis"] is False

        # Check that holdings were migrated
        holding = migrated["holdings"][0]
        assert "a_plus_improvement_suggestions" in holding
        assert "has_a_plus_opportunities" in holding
        assert "current_grade_potential" in holding

        # Check that original fields are preserved
        assert migrated["as_of"] == "2024-01-15T10:00:00"
        assert migrated["base_currency"] == "CHF"

    def test_should_handle_empty_holdings(self):
        """Test migration with empty holdings list."""
        v1_portfolio = {"as_of": "2024-01-15T10:00:00", "base_currency": "USD", "holdings": []}

        migrated = migrate_portfolio_review_v1_to_v2(v1_portfolio)

        # Should add v2 fields without errors
        assert "a_plus_opportunities" in migrated
        assert "schema_version" in migrated
        assert migrated["holdings"] == []

    def test_should_raise_error_on_invalid_data(self):
        """Test that migration raises error for invalid data."""
        invalid_portfolio = None  # Completely invalid data

        with pytest.raises(SchemaMigrationError):
            migrate_portfolio_review_v1_to_v2(invalid_portfolio)


class TestSchemaVersionDetection:
    """Test schema version detection utilities."""

    def test_should_detect_v1_schema(self):
        """Test detection of v1 schema."""
        v1_data = {"as_of": "2024-01-15T10:00:00", "base_currency": "CHF", "holdings": []}

        assert is_v1_schema(v1_data) is True

    def test_should_detect_v2_schema(self):
        """Test detection of v2 schema."""
        v2_data = {
            "as_of": "2024-01-15T10:00:00",
            "base_currency": "CHF",
            "holdings": [],
            "schema_version": "2.0",
            "has_a_plus_analysis": False,
        }

        assert is_v1_schema(v2_data) is False

    def test_should_get_schema_version(self):
        """Test getting schema version from data."""
        v1_data = {"as_of": "2024-01-15T10:00:00"}
        v2_data = {"as_of": "2024-01-15T10:00:00", "schema_version": "2.0"}

        assert get_schema_version(v1_data) == "1.0"
        assert get_schema_version(v2_data) == "2.0"


class TestAutomaticMigration:
    """Test automatic migration functionality."""

    def test_should_migrate_v1_data_automatically(self):
        """Test automatic migration of v1 data."""
        v1_data = {
            "as_of": "2024-01-15T10:00:00",
            "base_currency": "CHF",
            "holdings": [
                {
                    "asset_class": "stock",
                    "name": "Apple Inc.",
                    "ticker": "AAPL",
                    "currency": "USD",
                    "decision": "KEEP",
                    "composite_score": 0.9,
                    "grade": "A+",
                    "grade_description": "Excellent stock",
                    "recommended_action": "Strong Buy",
                    "risk": {"score": 3.0, "level": "Medium"},
                }
            ],
        }

        portfolio = migrate_portfolio_review_if_needed(v1_data)

        assert isinstance(portfolio, PortfolioReview)
        assert portfolio.schema_version == "2.1"
        assert portfolio.has_a_plus_analysis is False
        assert len(portfolio.holdings) == 1
        assert portfolio.holdings[0].has_a_plus_opportunities is False

    def test_should_handle_v2_data_without_migration(self):
        """Test that v2 data is handled without migration."""
        v2_data = {
            "as_of": "2024-01-15T10:00:00",
            "base_currency": "CHF",
            "holdings": [],
            "schema_version": "2.0",
            "has_a_plus_analysis": True,
        }

        portfolio = migrate_portfolio_review_if_needed(v2_data)

        assert isinstance(portfolio, PortfolioReview)
        assert portfolio.schema_version == "2.0"
        assert portfolio.has_a_plus_analysis is True

    def test_should_raise_error_on_invalid_data(self):
        """Test that invalid data raises appropriate error."""
        invalid_data = {"invalid": "data"}

        with pytest.raises((ValidationError, SchemaMigrationError)):
            migrate_portfolio_review_if_needed(invalid_data)


class TestAPlusOpportunityIntegration:
    """Test integration of A+ opportunities into existing reviews."""

    def test_should_add_opportunities_to_existing_review(self):
        """Test adding A+ opportunities to existing portfolio review."""
        portfolio = PortfolioReview(as_of=datetime.now(), base_currency="CHF", holdings=[])

        opportunities_data = {
            "total_opportunities_found": 3,
            "high_priority_opportunities": 1,
            "expected_portfolio_grade_improvement": 0.2,
            "grade_improvement_description": "Significant improvement",
            "top_recommendations": ["VTI", "VXUS"],
        }

        updated_portfolio = add_a_plus_opportunities_to_existing_review(portfolio, opportunities_data)

        assert updated_portfolio.a_plus_opportunities.total_opportunities_found == 3
        assert updated_portfolio.has_a_plus_analysis is True
        assert updated_portfolio.schema_version == "2.0"

    def test_should_raise_error_on_invalid_opportunities_data(self):
        """Test error handling for invalid opportunities data."""
        portfolio = PortfolioReview(as_of=datetime.now(), holdings=[])

        invalid_opportunities = {"invalid": "data"}

        with pytest.raises(SchemaMigrationError):
            add_a_plus_opportunities_to_existing_review(portfolio, invalid_opportunities)


class TestBackwardCompatibility:
    """Test backward compatibility utilities."""

    def test_should_create_v1_compatible_representation(self):
        """Test creating v1-compatible representation from v2 data."""
        # Create v2 portfolio with A+ fields
        opportunities = APlusOpportunitySection(total_opportunities_found=2, high_priority_opportunities=1)

        portfolio = PortfolioReview(
            as_of=datetime.now(),
            base_currency="CHF",
            holdings=[],
            a_plus_opportunities=opportunities,
            current_a_plus_holdings_count=1,
            schema_version="2.0",
            has_a_plus_analysis=True,
        )

        v1_compatible = ensure_backward_compatibility(portfolio)

        # Check that v2 fields are removed
        v2_fields = [
            "a_plus_opportunities",
            "current_a_plus_holdings_count",
            "potential_a_plus_holdings_count",
            "portfolio_grade_improvement_potential",
            "schema_version",
            "has_a_plus_analysis",
        ]

        for field in v2_fields:
            assert field not in v1_compatible

        # Check that v1 fields are preserved
        assert "as_of" in v1_compatible
        assert "base_currency" in v1_compatible
        assert "holdings" in v1_compatible

    def test_should_remove_v2_fields_from_holdings(self):
        """Test that v2 fields are removed from holdings in v1 representation."""
        from finwiz.schemas.common import RiskAssessmentStandardized
        from finwiz.schemas.portfolio_review import HoldingDecision

        risk = RiskAssessmentStandardized(score=2.0, level="Low")

        holding = HoldingDecision(
            asset_class="stock",
            name="Test Stock",
            ticker="TEST",
            currency="USD",
            decision="KEEP",
            composite_score=0.8,
            grade="A",
            grade_description="Good stock",
            recommended_action="Keep",
            risk=risk,
            has_a_plus_opportunities=True,
            current_grade_potential="High potential",
        )

        portfolio = PortfolioReview(as_of=datetime.now(), holdings=[holding])

        v1_compatible = ensure_backward_compatibility(portfolio)

        # Check that holding v2 fields are removed
        holding_data = v1_compatible["holdings"][0]
        holding_v2_fields = ["a_plus_improvement_suggestions", "has_a_plus_opportunities", "current_grade_potential"]

        for field in holding_v2_fields:
            assert field not in holding_data