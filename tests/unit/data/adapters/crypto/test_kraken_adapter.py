"""Tests for the Kraken crypto adapter."""

import json

from finwiz.data.adapters.crypto.kraken_adapter import KrakenAdapter


class _FakeTool:
    """Stands in for KrakenTickerInfoTool, recording the pair it saw."""

    def __init__(self, envelope, raises=None):
        self.envelope = envelope
        self.raises = raises
        self.seen_pair = None

    def _run(self, pair):
        self.seen_pair = pair
        if self.raises is not None:
            raise self.raises
        return self.envelope


def _envelope(data):
    return json.dumps({"success": True, "data": data, "error": None})


def _btc_payload():
    return {
        "a": ["81130.00000", "1", "1.000"],
        "b": ["81120.00000", "1", "1.000"],
        "c": ["81121.40000", "0.00100000"],
        "v": ["120.50000000", "1850.00000000"],
    }


def test_fetch_builds_pair_and_reads_last_trade():
    tool = _FakeTool(_envelope(_btc_payload()))
    adapter = KrakenAdapter(tool=tool)

    result = adapter.fetch("BTC-USD")

    assert tool.seen_pair == "BTCUSD"
    assert result is not None
    assert result.source == "kraken"
    assert result.ticker == "BTC-USD"
    assert result.price == 81121.4


def test_volume_is_converted_from_base_units_to_usd():
    result = KrakenAdapter(tool=_FakeTool(_envelope(_btc_payload()))).fetch("BTC-USD")

    assert result is not None
    # 1850 BTC over 24h at 81121.40 per BTC
    assert result.volume_24h == 1850.0 * 81121.4


def test_market_cap_and_supply_are_never_reported():
    result = KrakenAdapter(tool=_FakeTool(_envelope(_btc_payload()))).fetch("BTC-USD")

    assert result is not None
    assert result.market_cap is None
    assert result.circulating_supply is None
    assert result.max_supply is None


def test_unlisted_pair_returns_none():
    envelope = json.dumps({"success": False, "data": None, "error": "No data found for pair FOOUSD. Invalid pair."})
    adapter = KrakenAdapter(tool=_FakeTool(envelope))

    assert adapter.fetch("FOO-USD") is None


def test_transport_error_returns_none():
    adapter = KrakenAdapter(tool=_FakeTool(None, raises=RuntimeError("connection reset")))

    assert adapter.fetch("BTC-USD") is None


def test_missing_last_trade_returns_none():
    payload = _btc_payload()
    del payload["c"]
    adapter = KrakenAdapter(tool=_FakeTool(_envelope(payload)))

    assert adapter.fetch("BTC-USD") is None


def test_missing_volume_still_returns_price():
    payload = _btc_payload()
    del payload["v"]

    result = KrakenAdapter(tool=_FakeTool(_envelope(payload))).fetch("BTC-USD")

    assert result is not None
    assert result.price == 81121.4
    assert result.volume_24h is None
