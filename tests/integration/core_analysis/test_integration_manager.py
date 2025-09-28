"""
Tests for CrewDataIntegrationManager.

Unit tests for the core data integration infrastructure.
"""

import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from finwiz.integration import CrewDataIntegrationManager
from finwiz.integration.manager import CrewConfig


class TestCrewDataIntegrationManager:
    """Test suite for CrewDataIntegrationManager."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary output directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def integration_manager(self, temp_output_dir):
        """Create an integration manager with temporary directory."""
        return CrewDataIntegrationManager(output_dir=temp_output_dir)

    def test_should_initialize_with_correct_directory_structure(self, integration_manager, temp_output_dir):
        """Test that manager initializes with correct directory structure."""
        # Assert
        assert integration_manager.output_dir == temp_output_dir
        assert integration_manager.integration_dir == temp_output_dir / "integration"
        assert integration_manager.metadata_dir == temp_output_dir / "integration" / "metadata"
        assert integration_manager.contracts_dir == temp_output_dir / "integration" / "contracts"
        assert integration_manager.consolidated_dir == temp_output_dir / "integration" / "consolidated"

        # Check directories were created
        assert integration_manager.integration_dir.exists()
        assert integration_manager.metadata_dir.exists()
        assert integration_manager.contracts_dir.exists()
        assert integration_manager.consolidated_dir.exists()

    def test_should_setup_logging_correctly(self, integration_manager):
        """Test that logging is set up correctly."""
        # Assert
        assert integration_manager.logger is not None
        assert integration_manager.logger.name == "finwiz.integration"

    def test_should_validate_empty_output_data_as_invalid(self, integration_manager):
        """Test validation of empty output data."""
        # Act
        result = integration_manager.validate_crew_output("test_crew", {})

        # Assert
        assert not result.is_valid
        assert "Output data is empty" in result.errors
        assert isinstance(result.validation_timestamp, datetime)

    def test_should_validate_non_dict_output_as_invalid(self, integration_manager):
        """Test validation of non-dictionary output data."""
        # Act
        result = integration_manager.validate_crew_output("test_crew", "invalid_data")

        # Assert
        assert not result.is_valid
        assert "Output data must be a dictionary" in result.errors

    def test_should_validate_valid_output_data(self, integration_manager):
        """Test validation of valid output data."""
        # Arrange
        valid_data = {
            "metadata": {"crew_name": "test_crew", "execution_timestamp": datetime.now().isoformat()},
            "results": ["some", "data"],
        }

        # Act
        result = integration_manager.validate_crew_output("test_crew", valid_data)

        # Assert
        assert result.is_valid
        assert len(result.errors) == 0

    def test_should_detect_missing_upstream_data(self, integration_manager):
        """Test detection of missing upstream data."""
        # Act
        result = integration_manager.get_upstream_data("report")

        # Assert
        assert len(result.available_data) == 0
        assert "stock" in result.missing_data
        assert "etf" in result.missing_data
        assert "crypto" in result.missing_data
        assert "discovery" in result.missing_data
        assert "portfolio" in result.missing_data

    def test_should_check_data_freshness_with_missing_data(self, integration_manager):
        """Test data freshness check when data is missing."""
        # Act
        result = integration_manager.check_data_freshness(max_age_hours=24)

        # Assert
        assert len(result.fresh_data) == 0
        assert len(result.stale_data) == 0
        assert len(result.missing_data) > 0
        assert result.overall_status == "INSUFFICIENT"
        assert isinstance(result.check_timestamp, datetime)

    def test_should_coordinate_crew_execution_with_no_dependencies(self, integration_manager, mocker):
        """Test crew execution coordination with no dependencies."""
        # Arrange
        crews = [CrewConfig(name="stock", dependencies=[]), CrewConfig(name="etf", dependencies=[])]

        # Mock the async method to be synchronous for testing
        async def mock_coordinate():
            return await integration_manager.coordinate_crew_execution(crews)

        # Act
        import asyncio

        result = asyncio.run(mock_coordinate())

        # Assert
        assert result.success
        assert "stock" in result.executed_crews
        assert "etf" in result.executed_crews
        assert len(result.failed_crews) == 0
        assert result.execution_time > 0

    def test_should_handle_crew_execution_with_missing_dependencies(self, integration_manager):
        """Test crew execution coordination when dependencies are missing."""
        # Arrange
        crews = [CrewConfig(name="report", dependencies=["stock", "etf"])]

        # Mock the async method to be synchronous for testing
        async def mock_coordinate():
            return await integration_manager.coordinate_crew_execution(crews)

        # Act
        import asyncio

        result = asyncio.run(mock_coordinate())

        # Assert
        assert not result.success
        assert "report" in result.failed_crews
        assert len(result.errors) > 0
        assert "Dependencies not met" in result.errors[0]

    def test_should_create_execution_log_files(self, integration_manager):
        """Test that execution log files are created correctly."""
        # Assert
        assert integration_manager.execution_log_path.parent.exists()
        assert integration_manager.data_lineage_path.parent.exists()
        assert integration_manager.validation_status_path.parent.exists()

    def test_should_handle_json_file_operations_gracefully(self, integration_manager):
        """Test that JSON file operations handle errors gracefully."""
        # Arrange
        non_existent_path = integration_manager.metadata_dir / "non_existent.json"

        # Act
        result = integration_manager._load_json_file(non_existent_path, {"default": "value"})

        # Assert
        assert result == {"default": "value"}

    def test_should_sort_crews_by_dependencies_correctly(self, integration_manager):
        """Test that crews are sorted correctly by dependencies."""
        # Arrange
        crews = [
            CrewConfig(name="report", dependencies=["stock", "etf"]),
            CrewConfig(name="stock", dependencies=[]),
            CrewConfig(name="etf", dependencies=[]),
        ]

        # Act
        sorted_crews = integration_manager._sort_crews_by_dependencies(crews)

        # Assert
        # Crews with no dependencies should come first
        no_dep_crews = [crew.name for crew in sorted_crews if not crew.dependencies]
        with_dep_crews = [crew.name for crew in sorted_crews if crew.dependencies]

        assert "stock" in no_dep_crews
        assert "etf" in no_dep_crews
        assert "report" in with_dep_crews
