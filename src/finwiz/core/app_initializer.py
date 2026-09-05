#!/usr/bin/env python
"""
Application initialization logic for FinWiz.

This module handles the main application startup sequence, including
configuration validation, session management, and flow execution.
"""

import logging
import os
import warnings

from dotenv import load_dotenv

from finwiz.analysis.run_gate import exit_code_for
from finwiz.cli.argument_parser import (
    initialize_configuration,
    initialize_environment,
)
from finwiz.flow_state import FinwizState
from finwiz.flows.orchestrator import FinwizFlow
from finwiz.tools.logger import get_logger, setup_logging

# Load .env at module import so configuration from .env is available regardless
# of which crew modules get imported first.
load_dotenv()

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
        # Step 1: Validate template variables in crew configurations
        from finwiz.validation import validate_template_variables_at_startup

        validate_template_variables_at_startup()

        # Step 2: Initialize and validate configuration
        initialize_configuration()

        # Step 3: Initialize environment
        initialize_environment()

        # Step 4: Create and start the flow
        logger.info("Creating FinWiz flow")

        # Create flow state
        flow_state = FinwizState()

        # Create the flow instance
        finwiz_flow = FinwizFlow(state=flow_state)
        logger.debug("FinwizFlow instance created with FinwizState")

        # Step 5: Execute the flow. Phase 4 (Investment Discovery) ALWAYS runs —
        # the INVESTMENT_DISCOVERY_ENABLED kill switch was removed because
        # downstream alternatives-matching depends on discovery output and
        # turning it off silently produced the "no alternatives found" warning
        # class. Same philosophy as the v0.3.0 deep-analysis fix.
        logger.info("🚀 Starting FinWiz analysis execution")
        finwiz_flow.kickoff()
        # Step 6: The run gate left its verdict on state. PASS/WARN → 0, FAIL → 1,
        # ERROR or no verdict at all → 2. "Nothing to report" and "I did not look"
        # must never share an exit code.
        gate_verdict = getattr(flow_state, "gate_verdict", None)
        exit_code = exit_code_for(gate_verdict)
        logger.info(f"✅ FinWiz analysis workflow completed — run gate {gate_verdict or 'ERROR'} (exit {exit_code})")

        # Step 7: Force-exit the process so third-party thread pools
        # (CrewAI, LiteLLM, httpx) don't block Python's threading._shutdown().
        # Flush logs first to ensure nothing is lost.
        logging.shutdown()
        os._exit(exit_code)

    except SystemExit:
        # Re-raise SystemExit to allow proper application termination
        raise
    except Exception as e:
        logger.critical(f"❌ FinWiz analysis workflow failed: {e!s}", exc_info=True)
        logger.critical("Check the logs above for detailed error information")
        raise
