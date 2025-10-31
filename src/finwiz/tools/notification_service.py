"""
Notification service for portfolio monitoring alerts.

This module provides email and SMS notification capabilities for portfolio
monitoring alerts and rebalancing recommendations.
"""

from __future__ import annotations

import logging
import smtplib
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from typing import Any

from bs4 import BeautifulSoup
from pydantic import BaseModel, ConfigDict, Field

from finwiz.quantitative.portfolio_monitor import AlertSeverity, PortfolioAlert

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    """Notification type enumeration."""

    EMAIL = "EMAIL"
    SMS = "SMS"
    PUSH = "PUSH"
    WEBHOOK = "WEBHOOK"


class NotificationStatus(str, Enum):
    """Notification delivery status enumeration."""

    PENDING = "PENDING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"


class NotificationPreferences(BaseModel):
    """User notification preferences."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    # Contact information
    email_address: str | None = Field(None, description="Email address for notifications")
    phone_number: str | None = Field(None, description="Phone number for SMS notifications")

    # Notification settings
    enabled_notification_types: list[NotificationType] = Field(default_factory=lambda: [NotificationType.EMAIL], description="Enabled notification types")

    # Alert level preferences
    email_alert_levels: list[AlertSeverity] = Field(
        default_factory=lambda: [AlertSeverity.WARNING, AlertSeverity.ERROR, AlertSeverity.CRITICAL],
        description="Alert severities that trigger email notifications",
    )
    sms_alert_levels: list[AlertSeverity] = Field(
        default_factory=lambda: [AlertSeverity.ERROR, AlertSeverity.CRITICAL],
        description="Alert severities that trigger SMS notifications",
    )

    # Timing preferences
    quiet_hours_start: int = Field(default=22, ge=0, le=23, description="Quiet hours start (24h format)")
    quiet_hours_end: int = Field(default=7, ge=0, le=23, description="Quiet hours end (24h format)")
    max_notifications_per_hour: int = Field(default=5, ge=1, le=100, description="Maximum notifications per hour")

    # Content preferences
    include_detailed_analysis: bool = Field(default=True, description="Include detailed analysis in notifications")
    include_recommendations: bool = Field(default=True, description="Include recommended actions")


class NotificationRecord(BaseModel):
    """Record of a sent notification."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    # Identification
    notification_id: str = Field(..., description="Unique notification identifier")
    alert_id: str = Field(..., description="Associated alert identifier")
    portfolio_id: str = Field(..., description="Portfolio identifier")

    # Notification details
    notification_type: NotificationType = Field(..., description="Type of notification")
    recipient: str = Field(..., description="Notification recipient")
    subject: str = Field(..., description="Notification subject/title")

    # Status tracking
    status: NotificationStatus = Field(..., description="Delivery status")
    sent_timestamp: datetime = Field(default_factory=datetime.now, description="When notification was sent")
    delivered_timestamp: datetime | None = Field(None, description="When notification was delivered")

    # Error tracking
    error_message: str | None = Field(None, description="Error message if delivery failed")
    retry_count: int = Field(default=0, ge=0, description="Number of retry attempts")
    max_retries: int = Field(default=3, ge=0, description="Maximum retry attempts")


class NotificationProvider(ABC):
    """Abstract base class for notification providers."""

    @abstractmethod
    async def send_notification(self, recipient: str, subject: str, message: str, alert: PortfolioAlert) -> NotificationRecord:
        """Send a notification."""
        pass

    @abstractmethod
    def validate_recipient(self, recipient: str) -> bool:
        """Validate recipient format."""
        pass


class EmailNotificationProvider(NotificationProvider):
    """Email notification provider using SMTP."""

    def __init__(
        self,
        smtp_server: str = "localhost",
        smtp_port: int = 587,
        username: str | None = None,
        password: str | None = None,
        use_tls: bool = True,
        sender_email: str = "noreply@finwiz.com",
    ) -> None:
        """Initialize email provider."""
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.sender_email = sender_email

    async def send_notification(self, recipient: str, subject: str, message: str, alert: PortfolioAlert) -> NotificationRecord:
        """Send email notification."""
        notification_id = f"email_{alert.alert_id}_{datetime.now().isoformat()}"

        try:
            # Create email message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.sender_email
            msg["To"] = recipient

            # Create HTML and text versions
            html_content = self._create_html_email(alert, message)
            text_content = self._create_text_email(alert, message)

            msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.send_message(msg)

            logger.info(f"Email notification sent to {recipient} for alert {alert.alert_id}")

            return NotificationRecord(
                notification_id=notification_id,
                alert_id=alert.alert_id,
                portfolio_id=alert.portfolio_id,
                notification_type=NotificationType.EMAIL,
                recipient=recipient,
                subject=subject,
                status=NotificationStatus.SENT,
            )

        except Exception as e:
            logger.error(f"Failed to send email notification to {recipient}: {e}")
            return NotificationRecord(
                notification_id=notification_id,
                alert_id=alert.alert_id,
                portfolio_id=alert.portfolio_id,
                notification_type=NotificationType.EMAIL,
                recipient=recipient,
                subject=subject,
                status=NotificationStatus.FAILED,
                error_message=str(e),
            )

    def validate_recipient(self, recipient: str) -> bool:
        """Validate email address format."""
        import re

        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, recipient))

    def _create_html_email(self, alert: PortfolioAlert, message: str) -> str:
        """Create HTML email content using bs4."""
        severity_colors = {
            AlertSeverity.INFO: "#17a2b8",
            AlertSeverity.WARNING: "#ffc107",
            AlertSeverity.ERROR: "#dc3545",
            AlertSeverity.CRITICAL: "#6f42c1",
        }

        color = severity_colors.get(alert.severity, "#6c757d")

        # Create soup and HTML structure
        soup = BeautifulSoup("", "html.parser")
        html = soup.new_tag("html")

        # Create head with styles
        head = soup.new_tag("head")
        style = soup.new_tag("style")
        style.string = f"""
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                .header {{ background-color: {color}; color: white; padding: 15px; border-radius: 5px; }}
                .content {{ padding: 20px; border: 1px solid #ddd; border-radius: 5px; margin-top: 10px; }}
                .positions {{ background-color: #f8f9fa; padding: 10px; border-radius: 3px; margin: 10px 0; }}
                .actions {{ background-color: #e9ecef; padding: 10px; border-radius: 3px; margin: 10px 0; }}
                .footer {{ margin-top: 20px; font-size: 12px; color: #6c757d; }}
        """
        head.append(style)

        # Create body
        body = soup.new_tag("body")

        # Create header section
        header_div = soup.new_tag("div", **{"class": "header"})
        header_h2 = soup.new_tag("h2")
        header_h2.string = f"FinWiz Portfolio Alert - {alert.severity.value}"
        header_div.append(header_h2)

        header_p = soup.new_tag("p")
        header_p.string = alert.title
        header_div.append(header_p)

        # Create content section
        content_div = soup.new_tag("div", **{"class": "content"})

        # Portfolio info
        portfolio_p = soup.new_tag("p")
        portfolio_strong = soup.new_tag("strong")
        portfolio_strong.string = "Portfolio:"
        portfolio_p.append(portfolio_strong)
        portfolio_p.append(f" {alert.portfolio_id}")
        content_div.append(portfolio_p)

        # Alert time
        time_p = soup.new_tag("p")
        time_strong = soup.new_tag("strong")
        time_strong.string = "Alert Time:"
        time_p.append(time_strong)
        time_p.append(f" {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        content_div.append(time_p)

        # Message
        message_p = soup.new_tag("p")
        message_strong = soup.new_tag("strong")
        message_strong.string = "Message:"
        message_p.append(message_strong)
        message_p.append(f" {alert.message}")
        content_div.append(message_p)

        # Add affected positions and recommended actions
        positions_html = self._format_affected_positions_html(alert)
        if positions_html:
            positions_soup = BeautifulSoup(positions_html, "html.parser")
            content_div.extend(positions_soup.contents)

        actions_html = self._format_recommended_actions_html(alert)
        if actions_html:
            actions_soup = BeautifulSoup(actions_html, "html.parser")
            content_div.extend(actions_soup.contents)

        # Create footer
        footer_div = soup.new_tag("div", **{"class": "footer"})
        footer_p1 = soup.new_tag("p")
        footer_p1.string = "This is an automated notification from FinWiz Portfolio Monitoring System."
        footer_div.append(footer_p1)

        footer_p2 = soup.new_tag("p")
        footer_p2.string = "Please do not reply to this email."
        footer_div.append(footer_p2)

        # Assemble the document
        body.append(header_div)
        body.append(content_div)
        body.append(footer_div)

        html.append(head)
        html.append(body)
        soup.append(html)

        return soup.prettify(formatter="html")

    def _create_text_email(self, alert: PortfolioAlert, message: str) -> str:
        """Create plain text email content."""
        text = f"""
FinWiz Portfolio Alert - {alert.severity.value}

{alert.title}

Portfolio: {alert.portfolio_id}
Alert Time: {alert.timestamp.strftime("%Y-%m-%d %H:%M:%S")}
Severity: {alert.severity.value}

Message:
{alert.message}

{self._format_affected_positions_text(alert)}
{self._format_recommended_actions_text(alert)}

---
This is an automated notification from FinWiz Portfolio Monitoring System.
Please do not reply to this email.
        """
        return text.strip()

    def _format_affected_positions_html(self, alert: PortfolioAlert) -> str:
        """Format affected positions for HTML email using bs4."""
        if not alert.affected_positions:
            return ""

        soup = BeautifulSoup("", "html.parser")
        positions_div = soup.new_tag("div", **{"class": "positions"})

        # Create header
        h4 = soup.new_tag("h4")
        h4.string = "Affected Positions:"
        positions_div.append(h4)

        # Create list
        ul = soup.new_tag("ul")
        for symbol in alert.affected_positions:
            deviation = alert.current_deviations.get(symbol, 0.0)

            li = soup.new_tag("li")
            strong = soup.new_tag("strong")
            strong.string = symbol
            li.append(strong)
            li.append(f": {deviation:+.1%} deviation")
            ul.append(li)

        positions_div.append(ul)
        soup.append(positions_div)

        return str(soup)

    def _format_recommended_actions_html(self, alert: PortfolioAlert) -> str:
        """Format recommended actions for HTML email using bs4."""
        if not alert.recommended_actions:
            return ""

        soup = BeautifulSoup("", "html.parser")
        actions_div = soup.new_tag("div", **{"class": "actions"})

        # Create header
        h4 = soup.new_tag("h4")
        h4.string = "Recommended Actions:"
        actions_div.append(h4)

        # Create list
        ul = soup.new_tag("ul")
        for action in alert.recommended_actions:
            li = soup.new_tag("li")
            li.string = action  # bs4 automatically escapes content
            ul.append(li)

        actions_div.append(ul)
        soup.append(actions_div)

        return str(soup)

    def _format_affected_positions_text(self, alert: PortfolioAlert) -> str:
        """Format affected positions for text email."""
        if not alert.affected_positions:
            return ""

        text = "\nAffected Positions:\n"
        for symbol in alert.affected_positions:
            deviation = alert.current_deviations.get(symbol, 0.0)
            text += f"  - {symbol}: {deviation:+.1%} deviation\n"
        return text

    def _format_recommended_actions_text(self, alert: PortfolioAlert) -> str:
        """Format recommended actions for text email."""
        if not alert.recommended_actions:
            return ""

        text = "\nRecommended Actions:\n"
        for action in alert.recommended_actions:
            text += f"  - {action}\n"
        return text


class SMSNotificationProvider(NotificationProvider):
    """SMS notification provider (mock implementation)."""

    def __init__(self, api_key: str | None = None, sender_id: str = "FinWiz") -> None:
        """Initialize SMS provider."""
        self.api_key = api_key
        self.sender_id = sender_id

    async def send_notification(self, recipient: str, subject: str, message: str, alert: PortfolioAlert) -> NotificationRecord:
        """Send SMS notification (mock implementation)."""
        notification_id = f"sms_{alert.alert_id}_{datetime.now().isoformat()}"

        try:
            # Create SMS message (keep it short)
            sms_message = self._create_sms_message(alert)

            # Mock SMS sending (in real implementation, would use SMS API)
            logger.info(f"SMS notification would be sent to {recipient}: {sms_message}")

            return NotificationRecord(
                notification_id=notification_id,
                alert_id=alert.alert_id,
                portfolio_id=alert.portfolio_id,
                notification_type=NotificationType.SMS,
                recipient=recipient,
                subject=subject,
                status=NotificationStatus.SENT,
            )

        except Exception as e:
            logger.error(f"Failed to send SMS notification to {recipient}: {e}")
            return NotificationRecord(
                notification_id=notification_id,
                alert_id=alert.alert_id,
                portfolio_id=alert.portfolio_id,
                notification_type=NotificationType.SMS,
                recipient=recipient,
                subject=subject,
                status=NotificationStatus.FAILED,
                error_message=str(e),
            )

    def validate_recipient(self, recipient: str) -> bool:
        """Validate phone number format."""
        import re

        # Simple phone number validation (international format)
        # Must be at least 7 digits, max 15 digits, can start with +
        clean_number = recipient.replace(" ", "").replace("-", "")
        pattern = r"^\+?[1-9]\d{6,14}$"
        return bool(re.match(pattern, clean_number))

    def _create_sms_message(self, alert: PortfolioAlert) -> str:
        """Create SMS message (keep under 160 characters)."""
        positions_count = len(alert.affected_positions)
        if positions_count > 0:
            return f"FinWiz Alert: {alert.title}. {positions_count} positions need attention. Check your portfolio."
        else:
            return f"FinWiz Alert: {alert.title}. Check your portfolio for details."


class NotificationService:
    """Main notification service for portfolio monitoring."""

    def __init__(self) -> None:
        """Initialize notification service."""
        self.providers: dict[NotificationType, NotificationProvider] = {}
        self.notification_history: list[NotificationRecord] = []
        self.user_preferences: dict[str, NotificationPreferences] = {}

        # Initialize default providers
        self.providers[NotificationType.EMAIL] = EmailNotificationProvider()
        self.providers[NotificationType.SMS] = SMSNotificationProvider()

        logger.info("Notification service initialized")

    def register_provider(self, notification_type: NotificationType, provider: NotificationProvider) -> None:
        """Register a notification provider."""
        self.providers[notification_type] = provider
        logger.info(f"Registered {notification_type.value} provider")

    def set_user_preferences(self, user_id: str, preferences: NotificationPreferences) -> None:
        """Set notification preferences for a user."""
        self.user_preferences[user_id] = preferences
        logger.info(f"Updated notification preferences for user {user_id}")

    async def send_alert_notification(self, alert: PortfolioAlert, user_id: str) -> list[NotificationRecord]:
        """Send notifications for a portfolio alert."""
        records = []

        try:
            # Get user preferences
            preferences = self.user_preferences.get(user_id)
            if not preferences:
                logger.warning(f"No notification preferences found for user {user_id}")
                return records

            # Check if notifications should be sent based on alert severity and user preferences
            for notification_type in preferences.enabled_notification_types:
                should_send = False

                if notification_type == NotificationType.EMAIL:
                    should_send = alert.severity in preferences.email_alert_levels
                elif notification_type == NotificationType.SMS:
                    should_send = alert.severity in preferences.sms_alert_levels

                if not should_send:
                    continue

                # Check quiet hours
                if self._is_quiet_hours(preferences):
                    logger.info(f"Skipping {notification_type.value} notification during quiet hours")
                    continue

                # Check rate limiting
                if self._is_rate_limited(user_id, preferences):
                    logger.info(f"Rate limiting {notification_type.value} notifications for user {user_id}")
                    continue

                # Get recipient
                recipient = self._get_recipient(notification_type, preferences)
                if not recipient:
                    logger.warning(f"No recipient configured for {notification_type.value} notifications")
                    continue

                # Send notification
                provider = self.providers.get(notification_type)
                if provider:
                    subject = f"FinWiz Alert: {alert.title}"
                    message = self._create_notification_message(alert, preferences)

                    record = await provider.send_notification(recipient, subject, message, alert)
                    records.append(record)
                    self.notification_history.append(record)

            # Keep notification history manageable
            self.notification_history = self.notification_history[-1000:]

        except Exception as e:
            logger.error(f"Error sending alert notifications: {e}")

        return records

    def _get_recipient(self, notification_type: NotificationType, preferences: NotificationPreferences) -> str | None:
        """Get recipient for notification type."""
        if notification_type == NotificationType.EMAIL:
            return preferences.email_address
        elif notification_type == NotificationType.SMS:
            return preferences.phone_number
        return None

    def _is_quiet_hours(self, preferences: NotificationPreferences) -> bool:
        """Check if current time is within quiet hours."""
        current_hour = datetime.now().hour
        start = preferences.quiet_hours_start
        end = preferences.quiet_hours_end

        if start <= end:
            return start <= current_hour <= end
        else:  # Quiet hours span midnight
            return current_hour >= start or current_hour <= end

    def _is_rate_limited(self, user_id: str, preferences: NotificationPreferences) -> bool:
        """Check if user has exceeded notification rate limit."""
        # Count notifications sent in the last hour
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_notifications = [record for record in self.notification_history if record.portfolio_id.startswith(user_id) and record.sent_timestamp >= one_hour_ago]

        return len(recent_notifications) >= preferences.max_notifications_per_hour

    def _create_notification_message(self, alert: PortfolioAlert, preferences: NotificationPreferences) -> str:
        """Create notification message based on user preferences."""
        message = alert.message

        if preferences.include_detailed_analysis and alert.affected_positions:
            message += f"\n\nAffected positions: {', '.join(alert.affected_positions)}"

            # Add deviation details
            if alert.current_deviations:
                message += "\nCurrent deviations:"
                for symbol, deviation in alert.current_deviations.items():
                    message += f"\n  {symbol}: {deviation:+.1%}"

        if preferences.include_recommendations and alert.recommended_actions:
            message += "\n\nRecommended actions:"
            for action in alert.recommended_actions:
                message += f"\n  • {action}"

        return message

    def get_notification_history(self, portfolio_id: str | None = None, hours: int = 24) -> list[NotificationRecord]:
        """Get notification history."""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        filtered_records = [record for record in self.notification_history if record.sent_timestamp >= cutoff_time]

        if portfolio_id:
            filtered_records = [record for record in filtered_records if record.portfolio_id == portfolio_id]

        return filtered_records

    def get_notification_statistics(self) -> dict[str, Any]:
        """Get notification system statistics."""
        total_notifications = len(self.notification_history)
        successful_notifications = len([r for r in self.notification_history if r.status == NotificationStatus.SENT])
        failed_notifications = len([r for r in self.notification_history if r.status == NotificationStatus.FAILED])

        return {
            "total_notifications_sent": total_notifications,
            "successful_notifications": successful_notifications,
            "failed_notifications": failed_notifications,
            "success_rate": successful_notifications / total_notifications if total_notifications > 0 else 0.0,
            "registered_providers": list(self.providers.keys()),
            "active_user_preferences": len(self.user_preferences),
        }
