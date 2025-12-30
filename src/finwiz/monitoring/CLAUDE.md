# Monitoring Module

This directory contains monitoring and alerting infrastructure for tracking investment performance and system health.

## Directory Structure

```
monitoring/
├── investment_discovery_monitor.py  # Monitor A+ discoveries
├── alerting.py                      # Alert generation and delivery
└── __init__.py
```

## Major Entry Points

| File | Class/Function | Purpose |
|------|---------------|---------|
| `investment_discovery_monitor.py` | `InvestmentDiscoveryMonitor` | Track discovered A+ opportunities |
| `investment_discovery_monitor.py` | `monitor_price_targets()` | Check against price targets |
| `alerting.py` | `AlertManager` | Manage and send alerts |
| `alerting.py` | `create_alert()` | Create new alert instance |

## Usage Pattern

```python
from finwiz.monitoring.investment_discovery_monitor import InvestmentDiscoveryMonitor
from finwiz.monitoring.alerting import AlertManager

# Setup monitoring
monitor = InvestmentDiscoveryMonitor()
alert_manager = AlertManager()

# Add discoveries to monitor
monitor.add_discovery(ticker="NVDA", entry_price=120, target_price=150)

# Check for alerts
alerts = monitor.check_price_levels()
for alert in alerts:
    alert_manager.send_alert(alert)
```

## Alert Types

- **Price Target Hit**: Stock reached target price
- **Stop Loss Triggered**: Stock hit stop loss level
- **Trend Change**: Technical trend reversal detected
- **News Alert**: Significant news for monitored stock

## Related Modules

- `finwiz.services.a_plus_monitoring_service` - Higher-level monitoring
- `finwiz.utils.monitoring` - Performance monitoring
- `finwiz.tools.notification_service` - Notification delivery
