"""Unit tests for the live FX provider (network mocked)."""

import pytest

from finwiz.data import fx_rates


@pytest.fixture(autouse=True)
def _reset_fx_cache():
    """Each test starts with an empty per-run FX cache."""
    fx_rates.clear_fx_cache()
    yield
    fx_rates.clear_fx_cache()


def test_identity_rate_is_one_without_network(mocker):
    spy = mocker.patch("finwiz.data.fx_rates._fetch_pair_rate")

    assert fx_rates.get_fx_rate("EUR", "EUR") == 1.0
    spy.assert_not_called()


def test_simple_pair_lookup(mocker):
    mocker.patch("finwiz.data.fx_rates._fetch_pair_rate", return_value=0.92)

    assert fx_rates.get_fx_rate("CHF", "EUR") == 0.92


def test_gbp_pence_divided_by_100(mocker):
    # GBPEUR is ~1.17; a GBp (pence) amount must convert at rate/100.
    mocker.patch("finwiz.data.fx_rates._fetch_pair_rate", return_value=1.17)

    rate = fx_rates.get_fx_rate("GBp", "EUR")

    assert rate == pytest.approx(0.0117)


def test_gbp_pence_to_gbp_is_0_01(mocker):
    spy = mocker.patch("finwiz.data.fx_rates._fetch_pair_rate")

    assert fx_rates.get_fx_rate("GBp", "GBP") == pytest.approx(0.01)
    spy.assert_not_called()  # identity path: 1 pence = 0.01 GBP, no fetch


def test_failure_returns_none(mocker):
    mocker.patch("finwiz.data.fx_rates._fetch_pair_rate", return_value=None)

    assert fx_rates.get_fx_rate("CHF", "EUR") is None


def test_per_run_cache_hits_once(mocker):
    spy = mocker.patch("finwiz.data.fx_rates._fetch_pair_rate", return_value=0.92)

    fx_rates.get_fx_rate("CHF", "EUR")
    fx_rates.get_fx_rate("CHF", "EUR")

    spy.assert_called_once()


def test_blank_currency_returns_none(mocker):
    spy = mocker.patch("finwiz.data.fx_rates._fetch_pair_rate")

    assert fx_rates.get_fx_rate("", "EUR") is None
    spy.assert_not_called()
