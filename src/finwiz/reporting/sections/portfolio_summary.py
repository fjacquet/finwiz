"""Executive summary, strategic posture, and portfolio overview sections."""

from __future__ import annotations

from html import escape
from typing import Any

from finwiz.reporting.markdown_fragment import render_markdown_inline
from finwiz.schemas.portfolio_review import PortfolioReview


def _fmt_eur(value: float | None) -> str:
    """Format a EUR amount French-style: space-grouped thousands + euro sign.

    ``None`` → ``"—"`` (never "None"/"0 €") so the UI degrades gracefully when
    no CSV Quantity resolved. Example: ``53772.0`` → ``"53 772 €"``.
    """
    if value is None:
        return "—"
    # Round to whole euros, group thousands with a plain space (French convention).
    grouped = f"{round(value):,}".replace(",", " ")
    return f"{grouped} €"


def generate_allocation_section(portfolio_review: PortfolioReview) -> str:
    """Render the EUR allocation hero + per-holding weight breakdown.

    Surfaces the already-serialized ``total_value_eur`` and per-holding
    ``weight`` / ``eur_value`` data. Degrades gracefully: when nothing could be
    priced (no CSV Quantity), renders the hero shell with a French info note
    instead of numbers — never "0 €" / "None".
    """
    total = portfolio_review.total_value_eur
    weighted = [h for h in portfolio_review.holdings if h.weight is not None]

    # Graceful path: no priced total or no weighted holding → tasteful info note.
    if total is None or not weighted:
        return (
            """
  <div class="section">
    <h2>💰 Allocation du portefeuille</h2>
    <div class="value-hero">
      <div class="hero-meta">Valeur totale du portefeuille</div>
      <div class="hero-value muted">—</div>
      <p class="alloc-note">💡 Renseignez la colonne <code>Quantity</code> de vos fichiers """
            + """<code>data/*.csv</code> puis relancez l'analyse pour visualiser l'allocation en euros.</p>
    </div>
  </div>
"""
        )

    n_positions = len(portfolio_review.holdings)
    n_classes = len({h.asset_class for h in weighted})

    # Sort by weight desc so the largest exposure leads.
    rows = sorted(weighted, key=lambda h: h.weight or 0.0, reverse=True)
    alloc_rows = []
    for h in rows:
        pct = (h.weight or 0.0) * 100
        name_safe = escape(h.name or "Unknown")
        ticker_safe = escape(h.ticker or "—")
        alloc_rows.append(
            f"""
      <div class="alloc-row">
        <div class="alloc-label"><strong>{ticker_safe}</strong> <span class="muted small">{name_safe}</span></div>
        <div class="weight-bar"><div class="weight-bar-fill" style="width: {pct:.1f}%"></div></div>
        <div class="alloc-pct num">{pct:.1f}%</div>
        <div class="alloc-value num">{_fmt_eur(h.eur_value)}</div>
      </div>"""
        )
    alloc_html = "".join(alloc_rows)

    return f"""
  <div class="section">
    <h2>💰 Allocation du portefeuille</h2>
    <div class="value-hero">
      <div class="hero-meta">Valeur totale du portefeuille</div>
      <div class="hero-value num">{_fmt_eur(total)}</div>
      <div class="hero-meta">{n_positions} positions · {n_classes} classes d'actifs</div>
    </div>

    <h3>📊 Répartition par position</h3>
    <div class="alloc-list">
      {alloc_html}
    </div>
  </div>
"""


def generate_strategic_posture_section(posture: dict | None) -> str:
    """Verdict and link only; the analyst-length synthesis lives on its own page.

    This section used to embed the full PESTEL/SWOT/Porter prose, which rendered
    as a wall of raw markdown in a document meant for a family. ``posture`` is a
    :class:`PortfolioStrategicPosture` model_dump.

    When no posture is available this renders a short "indisponible" block
    rather than "". Silence is indistinguishable from "this report never had a
    posture", and the branch that made ``competitive_verdict`` /
    ``swot_verdict`` / ``strategic_score`` / ``confidence`` required also made
    losing the whole posture the normal consequence of a truncated model
    response. Failing loudly was the right call; failing silently *to the
    reader* turns "wrong data" into "lost data".
    The block carries no score (0 % would read as a measurement) and no link to
    the companion page, which is not written when there is no posture.

    The three verdicts are model-authored and go through the inline render
    boundary, not bare ``escape()``: escaping alone left "Le **durcissement**
    réglementaire pèse [1]" in the family artifact, which is the same
    readability defect this branch exists to remove. No citations are threaded
    here, so ``[n]`` markers are stripped rather than shown pointing at nothing.
    """
    if not posture or not isinstance(posture, dict):
        return """
  <div class="section">
    <h2>🎯 Posture Stratégique du Portefeuille</h2>
    <div class="highlight warning">
      <p>Posture stratégique indisponible pour ce run — la synthèse n'a pas abouti.
      Aucun score stratégique global n'est affiché : il serait inventé.</p>
    </div>
  </div>
"""

    covered = posture.get("holdings_covered")
    total = posture.get("holdings_total")
    # The score is never shown alone -- the fraction it speaks for goes right
    # beside it, in the same paragraph.
    coverage = f" (sur {covered}/{total} lignes)" if covered is not None and total else ""

    score_pct = round((posture.get("strategic_score") or 0.0) * 100)
    conf_pct = round((posture.get("confidence") or 0.0) * 100)

    return f"""
  <div class="section">
    <h2>🎯 Posture Stratégique du Portefeuille</h2>
    <p><strong>{score_pct} %</strong>{coverage} · Confiance : {conf_pct} %</p>
    <ul>
      <li>{render_markdown_inline(posture.get("competitive_verdict"))}</li>
      <li>{render_markdown_inline(posture.get("swot_verdict"))}</li>
    </ul>
    <p><a href="finwiz_posture_strategique.html">Analyse stratégique complète →</a></p>
  </div>
"""


def generate_executive_summary(portfolio_stats: dict[str, Any], trust_banner_html: str = "") -> str:
    """Generate executive summary section.

    ``trust_banner_html`` is the pre-rendered HTML produced by
    :func:`finwiz.reporting.python_report_generator.render_trust_banner`.
    When provided it replaces the former ad-hoc coverage-threshold logic entirely —
    TrustBanner.from_coverage already encoded all the state rules.
    """
    grade = portfolio_stats["portfolio_grade"]
    grade_class = f"grade-{grade.lower().replace('+', '-plus').replace('/', '-')}" if grade != "N/A" else "grade-na"

    # Don't wrap an N/A grade in a green "success" panel right under a red
    # coverage banner — pick a neutral "warning" wrapper to match the
    # incomplete-data state the banner already announced.
    grade_panel_class = "warning" if grade == "N/A" else "success"

    return f"""
  <div class="section">
    <h2>Executive Summary</h2>

    {trust_banner_html}

    <div class="highlight {grade_panel_class}">
      <h3>Portfolio Grade: <span class="{grade_class}">{grade}</span></h3>
      <p>Average score: <strong>{portfolio_stats["average_score"]:.3f}</strong> out of 1.000</p>
    </div>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-number">{portfolio_stats["total_holdings"]}</div>
        <div>Total Positions</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">{portfolio_stats["a_plus_count"]}</div>
        <div>A+/A Opportunities</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">{portfolio_stats["underperforming_count"]}</div>
        <div>Underperforming Positions</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">{portfolio_stats["recommendation_counts"]["SELL"]}</div>
        <div>SELL Recommendations</div>
      </div>
    </div>

    <h3>Key Points</h3>
    <ul>
      <li><strong>Ultra-fast:</strong> Python portfolio scoring in seconds (deterministic, $0)</li>
      <li><strong>Deterministic:</strong> Consistent and reproducible results</li>
      <li><strong>Transparent:</strong> Verifiable and auditable Python calculations</li>
    </ul>
  </div>
        """


def generate_portfolio_overview(portfolio_review: PortfolioReview, portfolio_stats: dict[str, Any]) -> str:
    """Generate portfolio overview section."""
    total = portfolio_stats["total_holdings"]

    def pct(count: int) -> str:
        return f"{count / total * 100:.1f}%" if total > 0 else "0.0%"

    return f"""
  <div class="section">
    <h2>Portfolio Overview</h2>

    <h3>Asset Class Distribution</h3>
    <table>
      <thead>
        <tr><th>Asset Class</th><th>Positions</th><th>Percentage</th></tr>
      </thead>
      <tbody>
        <tr>
          <td>Stocks</td>
          <td>{portfolio_stats["asset_counts"]["stock"]}</td>
          <td>{pct(portfolio_stats["asset_counts"]["stock"])}</td>
        </tr>
        <tr>
          <td>ETFs</td>
          <td>{portfolio_stats["asset_counts"]["etf"]}</td>
          <td>{pct(portfolio_stats["asset_counts"]["etf"])}</td>
        </tr>
        <tr>
          <td>Crypto</td>
          <td>{portfolio_stats["asset_counts"]["crypto"]}</td>
          <td>{pct(portfolio_stats["asset_counts"]["crypto"])}</td>
        </tr>
      </tbody>
    </table>

    <h3>Grade Distribution</h3>
    <table>
      <thead>
        <tr><th>Grade</th><th>Positions</th><th>Percentage</th></tr>
      </thead>
      <tbody>
        <tr><td class="grade-a-plus">A+</td><td>{portfolio_stats["grade_counts"]["A+"]}</td><td>{pct(portfolio_stats["grade_counts"]["A+"])}</td></tr>
        <tr><td class="grade-a">A</td><td>{portfolio_stats["grade_counts"]["A"]}</td><td>{pct(portfolio_stats["grade_counts"]["A"])}</td></tr>
        <tr><td class="grade-b">B</td><td>{portfolio_stats["grade_counts"]["B"]}</td><td>{pct(portfolio_stats["grade_counts"]["B"])}</td></tr>
        <tr><td class="grade-c">C</td><td>{portfolio_stats["grade_counts"]["C"]}</td><td>{pct(portfolio_stats["grade_counts"]["C"])}</td></tr>
        <tr><td class="grade-d">D</td><td>{portfolio_stats["grade_counts"]["D"]}</td><td>{pct(portfolio_stats["grade_counts"]["D"])}</td></tr>
        <tr><td class="grade-f">F</td><td>{portfolio_stats["grade_counts"]["F"]}</td><td>{pct(portfolio_stats["grade_counts"]["F"])}</td></tr>
      </tbody>
    </table>
  </div>
        """
