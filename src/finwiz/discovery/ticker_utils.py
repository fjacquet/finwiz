"""Ticker normalization helpers for discovery scanners.

Domain-model tickers are kept bare (``BTC``, ``AAVE``) so report UIs and
``NewcomerCandidate.ticker`` stay consistent with the rest of the product.
The ``-USD`` suffix for crypto is applied only at the yfinance query boundary.
"""

from __future__ import annotations

_CRYPTO_QUOTE_SUFFIXES: tuple[str, ...] = ("-USD", "-USDT", "-USDC")


def to_yfinance_symbol(ticker: str, asset_class: str) -> str:
    """Return the yfinance-query form of *ticker*.

    Crypto tickers receive a ``-USD`` suffix; stock/ETF tickers pass through.
    Idempotent: an already-suffixed crypto ticker (e.g. ``BTC-USD``) is
    returned unchanged.
    """
    symbol = ticker.strip().upper()
    if asset_class != "crypto":
        return symbol
    if symbol.endswith(_CRYPTO_QUOTE_SUFFIXES):
        return symbol
    return f"{symbol}-USD"
