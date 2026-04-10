# ADR-008: Options-Implied Scenario Probabilities

- **Status:** Accepted
- **Date:** 2026-04-10
- **Deciders:** FinWiz Core Team

## Context

The deep analysis report displays bull/base/bear scenario probability bars for each holding.
Previously these came from the AI crew (`scenario_probabilities` in `QualitativeInsights`),
which had two problems:

1. **AI omission**: The model frequently skipped the structured float object under token
   pressure, leaving `scenario_probabilities=None` and showing "Analyse de scénarios non
   disponible" in the HTML report.
2. **Uncalibrated guesses**: When the AI did produce values, they were derived from its
   qualitative narrative — not from any market signal. For real-money decisions this is
   insufficient; the numbers conveyed false precision.

The need is for probability estimates grounded in actual market consensus, with a graceful
fallback for assets that lack liquid options markets (crypto, niche ETFs).

## Decision

Derive scenario probabilities from the options market using Black-Scholes N(d₂), applied to
implied volatility fetched via yfinance. Implement a strict priority chain:

1. **Options-implied** (primary) — market consensus, most trustworthy for stocks and liquid ETFs
2. **Python formula** (fallback) — deterministic derivation from `composite_score` and
   `risk_score`; used when options data is unavailable
3. **AI-provided** — accepted only if it pre-empts the Python fallback (i.e., options data
   was unavailable AND the AI produced a value); never trusted over market data

### Implementation

**Data collection** (`deep_analysis_data_collector.py`):

- `_collect_options_iv()` fetches the options chain for the expiry closest to 90 days out
- IV is linearly interpolated at the +20% strike (bull) and -15% strike (bear)
- Results stored as `options_bull_iv`, `options_bear_iv`, `options_T` in `raw_data`
- Fails silently — any exception skips options data without aborting the pipeline

**Probability computation** (`deep_analysis_pipeline.py`):

- `_bs_nd2(S, K, T, r, σ)` — Black-Scholes N(d₂): risk-neutral P(S_T > K)
- `_compute_options_probabilities(raw_data)` — returns `ScenarioProbabilities` or `None`
- Priority logic applied in `synthesize_enriched_analysis()` before writing to `EnrichedAnalysis`

**Formula (Python fallback)**:

```
signal = 0.7 × composite_score + 0.3 × (1 − risk_score / 5)
bull   = 0.10 + 0.45 × signal
bear   = 0.60 − 0.50 × signal
base   = 1 − bull − bear
```

**Configuration**: `RISK_FREE_RATE` env var (default `0.045`) controls the risk-free rate.

## Consequences

### Positive

- Scenario probabilities for large-cap stocks and liquid ETFs are now anchored to the
  options market — the most liquid expression of collective forward-looking expectations.
- Python formula fallback ensures probability bars always appear (no more "non disponible").
- Silent failure design means crypto and niche ETFs continue to work without modification.
- Zero additional AI cost — options IV fetch is a Python tool call (~50ms, $0).

### Negative

- Options IV fetch adds latency (~50–200ms per holding) for stocks and ETFs.
- yfinance options data may be delayed or unavailable for thinly traded securities,
  causing silent fallback to the Python formula.
- The +20%/−15% strike thresholds are convention, not derived from the holding's own
  historical move distribution.

### Risks

- yfinance rate limits could cause widespread fallback to Python formula during large
  parallel runs. Mitigated by silent failure design — pipeline continues regardless.
- Black-Scholes assumes log-normal returns; fat tails (common in volatile stocks/crypto)
  may cause the options-implied probabilities to understate extreme scenarios.

## References

- `src/finwiz/orchestrators/deep_analysis_data_collector.py` — `_collect_options_iv()`, `_interpolate_iv()`
- `src/finwiz/analysis/deep_analysis_pipeline.py` — `_bs_nd2()`, `_compute_options_probabilities()`, `synthesize_enriched_analysis()`
- [ADR-003: AI Minimalism](ADR-003-ai-minimalism.md) — Python wins over AI for deterministic data
- [ADR-006: Context Scoping Strategy](ADR-006-context-scoping-strategy.md) — token budget context
