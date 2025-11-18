"""
Validation Orchestrator for FinWiz Flow.

This module provides validation and data availability checking including:
- Reporter input validation
- Core analysis availability checking
- Market conditions extraction
- Market context extraction from core analysis
"""

from typing import Any

from finwiz.flow_state import FinwizState
from finwiz.orchestrators.validation_helpers import (
    extract_common_factors,
    extract_crypto_context,
    extract_etf_context,
    extract_stock_context,
    prepare_core_analysis_summary,
)
from finwiz.tools.logger import get_logger


class ValidationOrchestrator:
    """Validates data and prepares for reporting."""

    def __init__(self, state: FinwizState, **dependencies: Any) -> None:
        """
        Initialize the ValidationOrchestrator.

        Args:
            state: FinwizState instance for accessing workflow state
            **dependencies: Additional dependencies including:
                - integration_manager: CrewDataIntegrationManager for data access
                - data_accessor: For consolidated data retrieval
                - cache_service: Optional cache service for Supabase integration

        """
        self.state = state
        self.logger = get_logger(self.__class__.__name__)
        self.integration_manager = dependencies.get("integration_manager")
        self.data_accessor = dependencies.get("data_accessor")
        self.cache_service = dependencies.get("cache_service")

    async def validate_data_integration(self) -> dict[str, Any]:
        """
        Validate data integration system before crew execution.

        Phase 1: Data Validation
        - Test Supabase connectivity (if enabled)
        - Validate integration manager
        - Initialize session metadata

        Requirements: 7.1

        Returns:
            dict: Validation results

        """
        self.logger.info("=" * 80)
        self.logger.info("Phase 1: Data Integration Validation")
        self.logger.info("=" * 80)

        validation_results = {
            "integration_manager_available": self.integration_manager is not None,
            "data_accessor_available": self.data_accessor is not None,
            "cache_service_available": self.cache_service is not None,
            "cache_enabled": False,
        }

        # Test Supabase connectivity if cache service is available
        if self.cache_service:
            try:
                self.logger.info("Testing Supabase connectivity...")
                is_healthy = await self.cache_service.health_check()

                if is_healthy:
                    self.logger.info("✓ Supabase connection successful")
                    validation_results["cache_enabled"] = True
                    self.state.cache_enabled = True
                else:
                    self.logger.warning("✗ Supabase health check failed - continuing without cache")
                    validation_results["cache_enabled"] = False
                    self.state.cache_enabled = False

            except Exception as e:
                self.logger.warning(f"✗ Supabase connectivity test failed: {e}")
                self.logger.info("Continuing without Supabase caching (graceful degradation)")
                validation_results["cache_enabled"] = False
                self.state.cache_enabled = False
        else:
            self.logger.info("Supabase cache service not configured - continuing without cache")

        # Validate integration manager
        if self.integration_manager:
            self.logger.info("✓ Data integration manager available")
        else:
            self.logger.warning("✗ Data integration manager not available")

        self.logger.info("=" * 80)

        return validation_results

    async def check_portfolio(self) -> dict[str, Any]:
        """
        Run portfolio keep-or-sell review orchestrator.

        Phase 2: Portfolio Analysis
        - Load portfolio data from CSV files
        - Build portfolio review with decisions
        - Store results in state

        Requirements: 7.1, 7.2

        Returns:
            dict: Portfolio review results

        """
        self.logger.info("=" * 80)
        self.logger.info("Phase 2: Portfolio Analysis")
        self.logger.info("=" * 80)

        # Import here to avoid circular dependencies
        from finwiz.orchestrators.review_engine import run

        try:
            # Run portfolio review (loads CSV, builds decisions) - MUST await async function
            review_path = await run(flow_state=self.state)
            
            # Load the generated review JSON
            import json
            from pathlib import Path
            
            review_data = json.loads(Path(review_path).read_text(encoding="utf-8"))

            # Update state
            self.state.portfolio_review = review_data
            self.state.portfolio_review_success = True
            self.state.portfolio_review_json = str(review_path)

            holdings_count = len(review_data.get("holdings", []))
            self.logger.info(f"Portfolio review completed: {holdings_count} holdings")
            self.logger.info(f"Review saved to: {review_path}")
            self.logger.info("=" * 80)

            return {
                "success": True,
                "portfolio_review": review_data,
                "holdings_count": holdings_count,
                "review_path": str(review_path),
            }

        except Exception as e:
            self.logger.error(f"Portfolio review failed: {e}", exc_info=True)
            self.state.portfolio_review_success = False
            self.state.portfolio_review_error = str(e)
            self.logger.info("=" * 80)

            return {
                "success": False,
                "error": str(e),
                "holdings_count": 0,
            }

    def check_portfolio_rebalancing(self) -> dict[str, Any]:
        """
        Run portfolio rebalancing analysis.

        Phase 6: Rebalancing
        - Execute rebalancing crew (if enabled)
        - Store results in state

        Requirements: 7.1

        Returns:
            dict: Rebalancing results

        """
        self.logger.info("=" * 80)
        self.logger.info("Phase 6: Portfolio Rebalancing")
        self.logger.info("=" * 80)

        # Check if rebalancing is enabled
        import os

        enabled = os.getenv("PORTFOLIO_ENABLE_REBALANCING", "false").lower() == "true"

        if not enabled:
            self.logger.info("Portfolio rebalancing disabled via PORTFOLIO_ENABLE_REBALANCING")
            self.logger.info("=" * 80)
            return {"success": True, "rebalancing_enabled": False}

        # Import here to avoid circular dependencies
        from finwiz.crews.portfolio_rebalancing.portfolio_rebalancing_crew import PortfolioRebalancingCrew

        try:
            # Execute rebalancing crew
            crew = PortfolioRebalancingCrew()
            result = crew.crew().kickoff(
                inputs={
                    "current_day": self.state.current_day,
                    "current_month": self.state.current_month,
                    "current_year": self.state.current_year,
                    "current_date": self.state.current_date,
                    "full_date": self.state.full_date,
                    "timestamp": self.state.timestamp,
                    "report_language": self.state.report_language,
                }
            )

            # Extract rebalancing results from crew output
            if hasattr(result, "pydantic") and result.pydantic:
                rebalancing_results = result.pydantic.model_dump() if hasattr(result.pydantic, "model_dump") else result.pydantic.dict()
            else:
                rebalancing_results = {"error": "Failed to extract rebalancing results"}

            # Update state
            self.state.rebalancing_results = rebalancing_results
            self.state.rebalancing_success = True

            self.logger.info("Portfolio rebalancing completed")
            self.logger.info("=" * 80)

            return {
                "success": True,
                "rebalancing_enabled": True,
                "rebalancing_results": rebalancing_results,
            }

        except Exception as e:
            self.logger.error(f"Portfolio rebalancing failed: {e}", exc_info=True)
            self.state.rebalancing_success = False
            self.state.rebalancing_error = str(e)
            self.logger.info("=" * 80)

            return {
                "success": False,
                "rebalancing_enabled": True,
                "error": str(e),
            }

    def pre_validate_reporter_input(
        self,
        consolidated_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Validate reporter input data before final report generation.

        This method consolidates data from all previous phases and validates
        that all required data is available for report generation.

        Args:
            consolidated_data: Optional pre-consolidated data. If not provided,
                will retrieve from data_accessor.

        Returns:
            Dictionary containing validation results and consolidated data

        """
        try:
            self.logger.info("Consolidating data for reporter input validation")
            core_analysis_status = self.check_core_analysis_availability()

            if consolidated_data is None:
                consolidated_data = self._get_consolidated_data()

            self._update_state_with_consolidated_data(consolidated_data)
            self._update_core_analysis_summary(consolidated_data, core_analysis_status)

            crew_data = consolidated_data.get("consolidated_crew_data", {})
            core_analysis_count = sum(1 for crew_type in ["stock", "etf", "crypto"] if crew_type in crew_data and crew_data[crew_type])

            return {
                "success": True,
                "core_analysis_available": core_analysis_count > 0,
                "core_analysis_count": core_analysis_count,
                "consolidated_data": consolidated_data,
                "core_analysis_status": core_analysis_status,
            }

        except Exception as e:
            self.logger.error(f"Reporter input validation failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "core_analysis_available": False,
                "core_analysis_count": 0,
            }

    def check_core_analysis_availability(self) -> dict[str, Any]:
        """
        Check which core analyses are available.

        Returns:
            Dictionary with availability status for each crew type

        """
        availability = {crew: self._check_crew_availability(crew) for crew in ["stock", "etf", "crypto"]}

        available_crews = [crew for crew, avail in availability.items() if avail]
        failed_crews = [crew for crew in ["stock", "etf", "crypto"] if getattr(self.state, f"{crew}_analysis_error")]
        disabled_crews = [crew for crew in ["stock", "etf", "crypto"] if getattr(self.state, f"{crew}_analysis_disabled")]

        return {
            "any_available": len(available_crews) > 0,
            "stock_available": availability["stock"],
            "etf_available": availability["etf"],
            "crypto_available": availability["crypto"],
            "available_crews": available_crews,
            "failed_crews": failed_crews,
            "disabled_crews": disabled_crews,
            "total_available": len(available_crews),
            "total_failed": len(failed_crews),
            "total_disabled": len(disabled_crews),
        }

    def extract_market_conditions(self) -> dict[str, Any]:
        """
        Extract market conditions from core analysis.

        Returns:
            Dictionary with market conditions extracted from state

        """
        conditions = {}
        if self.state.stock_analysis_result:
            conditions["stock_market_sentiment"] = "Available from stock analysis"
        if self.state.etf_analysis_result:
            conditions["sector_trends"] = "Available from ETF analysis"
        if self.state.crypto_analysis_result:
            conditions["crypto_market_dynamics"] = "Available from crypto analysis"
        return conditions

    def extract_market_context_from_core_analysis(
        self,
        core_analysis_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Extract market context information from core analysis results.

        Args:
            core_analysis_data: Dictionary containing core analysis results

        Returns:
            Dictionary with extracted market context including:
                - overall_sentiment: Overall market sentiment
                - market_trends: List of identified market trends
                - risk_factors: List of risk factors
                - opportunities: List of opportunities
                - sector_analysis: Sector-specific analysis

        """
        market_context = {
            "overall_sentiment": "neutral",
            "market_trends": [],
            "risk_factors": [],
            "opportunities": [],
            "sector_analysis": {},
        }

        try:
            extract_stock_context(core_analysis_data, market_context)
            extract_etf_context(core_analysis_data, market_context)
            extract_crypto_context(core_analysis_data, market_context)
            extract_common_factors(core_analysis_data, market_context)
        except Exception as e:
            self.logger.warning(f"Failed to extract market context: {e}", exc_info=True)

        return market_context

    def _get_consolidated_data(self) -> dict[str, Any]:
        """Retrieve consolidated data from data accessor."""
        try:
            if self.data_accessor:
                return self.data_accessor.get_consolidated_reporter_input()
            self.logger.warning("No data_accessor available")
            return {}
        except Exception as e:
            self.logger.warning(f"Failed to get consolidated data: {e}", exc_info=True)
            return {}

    def _update_state_with_consolidated_data(self, consolidated_data: dict[str, Any]) -> None:
        """Update state with consolidated data."""
        self.state.consolidated_data = consolidated_data
        self.state.integrated_data_available = len(consolidated_data) > 0
        self.state.market_sentiment = consolidated_data.get("market_sentiment", {})
        self.state.ticker_validation = consolidated_data.get("ticker_validation", {})
        self.state.aplus_opportunities = consolidated_data.get("aplus_opportunities")
        self.state.portfolio_allocation_updates = consolidated_data.get("portfolio_allocation_updates")
        self.state.aplus_availability_status = consolidated_data.get("aplus_availability_status")

    def _update_core_analysis_summary(
        self,
        consolidated_data: dict[str, Any],
        core_analysis_status: dict[str, Any],
    ) -> None:
        """Update state with core analysis summary."""
        try:
            summary = prepare_core_analysis_summary(consolidated_data, core_analysis_status)
            self.state.core_analysis_summary = summary
        except Exception as e:
            self.logger.warning(f"Failed to prepare core analysis summary: {e}")
            self.state.core_analysis_summary = {
                "available_crews": core_analysis_status["available_crews"],
                "failed_crews": core_analysis_status["failed_crews"],
                "disabled_crews": core_analysis_status["disabled_crews"],
                "error": "Failed to prepare detailed summary",
            }

    def _check_crew_availability(self, crew_type: str) -> bool:
        """Check if a specific crew type is available."""
        try:
            if self.integration_manager:
                data = self.integration_manager.get_crew_data_with_freshness_check(crew_type, max_age_hours=24, warn_on_stale=False)
                return data is not None
        except Exception as e:
            self.logger.warning(f"Failed to check {crew_type} availability: {e}")

        success = getattr(self.state, f"{crew_type}_analysis_success")
        fallback = getattr(self.state, f"{crew_type}_analysis_fallback")
        result = getattr(self.state, f"{crew_type}_analysis_result")
        return success or (fallback and result is not None)
