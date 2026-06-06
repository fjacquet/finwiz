"""Discovered-opportunities section with A/A+ conviction picks."""

from __future__ import annotations

from html import escape
from typing import Any

from finwiz.reporting.sections.common import grade_css_class

_CONVICTION_GRADES: frozenset[str] = frozenset({"A+", "A"})


def _format_fit(opp: dict[str, Any]) -> str:
    """Format a 0..1 portfolio_fit_score as a percentage, or '—' when absent."""
    fit = opp.get("portfolio_fit_score")
    if fit is None:
        return "—"
    try:
        return f"{float(fit):.0%}"
    except (TypeError, ValueError):
        return "—"


def _format_gap(opp: dict[str, Any]) -> str:
    """Format the gap_filled sector label (HTML-escaped), or '—' when absent."""
    gap = opp.get("gap_filled")
    if gap is None or not str(gap).strip():
        return "—"
    return escape(str(gap))


def _shortlist_opps(shortlist: Any) -> list[dict[str, Any]]:
    """Normalize the opportunity shortlist input to a list of opp dicts.

    Accepts either the raw list or the on-disk ``{"shortlist": [...], "size": N}``
    wrapper. Returns ``[]`` for anything unparseable.
    """
    if isinstance(shortlist, dict):
        shortlist = shortlist.get("shortlist")
    if not isinstance(shortlist, list):
        return []
    return [o for o in shortlist if isinstance(o, dict)]


def generate_gap_fill_shortlist_section(shortlist: Any) -> str:
    """Render a highlighted "Top Gap-Fill Opportunities" block.

    Surfaces the portfolio-aware cascade's marginal-fit ranking (which gaps each
    candidate fills) that is otherwise dark in the consolidated report.

    Returns "" when there is nothing to show.
    """
    opps = _shortlist_opps(shortlist)
    if not opps:
        return ""

    opps = sorted(opps, key=lambda o: o.get("composite_score", 0) or 0, reverse=True)

    rows: list[str] = []
    for rank, opp in enumerate(opps, start=1):
        ticker = escape(str(opp.get("ticker", "N/A")))
        grade = str(opp.get("grade", "?"))
        grade_safe = escape(grade)
        grade_class = grade_css_class(grade)
        score = opp.get("composite_score", 0) or 0
        try:
            score_str = f"{float(score):.3f}"
        except (TypeError, ValueError):
            score_str = "—"
        rows.append(f"""
        <tr>
          <td>{rank}</td>
          <td><strong>{ticker}</strong></td>
          <td class="{grade_class}"><strong>{grade_safe}</strong></td>
          <td>{score_str}</td>
          <td>{_format_fit(opp)}</td>
          <td>{_format_gap(opp)}</td>
        </tr>""")

    return f"""
  <div class="section">
    <div class="highlight success">
      <h3>🎯 Top Opportunités Comblant des Lacunes</h3>
      <p>Classement par adéquation marginale au portefeuille — chaque candidat comble une lacune sectorielle identifiée.</p>
      <table>
        <thead>
          <tr>
            <th>Rang</th>
            <th>Ticker</th>
            <th>Grade</th>
            <th>Score</th>
            <th>Adéquation</th>
            <th>Comble la lacune</th>
          </tr>
        </thead>
        <tbody>
          {"".join(rows)}
        </tbody>
      </table>
    </div>
  </div>
    """


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
        grade = str(p.get("grade", "?"))
        grade_safe = escape(grade)
        grade_class = grade_css_class(grade)
        score = p.get("composite_score", 0)
        rationale = escape(str(p.get("rationale", "")))[:120]
        rows.append(f"""
        <tr>
          <td><strong>{ticker}</strong><br><small>{name}</small></td>
          <td class="{grade_class}"><strong>{grade_safe}</strong></td>
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

    # Group by asset class: prefer the explicit payload field (the portfolio-aware
    # cascade sets it), fall back to a ticker heuristic only when absent.
    by_class: dict[str, list[dict[str, Any]]] = {"stock": [], "etf": [], "crypto": []}
    for opp in opportunities:
        ac = str(opp.get("asset_class") or "").lower()
        if ac in by_class:
            by_class[ac].append(opp)
            continue
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
        grade = str(opp.get("grade", "?"))
        grade_safe = escape(grade)
        grade_class = grade_css_class(grade)
        score = opp.get("composite_score", 0)
        recommendation = opp.get("recommendation", "BUY")
        rationale = escape(str(opp.get("rationale", "Promising opportunity identified by Python analysis")))[:100]

        rec_badge = '<span class="badge badge-buy">BUY</span>' if "BUY" in recommendation else '<span class="badge badge-hold">WATCH</span>'

        opps_rows.append(f"""
        <tr>
          <td><strong>{ticker}</strong><br><small>{name}</small></td>
          <td class="{grade_class}"><strong>{grade_safe}</strong></td>
          <td>{score:.3f}</td>
          <td>{_format_fit(opp)}</td>
          <td>{_format_gap(opp)}</td>
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
          <th>Portfolio Fit</th>
          <th>Fills Gap</th>
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
