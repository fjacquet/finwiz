"""Rewrite the `Currency` column of the portfolio CSVs from the authoritative
price-API currency. Run explicitly via `make fix-currencies` — never on a normal
analysis run. Atomic per file (temp + replace); per-ticker failures leave the row
untouched.
"""

from __future__ import annotations

import asyncio
import csv
import logging
import os
import sys
from collections.abc import Callable
from pathlib import Path
from tempfile import NamedTemporaryFile

from finwiz.schemas.portfolio_processing import AssetClass

logger = logging.getLogger(__name__)

# resolver(normalized_ticker) -> ISO currency code, or None when unresolved.
CurrencyResolver = Callable[[str], str | None]

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_CSV_FILES = [
    _PROJECT_ROOT / "data" / "stock.csv",
    _PROJECT_ROOT / "data" / "etf.csv",
    _PROJECT_ROOT / "data" / "crypto.csv",
]


def _normalize_ticker(raw: str, asset_class: AssetClass) -> str:
    """Strip the source prefix (and add -USD for crypto) for price-API lookup."""
    from finwiz.orchestrators.portfolio_holdings_processor import PortfolioHoldingsProcessor

    return PortfolioHoldingsProcessor().normalize_ticker(raw, asset_class=asset_class)


def rewrite_csv_currencies(
    path: Path,
    resolve_currency_fn: CurrencyResolver,
) -> list[tuple[str, str, str]]:
    """Rewrite `path`'s Currency column using the resolver.

    Returns a list of (normalized_ticker, old_currency, new_currency) for rows
    that changed. Adds a `Currency` column if absent (e.g. crypto.csv). Atomic.
    """
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    asset_class: AssetClass = "crypto" if path.stem == "crypto" else ("etf" if path.stem == "etf" else "stock")
    has_currency = "Currency" in fieldnames
    if not has_currency:
        # Insert Currency right after Ticker if present, else append.
        insert_at = fieldnames.index("Ticker") + 1 if "Ticker" in fieldnames else len(fieldnames)
        fieldnames.insert(insert_at, "Currency")

    changes: list[tuple[str, str, str]] = []
    for row in rows:
        raw_ticker = (row.get("Ticker") or "").strip()
        if not raw_ticker:
            row.setdefault("Currency", row.get("Currency", ""))
            continue
        norm = _normalize_ticker(raw_ticker, asset_class)
        old = (row.get("Currency") or "").strip()
        new = resolve_currency_fn(norm)
        if new is None:
            logger.warning("Could not resolve currency for %s; leaving %r", norm, old)
            row["Currency"] = old
            continue
        if new != old:
            changes.append((norm, old, new))
        row["Currency"] = new

    # Atomic write: temp file in the same dir, then replace. On any failure,
    # remove the orphaned temp file rather than leaving it in data/.
    tmp = NamedTemporaryFile("w", newline="", encoding="utf-8", dir=path.parent, delete=False)
    tmp_path = Path(tmp.name)
    try:
        with tmp:
            writer = csv.DictWriter(tmp, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow({k: row.get(k, "") for k in fieldnames})
        os.replace(tmp_path, path)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise

    return changes


def _build_live_resolver() -> CurrencyResolver:
    """Resolver backed by the live price API (network)."""
    from finwiz.tools.portfolio_price_service import PortfolioPriceService

    service = PortfolioPriceService()

    def resolve(norm_ticker: str) -> str | None:
        try:
            price_data = asyncio.run(service.get_current_price(norm_ticker))
        except Exception as exc:
            logger.warning("Price lookup failed for %s: %s", norm_ticker, exc)
            return None
        return price_data.currency if price_data is not None else None

    return resolve


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    resolver = _build_live_resolver()
    for csv_path in _CSV_FILES:
        if not csv_path.exists():
            logger.info("skip (missing): %s", csv_path)
            continue
        changes = rewrite_csv_currencies(csv_path, resolver)
        if changes:
            logger.info("%s: %d currency change(s)", csv_path.name, len(changes))
            for ticker, old, new in changes:
                logger.info("  %-14s %s -> %s", ticker, old or "(none)", new)
        else:
            logger.info("%s: no changes", csv_path.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
