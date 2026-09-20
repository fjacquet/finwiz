"""Shared shapes for crypto market-data adapters."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any

_QUOTE_SUFFIXES = ("-USD", "-USDT", "-USDC", "-EUR")


def normalize_crypto_symbol(ticker: str) -> str:
    """Strip the quote-currency suffix a yfinance-style crypto ticker carries.

    CoinGecko and Kraken both key on the bare base symbol; `BTC-USD` is a
    yfinance convention and resolves nowhere else.
    """
    symbol = ticker.strip().upper()
    for suffix in _QUOTE_SUFFIXES:
        if symbol.endswith(suffix):
            return symbol[: -len(suffix)]
    return symbol


def positive_or_none(value: Any) -> float | None:
    """Coerce to a strictly positive float, else None.

    Upstream sources signal "no data" with 0 as readily as with null, and a
    zero market cap or volume is never a real measurement.
    """
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


@dataclass
class CryptoMarketData:
    """Market data as reported by a single source."""

    ticker: str
    source: str
    timestamp: datetime
    confidence: float
    price: float | None = None
    market_cap: float | None = None
    volume_24h: float | None = None
    circulating_supply: float | None = None
    max_supply: float | None = None
    raw_data: dict[str, Any] | None = None
    warnings: list[str] | None = None

    def __post_init__(self) -> None:
        """Normalize warnings and validate confidence."""
        if self.warnings is None:
            self.warnings = []
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")


class BaseCryptoAdapter(ABC):
    """Base class for crypto market-data adapters.

    Synchronous by design: the underlying tools are synchronous and the calling
    collector runs one thread per holding.
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the identifier recorded in lineage for this source."""

    @abstractmethod
    def fetch(self, ticker: str) -> CryptoMarketData | None:
        """Return market data, or None when this source cannot answer.

        Implementations never raise for an unavailable source and never invent
        a value: an unanswerable lookup is None.
        """
