"""Curated crypto genesis years.

Genesis dates are immutable, so they are curated here rather than fetched: the
same reasoning as the curated ETF expense-ratio table. Years, not ages — an age
constant is wrong again every January. An unlisted symbol yields None, never a
default: a guessed age silently feeds 20% of the crypto fundamental score.
"""

from datetime import date

from finwiz.data.adapters.crypto.base import normalize_crypto_symbol

CRYPTO_GENESIS_YEAR: dict[str, int] = {
    "ADA": 2017,
    "AVAX": 2020,
    "BTC": 2009,
    "DOT": 2020,
    "ETH": 2015,
    "LINK": 2017,
    "LTC": 2011,
    "SOL": 2020,
    "XRP": 2012,
}


def crypto_age_years(ticker: str, *, today: date | None = None) -> float | None:
    """Return the asset's age in whole years, or None when it is not curated."""
    symbol = normalize_crypto_symbol(ticker)
    genesis_year = CRYPTO_GENESIS_YEAR.get(symbol)
    if genesis_year is None:
        return None
    reference = today or date.today()
    return float(reference.year - genesis_year)
