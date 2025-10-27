#!/usr/bin/env python
"""
CLI argument parsing and initialization for FinWiz application.

This module handles command-line interface setup, configuration validation,
session management, and environment initialization.
"""

import argparse
import os

from dotenv import load_dotenv

from finwiz.tools.crewai_retry_patch import initialize_retry_mechanism
from finwiz.tools.logger import get_logger
from finwiz.utils.configuration_manager import ConfigurationError, get_configuration_manager
from finwiz.utils.flow_state_manager import FlowStateManager
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


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments for FinWiz application.

    Returns:
        Parsed arguments namespace with resume_uuid and no_resume flags

    """
    parser = argparse.ArgumentParser(
        description="FinWiz - AI-powered financial analysis platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start fresh analysis (default)
  python -m finwiz.main

  # Resume from specific UUID
  python -m finwiz.main --resume-uuid abc123def456

  # Force fresh start (skip resume prompt)
  python -m finwiz.main --no-resume

Resume States:
  Flow states are stored in ~/.crewai/state/
  States older than 24 hours are marked as stale but can still be resumed.
        """,
    )

    parser.add_argument(
        "--resume-uuid",
        type=str,
        metavar="UUID",
        help="Resume from specific flow state UUID (e.g., abc123def456)",
    )

    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Force fresh start, skip resume prompt even if states exist",
    )

    return parser.parse_args()


def initialize_flow_with_resume(args: argparse.Namespace | None = None) -> "FinwizFlow":
    """
    Initialize FinwizFlow with resume capability based on CLI arguments.

    This function handles three scenarios:
    1. --no-resume flag: Force fresh start
    2. --resume-uuid provided: Load specific UUID
    3. Neither flag: Discover states and prompt user interactively

    Args:
        args: Parsed command-line arguments (if None, will parse from sys.argv)

    Returns:
        FinwizFlow instance (fresh or with loaded state)

    Raises:
        SystemExit: If invalid UUID provided or user cancels

    """
    from finwiz.flow_state import FinwizState
    from finwiz.flows.flow_orchestrator import FinwizFlow

    # Parse arguments if not provided
    if args is None:
        args = parse_arguments()

    # Scenario 1: Force fresh start
    if args.no_resume:
        logger.info("--no-resume flag set, starting fresh flow")
        flow_state = FinwizState()
        return FinwizFlow(state=flow_state)

    # Initialize state manager
    state_manager = FlowStateManager()

    # Scenario 2: Specific UUID provided
    if args.resume_uuid:
        logger.info(f"--resume-uuid provided: {args.resume_uuid}")

        # Load state data
        state_data = state_manager.load_flow_state_by_uuid(args.resume_uuid)

        if state_data is None:
            logger.error(f"❌ Failed to load state for UUID: {args.resume_uuid}")
            logger.error("State file not found or corrupted")
            logger.error("Available options:")
            logger.error("  1. Check UUID spelling")
            logger.error("  2. Use --no-resume to start fresh")
            logger.error("  3. Run without arguments to see available states")
            raise SystemExit(1)

        # Create state from loaded data
        try:
            flow_state = FinwizState(**state_data)
            flow_state.resume_from_checkpoint = True
            flow_state.checkpoint_uuid = args.resume_uuid

            logger.info(f"✅ Successfully loaded state for UUID: {args.resume_uuid}")
            logger.info(f"Progress: {flow_state.holdings_processed}/{flow_state.total_holdings} holdings")

            return FinwizFlow(state=flow_state)

        except Exception as e:
            logger.error(f"❌ Failed to create flow state from loaded data: {e}")
            logger.error("State data may be incompatible with current FinwizState schema")
            logger.error("Use --no-resume to start fresh")
            raise SystemExit(1) from e

    # Scenario 3: Interactive mode - discover and prompt
    logger.info("Checking for existing flow states...")
    states = state_manager.discover_persisted_states()

    if not states:
        logger.info("No existing flow states found, starting fresh")
        flow_state = FinwizState()
        return FinwizFlow(state=flow_state)

    # Prompt user for selection
    try:
        selected_uuid = state_manager.prompt_user_for_resume(states)

        if selected_uuid is None:
            # User chose to start fresh
            logger.info("User selected fresh start")
            flow_state = FinwizState()
            return FinwizFlow(state=flow_state)

        # Load selected state
        state_data = state_manager.load_flow_state_by_uuid(selected_uuid)

        if state_data is None:
            logger.error(f"❌ Failed to load selected state: {selected_uuid}")
            logger.error("Starting fresh as fallback")
            flow_state = FinwizState()
            return FinwizFlow(state=flow_state)

        # Create state from loaded data
        try:
            flow_state = FinwizState(**state_data)
            flow_state.resume_from_checkpoint = True
            flow_state.checkpoint_uuid = selected_uuid

            logger.info(f"✅ Resuming from UUID: {selected_uuid}")
            logger.info(f"Progress: {flow_state.holdings_processed}/{flow_state.total_holdings} holdings")

            return FinwizFlow(state=flow_state)

        except Exception as e:
            logger.error(f"❌ Failed to create flow state from loaded data: {e}")
            logger.error("Starting fresh as fallback")
            flow_state = FinwizState()
            return FinwizFlow(state=flow_state)

    except (KeyboardInterrupt, SystemExit):
        # User cancelled or error occurred
        raise
