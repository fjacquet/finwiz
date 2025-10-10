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
from finwiz.integration.data_availability_tracker import DataAvailabilityTracker
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

        # Initialize structured state (replaces self.inputs)
        # Note: self.state is automatically managed by Flow[FinwizState]
        # We just need to ensure it's initialized with session data
        if not hasattr(self, "state") or self.state is None:
            self.state = self.state_manager.create_initial_state()
            logger.info("Flow state initialized with session metadata")
        else:
            logger.info("Flow state already initialized by Flow framework")

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

    @listen("validate_data_integration")
    def check_crypto(self) -> dict[str, Any]:
        """Initiate the cryptocurrency analysis crew after data validation."""
        result_data = self.crew_factory.execute_crypto_crew(self._state_to_dict())
        self._update_state_from_dict(result_data)

        # Track crew execution for data availability
        if result_data.get("crypto_analysis_success"):
            self.availability_tracker.track_data_source(
                source="crypto_crew", status="available", last_updated=datetime.now(), record_count=1
            )
        else:
            error_msg = result_data.get("crypto_analysis_error", "Crypto analysis failed")
            self.availability_tracker.track_data_source(source="crypto_crew", status="unavailable", error_message=error_msg)

        return {"crypto_analysis_complete": True, "crypto_result": result_data.get("crypto_result", "")}

    @listen("validate_data_integration")
    def check_stock(self) -> dict[str, Any]:
        """Initiate the stock analysis crew after data validation."""
        result_data = self.crew_factory.execute_stock_crew(self._state_to_dict())
        self._update_state_from_dict(result_data)

        # Track crew execution for data availability
        if result_data.get("stock_analysis_success"):
            self.availability_tracker.track_data_source(
                source="stock_crew", status="available", last_updated=datetime.now(), record_count=1
            )
        else:
            error_msg = result_data.get("stock_analysis_error", "Stock analysis failed")
            self.availability_tracker.track_data_source(source="stock_crew", status="unavailable", error_message=error_msg)

        return {"stock_analysis_complete": True, "stock_result": result_data.get("stock_result", "")}

    @listen("validate_data_integration")
    def check_etf(self) -> dict[str, Any]:
        """Initiate the ETF analysis crew after data validation."""
        result_data = self.crew_factory.execute_etf_crew(self._state_to_dict())
        self._update_state_from_dict(result_data)

        # Track crew execution for data availability
        if result_data.get("etf_analysis_success"):
            self.availability_tracker.track_data_source(
                source="etf_crew", status="available", last_updated=datetime.now(), record_count=1
            )
        else:
            error_msg = result_data.get("etf_analysis_error", "ETF analysis failed")
            self.availability_tracker.track_data_source(source="etf_crew", status="unavailable", error_message=error_msg)

        return {"etf_analysis_complete": True, "etf_result": result_data.get("etf_result", "")}

    @start()
    def validate_data_integration(self) -> dict[str, Any]:
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

    @listen("check_portfolio")
    def analyze_holdings_deep(self) -> dict[str, Any]:
        """
        Perform deep crew analysis on portfolio holdings.

        CrewAI Flow Integration:
        - Triggered after portfolio review completes
        - Checks DEEP_PORTFOLIO_ANALYSIS environment variable
        - Uses direct crew instantiation and crew.kickoff()
        - Updates structured Flow state (self.state)
        - Returns analysis results for downstream listeners

        Returns:
            dict: Analysis results passed to downstream @listen() methods
        """
        # Check if deep analysis is enabled
        enabled = (os.getenv("DEEP_PORTFOLIO_ANALYSIS") or "false").strip().lower() in {"1", "true", "yes", "on"}
        if not enabled:
            logger.info("Deep portfolio analysis disabled via DEEP_PORTFOLIO_ANALYSIS")
            return {}  # Return empty dict for downstream listeners

        try:
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

            logger.info(f"Starting deep analysis for {len(holdings)} holdings")

            # Initialize cache manager
            from finwiz.cache.analysis_cache_manager import get_analysis_cache_manager

            cache_ttl_hours = int(os.getenv("PORTFOLIO_CACHE_TTL_HOURS", "24"))
            cache_manager = get_analysis_cache_manager(ttl_hours=cache_ttl_hours)

            # Import crew classes for direct instantiation
            from finwiz.crews.crypto_crew.crypto_crew import CryptoCrew
            from finwiz.crews.etf_crew.etf_crew import EtfCrew
            from finwiz.crews.stock_crew.stock_crew import StockCrew

            # Process each holding
            deep_analysis_results = {}
            processed_count = 0

            for holding in holdings:
                ticker = holding.get("ticker")
                asset_class = holding.get("asset_class")

                if not ticker or not asset_class:
                    logger.warning(f"Skipping holding with missing ticker or asset_class: {holding}")
                    continue

                try:
                    # Check cache first
                    cached_result = cache_manager.get_cached_analysis(ticker, asset_class)
                    if cached_result and cached_result.is_fresh(cache_ttl_hours):
                        logger.info(f"Using cached analysis for {ticker} (age: {cached_result.age_hours:.1f}h)")
                        analysis_result = cached_result.analysis

                        # Create DeepAnalysisResult from cached data
                        from finwiz.flow_state import DeepAnalysisResult

                        deep_result = DeepAnalysisResult(
                            ticker=ticker,
                            asset_class=asset_class,
                            crew_name=analysis_result.crew_name,
                            analyzed_at=analysis_result.analyzed_at,
                            composite_score=analysis_result.composite_score,
                            grade=analysis_result.grade,
                            fundamental_score=analysis_result.fundamental_score,
                            technical_score=analysis_result.technical_score,
                            risk_score=analysis_result.risk_score,
                            cached=True,
                        )
                        deep_analysis_results[ticker] = deep_result

                    else:
                        # Direct crew instantiation and execution (CrewAI Flow pattern)
                        # Crews need full template variables from Flow state
                        crew_inputs = {
                            "ticker": ticker,
                            "current_day": self.state.current_day,
                            "current_month": self.state.current_month,
                            "current_year": self.state.current_year,
                            "current_date": self.state.current_date,
                            "full_date": self.state.full_date,
                            "timestamp": self.state.timestamp,
                            "report_language": self.state.report_language,
                        }

                        if asset_class.lower() == "stock":
                            crew = StockCrew()
                            crew_name = "StockCrew"
                        elif asset_class.lower() == "etf":
                            crew = EtfCrew()
                            crew_name = "EtfCrew"
                        elif asset_class.lower() == "crypto":
                            crew = CryptoCrew()
                            crew_name = "CryptoCrew"
                        else:
                            logger.warning(f"Unknown asset class {asset_class} for {ticker}")
                            continue

                        logger.info(f"Running {crew_name} analysis for {ticker}")
                        result = crew.crew().kickoff(inputs=crew_inputs)

                        # Extract scores and calculate grade (using existing grading system)
                        analysis_result = self._parse_crew_output_for_holding(result, ticker, asset_class, crew_name)

                        # Cache the result
                        cache_manager.cache_analysis(ticker, asset_class, analysis_result)

                        # Create DeepAnalysisResult
                        from finwiz.flow_state import DeepAnalysisResult

                        deep_result = DeepAnalysisResult(
                            ticker=ticker,
                            asset_class=asset_class,
                            crew_name=crew_name,
                            analyzed_at=analysis_result.analyzed_at,
                            composite_score=analysis_result.composite_score,
                            grade=analysis_result.grade,
                            fundamental_score=analysis_result.fundamental_score,
                            technical_score=analysis_result.technical_score,
                            risk_score=analysis_result.risk_score,
                            cached=False,
                        )
                        deep_analysis_results[ticker] = deep_result

                    processed_count += 1
                    logger.info(f"Deep analysis progress: {processed_count}/{len(holdings)} holdings")

                except Exception as e:
                    logger.error(f"Deep analysis failed for {ticker}: {e}", exc_info=True)
                    # Continue with next holding (graceful degradation)
                    continue

            # Update structured Flow state
            self.state.deep_analysis_results = deep_analysis_results
            self.state.deep_analysis_success = True
            self.state.deep_analysis_count = processed_count

            # Log cache statistics
            cache_manager.log_cache_stats()

            logger.info(f"Deep analysis completed for {processed_count} holdings")

            # Return results for downstream Flow listeners
            return {
                "analysis_results": {ticker: result.model_dump(mode='json') for ticker, result in deep_analysis_results.items()},
                "processed_count": processed_count,
                "success": True,
            }

        except Exception as e:
            logger.error(f"Deep portfolio analysis failed: {e}", exc_info=True)
            # Update structured Flow state with error info
            self.state.deep_analysis_error = str(e)
            self.state.deep_analysis_success = False
            self.state.deep_analysis_results = {}

            logger.warning("Deep analysis failed - continuing with shallow validation")

            # Return error info for downstream listeners
            return {"analysis_results": {}, "processed_count": 0, "success": False, "error": str(e)}

    @listen("analyze_holdings_deep")
    def match_alternatives(self, analysis_data: dict[str, Any]) -> dict[str, Any]:
        """
        Match A+ alternatives for underperforming holdings.

        CrewAI Flow Integration:
        - Receives analysis_results from upstream Flow method as parameter
        - Uses existing AlternativeFinder tool
        - Updates structured Flow state (self.state)
        - Returns alternatives data for downstream listeners

        Args:
            analysis_data: Deep analysis results from analyze_holdings_deep()

        Returns:
            dict: Alternatives data passed to downstream @listen() methods
        """
        # Check if alternative matching is enabled
        enabled = (os.getenv("PORTFOLIO_ENABLE_ALTERNATIVES") or "true").strip().lower() in {"1", "true", "yes", "on"}
        if not enabled:
            logger.info("Alternative matching disabled via PORTFOLIO_ENABLE_ALTERNATIVES")
            return {}  # Return empty dict for downstream listeners

        try:
            # Check if deep analysis was successful (from parameter)
            if not analysis_data.get("success", False):
                logger.info("Skipping alternative matching - deep analysis not successful")
                return {}

            # Get deep analysis results from parameter (CrewAI Flow pattern)
            deep_results = analysis_data.get("analysis_results", {})
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
                grade = analysis.get("grade", "D")

                # Only find alternatives for grades C, D, or F
                if grade in ["C", "D", "F"]:
                    try:
                        # Create HoldingProfile for AlternativeFinder
                        holding_profile = HoldingProfile(
                            ticker=ticker,
                            name=analysis.get("name", ticker),
                            asset_class=analysis.get("asset_class", "stock"),
                            grade=grade,
                            composite_score=analysis.get("composite_score", 0.6),
                            risk_score=analysis.get("risk_score", 2.5),
                        )

                        # Find alternatives using existing tool
                        alternatives = alternative_finder.find_alternatives(
                            holding=holding_profile, max_alternatives=max_alternatives
                        )

                        if alternatives:
                            # Convert Alternative objects to dictionaries for storage
                            alternatives_data[ticker] = [alt.model_dump(mode='json') for alt in alternatives]
                            alternatives_count += len(alternatives)
                            logger.info(f"Found {len(alternatives)} alternatives for {ticker} (grade: {grade})")
                        else:
                            logger.info(f"No alternatives found for {ticker} (grade: {grade})")

                    except Exception as e:
                        logger.error(f"Alternative matching failed for {ticker}: {e}")
                        continue
                else:
                    logger.debug(f"Skipping alternative matching for {ticker} (grade: {grade} - B or above)")

            # Update structured Flow state
            self.state.portfolio_alternatives = alternatives_data
            self.state.alternatives_success = True
            self.state.alternatives_count = alternatives_count

            logger.info(f"Alternative matching completed: {alternatives_count} alternatives for {len(alternatives_data)} holdings")

            # Return results for downstream Flow listeners
            return {"alternatives_data": alternatives_data, "alternatives_count": alternatives_count, "success": True}

        except Exception as e:
            logger.error(f"Alternative matching failed: {e}", exc_info=True)
            # Update structured Flow state with error info
            self.state.alternatives_error = str(e)
            self.state.alternatives_success = False
            self.state.portfolio_alternatives = {}

            logger.warning("Alternative matching failed - continuing without alternatives")

            # Return error info for downstream listeners
            return {"alternatives_data": {}, "alternatives_count": 0, "success": False, "error": str(e)}

    @listen("match_alternatives")
    def update_portfolio_review_with_deep_analysis(self, alternatives_data: dict[str, Any]) -> dict[str, Any]:
        """
        Update portfolio review with deep analysis results and alternatives.

        This method re-runs the portfolio review after deep analysis and alternative
        matching are complete, merging the results into the final portfolio review.

        Args:
            alternatives_data: Alternatives data from match_alternatives()

        Returns:
            dict: Portfolio review update status for downstream listeners
        """
        try:
            # Check if deep analysis was performed
            if not self.state.deep_analysis_success:
                logger.info("Skipping portfolio review update - no deep analysis performed")
                return {"portfolio_review_updated": False, "reason": "no_deep_analysis"}

            logger.info("Updating portfolio review with deep analysis results")

            # Re-run portfolio review with Flow state containing deep analysis
            out_path = run_portfolio_review(flow_state=self.state)
            self.state.portfolio_review_json = str(out_path)

            # Reload updated portfolio review
            try:
                with open(out_path, encoding="utf-8") as f:
                    portfolio_data = json.load(f)
                    self.state.portfolio_review = portfolio_data

                logger.info(
                    f"Portfolio review updated with deep analysis: "
                    f"{self.state.deep_analysis_count} holdings analyzed, "
                    f"{self.state.alternatives_count} alternatives found"
                )

                return {
                    "portfolio_review_updated": True,
                    "holdings_analyzed": self.state.deep_analysis_count,
                    "alternatives_found": self.state.alternatives_count,
                }
            except Exception as le:
                logger.warning(f"Failed to reload updated portfolio review: {le}")
                return {"portfolio_review_updated": False, "error": str(le)}

        except Exception as e:
            logger.error(f"Failed to update portfolio review with deep analysis: {e}", exc_info=True)
            logger.warning("Continuing with original portfolio review")
            return {"portfolio_review_updated": False, "error": str(e)}

    @listen(and_("check_stock", "check_etf", "check_crypto"))
    def check_portfolio(self) -> dict[str, Any]:
        """Run portfolio keep-or-sell review orchestrator after core analysis completion (Phase 3: Portfolio Analysis)."""
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

            # Pass Flow state to portfolio review for deep analysis integration
            # Note: Deep analysis will be merged after analyze_holdings_deep() completes
            out_path = run_portfolio_review(flow_state=None)  # Initial run without deep analysis
            self.state.portfolio_review_json = str(out_path)

            # Load content for tool-less reporter consumption and structured state
            try:
                with open(out_path, encoding="utf-8") as f:
                    portfolio_data = json.load(f)
                    self.state.portfolio_review = portfolio_data
            except Exception as le:
                logger.warning(f"Failed to load portfolio review JSON content: {le}")
                # Continue with degraded functionality
                self.state.portfolio_review = {}

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

    @listen(and_("check_stock", "check_etf", "check_crypto"))
    def check_portfolio_rebalancing(self) -> dict[str, Any]:
        """Run portfolio rebalancing analysis after core analysis completion (Phase 3: Portfolio Analysis)."""
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

    @listen(and_("match_alternatives", "check_portfolio_rebalancing"))
    def check_investment_discovery(self) -> dict[str, Any]:
        """Run investment discovery analysis to find A+ grade opportunities."""
        # Check if investment discovery is enabled via feature flag
        if not is_feature_enabled("investment_discovery"):
            logger.info("Investment discovery disabled via feature flag")
            self.state.investment_discovery_available = False
            return {"investment_discovery_enabled": False}

        try:
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

                # Return data for downstream listeners
                return {
                    "investment_discovery_complete": True,
                    "discovery_available": True,
                    "has_a_plus_analysis": self.state.investment_discovery_structured.get("has_a_plus_analysis", False),
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

    @listen("check_investment_discovery")
    def pre_validate_reporter_input(self) -> dict[str, Any]:
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

            # Store consolidated data in structured state
            self.state.consolidated_data = consolidated_data

            # Add integrated data access information to structured state
            self.state.integrated_data_available = len(consolidated_data) > 0
            self.state.market_sentiment = consolidated_data.get("market_sentiment", {})
            self.state.ticker_validation = consolidated_data.get("ticker_validation", {})
            self.state.aplus_opportunities = consolidated_data.get("aplus_opportunities")
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

            # Note: Individual core analysis results are already in consolidated_data
            # which is stored in self.state.consolidated_data
            for crew_type in ["stock", "etf", "crypto"]:
                if crew_type in consolidated_data:
                    logger.info(f"Core analysis data available for {crew_type} in reporter input")
                else:
                    if core_analysis_status[f"{crew_type}_available"]:
                        logger.warning(f"Core analysis data missing for {crew_type} despite being marked available")

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
                    self.state.reporter_input = model.model_dump(mode="json")
                    logger.info("ReporterInput validated using example data")
                else:
                    logger.warning("No example data available for validation")

            # Generate data availability summary for reporter
            availability_summary = self.availability_tracker.get_availability_summary()
            # Use mode='json' to serialize datetime objects to ISO strings for CrewAI compatibility
            self.state.data_availability_summary = availability_summary.model_dump(mode='json')
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

    @listen("pre_validate_reporter_input")
    def report(self) -> dict[str, Any]:
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
            result_data = self.crew_factory.execute_report_crew(self._state_to_dict())

            # Update structured state from result
            self._update_state_from_dict(result_data)

            if result_data.get("report_generation_success"):
                logger.info("Report generation completed successfully with enhanced error handling")
                return {"report_generation_complete": True, "success": True}
            else:
                logger.warning("Report generation completed with errors")
                return {"report_generation_complete": True, "success": False}

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

            return {"report_generation_complete": False, "error": str(e)}

    def _get_degraded_functionality_summary(self) -> dict[str, Any]:
        """Get summary of degraded functionality for reporting."""
        return self.state_manager.get_degraded_functionality_summary(self.state)

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
