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
        # A list-valued row (holdings, recent events, allocation buckets) is
        # joined compactly for this one-line table cell; a string value is
        # prose and may itself contain a raw newline (yfinance's
        # longBusinessSummary is unedited scraped text) -- flattened to a
        # space rather than mistaken for a list the way insights.py's old
        # "\n" sniff used to.
        if isinstance(value, list):
            text = " · ".join(str(v).strip() for v in value if str(v).strip())
        else:
            text = str(value).replace("\n", " ").strip()
        if len(text) > _MAX_BODY_VALUE_CHARS:
            text = text[: _MAX_BODY_VALUE_CHARS - 1].rstrip() + "…"
        if text:
            parts.append(f"<strong>{escape(label)}</strong> : {escape(text)}")
    if not parts:
        return ""
    return f'<div class="small muted fact-pack-body">{" · ".join(parts)}</div>'


# Reader-facing names for the internal source identifiers in FactPack.sources_used.
# The tooltip reads "Vérifié via {label}", so these are prose, not keys: a reader
# seeing "yfinance.funds_data" in a financial report reads it as leaked debug output.
#
# Both yfinance.info and yfinance.funds_data map to the same name on purpose — the
# source really is Yahoo Finance either way, and the endpoint split is our concern,
# not the reader's. _sources_label de-duplicates, so a fund pack drawing on both
# says "Yahoo Finance" once.
#
# composer.schema_fallback is deliberately absent. It marks a pack the exception
# backstop assembled: a diagnostic about how the pack was built, not a place any
# fact came from. Rendering it as provenance told the reader the pack was
# "verified via composer.schema_fallback", which is both meaningless and false.
_SOURCE_LABELS: dict[str, str] = {
    "yfinance.info": "Yahoo Finance",
    "yfinance.funds_data": "Yahoo Finance",
    "yfinance.sec_filings": "dépôts SEC",
    "yfinance.news": "presse financière",
    "perplexity.gap_fill": "Perplexity",
    "etf_expense_ratios.yaml": "table de frais interne",
}


def _sources_label(fact_pack: FactPack) -> str:
    """Truthful, reader-facing label for the pill's provenance claim.

    Translates the pack's ``sources_used`` identifiers into names a reader can
    act on, de-duplicated and in first-seen order, and falls back to a generic
    phrase rather than naming a source that may not have run. Packs are built
    from yfinance and a curated table, with Perplexity demoted to an optional
    gap-filler that may never fire — the pill must not claim Perplexity
    verification unconditionally.

    An identifier with no entry in ``_SOURCE_LABELS`` is omitted rather than
    printed raw, so adding a source without adding its label degrades to the
    generic phrase instead of leaking an internal name into a report. If you add
    a source, add it above.
    """
    seen: list[str] = []
    for identifier in fact_pack.sources_used:
        label = _SOURCE_LABELS.get(identifier)
        if label is not None and label not in seen:
            seen.append(label)
    if seen:
        return ", ".join(seen)
    return "sources structurées"


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
    sources_label = _sources_label(fact_pack)

    if fact_pack.freshness == "fresh":
        pill = f'<span class="pill pill-green" title="Vérifié via {escape(sources_label)}">✓ Faits actuels — vérifiés le {escape(fetched_french)}</span>'
    elif fact_pack.freshness == "recent":
        pill = f'<span class="pill pill-neutral" title="Vérifié via {escape(sources_label)}">Faits vérifiés le {escape(fetched_french)}</span>'
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
