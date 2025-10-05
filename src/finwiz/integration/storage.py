"""
Crew Output Storage and Retrieval System.

Provides standardized storage and retrieval of crew outputs with metadata
persistence and data lineage tracking.
"""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from finwiz.schemas.integration import CrewOutputMetadata


class StorageResult(BaseModel):
    """Result of storage operation."""

    success: bool = Field(description="Whether storage was successful")
    storage_path: str | None = Field(default=None, description="Path where data was stored")
    metadata_path: str | None = Field(default=None, description="Path where metadata was stored")
    errors: list[str] = Field(default_factory=list, description="List of errors encountered")
    warnings: list[str] = Field(default_factory=list, description="List of warnings")


class RetrievalResult(BaseModel):
    """Result of retrieval operation."""

    success: bool = Field(description="Whether retrieval was successful")
    data: dict[str, Any] | None = Field(default=None, description="Retrieved data")
    metadata: CrewOutputMetadata | None = Field(default=None, description="Retrieved metadata")
    errors: list[str] = Field(default_factory=list, description="List of errors encountered")
    warnings: list[str] = Field(default_factory=list, description="List of warnings")


class StorageQuery(BaseModel):
    """Query parameters for storage retrieval."""

    crew_name: str | None = Field(default=None, description="Filter by crew name")
    start_date: datetime | None = Field(default=None, description="Filter by start date")
    end_date: datetime | None = Field(default=None, description="Filter by end date")
    max_age_hours: int | None = Field(default=None, description="Maximum age in hours")
    include_invalid: bool = Field(default=False, description="Include invalid outputs")
    limit: int | None = Field(default=None, description="Maximum number of results")


class CrewOutputStorage:
    """
    Standardized crew output storage and retrieval system.

    Provides centralized storage of crew outputs with comprehensive metadata,
    data lineage tracking, and efficient retrieval capabilities.
    """

    def __init__(self, output_dir: Path = Path("output")) -> None:
        """
        Initialize the storage system.

        Args:
            output_dir: Base directory for all crew outputs

        """
        self.output_dir = Path(output_dir)
        self.integration_dir = self.output_dir / "integration"
        self.storage_dir = self.integration_dir / "storage"
        self.metadata_dir = self.integration_dir / "metadata"
        self.lineage_dir = self.integration_dir / "lineage"

        # Set up logging
        self.logger = self._setup_logging()

        # Ensure directories exist
        self._ensure_directories()

        # Storage configuration
        self.max_storage_size_mb = 1000  # Maximum storage size per crew in MB
        self.retention_days = 30  # Default retention period

        self.logger.info(
            "CrewOutputStorage initialized", extra={"output_dir": str(self.output_dir), "storage_dir": str(self.storage_dir)}
        )

    def _setup_logging(self) -> logging.Logger:
        """Set up structured logging for storage operations."""
        logger = logging.getLogger("finwiz.integration.storage")

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

        return logger

    def _ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        directories = [self.integration_dir, self.storage_dir, self.metadata_dir, self.lineage_dir]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Ensured directory exists: {directory}")

    def store_crew_output(
        self, crew_name: str, output_data: dict[str, Any], metadata: CrewOutputMetadata, execution_id: str | None = None
    ) -> StorageResult:
        """
        Store crew output with comprehensive metadata.

        Args:
            crew_name: Name of the crew
            output_data: Output data to store
            metadata: Crew output metadata
            execution_id: Optional execution identifier

        Returns:
            StorageResult with storage status and paths

        """
        self.logger.info(
            f"Storing output for crew: {crew_name}",
            extra={"crew_name": crew_name, "execution_id": execution_id, "data_size": len(json.dumps(output_data, default=str))},
        )

        try:
            # Generate execution ID if not provided
            if not execution_id:
                execution_id = self._generate_execution_id(crew_name)

            # Create crew-specific storage directory
            crew_storage_dir = self.storage_dir / crew_name
            crew_storage_dir.mkdir(parents=True, exist_ok=True)

            # Generate storage paths
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            storage_filename = f"{crew_name}_{timestamp}_{execution_id}.json"
            metadata_filename = f"{crew_name}_{timestamp}_{execution_id}_metadata.json"

            storage_path = crew_storage_dir / storage_filename
            metadata_path = self.metadata_dir / metadata_filename

            # Prepare storage data
            storage_data = {
                "execution_id": execution_id,
                "crew_name": crew_name,
                "timestamp": datetime.now().isoformat(),
                "data": output_data,
                "data_hash": self._calculate_data_hash(output_data),
                "storage_version": "1.0",
            }

            # Store output data
            with open(storage_path, "w", encoding="utf-8") as f:
                json.dump(storage_data, f, indent=2, ensure_ascii=False, default=str)

            # Store metadata (without extra fields that aren't in the schema)
            metadata_dict = metadata.model_dump()
            # Add storage-specific metadata separately
            storage_metadata = {
                "crew_output_metadata": metadata_dict,
                "storage_path": str(storage_path),
                "execution_id": execution_id,
                "storage_timestamp": datetime.now().isoformat(),
            }

            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(storage_metadata, f, indent=2, ensure_ascii=False, default=str)

            # Update data lineage
            self._update_lineage(crew_name, execution_id, storage_path, metadata_path)

            # Check storage limits
            warnings = self._check_storage_limits(crew_name)

            result = StorageResult(
                success=True, storage_path=str(storage_path), metadata_path=str(metadata_path), warnings=warnings
            )

            self.logger.info(
                f"Successfully stored output for crew: {crew_name}",
                extra={
                    "crew_name": crew_name,
                    "execution_id": execution_id,
                    "storage_path": str(storage_path),
                    "metadata_path": str(metadata_path),
                },
            )

            return result

        except Exception as e:
            error_msg = f"Failed to store output for crew {crew_name}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)

            return StorageResult(success=False, errors=[error_msg])

    def retrieve_crew_output(self, crew_name: str, execution_id: str | None = None, latest: bool = True) -> RetrievalResult:
        """
        Retrieve crew output by crew name and optional execution ID.

        Args:
            crew_name: Name of the crew
            execution_id: Optional specific execution ID
            latest: Whether to get the latest output if execution_id not specified

        Returns:
            RetrievalResult with retrieved data and metadata

        """
        self.logger.info(
            f"Retrieving output for crew: {crew_name}",
            extra={"crew_name": crew_name, "execution_id": execution_id, "latest": latest},
        )

        try:
            crew_storage_dir = self.storage_dir / crew_name

            if not crew_storage_dir.exists():
                return RetrievalResult(success=False, errors=[f"No storage directory found for crew: {crew_name}"])

            # Find matching files
            if execution_id:
                # Look for specific execution ID
                storage_files = list(crew_storage_dir.glob(f"*_{execution_id}.json"))
            else:
                # Get all storage files
                storage_files = list(crew_storage_dir.glob("*.json"))

            if not storage_files:
                return RetrievalResult(success=False, errors=[f"No output files found for crew: {crew_name}"])

            # Select file to retrieve
            if latest and not execution_id:
                # Get the most recent file
                storage_file = max(storage_files, key=lambda f: f.stat().st_mtime)
            else:
                storage_file = storage_files[0]

            # Load storage data
            with open(storage_file, encoding="utf-8") as f:
                storage_data = json.load(f)

            # Load corresponding metadata
            metadata = None
            execution_id_from_file = storage_data.get("execution_id")
            if execution_id_from_file:
                metadata_files = list(self.metadata_dir.glob(f"*_{execution_id_from_file}_metadata.json"))
                if metadata_files:
                    with open(metadata_files[0], encoding="utf-8") as f:
                        storage_metadata = json.load(f)
                        # Extract the crew output metadata from the storage metadata
                        metadata_dict = storage_metadata.get("crew_output_metadata", storage_metadata)
                        # Convert datetime strings back to datetime objects
                        for key in ["execution_timestamp", "validation_timestamp"]:
                            if key in metadata_dict and isinstance(metadata_dict[key], str):
                                metadata_dict[key] = datetime.fromisoformat(metadata_dict[key])
                        # Handle nested validation_status datetime
                        if "validation_status" in metadata_dict and isinstance(metadata_dict["validation_status"], dict):
                            vs = metadata_dict["validation_status"]
                            if "validation_timestamp" in vs and isinstance(vs["validation_timestamp"], str):
                                vs["validation_timestamp"] = datetime.fromisoformat(vs["validation_timestamp"])
                        # Handle nested freshness_status datetime
                        if "freshness_status" in metadata_dict and isinstance(metadata_dict["freshness_status"], dict):
                            fs = metadata_dict["freshness_status"]
                            if "last_updated" in fs and isinstance(fs["last_updated"], str):
                                fs["last_updated"] = datetime.fromisoformat(fs["last_updated"])
                        # Handle data_sources datetime
                        if "data_sources" in metadata_dict and isinstance(metadata_dict["data_sources"], list):
                            for ds in metadata_dict["data_sources"]:
                                if isinstance(ds, dict) and "accessed_at" in ds and isinstance(ds["accessed_at"], str):
                                    ds["accessed_at"] = datetime.fromisoformat(ds["accessed_at"])
                        metadata = CrewOutputMetadata(**metadata_dict)

            result = RetrievalResult(success=True, data=storage_data.get("data"), metadata=metadata)

            self.logger.info(
                f"Successfully retrieved output for crew: {crew_name}",
                extra={"crew_name": crew_name, "execution_id": execution_id_from_file, "storage_file": str(storage_file)},
            )

            return result

        except Exception as e:
            error_msg = f"Failed to retrieve output for crew {crew_name}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)

            return RetrievalResult(success=False, errors=[error_msg])

    def query_crew_outputs(self, query: StorageQuery) -> list[RetrievalResult]:
        """
        Query crew outputs based on specified criteria.

        Args:
            query: Query parameters

        Returns:
            List of RetrievalResult matching the query

        """
        self.logger.info(
            "Querying crew outputs",
            extra={
                "crew_name": query.crew_name,
                "start_date": query.start_date,
                "end_date": query.end_date,
                "max_age_hours": query.max_age_hours,
                "limit": query.limit,
            },
        )

        try:
            results = []

            # Determine which crews to search
            if query.crew_name:
                crew_dirs = [self.storage_dir / query.crew_name]
            else:
                crew_dirs = [d for d in self.storage_dir.iterdir() if d.is_dir()]

            for crew_dir in crew_dirs:
                if not crew_dir.exists():
                    continue

                storage_files = list(crew_dir.glob("*.json"))

                for storage_file in storage_files:
                    try:
                        # Check file age if specified
                        if query.max_age_hours:
                            file_age_hours = (
                                datetime.now() - datetime.fromtimestamp(storage_file.stat().st_mtime)
                            ).total_seconds() / 3600

                            if file_age_hours > query.max_age_hours:
                                continue

                        # Load and check data
                        with open(storage_file, encoding="utf-8") as f:
                            storage_data = json.load(f)

                        # Check date filters
                        file_timestamp = datetime.fromisoformat(storage_data.get("timestamp", ""))

                        if query.start_date and file_timestamp < query.start_date:
                            continue

                        if query.end_date and file_timestamp > query.end_date:
                            continue

                        # Load metadata if available
                        metadata = None
                        execution_id = storage_data.get("execution_id")
                        if execution_id:
                            metadata_files = list(self.metadata_dir.glob(f"*_{execution_id}_metadata.json"))
                            if metadata_files:
                                with open(metadata_files[0], encoding="utf-8") as f:
                                    storage_metadata = json.load(f)
                                    # Extract the crew output metadata from the storage metadata
                                    metadata_dict = storage_metadata.get("crew_output_metadata", storage_metadata)
                                    # Convert datetime strings
                                    for key in ["execution_timestamp", "validation_timestamp"]:
                                        if key in metadata_dict and isinstance(metadata_dict[key], str):
                                            metadata_dict[key] = datetime.fromisoformat(metadata_dict[key])
                                    # Handle nested validation_status datetime
                                    if "validation_status" in metadata_dict and isinstance(
                                        metadata_dict["validation_status"], dict
                                    ):
                                        vs = metadata_dict["validation_status"]
                                        if "validation_timestamp" in vs and isinstance(vs["validation_timestamp"], str):
                                            vs["validation_timestamp"] = datetime.fromisoformat(vs["validation_timestamp"])
                                    # Handle nested freshness_status datetime
                                    if "freshness_status" in metadata_dict and isinstance(metadata_dict["freshness_status"], dict):
                                        fs = metadata_dict["freshness_status"]
                                        if "last_updated" in fs and isinstance(fs["last_updated"], str):
                                            fs["last_updated"] = datetime.fromisoformat(fs["last_updated"])
                                    # Handle data_sources datetime
                                    if "data_sources" in metadata_dict and isinstance(metadata_dict["data_sources"], list):
                                        for ds in metadata_dict["data_sources"]:
                                            if isinstance(ds, dict) and "accessed_at" in ds and isinstance(ds["accessed_at"], str):
                                                ds["accessed_at"] = datetime.fromisoformat(ds["accessed_at"])
                                    metadata = CrewOutputMetadata(**metadata_dict)

                        # Check validation status filter
                        if not query.include_invalid and metadata:
                            if not metadata.validation_status.is_valid:
                                continue

                        results.append(RetrievalResult(success=True, data=storage_data.get("data"), metadata=metadata))

                        # Check limit
                        if query.limit and len(results) >= query.limit:
                            break

                    except Exception as e:
                        self.logger.warning(f"Failed to process file {storage_file}: {str(e)}")
                        continue

                # Check limit
                if query.limit and len(results) >= query.limit:
                    break

            self.logger.info(f"Query completed, found {len(results)} results")
            return results

        except Exception as e:
            error_msg = f"Query failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)

            return [RetrievalResult(success=False, errors=[error_msg])]

    def get_data_lineage(self, crew_name: str | None = None) -> dict[str, Any]:
        """
        Get data lineage information for crews.

        Args:
            crew_name: Optional crew name to filter lineage

        Returns:
            Dictionary containing lineage information

        """
        try:
            lineage_file = self.lineage_dir / "data_lineage.json"

            if not lineage_file.exists():
                return {"executions": [], "summary": {"total_executions": 0}}

            with open(lineage_file, encoding="utf-8") as f:
                lineage_data = json.load(f)

            if crew_name:
                # Filter by crew name
                filtered_executions = [
                    exec_data for exec_data in lineage_data.get("executions", []) if exec_data.get("crew_name") == crew_name
                ]
                lineage_data["executions"] = filtered_executions

            # Add summary information
            executions = lineage_data.get("executions", [])
            lineage_data["summary"] = {
                "total_executions": len(executions),
                "crews": list(set(exec_data.get("crew_name") for exec_data in executions)),
                "date_range": {
                    "earliest": min((exec_data.get("timestamp") for exec_data in executions), default=None),
                    "latest": max((exec_data.get("timestamp") for exec_data in executions), default=None),
                },
            }

            return lineage_data

        except Exception as e:
            error_msg = f"Failed to get data lineage: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return {"error": error_msg, "executions": []}

    def cleanup_old_outputs(self, retention_days: int | None = None) -> dict[str, Any]:
        """
        Clean up old crew outputs based on retention policy.

        Args:
            retention_days: Number of days to retain outputs (uses default if None)

        Returns:
            Dictionary with cleanup results

        """
        retention_days = retention_days or self.retention_days
        cutoff_date = datetime.now().timestamp() - (retention_days * 24 * 3600)

        self.logger.info(f"Starting cleanup of outputs older than {retention_days} days")

        try:
            deleted_files = []
            errors = []

            # Clean up storage files
            for crew_dir in self.storage_dir.iterdir():
                if not crew_dir.is_dir():
                    continue

                for storage_file in crew_dir.glob("*.json"):
                    if storage_file.stat().st_mtime < cutoff_date:
                        try:
                            storage_file.unlink()
                            deleted_files.append(str(storage_file))
                        except Exception as e:
                            errors.append(f"Failed to delete {storage_file}: {str(e)}")

            # Clean up metadata files
            for metadata_file in self.metadata_dir.glob("*.json"):
                if metadata_file.stat().st_mtime < cutoff_date:
                    try:
                        metadata_file.unlink()
                        deleted_files.append(str(metadata_file))
                    except Exception as e:
                        errors.append(f"Failed to delete {metadata_file}: {str(e)}")

            result = {
                "deleted_count": len(deleted_files),
                "deleted_files": deleted_files,
                "errors": errors,
                "retention_days": retention_days,
            }

            self.logger.info(f"Cleanup completed, deleted {len(deleted_files)} files")
            return result

        except Exception as e:
            error_msg = f"Cleanup failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return {"error": error_msg, "deleted_count": 0}

    def _generate_execution_id(self, crew_name: str) -> str:
        """Generate unique execution ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        return f"{crew_name}_{timestamp}"

    def _calculate_data_hash(self, data: dict[str, Any]) -> str:
        """Calculate hash of data for integrity checking."""
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def _update_lineage(self, crew_name: str, execution_id: str, storage_path: Path, metadata_path: Path) -> None:
        """Update data lineage tracking."""
        try:
            lineage_file = self.lineage_dir / "data_lineage.json"

            # Load existing lineage
            lineage_data = {"executions": []}
            if lineage_file.exists():
                with open(lineage_file, encoding="utf-8") as f:
                    lineage_data = json.load(f)

            # Add new execution
            lineage_entry = {
                "execution_id": execution_id,
                "crew_name": crew_name,
                "timestamp": datetime.now().isoformat(),
                "storage_path": str(storage_path),
                "metadata_path": str(metadata_path),
            }

            lineage_data["executions"].append(lineage_entry)

            # Keep only last 10000 entries to prevent file from growing too large
            if len(lineage_data["executions"]) > 10000:
                lineage_data["executions"] = lineage_data["executions"][-10000:]

            # Save updated lineage
            with open(lineage_file, "w", encoding="utf-8") as f:
                json.dump(lineage_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger.warning(f"Failed to update lineage: {str(e)}")

    def _check_storage_limits(self, crew_name: str) -> list[str]:
        """Check storage limits and return warnings if exceeded."""
        warnings = []

        try:
            crew_storage_dir = self.storage_dir / crew_name
            if not crew_storage_dir.exists():
                return warnings

            # Calculate total size
            total_size = sum(f.stat().st_size for f in crew_storage_dir.rglob("*") if f.is_file())
            total_size_mb = total_size / (1024 * 1024)

            if total_size_mb > self.max_storage_size_mb:
                warnings.append(
                    f"Storage size for {crew_name} ({total_size_mb:.1f}MB) exceeds limit ({self.max_storage_size_mb}MB)"
                )

        except Exception as e:
            self.logger.warning(f"Failed to check storage limits: {str(e)}")

        return warnings
