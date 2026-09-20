"""Per-holding market sentiment section (Phase 16 enrichment)."""

from __future__ import annotations

from html import escape
from typing import Any

from finwiz.reporting.sections.common import plural


def _sentiment_color(score: float) -> str:
    """Return CSS inline style for a sentiment score."""
    if score > 0.2:
        return "color:#22c55e;font-weight:bold"
    if score < -0.2:
        return "color:#ef4444;font-weight:bold"
    return "color:#6b7280;font-weight:bold"


def _sentiment_label(score: float) -> str:
    """Return French sentiment label for a score."""
    if score > 0.2:
        return "Haussier"
    if score < -0.2:
        return "Baissier"
    return "Neutre"


def _headlines_cell(top_headlines: Any) -> str:
    """Headlines folded behind a per-row disclosure; ``—`` when there are none."""
    if not top_headlines:
        return '<td class="muted">—</td>'
    items: list[str] = []
    for hl in top_headlines[:3]:
        title = escape(str(hl.get("title", "")))
        source = escape(str(hl.get("source", "")))
        hl_label = escape(str(hl.get("sentiment_label", "")))
        items.append(f'<li><small>{title} <em>({source})</em> <span class="badge badge-hold">{hl_label}</span></small></li>')
    return f"<td><details><summary>Titres Recents ({len(items)})</summary><ul>{''.join(items)}</ul></details></td>"


def _sentiment_row(ticker: str, data: dict[str, Any]) -> str:
    score = float(data.get("score", 0.0) or 0.0)
    color_style = _sentiment_color(score)
    return (
        f"<tr><td><strong>{escape(ticker)}</strong></td>"
        f'<td class="num" style="{color_style}">{score:+.2f}</td>'
        f"<td>{_sentiment_label(score)}</td>"
        f'<td class="num">{float(data.get("confidence", 0.0) or 0.0):.0%}</td>'
        f'<td class="num">{int(data.get("article_count", 0) or 0)}</td>'
        f'<td class="num">{data.get("bullish_count", 0)} / {data.get("bearish_count", 0)} / {data.get("neutral_count", 0)}</td>'
        f"{_headlines_cell(data.get('top_headlines'))}</tr>"
    )


def _digest_line(with_news: dict[str, dict[str, Any]], no_news: list[str]) -> str:
    """One portfolio-wide sentence: mean score, label counts, positions without news."""
    parts: list[str] = []
    if with_news:
        scores = [float(d.get("score", 0.0) or 0.0) for d in with_news.values()]
        mean = sum(scores) / len(scores)
        labels = [_sentiment_label(s) for s in scores]
        parts.append(f'<span style="{_sentiment_color(mean)}">Sentiment moyen {mean:+.2f}</span>')
        parts.append(plural(labels.count("Haussier"), "haussier"))
        parts.append(plural(labels.count("Baissier"), "baissier"))
        parts.append(plural(labels.count("Neutre"), "neutre"))
    else:
        parts.append("Aucune position avec actualités")
    if no_news:
        parts.append(f"{plural(len(no_news), 'position')} sans actualités")
    return f'<p class="sentiment-digest">{" · ".join(parts)}</p>'


def generate_sentiment_section(holdings_sentiment: dict[str, dict] | None) -> str:
    """Generate per-holding sentiment summary section for consolidated report.

    Renders a portfolio digest line, then one compact table row per holding
    that has news (bearish first, so the risk reads first) with the headlines
    folded per row, then a single line naming the holdings without news.

    Args:
        holdings_sentiment: Dict mapping ticker -> sentiment data with keys:
            score, confidence, article_count, bullish_count, bearish_count,
            neutral_count, top_headlines (list of dicts with title, source, sentiment_label).

    Returns:
        HTML string for the sentiment section, or "" if no data.
    """
    if not holdings_sentiment:
        return ""

    with_news = {t: d for t, d in holdings_sentiment.items() if int(d.get("article_count", 0) or 0) > 0}
    no_news = sorted(t for t in holdings_sentiment if t not in with_news)

    table_html = ""
    if with_news:
        ordered = sorted(with_news.items(), key=lambda kv: float(kv[1].get("score", 0.0) or 0.0))
        rows = "".join(_sentiment_row(t, d) for t, d in ordered)
        table_html = f"""
    <table>
      <thead>
        <tr><th>Ticker</th><th>Score de Sentiment</th><th>Tendance</th><th>Confiance</th><th>Articles</th><th>Haussier / Baissier / Neutre</th><th>Titres</th></tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>"""

    no_news_html = ""
    if no_news:
        tickers = ", ".join(escape(t) for t in no_news)
        no_news_html = f'<p class="small muted">Sans actualités ({len(no_news)}) : {tickers}</p>'

    return f"""
  <div class="section">
    <h2>Sentiment de Marche</h2>
    <p class="muted">Analyse du sentiment des actualites financieres par position, du plus baissier au plus haussier.</p>
    {_digest_line(with_news, no_news)}
    {table_html}
    {no_news_html}
  </div>
    """
