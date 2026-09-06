"""Crypto facts from yfinance's `info`.

A protocol has no issuer and no officers, so none are asked for. What it does
have is a supply policy, and the distinction between "capped at 21 million",
"uncapped" and "we do not know" is the whole point of this module: yfinance
encodes the middle case as `maxSupply == 0`, which a naive reader would record
as a cap of zero.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from finwiz.schemas.hybrid_analysis.fact_pack import CryptoFacts
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

_DESCRIPTION_MAX_CHARS = 2000


def _number(value: Any, field_name: str = "") -> float | None:
    """Coerce to float. A wrong type or out-of-domain value is a missing field, not a crash.

    A string where a number belongs, or a negative number where only non-negatives belong,
    is treated as unknown. Logs mismatches at debug level with field name and value.
    """
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    fval = float(value)
    if fval < 0:
        if field_name:
            logger.debug(f"fact_pack: {field_name} is negative ({fval}); treating as unknown")
        return None
    return fval


def _year(value: Any) -> int | None:
    """Convert Unix timestamp to year, returning None if out of bounds or malformed.

    Valid range is 1900-2200 (schema constraint on launched_year).
    """
    epoch = _number(value, field_name="startDate")
    if epoch is None:
        return None
    try:
        year = datetime.fromtimestamp(epoch, tz=UTC).year
        if not (1900 <= year <= 2200):
            logger.debug(f"fact_pack: startDate yields year {year}; out of bounds [1900, 2200]")
            return None
        return year
    except (OSError, OverflowError, ValueError):
        return None


def crypto_facts(query_symbol: str, info: dict[str, Any]) -> tuple[CryptoFacts | None, tuple[str, ...]]:
    """Build crypto facts, or ``None`` when there is no description to anchor them."""
    # Read description defensively — if not a string, treat as absent.
    raw_desc = info.get("description")
    if not isinstance(raw_desc, str):
        logger.warning(f"fact_pack: {query_symbol} description is not a string; cannot build crypto facts")
        return None, ()
    description = raw_desc.strip()
    if not description:
        logger.warning(f"fact_pack: {query_symbol} has no description; cannot build crypto facts")
        return None, ()

    raw_max = _number(info.get("maxSupply"))
    # 0 is yfinance's encoding for "no maximum", not a cap of zero coins.
    capped = raw_max is not None and raw_max > 0
    try:
        facts = CryptoFacts(
            description=description[:_DESCRIPTION_MAX_CHARS],
            launched_year=_year(info.get("startDate")),
            circulating_supply=_number(info.get("circulatingSupply"), field_name="circulatingSupply"),
            max_supply=raw_max if capped else None,
            supply_is_capped=capped,
            market_cap=_number(info.get("marketCap"), field_name="marketCap"),
            volume_24h_market_cap_pct=_number(info.get("volume24HrMarketCapPercent"), field_name="volume24HrMarketCapPercent"),
        )
    except Exception as e:
        logger.error(f"fact_pack: {query_symbol} construction failed: {type(e).__name__}: {e}")
        return None, ()

    link = str(info.get("coinMarketCapLink") or "")
    citations = (link,) if link.startswith(("http://", "https://")) else ()
    return facts, citations
