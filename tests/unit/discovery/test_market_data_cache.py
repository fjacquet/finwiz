"""Cache-layer tests for discovery.market_data (memo -> disk -> fetch).

These lock the three-tier lookup behavior so the shared helper extraction is
provably behavior-preserving. Network fetch functions are mocked (pytest-mock).
"""

from __future__ import annotations

import pytest

from finwiz.discovery import market_data


@pytest.fixture(autouse=True)
def _isolate(tmp_path, mocker):
    """Reset module memos and redirect the day-cache into tmp."""
    mocker.patch.object(market_data, "_CACHE_DIR", tmp_path)
    market_data._returns_memo.clear()
    market_data._sectors_memo.clear()
    yield
    market_data._returns_memo.clear()
    market_data._sectors_memo.clear()


# ---------------------------------------------------------------- get_returns


def test_returns_empty_input() -> None:
    assert market_data.get_returns([]) == {}


def test_returns_fetch_then_memo_hit(mocker) -> None:
    fetch = mocker.patch.object(market_data, "_download_returns", return_value={"AAPL": [0.1, 0.2]})
    assert market_data.get_returns(["aapl"]) == {"AAPL": [0.1, 0.2]}
    # Second call served from memo: no second fetch.
    assert market_data.get_returns(["AAPL"]) == {"AAPL": [0.1, 0.2]}
    fetch.assert_called_once()


def test_returns_disk_hit_survives_memo_clear(mocker) -> None:
    mocker.patch.object(market_data, "_download_returns", return_value={"AAPL": [0.1, 0.2]})
    market_data.get_returns(["AAPL"])  # persists to disk
    market_data._returns_memo.clear()
    fetch = mocker.patch.object(market_data, "_download_returns", return_value={})
    assert market_data.get_returns(["AAPL"]) == {"AAPL": [0.1, 0.2]}  # served from disk
    fetch.assert_not_called()


# ---------------------------------------------------------------- get_sectors


def test_sectors_fetch_includes_none(mocker) -> None:
    fetch = mocker.patch.object(market_data, "_fetch_sectors", return_value={"AAPL": "Technology", "BTC": None})
    assert market_data.get_sectors(["AAPL", "BTC"]) == {"AAPL": "Technology", "BTC": None}
    fetch.assert_called_once()


def test_sectors_none_is_cached_not_refetched(mocker) -> None:
    mocker.patch.object(market_data, "_fetch_sectors", return_value={"BTC": None})
    market_data.get_sectors(["BTC"])  # None persisted to disk + memo
    market_data._sectors_memo.clear()
    fetch = mocker.patch.object(market_data, "_fetch_sectors", return_value={"BTC": "ShouldNotBeUsed"})
    assert market_data.get_sectors(["BTC"]) == {"BTC": None}  # disk membership wins
    fetch.assert_not_called()
