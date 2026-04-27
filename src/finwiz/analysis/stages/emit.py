"""Emit stage: produce the final (DeepAnalysisResult, EnrichedAnalysis) pair."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from finwiz.analysis.stages.synthesize import _apply_strategic_recompute
from finwiz.flow_state_models import DeepAnalysisResult
from finwiz.schemas.hybrid_analysis import EnrichedAnalysis

if TYPE_CHECKING:
    from finwiz.analysis.deep_analysis_pipeline import AnalysisContext

logger = logging.getLogger(__name__)


def build_verdict(
    ctx: AnalysisContext,
    result: DeepAnalysisResult,
    enriched: EnrichedAnalysis,
    strategic: object | None,
    processing_time: float,
) -> tuple[DeepAnalysisResult, EnrichedAnalysis]:
    """Build the user-visible verdict from the enriched analysis.

    Body moved verbatim from analyze_holding's final-assembly portion.
    Re-applies the strategic recompute when a strategic analysis is available,
    then logs completion and returns the finalised (result, enriched) pair.
    """
    if strategic is not None and enriched.qualitative is not None and enriched.qualitative.strategic_analysis is not None:
        result = _apply_strategic_recompute(result, enriched)

    logger.info(f"Pipeline complete for {ctx.ticker}: {processing_time:.1f}s")
    return result, enriched
