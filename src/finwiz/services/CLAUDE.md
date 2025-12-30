# Services Module

This directory contains business service classes that coordinate complex operations across multiple components.

## Directory Structure

```
services/
├── feedback/                    # Feedback system components
│   ├── analytics.py            # Feedback analytics
│   ├── criteria.py             # Feedback criteria definitions
│   ├── insights.py             # Insight generation from feedback
│   ├── service.py              # Main feedback service
│   └── storage.py              # Feedback persistence
├── feedback_service.py          # Legacy feedback service (re-export)
├── a_plus_monitoring_service.py # A+ investment monitoring
└── __init__.py
```

## Major Entry Points

| File | Class/Function | Purpose |
|------|---------------|---------|
| `feedback/service.py` | `FeedbackService` | Collect and process user feedback |
| `feedback/analytics.py` | `FeedbackAnalytics` | Analyze feedback patterns |
| `feedback/insights.py` | `FeedbackInsights` | Generate actionable insights |
| `a_plus_monitoring_service.py` | `APlusMonitoringService` | Monitor A+ investments |

## Feedback System

```python
from finwiz.services.feedback.service import FeedbackService

service = FeedbackService()

# Collect feedback
service.submit_feedback(
    ticker="AAPL",
    recommendation="BUY",
    user_action="FOLLOWED",
    outcome="POSITIVE"
)

# Analyze patterns
analytics = service.get_analytics()
accuracy = analytics.recommendation_accuracy
```

## A+ Monitoring

```python
from finwiz.services.a_plus_monitoring_service import APlusMonitoringService

monitor = APlusMonitoringService()

# Start monitoring discovered opportunities
monitor.start_monitoring(discoveries)

# Get alerts
alerts = monitor.get_price_alerts()
```

## Related Modules

- `finwiz.schemas.feedback` - Feedback schemas
- `finwiz.tools.feedback_integration_tool` - CrewAI tool integration
- `finwiz.monitoring` - Alerting infrastructure
