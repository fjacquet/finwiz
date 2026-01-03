"""Deep Analysis Orchestrator for FinWiz Flow.

This module coordinates deep analysis execution using functional pipeline composition:
- analyze_holding(): Main pipeline function (collect -> quantitative -> qualitative -> synthesize)
- DeepAnalysisDataCollector: Raw data collection (used by pipeline)

Architecture (Clean Functional Pipeline):
    1. collect_raw_data(ctx) -> RawData         [Python tools]
    2. calculate_quantitative(ctx, raw) -> Quant   [$0 Python]
    3. generate_qualitative(ctx, quant) -> Qual    [AI crew]
    4. synthesize(ctx, quant, qual) -> Enriched    [Python]
"""

import os
from pathlib import Path
from typing import Any

from finwiz.flow_state import DeepAnalysisResult, FinwizState
from finwiz.orchestrators.deep_analysis_data_collector import DeepAnalysisDataCollector
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

        # Data collector for raw data acquisition
        self.data_collector = DeepAnalysisDataCollector(state)

        # Enriched analysis storage (populated during analysis)
        self._enriched_analyses: dict[str, Any] = {}

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

        # Step 1: Run deep analysis on all holdings CONCURRENTLY
        try:
            # Use concurrent execution for better performance
            deep_results = await self.run_deep_analysis_concurrent(holdings)
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
        Execute deep analysis on all holdings using functional pipeline.

        Pipeline composition:
        1. collect_raw_data (Python tools)
        2. calculate_quantitative (Python scorer - $0)
        3. generate_qualitative (AI crew)
        4. synthesize_enriched_analysis (Python)

        Args:
            holdings: List of holding dicts with 'ticker' and 'asset_class' keys

        Returns:
            Dictionary mapping tickers to DeepAnalysisResult objects
        """
        from finwiz.analysis import analyze_holding

        results: dict[str, DeepAnalysisResult] = {}
        self._enriched_analyses = {}

        for holding in holdings:
            ticker = holding.get("ticker")
            asset_class = holding.get("asset_class")
            company_name = holding.get("name", "")

            if not ticker or not asset_class:
                self.logger.warning(f"Skipping holding with missing ticker or asset_class: {holding}")
                continue

            try:
                # Functional pipeline - returns BOTH DeepAnalysisResult AND EnrichedAnalysis
                result, enriched = analyze_holding(ticker, asset_class, company_name)
                results[ticker] = result

                # Store enriched analysis for HTML generation
                self._enriched_analyses[ticker] = enriched
                self._store_enriched_analysis(ticker, enriched)

                self.logger.info(f"Analysis complete: {ticker} grade={result.grade} score={result.composite_score:.2f}")

            except Exception as e:
                self.logger.error(f"Analysis failed for {ticker}: {e}", exc_info=True)
                # Continue with other holdings

        self.logger.info(f"Deep analysis completed: {len(results)}/{len(holdings)} holdings analyzed")
        return results

    def _store_enriched_analysis(self, ticker: str, enriched: Any) -> None:
        """Store enriched analysis JSON AND generate HTML immediately.
        
        AI Minimalism: HTML generation is pure Python, no need to wait.
        Generate outputs as soon as data is available.
        """
        try:
            from finwiz.reporting.enriched_analysis_report_generator import (
                generate_enriched_analysis_report,
            )
            from finwiz.schemas.hybrid_analysis import EnrichedAnalysis

            if not isinstance(enriched, EnrichedAnalysis):
                self.logger.warning(f"Expected EnrichedAnalysis, got {type(enriched)}")
                return

            # Store in session output directory
            session_id = getattr(self.state, "session_id", "default")
            output_dir = Path(f"output/enriched/{session_id}/{enriched.asset_class}")
            output_dir.mkdir(parents=True, exist_ok=True)

            # 1. Store JSON immediately
            json_path = output_dir / f"{ticker}_enriched.json"
            json_path.write_text(enriched.model_dump_json(indent=2))
            self.logger.info(f"✅ Stored JSON: {json_path}")

            # 2. Generate HTML immediately (pure Python, no AI cost)
            html_content = generate_enriched_analysis_report(enriched)
            html_path = output_dir / f"{ticker}_report.html"
            html_path.write_text(html_content)
            self.logger.info(f"✅ Generated HTML: {html_path}")

        except Exception as e:
            self.logger.error(f"Failed to store enriched analysis for {ticker}: {e}")

    def get_enriched_analysis(self, ticker: str) -> Any | None:
        """Get stored enriched analysis for a ticker."""
        return self._enriched_analyses.get(ticker)

    async def run_deep_analysis_concurrent(self, holdings: list[dict[str, Any]], max_workers: int | None = None) -> dict[str, DeepAnalysisResult]:
        """
        Execute deep analysis on all holdings concurrently.

        Uses a shared ThreadPoolExecutor with configurable max_workers for efficient
        parallel processing. The number of concurrent analyses is controlled by
        DEEP_ANALYSIS_BATCH_SIZE environment variable (default: 5).

        Args:
            holdings: List of holding dicts with 'ticker' and 'asset_class' keys
            max_workers: Max concurrent analyses (default: from DEEP_ANALYSIS_BATCH_SIZE)

        Returns:
            Dictionary mapping tickers to DeepAnalysisResult objects
        """
        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        from finwiz.analysis import analyze_holding
        from finwiz.config.performance.performance_config import get_batch_size

        # Get max_workers from config if not specified
        if max_workers is None:
            max_workers = get_batch_size()

        self.logger.info(f"Starting concurrent deep analysis: {len(holdings)} holdings, max_workers={max_workers}")

        results: dict[str, DeepAnalysisResult] = {}
        self._enriched_analyses = {}

        def analyze_single_sync(holding: dict[str, Any]) -> tuple[str, DeepAnalysisResult | None, Any | None]:
            """Synchronous wrapper for analyze_holding (runs in thread pool)."""
            ticker = holding.get("ticker")
            asset_class = holding.get("asset_class")
            company_name = holding.get("name", "")

            if not ticker or not asset_class:
                return (ticker or "unknown", None, None)

            try:
                result, enriched = analyze_holding(ticker, asset_class, company_name)
                return (ticker, result, enriched)
            except Exception as e:
                self.logger.error(f"Concurrent analysis failed for {ticker}: {e}")
                return (ticker, None, None)

        # Use a SHARED ThreadPoolExecutor for all holdings
        loop = asyncio.get_running_loop()
        completed: list[tuple[str, DeepAnalysisResult | None, Any | None]] = []

        # Per-holding timeout (5 minutes each) - prevents one stuck ticker blocking all
        PER_HOLDING_TIMEOUT = 300  # 5 minutes per holding

        async def analyze_with_timeout(holding: dict[str, Any]) -> tuple[str, DeepAnalysisResult | None, Any | None]:
            """Wrap analysis with per-holding timeout."""
            ticker = holding.get("ticker", "unknown")
            try:
                return await asyncio.wait_for(
                    loop.run_in_executor(executor, analyze_single_sync, holding),
                    timeout=PER_HOLDING_TIMEOUT,
                )
            except TimeoutError:
                self.logger.error(f"Analysis timed out for {ticker} after {PER_HOLDING_TIMEOUT}s")
                return (ticker, None, None)
            except Exception as e:
                self.logger.error(f"Analysis failed for {ticker}: {e}")
                return (ticker, None, None)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all holdings with per-holding timeout
            futures = [analyze_with_timeout(holding) for holding in holdings]
            # Wait for all to complete - each has its own timeout so no global timeout needed
            try:
                completed = await asyncio.gather(*futures, return_exceptions=False)
            except Exception as e:
                self.logger.error(f"Deep analysis gather failed: {e}")
                completed = []

        self.logger.info(f"asyncio.gather completed with {len(completed)} results")

        for ticker, result, enriched in completed:
            if result:
                results[ticker] = result
                if enriched:
                    self._enriched_analyses[ticker] = enriched
                    self._store_enriched_analysis(ticker, enriched)
                self.logger.info(f"Analysis complete: {ticker} grade={result.grade}")

        self.logger.info(f"Concurrent analysis completed: {len(results)}/{len(holdings)} holdings")
        return results

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

            alternatives_data = alternatives_orch.match_alternatives_for_holdings(holdings_with_analysis, {})

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
