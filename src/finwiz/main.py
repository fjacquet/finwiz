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


import logging
import os
import warnings
from datetime import datetime
from typing import Any

from crewai.flow import Flow, and_, listen, start
from dotenv import load_dotenv

from finwiz.crews.crypto_crew.crypto_crew import CryptoCrew
from finwiz.crews.etf_crew.etf_crew import EtfCrew
from finwiz.crews.report_crew.report_crew import ReportCrew
from finwiz.crews.stock_crew.stock_crew import StockCrew
from finwiz.tools.crewai_retry_patch import initialize_retry_mechanism
from finwiz.tools.logger import get_logger, setup_logging
# from finwiz.utils.flow_utils import get_output_dir, run_crew_with_caching

# Setup logging configuration
log_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs"
)
setup_logging(log_level=logging.INFO, log_dir=log_dir)

# Get logger for this module
logger = get_logger(__name__)

# Suppress specific warnings
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")
warnings.filterwarnings("ignore", message="No path_separator found in configuration")

logger.info("Loading environment variables")
load_dotenv()

# Initialize LLM retry mechanism with 5 max retries and longer timeout
logger.info("Initializing LLM retry mechanism with extended timeout")
initialize_retry_mechanism(max_retries=5, timeout=300)  # 5 minute timeout
logger.debug("Environment variables loaded")

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
        }
        logger.debug(f"Flow inputs prepared with timestamp: {self.inputs['timestamp']}")

    # Utility methods moved to flow_utils.py

    @start()
    def check_stock(self) -> None:
        """Initiate the stock analysis crew."""
        StockCrew().crew().kickoff()
        # run_crew_with_caching(
        #     StockCrew, "stock_unicorn_investment_recommendations.json", "stock_result", self.state, self.inputs
        # )

    @start(check_stock)
    def check_etf(self) -> None:
        """Initiate the ETF analysis crew."""
        EtfCrew().crew().kickoff()
        # run_crew_with_caching(
        #     EtfCrew, "etf_unicorn_investment_recommendations.json", "etf_result", self.state, self.inputs
        # )

    @start(check_etf)
    def check_crypto(self) -> None:
        """Initiate the cryptocurrency analysis crew."""
        CryptoCrew().crew(),kickoff()
        # run_crew_with_caching(
        #     CryptoCrew,
        #     "crypto_unicorn_investment_recommendations.json",
        #     "crypto_result",
        #     self.state,
        #     self.inputs
        # )

    @listen(and_(check_stock, check_etf, check_crypto))
    def report(self) -> None:
        """Generate a consolidated report after all analyses are complete."""
        ReportCrew().crew().kickoff()
        # output_dir = get_output_dir()
        # json_file = os.path.join(output_dir, "comprehensive_investment_report.json")

        # if os.path.exists(json_file):
        #     logger.info(
        #         f"Found existing comprehensive report at {json_file}. Skipping generation."
        #     )
        #     return

        # logger.info("Starting consolidated report generation")
        # try:
        #     kwargs = {}
        #     if isinstance(self.state, dict):
        #         logger.debug("Accessing results from flow state dictionary")
        #         kwargs["stock_result"] = self.state["stock_result"]
        #         kwargs["etf_result"] = self.state["etf_result"]
        #         kwargs["crypto_result"] = self.state["crypto_result"]
        #     else:
        #         logger.debug("Accessing results from flow state object")
        #         kwargs["stock_result"] = self.state.stock_result
        #         kwargs["etf_result"] = self.state.etf_result
        #         kwargs["crypto_result"] = self.state.crypto_result

        #     self.inputs.update(kwargs)

        #     logger.info("Initiating report crew")
        #     result = ReportCrew().crew().kickoff(inputs=self.inputs)
        #     logger.info("Report generation completed successfully")

        #     os.makedirs(output_dir, exist_ok=True)
        #     with open(json_file, "w") as f:
        #         f.write(result.raw)
        #     logger.debug(f"Saved comprehensive report to {json_file}")

        # except Exception as e:
        #     logger.error(f"Error in report generation: {e}", exc_info=True)
        #     raise

def kickoff() -> None:
    """Initialize and start the main FinWiz analysis flow."""
    logger.info("Starting FinWiz analysis workflow")
    try:
        finwiz_flow = FinwizFlow(state=FinwizState())
        logger.debug("FinwizFlow instance created with FinwizState")
        finwiz_flow.kickoff()
        logger.info("FinWiz analysis workflow completed successfully")
    except Exception as e:
        logger.critical(f"FinWiz analysis workflow failed: {str(e)}", exc_info=True)
        raise


def plot() -> None:
    """Initialize the FinWiz analysis flow and plot its structure."""
    logger.info("Plotting FinWiz analysis flow structure")
    try:
        finwiz_flow = FinwizFlow(state=FinwizState())
        finwiz_flow.plot()
        logger.info("Flow structure plotting completed")
    except Exception as e:
        logger.error(f"Error plotting flow structure: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    logger.info("main.py executed as script")
    kickoff()
