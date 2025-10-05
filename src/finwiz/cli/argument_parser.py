#!/usr/bin/env python
"""
CLI argument parsing and initialization for FinWiz application.

This module handles command-line interface setup, configuration validation,
session management, and environment initialization.
"""

import os

from dotenv import load_dotenv

from finwiz.tools.crewai_retry_patch import initialize_retry_mechanism
from finwiz.tools.logger import get_logger
from finwiz.utils.configuration_manager import ConfigurationError, get_configuration_manager
from finwiz.utils.session_manager import SessionManager, SessionParsingError

logger = get_logger(__name__)


def initialize_configuration() -> None:
    """Initialize and validate configuration."""
    logger.info("Initializing configuration management")
    config_manager = get_configuration_manager()

    try:
        config_manager.validate_startup_configuration()
        logger.info("✅ Configuration validation successful")

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
        logger.critical("❌ Configuration validation failed")
        logger.critical("Missing required API keys for FinWiz operation")
        logger.critical("\n" + e.remediation_guidance)
        logger.critical("Please configure the required API keys and restart the application")
        raise SystemExit(1) from e


def initialize_session_management() -> object:
    """Initialize session management and return financial plan."""
    logger.info("Initializing session management")
    session_manager = SessionManager()

    try:
        # Try to load existing session
        financial_plan = session_manager.load_existing_session()

        if financial_plan:
            logger.info("✅ Successfully loaded existing financial plan session")
            logger.info(f"Session ID: {financial_plan.plan_id}")
            logger.info(f"Created: {financial_plan.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"Last updated: {financial_plan.last_updated.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"Analysis history: {len(financial_plan.analysis_history)} records")

            # Validate session integrity
            is_valid, issues = session_manager.validate_session_integrity(financial_plan)
            if not is_valid:
                logger.warning(f"Session integrity issues detected: {issues}")
                logger.warning("Proceeding with session but recommend reviewing data quality")
        else:
            logger.info("No existing session found, creating new financial plan")
            financial_plan = session_manager.create_new_session()
            logger.info("✅ Created new financial plan session")
            logger.info(f"New session ID: {financial_plan.plan_id}")

        return financial_plan

    except SessionParsingError as e:
        logger.error(f"Session loading failed: {str(e)}")
        logger.warning("Attempting session recovery...")

        try:
            financial_plan = session_manager.recover_corrupted_session()
            logger.info("✅ Session recovery successful")
            logger.info(f"Recovered session ID: {financial_plan.plan_id}")
            return financial_plan
        except SessionParsingError as recovery_error:
            logger.error(f"Session recovery failed: {str(recovery_error)}")
            logger.info("Creating new session as fallback")
            financial_plan = session_manager.create_new_session()
            logger.info(f"✅ Fallback session created with ID: {financial_plan.plan_id}")
            return financial_plan


def initialize_environment() -> None:
    """Initialize environment variables and retry mechanism."""
    logger.info("Loading environment variables")
    load_dotenv()

    logger.info("Initializing LLM retry mechanism with extended timeout")
    initialize_retry_mechanism(max_retries=5, timeout=300)  # 5 minute timeout
    logger.debug("Environment variables loaded")


def setup_session_environment(financial_plan: object) -> None:
    """Set up session data in environment variables for crew access."""
    if financial_plan:
        # Store session data in environment variables for crew access
        os.environ["FINWIZ_SESSION_ID"] = financial_plan.plan_id
        os.environ["FINWIZ_SESSION_CREATED"] = financial_plan.created_at.isoformat()
        os.environ["FINWIZ_SESSION_UPDATED"] = financial_plan.last_updated.isoformat()
        os.environ["FINWIZ_HAS_EXISTING_SESSION"] = "true"
        os.environ["FINWIZ_ANALYSIS_COUNT"] = str(len(financial_plan.analysis_history))

        # Log session integration
        logger.info("✅ Session data made available to crews via environment variables")
        logger.info(f"Session ID: {financial_plan.plan_id}")
        logger.info(f"Analysis history: {len(financial_plan.analysis_history)} records")
    else:
        os.environ["FINWIZ_HAS_EXISTING_SESSION"] = "false"
        logger.info("No session data to integrate")


def cleanup_session_environment() -> None:
    """Clean up session environment variables."""
    session_env_vars = [
        "FINWIZ_SESSION_ID",
        "FINWIZ_SESSION_CREATED",
        "FINWIZ_SESSION_UPDATED",
        "FINWIZ_HAS_EXISTING_SESSION",
        "FINWIZ_ANALYSIS_COUNT",
    ]
    for var in session_env_vars:
        os.environ.pop(var, None)
    logger.debug("Session environment variables cleaned up")
