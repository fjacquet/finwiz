"""Shared string coercion for every source that reads a text field off yfinance.

Same shape as ``_numeric.py``'s ``_finite``, for the same reason: yfinance's
`info`/`companyOfficers`/`sec_filings`/`news` payloads are scraped, not
contractual, and a field that is usually a string can arrive as anything else
(an int, a list, `None` sitting behind a truthy sentinel). A bare
``(value or "").strip()`` raises `AttributeError` the moment that happens --
this hit fund_source's `issuer`/`legal_type` and, identically, six sites in
yfinance_source.py (a business summary, an officer's name and title, a
filing's title, a news item's provider and title) before it had a name.
"""

from __future__ import annotations

from typing import Any


def _safe_str(value: Any, max_chars: int | None = None) -> str:
    """Coerce to a stripped string, or "" if it isn't a string.

    A non-string value degrades to the empty string rather than raising --
    the caller's own "empty means absent" handling (an `if name and title`,
    an `issuer` that must be non-empty to build a pack) then applies
    unchanged, with no special-casing for the type mismatch. `max_chars`
    truncates when the caller has one to enforce (e.g. a schema field's
    `max_length`); left `None` when truncation happens downstream instead.
    """
    if not isinstance(value, str):
        return ""
    text = value.strip()
    return text[:max_chars] if max_chars is not None else text
