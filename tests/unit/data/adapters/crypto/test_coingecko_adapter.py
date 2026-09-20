"""Tests for the CoinGecko crypto adapter."""

import json

import pytest

from finwiz.data.adapters.crypto.base import normalize_crypto_symbol, positive_or_none
from finwiz.data.adapters.crypto.coingecko_adapter import CoinGeckoAdapter


class _FakeTool:
    """Stands in for EnhancedCryptoAnalysisTool, recording the symbol it saw."""

    def __init__(self, payload, raises=None):
        self.payload = payload
        self.raises = raises
        self.seen_symbol = None

    def _run(self, symbol, include_thesis=True, include_risk_assessment=True, include_perplexity=True):
        self.seen_symbol = symbol
        if self.raises is not None:
            raise self.raises
        return self.payload


def _good_payload():
    return {
        "symbol": "BTC",
        "crypto_data": {
            "symbol": "BTC",
            "name": "Bitcoin",
            "current_price": 81114.0,
            "market_cap": 1629408510367.0,
            "total_volume": 23900006504.0,
            "volume_24h": 23900006504.0,
            "circulating_supply": 20087096.0,
            "max_supply": 21000000.0,
            "sources": ["CoinGecko (via crewai_custom_tools)"],
        },
    }


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("BTC-USD", "BTC"), ("btc-usd", "BTC"), ("ETH-USDT", "ETH"), ("SOL", "SOL"), ("  xrp-usd  ", "XRP")],
)
def test_normalize_crypto_symbol(raw, expected):
    assert normalize_crypto_symbol(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [(1.5, 1.5), (0, None), (-3, None), (None, None), ("abc", None), ("12.5", 12.5)],
)
def test_positive_or_none(raw, expected):
    assert positive_or_none(raw) == expected


def test_fetch_maps_every_field_and_strips_usd_suffix():
    tool = _FakeTool(_good_payload())
    adapter = CoinGeckoAdapter(tool=tool)

    result = adapter.fetch("BTC-USD")

    assert tool.seen_symbol == "BTC", "the -USD suffix must be stripped before the CoinGecko lookup"
    assert result is not None
    assert result.source == "coingecko"
    assert result.ticker == "BTC-USD"
    assert result.price == 81114.0
    assert result.market_cap == 1629408510367.0
    assert result.volume_24h == 23900006504.0
    assert result.circulating_supply == 20087096.0
    assert result.max_supply == 21000000.0


def test_fabricated_fallback_payload_counts_as_failure():
    payload = {
        "crypto_data": {
            "symbol": "BTC-USD",
            "name": "Cryptocurrency BTC-USD",
            "current_price": 0,
            "market_cap": 0,
            "total_volume": 0,
            "circulating_supply": 0,
            "sources": ["Fallback Data"],
        }
    }
    adapter = CoinGeckoAdapter(tool=_FakeTool(payload))

    assert adapter.fetch("BTC-USD") is None, "invented fallback data must never be returned as real data"


def test_tool_exception_returns_none():
    adapter = CoinGeckoAdapter(tool=_FakeTool(None, raises=RuntimeError("network down")))

    assert adapter.fetch("ETH-USD") is None


def test_missing_crypto_data_returns_none():
    adapter = CoinGeckoAdapter(tool=_FakeTool({"symbol": "ETH"}))

    assert adapter.fetch("ETH-USD") is None


def test_uncapped_supply_keeps_max_supply_none():
    payload = _good_payload()
    payload["crypto_data"]["max_supply"] = None

    result = CoinGeckoAdapter(tool=_FakeTool(payload)).fetch("ETH-USD")

    assert result is not None
    assert result.max_supply is None, "no cap is a fact about the asset, not a missing value"
    assert result.circulating_supply == 20087096.0


def test_zero_market_cap_becomes_none():
    payload = _good_payload()
    payload["crypto_data"]["market_cap"] = 0

    result = CoinGeckoAdapter(tool=_FakeTool(payload)).fetch("BTC-USD")

    assert result is not None
    assert result.market_cap is None


def test_raw_data_is_json_serialisable():
    result = CoinGeckoAdapter(tool=_FakeTool(_good_payload())).fetch("BTC-USD")

    assert result is not None
    json.dumps(result.raw_data, default=str)
