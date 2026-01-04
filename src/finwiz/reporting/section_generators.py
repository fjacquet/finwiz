"""
Report section generators for Python report generation.

This module contains section generators extracted from PythonReportGenerator
for the family financial plan HTML report.
"""

from typing import Any

from finwiz.schemas.portfolio_review import HoldingDecision, PortfolioReview


def generate_executive_summary(portfolio_stats: dict[str, Any]) -> str:
    """Generate executive summary section."""
    grade_class = f"grade-{portfolio_stats['portfolio_grade'].lower().replace('+', '-plus')}"

    return f"""
  <div class="section">
    <h2>Executive Summary</h2>

    <div class="highlight success">
      <h3>Portfolio Grade: <span class="{grade_class}">{portfolio_stats["portfolio_grade"]}</span></h3>
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
      <li><strong>Ultra-fast analysis:</strong> Python processing in seconds (vs 5-10 minutes with AI)</li>
      <li><strong>Zero cost:</strong> 0 LLM calls, 100% savings on analysis fees</li>
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
        grade_class = f"grade-{grade.lower().replace('+', '-plus')}" if grade != "N/A" else "grade-f"
        rec_badge = _get_recommendation_badge(grade, holding.recommended_action)

        ticker = holding.ticker or "N/A"
        name = holding.name or "Unknown"
        asset_class = (holding.asset_class or "unknown").upper()
        composite_score = holding.composite_score if holding.composite_score is not None else 0.0
        rationale = holding.rationale_bullets[0] if holding.rationale_bullets else "Python analysis"

        # Generate deep analysis link
        deep_analysis_link = _get_deep_analysis_link(ticker, holding.asset_class or "stock")
        ticker_html = f'<a href="{deep_analysis_link}" class="ticker-link" title="View detailed analysis for {ticker}">{ticker}</a>'

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
        <li><strong>New A+ opportunities discovered:</strong> {discovery_count} promising assets identified</li>
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


def generate_discovery_section(discovery_results: dict[str, Any] | None) -> str:
    """Generate A+ discovery opportunities section."""
    if not discovery_results or "opportunities" not in discovery_results:
        return """
  <div class="section">
    <h2>A+ Opportunity Discovery</h2>
    <div class="highlight warning">
      <p><strong>No new A+ opportunities discovered.</strong></p>
      <p>The discovery analysis did not identify new promising assets in this session.</p>
    </div>
  </div>
            """

    opportunities = discovery_results["opportunities"]
    total_opps = len(opportunities)

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
        grade = opp.get("grade", "A+")
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
    <h2>A+ Opportunity Discovery</h2>

    <div class="highlight success">
      <h3>{total_opps} New Opportunities Identified</h3>
      <p>Python discovery analysis identified {total_opps} promising A/A+ assets that could improve your portfolio.</p>
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
        <li><strong>Replacement:</strong> Consider replacing D/F positions with these A/A+ assets</li>
        <li><strong>Diversification:</strong> Add these assets to balance your portfolio</li>
        <li><strong>DCA:</strong> Establish a progressive buying plan (Dollar Cost Averaging)</li>
        <li><strong>Due Diligence:</strong> Do your own research before investing</li>
      </ul>
    </div>
  </div>
        """
