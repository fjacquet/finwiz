"""Synthesize stage: combine quantitative + qualitative into EnrichedAnalysis."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from finwiz.analysis.stages._resilience import StageContext, stage
from finwiz.analysis.stages._synthesize_helpers import (
    _calculate_word_count,
    _count_unique_insights,
    _generate_executive_summary,
    _get_confidence,
    _get_investment_rationale,
)
from finwiz.analysis.stages._synthesize_options import (  # noqa: F401
    _bs_nd2,
    _compute_options_probabilities,
)
from finwiz.schemas.hybrid_analysis import (
    EnrichedAnalysis,
    QualitativeInsights,
    QuantitativeAnalysis,
)
from finwiz.schemas.hybrid_analysis.qualitative import ScenarioProbabilities

if TYPE_CHECKING:
    from finwiz.analysis.deep_analysis_pipeline import AnalysisContext
    from finwiz.flow_state_models import DeepAnalysisResult

logger = logging.getLogger(__name__)


def _synthesize_recommendation(quant: QuantitativeAnalysis, qual: QualitativeInsights) -> tuple[str, str | None]:
    """Return (final_recommendation, conflict_note | None). Python wins on conflicts."""
    python_rec = quant.preliminary_recommendation
    ai_rec = qual.investment_synthesis.final_recommendation if qual.investment_synthesis else "HOLD"

    if python_rec == ai_rec:
        return python_rec, None

    conflict = f"L'IA suggère {ai_rec} ; l'analyse quantitative Python (score={quant.composite_score:.2f}, grade={quant.grade}) prend la priorité selon le principe AI Minimalism."
    logger.warning(f"Recommendation conflict: Python={python_rec}, AI={ai_rec}. Using Python.")
    return python_rec, conflict


def _compute_scenario_probabilities(quant: QuantitativeAnalysis) -> ScenarioProbabilities:
    """Derive scenario probabilities from Python quantitative scores. $0, deterministic.

    Combines composite_score (0.0-1.0) and normalised risk_score:
      signal=0.0 (worst)  → bull=0.10, base=0.30, bear=0.60
      signal=0.5 (median) → bull≈0.33, base≈0.32, bear=0.35
      signal=1.0 (best)   → bull=0.55, base=0.35, bear=0.10
    """
    risk_normalized = 1.0 - min(quant.risk_score / 5.0, 1.0)
    signal = 0.7 * quant.composite_score + 0.3 * risk_normalized
    bull = round(0.10 + 0.45 * signal, 2)
    bear = round(0.60 - 0.50 * signal, 2)
    base = round(1.0 - bull - bear, 2)
    return ScenarioProbabilities(bull=bull, base=base, bear=bear)


def _apply_strategic_recompute(result: DeepAnalysisResult, enriched: EnrichedAnalysis) -> DeepAnalysisResult:
    """Re-derive composite/grade/recommendation using the AI-rated strategic score.

    Mutates the cached :class:`DeepAnalysisResult` and aligns ``enriched`` so the
    final report shows the recomputed values.
    """
    from finwiz.scoring.deep_analysis_scorer import DeepAnalysisScorer

    qual = enriched.qualitative
    if qual is None or qual.strategic_analysis is None:
        return result
    strategic_score = qual.strategic_analysis.composite_strategic_score
    if strategic_score is None:
        return result

    quant = enriched.quantitative
    fundamental = result.fundamental_score if result.fundamental_score is not None else (quant.fundamental_score if quant else 0.5)
    technical = result.technical_score if result.technical_score is not None else (quant.technical_score if quant else 0.5)
    raw_risk = result.risk_score if result.risk_score is not None else (quant.risk_score if quant else 2.5)
    # Risk is stored on a 0-5 scale where lower = better; convert to 0-1 favorability.
    risk_favorability = max(0.0, min(1.0, 1.0 - (raw_risk / 5.0)))

    scorer = DeepAnalysisScorer()
    new_composite, new_grade, new_recommendation = scorer.recompute_with_strategic(
        fundamental_score=fundamental,
        technical_score=technical,
        risk_score=risk_favorability,
        strategic_score=strategic_score,
    )

    logger.info(
        f"Strategic recompute for {result.ticker}: "
        f"{result.composite_score:.3f} ({result.grade}/{result.recommendation}) -> "
        f"{new_composite:.3f} ({new_grade}/{new_recommendation}) "
        f"[strategic={strategic_score:.2f}]"
    )

    enriched.final_score = new_composite
    enriched.final_grade = new_grade
    enriched.final_recommendation = new_recommendation
    return result.model_copy(
        update={
            "composite_score": new_composite,
            "grade": new_grade,
            "recommendation": new_recommendation,
        }
    )


def _synthesize_inner(
    ctx: AnalysisContext,
    quant: QuantitativeAnalysis,
    qual: QualitativeInsights,
    processing_time: float = 0.0,
    sentiment_summary: dict[str, Any] | None = None,
    options_probs: ScenarioProbabilities | None = None,
) -> EnrichedAnalysis:
    """Original synthesize body — extracted for testability."""
    from finwiz.analysis.stages._qualify_fallbacks import _create_python_qualitative

    logger.info(f"Synthesizing enriched analysis for {ctx.ticker}")

    # Python wins on recommendation conflicts
    final_rec, recommendation_conflict = _synthesize_recommendation(quant, qual)

    # Priority: options-implied > AI probs > Python formula (AI probs are uncalibrated)
    if options_probs is not None:
        final_probs = options_probs
        logger.info(f"Options-implied scenario probabilities used for {ctx.ticker}")
    elif qual.investment_synthesis and qual.investment_synthesis.scenario_probabilities is not None:
        final_probs = qual.investment_synthesis.scenario_probabilities
    else:
        final_probs = _compute_scenario_probabilities(quant)
        logger.info(f"Scenario probabilities computed from Python scores for {ctx.ticker} (no options data)")

    # Lazy Python fallback — computed once, shared across all empty-section checks
    _py_qual: QualitativeInsights | None = None

    def _py() -> QualitativeInsights:
        nonlocal _py_qual
        if _py_qual is None:
            _py_qual = _create_python_qualitative(ctx, quant)
        return _py_qual

    if qual.investment_synthesis is None:
        # AI returned null for the whole object — build from Python and inject probs
        py_synth = _py().investment_synthesis
        if py_synth is not None:
            qual = qual.model_copy(update={"investment_synthesis": py_synth.model_copy(update={"scenario_probabilities": final_probs})})
            logger.info(f"Null AI investment_synthesis replaced with Python content for {ctx.ticker}")
    else:
        # AI returned an object — inject probs then fill any empty prose
        ai_synth = qual.investment_synthesis  # non-None confirmed by else branch
        updated_synth = ai_synth.model_copy(update={"scenario_probabilities": final_probs})
        qual = qual.model_copy(update={"investment_synthesis": updated_synth})
        if not (updated_synth.investment_thesis or updated_synth.bull_case or updated_synth.base_case or updated_synth.bear_case):
            py_s = _py().investment_synthesis
            if py_s is not None:
                qual = qual.model_copy(
                    update={
                        "investment_synthesis": updated_synth.model_copy(
                            update={
                                "investment_thesis": py_s.investment_thesis,
                                "bull_case": py_s.bull_case,
                                "base_case": py_s.base_case,
                                "bear_case": py_s.bear_case,
                                "action_plan": updated_synth.action_plan or py_s.action_plan,
                            }
                        )
                    }
                )
                logger.info(f"Empty AI prose filled with Python content for {ctx.ticker}")

    # Fill other empty sections (fundamental_context, technical_strategy, contextual_risks)
    fc, ts, cr = qual.fundamental_context, qual.technical_strategy, qual.contextual_risks
    needs_fc = not fc or not (fc.industry_analysis or fc.growth_drivers or fc.competitive_positioning)
    needs_ts = not ts or not (ts.support_resistance or ts.entry_exit_strategy)
    needs_cr = not cr or not (cr.regulatory_risks or cr.geopolitical_risks or cr.competitive_risks or cr.operational_risks)
    if needs_fc or needs_ts or needs_cr:
        section_updates: dict[str, Any] = {}
        if needs_fc:
            section_updates["fundamental_context"] = _py().fundamental_context
        if needs_ts:
            section_updates["technical_strategy"] = _py().technical_strategy
        if needs_cr:
            section_updates["contextual_risks"] = _py().contextual_risks
        qual = qual.model_copy(update=section_updates)
        logger.info(f"Empty AI sections filled with Python content for {ctx.ticker}: {list(section_updates.keys())}")

    executive_summary = _generate_executive_summary(quant, qual)
    investment_rationale = _get_investment_rationale(qual)
    word_count = _calculate_word_count(executive_summary, investment_rationale, qual)
    unique_insights = _count_unique_insights(qual)

    enriched = EnrichedAnalysis(
        ticker=ctx.ticker,
        company_name=ctx.company_name,
        asset_class=ctx.asset_class,
        analysis_date=datetime.utcnow(),
        quantitative=quant,
        qualitative=qual,
        final_grade=quant.grade,
        final_score=quant.composite_score,
        final_recommendation=final_rec,
        recommendation_conflict=recommendation_conflict,
        recommendation_confidence=_get_confidence(qual),
        executive_summary=executive_summary,
        investment_rationale=investment_rationale,
        report_word_count=word_count,
        unique_insights_count=unique_insights,
        processing_time_seconds=processing_time,
        llm_cost_dollars=0.05,  # Estimate
        sentiment_summary=sentiment_summary,
    )

    logger.info(f"Synthesis complete: {ctx.ticker} grade={enriched.final_grade} rec={enriched.final_recommendation} words={enriched.report_word_count}")
    return enriched


@stage(name="synthesize", timeout_s=30, retries=0)
def synthesize(
    ctx: StageContext,
    quant: QuantitativeAnalysis,
    qual: QualitativeInsights,
    raw: dict[str, Any],
) -> EnrichedAnalysis:
    """Stage entry: combine quant+qual into EnrichedAnalysis."""
    analysis_ctx = ctx.extras["analysis_ctx"]
    processing_time: float = ctx.extras.get("processing_time", 0.0)
    sentiment_summary: dict[str, Any] | None = ctx.extras.get("sentiment_summary")
    options_probs: ScenarioProbabilities | None = ctx.extras.get("options_probs")
    return _synthesize_inner(analysis_ctx, quant, qual, processing_time, sentiment_summary=sentiment_summary, options_probs=options_probs)


# Legacy shim — callers outside run_pipeline continue to work unchanged.
def synthesize_enriched_analysis(
    ctx: AnalysisContext,
    quant: QuantitativeAnalysis,
    qual: QualitativeInsights,
    processing_time: float = 0.0,
    sentiment_summary: dict[str, Any] | None = None,
    options_probs: ScenarioProbabilities | None = None,
) -> EnrichedAnalysis:
    """Legacy entry point: delegates to _synthesize_inner."""
    return _synthesize_inner(ctx, quant, qual, processing_time, sentiment_summary=sentiment_summary, options_probs=options_probs)
