"""Centralized ticker hygiene: renames and non-tradable exclusions.

Single source of truth for two classes of yfinance noise observed in runs:

* **Renamed/migrated crypto** — symbols that changed ticker and now return
  "possibly delisted" under their old name (e.g. ``MATIC`` → ``POL`` after the
  2024 Polygon migration, ``FTM`` → ``S`` after the Sonic rebrand).
* **Non-tradable placeholders** — instrument codes that are not quotable
  securities (e.g. ``XTSLA``, a BlackRock cash-sweep line that leaks in from
  ETF holdings expansion) and 404 on every yfinance lookup.
* **Dotted share classes** — Yahoo writes a US share class with a dash
  (``BRK-B``) while the screening universe carries the dot form (``BRK.B``),
  which returns "No data found" on every lookup.

The share-class map is an explicit allow-list, never a pattern: a dot is also
an exchange suffix, and London's is a single letter (``IDPE.L``), so a rule
like "one letter after the dot becomes a dash" would silently break every
LSE holding.

Apply :func:`canonical_symbol` at the bare-ticker stage (before the ``-USD``
suffix) and filter with :func:`is_tradable` at fetch boundaries so the old
names never reach yfinance.
"""

from __future__ import annotations

from collections.abc import Iterable

# Bare-symbol renames (asset-class agnostic; applied before quote suffixing).
CRYPTO_SYMBOL_RENAMES: dict[str, str] = {
    "MATIC": "POL",  # Polygon migrated MATIC -> POL (2024)
    "FTM": "S",  # Fantom rebranded to Sonic (S) (2024)
}

# Dot-form share classes that Yahoo quotes with a dash. Explicit entries only —
# see the module docstring for why this must not be a pattern.
SHARE_CLASS_RENAMES: dict[str, str] = {
    "BRK.B": "BRK-B",  # Berkshire Hathaway class B, in the static stock universe
}

# Symbols that are not quotable securities and 404 on every yfinance call.
NON_TRADABLE_SYMBOLS: frozenset[str] = frozenset(
    {
        "XTSLA",  # BlackRock cash-sweep placeholder, not a tradable ticker
    }
)


def canonical_symbol(ticker: str) -> str:
    """Return the current canonical bare symbol, applying known renames.

    Idempotent and case-insensitive on input; returns an upper-cased symbol.
    """
    symbol = ticker.strip().upper()
    symbol = SHARE_CLASS_RENAMES.get(symbol, symbol)
    return CRYPTO_SYMBOL_RENAMES.get(symbol, symbol)


def is_tradable(ticker: str) -> bool:
    """Return False for known non-tradable placeholder symbols."""
    return canonical_symbol(ticker) not in NON_TRADABLE_SYMBOLS


def sanitize_symbols(tickers: Iterable[str]) -> list[str]:
    """Apply renames and drop non-tradable symbols, de-duplicated and sorted.

    Use at fetch boundaries that batch many tickers into a single yfinance call.
    """
    cleaned = {canonical_symbol(t) for t in tickers if is_tradable(t)}
    return sorted(cleaned)
