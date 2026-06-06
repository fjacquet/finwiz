"""Small cross-cutting helpers shared across report sections."""

from __future__ import annotations

from html import escape


def grade_css_class(grade: object) -> str:
    """Map a letter grade to its CSS class, HTML-attribute-safe.

    ``"A+"`` → ``"grade-a-plus"``, ``"B"`` → ``"grade-b"``. Empty/None → ``"grade-"``.
    Centralizes the grade→class expression that several sections render.
    """
    slug = str(grade or "").lower().replace("+", "-plus")
    return escape(f"grade-{slug}", quote=True)
