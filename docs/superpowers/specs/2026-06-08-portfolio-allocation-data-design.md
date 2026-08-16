# Portfolio Allocation Data — Design

**Date:** 2026-06-08
**Status:** Approved
**Prerequisite for:** allocation-weighted strategic posture, replacing the
interim count-based weighting.

> **Correction (2026-08-16):** this line previously pointed at
> `docs/superpowers/plans/2026-06-08-report-freshness-and-portfolio-posture.md`.
> That plan has never existed on `main` — it was authored on the unmerged
> `fix/report-freshness-and-posture` branch, so the link was dead for every
> reader from the day this spec landed.

## Problem

Holdings carry no position size, so the portfolio has no weights. Input CSVs
(`data/stock.csv`, `data/etf.csv`, `data/crypto.csv`) have only `Name,Ticker,Currency,Active`
(crypto lacks `Currency`), and `RawHolding` / `HoldingDecision` / `PortfolioReview` carry no
quantity/value/weight. The CSV `Currency` column is also **unreliable** — mostly `USD` even
for Swiss/EU tickers (`Yahoo:AEEM.PA` labelled USD; `Yahoo:AUUSI.SW` labelled USD). Without
weights, the report can't represent the portfolio by allocation.

Tickers are source-prefixed: `Yahoo:AAPL`, `Yahoo:AEEM.PA`; crypto is bare (`BTC`).

## Goals / Non-goals

**Goals**

- Each holding carries a position **Quantity** (units/shares) from the CSV.
- Compute each holding's market value in its **native currency** (from the price API) and
  convert to a **EUR** base via **live FX**, yielding a portfolio **weight** (`% of total EUR value`).
- Surface `quantity`, `native_currency`, `native_value`, `eur_value`, `weight` on the holding model.
- Provide an explicit `make fix-currencies` that rewrites the CSV `Currency` column from the
  authoritative price-API currency (intentional, not per-run).
- Degrade gracefully: missing/blank quantity or unavailable price/FX → that holding's weight is
  `None`; the run never crashes and other weights still compute (over the holdings that do have data).

**Non-goals**

- Cost basis, P&L, tax lots, or historical performance.
- Rebalancing trade math (separate module already exists).
- Changing the report-posture plan here (it consumes the new weights; the upgrade is a small
  follow-up edit to that plan's B2/B4).
- Auto-mutating input CSVs on every run.

## Decisions (from brainstorm)

- Source of truth: **Quantity** column in the CSVs (units/shares).
- Base currency: **EUR**.
- Native currency + price: from the **price API** (yfinance quote currency + last price), authoritative.
- FX: **live** (yfinance FX pairs, e.g. `CHFEUR=X`), cached per run.
- CSV Currency correction: **explicit `make fix-currencies`** command (rewrites `data/*.csv` in place).
- Missing data: weight `None`, graceful.

## Architecture

A new deterministic **valuation** unit takes holdings + quantities, resolves native price &
currency (price API), resolves FX→EUR (live, cached), and computes per-holding `native_value`,
`eur_value`, and portfolio `weight`. This is pure Python (AI Minimalism: no AI). It runs once
during portfolio processing and populates the holding model; weights then flow to the report and
to the strategic-posture combine.

### Components

1. **CSV schema + ingestion** (`portfolio_holdings_processor.py`, `schemas/portfolio_processing.py`)
   - Add optional `Quantity` column to `data/stock.csv`, `data/etf.csv`, `data/crypto.csv`
     (blank allowed). `_read_csv_holdings` parses it into `RawHolding.quantity: float | None`
     (robust parse: blank/invalid → `None`, logged at debug).
   - Crypto CSV gains `Quantity` (its `Currency` stays absent → native currency from price API,
     typically USD).

2. **FX provider** (`src/finwiz/data/fx_rates.py`, new)
   - `get_fx_rate(from_ccy: str, base: str = "EUR") -> float | None` — live rate via yfinance pair
     (`f"{from_ccy}{base}=X"`; identity 1.0 when equal; handles GBp→GBP/100 pence quirk). Per-run
     cache (module singleton dict, reset by the existing test isolation fixture pattern if needed).
     Best-effort: failure → `None` (caller treats weight as unknown).

3. **Valuation** (`src/finwiz/scoring/portfolio_valuation.py`, new)
   - `value_holdings(holdings, *, base="EUR", price_fn, fx_fn) -> ValuationResult` — pure, injects
     price/FX functions for testability. For each holding with a quantity: get `(price, native_ccy)`
     from `price_fn`; `native_value = quantity * price`; `eur_value = native_value * fx_fn(native_ccy)`.
     Sum `eur_value` over holdings that resolved → `total_eur`; `weight = eur_value / total_eur`.
     Holdings missing quantity/price/FX get `weight=None` and are excluded from `total_eur`.
   - Returns per-ticker `{quantity, native_currency, native_value, eur_value, weight}` + totals +
     a coverage note (`N of M holdings priced; X% of holdings by count weighted`).

4. **Holding model fields** (`schemas/portfolio_processing.py::RawHolding`,
   `schemas/portfolio_review.py::HoldingDecision`)
   - Add optional: `quantity: float | None`, `native_currency: str | None`,
     `native_value: float | None`, `eur_value: float | None`, `weight: float | None` (0..1).
     All optional/defaulted → no breaking change; `extra="forbid"` models get explicit fields.

5. **Wiring** (`portfolio_holdings_processor.py` / `portfolio_review_orchestrator.py`)
   - After holdings are built, run `value_holdings` (using the existing price service as `price_fn`
     and `fx_rates.get_fx_rate` as `fx_fn`) and stamp the weight fields onto the decisions.
   - `PortfolioReview` gains an optional `total_value_eur: float | None` for the report header.
     (`base_currency` keeps its existing default of `"CHF"` for backward compatibility; the EUR
     valuation is surfaced explicitly via `total_value_eur` rather than by changing that default.)

6. **`make fix-currencies`** (`scripts/fix_csv_currencies.py`, new + Makefile target)
   - Reads each CSV, resolves the authoritative currency per ticker from the price API, rewrites the
     `Currency` column in place (preserving row order and other columns; adds `Currency` to crypto.csv).
     Prints a diff summary (old→new per ticker). Idempotent. Not invoked by the analysis flow.

### Data flow

CSV (`Quantity`) → `RawHolding.quantity` → `value_holdings(price_fn, fx_fn)` →
per-holding `{native_value, eur_value, weight}` + `total_value_eur` → stamped on `HoldingDecision`
/ `PortfolioReview` → consumed by report renderer + strategic-posture combine.

### Error handling

- Blank/invalid quantity → `None`, debug log, holding excluded from weighting (still analyzed/rendered).
- Price or FX unavailable for a holding → its `weight=None`; it's excluded from `total_eur` (weights
  of the rest still sum to ~1.0 over priced holdings; coverage note states how many were priced).
- FX provider total failure → all weights `None`; report/posture fall back to count-based (the
  interim behavior), never crashes. Logged once at WARNING.
- `make fix-currencies`: per-ticker failure leaves that row's `Currency` unchanged + logs it; never
  corrupts the file (write to temp, atomic replace).

### Testing

- `fx_rates`: identity rate; mocked pair lookup; GBp handling; failure→None; per-run cache hit.
- `value_holdings` (pure, injected fns): full data → correct weights summing ~1.0; missing quantity →
  weight None + excluded from total; missing price/FX → weight None; empty → no crash; multi-currency
  mix → correct EUR conversion. (No network — fns injected.)
- CSV ingestion: `Quantity` parsed (valid/blank/garbage); crypto Quantity parsed.
- `fix_csv_currencies`: rewrites Currency from a mocked currency resolver; atomic; idempotent;
  preserves other columns/order; per-ticker failure leaves row intact.
- The live price/FX calls themselves are network → their direct tests `@pytest.mark.integration`.

## Affected files (reference)

- `data/stock.csv`, `data/etf.csv`, `data/crypto.csv` — add `Quantity` (+ crypto `Currency` via the fix tool).
- `src/finwiz/schemas/portfolio_processing.py` — `RawHolding.quantity`.
- `src/finwiz/schemas/portfolio_review.py` — `HoldingDecision` weight fields; `PortfolioReview.base_currency`/`total_value_eur`.
- `src/finwiz/orchestrators/portfolio_holdings_processor.py` — parse `Quantity`; invoke valuation.
- `src/finwiz/orchestrators/portfolio_review_orchestrator.py` — stamp weights/totals (where holdings are finalized).
- `src/finwiz/data/fx_rates.py` (new) — live FX→EUR.
- `src/finwiz/scoring/portfolio_valuation.py` (new) — pure valuation/weights.
- `scripts/fix_csv_currencies.py` (new) + `Makefile` `fix-currencies` target.

## Risks / open items for planning

- Confirm the existing price service exposes both **price and quote currency** per ticker (yfinance
  `fast_info.last_price` + `fast_info.currency`); if not, add a thin accessor.
- Confirm the source-prefixed ticker (`Yahoo:AAPL`) → price-API symbol normalization already done by
  `normalize_ticker`; reuse it for both price and FX-currency resolution.
- GBp (pence) vs GBP and any other minor-unit quirks (LSE `.L` often quotes GBp) — valuation must
  normalize to major units before FX.
- Decide exact insertion point where decisions are finalized so weights are stamped before report/posture.
