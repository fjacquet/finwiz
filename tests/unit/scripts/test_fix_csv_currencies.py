"""Unit tests for the fix-currencies CSV rewrite tool (resolver injected)."""

import csv

from scripts.fix_csv_currencies import rewrite_csv_currencies


def _rows(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_rewrites_currency_from_resolver(tmp_path):
    csv_path = tmp_path / "etf.csv"
    csv_path.write_text("Name,Ticker,Currency,Active\nAmundi EM,Yahoo:AEEM.PA,USD,true\nUBS Gold,Yahoo:AUUSI.SW,USD,true\n")

    def resolver(ticker):
        return {"AEEM.PA": "EUR", "AUUSI.SW": "CHF"}.get(ticker)

    changes = rewrite_csv_currencies(csv_path, resolver)

    rows = _rows(csv_path)
    assert rows[0]["Currency"] == "EUR"
    assert rows[1]["Currency"] == "CHF"
    assert ("AEEM.PA", "USD", "EUR") in changes


def test_preserves_other_columns_and_order(tmp_path):
    csv_path = tmp_path / "stock.csv"
    csv_path.write_text("Name,Ticker,Currency,Active\nApple,Yahoo:AAPL,USD,true\nNestle,Yahoo:NESN.SW,USD,true\n")

    def resolver(ticker):
        return {"AAPL": "USD", "NESN.SW": "CHF"}.get(ticker)

    rewrite_csv_currencies(csv_path, resolver)

    rows = _rows(csv_path)
    assert [r["Ticker"] for r in rows] == ["Yahoo:AAPL", "Yahoo:NESN.SW"]
    assert rows[0]["Active"] == "true"
    assert list(rows[0].keys()) == ["Name", "Ticker", "Currency", "Active"]


def test_adds_currency_column_to_crypto(tmp_path):
    csv_path = tmp_path / "crypto.csv"
    csv_path.write_text("Name,Ticker,Active\nBitcoin,BTC,true\n")

    def resolver(ticker):
        return "USD"

    rewrite_csv_currencies(csv_path, resolver)

    rows = _rows(csv_path)
    assert "Currency" in rows[0]
    assert rows[0]["Currency"] == "USD"


def test_per_ticker_failure_leaves_row_unchanged(tmp_path):
    csv_path = tmp_path / "stock.csv"
    csv_path.write_text("Name,Ticker,Currency,Active\nApple,Yahoo:AAPL,USD,true\nBroken,Yahoo:BAD,EUR,true\n")

    def resolver(ticker):
        return "CHF" if ticker == "AAPL" else None  # BAD unresolved

    rewrite_csv_currencies(csv_path, resolver)

    rows = _rows(csv_path)
    assert rows[0]["Currency"] == "CHF"
    assert rows[1]["Currency"] == "EUR"  # untouched


def test_idempotent(tmp_path):
    csv_path = tmp_path / "stock.csv"
    csv_path.write_text("Name,Ticker,Currency,Active\nApple,Yahoo:AAPL,USD,true\n")

    def resolver(ticker):
        return "EUR"

    first = rewrite_csv_currencies(csv_path, resolver)
    second = rewrite_csv_currencies(csv_path, resolver)

    assert first == [("AAPL", "USD", "EUR")]
    assert second == []  # nothing changed the second time


def test_empty_ticker_row_is_skipped(tmp_path):
    csv_path = tmp_path / "stock.csv"
    csv_path.write_text("Name,Ticker,Currency,Active\n,,USD,true\nApple,Yahoo:AAPL,EUR,true\n")

    def resolver(ticker):
        if not ticker:
            raise AssertionError("resolver must not be called for an empty ticker")
        return "EUR"

    changes = rewrite_csv_currencies(csv_path, resolver)

    rows = _rows(csv_path)
    # Empty-ticker row: Currency preserved, no change recorded for it.
    assert rows[0]["Ticker"] == ""
    assert rows[0]["Currency"] == "USD"
    assert all(norm != "" for norm, _, _ in changes)


def test_partial_change_within_one_run(tmp_path):
    csv_path = tmp_path / "stock.csv"
    csv_path.write_text("Name,Ticker,Currency,Active\nApple,Yahoo:AAPL,USD,true\nNestle,Yahoo:NESN.SW,USD,true\n")

    def resolver(ticker):
        return {"AAPL": "USD", "NESN.SW": "CHF"}.get(ticker)

    changes = rewrite_csv_currencies(csv_path, resolver)

    rows = _rows(csv_path)
    # Only the row that actually changed is recorded.
    assert changes == [("NESN.SW", "USD", "CHF")]
    assert rows[0]["Currency"] == "USD"
    assert rows[1]["Currency"] == "CHF"
