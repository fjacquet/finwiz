"""Ticker normalization helpers for discovery scanners.

Domain-model tickers are kept bare (``BTC``, ``AAVE``) so report UIs and
``NewcomerCandidate.ticker`` stay consistent with the rest of the product.
The ``-USD`` suffix for crypto is applied only at the yfinance query boundary.
"""

from __future__ import annotations

from finwiz.discovery.ticker_hygiene import canonical_symbol

_CRYPTO_QUOTE_SUFFIXES: tuple[str, ...] = ("-USD", "-USDT", "-USDC")


def to_yfinance_symbol(ticker: str, asset_class: str) -> str:
    """Return the yfinance-query form of *ticker*.

    Applies known renames (e.g. ``MATIC`` → ``POL``) so migrated symbols don't
    hit yfinance under their delisted old name. Crypto tickers then receive a
    ``-USD`` suffix; stock/ETF tickers pass through. Idempotent: an already-
    suffixed crypto ticker (e.g. ``BTC-USD``) is returned unchanged.
    """
    symbol = ticker.strip().upper()
    for suffix in _CRYPTO_QUOTE_SUFFIXES:
        if symbol.endswith(suffix):
            # Already suffixed: rename the base part if needed, keep the suffix.
            base = canonical_symbol(symbol[: -len(suffix)])
            return f"{base}{suffix}"
    symbol = canonical_symbol(symbol)
    if asset_class != "crypto":
        return symbol
    return f"{symbol}-USD"
