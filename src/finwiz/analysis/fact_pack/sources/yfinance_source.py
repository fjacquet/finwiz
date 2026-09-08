"""Fact pack fragments from yfinance.

yfinance is already a core dependency -- it fetches every price in this
project -- so nothing new is taken on here. It is also scraped rather than
contractual, which is why every accessor below degrades to an empty fragment
instead of raising: a shape change must cost one field, never a holding.
"""

from __future__ import annotations

import re
from datetime import UTC, date, datetime
from typing import Any

import yfinance as yf

from finwiz.analysis.fact_pack.fragment import FactPackFragment
from finwiz.analysis.fact_pack.sources._text import _safe_str
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

_MAX_OFFICERS = 6
_SOURCES = ("yfinance.info",)

# Legal-form suffixes stripped before matching a company name against a headline.
# "Mercedes-Benz Group AG" must match a headline saying "Mercedes-Benz"; leaving
# the suffix on would require the wire to spell the legal entity, which it never does.
_LEGAL_SUFFIXES = frozenset(
    {
        "ag",
        "sa",
        "sas",
        "nv",
        "bv",
        "plc",
        "inc",
        "inc.",
        "corp",
        "corp.",
        "co",
        "co.",
        "ltd",
        "ltd.",
        "llc",
        "spa",
        "se",
        "oyj",
        "ab",
        "as",
        "asa",
        "holding",
        "holdings",
        "group",
        "the",
        "company",
    }
)

# A token shorter than this is too generic to establish that a headline is about
# the holding -- "EL" (EssilorLuxottica) matches "EL NINO", and a two-letter root
# matches something in almost any sentence. Such a holding can still qualify
# through the keyword arm; it just cannot qualify on its name alone.
_MIN_NAME_TOKEN_CHARS = 4
_MIN_TICKER_ROOT_CHARS = 3

# Words that make a headline a corporate event regardless of whether it names the
# company: a wire writing "Q3 profit beats estimates" under a ticker is reporting on
# that ticker. Deliberately narrow -- every entry here is a hole through which
# syndicated noise can pass, so only unambiguous corporate-finance vocabulary
# qualifies. Anything arguable (an "outlook", a "report", a "deal") is left out.
_CORPORATE_EVENT_KEYWORDS = frozenset(
    {
        "earnings",
        "revenue",
        "profit",
        "profits",
        "loss",
        "losses",
        "dividend",
        "buyback",
        "guidance",
        "forecast",
        "merger",
        "acquisition",
        "acquires",
        "acquire",
        "takeover",
        "divest",
        "divests",
        "spinoff",
        "ipo",
        "bankruptcy",
        "restructuring",
        "layoffs",
        "recall",
        "lawsuit",
        "settlement",
        "probe",
        "downgrade",
        "downgrades",
        "upgrade",
        "upgrades",
        "ceo",
        "cfo",
        "chairman",
        "quarterly",
        "shareholders",
        "shares",
        "stake",
    }
)


def _name_tokens(company_name: str) -> set[str]:
    """Distinctive lowercase tokens of a company name, legal forms removed."""
    raw = "".join(ch if ch.isalnum() or ch in "-&" else " " for ch in company_name.lower())
    return {tok for tok in raw.split() if len(tok) >= _MIN_NAME_TOKEN_CHARS and tok not in _LEGAL_SUFFIXES}


def _ticker_root(symbol: str) -> str:
    """The symbol without its exchange or quote suffix: MCHA.F -> MCHA, BTC-USD -> BTC."""
    return symbol.split(".")[0].split("-")[0].strip().lower()


def _is_relevant_headline(title: str, ticker: str, company_name: str) -> bool:
    """Is this headline plausibly about the holding, rather than syndicated noise?

    Yahoo's ticker stream is loosely associated: a live run surfaced
    "2026-08-09 This City May Be the South's Most Underrated Getaway" as MCHA.F's
    only recent_event, which then reached the qualitative prompt inside the block
    it labels AUTORITAIRE. The provider allowlist screens *who published*, never
    *what about* -- a reputable wire syndicates travel copy under a ticker just as
    readily. See #169.

    Two independent ways to qualify, because either alone is wrong:

    - The headline names the holding (ticker root or a distinctive name token).
      Catches company-specific news whatever it is about.
    - The headline carries unambiguous corporate-event vocabulary. Catches the
      wire style that omits the name it is already filed under -- "Q3 profit beats
      estimates" -- which a name-only gate would discard.

    Neither is sufficient alone: name-only drops real events, keyword-only lets
    through any syndicated piece that happens to use a financial word. Requiring
    both would be stricter than the evidence justifies.
    """
    haystack = title.lower()

    # Match at a word start, not anywhere: a bare substring test let "el"
    # (EssilorLuxottica) match "EL NINO", and would equally match "shell" or
    # "held". Prefix-at-word-start still catches the common case where a wire
    # writes the name and the ticker is its stem -- AIR.PA against "Airbus".
    root = _ticker_root(ticker)
    candidates = _name_tokens(company_name)
    if len(root) >= _MIN_TICKER_ROOT_CHARS:
        candidates = candidates | {root}
    if any(re.search(rf"\b{re.escape(token)}", haystack) for token in candidates):
        return True

    words = {"".join(ch for ch in w if ch.isalnum()) for w in haystack.split()}
    return bool(words & _CORPORATE_EVENT_KEYWORDS)


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


def equity_fragment(ticker: str, info: dict[str, Any]) -> FactPackFragment:
    """Extract corporate structure and leadership from equity info."""
    try:
        summary = _safe_str(info.get("longBusinessSummary")) or None

        people: list[str] = []
        for officer in info.get("companyOfficers") or []:
            name = _safe_str(officer.get("name"))
            title = _safe_str(officer.get("title"))
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
        logger.warning(f"equity_fragment extraction failed for {ticker}: {e}")
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


def _parse_filing_date(raw_date: Any) -> tuple[datetime, str] | tuple[None, None]:
    """Parse a filing date that may be a date object, datetime, or string.

    Returns (datetime with UTC tz, ISO date string) or (None, None) on failure.
    """
    if isinstance(raw_date, datetime):
        # Already a datetime; ensure it has UTC tz if naive
        dt = raw_date if raw_date.tzinfo else raw_date.replace(tzinfo=UTC)
        return dt, dt.date().isoformat()
    if isinstance(raw_date, date):
        # A date object; convert to datetime at UTC
        dt = datetime.combine(raw_date, datetime.min.time()).replace(tzinfo=UTC)
        return dt, raw_date.isoformat()
    if isinstance(raw_date, str):
        # A string; parse it
        try:
            dt = datetime.strptime(raw_date, "%Y-%m-%d").replace(tzinfo=UTC)
            return dt, raw_date
        except ValueError:
            return None, None
    return None, None


def _extract_filing_event(filing: Any, now: datetime) -> tuple[str | None, str | None]:
    """Extract a filing event and URL from a raw filing, or return (None, None)."""
    if not isinstance(filing, dict):
        return None, None
    if filing.get("type") not in _MATERIAL_FILING_TYPES:
        return None, None
    raw_date = filing.get("date")
    if raw_date is None:
        return None, None
    filed, date_str = _parse_filing_date(raw_date)
    if filed is None:
        return None, None
    if not _within_window(filed, now):
        return None, None
    title = _safe_str(filing.get("title"))
    event = f"{date_str} {filing['type']}: {title}"[:_EVENT_MAX_CHARS]
    url = filing.get("edgarUrl")
    return event, url


def _extract_news_event(item: Any, now: datetime, ticker: str = "", company_name: str = "") -> tuple[str | None, str | None]:
    """Extract a news event and URL from a raw item, or return (None, None).

    Screens relevance as well as provider: see _is_relevant_headline. The ticker
    and company_name default to empty so an unrelated caller still gets the old
    provider/date/title behaviour, but the live path always passes both.
    """
    if not isinstance(item, dict):
        return None, None
    content = item.get("content") or {}
    provider = _safe_str((content.get("provider") or {}).get("displayName"))
    if provider not in _NEWS_PROVIDER_ALLOWLIST:
        return None, None
    raw_date = _safe_str(content.get("pubDate")).replace("Z", "+00:00")
    try:
        published = datetime.fromisoformat(raw_date)
    except (ValueError, TypeError):
        return None, None
    if not _within_window(published, now):
        return None, None
    title = _safe_str(content.get("title"))
    if not title:
        return None, None
    if (ticker or company_name) and not _is_relevant_headline(title, ticker, company_name):
        logger.debug(f"fact_pack: {ticker} dropped an off-topic headline: {title!r}")
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
            if len(events) >= _MAX_EVENTS:
                break
            # One malformed filing (e.g. a bare string instead of a dict --
            # _extract_filing_event's own isinstance check doesn't help if
            # the AttributeError happens before it) must cost that filing,
            # not the whole batch: without this, it used to escape to the
            # outer handler below and discard every good filing and
            # citation gathered so far, logged at debug where nobody saw it.
            try:
                event, url = _extract_filing_event(filing, now)
            except Exception as e:
                logger.warning(f"fact_pack: {ticker} skipped a malformed SEC filing: {e}")
                continue
            if event:
                events.append(event)
                if url:
                    citations.append(url)

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


def news_events(ticker: str, company_name: str = "", now: datetime | None = None) -> FactPackFragment:
    """Wire-service headlines in the last 12 months. Weaker than filings, still cited.

    Headlines are screened for relevance to the holding, not merely for a
    reputable provider -- Yahoo's ticker stream syndicates unrelated copy under a
    symbol, and a thin pack is exactly where one bogus "fact" carries most weight.
    """
    now = now or datetime.now(UTC)
    try:
        items = _ticker(ticker).news or []
        events: list[str] = []
        citations: list[str] = []
        for item in items:
            if len(events) >= _MAX_EVENTS:
                break
            # Same containment as filing_events above: one malformed item
            # must cost that item, not every good headline and citation
            # gathered before it.
            try:
                event, url = _extract_news_event(item, now, ticker, company_name)
            except Exception as e:
                logger.warning(f"fact_pack: {ticker} skipped a malformed news item: {e}")
                continue
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
