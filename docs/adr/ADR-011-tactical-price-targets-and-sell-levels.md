# ADR-011: Tactical Price Targets and Sell-Level Floors per Holding

- **Status:** Accepted
- **Date:** 2026-04-30
- **Deciders:** FinWiz Core Team

## Context

The deep-analysis report shows a verdict per holding (grade, recommendation, narrative) but no actionable *price levels*. Users reading the family financial plan have to do their own arithmetic to answer two questions every position raises:

1. **"À quel prix ce titre vaudrait sa juste valeur dans 3-6 mois ?"** (objectif de cours)
2. **"À quel prix devrais-je vendre si la thèse se casse ?"** (niveau de vente / stop-loss)

The compute primitives already exist:
- `quantitative/price_targets.py` — DCF, P/E, technical, support/resistance, consensus.
- `quantitative/derivative_pricing.py` — full Black-Scholes + Greeks.
- `quantitative/technical/` + TA-Lib — ATR, Fibonacci, support/resistance.
- `schemas/portfolio_review.py:PriceTargets` — already a field on `HoldingDecision`, currently always `None`.
- Price history is collected by `analysis/stages/collect.py` and reused by quantify; no new external API call is needed.

What is missing is (a) a single per-holding helper that orchestrates these primitives consistently across asset classes, and (b) the wiring that surfaces the result in the rendered HTML report.

The user explicitly framed this as a "with our existing data" feature (no new sources, no new costs). AI Minimalism (ADR-003) requires deterministic Python for any computation that is mechanically derivable — both targets and sell-levels are.

## Decision

Compute and surface, for every holding in the deep-analysis report, two deterministic price levels driven by the existing price history:

- **Objectif de cours** (3-6 month tactical target): the higher of the next major technical resistance and a volatility-projected drift, capped at ±25% (stocks, ETFs) or ±40% (crypto).
- **Niveau de vente** (stop-loss floor): the higher of the nearest technical support and `current_price − 2 × ATR(14)` — whichever triggers earlier, ensuring the floor is neither below a credible technical level nor unreasonably far in quiet markets.

A new module `src/finwiz/quantitative/tactical_pricing.py` exposes a single public entry point:

```python
def compute_tactical_pricing(
    ticker: str,
    asset_class: Literal["stock", "etf", "crypto"],
    price_history: pd.Series,
    current_price: float,
    *,
    horizon_months: int = 4,
) -> PriceTargets | None
```

It returns the existing `schemas/portfolio_review.PriceTargets` Pydantic model. `None` is returned only when the input has fewer than 60 trading days — every other edge case (missing ATR inputs, non-finite prices, collapsed ranges) yields safe defaults with a logged warning, matching the round-2 backtester resilience pattern.

Wiring path (each step is one short edit):

1. `analysis/stages/quantify.py` calls the helper after the existing technical-indicator computation and attaches the result to `QuantitativeAnalysis.price_targets` (new optional field).
2. `orchestrators/portfolio_review/merge.py` copies `quantitative.price_targets` onto `HoldingDecision.price_targets` for both the success and N/A branches.
3. `reporting/section_generators.py` adds two compact columns to the holdings table (target with `±%` delta, sell-level with `−%` delta) and renders a "🎯 Targets" detail panel inside each ticker's per-holding HTML report (`output/{asset_class}/{ticker}_report.html`) showing target, sell-level, and a one-sentence French rationale per number with a confidence badge (high/medium/low).

Confidence is high when the resistance/support level and the volatility-drift number agree directionally (within 10%), medium when they differ by ≤10%, low when they differ by more than 10% or when price history covers fewer than 120 trading days.

DCF and P/E primitives are deliberately **not** used in this scope: they revert on multi-year cycles and don't fit a 3-6 month horizon. The existing helpers stay available for a future "12-month strategic target" addition.

## Consequences

### Positive

- Every holding in the report carries two actionable numbers users can plug straight into broker stop-loss / take-profit orders.
- 100% deterministic Python — same inputs produce the same outputs, no AI cost, no external API call beyond the price history we already collect.
- Reuses existing schemas (`PriceTargets`) and existing math (`quantitative.price_targets`, `quantitative.technical`); the new module is thin orchestration.
- Works uniformly across stocks, ETFs, and crypto — no per-asset-class output asymmetry that confuses users.
- Confidence label flags wide-band cases (e.g., a recently-IPO'd stock with 90 days of history) so users don't read precision that isn't there.

### Negative

- Two more columns in the holdings table tighten horizontal layout on narrow screens. Mitigated by keeping each column to a single `$X (±Y%)` format.
- The 3-6 month horizon is a single point on the spectrum; users running a multi-year buy-and-hold strategy may want a longer-horizon strategic target later. (Followup: revive the existing DCF/PE helpers behind a separate "strategic target" ADR if requested.)
- ATR-based stop-loss does not adapt to fundamental regime shifts (earnings miss, sector rotation). It catches volatility-aware breaks, not narrative breaks; the qualitative section of the report is still where regime information lives.

### Risks

- **False precision:** users may treat the target as a forecast instead of a tactical reference. Mitigation: explicit "tactical 3-6 mois" label in every rendering site, plus the confidence badge.
- **Stale price history:** if the data collector returns a frame that's quietly truncated (e.g., yfinance hiccup), targets and sell-levels would lock onto a stale anchor. Mitigation: `compute_tactical_pricing` requires the most-recent date in `price_history` to be within 7 calendar days of "now", otherwise returns `None` and the report shows a `—` placeholder.
- **Crypto volatility blowing through caps:** the ±40% cap occasionally clips a justified target during fast moves. Acceptable trade-off given the alternative (uncapped projections producing absurd numbers).

## References

- ADR-003: AI Minimalism (drives the deterministic-Python-only constraint).
- ADR-008: Options-Implied Scenario Probabilities (companion deterministic-derivative work).
- `src/finwiz/quantitative/price_targets.py` — DCF, P/E, technical, consensus primitives.
- `src/finwiz/quantitative/derivative_pricing.py` — Black-Scholes used elsewhere.
- `src/finwiz/schemas/portfolio_review.py:PriceTargets` — destination Pydantic model.
- `src/finwiz/analysis/stages/quantify.py` — integration point for compute step.
- `src/finwiz/orchestrators/portfolio_review/merge.py` — propagation point into HoldingDecision.
- `src/finwiz/reporting/section_generators.py` — render point for both compact and detail surfaces.
