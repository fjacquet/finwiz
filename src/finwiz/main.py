#!/usr/bin/env python
"""
Main entry point for the FinWiz application.

This module defines and orchestrates the CrewAI flows for financial analysis,
integrating outputs from cryptocurrency, stock, and ETF research crews to
produce comprehensive investment recommendations.

It provides a command-line interface to initiate the analysis and includes
debugging information for flow orchestration.

Classes:
    CryptoState: State container for the cryptocurrency analysis flow.
    CryptoFlow: Main flow orchestrator for financial analysis.

Functions:
    kickoff: Initialize and start the main FinWiz analysis flow.
    plot: Initialize the FinWiz analysis flow and plot its structure.
"""

import json
import logging
import os
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

from crewai.flow import Flow, and_, listen, start
from dotenv import load_dotenv

from finwiz.crews.crypto_crew.crypto_crew import CryptoCrew
from finwiz.crews.etf_crew.etf_crew import EtfCrew
from finwiz.crews.report_crew.report_crew import ReportCrew
from finwiz.crews.stock_crew.stock_crew import StockCrew
from finwiz.orchestrators.portfolio_review import run as run_portfolio_review
from finwiz.schemas.validate import validate_reporter_input
from finwiz.tools.crewai_retry_patch import initialize_retry_mechanism
from finwiz.tools.logger import get_logger, setup_logging
from finwiz.utils.configuration_manager import ConfigurationError, get_configuration_manager
from finwiz.utils.session_manager import SessionManager, SessionParsingError

# from finwiz.utils.flow_utils import get_output_dir, run_crew_with_caching

# Setup logging configuration
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")
setup_logging(log_level=logging.INFO, log_dir=log_dir)

# Get logger for this module
logger = get_logger(__name__)

# Suppress specific warnings
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")
warnings.filterwarnings("ignore", message="No path_separator found in configuration")

# Configuration and session management will be initialized in kickoff() function
# to provide better error handling and user feedback


class FinwizState:
    """Represents the state for the cryptocurrency analysis flow."""

    etf_result: str = ""
    crypto_result: str = ""
    stock_result: str = ""


class FinwizFlow(Flow[FinwizState]):
    """
    Orchestrates the financial analysis workflow for FinWiz.

    This flow integrates analyses from cryptocurrency, stock, and ETF crews,
    and generates a consolidated investment report. It utilizes the crewAI
    Flow paradigm to manage task dependencies and execution.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the FinwizFlow instance."""
        logger.info("Initializing FinwizFlow")
        super().__init__(*args, **kwargs)

        # Create inputs at instance level
        today = datetime.now()
        self.inputs = {
            "current_day": today.day,
            "current_month": today.month,
            "current_year": today.year,
            "current_date": today.strftime("%Y-%m-%d"),
            "full_date": today.strftime("%B %d, %Y"),
            "timestamp": today.strftime("%Y-%m-%d %H:%M:%S"),
            "report_language": "fr",
            # Session information available via environment variables
            "has_existing_session": os.getenv("FINWIZ_HAS_EXISTING_SESSION", "false") == "true",
            "session_id": os.getenv("FINWIZ_SESSION_ID", ""),
            "analysis_count": int(os.getenv("FINWIZ_ANALYSIS_COUNT", "0")),
        }
        logger.debug(f"Flow inputs prepared with timestamp: {self.inputs['timestamp']}")

        if self.inputs["has_existing_session"]:
            logger.debug(f"Flow initialized with existing session: {self.inputs['session_id']}")
        else:
            logger.debug("Flow initialized without existing session")

    @start()
    def check_crypto(self) -> None:
        """Initiate the cryptocurrency analysis crew."""
        CryptoCrew().crew().kickoff(inputs=self.inputs)

    @start()
    def check_stock(self) -> None:
        """Initiate the stock analysis crew."""
        StockCrew().crew().kickoff(inputs=self.inputs)

    @start()
    def check_etf(self) -> None:
        """Initiate the ETF analysis crew."""
        EtfCrew().crew().kickoff(inputs=self.inputs)

    @start()
    def check_portfolio(self) -> None:
        """Run portfolio keep-or-sell review orchestrator and stash JSON path."""
        enabled = (os.getenv("PORTFOLIO_REVIEW_ENABLED") or "true").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        if not enabled:
            logger.info("Portfolio review disabled via PORTFOLIO_REVIEW_ENABLED")
            return
        try:
            out_path = run_portfolio_review()
            self.inputs["portfolio_review_json"] = str(out_path)
            # Load content for tool-less reporter consumption
            try:
                with open(out_path, encoding="utf-8") as f:
                    self.inputs["portfolio_review"] = json.load(f)
            except Exception as le:
                logger.warning(f"Failed to load portfolio review JSON content: {le}")
            logger.info(f"Portfolio review generated at {out_path}")
        except Exception as e:
            logger.error(f"Portfolio review failed: {e}")
            raise

    @listen(and_(check_stock, check_etf, check_crypto, check_portfolio))
    def pre_validate_reporter_input(self) -> None:
        """
        Validate ReporterInput payload before triggering the final report.

        This enforces the boundary contract using VALIDATION_STRICTNESS.
        Currently sources the example payload; replace with real aggregation
        once upstream consolidation writes the contract JSON to disk.
        """
        try:
            # src/finwiz/main.py -> parents[2] resolves to repository root
            project_root = Path(__file__).resolve().parents[2]
            example = project_root / "docs/schemas/examples/reporter_input.example.json"
            if not example.exists():
                logger.warning(f"ReporterInput example not found at {example}; skipping validation step")
                return
            model = validate_reporter_input(example)
            # Pass validated payload into downstream crew context as JSON-safe primitives
            self.inputs["reporter_input"] = model.model_dump(mode="json")
            logger.info("ReporterInput validated and injected into flow inputs")
        except Exception as e:
            logger.error(f"ReporterInput validation failed: {e}")
            raise

    @listen(pre_validate_reporter_input)
    def report(self) -> None:
        """Generate a consolidated report after all analyses are complete."""
        ReportCrew().crew().kickoff(inputs=self.inputs)


def kickoff() -> None:
    """Initialize and start the main FinWiz analysis flow."""
    logger.info("Starting FinWiz analysis workflow")

    try:
        # Step 1: Initialize and validate configuration
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

        # Step 2: Initialize session management
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

        except SessionParsingError as e:
            logger.error(f"Session loading failed: {str(e)}")
            logger.warning("Attempting session recovery...")

            try:
                financial_plan = session_manager.recover_corrupted_session()
                logger.info("✅ Session recovery successful")
                logger.info(f"Recovered session ID: {financial_plan.plan_id}")
            except SessionParsingError as recovery_error:
                logger.error(f"Session recovery failed: {str(recovery_error)}")
                logger.info("Creating new session as fallback")
                financial_plan = session_manager.create_new_session()
                logger.info(f"✅ Fallback session created with ID: {financial_plan.plan_id}")

        # Step 3: Initialize environment and retry mechanism
        logger.info("Loading environment variables")
        load_dotenv()

        logger.info("Initializing LLM retry mechanism with extended timeout")
        initialize_retry_mechanism(max_retries=5, timeout=300)  # 5 minute timeout
        logger.debug("Environment variables loaded")

        # Step 4: Create and start the flow with session data
        logger.info("Creating FinWiz flow with session integration")

        # Create flow state and prepare session data for flow inputs
        flow_state = FinwizState()

        # Store session data globally for potential crew access
        # This is safer than modifying flow inputs after creation
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

        # Create the flow instance
        finwiz_flow = FinwizFlow(state=flow_state)
        logger.debug("FinwizFlow instance created with FinwizState")

        # Step 5: Execute the flow
        logger.info("🚀 Starting FinWiz analysis execution")
        finwiz_flow.kickoff()
        logger.info("✅ FinWiz analysis workflow completed successfully")

        # Clean up session environment variables
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

    except SystemExit:
        # Re-raise SystemExit to allow proper application termination
        raise
    except Exception as e:
        logger.critical(f"❌ FinWiz analysis workflow failed: {str(e)}", exc_info=True)
        logger.critical("Check the logs above for detailed error information")
        raise


def plot() -> None:
    """Initialize the FinWiz analysis flow and plot its structure."""
    logger.info("Plotting FinWiz analysis flow structure")
    try:
        finwiz_flow = FinwizFlow()
        finwiz_flow.plot()
        logger.info("Flow structure plotting completed")
    except Exception as e:
        logger.error(f"Error plotting flow structure: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    logger.info("main.py executed as script")
    kickoff()
