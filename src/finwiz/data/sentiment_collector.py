"""Sentiment and macro data collector.

Orchestrates news sentiment (per-holding) and macroeconomic data (per-session)
collection based on feature flags. Returns None when flags are disabled.
"""

from __future__ import annotations

import logging

from finwiz.config.features.flags import is_feature_enabled
from finwiz.schemas.macro import MacroSnapshot
from finwiz.schemas.sentiment import NewsSentimentResult

logger = logging.getLogger(__name__)


class SentimentMacroCollector:
    """Collects news sentiment and macro data based on feature flags.

    Macro data is cached at session level (collected once, shared across holdings).
    """

    def __init__(self) -> None:
        self._macro_snapshot: MacroSnapshot | None = None

    def collect_sentiment(self, ticker: str) -> NewsSentimentResult | None:
        """Collect news sentiment for a ticker if feature flag is enabled.

        Returns None when finnhub_news flag is disabled or on failure.
        """
        if not is_feature_enabled("finnhub_news"):
            return None
        try:
            from finwiz.data.adapters.finnhub_news_adapter import FinnhubNewsAdapter

            adapter = FinnhubNewsAdapter()
            return adapter.get_news_sentiment(ticker)
        except Exception as e:
            logger.warning(f"Sentiment collection failed for {ticker}: {e}")
            return None

    def collect_macro(self) -> MacroSnapshot | None:
        """Collect macro data if feature flag is enabled. Cached per session.

        Returns None when fred_macro flag is disabled or on failure.
        """
        if not is_feature_enabled("fred_macro"):
            return None
        if self._macro_snapshot is not None:
            return self._macro_snapshot
        try:
            from finwiz.data.adapters.fred_adapter import FREDAdapter

            fred = FREDAdapter()
            if not fred.is_available():
                logger.info("FRED adapter not available (no API key)")
                return None
            self._macro_snapshot = fred.get_macro_snapshot()

            # Enrich with Fear & Greed if enabled
            if is_feature_enabled("fear_greed_index"):
                try:
                    from finwiz.data.adapters.fear_greed_adapter import FearGreedAdapter

                    fg = FearGreedAdapter()
                    value, label = fg.get_fear_greed()
                    self._macro_snapshot.fear_greed_index = value
                    self._macro_snapshot.fear_greed_label = label  # type: ignore[assignment]
                except Exception as e:
                    logger.warning(f"Fear & Greed collection failed: {e}")

            return self._macro_snapshot
        except Exception as e:
            logger.warning(f"Macro collection failed: {e}")
            return None
