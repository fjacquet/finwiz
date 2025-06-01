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

# Suppress specific warnings
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")
warnings.filterwarnings("ignore", message="No path_separator found in configuration")

load_dotenv()
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

    @start()
    def check_stock(self) -> None:
        """Initiate the stock analysis crew."""
        result = StockCrew().crew().kickoff(inputs=self.inputs)
        # Use dictionary access since the state is a dict during flow execution
        if isinstance(self.state, dict):
            self.state["stock_result"] = result.raw
        else:
            self.state.stock_result = result.raw

    @start()
    def check_etf(self) -> None:
        """Initiate the ETF analysis crew."""
        result = EtfCrew().crew().kickoff(inputs=self.inputs)
        # Use dictionary access since the state is a dict during flow execution
        if isinstance(self.state, dict):
            self.state["etf_result"] = result.raw
        else:
            self.state.etf_result = result.raw

    @start()
    def check_crypto(self) -> None:
        """Initiate the cryptocurrency analysis crew."""
        result = CryptoCrew().crew().kickoff(inputs=self.inputs)
        # Use dictionary access since the state is a dict during flow execution
        if isinstance(self.state, dict):
            self.state["crypto_result"] = result.raw
        else:
            self.state.crypto_result = result.raw




    @listen(and_(check_stock,check_etf,check_crypto))
    def report(self) -> None:
        """Generate a consolidated report after all analyses are complete."""
        report_inputs = self.inputs.copy()

        # Use dictionary access for state values
        if isinstance(self.state, dict):
            if "etf_result" in self.state:
                report_inputs["etf_result"] = self.state["etf_result"]
            if "crypto_result" in self.state:
                report_inputs["crypto_result"] = self.state["crypto_result"]
            if "stock_result" in self.state:
                report_inputs["stock_result"] = self.state["stock_result"]
        else:
            # Use attribute access if state is the actual CryptoState class
            report_inputs["etf_result"] = self.state.etf_result
            report_inputs["crypto_result"] = self.state.crypto_result
            report_inputs["stock_result"] = self.state.stock_result

        result = ReportCrew().crew().kickoff(inputs=report_inputs)


def kickoff() -> None:
    """Initialize and start the main FinWiz analysis flow."""
    # Create the flow instance
    crypto_flow = CryptoFlow()

    # Run the flow using the kickoff method
    crypto_flow.kickoff()


def plot() -> None:
    """Initialize the FinWiz analysis flow and plot its structure."""
    crypto_flow = CryptoFlow()
    crypto_flow.plot()


if __name__ == "__main__":
    print("DEBUG: main.py executed as script.")
    kickoff()
