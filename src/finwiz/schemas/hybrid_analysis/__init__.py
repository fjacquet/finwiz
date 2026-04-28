"""
Hybrid analysis schemas for Python/AI integration.

This module provides Pydantic models for the hybrid analysis architecture
where Python performs deterministic calculations and AI provides contextual insights.
"""

from finwiz.schemas.hybrid_analysis.collected import CollectedData
from finwiz.schemas.hybrid_analysis.enriched import EnrichedAnalysis
from finwiz.schemas.hybrid_analysis.fact_pack import FactPack
from finwiz.schemas.hybrid_analysis.metadata import DataQualityMetrics
from finwiz.schemas.hybrid_analysis.qualitative import (
    ActionPlan,
    ContextualRiskInsights,
    FundamentalContextInsights,
    InvestmentSynthesis,
    QualitativeInsights,
    ScenarioProbabilities,
    SecAnalysisInsights,
    TechnicalStrategyInsights,
)
from finwiz.schemas.hybrid_analysis.quantitative import QuantitativeAnalysis

__all__ = [
    # Collect
    "CollectedData",
    # Metadata
    "DataQualityMetrics",
    # Quantitative
    "QuantitativeAnalysis",
    # Fact Pack (v5.2)
    "FactPack",
    # Qualitative
    "SecAnalysisInsights",
    "FundamentalContextInsights",
    "TechnicalStrategyInsights",
    "ContextualRiskInsights",
    "ScenarioProbabilities",
    "ActionPlan",
    "InvestmentSynthesis",
    "QualitativeInsights",
    # Enriched
    "EnrichedAnalysis",
]
