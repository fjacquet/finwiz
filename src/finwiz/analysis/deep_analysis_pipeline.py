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
import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from finwiz.analysis._helpers import (
    _build_sentiment_summary,
    _get_analysis_crew,  # noqa: F401 — re-exported for test compatibility
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
from finwiz.flow_state_models import DeepAnalysisResult
from finwiz.schemas.hybrid_analysis import (
    EnrichedAnalysis,
    QualitativeInsights,
    QuantitativeAnalysis,
)
from finwiz.schemas.hybrid_analysis.qualitative import (
    ScenarioProbabilities,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AnalysisContext:
    """Immutable context for analysis pipeline."""

    ticker: str
    asset_class: str
    company_name: str = ""


# === STEP 4: Synthesize Final Analysis (Python) ===
def synthesize_enriched_analysis(
    ctx: AnalysisContext,
    quant: QuantitativeAnalysis,
    qual: QualitativeInsights,
    processing_time: float = 0.0,
    sentiment_summary: dict[str, Any] | None = None,
    options_probs: ScenarioProbabilities | None = None,
) -> EnrichedAnalysis:
    """
    Pure function: Combines quantitative + qualitative into EnrichedAnalysis.

    Python wins on recommendation conflicts (AI may hallucinate).

    Args:
        ctx: Analysis context
        quant: Python-calculated quantitative analysis
        qual: AI-generated qualitative insights
        processing_time: Total processing time in seconds
        sentiment_summary: Optional sentiment summary with score, confidence, top headlines

    Returns:
        EnrichedAnalysis combining both analyses
    """
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


def _bs_nd2(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Black-Scholes N(d₂): risk-neutral probability that S_T > K."""
    import math

    from scipy.stats import norm  # type: ignore[import-untyped]

    if T <= 0 or sigma <= 0 or S <= 0:
        return 0.5
    d2 = (math.log(S / K) + (r - 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    return float(norm.cdf(d2))


def _compute_options_probabilities(raw_data: dict[str, Any]) -> ScenarioProbabilities | None:
    """Compute options-implied scenario probabilities via Black-Scholes N(d₂).

    Returns None when options IV data is unavailable (crypto, niche ETFs, etc.).
    Priority: options-implied > Python formula > AI guess.
    """
    bull_iv_raw = raw_data.get("options_bull_iv")
    bear_iv_raw = raw_data.get("options_bear_iv")
    t_raw = raw_data.get("options_T")
    s_raw = raw_data.get("current_price")
    if bull_iv_raw is None or bear_iv_raw is None or t_raw is None or s_raw is None:
        return None

    s_val = float(s_raw)
    t_val = float(t_raw)
    bull_val = float(bull_iv_raw)
    bear_val = float(bear_iv_raw)
    r = float(os.getenv("RISK_FREE_RATE", "0.045"))
    p_bull = _bs_nd2(s_val, s_val * 1.20, t_val, r, bull_val)
    p_bear = 1.0 - _bs_nd2(s_val, s_val * 0.85, t_val, r, bear_val)
    p_base = max(0.0, 1.0 - p_bull - p_bear)
    total = p_bull + p_base + p_bear
    return ScenarioProbabilities(
        bull=round(p_bull / total, 2),
        base=round(p_base / total, 2),
        bear=round(p_bear / total, 2),
    )


def _generate_executive_summary(quant: QuantitativeAnalysis, qual: QualitativeInsights) -> str:
    """Render the executive summary as a short HTML headline + 3-5 bullets.

    The output is consumed by templates via ``{{ executive_summary | safe }}``. Long
    qualitative content (industry analysis, competitive positioning, full thesis)
    lives in its own sections later in the report — the summary is intentionally
    short and structured, not a wall of prose.
    """
    from html import escape

    rec = quant.preliminary_recommendation
    rec_emoji = "✅" if rec == "BUY" else ("❌" if rec == "SELL" else "⏸️")
    conf_map = {"LOW": "FAIBLE", "MEDIUM": "MOYENNE", "HIGH": "ÉLEVÉE"}
    confidence = conf_map.get(
        qual.investment_synthesis.recommendation_confidence if qual.investment_synthesis else "MEDIUM",
        "MOYENNE",
    )

    headline = f'<p class="exec-headline"><strong>Grade {escape(quant.grade)} ({quant.composite_score:.2f}) · {rec_emoji} {escape(rec)} · Confiance {confidence}</strong></p>'

    bullets: list[str] = []

    # Fundamentals — drivers from real metrics, not prose
    fund_metrics = quant.fundamental_metrics or {}
    fund_drivers: list[str] = []
    if "roe" in fund_metrics:
        fund_drivers.append(f"ROE {fund_metrics['roe'] * 100:.0f}%")
    if "revenue_growth" in fund_metrics:
        fund_drivers.append(f"croissance {fund_metrics['revenue_growth'] * 100:.0f}%")
    if "debt_to_equity" in fund_metrics:
        fund_drivers.append(f"D/E {fund_metrics['debt_to_equity']:.2f}")
    if "expense_ratio" in fund_metrics:
        fund_drivers.append(f"frais {fund_metrics['expense_ratio'] * 100:.2f}%")
    fund_text = f"Fondamentaux {quant.fundamental_score * 100:.0f}%"
    if fund_drivers:
        fund_text += " — " + ", ".join(fund_drivers[:3])
    bullets.append(fund_text)

    # Technical — RSI + trend if available
    tech_metrics = quant.technical_indicators or {}
    tech_drivers: list[str] = []
    if "rsi" in tech_metrics:
        rsi = tech_metrics["rsi"]
        rsi_label = "neutre" if 40 <= rsi <= 60 else ("suracheté" if rsi > 70 else ("survendu" if rsi < 30 else "tendanciel"))
        tech_drivers.append(f"RSI {rsi:.0f} ({rsi_label})")
    if "trend_strength" in tech_metrics:
        tech_drivers.append(f"force tendance {tech_metrics['trend_strength']:.2f}")
    tech_text = f"Technique {quant.technical_score * 100:.0f}%"
    if tech_drivers:
        tech_text += " — " + ", ".join(tech_drivers[:2])
    bullets.append(tech_text)

    # Risk — volatility + drawdown
    risk_metrics = quant.risk_metrics or {}
    risk_drivers: list[str] = []
    if "volatility" in risk_metrics:
        risk_drivers.append(f"vol {risk_metrics['volatility'] * 100:.0f}%")
    if "max_drawdown" in risk_metrics:
        risk_drivers.append(f"drawdown {risk_metrics['max_drawdown'] * 100:.0f}%")
    if "beta" in risk_metrics:
        risk_drivers.append(f"β {risk_metrics['beta']:.2f}")
    risk_text = f"Risque {quant.risk_score:.1f}/5"
    if risk_drivers:
        risk_text += " — " + ", ".join(risk_drivers[:3])
    bullets.append(risk_text)

    # Thesis — first sentence only, never truncated mid-word
    if qual.investment_synthesis and qual.investment_synthesis.investment_thesis:
        thesis = qual.investment_synthesis.investment_thesis.strip()
        first_sentence = thesis.split(".")[0].strip()
        if first_sentence:
            bullets.append(f"Thèse : {first_sentence}.")

    bullets_html = '<ul class="exec-bullets">' + "".join(f"<li>{escape(b)}</li>" for b in bullets) + "</ul>"
    return headline + bullets_html


def _get_investment_rationale(qual: QualitativeInsights) -> str:
    """Get investment rationale from qualitative insights."""
    if qual.investment_synthesis and qual.investment_synthesis.investment_thesis:
        return qual.investment_synthesis.investment_thesis
    return "Investment rationale unavailable."


def _get_confidence(qual: QualitativeInsights) -> str:
    """Get recommendation confidence from qualitative insights."""
    if qual.investment_synthesis and qual.investment_synthesis.recommendation_confidence:
        return qual.investment_synthesis.recommendation_confidence
    return "MEDIUM"


def _calculate_word_count(
    executive_summary: str,
    investment_rationale: str,
    qual: QualitativeInsights,
) -> int:
    """Calculate total word count from all text content."""
    sections = [executive_summary, investment_rationale]

    if qual.sec_insights:
        sections.append(qual.sec_insights.business_model)
        sections.extend(qual.sec_insights.competitive_advantages)
        sections.extend(qual.sec_insights.risk_factors)
        sections.extend(qual.sec_insights.strategic_initiatives)

    if qual.fundamental_context:
        sections.append(qual.fundamental_context.industry_analysis)
        sections.extend(qual.fundamental_context.growth_drivers)
        sections.append(qual.fundamental_context.competitive_positioning)
        sections.append(qual.fundamental_context.management_assessment)

    if qual.technical_strategy:
        sections.extend(qual.technical_strategy.chart_patterns)
        sections.append(qual.technical_strategy.support_resistance)
        sections.append(qual.technical_strategy.entry_exit_strategy)
        sections.append(qual.technical_strategy.timing_assessment)

    if qual.contextual_risks:
        sections.extend(qual.contextual_risks.regulatory_risks)
        sections.extend(qual.contextual_risks.geopolitical_risks)
        sections.extend(qual.contextual_risks.competitive_risks)
        sections.extend(qual.contextual_risks.operational_risks)
        sections.extend(qual.contextual_risks.stress_scenarios)

    if qual.investment_synthesis:
        sections.append(qual.investment_synthesis.investment_thesis)
        sections.append(qual.investment_synthesis.bull_case)
        sections.append(qual.investment_synthesis.base_case)
        sections.append(qual.investment_synthesis.bear_case)

    combined = " ".join(str(s) for s in sections if s)
    return len(combined.split())


def _count_unique_insights(qual: QualitativeInsights) -> int:
    """Count unique qualitative insights."""
    insights: list[str] = []

    if qual.sec_insights:
        insights.extend(qual.sec_insights.competitive_advantages)
        insights.extend(qual.sec_insights.risk_factors)
        insights.extend(qual.sec_insights.strategic_initiatives)

    if qual.fundamental_context:
        insights.extend(qual.fundamental_context.growth_drivers)

    if qual.investment_synthesis:
        insights.append(qual.investment_synthesis.bull_case)
        insights.append(qual.investment_synthesis.base_case)
        insights.append(qual.investment_synthesis.bear_case)

    return len(set(i for i in insights if i))
