"""Fact pack fragments from yfinance.

yfinance is already a core dependency -- it fetches every price in this
project -- so nothing new is taken on here. It is also scraped rather than
contractual, which is why every accessor below degrades to an empty fragment
instead of raising: a shape change must cost one field, never a holding.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import yfinance as yf

from finwiz.analysis.fact_pack.fragment import FactPackFragment
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

_MAX_OFFICERS = 6
_QUOTE_URL = "https://finance.yahoo.com/quote/{ticker}"
_SOURCES = ("yfinance.info",)


def _ticker(symbol: str) -> Any:
    """Network seam. Tests patch this, never yfinance itself."""
    return yf.Ticker(symbol)


def resolve(ticker: str) -> dict[str, Any]:
    """Fetch `info`, or an empty dict if yfinance fails for any reason."""
    try:
        return _ticker(ticker).info or {}
    except Exception as e:
        logger.warning(f"yfinance info lookup failed for {ticker}: {e}")
        return {}


def is_resolvable(info: dict[str, Any]) -> bool:
    """A real instrument always carries a quoteType; an unknown symbol never does."""
    return info.get("quoteType") is not None


def equity_fragment(info: dict[str, Any]) -> FactPackFragment:
    """Extract corporate structure and leadership from equity info."""
    try:
        summary = (info.get("longBusinessSummary") or "").strip() or None

        people: list[str] = []
        for officer in info.get("companyOfficers") or []:
            name = (officer.get("name") or "").strip()
            title = (officer.get("title") or "").strip()
            if name and title:
                people.append(f"{name} ({title})")
            if len(people) >= _MAX_OFFICERS:
                break

        return FactPackFragment(
            corporate_structure=summary,
            leadership="; ".join(people) or None,
            sources=_SOURCES,
        )
    except Exception as e:
        logger.warning(f"equity_fragment extraction failed: {e}")
        return FactPackFragment()


def etf_fragment(ticker: str, info: dict[str, Any]) -> FactPackFragment:
    """For a fund, the issuer IS the corporate structure and the manager IS the leadership.

    Stating that plainly beats asking an LLM to write prose about a CEO the fund
    does not have.
    """
    try:
        issuer = (info.get("fundFamily") or "").strip()
        legal_type = (info.get("legalType") or "").strip()
        long_name = (info.get("longName") or ticker).strip()

        parts = [long_name]
        if legal_type:
            parts.append(legal_type)
        if issuer:
            parts.append(f"issued by {issuer}")
        inception = info.get("fundInceptionDate")
        if isinstance(inception, int | float):
            parts.append(f"inception {datetime.fromtimestamp(inception, tz=UTC).year}")

        return FactPackFragment(
            corporate_structure=", ".join(parts) + ".",
            leadership=issuer or None,
            citations=(_QUOTE_URL.format(ticker=ticker),),
            sources=_SOURCES,
        )
    except Exception as e:
        logger.warning(f"etf_fragment extraction failed for {ticker}: {e}")
        return FactPackFragment()


def crypto_fragment(info: dict[str, Any]) -> FactPackFragment:
    """Crypto has no issuer and no officers; say nothing rather than invent one.

    Both fields stay None so the composer writes the placeholder and confidence
    scores this holding as the thin pack it genuinely is.
    """
    try:
        return FactPackFragment(sources=_SOURCES) if is_resolvable(info) else FactPackFragment()
    except Exception as e:
        logger.warning(f"crypto_fragment extraction failed: {e}")
        return FactPackFragment()
