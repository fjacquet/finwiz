"""
Integration tests for portfolio monitoring and alerting system.

Tests cover the complete workflow from portfolio monitoring to alert generation
and notification delivery.
"""

import pytest

from finwiz.quantitative.portfolio_analyzer import PortfolioAnalyzer
from finwiz.quantitative.portfolio_monitor import (
    AlertSeverity,
    AlertType,
    MonitoringRule,
    PortfolioMonitor,
    UrgencyLevel,
)
from finwiz.quantitative.rebalancing_engine import RebalancingEngine
from finwiz.schemas.portfolio_rebalancing import (
    Holding,
    PortfolioAnalysis,
    PortfolioConfiguration,
    RebalancingNeed,
    TradeAction,
)
from finwiz.tools.notification_service import (
    NotificationPreferences,
    NotificationService,
    NotificationType,
)
from finwiz.tools.portfolio_price_service import PortfolioPriceService


class TestPortfolioMonitoringIntegration:
    """Integration tests for complete portfolio monitoring workflow."""

    @pytest.fixture
    def mock_price_service(self, mocker):
        """Mock price service with realistic price data."""
        mock_service = mocker.patch.object(PortfolioPriceService, "get_current_prices")
        mock_service.return_value = {"AAPL": 150.0, "GOOGL": 2500.0, "MSFT": 300.0, "TSLA": 800.0}
        return mock_service

    @pytest.fixture
    def sample_portfolio_config(self):
        """Sample portfolio configuration with realistic holdings."""
        return PortfolioConfiguration(
            holdings=[
                Holding(symbol="AAPL", shares=100),  # $15,000
                Holding(symbol="GOOGL", shares=10),  # $25,000
                Holding(symbol="MSFT", shares=50),  # $15,000
                Holding(symbol="TSLA", shares=25),  # $20,000
            ],
            target_weights={
                "AAPL": 0.25,  # Target: 25%, Current: ~20%
                "GOOGL": 0.30,  # Target: 30%, Current: ~33%
                "MSFT": 0.25,  # Target: 25%, Current: ~20%
                "TSLA": 0.20,  # Target: 20%, Current: ~27%
            },
            global_tolerance=0.05,  # 5% tolerance
            available_capital=5000.0,
        )

    @pytest.fixture
    def monitoring_rule(self):
        """Create monitoring rule for testing."""
        return MonitoringRule(
            rule_id="test_monitoring_rule",
            rule_name="Test Portfolio Monitoring",
            max_deviation_threshold=0.08,  # 8% threshold
            min_check_interval_hours=1,
            alert_on_deviation=True,
            alert_on_multiple_positions=True,
            min_positions_for_alert=2,
            enable_auto_rebalancing=False,
        )

    @pytest.fixture
    def notification_preferences(self):
        """Notification preferences for testing."""
        return NotificationPreferences(
            email_address="test@example.com",
            phone_number="+1234567890",
            enabled_notification_types=[NotificationType.EMAIL, NotificationType.SMS],
            email_alert_levels=[AlertSeverity.WARNING, AlertSeverity.ERROR, AlertSeverity.CRITICAL],
            sms_alert_levels=[AlertSeverity.ERROR, AlertSeverity.CRITICAL],
            max_notifications_per_hour=10,
            include_detailed_analysis=True,
            include_recommendations=True,
        )

    @pytest.mark.asyncio
    async def test_should_complete_full_monitoring_workflow_when_deviations_detected(
        self, mocker, mock_price_service, sample_portfolio_config, monitoring_rule, notification_preferences
    ):
        """Test complete monitoring workflow from drift detection to notification."""
        # Arrange
        portfolio_id = "integration_test_portfolio"
        user_id = "test_user"

        # Initialize services
        price_service = PortfolioPriceService()
        portfolio_analyzer = PortfolioAnalyzer()
        rebalancing_engine = RebalancingEngine()
        portfolio_monitor = PortfolioMonitor(price_service, portfolio_analyzer, rebalancing_engine)
        notification_service = NotificationService()

        # Set up notification preferences
        notification_service.set_user_preferences(user_id, notification_preferences)

        # Mock portfolio analyzer to return realistic rebalancing needs
        mock_rebalancing_needs = [
            RebalancingNeed(
                symbol="AAPL",
                current_weight=0.20,
                target_weight=0.25,
                deviation=-0.05,
                tolerance_band=0.05,
                exceeds_tolerance=False,
                urgency_score=0.4,
                recommended_action=TradeAction.BUY,
            ),
            RebalancingNeed(
                symbol="GOOGL",
                current_weight=0.33,
                target_weight=0.30,
                deviation=0.03,
                tolerance_band=0.05,
                exceeds_tolerance=False,
                urgency_score=0.3,
                recommended_action=TradeAction.SELL,
            ),
            RebalancingNeed(
                symbol="MSFT",
                current_weight=0.20,
                target_weight=0.25,
                deviation=-0.05,
                tolerance_band=0.05,
                exceeds_tolerance=False,
                urgency_score=0.4,
                recommended_action=TradeAction.BUY,
            ),
            RebalancingNeed(
                symbol="TSLA",
                current_weight=0.27,
                target_weight=0.20,
                deviation=0.07,
                tolerance_band=0.05,
                exceeds_tolerance=True,  # Exceeds tolerance
                urgency_score=0.7,
                recommended_action=TradeAction.SELL,
            ),
        ]

        # Mock the analyzer methods
        portfolio_analyzer.analyze_current_portfolio = mocker.AsyncMock(
            return_value=PortfolioAnalysis(
                total_value=75000.0,
                weightings={"AAPL": 0.20, "GOOGL": 0.33, "MSFT": 0.20, "TSLA": 0.27},
                deviations_from_target={"AAPL": -0.05, "GOOGL": 0.03, "MSFT": -0.05, "TSLA": 0.07},
                positions_needing_rebalancing=["TSLA"],
            )
        )
        portfolio_analyzer.identify_rebalancing_needs = mocker.MagicMock(return_value=mock_rebalancing_needs)

        # Mock notification providers to track calls
        mock_email_provider = mocker.AsyncMock()
        mock_sms_provider = mocker.AsyncMock()
        notification_service.providers[NotificationType.EMAIL] = mock_email_provider
        notification_service.providers[NotificationType.SMS] = mock_sms_provider

        # Act - Perform drift check
        rebalancing_needs = await portfolio_monitor.check_portfolio_drift(portfolio_id, sample_portfolio_config)

        # Assert - Verify drift detection
        assert len(rebalancing_needs) == 4
        positions_exceeding_tolerance = [need for need in rebalancing_needs if need.exceeds_tolerance]
        assert len(positions_exceeding_tolerance) == 1
        assert positions_exceeding_tolerance[0].symbol == "TSLA"

        # Act - Generate health dashboard
        dashboard = await portfolio_monitor.generate_health_dashboard(portfolio_id, sample_portfolio_config)

        # Assert - Verify dashboard generation
        assert dashboard.portfolio_id == portfolio_id
        assert dashboard.max_deviation == 0.07  # TSLA deviation
        assert len(dashboard.positions_needing_attention) == 1
        assert dashboard.positions_needing_attention[0].symbol == "TSLA"
        assert dashboard.rebalancing_urgency == UrgencyLevel.LOW  # Only one position exceeds tolerance

        # Act - Simulate alert generation (would normally happen in monitoring loop)
        alert = await portfolio_monitor._generate_alert(
            portfolio_id=portfolio_id,
            alert_type=AlertType.DEVIATION_ALERT,
            severity=AlertSeverity.WARNING,
            title="Portfolio Deviation Detected",
            message="TSLA position exceeds tolerance band by 2%",
            affected_positions=["TSLA"],
            current_deviations={"TSLA": 0.07},
            recommended_actions=["Consider selling TSLA shares", "Review portfolio allocation"],
        )

        # Assert - Verify alert generation
        assert alert.portfolio_id == portfolio_id
        assert alert.alert_type == AlertType.DEVIATION_ALERT
        assert alert.severity == AlertSeverity.WARNING
        assert "TSLA" in alert.affected_positions

        # Act - Send notifications
        notification_records = await notification_service.send_alert_notification(alert, user_id)

        # Assert - Verify notifications sent
        assert len(notification_records) == 1  # Only email for WARNING level
        assert notification_records[0].notification_type == NotificationType.EMAIL
        mock_email_provider.send_notification.assert_called_once()
        mock_sms_provider.send_notification.assert_not_called()  # SMS only for ERROR+

    @pytest.mark.asyncio
    async def test_should_send_multiple_notifications_when_critical_alert_generated(
        self, mocker, mock_price_service, sample_portfolio_config, monitoring_rule, notification_preferences
    ):
        """Test that critical alerts trigger both email and SMS notifications."""
        # Arrange
        portfolio_id = "critical_test_portfolio"
        user_id = "test_user"

        # Initialize services
        portfolio_monitor = PortfolioMonitor()
        notification_service = NotificationService()
        notification_service.set_user_preferences(user_id, notification_preferences)

        # Mock notification providers
        mock_email_provider = mocker.AsyncMock()
        mock_sms_provider = mocker.AsyncMock()
        notification_service.providers[NotificationType.EMAIL] = mock_email_provider
        notification_service.providers[NotificationType.SMS] = mock_sms_provider

        # Act - Generate critical alert
        critical_alert = await portfolio_monitor._generate_alert(
            portfolio_id=portfolio_id,
            alert_type=AlertType.MULTIPLE_POSITIONS_ALERT,
            severity=AlertSeverity.CRITICAL,
            title="Critical Portfolio Imbalance",
            message="Multiple positions severely out of tolerance",
            affected_positions=["AAPL", "GOOGL", "TSLA"],
            current_deviations={"AAPL": -0.15, "GOOGL": 0.12, "TSLA": 0.18},
            recommended_actions=["Immediate rebalancing required", "Contact financial advisor"],
        )

        # Send notifications
        notification_records = await notification_service.send_alert_notification(critical_alert, user_id)

        # Assert - Verify both notifications sent
        assert len(notification_records) == 2
        notification_types = [record.notification_type for record in notification_records]
        assert NotificationType.EMAIL in notification_types
        assert NotificationType.SMS in notification_types
        mock_email_provider.send_notification.assert_called_once()
        mock_sms_provider.send_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_respect_quiet_hours_when_sending_notifications(self, mocker, mock_price_service, sample_portfolio_config, notification_preferences):
        """Test that notifications respect quiet hours settings."""
        # Arrange
        portfolio_id = "quiet_hours_test_portfolio"
        user_id = "test_user"

        # Set quiet hours preferences
        quiet_hours_preferences = NotificationPreferences(
            email_address="test@example.com",
            enabled_notification_types=[NotificationType.EMAIL],
            email_alert_levels=[AlertSeverity.WARNING],
            quiet_hours_start=22,
            quiet_hours_end=7,
            max_notifications_per_hour=10,
        )

        portfolio_monitor = PortfolioMonitor()
        notification_service = NotificationService()
        notification_service.set_user_preferences(user_id, quiet_hours_preferences)

        # Mock current time to be in quiet hours (11 PM)
        with pytest.MonkeyPatch().context() as m:
            mock_datetime = mocker.MagicMock()
            mock_datetime.now.return_value.hour = 23
            m.setattr("finwiz.tools.notification_service.datetime", mock_datetime)

            # Mock notification provider
            mock_email_provider = mocker.AsyncMock()
            notification_service.providers[NotificationType.EMAIL] = mock_email_provider

            # Act - Generate alert during quiet hours
            alert = await portfolio_monitor._generate_alert(
                portfolio_id=portfolio_id,
                alert_type=AlertType.DEVIATION_ALERT,
                severity=AlertSeverity.WARNING,
                title="Portfolio Alert During Quiet Hours",
                message="Test alert during quiet hours",
                affected_positions=[],
                current_deviations={},
                recommended_actions=[],
            )

            # Send notifications
            notification_records = await notification_service.send_alert_notification(alert, user_id)

            # Assert - Verify no notifications sent during quiet hours
            assert len(notification_records) == 0
            mock_email_provider.send_notification.assert_not_called()

    @pytest.mark.asyncio
    async def test_should_respect_rate_limiting_when_sending_notifications(self, mocker, mock_price_service, sample_portfolio_config, notification_preferences):
        """Test that notifications respect rate limiting settings."""
        # Arrange
        portfolio_id = "rate_limit_test_portfolio"
        user_id = "test_user"

        # Set low rate limit
        rate_limit_preferences = NotificationPreferences(
            email_address="test@example.com",
            enabled_notification_types=[NotificationType.EMAIL],
            email_alert_levels=[AlertSeverity.WARNING],
            max_notifications_per_hour=2,  # Low limit for testing
        )

        portfolio_monitor = PortfolioMonitor()
        notification_service = NotificationService()
        notification_service.set_user_preferences(user_id, rate_limit_preferences)

        # Mock notification provider
        mock_email_provider = mocker.AsyncMock()
        notification_service.providers[NotificationType.EMAIL] = mock_email_provider

        # Act - Send multiple alerts to exceed rate limit
        alerts_sent = 0
        for i in range(5):  # Try to send 5 alerts (exceeds limit of 2)
            alert = await portfolio_monitor._generate_alert(
                portfolio_id=portfolio_id,
                alert_type=AlertType.DEVIATION_ALERT,
                severity=AlertSeverity.WARNING,
                title=f"Portfolio Alert {i + 1}",
                message=f"Test alert {i + 1}",
                affected_positions=[],
                current_deviations={},
                recommended_actions=[],
            )

            notification_records = await notification_service.send_alert_notification(alert, user_id)
            alerts_sent += len(notification_records)

        # Assert - Verify rate limiting applied
        assert alerts_sent <= 2  # Should not exceed rate limit
        assert mock_email_provider.send_notification.call_count <= 2

    @pytest.mark.asyncio
    async def test_should_handle_monitoring_errors_gracefully(self, mocker, mock_price_service, sample_portfolio_config, monitoring_rule):
        """Test that monitoring system handles errors gracefully."""
        # Arrange
        portfolio_id = "error_test_portfolio"

        # Create portfolio monitor with failing price service
        failing_price_service = mocker.MagicMock()
        failing_price_service.get_current_prices = mocker.AsyncMock(side_effect=Exception("Price service unavailable"))

        portfolio_monitor = PortfolioMonitor(price_service=failing_price_service)

        # Act & Assert - Should handle error gracefully
        with pytest.raises(Exception, match="Price service unavailable"):
            await portfolio_monitor.check_portfolio_drift(portfolio_id, sample_portfolio_config)

        # Verify that monitoring can continue after error
        # (In real implementation, this would generate an error alert)
        stats = portfolio_monitor.get_monitoring_statistics()
        assert isinstance(stats, dict)

    @pytest.mark.asyncio
    async def test_should_track_alert_acknowledgment_and_resolution(self, mocker, mock_price_service, sample_portfolio_config):
        """Test alert acknowledgment and resolution workflow."""
        # Arrange
        portfolio_id = "alert_lifecycle_test_portfolio"
        portfolio_monitor = PortfolioMonitor()

        # Act - Generate alert
        alert = await portfolio_monitor._generate_alert(
            portfolio_id=portfolio_id,
            alert_type=AlertType.DEVIATION_ALERT,
            severity=AlertSeverity.WARNING,
            title="Test Alert Lifecycle",
            message="Test alert for lifecycle testing",
            affected_positions=["AAPL"],
            current_deviations={"AAPL": 0.08},
            recommended_actions=["Test action"],
        )

        # Verify initial state
        assert not alert.acknowledged
        assert not alert.resolved

        # Act - Acknowledge alert
        ack_result = await portfolio_monitor.acknowledge_alert(portfolio_id, alert.alert_id)
        assert ack_result is True
        assert alert.acknowledged is True

        # Act - Resolve alert
        resolution_notes = "Portfolio rebalanced successfully"
        resolve_result = await portfolio_monitor.resolve_alert(portfolio_id, alert.alert_id, resolution_notes)
        assert resolve_result is True
        assert alert.resolved is True
        assert alert.resolution_notes == resolution_notes

        # Verify alert no longer appears in active alerts
        active_alerts = await portfolio_monitor.get_active_alerts(portfolio_id)
        assert len(active_alerts) == 0

    def test_should_provide_comprehensive_monitoring_statistics(self, mocker, mock_price_service):
        """Test that monitoring system provides comprehensive statistics."""
        # Arrange
        portfolio_monitor = PortfolioMonitor()
        notification_service = NotificationService()

        # Act
        monitor_stats = portfolio_monitor.get_monitoring_statistics()
        notification_stats = notification_service.get_notification_statistics()

        # Assert - Verify comprehensive statistics
        assert isinstance(monitor_stats, dict)
        assert "total_portfolios_monitored" in monitor_stats
        assert "active_monitoring_tasks" in monitor_stats
        assert "total_alerts_generated" in monitor_stats

        assert isinstance(notification_stats, dict)
        assert "total_notifications_sent" in notification_stats
        assert "success_rate" in notification_stats
        assert "registered_providers" in notification_stats
