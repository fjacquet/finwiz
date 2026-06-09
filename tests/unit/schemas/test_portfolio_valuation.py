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
