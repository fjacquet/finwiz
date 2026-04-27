"""Collect stage: pure-Python raw-data gathering for one holding."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from finwiz.analysis.stages._resilience import StageContext, stage
from finwiz.schemas.hybrid_analysis.collected import CollectedData

if TYPE_CHECKING:
    from finwiz.analysis.deep_analysis_pipeline import AnalysisContext

logger = logging.getLogger(__name__)


def _collect_raw_data_inner(
    ctx: AnalysisContext,
    prefetched_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """The original collect_raw_data body — extracted for testability."""
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


@stage(name="collect", timeout_s=120, retries=1)
def collect(ctx: StageContext) -> CollectedData:
    """Stage entry point: wraps the raw-data collector in a typed payload."""
    # The orchestrator populates ctx.extras["analysis_ctx"] and optionally
    # ctx.extras["prefetched_data"]. Use .get() so the mock boundary is at
    # _collect_raw_data_inner — tests can patch that without needing extras.
    analysis_ctx: AnalysisContext = ctx.extras.get("analysis_ctx")  # type: ignore[assignment]
    prefetched: dict[str, Any] | None = ctx.extras.get("prefetched_data")
    raw = _collect_raw_data_inner(analysis_ctx, prefetched)
    return CollectedData(data=raw)


# Backwards-compatible legacy entry point (callers/tests still use this)
def collect_raw_data(
    ctx: AnalysisContext,
    prefetched_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Legacy entry point used by the facade. Delegates to _collect_raw_data_inner."""
    return _collect_raw_data_inner(ctx, prefetched_data)
