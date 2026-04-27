"""
Report section generators for Python report generation.

This module contains section generators extracted from PythonReportGenerator
for the family financial plan HTML report.
"""

from html import escape
from typing import Any

from finwiz.schemas.portfolio_review import HoldingDecision, PortfolioReview


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


def generate_executive_summary(portfolio_stats: dict[str, Any]) -> str:
    """Generate executive summary section."""
    grade = portfolio_stats["portfolio_grade"]
    grade_class = f"grade-{grade.lower().replace('+', '-plus').replace('/', '-')}" if grade != "N/A" else "grade-na"

    # Coverage banner — truthful display of how many holdings actually got deep
    # analysis vs. the "Analyse en attente" placeholder. Three states:
    #   ✅ full coverage   — green, no warning
    #   ⚠️ partial         — amber, encourage rerun
    #   ❌ zero coverage   — red, explicit "ne pas décider sur ce rapport"
    coverage = portfolio_stats.get("coverage") or {"analyzed": 0, "total": 0}
    analyzed = coverage.get("analyzed", 0)
    total = coverage.get("total", 0)
    if total == 0:
        coverage_html = ""
    elif analyzed == total:
        coverage_html = f'<div class="highlight success" style="margin-bottom:12px;">✅ <strong>{analyzed}/{total} holdings analysées</strong> — couverture complète.</div>'
    elif analyzed == 0:
        coverage_html = (
            f'<div class="highlight" style="background:#fef2f2;border:2px solid #dc2626;color:#991b1b;margin-bottom:12px;">'
            f"❌ <strong>0/{total} holdings analysées</strong> — données partielles. "
            "<strong>NE PAS prendre de décisions sur ce rapport.</strong> Relancez l'analyse approfondie."
            f"</div>"
        )
    else:
        pending = total - analyzed
        coverage_html = (
            f'<div class="highlight" style="background:#fffbeb;border:2px solid #f59e0b;color:#92400e;margin-bottom:12px;">'
            f"⚠️ <strong>{analyzed}/{total} holdings analysées</strong> — {pending} en attente. "
            "Le score de portefeuille n'inclut pas les holdings sans analyse."
            f"</div>"
        )

    return f"""
  <div class="section">
    <h2>Executive Summary</h2>

    {coverage_html}

    <div class="highlight success">
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


def _get_recommendation_badge(grade: str, recommended_action: str | None) -> str:
    """Get recommendation badge HTML based on grade."""
    if grade in ["A+", "A"]:
        return '<span class="badge badge-buy">BUY</span>'
    if grade in ["D", "F", "N/A"]:
        return '<span class="badge badge-sell">SELL</span>'
    if grade in ["B+", "B", "C+", "C"]:
        return '<span class="badge badge-hold">HOLD</span>'

    # Fallback to recommended_action
    if recommended_action and "BUY" in recommended_action:
        return '<span class="badge badge-buy">BUY</span>'
    if recommended_action and "SELL" in recommended_action:
        return '<span class="badge badge-sell">SELL</span>'
    return '<span class="badge badge-hold">HOLD</span>'


def _get_deep_analysis_link(ticker: str, asset_class: str) -> str:
    """Generate relative link to deep analysis report if available.

    Args:
        ticker: The ticker symbol
        asset_class: The asset class (stock, etf, crypto)

    Returns:
        Relative path to deep analysis HTML file

    Note:
        Reports are now stored in unified structure: output/{asset_class}/{ticker}_report.html
        Generated on-the-fly by DeepAnalysisOrchestrator._store_enriched_analysis()
    """
    asset_class_lower = asset_class.lower()
    # Unified output structure: output/stock/, output/etf/, output/crypto/
    return f"{asset_class_lower}/{ticker}_report.html"


def generate_holdings_analysis(holdings: list[HoldingDecision]) -> str:
    """Generate detailed holdings analysis."""
    sorted_holdings = sorted(holdings, key=lambda h: (h.grade or "Z", -(h.composite_score or 0)))

    holdings_rows = []
    for holding in sorted_holdings:
        grade = holding.grade or "N/A"
        # Treat both explicit "N/A" grade AND missing crew_analysis_used as
        # "deep analysis didn't run for this holding" — render an explicit
        # pending state instead of a fake grade. This is the truthful
        # rendering required after the DELL "B+ → D" placeholder leak.
        is_pending = grade == "N/A" or holding.crew_analysis_used is None

        ticker = holding.ticker or "N/A"
        name = holding.name or "Unknown"
        asset_class = (holding.asset_class or "unknown").upper()

        # Generate deep analysis link
        deep_analysis_link = _get_deep_analysis_link(ticker, holding.asset_class or "stock")
        ticker_html = f'<a href="{deep_analysis_link}" class="ticker-link" title="View detailed analysis for {ticker}">{ticker}</a>'

        if is_pending:
            holdings_rows.append(f"""
        <tr class="row-pending">
          <td><strong>{ticker_html}</strong><br><small>{name}</small></td>
          <td>{asset_class}</td>
          <td class="grade-na" title="Deep analysis did not run for this holding"><strong>⏳ Analyse en attente</strong></td>
          <td class="muted">—</td>
          <td class="muted">—</td>
          <td><small class="muted">Analyse approfondie non disponible — relancer l'analyse pour obtenir un verdict.</small></td>
        </tr>""")
        else:
            grade_class = f"grade-{grade.lower().replace('+', '-plus')}"
            rec_badge = _get_recommendation_badge(grade, holding.recommended_action)
            composite_score = holding.composite_score if holding.composite_score is not None else 0.0
            rationale = holding.rationale_bullets[0] if holding.rationale_bullets else "Python analysis"
            holdings_rows.append(f"""
        <tr>
          <td><strong>{ticker_html}</strong><br><small>{name}</small></td>
          <td>{asset_class}</td>
          <td class="{grade_class}"><strong>{grade}</strong></td>
          <td>{composite_score:.3f}</td>
          <td>{rec_badge}</td>
          <td><small>{rationale}</small></td>
        </tr>""")

    holdings_html = "".join(holdings_rows)

    return f"""
  <div class="section">
    <h2>Detailed Holdings Analysis</h2>

    <table>
      <thead>
        <tr>
          <th>Ticker / Name</th>
          <th>Class</th>
          <th>Grade</th>
          <th>Score</th>
          <th>Recommendation</th>
          <th>Rationale</th>
        </tr>
      </thead>
      <tbody>
        {holdings_html}
      </tbody>
    </table>

    <p class="small muted">Displaying all positions sorted by grade and score.</p>
  </div>
        """


def generate_recommendations(portfolio_stats: dict[str, Any], discovery_results: dict[str, Any] | None = None) -> str:
    """Generate recommendations section."""
    a_plus_list = ""
    if portfolio_stats.get("a_plus_holdings"):
        a_plus_items = [
            f"<strong>{getattr(h, 'ticker', 'N/A')}</strong> (Grade: {getattr(h, 'grade', 'N/A')}, Score: {getattr(h, 'composite_score', 0):.3f})"
            for h in portfolio_stats["a_plus_holdings"]
        ]
        a_plus_list = f"""
      <p><strong>A+ positions identified ({len(portfolio_stats["a_plus_holdings"])}):</strong></p>
      <ul>
        {"".join(f"<li>{item}</li>" for item in a_plus_items)}
      </ul>"""

    discovery_count = len(discovery_results["opportunities"]) if discovery_results and "opportunities" in discovery_results else 0

    return f"""
  <div class="section">
    <h2>Strategic Recommendations</h2>

    <div class="highlight warning">
      <h3>Priority Actions</h3>
      <ul>
        <li><strong>Positions to sell:</strong> {portfolio_stats["recommendation_counts"]["SELL"]} positions need immediate attention</li>
        <li><strong>A+ opportunities (current portfolio):</strong> {portfolio_stats["a_plus_count"]} excellent positions to keep or reinforce</li>
        <li><strong>New opportunities discovered:</strong> {discovery_count} actionable candidates (grade C or better)</li>
        <li><strong>Rebalancing:</strong> Consider diversification if excessive concentration</li>
      </ul>
      {a_plus_list}
    </div>

    <h3>Suggested Optimizations</h3>
    <ul>
      <li><strong>Risk reduction:</strong> Replace D/F positions with A/B alternatives</li>
      <li><strong>Improve returns:</strong> Increase allocation to A+ positions</li>
      <li><strong>Diversification:</strong> Balance between stocks, ETFs and crypto by risk profile</li>
      <li><strong>Costs:</strong> Favor low-fee ETFs for passive exposure</li>
    </ul>

    <div class="highlight success">
      <h3>Python Analysis Benefits</h3>
      <ul>
        <li><strong>Speed:</strong> Complete analysis in seconds vs minutes with AI</li>
        <li><strong>Cost:</strong> $0 LLM fees vs $0.05-0.10 per analysis with AI</li>
        <li><strong>Consistency:</strong> Identical results on every run</li>
        <li><strong>Transparency:</strong> Auditable scoring algorithms</li>
      </ul>
    </div>
  </div>
        """


def generate_deep_analysis_section(deep_analysis_results: dict[str, Any] | None) -> str:
    """Generate deep analysis section."""
    if not deep_analysis_results:
        return """
  <div class="section">
    <h2>Deep Analysis</h2>
    <div class="highlight warning">
      <p><strong>Deep analysis not available.</strong></p>
      <p>Python deep analysis was not executed for this session.</p>
      <p>To enable deep analysis, use the parameter <code>DEEP_PORTFOLIO_ANALYSIS=true</code>.</p>
    </div>
  </div>
            """

    successful = deep_analysis_results.get("successful_analyses", 0)
    failed = deep_analysis_results.get("failed_analyses", 0)
    total = deep_analysis_results.get("total_holdings", 0)
    success_rate = (successful / total * 100) if total > 0 else 0

    status_text = (
        f"Deep analysis completed successfully on {successful} positions."
        if successful > 0
        else "All your positions have satisfactory grades (>=B). Deep analysis only runs on positions needing attention."
    )
    status_title = "Deep Analysis Completed" if successful > 0 else "No Deep Analysis Needed"

    return f"""
  <div class="section">
    <h2>Python Deep Analysis</h2>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-number">{successful}</div>
        <div>Successful Analyses</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">{failed}</div>
        <div>Failed Analyses</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">{success_rate:.1f}%</div>
        <div>Success Rate</div>
      </div>
    </div>

    <div class="highlight success">
      <h3>{status_title}</h3>
      <p>{status_text}</p>
      <p>Results include detailed scores for fundamental, technical and risk components.</p>
    </div>
  </div>
        """


def generate_performance_metrics(deep_analysis_results: dict[str, Any] | None) -> str:
    """Generate performance metrics section."""
    if not deep_analysis_results or "performance_metrics" not in deep_analysis_results:
        return """
  <div class="section">
    <h2>Performance Metrics</h2>
    <div class="highlight">
      <p><strong>Performance metrics not available.</strong></p>
      <p>Detailed metrics will be available after running deep analysis.</p>
    </div>
  </div>
            """

    metrics = deep_analysis_results["performance_metrics"]

    return f"""
  <div class="section">
    <h2>Performance Metrics</h2>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-number">{metrics.get("total_execution_time_seconds", 0):.1f}s</div>
        <div>Total Time</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">{metrics.get("average_time_per_holding", 0):.2f}s</div>
        <div>Time per Position</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">{metrics.get("llm_calls_made", 0)}</div>
        <div>LLM Calls</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">${metrics.get("estimated_cost_usd", 0):.2f}</div>
        <div>Estimated Cost</div>
      </div>
    </div>

    <div class="highlight success">
      <h3>Exceptional Performance</h3>
      <ul>
        <li><strong>Speed:</strong> {metrics.get("speedup_vs_ai", "10-20x")} faster than AI</li>
        <li><strong>Savings:</strong> {metrics.get("cost_reduction", "100%")} cost reduction</li>
        <li><strong>Efficiency:</strong> {metrics.get("holdings_per_second", 0):.1f} positions/second</li>
        <li><strong>Reliability:</strong> Deterministic and reproducible results</li>
      </ul>
    </div>
  </div>
        """


def _impact_color(impact_pct: float) -> str:
    """Return CSS color for a portfolio impact percentage."""
    abs_impact = abs(impact_pct * 100)
    if abs_impact > 15:
        return "color:#dc3545;font-weight:bold"
    if abs_impact > 5:
        return "color:#fd7e14;font-weight:bold"
    return "color:#28a745"


def _sensitivity_style(label: str) -> str:
    """Return inline CSS for a sensitivity label."""
    upper = label.upper()
    if upper == "HIGH":
        return 'style="color:#dc3545;font-weight:bold"'
    if upper == "MEDIUM":
        return 'style="color:#fd7e14;font-weight:bold"'
    return 'style="color:#28a745"'


def generate_stress_test_section(stress_test_results: list[dict[str, Any]] | None) -> str:
    """Generate stress test analysis section.

    Args:
        stress_test_results: List of PortfolioStressTestResult.model_dump() dicts.

    Returns:
        HTML string for the stress test section, or "" if no data.
    """
    if not stress_test_results:
        return ""

    scenario_cards: list[str] = []
    for result in stress_test_results:
        scenario = result.get("scenario", {})
        name = scenario.get("name", "Scenario inconnu")
        description = scenario.get("description", "")
        impact_pct = result.get("total_portfolio_impact_pct", 0.0)
        projected_pnl = result.get("total_projected_pnl", 0.0)
        holding_impacts = result.get("holding_impacts", [])
        most_affected = result.get("most_affected", [])
        least_affected = result.get("least_affected", [])

        # Build holding impact rows
        impact_rows: list[str] = []
        for hi in holding_impacts:
            sens_label = hi.get("sensitivity_label", "LOW")
            impact_rows.append(
                f"<tr><td>{hi.get('ticker', 'N/A')}</td>"
                f"<td>{hi.get('sector', 'N/A')}</td>"
                f"<td>{hi.get('beta', 0):.2f}</td>"
                f'<td style="{_impact_color(hi.get("projected_change_pct", 0))}">'
                f"{hi.get('projected_change_pct', 0) * 100:+.1f}%</td>"
                f"<td {_sensitivity_style(sens_label)}>{sens_label}</td></tr>"
            )

        impacts_html = "\n        ".join(impact_rows) if impact_rows else "<tr><td colspan='5'>Aucun impact calcule</td></tr>"

        most_html = ", ".join(most_affected) if most_affected else "N/A"
        least_html = ", ".join(least_affected) if least_affected else "N/A"

        scenario_cards.append(f"""
    <div class="highlight" style="margin-bottom:1.5rem">
      <h3>{name}</h3>
      <p class="muted">{description}</p>
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-number" style="{_impact_color(impact_pct)}">{impact_pct * 100:+.1f}%</div>
          <div>Impact total portefeuille</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">${projected_pnl:+,.0f}</div>
          <div>P&amp;L projete</div>
        </div>
      </div>
      <p><strong>Plus affectes :</strong> {most_html} &nbsp;|&nbsp; <strong>Moins affectes :</strong> {least_html}</p>
      <table>
        <thead>
          <tr><th>Ticker</th><th>Secteur</th><th>Beta</th><th>Variation projetee</th><th>Sensibilite</th></tr>
        </thead>
        <tbody>
        {impacts_html}
        </tbody>
      </table>
    </div>""")

    cards_html = "\n".join(scenario_cards)

    return f"""
  <div class="section">
    <h2>Analyse de Stress du Portefeuille</h2>
    <p class="muted">Projection de l'impact de scenarios de marche extremes sur le portefeuille.</p>
    {cards_html}
  </div>
    """


_CONVICTION_GRADES: frozenset[str] = frozenset({"A+", "A"})


def _render_conviction_picks(opportunities: list[dict[str, Any]]) -> str:
    """Render a short A/A+ "Conviction Picks" callout, or empty if none qualify.

    Sits above the full opportunity table to give reviewers a narrow, high-
    conviction shortlist without losing the broader C-or-better list below.
    """
    picks = [o for o in opportunities if o.get("grade") in _CONVICTION_GRADES]
    if not picks:
        return ""

    picks = sorted(picks, key=lambda o: o.get("composite_score", 0), reverse=True)

    rows: list[str] = []
    for p in picks:
        ticker = p.get("ticker", "N/A")
        name = p.get("name", "N/A")
        grade = p.get("grade", "?")
        score = p.get("composite_score", 0)
        rationale = p.get("rationale", "")
        grade_class = f"grade-{grade.lower().replace('+', '-plus')}"
        rows.append(f"""
        <tr>
          <td><strong>{ticker}</strong><br><small>{name}</small></td>
          <td class="{grade_class}"><strong>{grade}</strong></td>
          <td>{score:.3f}</td>
          <td><small>{rationale[:120]}</small></td>
        </tr>""")

    return f"""
    <div class="highlight success">
      <h3>Conviction Picks: {len(picks)} A/A+ Candidates</h3>
      <p>High-conviction shortlist — only candidates graded A or A+. Review first; the broader C-or-better list follows below.</p>
      <table>
        <thead>
          <tr>
            <th>Ticker / Name</th>
            <th>Grade</th>
            <th>Score</th>
            <th>Rationale</th>
          </tr>
        </thead>
        <tbody>
          {"".join(rows)}
        </tbody>
      </table>
    </div>
    """


def generate_discovery_section(discovery_results: dict[str, Any] | None) -> str:
    """Generate A+ discovery opportunities section."""
    if not discovery_results or "opportunities" not in discovery_results:
        return """
  <div class="section">
    <h2>Discovered Opportunities</h2>
    <div class="highlight warning">
      <p><strong>No new opportunities discovered.</strong></p>
      <p>The discovery analysis did not identify actionable candidates in this session.</p>
    </div>
  </div>
            """

    opportunities = discovery_results["opportunities"]
    total_opps = len(opportunities)
    conviction_html = _render_conviction_picks(opportunities)

    # Group by asset class (simple heuristic)
    by_class: dict[str, list[dict[str, Any]]] = {"stock": [], "etf": [], "crypto": []}
    for opp in opportunities:
        ticker = opp.get("ticker", "").lower()
        if "btc" in ticker or "eth" in ticker:
            by_class["crypto"].append(opp)
        elif any(x in ticker for x in ["vt", "vx", "bnd", "spy", "qqq"]):
            by_class["etf"].append(opp)
        else:
            by_class["stock"].append(opp)

    # Generate opportunity rows
    opps_rows = []
    for opp in opportunities:
        ticker = opp.get("ticker", "N/A")
        name = opp.get("name", "N/A")
        grade = opp.get("grade", "?")
        score = opp.get("composite_score", 0)
        recommendation = opp.get("recommendation", "BUY")
        rationale = opp.get("rationale", "Promising opportunity identified by Python analysis")

        grade_class = f"grade-{grade.lower().replace('+', '-plus')}"
        rec_badge = '<span class="badge badge-buy">BUY</span>' if "BUY" in recommendation else '<span class="badge badge-hold">WATCH</span>'

        opps_rows.append(f"""
        <tr>
          <td><strong>{ticker}</strong><br><small>{name}</small></td>
          <td class="{grade_class}"><strong>{grade}</strong></td>
          <td>{score:.3f}</td>
          <td>{rec_badge}</td>
          <td><small>{rationale[:100]}...</small></td>
        </tr>""")

    opps_html = "".join(opps_rows)

    return f"""
  <div class="section">
    <h2>Discovered Opportunities</h2>
    {conviction_html}
    <div class="highlight success">
      <h3>{total_opps} New Opportunities Identified</h3>
      <p>Python discovery analysis identified {total_opps} actionable opportunities (graded C or better) that could improve your portfolio.</p>
      <ul>
        <li><strong>Stocks:</strong> {len(by_class["stock"])} opportunities</li>
        <li><strong>ETFs:</strong> {len(by_class["etf"])} opportunities</li>
        <li><strong>Crypto:</strong> {len(by_class["crypto"])} opportunities</li>
      </ul>
    </div>

    <h3>Discovered Opportunities List</h3>
    <table>
      <thead>
        <tr>
          <th>Ticker / Name</th>
          <th>Grade</th>
          <th>Score</th>
          <th>Recommendation</th>
          <th>Rationale</th>
        </tr>
      </thead>
      <tbody>
        {opps_html}
      </tbody>
    </table>

    <div class="highlight warning">
      <h3>How to Use These Opportunities</h3>
      <ul>
        <li><strong>Replacement:</strong> Consider replacing D/F positions with these higher-grade alternatives</li>
        <li><strong>Diversification:</strong> Add these assets to balance your portfolio</li>
        <li><strong>DCA:</strong> Establish a progressive buying plan (Dollar Cost Averaging)</li>
        <li><strong>Due Diligence:</strong> Do your own research before investing</li>
      </ul>
    </div>
  </div>
        """


# ===== Phase 16 Report Enrichment Section Generators =====


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
    """Format a macro indicator value for display."""
    if value is None:
        return "N/A"
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
            estimate = evt.get("estimate")
            prev = evt.get("prev")
            estimate_str = f"{estimate:.2f}" if estimate is not None else "-"
            prev_str = f"{prev:.2f}" if prev is not None else "-"
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
            eps_est = ear.get("eps_estimate")
            eps_str = f"{eps_est:.2f}" if eps_est is not None else "-"
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
