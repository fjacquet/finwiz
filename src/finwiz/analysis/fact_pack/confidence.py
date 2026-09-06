"""Completeness scoring, per asset class.

A single scale across three structures is what capped a complete fund at 0.70:
it was marked down for lacking a CEO. Each class is scored over the fields that
apply to it, so 1.00 means "we know what there is to know about this kind of
thing", and scores are comparable between holdings of the same class.
"""

from __future__ import annotations

from finwiz.analysis.fact_pack.fragment import PLACEHOLDER
from finwiz.schemas.hybrid_analysis.fact_pack import CryptoFacts, EquityFacts, FundFacts

_W_CITATION = 0.10

_EQUITY_SUMMARY = 0.35
_EQUITY_LEADERSHIP = 0.25
_EQUITY_EVENTS_FILINGS = 0.30
_EQUITY_EVENTS_NEWS = 0.15

# The expense ratio outweighs everything else a fund can tell us: it is the one
# figure that reduces net return every year regardless of what the fund holds.
_FUND_IDENTITY = 0.20
_FUND_EXPENSE_RATIO = 0.30
_FUND_HOLDINGS = 0.25
_FUND_ASSET_MIX = 0.15

_CRYPTO_DESCRIPTION = 0.25
_CRYPTO_SUPPLY = 0.30
_CRYPTO_MARKET_CAP = 0.20
_CRYPTO_LAUNCHED = 0.15


def _populated(value: str | None) -> bool:
    return bool(value and value.strip() and value.strip() != PLACEHOLDER)


def _equity(facts: EquityFacts) -> float:
    total = 0.0
    if _populated(facts.business_summary):
        total += _EQUITY_SUMMARY
    if _populated(facts.leadership):
        total += _EQUITY_LEADERSHIP
    if facts.recent_events:
        total += _EQUITY_EVENTS_FILINGS if facts.events_from_filings else _EQUITY_EVENTS_NEWS
    return total


def _fund(facts: FundFacts) -> float:
    total = 0.0
    if _populated(facts.issuer):
        total += _FUND_IDENTITY
    # `is not None`, not truthiness: a 0.0% fee is a real and notable fact.
    if facts.expense_ratio is not None:
        total += _FUND_EXPENSE_RATIO
    if facts.top_holdings:
        total += _FUND_HOLDINGS
    if facts.asset_mix:
        total += _FUND_ASSET_MIX
    return total


def _crypto(facts: CryptoFacts) -> float:
    total = 0.0
    if _populated(facts.description):
        total += _CRYPTO_DESCRIPTION
    # Supply is known when we can state it, and "uncapped" is a statement.
    if facts.circulating_supply is not None and (facts.supply_is_capped or facts.max_supply is None):
        total += _CRYPTO_SUPPLY
    if facts.market_cap is not None:
        total += _CRYPTO_MARKET_CAP
    if facts.launched_year is not None:
        total += _CRYPTO_LAUNCHED
    return total


def score(details: EquityFacts | FundFacts | CryptoFacts, has_citation: bool) -> float:
    """Completeness in [0.0, 1.0], scored against the class's own fields."""
    if isinstance(details, EquityFacts):
        total = _equity(details)
    elif isinstance(details, FundFacts):
        total = _fund(details)
    else:
        total = _crypto(details)
    if has_citation:
        total += _W_CITATION
    return round(min(total, 1.0), 2)
