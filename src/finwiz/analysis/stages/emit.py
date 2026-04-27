"""Emit stage: produce the final (DeepAnalysisResult, EnrichedAnalysis) pair."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from finwiz.analysis.stages._resilience import StageContext, stage
from finwiz.analysis.stages.synthesize import _apply_strategic_recompute
from finwiz.flow_state_models import DeepAnalysisResult
from finwiz.schemas.hybrid_analysis import EnrichedAnalysis

if TYPE_CHECKING:
    from finwiz.analysis.deep_analysis_pipeline import AnalysisContext

logger = logging.getLogger(__name__)


def _build_verdict_inner(
    ctx: AnalysisContext,
    result: DeepAnalysisResult,
    enriched: EnrichedAnalysis,
    strategic: object | None,
    processing_time: float,
) -> tuple[DeepAnalysisResult, EnrichedAnalysis]:
    """Original build_verdict body — extracted for testability.

    Re-applies the strategic recompute when a strategic analysis is available,
    then logs completion and returns the finalised (result, enriched) pair.
    """
    if strategic is not None and enriched.qualitative is not None and enriched.qualitative.strategic_analysis is not None:
        result = _apply_strategic_recompute(result, enriched)

    logger.info(f"Pipeline complete for {ctx.ticker}: {processing_time:.1f}s")
    return result, enriched


@stage(name="emit", timeout_s=10, retries=0)
def emit(ctx: StageContext, enriched: EnrichedAnalysis) -> DeepAnalysisResult:
    """Stage entry: emit the user-visible verdict from EnrichedAnalysis."""
    analysis_ctx = ctx.extras["analysis_ctx"]
    partial_result = ctx.extras["partial_result"]
    strategic = ctx.extras.get("strategic")
    processing_time: float = ctx.extras.get("processing_time", 0.0)
    final_result, _ = _build_verdict_inner(analysis_ctx, partial_result, enriched, strategic, processing_time)
    return final_result


def _emit_pending(ctx: StageContext, reason: str | None = None) -> DeepAnalysisResult:
    """Build the 'Analyse en attente' placeholder used when an upstream stage failed.

    Used by run_pipeline when collect/quantify/qualify/synthesize emit FAILED — the
    pipeline cannot produce a real verdict so it emits a flagged placeholder that
    the report renderer maps to 'Analyse en attente'. Mirrors the v0.3.0 fix.
    """
    pending_rationale = f"Analyse en attente — ne pas décider sur ce holding. {reason}" if reason else "Analyse en attente — ne pas décider sur ce holding"
    return DeepAnalysisResult.model_construct(
        ticker=ctx.ticker,
        asset_class="unknown",
        crew_name="pipeline",
        composite_score=0.0,
        grade="N/A",
        recommendation="WAIT",
        rationale=pending_rationale,
        risk_details={},
        fundamental_score=None,
        technical_score=None,
        risk_score=None,
        fundamental_details={},
        technical_details={},
        data_freshness_hours=0.0,
        confidence_level=0.0,
        warnings=["upstream stage failure — analysis incomplete"],
        data_quality=None,
        lineage=None,
        cached=False,
        sentiment_score=None,
        sentiment_confidence=None,
        macro_score=None,
        macro_regime=None,
    )


# Legacy shim — callers outside run_pipeline continue to work unchanged.
def build_verdict(
    ctx: AnalysisContext,
    result: DeepAnalysisResult,
    enriched: EnrichedAnalysis,
    strategic: object | None,
    processing_time: float,
) -> tuple[DeepAnalysisResult, EnrichedAnalysis]:
    """Legacy entry point: delegates to _build_verdict_inner."""
    return _build_verdict_inner(ctx, result, enriched, strategic, processing_time)
