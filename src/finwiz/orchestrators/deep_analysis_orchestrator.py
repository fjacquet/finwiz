"""Deep Analysis Orchestrator for FinWiz Flow.

This module coordinates deep analysis execution by delegating to specialized modules:
- DeepAnalysisDataCollector: Raw data collection
- DeepAnalysisExecutor: Sequential/concurrent execution
- DeepAnalysisProcessor: Result processing and metrics
"""

import os
from typing import Any

from finwiz.flow_state import DeepAnalysisResult, FinwizState
from finwiz.orchestrators.deep_analysis_data_collector import DeepAnalysisDataCollector
from finwiz.orchestrators.deep_analysis_executor import DeepAnalysisExecutor
from finwiz.orchestrators.deep_analysis_processor import DeepAnalysisProcessor
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class DeepAnalysisOrchestrator:
    """Orchestrates deep analysis execution on portfolio holdings."""

    def __init__(self, state: FinwizState, **dependencies: Any) -> None:
        self.state = state
        self.logger = get_logger(self.__class__.__name__)
        self.batch_prefetch_config = dependencies.get("batch_prefetch_config")
        self.cache_service = dependencies.get("cache_service")
        self.cache_enabled = dependencies.get("cache_enabled", False)
        self.crew_factory = dependencies.get("crew_factory")
        self.integration_manager = dependencies.get("integration_manager")
        self.error_handler = dependencies.get("error_handler")

        # Initialize component modules
        self.data_collector = DeepAnalysisDataCollector(state)
        self.result_processor = DeepAnalysisProcessor(state)
        self.executor = DeepAnalysisExecutor(
            state=state,
            data_collector=self.data_collector,
            result_processor=self.result_processor,
            batch_prefetch_config=self.batch_prefetch_config,
            integration_manager=self.integration_manager,
        )

        # Initialize DataSourceOrchestrator for multi-source data acquisition
        from finwiz.data.data_source_orchestrator import DataSourceOrchestrator

        self.data_orchestrator = DataSourceOrchestrator(
            total_timeout=10.0,
            per_source_timeout=3.0,
            enable_validation=True,
        )

    async def analyze_and_update_portfolio(self) -> dict[str, Any]:
        """
        Perform deep analysis and update portfolio review (atomic operation).

        This method consolidates three related operations:
        1. Run deep analysis on holdings
        2. Match alternatives for underperforming holdings
        3. Update portfolio review with enriched data

        Returns:
            dict: Consolidated results with deep analysis and alternatives
        """
        self.logger.info("=" * 80)
        self.logger.info("Phase 3: Deep Analysis & Portfolio Update (Atomic Operation)")
        self.logger.info("=" * 80)

        enabled = os.getenv("DEEP_PORTFOLIO_ANALYSIS", "false").lower() == "true"
        if not enabled:
            self.logger.info("Deep analysis disabled via DEEP_PORTFOLIO_ANALYSIS")
            return {}

        portfolio_review = self.state.portfolio_review
        if not portfolio_review or not portfolio_review.get("holdings"):
            self.logger.warning("No portfolio holdings available for deep analysis")
            return {}

        holdings = portfolio_review.get("holdings", [])
        self.logger.info(f"Starting deep analysis for {len(holdings)} holdings")

        # Step 1: Run deep analysis on all holdings
        try:
            deep_results = self.run_deep_analysis_on_holdings(holdings)
            self.state.deep_analysis_results = deep_results
            self.state.deep_analysis_success = True
            self.logger.info(f"Deep analysis completed: {len(deep_results)}/{len(holdings)} holdings analyzed")
        except Exception as e:
            self.logger.error(f"Deep analysis failed: {e}", exc_info=True)
            self.state.deep_analysis_success = False
            self.state.deep_analysis_error = str(e)
            return {"deep_analysis_results": {}, "error": str(e)}

        # Step 2: Match alternatives for underperforming holdings
        alternatives_data = self._match_alternatives(deep_results)

        # Step 3: Update portfolio review with enriched data
        self._update_portfolio_review_with_enriched_data(deep_results, alternatives_data)

        self.logger.info("=" * 80)

        return {
            "deep_analysis_results": deep_results,
            "alternatives": alternatives_data,
            "portfolio_updated": True,
        }

    def run_deep_analysis_on_holdings(self, holdings: list[dict[str, Any]]) -> dict[str, DeepAnalysisResult]:
        """
        Execute deep analysis on all holdings.

        Delegates to DeepAnalysisExecutor for actual execution.

        Args:
            holdings: List of holding dicts with 'ticker' and 'asset_class' keys

        Returns:
            Dictionary mapping tickers to DeepAnalysisResult objects
        """
        return self.executor.run_deep_analysis_on_holdings(holdings)

    async def run_deep_analysis_concurrent(self, holdings: list[dict[str, Any]]) -> dict[str, DeepAnalysisResult]:
        """
        Execute deep analysis on all holdings concurrently.

        Delegates to DeepAnalysisExecutor.

        Args:
            holdings: List of holding dicts with 'ticker' and 'asset_class' keys

        Returns:
            Dictionary mapping tickers to DeepAnalysisResult objects
        """
        return await self.executor.run_deep_analysis_concurrent(holdings)

    def _match_alternatives(self, deep_results: dict[str, DeepAnalysisResult]) -> dict[str, list[dict[str, Any]]]:
        """Match alternatives for underperforming holdings."""
        try:
            from finwiz.orchestrators.alternatives_matching_orchestrator import AlternativesMatchingOrchestrator

            alternatives_orch = AlternativesMatchingOrchestrator(
                state=self.state,
                crew_factory=self.crew_factory,
                integration_manager=self.integration_manager,
                error_handler=self.error_handler,
            )

            holdings_with_analysis = [
                {
                    "ticker": ticker,
                    "grade": analysis.grade,
                    "composite_score": analysis.composite_score,
                    "risk_score": analysis.risk_score,
                    "name": getattr(analysis, "name", ticker),
                    "asset_class": analysis.asset_class,
                }
                for ticker, analysis in deep_results.items()
            ]

            alternatives_data = alternatives_orch.match_alternatives_for_holdings(
                holdings_with_analysis, {}
            )

            self.state.portfolio_alternatives = alternatives_data
            self.state.alternatives_success = True
            self.state.alternatives_count = sum(len(alts) for alts in alternatives_data.values())

            self.logger.info(f"Alternative matching completed: {self.state.alternatives_count} alternatives found")
            return alternatives_data

        except Exception as e:
            self.logger.error(f"Alternative matching failed: {e}", exc_info=True)
            self.state.alternatives_success = False
            return {}

    def _update_portfolio_review_with_enriched_data(
        self,
        deep_results: dict[str, DeepAnalysisResult],
        alternatives_data: dict[str, list[dict[str, Any]]],
    ) -> None:
        """Update portfolio review with deep analysis results and alternatives."""
        try:
            if not self.state.portfolio_review:
                return

            holdings = self.state.portfolio_review.get("holdings", [])

            for holding in holdings:
                ticker = holding.get("ticker")
                if not ticker:
                    continue

                if ticker in deep_results:
                    analysis = deep_results[ticker]
                    holding["composite_score"] = analysis.composite_score
                    holding["grade"] = analysis.grade

                if ticker in alternatives_data:
                    holding["alternatives"] = alternatives_data[ticker]

            self.state.portfolio_review["holdings"] = holdings
            self.logger.info("Portfolio review updated with deep analysis and alternatives")

        except Exception as e:
            self.logger.error(f"Portfolio review update failed: {e}", exc_info=True)

    # Legacy method delegation for backward compatibility
    def execute_deep_analysis_with_prefetch(self, tickers: list[str]) -> dict[str, Any]:
        """Execute with batch prefetch optimization. Delegates to executor."""
        return self.executor._execute_prefetch(tickers)

    def save_batch_metrics_to_file(self, metrics: dict[str, Any], output_path: str | None = None) -> None:
        """Save batch metrics to file. Delegates to processor."""
        self.result_processor.save_batch_metrics_to_file(metrics, output_path)

    def create_deep_analysis_result_from_crew_output(
        self, crew_output: Any, ticker: str, asset_class: str, crew_name: str = "DeepAnalysisCrew", cached: bool = False
    ) -> DeepAnalysisResult:
        """Parse crew output into structured result. Delegates to processor."""
        return self.result_processor.create_deep_analysis_result_from_crew_output(
            crew_output, ticker, asset_class, crew_name, cached
        )
