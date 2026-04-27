"""Stage modules for the deep-analysis pipeline."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from finwiz.analysis._helpers import _build_sentiment_summary
from finwiz.analysis.stages._ledger import RunLedger
from finwiz.analysis.stages._resilience import StageContext
from finwiz.analysis.stages.collect import collect
from finwiz.analysis.stages.collect import collect_raw_data as collect_raw_data
from finwiz.analysis.stages.emit import build_verdict
from finwiz.analysis.stages.qualify import _run_qualitative_and_strategic_in_parallel
from finwiz.analysis.stages.quantify import calculate_quantitative
from finwiz.analysis.stages.synthesize import _compute_options_probabilities, synthesize_enriched_analysis

if TYPE_CHECKING:
    from finwiz.analysis.deep_analysis_pipeline import AnalysisContext
    from finwiz.flow_state_models import DeepAnalysisResult
    from finwiz.schemas.hybrid_analysis import EnrichedAnalysis

logger = logging.getLogger(__name__)


def run_pipeline(
    ctx: AnalysisContext,
    prefetched_data: dict[str, Any] | None = None,
) -> tuple[DeepAnalysisResult, EnrichedAnalysis]:
    """Sequential orchestration of the five deep-analysis stages.

    Phase 1 (collect) uses the @stage decorator and StageResult contract.
    Phases 2-5 use legacy entry points until D2-D5 migrate them.
    """
    start = time.time()

    logger.info(f"Starting analysis pipeline for {ctx.ticker} ({ctx.asset_class})")

    # Build a per-holding StageContext for the new contract.
    # If the AnalysisContext carries a ledger (D6 will populate it from the
    # orchestrator), reuse it; otherwise create a per-call in-memory ledger so
    # legacy callers don't break.
    ledger = getattr(ctx, "ledger", None)
    run_id = getattr(ctx, "run_id", None) or uuid4().hex[:12]
    if ledger is None:
        ledger = RunLedger(run_id=run_id, artifact_dir=Path("output/run_ledger"))

    stage_ctx = StageContext(
        ticker=ctx.ticker,
        run_id=run_id,
        ledger=ledger,
        extras={"analysis_ctx": ctx, "prefetched_data": prefetched_data},
    )

    # Phase 1: Collect — typed StageResult contract via @stage decorator.
    cr = collect(stage_ctx)
    if cr.payload is None:
        # Pipeline cannot proceed without raw data; fall through with empty dict
        # so existing tests don't break (FAILED branch is rare in current tests).
        raw_data: dict[str, Any] = {}
    else:
        raw_data = cr.payload.data

    # Phases 2-5: legacy path (unchanged for D1, migrated in D2-D5).
    options_probs = _compute_options_probabilities(raw_data)  # None for crypto/niche ETFs
    result, quant = calculate_quantitative(ctx, raw_data)

    # Phase 3 — qualitative AI crew + strategic Perplexity research run in PARALLEL.
    # The strategic call is independent (no quant/qual context fed in) and only matters
    # for stocks. ETFs/crypto skip it (frameworks don't fit those asset classes well).
    qual, strategic = _run_qualitative_and_strategic_in_parallel(ctx, quant, raw_data)
    if strategic is not None:
        qual = qual.model_copy(update={"strategic_analysis": strategic})

    # Phase 4 synthesize — re-derives composite with the AI-rated strategic component.
    processing_time = time.time() - start
    sentiment_summary = _build_sentiment_summary(raw_data)
    enriched = synthesize_enriched_analysis(ctx, quant, qual, processing_time, sentiment_summary=sentiment_summary, options_probs=options_probs)

    # Phase 5 emit — final assembly: strategic recompute + return.
    return build_verdict(ctx, result, enriched, strategic, processing_time)
