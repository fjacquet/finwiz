"""
Analysis Module - Functional Programming Approach.

This module provides pure functions with composition for financial analysis.
Combines Python quantitative scoring ($0) with AI qualitative insights.

Main Entry Point:
    analyze_holding(ticker, asset_class, company_name) -> (DeepAnalysisResult, EnrichedAnalysis)

Architecture:
    1. collect_raw_data(ctx) -> RawData         [Python tools]
    2. calculate_quantitative(ctx, raw) -> Quant   [$0 Python]
    3. generate_qualitative(ctx, quant) -> Qual    [AI crew]
    4. synthesize(ctx, quant, qual) -> Enriched    [Python]
"""

from finwiz.analysis.deep_analysis_pipeline import (
    AnalysisContext,
    analyze_holding,
    calculate_quantitative,
    collect_raw_data,
    generate_qualitative,
    synthesize_enriched_analysis,
)

__all__ = [
    "AnalysisContext",
    "analyze_holding",
    "calculate_quantitative",
    "collect_raw_data",
    "generate_qualitative",
    "synthesize_enriched_analysis",
]
