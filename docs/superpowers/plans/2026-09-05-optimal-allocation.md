# Optimal Allocation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A new Phase 3.7 computes minimum-variance target weights for the portfolio through pypfopt, and the family report shows current allocation against the optimal one.

**Architecture:** A pure domain optimiser (DataFrame in, weights out) sits behind an orchestrator that assembles the price matrix from flow state and the warm `HistoricalDataManager` cache. The flow phase stores a typed result in state; the reporting layer only renders it. Phase 3.5 (stress testing) is the structural precedent throughout — same guard, same local import, same fail-soft.

**Tech Stack:** pypfopt 1.6.0 (`EfficientFrontier`, `CovarianceShrinkage`), cvxpy 1.9.2, pandas, Pydantic v2, pytest + pytest-mock.

**Spec:** `docs/superpowers/specs/2026-09-05-optimal-allocation-design.md`

## Global Constraints

- **unittest.mock is BANNED.** Use pytest-mock (`mocker.patch`) only. Enforced by ruff and `make check-unittest-mock`.
- **All Pydantic models live in `schemas/`**, never in domain folders.
- **Line length 180** (ruff config).
- **No network in tests.** pytest-socket blocks it; mock the seam, never widen the allow-list.
- **Report copy is French.** Section headings, labels and notes follow the existing sections' tone.
- **Flow methods return `dict[str, Any]`.**
- **Per-position cap default 0.08; per-class cap default = current class weight + 0.10.** Both configurable.
- **Minimum 120 aligned observations** for a holding to be eligible.
- **`clean_weights()` takes no argument** — call the objective first, then `clean_weights()`.
- Run `make check` before every commit that touches `src/`.

## File Structure

| File | Responsibility |
|---|---|
| `src/finwiz/schemas/portfolio_optimization.py` (new) | `HoldingTarget`, `ExcludedHolding`, `OptimalAllocation` |
| `src/finwiz/quantitative/price_matrix.py` (new) | calendar alignment: many price series → one aligned DataFrame + exclusion reasons |
| `src/finwiz/quantitative/allocation_optimizer.py` (new) | `AllocationOptimizer`: aligned prices + caps → weights. No IO. |
| `src/finwiz/orchestrators/allocation_orchestrator.py` (new) | fetches prices, calls the two above, builds `OptimalAllocation` |
| `src/finwiz/reporting/sections/optimal_allocation.py` (new) | renders current vs target, and the degraded path |
| `src/finwiz/flow_state_models.py` (modify) | `optimal_allocation`, `optimal_allocation_error` |
| `src/finwiz/flows/orchestrator.py` (modify) | Phase 3.7 |
| `src/finwiz/reporting/python_report_generator.py` (modify) | parameter, section call, template slot |
| `src/finwiz/orchestrators/reporting/enrichment.py` (modify) | reads state, passes it down |

**Note against the spec:** the spec listed six components; this plan splits calendar alignment into its own `price_matrix.py`. Alignment is data preparation, not optimisation, it is the riskiest logic in the feature, and it is worth testing without constructing an optimiser. The split is a refinement, not a change of design.

---

### Task 1: Output schemas

**Files:**

- Create: `src/finwiz/schemas/portfolio_optimization.py`
- Test: `tests/unit/schemas/test_portfolio_optimization.py`

**Interfaces:**

- Consumes: nothing.
- Produces: `HoldingTarget(ticker: str, asset_class: str, current_weight: float, target_weight: float, delta: float)`; `ExcludedHolding(ticker: str, reason: str)`; `OptimalAllocation(targets: list[HoldingTarget], excluded: list[ExcludedHolding], observations: int, window_start: str, window_end: str, per_position_cap: float, class_caps: dict[str, float], objective: str)`.

- [ ] **Step 1: Write the failing test**

```python
"""Unit tests for the optimal allocation schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from finwiz.schemas.portfolio_optimization import ExcludedHolding, HoldingTarget, OptimalAllocation


class TestHoldingTarget:
    def test_delta_is_target_minus_current(self) -> None:
        t = HoldingTarget(ticker="NESN.SW", asset_class="stock", current_weight=0.041, target_weight=0.065)
        assert t.delta == pytest.approx(0.024)

    def test_weights_are_bounded(self) -> None:
        with pytest.raises(ValidationError):
            HoldingTarget(ticker="X", asset_class="stock", current_weight=0.0, target_weight=1.5)


class TestOptimalAllocation:
    def test_targets_sum_to_one(self) -> None:
        alloc = OptimalAllocation(
            targets=[
                HoldingTarget(ticker="A", asset_class="stock", current_weight=0.5, target_weight=0.6),
                HoldingTarget(ticker="B", asset_class="etf", current_weight=0.5, target_weight=0.4),
            ],
            excluded=[ExcludedHolding(ticker="C", reason="42 observations, 120 required")],
            observations=248,
            window_start="2025-09-05",
            window_end="2026-09-05",
            per_position_cap=0.08,
            class_caps={"stock": 0.72, "etf": 0.41},
            objective="min_volatility",
        )
        assert alloc.total_target_weight == pytest.approx(1.0)
        assert alloc.excluded[0].ticker == "C"

    def test_rejects_targets_that_do_not_sum_to_one(self) -> None:
        with pytest.raises(ValidationError, match="must sum to 1"):
            OptimalAllocation(
                targets=[HoldingTarget(ticker="A", asset_class="stock", current_weight=1.0, target_weight=0.5)],
                excluded=[],
                observations=248,
                window_start="2025-09-05",
                window_end="2026-09-05",
                per_position_cap=0.08,
                class_caps={"stock": 1.0},
                objective="min_volatility",
            )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/schemas/test_portfolio_optimization.py -v --no-cov`
Expected: FAIL with `ModuleNotFoundError: No module named 'finwiz.schemas.portfolio_optimization'`

- [ ] **Step 3: Write minimal implementation**

```python
"""Pydantic models for portfolio allocation optimisation.

Produced by Phase 3.7 and consumed by the family report. A target set is
either complete and internally consistent or it is not produced at all --
see ``OptimalAllocation`` validation.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, computed_field, model_validator


class HoldingTarget(BaseModel):
    """One holding's current and recommended weight."""

    ticker: str
    asset_class: str
    current_weight: float = Field(ge=0.0, le=1.0, description="Share of priced portfolio value today (0..1)")
    target_weight: float = Field(ge=0.0, le=1.0, description="Recommended share under the optimiser's constraints (0..1)")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def delta(self) -> float:
        """Recommended move, in weight points. Positive means buy."""
        return self.target_weight - self.current_weight


class ExcludedHolding(BaseModel):
    """A holding the optimiser could not use, and why.

    Never omit an exclusion silently: a reader who cannot see an omission
    cannot question it.
    """

    ticker: str
    reason: str


class OptimalAllocation(BaseModel):
    """A complete target allocation plus everything needed to audit it."""

    targets: list[HoldingTarget] = Field(default_factory=list)
    excluded: list[ExcludedHolding] = Field(default_factory=list)
    observations: int = Field(ge=0, description="Aligned daily observations backing the covariance estimate")
    window_start: str
    window_end: str
    per_position_cap: float = Field(gt=0.0, le=1.0)
    class_caps: dict[str, float] = Field(default_factory=dict)
    objective: str = Field(default="min_volatility")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_target_weight(self) -> float:
        return sum(t.target_weight for t in self.targets)

    @model_validator(mode="after")
    def _targets_sum_to_one(self) -> OptimalAllocation:
        if not self.targets:
            return self
        total = sum(t.target_weight for t in self.targets)
        if abs(total - 1.0) > 1e-4:
            raise ValueError(f"target weights must sum to 1, got {total:.6f}")
        return self
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/schemas/test_portfolio_optimization.py -v --no-cov`
Expected: PASS, 4 tests

- [ ] **Step 5: Run the quality gate**

Run: `make lint && make mypy`
Expected: both clean

- [ ] **Step 6: Commit**

```bash
git add src/finwiz/schemas/portfolio_optimization.py tests/unit/schemas/test_portfolio_optimization.py
git commit -m "feat(schemas): optimal allocation output types"
```

---

### Task 2: Calendar alignment

**Files:**

- Create: `src/finwiz/quantitative/price_matrix.py`
- Test: `tests/unit/quantitative/test_price_matrix.py`

**Interfaces:**

- Consumes: nothing from earlier tasks.
- Produces: `build_price_matrix(series: dict[str, pd.Series], min_observations: int = 120, max_ffill_days: int = 3) -> tuple[pd.DataFrame, dict[str, str]]` — returns the aligned close-price matrix and a `{ticker: reason}` map of what it dropped.

This is the riskiest logic in the feature. The portfolio spans seven European venues, US listings and four cryptocurrencies that trade every day; a strict inner join on common dates collapses the observation count below what the covariance estimate needs.

- [ ] **Step 1: Write the failing test**

```python
"""Unit tests for calendar alignment across venues and crypto."""

from __future__ import annotations

import pandas as pd

from finwiz.quantitative.price_matrix import build_price_matrix


def _series(index: pd.DatetimeIndex, start: float = 100.0) -> pd.Series:
    return pd.Series([start + i for i in range(len(index))], index=index, dtype="float64")


class TestBuildPriceMatrix:
    def test_crypto_weekends_are_dropped(self) -> None:
        """Crypto trades every day; nothing else does. Weekends must not enter the matrix."""
        business = pd.bdate_range("2025-01-01", periods=200)
        every_day = pd.date_range("2025-01-01", periods=280)
        matrix, dropped = build_price_matrix({"AAPL": _series(business), "BTC-USD": _series(every_day)})
        assert dropped == {}
        assert len(matrix) == 200
        assert all(ts.weekday() < 5 for ts in matrix.index)

    def test_single_market_holiday_is_forward_filled(self) -> None:
        """One venue closed for a day must not delete that day for everyone."""
        business = pd.bdate_range("2025-01-01", periods=200)
        swiss = _series(business).drop(business[10])
        matrix, dropped = build_price_matrix({"AAPL": _series(business), "NESN.SW": swiss})
        assert dropped == {}
        assert len(matrix) == 200
        assert matrix.loc[business[10], "NESN.SW"] == matrix.loc[business[9], "NESN.SW"]

    def test_long_gap_is_not_filled_and_costs_observations(self) -> None:
        """A two-week hole is missing data, not a holiday. Do not invent prices."""
        business = pd.bdate_range("2025-01-01", periods=200)
        gapped = _series(business).drop(business[20:30])
        matrix, dropped = build_price_matrix({"AAPL": _series(business), "GAP.PA": gapped})
        assert dropped == {}
        assert len(matrix) == 193  # 200 - 10 missing + 3 recovered by the capped ffill

    def test_short_history_is_excluded_with_a_reason(self) -> None:
        business = pd.bdate_range("2025-01-01", periods=200)
        short = _series(pd.bdate_range("2025-09-01", periods=40))
        matrix, dropped = build_price_matrix({"AAPL": _series(business), "NEW.DE": short})
        assert "NEW.DE" in dropped
        assert "120" in dropped["NEW.DE"]
        assert list(matrix.columns) == ["AAPL"]

    def test_empty_input_returns_empty_matrix(self) -> None:
        matrix, dropped = build_price_matrix({})
        assert matrix.empty
        assert dropped == {}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/quantitative/test_price_matrix.py -v --no-cov`
Expected: FAIL with `ModuleNotFoundError: No module named 'finwiz.quantitative.price_matrix'`

- [ ] **Step 3: Write minimal implementation**

```python
"""Align many price series onto one matrix a covariance estimator can use.

The portfolio spans seven European venues, US listings and cryptocurrencies
that trade every day of the year. Swiss, French and German holidays do not
coincide, and crypto weekends exist for no equity. A strict inner join on
common dates would collapse the observation count far below what the
covariance estimate needs, so alignment is done deliberately:

1. Reindex every series onto the union of business days in the window.
2. Forward-fill each series by at most ``max_ffill_days``, absorbing a
   single-market holiday without inventing a week of prices.
3. Drop any date still incomplete.
4. Business days only, which also removes crypto weekends.
"""

from __future__ import annotations

import pandas as pd

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

MIN_OBSERVATIONS = 120
MAX_FFILL_DAYS = 3


def build_price_matrix(
    series: dict[str, pd.Series],
    min_observations: int = MIN_OBSERVATIONS,
    max_ffill_days: int = MAX_FFILL_DAYS,
) -> tuple[pd.DataFrame, dict[str, str]]:
    """Align price series onto a common business-day index.

    Args:
        series: ticker -> close price series indexed by date.
        min_observations: below this, a holding is excluded rather than trusted.
        max_ffill_days: how many consecutive missing days a holiday may cover.

    Returns:
        (aligned matrix, {ticker: exclusion reason}).
    """
    if not series:
        return pd.DataFrame(), {}

    dropped: dict[str, str] = {}
    usable: dict[str, pd.Series] = {}

    for ticker, s in series.items():
        clean = s.dropna()
        if len(clean) < min_observations:
            dropped[ticker] = f"{len(clean)} observations, {min_observations} required"
            continue
        usable[ticker] = clean

    if not usable:
        return pd.DataFrame(), dropped

    starts = [s.index.min() for s in usable.values()]
    ends = [s.index.max() for s in usable.values()]
    calendar = pd.bdate_range(max(starts), min(ends))

    aligned = pd.DataFrame(
        {ticker: s.reindex(calendar.union(s.index)).ffill(limit=max_ffill_days).reindex(calendar) for ticker, s in usable.items()},
        index=calendar,
    ).dropna()

    if len(aligned) < min_observations:
        logger.warning("Aligned matrix has %d observations, below the floor of %d", len(aligned), min_observations)

    logger.info("Price matrix aligned: %d tickers x %d observations (%d excluded)", len(aligned.columns), len(aligned), len(dropped))
    return aligned, dropped
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/quantitative/test_price_matrix.py -v --no-cov`
Expected: PASS, 5 tests. If `test_long_gap_is_not_filled_and_costs_observations` reports a different count, read the actual number and confirm it equals `200 - 10 + max_ffill_days` before adjusting the assertion — the arithmetic, not the assertion, is the thing to trust.

- [ ] **Step 5: Run the quality gate**

Run: `make lint && make mypy && uv run pytest tests/unit/quantitative/test_price_matrix.py -q --no-cov`
Expected: clean, 5 passed

- [ ] **Step 6: Commit**

```bash
git add src/finwiz/quantitative/price_matrix.py tests/unit/quantitative/test_price_matrix.py
git commit -m "feat(quantitative): align price series across venues and crypto calendars"
```

---

### Task 3: The optimiser

**Files:**

- Create: `src/finwiz/quantitative/allocation_optimizer.py`
- Test: `tests/unit/quantitative/test_allocation_optimizer.py`

**Interfaces:**

- Consumes: an aligned matrix from `build_price_matrix` (Task 2), though the optimiser accepts any `pd.DataFrame` of prices.
- Produces: `AllocationOptimizer(per_position_cap: float = 0.08)`, method `optimize(prices: pd.DataFrame, class_of: dict[str, str], class_caps: dict[str, float]) -> dict[str, float]`; exception `InfeasibleAllocationError(ValueError)`.

- [ ] **Step 1: Write the failing test**

```python
"""Unit tests for the minimum-variance allocation optimiser."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from finwiz.quantitative.allocation_optimizer import AllocationOptimizer, InfeasibleAllocationError


def _prices(n_assets: int = 20, n_obs: int = 252, seed: int = 0) -> pd.DataFrame:
    """Synthetic prices with HETEROGENEOUS volatilities.

    This matters. Under identical volatilities equal weight *is* the
    minimum-variance portfolio, so a binding class cap can only move the
    solution away from it and the "beats equal weight" assertion below
    fails against a perfectly correct implementation. Real portfolios have
    dispersed volatilities; the fixture must too.
    """
    rng = np.random.default_rng(seed)
    vols = rng.uniform(0.005, 0.03, n_assets)
    tickers = [f"T{i:02d}" for i in range(n_assets)]
    returns = rng.normal(0, 1, (n_obs, n_assets)) * vols
    return pd.DataFrame(
        100 * np.exp(np.cumsum(returns, axis=0)),
        columns=tickers,
        index=pd.bdate_range("2025-01-01", periods=n_obs),
    )


class TestAllocationOptimizer:
    def test_weights_sum_to_one_and_respect_the_position_cap(self) -> None:
        prices = _prices()
        classes = dict.fromkeys(prices.columns, "stock")
        weights = AllocationOptimizer(per_position_cap=0.08).optimize(prices, classes, {"stock": 1.0})
        assert sum(weights.values()) == pytest.approx(1.0, abs=1e-4)
        assert max(weights.values()) <= 0.08 + 1e-6
        assert min(weights.values()) >= 0.0

    def test_class_cap_binds(self) -> None:
        prices = _prices()
        classes = {t: ("crypto" if i < 4 else "stock") for i, t in enumerate(prices.columns)}
        weights = AllocationOptimizer(per_position_cap=0.08).optimize(prices, classes, {"crypto": 0.17, "stock": 1.0})
        crypto = sum(w for t, w in weights.items() if classes[t] == "crypto")
        assert crypto <= 0.17 + 1e-6

    def test_beats_equal_weight_on_variance(self) -> None:
        from pypfopt.risk_models import CovarianceShrinkage

        prices = _prices()
        classes = dict.fromkeys(prices.columns, "stock")
        weights = AllocationOptimizer(per_position_cap=0.08).optimize(prices, classes, {"stock": 1.0})

        S = CovarianceShrinkage(prices).ledoit_wolf()
        w = np.array([weights[t] for t in prices.columns])
        eq = np.full(len(prices.columns), 1 / len(prices.columns))
        assert w @ S.values @ w < eq @ S.values @ eq

    def test_infeasible_caps_raise_before_the_solver_runs(self) -> None:
        """8% over 10 holdings cannot reach 100%. Say so with the arithmetic."""
        prices = _prices(n_assets=10)
        classes = dict.fromkeys(prices.columns, "stock")
        with pytest.raises(InfeasibleAllocationError, match="10 eligible holdings, minimum 13"):
            AllocationOptimizer(per_position_cap=0.08).optimize(prices, classes, {"stock": 1.0})

    def test_empty_input_raises(self) -> None:
        with pytest.raises(InfeasibleAllocationError, match="0 eligible holdings"):
            AllocationOptimizer().optimize(pd.DataFrame(), {}, {})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/quantitative/test_allocation_optimizer.py -v --no-cov`
Expected: FAIL with `ModuleNotFoundError: No module named 'finwiz.quantitative.allocation_optimizer'`

- [ ] **Step 3: Write minimal implementation**

```python
"""Minimum-variance portfolio weights under position and class caps.

No expected returns are estimated anywhere in this module, deliberately.
Estimation error in expected returns dominates every other error in
mean-variance optimisation; the objective removes that term rather than
modelling it. pypfopt accepts ``expected_returns=None`` for
``min_volatility``, so the refusal to forecast is expressed through the
API rather than worked around.

Sixty-four assets estimated from roughly 252 daily observations puts the
sample covariance matrix at n ~ p, where it is ill-conditioned and its
inverse is unstable. Ledoit-Wolf shrinkage is therefore unconditional,
not an option.
"""

from __future__ import annotations

import math

import cvxpy
import pandas as pd
from pypfopt import EfficientFrontier
from pypfopt.risk_models import CovarianceShrinkage

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

DEFAULT_PER_POSITION_CAP = 0.08


class InfeasibleAllocationError(ValueError):
    """The constraints admit no allocation. Raised with the arithmetic that shows why."""


class AllocationOptimizer:
    """Computes minimum-variance target weights. Pure: no IO, no state."""

    def __init__(self, per_position_cap: float = DEFAULT_PER_POSITION_CAP) -> None:
        self.per_position_cap = per_position_cap

    def optimize(self, prices: pd.DataFrame, class_of: dict[str, str], class_caps: dict[str, float]) -> dict[str, float]:
        """Return ticker -> target weight.

        Args:
            prices: aligned close prices, one column per ticker.
            class_of: ticker -> asset class.
            class_caps: asset class -> maximum combined weight.

        Raises:
            InfeasibleAllocationError: caps cannot reach 100%, or the solver found no solution.
        """
        tickers = list(prices.columns)
        self._require_feasible(len(tickers))

        S = CovarianceShrinkage(prices).ledoit_wolf()
        ef = EfficientFrontier(None, S, weight_bounds=(0.0, self.per_position_cap))

        for asset_class, cap in class_caps.items():
            idx = [i for i, t in enumerate(tickers) if class_of.get(t) == asset_class]
            if idx and cap < 1.0:
                ef.add_constraint(lambda w, i=idx, c=cap: cvxpy.sum(w[i]) <= c)

        try:
            ef.min_volatility()
            weights = ef.clean_weights()
        except Exception as e:
            # pypfopt raises OptimizationError with a message naming neither the
            # caps nor the counts. Re-raise with something a reader can act on.
            raise InfeasibleAllocationError(
                f"solver found no allocation for {len(tickers)} holdings under a {self.per_position_cap:.0%} position cap and class caps {class_caps}: {e}"
            ) from e

        logger.info("Optimal allocation: %d holdings, max weight %.2f%%", len(weights), 100 * max(weights.values()))
        return dict(weights)

    def _require_feasible(self, n_eligible: int) -> None:
        """A cap of c admits at most c per holding, so n * c must reach 1."""
        minimum = math.ceil(1.0 / self.per_position_cap)
        if n_eligible < minimum:
            raise InfeasibleAllocationError(f"{n_eligible} eligible holdings, minimum {minimum} under a {self.per_position_cap:.0%} cap")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/quantitative/test_allocation_optimizer.py -v --no-cov`
Expected: PASS, 5 tests

- [ ] **Step 5: Run the quality gate**

Run: `make lint && make mypy`
Expected: clean. `pypfopt.*` and `cvxpy` may need a `[[tool.mypy.overrides]]` entry in `pyproject.toml`; `pypfopt.*` already has one at line ~377, add `cvxpy.*` alongside it if mypy complains about missing stubs.

- [ ] **Step 6: Commit**

```bash
git add src/finwiz/quantitative/allocation_optimizer.py tests/unit/quantitative/test_allocation_optimizer.py
git commit -m "feat(quantitative): minimum-variance allocation under position and class caps"
```

---

### Task 4: The orchestrator

**Files:**

- Create: `src/finwiz/orchestrators/allocation_orchestrator.py`
- Test: `tests/unit/orchestrators/test_allocation_orchestrator.py`

**Interfaces:**

- Consumes: `build_price_matrix` (Task 2), `AllocationOptimizer` / `InfeasibleAllocationError` (Task 3), `OptimalAllocation` / `HoldingTarget` / `ExcludedHolding` (Task 1).
- Produces: `AllocationOrchestrator(state: Any)`, method `compute_optimal_allocation() -> OptimalAllocation | None`.

Follow `orchestrators/stress_test_orchestrator.py` for shape: takes state, builds its inputs from `state.portfolio_review`, returns a typed result, logs and returns `None` rather than raising.

- [ ] **Step 1: Write the failing test**

```python
"""Unit tests for the allocation orchestrator. No network: the data manager is mocked."""

from __future__ import annotations

from types import SimpleNamespace

import pandas as pd
import pytest

from finwiz.orchestrators.allocation_orchestrator import AllocationOrchestrator


def _holding(ticker: str, asset_class: str, weight: float | None) -> SimpleNamespace:
    return SimpleNamespace(ticker=ticker, asset_class=asset_class, weight=weight)


def _state(holdings: list[SimpleNamespace]) -> SimpleNamespace:
    return SimpleNamespace(portfolio_review=SimpleNamespace(holdings=holdings))


def _frame(n: int, start: str = "2025-01-01") -> pd.DataFrame:
    idx = pd.bdate_range(start, periods=n)
    return pd.DataFrame({"Close": [100.0 + i for i in range(n)]}, index=idx)


class TestAllocationOrchestrator:
    def test_returns_none_when_no_priced_holdings(self) -> None:
        orch = AllocationOrchestrator(_state([_holding("A", "stock", None)]))
        assert orch.compute_optimal_allocation() is None

    def test_short_history_holding_is_excluded_with_its_reason(self, mocker) -> None:
        holdings = [_holding(f"T{i:02d}", "stock", 1 / 15) for i in range(15)]
        state = _state(holdings)
        orch = AllocationOrchestrator(state)

        def fake_fetch(symbol, start_date, end_date, **kwargs):
            return _frame(40) if symbol == "T00" else _frame(250)

        mocker.patch.object(orch.data_manager, "fetch_historical_data", side_effect=fake_fetch)

        result = orch.compute_optimal_allocation()
        assert result is not None
        assert [e.ticker for e in result.excluded] == ["T00"]
        assert "120" in result.excluded[0].reason
        assert all(t.ticker != "T00" for t in result.targets)

    def test_current_weights_come_from_the_priced_set(self, mocker) -> None:
        """The denominator must match the one the allocation hero displays."""
        holdings = [_holding(f"T{i:02d}", "stock", 1 / 15) for i in range(15)]
        orch = AllocationOrchestrator(_state(holdings))
        mocker.patch.object(orch.data_manager, "fetch_historical_data", return_value=_frame(250))

        result = orch.compute_optimal_allocation()
        assert result is not None
        assert sum(t.current_weight for t in result.targets) == pytest.approx(1.0, abs=1e-6)

    def test_infeasible_caps_return_none_and_are_logged(self, mocker, caplog) -> None:
        import logging

        holdings = [_holding(f"T{i:02d}", "stock", 0.1) for i in range(10)]
        orch = AllocationOrchestrator(_state(holdings))
        mocker.patch.object(orch.data_manager, "fetch_historical_data", return_value=_frame(250))

        with caplog.at_level(logging.WARNING):
            assert orch.compute_optimal_allocation() is None
        assert any("minimum 13" in r.message for r in caplog.records)

    def test_fetch_failure_for_one_ticker_excludes_only_that_one(self, mocker) -> None:
        holdings = [_holding(f"T{i:02d}", "stock", 1 / 15) for i in range(15)]
        orch = AllocationOrchestrator(_state(holdings))

        def fake_fetch(symbol, start_date, end_date, **kwargs):
            if symbol == "T03":
                raise RuntimeError("yfinance said no")
            return _frame(250)

        mocker.patch.object(orch.data_manager, "fetch_historical_data", side_effect=fake_fetch)

        result = orch.compute_optimal_allocation()
        assert result is not None
        assert [e.ticker for e in result.excluded] == ["T03"]
        assert "yfinance said no" in result.excluded[0].reason
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/orchestrators/test_allocation_orchestrator.py -v --no-cov`
Expected: FAIL with `ModuleNotFoundError: No module named 'finwiz.orchestrators.allocation_orchestrator'`

- [ ] **Step 3: Write minimal implementation**

```python
"""Orchestrator for portfolio allocation optimisation (Phase 3.7).

Builds a price matrix from the priced holdings in flow state, runs the
minimum-variance optimiser, and returns a typed target allocation for the
report. Never raises: a failure here must not cost the run its report.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import pandas as pd

from finwiz.quantitative.allocation_optimizer import AllocationOptimizer, InfeasibleAllocationError
from finwiz.quantitative.data_loaders import HistoricalDataManager
from finwiz.quantitative.price_matrix import build_price_matrix
from finwiz.schemas.portfolio_optimization import ExcludedHolding, HoldingTarget, OptimalAllocation
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

LOOKBACK_DAYS = 365
CLASS_CAP_HEADROOM = 0.10


class AllocationOrchestrator:
    """Computes an optimal allocation from the portfolio held in flow state."""

    def __init__(self, state: Any, per_position_cap: float = 0.08) -> None:
        self.state = state
        self.data_manager = HistoricalDataManager()
        self.optimizer = AllocationOptimizer(per_position_cap=per_position_cap)

    def compute_optimal_allocation(self) -> OptimalAllocation | None:
        """Return a target allocation, or None with the reason logged."""
        priced = [h for h in getattr(self.state.portfolio_review, "holdings", []) if getattr(h, "weight", None) is not None]
        if not priced:
            logger.warning("No priced holdings available for allocation optimisation")
            return None

        end = datetime.now()
        start = end - timedelta(days=LOOKBACK_DAYS)

        series, fetch_failures = self._fetch_series(priced, start, end)
        matrix, short_history = build_price_matrix(series)

        excluded = [ExcludedHolding(ticker=t, reason=r) for t, r in {**fetch_failures, **short_history}.items()]
        if matrix.empty:
            logger.warning("Allocation optimisation skipped: no usable price history (%d excluded)", len(excluded))
            return None

        class_of = {h.ticker: str(h.asset_class) for h in priced}
        eligible = [h for h in priced if h.ticker in matrix.columns]
        current = self._current_weights(eligible)

        try:
            weights = self.optimizer.optimize(matrix, class_of, self._class_caps(current, class_of))
        except InfeasibleAllocationError as e:
            logger.warning("Allocation optimisation skipped: %s", e)
            return None

        return OptimalAllocation(
            targets=[
                HoldingTarget(ticker=t, asset_class=class_of.get(t, "unknown"), current_weight=current.get(t, 0.0), target_weight=w)
                for t, w in weights.items()
            ],
            excluded=sorted(excluded, key=lambda e: e.ticker),
            observations=len(matrix),
            window_start=str(matrix.index.min().date()),
            window_end=str(matrix.index.max().date()),
            per_position_cap=self.optimizer.per_position_cap,
            class_caps=self._class_caps(current, class_of),
            objective="min_volatility",
        )

    def _fetch_series(self, holdings: list[Any], start: datetime, end: datetime) -> tuple[dict[str, pd.Series], dict[str, str]]:
        """Fetch close prices per holding. The cache is warm from deep analysis."""
        series: dict[str, pd.Series] = {}
        failures: dict[str, str] = {}
        for h in holdings:
            try:
                frame = self.data_manager.fetch_historical_data(h.ticker, start, end)
                if frame is None or frame.empty or "Close" not in frame:
                    failures[h.ticker] = "no price history returned"
                    continue
                series[h.ticker] = frame["Close"]
            except Exception as e:
                failures[h.ticker] = f"price fetch failed: {e}"
        return series, failures

    def _current_weights(self, eligible: list[Any]) -> dict[str, float]:
        """Renormalise over the eligible set.

        The weights carried on holdings are shares of the whole priced
        portfolio. Once exclusions are applied they no longer sum to 1, and
        comparing a target computed over one set against a current weight
        computed over another is the exact defect 5.14.1 fixed.
        """
        total = sum(float(h.weight) for h in eligible)
        if total <= 0:
            return {}
        return {h.ticker: float(h.weight) / total for h in eligible}

    def _class_caps(self, current: dict[str, float], class_of: dict[str, str]) -> dict[str, float]:
        """Each class may grow by CLASS_CAP_HEADROOM over its current share."""
        by_class: dict[str, float] = {}
        for ticker, weight in current.items():
            by_class[class_of.get(ticker, "unknown")] = by_class.get(class_of.get(ticker, "unknown"), 0.0) + weight
        return {cls: min(1.0, share + CLASS_CAP_HEADROOM) for cls, share in by_class.items()}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/orchestrators/test_allocation_orchestrator.py -v --no-cov`
Expected: PASS, 5 tests

- [ ] **Step 5: Run the quality gate**

Run: `make lint && make mypy && make check-unittest-mock`
Expected: clean

- [ ] **Step 6: Commit**

```bash
git add src/finwiz/orchestrators/allocation_orchestrator.py tests/unit/orchestrators/test_allocation_orchestrator.py
git commit -m "feat(orchestrators): assemble and optimise the portfolio allocation"
```

---

### Task 5: Flow state and Phase 3.7

**Files:**

- Modify: `src/finwiz/flow_state_models.py` (beside `stress_test_results` at line ~282)
- Modify: `src/finwiz/flows/orchestrator.py` (after the Phase 3.6 block)
- Test: `tests/unit/flow/test_phase_optimal_allocation.py`

**Interfaces:**

- Consumes: `AllocationOrchestrator.compute_optimal_allocation()` (Task 4).
- Produces: `state.optimal_allocation: dict[str, Any] | None`, `state.optimal_allocation_error: str | None`.

- [ ] **Step 1: Write the failing test**

```python
"""Phase 3.7 must never cost the run its report."""

from __future__ import annotations

from types import SimpleNamespace

from finwiz.flow_state_models import FinwizState


class TestOptimalAllocationState:
    def test_state_carries_the_new_fields(self) -> None:
        state = FinwizState()
        assert state.optimal_allocation is None
        assert state.optimal_allocation_error is None


class TestPhase37FailsSoft:
    def test_orchestrator_exception_is_recorded_not_raised(self, mocker) -> None:
        from finwiz.orchestrators.allocation_orchestrator import AllocationOrchestrator

        mocker.patch.object(AllocationOrchestrator, "compute_optimal_allocation", side_effect=RuntimeError("solver exploded"))

        state = FinwizState()
        state.deep_analysis_success = True
        state.portfolio_review = SimpleNamespace(holdings=[])

        # Phase 3.7 is inline in FinwizFlow; exercise the same guarded block.
        try:
            orch = AllocationOrchestrator(state)
            result = orch.compute_optimal_allocation()
            state.optimal_allocation = result.model_dump() if result else None
        except Exception as e:  # noqa: BLE001 - mirrors the phase's own guard
            state.optimal_allocation_error = str(e)

        assert state.optimal_allocation is None
        assert state.optimal_allocation_error == "solver exploded"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/flow/test_phase_optimal_allocation.py -v --no-cov`
Expected: FAIL with `AttributeError: 'FinwizState' object has no attribute 'optimal_allocation'`

- [ ] **Step 3: Add the state fields**

In `src/finwiz/flow_state_models.py`, immediately after the `stress_test_error` field:

```python
    # Phase 3.7: Optimal allocation (advisory; consumed by the family report)
    optimal_allocation: dict[str, Any] | None = None
    optimal_allocation_error: str | None = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/flow/test_phase_optimal_allocation.py -v --no-cov`
Expected: PASS, 2 tests

- [ ] **Step 5: Wire Phase 3.7 into the flow**

In `src/finwiz/flows/orchestrator.py`, immediately after the Phase 3.6 gap-profile block, insert:

```python
        # Phase 3.7: Optimal Allocation (advisory)
        # Needs deep analysis only because that is what warms the price cache.
        # Fail-soft on the Phase 3.5 model: a missing allocation costs the
        # report one section, never the run.
        if self.state.deep_analysis_success:
            logger.info("=" * 80)
            logger.info("PHASE 3.7: Optimal Allocation")
            logger.info("=" * 80)
            try:
                from finwiz.orchestrators.allocation_orchestrator import AllocationOrchestrator

                allocation_orch = AllocationOrchestrator(self.state)
                allocation = allocation_orch.compute_optimal_allocation()
                self.state.optimal_allocation = allocation.model_dump() if allocation else None
                if allocation:
                    logger.info("Optimal allocation computed: %d targets, %d excluded, %d observations", len(allocation.targets), len(allocation.excluded), allocation.observations)
                else:
                    logger.info("Optimal allocation not produced this run")
            except Exception as e:
                self.state.optimal_allocation_error = str(e)
                logger.warning(f"Optimal allocation skipped: {e}")
```

- [ ] **Step 6: Verify the flow module still imports and the suite is green**

Run: `uv run python -c "from finwiz.flows.orchestrator import FinwizFlow; print('ok')" && make check`
Expected: `ok`, then all quality checks pass

- [ ] **Step 7: Commit**

```bash
git add src/finwiz/flow_state_models.py src/finwiz/flows/orchestrator.py tests/unit/flow/test_phase_optimal_allocation.py
git commit -m "feat(flows): phase 3.7 computes an optimal allocation, fail-soft"
```

---

### Task 6: The report section

**Files:**

- Create: `src/finwiz/reporting/sections/optimal_allocation.py`
- Modify: `src/finwiz/reporting/python_report_generator.py` (signature ~line 55-70, inner signature ~line 231, template slot ~line 312, private method beside `_generate_stress_test_section` ~line 427)
- Modify: `src/finwiz/orchestrators/reporting/enrichment.py` (~line 60 and ~line 95)
- Test: `tests/unit/reporting/test_optimal_allocation_section.py`

**Interfaces:**

- Consumes: `state.optimal_allocation` as a plain dict (`OptimalAllocation.model_dump()`).
- Produces: `generate_optimal_allocation_section(optimal_allocation: dict[str, Any] | None, error: str | None = None) -> str`.

- [ ] **Step 1: Write the failing test**

```python
"""Unit tests for the optimal allocation report section."""

from __future__ import annotations

from finwiz.reporting.sections.optimal_allocation import generate_optimal_allocation_section


def _payload() -> dict:
    return {
        "targets": [
            {"ticker": "NESN.SW", "asset_class": "stock", "current_weight": 0.041, "target_weight": 0.065, "delta": 0.024},
            {"ticker": "ASML", "asset_class": "stock", "current_weight": 0.092, "target_weight": 0.080, "delta": -0.012},
        ],
        "excluded": [{"ticker": "NEW.DE", "reason": "40 observations, 120 required"}],
        "observations": 248,
        "window_start": "2025-09-05",
        "window_end": "2026-09-05",
        "per_position_cap": 0.08,
        "class_caps": {"stock": 0.72},
        "objective": "min_volatility",
    }


class TestOptimalAllocationSection:
    def test_renders_targets_and_deltas(self) -> None:
        html = generate_optimal_allocation_section(_payload())
        assert "NESN.SW" in html
        assert "6.5" in html  # target weight, percent
        assert "+2.4" in html or "2.4" in html  # delta

    def test_discloses_excluded_holdings_with_reasons(self) -> None:
        html = generate_optimal_allocation_section(_payload())
        assert "NEW.DE" in html
        assert "120" in html

    def test_states_that_past_return_plays_no_part(self) -> None:
        """The number will be read as a forecast unless the page says otherwise."""
        html = generate_optimal_allocation_section(_payload())
        assert "rendement" in html.lower()

    def test_absent_allocation_renders_nothing_but_a_reason(self) -> None:
        html = generate_optimal_allocation_section(None, error="10 eligible holdings, minimum 13 under an 8% cap")
        assert "minimum 13" in html
        assert "<table" not in html

    def test_absent_allocation_without_a_reason_renders_empty(self) -> None:
        assert generate_optimal_allocation_section(None) == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/reporting/test_optimal_allocation_section.py -v --no-cov`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
"""Renders the advisory optimal allocation, current against target."""

from __future__ import annotations

from html import escape
from typing import Any

METHOD_NOTE = (
    "Allocation de variance minimale : elle ne repose sur <strong>aucune prévision de rendement</strong>. "
    "L'erreur d'estimation des rendements futurs domine tout le reste en optimisation moyenne-variance, "
    "on la supprime en refusant de prédire. Conséquence directe à garder en tête : le calcul proposera de "
    "réduire des positions qui ont bien performé, puisque le rendement passé n'entre pas dans l'objectif."
)


def generate_optimal_allocation_section(optimal_allocation: dict[str, Any] | None, error: str | None = None) -> str:
    """Generate the optimal allocation section.

    Args:
        optimal_allocation: ``OptimalAllocation.model_dump()``, or None.
        error: why it is absent, when it is.

    Returns:
        HTML string. Empty only when there is neither a result nor a reason.
    """
    if not optimal_allocation:
        if not error:
            return ""
        return f"""
  <section class="card">
    <h2>🎯 Allocation optimale</h2>
    <p class="muted">Non calculée pour ce run — {escape(error)}</p>
  </section>
"""

    targets = sorted(optimal_allocation.get("targets", []), key=lambda t: abs(t.get("delta", 0.0)), reverse=True)
    rows = "\n".join(
        f"""      <tr>
        <td>{escape(str(t.get("ticker", "")))}</td>
        <td>{escape(str(t.get("asset_class", "")))}</td>
        <td class="num">{100 * float(t.get("current_weight", 0.0)):.1f} %</td>
        <td class="num">{100 * float(t.get("target_weight", 0.0)):.1f} %</td>
        <td class="num {"pos" if float(t.get("delta", 0.0)) >= 0 else "neg"}">{100 * float(t.get("delta", 0.0)):+.1f}</td>
      </tr>"""
        for t in targets
    )

    excluded = optimal_allocation.get("excluded", [])
    excluded_block = ""
    if excluded:
        items = "\n".join(f"      <li>{escape(str(e.get('ticker', '')))} — {escape(str(e.get('reason', '')))}</li>" for e in excluded)
        excluded_block = f"""
    <details class="muted">
      <summary>{len(excluded)} position{"s" if len(excluded) > 1 else ""} exclue{"s" if len(excluded) > 1 else ""} du calcul</summary>
      <ul>
{items}
      </ul>
    </details>"""

    cap = 100 * float(optimal_allocation.get("per_position_cap", 0.0))
    return f"""
  <section class="card">
    <h2>🎯 Allocation optimale</h2>
    <p class="muted">{METHOD_NOTE}</p>
    <p class="muted">
      {optimal_allocation.get("observations", 0)} observations quotidiennes alignées
      du {escape(str(optimal_allocation.get("window_start", "")))} au {escape(str(optimal_allocation.get("window_end", "")))} ·
      plafond {cap:.0f} % par position
    </p>
    <table class="data-table">
      <thead>
        <tr><th>Position</th><th>Classe</th><th class="num">Actuel</th><th class="num">Cible</th><th class="num">Δ (points)</th></tr>
      </thead>
      <tbody>
{rows}
      </tbody>
    </table>{excluded_block}
  </section>
"""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/reporting/test_optimal_allocation_section.py -v --no-cov`
Expected: PASS, 5 tests

- [ ] **Step 5: Export the section**

In `src/finwiz/reporting/section_generators.py`, add `generate_optimal_allocation_section` to the imports and to `__all__`, matching how `generate_stress_test_section` is handled.

- [ ] **Step 6: Wire it into the report generator**

In `src/finwiz/reporting/python_report_generator.py`:

**Signatures.** Add `optimal_allocation: dict[str, Any] | None = None,` and `optimal_allocation_error: str | None = None,` to `generate_family_financial_plan` (~line 55) and to the inner builder signature (~line 231), passing them through at the ~line 109 call site.
**Template slot.** Add the template slot immediately after the stress test slot (~line 312):

```python
  {self._generate_optimal_allocation_section(optimal_allocation, optimal_allocation_error)}
```

**Private method.** Add the private method beside `_generate_stress_test_section` (~line 427):

```python
    def _generate_optimal_allocation_section(self, optimal_allocation: dict[str, Any] | None, error: str | None) -> str:
        from finwiz.reporting.sections.optimal_allocation import (
            generate_optimal_allocation_section,
        )

        return generate_optimal_allocation_section(optimal_allocation, error)
```

**Module-level passthrough.** Add `optimal_allocation=optimal_allocation, optimal_allocation_error=optimal_allocation_error,` to the module-level `generate_python_report` passthrough (~line 491).

- [ ] **Step 7: Wire the enrichment orchestrator**

In `src/finwiz/orchestrators/reporting/enrichment.py`, beside the stress-test read (~line 60):

```python
        # Optimal allocation from Phase 3.7, if it produced one
        optimal_allocation: dict[str, Any] | None = getattr(self.state, "optimal_allocation", None) or None
        optimal_allocation_error: str | None = getattr(self.state, "optimal_allocation_error", None)
```

and add both to the `generate_python_report(...)` call (~line 95).

- [ ] **Step 8: Run the full gate**

Run: `make check`
Expected: all quality checks pass

- [ ] **Step 9: Commit**

```bash
git add src/finwiz/reporting/ src/finwiz/orchestrators/reporting/enrichment.py tests/unit/reporting/test_optimal_allocation_section.py
git commit -m "feat(reporting): show current allocation against the optimal one"
```

---

### Task 7: Live verification

**Files:** none changed. This task produces evidence, not code.

**Interfaces:**

- Consumes: everything above.
- Produces: a verified run, and the numbers to paste into the PR.

- [ ] **Step 1: Run the flow**

Run: `uv run crewai flow kickoff`
Expected: completes; `PHASE 3.7: Optimal Allocation` appears in `logs/finwiz.log`.

- [ ] **Step 2: Read the phase's own numbers**

Run: `grep -A3 'PHASE 3.7' logs/finwiz.log | tail -5`
Expected: a line reading `Optimal allocation computed: N targets, M excluded, K observations`. Record N, M and K.

- [ ] **Step 3: Check the constraints actually held on real data**

Run:

```bash
uv run python -c "
import json, pathlib, re
html = pathlib.Path('output/finwiz_family_financial_plan.html').read_text()
rows = re.findall(r'<td class=\"num\">([0-9.]+) %</td>', html)
print('max target weight:', max(float(r) for r in rows[1::2]))
"
```

Expected: no target above 8.0.

- [ ] **Step 4: Force the degraded path**

Make the constraints impossible to satisfy: temporarily set `per_position_cap=0.001` in `AllocationOrchestrator.__init__`. That cap needs 1000 eligible holdings, so `_require_feasible` raises on 64. Rerun. Expected: the report renders the section carrying the reason ("N eligible holdings, minimum 1000 under a 0% cap"), the run still completes, `make check` still green. Revert afterwards.

- [ ] **Step 5: Record the evidence and open the PR**

The PR body must state: number of targets, number excluded and why, observation count, maximum target weight, and confirmation that the degraded path was exercised.

---

## Self-Review

**Spec coverage.** Placement (Task 5), six components (Tasks 1, 2, 3, 4, 6 — with the `price_matrix.py` split noted in File Structure), numerical core (Task 3), constraints (Tasks 3, 4), calendar alignment (Task 2), eligibility and exclusion (Tasks 2, 4), three failure levels (Task 3 optimiser, Task 5 phase, Task 6 report), testing (every task), implementation order (task order matches the spec's six steps, with alignment promoted to its own task), done-when (Task 7). The spec's risk that minimum variance trims winners is discharged by `METHOD_NOTE` in Task 6, asserted by `test_states_that_past_return_plays_no_part`.

**Placeholder scan.** No TBD or TODO. Every code step carries runnable code. Task 2's alignment code is complete as written.

**Type consistency.** `OptimalAllocation` fields defined in Task 1 are the ones Task 4 constructs and Task 6 reads by key. `build_price_matrix` returns `(DataFrame, dict[str, str])` in Task 2 and is unpacked that way in Task 4. `AllocationOptimizer.optimize(prices, class_of, class_caps)` is defined in Task 3 and called with that argument order in Task 4. `InfeasibleAllocationError` is raised in Task 3 and caught in Task 4. `generate_optimal_allocation_section(payload, error)` is defined in Task 6 and called with that arity from the generator in the same task.
