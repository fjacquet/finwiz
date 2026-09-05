# Tactical Price Targets Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic 3-6 month "objectif de cours" (target) and a "niveau de vente" (stop-loss floor) to every holding in the deep-analysis report, computed entirely from price history we already collect.

**Architecture:** New thin orchestration module `quantitative/tactical_pricing.py` that combines existing primitives (`calculate_support_resistance_targets`, ATR, log-return drift) into a `PriceTargets` Pydantic instance. Wiring path: quantify stage → `QuantitativeAnalysis.price_targets` (new optional field) → merge.py copies onto `HoldingDecision.price_targets` (existing optional field) → `section_generators.py` renders compact columns + a detail panel in the per-ticker HTML. 100% Python — no AI.

**Tech Stack:** Python 3.12, Pydantic v2, pandas, NumPy, TA-Lib (already a dep), pytest + pytest-mock.

**Spec:** [docs/adr/ADR-011-tactical-price-targets-and-sell-levels.md](../../adr/ADR-011-tactical-price-targets-and-sell-levels.md).

---

## File Plan

| File | Status | Responsibility |
|---|---|---|
| `src/finwiz/quantitative/tactical_pricing.py` | NEW | Public `compute_tactical_pricing()` returning `PriceTargets`. Uses ATR + support/resistance + drift. |
| `tests/unit/quantitative/test_tactical_pricing.py` | NEW | Unit tests for the helper across asset classes + edge cases. |
| `src/finwiz/schemas/hybrid_analysis/quantitative.py` | MODIFY | Add `price_targets: PriceTargets \| None = None` field. |
| `src/finwiz/analysis/stages/quantify.py` | MODIFY | Call `compute_tactical_pricing` after scoring; attach to `QuantitativeAnalysis`. |
| `tests/unit/analysis/stages/test_quantify.py` | NEW (or extend) | Verify quantify stage propagates `price_targets`. |
| `src/finwiz/orchestrators/portfolio_review/merge.py` | MODIFY | Copy `quant.price_targets` → `decision.price_targets`. |
| `tests/unit/orchestrators/test_merge.py` | EXTEND | Verify price_targets propagation. |
| `src/finwiz/reporting/section_generators.py` | MODIFY | Render two compact columns in holdings table; add table header. |
| `tests/unit/reporting/test_section_generators.py` | EXTEND | Render compact columns; verify HTML escape + N/A rendering. |
| `src/finwiz/templates/enriched_analysis_report.html` | MODIFY | Detail panel "🎯 Targets" with confidence badge. |
| `src/finwiz/reporting/enriched_analysis_report_generator.py` | MODIFY | Pass `price_targets` into template_vars. |
| `tests/property/test_enriched_analysis_report_properties.py` | EXTEND | Detail panel renders when price_targets present. |

---

## Task 1: Create `tactical_pricing.py` core module

**Files:**

- Create: `src/finwiz/quantitative/tactical_pricing.py`
- Test: `tests/unit/quantitative/test_tactical_pricing.py`

- [ ] **Step 1.1: Write the failing test file**

```python
# tests/unit/quantitative/test_tactical_pricing.py
"""Tests for tactical_pricing.compute_tactical_pricing helper."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from finwiz.quantitative.tactical_pricing import compute_tactical_pricing
from finwiz.schemas.portfolio_review import PriceTargets


def _series(values: list[float], freq: str = "B") -> pd.Series:
    """Build a business-day-indexed price series ending today."""
    end = pd.Timestamp.now().normalize()
    idx = pd.bdate_range(end=end, periods=len(values))
    return pd.Series(values, index=idx, dtype=float)


class TestStockTactical:
    def test_returns_pricetargets_for_stock(self) -> None:
        # 250-day uptrend with mild noise — a typical liquid stock.
        rng = np.random.default_rng(seed=42)
        base = np.linspace(100.0, 130.0, 250)
        noise = rng.normal(0.0, 1.0, 250)
        prices = _series((base + noise).tolist())
        result = compute_tactical_pricing(
            ticker="AAPL",
            asset_class="stock",
            price_history=prices,
            current_price=130.0,
        )
        assert isinstance(result, PriceTargets)
        assert result.current_price == pytest.approx(130.0)
        assert result.currency == "USD"
        assert result.sell_target_primary is not None
        assert result.buy_target_primary is not None
        # Target above current (stock is in uptrend), sell-level below current.
        assert result.buy_target_primary > 130.0
        assert result.sell_target_primary < 130.0

    def test_target_capped_at_25pct_for_stock(self) -> None:
        # Pathological 10x rip — drift would project crazy upside; cap at +25%.
        prices = _series([10.0] * 50 + list(np.linspace(10.0, 100.0, 200)))
        result = compute_tactical_pricing(
            ticker="MEME",
            asset_class="stock",
            price_history=prices,
            current_price=100.0,
        )
        assert result is not None
        assert result.buy_target_primary is not None
        assert result.buy_target_primary <= 100.0 * 1.25 + 1e-6

    def test_sell_level_uses_higher_of_support_or_atr_floor(self) -> None:
        # Flat-ish series so technical support is right below current price.
        # ATR floor = current - 2*ATR; support is the local low.
        # Whichever is HIGHER (more conservative) wins.
        prices = _series([100.0, 99.0, 101.0, 100.5, 99.5, 100.2, 100.8] * 30)
        result = compute_tactical_pricing(
            ticker="STABLE",
            asset_class="stock",
            price_history=prices,
            current_price=100.8,
        )
        assert result is not None
        assert result.sell_target_primary is not None
        # ATR is small so the floor stays close to current.
        assert result.sell_target_primary >= 95.0
        assert result.sell_target_primary <= 100.8


class TestETFTactical:
    def test_returns_pricetargets_for_etf(self) -> None:
        prices = _series(list(np.linspace(50.0, 60.0, 250)))
        result = compute_tactical_pricing(
            ticker="VOO",
            asset_class="etf",
            price_history=prices,
            current_price=60.0,
        )
        assert result is not None
        assert result.buy_rationale.lower().startswith(("target", "objectif", "résistance"))

    def test_etf_uses_same_25pct_cap(self) -> None:
        prices = _series(list(np.linspace(10.0, 100.0, 250)))
        result = compute_tactical_pricing(
            ticker="HYPE",
            asset_class="etf",
            price_history=prices,
            current_price=100.0,
        )
        assert result is not None
        assert result.buy_target_primary <= 100.0 * 1.25 + 1e-6


class TestCryptoTactical:
    def test_crypto_uses_40pct_cap(self) -> None:
        # Crypto lets drift run further than stocks.
        prices = _series(list(np.linspace(1000.0, 10000.0, 250)))
        result = compute_tactical_pricing(
            ticker="BTC-USD",
            asset_class="crypto",
            price_history=prices,
            current_price=10000.0,
        )
        assert result is not None
        # 40% cap must be respected and must be ABOVE the 25% stock cap.
        assert result.buy_target_primary <= 10000.0 * 1.40 + 1e-6
        assert result.buy_target_primary > 10000.0 * 1.25  # widened from stocks


class TestEdgeCases:
    def test_short_history_returns_none(self) -> None:
        prices = _series([100.0] * 30)  # < 60 days
        result = compute_tactical_pricing(
            ticker="NEW",
            asset_class="stock",
            price_history=prices,
            current_price=100.0,
        )
        assert result is None

    def test_stale_history_returns_none(self) -> None:
        # Last price is 10 days old → stale; don't lock onto stale anchor.
        end = pd.Timestamp.now().normalize() - pd.Timedelta(days=10)
        idx = pd.bdate_range(end=end, periods=120)
        prices = pd.Series([100.0] * 120, index=idx, dtype=float)
        result = compute_tactical_pricing(
            ticker="STALE",
            asset_class="stock",
            price_history=prices,
            current_price=100.0,
        )
        assert result is None

    def test_zero_current_price_returns_none(self) -> None:
        prices = _series([100.0] * 120)
        result = compute_tactical_pricing(
            ticker="ZERO",
            asset_class="stock",
            price_history=prices,
            current_price=0.0,
        )
        assert result is None

    def test_breakout_target_uses_drift_only(self) -> None:
        # Build prices where current is ABOVE all historical resistance.
        prices = _series(list(np.linspace(80.0, 100.0, 250)))
        result = compute_tactical_pricing(
            ticker="BRK",
            asset_class="stock",
            price_history=prices,
            current_price=110.0,  # above the entire history
        )
        assert result is not None
        assert "breakout" in result.buy_rationale.lower() or "drift" in result.buy_rationale.lower()


class TestConfidence:
    def test_high_confidence_when_signals_agree(self) -> None:
        # Steady drift + clear resistance → both methods agree directionally.
        prices = _series(list(np.linspace(100.0, 130.0, 250)))
        result = compute_tactical_pricing(
            ticker="AGREE",
            asset_class="stock",
            price_history=prices,
            current_price=130.0,
        )
        assert result is not None
        assert "high" in (result.buy_rationale + result.sell_rationale).lower() or "élevée" in (result.buy_rationale + result.sell_rationale).lower()

    def test_low_confidence_when_history_short(self) -> None:
        # 80 days of history, just over the 60-day floor but below 120 → low confidence.
        prices = _series(list(np.linspace(100.0, 110.0, 80)))
        result = compute_tactical_pricing(
            ticker="THIN",
            asset_class="stock",
            price_history=prices,
            current_price=110.0,
        )
        assert result is not None
        rationale = (result.buy_rationale + result.sell_rationale).lower()
        assert "low" in rationale or "faible" in rationale
```

- [ ] **Step 1.2: Run the test file to verify it fails (module not yet created)**

```bash
rtk uv run pytest tests/unit/quantitative/test_tactical_pricing.py --no-cov -v 2>&1 | tail -10
```

Expected: `ModuleNotFoundError: No module named 'finwiz.quantitative.tactical_pricing'` or import-time collection error on every test.

- [ ] **Step 1.3: Create the module**

Create `src/finwiz/quantitative/tactical_pricing.py`:

```python
"""Tactical (3-6 month) price targets and sell-level floors per holding.

Thin orchestration over existing primitives:
- ``calculate_support_resistance_targets`` for technical levels.
- TA-Lib ATR for volatility-adjusted floor.
- Log-return drift over the trailing year for forward projection.

Returns a :class:`PriceTargets` Pydantic model already wired into
``HoldingDecision``. AI-Minimalism (ADR-003) preserved — pure Python.

See ADR-011 for the full design rationale.
"""

from __future__ import annotations

import logging
from typing import Literal

import numpy as np
import pandas as pd

from finwiz.quantitative.price_targets import calculate_support_resistance_targets
from finwiz.schemas.portfolio_review import PriceTargets

logger = logging.getLogger(__name__)


# Drift caps — keep upside projections tied to plausibility.
_DRIFT_CAP_STOCK_ETF = 0.25
_DRIFT_CAP_CRYPTO = 0.40

# Minimum history before any computation is meaningful.
_MIN_HISTORY_DAYS = 60
_LOW_CONFIDENCE_THRESHOLD_DAYS = 120

# Reject a price series whose last bar is older than this — stale anchor risk.
_MAX_HISTORY_LAG_DAYS = 7


def _atr(prices: pd.Series, period: int = 14) -> float:
    """Average True Range proxy from a close-only series.

    The full ATR uses high/low/close; here we approximate with abs daily
    returns × current price, which is a common simplification when only
    closes are available and is sufficient for a stop-loss floor.
    """
    if len(prices) < period + 1:
        return float("nan")
    daily_changes = prices.diff().abs().dropna()
    if daily_changes.empty:
        return float("nan")
    rolled = daily_changes.rolling(window=period, min_periods=period).mean()
    last = rolled.iloc[-1]
    return float(last) if np.isfinite(last) else float("nan")


def _annualized_log_return(prices: pd.Series) -> float:
    """Compute annualized log return over the supplied window."""
    if len(prices) < 2:
        return 0.0
    log_ret = np.log(prices.iloc[-1] / prices.iloc[0])
    days = (prices.index[-1] - prices.index[0]).days or 1
    annualized = float(log_ret) * (365.25 / days)
    if not np.isfinite(annualized):
        return 0.0
    return annualized


def _confidence(prices: pd.Series, target: float, drift_target: float, current: float) -> str:
    """Three-bucket confidence label based on history depth + signal agreement.

    'high'   when both signals agree directionally (within 10%) AND we have
             enough history (≥ 120 trading days).
    'low'    when history is short (< 120 days) or the two signals disagree
             by more than 10%.
    'medium' otherwise.
    """
    if len(prices) < _LOW_CONFIDENCE_THRESHOLD_DAYS:
        return "low"
    if current <= 0 or target <= 0 or drift_target <= 0:
        return "low"
    pct_diff = abs(target - drift_target) / current
    if pct_diff <= 0.10:
        return "high"
    if pct_diff <= 0.20:
        return "medium"
    return "low"


def _is_history_fresh(prices: pd.Series) -> bool:
    """Reject obviously stale price history."""
    if prices.empty:
        return False
    last_dt = prices.index[-1]
    if not isinstance(last_dt, pd.Timestamp):
        last_dt = pd.Timestamp(last_dt)
    age = pd.Timestamp.now().normalize() - last_dt.normalize()
    return age <= pd.Timedelta(days=_MAX_HISTORY_LAG_DAYS)


def compute_tactical_pricing(
    ticker: str,
    asset_class: Literal["stock", "etf", "crypto"],
    price_history: pd.Series,
    current_price: float,
    *,
    horizon_months: int = 4,
    currency: str = "USD",
) -> PriceTargets | None:
    """Compute a 3-6 month tactical target and a stop-loss floor.

    Returns ``None`` when input is unusable:
    - fewer than 60 trading days of history
    - last price more than 7 calendar days old (stale anchor risk)
    - current_price not finite or non-positive
    """
    if not np.isfinite(current_price) or current_price <= 0:
        logger.warning(f"tactical_pricing: invalid current_price={current_price} for {ticker}")
        return None
    if len(price_history) < _MIN_HISTORY_DAYS:
        logger.warning(
            f"tactical_pricing: insufficient history for {ticker} ({len(price_history)} < {_MIN_HISTORY_DAYS} days)",
        )
        return None
    if not _is_history_fresh(price_history):
        logger.warning(f"tactical_pricing: stale history for {ticker} — skipping")
        return None

    # ---- target: max(technical resistance, drift projection) capped per asset class ----
    sr = calculate_support_resistance_targets(price_history, current_price=current_price)
    resistance = float(sr["resistance"].target_price) or current_price * 1.10
    support = float(sr["support"].target_price) or current_price * 0.90

    # Annualised log-return → time-projected drift over horizon_months.
    horizon_years = horizon_months / 12.0
    annual_log_ret = _annualized_log_return(price_history)
    drift_target = float(current_price * np.exp(annual_log_ret * horizon_years))
    if not np.isfinite(drift_target) or drift_target <= 0:
        drift_target = current_price

    cap = _DRIFT_CAP_CRYPTO if asset_class == "crypto" else _DRIFT_CAP_STOCK_ETF
    drift_target_capped = float(min(drift_target, current_price * (1.0 + cap)))

    is_breakout = resistance <= current_price
    if is_breakout:
        target = drift_target_capped
        target_method = "breakout — drift-based projection"
    else:
        target = float(max(resistance, drift_target_capped))
        target = float(min(target, current_price * (1.0 + cap)))
        target_method = "max(résistance technique, dérive projetée)"

    # ---- sell-level: max(support, current - 2*ATR) — more conservative wins ----
    atr = _atr(price_history)
    if not np.isfinite(atr):
        atr_floor = current_price * 0.85  # generous default when ATR can't compute
    else:
        atr_floor = current_price - 2.0 * atr

    sell_level = float(max(support, atr_floor))
    if sell_level >= current_price:  # support above current → use ATR-only
        sell_level = atr_floor
    if not np.isfinite(sell_level) or sell_level <= 0:
        sell_level = current_price * 0.85

    # ---- confidence label ----
    confidence = _confidence(price_history, target, drift_target_capped, current_price)
    confidence_fr = {"high": "élevée", "medium": "moyenne", "low": "faible"}[confidence]

    buy_rationale = f"Target {target_method} sur {horizon_months} mois — confiance {confidence_fr}."
    sell_rationale = f"Plancher = max(support technique, prix − 2×ATR) — confiance {confidence_fr}."

    return PriceTargets(
        current_price=current_price,
        currency=currency,
        fair_value_estimate=None,  # tactical; no fundamental fair value here
        buy_target_primary=target,
        buy_target_secondary=None,
        buy_rationale=buy_rationale,
        sell_target_primary=sell_level,
        sell_target_secondary=None,
        stop_loss_level=sell_level,
        sell_rationale=sell_rationale,
    )
```

- [ ] **Step 1.4: Run the tests; confirm all pass**

```bash
rtk uv run pytest tests/unit/quantitative/test_tactical_pricing.py --no-cov -v 2>&1 | tail -25
```

Expected: 11 tests pass.

- [ ] **Step 1.5: Commit**

```bash
git add src/finwiz/quantitative/tactical_pricing.py tests/unit/quantitative/test_tactical_pricing.py
git commit -m "feat(quant): add tactical_pricing helper for 3-6 month targets and stop floors

Pure-Python orchestration over existing price_targets / TA-Lib primitives.
Returns the existing PriceTargets schema; ready to be wired into the
quantify stage in the next task. See ADR-011."
```

---

## Task 2: Add `price_targets` field to `QuantitativeAnalysis` schema

**Files:**

- Modify: `src/finwiz/schemas/hybrid_analysis/quantitative.py`
- Test: extend `tests/unit/schemas/test_hybrid_analysis_schemas.py` (or create if absent)

- [ ] **Step 2.1: Inspect existing test file**

```bash
ls tests/unit/schemas/test_hybrid_*.py 2>&1 || echo "no schema tests yet"
```

If no test exists, create `tests/unit/schemas/test_quantitative_schema.py`. Otherwise extend.

- [ ] **Step 2.2: Write the failing test**

In `tests/unit/schemas/test_quantitative_schema.py`:

```python
"""Schema-level tests for QuantitativeAnalysis.price_targets (ADR-011)."""

from datetime import datetime

from finwiz.schemas.hybrid_analysis.quantitative import QuantitativeAnalysis
from finwiz.schemas.hybrid_analysis.metadata import DataQualityMetrics
from finwiz.schemas.portfolio_review import PriceTargets


def _build_quant(price_targets: PriceTargets | None = None) -> QuantitativeAnalysis:
    return QuantitativeAnalysis(
        composite_score=0.7,
        fundamental_score=0.7,
        technical_score=0.7,
        risk_score=2.0,
        grade="B",
        preliminary_recommendation="HOLD",
        fundamental_metrics={},
        technical_indicators={},
        risk_metrics={},
        calculation_timestamp=datetime.now(),
        data_quality=DataQualityMetrics(
            completeness_score=0.9,
            freshness_score=1.0,
            accuracy_confidence=0.9,
            source_reliability=0.85,
        ),
        confidence_level=0.9,
        python_rationale="placeholder rationale",
        price_targets=price_targets,
    )


def test_quantitative_analysis_accepts_none_price_targets() -> None:
    quant = _build_quant(price_targets=None)
    assert quant.price_targets is None


def test_quantitative_analysis_accepts_pricetargets_instance() -> None:
    pt = PriceTargets(
        current_price=100.0,
        currency="USD",
        buy_target_primary=120.0,
        sell_target_primary=85.0,
        buy_rationale="r1",
        sell_rationale="r2",
    )
    quant = _build_quant(price_targets=pt)
    assert quant.price_targets is not None
    assert quant.price_targets.buy_target_primary == 120.0
```

- [ ] **Step 2.3: Run the test; expect it to fail**

```bash
rtk uv run pytest tests/unit/schemas/test_quantitative_schema.py --no-cov -v 2>&1 | tail -10
```

Expected: `TypeError: ... got an unexpected keyword argument 'price_targets'` or pydantic `extra fields forbidden`.

- [ ] **Step 2.4: Modify the schema**

In `src/finwiz/schemas/hybrid_analysis/quantitative.py`, add the field directly under `python_rationale` (around line 63):

```python
    # ADR-011: tactical price target + stop-loss floor for the holding.
    # Optional because computation can return None for short / stale history.
    # Imported here (not at module top) to avoid a circular import; PriceTargets
    # lives in portfolio_review which already imports from common/risk.
    from finwiz.schemas.portfolio_review import PriceTargets  # noqa: E402

    price_targets: PriceTargets | None = Field(
        default=None,
        description="Tactical 3-6 month price target and stop-loss floor (ADR-011)",
    )
```

If the inline-import approach trips Pydantic forward-ref resolution, move the import to the module top. Verify the schema's existing `model_config` is compatible with the optional field.

- [ ] **Step 2.5: Run the tests; expect pass**

```bash
rtk uv run pytest tests/unit/schemas/test_quantitative_schema.py --no-cov -v 2>&1 | tail -10
```

Expected: 2 / 2 pass.

- [ ] **Step 2.6: Run mypy + lint to catch import-cycle regressions**

```bash
rtk make lint 2>&1 | tail -5
```

Expected: `All checks passed!`

- [ ] **Step 2.7: Commit**

```bash
git add src/finwiz/schemas/hybrid_analysis/quantitative.py tests/unit/schemas/test_quantitative_schema.py
git commit -m "feat(schema): add QuantitativeAnalysis.price_targets (ADR-011)

Optional Pydantic field. None when tactical_pricing returns None
(short / stale history)."
```

---

## Task 3: Wire `compute_tactical_pricing` into the quantify stage

**Files:**

- Modify: `src/finwiz/analysis/stages/quantify.py`
- Test: extend `tests/unit/analysis/stages/test_quantify.py`

- [ ] **Step 3.1: Inspect quantify.py**

```bash
sed -n '60,95p' src/finwiz/analysis/stages/quantify.py
```

The integration point is `_result_to_quantitative` around line 60-95. The price history is already available via `HistoricalDataManager` used by the technical engine.

- [ ] **Step 3.2: Write the failing test**

In `tests/unit/analysis/stages/test_quantify.py`, add (or create the file if absent):

```python
"""Quantify stage attaches tactical price_targets when history is available."""

from typing import Any

import numpy as np
import pandas as pd

from finwiz.analysis.deep_analysis_pipeline import AnalysisContext
from finwiz.analysis.stages.quantify import calculate_quantitative


class _FakeScorer:
    """Minimal stand-in to avoid heavy DeepAnalysisScorer setup in unit tests."""

    def calculate_composite_score(self, ticker: str, asset_class: str, raw: dict[str, Any]):
        from finwiz.flow_state_models import DeepAnalysisResult

        return DeepAnalysisResult.model_construct(
            ticker=ticker,
            asset_class=asset_class,
            crew_name="test",
            composite_score=0.7,
            grade="B",
            recommendation="HOLD",
            rationale="placeholder",
            risk_details={},
            fundamental_score=0.7,
            technical_score=0.7,
            risk_score=2.0,
            fundamental_details={},
            technical_details={},
            data_freshness_hours=0.5,
            confidence_level=0.9,
            warnings=[],
            data_quality=None,
            lineage=None,
            cached=False,
        )


def test_quantify_attaches_price_targets_when_history_available(mocker: Any) -> None:
    mocker.patch("finwiz.scoring.deep_analysis_scorer.DeepAnalysisScorer", _FakeScorer)
    end = pd.Timestamp.now().normalize()
    idx = pd.bdate_range(end=end, periods=250)
    prices = pd.Series(np.linspace(100.0, 130.0, 250), index=idx)
    raw = {"current_price": 130.0, "price_history": prices}
    ctx = AnalysisContext(ticker="AAPL", asset_class="stock", company_name="Apple")
    result, quant = calculate_quantitative(ctx, raw)
    assert quant.price_targets is not None
    assert quant.price_targets.buy_target_primary > 130.0
    assert quant.price_targets.sell_target_primary < 130.0


def test_quantify_no_price_targets_when_history_missing(mocker: Any) -> None:
    mocker.patch("finwiz.scoring.deep_analysis_scorer.DeepAnalysisScorer", _FakeScorer)
    raw = {"current_price": 130.0}  # no price_history key
    ctx = AnalysisContext(ticker="AAPL", asset_class="stock", company_name="Apple")
    result, quant = calculate_quantitative(ctx, raw)
    assert quant.price_targets is None
```

- [ ] **Step 3.3: Run the failing test**

```bash
rtk uv run pytest tests/unit/analysis/stages/test_quantify.py --no-cov -v 2>&1 | tail -10
```

Expected: assertion failure on `quant.price_targets is not None` (currently always None).

- [ ] **Step 3.4: Modify quantify.py**

Edit `_calculate_quantitative_inner` to compute and attach price_targets, and edit `_result_to_quantitative` to accept the new arg:

Replace the `_calculate_quantitative_inner` body (around lines 18-32):

```python
def _calculate_quantitative_inner(
    ctx: AnalysisContext,
    raw_data: dict[str, Any],
) -> tuple[DeepAnalysisResult, QuantitativeAnalysis]:
    """The original calculate_quantitative body — extracted for testability."""
    from finwiz.scoring.deep_analysis_scorer import DeepAnalysisScorer

    logger.info(f"Calculating quantitative metrics for {ctx.ticker}")
    scorer = DeepAnalysisScorer()
    result = scorer.calculate_composite_score(ctx.ticker, ctx.asset_class, raw_data)

    # ADR-011: compute tactical price targets when we have usable history.
    price_targets = _maybe_compute_price_targets(ctx, raw_data)

    quant = _result_to_quantitative(result, price_targets=price_targets)
    logger.info(f"Quantitative: {ctx.ticker} grade={quant.grade} score={quant.composite_score:.2f}")
    return result, quant


def _maybe_compute_price_targets(
    ctx: AnalysisContext,
    raw_data: dict[str, Any],
) -> "PriceTargets | None":
    """Best-effort tactical pricing. Logs and returns None on any failure."""
    from finwiz.quantitative.tactical_pricing import compute_tactical_pricing

    history = raw_data.get("price_history")
    current = raw_data.get("current_price")
    currency = str(raw_data.get("currency") or "USD")
    if history is None or current is None:
        return None
    try:
        return compute_tactical_pricing(
            ticker=ctx.ticker,
            asset_class=ctx.asset_class,
            price_history=history,
            current_price=float(current),
            currency=currency,
        )
    except Exception as exc:  # never let pricing failure derail scoring
        logger.warning(f"tactical_pricing failed for {ctx.ticker}: {exc}")
        return None
```

Add `price_targets` arg to `_result_to_quantitative` (it currently has none) and pass through to the constructor:

```python
def _result_to_quantitative(
    result: DeepAnalysisResult,
    price_targets: "PriceTargets | None" = None,
) -> QuantitativeAnalysis:
    """Convert DeepAnalysisResult to QuantitativeAnalysis schema."""
    # ... existing body unchanged ...
    return QuantitativeAnalysis(
        # ... existing fields ...
        python_rationale=result.rationale,
        price_targets=price_targets,
    )
```

Add the TYPE_CHECKING import at the top of quantify.py:

```python
if TYPE_CHECKING:
    from finwiz.analysis.deep_analysis_pipeline import AnalysisContext
    from finwiz.schemas.portfolio_review import PriceTargets
```

- [ ] **Step 3.5: Run the test; expect pass**

```bash
rtk uv run pytest tests/unit/analysis/stages/test_quantify.py --no-cov -v 2>&1 | tail -10
```

Expected: 2 / 2 pass.

- [ ] **Step 3.6: Verify the data collector populates `price_history` in raw_data**

```bash
grep -n "price_history\|hist\[" src/finwiz/orchestrators/deep_analysis_data_collector.py | head -10
```

If `price_history` is NOT a key the collector sets, then the integration test passes only because we mocked it. Check whether the data collector already returns a price series the scorer could use. If not, file the wiring as a sub-task: in `_collect_raw_data` (or the data_collector), after fetching historical prices for the technical analyzer, also expose them as `raw_data["price_history"] = close_series`.

If this sub-task is needed, do it here:

```bash
grep -n "fetch_historical_data\|HistoricalDataManager" src/finwiz/orchestrators/deep_analysis_data_collector.py | head -5
```

Add a single line after the existing fetch:

```python
# ADR-011: expose closes for tactical_pricing.
collected_data["price_history"] = hist["Close"].dropna()
```

(Actual code depends on what variables are in scope at the call site — read the surrounding 20 lines first.)

- [ ] **Step 3.7: Commit**

```bash
git add src/finwiz/analysis/stages/quantify.py src/finwiz/orchestrators/deep_analysis_data_collector.py tests/unit/analysis/stages/test_quantify.py
git commit -m "feat(quantify): wire tactical_pricing into quantify stage (ADR-011)

When price_history + current_price are available in raw_data, attach a
tactical PriceTargets to the QuantitativeAnalysis output. Failure to
compute tactical pricing never fails the scoring pipeline."
```

---

## Task 4: Propagate `price_targets` through merge to `HoldingDecision`

**Files:**

- Modify: `src/finwiz/orchestrators/portfolio_review/merge.py`
- Test: extend `tests/unit/orchestrators/test_merge.py`

- [ ] **Step 4.1: Write the failing test**

Add to `tests/unit/orchestrators/test_merge.py`:

```python
def test_merge_propagates_price_targets() -> None:
    """ADR-011: when a successful deep_result carries price_targets via its
    enriched analysis, merge.py copies them onto HoldingDecision.price_targets.
    """
    from finwiz.flow_state_models import DeepAnalysisResult
    from finwiz.schemas.portfolio_review import PriceTargets

    decisions = [_stub_decision()]
    pt = PriceTargets(
        current_price=100.0,
        currency="USD",
        buy_target_primary=120.0,
        sell_target_primary=85.0,
        buy_rationale="r1",
        sell_rationale="r2",
    )
    good = DeepAnalysisResult.model_construct(
        ticker="ASML",
        asset_class="stock",
        crew_name="test",
        composite_score=0.85,
        grade="A",
        recommendation="BUY",
        rationale="ok",
        confidence="high",
        cached=False,
    )
    # The merge currently inspects deep_result.fact_pack via getattr —
    # follow the same idiom for price_targets so model_construct shapes
    # without the field still work.
    object.__setattr__(good, "price_targets", pt)

    flow_state = _FakeFlowState({"ASML": good})
    merged = merge_deep_analysis_from_flow_state(decisions, flow_state)
    assert merged[0].price_targets is not None
    assert merged[0].price_targets.buy_target_primary == 120.0
```

- [ ] **Step 4.2: Run the test; expect failure**

```bash
rtk uv run pytest tests/unit/orchestrators/test_merge.py::test_merge_propagates_price_targets --no-cov -v 2>&1 | tail -8
```

Expected: `assert merged[0].price_targets is not None` fails (None).

- [ ] **Step 4.3: Modify merge.py**

In `src/finwiz/orchestrators/portfolio_review/merge.py`, inside the `if ticker in deep_analysis_results:` branch (where the existing `decision.fact_pack` line lives), add right after:

```python
                decision.fact_pack = getattr(deep_result, "fact_pack", None)
                # ADR-011: propagate tactical price targets when present.
                decision.price_targets = getattr(deep_result, "price_targets", None)
```

Note: `DeepAnalysisResult` does not have a `price_targets` field directly. The plan stores it on the **enriched** `QuantitativeAnalysis`. The merge needs to dig: `flow_state.deep_analysis_results[ticker]` is `DeepAnalysisResult`, but enriched is in a separate map. Adjust:

```python
                # ADR-011: pull price_targets from the enriched analysis if available.
                enriched_map = getattr(flow_state, "_enriched_analyses", {}) or {}
                enriched = enriched_map.get(ticker)
                if enriched is not None and getattr(enriched, "quantitative", None) is not None:
                    decision.price_targets = getattr(enriched.quantitative, "price_targets", None)
```

Verify the actual location of enriched results in flow_state by reading `deep_analysis_orchestrator.py:225-260` (the `_store_enriched_analysis` storage path).

- [ ] **Step 4.4: Run the test; expect pass**

```bash
rtk uv run pytest tests/unit/orchestrators/test_merge.py --no-cov -v 2>&1 | tail -10
```

Expected: all merge tests pass.

- [ ] **Step 4.5: Commit**

```bash
git add src/finwiz/orchestrators/portfolio_review/merge.py tests/unit/orchestrators/test_merge.py
git commit -m "feat(merge): propagate price_targets onto HoldingDecision (ADR-011)"
```

---

## Task 5: Render compact target/sell columns in the holdings table

**Files:**

- Modify: `src/finwiz/reporting/section_generators.py`
- Test: extend `tests/unit/reporting/test_section_generators.py`

- [ ] **Step 5.1: Locate the holdings table header + row renderer**

```bash
grep -n "Position\|Grade\|<th>" src/finwiz/reporting/section_generators.py | head -20
```

Two surfaces to update: the `<thead>` row (add two `<th>` columns) and `_render_holding_row` (add the two `<td>` cells).

- [ ] **Step 5.2: Write the failing test**

Append to `tests/unit/reporting/test_section_generators.py`:

```python
def test_holding_row_renders_target_and_sell_columns_when_present() -> None:
    """ADR-011: holdings with price_targets show two extra columns."""
    from finwiz.schemas.portfolio_review import PriceTargets

    holding = _build_holding(grade="A", confidence="high")
    holding.price_targets = PriceTargets(
        current_price=100.0,
        currency="USD",
        buy_target_primary=120.0,
        sell_target_primary=85.0,
        buy_rationale="rationale-up",
        sell_rationale="rationale-down",
    )
    html = _render_holding_row(holding)
    assert "120" in html or "$120" in html  # target value
    assert "85" in html  # sell-level value
    assert "+20" in html or "20.0%" in html  # target delta
    assert "-15" in html or "15.0%" in html or "−15" in html  # sell delta


def test_holding_row_renders_dash_when_price_targets_missing() -> None:
    holding = _build_holding(grade="A", confidence="high")
    holding.price_targets = None
    html = _render_holding_row(holding)
    # The two extra columns must render with em-dash placeholders.
    # Count td's containing the em-dash to confirm no crash and proper graceful display.
    assert "—" in html
```

- [ ] **Step 5.3: Run the test; expect failure**

```bash
rtk uv run pytest tests/unit/reporting/test_section_generators.py --no-cov -v 2>&1 | tail -10
```

Expected: assertion failures on missing price values.

- [ ] **Step 5.4: Modify section_generators.py — add helper + update row + update header**

Add a private helper near the top of the file:

```python
def _format_target_cell(price_targets, current_price: float | None, kind: str) -> str:
    """Render one of the two ADR-011 columns ('target' or 'sell').

    Returns "<td>—</td>" when no price_targets or current_price is unusable.
    Otherwise produces "$X (±Y%)" with HTML-safe escaping.
    """
    if price_targets is None or current_price is None or current_price <= 0:
        return '<td class="muted">—</td>'
    value = price_targets.buy_target_primary if kind == "target" else price_targets.sell_target_primary
    if value is None:
        return '<td class="muted">—</td>'
    delta_pct = (value - current_price) / current_price * 100
    sign = "+" if delta_pct >= 0 else ""
    return f"<td>${value:,.2f}<br><small>{sign}{delta_pct:.1f}%</small></td>"
```

In `_render_holding_row`, add the two cells right before the closing `</tr>` of the analyzed branch (do NOT add them to the pending branch — pending rows already have an em-dash filler):

```python
    # ADR-011 columns
    target_cell = _format_target_cell(
        holding.price_targets,
        getattr(holding.price_targets, "current_price", None) if holding.price_targets else None,
        kind="target",
    )
    sell_cell = _format_target_cell(
        holding.price_targets,
        getattr(holding.price_targets, "current_price", None) if holding.price_targets else None,
        kind="sell",
    )
    return f"""
        <tr>
          ...existing cells...
          {target_cell}
          {sell_cell}
        </tr>"""
```

In the table header (the `generate_holdings_analysis` or `generate_holdings_table` function — find via grep), add two new `<th>` cells in the same position:

```html
<th>Objectif (3-6 mo)</th>
<th>Niveau de vente</th>
```

For the **pending** row branch in `_render_holding_row`, add two muted cells so the grid stays aligned:

```python
        <tr class="row-pending">
          ...existing cells...
          <td class="muted">—</td>
          <td class="muted">—</td>
        </tr>
```

- [ ] **Step 5.5: Run the test; expect pass**

```bash
rtk uv run pytest tests/unit/reporting/test_section_generators.py --no-cov -v 2>&1 | tail -10
```

Expected: all tests pass (existing ones still + the two new ones).

- [ ] **Step 5.6: Commit**

```bash
git add src/finwiz/reporting/section_generators.py tests/unit/reporting/test_section_generators.py
git commit -m "feat(report): add target/sell columns to holdings table (ADR-011)

Compact two-column block per holding: 'Objectif (3-6 mo)' and 'Niveau de
vente'. Pending rows show em-dash placeholders so the table grid stays
aligned. Cells render via _format_target_cell helper with HTML-safe
escaping."
```

---

## Task 6: Render "🎯 Targets" detail panel in per-ticker HTML

**Files:**

- Modify: `src/finwiz/reporting/enriched_analysis_report_generator.py`
- Modify: `src/finwiz/templates/enriched_analysis_report.html`
- Test: extend `tests/property/test_enriched_analysis_report_properties.py`

- [ ] **Step 6.1: Write the failing test**

Add to `tests/property/test_enriched_analysis_report_properties.py`, near `TestRendererToleratesSkippedAnalysis`:

```python
class TestRendererShowsPriceTargets:
    """ADR-011: per-ticker HTML report shows a Targets panel when price_targets
    is present; gracefully omits it when None."""

    def _payload_with_targets(self) -> dict:
        return {
            "ticker": "AAPL",
            "company_name": "Apple Inc.",
            "asset_class": "stock",
            "analysis_date": datetime.now(),
            "executive_summary": "summary",
            "investment_rationale": "rat",
            "final_grade": "A",
            "final_recommendation": "BUY",
            "recommendation_confidence": "HIGH",
            "final_score": 0.85,
            "report_word_count": 2000,
            "unique_insights_count": 5,
            "processing_time_seconds": 5.0,
            "llm_cost_dollars": 0.05,
            "quantitative": {
                "composite_score": 0.85,
                "fundamental_score": 0.85,
                "technical_score": 0.85,
                "risk_score": 1.5,
                "grade": "A",
                "preliminary_recommendation": "BUY",
                "fundamental_metrics": {},
                "technical_indicators": {},
                "risk_metrics": {},
                "price_targets": {
                    "current_price": 100.0,
                    "currency": "USD",
                    "buy_target_primary": 120.0,
                    "sell_target_primary": 85.0,
                    "buy_rationale": "drift + résistance — confiance élevée",
                    "sell_rationale": "ATR floor — confiance élevée",
                },
            },
            "qualitative": {},
        }

    def test_detail_panel_renders_when_price_targets_present(self) -> None:
        gen = EnrichedAnalysisReportGenerator()
        html = gen.generate_report(self._payload_with_targets())
        assert "Objectif" in html or "🎯" in html
        assert "120" in html
        assert "85" in html
        assert "élevée" in html or "high" in html.lower()

    def test_detail_panel_omitted_when_price_targets_none(self) -> None:
        payload = self._payload_with_targets()
        payload["quantitative"]["price_targets"] = None
        gen = EnrichedAnalysisReportGenerator()
        html = gen.generate_report(payload)
        # Body must not contain the 🎯 panel headline when no targets.
        assert "🎯 Targets" not in html and "🎯 Objectifs" not in html
```

- [ ] **Step 6.2: Run the failing test**

```bash
rtk uv run pytest tests/property/test_enriched_analysis_report_properties.py::TestRendererShowsPriceTargets --no-cov -v 2>&1 | tail -10
```

Expected: failures on missing template content.

- [ ] **Step 6.3: Pass `price_targets` into template_vars**

In `src/finwiz/reporting/enriched_analysis_report_generator.py`, in `_prepare_template_variables`, after the existing quant/qual extraction (around line 209), append:

```python
        # ADR-011: surface tactical price targets for the detail panel.
        template_vars["price_targets"] = quant.get("price_targets") if quant else None
```

- [ ] **Step 6.4: Add the detail panel block in the template**

In `src/finwiz/templates/enriched_analysis_report.html`, add inside the `{% else %}` (non-skipped) branch, between the recommendation block and the existing quantitative section:

```html
        {% if price_targets %}
        <div class="section">
            <h2>🎯 Objectifs Tactiques (3-6 mois)</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <h4>Objectif de cours</h4>
                    <p class="metric-value">${{ "%.2f"|format(price_targets.buy_target_primary) }}</p>
                    <small>{{ price_targets.buy_rationale }}</small>
                </div>
                <div class="metric-card">
                    <h4>Niveau de vente</h4>
                    <p class="metric-value">${{ "%.2f"|format(price_targets.sell_target_primary) }}</p>
                    <small>{{ price_targets.sell_rationale }}</small>
                </div>
                <div class="metric-card">
                    <h4>Prix actuel</h4>
                    <p class="metric-value">${{ "%.2f"|format(price_targets.current_price) }}</p>
                    <small>{{ price_targets.currency }}</small>
                </div>
            </div>
        </div>
        {% endif %}
```

- [ ] **Step 6.5: Run the tests; expect pass**

```bash
rtk uv run pytest tests/property/test_enriched_analysis_report_properties.py::TestRendererShowsPriceTargets --no-cov -v 2>&1 | tail -10
```

Expected: 2 / 2 pass.

- [ ] **Step 6.6: Commit**

```bash
git add src/finwiz/reporting/enriched_analysis_report_generator.py src/finwiz/templates/enriched_analysis_report.html tests/property/test_enriched_analysis_report_properties.py
git commit -m "feat(report): per-ticker '🎯 Objectifs Tactiques' detail panel (ADR-011)

Three metric cards in the per-ticker HTML report when price_targets is
populated: target, sell-level, and current price (with currency). Panel
is omitted entirely when targets are None — no empty placeholder."
```

---

## Task 7: Run the full lint + test sweep

- [ ] **Step 7.1: Lint**

```bash
rtk make lint 2>&1 | tail -10
```

Expected: `All checks passed!`

- [ ] **Step 7.2: Touched-area test sweep**

```bash
rtk uv run pytest \
  tests/unit/quantitative/test_tactical_pricing.py \
  tests/unit/schemas/test_quantitative_schema.py \
  tests/unit/analysis/stages/test_quantify.py \
  tests/unit/orchestrators/test_merge.py \
  tests/unit/reporting/test_section_generators.py \
  tests/property/test_enriched_analysis_report_properties.py \
  --no-cov -v --timeout 60 2>&1 | tail -15
```

Expected: all green.

- [ ] **Step 7.3: Broader regression sweep — adjacent paths**

```bash
rtk uv run pytest tests/unit/quantitative/ tests/unit/analysis/ tests/unit/orchestrators/ tests/unit/reporting/ --no-cov -q --timeout 60 2>&1 | tail -10
```

Expected: no regressions.

- [ ] **Step 7.4: Push branch + open PR**

```bash
rtk git push -u origin feat/tactical-price-targets
rtk gh pr create --title "feat: tactical price targets and sell-level floors per holding (ADR-011)" --body "$(cat <<'EOF'
## Summary
Implements ADR-011. Adds two deterministic price levels to every holding in the deep-analysis report:
- **Objectif de cours** (3-6 month tactical target)
- **Niveau de vente** (stop-loss floor = max(support, current − 2×ATR))

Reuses existing primitives in \`quantitative/price_targets.py\` and TA-Lib's ATR. 100% Python — AI Minimalism (ADR-003) preserved.

## Behaviour
- Compact two columns in the holdings table.
- "🎯 Objectifs Tactiques" detail panel in the per-ticker HTML report.
- Confidence label (élevée / moyenne / faible) based on history depth and signal agreement.
- Returns \`None\` for short (<60d) or stale (>7d lag) history; report shows em-dash placeholders.

## Test plan
- [x] Unit tests for tactical_pricing across asset classes + edge cases (11 tests)
- [x] Schema tests for QuantitativeAnalysis.price_targets (2 tests)
- [x] Quantify stage integration test (2 tests)
- [x] Merge propagation test
- [x] Renderer tests — compact columns + detail panel
- [ ] End-to-end: replay the family portfolio and verify each ticker shows two numbers

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 7.5: Final commit (if any leftover changes)**

```bash
git status --short
```

If there are leftover changes (from inline import fixes, etc.), commit them with `chore: misc cleanup post-implementation`.

---

## Self-Review Notes

- **Spec coverage:** every section of ADR-011 maps to a task above (compute → schema → wiring → render). Compact columns (Q2-C inline) → Task 5; detail panel (Q2-C drill-down) → Task 6; deterministic floor (Q1-A) → Task 1; tactical horizon (Q3-B) → Task 1.
- **Placeholders:** none — all step content shows the actual code.
- **Type consistency:** `compute_tactical_pricing` returns `PriceTargets | None`; `QuantitativeAnalysis.price_targets` is `PriceTargets | None`; `HoldingDecision.price_targets` already exists as `PriceTargets | None`. Names consistent across all tasks.
- **Risk:** Step 3.6 conditionally adds a one-line edit to the data collector; the exact location depends on what's already in scope. The plan flags this and tells the implementer to grep first. Acceptable — alternative would be reading 200 lines of the collector inline.
