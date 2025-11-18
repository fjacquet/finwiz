"""
Unit tests for Supabase MigrationService.

Tests migration service functionality including:
- Scanning for export files
- Extracting metadata from file paths
- Validating export data
- File hash calculation
"""

import json
from pathlib import Path

import pytest

from finwiz.supabase.services.migration_service import MigrationService


class TestMigrationService:
    """Test suite for MigrationService."""

    @pytest.fixture
    def migration_service(self, mocker):
        """Create MigrationService with mocked client."""
        mock_client = mocker.Mock()
        mock_client.enabled = True
        return MigrationService(client=mock_client, output_dir="output")

    @pytest.fixture
    def sample_export_data(self):
        """Create sample export data for testing."""
        return {
            "ticker": "AAPL",
            "asset_class": "stock",
            "composite_score": 0.85,
            "grade": "A+",
            "recommendation": "BUY",
            "analysis_timestamp": "2025-10-30T22:17:44Z",
            "fundamental_score": 0.90,
            "technical_score": 0.80,
            "risk_score": 0.85,
        }

    def test_should_extract_metadata_from_path(self, migration_service):
        """Test metadata extraction from file path."""
        # Arrange
        file_path = Path("output/stock/AAPL_default.json")

        # Act
        metadata = migration_service._extract_metadata_from_path(file_path)

        # Assert
        assert metadata["ticker"] == "AAPL"
        assert metadata["asset_class"] == "stock"

    def test_should_extract_metadata_with_complex_ticker(self, migration_service):
        """Test metadata extraction with complex ticker symbols."""
        # Arrange
        file_path = Path("output/stock/NESN.SW_default.json")

        # Act
        metadata = migration_service._extract_metadata_from_path(file_path)

        # Assert
        assert metadata["ticker"] == "NESN.SW"
        assert metadata["asset_class"] == "stock"

    def test_should_validate_export_data_with_required_fields(self, migration_service, sample_export_data):
        """Test validation passes with all required fields."""
        # Act
        is_valid = migration_service._validate_export_data(sample_export_data)

        # Assert
        assert is_valid is True

    def test_should_fail_validation_with_missing_ticker(self, migration_service, sample_export_data):
        """Test validation fails when ticker is missing."""
        # Arrange
        del sample_export_data["ticker"]

        # Act
        is_valid = migration_service._validate_export_data(sample_export_data)

        # Assert
        assert is_valid is False

    def test_should_fail_validation_with_missing_composite_score(self, migration_service, sample_export_data):
        """Test validation fails when composite_score is missing."""
        # Arrange
        del sample_export_data["composite_score"]

        # Act
        is_valid = migration_service._validate_export_data(sample_export_data)

        # Assert
        assert is_valid is False

    def test_should_calculate_file_hash(self, migration_service, tmp_path):
        """Test file hash calculation."""
        # Arrange
        test_file = tmp_path / "test.json"
        test_data = {"test": "data"}
        test_file.write_text(json.dumps(test_data))

        # Act
        hash1 = migration_service._calculate_file_hash(test_file)
        hash2 = migration_service._calculate_file_hash(test_file)

        # Assert
        assert hash1 == hash2  # Same file should produce same hash
        assert len(hash1) == 64  # SHA256 produces 64-character hex string

    def test_should_produce_different_hashes_for_different_files(self, migration_service, tmp_path):
        """Test that different files produce different hashes."""
        # Arrange
        file1 = tmp_path / "file1.json"
        file2 = tmp_path / "file2.json"
        file1.write_text(json.dumps({"data": "file1"}))
        file2.write_text(json.dumps({"data": "file2"}))

        # Act
        hash1 = migration_service._calculate_file_hash(file1)
        hash2 = migration_service._calculate_file_hash(file2)

        # Assert
        assert hash1 != hash2

    def test_should_scan_exports_with_no_files(self, migration_service, tmp_path):
        """Test scanning when no export files exist."""
        # Arrange
        migration_service.output_dir = tmp_path

        # Act
        files = migration_service.scan_exports()

        # Assert
        assert len(files) == 0

    def test_should_scan_exports_with_stock_files(self, migration_service, tmp_path):
        """Test scanning finds stock export files."""
        # Arrange
        migration_service.output_dir = tmp_path
        stock_dir = tmp_path / "stock"
        stock_dir.mkdir()

        # Create test files
        (stock_dir / "AAPL_default.json").write_text("{}")
        (stock_dir / "GOOGL_default.json").write_text("{}")
        (stock_dir / "AAPL_default.html").write_text("<html></html>")  # Should be ignored

        # Act
        files = migration_service.scan_exports(asset_classes=["stock"])

        # Assert
        assert len(files) == 2
        assert all(f.suffix == ".json" for f in files)

    def test_should_scan_multiple_asset_classes(self, migration_service, tmp_path):
        """Test scanning multiple asset class directories."""
        # Arrange
        migration_service.output_dir = tmp_path

        # Create directories and files
        for asset_class in ["stock", "etf", "crypto"]:
            asset_dir = tmp_path / asset_class
            asset_dir.mkdir()
            (asset_dir / f"TEST_{asset_class}.json").write_text("{}")

        # Act
        files = migration_service.scan_exports(asset_classes=["stock", "etf", "crypto"])

        # Assert
        assert len(files) == 3

    def test_should_skip_consolidated_files(self, migration_service, tmp_path):
        """Test that consolidated report files are skipped."""
        # Arrange
        migration_service.output_dir = tmp_path
        stock_dir = tmp_path / "stock"
        stock_dir.mkdir()

        # Create files
        (stock_dir / "AAPL_default.json").write_text("{}")
        (stock_dir / "deep_analysis_consolidated_default.json").write_text("{}")

        # Act
        files = migration_service.scan_exports(asset_classes=["stock"])

        # Assert
        assert len(files) == 1
        assert "consolidated" not in files[0].name

    @pytest.mark.asyncio
    async def test_should_detect_already_migrated_file(self, migration_service, tmp_path, mocker):
        """Test idempotency check detects already migrated files."""
        # Arrange
        test_file = tmp_path / "AAPL_default.json"
        test_file.write_text(json.dumps({"ticker": "AAPL"}))

        # Mock Supabase client to return existing migration record
        mock_result = mocker.Mock()
        mock_result.data = [{"id": "existing-migration-id"}]
        migration_service.client.execute_with_timeout = mocker.AsyncMock(return_value=mock_result)

        # Act
        is_migrated = await migration_service._is_already_migrated(test_file)

        # Assert
        assert is_migrated is True
        migration_service.client.execute_with_timeout.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_detect_not_migrated_file(self, migration_service, tmp_path, mocker):
        """Test idempotency check detects files not yet migrated."""
        # Arrange
        test_file = tmp_path / "AAPL_default.json"
        test_file.write_text(json.dumps({"ticker": "AAPL"}))

        # Mock Supabase client to return no migration record
        mock_result = mocker.Mock()
        mock_result.data = []
        migration_service.client.execute_with_timeout = mocker.AsyncMock(return_value=mock_result)

        # Act
        is_migrated = await migration_service._is_already_migrated(test_file)

        # Assert
        assert is_migrated is False

    @pytest.mark.asyncio
    async def test_should_handle_migration_check_failure_gracefully(self, migration_service, tmp_path, mocker):
        """Test that migration check failures don't block migration."""
        # Arrange
        test_file = tmp_path / "AAPL_default.json"
        test_file.write_text(json.dumps({"ticker": "AAPL"}))

        # Mock Supabase client to raise exception
        migration_service.client.execute_with_timeout = mocker.AsyncMock(side_effect=Exception("Database connection failed"))

        # Act
        is_migrated = await migration_service._is_already_migrated(test_file)

        # Assert - Should return False to allow migration attempt
        assert is_migrated is False

    @pytest.mark.asyncio
    async def test_should_migrate_valid_export(self, migration_service, tmp_path, sample_export_data, mocker):
        """Test successful migration of valid export file."""
        # Arrange
        test_file = tmp_path / "stock" / "AAPL_default.json"
        test_file.parent.mkdir(parents=True)
        test_file.write_text(json.dumps(sample_export_data))

        # Mock dependencies
        migration_service._is_already_migrated = mocker.AsyncMock(return_value=False)
        migration_service.repository.store_analysis = mocker.AsyncMock(return_value=True)
        migration_service._record_migration = mocker.AsyncMock()

        # Act
        success = await migration_service.migrate_export(test_file)

        # Assert
        assert success is True
        migration_service.repository.store_analysis.assert_called_once()
        migration_service._record_migration.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_skip_already_migrated_export(self, migration_service, tmp_path, sample_export_data, mocker):
        """Test that already migrated files are skipped."""
        # Arrange
        test_file = tmp_path / "stock" / "AAPL_default.json"
        test_file.parent.mkdir(parents=True)
        test_file.write_text(json.dumps(sample_export_data))

        # Mock as already migrated
        migration_service._is_already_migrated = mocker.AsyncMock(return_value=True)
        migration_service.repository.store_analysis = mocker.AsyncMock()

        # Act
        success = await migration_service.migrate_export(test_file)

        # Assert
        assert success is False
        migration_service.repository.store_analysis.assert_not_called()

    @pytest.mark.asyncio
    async def test_should_force_migrate_already_migrated_export(self, migration_service, tmp_path, sample_export_data, mocker):
        """Test that force flag bypasses idempotency check."""
        # Arrange
        test_file = tmp_path / "stock" / "AAPL_default.json"
        test_file.parent.mkdir(parents=True)
        test_file.write_text(json.dumps(sample_export_data))

        # Mock dependencies
        migration_service._is_already_migrated = mocker.AsyncMock(return_value=True)
        migration_service.repository.store_analysis = mocker.AsyncMock(return_value=True)
        migration_service._record_migration = mocker.AsyncMock()

        # Act
        success = await migration_service.migrate_export(test_file, force=True)

        # Assert
        assert success is True
        migration_service._is_already_migrated.assert_not_called()  # Skipped due to force
        migration_service.repository.store_analysis.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_skip_invalid_json_file(self, migration_service, tmp_path, mocker):
        """Test that files with invalid JSON are skipped."""
        # Arrange
        test_file = tmp_path / "stock" / "AAPL_default.json"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("{ invalid json }")

        # Mock dependencies
        migration_service._is_already_migrated = mocker.AsyncMock(return_value=False)
        migration_service.repository.store_analysis = mocker.AsyncMock()

        # Act
        success = await migration_service.migrate_export(test_file)

        # Assert
        assert success is False
        migration_service.repository.store_analysis.assert_not_called()

    @pytest.mark.asyncio
    async def test_should_skip_export_with_missing_required_fields(self, migration_service, tmp_path, mocker):
        """Test that exports missing required fields are skipped."""
        # Arrange
        test_file = tmp_path / "stock" / "AAPL_default.json"
        test_file.parent.mkdir(parents=True)
        invalid_data = {
            "ticker": "AAPL",
            # Missing: asset_class, composite_score, grade, recommendation
        }
        test_file.write_text(json.dumps(invalid_data))

        # Mock dependencies
        migration_service._is_already_migrated = mocker.AsyncMock(return_value=False)
        migration_service.repository.store_analysis = mocker.AsyncMock()

        # Act
        success = await migration_service.migrate_export(test_file)

        # Assert
        assert success is False
        migration_service.repository.store_analysis.assert_not_called()

    @pytest.mark.asyncio
    async def test_should_add_metadata_from_path_when_missing(self, migration_service, tmp_path, mocker):
        """Test that ticker and asset_class are extracted from path if missing."""
        # Arrange
        test_file = tmp_path / "stock" / "AAPL_default.json"
        test_file.parent.mkdir(parents=True)
        # Data missing ticker and asset_class
        incomplete_data = {
            "composite_score": 0.85,
            "grade": "A+",
            "recommendation": "BUY",
        }
        test_file.write_text(json.dumps(incomplete_data))

        # Mock dependencies
        migration_service._is_already_migrated = mocker.AsyncMock(return_value=False)
        migration_service.repository.store_analysis = mocker.AsyncMock(return_value=True)
        migration_service._record_migration = mocker.AsyncMock()

        # Act
        success = await migration_service.migrate_export(test_file)

        # Assert
        assert success is True
        # Verify store_analysis was called with extracted metadata
        call_args = migration_service.repository.store_analysis.call_args
        assert call_args[1]["ticker"] == "AAPL"
        assert call_args[1]["asset_class"] == "stock"

    @pytest.mark.asyncio
    async def test_should_preserve_file_timestamp(self, migration_service, tmp_path, sample_export_data, mocker):
        """Test that file modification time is preserved as analysis timestamp."""
        # Arrange
        test_file = tmp_path / "stock" / "AAPL_default.json"
        test_file.parent.mkdir(parents=True)
        # Remove timestamp from data to test fallback
        data_without_timestamp = sample_export_data.copy()
        del data_without_timestamp["analysis_timestamp"]
        test_file.write_text(json.dumps(data_without_timestamp))

        # Mock dependencies
        migration_service._is_already_migrated = mocker.AsyncMock(return_value=False)
        migration_service.repository.store_analysis = mocker.AsyncMock(return_value=True)
        migration_service._record_migration = mocker.AsyncMock()

        # Act
        success = await migration_service.migrate_export(test_file)

        # Assert
        assert success is True
        # Verify timestamp was added
        call_args = migration_service.repository.store_analysis.call_args
        export_data = call_args[1]["export_data"]
        assert "analysis_timestamp" in export_data

    @pytest.mark.asyncio
    async def test_should_handle_storage_failure(self, migration_service, tmp_path, sample_export_data, mocker):
        """Test handling of storage failures."""
        # Arrange
        test_file = tmp_path / "stock" / "AAPL_default.json"
        test_file.parent.mkdir(parents=True)
        test_file.write_text(json.dumps(sample_export_data))

        # Mock dependencies
        migration_service._is_already_migrated = mocker.AsyncMock(return_value=False)
        migration_service.repository.store_analysis = mocker.AsyncMock(return_value=False)
        migration_service._record_migration = mocker.AsyncMock()

        # Act
        success = await migration_service.migrate_export(test_file)

        # Assert
        assert success is False
        migration_service._record_migration.assert_not_called()

    @pytest.mark.asyncio
    async def test_should_run_migration_twice_without_duplicates(self, migration_service, tmp_path, sample_export_data, mocker):
        """Test idempotency: running migration twice doesn't create duplicates."""
        # Arrange
        test_file = tmp_path / "stock" / "AAPL_default.json"
        test_file.parent.mkdir(parents=True)
        test_file.write_text(json.dumps(sample_export_data))

        # Mock dependencies for first run
        migration_service.repository.store_analysis = mocker.AsyncMock(return_value=True)
        migration_service._record_migration = mocker.AsyncMock()

        # First migration - not yet migrated
        migration_service._is_already_migrated = mocker.AsyncMock(return_value=False)

        # Act - First migration
        success1 = await migration_service.migrate_export(test_file)

        # Assert first migration succeeded
        assert success1 is True
        assert migration_service.repository.store_analysis.call_count == 1

        # Second migration - now already migrated
        migration_service._is_already_migrated = mocker.AsyncMock(return_value=True)

        # Act - Second migration
        success2 = await migration_service.migrate_export(test_file)

        # Assert second migration was skipped
        assert success2 is False
        assert migration_service.repository.store_analysis.call_count == 1  # Still 1, not 2
