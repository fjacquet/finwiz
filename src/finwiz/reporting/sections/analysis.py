"""Deep analysis, performance metrics, and stress-test sections."""

from __future__ import annotations

from typing import Any


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
