"""Fact-pack provenance rendering shared across report sections."""

from __future__ import annotations

from datetime import datetime
from html import escape
from urllib.parse import urlparse

from finwiz.analysis.fact_pack.render import to_rows
from finwiz.schemas.hybrid_analysis.fact_pack import FactPack

_MAX_BODY_VALUE_CHARS = 160


def _is_safe_url(url: str) -> bool:
    """Defense-in-depth: only allow http/https citation URLs in rendered HTML.

    Pydantic validates URLs at fact-pack ingestion, but a stale cache or future
    schema drift could leak a `javascript:` / `data:` scheme into the report.
    Block them here so the renderer is the last line of defense.
    """
    try:
        return urlparse(url).scheme in ("http", "https")
    except (ValueError, TypeError):
        return False


def _format_fetched_at_french(fetched_at: datetime) -> str:
    """Format a datetime as e.g. '28 avril 2026'."""
    months = {
        1: "janvier",
        2: "février",
        3: "mars",
        4: "avril",
        5: "mai",
        6: "juin",
        7: "juillet",
        8: "août",
        9: "septembre",
        10: "octobre",
        11: "novembre",
        12: "décembre",
    }
    return f"{fetched_at.day} {months[fetched_at.month]} {fetched_at.year}"


def _fact_pack_body(fact_pack: FactPack) -> str:
    """Render the class-appropriate facts compactly, via the shared renderer.

    Uses :func:`finwiz.analysis.fact_pack.render.to_rows` — the same labels the
    qualitative prompt sees (spec decision D5) — so this table cell can never
    show a label the prompt doesn't. Best-effort: an unrenderable pack (e.g. a
    schema-drifted cache) omits the body rather than raising.
    """
    try:
        rows = to_rows(fact_pack)
    except Exception:
        return ""
    parts: list[str] = []
    for label, value in rows:
        text = str(value).replace("\n", " ").strip()
        if len(text) > _MAX_BODY_VALUE_CHARS:
            text = text[: _MAX_BODY_VALUE_CHARS - 1].rstrip() + "…"
        if text:
            parts.append(f"<strong>{escape(label)}</strong> : {escape(text)}")
    if not parts:
        return ""
    return f'<div class="small muted fact-pack-body">{" · ".join(parts)}</div>'


def _fact_pack_provenance_footer(fact_pack: FactPack | None) -> str:
    """Render the fact-pack body plus a provenance pill + citations footnote.

    Maps freshness to a colored pill:
      - fresh → green
      - recent → neutral
      - stale → amber (with confidence shown)
      - None → muted "Faits non vérifiés" note (legacy callers only)
    """
    if fact_pack is None:
        return '<small class="muted">Faits non vérifiés pour cette analyse.</small>'

    body = _fact_pack_body(fact_pack)
    fetched_french = _format_fetched_at_french(fact_pack.fetched_at)

    if fact_pack.freshness == "fresh":
        pill = f'<span class="pill pill-green" title="Sources Perplexity vérifiées">✓ Faits actuels: vérifiés via Perplexity le {escape(fetched_french)}</span>'
    elif fact_pack.freshness == "recent":
        pill = f'<span class="pill pill-neutral">Faits vérifiés via Perplexity le {escape(fetched_french)}</span>'
    else:  # stale
        pill = (
            f'<span class="pill pill-amber" '
            f'title="Confidence {fact_pack.confidence:.2f}">'
            f"⚠️ Faits vérifiés il y a >7 jours — à actualiser "
            f"(confidence {fact_pack.confidence:.2f})</span>"
        )

    safe_citations = [url for url in fact_pack.source_citations if _is_safe_url(url)]
    if safe_citations:
        citations = " ".join(f'<a href="{escape(url, quote=True)}" rel="noopener" target="_blank">[{i + 1}]</a>' for i, url in enumerate(safe_citations[:5]))
        pill += f' <small class="muted">Sources: {citations}</small>'

    return f'<div class="fact-pack-footer">{body}{pill}</div>'
