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
from uuid import uuid4

from finwiz.analysis.stages._ledger import RunLedger
from finwiz.flow_state import DeepAnalysisResult, FinwizState
from finwiz.orchestrators.deep_analysis_data_collector import DeepAnalysisDataCollector
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


def _analyze_single_sync(
    holding: dict[str, Any],
    *,
    prefetched_data: Any,
    ledger: Any,
    logger: Any,
    make_synthetic_pending: Any,
) -> tuple[str, "DeepAnalysisResult | None", Any | None]:
    """Synchronous per-holding analysis (runs inside the thread pool).

    Extracted from ``run_deep_analysis_concurrent`` to reduce that method's
    cyclomatic complexity (C901) and statement count (PLR0915).  All
    previously-closed-over names are passed as explicit keyword arguments.
    """
    from finwiz.analysis import analyze_holding

    ticker = holding.get("ticker")
    asset_class = holding.get("asset_class")
    company_name = holding.get("name", "")

    if not ticker or not asset_class:
        return (ticker or "unknown", None, None)

    try:
        result, enriched = analyze_holding(
            ticker,
            asset_class,
            company_name,
            prefetched_data=prefetched_data,
            ledger=ledger,
            run_id=ledger.run_id,
        )
        return (ticker, result, enriched)
    except Exception as e:
        logger.error(f"Concurrent analysis failed for {ticker}: {e}", exc_info=True)
        # Surface the specific exception in a synthetic pending result so
        # the report renderer can show "Analyse interrompue : <Type> ..."
        # instead of falling back to the generic placeholder.
        pending = make_synthetic_pending(
            ticker=ticker,
            asset_class=asset_class,
            rationale=f"Analyse interrompue : {type(e).__name__} — voir logs",
        )
        return (ticker, pending, None)


async def _analyze_with_timeout(
    holding: dict[str, Any],
    *,
    executor: Any,
    semaphore: Any,
    loop: Any,
    timeout_seconds: int,
    prefetched_data: Any,
    ledger: Any,
    logger: Any,
    make_synthetic_pending: Any,
) -> tuple[str, "DeepAnalysisResult | None", Any | None]:
    """Per-holding timeout wrapper around ``_analyze_single_sync``.

    Extracted from ``run_deep_analysis_concurrent`` to reduce that method's
    cyclomatic complexity (C901) and statement count (PLR0915).  Per-holding
    timeout semantics are UNTOUCHED: the semaphore is acquired *before*
    the timer starts so timeouts only count active work, not queue-wait time.
    """
    import asyncio
    from functools import partial

    ticker = holding.get("ticker", "unknown")
    # Acquire semaphore BEFORE starting timeout - this ensures timeout
    # only counts time spent actually working, not time spent in queue
    async with semaphore:
        logger.debug(f"Starting analysis for {ticker} (timeout={timeout_seconds}s)")
        try:
            sync_fn = partial(
                _analyze_single_sync,
                holding,
                prefetched_data=prefetched_data,
                ledger=ledger,
                logger=logger,
                make_synthetic_pending=make_synthetic_pending,
            )
            return await asyncio.wait_for(
                loop.run_in_executor(executor, sync_fn),
                timeout=timeout_seconds,
            )
        except TimeoutError:
            logger.error(f"Analysis timed out for {ticker} after {timeout_seconds}s")
            # Failure recorded by ledger via @stage decorator on emit; no manual append needed.
            # Surface the timeout reason in a synthetic pending result so
            # the renderer can show "crew dépassé Xs — voir logs" instead
            # of a generic placeholder.
            pending = make_synthetic_pending(
                ticker=ticker,
                asset_class=str(holding.get("asset_class") or "unknown"),
                rationale=(f"Analyse interrompue : crew dépassé {timeout_seconds}s — voir logs"),
            )
            return (ticker, pending, None)
        except Exception as e:
            logger.error(f"Analysis failed for {ticker}: {e}", exc_info=True)
            # Failure recorded by ledger via @stage decorator on emit; no manual append needed.
            pending = make_synthetic_pending(
                ticker=ticker,
                asset_class=str(holding.get("asset_class") or "unknown"),
                rationale=(f"Analyse interrompue : {type(e).__name__} — voir logs"),
            )
            return (ticker, pending, None)


class DeepAnalysisOrchestrator:
    """Orchestrates deep analysis execution on portfolio holdings."""

    def __init__(self, state: FinwizState, **dependencies: Any) -> None:
        self.state = state
        self.logger = get_logger(self.__class__.__name__)
        self.batch_prefetch_config = dependencies.get("batch_prefetch_config")
        self.crew_factory = dependencies.get("crew_factory")
        self.integration_manager = dependencies.get("integration_manager")
        self.error_handler = dependencies.get("error_handler")

        # Data collector for raw data acquisition
        self.data_collector = DeepAnalysisDataCollector(state)

        # Enriched analysis storage (populated during analysis)
        self._enriched_analyses: dict[str, Any] = {}

        # Build the run ledger for this orchestrator instance and wire it to state.
        # The ledger is the source of truth for failed/analyzed tickers — the old
        # manual _failed_holdings list is now a read-only property derived from it.
        run_id = getattr(state, "run_id", None) or uuid4().hex[:12]
        self._ledger = RunLedger(
            run_id=run_id,
            artifact_dir=Path("output/run_ledger"),
        )
        self.state.run_ledger = self._ledger

        # Initialize DataSourceOrchestrator for multi-source data acquisition
        from finwiz.data.data_source_orchestrator import DataSourceOrchestrator

        self.data_orchestrator = DataSourceOrchestrator(
            total_timeout=10.0,
            per_source_timeout=3.0,
            enable_validation=True,
        )

    @property
    def _failed_holdings(self) -> list[str]:
        """Tickers without an OK terminal-stage outcome — derived from the ledger.

        Replaces the old manual list. The @stage decorator on the `emit` stage
        records FAILED entries automatically; this property surfaces them for
        logging and coverage reporting without any manual append calls.
        """
        return self._ledger.failed_tickers()

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

        # Deep analysis ALWAYS runs — no env-var gate.
        # Reason: this is a financial trust system. A "✅ completed" report on
        # zero analyses is worse than a hard failure. The previous
        # DEEP_PORTFOLIO_ANALYSIS kill switch defaulted to "false" and silently
        # no-op'd the entire phase, producing reports with placeholder grades
        # that users mistook for real verdicts.

        portfolio_review = self.state.portfolio_review
        if not portfolio_review or not portfolio_review.get("holdings"):
            self.logger.warning("No portfolio holdings available for deep analysis")
            return {}

        holdings = portfolio_review.get("holdings", [])
        self.logger.info(f"Starting deep analysis for {len(holdings)} holdings")

        # Tell the ledger the expected total so coverage() can compute pending counts
        # even before all emit stages have fired.
        self._ledger.set_total(len(holdings))

        # Step 0: Batch prefetch data for all holdings
        from finwiz.orchestrators.batch_prefetch_runner import run_batch_prefetch

        run_batch_prefetch(self.state, holdings, self.logger)

        # Step 1: Run deep analysis on all holdings CONCURRENTLY.
        # If the runner itself raises (executor init, asyncio loop, config
        # error — NOT per-holding errors which are isolated by the gather's
        # return_exceptions=True), re-raise so the flow can't continue and
        # report success on a Phase 3 crash. State is updated first so the
        # post-flow cost summary (in flows/orchestrator.py try/except) can
        # still see the failure context.
        try:
            deep_results = await self.run_deep_analysis_concurrent(holdings)
        except Exception as e:
            self.logger.critical(f"❌ Deep analysis runner crashed: {e}", exc_info=True)
            self.state.deep_analysis_success = False
            self.state.deep_analysis_error = str(e)
            self.state.deep_analysis_coverage = (0, len(holdings))
            raise

        # Honest success accounting — success only if we actually produced analyses.
        # Coverage tuple (analyzed, total) is read by the reporting layer to
        # render a banner showing how many holdings have real analysis.
        analyzed = len(deep_results)
        total = len(holdings)
        self.state.deep_analysis_results = deep_results
        self.state.deep_analysis_coverage = (analyzed, total)
        self.state.deep_analysis_success = analyzed > 0

        if analyzed == 0:
            # FAIL LOUDLY from the orchestrator. This is the single source of
            # truth for "Phase 3 produced nothing" — fires regardless of which
            # flow path called us (sequential body vs @listen callback). The
            # flow-level wrapper (try/except: _log_post_flow_summaries; raise)
            # ensures cost summary still fires before this propagates.
            failed_preview = self._failed_holdings[:10]
            ellipsis = "..." if len(self._failed_holdings) > 10 else ""
            msg = f"Deep analysis produced 0 results for {total} holdings. Failed tickers: {failed_preview}{ellipsis}"
            self.logger.critical(f"❌ {msg}")
            raise RuntimeError(msg)
        if analyzed < total:
            missing = total - analyzed
            self.logger.warning(
                f"⚠️ Partial coverage: {analyzed}/{total} holdings analyzed, "
                f"{missing} pending. Failed: {self._failed_holdings[:10]}{'...' if len(self._failed_holdings) > 10 else ''}"
            )
        else:
            self.logger.info(f"✅ Deep analysis complete: {analyzed}/{total} holdings analyzed")

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

        # Ensure macro_snapshot is set on state for report-time access (Phase 16)
        self._ensure_macro_snapshot_on_state()

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
                result, enriched = analyze_holding(ticker, asset_class, company_name, ledger=self._ledger, run_id=self._ledger.run_id)

                # ADR-011: copy tactical price targets onto the result so the merge layer
                # can propagate them to HoldingDecision without reaching back into _enriched_analyses.
                if enriched is not None and getattr(enriched.quantitative, "price_targets", None) is not None:
                    result = result.model_copy(update={"price_targets": enriched.quantitative.price_targets})

                results[ticker] = result

                # Store enriched analysis for HTML generation
                self._enriched_analyses[ticker] = enriched
                self._store_enriched_analysis(ticker, enriched)

                self.logger.info(f"Analysis complete: {ticker} grade={result.grade} score={result.composite_score:.2f}")

            except Exception as e:
                self.logger.error(f"Analysis failed for {ticker}: {e}", exc_info=True)
                # Surface the specific exception so the report can show
                # "Analyse interrompue : <Type> ..." instead of falling back to
                # the generic "Analyse approfondie non disponible" placeholder.
                results[ticker] = self._make_synthetic_pending(
                    ticker=ticker,
                    asset_class=asset_class,
                    rationale=f"Analyse interrompue : {type(e).__name__} — voir logs",
                )

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

            # Store in simplified output directory: output/{asset_class}/
            # All deep analysis reports go directly to output/stock/, output/etf/, output/crypto/
            output_dir = Path(f"output/{enriched.asset_class}")
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

        except OSError as e:
            # I/O error writing JSON or HTML to disk — logged only; the ledger
            # already recorded the emit stage outcome for this ticker.
            self.logger.error(f"Failed to store enriched analysis for {ticker}: {e}", exc_info=True)
        except Exception as e:
            self.logger.error(f"Failed to store enriched analysis for {ticker}: {e}", exc_info=True)

    def get_enriched_analysis(self, ticker: str) -> Any | None:
        """Get stored enriched analysis for a ticker."""
        return self._enriched_analyses.get(ticker)

    @staticmethod
    def _make_synthetic_pending(ticker: str, asset_class: str, rationale: str) -> DeepAnalysisResult:
        """Build a synthetic pending result so the rationale reaches the renderer.

        Without this, the orchestrator returned ``(ticker, None, None)`` and
        downstream merge / renderer applied a generic "Analyse approfondie non
        disponible" placeholder — losing the *specific* reason (timeout,
        breaker open, etc.) that the user needs to see. Mirrors the shape
        produced by ``finwiz.analysis.stages.emit._emit_pending``.
        """
        return DeepAnalysisResult.model_construct(
            ticker=ticker,
            asset_class=asset_class or "unknown",
            crew_name="pipeline",
            composite_score=0.0,
            grade="N/A",
            recommendation="WAIT",
            rationale=rationale,
            risk_details={},
            fundamental_score=None,
            technical_score=None,
            risk_score=None,
            fundamental_details={},
            technical_details={},
            data_freshness_hours=0.0,
            confidence_level=0.0,
            confidence="low",
            warnings=["upstream stage failure — analysis incomplete"],
            data_quality=None,
            lineage=None,
            cached=False,
            sentiment_score=None,
            sentiment_confidence=None,
            macro_score=None,
            macro_regime=None,
        )

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

        from finwiz.config.performance.performance_config import get_batch_size

        # Get max_workers from config if not specified
        if max_workers is None:
            max_workers = get_batch_size()

        self.logger.info(f"Starting concurrent deep analysis: {len(holdings)} holdings, max_workers={max_workers}")

        # Ensure macro_snapshot is set on state for report-time access (Phase 16)
        self._ensure_macro_snapshot_on_state()

        results: dict[str, DeepAnalysisResult] = {}
        self._enriched_analyses = {}

        # Use a semaphore to limit concurrency - this ensures timeout starts when work begins
        # NOT when it's queued (which was the bug causing all timeouts at same second)
        loop = asyncio.get_running_loop()
        completed: list[tuple[str, DeepAnalysisResult | None, Any | None]] = []
        semaphore = asyncio.Semaphore(max_workers)

        # Per-holding timeout - prevents one stuck ticker blocking all.
        # Default 900 s after the 2026-04-29 run (DELL succeeded at 1488 s,
        # asyncio.wait_for cannot interrupt sync crew.kickoff() in a thread).
        per_holding_timeout = int(os.getenv("FINWIZ_HOLDING_TIMEOUT", "900"))

        # Resolve prefetched_data once so the helper receives the value, not self
        prefetched_data = self.state.prefetched_data if self.state.batch_prefetch_enabled else None

        # NO AGGREGATE TIMEOUT. Each holding has its own per_holding_timeout
        # (_analyze_with_timeout). An aggregate cap would discard already
        # completed work when one slow ticker pushes total runtime over —
        # which is exactly what discarded XRP-USD's grade=D verdict on
        # 2026-04-27 (XRP finished at 09:00:12, the 1800s aggregate timeout
        # fired at 09:04:55 and threw the result away). With 60+ holdings,
        # an outer cap is the wrong abstraction — let total runtime scale
        # with N at the per-holding budget.
        # See memory/feedback_no_aggregate_timeouts.md for the principle.
        executor = ThreadPoolExecutor(max_workers=max_workers * 2)
        try:
            # Submit all holdings - semaphore ensures only max_workers run at a
            # time and per-holding timeout starts when semaphore is acquired.
            futures = [
                _analyze_with_timeout(
                    holding,
                    executor=executor,
                    semaphore=semaphore,
                    loop=loop,
                    timeout_seconds=per_holding_timeout,
                    prefetched_data=prefetched_data,
                    ledger=self._ledger,
                    logger=self.logger,
                    make_synthetic_pending=self._make_synthetic_pending,
                )
                for holding in holdings
            ]
            # return_exceptions=True so one holding's escaped exception doesn't
            # cancel siblings. Per-holding handlers (_analyze_with_timeout +
            # _analyze_single_sync) already log failures — this is defense-in-depth.
            results_or_excs = await asyncio.gather(*futures, return_exceptions=True)
            for item in results_or_excs:
                if isinstance(item, BaseException):
                    self.logger.error(f"Unhandled exception in gather: {item!r}", exc_info=item)
                    continue
                completed.append(item)
        finally:
            # CRITICAL: Don't wait for stuck threads - they may be deadlocked.
            # cancel_futures=True attempts to cancel pending futures (Python 3.9+)
            self.logger.info("Shutting down executor (not waiting for stuck threads)")
            executor.shutdown(wait=False, cancel_futures=True)

        self.logger.info(f"asyncio.gather completed with {len(completed)} results")

        for ticker, result, enriched in completed:
            if result:
                # ADR-011: copy tactical price targets onto the result so the merge layer
                # can propagate them to HoldingDecision without reaching back into _enriched_analyses.
                if enriched is not None and getattr(enriched.quantitative, "price_targets", None) is not None:
                    result = result.model_copy(update={"price_targets": enriched.quantitative.price_targets})
                results[ticker] = result
                if enriched:
                    self._enriched_analyses[ticker] = enriched
                    self._store_enriched_analysis(ticker, enriched)
                self.logger.info(f"Analysis complete: {ticker} grade={result.grade}")

        self.logger.info(f"Concurrent analysis completed: {len(results)}/{len(holdings)} holdings")
        return results

    def _ensure_macro_snapshot_on_state(self) -> None:
        """Set macro_snapshot on FinwizState if not already set.

        Collects macro data once per session for report-time access (Phase 16).
        """
        if self.state.macro_snapshot is not None:
            return

        try:
            from finwiz.data.sentiment_collector import SentimentMacroCollector

            collector = SentimentMacroCollector()
            macro = collector.collect_macro()
            if macro is not None:
                snapshot_dict: dict[str, Any] = macro.model_dump() if hasattr(macro, "model_dump") else dict(macro)  # type: ignore[arg-type]
                self.state.macro_snapshot = snapshot_dict
                self.logger.info(f"Macro snapshot set on FinwizState: {macro.get_market_regime()} regime")
        except Exception as e:
            self.logger.debug(f"Macro snapshot collection for state skipped: {e}")

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
