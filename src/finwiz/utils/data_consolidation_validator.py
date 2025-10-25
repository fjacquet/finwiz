"""
Data Consolidation Validator for FinWiz.

Validates that crew outputs are properly retrieved and consolidated.
Implements fail-fast behavior to prevent silent degradation.
"""

import logging
from typing import Any

from finwiz.integration.registry_manager import RegistryManager

logger = logging.getLogger(__name__)


class DataRetrievalError(Exception):
    """Raised when crew data retrieval fails."""

    pass


class DataConsolidationValidator:
    """
    Validate that crew outputs are properly retrieved and consolidated.

    FAIL-FAST: Stop immediately if data is missing or corrupted.
    """

    def __init__(self, registry_manager: RegistryManager) -> None:
        """
        Initialize the data consolidation validator.

        Args:
            registry_manager: RegistryManager instance for data retrieval

        """
        self.registry_manager = registry_manager

    def validate_crew_data_retrieval(self, expected_crews: list[str]) -> dict[str, Any]:
        """
        Validate that all expected crew data can be retrieved.

        Args:
            expected_crews: List of crew names that should have data

        Returns:
            Dict mapping crew names to their data

        Raises:
            DataRetrievalError: If any crew data is missing or corrupted

        """
        retrieved_data = {}
        missing_crews = []
        corrupted_crews = []

        for crew_name in expected_crews:
            logger.info(f"Retrieving data for crew: {crew_name}")

            # Attempt retrieval
            crew_data = self.registry_manager.get_crew_data_with_freshness_check(crew_name)

            if crew_data is None:
                missing_crews.append(crew_name)
                logger.error(f"❌ No data found for {crew_name} crew. Expected location: output/{crew_name}/")
                continue

            # Validate data is not corrupted
            if not self._validate_crew_data_structure(crew_data, crew_name):
                corrupted_crews.append(crew_name)
                logger.error(f"❌ Data for {crew_name} is corrupted or invalid")
                continue

            retrieved_data[crew_name] = crew_data
            logger.info(f"✅ Successfully retrieved data for {crew_name}")

        # FAIL-FAST: Stop if any data is missing or corrupted
        if missing_crews or corrupted_crews:
            error_msg = []
            if missing_crews:
                error_msg.append(f"Missing data for crews: {missing_crews}")
            if corrupted_crews:
                error_msg.append(f"Corrupted data for crews: {corrupted_crews}")

            raise DataRetrievalError("Data consolidation failed. " + " ".join(error_msg))

        logger.info(f"✅ Data consolidation successful: retrieved data from {len(retrieved_data)} crews")

        return retrieved_data

    def _validate_crew_data_structure(self, data: dict[str, Any], crew_name: str) -> bool:
        """
        Validate crew data has expected structure.

        Args:
            data: Crew data to validate
            crew_name: Name of the crew

        Returns:
            True if data structure is valid, False otherwise

        """
        # Check for required fields
        required_fields = ["metadata"]

        for field in required_fields:
            if field not in data:
                logger.error(f"Missing required field '{field}' in {crew_name} data")
                return False

        # Validate metadata structure
        metadata = data.get("metadata", {})
        if not isinstance(metadata, dict):
            logger.error(f"Invalid metadata structure in {crew_name} data")
            return False

        # Check for crew_name in metadata
        if "crew_name" in metadata:
            stored_crew_name = metadata.get("crew_name")
            if stored_crew_name != crew_name:
                logger.error(f"Crew name mismatch: expected {crew_name}, got {stored_crew_name}")
                return False

        # Validate that data has some content (not just metadata)
        content_fields = ["raw_output", "json_dict", "pydantic", "tasks_output"]
        has_content = any(field in data for field in content_fields)

        if not has_content:
            logger.error(f"No content fields found in {crew_name} data. Expected at least one of: {content_fields}")
            return False

        return True
