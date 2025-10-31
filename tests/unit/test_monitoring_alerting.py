"""
Unit tests for Monitoring Alerting System.

Tests the alerting system for investment discovery monitoring,
including alert creation, notification delivery, and escalation.
"""

from datetime import datetime, timedelta

import pytest

from finwiz.monitoring.alerting import (
    Alert,
    AlertingConfig,
    AlertManager,
    AlertSeverity,
    AlertType,
    get_alert_manager,
    resolve_discovery_alert,
    send_discovery_alert,
)


class TestAlert:
    """Test cases for Alert dataclass."""

    def test_should_create_alert_with_required_fields(self):
        """Test creating alert with required fields."""
        alert = Alert(
            id="test_001",
            type=AlertType.DISCOVERY_RATE,
            severity=AlertSeverity.WARNING,
            title="Test Alert",
            message="This is a test alert",
            timestamp=datetime.now(),
        )

        assert alert.id == "test_001"
        assert alert.type == AlertType.DISCOVERY_RATE
        assert alert.severity == AlertSeverity.WARNING
        assert alert.title == "Test Alert"
        assert alert.message == "This is a test alert"
        assert not alert.resolved
        assert not alert.escalated
        assert alert.resolved_at is None
        assert alert.escalated_at is None


class TestAlertingConfig:
    """Test cases for AlertingConfig dataclass."""

    def test_should_initialize_with_defaults(self):
        """Test AlertingConfig initialization with default values."""
        config = AlertingConfig()

        assert config.smtp_host == "localhost"
        assert config.smtp_port == 587
        assert config.smtp_use_tls is True
        assert config.email_recipients == []
        assert config.critical_recipients == []
        assert config.webhook_urls == []
        assert config.escalation_timeout_minutes == 30
        assert config.max_alerts_per_hour == 10
        assert config.email_enabled is True
        assert config.webhook_enabled is True
        assert config.escalation_enabled is True


class TestAlertManager:
    """Test cases for AlertManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = AlertingConfig(
            email_recipients=["test@example.com"],
            critical_recipients=["critical@example.com"],
            webhook_urls=["http://webhook.example.com"],
            max_alerts_per_hour=5,
        )
        self.alert_manager = AlertManager(self.config)

    @pytest.mark.asyncio
    async def test_should_create_alert_successfully(self, mocker):
        """Test creating an alert successfully."""
        mock_send = mocker.patch.object(self.alert_manager, "_send_notifications", new_callable=mocker.AsyncMock)
        alert = await self.alert_manager.create_alert(
            AlertType.DISCOVERY_RATE,
            AlertSeverity.WARNING,
            "Low Discovery Rate",
            "Discovery rate has dropped below threshold",
            {"threshold": 5, "current": 2},
        )

        assert alert is not None
        assert alert.type == AlertType.DISCOVERY_RATE
        assert alert.severity == AlertSeverity.WARNING
        assert alert.title == "Low Discovery Rate"
        assert alert.message == "Discovery rate has dropped below threshold"
        assert alert.metadata["threshold"] == 5
        assert alert.metadata["current"] == 2

        # Check that alert is stored
        assert alert.id in self.alert_manager.active_alerts
        assert len(self.alert_manager.alert_history) == 1

        # Check that notifications were sent
        mock_send.assert_called_once_with(alert)

    @pytest.mark.asyncio
    async def test_should_rate_limit_alerts(self, mocker):
        """Test alert rate limiting."""
        # Create alerts up to the limit
        for i in range(self.config.max_alerts_per_hour):
            alert = await self.alert_manager.create_alert(AlertType.DISCOVERY_RATE, AlertSeverity.WARNING, f"Alert {i}", f"Test alert {i}")
            assert alert is not None

        # Next alert should be rate limited
        mocker.patch.object(self.alert_manager, "_send_notifications", new_callable=mocker.AsyncMock)
        rate_limited_alert = await self.alert_manager.create_alert(AlertType.DISCOVERY_RATE, AlertSeverity.WARNING, "Rate Limited Alert", "This should be rate limited")
        assert rate_limited_alert is None

    @pytest.mark.asyncio
    async def test_should_resolve_alert_successfully(self, mocker):
        """Test resolving an alert successfully."""
        # Create an alert first
        mocker.patch.object(self.alert_manager, "_send_notifications", new_callable=mocker.AsyncMock)
        alert = await self.alert_manager.create_alert(AlertType.ERROR_RATE, AlertSeverity.CRITICAL, "High Error Rate", "Error rate exceeded threshold")

        # Resolve the alert
        mock_resolution = mocker.patch.object(self.alert_manager, "_send_resolution_notification", new_callable=mocker.AsyncMock)
        success = await self.alert_manager.resolve_alert(alert.id, "Issue fixed")

        assert success is True
        assert alert.resolved is True
        assert alert.resolved_at is not None
        assert alert.metadata["resolution_message"] == "Issue fixed"

        # Check that alert is removed from active alerts
        assert alert.id not in self.alert_manager.active_alerts

        # Check that resolution notification was sent
        mock_resolution.assert_called_once_with(alert)

    @pytest.mark.asyncio
    async def test_should_fail_to_resolve_nonexistent_alert(self):
        """Test failing to resolve a non-existent alert."""
        success = await self.alert_manager.resolve_alert("nonexistent_id", "Test resolution")
        assert success is False

    @pytest.mark.asyncio
    async def test_should_escalate_alert_successfully(self, mocker):
        """Test escalating an alert successfully."""
        # Create a critical alert
        mocker.patch.object(self.alert_manager, "_send_notifications", new_callable=mocker.AsyncMock)
        alert = await self.alert_manager.create_alert(AlertType.SYSTEM_HEALTH, AlertSeverity.CRITICAL, "System Down", "System is not responding")

        # Escalate the alert
        mock_escalation = mocker.patch.object(self.alert_manager, "_send_escalation_notification", new_callable=mocker.AsyncMock)
        success = await self.alert_manager.escalate_alert(alert.id)

        assert success is True
        assert alert.escalated is True
        assert alert.escalated_at is not None

        # Check that escalation notification was sent
        mock_escalation.assert_called_once_with(alert)

    @pytest.mark.asyncio
    async def test_should_not_escalate_already_escalated_alert(self, mocker):
        """Test not escalating an already escalated alert."""
        # Create and escalate an alert
        mocker.patch.object(self.alert_manager, "_send_notifications", new_callable=mocker.AsyncMock)
        alert = await self.alert_manager.create_alert(AlertType.QUALITY, AlertSeverity.CRITICAL, "Quality Issue", "Quality metrics degraded")

        mocker.patch.object(self.alert_manager, "_send_escalation_notification", new_callable=mocker.AsyncMock)
        await self.alert_manager.escalate_alert(alert.id)

        # Try to escalate again
        mock_escalation = mocker.patch.object(self.alert_manager, "_send_escalation_notification", new_callable=mocker.AsyncMock)
        success = await self.alert_manager.escalate_alert(alert.id)

        assert success is True  # Returns True but doesn't escalate again
        mock_escalation.assert_not_called()

    @pytest.mark.asyncio
    async def test_should_check_escalations_for_old_critical_alerts(self, mocker):
        """Test checking escalations for old critical alerts."""
        # Create a critical alert with old timestamp
        mocker.patch.object(self.alert_manager, "_send_notifications", new_callable=mocker.AsyncMock)
        alert = await self.alert_manager.create_alert(AlertType.PERFORMANCE, AlertSeverity.CRITICAL, "Performance Issue", "System performance degraded")

        # Manually set timestamp to be old enough for escalation
        alert.timestamp = datetime.now() - timedelta(minutes=35)

        # Check escalations
        mock_escalation = mocker.patch.object(self.alert_manager, "_send_escalation_notification", new_callable=mocker.AsyncMock)
        await self.alert_manager.check_escalations()

        assert alert.escalated is True
        mock_escalation.assert_called_once_with(alert)

    def test_should_get_active_alerts_all(self):
        """Test getting all active alerts."""
        # Create some test alerts
        alert1 = Alert(
            id="test_001",
            type=AlertType.DISCOVERY_RATE,
            severity=AlertSeverity.WARNING,
            title="Alert 1",
            message="Test alert 1",
            timestamp=datetime.now() - timedelta(minutes=10),
        )
        alert2 = Alert(
            id="test_002",
            type=AlertType.ERROR_RATE,
            severity=AlertSeverity.CRITICAL,
            title="Alert 2",
            message="Test alert 2",
            timestamp=datetime.now() - timedelta(minutes=5),
        )

        self.alert_manager.active_alerts[alert1.id] = alert1
        self.alert_manager.active_alerts[alert2.id] = alert2

        active_alerts = self.alert_manager.get_active_alerts()

        assert len(active_alerts) == 2
        # Should be sorted by timestamp (newest first)
        assert active_alerts[0].id == "test_002"
        assert active_alerts[1].id == "test_001"

    def test_should_get_active_alerts_filtered_by_severity(self):
        """Test getting active alerts filtered by severity."""
        # Create alerts with different severities
        warning_alert = Alert(
            id="warning_001",
            type=AlertType.DISCOVERY_RATE,
            severity=AlertSeverity.WARNING,
            title="Warning Alert",
            message="Warning message",
            timestamp=datetime.now(),
        )
        critical_alert = Alert(
            id="critical_001",
            type=AlertType.ERROR_RATE,
            severity=AlertSeverity.CRITICAL,
            title="Critical Alert",
            message="Critical message",
            timestamp=datetime.now(),
        )

        self.alert_manager.active_alerts[warning_alert.id] = warning_alert
        self.alert_manager.active_alerts[critical_alert.id] = critical_alert

        # Get only critical alerts
        critical_alerts = self.alert_manager.get_active_alerts(AlertSeverity.CRITICAL)

        assert len(critical_alerts) == 1
        assert critical_alerts[0].id == "critical_001"
        assert critical_alerts[0].severity == AlertSeverity.CRITICAL

    def test_should_get_alert_summary(self):
        """Test getting alert summary."""
        # Create test alerts
        now = datetime.now()
        alerts = [
            Alert("001", AlertType.DISCOVERY_RATE, AlertSeverity.WARNING, "Alert 1", "Message 1", now - timedelta(minutes=30)),
            Alert("002", AlertType.ERROR_RATE, AlertSeverity.CRITICAL, "Alert 2", "Message 2", now - timedelta(minutes=20)),
            Alert("003", AlertType.QUALITY, AlertSeverity.WARNING, "Alert 3", "Message 3", now - timedelta(minutes=10)),
        ]

        # Set one as escalated
        alerts[1].escalated = True

        for alert in alerts:
            self.alert_manager.active_alerts[alert.id] = alert

        summary = self.alert_manager.get_alert_summary()

        assert summary["total_active"] == 3
        assert summary["by_severity"]["warning"] == 2
        assert summary["by_severity"]["critical"] == 1
        assert summary["by_severity"]["info"] == 0
        assert summary["escalated_count"] == 1
        assert summary["oldest_alert"] == alerts[0].timestamp
        assert summary["newest_alert"] == alerts[2].timestamp

    def test_should_check_rate_limit_within_limit(self):
        """Test rate limiting when within limit."""
        alert_type = "test_type"

        # Should allow alerts within limit
        for i in range(self.config.max_alerts_per_hour):
            allowed = self.alert_manager._check_rate_limit(alert_type)
            assert allowed is True

        # Should reject when over limit
        rejected = self.alert_manager._check_rate_limit(alert_type)
        assert rejected is False

    def test_should_reset_rate_limit_after_hour(self):
        """Test rate limit reset after an hour."""
        alert_type = "test_type"

        # Fill up the rate limit
        for i in range(self.config.max_alerts_per_hour):
            self.alert_manager._check_rate_limit(alert_type)

        # Should be rate limited
        assert self.alert_manager._check_rate_limit(alert_type) is False

        # Manually set old timestamps (simulate time passing)
        old_time = datetime.now() - timedelta(hours=2)
        self.alert_manager.rate_limiter[alert_type] = [old_time] * self.config.max_alerts_per_hour

        # Should allow new alerts after cleanup
        assert self.alert_manager._check_rate_limit(alert_type) is True

    @pytest.mark.asyncio
    async def test_should_send_email_notification(self, mocker):
        """Test sending email notification."""
        alert = Alert(
            id="email_test",
            type=AlertType.DISCOVERY_RATE,
            severity=AlertSeverity.WARNING,
            title="Email Test",
            message="Test email notification",
            timestamp=datetime.now(),
        )

        mock_smtp = mocker.patch("smtplib.SMTP")
        mock_server = mocker.MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        await self.alert_manager._send_email_notification(alert)

        # Check that SMTP was used
        mock_smtp.assert_called_once_with(self.config.smtp_host, self.config.smtp_port)
        mock_server.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_send_webhook_notifications(self, mocker):
        """Test sending webhook notifications."""
        alert = Alert(
            id="webhook_test",
            type=AlertType.ERROR_RATE,
            severity=AlertSeverity.CRITICAL,
            title="Webhook Test",
            message="Test webhook notification",
            timestamp=datetime.now(),
        )

        mock_client = mocker.patch("httpx.AsyncClient")
        mock_response = mocker.MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

        await self.alert_manager._send_webhook_notifications(alert)

        # Check that HTTP POST was made
        mock_client.return_value.__aenter__.return_value.post.assert_called_once()


class TestGlobalAlertFunctions:
    """Test cases for global alert functions."""

    def test_should_get_alert_manager_singleton(self):
        """Test getting alert manager singleton."""
        manager1 = get_alert_manager()
        manager2 = get_alert_manager()

        assert manager1 is manager2

    @pytest.mark.asyncio
    async def test_should_send_discovery_alert(self, mocker):
        """Test sending discovery alert via global function."""
        mock_get_manager = mocker.patch("finwiz.monitoring.alerting.get_alert_manager")
        mock_manager = mocker.MagicMock()
        mock_manager.create_alert = mocker.AsyncMock(return_value=mocker.MagicMock())
        mock_get_manager.return_value = mock_manager

        alert = await send_discovery_alert(AlertType.DISCOVERY_RATE, AlertSeverity.WARNING, "Test Alert", "Test message", {"test": "metadata"})

        assert alert is not None
        mock_manager.create_alert.assert_called_once_with(AlertType.DISCOVERY_RATE, AlertSeverity.WARNING, "Test Alert", "Test message", {"test": "metadata"})

    @pytest.mark.asyncio
    async def test_should_resolve_discovery_alert(self, mocker):
        """Test resolving discovery alert via global function."""
        mock_get_manager = mocker.patch("finwiz.monitoring.alerting.get_alert_manager")
        mock_manager = mocker.MagicMock()
        mock_manager.resolve_alert = mocker.AsyncMock(return_value=True)
        mock_get_manager.return_value = mock_manager

        success = await resolve_discovery_alert("test_alert_id", "Test resolution")

        assert success is True
        mock_manager.resolve_alert.assert_called_once_with("test_alert_id", "Test resolution")
