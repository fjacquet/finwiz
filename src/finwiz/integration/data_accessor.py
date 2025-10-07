"""
Crew Data Accessor for unified data access with freshness validation.

This module provides a unified interface for accessing crew data with
automatic freshness validation, error handling, and graceful degradation.
"""

from typing import Any

from finwiz.schemas.integration import APlusOpportunityCollection, DataAvailabilityReport

from .backtesting_extractor import BacktestingDataExtractor
from .data_cache import DataCache
from .data_validation import DataValidator
from .discovery_methodology_extractor import DiscoveryMethodologyExtractor
from .manager import CrewDataIntegrationManager
from .market_context_extractor import MarketContextExtractor
from .performance_metrics_aggregator import PerformanceMetricsAggregator


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

        # Initialize enhanced data extractors
        self.backtesting_extractor = BacktestingDataExtractor(logger=self.logger)
        self.market_context_extractor = MarketContextExtractor(logger=self.logger)
        self.methodology_extractor = DiscoveryMethodologyExtractor(logger=self.logger)
        self.performance_aggregator = PerformanceMetricsAggregator(
            backtesting_extractor=self.backtesting_extractor, logger=self.logger
        )

        self.logger.info("CrewDataAccessor initialized with enhanced extractors")

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

    def get_consolidated_reporter_input(
        self, max_age_hours: int = 24, current_portfolio_grade: float = 0.70
    ) -> dict[str, Any]:
        """
        Get consolidated data for report generation including A+ opportunities and core analysis.

        This method now includes enhanced data extraction:
        - Backtesting performance metrics from validation results
        - Market context indicators (VIX, inflation, interest rates, regime type)
        - Discovery methodology details (screening criteria, validation statistics)
        - Performance report aggregating metrics across asset types and regimes

        Args:
            max_age_hours: Maximum acceptable age in hours
            current_portfolio_grade: Current portfolio grade (0.0 to 1.0) for impact calculation

        Returns:
            Dictionary containing consolidated data optimized for report generation

        """
        # Get base consolidated reporter input
        reporter_input = self.cache.get_consolidated_reporter_input(max_age_hours)

        if not reporter_input:
            self.logger.warning("No base reporter input available")
            return {}

        try:
            # Extract enhanced data from discovery crew outputs
            backtesting_summary = self.get_backtesting_metrics(max_age_hours)
            market_context_summary = self.get_market_context(max_age_hours)
            methodology_summary = self.get_discovery_methodology(max_age_hours)
            performance_report = self.get_performance_report(max_age_hours, current_portfolio_grade)

            # Add enhanced data to reporter input
            reporter_input["backtesting_summary"] = backtesting_summary
            reporter_input["market_context_summary"] = market_context_summary
            reporter_input["methodology_summary"] = methodology_summary
            reporter_input["performance_report"] = performance_report

            # Log what enhanced data was included
            enhanced_data_status = {
                "has_backtesting": backtesting_summary is not None,
                "has_market_context": market_context_summary is not None,
                "has_methodology": methodology_summary is not None,
                "has_performance_report": performance_report is not None,
            }

            self.logger.info(
                "Enhanced reporter input generated with additional data",
                extra=enhanced_data_status,
            )

            return reporter_input

        except Exception as e:
            self.logger.error(f"Failed to add enhanced data to reporter input: {e}")
            # Return base reporter input even if enhanced data extraction fails
            return reporter_input

    def get_backtesting_metrics(self, max_age_hours: int = 24) -> dict[str, Any] | None:
        """
        Get backtesting performance metrics from discovery crew validation results.

        Args:
            max_age_hours: Maximum acceptable age in hours for discovery data

        Returns:
            Dictionary containing backtesting metrics summary, or None if unavailable

        """
        try:
            # Get discovery data
            discovery_data = self.get_discovery_data(max_age_hours)
            if not discovery_data:
                self.logger.warning("No discovery data available for backtesting metrics extraction")
                return None

            # Extract validation results from discovery data
            validation_results = discovery_data.get("validation_results", [])
            if not validation_results:
                self.logger.warning("No validation results found in discovery data")
                return None

            # Convert to ValidationResult objects if needed
            from finwiz.schemas.investment_discovery import ValidationResult

            vr_objects = []
            for vr_data in validation_results:
                if isinstance(vr_data, ValidationResult):
                    vr_objects.append(vr_data)
                elif isinstance(vr_data, dict):
                    vr_objects.append(ValidationResult(**vr_data))

            if not vr_objects:
                return None

            # Generate backtesting summary
            summary = self.backtesting_extractor.get_performance_summary(vr_objects)

            if summary:
                self.logger.info(
                    f"Extracted backtesting metrics: {summary.total_candidates_tested} candidates tested"
                )
                return summary.model_dump()

            return None

        except Exception as e:
            self.logger.error(f"Failed to extract backtesting metrics: {e}")
            return None

    def get_market_context(self, max_age_hours: int = 24) -> dict[str, Any] | None:
        """
        Get market context indicators from discovery crew outputs.

        Args:
            max_age_hours: Maximum acceptable age in hours for discovery data

        Returns:
            Dictionary containing market context summary, or None if unavailable

        """
        try:
            # Get discovery data
            discovery_data = self.get_discovery_data(max_age_hours)
            if not discovery_data:
                self.logger.warning("No discovery data available for market context extraction")
                return None

            # Extract discovery result
            from finwiz.schemas.investment_discovery import APlusDiscoveryResult

            discovery_result = discovery_data.get("discovery_result")
            if not discovery_result:
                self.logger.warning("No discovery result found in discovery data")
                return None

            # Convert to APlusDiscoveryResult object if needed
            if isinstance(discovery_result, dict):
                discovery_result = APlusDiscoveryResult(**discovery_result)

            # Generate market context summary
            summary = self.market_context_extractor.get_market_context_summary(discovery_result)

            if summary:
                self.logger.info(
                    f"Extracted market context: {summary.market_regime.regime_type} regime, "
                    f"{summary.risk_environment} risk environment"
                )
                return summary.model_dump()

            return None

        except Exception as e:
            self.logger.error(f"Failed to extract market context: {e}")
            return None

    def get_discovery_methodology(self, max_age_hours: int = 24) -> dict[str, Any] | None:
        """
        Get discovery methodology details including screening criteria and validation statistics.

        Args:
            max_age_hours: Maximum acceptable age in hours for discovery data

        Returns:
            Dictionary containing methodology summary, or None if unavailable

        """
        try:
            # Get discovery data
            discovery_data = self.get_discovery_data(max_age_hours)
            if not discovery_data:
                self.logger.warning("No discovery data available for methodology extraction")
                return None

            # Extract discovery result
            from finwiz.schemas.investment_discovery import APlusDiscoveryResult

            discovery_result = discovery_data.get("discovery_result")
            if not discovery_result:
                self.logger.warning("No discovery result found in discovery data")
                return None

            # Convert to APlusDiscoveryResult object if needed
            if isinstance(discovery_result, dict):
                discovery_result = APlusDiscoveryResult(**discovery_result)

            # Generate methodology summary
            summary = self.methodology_extractor.get_methodology_summary(discovery_result)

            if summary:
                self.logger.info(
                    f"Extracted methodology: {summary.validation_statistics.candidates_found} candidates found, "
                    f"{len(summary.score_breakdowns)} score breakdowns"
                )
                return summary.model_dump()

            return None

        except Exception as e:
            self.logger.error(f"Failed to extract discovery methodology: {e}")
            return None

    def get_performance_report(
        self, max_age_hours: int = 24, current_portfolio_grade: float = 0.70
    ) -> dict[str, Any] | None:
        """
        Get comprehensive performance report aggregating metrics across asset types and regimes.

        Args:
            max_age_hours: Maximum acceptable age in hours for discovery data
            current_portfolio_grade: Current portfolio grade (0.0 to 1.0) for impact calculation

        Returns:
            Dictionary containing performance report, or None if unavailable

        """
        try:
            # Get discovery data
            discovery_data = self.get_discovery_data(max_age_hours)
            if not discovery_data:
                self.logger.warning("No discovery data available for performance report generation")
                return None

            # Extract validation results
            validation_results = discovery_data.get("validation_results", [])
            if not validation_results:
                self.logger.warning("No validation results found in discovery data")
                return None

            # Convert to ValidationResult objects if needed
            from finwiz.schemas.investment_discovery import ValidationResult

            vr_objects = []
            for vr_data in validation_results:
                if isinstance(vr_data, ValidationResult):
                    vr_objects.append(vr_data)
                elif isinstance(vr_data, dict):
                    vr_objects.append(ValidationResult(**vr_data))

            if not vr_objects:
                return None

            # Build asset type map from discovery data
            asset_type_map = self._build_asset_type_map(discovery_data)

            # Generate performance report
            report = self.performance_aggregator.generate_performance_report(
                validation_results=vr_objects,
                asset_type_map=asset_type_map,
                current_portfolio_grade=current_portfolio_grade,
            )

            if report:
                self.logger.info(
                    f"Generated performance report: {report.total_candidates_analyzed} candidates, "
                    f"{len(report.top_opportunities)} top opportunities"
                )
                return report.model_dump()

            return None

        except Exception as e:
            self.logger.error(f"Failed to generate performance report: {e}")
            return None

    def _build_asset_type_map(self, discovery_data: dict[str, Any]) -> dict[str, str]:
        """
        Build asset type map from discovery data.

        Args:
            discovery_data: Discovery crew data containing candidate information

        Returns:
            Dictionary mapping symbols to asset types

        """
        asset_type_map: dict[str, str] = {}

        try:
            # Extract asset type from discovery result
            discovery_result = discovery_data.get("discovery_result")
            if discovery_result:
                asset_type = discovery_result.get("asset_type", "stock")

                # Extract all candidate symbols
                a_plus_candidates = discovery_result.get("a_plus_candidates", [])
                for candidate_analysis in a_plus_candidates:
                    candidate = candidate_analysis.get("candidate", {})
                    symbol = candidate.get("symbol")
                    if symbol:
                        asset_type_map[symbol] = asset_type

            # Also check validation results for symbols
            validation_results = discovery_data.get("validation_results", [])
            for vr in validation_results:
                if isinstance(vr, dict):
                    for detail in vr.get("validation_details", []):
                        symbol = detail.get("symbol")
                        if symbol and symbol not in asset_type_map:
                            # Default to stock if not found
                            asset_type_map[symbol] = "stock"

        except Exception as e:
            self.logger.warning(f"Failed to build asset type map: {e}")

        return asset_type_map
