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
