"""Executive summary, strategic posture, and portfolio overview sections."""

from __future__ import annotations

from html import escape
from typing import Any

from finwiz.schemas.portfolio_review import PortfolioReview


def generate_strategic_posture_section(posture: dict | None) -> str:
    """Render the portfolio-wide strategic posture (PESTEL/SWOT/Porter synthesis).

    ``posture`` is a :class:`PortfolioStrategicPosture` model_dump. Returns "" when
    no posture is available so the surrounding report stays clean.
    """
    if not posture or not isinstance(posture, dict):
        return ""

    def _list(items: list[str] | None, emoji: str) -> str:
        if not items:
            return ""
        return "<ul>" + "".join(f"<li>{emoji} {escape(str(x))}</li>" for x in items) + "</ul>"

    macro = escape(posture.get("macro_environment_summary") or "")
    competitive = escape(posture.get("competitive_landscape_summary") or "")
    overall = escape(posture.get("overall_assessment") or "")
    # Schema defaults strategic_score / confidence to 0.5; only fall back to that
    # when the field is genuinely missing (key absent or None) — never use `or 0.5`
    # because it masks a legitimate AI-rated 0.0 (worst signal) as 50% (neutral).
    score_raw = posture.get("strategic_score")
    conf_raw = posture.get("confidence")
    score_pct = round((score_raw if score_raw is not None else 0.5) * 100)
    conf_pct = round((conf_raw if conf_raw is not None else 0.5) * 100)
    themes = posture.get("dominant_themes") or []
    themes_html = "".join(f'<span class="badge">{escape(str(t))}</span>' for t in themes)

    return f"""
  <div class="section">
    <h2>🎯 Posture Stratégique du Portefeuille</h2>
    <div class="metrics-grid">
      <div class="metric-card">
        <h4>Score Stratégique Global</h4>
        <p class="metric-value">{score_pct}%</p>
        <small>Confiance : {conf_pct}%</small>
      </div>
    </div>

    {f"<h3>🌍 Environnement Macro</h3><p>{macro}</p>" if macro else ""}
    {f"<h3>⚔️ Paysage Concurrentiel</h3><p>{competitive}</p>" if competitive else ""}

    <h3>📐 SWOT Agrégé</h3>
    <div class="metrics-grid">
      <div class="metric-card"><h4>💪 Forces du portefeuille</h4>{_list(posture.get("portfolio_strengths"), "✅")}</div>
      <div class="metric-card"><h4>🪫 Faiblesses</h4>{_list(posture.get("portfolio_weaknesses"), "•")}</div>
      <div class="metric-card"><h4>🚀 Opportunités</h4>{_list(posture.get("portfolio_opportunities"), "→")}</div>
      <div class="metric-card"><h4>⚡ Menaces</h4>{_list(posture.get("portfolio_threats"), "⚠️")}</div>
    </div>

    {f"<h3>🧭 Thèmes Dominants</h3><div>{themes_html}</div>" if themes_html else ""}
    {f"<h3>📝 Synthèse</h3><p>{overall}</p>" if overall else ""}
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
