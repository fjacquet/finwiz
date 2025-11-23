"""
Backward compatibility layer for legacy schema names.

This module provides re-exports of old schema names pointing to new hybrid
analysis schemas. It includes deprecation warnings to guide users toward
the new schema structure.

DEPRECATED: This module is provided for backward compatibility only.
New code should import directly from finwiz.schemas.hybrid_analysis.

Migration Path:
    Old: from finwiz.schemas.stock_analysis_result import StockAnalysisResult
    New: from finwiz.schemas.hybrid_analysis import EnrichedAnalysis

    Old: from finwiz.schemas.deep_analysis_result import DeepAnalysisResult
    New: from finwiz.schemas.hybrid_analysis import EnrichedAnalysis
"""

import warnings
from typing import Any

from finwiz.schemas.hybrid_analysis import (
    ContextualRiskInsights,
    DataLineage,
    DataQualityMetrics,
    EnrichedAnalysis,
    FundamentalContextInsights,
    InvestmentSynthesis,
    QualitativeInsights,
    QuantitativeAnalysis,
    SecAnalysisInsights,
    TechnicalStrategyInsights,
)


def _deprecation_warning(old_name: str, new_name: str) -> None:
    """Issue deprecation warning for legacy schema usage."""
    warnings.warn(
        f"{old_name} is deprecated and will be removed in a future version. "
        f"Use {new_name} instead. "
        f"See finwiz.schemas.hybrid_analysis for the new schema structure.",
        DeprecationWarning,
        stacklevel=3,
    )


class StockAnalysisResult(EnrichedAnalysis):
    """
    DEPRECATED: Legacy name for EnrichedAnalysis.

    This class is provided for backward compatibility only.
    New code should use EnrichedAnalysis from finwiz.schemas.hybrid_analysis.

    Migration:
        Old: from finwiz.schemas.stock_analysis_result import StockAnalysisResult
        New: from finwiz.schemas.hybrid_analysis import EnrichedAnalysis
    """

    def __init__(self, **data: Any) -> None:
        _deprecation_warning("StockAnalysisResult", "EnrichedAnalysis")
        super().__init__(**data)


class DeepAnalysisResult(EnrichedAnalysis):
    """
    DEPRECATED: Legacy name for EnrichedAnalysis.

    This class is provided for backward compatibility only.
    New code should use EnrichedAnalysis from finwiz.schemas.hybrid_analysis.

    Migration:
        Old: from finwiz.schemas.deep_analysis_result import DeepAnalysisResult
        New: from finwiz.schemas.hybrid_analysis import EnrichedAnalysis
    """

    def __init__(self, **data: Any) -> None:
        _deprecation_warning("DeepAnalysisResult", "EnrichedAnalysis")
        super().__init__(**data)


# Re-export all hybrid analysis schemas for convenience
__all__ = [
    # Legacy names (deprecated)
    "StockAnalysisResult",
    "DeepAnalysisResult",
    # New schema names (recommended)
    "EnrichedAnalysis",
    "QuantitativeAnalysis",
    "QualitativeInsights",
    "SecAnalysisInsights",
    "FundamentalContextInsights",
    "TechnicalStrategyInsights",
    "ContextualRiskInsights",
    "InvestmentSynthesis",
    "DataQualityMetrics",
    "DataLineage",
]
