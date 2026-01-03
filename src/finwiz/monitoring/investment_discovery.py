"""
Investment Discovery Monitoring System.

This module provides comprehensive monitoring for the Investment Discovery Crew,
including performance metrics, discovery quality tracking, and alerting for
production deployment.
"""

import json
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from finwiz.infrastructure.monitoring.core import get_metrics_collector
from finwiz.schemas.investment_discovery import APlusDiscoveryResult
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


@dataclass
class DiscoveryMetrics:
    """Metrics for investment discovery performance."""

    total_discoveries: int = 0
    a_plus_discoveries: int = 0
    discovery_success_rate: float = 0.0
    avg_discovery_time: float = 0.0
    grade_distribution: dict[str, int] = field(default_factory=dict)
    asset_type_distribution: dict[str, int] = field(default_factory=dict)
    last_discovery_time: datetime | None = None
    discovery_errors: int = 0
    validation_pass_rate: float = 0.0


@dataclass
class QualityMetrics:
    """Quality metrics for A+ discoveries."""

    grade_retention_rate: float = 0.0  # % of A+ that stay A+ after 30 days
    recommendation_acceptance_rate: float = 0.0  # % of recommendations accepted
    portfolio_improvement_rate: float = 0.0  # Average grade improvement
    false_positive_rate: float = 0.0  # % of A+ that become B+ or lower
    discovery_precision: float = 0.0  # True A+ / Total A+ discovered
    discovery_recall: float = 0.0  # True A+ discovered / Total True A+


@dataclass
class AlertThresholds:
    """Alert thresholds for monitoring."""

    min_discovery_rate: int = 5  # Minimum discoveries per day
    max_error_rate: float = 0.1  # Maximum 10% error rate
    min_success_rate: float = 0.8  # Minimum 80% success rate
    max_discovery_time: float = 600.0  # Maximum 10 minutes per discovery
    min_grade_retention: float = 0.7  # Minimum 70% grade retention
    min_validation_pass_rate: float = 0.6  # Minimum 60% validation pass rate


class InvestmentDiscoveryMonitor:
    """
    Comprehensive monitoring system for Investment Discovery Crew.

    Tracks performance, quality, and operational metrics for production
    deployment with alerting and dashboard capabilities.
    """

    def __init__(self, output_dir: str = "output/monitoring") -> None:
        """Initialize the investment discovery monitor."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.metrics_collector = get_metrics_collector()
        self.discovery_metrics = DiscoveryMetrics()
        self.quality_metrics = QualityMetrics()
        self.alert_thresholds = AlertThresholds()

        # Historical data storage
        self.discovery_history: list[dict[str, Any]] = []
        self.quality_history: list[dict[str, Any]] = []
        self.alert_history: list[dict[str, Any]] = []

        # Performance tracking
        self.discovery_times: list[float] = []
        self.grade_changes: dict[str, list[dict[str, Any]]] = defaultdict(list)

        logger.info("Investment Discovery Monitor initialized")

    def record_discovery_start(self, discovery_id: str, asset_type: str) -> None:
        """Record the start of a discovery operation."""
        self.metrics_collector.record_counter("discovery.started", tags={"asset_type": asset_type, "discovery_id": discovery_id})

        logger.info(f"Discovery started: {discovery_id} ({asset_type})")

    def record_discovery_completion(self, discovery_id: str, result: APlusDiscoveryResult, duration: float, success: bool = True) -> None:
        """Record the completion of a discovery operation."""
        # Update basic metrics
        self.discovery_metrics.total_discoveries += 1
        self.discovery_metrics.last_discovery_time = datetime.now()
        self.discovery_times.append(duration)

        if success:
            # Count A+ discoveries
            a_plus_count = sum(1 for analysis in result.a_plus_candidates if analysis.candidate.grade == "A+")
            self.discovery_metrics.a_plus_discoveries += a_plus_count

            # Update grade distribution
            for analysis in result.a_plus_candidates:
                grade = analysis.candidate.grade
                self.discovery_metrics.grade_distribution[grade] = self.discovery_metrics.grade_distribution.get(grade, 0) + 1

            # Update asset type distribution
            asset_type = result.asset_type
            self.discovery_metrics.asset_type_distribution[asset_type] = self.discovery_metrics.asset_type_distribution.get(asset_type, 0) + 1

            # Record metrics
            self.metrics_collector.record_counter("discovery.completed", tags={"asset_type": asset_type, "success": "true"})
            self.metrics_collector.record_histogram("discovery.duration", duration, tags={"asset_type": asset_type})
            self.metrics_collector.record_gauge("discovery.a_plus_count", a_plus_count, tags={"asset_type": asset_type})

        else:
            self.discovery_metrics.discovery_errors += 1
            self.metrics_collector.record_counter("discovery.failed", tags={"asset_type": result.asset_type if result else "unknown"})

        # Update calculated metrics
        self._update_calculated_metrics()

        # Store historical data
        self._store_discovery_record(discovery_id, result, duration, success)

        logger.info(f"Discovery completed: {discovery_id} (duration: {duration:.2f}s, success: {success})")

    def record_validation_result(self, candidate_symbol: str, validation_passed: bool, validation_score: float) -> None:
        """Record validation results for discovered candidates."""
        self.metrics_collector.record_counter("validation.completed", tags={"result": "pass" if validation_passed else "fail"})
        self.metrics_collector.record_gauge("validation.score", validation_score, tags={"symbol": candidate_symbol})

        logger.info(f"Validation recorded: {candidate_symbol} (passed: {validation_passed}, score: {validation_score:.3f})")

    def record_grade_change(self, symbol: str, old_grade: str, new_grade: str, days_since_discovery: int) -> None:
        """Record grade changes for tracking quality metrics."""
        self.grade_changes[symbol].append(
            {
                "old_grade": old_grade,
                "new_grade": new_grade,
                "days_since_discovery": days_since_discovery,
                "timestamp": datetime.now().isoformat(),
            }
        )

        self.metrics_collector.record_counter("grade.changed", tags={"from_grade": old_grade, "to_grade": new_grade, "symbol": symbol})

        # Update quality metrics
        self._update_quality_metrics()

        logger.info(f"Grade change recorded: {symbol} {old_grade} -> {new_grade} ({days_since_discovery} days)")

    def record_recommendation_feedback(self, symbol: str, accepted: bool, portfolio_improvement: float) -> None:
        """Record user feedback on recommendations."""
        self.metrics_collector.record_counter("recommendation.feedback", tags={"accepted": str(accepted).lower(), "symbol": symbol})

        if accepted:
            self.metrics_collector.record_gauge("portfolio.improvement", portfolio_improvement, tags={"symbol": symbol})

        logger.info(f"Recommendation feedback: {symbol} (accepted: {accepted}, improvement: {portfolio_improvement:.3f})")

    def check_alert_conditions(self) -> list[dict[str, Any]]:
        """Check for alert conditions and return active alerts."""
        alerts = []
        now = datetime.now()

        # Check discovery rate
        if self.discovery_metrics.last_discovery_time:
            hours_since_last = (now - self.discovery_metrics.last_discovery_time).total_seconds() / 3600
            if hours_since_last > 24:  # No discoveries in 24 hours
                alerts.append(
                    {
                        "type": "discovery_rate",
                        "severity": "warning",
                        "message": f"No discoveries in {hours_since_last:.1f} hours",
                        "timestamp": now.isoformat(),
                    }
                )

        # Check error rate
        if (
            self.discovery_metrics.total_discoveries > 0
            and self.discovery_metrics.discovery_errors / self.discovery_metrics.total_discoveries > self.alert_thresholds.max_error_rate
        ):
            error_rate = self.discovery_metrics.discovery_errors / self.discovery_metrics.total_discoveries
            alerts.append(
                {
                    "type": "error_rate",
                    "severity": "critical",
                    "message": f"High error rate: {error_rate:.1%}",
                    "timestamp": now.isoformat(),
                }
            )

        # Check success rate
        if self.discovery_metrics.discovery_success_rate < self.alert_thresholds.min_success_rate:
            alerts.append(
                {
                    "type": "success_rate",
                    "severity": "warning",
                    "message": f"Low success rate: {self.discovery_metrics.discovery_success_rate:.1%}",
                    "timestamp": now.isoformat(),
                }
            )

        # Check discovery time
        if self.discovery_times and self.discovery_metrics.avg_discovery_time > self.alert_thresholds.max_discovery_time:
            alerts.append(
                {
                    "type": "performance",
                    "severity": "warning",
                    "message": f"Slow discovery time: {self.discovery_metrics.avg_discovery_time:.1f}s",
                    "timestamp": now.isoformat(),
                }
            )

        # Check grade retention
        if self.quality_metrics.grade_retention_rate < self.alert_thresholds.min_grade_retention:
            alerts.append(
                {
                    "type": "quality",
                    "severity": "warning",
                    "message": f"Low grade retention: {self.quality_metrics.grade_retention_rate:.1%}",
                    "timestamp": now.isoformat(),
                }
            )

        # Store alerts
        for alert in alerts:
            self.alert_history.append(alert)
            logger.warning(f"Alert triggered: {alert['type']} - {alert['message']}")

        return alerts

    def get_dashboard_data(self) -> dict[str, Any]:
        """Get comprehensive dashboard data for monitoring UI."""
        return {
            "discovery_metrics": asdict(self.discovery_metrics),
            "quality_metrics": asdict(self.quality_metrics),
            "recent_alerts": self.alert_history[-10:],  # Last 10 alerts
            "performance_summary": self.metrics_collector.get_performance_summary(),
            "health_status": self.metrics_collector.get_health_status(),
            "grade_distribution": dict(self.discovery_metrics.grade_distribution),
            "asset_type_distribution": dict(self.discovery_metrics.asset_type_distribution),
            "recent_discoveries": self.discovery_history[-20:],  # Last 20 discoveries
            "timestamp": datetime.now().isoformat(),
        }

    def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format."""
        dashboard_data = self.get_dashboard_data()

        if format.lower() == "json":
            output_file = self.output_dir / f"discovery_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, "w") as f:
                json.dump(dashboard_data, f, indent=2, default=str)
            return str(output_file)

        # Add other formats as needed (CSV, etc.)
        raise ValueError(f"Unsupported export format: {format}")

    def _update_calculated_metrics(self) -> None:
        """Update calculated metrics based on current data."""
        if self.discovery_metrics.total_discoveries > 0:
            # Success rate
            successful_discoveries = self.discovery_metrics.total_discoveries - self.discovery_metrics.discovery_errors
            self.discovery_metrics.discovery_success_rate = successful_discoveries / self.discovery_metrics.total_discoveries

            # Average discovery time
            if self.discovery_times:
                self.discovery_metrics.avg_discovery_time = sum(self.discovery_times) / len(self.discovery_times)

    def _update_quality_metrics(self) -> None:
        """Update quality metrics based on grade changes."""
        if not self.grade_changes:
            return

        # Calculate grade retention rate
        a_plus_to_a_plus = 0
        total_a_plus_tracked = 0

        for symbol, changes in self.grade_changes.items():
            for change in changes:
                if change["old_grade"] == "A+":
                    total_a_plus_tracked += 1
                    if change["new_grade"] == "A+":
                        a_plus_to_a_plus += 1

        if total_a_plus_tracked > 0:
            self.quality_metrics.grade_retention_rate = a_plus_to_a_plus / total_a_plus_tracked

    def _store_discovery_record(self, discovery_id: str, result: APlusDiscoveryResult, duration: float, success: bool) -> None:
        """Store discovery record for historical analysis."""
        record = {
            "discovery_id": discovery_id,
            "timestamp": datetime.now().isoformat(),
            "duration": duration,
            "success": success,
            "asset_type": result.asset_type if result else None,
            "candidates_count": len(result.a_plus_candidates) if result and result.a_plus_candidates else 0,
            "a_plus_count": sum(1 for a in result.a_plus_candidates if a.candidate.grade == "A+") if result and result.a_plus_candidates else 0,
        }

        self.discovery_history.append(record)

        # Keep only last 1000 records
        if len(self.discovery_history) > 1000:
            self.discovery_history = self.discovery_history[-1000:]


# Global monitor instance
_discovery_monitor: InvestmentDiscoveryMonitor | None = None


def get_discovery_monitor() -> InvestmentDiscoveryMonitor:
    """Get the global investment discovery monitor instance."""
    global _discovery_monitor
    if _discovery_monitor is None:
        _discovery_monitor = InvestmentDiscoveryMonitor()
    return _discovery_monitor


async def monitor_discovery_health() -> dict[str, Any]:
    """Monitor discovery system health and return status."""
    monitor = get_discovery_monitor()

    # Check for alerts
    alerts = monitor.check_alert_conditions()

    # Get health status
    health_status = monitor.metrics_collector.get_health_status()

    # Get dashboard data
    dashboard_data = monitor.get_dashboard_data()

    return {
        "health_status": health_status,
        "active_alerts": alerts,
        "discovery_metrics": dashboard_data["discovery_metrics"],
        "quality_metrics": dashboard_data["quality_metrics"],
    }
