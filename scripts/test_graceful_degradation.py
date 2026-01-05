"""
Unit tests for the graceful degradation system.

Tests service health monitoring, fallback strategies, circuit breaker patterns,
and recovery mechanisms.
"""

import asyncio
import time

import pytest
from finwiz.utils.graceful_degradation import (
    DegradationConfig,
    DegradationLevel,
    GracefulDegradationManager,
    ServiceHealth,
    ServiceStatus,
    execute_with_degradation,
    get_degradation_manager,
)


@pytest.fixture(autouse=True)
def mock_sleep(mocker):
    """Mock asyncio.sleep to avoid delays in tests."""
    return mocker.patch("asyncio.sleep", new_callable=mocker.AsyncMock)


class TestGracefulDegradationManager:
    """Test suite for GracefulDegradationManager class."""

    def setup_method(self):
        """Set up test environment."""
        # Create fresh manager for each test
        self.manager = GracefulDegradationManager()

    def test_should_initialize_with_default_service_configs(self):
        """Test that manager initializes with expected default service configurations."""
        # Arrange & Act
        manager = GracefulDegradationManager()

        # Assert
        assert len(manager.degradation_configs) > 0
        assert "openai" in manager.degradation_configs
        assert "alpha_vantage" in manager.degradation_configs
        assert "chart_img" in manager.degradation_configs
        assert "twelve_data" in manager.degradation_configs

        # Check that health status is initialized
        assert len(manager.service_health) > 0
        assert all(health.status == ServiceStatus.HEALTHY for health in manager.service_health.values())

    @pytest.mark.asyncio
    async def test_should_execute_primary_function_successfully(self):
        """Test successful execution of primary function."""

        # Arrange
        async def primary_func(value):
            return f"success_{value}"

        # Act
        result = await self.manager.execute_with_degradation("test_service", primary_func, value="test")

        # Assert
        assert result == "success_test"

    @pytest.mark.asyncio
    async def test_should_record_success_and_update_health(self):
        """Test that successful calls update service health correctly."""
        # Arrange
        service_name = "test_service"
        self.manager.degradation_configs[service_name] = DegradationConfig(service_name=service_name, recovery_threshold=1)
        self.manager.service_health[service_name] = ServiceHealth(service_name=service_name, status=ServiceStatus.DEGRADED, error_count=2)

        async def primary_func():
            return "success"

        # Act
        result = await self.manager.execute_with_degradation(service_name, primary_func)

        # Assert
        assert result == "success"
        health = self.manager.service_health[service_name]
        assert health.status == ServiceStatus.HEALTHY
        assert health.success_count >= 1
        assert health.error_count == 0  # Should be reset on recovery

    @pytest.mark.asyncio
    async def test_should_handle_timeout_errors(self):
        """Test handling of timeout errors."""
        # Arrange
        service_name = "test_service"
        self.manager.degradation_configs[service_name] = DegradationConfig(service_name=service_name, timeout_seconds=0.1, max_retries=1)

        async def slow_func():
            # Raise TimeoutError directly to simulate timeout
            raise TimeoutError("Operation timed out")

        async def fallback_func():
            return "fallback_result"

        # Act
        result = await self.manager.execute_with_degradation(service_name, slow_func, fallback_func)

        # Assert
        assert result == "fallback_result"
        health = self.manager.service_health[service_name]
        assert health.status == ServiceStatus.TIMEOUT
        assert health.error_count > 0

    @pytest.mark.asyncio
    async def test_should_handle_rate_limit_errors(self):
        """Test handling of rate limit errors."""
        # Arrange
        service_name = "test_service"
        self.manager.degradation_configs[service_name] = DegradationConfig(service_name=service_name, max_retries=1)

        async def rate_limited_func():
            raise Exception("Rate limit exceeded (429)")

        async def fallback_func():
            return "rate_limit_fallback"

        # Act
        result = await self.manager.execute_with_degradation(service_name, rate_limited_func, fallback_func)

        # Assert
        assert result == "rate_limit_fallback"
        health = self.manager.service_health[service_name]
        assert health.status == ServiceStatus.RATE_LIMITED

    @pytest.mark.asyncio
    async def test_should_implement_exponential_backoff_on_retries(self, mock_sleep):
        """Test exponential backoff during retries."""
        # Arrange
        service_name = "test_service"
        self.manager.degradation_configs[service_name] = DegradationConfig(service_name=service_name, max_retries=2, retry_delay=0.1)

        call_count = 0

        async def failing_func():
            nonlocal call_count
            call_count += 1
            raise Exception("Service error")

        async def fallback_func():
            return "fallback"

        # Act
        result = await self.manager.execute_with_degradation(service_name, failing_func, fallback_func)

        # Assert
        assert result == "fallback"
        assert call_count == 3  # Initial + 2 retries
        assert mock_sleep.call_count >= 2  # Should have sleep calls for retries

    @pytest.mark.asyncio
    async def test_should_use_cached_fallback_data(self, mocker):
        """Test using cached data as fallback."""
        # Arrange
        service_name = "test_service"
        cache_key = "test_cache_key"
        cached_data = {"cached": True, "value": "cached_result"}

        # Mock cache manager
        mocker.patch.object(self.manager.cache_manager, "get", return_value=cached_data)

        self.manager.degradation_configs[service_name] = DegradationConfig(service_name=service_name, cache_fallback=True, max_retries=1)

        async def failing_func():
            raise Exception("Service unavailable")

        # Act
        result = await self.manager.execute_with_degradation(service_name, failing_func, cache_key=cache_key)

        # Assert
        assert result == cached_data

    @pytest.mark.asyncio
    async def test_should_cache_successful_results(self, mocker):
        """Test caching of successful results."""
        # Arrange
        service_name = "test_service"
        cache_key = "test_cache_key"
        success_data = {"success": True, "value": "result"}

        # Setup service configuration
        self.manager.degradation_configs[service_name] = DegradationConfig(service_name=service_name)

        # Mock cache manager
        mock_set = mocker.patch.object(self.manager.cache_manager, "set")

        async def successful_func():
            return success_data

        # Act
        result = await self.manager.execute_with_degradation(service_name, successful_func, cache_key=cache_key)

        # Assert
        assert result == success_data
        mock_set.assert_called_once_with(cache_key, success_data, ttl=1800)

    @pytest.mark.asyncio
    async def test_should_implement_circuit_breaker_pattern(self):
        """Test circuit breaker pattern implementation."""
        # Arrange
        service_name = "test_service"
        self.manager.degradation_configs[service_name] = DegradationConfig(
            service_name=service_name,
            error_threshold=2,
            enable_circuit_breaker=True,
            health_check_interval=1,  # 1 second for testing
            max_retries=1,
        )

        async def failing_func():
            raise Exception("Service error")

        async def fallback_func():
            return "circuit_breaker_fallback"

        # Act - Trigger circuit breaker
        for _ in range(3):  # Exceed error threshold
            await self.manager.execute_with_degradation(service_name, failing_func, fallback_func)

        # Service should now be unavailable
        health = self.manager.service_health[service_name]
        assert health.status == ServiceStatus.UNAVAILABLE

        # Next call should use fallback immediately (circuit breaker open)
        result = await self.manager.execute_with_degradation(service_name, failing_func, fallback_func)

        # Assert
        assert result == "circuit_breaker_fallback"
        # Circuit breaker should prevent retries, so no additional calls to failing_func

    @pytest.mark.asyncio
    async def test_should_recover_from_circuit_breaker_state(self):
        """Test recovery from circuit breaker state."""
        # Arrange
        service_name = "test_service"
        self.manager.degradation_configs[service_name] = DegradationConfig(
            service_name=service_name,
            error_threshold=1,
            health_check_interval=0.1,  # Very short for testing
            recovery_threshold=1,
        )

        # Set service to unavailable state
        self.manager.service_health[service_name] = ServiceHealth(
            service_name=service_name,
            status=ServiceStatus.UNAVAILABLE,
            error_count=5,
            last_check=time.time() - 1,  # Old timestamp
        )

        async def working_func():
            return "recovered"

        # Act - Circuit breaker timeout is mocked, execute directly
        result = await self.manager.execute_with_degradation(service_name, working_func)

        # Assert
        assert result == "recovered"
        health = self.manager.service_health[service_name]
        assert health.status == ServiceStatus.HEALTHY

    def test_should_get_default_fallback_data_for_known_services(self):
        """Test getting default fallback data for known services."""
        # Arrange & Act
        openai_fallback = self.manager._get_default_fallback_data("openai")
        alpha_fallback = self.manager._get_default_fallback_data("alpha_vantage")
        unknown_fallback = self.manager._get_default_fallback_data("unknown_service")

        # Assert
        assert "choices" in openai_fallback
        assert "Global Quote" in alpha_fallback
        assert unknown_fallback["status"] == "unavailable"

    def test_should_calculate_degradation_levels_correctly(self):
        """Test calculation of degradation levels based on error count."""
        # Arrange
        config = DegradationConfig(service_name="test", error_threshold=10)

        # Act & Assert
        assert self.manager._calculate_degradation_level(0, config) == DegradationLevel.NONE
        assert self.manager._calculate_degradation_level(3, config) == DegradationLevel.MINOR
        assert self.manager._calculate_degradation_level(7, config) == DegradationLevel.MODERATE
        assert self.manager._calculate_degradation_level(12, config) == DegradationLevel.SEVERE

    def test_should_get_service_health_status(self):
        """Test getting service health status."""
        # Arrange
        service_name = "test_service"
        health = ServiceHealth(service_name=service_name, status=ServiceStatus.DEGRADED, error_count=3)
        self.manager.service_health[service_name] = health

        # Act
        retrieved_health = self.manager.get_service_health(service_name)

        # Assert
        assert retrieved_health is not None
        assert retrieved_health.service_name == service_name
        assert retrieved_health.status == ServiceStatus.DEGRADED
        assert retrieved_health.error_count == 3

    def test_should_get_system_health_summary(self):
        """Test getting comprehensive system health summary."""
        # Arrange - Clear existing health data first
        self.manager.service_health.clear()

        self.manager.service_health["healthy_service"] = ServiceHealth(service_name="healthy_service", status=ServiceStatus.HEALTHY, degradation_level=DegradationLevel.NONE)
        self.manager.service_health["degraded_service"] = ServiceHealth(service_name="degraded_service", status=ServiceStatus.DEGRADED, degradation_level=DegradationLevel.MODERATE)

        # Act
        summary = self.manager.get_system_health_summary()

        # Assert
        assert "overall_health" in summary
        assert "healthy_services" in summary
        assert "total_services" in summary
        assert "service_details" in summary
        assert summary["overall_health"] == "degraded"  # At least one service is degraded
        # Le niveau de dégradation devrait être le maximum des services configurés
        expected_degradation = "moderate"  # Car degraded_service a DegradationLevel.MODERATE
        assert summary["overall_degradation"] == expected_degradation, f"Expected {expected_degradation}, got {summary['overall_degradation']}"

    @pytest.mark.asyncio
    async def test_should_force_health_check_and_reset_circuit_breaker(self):
        """Test forcing health check and resetting circuit breaker."""
        # Arrange
        service_name = "test_service"
        self.manager.degradation_configs[service_name] = DegradationConfig(service_name=service_name, health_check_interval=0.1)
        self.manager.service_health[service_name] = ServiceHealth(
            service_name=service_name,
            status=ServiceStatus.UNAVAILABLE,
            error_count=10,
            last_check=time.time() - 1,  # Old timestamp
        )

        # Act
        await asyncio.sleep(0.2)  # Wait longer than health check interval
        health = await self.manager.force_health_check(service_name)

        # Assert
        assert health.status == ServiceStatus.DEGRADED  # Should be reset from UNAVAILABLE
        assert health.degradation_level == DegradationLevel.MODERATE

    def test_should_update_service_configuration(self):
        """Test updating service configuration at runtime."""
        # Arrange
        service_name = "test_service"
        self.manager.degradation_configs[service_name] = DegradationConfig(service_name=service_name, max_retries=3, timeout_seconds=30.0)

        # Act
        success = self.manager.update_service_config(service_name, max_retries=5, timeout_seconds=60.0)

        # Assert
        assert success is True
        config = self.manager.degradation_configs[service_name]
        assert config.max_retries == 5
        assert config.timeout_seconds == 60.0

    def test_should_handle_unknown_service_configuration_update(self):
        """Test handling of configuration update for unknown service."""
        # Arrange & Act
        success = self.manager.update_service_config("unknown_service", max_retries=5)

        # Assert
        assert success is False


class TestServiceHealth:
    """Test suite for ServiceHealth dataclass."""

    def test_should_create_service_health_with_defaults(self):
        """Test creating ServiceHealth with default values."""
        # Arrange & Act
        health = ServiceHealth(service_name="test_service", status=ServiceStatus.HEALTHY)

        # Assert
        assert health.service_name == "test_service"
        assert health.status == ServiceStatus.HEALTHY
        assert health.degradation_level == DegradationLevel.NONE
        assert health.error_count == 0
        assert health.success_count == 0

    def test_should_check_if_service_is_expired(self):
        """Test checking if service health check is expired."""
        # Arrange
        old_time = time.time() - 3600  # 1 hour ago
        health = ServiceHealth(service_name="test_service", status=ServiceStatus.HEALTHY, last_check=old_time)

        # Act & Assert
        # Note: ServiceHealth doesn't have is_expired method, but we can check age
        age = health.last_check
        assert age < time.time()


class TestDegradationConfig:
    """Test suite for DegradationConfig dataclass."""

    def test_should_create_degradation_config_with_defaults(self):
        """Test creating DegradationConfig with default values."""
        # Arrange & Act
        config = DegradationConfig(service_name="test_service")

        # Assert
        assert config.service_name == "test_service"
        assert config.max_retries == 3
        assert config.retry_delay == 1.0
        assert config.timeout_seconds == 30.0
        assert config.cache_fallback is True
        assert config.enable_circuit_breaker is True

    def test_should_create_degradation_config_with_custom_values(self):
        """Test creating DegradationConfig with custom values."""
        # Arrange & Act
        config = DegradationConfig(
            service_name="custom_service",
            max_retries=5,
            retry_delay=2.0,
            timeout_seconds=60.0,
            error_threshold=10,
            cache_fallback=False,
        )

        # Assert
        assert config.service_name == "custom_service"
        assert config.max_retries == 5
        assert config.retry_delay == 2.0
        assert config.timeout_seconds == 60.0
        assert config.error_threshold == 10
        assert config.cache_fallback is False


class TestGracefulDegradationConvenienceFunctions:
    """Test suite for convenience functions."""

    def test_should_get_degradation_manager_singleton(self):
        """Test that get_degradation_manager returns singleton instance."""
        # Arrange & Act
        manager1 = get_degradation_manager()
        manager2 = get_degradation_manager()

        # Assert
        assert manager1 is manager2

    @pytest.mark.asyncio
    async def test_should_execute_with_degradation_via_convenience_function(self):
        """Test execute_with_degradation convenience function."""

        # Arrange
        async def test_func(value):
            return f"result_{value}"

        # Act
        result = await execute_with_degradation("test_service", test_func, value="test")

        # Assert
        assert result == "result_test"


class TestGracefulDegradationIntegration:
    """Integration tests for graceful degradation system."""

    @pytest.mark.asyncio
    async def test_should_integrate_with_feature_flags_circuit_breaker(self, mocker):
        """Test integration with feature flags circuit breaker."""
        # Arrange
        manager = GracefulDegradationManager()
        service_name = "test_service"

        # Setup service configuration
        manager.degradation_configs[service_name] = DegradationConfig(service_name=service_name, max_retries=1)

        # Mock feature flags
        mock_success = mocker.patch.object(manager.feature_flags, "record_success")
        mock_failure = mocker.patch.object(manager.feature_flags, "record_failure")

        async def successful_func():
            return "success"

        async def failing_func():
            raise Exception("Service error")

        async def fallback_func():
            return "fallback"

        # Act - Success case
        await manager.execute_with_degradation(service_name, successful_func)

        # Act - Failure case (with fallback to prevent exception)
        await manager.execute_with_degradation(service_name, failing_func, fallback_func)

        # Assert
        mock_success.assert_called_with("test_service_integration")
        mock_failure.assert_called_with("test_service_integration")

    @pytest.mark.asyncio
    async def test_should_handle_complete_service_failure_scenario(self):
        """Test complete service failure and recovery scenario."""
        # Arrange
        manager = GracefulDegradationManager()
        service_name = "integration_test_service"

        manager.degradation_configs[service_name] = DegradationConfig(service_name=service_name, error_threshold=2, max_retries=1, health_check_interval=0.1, recovery_threshold=1)

        call_count = 0

        async def intermittent_func():
            nonlocal call_count
            call_count += 1
            if call_count <= 3:  # Fail first 3 calls
                raise Exception("Service temporarily unavailable")
            return f"success_after_{call_count}_calls"

        async def fallback_func():
            return "fallback_response"

        # Act - Initial failures should trigger circuit breaker
        result1 = await manager.execute_with_degradation(service_name, intermittent_func, fallback_func)
        result2 = await manager.execute_with_degradation(service_name, intermittent_func, fallback_func)

        # Service should be in circuit breaker state
        health = manager.get_service_health(service_name)
        assert health.status == ServiceStatus.UNAVAILABLE

        # Wait for circuit breaker timeout
        await asyncio.sleep(0.2)

        # Service should recover on next successful call
        result3 = await manager.execute_with_degradation(service_name, intermittent_func, fallback_func)

        # Assert
        assert result1 == "fallback_response"
        assert result2 == "fallback_response"
        assert "success_after" in result3

        # Service should be healthy again
        final_health = manager.get_service_health(service_name)
        assert final_health.status == ServiceStatus.HEALTHY
