"""Collect stage: pure-Python raw-data gathering for one holding."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from finwiz.analysis.deep_analysis_pipeline import AnalysisContext

logger = logging.getLogger(__name__)


def collect_raw_data(
    ctx: AnalysisContext,
    prefetched_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Pure function: Collect raw financial data using Python tools.

    Args:
        ctx: Analysis context with ticker and asset class
        prefetched_data: Batch-prefetched data dict (from BatchDataPreFetcher)

    Returns:
        Dictionary containing raw financial data from multiple sources
    """
    from datetime import datetime
    from types import SimpleNamespace

    from finwiz.orchestrators.deep_analysis_data_collector import DeepAnalysisDataCollector

    logger.info(f"Collecting raw data for {ctx.ticker} ({ctx.asset_class})")

    # Create a minimal state object with required fields
    # DeepAnalysisDataCollector expects state.full_date
    minimal_state = SimpleNamespace(full_date=datetime.now().isoformat())

    collector = DeepAnalysisDataCollector(state=minimal_state)
    batch_enabled = prefetched_data is not None
    raw_data = collector.collect_data(
        ctx.ticker,
        ctx.asset_class,
        batch_enabled=batch_enabled,
        prefetched_data=prefetched_data,
    )
    logger.info(f"Raw data collected for {ctx.ticker}: {len(raw_data)} fields")

    # v4 Data Intelligence: collect sentiment and macro data if feature flags are enabled
    try:
        from finwiz.data.sentiment_collector import SentimentMacroCollector

        v4_collector = SentimentMacroCollector()
        sentiment = v4_collector.collect_sentiment(ctx.ticker)
        macro = v4_collector.collect_macro()
        if sentiment is not None:
            raw_data["news_sentiment"] = sentiment.model_dump(mode="json")
            logger.info(f"News sentiment collected for {ctx.ticker}: {sentiment.article_count} articles")
        if macro is not None:
            raw_data["macro_snapshot"] = macro.model_dump(mode="json")
            logger.info(f"Macro snapshot collected: {macro.get_market_regime()} regime")
    except Exception as e:
        logger.debug(f"v4 sentiment/macro collection skipped for {ctx.ticker}: {e}")

    return raw_data
