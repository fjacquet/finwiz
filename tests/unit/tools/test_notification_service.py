"""
Unit tests for notification service.

Tests cover email/SMS notifications, user preferences, and notification delivery.
"""

from datetime import datetime, timedelta

import pytest
from pytest import approx

from finwiz.quantitative.portfolio_monitor import AlertSeverity, AlertType, PortfolioAlert
from finwiz.tools.notification_service import (
    EmailNotificationProvider,
    NotificationPreferences,
    NotificationRecord,
    NotificationService,
    NotificationStatus,
    NotificationType,
    SMSNotificationProvider,
)


class TestNotificationPreferences:
    """Test cases for NotificationPreferences class."""

    def test_should_create_notification_preferences_when_valid_data_provided(self):
        """Test notification preferences creation with valid data."""
        # Arrange & Act
        preferences = NotificationPreferences(
            email_address="test@example.com",
            phone_number="+1234567890",
            enabled_notification_types=[NotificationType.EMAIL, NotificationType.SMS],
            email_alert_levels=[AlertSeverity.WARNING, AlertSeverity.ERROR],
            sms_alert_levels=[AlertSeverity.CRITICAL],
            quiet_hours_start=22,
            quiet_hours_end=7,
            max_notifications_per_hour=3,
            include_detailed_analysis=True,
            include_recommendations=False,
        )

        # Assert
        assert preferences.email_address == "test@example.com"
        assert preferences.phone_number == "+1234567890"
        assert preferences.enabled_notification_types == [NotificationType.EMAIL, NotificationType.SMS]
        assert preferences.email_alert_levels == [AlertSeverity.WARNING, AlertSeverity.ERROR]
        assert preferences.sms_alert_levels == [AlertSeverity.CRITICAL]
        assert preferences.quiet_hours_start == 22
        assert preferences.quiet_hours_end == 7
        assert preferences.max_notifications_per_hour == 3
        assert preferences.include_detailed_analysis is True
        assert preferences.include_recommendations is False

    def test_should_use_default_values_when_not_specified(self):
        """Test notification preferences creation with default values."""
        # Arrange & Act
        preferences = NotificationPreferences()

        # Assert
        assert preferences.email_address is None
        assert preferences.phone_number is None
        assert preferences.enabled_notification_types == [NotificationType.EMAIL]
        assert AlertSeverity.WARNING in preferences.email_alert_levels
        assert AlertSeverity.ERROR in preferences.email_alert_levels
        assert AlertSeverity.CRITICAL in preferences.email_alert_levels
        assert AlertSeverity.ERROR in preferences.sms_alert_levels
        assert AlertSeverity.CRITICAL in preferences.sms_alert_levels
        assert preferences.quiet_hours_start == 22
        assert preferences.quiet_hours_end == 7
        assert preferences.max_notifications_per_hour == 5
        assert preferences.include_detailed_analysis is True
        assert preferences.include_recommendations is True

    def test_should_raise_validation_error_when_invalid_quiet_hours_provided(self):
        """Test notification preferences validation with invalid quiet hours."""
        # Arrange & Act & Assert
        with pytest.raises(ValueError):
            NotificationPreferences(quiet_hours_start=25)  # Invalid: > 23

        with pytest.raises(ValueError):
            NotificationPreferences(quiet_hours_end=-1)  # Invalid: < 0


class TestEmailNotificationProvider:
    """Test cases for EmailNotificationProvider class."""

    @pytest.fixture
    def email_provider(self):
        """Email notification provider instance."""
        return EmailNotificationProvider(
            smtp_server="localhost",
            smtp_port=587,
            username="test@example.com",
            password="password",
            sender_email="noreply@finwiz.com",
        )

    @pytest.fixture
    def sample_alert(self):
        """Sample portfolio alert."""
        return PortfolioAlert(
            alert_id="test_alert_123",
            portfolio_id="test_portfolio",
            alert_type=AlertType.DEVIATION_ALERT,
            severity=AlertSeverity.WARNING,
            title="Portfolio Deviation Alert",
            message="Portfolio has positions exceeding tolerance bands",
            affected_positions=["AAPL", "GOOGL"],
            current_deviations={"AAPL": 0.08, "GOOGL": -0.06},
            recommended_actions=["Review portfolio", "Consider rebalancing"],
        )

    def test_should_validate_correct_email_address(self, email_provider):
        """Test email address validation with correct format."""
        # Arrange
        valid_emails = ["test@example.com", "user.name@domain.co.uk", "user+tag@example.org"]

        # Act & Assert
        for email in valid_emails:
            assert email_provider.validate_recipient(email) is True

    def test_should_not_validate_incorrect_email_address(self, email_provider, mocker):
        """Test email address validation with incorrect format."""
        # Arrange
        invalid_emails = ["invalid-email", "@example.com", "user@", "user@domain", ""]

        # Act & Assert
        for email in invalid_emails:
            assert email_provider.validate_recipient(email) is False

    @pytest.mark.asyncio
    async def test_should_send_email_notification_when_valid_data_provided(self, mocker, email_provider, sample_alert):
        """Test email notification sending with valid data."""
        # Arrange
        recipient = "test@example.com"
        subject = "Test Alert"
        message = "Test message"

        mock_server = mocker.MagicMock()
        mock_smtp_context = mocker.MagicMock()
        mock_smtp_context.__enter__ = mocker.MagicMock(return_value=mock_server)
        mock_smtp_context.__exit__ = mocker.MagicMock(return_value=None)

        mock_smtp = mocker.patch("smtplib.SMTP")
        mock_smtp.return_value = mock_smtp_context

        # Act
        record = await email_provider.send_notification(recipient, subject, message, sample_alert)

        # Assert
        assert isinstance(record, NotificationRecord)
        assert record.notification_type == NotificationType.EMAIL
        assert record.recipient == recipient
        assert record.subject == subject
        assert record.status == NotificationStatus.SENT
        assert record.error_message is None

        # Verify SMTP calls
        mock_server.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_handle_email_sending_failure(self, mocker, email_provider, sample_alert):
        """Test email notification handling when sending fails."""
        # Arrange
        recipient = "test@example.com"
        subject = "Test Alert"
        message = "Test message"

        mock_smtp = mocker.patch("smtplib.SMTP")
        mock_smtp.side_effect = Exception("SMTP connection failed")

        # Act
        record = await email_provider.send_notification(recipient, subject, message, sample_alert)

        # Assert
        assert record.status == NotificationStatus.FAILED
        assert record.error_message == "SMTP connection failed"

    def test_should_create_html_email_content(self, email_provider, sample_alert):
        """Test HTML email content creation."""
        # Arrange
        message = "Test message"

        # Act
        html_content = email_provider._create_html_email(sample_alert, message)

        # Assert
        assert isinstance(html_content, str)
        assert "FinWiz Portfolio Alert" in html_content
        assert sample_alert.title in html_content
        assert sample_alert.portfolio_id in html_content
        assert "AAPL" in html_content
        assert "GOOGL" in html_content

    def test_should_create_text_email_content(self, email_provider, sample_alert):
        """Test plain text email content creation."""
        # Arrange
        message = "Test message"

        # Act
        text_content = email_provider._create_text_email(sample_alert, message)

        # Assert
        assert isinstance(text_content, str)
        assert "FinWiz Portfolio Alert" in text_content
        assert sample_alert.title in text_content
        assert sample_alert.portfolio_id in text_content
        assert "AAPL" in text_content
        assert "GOOGL" in text_content


class TestSMSNotificationProvider:
    """Test cases for SMSNotificationProvider class."""

    @pytest.fixture
    def sms_provider(self):
        """SMS notification provider instance."""
        return SMSNotificationProvider(api_key="test_api_key", sender_id="FinWiz")

    @pytest.fixture
    def sample_alert(self):
        """Sample portfolio alert."""
        return PortfolioAlert(
            alert_id="test_alert_123",
            portfolio_id="test_portfolio",
            alert_type=AlertType.DEVIATION_ALERT,
            severity=AlertSeverity.WARNING,
            title="Portfolio Deviation Alert",
            message="Portfolio has positions exceeding tolerance bands",
            affected_positions=["AAPL", "GOOGL"],
            current_deviations={"AAPL": 0.08, "GOOGL": -0.06},
            recommended_actions=["Review portfolio", "Consider rebalancing"],
        )

    def test_should_validate_correct_phone_number(self, sms_provider):
        """Test phone number validation with correct format."""
        # Arrange
        valid_numbers = ["+1234567890", "+44123456789", "1234567890", "+12345678901234"]

        # Act & Assert
        for number in valid_numbers:
            assert sms_provider.validate_recipient(number) is True

    def test_should_not_validate_incorrect_phone_number(self, sms_provider):
        """Test phone number validation with incorrect format."""
        # Arrange
        invalid_numbers = [
            "123",
            "+0123456789",  # Starts with 0 after country code
            "abc123456789",
            "",
            "+123456789012345678",  # Too long
        ]

        # Act & Assert
        for number in invalid_numbers:
            assert sms_provider.validate_recipient(number) is False

    @pytest.mark.asyncio
    async def test_should_send_sms_notification_when_valid_data_provided(self, sms_provider, sample_alert):
        """Test SMS notification sending with valid data."""
        # Arrange
        recipient = "+1234567890"
        subject = "Test Alert"
        message = "Test message"

        # Act
        record = await sms_provider.send_notification(recipient, subject, message, sample_alert)

        # Assert
        assert isinstance(record, NotificationRecord)
        assert record.notification_type == NotificationType.SMS
        assert record.recipient == recipient
        assert record.subject == subject
        assert record.status == NotificationStatus.SENT
        assert record.error_message is None

    def test_should_create_short_sms_message(self, sms_provider, sample_alert):
        """Test SMS message creation keeps message short."""
        # Act
        sms_message = sms_provider._create_sms_message(sample_alert)

        # Assert
        assert isinstance(sms_message, str)
        assert len(sms_message) <= 160  # Standard SMS length
        assert "FinWiz Alert" in sms_message
        assert "2 positions" in sms_message  # Number of affected positions


class TestNotificationService:
    """Test cases for NotificationService class."""

    @pytest.fixture
    def notification_service(self):
        """Notification service instance."""
        return NotificationService()

    @pytest.fixture
    def sample_alert(self):
        """Sample portfolio alert."""
        return PortfolioAlert(
            alert_id="test_alert_123",
            portfolio_id="test_portfolio",
            alert_type=AlertType.DEVIATION_ALERT,
            severity=AlertSeverity.WARNING,
            title="Portfolio Deviation Alert",
            message="Portfolio has positions exceeding tolerance bands",
            affected_positions=["AAPL", "GOOGL"],
            current_deviations={"AAPL": 0.08, "GOOGL": -0.06},
            recommended_actions=["Review portfolio", "Consider rebalancing"],
        )

    @pytest.fixture
    def sample_preferences(self):
        """Sample notification preferences."""
        return NotificationPreferences(
            email_address="test@example.com",
            phone_number="+1234567890",
            enabled_notification_types=[NotificationType.EMAIL, NotificationType.SMS],
            email_alert_levels=[AlertSeverity.WARNING, AlertSeverity.ERROR, AlertSeverity.CRITICAL],
            sms_alert_levels=[AlertSeverity.ERROR, AlertSeverity.CRITICAL],
            quiet_hours_start=22,
            quiet_hours_end=7,
            max_notifications_per_hour=5,
        )

    def test_should_initialize_notification_service_when_created(self, notification_service):
        """Test notification service initialization."""
        # Assert
        assert notification_service is not None
        assert NotificationType.EMAIL in notification_service.providers
        assert NotificationType.SMS in notification_service.providers
        assert notification_service.notification_history == []
        assert notification_service.user_preferences == {}

    def test_should_register_provider_when_called(self, mocker, notification_service):
        """Test provider registration."""
        # Arrange
        mock_provider = mocker.MagicMock()

        # Act
        notification_service.register_provider(NotificationType.EMAIL, mock_provider)

        # Assert
        assert notification_service.providers[NotificationType.EMAIL] == mock_provider

    def test_should_set_user_preferences_when_called(self, notification_service, sample_preferences, mocker):
        """Test user preferences setting."""
        # Arrange
        user_id = "test_user"

        # Act
        notification_service.set_user_preferences(user_id, sample_preferences)

        # Assert
        assert notification_service.user_preferences[user_id] == sample_preferences

    @pytest.mark.asyncio
    async def test_should_send_email_notification_when_preferences_allow(self, notification_service, sample_alert, sample_preferences, mocker):
        """Test sending email notification when preferences allow."""
        # Arrange
        user_id = "test_user"
        notification_service.set_user_preferences(user_id, sample_preferences)

        # Ensure test is not blocked by quiet hours (CI runs at 06:xx UTC which is within 22-7)
        mocker.patch.object(notification_service, "_is_quiet_hours", return_value=False)

        # Mock email provider
        mock_email_provider = mocker.AsyncMock()
        mock_record = NotificationRecord(
            notification_id="test_notification",
            alert_id=sample_alert.alert_id,
            portfolio_id=sample_alert.portfolio_id,
            notification_type=NotificationType.EMAIL,
            recipient="test@example.com",
            subject="Test Alert",
            status=NotificationStatus.SENT,
        )
        mock_email_provider.send_notification.return_value = mock_record
        notification_service.providers[NotificationType.EMAIL] = mock_email_provider

        # Act
        records = await notification_service.send_alert_notification(sample_alert, user_id)

        # Assert
        assert len(records) == 1  # Only email should be sent (SMS requires ERROR+ severity)
        assert records[0].notification_type == NotificationType.EMAIL
        mock_email_provider.send_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_send_both_notifications_when_alert_severity_high(self, notification_service, sample_preferences, mocker):
        """Test sending both email and SMS when alert severity is high enough."""
        # Arrange
        user_id = "test_user"
        notification_service.set_user_preferences(user_id, sample_preferences)

        # Create high severity alert
        high_severity_alert = PortfolioAlert(
            alert_id="test_alert_456",
            portfolio_id="test_portfolio",
            alert_type=AlertType.DEVIATION_ALERT,
            severity=AlertSeverity.ERROR,  # High enough for both email and SMS
            title="Critical Portfolio Alert",
            message="Critical portfolio deviation detected",
        )

        # Ensure test is not blocked by quiet hours (CI runs at 06:xx UTC which is within 22-7)
        mocker.patch.object(notification_service, "_is_quiet_hours", return_value=False)

        # Mock providers
        mock_email_provider = mocker.AsyncMock()
        mock_sms_provider = mocker.AsyncMock()

        mock_email_record = NotificationRecord(
            notification_id="email_notification",
            alert_id=high_severity_alert.alert_id,
            portfolio_id=high_severity_alert.portfolio_id,
            notification_type=NotificationType.EMAIL,
            recipient="test@example.com",
            subject="Test Alert",
            status=NotificationStatus.SENT,
        )

        mock_sms_record = NotificationRecord(
            notification_id="sms_notification",
            alert_id=high_severity_alert.alert_id,
            portfolio_id=high_severity_alert.portfolio_id,
            notification_type=NotificationType.SMS,
            recipient="+1234567890",
            subject="Test Alert",
            status=NotificationStatus.SENT,
        )

        mock_email_provider.send_notification.return_value = mock_email_record
        mock_sms_provider.send_notification.return_value = mock_sms_record

        notification_service.providers[NotificationType.EMAIL] = mock_email_provider
        notification_service.providers[NotificationType.SMS] = mock_sms_provider

        # Act
        records = await notification_service.send_alert_notification(high_severity_alert, user_id)

        # Assert
        assert len(records) == 2  # Both email and SMS should be sent
        notification_types = [record.notification_type for record in records]
        assert NotificationType.EMAIL in notification_types
        assert NotificationType.SMS in notification_types

    @pytest.mark.asyncio
    async def test_should_not_send_notification_when_no_preferences(self, notification_service, sample_alert):
        """Test not sending notification when no user preferences exist."""
        # Arrange
        user_id = "unknown_user"

        # Act
        records = await notification_service.send_alert_notification(sample_alert, user_id)

        # Assert
        assert len(records) == 0

    def test_should_detect_quiet_hours_correctly(self, mocker, notification_service):
        """Test quiet hours detection."""
        # Arrange
        preferences = NotificationPreferences(quiet_hours_start=22, quiet_hours_end=7)

        # Mock current time to be in quiet hours (11 PM)
        mock_now_quiet = mocker.Mock()
        mock_now_quiet.hour = 23
        mock_datetime_quiet = mocker.patch("finwiz.tools.notification_service.datetime")
        mock_datetime_quiet.now.return_value = mock_now_quiet

        # Act
        is_quiet = notification_service._is_quiet_hours(preferences)

        # Assert
        assert is_quiet is True

        # Mock current time to be outside quiet hours (10 AM)
        mock_now_active = mocker.Mock()
        mock_now_active.hour = 10
        mock_datetime_active = mocker.patch("finwiz.tools.notification_service.datetime")
        mock_datetime_active.now.return_value = mock_now_active

        # Act
        is_quiet = notification_service._is_quiet_hours(preferences)

        # Assert
        assert is_quiet is False

    def test_should_detect_rate_limiting_correctly(self, notification_service, sample_preferences):
        """Test rate limiting detection."""
        # Arrange
        user_id = "test_user"

        # Add multiple recent notifications to history
        recent_time = datetime.now() - timedelta(minutes=30)
        for i in range(6):  # Exceed the limit of 5
            record = NotificationRecord(
                notification_id=f"notification_{i}",
                alert_id=f"alert_{i}",
                portfolio_id=f"{user_id}_portfolio",
                notification_type=NotificationType.EMAIL,
                recipient="test@example.com",
                subject="Test Alert",
                status=NotificationStatus.SENT,
                sent_timestamp=recent_time,
            )
            notification_service.notification_history.append(record)

        # Act
        is_rate_limited = notification_service._is_rate_limited(user_id, sample_preferences)

        # Assert
        assert is_rate_limited is True

    def test_should_create_notification_message_with_details(self, notification_service, sample_alert, sample_preferences):
        """Test notification message creation with detailed analysis."""
        # Act
        message = notification_service._create_notification_message(sample_alert, sample_preferences)

        # Assert
        assert sample_alert.message in message
        assert "AAPL" in message
        assert "GOOGL" in message
        assert "+8.0%" in message  # AAPL deviation
        assert "-6.0%" in message  # GOOGL deviation
        assert "Review portfolio" in message
        assert "Consider rebalancing" in message

    def test_should_create_notification_message_without_details(self, notification_service, sample_alert):
        """Test notification message creation without detailed analysis."""
        # Arrange
        preferences = NotificationPreferences(include_detailed_analysis=False, include_recommendations=False)

        # Act
        message = notification_service._create_notification_message(sample_alert, preferences)

        # Assert
        assert message == sample_alert.message
        assert "AAPL" not in message
        assert "Review portfolio" not in message

    def test_should_get_notification_history_when_requested(self, notification_service):
        """Test getting notification history."""
        # Arrange
        portfolio_id = "test_portfolio"

        # Add notifications to history
        recent_record = NotificationRecord(
            notification_id="recent_notification",
            alert_id="recent_alert",
            portfolio_id=portfolio_id,
            notification_type=NotificationType.EMAIL,
            recipient="test@example.com",
            subject="Recent Alert",
            status=NotificationStatus.SENT,
            sent_timestamp=datetime.now() - timedelta(hours=1),
        )

        old_record = NotificationRecord(
            notification_id="old_notification",
            alert_id="old_alert",
            portfolio_id=portfolio_id,
            notification_type=NotificationType.EMAIL,
            recipient="test@example.com",
            subject="Old Alert",
            status=NotificationStatus.SENT,
            sent_timestamp=datetime.now() - timedelta(hours=25),
        )

        notification_service.notification_history.extend([recent_record, old_record])

        # Act
        history = notification_service.get_notification_history(portfolio_id, hours=24)

        # Assert
        assert len(history) == 1  # Only recent record should be returned
        assert history[0] == recent_record

    def test_should_get_notification_statistics_when_requested(self, notification_service):
        """Test getting notification statistics."""
        # Arrange
        # Add some notifications to history
        successful_record = NotificationRecord(
            notification_id="success_notification",
            alert_id="success_alert",
            portfolio_id="test_portfolio",
            notification_type=NotificationType.EMAIL,
            recipient="test@example.com",
            subject="Success Alert",
            status=NotificationStatus.SENT,
        )

        failed_record = NotificationRecord(
            notification_id="failed_notification",
            alert_id="failed_alert",
            portfolio_id="test_portfolio",
            notification_type=NotificationType.EMAIL,
            recipient="test@example.com",
            subject="Failed Alert",
            status=NotificationStatus.FAILED,
        )

        notification_service.notification_history.extend([successful_record, failed_record])

        # Act
        stats = notification_service.get_notification_statistics()

        # Assert
        assert isinstance(stats, dict)
        assert stats["total_notifications_sent"] == 2
        assert stats["successful_notifications"] == 1
        assert stats["failed_notifications"] == 1
        assert stats["success_rate"] == approx(0.5)
        assert NotificationType.EMAIL in stats["registered_providers"]
        assert NotificationType.SMS in stats["registered_providers"]
