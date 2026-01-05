"""
Registry management for crew data integration.

Handles crew coordination, data storage, retrieval, and dependency management.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from finwiz.infrastructure.monitoring.freshness_checker import DataFreshnessChecker, FreshnessReport

from .registry_data_retrieval import (
    get_cached_crew_output,
    get_crew_data_with_freshness_check,
    get_upstream_data,
)
from .registry_execution import coordinate_crew_execution
from .registry_models import CrewConfig, ExecutionResult, UpstreamDataCollection


# Re-export models for backward compatibility
__all__ = [
    "CrewConfig",
    "ExecutionResult",
    "RegistryManager",
    "UpstreamDataCollection",
]


class RegistryManager:
    """Manager for crew registry and data coordination."""

    def __init__(
        self,
        output_dir: Path,
        metadata_dir: Path,
        freshness_checker: DataFreshnessChecker,
        logger: logging.Logger,
    ) -> None:
        """Initialize the registry manager."""
        self.output_dir = output_dir
        self.metadata_dir = metadata_dir
        self.freshness_checker = freshness_checker
        self.logger = logger
        self.execution_log_path = self.metadata_dir / "crew_execution_log.json"
        self.data_lineage_path = self.metadata_dir / "data_lineage.json"

    async def coordinate_crew_execution(self, crews: list[CrewConfig]) -> ExecutionResult:
        """Coordinate execution of multiple crews based on dependencies."""
        return await coordinate_crew_execution(
            crews=crews,
            output_dir=self.output_dir,
            execution_log_path=self.execution_log_path,
            logger=self.logger,
        )

    def store_crew_output(self, crew_name: str, crew_output: Any) -> bool:
        """Store crew output to the integration system."""
        try:
            # Create output directory if needed
            crew_output_dir = self.output_dir / crew_name
            crew_output_dir.mkdir(parents=True, exist_ok=True)

            # Determine output file path
            output_file = crew_output_dir / f"{crew_name}_output.json"

            # Convert crew output to serializable format
            if hasattr(crew_output, "model_dump"):
                data = crew_output.model_dump()
            elif hasattr(crew_output, "dict"):
                data = crew_output.dict()
            elif isinstance(crew_output, dict):
                data = crew_output
            else:
                data = {"raw_output": str(crew_output)}

            # Add metadata
            data["_metadata"] = {
                "crew_name": crew_name,
                "stored_at": datetime.now().isoformat(),
            }

            # Write to file
            with open(output_file, "w") as f:
                json.dump(data, f, indent=2, default=str)

            self.logger.info(f"Stored {crew_name} output to {output_file}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to store {crew_name} output: {e}")
            return False

    def get_cached_crew_output(self, crew_name: str) -> dict[str, Any] | None:
        """Get cached crew output if available."""
        return get_cached_crew_output(
            output_dir=self.output_dir,
            crew_name=crew_name,
            logger=self.logger,
        )

    def get_upstream_data(self, requesting_crew: str, max_age_hours: int = 24) -> UpstreamDataCollection:
        """Get available upstream data for a requesting crew."""
        return get_upstream_data(
            output_dir=self.output_dir,
            requesting_crew=requesting_crew,
            freshness_checker=self.freshness_checker,
            logger=self.logger,
            max_age_hours=max_age_hours,
        )

    def get_crew_data_with_freshness_check(
        self,
        crew_name: str,
        max_age_hours: int = 24,
        warn_on_stale: bool = True,
    ) -> dict | None:
        """Get crew data with automatic freshness validation."""
        return get_crew_data_with_freshness_check(
            output_dir=self.output_dir,
            crew_name=crew_name,
            freshness_checker=self.freshness_checker,
            logger=self.logger,
            max_age_hours=max_age_hours,
            warn_on_stale=warn_on_stale,
        )

    def get_refresh_recommendations(self, max_age_hours: int = 24) -> list[str]:
        """Get list of crews that should be refreshed based on data staleness."""
        try:
            return self.freshness_checker.recommend_refresh_order(max_age_hours)
        except Exception as e:
            self.logger.error(f"Failed to get refresh recommendations: {str(e)}", exc_info=True)
            return []

    def check_data_freshness(self, max_age_hours: int = 24) -> FreshnessReport:
        """Check freshness of all crew data using the DataFreshnessChecker."""
        self.logger.info(f"Checking data freshness with max age: {max_age_hours} hours")

        try:
            return self.freshness_checker.generate_freshness_report(max_age_hours)
        except Exception as e:
            self.logger.error(f"Data freshness check failed: {str(e)}", exc_info=True)
            return FreshnessReport(
                fresh_data=[],
                stale_data=[],
                missing_data=["stock", "etf", "crypto", "discovery", "portfolio"],
                overall_status="ERROR",
                check_timestamp=datetime.now(),
                recommendations=["Fix data freshness checker and retry"],
            )
