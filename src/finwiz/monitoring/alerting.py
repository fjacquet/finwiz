"""
Alerting System for Investment Discovery Monitoring.

This module provides comprehensive alerting capabilities for the Investment
Discovery system, including email notifications, webhook alerts, and
escalation procedures for production deployment.
"""

import asyncio
import json
import os
import smtplib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from typing import Any

import httpx

from finwiz.tools.logger import get_logger
from finwiz.utils.configuration_manager import get_configuration_manager

logger = get_logger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of alerts."""

    DISCOVERY_RATE = "discovery_rate"
    ERROR_RATE = "error_rate"
    SUCCESS_RATE = "success_rate"
    PERFORMANCE = "performance"
    QUALITY = "quality"
    SYSTEM_HEALTH = "system_health"


@dataclass
class Alert:
    """Alert data structure."""

    id: str
    type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: datetime | None = None
    escalated: bool = False
    escalated_at: datetime | None = None


@dataclass
class AlertingConfig:
    """Configuration for alerting system."""

    # Email configuration
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True

    # Recipients
    email_recipients: list[str] = field(default_factory=list)
    critical_recipients: list[str] = field(default_factory=list)

    # Webhook configuration
    webhook_urls: list[str] = field(default_factory=list)

    # Alert thresholds
    escalation_timeout_minutes: int = 30
    max_alerts_per_hour: int = 10

    # Feature flags
    email_enabled: bool = True
    webhook_enabled: bool = True
    escalation_enabled: bool = True


class AlertManager:
    """
    Comprehensive alert management system for Investment Discovery.

    Handles alert generation, notification delivery, escalation,
    and resolution tracking for production monitoring.
    """

    def __init__(self, config: AlertingConfig | None = None) -> None:
        """Initialize the alert manager."""
        self.config = config or AlertingConfig()
        self.active_alerts: dict[str, Alert] = {}
        self.alert_history: list[Alert] = []
        self.rate_limiter: dict[str, list[datetime]] = {}

        # Load configuration from environment
        self._load_config_from_env()

        logger.info("Alert Manager initialized")

    def _load_config_from_env(self) -> None:
        """Load configuration from environment variables."""
        config_manager = get_configuration_manager()

        # Email configuration
        self.config.smtp_host = os.getenv("SMTP_HOST", self.config.smtp_host)
        self.config.smtp_port = int(os.getenv("SMTP_PORT", str(self.config.smtp_port)))
        self.config.smtp_username = os.getenv("SMTP_USERNAME", self.config.smtp_username)
        self.config.smtp_password = os.getenv("SMTP_PASSWORD", self.config.smtp_password)

        # Recipients
        email_recipients = os.getenv("ALERT_EMAIL_RECIPIENTS", "")
        if email_recipients:
            self.config.email_recipients = [email.strip() for email in email_recipients.split(",")]

        critical_recipients = os.getenv("ALERT_CRITICAL_RECIPIENTS", "")
        if critical_recipients:
            self.config.critical_recipients = [email.strip() for email in critical_recipients.split(",")]

        # Webhook URLs
        webhook_urls = os.getenv("ALERT_WEBHOOK_URLS", "")
        if webhook_urls:
            self.config.webhook_urls = [url.strip() for url in webhook_urls.split(",")]

        # Feature flags
        self.config.email_enabled = os.getenv("ALERT_EMAIL_ENABLED", "true").lower() == "true"
        self.config.webhook_enabled = os.getenv("ALERT_WEBHOOK_ENABLED", "true").lower() == "true"
        self.config.escalation_enabled = os.getenv("ALERT_ESCALATION_ENABLED", "true").lower() == "true"

    async def create_alert(self, alert_type: AlertType, severity: AlertSeverity, title: str, message: str, metadata: dict[str, Any] | None = None) -> Alert | None:
        """Create and process a new alert."""
        # Generate unique alert ID
        alert_id = f"{alert_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        # Check rate limiting
        if not self._check_rate_limit(alert_type.value):
            logger.warning(f"Alert rate limited: {alert_type.value}")
            return None

        # Create alert
        alert = Alert(
            id=alert_id,
            type=alert_type,
            severity=severity,
            title=title,
            message=message,
            timestamp=datetime.now(),
            metadata=metadata or {},
        )

        # Store alert
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)

        # Send notifications
        await self._send_notifications(alert)

        logger.info(f"Alert created: {alert_id} ({severity.value}) - {title}")

        return alert

    async def resolve_alert(self, alert_id: str, resolution_message: str = "") -> bool:
        """Resolve an active alert."""
        if alert_id not in self.active_alerts:
            logger.warning(f"Alert not found for resolution: {alert_id}")
            return False

        alert = self.active_alerts[alert_id]
        alert.resolved = True
        alert.resolved_at = datetime.now()

        if resolution_message:
            alert.metadata["resolution_message"] = resolution_message

        # Remove from active alerts
        del self.active_alerts[alert_id]

        # Send resolution notification
        await self._send_resolution_notification(alert)

        logger.info(f"Alert resolved: {alert_id}")

        return True

    async def escalate_alert(self, alert_id: str) -> bool:
        """Escalate an alert to critical recipients."""
        if alert_id not in self.active_alerts:
            logger.warning(f"Alert not found for escalation: {alert_id}")
            return False

        alert = self.active_alerts[alert_id]

        if alert.escalated:
            logger.info(f"Alert already escalated: {alert_id}")
            return True

        alert.escalated = True
        alert.escalated_at = datetime.now()

        # Send escalation notification
        await self._send_escalation_notification(alert)

        logger.warning(f"Alert escalated: {alert_id}")

        return True

    async def check_escalations(self) -> None:
        """Check for alerts that need escalation."""
        if not self.config.escalation_enabled:
            return

        escalation_threshold = datetime.now() - timedelta(minutes=self.config.escalation_timeout_minutes)

        for alert in self.active_alerts.values():
            if not alert.escalated and alert.severity == AlertSeverity.CRITICAL and alert.timestamp <= escalation_threshold:
                await self.escalate_alert(alert.id)

    def get_active_alerts(self, severity: AlertSeverity | None = None) -> list[Alert]:
        """Get active alerts, optionally filtered by severity."""
        alerts = list(self.active_alerts.values())

        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]

        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)

    def get_alert_summary(self) -> dict[str, Any]:
        """Get summary of alert status."""
        active_alerts = list(self.active_alerts.values())

        summary = {
            "total_active": len(active_alerts),
            "by_severity": {
                "critical": len([a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]),
                "warning": len([a for a in active_alerts if a.severity == AlertSeverity.WARNING]),
                "info": len([a for a in active_alerts if a.severity == AlertSeverity.INFO]),
            },
            "by_type": {},
            "escalated_count": len([a for a in active_alerts if a.escalated]),
            "oldest_alert": min([a.timestamp for a in active_alerts]) if active_alerts else None,
            "newest_alert": max([a.timestamp for a in active_alerts]) if active_alerts else None,
        }

        # Count by type
        for alert_type in AlertType:
            summary["by_type"][alert_type.value] = len([a for a in active_alerts if a.type == alert_type])

        return summary

    def _check_rate_limit(self, alert_type: str) -> bool:
        """Check if alert type is rate limited."""
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)

        # Initialize rate limiter for this type
        if alert_type not in self.rate_limiter:
            self.rate_limiter[alert_type] = []

        # Clean old entries
        self.rate_limiter[alert_type] = [timestamp for timestamp in self.rate_limiter[alert_type] if timestamp > hour_ago]

        # Check limit
        if len(self.rate_limiter[alert_type]) >= self.config.max_alerts_per_hour:
            return False

        # Add current timestamp
        self.rate_limiter[alert_type].append(now)
        return True

    async def _send_notifications(self, alert: Alert) -> None:
        """Send notifications for an alert."""
        tasks = []

        # Email notifications
        if self.config.email_enabled and self.config.email_recipients:
            tasks.append(self._send_email_notification(alert))

        # Webhook notifications
        if self.config.webhook_enabled and self.config.webhook_urls:
            tasks.append(self._send_webhook_notifications(alert))

        # Execute all notifications concurrently
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_email_notification(self, alert: Alert) -> None:
        """Send email notification for an alert."""
        try:
            # Determine recipients
            recipients = self.config.email_recipients.copy()
            if alert.severity == AlertSeverity.CRITICAL and self.config.critical_recipients:
                recipients.extend(self.config.critical_recipients)

            # Remove duplicates
            recipients = list(set(recipients))

            if not recipients:
                logger.warning("No email recipients configured for alerts")
                return

            # Create email
            msg = MIMEMultipart()
            msg["From"] = self.config.smtp_username
            msg["To"] = ", ".join(recipients)
            msg["Subject"] = f"[FinWiz Alert] {alert.severity.value.upper()}: {alert.title}"

            # Email body
            body = f"""
Investment Discovery Alert

Severity: {alert.severity.value.upper()}
Type: {alert.type.value}
Time: {alert.timestamp.strftime("%Y-%m-%d %H:%M:%S")}

Message:
{alert.message}

Metadata:
{json.dumps(alert.metadata, indent=2, default=str)}

Alert ID: {alert.id}

---
FinWiz Investment Discovery Monitoring System
            """.strip()

            msg.attach(MIMEText(body, "plain"))

            # Send email
            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                if self.config.smtp_use_tls:
                    server.starttls()

                if self.config.smtp_username and self.config.smtp_password:
                    server.login(self.config.smtp_username, self.config.smtp_password)

                server.send_message(msg)

            logger.info(f"Email notification sent for alert: {alert.id}")

        except Exception as e:
            logger.error(f"Failed to send email notification for alert {alert.id}: {e}")

    async def _send_webhook_notifications(self, alert: Alert) -> None:
        """Send webhook notifications for an alert."""
        payload = {
            "alert_id": alert.id,
            "type": alert.type.value,
            "severity": alert.severity.value,
            "title": alert.title,
            "message": alert.message,
            "timestamp": alert.timestamp.isoformat(),
            "metadata": alert.metadata,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            for webhook_url in self.config.webhook_urls:
                try:
                    response = await client.post(webhook_url, json=payload, headers={"Content-Type": "application/json"})
                    response.raise_for_status()

                    logger.info(f"Webhook notification sent to {webhook_url} for alert: {alert.id}")

                except Exception as e:
                    logger.error(f"Failed to send webhook notification to {webhook_url} for alert {alert.id}: {e}")

    async def _send_resolution_notification(self, alert: Alert) -> None:
        """Send notification when an alert is resolved."""
        # Create resolution alert
        resolution_alert = Alert(
            id=f"resolved_{alert.id}",
            type=alert.type,
            severity=AlertSeverity.INFO,
            title=f"RESOLVED: {alert.title}",
            message=f"Alert has been resolved: {alert.message}",
            timestamp=datetime.now(),
            metadata={
                "original_alert_id": alert.id,
                "resolution_time": alert.resolved_at.isoformat() if alert.resolved_at else None,
                "duration_minutes": ((alert.resolved_at - alert.timestamp).total_seconds() / 60 if alert.resolved_at else None),
            },
        )

        await self._send_notifications(resolution_alert)

    async def _send_escalation_notification(self, alert: Alert) -> None:
        """Send notification when an alert is escalated."""
        if not self.config.critical_recipients:
            logger.warning("No critical recipients configured for escalation")
            return

        # Send to critical recipients only
        original_recipients = self.config.email_recipients.copy()
        self.config.email_recipients = self.config.critical_recipients.copy()

        try:
            escalation_alert = Alert(
                id=f"escalated_{alert.id}",
                type=alert.type,
                severity=AlertSeverity.CRITICAL,
                title=f"ESCALATED: {alert.title}",
                message=f"Alert has been escalated due to no resolution: {alert.message}",
                timestamp=datetime.now(),
                metadata={
                    "original_alert_id": alert.id,
                    "escalation_time": alert.escalated_at.isoformat() if alert.escalated_at else None,
                    "time_since_creation_minutes": ((datetime.now() - alert.timestamp).total_seconds() / 60),
                },
            )

            await self._send_notifications(escalation_alert)

        finally:
            # Restore original recipients
            self.config.email_recipients = original_recipients


# Global alert manager instance
_alert_manager: AlertManager | None = None


def get_alert_manager() -> AlertManager:
    """Get the global alert manager instance."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager


async def send_discovery_alert(alert_type: AlertType, severity: AlertSeverity, title: str, message: str, metadata: dict[str, Any] | None = None) -> Alert | None:
    """Send an investment discovery alert."""
    alert_manager = get_alert_manager()
    return await alert_manager.create_alert(alert_type, severity, title, message, metadata)


async def resolve_discovery_alert(alert_id: str, resolution_message: str = "") -> bool:
    """Resolve an investment discovery alert."""
    alert_manager = get_alert_manager()
    return await alert_manager.resolve_alert(alert_id, resolution_message)


async def check_alert_escalations() -> None:
    """Check for alerts that need escalation."""
    alert_manager = get_alert_manager()
    await alert_manager.check_escalations()
