# Design: crypto market data from real sources, with honest degradation

**Date:** 2026-09-20
**Status:** approved
**Path:** architectural (new acquisition seam for one asset class; changes what
"missing" means between collection and scoring)

## Problem

Crypto fundamental data is fabricated in production. Nobody noticed because the
fabricated values are plausible.

`DeepAnalysisDataCollector._collect_crypto_data` passes the yfinance-normalized
ticker (`BTC-USD`) to `EnhancedCryptoAnalysisTool`, which queries CoinGecko.
CoinGecko has no `BTC-USD`. Measured live on 2026-09-20:

```text
BTC-USD -> Cryptocurrency 'BTC-USD' not found on CoinGecko  -> Fallback Data
BTC     -> price=81114  market_cap=1_629_408_510_367
           volume_24h=23_900_006_504  circulating_supply=20_087_096
```

The lookup fails for every holding, and the failure is swallowed into
`_create_fallback_crypto_data`, which returns invented numbers instead of an
error. The collector then applies its own fabricated defaults on top. The
2026-09-20 21:16 run (all 67 holdings) produced, for all four crypto holdings:

| Holding | `market_cap` used | real | `volume_24h` | `circulating_supply` | `age_years` |
|---|---|---|---|---|---|
| BTC | 10 G$ | 1 629 G$ | 0 | 0 | 15.0 |
| ETH | 10 G$ | — | 0 | 0 | 9.0 |
| SOL | 10 G$ | — | 0 | 0 | 4.0 |
| XRP | 10 G$ | — | 0 | 0 | 3.0 |

`CryptoAnalyzer.calculate_fundamental_score` weights market cap 40 %, volume
30 %, age 20 %, supply 10 %. Three of those four inputs are fabricated, so
**80 % of every crypto fundamental score is computed on invented data**. The
four holdings score almost identically (0.63 / 0.63 / 0.59 / 0.59) regardless of
what they actually are; the only thing separating them is a hardcoded age table.
With real data BTC's fundamental score would be roughly 0.95 instead of 0.63.

`data_quality.missing_fields` reports `[]` for all four. That is the mechanism of
the lie: the fabricated value is written into `collected_data`, so the
completeness check sees the field as present.

Prices are the one thing that is correct today — they come from yfinance, not
from this broken path, and match Kraken live within 0.1–0.4 %.

### Where the fabrication lives

```text
orchestrators/deep_analysis_data_collector.py:153-155   volume 1e9 / age 3.0 / mcap 10e9  (except branch)
orchestrators/deep_analysis_data_collector.py:182       mcap 10e9                         (happy path, if <= 0)
orchestrators/deep_analysis_data_collector.py:208-210   volume 1e9 / age 3.0 / mcap 10e9  (non-dict branch)
scoring/portfolio_deep_analyzer.py:243-245              mcap 100e9 / volume 1e9 / age 5
tools/enhanced_crypto_tool.py:210                       _create_fallback_crypto_data
```

Crypto is the only asset class that fabricates. The stock and ETF branches
degrade honestly (`expense_ratio = None`, `company_info = {}`), and
`portfolio_deep_analyzer.py:230-238` states the rule explicitly for ETFs:

```text
# CRITICAL: Do NOT use defaults for expense_ratio and tracking_error
# These are critical fields that must come from real data
```

The crypto branch immediately below does the opposite. Honest degradation is
already this repo's rule; crypto is the branch that never received it.

Symbol normalization is likewise already solved in two of the three call sites —
`tools/portfolio_price_service.py:296` and
`orchestrators/discovery/extractors/crypto_extractor.py:151` both strip `-USD`.
Only the deep-analysis collector does not.

## Decisions taken in the brainstorm

- **Total source failure degrades honestly**: the field is absent (`None`),
  declared in `data_quality.missing_fields`, and confidence drops. Never a
  fabricated stand-in. Consequence accepted: during an API outage crypto scores
  fall instead of looking normal, and that is visible in the run gate.
- **A dedicated crypto orchestrator**, not a generalization of the equity one.
  `DataSourceOrchestrator` has the right contract (per-field lineage,
  confidence, `None` on missing) but `FundamentalData` is hardwired to four
  equity metrics with equity validation bounds. Generalizing it would rework a
  working path for no crypto benefit.
- **Disagreement is observed, not arbitrated**: the designated primary always
  keeps the value. Other sources only record a divergence and lower confidence.
  Median arbitration was considered and rejected as less predictable.
- **CoinGecko is primary for price**, so price, market cap and volume are
  mutually consistent (same source, same snapshot).
- **Fallback order when CoinGecko is unavailable: yfinance, then Kraken.**
  Absence is not disagreement — the observation-only rule governs conflicting
  values, not a missing primary. Without a fallback rule a CoinGecko rate limit
  would leave the holding with no price at all and break `price_targets`.
- **`age_years` stays a curated table**, corrected, with unknown mapping to
  `None`. Same precedent as the curated ETF expense-ratio table already in the
  repo. Deriving age from `history(period="max")` was rejected: a network call
  per holding to rediscover an immutable constant, and first-quote date is not
  genesis date.
- **Scope**: the collector plus the crypto branch of `portfolio_deep_analyzer`.
  Both places that fabricate today are fixed together. Auditing stock and ETF
  for the same pattern (`aum 5e9`) is out of scope — those paths work.

## Design

### 1. New module — `data/crypto_source_orchestrator.py`

Mirrors the contract of `DataSourceOrchestrator`:

```text
@dataclass
class CryptoMarketData:            # what one adapter returns
    ticker: str
    source: str
    timestamp: datetime
    confidence: float              # 0.0..1.0
    price: float | None = None
    market_cap: float | None = None
    volume_24h: float | None = None
    circulating_supply: float | None = None
    max_supply: float | None = None
    raw_data: dict[str, Any] | None = None
    warnings: list[str] | None = None

@dataclass
class CryptoLineage:               # which source supplied which field
    price_source: str | None = None
    market_cap_source: str | None = None
    volume_24h_source: str | None = None
    supply_source: str | None = None

@dataclass
class CryptoOrchestrationResult:
    ticker: str
    timestamp: datetime
    price: float | None = None
    market_cap: float | None = None
    volume_24h: float | None = None
    circulating_supply: float | None = None
    max_supply: float | None = None
    lineage: CryptoLineage = field(default_factory=CryptoLineage)
    confidence: float = 0.0
    sources_attempted: list[str] = field(default_factory=list)
    sources_succeeded: list[str] = field(default_factory=list)
    sources_failed: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    price_divergence_pct: float | None = None

class CryptoSourceOrchestrator:
    def fetch(self, ticker: str, *, yfinance_price: float | None = None) -> CryptoOrchestrationResult
```

Resolution order inside `fetch`:

1. CoinGecko adapter. On success it supplies price, market cap, volume, both
   supplies; lineage records `"coingecko"` for each.
2. Kraken adapter, attempted on every fetch — one extra public call per crypto
   holding per run (four today). When CoinGecko succeeded, Kraken's only job is
   observation; when it failed, Kraken is also a price fallback candidate.
3. Price value: CoinGecko if present; else `yfinance_price` (passed in by the
   caller, already fetched, no extra call); else Kraken. Lineage records which
   one was actually used.
4. `price_divergence_pct` = max relative spread across the prices actually
   obtained. Above 2 % it produces a WARNING and lowers confidence. It never
   changes the value.
5. Confidence is pinned so two readers cannot compute it differently: 1.0 when
   CoinGecko supplied the price, 0.8 for the yfinance fallback, 0.6 for the
   Kraken fallback, 0.0 when no source answered; then minus 0.2 if
   `price_divergence_pct` exceeds 2 %, and minus 0.1 for each of market cap,
   volume and supply left unresolved. Floored at 0.0.
6. `market_cap`, `circulating_supply`, `max_supply` are CoinGecko-only. If
   CoinGecko failed they stay `None`. There is no second source for them and
   none is invented.
7. `volume_24h`: CoinGecko when available. Kraken's volume is used only as a
   last resort and lineage marks it `"kraken:single-venue"`, because Kraken
   reports one venue in base units while CoinGecko aggregates all venues in USD.
   The two are not comparable, so they are never cross-checked against each
   other — comparing them would generate noise, not signal.

### 2. Adapters — `data/adapters/crypto/`

A small `BaseCryptoAdapter` returning `CryptoMarketData`. It does not extend
`BaseDataAdapter`, which imposes `FundamentalData` and equity validation bounds.

**`coingecko_adapter.py`** wraps `EnhancedCryptoAnalysisTool`, normalizing the
ticker (`BTC-USD` to `BTC`) through a shared `normalize_crypto_symbol()` helper.

Critical detail: the wrapped tool does not raise on a failed lookup. It returns
invented data tagged `sources == ["Fallback Data"]`. The adapter MUST treat that
marker as a failure and return `None`. Missing this check would move the
fabrication one layer down instead of removing it.

**`kraken_adapter.py`** wraps `KrakenTickerInfoTool` with pair `f"{base}USD"`,
reading `c[0]` (last trade price) and `v[1]` (24 h volume, base units). All four
portfolio pairs resolve on the public endpoint with no API key (verified
2026-09-20): `BTCUSD` to `XXBTZUSD`, `ETHUSD` to `XETHZUSD`, `XRPUSD` to
`XXRPZUSD`, `SOLUSD` to `SOLUSD`. A pair Kraken does not list is a normal
failure, not an error.

`normalize_crypto_symbol()` lives in the crypto adapter package. The two
existing call sites that already strip `-USD` are left alone; they work, and
changing them is unrelated churn.

### 3. Scorer must not turn "missing" into "worst"

`CryptoAnalyzer.calculate_fundamental_score` reads every input through
`_safe_get_float(data, key, 0.0)`, and `_safe_get_float`
(`crew_export_generator.py:349`) maps `None` to the default. So a `None` market
cap would score 0.0 — replacing a falsely good score with a falsely catastrophic
one, which is the same lie inverted.

`calculate_fundamental_score` therefore computes over the components actually
present and **renormalizes their weights** (market cap 40 %, volume 30 %, age
20 %, supply 10 %). Excluded components are listed in the returned details so
the report and the gate can see which ones were dropped. When no component is
available the fundamental score is `None`, not 0.0.

### 4. `age_years` — store genesis year, derive age

The current table stores ages (`BTC: 15.0`), values that silently rot every
year. It stores genesis years instead, and the age is derived at run date:

```text
CRYPTO_GENESIS_YEAR = {"BTC": 2009, "ETH": 2015, "XRP": 2012, "SOL": 2020}
```

An unlisted symbol yields `None`, never `3.0`. XRP is the holding this fixes:
it dates from 2012 and is currently scored as three years old because it was
absent from the table and took the default.

### 5. Wiring

`_collect_crypto_data` calls the orchestrator, passing the already-fetched
yfinance price, and copies the result across with explicit `None` for anything
missing. The three fabrication sites (`153-155`, `182`, `208-210`) are deleted.
Lineage and warnings are carried into `collected_data` for the report.

`portfolio_deep_analyzer.py:243-245` adopts the *no-fabricated-default* half of
its ETF neighbour's rule: `market_cap`, `volume_24h` and `age_years` all pass
`None` through instead of `100e9` / `1e9` / `5`.

It deliberately does NOT adopt the ETF branch's `CriticalFieldError`. Raising
would skip the holding entirely, which is the "fail the holding" option
considered and rejected in the brainstorm. The chosen behaviour is to keep the
holding and let the renormalizing scorer (section 3) grade it on whatever
components survived, with the gap declared in `missing_fields` and confidence.
Removing the default is what stops the lie; failing the holding is a separate
policy this design does not take.

`_identify_missing_fields` (`crew_export_generator.py:281`) already counts `None`
as missing, so writing `None` makes the declaration truthful with no further
work. One addition is required: `market_cap` is not in its `key_fields` list for
crypto and must be added, otherwise a missing market cap still goes unreported.

### 6. Testing

pytest-mock only, no network; adapters are stubbed at the tool seam.

- Adapter: CoinGecko success maps every field; `sources == ["Fallback Data"]`
  counts as failure and returns `None`; `BTC-USD` is normalized to `BTC`;
  Kraken parses `c[0]` and `v[1]`; an unlisted Kraken pair fails cleanly.
- Orchestrator: primary keeps the value on disagreement; divergence above 2 %
  warns and lowers confidence without changing the value; fallback order is
  yfinance then Kraken; all sources failing yields `None` everywhere plus
  populated `sources_failed`; market cap stays `None` when CoinGecko fails.
- Scorer: weights renormalize over available components; all-missing yields a
  `None` score, never 0.0; excluded components appear in the details.
- Collector: no fabricated constant survives anywhere in the output;
  `missing_fields` lists what is genuinely absent.
- `portfolio_deep_analyzer`: a missing crypto market cap passes through as
  `None` — no fabricated default, and no `CriticalFieldError`; the holding is
  still scored.
- One `integration`-marked test against the public Kraken endpoint, skippable.

### 7. Verification

1. `make check`, `uv run mypy src/finwiz`, `uvx vulture src/finwiz --min-confidence 80`.
2. Three-CSV cheap run: BTC's `market_cap` reads about 1 630 G$, not 10 G$;
   `volume_24h` is non-zero; `circulating_supply` is about 20.1 M;
   `missing_fields` is empty for a healthy run.
3. One run with the CoinGecko path forced to fail: price still resolves through
   yfinance, market cap and supply are absent and declared, the crypto
   fundamental score is computed on the remaining components with renormalized
   weights, and the drop is visible rather than hidden.

## Out of scope

- Auditing stock and ETF paths for the same fabricated-default pattern
  (`aum 5e9` and friends). Those paths work; changing them shifts scores.
- Changing the two call sites that already normalize crypto symbols correctly.
- Adding CoinGecko `genesis_date` support to `crewai_custom_tools` (separate
  repository).
- Rendering lineage and divergence in the HTML report. The data is recorded;
  displaying it is a reporting change.
- Wiring Kraken into the deep-analysis crew's agent tools. The agent has no
  tools by design (`response_model` requires an empty tool list, pinned by
  `test_asset_analyst_has_no_tools`); this work is entirely in the Python
  collection path.
