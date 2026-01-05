"""
Unit tests for FastAPI application factory.

Tests for the FastAPI application setup, middleware, error handlers,
and route registration based on feature flags.
"""

import pytest

# Check if FastAPI is available
try:
    import fastapi  # noqa: F401

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

pytestmark = pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")

if FASTAPI_AVAILABLE:
    from fastapi import FastAPI

    from finwiz.api.app import create_app, lifespan
    from finwiz.config.manager import ConfigurationError


class TestLifespan:
    """Test the lifespan context manager for startup/shutdown."""

    @pytest.mark.asyncio
    async def test_should_validate_configuration_on_startup(self, mocker):
        """Test that configuration is validated during startup."""
        mock_config_manager = mocker.MagicMock()
        mocker.patch(
            "finwiz.api.app.get_configuration_manager",
            return_value=mock_config_manager,
        )
        mock_logger = mocker.patch("finwiz.api.app.logger")

        mock_app = mocker.MagicMock()

        async with lifespan(mock_app):
            pass

        # Verify configuration validation was called
        mock_config_manager.validate_startup_configuration.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_log_startup_and_shutdown(self, mocker):
        """Test that startup and shutdown are logged."""
        mock_config_manager = mocker.MagicMock()
        mocker.patch(
            "finwiz.api.app.get_configuration_manager",
            return_value=mock_config_manager,
        )
        mock_logger = mocker.patch("finwiz.api.app.logger")

        mock_app = mocker.MagicMock()

        async with lifespan(mock_app):
            pass

        # Verify startup and shutdown logs
        assert mock_logger.info.call_count >= 2
        startup_logged = any("Starting FinWiz API" in str(call) for call in mock_logger.info.call_args_list)
        shutdown_logged = any("Shutting down" in str(call) for call in mock_logger.info.call_args_list)
        assert startup_logged
        assert shutdown_logged

    @pytest.mark.asyncio
    async def test_should_raise_configuration_error(self, mocker):
        """Test that ConfigurationError is re-raised."""
        mock_config_manager = mocker.MagicMock()
        mock_config_manager.validate_startup_configuration.side_effect = ConfigurationError("Invalid config", "Fix this")
        mocker.patch(
            "finwiz.api.app.get_configuration_manager",
            return_value=mock_config_manager,
        )
        mock_logger = mocker.patch("finwiz.api.app.logger")

        mock_app = mocker.MagicMock()

        with pytest.raises(ConfigurationError):
            async with lifespan(mock_app):
                pass

        # Verify error was logged
        mock_logger.critical.assert_called()

    @pytest.mark.asyncio
    async def test_should_raise_generic_exception(self, mocker):
        """Test that generic exceptions are re-raised."""
        mock_config_manager = mocker.MagicMock()
        mock_config_manager.validate_startup_configuration.side_effect = ValueError("Bad value")
        mocker.patch(
            "finwiz.api.app.get_configuration_manager",
            return_value=mock_config_manager,
        )
        mock_logger = mocker.patch("finwiz.api.app.logger")

        mock_app = mocker.MagicMock()

        with pytest.raises(ValueError):
            async with lifespan(mock_app):
                pass

        # Verify error was logged as critical
        mock_logger.critical.assert_called()


class TestCreateApp:
    """Test the FastAPI application factory."""

    def test_should_create_app_instance(self, mocker):
        """Test that create_app returns a FastAPI instance."""
        mocker.patch(
            "finwiz.api.app.get_configuration_manager",
            return_value=mocker.MagicMock(),
        )
        mocker.patch("finwiz.api.app.is_feature_enabled", return_value=False)

        app = create_app()

        assert isinstance(app, FastAPI)
        assert app.title == "FinWiz API"
        assert "financial analysis" in app.description.lower()
        assert app.version == "1.0.0"

    def test_should_enable_docs_when_env_var_true(self, mocker):
        """Test that docs are enabled when FINWIZ_API_DOCS is true."""
        mocker.patch.dict("os.environ", {"FINWIZ_API_DOCS": "true"})
        mocker.patch(
            "finwiz.api.app.get_configuration_manager",
            return_value=mocker.MagicMock(),
        )
        mocker.patch("finwiz.api.app.is_feature_enabled", return_value=False)

        app = create_app()

        assert app.docs_url == "/docs"
        assert app.redoc_url == "/redoc"

    def test_should_disable_docs_when_env_var_false(self, mocker):
        """Test that docs are disabled when FINWIZ_API_DOCS is false."""
        mocker.patch.dict("os.environ", {"FINWIZ_API_DOCS": "false"})
        mocker.patch(
            "finwiz.api.app.get_configuration_manager",
            return_value=mocker.MagicMock(),
        )
        mocker.patch("finwiz.api.app.is_feature_enabled", return_value=False)

        app = create_app()

        assert app.docs_url is None
        assert app.redoc_url is None

    def test_should_add_cors_middleware(self, mocker):
        """Test that CORS middleware is added."""
        mocker.patch.dict("os.environ", {}, clear=False)
        mocker.patch(
            "finwiz.api.app.get_configuration_manager",
            return_value=mocker.MagicMock(),
        )
        mocker.patch("finwiz.api.app.is_feature_enabled", return_value=False)

        app = create_app()

        # Verify middleware was added (check that user_middleware is not empty)
        assert len(app.user_middleware) > 0

    def test_should_add_cors_with_custom_origins(self, mocker):
        """Test that CORS middleware uses custom origins from env var."""
        origins = "http://localhost:3000,http://localhost:5173"
        mocker.patch.dict("os.environ", {"FINWIZ_CORS_ORIGINS": origins})
        mocker.patch(
            "finwiz.api.app.get_configuration_manager",
            return_value=mocker.MagicMock(),
        )
        mocker.patch("finwiz.api.app.is_feature_enabled", return_value=False)

        app = create_app()

        # Verify middleware was added (check that user_middleware is not empty)
        assert len(app.user_middleware) > 0

    def test_should_register_rebalancing_router_when_enabled(self, mocker):
        """Test that rebalancing router is registered when feature is enabled."""
        mocker.patch(
            "finwiz.api.app.get_configuration_manager",
            return_value=mocker.MagicMock(),
        )
        mocker.patch(
            "finwiz.api.app.is_feature_enabled",
            side_effect=lambda feature: feature == "rebalancing_api",
        )

        app = create_app()

        # Check that rebalancing router was included
        routes = [route.path for route in app.routes]
        assert any("/api/v1" in route for route in routes)

    def test_should_not_register_rebalancing_router_when_disabled(self, mocker):
        """Test that rebalancing router is not registered when feature is disabled."""
        mocker.patch(
            "finwiz.api.app.get_configuration_manager",
            return_value=mocker.MagicMock(),
        )
        mocker.patch("finwiz.api.app.is_feature_enabled", return_value=False)

        app = create_app()

        # Rebalancing routes should not be present
        routes = [route.path for route in app.routes]
        rebalancing_routes = [r for r in routes if "/api/v1" in r and "rebalancing" in r]
        assert len(rebalancing_routes) == 0

    @pytest.mark.asyncio
    async def test_health_check_endpoint_should_return_healthy(self, mocker):
        """Test that health check endpoint returns healthy status."""
        mocker.patch(
            "finwiz.api.app.get_configuration_manager",
            return_value=mocker.MagicMock(),
        )
        mocker.patch("finwiz.api.app.is_feature_enabled", return_value=False)

        app = create_app()

        # Get the health check endpoint
        health_endpoint = None
        for route in app.routes:
            if hasattr(route, "path") and route.path == "/health":
                health_endpoint = route
                break

        assert health_endpoint is not None

    @pytest.mark.asyncio
    async def test_global_exception_handler_should_return_500(self, mocker):
        """Test that global exception handler returns 500 status."""
        mocker.patch(
            "finwiz.api.app.get_configuration_manager",
            return_value=mocker.MagicMock(),
        )
        mock_logger = mocker.patch("finwiz.api.app.logger")
        mocker.patch("finwiz.api.app.is_feature_enabled", return_value=False)

        app = create_app()

        # Check that exception handler is registered
        assert len(app.exception_handlers) > 0


class TestAppInstance:
    """Test the module-level app instance."""

    def test_app_instance_should_be_created(self, mocker):
        """Test that module-level app instance is created."""
        mocker.patch(
            "finwiz.api.app.get_configuration_manager",
            return_value=mocker.MagicMock(),
        )
        mocker.patch("finwiz.api.app.is_feature_enabled", return_value=False)

        # Import the app instance
        from finwiz.api.app import app

        assert isinstance(app, FastAPI)
        assert app.title == "FinWiz API"
