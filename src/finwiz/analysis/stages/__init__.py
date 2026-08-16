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
from finwiz.analysis.stages.emit import _emit_pending, _pending_enriched, emit
from finwiz.analysis.stages.emit import build_verdict as build_verdict
from finwiz.analysis.stages.fact_pack import fact_pack
from finwiz.analysis.stages.qualify import _run_qualitative_and_strategic_in_parallel as _run_qualitative_and_strategic_in_parallel
from finwiz.analysis.stages.qualify import qualify
from finwiz.analysis.stages.quantify import calculate_quantitative as calculate_quantitative
from finwiz.analysis.stages.quantify import quantify
from finwiz.analysis.stages.synthesize import _compute_options_probabilities, synthesize
from finwiz.analysis.stages.synthesize import synthesize_enriched_analysis as synthesize_enriched_analysis
from finwiz.schemas.hybrid_analysis import EnrichedAnalysis

if TYPE_CHECKING:
    from finwiz.analysis.deep_analysis_pipeline import AnalysisContext
    from finwiz.flow_state_models import DeepAnalysisResult

logger = logging.getLogger(__name__)


def run_pipeline(
    ctx: AnalysisContext,
    prefetched_data: dict[str, Any] | None = None,
) -> tuple[DeepAnalysisResult, EnrichedAnalysis]:
    """Sequential orchestration of the five deep-analysis stages.

    Any stage that returns FAILED (payload is None) immediately short-circuits to
    an AnalysePending placeholder. Silent fall-through to downstream stages is
    structurally impossible: every FAILED outcome exits early via _emit_pending.
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

    # Phase 1: Collect — any FAILED result short-circuits to AnalysePending.
    cr = collect(stage_ctx)
    if cr.payload is None:
        return _emit_pending(stage_ctx, reason=cr.provenance.reason), _pending_enriched(stage_ctx, reason=cr.provenance.reason)
    raw_data: dict[str, Any] = cr.payload.data

    # Phase 2: Quantify — any FAILED result short-circuits to AnalysePending.
    options_probs = _compute_options_probabilities(raw_data)  # None for crypto/niche ETFs
    qr = quantify(stage_ctx, raw_data)
    if qr.payload is None:
        return _emit_pending(stage_ctx, reason=qr.provenance.reason), _pending_enriched(stage_ctx, reason=qr.provenance.reason)
    quant = qr.payload
    # Pull the partial result stashed by quantify into stage_ctx.extras.
    # synthesize is the last writer of partial_result; nothing after it re-assigns.
    result = stage_ctx.extras.get("partial_result")
    if result is None:
        return _emit_pending(stage_ctx, reason="quantify stage did not seed partial_result"), _pending_enriched(stage_ctx, reason="quantify stage did not seed partial_result")

    # Phase 2c: fact_pack (v5.2)
    fpr = fact_pack(stage_ctx, raw_data)
    if fpr.payload is None:
        # FAILED — no cache and Perplexity unavailable. Trust-spine policy:
        # halt holding to AnalysePending rather than running ungrounded.
        return _emit_pending(stage_ctx, reason=fpr.provenance.reason), _pending_enriched(stage_ctx, reason=fpr.provenance.reason)
    stage_ctx.extras["fact_pack"] = fpr.payload  # FactPack with freshness in {"fresh","recent","stale"}

    # Phase 3: Qualify — any FAILED result short-circuits to AnalysePending.
    # Strategic Perplexity research runs independently for stocks (not via the legacy
    # parallel helper, which silently swallows qualify failures).
    qr3 = qualify(stage_ctx, quant, raw_data)
    if qr3.payload is None:
        return _emit_pending(stage_ctx, reason=qr3.provenance.reason), _pending_enriched(stage_ctx, reason=qr3.provenance.reason)
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

    # Phase 4: Synthesize — any FAILED result short-circuits to AnalysePending.
    processing_time = time.time() - start
    sentiment_summary = _build_sentiment_summary(raw_data)
    stage_ctx.extras["processing_time"] = processing_time
    stage_ctx.extras["sentiment_summary"] = sentiment_summary
    stage_ctx.extras["options_probs"] = options_probs
    # Thread qualify outcome so synthesize can propagate confidence="low" on DEGRADED.
    stage_ctx.extras["qualify_outcome"] = qr3.provenance.outcome
    sr4 = synthesize(stage_ctx, quant, qual, raw_data)
    if sr4.payload is None:
        return _emit_pending(stage_ctx, reason=sr4.provenance.reason), _pending_enriched(stage_ctx, reason=sr4.provenance.reason)
    enriched = sr4.payload

    # Phase 5: Emit — synthesize is the last writer of partial_result; do not
    # re-assign here. emit reads stage_ctx.extras["partial_result"] directly so it
    # sees the confidence downgrade that synthesize may have applied.
    stage_ctx.extras["strategic"] = strategic
    er = emit(stage_ctx, enriched)
    if er.payload is None:
        # Emit stage failed — produce pending placeholder.
        final_result = _emit_pending(stage_ctx, reason=er.provenance.reason)
    else:
        final_result = er.payload

    # Return the (DeepAnalysisResult, EnrichedAnalysis) tuple to match the legacy contract.
    return final_result, enriched
