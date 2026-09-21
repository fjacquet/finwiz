"""Kraken crypto market-data adapter (public Ticker endpoint, no API key)."""

from datetime import datetime
from typing import Any

from crewai_custom_tools.core.results import parse_tool_result

from finwiz.data.adapters.crypto.base import (
    BaseCryptoAdapter,
    CryptoMarketData,
    normalize_crypto_symbol,
    positive_or_none,
)
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


def _indexed_float(value: Any, index: int) -> float | None:
    """Read one positive float out of a Kraken array field."""
    if not isinstance(value, (list, tuple)) or len(value) <= index:
        return None
    return positive_or_none(value[index])


class KrakenAdapter(BaseCryptoAdapter):
    """Reads the last traded price and single-venue 24h volume from Kraken."""

    def __init__(self, tool: Any | None = None) -> None:
        """Wire the underlying tool, constructed lazily so tests can inject one."""
        if tool is None:
            from crewai_custom_tools import KrakenTickerInfoTool

            tool = KrakenTickerInfoTool()
        self._tool = tool

    @property
    def source_name(self) -> str:
        """Return the lineage identifier for this source."""
        return "kraken"

    def fetch(self, ticker: str) -> CryptoMarketData | None:
        """Fetch price and volume for one ticker, or None when Kraken cannot answer."""
        symbol = normalize_crypto_symbol(ticker)
        pair = f"{symbol}USD"
        try:
            payload = parse_tool_result(self._tool._run(pair=pair))
        except Exception as exc:
            logger.warning("Kraken fetch failed for %s: %s", pair, exc)
            return None

        if not isinstance(payload, dict):
            logger.warning("Kraken returned a non-dict payload for %s", pair)
            return None

        price = _indexed_float(payload.get("c"), 0)
        if price is None:
            logger.warning("Kraken payload for %s carries no last trade price", pair)
            return None

        base_volume = _indexed_float(payload.get("v"), 1)

        return CryptoMarketData(
            ticker=ticker,
            source=self.source_name,
            timestamp=datetime.now(),
            confidence=1.0,
            price=price,
            # Kraken reports volume in base units for one venue; convert to USD
            # so the field carries the same unit as CoinGecko's aggregate.
            volume_24h=base_volume * price if base_volume is not None else None,
            raw_data=payload,
        )
