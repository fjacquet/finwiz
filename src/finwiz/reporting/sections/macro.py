"""Macro dashboard and economic calendar sections (Phase 16 enrichment)."""

from __future__ import annotations

from html import escape


def _fmt_2f(value: float | int | str | None) -> str:
    """Format a possibly string/None numeric as 2dp, falling back to '-'."""
    if value is None:
        return "-"
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return "-"


def _traffic_light_class(indicator: str, value: float | None) -> str:
    """Return traffic-light CSS class for a macro indicator value.

    Thresholds:
    - VIX: green <=20, yellow 20-30, red >30
    - yield_curve: green >0.50, yellow 0-0.50, red <0
    - gdp: green >2.0, yellow 0-2.0, red <0
    - cpi: green <3.0, yellow 3.0-5.0, red >5.0
    - fed_rate: green <3.0, yellow 3.0-5.0, red >5.0
    - unemployment: green <5.0, yellow 5.0-7.0, red >7.0
    """
    if value is None:
        return ""

    if indicator == "vix":
        if value <= 20.0:
            return "traffic-light-green"
        if value <= 30.0:
            return "traffic-light-yellow"
        return "traffic-light-red"

    if indicator == "yield_curve":
        if value > 0.50:
            return "traffic-light-green"
        if value >= 0.0:
            return "traffic-light-yellow"
        return "traffic-light-red"

    if indicator == "gdp":
        if value > 2.0:
            return "traffic-light-green"
        if value >= 0.0:
            return "traffic-light-yellow"
        return "traffic-light-red"

    if indicator == "cpi":
        if value < 3.0:
            return "traffic-light-green"
        if value <= 5.0:
            return "traffic-light-yellow"
        return "traffic-light-red"

    if indicator == "fed_rate":
        if value < 3.0:
            return "traffic-light-green"
        if value <= 5.0:
            return "traffic-light-yellow"
        return "traffic-light-red"

    if indicator == "unemployment":
        if value < 5.0:
            return "traffic-light-green"
        if value <= 7.0:
            return "traffic-light-yellow"
        return "traffic-light-red"

    return "traffic-light-yellow"


def _fear_greed_label(value: int | float) -> str:
    """Return French label for Fear & Greed index value."""
    if value < 25:
        return "Peur Extreme"
    if value < 45:
        return "Peur"
    if value <= 55:
        return "Neutre"
    if value <= 75:
        return "Cupidite"
    return "Cupidite Extreme"


def _format_macro_value(indicator: str, value: float | None) -> str:
    """Format a macro indicator value for display.

    Coerces to float first: provider feeds often deliver numbers as strings,
    and a raw ``f"{value:.1f}"`` on a string raises TypeError mid-render.
    """
    if value is None:
        return "N/A"
    try:
        value = float(value)
    except (TypeError, ValueError):
        return escape(str(value))
    if indicator == "vix":
        return f"{value:.1f}"
    if indicator == "yield_curve":
        return f"{value:+.2f}%"
    if indicator in ("gdp", "cpi", "fed_rate", "unemployment"):
        return f"{value:.1f}%"
    return f"{value:.2f}"


def generate_macro_dashboard_section(macro_snapshot: dict | None) -> str:
    """Generate portfolio-level macro dashboard with traffic-light indicators and Fear & Greed gauge.

    Args:
        macro_snapshot: Dict with keys matching MacroSnapshot fields:
            vix, yield_curve_spread, gdp_growth, cpi_yoy, fed_rate,
            unemployment_rate, fear_greed_index, fear_greed_label.

    Returns:
        HTML string for the macro dashboard section, or "" if no data.
    """
    if not macro_snapshot:
        return ""

    # Define the 6 indicator cards
    indicators = [
        ("vix", "VIX", macro_snapshot.get("vix")),
        ("yield_curve", "Courbe des Taux", macro_snapshot.get("yield_curve_spread")),
        ("gdp", "Croissance PIB", macro_snapshot.get("gdp_growth")),
        ("cpi", "IPC (Inflation)", macro_snapshot.get("cpi_yoy")),
        ("fed_rate", "Taux Directeur Fed", macro_snapshot.get("fed_rate")),
        ("unemployment", "Chomage", macro_snapshot.get("unemployment_rate")),
    ]

    indicator_cards: list[str] = []
    for key, name, value in indicators:
        tl_class = _traffic_light_class(key, value)
        formatted = _format_macro_value(key, value)
        dot_html = f'<span class="traffic-light {tl_class}"></span>' if tl_class else ""

        indicator_cards.append(f"""
        <div class="macro-card">
          <h4>{name}</h4>
          <div class="macro-value">{dot_html}{formatted}</div>
        </div>""")

    cards_html = "".join(indicator_cards)

    # Fear & Greed gauge
    fg_index = macro_snapshot.get("fear_greed_index")
    if fg_index is not None:
        fg_value = int(fg_index)
        fg_label = _fear_greed_label(fg_value)
        marker_pct = max(0, min(100, fg_value))
        gauge_html = f"""
    <div style="margin-top:20px">
      <h3>Indice Fear &amp; Greed</h3>
      <div class="fear-greed-value">{fg_value}</div>
      <div class="fear-greed-gauge">
        <div class="fear-greed-marker" style="left:{marker_pct}%"></div>
      </div>
      <div class="fear-greed-label">{fg_label}</div>
    </div>"""
    else:
        gauge_html = """
    <div style="margin-top:20px">
      <h3>Indice Fear &amp; Greed</h3>
      <p class="muted">Indice non disponible</p>
    </div>"""

    return f"""
  <div class="section">
    <h2>Tableau de Bord Macroeconomique</h2>
    <p class="muted">Indicateurs macroeconomiques cles avec signalisation par couleur.</p>
    <div class="macro-grid">
      {cards_html}
    </div>
    {gauge_html}
  </div>
    """


def generate_economic_calendar_section(calendar_data: dict | None) -> str:
    """Generate upcoming economic events and earnings calendar section.

    Args:
        calendar_data: Dict with keys:
            economic_events: list of dicts with event, date, impact, estimate, prev
            earnings_events: list of dicts with symbol, date, eps_estimate

    Returns:
        HTML string for the economic calendar section, or "" if no data.
    """
    if not calendar_data:
        return ""

    economic_events = calendar_data.get("economic_events", [])
    earnings_events = calendar_data.get("earnings_events", [])

    # Economic events table (max 15 rows)
    if economic_events:
        event_rows: list[str] = []
        for evt in economic_events[:15]:
            date = escape(str(evt.get("date", "")))
            event_name = escape(str(evt.get("event", "")))
            impact = escape(str(evt.get("impact", "") or ""))
            estimate_str = _fmt_2f(evt.get("estimate"))
            prev_str = _fmt_2f(evt.get("prev"))
            event_rows.append(f"<tr><td>{date}</td><td>{event_name}</td><td>{impact}</td><td>{estimate_str}</td><td>{prev_str}</td></tr>")

        events_html = f"""
      <h3>Evenements Economiques</h3>
      <table class="calendar-table">
        <thead>
          <tr><th>Date</th><th>Evenement</th><th>Impact</th><th>Estimation</th><th>Precedent</th></tr>
        </thead>
        <tbody>
          {"".join(event_rows)}
        </tbody>
      </table>"""
    else:
        events_html = """
      <h3>Evenements Economiques</h3>
      <p class="muted">Aucun evenement economique programme dans les 30 prochains jours.</p>"""

    # Earnings events table (max 20 rows)
    if earnings_events:
        earnings_rows: list[str] = []
        for ear in earnings_events[:20]:
            date = escape(str(ear.get("date", "")))
            symbol = escape(str(ear.get("symbol", "")))
            eps_str = _fmt_2f(ear.get("eps_estimate"))
            earnings_rows.append(f"<tr><td>{date}</td><td>{symbol}</td><td>{eps_str}</td></tr>")

        earnings_html = f"""
      <h3>Dates de Resultats</h3>
      <table class="calendar-table">
        <thead>
          <tr><th>Date</th><th>Symbole</th><th>BPA Estime</th></tr>
        </thead>
        <tbody>
          {"".join(earnings_rows)}
        </tbody>
      </table>"""
    else:
        earnings_html = """
      <h3>Dates de Resultats</h3>
      <p class="muted">Aucune date de resultats a venir.</p>"""

    return f"""
  <div class="section">
    <h2>Calendrier Economique</h2>
    <p class="muted">Evenements economiques et dates de resultats a venir.</p>
    {events_html}
    {earnings_html}
  </div>
    """
