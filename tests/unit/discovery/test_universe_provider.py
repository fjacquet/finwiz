"""Tests for universe selection, hygiene and the candidate floor."""

from __future__ import annotations

from finwiz.discovery.universe_provider import DynamicUniverseProvider


def test_untradable_placeholders_are_filtered_out(mocker):
    provider = DynamicUniverseProvider()
    mocker.patch.object(provider, "_fallback_static_universe", return_value=[])
    mocker.patch.object(provider, "_mine_etf_holdings", return_value=["AAPL", "XTSLA", "MSFT"])

    result = provider.get_universe("etf")

    assert "XTSLA" not in result
    assert "AAPL" in result
    assert "MSFT" in result


def test_seed_override_is_honored_for_etfs(mocker):
    provider = DynamicUniverseProvider(seed_etfs=["SPY"])
    mocker.patch.object(provider, "_fallback_static_universe", return_value=[])
    mine = mocker.patch.object(provider, "_mine_etf_holdings", return_value=["AAPL"])

    provider.get_universe("etf")

    assert mine.call_args.args[0] == ["SPY"]


def test_seed_override_is_honored_for_stocks(mocker):
    provider = DynamicUniverseProvider(seed_etfs=["QQQ"])
    mocker.patch.object(provider, "_fallback_static_universe", return_value=[])
    mine = mocker.patch.object(provider, "_mine_etf_holdings", return_value=["AAPL"])

    provider.get_universe("stock")

    assert mine.call_args.args[0] == ["QQQ"]
