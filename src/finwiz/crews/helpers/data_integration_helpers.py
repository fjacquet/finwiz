"""
Data integration helpers for ReportCrew.

This module provides helper methods for integrating data from various sources
and managing data availability tracking.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class DiscoveryStatusHelper:
    """Manages A+ discovery status checking."""

    def __init__(self, discovery_accessor: Any) -> None:
        """Initialize with discovery accessor."""
        self.discovery_accessor = discovery_accessor

    def get_discovery_status(self, inputs: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Get A+ discovery status with clear messaging.

        Checks for discovery data in this order:
        1. Flow state inputs (aplus_opportunities)
        2. Flow state inputs (investment_discovery_structured)
        3. File-based discovery accessor (fallback)

        Args:
            inputs: Optional inputs from Flow state containing discovery data

        Returns:
            Dictionary with discovery status information

        """
        # FIRST: Check if discovery data was provided in Flow state inputs
        if inputs:
            # Check for aplus_opportunities in inputs
            if inputs.get("aplus_opportunities"):
                logger.info("Discovery data found in Flow state (aplus_opportunities)")
                return {"has_results": True, "message": "A+ discovery results available", "status": "available"}

            # Check for investment_discovery_structured in inputs
            if inputs.get("investment_discovery_structured"):
                logger.info("Discovery data found in Flow state (investment_discovery_structured)")
                return {"has_results": True, "message": "A+ discovery results available", "status": "available"}

        # SECOND: Fall back to file-based checking
        has_results = self.discovery_accessor.has_discovery_results()

        if has_results:
            logger.info("Discovery data found via file-based accessor")
            return {"has_results": True, "message": "A+ discovery results available", "status": "available"}
        else:
            logger.info("No discovery data found in inputs or files")
            return {
                "has_results": False,
                "message": "A+ discovery not run - use --discovery flag to enable discovery analysis",
                "status": "not_run",
            }


class BacktestingStatusHelper:
    """Manages backtesting data status checking."""

    def __init__(self, discovery_accessor: Any, backtesting_extractor: Any) -> None:
        """Initialize with accessors."""
        self.discovery_accessor = discovery_accessor
        self.backtesting_extractor = backtesting_extractor

    def get_backtesting_status(self, inputs: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Get backtesting data status.

        Args:
            inputs: Optional inputs from Flow state

        Returns:
            Dictionary with backtesting status

        """
        # FIRST: Try to get discovery results from Flow state inputs
        discovery_results = None
        if inputs:
            if inputs.get("aplus_opportunities"):
                discovery_results = inputs["aplus_opportunities"]
                logger.info("Using discovery results from Flow state (aplus_opportunities) for backtesting")
            elif inputs.get("investment_discovery_structured"):
                discovery_results = inputs["investment_discovery_structured"]
                logger.info("Using discovery results from Flow state (investment_discovery_structured) for backtesting")

        # SECOND: Fall back to file-based loading if not in inputs
        if not discovery_results:
            if not self.discovery_accessor.has_discovery_results():
                logger.info("No discovery results available for backtesting")
                return {
                    "has_backtesting_data": False,
                    "message": "Backtesting data not available - discovery not run",
                    "status": "not_available",
                }

            # Load discovery results from files
            discovery_results = self.discovery_accessor.load_discovery_results()
            if not discovery_results:
                logger.info("Discovery results exist but could not be loaded")
                return {
                    "has_backtesting_data": False,
                    "message": "Backtesting data not available - discovery results could not be loaded",
                    "status": "not_available",
                }

        # Check for validation results
        validation_results = discovery_results.get("validation_results", [])
        if not validation_results:
            logger.info("No validation results found in discovery data")
            return {
                "has_backtesting_data": False,
                "message": "Backtesting data not available - no validation results in discovery",
                "status": "not_available",
            }

        return {
            "has_backtesting_data": True,
            "discovery_results": discovery_results,
            "validation_results": validation_results,
        }


class ContextMerger:
    """Merges Flow state inputs with integrated context."""

    @staticmethod
    def merge_flow_state_inputs(integrated_context: dict[str, Any], inputs: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Merge Flow state inputs with integrated context.

        Args:
            integrated_context: The integrated data context
            inputs: Optional Flow state inputs

        Returns:
            Merged context dictionary

        """
        if not inputs:
            logger.warning("⚠️  No inputs provided to merge - template variables will be missing")
            return integrated_context

        logger.info(f"Merging Flow state inputs - available keys: {list(inputs.keys())[:20]}")

        # Preserve original Flow state data that tasks expect
        preserved_keys = []
        for key in [
            "portfolio_review",
            "current_day",
            "current_month",
            "current_year",
            "current_date",
            "full_date",
            "timestamp",
            "report_language",
        ]:
            if key in inputs:
                if key not in integrated_context:
                    integrated_context[key] = inputs[key]
                    preserved_keys.append(key)
                    logger.info(f"✅ Preserved key: {key}")
                else:
                    logger.debug(f"Key {key} already in integrated_context, skipping")
            else:
                logger.warning(f"❌ Expected key '{key}' not found in Flow state inputs")

        if preserved_keys:
            logger.info(f"Successfully preserved {len(preserved_keys)} Flow state keys: {preserved_keys}")
        else:
            logger.warning("⚠️  No Flow state keys were preserved - this may cause template variable errors")

        return integrated_context
