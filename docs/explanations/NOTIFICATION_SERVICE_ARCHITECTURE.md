# Notification Service Architecture

**Status**: All tests passing (25/25) ✅
**Fixed**: 2025-11-16
**Test File**: `tests/unit/tools/test_notification_service.py`
**Implementation**: `src/finwiz/tools/notification_service.py`

## Overview

The NotificationService provides email and SMS notification capabilities for portfolio monitoring alerts and rebalancing recommendations. It implements a clean provider pattern with support for user preferences, quiet hours, and rate limiting.

## Architecture Components

### 1. Core Classes

#### `NotificationService`
Main service orchestrating notifications with the following responsibilities:
- Provider registration and management
- User preference storage
- Alert notification dispatching
- Quiet hours detection (`_is_quiet_hours`)
- Rate limiting enforcement (`_is_rate_limited`)
- Notification message formatting (`_create_notification_message`)
- History tracking and statistics

**Key Methods**:
```python
async def send_alert_notification(alert: PortfolioAlert, user_id: str) -> list[NotificationRecord]
def _is_quiet_hours(preferences: NotificationPreferences) -> bool
def _is_rate_limited(user_id: str, preferences: NotificationPreferences) -> bool
def _create_notification_message(alert: PortfolioAlert, preferences: NotificationPreferences) -> str
def get_notification_history(portfolio_id: str | None = None, hours: int = 24) -> list[NotificationRecord]
def get_notification_statistics() -> dict[str, Any]
```

### 2. Notification Providers (Strategy Pattern)

#### `NotificationProvider` (ABC)
Abstract base class defining the provider interface:
- `async send_notification()` - Send notification
- `validate_recipient()` - Validate recipient format

#### `EmailNotificationProvider`
SMTP-based email notification provider:
- HTML and plain text email generation using BeautifulSoup
- SMTP connection management
- Email address validation (regex-based)
- Formatted email content with alert details, affected positions, and recommended actions

**HTML Email Features**:
- Severity-based color coding
- Responsive design with styled sections
- Formatted position deviations
- Recommended action lists

#### `SMSNotificationProvider`
SMS notification provider (mock implementation):
- Phone number validation (international format)
- SMS message formatting (≤160 characters)
- Concise alert summaries

### 3. Data Models (Pydantic)

#### `NotificationPreferences`
User notification preferences:
```python
class NotificationPreferences(BaseModel):
    # Contact information
    email_address: str | None
    phone_number: str | None

    # Notification settings
    enabled_notification_types: list[NotificationType]
    email_alert_levels: list[AlertSeverity]
    sms_alert_levels: list[AlertSeverity]

    # Timing preferences
    quiet_hours_start: int = 22  # 24h format
    quiet_hours_end: int = 7
    max_notifications_per_hour: int = 5

    # Content preferences
    include_detailed_analysis: bool = True
    include_recommendations: bool = True
```

#### `NotificationRecord`
Record of sent notification:
```python
class NotificationRecord(BaseModel):
    notification_id: str
    alert_id: str
    portfolio_id: str
    notification_type: NotificationType
    recipient: str
    subject: str
    status: NotificationStatus
    sent_timestamp: datetime
    delivered_timestamp: datetime | None
    error_message: str | None
    retry_count: int = 0
    max_retries: int = 3
```

### 4. Enums

#### `NotificationType`
- `EMAIL` - Email notifications
- `SMS` - SMS notifications
- `PUSH` - Push notifications (future)
- `WEBHOOK` - Webhook notifications (future)

#### `NotificationStatus`
- `PENDING` - Notification queued
- `SENT` - Notification sent
- `DELIVERED` - Notification delivered
- `FAILED` - Notification failed
- `RETRYING` - Retry in progress

## Key Features

### 1. Quiet Hours Detection
**Implementation**: `NotificationService._is_quiet_hours()`

Respects user-defined quiet hours with support for midnight-spanning periods:
```python
def _is_quiet_hours(self, preferences: NotificationPreferences) -> bool:
    current_hour = datetime.now().hour
    start = preferences.quiet_hours_start
    end = preferences.quiet_hours_end

    if start <= end:
        return start <= current_hour <= end
    else:  # Quiet hours span midnight (e.g., 22:00 - 07:00)
        return current_hour >= start or current_hour <= end
```

### 2. Rate Limiting
**Implementation**: `NotificationService._is_rate_limited()`

Prevents notification spam by enforcing per-hour limits:
```python
def _is_rate_limited(self, user_id: str, preferences: NotificationPreferences) -> bool:
    one_hour_ago = datetime.now() - timedelta(hours=1)
    recent_notifications = [
        record for record in self.notification_history
        if record.portfolio_id.startswith(user_id)
        and record.sent_timestamp >= one_hour_ago
    ]
    return len(recent_notifications) >= preferences.max_notifications_per_hour
```

### 3. Alert Severity Filtering
Different notification types can have different severity thresholds:
- **Email**: Default to WARNING, ERROR, CRITICAL
- **SMS**: Default to ERROR, CRITICAL (more urgent only)

### 4. Message Formatting
**Implementation**: `NotificationService._create_notification_message()`

Customizable message content based on user preferences:
- Base alert message (always included)
- Affected positions list (if `include_detailed_analysis=True`)
- Deviation percentages (if available)
- Recommended actions (if `include_recommendations=True`)

## Test Fix Applied

### Problem
The `test_should_detect_quiet_hours_correctly` test was failing with:
```
AttributeError: 'NoneType' object has no attribute 'now'
```

### Root Cause
Incorrect mock configuration when patching `datetime` with pytest-mock:
```python
# ❌ WRONG - mocker.patch() returns the mock, not None
with mocker.patch("finwiz.tools.notification_service.datetime") as mock_datetime:
    mock_datetime.now.return_value.hour = 23  # Fails: mock_datetime is Mock, but return_value not configured
```

### Solution
Properly configure the mock datetime object with `now()` method returning a mock with `hour` attribute:
```python
# ✅ CORRECT - Configure mock return value first
mock_now_quiet = mocker.Mock()
mock_now_quiet.hour = 23
mock_datetime_quiet = mocker.patch("finwiz.tools.notification_service.datetime")
mock_datetime_quiet.now.return_value = mock_now_quiet
```

### Changes Made
**File**: `tests/unit/tools/test_notification_service.py`
- Fixed `test_should_detect_quiet_hours_correctly` to properly mock `datetime.now()`
- Created separate mock objects for quiet hours (23:00) and active hours (10:00)
- Removed unnecessary `with` context manager (pytest-mock auto-cleans up)

## Testing Strategy

### Test Coverage (25 tests)

**NotificationPreferences** (3 tests):
- Valid data creation
- Default values
- Validation error handling

**EmailNotificationProvider** (6 tests):
- Email address validation (valid/invalid)
- Email sending (success/failure)
- HTML email content generation
- Plain text email content generation

**SMSNotificationProvider** (4 tests):
- Phone number validation (valid/invalid)
- SMS sending
- SMS message formatting (≤160 chars)

**NotificationService** (12 tests):
- Service initialization
- Provider registration
- User preferences management
- Alert notification dispatching (severity-based)
- Quiet hours detection
- Rate limiting detection
- Message formatting (with/without details)
- Notification history retrieval
- Statistics generation

### Mock Strategy

**External Dependencies Mocked**:
1. **SMTP** - `smtplib.SMTP` mocked with `mocker.patch()`
2. **DateTime** - `datetime.now()` mocked for time-based tests
3. **SMS API** - Mock implementation (no actual API calls)

**Not Mocked**:
- Pydantic models (real validation)
- Internal logic (quiet hours calculation, rate limiting)
- Message formatting

## Usage Example

```python
from finwiz.tools.notification_service import (
    NotificationService,
    NotificationPreferences,
    NotificationType,
)
from finwiz.quantitative.portfolio_monitor import AlertSeverity

# Initialize service
service = NotificationService()

# Configure user preferences
preferences = NotificationPreferences(
    email_address="user@example.com",
    phone_number="+1234567890",
    enabled_notification_types=[NotificationType.EMAIL, NotificationType.SMS],
    email_alert_levels=[AlertSeverity.WARNING, AlertSeverity.ERROR, AlertSeverity.CRITICAL],
    sms_alert_levels=[AlertSeverity.ERROR, AlertSeverity.CRITICAL],
    quiet_hours_start=22,
    quiet_hours_end=7,
    max_notifications_per_hour=5,
    include_detailed_analysis=True,
    include_recommendations=True,
)
service.set_user_preferences("user_123", preferences)

# Send alert notification
from finwiz.quantitative.portfolio_monitor import PortfolioAlert, AlertType

alert = PortfolioAlert(
    alert_id="alert_456",
    portfolio_id="portfolio_123",
    alert_type=AlertType.DEVIATION_ALERT,
    severity=AlertSeverity.ERROR,
    title="Portfolio Deviation Detected",
    message="Portfolio has positions exceeding tolerance bands",
    affected_positions=["AAPL", "GOOGL"],
    current_deviations={"AAPL": 0.08, "GOOGL": -0.06},
    recommended_actions=["Review portfolio", "Consider rebalancing"],
)

# Send notifications (email + SMS for ERROR severity)
records = await service.send_alert_notification(alert, "user_123")

# Check results
for record in records:
    print(f"{record.notification_type}: {record.status}")

# Get statistics
stats = service.get_notification_statistics()
print(f"Success rate: {stats['success_rate']:.1%}")
```

## Best Practices

### 1. Provider Pattern
- All providers implement `NotificationProvider` ABC
- Easy to add new notification channels (PUSH, WEBHOOK)
- Each provider handles its own validation and formatting

### 2. Pydantic Validation
- All data models use Pydantic for validation
- Type safety with `str | None` (Python 3.12+)
- Clear validation errors for invalid data

### 3. pytest-mock Usage
- Always use `mocker` fixture (NEVER `unittest.mock`)
- Configure mock return values before use
- Let pytest-mock handle cleanup (no context managers needed)

### 4. Async/Await Pattern
- All notification sending is async
- Supports concurrent notification dispatch
- Non-blocking for high-volume scenarios

## Future Enhancements

1. **Push Notifications**: Implement mobile push notification provider
2. **Webhook Support**: Allow custom webhook integrations
3. **Template System**: Jinja2 templates for email formatting
4. **Retry Logic**: Automatic retry with exponential backoff
5. **Delivery Confirmation**: Track delivery status from providers
6. **Notification Batching**: Combine multiple alerts into digest emails
7. **User Unsubscribe**: Allow users to opt-out of specific alert types

## Related Modules

- **Portfolio Monitor**: `src/finwiz/quantitative/portfolio_monitor.py` (alert generation)
- **Alert Models**: Uses `PortfolioAlert`, `AlertSeverity`, `AlertType`
- **Testing**: `tests/unit/tools/test_notification_service.py`

## Key Lessons Learned

### pytest-mock Best Practices
1. **Configure before use**: Always set up mock return values before calling mocked methods
2. **Explicit mocking**: Create mock objects explicitly with `mocker.Mock()`
3. **Attribute access**: Use attribute assignment for simple values: `mock.hour = 23`
4. **No context managers**: pytest-mock auto-cleans up; `with` statement not needed

### Datetime Mocking Pattern
```python
# Create mock datetime object with specific hour
mock_now = mocker.Mock()
mock_now.hour = 23

# Patch datetime and configure return value
mock_datetime = mocker.patch("module.datetime")
mock_datetime.now.return_value = mock_now

# Now datetime.now().hour returns 23
```

### Test Organization
- Group tests by class (`TestNotificationService`, `TestEmailNotificationProvider`)
- Use descriptive test names: `test_should_<action>_when_<condition>`
- Arrange-Act-Assert pattern with clear comments
- Shared fixtures for common test data

## References

- **CLAUDE.md**: FinWiz testing standards (pytest-mock required)
- **pytest-mock**: https://pytest-mock.readthedocs.io/
- **Pydantic**: https://docs.pydantic.dev/latest/
- **BeautifulSoup**: https://www.crummy.com/software/BeautifulSoup/ (HTML email generation)
