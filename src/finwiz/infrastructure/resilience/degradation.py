"""
Graceful degradation utilities for FinWiz application.

This module provides utilities for handling API failures, rate limits,
and service unavailability with intelligent fallback strategies.
"""

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, cast

from finwiz.config.features.flags import get_feature_flags
from finwiz.infrastructure.caching.manager import get_cache_manager
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class ServiceStatus(StrEnum):
    """Service availability status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    RATE_LIMITED = "rate_limited"
    TIMEOUT = "timeout"


class DegradationLevel(StrEnum):
    """Levels of service degradation."""

    NONE = "none"  # Full functionality
    MINOR = "minor"  # Slight reduction in features
    MODERATE = "moderate"  # Significant feature reduction
    SEVERE = "severe"  # Minimal functionality
    CRITICAL = "critical"  # Emergency mode only


@dataclass
class ServiceHealth:
    """Health status of a service."""

    service_name: str
    status: ServiceStatus
    degradation_level: DegradationLevel = DegradationLevel.NONE
    last_check: float = field(default_factory=time.time)
    error_count: int = 0
    success_count: int = 0
    response_time: float = 0.0
    error_message: str | None = None
    fallback_data: dict[str, Any] | None = None


@dataclass
class DegradationConfig:
    """Configuration for graceful degradation behavior."""

    service_name: str
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout_seconds: float = 30.0
    health_check_interval: int = 300  # 5 minutes
    error_threshold: int = 5
    recovery_threshold: int = 3
    cache_fallback: bool = True
    default_fallback: bool = True
    enable_circuit_breaker: bool = True


class GracefulDegradationManager:
    """
    Manager for graceful degradation across FinWiz services.

    Handles service health monitoring, fallback strategies, and
    intelligent recovery mechanisms.
    """

    def __init__(self) -> None:
        """Initialize graceful degradation manager."""
        self.feature_flags = get_feature_flags()
        self.cache_manager = get_cache_manager()
        self.service_health: dict[str, ServiceHealth] = {}
        self.degradation_configs: dict[str, DegradationConfig] = {}

        # Initialize default service configurations
        self._initialize_default_configs()
        logger.info("Graceful degradation manager initialized")

    def _initialize_default_configs(self) -> None:
        """Initialize default degradation configurations for FinWiz services."""
        default_services = {
            "openai": DegradationConfig(service_name="openai", max_retries=3, retry_delay=2.0, timeout_seconds=60.0, error_threshold=3, recovery_threshold=2),
            "alpha_vantage": DegradationConfig(
                service_name="alpha_vantage",
                max_retries=5,
                retry_delay=1.0,
                timeout_seconds=30.0,
                error_threshold=5,
                recovery_threshold=3,
            ),
            "chart_img": DegradationConfig(
                service_name="chart_img",
                max_retries=2,
                retry_delay=1.5,
                timeout_seconds=45.0,
                error_threshold=3,
                recovery_threshold=2,
                cache_fallback=True,
            ),
            "twelve_data": DegradationConfig(
                service_name="twelve_data",
                max_retries=4,
                retry_delay=2.0,
                timeout_seconds=30.0,
                error_threshold=4,
                recovery_threshold=2,
            ),
            "yahoo_finance": DegradationConfig(
                service_name="yahoo_finance",
                max_retries=3,
                retry_delay=1.0,
                timeout_seconds=20.0,
                error_threshold=5,
                recovery_threshold=3,
            ),
            "coinmarketcap": DegradationConfig(
                service_name="coinmarketcap",
                max_retries=3,
                retry_delay=2.0,
                timeout_seconds=25.0,
                error_threshold=4,
                recovery_threshold=2,
            ),
        }

        self.degradation_configs.update(default_services)

        # Initialize health status for each service
        for service_name in default_services:
            self.service_health[service_name] = ServiceHealth(service_name=service_name, status=ServiceStatus.HEALTHY)

    async def execute_with_degradation(
        self,
        service_name: str,
        primary_func: Callable,
        fallback_func: Callable | None = None,
        cache_key: str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Execute function with graceful degradation support.

        Args:
            service_name: Name of the service being called
            primary_func: Primary function to execute
            fallback_func: Optional fallback function
            cache_key: Optional cache key for fallback data
            *args: Positional arguments for the functions
            **kwargs: Keyword arguments for the functions

        Returns:
            Result from primary function or fallback

        """
        config = self.degradation_configs.get(service_name)
        if not config:
            logger.warning(f"No degradation config for service: {service_name}")
            return await self._execute_primary_function(primary_func, *args, **kwargs)

        health = self.service_health.get(service_name)
        if not health:
            health = ServiceHealth(service_name=service_name, status=ServiceStatus.HEALTHY)
            self.service_health[service_name] = health

        # Check if service is in circuit breaker state
        if health.status == ServiceStatus.UNAVAILABLE and config.enable_circuit_breaker:
            if time.time() - health.last_check < config.health_check_interval:
                logger.info(f"Service {service_name} in circuit breaker state, using fallback")
                return await self._execute_fallback(service_name, fallback_func, cache_key, *args, **kwargs)

        # Attempt primary function with retries
        for attempt in range(config.max_retries + 1):
            try:
                start_time = time.time()

                if asyncio.iscoroutinefunction(primary_func):
                    result = await asyncio.wait_for(primary_func(*args, **kwargs), timeout=config.timeout_seconds)
                else:
                    result = primary_func(*args, **kwargs)

                # Record success
                response_time = time.time() - start_time
                await self._record_success(service_name, response_time)

                # Cache successful result if cache key provided
                if cache_key and result is not None:
                    await self.cache_manager.set(cache_key, result, ttl=1800)  # 30 minutes

                return result

            except TimeoutError:
                logger.warning(f"Timeout for {service_name} on attempt {attempt + 1}")
                await self._record_error(service_name, "Timeout", ServiceStatus.TIMEOUT)

            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Error in {service_name} on attempt {attempt + 1}: {error_msg}")

                # Determine error type
                if "rate limit" in error_msg.lower() or "429" in error_msg:
                    await self._record_error(service_name, error_msg, ServiceStatus.RATE_LIMITED)
                else:
                    await self._record_error(service_name, error_msg, ServiceStatus.UNAVAILABLE)

            # Wait before retry (except on last attempt)
            if attempt < config.max_retries:
                delay = config.retry_delay * (2**attempt)  # Exponential backoff
                logger.info(f"Retrying {service_name} in {delay:.1f} seconds")
                await asyncio.sleep(delay)

        # All attempts failed, use fallback
        logger.error(f"All attempts failed for {service_name}, using fallback")
        return await self._execute_fallback(service_name, fallback_func, cache_key, *args, **kwargs)

    async def _execute_primary_function(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Execute primary function without degradation handling."""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)

    async def _execute_fallback(self, service_name: str, fallback_func: Callable | None, cache_key: str | None, *args: Any, **kwargs: Any) -> Any:
        """Execute fallback strategy for failed service."""
        config = self.degradation_configs.get(service_name)
        if not config:
            return None

        # Try cached data first if enabled
        if config.cache_fallback and cache_key:
            cached_result = await self.cache_manager.get(cache_key)
            if cached_result is not None:
                logger.info(f"Using cached data for {service_name}")
                return cached_result

        # Try custom fallback function
        if fallback_func:
            try:
                if asyncio.iscoroutinefunction(fallback_func):
                    result = await fallback_func(*args, **kwargs)
                else:
                    result = fallback_func(*args, **kwargs)
                logger.info(f"Used custom fallback for {service_name}")
                return result
            except Exception as e:
                logger.error(f"Fallback function failed for {service_name}: {e}")

        # Use default fallback if enabled
        if config.default_fallback:
            default_result = self._get_default_fallback_data(service_name)
            logger.info(f"Using default fallback data for {service_name}")
            return default_result

        logger.warning(f"No fallback available for {service_name}")
        return None

    def _get_default_fallback_data(self, service_name: str) -> dict[str, Any]:
        """Get default fallback data for a service."""
        default_data = {
            "openai": {"choices": [{"message": {"content": "Service temporarily unavailable"}}], "usage": {"total_tokens": 0}},
            "alpha_vantage": {
                "Global Quote": {"01. symbol": "N/A", "05. price": "0.00", "09. change": "0.00", "10. change percent": "0.00%"},
                "status": "fallback",
            },
            "chart_img": {"chart_url": None, "status": "unavailable", "message": "Chart generation temporarily unavailable"},
            "twelve_data": {"values": [], "status": "unavailable", "message": "Technical indicators temporarily unavailable"},
            "yahoo_finance": {
                "symbol": "N/A",
                "regularMarketPrice": 0.0,
                "regularMarketChange": 0.0,
                "regularMarketChangePercent": 0.0,
                "status": "fallback",
            },
            "coinmarketcap": {"data": {}, "status": "unavailable", "message": "Cryptocurrency data temporarily unavailable"},
        }

        return cast(dict[str, Any], default_data.get(service_name, {"status": "unavailable", "data": None}))

    async def _record_success(self, service_name: str, response_time: float) -> None:
        """Record successful service call."""
        health = self.service_health.get(service_name)
        if not health:
            return

        health.success_count += 1
        health.response_time = response_time
        health.last_check = time.time()
        health.error_message = None

        config = self.degradation_configs.get(service_name)
        if config and health.success_count >= config.recovery_threshold:
            if health.status != ServiceStatus.HEALTHY:
                logger.info(f"Service {service_name} recovered to healthy status")
                health.status = ServiceStatus.HEALTHY
                health.degradation_level = DegradationLevel.NONE
                health.error_count = 0

        # Record success in feature flags circuit breaker
        self.feature_flags.record_success(f"{service_name}_integration")

    async def _record_error(self, service_name: str, error_message: str, status: ServiceStatus) -> None:
        """Record service error."""
        health = self.service_health.get(service_name)
        if not health:
            return

        health.error_count += 1
        health.last_check = time.time()
        health.error_message = error_message
        health.success_count = 0  # Reset success count

        config = self.degradation_configs.get(service_name)
        if config and health.error_count >= config.error_threshold:
            if health.status != ServiceStatus.UNAVAILABLE:
                logger.warning(f"Service {service_name} marked as unavailable after {health.error_count} errors")
                health.status = ServiceStatus.UNAVAILABLE
                health.degradation_level = DegradationLevel.SEVERE
        else:
            health.status = status
            health.degradation_level = self._calculate_degradation_level(health.error_count, config)

        # Record failure in feature flags circuit breaker
        self.feature_flags.record_failure(f"{service_name}_integration")

    def _calculate_degradation_level(self, error_count: int, config: DegradationConfig | None) -> DegradationLevel:
        """Calculate degradation level based on error count."""
        if not config:
            return DegradationLevel.MODERATE

        threshold = config.error_threshold

        if error_count == 0:
            return DegradationLevel.NONE
        elif error_count < threshold // 2:
            return DegradationLevel.MINOR
        elif error_count < threshold:
            return DegradationLevel.MODERATE
        else:
            return DegradationLevel.SEVERE

    def get_service_health(self, service_name: str) -> ServiceHealth | None:
        """Get health status for a specific service."""
        return self.service_health.get(service_name)

    def get_all_service_health(self) -> dict[str, ServiceHealth]:
        """Get health status for all services."""
        return self.service_health.copy()

    def get_system_health_summary(self) -> dict[str, Any]:
        """Get comprehensive system health summary."""
        healthy_services = sum(1 for h in self.service_health.values() if h.status == ServiceStatus.HEALTHY)
        total_services = len(self.service_health)

        degradation_levels = [h.degradation_level for h in self.service_health.values()]
        # Find the highest degradation level based on severity order
        degradation_order = [
            DegradationLevel.NONE,
            DegradationLevel.MINOR,
            DegradationLevel.MODERATE,
            DegradationLevel.SEVERE,
            DegradationLevel.CRITICAL,
        ]
        overall_degradation = DegradationLevel.NONE
        if degradation_levels:
            for level in reversed(degradation_order):
                if level in degradation_levels:
                    overall_degradation = level
                    break

        return {
            "overall_health": "healthy" if healthy_services == total_services else "degraded",
            "healthy_services": healthy_services,
            "total_services": total_services,
            "overall_degradation": overall_degradation.value,
            "service_details": {
                name: {
                    "status": health.status.value,
                    "degradation_level": health.degradation_level.value,
                    "error_count": health.error_count,
                    "success_count": health.success_count,
                    "last_check": health.last_check,
                    "response_time": health.response_time,
                }
                for name, health in self.service_health.items()
            },
        }

    async def force_health_check(self, service_name: str) -> ServiceHealth:
        """Force a health check for a specific service."""
        health = self.service_health.get(service_name)
        if not health:
            logger.warning(f"No health record for service: {service_name}")
            return ServiceHealth(service_name=service_name, status=ServiceStatus.UNAVAILABLE)

        # Reset circuit breaker if enough time has passed
        config = self.degradation_configs.get(service_name)
        if config and health.status == ServiceStatus.UNAVAILABLE:
            if time.time() - health.last_check >= config.health_check_interval:
                logger.info(f"Resetting circuit breaker for {service_name}")
                health.status = ServiceStatus.DEGRADED
                health.degradation_level = DegradationLevel.MODERATE
                health.error_count = config.error_threshold // 2

        return health

    def update_service_config(self, service_name: str, **config_updates: Any) -> bool:
        """Update degradation configuration for a service."""
        if service_name not in self.degradation_configs:
            logger.error(f"No configuration found for service: {service_name}")
            return False

        config = self.degradation_configs[service_name]
        for key, value in config_updates.items():
            if hasattr(config, key):
                setattr(config, key, value)
                logger.info(f"Updated {service_name}.{key} to {value}")
            else:
                logger.warning(f"Unknown config key for {service_name}: {key}")

        return True


# Global graceful degradation manager instance
_degradation_manager: GracefulDegradationManager | None = None


def get_degradation_manager() -> GracefulDegradationManager:
    """Get the global graceful degradation manager instance."""
    global _degradation_manager
    if _degradation_manager is None:
        _degradation_manager = GracefulDegradationManager()
    return _degradation_manager


async def execute_with_degradation(
    service_name: str,
    primary_func: Callable,
    fallback_func: Callable | None = None,
    cache_key: str | None = None,
    *args: Any,
    **kwargs: Any,
) -> Any:
    """Execute with graceful degradation."""
    manager = get_degradation_manager()
    return await manager.execute_with_degradation(service_name, primary_func, fallback_func, cache_key, *args, **kwargs)
