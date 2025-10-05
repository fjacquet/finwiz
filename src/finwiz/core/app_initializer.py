#!/usr/bin/env python
"""
Application initialization logic for FinWiz.

This module handles the main application startup sequence, including
configuration validation, session management, and flow execution.
"""

import logging
import os
import warnings

from finwiz.cli.argument_parser import (
    cleanup_session_environment,
    initialize_configuration,
    initialize_environment,
    initialize_session_management,
    setup_session_environment,
)
from finwiz.flow_state import FinwizState
from finwiz.flows.flow_orchestrator import FinwizFlow
from finwiz.tools.logger import get_logger, setup_logging

# Setup logging configuration
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "logs")
setup_logging(log_level=logging.INFO, log_dir=log_dir)

# Get logger for this module
logger = get_logger(__name__)

# Suppress specific warnings
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")
warnings.filterwarnings("ignore", message="No path_separator found in configuration")


def kickoff() -> None:
    """Initialize and start the main FinWiz analysis flow."""
    logger.info("Starting FinWiz analysis workflow")

    try:
        # Step 1: Initialize and validate configuration
        initialize_configuration()

        # Step 2: Initialize session management
        financial_plan = initialize_session_management()

        # Step 3: Initialize environment and retry mechanism
        initialize_environment()

        # Step 4: Create and start the flow with session data
        logger.info("Creating FinWiz flow with session integration")

        # Create flow state and prepare session data for flow inputs
        flow_state = FinwizState()

        # Store session data globally for potential crew access
        # This is safer than modifying flow inputs after creation
        setup_session_environment(financial_plan)

        # Create the flow instance
        finwiz_flow = FinwizFlow(state=flow_state)
        logger.debug("FinwizFlow instance created with FinwizState")

        # Step 5: Execute the flow
        logger.info("🚀 Starting FinWiz analysis execution")
        finwiz_flow.kickoff()
        logger.info("✅ FinWiz analysis workflow completed successfully")

        # Clean up session environment variables
        cleanup_session_environment()

    except SystemExit:
        # Re-raise SystemExit to allow proper application termination
        raise
    except Exception as e:
        logger.critical(f"❌ FinWiz analysis workflow failed: {str(e)}", exc_info=True)
        logger.critical("Check the logs above for detailed error information")
        raise
