"""
Monitoring utilities for Supabase database operations.

Provides comprehensive monitoring and observability for:
- Connection pool health and utilization
- Operation duration tracking with configurable thresholds
- Cache hit/miss rate tracking
- Circuit breaker state monitoring
- Connection pool metrics (size, utilization, wait times)
- Pool utilization alerts (warn when >80%)
- Metrics export for external monitoring systems
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from finwiz.supabase.circuit_breaker import CircuitState

logger = logging.getLogger(__name__)


class OperationType(Enum):
    """Types of database operations for metrics tracking."""

    READ = "read"
    WRITE = "write"
    CACHE_CHECK = "cache_check"
    VECTOR_SEARCH = "vector_search"
    EMBEDDING_GENERATION = "embedding_generation"


@dataclass
class OperationMetrics:
    """Metrics for a specific operation type."""

    operation_type: OperationType
    total_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    timeout_count: int = 0
    total_duration_ms: float = 0.0
    min_duration_ms: float = float('inf')
    max_duration_ms: float = 0.0
    durations: list[float] = field(default_factory=list)
    max_durations: int = 100  # Keep last 100 durations

    def record_success(self, duration_ms: float) -> None:
        """
        Record successful operation.

        Args:
            duration_ms: Operation duration in milliseconds

        """
        self.total_count += 1
        self.success_count += 1
        self._record_duration(duration_ms)

    def record_failure(self, duration_ms: float | None = None) -> None:
        """
        Record failed operation.

        Args:
            duration_ms: Operation duration in milliseconds (if available)

        """
        self.total_count += 1
        self.failure_count += 1
        if duration_ms is not None:
            self._record_duration(duration_ms)

    def record_timeout(self, duration_ms: float) -> None:
        """
        Record timeout operation.

        Args:
            duration_ms: Operation duration in milliseconds

        """
        self.total_count += 1
        self.timeout_count += 1
        self._record_duration(duration_ms)

    def _record_duration(self, duration_ms: float) -> None:
        """
        Record operation duration.

        Args:
            duration_ms: Operation duration in milliseconds

        """
        self.total_duration_ms += duration_ms
        self.min_duration_ms = min(self.min_duration_ms, duration_ms)
        self.max_duration_ms = max(self.max_duration_ms, duration_ms)

        # Keep rolling window of recent durations
        self.durations.append(duration_ms)
        if len(self.durations) > self.max_durations:
            self.durations.pop(0)

    @property
    def avg_duration_ms(self) -> float:
        """Calculate average duration."""
        if not self.durations:
            return 0.0
        return sum(self.durations) / len(self.durations)

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_count == 0:
            return 0.0
        return self.success_count / self.total_count

    @property
    def failure_rate(self) -> float:
        """Calculate failure rate."""
        if self.total_count == 0:
            return 0.0
        return self.failure_count / self.total_count

    @property
    def timeout_rate(self) -> float:
        """Calculate timeout rate."""
        if self.total_count == 0:
            return 0.0
        return self.timeout_count / self.total_count


@dataclass
class CacheMetrics:
    """Metrics for cache operations."""

    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    cache_timeouts: int = 0
    cache_errors: int = 0

    def record_hit(self) -> None:
        """Record cache hit."""
        self.total_requests += 1
        self.cache_hits += 1

    def record_miss(self) -> None:
        """Record cache miss."""
        self.total_requests += 1
        self.cache_misses += 1

    def record_timeout(self) -> None:
        """Record cache timeout."""
        self.total_requests += 1
        self.cache_timeouts += 1

    def record_error(self) -> None:
        """Record cache error."""
        self.total_requests += 1
        self.cache_errors += 1

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        if self.total_requests == 0:
            return 0.0
        return self.cache_hits / self.total_requests

    @property
    def miss_rate(self) -> float:
        """Calculate cache miss rate."""
        if self.total_requests == 0:
            return 0.0
        return self.cache_misses / self.total_requests

    @property
    def timeout_rate(self) -> float:
        """Calculate cache timeout rate."""
        if self.total_requests == 0:
            return 0.0
        return self.cache_timeouts / self.total_requests

    @property
    def error_rate(self) -> float:
        """Calculate cache error rate."""
        if self.total_requests == 0:
            return 0.0
        return self.cache_errors / self.total_requests


@dataclass
class PoolMetrics:
    """Metrics for connection pool operations."""

    acquisitions: int = 0
    releases: int = 0
    acquisition_timeouts: int = 0
    acquisition_failures: int = 0
    acquisition_times: list[float] = field(default_factory=list)
    max_acquisition_times: int = 100  # Keep last 100 acquisition times

    def record_acquisition(self, duration_ms: float) -> None:
        """
        Record successful connection acquisition.

        Args:
            duration_ms: Acquisition duration in milliseconds

        """
        self.acquisitions += 1
        self.acquisition_times.append(duration_ms)
        if len(self.acquisition_times) > self.max_acquisition_times:
            self.acquisition_times.pop(0)

    def record_release(self) -> None:
        """Record connection release."""
        self.releases += 1

    def record_timeout(self) -> None:
        """Record acquisition timeout."""
        self.acquisition_timeouts += 1

    def record_failure(self) -> None:
        """Record acquisition failure."""
        self.acquisition_failures += 1

    @property
    def avg_acquisition_time_ms(self) -> float:
        """Calculate average acquisition time."""
        if not self.acquisition_times:
            return 0.0
        return sum(self.acquisition_times) / len(self.acquisition_times)

    @property
    def timeout_rate(self) -> float:
        """Calculate acquisition timeout rate."""
        total_attempts = self.acquisitions + self.acquisition_timeouts + self.acquisition_failures
        if total_attempts == 0:
            return 0.0
        return self.acquisition_timeouts / total_attempts


class PerformanceMonitor:
    """
    Monitor database operation performance.

    Tracks operation durations and alerts when thresholds are exceeded.
    """

    def __init__(
        self,
        read_threshold_ms: float = 2000.0,
        write_threshold_ms: float = 5000.0,
        cache_threshold_ms: float = 2000.0,
        vector_search_threshold_ms: float = 1000.0,
    ) -> None:
        """
        Initialize performance monitor.

        Args:
            read_threshold_ms: Threshold for read operations in milliseconds
            write_threshold_ms: Threshold for write operations in milliseconds
            cache_threshold_ms: Threshold for cache operations in milliseconds
            vector_search_threshold_ms: Threshold for vector search in milliseconds

        """
        self.thresholds = {
            OperationType.READ: read_threshold_ms,
            OperationType.WRITE: write_threshold_ms,
            OperationType.CACHE_CHECK: cache_threshold_ms,
            OperationType.VECTOR_SEARCH: vector_search_threshold_ms,
        }
        self.metrics: dict[OperationType, OperationMetrics] = {
            op_type: OperationMetrics(operation_type=op_type)
            for op_type in OperationType
        }

    def record_operation(
        self,
        operation_type: OperationType,
        duration_ms: float,
        success: bool = True,
        timeout: bool = False,
    ) -> None:
        """
        Record operation metrics.

        Args:
            operation_type: Type of operation
            duration_ms: Operation duration in milliseconds
            success: Whether operation succeeded
            timeout: Whether operation timed out

        """
        metrics = self.metrics[operation_type]

        if timeout:
            metrics.record_timeout(duration_ms)
        elif success:
            metrics.record_success(duration_ms)
        else:
            metrics.record_failure(duration_ms)

        # Check threshold and log warning if exceeded
        threshold = self.thresholds.get(operation_type)
        if threshold and duration_ms > threshold:
            logger.warning(
                f"⚠️ {operation_type.value} operation exceeded threshold: "
                f"{duration_ms:.1f}ms > {threshold:.1f}ms "
                f"(avg: {metrics.avg_duration_ms:.1f}ms, "
                f"success rate: {metrics.success_rate:.1%})"
            )

    def get_metrics(self, operation_type: OperationType) -> OperationMetrics:
        """
        Get metrics for specific operation type.

        Args:
            operation_type: Type of operation

        Returns:
            Operation metrics

        """
        return self.metrics[operation_type]

    def get_all_metrics(self) -> dict[OperationType, OperationMetrics]:
        """
        Get all operation metrics.

        Returns:
            Dictionary of operation type to metrics

        """
        return self.metrics.copy()

    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self.metrics = {
            op_type: OperationMetrics(operation_type=op_type)
            for op_type in OperationType
        }
        logger.debug("Performance metrics reset")


class PoolMonitor:
    """
    Monitor connection pool health and performance.

    Tracks pool utilization, connection acquisition times, and alerts
    when utilization exceeds thresholds.
    """

    def __init__(
        self,
        utilization_warning_threshold: float = 0.80,
        utilization_critical_threshold: float = 0.95,
    ) -> None:
        """
        Initialize pool monitor.

        Args:
            utilization_warning_threshold: Threshold for warning alerts (default: 80%)
            utilization_critical_threshold: Threshold for critical alerts (default: 95%)

        """
        self.utilization_warning_threshold = utilization_warning_threshold
        self.utilization_critical_threshold = utilization_critical_threshold
        self.pool_metrics = PoolMetrics()
        self.last_stats: dict[str, Any] = {}

    async def log_pool_stats(self, client: Any) -> None:
        """
        Log current pool statistics.

        Args:
            client: SupabaseClient instance

        """
        stats = await client.get_pool_stats()

        if stats["status"] == "disabled":
            logger.debug("Connection pool is disabled")
            return

        # Calculate utilization
        size = stats["size"]
        free_size = stats["free_size"]
        max_size = stats["max_size"]
        utilization = (size - free_size) / max_size if max_size > 0 else 0.0

        # Store stats for metrics export
        self.last_stats = {
            **stats,
            "utilization": utilization,
            "active_connections": size - free_size,
        }

        # Log stats
        logger.info(
            f"📊 Connection Pool Stats: "
            f"size={size}/{max_size}, "
            f"free={free_size}, "
            f"utilization={utilization:.1%}, "
            f"idle_timeout={stats['idle_timeout']}s"
        )

        # Alert if utilization is high
        if utilization >= self.utilization_critical_threshold:
            logger.error(
                f"🚨 CRITICAL: Connection pool utilization very high: {utilization:.1%} "
                f"(threshold: {self.utilization_critical_threshold:.1%})"
            )
        elif utilization >= self.utilization_warning_threshold:
            logger.warning(
                f"⚠️ WARNING: Connection pool utilization high: {utilization:.1%} "
                f"(threshold: {self.utilization_warning_threshold:.1%})"
            )

    def record_acquisition(self, duration_ms: float) -> None:
        """
        Record connection acquisition.

        Args:
            duration_ms: Acquisition duration in milliseconds

        """
        self.pool_metrics.record_acquisition(duration_ms)

    def record_release(self) -> None:
        """Record connection release."""
        self.pool_metrics.record_release()

    def record_timeout(self) -> None:
        """Record acquisition timeout."""
        self.pool_metrics.record_timeout()

    def record_failure(self) -> None:
        """Record acquisition failure."""
        self.pool_metrics.record_failure()

    def get_metrics(self) -> PoolMetrics:
        """
        Get pool metrics.

        Returns:
            Pool metrics

        """
        return self.pool_metrics

    def get_pool_stats(self) -> dict[str, Any]:
        """
        Get last recorded pool stats.

        Returns:
            Dictionary with pool statistics

        """
        return self.last_stats.copy()

    def reset_metrics(self) -> None:
        """Reset pool metrics."""
        self.pool_metrics = PoolMetrics()
        logger.debug("Pool metrics reset")


class CircuitBreakerMonitor:
    """
    Monitor circuit breaker state changes.

    Tracks state transitions and logs alerts when circuit breaker opens.
    """

    def __init__(self) -> None:
        """Initialize circuit breaker monitor."""
        self.state_changes: list[tuple[datetime, CircuitState, CircuitState]] = []
        self.current_state: CircuitState = CircuitState.CLOSED
        self.open_count: int = 0
        self.half_open_count: int = 0
        self.closed_count: int = 0

    def record_state_change(
        self,
        old_state: CircuitState,
        new_state: CircuitState,
    ) -> None:
        """
        Record circuit breaker state change.

        Args:
            old_state: Previous state
            new_state: New state

        """
        timestamp = datetime.now()
        self.state_changes.append((timestamp, old_state, new_state))
        self.current_state = new_state

        # Update counters
        if new_state == CircuitState.OPEN:
            self.open_count += 1
            logger.error(
                f"🚨 Circuit breaker OPENED: {old_state.value} → {new_state.value} "
                f"(total opens: {self.open_count})"
            )
        elif new_state == CircuitState.HALF_OPEN:
            self.half_open_count += 1
            logger.warning(
                f"⚠️ Circuit breaker HALF-OPEN: {old_state.value} → {new_state.value} "
                f"(attempting recovery)"
            )
        elif new_state == CircuitState.CLOSED:
            self.closed_count += 1
            if old_state != CircuitState.CLOSED:
                logger.info(
                    f"✅ Circuit breaker CLOSED: {old_state.value} → {new_state.value} "
                    f"(recovery successful)"
                )

    def get_current_state(self) -> CircuitState:
        """
        Get current circuit breaker state.

        Returns:
            Current state

        """
        return self.current_state

    def get_state_history(self) -> list[tuple[datetime, CircuitState, CircuitState]]:
        """
        Get state change history.

        Returns:
            List of (timestamp, old_state, new_state) tuples

        """
        return self.state_changes.copy()

    def get_metrics(self) -> dict[str, Any]:
        """
        Get circuit breaker metrics.

        Returns:
            Dictionary with metrics

        """
        return {
            "current_state": self.current_state.value,
            "open_count": self.open_count,
            "half_open_count": self.half_open_count,
            "closed_count": self.closed_count,
            "total_state_changes": len(self.state_changes),
        }

    def reset_metrics(self) -> None:
        """Reset circuit breaker metrics."""
        self.state_changes = []
        self.open_count = 0
        self.half_open_count = 0
        self.closed_count = 0
        logger.debug("Circuit breaker metrics reset")


class MetricsExporter:
    """
    Export metrics for external monitoring systems.

    Provides metrics in a format suitable for Prometheus, Grafana, or other
    monitoring systems.
    """

    def __init__(
        self,
        performance_monitor: PerformanceMonitor,
        pool_monitor: PoolMonitor,
        circuit_breaker_monitor: CircuitBreakerMonitor,
        cache_metrics: CacheMetrics,
    ) -> None:
        """
        Initialize metrics exporter.

        Args:
            performance_monitor: Performance monitor instance
            pool_monitor: Pool monitor instance
            circuit_breaker_monitor: Circuit breaker monitor instance
            cache_metrics: Cache metrics instance

        """
        self.performance_monitor = performance_monitor
        self.pool_monitor = pool_monitor
        self.circuit_breaker_monitor = circuit_breaker_monitor
        self.cache_metrics = cache_metrics

    def export_metrics(self) -> dict[str, Any]:
        """
        Export all metrics.

        Returns:
            Dictionary with all metrics in exportable format

        """
        return {
            "timestamp": datetime.now().isoformat(),
            "performance": self._export_performance_metrics(),
            "pool": self._export_pool_metrics(),
            "circuit_breaker": self._export_circuit_breaker_metrics(),
            "cache": self._export_cache_metrics(),
        }

    def _export_performance_metrics(self) -> dict[str, Any]:
        """Export performance metrics."""
        metrics = {}
        for op_type, op_metrics in self.performance_monitor.get_all_metrics().items():
            metrics[op_type.value] = {
                "total_count": op_metrics.total_count,
                "success_count": op_metrics.success_count,
                "failure_count": op_metrics.failure_count,
                "timeout_count": op_metrics.timeout_count,
                "success_rate": op_metrics.success_rate,
                "failure_rate": op_metrics.failure_rate,
                "timeout_rate": op_metrics.timeout_rate,
                "avg_duration_ms": op_metrics.avg_duration_ms,
                "min_duration_ms": op_metrics.min_duration_ms if op_metrics.min_duration_ms != float('inf') else 0.0,
                "max_duration_ms": op_metrics.max_duration_ms,
            }
        return metrics

    def _export_pool_metrics(self) -> dict[str, Any]:
        """Export pool metrics."""
        pool_metrics = self.pool_monitor.get_metrics()
        pool_stats = self.pool_monitor.get_pool_stats()

        return {
            "acquisitions": pool_metrics.acquisitions,
            "releases": pool_metrics.releases,
            "acquisition_timeouts": pool_metrics.acquisition_timeouts,
            "acquisition_failures": pool_metrics.acquisition_failures,
            "avg_acquisition_time_ms": pool_metrics.avg_acquisition_time_ms,
            "timeout_rate": pool_metrics.timeout_rate,
            **pool_stats,
        }

    def _export_circuit_breaker_metrics(self) -> dict[str, Any]:
        """Export circuit breaker metrics."""
        return self.circuit_breaker_monitor.get_metrics()

    def _export_cache_metrics(self) -> dict[str, Any]:
        """Export cache metrics."""
        return {
            "total_requests": self.cache_metrics.total_requests,
            "cache_hits": self.cache_metrics.cache_hits,
            "cache_misses": self.cache_metrics.cache_misses,
            "cache_timeouts": self.cache_metrics.cache_timeouts,
            "cache_errors": self.cache_metrics.cache_errors,
            "hit_rate": self.cache_metrics.hit_rate,
            "miss_rate": self.cache_metrics.miss_rate,
            "timeout_rate": self.cache_metrics.timeout_rate,
            "error_rate": self.cache_metrics.error_rate,
        }

    def export_prometheus_format(self) -> str:
        """
        Export metrics in Prometheus format.

        Returns:
            Metrics in Prometheus text format

        """
        lines = []
        metrics = self.export_metrics()

        # Performance metrics
        for op_type, op_metrics in metrics["performance"].items():
            prefix = f"supabase_{op_type}"
            lines.append(f"{prefix}_total {op_metrics['total_count']}")
            lines.append(f"{prefix}_success {op_metrics['success_count']}")
            lines.append(f"{prefix}_failure {op_metrics['failure_count']}")
            lines.append(f"{prefix}_timeout {op_metrics['timeout_count']}")
            lines.append(f"{prefix}_success_rate {op_metrics['success_rate']}")
            lines.append(f"{prefix}_avg_duration_ms {op_metrics['avg_duration_ms']}")

        # Pool metrics
        pool = metrics["pool"]
        lines.append(f"supabase_pool_acquisitions {pool['acquisitions']}")
        lines.append(f"supabase_pool_releases {pool['releases']}")
        lines.append(f"supabase_pool_timeouts {pool['acquisition_timeouts']}")
        lines.append(f"supabase_pool_failures {pool['acquisition_failures']}")
        if "utilization" in pool:
            lines.append(f"supabase_pool_utilization {pool['utilization']}")

        # Circuit breaker metrics
        cb = metrics["circuit_breaker"]
        lines.append(f"supabase_circuit_breaker_open_count {cb['open_count']}")
        lines.append(f"supabase_circuit_breaker_state {{state=\"{cb['current_state']}\"}} 1")

        # Cache metrics
        cache = metrics["cache"]
        lines.append(f"supabase_cache_requests_total {cache['total_requests']}")
        lines.append(f"supabase_cache_hits {cache['cache_hits']}")
        lines.append(f"supabase_cache_misses {cache['cache_misses']}")
        lines.append(f"supabase_cache_hit_rate {cache['hit_rate']}")

        return "\n".join(lines)
