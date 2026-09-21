"""Tests for the curated crypto genesis-year table."""

from datetime import date

import pytest

from finwiz.data.adapters.crypto.genesis import CRYPTO_GENESIS_YEAR, crypto_age_years


def test_known_symbol_age_is_derived_from_the_run_date():
    assert crypto_age_years("BTC", today=date(2026, 9, 20)) == pytest.approx(17.0)


def test_age_advances_with_the_calendar():
    assert crypto_age_years("BTC", today=date(2027, 9, 20)) == pytest.approx(18.0)


def test_usd_suffix_is_normalized():
    assert crypto_age_years("BTC-USD", today=date(2026, 9, 20)) == pytest.approx(17.0)


def test_xrp_is_not_three_years_old():
    age = crypto_age_years("XRP-USD", today=date(2026, 9, 20))

    assert age == pytest.approx(14.0), "XRP has been live since 2012"


def test_unknown_symbol_is_none_never_a_default():
    assert crypto_age_years("DOGE-USD", today=date(2026, 9, 20)) is None


@pytest.mark.parametrize(("symbol", "year"), [("BTC", 2009), ("ETH", 2015), ("XRP", 2012), ("SOL", 2020)])
def test_portfolio_holdings_are_covered(symbol, year):
    assert CRYPTO_GENESIS_YEAR[symbol] == year


def test_table_keys_are_bare_upper_case_symbols():
    for symbol in CRYPTO_GENESIS_YEAR:
        assert symbol == symbol.upper()
        assert "-" not in symbol
