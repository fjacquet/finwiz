from __future__ import annotations

import json
from pathlib import Path

import pytest

from finwiz.orchestrators.portfolio_review import (
    RawHolding,
    basic_composite_score,
    basic_risk,
    build_portfolio_review,
    normalize_ticker,
    read_csv_holdings,
)
from finwiz.schemas.portfolio_review import PortfolioReview


def test_normalize_ticker():
    assert normalize_ticker("Yahoo:SPY") == "SPY"
    assert normalize_ticker(" yahoo:AAPL ") == "AAPL"
    assert normalize_ticker("AAPL") == "AAPL"


def test_read_csv_holdings(tmp_path: Path):
    csv_path = tmp_path / "etf.csv"
    csv_path.write_text(
        "Name,Ticker,Currency\nSPDR S&P 500,Yahoo:SPY,USD\nVanguard Total World,VT,USD\n",
        encoding="utf-8",
    )
    items = read_csv_holdings(csv_path, "etf")
    assert len(items) == 2
    assert items[0].ticker == "SPY"
    assert items[0].asset_class == "etf"


def test_basic_scoring_and_risk():
    assert 0.0 <= basic_composite_score(True, "stock") <= 1.0
    assert 0.0 <= basic_composite_score(True, "etf") <= 1.0
    r_valid = basic_risk(True)
    r_invalid = basic_risk(False)
    assert r_valid.score < r_invalid.score


def test_build_portfolio_review_decisions(monkeypatch):
    # Monkeypatch validation to control validity per symbol
    from finwiz.tools.ticker_validation_tool import TickerExistenceValidationTool

    def fake_run(self, symbol: str, asset_class: str = "auto"):
        return {"valid": symbol in {"AAPL", "SPY"}, "meta": {"source": "yahoo"}, "reason": None}

    monkeypatch.setattr(TickerExistenceValidationTool, "_run", fake_run, raising=True)

    raw = [
        RawHolding(asset_class="stock", name="Apple", ticker="AAPL", currency="USD"),
        RawHolding(asset_class="etf", name="SPDR S&P 500", ticker="SPY", currency="USD"),
        RawHolding(asset_class="stock", name="BadCorp", ticker="BAD", currency="USD"),
    ]

    review = build_portfolio_review(raw)
    assert isinstance(review, PortfolioReview)
    by_ticker = {h.ticker: h for h in review.holdings}
    assert by_ticker["AAPL"].decision == "KEEP"
    assert by_ticker["SPY"].decision == "KEEP"
    assert by_ticker["BAD"].decision == "SELL"


def test_threshold_effect(monkeypatch):
    from finwiz.tools.ticker_validation_tool import TickerExistenceValidationTool

    def always_valid(self, symbol: str, asset_class: str = "auto"):
        return {"valid": True, "meta": {"source": "yahoo"}, "reason": None}

    monkeypatch.setattr(TickerExistenceValidationTool, "_run", always_valid, raising=True)

    monkeypatch.setenv("KEEP_THRESHOLD", "0.70")  # stock valid base is 0.6 -> SELL under this threshold
    raw = [RawHolding(asset_class="stock", name="Apple", ticker="AAPL", currency="USD")]
    review = build_portfolio_review(raw)
    assert review.holdings[0].composite_score == pytest.approx(0.6, abs=1e-6)
    assert review.holdings[0].decision == "SELL"


def test_save_and_load_json(tmp_path: Path, monkeypatch):
    # Make all valid for simplicity
    from finwiz.tools.ticker_validation_tool import TickerExistenceValidationTool

    def always_valid(self, symbol: str, asset_class: str = "auto"):
        return {"valid": True, "meta": {"source": "yahoo"}, "reason": None}

    monkeypatch.setattr(TickerExistenceValidationTool, "_run", always_valid, raising=True)

    raw = [RawHolding(asset_class="stock", name="Apple", ticker="AAPL", currency="USD")]
    review = build_portfolio_review(raw)

    out_path = tmp_path / "portfolio_review.json"
    out_path.write_text(review.model_dump_json(indent=2), encoding="utf-8")
    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert data["holdings"][0]["ticker"] == "AAPL"
