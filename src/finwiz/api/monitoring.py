"""
Monitoring API endpoints for Investment Discovery system.

This module provides REST API endpoints for accessing monitoring data,
health status, and alert information for the Investment Discovery system.
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query  # fastapi may not be installed
from pydantic import BaseModel, Field

from finwiz.monitoring.alerting import AlertSeverity, get_alert_manager
from finwiz.monitoring.investment_discovery import get_discovery_monitor
from finwiz.tools.logger import get_logger
from finwiz.config.features.flags import is_feature_enabled

logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])


# Response models
class HealthStatusResponse(BaseModel):
    """Health status response model."""

    status: str = Field(..., description="Overall health status")
    uptime_seconds: float = Field(..., description="System uptime in seconds")
    total_operations: int = Field(..., description="Total operations performed")
    total_errors: int = Field(..., description="Total errors encountered")
    error_rate: float = Field(..., description="Overall error rate")
    timestamp: str = Field(..., description="Status timestamp")


class DiscoveryMetricsResponse(BaseModel):
    """Discovery metrics response model."""

    total_discoveries: int = Field(..., description="Total discoveries performed")
    a_plus_discoveries: int = Field(..., description="A+ grade discoveries")
    discovery_success_rate: float = Field(..., description="Discovery success rate")
    avg_discovery_time: float = Field(..., description="Average discovery time in seconds")
    grade_distribution: dict[str, int] = Field(..., description="Distribution of grades")
    asset_type_distribution: dict[str, int] = Field(..., description="Distribution by asset type")
    last_discovery_time: str | None = Field(None, description="Last discovery timestamp")
    discovery_errors: int = Field(..., description="Number of discovery errors")
    validation_pass_rate: float = Field(..., description="Validation pass rate")


class AlertResponse(BaseModel):
    """Alert response model."""

    id: str = Field(..., description="Alert ID")
    type: str = Field(..., description="Alert type")
    severity: str = Field(..., description="Alert severity")
    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Alert message")
    timestamp: str = Field(..., description="Alert timestamp")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Alert metadata")
    resolved: bool = Field(..., description="Whether alert is resolved")
    resolved_at: str | None = Field(None, description="Resolution timestamp")
    escalated: bool = Field(..., description="Whether alert is escalated")
    escalated_at: str | None = Field(None, description="Escalation timestamp")


class AlertSummaryResponse(BaseModel):
    """Alert summary response model."""

    total_active: int = Field(..., description="Total active alerts")
    by_severity: dict[str, int] = Field(..., description="Alerts by severity")
    by_type: dict[str, int] = Field(..., description="Alerts by type")
    escalated_count: int = Field(..., description="Number of escalated alerts")
    oldest_alert: str | None = Field(None, description="Oldest alert timestamp")
    newest_alert: str | None = Field(None, description="Newest alert timestamp")


class DashboardResponse(BaseModel):
    """Complete dashboard response model."""

    health_status: HealthStatusResponse
    discovery_metrics: DiscoveryMetricsResponse
    alert_summary: AlertSummaryResponse
    recent_alerts: list[AlertResponse]
    performance_summary: dict[str, Any]
    timestamp: str = Field(..., description="Dashboard timestamp")


# Utility functions
def check_monitoring_enabled() -> None:
    """Check if monitoring is enabled."""
    if not is_feature_enabled("investment_discovery_monitoring"):
        raise HTTPException(status_code=503, detail="Investment Discovery monitoring is disabled")


# API endpoints
@router.get("/health", response_model=HealthStatusResponse)
async def get_health_status() -> HealthStatusResponse:
    """Get system health status."""
    check_monitoring_enabled()

    try:
        monitor = get_discovery_monitor()
        health_data = monitor.metrics_collector.get_health_status()

        return HealthStatusResponse(
            status=health_data["status"],
            uptime_seconds=health_data["uptime_seconds"],
            total_operations=health_data["total_operations"],
            total_errors=health_data["total_errors"],
            error_rate=health_data["error_rate"],
            timestamp=health_data["timestamp"],
        )

    except Exception as e:
        logger.error(f"Failed to get health status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve health status")


@router.get("/discovery/metrics", response_model=DiscoveryMetricsResponse)
async def get_discovery_metrics() -> DiscoveryMetricsResponse:
    """Get investment discovery metrics."""
    check_monitoring_enabled()

    try:
        monitor = get_discovery_monitor()
        metrics = monitor.discovery_metrics

        return DiscoveryMetricsResponse(
            total_discoveries=metrics.total_discoveries,
            a_plus_discoveries=metrics.a_plus_discoveries,
            discovery_success_rate=metrics.discovery_success_rate,
            avg_discovery_time=metrics.avg_discovery_time,
            grade_distribution=dict(metrics.grade_distribution),
            asset_type_distribution=dict(metrics.asset_type_distribution),
            last_discovery_time=metrics.last_discovery_time.isoformat() if metrics.last_discovery_time else None,
            discovery_errors=metrics.discovery_errors,
            validation_pass_rate=metrics.validation_pass_rate,
        )

    except Exception as e:
        logger.error(f"Failed to get discovery metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve discovery metrics")


@router.get("/alerts", response_model=list[AlertResponse])
async def get_alerts(
    severity: str | None = Query(None, description="Filter by severity"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of alerts to return"),
) -> list[AlertResponse]:
    """Get active alerts."""
    check_monitoring_enabled()

    try:
        alert_manager = get_alert_manager()

        # Parse severity filter
        severity_filter = None
        if severity:
            try:
                severity_filter = AlertSeverity(severity.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")

        # Get alerts
        alerts = alert_manager.get_active_alerts(severity=severity_filter)

        # Limit results
        alerts = alerts[:limit]

        # Convert to response format
        alert_responses = []
        for alert in alerts:
            alert_responses.append(
                AlertResponse(
                    id=alert.id,
                    type=alert.type.value,
                    severity=alert.severity.value,
                    title=alert.title,
                    message=alert.message,
                    timestamp=alert.timestamp.isoformat(),
                    metadata=alert.metadata,
                    resolved=alert.resolved,
                    resolved_at=alert.resolved_at.isoformat() if alert.resolved_at else None,
                    escalated=alert.escalated,
                    escalated_at=alert.escalated_at.isoformat() if alert.escalated_at else None,
                )
            )

        return alert_responses

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alerts")


@router.get("/alerts/summary", response_model=AlertSummaryResponse)
async def get_alert_summary() -> AlertSummaryResponse:
    """Get alert summary."""
    check_monitoring_enabled()

    try:
        alert_manager = get_alert_manager()
        summary = alert_manager.get_alert_summary()

        return AlertSummaryResponse(
            total_active=summary["total_active"],
            by_severity=summary["by_severity"],
            by_type=summary["by_type"],
            escalated_count=summary["escalated_count"],
            oldest_alert=summary["oldest_alert"].isoformat() if summary["oldest_alert"] else None,
            newest_alert=summary["newest_alert"].isoformat() if summary["newest_alert"] else None,
        )

    except Exception as e:
        logger.error(f"Failed to get alert summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alert summary")


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str, resolution_message: str = "") -> dict[str, str]:
    """Resolve an alert."""
    check_monitoring_enabled()

    try:
        alert_manager = get_alert_manager()
        success = await alert_manager.resolve_alert(alert_id, resolution_message)

        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")

        return {"message": f"Alert {alert_id} resolved successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resolve alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to resolve alert")


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard() -> DashboardResponse:
    """Get complete monitoring dashboard data."""
    check_monitoring_enabled()

    try:
        monitor = get_discovery_monitor()
        alert_manager = get_alert_manager()

        # Get all data
        dashboard_data = monitor.get_dashboard_data()
        health_data = dashboard_data["health_status"]
        discovery_metrics = dashboard_data["discovery_metrics"]
        alert_summary = alert_manager.get_alert_summary()
        recent_alerts = alert_manager.get_active_alerts()[:10]  # Last 10 alerts

        # Convert alerts to response format
        alert_responses = []
        for alert in recent_alerts:
            alert_responses.append(
                AlertResponse(
                    id=alert.id,
                    type=alert.type.value,
                    severity=alert.severity.value,
                    title=alert.title,
                    message=alert.message,
                    timestamp=alert.timestamp.isoformat(),
                    metadata=alert.metadata,
                    resolved=alert.resolved,
                    resolved_at=alert.resolved_at.isoformat() if alert.resolved_at else None,
                    escalated=alert.escalated,
                    escalated_at=alert.escalated_at.isoformat() if alert.escalated_at else None,
                )
            )

        return DashboardResponse(
            health_status=HealthStatusResponse(
                status=health_data["status"],
                uptime_seconds=health_data["uptime_seconds"],
                total_operations=health_data["total_operations"],
                total_errors=health_data["total_errors"],
                error_rate=health_data["error_rate"],
                timestamp=health_data["timestamp"],
            ),
            discovery_metrics=DiscoveryMetricsResponse(
                total_discoveries=discovery_metrics["total_discoveries"],
                a_plus_discoveries=discovery_metrics["a_plus_discoveries"],
                discovery_success_rate=discovery_metrics["discovery_success_rate"],
                avg_discovery_time=discovery_metrics["avg_discovery_time"],
                grade_distribution=discovery_metrics["grade_distribution"],
                asset_type_distribution=discovery_metrics["asset_type_distribution"],
                last_discovery_time=discovery_metrics["last_discovery_time"],
                discovery_errors=discovery_metrics["discovery_errors"],
                validation_pass_rate=discovery_metrics["validation_pass_rate"],
            ),
            alert_summary=AlertSummaryResponse(
                total_active=alert_summary["total_active"],
                by_severity=alert_summary["by_severity"],
                by_type=alert_summary["by_type"],
                escalated_count=alert_summary["escalated_count"],
                oldest_alert=alert_summary["oldest_alert"].isoformat() if alert_summary["oldest_alert"] else None,
                newest_alert=alert_summary["newest_alert"].isoformat() if alert_summary["newest_alert"] else None,
            ),
            recent_alerts=alert_responses,
            performance_summary=dashboard_data["performance_summary"],
            timestamp=datetime.now().isoformat(),
        )

    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard data")


@router.get("/metrics/export")
async def export_metrics(format: str = Query("json", description="Export format")) -> dict[str, Any]:
    """Export metrics data."""
    check_monitoring_enabled()

    try:
        monitor = get_discovery_monitor()

        if format.lower() not in ["json"]:
            raise HTTPException(status_code=400, detail="Unsupported export format")

        export_file = monitor.export_metrics(format)

        return {
            "message": "Metrics exported successfully",
            "file_path": export_file,
            "format": format,
            "timestamp": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to export metrics")


@router.post("/discovery/test")
async def test_discovery_monitoring() -> dict[str, Any]:
    """Test discovery monitoring system."""
    check_monitoring_enabled()

    try:
        monitor = get_discovery_monitor()

        # Record a test discovery
        test_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        monitor.record_discovery_start(test_id, "test")

        # Simulate completion
        from finwiz.schemas.investment_discovery import (
            APlusAnalysis,
            APlusCriteria,
            APlusDiscoveryResult,
            InvestmentCandidate,
            MarketRegime,
        )

        # Create a valid InvestmentCandidate with all required fields
        test_candidate = InvestmentCandidate(
            symbol="TEST",
            name="Test Investment",
            asset_type="stock",
            current_price=100.0,
            market_cap=1000000000.0,
            preliminary_score=0.95,
            final_score=0.95,
            grade="A+",
            grade_description="Test investment for monitoring",
            recommended_action="BUY",
            data_source="test",
            risk_assessment=None,  # Optional field
        )

        # Wrap in APlusAnalysis as required by a_plus_candidates
        test_analysis = APlusAnalysis(
            candidate=test_candidate,
            fundamental_score=0.95,
            technical_score=0.90,
            quality_score=0.92,
            risk_score=0.88,
            composite_score=0.95,
            confidence_level=0.90,
            is_a_plus_candidate=True,
            rationale=["Test investment for monitoring"],
            market_context=None,  # Optional field
            criteria_used=None,  # Optional field
        )

        test_result = APlusDiscoveryResult(
            asset_type="stock",
            a_plus_candidates=[test_analysis],
            discovery_timestamp=datetime.now(),
            total_screened=1,
            candidates_found=1,
            discovery_criteria=APlusCriteria(),
            market_context=MarketRegime(
                regime_type="sideways",
                vix_level=20.0,
                inflation_rate=3.0,
                interest_rate_trend="stable",
                market_stress_level="low",
            ),
            ucits_compliant_count=None,  # Optional field
        )

        monitor.record_discovery_completion(test_id, test_result, 5.0, True)

        return {
            "message": "Discovery monitoring test completed successfully",
            "test_id": test_id,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Discovery monitoring test failed: {e}")
        raise HTTPException(status_code=500, detail="Discovery monitoring test failed")


# Health check endpoint for load balancers
@router.get("/ping")
async def ping() -> dict[str, str]:
    """Return simple health check status."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}
