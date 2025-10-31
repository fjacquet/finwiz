"""
Integration tests for CrewOutputStorage.

Tests storage, retrieval, querying, and data lineage functionality.
"""

import json
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from finwiz.integration.storage import CrewOutputStorage, RetrievalResult, StorageQuery, StorageResult
from finwiz.schemas.integration import (
    CrewOutputMetadata,
    DataQuality,
    DataSource,
    DataSourceType,
    FreshnessStatus,
    ValidationStatus,
)


class TestCrewOutputStorage:
    """Test suite for CrewOutputStorage."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def storage(self, temp_output_dir):
        """Create storage instance with temporary directory."""
        return CrewOutputStorage(output_dir=temp_output_dir)

    @pytest.fixture
    def sample_metadata(self):
        """Create sample crew output metadata."""
        return CrewOutputMetadata(
            crew_name="test_crew",
            execution_timestamp=datetime.now(),
            schema_version=1,
            validation_status=ValidationStatus(is_valid=True, validation_timestamp=datetime.now(), validation_errors=[], validation_warnings=[], schema_version=1),
            data_sources=[
                DataSource(
                    source_type=DataSourceType.YAHOO_FINANCE,
                    accessed_at=datetime.now(),
                    data_quality=DataQuality.HIGH,
                    response_time_ms=150.0,
                )
            ],
            dependencies_met=True,
            freshness_status=FreshnessStatus(is_fresh=True, age_hours=0.5, max_age_hours=24, refresh_recommended=False, last_updated=datetime.now()),
            execution_duration_seconds=5.2,
        )

    @pytest.fixture
    def sample_output_data(self):
        """Create sample crew output data."""
        return {
            "analysis": {"ticker": "AAPL", "recommendation": "BUY", "confidence": 0.85, "price_target": 180.0},
            "risk_assessment": {"risk_score": 3, "risk_factors": ["Market volatility", "Sector rotation"]},
            "metadata": {"analysis_date": datetime.now().isoformat(), "data_sources": ["Yahoo Finance", "SEC EDGAR"]},
        }

    def test_should_initialize_storage_with_directories(self, temp_output_dir):
        """Test storage initialization creates required directories."""
        # Act
        storage = CrewOutputStorage(output_dir=temp_output_dir)

        # Assert
        assert storage.output_dir == temp_output_dir
        assert storage.integration_dir.exists()
        assert storage.storage_dir.exists()
        assert storage.metadata_dir.exists()
        assert storage.lineage_dir.exists()

    def test_should_store_crew_output_successfully(self, storage, sample_metadata, sample_output_data):
        """Test successful storage of crew output with metadata."""
        # Arrange
        crew_name = "test_crew"
        execution_id = "test_exec_123"

        # Act
        result = storage.store_crew_output(crew_name=crew_name, output_data=sample_output_data, metadata=sample_metadata, execution_id=execution_id)

        # Assert
        assert result.success is True
        assert result.storage_path is not None
        assert result.metadata_path is not None
        assert len(result.errors) == 0

        # Verify files were created
        storage_path = Path(result.storage_path)
        metadata_path = Path(result.metadata_path)
        assert storage_path.exists()
        assert metadata_path.exists()

        # Verify storage content
        with open(storage_path) as f:
            stored_data = json.load(f)
        assert stored_data["execution_id"] == execution_id
        assert stored_data["crew_name"] == crew_name
        assert stored_data["data"] == sample_output_data
        assert "data_hash" in stored_data
        assert "timestamp" in stored_data

        # Verify metadata content
        with open(metadata_path) as f:
            stored_metadata = json.load(f)
        assert stored_metadata["crew_name"] == crew_name
        assert stored_metadata["execution_id"] == execution_id
        assert stored_metadata["storage_path"] == str(storage_path)

    def test_should_generate_execution_id_when_not_provided(self, storage, sample_metadata, sample_output_data):
        """Test automatic generation of execution ID when not provided."""
        # Arrange
        crew_name = "test_crew"

        # Act
        result = storage.store_crew_output(crew_name=crew_name, output_data=sample_output_data, metadata=sample_metadata)

        # Assert
        assert result.success is True

        # Verify execution ID was generated
        with open(result.storage_path) as f:
            stored_data = json.load(f)
        assert stored_data["execution_id"] is not None
        assert stored_data["execution_id"].startswith(crew_name)

    def test_should_update_data_lineage_on_storage(self, storage, sample_metadata, sample_output_data):
        """Test that data lineage is updated when storing outputs."""
        # Arrange
        crew_name = "test_crew"
        execution_id = "test_exec_123"

        # Act
        result = storage.store_crew_output(crew_name=crew_name, output_data=sample_output_data, metadata=sample_metadata, execution_id=execution_id)

        # Assert
        assert result.success is True

        # Verify lineage was updated
        lineage = storage.get_data_lineage()
        assert "executions" in lineage
        assert len(lineage["executions"]) == 1

        lineage_entry = lineage["executions"][0]
        assert lineage_entry["execution_id"] == execution_id
        assert lineage_entry["crew_name"] == crew_name
        assert lineage_entry["storage_path"] == result.storage_path
        assert lineage_entry["metadata_path"] == result.metadata_path

    def test_should_retrieve_crew_output_by_name(self, storage, sample_metadata, sample_output_data):
        """Test retrieval of crew output by crew name."""
        # Arrange
        crew_name = "test_crew"
        execution_id = "test_exec_123"

        # Store output first
        storage.store_crew_output(crew_name=crew_name, output_data=sample_output_data, metadata=sample_metadata, execution_id=execution_id)

        # Act
        result = storage.retrieve_crew_output(crew_name=crew_name)

        # Assert
        assert result.success is True
        assert result.data == sample_output_data
        assert result.metadata is not None
        assert result.metadata.crew_name == crew_name
        assert len(result.errors) == 0

    def test_should_retrieve_crew_output_by_execution_id(self, storage, sample_metadata, sample_output_data):
        """Test retrieval of crew output by specific execution ID."""
        # Arrange
        crew_name = "test_crew"
        execution_id = "test_exec_123"

        # Store output first
        storage.store_crew_output(crew_name=crew_name, output_data=sample_output_data, metadata=sample_metadata, execution_id=execution_id)

        # Act
        result = storage.retrieve_crew_output(crew_name=crew_name, execution_id=execution_id)

        # Assert
        assert result.success is True
        assert result.data == sample_output_data
        assert result.metadata is not None
        assert len(result.errors) == 0

    def test_should_return_error_for_nonexistent_crew(self, storage):
        """Test error handling when retrieving nonexistent crew output."""
        # Act
        result = storage.retrieve_crew_output(crew_name="nonexistent_crew")

        # Assert
        assert result.success is False
        assert result.data is None
        assert result.metadata is None
        assert len(result.errors) > 0
        assert "No storage directory found" in result.errors[0]

    def test_should_retrieve_latest_output_when_multiple_exist(self, storage, sample_metadata, sample_output_data):
        """Test retrieval of latest output when multiple outputs exist for a crew."""
        # Arrange
        crew_name = "test_crew"

        # Store multiple outputs with slight delays
        storage.store_crew_output(crew_name=crew_name, output_data={"version": 1}, metadata=sample_metadata, execution_id="exec_1")

        # Modify metadata for second storage
        newer_metadata = sample_metadata.model_copy()
        newer_metadata.execution_timestamp = datetime.now() + timedelta(seconds=1)

        storage.store_crew_output(crew_name=crew_name, output_data={"version": 2}, metadata=newer_metadata, execution_id="exec_2")

        # Act
        result = storage.retrieve_crew_output(crew_name=crew_name, latest=True)

        # Assert
        assert result.success is True
        assert result.data["version"] == 2  # Should get the newer version

    def test_should_query_outputs_by_crew_name(self, storage, sample_metadata, sample_output_data):
        """Test querying outputs by crew name."""
        # Arrange
        crew_names = ["crew_a", "crew_b", "crew_c"]

        for crew_name in crew_names:
            storage.store_crew_output(crew_name=crew_name, output_data={"crew": crew_name}, metadata=sample_metadata)

        # Act
        query = StorageQuery(crew_name="crew_b")
        results = storage.query_crew_outputs(query)

        # Assert
        assert len(results) == 1
        assert results[0].success is True
        assert results[0].data["crew"] == "crew_b"

    def test_should_query_outputs_by_date_range(self, storage, sample_metadata, sample_output_data):
        """Test querying outputs by date range."""
        # Arrange
        base_time = datetime.now()

        # Store outputs with different timestamps
        for i in range(3):
            metadata = sample_metadata.model_copy()
            metadata.execution_timestamp = base_time + timedelta(hours=i)

            storage.store_crew_output(crew_name=f"crew_{i}", output_data={"hour": i}, metadata=metadata)

        # Act - Query for outputs in middle hour
        query = StorageQuery(start_date=base_time + timedelta(minutes=30), end_date=base_time + timedelta(hours=1, minutes=30))
        results = storage.query_crew_outputs(query)

        # Assert
        assert len(results) == 1
        assert results[0].data["hour"] == 1

    def test_should_query_outputs_with_limit(self, storage, sample_metadata, sample_output_data):
        """Test querying outputs with result limit."""
        # Arrange
        for i in range(5):
            storage.store_crew_output(crew_name=f"crew_{i}", output_data={"index": i}, metadata=sample_metadata)

        # Act
        query = StorageQuery(limit=3)
        results = storage.query_crew_outputs(query)

        # Assert
        assert len(results) == 3
        assert all(result.success for result in results)

    def test_should_filter_invalid_outputs_in_query(self, storage, sample_output_data):
        """Test filtering of invalid outputs in queries."""
        # Arrange
        valid_metadata = CrewOutputMetadata(
            crew_name="valid_crew",
            execution_timestamp=datetime.now(),
            schema_version=1,
            validation_status=ValidationStatus(is_valid=True, validation_timestamp=datetime.now(), validation_errors=[], validation_warnings=[], schema_version=1),
            dependencies_met=True,
            freshness_status=FreshnessStatus(is_fresh=True, age_hours=0.5, max_age_hours=24, refresh_recommended=False, last_updated=datetime.now()),
        )

        invalid_metadata = valid_metadata.model_copy()
        invalid_metadata.validation_status.is_valid = False
        invalid_metadata.validation_status.validation_errors = ["Schema error"]

        # Store valid and invalid outputs
        storage.store_crew_output(crew_name="valid_crew", output_data={"status": "valid"}, metadata=valid_metadata)

        storage.store_crew_output(crew_name="invalid_crew", output_data={"status": "invalid"}, metadata=invalid_metadata)

        # Act - Query without including invalid
        query = StorageQuery(include_invalid=False)
        results = storage.query_crew_outputs(query)

        # Assert
        assert len(results) == 1
        assert results[0].data["status"] == "valid"

        # Act - Query including invalid
        query_with_invalid = StorageQuery(include_invalid=True)
        results_with_invalid = storage.query_crew_outputs(query_with_invalid)

        # Assert
        assert len(results_with_invalid) == 2

    def test_should_get_data_lineage_for_all_crews(self, storage, sample_metadata, sample_output_data):
        """Test retrieval of complete data lineage."""
        # Arrange
        crews = ["crew_a", "crew_b", "crew_c"]

        for crew_name in crews:
            storage.store_crew_output(crew_name=crew_name, output_data={"crew": crew_name}, metadata=sample_metadata)

        # Act
        lineage = storage.get_data_lineage()

        # Assert
        assert "executions" in lineage
        assert "summary" in lineage
        assert len(lineage["executions"]) == 3
        assert lineage["summary"]["total_executions"] == 3
        assert set(lineage["summary"]["crews"]) == set(crews)
        assert lineage["summary"]["date_range"]["earliest"] is not None
        assert lineage["summary"]["date_range"]["latest"] is not None

    def test_should_get_filtered_data_lineage_by_crew(self, storage, sample_metadata, sample_output_data):
        """Test retrieval of filtered data lineage by crew name."""
        # Arrange
        crews = ["crew_a", "crew_b", "crew_c"]

        for crew_name in crews:
            storage.store_crew_output(crew_name=crew_name, output_data={"crew": crew_name}, metadata=sample_metadata)

        # Act
        lineage = storage.get_data_lineage(crew_name="crew_b")

        # Assert
        assert len(lineage["executions"]) == 1
        assert lineage["executions"][0]["crew_name"] == "crew_b"
        assert lineage["summary"]["total_executions"] == 1
        assert lineage["summary"]["crews"] == ["crew_b"]

    def test_should_cleanup_old_outputs(self, storage, sample_metadata, sample_output_data):
        """Test cleanup of old outputs based on retention policy."""
        # Arrange
        crew_name = "test_crew"

        # Store output
        result = storage.store_crew_output(crew_name=crew_name, output_data=sample_output_data, metadata=sample_metadata)

        # Manually modify file timestamps to make them old
        storage_path = Path(result.storage_path)
        metadata_path = Path(result.metadata_path)

        old_timestamp = (datetime.now() - timedelta(days=35)).timestamp()
        import os

        os.utime(storage_path, (old_timestamp, old_timestamp))
        os.utime(metadata_path, (old_timestamp, old_timestamp))

        # Act
        cleanup_result = storage.cleanup_old_outputs(retention_days=30)

        # Assert
        assert cleanup_result["deleted_count"] == 2
        assert str(storage_path) in cleanup_result["deleted_files"]
        assert str(metadata_path) in cleanup_result["deleted_files"]
        assert len(cleanup_result["errors"]) == 0

        # Verify files were actually deleted
        assert not storage_path.exists()
        assert not metadata_path.exists()

    def test_should_handle_storage_errors_gracefully(self, storage, sample_metadata):
        """Test error handling during storage operations."""

        # Arrange - Use invalid data that will cause JSON serialization to fail
        class NonSerializable:
            def __str__(self):
                raise Exception("Cannot serialize this object")

        invalid_data = {"invalid": NonSerializable()}

        # Act
        result = storage.store_crew_output(crew_name="test_crew", output_data=invalid_data, metadata=sample_metadata)

        # Assert
        assert result.success is False
        assert len(result.errors) > 0
        assert result.storage_path is None
        assert result.metadata_path is None

    def test_should_handle_retrieval_errors_gracefully(self, storage):
        """Test error handling during retrieval operations."""
        # Act - Try to retrieve from non-existent crew
        result = storage.retrieve_crew_output(crew_name="nonexistent_crew")

        # Assert
        assert result.success is False
        assert result.data is None
        assert result.metadata is None
        assert len(result.errors) > 0

    def test_should_check_storage_limits(self, storage, sample_metadata, sample_output_data):
        """Test storage limit checking and warnings."""
        # Arrange - Set a very low storage limit for testing
        storage.max_storage_size_mb = 0.001  # 1KB limit

        crew_name = "test_crew"

        # Act - Store large data that exceeds limit
        large_data = {"large_field": "x" * 10000}  # 10KB of data
        result = storage.store_crew_output(crew_name=crew_name, output_data=large_data, metadata=sample_metadata)

        # Assert
        assert result.success is True  # Storage should still succeed
        assert len(result.warnings) > 0
        assert "exceeds limit" in result.warnings[0]

    def test_should_maintain_lineage_size_limit(self, storage, sample_metadata, sample_output_data):
        """Test that lineage file doesn't grow beyond size limit."""
        # Arrange - Mock a large number of executions
        lineage_file = storage.lineage_dir / "data_lineage.json"

        # Create initial lineage with many entries
        large_lineage = {
            "executions": [
                {
                    "execution_id": f"exec_{i}",
                    "crew_name": "test_crew",
                    "timestamp": datetime.now().isoformat(),
                    "storage_path": f"/path/to/storage_{i}",
                    "metadata_path": f"/path/to/metadata_{i}",
                }
                for i in range(10005)  # More than the 10000 limit
            ]
        }

        with open(lineage_file, "w") as f:
            json.dump(large_lineage, f)

        # Act - Store new output which should trigger lineage cleanup
        storage.store_crew_output(crew_name="new_crew", output_data=sample_output_data, metadata=sample_metadata)

        # Assert
        lineage = storage.get_data_lineage()
        assert len(lineage["executions"]) == 10000  # Should be limited to 10000

        # Verify the newest entry is included
        newest_entry = lineage["executions"][-1]
        assert newest_entry["crew_name"] == "new_crew"


class TestStorageQuery:
    """Test StorageQuery model."""

    def test_should_create_valid_storage_query(self):
        """Test creation of valid StorageQuery."""
        # Arrange
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()

        # Act
        query = StorageQuery(crew_name="test_crew", start_date=start_date, end_date=end_date, max_age_hours=24, include_invalid=True, limit=10)

        # Assert
        assert query.crew_name == "test_crew"
        assert query.start_date == start_date
        assert query.end_date == end_date
        assert query.max_age_hours == 24
        assert query.include_invalid is True
        assert query.limit == 10

    def test_should_create_query_with_defaults(self):
        """Test creation of StorageQuery with default values."""
        # Act
        query = StorageQuery()

        # Assert
        assert query.crew_name is None
        assert query.start_date is None
        assert query.end_date is None
        assert query.max_age_hours is None
        assert query.include_invalid is False
        assert query.limit is None


class TestStorageResult:
    """Test StorageResult model."""

    def test_should_create_successful_storage_result(self):
        """Test creation of successful StorageResult."""
        # Act
        result = StorageResult(
            success=True,
            storage_path="/path/to/storage.json",
            metadata_path="/path/to/metadata.json",
            warnings=["Storage limit warning"],
        )

        # Assert
        assert result.success is True
        assert result.storage_path == "/path/to/storage.json"
        assert result.metadata_path == "/path/to/metadata.json"
        assert result.errors == []
        assert result.warnings == ["Storage limit warning"]

    def test_should_create_failed_storage_result(self):
        """Test creation of failed StorageResult."""
        # Act
        result = StorageResult(success=False, errors=["Storage failed", "Disk full"])

        # Assert
        assert result.success is False
        assert result.storage_path is None
        assert result.metadata_path is None
        assert result.errors == ["Storage failed", "Disk full"]
        assert result.warnings == []


class TestRetrievalResult:
    """Test RetrievalResult model."""

    def test_should_create_successful_retrieval_result(self):
        """Test creation of successful RetrievalResult."""
        # Arrange
        data = {"test": "data"}
        metadata = CrewOutputMetadata(
            crew_name="test_crew",
            execution_timestamp=datetime.now(),
            schema_version=1,
            validation_status=ValidationStatus(is_valid=True, validation_timestamp=datetime.now(), validation_errors=[], validation_warnings=[], schema_version=1),
            dependencies_met=True,
            freshness_status=FreshnessStatus(is_fresh=True, age_hours=0.5, max_age_hours=24, refresh_recommended=False, last_updated=datetime.now()),
        )

        # Act
        result = RetrievalResult(success=True, data=data, metadata=metadata)

        # Assert
        assert result.success is True
        assert result.data == data
        assert result.metadata == metadata
        assert result.errors == []
        assert result.warnings == []

    def test_should_create_failed_retrieval_result(self):
        """Test creation of failed RetrievalResult."""
        # Act
        result = RetrievalResult(success=False, errors=["File not found", "Permission denied"])

        # Assert
        assert result.success is False
        assert result.data is None
        assert result.metadata is None
        assert result.errors == ["File not found", "Permission denied"]
        assert result.warnings == []
