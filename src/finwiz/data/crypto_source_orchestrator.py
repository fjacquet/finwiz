"""Multi-source acquisition of crypto market data.

Mirrors the contract of `DataSourceOrchestrator` (per-field lineage, pinned
confidence, None for anything unresolved) without reusing `FundamentalData`,
which is hardwired to equity metrics.
"""

from dataclasses import dataclass, field
from datetime import datetime

from finwiz.data.adapters.crypto.base import BaseCryptoAdapter, CryptoMarketData
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

DIVERGENCE_WARN_PCT = 2.0

_PRICE_CONFIDENCE = {"coingecko": 1.0, "yfinance": 0.8, "kraken": 0.6}
_DIVERGENCE_PENALTY = 0.2
_UNRESOLVED_PENALTY = 0.1


@dataclass
class CryptoLineage:
    """Records which source supplied each field."""

    price_source: str | None = None
    market_cap_source: str | None = None
    volume_24h_source: str | None = None
    supply_source: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        """Convert to a dictionary for logging and export."""
        return {
            "price": self.price_source,
            "market_cap": self.market_cap_source,
            "volume_24h": self.volume_24h_source,
            "supply": self.supply_source,
        }


@dataclass
class CryptoOrchestrationResult:
    """Resolved crypto market data plus the provenance of every field."""

    ticker: str
    timestamp: datetime
    price: float | None = None
    market_cap: float | None = None
    volume_24h: float | None = None
    circulating_supply: float | None = None
    max_supply: float | None = None
    lineage: CryptoLineage = field(default_factory=CryptoLineage)
    confidence: float = 0.0
    sources_attempted: list[str] = field(default_factory=list)
    sources_succeeded: list[str] = field(default_factory=list)
    sources_failed: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    price_divergence_pct: float | None = None


class CryptoSourceOrchestrator:
    """Resolves crypto market data across CoinGecko, yfinance and Kraken."""

    def __init__(self, coingecko: BaseCryptoAdapter | None = None, kraken: BaseCryptoAdapter | None = None) -> None:
        """Wire the adapters, constructed lazily so tests can inject stubs."""
        if coingecko is None:
            from finwiz.data.adapters.crypto.coingecko_adapter import CoinGeckoAdapter

            coingecko = CoinGeckoAdapter()
        if kraken is None:
            from finwiz.data.adapters.crypto.kraken_adapter import KrakenAdapter

            kraken = KrakenAdapter()
        self._coingecko = coingecko
        self._kraken = kraken

    def fetch(self, ticker: str, *, yfinance_price: float | None = None) -> CryptoOrchestrationResult:
        """Resolve every crypto field for one ticker, leaving gaps as None."""
        result = CryptoOrchestrationResult(ticker=ticker, timestamp=datetime.now())

        gecko = self._attempt(self._coingecko, ticker, result)
        # Kraken runs on every fetch: it is the cross-check when CoinGecko
        # answered, and a price candidate when it did not.
        kraken = self._attempt(self._kraken, ticker, result)

        self._resolve_price(result, gecko, kraken, yfinance_price)
        self._resolve_market_data(result, gecko, kraken)
        result.confidence = self._compute_confidence(result)

        logger.info(
            "Crypto sources for %s: price=%s lineage=%s confidence=%.2f divergence=%s",
            ticker,
            result.price,
            result.lineage.to_dict(),
            result.confidence,
            result.price_divergence_pct,
        )
        return result

    def _attempt(self, adapter: BaseCryptoAdapter, ticker: str, result: CryptoOrchestrationResult) -> CryptoMarketData | None:
        """Run one adapter, recording the attempt on the result."""
        name = adapter.source_name
        result.sources_attempted.append(name)
        data = adapter.fetch(ticker)
        if data is None:
            result.sources_failed.append(name)
        else:
            result.sources_succeeded.append(name)
        return data

    def _resolve_price(
        self,
        result: CryptoOrchestrationResult,
        gecko: CryptoMarketData | None,
        kraken: CryptoMarketData | None,
        yfinance_price: float | None,
    ) -> None:
        """Pick the price by fallback order, then observe the disagreement."""
        candidates: dict[str, float] = {}
        if gecko is not None and gecko.price is not None:
            candidates["coingecko"] = gecko.price
        if yfinance_price is not None and yfinance_price > 0:
            candidates["yfinance"] = float(yfinance_price)
        if kraken is not None and kraken.price is not None:
            candidates["kraken"] = kraken.price

        for source in ("coingecko", "yfinance", "kraken"):
            if source in candidates:
                result.price = candidates[source]
                result.lineage.price_source = source
                break

        if len(candidates) >= 2:
            values = list(candidates.values())
            low, high = min(values), max(values)
            result.price_divergence_pct = (high - low) / low * 100.0
            if result.price_divergence_pct > DIVERGENCE_WARN_PCT:
                message = f"Price divergence {result.price_divergence_pct:.2f}% across {sorted(candidates)}; keeping {result.lineage.price_source}"
                result.warnings.append(message)
                logger.warning("%s for %s", message, result.ticker)

    def _resolve_market_data(self, result: CryptoOrchestrationResult, gecko: CryptoMarketData | None, kraken: CryptoMarketData | None) -> None:
        """Fill market cap, supply and volume; leave gaps as None."""
        if gecko is not None:
            if gecko.market_cap is not None:
                result.market_cap = gecko.market_cap
                result.lineage.market_cap_source = "coingecko"
            if gecko.circulating_supply is not None:
                result.circulating_supply = gecko.circulating_supply
                result.max_supply = gecko.max_supply
                result.lineage.supply_source = "coingecko"
            if gecko.volume_24h is not None:
                result.volume_24h = gecko.volume_24h
                result.lineage.volume_24h_source = "coingecko"

        if result.volume_24h is None and kraken is not None and kraken.volume_24h is not None:
            # One venue in USD, not the all-venue aggregate CoinGecko reports.
            # Never cross-checked against CoinGecko's figure: they do not
            # measure the same thing.
            result.volume_24h = kraken.volume_24h
            result.lineage.volume_24h_source = "kraken:single-venue"

    def _compute_confidence(self, result: CryptoOrchestrationResult) -> float:
        """Score confidence from the price provenance and the remaining gaps."""
        confidence = _PRICE_CONFIDENCE.get(result.lineage.price_source or "", 0.0)
        if confidence == 0.0:
            return 0.0

        if result.price_divergence_pct is not None and result.price_divergence_pct > DIVERGENCE_WARN_PCT:
            confidence -= _DIVERGENCE_PENALTY

        # max_supply is deliberately excluded: None there means uncapped.
        for value in (result.market_cap, result.volume_24h, result.circulating_supply):
            if value is None:
                confidence -= _UNRESOLVED_PENALTY

        return max(0.0, round(confidence, 4))
