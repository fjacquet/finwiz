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
from finwiz.analysis.stages.qualify import _run_qualitative_and_strategic_in_parallel, qualify
from finwiz.analysis.stages.quantify import calculate_quantitative, quantify
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

    Phases 1-2 (collect, quantify) use the @stage decorator and StageResult contract.
    Phases 3-5 use legacy entry points until D3-D5 migrate them.
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

    # Phase 2: Quantify — typed StageResult contract via @stage decorator.
    options_probs = _compute_options_probabilities(raw_data)  # None for crypto/niche ETFs
    qr = quantify(stage_ctx, raw_data)
    if qr.payload is None:
        # Scorer failed; fall through with a sentinel so downstream stages can still run.
        quant = calculate_quantitative(ctx, raw_data)[1]
    else:
        quant = qr.payload
    # Pull the partial result stashed by quantify (or recompute for fallback path).
    result = stage_ctx.extras.get("partial_result") or calculate_quantitative(ctx, raw_data)[0]

    # Phase 3: Qualify — typed StageResult contract via @stage decorator.
    # Strategic Perplexity research still runs in parallel via the legacy parallel helper;
    # only the qualitative crew call is migrated here. The parallel helper internally
    # calls generate_qualitative (the legacy shim) so the strategic path is unaffected.
    qr3 = qualify(stage_ctx, quant, raw_data)
    if qr3.payload is None:
        # Qualify failed; fall through using the parallel helper for both qual + strategic.
        qual, strategic = _run_qualitative_and_strategic_in_parallel(ctx, quant, raw_data)
    else:
        qual = qr3.payload
        # Run strategic research independently for stocks.
        from finwiz.analysis.stages.qualify import _safe_strategic

        do_strategic = ctx.asset_class == "stock"
        sector = str(raw_data.get("sector") or raw_data.get("Sector") or "")
        industry = str(raw_data.get("industry") or raw_data.get("Industry") or "")
        description = str(raw_data.get("longBusinessSummary") or raw_data.get("description") or raw_data.get("company_description") or "")
        strategic = _safe_strategic(ctx.ticker, sector, industry, description) if do_strategic else None
    if strategic is not None:
        qual = qual.model_copy(update={"strategic_analysis": strategic})

    # Phase 4 synthesize — re-derives composite with the AI-rated strategic component.
    processing_time = time.time() - start
    sentiment_summary = _build_sentiment_summary(raw_data)
    enriched = synthesize_enriched_analysis(ctx, quant, qual, processing_time, sentiment_summary=sentiment_summary, options_probs=options_probs)

    # Phase 5 emit — final assembly: strategic recompute + return.
    return build_verdict(ctx, result, enriched, strategic, processing_time)
