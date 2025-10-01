"""
Integration tests for freshness checking workflow.

Tests the integration of freshness checking into data access methods
with mocked crew outputs and file system operations.
"""

import json
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from finwiz.integration import CrewDataAccessor, CrewDataIntegrationManager
from finwiz.schemas.integration import DataAvailabilityStatus


class TestFreshnessIntegration:
    """Test suite for freshness checking integration."""

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

    @pytest.fixture
    def data_accessor(self, integration_manager):
        """Create a data accessor with the integration manager."""
        return CrewDataAccessor(integration_manager)

    @pytest.fixture
    def current_time(self):
        """Return fixed current time for consistent testing."""
        return datetime(2024, 1, 15, 12, 0, 0)

    def test_should_detect_stale_data_in_upstream_collection(self, integration_manager, temp_output_dir, mocker, current_time):
        """Test that upstream data collection properly detects stale data."""
        # Arrange
        # Create mock crew directories with files
        stock_dir = temp_output_dir / "stock"
        stock_dir.mkdir(parents=True)

        etf_dir = temp_output_dir / "etf"
        etf_dir.mkdir(parents=True)

        # Create mock files with different ages
        stock_file = stock_dir / "stock_output.json"
        etf_file = etf_dir / "etf_output.json"

        stock_file.write_text('{"test": "data"}')
        etf_file.write_text('{"test": "data"}')

        # Mock file modification times
        stale_time = (current_time - timedelta(hours=48)).timestamp()  # 48 hours ago (stale)
        fresh_time = (current_time - timedelta(hours=1)).timestamp()  # 1 hour ago (fresh)

        with patch("pathlib.Path.stat") as mock_stat:
            # Configure stat mock to return different times for different files
            def stat_side_effect():
                mock_stat_obj = Mock()
                if str(stock_file) in str(mock_stat.call_args):
                    mock_stat_obj.st_mtime = stale_time
                else:
                    mock_stat_obj.st_mtime = fresh_time
                return mock_stat_obj

            mock_stat.side_effect = stat_side_effect

            # Mock datetime in freshness checker
            with patch("finwiz.integration.freshness_checker.datetime") as datetime_mock:
                datetime_mock.now.return_value = current_time
                datetime_mock.fromtimestamp.side_effect = lambda ts: datetime.fromtimestamp(ts)
                datetime_mock.min = datetime.min

                # Act
                upstream_data = integration_manager.get_upstream_data("discovery", max_age_hours=24)

                # Assert
                assert "stock" in upstream_data.stale_data
                assert "etf" not in upstream_data.stale_data
                assert len(upstream_data.available_data) == 2  # Both should be available despite staleness

    def test_should_warn_on_stale_data_access(self, integration_manager, temp_output_dir, mocker, current_time):
        """Test that data access methods warn about stale data."""
        # Arrange
        stock_dir = temp_output_dir / "stock"
        stock_dir.mkdir(parents=True)

        stock_file = stock_dir / "stock_output.json"
        test_data = {"test": "stale_data", "timestamp": current_time.isoformat()}
        stock_file.write_text(json.dumps(test_data))

        # Mock file as stale (48 hours old)
        stale_time = (current_time - timedelta(hours=48)).timestamp()

        with patch("pathlib.Path.stat") as mock_stat:
            mock_stat_obj = Mock()
            mock_stat_obj.st_mtime = stale_time
            mock_stat.return_value = mock_stat_obj

            with patch("finwiz.integration.freshness_checker.datetime") as datetime_mock:
                datetime_mock.now.return_value = current_time
                datetime_mock.fromtimestamp.return_value = current_time - timedelta(hours=48)
                datetime_mock.min = datetime.min

                # Act
                data = integration_manager.get_crew_data_with_freshness_check("stock", max_age_hours=24)

                # Assert
                assert data is not None
                assert data["test"] == "stale_data"

                # Verify warning was logged
                integration_manager.logger.warning.assert_called()
                warning_call = integration_manager.logger.warning.call_args
                assert "stale data" in warning_call[0][0].lower()

    def test_should_provide_refresh_recommendations(self, integration_manager, temp_output_dir, mocker, current_time):
        """Test that refresh recommendations are provided based on staleness and dependencies."""
        # Arrange
        # Create directories for different crews
        for crew_name in ["stock", "etf", "crypto", "discovery"]:
            crew_dir = temp_output_dir / crew_name
            crew_dir.mkdir(parents=True)

            crew_file = crew_dir / f"{crew_name}_output.json"
            crew_file.write_text('{"test": "data"}')

        # Mock different staleness levels
        crew_staleness = {
            "stock": 48,  # Very stale
            "etf": 1,  # Fresh
            "crypto": 36,  # Stale
            "discovery": 72,  # Very stale (depends on others)
        }

        def stat_side_effect(path_obj):
            mock_stat_obj = Mock()
            for crew_name, hours_ago in crew_staleness.items():
                if crew_name in str(path_obj):
                    mock_stat_obj.st_mtime = (current_time - timedelta(hours=hours_ago)).timestamp()
                    break
            else:
                mock_stat_obj.st_mtime = current_time.timestamp()
            return mock_stat_obj

        with patch("pathlib.Path.stat", side_effect=stat_side_effect):
            with patch("finwiz.integration.freshness_checker.datetime") as datetime_mock:
                datetime_mock.now.return_value = current_time
                datetime_mock.fromtimestamp.side_effect = lambda ts: datetime.fromtimestamp(ts)

                # Act
                recommendations = integration_manager.get_refresh_recommendations(max_age_hours=24)

                # Assert
                # Should recommend refreshing stale crews, with dependencies considered
                assert "stock" in recommendations
                assert "crypto" in recommendations
                assert "discovery" in recommendations
                assert "etf" not in recommendations  # Fresh data

                # Discovery should come after its dependencies
                if "discovery" in recommendations:
                    discovery_index = recommendations.index("discovery")
                    for base_crew in ["stock", "crypto"]:
                        if base_crew in recommendations:
                            assert recommendations.index(base_crew) < discovery_index

    def test_should_generate_comprehensive_availability_report(self, data_accessor, temp_output_dir, mocker, current_time):
        """Test comprehensive data availability reporting."""
        # Arrange
        # Create mixed scenario: some fresh, some stale, some missing
        scenarios = {
            "stock": {"exists": True, "age_hours": 1},  # Fresh
            "etf": {"exists": True, "age_hours": 48},  # Stale
            "crypto": {"exists": False, "age_hours": 0},  # Missing
            "discovery": {"exists": True, "age_hours": 12},  # Fresh
            "portfolio": {"exists": False, "age_hours": 0},  # Missing
        }

        for crew_name, scenario in scenarios.items():
            if scenario["exists"]:
                crew_dir = temp_output_dir / crew_name
                crew_dir.mkdir(parents=True)

                crew_file = crew_dir / f"{crew_name}_output.json"
                crew_file.write_text(json.dumps({"crew": crew_name, "test": "data"}))

        def stat_side_effect(path_obj):
            mock_stat_obj = Mock()
            mock_stat_obj.st_size = 1024
            for crew_name, scenario in scenarios.items():
                if crew_name in str(path_obj) and scenario["exists"]:
                    mock_stat_obj.st_mtime = (current_time - timedelta(hours=scenario["age_hours"])).timestamp()
                    break
            else:
                mock_stat_obj.st_mtime = current_time.timestamp()
            return mock_stat_obj

        with patch("pathlib.Path.stat", side_effect=stat_side_effect):
            with patch("finwiz.integration.freshness_checker.datetime") as datetime_mock:
                datetime_mock.now.return_value = current_time
                datetime_mock.fromtimestamp.side_effect = lambda ts: datetime.fromtimestamp(ts)
                datetime_mock.min = datetime.min

                # Act
                availability_report = data_accessor.check_data_availability(max_age_hours=24)

                # Assert
                assert availability_report.stock_available is True
                assert availability_report.etf_available is True  # Available but stale
                assert availability_report.crypto_available is False
                assert availability_report.discovery_available is True
                assert availability_report.portfolio_available is False

                assert "etf" in availability_report.stale_data
                assert "crypto" in availability_report.missing_data
                assert "portfolio" in availability_report.missing_data

                assert availability_report.overall_status == DataAvailabilityStatus.PARTIAL
                assert len(availability_report.integration_errors) > 0
                assert len(availability_report.recommendations) > 0

    def test_should_consolidate_available_data_with_warnings(self, data_accessor, temp_output_dir, mocker, current_time):
        """Test data consolidation with freshness warnings."""
        # Arrange
        # Create data for multiple crews
        crews_data = {
            "stock": {"analysis": "stock_analysis", "recommendations": ["BUY AAPL"]},
            "etf": {"analysis": "etf_analysis", "recommendations": ["HOLD VTI"]},
            "crypto": {"analysis": "crypto_analysis", "recommendations": ["SELL BTC"]},
        }

        for crew_name, data in crews_data.items():
            crew_dir = temp_output_dir / crew_name
            crew_dir.mkdir(parents=True)

            crew_file = crew_dir / f"{crew_name}_output.json"
            crew_file.write_text(json.dumps(data))

        # Mock ETF data as stale
        def stat_side_effect(path_obj):
            mock_stat_obj = Mock()
            if "etf" in str(path_obj):
                mock_stat_obj.st_mtime = (current_time - timedelta(hours=48)).timestamp()  # Stale
            else:
                mock_stat_obj.st_mtime = (current_time - timedelta(hours=1)).timestamp()  # Fresh
            return mock_stat_obj

        with patch("pathlib.Path.stat", side_effect=stat_side_effect):
            with patch("finwiz.integration.freshness_checker.datetime") as datetime_mock:
                datetime_mock.now.return_value = current_time
                datetime_mock.fromtimestamp.side_effect = lambda ts: datetime.fromtimestamp(ts)
                datetime_mock.min = datetime.min

                # Act
                consolidated_data = data_accessor.get_consolidated_data(max_age_hours=24)

                # Assert
                assert len(consolidated_data) == 3
                assert "stock" in consolidated_data
                assert "etf" in consolidated_data  # Should be included despite being stale
                assert "crypto" in consolidated_data

                assert consolidated_data["stock"]["analysis"] == "stock_analysis"
                assert consolidated_data["etf"]["analysis"] == "etf_analysis"
                assert consolidated_data["crypto"]["analysis"] == "crypto_analysis"

    def test_should_handle_missing_data_gracefully(self, data_accessor, temp_output_dir):
        """Test graceful handling when no data is available."""
        # Arrange - no crew directories created (all missing)

        # Act
        availability_report = data_accessor.check_data_availability(max_age_hours=24)
        consolidated_data = data_accessor.get_consolidated_data(max_age_hours=24)

        # Assert
        assert availability_report.overall_status == DataAvailabilityStatus.UNAVAILABLE
        assert len(availability_report.missing_data) == 5  # All crews missing
        assert len(consolidated_data) == 0

        # All crews should be marked as unavailable
        assert not availability_report.stock_available
        assert not availability_report.etf_available
        assert not availability_report.crypto_available
        assert not availability_report.discovery_available
        assert not availability_report.portfolio_available
