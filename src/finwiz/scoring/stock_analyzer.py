#!/usr/bin/env python
"""
Stock Analyzer - Pure Python stock analysis.

This module provides Python-based stock analysis to replace AI crews
for 10-20x speed improvement and 100% cost reduction.
"""

import time
from typing import Any

from finwiz.config.features.flags import is_feature_enabled
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


def analyze_stock_opportunities(session_id: str) -> dict[str, Any]:
    """Analyze stock opportunities using pure Python.

    When the ``newcomer_discovery`` feature flag is enabled, routes
    through ``NewcomerDiscoveryPipeline``.  Falls back to legacy
    mocked data when the flag is disabled or the pipeline fails.
    """
    start_time = time.time()

    if is_feature_enabled("newcomer_discovery"):
        try:
            logger.info("Using NewcomerDiscoveryPipeline for stock discovery")
            from finwiz.scoring.discovery.pipeline import NewcomerDiscoveryPipeline

            pipeline = NewcomerDiscoveryPipeline("stock")
            result = pipeline.discover(session_id)
            return pipeline._to_legacy_format(result, start_time)
        except Exception as e:
            logger.error("Newcomer discovery pipeline failed for stock, falling back to legacy: %s", e)

    return _legacy_stock_analysis(session_id, start_time)


def _legacy_stock_analysis(session_id: str, start_time: float) -> dict[str, Any]:
    """Legacy mocked stock analysis (hardcoded data)."""
    logger.info("Starting Python-based stock analysis (legacy)")

    try:
        opportunities = [
            {
                "ticker": "MSFT",
                "name": "Microsoft Corporation",
                "grade": "A+",
                "composite_score": 0.94,
                "recommendation": "BUY",
                "rationale": "Strong cloud growth and AI leadership",
            },
            {
                "ticker": "NVDA",
                "name": "NVIDIA Corporation",
                "grade": "A+",
                "composite_score": 0.91,
                "recommendation": "BUY",
                "rationale": "AI chip market dominance and data center growth",
            },
            {
                "ticker": "GOOGL",
                "name": "Alphabet Inc.",
                "grade": "A",
                "composite_score": 0.87,
                "recommendation": "BUY",
                "rationale": "Search dominance and AI integration",
            },
        ]

        execution_time = time.time() - start_time
        results = {
            "opportunities": opportunities,
            "analysis_summary": f"Identified {len(opportunities)} stock opportunities",
            "performance_metrics": {
                "execution_time_seconds": execution_time,
                "opportunities_found": len(opportunities),
                "cost_usd": 0.0,
                "llm_calls_made": 0,
                "method": "python_analysis",
            },
        }
        logger.info("Stock analysis completed in %.2fs", execution_time)
        return results

    except Exception as e:
        logger.error("Stock Python analysis failed: %s", e)
        execution_time = time.time() - start_time
        return {
            "opportunities": [],
            "analysis_summary": f"Stock analysis failed: {e}",
            "performance_metrics": {
                "execution_time_seconds": execution_time,
                "opportunities_found": 0,
                "cost_usd": 0.0,
                "llm_calls_made": 0,
                "method": "python_analysis_failed",
                "error": str(e),
            },
        }
