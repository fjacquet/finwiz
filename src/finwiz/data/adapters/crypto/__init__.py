"""Crypto market-data adapters.

Separate from the equity adapters in the parent package: `BaseDataAdapter`
imposes `FundamentalData`, which is hardwired to four equity metrics with
equity validation bounds and has no place to put market cap, volume or supply.
"""

from finwiz.data.adapters.crypto.base import (
    BaseCryptoAdapter,
    CryptoMarketData,
    normalize_crypto_symbol,
    positive_or_none,
)
from finwiz.data.adapters.crypto.coingecko_adapter import CoinGeckoAdapter
from finwiz.data.adapters.crypto.kraken_adapter import KrakenAdapter

__all__ = [
    "BaseCryptoAdapter",
    "CoinGeckoAdapter",
    "CryptoMarketData",
    "KrakenAdapter",
    "normalize_crypto_symbol",
    "positive_or_none",
]
