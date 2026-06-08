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
