# ADR-014: Crypto market data from real sources, with honest degradation

**Status:** Accepted
**Date:** 2026-09-20
**Supersedes:** nothing. Complements ADR-012 (research provider).

## Context

`_collect_crypto_data` passed the yfinance-normalized ticker (`BTC-USD`) to
CoinGecko, which keys on the bare symbol. Every crypto lookup failed, and
`EnhancedCryptoAnalysisTool` returned invented numbers tagged
`sources == ["Fallback Data"]` rather than an error. The collector layered its
own defaults on top (`market_cap 10e9`, `volume_24h 1e9`, `age_years 3.0`).

The 2026-09-20 full run scored all four crypto holdings on a $10B market cap,
zero volume and zero supply. Those fields carry 80% of the crypto fundamental
score, so the four holdings scored almost identically regardless of what they
are. `data_quality.missing_fields` read `[]` because a fabricated value counts
as present.

## Decision

A dedicated `CryptoSourceOrchestrator` resolves crypto market data from a
CoinGecko adapter (primary), the already-fetched yfinance price, and a Kraken
adapter, recording per-field lineage and a pinned confidence.

- Unresolved fields stay `None` everywhere. No fabricated stand-ins.
- Sources that disagree do not arbitrate: the primary keeps the value, the
  divergence is recorded and confidence drops.
- Price falls back CoinGecko, then yfinance, then Kraken. Absence is not
  disagreement.
- Market cap and supply are CoinGecko-only; there is no second source and none
  is invented.
- Kraken's volume is single-venue and in base units; it is converted to USD and
  used only as a last resort, never cross-checked against CoinGecko's aggregate.
- `CryptoAnalyzer` renormalizes its weights over available components, so a
  missing value is excluded rather than scored as the worst observed value.
- Ages come from a curated genesis-year table; an uncurated symbol yields
  `None`, never a default.

## Consequences

- Crypto fundamental scores change materially. Measured on the 2026-09-21
  three-CSV verification run (`data/crypto.csv`, real API data, no mocks):
  BTC's real market cap resolved to 1 629.96 G$ (not the fabricated 10 G$),
  volume_24h to 23.77 G$, circulating supply to ~20.09M BTC and age to 17
  years, with `missing_fields: []` and every source healthy. BTC's fundamental
  score came out at **1.0**, not the ~0.95 this ADR originally predicted
  before the code existed — the real market cap clears every threshold in
  `CryptoAnalyzer`'s scoring bands, so it maxes the component rather than
  landing just under the top band. The other three holdings moved similarly:
  ETH 0.95, SOL 0.81, XRP 0.82 (composite scores 0.802 / 0.764 / 0.732 / 0.688
  respectively) — all four holdings now score on what they actually are
  instead of clustering near-identically on the fabricated $10B floor. See
  `.superpowers/sdd/2026-09-20-crypto-data-sources/task-8-report.md` for the
  full verification record.
- During a CoinGecko outage crypto scores fall instead of looking normal, and
  the drop is visible in `missing_fields`, in confidence and in the run gate.
  This is the intended trade: a visible gap beats an invisible fabrication.
- One extra public Kraken call per crypto holding per run (four today), so the
  cross-check exists even on the happy path.
- The equity `DataSourceOrchestrator` is untouched. Two orchestrators now exist
  with the same contract and different field shapes.
- `portfolio_deep_analyzer`'s crypto branch no longer fabricates, but unlike its
  ETF neighbour it does not raise either: the holding is kept and graded on what
  survived.
