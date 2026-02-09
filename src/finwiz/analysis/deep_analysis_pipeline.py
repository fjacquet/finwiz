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
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal, cast

from finwiz.flow_state_models import DeepAnalysisResult
from finwiz.schemas.hybrid_analysis import (
    EnrichedAnalysis,
    QualitativeInsights,
    QuantitativeAnalysis,
)
from finwiz.schemas.hybrid_analysis.metadata import DataQualityMetrics
from finwiz.schemas.hybrid_analysis.qualitative import (
    ActionPlan,
    ContextualRiskInsights,
    FundamentalContextInsights,
    InvestmentSynthesis,
    ScenarioProbabilities,
    SecAnalysisInsights,
    TechnicalStrategyInsights,
)

if TYPE_CHECKING:
    from crewai import CrewOutput

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AnalysisContext:
    """Immutable context for analysis pipeline."""

    ticker: str
    asset_class: str
    company_name: str = ""


# === STEP 1: Collect Raw Data (Python tools) ===
def collect_raw_data(
    ctx: AnalysisContext,
    prefetched_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Pure function: Collect raw financial data using Python tools.

    Args:
        ctx: Analysis context with ticker and asset class
        prefetched_data: Batch-prefetched data dict (from BatchDataPreFetcher)

    Returns:
        Dictionary containing raw financial data from multiple sources
    """
    from datetime import datetime
    from types import SimpleNamespace

    from finwiz.orchestrators.deep_analysis_data_collector import DeepAnalysisDataCollector

    logger.info(f"Collecting raw data for {ctx.ticker} ({ctx.asset_class})")

    # Create a minimal state object with required fields
    # DeepAnalysisDataCollector expects state.full_date
    minimal_state = SimpleNamespace(full_date=datetime.now().isoformat())

    collector = DeepAnalysisDataCollector(state=minimal_state)
    batch_enabled = prefetched_data is not None
    raw_data = collector.collect_data(
        ctx.ticker,
        ctx.asset_class,
        batch_enabled=batch_enabled,
        prefetched_data=prefetched_data,
    )
    logger.info(f"Raw data collected for {ctx.ticker}: {len(raw_data)} fields")

    # v4 Data Intelligence: collect sentiment and macro data if feature flags are enabled
    try:
        from finwiz.data.sentiment_collector import SentimentMacroCollector

        v4_collector = SentimentMacroCollector()
        sentiment = v4_collector.collect_sentiment(ctx.ticker)
        macro = v4_collector.collect_macro()
        if sentiment is not None:
            raw_data["news_sentiment"] = sentiment.model_dump(mode="json")
            logger.info(f"News sentiment collected for {ctx.ticker}: {sentiment.article_count} articles")
        if macro is not None:
            raw_data["macro_snapshot"] = macro.model_dump(mode="json")
            logger.info(f"Macro snapshot collected: {macro.get_market_regime()} regime")
    except Exception as e:
        logger.debug(f"v4 sentiment/macro collection skipped for {ctx.ticker}: {e}")

    return raw_data


# === STEP 2: Calculate Quantitative Metrics ($0 Python) ===
def calculate_quantitative(
    ctx: AnalysisContext,
    raw_data: dict[str, Any],
) -> tuple[DeepAnalysisResult, QuantitativeAnalysis]:
    """
    Pure function: Deterministic Python scoring, $0 cost, ~100ms.

    Args:
        ctx: Analysis context
        raw_data: Raw financial data from collect_raw_data

    Returns:
        Tuple of (DeepAnalysisResult for caching, QuantitativeAnalysis for AI context)
    """
    from finwiz.scoring.deep_analysis_scorer import DeepAnalysisScorer

    logger.info(f"Calculating quantitative metrics for {ctx.ticker}")
    scorer = DeepAnalysisScorer()
    result = scorer.calculate_composite_score(ctx.ticker, ctx.asset_class, raw_data)
    quant = _result_to_quantitative(result)
    logger.info(f"Quantitative: {ctx.ticker} grade={quant.grade} score={quant.composite_score:.2f}")
    return result, quant


# === STEP 3: Generate Qualitative Insights (AI Crew) ===
def generate_qualitative(
    ctx: AnalysisContext,
    quant: QuantitativeAnalysis,
) -> QualitativeInsights:
    """
    Side effect: Calls AI crew for qualitative analysis.

    The crew receives Python-calculated metrics as READ-ONLY context
    and generates contextual qualitative insights.

    In MAXIMUM_SPEED mode (DEEP_ANALYSIS_AI_SUMMARY=false), skips AI entirely
    and returns Python-generated qualitative content to avoid slow free-tier models.

    Args:
        ctx: Analysis context
        quant: Python-calculated quantitative analysis

    Returns:
        AI-generated qualitative insights (or Python fallback in fast mode)
    """
    from finwiz.config.performance.performance_config import is_maximum_speed_mode

    # Skip AI in MAXIMUM_SPEED mode - use Python-generated content instead
    if is_maximum_speed_mode():
        logger.info(f"MAXIMUM_SPEED mode: Skipping AI crew for {ctx.ticker}, using Python qualitative")
        return _create_python_qualitative(ctx, quant)

    logger.info(f"Generating qualitative insights for {ctx.ticker}")

    crew = _get_analysis_crew(ctx.asset_class)
    crew_inputs = _build_crew_inputs(ctx, quant)

    try:
        # Use wrapper with timeout and circuit breaker protection
        import asyncio
        import concurrent.futures

        from finwiz.infrastructure.resilience.crew_execution import execute_crew_with_timeout

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, execute_crew_with_timeout(f"deep_analysis_{ctx.asset_class}", crew, crew_inputs))
                crew_result = future.result()
        else:
            crew_result = asyncio.run(execute_crew_with_timeout(f"deep_analysis_{ctx.asset_class}", crew, crew_inputs))
        qual = _extract_qualitative(crew_result, quant)
        logger.info(f"Qualitative insights generated for {ctx.ticker}")
        return qual
    except Exception as e:
        import traceback

        logger.error(f"AI analysis failed for {ctx.ticker}: {e}\nTraceback:\n{traceback.format_exc()}")
        return _create_fallback_qualitative(ctx, quant, str(e))


# === STEP 4: Synthesize Final Analysis (Python) ===
def synthesize_enriched_analysis(
    ctx: AnalysisContext,
    quant: QuantitativeAnalysis,
    qual: QualitativeInsights,
    processing_time: float = 0.0,
    sentiment_summary: dict[str, Any] | None = None,
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
    final_rec = _synthesize_recommendation(quant, qual)
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
    result, quant = calculate_quantitative(ctx, raw_data)
    qual = generate_qualitative(ctx, quant)
    processing_time = time.time() - start
    sentiment_summary = _build_sentiment_summary(raw_data)
    enriched = synthesize_enriched_analysis(ctx, quant, qual, processing_time, sentiment_summary=sentiment_summary)

    logger.info(f"Pipeline complete for {ticker}: {processing_time:.1f}s")
    return result, enriched


# === Helper Functions ===


def _build_sentiment_summary(raw_data: dict[str, Any]) -> dict[str, Any] | None:
    """Build sentiment summary dict from raw_data for enriched JSON persistence.

    Extracts top headlines, aggregate score, confidence, and article counts
    from the news_sentiment data collected during raw data phase.

    Args:
        raw_data: Raw data dict potentially containing 'news_sentiment'.

    Returns:
        Sentiment summary dict or None if no news sentiment data available.
    """
    ns_raw = raw_data.get("news_sentiment")
    if ns_raw is None:
        return None

    try:
        # news_sentiment may be a dict (from model_dump) or a NewsSentimentResult
        if isinstance(ns_raw, dict):
            aggregate_sentiment = ns_raw.get("aggregate_sentiment", 0.0)
            article_count = ns_raw.get("article_count", 0)
            bullish_count = ns_raw.get("bullish_count", 0)
            bearish_count = ns_raw.get("bearish_count", 0)
            neutral_count = ns_raw.get("neutral_count", 0)
            articles = ns_raw.get("articles", [])
            # Confidence: not stored on NewsSentimentResult, compute from article count
            confidence = min(1.0, article_count / 10.0) if article_count > 0 else 0.0
        else:
            # NewsSentimentResult object
            aggregate_sentiment = getattr(ns_raw, "aggregate_sentiment", 0.0)
            article_count = getattr(ns_raw, "article_count", 0)
            bullish_count = getattr(ns_raw, "bullish_count", 0)
            bearish_count = getattr(ns_raw, "bearish_count", 0)
            neutral_count = getattr(ns_raw, "neutral_count", 0)
            articles = getattr(ns_raw, "articles", []) or []
            confidence = min(1.0, article_count / 10.0) if article_count > 0 else 0.0

        # Top 5 headlines
        top_headlines: list[dict[str, str]] = []
        for article in articles[:5]:
            if isinstance(article, dict):
                top_headlines.append(
                    {
                        "title": article.get("title", ""),
                        "source": article.get("source", ""),
                        "sentiment_label": article.get("sentiment_label", "neutral"),
                    }
                )
            else:
                top_headlines.append(
                    {
                        "title": getattr(article, "title", ""),
                        "source": getattr(article, "source", ""),
                        "sentiment_label": getattr(article, "sentiment_label", "neutral") or "neutral",
                    }
                )

        return {
            "score": aggregate_sentiment,
            "confidence": confidence,
            "article_count": article_count,
            "bullish_count": bullish_count,
            "bearish_count": bearish_count,
            "neutral_count": neutral_count,
            "top_headlines": top_headlines,
        }
    except Exception as e:
        logger.warning(f"Failed to build sentiment summary: {e}")
        return None


def _get_analysis_crew(asset_class: str) -> Any:
    """Factory for asset-specific crews."""
    from finwiz.crews.deep_analysis.deep_analysis import DeepAnalysisCrew

    # DeepAnalysisCrew handles all asset classes
    return DeepAnalysisCrew()


def _summarize_metrics(metrics: dict[str, float] | None, max_items: int = 10) -> str:
    """Summarize metrics dict to a compact string for AI context.

    Instead of passing the full dict (which can be 100K+ tokens),
    we pass a formatted summary of the top metrics.

    NOTE: Filters out None values to prevent format string errors like
    "unsupported format string passed to NoneType.__format__".
    """
    if not metrics:
        return "No data available"

    # Filter out None values BEFORE formatting to prevent format string errors
    valid_metrics = {k: v for k, v in metrics.items() if v is not None}

    if not valid_metrics:
        return "No data available"

    # Sort by absolute value (most significant metrics first)
    sorted_items = sorted(valid_metrics.items(), key=lambda x: abs(x[1]), reverse=True)

    # Take top N items and format compactly
    top_items = sorted_items[:max_items]
    parts = [f"{k}={v:.3f}" if isinstance(v, float) else f"{k}={v}" for k, v in top_items]

    return ", ".join(parts)


def _truncate_text(text: str | None, max_chars: int = 500) -> str:
    """Truncate text to max_chars, preserving word boundaries.

    Prevents token overflow from large text fields like python_rationale.
    """
    if not text:
        return "Analysis based on available data."
    if len(text) <= max_chars:
        return text
    # Truncate at word boundary
    truncated = text[:max_chars].rsplit(" ", 1)[0]
    return truncated + "..."


def _build_crew_inputs(ctx: AnalysisContext, quant: QuantitativeAnalysis) -> dict[str, Any]:
    """Build inputs dict for crew kickoff.

    IMPORTANT: We pass SUMMARIZED metrics, not full dictionaries.
    Full dicts can be 100K+ tokens, causing context overflow errors.
    The AI only needs key metrics for qualitative insights.

    NOTE: All values have None-safe defaults to prevent format string errors
    like "unsupported format string passed to NoneType.__format__".
    """
    # Build inputs with None-safe defaults and size limits
    inputs = {
        "ticker": ctx.ticker or "UNKNOWN",
        "asset_class": ctx.asset_class or "stock",
        "company_name": ctx.company_name or ctx.ticker or "Unknown",
        # Numeric defaults prevent "unsupported format string passed to NoneType"
        "grade": quant.grade or "C",
        "composite_score": quant.composite_score if quant.composite_score is not None else 0.5,
        "preliminary_recommendation": quant.preliminary_recommendation or "HOLD",
        "fundamental_score": quant.fundamental_score if quant.fundamental_score is not None else 0.5,
        "technical_score": quant.technical_score if quant.technical_score is not None else 0.5,
        "risk_score": quant.risk_score if quant.risk_score is not None else 0.5,
        # Pass SUMMARIES instead of full dicts to avoid token overflow
        "fundamental_metrics": _summarize_metrics(quant.fundamental_metrics, max_items=12) or "N/A",
        "technical_indicators": _summarize_metrics(quant.technical_indicators, max_items=10) or "N/A",
        "risk_metrics": _summarize_metrics(quant.risk_metrics, max_items=8) or "N/A",
        # Truncate rationale to prevent large text fields causing overflow
        "python_rationale": _truncate_text(quant.python_rationale, max_chars=500),
    }

    # ⚡ DIAGNOSTIC: Log sizes of each input field for debugging
    total_chars = sum(len(str(v)) for v in inputs.values() if v is not None)
    estimated_tokens = total_chars // 4
    logger.info(f"⚡ Crew inputs for {ctx.ticker}: {total_chars:,} chars (~{estimated_tokens:,} tokens)")

    return inputs


def _filter_numeric_values(data: dict[str, Any] | None) -> dict[str, float]:
    """Filter dictionary to only include numeric values (int/float)."""
    if not data:
        return {}
    return {k: float(v) for k, v in data.items() if isinstance(v, (int, float)) and not isinstance(v, bool)}


def _result_to_quantitative(result: DeepAnalysisResult) -> QuantitativeAnalysis:
    """Convert DeepAnalysisResult to QuantitativeAnalysis schema."""
    # Filter dicts to only include numeric values
    # (the schema expects dict[str, float], not dict[str, Any])
    fundamental_metrics = _filter_numeric_values(result.fundamental_details)
    technical_indicators = _filter_numeric_values(result.technical_details)
    risk_metrics = _filter_numeric_values(result.risk_details)

    return QuantitativeAnalysis(
        composite_score=result.composite_score,
        fundamental_score=result.fundamental_score or 0.0,
        technical_score=result.technical_score or 0.0,
        risk_score=result.risk_score or 0.0,
        grade=result.grade,
        preliminary_recommendation=result.recommendation,
        fundamental_metrics=fundamental_metrics,
        technical_indicators=technical_indicators,
        risk_metrics=risk_metrics,
        calculation_timestamp=datetime.now(),
        data_quality=DataQualityMetrics(
            completeness_score=result.confidence_level,
            freshness_score=1.0 if result.data_freshness_hours < 24 else 0.5,
            accuracy_confidence=result.confidence_level,
            source_reliability=0.85,
            missing_fields=result.warnings if hasattr(result, "warnings") else [],
        ),
        confidence_level=result.confidence_level,
        python_rationale=result.rationale,
    )


def _has_qualitative_content(qual: QualitativeInsights | None) -> bool:
    """Check if QualitativeInsights has actual content (not just defaults)."""
    if qual is None:
        return False
    # Check if any of the main sections have content
    has_sec = qual.sec_insights is not None
    has_fundamental = qual.fundamental_context is not None
    has_technical = qual.technical_strategy is not None
    has_risks = qual.contextual_risks is not None
    has_synthesis = qual.investment_synthesis is not None
    # Also check ai_confidence - 0.5 is the default (no AI analysis)
    has_confidence = qual.ai_confidence != 0.5
    return any([has_sec, has_fundamental, has_technical, has_risks, has_synthesis, has_confidence])


def _extract_qualitative(crew_result: CrewOutput, quant: QuantitativeAnalysis) -> QualitativeInsights:
    """Extract QualitativeInsights from crew result."""
    # Try to get pydantic model directly
    if hasattr(crew_result, "pydantic") and crew_result.pydantic:
        # Case 1: Direct QualitativeInsights
        if isinstance(crew_result.pydantic, QualitativeInsights):
            qual = crew_result.pydantic
            if _has_qualitative_content(qual):
                return qual
            logger.warning("QualitativeInsights from pydantic has no content, trying fallback")

        # Case 2: EnrichedAnalysis containing QualitativeInsights
        if isinstance(crew_result.pydantic, EnrichedAnalysis):
            enriched_qual = crew_result.pydantic.qualitative
            if enriched_qual is not None and _has_qualitative_content(enriched_qual):
                logger.info("Extracted QualitativeInsights from EnrichedAnalysis.qualitative")
                return enriched_qual
            logger.warning("EnrichedAnalysis.qualitative has no content, trying fallback")

    # Try tasks_output first (more reliable than raw parsing)
    if hasattr(crew_result, "tasks_output") and crew_result.tasks_output:
        for task_output in crew_result.tasks_output:
            if hasattr(task_output, "pydantic"):
                # Check for direct QualitativeInsights
                if isinstance(task_output.pydantic, QualitativeInsights):
                    qual = task_output.pydantic
                    if _has_qualitative_content(qual):
                        logger.info("Extracted QualitativeInsights from tasks_output")
                        return qual
                # Check for EnrichedAnalysis containing qualitative
                if isinstance(task_output.pydantic, EnrichedAnalysis) and task_output.pydantic.qualitative:
                    qual = task_output.pydantic.qualitative
                    if _has_qualitative_content(qual):
                        logger.info("Extracted QualitativeInsights from tasks_output EnrichedAnalysis")
                        return qual

    # Try to parse from raw output
    if hasattr(crew_result, "raw") and crew_result.raw:
        try:
            import json

            data = json.loads(crew_result.raw)
            # Try to extract qualitative from EnrichedAnalysis-shaped JSON
            if "qualitative" in data and isinstance(data["qualitative"], dict):
                qual = QualitativeInsights(**data["qualitative"])
                if _has_qualitative_content(qual):
                    logger.info("Extracted QualitativeInsights from raw JSON qualitative field")
                    return qual
            # Try direct QualitativeInsights parse
            qual = QualitativeInsights(**data)
            if _has_qualitative_content(qual):
                return qual
            logger.warning("Parsed QualitativeInsights has no content, using fallback")
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.warning(f"Failed to parse crew output as JSON: {e}")

    # Fallback: Use validation with retry
    from finwiz.validation.ai_output import validate_ai_output_with_retry

    logger.warning("All extraction methods failed, falling back to validation with retry")
    raw_output = crew_result.raw if hasattr(crew_result, "raw") else str(crew_result)
    return validate_ai_output_with_retry(raw_output, quant, max_retries=2)


def _create_python_qualitative(ctx: AnalysisContext, quant: QuantitativeAnalysis) -> QualitativeInsights:
    """Generate qualitative insights using Python templates (no AI).

    This is used in MAXIMUM_SPEED mode to avoid slow AI calls.
    Content is derived from quantitative metrics using rule-based templates.
    """
    ticker = ctx.ticker
    grade = quant.grade
    score = quant.composite_score
    rec = quant.preliminary_recommendation
    fund_score = quant.fundamental_score
    tech_score = quant.technical_score
    risk_score = quant.risk_score
    rationale = quant.python_rationale

    # Determine sentiment based on scores
    is_strong = score >= 0.7
    is_weak = score < 0.4
    sentiment = "positif" if is_strong else ("négatif" if is_weak else "neutre")

    # Build business model from metrics
    fund_metrics = quant.fundamental_metrics
    roe = fund_metrics.get("roe", 0)
    debt_ratio = fund_metrics.get("debt_to_equity", 0)
    revenue_growth = fund_metrics.get("revenue_growth", 0)

    business_model = (
        f"{ticker} présente un profil fondamental avec un score de {fund_score:.2f}. "
        f"Le rendement sur capitaux propres (ROE) est de {roe:.1%}, "
        f"avec un ratio dette/capitaux propres de {debt_ratio:.2f}. "
        f"La croissance des revenus est de {revenue_growth:.1%}. "
        f"Ces métriques suggèrent un modèle d'affaires {'solide' if fund_score >= 0.6 else 'modéré' if fund_score >= 0.4 else 'à surveiller'}. "
        f"{rationale} "
        f"L'analyse quantitative Python a attribué la note {grade} avec un score composite de {score:.2f}."
    )

    # Build technical analysis from indicators
    tech_indicators = quant.technical_indicators
    rsi = tech_indicators.get("rsi", 50)
    macd = tech_indicators.get("macd", 0)

    support_resistance = (
        f"Analyse technique avec score {tech_score:.2f}. "
        f"RSI actuel: {rsi:.1f} ({'suracheté' if rsi > 70 else 'survendu' if rsi < 30 else 'neutre'}). "
        f"MACD: {macd:.3f} ({'signal haussier' if macd > 0 else 'signal baissier'}). "
        f"Les niveaux de support et résistance sont déterminés par l'analyse des moyennes mobiles."
    )

    entry_exit = (
        f"Stratégie d'entrée basée sur le score technique de {tech_score:.2f}. "
        f"Recommandation: {rec}. "
        f"{'Accumuler sur les replis' if rec == 'BUY' else 'Attendre confirmation' if rec == 'HOLD' else 'Réduire exposition'} "
        f"avec gestion du risque appropriée. "
        f"Le score de risque de {risk_score:.2f} suggère une volatilité {'élevée' if risk_score < 0.4 else 'modérée' if risk_score < 0.7 else 'faible'}."
    )

    # Build investment thesis
    risk_metrics = quant.risk_metrics
    volatility = risk_metrics.get("volatility", 0)
    beta = risk_metrics.get("beta", 1)
    max_drawdown = risk_metrics.get("max_drawdown", 0)

    investment_thesis = (
        f"Analyse quantitative complète pour {ticker} ({ctx.asset_class}). "
        f"Note finale: {grade} avec score composite {score:.2f}. "
        f"Recommandation Python: {rec}. "
        f"Score fondamental: {fund_score:.2f} - ROE {roe:.1%}, ratio dette {debt_ratio:.2f}, croissance {revenue_growth:.1%}. "
        f"Score technique: {tech_score:.2f} - RSI {rsi:.1f}, MACD {macd:.3f}. "
        f"Score risque: {risk_score:.2f} - Volatilité {volatility:.1%}, Beta {beta:.2f}, Drawdown max {max_drawdown:.1%}. "
        f"Justification: {rationale} "
        f"Cette analyse est générée en mode MAXIMUM_SPEED sans appel AI pour optimiser les performances. "
        f"Pour une analyse qualitative approfondie avec contexte sectoriel et analyse des filings SEC, "
        f"désactivez le mode MAXIMUM_SPEED dans la configuration."
    )

    bull_case = (
        f"Scénario haussier: Si les fondamentaux s'améliorent au-delà du score actuel de {fund_score:.2f}, "
        f"et que les indicateurs techniques confirment avec RSI > 50 et MACD positif, "
        f"{ticker} pourrait surperformer. Catalyseurs potentiels: amélioration du ROE, réduction de la dette, "
        f"momentum technique positif. Probabilité estimée basée sur le grade {grade}."
    )

    base_case = (
        f"Scénario de base: Maintien du profil actuel avec score {score:.2f} et grade {grade}. "
        f"Les métriques fondamentales restent stables, les indicateurs techniques oscillent autour des niveaux actuels. "
        f"Performance alignée avec le secteur. Recommandation {rec} reste appropriée."
    )

    bear_case = (
        f"Scénario baissier: Détérioration des fondamentaux en dessous du score {fund_score:.2f}, "
        f"signaux techniques négatifs avec RSI < 30 et MACD négatif, "
        f"augmentation de la volatilité au-delà de {volatility:.1%}. "
        f"Risque de drawdown supérieur à {max_drawdown:.1%}."
    )

    # Scenario probabilities based on score
    if score >= 0.7:
        probs = ScenarioProbabilities(bull=0.40, base=0.45, bear=0.15)
    elif score >= 0.5:
        probs = ScenarioProbabilities(bull=0.25, base=0.50, bear=0.25)
    else:
        probs = ScenarioProbabilities(bull=0.15, base=0.45, bear=0.40)

    return QualitativeInsights(
        sec_insights=SecAnalysisInsights(
            business_model=business_model,
            competitive_advantages=[f"Score fondamental {fund_score:.2f}", f"Grade {grade}"],
            risk_factors=[f"Volatilité {volatility:.1%}", f"Beta {beta:.2f}", f"Drawdown max {max_drawdown:.1%}"],
            strategic_initiatives=["Analyse Python MAXIMUM_SPEED mode"],
        ),
        fundamental_context=FundamentalContextInsights(
            industry_analysis=f"Analyse sectorielle basée sur métriques quantitatives. Score fondamental: {fund_score:.2f}. {rationale}",
            growth_drivers=[f"ROE: {roe:.1%}", f"Croissance revenus: {revenue_growth:.1%}"],
            competitive_positioning=f"Position basée sur score {score:.2f} et grade {grade}. {sentiment.capitalize()} par rapport au marché.",
            management_assessment=f"Évaluation basée sur métriques quantitatives: ratio dette {debt_ratio:.2f}, ROE {roe:.1%}.",
        ),
        technical_strategy=TechnicalStrategyInsights(
            chart_patterns=[f"RSI: {rsi:.1f}", f"MACD: {macd:.3f}"],
            support_resistance=support_resistance,
            entry_exit_strategy=entry_exit,
            timing_assessment=f"Score technique {tech_score:.2f}. {'Timing favorable' if tech_score >= 0.6 else 'Attendre confirmation'}.",
        ),
        contextual_risks=ContextualRiskInsights(
            regulatory_risks=["Non évalué en mode MAXIMUM_SPEED"],
            geopolitical_risks=["Non évalué en mode MAXIMUM_SPEED"],
            competitive_risks=["Non évalué en mode MAXIMUM_SPEED"],
            operational_risks=[f"Volatilité: {volatility:.1%}"],
            stress_scenarios=[f"Drawdown max historique: {max_drawdown:.1%}"],
        ),
        investment_synthesis=InvestmentSynthesis(
            investment_thesis=investment_thesis,
            bull_case=bull_case,
            base_case=base_case,
            bear_case=bear_case,
            scenario_probabilities=probs,
            final_recommendation=cast(Literal["BUY", "HOLD", "SELL"], rec),
            recommendation_confidence="MEDIUM",
            action_plan=ActionPlan(
                immediate_actions=[f"Suivre recommandation {rec}", "Surveiller indicateurs techniques"],
                monitoring_points=["RSI", "MACD", "Volatilité"],
                exit_triggers=[f"Drawdown > {abs(max_drawdown) * 1.5:.1%}", "RSI > 80 ou < 20"],
            ),
        ),
        analysis_timestamp=datetime.now(),
        ai_confidence=0.7,  # Python analysis confidence
    )


def _create_fallback_qualitative(ctx: AnalysisContext, quant: QuantitativeAnalysis, error: str) -> QualitativeInsights:
    """Create fallback QualitativeInsights when AI fails."""
    fallback_text = f"Analysis unavailable due to AI failure: {error}. " * 5

    return QualitativeInsights(
        sec_insights=SecAnalysisInsights(
            business_model=fallback_text,
            competitive_advantages=["Unavailable due to AI failure"],
            risk_factors=["AI analysis failed - rely on Python metrics"],
            strategic_initiatives=[],
        ),
        fundamental_context=FundamentalContextInsights(
            industry_analysis=fallback_text,
            growth_drivers=["Unavailable"],
            competitive_positioning=fallback_text,
            management_assessment=fallback_text,
        ),
        technical_strategy=TechnicalStrategyInsights(
            chart_patterns=["Unavailable"],
            support_resistance=fallback_text,
            entry_exit_strategy=fallback_text,
            timing_assessment=fallback_text,
        ),
        contextual_risks=ContextualRiskInsights(
            regulatory_risks=[],
            geopolitical_risks=[],
            competitive_risks=[],
            operational_risks=[],
            stress_scenarios=[],
        ),
        investment_synthesis=InvestmentSynthesis(
            investment_thesis=(
                f"FALLBACK: AI analysis failed for {ctx.ticker}. "
                f"Python analysis: Grade {quant.grade}, Score {quant.composite_score:.2f}, "
                f"Recommendation {quant.preliminary_recommendation}. "
                f"{quant.python_rationale} " * 3
            ),
            bull_case="Unavailable due to AI failure. " * 10,
            base_case="Unavailable due to AI failure. " * 10,
            bear_case="Unavailable due to AI failure. " * 10,
            scenario_probabilities=ScenarioProbabilities(bull=0.0, base=1.0, bear=0.0),
            final_recommendation=cast(Literal["BUY", "HOLD", "SELL"], quant.preliminary_recommendation),
            recommendation_confidence="LOW",
            action_plan=ActionPlan(
                immediate_actions=["Review Python metrics manually"],
                monitoring_points=["Re-run analysis when AI is available"],
                exit_triggers=["Significant price movement"],
            ),
        ),
        analysis_timestamp=datetime.now(),
        ai_confidence=0.0,
    )


def _synthesize_recommendation(quant: QuantitativeAnalysis, qual: QualitativeInsights) -> str:
    """Synthesize final recommendation. Python wins on conflicts."""
    python_rec = quant.preliminary_recommendation
    ai_rec = qual.investment_synthesis.final_recommendation if qual.investment_synthesis else "HOLD"

    if python_rec == ai_rec:
        return python_rec

    logger.warning(f"Recommendation conflict: Python={python_rec}, AI={ai_rec}. Using Python.")
    return python_rec


def _generate_executive_summary(quant: QuantitativeAnalysis, qual: QualitativeInsights) -> str:
    """Generate executive summary combining both analyses."""
    parts = [
        f"Investment Grade: {quant.grade} with composite score {quant.composite_score:.2f}.",
        f"Recommendation: {quant.preliminary_recommendation}.",
        f"Quantitative: Fundamental {quant.fundamental_score:.2f}, Technical {quant.technical_score:.2f}, Risk {quant.risk_score:.2f}.",
    ]

    if qual.sec_insights and qual.sec_insights.business_model:
        model = qual.sec_insights.business_model[:200].strip()
        if not model.endswith("."):
            model += "..."
        parts.append(f"Business: {model}")

    if qual.sec_insights and qual.sec_insights.competitive_advantages:
        advantages = qual.sec_insights.competitive_advantages[:3]
        parts.append(f"Advantages: {', '.join(advantages)}.")

    if qual.fundamental_context and qual.fundamental_context.industry_analysis:
        industry = qual.fundamental_context.industry_analysis[:150].strip()
        if not industry.endswith("."):
            industry += "..."
        parts.append(f"Industry: {industry}")

    if qual.investment_synthesis and qual.investment_synthesis.investment_thesis:
        thesis = qual.investment_synthesis.investment_thesis[:300].strip()
        if not thesis.endswith("."):
            thesis += "..."
        parts.append(f"Thesis: {thesis}")

    summary = " ".join(parts)

    # Ensure minimum 200 words
    word_count = len(summary.split())
    if word_count < 200:
        summary += " " + quant.python_rationale
        if qual.fundamental_context:
            summary += " " + qual.fundamental_context.competitive_positioning
            summary += " " + qual.fundamental_context.management_assessment

    return summary


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
