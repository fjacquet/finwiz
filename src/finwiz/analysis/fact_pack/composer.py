"""Route by declared asset class, merge fragments, build the FactPack."""

from __future__ import annotations

from datetime import UTC, datetime

from finwiz.analysis.fact_pack.fragment import PLACEHOLDER, FactPackFragment, derive_confidence, merge_fragments
from finwiz.analysis.fact_pack.sources import yfinance_source
from finwiz.schemas.hybrid_analysis.fact_pack import FactPack
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

# quoteType values that corroborate a declared asset class. A mismatch does not
# change routing -- the declared value is authoritative -- it only warns. This
# repo once classified 33 European tickers as crypto from symbol length alone
# and nothing said a word; this is the cheap detector for that class of bug.
_EXPECTED_QUOTE_TYPES: dict[str, frozenset[str]] = {
    "stock": frozenset({"EQUITY"}),
    "etf": frozenset({"ETF", "MUTUALFUND"}),
    "crypto": frozenset({"CRYPTOCURRENCY"}),
}


def _gap_fill(ticker: str, company_name: str, sector: str | None, industry: str | None, missing: tuple[str, ...]) -> FactPackFragment:
    """Hook for the Perplexity gap-fill. Wired in Task 5; inert until then."""
    return FactPackFragment()


def _identity_fragment(ticker: str, asset_class: str, info: dict) -> FactPackFragment:
    if asset_class == "etf":
        return yfinance_source.etf_fragment(ticker, info)
    if asset_class == "crypto":
        return yfinance_source.crypto_fragment(ticker, info)
    return yfinance_source.equity_fragment(ticker, info)


def _missing_fields(fragment: FactPackFragment) -> tuple[str, ...]:
    missing: list[str] = []
    if not fragment.corporate_structure:
        missing.append("corporate_structure")
    if not fragment.leadership:
        missing.append("leadership")
    if not fragment.recent_events:
        missing.append("recent_events")
    return tuple(missing)


def compose_fact_pack(ticker: str, company_name: str, sector: str | None, industry: str | None, asset_class: str) -> FactPack | None:
    """Build a pack from free structured sources.

    Returns None ONLY when the ticker resolves to nothing. Every other outcome is
    a pack, however thin -- one provider must never be able to halt a holding,
    which is exactly what happened on 2026-09-06 when a quota error took all 64.
    """
    info = yfinance_source.resolve(ticker)
    if not yfinance_source.is_resolvable(info):
        logger.warning(f"fact_pack: {ticker} resolves to nothing (no quoteType); cannot build a pack")
        return None

    quote_type = info.get("quoteType")
    expected = _EXPECTED_QUOTE_TYPES.get(asset_class)
    if expected is not None and quote_type not in expected:
        logger.warning(f"fact_pack: {ticker} declared asset_class={asset_class!r} but yfinance reports quoteType={quote_type!r}; routing follows the declared value")

    # Fixed precedence per asset class: identity first, then filings, then news.
    # Filings outrank news because merge takes the first non-empty events tuple.
    fragment = merge_fragments(
        _identity_fragment(ticker, asset_class, info),
        yfinance_source.filing_events(ticker),
        yfinance_source.news_events(ticker),
    )

    missing = _missing_fields(fragment)
    if missing:
        fragment = merge_fragments(fragment, _gap_fill(ticker, company_name, sector, industry, missing))

    fetched_at = datetime.now(UTC)
    return FactPack(
        corporate_structure=fragment.corporate_structure or PLACEHOLDER,
        recent_events=list(fragment.recent_events),
        leadership=fragment.leadership or PLACEHOLDER,
        fetched_at=fetched_at,
        freshness=FactPack.derive_freshness(fetched_at),
        confidence=derive_confidence(fragment),
        source_citations=list(fragment.citations),
        sources_used=list(fragment.sources),
    )
