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
    """Build a synthetic price/volume history strong enough to pass all signal gates.

    * Steady uptrend in closing price → positive ROC.
    * A volume spike on the last bar → volume anomaly above threshold.
    * RSI on the resulting series lands comfortably in the 50–70 band.
    """
    closes = np.linspace(100.0, 130.0, length)
    volumes = np.full(length, 1_000_000, dtype=float)
    volumes[-1] = 5_000_000  # last-bar spike → ratio = 5x
    idx = pd.date_range("2026-01-01", periods=length, freq="D")
    return pd.DataFrame({"Close": closes, "Volume": volumes}, index=idx)


class _FakeTicker:
    """Minimal stand-in for ``yfinance.Ticker``."""

    def __init__(self, info: dict[str, Any] | None = None) -> None:
        self.info = info or {"longName": "Fake Asset", "marketCap": 1_000_000_000}
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
