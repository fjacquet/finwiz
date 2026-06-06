"""
Monitoring and metrics collection for FinWiz application.

This module provides comprehensive monitoring capabilities including
performance metrics, error tracking, and operational insights for
production deployment.
"""

import asyncio
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from finwiz.config.features.flags import is_feature_enabled
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


@dataclass
class MetricPoint:
    """Individual metric data point."""

    timestamp: datetime
    value: float
    tags: dict[str, str] = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    """Performance metrics for operations."""

    operation_name: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_duration: float = 0.0
    min_duration: float = float("inf")
    max_duration: float = 0.0
    last_call_time: datetime | None = None
    error_rate: float = 0.0
    avg_duration: float = 0.0


class MetricsCollector:
    """
    Metrics collector for FinWiz application monitoring.

    Collects performance metrics, error rates, and operational data
    for monitoring and alerting in production environments.
    """

    def __init__(self, max_history: int = 1000) -> None:
        """Initialize metrics collector."""
        self.max_history = max_history
        self.metrics: dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.performance_metrics: dict[str, PerformanceMetrics] = {}
        self.counters: dict[str, int] = defaultdict(int)
        self.gauges: dict[str, float] = {}
        self.start_time = datetime.now()

        logger.info("Metrics collector initialized")

    def record_counter(self, name: str, value: int = 1, tags: dict[str, str] | None = None) -> None:
        """Record a counter metric."""
        self.counters[name] += value

        if tags:
            tagged_name = f"{name}:{','.join(f'{k}={v}' for k, v in tags.items())}"
            self.counters[tagged_name] += value

    def record_histogram(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        """Record a histogram metric."""
        metric_point = MetricPoint(timestamp=datetime.now(), value=value, tags=tags or {})
        self.metrics[name].append(metric_point)

    def start_timer(self, operation_name: str) -> Callable[[], None]:
        """Start a timer for an operation."""
        start_time = time.time()

        def end_timer(success: bool = True, error: str | None = None) -> None:
            duration = time.time() - start_time
            self.record_operation_metrics(operation_name, duration, success, error)

        return end_timer

    def record_operation_metrics(self, operation_name: str, duration: float, success: bool = True, error: str | None = None) -> None:
        """Record metrics for an operation."""
        if operation_name not in self.performance_metrics:
            self.performance_metrics[operation_name] = PerformanceMetrics(operation_name)

        metrics = self.performance_metrics[operation_name]
        metrics.total_calls += 1
        metrics.total_duration += duration
        metrics.last_call_time = datetime.now()

        if success:
            metrics.successful_calls += 1
        else:
            metrics.failed_calls += 1
            if error:
                logger.warning(f"Operation {operation_name} failed: {error}")

        # Update duration statistics
        metrics.min_duration = min(metrics.min_duration, duration)
        metrics.max_duration = max(metrics.max_duration, duration)
        metrics.avg_duration = metrics.total_duration / metrics.total_calls
        metrics.error_rate = metrics.failed_calls / metrics.total_calls

        # Record histogram for duration
        self.record_histogram(f"{operation_name}.duration", duration)

        # Record counter for calls
        self.record_counter(f"{operation_name}.calls", tags={"status": "success" if success else "error"})

    def get_performance_summary(self) -> dict[str, Any]:
        """Get performance summary for all operations."""
        summary = {"uptime_seconds": (datetime.now() - self.start_time).total_seconds(), "operations": {}}

        for name, metrics in self.performance_metrics.items():
            summary["operations"][name] = {
                "total_calls": metrics.total_calls,
                "successful_calls": metrics.successful_calls,
                "failed_calls": metrics.failed_calls,
                "error_rate": metrics.error_rate,
                "avg_duration": metrics.avg_duration,
                "min_duration": metrics.min_duration if metrics.min_duration != float("inf") else 0,
                "max_duration": metrics.max_duration,
                "last_call": metrics.last_call_time.isoformat() if metrics.last_call_time else None,
            }

        return summary

    def get_health_status(self) -> dict[str, Any]:
        """Get overall health status of the application."""
        total_operations = sum(m.total_calls for m in self.performance_metrics.values())
        total_errors = sum(m.failed_calls for m in self.performance_metrics.values())
        overall_error_rate = total_errors / total_operations if total_operations > 0 else 0

        # Determine health status
        if overall_error_rate > 0.1:  # More than 10% error rate
            health_status = "unhealthy"
        elif overall_error_rate > 0.05:  # More than 5% error rate
            health_status = "degraded"
        else:
            health_status = "healthy"

        return {
            "status": health_status,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "total_operations": total_operations,
            "total_errors": total_errors,
            "error_rate": overall_error_rate,
            "timestamp": datetime.now().isoformat(),
        }


class PerformanceMonitor:
    """
    Performance monitoring decorator and context manager.

    Provides easy-to-use decorators and context managers for
    monitoring function and operation performance.
    """

    def __init__(self, metrics_collector: MetricsCollector) -> None:
        """Initialize performance monitor."""
        self.metrics_collector = metrics_collector

    def monitor_function(self, operation_name: str | None = None) -> Callable:
        """Monitor function performance."""

        def decorator(func: Callable) -> Callable:
            name = operation_name or f"{func.__module__}.{func.__name__}"

            if asyncio.iscoroutinefunction(func):

                async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                    end_timer = self.metrics_collector.start_timer(name)
                    try:
                        result = await func(*args, **kwargs)
                        end_timer(success=True)
                        return result
                    except Exception as e:
                        end_timer(success=False, error=str(e))
                        raise

                return async_wrapper
            else:

                def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                    end_timer = self.metrics_collector.start_timer(name)
                    try:
                        result = func(*args, **kwargs)
                        end_timer(success=True)
                        return result
                    except Exception as e:
                        end_timer(success=False, error=str(e))
                        raise

                return sync_wrapper

        return decorator

    def monitor_operation(self, operation_name: str) -> "OperationMonitor":
        """Monitor operation performance."""
        return OperationMonitor(self.metrics_collector, operation_name)


class OperationMonitor:
    """Context manager for monitoring operations."""

    def __init__(self, metrics_collector: MetricsCollector, operation_name: str) -> None:
        """Initialize operation monitor."""
        self.metrics_collector = metrics_collector
        self.operation_name = operation_name
        self.end_timer: Callable | None = None

    def __enter__(self) -> "OperationMonitor":
        """Start monitoring."""
        self.end_timer = self.metrics_collector.start_timer(self.operation_name)
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, _exc_tb: Any) -> None:
        """End monitoring."""
        if self.end_timer:
            success = exc_type is None
            error = str(exc_val) if exc_val else None
            self.end_timer(success=success, error=error)


# Global metrics collector instance
_metrics_collector: MetricsCollector | None = None
_performance_monitor: PerformanceMonitor | None = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor(get_metrics_collector())
    return _performance_monitor


def monitor_operation(operation_name: str) -> Any:
    """Monitor operation performance."""
    if not is_feature_enabled("monitoring"):
        # Return a no-op context manager if monitoring is disabled
        class NoOpMonitor:
            def __enter__(self) -> "NoOpMonitor":
                return self

            def __exit__(self, *args: Any) -> None:
                pass

        return NoOpMonitor()

    return get_performance_monitor().monitor_operation(operation_name)
