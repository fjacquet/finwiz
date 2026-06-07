"""Unit tests for the discovery ticker-normalization helper.

Covers the contract of :func:`finwiz.discovery.ticker_utils.to_yfinance_symbol`:
bare tickers pass through for stock/ETF, crypto gets a ``-USD`` suffix, and
the function is idempotent on already-suffixed crypto tickers.
"""

from __future__ import annotations

import pytest

from finwiz.discovery.ticker_utils import to_yfinance_symbol


class TestStockAndETFPassThrough:
    """Stock and ETF tickers should be returned unchanged (beyond upper-casing)."""

    @pytest.mark.parametrize("ticker", ["AAPL", "MSFT", "GOOG", "BRK.B"])
    def test_stock_pass_through(self, ticker: str) -> None:
        assert to_yfinance_symbol(ticker, "stock") == ticker.upper()

    @pytest.mark.parametrize("ticker", ["QQQ", "SPY", "VOO", "IEMG"])
    def test_etf_pass_through(self, ticker: str) -> None:
        assert to_yfinance_symbol(ticker, "etf") == ticker.upper()

    def test_stock_with_usd_suffix_left_alone(self) -> None:
        # Non-crypto asset classes must never rewrite the symbol,
        # even if it happens to end with "-USD".
        assert to_yfinance_symbol("BTC-USD", "stock") == "BTC-USD"


class TestCryptoNormalization:
    """Crypto tickers must receive a ``-USD`` suffix at the yfinance boundary."""

    @pytest.mark.parametrize(
        ("bare", "expected"),
        [
            ("BTC", "BTC-USD"),
            ("ETH", "ETH-USD"),
            ("AAVE", "AAVE-USD"),
            ("DOGE", "DOGE-USD"),
            ("SOL", "SOL-USD"),
        ],
    )
    def test_bare_crypto_gets_usd_suffix(self, bare: str, expected: str) -> None:
        assert to_yfinance_symbol(bare, "crypto") == expected

    @pytest.mark.parametrize(
        ("old", "expected"),
        [
            ("MATIC", "POL-USD"),  # Polygon migration
            ("FTM", "S-USD"),  # Sonic rebrand
            ("MATIC-USD", "POL-USD"),  # rename applies even when pre-suffixed
        ],
    )
    def test_renamed_crypto_uses_current_symbol(self, old: str, expected: str) -> None:
        assert to_yfinance_symbol(old, "crypto") == expected

    def test_case_normalization(self) -> None:
        assert to_yfinance_symbol("btc", "crypto") == "BTC-USD"
        assert to_yfinance_symbol("  aave  ", "crypto") == "AAVE-USD"

    def test_idempotent_on_usd_suffixed(self) -> None:
        assert to_yfinance_symbol("BTC-USD", "crypto") == "BTC-USD"

    def test_idempotent_on_usdt_suffixed(self) -> None:
        assert to_yfinance_symbol("BTC-USDT", "crypto") == "BTC-USDT"

    def test_idempotent_on_usdc_suffixed(self) -> None:
        assert to_yfinance_symbol("USDC-USDC", "crypto") == "USDC-USDC"
