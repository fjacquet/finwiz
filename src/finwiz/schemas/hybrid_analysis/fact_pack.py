"""FactPack schema for grounded qualitative analysis (v5.2).

Class-appropriate facts from structured sources, cached for 7 days, injected
into the qualitative prompt as ground truth. The qualitative crew must NOT
contradict the fact pack — anti-hallucination becomes structural.

Provenance:
- Equity: business summary and officers from yfinance info; recent events from
  SEC filing index for US listings and ADRs, otherwise from filtered wire news.
- Fund: issuer, legal form and inception from yfinance info; ongoing charges
  and holdings from yfinance funds_data.
- Crypto: description, supply and market figures from yfinance info, which
  sources these from CoinMarketCap.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

_FRESHNESS_VALUES = ("fresh", "recent", "stale")
Freshness = Literal["fresh", "recent", "stale"]


class FundHolding(BaseModel):
    """One line of a fund's published holdings."""

    symbol: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=200)
    # None when yfinance reported this holding's weight as unusable
    # (missing/NaN/out of range): a known holding whose weight is unknown,
    # not a fact to clamp to a boundary.
    weight: float | None = Field(default=None, ge=0.0, le=1.0, description="Fraction of the fund, as yfinance reports it (0.077756 == 7.78%)")

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class EquityFacts(BaseModel):
    """A company: what it does, who runs it, what it filed."""

    kind: Literal["equity"] = "equity"
    business_summary: str = Field(min_length=1, max_length=2000)
    leadership: str = Field(min_length=1, max_length=1000)
    recent_events: list[str] = Field(default_factory=list, max_length=10)
    events_from_filings: bool = False

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class FundFacts(BaseModel):
    """A fund: who issues it, what it costs, what it holds.

    There is no CEO here, and asking for one is what produced a 0.70 ceiling
    and an issuer's name standing in as `leadership`.
    """

    kind: Literal["fund"] = "fund"
    issuer: str = Field(min_length=1, max_length=200)
    legal_type: str = Field(default="", max_length=100)
    inception_year: int | None = Field(default=None, ge=1900, le=2200)
    expense_ratio: float | None = Field(default=None, ge=0.0, le=1.0, description="0.002 == 0.20% per year")
    turnover: float | None = Field(default=None, ge=0.0)
    top_holdings: list[FundHolding] = Field(default_factory=list, max_length=25)
    asset_mix: dict[str, float] = Field(default_factory=dict)
    sector_weights: dict[str, float] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CryptoFacts(BaseModel):
    """A protocol: what it is, when it launched, how its supply behaves."""

    kind: Literal["crypto"] = "crypto"
    description: str = Field(min_length=1, max_length=2000)
    launched_year: int | None = Field(default=None, ge=1900, le=2200)
    circulating_supply: float | None = Field(default=None, ge=0.0)
    max_supply: float | None = Field(default=None, ge=0.0, description="None when unknown OR uncapped; read supply_is_capped to tell them apart")
    supply_is_capped: bool = False
    market_cap: float | None = Field(default=None, ge=0.0)
    volume_24h_market_cap_pct: float | None = Field(default=None, ge=0.0)

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @model_validator(mode="after")
    def _check_supply_cap_consistency(self) -> CryptoFacts:
        """Capped and uncapped supplies are data, not inferred from max_supply value.

        Without this invariant, a reader re-infers capped/uncapped from max_supply,
        which is the yfinance magic (maxSupply == 0) we added supply_is_capped to
        eliminate. The two fields must agree: if capped, max_supply is a number;
        if uncapped, max_supply is None.
        """
        has_max = self.max_supply is not None
        if self.supply_is_capped != has_max:
            raise ValueError(
                f"supply_is_capped={self.supply_is_capped!r} contradicts max_supply={self.max_supply!r} (if capped, max_supply must be not None; if uncapped, must be None)"
            )
        return self


# Beyond this, a cached fact pack is not merely stale — it predates any
# reporting cycle we would defend, so the cache evicts rather than serve it.
_STALE_HORIZON_DAYS = 90


class FactPack(BaseModel):
    """Verified facts for one holding, typed per asset class.

    Lifecycle: built once per holding from structured sources (yfinance,
    plus a curated expense-ratio table for funds) and cached. Perplexity is
    an optional gap-filler for equities that have neither SEC filings nor
    allowlisted wire-news coverage, and may never run. The `freshness` field
    is Python-derived from `fetched_at` — AI cannot lie about it
    (cross-checked by model_validator).
    """

    asset_class: Literal["stock", "etf", "crypto"]
    details: EquityFacts | FundFacts | CryptoFacts = Field(discriminator="kind")
    fetched_at: datetime
    freshness: Freshness
    confidence: float = Field(ge=0.0, le=1.0, description="Python-derived completeness score 0.0-1.0 (see analysis/fact_pack/fragment.py)")
    source_citations: list[str] = Field(default_factory=list, max_length=20, description="Perplexity citation URLs")
    sources_used: list[str] = Field(
        default_factory=list,
        description="Which sources produced this pack, e.g. ['yfinance.info', 'yfinance.sec_filings']",
    )

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @classmethod
    def derive_freshness(cls, fetched_at: datetime) -> Freshness:
        """Python owns freshness derivation; AI may not lie about it.

        <3d -> fresh, 3-7d -> recent, 7-90d -> stale, >90d -> raises (cache must have evicted).
        """
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=UTC)
        now = datetime.now(UTC)
        age = now - fetched_at
        if age < timedelta(days=3):
            return "fresh"
        if age < timedelta(days=7):
            return "recent"
        # Corporate structure and leadership do not turn over in a fortnight.
        # A 15-day cliff meant a rate-limited run had no cache to fall back on
        # and killed the holding outright — worse than a labelled stale answer.
        # Staleness is a payload field, not a stage outcome (see stages/fact_pack.py).
        if age < timedelta(days=_STALE_HORIZON_DAYS):
            return "stale"
        raise ValueError(f"FactPack older than {_STALE_HORIZON_DAYS} days (age={age}); cache should have evicted")

    @model_validator(mode="after")
    def _check_freshness_matches_fetched_at(self) -> FactPack:
        """AI may not lie about freshness — Python is authoritative."""
        expected = self.derive_freshness(self.fetched_at)
        if self.freshness != expected:
            raise ValueError(f"freshness={self.freshness!r} contradicts fetched_at={self.fetched_at} (Python derived: {expected!r})")
        return self

    @model_validator(mode="after")
    def _check_details_match_asset_class(self) -> FactPack:
        """The envelope's class and the payload's tag are one fact, stated twice."""
        expected = {"stock": "equity", "etf": "fund", "crypto": "crypto"}[self.asset_class]
        if self.details.kind != expected:
            raise ValueError(f"asset_class={self.asset_class!r} requires details.kind={expected!r}, got {self.details.kind!r}")
        return self
