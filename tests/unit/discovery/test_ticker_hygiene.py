"""Unit tests for centralized ticker hygiene (renames + non-tradable exclusions)."""

from __future__ import annotations

import pytest

from finwiz.discovery.ticker_hygiene import (
    canonical_symbol,
    is_tradable,
    sanitize_symbols,
)


class TestCanonicalSymbol:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("MATIC", "POL"),
            ("matic", "POL"),
            ("  FTM  ", "S"),
            ("BTC", "BTC"),  # unchanged
            ("aapl", "AAPL"),  # upper-cased pass-through
        ],
    )
    def test_renames_and_passthrough(self, raw: str, expected: str) -> None:
        assert canonical_symbol(raw) == expected

    def test_idempotent(self) -> None:
        assert canonical_symbol(canonical_symbol("MATIC")) == "POL"


class TestShareClassRenames:
    """Yahoo writes share classes with a dash; the screening universe uses a dot."""

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("BRK.B", "BRK-B"),
            ("brk.b", "BRK-B"),
            ("  BRK.B  ", "BRK-B"),
        ],
    )
    def test_dotted_share_class_becomes_dashed(self, raw: str, expected: str) -> None:
        assert canonical_symbol(raw) == expected

    def test_idempotent(self) -> None:
        assert canonical_symbol(canonical_symbol("BRK.B")) == "BRK-B"

    @pytest.mark.parametrize(
        "ticker",
        [
            "IDPE.L",  # London — a one-letter suffix, same shape as a share class
            "HYLD.L",
            "IJPA.L",
            "SUAS.L",
            "NESN.SW",
            "EL.PA",
            "VOW.DE",
            "SCL.F",
            "IESE.AS",
            "QDV5.DU",
        ],
    )
    def test_exchange_suffixes_are_left_alone(self, ticker: str) -> None:
        """A dot is also an exchange suffix. Only known share classes may move."""
        assert canonical_symbol(ticker) == ticker

    def test_sanitize_applies_share_class_rename(self) -> None:
        assert sanitize_symbols(["BRK.B", "AAPL", "IDPE.L"]) == ["AAPL", "BRK-B", "IDPE.L"]


class TestIsTradable:
    def test_non_tradable_excluded(self) -> None:
        assert is_tradable("XTSLA") is False
        assert is_tradable("xtsla") is False

    def test_tradable_allowed(self) -> None:
        assert is_tradable("AAPL") is True
        assert is_tradable("BTC") is True
        assert is_tradable("MATIC") is True  # renamed, still tradable


class TestSanitizeSymbols:
    def test_applies_rename_and_drops_non_tradable(self) -> None:
        result = sanitize_symbols(["AAPL", "MATIC", "XTSLA", "FTM", "btc"])
        assert "XTSLA" not in result
        assert "MATIC" not in result and "FTM" not in result
        assert {"AAPL", "POL", "S", "BTC"} == set(result)

    def test_dedup_and_sorted(self) -> None:
        result = sanitize_symbols(["MATIC", "POL", "btc", "BTC"])
        # MATIC -> POL collapses with POL; btc/BTC collapse
        assert result == ["BTC", "POL"]

    def test_empty(self) -> None:
        assert sanitize_symbols([]) == []
