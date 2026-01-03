"""
Health monitoring and reporting for integration system.

Provides comprehensive health monitoring, report generation, and
recommendations for the crew data integration pipeline.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from finwiz.integration.config import get_integration_config
from .checks import (
    HealthStatus,
    check_data_availability,
    check_data_freshness,
    check_directory_structure,
    check_integration_metadata,
    check_system_resources,
    check_validation_status,
)

# Re-export HealthStatus for backward compatibility
__all__ = ["HealthStatus", "SystemHealthReport", "IntegrationHealthChecker", "get_health_checker", "perform_quick_health_check", "perform_comprehensive_health_check"]
from finwiz.infrastructure.logging.utils import IntegrationLogger


class SystemHealthReport(BaseModel):
    """Comprehensive system health report."""

    overall_status: str = Field(..., pattern="^(healthy|warning|critical|unknown)$")
    check_timestamp: datetime
    components: list[dict[str, Any]] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)


class IntegrationHealthChecker:
    """
    Comprehensive health checker for the integration system.

    Monitors data pipeline health, freshness, availability, and system resources
    for single-user workflow debugging and monitoring.
    """

    def __init__(self, output_dir: Path | None = None) -> None:
        """
        Initialize the health checker.

        Args:
            output_dir: Base directory for crew outputs

        """
        self.config = get_integration_config()
        self.output_dir = output_dir or self.config.output_dir
        self.integration_dir = self.output_dir / self.config.integration_dir_name

        self.logger = IntegrationLogger("finwiz.integration.health")

        # Health check configuration
        self.crew_names = ["stock", "etf", "crypto", "discovery", "portfolio", "report"]
        self.critical_directories = [
            self.output_dir,
            self.integration_dir,
            self.integration_dir / "metadata",
            self.integration_dir / "contracts",
            self.integration_dir / "consolidated",
        ]

    def _check_data_freshness(self) -> "HealthStatus":
        """Check data freshness across all crews (backward compatibility wrapper)."""
        return check_data_freshness(
            output_dir=self.output_dir,
            crew_names=self.crew_names,
            max_age_hours=self.config.default_max_age_hours,
            logger=self.logger,
        )

    def _check_data_availability(self) -> "HealthStatus":
        """Check data availability (backward compatibility wrapper)."""
        return check_data_availability(
            output_dir=self.output_dir,
            crew_names=self.crew_names,
            logger=self.logger,
        )

    def _check_directory_structure(self) -> "HealthStatus":
        """Check directory structure (backward compatibility wrapper)."""
        return check_directory_structure(
            critical_directories=self.critical_directories,
            logger=self.logger,
        )

    def _check_system_resources(self) -> "HealthStatus":
        """Check system resources (backward compatibility wrapper)."""
        return check_system_resources(
            output_dir=self.output_dir,
            logger=self.logger,
        )

    def _check_integration_metadata(self) -> "HealthStatus":
        """Check integration metadata (backward compatibility wrapper)."""
        return check_integration_metadata(
            integration_dir=self.integration_dir,
            logger=self.logger,
        )

    def _check_validation_status(self) -> "HealthStatus":
        """Check validation status (backward compatibility wrapper)."""
        return check_validation_status(
            integration_dir=self.integration_dir,
            crew_names=self.crew_names,
            logger=self.logger,
        )

    def perform_comprehensive_health_check(self) -> SystemHealthReport:
        """Perform a comprehensive health check of the integration system."""
        self.logger.logger.info("Starting comprehensive health check")

        try:
            components = []
            overall_status = "healthy"
            recommendations = []

            # Check data freshness
            freshness_health = self._check_data_freshness()
            components.append(self._health_status_to_dict(freshness_health))
            if freshness_health.status in ["warning", "critical"]:
                overall_status = self._escalate_status(overall_status, freshness_health.status)

            # Check data availability
            availability_health = self._check_data_availability()
            components.append(self._health_status_to_dict(availability_health))
            if availability_health.status in ["warning", "critical"]:
                overall_status = self._escalate_status(overall_status, availability_health.status)

            # Check directory structure
            directory_health = self._check_directory_structure()
            components.append(self._health_status_to_dict(directory_health))
            if directory_health.status in ["warning", "critical"]:
                overall_status = self._escalate_status(overall_status, directory_health.status)

            # Check system resources
            resource_health = self._check_system_resources()
            components.append(self._health_status_to_dict(resource_health))
            if resource_health.status in ["warning", "critical"]:
                overall_status = self._escalate_status(overall_status, resource_health.status)

            # Check integration metadata
            metadata_health = self._check_integration_metadata()
            components.append(self._health_status_to_dict(metadata_health))
            if metadata_health.status in ["warning", "critical"]:
                overall_status = self._escalate_status(overall_status, metadata_health.status)

            # Check validation status
            validation_health = self._check_validation_status()
            components.append(self._health_status_to_dict(validation_health))
            if validation_health.status in ["warning", "critical"]:
                overall_status = self._escalate_status(overall_status, validation_health.status)

            # Generate recommendations
            recommendations = self._generate_recommendations(components)

            # Create summary
            summary = self._create_health_summary(components)

            report = SystemHealthReport(
                overall_status=overall_status,
                check_timestamp=datetime.now(),
                components=components,
                summary=summary,
                recommendations=recommendations,
            )

            self.logger.log_system_health_check(
                component="integration_system",
                status=overall_status,
                details={"component_count": len(components), "recommendations": len(recommendations)},
            )

            return report

        except Exception as e:
            error_msg = f"Health check failed: {str(e)}"
            self.logger.log_integration_error(error_type="HEALTH_CHECK_ERROR", crew_name="system", error_message=error_msg)

            return SystemHealthReport(
                overall_status="critical",
                check_timestamp=datetime.now(),
                components=[
                    {
                        "component": "health_checker",
                        "status": "critical",
                        "message": error_msg,
                        "details": {},
                        "last_check": datetime.now().isoformat(),
                    }
                ],
                summary={"error": error_msg},
                recommendations=["Fix health checker and retry"],
            )

    def _health_status_to_dict(self, health_status: HealthStatus) -> dict[str, Any]:
        """Convert HealthStatus to dictionary."""
        return {
            "component": health_status.component,
            "status": health_status.status,
            "message": health_status.message,
            "details": health_status.details,
            "last_check": health_status.last_check.isoformat(),
            "next_check": health_status.next_check.isoformat() if health_status.next_check else None,
        }

    def _escalate_status(self, current: str, new: str) -> str:
        """Escalate status based on severity."""
        severity_order = ["healthy", "warning", "critical", "unknown"]

        current_index = severity_order.index(current) if current in severity_order else 0
        new_index = severity_order.index(new) if new in severity_order else 0

        return severity_order[max(current_index, new_index)]

    def _generate_recommendations(self, components: list[dict[str, Any]] | list[HealthStatus]) -> list[str]:
        """Generate recommendations based on health check results."""
        recommendations = []

        for component in components:
            # Handle both dict and HealthStatus objects
            if isinstance(component, dict):
                status = component["status"]
                comp_name = component["component"]
                details = component["details"]
            else:
                status = component.status
                comp_name = component.component
                details = component.details

            if status == "critical":
                if comp_name == "data_freshness":
                    stale_data = details.get("stale_data", [])
                    if stale_data:
                        recommendations.append(f"Run crew executions to refresh stale data: {', '.join(stale_data)}")
                elif comp_name == "data_availability":
                    missing = details.get("missing_crews", [])
                    if missing:
                        recommendations.append(f"Execute missing crews: {', '.join(missing)}")
                elif comp_name == "directory_structure":
                    missing_dirs = details.get("missing_directories", [])
                    if missing_dirs:
                        recommendations.append(f"Create missing directories: {', '.join(missing_dirs)}")
                elif comp_name == "integration_metadata":
                    corrupted = details.get("corrupted_files", [])
                    if corrupted:
                        recommendations.append(f"Fix corrupted metadata files: {', '.join(corrupted)}")
                elif comp_name == "validation_status":
                    invalid = details.get("invalid_crews", [])
                    if invalid:
                        recommendations.append(f"Fix validation errors for crews: {', '.join(invalid)}")

            elif status == "warning":
                if comp_name == "data_freshness":
                    stale = details.get("stale_data", [])
                    if stale:
                        recommendations.append(f"Consider refreshing stale data: {', '.join(stale)}")
                elif comp_name == "system_resources":
                    issues = details.get("issues", [])
                    if issues:
                        recommendations.append(f"Monitor system resources: {', '.join(issues)}")

        # Add general recommendations
        if not recommendations:
            recommendations.append("System appears healthy - continue monitoring")

        return recommendations

    def _create_health_summary(self, components: list[dict[str, Any]] | list[HealthStatus]) -> dict[str, Any]:
        """Create a summary of health check results."""
        status_counts = {"healthy": 0, "warning": 0, "critical": 0, "unknown": 0}

        for component in components:
            # Handle both dict and HealthStatus objects
            if isinstance(component, dict):
                status = component["status"]
                comp_name = component["component"]
            else:
                status = component.status
                comp_name = component.component

            status_counts[status] = status_counts.get(status, 0) + 1

        # Get component names
        if components and isinstance(components[0], dict):
            comp_names = [comp["component"] for comp in components]
        else:
            comp_names = [comp.component for comp in components]

        return {
            "total_components": len(components),
            "status_distribution": status_counts,
            "health_percentage": (status_counts["healthy"] / len(components)) * 100 if components else 0,
            "components_checked": comp_names,
        }

    def quick_health_check(self) -> dict[str, Any]:
        """Perform a quick health check returning simple status."""
        try:
            # Quick checks without full analysis
            issues = []

            # Check if output directory exists
            if not self.output_dir.exists():
                issues.append("Output directory missing")

            # Check if any crew data exists
            crew_data_exists = False
            for crew_name in self.crew_names:
                crew_dir = self.output_dir / crew_name
                if crew_dir.exists() and list(crew_dir.glob("*.json")):
                    crew_data_exists = True
                    break

            if not crew_data_exists:
                issues.append("No crew data found")

            # Check integration directory
            if not self.integration_dir.exists():
                issues.append("Integration directory missing")

            # Determine overall status
            if len(issues) > 2:
                overall_status = "critical"
            elif len(issues) > 0:
                overall_status = "warning"
            else:
                overall_status = "healthy"

            return {"overall_status": overall_status, "issues": issues, "check_timestamp": datetime.now().isoformat()}

        except Exception as e:
            return {
                "overall_status": "critical",
                "issues": [f"Health check failed: {str(e)}"],
                "check_timestamp": datetime.now().isoformat(),
            }

    def export_health_report(self, output_file: Path | None = None) -> Path:
        """Export comprehensive health report to JSON file."""
        try:
            report = self.perform_comprehensive_health_check()

            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = self.integration_dir / "metadata" / f"health_report_{timestamp}.json"

            # Ensure directory exists
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Write report
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(report.model_dump(), f, indent=2, ensure_ascii=False, default=str)

            self.logger.logger.info(f"Health report exported to: {output_file}")
            return output_file

        except Exception as e:
            error_msg = f"Failed to export health report: {str(e)}"
            self.logger.log_integration_error(error_type="HEALTH_EXPORT_ERROR", crew_name="system", error_message=error_msg)
            raise


# Global health checker instance
_health_checker: IntegrationHealthChecker | None = None


def get_health_checker() -> IntegrationHealthChecker:
    """Get the global health checker instance."""
    global _health_checker
    if _health_checker is None:
        _health_checker = IntegrationHealthChecker()
    return _health_checker


def perform_quick_health_check() -> dict[str, Any]:
    """Perform a quick health check of the integration system."""
    health_checker = get_health_checker()
    return health_checker.quick_health_check()


def perform_comprehensive_health_check() -> SystemHealthReport:
    """Perform a comprehensive health check of the integration system."""
    health_checker = get_health_checker()
    return health_checker.perform_comprehensive_health_check()
