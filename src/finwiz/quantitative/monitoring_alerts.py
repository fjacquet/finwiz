"""
Alert generation and management for portfolio monitoring.

This module provides alert generation, storage, and management functionality
for portfolio monitoring systems.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from finwiz.schemas.portfolio_rebalancing import RebalancingNeed

logger = logging.getLogger(__name__)


class AlertType(str, Enum):
    """Alert type enumeration."""

    DEVIATION_ALERT = "DEVIATION_ALERT"
    MULTIPLE_POSITIONS_ALERT = "MULTIPLE_POSITIONS_ALERT"
    AUTO_REBALANCE_TRIGGERED = "AUTO_REBALANCE_TRIGGERED"
    MONITORING_ERROR = "MONITORING_ERROR"
    PRICE_DATA_STALE = "PRICE_DATA_STALE"


class AlertSeverity(str, Enum):
    """Alert severity enumeration."""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class PortfolioAlert(BaseModel):
    """Portfolio monitoring alert."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    # Alert identification
    alert_id: str = Field(..., description="Unique alert identifier")
    portfolio_id: str = Field(..., description="Portfolio identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Alert timestamp")

    # Alert details
    alert_type: AlertType = Field(..., description="Type of alert")
    severity: AlertSeverity = Field(..., description="Alert severity")
    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Detailed alert message")

    # Context data
    affected_positions: list[str] = Field(default_factory=list, description="Positions affected by alert")
    current_deviations: dict[str, float] = Field(default_factory=dict, description="Current deviations by position")
    recommended_actions: list[str] = Field(default_factory=list, description="Recommended actions")

    # Status
    acknowledged: bool = Field(default=False, description="Whether alert has been acknowledged")
    resolved: bool = Field(default=False, description="Whether alert has been resolved")
    resolution_notes: str | None = Field(None, description="Resolution notes")


class AlertManager:
    """Manages alert generation and storage."""

    def __init__(self) -> None:
        """Initialize alert manager."""
        self._alert_history: dict[str, list[PortfolioAlert]] = {}
        logger.info("Alert manager initialized")

    async def generate_alert(
        self,
        portfolio_id: str,
        alert_type: AlertType,
        severity: AlertSeverity,
        title: str,
        message: str,
        affected_positions: list[str],
        current_deviations: dict[str, float],
        recommended_actions: list[str],
    ) -> PortfolioAlert:
        """Generate and store a portfolio alert."""
        alert = PortfolioAlert(
            alert_id=f"{portfolio_id}_{alert_type.value}_{datetime.now().isoformat()}",
            portfolio_id=portfolio_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            affected_positions=affected_positions,
            current_deviations=current_deviations,
            recommended_actions=recommended_actions,
        )

        # Store alert in history
        if portfolio_id not in self._alert_history:
            self._alert_history[portfolio_id] = []
        self._alert_history[portfolio_id].append(alert)

        # Keep only recent alerts (last 100)
        self._alert_history[portfolio_id] = self._alert_history[portfolio_id][-100:]

        logger.info(f"Generated {severity.value} alert for portfolio {portfolio_id}: {title}")

        return alert

    async def generate_deviation_alert(
        self,
        portfolio_id: str,
        positions_out_of_tolerance: list[RebalancingNeed],
        max_deviation: float,
        max_deviation_threshold: float,
    ) -> PortfolioAlert:
        """Generate alert for deviation threshold breach."""
        affected_positions = [need.symbol for need in positions_out_of_tolerance]
        current_deviations = {need.symbol: need.deviation for need in positions_out_of_tolerance}

        severity = AlertSeverity.WARNING
        if max_deviation > max_deviation_threshold * 2:
            severity = AlertSeverity.ERROR
        if max_deviation > max_deviation_threshold * 3:
            severity = AlertSeverity.CRITICAL

        return await self.generate_alert(
            portfolio_id=portfolio_id,
            alert_type=AlertType.DEVIATION_ALERT,
            severity=severity,
            title=f"Portfolio Deviation Alert - {max_deviation:.1%}",
            message=f"Portfolio has {len(positions_out_of_tolerance)} positions exceeding tolerance bands. "
            f"Maximum deviation: {max_deviation:.1%} (threshold: {max_deviation_threshold:.1%})",
            affected_positions=affected_positions,
            current_deviations=current_deviations,
            recommended_actions=[
                "Review portfolio allocations",
                "Consider rebalancing affected positions",
                "Check if tolerance bands need adjustment",
            ],
        )

    async def generate_multiple_positions_alert(
        self,
        portfolio_id: str,
        positions_out_of_tolerance: list[RebalancingNeed],
    ) -> PortfolioAlert:
        """Generate alert for multiple positions needing rebalancing."""
        affected_positions = [need.symbol for need in positions_out_of_tolerance]
        current_deviations = {need.symbol: need.deviation for need in positions_out_of_tolerance}

        return await self.generate_alert(
            portfolio_id=portfolio_id,
            alert_type=AlertType.MULTIPLE_POSITIONS_ALERT,
            severity=AlertSeverity.WARNING,
            title=f"Multiple Positions Need Rebalancing - {len(positions_out_of_tolerance)} positions",
            message=f"{len(positions_out_of_tolerance)} positions are outside tolerance bands and may need rebalancing. Consider comprehensive portfolio rebalancing.",
            affected_positions=affected_positions,
            current_deviations=current_deviations,
            recommended_actions=[
                "Run comprehensive rebalancing analysis",
                "Review overall portfolio strategy",
                "Consider batch rebalancing to minimize costs",
            ],
        )

    async def generate_auto_rebalance_alert(
        self,
        portfolio_id: str,
        positions_out_of_tolerance: list[RebalancingNeed],
    ) -> PortfolioAlert:
        """Generate alert for auto-rebalancing recommendation."""
        affected_positions = [need.symbol for need in positions_out_of_tolerance]
        current_deviations = {need.symbol: need.deviation for need in positions_out_of_tolerance}

        return await self.generate_alert(
            portfolio_id=portfolio_id,
            alert_type=AlertType.AUTO_REBALANCE_TRIGGERED,
            severity=AlertSeverity.INFO,
            title="Auto-Rebalancing Recommended",
            message=f"Portfolio deviations exceed auto-rebalancing threshold. Automated rebalancing is recommended for {len(positions_out_of_tolerance)} positions.",
            affected_positions=affected_positions,
            current_deviations=current_deviations,
            recommended_actions=[
                "Execute automated rebalancing",
                "Review rebalancing recommendations",
                "Confirm available capital for rebalancing",
            ],
        )

    async def generate_error_alert(
        self,
        portfolio_id: str,
        error_message: str,
    ) -> PortfolioAlert:
        """Generate alert for monitoring error."""
        return await self.generate_alert(
            portfolio_id=portfolio_id,
            alert_type=AlertType.MONITORING_ERROR,
            severity=AlertSeverity.ERROR,
            title="Monitoring Error",
            message=f"Error occurred during monitoring: {error_message}",
            affected_positions=[],
            current_deviations={},
            recommended_actions=["Check monitoring system", "Review error logs"],
        )

    async def acknowledge_alert(self, portfolio_id: str, alert_id: str) -> bool:
        """Acknowledge an alert."""
        alerts = self._alert_history.get(portfolio_id, [])
        for alert in alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                logger.info(f"Acknowledged alert {alert_id} for portfolio {portfolio_id}")
                return True
        return False

    async def resolve_alert(self, portfolio_id: str, alert_id: str, resolution_notes: str = "") -> bool:
        """Resolve an alert."""
        alerts = self._alert_history.get(portfolio_id, [])
        for alert in alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                alert.resolution_notes = resolution_notes
                logger.info(f"Resolved alert {alert_id} for portfolio {portfolio_id}")
                return True
        return False

    async def get_active_alerts(self, portfolio_id: str) -> list[PortfolioAlert]:
        """Get all active (unresolved) alerts for a portfolio."""
        alerts = self._alert_history.get(portfolio_id, [])
        return [alert for alert in alerts if not alert.resolved]

    def _get_recent_alerts(self, portfolio_id: str, hours: int = 24) -> list[PortfolioAlert]:
        """Get recent alerts for a portfolio."""
        alerts = self._alert_history.get(portfolio_id, [])
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [alert for alert in alerts if alert.timestamp >= cutoff_time]

    def _get_monitoring_status_alerts(self, portfolio_id: str) -> tuple[int, int, datetime | None]:
        """Get alert counts and last alert timestamp for monitoring status."""
        alerts = self._alert_history.get(portfolio_id, [])
        active_alerts = len([alert for alert in alerts if not alert.resolved])
        unacknowledged_alerts = len([alert for alert in alerts if not alert.acknowledged])
        last_alert_timestamp = alerts[-1].timestamp if alerts else None
        return active_alerts, unacknowledged_alerts, last_alert_timestamp

    def get_alert_statistics(self) -> dict[str, Any]:
        """Get overall alert statistics."""
        total_alerts = sum(len(alerts) for alerts in self._alert_history.values())
        total_active = sum(len([alert for alert in alerts if not alert.resolved]) for alerts in self._alert_history.values())

        return {
            "total_alerts_generated": total_alerts,
            "total_active_alerts": total_active,
            "portfolios_with_alerts": len(self._alert_history),
        }
