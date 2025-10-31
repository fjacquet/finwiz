"""
Data caching utilities for crew data processing.

This module contains caching logic for crew data access and
consolidated data operations.
"""

from datetime import datetime
from typing import Any

from finwiz.schemas.integration import APlusOpportunityCollection


class DataCache:
    """Handles caching operations for crew data."""

    def __init__(self, integration_manager: Any, logger: Any) -> None:
        """
        Initialize the data cache.

        Args:
            integration_manager: The integration manager instance
            logger: Logger instance for cache operations

        """
        self.integration_manager = integration_manager
        self.logger = logger

    def get_stock_data(self, max_age_hours: int = 24) -> dict[str, Any] | None:
        """
        Get stock crew data with freshness validation.

        Args:
            max_age_hours: Maximum acceptable age in hours

        Returns:
            Stock crew data dictionary, or None if unavailable

        """
        return self.integration_manager.get_crew_data_with_freshness_check("stock", max_age_hours, warn_on_stale=True)

    def get_etf_data(self, max_age_hours: int = 24) -> dict[str, Any] | None:
        """
        Get ETF crew data with freshness validation.

        Args:
            max_age_hours: Maximum acceptable age in hours

        Returns:
            ETF crew data dictionary, or None if unavailable

        """
        return self.integration_manager.get_crew_data_with_freshness_check("etf", max_age_hours, warn_on_stale=True)

    def get_crypto_data(self, max_age_hours: int = 24) -> dict[str, Any] | None:
        """
        Get crypto crew data with freshness validation.

        Args:
            max_age_hours: Maximum acceptable age in hours

        Returns:
            Crypto crew data dictionary, or None if unavailable

        """
        return self.integration_manager.get_crew_data_with_freshness_check("crypto", max_age_hours, warn_on_stale=True)

    def get_discovery_data(self, max_age_hours: int = 24) -> dict[str, Any] | None:
        """
        Get discovery crew data with freshness validation.

        Args:
            max_age_hours: Maximum acceptable age in hours

        Returns:
            Discovery crew data dictionary, or None if unavailable

        """
        return self.integration_manager.get_crew_data_with_freshness_check("discovery", max_age_hours, warn_on_stale=True)

    def get_consolidated_data(self, max_age_hours: int = 24) -> dict[str, Any]:
        """
        Get consolidated data from all available crews.

        Args:
            max_age_hours: Maximum acceptable age in hours

        Returns:
            Dictionary containing all available crew data

        """
        from .data_transformation import serialize_datetime_objects

        consolidated = {}

        try:
            # Get data from each crew
            crews = ["stock", "etf", "crypto", "discovery", "portfolio"]

            for crew_name in crews:
                crew_data = self.integration_manager.get_crew_data_with_freshness_check(crew_name, max_age_hours, warn_on_stale=True)

                if crew_data:
                    # Validate that the data is not empty
                    if isinstance(crew_data, dict) and len(crew_data) > 0:
                        consolidated[crew_name] = crew_data
                        self.logger.debug(
                            f"Successfully retrieved {crew_name} crew data",
                            extra={"data_size": len(str(crew_data)), "keys": list(crew_data.keys())[:5]},
                        )
                    else:
                        self.logger.warning(
                            f"Retrieved {crew_name} crew data but it appears empty",
                            extra={
                                "data_type": type(crew_data),
                                "data_length": len(crew_data) if hasattr(crew_data, "__len__") else "N/A",
                            },
                        )
                else:
                    self.logger.warning(f"No data available for {crew_name} crew")

            self.logger.info(f"Consolidated data from {len(consolidated)} crews", extra={"crews": list(consolidated.keys())})

            # Serialize datetime objects for CrewAI compatibility
            serialized_consolidated = serialize_datetime_objects(consolidated)

            return serialized_consolidated

        except Exception as e:
            self.logger.error(f"Failed to consolidate data: {str(e)}", exc_info=True)
            return {}

    def get_aplus_opportunities(self, max_age_hours: int = 24) -> APlusOpportunityCollection | None:
        """
        Get A+ investment opportunities from discovery crew outputs.

        Args:
            max_age_hours: Maximum acceptable age in hours for discovery data

        Returns:
            APlusOpportunityCollection with extracted opportunities, or None if unavailable

        """
        try:
            # Check if discovery data is available and fresh
            discovery_data = self.integration_manager.get_crew_data_with_freshness_check("discovery", max_age_hours, warn_on_stale=True)

            if not discovery_data:
                self.logger.warning("No discovery data available for A+ opportunity extraction")
                return None

            # Extract A+ opportunities using the extractor
            from .aplus_extractor import APlusDataExtractor

            aplus_extractor = APlusDataExtractor(self.integration_manager.output_dir)
            opportunities = aplus_extractor.extract_aplus_opportunities()

            if opportunities:
                self.logger.info(
                    "A+ opportunities extracted successfully",
                    extra={
                        "stock_count": len(opportunities.stock_opportunities),
                        "etf_count": len(opportunities.etf_opportunities),
                        "crypto_count": len(opportunities.crypto_opportunities),
                        "confidence_score": opportunities.confidence_score,
                    },
                )

                return opportunities
            else:
                self.logger.warning("No A+ opportunities could be extracted from discovery data")
                return None

        except Exception as e:
            self.logger.error(f"Failed to extract A+ opportunities: {str(e)}", exc_info=True)
            return None

    def get_consolidated_reporter_input(self, max_age_hours: int = 24) -> dict[str, Any]:
        """
        Get consolidated data for report generation including A+ opportunities and core analysis.

        This method now includes enhanced data extraction:
        - Backtesting performance metrics from validation results
        - Market context indicators (VIX, inflation, interest rates, regime type)
        - Discovery methodology details (screening criteria, validation statistics)
        - Performance report aggregating metrics across asset types and regimes

        Args:
            max_age_hours: Maximum acceptable age in hours

        Returns:
            Dictionary containing consolidated data optimized for report generation

        """
        from .data_transformation import generate_core_analysis_summary, serialize_datetime_objects

        try:
            # Get consolidated crew data
            consolidated_data = self.get_consolidated_data(max_age_hours)

            if not consolidated_data:
                self.logger.warning("No consolidated data available for reporter input")
                return {}

            # Get A+ opportunities
            aplus_opportunities = self.get_aplus_opportunities(max_age_hours)

            # Generate core analysis summary
            core_analysis_summary = generate_core_analysis_summary(consolidated_data, max_age_hours)

            # Generate portfolio allocation updates if A+ opportunities exist
            portfolio_allocation_updates = []
            if aplus_opportunities:
                portfolio_allocation_updates = self._generate_portfolio_allocation_updates(aplus_opportunities)

            # Create comprehensive reporter input
            reporter_input = {
                "consolidated_crew_data": consolidated_data,
                "core_analysis_summary": core_analysis_summary,
                "aplus_opportunities": aplus_opportunities.model_dump() if aplus_opportunities else None,
                "aplus_availability_status": self._get_aplus_availability_status(aplus_opportunities),
                "portfolio_allocation_updates": portfolio_allocation_updates,
                "data_freshness_hours": max_age_hours,
                "report_generation_timestamp": datetime.now(),
                "data_sources": list(consolidated_data.keys()),
                "total_data_points": sum(len(crew_data) if isinstance(crew_data, dict) else 0 for crew_data in consolidated_data.values()),
            }

            # Serialize for CrewAI compatibility
            serialized_input = serialize_datetime_objects(reporter_input)

            self.logger.info(
                "Reporter input generated successfully",
                extra={
                    "data_sources": len(consolidated_data),
                    "has_aplus_opportunities": aplus_opportunities is not None,
                    "total_data_points": reporter_input["total_data_points"],
                },
            )

            return serialized_input

        except Exception as e:
            self.logger.error(f"Failed to generate reporter input: {str(e)}", exc_info=True)
            return {}

    def _generate_portfolio_allocation_updates(self, opportunities: APlusOpportunityCollection) -> list[dict[str, Any]]:
        """
        Generate portfolio allocation updates based on A+ opportunities.

        Args:
            opportunities: A+ opportunities collection

        Returns:
            List of portfolio allocation update recommendations

        """
        try:
            allocation_updates = []

            # Process stock opportunities
            for stock_opp in opportunities.stock_opportunities:
                if hasattr(stock_opp, "allocation_recommendation") and stock_opp.allocation_recommendation:
                    allocation_pct = self._parse_allocation_percentage(stock_opp.allocation_recommendation)
                    if allocation_pct:
                        allocation_updates.append(
                            {
                                "asset_type": "stock",
                                "symbol": stock_opp.symbol,
                                "company_name": getattr(stock_opp, "company_name", stock_opp.symbol),
                                "recommended_allocation": allocation_pct,
                                "rationale": getattr(stock_opp, "investment_thesis", "A+ opportunity identified"),
                                "confidence_score": getattr(stock_opp, "confidence_score", 0.8),
                                "risk_level": getattr(stock_opp, "risk_assessment", "MODERATE"),
                                "time_horizon": getattr(stock_opp, "time_horizon", "MEDIUM"),
                            }
                        )

            # Process ETF opportunities
            for etf_opp in opportunities.etf_opportunities:
                if hasattr(etf_opp, "allocation_recommendation") and etf_opp.allocation_recommendation:
                    allocation_pct = self._parse_allocation_percentage(etf_opp.allocation_recommendation)
                    if allocation_pct:
                        allocation_updates.append(
                            {
                                "asset_type": "etf",
                                "symbol": etf_opp.symbol,
                                "fund_name": getattr(etf_opp, "fund_name", etf_opp.symbol),
                                "recommended_allocation": allocation_pct,
                                "rationale": getattr(etf_opp, "investment_thesis", "A+ ETF opportunity identified"),
                                "confidence_score": getattr(etf_opp, "confidence_score", 0.8),
                                "expense_ratio": getattr(etf_opp, "expense_ratio", None),
                                "diversification_benefit": getattr(etf_opp, "diversification_benefit", "HIGH"),
                            }
                        )

            # Process crypto opportunities
            for crypto_opp in opportunities.crypto_opportunities:
                if hasattr(crypto_opp, "allocation_recommendation") and crypto_opp.allocation_recommendation:
                    allocation_pct = self._parse_allocation_percentage(crypto_opp.allocation_recommendation)
                    if allocation_pct:
                        allocation_updates.append(
                            {
                                "asset_type": "crypto",
                                "symbol": crypto_opp.symbol,
                                "crypto_name": getattr(crypto_opp, "crypto_name", crypto_opp.symbol),
                                "recommended_allocation": allocation_pct,
                                "rationale": getattr(crypto_opp, "investment_thesis", "A+ crypto opportunity identified"),
                                "confidence_score": getattr(crypto_opp, "confidence_score", 0.7),
                                "volatility_warning": True,
                                "risk_level": "HIGH",
                            }
                        )

            # Sort by confidence score and allocation percentage
            allocation_updates.sort(key=lambda x: (x["confidence_score"], x["recommended_allocation"]), reverse=True)

            return allocation_updates

        except Exception as e:
            self.logger.error(f"Failed to generate portfolio allocation updates: {str(e)}", exc_info=True)
            return []

    def _parse_allocation_percentage(self, allocation_text: str) -> float | None:
        """
        Parse allocation percentage from text.

        Args:
            allocation_text: Text containing allocation percentage

        Returns:
            Allocation percentage as float, or None if not parseable

        """
        try:
            import re

            # Look for percentage patterns
            percentage_patterns = [
                r"(\d+(?:\.\d+)?)\s*%",  # "5.5%", "10%"
                r"(\d+(?:\.\d+)?)\s*percent",  # "5.5 percent"
                r"allocate\s+(\d+(?:\.\d+)?)\s*%",  # "allocate 5%"
                r"(\d+(?:\.\d+)?)\s*percentage",  # "5.5 percentage"
            ]

            for pattern in percentage_patterns:
                match = re.search(pattern, allocation_text.lower())
                if match:
                    percentage = float(match.group(1))
                    # Ensure reasonable range (0-50% for individual positions)
                    if 0.1 <= percentage <= 50.0:
                        return percentage

            return None

        except Exception:
            return None

    def _get_aplus_availability_status(self, opportunities: APlusOpportunityCollection | None) -> dict[str, Any]:
        """
        Get A+ opportunities availability status.

        Args:
            opportunities: The A+ opportunities collection or None

        Returns:
            Dictionary with availability status information

        """
        if not opportunities:
            return {
                "available": False,
                "status": "UNAVAILABLE",
                "reason": "No A+ opportunities could be extracted from discovery data",
                "total_opportunities": 0,
                "by_asset_type": {"stocks": 0, "etfs": 0, "cryptos": 0},
            }

        total_opportunities = len(opportunities.stock_opportunities) + len(opportunities.etf_opportunities) + len(opportunities.crypto_opportunities)

        if total_opportunities == 0:
            status = "EMPTY"
        elif opportunities.confidence_score >= 0.8:
            status = "HIGH_CONFIDENCE"
        elif opportunities.confidence_score >= 0.6:
            status = "MEDIUM_CONFIDENCE"
        else:
            status = "LOW_CONFIDENCE"

        return {
            "available": True,
            "status": status,
            "confidence_score": opportunities.confidence_score,
            "total_opportunities": total_opportunities,
            "by_asset_type": {
                "stocks": len(opportunities.stock_opportunities),
                "etfs": len(opportunities.etf_opportunities),
                "cryptos": len(opportunities.crypto_opportunities),
            },
            "validation_timestamp": opportunities.validation_timestamp.isoformat(),
            "has_allocation_recommendations": len(opportunities.allocation_recommendations) > 0,
            "has_replacement_notes": len(opportunities.replacement_notes) > 0,
        }

    def get_consolidated_market_sentiment(self, max_age_hours: int = 24) -> dict[str, Any]:
        """
        Consolidate market sentiment data from all crews.

        Args:
            max_age_hours: Maximum acceptable age in hours

        Returns:
            Dictionary containing consolidated sentiment data

        """
        from .data_transformation import (
            consolidate_market_sentiment_data,
            create_error_response_for_sentiment,
        )

        try:
            # Get consolidated crew data
            consolidated_data = self.get_consolidated_data(max_age_hours)

            # Use transformation module to consolidate sentiment
            result = consolidate_market_sentiment_data(consolidated_data)

            self.logger.info(f"Consolidated sentiment data from {len(result['crew_sentiments'])} crews, {result['aggregated_scores']['total_sources']} total sources")

            return result

        except Exception as e:
            self.logger.error(f"Failed to consolidate market sentiment: {str(e)}", exc_info=True)
            return create_error_response_for_sentiment(str(e))

    def get_consolidated_ticker_validation(self, max_age_hours: int = 24) -> dict[str, Any]:
        """
        Consolidate ticker validation results from all crews.

        Args:
            max_age_hours: Maximum acceptable age in hours

        Returns:
            Dictionary containing consolidated ticker validation

        """
        from .data_transformation import (
            consolidate_ticker_validation_data,
            create_error_response_for_ticker_validation,
        )

        try:
            # Get consolidated crew data
            consolidated_data = self.get_consolidated_data(max_age_hours)

            # Use transformation module to consolidate ticker validation
            result = consolidate_ticker_validation_data(consolidated_data)

            self.logger.info(
                f"Consolidated ticker validation: {result['validation_summary']['valid_symbols']}/"
                f"{result['validation_summary']['total_symbols']} symbols valid "
                f"({result['validation_summary']['validation_rate']:.1f}%)"
            )

            return result

        except Exception as e:
            self.logger.error(f"Failed to consolidate ticker validation: {str(e)}", exc_info=True)
            return create_error_response_for_ticker_validation(str(e))
