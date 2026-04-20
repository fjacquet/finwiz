"""Unit tests for ``MomentumScanner`` — asset-class plumbing.

Proves the coupled fix:
* Crypto universes cause yfinance to be queried with the ``-USD`` suffix.
* ``NewcomerCandidate.ticker`` stays bare (no ``-USD``) so domain output and
  report UIs are consistent with the rest of the product.
* ``NewcomerCandidate.asset_class`` reflects the scanned universe's asset
  class (no more hardcoded ``"stock"`` on crypto candidates).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import pytest

from finwiz.discovery.momentum_scanner import MomentumScanner


def _history_frame(length: int = 60) -> pd.DataFrame:
    """Synthetic price/volume history strong enough to clear the new quality gates.

    * Staircase trend (3 up, 1 down) → RSI settles in the active bullish band
      rather than saturating at 100.
    * +20% push over the final 10 bars → ROC clears the strong-signal threshold.
    * Final-bar volume spike (5x SMA) → volume anomaly saturates at 1.0.
    """
    pattern = [0.015, 0.015, 0.015, -0.005]
    closes = [100.0]
    for i in range(1, length):
        closes.append(closes[-1] * (1.0 + pattern[i % 4]))
    close_arr = np.array(closes, dtype=float)
    close_arr[-10:] *= np.linspace(1.0, 1.20, 10)
    volumes = np.full(length, 1_000_000, dtype=float)
    volumes[-1] = 5_000_000
    idx = pd.date_range("2026-01-01", periods=length, freq="D")
    return pd.DataFrame({"Close": close_arr, "Volume": volumes}, index=idx)


class _FakeTicker:
    """Minimal stand-in for ``yfinance.Ticker``."""

    def __init__(self, info: dict[str, Any] | None = None) -> None:
        # Default info carries strong fundamentals so the stock/ETF blend path
        # clears the fund-score floor in ``MomentumScanner._passes_quality_gate``.
        self.info = info or {
            "longName": "Fake Asset",
            "marketCap": 1_000_000_000,
            "returnOnEquity": 0.25,
            "revenueGrowth": 0.20,
            "profitMargins": 0.22,
            "debtToEquity": 30.0,
        }
        self._history = _history_frame()

    def history(self, period: str) -> pd.DataFrame:
        return self._history


class TestMomentumScannerAssetClass:
    """``asset_class`` must flow from caller → yfinance boundary → candidate."""

    def test_crypto_universe_queries_yfinance_with_usd_suffix(self, mocker: Any) -> None:
        ticker_factory = mocker.patch(
            "finwiz.discovery.momentum_scanner.yf.Ticker",
            return_value=_FakeTicker(),
        )

        scanner = MomentumScanner()
        candidates = scanner.scan(["BTC"], asset_class="crypto")

        ticker_factory.assert_called_once_with("BTC-USD")
        assert len(candidates) == 1
        assert candidates[0].ticker == "BTC", "domain ticker must stay bare"
        assert candidates[0].asset_class == "crypto"

    def test_stock_universe_queries_yfinance_without_suffix(self, mocker: Any) -> None:
        ticker_factory = mocker.patch(
            "finwiz.discovery.momentum_scanner.yf.Ticker",
            return_value=_FakeTicker(),
        )

        scanner = MomentumScanner()
        candidates = scanner.scan(["AAPL"], asset_class="stock")

        ticker_factory.assert_called_once_with("AAPL")
        assert len(candidates) == 1
        assert candidates[0].ticker == "AAPL"
        assert candidates[0].asset_class == "stock"

    def test_default_asset_class_is_stock(self, mocker: Any) -> None:
        """Calling ``scan(universe)`` without ``asset_class`` keeps legacy behavior."""
        mocker.patch(
            "finwiz.discovery.momentum_scanner.yf.Ticker",
            return_value=_FakeTicker(),
        )

        scanner = MomentumScanner()
        candidates = scanner.scan(["AAPL"])

        assert candidates and candidates[0].asset_class == "stock"

    @pytest.mark.parametrize(
        ("bare", "expected_query"),
        [("AAVE", "AAVE-USD"), ("DOGE", "DOGE-USD"), ("SOL", "SOL-USD")],
    )
    def test_multiple_crypto_tickers_all_normalized(
        self,
        mocker: Any,
        bare: str,
        expected_query: str,
    ) -> None:
        ticker_factory = mocker.patch(
            "finwiz.discovery.momentum_scanner.yf.Ticker",
            return_value=_FakeTicker(),
        )

        MomentumScanner().scan([bare], asset_class="crypto")

        ticker_factory.assert_called_once_with(expected_query)


def _weak_signal_history(length: int = 60) -> pd.DataFrame:
    """SUSHI/DLR-class history: flat-ish price, drifting volume — no real signal.

    * Near-flat closes → RSI hovers near 50, ROC well below 10%.
    * Volume roughly at SMA → volume anomaly sits in the neutral band.
    Every component lives below the strong-signal thresholds, so the quality
    gate must exclude the candidate rather than emit it with a low grade.
    """
    closes = np.linspace(100.0, 102.0, length)
    volumes = np.full(length, 1_000_000.0)
    idx = pd.date_range("2026-01-01", periods=length, freq="D")
    return pd.DataFrame({"Close": closes, "Volume": volumes}, index=idx)


class _WeakSignalTicker:
    """yfinance stand-in returning near-flat price/volume + strong fundamentals."""

    def __init__(self) -> None:
        self.info = {
            "longName": "Weak Signal Corp",
            "marketCap": 1_000_000_000,
            "returnOnEquity": 0.30,
            "revenueGrowth": 0.20,
            "profitMargins": 0.25,
            "debtToEquity": 25.0,
        }
        self._history = _weak_signal_history()

    def history(self, period: str) -> pd.DataFrame:
        return self._history


class _StrongTechnicalsBadFundamentalsTicker:
    """Strong momentum but objectively bad fundamentals — must be filtered."""

    def __init__(self) -> None:
        self.info = {
            "longName": "Cash Burn Corp",
            "marketCap": 500_000_000,
            "returnOnEquity": -0.40,
            "revenueGrowth": -0.25,
            "profitMargins": -0.35,
            "debtToEquity": 450.0,
        }
        self._history = _history_frame()

    def history(self, period: str) -> pd.DataFrame:
        return self._history


class TestMomentumScannerQualityGate:
    """Weak-signal candidates (SUSHI/DLR-class) must be excluded, not low-graded."""

    def test_weak_signal_crypto_excluded_from_output(self, mocker: Any) -> None:
        mocker.patch(
            "finwiz.discovery.momentum_scanner.yf.Ticker",
            return_value=_WeakSignalTicker(),
        )

        candidates = MomentumScanner().scan(["SUSHI"], asset_class="crypto")

        assert candidates == [], "weak-signal crypto must not appear in opportunity list"

    def test_weak_signal_stock_excluded_even_with_strong_fundamentals(self, mocker: Any) -> None:
        """A stock with no real technical signal cannot be rescued by fundamentals alone."""
        mocker.patch(
            "finwiz.discovery.momentum_scanner.yf.Ticker",
            return_value=_WeakSignalTicker(),
        )

        candidates = MomentumScanner().scan(["DLR"], asset_class="stock")

        assert candidates == []

    def test_strong_technicals_but_bad_fundamentals_excluded(self, mocker: Any) -> None:
        """The fundamentals floor drops momentum-only tickers with poor stock quality."""
        mocker.patch(
            "finwiz.discovery.momentum_scanner.yf.Ticker",
            return_value=_StrongTechnicalsBadFundamentalsTicker(),
        )

        candidates = MomentumScanner().scan(["BADCO"], asset_class="stock")

        assert candidates == []


class TestMomentumScannerFundamentalsBlend:
    """Stocks with usable fundamentals expose a blended composite + fund_score metadata."""

    def test_stock_candidate_records_fundamental_score_in_metadata(self, mocker: Any) -> None:
        mocker.patch(
            "finwiz.discovery.momentum_scanner.yf.Ticker",
            return_value=_FakeTicker(),
        )

        candidates = MomentumScanner().scan(["GOOG"], asset_class="stock")

        assert len(candidates) == 1
        candidate = candidates[0]
        # The blend must leave a trace so downstream tooling (and debug runs)
        # can tell that fundamentals actually contributed to the composite.
        assert "fundamental_score" in candidate.metadata
        assert "momentum_composite" in candidate.metadata
        assert 0.0 <= candidate.metadata["fundamental_score"] <= 1.0

    def test_crypto_candidate_omits_fundamental_score(self, mocker: Any) -> None:
        """Crypto has no fundamentals surface on yfinance — metadata must reflect that."""
        mocker.patch(
            "finwiz.discovery.momentum_scanner.yf.Ticker",
            return_value=_FakeTicker(),
        )

        candidates = MomentumScanner().scan(["BTC"], asset_class="crypto")

        assert len(candidates) == 1
        assert "fundamental_score" not in candidates[0].metadata
