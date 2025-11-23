"""
Hybrid analysis schemas for Python/AI integration.

This module provides Pydantic models for the hybrid analysis architecture
where Python performs deterministic calculations and AI provides contextual insights.
"""

from finwiz.schemas.hybrid_analysis.enriched import EnrichedAnalysis
from finwiz.schemas.hybrid_analysis.metadata import (
    DataLineage,
    DataQualityMetrics,
)
from finwiz.schemas.hybrid_analysis.qualitative import (
    ContextualRiskInsights,
    FundamentalContextInsights,
    InvestmentSynthesis,
    QualitativeInsights,
    SecAnalysisInsights,
    TechnicalStrategyInsights,
)
from finwiz.schemas.hybrid_analysis.quantitative import QuantitativeAnalysis

__all__ = [
    # Metadata
    "DataQualityMetrics",
    "DataLineage",
    # Quantitative
    "QuantitativeAnalysis",
    # Qualitative
    "SecAnalysisInsights",
    "FundamentalContextInsights",
    "TechnicalStrategyInsights",
    "ContextualRiskInsights",
    "InvestmentSynthesis",
    "QualitativeInsights",
    # Enriched
    "EnrichedAnalysis",
]
