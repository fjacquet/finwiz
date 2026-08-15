"""Tests for universe selection, hygiene and the candidate floor."""

from __future__ import annotations

from finwiz.discovery.universe_provider import MIN_UNIVERSE_SIZE, DynamicUniverseProvider


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


def test_static_universe_is_unioned_in_when_mining_falls_short(mocker):
    provider = DynamicUniverseProvider()
    mocker.patch.object(provider, "_mine_etf_holdings", return_value=["AAPL", "MSFT"])
    mocker.patch.object(provider, "_fallback_static_universe", return_value=[f"T{i}" for i in range(MIN_UNIVERSE_SIZE)])

    result = provider.get_universe("etf")

    assert len(result) >= MIN_UNIVERSE_SIZE
    assert "AAPL" in result


def test_shortfall_is_logged_when_floor_cannot_be_met(mocker):
    provider = DynamicUniverseProvider()
    mocker.patch.object(provider, "_mine_etf_holdings", return_value=["AAPL"])
    mocker.patch.object(provider, "_fallback_static_universe", return_value=["MSFT"])
    warn = mocker.patch.object(provider._logger, "warning")

    result = provider.get_universe("etf")

    assert len(result) == 2
    assert any("below the floor" in str(c.args[0]) for c in warn.call_args_list)


def test_excluded_ticker_cannot_leak_back_in_via_the_static_union(mocker):
    provider = DynamicUniverseProvider()
    mocker.patch.object(provider, "_mine_etf_holdings", return_value=["AAPL"])
    static_universe = ["GOOG", *[f"T{i}" for i in range(MIN_UNIVERSE_SIZE - 1)]]
    mocker.patch.object(provider, "_fallback_static_universe", return_value=static_universe)

    result = provider.get_universe("etf", exclude_tickers=["GOOG"])

    assert "GOOG" not in result
    assert "AAPL" in result
    assert len(result) >= MIN_UNIVERSE_SIZE


def test_crypto_shortfall_does_not_trigger_static_union_but_still_warns(mocker):
    provider = DynamicUniverseProvider()
    static = mocker.patch.object(provider, "_fallback_static_universe", return_value=[f"C{i}" for i in range(10)])
    warn = mocker.patch.object(provider._logger, "warning")

    result = provider.get_universe("crypto")

    assert static.call_count == 1
    assert len(result) == 10
    assert any("below the floor" in str(c.args[0]) for c in warn.call_args_list)
