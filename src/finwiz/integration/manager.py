"""
Crew Data Integration Manager.

Central manager for crew data integration and coordination.
Handles data flow between crews and ensures proper data accessibility.
"""

import logging
from pathlib import Path
from typing import Any

from finwiz.infrastructure.monitoring.freshness_checker import DataFreshnessChecker, FreshnessReport
from finwiz.orchestrators.registry.registry_manager import CrewConfig, ExecutionResult, RegistryManager, UpstreamDataCollection
from finwiz.validation.int_manager import ValidationManager, ValidationResult

from .schema import SchemaManager


class CrewDataIntegrationManager:
    """
    Central manager for crew data integration and coordination.

    This class orchestrates data flow between crews, validates outputs,
    and ensures proper data accessibility for downstream crews.
    """

    def __init__(self, output_dir: Path = Path("output"), config_path: Path | None = None) -> None:
        """
        Initialize the integration manager.

        Args:
            output_dir: Base directory for all crew outputs
            config_path: Path to configuration file (optional)

        """
        # Load configuration
        from .config import load_integration_config

        self.config = load_integration_config(config_path)

        # Use configured output directory if not explicitly provided
        if output_dir == Path("output") and self.config.output_dir != Path("output"):
            self.output_dir = self.config.output_dir
        else:
            self.output_dir = Path(output_dir)

        self.integration_dir = self.output_dir / self.config.integration_dir_name
        self.metadata_dir = self.integration_dir / self.config.metadata_dir_name
        self.contracts_dir = self.integration_dir / self.config.contracts_dir_name
        self.consolidated_dir = self.integration_dir / self.config.consolidated_dir_name

        # Set up logging
        self.logger = self._setup_logging()

        # Ensure directories exist
        self._ensure_directories()

        # Initialize freshness checker
        self.freshness_checker = DataFreshnessChecker(output_dir=self.output_dir, logger=self.logger)

        # Initialize component managers
        self.schema_manager = SchemaManager(self.logger)
        self.validation_manager = ValidationManager(self.metadata_dir, self.logger)
        self.registry_manager = RegistryManager(self.output_dir, self.metadata_dir, self.freshness_checker, self.logger)

        # Expose paths for backward compatibility with tests
        self.execution_log_path = self.metadata_dir / "crew_execution_log.json"
        self.data_lineage_path = self.metadata_dir / "data_lineage.json"
        self.validation_status_path = self.metadata_dir / "validation_status.json"

        self.logger.info(
            "CrewDataIntegrationManager initialized",
            extra={
                "output_dir": str(self.output_dir),
                "integration_dir": str(self.integration_dir),
                "config_loaded": config_path is not None,
                "strict_validation": self.config.strict_validation,
            },
        )

    def _setup_logging(self) -> logging.Logger:
        """Set up structured logging for integration operations."""
        logger = logging.getLogger("finwiz.integration")

        if not logger.handlers:
            # Create handler if it doesn't exist
            handler = logging.StreamHandler()

            # Use configured log format
            formatter = logging.Formatter(self.config.log_format)
            handler.setFormatter(formatter)
            logger.addHandler(handler)

            # Set configured log level
            log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
            logger.setLevel(log_level)

        return logger

    def _ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        directories = [self.integration_dir, self.metadata_dir, self.contracts_dir, self.consolidated_dir]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Ensured directory exists: {directory}")

    async def coordinate_crew_execution(self, crews: list[CrewConfig]) -> ExecutionResult:
        """
        Coordinate execution of multiple crews based on dependencies.

        Args:
            crews: List of crew configurations to execute

        Returns:
            ExecutionResult with success status and execution details

        """
        return await self.registry_manager.coordinate_crew_execution(crews)

    def store_crew_output(self, crew_name: str, crew_output: Any) -> bool:
        """
        Store crew output to the integration system.

        Args:
            crew_name: Name of the crew (e.g., 'stock', 'etf', 'crypto')
            crew_output: The crew output object (CrewOutput or similar)

        Returns:
            True if storage was successful, False otherwise

        """
        return self.registry_manager.store_crew_output(crew_name, crew_output)

    def get_cached_crew_output(self, crew_name: str) -> dict[str, Any] | None:
        """
        Get cached crew output if available.

        Args:
            crew_name: Name of the crew

        Returns:
            Cached crew output data, or None if not available

        """
        return self.registry_manager.get_cached_crew_output(crew_name)

    def validate_crew_output(self, crew_name: str, output_data: dict[str, Any]) -> ValidationResult:
        """
        Validate crew output against expected schema.

        Args:
            crew_name: Name of the crew
            output_data: Output data to validate

        Returns:
            ValidationResult with validation status and details

        """
        return self.validation_manager.validate_crew_output(crew_name, output_data)

    def get_upstream_data(self, requesting_crew: str, max_age_hours: int = 24) -> UpstreamDataCollection:
        """
        Get available upstream data for a requesting crew with freshness validation.

        Args:
            requesting_crew: Name of the crew requesting data
            max_age_hours: Maximum acceptable age in hours for data freshness

        Returns:
            UpstreamDataCollection with available, missing, and stale data

        """
        return self.registry_manager.get_upstream_data(requesting_crew, max_age_hours)

    def get_crew_data_with_freshness_check(self, crew_name: str, max_age_hours: int = 24, warn_on_stale: bool = True) -> dict | None:
        """
        Get crew data with automatic freshness validation and warnings.

        Args:
            crew_name: Name of the crew whose data to retrieve
            max_age_hours: Maximum acceptable age in hours
            warn_on_stale: Whether to log warnings for stale data

        Returns:
            Dictionary containing crew data, or None if not available

        """
        return self.registry_manager.get_crew_data_with_freshness_check(crew_name, max_age_hours, warn_on_stale)

    def get_refresh_recommendations(self, max_age_hours: int = 24) -> list[str]:
        """
        Get list of crews that should be refreshed based on data staleness.

        Args:
            max_age_hours: Maximum acceptable age in hours

        Returns:
            List of crew names in recommended refresh order

        """
        return self.registry_manager.get_refresh_recommendations(max_age_hours)

    def check_data_freshness(self, max_age_hours: int = 24) -> FreshnessReport:
        """
        Check freshness of all crew data using the DataFreshnessChecker.

        Args:
            max_age_hours: Maximum age in hours before data is considered stale

        Returns:
            FreshnessReport with freshness status

        """
        return self.registry_manager.check_data_freshness(max_age_hours)

    # Backward compatibility methods for tests
    def _load_json_file(self, file_path: Path, default: dict[str, Any]) -> dict[str, Any]:
        """Load JSON file with default fallback (backward compatibility)."""
        return self.schema_manager.load_json_file(file_path, default)

    def _save_json_file(self, file_path: Path, data: dict[str, Any]) -> None:
        """Save data to JSON file (backward compatibility)."""
        return self.schema_manager.save_json_file(file_path, data)

    def _sort_crews_by_dependencies(self, crews: list[CrewConfig]) -> list[CrewConfig]:
        """Sort crews by their dependencies (backward compatibility)."""
        result: list[CrewConfig] = self.registry_manager._sort_crews_by_dependencies(crews)
        return result
