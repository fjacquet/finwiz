"""Live FX rate provider (yfinance), EUR-based, with a per-run cache.

Best-effort: any failure yields `None` and the caller treats the affected
weight as unknown. Pure deterministic glue around a network call (AI Minimalism).
"""

from __future__ import annotations

import logging

import yfinance as yf  # yfinance has no official type stubs

logger = logging.getLogger(__name__)

# Sub-unit (minor) currency codes -> (major ISO code, divisor).
# e.g. LSE quotes "GBp" (pence); 100 pence = 1 GBP.
_MINOR_UNITS: dict[str, tuple[str, float]] = {
    "GBp": ("GBP", 100.0),
    "GBX": ("GBP", 100.0),
    "ZAc": ("ZAR", 100.0),
    "ILA": ("ILS", 100.0),
}

# Per-run cache keyed by (from_ccy, base) -> rate or None. Reset via clear_fx_cache().
# Not thread-safe by design — the flow runs in a single asyncio thread. Cache keys use
# the raw (stripped) from_ccy so the case-sensitive minor-unit codes (e.g. "GBp") survive;
# yfinance returns ISO-cased currencies, so case-variant keys don't occur in practice.
_FX_CACHE: dict[tuple[str, str], float | None] = {}


def clear_fx_cache() -> None:
    """Clear the per-run FX cache (used by tests and between flow runs)."""
    _FX_CACHE.clear()


def _fetch_pair_rate(from_ccy: str, base: str) -> float | None:
    """Fetch the spot rate for `<from_ccy><base>=X` from yfinance. Network site."""
    pair = f"{from_ccy}{base}=X"
    try:
        ticker = yf.Ticker(pair)
        # Primary: fast_info last price.
        try:
            rate = ticker.fast_info["lastPrice"]
        except Exception:
            rate = getattr(ticker.fast_info, "last_price", None)
        if rate and float(rate) > 0:
            return float(rate)

        # Fallback: 1-day history close.
        hist = ticker.history(period="1d")
        if not hist.empty and "Close" in hist.columns:
            close = float(hist["Close"].iloc[-1])
            if close > 0:
                return close
    except Exception as exc:  # best-effort
        logger.warning("FX lookup failed for %s: %s", pair, exc)
    return None


def get_fx_rate(from_ccy: str, base: str = "EUR") -> float | None:
    """Return the rate to multiply a `from_ccy` amount by to get `base`.

    Identity (1.0) when currencies match. Minor units (GBp/GBX/ZAc/ILA) are
    mapped to their major unit and the rate divided by 100. Best-effort: any
    failure returns None. Results (including None) are cached per run.
    """
    raw = (from_ccy or "").strip()
    base_ccy = (base or "EUR").strip().upper()
    if not raw or not base_ccy:
        return None

    cache_key = (raw, base_ccy)
    if cache_key in _FX_CACHE:
        return _FX_CACHE[cache_key]

    major, divisor = _MINOR_UNITS.get(raw, (raw.upper(), 1.0))

    if major == base_ccy:
        result: float | None = 1.0 / divisor
    else:
        pair_rate = _fetch_pair_rate(major, base_ccy)
        result = None if pair_rate is None else pair_rate / divisor

    _FX_CACHE[cache_key] = result
    return result
