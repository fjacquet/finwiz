#!/usr/bin/env python
"""
CLI argument parsing and initialization for FinWiz application.

This module handles command-line interface setup and configuration validation.
"""

from typing import TYPE_CHECKING

from dotenv import load_dotenv

from finwiz.tools.crewai_retry_patch import initialize_retry_mechanism

if TYPE_CHECKING:
    pass

from finwiz.config.manager import ConfigurationError, get_configuration_manager
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


def initialize_configuration() -> None:
    """Initialize and validate configuration."""
    logger.info("Initializing configuration management")
    config_manager = get_configuration_manager()

    try:
        config_manager.validate_startup_configuration()
        logger.info("Configuration validation successful")

        # Log configuration status
        config_summary = config_manager.get_configuration_summary()
        logger.info(f"API keys configured: {config_summary['api_keys_configured']}")
        logger.info(f"Available services: {', '.join(config_summary['available_services'])}")

        # Log feature flag states
        feature_flags = config_manager.feature_flags
        enabled_flags = feature_flags.get_enabled_flags()
        if enabled_flags:
            logger.info(f"Enabled feature flags: {', '.join(enabled_flags)}")
        else:
            logger.info("No feature flags enabled")

    except ConfigurationError as e:
        logger.critical("Configuration validation failed")
        logger.critical("Missing required API keys for FinWiz operation")
        logger.critical("\n" + e.remediation_guidance)
        logger.critical("Please configure the required API keys and restart the application")
        raise SystemExit(1) from e


def initialize_environment() -> None:
    """Initialize environment variables and retry mechanism."""
    logger.info("Loading environment variables")
    load_dotenv()

    logger.info("Initializing LLM retry mechanism with extended timeout")
    initialize_retry_mechanism(max_retries=5, timeout=300)  # 5 minute timeout
    logger.debug("Environment variables loaded")
