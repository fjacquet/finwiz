"""Per-holding market sentiment section (Phase 16 enrichment)."""

from __future__ import annotations

from html import escape


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


def generate_sentiment_section(holdings_sentiment: dict[str, dict] | None) -> str:
    """Generate per-holding sentiment summary section for consolidated report.

    Args:
        holdings_sentiment: Dict mapping ticker -> sentiment data with keys:
            score, confidence, article_count, bullish_count, bearish_count,
            neutral_count, top_headlines (list of dicts with title, source, sentiment_label).

    Returns:
        HTML string for the sentiment section, or "" if no data.
    """
    if not holdings_sentiment:
        return ""

    cards: list[str] = []
    for ticker, data in holdings_sentiment.items():
        score = data.get("score", 0.0)
        confidence = data.get("confidence", 0.0)
        article_count = data.get("article_count", 0)
        bullish = data.get("bullish_count", 0)
        bearish = data.get("bearish_count", 0)
        neutral = data.get("neutral_count", 0)
        top_headlines = data.get("top_headlines", [])

        color_style = _sentiment_color(score)
        label = _sentiment_label(score)

        # Build headlines list (max 3)
        headlines_html = ""
        if top_headlines:
            headline_items: list[str] = []
            for hl in top_headlines[:3]:
                title = escape(str(hl.get("title", "")))
                source = escape(str(hl.get("source", "")))
                hl_label = escape(str(hl.get("sentiment_label", "")))
                headline_items.append(f'<li><small>{title} <em>({source})</em> <span class="badge badge-hold">{hl_label}</span></small></li>')
            headlines_html = f"<h4>Titres Recents</h4><ul>{''.join(headline_items)}</ul>"

        cards.append(f"""
      <div class="stat-card">
        <h4>{escape(ticker)}</h4>
        <div style="{color_style};font-size:1.5em">{score:+.2f}</div>
        <div><small>{label}</small></div>
        <table style="width:100%;font-size:0.85em;margin-top:8px">
          <tr><td>Score de Sentiment</td><td style="{color_style}">{score:+.2f}</td></tr>
          <tr><td>Confiance</td><td>{confidence:.0%}</td></tr>
          <tr><td>Articles</td><td>{article_count}</td></tr>
          <tr><td>Haussier / Baissier / Neutre</td><td>{bullish} / {bearish} / {neutral}</td></tr>
        </table>
        {headlines_html}
      </div>""")

    cards_html = "".join(cards)

    return f"""
  <div class="section">
    <h2>Sentiment de Marche</h2>
    <p class="muted">Analyse du sentiment des actualites financieres par position.</p>
    <div class="stats-grid">
      {cards_html}
    </div>
  </div>
    """
