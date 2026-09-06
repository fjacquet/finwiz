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


_EVENT_MAX_CHARS = 200
_EVENT_WINDOW_DAYS = 365
_MAX_EVENTS = 10

# Filing types that describe something material. CORRESP, S-8, 25-NSE and the
# rest are administrative traffic and would crowd out the events that matter.
_MATERIAL_FILING_TYPES = frozenset({"8-K", "8-K/A", "10-K", "10-Q", "20-F", "6-K", "6-K/A", "DEF 14A", "SC 13D", "SC 13G"})

# Wire services and regulatory-filing distributors only. Yahoo's feed also
# carries opinion sites whose headlines are predictions, not events; per the
# project rule those are excluded outright rather than emitted at low grade.
_NEWS_PROVIDER_ALLOWLIST = frozenset(
    {
        "Reuters",
        "Bloomberg",
        "Associated Press",
        "AP Finance",
        "Financial Times",
        "Business Wire",
        "PR Newswire",
        "GlobeNewswire",
        "Dow Jones Newswires",
        "The Wall Street Journal",
    },
)


def _within_window(when: datetime, now: datetime) -> bool:
    return 0 <= (now - when).days <= _EVENT_WINDOW_DAYS


def _extract_news_event(item: Any, now: datetime) -> tuple[str | None, str | None]:
    """Extract a news event and URL from a raw item, or return (None, None)."""
    if not isinstance(item, dict):
        return None, None
    content = item.get("content") or {}
    provider = ((content.get("provider") or {}).get("displayName") or "").strip()
    if provider not in _NEWS_PROVIDER_ALLOWLIST:
        return None, None
    raw_date = (content.get("pubDate") or "").replace("Z", "+00:00")
    try:
        published = datetime.fromisoformat(raw_date)
    except (ValueError, TypeError):
        return None, None
    if not _within_window(published, now):
        return None, None
    title = (content.get("title") or "").strip()
    if not title:
        return None, None
    event = f"{published.date().isoformat()} {title}"[:_EVENT_MAX_CHARS]
    url = (content.get("canonicalUrl") or {}).get("url")
    return event, url


def filing_events(ticker: str, now: datetime | None = None) -> FactPackFragment:
    """Material SEC filings in the last 12 months, with EDGAR links.

    This is the strongest evidence available for `recent_events`: dated, filed,
    and citable. It covers US listings and foreign issuers with ADRs (ASML files
    20-F / 6-K); a European-only listing returns nothing and falls back to news.
    """
    now = now or datetime.now(UTC)
    try:
        filings = _ticker(ticker).sec_filings or []
        events: list[str] = []
        citations: list[str] = []
        for filing in filings:
            if not isinstance(filing, dict):
                continue
            if filing.get("type") not in _MATERIAL_FILING_TYPES:
                continue
            raw_date = filing.get("date") or ""
            try:
                filed = datetime.strptime(raw_date, "%Y-%m-%d").replace(tzinfo=UTC)
            except (ValueError, TypeError):
                continue
            if not _within_window(filed, now):
                continue
            title = (filing.get("title") or "").strip()
            events.append(f"{raw_date} {filing['type']}: {title}"[:_EVENT_MAX_CHARS])
            url = filing.get("edgarUrl")
            if url:
                citations.append(url)
            if len(events) >= _MAX_EVENTS:
                break

        if not events:
            return FactPackFragment()
        return FactPackFragment(
            recent_events=tuple(events),
            citations=tuple(citations),
            sources=("yfinance.sec_filings",),
            events_from_filings=True,
        )
    except Exception as e:
        logger.debug(f"sec_filings processing failed for {ticker}: {e}")
        return FactPackFragment()


def news_events(ticker: str, now: datetime | None = None) -> FactPackFragment:
    """Wire-service headlines in the last 12 months. Weaker than filings, still cited."""
    now = now or datetime.now(UTC)
    try:
        items = _ticker(ticker).news or []
        events: list[str] = []
        citations: list[str] = []
        for item in items:
            if len(events) >= _MAX_EVENTS:
                break
            event, url = _extract_news_event(item, now)
            if event:
                events.append(event)
                if url:
                    citations.append(url)

        if not events:
            return FactPackFragment()
        return FactPackFragment(recent_events=tuple(events), citations=tuple(citations), sources=("yfinance.news",))
    except Exception as e:
        logger.debug(f"news processing failed for {ticker}: {e}")
        return FactPackFragment()
