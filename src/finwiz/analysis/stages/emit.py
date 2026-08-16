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

    # v5.2: copy fact_pack from enriched.qualitative onto the result so the merge
    # layer can populate HoldingDecision.fact_pack for the report renderer.
    if enriched.qualitative is not None and enriched.qualitative.fact_pack is not None:
        result = result.model_copy(update={"fact_pack": enriched.qualitative.fact_pack})

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

    When the underlying ``reason`` indicates a circuit-breaker fast-fail (the
    literal ``"Circuit breaker open"`` raised from ``crew_execution.py``), use
    a more specific French phrasing so users can distinguish a genuine pending
    holding from one that was skipped because the upstream breaker opened.
    """
    if reason and "Circuit breaker open" in reason:
        pending_rationale = f"Analyse interrompue : circuit breaker ouvert — réessayer après cooldown ({reason})"
    elif reason:
        pending_rationale = f"Analyse en attente — ne pas décider sur ce holding. {reason}"
    else:
        pending_rationale = "Analyse en attente — ne pas décider sur ce holding"
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


def _pending_enriched(ctx: StageContext, reason: str | None = None) -> EnrichedAnalysis:
    """Build the EnrichedAnalysis that accompanies a pending verdict.

    ``{TICKER}_enriched.json`` is serialized from this object, and it is what the
    report renderer and every downstream consumer read. It therefore has to state
    a refusal explicitly rather than fall back to the schema's defaults.

    This exists because it previously did not: the pipeline returned a bare
    ``EnrichedAnalysis.model_construct()``, which took the defaults and wrote
    ``final_grade="C"``, ``final_score=0.5``, ``final_recommendation="HOLD"`` to
    disk — with ``ticker=""`` and both analysis sections ``None`` — for a holding
    the pipeline had just refused to analyse. A reader of that file saw a
    confident middling hold where the truth was "we don't know".
    """
    return EnrichedAnalysis(
        ticker=ctx.ticker,
        quantitative=None,
        qualitative=None,
        final_grade="N/A",
        final_score=0.0,
        final_recommendation="WAIT",
        recommendation_confidence="LOW",
        executive_summary="Analyse en attente — ne pas décider sur ce holding.",
        investment_rationale=(f"Analyse incomplète : {reason}" if reason else "Analyse incomplète : échec d'une étape amont."),
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
