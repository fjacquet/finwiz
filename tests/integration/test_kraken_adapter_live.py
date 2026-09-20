"""Live check that the Kraken public endpoint still answers for our pairs."""

import pytest

from finwiz.data.adapters.crypto.kraken_adapter import KrakenAdapter

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("ticker", ["BTC-USD", "ETH-USD", "XRP-USD", "SOL-USD"])
def test_public_endpoint_answers_for_portfolio_pairs(ticker):
    result = KrakenAdapter().fetch(ticker)

    assert result is not None, f"Kraken no longer resolves {ticker}"
    assert result.price is not None
    assert result.price > 0
    assert result.market_cap is None, "Kraken never reports market cap"
