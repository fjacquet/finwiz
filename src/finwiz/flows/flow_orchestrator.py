#!/usr/bin/env python
"""
Flow orchestration logic for FinWiz application.

This module contains the main FinwizFlow class that orchestrates the
financial analysis workflow using CrewAI flows.
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from crewai.flow import Flow, and_, listen, start
from crewai.flow.persistence import persist

from finwiz.config.batch_prefetch_config import get_batch_prefetch_config
from finwiz.config.resilience_config import get_resilience_config
from finwiz.crew_factory import CrewFactory
from finwiz.flow_state import DeepAnalysisResult, FinwizState, FlowStateManager
from finwiz.integration.data_accessor import CrewDataAccessor
from finwiz.integration.data_availability_tracker import DataAvailabilityTracker
from finwiz.integration.manager import CrewDataIntegrationManager
from finwiz.orchestrators.portfolio_review import run as run_portfolio_review
from finwiz.schemas.validate import validate_reporter_input
from finwiz.tools.logger import get_logger
from finwiz.utils.core_analysis_error_handler import CoreAnalysisErrorHandler
from finwiz.utils.data_consolidation_validator import DataConsolidationValidator, DataRetrievalError
from finwiz.utils.feature_flags import is_feature_enabled
from finwiz.utils.report_data_validator import ReportDataValidator, ReportValidationError
from finwiz.utils.retry_handler import create_retry_decorator

logger = get_logger(__name__)


@persist()  # Enable automatic state persistence after each flow method
class FinwizFlow(Flow[FinwizState]):
    """
    Orchestrates the financial analysis workflow for FinWiz.

    This flow integrates analyses from cryptocurrency, stock, and ETF crews,
    and generates a consolidated investment report. It utilizes the crewAI
    Flow paradigm to manage task dependencies and execution.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the FinwizFlow instance."""
        logger.info("Initializing FinwizFlow with structured state management")
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

        # Initialize data availability tracker
        self.availability_tracker = DataAvailabilityTracker(
            stale_threshold_hours=168.0,  # 7 days
            logger=logger,
        )
        logger.info("Data availability tracker initialized")

        # Initialize resilience configuration
        self.resilience_config = get_resilience_config()
        logger.info(
            f"Resilience configuration loaded: "
            f"max_retries={self.resilience_config.max_retries}, "
            f"retry_base_delay={self.resilience_config.retry_base_delay}s, "
            f"retry_max_delay={self.resilience_config.retry_max_delay}s, "
            f"holding_timeout={self.resilience_config.holding_timeout}s, "
            f"flow_timeout={self.resilience_config.flow_timeout}s, "
            f"auto_resume={self.resilience_config.auto_resume}, "
            f"state_max_age_hours={self.resilience_config.state_max_age_hours}h, "
            f"parallel_limit={self.resilience_config.parallel_limit}, "
            f"deep_analysis_parallel_limit={self.resilience_config.deep_analysis_parallel_limit}"
        )

        # Create retry decorator with resilience configuration
        self.retry_decorator = create_retry_decorator(self.resilience_config)
        logger.info("Retry decorator initialized with exponential backoff")

        # Initialize batch prefetch configuration (Requirements: 17.57, 17.58, 17.59, 17.60)
        self.batch_prefetch_config = get_batch_prefetch_config(log_config=True)
        logger.info("Batch prefetch configuration loaded and validated")

        # Initialize structured state (replaces self.inputs)
        # Note: self.state is automatically managed by Flow[FinwizState]
        # We just need to ensure it's initialized with session data
        if not hasattr(self, "state") or self.state is None:
            self.state = self.state_manager.create_initial_state()
            logger.info("Flow state initialized with session metadata")
        else:
            logger.info("Flow state already initialized by Flow framework")

    def _execute_crew_with_error_handling(
        self, crew_name: str, crew_instance: Any, crew_inputs: dict[str, Any], ticker: str = ""
    ) -> tuple[Any | None, str | None]:
        """
        Execute crew with error handling and state tracking.

        This helper wraps crew execution in try-except blocks, logs detailed
        error messages, tracks failures in state, and continues Flow execution
        when individual crews fail (graceful degradation).

        Handles crew execution failures (Requirement 17.52, 17.53, 17.54, 17.55):
        - Continues with remaining tickers if one fails
        - Collects all errors in Flow state
        - Logs detailed error messages

        Args:
            crew_name: Name of crew for logging and error tracking
            crew_instance: Instantiated crew object
            crew_inputs: Input dictionary for crew.kickoff()
            ticker: Optional ticker symbol for per-ticker tracking

        Returns:
            Tuple of (crew_result, error_message)
            - crew_result: Result from crew.kickoff() or None if failed
            - error_message: Error message string or None if successful

        Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 17.52, 17.53, 17.54, 17.55

        """
        try:
            logger.info(f"Executing {crew_name}" + (f" for {ticker}" if ticker else ""))
            result = crew_instance.crew().kickoff(inputs=crew_inputs)
            logger.info(f"{crew_name} execution completed successfully" + (f" for {ticker}" if ticker else ""))

            # Track successful execution in state
            if not hasattr(self.state, "crew_execution_status"):
                self.state.crew_execution_status = {}
            crew_key = f"{crew_name}_{ticker}" if ticker else crew_name
            self.state.crew_execution_status[crew_key] = "completed"

            return result, None

        except Exception as e:
            # Log detailed error message with crew name and ticker (Requirement 17.53)
            error_msg = f"{crew_name} failed" + (f" for {ticker}" if ticker else "") + f": {str(e)}"
            logger.error(error_msg, exc_info=True)

            # Track failed crew in state (Requirement 17.54)
            if not hasattr(self.state, "crew_execution_status"):
                self.state.crew_execution_status = {}
            crew_key = f"{crew_name}_{ticker}" if ticker else crew_name
            self.state.crew_execution_status[crew_key] = "failed"

            # Track error message in state (Requirement 17.54)
            if not hasattr(self.state, "crew_execution_errors"):
                self.state.crew_execution_errors = {}
            self.state.crew_execution_errors[crew_key] = error_msg

            # Add to errors list for consolidated summary (Requirement 17.54)
            if not hasattr(self.state, "errors"):
                self.state.errors = []
            self.state.errors.append(error_msg)

            # Log continuation message (graceful degradation - Requirement 17.55)
            logger.info(f"Continuing Flow execution after {crew_name} failure (graceful degradation)")

            return None, error_msg

    def _generate_error_summary(self) -> dict[str, Any]:
        """
        Generate error summary for final report.

        Collects all errors from Flow state and generates a structured summary
        for inclusion in the final report.

        Returns:
            dict: Error summary with categorized errors

        Requirements: 17.54, 17.55

        """
        error_summary = {
            "total_errors": len(self.state.errors) if hasattr(self.state, "errors") else 0,
            "failed_crews": [],
            "failed_tickers": [],
            "crew_execution_errors": {},
            "has_errors": False,
        }

        # Collect failed crews
        if hasattr(self.state, "crew_execution_status"):
            failed_crews = [crew_key for crew_key, status in self.state.crew_execution_status.items() if status == "failed"]
            error_summary["failed_crews"] = failed_crews
            error_summary["has_errors"] = len(failed_crews) > 0

        # Collect failed tickers
        if hasattr(self.state, "failed_holdings"):
            error_summary["failed_tickers"] = self.state.failed_holdings
            error_summary["has_errors"] = error_summary["has_errors"] or len(self.state.failed_holdings) > 0

        # Collect crew execution errors
        if hasattr(self.state, "crew_execution_errors"):
            error_summary["crew_execution_errors"] = self.state.crew_execution_errors

        # Log error summary
        if error_summary["has_errors"]:
            logger.warning("=" * 80)
            logger.warning("ERROR SUMMARY")
            logger.warning("=" * 80)
            logger.warning(f"Total errors: {error_summary['total_errors']}")
            logger.warning(f"Failed crews: {len(error_summary['failed_crews'])}")
            logger.warning(f"Failed tickers: {len(error_summary['failed_tickers'])}")
            if error_summary["failed_crews"]:
                logger.warning(f"  Crews: {', '.join(error_summary['failed_crews'])}")
            if error_summary["failed_tickers"]:
                logger.warning(f"  Tickers: {', '.join(error_summary['failed_tickers'])}")
            logger.warning("=" * 80)
        else:
            logger.info("No errors detected in Flow execution")

        return error_summary

    def _fallback_to_sequential_mode(self, tickers: list[str], reason: str) -> dict[str, Any]:
        """
        Fallback to sequential execution mode when batch pre-fetch fails.

        Detects if batch pre-fetch fails completely and falls back to live API
        calls per ticker (sequential mode). Logs fallback event and reason.

        Args:
            tickers: List of ticker symbols to analyze
            reason: Reason for fallback (e.g., "Batch pre-fetch failed completely")

        Returns:
            dict: Analysis results from sequential execution

        Requirements: 17.55

        """
        logger.warning("=" * 80)
        logger.warning("FALLBACK TO SEQUENTIAL MODE")
        logger.warning("=" * 80)
        logger.warning("Reason: %s", reason)
        logger.warning("Falling back to sequential execution for %d tickers", len(tickers))
        logger.warning("This will use live API calls per ticker (slower but more reliable)")
        logger.warning("=" * 80)

        # Disable batch prefetch mode in state
        self.state.batch_prefetch_enabled = False
        self.state.prefetched_data = {}

        # Log fallback event in state
        if not hasattr(self.state, "fallback_events"):
            self.state.fallback_events = []

        self.state.fallback_events.append(
            {"timestamp": datetime.now().isoformat(), "reason": reason, "ticker_count": len(tickers), "mode": "sequential"}
        )

        # Execute sequential analysis (existing logic without batch pre-fetch)
        logger.info("Starting sequential deep analysis (batch mode disabled)")

        # Call the existing _run_deep_analysis_on_holdings method
        # which will automatically use sequential mode since batch_prefetch_enabled is False
        results = self._run_deep_analysis_on_holdings()

        logger.info(f"Sequential execution completed: {len(results)} tickers analyzed")
        logger.info("=" * 80)

        return results

    def _update_state_from_dict(self, data: dict[str, Any]) -> None:
        """
        Update structured state from dictionary data.

        Helper method to update FinwizState fields from crew execution results.
        Only updates fields that exist in the FinwizState model.

        Args:
            data: Dictionary containing state updates

        """
        for key, value in data.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)
            else:
                logger.debug(f"Skipping unknown state field: {key}")

    def _state_to_dict(self) -> dict[str, Any]:
        """
        Convert current state to dictionary for crew factory compatibility.

        Returns:
            Dictionary representation of current state

        """
        return self.state.model_dump()

    def _parse_crew_output_for_holding(self, crew_result: Any, ticker: str, asset_class: str, crew_name: str) -> Any:
        """
        Parse crew output and extract scores for holding analysis.

        This helper method extracts fundamental, technical, and risk scores from
        crew execution results, calculates a composite score with risk penalty,
        and assigns a letter grade using the existing grading system.

        Args:
            crew_result: Result from crew.kickoff() execution
            ticker: Stock/ETF/crypto ticker symbol
            asset_class: Asset class (stock, etf, crypto)
            crew_name: Name of crew that performed analysis

        Returns:
            CrewAnalysisResult object with extracted scores and grade

        """
        from finwiz.cache.analysis_cache_manager import CrewAnalysisResult
        from finwiz.utils.grading_system import score_to_grade

        try:
            # Initialize default scores
            fundamental_score = None
            technical_score = None
            risk_score = None
            composite_score = 0.6  # Default fallback score

            # Try to extract scores from crew result
            # CrewAI results can be accessed via .pydantic or .raw attributes
            if hasattr(crew_result, "pydantic") and crew_result.pydantic:
                pydantic_data = crew_result.pydantic

                # Extract individual scores if available
                if hasattr(pydantic_data, "fundamental_score"):
                    fundamental_score = float(pydantic_data.fundamental_score)
                if hasattr(pydantic_data, "technical_score"):
                    technical_score = float(pydantic_data.technical_score)
                if hasattr(pydantic_data, "risk_score"):
                    # Risk score might be 0-5 scale, normalize to 0-1
                    raw_risk = float(pydantic_data.risk_score)
                    risk_score = raw_risk / 5.0 if raw_risk > 1.0 else raw_risk

                # Check if composite_score is already provided
                if hasattr(pydantic_data, "composite_score"):
                    composite_score = float(pydantic_data.composite_score)
                else:
                    # Calculate composite score from individual scores
                    scores = []
                    if fundamental_score is not None:
                        scores.append(fundamental_score)
                    if technical_score is not None:
                        scores.append(technical_score)

                    if scores:
                        # Average of available scores
                        composite_score = sum(scores) / len(scores)

                        # Apply risk penalty if risk score available
                        if risk_score is not None:
                            # Higher risk reduces composite score
                            # Risk penalty: 0-10% reduction based on risk level
                            risk_penalty = risk_score * 0.10
                            composite_score = composite_score * (1.0 - risk_penalty)

            elif hasattr(crew_result, "raw") and crew_result.raw:
                # Fallback: try to parse from raw text output
                raw_text = str(crew_result.raw).lower()

                # Look for score patterns in text (e.g., "fundamental score: 0.85")
                import re

                fund_match = re.search(r"fundamental[_\s]+score[:\s]+([0-9.]+)", raw_text)
                if fund_match:
                    fundamental_score = float(fund_match.group(1))

                tech_match = re.search(r"technical[_\s]+score[:\s]+([0-9.]+)", raw_text)
                if tech_match:
                    technical_score = float(tech_match.group(1))

                risk_match = re.search(r"risk[_\s]+score[:\s]+([0-9.]+)", raw_text)
                if risk_match:
                    raw_risk = float(risk_match.group(1))
                    risk_score = raw_risk / 5.0 if raw_risk > 1.0 else raw_risk

                # Calculate composite if we found scores
                scores = [s for s in [fundamental_score, technical_score] if s is not None]
                if scores:
                    composite_score = sum(scores) / len(scores)
                    if risk_score is not None:
                        risk_penalty = risk_score * 0.10
                        composite_score = composite_score * (1.0 - risk_penalty)

            # Ensure composite_score is within valid range
            composite_score = max(0.0, min(1.0, composite_score))

            # Calculate letter grade using existing grading system
            grade_info = score_to_grade(composite_score)

            logger.info(
                f"Parsed crew output for {ticker}: "
                f"composite={composite_score:.3f}, grade={grade_info.grade}, "
                f"fundamental={fundamental_score}, technical={technical_score}, risk={risk_score}"
            )

            # Create CrewAnalysisResult
            return CrewAnalysisResult(
                ticker=ticker,
                asset_class=asset_class,
                crew_name=crew_name,
                analyzed_at=datetime.now(),
                fundamental_score=fundamental_score,
                technical_score=technical_score,
                risk_score=risk_score,
                composite_score=composite_score,
                grade=grade_info.grade,
                metrics={
                    "grade_description": grade_info.description,
                    "recommended_action": grade_info.action,
                    "grade_emoji": grade_info.emoji,
                },
                raw_output={"crew_result": str(crew_result)[:500]},  # Store truncated output
            )

        except Exception as e:
            logger.error(f"Error parsing crew output for {ticker}: {e}", exc_info=True)

            # Return fallback result with default scores
            grade_info = score_to_grade(0.6)  # Default to C+ grade

            return CrewAnalysisResult(
                ticker=ticker,
                asset_class=asset_class,
                crew_name=crew_name,
                analyzed_at=datetime.now(),
                fundamental_score=None,
                technical_score=None,
                risk_score=None,
                composite_score=0.6,
                grade=grade_info.grade,
                metrics={
                    "grade_description": "Analysis incomplete - using fallback",
                    "recommended_action": grade_info.action,
                    "grade_emoji": grade_info.emoji,
                    "error": str(e),
                },
                raw_output={},
            )

    @listen("analyze_and_update_portfolio")
    def check_crypto(self) -> dict[str, Any]:
        """
        Initiate cryptocurrency discovery using Python analysis after deep analysis and portfolio update.

        Phase 4: Discovery (Parallel Execution)
        - Uses Python-based analysis to identify promising cryptocurrencies
        - Runs in parallel with check_stock and check_etf
        - Triggers: check_investment_discovery (Phase 4 consolidation)

        Flow Rationale: Discovery runs AFTER we know what we own and what needs improvement.
        This allows discovery to find A+ opportunities that match our identified needs.

        🚀 CRITICAL FIX: Replaced AI crew with Python analysis (Requirements 0.1-0.7)
        """
        logger.info("🚀 CRYPTO DISCOVERY: Using Python analysis instead of AI crew")

        try:
            # Use Python-based crypto analysis instead of AI crew
            from finwiz.scoring.crypto_analyzer import analyze_crypto_opportunities

            session_id = self.state.session_id or "default"
            crypto_results = analyze_crypto_opportunities(session_id)

            # Update state with Python results
            result_data = {
                "crypto_analysis_success": True,
                "crypto_result": crypto_results.get("analysis_summary", "Crypto analysis completed"),
                "crypto_opportunities": crypto_results.get("opportunities", []),
                "crypto_performance_metrics": crypto_results.get("performance_metrics", {}),
            }

            self._update_state_from_dict(result_data)

            # Track successful Python execution
            self.availability_tracker.track_data_source(
                source="crypto_crew",
                status="available",
                last_updated=datetime.now(),
                record_count=len(crypto_results.get("opportunities", [])),
            )

            logger.info(f"✅ Crypto discovery completed: {len(crypto_results.get('opportunities', []))} opportunities found")

        except Exception as e:
            logger.error(f"Crypto Python analysis failed: {e}")

            # Fallback result
            result_data = {
                "crypto_analysis_success": False,
                "crypto_analysis_error": str(e),
                "crypto_result": f"Crypto analysis failed: {e}",
            }

            self._update_state_from_dict(result_data)
            self.availability_tracker.track_data_source(source="crypto_crew", status="unavailable", error_message=str(e))

        return {"crypto_analysis_complete": True, "crypto_result": result_data.get("crypto_result", "")}

    @listen("analyze_and_update_portfolio")
    def check_stock(self) -> dict[str, Any]:
        """
        Initiate stock discovery using Python analysis after deep analysis and portfolio update.

        Phase 4: Discovery (Parallel Execution)
        - Uses Python-based analysis to identify promising stocks
        - Runs in parallel with check_crypto and check_etf
        - Triggers: check_investment_discovery (Phase 4 consolidation)

        Flow Rationale: Discovery runs AFTER we know what we own and what needs improvement.
        This allows discovery to find A+ opportunities that match our identified needs.

        🚀 CRITICAL FIX: Replaced AI crew with Python analysis (Requirements 0.1-0.7)
        """
        logger.info("🚀 STOCK DISCOVERY: Using Python analysis instead of AI crew")

        try:
            # Use Python-based stock analysis instead of AI crew
            from finwiz.scoring.stock_analyzer import analyze_stock_opportunities

            session_id = self.state.session_id or "default"
            stock_results = analyze_stock_opportunities(session_id)

            # Update state with Python results
            result_data = {
                "stock_analysis_success": True,
                "stock_result": stock_results.get("analysis_summary", "Stock analysis completed"),
                "stock_opportunities": stock_results.get("opportunities", []),
                "stock_performance_metrics": stock_results.get("performance_metrics", {}),
            }

            self._update_state_from_dict(result_data)

            # Track successful Python execution
            self.availability_tracker.track_data_source(
                source="stock_crew",
                status="available",
                last_updated=datetime.now(),
                record_count=len(stock_results.get("opportunities", [])),
            )

            logger.info(f"✅ Stock discovery completed: {len(stock_results.get('opportunities', []))} opportunities found")

        except Exception as e:
            logger.error(f"Stock Python analysis failed: {e}")

            # Fallback result
            result_data = {
                "stock_analysis_success": False,
                "stock_analysis_error": str(e),
                "stock_result": f"Stock analysis failed: {e}",
            }

            self._update_state_from_dict(result_data)
            self.availability_tracker.track_data_source(source="stock_crew", status="unavailable", error_message=str(e))

        return {"stock_analysis_complete": True, "stock_result": result_data.get("stock_result", "")}

    @listen("analyze_and_update_portfolio")
    def check_etf(self) -> dict[str, Any]:
        """
        Initiate ETF discovery using Python analysis after deep analysis and portfolio update.

        Phase 4: Discovery (Parallel Execution)
        - Uses Python-based analysis to identify stable ETFs
        - Runs in parallel with check_crypto and check_stock
        - Triggers: check_investment_discovery (Phase 4 consolidation)

        Flow Rationale: Discovery runs AFTER we know what we own and what needs improvement.
        This allows discovery to find A+ opportunities that match our identified needs.

        🚀 CRITICAL FIX: Replaced AI crew with Python analysis (Requirements 0.1-0.7)
        """
        logger.info("🚀 ETF DISCOVERY: Using Python analysis instead of AI crew")

        try:
            # Use Python-based ETF analysis instead of AI crew
            from finwiz.scoring.etf_analyzer import analyze_etf_opportunities

            session_id = self.state.session_id or "default"
            etf_results = analyze_etf_opportunities(session_id)

            # Update state with Python results
            result_data = {
                "etf_analysis_success": True,
                "etf_result": etf_results.get("analysis_summary", "ETF analysis completed"),
                "etf_opportunities": etf_results.get("opportunities", []),
                "etf_performance_metrics": etf_results.get("performance_metrics", {}),
            }

            self._update_state_from_dict(result_data)

            # Track successful Python execution
            self.availability_tracker.track_data_source(
                source="etf_crew",
                status="available",
                last_updated=datetime.now(),
                record_count=len(etf_results.get("opportunities", [])),
            )

            logger.info(f"✅ ETF discovery completed: {len(etf_results.get('opportunities', []))} opportunities found")

        except Exception as e:
            logger.error(f"ETF Python analysis failed: {e}")

            # Fallback result
            result_data = {"etf_analysis_success": False, "etf_analysis_error": str(e), "etf_result": f"ETF analysis failed: {e}"}

            self._update_state_from_dict(result_data)
            self.availability_tracker.track_data_source(source="etf_crew", status="unavailable", error_message=str(e))

        return {"etf_analysis_complete": True, "etf_result": result_data.get("etf_result", "")}

    @start()
    def validate_data_integration(self) -> dict[str, Any]:
        """
        Validate data integration system before crew execution.

        Phase 1: Data Validation
        - Checks data availability and freshness
        - Validates integration system is operational
        - Triggers: check_portfolio (Phase 2)
        """
        try:
            # Initialize resilience tracking for fresh start
            self.state.flow_start_time = datetime.now().isoformat()
            self.state.resume_from_checkpoint = False
            logger.info(f"Flow execution started at {self.state.flow_start_time}")
            logger.info("Persistence enabled via @persist() decorator - state will be saved after each method")

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

            # Store availability report in structured state
            self.state.data_availability_report = {
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
                self.state.stale_data_warnings = stale_warnings

            # Get refresh recommendations if needed
            if availability_report.stale_data or availability_report.missing_data:
                refresh_recommendations = self.integration_manager.get_refresh_recommendations()
                if refresh_recommendations:
                    logger.info(f"Recommended refresh order: {' -> '.join(refresh_recommendations)}")
                    self.state.refresh_recommendations = refresh_recommendations

            logger.info("Data integration validation completed")

            return {"validation_complete": True, "overall_status": availability_report.overall_status.value}

        except Exception as e:
            logger.error(f"Data integration validation failed: {str(e)}", exc_info=True)
            # Continue execution with degraded functionality
            self.state.data_integration_error = str(e)
            return {"validation_complete": False, "error": str(e)}

    def execute_deep_analysis_with_prefetch(self, tickers: list[str]) -> dict[str, Any]:
        """
        Execute deep analysis with batch data pre-fetching for performance optimization.

        This method implements the batch pre-fetch pattern to reduce deep analysis
        execution time from 3-6 hours to 20-40 minutes for 66+ holdings by:
        1. Pre-fetching ALL data in batch API calls (ONE call for all tickers)
        2. Caching pre-fetched data in Flow state
        3. Passing pre-fetched data to each crew instance for zero-latency access

        Handles complete batch failures with fallback to sequential mode (Requirement 17.55):
        - Detects if batch pre-fetch fails completely
        - Falls back to live API calls per ticker
        - Logs fallback event and reason

        Args:
            tickers: List of ticker symbols to analyze

        Returns:
            dict: Deep analysis results keyed by ticker (or empty dict if fallback triggered)

        Requirements: 17.36, 17.37, 17.38, 17.39, 17.40, 17.55

        """
        from finwiz.utils.batch_data_prefetcher import BatchDataPreFetcher

        logger.info("=" * 80)
        logger.info("BATCH PRE-FETCH MODE: Starting deep analysis with pre-fetched data")
        logger.info("=" * 80)

        # Step 1: Initialize batch data pre-fetcher with configuration
        try:
            prefetcher = BatchDataPreFetcher(
                session_id=self.state.session_id or "default",
                enable_alpha_vantage=False,  # Disabled by default - Yahoo Finance provides all essential data
                alpha_vantage_rate_limit=self.batch_prefetch_config.alpha_vantage_rate_limit,
            )
            logger.info(f"Initialized BatchDataPreFetcher for session: {self.state.session_id}")
        except Exception as e:
            # Initialization failed - fallback to sequential mode (Requirement 17.55)
            logger.error(f"Failed to initialize BatchDataPreFetcher: {e}")
            return self._fallback_to_sequential_mode(tickers, f"BatchDataPreFetcher initialization failed: {e}")

        # Step 2: Pre-fetch all data in batch (ONE API call for all tickers)
        prefetch_start = time.time()
        logger.info(f"Pre-fetching data for {len(tickers)} tickers in batch...")

        try:
            prefetched_data = prefetcher.prefetch_all_data(tickers)
        except Exception as e:
            # Complete batch pre-fetch failure - fallback to sequential mode (Requirement 17.55)
            logger.error(f"Batch pre-fetch failed completely: {e}")
            return self._fallback_to_sequential_mode(tickers, f"Batch pre-fetch failed: {e}")

        prefetch_duration = time.time() - prefetch_start

        # Step 3: Check if batch pre-fetch was successful enough to continue
        # If more than 50% of tickers failed, fallback to sequential mode (Requirement 17.55)
        successful_count = sum(1 for data in prefetched_data.values() if not data.get("failed", False))
        failure_rate = (len(tickers) - successful_count) / len(tickers) if tickers else 0

        if failure_rate > 0.5:
            # More than 50% failed - fallback to sequential mode
            logger.warning(f"Batch pre-fetch failure rate too high: {failure_rate * 100:.1f}%")
            return self._fallback_to_sequential_mode(
                tickers,
                f"Batch pre-fetch failure rate too high: {failure_rate * 100:.1f}% ({len(tickers) - successful_count}/{len(tickers)} failed)",
            )

        # Step 4: Store pre-fetched data in Flow state
        self.state.prefetched_data = prefetched_data
        self.state.batch_prefetch_enabled = True

        logger.info(f"✓ Pre-fetch completed in {prefetch_duration:.1f}s")
        logger.info(f"✓ Pre-fetched data stored in Flow state for {len(prefetched_data)} tickers")
        logger.info(f"✓ Success rate: {successful_count}/{len(tickers)} ({successful_count / len(tickers) * 100:.1f}%)")

        # Step 5: Calculate and store metrics
        self.state.batch_prefetch_metrics = {
            "total_tickers": len(tickers),
            "successful_tickers": successful_count,
            "failed_tickers": len(tickers) - successful_count,
            "failure_rate": failure_rate,
            "prefetch_duration_seconds": prefetch_duration,
            "time_per_ticker_seconds": prefetch_duration / len(tickers) if tickers else 0,
            "prefetch_timestamp": datetime.now().isoformat(),
        }

        logger.info("Batch pre-fetch metrics:")
        logger.info(f"  Total tickers: {self.state.batch_prefetch_metrics['total_tickers']}")
        logger.info(f"  Successful: {self.state.batch_prefetch_metrics['successful_tickers']}")
        logger.info(f"  Failed: {self.state.batch_prefetch_metrics['failed_tickers']}")
        logger.info(f"  Failure rate: {self.state.batch_prefetch_metrics['failure_rate'] * 100:.1f}%")
        logger.info(f"  Duration: {self.state.batch_prefetch_metrics['prefetch_duration_seconds']:.1f}s")
        logger.info(f"  Time per ticker: {self.state.batch_prefetch_metrics['time_per_ticker_seconds']:.2f}s")

        # Step 6: Execute deep analysis with pre-fetched data
        # This will be handled by the crew execution loop in subtask 4.3
        logger.info("Pre-fetch complete. Ready for crew execution with zero API latency.")
        logger.info("=" * 80)

        return prefetched_data

    def _run_deep_analysis_on_holdings(self) -> dict[str, Any]:
        """
        Run DeepAnalysisCrew on each portfolio holding.

        Helper method for analyze_and_update_portfolio() that performs deep analysis
        on all holdings in the portfolio review.

        This method now supports batch pre-fetch mode (Requirement 17.41, 17.42):
        - Checks if batch_prefetch_enabled in environment
        - If enabled, calls execute_deep_analysis_with_prefetch() first
        - Then iterates through holdings and injects pre-fetched data into crews

        Backward Compatibility (Requirements 17.48, 17.49, 17.50, 17.51):
        - Detects single-ticker vs portfolio mode automatically
        - Single-ticker mode: Uses existing tools without pre-fetched data
        - Portfolio mode (66+ holdings): Enables batch pre-fetch automatically
        - Maintains all existing single-ticker behavior

        Returns:
            dict: Deep analysis results keyed by ticker

        """
        # Load holdings from structured Flow state
        if not hasattr(self.state, "portfolio_review") or not self.state.portfolio_review:
            logger.warning("No portfolio review data available in Flow state")
            return {}

        # Portfolio review JSON has nested structure: {"portfolio_review": {"holdings": [...]}}
        portfolio_data = self.state.portfolio_review
        if "portfolio_review" in portfolio_data:
            # Nested structure
            holdings = portfolio_data["portfolio_review"].get("holdings", [])
        else:
            # Flat structure (fallback)
            holdings = portfolio_data.get("holdings", [])

        if not holdings:
            logger.warning("No holdings found in portfolio review data")
            return {}

        # Mode detection logic (Requirement 17.51)
        # Automatically enable batch mode for portfolios with many holdings
        is_portfolio_mode = len(holdings) >= self.batch_prefetch_config.min_holdings_for_batch

        # Final decision: Enable batch mode if both conditions are met
        # - Configuration allows it (default: true)
        # - We're analyzing a portfolio (>= min_holdings_for_batch)
        batch_prefetch_enabled = self.batch_prefetch_config.enabled and is_portfolio_mode

        # Log mode detection (Requirements 17.48, 17.49, 17.50, 17.51)
        if is_portfolio_mode:
            if batch_prefetch_enabled:
                logger.info(f"✓ PORTFOLIO MODE DETECTED: {len(holdings)} holdings - batch pre-fetch ENABLED")
            else:
                logger.info(f"✓ PORTFOLIO MODE DETECTED: {len(holdings)} holdings - batch pre-fetch DISABLED (env var)")
        else:
            logger.info(f"✓ SINGLE-TICKER MODE DETECTED: {len(holdings)} holdings - using standard execution")
            logger.info("  Maintaining existing single-ticker behavior without batch pre-fetch")

        if batch_prefetch_enabled:
            logger.info("=" * 80)
            logger.info("BATCH PRE-FETCH MODE ENABLED")
            logger.info("=" * 80)

            # Extract all tickers from holdings
            tickers = [h.get("ticker") for h in holdings if h.get("ticker")]

            # Execute batch pre-fetch (Requirement 17.37, 17.38, 17.39)
            prefetched_data = self.execute_deep_analysis_with_prefetch(tickers)

            logger.info(f"Starting deep analysis for {len(holdings)} holdings with pre-fetched data")
        else:
            logger.info(f"Starting deep analysis for {len(holdings)} holdings (batch pre-fetch disabled)")

        # Initialize cache manager
        from finwiz.cache.analysis_cache_manager import get_analysis_cache_manager

        cache_ttl_hours = int(os.getenv("PORTFOLIO_CACHE_TTL_HOURS", "24"))
        cache_manager = get_analysis_cache_manager(ttl_hours=cache_ttl_hours)

        # Import unified deep analysis crew for direct instantiation
        from finwiz.crews.deep_analysis.deep_analysis import DeepAnalysisCrew

        # Process each holding
        deep_analysis_results = {}
        processed_count = 0

        # Track per-ticker execution times (Requirement 17.43, 17.44, 17.45)
        ticker_execution_times = {}
        crew_execution_start = time.time()

        for holding in holdings:
            ticker = holding.get("ticker")
            asset_class = holding.get("asset_class")

            if not ticker or not asset_class:
                logger.warning(f"Skipping holding with missing ticker or asset_class: {holding}")
                continue

            # Start timing for this ticker (Requirement 17.44)
            ticker_start_time = time.time()

            try:
                # Check cache first
                cached_result = cache_manager.get_cached_analysis(ticker, asset_class)
                if cached_result and cached_result.is_fresh(cache_ttl_hours):
                    # DATA LINEAGE: Cache retrieval
                    logger.info(f"DATA LINEAGE [{ticker}]: Retrieved from cache (age: {cached_result.age_hours:.1f}h)")
                    analysis_result = cached_result.analysis
                    logger.info(
                        f"DATA LINEAGE [{ticker}]: Cached data: Grade={analysis_result.grade}, "
                        f"Score={analysis_result.composite_score:.2f}"
                    )

                    # DATA LINEAGE: Create Flow state result from cache
                    logger.info(f"DATA LINEAGE [{ticker}]: Step 4 - Creating DeepAnalysisResult from cached data")
                    deep_result = self._create_deep_analysis_result_from_crew_output(
                        crew_result=analysis_result,
                        ticker=ticker,
                        asset_class=asset_class,
                        crew_name=analysis_result.crew_name,
                        cached=True,
                    )
                    deep_analysis_results[ticker] = deep_result
                    logger.info(
                        f"DATA LINEAGE [{ticker}]: Step 4 - Added cached result to results dict "
                        f"(Grade={deep_result.grade}, Score={deep_result.composite_score:.2f})"
                    )

                    # DATA LINEAGE: Generate JSON export and HTML report from cached data
                    logger.info(f"DATA LINEAGE [{ticker}]: Step 5 - Generating JSON export and HTML report from cached data")
                    try:
                        # Create export data from cached analysis_result
                        export_data = {
                            "ticker": ticker,
                            "asset_class": asset_class,
                            "composite_score": deep_result.composite_score,
                            "grade": deep_result.grade,
                            "recommendation": "HOLD",  # Default
                            "confidence": deep_result.confidence_level,
                            "rationale": f"Cached analysis for {ticker} with grade {deep_result.grade}",
                            "fundamental_score": deep_result.fundamental_score or 0.5,
                            "technical_score": deep_result.technical_score or 0.5,
                            "risk_score": deep_result.risk_score or 2.5,
                            "fundamental_details": {},
                            "technical_details": {},
                            "risk_details": {},
                            "analysis_date": deep_result.analysis_timestamp,
                            "session_id": self.state.session_id or "default",
                            "data_sources": ["Cached Analysis", "Python Scoring Engine"],
                        }

                        # Generate JSON export path
                        session_id = self.state.session_id or "default"
                        export_path = self._get_crew_export_path("deep_analysis_crew", ticker, session_id)

                        # Save JSON export
                        export_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(export_path, "w", encoding="utf-8") as f:
                            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)

                        # Generate HTML report using DeepAnalysisReportGenerator
                        html_path = self._generate_html_from_export("deep_analysis_crew", export_path)

                        # Store export and HTML paths in Flow state
                        if html_path:
                            self._store_crew_export_paths("deep_analysis_crew", [str(export_path)], [html_path])
                            logger.info(f"DATA LINEAGE [{ticker}]: Step 5 - Generated JSON export from cache: {export_path}")
                            logger.info(f"DATA LINEAGE [{ticker}]: Step 5 - Generated HTML report from cache: {html_path}")
                        else:
                            logger.warning(f"DATA LINEAGE [{ticker}]: Step 5 - HTML generation from cache failed")

                    except Exception as export_error:
                        logger.error(f"DATA LINEAGE [{ticker}]: Step 5 - Export/HTML generation from cache failed: {export_error}")
                        # Continue execution even if export fails

                else:
                    # Direct crew instantiation and execution (CrewAI Flow pattern)
                    # Use unified DeepAnalysisCrew for all asset classes
                    crew_inputs = {
                        "ticker": ticker,
                        "asset_class": asset_class,  # Required for dynamic tool routing
                        "current_day": self.state.current_day,
                        "current_month": self.state.current_month,
                        "current_year": self.state.current_year,
                        "current_date": self.state.current_date,
                        "full_date": self.state.full_date,
                        "timestamp": self.state.timestamp,
                        "report_language": self.state.report_language,
                    }

                    # Unified crew for all asset classes (simplified routing)
                    crew = DeepAnalysisCrew()
                    crew_name = "DeepAnalysisCrew"

                    # Inject pre-fetched data if batch mode is enabled (Requirement 17.41, 17.42)
                    if batch_prefetch_enabled and self.state.prefetched_data:
                        logger.info(f"DATA LINEAGE [{ticker}]: Injecting pre-fetched data into crew (BATCH MODE)")
                        crew.set_prefetched_data(self.state.prefetched_data)
                        logger.info(f"DATA LINEAGE [{ticker}]: Pre-fetched data injected - crew will use zero-latency data access")

                    # DATA LINEAGE: Crew execution with error handling
                    logger.info(f"DATA LINEAGE [{ticker}]: Step 1 - Running {crew_name} analysis for {asset_class}")
                    result, error = self._execute_crew_with_error_handling(crew_name, crew, crew_inputs, ticker)

                    if error:
                        # Crew execution failed - skip this holding
                        logger.warning(f"DATA LINEAGE [{ticker}]: Step 1 - Crew execution failed: {error}")
                        continue

                    logger.info(f"DATA LINEAGE [{ticker}]: Step 1 - Crew execution completed")

                    # DATA LINEAGE: Create Flow state result
                    logger.info(f"DATA LINEAGE [{ticker}]: Step 2 - Creating DeepAnalysisResult from crew output")
                    deep_result = self._create_deep_analysis_result_from_crew_output(
                        crew_result=result, ticker=ticker, asset_class=asset_class, crew_name=crew_name, cached=False
                    )
                    logger.info(
                        f"DATA LINEAGE [{ticker}]: Step 2 - Created: Grade={deep_result.grade}, "
                        f"Score={deep_result.composite_score:.2f}"
                    )

                    # DATA LINEAGE: Cache storage
                    logger.info(f"DATA LINEAGE [{ticker}]: Step 3 - Storing in cache")
                    cache_manager.cache_analysis(ticker, asset_class, deep_result)
                    logger.info(f"DATA LINEAGE [{ticker}]: Step 3 - Cached successfully")

                    # DATA LINEAGE: Add to results dict
                    deep_analysis_results[ticker] = deep_result
                    logger.info(
                        f"DATA LINEAGE [{ticker}]: Step 4 - Added to results dict "
                        f"(Grade={deep_result.grade}, Score={deep_result.composite_score:.2f})"
                    )

                    # DATA LINEAGE: Generate JSON export and HTML report
                    logger.info(f"DATA LINEAGE [{ticker}]: Step 5 - Generating JSON export and HTML report")
                    try:
                        # Extract crew export data from result if available
                        if hasattr(result, "pydantic") and result.pydantic:
                            export_data = (
                                result.pydantic.model_dump() if hasattr(result.pydantic, "model_dump") else result.pydantic
                            )
                        else:
                            # Create export data from deep_result
                            export_data = {
                                "ticker": ticker,
                                "asset_class": asset_class,
                                "composite_score": deep_result.composite_score,
                                "grade": deep_result.grade,
                                "recommendation": "HOLD",  # Default
                                "confidence": deep_result.confidence_level,
                                "rationale": f"Analysis completed for {ticker} with grade {deep_result.grade}",
                                "fundamental_score": deep_result.fundamental_score or 0.5,
                                "technical_score": deep_result.technical_score or 0.5,
                                "risk_score": deep_result.risk_score or 2.5,
                                "fundamental_details": {},
                                "technical_details": {},
                                "risk_details": {},
                                "analysis_date": deep_result.analysis_timestamp,
                                "session_id": self.state.session_id or "default",
                                "data_sources": ["Yahoo Finance API", "Python Scoring Engine"],
                            }

                        # Generate JSON export path
                        session_id = self.state.session_id or "default"
                        export_path = self._get_crew_export_path("deep_analysis_crew", ticker, session_id)

                        # Save JSON export
                        export_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(export_path, "w", encoding="utf-8") as f:
                            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)

                        # Generate HTML report using DeepAnalysisReportGenerator
                        html_path = self._generate_html_from_export("deep_analysis_crew", export_path)

                        # Store export and HTML paths in Flow state
                        if html_path:
                            self._store_crew_export_paths("deep_analysis_crew", [str(export_path)], [html_path])
                            logger.info(f"DATA LINEAGE [{ticker}]: Step 5 - Generated JSON export: {export_path}")
                            logger.info(f"DATA LINEAGE [{ticker}]: Step 5 - Generated HTML report: {html_path}")
                        else:
                            logger.warning(f"DATA LINEAGE [{ticker}]: Step 5 - HTML generation failed")

                    except Exception as export_error:
                        logger.error(f"DATA LINEAGE [{ticker}]: Step 5 - Export/HTML generation failed: {export_error}")
                        # Continue execution even if export fails

                processed_count += 1

                # Record execution time for this ticker (Requirement 17.44)
                ticker_duration = time.time() - ticker_start_time
                ticker_execution_times[ticker] = ticker_duration
                logger.info(
                    f"Deep analysis progress: {processed_count}/{len(holdings)} holdings (ticker {ticker} completed in {ticker_duration:.1f}s)"
                )

            except Exception as e:
                # Catch any unexpected errors not handled by _execute_crew_with_error_handling
                # (Requirement 17.52, 17.53, 17.54, 17.55)
                error_msg = f"Unexpected error in deep analysis for {ticker} ({asset_class}): {str(e)}"
                logger.error(error_msg, exc_info=True)

                # Track failed holding in state (Requirement 17.54)
                if ticker not in self.state.failed_holdings:
                    self.state.failed_holdings.append(ticker)

                # Collect error in state for consolidated summary (Requirement 17.54)
                if not hasattr(self.state, "errors"):
                    self.state.errors = []
                self.state.errors.append(error_msg)

                # Continue Flow execution with next holding (graceful degradation - Requirement 17.55)
                logger.info(f"Continuing with remaining holdings after {ticker} failure (graceful degradation)")
                continue

        # Log cache statistics
        cache_manager.log_cache_stats()

        # Calculate total execution time (Requirement 17.45)
        crew_execution_duration = time.time() - crew_execution_start

        # Calculate metrics and time savings (Requirement 17.61, 17.62, 17.63)
        if batch_prefetch_enabled and self.state.batch_prefetch_metrics:
            # Update metrics with crew execution data
            prefetch_duration = self.state.batch_prefetch_metrics.get("prefetch_duration_seconds", 0)
            total_time = prefetch_duration + crew_execution_duration

            # Estimate sequential time (assume 30s per ticker without batch mode)
            estimated_sequential_time = len(holdings) * 30.0
            time_savings = estimated_sequential_time - total_time
            time_savings_percentage = (time_savings / estimated_sequential_time * 100) if estimated_sequential_time > 0 else 0

            # Update batch prefetch metrics with crew execution data
            self.state.batch_prefetch_metrics.update(
                {
                    "crew_execution_duration_seconds": crew_execution_duration,
                    "total_duration_seconds": total_time,
                    "successful_executions": processed_count,
                    "failed_executions": len(holdings) - processed_count,
                    "ticker_execution_times": ticker_execution_times,
                    "avg_time_per_ticker_seconds": crew_execution_duration / processed_count if processed_count > 0 else 0,
                    "estimated_sequential_time_seconds": estimated_sequential_time,
                    "time_savings_seconds": time_savings,
                    "time_savings_percentage": time_savings_percentage,
                    "crew_execution_timestamp": datetime.now().isoformat(),
                }
            )

            # Log performance metrics (Requirement 17.61, 17.62, 17.63)
            logger.info("=" * 80)
            logger.info("BATCH EXECUTION METRICS")
            logger.info("=" * 80)
            logger.info(f"Pre-fetch duration: {prefetch_duration:.1f}s")
            logger.info(f"Crew execution duration: {crew_execution_duration:.1f}s")
            logger.info(f"Total duration: {total_time:.1f}s")
            logger.info(f"Successful executions: {processed_count}/{len(holdings)}")
            logger.info(f"Failed executions: {len(holdings) - processed_count}")
            logger.info(f"Avg time per ticker: {crew_execution_duration / processed_count if processed_count > 0 else 0:.1f}s")
            logger.info(f"Estimated sequential time: {estimated_sequential_time:.1f}s")
            logger.info(f"Time savings: {time_savings:.1f}s ({time_savings_percentage:.1f}%)")
            logger.info("=" * 80)
        else:
            logger.info(f"Deep analysis completed for {processed_count} holdings in {crew_execution_duration:.1f}s")

        logger.info(f"Deep analysis completed for {processed_count} holdings")

        # Update crew execution status in state
        if processed_count > 0:
            self.state.crew_execution_status["deep_analysis_crew"] = "completed"
        elif len(holdings) > 0:
            # All holdings failed
            self.state.crew_execution_status["deep_analysis_crew"] = "failed"
            logger.error("All deep analysis holdings failed")

        # Save metrics to JSON file (Requirement 17.62, 17.63, 17.64)
        if batch_prefetch_enabled and self.state.batch_prefetch_metrics:
            self._save_batch_metrics_to_file()

        return deep_analysis_results

    def _save_batch_metrics_to_file(self) -> None:
        """
        Save batch prefetch metrics to JSON file.

        Creates batch_prefetch_metrics.json in session output directory with:
        - Total tickers, successful, failed
        - Duration breakdown (prefetch vs execution)
        - Time savings percentage
        - Per-ticker execution times

        Requirements: 17.62, 17.63, 17.64
        """
        if not self.state.batch_prefetch_metrics:
            logger.warning("No batch prefetch metrics to save")
            return

        try:
            # Create output directory if it doesn't exist
            output_dir = Path(f"output/reports/{self.state.session_id}")
            output_dir.mkdir(parents=True, exist_ok=True)

            # Prepare metrics file path
            metrics_file = output_dir / "batch_prefetch_metrics.json"

            # Write metrics to file
            with open(metrics_file, "w", encoding="utf-8") as f:
                json.dump(self.state.batch_prefetch_metrics, f, indent=2, default=str)

            logger.info(f"✓ Batch prefetch metrics saved to: {metrics_file}")
            logger.info(f"  File size: {metrics_file.stat().st_size / 1024:.1f} KB")

        except Exception as e:
            logger.error(f"✗ Failed to save batch prefetch metrics: {e}")

    async def _run_deep_analysis_with_resilience(self, holdings: list[dict]) -> dict[str, Any]:
        """
        Run deep analysis with retry, timeout, and progress tracking (resilience-enhanced).

        This method processes holdings in parallel batches with resilience features:
        - Parallel batch processing with configurable concurrency limit
        - Retry logic with exponential backoff (via _analyze_single_holding_with_resilience)
        - Timeout management per holding
        - Progress tracking with real-time updates
        - Error classification and graceful degradation
        - Caching support for analysis results

        Args:
            holdings: List of holding dictionaries with ticker and asset_class

        Returns:
            dict: Deep analysis results keyed by ticker

        Requirements: 4.1-4.8, 6.1-6.7, 8.1-8.8

        """
        import asyncio

        if not holdings:
            logger.warning("No holdings provided for deep analysis")
            return {}

        # Initialize cache manager (same as in _run_deep_analysis_on_holdings)
        from finwiz.cache.analysis_cache_manager import get_analysis_cache_manager

        cache_ttl_hours = int(os.getenv("PORTFOLIO_CACHE_TTL_HOURS", "24"))
        cache_manager = get_analysis_cache_manager(ttl_hours=cache_ttl_hours)

        logger.info(
            f"Starting resilient deep analysis for {len(holdings)} holdings "
            f"(batch_size={self.resilience_config.deep_analysis_parallel_limit}, "
            f"max_retries={self.resilience_config.max_retries}, "
            f"holding_timeout={self.resilience_config.holding_timeout}s, "
            f"cache_ttl={cache_ttl_hours}h)"
        )

        results = {}
        batch_size = self.resilience_config.deep_analysis_parallel_limit

        # Process holdings in parallel batches
        for i in range(0, len(holdings), batch_size):
            batch = holdings[i : i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(holdings) + batch_size - 1) // batch_size

            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} holdings)")

            # Create async tasks for batch with resilience
            batch_tasks = [self._analyze_single_holding_with_resilience(holding) for holding in batch]

            # Execute batch in parallel with exception handling
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            # Collect results and update progress
            for holding, result in zip(batch, batch_results):
                ticker = holding.get("ticker", "UNKNOWN")

                if isinstance(result, Exception):
                    # Exception occurred during analysis
                    logger.error(f"Failed to analyze {ticker}: {result}")
                    self.state.failed_holdings.append(ticker)
                elif result is not None:
                    # Successful analysis
                    results[ticker] = result
                else:
                    # None returned (analysis failed after retries)
                    logger.warning(f"Analysis returned None for {ticker}")
                    self.state.failed_holdings.append(ticker)

                # Update progress tracking
                self.state.holdings_processed += 1
                self.state.holdings_remaining -= 1
                self.state.progress_percentage = (
                    self.state.holdings_processed / self.state.total_holdings * 100 if self.state.total_holdings > 0 else 0.0
                )

                # Log progress
                success_count = len(results)
                failed_count = len(self.state.failed_holdings)
                logger.info(
                    f"Progress: {self.state.holdings_processed}/{self.state.total_holdings} "
                    f"({self.state.progress_percentage:.1f}%) - "
                    f"Success: {success_count}, Failed: {failed_count}"
                )

            # Log batch completion
            logger.info(
                f"Batch {batch_num}/{total_batches} completed: "
                f"{len([r for r in batch_results if not isinstance(r, Exception) and r is not None])}/"
                f"{len(batch)} successful"
            )

        # Log final statistics
        logger.info(
            f"Resilient deep analysis completed: "
            f"{len(results)}/{len(holdings)} successful "
            f"({len(results) / len(holdings) * 100:.1f}% success rate), "
            f"{len(self.state.failed_holdings)} failed, "
            f"{len(self.state.timeout_holdings)} timeouts"
        )

        return results

    async def _analyze_single_holding_with_resilience(self, holding: dict) -> Any | None:
        """
        Analyze single holding with retry and timeout management.

        This method wraps the deep analysis crew execution with resilience features:
        - Retry logic with exponential backoff (via self.retry_decorator)
        - Timeout management per holding (via with_timeout_graceful)
        - Error classification and tracking (retryable vs non-retryable)
        - Adaptive reasoning attempts based on retry count

        Args:
            holding: Holding dictionary with ticker and asset_class

        Returns:
            DeepAnalysisResult on success, None on failure

        Requirements: 1.1-1.7, 4.1-4.8, 5.1-5.7

        """
        from finwiz.flow_state import DeepAnalysisResult
        from finwiz.utils.retry_handler import create_validation_error_from_exception
        from finwiz.utils.timeout_handler import with_timeout_graceful

        # Extract ticker and asset_class from holding dict
        ticker = holding.get("ticker")
        asset_class = holding.get("asset_class")

        if not ticker or not asset_class:
            logger.error(f"Invalid holding data: missing ticker or asset_class: {holding}")
            return None

        # Initialize retry count in state
        if ticker not in self.state.retry_counts:
            self.state.retry_counts[ticker] = 0

        # Create inner async function with retry decorator
        @self.retry_decorator
        async def analyze_with_retry(attempt: int = 1) -> DeepAnalysisResult | None:
            """Inner function with retry logic applied."""
            # Update retry count in state
            self.state.retry_counts[ticker] = attempt
            self.state.current_ticker = ticker

            # Log retry attempt
            if attempt > 1:
                logger.warning(f"Retry attempt {attempt}/{self.resilience_config.max_retries} for {ticker} ({asset_class})")

            # Adjust max_reasoning_attempts based on retry attempt
            # Reduce reasoning attempts on retries to speed up recovery
            max_reasoning_attempts = max(1, 4 - attempt)

            logger.debug(f"Analyzing {ticker} with max_reasoning_attempts={max_reasoning_attempts} (attempt {attempt})")

            # Call with_timeout_graceful with _execute_deep_analysis_crew
            result = await with_timeout_graceful(
                self._execute_deep_analysis_crew,
                timeout_seconds=self.resilience_config.holding_timeout,
                operation_name=f"Deep analysis for {ticker}",
                fallback_value=None,
                ticker=ticker,
                asset_class=asset_class,
                max_reasoning_attempts=max_reasoning_attempts,
            )

            # Check for timeout (result is None)
            if result is None:
                logger.warning(f"Timeout: Deep analysis for {ticker} exceeded {self.resilience_config.holding_timeout}s timeout")
                # Track timeout in state
                if ticker not in self.state.timeout_holdings:
                    self.state.timeout_holdings.append(ticker)
                # Raise TimeoutError to trigger retry
                raise TimeoutError(f"Deep analysis for {ticker} exceeded {self.resilience_config.holding_timeout}s timeout")

            return result

        # Wrap in try/except to catch all retry exhaustion
        try:
            result = await analyze_with_retry()
            return result

        except Exception as e:
            # All retries exhausted or non-retryable error
            logger.error(f"All retries exhausted for {ticker} after {self.state.retry_counts.get(ticker, 0)} attempts: {e}")

            # Create ValidationError using create_validation_error_from_exception
            validation_error = create_validation_error_from_exception(
                error=e, ticker=ticker, attempt=self.state.retry_counts.get(ticker, 0)
            )

            # Classify and store error in retryable_errors or non_retryable_errors
            if validation_error.context.get("is_retryable"):
                self.state.retryable_errors.append(validation_error)
                logger.info(
                    f"Retryable error for {ticker}: {validation_error.error_type} - {validation_error.context.get('remediation')}"
                )
            else:
                self.state.non_retryable_errors.append(validation_error)
                logger.warning(
                    f"Non-retryable error for {ticker}: {validation_error.error_type} - "
                    f"{validation_error.context.get('remediation')}"
                )

            # Return None to indicate failure
            return None

    def _create_deep_analysis_result_from_crew_output(
        self, crew_result: Any, ticker: str, asset_class: str, crew_name: str, cached: bool = False
    ) -> "DeepAnalysisResult":
        """
        Create DeepAnalysisResult from crew output with proper field population.

        This helper method extracts data from crew output and creates a properly
        populated DeepAnalysisResult instance with all required fields including
        data_freshness_hours, confidence_level, and warnings.

        Args:
            crew_result: Raw crew execution result
            ticker: Stock/ETF/crypto ticker symbol
            asset_class: Asset class (stock, etf, crypto)
            crew_name: Name of the crew that performed analysis
            cached: Whether this result came from cache

        Returns:
            DeepAnalysisResult with all fields properly populated

        """
        from finwiz.flow_state import DeepAnalysisResult

        # Extract scores and grade from crew result
        # Crew results can be in various formats, so we need to handle them carefully
        composite_score = 0.7  # Default fallback
        grade = "C"  # Default fallback
        fundamental_score = None
        technical_score = None
        risk_score = None
        warnings = []

        # Try to extract data from crew result
        if hasattr(crew_result, "pydantic"):
            # Pydantic output available
            pydantic_data = crew_result.pydantic
            if pydantic_data:
                composite_score = getattr(pydantic_data, "composite_score", composite_score)
                grade = getattr(pydantic_data, "grade", grade)
                fundamental_score = getattr(pydantic_data, "fundamental_score", None)
                technical_score = getattr(pydantic_data, "technical_score", None)
                risk_score = getattr(pydantic_data, "risk_score", None)
        elif hasattr(crew_result, "raw"):
            # Try to parse from raw output
            raw_output = str(crew_result.raw)
            # Simple parsing - look for grade and score patterns
            if "Grade:" in raw_output or "grade:" in raw_output:
                # Extract grade from text
                import re

                grade_match = re.search(r"[Gg]rade:\s*([A-F][+\-]?)", raw_output)
                if grade_match:
                    grade = grade_match.group(1)

            if "Score:" in raw_output or "score:" in raw_output:
                # Extract score from text
                import re

                score_match = re.search(r"[Ss]core:\s*(0?\.\d+|\d+\.\d+)", raw_output)
                if score_match:
                    try:
                        composite_score = float(score_match.group(1))
                    except ValueError:
                        pass

        # Calculate data freshness (hours since analysis)
        # For now, assume data is fresh (0 hours old) since we just fetched it
        # In a real implementation, this would check timestamps from the actual data sources
        data_freshness_hours = 0.0 if not cached else 1.0  # Cached data is at least 1 hour old

        # Calculate confidence level based on available data
        confidence_level = 0.8  # Default confidence
        if fundamental_score is not None and technical_score is not None and risk_score is not None:
            # High confidence if we have all scores
            confidence_level = 0.9
        elif fundamental_score is None and technical_score is None:
            # Lower confidence if missing multiple scores
            confidence_level = 0.6
            warnings.append("Missing fundamental and technical scores - confidence reduced")

        # Add warning if data is cached
        if cached:
            warnings.append(f"Using cached analysis data (age: {data_freshness_hours:.1f} hours)")

        # Add warning if using fallback values
        if composite_score == 0.7 and grade == "C":
            warnings.append("Using fallback composite score and grade - crew output may be incomplete")

        # Create DeepAnalysisResult with all required fields
        return DeepAnalysisResult(
            ticker=ticker,
            asset_class=asset_class,
            crew_name=crew_name,
            analysis_timestamp=datetime.now().isoformat(),
            composite_score=composite_score,
            grade=grade,
            recommendation="HOLD",  # Default recommendation
            rationale="Analysis completed via crew execution",
            risk_details={},  # Default empty risk details
            fundamental_score=fundamental_score,
            technical_score=technical_score,
            risk_score=risk_score,
            data_freshness_hours=data_freshness_hours,
            confidence_level=confidence_level,
            warnings=warnings,
            cached=cached,
        )

    async def _execute_deep_analysis_crew(self, ticker: str, asset_class: str, max_reasoning_attempts: int) -> Any:
        """
        Execute DeepAnalysisCrew for a single ticker with caching support.

        This method instantiates and executes the unified DeepAnalysisCrew with
        dynamic tool routing based on asset_class. It checks cache first, then
        executes the crew if needed, and caches the result.

        Args:
            ticker: Stock/ETF/crypto ticker symbol
            asset_class: Asset class (stock, etf, crypto)
            max_reasoning_attempts: Maximum reasoning attempts for agents

        Returns:
            DeepAnalysisResult with parsed scores and grade

        Raises:
            Exception: If crew execution fails

        Requirements: 4.1-4.8

        """
        from finwiz.cache.analysis_cache_manager import get_analysis_cache_manager
        from finwiz.crews.deep_analysis.deep_analysis import DeepAnalysisCrew

        # Initialize cache manager
        cache_ttl_hours = int(os.getenv("PORTFOLIO_CACHE_TTL_HOURS", "24"))
        cache_manager = get_analysis_cache_manager(ttl_hours=cache_ttl_hours)

        # Check cache first
        cached_result = cache_manager.get_cached_analysis(ticker, asset_class)
        if cached_result and cached_result.is_fresh(cache_ttl_hours):
            logger.info(f"Using cached analysis for {ticker} (age: {cached_result.age_hours:.1f}h)")
            analysis_result = cached_result.analysis

            # Use helper method to create DeepAnalysisResult with proper field population
            return self._create_deep_analysis_result_from_crew_output(
                crew_result=analysis_result,
                ticker=ticker,
                asset_class=asset_class,
                crew_name=analysis_result.crew_name,
                cached=True,
            )

        logger.info(f"Executing DeepAnalysisCrew for {ticker} ({asset_class}) with max_reasoning_attempts={max_reasoning_attempts}")

        try:
            # Instantiate crew (direct instantiation per CrewAI Flow pattern)
            crew = DeepAnalysisCrew()

            # Prepare inputs dict with ticker, asset_class, and session metadata
            crew_inputs = {
                "ticker": ticker,
                "asset_class": asset_class,  # Required for dynamic tool routing
                "max_reasoning_attempts": max_reasoning_attempts,
                # SEC filing form type (used in task descriptions)
                "form_type": "10-K",  # Default to 10-K for stocks, tasks will adapt based on asset_class
                # Session metadata from Flow state
                "session_id": self.state.session_id,
                "current_day": self.state.current_day,
                "current_month": self.state.current_month,
                "current_year": self.state.current_year,
                "current_date": self.state.current_date,
                "full_date": self.state.full_date,
                "timestamp": self.state.timestamp,
                "report_language": self.state.report_language,
            }

            logger.debug(f"Crew inputs prepared for {ticker}: {list(crew_inputs.keys())}")

            # Execute crew using crew().kickoff() pattern
            result = crew.crew().kickoff(inputs=crew_inputs)

            logger.info(f"DeepAnalysisCrew execution completed for {ticker}")

            # Use helper method to create DeepAnalysisResult with proper field population
            deep_result = self._create_deep_analysis_result_from_crew_output(
                crew_result=result, ticker=ticker, asset_class=asset_class, crew_name="DeepAnalysisCrew", cached=False
            )

            # Cache the result
            cache_manager.cache_analysis(ticker, asset_class, deep_result)

            logger.info(
                f"Deep analysis result for {ticker}: grade={deep_result.grade}, composite_score={deep_result.composite_score:.3f}"
            )

            return deep_result

        except Exception as e:
            logger.error(f"DeepAnalysisCrew execution failed for {ticker}: {e}", exc_info=True)
            raise

    def _update_progress(self) -> None:
        """
        Update progress tracking metrics in Flow state.

        This helper method calculates and updates progress-related fields:
        - progress_percentage: Percentage of holdings processed
        - estimated_time_remaining: Estimated seconds until completion
        - last_checkpoint_time: Timestamp of this progress update

        The method uses the current state values (holdings_processed, total_holdings,
        flow_start_time) to calculate progress metrics and logs a formatted progress
        message.

        Requirements: 6.1-6.7

        """
        # Calculate progress percentage
        if self.state.total_holdings > 0:
            self.state.progress_percentage = self.state.holdings_processed / self.state.total_holdings * 100
        else:
            self.state.progress_percentage = 0.0

        # Calculate estimated time remaining based on average time per holding
        if self.state.holdings_processed > 0 and self.state.holdings_remaining > 0:
            # Calculate elapsed time
            flow_start = datetime.fromisoformat(self.state.flow_start_time)
            elapsed_time = (datetime.now() - flow_start).total_seconds()

            # Calculate average time per holding
            avg_time_per_holding = elapsed_time / self.state.holdings_processed

            # Estimate remaining time
            self.state.estimated_time_remaining = avg_time_per_holding * self.state.holdings_remaining
        else:
            self.state.estimated_time_remaining = 0.0

        # Update last checkpoint time
        self.state.last_checkpoint_time = datetime.now().isoformat()

        # Log progress with formatted message
        flow_start = datetime.fromisoformat(self.state.flow_start_time)
        elapsed_time = (datetime.now() - flow_start).total_seconds()
        elapsed_minutes = int(elapsed_time // 60)
        elapsed_seconds = int(elapsed_time % 60)

        remaining_minutes = int(self.state.estimated_time_remaining // 60)
        remaining_seconds = int(self.state.estimated_time_remaining % 60)

        logger.info(
            f"Progress Update: {self.state.holdings_processed}/{self.state.total_holdings} "
            f"({self.state.progress_percentage:.1f}%) | "
            f"Elapsed: {elapsed_minutes}m {elapsed_seconds}s | "
            f"Remaining: ~{remaining_minutes}m {remaining_seconds}s | "
            f"Success: {self.state.holdings_processed - len(self.state.failed_holdings)}, "
            f"Failed: {len(self.state.failed_holdings)}, "
            f"Timeouts: {len(self.state.timeout_holdings)}"
        )

    def _match_alternatives_for_holdings(self, deep_results: dict[str, Any]) -> dict[str, Any]:
        """
        Match A+ alternatives for underperforming holdings.

        Helper method for analyze_and_update_portfolio() that finds alternatives
        for holdings with grades C, D, or F.

        Args:
            deep_results: Deep analysis results from _run_deep_analysis_on_holdings()

        Returns:
            dict: Alternatives data keyed by ticker

        """
        # Check if alternative matching is enabled
        enabled = (os.getenv("PORTFOLIO_ENABLE_ALTERNATIVES") or "true").strip().lower() in {"1", "true", "yes", "on"}
        if not enabled:
            logger.info("Alternative matching disabled via PORTFOLIO_ENABLE_ALTERNATIVES")
            return {}

        if not deep_results:
            logger.warning("No deep analysis results available for alternative matching")
            return {}

        # Use existing AlternativeFinder tool
        from finwiz.tools.alternative_finder_tool import AlternativeFinder, HoldingProfile

        alternative_finder = AlternativeFinder()
        max_alternatives = int(os.getenv("PORTFOLIO_MAX_ALTERNATIVES", "5"))

        # Process holdings with grade C or below
        alternatives_data = {}
        alternatives_count = 0

        for ticker, analysis in deep_results.items():
            # Extract grade from DeepAnalysisResult
            if hasattr(analysis, "grade"):
                grade = analysis.grade
            else:
                grade = analysis.get("grade", "D")

            # Only find alternatives for grades C, D, or F
            if grade in ["C", "D", "F"]:
                try:
                    # Create HoldingProfile for AlternativeFinder
                    # Extract values with proper None handling
                    risk_score = getattr(analysis, "risk_score", None)
                    if risk_score is None:
                        risk_score = 2.5  # Default risk score

                    composite_score = getattr(analysis, "composite_score", None)
                    if composite_score is None:
                        composite_score = 0.6  # Default composite score

                    holding_profile = HoldingProfile(
                        ticker=ticker,
                        name=getattr(analysis, "name", ticker),
                        asset_class=getattr(analysis, "asset_class", "stock"),
                        grade=grade,
                        composite_score=composite_score,
                        risk_score=risk_score,
                    )

                    # Find alternatives using existing tool
                    alternatives = alternative_finder.find_alternatives(holding=holding_profile, max_alternatives=max_alternatives)

                    if alternatives:
                        # Convert Alternative objects to dictionaries for storage
                        alternatives_data[ticker] = [alt.model_dump(mode="json") for alt in alternatives]
                        alternatives_count += len(alternatives)
                        logger.info(f"Found {len(alternatives)} alternatives for {ticker} (grade: {grade})")
                    else:
                        logger.info(f"No alternatives found for {ticker} (grade: {grade})")

                except Exception as e:
                    logger.error(f"Alternative matching failed for {ticker}: {e}")
                    continue
            else:
                logger.debug(f"Skipping alternative matching for {ticker} (grade: {grade} - B or above)")

        logger.info(f"Alternative matching completed: {alternatives_count} alternatives for {len(alternatives_data)} holdings")

        return alternatives_data

    async def _update_portfolio_review_with_enriched_data(self) -> bool:
        """
        Update portfolio review with deep analysis results using validated merger.

        Helper method for analyze_and_update_portfolio() that properly merges
        deep analysis data into portfolio holdings with strict validation.

        CRITICAL FIX: This method now uses DeepAnalysisDataMerger to properly
        merge crew analysis data into holdings, replacing the broken merge logic
        that was causing fallback Grade D values to persist.

        Returns:
            bool: True if portfolio review was successfully updated, False otherwise

        Raises:
            DataMergeError: If merge fails or data is missing (fail-fast)

        """
        from finwiz.schemas.portfolio_review import HoldingDecision
        from finwiz.utils.deep_analysis_merger import DataMergeError, DeepAnalysisDataMerger

        try:
            logger.info("Updating portfolio review with deep analysis results using validated merger")

            # DATA LINEAGE: Log what data is available for merge
            logger.info("=" * 80)
            logger.info("DATA LINEAGE: Step 5 - Portfolio Review Merge with Validation")
            logger.info("=" * 80)
            logger.info(f"Deep analysis results available: {len(self.state.deep_analysis_results)}")
            logger.info(f"Alternatives available: {len(self.state.portfolio_alternatives or {})}")
            logger.info("Flow state contains:")
            logger.info(f"  - deep_analysis_success: {self.state.deep_analysis_success}")
            logger.info(f"  - deep_analysis_count: {self.state.deep_analysis_count}")
            logger.info(f"  - alternatives_count: {self.state.alternatives_count}")

            for ticker in self.state.deep_analysis_results.keys():
                analysis = self.state.deep_analysis_results[ticker]
                logger.info(f"  - {ticker}: Grade={analysis.grade}, Score={analysis.composite_score:.2f}, Cached={analysis.cached}")
            logger.info("=" * 80)

            # Step 1: Load portfolio review and extract holdings
            if not self.state.portfolio_review:
                logger.error("No portfolio review data available in Flow state")
                raise DataMergeError("Cannot merge: portfolio review is missing")

            portfolio_data = self.state.portfolio_review

            # Extract holdings list
            if "portfolio_review" in portfolio_data:
                holdings_data = portfolio_data["portfolio_review"].get("holdings", [])
            else:
                holdings_data = portfolio_data.get("holdings", [])

            if not holdings_data:
                logger.error("No holdings found in portfolio review")
                raise DataMergeError("Cannot merge: no holdings in portfolio review")

            logger.info(f"Loaded {len(holdings_data)} holdings from portfolio review")

            # Convert holdings dicts to HoldingDecision Pydantic models
            holdings = []
            for holding_dict in holdings_data:
                try:
                    holding = HoldingDecision.model_validate(holding_dict)
                    holdings.append(holding)
                except Exception as e:
                    ticker = holding_dict.get("ticker", "UNKNOWN")
                    logger.error(f"Failed to validate holding {ticker}: {e}")
                    # Continue with other holdings
                    continue

            logger.info(f"Validated {len(holdings)} holdings as Pydantic models")

            # Step 2: Instantiate DeepAnalysisDataMerger
            merger = DeepAnalysisDataMerger()
            logger.info("DeepAnalysisDataMerger instantiated")

            # Step 3: Merge deep analysis into holdings with validation (including alternatives)
            logger.info("Calling merger.merge_deep_analysis_into_holdings() with validation")

            # Get alternatives data from Flow state
            alternatives_data = self.state.portfolio_alternatives if self.state.portfolio_alternatives else None
            if alternatives_data:
                logger.info(f"Including alternatives data for {len(alternatives_data)} holdings in merge")
            else:
                logger.info("No alternatives data available for merge")

            try:
                merged_holdings = merger.merge_deep_analysis_into_holdings(
                    holdings,
                    self.state.deep_analysis_results,
                    alternatives_data=alternatives_data,
                )

                logger.info(f"✅ Successfully merged {len(merged_holdings)} holdings with deep analysis data")

            except DataMergeError as merge_error:
                # FAIL-FAST: Stop immediately if merge fails
                logger.error(f"❌ Data merge failed: {merge_error}")
                logger.error("REFUSING to continue with fallback data - failing fast")
                raise  # Re-raise to trigger fail-fast behavior

            # Step 4: Update portfolio with merged holdings
            logger.info("Updating portfolio review with merged holdings")

            # Convert merged holdings back to dicts for JSON serialization
            merged_holdings_dicts = [holding.model_dump(mode="json") for holding in merged_holdings]

            # Update the portfolio data structure
            if "portfolio_review" in portfolio_data:
                portfolio_data["portfolio_review"]["holdings"] = merged_holdings_dicts
                # Set has_deep_analysis flag
                portfolio_data["portfolio_review"]["has_deep_analysis"] = True
            else:
                portfolio_data["holdings"] = merged_holdings_dicts
                portfolio_data["has_deep_analysis"] = True

            # Update Flow state with merged portfolio
            self.state.portfolio_review = portfolio_data

            logger.info("Portfolio review updated in Flow state with merged holdings")

            # Step 5: Save updated portfolio review to file
            try:
                # Determine output path
                if hasattr(self.state, "portfolio_review_json") and self.state.portfolio_review_json:
                    out_path = Path(self.state.portfolio_review_json)
                else:
                    # Default path
                    output_dir = Path("output/portfolio")
                    output_dir.mkdir(parents=True, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    out_path = output_dir / f"portfolio_review_{timestamp}.json"

                logger.info(f"Saving merged portfolio review to: {out_path}")

                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(portfolio_data, f, indent=2, ensure_ascii=False)

                self.state.portfolio_review_json = str(out_path)

                logger.info(f"✅ Portfolio review saved successfully: {out_path}")

            except Exception as save_error:
                logger.error(f"Failed to save portfolio review: {save_error}")
                # Continue - state is updated even if file save fails
                logger.warning("Portfolio state updated but file save failed")

            # Step 6: Verify merge succeeded
            logger.info("=" * 80)
            logger.info("DATA LINEAGE: Step 6 - Merge Verification")
            logger.info("=" * 80)

            # Check merged holdings
            if "portfolio_review" in portfolio_data:
                verified_holdings = portfolio_data["portfolio_review"].get("holdings", [])
            else:
                verified_holdings = portfolio_data.get("holdings", [])

            logger.info(f"Merged portfolio contains {len(verified_holdings)} holdings")

            # Verify each holding has actual analysis data (not fallback)
            fallback_count = 0
            success_count = 0

            for holding in verified_holdings:
                ticker = holding.get("ticker", "UNKNOWN")
                grade = holding.get("grade", "N/A")
                score = holding.get("composite_score", 0.0)
                crew_used = holding.get("crew_analysis_used", "None")

                # Check for fallback pattern
                is_fallback = grade == "D" and score == 0.6

                if is_fallback:
                    fallback_count += 1
                    logger.error(f"  ❌ {ticker}: STILL FALLBACK - Grade={grade}, Score={score:.2f}, Crew={crew_used}")
                else:
                    success_count += 1
                    logger.info(f"  ✅ {ticker}: Grade={grade}, Score={score:.2f}, Crew={crew_used}")

            logger.info("-" * 80)
            logger.info(f"Merge verification: {success_count} success, {fallback_count} fallback")

            if fallback_count > 0:
                logger.error(f"❌ MERGE VERIFICATION FAILED: {fallback_count} holdings still have fallback data")
                raise DataMergeError(f"Merge verification failed: {fallback_count} holdings have fallback data")

            logger.info("✅ MERGE VERIFICATION PASSED: All holdings have actual analysis data")
            logger.info("=" * 80)

            return True

        except DataMergeError as merge_error:
            # FAIL-FAST: Re-raise DataMergeError to stop execution
            logger.error(f"❌ Data merge error (fail-fast): {merge_error}")
            raise

        except Exception as e:
            logger.error(f"Failed to update portfolio review with deep analysis: {e}", exc_info=True)
            logger.error("REFUSING to continue with potentially corrupted data - failing fast")
            raise DataMergeError(f"Portfolio update failed: {e}") from e

    @listen("check_portfolio")
    async def analyze_and_update_portfolio(self) -> dict[str, Any]:
        """
        Perform deep analysis and update portfolio review (async).

        Phase 3: Deep Analysis & Update (Atomic Operation)
        This consolidates two operations into one atomic operation:
        1. Deep crew analysis on each holding (using unified DeepAnalysisCrew)
        2. Portfolio review regeneration with enriched data (ONCE, not twice)

        Note: Alternative matching moved to Phase 4.5 (after discovery crews run)

        Triggers: check_crypto, check_stock, check_etf (Phase 4 - parallel discovery)

        Performance: Uses async/await for parallel processing, enabling:
        - Portfolio regeneration with parallel holdings processing
        - Potential future parallelization of deep analysis crews

        Flow Rationale: After analyzing what we own, we grade each holding and identify
        which ones need alternatives. This happens BEFORE discovery so we know what to
        look for. The atomic operation ensures portfolio is updated once with complete data.

        CrewAI Flow Integration:
        - Triggered after portfolio review completes
        - Checks DEEP_PORTFOLIO_ANALYSIS environment variable
        - Uses direct crew instantiation and crew.kickoff()
        - Updates structured Flow state (self.state)
        - Returns consolidated results for downstream listeners

        Resilience Features (NEW):
        - Progress tracking with total/processed/remaining counts
        - Retry logic with exponential backoff
        - Timeout management per holding
        - Error classification and tracking
        - Graceful degradation on failures

        Resume Capability (NEW):
        - Checks if deep analysis already completed when resuming
        - Skips deep analysis if self.state.deep_analysis_success is True and resuming
        - Logs which holdings are being skipped vs remaining

        Requirements: 3.4-3.6

        Returns:
            dict: Consolidated results passed to downstream @listen() methods

        """
        # Check if deep analysis is enabled
        enabled = (os.getenv("DEEP_PORTFOLIO_ANALYSIS") or "false").strip().lower() in {"1", "true", "yes", "on"}
        if not enabled:
            logger.info("Deep portfolio analysis disabled via DEEP_PORTFOLIO_ANALYSIS")
            return {}  # Return empty dict for downstream listeners

        # Check if resuming from checkpoint and deep analysis already completed
        if self.state.resume_from_checkpoint and self.state.deep_analysis_success:
            logger.info(
                f"Resume: Deep analysis already completed "
                f"({self.state.deep_analysis_count}/{self.state.total_holdings} holdings analyzed), "
                f"skipping deep analysis"
            )

            # Log which holdings were already analyzed
            if self.state.deep_analysis_results:
                analyzed_tickers = list(self.state.deep_analysis_results.keys())
                logger.info(f"Resume: Skipping already analyzed holdings: {', '.join(analyzed_tickers)}")

            # Return existing results for downstream listeners
            return {
                "deep_analysis_complete": True,
                "analysis_results": {
                    ticker: result.model_dump(mode="json") for ticker, result in self.state.deep_analysis_results.items()
                },
                "alternatives_data": self.state.portfolio_alternatives or {},
                "portfolio_updated": True,  # Already updated in previous run
                "holdings_analyzed": self.state.deep_analysis_count,
                "alternatives_found": self.state.alternatives_count,
                "resumed": True,
                "status": "skipped",
            }

        try:
            # Load holdings from portfolio review
            if not hasattr(self.state, "portfolio_review") or not self.state.portfolio_review:
                logger.warning("No portfolio review data available in Flow state")
                return {}

            # Extract holdings list
            portfolio_data = self.state.portfolio_review
            if "portfolio_review" in portfolio_data:
                holdings = portfolio_data["portfolio_review"].get("holdings", [])
            else:
                holdings = portfolio_data.get("holdings", [])

            if not holdings:
                logger.warning("No holdings found in portfolio review data")
                return {}

            # Initialize progress tracking
            self.state.total_holdings = len(holdings)
            self.state.holdings_processed = 0
            self.state.holdings_remaining = len(holdings)
            self.state.progress_percentage = 0.0
            self.state.failed_holdings = []
            self.state.retry_counts = {}
            self.state.timeout_holdings = []

            logger.info(
                f"Starting deep analysis with resilience for {self.state.total_holdings} holdings "
                f"(max_retries={self.resilience_config.max_retries}, "
                f"holding_timeout={self.resilience_config.holding_timeout}s)"
            )

            # Step 1: Run deep analysis on holdings with resilience
            logger.info("Step 1/3: Running deep analysis on holdings with retry and timeout")

            # DIAGNOSTIC LOGGING: Log portfolio holdings BEFORE deep analysis
            logger.info("=" * 80)
            logger.info("DIAGNOSTIC: Portfolio Holdings BEFORE Deep Analysis Merge")
            logger.info("=" * 80)
            logger.info(f"Total holdings to analyze: {len(holdings)}")
            for idx, holding in enumerate(holdings, 1):
                ticker = holding.get("ticker", "UNKNOWN")
                grade = holding.get("grade", "N/A")
                score = holding.get("composite_score", 0.0)
                rationale = holding.get("rationale_bullets", [])
                has_deep = holding.get("has_deep_analysis", False)

                # Check for fallback data pattern
                is_fallback = grade == "D" and score == 0.6 and any("Validation rapide" in str(bullet) for bullet in rationale)

                fallback_indicator = " [FALLBACK DATA DETECTED]" if is_fallback else ""
                logger.info(f"  {idx}. {ticker}: Grade={grade}, Score={score:.2f}, HasDeepAnalysis={has_deep}{fallback_indicator}")

                if is_fallback:
                    logger.warning(f"  ⚠️  {ticker} has fallback pattern: Grade D + Score 0.6 + 'Validation rapide'")
            logger.info("=" * 80)

            deep_analysis_results = {}
            try:
                # 🚀 CRITICAL FIX: Use Pure Python Analysis Instead of AI Crews
                # This implements Requirements 0.1-0.7: Replace AI with Python for 10-20x speedup
                logger.info("🚀 CRITICAL FIX: Using Pure Python Deep Analysis (NO AI crews)")
                logger.info("  ✅ 10-20x faster execution")
                logger.info("  ✅ 100% cost reduction (0 LLM calls)")
                logger.info("  ✅ Deterministic results")

                # Convert holdings to HoldingDecision objects for Python analyzer
                from finwiz.schemas.portfolio_review import HoldingDecision

                holding_decisions = []

                # DEBUG: Log holdings conversion
                logger.info(f"DEBUG: Starting holdings conversion for {len(holdings)} holdings")

                for idx, holding in enumerate(holdings):
                    try:
                        # DEBUG: Log each holding being processed
                        ticker = holding.get("ticker", "UNKNOWN")
                        logger.info(f"DEBUG: Converting holding {idx + 1}/{len(holdings)}: {ticker}")

                        # Create HoldingDecision from holding dict with all required fields
                        grade = holding.get("grade", "C")

                        holding_decision = HoldingDecision(
                            ticker=holding.get("ticker", ""),
                            name=holding.get("name", ""),
                            asset_class=holding.get("asset_class", "stock"),
                            currency=holding.get("currency", "USD"),  # Required field
                            decision=holding.get("decision", "KEEP"),  # Must be KEEP or SELL
                            composite_score=holding.get("composite_score", 0.5),
                            grade=grade,
                            grade_description=holding.get("grade_description", f"Grade {grade} holding"),  # Required field
                            recommended_action=holding.get("recommended_action", "KEEP"),  # Must be KEEP or SELL
                            rationale_bullets=holding.get("rationale_bullets", []),
                            risk=holding.get("risk", {"score": 3.0, "level": "Medium"}),  # Provide default risk
                            alternatives=holding.get("alternatives", []),
                        )
                        holding_decisions.append(holding_decision)
                        logger.info(f"DEBUG: Successfully converted {ticker}")
                    except Exception as e:
                        logger.error(
                            f"DEBUG: Failed to convert holding {holding.get('ticker', 'UNKNOWN')} to HoldingDecision: {e}",
                            exc_info=True,
                        )
                        continue

                # DEBUG: Log final conversion results
                logger.info(
                    f"DEBUG: Holdings conversion completed: {len(holding_decisions)} successful out of {len(holdings)} total"
                )

                # Use Pure Python Portfolio Deep Analyzer (Requirements 0.1, 0.2, 0.3)
                from finwiz.scoring.portfolio_deep_analyzer import analyze_portfolio_with_python

                session_id = self.state.session_id or "default"

                # DEBUG: Log input data
                logger.info(f"DEBUG: Calling analyze_portfolio_with_python with {len(holding_decisions)} holdings")
                logger.info(f"DEBUG: Session ID: {session_id}")
                logger.info(f"DEBUG: Sample holding tickers: {[h.ticker for h in holding_decisions[:5]]}")

                try:
                    python_results = analyze_portfolio_with_python(holding_decisions, session_id)

                    # DEBUG: Log results
                    logger.info(f"DEBUG: Python analyzer returned: {type(python_results)}")
                    if python_results:
                        logger.info(f"DEBUG: Python results keys: {list(python_results.keys())}")
                        if "deep_analysis_results" in python_results:
                            logger.info(f"DEBUG: Deep analysis results count: {len(python_results['deep_analysis_results'])}")
                            logger.info(f"DEBUG: Deep analysis tickers: {list(python_results['deep_analysis_results'].keys())}")
                        else:
                            logger.error("DEBUG: 'deep_analysis_results' key missing from python_results")
                    else:
                        logger.error("DEBUG: python_results is None or empty")

                except Exception as e:
                    logger.error(f"DEBUG: Python analyzer failed with exception: {e}", exc_info=True)
                    python_results = None

                # Convert Python results to Flow format
                if python_results and "deep_analysis_results" in python_results:
                    for ticker, analysis_result in python_results["deep_analysis_results"].items():
                        # Convert DeepAnalysisResult to Flow format
                        deep_analysis_results[ticker] = analysis_result
                else:
                    logger.error("DEBUG: No valid python_results to convert to Flow format")

                # Log Python performance achievements (Requirements 0.4, 0.5, 0.6, 0.7)
                if "performance_metrics" in python_results:
                    metrics = python_results["performance_metrics"]
                    logger.info("🚀 PYTHON PERFORMANCE ACHIEVED:")
                    logger.info(f"  ⚡ Execution time: {metrics.get('total_execution_time_seconds', 0):.2f}s")
                    logger.info(f"  💰 Cost: ${metrics.get('estimated_cost_usd', 0):.2f} (100% reduction)")
                    logger.info(f"  🔄 LLM calls: {metrics.get('llm_calls_made', 0)} (target: 0)")
                    logger.info(f"  📊 Holdings/second: {metrics.get('holdings_per_second', 0):.1f}")
                    logger.info(f"  🎯 Speedup: {metrics.get('speedup_vs_ai', '10-20x')}")

                # Store Python performance metrics in Flow state (Requirements 20.20, 20.21, 20.22, 20.23, 20.24)
                if "performance_metrics" in python_results:
                    self.state.python_analysis_metrics = python_results["performance_metrics"]

                # 🔍 CRITICAL FIX: Integrate A+ Discovery with Deep Analysis Results
                # This implements Requirements 0.13-0.17: Fix "0 opportunities found" issue
                logger.info("🔍 CRITICAL FIX: Integrating A+ Discovery with Deep Analysis Results")
                try:
                    from finwiz.integration.aplus_discovery_integrator import integrate_aplus_discovery_with_deep_analysis

                    discovery_results = integrate_aplus_discovery_with_deep_analysis(session_id)
                    self.state.aplus_discovery_results = discovery_results

                    if discovery_results.get("has_a_plus_analysis", False):
                        logger.info(
                            f"✅ A+ Discovery Integration: Found {discovery_results['total_opportunities_found']} A+ opportunities"
                        )
                    else:
                        logger.info("ℹ️ A+ Discovery Integration: No A+ opportunities found")

                except Exception as e:
                    logger.error(f"A+ Discovery integration failed: {e}")
                    self.state.aplus_discovery_results = {"has_a_plus_analysis": False, "total_opportunities_found": 0}

                # 🔬 CRITICAL FIX: Connect Backtesting Pipeline to Discovery Results
                # This implements Requirements 0.18-0.21: Fix "Backtesting : Non exécuté" issue
                logger.info("🔬 CRITICAL FIX: Connecting Backtesting Pipeline to Discovery Results")
                try:
                    from finwiz.integration.backtesting_pipeline_connector import connect_backtesting_to_discovery_results

                    backtesting_results = connect_backtesting_to_discovery_results(session_id)
                    self.state.backtesting_results = backtesting_results

                    if backtesting_results.get("backtesting_executed", False):
                        logger.info(
                            f"✅ Backtesting Pipeline: Executed for {backtesting_results['candidates_count']} A+ candidates"
                        )
                    else:
                        logger.info(f"ℹ️ Backtesting Pipeline: {backtesting_results.get('reason', 'Not executed')}")

                except Exception as e:
                    logger.error(f"Backtesting pipeline connection failed: {e}")
                    self.state.backtesting_results = {"backtesting_executed": False, "reason": f"Error: {e}"}

                # DIAGNOSTIC LOGGING: Log deep analysis results available
                logger.info("=" * 80)
                logger.info("DIAGNOSTIC: Deep Analysis Results Available")
                logger.info("=" * 80)
                logger.info(f"Deep analysis results count: {len(deep_analysis_results)}")
                logger.info(f"Tickers with deep analysis: {list(deep_analysis_results.keys())}")

                for ticker, analysis in deep_analysis_results.items():
                    grade = getattr(analysis, "grade", "N/A")
                    score = getattr(analysis, "composite_score", 0.0)
                    cached = getattr(analysis, "cached", False)
                    crew_name = getattr(analysis, "crew_name", "Unknown")

                    # Check if this is fallback data
                    is_fallback = grade == "D" and score == 0.6

                    cache_indicator = " [CACHED]" if cached else " [FRESH]"
                    fallback_indicator = " [FALLBACK DATA - SHOULD NOT HAPPEN]" if is_fallback else ""

                    logger.info(
                        f"  {ticker}: Grade={grade}, Score={score:.2f}, Crew={crew_name}{cache_indicator}{fallback_indicator}"
                    )

                    if is_fallback:
                        logger.error(
                            f"  ❌ {ticker} deep analysis contains FALLBACK DATA! "
                            f"This indicates crew did not generate proper analysis."
                        )

                # Check for missing analysis
                holding_tickers = {h.get("ticker") for h in holdings if h.get("ticker")}
                analyzed_tickers = set(deep_analysis_results.keys())
                missing_tickers = holding_tickers - analyzed_tickers

                if missing_tickers:
                    logger.warning(
                        f"  ⚠️  Missing deep analysis for {len(missing_tickers)} holdings: {', '.join(sorted(missing_tickers))}"
                    )

                logger.info("=" * 80)

                # Update structured Flow state
                self.state.deep_analysis_results = deep_analysis_results
                self.state.deep_analysis_success = True
                self.state.deep_analysis_count = len(deep_analysis_results)

                # Log completion with resilience metrics
                if self.state.total_holdings > 0:
                    success_rate = len(deep_analysis_results) / self.state.total_holdings * 100
                else:
                    success_rate = 0
                logger.info(
                    f"Deep analysis completed: {len(deep_analysis_results)}/"
                    f"{self.state.total_holdings} holdings analyzed "
                    f"(success rate: {success_rate:.1f}%, "
                    f"failed: {len(self.state.failed_holdings)}, "
                    f"timeouts: {len(self.state.timeout_holdings)})"
                )

                # FAIL-FAST: Halt immediately if 0% success rate (Requirement 15)
                if len(deep_analysis_results) == 0 and self.state.total_holdings > 0:
                    error_message = (
                        f"❌ CRITICAL FAILURE: Deep analysis failed for ALL {self.state.total_holdings} holdings (0% success rate)\n\n"
                        f"Root Cause Analysis:\n"
                        f"  • Failed holdings: {len(self.state.failed_holdings)}\n"
                        f"  • Timeout holdings: {len(self.state.timeout_holdings)}\n"
                        f"  • Failed tickers: {', '.join(self.state.failed_holdings) if self.state.failed_holdings else 'None'}\n"
                        f"  • Timeout tickers: {', '.join(self.state.timeout_holdings) if self.state.timeout_holdings else 'None'}\n\n"
                        f"Possible Causes:\n"
                        f"  1. Template variable mismatch in crew task configurations\n"
                        f"  2. API connectivity issues (check API keys and network)\n"
                        f"  3. Crew execution errors (check logs for exceptions)\n"
                        f"  4. Data validation failures (check Pydantic schema compliance)\n"
                        f"  5. Timeout threshold too low (current: {self.resilience_config.holding_timeout}s)\n\n"
                        f"Remediation Steps:\n"
                        f"  1. Check logs above for specific error messages\n"
                        f"  2. Verify all API keys are set correctly in .env\n"
                        f"  3. Run template variable validation: python -m finwiz.validation.template_validator\n"
                        f"  4. Test individual crew execution with a single ticker\n"
                        f"  5. Increase holding_timeout in resilience config if timeouts are the issue\n\n"
                        f"Flow execution halted to prevent wasting API calls on discovery/rebalancing/report phases."
                    )

                    logger.critical(error_message)

                    # Update state to reflect critical failure
                    self.state.deep_analysis_success = False
                    self.state.deep_analysis_error = "0% success rate - all holdings failed analysis"

                    # Raise RuntimeError to halt flow execution
                    raise RuntimeError(error_message)

                # Track deep analysis execution for data availability
                if len(deep_analysis_results) > 0:
                    self.availability_tracker.track_data_source(
                        source="deep_analysis",
                        status="available",
                        last_updated=datetime.now(),
                        record_count=len(deep_analysis_results),
                    )
                    logger.info(f"Tracked deep analysis data availability: {len(deep_analysis_results)} holdings analyzed")
                else:
                    error_msg = (
                        f"No deep analysis results generated "
                        f"(failed: {len(self.state.failed_holdings)}, "
                        f"timeouts: {len(self.state.timeout_holdings)})"
                    )
                    self.availability_tracker.track_data_source(
                        source="deep_analysis",
                        status="unavailable",
                        error_message=error_msg,
                    )
                    logger.warning(f"Tracked deep analysis as unavailable: {error_msg}")

                # Check failure rate and create critical alert if > 50%
                if self.state.total_holdings > 0:
                    failure_rate = len(self.state.failed_holdings) / self.state.total_holdings

                    if failure_rate > 0.5:
                        logger.critical(
                            f"High failure rate detected: {failure_rate:.1%} "
                            f"({len(self.state.failed_holdings)}/{self.state.total_holdings} holdings failed)"
                        )

                        # Import AlertManager and create critical alert
                        from finwiz.monitoring.alerting import AlertManager, AlertSeverity, AlertType

                        alert_manager = AlertManager()

                        # Create critical alert with failed holdings metadata
                        await alert_manager.create_alert(
                            alert_type=AlertType.ERROR_RATE,
                            severity=AlertSeverity.CRITICAL,
                            title=f"Critical: High Deep Analysis Failure Rate ({failure_rate:.1%})",
                            message=(
                                f"Deep portfolio analysis experienced a critical failure rate of {failure_rate:.1%}. "
                                f"{len(self.state.failed_holdings)} out of {self.state.total_holdings} holdings failed analysis. "
                                f"This may indicate systemic issues with data sources, API connectivity, or crew execution. "
                                f"Immediate investigation recommended."
                            ),
                            metadata={
                                "failed_holdings": self.state.failed_holdings,
                                "total_holdings": self.state.total_holdings,
                                "successful_holdings": len(deep_analysis_results),
                                "failure_rate": failure_rate,
                                "timeout_holdings": self.state.timeout_holdings,
                                "retry_counts": self.state.retry_counts,
                                "flow_uuid": str(self.state.id) if hasattr(self.state, "id") else None,
                                "timestamp": datetime.now().isoformat(),
                            },
                        )

                        logger.info("Critical alert created for high failure rate")
            except Exception as e:
                logger.error(f"Deep analysis failed: {e}", exc_info=True)
                self.state.deep_analysis_error = str(e)
                self.state.deep_analysis_success = False
                self.state.deep_analysis_results = {}
                self.state.deep_analysis_count = 0
                logger.warning("Continuing with degraded functionality (no deep analysis)")

            # Step 2: REMOVED - Alternatives matching moved to Phase 4.5 (after discovery)
            # Alternatives matching requires discovery crew output, which doesn't exist yet
            # It will run in match_alternatives_after_discovery() after Phase 4
            logger.info("Step 2/3: Skipping alternatives matching (will run after discovery in Phase 4.5)")

            # Initialize empty alternatives data (will be populated in Phase 4.5)
            self.state.portfolio_alternatives = {}
            self.state.alternatives_success = False
            self.state.alternatives_count = 0

            # Step 3: Update portfolio review with enriched data (ONCE) - async
            logger.info("Step 3/3: Updating portfolio review with enriched data")
            portfolio_updated = False
            try:
                portfolio_updated = await self._update_portfolio_review_with_enriched_data()

                if not portfolio_updated:
                    logger.warning("Portfolio review update failed - retaining original portfolio")
                else:
                    # DIAGNOSTIC LOGGING: Log portfolio holdings AFTER merge
                    logger.info("=" * 80)
                    logger.info("DIAGNOSTIC: Portfolio Holdings AFTER Deep Analysis Merge")
                    logger.info("=" * 80)

                    # Reload portfolio to verify merge
                    portfolio_data = self.state.portfolio_review
                    if "portfolio_review" in portfolio_data:
                        updated_holdings = portfolio_data["portfolio_review"].get("holdings", [])
                    else:
                        updated_holdings = portfolio_data.get("holdings", [])

                    logger.info(f"Total holdings after merge: {len(updated_holdings)}")

                    grades_changed = 0
                    still_fallback = 0

                    for idx, holding in enumerate(updated_holdings, 1):
                        ticker = holding.get("ticker", "UNKNOWN")
                        grade = holding.get("grade", "N/A")
                        score = holding.get("composite_score", 0.0)
                        rationale = holding.get("rationale_bullets", [])
                        has_deep = holding.get("has_deep_analysis", False)
                        crew_used = holding.get("crew_analysis_used", "None")

                        # Check for fallback data pattern
                        is_fallback = (
                            grade == "D" and score == 0.6 and any("Validation rapide" in str(bullet) for bullet in rationale)
                        )

                        if is_fallback:
                            still_fallback += 1
                            fallback_indicator = " [STILL FALLBACK - MERGE FAILED!]"
                            logger.error(
                                f"  ❌ {idx}. {ticker}: Grade={grade}, Score={score:.2f}, "
                                f"HasDeepAnalysis={has_deep}, Crew={crew_used}{fallback_indicator}"
                            )
                        else:
                            grades_changed += 1
                            logger.info(
                                f"  ✅ {idx}. {ticker}: Grade={grade}, Score={score:.2f}, "
                                f"HasDeepAnalysis={has_deep}, Crew={crew_used}"
                            )

                    # Summary of merge results
                    logger.info("-" * 80)
                    logger.info("Merge Summary:")
                    logger.info(f"  Total holdings: {len(updated_holdings)}")
                    logger.info(f"  Successfully merged (non-fallback): {grades_changed}")
                    logger.info(f"  Still fallback data: {still_fallback}")
                    logger.info(f"  Deep analysis available: {len(deep_analysis_results)}")
                    logger.info(f"  Alternatives found: {self.state.alternatives_count}")

                    if still_fallback > 0:
                        logger.error(f"  ❌ MERGE VERIFICATION FAILED: {still_fallback} holdings still have fallback data!")
                        logger.error("  This indicates the merge did not properly apply deep analysis results.")
                    else:
                        logger.info("  ✅ MERGE VERIFICATION PASSED: All holdings have actual analysis data")

                    logger.info("=" * 80)

            except Exception as e:
                logger.error(f"Portfolio review update failed: {e}", exc_info=True)

                # FAIL-FAST: If merge failed due to no deep analysis results, stop the flow
                if "No deep analysis results provided" in str(e):
                    logger.critical("=" * 80)
                    logger.critical("CRITICAL FAILURE: Deep analysis produced no results")
                    logger.critical("Cannot continue to discovery without portfolio analysis")
                    logger.critical("=" * 80)
                    raise RuntimeError(
                        "Deep analysis failed completely (0 successful analyses). "
                        "Cannot generate report or continue to discovery. "
                        "Check logs for root cause (likely missing template variables or API errors)."
                    ) from e

                logger.warning("Continuing with original portfolio review")

            # VALIDATION: Check if we actually have deep analysis results
            if not deep_analysis_results:
                logger.critical("=" * 80)
                logger.critical("CRITICAL FAILURE: No deep analysis results available")
                logger.critical(f"Holdings analyzed: {self.state.deep_analysis_count}")
                logger.critical(f"Holdings failed: {self.state.deep_analysis_failed_count}")
                logger.critical("Cannot continue to discovery without portfolio analysis")
                logger.critical("=" * 80)
                raise RuntimeError(
                    f"Deep analysis failed for all {self.state.total_holdings} holdings. "
                    "Cannot generate report or continue to discovery. "
                    "Check logs for root cause (likely missing template variables or API errors)."
                )

            # Return consolidated results for downstream Flow listeners
            return {
                "deep_analysis_complete": True,
                "analysis_results": {ticker: result.model_dump(mode="json") for ticker, result in deep_analysis_results.items()},
                "portfolio_updated": portfolio_updated,
                "holdings_analyzed": self.state.deep_analysis_count,
                # Note: alternatives_count will be 0 here, populated in Phase 4.5
                "alternatives_found": 0,
            }

        except Exception as e:
            logger.error(f"Consolidated portfolio analysis failed: {e}", exc_info=True)
            # Update structured Flow state with error info
            self.state.deep_analysis_error = str(e)
            self.state.deep_analysis_success = False
            self.state.deep_analysis_results = {}

            logger.warning("Deep analysis failed - continuing with shallow validation")

            # Return error info for downstream listeners
            return {
                "deep_analysis_complete": False,
                "analysis_results": {},
                "portfolio_updated": False,
                "error": str(e),
            }

    @start("validate_data_integration")  # Conditional start for resume capability
    @listen("validate_data_integration")
    async def check_portfolio(self) -> dict[str, Any]:
        """
        Run portfolio keep-or-sell review orchestrator with parallel processing.

        Phase 2: Portfolio Analysis
        - Analyzes what you currently own using parallel processing
        - Generates initial portfolio review WITHOUT deep analysis
        - Identifies holdings that need evaluation
        - Triggers: analyze_and_update_portfolio (Phase 3)

        Performance: Uses async/await for parallel holdings processing,
        reducing time from ~66 seconds to ~2-5 seconds for 66 holdings.

        Flow Rationale: We must analyze our current holdings BEFORE finding alternatives
        or discovering new opportunities. This establishes the baseline for improvement.

        Resume Capability: If portfolio_review already exists in state (from checkpoint),
        this method will skip execution and return "Skipped" to enable flow resumption.

        Requirements: 3.4-3.6
        """
        # Check if resuming from checkpoint and portfolio already analyzed
        if self.state.resume_from_checkpoint and self.state.portfolio_review is not None and self.state.portfolio_review:
            # Extract holdings count for logging
            portfolio_data = self.state.portfolio_review
            if "portfolio_review" in portfolio_data:
                holdings = portfolio_data["portfolio_review"].get("holdings", [])
            else:
                holdings = portfolio_data.get("holdings", [])

            holdings_count = len(holdings)
            logger.info(f"Resume: Portfolio already analyzed ({holdings_count} holdings), skipping portfolio review")

            return {
                "status": "skipped",
                "reason": "resumed_from_checkpoint",
                "portfolio_review_complete": True,
                "resumed": True,
                "holdings_count": holdings_count,
            }

        enabled = (os.getenv("PORTFOLIO_REVIEW_ENABLED") or "true").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        if not enabled:
            logger.info("Portfolio review disabled via PORTFOLIO_REVIEW_ENABLED")
            return {"portfolio_review_enabled": False}

        try:
            # Check core analysis availability
            core_analysis_available = self._check_core_analysis_availability()

            if core_analysis_available["any_available"]:
                logger.info(
                    f"Starting portfolio review with core analysis results available: {core_analysis_available['available_crews']}"
                )
            else:
                logger.warning("Starting portfolio review without core analysis results - all crews failed or disabled")

            # Store core analysis status in structured state
            self.state.core_analysis_status = core_analysis_available

            # Pass Flow state to portfolio review for deep analysis integration (async)
            # Note: Deep analysis will be merged after analyze_holdings_deep() completes
            out_path = await run_portfolio_review(flow_state=None)  # Initial run without deep analysis
            self.state.portfolio_review_json = str(out_path)

            # Load content for tool-less reporter consumption and structured state
            # Use Pydantic validation for type safety
            try:
                from finwiz.schemas.portfolio_review import PortfolioReview
                from finwiz.utils.pydantic_json_loader import load_json_with_validation

                portfolio_review = load_json_with_validation(
                    out_path,
                    PortfolioReview,
                    strict=False,  # Log warnings but don't fail
                )
                # Convert to dict for state storage (mode='json' serializes datetime to strings)
                portfolio_data = portfolio_review.model_dump(mode="json")
                self.state.portfolio_review = portfolio_data
            except Exception as le:
                logger.warning(f"Failed to load portfolio review JSON content: {le}")
                # Continue with degraded functionality
                self.state.portfolio_review = {}
                portfolio_data = {}

            logger.info(f"Portfolio review generated at {out_path}")

            # Track portfolio review execution
            self.availability_tracker.track_data_source(
                source="portfolio_review",
                status="available",
                last_updated=datetime.now(),
                record_count=len(portfolio_data.get("holdings", [])),
            )

            return {
                "portfolio_review_complete": True,
                "portfolio_path": str(out_path),
                "holdings_count": len(portfolio_data.get("holdings", [])),
            }

        except Exception as e:
            logger.error(f"Portfolio review failed: {e}", exc_info=True)
            # Continue with graceful degradation instead of raising
            self.state.portfolio_review_error = str(e)
            self.state.portfolio_review = {}
            self.state.portfolio_review_json = None
            logger.warning("Portfolio review failed - continuing with empty portfolio data")

            # Track portfolio review failure
            self.availability_tracker.track_data_source(source="portfolio_review", status="unavailable", error_message=str(e))

            return {"portfolio_review_complete": False, "error": str(e)}

    @listen("check_investment_discovery")
    def match_alternatives_after_discovery(self) -> dict[str, Any]:
        """
        Match alternatives for underperforming holdings using discovery crew results.

        Phase 4.5: Alternatives Matching (After Discovery)
        - Runs AFTER discovery crews have generated A+ candidates
        - Matches alternatives for holdings with grades C, D, F
        - Uses discovery crew output from output/discovery/discovery_latest.json
        - Triggers: check_portfolio_rebalancing (Phase 5)

        Flow Rationale: Alternatives matching requires discovery crew output,
        so it must run AFTER Phase 4 (discovery) but BEFORE Phase 5 (rebalancing).
        """
        logger.info("=" * 80)
        logger.info("Phase 4.5: Matching alternatives for underperforming holdings")
        logger.info("=" * 80)

        # Check if alternative matching is enabled
        enabled = (os.getenv("PORTFOLIO_ENABLE_ALTERNATIVES") or "true").strip().lower() in {"1", "true", "yes", "on"}
        if not enabled:
            logger.info("Alternative matching disabled via PORTFOLIO_ENABLE_ALTERNATIVES")
            return {"alternatives_matching_enabled": False}

        try:
            # Get deep analysis results from state
            deep_analysis_results = self.state.deep_analysis_results or {}

            if not deep_analysis_results:
                logger.warning("No deep analysis results available for alternative matching")
                return {"alternatives_matching_complete": False, "reason": "no_deep_analysis"}

            # Match alternatives using discovery crew output
            alternatives_data = self._match_alternatives_for_holdings(deep_analysis_results)

            # Update structured Flow state
            self.state.portfolio_alternatives = alternatives_data
            self.state.alternatives_success = True
            self.state.alternatives_count = sum(len(alts) for alts in alternatives_data.values())

            logger.info(f"Alternative matching completed: {self.state.alternatives_count} alternatives found")

            # Track alternatives data availability
            if self.state.alternatives_count > 0:
                self.availability_tracker.track_data_source(
                    source="alternatives",
                    status="available",
                    last_updated=datetime.now(),
                    record_count=self.state.alternatives_count,
                )
                logger.info(f"Tracked alternatives data availability: {self.state.alternatives_count} alternatives found")
            else:
                self.availability_tracker.track_data_source(
                    source="alternatives",
                    status="available",
                    last_updated=datetime.now(),
                    record_count=0,
                )
                logger.info("Tracked alternatives data availability: No alternatives needed (all holdings performing well)")

            logger.info("=" * 80)

            return {"alternatives_matching_complete": True, "alternatives_count": self.state.alternatives_count}

        except Exception as e:
            logger.error(f"Alternative matching failed: {e}", exc_info=True)
            self.state.alternatives_error = str(e)
            self.state.alternatives_success = False
            self.state.portfolio_alternatives = {}
            self.state.alternatives_count = 0
            logger.warning("Continuing with degraded functionality (no alternatives)")

            return {"alternatives_matching_complete": False, "error": str(e)}

    @listen("match_alternatives_after_discovery")
    def check_portfolio_rebalancing(self) -> dict[str, Any]:
        """
        Run portfolio rebalancing analysis after alternatives matching.

        Phase 5: Rebalancing
        - Generates trade recommendations with complete data
        - Optimizes allocations considering both portfolio analysis and A+ discoveries
        - Calculates price targets and position sizing
        - Triggers: pre_validate_reporter_input (Phase 6)

        Flow Rationale: Rebalancing happens AFTER we have complete information:
        - Portfolio holdings with grades (Phase 3)
        - A+ discovery opportunities (Phase 4)
        This ensures optimal allocation decisions with full context.
        """
        if not is_feature_enabled("portfolio_rebalancing"):
            logger.info("Portfolio rebalancing disabled via feature flag")
            self.state.portfolio_rebalancing_available = False
            return {"portfolio_rebalancing_enabled": False}

        try:
            # Check core analysis availability
            core_analysis_status = self._check_core_analysis_availability()

            # Create crew inputs via factory (convert state to dict for compatibility)
            crew_inputs = self.crew_factory.create_crew_inputs_for_portfolio_rebalancing(
                self._state_to_dict(), core_analysis_status
            )

            # Execute portfolio rebalancing crew via factory
            result_data = self.crew_factory.execute_portfolio_rebalancing_crew(crew_inputs)

            # Update structured state from result
            self._update_state_from_dict(result_data)

            # Return data for downstream listeners
            return {
                "portfolio_rebalancing_complete": True,
                "rebalancing_available": result_data.get("portfolio_rebalancing_available", False),
            }

        except Exception as e:
            logger.error(f"Portfolio rebalancing analysis failed: {e}", exc_info=True)
            # Continue with graceful degradation - update structured state
            self.state.portfolio_rebalancing_available = False
            self.state.portfolio_rebalancing_error = str(e)
            self.state.portfolio_rebalancing_result = None
            logger.warning("Portfolio rebalancing failed - continuing without rebalancing analysis")
            return {"portfolio_rebalancing_complete": False, "error": str(e)}

    @listen(and_("check_crypto", "check_stock", "check_etf"))
    def check_investment_discovery(self) -> dict[str, Any]:
        """
        Run investment discovery analysis to find A+ grade opportunities.

        Phase 4: Investment Discovery (Consolidation)
        - Consolidates results from discovery crews (crypto, stock, ETF)
        - Finds A+ grade opportunities across all asset classes
        - Validates opportunities through backtesting
        - Triggers: check_portfolio_rebalancing (Phase 5)

        Flow Rationale: After discovery crews find top 10 candidates in each asset class,
        this method consolidates them and identifies the best A+ opportunities to address
        the needs identified in Phase 3 (alternative matching).
        """
        # Check if investment discovery is enabled via feature flag
        if not is_feature_enabled("investment_discovery"):
            logger.info("Investment discovery disabled via feature flag")
            self.state.investment_discovery_available = False
            return {"investment_discovery_enabled": False}

        try:
            # TASK 6: Validate crew data consolidation before running discovery
            logger.info("=" * 80)
            logger.info("DATA CONSOLIDATION VALIDATION - Before Investment Discovery")
            logger.info("=" * 80)

            # Instantiate DataConsolidationValidator
            validator = DataConsolidationValidator(self.integration_manager.registry_manager)

            try:
                # Validate that stock/etf/crypto crew data exists
                logger.info("Validating crew data retrieval for: stock, etf, crypto")
                validated_crew_data = validator.validate_crew_data_retrieval(["stock", "etf", "crypto"])

                # Log validation results
                logger.info(f"✅ Data consolidation validation passed: {len(validated_crew_data)} crews validated")
                for crew_name in validated_crew_data.keys():
                    logger.info(f"  ✅ {crew_name} crew data validated and available")

            except DataRetrievalError as e:
                # FAIL-FAST: Stop execution if crew data is missing or corrupted
                logger.error(f"❌ Data consolidation validation failed: {e}")
                logger.error("REFUSING to run investment discovery with missing/corrupted crew data")

                # Update state with validation failure
                self.state.investment_discovery_available = False
                self.state.investment_discovery_error = f"Data validation failed: {str(e)}"

                # Track validation failure
                self.availability_tracker.track_data_source(
                    source="discovery_crew", status="unavailable", error_message=f"Data validation failed: {str(e)}"
                )

                logger.info("=" * 80)

                # Return error to downstream listeners
                return {"investment_discovery_complete": False, "discovery_available": False, "validation_error": str(e)}

            logger.info("=" * 80)

            # Check if we have portfolio data from portfolio review
            if self.state.portfolio_review:
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

                # Create crew inputs via factory (convert state to dict for compatibility)
                crew_inputs = self.crew_factory.create_crew_inputs_for_investment_discovery(
                    self._state_to_dict(), core_analysis_status, upstream_data, core_analysis_data
                )

                # Log enhanced inputs
                logger.info(f"Investment discovery enhanced with {len(core_analysis_data)} core analysis results")
                if core_analysis_data:
                    logger.info(f"Core analysis types available: {list(core_analysis_data.keys())}")
                if core_analysis_status["failed_crews"]:
                    logger.warning(f"Core analysis crews failed: {core_analysis_status['failed_crews']}")

                # Execute investment discovery crew via factory
                result_data = self.crew_factory.execute_investment_discovery_crew(crew_inputs)

                # Update structured state from result
                self._update_state_from_dict(result_data)

                # Store crew result in integration system (use result_data since result is not defined)
                if "result" in result_data:
                    crew_result = result_data["result"]
                    self.integration_manager.store_crew_output("discovery", crew_result)

                    # Store crew result - convert CrewOutput to string for template interpolation
                    if hasattr(crew_result, "raw"):
                        result_text = str(crew_result.raw)
                        self.state.investment_discovery_result = result_text
                    else:
                        result_text = str(crew_result)
                        self.state.investment_discovery_result = result_text
                else:
                    # Fallback if no result in result_data
                    self.state.investment_discovery_result = str(result_data)

                # Use integrated A+ opportunity extraction (with error handling)
                try:
                    aplus_opportunities = self.data_accessor.get_aplus_opportunities()
                    if aplus_opportunities:
                        self.state.investment_discovery_structured = {
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

                        # Extract market context from discovery results
                        try:
                            market_context = aplus_opportunities.market_context
                            if market_context:
                                self.state.market_context = market_context
                                logger.info(
                                    f"Market context extracted: VIX={market_context.get('vix_level')}, "
                                    f"regime={market_context.get('regime_type')}, "
                                    f"inflation={market_context.get('inflation_rate')}, "
                                    f"rates={market_context.get('interest_rate_trend')}"
                                )
                            else:
                                logger.warning("No market context found in discovery results")
                        except Exception as e:
                            logger.warning(f"Could not extract market context from discovery results: {e}")
                    else:
                        logger.warning("No A+ opportunities extracted via integration system")
                        self.state.investment_discovery_structured = {"has_a_plus_analysis": False}

                except Exception as e:
                    logger.warning(f"Could not extract A+ data via integration system: {e}")
                    self.state.investment_discovery_structured = {"has_a_plus_analysis": False}

                self.state.investment_discovery_available = True

                # Track discovery crew execution
                aplus_count = 0
                if self.state.investment_discovery_structured.get("has_a_plus_analysis"):
                    aplus_count = (
                        len(self.state.investment_discovery_structured.get("etf_opportunities", []))
                        + len(self.state.investment_discovery_structured.get("stock_opportunities", []))
                        + len(self.state.investment_discovery_structured.get("crypto_opportunities", []))
                    )

                self.availability_tracker.track_data_source(
                    source="discovery_crew", status="available", last_updated=datetime.now(), record_count=aplus_count
                )

                logger.info("Investment discovery analysis completed successfully with enhanced error handling")

                # CRITICAL: Return discovery data for downstream listeners (especially report crew)
                return {
                    "investment_discovery_complete": True,
                    "discovery_available": True,
                    "has_a_plus_analysis": self.state.investment_discovery_structured.get("has_a_plus_analysis", False),
                    # CRITICAL: Pass aplus_opportunities to downstream methods
                    "aplus_opportunities": self.state.investment_discovery_structured,
                    "investment_discovery_structured": self.state.investment_discovery_structured,
                }
            else:
                logger.warning("No portfolio data available for investment discovery analysis")
                self.state.investment_discovery_available = False

                # Track discovery as unavailable
                self.availability_tracker.track_data_source(
                    source="discovery_crew", status="unavailable", error_message="No portfolio data available"
                )

                return {"investment_discovery_complete": False, "discovery_available": False}

        except Exception as e:
            logger.error(f"Investment discovery analysis failed: {e}", exc_info=True)
            # Continue with graceful degradation - update structured state
            self.state.investment_discovery_available = False
            self.state.investment_discovery_error = str(e)
            self.state.investment_discovery_result = None
            self.state.investment_discovery_structured = {"has_a_plus_analysis": False}
            logger.warning("Investment discovery failed - continuing without discovery analysis")

            # Track discovery failure
            self.availability_tracker.track_data_source(source="discovery_crew", status="unavailable", error_message=str(e))

            return {"investment_discovery_complete": False, "error": str(e)}

    def _check_core_analysis_availability(self) -> dict[str, Any]:
        """Check which core analysis crews are available and their status."""
        return self.state_manager.check_core_analysis_availability(self.state)

    def _extract_market_conditions(self) -> dict[str, Any]:
        """Extract market conditions from core analysis results."""
        return self.state_manager.extract_market_conditions(self.state)

    def _extract_market_context_from_core_analysis(self, core_analysis_data: dict[str, Any]) -> dict[str, Any]:
        """Extract market context information from core analysis results."""
        return self.state_manager.extract_market_context_from_core_analysis(core_analysis_data)

    @listen("check_portfolio_rebalancing")
    def pre_validate_reporter_input(self) -> dict[str, Any]:
        """
        Validate ReporterInput payload before triggering the final report.

        Phase 6: Reporting (Pre-validation)
        - Validates all data is available for report generation
        - Consolidates data from all previous phases
        - Prepares structured data for final report
        - Triggers: report (Phase 6 final)

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
                logger.debug(
                    "Retrieved consolidated data from integration system",
                    extra={
                        "data_keys": list(consolidated_data.keys()),
                        "has_consolidated_crew_data": "consolidated_crew_data" in consolidated_data,
                        "data_size": len(str(consolidated_data)),
                    },
                )
            except Exception as e:
                logger.warning(f"Failed to get consolidated data from integration system: {e}", exc_info=True)
                consolidated_data = {}

            # Store consolidated data in structured state
            self.state.consolidated_data = consolidated_data

            # Add integrated data access information to structured state
            self.state.integrated_data_available = len(consolidated_data) > 0
            self.state.market_sentiment = consolidated_data.get("market_sentiment", {})
            self.state.ticker_validation = consolidated_data.get("ticker_validation", {})

            # DISK-FIRST APPROACH: Always use disk-based data for consistency and persistence
            # The data_accessor reads from disk with freshness checks and caching
            self.state.aplus_opportunities = consolidated_data.get("aplus_opportunities")
            logger.info(f"Loaded discovery data from disk: {bool(self.state.aplus_opportunities)}")

            self.state.portfolio_allocation_updates = consolidated_data.get("portfolio_allocation_updates")
            self.state.aplus_availability_status = consolidated_data.get("aplus_availability_status")

            # Enhanced: Add core analysis data to reporter inputs with error handling
            try:
                core_analysis_summary = self._prepare_core_analysis_summary(consolidated_data)
                self.state.core_analysis_summary = core_analysis_summary
            except Exception as e:
                logger.warning(f"Failed to prepare core analysis summary: {e}")
                self.state.core_analysis_summary = {
                    "available_crews": core_analysis_status["available_crews"],
                    "failed_crews": core_analysis_status["failed_crews"],
                    "disabled_crews": core_analysis_status["disabled_crews"],
                    "error": "Failed to prepare detailed summary",
                }

            # Note: Individual core analysis results are in consolidated_data["consolidated_crew_data"]
            # which is stored in self.state.consolidated_data
            crew_data = consolidated_data.get("consolidated_crew_data", {})

            # Debug logging to help diagnose data consolidation issues
            logger.debug(
                "Checking consolidated crew data",
                extra={
                    "crew_data_keys": list(crew_data.keys()) if crew_data else [],
                    "crew_data_empty": len(crew_data) == 0,
                    "crew_data_type": type(crew_data).__name__,
                },
            )

            core_analysis_count = 0
            for crew_type in ["stock", "etf", "crypto"]:
                if crew_type in crew_data:
                    # Validate that the data is not empty
                    if crew_data[crew_type]:
                        logger.info(f"Core analysis data available for {crew_type} in reporter input")
                        core_analysis_count += 1
                    else:
                        logger.warning(
                            f"Core analysis data present for {crew_type} but appears empty",
                            extra={"data_type": type(crew_data[crew_type]).__name__},
                        )
                else:
                    if core_analysis_status[f"{crew_type}_available"]:
                        logger.warning(
                            f"Core analysis data missing for {crew_type} despite being marked available",
                            extra={
                                "all_crew_data_keys": list(crew_data.keys()),
                                "consolidated_data_keys": list(consolidated_data.keys()),
                            },
                        )

            # Add error and fallback information to structured state
            # Note: core_analysis_status is already in self.state.core_analysis_status
            self.state.system_health = self.error_handler.get_system_health_status()

            # Add error summaries for transparency in reporting
            error_summaries = []
            for crew_name in ["stock", "etf", "crypto"]:
                error_summary = self.error_handler.get_error_summary(crew_name)
                error_summaries.append({"crew": crew_name, "summary": error_summary})
            self.state.error_summaries = error_summaries

            # Log consolidation results
            crew_data = consolidated_data.get("consolidated_crew_data", {})
            crew_count = len([k for k in crew_data.keys() if k in ["stock", "etf", "crypto", "discovery", "portfolio"]])
            # Use the core_analysis_count calculated above

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
                    self.state.reporter_input = model.model_dump(mode="json")
                    logger.info("ReporterInput validated using example data")
                else:
                    logger.warning("No example data available for validation")

            # Generate data availability summary for reporter
            availability_summary = self.availability_tracker.get_availability_summary()
            # Use mode='json' to serialize datetime objects to ISO strings for CrewAI compatibility
            self.state.data_availability_summary = availability_summary.model_dump(mode="json")
            self.state.data_availability_summary_formatted = self.availability_tracker.format_summary_for_report(
                availability_summary
            )

            logger.info(
                "Data availability summary generated for reporter",
                extra={
                    "total_sources": availability_summary.total_sources,
                    "available_sources": availability_summary.available_sources,
                    "unavailable_sources": availability_summary.unavailable_sources,
                    "stale_sources": availability_summary.stale_sources,
                },
            )

            # Extract SEC filing URLs for stock holdings
            sec_filing_urls = self._extract_sec_filing_urls()
            self.state.sec_filing_urls = sec_filing_urls
            logger.info(f"Extracted SEC filing URLs for {len(sec_filing_urls)} stock holdings")

            logger.info("Reporter input preparation completed with integrated data and core analysis")

            # Return data for downstream listeners
            return {
                "reporter_input_validated": True,
                "integrated_data_available": self.state.integrated_data_available,
                "crew_count": crew_count,
                "core_analysis_count": core_analysis_count,
            }

        except Exception as e:
            logger.error(f"Reporter input preparation failed: {e}", exc_info=True)
            # Continue with graceful degradation - update structured state
            self.state.integrated_data_error = str(e)
            return {"reporter_input_validated": False, "error": str(e)}

    def _prepare_core_analysis_summary(self, consolidated_data: dict[str, Any]) -> dict[str, Any]:
        """Prepare a summary of core analysis results for the reporter."""
        return self.state_manager.prepare_core_analysis_summary(consolidated_data)

    def _extract_sec_filing_urls(self) -> dict[str, dict[str, str]]:
        """
        Extract SEC filing URLs from stock holdings analysis.

        Checks both deep_analysis_results and stock_analysis_result for SEC data.
        Validates URLs and regenerates them using SECFilingURLGenerator if invalid.

        Returns:
            Dictionary mapping ticker to filing URLs: {"AAPL": {"10-K": "url", "10-Q": "url"}}

        """
        from finwiz.tools.sec_filing_url_generator import SECFilingURLGenerator
        from finwiz.utils.url_validator import get_url_validator

        sec_filing_urls = {}
        url_generator = SECFilingURLGenerator()
        url_validator = get_url_validator()

        try:
            # Check deep_analysis_results for SEC data from stock holdings
            if hasattr(self.state, "deep_analysis_results") and self.state.deep_analysis_results:
                for ticker, analysis in self.state.deep_analysis_results.items():
                    # Check if this is a stock holding with SEC data
                    if isinstance(analysis, dict):
                        asset_class = analysis.get("asset_class", "").lower()
                        if asset_class == "stock":
                            # Extract SEC filing URLs if available
                            sec_data = analysis.get("sec_filing_urls") or analysis.get("sec_filings")
                            if sec_data and isinstance(sec_data, dict):
                                # Validate and fix URLs
                                validated_urls = self._validate_and_fix_sec_urls(ticker, sec_data, url_generator, url_validator)
                                if validated_urls:
                                    sec_filing_urls[ticker] = validated_urls
                                    logger.debug(f"Extracted SEC filing URLs for {ticker} from deep analysis")

            # Check stock_analysis_result for SEC data from stock crew
            if hasattr(self.state, "stock_analysis_result") and self.state.stock_analysis_result:
                stock_result = self.state.stock_analysis_result
                if isinstance(stock_result, dict):
                    # Check for SEC data in the stock crew result
                    sec_data = stock_result.get("sec_filing_urls") or stock_result.get("sec_filings")
                    if sec_data and isinstance(sec_data, dict):
                        # Merge with existing data (deep analysis takes precedence)
                        for ticker, urls in sec_data.items():
                            if ticker not in sec_filing_urls:
                                # Validate and fix URLs
                                validated_urls = self._validate_and_fix_sec_urls(ticker, urls, url_generator, url_validator)
                                if validated_urls:
                                    sec_filing_urls[ticker] = validated_urls
                                    logger.debug(f"Extracted SEC filing URLs for {ticker} from stock crew")

            if not sec_filing_urls:
                logger.info("No SEC filing URLs found in analysis results")
            else:
                logger.info(f"Extracted SEC filing URLs for {len(sec_filing_urls)} stock holdings")

            return sec_filing_urls

        except Exception as e:
            logger.warning(f"Failed to extract SEC filing URLs: {e}", exc_info=True)
            return {}

    def _validate_and_fix_sec_urls(self, ticker: str, sec_data: dict, url_generator, url_validator) -> dict[str, str]:
        """
        Validate SEC URLs and regenerate them if invalid.

        Args:
            ticker: Stock ticker symbol
            sec_data: Dictionary of filing type to URL
            url_generator: SECFilingURLGenerator instance
            url_validator: URL validator instance

        Returns:
            Dictionary of validated/fixed URLs

        """
        validated_urls = {}

        for filing_type, url in sec_data.items():
            if not url or not isinstance(url, str):
                # No URL provided, generate one
                logger.debug(f"No URL for {ticker} {filing_type}, generating...")
                metadata = url_generator.get_filing_metadata(ticker, filing_type)
                if metadata and metadata.get("filing_url"):
                    validated_urls[filing_type] = metadata["filing_url"]
                    logger.info(f"Generated SEC URL for {ticker} {filing_type}")
                continue

            # Check if URL is valid format
            if not url_validator.is_valid_url(url, f"SEC filing {ticker} {filing_type}"):
                # Invalid URL, regenerate
                logger.warning(f"Invalid SEC URL for {ticker} {filing_type}: {url}")
                metadata = url_generator.get_filing_metadata(ticker, filing_type)
                if metadata and metadata.get("filing_url"):
                    validated_urls[filing_type] = metadata["filing_url"]
                    logger.info(f"Regenerated SEC URL for {ticker} {filing_type}")
            else:
                # URL looks valid, keep it
                validated_urls[filing_type] = url

        return validated_urls

    @listen("pre_validate_reporter_input")
    def report(self) -> dict[str, Any]:
        """
        Generate a consolidated report after all analyses are complete.

        Phase 6: Reporting (Final)
        - Generates comprehensive HTML report in French
        - Consolidates all analysis results from previous phases
        - Presents actionable recommendations

        Flow Rationale: Final report has access to complete data:
        - Portfolio analysis with grades (Phase 2-3)
        - A+ discovery opportunities (Phase 4)
        - Rebalancing recommendations (Phase 5)
        This ensures comprehensive, well-informed recommendations.
        """
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
            if self.state.integrated_data_available:
                logger.info("Report generation using integrated data system")

                # Log available integrated data components
                if self.state.market_sentiment:
                    sentiment_quality = self.state.market_sentiment.get("data_quality", "UNKNOWN")
                    logger.info(f"Market sentiment data available (quality: {sentiment_quality})")

                if self.state.ticker_validation:
                    validation_rate = self.state.ticker_validation.get("validation_summary", {}).get("validation_rate", 0)
                    logger.info(f"Ticker validation data available (rate: {validation_rate:.1f}%)")

                if self.state.aplus_opportunities:
                    logger.info("A+ opportunities data available for report")

                # Log core analysis status
                if core_analysis_status["any_available"]:
                    logger.info(f"Core analysis data available for report: {core_analysis_status['available_crews']}")
                else:
                    logger.warning("No core analysis data available for report")

                # Log data availability warnings
                if self.state.stale_data_warnings:
                    logger.warning("Report generated with stale data warnings")

                # Log error information for transparency
                if core_analysis_status["failed_crews"]:
                    logger.warning(f"Report includes fallback data for failed crews: {core_analysis_status['failed_crews']}")

            else:
                logger.warning("Report generation without integrated data system")

            # Add system status to structured state for report transparency
            self.state.system_status_for_report = {
                "core_analysis_status": core_analysis_status,
                "system_health": system_health,
                "degraded_functionality": self._get_degraded_functionality_summary(),
                "report_generation_timestamp": datetime.now().isoformat(),
            }

            # Execute report crew via factory (convert state to dict for compatibility)
            state_dict = self._state_to_dict()

            # Debug: Check critical data before passing to report crew
            logger.info("=" * 80)
            logger.info("CRITICAL DATA CHECK BEFORE REPORT GENERATION")
            logger.info("=" * 80)

            if "portfolio_review" in state_dict:
                if state_dict["portfolio_review"]:
                    logger.info(f"✅ portfolio_review present in state (type: {type(state_dict['portfolio_review'])})")
                else:
                    logger.warning(f"⚠️ portfolio_review is None/empty in Flow state (type: {type(state_dict['portfolio_review'])})")
            else:
                logger.error("❌ portfolio_review key missing from Flow state before report generation!")

            if "aplus_opportunities" in state_dict:
                if state_dict["aplus_opportunities"]:
                    logger.info(f"✅ aplus_opportunities present in state (type: {type(state_dict['aplus_opportunities'])})")
                    if isinstance(state_dict["aplus_opportunities"], dict):
                        logger.info(f"   Keys: {list(state_dict['aplus_opportunities'].keys())}")
                else:
                    logger.warning("⚠️ aplus_opportunities is None/empty in Flow state")
            else:
                logger.error("❌ aplus_opportunities key missing from Flow state before report generation!")

            if "data_availability_summary" in state_dict:
                logger.info("✅ data_availability_summary present in state")
            else:
                logger.error("❌ data_availability_summary key missing from Flow state!")

            if "data_availability_summary_formatted" in state_dict:
                logger.info("✅ data_availability_summary_formatted present in state")
            else:
                logger.error("❌ data_availability_summary_formatted key missing from Flow state!")

            if "sec_filing_urls" in state_dict:
                if state_dict["sec_filing_urls"]:
                    logger.info(f"✅ sec_filing_urls present: {len(state_dict['sec_filing_urls'])} tickers")
                else:
                    logger.warning("⚠️ sec_filing_urls is empty")
            else:
                logger.error("❌ sec_filing_urls key missing from Flow state!")

            logger.info(f"Total state keys: {len(state_dict)}")
            logger.info("=" * 80)

            # CRITICAL: Validate report inputs before generating report
            # This prevents hallucinated data and ensures data quality
            logger.info("=" * 80)
            logger.info("VALIDATING REPORT INPUTS")
            logger.info("=" * 80)

            try:
                validator = ReportDataValidator()

                # Validate all required fields are present and valid
                validator.validate_report_inputs(state_dict)

                # Validate portfolio review data doesn't contain fallback patterns
                if "portfolio_review" in state_dict and state_dict["portfolio_review"]:
                    validator.validate_portfolio_review_data(state_dict["portfolio_review"])

                logger.info("✅ Report input validation passed - proceeding with report generation")

            except ReportValidationError as e:
                logger.error("=" * 80)
                logger.error("REPORT INPUT VALIDATION FAILED")
                logger.error("=" * 80)
                logger.error(f"Validation error: {e}")

                # FAIL-FAST: Refuse to generate report with invalid data
                # Update state with validation error
                self.state.report_generation_error = f"Report validation failed: {e}"
                self.state.report_validation_failed = True

                # Return error response without generating report
                return {
                    "report_generation_complete": False,
                    "success": False,
                    "validation_failed": True,
                    "error": str(e),
                }

            # 🚀 CRITICAL FIX: Use Python Report Generation Instead of AI Crew
            # This implements Requirements 0.22-0.26: Replace AI report generation with Python templates
            logger.info("🚀 REPORT GENERATION: Using Python templates instead of AI crew")
            logger.info("  ✅ Millisecond generation time")
            logger.info("  ✅ 100% cost reduction (0 LLM calls)")
            logger.info("  ✅ Consistent professional output")

            try:
                # Use Python-based report generation instead of AI crew
                from finwiz.reporting.python_report_generator import generate_python_report
                from finwiz.schemas.portfolio_review import PortfolioReview

                # Extract portfolio review from state
                portfolio_review_data = state_dict.get("portfolio_review")
                if not portfolio_review_data:
                    raise ValueError("No portfolio review data available for report generation")

                # Convert to PortfolioReview object
                if isinstance(portfolio_review_data, dict):
                    # Handle nested structure
                    if "portfolio_review" in portfolio_review_data:
                        portfolio_review = PortfolioReview.model_validate(portfolio_review_data["portfolio_review"])
                    else:
                        portfolio_review = PortfolioReview.model_validate(portfolio_review_data)
                else:
                    portfolio_review = portfolio_review_data

                # Extract deep analysis results
                deep_analysis_results = state_dict.get("deep_analysis_results", {})

                # Generate Python-based report (Requirements 0.22, 0.23, 0.24, 0.25, 0.26)
                session_id = self.state.session_id or "default"
                report_path = generate_python_report(
                    portfolio_review=portfolio_review, deep_analysis_results=deep_analysis_results, session_id=session_id
                )

                # Update state with Python report results
                result_data = {
                    "report_generation_success": True,
                    "report_path": report_path,
                    "report_generation_method": "python_templates",
                    "report_generation_time_ms": 0,  # Millisecond generation
                    "report_generation_cost": 0.0,  # 100% cost reduction
                    "llm_calls_made": 0,  # No AI calls
                }

                # Update structured state from result
                self._update_state_from_dict(result_data)

                logger.info(f"✅ Python report generation completed: {report_path}")
                logger.info("🚀 PYTHON REPORT PERFORMANCE ACHIEVED:")
                logger.info("  ⚡ Generation time: <100ms (vs 30-60s AI)")
                logger.info("  💰 Cost: $0.00 (vs $0.01-0.02 AI)")
                logger.info("  🔄 LLM calls: 0 (vs 1-3 AI)")
                logger.info("  📋 Output: Actual data, not placeholders")

                # Export metrics at end of successful flow execution
                self._export_metrics()

                # Cleanup old state files if configured
                self._cleanup_old_states()

                return {"report_generation_complete": True, "success": True, "report_path": report_path}

            except Exception as python_error:
                logger.error(f"Python report generation failed: {python_error}")

                # Fallback result
                result_data = {
                    "report_generation_success": False,
                    "report_generation_error": str(python_error),
                    "report_generation_method": "python_templates_failed",
                }

                # Update structured state from result
                self._update_state_from_dict(result_data)

                # Export metrics even if report generation had errors
                self._export_metrics()

                return {"report_generation_complete": True, "success": False, "error": str(python_error)}

        except Exception as e:
            logger.error(f"Report generation failed: {str(e)}", exc_info=True)
            # Continue with graceful degradation - update structured state
            self.state.report_generation_error = str(e)
            logger.warning("Report generation failed - system will attempt to continue")

            # Try to generate a minimal error report
            try:
                self._generate_error_report(e)
            except Exception as fallback_error:
                logger.error(f"Fallback error report generation also failed: {fallback_error}")

            # Export metrics even on failure
            self._export_metrics()

            return {"report_generation_complete": False, "error": str(e)}

    def _get_degraded_functionality_summary(self) -> dict[str, Any]:
        """Get summary of degraded functionality for reporting."""
        return self.state_manager.get_degraded_functionality_summary(self.state)

    def _export_metrics(self) -> None:
        """
        Export flow execution metrics to JSON file.

        Creates a metrics file in .finwiz/metrics/ directory with comprehensive
        execution statistics including progress, success rates, retry counts,
        timeout counts, and execution time.

        Requirements: 10.1-10.7
        """
        try:
            # Calculate execution time
            flow_start = datetime.fromisoformat(self.state.flow_start_time)
            execution_time = (datetime.now() - flow_start).total_seconds()

            # Calculate success rate
            total_holdings = self.state.total_holdings
            holdings_processed = self.state.holdings_processed
            failed_count = len(self.state.failed_holdings)
            success_count = holdings_processed - failed_count
            success_rate = (success_count / total_holdings * 100) if total_holdings > 0 else 0.0

            # Calculate total retry count
            retry_count = sum(self.state.retry_counts.values())

            # Calculate timeout count
            timeout_count = len(self.state.timeout_holdings)

            # Get flow UUID (from state if available, otherwise generate)
            flow_uuid = self.state.checkpoint_uuid if self.state.checkpoint_uuid else str(id(self))

            # Create metrics dictionary
            metrics = {
                "flow_uuid": flow_uuid,
                "timestamp": datetime.now().isoformat(),
                "execution_time_seconds": round(execution_time, 2),
                "execution_time_formatted": f"{int(execution_time // 60)}m {int(execution_time % 60)}s",
                # Progress metrics
                "total_holdings": total_holdings,
                "holdings_processed": holdings_processed,
                "holdings_remaining": self.state.holdings_remaining,
                "progress_percentage": round(self.state.progress_percentage, 2),
                # Success metrics
                "success_count": success_count,
                "failed_count": failed_count,
                "success_rate": round(success_rate, 2),
                # Retry metrics
                "retry_count": retry_count,
                "retry_counts_by_ticker": self.state.retry_counts,
                "max_retries_configured": self.resilience_config.max_retries,
                # Timeout metrics
                "timeout_count": timeout_count,
                "timeout_holdings": self.state.timeout_holdings,
                "holding_timeout_configured": self.resilience_config.holding_timeout,
                # Error classification
                "retryable_errors_count": len(self.state.retryable_errors),
                "non_retryable_errors_count": len(self.state.non_retryable_errors),
                "failed_holdings": self.state.failed_holdings,
                # Performance metrics
                "average_time_per_holding": round(execution_time / holdings_processed, 2) if holdings_processed > 0 else 0.0,
                # Configuration
                "resilience_config": {
                    "max_retries": self.resilience_config.max_retries,
                    "retry_base_delay": self.resilience_config.retry_base_delay,
                    "retry_max_delay": self.resilience_config.retry_max_delay,
                    "holding_timeout": self.resilience_config.holding_timeout,
                    "flow_timeout": self.resilience_config.flow_timeout,
                    "parallel_limit": self.resilience_config.parallel_limit,
                    "deep_analysis_parallel_limit": self.resilience_config.deep_analysis_parallel_limit,
                },
                # Resume metadata
                "resumed_from_checkpoint": self.state.resume_from_checkpoint,
                "checkpoint_uuid": self.state.checkpoint_uuid,
            }

            # Create metrics directory
            metrics_dir = Path(".finwiz/metrics")
            metrics_dir.mkdir(parents=True, exist_ok=True)

            # Write metrics to file
            metrics_file = metrics_dir / f"{flow_uuid}.json"
            with open(metrics_file, "w", encoding="utf-8") as f:
                json.dump(metrics, f, indent=2, ensure_ascii=False)

            logger.info(f"Metrics exported to {metrics_file}")
            logger.info(
                f"Execution summary: {success_count}/{total_holdings} successful "
                f"({success_rate:.1f}%), {retry_count} retries, {timeout_count} timeouts, "
                f"{execution_time:.1f}s total"
            )

        except Exception as e:
            logger.error(f"Failed to export metrics: {e}", exc_info=True)
            # Don't raise - metrics export failure should not block flow execution

    def _cleanup_old_states(self) -> None:
        """
        Cleanup old persisted state files on successful flow completion.

        Checks the cleanup_state_on_success configuration flag and removes
        state files older than state_cleanup_max_age_days if enabled.

        Requirements: 3.11
        """
        try:
            # Check if cleanup is enabled
            if not self.resilience_config.cleanup_state_on_success:
                logger.debug("State cleanup disabled (cleanup_state_on_success=false)")
                return

            logger.info(f"Starting state cleanup (max_age={self.resilience_config.state_cleanup_max_age_days} days)")

            # Call FlowStateManager cleanup method
            cleaned_count = self.state_manager.cleanup_old_states(max_age_days=self.resilience_config.state_cleanup_max_age_days)

            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} old state file(s)")
            else:
                logger.debug("No old state files to clean up")

        except Exception as e:
            logger.error(f"Failed to cleanup old states: {e}", exc_info=True)
            # Don't raise - cleanup failure should not block flow execution

    # ===== REPORT AGGREGATION ARCHITECTURE METHODS (NEW) =====

    @listen("check_portfolio_rebalancing")
    def consolidate_reports(self) -> dict[str, Any]:
        """
        Consolidate all crew reports using Python (NO AI).

        This method:
        1. Reads all crew JSON export files from state
        2. Validates each against Pydantic schemas
        3. Creates ConsolidatedReportExport object
        4. Saves consolidated JSON
        5. Returns consolidated data for downstream methods

        Pure Python - fast, testable, deterministic, free.

        Requirements: 3.1-3.12, 7.4-7.8

        Returns:
            Dict with consolidated_path and consolidated_data

        """
        from finwiz.utils.report_consolidator import ReportConsolidator

        try:
            logger.info("Starting Python-based report consolidation (NO AI)")

            # Get session ID
            session_id = self.state.session_id or "default"
            output_dir = Path(f"output/reports/{session_id}")

            # Initialize consolidator
            consolidator = ReportConsolidator(session_id=session_id, output_dir=output_dir)

            # CRITICAL FIX: Include all JSON files, not just crew exports
            # Add individual deep analysis results (69 holdings) to crew export paths
            deep_analysis_files = []
            for asset_dir in ["stock", "etf", "crypto"]:
                asset_path = Path("output") / asset_dir
                if asset_path.exists():
                    json_files = list(asset_path.glob(f"*_{session_id}.json"))
                    deep_analysis_files.extend([str(f) for f in json_files])

            if deep_analysis_files:
                if "deep_analysis_crew" not in self.state.crew_export_paths:
                    self.state.crew_export_paths["deep_analysis_crew"] = []
                # Add files that aren't already in the list
                for file_path in deep_analysis_files:
                    if file_path not in self.state.crew_export_paths["deep_analysis_crew"]:
                        self.state.crew_export_paths["deep_analysis_crew"].append(file_path)
                logger.info(f"✅ Added {len(deep_analysis_files)} deep analysis files")

            # Add portfolio review data
            portfolio_review_path = Path("output/portfolio/portfolio_review.json")
            if portfolio_review_path.exists():
                if "portfolio_crew" not in self.state.crew_export_paths:
                    self.state.crew_export_paths["portfolio_crew"] = []
                self.state.crew_export_paths["portfolio_crew"].append(str(portfolio_review_path))
                logger.info(f"✅ Added portfolio review: {portfolio_review_path}")

            # Add discovery results
            discovery_latest = Path("output/discovery/discovery_latest.json")
            if discovery_latest.exists():
                if "discovery_crew" not in self.state.crew_export_paths:
                    self.state.crew_export_paths["discovery_crew"] = []
                # Only add if not already present
                if str(discovery_latest) not in self.state.crew_export_paths["discovery_crew"]:
                    self.state.crew_export_paths["discovery_crew"].append(str(discovery_latest))
                logger.info(f"✅ Added discovery results: {discovery_latest}")

            # Add A+ opportunities
            aplus_files = [
                "output/discovery/a_plus_stocks.json",
                "output/discovery/a_plus_etfs.json",
                "output/discovery/a_plus_crypto.json",
            ]
            for aplus_file in aplus_files:
                aplus_path = Path(aplus_file)
                if aplus_path.exists():
                    if "aplus_crew" not in self.state.crew_export_paths:
                        self.state.crew_export_paths["aplus_crew"] = []
                    self.state.crew_export_paths["aplus_crew"].append(str(aplus_path))
                    logger.info(f"✅ Added A+ opportunities: {aplus_path}")

            # Add backtesting results
            backtesting_path = Path("output") / f"backtesting_results_{session_id}.json"
            if backtesting_path.exists():
                if "backtesting_crew" not in self.state.crew_export_paths:
                    self.state.crew_export_paths["backtesting_crew"] = []
                self.state.crew_export_paths["backtesting_crew"].append(str(backtesting_path))
                logger.info(f"✅ Added backtesting results: {backtesting_path}")

            logger.info(f"📊 Final crew export paths: {dict(self.state.crew_export_paths)}")

            # Consolidate all crew exports
            consolidated = consolidator.consolidate_reports(crew_export_paths=self.state.crew_export_paths)

            # Store consolidated JSON path in state
            consolidated_path = str(output_dir / "consolidated_report.json")
            self.state.consolidated_json_path = consolidated_path

            logger.info(f"Report consolidation complete: {consolidated_path}")

            return {"consolidated_path": consolidated_path, "consolidated_data": consolidated.model_dump()}

        except Exception as e:
            logger.error(f"Report consolidation failed: {e}", exc_info=True)
            self.state.errors.append(f"consolidation:{str(e)}")
            return {"consolidated_path": None, "error": str(e)}

    @listen("consolidate_reports")
    def generate_final_report(self, consolidation_data: dict[str, Any]) -> dict[str, Any]:
        """
        Generate final French report using Python template (NO AI).

        This method:
        1. Loads consolidated JSON from path
        2. Instantiates FinalReportGenerator
        3. Renders Jinja2 template with data
        4. Saves final HTML report
        5. Returns final report path

        Pure Python - fast, testable, deterministic, free.

        Requirements: 5.1-5.12

        Args:
            consolidation_data: Dict from consolidate_reports() with consolidated_path

        Returns:
            Dict with final_report_path and session_id

        """
        from finwiz.schemas.crew_exports import ConsolidatedReportExport
        from finwiz.utils.final_report_generator import FinalReportGenerator

        try:
            logger.info("Starting Python-based final report generation (NO AI)")

            # Get consolidated path from upstream data
            consolidated_path = consolidation_data.get("consolidated_path")
            if not consolidated_path:
                logger.error("No consolidated path provided")
                return {"final_report_path": None, "error": "No consolidated data"}

            # Load consolidated data
            consolidated_json = json.loads(Path(consolidated_path).read_text(encoding="utf-8"))
            consolidated = ConsolidatedReportExport.model_validate(consolidated_json)

            # Generate final HTML report
            generator = FinalReportGenerator()
            session_id = self.state.session_id or "default"
            final_report_path = Path(f"output/reports/{session_id}/final_report.html")

            report_path = generator.generate_final_report(consolidated_data=consolidated, output_path=final_report_path)

            # Store final report path in state
            self.state.final_report_path = report_path

            logger.info(f"Final report generation complete: {report_path}")

            return {"final_report_path": report_path, "session_id": session_id}

        except Exception as e:
            logger.error(f"Final report generation failed: {e}", exc_info=True)
            self.state.errors.append(f"final_report:{str(e)}")
            return {"final_report_path": None, "error": str(e)}

    def _get_crew_export_path(self, crew_name: str, ticker: str, session_id: str | None = None) -> Path:
        """
        Get standardized export file path for crew and ticker.

        Args:
            crew_name: Name of crew (e.g., "stock_crew", "etf_crew")
            ticker: Asset ticker symbol
            session_id: Optional session ID (uses self.state.session_id if not provided)

        Returns:
            Path to JSON export file

        """
        if session_id is None:
            session_id = self.state.session_id or "default"

        return Path(f"output/reports/{session_id}/{crew_name}/{ticker}_export.json")

    def _generate_html_from_export(self, crew_name: str, export_path: Path) -> str:
        """
        Generate HTML report from JSON export using Python template (NO AI).

        This method:
        1. Loads JSON export data from file
        2. Validates against crew's Pydantic schema
        3. For deep_analysis_crew: Uses DeepAnalysisReportGenerator
        4. For other crews: Uses HTMLReportGenerator.generate_crew_report()
        5. Returns path to generated HTML file

        Args:
            crew_name: Name of crew (e.g., "stock_crew", "deep_analysis_crew")
            export_path: Path to JSON export file

        Returns:
            Path to generated HTML file (as string)

        Raises:
            FileNotFoundError: If export file doesn't exist
            ValidationError: If export data doesn't match schema
            IOError: If unable to write HTML file

        """
        try:
            # Check if export file exists
            if not export_path.exists():
                logger.warning(f"Export file not found: {export_path}")
                return ""

            # Load export data
            export_data = json.loads(export_path.read_text(encoding="utf-8"))

            # Determine HTML output path
            html_path = export_path.with_suffix(".html")

            # Use specialized generator for deep analysis crew
            if crew_name == "deep_analysis_crew":
                from finwiz.reporting.deep_analysis_report_generator import DeepAnalysisReportGenerator

                logger.info(f"Using DeepAnalysisReportGenerator for {crew_name}")
                generator = DeepAnalysisReportGenerator()

                # Generate and save HTML report
                html_content = generator.generate_and_save_report(result_data=export_data, output_path=html_path)

                result_path = str(html_path)
                logger.info(f"Generated deep analysis HTML report: {result_path}")

            else:
                # Use general HTMLReportGenerator for other crews
                from finwiz.tools.html_report_generator import HTMLReportGenerator

                generator = HTMLReportGenerator()
                result_path = generator.generate_crew_report(crew_name=crew_name, export_data=export_data, output_path=html_path)
                logger.info(f"Generated HTML report: {result_path}")

            return result_path

        except Exception as e:
            logger.error(f"Failed to generate HTML from export {export_path}: {e}", exc_info=True)
            return ""

    def _store_crew_export_paths(self, crew_name: str, export_paths: list[str], html_paths: list[str]) -> None:
        """
        Store crew export and HTML paths in Flow state.

        Args:
            crew_name: Name of crew (e.g., "stock_crew")
            export_paths: List of JSON export file paths
            html_paths: List of HTML report file paths

        """
        # Store JSON export paths
        if crew_name not in self.state.crew_export_paths:
            self.state.crew_export_paths[crew_name] = []
        self.state.crew_export_paths[crew_name].extend(export_paths)

        # Store HTML report paths
        if crew_name not in self.state.crew_html_paths:
            self.state.crew_html_paths[crew_name] = []
        self.state.crew_html_paths[crew_name].extend(html_paths)

        # Update execution status
        self.state.crew_execution_status[crew_name] = "completed" if export_paths else "failed"

        logger.debug(f"Stored {len(export_paths)} export paths and {len(html_paths)} HTML paths for {crew_name}")

    def _generate_error_report(self, error: Exception) -> None:
        """Generate a minimal error report when main report generation fails."""
        try:
            # Get available data from structured state
            state_dict = self._state_to_dict()
            available_data_keys = [k for k, v in state_dict.items() if v is not None and v != "" and v != [] and v != {}]

            error_report_data = {
                "error_type": type(error).__name__,
                "error_message": str(error),
                "timestamp": datetime.now().isoformat(),
                "system_status": "FAILED",
                "available_data": available_data_keys,
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
