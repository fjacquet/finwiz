"""
Crew Output Cache Utility.

This module provides utilities to check for and load recent crew output files
before executing crews, saving time by reusing recent results.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class CrewOutputCache:
    """Manages caching and loading of crew output files."""

    def __init__(self, output_dir: Path = Path("output"), max_age_hours: int = 24) -> None:
        """
        Initialize the crew output cache.

        Args:
            output_dir: Base output directory (default: "output")
            max_age_hours: Maximum age in hours for cached files (default: 24)

        """
        self.output_dir = output_dir
        self.max_age_hours = max_age_hours
        self.logger = logger

    def get_cached_crew_output(self, crew_name: str) -> dict[str, Any] | None:
        """
        Get cached crew output if a recent file exists.

        Args:
            crew_name: Name of the crew (e.g., "stock", "etf", "crypto", "portfolio", "discovery")

        Returns:
            Cached crew output data if recent file exists, None otherwise

        """
        crew_dir = self.output_dir / crew_name

        if not crew_dir.exists():
            self.logger.debug(f"No output directory for {crew_name} crew")
            return None

        # Find the most recent output file
        recent_file = self._find_most_recent_file(crew_dir)

        if not recent_file:
            self.logger.debug(f"No output files found for {crew_name} crew")
            return None

        # Check if file is recent enough
        if not self._is_file_recent(recent_file):
            age_hours = self._get_file_age_hours(recent_file)
            self.logger.info(
                f"Cached {crew_name} output too old ({age_hours:.1f}h > {self.max_age_hours}h), will regenerate"
            )
            return None

        # Load and return the cached data
        try:
            with open(recent_file, encoding="utf-8") as f:
                data = json.load(f)

            age_hours = self._get_file_age_hours(recent_file)
            self.logger.info(
                f"✅ Using cached {crew_name} output from {recent_file.name} (age: {age_hours:.1f}h)"
            )

            # Add cache metadata
            data["_cache_metadata"] = {
                "cached": True,
                "cache_file": str(recent_file),
                "cache_age_hours": age_hours,
                "cache_timestamp": datetime.fromtimestamp(recent_file.stat().st_mtime).isoformat(),
            }

            return data

        except Exception as e:
            self.logger.error(f"Failed to load cached {crew_name} output from {recent_file}: {e}")
            return None

    def _find_most_recent_file(self, crew_dir: Path) -> Path | None:
        """
        Find the most recent JSON file in the crew directory.

        Args:
            crew_dir: Directory to search

        Returns:
            Path to most recent file, or None if no files found

        """
        json_files = list(crew_dir.glob("*.json"))

        if not json_files:
            return None

        # Return the file with the most recent modification time
        return max(json_files, key=lambda f: f.stat().st_mtime)

    def _is_file_recent(self, file_path: Path) -> bool:
        """
        Check if a file is recent enough to use.

        Args:
            file_path: Path to file

        Returns:
            True if file is recent enough, False otherwise

        """
        age_hours = self._get_file_age_hours(file_path)
        return age_hours <= self.max_age_hours

    def _get_file_age_hours(self, file_path: Path) -> float:
        """
        Get the age of a file in hours.

        Args:
            file_path: Path to file

        Returns:
            Age in hours

        """
        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
        age = datetime.now() - file_mtime
        return age.total_seconds() / 3600

    def should_use_cache(self, crew_name: str) -> bool:
        """
        Check if cached output should be used for a crew.

        Args:
            crew_name: Name of the crew

        Returns:
            True if cache should be used, False otherwise

        """
        cached_data = self.get_cached_crew_output(crew_name)
        return cached_data is not None

    def get_cache_info(self, crew_name: str) -> dict[str, Any]:
        """
        Get information about cached output for a crew.

        Args:
            crew_name: Name of the crew

        Returns:
            Dictionary with cache information

        """
        crew_dir = self.output_dir / crew_name

        if not crew_dir.exists():
            return {"exists": False, "crew_name": crew_name}

        recent_file = self._find_most_recent_file(crew_dir)

        if not recent_file:
            return {"exists": False, "crew_name": crew_name, "directory_exists": True}

        age_hours = self._get_file_age_hours(recent_file)
        is_recent = self._is_file_recent(recent_file)

        return {
            "exists": True,
            "crew_name": crew_name,
            "file_path": str(recent_file),
            "file_name": recent_file.name,
            "age_hours": age_hours,
            "is_recent": is_recent,
            "max_age_hours": self.max_age_hours,
            "timestamp": datetime.fromtimestamp(recent_file.stat().st_mtime).isoformat(),
        }


def get_crew_output_cache(max_age_hours: int | None = None) -> CrewOutputCache:
    """
    Get a crew output cache instance.

    Args:
        max_age_hours: Maximum age in hours for cached files (default: from env or 24)

    Returns:
        CrewOutputCache instance

    """
    import os

    if max_age_hours is None:
        # Get from environment or use default
        max_age_hours = int(os.getenv("CREW_CACHE_MAX_AGE_HOURS", "24"))

    return CrewOutputCache(max_age_hours=max_age_hours)
