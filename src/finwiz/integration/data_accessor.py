"""
Crew Data Accessor for unified data access with freshness validation.

This module provides a unified interface for accessing crew data with
automatic freshness checking and validation.
"""

from datetime import datetime
from typing import Any

from ..schemas.integration import (
    APlusOpportunityCollection,
    DataAvailabilityReport,
    DataAvailabilityStatus,
    IntegrationError,
    IntegrationErrorType,
)
from .aplus_extractor import APlusDataExtractor
from .manager import CrewDataIntegrationManager


def serialize_datetime_objects(obj: Any, _seen: set | None = None) -> Any:
    """
    Recursively serialize datetime objects and other non-serializable types to CrewAI-compatible formats.

    This is required for CrewAI compatibility as it only accepts
    str, int, float, bool, dict, and list types in inputs.

    Args:
        obj: Object that may contain datetime objects or other non-serializable types
        _seen: Set to track visited objects to prevent infinite recursion

    Returns:
        Object with all non-serializable types converted to compatible formats

    """
    if _seen is None:
        _seen = set()

    # Prevent infinite recursion
    obj_id = id(obj)
    if obj_id in _seen:
        return f"<circular reference to {type(obj).__name__}>"

    # For basic types that CrewAI accepts, return as-is
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj

    # Add to seen set for complex objects
    _seen.add(obj_id)

    try:
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {key: serialize_datetime_objects(value, _seen) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [serialize_datetime_objects(item, _seen) for item in obj]
        elif isinstance(obj, tuple):
            return [serialize_datetime_objects(item, _seen) for item in obj]
        elif isinstance(obj, set):
            return [serialize_datetime_objects(item, _seen) for item in obj]
        elif hasattr(obj, "items") and callable(getattr(obj, "items")):
            # Handle mappingproxy and other dict-like objects
            return {key: serialize_datetime_objects(value, _seen) for key, value in obj.items()}
        elif hasattr(obj, "model_dump"):
            # Pydantic v2 model
            return serialize_datetime_objects(obj.model_dump(), _seen)
        elif hasattr(obj, "dict"):
            # Pydantic v1 model
            return serialize_datetime_objects(obj.dict(), _seen)
        elif hasattr(obj, "__dict__"):
            # Generic object with __dict__ - but avoid certain types
            if type(obj).__name__ in ["CrewDataAccessor", "CrewDataIntegrationManager", "APlusDataExtractor"]:
                return f"<{type(obj).__name__} instance>"
            return serialize_datetime_objects(obj.__dict__, _seen)
        elif hasattr(obj, "__iter__") and not isinstance(obj, (str, bytes)):
            # Handle other iterable types (but not strings/bytes)
            try:
                return [serialize_datetime_objects(item, _seen) for item in obj]
            except (TypeError, RecursionError):
                # If iteration fails, convert to string
                return str(obj)
        else:
            # Convert other types to string representation
            return str(obj)
    finally:
        # Remove from seen set when done processing
        _seen.discard(obj_id)


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
        self.aplus_extractor = APlusDataExtractor(integration_manager.output_dir)

        self.logger.info("CrewDataAccessor initialized")

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
        consolidated = {}

        try:
            # Get data from each crew
            crews = ["stock", "etf", "crypto", "discovery", "portfolio"]

            for crew_name in crews:
                crew_data = self.integration_manager.get_crew_data_with_freshness_check(
                    crew_name, max_age_hours, warn_on_stale=True
                )

                if crew_data:
                    consolidated[crew_name] = crew_data
                else:
                    self.logger.warning(f"No data available for {crew_name} crew")

            self.logger.info(f"Consolidated data from {len(consolidated)} crews")

            # Serialize datetime objects for CrewAI compatibility
            serialized_consolidated = serialize_datetime_objects(consolidated)

            return serialized_consolidated

        except Exception as e:
            self.logger.error(f"Failed to consolidate data: {str(e)}", exc_info=True)
            return {}

    def check_data_availability(self, max_age_hours: int = 24) -> DataAvailabilityReport:
        """
        Check availability of data across all crews.

        Args:
            max_age_hours: Maximum acceptable age in hours

        Returns:
            DataAvailabilityReport with detailed availability status

        """
        try:
            # Get freshness report
            freshness_report = self.integration_manager.check_data_freshness(max_age_hours)

            # Check individual crew availability
            stock_available = "stock" in freshness_report.fresh_data or "stock" in freshness_report.stale_data
            etf_available = "etf" in freshness_report.fresh_data or "etf" in freshness_report.stale_data
            crypto_available = "crypto" in freshness_report.fresh_data or "crypto" in freshness_report.stale_data
            discovery_available = "discovery" in freshness_report.fresh_data or "discovery" in freshness_report.stale_data
            portfolio_available = "portfolio" in freshness_report.fresh_data or "portfolio" in freshness_report.stale_data

            # Create integration errors for missing/stale data
            integration_errors = []

            for crew_name in freshness_report.missing_data:
                integration_errors.append(
                    IntegrationError(
                        error_type=IntegrationErrorType.MISSING_DATA,
                        crew_name=crew_name,
                        error_message=f"No data found for {crew_name} crew",
                        expected_path=str(self.integration_manager.output_dir / crew_name),
                        recovery_suggestions=[
                            f"Run {crew_name} crew to generate initial data",
                            f"Check if {crew_name} crew execution completed successfully",
                        ],
                        timestamp=freshness_report.check_timestamp,
                    )
                )

            for crew_name in freshness_report.stale_data:
                integration_errors.append(
                    IntegrationError(
                        error_type=IntegrationErrorType.STALE_DATA,
                        crew_name=crew_name,
                        error_message=f"Stale data detected for {crew_name} crew",
                        recovery_suggestions=[
                            f"Re-run {crew_name} crew to refresh data",
                            "Check if crew execution schedule needs adjustment",
                        ],
                        timestamp=freshness_report.check_timestamp,
                    )
                )

            # Determine overall status
            total_crews = 5
            available_crews = sum([stock_available, etf_available, crypto_available, discovery_available, portfolio_available])

            if available_crews == 0:
                overall_status = DataAvailabilityStatus.UNAVAILABLE
            elif available_crews < total_crews // 2:
                overall_status = DataAvailabilityStatus.INSUFFICIENT
            elif len(freshness_report.stale_data) > 0 or len(freshness_report.missing_data) > 0:
                overall_status = DataAvailabilityStatus.PARTIAL
            else:
                overall_status = DataAvailabilityStatus.COMPLETE

            # Create freshness summary
            data_freshness_summary = {
                "fresh_crews": len(freshness_report.fresh_data),
                "stale_crews": len(freshness_report.stale_data),
                "missing_crews": len(freshness_report.missing_data),
                "total_crews": total_crews,
                "freshness_threshold_hours": max_age_hours,
            }

            # Generate recommendations
            recommendations = list(freshness_report.recommendations)
            if len(freshness_report.stale_data) > 0:
                refresh_order = self.integration_manager.get_refresh_recommendations(max_age_hours)
                if refresh_order:
                    recommendations.append(f"Recommended refresh order: {' -> '.join(refresh_order)}")

            report = DataAvailabilityReport(
                stock_available=stock_available,
                etf_available=etf_available,
                crypto_available=crypto_available,
                discovery_available=discovery_available,
                portfolio_available=portfolio_available,
                missing_data=freshness_report.missing_data,
                stale_data=freshness_report.stale_data,
                integration_errors=integration_errors,
                overall_status=overall_status,
                report_timestamp=freshness_report.check_timestamp,
                data_freshness_summary=data_freshness_summary,
                recommendations=recommendations,
            )

            self.logger.info(
                "Data availability check completed",
                extra={"overall_status": overall_status.value, "available_crews": available_crews, "total_crews": total_crews},
            )

            return report

        except Exception as e:
            self.logger.error(f"Data availability check failed: {str(e)}", exc_info=True)

            # Return error report
            return DataAvailabilityReport(
                stock_available=False,
                etf_available=False,
                crypto_available=False,
                discovery_available=False,
                portfolio_available=False,
                missing_data=["stock", "etf", "crypto", "discovery", "portfolio"],
                stale_data=[],
                integration_errors=[
                    IntegrationError(
                        error_type=IntegrationErrorType.ACCESS_ERROR,
                        crew_name="system",
                        error_message=f"Data availability check failed: {str(e)}",
                        recovery_suggestions=["Check system logs", "Restart integration system"],
                        timestamp=datetime.now(),
                    )
                ],
                overall_status=DataAvailabilityStatus.UNAVAILABLE,
                report_timestamp=datetime.now(),
                data_freshness_summary={},
                recommendations=["Fix data availability checker and retry"],
            )

    def get_stale_data_warnings(self, max_age_hours: int = 24) -> list[str]:
        """
        Get list of warnings for stale data.

        Args:
            max_age_hours: Maximum acceptable age in hours

        Returns:
            List of warning messages for stale data

        """
        try:
            freshness_report = self.integration_manager.check_data_freshness(max_age_hours)
            warnings = []

            for crew_name in freshness_report.stale_data:
                # Get specific freshness info for this crew
                freshness_result = self.integration_manager.freshness_checker.check_data_freshness_for_crew(
                    crew_name, max_age_hours
                )

                if freshness_result:
                    age_hours = freshness_result.freshness_status.age_hours
                    warnings.append(
                        f"Stale data warning: {crew_name} crew data is {age_hours:.1f} hours old (threshold: {max_age_hours} hours)"
                    )
                else:
                    warnings.append(f"Stale data warning: {crew_name} crew data age unknown")

            return warnings

        except Exception as e:
            self.logger.error(f"Failed to get stale data warnings: {str(e)}", exc_info=True)
            return [f"Error checking data staleness: {str(e)}"]

    def get_consolidated_market_sentiment(self, max_age_hours: int = 24) -> dict[str, Any]:
        """
        Consolidate market sentiment data from all crews.

        Args:
            max_age_hours: Maximum acceptable age in hours

        Returns:
            Dictionary containing consolidated sentiment data with:
            - aggregated_scores: Overall sentiment distribution
            - top_sources: Top 3 sentiment sources with URLs and dates
            - crew_sentiments: Individual crew sentiment data
            - data_quality: Quality assessment of sentiment data

        """
        try:
            consolidated_sentiment = {
                "aggregated_scores": {"positive": 0.0, "neutral": 0.0, "negative": 0.0, "total_sources": 0},
                "top_sources": [],
                "crew_sentiments": {},
                "data_quality": "HIGH",
                "consolidation_timestamp": datetime.now(),
            }

            all_sources = []
            total_positive = 0.0
            total_neutral = 0.0
            total_negative = 0.0
            total_weight = 0.0

            # Get sentiment data from each crew
            crews_with_sentiment = ["stock", "crypto"]  # ETF typically doesn't have sentiment

            for crew_name in crews_with_sentiment:
                crew_data = self.integration_manager.get_crew_data_with_freshness_check(
                    crew_name, max_age_hours, warn_on_stale=True
                )

                if not crew_data:
                    self.logger.warning(f"No {crew_name} data available for sentiment consolidation")
                    continue

                # Extract sentiment data based on crew structure
                crew_sentiments = []
                if crew_name == "stock" and "market_sentiments" in crew_data:
                    crew_sentiments = crew_data["market_sentiments"]
                elif crew_name == "crypto" and "market_analysis" in crew_data:
                    # Extract sentiment from crypto market analysis
                    market_analysis = crew_data["market_analysis"]
                    if isinstance(market_analysis, list):
                        for analysis in market_analysis:
                            if "sentiment" in analysis:
                                crew_sentiments.append(analysis["sentiment"])
                    elif isinstance(market_analysis, dict) and "sentiment" in market_analysis:
                        crew_sentiments.append(market_analysis["sentiment"])

                if not crew_sentiments:
                    self.logger.info(f"No sentiment data found in {crew_name} crew output")
                    continue

                # Process sentiment data for this crew
                crew_sentiment_summary = {"positive": 0.0, "neutral": 0.0, "negative": 0.0, "source_count": 0, "sources": []}

                for sentiment in crew_sentiments:
                    if not isinstance(sentiment, dict):
                        continue

                    # Extract sentiment scores (normalize different formats)
                    pos_score = sentiment.get("positive", sentiment.get("positive_score", 0.0))
                    neu_score = sentiment.get("neutral", sentiment.get("neutral_score", 0.0))
                    neg_score = sentiment.get("negative", sentiment.get("negative_score", 0.0))

                    # Normalize scores if they're percentages
                    if pos_score > 1.0 or neu_score > 1.0 or neg_score > 1.0:
                        total_score = pos_score + neu_score + neg_score
                        if total_score > 0:
                            pos_score /= total_score
                            neu_score /= total_score
                            neg_score /= total_score

                    crew_sentiment_summary["positive"] += pos_score
                    crew_sentiment_summary["neutral"] += neu_score
                    crew_sentiment_summary["negative"] += neg_score
                    crew_sentiment_summary["source_count"] += 1

                    # Collect source information
                    source_info = {
                        "crew": crew_name,
                        "url": sentiment.get("source_url", sentiment.get("url", "")),
                        "date": sentiment.get("date", sentiment.get("published_date", "")),
                        "source_name": sentiment.get("source", sentiment.get("source_name", f"{crew_name}_analysis")),
                        "sentiment_score": pos_score - neg_score,  # Net sentiment
                        "confidence": sentiment.get("confidence", 0.5),
                    }

                    all_sources.append(source_info)
                    crew_sentiment_summary["sources"].append(source_info)

                # Average the crew sentiment scores
                if crew_sentiment_summary["source_count"] > 0:
                    count = crew_sentiment_summary["source_count"]
                    crew_sentiment_summary["positive"] /= count
                    crew_sentiment_summary["neutral"] /= count
                    crew_sentiment_summary["negative"] /= count

                    # Add to overall totals (weight by source count)
                    weight = count
                    total_positive += crew_sentiment_summary["positive"] * weight
                    total_neutral += crew_sentiment_summary["neutral"] * weight
                    total_negative += crew_sentiment_summary["negative"] * weight
                    total_weight += weight

                consolidated_sentiment["crew_sentiments"][crew_name] = crew_sentiment_summary

            # Calculate overall aggregated scores
            if total_weight > 0:
                consolidated_sentiment["aggregated_scores"]["positive"] = total_positive / total_weight
                consolidated_sentiment["aggregated_scores"]["neutral"] = total_neutral / total_weight
                consolidated_sentiment["aggregated_scores"]["negative"] = total_negative / total_weight
                consolidated_sentiment["aggregated_scores"]["total_sources"] = len(all_sources)

            # Get top 3 sources by confidence and sentiment strength
            if all_sources:
                # Sort by confidence and absolute sentiment score
                sorted_sources = sorted(all_sources, key=lambda x: (x["confidence"], abs(x["sentiment_score"])), reverse=True)

                consolidated_sentiment["top_sources"] = sorted_sources[:3]

            # Assess data quality
            if len(all_sources) >= 5:
                consolidated_sentiment["data_quality"] = "HIGH"
            elif len(all_sources) >= 2:
                consolidated_sentiment["data_quality"] = "MEDIUM"
            elif len(all_sources) >= 1:
                consolidated_sentiment["data_quality"] = "LOW"
            else:
                consolidated_sentiment["data_quality"] = "INSUFFICIENT"

            self.logger.info(
                f"Consolidated sentiment data from {len(consolidated_sentiment['crew_sentiments'])} crews, "
                f"{len(all_sources)} total sources"
            )

            return consolidated_sentiment

        except Exception as e:
            self.logger.error(f"Failed to consolidate market sentiment: {str(e)}", exc_info=True)
            return {
                "aggregated_scores": {"positive": 0.0, "neutral": 0.0, "negative": 0.0, "total_sources": 0},
                "top_sources": [],
                "crew_sentiments": {},
                "data_quality": "ERROR",
                "consolidation_timestamp": datetime.now(),
                "error": str(e),
            }

    def get_consolidated_ticker_validation(self, max_age_hours: int = 24) -> dict[str, Any]:
        """
        Consolidate ticker validation results from all crews.

        Args:
            max_age_hours: Maximum acceptable age in hours

        Returns:
            Dictionary containing consolidated ticker validation with:
            - validated_tickers: All validated stock tickers
            - validated_etfs: All validated ETF tickers
            - validated_cryptos: All validated crypto symbols
            - validation_summary: Summary of validation results
            - failed_validations: Failed validations with alternatives

        """
        try:
            consolidated_validation = {
                "validated_tickers": [],
                "validated_etfs": [],
                "validated_cryptos": [],
                "validation_summary": {"total_symbols": 0, "valid_symbols": 0, "invalid_symbols": 0, "validation_rate": 0.0},
                "failed_validations": [],
                "consolidation_timestamp": datetime.now(),
            }

            # Get validation data from each crew
            crew_mappings = {
                "stock": ("validated_tickers", "validated_tickers"),
                "etf": ("validated_etfs", "validated_etfs"),
                "crypto": ("validated_symbols", "validated_cryptos"),
            }

            total_symbols = 0
            valid_symbols = 0

            for crew_name, (source_key, target_key) in crew_mappings.items():
                crew_data = self.integration_manager.get_crew_data_with_freshness_check(
                    crew_name, max_age_hours, warn_on_stale=True
                )

                if not crew_data:
                    self.logger.warning(f"No {crew_name} data available for ticker validation consolidation")
                    continue

                # Extract validation data
                validation_data = crew_data.get(source_key, [])
                if not validation_data:
                    self.logger.info(f"No validation data found in {crew_name} crew output")
                    continue

                # Process validation results
                for validation in validation_data:
                    if not isinstance(validation, dict):
                        continue

                    total_symbols += 1

                    # Standardize validation format
                    standardized_validation = {
                        "symbol": validation.get("symbol", ""),
                        "is_valid": validation.get("is_valid", False),
                        "validation_source": validation.get("validation_source", f"{crew_name}_crew"),
                        "validation_timestamp": validation.get("validation_timestamp", datetime.now().isoformat()),
                        "crew_source": crew_name,
                        "market": validation.get("market", ""),
                        "sector": validation.get("sector", ""),
                        "company_name": validation.get("company_name", validation.get("full_name", "")),
                        "validation_errors": validation.get("validation_errors", []),
                        "alternative_suggestions": validation.get("alternative_suggestions", []),
                    }

                    # Add to appropriate category
                    consolidated_validation[target_key].append(standardized_validation)

                    if standardized_validation["is_valid"]:
                        valid_symbols += 1
                    else:
                        # Add to failed validations with recovery suggestions
                        failed_validation = {
                            "symbol": standardized_validation["symbol"],
                            "crew": crew_name,
                            "errors": standardized_validation["validation_errors"],
                            "alternatives": standardized_validation["alternative_suggestions"],
                            "recovery_suggestions": [
                                f"Verify {standardized_validation['symbol']} symbol spelling",
                                f"Check if {standardized_validation['symbol']} is actively traded",
                                "Consider using alternative symbols if available",
                            ],
                        }

                        if standardized_validation["alternative_suggestions"]:
                            failed_validation["recovery_suggestions"].append(
                                f"Try alternatives: {', '.join(standardized_validation['alternative_suggestions'][:3])}"
                            )

                        consolidated_validation["failed_validations"].append(failed_validation)

            # Calculate validation summary
            consolidated_validation["validation_summary"] = {
                "total_symbols": total_symbols,
                "valid_symbols": valid_symbols,
                "invalid_symbols": total_symbols - valid_symbols,
                "validation_rate": (valid_symbols / total_symbols * 100) if total_symbols > 0 else 0.0,
            }

            self.logger.info(
                f"Consolidated ticker validation: {valid_symbols}/{total_symbols} symbols valid "
                f"({consolidated_validation['validation_summary']['validation_rate']:.1f}%)"
            )

            return consolidated_validation

        except Exception as e:
            self.logger.error(f"Failed to consolidate ticker validation: {str(e)}", exc_info=True)
            return {
                "validated_tickers": [],
                "validated_etfs": [],
                "validated_cryptos": [],
                "validation_summary": {"total_symbols": 0, "valid_symbols": 0, "invalid_symbols": 0, "validation_rate": 0.0},
                "failed_validations": [],
                "consolidation_timestamp": datetime.now(),
                "error": str(e),
            }

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
            discovery_data = self.integration_manager.get_crew_data_with_freshness_check(
                "discovery", max_age_hours, warn_on_stale=True
            )

            if not discovery_data:
                self.logger.warning("No discovery data available for A+ opportunity extraction")
                return None

            # Extract A+ opportunities using the extractor
            opportunities = self.aplus_extractor.extract_aplus_opportunities()

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
            else:
                self.logger.warning("No A+ opportunities could be extracted from discovery data")

            return opportunities

        except Exception as e:
            self.logger.error(f"Failed to get A+ opportunities: {str(e)}", exc_info=True)
            return None

    def get_consolidated_reporter_input(self, max_age_hours: int = 24) -> dict[str, Any]:
        """
        Get consolidated data for report generation including A+ opportunities and core analysis.

        Args:
            max_age_hours: Maximum acceptable age in hours

        Returns:
            Dictionary containing all consolidated data for report generation

        """
        try:
            # Get base consolidated data (includes core analysis crews)
            consolidated = self.get_consolidated_data(max_age_hours)

            # Add market sentiment consolidation (enhanced with core analysis)
            consolidated["market_sentiment"] = self.get_consolidated_market_sentiment(max_age_hours)

            # Add ticker validation consolidation (enhanced with core analysis)
            consolidated["ticker_validation"] = self.get_consolidated_ticker_validation(max_age_hours)

            # Add core analysis summary for easy access
            consolidated["core_analysis_summary"] = self._generate_core_analysis_summary(consolidated, max_age_hours)

            # Add A+ opportunities
            aplus_opportunities = self.get_aplus_opportunities(max_age_hours)
            if aplus_opportunities:
                consolidated["aplus_opportunities"] = {
                    "stock_opportunities": aplus_opportunities.stock_opportunities,
                    "etf_opportunities": aplus_opportunities.etf_opportunities,
                    "crypto_opportunities": aplus_opportunities.crypto_opportunities,
                    "discovery_summary": aplus_opportunities.discovery_summary,
                    "confidence_score": aplus_opportunities.confidence_score,
                    "allocation_recommendations": aplus_opportunities.allocation_recommendations,
                    "replacement_notes": aplus_opportunities.replacement_notes,
                    "validation_timestamp": aplus_opportunities.validation_timestamp.isoformat(),
                }

                # Update portfolio allocation recommendations based on A+ opportunities
                consolidated["portfolio_allocation_updates"] = self._generate_portfolio_allocation_updates(aplus_opportunities)
            else:
                consolidated["aplus_opportunities"] = None
                consolidated["portfolio_allocation_updates"] = []

            # Add A+ availability status
            consolidated["aplus_availability_status"] = self._get_aplus_availability_status(aplus_opportunities)

            # Add data availability report
            consolidated["data_availability"] = self.check_data_availability(max_age_hours)

            # Count core analysis crews specifically
            core_analysis_count = len([k for k in consolidated.keys() if k in ["stock", "etf", "crypto"]])
            total_crew_count = len([k for k in consolidated.keys() if k in ["stock", "etf", "crypto", "discovery", "portfolio"]])

            self.logger.info(
                "Consolidated reporter input generated successfully with core analysis integration",
                extra={
                    "total_crew_count": total_crew_count,
                    "core_analysis_count": core_analysis_count,
                    "has_aplus": aplus_opportunities is not None,
                    "has_sentiment": "market_sentiment" in consolidated,
                    "has_validation": "ticker_validation" in consolidated,
                    "has_core_summary": "core_analysis_summary" in consolidated,
                },
            )

            # Serialize datetime objects for CrewAI compatibility
            serialized_consolidated = serialize_datetime_objects(consolidated)

            return serialized_consolidated

        except Exception as e:
            self.logger.error(f"Failed to generate consolidated reporter input: {str(e)}", exc_info=True)
            return {}

    def _generate_core_analysis_summary(self, consolidated_data: dict[str, Any], max_age_hours: int) -> dict[str, Any]:
        """
        Generate a summary of core analysis results for easy consumption.

        Args:
            consolidated_data: The consolidated data containing core analysis results
            max_age_hours: Maximum acceptable age in hours

        Returns:
            Dictionary with core analysis summary

        """
        summary = {
            "available_crews": [],
            "analysis_timestamps": {},
            "data_freshness": {},
            "key_metrics": {},
            "recommendations_count": 0,
            "overall_sentiment": "neutral",
            "risk_levels": {},
            "market_insights": [],
        }

        try:
            # Process each core analysis crew
            for crew_type in ["stock", "etf", "crypto"]:
                if crew_type in consolidated_data:
                    summary["available_crews"].append(crew_type)
                    crew_data = consolidated_data[crew_type]

                    # Extract timestamps and freshness
                    if "metadata" in crew_data:
                        metadata = crew_data["metadata"]
                        if "storage_timestamp" in metadata:
                            summary["analysis_timestamps"][crew_type] = metadata["storage_timestamp"]

                        if "data_freshness" in metadata:
                            freshness = metadata["data_freshness"]
                            summary["data_freshness"][crew_type] = {
                                "is_fresh": freshness.get("is_fresh", False),
                                "age_hours": freshness.get("age_hours", 0),
                            }

                    # Extract key metrics from raw output
                    if "raw_output" in crew_data:
                        raw_output = str(crew_data["raw_output"])

                        # Count recommendations
                        recommendation_keywords = ["buy", "strong buy", "hold", "sell"]
                        for keyword in recommendation_keywords:
                            summary["recommendations_count"] += raw_output.lower().count(keyword)

                        # Extract market insights (first 200 chars of meaningful content)
                        if len(raw_output) > 100:
                            summary["market_insights"].append(
                                {
                                    "source": crew_type,
                                    "insight": raw_output[:200] + "..." if len(raw_output) > 200 else raw_output,
                                }
                            )

                    # Extract structured data from pydantic if available
                    if "pydantic" in crew_data and crew_data["pydantic"]:
                        pydantic_data = crew_data["pydantic"]

                        # Extract risk levels
                        if "risk_score" in pydantic_data:
                            summary["risk_levels"][crew_type] = pydantic_data["risk_score"]
                        elif "risk_assessment" in pydantic_data:
                            risk_assessment = pydantic_data["risk_assessment"]
                            if isinstance(risk_assessment, dict) and "risk_score" in risk_assessment:
                                summary["risk_levels"][crew_type] = risk_assessment["risk_score"]

                        # Extract key metrics
                        metrics = {}
                        for key in ["current_price", "price_target", "confidence_score", "recommendation"]:
                            if key in pydantic_data:
                                metrics[key] = pydantic_data[key]

                        if metrics:
                            summary["key_metrics"][crew_type] = metrics

            # Calculate overall sentiment from market sentiment data
            if "market_sentiment" in consolidated_data:
                sentiment_data = consolidated_data["market_sentiment"]
                if "aggregated_scores" in sentiment_data:
                    scores = sentiment_data["aggregated_scores"]
                    positive = scores.get("positive", 0)
                    negative = scores.get("negative", 0)

                    if positive > negative + 0.1:
                        summary["overall_sentiment"] = "positive"
                    elif negative > positive + 0.1:
                        summary["overall_sentiment"] = "negative"

            # Add summary statistics
            summary["summary_stats"] = {
                "total_crews_analyzed": len(summary["available_crews"]),
                "fresh_data_count": sum(1 for freshness in summary["data_freshness"].values() if freshness.get("is_fresh", False)),
                "average_risk_level": sum(summary["risk_levels"].values()) / len(summary["risk_levels"])
                if summary["risk_levels"]
                else 5,
                "total_insights": len(summary["market_insights"]),
            }

            self.logger.debug(f"Generated core analysis summary for {len(summary['available_crews'])} crews")
            return summary

        except Exception as e:
            self.logger.warning(f"Failed to generate core analysis summary: {e}")
            return summary

    def _generate_portfolio_allocation_updates(self, opportunities: APlusOpportunityCollection) -> list[dict[str, Any]]:
        """
        Generate portfolio allocation updates based on A+ opportunities.

        Args:
            opportunities: The A+ opportunities collection

        Returns:
            List of portfolio allocation update recommendations

        """
        updates = []

        try:
            # Process allocation recommendations from A+ opportunities
            for recommendation in opportunities.allocation_recommendations:
                asset_type = recommendation.get("asset_type", "unknown")
                symbol = recommendation.get("symbol", "")
                allocation = recommendation.get("allocation", "")
                grade = recommendation.get("grade", "")
                rank = recommendation.get("rank", 0)

                # Parse allocation percentage if possible
                allocation_percentage = self._parse_allocation_percentage(allocation)

                update = {
                    "action": "ADD_OR_INCREASE",
                    "asset_type": asset_type,
                    "symbol": symbol,
                    "grade": grade,
                    "rank": rank,
                    "recommended_allocation": allocation,
                    "allocation_percentage": allocation_percentage,
                    "rationale": f"A+ opportunity identified with grade {grade} (rank {rank})",
                    "priority": "HIGH" if grade == "A+" else "MEDIUM",
                }

                updates.append(update)

            # Add replacement recommendations based on replacement notes
            for note in opportunities.replacement_notes:
                if ":" in note:
                    symbol, replacement_info = note.split(":", 1)
                    symbol = symbol.strip()
                    replacement_info = replacement_info.strip()

                    # Find the corresponding opportunity
                    all_symbols = (
                        opportunities.stock_opportunities + opportunities.etf_opportunities + opportunities.crypto_opportunities
                    )

                    if symbol in all_symbols:
                        update = {
                            "action": "REPLACE_OR_SUBSTITUTE",
                            "symbol": symbol,
                            "replacement_rationale": replacement_info,
                            "priority": "MEDIUM",
                        }
                        updates.append(update)

            self.logger.info(f"Generated {len(updates)} portfolio allocation updates from A+ opportunities")
            return updates

        except Exception as e:
            self.logger.error(f"Failed to generate portfolio allocation updates: {str(e)}", exc_info=True)
            return []

    def _parse_allocation_percentage(self, allocation_text: str) -> float | None:
        """
        Parse allocation percentage from text.

        Args:
            allocation_text: Text containing allocation information

        Returns:
            Parsed percentage as float, or None if not found

        """
        try:
            import re

            # Look for percentage patterns like "5-8%", "2.0%", "1.5% of portfolio"
            percentage_patterns = [
                r"(\d+(?:\.\d+)?)\s*-\s*\d+(?:\.\d+)?\s*%",  # Range - take lower bound (check first)
                r"(\d+(?:\.\d+)?)\s*%",  # Simple percentage
                r"(\d+(?:\.\d+)?)\s*of\s*total\s*portfolio",  # "2.0 of total portfolio"
            ]

            for pattern in percentage_patterns:
                match = re.search(pattern, allocation_text, re.IGNORECASE)
                if match:
                    return float(match.group(1))

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

        total_opportunities = (
            len(opportunities.stock_opportunities) + len(opportunities.etf_opportunities) + len(opportunities.crypto_opportunities)
        )

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
