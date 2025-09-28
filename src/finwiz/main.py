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
from finwiz.crews.investment_discovery_crew.investment_discovery_crew import InvestmentDiscoveryCrew
from finwiz.crews.portfolio_rebalancing_crew.portfolio_rebalancing_crew import PortfolioRebalancingCrew
from finwiz.crews.report_crew.report_crew import ReportCrew
from finwiz.crews.stock_crew.stock_crew import StockCrew
from finwiz.integration.data_accessor import CrewDataAccessor
from finwiz.integration.manager import CrewDataIntegrationManager
from finwiz.orchestrators.portfolio_review import run as run_portfolio_review
from finwiz.schemas.validate import validate_reporter_input
from finwiz.tools.crewai_retry_patch import initialize_retry_mechanism
from finwiz.tools.logger import get_logger, setup_logging
from finwiz.utils.configuration_manager import ConfigurationError, get_configuration_manager
from finwiz.utils.core_analysis_error_handler import CoreAnalysisErrorHandler
from finwiz.utils.feature_flags import is_feature_enabled
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

        # Initialize data integration system
        self.integration_manager = CrewDataIntegrationManager()
        self.data_accessor = CrewDataAccessor(self.integration_manager)
        logger.info("Data integration system initialized")

        # Initialize error handling system
        self.error_handler = CoreAnalysisErrorHandler(self.integration_manager)
        logger.info("Core analysis error handling system initialized")

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

    @listen("validate_data_integration")
    def check_crypto(self) -> None:
        """Initiate the cryptocurrency analysis crew after data validation."""
        if not is_feature_enabled("crypto_analysis"):
            logger.info("Crypto analysis disabled via feature flag")
            self.inputs["crypto_analysis_disabled"] = True
            return

        start_time = datetime.now()

        try:
            logger.info("Starting cryptocurrency analysis crew (Phase 2: Core Analysis)")
            crypto_crew = CryptoCrew()
            result = crypto_crew.crew().kickoff(inputs=self.inputs)

            # Store crew result in flow inputs
            if hasattr(result, "raw"):
                self.inputs["crypto_analysis_result"] = str(result.raw)
            else:
                self.inputs["crypto_analysis_result"] = str(result)

            # Store result in data integration system
            self.integration_manager.store_crew_output("crypto", result)

            # Mark core analysis as available
            self.inputs["core_analysis_completed"] = True
            self.inputs["crypto_analysis_success"] = True

            logger.info("Cryptocurrency analysis crew completed successfully")

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Cryptocurrency analysis crew failed: {e}", exc_info=True)

            # Handle error with graceful degradation
            fallback_response = self.error_handler.handle_crew_failure(
                crew_name="crypto", error=e, inputs=self.inputs, execution_time=execution_time
            )

            # Store fallback results
            self.inputs["crypto_analysis_error"] = str(e)
            self.inputs["crypto_analysis_success"] = False
            self.inputs["crypto_analysis_fallback"] = True
            self.inputs["crypto_fallback_strategy"] = fallback_response.fallback_strategy
            self.inputs["crypto_degraded_functionality"] = fallback_response.degraded_functionality

            if fallback_response.success and fallback_response.data:
                # Use fallback data
                self.inputs["crypto_analysis_result"] = json.dumps(fallback_response.data)
                self.integration_manager.store_crew_output("crypto", fallback_response.data)
                logger.info(f"Using fallback data for crypto analysis: {fallback_response.message}")
            else:
                # Complete failure - continue without crypto analysis
                self.inputs["crypto_analysis_result"] = None
                logger.warning(f"Crypto analysis completely failed: {fallback_response.message}")

            # Continue execution - don't raise the exception

    @listen("validate_data_integration")
    def check_stock(self) -> None:
        """Initiate the stock analysis crew after data validation."""
        if not is_feature_enabled("stock_analysis"):
            logger.info("Stock analysis disabled via feature flag")
            self.inputs["stock_analysis_disabled"] = True
            return

        start_time = datetime.now()

        try:
            logger.info("Starting stock analysis crew (Phase 2: Core Analysis)")
            stock_crew = StockCrew()
            result = stock_crew.crew().kickoff(inputs=self.inputs)

            # Store crew result in flow inputs
            if hasattr(result, "raw"):
                self.inputs["stock_analysis_result"] = str(result.raw)
            else:
                self.inputs["stock_analysis_result"] = str(result)

            # Store result in data integration system
            self.integration_manager.store_crew_output("stock", result)

            # Mark core analysis as available
            self.inputs["core_analysis_completed"] = True
            self.inputs["stock_analysis_success"] = True

            logger.info("Stock analysis crew completed successfully")

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Stock analysis crew failed: {e}", exc_info=True)

            # Handle error with graceful degradation
            fallback_response = self.error_handler.handle_crew_failure(
                crew_name="stock", error=e, inputs=self.inputs, execution_time=execution_time
            )

            # Store fallback results
            self.inputs["stock_analysis_error"] = str(e)
            self.inputs["stock_analysis_success"] = False
            self.inputs["stock_analysis_fallback"] = True
            self.inputs["stock_fallback_strategy"] = fallback_response.fallback_strategy
            self.inputs["stock_degraded_functionality"] = fallback_response.degraded_functionality

            if fallback_response.success and fallback_response.data:
                # Use fallback data
                self.inputs["stock_analysis_result"] = json.dumps(fallback_response.data)
                self.integration_manager.store_crew_output("stock", fallback_response.data)
                logger.info(f"Using fallback data for stock analysis: {fallback_response.message}")
            else:
                # Complete failure - continue without stock analysis
                self.inputs["stock_analysis_result"] = None
                logger.warning(f"Stock analysis completely failed: {fallback_response.message}")

            # Continue execution - don't raise the exception

    @listen("validate_data_integration")
    def check_etf(self) -> None:
        """Initiate the ETF analysis crew after data validation."""
        if not is_feature_enabled("etf_analysis"):
            logger.info("ETF analysis disabled via feature flag")
            self.inputs["etf_analysis_disabled"] = True
            return

        start_time = datetime.now()

        try:
            logger.info("Starting ETF analysis crew (Phase 2: Core Analysis)")
            etf_crew = EtfCrew()
            result = etf_crew.crew().kickoff(inputs=self.inputs)

            # Store crew result in flow inputs
            if hasattr(result, "raw"):
                self.inputs["etf_analysis_result"] = str(result.raw)
            else:
                self.inputs["etf_analysis_result"] = str(result)

            # Store result in data integration system
            self.integration_manager.store_crew_output("etf", result)

            # Mark core analysis as available
            self.inputs["core_analysis_completed"] = True
            self.inputs["etf_analysis_success"] = True

            logger.info("ETF analysis crew completed successfully")

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"ETF analysis crew failed: {e}", exc_info=True)

            # Handle error with graceful degradation
            fallback_response = self.error_handler.handle_crew_failure(
                crew_name="etf", error=e, inputs=self.inputs, execution_time=execution_time
            )

            # Store fallback results
            self.inputs["etf_analysis_error"] = str(e)
            self.inputs["etf_analysis_success"] = False
            self.inputs["etf_analysis_fallback"] = True
            self.inputs["etf_fallback_strategy"] = fallback_response.fallback_strategy
            self.inputs["etf_degraded_functionality"] = fallback_response.degraded_functionality

            if fallback_response.success and fallback_response.data:
                # Use fallback data
                self.inputs["etf_analysis_result"] = json.dumps(fallback_response.data)
                self.integration_manager.store_crew_output("etf", fallback_response.data)
                logger.info(f"Using fallback data for ETF analysis: {fallback_response.message}")
            else:
                # Complete failure - continue without ETF analysis
                self.inputs["etf_analysis_result"] = None
                logger.warning(f"ETF analysis completely failed: {fallback_response.message}")

            # Continue execution - don't raise the exception

    @start()
    def validate_data_integration(self) -> None:
        """Validate data integration system before crew execution."""
        try:
            logger.info("Validating data integration system")

            # Check data availability and freshness
            availability_report = self.data_accessor.check_data_availability()

            # Log data availability status
            logger.info(f"Data availability status: {availability_report.overall_status.value}")
            logger.info(
                f"Available crews: Stock={availability_report.stock_available}, "
                f"ETF={availability_report.etf_available}, "
                f"Crypto={availability_report.crypto_available}, "
                f"Discovery={availability_report.discovery_available}, "
                f"Portfolio={availability_report.portfolio_available}"
            )

            # Store availability report for downstream use
            self.inputs["data_availability_report"] = {
                "overall_status": availability_report.overall_status.value,
                "stock_available": availability_report.stock_available,
                "etf_available": availability_report.etf_available,
                "crypto_available": availability_report.crypto_available,
                "discovery_available": availability_report.discovery_available,
                "portfolio_available": availability_report.portfolio_available,
                "missing_data": availability_report.missing_data,
                "stale_data": availability_report.stale_data,
                "recommendations": availability_report.recommendations,
            }

            # Get stale data warnings
            stale_warnings = self.data_accessor.get_stale_data_warnings()
            if stale_warnings:
                logger.warning("Stale data detected:")
                for warning in stale_warnings:
                    logger.warning(f"  - {warning}")
                self.inputs["stale_data_warnings"] = stale_warnings

            # Get refresh recommendations if needed
            if availability_report.stale_data or availability_report.missing_data:
                refresh_recommendations = self.integration_manager.get_refresh_recommendations()
                if refresh_recommendations:
                    logger.info(f"Recommended refresh order: {' -> '.join(refresh_recommendations)}")
                    self.inputs["refresh_recommendations"] = refresh_recommendations

            logger.info("Data integration validation completed")

        except Exception as e:
            logger.error(f"Data integration validation failed: {str(e)}", exc_info=True)
            # Continue execution with degraded functionality
            self.inputs["data_integration_error"] = str(e)

    @listen(and_("check_stock", "check_etf", "check_crypto"))
    def check_portfolio(self) -> None:
        """Run portfolio keep-or-sell review orchestrator after core analysis completion (Phase 3: Portfolio Analysis)."""
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
            # Check core analysis availability
            core_analysis_available = self._check_core_analysis_availability()

            if core_analysis_available["any_available"]:
                logger.info(
                    f"Starting portfolio review with core analysis results available: {core_analysis_available['available_crews']}"
                )
            else:
                logger.warning("Starting portfolio review without core analysis results - all crews failed or disabled")

            # Add core analysis status to inputs for portfolio review
            self.inputs["core_analysis_status"] = core_analysis_available

            out_path = run_portfolio_review()
            self.inputs["portfolio_review_json"] = str(out_path)

            # Load content for tool-less reporter consumption
            try:
                with open(out_path, encoding="utf-8") as f:
                    self.inputs["portfolio_review"] = json.load(f)
            except Exception as le:
                logger.warning(f"Failed to load portfolio review JSON content: {le}")
                # Continue with degraded functionality
                self.inputs["portfolio_review"] = {}

            logger.info(f"Portfolio review generated at {out_path}")

        except Exception as e:
            logger.error(f"Portfolio review failed: {e}", exc_info=True)
            # Continue with graceful degradation instead of raising
            self.inputs["portfolio_review_error"] = str(e)
            self.inputs["portfolio_review"] = {}
            self.inputs["portfolio_review_json"] = None
            logger.warning("Portfolio review failed - continuing with empty portfolio data")

    @listen(and_("check_stock", "check_etf", "check_crypto"))
    def check_portfolio_rebalancing(self) -> None:
        """Run portfolio rebalancing analysis after core analysis completion (Phase 3: Portfolio Analysis)."""
        from finwiz.utils.feature_flags import is_feature_enabled

        if not is_feature_enabled("portfolio_rebalancing"):
            logger.info("Portfolio rebalancing disabled via feature flag")
            return

        try:
            # Check core analysis availability
            core_analysis_status = self._check_core_analysis_availability()

            if core_analysis_status["any_available"]:
                logger.info(
                    f"Starting portfolio rebalancing with core analysis integration: {core_analysis_status['available_crews']}"
                )

                # Prepare enhanced inputs with available core analysis
                crew_inputs = {
                    "full_date": datetime.now().strftime("%B %d, %Y"),
                    "portfolio_data": self.inputs.get("portfolio_review", {}),
                    "target_allocations": self.inputs.get("target_allocations", {}),
                    "tolerance_bands": self.inputs.get("tolerance_bands", {}),
                    "available_capital": self.inputs.get("available_capital", 0.0),
                    # Enhanced with available core analysis results
                    "stock_analysis": self.inputs.get("stock_analysis_result") if core_analysis_status["stock_available"] else None,
                    "etf_analysis": self.inputs.get("etf_analysis_result") if core_analysis_status["etf_available"] else None,
                    "crypto_analysis": self.inputs.get("crypto_analysis_result")
                    if core_analysis_status["crypto_available"]
                    else None,
                    "market_conditions": self._extract_market_conditions(),
                    "core_analysis_status": core_analysis_status,
                    # Include fallback information
                    "stock_fallback": self.inputs.get("stock_analysis_fallback", False),
                    "etf_fallback": self.inputs.get("etf_analysis_fallback", False),
                    "crypto_fallback": self.inputs.get("crypto_analysis_fallback", False),
                }
            else:
                logger.warning("Starting portfolio rebalancing without core analysis - all crews failed or disabled")

                # Fallback to basic behavior
                crew_inputs = {
                    "full_date": datetime.now().strftime("%B %d, %Y"),
                    "portfolio_data": self.inputs.get("portfolio_review", {}),
                    "target_allocations": self.inputs.get("target_allocations", {}),
                    "tolerance_bands": self.inputs.get("tolerance_bands", {}),
                    "available_capital": self.inputs.get("available_capital", 0.0),
                    "core_analysis_status": core_analysis_status,
                    "degraded_mode": True,
                }

            # Initialize portfolio rebalancing crew
            portfolio_rebalancing_crew = PortfolioRebalancingCrew()

            # Execute the portfolio rebalancing crew
            result = portfolio_rebalancing_crew.crew().kickoff(inputs=crew_inputs)

            # Store crew result - convert CrewOutput to string for template interpolation
            if hasattr(result, "raw"):
                # Use the raw output string from CrewOutput
                self.inputs["portfolio_rebalancing_result"] = str(result.raw)
            else:
                # Fallback to string conversion
                self.inputs["portfolio_rebalancing_result"] = str(result)
            self.inputs["portfolio_rebalancing_available"] = True

            logger.info("Portfolio rebalancing analysis completed successfully")

        except Exception as e:
            logger.error(f"Portfolio rebalancing analysis failed: {e}", exc_info=True)
            # Continue with graceful degradation
            self.inputs["portfolio_rebalancing_available"] = False
            self.inputs["portfolio_rebalancing_error"] = str(e)
            self.inputs["portfolio_rebalancing_result"] = None
            logger.warning("Portfolio rebalancing failed - continuing without rebalancing analysis")

    @listen(and_("check_portfolio", "check_portfolio_rebalancing"))
    def check_investment_discovery(self) -> None:
        """Run investment discovery analysis to find A+ grade opportunities."""
        from finwiz.utils.feature_flags import is_feature_enabled

        # Check if investment discovery is enabled via feature flag
        if not is_feature_enabled("investment_discovery"):
            logger.info("Investment discovery disabled via feature flag")
            self.inputs["investment_discovery_available"] = False
            return

        try:
            # Check if we have portfolio data from portfolio review
            if "portfolio_review" in self.inputs:
                # Check core analysis availability
                core_analysis_status = self._check_core_analysis_availability()

                if core_analysis_status["any_available"]:
                    logger.info(
                        f"Running investment discovery with core analysis integration: {core_analysis_status['available_crews']}"
                    )
                else:
                    logger.warning("Running investment discovery without core analysis - all crews failed or disabled")

                # Get upstream data using integration system
                upstream_data = self.integration_manager.get_upstream_data("discovery")
                logger.info(f"Upstream data available for discovery: {list(upstream_data.available_data.keys())}")

                if upstream_data.stale_data:
                    logger.warning(f"Stale upstream data detected: {upstream_data.stale_data}")
                if upstream_data.missing_data:
                    logger.warning(f"Missing upstream data: {upstream_data.missing_data}")

                # Get core analysis results from integration system (with error handling)
                core_analysis_data = {}
                for crew_type in ["stock", "etf", "crypto"]:
                    if core_analysis_status[f"{crew_type}_available"]:
                        try:
                            crew_data = self.integration_manager.get_crew_data_with_freshness_check(
                                crew_type, max_age_hours=24, warn_on_stale=True
                            )
                            if crew_data:
                                core_analysis_data[f"{crew_type}_analysis"] = crew_data
                                logger.info(f"Core analysis data available for {crew_type}")
                            else:
                                logger.warning(f"No core analysis data available for {crew_type}")
                        except Exception as e:
                            logger.warning(f"Failed to get core analysis data for {crew_type}: {e}")
                    else:
                        logger.debug(f"Core analysis not available for {crew_type}")

                # Initialize investment discovery crew
                investment_discovery_crew = InvestmentDiscoveryCrew()

                # Prepare inputs for the crew with integrated data access and core analysis results
                crew_inputs = {
                    "full_date": datetime.now().strftime("%B %d, %Y"),
                    "current_date": self.inputs.get("current_date"),
                    "timestamp": self.inputs.get("timestamp"),
                    "portfolio_data": self.inputs.get("portfolio_review", {}),
                    "portfolio_review_json": self.inputs.get("portfolio_review_json", ""),
                    "has_existing_session": self.inputs.get("has_existing_session", False),
                    "session_id": self.inputs.get("session_id", ""),
                    "analysis_count": self.inputs.get("analysis_count", 0),
                    "report_language": self.inputs.get("report_language", "fr"),
                    # Portfolio rebalancing results if available
                    "portfolio_rebalancing_result": self.inputs.get("portfolio_rebalancing_result"),
                    "portfolio_rebalancing_available": self.inputs.get("portfolio_rebalancing_available", False),
                    # Add upstream data information
                    "upstream_data_available": list(upstream_data.available_data.keys()),
                    "upstream_data_stale": upstream_data.stale_data,
                    "upstream_data_missing": upstream_data.missing_data,
                    # Enhanced: Add core analysis results with error handling
                    "core_analysis_available": len(core_analysis_data) > 0,
                    "available_core_analysis": list(core_analysis_data.keys()),
                    "core_analysis_status": core_analysis_status,
                    **core_analysis_data,  # Include all available core analysis data
                    # Add market context from core analysis (with error handling)
                    "market_context": self._extract_market_context_from_core_analysis(core_analysis_data),
                    # Include error information for transparency
                    "core_analysis_errors": {
                        "stock_error": self.inputs.get("stock_analysis_error"),
                        "etf_error": self.inputs.get("etf_analysis_error"),
                        "crypto_error": self.inputs.get("crypto_analysis_error"),
                    },
                    "fallback_strategies_used": {
                        "stock_fallback": self.inputs.get("stock_fallback_strategy"),
                        "etf_fallback": self.inputs.get("etf_fallback_strategy"),
                        "crypto_fallback": self.inputs.get("crypto_fallback_strategy"),
                    },
                }

                # Log enhanced inputs
                logger.info(f"Investment discovery enhanced with {len(core_analysis_data)} core analysis results")
                if core_analysis_data:
                    logger.info(f"Core analysis types available: {list(core_analysis_data.keys())}")
                if core_analysis_status["failed_crews"]:
                    logger.warning(f"Core analysis crews failed: {core_analysis_status['failed_crews']}")

                # Execute the investment discovery crew
                result = investment_discovery_crew.crew().kickoff(inputs=crew_inputs)

                # Store crew result in integration system
                self.integration_manager.store_crew_output("discovery", result)

                # Store crew result - convert CrewOutput to string for template interpolation
                if hasattr(result, "raw"):
                    result_text = str(result.raw)
                    self.inputs["investment_discovery_result"] = result_text
                else:
                    result_text = str(result)
                    self.inputs["investment_discovery_result"] = result_text

                # Use integrated A+ opportunity extraction (with error handling)
                try:
                    aplus_opportunities = self.data_accessor.get_aplus_opportunities()
                    if aplus_opportunities:
                        self.inputs["investment_discovery_structured"] = {
                            "has_a_plus_analysis": True,
                            "etf_opportunities": aplus_opportunities.etf_opportunities,
                            "stock_opportunities": aplus_opportunities.stock_opportunities,
                            "crypto_opportunities": aplus_opportunities.crypto_opportunities,
                            "portfolio_improvement": "Available - see discovery files",
                            "discovery_summary": aplus_opportunities.discovery_summary,
                            "confidence_score": aplus_opportunities.confidence_score,
                            "allocation_recommendations": aplus_opportunities.allocation_recommendations,
                            "replacement_notes": aplus_opportunities.replacement_notes,
                        }
                        logger.info(
                            f"Extracted A+ opportunities via integration system: "
                            f"{len(aplus_opportunities.etf_opportunities)} ETFs, "
                            f"{len(aplus_opportunities.stock_opportunities)} stocks, "
                            f"{len(aplus_opportunities.crypto_opportunities)} crypto"
                        )
                    else:
                        logger.warning("No A+ opportunities extracted via integration system")
                        self.inputs["investment_discovery_structured"] = {"has_a_plus_analysis": False}

                except Exception as e:
                    logger.warning(f"Could not extract A+ data via integration system: {e}")
                    self.inputs["investment_discovery_structured"] = {"has_a_plus_analysis": False}

                self.inputs["investment_discovery_available"] = True

                logger.info("Investment discovery analysis completed successfully with enhanced error handling")
            else:
                logger.warning("No portfolio data available for investment discovery analysis")
                self.inputs["investment_discovery_available"] = False

        except Exception as e:
            logger.error(f"Investment discovery analysis failed: {e}", exc_info=True)
            # Continue with graceful degradation
            self.inputs["investment_discovery_available"] = False
            self.inputs["investment_discovery_error"] = str(e)
            self.inputs["investment_discovery_result"] = None
            self.inputs["investment_discovery_structured"] = {"has_a_plus_analysis": False}
            logger.warning("Investment discovery failed - continuing without discovery analysis")

    def _check_core_analysis_availability(self) -> dict[str, Any]:
        """Check which core analysis crews are available and their status."""
        stock_available = self.inputs.get("stock_analysis_success", False) or (
            self.inputs.get("stock_analysis_fallback", False) and self.inputs.get("stock_analysis_result") is not None
        )
        etf_available = self.inputs.get("etf_analysis_success", False) or (
            self.inputs.get("etf_analysis_fallback", False) and self.inputs.get("etf_analysis_result") is not None
        )
        crypto_available = self.inputs.get("crypto_analysis_success", False) or (
            self.inputs.get("crypto_analysis_fallback", False) and self.inputs.get("crypto_analysis_result") is not None
        )

        available_crews = []
        if stock_available:
            available_crews.append("stock")
        if etf_available:
            available_crews.append("etf")
        if crypto_available:
            available_crews.append("crypto")

        failed_crews = []
        if self.inputs.get("stock_analysis_error"):
            failed_crews.append("stock")
        if self.inputs.get("etf_analysis_error"):
            failed_crews.append("etf")
        if self.inputs.get("crypto_analysis_error"):
            failed_crews.append("crypto")

        disabled_crews = []
        if self.inputs.get("stock_analysis_disabled"):
            disabled_crews.append("stock")
        if self.inputs.get("etf_analysis_disabled"):
            disabled_crews.append("etf")
        if self.inputs.get("crypto_analysis_disabled"):
            disabled_crews.append("crypto")

        return {
            "any_available": len(available_crews) > 0,
            "stock_available": stock_available,
            "etf_available": etf_available,
            "crypto_available": crypto_available,
            "available_crews": available_crews,
            "failed_crews": failed_crews,
            "disabled_crews": disabled_crews,
            "total_available": len(available_crews),
            "total_failed": len(failed_crews),
            "total_disabled": len(disabled_crews),
        }

    def _extract_market_conditions(self) -> dict[str, Any]:
        """Extract market conditions from core analysis results."""
        conditions = {}

        if self.inputs.get("stock_analysis_result"):
            # Extract market sentiment and trends from stock analysis
            conditions["stock_market_sentiment"] = "Available from stock analysis"

        if self.inputs.get("etf_analysis_result"):
            # Extract sector trends from ETF analysis
            conditions["sector_trends"] = "Available from ETF analysis"

        if self.inputs.get("crypto_analysis_result"):
            # Extract crypto market dynamics
            conditions["crypto_market_dynamics"] = "Available from crypto analysis"

        return conditions

    def _extract_market_context_from_core_analysis(self, core_analysis_data: dict[str, Any]) -> dict[str, Any]:
        """
        Extract market context information from core analysis results.

        Args:
            core_analysis_data: Dictionary containing core analysis results

        Returns:
            Dictionary with extracted market context

        """
        market_context = {
            "overall_sentiment": "neutral",
            "market_trends": [],
            "risk_factors": [],
            "opportunities": [],
            "sector_analysis": {},
        }

        try:
            # Extract from stock analysis
            if "stock_analysis" in core_analysis_data:
                stock_data = core_analysis_data["stock_analysis"]

                # Extract market sentiment from stock analysis
                if "market_sentiments" in stock_data:
                    sentiments = stock_data["market_sentiments"]
                    if sentiments and len(sentiments) > 0:
                        # Calculate overall sentiment
                        positive_count = sum(1 for s in sentiments if s.get("sentiment", "").lower() in ["positive", "bullish"])
                        negative_count = sum(1 for s in sentiments if s.get("sentiment", "").lower() in ["negative", "bearish"])

                        if positive_count > negative_count:
                            market_context["overall_sentiment"] = "positive"
                        elif negative_count > positive_count:
                            market_context["overall_sentiment"] = "negative"

                # Extract sector information
                if "sector_analysis" in stock_data:
                    market_context["sector_analysis"] = stock_data["sector_analysis"]

            # Extract from ETF analysis
            if "etf_analysis" in core_analysis_data:
                etf_data = core_analysis_data["etf_analysis"]

                # Extract sector trends from ETF analysis
                if "sector_trends" in etf_data:
                    market_context["market_trends"].extend(etf_data["sector_trends"])

            # Extract from crypto analysis
            if "crypto_analysis" in core_analysis_data:
                crypto_data = core_analysis_data["crypto_analysis"]

                # Extract crypto market dynamics
                if "market_dynamics" in crypto_data:
                    market_context["market_trends"].append(f"Crypto: {crypto_data['market_dynamics']}")

            # Extract common risk factors
            for analysis_type, analysis_data in core_analysis_data.items():
                if "risk_factors" in analysis_data:
                    risk_factors = analysis_data["risk_factors"]
                    if isinstance(risk_factors, list):
                        market_context["risk_factors"].extend(risk_factors)

            # Extract opportunities
            for analysis_type, analysis_data in core_analysis_data.items():
                if "opportunities" in analysis_data:
                    opportunities = analysis_data["opportunities"]
                    if isinstance(opportunities, list):
                        market_context["opportunities"].extend(opportunities)

            logger.debug(f"Extracted market context from {len(core_analysis_data)} core analysis results")
            return market_context

        except Exception as e:
            logger.warning(f"Failed to extract market context from core analysis: {e}")
            return market_context

    @listen("check_investment_discovery")
    def pre_validate_reporter_input(self) -> None:
        """
        Validate ReporterInput payload before triggering the final report.

        Uses the integrated data system to consolidate all crew outputs
        and validate the reporter input contract, including core analysis data.
        """
        try:
            logger.info("Consolidating data for reporter input validation with enhanced error handling")

            # Get core analysis status
            core_analysis_status = self._check_core_analysis_availability()

            # Get consolidated data from integration system (includes core analysis)
            try:
                consolidated_data = self.data_accessor.get_consolidated_reporter_input()
            except Exception as e:
                logger.warning(f"Failed to get consolidated data from integration system: {e}")
                consolidated_data = {}

            # Store consolidated data for report crew
            self.inputs["consolidated_data"] = consolidated_data

            # Add integrated data access information
            self.inputs["integrated_data_available"] = len(consolidated_data) > 0
            self.inputs["market_sentiment"] = consolidated_data.get("market_sentiment", {})
            self.inputs["ticker_validation"] = consolidated_data.get("ticker_validation", {})
            self.inputs["aplus_opportunities"] = consolidated_data.get("aplus_opportunities")
            self.inputs["portfolio_allocation_updates"] = consolidated_data.get("portfolio_allocation_updates", [])
            self.inputs["aplus_availability_status"] = consolidated_data.get("aplus_availability_status", "UNAVAILABLE")

            # Enhanced: Add core analysis data to reporter inputs with error handling
            try:
                core_analysis_summary = self._prepare_core_analysis_summary(consolidated_data)
                self.inputs["core_analysis_summary"] = core_analysis_summary
            except Exception as e:
                logger.warning(f"Failed to prepare core analysis summary: {e}")
                self.inputs["core_analysis_summary"] = {
                    "available_crews": core_analysis_status["available_crews"],
                    "failed_crews": core_analysis_status["failed_crews"],
                    "disabled_crews": core_analysis_status["disabled_crews"],
                    "error": "Failed to prepare detailed summary",
                }

            # Add individual core analysis results for detailed reporting (with error handling)
            for crew_type in ["stock", "etf", "crypto"]:
                if crew_type in consolidated_data:
                    self.inputs[f"{crew_type}_analysis_data"] = consolidated_data[crew_type]
                    logger.info(f"Core analysis data available for {crew_type} in reporter input")
                else:
                    self.inputs[f"{crew_type}_analysis_data"] = None
                    if core_analysis_status[f"{crew_type}_available"]:
                        logger.warning(f"Core analysis data missing for {crew_type} despite being marked available")

            # Add error and fallback information to reporter inputs
            self.inputs["core_analysis_status"] = core_analysis_status
            self.inputs["system_health"] = self.error_handler.get_system_health_status()

            # Add error summaries for transparency in reporting
            error_summaries = {}
            for crew_name in ["stock", "etf", "crypto"]:
                error_summaries[crew_name] = self.error_handler.get_error_summary(crew_name)
            self.inputs["error_summaries"] = error_summaries

            # Log consolidation results
            crew_count = len([k for k in consolidated_data.keys() if k in ["stock", "etf", "crypto", "discovery", "portfolio"]])
            core_analysis_count = len([k for k in consolidated_data.keys() if k in ["stock", "etf", "crypto"]])

            logger.info(f"Consolidated data from {crew_count} crews (including {core_analysis_count} core analysis crews)")
            logger.info(
                f"Core analysis status: {core_analysis_status['total_available']} available, {core_analysis_status['total_failed']} failed, {core_analysis_status['total_disabled']} disabled"
            )

            if consolidated_data.get("aplus_opportunities"):
                logger.info("A+ opportunities available in consolidated data")

            if consolidated_data.get("market_sentiment", {}).get("data_quality") != "ERROR":
                sentiment_quality = consolidated_data.get("market_sentiment", {}).get("data_quality", "UNKNOWN")
                logger.info(f"Market sentiment data quality: {sentiment_quality}")

            # Enhanced logging for core analysis integration
            if core_analysis_summary.get("available_analyses"):
                logger.info(f"Core analysis summary includes: {', '.join(core_analysis_summary['available_analyses'])}")
                sentiment = core_analysis_summary.get("overall_market_sentiment", "unknown")
                logger.info(f"Overall market sentiment from core analysis: {sentiment}")

            # Fallback to example validation if needed
            if crew_count == 0:
                logger.warning("No crew data available, falling back to example validation")
                project_root = Path(__file__).resolve().parents[2]
                example = project_root / "docs/schemas/examples/reporter_input.example.json"
                if example.exists():
                    model = validate_reporter_input(example)
                    self.inputs["reporter_input"] = model.model_dump(mode="json")
                    logger.info("ReporterInput validated using example data")
                else:
                    logger.warning("No example data available for validation")

            logger.info("Reporter input preparation completed with integrated data and core analysis")

        except Exception as e:
            logger.error(f"Reporter input preparation failed: {e}", exc_info=True)
            # Continue with graceful degradation
            self.inputs["integrated_data_error"] = str(e)

    def _prepare_core_analysis_summary(self, consolidated_data: dict[str, Any]) -> dict[str, Any]:
        """
        Prepare a summary of core analysis results for the reporter.

        Args:
            consolidated_data: Consolidated data from all crews

        Returns:
            Dictionary with core analysis summary

        """
        summary = {
            "available_analyses": [],
            "total_recommendations": 0,
            "overall_market_sentiment": "neutral",
            "key_insights": [],
            "risk_assessment": {
                "overall_risk_level": "medium",
                "major_risk_factors": [],
            },
            "investment_opportunities": {
                "stocks": [],
                "etfs": [],
                "cryptos": [],
            },
        }

        try:
            # Process each core analysis type
            for crew_type in ["stock", "etf", "crypto"]:
                if crew_type in consolidated_data:
                    summary["available_analyses"].append(crew_type)
                    crew_data = consolidated_data[crew_type]

                    # Extract recommendations
                    if "raw_output" in crew_data:
                        # Count recommendations in raw output
                        raw_output = str(crew_data["raw_output"]).lower()
                        if "buy" in raw_output or "strong buy" in raw_output:
                            summary["total_recommendations"] += raw_output.count("buy")

                    # Extract key insights from tasks output
                    if "tasks_output" in crew_data:
                        for task in crew_data["tasks_output"]:
                            if isinstance(task, dict) and "raw" in task:
                                task_content = str(task["raw"])
                                if len(task_content) > 100:  # Meaningful content
                                    summary["key_insights"].append(
                                        {
                                            "source": crew_type,
                                            "insight": task_content[:200] + "..." if len(task_content) > 200 else task_content,
                                        }
                                    )

                    # Extract investment opportunities
                    opportunities_key = f"{crew_type}s" if crew_type != "crypto" else "cryptos"
                    if opportunities_key in summary["investment_opportunities"]:
                        # Extract symbols or opportunities from the analysis
                        if "pydantic" in crew_data and crew_data["pydantic"]:
                            pydantic_data = crew_data["pydantic"]
                            if "opportunities" in pydantic_data:
                                summary["investment_opportunities"][opportunities_key].extend(
                                    pydantic_data["opportunities"][:3]  # Top 3
                                )

            # Determine overall market sentiment
            sentiment_data = consolidated_data.get("market_sentiment", {})
            if sentiment_data.get("aggregated_scores"):
                scores = sentiment_data["aggregated_scores"]
                positive = scores.get("positive", 0)
                negative = scores.get("negative", 0)

                if positive > negative + 0.1:
                    summary["overall_market_sentiment"] = "positive"
                elif negative > positive + 0.1:
                    summary["overall_market_sentiment"] = "negative"
                else:
                    summary["overall_market_sentiment"] = "neutral"

            # Extract major risk factors
            for crew_type in ["stock", "etf", "crypto"]:
                if crew_type in consolidated_data:
                    crew_data = consolidated_data[crew_type]
                    if "raw_output" in crew_data:
                        raw_output = str(crew_data["raw_output"]).lower()
                        # Look for risk-related keywords
                        risk_keywords = ["risk", "volatility", "uncertainty", "concern", "warning"]
                        for keyword in risk_keywords:
                            if keyword in raw_output:
                                summary["risk_assessment"]["major_risk_factors"].append(f"{crew_type}: {keyword}")

            # Determine overall risk level
            risk_factor_count = len(summary["risk_assessment"]["major_risk_factors"])
            if risk_factor_count >= 5:
                summary["risk_assessment"]["overall_risk_level"] = "high"
            elif risk_factor_count >= 2:
                summary["risk_assessment"]["overall_risk_level"] = "medium"
            else:
                summary["risk_assessment"]["overall_risk_level"] = "low"

            logger.debug(f"Prepared core analysis summary with {len(summary['available_analyses'])} analyses")
            return summary

        except Exception as e:
            logger.warning(f"Failed to prepare core analysis summary: {e}")
            return summary

    @listen("pre_validate_reporter_input")
    def report(self) -> None:
        """Generate a consolidated report after all analyses are complete."""
        try:
            logger.info("Starting report generation with enhanced error handling")

            # Get core analysis status for reporting
            core_analysis_status = self._check_core_analysis_availability()
            system_health = self.error_handler.get_system_health_status()

            # Log system status before report generation
            logger.info(f"System health status: {system_health['overall_status']}")
            if system_health["degraded_crews"]:
                logger.warning(f"Degraded crews detected: {system_health['degraded_crews']}")

            # Initialize Report crew and validate inputs
            report_crew = ReportCrew()

            # Note: data_accessor and integration_manager are available as instance attributes
            # but not passed to CrewAI inputs due to serialization constraints
            if hasattr(self, "data_accessor"):
                logger.info("Data integration system made available to report crew")

            # Validate reporter input using the crew's validator (with error handling)
            try:
                report_crew.validate_reporter_input(self.inputs)
                logger.info("Reporter input validation passed")
            except Exception as e:
                logger.warning(f"Reporter input validation warning: {e}")
                # Continue with graceful degradation as per ReporterInputValidator design

            # Log data integration status for report generation
            if self.inputs.get("integrated_data_available"):
                logger.info("Report generation using integrated data system")

                # Log available integrated data components
                if self.inputs.get("market_sentiment"):
                    sentiment_quality = self.inputs["market_sentiment"].get("data_quality", "UNKNOWN")
                    logger.info(f"Market sentiment data available (quality: {sentiment_quality})")

                if self.inputs.get("ticker_validation"):
                    validation_rate = self.inputs["ticker_validation"].get("validation_summary", {}).get("validation_rate", 0)
                    logger.info(f"Ticker validation data available (rate: {validation_rate:.1f}%)")

                if self.inputs.get("aplus_opportunities"):
                    logger.info("A+ opportunities data available for report")

                # Log core analysis status
                if core_analysis_status["any_available"]:
                    logger.info(f"Core analysis data available for report: {core_analysis_status['available_crews']}")
                else:
                    logger.warning("No core analysis data available for report")

                # Log data availability warnings
                if self.inputs.get("stale_data_warnings"):
                    logger.warning("Report generated with stale data warnings")

                # Log error information for transparency
                if core_analysis_status["failed_crews"]:
                    logger.warning(f"Report includes fallback data for failed crews: {core_analysis_status['failed_crews']}")

            else:
                logger.warning("Report generation without integrated data system")

            # Add system status to inputs for report transparency
            self.inputs["system_status_for_report"] = {
                "core_analysis_status": core_analysis_status,
                "system_health": system_health,
                "degraded_functionality": self._get_degraded_functionality_summary(),
                "report_generation_timestamp": datetime.now().isoformat(),
            }

            # Execute the report crew
            report_crew.crew().kickoff(inputs=self.inputs)

            logger.info("Report generation completed successfully with enhanced error handling")

        except Exception as e:
            logger.error(f"Report generation failed: {str(e)}", exc_info=True)
            # Continue with graceful degradation instead of raising
            self.inputs["report_generation_error"] = str(e)
            logger.warning("Report generation failed - system will attempt to continue")

            # Try to generate a minimal error report
            try:
                self._generate_error_report(e)
            except Exception as fallback_error:
                logger.error(f"Fallback error report generation also failed: {fallback_error}")

    def _get_degraded_functionality_summary(self) -> dict[str, Any]:
        """Get summary of degraded functionality across the system."""
        degraded_summary = {
            "has_degraded_functionality": False,
            "degraded_crews": [],
            "fallback_strategies_used": [],
            "missing_features": [],
            "data_quality_issues": [],
        }

        # Check for crew-specific degraded functionality
        for crew_name in ["stock", "etf", "crypto"]:
            degraded_functionality = self.inputs.get(f"{crew_name}_degraded_functionality", [])
            if degraded_functionality:
                degraded_summary["has_degraded_functionality"] = True
                degraded_summary["degraded_crews"].append(crew_name)
                degraded_summary["missing_features"].extend(degraded_functionality)

            fallback_strategy = self.inputs.get(f"{crew_name}_fallback_strategy")
            if fallback_strategy:
                degraded_summary["fallback_strategies_used"].append(f"{crew_name}: {fallback_strategy}")

        # Check for data quality issues
        if self.inputs.get("stale_data_warnings"):
            degraded_summary["data_quality_issues"].append("stale_data")

        if self.inputs.get("integrated_data_error"):
            degraded_summary["data_quality_issues"].append("integration_error")

        return degraded_summary

    def _generate_error_report(self, error: Exception) -> None:
        """Generate a minimal error report when main report generation fails."""
        logger.info("Attempting to generate minimal error report")

        try:
            # Create minimal report data
            error_report_data = {
                "report_type": "error_report",
                "generation_timestamp": datetime.now().isoformat(),
                "error_message": str(error),
                "system_status": self.error_handler.get_system_health_status(),
                "available_data": {
                    "portfolio_review": bool(self.inputs.get("portfolio_review")),
                    "investment_discovery": bool(self.inputs.get("investment_discovery_result")),
                    "portfolio_rebalancing": bool(self.inputs.get("portfolio_rebalancing_result")),
                    "core_analysis": self._check_core_analysis_availability(),
                },
            }

            # Save error report to output directory
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)

            error_report_path = output_dir / f"error_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(error_report_path, "w", encoding="utf-8") as f:
                json.dump(error_report_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Minimal error report generated at {error_report_path}")

        except Exception as e:
            logger.error(f"Failed to generate minimal error report: {e}")


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
