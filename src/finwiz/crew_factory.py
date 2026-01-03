"""
Crew Factory for FinWiz Application.

This module provides factory methods for creating and configuring CrewAI crews,
centralizing crew initialization logic and providing consistent error handling.
"""

import json
import os
from datetime import datetime
from typing import Any

from finwiz.config.features.flags import is_feature_enabled
from finwiz.crews.crypto_crew.crypto_crew import CryptoCrew
from finwiz.crews.etf_crew.etf_crew import EtfCrew
from finwiz.crews.investment_discovery_crew.investment_discovery_crew import InvestmentDiscoveryCrew
from finwiz.crews.portfolio_rebalancing_crew.portfolio_rebalancing_crew import PortfolioRebalancingCrew
from finwiz.crews.report_crew.report_crew import ReportCrew
from finwiz.crews.stock_crew.stock_crew import StockCrew
from finwiz.infrastructure.caching.crew_output_cache import get_crew_output_cache
from finwiz.orchestrators.error_handling.core_analysis_error_handler import CoreAnalysisErrorHandler
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class CrewFactory:
    """Factory for creating and managing CrewAI crews."""

    def __init__(self, integration_manager: Any, error_handler: CoreAnalysisErrorHandler) -> None:
        """
        Initialize the CrewFactory.

        Args:
            integration_manager: Data integration manager instance
            error_handler: Core analysis error handler instance

        """
        self.integration_manager = integration_manager
        self.error_handler = error_handler
        self.logger = get_logger(__name__)

        # Initialize crew output cache
        cache_enabled = os.getenv("CREW_CACHE_ENABLED", "true").lower() == "true"
        cache_max_age_hours = int(os.getenv("CREW_CACHE_MAX_AGE_HOURS", "24"))

        self.cache_enabled = cache_enabled
        self.output_cache = get_crew_output_cache(max_age_hours=cache_max_age_hours) if cache_enabled else None

        if cache_enabled:
            self.logger.info(f"Crew output caching enabled (max age: {cache_max_age_hours}h)")
        else:
            self.logger.info("Crew output caching disabled")

    def execute_crypto_crew(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Execute cryptocurrency analysis crew with error handling."""
        if not is_feature_enabled("crypto_analysis"):
            self.logger.info("Crypto analysis disabled via feature flag")
            return {"crypto_analysis_disabled": True}

        # Check for cached output first
        if self.cache_enabled and self.output_cache:
            cached_data = self.output_cache.get_cached_crew_output("crypto")
            if cached_data:
                # Wrap cached data in expected structure before storing
                wrapped_cached_data = self._wrap_cached_data_for_storage(cached_data, "crypto")

                # Store wrapped cached data in integration system
                self.integration_manager.store_crew_output("crypto", wrapped_cached_data)

                # Return success response with cached data
                return {
                    "crypto_analysis_result": json.dumps(cached_data),
                    "core_analysis_completed": True,
                    "crypto_analysis_success": True,
                    "crypto_analysis_cached": True,
                    "cache_age_hours": cached_data.get("_cache_metadata", {}).get("cache_age_hours", 0),
                }

        start_time = datetime.now()

        try:
            self.logger.info("Starting cryptocurrency analysis crew (Phase 2: Core Analysis)")
            crypto_crew = CryptoCrew()
            result = crypto_crew.crew().kickoff(inputs=inputs)

            # Store crew result in integration system
            self.integration_manager.store_crew_output("crypto", result)

            # Prepare success response
            result_data = {
                "crypto_analysis_result": str(result.raw) if hasattr(result, "raw") else str(result),
                "core_analysis_completed": True,
                "crypto_analysis_success": True,
                "crypto_analysis_cached": False,
            }

            self.logger.info("Cryptocurrency analysis crew completed successfully")
            return result_data

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Cryptocurrency analysis crew failed: {e}", exc_info=True)

            # Handle error with graceful degradation
            fallback_response = self.error_handler.handle_crew_failure(crew_name="crypto", error=e, inputs=inputs, execution_time=execution_time)

            # Prepare error response
            result_data = {
                "crypto_analysis_error": str(e),
                "crypto_analysis_success": False,
                "crypto_analysis_fallback": True,
                "crypto_fallback_strategy": fallback_response.fallback_strategy,
                "crypto_degraded_functionality": fallback_response.degraded_functionality,
            }

            if fallback_response.success and fallback_response.data:
                # Use fallback data
                result_data["crypto_analysis_result"] = json.dumps(fallback_response.data)
                self.integration_manager.store_crew_output("crypto", fallback_response.data)
                self.logger.info(f"Using fallback data for crypto analysis: {fallback_response.message}")
            else:
                # Complete failure - continue without crypto analysis
                result_data["crypto_analysis_result"] = None
                self.logger.warning(f"Crypto analysis completely failed: {fallback_response.message}")

            return result_data

    def execute_stock_crew(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Execute stock analysis crew with error handling."""
        if not is_feature_enabled("stock_analysis"):
            self.logger.info("Stock analysis disabled via feature flag")
            return {"stock_analysis_disabled": True}

        # Check for cached output first
        if self.cache_enabled and self.output_cache:
            cached_data = self.output_cache.get_cached_crew_output("stock")
            if cached_data:
                # Wrap cached data in expected structure before storing
                wrapped_cached_data = self._wrap_cached_data_for_storage(cached_data, "stock")

                # Store wrapped cached data in integration system
                self.integration_manager.store_crew_output("stock", wrapped_cached_data)

                # Return success response with cached data
                return {
                    "stock_analysis_result": json.dumps(cached_data),
                    "core_analysis_completed": True,
                    "stock_analysis_success": True,
                    "stock_analysis_cached": True,
                    "cache_age_hours": cached_data.get("_cache_metadata", {}).get("cache_age_hours", 0),
                }

        start_time = datetime.now()

        try:
            self.logger.info("Starting stock analysis crew (Phase 2: Core Analysis)")
            stock_crew = StockCrew()
            result = stock_crew.crew().kickoff(inputs=inputs)

            # Store crew result in integration system
            self.integration_manager.store_crew_output("stock", result)

            # Prepare success response
            result_data = {
                "stock_analysis_result": str(result.raw) if hasattr(result, "raw") else str(result),
                "core_analysis_completed": True,
                "stock_analysis_success": True,
                "stock_analysis_cached": False,
            }

            self.logger.info("Stock analysis crew completed successfully")
            return result_data

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Stock analysis crew failed: {e}", exc_info=True)

            # Handle error with graceful degradation
            fallback_response = self.error_handler.handle_crew_failure(crew_name="stock", error=e, inputs=inputs, execution_time=execution_time)

            # Prepare error response
            result_data = {
                "stock_analysis_error": str(e),
                "stock_analysis_success": False,
                "stock_analysis_fallback": True,
                "stock_fallback_strategy": fallback_response.fallback_strategy,
                "stock_degraded_functionality": fallback_response.degraded_functionality,
            }

            if fallback_response.success and fallback_response.data:
                # Use fallback data
                result_data["stock_analysis_result"] = json.dumps(fallback_response.data)
                self.integration_manager.store_crew_output("stock", fallback_response.data)
                self.logger.info(f"Using fallback data for stock analysis: {fallback_response.message}")
            else:
                # Complete failure - continue without stock analysis
                result_data["stock_analysis_result"] = None
                self.logger.warning(f"Stock analysis completely failed: {fallback_response.message}")

            return result_data

    def execute_etf_crew(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Execute ETF analysis crew with error handling."""
        if not is_feature_enabled("etf_analysis"):
            self.logger.info("ETF analysis disabled via feature flag")
            return {"etf_analysis_disabled": True}

        # Check for cached output first
        if self.cache_enabled and self.output_cache:
            cached_data = self.output_cache.get_cached_crew_output("etf")
            if cached_data:
                # Wrap cached data in expected structure before storing
                wrapped_cached_data = self._wrap_cached_data_for_storage(cached_data, "etf")

                # Store wrapped cached data in integration system
                self.integration_manager.store_crew_output("etf", wrapped_cached_data)

                # Return success response with cached data
                return {
                    "etf_analysis_result": json.dumps(cached_data),
                    "core_analysis_completed": True,
                    "etf_analysis_success": True,
                    "etf_analysis_cached": True,
                    "cache_age_hours": cached_data.get("_cache_metadata", {}).get("cache_age_hours", 0),
                }

        start_time = datetime.now()

        try:
            self.logger.info("Starting ETF analysis crew (Phase 2: Core Analysis)")
            etf_crew = EtfCrew()
            result = etf_crew.crew().kickoff(inputs=inputs)

            # Store crew result in integration system
            self.integration_manager.store_crew_output("etf", result)

            # Prepare success response
            result_data = {
                "etf_analysis_result": str(result.raw) if hasattr(result, "raw") else str(result),
                "core_analysis_completed": True,
                "etf_analysis_success": True,
            }

            self.logger.info("ETF analysis crew completed successfully")
            return result_data

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"ETF analysis crew failed: {e}", exc_info=True)

            # Handle error with graceful degradation
            fallback_response = self.error_handler.handle_crew_failure(crew_name="etf", error=e, inputs=inputs, execution_time=execution_time)

            # Prepare error response
            result_data = {
                "etf_analysis_error": str(e),
                "etf_analysis_success": False,
                "etf_analysis_fallback": True,
                "etf_fallback_strategy": fallback_response.fallback_strategy,
                "etf_degraded_functionality": fallback_response.degraded_functionality,
            }

            if fallback_response.success and fallback_response.data:
                # Use fallback data
                result_data["etf_analysis_result"] = json.dumps(fallback_response.data)
                self.integration_manager.store_crew_output("etf", fallback_response.data)
                self.logger.info(f"Using fallback data for ETF analysis: {fallback_response.message}")
            else:
                # Complete failure - continue without ETF analysis
                result_data["etf_analysis_result"] = None
                self.logger.warning(f"ETF analysis completely failed: {fallback_response.message}")

            return result_data

    def execute_portfolio_rebalancing_crew(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Execute portfolio rebalancing crew with error handling."""
        if not is_feature_enabled("portfolio_rebalancing"):
            self.logger.info("Portfolio rebalancing disabled via feature flag")
            return {"portfolio_rebalancing_available": False}

        try:
            self.logger.info("Starting portfolio rebalancing crew")

            # Initialize portfolio rebalancing crew
            portfolio_rebalancing_crew = PortfolioRebalancingCrew()

            # Execute the portfolio rebalancing crew
            result = portfolio_rebalancing_crew.crew().kickoff(inputs=inputs)

            # Prepare success response
            result_data = {
                "portfolio_rebalancing_result": str(result.raw) if hasattr(result, "raw") else str(result),
                "portfolio_rebalancing_available": True,
            }

            self.logger.info("Portfolio rebalancing analysis completed successfully")
            return result_data

        except Exception as e:
            self.logger.error(f"Portfolio rebalancing analysis failed: {e}", exc_info=True)

            # Return error response with graceful degradation
            return {
                "portfolio_rebalancing_available": False,
                "portfolio_rebalancing_error": str(e),
                "portfolio_rebalancing_result": None,
            }

    def execute_investment_discovery_crew(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Execute investment discovery crew with error handling."""
        if not is_feature_enabled("investment_discovery"):
            self.logger.info("Investment discovery disabled via feature flag")
            return {"investment_discovery_available": False}

        try:
            self.logger.info("Starting investment discovery crew")

            # Initialize investment discovery crew
            investment_discovery_crew = InvestmentDiscoveryCrew()

            # Execute the investment discovery crew
            result = investment_discovery_crew.crew().kickoff(inputs=inputs)

            # Store crew result in integration system
            self.integration_manager.store_crew_output("discovery", result)

            # Prepare success response
            result_data = {
                "investment_discovery_result": str(result.raw) if hasattr(result, "raw") else str(result),
                "investment_discovery_available": True,
            }

            self.logger.info("Investment discovery analysis completed successfully")
            return result_data

        except Exception as e:
            self.logger.error(f"Investment discovery analysis failed: {e}", exc_info=True)

            # Return error response with graceful degradation
            return {
                "investment_discovery_available": False,
                "investment_discovery_error": str(e),
                "investment_discovery_result": None,
                "investment_discovery_structured": {"has_a_plus_analysis": False},
            }

    def execute_report_crew(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Execute report generation crew with error handling."""
        try:
            self.logger.info("Starting report generation crew")

            # Debug: Log what keys are in inputs
            self.logger.info(f"Inputs keys received: {list(inputs.keys())[:30]}")
            if "portfolio_review" in inputs:
                self.logger.info("✅ portfolio_review found in inputs")
            else:
                self.logger.warning("❌ portfolio_review NOT found in inputs - this will cause template variable error")

            # Initialize Report crew
            report_crew = ReportCrew()

            # CRITICAL: Prepare crew context with validated tickers
            # This extracts tickers from upstream crew data and prevents hallucination
            try:
                prepared_context = report_crew.context_manager.prepare_crew_context(max_age_hours=24, inputs=inputs)
                ticker_count = prepared_context.get("ticker_count", 0)

                # Check for insufficient tickers warning
                if prepared_context.get("insufficient_tickers", False):
                    self.logger.warning(f"Proceeding with limited report generation: {ticker_count} validated tickers (recommended: 3+)")
                else:
                    self.logger.info(f"Crew context prepared with {ticker_count} validated tickers")

                # Debug: Check if portfolio_review is in prepared context
                if "portfolio_review" in prepared_context:
                    self.logger.info("✅ portfolio_review preserved in prepared_context")
                else:
                    self.logger.error("❌ portfolio_review NOT in prepared_context - template variable error will occur")

            except Exception as e:
                self.logger.error(f"Failed to prepare crew context: {e}", exc_info=True)
                return {
                    "report_generation_error": f"Context preparation failed: {e}",
                    "report_generation_success": False,
                    "error_type": "context_preparation_failed",
                }

            # Execute the report crew with prepared context
            report_crew.crew().kickoff(inputs=prepared_context)

            self.logger.info("Report generation completed successfully")
            return {"report_generation_success": True}

        except Exception as e:
            self.logger.error(f"Report generation failed: {str(e)}", exc_info=True)

            # Return error response
            return {
                "report_generation_error": str(e),
                "report_generation_success": False,
            }

    def create_crew_inputs_for_portfolio_rebalancing(self, base_inputs: dict[str, Any], core_analysis_status: dict[str, Any]) -> dict[str, Any]:
        """Create specialized inputs for portfolio rebalancing crew."""
        if core_analysis_status["any_available"]:
            self.logger.info(f"Creating portfolio rebalancing inputs with core analysis integration: {core_analysis_status['available_crews']}")

            # Prepare enhanced inputs with available core analysis
            crew_inputs = {
                "full_date": datetime.now().strftime("%B %d, %Y"),
                "portfolio_data": base_inputs.get("portfolio_review", {}),
                "target_allocations": base_inputs.get("target_allocations", {}),
                "tolerance_bands": base_inputs.get("tolerance_bands", {}),
                "available_capital": base_inputs.get("available_capital", 0.0),
                # Enhanced with available core analysis results
                "stock_analysis": base_inputs.get("stock_analysis_result") if core_analysis_status["stock_available"] else None,
                "etf_analysis": base_inputs.get("etf_analysis_result") if core_analysis_status["etf_available"] else None,
                "crypto_analysis": base_inputs.get("crypto_analysis_result") if core_analysis_status["crypto_available"] else None,
                "market_conditions": self._extract_market_conditions_from_inputs(base_inputs),
                "core_analysis_status": core_analysis_status,
                # Include fallback information
                "stock_fallback": base_inputs.get("stock_analysis_fallback", False),
                "etf_fallback": base_inputs.get("etf_analysis_fallback", False),
                "crypto_fallback": base_inputs.get("crypto_analysis_fallback", False),
            }
        else:
            self.logger.warning("Creating portfolio rebalancing inputs without core analysis - all crews failed or disabled")

            # Fallback to basic behavior
            crew_inputs = {
                "full_date": datetime.now().strftime("%B %d, %Y"),
                "portfolio_data": base_inputs.get("portfolio_review", {}),
                "target_allocations": base_inputs.get("target_allocations", {}),
                "tolerance_bands": base_inputs.get("tolerance_bands", {}),
                "available_capital": base_inputs.get("available_capital", 0.0),
                "core_analysis_status": core_analysis_status,
                "degraded_mode": True,
            }

        return crew_inputs

    def create_crew_inputs_for_investment_discovery(
        self,
        base_inputs: dict[str, Any],
        core_analysis_status: dict[str, Any],
        upstream_data: Any,
        core_analysis_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Create specialized inputs for investment discovery crew."""
        # Prepare inputs for the crew with integrated data access and core analysis results
        crew_inputs = {
            "full_date": datetime.now().strftime("%B %d, %Y"),
            "current_date": base_inputs.get("current_date"),
            "timestamp": base_inputs.get("timestamp"),
            "portfolio_data": base_inputs.get("portfolio_review", {}),
            "portfolio_review_json": base_inputs.get("portfolio_review_json", ""),
            "has_existing_session": base_inputs.get("has_existing_session", False),
            "session_id": base_inputs.get("session_id", ""),
            "analysis_count": base_inputs.get("analysis_count", 0),
            "report_language": base_inputs.get("report_language", "fr"),
            # Portfolio rebalancing results if available
            "portfolio_rebalancing_result": base_inputs.get("portfolio_rebalancing_result"),
            "portfolio_rebalancing_available": base_inputs.get("portfolio_rebalancing_available", False),
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
                "stock_error": base_inputs.get("stock_analysis_error"),
                "etf_error": base_inputs.get("etf_analysis_error"),
                "crypto_error": base_inputs.get("crypto_analysis_error"),
            },
            "fallback_strategies_used": {
                "stock_fallback": base_inputs.get("stock_fallback_strategy"),
                "etf_fallback": base_inputs.get("etf_fallback_strategy"),
                "crypto_fallback": base_inputs.get("crypto_fallback_strategy"),
            },
        }

        return crew_inputs

    def _extract_market_conditions_from_inputs(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Extract market conditions from flow inputs."""
        conditions = {}

        if inputs.get("stock_analysis_result"):
            conditions["stock_market_sentiment"] = "Available from stock analysis"

        if inputs.get("etf_analysis_result"):
            conditions["sector_trends"] = "Available from ETF analysis"

        if inputs.get("crypto_analysis_result"):
            conditions["crypto_market_dynamics"] = "Available from crypto analysis"

        return conditions

    def _extract_market_context_from_core_analysis(self, core_analysis_data: dict[str, Any]) -> dict[str, Any]:
        """Extract market context from core analysis data."""
        # This is a simplified version - the full implementation is in FlowStateManager
        market_context: dict[str, Any] = {
            "overall_sentiment": "neutral",
            "market_trends": [],
            "risk_factors": [],
            "opportunities": [],
        }

        try:
            # Extract basic context from available core analysis
            for analysis_type, analysis_data in core_analysis_data.items():
                if "opportunities" in analysis_data:
                    opportunities = analysis_data["opportunities"]
                    if isinstance(opportunities, list):
                        market_context["opportunities"].extend(opportunities)

            return market_context

        except Exception as e:
            self.logger.warning(f"Failed to extract market context from core analysis: {e}")
            return market_context

    def _wrap_cached_data_for_storage(self, cached_data: dict[str, Any], crew_name: str) -> dict[str, Any]:
        """
        Wrap cached crew data in the expected storage structure.

        This ensures cached data has the same structure as fresh crew outputs,
        preventing validation errors in the data consolidation validator.

        Args:
            cached_data: Raw cached data (Pydantic model output)
            crew_name: Name of the crew

        Returns:
            Wrapped data with expected structure (raw_output, json_dict, pydantic, tasks_output)

        """
        return {
            "raw_output": json.dumps(cached_data, indent=2, default=str),
            "json_dict": cached_data,
            "pydantic": cached_data,  # Already in dict form from cache
            "tasks_output": [],  # Cached data doesn't have task-level details
            "metadata": {
                "crew_name": crew_name,
                "storage_timestamp": datetime.now().isoformat(),
                "integration_version": "1.0",
                "data_source": "cache",
                "data_freshness": {
                    "stored_at": datetime.now().isoformat(),
                    "is_fresh": True,
                    "age_hours": cached_data.get("_cache_metadata", {}).get("cache_age_hours", 0),
                },
            },
        }
