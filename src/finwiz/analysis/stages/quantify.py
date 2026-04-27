"""Quantify stage: deterministic Python scoring."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from finwiz.flow_state_models import DeepAnalysisResult
from finwiz.schemas.hybrid_analysis import QuantitativeAnalysis

if TYPE_CHECKING:
    from finwiz.analysis.deep_analysis_pipeline import AnalysisContext

logger = logging.getLogger(__name__)


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


def _result_to_quantitative(result: DeepAnalysisResult) -> QuantitativeAnalysis:
    """Convert DeepAnalysisResult to QuantitativeAnalysis schema."""
    from datetime import datetime

    from finwiz.analysis._helpers import _filter_numeric_values
    from finwiz.schemas.hybrid_analysis.metadata import DataQualityMetrics

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
