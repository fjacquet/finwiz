"""
Deep Analysis Pipeline - Functional Programming Approach.

Pure functions with composition for per-holding analysis.
Combines Python quantitative scoring ($0) with AI qualitative insights.

Architecture:
    1. collect_raw_data(ctx) -> RawData         [Python tools]
    2. calculate_quantitative(ctx, raw) -> Quant   [$0 Python]
    3. generate_qualitative(ctx, quant) -> Qual    [AI crew]
    4. synthesize(ctx, quant, qual) -> Enriched    [Python]
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from finwiz.analysis._helpers import (
    _build_sentiment_summary,
    _get_analysis_crew,  # noqa: F401 — re-exported for test compatibility
)
from finwiz.analysis.stages._synthesize_helpers import (  # noqa: F401
    _calculate_word_count,
    _count_unique_insights,
    _generate_executive_summary,
    _get_confidence,
    _get_investment_rationale,
)
from finwiz.analysis.stages.collect import collect_raw_data
from finwiz.analysis.stages.qualify import (  # noqa: F401
    _create_fallback_qualitative,
    _create_python_qualitative,
    _extract_qualitative,
    _has_qualitative_content,
    _run_qualitative_and_strategic_in_parallel,
    _safe_strategic,
    generate_qualitative,
)
from finwiz.analysis.stages.quantify import _result_to_quantitative, calculate_quantitative  # noqa: F401
from finwiz.analysis.stages.synthesize import (  # noqa: F401
    _apply_strategic_recompute,
    _bs_nd2,
    _compute_options_probabilities,
    _compute_scenario_probabilities,
    _synthesize_recommendation,
    synthesize_enriched_analysis,
)
from finwiz.flow_state_models import DeepAnalysisResult
from finwiz.schemas.hybrid_analysis import (
    EnrichedAnalysis,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AnalysisContext:
    """Immutable context for analysis pipeline."""

    ticker: str
    asset_class: str
    company_name: str = ""


# === COMPOSED PIPELINE (Main Entry Point) ===
def analyze_holding(
    ticker: str,
    asset_class: str,
    company_name: str = "",
    prefetched_data: dict[str, Any] | None = None,
) -> tuple[DeepAnalysisResult, EnrichedAnalysis]:
    """
    Complete analysis pipeline for a single holding.

    Composes:
    1. collect_raw_data (Python tools)
    2. calculate_quantitative (Python scorer - $0)
    3. generate_qualitative (AI crew)
    4. synthesize_enriched_analysis (Python)

    Args:
        ticker: Asset ticker symbol
        asset_class: Asset class (stock, etf, crypto)
        company_name: Optional company name
        prefetched_data: Batch-prefetched data dict (from BatchDataPreFetcher)

    Returns:
        Tuple of (DeepAnalysisResult for caching, EnrichedAnalysis for HTML)
    """
    start = time.time()
    ctx = AnalysisContext(ticker=ticker, asset_class=asset_class, company_name=company_name)

    logger.info(f"Starting analysis pipeline for {ticker} ({asset_class})")

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
    if strategic is not None and enriched.qualitative is not None and enriched.qualitative.strategic_analysis is not None:
        result = _apply_strategic_recompute(result, enriched)

    logger.info(f"Pipeline complete for {ticker}: {processing_time:.1f}s")
    return result, enriched
