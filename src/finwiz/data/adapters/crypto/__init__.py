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
from finwiz.data.adapters.crypto.genesis import CRYPTO_GENESIS_YEAR, crypto_age_years
from finwiz.data.adapters.crypto.kraken_adapter import KrakenAdapter

__all__ = [
    "BaseCryptoAdapter",
    "CoinGeckoAdapter",
    "CRYPTO_GENESIS_YEAR",
    "CryptoMarketData",
    "KrakenAdapter",
    "crypto_age_years",
    "normalize_crypto_symbol",
    "positive_or_none",
]
