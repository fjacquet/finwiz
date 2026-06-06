"""Discovered-opportunities section with A/A+ conviction picks."""

from __future__ import annotations

from html import escape
from typing import Any

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
        ticker = escape(str(p.get("ticker", "N/A")))
        name = escape(str(p.get("name", "N/A")))
        grade = p.get("grade", "?")
        score = p.get("composite_score", 0)
        rationale = escape(str(p.get("rationale", "")))[:120]
        grade_class = f"grade-{grade.lower().replace('+', '-plus')}"
        rows.append(f"""
        <tr>
          <td><strong>{ticker}</strong><br><small>{name}</small></td>
          <td class="{grade_class}"><strong>{grade}</strong></td>
          <td>{score:.3f}</td>
          <td><small>{rationale}</small></td>
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
        ticker = escape(str(opp.get("ticker", "N/A")))
        name = escape(str(opp.get("name", "N/A")))
        grade = opp.get("grade", "?")
        score = opp.get("composite_score", 0)
        recommendation = opp.get("recommendation", "BUY")
        rationale = escape(str(opp.get("rationale", "Promising opportunity identified by Python analysis")))[:100]

        grade_class = f"grade-{grade.lower().replace('+', '-plus')}"
        rec_badge = '<span class="badge badge-buy">BUY</span>' if "BUY" in recommendation else '<span class="badge badge-hold">WATCH</span>'

        opps_rows.append(f"""
        <tr>
          <td><strong>{ticker}</strong><br><small>{name}</small></td>
          <td class="{grade_class}"><strong>{grade}</strong></td>
          <td>{score:.3f}</td>
          <td>{rec_badge}</td>
          <td><small>{rationale}...</small></td>
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
