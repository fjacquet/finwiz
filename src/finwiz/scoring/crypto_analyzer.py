#!/usr/bin/env python
"""
Crypto Analyzer - Pure Python cryptocurrency analysis.

This module provides Python-based cryptocurrency analysis to replace AI crews
for 10-20x speed improvement and 100% cost reduction.
"""

import time
from typing import Any

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


def analyze_crypto_opportunities(session_id: str) -> dict[str, Any]:
    """Analyze cryptocurrency opportunities using pure Python.

    Routes through ``NewcomerDiscoveryPipeline``. A pipeline failure yields an
    empty, honestly-labelled result — never fabricated candidates. Inventing
    A-grade tickers to fill a gap is worse than reporting the gap.
    """
    start_time = time.time()

    try:
        logger.info("Using NewcomerDiscoveryPipeline for crypto discovery")
        from finwiz.scoring.discovery.pipeline import NewcomerDiscoveryPipeline

        pipeline = NewcomerDiscoveryPipeline("crypto")
        result = pipeline.discover(session_id)
        return pipeline._to_legacy_format(result, start_time)
    except Exception as e:
        logger.error("Newcomer discovery pipeline failed for crypto: %s", e)
        return {
            "opportunities": [],
            "analysis_summary": f"Crypto discovery unavailable this run: {e}",
            "performance_metrics": {
                "execution_time_seconds": time.time() - start_time,
                "opportunities_found": 0,
                "cost_usd": 0.0,
                "llm_calls_made": 0,
                "method": "newcomer_discovery_failed",
                "error": str(e),
            },
        }
