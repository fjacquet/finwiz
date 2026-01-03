#!/usr/bin/env python
"""
Main entry point for the FinWiz application.

This module serves as a thin entry point that delegates to the
application initializer for the main workflow execution.

Functions:
    kickoff: Initialize and start the main FinWiz analysis flow.
    plot: Initialize the FinWiz analysis flow and plot its structure.
"""

# Import and re-export for backward compatibility
from finwiz.config.features.flags import is_feature_enabled
from finwiz.core.app_initializer import kickoff
from finwiz.crews.crypto_crew.crypto_crew import CryptoCrew
from finwiz.crews.etf_crew.etf_crew import EtfCrew
from finwiz.crews.investment_discovery_crew.investment_discovery_crew import InvestmentDiscoveryCrew
from finwiz.crews.portfolio_rebalancing_crew.portfolio_rebalancing_crew import PortfolioRebalancingCrew
from finwiz.crews.report_crew.report_crew import ReportCrew
from finwiz.crews.stock_crew.stock_crew import StockCrew
from finwiz.flow_state import FinwizState
from finwiz.flows.orchestrator import FinwizFlow, plot
from finwiz.integration.accessor import CrewDataAccessor
from finwiz.integration.manager import CrewDataIntegrationManager
from finwiz.tools.logger import get_logger

# Re-export for backward compatibility
__all__ = [
    "kickoff",
    "plot",
    "FinwizFlow",
    "FinwizState",
    "is_feature_enabled",
    "CryptoCrew",
    "EtfCrew",
    "InvestmentDiscoveryCrew",
    "PortfolioRebalancingCrew",
    "ReportCrew",
    "StockCrew",
    "CrewDataAccessor",
    "CrewDataIntegrationManager",
]

logger = get_logger(__name__)


if __name__ == "__main__":
    logger.info("main.py executed as script")
    kickoff()
