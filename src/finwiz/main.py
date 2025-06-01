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
import json
import warnings
from datetime import datetime
from typing import Any

# import agentops  # Disabled to avoid instrumentation errors
from crewai.flow import Flow, and_, listen, start
from dotenv import load_dotenv

from finwiz.crews.crypto_crew.crypto_crew import CryptoCrew
from finwiz.crews.etf_crew.etf_crew import EtfCrew
from finwiz.crews.report_crew.report_crew import ReportCrew
from finwiz.crews.stock_crew.stock_crew import StockCrew
from finwiz.tools.crewai_retry_patch import initialize_retry_mechanism
from finwiz.tools.logger import get_logger, setup_logging

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

# Initialize LLM retry mechanism with 5 max retries
logger.info("Initializing LLM retry mechanism")
initialize_retry_mechanism(max_retries=5)
logger.debug("Environment variables loaded")

# Disable AgentOps to avoid instrumentation error
# agentops.init()


class CryptoState:
    """Represents the state for the cryptocurrency analysis flow."""

    symbol: str = ""
    etf_result: str = ""
    crypto_result: str = ""
    stock_result: str = ""


class CryptoFlow(Flow[CryptoState]):
    """
    Orchestrates the financial analysis workflow for FinWiz.

    This flow integrates analyses from cryptocurrency, stock, and ETF crews,
    and generates a consolidated investment report. It utilizes the crewAI
    Flow paradigm to manage task dependencies and execution.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the CryptoFlow instance."""
        logger.info("Initializing CryptoFlow")
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

    @start()
    def check_stock(self) -> None:
        """Initiate the stock analysis crew or use existing results if available."""
        report_dir = os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ),
            "report",
        )
        json_file = os.path.join(
            report_dir, "stock_unicorn_investment_recommendations.json"
        )

        if os.path.exists(json_file):
            logger.info(f"Found existing stock analysis results at {json_file}")
            try:
                with open(json_file, "r") as f:
                    result_raw = f.read()
                    if isinstance(self.state, dict):
                        self.state["stock_result"] = result_raw
                        logger.debug(
                            "Existing stock results loaded to flow state dictionary"
                        )
                    else:
                        self.state.stock_result = result_raw
                        logger.debug(
                            "Existing stock results loaded to flow state object"
                        )
                logger.info("Loaded existing stock analysis results successfully")
                return
            except Exception as e:
                logger.warning(
                    f"Failed to load existing stock results: {str(e)}. Will run analysis instead."
                )

        logger.info("Starting stock analysis crew")
        try:
            result = StockCrew().crew().kickoff(inputs=self.inputs)
            logger.info("Stock analysis completed successfully")
            # Use dictionary access since the state is a dict during flow execution
            if isinstance(self.state, dict):
                self.state["stock_result"] = result.raw
                logger.debug("Stock results saved to flow state dictionary")
            else:
                self.state.stock_result = result.raw
                logger.debug("Stock results saved to flow state object")

            # Save the result to JSON file for future use
            try:
                os.makedirs(report_dir, exist_ok=True)
                with open(json_file, "w") as f:
                    f.write(result.raw)
                logger.debug(f"Saved stock results to {json_file}")
            except Exception as e:
                logger.warning(f"Failed to save stock results to file: {str(e)}")
        except Exception as e:
            logger.error(f"Error in stock analysis: {str(e)}", exc_info=True)
            raise

    @listen(check_stock)
    def check_etf(self) -> None:
        """Initiate the ETF analysis crew or use existing results if available."""
        # Define the path for the JSON result file
        report_dir = os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ),
            "report",
        )
        json_file = os.path.join(
            report_dir, "etf_unicorn_investment_recommendations.json"
        )

        # Check if the JSON file exists
        if os.path.exists(json_file):
            logger.info(f"Found existing ETF analysis results at {json_file}")
            try:
                with open(json_file) as f:
                    result_raw = f.read()
                    # Use dictionary access since the state is a dict during flow execution
                    if isinstance(self.state, dict):
                        self.state["etf_result"] = result_raw
                        logger.debug(
                            "Existing ETF results loaded to flow state dictionary"
                        )
                    else:
                        self.state.etf_result = result_raw
                        logger.debug("Existing ETF results loaded to flow state object")
                logger.info("Loaded existing ETF analysis results successfully")
                return
            except Exception as e:
                logger.warning(
                    f"Failed to load existing ETF results: {str(e)}. Will run analysis instead."
                )

        # If no JSON file exists or loading failed, run the crew
        logger.info("Starting ETF analysis crew")
        try:
            result = EtfCrew().crew().kickoff(inputs=self.inputs)
            logger.info("ETF analysis completed successfully")
            # Use dictionary access since the state is a dict during flow execution
            if isinstance(self.state, dict):
                self.state["etf_result"] = result.raw
                logger.debug("ETF results saved to flow state dictionary")
            else:
                self.state.etf_result = result.raw
                logger.debug("ETF results saved to flow state object")

            # Save the result to JSON file for future use
            try:
                os.makedirs(report_dir, exist_ok=True)
                with open(json_file, "w") as f:
                    f.write(result.raw)
                logger.debug(f"Saved ETF results to {json_file}")
            except Exception as e:
                logger.warning(f"Failed to save ETF results to file: {str(e)}")
        except Exception as e:
            logger.error(f"Error in ETF analysis: {str(e)}", exc_info=True)
            raise

    @listen(check_etf)
    def check_crypto(self) -> None:
        """Initiate the cryptocurrency analysis crew or use existing results if available."""
        import os

        # Define the path for the JSON result file
        report_dir = os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ),
            "report",
        )
        json_file = os.path.join(
            report_dir, "crypto_unicorn_investment_recommendations.json"
        )

        # Check if the JSON file exists
        if os.path.exists(json_file):
            logger.info(
                f"Found existing cryptocurrency analysis results at {json_file}"
            )
            try:
                with open(json_file) as f:
                    result_raw = f.read()
                    # Use dictionary access since the state is a dict during flow execution
                    if isinstance(self.state, dict):
                        self.state["crypto_result"] = result_raw
                        logger.debug(
                            "Existing cryptocurrency results loaded to flow state dictionary"
                        )
                    else:
                        self.state.crypto_result = result_raw
                        logger.debug(
                            "Existing cryptocurrency results loaded to flow state object"
                        )
                logger.info(
                    "Loaded existing cryptocurrency analysis results successfully"
                )
                return
            except Exception as e:
                logger.warning(
                    f"Failed to load existing cryptocurrency results: {str(e)}. "
                    "Will run analysis instead."
                )

        # If no JSON file exists or loading failed, run the crew
        logger.info("Starting cryptocurrency analysis crew")
        try:
            result = CryptoCrew().crew().kickoff(inputs=self.inputs)
            logger.info("Cryptocurrency analysis completed successfully")
            # Use dictionary access since the state is a dict during flow execution
            if isinstance(self.state, dict):
                self.state["crypto_result"] = result.raw
                logger.debug("Cryptocurrency results saved to flow state dictionary")
            else:
                self.state.crypto_result = result.raw
                logger.debug("Cryptocurrency results saved to flow state object")

            # Save the result to JSON file for future use
            try:
                os.makedirs(report_dir, exist_ok=True)
                with open(json_file, "w") as f:
                    f.write(result.raw)
                logger.debug(f"Saved cryptocurrency results to {json_file}")
            except Exception as e:
                logger.warning(
                    f"Failed to save cryptocurrency results to file: {str(e)}"
                )
        except Exception as e:
            logger.error(f"Error in cryptocurrency analysis: {str(e)}", exc_info=True)
            raise

    @listen(and_(check_stock, check_etf, check_crypto))
    def report(self) -> None:
        """Generate a consolidated report after all analyses are complete."""
        import os

        # Define the path for the JSON result file
        report_dir = os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ),
            "report",
        )
        json_file = os.path.join(report_dir, "comprehensive_investment_report.json")

        # Check if the JSON file exists
        if os.path.exists(json_file):
            logger.info(f"Found existing comprehensive report at {json_file}")
            try:
                with open(json_file) as f:
                    logger.info("Using existing comprehensive report")
                    return
            except Exception as e:
                logger.warning(
                    f"Failed to load existing report: {str(e)}. Will generate a new one."
                )

        logger.info("Starting consolidated report generation")
        try:
            # Use dictionary access since the state is a dict during flow execution
            kwargs = {}
            if isinstance(self.state, dict):
                logger.debug("Accessing results from flow state dictionary")
                kwargs["stock_result"] = self.state["stock_result"]
                kwargs["etf_result"] = self.state["etf_result"]
                kwargs["crypto_result"] = self.state["crypto_result"]
            else:
                logger.debug("Accessing results from flow state object")
                kwargs["stock_result"] = self.state.stock_result
                kwargs["etf_result"] = self.state.etf_result
                kwargs["crypto_result"] = self.state.crypto_result

            logger.debug("Updating inputs with analysis results")
            self.inputs.update(kwargs)

            logger.info("Initiating report crew")
            result = ReportCrew().crew().kickoff(inputs=self.inputs)
            logger.info("Report generation completed successfully")

            # Save the result to JSON file for future use
            try:
                os.makedirs(report_dir, exist_ok=True)
                with open(json_file, "w") as f:
                    f.write(result.raw)
                logger.debug(f"Saved comprehensive report to {json_file}")
            except Exception as e:
                logger.warning(f"Failed to save report to file: {str(e)}")

        except Exception as e:
            logger.error(f"Error in report generation: {str(e)}", exc_info=True)
            raise

    # @start()
    # def report(self) -> None:
    #     """Generate a consolidated report after all analyses are complete."""
    #     logger.info(
    #         "Starting consolidated report generation - DEBUG MODE with file inputs"
    #     )
    #     try:
    #         import json
    #         import os

    #         # Project root directory
    #         base_dir = os.path.dirname(
    #             os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    #         )

    #         # Load JSON files directly instead of using crew results
    #         logger.info("Loading recommendation files directly for debugging")
    #         stock_file = os.path.join(
    #             base_dir, "report/stock_unicorn_investment_recommendations.json"
    #         )
    #         etf_file = os.path.join(
    #             base_dir, "report/etf_unicorn_investment_recommendations.json"
    #         )
    #         crypto_file = os.path.join(
    #             base_dir, "report/crypto_unicorn_investment_recommendations.json"
    #         )

    #         # Read files
    #         with open(stock_file, "r") as f:
    #             stock_result = f.read()
    #             logger.debug(f"Loaded stock recommendations from {stock_file}")

    #         with open(etf_file, "r") as f:
    #             etf_result = f.read()
    #             logger.debug(f"Loaded ETF recommendations from {etf_file}")

    #         with open(crypto_file, "r") as f:
    #             crypto_result = f.read()
    #             logger.debug(f"Loaded crypto recommendations from {crypto_file}")

    #         # Prepare inputs for report crew
    #         kwargs = {
    #             "stock_result": stock_result,
    #             "etf_result": etf_result,
    #             "crypto_result": crypto_result,
    #         }

    #         logger.debug("Updating inputs with file-based results")
    #         self.inputs.update(kwargs)

    #         logger.info("Initiating report crew with file-based inputs")
    #         ReportCrew().crew().kickoff(inputs=self.inputs)
    #         logger.info("Report generation completed successfully")
    #     except Exception as e:
    #         logger.error(f"Error in report generation: {str(e)}", exc_info=True)
    #         raise


def kickoff() -> None:
    """Initialize and start the main FinWiz analysis flow."""
    logger.info("Starting FinWiz analysis workflow")
    try:
        crypto_flow = CryptoFlow(state=CryptoState())
        logger.debug("CryptoFlow instance created with CryptoState")
        crypto_flow.kickoff()
        logger.info("FinWiz analysis workflow completed successfully")
    except Exception as e:
        logger.critical(f"FinWiz analysis workflow failed: {str(e)}", exc_info=True)
        raise


def plot() -> None:
    """Initialize the FinWiz analysis flow and plot its structure."""
    logger.info("Plotting FinWiz analysis flow structure")
    try:
        crypto_flow = CryptoFlow(state=CryptoState())
        crypto_flow.plot()
        logger.info("Flow structure plotting completed")
    except Exception as e:
        logger.error(f"Error plotting flow structure: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    logger.info("main.py executed as script")
    kickoff()
