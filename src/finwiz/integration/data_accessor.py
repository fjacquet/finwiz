"""
Crew Data Accessor for unified data access with freshness validation.

This module provides a unified interface for accessing crew data with
automatic freshness validation, error handling, and graceful degradation.
"""

from typing import Any

from ..schemas.integration import APlusOpportunityCollection, DataAvailabilityReport
from .data_cache import DataCache
from .data_validation import DataValidator
from .manager import CrewDataIntegrationManager


class CrewDataAccessor:
    """
    Provides unified access to crew data with validation and error handling.

    This class acts as a high-level interface for accessing crew outputs
    with automatic freshness validation, error handling, and graceful degradation.
    """

    def __init__(self, integration_manager: CrewDataIntegrationManager) -> None:
        """
        Initialize the data accessor.

        Args:
            integration_manager: The integration manager instance

        """
        self.integration_manager = integration_manager
        self.logger = integration_manager.logger

        # Initialize component modules
        self.cache = DataCache(integration_manager, self.logger)
        self.validator = DataValidator(integration_manager, self.logger)

        self.logger.info("CrewDataAccessor initialized")

    def get_crew_data(self, crew_name: str, max_age_hours: int = 24) -> dict[str, Any] | None:
        """
        Get crew data with freshness validation.

        Args:
            crew_name: Name of the crew (stock, etf, crypto, discovery)
            max_age_hours: Maximum acceptable age in hours

        Returns:
            Crew data dictionary, or None if unavailable

        """
        return getattr(self.cache, f"get_{crew_name}_data")(max_age_hours)

    # Convenience methods for backward compatibility
    def get_stock_data(self, max_age_hours: int = 24) -> dict[str, Any] | None:
        """Get stock crew data with freshness validation."""
        return self.get_crew_data("stock", max_age_hours)

    def get_etf_data(self, max_age_hours: int = 24) -> dict[str, Any] | None:
        """Get ETF crew data with freshness validation."""
        return self.get_crew_data("etf", max_age_hours)

    def get_crypto_data(self, max_age_hours: int = 24) -> dict[str, Any] | None:
        """Get crypto crew data with freshness validation."""
        return self.get_crew_data("crypto", max_age_hours)

    def get_discovery_data(self, max_age_hours: int = 24) -> dict[str, Any] | None:
        """Get discovery crew data with freshness validation."""
        return self.get_crew_data("discovery", max_age_hours)

    def get_consolidated_data(self, max_age_hours: int = 24) -> dict[str, Any]:
        """
        Get consolidated data from all available crews.

        Args:
            max_age_hours: Maximum acceptable age in hours

        Returns:
            Dictionary containing all available crew data

        """
        return self.cache.get_consolidated_data(max_age_hours)

    def check_data_availability(self, max_age_hours: int = 24) -> DataAvailabilityReport:
        """
        Check availability of data across all crews.

        Args:
            max_age_hours: Maximum acceptable age in hours

        Returns:
            DataAvailabilityReport with detailed availability status

        """
        return self.validator.check_data_availability(max_age_hours)

    def get_stale_data_warnings(self, max_age_hours: int = 24) -> list[str]:
        """
        Get list of warnings for stale data.

        Args:
            max_age_hours: Maximum acceptable age in hours

        Returns:
            List of warning messages for stale data

        """
        return self.validator.get_stale_data_warnings(max_age_hours)

    def get_consolidated_market_sentiment(self, max_age_hours: int = 24) -> dict[str, Any]:
        """Consolidate market sentiment data from all crews."""
        return self.cache.get_consolidated_market_sentiment(max_age_hours)

    def get_consolidated_ticker_validation(self, max_age_hours: int = 24) -> dict[str, Any]:
        """Consolidate ticker validation results from all crews."""
        return self.cache.get_consolidated_ticker_validation(max_age_hours)

    def get_aplus_opportunities(self, max_age_hours: int = 24) -> APlusOpportunityCollection | None:
        """
        Get A+ investment opportunities from discovery crew outputs.

        Args:
            max_age_hours: Maximum acceptable age in hours for discovery data

        Returns:
            APlusOpportunityCollection with extracted opportunities, or None if unavailable

        """
        return self.cache.get_aplus_opportunities(max_age_hours)

    def get_consolidated_reporter_input(self, max_age_hours: int = 24) -> dict[str, Any]:
        """
        Get consolidated data for report generation including A+ opportunities and core analysis.

        Args:
            max_age_hours: Maximum acceptable age in hours

        Returns:
            Dictionary containing consolidated data optimized for report generation

        """
        return self.cache.get_consolidated_reporter_input(max_age_hours)
