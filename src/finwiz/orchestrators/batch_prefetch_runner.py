"""Batch prefetch runner for deep analysis integration.

Wires BatchDataPreFetcher into the main analysis flow so all ticker data
is fetched in a single batch call before concurrent deep analysis begins.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from finwiz.config.batch_prefetch_config import (
    load_batch_prefetch_config,
    should_use_alpha_vantage,
)
from finwiz.integration.batch_data_prefetcher import BatchDataPreFetcher


def run_batch_prefetch(
    state: Any,
    holdings: list[dict[str, Any]],
    logger: logging.Logger,
) -> dict[str, Any]:
    """Run batch prefetch for all holdings and update state.

    Args:
        state: FinwizState instance (updated in-place)
        holdings: List of holding dicts with 'ticker' key
        logger: Logger instance

    Returns:
        Prefetched data dict (also stored in state.prefetched_data)
    """
    config = load_batch_prefetch_config()

    if not config.enabled:
        logger.info("Batch prefetch disabled via BATCH_PREFETCH_ENABLED")
        return {}

    if len(holdings) < config.min_holdings_for_batch:
        logger.info(
            "Batch prefetch skipped: %d holdings < min %d",
            len(holdings),
            config.min_holdings_for_batch,
        )
        return {}

    tickers = [h.get("ticker", "") for h in holdings if h.get("ticker")]
    if not tickers:
        logger.warning("No valid tickers found in holdings")
        return {}

    logger.info("Batch prefetching %d tickers before deep analysis", len(tickers))
    start = time.time()

    try:
        prefetcher = BatchDataPreFetcher(
            session_id=state.session_id,
            enable_alpha_vantage=should_use_alpha_vantage(),
        )
        prefetched_data = prefetcher.prefetch_all_data(tickers)
    except Exception:
        logger.exception("Batch prefetch failed, continuing without prefetched data")
        return {}

    elapsed = time.time() - start
    state.batch_prefetch_enabled = True
    state.prefetched_data = json.loads(json.dumps(prefetched_data, default=str))
    state.batch_prefetch_metrics = {
        "tickers_requested": len(tickers),
        "tickers_fetched": sum(1 for v in prefetched_data.values() if not v.get("failed")),
        "elapsed_seconds": round(elapsed, 1),
    }

    logger.info(
        "Batch prefetch complete: %d/%d tickers in %.1fs",
        state.batch_prefetch_metrics["tickers_fetched"],
        len(tickers),
        elapsed,
    )
    return prefetched_data
