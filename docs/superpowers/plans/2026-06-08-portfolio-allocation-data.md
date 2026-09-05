# Portfolio Allocation Data Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give each holding a position `Quantity` from the CSV, value it in its native currency via the price API, convert to a EUR base via live FX, and surface `quantity / native_currency / native_value / eur_value / weight` on the holding model so the portfolio can be represented by allocation.

**Architecture:** A new deterministic, pure-Python valuation unit (`scoring/portfolio_valuation.py`) takes holdings + injected `price_fn`/`fx_fn` and computes per-holding EUR value and portfolio weight. A new live FX provider (`data/fx_rates.py`) resolves `<ccy>EUR` rates via yfinance with a per-run cache. The existing async `PortfolioPriceService` (already returns price **and** quote currency) supplies prices; the wiring in `build_portfolio_review` pre-fetches prices, runs `value_holdings`, and stamps weights onto `HoldingDecision`s. AI Minimalism: this is 100% Python, no AI. An explicit `make fix-currencies` rewrites the unreliable CSV `Currency` column from the authoritative price-API currency (never on a normal run).

**Tech Stack:** Python 3.12, Pydantic v2, yfinance, asyncio, pytest + pytest-mock (`mocker`), `make`.

---

## Key facts the implementer must know (verified against the codebase)

- **Price + currency already exist together.** `PortfolioPriceService.get_current_price(symbol) -> PriceData | None` and `get_current_prices(symbols) -> dict[str, PriceData]` (in `src/finwiz/tools/portfolio_price_service.py`). `PriceData` (`src/finwiz/schemas/rebalancing/core.py:106`) has `.price: float` and `.currency: str`. **No new price accessor is needed** — the spec's top open risk is resolved.
- **`get_current_prices` keys the result dict by the symbol string you pass in** (it uppercases only for the internal fetch). Pass the already-normalized ticker (e.g. `"AAPL"`, `"BTC-USD"`) and look results up by that same string.
- **Ticker normalization** lives on `PortfolioHoldingsProcessor.normalize_ticker(raw, asset_class)` (strips `YAHOO:` prefix, adds `-USD` for crypto). Tickers in `RawHolding.ticker` are already normalized by the time holdings are built.
- **Wiring point:** `build_portfolio_review` in `src/finwiz/orchestrators/portfolio_review_orchestrator.py`, after `decisions` are produced and `merge_deep_analysis_from_flow_state` runs, right before `PortfolioReview(...)` is constructed (around line 137).
- **`value_holdings` skips any holding whose `quantity is None` BEFORE calling `price_fn`.** Therefore, when no holding has a quantity (every existing unit test, and production until users fill the column), the wiring must make **zero** network calls and leave all weights `None`. This keeps the existing offline tests in `tests/unit/orchestrators/test_portfolio_review.py` green.
- **`RawHolding` is a `@dataclass`** (not Pydantic) in `src/finwiz/schemas/portfolio_processing.py`. `HoldingDecision` and `PortfolioReview` are Pydantic v2 models with `extra="forbid"` in `src/finwiz/schemas/portfolio_review.py`. Pydantic v2 allows plain attribute assignment after construction (no `validate_assignment`), so `decision.weight = ...` works once the field exists.
- **Pydantic models go in `schemas/`** (project rule). The pure valuation function goes in `scoring/`, but its result models (`HoldingValuation`, `ValuationResult`) go in `schemas/portfolio_valuation.py`.
- **unittest.mock is BANNED.** Use `mocker.patch(...)` (pytest-mock) only.
- **Async tests** in this repo are written as `async def test_...` with no decorator (pytest-asyncio auto mode is configured). Follow that style.
- **GBp (pence) quirk:** LSE tickers can report currency `"GBp"` (capital G, capital B, lowercase p) priced in pence. The FX provider maps `GBp`/`GBX` → `GBP` and divides the rate by 100, so a pence-quoted `native_value` converts to EUR correctly. The division lives **only** in `fx_rates` (single site, no double division).

## File structure

| File | Responsibility |
|------|----------------|
| `src/finwiz/schemas/portfolio_processing.py` (modify) | `RawHolding.quantity: float \| None` |
| `src/finwiz/schemas/portfolio_review.py` (modify) | `HoldingDecision` weight fields; `PortfolioReview.total_value_eur` |
| `src/finwiz/schemas/portfolio_valuation.py` (new) | `HoldingValuation`, `ValuationResult` Pydantic models |
| `src/finwiz/data/fx_rates.py` (new) | `get_fx_rate()` live FX→EUR + per-run cache + `clear_fx_cache()` |
| `src/finwiz/scoring/portfolio_valuation.py` (new) | pure `value_holdings(...)` |
| `src/finwiz/orchestrators/portfolio_holdings_processor.py` (modify) | parse `Quantity` from CSV into `RawHolding.quantity` |
| `src/finwiz/orchestrators/portfolio_review_orchestrator.py` (modify) | pre-fetch prices, run valuation, stamp weights, set `total_value_eur` |
| `scripts/fix_csv_currencies.py` (new) | pure CSV rewrite fn + `main()` wiring the live currency resolver |
| `Makefile` (modify) | `fix-currencies` target |
| `data/stock.csv`, `data/etf.csv`, `data/crypto.csv` (modify) | add empty `Quantity` column |

---

## Task 1: `RawHolding.quantity` field + CSV ingestion

**Files:**

- Modify: `src/finwiz/schemas/portfolio_processing.py:17-26`
- Modify: `src/finwiz/orchestrators/portfolio_holdings_processor.py:125-188`
- Test: `tests/unit/orchestrators/test_portfolio_holdings_processor.py` (add to existing file)

- [ ] **Step 1: Write the failing test for quantity parsing**

Add to `tests/unit/orchestrators/test_portfolio_holdings_processor.py`:

```python
class TestQuantityIngestion:
    """CSV `Quantity` column parsing into RawHolding.quantity."""

    def test_parses_valid_quantity(self, tmp_path):
        from finwiz.orchestrators.portfolio_holdings_processor import PortfolioHoldingsProcessor

        csv = tmp_path / "stock.csv"
        csv.write_text("Name,Ticker,Currency,Active,Quantity\nApple,Yahoo:AAPL,USD,true,10.5\n")
        processor = PortfolioHoldingsProcessor()

        holdings = processor._read_csv_holdings(csv, "stock")

        assert len(holdings) == 1
        assert holdings[0].quantity == 10.5

    def test_blank_quantity_is_none(self, tmp_path):
        from finwiz.orchestrators.portfolio_holdings_processor import PortfolioHoldingsProcessor

        csv = tmp_path / "stock.csv"
        csv.write_text("Name,Ticker,Currency,Active,Quantity\nApple,Yahoo:AAPL,USD,true,\n")
        processor = PortfolioHoldingsProcessor()

        holdings = processor._read_csv_holdings(csv, "stock")

        assert holdings[0].quantity is None

    def test_garbage_quantity_is_none(self, tmp_path):
        from finwiz.orchestrators.portfolio_holdings_processor import PortfolioHoldingsProcessor

        csv = tmp_path / "stock.csv"
        csv.write_text("Name,Ticker,Currency,Active,Quantity\nApple,Yahoo:AAPL,USD,true,abc\n")
        processor = PortfolioHoldingsProcessor()

        holdings = processor._read_csv_holdings(csv, "stock")

        assert holdings[0].quantity is None

    def test_missing_quantity_column_is_none(self, tmp_path):
        from finwiz.orchestrators.portfolio_holdings_processor import PortfolioHoldingsProcessor

        csv = tmp_path / "stock.csv"
        csv.write_text("Name,Ticker,Currency,Active\nApple,Yahoo:AAPL,USD,true\n")
        processor = PortfolioHoldingsProcessor()

        holdings = processor._read_csv_holdings(csv, "stock")

        assert holdings[0].quantity is None

    def test_crypto_quantity_parsed(self, tmp_path):
        from finwiz.orchestrators.portfolio_holdings_processor import PortfolioHoldingsProcessor

        csv = tmp_path / "crypto.csv"
        csv.write_text("Name,Ticker,Active,Quantity\nBitcoin,BTC,true,0.25\n")
        processor = PortfolioHoldingsProcessor()

        holdings = processor._read_csv_holdings(csv, "crypto")

        assert holdings[0].quantity == 0.25
        assert holdings[0].ticker == "BTC-USD"  # crypto normalization still applies
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/unit/orchestrators/test_portfolio_holdings_processor.py::TestQuantityIngestion -v`
Expected: FAIL — `RawHolding.__init__() got an unexpected keyword argument 'quantity'` (or `AttributeError: 'RawHolding' object has no attribute 'quantity'`).

- [ ] **Step 3: Add the `quantity` field to `RawHolding`**

In `src/finwiz/schemas/portfolio_processing.py`, change the `RawHolding` dataclass to:

```python
@dataclass
class RawHolding:
    """Raw holding data from CSV."""

    asset_class: AssetClass
    name: str
    ticker: str
    currency: str
    source_file: str
    line_number: int
    quantity: float | None = None
```

- [ ] **Step 4: Parse `Quantity` in `_read_csv_holdings`**

In `src/finwiz/orchestrators/portfolio_holdings_processor.py`, inside `_read_csv_holdings`, add a parse helper just above the class (module level, after `logger = ...`):

```python
def _parse_quantity(raw: str | None) -> float | None:
    """Parse a CSV Quantity cell into a float; blank/invalid -> None (debug-logged)."""
    s = (raw or "").strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        logger.debug("Ignoring unparseable Quantity value %r", s)
        return None
```

Then in the loop, after `active_raw = ...`, add:

```python
                    quantity = _parse_quantity(row.get("Quantity"))
```

And add `quantity=quantity` to the `RawHolding(...)` construction:

```python
                    holdings.append(
                        RawHolding(
                            asset_class=asset_class,
                            name=name or "Unknown",
                            ticker=ticker or "UNKNOWN",
                            currency=currency or "USD",
                            source_file=str(path),
                            line_number=line_num,
                            quantity=quantity,
                        )
                    )
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/unit/orchestrators/test_portfolio_holdings_processor.py::TestQuantityIngestion -v`
Expected: PASS (5 passed).

- [ ] **Step 6: Commit**

```bash
git add src/finwiz/schemas/portfolio_processing.py src/finwiz/orchestrators/portfolio_holdings_processor.py tests/unit/orchestrators/test_portfolio_holdings_processor.py
git commit -m "feat(portfolio): parse CSV Quantity into RawHolding.quantity"
```

---

## Task 2: Holding-model weight fields

**Files:**

- Modify: `src/finwiz/schemas/portfolio_review.py:134-181` (`HoldingDecision`), `:210-230` (`PortfolioReview`)
- Test: `tests/unit/schemas/test_portfolio_review_enhancements.py` (add to existing file)

- [ ] **Step 1: Write the failing test**

Add to `tests/unit/schemas/test_portfolio_review_enhancements.py`:

```python
class TestAllocationFields:
    """Allocation/valuation fields on HoldingDecision and PortfolioReview."""

    def _risk(self):
        from finwiz.schemas.common import RiskAssessmentStandardized

        return RiskAssessmentStandardized(score=2.5, level="Medium", risk_factors=[])

    def test_holding_decision_allocation_fields_default_none(self):
        from finwiz.schemas.portfolio_review import HoldingDecision

        d = HoldingDecision(
            asset_class="stock",
            name="Apple",
            ticker="AAPL",
            currency="USD",
            decision="KEEP",
            composite_score=0.8,
            grade="A",
            grade_description="Strong",
            recommended_action="hold",
            risk=self._risk(),
        )

        assert d.quantity is None
        assert d.native_currency is None
        assert d.native_value is None
        assert d.eur_value is None
        assert d.weight is None

    def test_holding_decision_allocation_fields_assignable(self):
        from finwiz.schemas.portfolio_review import HoldingDecision

        d = HoldingDecision(
            asset_class="stock",
            name="Apple",
            ticker="AAPL",
            currency="USD",
            decision="KEEP",
            composite_score=0.8,
            grade="A",
            grade_description="Strong",
            recommended_action="hold",
            risk=self._risk(),
        )
        d.quantity = 10.0
        d.native_currency = "USD"
        d.native_value = 1500.0
        d.eur_value = 1380.0
        d.weight = 0.25

        assert d.weight == 0.25

    def test_weight_must_be_between_0_and_1(self):
        import pytest
        from pydantic import ValidationError
        from finwiz.schemas.portfolio_review import HoldingDecision

        with pytest.raises(ValidationError):
            HoldingDecision(
                asset_class="stock",
                name="Apple",
                ticker="AAPL",
                currency="USD",
                decision="KEEP",
                composite_score=0.8,
                grade="A",
                grade_description="Strong",
                recommended_action="hold",
                risk=self._risk(),
                weight=1.5,
            )

    def test_portfolio_review_total_value_eur_default_none(self):
        from datetime import UTC, datetime
        from finwiz.schemas.portfolio_review import PortfolioReview

        review = PortfolioReview(as_of=datetime.now(UTC))

        assert review.total_value_eur is None
```

(`RiskAssessmentStandardized` lives in `src/finwiz/schemas/common.py`: `score: float (0..5)`, `level: Literal["Low","Medium","High","Very High"]`, `risk_factors: list[str]` — the `_risk()` helper above matches it.)

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/unit/schemas/test_portfolio_review_enhancements.py::TestAllocationFields -v`
Expected: FAIL — `extra="forbid"` rejects `quantity`/`weight`/`total_value_eur` (Pydantic `ValidationError: Extra inputs are not permitted`), or `AttributeError` on `d.quantity`.

- [ ] **Step 3: Add the fields**

In `src/finwiz/schemas/portfolio_review.py`, inside `HoldingDecision`, add after the `confidence` field (around line 181):

```python
    # Allocation/valuation (deterministic Python; see scoring/portfolio_valuation.py).
    # All optional — populated only when a CSV Quantity and live price/FX resolve.
    quantity: float | None = Field(default=None, description="Position size (units/shares) from the CSV")
    native_currency: str | None = Field(default=None, description="Authoritative quote currency from the price API")
    native_value: float | None = Field(default=None, description="quantity * native price, in native currency")
    eur_value: float | None = Field(default=None, description="native_value converted to EUR via live FX")
    weight: float | None = Field(default=None, ge=0.0, le=1.0, description="Share of total EUR portfolio value (0..1)")
```

In `PortfolioReview`, add after `holdings` (around line 215):

```python
    total_value_eur: float | None = Field(default=None, description="Sum of holdings' eur_value (priced holdings only); None when nothing could be priced")
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/unit/schemas/test_portfolio_review_enhancements.py::TestAllocationFields -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add src/finwiz/schemas/portfolio_review.py tests/unit/schemas/test_portfolio_review_enhancements.py
git commit -m "feat(portfolio): add allocation/weight fields to HoldingDecision and PortfolioReview"
```

---

## Task 3: Valuation result schemas

**Files:**

- Create: `src/finwiz/schemas/portfolio_valuation.py`
- Test: `tests/unit/schemas/test_portfolio_valuation.py`

- [ ] **Step 1: Write the failing test**

Create `tests/unit/schemas/test_portfolio_valuation.py`:

```python
"""Unit tests for portfolio valuation result schemas."""

from finwiz.schemas.portfolio_valuation import HoldingValuation, ValuationResult


def test_holding_valuation_defaults():
    hv = HoldingValuation(ticker="AAPL")

    assert hv.ticker == "AAPL"
    assert hv.quantity is None
    assert hv.native_currency is None
    assert hv.native_value is None
    assert hv.eur_value is None
    assert hv.weight is None


def test_holding_valuation_fields_mutable():
    hv = HoldingValuation(ticker="AAPL")
    hv.eur_value = 100.0
    hv.weight = 0.5

    assert hv.eur_value == 100.0
    assert hv.weight == 0.5


def test_valuation_result_defaults():
    result = ValuationResult()

    assert result.per_ticker == {}
    assert result.total_value_eur is None
    assert result.priced_count == 0
    assert result.total_count == 0
    assert result.coverage_note == ""
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/unit/schemas/test_portfolio_valuation.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'finwiz.schemas.portfolio_valuation'`.

- [ ] **Step 3: Create the schema module**

Create `src/finwiz/schemas/portfolio_valuation.py`:

```python
"""Result models for deterministic portfolio valuation.

Produced by `finwiz.scoring.portfolio_valuation.value_holdings`. Pure data —
no AI, no network. Models live here per the schemas-in-`schemas/` rule.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class HoldingValuation(BaseModel):
    """Per-holding valuation output. All money fields optional (graceful degradation)."""

    model_config = ConfigDict(extra="forbid")

    ticker: str
    quantity: float | None = None
    native_currency: str | None = None
    native_value: float | None = None
    eur_value: float | None = None
    weight: float | None = Field(default=None, ge=0.0, le=1.0)


class ValuationResult(BaseModel):
    """Portfolio-level valuation: per-ticker breakdown, total EUR, coverage."""

    model_config = ConfigDict(extra="forbid")

    per_ticker: dict[str, HoldingValuation] = Field(default_factory=dict)
    total_value_eur: float | None = None
    priced_count: int = 0
    total_count: int = 0
    coverage_note: str = ""
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/unit/schemas/test_portfolio_valuation.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add src/finwiz/schemas/portfolio_valuation.py tests/unit/schemas/test_portfolio_valuation.py
git commit -m "feat(portfolio): add HoldingValuation/ValuationResult schemas"
```

---

## Task 4: Live FX provider (`fx_rates.py`)

**Files:**

- Create: `src/finwiz/data/fx_rates.py`
- Test: `tests/unit/data/test_fx_rates.py`

The unit tests patch the internal `_fetch_pair_rate` (the only network site) so no network is hit. The real `_fetch_pair_rate` is exercised by a separate `@pytest.mark.integration` test.

- [ ] **Step 1: Write the failing unit tests**

Create `tests/unit/data/test_fx_rates.py`:

```python
"""Unit tests for the live FX provider (network mocked)."""

import pytest

from finwiz.data import fx_rates


@pytest.fixture(autouse=True)
def _reset_fx_cache():
    """Each test starts with an empty per-run FX cache."""
    fx_rates.clear_fx_cache()
    yield
    fx_rates.clear_fx_cache()


def test_identity_rate_is_one_without_network(mocker):
    spy = mocker.patch("finwiz.data.fx_rates._fetch_pair_rate")

    assert fx_rates.get_fx_rate("EUR", "EUR") == 1.0
    spy.assert_not_called()


def test_simple_pair_lookup(mocker):
    mocker.patch("finwiz.data.fx_rates._fetch_pair_rate", return_value=0.92)

    assert fx_rates.get_fx_rate("CHF", "EUR") == 0.92


def test_gbp_pence_divided_by_100(mocker):
    # GBPEUR is ~1.17; a GBp (pence) amount must convert at rate/100.
    mocker.patch("finwiz.data.fx_rates._fetch_pair_rate", return_value=1.17)

    rate = fx_rates.get_fx_rate("GBp", "EUR")

    assert rate == pytest.approx(0.0117)


def test_failure_returns_none(mocker):
    mocker.patch("finwiz.data.fx_rates._fetch_pair_rate", return_value=None)

    assert fx_rates.get_fx_rate("CHF", "EUR") is None


def test_per_run_cache_hits_once(mocker):
    spy = mocker.patch("finwiz.data.fx_rates._fetch_pair_rate", return_value=0.92)

    fx_rates.get_fx_rate("CHF", "EUR")
    fx_rates.get_fx_rate("CHF", "EUR")

    spy.assert_called_once()


def test_blank_currency_returns_none(mocker):
    spy = mocker.patch("finwiz.data.fx_rates._fetch_pair_rate")

    assert fx_rates.get_fx_rate("", "EUR") is None
    spy.assert_not_called()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/unit/data/test_fx_rates.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'finwiz.data.fx_rates'`.

- [ ] **Step 3: Create the FX provider**

Create `src/finwiz/data/fx_rates.py`:

```python
"""Live FX rate provider (yfinance), EUR-based, with a per-run cache.

Best-effort: any failure yields `None` and the caller treats the affected
weight as unknown. Pure deterministic glue around a network call (AI Minimalism).
"""

from __future__ import annotations

import logging

import yfinance as yf  # yfinance has no official type stubs

logger = logging.getLogger(__name__)

# Sub-unit (minor) currency codes -> (major ISO code, divisor).
# e.g. LSE quotes "GBp" (pence); 100 pence = 1 GBP.
_MINOR_UNITS: dict[str, tuple[str, float]] = {
    "GBp": ("GBP", 100.0),
    "GBX": ("GBP", 100.0),
    "ZAc": ("ZAR", 100.0),
    "ILA": ("ILS", 100.0),
}

# Per-run cache keyed by (from_ccy, base) -> rate or None. Reset via clear_fx_cache().
_FX_CACHE: dict[tuple[str, str], float | None] = {}


def clear_fx_cache() -> None:
    """Clear the per-run FX cache (used by tests and between flow runs)."""
    _FX_CACHE.clear()


def _fetch_pair_rate(from_ccy: str, base: str) -> float | None:
    """Fetch the spot rate for `<from_ccy><base>=X` from yfinance. Network site."""
    pair = f"{from_ccy}{base}=X"
    try:
        ticker = yf.Ticker(pair)
        # Primary: fast_info last price.
        try:
            rate = ticker.fast_info["lastPrice"]
        except Exception:
            rate = getattr(ticker.fast_info, "last_price", None)
        if rate and float(rate) > 0:
            return float(rate)

        # Fallback: 1-day history close.
        hist = ticker.history(period="1d")
        if not hist.empty and "Close" in hist.columns:
            close = float(hist["Close"].iloc[-1])
            if close > 0:
                return close
    except Exception as exc:  # best-effort
        logger.warning("FX lookup failed for %s: %s", pair, exc)
    return None


def get_fx_rate(from_ccy: str, base: str = "EUR") -> float | None:
    """Return the rate to multiply a `from_ccy` amount by to get `base`.

    Identity (1.0) when currencies match. Minor units (GBp/GBX/ZAc/ILA) are
    mapped to their major unit and the rate divided by 100. Best-effort: any
    failure returns None. Results (including None) are cached per run.
    """
    raw = (from_ccy or "").strip()
    base_ccy = (base or "EUR").strip().upper()
    if not raw or not base_ccy:
        return None

    cache_key = (raw, base_ccy)
    if cache_key in _FX_CACHE:
        return _FX_CACHE[cache_key]

    major, divisor = _MINOR_UNITS.get(raw, (raw.upper(), 1.0))

    if major == base_ccy:
        result: float | None = 1.0 / divisor
    else:
        pair_rate = _fetch_pair_rate(major, base_ccy)
        result = None if pair_rate is None else pair_rate / divisor

    _FX_CACHE[cache_key] = result
    return result
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/unit/data/test_fx_rates.py -v`
Expected: PASS (6 passed).

- [ ] **Step 5: Add the live integration test**

Create `tests/integration/test_fx_rates_live.py` (create the file; the `integration` marker is already registered in `pyproject.toml`/`pytest.ini`):

```python
"""Live network test for the FX provider. Excluded from default `make test`."""

import pytest

from finwiz.data import fx_rates


@pytest.mark.integration
def test_live_chf_eur_rate_is_plausible():
    fx_rates.clear_fx_cache()
    rate = fx_rates.get_fx_rate("CHF", "EUR")

    assert rate is not None
    assert 0.5 < rate < 2.0  # sanity band, not a precise assertion
```

- [ ] **Step 6: Verify the integration test is excluded from the default run, then runs on demand**

Run: `uv run pytest tests/unit/data/test_fx_rates.py tests/integration/test_fx_rates_live.py -v -m "not integration"`
Expected: the live test is deselected; unit tests PASS.

(Optional, requires network) Run: `uv run pytest tests/integration/test_fx_rates_live.py -v -m integration`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/finwiz/data/fx_rates.py tests/unit/data/test_fx_rates.py tests/integration/test_fx_rates_live.py
git commit -m "feat(portfolio): add live yfinance FX->EUR provider with per-run cache"
```

---

## Task 5: Pure `value_holdings`

**Files:**

- Create: `src/finwiz/scoring/portfolio_valuation.py`
- Test: `tests/unit/scoring/test_portfolio_valuation.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/scoring/test_portfolio_valuation.py`:

```python
"""Unit tests for pure portfolio valuation (price_fn / fx_fn injected, no network)."""

from dataclasses import dataclass

import pytest

from finwiz.scoring.portfolio_valuation import value_holdings


@dataclass
class _H:
    """Minimal holding stand-in (matches the .ticker/.quantity attributes used)."""

    ticker: str
    quantity: float | None


def test_full_data_weights_sum_to_one():
    holdings = [_H("AAPL", 10.0), _H("MSFT", 5.0)]
    prices = {"AAPL": (100.0, "EUR"), "MSFT": (200.0, "EUR")}

    result = value_holdings(
        holdings,
        base="EUR",
        price_fn=lambda t: prices.get(t),
        fx_fn=lambda c: 1.0,
    )

    # AAPL: 1000 EUR, MSFT: 1000 EUR -> total 2000, each weight 0.5
    assert result.total_value_eur == pytest.approx(2000.0)
    assert result.per_ticker["AAPL"].eur_value == pytest.approx(1000.0)
    assert result.per_ticker["AAPL"].weight == pytest.approx(0.5)
    assert result.per_ticker["MSFT"].weight == pytest.approx(0.5)
    total_weight = sum(hv.weight for hv in result.per_ticker.values() if hv.weight is not None)
    assert total_weight == pytest.approx(1.0)


def test_multi_currency_conversion():
    holdings = [_H("AAPL", 10.0), _H("NESN", 10.0)]
    prices = {"AAPL": (100.0, "USD"), "NESN": (100.0, "CHF")}
    fx = {"USD": 0.9, "CHF": 1.0}

    result = value_holdings(
        holdings,
        base="EUR",
        price_fn=lambda t: prices.get(t),
        fx_fn=lambda c: fx.get(c),
    )

    # AAPL: 10*100*0.9 = 900 EUR; NESN: 10*100*1.0 = 1000 EUR; total 1900
    assert result.per_ticker["AAPL"].eur_value == pytest.approx(900.0)
    assert result.per_ticker["NESN"].eur_value == pytest.approx(1000.0)
    assert result.total_value_eur == pytest.approx(1900.0)
    assert result.per_ticker["AAPL"].weight == pytest.approx(900.0 / 1900.0)


def test_missing_quantity_excluded_and_no_price_call():
    calls = []

    def price_fn(t):
        calls.append(t)
        return (100.0, "EUR")

    holdings = [_H("AAPL", None), _H("MSFT", 5.0)]

    result = value_holdings(holdings, base="EUR", price_fn=price_fn, fx_fn=lambda c: 1.0)

    assert result.per_ticker["AAPL"].weight is None
    assert result.per_ticker["AAPL"].eur_value is None
    assert "AAPL" not in calls  # price_fn NOT called for quantity-less holding
    assert result.per_ticker["MSFT"].weight == pytest.approx(1.0)
    assert result.priced_count == 1
    assert result.total_count == 2


def test_missing_price_yields_none_weight():
    holdings = [_H("AAPL", 10.0), _H("MSFT", 5.0)]
    prices = {"MSFT": (200.0, "EUR")}  # AAPL price unavailable

    result = value_holdings(
        holdings,
        base="EUR",
        price_fn=lambda t: prices.get(t),
        fx_fn=lambda c: 1.0,
    )

    assert result.per_ticker["AAPL"].weight is None
    assert result.per_ticker["AAPL"].native_value is None
    assert result.per_ticker["MSFT"].weight == pytest.approx(1.0)


def test_missing_fx_keeps_native_value_but_none_weight():
    holdings = [_H("NESN", 10.0)]
    prices = {"NESN": (100.0, "CHF")}

    result = value_holdings(
        holdings,
        base="EUR",
        price_fn=lambda t: prices.get(t),
        fx_fn=lambda c: None,  # FX unavailable
    )

    hv = result.per_ticker["NESN"]
    assert hv.native_value == pytest.approx(1000.0)  # surfaced
    assert hv.native_currency == "CHF"
    assert hv.eur_value is None
    assert hv.weight is None
    assert result.total_value_eur is None  # nothing priced into EUR


def test_empty_holdings_no_crash():
    result = value_holdings([], base="EUR", price_fn=lambda t: None, fx_fn=lambda c: 1.0)

    assert result.per_ticker == {}
    assert result.total_value_eur is None
    assert result.total_count == 0


def test_coverage_note_reports_counts():
    holdings = [_H("AAPL", 10.0), _H("MSFT", None)]
    prices = {"AAPL": (100.0, "EUR")}

    result = value_holdings(
        holdings,
        base="EUR",
        price_fn=lambda t: prices.get(t),
        fx_fn=lambda c: 1.0,
    )

    assert "1 of 2" in result.coverage_note
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/unit/scoring/test_portfolio_valuation.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'finwiz.scoring.portfolio_valuation'`.

- [ ] **Step 3: Implement `value_holdings`**

Create `src/finwiz/scoring/portfolio_valuation.py`:

```python
"""Pure deterministic portfolio valuation: quantities + price/FX -> EUR weights.

No AI, no network — `price_fn` and `fx_fn` are injected for testability and are
the only I/O boundaries. AI Minimalism: when Python can compute it, Python does.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Protocol

from finwiz.schemas.portfolio_valuation import HoldingValuation, ValuationResult

# price_fn(ticker) -> (price, native_currency) or None when unavailable.
PriceFn = Callable[[str], tuple[float, str] | None]
# fx_fn(native_currency) -> rate to multiply by for the base currency, or None.
FxFn = Callable[[str], float | None]


class _HasTickerQuantity(Protocol):
    ticker: str
    quantity: float | None


def value_holdings(
    holdings: Iterable[_HasTickerQuantity],
    *,
    base: str = "EUR",
    price_fn: PriceFn,
    fx_fn: FxFn,
) -> ValuationResult:
    """Value each holding and compute portfolio weights.

    For each holding WITH a quantity: resolve (price, native_ccy) via price_fn,
    compute native_value = quantity * price, convert to base via fx_fn(native_ccy).
    Holdings missing quantity/price/FX get weight=None and are excluded from the
    base total. Weights are eur_value / total over the holdings that fully resolved.
    """
    per_ticker: dict[str, HoldingValuation] = {}
    total = 0.0
    priced = 0
    total_count = 0

    for holding in holdings:
        total_count += 1
        ticker = holding.ticker
        quantity = holding.quantity
        hv = HoldingValuation(ticker=ticker, quantity=quantity)
        per_ticker[ticker] = hv

        if quantity is None:
            continue

        priced_pair = price_fn(ticker)
        if priced_pair is None:
            continue

        price, native_ccy = priced_pair
        hv.native_currency = native_ccy
        hv.native_value = quantity * price

        rate = fx_fn(native_ccy)
        if rate is None:
            continue

        hv.eur_value = hv.native_value * rate
        total += hv.eur_value
        priced += 1

    total_eur = total if priced > 0 else None
    if total_eur and total_eur > 0:
        for hv in per_ticker.values():
            if hv.eur_value is not None:
                hv.weight = hv.eur_value / total_eur

    pct = (priced / total_count * 100.0) if total_count else 0.0
    note = f"{priced} of {total_count} holdings priced; {pct:.0f}% of holdings by count weighted"

    return ValuationResult(
        per_ticker=per_ticker,
        total_value_eur=total_eur,
        priced_count=priced,
        total_count=total_count,
        coverage_note=note,
    )
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/unit/scoring/test_portfolio_valuation.py -v`
Expected: PASS (7 passed).

- [ ] **Step 5: Commit**

```bash
git add src/finwiz/scoring/portfolio_valuation.py tests/unit/scoring/test_portfolio_valuation.py
git commit -m "feat(portfolio): pure value_holdings (quantity+price+FX -> EUR weights)"
```

---

## Task 6: Wire valuation into `build_portfolio_review`

**Files:**

- Modify: `src/finwiz/orchestrators/portfolio_review_orchestrator.py:80-143`
- Test: `tests/unit/orchestrators/test_portfolio_review.py` (add to existing file)

- [ ] **Step 1: Write the failing test**

Add to `tests/unit/orchestrators/test_portfolio_review.py`:

```python
class TestAllocationWiring:
    """build_portfolio_review stamps weights and total_value_eur when quantities exist."""

    async def test_weights_stamped_from_quantities(self, tmp_path, mocker):
        from finwiz.orchestrators.portfolio_review_orchestrator import build_portfolio_review

        stock_csv = tmp_path / "stock.csv"
        stock_csv.write_text("Name,Ticker,Currency,Active,Quantity\nApple,AAPL,USD,true,10\nMicrosoft,MSFT,USD,true,10\n")

        mock_validator = mocker.patch("finwiz.orchestrators.portfolio_holdings_processor.TickerExistenceValidationTool")
        mock_validator.return_value._run.return_value = {"valid": True, "meta": {"source": "yahoo"}}

        # Mock the price service so no network is hit.
        from finwiz.schemas.rebalancing.core import PriceData

        async def fake_get_current_prices(symbols):
            return {s: PriceData(symbol=s, price=100.0, currency="EUR") for s in symbols}

        price_service = mocker.patch("finwiz.orchestrators.portfolio_review_orchestrator.PortfolioPriceService")
        price_service.return_value.get_current_prices = fake_get_current_prices

        # Mock FX (EUR identity) — guard against any accidental network.
        mocker.patch("finwiz.orchestrators.portfolio_review_orchestrator.get_fx_rate", return_value=1.0)

        review, _summary = await build_portfolio_review(stock_csv=stock_csv)

        weights = {h.ticker: h.weight for h in review.holdings}
        assert weights["AAPL"] == pytest.approx(0.5)
        assert weights["MSFT"] == pytest.approx(0.5)
        assert review.total_value_eur == pytest.approx(2000.0)
        aapl = next(h for h in review.holdings if h.ticker == "AAPL")
        assert aapl.quantity == 10.0
        assert aapl.eur_value == pytest.approx(1000.0)

    async def test_no_quantities_means_no_price_fetch_and_none_weights(self, tmp_path, mocker):
        from finwiz.orchestrators.portfolio_review_orchestrator import build_portfolio_review

        stock_csv = tmp_path / "stock.csv"
        stock_csv.write_text("Name,Ticker,Currency,Active\nApple,AAPL,USD,true\n")

        mock_validator = mocker.patch("finwiz.orchestrators.portfolio_holdings_processor.TickerExistenceValidationTool")
        mock_validator.return_value._run.return_value = {"valid": True, "meta": {"source": "yahoo"}}

        price_service = mocker.patch("finwiz.orchestrators.portfolio_review_orchestrator.PortfolioPriceService")

        review, _summary = await build_portfolio_review(stock_csv=stock_csv)

        # No quantity anywhere -> the price service is never constructed.
        price_service.assert_not_called()
        assert review.holdings[0].weight is None
        assert review.total_value_eur is None

    async def test_valuation_failure_is_graceful(self, tmp_path, mocker):
        from finwiz.orchestrators.portfolio_review_orchestrator import build_portfolio_review

        stock_csv = tmp_path / "stock.csv"
        stock_csv.write_text("Name,Ticker,Currency,Active,Quantity\nApple,AAPL,USD,true,10\n")

        mock_validator = mocker.patch("finwiz.orchestrators.portfolio_holdings_processor.TickerExistenceValidationTool")
        mock_validator.return_value._run.return_value = {"valid": True, "meta": {"source": "yahoo"}}

        # Price service blows up -> review must still be produced, weights None.
        price_service = mocker.patch("finwiz.orchestrators.portfolio_review_orchestrator.PortfolioPriceService")
        price_service.return_value.get_current_prices = mocker.AsyncMock(side_effect=RuntimeError("boom"))

        review, _summary = await build_portfolio_review(stock_csv=stock_csv)

        assert len(review.holdings) == 1
        assert review.holdings[0].weight is None
        assert review.total_value_eur is None
```

Add `import pytest` at the top of the test file if not already present.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/unit/orchestrators/test_portfolio_review.py::TestAllocationWiring -v`
Expected: FAIL — `AttributeError`/`ImportError`: `PortfolioPriceService` / `get_fx_rate` are not yet imported into `portfolio_review_orchestrator`, and weights are not stamped.

- [ ] **Step 3: Implement the wiring**

In `src/finwiz/orchestrators/portfolio_review_orchestrator.py`, add imports near the top (after the existing `from finwiz.schemas.portfolio_review import PortfolioReview`):

```python
from finwiz.data.fx_rates import get_fx_rate
from finwiz.schemas.portfolio_processing import RawHolding
from finwiz.schemas.portfolio_valuation import ValuationResult
from finwiz.scoring.portfolio_valuation import value_holdings
from finwiz.tools.portfolio_price_service import PortfolioPriceService
```

Add a private helper above `build_portfolio_review`:

```python
async def _value_portfolio(raw_holdings: list[RawHolding]) -> ValuationResult | None:
    """Pre-fetch prices and compute EUR weights. Best-effort: None on any failure.

    Short-circuits (no price service, no network) when no holding has a quantity.
    """
    tickers = list({h.ticker for h in raw_holdings if h.quantity is not None})
    if not tickers:
        return None

    try:
        service = PortfolioPriceService()
        prices = await service.get_current_prices(tickers)

        def price_fn(ticker: str) -> tuple[float, str] | None:
            pd = prices.get(ticker)
            if pd is None:
                return None
            return (pd.price, pd.currency)

        return value_holdings(
            raw_holdings,
            base="EUR",
            price_fn=price_fn,
            fx_fn=get_fx_rate,
        )
    except Exception as exc:  # never break the review over valuation
        logger.warning("Portfolio valuation failed; weights unavailable this run: %s", exc)
        return None
```

In `build_portfolio_review`, replace the block from the `if flow_state is not None:` merge through the `review = PortfolioReview(...)` construction (currently lines ~133-141) with:

```python
    if flow_state is not None:
        logger.info("Merging deep analysis data from Flow state")
        decisions = merge_deep_analysis_from_flow_state(decisions, flow_state)

    total_value_eur: float | None = None
    valuation = await _value_portfolio(raw_holdings)
    if valuation is not None:
        total_value_eur = valuation.total_value_eur
        for decision in decisions:
            hv = valuation.per_ticker.get(decision.ticker)
            if hv is None:
                continue
            decision.quantity = hv.quantity
            decision.native_currency = hv.native_currency
            decision.native_value = hv.native_value
            decision.eur_value = hv.eur_value
            decision.weight = hv.weight
        logger.info("Valuation coverage: %s", valuation.coverage_note)

    review = PortfolioReview(
        as_of=datetime.now(UTC),
        base_currency=base_currency,
        holdings=decisions,
        total_value_eur=total_value_eur,
    )

    return review, summary
```

Note: `raw_holdings` is already in scope in `build_portfolio_review` (assigned from `processor.load_all_holdings(...)`).

- [ ] **Step 4: Run the new tests to verify they pass**

Run: `uv run pytest tests/unit/orchestrators/test_portfolio_review.py::TestAllocationWiring -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Run the FULL existing review + processor suites to confirm no regression**

Run: `uv run pytest tests/unit/orchestrators/test_portfolio_review.py tests/unit/orchestrators/test_portfolio_holdings_processor.py -v`
Expected: PASS (all existing tests still green — the quantity-less CSVs in the old tests trigger the short-circuit, so no price service is constructed).

- [ ] **Step 6: Commit**

```bash
git add src/finwiz/orchestrators/portfolio_review_orchestrator.py tests/unit/orchestrators/test_portfolio_review.py
git commit -m "feat(portfolio): stamp EUR weights and total_value_eur in build_portfolio_review"
```

---

## Task 7: `make fix-currencies` (CSV Currency rewrite tool)

**Files:**

- Create: `scripts/fix_csv_currencies.py`
- Modify: `Makefile` (add `fix-currencies` target + `.PHONY`)
- Test: `tests/unit/scripts/test_fix_csv_currencies.py`

The core rewrite is a pure function taking an injected `resolve_currency_fn`, so tests need no network. `main()` wires the real resolver (price API).

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/scripts/test_fix_csv_currencies.py`:

```python
"""Unit tests for the fix-currencies CSV rewrite tool (resolver injected)."""

import csv

from scripts.fix_csv_currencies import rewrite_csv_currencies


def _rows(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_rewrites_currency_from_resolver(tmp_path):
    csv_path = tmp_path / "etf.csv"
    csv_path.write_text("Name,Ticker,Currency,Active\nAmundi EM,Yahoo:AEEM.PA,USD,true\nUBS Gold,Yahoo:AUUSI.SW,USD,true\n")

    def resolver(ticker):
        return {"AEEM.PA": "EUR", "AUUSI.SW": "CHF"}.get(ticker)

    changes = rewrite_csv_currencies(csv_path, resolver)

    rows = _rows(csv_path)
    assert rows[0]["Currency"] == "EUR"
    assert rows[1]["Currency"] == "CHF"
    assert ("AEEM.PA", "USD", "EUR") in changes


def test_preserves_other_columns_and_order(tmp_path):
    csv_path = tmp_path / "stock.csv"
    csv_path.write_text("Name,Ticker,Currency,Active\nApple,Yahoo:AAPL,USD,true\nNestle,Yahoo:NESN.SW,USD,true\n")

    def resolver(ticker):
        return {"AAPL": "USD", "NESN.SW": "CHF"}.get(ticker)

    rewrite_csv_currencies(csv_path, resolver)

    rows = _rows(csv_path)
    assert [r["Ticker"] for r in rows] == ["Yahoo:AAPL", "Yahoo:NESN.SW"]
    assert rows[0]["Active"] == "true"
    assert list(rows[0].keys()) == ["Name", "Ticker", "Currency", "Active"]


def test_adds_currency_column_to_crypto(tmp_path):
    csv_path = tmp_path / "crypto.csv"
    csv_path.write_text("Name,Ticker,Active\nBitcoin,BTC,true\n")

    def resolver(ticker):
        return "USD"

    rewrite_csv_currencies(csv_path, resolver)

    rows = _rows(csv_path)
    assert "Currency" in rows[0]
    assert rows[0]["Currency"] == "USD"


def test_per_ticker_failure_leaves_row_unchanged(tmp_path):
    csv_path = tmp_path / "stock.csv"
    csv_path.write_text("Name,Ticker,Currency,Active\nApple,Yahoo:AAPL,USD,true\nBroken,Yahoo:BAD,EUR,true\n")

    def resolver(ticker):
        return "CHF" if ticker == "AAPL" else None  # BAD unresolved

    rewrite_csv_currencies(csv_path, resolver)

    rows = _rows(csv_path)
    assert rows[0]["Currency"] == "CHF"
    assert rows[1]["Currency"] == "EUR"  # untouched


def test_idempotent(tmp_path):
    csv_path = tmp_path / "stock.csv"
    csv_path.write_text("Name,Ticker,Currency,Active\nApple,Yahoo:AAPL,USD,true\n")

    def resolver(ticker):
        return "EUR"

    first = rewrite_csv_currencies(csv_path, resolver)
    second = rewrite_csv_currencies(csv_path, resolver)

    assert first == [("AAPL", "USD", "EUR")]
    assert second == []  # nothing changed the second time
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/unit/scripts/test_fix_csv_currencies.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.fix_csv_currencies'`.

- [ ] **Step 3: Implement the tool**

Create `scripts/fix_csv_currencies.py`:

```python
"""Rewrite the `Currency` column of the portfolio CSVs from the authoritative
price-API currency. Run explicitly via `make fix-currencies` — never on a normal
analysis run. Atomic per file (temp + replace); per-ticker failures leave the row
untouched.
"""

from __future__ import annotations

import asyncio
import csv
import logging
import os
import sys
from collections.abc import Callable
from pathlib import Path
from tempfile import NamedTemporaryFile

logger = logging.getLogger(__name__)

# resolver(normalized_ticker) -> ISO currency code, or None when unresolved.
CurrencyResolver = Callable[[str], str | None]

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_CSV_FILES = [
    _PROJECT_ROOT / "data" / "stock.csv",
    _PROJECT_ROOT / "data" / "etf.csv",
    _PROJECT_ROOT / "data" / "crypto.csv",
]


def _normalize_ticker(raw: str, asset_class: str) -> str:
    """Strip the source prefix (and add -USD for crypto) for price-API lookup."""
    from finwiz.orchestrators.portfolio_holdings_processor import PortfolioHoldingsProcessor

    return PortfolioHoldingsProcessor().normalize_ticker(raw, asset_class=asset_class)  # type: ignore[arg-type]


def rewrite_csv_currencies(
    path: Path,
    resolve_currency_fn: CurrencyResolver,
) -> list[tuple[str, str, str]]:
    """Rewrite `path`'s Currency column using the resolver.

    Returns a list of (normalized_ticker, old_currency, new_currency) for rows
    that changed. Adds a `Currency` column if absent (e.g. crypto.csv). Atomic.
    """
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    asset_class = "crypto" if path.stem == "crypto" else ("etf" if path.stem == "etf" else "stock")
    has_currency = "Currency" in fieldnames
    if not has_currency:
        # Insert Currency right after Ticker if present, else append.
        insert_at = fieldnames.index("Ticker") + 1 if "Ticker" in fieldnames else len(fieldnames)
        fieldnames.insert(insert_at, "Currency")

    changes: list[tuple[str, str, str]] = []
    for row in rows:
        raw_ticker = (row.get("Ticker") or "").strip()
        if not raw_ticker:
            row.setdefault("Currency", row.get("Currency", ""))
            continue
        norm = _normalize_ticker(raw_ticker, asset_class)
        old = (row.get("Currency") or "").strip()
        new = resolve_currency_fn(norm)
        if new is None:
            logger.warning("Could not resolve currency for %s; leaving %r", norm, old)
            row["Currency"] = old
            continue
        if new != old:
            changes.append((norm, old, new))
        row["Currency"] = new

    # Atomic write: temp file in the same dir, then replace.
    with NamedTemporaryFile("w", newline="", encoding="utf-8", dir=path.parent, delete=False) as tmp:
        writer = csv.DictWriter(tmp, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, path)

    return changes


def _build_live_resolver() -> CurrencyResolver:
    """Resolver backed by the live price API (network)."""
    from finwiz.tools.portfolio_price_service import PortfolioPriceService

    service = PortfolioPriceService()

    def resolve(norm_ticker: str) -> str | None:
        try:
            price_data = asyncio.run(service.get_current_price(norm_ticker))
        except Exception as exc:
            logger.warning("Price lookup failed for %s: %s", norm_ticker, exc)
            return None
        return price_data.currency if price_data is not None else None

    return resolve


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    resolver = _build_live_resolver()
    for csv_path in _CSV_FILES:
        if not csv_path.exists():
            logger.info("skip (missing): %s", csv_path)
            continue
        changes = rewrite_csv_currencies(csv_path, resolver)
        if changes:
            logger.info("%s: %d currency change(s)", csv_path.name, len(changes))
            for ticker, old, new in changes:
                logger.info("  %-14s %s -> %s", ticker, old or "(none)", new)
        else:
            logger.info("%s: no changes", csv_path.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/unit/scripts/test_fix_csv_currencies.py -v`
Expected: PASS (5 passed).

- [ ] **Step 5: Add the Makefile target**

In `Makefile`, add `fix-currencies` to the `.PHONY` line (line 3) and add this target (place it near the other data/utility targets, e.g. after `cleanup:`):

```makefile
fix-currencies:  ## Rewrite data/*.csv Currency columns from the authoritative price API (network; explicit)
 uv run python scripts/fix_csv_currencies.py
```

- [ ] **Step 6: Verify the target is wired (dry check — no network needed for `make -n`)**

Run: `make -n fix-currencies`
Expected: prints `uv run python scripts/fix_csv_currencies.py`.

- [ ] **Step 7: Commit**

```bash
git add scripts/fix_csv_currencies.py tests/unit/scripts/test_fix_csv_currencies.py Makefile
git commit -m "feat(portfolio): add 'make fix-currencies' CSV currency rewrite tool"
```

---

## Task 8: Add the `Quantity` column to the data CSVs

This is the operational enablement step. We add an empty `Quantity` column to each CSV (blank = no position size yet; the pipeline stays inert/graceful until a user fills values). We do **not** invent position sizes.

**Files:**

- Modify: `data/stock.csv`, `data/etf.csv`, `data/crypto.csv`

- [ ] **Step 1: Add an empty `Quantity` column to all three CSVs**

Run this exact script (appends a `Quantity` header and an empty trailing cell to each data row, preserving all existing columns and row order):

```bash
uv run python - <<'PY'
import csv
from pathlib import Path

for name in ("data/stock.csv", "data/etf.csv", "data/crypto.csv"):
    path = Path(name)
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)
    if "Quantity" in fieldnames:
        print(f"{name}: already has Quantity, skipping")
        continue
    fieldnames.append("Quantity")
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            row["Quantity"] = ""
            writer.writerow(row)
    print(f"{name}: added empty Quantity column ({len(rows)} rows)")
PY
```

Expected output: three lines confirming the column was added with the row counts.

- [ ] **Step 2: Verify the headers**

Run: `head -1 data/stock.csv data/etf.csv data/crypto.csv`
Expected: each header now ends with `,Quantity` (e.g. `Name,Ticker,Currency,Active,Quantity`; crypto: `Name,Ticker,Active,Quantity`).

- [ ] **Step 3: Verify ingestion still parses cleanly (no crash, quantities are None)**

Run: `uv run pytest tests/unit/orchestrators/test_portfolio_holdings_processor.py -v`
Expected: PASS — blank quantities parse to `None`, no regressions.

- [ ] **Step 4: Commit**

```bash
git add data/stock.csv data/etf.csv data/crypto.csv
git commit -m "chore(data): add empty Quantity column to portfolio CSVs"
```

---

## Task 9: Full-suite verification + quality gates

- [ ] **Step 1: Run the full default unit test suite**

Run: `make test`
Expected: PASS, no new failures. (Integration tests, including the live FX test, are excluded by the default `-m "not integration"`.)

- [ ] **Step 2: Lint + format**

Run: `make lint`
Expected: ruff check + format clean (auto-fixes applied; re-run if it reports fixes).

- [ ] **Step 3: Type check the touched modules**

Run: `uv run mypy src/finwiz/data/fx_rates.py src/finwiz/scoring/portfolio_valuation.py src/finwiz/schemas/portfolio_valuation.py src/finwiz/orchestrators/portfolio_review_orchestrator.py src/finwiz/orchestrators/portfolio_holdings_processor.py`
Expected: no errors. (yfinance is untyped; the `# yfinance has no official type stubs` comment mirrors the existing convention in `portfolio_price_service.py`.)

- [ ] **Step 4: unittest.mock ban check**

Run: `make check-unittest-mock`
Expected: PASS — all new tests use `mocker` (pytest-mock), zero `unittest.mock` imports.

- [ ] **Step 5: Commit any lint/format fixups**

```bash
git add -A
git commit -m "chore(portfolio): lint/format/type fixups for allocation data" || echo "nothing to commit"
```

---

## Self-review notes (traceability to the spec)

- **Quantity from CSV → `RawHolding.quantity`:** Task 1.
- **Native value + EUR conversion + weight on the holding model:** Tasks 2, 5, 6.
- **Surface `quantity / native_currency / native_value / eur_value / weight`:** Task 2 (model) + Task 6 (stamping).
- **`make fix-currencies` (explicit, atomic, idempotent, adds crypto Currency):** Task 7.
- **Graceful degradation (missing quantity/price/FX → weight None; never crashes; total over priced holdings):** Tasks 5 (pure logic) + 6 (`_value_portfolio` try/except + short-circuit).
- **FX live via yfinance pairs, per-run cache, GBp/100:** Task 4.
- **`PortfolioReview.total_value_eur` for the report header:** Tasks 2 + 6.
- **Network calls isolated to `@pytest.mark.integration`:** Task 4 Step 5 (FX) + Task 7 keeps the network in `_build_live_resolver` (untested) while the pure rewrite is unit-tested.

**Deliberate scope decision (flag for reviewer):** `PortfolioReview.base_currency` keeps its existing default (`"CHF"`) and is **not** changed to `"EUR"`. The spec's narrative says "base currency EUR", but the *weight* is a dimensionless ratio and `total_value_eur` already carries the EUR total explicitly, so changing the long-standing `base_currency` default is unnecessary and risks regressions elsewhere. The valuation is hard-coded to EUR internally. If the report header must literally display "EUR", that is a one-line follow-up in the report renderer (out of scope here, consistent with the spec's "Non-goals: changing the report-posture plan").

**Consumption by the strategic-posture combine** (the prerequisite-of relationship in the spec header) is explicitly out of scope for this plan — it is the small follow-up edit to the report-posture plan's B2/B4, as the spec states.

```
