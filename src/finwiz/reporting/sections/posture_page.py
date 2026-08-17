"""The dedicated strategic posture page.

Separate from the family artifact because the posture is analyst-length and the
family artifact is a decision sheet (see Task 11). Coverage leads the page: a
portfolio score is meaningless without the fraction of the portfolio it speaks
for, so the coverage banner renders first and the score is never shown without
it nearby.

Verdicts stay in the open; the analyst-length synthesis behind each theme goes
inside a ``<details>`` disclosure. That split — not just moving the prose to a
new URL — is the actual readability fix.

Presentation layer: takes a plain ``dict`` (a ``model_dump()``), not a
Pydantic model, so this module stays schema-free per reporting/CLAUDE.md.
"""

from __future__ import annotations

from html import escape
from typing import Any

from finwiz.reporting.css_styles import get_report_css
from finwiz.reporting.markdown_fragment import _is_safe_url, render_markdown_fragment, render_markdown_inline

# (heading, verdict field, analyst-length detail field)
_THEMES = (
    ("🌍 Environnement Macro", "macro_verdict", "macro_environment_summary"),
    ("⚔️ Paysage Concurrentiel", "competitive_verdict", "competitive_landscape_summary"),
    ("📐 SWOT Agrégé", "swot_verdict", "overall_assessment"),
)

# (heading, emoji, posture field) — the four aggregated SWOT lists.
_SWOT_LISTS = (
    ("Forces du portefeuille", "✅", "portfolio_strengths"),
    ("Faiblesses", "🪫", "portfolio_weaknesses"),
    ("Opportunités", "🚀", "portfolio_opportunities"),
    ("Menaces", "⚡", "portfolio_threats"),
)

# (label, framework key inside each holding's strategic dict)
_FRAMEWORK_COLUMNS = (
    ("PESTEL", "pestel"),
    ("SWOT", "swot"),
    ("Porter", "five_forces"),
)


def _coverage_banner(posture: dict[str, Any]) -> str:
    """Coverage first, always. Complete and incomplete coverage must look different.

    Follows the report's existing ``highlight`` + state-modifier convention
    (see ``sections/analysis.py``, ``sections/discovery.py``,
    ``sections/portfolio_summary.py``) rather than a bare state class: the
    ``.highlight`` rule supplies padding/border-radius/margin and
    ``.warning``/``.success`` supply the color cue. Neither alone reproduces
    the existing banner look.
    """
    covered = posture.get("holdings_covered", 0)
    total = posture.get("holdings_total", 0)
    pct = posture.get("value_covered_pct", 0.0)
    uncovered = posture.get("uncovered_tickers") or []
    state = "success" if covered == total and total > 0 else "warning"
    missing = f"<p>Non couverts : {escape(', '.join(str(t) for t in uncovered))}</p>" if uncovered else ""
    return (
        f'<div class="highlight {state}" id="couverture">'
        "<h2>Couverture</h2>"
        f"<p><strong>{covered} / {total}</strong> holdings · {pct:.1f} % de la valeur du portefeuille</p>"
        f"{missing}"
        "</div>"
    )


def _dominant_themes(posture: dict[str, Any], citations: list[str] | None) -> str:
    """Top 3-5 recurring themes — the single most useful line for a family reader.

    Rendered prominently (right after coverage, before the analyst blocks)
    because a handful of short themes beats three paragraphs of synthesis.

    Themes are model-authored, so they go through the inline render boundary
    rather than bare ``escape()``: a badge reading "**Résilience** énergétique
    [1]" is the same readability defect this branch set out to remove, one
    surface further along.
    """
    themes = posture.get("dominant_themes") or []
    if not themes:
        return ""
    badges = "".join(f'<span class="badge">{render_markdown_inline(t, citations=citations)}</span>' for t in themes)
    return f'<section class="section"><h2>🧭 Thèmes Dominants</h2><div>{badges}</div></section>'


def _theme_block(title: str, verdict: str, detail_md: str, citations: list[str] | None) -> str:
    """Verdict in the open; analyst-length prose behind a disclosure.

    ``title`` is a module constant, so plain ``escape()`` is right for it.
    ``verdict`` is model-authored and goes through the inline render boundary
    (see :func:`_dominant_themes`).
    """
    detail = render_markdown_fragment(detail_md, citations=citations)
    body = f"<details><summary>Détail</summary>{detail}</details>" if detail else ""
    verdict_inline = render_markdown_inline(verdict, citations=citations)
    verdict_html = f'<p class="verdict">{verdict_inline}</p>' if verdict_inline else ""
    return f'<section class="section"><h2>{escape(title)}</h2>{verdict_html}{body}</section>'


def _swot_lists(posture: dict[str, Any], citations: list[str] | None) -> str:
    """Four short lists, not merged into prose. Skipped entirely if all empty.

    Each item is model-authored — inline render boundary, not bare
    ``escape()`` (see :func:`_dominant_themes`). Headings are constants.
    """
    cards = []
    for heading, emoji, field in _SWOT_LISTS:
        items = posture.get(field) or []
        if not items:
            continue
        rows = "".join(f"<li>{emoji} {render_markdown_inline(item, citations=citations)}</li>" for item in items)
        cards.append(f'<div class="metric-card"><h4>{emoji} {escape(heading)}</h4><ul>{rows}</ul></div>')
    if not cards:
        return ""
    return f'<section class="section"><h2>📐 SWOT Agrégé du Portefeuille</h2><div class="metrics-grid">{"".join(cards)}</div></section>'


def _score_cell(framework: dict[str, Any] | None) -> str:
    if not framework:
        return '<td class="num">—</td>'
    score = framework.get("strategic_score")
    if score is None:
        return '<td class="num">—</td>'
    return f'<td class="num">{score * 100:.0f} %</td>'


def _per_holding_table(holdings_strategic: dict[str, dict] | None) -> str:
    """A compact scannable score table, not a bare ticker list.

    A section promising per-line detail with only a ticker in it is worse
    than no section — see the family artifact's own former "Par ligne". Each
    holding's PESTEL/SWOT/Porter ``strategic_score`` earns the section its
    place instead. The three column headers are untranslated analyst jargon,
    so a one-sentence legend glosses what each score actually measures --
    a glance-level explanation, not a tutorial.
    """
    if not holdings_strategic:
        return ""
    header_cells = "".join(f"<th>{label}</th>" for label, _ in _FRAMEWORK_COLUMNS)
    rows = []
    for ticker in sorted(holdings_strategic):
        analysis = holdings_strategic[ticker] or {}
        cells = "".join(_score_cell(analysis.get(key)) for _, key in _FRAMEWORK_COLUMNS)
        rows.append(f"<tr><td><strong>{escape(ticker)}</strong></td>{cells}</tr>")
    legend = (
        '<p class="muted small">PESTEL évalue l\'environnement macro-économique et réglementaire, '
        "SWOT les forces et faiblesses internes, et Porter la solidité de l'avantage concurrentiel.</p>"
    )
    return f'<section class="section"><h2>Par ligne</h2>{legend}<table><thead><tr><th>Ticker</th>{header_cells}</tr></thead><tbody>{"".join(rows)}</tbody></table></section>'


def _sources(citations: list[str] | None) -> str:
    """Render the sources list, dropping any URL the render boundary would reject.

    Citation URLs are model-supplied. ``escape(u, quote=True)`` stops attribute
    breakout but not an executable scheme, so a ``javascript:`` citation would
    become a clickable payload here while ``render_markdown_fragment`` refuses
    the identical string. Both surfaces apply ``_is_safe_url`` so the boundary
    is one rule rather than two.
    """
    if not citations:
        return ""
    items = "".join(
        f'<li id="src{i}"><a href="{escape(u, quote=True)}" rel="noopener noreferrer" target="_blank">{escape(u)}</a></li>' for i, u in enumerate(citations, 1) if _is_safe_url(u)
    )
    if not items:
        return ""
    return f'<section class="section"><h2>Sources</h2><ol>{items}</ol></section>'


def generate_posture_page(
    posture: dict[str, Any],
    *,
    holdings_strategic: dict[str, dict] | None = None,
    citations: list[str] | None = None,
) -> str:
    """Render the standalone posture page as a complete HTML document."""
    score = posture.get("strategic_score") or 0.0
    confidence = posture.get("confidence") or 0.0
    score_pct = score * 100
    conf_pct = confidence * 100

    themes = "".join(_theme_block(title, posture.get(verdict_field, ""), posture.get(detail_field, ""), citations) for title, verdict_field, detail_field in _THEMES)

    return (
        '<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>Posture Stratégique — FinWiz</title>"
        f"<style>{get_report_css()}</style></head><body>"
        "<h1>Posture Stratégique du Portefeuille</h1>"
        f"{_coverage_banner(posture)}"
        f'<p class="verdict">Score stratégique global : <strong>{score_pct:.0f} %</strong> · Confiance : <strong>{conf_pct:.0f} %</strong></p>'
        f"{_dominant_themes(posture, citations)}"
        f"{themes}"
        f"{_swot_lists(posture, citations)}"
        f"{_per_holding_table(holdings_strategic)}"
        f"{_sources(citations)}"
        "</body></html>"
    )
