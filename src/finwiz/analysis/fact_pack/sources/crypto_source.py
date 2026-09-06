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


def _number(value: Any) -> float | None:
    """Floats only. A string where a number belongs is a missing field, not a crash."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value)


def _year(value: Any) -> int | None:
    epoch = _number(value)
    if epoch is None:
        return None
    try:
        return datetime.fromtimestamp(epoch, tz=UTC).year
    except (OSError, OverflowError, ValueError):
        return None


def crypto_facts(query_symbol: str, info: dict[str, Any]) -> tuple[CryptoFacts | None, tuple[str, ...]]:
    """Build crypto facts, or ``None`` when there is no description to anchor them."""
    description = (info.get("description") or "").strip()
    if not description:
        logger.warning(f"fact_pack: {query_symbol} has no description; cannot build crypto facts")
        return None, ()

    raw_max = _number(info.get("maxSupply"))
    # 0 is yfinance's encoding for "no maximum", not a cap of zero coins.
    capped = raw_max is not None and raw_max > 0
    facts = CryptoFacts(
        description=description[:_DESCRIPTION_MAX_CHARS],
        launched_year=_year(info.get("startDate")),
        circulating_supply=_number(info.get("circulatingSupply")),
        max_supply=raw_max if capped else None,
        supply_is_capped=capped,
        market_cap=_number(info.get("marketCap")),
        volume_24h_market_cap_pct=_number(info.get("volume24HrMarketCapPercent")),
    )

    link = str(info.get("coinMarketCapLink") or "")
    citations = (link,) if link.startswith(("http://", "https://")) else ()
    return facts, citations
