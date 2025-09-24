# Portfolio Monitoring and Alerting System

## Overview

The Portfolio Monitoring and Alerting System provides comprehensive real-time monitoring capabilities for portfolio drift detection, alert generation, and multi-channel notifications. This system integrates seamlessly with the existing FinWiz portfolio rebalancing infrastructure.

## Key Components

### 1. Portfolio Monitor (`src/finwiz/quantitative/portfolio_monitor.py`)

The core monitoring engine that provides:

- **Continuous Drift Monitoring**: Real-time tracking of portfolio positions against target allocations
- **Health Dashboard**: Comprehensive portfolio health scoring and visualization
- **Alert Generation**: Intelligent alert creation based on configurable rules
- **Alert Management**: Full lifecycle management including acknowledgment and resolution

#### Key Features:
- Configurable monitoring rules with customizable thresholds
- Multiple urgency levels (LOW, MEDIUM, HIGH, CRITICAL)
- Portfolio health scoring (1-10 scale)
- Automated monitoring loops with error recovery
- Comprehensive statistics and reporting

### 2. Notification Service (`src/finwiz/tools/notification_service.py`)

Multi-channel notification system supporting:

- **Email Notifications**: HTML and plain text email alerts via SMTP
- **SMS Notifications**: Text message alerts for critical issues
- **User Preferences**: Granular control over notification settings
- **Rate Limiting**: Prevents notification spam
- **Quiet Hours**: Respects user-defined quiet periods

#### Key Features:
- Multiple notification providers (Email, SMS, extensible for others)
- Rich HTML email templates with portfolio details
- User preference management (alert levels, timing, content)
- Delivery tracking and error handling
- Comprehensive notification statistics

### 3. Data Models and Schemas

Comprehensive Pydantic models for:

- **MonitoringRule**: Configuration for automated monitoring
- **PortfolioAlert**: Alert data structure with full context
- **NotificationPreferences**: User notification settings
- **PortfolioHealthDashboard**: Health metrics and status
- **MonitoringStatus**: Real-time monitoring state

## Configuration

### Monitoring Rules

```python
monitoring_rule = MonitoringRule(
    rule_id="portfolio_monitor",
    rule_name="Standard Portfolio Monitoring",
    max_deviation_threshold=0.08,  # 8% threshold
    min_check_interval_hours=1,
    alert_on_deviation=True,
    alert_on_multiple_positions=True,
    min_positions_for_alert=2,
    enable_auto_rebalancing=False
)
```

### Notification Preferences

```python
preferences = NotificationPreferences(
    email_address="user@example.com",
    phone_number="+1234567890",
    enabled_notification_types=[NotificationType.EMAIL, NotificationType.SMS],
    email_alert_levels=[AlertSeverity.WARNING, AlertSeverity.ERROR, AlertSeverity.CRITICAL],
    sms_alert_levels=[AlertSeverity.ERROR, AlertSeverity.CRITICAL],
    quiet_hours_start=22,
    quiet_hours_end=7,
    max_notifications_per_hour=5
)
```

## Usage Examples

### Basic Monitoring Setup

```python
from finwiz.quantitative.portfolio_monitor import PortfolioMonitor, MonitoringRule
from finwiz.tools.notification_service import NotificationService

# Initialize services
monitor = PortfolioMonitor()
notification_service = NotificationService()

# Start monitoring
await monitor.start_monitoring(portfolio_id, portfolio_config, monitoring_rule)

# Check portfolio drift
rebalancing_needs = await monitor.check_portfolio_drift(portfolio_id, portfolio_config)

# Generate health dashboard
dashboard = await monitor.generate_health_dashboard(portfolio_id, portfolio_config)
```

### Alert Management

```python
# Get active alerts
active_alerts = await monitor.get_active_alerts(portfolio_id)

# Acknowledge alert
await monitor.acknowledge_alert(portfolio_id, alert_id)

# Resolve alert
await monitor.resolve_alert(portfolio_id, alert_id, "Issue resolved")
```

### Notification Sending

```python
# Set user preferences
notification_service.set_user_preferences(user_id, preferences)

# Send alert notification
records = await notification_service.send_alert_notification(alert, user_id)
```

## Alert Types and Severity Levels

### Alert Types
- **DEVIATION_ALERT**: Position exceeds tolerance threshold
- **MULTIPLE_POSITIONS_ALERT**: Multiple positions need rebalancing
- **AUTO_REBALANCE_TRIGGERED**: Automated rebalancing recommended
- **MONITORING_ERROR**: System monitoring errors
- **PRICE_DATA_STALE**: Price data is outdated

### Severity Levels
- **INFO**: Informational messages
- **WARNING**: Minor issues requiring attention
- **ERROR**: Significant problems needing action
- **CRITICAL**: Urgent issues requiring immediate attention

## Health Dashboard Metrics

The portfolio health dashboard provides:

- **Overall Health Score**: 1-10 scale based on deviations and risk
- **Health Status**: Descriptive status (Excellent, Good, Fair, Poor, Critical)
- **Deviation Analysis**: Maximum and average position deviations
- **Rebalancing Urgency**: Urgency level for rebalancing actions
- **Cost Estimates**: Estimated costs for recommended rebalancing
- **Monitoring Status**: Current system monitoring state

## Integration Points

### With Existing FinWiz Components
- **Portfolio Analyzer**: Uses existing analysis capabilities
- **Price Service**: Leverages existing price data infrastructure
- **Rebalancing Engine**: Integrates with optimization algorithms
- **HTML Reports**: Extends existing report generation framework

### External Integrations
- **SMTP Servers**: For email notifications
- **SMS APIs**: For text message alerts (Twilio, AWS SNS, etc.)
- **Webhooks**: For custom notification endpoints
- **Monitoring Systems**: For system health tracking

## Testing

Comprehensive test suite includes:

### Unit Tests
- Portfolio monitor functionality
- Notification service operations
- Data model validation
- Alert generation and management

### Integration Tests
- Complete monitoring workflow
- Multi-channel notification delivery
- Error handling and recovery
- Rate limiting and quiet hours

### Performance Tests
- Large portfolio monitoring
- High-frequency alert generation
- Notification delivery at scale

## Security Considerations

- **API Key Management**: Secure storage of notification service credentials
- **Data Privacy**: No sensitive portfolio data in logs
- **Rate Limiting**: Prevents abuse and spam
- **Input Validation**: Strict validation of all inputs
- **Error Handling**: Graceful degradation without data exposure

## Deployment

### Environment Variables
```bash
# Email configuration
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=notifications@example.com
SMTP_PASSWORD=secure_password

# SMS configuration (if using Twilio)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
```

### Production Considerations
- Configure proper SMTP server for email delivery
- Set up SMS provider (Twilio, AWS SNS, etc.)
- Implement proper logging and monitoring
- Configure appropriate rate limits and thresholds
- Set up database for persistent alert storage
- Implement proper backup and recovery procedures

## Future Enhancements

### Planned Features
- **Push Notifications**: Mobile app notifications
- **Webhook Integration**: Custom notification endpoints
- **Advanced Analytics**: Machine learning for optimal thresholds
- **Multi-Portfolio Monitoring**: Enterprise-scale monitoring
- **Custom Alert Rules**: User-defined alert conditions
- **Integration APIs**: Third-party system integration

### Scalability Improvements
- **Database Storage**: Persistent alert and notification history
- **Message Queues**: Asynchronous notification processing
- **Microservices**: Separate monitoring and notification services
- **Load Balancing**: Distributed monitoring capabilities
- **Caching**: Enhanced performance for large portfolios

## Conclusion

The Portfolio Monitoring and Alerting System provides a robust, scalable foundation for real-time portfolio management. With comprehensive monitoring capabilities, intelligent alerting, and flexible notification options, it enables proactive portfolio management and helps users maintain optimal asset allocations.

The system is designed to integrate seamlessly with existing FinWiz infrastructure while providing extensibility for future enhancements and third-party integrations.