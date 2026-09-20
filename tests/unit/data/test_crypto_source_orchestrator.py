"""Tests for the crypto multi-source orchestrator."""

from datetime import datetime

import pytest

from finwiz.data.adapters.crypto.base import CryptoMarketData
from finwiz.data.crypto_source_orchestrator import CryptoSourceOrchestrator


class _StubAdapter:
    """Returns a canned CryptoMarketData (or None) and records its calls."""

    def __init__(self, name, result):
        self._name = name
        self._result = result
        self.calls = []

    @property
    def source_name(self):
        return self._name

    def fetch(self, ticker):
        self.calls.append(ticker)
        return self._result


def _coingecko_data(price=81114.0, market_cap=1629408510367.0, volume=23900006504.0, circulating=20087096.0, max_supply=21000000.0):
    return CryptoMarketData(
        ticker="BTC-USD",
        source="coingecko",
        timestamp=datetime.now(),
        confidence=1.0,
        price=price,
        market_cap=market_cap,
        volume_24h=volume,
        circulating_supply=circulating,
        max_supply=max_supply,
    )


def _kraken_data(price=81121.4, volume=150074590.0):
    return CryptoMarketData(
        ticker="BTC-USD",
        source="kraken",
        timestamp=datetime.now(),
        confidence=1.0,
        price=price,
        volume_24h=volume,
    )


def _orchestrator(coingecko_result, kraken_result):
    return CryptoSourceOrchestrator(
        coingecko=_StubAdapter("coingecko", coingecko_result),
        kraken=_StubAdapter("kraken", kraken_result),
    )


def test_happy_path_uses_coingecko_for_every_field():
    result = _orchestrator(_coingecko_data(), _kraken_data()).fetch("BTC-USD", yfinance_price=81061.41)

    assert result.price == 81114.0
    assert result.market_cap == 1629408510367.0
    assert result.volume_24h == 23900006504.0
    assert result.circulating_supply == 20087096.0
    assert result.max_supply == 21000000.0
    assert result.lineage.price_source == "coingecko"
    assert result.lineage.market_cap_source == "coingecko"
    assert result.lineage.volume_24h_source == "coingecko"
    assert result.lineage.supply_source == "coingecko"
    assert result.confidence == pytest.approx(1.0)


def test_kraken_is_always_consulted_even_when_coingecko_succeeds():
    kraken = _StubAdapter("kraken", _kraken_data())
    orchestrator = CryptoSourceOrchestrator(coingecko=_StubAdapter("coingecko", _coingecko_data()), kraken=kraken)

    orchestrator.fetch("BTC-USD", yfinance_price=81061.41)

    assert kraken.calls == ["BTC-USD"], "the cross-check must run even on the happy path"


def test_disagreement_never_changes_the_value():
    # Kraken is 10% away; the primary still wins.
    result = _orchestrator(_coingecko_data(price=81114.0), _kraken_data(price=89225.4)).fetch("BTC-USD")

    assert result.price == 81114.0
    assert result.lineage.price_source == "coingecko"
    assert result.price_divergence_pct == pytest.approx(10.0, abs=0.01)
    assert any("divergence" in warning.lower() for warning in result.warnings)


def test_divergence_below_threshold_raises_no_warning():
    result = _orchestrator(_coingecko_data(price=81114.0), _kraken_data(price=81121.4)).fetch("BTC-USD")

    assert result.price_divergence_pct == pytest.approx(0.009, abs=0.01)
    assert result.warnings == []
    assert result.confidence == pytest.approx(1.0)


def test_price_divergence_is_none_with_a_single_source():
    result = _orchestrator(_coingecko_data(), None).fetch("BTC-USD")

    assert result.price_divergence_pct is None


def test_fallback_order_is_yfinance_then_kraken():
    result = _orchestrator(None, _kraken_data(price=81121.4)).fetch("BTC-USD", yfinance_price=81061.41)

    assert result.price == 81061.41
    assert result.lineage.price_source == "yfinance"


def test_kraken_is_the_last_resort_price():
    result = _orchestrator(None, _kraken_data(price=81121.4)).fetch("BTC-USD", yfinance_price=None)

    assert result.price == 81121.4
    assert result.lineage.price_source == "kraken"


def test_market_cap_and_supply_stay_none_when_coingecko_fails():
    result = _orchestrator(None, _kraken_data()).fetch("BTC-USD", yfinance_price=81061.41)

    assert result.market_cap is None
    assert result.circulating_supply is None
    assert result.max_supply is None
    assert result.lineage.market_cap_source is None
    assert result.lineage.supply_source is None


def test_kraken_volume_is_marked_single_venue():
    result = _orchestrator(None, _kraken_data(volume=150074590.0)).fetch("BTC-USD", yfinance_price=81061.41)

    assert result.volume_24h == 150074590.0
    assert result.lineage.volume_24h_source == "kraken:single-venue"


def test_every_source_failing_yields_all_none():
    result = _orchestrator(None, None).fetch("BTC-USD", yfinance_price=None)

    assert result.price is None
    assert result.market_cap is None
    assert result.volume_24h is None
    assert result.circulating_supply is None
    assert result.confidence == 0.0
    assert sorted(result.sources_failed) == ["coingecko", "kraken"]
    assert sorted(result.sources_attempted) == ["coingecko", "kraken"]
    assert result.sources_succeeded == []


def test_confidence_drops_for_each_unresolved_group():
    # yfinance price (0.8), no market cap, no volume, no supply: 0.8 - 0.3
    result = _orchestrator(None, None).fetch("BTC-USD", yfinance_price=81061.41)

    assert result.lineage.price_source == "yfinance"
    assert result.confidence == pytest.approx(0.5)


def test_uncapped_supply_does_not_count_as_a_gap():
    capped = _orchestrator(_coingecko_data(), _kraken_data()).fetch("BTC-USD")
    uncapped = _orchestrator(_coingecko_data(max_supply=None), _kraken_data()).fetch("ETH-USD")

    assert uncapped.max_supply is None
    assert uncapped.confidence == pytest.approx(capped.confidence), "no cap is a fact, not missing data"


def test_divergence_penalty_applies_to_confidence():
    result = _orchestrator(_coingecko_data(price=81114.0), _kraken_data(price=89225.4)).fetch("BTC-USD")

    assert result.confidence == pytest.approx(0.8)


def test_confidence_never_goes_below_zero():
    result = _orchestrator(None, _kraken_data(price=1.0, volume=None)).fetch("BTC-USD", yfinance_price=2.0)

    assert result.confidence >= 0.0
