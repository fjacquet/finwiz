"""
Unit tests for graceful degradation utilities.

Tests for GracefulDegradationManager and related classes.
"""

import asyncio
import time

import pytest
from faker import Faker

from finwiz.infrastructure.resilience.degradation import (
    DegradationConfig,
    DegradationLevel,
    GracefulDegradationManager,
    ServiceHealth,
    ServiceStatus,
    execute_with_degradation,
    get_degradation_manager,
)


class TestServiceStatus:
    """Tests for ServiceStatus enum."""

    def test_should_have_healthy_value(self):
        """Test HEALTHY enum value."""
        assert ServiceStatus.HEALTHY.value == "healthy"

    def test_should_have_degraded_value(self):
        """Test DEGRADED enum value."""
        assert ServiceStatus.DEGRADED.value == "degraded"

    def test_should_have_unavailable_value(self):
        """Test UNAVAILABLE enum value."""
        assert ServiceStatus.UNAVAILABLE.value == "unavailable"

    def test_should_have_rate_limited_value(self):
        """Test RATE_LIMITED enum value."""
        assert ServiceStatus.RATE_LIMITED.value == "rate_limited"

    def test_should_have_timeout_value(self):
        """Test TIMEOUT enum value."""
        assert ServiceStatus.TIMEOUT.value == "timeout"

    def test_should_be_str_subclass(self):
        """Test ServiceStatus is str subclass."""
        assert isinstance(ServiceStatus.HEALTHY, str)


class TestDegradationLevel:
    """Tests for DegradationLevel enum."""

    def test_should_have_none_value(self):
        """Test NONE enum value."""
        assert DegradationLevel.NONE.value == "none"

    def test_should_have_minor_value(self):
        """Test MINOR enum value."""
        assert DegradationLevel.MINOR.value == "minor"

    def test_should_have_moderate_value(self):
        """Test MODERATE enum value."""
        assert DegradationLevel.MODERATE.value == "moderate"

    def test_should_have_severe_value(self):
        """Test SEVERE enum value."""
        assert DegradationLevel.SEVERE.value == "severe"

    def test_should_have_critical_value(self):
        """Test CRITICAL enum value."""
        assert DegradationLevel.CRITICAL.value == "critical"


class TestServiceHealth:
    """Tests for ServiceHealth dataclass."""

    @pytest.fixture
    def fake(self):
        """Provide Faker instance."""
        return Faker()

    def test_should_initialize_with_required_fields(self, fake):
        """Test initialization with required fields only."""
        service_name = fake.word()

        health = ServiceHealth(
            service_name=service_name,
            status=ServiceStatus.HEALTHY,
        )

        assert health.service_name == service_name
        assert health.status == ServiceStatus.HEALTHY

    def test_should_have_default_degradation_level(self):
        """Test default degradation level is NONE."""
        health = ServiceHealth(
            service_name="test",
            status=ServiceStatus.HEALTHY,
        )

        assert health.degradation_level == DegradationLevel.NONE

    def test_should_have_default_error_count(self):
        """Test default error count is 0."""
        health = ServiceHealth(
            service_name="test",
            status=ServiceStatus.HEALTHY,
        )

        assert health.error_count == 0

    def test_should_have_default_success_count(self):
        """Test default success count is 0."""
        health = ServiceHealth(
            service_name="test",
            status=ServiceStatus.HEALTHY,
        )

        assert health.success_count == 0

    def test_should_have_default_response_time(self):
        """Test default response time is 0.0."""
        health = ServiceHealth(
            service_name="test",
            status=ServiceStatus.HEALTHY,
        )

        assert health.response_time == 0.0

    def test_should_accept_custom_values(self, fake):
        """Test initialization with all custom values."""
        service_name = fake.word()
        error_msg = fake.sentence()

        health = ServiceHealth(
            service_name=service_name,
            status=ServiceStatus.DEGRADED,
            degradation_level=DegradationLevel.MODERATE,
            error_count=5,
            success_count=10,
            response_time=1.5,
            error_message=error_msg,
        )

        assert health.service_name == service_name
        assert health.status == ServiceStatus.DEGRADED
        assert health.degradation_level == DegradationLevel.MODERATE
        assert health.error_count == 5
        assert health.success_count == 10
        assert health.response_time == 1.5
        assert health.error_message == error_msg


class TestDegradationConfig:
    """Tests for DegradationConfig dataclass."""

    @pytest.fixture
    def fake(self):
        """Provide Faker instance."""
        return Faker()

    def test_should_initialize_with_service_name(self, fake):
        """Test initialization with service name."""
        service_name = fake.word()

        config = DegradationConfig(service_name=service_name)

        assert config.service_name == service_name

    def test_should_have_default_max_retries(self):
        """Test default max_retries is 3."""
        config = DegradationConfig(service_name="test")

        assert config.max_retries == 3

    def test_should_have_default_retry_delay(self):
        """Test default retry_delay is 1.0."""
        config = DegradationConfig(service_name="test")

        assert config.retry_delay == 1.0

    def test_should_have_default_timeout_seconds(self):
        """Test default timeout_seconds is 30.0."""
        config = DegradationConfig(service_name="test")

        assert config.timeout_seconds == 30.0

    def test_should_have_default_health_check_interval(self):
        """Test default health_check_interval is 300."""
        config = DegradationConfig(service_name="test")

        assert config.health_check_interval == 300

    def test_should_have_default_error_threshold(self):
        """Test default error_threshold is 5."""
        config = DegradationConfig(service_name="test")

        assert config.error_threshold == 5

    def test_should_have_default_recovery_threshold(self):
        """Test default recovery_threshold is 3."""
        config = DegradationConfig(service_name="test")

        assert config.recovery_threshold == 3

    def test_should_have_default_cache_fallback(self):
        """Test default cache_fallback is True."""
        config = DegradationConfig(service_name="test")

        assert config.cache_fallback is True

    def test_should_have_default_enable_circuit_breaker(self):
        """Test default enable_circuit_breaker is True."""
        config = DegradationConfig(service_name="test")

        assert config.enable_circuit_breaker is True

    def test_should_accept_custom_values(self, fake):
        """Test initialization with custom values."""
        config = DegradationConfig(
            service_name="custom",
            max_retries=5,
            retry_delay=2.0,
            timeout_seconds=60.0,
            health_check_interval=600,
            error_threshold=10,
            recovery_threshold=5,
            cache_fallback=False,
            default_fallback=False,
            enable_circuit_breaker=False,
        )

        assert config.max_retries == 5
        assert config.retry_delay == 2.0
        assert config.timeout_seconds == 60.0
        assert config.health_check_interval == 600
        assert config.error_threshold == 10
        assert config.recovery_threshold == 5
        assert config.cache_fallback is False
        assert config.default_fallback is False
        assert config.enable_circuit_breaker is False


class TestGracefulDegradationManager:
    """Tests for GracefulDegradationManager class."""

    @pytest.fixture
    def mock_dependencies(self, mocker):
        """Mock external dependencies."""
        mock_cache_manager = mocker.Mock()
        mock_cache_manager.get = mocker.AsyncMock(return_value=None)
        mock_cache_manager.set = mocker.AsyncMock()
        mocker.patch(
            "finwiz.infrastructure.resilience.degradation.get_cache_manager",
            return_value=mock_cache_manager,
        )

        mock_feature_flags = mocker.Mock()
        mock_feature_flags.record_success = mocker.Mock()
        mock_feature_flags.record_failure = mocker.Mock()
        mocker.patch(
            "finwiz.infrastructure.resilience.degradation.get_feature_flags",
            return_value=mock_feature_flags,
        )

        return {
            "cache_manager": mock_cache_manager,
            "feature_flags": mock_feature_flags,
        }

    @pytest.fixture
    def manager(self, mock_dependencies):
        """Create GracefulDegradationManager instance."""
        return GracefulDegradationManager()

    def test_should_initialize_with_default_configs(self, manager):
        """Test manager initializes default service configs."""
        assert "openai" in manager.degradation_configs
        assert "alpha_vantage" in manager.degradation_configs
        assert "chart_img" in manager.degradation_configs
        assert "twelve_data" in manager.degradation_configs
        assert "yahoo_finance" in manager.degradation_configs
        assert "coinmarketcap" in manager.degradation_configs

    def test_should_initialize_service_health(self, manager):
        """Test manager initializes service health."""
        assert "openai" in manager.service_health
        assert manager.service_health["openai"].status == ServiceStatus.HEALTHY

    def test_should_get_service_health(self, manager):
        """Test get_service_health returns correct health."""
        health = manager.get_service_health("openai")

        assert health is not None
        assert health.service_name == "openai"

    def test_should_return_none_for_unknown_service(self, manager):
        """Test get_service_health returns None for unknown service."""
        health = manager.get_service_health("unknown_service")

        assert health is None

    def test_should_get_all_service_health(self, manager):
        """Test get_all_service_health returns all services."""
        all_health = manager.get_all_service_health()

        assert len(all_health) == 6
        assert "openai" in all_health
        assert "alpha_vantage" in all_health

    def test_should_return_copy_of_service_health(self, manager):
        """Test get_all_service_health returns a copy."""
        all_health1 = manager.get_all_service_health()
        all_health2 = manager.get_all_service_health()

        assert all_health1 is not all_health2

    def test_should_get_system_health_summary(self, manager):
        """Test get_system_health_summary returns correct structure."""
        summary = manager.get_system_health_summary()

        assert "overall_health" in summary
        assert "healthy_services" in summary
        assert "total_services" in summary
        assert "overall_degradation" in summary
        assert "service_details" in summary

    def test_should_report_healthy_when_all_services_healthy(self, manager):
        """Test overall health is healthy when all services healthy."""
        summary = manager.get_system_health_summary()

        assert summary["overall_health"] == "healthy"
        assert summary["healthy_services"] == 6
        assert summary["total_services"] == 6

    def test_should_report_degraded_when_service_unhealthy(self, manager):
        """Test overall health is degraded when service unhealthy."""
        manager.service_health["openai"].status = ServiceStatus.DEGRADED

        summary = manager.get_system_health_summary()

        assert summary["overall_health"] == "degraded"

    def test_should_update_service_config(self, manager):
        """Test update_service_config updates config."""
        result = manager.update_service_config("openai", max_retries=5)

        assert result is True
        assert manager.degradation_configs["openai"].max_retries == 5

    def test_should_return_false_for_unknown_service_config(self, manager):
        """Test update_service_config returns False for unknown service."""
        result = manager.update_service_config("unknown", max_retries=5)

        assert result is False

    def test_should_ignore_unknown_config_keys(self, manager):
        """Test update_service_config ignores unknown keys."""
        result = manager.update_service_config("openai", unknown_key="value")

        assert result is True  # Returns True but logs warning


class TestGracefulDegradationManagerAsync:
    """Async tests for GracefulDegradationManager."""

    @pytest.fixture
    def mock_dependencies(self, mocker):
        """Mock external dependencies."""
        mock_cache_manager = mocker.Mock()
        mock_cache_manager.get = mocker.AsyncMock(return_value=None)
        mock_cache_manager.set = mocker.AsyncMock()
        mocker.patch(
            "finwiz.infrastructure.resilience.degradation.get_cache_manager",
            return_value=mock_cache_manager,
        )

        mock_feature_flags = mocker.Mock()
        mock_feature_flags.record_success = mocker.Mock()
        mock_feature_flags.record_failure = mocker.Mock()
        mocker.patch(
            "finwiz.infrastructure.resilience.degradation.get_feature_flags",
            return_value=mock_feature_flags,
        )

        return {
            "cache_manager": mock_cache_manager,
            "feature_flags": mock_feature_flags,
        }

    @pytest.fixture
    def manager(self, mock_dependencies):
        """Create GracefulDegradationManager instance."""
        return GracefulDegradationManager()

    @pytest.mark.asyncio
    async def test_should_execute_primary_function(self, manager):
        """Test execute_with_degradation executes primary function."""
        async def primary_func():
            return "success"

        result = await manager.execute_with_degradation(
            "openai",
            primary_func,
        )

        assert result == "success"

    @pytest.mark.asyncio
    async def test_should_execute_sync_function(self, manager):
        """Test execute_with_degradation handles sync functions."""
        def sync_func():
            return "sync_success"

        result = await manager.execute_with_degradation(
            "openai",
            sync_func,
        )

        assert result == "sync_success"

    @pytest.mark.asyncio
    async def test_should_use_fallback_on_error(self, manager, mocker):
        """Test fallback is used when primary fails."""
        call_count = 0

        async def failing_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("test error")

        async def fallback_func():
            return "fallback_result"

        # Set max_retries to 0 for faster test
        manager.degradation_configs["openai"].max_retries = 0

        result = await manager.execute_with_degradation(
            "openai",
            failing_func,
            fallback_func=fallback_func,
        )

        assert result == "fallback_result"

    @pytest.mark.asyncio
    async def test_should_use_default_fallback(self, manager):
        """Test default fallback is used when no custom fallback."""
        async def failing_func():
            raise ValueError("test error")

        manager.degradation_configs["openai"].max_retries = 0

        result = await manager.execute_with_degradation(
            "openai",
            failing_func,
        )

        assert result is not None
        assert "choices" in result  # OpenAI default fallback structure

    @pytest.mark.asyncio
    async def test_should_record_success(self, manager, mock_dependencies):
        """Test success is recorded after successful call."""
        async def success_func():
            return "ok"

        await manager.execute_with_degradation("openai", success_func)

        mock_dependencies["feature_flags"].record_success.assert_called_with(
            "openai_integration"
        )

    @pytest.mark.asyncio
    async def test_should_record_error(self, manager, mock_dependencies):
        """Test error is recorded after failed call."""
        async def failing_func():
            raise ValueError("error")

        manager.degradation_configs["openai"].max_retries = 0

        await manager.execute_with_degradation("openai", failing_func)

        mock_dependencies["feature_flags"].record_failure.assert_called_with(
            "openai_integration"
        )

    @pytest.mark.asyncio
    async def test_should_handle_timeout(self, manager):
        """Test timeout handling."""
        async def slow_func():
            await asyncio.sleep(10)
            return "too_slow"

        manager.degradation_configs["openai"].timeout_seconds = 0.01
        manager.degradation_configs["openai"].max_retries = 0
        manager.degradation_configs["openai"].retry_delay = 0.01

        result = await manager.execute_with_degradation("openai", slow_func)

        # Should use fallback due to timeout
        assert result is not None

    @pytest.mark.asyncio
    async def test_should_cache_successful_result(self, manager, mock_dependencies):
        """Test successful result is cached."""
        async def success_func():
            return {"data": "value"}

        await manager.execute_with_degradation(
            "openai",
            success_func,
            cache_key="test_cache_key",
        )

        mock_dependencies["cache_manager"].set.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_use_cached_fallback(self, manager, mock_dependencies):
        """Test cached data is used as fallback."""
        mock_dependencies["cache_manager"].get = mocker.AsyncMock(
            return_value={"cached": "data"}
        )

        async def failing_func():
            raise ValueError("error")

        manager.degradation_configs["openai"].max_retries = 0

        result = await manager.execute_with_degradation(
            "openai",
            failing_func,
            cache_key="test_key",
        )

        assert result == {"cached": "data"}

    @pytest.mark.asyncio
    async def test_should_force_health_check(self, manager):
        """Test force_health_check returns health."""
        health = await manager.force_health_check("openai")

        assert health is not None
        assert health.service_name == "openai"

    @pytest.mark.asyncio
    async def test_should_reset_circuit_breaker_on_force_check(self, manager):
        """Test circuit breaker resets on force health check."""
        # Set service as unavailable
        manager.service_health["openai"].status = ServiceStatus.UNAVAILABLE
        manager.service_health["openai"].last_check = time.time() - 400  # Past interval

        health = await manager.force_health_check("openai")

        assert health.status == ServiceStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_should_handle_unknown_service(self, manager):
        """Test execute_with_degradation handles unknown service."""
        async def func():
            return "result"

        result = await manager.execute_with_degradation(
            "unknown_service",
            func,
        )

        assert result == "result"


class TestCalculateDegradationLevel:
    """Tests for _calculate_degradation_level method."""

    @pytest.fixture
    def mock_dependencies(self, mocker):
        """Mock external dependencies."""
        mock_cache_manager = mocker.Mock()
        mock_cache_manager.get = mocker.AsyncMock(return_value=None)
        mock_cache_manager.set = mocker.AsyncMock()
        mocker.patch(
            "finwiz.infrastructure.resilience.degradation.get_cache_manager",
            return_value=mock_cache_manager,
        )

        mock_feature_flags = mocker.Mock()
        mock_feature_flags.record_success = mocker.Mock()
        mock_feature_flags.record_failure = mocker.Mock()
        mocker.patch(
            "finwiz.infrastructure.resilience.degradation.get_feature_flags",
            return_value=mock_feature_flags,
        )

    @pytest.fixture
    def manager(self, mock_dependencies):
        """Create manager instance."""
        return GracefulDegradationManager()

    def test_should_return_none_for_zero_errors(self, manager):
        """Test returns NONE for 0 errors."""
        config = DegradationConfig(service_name="test", error_threshold=5)

        level = manager._calculate_degradation_level(0, config)

        assert level == DegradationLevel.NONE

    def test_should_return_minor_for_low_errors(self, manager):
        """Test returns MINOR for low error count."""
        config = DegradationConfig(service_name="test", error_threshold=6)

        level = manager._calculate_degradation_level(1, config)

        assert level == DegradationLevel.MINOR

    def test_should_return_moderate_for_medium_errors(self, manager):
        """Test returns MODERATE for medium error count."""
        config = DegradationConfig(service_name="test", error_threshold=6)

        level = manager._calculate_degradation_level(4, config)

        assert level == DegradationLevel.MODERATE

    def test_should_return_severe_for_high_errors(self, manager):
        """Test returns SEVERE for high error count."""
        config = DegradationConfig(service_name="test", error_threshold=5)

        level = manager._calculate_degradation_level(5, config)

        assert level == DegradationLevel.SEVERE

    def test_should_return_moderate_when_no_config(self, manager):
        """Test returns MODERATE when config is None."""
        level = manager._calculate_degradation_level(3, None)

        assert level == DegradationLevel.MODERATE


class TestGetDefaultFallbackData:
    """Tests for _get_default_fallback_data method."""

    @pytest.fixture
    def mock_dependencies(self, mocker):
        """Mock external dependencies."""
        mock_cache_manager = mocker.Mock()
        mock_cache_manager.get = mocker.AsyncMock(return_value=None)
        mock_cache_manager.set = mocker.AsyncMock()
        mocker.patch(
            "finwiz.infrastructure.resilience.degradation.get_cache_manager",
            return_value=mock_cache_manager,
        )

        mock_feature_flags = mocker.Mock()
        mocker.patch(
            "finwiz.infrastructure.resilience.degradation.get_feature_flags",
            return_value=mock_feature_flags,
        )

    @pytest.fixture
    def manager(self, mock_dependencies):
        """Create manager instance."""
        return GracefulDegradationManager()

    def test_should_return_openai_fallback(self, manager):
        """Test returns OpenAI fallback data."""
        data = manager._get_default_fallback_data("openai")

        assert "choices" in data
        assert "usage" in data

    def test_should_return_alpha_vantage_fallback(self, manager):
        """Test returns Alpha Vantage fallback data."""
        data = manager._get_default_fallback_data("alpha_vantage")

        assert "Global Quote" in data
        assert data["status"] == "fallback"

    def test_should_return_chart_img_fallback(self, manager):
        """Test returns chart_img fallback data."""
        data = manager._get_default_fallback_data("chart_img")

        assert data["chart_url"] is None
        assert data["status"] == "unavailable"

    def test_should_return_twelve_data_fallback(self, manager):
        """Test returns twelve_data fallback data."""
        data = manager._get_default_fallback_data("twelve_data")

        assert data["values"] == []
        assert data["status"] == "unavailable"

    def test_should_return_yahoo_finance_fallback(self, manager):
        """Test returns yahoo_finance fallback data."""
        data = manager._get_default_fallback_data("yahoo_finance")

        assert "regularMarketPrice" in data
        assert data["status"] == "fallback"

    def test_should_return_coinmarketcap_fallback(self, manager):
        """Test returns coinmarketcap fallback data."""
        data = manager._get_default_fallback_data("coinmarketcap")

        assert data["data"] == {}
        assert data["status"] == "unavailable"

    def test_should_return_generic_fallback_for_unknown(self, manager):
        """Test returns generic fallback for unknown service."""
        data = manager._get_default_fallback_data("unknown_service")

        assert data["status"] == "unavailable"
        assert data["data"] is None


class TestGetDegradationManager:
    """Tests for get_degradation_manager function."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self, mocker):
        """Reset singleton before each test."""
        import finwiz.infrastructure.resilience.degradation as module

        module._degradation_manager = None

        # Mock dependencies
        mock_cache_manager = mocker.Mock()
        mock_cache_manager.get = mocker.AsyncMock(return_value=None)
        mock_cache_manager.set = mocker.AsyncMock()
        mocker.patch(
            "finwiz.infrastructure.resilience.degradation.get_cache_manager",
            return_value=mock_cache_manager,
        )

        mock_feature_flags = mocker.Mock()
        mocker.patch(
            "finwiz.infrastructure.resilience.degradation.get_feature_flags",
            return_value=mock_feature_flags,
        )

        yield
        module._degradation_manager = None

    def test_should_return_manager_instance(self):
        """Test returns manager instance."""
        manager = get_degradation_manager()

        assert manager is not None
        assert isinstance(manager, GracefulDegradationManager)

    def test_should_return_singleton(self):
        """Test returns same instance on repeated calls."""
        manager1 = get_degradation_manager()
        manager2 = get_degradation_manager()

        assert manager1 is manager2


class TestExecuteWithDegradationFunction:
    """Tests for execute_with_degradation module function."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self, mocker):
        """Reset singleton before each test."""
        import finwiz.infrastructure.resilience.degradation as module

        module._degradation_manager = None

        # Mock dependencies
        mock_cache_manager = mocker.Mock()
        mock_cache_manager.get = mocker.AsyncMock(return_value=None)
        mock_cache_manager.set = mocker.AsyncMock()
        mocker.patch(
            "finwiz.infrastructure.resilience.degradation.get_cache_manager",
            return_value=mock_cache_manager,
        )

        mock_feature_flags = mocker.Mock()
        mock_feature_flags.record_success = mocker.Mock()
        mock_feature_flags.record_failure = mocker.Mock()
        mocker.patch(
            "finwiz.infrastructure.resilience.degradation.get_feature_flags",
            return_value=mock_feature_flags,
        )

        yield
        module._degradation_manager = None

    @pytest.mark.asyncio
    async def test_should_delegate_to_manager(self):
        """Test module function delegates to manager."""
        async def test_func():
            return "result"

        result = await execute_with_degradation("openai", test_func)

        assert result == "result"
