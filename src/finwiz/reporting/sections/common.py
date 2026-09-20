"""Small cross-cutting helpers shared across report sections."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Any

# Worst → best, ``N/A`` (deep analysis never ran) last. Mirrors the ``Grade``
# Literal in ``schemas/portfolio_review.py``; the consolidated report buckets
# and orders by this list so the reader meets the problem positions first.
GRADE_ORDER: tuple[str, ...] = ("F", "D-", "D", "D+", "C-", "C", "C+", "B-", "B", "B+", "A-", "A", "A+", "N/A")

# Grades whose group is rendered expanded by default: the ones that call for a decision.
OPEN_BY_DEFAULT_GRADES: frozenset[str] = frozenset({"F", "D-", "D", "D+"})

# French labels for the ``AssetClass`` Literal (``schemas/portfolio_processing.py``);
# ``other`` catches a missing/unknown class so no holding silently disappears.
ASSET_CLASS_LABELS: dict[str, str] = {"stock": "Actions", "etf": "ETF", "crypto": "Crypto", "other": "Autres"}


def grade_css_class(grade: object) -> str:
    """Map a letter grade to its CSS class, HTML-attribute-safe.

    ``"A+"`` → ``"grade-a-plus"``, ``"B"`` → ``"grade-b"``. Empty/None → ``"grade-"``.
    Centralizes the grade→class expression that several sections render.
    """
    slug = str(grade or "").lower().replace("+", "-plus")
    return escape(f"grade-{slug}", quote=True)


def grade_sort_key(grade: object) -> int:
    """Position of ``grade`` in :data:`GRADE_ORDER`; unknown values sort after ``N/A``."""
    try:
        return GRADE_ORDER.index(str(grade or "N/A"))
    except ValueError:
        return len(GRADE_ORDER)


@dataclass
class AssetGroup:
    """One asset-class bucket of holdings, in canonical class order."""

    key: str
    label: str
    items: list[Any]


def group_by_asset_class(items: list[Any]) -> list[AssetGroup]:
    """Bucket ``items`` by their ``asset_class`` attribute.

    Returns only the buckets that are non-empty, in :data:`ASSET_CLASS_LABELS`
    order (stock, etf, crypto, other). Items keep their input order inside a
    bucket; callers sort as they see fit.
    """
    buckets: dict[str, list[Any]] = {}
    for item in items:
        key = str(getattr(item, "asset_class", None) or "").lower()
        if key not in ASSET_CLASS_LABELS or key == "other":
            key = "other"
        buckets.setdefault(key, []).append(item)
    return [AssetGroup(key=k, label=label, items=buckets[k]) for k, label in ASSET_CLASS_LABELS.items() if k in buckets]


def plural(n: int, singular: str, plural_form: str | None = None) -> str:
    """``"1 position"`` / ``"3 positions"`` — French pluralisation for counts."""
    word = singular if n <= 1 else (plural_form or f"{singular}s")
    return f"{n} {word}"
