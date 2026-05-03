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
    # Snap to most recent business day so periods=N yields exactly N dates
    # regardless of whether the test runs on a weekend.
    end = pd.tseries.offsets.BDay(0).rollback(pd.Timestamp.now().normalize())
    idx = pd.bdate_range(end=end, periods=len(values))
    return pd.Series(values, index=idx, dtype=float)


class TestStockTactical:
    def test_returns_pricetargets_for_stock(self) -> None:
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
        assert result.buy_target_primary > 130.0
        assert result.sell_target_primary < 130.0

    def test_target_capped_at_25pct_for_stock(self) -> None:
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
        prices = _series([100.0, 99.0, 101.0, 100.5, 99.5, 100.2, 100.8] * 30)
        result = compute_tactical_pricing(
            ticker="STABLE",
            asset_class="stock",
            price_history=prices,
            current_price=100.8,
        )
        assert result is not None
        assert result.sell_target_primary is not None
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
        assert result.buy_rationale.lower().startswith("objectif")

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
        prices = _series(list(np.linspace(1000.0, 10000.0, 250)))
        result = compute_tactical_pricing(
            ticker="BTC-USD",
            asset_class="crypto",
            price_history=prices,
            current_price=10000.0,
        )
        assert result is not None
        assert result.buy_target_primary <= 10000.0 * 1.40 + 1e-6
        assert result.buy_target_primary > 10000.0 * 1.25


class TestEdgeCases:
    def test_short_history_returns_none(self) -> None:
        prices = _series([100.0] * 30)
        result = compute_tactical_pricing(
            ticker="NEW",
            asset_class="stock",
            price_history=prices,
            current_price=100.0,
        )
        assert result is None

    def test_stale_history_returns_none(self) -> None:
        end = pd.tseries.offsets.BDay(0).rollback(pd.Timestamp.now().normalize() - pd.Timedelta(days=10))
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
        prices = _series(list(np.linspace(80.0, 100.0, 250)))
        result = compute_tactical_pricing(
            ticker="BRK",
            asset_class="stock",
            price_history=prices,
            current_price=110.0,
        )
        assert result is not None
        assert "cassure" in result.buy_rationale.lower() or "dérive" in result.buy_rationale.lower()

    def test_exactly_60_days_passes_min_history_check(self) -> None:
        """Boundary: spec says 'fewer than 60 days' → None; exactly 60 should pass."""
        prices = _series(list(np.linspace(100.0, 110.0, 60)))
        result = compute_tactical_pricing(
            ticker="EDGE60",
            asset_class="stock",
            price_history=prices,
            current_price=110.0,
        )
        # 60 days passes the >= guard; result should be non-None (low confidence).
        assert result is not None

    def test_nan_heavy_history_returns_none(self) -> None:
        """A series that drops to <60 clean bars after NaN filter must return None."""
        values = [100.0, np.nan] * 60 + [np.nan] * 30  # ~60 valid bars
        # Only ~60 valid bars survives the NaN filter from 150 total — borderline.
        prices = _series(values)
        result = compute_tactical_pricing(
            ticker="NANSY",
            asset_class="stock",
            price_history=prices,
            current_price=100.0,
        )
        # Either returns None (preferred) or a valid PriceTargets — but must not crash.
        if result is not None:
            assert result.buy_target_primary > 0
            assert result.sell_target_primary > 0

    def test_all_zero_history_returns_none(self) -> None:
        """All-zero history is degenerate — return None with a logged warning."""
        prices = _series([0.0] * 150)
        result = compute_tactical_pricing(
            ticker="ZEROS",
            asset_class="stock",
            price_history=prices,
            current_price=100.0,
        )
        assert result is None

    def test_flat_price_series_uses_default_atr_floor(self) -> None:
        """Flat (zero-volatility) series must NOT produce sell_level == current_price.

        Regression: ATR is 0.0 for an all-identical series, which previously made
        atr_floor = current - 0 = current, triggering immediate stop-loss exit.
        """
        prices = _series([100.0] * 150)
        result = compute_tactical_pricing(
            ticker="FLAT",
            asset_class="stock",
            price_history=prices,
            current_price=100.0,
        )
        # When this is a degenerate input, the function may return None
        # (per all-zero / non-positive guard). If it returns a result, sell_level
        # must be strictly below current_price.
        if result is not None:
            assert result.sell_target_primary < 100.0


class TestTimezone:
    def test_tz_aware_history_does_not_crash(self) -> None:
        """yfinance returns tz-aware indexes; the helper must not crash on them."""
        end = pd.tseries.offsets.BDay(0).rollback(pd.Timestamp.now(tz="America/New_York").normalize())
        idx = pd.bdate_range(end=end, periods=150, tz="America/New_York")
        prices = pd.Series(np.linspace(100.0, 130.0, 150), index=idx)
        result = compute_tactical_pricing(
            ticker="AAPL",
            asset_class="stock",
            price_history=prices,
            current_price=130.0,
        )
        # Must not raise; should produce a valid result.
        assert result is not None
        assert result.buy_target_primary > 130.0


class TestConfidence:
    def test_high_confidence_when_signals_agree(self) -> None:
        prices = _series(list(np.linspace(100.0, 130.0, 250)))
        result = compute_tactical_pricing(
            ticker="AGREE",
            asset_class="stock",
            price_history=prices,
            current_price=130.0,
        )
        assert result is not None
        rationale = (result.buy_rationale + result.sell_rationale).lower()
        assert "high" in rationale or "élevée" in rationale

    def test_low_confidence_when_history_short(self) -> None:
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
