# Deterministic Fact Pack — Design

Date: 2026-09-06
Status: approved (brainstorming), not yet planned
Supersedes: the Perplexity-only fetch path in ADR-010 (Fact Pack — Grounded Qualitative)

## Problem

On 2026-09-06 a full run analysed **0 of 64 holdings**. The run ledger recorded
`collect ok ×64`, `quantify ok ×64`, `fact_pack failed ×64`: every holding
short-circuited to `AnalysePending`, and nothing downstream ran. The cause was a
single line of billing state — `Perplexity HTTP 401`, body
`{"type": "insufficient_quota"}` — repeated 512 times.

Two structural facts made a billing problem into a total outage:

1. **Perplexity is the only source of a fact pack.** `fetch_fact_pack_sync` calls
   it and nothing else. When it is unavailable and the cache is cold, the stage
   raises and the holding dies.
2. **The cache was the only thing hiding it.** The same 401 appeared 59 times in
   the 09:31 run on `main`, which still looked healthy because
   `cache/fact_packs` held 58 warm packs and only 6 holdings needed the network.
   The dependency had already failed; the run only *looked* fine.

A fact pack is `corporate_structure`, `leadership`, `recent_events`,
`confidence`, `source_citations`. Measurement on this portfolio (2026-09-06)
shows that free, structured, already-installed sources supply all of it — and
supply the `recent_events` field with *better* evidence than the LLM did.

## Decisions

Taken during brainstorming, with the reasoning that produced them:

- **D1. Perplexity becomes a gap-filler, not the provider.** Deterministic
  sources build the pack; Perplexity is called only for fields still empty.
  36 of 64 holdings then never touch it.
- **D2. The stage FAILs only when the ticker resolves to nothing.** A thin pack
  is emitted rather than withheld. The 0/64 outage is the argument: one
  provider must never be able to halt every holding.
- **D3. The cache and its 3d/7d/90d freshness ladder are kept.** yfinance is
  rate-limited and unofficial; caching also keeps the run gate's
  `fact_pack_stale` check meaningful.
- **D4. `confidence` stops being self-reported.** It becomes a Python function
  of which fields were actually populated.
- **D5. Asset-class routing reads the declared `asset_class`.** Never inferred
  from symbol shape. This repo lost 33 European tickers to a `len(symbol) > 5`
  heuristic that classified them as crypto; that mistake is not repeated.
- **D6. CoinGecko is out of scope.** No client exists in the repo (only a
  hardcoded URL string in `enhanced_crypto_tool.py`), and it would serve 4
  holdings whose one gap Perplexity already fills.

## Measured source coverage

Probed against the live portfolio on 2026-09-06. Composition: 36 stocks (24
US-plain tickers, 12 with a non-US suffix), 27 ETFs, 4 crypto.

| field | US stock | non-US stock | ETF | crypto |
|---|---|---|---|---|
| `corporate_structure` | `longBusinessSummary` (~1.8k chars) | `longBusinessSummary` (1.2–2.0k) | `fundFamily` + `legalType` + `fundInceptionDate` + top holdings | — |
| `leadership` | `companyOfficers` (10) | `companyOfficers` (7–10) | `fundFamily` as manager | — |
| `recent_events` | `sec_filings` (8-K, 10-K, 10-Q…) | news headlines | — | news headlines |
| `source_citations` | `edgarUrl` | `canonicalUrl` | Yahoo quote URL | `canonicalUrl` |

Representative measurements: AAPL 80 filings, CSCO 102, ASML 39 (20-F / 6-K, as
a US-listed foreign issuer). AIR.PA, NESN.SW, 2B7K.DE and BTC-USD return 0 —
`sec_filings` is a US-filing endpoint, not a general one. Business summaries and
officer lists, by contrast, are present for every European stock probed
(AIR.PA 1230 chars / 10 officers, NESN.SW 1998 / 10, SAN.PA 1718 / 7,
SIE.DE 1915 / 10).

`sec_filings` is the quality argument for this whole change: for US listings and
ADRs, `recent_events` becomes *filed corporate events with EDGAR links* rather
than LLM prose. It is citable, dated, and cannot drift between runs.

## Design

### 1. Placement

The public seam is unchanged in name and unchanged in its contract to the stage:

```python
fetch_fact_pack_sync(ticker, company_name, sector, industry, asset_class) -> FactPack | None
```

`asset_class` is the one added parameter. It is available at the call site today
as `ctx.extras["analysis_ctx"].asset_class` and requires no new plumbing.

`analysis/stages/fact_pack.py`, `cache/fact_pack_cache.py`, the `@stage`
decorator's retry semantics, and the stage's OK/FAILED contract are **not
modified**. The blast radius is one function's body.

### 2. Components

New package `src/finwiz/analysis/fact_pack/`:

| module | responsibility |
|---|---|
| `sources/yfinance_source.py` | `info`, `companyOfficers`, `sec_filings`, `news` → per-field fragments |
| `sources/perplexity_source.py` | the existing Perplexity call, narrowed to named missing fields |
| `composer.py` | route by asset class, merge fragments, derive confidence, decide gap-fill |

Each source returns a `FactPackFragment` — a dataclass of optional fields plus
the citations and source label that produced them. A source never returns a
`FactPack`; only the composer builds one. This is what keeps "which source said
what" answerable.

### 3. Composition order

1. Route on declared `asset_class` to the applicable deterministic sources, as
   an ordered list. Order is the merge precedence and is fixed per asset class,
   not discovered at runtime, so two runs over the same inputs compose
   identically.
2. Merge fragments in that order. First non-empty wins; nothing overwrites.
3. Derive `confidence` (§4).
4. If any field is still empty **and** `FF_PERPLEXITY_RESEARCH` is on, make one
   Perplexity call naming only the missing fields.
5. Merge the Perplexity fragment under the same first-non-empty rule, so it can
   only add.
6. Build the `FactPack`. `fetched_at` and `freshness` stay Python-owned.

### 4. Confidence

| component | weight |
|---|---|
| `corporate_structure` populated (not the placeholder) | 0.35 |
| `leadership` populated | 0.25 |
| `recent_events` sourced from SEC filings | 0.30 |
| `recent_events` sourced from news only | 0.15 |
| at least one citation | 0.10 |

Filing-backed and news-backed events are mutually exclusive; the higher applies.
Expected values: US stock with filings 1.00, European stock with news events
0.85, typical ETF 0.70, crypto 0.25.

Crypto scores lowest because yfinance gives it no business summary and no
officers: `corporate_structure` and `leadership` both fall back to the existing
`_PLACEHOLDER` string, which satisfies the schema's `min_length=1` without
claiming a fact. Those two fields are exactly what the gap-fill call requests
when `FF_PERPLEXITY_RESEARCH` is on. A crypto holding whose gap-fill is
unavailable is therefore emitted at 0.25 rather than failed — per D2 — and its
low confidence is the honest signal that almost nothing is known.

The point is comparability. A self-rated number cannot be checked against
anything; a completeness score can be recomputed from the pack itself, compared
between holdings, and trended across runs.

### 5. Schema change

One field added to `FactPack`:

```python
sources_used: list[str] = Field(default_factory=list)  # e.g. ["yfinance.info", "yfinance.sec_filings"]
```

`FactPack` is `extra="forbid"`, so this must be explicit. The default makes it
backward-compatible with the 58 packs already in `cache/fact_packs`, which were
written without it.

`confidence`'s description changes from "AI-rated 0.0-1.0" to state that Python
derives it from field completeness.

### 6. Error handling

- **The only path to FAILED**: `info["quoteType"] is None` (an unresolvable
  ticker returns exactly one key) **and** no cached pack exists. That raises
  `TransientStageError`, preserving `@stage`'s retry-then-FAILED behaviour.
- **Source exceptions never leave their source.** `sec_filings` raises an
  internal 404 for every European ticker; that degrades `recent_events` alone.
  No source exception may reach the composer.
- **Perplexity failure is inert.** Quota, timeout or 401 leaves the
  deterministic pack exactly as built, logged and not raised. It can never turn
  a good pack into a failed stage.
- **429s degrade, they do not fail.** Sources fetch sequentially with bounded
  backoff. A cold cache means 64 holdings back to back, which is the shape
  yfinance throttles.
- **`quoteType` cross-checks the declared asset class.** Routing still uses the
  CSV value; a mismatch logs a warning. This is the cheap detector for the class
  of defect that misrouted 33 tickers, which failed silently for months.

### 7. Testing

- One module per source, fed fixtures captured from the real 2026-09-06
  responses: AAPL (filings present), AIR.PA (filings absent), 2B7K.DE (ETF
  shape), BTC-USD (crypto), ZZZZNOTREAL (unresolvable).
- Network is mocked at the yfinance seam with `mocker.patch`. `unittest.mock`
  stays banned; pytest-socket stays armed.
- Composer: table-driven confidence arithmetic; gap-fill never overwrites a
  deterministic field; a Perplexity 401 leaves the pack byte-identical.
- Backward compatibility: a cached pack written without `sources_used`
  deserializes.
- Stage level: unresolvable ticker → FAILED; thin ETF pack → OK at ~0.70.
- Every new test gets a mutation check. A test that does not bite does not count.

## Risks

- **yfinance is scraped, not contractual.** It can change shape or break without
  notice. Mitigation: the repo already depends on it for prices, so the risk is
  already carried; sources degrade per-field rather than failing.
- **News headlines are noisy.** Yahoo's feed mixes Reuters with "Prediction:
  Amazon Will Join…" opinion pieces. Per the project's own rule — filter noise
  out, do not low-grade it — a provider allowlist and a 12-month `pubDate`
  window apply, accepting fewer events over junk ones.
- **ETF packs stay thin.** All 27 have empty `recent_events` unless Perplexity
  gap-fills. This is the case D2 deliberately permits, and confidence 0.70
  reports it honestly.
- **Confidence weights are a first guess.** They are tunable and recomputable
  from stored packs, so a later change can be validated against history rather
  than argued about.

## Implementation order

1. `FactPackFragment` + the schema change (`sources_used`, `confidence` doc).
2. `yfinance_source` — info / officers / filings / news, per-field degradation.
3. `composer` — routing, merge, confidence.
4. `perplexity_source` narrowed to missing fields; gap-fill wiring.
5. `fetch_fact_pack_sync` body swap; `asset_class` threaded from the stage.
6. Live verification on the real portfolio, cache cleared, `FF_PERPLEXITY_RESEARCH` off.

## Done when

- A run with `FF_PERPLEXITY_RESEARCH=off` and a cold cache produces a pack for
  every resolvable holding, and the run gate's coverage check passes.
- US holdings show filing-derived `recent_events` with EDGAR citations.
- The 58 pre-existing cached packs still load.
- No holding fails because of a fact-pack provider outage.
