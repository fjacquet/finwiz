"""Qualify stage: AI-generated qualitative insights for one holding.

This stage is the only one allowed to emit a DEGRADED outcome — when the AI
returns null/empty, a Python proxy fallback is used and the outcome is labelled
DEGRADED with fallback_used="python_proxy_qualitative" (E1).
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field

from finwiz.analysis._helpers import _build_crew_inputs, _get_analysis_crew
from finwiz.analysis.stages._qualify_fallbacks import (
    _create_fallback_qualitative,
    _create_python_qualitative,
)
from finwiz.analysis.stages._resilience import StageContext, stage
from finwiz.schemas.hybrid_analysis import (
    ContextualRiskInsights,
    EnrichedAnalysis,
    FundamentalContextInsights,
    InvestmentSynthesis,
    QualitativeInsights,
    QuantitativeAnalysis,
    SecAnalysisInsights,
    TechnicalStrategyInsights,
)
from finwiz.schemas.hybrid_analysis.fact_pack import FactPack
from finwiz.schemas.hybrid_analysis.strategic import StrategicAnalysis
from finwiz.schemas.stage_contract import StageOutcome, StageProvenance, StageResult

if TYPE_CHECKING:
    from crewai import CrewOutput

    from finwiz.analysis.deep_analysis_pipeline import AnalysisContext

logger = logging.getLogger(__name__)


class _QualitativeInsightsRaw(BaseModel):
    """Bridging schema for the LLM's qualitative output.

    Mirrors :class:`QualitativeInsights` minus the Python-controlled fields
    that produced the 2026-04-28 LLM/Pydantic thrash:

    * ``fact_pack`` is dropped — Python fetches verified facts via
      :mod:`finwiz.analysis.fact_pack_research` and overlays them on
      promotion. The LLM never has to satisfy ``FactPack``'s freshness
      ``model_validator`` or its 200/1000-char string caps.
    * ``analysis_timestamp`` is dropped — Python sets it on promotion.

    ``extra="ignore"`` so any of those keys the LLM still emits are dropped
    silently rather than triggering a retry loop.
    """

    investment_synthesis: InvestmentSynthesis | None = Field(default=None)
    sec_insights: SecAnalysisInsights | None = Field(default=None)
    fundamental_context: FundamentalContextInsights | None = Field(default=None)
    technical_strategy: TechnicalStrategyInsights | None = Field(default=None)
    contextual_risks: ContextualRiskInsights | None = Field(default=None)
    strategic_analysis: StrategicAnalysis | None = Field(default=None)
    ai_confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")


def _promote_to_qualitative(
    raw: _QualitativeInsightsRaw,
    fact_pack: FactPack | None = None,
) -> QualitativeInsights:
    """Promote a raw LLM-bridging payload to the canonical schema.

    Python attaches the deterministic ``fact_pack`` (if available) and a
    fresh ``analysis_timestamp``. Validation runs against the public schema
    so internal Python code paths still benefit from strict validation.
    """
    return QualitativeInsights.model_validate(
        {
            **raw.model_dump(),
            "fact_pack": fact_pack,
            "analysis_timestamp": datetime.now(UTC),
        },
    )


def _run_deep_analysis_crew(asset_class: str, crew: Any, crew_inputs: dict[str, Any]) -> Any:
    """Execute the deep-analysis crew, loop-aware, re-raising hard failures.

    Shared by the initial qualitative attempt and the retry callback so both use
    the same event-loop handling and timeout wrapper.
    """
    import asyncio
    import concurrent.futures

    from finwiz.infrastructure.resilience.crew_execution import execute_crew_with_timeout

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    name = f"deep_analysis_{asset_class}"
    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, execute_crew_with_timeout(name, crew, crew_inputs))
            return future.result()
    return asyncio.run(execute_crew_with_timeout(name, crew, crew_inputs))


def _try_ai_qualify(
    ctx: AnalysisContext,
    quant: QuantitativeAnalysis,
    raw_data: dict[str, Any] | None = None,
    fact_pack: Any = None,
) -> QualitativeInsights | None:
    """Attempt AI-driven qualitative insights. Returns None when AI fails or returns empty.

    Skips the AI call in MAXIMUM_SPEED mode and returns None so the caller can
    take the DEGRADED branch.
    """
    from finwiz.config.performance.performance_config import is_maximum_speed_mode

    if is_maximum_speed_mode():
        logger.info(f"MAXIMUM_SPEED mode: Skipping AI crew for {ctx.ticker}")
        return None

    logger.info(f"Generating qualitative insights for {ctx.ticker}")

    crew = _get_analysis_crew(ctx.asset_class)
    crew_inputs = _build_crew_inputs(ctx, quant, raw_data, fact_pack=fact_pack)

    import traceback

    try:
        crew_result = _run_deep_analysis_crew(ctx.asset_class, crew, crew_inputs)
    except (OSError, TimeoutError):
        # Transient I/O or timeout — let @stage decorator retry then record FAILED.
        raise
    except Exception:
        # Any other hard failure (network protocol error, provider error, etc.) —
        # re-raise so the @stage decorator captures it as FAILED, not DEGRADED.
        raise

    def _retry_crew(format_instructions: str, retry_context: str) -> Any:
        """Re-run the crew with explicit JSON format instructions.

        Wired into ``validate_ai_output_with_retry`` so a first output that fails
        structured parsing gets one real corrected attempt before the Python-only
        fallback — instead of the old dead no-callback path that always degraded.
        Returns a canonical dict on success, or the raw output on failure so the
        validator cleanly exhausts its retries and falls back to Python-only.
        """
        retry_inputs = dict(crew_inputs)
        retry_inputs["retry_guidance"] = (
            "⚠️ RETRY — la sortie précédente n'a pas pu être parsée en JSON "
            f"structuré. {retry_context}\n"
            "Réémets UNIQUEMENT un objet JSON valide conforme au schéma, sans "
            "aucun texte ni balise markdown autour.\n"
            f"{format_instructions}"
        )
        logger.info(f"Retrying qualitative crew for {ctx.ticker} with explicit format instructions")
        retry_result = _run_deep_analysis_crew(ctx.asset_class, crew, retry_inputs)
        retry_qual = _extract_qualitative(retry_result, quant, fact_pack=fact_pack)
        if retry_qual is not None and _has_qualitative_content(retry_qual):
            return retry_qual.model_dump()
        return retry_result.raw if hasattr(retry_result, "raw") else str(retry_result)

    # Only return None when the AI call succeeded but returned empty/null content.
    # This is the one legitimate trigger for the DEGRADED branch.
    qual = _extract_qualitative(crew_result, quant, fact_pack=fact_pack, retry_callback=_retry_crew)
    if qual is not None and _has_qualitative_content(qual):
        logger.info(f"Qualitative insights generated for {ctx.ticker}")
        return qual
    logger.warning(f"AI returned empty qualitative content for {ctx.ticker}: traceback=\n{traceback.format_stack()[-1]}")
    return None


def _python_proxy_qualify(ctx: AnalysisContext, quant: QuantitativeAnalysis) -> QualitativeInsights:
    """Return Python-template qualitative insights as a fallback proxy."""
    return _create_python_qualitative(ctx, quant)


def _generate_qualitative_inner(
    ctx: AnalysisContext,
    quant: QuantitativeAnalysis,
    raw_data: dict[str, Any] | None = None,
    fact_pack: Any = None,
) -> QualitativeInsights:
    """Silent-fallback path for legacy shim callers.

    Non-stage callers (generate_qualitative shim, parallel runner) get the
    traditional behaviour: AI on success, Python proxy on failure — no
    StageResult envelope, no DEGRADED label.
    """
    ai = _try_ai_qualify(ctx, quant, raw_data, fact_pack=fact_pack)
    if ai is not None:
        return ai
    return _python_proxy_qualify(ctx, quant)


@stage(name="qualify", timeout_s=180, retries=2, allow_degrade=True)
def qualify(ctx: StageContext, quant: QuantitativeAnalysis, raw: dict[str, Any]) -> QualitativeInsights:
    """Qualitative stage. Returns OK on AI success, DEGRADED on Python fallback."""
    analysis_ctx: AnalysisContext = ctx.extras["analysis_ctx"]
    fact_pack = ctx.extras.get("fact_pack")
    ai = _try_ai_qualify(analysis_ctx, quant, raw, fact_pack=fact_pack)
    if ai is not None:
        # Attach the fact_pack used for grounding to the qualitative payload
        if isinstance(ai, QualitativeInsights) and fact_pack is not None:
            ai = ai.model_copy(update={"fact_pack": fact_pack})
        result: Any = StageResult(
            payload=ai,
            provenance=StageProvenance(
                stage="qualify",
                outcome=StageOutcome.OK,
                duration_ms=0,  # decorator backfills
            ),
        )
        return result
    proxy = _python_proxy_qualify(analysis_ctx, quant)
    degraded: Any = StageResult(
        payload=proxy,
        provenance=StageProvenance(
            stage="qualify",
            outcome=StageOutcome.DEGRADED,
            fallback_used="python_proxy_qualitative",
            reason="AI provider returned null/empty after retries",
            duration_ms=0,
        ),
    )
    return degraded


# Legacy shim — preserves existing call sites
def generate_qualitative(
    ctx: AnalysisContext,
    quant: QuantitativeAnalysis,
    raw_data: dict[str, Any] | None = None,
) -> QualitativeInsights:
    """Legacy entry point. Uses silent fallback (no DEGRADED label)."""
    return _generate_qualitative_inner(ctx, quant, raw_data)


def _run_qualitative_and_strategic_in_parallel(
    ctx: AnalysisContext,
    quant: QuantitativeAnalysis,
    raw_data: dict[str, Any],
) -> tuple[QualitativeInsights, Any]:
    """Run the qualitative crew and the strategic Perplexity research concurrently.

    Strategic research is gated to stocks — PESTEL/SWOT/Porter were designed
    for companies and adapt poorly to ETFs and crypto.
    """
    import concurrent.futures

    do_strategic = ctx.asset_class == "stock"
    sector = str(raw_data.get("sector") or raw_data.get("Sector") or "")
    industry = str(raw_data.get("industry") or raw_data.get("Industry") or "")
    description = str(raw_data.get("longBusinessSummary") or raw_data.get("description") or raw_data.get("company_description") or "")

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        qual_future = pool.submit(generate_qualitative, ctx, quant, raw_data)
        strategic_future = pool.submit(_safe_strategic, ctx.ticker, sector, industry, description) if do_strategic else None

        try:
            qual = qual_future.result()
        except Exception as exc:
            logger.error(f"Qualitative generation failed for {ctx.ticker}: {exc}")
            qual = _create_fallback_qualitative(ctx, quant, str(exc))

        if strategic_future is None:
            return qual, None
        try:
            strategic = strategic_future.result()
        except Exception as exc:
            logger.warning(f"Strategic research failed for {ctx.ticker}: {exc}")
            strategic = None
        return qual, strategic


def _safe_strategic(ticker: str, sector: str, industry: str, description: str) -> Any:
    """Wrapper that swallows import-time/runtime issues with the strategic module."""
    try:
        from finwiz.analysis.strategic_research import gather_strategic_analysis_sync

        return gather_strategic_analysis_sync(
            ticker=ticker,
            sector=sector,
            industry=industry,
            description=description,
        )
    except Exception as exc:
        logger.warning(f"Strategic research skipped for {ticker}: {exc}")
        return None


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


def _extract_qualitative(
    crew_result: CrewOutput,
    quant: QuantitativeAnalysis,
    fact_pack: FactPack | None = None,
    retry_callback: Any = None,
) -> QualitativeInsights:
    """Extract QualitativeInsights from a crew result.

    The deep-analysis crew now emits :class:`_QualitativeInsightsRaw` (no
    fact_pack, no analysis_timestamp). When that bridging schema is found,
    promote it via :func:`_promote_to_qualitative` so Python attaches the
    deterministic fact_pack and a fresh timestamp.

    Older code paths that still produce :class:`QualitativeInsights` directly
    continue to work — we just hand them through.

    ``retry_callback`` (optional) is forwarded to
    :func:`validate_ai_output_with_retry` as the last-resort path: when all
    direct extraction fails it re-runs the crew once with explicit format
    instructions before falling back to Python-only analysis.
    """

    def _coerce(candidate: Any) -> QualitativeInsights | None:
        """Return a canonical QualitativeInsights from raw or canonical input."""
        if isinstance(candidate, QualitativeInsights):
            return candidate
        if isinstance(candidate, _QualitativeInsightsRaw):
            return _promote_to_qualitative(candidate, fact_pack=fact_pack)
        return None

    # Try to get pydantic model directly
    if hasattr(crew_result, "pydantic") and crew_result.pydantic:
        # Case 1: Direct QualitativeInsights or _QualitativeInsightsRaw
        coerced = _coerce(crew_result.pydantic)
        if coerced is not None and _has_qualitative_content(coerced):
            return coerced
        if coerced is not None:
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
                # Check for direct QualitativeInsights or raw bridging schema
                coerced = _coerce(task_output.pydantic)
                if coerced is not None and _has_qualitative_content(coerced):
                    logger.info("Extracted QualitativeInsights from tasks_output")
                    return coerced
                # Check for EnrichedAnalysis containing qualitative
                if isinstance(task_output.pydantic, EnrichedAnalysis) and task_output.pydantic.qualitative:
                    qual = task_output.pydantic.qualitative
                    if _has_qualitative_content(qual):
                        logger.info("Extracted QualitativeInsights from tasks_output EnrichedAnalysis")
                        return qual

    # Try to parse from raw output. Prefer the bridging schema (it's what the
    # crew is asked to produce now); fall back to the canonical schema for
    # legacy outputs.
    if hasattr(crew_result, "raw") and crew_result.raw:
        try:
            data = json.loads(crew_result.raw)
            # Try to extract qualitative from EnrichedAnalysis-shaped JSON
            if "qualitative" in data and isinstance(data["qualitative"], dict):
                qual = _promote_to_qualitative(
                    _QualitativeInsightsRaw.model_validate(data["qualitative"]),
                    fact_pack=fact_pack,
                )
                if _has_qualitative_content(qual):
                    logger.info("Extracted QualitativeInsights from raw JSON qualitative field")
                    return qual
            # Try direct parse via the bridging schema
            qual = _promote_to_qualitative(
                _QualitativeInsightsRaw.model_validate(data),
                fact_pack=fact_pack,
            )
            if _has_qualitative_content(qual):
                return qual
            logger.warning("Parsed QualitativeInsights has no content, using fallback")
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.warning(f"Failed to parse crew output as JSON: {e}")

    # Fallback: Use validation with retry
    from finwiz.validation.ai_output import validate_ai_output_with_retry

    logger.warning("All extraction methods failed, falling back to validation with retry")
    raw_output = crew_result.raw if hasattr(crew_result, "raw") else str(crew_result)
    # One crew re-run with explicit format instructions (when a callback is
    # wired) before Python-only fallback.
    return validate_ai_output_with_retry(raw_output, quant, retry_callback=retry_callback, max_retries=1)
