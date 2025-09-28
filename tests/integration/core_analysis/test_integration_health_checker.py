"""
Tests for Integration Health Checker.

Tests the health checking functionality for the crew data integration system.
"""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from finwiz.integration.health_checker import (
    HealthStatus,
    IntegrationHealthChecker,
    SystemHealthReport,
    get_health_checker,
    perform_quick_health_check,
)


class TestIntegrationHealthChecker:
    """Test the IntegrationHealthChecker class."""

    def test_should_initialize_health_checker_with_default_config(self):
        """Test health checker initialization with default configuration."""
        # Act
        health_checker = IntegrationHealthChecker()

        # Assert
        assert health_checker.output_dir == Path("output")
        assert health_checker.integration_dir == Path("output/integration")
        assert len(health_checker.crew_names) == 6
        assert "stock" in health_checker.crew_names
        assert "etf" in health_checker.crew_names

    def test_should_initialize_health_checker_with_custom_output_dir(self):
        """Test health checker initialization with custom output directory."""
        # Arrange
        custom_dir = Path("/tmp/test_output")

        # Act
        health_checker = IntegrationHealthChecker(output_dir=custom_dir)

        # Assert
        assert health_checker.output_dir == custom_dir
        assert health_checker.integration_dir == custom_dir / "integration"

    @patch("finwiz.integration.health_checker.psutil.cpu_percent")
    @patch("finwiz.integration.health_checker.psutil.virtual_memory")
    @patch("finwiz.integration.health_checker.psutil.disk_usage")
    def test_should_check_system_resources_when_healthy(self, mock_disk, mock_memory, mock_cpu):
        """Test system resource checking when resources are healthy."""
        # Arrange
        mock_cpu.return_value = 25.0
        mock_memory.return_value = Mock(percent=30.0, available=8 * 1024**3)
        mock_disk.return_value = Mock(percent=40.0, free=100 * 1024**3)

        health_checker = IntegrationHealthChecker()

        # Act
        result = health_checker._check_system_resources()

        # Assert
        assert isinstance(result, HealthStatus)
        assert result.component == "system_resources"
        assert result.status == "healthy"
        assert "Resources healthy" in result.message
        assert result.details["cpu_percent"] == 25.0
        assert result.details["memory_percent"] == 30.0
        assert result.details["disk_percent"] == 40.0

    @patch("finwiz.integration.health_checker.psutil.cpu_percent")
    @patch("finwiz.integration.health_checker.psutil.virtual_memory")
    @patch("finwiz.integration.health_checker.psutil.disk_usage")
    def test_should_detect_critical_resource_usage(self, mock_disk, mock_memory, mock_cpu):
        """Test system resource checking when resources are critical."""
        # Arrange
        mock_cpu.return_value = 95.0
        mock_memory.return_value = Mock(percent=95.0, available=1 * 1024**3)
        mock_disk.return_value = Mock(percent=95.0, free=5 * 1024**3)

        health_checker = IntegrationHealthChecker()

        # Act
        result = health_checker._check_system_resources()

        # Assert
        assert result.status == "critical"
        assert "Critical resource issues" in result.message
        assert len(result.details["issues"]) == 3  # CPU, memory, and disk

    def test_should_check_directory_structure_when_missing_directories(self):
        """Test directory structure checking when directories are missing."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            health_checker = IntegrationHealthChecker(output_dir=temp_path)

            # Act
            result = health_checker._check_directory_structure()

            # Assert
            assert result.component == "directory_structure"
            assert result.status in ["warning", "critical"]
            assert len(result.details["missing_directories"]) > 0

    def test_should_check_directory_structure_when_directories_exist(self):
        """Test directory structure checking when directories exist."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create required directories
            (temp_path / "integration").mkdir()
            (temp_path / "integration" / "metadata").mkdir()
            (temp_path / "integration" / "contracts").mkdir()
            (temp_path / "integration" / "consolidated").mkdir()

            health_checker = IntegrationHealthChecker(output_dir=temp_path)

            # Act
            result = health_checker._check_directory_structure()

            # Assert
            assert result.component == "directory_structure"
            assert result.status == "healthy"
            assert len(result.details["healthy_directories"]) > 0
            assert len(result.details["missing_directories"]) == 0

    def test_should_check_data_availability_when_no_crew_data(self):
        """Test data availability checking when no crew data exists."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            health_checker = IntegrationHealthChecker(output_dir=temp_path)

            # Act
            result = health_checker._check_data_availability()

            # Assert
            assert result.component == "data_availability"
            assert result.status == "critical"
            assert "No crew data available" in result.message
            assert len(result.details["available_crews"]) == 0
            assert len(result.details["missing_crews"]) == 6  # All crews missing

    def test_should_check_data_availability_when_crew_data_exists(self):
        """Test data availability checking when crew data exists."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create crew directories with JSON files
            for crew_name in ["stock", "etf", "crypto"]:
                crew_dir = temp_path / crew_name
                crew_dir.mkdir()
                (crew_dir / f"{crew_name}_analysis.json").write_text('{"test": "data"}')

            health_checker = IntegrationHealthChecker(output_dir=temp_path)

            # Act
            result = health_checker._check_data_availability()

            # Assert
            assert result.component == "data_availability"
            assert result.status in ["warning", "healthy"]  # Some crews have data
            assert len(result.details["available_crews"]) == 3
            assert len(result.details["missing_crews"]) == 3  # discovery, portfolio, report

    def test_should_check_integration_metadata_when_files_missing(self):
        """Test integration metadata checking when files are missing."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            health_checker = IntegrationHealthChecker(output_dir=temp_path)

            # Act
            result = health_checker._check_integration_metadata()

            # Assert
            assert result.component == "integration_metadata"
            assert result.status == "warning"
            assert len(result.details["missing_files"]) == 3  # All expected files missing

    def test_should_check_integration_metadata_when_files_exist(self):
        """Test integration metadata checking when files exist."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            metadata_dir = temp_path / "integration" / "metadata"
            metadata_dir.mkdir(parents=True)

            # Create valid JSON files
            (metadata_dir / "crew_execution_log.json").write_text('{"executions": []}')
            (metadata_dir / "data_lineage.json").write_text('{"executions": []}')
            (metadata_dir / "validation_status.json").write_text("{}")

            health_checker = IntegrationHealthChecker(output_dir=temp_path)

            # Act
            result = health_checker._check_integration_metadata()

            # Assert
            assert result.component == "integration_metadata"
            assert result.status == "healthy"
            assert len(result.details["existing_files"]) == 3
            assert len(result.details["missing_files"]) == 0
            assert len(result.details["corrupted_files"]) == 0

    def test_should_check_integration_metadata_when_files_corrupted(self):
        """Test integration metadata checking when files are corrupted."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            metadata_dir = temp_path / "integration" / "metadata"
            metadata_dir.mkdir(parents=True)

            # Create corrupted JSON file
            (metadata_dir / "crew_execution_log.json").write_text("invalid json content")

            health_checker = IntegrationHealthChecker(output_dir=temp_path)

            # Act
            result = health_checker._check_integration_metadata()

            # Assert
            assert result.component == "integration_metadata"
            assert result.status == "critical"
            assert "corrupted metadata files" in result.message
            assert len(result.details["corrupted_files"]) == 1

    def test_should_escalate_status_correctly(self):
        """Test status escalation logic."""
        # Arrange
        health_checker = IntegrationHealthChecker()

        # Act & Assert
        assert health_checker._escalate_status("healthy", "warning") == "warning"
        assert health_checker._escalate_status("warning", "healthy") == "warning"
        assert health_checker._escalate_status("warning", "critical") == "critical"
        assert health_checker._escalate_status("critical", "warning") == "critical"
        assert health_checker._escalate_status("healthy", "unknown") == "unknown"

    def test_should_generate_recommendations_for_critical_issues(self):
        """Test recommendation generation for critical issues."""
        # Arrange
        health_checker = IntegrationHealthChecker()

        components = [
            HealthStatus(
                component="data_availability",
                status="critical",
                message="Missing crews",
                details={"missing_crews": ["stock", "etf"]},
                last_check=datetime.now(),
            ),
            HealthStatus(
                component="validation_status",
                status="critical",
                message="Validation errors",
                details={"invalid_crews": ["crypto"]},
                last_check=datetime.now(),
            ),
        ]

        # Act
        recommendations = health_checker._generate_recommendations(components)

        # Assert
        assert len(recommendations) >= 2
        assert any("Execute missing crews" in rec for rec in recommendations)
        assert any("Fix validation errors" in rec for rec in recommendations)

    def test_should_create_health_summary(self):
        """Test health summary creation."""
        # Arrange
        health_checker = IntegrationHealthChecker()

        components = [
            HealthStatus(component="test1", status="healthy", message="OK", last_check=datetime.now()),
            HealthStatus(component="test2", status="warning", message="Warning", last_check=datetime.now()),
            HealthStatus(component="test3", status="critical", message="Error", last_check=datetime.now()),
        ]

        # Act
        summary = health_checker._create_health_summary(components)

        # Assert
        assert summary["total_components"] == 3
        assert summary["status_distribution"]["healthy"] == 1
        assert summary["status_distribution"]["warning"] == 1
        assert summary["status_distribution"]["critical"] == 1
        assert summary["health_percentage"] == pytest.approx(33.33, rel=1e-2)

    def test_should_perform_quick_health_check(self):
        """Test quick health check functionality."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            health_checker = IntegrationHealthChecker(output_dir=temp_path)

            # Act
            result = health_checker.quick_health_check()

            # Assert
            assert "overall_status" in result
            assert "issues" in result
            assert "check_timestamp" in result
            assert result["overall_status"] in ["healthy", "warning", "critical"]

    @patch("finwiz.integration.health_checker.DataFreshnessChecker")
    def test_should_perform_comprehensive_health_check(self, mock_freshness_checker):
        """Test comprehensive health check functionality."""
        # Arrange
        mock_freshness_report = Mock()
        mock_freshness_report.fresh_data = ["stock"]
        mock_freshness_report.stale_data = ["etf"]
        mock_freshness_report.missing_data = ["crypto"]
        mock_freshness_report.overall_status = "warning"

        mock_freshness_checker.return_value.generate_freshness_report.return_value = mock_freshness_report

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            health_checker = IntegrationHealthChecker(output_dir=temp_path)

            # Act
            report = health_checker.perform_comprehensive_health_check()

            # Assert
            assert isinstance(report, SystemHealthReport)
            assert report.overall_status in ["healthy", "warning", "critical"]
            assert len(report.components) > 0
            assert len(report.recommendations) > 0
            assert isinstance(report.summary, dict)


class TestHealthCheckerGlobalFunctions:
    """Test global health checker functions."""

    def test_should_get_global_health_checker_instance(self):
        """Test getting global health checker instance."""
        # Act
        health_checker1 = get_health_checker()
        health_checker2 = get_health_checker()

        # Assert
        assert health_checker1 is health_checker2  # Same instance
        assert isinstance(health_checker1, IntegrationHealthChecker)

    def test_should_perform_quick_health_check_globally(self):
        """Test global quick health check function."""
        # Act
        result = perform_quick_health_check()

        # Assert
        assert isinstance(result, dict)
        assert "overall_status" in result
        assert "issues" in result
        assert "check_timestamp" in result
