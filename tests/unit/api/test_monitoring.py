"""
Unit tests for API monitoring endpoints.

Tests for the FastAPI monitoring API endpoints including health, metrics,
alerts, and dashboard functionality.
"""

from datetime import datetime

import pytest
from faker import Faker

# Check if FastAPI is available
try:
    import fastapi  # noqa: F401

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

pytestmark = pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")

if FASTAPI_AVAILABLE:
    from finwiz.api.monitoring import (
        AlertResponse,
        AlertSummaryResponse,
        DiscoveryMetricsResponse,
        HealthStatusResponse,
        check_monitoring_enabled,
    )


class TestResponseModels:
    """Test response model validation."""

    def test_health_status_response_should_validate(self):
        """Test HealthStatusResponse validation."""
        response = HealthStatusResponse(
            status="healthy",
            uptime_seconds=3600.5,
            total_operations=100,
            total_errors=2,
            error_rate=0.02,
            timestamp="2024-01-01T12:00:00",
        )

        assert response.status == "healthy"
        assert response.uptime_seconds == 3600.5
        assert response.total_operations == 100
        assert response.error_rate == 0.02

    def test_discovery_metrics_response_should_validate(self):
        """Test DiscoveryMetricsResponse validation."""
        response = DiscoveryMetricsResponse(
            total_discoveries=50,
            a_plus_discoveries=10,
            discovery_success_rate=0.9,
            avg_discovery_time=120.5,
            grade_distribution={"A+": 10, "A": 15, "B+": 25},
            asset_type_distribution={"stock": 30, "etf": 20},
            last_discovery_time="2024-01-01T12:00:00",
            discovery_errors=5,
            validation_pass_rate=0.95,
        )

        assert response.total_discoveries == 50
        assert response.a_plus_discoveries == 10
        assert response.discovery_success_rate == 0.9
        assert response.grade_distribution["A+"] == 10

    def test_alert_response_should_validate(self):
        """Test AlertResponse validation."""
        response = AlertResponse(
            id="alert-001",
            type="discovery_rate",
            severity="warning",
            title="Low Discovery Rate",
            message="No discoveries in the last 24 hours",
            timestamp="2024-01-01T12:00:00",
            metadata={"hours_since_last": 25},
            resolved=False,
            resolved_at=None,
            escalated=False,
            escalated_at=None,
        )

        assert response.id == "alert-001"
        assert response.type == "discovery_rate"
        assert response.severity == "warning"
        assert not response.resolved

    def test_alert_response_should_allow_resolved(self):
        """Test AlertResponse with resolved status."""
        response = AlertResponse(
            id="alert-002",
            type="error_rate",
            severity="critical",
            title="High Error Rate",
            message="Error rate exceeded threshold",
            timestamp="2024-01-01T12:00:00",
            metadata={},
            resolved=True,
            resolved_at="2024-01-01T14:00:00",
            escalated=True,
            escalated_at="2024-01-01T13:00:00",
        )

        assert response.resolved is True
        assert response.resolved_at == "2024-01-01T14:00:00"
        assert response.escalated is True

    def test_alert_summary_response_should_validate(self):
        """Test AlertSummaryResponse validation."""
        response = AlertSummaryResponse(
            total_active=5,
            by_severity={"critical": 1, "warning": 3, "info": 1},
            by_type={"discovery_rate": 2, "error_rate": 1, "performance": 2},
            escalated_count=1,
            oldest_alert="2024-01-01T10:00:00",
            newest_alert="2024-01-01T14:00:00",
        )

        assert response.total_active == 5
        assert response.by_severity["critical"] == 1
        assert response.escalated_count == 1


class TestCheckMonitoringEnabled:
    """Test the check_monitoring_enabled utility function."""

    def test_should_raise_when_monitoring_disabled(self, mocker):
        """Test that HTTPException is raised when monitoring is disabled."""
        mocker.patch(
            "finwiz.api.monitoring.is_feature_enabled",
            return_value=False,
        )

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            check_monitoring_enabled()

        assert exc_info.value.status_code == 503
        assert "disabled" in exc_info.value.detail.lower()

    def test_should_not_raise_when_monitoring_enabled(self, mocker):
        """Test that no exception is raised when monitoring is enabled."""
        mocker.patch(
            "finwiz.api.monitoring.is_feature_enabled",
            return_value=True,
        )

        # Should not raise
        check_monitoring_enabled()


class TestGetHealthStatusEndpoint:
    """Test the /health endpoint."""

    @pytest.mark.asyncio
    async def test_should_return_health_status(self, mocker):
        """Test getting health status."""
        mocker.patch(
            "finwiz.api.monitoring.is_feature_enabled",
            return_value=True,
        )

        mock_monitor = mocker.MagicMock()
        mock_monitor.metrics_collector.get_health_status.return_value = {
            "status": "healthy",
            "uptime_seconds": 7200.0,
            "total_operations": 250,
            "total_errors": 5,
            "error_rate": 0.02,
            "timestamp": "2024-01-01T12:00:00",
        }

        mocker.patch(
            "finwiz.api.monitoring.get_discovery_monitor",
            return_value=mock_monitor,
        )

        from finwiz.api.monitoring import get_health_status

        result = await get_health_status()

        assert result.status == "healthy"
        assert result.uptime_seconds == 7200.0
        assert result.total_operations == 250

    @pytest.mark.asyncio
    async def test_should_raise_500_on_error(self, mocker):
        """Test that 500 error is raised on internal error."""
        mocker.patch(
            "finwiz.api.monitoring.is_feature_enabled",
            return_value=True,
        )

        mocker.patch(
            "finwiz.api.monitoring.get_discovery_monitor",
            side_effect=Exception("Internal error"),
        )

        from fastapi import HTTPException

        from finwiz.api.monitoring import get_health_status

        with pytest.raises(HTTPException) as exc_info:
            await get_health_status()

        assert exc_info.value.status_code == 500


class TestGetDiscoveryMetricsEndpoint:
    """Test the /discovery/metrics endpoint."""

    @pytest.mark.asyncio
    async def test_should_return_discovery_metrics(self, mocker):
        """Test getting discovery metrics."""
        mocker.patch(
            "finwiz.api.monitoring.is_feature_enabled",
            return_value=True,
        )

        mock_metrics = mocker.MagicMock()
        mock_metrics.total_discoveries = 100
        mock_metrics.a_plus_discoveries = 20
        mock_metrics.discovery_success_rate = 0.85
        mock_metrics.avg_discovery_time = 150.0
        mock_metrics.grade_distribution = {"A+": 20, "A": 30, "B+": 50}
        mock_metrics.asset_type_distribution = {"stock": 60, "etf": 40}
        mock_metrics.last_discovery_time = datetime(2024, 1, 1, 12, 0, 0)
        mock_metrics.discovery_errors = 15
        mock_metrics.validation_pass_rate = 0.92

        mock_monitor = mocker.MagicMock()
        mock_monitor.discovery_metrics = mock_metrics

        mocker.patch(
            "finwiz.api.monitoring.get_discovery_monitor",
            return_value=mock_monitor,
        )

        from finwiz.api.monitoring import get_discovery_metrics

        result = await get_discovery_metrics()

        assert result.total_discoveries == 100
        assert result.a_plus_discoveries == 20
        assert result.discovery_success_rate == 0.85


class TestGetAlertsEndpoint:
    """Test the /alerts endpoint."""

    @pytest.mark.asyncio
    async def test_should_return_alerts(self, mocker):
        """Test getting alerts."""
        mocker.patch(
            "finwiz.api.monitoring.is_feature_enabled",
            return_value=True,
        )

        mock_alert = mocker.MagicMock()
        mock_alert.id = "alert-001"
        mock_alert.type.value = "discovery_rate"
        mock_alert.severity.value = "warning"
        mock_alert.title = "Low Discovery Rate"
        mock_alert.message = "No discoveries in 24 hours"
        mock_alert.timestamp = datetime(2024, 1, 1, 12, 0, 0)
        mock_alert.metadata = {}
        mock_alert.resolved = False
        mock_alert.resolved_at = None
        mock_alert.escalated = False
        mock_alert.escalated_at = None

        mock_alert_manager = mocker.MagicMock()
        mock_alert_manager.get_active_alerts.return_value = [mock_alert]

        mocker.patch(
            "finwiz.api.monitoring.get_alert_manager",
            return_value=mock_alert_manager,
        )

        from finwiz.api.monitoring import get_alerts

        result = await get_alerts(severity=None, limit=50)

        assert len(result) == 1
        assert result[0].id == "alert-001"
        assert result[0].type == "discovery_rate"

    @pytest.mark.asyncio
    async def test_should_filter_by_severity(self, mocker):
        """Test filtering alerts by severity."""
        mocker.patch(
            "finwiz.api.monitoring.is_feature_enabled",
            return_value=True,
        )

        mock_alert_manager = mocker.MagicMock()
        mock_alert_manager.get_active_alerts.return_value = []

        mocker.patch(
            "finwiz.api.monitoring.get_alert_manager",
            return_value=mock_alert_manager,
        )

        from finwiz.api.monitoring import get_alerts

        await get_alerts(severity="warning", limit=50)

        mock_alert_manager.get_active_alerts.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_raise_400_for_invalid_severity(self, mocker):
        """Test that 400 error is raised for invalid severity."""
        mocker.patch(
            "finwiz.api.monitoring.is_feature_enabled",
            return_value=True,
        )

        mock_alert_manager = mocker.MagicMock()
        mocker.patch(
            "finwiz.api.monitoring.get_alert_manager",
            return_value=mock_alert_manager,
        )

        from fastapi import HTTPException

        from finwiz.api.monitoring import get_alerts

        with pytest.raises(HTTPException) as exc_info:
            await get_alerts(severity="invalid_severity")

        assert exc_info.value.status_code == 400


class TestGetAlertSummaryEndpoint:
    """Test the /alerts/summary endpoint."""

    @pytest.mark.asyncio
    async def test_should_return_alert_summary(self, mocker):
        """Test getting alert summary."""
        mocker.patch(
            "finwiz.api.monitoring.is_feature_enabled",
            return_value=True,
        )

        mock_alert_manager = mocker.MagicMock()
        mock_alert_manager.get_alert_summary.return_value = {
            "total_active": 10,
            "by_severity": {"critical": 2, "warning": 5, "info": 3},
            "by_type": {"discovery_rate": 4, "error_rate": 3, "performance": 3},
            "escalated_count": 2,
            "oldest_alert": datetime(2024, 1, 1, 10, 0, 0),
            "newest_alert": datetime(2024, 1, 1, 14, 0, 0),
        }

        mocker.patch(
            "finwiz.api.monitoring.get_alert_manager",
            return_value=mock_alert_manager,
        )

        from finwiz.api.monitoring import get_alert_summary

        result = await get_alert_summary()

        assert result.total_active == 10
        assert result.by_severity["critical"] == 2
        assert result.escalated_count == 2


class TestResolveAlertEndpoint:
    """Test the /alerts/{alert_id}/resolve endpoint."""

    @pytest.mark.asyncio
    async def test_should_resolve_alert(self, mocker):
        """Test resolving an alert."""
        mocker.patch(
            "finwiz.api.monitoring.is_feature_enabled",
            return_value=True,
        )

        mock_alert_manager = mocker.MagicMock()
        # Create async mock for resolve_alert
        async def mock_resolve(*args, **kwargs):
            return True
        mock_alert_manager.resolve_alert = mock_resolve

        mocker.patch(
            "finwiz.api.monitoring.get_alert_manager",
            return_value=mock_alert_manager,
        )

        from finwiz.api.monitoring import resolve_alert

        result = await resolve_alert("alert-001", "Resolved by admin")

        assert "resolved successfully" in result["message"]

    @pytest.mark.asyncio
    async def test_should_raise_404_for_unknown_alert(self, mocker):
        """Test that 404 is raised for unknown alert ID."""
        mocker.patch(
            "finwiz.api.monitoring.is_feature_enabled",
            return_value=True,
        )

        mock_alert_manager = mocker.MagicMock()
        # Create async mock for resolve_alert that returns False
        async def mock_resolve(*args, **kwargs):
            return False
        mock_alert_manager.resolve_alert = mock_resolve

        mocker.patch(
            "finwiz.api.monitoring.get_alert_manager",
            return_value=mock_alert_manager,
        )

        from fastapi import HTTPException

        from finwiz.api.monitoring import resolve_alert

        with pytest.raises(HTTPException) as exc_info:
            await resolve_alert("unknown-alert")

        assert exc_info.value.status_code == 404


class TestExportMetricsEndpoint:
    """Test the /metrics/export endpoint."""

    @pytest.mark.asyncio
    async def test_should_export_metrics_as_json(self, mocker):
        """Test exporting metrics as JSON."""
        mocker.patch(
            "finwiz.api.monitoring.is_feature_enabled",
            return_value=True,
        )

        mock_monitor = mocker.MagicMock()
        mock_monitor.export_metrics.return_value = "/tmp/metrics_export.json"

        mocker.patch(
            "finwiz.api.monitoring.get_discovery_monitor",
            return_value=mock_monitor,
        )

        from finwiz.api.monitoring import export_metrics

        result = await export_metrics(format="json")

        assert result["format"] == "json"
        assert result["file_path"] == "/tmp/metrics_export.json"
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_should_raise_400_for_unsupported_format(self, mocker):
        """Test that 400 is raised for unsupported format."""
        mocker.patch(
            "finwiz.api.monitoring.is_feature_enabled",
            return_value=True,
        )

        mock_monitor = mocker.MagicMock()
        mocker.patch(
            "finwiz.api.monitoring.get_discovery_monitor",
            return_value=mock_monitor,
        )

        from fastapi import HTTPException

        from finwiz.api.monitoring import export_metrics

        with pytest.raises(HTTPException) as exc_info:
            await export_metrics(format="xml")

        assert exc_info.value.status_code == 400


class TestPingEndpoint:
    """Test the /ping endpoint."""

    @pytest.mark.asyncio
    async def test_should_return_ok_status(self):
        """Test that ping returns ok status."""
        from finwiz.api.monitoring import ping

        result = await ping()

        assert result["status"] == "ok"
        assert "timestamp" in result
