"""
Integration System Health Checker.

Provides comprehensive health checking for the crew data integration pipeline
in a single-user environment. Monitors data freshness, availability, and
integration system status.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import psutil
from pydantic import BaseModel, Field

from .config import get_integration_config
from .freshness_checker import DataFreshnessChecker
from .logging_utils import IntegrationLogger


class HealthStatus(BaseModel):
    """Health status for a component."""

    component: str
    status: str = Field(..., pattern="^(healthy|warning|critical|unknown)$")
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    last_check: datetime
    next_check: datetime | None = None


class SystemHealthReport(BaseModel):
    """Comprehensive system health report."""

    overall_status: str = Field(..., pattern="^(healthy|warning|critical|unknown)$")
    check_timestamp: datetime
    components: list[HealthStatus] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)


class IntegrationHealthChecker:
    """
    Comprehensive health checker for the integration system.

    Monitors data pipeline health, freshness, availability, and system resources
    for single-user workflow debugging and monitoring.
    """

    def __init__(self, output_dir: Path = None) -> None:
        """
        Initialize the health checker.

        Args:
            output_dir: Base directory for crew outputs

        """
        self.config = get_integration_config()
        self.output_dir = output_dir or self.config.output_dir
        self.integration_dir = self.output_dir / self.config.integration_dir_name

        self.logger = IntegrationLogger("finwiz.integration.health")
        self.freshness_checker = DataFreshnessChecker(output_dir=self.output_dir)

        # Health check configuration
        self.crew_names = ["stock", "etf", "crypto", "discovery", "portfolio", "report"]
        self.critical_directories = [
            self.output_dir,
            self.integration_dir,
            self.integration_dir / "metadata",
            self.integration_dir / "contracts",
            self.integration_dir / "consolidated",
        ]

    def perform_comprehensive_health_check(self) -> SystemHealthReport:
        """Perform a comprehensive health check of the integration system."""
        self.logger.info("Starting comprehensive health check")

        try:
            components = []
            overall_status = "healthy"
            recommendations = []

            # Check data freshness
            freshness_health = self._check_data_freshness()
            components.append(freshness_health)
            if freshness_health.status in ["warning", "critical"]:
                overall_status = self._escalate_status(overall_status, freshness_health.status)

            # Check data availability
            availability_health = self._check_data_availability()
            components.append(availability_health)
            if availability_health.status in ["warning", "critical"]:
                overall_status = self._escalate_status(overall_status, availability_health.status)

            # Check directory structure
            directory_health = self._check_directory_structure()
            components.append(directory_health)
            if directory_health.status in ["warning", "critical"]:
                overall_status = self._escalate_status(overall_status, directory_health.status)

            # Check system resources
            resource_health = self._check_system_resources()
            components.append(resource_health)
            if resource_health.status in ["warning", "critical"]:
                overall_status = self._escalate_status(overall_status, resource_health.status)

            # Check integration metadata
            metadata_health = self._check_integration_metadata()
            components.append(metadata_health)
            if metadata_health.status in ["warning", "critical"]:
                overall_status = self._escalate_status(overall_status, metadata_health.status)

            # Check validation status
            validation_health = self._check_validation_status()
            components.append(validation_health)
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
                    HealthStatus(component="health_checker", status="critical", message=error_msg, last_check=datetime.now())
                ],
                summary={"error": error_msg},
                recommendations=["Fix health checker and retry"],
            )

    def _check_data_freshness(self) -> HealthStatus:
        """Check data freshness across all crews."""
        try:
            freshness_report = self.freshness_checker.generate_freshness_report(max_age_hours=self.config.default_max_age_hours)

            fresh_count = len(freshness_report.fresh_data)
            stale_count = len(freshness_report.stale_data)
            missing_count = len(freshness_report.missing_data)
            total_crews = len(self.crew_names)

            # Determine status
            if missing_count > total_crews * 0.5:  # More than 50% missing
                status = "critical"
                message = f"Critical: {missing_count} crews missing data, {stale_count} stale"
            elif stale_count > total_crews * 0.3:  # More than 30% stale
                status = "warning"
                message = f"Warning: {stale_count} crews have stale data, {missing_count} missing"
            elif missing_count > 0 or stale_count > 0:
                status = "warning"
                message = f"Some issues: {stale_count} stale, {missing_count} missing"
            else:
                status = "healthy"
                message = f"All data fresh: {fresh_count} crews up-to-date"

            return HealthStatus(
                component="data_freshness",
                status=status,
                message=message,
                details={
                    "fresh_crews": fresh_count,
                    "stale_crews": stale_count,
                    "missing_crews": missing_count,
                    "total_crews": total_crews,
                    "fresh_data": freshness_report.fresh_data,
                    "stale_data": freshness_report.stale_data,
                    "missing_data": freshness_report.missing_data,
                    "overall_freshness_status": freshness_report.overall_status,
                },
                last_check=datetime.now(),
            )

        except Exception as e:
            return HealthStatus(
                component="data_freshness",
                status="critical",
                message=f"Freshness check failed: {str(e)}",
                last_check=datetime.now(),
            )

    def _check_data_availability(self) -> HealthStatus:
        """Check data availability across all crew output directories."""
        try:
            available_crews = []
            missing_crews = []
            empty_crews = []

            for crew_name in self.crew_names:
                crew_dir = self.output_dir / crew_name

                if not crew_dir.exists():
                    missing_crews.append(crew_name)
                    continue

                # Check for JSON files
                json_files = list(crew_dir.glob("*.json"))
                if not json_files:
                    empty_crews.append(crew_name)
                else:
                    available_crews.append(
                        {"crew": crew_name, "file_count": len(json_files), "files": [f.name for f in json_files]}
                    )

            # Determine status
            total_crews = len(self.crew_names)
            available_count = len(available_crews)

            if available_count == 0:
                status = "critical"
                message = "Critical: No crew data available"
            elif available_count < total_crews * 0.5:  # Less than 50% available
                status = "critical"
                message = f"Critical: Only {available_count}/{total_crews} crews have data"
            elif len(missing_crews) > 0 or len(empty_crews) > 0:
                status = "warning"
                message = f"Warning: {len(missing_crews)} missing, {len(empty_crews)} empty directories"
            else:
                status = "healthy"
                message = f"All crews have data: {available_count}/{total_crews}"

            return HealthStatus(
                component="data_availability",
                status=status,
                message=message,
                details={
                    "available_crews": available_crews,
                    "missing_crews": missing_crews,
                    "empty_crews": empty_crews,
                    "availability_percentage": (available_count / total_crews) * 100,
                },
                last_check=datetime.now(),
            )

        except Exception as e:
            return HealthStatus(
                component="data_availability",
                status="critical",
                message=f"Availability check failed: {str(e)}",
                last_check=datetime.now(),
            )

    def _check_directory_structure(self) -> HealthStatus:
        """Check that all required directories exist and are accessible."""
        try:
            missing_dirs = []
            inaccessible_dirs = []
            healthy_dirs = []

            for directory in self.critical_directories:
                if not directory.exists():
                    missing_dirs.append(str(directory))
                elif not directory.is_dir():
                    inaccessible_dirs.append(f"{directory} (not a directory)")
                else:
                    try:
                        # Test write access
                        test_file = directory / ".health_check_test"
                        test_file.touch()
                        test_file.unlink()
                        healthy_dirs.append(str(directory))
                    except Exception:
                        inaccessible_dirs.append(f"{directory} (no write access)")

            # Determine status
            if missing_dirs or inaccessible_dirs:
                if len(missing_dirs) > len(self.critical_directories) * 0.5:
                    status = "critical"
                    message = f"Critical: {len(missing_dirs)} directories missing, {len(inaccessible_dirs)} inaccessible"
                else:
                    status = "warning"
                    message = f"Warning: {len(missing_dirs)} missing, {len(inaccessible_dirs)} inaccessible"
            else:
                status = "healthy"
                message = f"All directories healthy: {len(healthy_dirs)} accessible"

            return HealthStatus(
                component="directory_structure",
                status=status,
                message=message,
                details={
                    "healthy_directories": healthy_dirs,
                    "missing_directories": missing_dirs,
                    "inaccessible_directories": inaccessible_dirs,
                    "total_checked": len(self.critical_directories),
                },
                last_check=datetime.now(),
            )

        except Exception as e:
            return HealthStatus(
                component="directory_structure",
                status="critical",
                message=f"Directory check failed: {str(e)}",
                last_check=datetime.now(),
            )

    def _check_system_resources(self) -> HealthStatus:
        """Check system resource usage."""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage(str(self.output_dir))

            # Check thresholds
            issues = []
            if cpu_percent > 90:
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
            if memory.percent > 90:
                issues.append(f"High memory usage: {memory.percent:.1f}%")
            if disk.percent > 90:
                issues.append(f"High disk usage: {disk.percent:.1f}%")

            # Determine status
            if len(issues) > 2:
                status = "critical"
                message = f"Critical resource issues: {', '.join(issues)}"
            elif len(issues) > 0:
                status = "warning"
                message = f"Resource warnings: {', '.join(issues)}"
            else:
                status = "healthy"
                message = f"Resources healthy: CPU {cpu_percent:.1f}%, Memory {memory.percent:.1f}%, Disk {disk.percent:.1f}%"

            return HealthStatus(
                component="system_resources",
                status=status,
                message=message,
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_percent": disk.percent,
                    "disk_free_gb": disk.free / (1024**3),
                    "issues": issues,
                },
                last_check=datetime.now(),
            )

        except Exception as e:
            return HealthStatus(
                component="system_resources",
                status="warning",
                message=f"Resource check failed: {str(e)}",
                last_check=datetime.now(),
            )

    def _check_integration_metadata(self) -> HealthStatus:
        """Check integration metadata files."""
        try:
            metadata_dir = self.integration_dir / "metadata"
            expected_files = ["crew_execution_log.json", "data_lineage.json", "validation_status.json"]

            existing_files = []
            missing_files = []
            corrupted_files = []

            for filename in expected_files:
                file_path = metadata_dir / filename

                if not file_path.exists():
                    missing_files.append(filename)
                    continue

                try:
                    # Try to load JSON to check if it's valid
                    with open(file_path, encoding="utf-8") as f:
                        json.load(f)
                    existing_files.append(filename)
                except json.JSONDecodeError:
                    corrupted_files.append(filename)
                except Exception:
                    corrupted_files.append(filename)

            # Determine status
            if len(corrupted_files) > 0:
                status = "critical"
                message = f"Critical: {len(corrupted_files)} corrupted metadata files"
            elif len(missing_files) > len(expected_files) * 0.5:
                status = "warning"
                message = f"Warning: {len(missing_files)} metadata files missing"
            elif len(missing_files) > 0:
                status = "warning"
                message = f"Some metadata missing: {len(missing_files)} files"
            else:
                status = "healthy"
                message = f"All metadata healthy: {len(existing_files)} files"

            return HealthStatus(
                component="integration_metadata",
                status=status,
                message=message,
                details={
                    "existing_files": existing_files,
                    "missing_files": missing_files,
                    "corrupted_files": corrupted_files,
                    "metadata_directory": str(metadata_dir),
                },
                last_check=datetime.now(),
            )

        except Exception as e:
            return HealthStatus(
                component="integration_metadata",
                status="critical",
                message=f"Metadata check failed: {str(e)}",
                last_check=datetime.now(),
            )

    def _check_validation_status(self) -> HealthStatus:
        """Check validation status across crews."""
        try:
            validation_file = self.integration_dir / "metadata" / "validation_status.json"

            if not validation_file.exists():
                return HealthStatus(
                    component="validation_status",
                    status="warning",
                    message="No validation status file found",
                    last_check=datetime.now(),
                )

            with open(validation_file, encoding="utf-8") as f:
                validation_data = json.load(f)

            valid_crews = []
            invalid_crews = []
            warning_crews = []

            for crew_name, status in validation_data.items():
                if status.get("is_valid", False):
                    if status.get("warnings", []):
                        warning_crews.append(crew_name)
                    else:
                        valid_crews.append(crew_name)
                else:
                    invalid_crews.append(crew_name)

            # Determine status
            if len(invalid_crews) > 0:
                status = "critical"
                message = f"Critical: {len(invalid_crews)} crews have validation errors"
            elif len(warning_crews) > len(self.crew_names) * 0.5:
                status = "warning"
                message = f"Warning: {len(warning_crews)} crews have validation warnings"
            elif len(warning_crews) > 0:
                status = "warning"
                message = f"Some warnings: {len(warning_crews)} crews"
            else:
                status = "healthy"
                message = f"All validations passed: {len(valid_crews)} crews"

            return HealthStatus(
                component="validation_status",
                status=status,
                message=message,
                details={
                    "valid_crews": valid_crews,
                    "invalid_crews": invalid_crews,
                    "warning_crews": warning_crews,
                    "total_validated": len(validation_data),
                },
                last_check=datetime.now(),
            )

        except Exception as e:
            return HealthStatus(
                component="validation_status",
                status="warning",
                message=f"Validation check failed: {str(e)}",
                last_check=datetime.now(),
            )

    def _escalate_status(self, current: str, new: str) -> str:
        """Escalate status based on severity."""
        severity_order = ["healthy", "warning", "critical", "unknown"]

        current_index = severity_order.index(current) if current in severity_order else 0
        new_index = severity_order.index(new) if new in severity_order else 0

        return severity_order[max(current_index, new_index)]

    def _generate_recommendations(self, components: list[HealthStatus]) -> list[str]:
        """Generate recommendations based on health check results."""
        recommendations = []

        for component in components:
            if component.status == "critical":
                if component.component == "data_freshness":
                    recommendations.append(
                        f"Run crew executions to refresh stale data: {', '.join(component.details.get('stale_data', []))}"
                    )
                elif component.component == "data_availability":
                    missing = component.details.get("missing_crews", [])
                    if missing:
                        recommendations.append(f"Execute missing crews: {', '.join(missing)}")
                elif component.component == "directory_structure":
                    missing_dirs = component.details.get("missing_directories", [])
                    if missing_dirs:
                        recommendations.append(f"Create missing directories: {', '.join(missing_dirs)}")
                elif component.component == "integration_metadata":
                    corrupted = component.details.get("corrupted_files", [])
                    if corrupted:
                        recommendations.append(f"Fix corrupted metadata files: {', '.join(corrupted)}")
                elif component.component == "validation_status":
                    invalid = component.details.get("invalid_crews", [])
                    if invalid:
                        recommendations.append(f"Fix validation errors for crews: {', '.join(invalid)}")

            elif component.status == "warning":
                if component.component == "data_freshness":
                    stale = component.details.get("stale_data", [])
                    if stale:
                        recommendations.append(f"Consider refreshing stale data: {', '.join(stale)}")
                elif component.component == "system_resources":
                    issues = component.details.get("issues", [])
                    if issues:
                        recommendations.append(f"Monitor system resources: {', '.join(issues)}")

        # Add general recommendations
        if not recommendations:
            recommendations.append("System appears healthy - continue monitoring")

        return recommendations

    def _create_health_summary(self, components: list[HealthStatus]) -> dict[str, Any]:
        """Create a summary of health check results."""
        status_counts = {"healthy": 0, "warning": 0, "critical": 0, "unknown": 0}

        for component in components:
            status_counts[component.status] = status_counts.get(component.status, 0) + 1

        return {
            "total_components": len(components),
            "status_distribution": status_counts,
            "health_percentage": (status_counts["healthy"] / len(components)) * 100 if components else 0,
            "components_checked": [comp.component for comp in components],
        }

    def quick_health_check(self) -> dict[str, str]:
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

    def export_health_report(self, output_file: Path = None) -> Path:
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

            self.logger.info(f"Health report exported to: {output_file}")
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


def perform_quick_health_check() -> dict[str, str]:
    """Perform a quick health check of the integration system."""
    health_checker = get_health_checker()
    return health_checker.quick_health_check()


def perform_comprehensive_health_check() -> SystemHealthReport:
    """Perform a comprehensive health check of the integration system."""
    health_checker = get_health_checker()
    return health_checker.perform_comprehensive_health_check()
