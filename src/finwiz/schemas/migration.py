"""
Migration utilities for schema evolution and backward compatibility.

This module provides utilities to migrate existing portfolio data to support
A+ investment discovery features while maintaining backward compatibility.
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import ValidationError

from .portfolio_review import APlusOpportunitySection, PortfolioReview

logger = logging.getLogger(__name__)


class SchemaMigrationError(Exception):
    """Raised when schema migration fails."""

    pass


def migrate_holding_decision_v1_to_v2(holding_data: dict[str, Any]) -> dict[str, Any]:
    """
    Migrate HoldingDecision from v1 (without A+ fields) to v2 (with A+ fields).

    Args:
        holding_data: Raw holding decision data from v1 schema

    Returns:
        Migrated holding decision data compatible with v2 schema

    Raises:
        SchemaMigrationError: If migration fails

    """
    try:
        # Create a copy to avoid modifying original data
        migrated_data = holding_data.copy()

        # Add new A+ fields with default values
        if "a_plus_improvement_suggestions" not in migrated_data:
            migrated_data["a_plus_improvement_suggestions"] = []

        if "has_a_plus_opportunities" not in migrated_data:
            migrated_data["has_a_plus_opportunities"] = False

        if "current_grade_potential" not in migrated_data:
            migrated_data["current_grade_potential"] = None

        # Migrate alternatives to include A+ fields
        if "alternatives" in migrated_data:
            for alternative in migrated_data["alternatives"]:
                if "is_a_plus_candidate" not in alternative:
                    alternative["is_a_plus_candidate"] = False
                if "discovery_source" not in alternative:
                    alternative["discovery_source"] = None
                if "confidence_level" not in alternative:
                    alternative["confidence_level"] = None
                if "expected_annual_benefit" not in alternative:
                    alternative["expected_annual_benefit"] = None

        # Ensure asset_class supports crypto (backward compatible)
        if migrated_data.get("asset_class") not in ["stock", "etf", "crypto"]:
            logger.warning(f"Unknown asset_class: {migrated_data.get('asset_class')}, defaulting to 'stock'")
            migrated_data["asset_class"] = "stock"

        return migrated_data

    except Exception as e:
        raise SchemaMigrationError(f"Failed to migrate HoldingDecision: {e}") from e


def migrate_portfolio_review_v1_to_v2(portfolio_data: dict[str, Any]) -> dict[str, Any]:
    """
    Migrate PortfolioReview from v1 (without A+ fields) to v2 (with A+ fields).

    Args:
        portfolio_data: Raw portfolio review data from v1 schema

    Returns:
        Migrated portfolio review data compatible with v2 schema

    Raises:
        SchemaMigrationError: If migration fails

    """
    try:
        # Create a copy to avoid modifying original data
        migrated_data = portfolio_data.copy()

        # Add A+ opportunity section with defaults
        if "a_plus_opportunities" not in migrated_data:
            migrated_data["a_plus_opportunities"] = {
                "total_opportunities_found": 0,
                "high_priority_opportunities": 0,
                "expected_portfolio_grade_improvement": 0.0,
                "grade_improvement_description": "",
                "replacement_opportunities": 0,
                "addition_opportunities": 0,
                "rebalancing_opportunities": 0,
                "top_recommendations": [],
                "implementation_timeline": "",
                "total_expected_annual_benefit": 0.0,
                "last_discovery_date": None,
                "discovery_coverage": [],
                "market_conditions_note": "",
            }

        # Add portfolio-level A+ metrics
        if "current_a_plus_holdings_count" not in migrated_data:
            migrated_data["current_a_plus_holdings_count"] = 0

        if "potential_a_plus_holdings_count" not in migrated_data:
            migrated_data["potential_a_plus_holdings_count"] = 0

        if "portfolio_grade_improvement_potential" not in migrated_data:
            migrated_data["portfolio_grade_improvement_potential"] = 0.0

        # Add migration and compatibility fields
        if "schema_version" not in migrated_data:
            migrated_data["schema_version"] = "2.0"

        if "has_a_plus_analysis" not in migrated_data:
            migrated_data["has_a_plus_analysis"] = False

        # Migrate all holdings
        if "holdings" in migrated_data:
            migrated_holdings = []
            for holding in migrated_data["holdings"]:
                migrated_holding = migrate_holding_decision_v1_to_v2(holding)
                migrated_holdings.append(migrated_holding)
            migrated_data["holdings"] = migrated_holdings

        return migrated_data

    except Exception as e:
        raise SchemaMigrationError(f"Failed to migrate PortfolioReview: {e}") from e


def is_v1_schema(data: dict[str, Any]) -> bool:
    """
    Check if the data represents a v1 schema (without A+ fields).

    Args:
        data: Raw data to check

    Returns:
        True if data appears to be v1 schema, False otherwise

    """
    # Check for absence of v2 fields
    v2_indicators = ["a_plus_opportunities", "schema_version", "has_a_plus_analysis"]

    return not any(indicator in data for indicator in v2_indicators)


def migrate_portfolio_review_if_needed(data: dict[str, Any]) -> PortfolioReview:
    """
    Migrate portfolio review data if needed and return validated model.

    Args:
        data: Raw portfolio review data

    Returns:
        Validated PortfolioReview model

    Raises:
        SchemaMigrationError: If migration fails
        ValidationError: If validation fails after migration

    """
    try:
        # First try to validate as-is (might be v2 already)
        try:
            return PortfolioReview.model_validate(data)
        except ValidationError:
            # If validation fails, try migration
            if is_v1_schema(data):
                logger.info("Detected v1 schema, performing migration to v2")
                migrated_data = migrate_portfolio_review_v1_to_v2(data)
                return PortfolioReview.model_validate(migrated_data)
            else:
                # Re-raise the original validation error
                raise

    except ValidationError as e:
        logger.error(f"Schema validation failed after migration: {e}")
        raise
    except Exception as e:
        raise SchemaMigrationError(f"Migration process failed: {e}") from e


def get_schema_version(data: dict[str, Any]) -> str:
    """
    Get the schema version from data, defaulting to "1.0" if not present.

    Args:
        data: Raw data to check

    Returns:
        Schema version string

    """
    return data.get("schema_version", "1.0")


def add_a_plus_opportunities_to_existing_review(portfolio_review: PortfolioReview, opportunities_data: dict[str, Any]) -> PortfolioReview:
    """
    Add A+ opportunities to an existing portfolio review.

    Args:
        portfolio_review: Existing portfolio review
        opportunities_data: A+ opportunities data to add

    Returns:
        Updated portfolio review with A+ opportunities

    """
    try:
        # Update the A+ opportunities section
        portfolio_review.a_plus_opportunities = APlusOpportunitySection.model_validate(opportunities_data)

        # Mark as having A+ analysis
        portfolio_review.has_a_plus_analysis = True

        # Update schema version
        portfolio_review.schema_version = "2.0"

        return portfolio_review

    except ValidationError as e:
        logger.error(f"Failed to add A+ opportunities: {e}")
        raise SchemaMigrationError(f"Failed to add A+ opportunities: {e}") from e


def ensure_backward_compatibility(portfolio_review: PortfolioReview) -> dict[str, Any]:
    """
    Ensure backward compatibility by providing a v1-compatible representation.

    This function creates a dictionary that can be safely used with v1 consumers
    by excluding v2-specific fields.

    Args:
        portfolio_review: PortfolioReview model instance

    Returns:
        Dictionary compatible with v1 schema

    """
    # Convert to dict and remove v2-specific fields
    data = portfolio_review.model_dump()

    # Remove v2-specific top-level fields
    v2_fields = [
        "a_plus_opportunities",
        "current_a_plus_holdings_count",
        "potential_a_plus_holdings_count",
        "portfolio_grade_improvement_potential",
        "schema_version",
        "has_a_plus_analysis",
    ]

    for field in v2_fields:
        data.pop(field, None)

    # Remove v2-specific fields from holdings
    if "holdings" in data:
        for holding in data["holdings"]:
            holding_v2_fields = ["a_plus_improvement_suggestions", "has_a_plus_opportunities", "current_grade_potential"]
            for field in holding_v2_fields:
                holding.pop(field, None)

            # Remove v2-specific fields from alternatives
            if "alternatives" in holding:
                for alternative in holding["alternatives"]:
                    alt_v2_fields = ["is_a_plus_candidate", "discovery_source", "confidence_level", "expected_annual_benefit"]
                    for field in alt_v2_fields:
                        alternative.pop(field, None)

    return data
