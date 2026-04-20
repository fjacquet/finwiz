"""Unit tests for the yfinance → FundamentalScorer adapter.

Locks in the field-mapping contract that ``MomentumScanner`` depends on:

* yfinance ``debtToEquity`` is reported in percent; the adapter rescales
  to a ratio. A test missing this detail would silently label healthy
  companies as over-leveraged.
* When required primary fields are absent the adapter returns ``None``,
  so callers skip the blend rather than scoring on synthetic defaults.
* ETF inception timestamps convert to years of history via ``datetime.fromtimestamp``.
"""

from __future__ import annotations

from datetime import UTC, datetime

from finwiz.discovery.fundamentals_adapter import yfinance_info_to_fundamentals_data


class TestStockMapping:
    """Stock path: primary fields required, debtToEquity rescaled to ratio."""

    def test_full_mapping(self) -> None:
        info = {
            "returnOnEquity": 0.30,
            "revenueGrowth": 0.15,
            "profitMargins": 0.22,
            "debtToEquity": 45.2,
            "marketCap": 2_000_000_000_000,
            "longName": "Alphabet Inc.",
        }
        out = yfinance_info_to_fundamentals_data(info, "stock")
        assert out is not None
        assert out["roe"] == 0.30
        assert out["revenue_growth"] == 0.15
        assert out["profit_margin"] == 0.22
        # yfinance reports debtToEquity in percent points (45.2 → 0.452 ratio).
        assert out["debt_to_equity"] == 0.452
        assert out["market_cap"] == 2_000_000_000_000
        assert out["name"] == "Alphabet Inc."

    def test_returns_none_when_required_fields_missing(self) -> None:
        """Missing returnOnEquity → skip blend rather than score on default."""
        info = {
            "revenueGrowth": 0.15,
            "profitMargins": 0.22,
        }
        assert yfinance_info_to_fundamentals_data(info, "stock") is None

    def test_debt_to_equity_defaults_when_absent(self) -> None:
        """Missing debtToEquity is not a hard failure — defaults to 0.5 ratio."""
        info = {
            "returnOnEquity": 0.20,
            "revenueGrowth": 0.10,
            "profitMargins": 0.15,
        }
        out = yfinance_info_to_fundamentals_data(info, "stock")
        assert out is not None
        assert out["debt_to_equity"] == 0.5

    def test_name_falls_back_to_short_name(self) -> None:
        info = {
            "returnOnEquity": 0.20,
            "revenueGrowth": 0.10,
            "profitMargins": 0.15,
            "shortName": "ACME",
        }
        out = yfinance_info_to_fundamentals_data(info, "stock")
        assert out is not None
        assert out["name"] == "ACME"


class TestEtfMapping:
    """ETF path: expense ratio + AUM required; tracking error optional with default."""

    def test_full_mapping(self) -> None:
        inception_ts = int(datetime(2020, 1, 1, tzinfo=UTC).timestamp())
        info = {
            "annualReportExpenseRatio": 0.003,
            "totalAssets": 500_000_000_000,
            "trackingError": 0.002,
            "fundInceptionDate": inception_ts,
            "longName": "Vanguard 500 Index ETF",
        }
        out = yfinance_info_to_fundamentals_data(info, "etf")
        assert out is not None
        assert out["expense_ratio"] == 0.003
        assert out["aum"] == 500_000_000_000
        assert out["tracking_error"] == 0.002
        assert out["history_years"] > 0

    def test_returns_none_when_required_fields_missing(self) -> None:
        info = {"trackingError": 0.01}
        assert yfinance_info_to_fundamentals_data(info, "etf") is None

    def test_tracking_error_defaults_when_absent(self) -> None:
        info = {
            "annualReportExpenseRatio": 0.005,
            "totalAssets": 1_000_000_000,
        }
        out = yfinance_info_to_fundamentals_data(info, "etf")
        assert out is not None
        assert out["tracking_error"] == 0.01

    def test_history_years_defaults_when_inception_absent(self) -> None:
        info = {
            "annualReportExpenseRatio": 0.005,
            "totalAssets": 1_000_000_000,
        }
        out = yfinance_info_to_fundamentals_data(info, "etf")
        assert out is not None
        assert out["history_years"] == 0.0

    def test_history_years_survives_malformed_inception(self) -> None:
        """A non-numeric inception value must degrade to 0.0, not raise."""
        info = {
            "annualReportExpenseRatio": 0.005,
            "totalAssets": 1_000_000_000,
            "fundInceptionDate": "not-a-date",
        }
        out = yfinance_info_to_fundamentals_data(info, "etf")
        assert out is not None
        assert out["history_years"] == 0.0


class TestUnsupportedAssetClass:
    """Crypto / unknown asset classes must return ``None`` (no fundamentals surface)."""

    def test_crypto_returns_none(self) -> None:
        info = {"returnOnEquity": 0.2, "revenueGrowth": 0.1, "profitMargins": 0.1}
        assert yfinance_info_to_fundamentals_data(info, "crypto") is None

    def test_unknown_asset_class_returns_none(self) -> None:
        assert yfinance_info_to_fundamentals_data({}, "bond") is None
