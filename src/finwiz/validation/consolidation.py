"""
Data Consolidation Validator for FinWiz.

Validates that crew outputs are properly retrieved and consolidated.
Implements fail-fast behavior to prevent silent degradation.
"""

import logging
from typing import Any

from finwiz.orchestrators.registry.registry_manager import RegistryManager

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
        # Check for required fields in current crew output format
        # For consolidated data, we don't require 'ticker' since it represents multiple tickers
        required_fields = ["crew_name", "execution_id", "asset_class", "analysis_timestamp"]

        for field in required_fields:
            if field not in data:
                logger.error(f"Missing required field '{field}' in {crew_name} data")
                return False

        # Validate crew_name matches expected
        stored_crew_name = data.get("crew_name")
        if stored_crew_name and crew_name not in ["stock", "etf", "crypto"]:
            # For specific crew names, validate exact match
            if stored_crew_name != crew_name:
                logger.error(f"Crew name mismatch: expected {crew_name}, got {stored_crew_name}")
                return False

        # For consolidated data, check for ticker_analyses and summary_statistics
        if "ticker_analyses" in data and "summary_statistics" in data:
            # This is consolidated data - validate the structure
            ticker_analyses = data.get("ticker_analyses", {})
            if not isinstance(ticker_analyses, dict):
                logger.error(f"Invalid ticker_analyses structure in {crew_name} data")
                return False

            summary_stats = data.get("summary_statistics", {})
            if not isinstance(summary_stats, dict):
                logger.error(f"Invalid summary_statistics structure in {crew_name} data")
                return False

            # Check that we have some ticker analyses
            if len(ticker_analyses) == 0:
                logger.error(f"No ticker analyses found in consolidated {crew_name} data")
                return False

            logger.debug(f"Validated consolidated {crew_name} data with {len(ticker_analyses)} ticker analyses")
            return True

        # For individual ticker data, check for analysis fields
        analysis_fields = ["composite_score", "grade", "recommendation", "rationale"]
        has_analysis = any(field in data for field in analysis_fields)

        if not has_analysis:
            logger.error(f"No analysis fields found in {crew_name} data. Expected at least one of: {analysis_fields}")
            return False

        # Validate essential analysis fields have valid values
        if "composite_score" in data:
            score = data.get("composite_score")
            if not isinstance(score, (int, float)) or not (0.0 <= score <= 1.0):
                logger.error(f"Invalid composite_score in {crew_name} data: {score}")
                return False

        if "grade" in data:
            grade = data.get("grade")
            valid_grades = ["A+", "A", "B+", "B", "C+", "C", "D+", "D", "F"]
            if grade not in valid_grades:
                logger.error(f"Invalid grade in {crew_name} data: {grade}")
                return False

        return True
