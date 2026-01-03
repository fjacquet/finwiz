"""
Health check implementations for integration system components.

Provides individual health check functions for data freshness, availability,
directory structure, system resources, metadata, and validation status.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import psutil
from pydantic import BaseModel, Field

from finwiz.infrastructure.monitoring.freshness_checker import DataFreshnessChecker
from finwiz.infrastructure.logging.utils import IntegrationLogger


class HealthStatus(BaseModel):
    """Health status for a component."""

    component: str
    status: str = Field(..., pattern="^(healthy|warning|critical|unknown)$")
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    last_check: datetime
    next_check: datetime | None = None


def check_data_freshness(
    output_dir: Path,
    crew_names: list[str],
    max_age_hours: int,
    logger: IntegrationLogger,
) -> HealthStatus:
    """
    Check data freshness across all crews.

    Args:
        output_dir: Base output directory
        crew_names: List of crew names to check
        max_age_hours: Maximum age in hours for fresh data
        logger: Logger instance

    Returns:
        HealthStatus for data freshness

    """
    try:
        freshness_checker = DataFreshnessChecker(output_dir=output_dir)
        freshness_report = freshness_checker.generate_freshness_report(max_age_hours=max_age_hours)

        fresh_count = len(freshness_report.fresh_data)
        stale_count = len(freshness_report.stale_data)
        missing_count = len(freshness_report.missing_data)
        total_crews = len(crew_names)

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


def check_data_availability(
    output_dir: Path,
    crew_names: list[str],
    logger: IntegrationLogger,
) -> HealthStatus:
    """
    Check data availability across all crew output directories.

    Args:
        output_dir: Base output directory
        crew_names: List of crew names to check
        logger: Logger instance

    Returns:
        HealthStatus for data availability

    """
    try:
        available_crews = []
        missing_crews = []
        empty_crews = []

        for crew_name in crew_names:
            crew_dir = output_dir / crew_name

            if not crew_dir.exists():
                missing_crews.append(crew_name)
                continue

            # Check for JSON files
            json_files = list(crew_dir.glob("*.json"))
            if not json_files:
                empty_crews.append(crew_name)
            else:
                available_crews.append({"crew": crew_name, "file_count": len(json_files), "files": [f.name for f in json_files]})

        # Determine status
        total_crews = len(crew_names)
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


def check_directory_structure(
    critical_directories: list[Path],
    logger: IntegrationLogger,
) -> HealthStatus:
    """
    Check that all required directories exist and are accessible.

    Args:
        critical_directories: List of critical directories to check
        logger: Logger instance

    Returns:
        HealthStatus for directory structure

    """
    try:
        missing_dirs = []
        inaccessible_dirs = []
        healthy_dirs = []

        for directory in critical_directories:
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
            if len(missing_dirs) > len(critical_directories) * 0.5:
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
                "total_checked": len(critical_directories),
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


def check_system_resources(
    output_dir: Path,
    logger: IntegrationLogger,
) -> HealthStatus:
    """
    Check system resource usage.

    Args:
        output_dir: Base output directory for disk usage check
        logger: Logger instance

    Returns:
        HealthStatus for system resources

    """
    try:
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(str(output_dir))

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


def check_integration_metadata(
    integration_dir: Path,
    logger: IntegrationLogger,
) -> HealthStatus:
    """
    Check integration metadata files.

    Args:
        integration_dir: Integration directory path
        logger: Logger instance

    Returns:
        HealthStatus for integration metadata

    """
    try:
        metadata_dir = integration_dir / "metadata"
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


def check_validation_status(
    integration_dir: Path,
    crew_names: list[str],
    logger: IntegrationLogger,
) -> HealthStatus:
    """
    Check validation status across crews.

    Args:
        integration_dir: Integration directory path
        crew_names: List of crew names
        logger: Logger instance

    Returns:
        HealthStatus for validation status

    """
    try:
        validation_file = integration_dir / "metadata" / "validation_status.json"

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
        elif len(warning_crews) > len(crew_names) * 0.5:
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
