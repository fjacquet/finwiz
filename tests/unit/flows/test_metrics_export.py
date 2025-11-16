"""
Unit tests for metrics export functionality in FinwizFlow.

Tests the _export_metrics() method that exports flow execution metrics to JSON.
"""

import json
import os
from datetime import datetime, timedelta

import pytest

from finwiz.config.resilience_config import ResilienceConfig
from finwiz.flow_state import FinwizState
from finwiz.flows.flow_orchestrator import FinwizFlow


class TestMetricsExport:
    """Test suite for metrics export functionality."""

    @pytest.fixture
    def flow_with_state(self, tmp_path, mocker):
        """Create a FinwizFlow instance with test state."""
        # Change to tmp directory for test isolation
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        # Create flow instance
        flow = FinwizFlow()

        # Mock the state property to return our test state
        test_state = FinwizState(
            flow_start_time=(datetime.now() - timedelta(minutes=10)).isoformat(),
            total_holdings=10,
            holdings_processed=8,
            holdings_remaining=2,
            progress_percentage=80.0,
            failed_holdings=["FAIL1", "FAIL2"],
            retry_counts={"AAPL": 1, "TSLA": 2, "FAIL1": 3},
            timeout_holdings=["TIMEOUT1"],
            retryable_errors=[],
            non_retryable_errors=[],
            checkpoint_uuid="test-uuid-123",
            resume_from_checkpoint=False,
        )

        # Mock the state property
        mocker.patch.object(type(flow), "state", new_callable=mocker.PropertyMock, return_value=test_state)

        # Set up resilience config with ALL required fields
        flow.resilience_config = ResilienceConfig(
            max_retries=3,
            retry_base_delay=2.0,
            retry_max_delay=60.0,
            holding_timeout=300,
            flow_timeout=7200,
            parallel_limit=10,
            auto_resume=False,
            state_max_age_hours=24,
            deep_analysis_parallel_limit=3,
            cleanup_state_on_success=False,
            state_cleanup_max_age_days=7,
        )

        yield flow, tmp_path

        # Restore original directory
        os.chdir(original_cwd)

    def test_should_export_metrics_to_json_file(self, flow_with_state):
        """Test that metrics are exported to JSON file with correct structure."""
        flow, tmp_path = flow_with_state

        # Execute metrics export (will create .finwiz/metrics in tmp_path)
        flow._export_metrics()

        # Verify file was created
        metrics_file = tmp_path / ".finwiz" / "metrics" / "test-uuid-123.json"
        assert metrics_file.exists(), "Metrics file should be created"

        # Load and verify metrics content
        with open(metrics_file) as f:
            metrics = json.load(f)

        # Verify required fields
        assert metrics["flow_uuid"] == "test-uuid-123"
        assert "timestamp" in metrics
        assert "execution_time_seconds" in metrics
        assert "execution_time_formatted" in metrics

    def test_should_include_progress_metrics(self, flow_with_state):
        """Test that progress metrics are included in export."""
        flow, tmp_path = flow_with_state

        # Execute
        flow._export_metrics()

        # Load metrics
        metrics_file = tmp_path / ".finwiz" / "metrics" / "test-uuid-123.json"
        with open(metrics_file) as f:
            metrics = json.load(f)

        # Verify progress metrics
        assert metrics["total_holdings"] == 10
        assert metrics["holdings_processed"] == 8
        assert metrics["holdings_remaining"] == 2
        assert metrics["progress_percentage"] == 80.0

    def test_should_calculate_success_rate(self, flow_with_state):
        """Test that success rate is calculated correctly."""
        flow, tmp_path = flow_with_state

        # Execute
        flow._export_metrics()

        # Load metrics
        metrics_file = tmp_path / ".finwiz" / "metrics" / "test-uuid-123.json"
        with open(metrics_file) as f:
            metrics = json.load(f)

        # Verify success metrics
        # 8 processed - 2 failed = 6 successful
        # 6/10 = 60% success rate
        assert metrics["success_count"] == 6
        assert metrics["failed_count"] == 2
        assert metrics["success_rate"] == 60.0

    def test_should_include_retry_metrics(self, flow_with_state):
        """Test that retry metrics are included."""
        flow, tmp_path = flow_with_state

        # Execute
        flow._export_metrics()

        # Load metrics
        metrics_file = tmp_path / ".finwiz" / "metrics" / "test-uuid-123.json"
        with open(metrics_file) as f:
            metrics = json.load(f)

        # Verify retry metrics
        # Total retries: 1 + 2 + 3 = 6
        assert metrics["retry_count"] == 6
        assert metrics["retry_counts_by_ticker"] == {"AAPL": 1, "TSLA": 2, "FAIL1": 3}
        assert metrics["max_retries_configured"] == 3

    def test_should_include_timeout_metrics(self, flow_with_state):
        """Test that timeout metrics are included."""
        flow, tmp_path = flow_with_state

        # Execute
        flow._export_metrics()

        # Load metrics
        metrics_file = tmp_path / ".finwiz" / "metrics" / "test-uuid-123.json"
        with open(metrics_file) as f:
            metrics = json.load(f)

        # Verify timeout metrics
        assert metrics["timeout_count"] == 1
        assert metrics["timeout_holdings"] == ["TIMEOUT1"]
        assert metrics["holding_timeout_configured"] == 300

    def test_should_include_resilience_config(self, flow_with_state):
        """Test that resilience configuration is included."""
        flow, tmp_path = flow_with_state

        # Execute
        flow._export_metrics()

        # Load metrics
        metrics_file = tmp_path / ".finwiz" / "metrics" / "test-uuid-123.json"
        with open(metrics_file) as f:
            metrics = json.load(f)

        # Verify resilience config
        config = metrics["resilience_config"]
        assert config["max_retries"] == 3
        assert config["retry_base_delay"] == 2.0
        assert config["retry_max_delay"] == 60.0
        assert config["holding_timeout"] == 300
        assert config["flow_timeout"] == 7200
        assert config["parallel_limit"] == 10
        assert config["deep_analysis_parallel_limit"] == 3

    def test_should_calculate_average_time_per_holding(self, flow_with_state):
        """Test that average time per holding is calculated."""
        flow, tmp_path = flow_with_state

        # Execute
        flow._export_metrics()

        # Load metrics
        metrics_file = tmp_path / ".finwiz" / "metrics" / "test-uuid-123.json"
        with open(metrics_file) as f:
            metrics = json.load(f)

        # Verify average time calculation
        # 10 minutes = 600 seconds / 8 holdings = 75 seconds per holding
        assert "average_time_per_holding" in metrics
        assert metrics["average_time_per_holding"] > 0

    def test_should_create_metrics_directory_if_not_exists(self, flow_with_state):
        """Test that metrics directory is created if it doesn't exist."""
        flow, tmp_path = flow_with_state

        # Verify directory doesn't exist yet
        metrics_dir = tmp_path / ".finwiz" / "metrics"
        assert not metrics_dir.exists()

        # Execute
        flow._export_metrics()

        # Verify directory was created
        assert metrics_dir.exists()

        # Verify file was created
        metrics_file = metrics_dir / "test-uuid-123.json"
        assert metrics_file.exists()
