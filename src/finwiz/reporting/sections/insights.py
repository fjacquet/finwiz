"""Per-holding "quintessence" insight cards + LLM cost summary for the consolidated report.

These two sections surface the most expensive AI research — distilled per-holding
investment synthesis, SEC moat/risks, fundamentals, contextual risks and verified
fact-pack facts — into the single consolidated report, plus the real LLM spend.

AI Minimalism: pure-Python rendering. Every input is HTML-escaped at the boundary
and every sub-block is omitted (never errors) when its data is absent.
"""

from __future__ import annotations

from html import escape
from typing import Any

from finwiz.reporting.sections.factpack import _is_safe_url

_REC_BADGE: dict[str, str] = {
    "BUY": '<span class="badge badge-buy">BUY</span>',
    "SELL": '<span class="badge badge-sell">SELL</span>',
    "HOLD": '<span class="badge badge-hold">HOLD</span>',
}


def _truncate(text: str, limit: int) -> str:
    """Trim whitespace and cap at ``limit`` chars with an ellipsis."""
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _rec_badge(recommendation: str) -> str:
    """Recommendation badge, defaulting to a neutral HOLD pill."""
    return _REC_BADGE.get(str(recommendation).upper(), _REC_BADGE["HOLD"])


def _scenario_bar(probs: dict[str, Any] | None) -> str:
    """Render a bull/base/bear stacked mini-bar from probabilities (0..1 each).

    Returns "" when probabilities are missing or unparseable.
    """
    if not isinstance(probs, dict):
        return ""
    try:
        bull = max(0.0, float(probs.get("bull", 0.0)))
        base = max(0.0, float(probs.get("base", 0.0)))
        bear = max(0.0, float(probs.get("bear", 0.0)))
    except (TypeError, ValueError):
        return ""
    total = bull + base + bear
    if total <= 0:
        return ""
    bull_pct, base_pct, bear_pct = (100 * bull / total, 100 * base / total, 100 * bear / total)
    return (
        '<div style="display:flex;height:14px;border-radius:7px;overflow:hidden;'
        'margin:6px 0;font-size:0;width:100%">'
        f'<div title="Haussier {bull_pct:.0f}%" style="width:{bull_pct:.1f}%;background:#22c55e"></div>'
        f'<div title="Neutre {base_pct:.0f}%" style="width:{base_pct:.1f}%;background:#9ca3af"></div>'
        f'<div title="Baissier {bear_pct:.0f}%" style="width:{bear_pct:.1f}%;background:#ef4444"></div>'
        "</div>"
        '<div class="small muted">'
        f"Haussier {bull_pct:.0f}% · Neutre {base_pct:.0f}% · Baissier {bear_pct:.0f}%"
        "</div>"
    )


def _prose_block(label: str, value: str, limit: int) -> str:
    """Render a labeled prose paragraph, or "" when empty."""
    text = _truncate(str(value or ""), limit)
    if not text:
        return ""
    return f"<p><strong>{escape(label)} :</strong> {escape(text)}</p>"


def _list_block(label: str, items: list[Any] | None, limit: int) -> str:
    """Render a labeled <ul> from a list of strings, or "" when empty."""
    if not items:
        return ""
    li = [f"<li>{escape(_truncate(str(it), limit))}</li>" for it in items if str(it).strip()]
    if not li:
        return ""
    return f"<p><strong>{escape(label)} :</strong></p><ul>{''.join(li)}</ul>"


def _fact_pack_block(fact_pack: dict[str, Any] | None) -> str:
    """Render distilled fact-pack facts (structure, events, leadership, citations)."""
    if not isinstance(fact_pack, dict):
        return ""
    rows: list[str] = []
    rows.append(_prose_block("Structure", fact_pack.get("corporate_structure", ""), 400))
    rows.append(_prose_block("Direction", fact_pack.get("leadership", ""), 300))
    rows.append(_list_block("Événements récents", (fact_pack.get("recent_events") or [])[:3], 240))
    body = "".join(r for r in rows if r)
    if not body:
        return ""

    freshness = str(fact_pack.get("freshness", "")).strip()
    fresh_note = f'<div class="small muted">Faits vérifiés (Perplexity) — fraîcheur : {escape(freshness)}.</div>' if freshness else ""

    safe = [u for u in (fact_pack.get("source_citations") or []) if _is_safe_url(str(u))][:5]
    citations = ""
    if safe:
        links = " ".join(f'<a href="{escape(str(u), quote=True)}" rel="noopener" target="_blank">[{i + 1}]</a>' for i, u in enumerate(safe))
        citations = f'<div class="small muted">Sources : {links}</div>'

    return f"<h4>Faits vérifiés</h4>{body}{fresh_note}{citations}"


def _render_card(ticker: str, grade: str, data: dict[str, Any], report_link: str | None) -> str:
    """Render one collapsible <details> quintessence card for a holding."""
    rec = str(data.get("final_recommendation", "HOLD"))
    confidence = str(data.get("recommendation_confidence", "")).strip()
    conf_note = f" · Confiance {escape(confidence)}" if confidence else ""
    grade_safe = escape(str(grade or "?"))
    grade_class = escape(f"grade-{str(grade or '').lower().replace('+', '-plus')}", quote=True)

    summary = f'<summary><strong>{escape(ticker)}</strong> <span class="{grade_class}">{grade_safe}</span> {_rec_badge(rec)}{conf_note}</summary>'

    parts: list[str] = [_scenario_bar(data.get("scenario_probabilities"))]
    parts.append(_prose_block("Thèse d'investissement", data.get("thesis", ""), 600))
    parts.append(_prose_block("Scénario haussier", data.get("bull_case", ""), 400))
    parts.append(_prose_block("Scénario baissier", data.get("bear_case", ""), 400))
    parts.append(_prose_block("Avantage concurrentiel (moat)", data.get("moat", ""), 300))
    parts.append(_prose_block("Risque SEC principal", data.get("top_sec_risk", ""), 300))
    parts.append(_list_block("Moteurs de croissance", (data.get("growth_drivers") or [])[:2], 240))
    parts.append(_prose_block("Positionnement concurrentiel", data.get("competitive_positioning", ""), 300))
    parts.append(_list_block("Risques clés", (data.get("key_risks") or [])[:3], 240))
    parts.append(_prose_block("Justification de l'objectif de cours", data.get("price_target_rationale", ""), 300))
    parts.append(_list_block("Actions immédiates", (data.get("immediate_actions") or [])[:2], 240))
    parts.append(_fact_pack_block(data.get("fact_pack")))

    if report_link:
        parts.append(f'<p><a class="ticker-link" href="{escape(report_link, quote=True)}">Analyse complète →</a></p>')

    body = "".join(p for p in parts if p)
    return f'<details class="highlight">{summary}{body}</details>'


def generate_holdings_insight_cards(insights: dict[str, dict] | None, holdings: list[Any] | None) -> str:
    """Render distilled per-holding "quintessence" cards for the consolidated report.

    Args:
        insights: ticker -> distilled insight dict (from ReportEnrichmentMixin
            ._extract_holdings_insights). Tickers without qualitative data are absent.
        holdings: portfolio holdings (HoldingDecision-like) used for authoritative
            per-ticker grade. Optional; falls back to the grade carried in ``insights``.

    Returns:
        HTML for the section, or "" when there are no insights to render.
    """
    if not insights:
        return ""

    grade_by_ticker: dict[str, str] = {}
    for h in holdings or []:
        t = getattr(h, "ticker", None)
        if t:
            grade_by_ticker[str(t)] = str(getattr(h, "grade", "") or "")

    cards: list[str] = []
    for ticker, data in insights.items():
        if not isinstance(data, dict):
            continue
        grade = grade_by_ticker.get(ticker) or str(data.get("grade", "") or "")
        report_link = data.get("report_link")
        cards.append(_render_card(ticker, grade, data, report_link if isinstance(report_link, str) else None))

    if not cards:
        return ""

    return f"""
  <div class="section">
    <h2>Quintessence par position</h2>
    <p class="muted">Synthèse distillée de la recherche IA approfondie (thèse, scénarios, moat, risques, faits vérifiés). Cliquez pour déplier ; l'analyse complète reste dans le rapport détaillé de chaque position.</p>
    {"".join(cards)}
  </div>
    """


def generate_cost_summary_section(cost_summary: dict[str, Any] | None) -> str:
    """Render the real LLM cost summary (total, calls, per-crew breakdown).

    Args:
        cost_summary: output of ``get_token_monitor().get_cost_summary()`` —
            ``{"total_cost": float, "call_count": int, "per_crew": {...}}``.

    Returns:
        HTML for the section, or "" when no usable cost data is available.
    """
    if not isinstance(cost_summary, dict):
        return ""

    per_crew = cost_summary.get("per_crew") or {}
    try:
        total_cost = float(cost_summary.get("total_cost", 0.0) or 0.0)
    except (TypeError, ValueError):
        total_cost = 0.0

    # call_count can be unreliable; derive from per-crew calls when it reads zero.
    try:
        call_count = int(cost_summary.get("call_count", 0) or 0)
    except (TypeError, ValueError):
        call_count = 0
    if call_count <= 0 and isinstance(per_crew, dict):
        call_count = sum(int(d.get("calls", 0) or 0) for d in per_crew.values() if isinstance(d, dict))

    if total_cost <= 0 and call_count <= 0:
        return ""

    rows: list[str] = []
    if isinstance(per_crew, dict):
        ordered = sorted(per_crew.items(), key=lambda kv: float(kv[1].get("cost", 0.0) or 0.0) if isinstance(kv[1], dict) else 0.0, reverse=True)
        for crew_name, data in ordered:
            if not isinstance(data, dict):
                continue
            try:
                cost = float(data.get("cost", 0.0) or 0.0)
                calls = int(data.get("calls", 0) or 0)
            except (TypeError, ValueError):
                continue
            tokens = data.get("tokens") or {}
            total_tokens = int(tokens.get("prompt", 0) or 0) + int(tokens.get("completion", 0) or 0) if isinstance(tokens, dict) else 0
            rows.append(f"<tr><td>{escape(str(crew_name))}</td><td>${cost:.4f}</td><td>{calls}</td><td>{total_tokens:,}</td></tr>")

    table = ""
    if rows:
        table = f"""
    <table>
      <thead>
        <tr><th>Crew</th><th>Coût</th><th>Appels</th><th>Tokens</th></tr>
      </thead>
      <tbody>
        {"".join(rows)}
      </tbody>
    </table>"""

    return f"""
  <div class="section">
    <h2>Coût réel de l'analyse IA</h2>
    <div class="highlight">
      <p>L'analyse qualitative approfondie a engagé <strong>${total_cost:.2f}</strong> de coûts LLM sur <strong>{call_count}</strong> appels. Le scoring quantitatif et le rendu des rapports restent 100% Python ($0).</p>
    </div>{table}
  </div>
    """
