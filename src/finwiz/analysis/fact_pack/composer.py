"""Route by declared asset class, merge fragments, build the FactPack."""

from __future__ import annotations

from datetime import UTC, datetime

from finwiz.analysis.fact_pack.fragment import PLACEHOLDER, FactPackFragment, derive_confidence, merge_fragments
from finwiz.analysis.fact_pack.sources import yfinance_source
from finwiz.discovery.ticker_utils import to_yfinance_symbol
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

# Mirrors FactPack's own Field(max_length=...) caps (schemas/hybrid_analysis/fact_pack.py).
# Deliberately duplicated here rather than imported from fact_pack_research.py --
# this package carries no dependency on the LLM path. A live-portfolio measurement
# on 2026-09-06 found 19 of 36 stock summaries within 200 chars of the 2000-char
# cap and one (NTNX, 2212 chars) already over it -- yfinance's longBusinessSummary
# is unbounded prose, and FactPack's Field constraints raise ValidationError on
# the first holding that crosses them. Clamping here keeps the composer's own
# promise: every non-None outcome is a valid FactPack, however thin.
_CORPORATE_STRUCTURE_MAX_CHARS = 2000
_LEADERSHIP_MAX_CHARS = 1000
_MAX_CITATIONS = 20

# Marks a pack the try/except backstop below built, not a legitimately thin one.
# Packs are cached to disk and read back weeks later; by then the ERROR log line
# that flagged the original failure is long gone, and a fallback pack is
# byte-identical in content to a holding that genuinely has no facts available.
_SCHEMA_FALLBACK_SOURCE = "composer.schema_fallback"


def _gap_fill(ticker: str, company_name: str, sector: str | None, industry: str | None, missing: tuple[str, ...]) -> FactPackFragment:
    """Hook for the Perplexity gap-fill. Wired in Task 5; inert until then."""
    return FactPackFragment()


def _describe(ticker: str, query_symbol: str) -> str:
    """Holding identity for log lines, with the query form when it differs.

    `BTC` alone is ambiguous about what was actually fetched -- yfinance's
    `BTC` is a Grayscale trust ETF, not the coin -- so a log line names both
    once they diverge.
    """
    return ticker if ticker == query_symbol else f"{ticker} (query={query_symbol})"


def _identity_fragment(query_symbol: str, asset_class: str, info: dict) -> FactPackFragment:
    if asset_class == "etf":
        return yfinance_source.etf_fragment(query_symbol, info)
    if asset_class == "crypto":
        return yfinance_source.crypto_fragment(query_symbol, info)
    return yfinance_source.equity_fragment(query_symbol, info)


def _missing_fields(fragment: FactPackFragment) -> tuple[str, ...]:
    missing: list[str] = []
    if not fragment.corporate_structure:
        missing.append("corporate_structure")
    if not fragment.leadership:
        missing.append("leadership")
    if not fragment.recent_events:
        missing.append("recent_events")
    return tuple(missing)


def _clamp_text(ticker: str, field: str, value: str, max_chars: int) -> str:
    """Truncate to the schema's own cap rather than let FactPack raise on it."""
    if len(value) <= max_chars:
        return value
    logger.warning(f"fact_pack: {ticker} {field} truncated from {len(value)} to {max_chars} chars")
    return value[:max_chars].rstrip()


def _clamp_citations(ticker: str, citations: tuple[str, ...]) -> list[str]:
    """Cap accumulated citations to the schema's max_length.

    merge_fragments accumulates citations across every source rather than
    first-non-empty-wins, so an ETF (identity quote page + up to 10 filing URLs
    + up to 10 news URLs) can exceed FactPack's 20-URL cap by one.
    """
    if len(citations) <= _MAX_CITATIONS:
        return list(citations)
    logger.warning(f"fact_pack: {ticker} source_citations truncated from {len(citations)} to {_MAX_CITATIONS}")
    return list(citations[:_MAX_CITATIONS])


def compose_fact_pack(ticker: str, company_name: str, sector: str | None, industry: str | None, asset_class: str) -> FactPack | None:
    """Build a pack from free structured sources.

    Returns None ONLY when the ticker resolves to nothing. Every other outcome is
    a pack, however thin -- one provider must never be able to halt a holding,
    which is exactly what happened on 2026-09-06 when a quota error took all 64.
    """
    # Domain-model tickers stay bare (BTC, AAVE); yfinance needs the query form
    # (BTC-USD). Without this, yfinance's own `BTC` resolves to a Grayscale
    # trust ETF, not the coin -- silently fetching facts about the wrong
    # instrument rather than failing loudly. Derived once and threaded through
    # every yfinance call below, including the ETF citation URL.
    query_symbol = to_yfinance_symbol(ticker, asset_class)
    identity = _describe(ticker, query_symbol)

    info = yfinance_source.resolve(query_symbol)
    if not yfinance_source.is_resolvable(info):
        logger.warning(f"fact_pack: {identity} resolves to nothing (no quoteType); cannot build a pack")
        return None

    quote_type = info.get("quoteType")
    expected = _EXPECTED_QUOTE_TYPES.get(asset_class)
    if expected is not None and quote_type not in expected:
        logger.warning(f"fact_pack: {identity} declared asset_class={asset_class!r} but yfinance reports quoteType={quote_type!r}; routing follows the declared value")

    # Fixed precedence per asset class: identity first, then filings, then news.
    # Filings outrank news because merge takes the first non-empty events tuple.
    fragment = merge_fragments(
        _identity_fragment(query_symbol, asset_class, info),
        yfinance_source.filing_events(query_symbol),
        yfinance_source.news_events(query_symbol),
    )

    missing = _missing_fields(fragment)
    if missing:
        fragment = merge_fragments(fragment, _gap_fill(ticker, company_name, sector, industry, missing))

    fetched_at = datetime.now(UTC)
    freshness = FactPack.derive_freshness(fetched_at)
    corporate_structure = _clamp_text(identity, "corporate_structure", fragment.corporate_structure or PLACEHOLDER, _CORPORATE_STRUCTURE_MAX_CHARS)
    leadership = _clamp_text(identity, "leadership", fragment.leadership or PLACEHOLDER, _LEADERSHIP_MAX_CHARS)
    source_citations = _clamp_citations(identity, fragment.citations)

    try:
        return FactPack(
            corporate_structure=corporate_structure,
            recent_events=list(fragment.recent_events),
            leadership=leadership,
            fetched_at=fetched_at,
            freshness=freshness,
            confidence=derive_confidence(fragment),
            source_citations=source_citations,
            sources_used=list(fragment.sources),
        )
    except Exception as e:
        # Layer 1 (the clamps above) covers every constraint this module knows
        # about; this is the backstop for one it doesn't. Logged at ERROR --
        # unlike the warnings above, this means the enumeration above is
        # incomplete and should never fire silently. One provider must never be
        # able to halt a holding, so the fallback is still a valid, if minimal, pack.
        logger.error(f"fact_pack: {identity} FactPack construction failed unexpectedly, falling back to a minimal pack: {e}")
        # A fallback pack is otherwise byte-identical to a legitimately
        # data-free holding -- placeholders, confidence=0.0, no citations --
        # and packs are cached to disk and read back long after this log line
        # has scrolled away. The marker is provenance, appended alongside
        # whatever real sources the fragment already carried, not instead of them.
        return FactPack(
            corporate_structure=PLACEHOLDER,
            recent_events=[],
            leadership=PLACEHOLDER,
            fetched_at=fetched_at,
            freshness=freshness,
            confidence=0.0,
            source_citations=[],
            sources_used=[*fragment.sources, _SCHEMA_FALLBACK_SOURCE],
        )
