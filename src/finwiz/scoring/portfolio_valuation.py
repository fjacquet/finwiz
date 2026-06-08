"""Pure deterministic portfolio valuation: quantities + price/FX -> EUR weights.

No AI, no network — `price_fn` and `fx_fn` are injected for testability and are
the only I/O boundaries. AI Minimalism: when Python can compute it, Python does.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Protocol

from finwiz.schemas.portfolio_valuation import HoldingValuation, ValuationResult

# price_fn(ticker) -> (price, native_currency) or None when unavailable.
PriceFn = Callable[[str], tuple[float, str] | None]
# fx_fn(native_currency) -> rate to multiply by for the base currency, or None.
FxFn = Callable[[str], float | None]


class _HasTickerQuantity(Protocol):
    ticker: str
    quantity: float | None


def value_holdings(
    holdings: Iterable[_HasTickerQuantity],
    *,
    base: str = "EUR",
    price_fn: PriceFn,
    fx_fn: FxFn,
) -> ValuationResult:
    """Value each holding and compute portfolio weights.

    For each holding WITH a quantity: resolve (price, native_ccy) via price_fn,
    compute native_value = quantity * price, convert to base via fx_fn(native_ccy).
    Holdings missing quantity/price/FX get weight=None and are excluded from the
    base total. Weights are eur_value / total over the holdings that fully resolved.

    `fx_fn` is expected to already convert a native amount into `base`; `base` is
    not threaded into `fx_fn`. Duplicate tickers collapse last-write-wins.
    """
    per_ticker: dict[str, HoldingValuation] = {}

    for holding in holdings:
        ticker = holding.ticker
        quantity = holding.quantity
        hv = HoldingValuation(ticker=ticker, quantity=quantity)
        per_ticker[ticker] = hv  # duplicate tickers collapse last-write-wins

        if quantity is None:
            continue

        priced_pair = price_fn(ticker)
        if priced_pair is None:
            continue

        price, native_ccy = priced_pair
        hv.native_currency = native_ccy
        hv.native_value = quantity * price

        rate = fx_fn(native_ccy)
        if rate is None:
            continue

        hv.eur_value = hv.native_value * rate

    # Derive aggregates from the final per_ticker map (not from a running sum in the
    # loop), so duplicate tickers — which collapse last-write-wins above — stay
    # internally consistent: the total never double-counts a repeated ticker.
    resolved = [hv for hv in per_ticker.values() if hv.eur_value is not None]
    total_eur = sum(hv.eur_value or 0.0 for hv in resolved) if resolved else None
    priced = len(resolved)
    total_count = len(per_ticker)

    if total_eur is not None and total_eur > 0.0:
        for hv in resolved:
            hv.weight = (hv.eur_value or 0.0) / total_eur

    pct = (priced / total_count * 100.0) if total_count else 0.0
    note = f"{priced} of {total_count} holdings priced ({pct:.0f}% by count)"

    return ValuationResult(
        per_ticker=per_ticker,
        total_value_eur=total_eur,
        priced_count=priced,
        total_count=total_count,
        coverage_note=note,
    )
