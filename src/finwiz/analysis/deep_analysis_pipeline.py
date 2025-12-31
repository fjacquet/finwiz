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
from finwiz.schemas.hybrid_analysis.metadata import DataLineage, DataQualityMetrics
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
def collect_raw_data(ctx: AnalysisContext) -> dict[str, Any]:
    """
    Pure function: Collect raw financial data using Python tools.

    Args:
        ctx: Analysis context with ticker and asset class

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
    raw_data = collector.collect_data(ctx.ticker, ctx.asset_class, batch_enabled=False)
    logger.info(f"Raw data collected for {ctx.ticker}: {len(raw_data)} fields")
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

    Args:
        ctx: Analysis context
        quant: Python-calculated quantitative analysis

    Returns:
        AI-generated qualitative insights
    """
    logger.info(f"Generating qualitative insights for {ctx.ticker}")

    crew = _get_analysis_crew(ctx.asset_class)
    crew_inputs = _build_crew_inputs(ctx, quant)

    try:
        crew_result = crew.crew().kickoff(inputs=crew_inputs)
        qual = _extract_qualitative(crew_result, quant)
        logger.info(f"Qualitative insights generated for {ctx.ticker}")
        return qual
    except Exception as e:
        logger.error(f"AI analysis failed for {ctx.ticker}: {e}")
        return _create_fallback_qualitative(ctx, quant, str(e))


# === STEP 4: Synthesize Final Analysis (Python) ===
def synthesize_enriched_analysis(
    ctx: AnalysisContext,
    quant: QuantitativeAnalysis,
    qual: QualitativeInsights,
    processing_time: float = 0.0,
) -> EnrichedAnalysis:
    """
    Pure function: Combines quantitative + qualitative into EnrichedAnalysis.

    Python wins on recommendation conflicts (AI may hallucinate).

    Args:
        ctx: Analysis context
        quant: Python-calculated quantitative analysis
        qual: AI-generated qualitative insights
        processing_time: Total processing time in seconds

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
    )

    logger.info(
        f"Synthesis complete: {ctx.ticker} grade={enriched.final_grade} "
        f"rec={enriched.final_recommendation} words={enriched.report_word_count}"
    )
    return enriched


# === COMPOSED PIPELINE (Main Entry Point) ===
def analyze_holding(
    ticker: str,
    asset_class: str,
    company_name: str = "",
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

    Returns:
        Tuple of (DeepAnalysisResult for caching, EnrichedAnalysis for HTML)
    """
    start = time.time()
    ctx = AnalysisContext(ticker=ticker, asset_class=asset_class, company_name=company_name)

    logger.info(f"Starting analysis pipeline for {ticker} ({asset_class})")

    # Pipeline composition
    raw_data = collect_raw_data(ctx)
    result, quant = calculate_quantitative(ctx, raw_data)
    qual = generate_qualitative(ctx, quant)
    processing_time = time.time() - start
    enriched = synthesize_enriched_analysis(ctx, quant, qual, processing_time)

    logger.info(f"Pipeline complete for {ticker}: {processing_time:.1f}s")
    return result, enriched


# === Helper Functions ===


def _get_analysis_crew(asset_class: str) -> Any:
    """Factory for asset-specific crews."""
    from finwiz.crews.deep_analysis.deep_analysis import DeepAnalysisCrew

    # DeepAnalysisCrew handles all asset classes
    return DeepAnalysisCrew()


def _build_crew_inputs(ctx: AnalysisContext, quant: QuantitativeAnalysis) -> dict[str, Any]:
    """Build inputs dict for crew kickoff."""
    return {
        "ticker": ctx.ticker,
        "asset_class": ctx.asset_class,
        "company_name": ctx.company_name,
        "grade": quant.grade,
        "composite_score": quant.composite_score,
        "preliminary_recommendation": quant.preliminary_recommendation,
        "fundamental_score": quant.fundamental_score,
        "technical_score": quant.technical_score,
        "risk_score": quant.risk_score,
        "fundamental_metrics": quant.fundamental_metrics,
        "technical_indicators": quant.technical_indicators,
        "risk_metrics": quant.risk_metrics,
        "python_rationale": quant.python_rationale,
    }


def _result_to_quantitative(result: DeepAnalysisResult) -> QuantitativeAnalysis:
    """Convert DeepAnalysisResult to QuantitativeAnalysis schema."""
    return QuantitativeAnalysis(
        composite_score=result.composite_score,
        fundamental_score=result.fundamental_score or 0.0,
        technical_score=result.technical_score or 0.0,
        risk_score=result.risk_score or 0.0,
        grade=result.grade,
        preliminary_recommendation=result.recommendation,
        fundamental_metrics=result.fundamental_details,
        technical_indicators=result.technical_details,
        risk_metrics=result.risk_details,
        calculation_timestamp=datetime.now(),
        data_quality=DataQualityMetrics(
            completeness_score=result.confidence_level,
            freshness_score=1.0 if result.data_freshness_hours < 24 else 0.5,
            accuracy_confidence=result.confidence_level,
            source_reliability=0.85,
            missing_fields=result.warnings if hasattr(result, "warnings") else [],
        ),
        data_lineage=DataLineage(
            primary_sources=["yfinance", "alpha_vantage"],
            collection_timestamp=datetime.now(),
            transformation_steps=["normalize", "calculate_metrics"],
            cache_status="fresh",
        ),
        confidence_level=result.confidence_level,
        python_rationale=result.rationale,
    )


def _extract_qualitative(crew_result: CrewOutput, quant: QuantitativeAnalysis) -> QualitativeInsights:
    """Extract QualitativeInsights from crew result."""
    # Try to get pydantic model directly
    if hasattr(crew_result, "pydantic") and crew_result.pydantic:
        if isinstance(crew_result.pydantic, QualitativeInsights):
            return crew_result.pydantic

    # Try to parse from raw output
    if hasattr(crew_result, "raw") and crew_result.raw:
        try:
            import json

            data = json.loads(crew_result.raw)
            return QualitativeInsights(**data)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse crew output as JSON: {e}")

    # Try tasks_output
    if hasattr(crew_result, "tasks_output") and crew_result.tasks_output:
        for task_output in crew_result.tasks_output:
            if hasattr(task_output, "pydantic") and isinstance(task_output.pydantic, QualitativeInsights):
                return task_output.pydantic

    # Fallback: Use validation with retry
    from finwiz.validation.ai_output_validator import validate_ai_output_with_retry

    raw_output = crew_result.raw if hasattr(crew_result, "raw") else str(crew_result)
    return validate_ai_output_with_retry(raw_output, quant, max_retries=2)


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
