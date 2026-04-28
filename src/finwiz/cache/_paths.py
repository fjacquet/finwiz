"""Shared path-safety helpers for cache modules.

Both `AnalysisCacheManager` and `FactPackCache` build on-disk paths from
caller-supplied tickers (and, for analysis cache, asset_class). These
helpers enforce a defense-in-depth path-traversal guard at the cache layer
even when the caller already validates upstream (Pydantic schemas).
"""

from __future__ import annotations

import re

# Yahoo / Kraken ticker alphabet — uppercase alnum plus `.` (BRK.B), `-`
# (BTC-USD), `:` (exchange:symbol), `^` (^GSPC), `=` (futures). Same regex
# as `HoldingDecision._TICKER_RE` in `schemas/portfolio_review.py`.
_TICKER_RE = re.compile(r"^[A-Z0-9:.\-^=]{1,15}$")
# Asset-class alphabet — lowercase alnum + underscore. Covers
# stock / etf / crypto / fact_pack and any future literal that fits.
_ASSET_CLASS_RE = re.compile(r"^[a-z0-9_]{1,20}$")


def safe_ticker(ticker: str) -> str:
    """Upper-case the ticker and reject anything outside the Yahoo / Kraken alphabet.

    Also explicitly rejects the `..` substring — `.` is in the alphabet (BRK.B
    is legitimate) but `..` is a path-traversal token.
    """
    upper = ticker.upper()
    if not _TICKER_RE.match(upper):
        raise ValueError(f"invalid ticker {ticker!r}: must match {_TICKER_RE.pattern}")
    if ".." in upper:
        raise ValueError(f"invalid ticker {ticker!r}: contains path-traversal sequence '..'")
    return upper


def safe_asset_class(asset_class: str) -> str:
    """Lower-case asset_class and restrict to `[a-z0-9_]{1,20}`."""
    lower = asset_class.lower()
    if not _ASSET_CLASS_RE.match(lower):
        raise ValueError(f"invalid asset_class {asset_class!r}: must match {_ASSET_CLASS_RE.pattern}")
    return lower
