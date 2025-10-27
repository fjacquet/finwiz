"""
Flow State Management for FinWiz Application.

This module contains state management classes and utilities for the CrewAI flow,
including state containers and state-related helper methods.
"""

import os
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

# Import ValidationError for error tracking
try:
    from finwiz.validation.result import ValidationError
except ImportError:
    # Fallback if validation module not available
    ValidationError = None  # type: ignore


class DeepAnalysisResult(BaseModel):
    """Result from deep crew analysis of a portfolio holding."""

    ticker: str = Field(..., description="Stock/ETF/crypto ticker symbol")
    asset_class: str = Field(..., description="Asset class (stock, etf, crypto)")
    crew_name: str = Field(..., description="Name of crew that performed analysis")
    analysis_timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(), description="When analysis was performed (ISO format)"
    )
    composite_score: float = Field(..., ge=0.0, le=1.0, description="Composite score (0.0-1.0)")
    grade: str = Field(..., description="Letter grade (A+ to F)")

    # Investment recommendation
    recommendation: str = Field(..., description="Investment recommendation (BUY, HOLD, SELL)")
    rationale: str = Field(..., description="Detailed rationale for the recommendation")
    risk_details: dict[str, float] = Field(default_factory=dict, description="Risk factor breakdown")

    # Individual scores (optional)
    fundamental_score: float | None = Field(None, ge=0.0, le=1.0, description="Fundamental analysis score")
    technical_score: float | None = Field(None, ge=0.0, le=1.0, description="Technical analysis score")
    risk_score: float | None = Field(None, ge=0.0, le=5.0, description="Risk score (0-5 scale)")

    # Data quality and freshness
    data_freshness_hours: float = Field(..., ge=0.0, description="Age of market data in hours")
    confidence_level: float = Field(..., ge=0.0, le=1.0, description="Confidence level in analysis (0.0-1.0)")
    warnings: list[str] = Field(default_factory=list, description="List of analysis warnings")

    # Cache metadata
    cached: bool = Field(default=False, description="Whether result came from cache")

    model_config = {"extra": "forbid", "str_strip_whitespace": True, "ser_json_timedelta": "iso8601", "ser_json_bytes": "base64"}


class FinwizState(BaseModel):
    """
    Comprehensive structured state for the FinWiz analysis flow using Pydantic for type safety.

    This replaces ALL previous usage of self.inputs dictionary with structured, type-safe fields.
    NO backward compatibility with self.inputs - complete migration.
    """

    # Session metadata (from create_flow_inputs)
    current_day: int = Field(default_factory=lambda: datetime.now().day)
    current_month: int = Field(default_factory=lambda: datetime.now().month)
    current_year: int = Field(default_factory=lambda: datetime.now().year)
    current_date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    full_date: str = Field(default_factory=lambda: datetime.now().strftime("%B %d, %Y"))
    timestamp: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    report_language: str = Field(default="fr", description="Report language (default: French)")

    # Session information
    has_existing_session: bool = Field(default=False, description="Whether an existing session is available")
    session_id: str = Field(default="", description="Session ID if available")
    analysis_count: int = Field(default=0, description="Number of analyses in current session")

    # Core analysis results (from check_stock, check_etf, check_crypto)
    stock_result: str = Field(default="", description="Stock crew analysis result")
    etf_result: str = Field(default="", description="ETF crew analysis result")
    crypto_result: str = Field(default="", description="Crypto crew analysis result")

    # Core analysis status and errors
    stock_analysis_success: bool = Field(default=False)
    stock_analysis_error: str | None = None
    stock_analysis_disabled: bool = Field(default=False)
    stock_analysis_fallback: bool = Field(default=False)
    stock_analysis_result: dict[str, Any] | None = None

    etf_analysis_success: bool = Field(default=False)
    etf_analysis_error: str | None = None
    etf_analysis_disabled: bool = Field(default=False)
    etf_analysis_fallback: bool = Field(default=False)
    etf_analysis_result: dict[str, Any] | None = None

    crypto_analysis_success: bool = Field(default=False)
    crypto_analysis_error: str | None = None
    crypto_analysis_disabled: bool = Field(default=False)
    crypto_analysis_fallback: bool = Field(default=False)
    crypto_analysis_result: dict[str, Any] | None = None

    # Data integration and validation (from validate_data_integration)
    data_availability_report: dict[str, Any] | None = Field(None, description="Data availability status report")
    stale_data_warnings: list[str] = Field(default_factory=list, description="Warnings about stale data")
    refresh_recommendations: list[str] = Field(default_factory=list, description="Recommended refresh order")
    data_integration_error: str | None = Field(None, description="Data integration error if any")

    # Portfolio review data (from check_portfolio)
    portfolio_review: dict[str, Any] | None = Field(None, description="Portfolio review data")
    portfolio_review_json: str | None = Field(None, description="Path to portfolio review JSON file")
    portfolio_review_error: str | None = Field(None, description="Portfolio review error if any")
    core_analysis_status: dict[str, Any] | None = Field(None, description="Core analysis availability status")

    # Portfolio rebalancing data (from check_portfolio_rebalancing)
    portfolio_rebalancing_available: bool = Field(default=False, description="Whether rebalancing analysis is available")
    portfolio_rebalancing_result: dict[str, Any] | None = Field(None, description="Portfolio rebalancing result")
    portfolio_rebalancing_error: str | None = Field(None, description="Portfolio rebalancing error if any")
    portfolio_allocation_updates: dict[str, Any] | None = Field(None, description="Portfolio allocation updates")

    # Investment discovery data (from check_investment_discovery)
    investment_discovery_available: bool = Field(default=False, description="Whether discovery analysis is available")
    investment_discovery_result: str | None = Field(None, description="Investment discovery crew result text")
    investment_discovery_structured: dict[str, Any] | None = Field(None, description="Structured A+ opportunities")
    investment_discovery_error: str | None = Field(None, description="Investment discovery error if any")

    # Consolidated data and integration (from pre_validate_reporter_input)
    consolidated_data: dict[str, Any] | None = Field(None, description="Consolidated data from all crews")
    core_analysis_summary: dict[str, Any] | None = Field(None, description="Summary of core analysis results")
    integrated_data_available: bool = Field(default=False, description="Whether integrated data is available")
    integrated_data_error: str | None = Field(None, description="Integrated data error if any")
    market_sentiment: dict[str, Any] | None = Field(None, description="Market sentiment data")
    ticker_validation: dict[str, Any] | None = Field(None, description="Ticker validation data")
    aplus_opportunities: dict[str, Any] | None = Field(None, description="A+ opportunities data")
    aplus_availability_status: dict[str, Any] | None = Field(None, description="A+ availability status")
    market_context: dict[str, Any] | None = Field(None, description="Market context data (VIX, inflation, rates, regime)")

    # System health and error tracking
    error_summaries: list[dict[str, Any]] = Field(default_factory=list, description="Error summaries from all crews")
    system_health: dict[str, Any] | None = Field(None, description="Overall system health status")
    system_status_for_report: dict[str, Any] | None = Field(None, description="System status for report generation")

    # Reporter input validation (from pre_validate_reporter_input)
    reporter_input: dict[str, Any] | None = Field(None, description="Validated input for reporter crew")
    report_generation_error: str | None = Field(None, description="Report generation error if any")

    # Degraded functionality tracking
    stock_degraded_functionality: list[str] = Field(default_factory=list)
    etf_degraded_functionality: list[str] = Field(default_factory=list)
    crypto_degraded_functionality: list[str] = Field(default_factory=list)
    stock_fallback_strategy: str | None = None
    etf_fallback_strategy: str | None = None
    crypto_fallback_strategy: str | None = None

    # Deep portfolio analysis results (NEW - from analyze_holdings_deep)
    deep_analysis_results: dict[str, DeepAnalysisResult] = Field(
        default_factory=dict, description="Deep analysis results keyed by ticker"
    )
    deep_analysis_success: bool = Field(default=False, description="Whether deep analysis completed successfully")
    deep_analysis_count: int = Field(default=0, description="Number of holdings analyzed deeply")
    deep_analysis_error: str | None = Field(None, description="Error message if deep analysis failed")

    # Alternative matching results (NEW - from match_alternatives)
    portfolio_alternatives: dict[str, list[dict[str, Any]]] = Field(
        default_factory=dict, description="A+ alternatives keyed by ticker"
    )
    alternatives_success: bool = Field(default=False, description="Whether alternative matching completed successfully")
    alternatives_count: int = Field(default=0, description="Number of alternatives found")
    alternatives_error: str | None = Field(None, description="Error message if alternative matching failed")

    # Data availability tracking (NEW - for reporter transparency)
    data_availability_summary: dict[str, Any] | None = Field(None, description="Summary of data source availability and freshness")
    data_availability_summary_formatted: str | None = Field(
        None, description="Formatted data availability summary for report display"
    )

    # ===== REPORT AGGREGATION ARCHITECTURE FIELDS (NEW) =====

    # Crew export paths (JSON files)
    crew_export_paths: dict[str, list[str]] = Field(
        default_factory=dict,
        description="JSON export file paths keyed by crew name (e.g., {'stock_crew': ['path/to/AAPL_export.json']})",
    )

    # Crew HTML report paths
    crew_html_paths: dict[str, list[str]] = Field(
        default_factory=dict,
        description="HTML report file paths keyed by crew name (e.g., {'stock_crew': ['path/to/AAPL_report.html']})",
    )

    # Consolidation results
    consolidated_json_path: str | None = Field(None, description="Path to consolidated JSON report aggregating all crew exports")

    # Final report path
    final_report_path: str | None = Field(None, description="Path to final French HTML report generated from consolidated data")

    # Crew execution status tracking (for error handling)
    crew_execution_status: dict[str, str] = Field(
        default_factory=dict, description="Execution status for each crew (completed/failed/pending)"
    )

    # Crew execution errors
    crew_execution_errors: dict[str, str] = Field(
        default_factory=dict, description="Error messages for failed crews keyed by crew name"
    )

    # ===== RESILIENCE TRACKING FIELDS (NEW) =====

    # Progress tracking
    total_holdings: int = Field(default=0, description="Total number of holdings to analyze")
    holdings_processed: int = Field(default=0, description="Number of holdings processed so far")
    holdings_remaining: int = Field(default=0, description="Number of holdings remaining to process")
    current_ticker: str = Field(default="", description="Currently processing ticker")
    progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0, description="Overall progress percentage")

    # Timing fields (stored as ISO format strings for JSON serialization compatibility)
    flow_start_time: str = Field(
        default_factory=lambda: datetime.now().isoformat(), description="When the flow execution started (ISO format)"
    )
    last_checkpoint_time: str | None = Field(None, description="Last checkpoint timestamp (ISO format)")
    estimated_time_remaining: float = Field(default=0.0, ge=0.0, description="Estimated seconds remaining")

    # Error tracking
    failed_holdings: list[str] = Field(default_factory=list, description="List of tickers that failed analysis")
    retry_counts: dict[str, int] = Field(default_factory=dict, description="Retry count per ticker")
    timeout_holdings: list[str] = Field(default_factory=list, description="List of tickers that timed out")

    # Error classification (using ValidationError if available)
    retryable_errors: list[Any] = Field(default_factory=list, description="List of retryable ValidationError objects")
    non_retryable_errors: list[Any] = Field(default_factory=list, description="List of non-retryable ValidationError objects")

    # Resume metadata
    resume_from_checkpoint: bool = Field(default=False, description="Whether this is a resumed execution")
    checkpoint_uuid: str | None = Field(None, description="UUID of checkpoint being resumed from")

    # ===== BATCH PRE-FETCH FIELDS (NEW - Task 4.1) =====

    # Batch pre-fetch configuration
    batch_prefetch_enabled: bool = Field(default=False, description="Whether batch data pre-fetching is enabled for deep analysis")

    # Pre-fetched data cache
    prefetched_data: dict[str, dict[str, Any]] | None = Field(
        None, description="Pre-fetched data for all tickers (keyed by ticker symbol)"
    )

    # Batch pre-fetch performance metrics
    batch_prefetch_metrics: dict[str, Any] | None = Field(None, description="Performance metrics for batch pre-fetch operation")

    model_config = {
        "extra": "allow",  # Allow CrewAI Flow to add internal fields (StateWithId wrapper)
        "ser_json_timedelta": "iso8601",
        "ser_json_bytes": "base64",
    }


class FlowStateManager:
    """Manages flow state and provides state-related utilities."""

    def __init__(self) -> None:
        """Initialize the FlowStateManager."""
        self.logger = get_logger(__name__)

    def create_initial_state(self) -> FinwizState:
        """
        Create initial FinwizState with session information from environment.

        Returns:
            FinwizState: Initialized state with session metadata

        """
        # Get session information from environment
        has_existing_session = os.getenv("FINWIZ_HAS_EXISTING_SESSION", "false") == "true"
        session_id = os.getenv("FINWIZ_SESSION_ID", "")
        analysis_count = int(os.getenv("FINWIZ_ANALYSIS_COUNT", "0"))

        # Create state with session information
        state = FinwizState(has_existing_session=has_existing_session, session_id=session_id, analysis_count=analysis_count)

        self.logger.debug(f"Flow state initialized with timestamp: {state.timestamp}")

        if state.has_existing_session:
            self.logger.debug(f"Flow initialized with existing session: {state.session_id}")
        else:
            self.logger.debug("Flow initialized without existing session")

        return state

    def check_core_analysis_availability(self, state: FinwizState) -> dict[str, Any]:
        """Check which core analysis crews are available and their status."""
        # Import here to avoid circular imports
        from .integration.manager import CrewDataIntegrationManager

        # Create integration manager to check actual data availability
        integration_manager = CrewDataIntegrationManager()

        # Check actual data availability in the integration system
        stock_available = False
        etf_available = False
        crypto_available = False

        try:
            # Check if data actually exists in the integration system
            stock_data = integration_manager.get_crew_data_with_freshness_check("stock", max_age_hours=24, warn_on_stale=False)
            stock_available = stock_data is not None

            etf_data = integration_manager.get_crew_data_with_freshness_check("etf", max_age_hours=24, warn_on_stale=False)
            etf_available = etf_data is not None

            crypto_data = integration_manager.get_crew_data_with_freshness_check("crypto", max_age_hours=24, warn_on_stale=False)
            crypto_available = crypto_data is not None

        except Exception as e:
            # Fallback to state flags if integration system check fails
            self.logger.warning(f"Failed to check actual data availability, falling back to state flags: {e}")
            stock_available = state.stock_analysis_success or (
                state.stock_analysis_fallback and state.stock_analysis_result is not None
            )
            etf_available = state.etf_analysis_success or (state.etf_analysis_fallback and state.etf_analysis_result is not None)
            crypto_available = state.crypto_analysis_success or (
                state.crypto_analysis_fallback and state.crypto_analysis_result is not None
            )

        available_crews = []
        if stock_available:
            available_crews.append("stock")
        if etf_available:
            available_crews.append("etf")
        if crypto_available:
            available_crews.append("crypto")

        # Check for failed crews based on state flags (these are still relevant)
        failed_crews = []
        if state.stock_analysis_error:
            failed_crews.append("stock")
        if state.etf_analysis_error:
            failed_crews.append("etf")
        if state.crypto_analysis_error:
            failed_crews.append("crypto")

        # Check for disabled crews based on state flags
        disabled_crews = []
        if state.stock_analysis_disabled:
            disabled_crews.append("stock")
        if state.etf_analysis_disabled:
            disabled_crews.append("etf")
        if state.crypto_analysis_disabled:
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

    def extract_market_conditions(self, state: FinwizState) -> dict[str, Any]:
        """Extract market conditions from core analysis results."""
        conditions = {}

        if state.stock_analysis_result:
            # Extract market sentiment and trends from stock analysis
            conditions["stock_market_sentiment"] = "Available from stock analysis"

        if state.etf_analysis_result:
            # Extract sector trends from ETF analysis
            conditions["sector_trends"] = "Available from ETF analysis"

        if state.crypto_analysis_result:
            # Extract crypto market dynamics
            conditions["crypto_market_dynamics"] = "Available from crypto analysis"

        return conditions

    def extract_market_context_from_core_analysis(self, core_analysis_data: dict[str, Any]) -> dict[str, Any]:
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

            self.logger.debug(f"Extracted market context from {len(core_analysis_data)} core analysis results")
            return market_context

        except Exception as e:
            self.logger.warning(f"Failed to extract market context from core analysis: {e}")
            return market_context

    def prepare_core_analysis_summary(self, consolidated_data: dict[str, Any]) -> dict[str, Any]:
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
            crew_data_dict = consolidated_data.get("consolidated_crew_data", consolidated_data)
            for crew_type in ["stock", "etf", "crypto"]:
                if crew_type in crew_data_dict:
                    summary["available_analyses"].append(crew_type)
                    crew_data = crew_data_dict[crew_type]

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
            crew_data_dict = consolidated_data.get("consolidated_crew_data", consolidated_data)
            for crew_type in ["stock", "etf", "crypto"]:
                if crew_type in crew_data_dict:
                    crew_data = crew_data_dict[crew_type]
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

            self.logger.debug(f"Prepared core analysis summary with {len(summary['available_analyses'])} analyses")
            return summary

        except Exception as e:
            self.logger.warning(f"Failed to prepare core analysis summary: {e}")
            return summary

    def get_degraded_functionality_summary(self, state: FinwizState) -> dict[str, Any]:
        """Get summary of degraded functionality across the system."""
        degraded_summary = {
            "has_degraded_functionality": False,
            "degraded_crews": [],
            "fallback_strategies_used": [],
            "missing_features": [],
            "data_quality_issues": [],
        }

        # Check for crew-specific degraded functionality
        degraded_funcs = {
            "stock": state.stock_degraded_functionality,
            "etf": state.etf_degraded_functionality,
            "crypto": state.crypto_degraded_functionality,
        }

        for crew_name, degraded_functionality in degraded_funcs.items():
            if degraded_functionality:
                degraded_summary["has_degraded_functionality"] = True
                degraded_summary["degraded_crews"].append(crew_name)
                degraded_summary["missing_features"].extend(degraded_functionality)

        fallback_strategies = {
            "stock": state.stock_fallback_strategy,
            "etf": state.etf_fallback_strategy,
            "crypto": state.crypto_fallback_strategy,
        }

        for crew_name, fallback_strategy in fallback_strategies.items():
            if fallback_strategy:
                degraded_summary["fallback_strategies_used"].append(f"{crew_name}: {fallback_strategy}")

        # Check for data quality issues
        if state.stale_data_warnings:
            degraded_summary["data_quality_issues"].append("stale_data")

        if state.integrated_data_error:
            degraded_summary["data_quality_issues"].append("integration_error")

        return degraded_summary
