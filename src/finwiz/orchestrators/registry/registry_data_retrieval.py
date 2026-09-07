"""
Data retrieval operations for registry management.

Functions for retrieving, caching, and consolidating crew output data.
"""

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .registry_models import UpstreamDataCollection

if TYPE_CHECKING:
    from finwiz.infrastructure.monitoring.freshness_checker import DataFreshnessChecker


def get_cached_crew_output(
    output_dir: Path,
    crew_name: str,
    logger: logging.Logger,
) -> dict[str, Any] | None:
    """Get cached crew output if available."""
    try:
        from finwiz.integration.schema import SchemaManager

        schema_manager = SchemaManager(logger)
        crew_output_dir = output_dir / crew_name
        latest_file = crew_output_dir / f"{crew_name}_latest.json"

        if latest_file.exists():
            return schema_manager.load_json_file(latest_file, {})

        # Fallback: find most recent file
        output_files = list(crew_output_dir.glob(f"{crew_name}_output_*.json"))
        if output_files:
            newest_file = max(output_files, key=lambda f: f.stat().st_mtime)
            return schema_manager.load_json_file(newest_file, {})

        return None

    except Exception as e:
        logger.error(f"Failed to get cached output for crew {crew_name}: {e!s}")
        return None


def get_upstream_data(
    output_dir: Path,
    requesting_crew: str,
    freshness_checker: "DataFreshnessChecker",
    logger: logging.Logger,
    max_age_hours: int = 24,
) -> UpstreamDataCollection:
    """Get available upstream data for a requesting crew with freshness validation."""
    logger.info(f"Getting upstream data for crew: {requesting_crew}")
    crew_dirs = ["stock", "etf", "crypto", "discovery", "portfolio"]

    try:
        available_data: dict[str, Any] = {}
        missing_data: list[str] = []
        stale_data: list[str] = []

        for crew_dir in crew_dirs:
            if crew_dir == requesting_crew:
                continue

            crew_output_dir = output_dir / crew_dir
            if crew_output_dir.exists():
                output_files = list(crew_output_dir.glob("*.json"))
                if output_files:
                    max(output_files, key=lambda f: f.stat().st_mtime)
                    freshness_result = freshness_checker.check_data_freshness_for_crew(crew_dir, max_age_hours)

                    if freshness_result and freshness_result.freshness_status.is_fresh:
                        available_data[crew_dir] = [str(f) for f in output_files]
                    else:
                        stale_data.append(crew_dir)
                        available_data[crew_dir] = [str(f) for f in output_files]
                        age_hours = freshness_result.freshness_status.age_hours if freshness_result else float("inf")
                        logger.warning(f"Stale data detected for {crew_dir} crew (age: {age_hours:.1f}h > {max_age_hours}h)")
                else:
                    missing_data.append(crew_dir)
            else:
                missing_data.append(crew_dir)

        result = UpstreamDataCollection(
            available_data=available_data,
            missing_data=missing_data,
            stale_data=stale_data,
        )

        logger.info(
            f"Upstream data collection completed for {requesting_crew}",
            extra={
                "available_crews": len(available_data),
                "missing_crews": len(missing_data),
                "stale_crews": len(stale_data),
            },
        )
        return result

    except Exception as e:
        logger.error(
            f"Failed to get upstream data for {requesting_crew}: {e!s}",
            exc_info=True,
        )
        return UpstreamDataCollection(available_data={}, missing_data=crew_dirs, stale_data=[])


def get_crew_data_with_freshness_check(
    output_dir: Path,
    crew_name: str,
    freshness_checker: "DataFreshnessChecker",
    logger: logging.Logger,
    max_age_hours: int = 24,
    warn_on_stale: bool = True,
) -> dict | None:
    """Get crew data with automatic freshness validation and warnings."""
    try:
        crew_output_dir = output_dir / crew_name

        if not crew_output_dir.exists():
            logger.warning(f"No output directory found for {crew_name} crew")
            return None

        # Find JSON files with proper filtering
        if crew_name == "discovery":
            output_files = list(crew_output_dir.glob("discovery_output_*.json"))
        else:
            output_files = list(crew_output_dir.glob("*.json"))

        if not output_files:
            logger.warning(f"No output files found for {crew_name} crew")
            return None

        # Check freshness
        freshness_result = freshness_checker.check_data_freshness_for_crew(crew_name, max_age_hours)

        if freshness_result:
            status = freshness_result.freshness_status
            if not status.is_fresh and warn_on_stale:
                logger.warning(
                    f"Using stale data for {crew_name} crew",
                    extra={
                        "crew_name": crew_name,
                        "age_hours": status.age_hours,
                        "max_age_hours": max_age_hours,
                        "file_count": len(output_files),
                    },
                )
            elif status.refresh_recommended and warn_on_stale:
                logger.info(
                    f"Data refresh recommended for {crew_name} crew",
                    extra={
                        "crew_name": crew_name,
                        "age_hours": status.age_hours,
                        "max_age_hours": max_age_hours,
                    },
                )

        # Return the newest single file
        newest_file = max(output_files, key=lambda f: f.stat().st_mtime)

        if newest_file.stat().st_size == 0:
            logger.warning(f"Cache file for {crew_name} crew is empty: {newest_file}")
            return None

        with open(newest_file, encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                logger.warning(f"Cache file for {crew_name} crew has no content: {newest_file}")
                return None

            try:
                data: dict[Any, Any] = json.loads(content)
                logger.debug(f"Successfully loaded data for {crew_name} crew from {newest_file}")
                return data
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in cache file for {crew_name} crew: {newest_file} - {e}")
                return None

    except Exception as e:
        logger.error(f"Failed to get data for {crew_name} crew: {e!s}", exc_info=True)
        return None
