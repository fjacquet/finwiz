"""
Data validation utilities for crew data processing.

This module contains validation logic for checking data availability,
freshness, and generating validation reports.
"""

from datetime import datetime
from typing import Any

from ..schemas.integration import (
    DataAvailabilityReport,
    DataAvailabilityStatus,
    IntegrationError,
    IntegrationErrorType,
)


class DataValidator:
    """Handles data validation operations for crew data."""

    def __init__(self, integration_manager: Any, logger: Any) -> None:
        """
        Initialize the data validator.

        Args:
            integration_manager: The integration manager instance
            logger: Logger instance for validation operations

        """
        self.integration_manager = integration_manager
        self.logger = logger

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

    def validate_crew_data_structure(self, crew_name: str, crew_data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate the structure of crew data.

        Args:
            crew_name: Name of the crew
            crew_data: The crew data to validate

        Returns:
            Dictionary containing validation results

        """
        validation_result = {
            "crew_name": crew_name,
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "data_completeness": 0.0,
            "validation_timestamp": datetime.now(),
        }

        if not isinstance(crew_data, dict):
            validation_result["is_valid"] = False
            validation_result["errors"].append("Crew data must be a dictionary")
            return validation_result

        # Define expected fields by crew type
        expected_fields = self._get_expected_fields_for_crew(crew_name)

        # Check for required fields
        missing_fields = []
        present_fields = 0

        for field in expected_fields["required"]:
            if field not in crew_data:
                missing_fields.append(field)
            else:
                present_fields += 1

        # Check for optional fields
        for field in expected_fields["optional"]:
            if field in crew_data:
                present_fields += 1

        # Calculate completeness
        total_fields = len(expected_fields["required"]) + len(expected_fields["optional"])
        validation_result["data_completeness"] = present_fields / total_fields if total_fields > 0 else 0.0

        # Add errors for missing required fields
        if missing_fields:
            validation_result["is_valid"] = False
            validation_result["errors"].extend([f"Missing required field: {field}" for field in missing_fields])

        # Add warnings for missing optional fields
        missing_optional = [field for field in expected_fields["optional"] if field not in crew_data]
        if missing_optional:
            validation_result["warnings"].extend([f"Missing optional field: {field}" for field in missing_optional])

        # Validate data types
        type_errors = self._validate_data_types(crew_name, crew_data)
        validation_result["errors"].extend(type_errors)

        if type_errors:
            validation_result["is_valid"] = False

        return validation_result

    def _get_expected_fields_for_crew(self, crew_name: str) -> dict[str, list[str]]:
        """Get expected fields for a specific crew type."""
        field_mappings = {
            "stock": {
                "required": ["analysis", "recommendations"],
                "optional": ["technical_analysis", "risk_assessment", "market_data", "symbols"],
            },
            "etf": {
                "required": ["analysis", "recommendations"],
                "optional": ["expense_analysis", "holdings_analysis", "performance_data", "symbols"],
            },
            "crypto": {
                "required": ["market_analysis", "recommendations"],
                "optional": ["technical_analysis", "sentiment_analysis", "risk_assessment", "symbols"],
            },
            "discovery": {
                "required": ["opportunities", "analysis"],
                "optional": ["market_regime", "confidence_score", "validation_timestamp"],
            },
            "portfolio": {
                "required": ["holdings", "analysis"],
                "optional": ["rebalancing_recommendations", "risk_metrics", "performance_summary"],
            },
        }

        return field_mappings.get(crew_name, {"required": [], "optional": []})

    def _validate_data_types(self, crew_name: str, crew_data: dict[str, Any]) -> list[str]:
        """Validate data types for crew data fields."""
        errors = []

        # Common validations
        if "analysis" in crew_data and not isinstance(crew_data["analysis"], (str, dict)):
            errors.append("Field 'analysis' must be a string or dictionary")

        if "recommendations" in crew_data and not isinstance(crew_data["recommendations"], list):
            errors.append("Field 'recommendations' must be a list")

        if "symbols" in crew_data and not isinstance(crew_data["symbols"], list):
            errors.append("Field 'symbols' must be a list")

        # Crew-specific validations
        if crew_name == "discovery":
            if "opportunities" in crew_data and not isinstance(crew_data["opportunities"], list):
                errors.append("Field 'opportunities' must be a list")

            if "confidence_score" in crew_data:
                score = crew_data["confidence_score"]
                if not isinstance(score, (int, float)) or not (0.0 <= score <= 1.0):
                    errors.append("Field 'confidence_score' must be a number between 0.0 and 1.0")

        elif crew_name == "portfolio":
            if "holdings" in crew_data and not isinstance(crew_data["holdings"], list):
                errors.append("Field 'holdings' must be a list")

        return errors
