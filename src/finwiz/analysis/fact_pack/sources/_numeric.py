"""Shared numeric coercion for every source that reads a number off yfinance.

`NaN` defeats every guard written ad hoc against it, because it satisfies
`isinstance(x, float)` and loses every comparison:

    isinstance(nan, float)  -> True
    nan < 0                 -> False
    nan is None             -> False

A bound written as `if value < 0: treat as unknown` silently lets a NaN
through when the intent was to catch exactly this kind of bad value. This
defect class hit four call sites before it got a name: crypto_source's
supply/market-cap/launch-year fields, and fund_source's expense ratio,
turnover, asset mix, sector weights and holdings weights all read a number
off a source that scrapes rather than promises a contract, and any of them
could receive `NaN` or `+/-inf` instead of a missing value.
"""

from __future__ import annotations

import math
from typing import Any


def _finite(value: Any) -> float | None:
    """Coerce to a finite float, or None if it isn't one.

    Rejects non-numbers (including bool, which is technically an int),
    and rejects NaN/+inf/-inf explicitly -- `float(value)` alone accepts
    all three without complaint. Domain-specific bounds (weight in
    [0.0, 1.0], a metric that must be non-negative, ...) are each
    call site's own job; this only answers "is this a real number".
    """
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    fval = float(value)
    if not math.isfinite(fval):
        return None
    return fval
