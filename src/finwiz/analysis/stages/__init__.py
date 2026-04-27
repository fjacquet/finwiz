"""Stage modules for the deep-analysis pipeline."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

from finwiz.analysis._helpers import _build_sentiment_summary
from finwiz.analysis.stages.collect import collect_raw_data
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

    Mirrors the original analyze_holding control flow. A later task (D-phase)
    promotes each call site to use the @stage decorator and StageResult envelope.
    """
    start = time.time()

    logger.info(f"Starting analysis pipeline for {ctx.ticker} ({ctx.asset_class})")

    # Pipeline composition
    raw_data = collect_raw_data(ctx, prefetched_data=prefetched_data)
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
