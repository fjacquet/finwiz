"""
Data Freshness Checker for Crew Data Integration System.

This module provides comprehensive data freshness monitoring capabilities,
including file timestamp checking, stale data detection, and freshness reporting.
"""

import logging
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from finwiz.schemas.integration import FreshnessStatus


class FreshnessCheckResult(BaseModel):
    """Result of a freshness check for a single data source."""

    crew_name: str = Field(description="Name of the crew")
    file_path: str = Field(description="Path to the checked file")
    freshness_status: FreshnessStatus = Field(description="Freshness status details")
    file_exists: bool = Field(description="Whether the file exists")
    file_size_bytes: int | None = Field(default=None, description="Size of the file in bytes")


class FreshnessReport(BaseModel):
    """Comprehensive freshness report across all crew outputs."""

    fresh_data: list[str] = Field(default_factory=list, description="List of fresh data sources")
    stale_data: list[str] = Field(default_factory=list, description="List of stale data sources")
    missing_data: list[str] = Field(default_factory=list, description="List of missing data sources")
    check_results: list[FreshnessCheckResult] = Field(default_factory=list, description="Detailed check results for each data source")
    overall_status: str = Field(description="Overall freshness status")
    check_timestamp: datetime = Field(description="When the freshness check was performed")
    recommendations: list[str] = Field(default_factory=list, description="Recommendations for improving data freshness")


class DataFreshnessChecker:
    """
    Monitors data freshness across all crew outputs.

    This class provides comprehensive freshness checking capabilities including:
    - File timestamp checking with configurable age thresholds
    - Stale data detection across all crew output directories
    - Detailed freshness reporting with status information
    - Refresh recommendations based on data dependencies
    """

    def __init__(self, output_dir: Path = Path("output"), logger: logging.Logger | None = None) -> None:
        """
        Initialize the data freshness checker.

        Args:
            output_dir: Base directory for all crew outputs
            logger: Optional logger instance

        """
        self.output_dir = Path(output_dir)
        self.logger = logger or self._setup_logging()

        # Default crew directories to monitor
        self.crew_directories = ["stock", "etf", "crypto", "discovery", "portfolio"]

        # Default file patterns to check
        self.file_patterns = ["*.json", "*.yaml", "*.yml"]

        self.logger.info(
            "DataFreshnessChecker initialized",
            extra={"output_dir": str(self.output_dir), "crew_directories": self.crew_directories},
        )

    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the freshness checker."""
        logger = logging.getLogger("finwiz.integration.freshness")

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

        return logger

    def check_file_freshness(self, file_path: Path, max_age_hours: int = 24) -> FreshnessStatus:
        """
        Check freshness of a single file.

        Args:
            file_path: Path to the file to check
            max_age_hours: Maximum acceptable age in hours

        Returns:
            FreshnessStatus with detailed freshness information

        """
        try:
            if not file_path.exists():
                return FreshnessStatus(
                    is_fresh=False,
                    age_hours=float("inf"),
                    max_age_hours=max_age_hours,
                    refresh_recommended=True,
                    last_updated=datetime.min,
                )

            # Get file modification time
            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            current_time = datetime.now()

            # Calculate age in hours
            age_delta = current_time - file_mtime
            age_hours = age_delta.total_seconds() / 3600

            # Determine freshness
            is_fresh = age_hours <= max_age_hours
            refresh_recommended = age_hours > (max_age_hours * 0.8)  # Recommend refresh at 80% of max age

            freshness_status = FreshnessStatus(
                is_fresh=is_fresh,
                age_hours=age_hours,
                max_age_hours=max_age_hours,
                refresh_recommended=refresh_recommended,
                last_updated=file_mtime,
            )

            self.logger.debug(
                f"Checked freshness for {file_path}",
                extra={"is_fresh": is_fresh, "age_hours": age_hours, "max_age_hours": max_age_hours},
            )

            return freshness_status

        except Exception as e:
            self.logger.error(f"Error checking freshness for {file_path}: {e!s}", exc_info=True)

            return FreshnessStatus(
                is_fresh=False,
                age_hours=float("inf"),
                max_age_hours=max_age_hours,
                refresh_recommended=True,
                last_updated=datetime.min,
            )

    def get_stale_files(self, max_age_hours: int = 24) -> list[Path]:
        """
        Get list of all stale files across crew directories.

        Args:
            max_age_hours: Maximum acceptable age in hours

        Returns:
            List of Path objects for stale files

        """
        stale_files = []

        try:
            for crew_dir in self.crew_directories:
                crew_path = self.output_dir / crew_dir

                if not crew_path.exists():
                    continue

                # Check all files matching patterns
                for pattern in self.file_patterns:
                    for file_path in crew_path.glob(pattern):
                        freshness = self.check_file_freshness(file_path, max_age_hours)
                        if not freshness.is_fresh:
                            stale_files.append(file_path)

            self.logger.info(f"Found {len(stale_files)} stale files", extra={"max_age_hours": max_age_hours, "stale_count": len(stale_files)})

            return stale_files

        except Exception as e:
            self.logger.error(f"Error getting stale files: {e!s}", exc_info=True)
            return []

    def recommend_refresh_order(self, max_age_hours: int = 24) -> list[str]:
        """
        Recommend crew execution order based on data dependencies and staleness.

        Args:
            max_age_hours: Maximum acceptable age in hours

        Returns:
            List of crew names in recommended refresh order

        """
        try:
            # Define dependency order (crews with no dependencies first)
            dependency_order = {
                "stock": 0,  # No dependencies
                "etf": 0,  # No dependencies
                "crypto": 0,  # No dependencies
                "discovery": 1,  # Depends on stock, etf, crypto
                "portfolio": 2,  # Depends on all others
            }

            crew_staleness = {}

            # Check staleness for each crew
            for crew_dir in self.crew_directories:
                crew_path = self.output_dir / crew_dir

                if not crew_path.exists():
                    crew_staleness[crew_dir] = float("inf")  # Missing = most stale
                    continue

                # Find the newest file in the crew directory
                newest_file = None
                newest_time = datetime.min

                for pattern in self.file_patterns:
                    for file_path in crew_path.glob(pattern):
                        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if file_mtime > newest_time:
                            newest_time = file_mtime
                            newest_file = file_path

                if newest_file:
                    age_hours = (datetime.now() - newest_time).total_seconds() / 3600
                    crew_staleness[crew_dir] = age_hours
                else:
                    crew_staleness[crew_dir] = float("inf")

            # Sort crews by dependency order first, then by staleness
            sorted_crews = sorted(self.crew_directories, key=lambda crew: (dependency_order.get(crew, 999), crew_staleness.get(crew, 0)))

            # Filter to only include crews that need refresh
            refresh_needed = [crew for crew in sorted_crews if crew_staleness.get(crew, 0) > max_age_hours]

            self.logger.info(
                "Generated refresh order recommendations",
                extra={
                    "total_crews": len(sorted_crews),
                    "refresh_needed": len(refresh_needed),
                    "recommended_order": refresh_needed,
                },
            )

            return refresh_needed

        except Exception as e:
            self.logger.error(f"Error generating refresh order: {e!s}", exc_info=True)
            return self.crew_directories  # Fallback to default order

    def generate_freshness_report(self, max_age_hours: int = 24) -> FreshnessReport:
        """
        Generate comprehensive freshness report across all crew outputs.

        Args:
            max_age_hours: Maximum acceptable age in hours

        Returns:
            FreshnessReport with detailed status information

        """
        try:
            fresh_data = []
            stale_data = []
            missing_data = []
            check_results = []
            recommendations = []

            self.logger.info(f"Generating freshness report with max age: {max_age_hours} hours")

            for crew_dir in self.crew_directories:
                crew_path = self.output_dir / crew_dir

                if not crew_path.exists():
                    missing_data.append(crew_dir)
                    recommendations.append(f"Create output directory for {crew_dir} crew")
                    continue

                # Find files in crew directory
                crew_files = []
                for pattern in self.file_patterns:
                    crew_files.extend(list(crew_path.glob(pattern)))

                if not crew_files:
                    missing_data.append(crew_dir)
                    recommendations.append(f"Generate initial output for {crew_dir} crew")
                    continue

                # Check freshness of the newest file
                newest_file = max(crew_files, key=lambda f: f.stat().st_mtime)
                freshness_status = self.check_file_freshness(newest_file, max_age_hours)

                # Create check result
                check_result = FreshnessCheckResult(
                    crew_name=crew_dir,
                    file_path=str(newest_file),
                    freshness_status=freshness_status,
                    file_exists=True,
                    file_size_bytes=newest_file.stat().st_size,
                )
                check_results.append(check_result)

                # Categorize based on freshness
                if freshness_status.is_fresh:
                    fresh_data.append(crew_dir)
                else:
                    stale_data.append(crew_dir)
                    recommendations.append(f"Refresh {crew_dir} crew data (age: {freshness_status.age_hours:.1f}h)")

            # Determine overall status
            total_crews = len(self.crew_directories)
            fresh_count = len(fresh_data)
            missing_count = len(missing_data)

            if missing_count > total_crews // 2:
                overall_status = "INSUFFICIENT"
            elif len(stale_data) > 0:
                overall_status = "PARTIAL"
            elif fresh_count == total_crews:
                overall_status = "FRESH"
            else:
                overall_status = "MIXED"

            # Add general recommendations
            if stale_data:
                refresh_order = self.recommend_refresh_order(max_age_hours)
                if refresh_order:
                    recommendations.append(f"Recommended refresh order: {' -> '.join(refresh_order)}")

            if missing_data:
                recommendations.append("Run missing crews to generate initial data")

            report = FreshnessReport(
                fresh_data=fresh_data,
                stale_data=stale_data,
                missing_data=missing_data,
                check_results=check_results,
                overall_status=overall_status,
                check_timestamp=datetime.now(),
                recommendations=recommendations,
            )

            self.logger.info(
                "Freshness report generated",
                extra={
                    "fresh_count": len(fresh_data),
                    "stale_count": len(stale_data),
                    "missing_count": len(missing_data),
                    "overall_status": overall_status,
                },
            )

            return report

        except Exception as e:
            self.logger.error(f"Error generating freshness report: {e!s}", exc_info=True)

            # Return error report
            return FreshnessReport(
                fresh_data=[],
                stale_data=[],
                missing_data=self.crew_directories,
                check_results=[],
                overall_status="ERROR",
                check_timestamp=datetime.now(),
                recommendations=["Fix freshness checker errors and retry"],
            )

    def check_data_freshness_for_crew(self, crew_name: str, max_age_hours: int = 24) -> FreshnessCheckResult | None:
        """
        Check data freshness for a specific crew.

        Args:
            crew_name: Name of the crew to check
            max_age_hours: Maximum acceptable age in hours

        Returns:
            FreshnessCheckResult for the crew, or None if crew not found

        """
        try:
            crew_path = self.output_dir / crew_name

            if not crew_path.exists():
                return FreshnessCheckResult(
                    crew_name=crew_name,
                    file_path=str(crew_path),
                    freshness_status=FreshnessStatus(
                        is_fresh=False,
                        age_hours=float("inf"),
                        max_age_hours=max_age_hours,
                        refresh_recommended=True,
                        last_updated=datetime.min,
                    ),
                    file_exists=False,
                    file_size_bytes=None,
                )

            # Find files in crew directory
            crew_files = []
            for pattern in self.file_patterns:
                crew_files.extend(list(crew_path.glob(pattern)))

            if not crew_files:
                return FreshnessCheckResult(
                    crew_name=crew_name,
                    file_path=str(crew_path),
                    freshness_status=FreshnessStatus(
                        is_fresh=False,
                        age_hours=float("inf"),
                        max_age_hours=max_age_hours,
                        refresh_recommended=True,
                        last_updated=datetime.min,
                    ),
                    file_exists=True,
                    file_size_bytes=0,
                )

            # Check freshness of the newest file
            newest_file = max(crew_files, key=lambda f: f.stat().st_mtime)
            freshness_status = self.check_file_freshness(newest_file, max_age_hours)

            return FreshnessCheckResult(
                crew_name=crew_name,
                file_path=str(newest_file),
                freshness_status=freshness_status,
                file_exists=True,
                file_size_bytes=newest_file.stat().st_size,
            )

        except Exception as e:
            self.logger.error(f"Error checking freshness for crew {crew_name}: {e!s}", exc_info=True)
            return None
