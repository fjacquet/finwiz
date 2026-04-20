"""Unit tests for ``BreakoutDetector`` — asset-class plumbing.

Proves the coupled fix:
* Crypto universes cause yfinance to be queried with the ``-USD`` suffix.
* ``NewcomerCandidate.ticker`` stays bare; ``asset_class`` reflects the
  scanned universe rather than the previously-hardcoded ``"stock"``.
* The market-cap filter only applies to stocks — crypto coins have no
  equity-style marketCap, so they should not be silently dropped.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from finwiz.discovery.breakout_detector import BreakoutDetector


def _breakout_history(length: int = 40) -> pd.DataFrame:
    """Flat-then-spike history: closes flat for N-1 days, last bar breaks out strongly.

    * Flat 20-day window → n-day high anchored near baseline.
    * Final bar closes well above that high → price breakout score > 0.
    * Volume on last bar jumps → volume breakout score > 0.
    """
    closes = np.full(length, 100.0)
    closes[-1] = 115.0  # 15% break above flat window
    volumes = np.full(length, 1_000_000.0)
    volumes[-1] = 4_000_000.0  # volume ratio = 4x
    idx = pd.date_range("2026-01-01", periods=length, freq="D")
    return pd.DataFrame({"Close": closes, "Volume": volumes}, index=idx)


class _FakeTicker:
    """Minimal stand-in for ``yfinance.Ticker``."""

    def __init__(self, info: dict[str, Any] | None = None) -> None:
        # marketCap inside the breakout detector's $200M-$50B window so
        # stock candidates aren't filtered out by the cap gate.
        self.info = info or {"longName": "Fake Asset", "marketCap": 5_000_000_000}
        self._history = _breakout_history()

    def history(self, period: str) -> pd.DataFrame:
        return self._history


class TestBreakoutDetectorAssetClass:
    """``asset_class`` must flow from caller → yfinance boundary → candidate."""

    def test_crypto_universe_queries_yfinance_with_usd_suffix(self, mocker: Any) -> None:
        ticker_factory = mocker.patch(
            "finwiz.discovery.breakout_detector.yf.Ticker",
            return_value=_FakeTicker(),
        )

        detector = BreakoutDetector()
        candidates = detector.detect(["BTC"], asset_class="crypto")

        # Crypto tickers must be queried only with the -USD suffix,
        # never with the bare symbol.
        called_symbols = {call.args[0] for call in ticker_factory.call_args_list}
        assert called_symbols == {"BTC-USD"}, called_symbols

        assert len(candidates) == 1
        assert candidates[0].ticker == "BTC", "domain ticker must stay bare"
        assert candidates[0].asset_class == "crypto"

    def test_stock_universe_queries_yfinance_without_suffix(self, mocker: Any) -> None:
        ticker_factory = mocker.patch(
            "finwiz.discovery.breakout_detector.yf.Ticker",
            return_value=_FakeTicker(),
        )

        detector = BreakoutDetector()
        candidates = detector.detect(["AAPL"], asset_class="stock")

        called_symbols = {call.args[0] for call in ticker_factory.call_args_list}
        assert called_symbols == {"AAPL"}

        assert len(candidates) == 1
        assert candidates[0].ticker == "AAPL"
        assert candidates[0].asset_class == "stock"

    def test_default_asset_class_is_stock(self, mocker: Any) -> None:
        mocker.patch(
            "finwiz.discovery.breakout_detector.yf.Ticker",
            return_value=_FakeTicker(),
        )

        candidates = BreakoutDetector().detect(["AAPL"])

        assert candidates and candidates[0].asset_class == "stock"

    def test_crypto_bypasses_market_cap_filter(self, mocker: Any) -> None:
        """Crypto coins have no equity-style marketCap — filter must not drop them."""
        mocker.patch(
            "finwiz.discovery.breakout_detector.yf.Ticker",
            return_value=_FakeTicker(info={"longName": "Aave", "marketCap": None}),
        )

        detector = BreakoutDetector()
        candidates = detector.detect(["AAVE"], asset_class="crypto")

        assert len(candidates) == 1
        assert candidates[0].ticker == "AAVE"
        assert candidates[0].asset_class == "crypto"


def _weak_breakout_history(length: int = 40) -> pd.DataFrame:
    """Flat price / flat volume — nothing breaking out.

    Closes hover near baseline with no final push; volume sits at SMA.
    Price breakout score and volume breakout score both stay well below
    ``_BREAKOUT_STRONG_SIGNAL``, so the candidate must be filtered out.
    """
    closes = np.linspace(100.0, 100.5, length)
    volumes = np.full(length, 1_000_000.0)
    idx = pd.date_range("2026-01-01", periods=length, freq="D")
    return pd.DataFrame({"Close": closes, "Volume": volumes}, index=idx)


class _WeakBreakoutTicker:
    """yfinance stand-in producing a history that fails the breakout gate."""

    def __init__(self) -> None:
        self.info = {"longName": "Flat Corp", "marketCap": 5_000_000_000}
        self._history = _weak_breakout_history()

    def history(self, period: str) -> pd.DataFrame:
        return self._history


class TestBreakoutDetectorQualityGate:
    """Weak-breakout candidates must be excluded from the opportunity list."""

    def test_flat_price_and_volume_excluded(self, mocker: Any) -> None:
        mocker.patch(
            "finwiz.discovery.breakout_detector.yf.Ticker",
            return_value=_WeakBreakoutTicker(),
        )

        candidates = BreakoutDetector().detect(["FLATCO"], asset_class="stock")

        assert candidates == [], "weak-breakout stock must not appear in opportunity list"
