#!/usr/bin/env python3
"""
Portfolio Monitoring and Alerting Demo.

This script demonstrates the portfolio monitoring and alerting capabilities
including drift detection, alert generation, and notification delivery.
"""

import asyncio
import logging

from finwiz.quantitative.portfolio_monitor import (
    AlertSeverity,
    AlertType,
    MonitoringRule,
    PortfolioMonitor,
)
from finwiz.schemas.portfolio_rebalancing import (
    Holding,
    PortfolioConfiguration,
)
from finwiz.tools.notification_service import (
    NotificationPreferences,
    NotificationService,
    NotificationType,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Demonstrate portfolio monitoring and alerting functionality."""
    print("🔍 Portfolio Monitoring and Alerting Demo")
    print("=" * 50)

    # 1. Create sample portfolio configuration
    print("\n1. Setting up sample portfolio...")

    portfolio_config = PortfolioConfiguration(
        holdings=[
            Holding(symbol="AAPL", shares=100),  # $15,000 (target: 25%)
            Holding(symbol="GOOGL", shares=10),  # $25,000 (target: 30%)
            Holding(symbol="MSFT", shares=50),  # $15,000 (target: 25%)
            Holding(symbol="TSLA", shares=25),  # $20,000 (target: 20%)
        ],
        target_weights={
            "AAPL": 0.25,  # Target: 25%
            "GOOGL": 0.30,  # Target: 30%
            "MSFT": 0.25,  # Target: 25%
            "TSLA": 0.20,  # Target: 20%
        },
        global_tolerance=0.05,  # 5% tolerance
        available_capital=5000.0,
    )

    print("Portfolio Holdings:")
    for holding in portfolio_config.holdings:
        target_weight = portfolio_config.target_weights[holding.symbol]
        print(f"  {holding.symbol}: {holding.shares} shares (target: {target_weight:.1%})")

    # 2. Set up monitoring rule
    print("\n2. Configuring monitoring rules...")

    monitoring_rule = MonitoringRule(
        rule_id="demo_monitoring_rule",
        rule_name="Demo Portfolio Monitoring",
        max_deviation_threshold=0.08,  # 8% threshold
        min_check_interval_hours=1,
        alert_on_deviation=True,
        alert_on_multiple_positions=True,
        min_positions_for_alert=2,
        enable_auto_rebalancing=False,
    )

    print("Monitoring Rule:")
    print(f"  Max deviation threshold: {monitoring_rule.max_deviation_threshold:.1%}")
    print(f"  Check interval: {monitoring_rule.min_check_interval_hours} hours")
    print(f"  Alert on deviation: {monitoring_rule.alert_on_deviation}")

    # 3. Set up notification preferences
    print("\n3. Setting up notification preferences...")

    notification_preferences = NotificationPreferences(
        email_address="demo@example.com",
        phone_number="+1234567890",
        enabled_notification_types=[NotificationType.EMAIL, NotificationType.SMS],
        email_alert_levels=[AlertSeverity.WARNING, AlertSeverity.ERROR, AlertSeverity.CRITICAL],
        sms_alert_levels=[AlertSeverity.ERROR, AlertSeverity.CRITICAL],
        max_notifications_per_hour=10,
        include_detailed_analysis=True,
        include_recommendations=True,
    )

    print("Notification Preferences:")
    print(f"  Email: {notification_preferences.email_address}")
    print(f"  Phone: {notification_preferences.phone_number}")
    print(f"  Email alerts: {[level.value for level in notification_preferences.email_alert_levels]}")
    print(f"  SMS alerts: {[level.value for level in notification_preferences.sms_alert_levels]}")

    # 4. Initialize monitoring and notification services
    print("\n4. Initializing monitoring system...")

    portfolio_monitor = PortfolioMonitor()
    notification_service = NotificationService()

    # Set user preferences
    user_id = "demo_user"
    notification_service.set_user_preferences(user_id, notification_preferences)

    print("✅ Monitoring system initialized")

    # 5. Perform portfolio drift check
    print("\n5. Checking portfolio drift...")

    portfolio_id = "demo_portfolio"

    try:
        # This would normally use real price data
        # For demo purposes, we'll simulate the check
        print("📊 Analyzing current portfolio weights vs targets...")

        # Generate health dashboard
        dashboard = await portfolio_monitor.generate_health_dashboard(portfolio_id, portfolio_config)

        print("\n📈 Portfolio Health Dashboard:")
        print(f"  Overall health score: {dashboard.overall_health_score:.1f}/10")
        print(f"  Health status: {dashboard.health_status}")
        print(f"  Max deviation: {dashboard.max_deviation:.1%}")
        print(f"  Avg deviation: {dashboard.avg_deviation:.1%}")
        print(f"  Rebalancing urgency: {dashboard.rebalancing_urgency.value}")
        print(f"  Positions needing attention: {len(dashboard.positions_needing_attention)}")

        if dashboard.positions_needing_attention:
            print("\n⚠️  Positions requiring attention:")
            for position in dashboard.positions_needing_attention:
                print(
                    f"    {position.symbol}: {position.deviation:+.1%} deviation "
                    f"(target: {position.target_weight:.1%}, current: {position.current_weight:.1%})"
                )

    except Exception as e:
        print(f"⚠️  Note: Portfolio drift check requires real price data. Error: {e}")
        print("📝 In a real implementation, this would connect to market data APIs")

    # 6. Demonstrate alert generation
    print("\n6. Demonstrating alert generation...")

    # Generate sample alert
    sample_alert = await portfolio_monitor._generate_alert(
        portfolio_id=portfolio_id,
        alert_type=AlertType.DEVIATION_ALERT,
        severity=AlertSeverity.WARNING,
        title="Portfolio Deviation Detected",
        message="TSLA position has drifted 7% above target allocation",
        affected_positions=["TSLA"],
        current_deviations={"TSLA": 0.07},
        recommended_actions=[
            "Consider selling TSLA shares to rebalance",
            "Review overall portfolio allocation",
            "Check if target weights need adjustment",
        ],
    )

    print("🚨 Generated Alert:")
    print(f"  Alert ID: {sample_alert.alert_id}")
    print(f"  Type: {sample_alert.alert_type}")
    print(f"  Severity: {sample_alert.severity}")
    print(f"  Title: {sample_alert.title}")
    print(f"  Message: {sample_alert.message}")
    print(f"  Affected positions: {sample_alert.affected_positions}")
    print("  Recommended actions:")
    for action in sample_alert.recommended_actions:
        print(f"    • {action}")

    # 7. Demonstrate notification sending
    print("\n7. Demonstrating notification delivery...")

    try:
        notification_records = await notification_service.send_alert_notification(sample_alert, user_id)

        print("📧 Notification Results:")
        if notification_records:
            for record in notification_records:
                print(f"  {record.notification_type.value}: {record.status.value} to {record.recipient}")
        else:
            print("  No notifications sent (may be due to quiet hours or rate limiting)")

    except Exception as e:
        print(f"📝 Note: Notification sending simulated. Error: {e}")
        print("📧 In a real implementation, this would send actual emails/SMS")

    # 8. Show monitoring statistics
    print("\n8. Monitoring system statistics...")

    monitor_stats = portfolio_monitor.get_monitoring_statistics()
    notification_stats = notification_service.get_notification_statistics()

    print("📊 Monitoring Statistics:")
    print(f"  Portfolios monitored: {monitor_stats['total_portfolios_monitored']}")
    print(f"  Active monitoring tasks: {monitor_stats['active_monitoring_tasks']}")
    print(f"  Total alerts generated: {monitor_stats['total_alerts_generated']}")

    print("\n📧 Notification Statistics:")
    print(f"  Total notifications: {notification_stats['total_notifications_sent']}")
    print(f"  Success rate: {notification_stats['success_rate']:.1%}")
    print(f"  Registered providers: {notification_stats['registered_providers']}")

    # 9. Demonstrate alert management
    print("\n9. Demonstrating alert management...")

    # Get active alerts
    active_alerts = await portfolio_monitor.get_active_alerts(portfolio_id)
    print(f"📋 Active alerts: {len(active_alerts)}")

    if active_alerts:
        alert = active_alerts[0]
        print(f"  Alert: {alert.title}")

        # Acknowledge alert
        ack_result = await portfolio_monitor.acknowledge_alert(portfolio_id, alert.alert_id)
        print(f"  ✅ Alert acknowledged: {ack_result}")

        # Resolve alert
        resolve_result = await portfolio_monitor.resolve_alert(portfolio_id, alert.alert_id, "Portfolio rebalanced successfully")
        print(f"  ✅ Alert resolved: {resolve_result}")

    print("\n🎉 Portfolio monitoring and alerting demo completed!")
    print("\nKey Features Demonstrated:")
    print("  ✅ Portfolio drift monitoring")
    print("  ✅ Health dashboard generation")
    print("  ✅ Configurable monitoring rules")
    print("  ✅ Multi-channel notifications (email/SMS)")
    print("  ✅ Alert severity levels and urgency")
    print("  ✅ User notification preferences")
    print("  ✅ Alert acknowledgment and resolution")
    print("  ✅ Comprehensive monitoring statistics")


if __name__ == "__main__":
    asyncio.run(main())
