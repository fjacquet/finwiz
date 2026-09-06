# Per-Asset-Class Fact Pack — Design

Date: 2026-09-06
Status: approved (brainstorming), not yet planned
Amends: `2026-09-06-deterministic-fact-pack-design.md` — keeps its D1 (Perplexity as gap-filler),
D2 (fail only on an unresolvable ticker) and D3 (cache and freshness ladder). Replaces its §3–§5,
which assumed a single fact-pack shape for every holding.

## Problem

The `FactPack` schema is shaped for a **company**: `corporate_structure`, `leadership`,
`recent_events`. A fund has no CEO and a protocol has no head office, so two of the three asset
classes are asked questions that do not apply to them. Measured on the live portfolio after the
deterministic sources landed:

| class | what a pack actually contains | confidence |
|---|---|---|
| equity (23) | SEC filings, real officers, business summary | 1.00 |
| equity (13) | no filings; filtered news or nothing | 0.60–0.85 |
| fund (27) | `leadership` = the issuer's name, as a stand-in | 0.70 |
| crypto (4) | two placeholders, 24 characters each | 0.00–0.25 |

`struct=24ch` is the exact length of `"Information indisponible"`. After the symbol-normalisation
fix we correctly identify Bitcoin — and then have nothing to say about it.

The low scores are not the defect. The defect is that they are **honest answers to the wrong
questions**, and that the planned gap-fill would then spend money on Perplexity to paper over a
modelling error: asking an LLM to write prose about an ETF's "recent corporate events" is paying
for a fact that does not exist rather than fetching the facts that do.

A prior claim in this repo's own spec was also wrong and is corrected here: crypto **does** carry a
description. The earlier probe looked for `longBusinessSummary`, an equity field; crypto uses
`description`. That error is why CoinGecko was deferred as the only route to crypto facts — it is
unnecessary, and remains out of scope for a better reason than the one first given.

## Decisions

- **D1. One envelope, a discriminated payload.** `FactPack` keeps its spine — `fetched_at`,
  `freshness`, `confidence`, `source_citations`, `sources_used` — and gains a `details` field typed
  per class. The run gate, the cache and the freshness ladder, all shipped this week, are untouched.
- **D2. Confidence is scored per class**, over the fields that matter for that class. A complete
  fund scores 1.00 instead of being capped at 0.70 by a field it cannot have.
- **D3. `maxSupply = 0` means "no cap", not "unknown".** It counts as a known field. Scoring it as
  absent would penalise Ethereum for having a different monetary policy from Bitcoin.
- **D4. The prompt receives one preformatted block**, not three fixed variables, so labels can suit
  the class.
- **D5. Labels live in one module.** A formatter produces ordered (label, value) rows consumed by
  both the prompt and the report. Schemas stay pure data, per the repo's convention.
- **D6. The legacy fields are removed and the cache is invalidated.** No dead fields kept "just in
  case". A cold cache costs nothing now that the sources are free — which was not true of Perplexity,
  and is a benefit of the new design rather than a concession.
- **D7. A number whose unit cannot be stated is omitted.** `Total Net Assets` reads `143259.6` with
  no documented unit; an AUM without a unit is worse than no AUM.

## Measured source availability

Probed 2026-09-06 against live responses, reading raw types rather than string-formatted output.
That distinction matters: the previous spec recorded a filing date as the string `"2026-09-01"`
because the probe printed it through `str()`, and the resulting wrong assumption silently disabled
`filing_events` for every holding. Types below are the real ones.

**Fund** (`2B7K.DE`, `AEEM.PA`):

| field | source | measured |
|---|---|---|
| issuer | `info["fundFamily"]` | `str` — "BlackRock Asset Management Ireland - ETF" |
| legal type | `info["legalType"]` | `str` — "Exchange Traded Fund" |
| inception | `info["fundInceptionDate"]` | `int` epoch → 2020 |
| expense ratio | `funds_data.fund_operations` | `0.002` → 0.20 % |
| turnover | `funds_data.fund_operations` | `0.0` |
| top holdings | `funds_data.top_holdings` | DataFrame, 10 rows for 2B7K.DE, **0 for AEEM.PA** |
| asset mix | `funds_data.asset_classes` | dict — stock 0.9942, cash 0.0041 |
| sector weights | `funds_data.sector_weightings` | dict — 11 sectors |

`funds_data.description` is empty for both European UCITS funds; it is not a dependable field.

**Crypto** (`BTC-USD`, `ETH-USD`, `SOL-USD`):

| field | source | measured |
|---|---|---|
| description | `info["description"]` | `str` — 411 / 349 / 390 chars |
| launched | `info["startDate"]` | `int` epoch → 2010 / 2015 / 2020 |
| circulating supply | `info["circulatingSupply"]` | `int` |
| max supply | `info["maxSupply"]` | `int` — 21000000 for BTC, **0 for ETH and SOL** |
| market cap | `info["marketCap"]` | `int` |
| 24h volume share | `info["volume24HrMarketCapPercent"]` | `float` |
| citation | `info["coinMarketCapLink"]` | `str` |

**Equity** — unchanged from the amended spec: `longBusinessSummary`, `companyOfficers`,
`sec_filings` (US listings and ADRs), filtered `news`.

## Design

### 1. Schema

```python
class FundHolding(BaseModel):
    symbol: str  # the DataFrame index, e.g. "NVDA", "ASML.AS"
    name: str  # "Holding Percent" column's companion "Name"
    weight: float  # 0.0-1.0, as yfinance reports it


class EquityFacts(BaseModel):
    business_summary: str
    leadership: str
    recent_events: list[str]
    events_from_filings: bool


class FundFacts(BaseModel):
    issuer: str
    legal_type: str
    inception_year: int | None
    expense_ratio: float | None  # 0.002 == 0.20 %
    turnover: float | None
    top_holdings: list[FundHolding]  # symbol, name, weight
    asset_mix: dict[str, float]
    sector_weights: dict[str, float]


class CryptoFacts(BaseModel):
    description: str
    launched_year: int | None
    circulating_supply: float | None
    max_supply: float | None  # None == unknown; 0 == no cap, see `supply_is_capped`
    supply_is_capped: bool
    market_cap: float | None
    volume_24h_market_cap_pct: float | None
```

`FactPack.details: EquityFacts | FundFacts | CryptoFacts` discriminated on `asset_class`, which
becomes an explicit field on the envelope. `supply_is_capped` exists so D3 is carried in the data
rather than inferred by every reader from a magic zero.

### 2. Confidence

| class | weights |
|---|---|
| equity | summary 0.35 · leadership 0.25 · events 0.30 filings / 0.15 news · citation 0.10 |
| fund | issuer+legal type 0.20 · **expense ratio 0.30** · top holdings 0.25 · asset mix 0.15 · citation 0.10 |
| crypto | description 0.25 · supply 0.30 · market cap 0.20 · launched 0.15 · citation 0.10 |

The expense ratio carries the most weight for a fund because it is the only figure that
mechanically reduces net return every year regardless of what the fund holds.

Expected: 2B7K.DE 1.00, AEEM.PA 0.75 (no top holdings), BTC/ETH/SOL 1.00, equities unchanged.

### 3. Rendering and the prompt

`analysis/fact_pack/render.py` exposes `to_rows(pack) -> list[tuple[str, str]]` and
`to_prompt_block(pack) -> str`. Labels are defined once, per class:

- equity — Structure / Direction / Événements récents
- fund — Émetteur / Forme / Frais courants / Principales lignes / Allocation
- crypto — Protocole / Lancement / Offre / Capitalisation

`_helpers.py` injects a single `fact_pack_block` variable. `deep_analysis/config/tasks.yaml` drops
`{corporate_structure}`, `{leadership}` and `{recent_events}` for that one placeholder, and its
line 18 stops claiming the pack is "vérifié via Perplexity". `reporting/sections/insights.py` and
`reporting/sections/factpack.py` consume `to_rows` instead of naming fields.

`validate_template_variables_at_startup()` must keep passing — the removed variables have to leave
the YAML in the same change that stops supplying them.

### 4. Migration

The three legacy fields leave `FactPack`. Cached packs written under the old shape can no longer be
validated, so the cache is invalidated once with the existing `scripts/invalidate_fact_pack.py`, which calls `FactPackCache.invalidate_all()`. No compatibility
shims and no deprecated fields.

The first run after invalidation reports `fact_pack_stale` at 0 %, because every pack is new. That
is correct and self-correcting, but it means the gate's staleness signal carries no information on
that one run.

### 5. Consequence for gap-fill

Under per-class scoring, funds and crypto are complete from deterministic sources alone, so they
need no Perplexity call at all. Gap-fill narrows to equities that have neither filings nor
allowlisted news — measured at **6 of 67 holdings**, against 36 under the single-shape design.

## Risks

- **yfinance is scraped, not contractual**, and this design depends on more of its surface than
  before (`funds_data` especially). Mitigation: the integration shape canary added on this branch is
  extended to cover the fund and crypto fields, and every accessor keeps the existing
  degrade-don't-raise contract.
- **`funds_data` is not uniformly populated.** AEEM.PA returns zero top holdings while 2B7K.DE
  returns ten. Fields are optional by construction and confidence reports the difference.
- **The expense ratio is a single-sourced number carrying the heaviest fund weight.** The repo
  already ships `data/etf_expense_ratios.yaml`; cross-checking yfinance against it, and logging a
  warning on disagreement, is cheap insurance on the one figure an investor will check by hand.
- **A discriminated union changes the cached JSON shape**, so a future third-party reader of
  `cache/fact_packs` would break. Nothing outside this repo reads it today.

## Implementation order

1. The three facts models, `supply_is_capped`, and the `FactPack` envelope change.
2. Per-class confidence.
3. Fund source: `funds_data` accessors with degrade-don't-raise, plus the expense-ratio cross-check.
4. Crypto source: `info` accessors, including the no-cap semantics.
5. `render.py`, the prompt block, `tasks.yaml`, and both report sections.
6. Cache invalidation, canary extension, docs (ADR-010 note, CHANGELOG, CLAUDE.md, PRD).
7. Live verification on the real portfolio.

## Done when

- A fund pack states issuer, legal form, expense ratio and top holdings, and scores 1.00 when all
  are present.
- A crypto pack states supply and its cap semantics correctly for both a capped (BTC) and an
  uncapped (ETH, SOL) asset.
- No holding is asked a question that does not apply to its class.
- The prompt block and the report show class-appropriate labels drawn from one definition.
- Gap-fill is required for equities only.
