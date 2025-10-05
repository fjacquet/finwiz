#!/usr/bin/env python
"""
Flow orchestration logic for FinWiz application.

This module contains the main FinwizFlow class that orchestrates the
financial analysis workflow using CrewAI flows.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from crewai.flow import Flow, and_, listen, start

from finwiz.crew_factory import CrewFactory
from finwiz.flow_state import FinwizState, FlowStateManager
from finwiz.integration.data_accessor import CrewDataAccessor
from finwiz.integration.manager import CrewDataIntegrationManager
from finwiz.orchestrators.portfolio_review import run as run_portfolio_review
from finwiz.schemas.validate import validate_reporter_input
from finwiz.tools.logger import get_logger
from finwiz.utils.core_analysis_error_handler import CoreAnalysisErrorHandler
from finwiz.utils.feature_flags import is_feature_enabled

logger = get_logger(__name__)


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

        # Initialize flow state manager
        self.state_manager = FlowStateManager()
        logger.info("Flow state manager initialized")

        # Initialize crew factory
        self.crew_factory = CrewFactory(self.integration_manager, self.error_handler)
        logger.info("Crew factory initialized")

        # Create inputs using state manager
        self.inputs = self.state_manager.create_flow_inputs()
        logger.info("Flow inputs created via state manager")

    @listen("validate_data_integration")
    def check_crypto(self) -> None:
        """Initiate the cryptocurrency analysis crew after data validation."""
        result_data = self.crew_factory.execute_crypto_crew(self.inputs)
        self.inputs.update(result_data)

    @listen("validate_data_integration")
    def check_stock(self) -> None:
        """Initiate the stock analysis crew after data validation."""
        result_data = self.crew_factory.execute_stock_crew(self.inputs)
        self.inputs.update(result_data)

    @listen("validate_data_integration")
    def check_etf(self) -> None:
        """Initiate the ETF analysis crew after data validation."""
        result_data = self.crew_factory.execute_etf_crew(self.inputs)
        self.inputs.update(result_data)

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
        if not is_feature_enabled("portfolio_rebalancing"):
            logger.info("Portfolio rebalancing disabled via feature flag")
            return

        try:
            # Check core analysis availability
            core_analysis_status = self._check_core_analysis_availability()

            # Create crew inputs via factory
            crew_inputs = self.crew_factory.create_crew_inputs_for_portfolio_rebalancing(self.inputs, core_analysis_status)

            # Execute portfolio rebalancing crew via factory
            result_data = self.crew_factory.execute_portfolio_rebalancing_crew(crew_inputs)
            self.inputs.update(result_data)

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

                # Create crew inputs via factory
                crew_inputs = self.crew_factory.create_crew_inputs_for_investment_discovery(
                    self.inputs, core_analysis_status, upstream_data, core_analysis_data
                )

                # Log enhanced inputs
                logger.info(f"Investment discovery enhanced with {len(core_analysis_data)} core analysis results")
                if core_analysis_data:
                    logger.info(f"Core analysis types available: {list(core_analysis_data.keys())}")
                if core_analysis_status["failed_crews"]:
                    logger.warning(f"Core analysis crews failed: {core_analysis_status['failed_crews']}")

                # Execute investment discovery crew via factory
                result_data = self.crew_factory.execute_investment_discovery_crew(crew_inputs)
                self.inputs.update(result_data)

                # Store crew result in integration system (use result_data since result is not defined)
                if "result" in result_data:
                    crew_result = result_data["result"]
                    self.integration_manager.store_crew_output("discovery", crew_result)

                    # Store crew result - convert CrewOutput to string for template interpolation
                    if hasattr(crew_result, "raw"):
                        result_text = str(crew_result.raw)
                        self.inputs["investment_discovery_result"] = result_text
                    else:
                        result_text = str(crew_result)
                        self.inputs["investment_discovery_result"] = result_text
                else:
                    # Fallback if no result in result_data
                    self.inputs["investment_discovery_result"] = str(result_data)

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
        return self.state_manager.check_core_analysis_availability(self.inputs)

    def _extract_market_conditions(self) -> dict[str, Any]:
        """Extract market conditions from core analysis results."""
        return self.state_manager.extract_market_conditions(self.inputs)

    def _extract_market_context_from_core_analysis(self, core_analysis_data: dict[str, Any]) -> dict[str, Any]:
        """Extract market context information from core analysis results."""
        return self.state_manager.extract_market_context_from_core_analysis(core_analysis_data)

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
                f"Core analysis status: {core_analysis_status['total_available']} available, "
                f"{core_analysis_status['total_failed']} failed, {core_analysis_status['total_disabled']} disabled"
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
        """Prepare a summary of core analysis results for the reporter."""
        return self.state_manager.prepare_core_analysis_summary(consolidated_data)

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

            # Note: data_accessor and integration_manager are available as instance attributes
            # but not passed to CrewAI inputs due to serialization constraints
            if hasattr(self, "data_accessor"):
                logger.info("Data integration system made available to report crew")

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

            # Execute report crew via factory
            result_data = self.crew_factory.execute_report_crew(self.inputs)
            self.inputs.update(result_data)

            if result_data.get("report_generation_success"):
                logger.info("Report generation completed successfully with enhanced error handling")
            else:
                logger.warning("Report generation completed with errors")

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
        """Get summary of degraded functionality for reporting."""
        return self.state_manager.get_degraded_functionality_summary(self.inputs)

    def _generate_error_report(self, error: Exception) -> None:
        """Generate a minimal error report when main report generation fails."""
        try:
            error_report_data = {
                "error_type": type(error).__name__,
                "error_message": str(error),
                "timestamp": datetime.now().isoformat(),
                "system_status": "FAILED",
                "available_data": list(self.inputs.keys()),
                "recommendations": [
                    "Check API key configuration",
                    "Verify network connectivity",
                    "Review application logs for detailed error information",
                    "Consider running individual crew analyses to isolate issues",
                ],
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
