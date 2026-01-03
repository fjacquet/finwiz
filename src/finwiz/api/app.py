"""
FastAPI application factory for FinWiz API.

This module creates and configures the FastAPI application with
all necessary middleware, error handlers, and route registrations.
"""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request  # fastapi may not be installed
from fastapi.middleware.cors import CORSMiddleware  # fastapi may not be installed
from fastapi.responses import JSONResponse  # fastapi may not be installed

from finwiz.api.rebalancing import router as rebalancing_router
from finwiz.tools.logger import get_logger
from finwiz.config.manager import ConfigurationError, get_configuration_manager
from finwiz.config.features.flags import is_feature_enabled

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup and shutdown tasks."""
    logger.info("Starting FinWiz API application")

    try:
        # Validate configuration on startup
        config_manager = get_configuration_manager()
        config_manager.validate_startup_configuration()
        logger.info("✅ API configuration validation successful")

        yield

    except ConfigurationError as e:
        logger.critical("❌ API startup failed due to configuration errors")
        logger.critical(e.remediation_guidance)
        raise
    except Exception as e:
        logger.critical(f"❌ API startup failed: {e}")
        raise
    finally:
        logger.info("Shutting down FinWiz API application")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance

    """
    app = FastAPI(
        title="FinWiz API",
        description="AI-powered financial analysis and portfolio management API",
        version="1.0.0",
        docs_url="/docs" if os.getenv("FINWIZ_API_DOCS", "true").lower() == "true" else None,
        redoc_url="/redoc" if os.getenv("FINWIZ_API_DOCS", "true").lower() == "true" else None,
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.getenv("FINWIZ_CORS_ORIGINS", "*").split(","),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    # Add global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Global exception handler for unhandled errors."""
        logger.error(f"Unhandled API error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": "An unexpected error occurred",
                "request_id": getattr(request.state, "request_id", None),
            },
        )

    # Add health check endpoint
    @app.get("/health")
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy", "service": "finwiz-api"}

    # Register routers based on feature flags
    if is_feature_enabled("rebalancing_api"):
        app.include_router(rebalancing_router, prefix="/api/v1")
        logger.info("✅ Rebalancing API endpoints enabled")
    else:
        logger.info("ℹ️ Rebalancing API endpoints disabled via feature flag")

    logger.info("FastAPI application created and configured")
    return app


# Create application instance
app = create_app()
