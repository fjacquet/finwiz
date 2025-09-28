"""
CLI tool for managing A+ investment monitoring system.

Provides command-line interface for monitoring operations including:
- Starting/stopping monitoring
- Viewing monitoring status and alerts
- Managing monitored investments
- Generating monitoring reports
"""

import asyncio
import json
from datetime import datetime

import click

from finwiz.services.a_plus_monitoring_service import get_monitoring_service
from finwiz.tools.logger import get_logger
from finwiz.utils.a_plus_monitoring import get_monitoring_system

logger = get_logger(__name__)


@click.group()
def a_plus_monitoring() -> None:
    """A+ Investment Monitoring System CLI."""
    pass


@a_plus_monitoring.command()
@click.option("--background", "-b", is_flag=True, help="Run monitoring in background")
def start(background: bool) -> None:
    """Start the A+ monitoring system."""

    async def _start() -> None:
        try:
            service = get_monitoring_service()
            await service.start_service()

            if background:
                click.echo("✅ A+ monitoring started in background")
                # In production, would detach process or use systemd
            else:
                click.echo("✅ A+ monitoring started")
                click.echo("Press Ctrl+C to stop monitoring...")
                try:
                    # Keep running until interrupted
                    while True:
                        await asyncio.sleep(60)
                        # Could show periodic status updates here
                except KeyboardInterrupt:
                    click.echo("\n🛑 Stopping A+ monitoring...")
                    await service.stop_service()
                    click.echo("✅ A+ monitoring stopped")

        except Exception as e:
            click.echo(f"❌ Failed to start monitoring: {str(e)}", err=True)
            raise click.Abort()

    asyncio.run(_start())


@a_plus_monitoring.command()
def stop() -> None:
    """Stop the A+ monitoring system."""

    async def _stop() -> None:
        try:
            service = get_monitoring_service()
            await service.stop_service()
            click.echo("✅ A+ monitoring stopped")

        except Exception as e:
            click.echo(f"❌ Failed to stop monitoring: {str(e)}", err=True)
            raise click.Abort()

    asyncio.run(_stop())


@a_plus_monitoring.command()
@click.option("--format", "-f", type=click.Choice(["table", "json"]), default="table", help="Output format")
def status(format: str) -> None:
    """Show A+ monitoring system status."""

    async def _status() -> None:
        try:
            service = get_monitoring_service()
            dashboard = await service.get_monitoring_dashboard()

            if format == "json":
                click.echo(json.dumps(dashboard, indent=2, default=str))
                return

            # Table format
            click.echo("🔍 A+ Monitoring System Status")
            click.echo("=" * 50)

            # Service status
            status_info = dashboard["service_status"]
            status_icon = "🟢" if status_info["is_running"] else "🔴"
            click.echo(f"{status_icon} Service Running: {status_info['is_running']}")
            click.echo(f"📊 Monitoring Active: {status_info['monitoring_active']}")
            click.echo(f"🕐 Last Updated: {status_info['last_updated']}")
            click.echo()

            # Performance summary
            perf = dashboard["performance_summary"]
            click.echo("📈 Performance Summary")
            click.echo("-" * 30)
            click.echo(f"Total Investments: {perf['total_investments']}")
            click.echo(f"A+ Count: {perf['a_plus_count']} ({perf.get('a_plus_percentage', 0):.1f}%)")
            click.echo(f"A Grade Count: {perf['a_grade_count']}")
            click.echo(f"Degraded Count: {perf['degraded_count']}")
            click.echo(f"Average Score: {perf.get('average_score', 0):.3f}")
            click.echo(f"Health Status: {perf.get('monitoring_health', 'unknown')}")
            click.echo()

            # Alerts
            alerts = dashboard["alerts"]
            alert_icon = "🚨" if alerts["critical_count"] > 0 else "⚠️" if alerts["total_recent"] > 0 else "✅"
            click.echo(f"{alert_icon} Recent Alerts (24h)")
            click.echo("-" * 30)
            click.echo(f"Total: {alerts['total_recent']}")
            click.echo(f"Critical: {alerts['critical_count']}")

            if alerts["recent_alerts"]:
                click.echo("\nRecent Alerts:")
                for alert in alerts["recent_alerts"][:5]:
                    severity_icon = "🚨" if alert["severity"] in ["high", "critical"] else "⚠️"
                    click.echo(
                        f"  {severity_icon} {alert['symbol']}: {alert['grade_change']} (score: {alert['score_change']:+.3f})"
                    )
            click.echo()

            # Recommendations
            recommendations = dashboard["recommendations"]
            if recommendations:
                click.echo("💡 Recommendations")
                click.echo("-" * 30)
                for rec in recommendations:
                    click.echo(f"  {rec}")

        except Exception as e:
            click.echo(f"❌ Failed to get status: {str(e)}", err=True)
            raise click.Abort()

    asyncio.run(_status())


@a_plus_monitoring.command()
@click.option("--hours", "-h", default=24, help="Hours back to show alerts")
@click.option("--severity", "-s", type=click.Choice(["low", "medium", "high", "critical"]), help="Filter by severity")
@click.option("--format", "-f", type=click.Choice(["table", "json"]), default="table", help="Output format")
def alerts(hours: int, severity: str | None, format: str) -> None:
    """Show recent degradation alerts."""

    async def _alerts() -> None:
        try:
            monitoring_system = get_monitoring_system()
            recent_alerts = monitoring_system.get_degradation_alerts(hours_back=hours)

            # Filter by severity if specified
            if severity:
                recent_alerts = [alert for alert in recent_alerts if alert.severity.value == severity]

            if format == "json":
                alerts_data = [
                    {
                        "symbol": alert.symbol,
                        "asset_type": alert.asset_type,
                        "previous_grade": alert.previous_grade,
                        "current_grade": alert.current_grade,
                        "score_change": alert.score_change,
                        "severity": alert.severity.value,
                        "timestamp": alert.alert_timestamp.isoformat(),
                        "factors": alert.degradation_factors,
                        "actions": alert.recommended_actions,
                    }
                    for alert in recent_alerts
                ]
                click.echo(json.dumps(alerts_data, indent=2))
                return

            # Table format
            click.echo(f"🚨 Degradation Alerts (Last {hours} hours)")
            click.echo("=" * 70)

            if not recent_alerts:
                click.echo("✅ No alerts in the specified time period")
                return

            for alert in recent_alerts:
                severity_icon = {"low": "ℹ️", "medium": "⚠️", "high": "🔥", "critical": "🚨"}.get(alert.severity.value, "⚠️")

                click.echo(f"{severity_icon} {alert.symbol} ({alert.asset_type.upper()})")
                click.echo(f"   Grade: {alert.previous_grade} → {alert.current_grade}")
                click.echo(f"   Score: {alert.previous_score:.3f} → {alert.current_score:.3f} ({alert.score_change:+.3f})")
                click.echo(f"   Time: {alert.alert_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                click.echo(f"   Severity: {alert.severity.value.upper()}")

                if alert.degradation_factors:
                    click.echo(f"   Factors: {', '.join(alert.degradation_factors[:3])}")

                if alert.recommended_actions:
                    click.echo(f"   Actions: {alert.recommended_actions[0]}")

                click.echo()

        except Exception as e:
            click.echo(f"❌ Failed to get alerts: {str(e)}", err=True)
            raise click.Abort()

    asyncio.run(_alerts())


@a_plus_monitoring.command()
@click.option("--format", "-f", type=click.Choice(["table", "json"]), default="table", help="Output format")
def investments(format: str) -> None:
    """List monitored investments."""

    async def _investments() -> None:
        try:
            monitoring_system = get_monitoring_system()
            active_investments = monitoring_system.get_active_investments()

            if format == "json":
                investments_data = {}
                for symbol, metrics in active_investments.items():
                    investments_data[symbol] = {
                        "asset_type": metrics.asset_type,
                        "current_grade": metrics.current_grade,
                        "current_score": metrics.current_score,
                        "initial_grade": metrics.initial_grade,
                        "initial_score": metrics.initial_score,
                        "score_change": metrics.current_score - metrics.initial_score,
                        "recommendation_date": metrics.recommendation_date.isoformat(),
                        "last_evaluation": metrics.last_evaluation.isoformat(),
                        "total_return": metrics.total_return,
                        "alpha": metrics.alpha,
                        "days_monitored": (datetime.now() - metrics.recommendation_date).days,
                    }
                click.echo(json.dumps(investments_data, indent=2))
                return

            # Table format
            click.echo("📊 Monitored A+ Investments")
            click.echo("=" * 80)

            if not active_investments:
                click.echo("No investments currently monitored")
                return

            # Sort by current score (descending)
            sorted_investments = sorted(active_investments.items(), key=lambda x: x[1].current_score, reverse=True)

            # Header
            click.echo(f"{'Symbol':<10} {'Type':<6} {'Grade':<6} {'Score':<7} {'Change':<8} {'Days':<5} {'Return':<8}")
            click.echo("-" * 80)

            for symbol, metrics in sorted_investments:
                score_change = metrics.current_score - metrics.initial_score
                days_monitored = (datetime.now() - metrics.recommendation_date).days

                # Color coding for grade
                grade_icon = {"A+": "🏆", "A": "⭐", "B+": "📈", "B": "✅", "C+": "⚠️", "C": "🔍", "D": "⚡", "F": "❌"}.get(
                    metrics.current_grade, ""
                )

                click.echo(
                    f"{symbol:<10} {metrics.asset_type:<6} "
                    f"{grade_icon}{metrics.current_grade:<5} "
                    f"{metrics.current_score:<7.3f} "
                    f"{score_change:+7.3f} "
                    f"{days_monitored:<5} "
                    f"{metrics.total_return:+7.1%}"
                )

        except Exception as e:
            click.echo(f"❌ Failed to list investments: {str(e)}", err=True)
            raise click.Abort()

    asyncio.run(_investments())


@a_plus_monitoring.command()
@click.argument("symbol")
@click.option("--asset-type", "-t", type=click.Choice(["etf", "stock", "crypto"]), required=True, help="Asset type")
def add(symbol: str, asset_type: str) -> None:
    """Add an investment to monitoring (requires manual setup)."""
    click.echo("⚠️ Manual addition not fully implemented")
    click.echo(f"To add {symbol} ({asset_type}) to monitoring:")
    click.echo("1. Run investment discovery crew to get A+ analysis")
    click.echo("2. Use the discovery results to automatically add to monitoring")
    click.echo("3. Or use the monitoring service API programmatically")


@a_plus_monitoring.command()
@click.argument("symbol")
@click.option("--reason", "-r", default="Manual removal", help="Reason for removal")
def remove(symbol: str, reason: str) -> None:
    """Remove an investment from monitoring."""
    try:
        monitoring_system = get_monitoring_system()

        if symbol not in monitoring_system.monitored_investments:
            click.echo(f"❌ {symbol} not found in monitoring system")
            raise click.Abort()

        monitoring_system.remove_investment_from_monitor(symbol, reason)
        click.echo(f"✅ Removed {symbol} from monitoring")
        click.echo(f"Reason: {reason}")

    except Exception as e:
        click.echo(f"❌ Failed to remove {symbol}: {str(e)}", err=True)
        raise click.Abort()


@a_plus_monitoring.command()
@click.option("--symbol", "-s", help="Evaluate specific symbol only")
def evaluate(symbol: str | None) -> None:
    """Force evaluation of monitored investments."""

    async def _evaluate() -> None:
        try:
            service = get_monitoring_service()

            if symbol:
                # Evaluate single investment
                monitoring_system = get_monitoring_system()
                if symbol not in monitoring_system.get_active_investments():
                    click.echo(f"❌ {symbol} not found in monitoring")
                    raise click.Abort()

                click.echo(f"🔄 Evaluating {symbol}...")
                analysis = await monitoring_system.evaluate_investment(symbol, force_evaluation=True)

                if analysis:
                    click.echo(f"✅ {symbol} evaluation complete")
                    click.echo(f"   Grade: {analysis.candidate.grade}")
                    click.echo(f"   Score: {analysis.composite_score:.3f}")
                    click.echo(f"   A+ Status: {'Yes' if analysis.is_a_plus_candidate else 'No'}")
                else:
                    click.echo(f"❌ Failed to evaluate {symbol}")
            else:
                # Evaluate all investments
                click.echo("🔄 Evaluating all monitored investments...")
                result = await service.force_evaluation_all()

                click.echo("✅ Evaluation complete")
                click.echo(f"   Total Evaluated: {result['total_evaluated']}")
                click.echo(f"   Still A+: {result['still_a_plus']}")
                click.echo(f"   Degraded: {result['degraded_count']}")
                click.echo(f"   New Alerts: {result['new_alerts']}")

        except Exception as e:
            click.echo(f"❌ Evaluation failed: {str(e)}", err=True)
            raise click.Abort()

    asyncio.run(_evaluate())


@a_plus_monitoring.command()
@click.option("--days", "-d", default=30, help="Days of inactivity before cleanup")
@click.option("--dry-run", is_flag=True, help="Show what would be cleaned up without doing it")
def cleanup(days: int, dry_run: bool) -> None:
    """Clean up inactive or degraded investments."""

    async def _cleanup() -> None:
        try:
            if dry_run:
                click.echo("🔍 Dry run: showing investments that would be cleaned up")
                # In a real implementation, would show what would be removed
                click.echo("(Dry run functionality not fully implemented)")
                return

            service = get_monitoring_service()
            result = await service.cleanup_inactive_investments(days_inactive=days)

            click.echo("🧹 Cleanup complete")
            click.echo(f"   Removed: {result['removed_count']} investments")
            click.echo(f"   Remaining: {result['remaining_monitored']} investments")

            if result["removed_symbols"]:
                click.echo(f"   Removed symbols: {', '.join(result['removed_symbols'])}")

        except Exception as e:
            click.echo(f"❌ Cleanup failed: {str(e)}", err=True)
            raise click.Abort()

    asyncio.run(_cleanup())


@a_plus_monitoring.command()
@click.option("--output", "-o", help="Output file path")
@click.option("--format", "-f", type=click.Choice(["json", "csv"]), default="json", help="Output format")
def export(output: str | None, format: str) -> None:
    """Export monitoring data."""

    async def _export() -> None:
        try:
            service = get_monitoring_service()
            dashboard = await service.get_monitoring_dashboard()

            if format == "json":
                data = json.dumps(dashboard, indent=2, default=str)
            elif format == "csv":
                # Simplified CSV export of investments
                import csv
                import io

                output_buffer = io.StringIO()
                writer = csv.writer(output_buffer)

                # Header
                writer.writerow(
                    [
                        "Symbol",
                        "Asset Type",
                        "Current Grade",
                        "Current Score",
                        "Score Change",
                        "Days Monitored",
                        "Total Return",
                        "Alpha",
                    ]
                )

                # Data
                for inv in dashboard["investments"]["details"]:
                    writer.writerow(
                        [
                            inv["symbol"],
                            inv["asset_type"],
                            inv["current_grade"],
                            inv["current_score"],
                            inv["score_change"],
                            inv["days_monitored"],
                            inv["total_return"],
                            inv["alpha"],
                        ]
                    )

                data = output_buffer.getvalue()

            if output:
                with open(output, "w") as f:
                    f.write(data)
                click.echo(f"✅ Data exported to {output}")
            else:
                click.echo(data)

        except Exception as e:
            click.echo(f"❌ Export failed: {str(e)}", err=True)
            raise click.Abort()

    asyncio.run(_export())


if __name__ == "__main__":
    a_plus_monitoring()
