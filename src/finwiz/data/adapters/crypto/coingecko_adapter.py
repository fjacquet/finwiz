"""CoinGecko crypto market-data adapter."""

from datetime import datetime
from typing import Any

from finwiz.data.adapters.crypto.base import (
    BaseCryptoAdapter,
    CryptoMarketData,
    normalize_crypto_symbol,
    positive_or_none,
)
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

# EnhancedCryptoAnalysisTool does not raise on an unknown symbol: it returns a
# zeroed-out payload (market_cap: 0, etc.) tagged with this marker rather than
# an error. This adapter checks for the marker below and discards that payload
# as None. The old collector (now deleted) did not check for it: it treated
# the tool's market_cap: 0 as merely "missing" and layered its own fabricated
# $10B default on top. The $10B was the collector's, never this tool's.
FALLBACK_MARKER = "Fallback Data"


class CoinGeckoAdapter(BaseCryptoAdapter):
    """Reads price, market cap, volume and supply from CoinGecko."""

    def __init__(self, tool: Any | None = None) -> None:
        """Wire the underlying tool, constructed lazily so tests can inject one."""
        if tool is None:
            from finwiz.tools.enhanced_crypto_tool import EnhancedCryptoAnalysisTool

            tool = EnhancedCryptoAnalysisTool()
        self._tool = tool

    @property
    def source_name(self) -> str:
        """Return the lineage identifier for this source."""
        return "coingecko"

    def fetch(self, ticker: str) -> CryptoMarketData | None:
        """Fetch market data for one ticker, or None when CoinGecko cannot answer."""
        symbol = normalize_crypto_symbol(ticker)
        try:
            result = self._tool._run(
                symbol=symbol,
                include_thesis=False,
                include_risk_assessment=False,
                include_perplexity=False,
            )
        except Exception as exc:
            logger.warning("CoinGecko fetch failed for %s: %s", symbol, exc)
            return None

        if not isinstance(result, dict):
            logger.warning("CoinGecko returned a non-dict payload for %s", symbol)
            return None

        data = result.get("crypto_data")
        if not isinstance(data, dict):
            logger.warning("CoinGecko payload for %s carries no crypto_data", symbol)
            return None

        if FALLBACK_MARKER in (data.get("sources") or []):
            logger.warning("CoinGecko has no entry for %s; discarding fabricated fallback payload", symbol)
            return None

        volume = data.get("total_volume")
        if volume is None:
            volume = data.get("volume_24h")

        return CryptoMarketData(
            ticker=ticker,
            source=self.source_name,
            timestamp=datetime.now(),
            confidence=1.0,
            price=positive_or_none(data.get("current_price")),
            market_cap=positive_or_none(data.get("market_cap")),
            volume_24h=positive_or_none(volume),
            circulating_supply=positive_or_none(data.get("circulating_supply")),
            max_supply=positive_or_none(data.get("max_supply")),
            raw_data=data,
        )
