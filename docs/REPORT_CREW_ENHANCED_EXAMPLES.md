# Report Crew Enhanced Data Usage Examples

## Overview

This document provides practical examples of how the Report crew uses enhanced data extraction to generate comprehensive investment reports with backtesting metrics, market context, discovery methodology, and performance aggregation.

## Example 1: Backtesting Metrics in Reports

### Scenario

Generate a report section showing backtesting performance metrics for A+ opportunities.

### Implementation

```python
from finwiz.integration.data_accessor import CrewDataAccessor
from datetime import datetime

def generate_backtesting_section(accessor: CrewDataAccessor) -> str:
    """Generate backtesting performance section for report."""
    
    # Get backtesting summary
    summary = accessor.get_backtesting_metrics()
    
    if summary is None:
        return """
        <section id="backtesting">
            <h2>📊 Backtesting Performance Analysis</h2>
            <p><em>Backtesting data not available for this analysis.</em></p>
        </section>
        """
    
    # Build HTML section
    html = f"""
    <section id="backtesting">
        <h2>📊 Backtesting Performance Analysis</h2>
        <p><strong>Candidates Tested:</strong> {summary.total_candidates_tested}</p>
        
        <h3>Average Performance Metrics</h3>
        <table class="metrics-table">
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>Annualized Return</td>
                <td class="positive">{summary.average_metrics.annualized_return:.2%}</td>
            </tr>
            <tr>
                <td>Sharpe Ratio</td>
                <td>{summary.average_metrics.sharpe_ratio:.2f}</td>
            </tr>
            <tr>
                <td>Maximum Drawdown</td>
                <td class="negative">{summary.average_metrics.max_drawdown:.2%}</td>
            </tr>
            <tr>
                <td>Win Rate</td>
                <td>{summary.average_metrics.win_rate:.2%}</td>
            </tr>
        </table>
        
        <h3>Performance Comparison</h3>
        <table class="comparison-table">
            <tr>
                <th>Category</th>
                <th>Symbol</th>
                <th>Return</th>
                <th>Sharpe</th>
            </tr>
            <tr class="best-performer">
                <td>🏆 Best Performer</td>
                <td><strong>{summary.best_performer}</strong></td>
                <td colspan="2">Highest risk-adjusted returns</td>
            </tr>
            <tr class="worst-performer">
                <td>⚠️ Worst Performer</td>
                <td>{summary.worst_performer}</td>
                <td colspan="2">Lowest risk-adjusted returns</td>
            </tr>
        </table>
        
        <h3>Regime Performance Analysis</h3>
        <table class="regime-table">
            <tr>
                <th>Market Regime</th>
                <th>Return</th>
                <th>Sharpe</th>
                <th>Max Drawdown</th>
                <th>Consistency</th>
            </tr>
    """
    
    # Add regime performance rows
    for regime_type, regime_perf in summary.regime_performance.items():
        regime_emoji = {
            "bull": "📈",
            "bear": "📉",
            "sideways": "↔️",
            "volatile": "🌊"
        }.get(regime_type, "")
        
        html += f"""
            <tr>
                <td>{regime_emoji} {regime_type.capitalize()}</td>
                <td>{regime_perf.annualized_return:.2%}</td>
                <td>{regime_perf.sharpe_ratio:.2f}</td>
                <td>{regime_perf.max_drawdown:.2%}</td>
                <td>{regime_perf.consistency_score:.2f}</td>
            </tr>
        """
    
    html += """
        </table>
        
        <div class="insight-box">
            <h4>💡 Key Insights</h4>
            <ul>
                <li>All A+ candidates have been rigorously backtested over multiple market cycles</li>
                <li>Performance metrics demonstrate consistent risk-adjusted returns</li>
                <li>Regime analysis shows resilience across different market conditions</li>
            </ul>
        </div>
    </section>
    """
    
    return html

# Usage in report generation
accessor = CrewDataAccessor()
backtesting_html = generate_backtesting_section(accessor)
```

### Output Example

The generated HTML creates a professional section with:
- Summary statistics table
- Best/worst performer comparison
- Regime-specific performance breakdown
- Key insights highlighting backtesting rigor

## Example 2: Market Context in Risk Assessment

### Scenario

Incorporate current market context into risk assessment section.

### Implementation

```python
def generate_risk_assessment_with_context(accessor: CrewDataAccessor) -> str:
    """Generate risk assessment section with market context."""
    
    # Get market context
    context = accessor.get_market_context()
    
    if context is None:
        return """
        <section id="risk-assessment">
            <h2>⚠️ Risk Assessment</h2>
            <p><em>Using conservative market assumptions.</em></p>
        </section>
        """
    
    # Determine risk level based on context
    risk_level = "elevated" if context.market_regime.market_stress_level == "high" else "moderate"
    risk_color = "red" if risk_level == "elevated" else "orange"
    
    html = f"""
    <section id="risk-assessment">
        <h2>⚠️ Risk Assessment & Market Context</h2>
        
        <h3>Current Market Environment</h3>
        <div class="market-context-box">
            <table class="context-table">
                <tr>
                    <th>Indicator</th>
                    <th>Current Value</th>
                    <th>Assessment</th>
                </tr>
                <tr>
                    <td>Market Regime</td>
                    <td><strong>{context.market_regime.regime_type.upper()}</strong></td>
                    <td>{_get_regime_description(context.market_regime.regime_type)}</td>
                </tr>
                <tr>
                    <td>VIX Level</td>
                    <td>{context.vix_indicators.current_vix:.2f}</td>
                    <td>{context.vix_indicators.volatility_regime.capitalize()} volatility ({context.vix_indicators.vix_percentile:.0f}th percentile)</td>
                </tr>
                <tr>
                    <td>Inflation Rate</td>
                    <td>{context.macro_indicators.inflation_rate:.2%}</td>
                    <td>{_get_inflation_assessment(context.macro_indicators.inflation_rate)}</td>
                </tr>
                <tr>
                    <td>Interest Rate Trend</td>
                    <td>{context.macro_indicators.interest_rate_trend.capitalize()}</td>
                    <td>{_get_rate_trend_impact(context.macro_indicators.interest_rate_trend)}</td>
                </tr>
                <tr>
                    <td>Market Stress Level</td>
                    <td class="{risk_color}"><strong>{context.market_regime.market_stress_level.upper()}</strong></td>
                    <td>Overall risk environment: {context.risk_environment}</td>
                </tr>
            </table>
        </div>
        
        <h3>Allocation Implications</h3>
        <div class="implications-box">
            <ul>
    """
    
    for implication in context.allocation_implications:
        html += f"                <li>{implication}</li>\n"
    
    html += """
            </ul>
        </div>
        
        <h3>Risk Mitigation Strategies</h3>
        <div class="strategies-box">
    """
    
    # Add context-specific strategies
    if context.market_regime.market_stress_level == "high":
        html += """
            <p><strong>🛡️ Defensive Positioning Recommended:</strong></p>
            <ul>
                <li>Increase allocation to defensive sectors and quality assets</li>
                <li>Consider reducing position sizes during implementation</li>
                <li>Implement gradual entry strategies to average costs</li>
                <li>Maintain higher cash reserves for opportunistic buying</li>
            </ul>
        """
    elif context.vix_indicators.volatility_regime == "elevated":
        html += """
            <p><strong>⚡ Elevated Volatility Management:</strong></p>
            <ul>
                <li>Use limit orders to avoid unfavorable execution prices</li>
                <li>Consider options strategies for downside protection</li>
                <li>Monitor positions more frequently during volatile periods</li>
                <li>Rebalance opportunistically during market swings</li>
            </ul>
        """
    else:
        html += """
            <p><strong>✅ Normal Market Conditions:</strong></p>
            <ul>
                <li>Standard implementation strategies appropriate</li>
                <li>Focus on long-term fundamentals and quality</li>
                <li>Maintain disciplined rebalancing schedule</li>
                <li>Monitor for regime changes and adjust accordingly</li>
            </ul>
        """
    
    html += """
        </div>
    </section>
    """
    
    return html

def _get_regime_description(regime_type: str) -> str:
    """Get description for market regime."""
    descriptions = {
        "bull": "Strong upward trend with positive momentum",
        "bear": "Downward trend with negative sentiment",
        "sideways": "Range-bound market with low directional bias",
        "volatile": "High uncertainty with rapid price swings"
    }
    return descriptions.get(regime_type, "Market conditions unclear")

def _get_inflation_assessment(inflation_rate: float) -> str:
    """Get assessment of inflation level."""
    if inflation_rate > 0.04:
        return "Elevated - May pressure valuations"
    elif inflation_rate > 0.02:
        return "Moderate - Within target range"
    else:
        return "Low - Supportive for growth assets"

def _get_rate_trend_impact(trend: str) -> str:
    """Get impact description for interest rate trend."""
    impacts = {
        "rising": "Headwind for growth stocks, favor value",
        "falling": "Tailwind for growth stocks and risk assets",
        "stable": "Neutral impact on asset allocation"
    }
    return impacts.get(trend, "Impact unclear")

# Usage
accessor = CrewDataAccessor()
risk_html = generate_risk_assessment_with_context(accessor)
```

### Output Example

Creates a comprehensive risk assessment that:
- Shows current market indicators with context
- Provides allocation implications based on regime
- Recommends specific risk mitigation strategies
- Adapts recommendations to market conditions


## Example 3: Discovery Methodology in Reports

### Scenario

Document the discovery methodology used to identify A+ opportunities.

### Implementation

```python
def generate_methodology_section(accessor: CrewDataAccessor) -> str:
    """Generate discovery methodology section for report."""
    
    # Get methodology summary
    methodology = accessor.get_discovery_methodology()
    
    if methodology is None:
        return """
        <section id="methodology">
            <h2>🔍 Discovery Methodology</h2>
            <p><em>Methodology details not available.</em></p>
        </section>
        """
    
    criteria = methodology.screening_criteria
    stats = methodology.validation_statistics
    
    html = f"""
    <section id="methodology">
        <h2>🔍 Discovery Methodology</h2>
        
        <h3>Screening Criteria</h3>
        <p>A+ opportunities are identified using rigorous multi-factor screening:</p>
        
        <h4>📊 ETF Criteria</h4>
        <table class="criteria-table">
            <tr>
                <th>Criterion</th>
                <th>Threshold</th>
                <th>Rationale</th>
            </tr>
            <tr>
                <td>Expense Ratio</td>
                <td>≤ {criteria.etf_max_expense_ratio:.2%}</td>
                <td>Minimize cost drag on returns</td>
            </tr>
            <tr>
                <td>Assets Under Management</td>
                <td>≥ ${criteria.etf_min_aum / 1e9:.1f}B</td>
                <td>Ensure liquidity and stability</td>
            </tr>
            <tr>
                <td>Tracking Error</td>
                <td>≤ {criteria.etf_max_tracking_error:.3%}</td>
                <td>Accurate benchmark replication</td>
            </tr>
            <tr>
                <td>Operating History</td>
                <td>≥ {criteria.etf_min_history_years} years</td>
                <td>Proven track record</td>
            </tr>
        </table>
        
        <h4>📈 Stock Criteria</h4>
        <table class="criteria-table">
            <tr>
                <th>Criterion</th>
                <th>Threshold</th>
                <th>Rationale</th>
            </tr>
            <tr>
                <td>Return on Equity (ROE)</td>
                <td>≥ {criteria.stock_min_roe:.0%}</td>
                <td>High profitability and efficiency</td>
            </tr>
            <tr>
                <td>Revenue Growth</td>
                <td>≥ {criteria.stock_min_revenue_growth:.0%}</td>
                <td>Strong business momentum</td>
            </tr>
            <tr>
                <td>Debt-to-Equity</td>
                <td>≤ {criteria.stock_max_debt_to_equity:.1f}</td>
                <td>Conservative leverage</td>
            </tr>
            <tr>
                <td>Market Capitalization</td>
                <td>≥ ${criteria.stock_min_market_cap / 1e9:.1f}B</td>
                <td>Established companies</td>
            </tr>
        </table>
        
        <h4>₿ Crypto Criteria</h4>
        <table class="criteria-table">
            <tr>
                <th>Criterion</th>
                <th>Threshold</th>
                <th>Rationale</th>
            </tr>
            <tr>
                <td>Market Capitalization</td>
                <td>≥ ${criteria.crypto_min_market_cap / 1e9:.1f}B</td>
                <td>Established projects only</td>
            </tr>
            <tr>
                <td>Daily Trading Volume</td>
                <td>≥ ${criteria.crypto_min_daily_volume / 1e6:.0f}M</td>
                <td>Sufficient liquidity</td>
            </tr>
            <tr>
                <td>Operating History</td>
                <td>≥ {criteria.crypto_min_age_months} months</td>
                <td>Proven longevity</td>
            </tr>
        </table>
    """
    
    # Add regime adjustment note if applicable
    if criteria.regime_adjusted:
        html += f"""
        <div class="adjustment-note">
            <h4>⚙️ Regime Adjustment Applied</h4>
            <p>{criteria.adjustment_rationale}</p>
        </div>
        """
    
    # Add validation statistics
    html += f"""
        <h3>Validation Statistics</h3>
        <div class="stats-box">
            <table class="stats-table">
                <tr>
                    <th>Stage</th>
                    <th>Count</th>
                    <th>Percentage</th>
                </tr>
                <tr>
                    <td>Total Assets Screened</td>
                    <td>{stats.total_screened:,}</td>
                    <td>100%</td>
                </tr>
                <tr>
                    <td>Candidates Found</td>
                    <td>{stats.candidates_found}</td>
                    <td>{(stats.candidates_found / stats.total_screened * 100):.2f}%</td>
                </tr>
                <tr class="success">
                    <td>✅ Passed Validation</td>
                    <td><strong>{stats.passed_validation}</strong></td>
                    <td><strong>{stats.validation_rate:.1%}</strong></td>
                </tr>
                <tr class="failure">
                    <td>❌ Failed Validation</td>
                    <td>{stats.failed_validation}</td>
                    <td>{(stats.failed_validation / stats.candidates_found * 100):.1f}%</td>
                </tr>
            </table>
            
            <p><strong>Screening Efficiency:</strong> {stats.screening_efficiency:.2f}% of screened assets met A+ criteria</p>
        </div>
        
        <h3>Score Breakdown by Candidate</h3>
        <table class="scores-table">
            <tr>
                <th>Symbol</th>
                <th>Fundamental</th>
                <th>Technical</th>
                <th>Quality</th>
                <th>Risk</th>
                <th>Composite</th>
                <th>Grade</th>
            </tr>
    """
    
    # Add score breakdowns
    for symbol, breakdown in methodology.score_breakdowns.items():
        grade_class = f"grade-{breakdown.grade.lower().replace('+', '-plus')}"
        html += f"""
            <tr>
                <td><strong>{symbol}</strong></td>
                <td>{breakdown.fundamental_score:.2f}</td>
                <td>{breakdown.technical_score:.2f}</td>
                <td>{breakdown.quality_score:.2f}</td>
                <td>{breakdown.risk_score:.2f}</td>
                <td><strong>{breakdown.composite_score:.2f}</strong></td>
                <td class="{grade_class}"><strong>{breakdown.grade}</strong></td>
            </tr>
        """
    
    html += """
        </table>
        
        <h3>Methodology Notes</h3>
        <div class="notes-box">
            <ul>
    """
    
    for note in methodology.methodology_notes:
        html += f"                <li>{note}</li>\n"
    
    html += """
            </ul>
        </div>
        
        <h3>Data Sources</h3>
        <div class="sources-box">
            <ul>
    """
    
    for source in methodology.data_sources:
        html += f"                <li>{source}</li>\n"
    
    html += """
            </ul>
        </div>
    </section>
    """
    
    return html

# Usage
accessor = CrewDataAccessor()
methodology_html = generate_methodology_section(accessor)
```

### Output Example

Generates a detailed methodology section with:
- Complete screening criteria tables for all asset types
- Validation statistics showing screening funnel
- Score breakdowns for each A+ candidate
- Methodology notes and data sources

## Example 4: Performance Aggregation

### Scenario

Create a comprehensive performance overview aggregating metrics across asset types and regimes.

### Implementation

```python
def generate_performance_overview(accessor: CrewDataAccessor) -> str:
    """Generate performance aggregation overview."""
    
    # Get performance report
    report = accessor.get_performance_report()
    
    if report is None:
        return """
        <section id="performance-overview">
            <h2>📊 Performance Overview</h2>
            <p><em>Performance data not available.</em></p>
        </section>
        """
    
    html = f"""
    <section id="performance-overview">
        <h2>📊 Performance Overview</h2>
        <p><em>Report generated: {report.report_timestamp.strftime('%Y-%m-%d %H:%M:%S')}</em></p>
        
        <h3>Performance by Asset Type</h3>
        <table class="performance-table">
            <tr>
                <th>Asset Type</th>
                <th>Count</th>
                <th>Avg Return</th>
                <th>Avg Sharpe</th>
                <th>Avg Max DD</th>
                <th>Avg Win Rate</th>
                <th>Best Performer</th>
            </tr>
    """
    
    # Add asset type rows
    for asset_type, metrics in report.by_asset_type.items():
        if metrics.count == 0:
            continue
            
        asset_emoji = {
            "etf": "📊",
            "stock": "📈",
            "crypto": "₿",
            "all": "🌐"
        }.get(asset_type, "")
        
        html += f"""
            <tr>
                <td>{asset_emoji} {asset_type.upper()}</td>
                <td>{metrics.count}</td>
                <td class="positive">{metrics.average_return:.2%}</td>
                <td>{metrics.average_sharpe:.2f}</td>
                <td class="negative">{metrics.average_max_drawdown:.2%}</td>
                <td>{metrics.average_win_rate:.2%}</td>
                <td><strong>{metrics.best_performer or 'N/A'}</strong></td>
            </tr>
        """
    
    html += """
        </table>
        
        <h3>Performance by Market Regime</h3>
        <table class="regime-performance-table">
            <tr>
                <th>Market Regime</th>
                <th>Avg Return</th>
                <th>Avg Sharpe</th>
                <th>Avg Max DD</th>
                <th>Avg Win Rate</th>
            </tr>
    """
    
    # Add regime rows
    for regime, metrics in report.by_regime.items():
        regime_emoji = {
            "bull": "📈",
            "bear": "📉",
            "sideways": "↔️",
            "volatile": "🌊"
        }.get(regime, "")
        
        html += f"""
            <tr>
                <td>{regime_emoji} {regime.capitalize()}</td>
                <td>{metrics.average_return:.2%}</td>
                <td>{metrics.average_sharpe:.2f}</td>
                <td>{metrics.average_max_drawdown:.2%}</td>
                <td>{metrics.average_win_rate:.2%}</td>
            </tr>
        """
    
    html += """
        </table>
        
        <h3>Portfolio Impact Assessment</h3>
        <div class="impact-box">
            <table class="impact-table">
                <tr>
                    <th>Impact Category</th>
                    <th>Assessment</th>
                </tr>
                <tr>
                    <td>Expected Grade Improvement</td>
                    <td class="positive"><strong>+{report.portfolio_impact.expected_grade_improvement:.1f}%</strong></td>
                </tr>
                <tr>
                    <td>Expected Return Improvement</td>
                    <td class="positive"><strong>+{report.portfolio_impact.expected_return_improvement:.2%}</strong></td>
                </tr>
                <tr>
                    <td>Risk Impact</td>
                    <td class="{_get_impact_class(report.portfolio_impact.risk_impact)}">
                        {_get_impact_icon(report.portfolio_impact.risk_impact)} {report.portfolio_impact.risk_impact.capitalize()}
                    </td>
                </tr>
                <tr>
                    <td>Diversification Impact</td>
                    <td class="{_get_impact_class(report.portfolio_impact.diversification_impact)}">
                        {_get_impact_icon(report.portfolio_impact.diversification_impact)} {report.portfolio_impact.diversification_impact.capitalize()}
                    </td>
                </tr>
                <tr>
                    <td>Implementation Complexity</td>
                    <td class="{_get_complexity_class(report.portfolio_impact.implementation_complexity)}">
                        {report.portfolio_impact.implementation_complexity.capitalize()}
                    </td>
                </tr>
            </table>
        </div>
        
        <h3>Top 5 Opportunities</h3>
        <div class="top-opportunities">
            <ol>
    """
    
    for i, symbol in enumerate(report.top_opportunities, 1):
        html += f"                <li><strong>{symbol}</strong> - Highest composite score in category</li>\n"
    
    html += """
            </ol>
        </div>
        
        <div class="summary-box">
            <h4>💡 Performance Summary</h4>
            <p>The A+ opportunities demonstrate strong risk-adjusted returns across multiple asset types and market regimes. 
            Implementation of these recommendations is expected to improve portfolio grade and returns while maintaining 
            appropriate risk levels.</p>
        </div>
    </section>
    """
    
    return html

def _get_impact_class(impact: str) -> str:
    """Get CSS class for impact indicator."""
    if impact in ["improved", "reduced"]:
        return "positive"
    elif impact == "neutral":
        return "neutral"
    else:
        return "negative"

def _get_impact_icon(impact: str) -> str:
    """Get icon for impact indicator."""
    if impact in ["improved", "reduced"]:
        return "✅"
    elif impact == "neutral":
        return "➖"
    else:
        return "⚠️"

def _get_complexity_class(complexity: str) -> str:
    """Get CSS class for complexity indicator."""
    if complexity == "low":
        return "positive"
    elif complexity == "medium":
        return "neutral"
    else:
        return "warning"

# Usage
accessor = CrewDataAccessor()
performance_html = generate_performance_overview(accessor)
```

### Output Example

Creates a comprehensive performance overview with:
- Asset type performance comparison table
- Market regime performance breakdown
- Portfolio impact assessment
- Top 5 opportunities ranked by composite score

## Example 5: Complete Report Integration

### Scenario

Generate a complete investment report integrating all enhanced data sources.

### Implementation

```python
from datetime import datetime

def generate_complete_report(accessor: CrewDataAccessor) -> str:
    """Generate complete investment report with all enhanced data."""
    
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # Generate all sections
    backtesting_section = generate_backtesting_section(accessor)
    risk_section = generate_risk_assessment_with_context(accessor)
    methodology_section = generate_methodology_section(accessor)
    performance_section = generate_performance_overview(accessor)
    
    # Build complete HTML report
    html = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapport d'Investissement FinWiz - {current_date}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-bottom: 2px solid #95a5a6;
            padding-bottom: 5px;
        }}
        
        h3 {{
            color: #7f8c8d;
            margin-top: 20px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        th {{
            background-color: #3498db;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: bold;
        }}
        
        td {{
            padding: 10px;
            border-bottom: 1px solid #ecf0f1;
        }}
        
        tr:hover {{
            background-color: #f8f9fa;
        }}
        
        .positive {{ color: #27ae60; font-weight: bold; }}
        .negative {{ color: #e74c3c; font-weight: bold; }}
        .neutral {{ color: #95a5a6; }}
        .warning {{ color: #f39c12; }}
        
        .grade-a-plus {{ color: #27ae60; font-weight: bold; }}
        .grade-a {{ color: #2ecc71; }}
        .grade-b {{ color: #f39c12; }}
        .grade-c {{ color: #e67e22; }}
        .grade-d {{ color: #e74c3c; }}
        .grade-f {{ color: #c0392b; font-weight: bold; }}
        
        .insight-box, .implications-box, .strategies-box, .notes-box, .sources-box, .summary-box {{
            background-color: #ecf0f1;
            padding: 15px;
            border-left: 4px solid #3498db;
            margin: 20px 0;
        }}
        
        .market-context-box, .stats-box, .impact-box {{
            background-color: white;
            padding: 15px;
            border: 1px solid #bdc3c7;
            border-radius: 5px;
            margin: 20px 0;
        }}
        
        .best-performer {{
            background-color: #d5f4e6;
        }}
        
        .worst-performer {{
            background-color: #fadbd8;
        }}
        
        .success {{
            background-color: #d5f4e6;
        }}
        
        .failure {{
            background-color: #fadbd8;
        }}
        
        @media print {{
            body {{
                background-color: white;
            }}
            
            table {{
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <h1>📊 Rapport d'Investissement FinWiz</h1>
    <p><strong>Date de génération:</strong> {current_date}</p>
    <p><strong>Type d'analyse:</strong> Analyse complète avec données enrichies</p>
    
    <section id="table-of-contents">
        <h2>📑 Table des Matières</h2>
        <ul>
            <li><a href="#backtesting">Analyse de Performance Backtesting</a></li>
            <li><a href="#risk-assessment">Évaluation des Risques & Contexte de Marché</a></li>
            <li><a href="#methodology">Méthodologie de Découverte</a></li>
            <li><a href="#performance-overview">Vue d'Ensemble des Performances</a></li>
        </ul>
    </section>
    
    {backtesting_section}
    {risk_section}
    {methodology_section}
    {performance_section}
    
    <section id="disclaimer">
        <h2>⚠️ Avertissement</h2>
        <p><em>Ce rapport est généré à des fins d'information uniquement et ne constitue pas un conseil en investissement. 
        Les performances passées ne garantissent pas les résultats futurs. Consultez un conseiller financier qualifié 
        avant de prendre des décisions d'investissement.</em></p>
    </section>
    
    <footer>
        <p style="text-align: center; color: #95a5a6; margin-top: 40px;">
            Généré par FinWiz AI Investment Analysis Platform
        </p>
    </footer>
</body>
</html>
    """
    
    return html

# Usage
accessor = CrewDataAccessor()
complete_report = generate_complete_report(accessor)

# Save to file
with open("finwiz_investment_report.html", "w", encoding="utf-8") as f:
    f.write(complete_report)

print("Complete report generated: finwiz_investment_report.html")
```

### Output Example

Generates a complete, professional HTML report with:
- Table of contents with navigation links
- All four enhanced data sections integrated
- Professional styling with responsive design
- Print-friendly CSS
- Proper French language formatting
- Disclaimer and footer

## Best Practices

1. **Always Check for None**: Enhanced data may not be available
2. **Provide Fallbacks**: Show meaningful content when data is missing
3. **Use Semantic HTML**: Proper structure for accessibility
4. **Add Visual Indicators**: Use emojis and colors strategically
5. **Include Context**: Explain what metrics mean and why they matter
6. **Maintain Consistency**: Use consistent formatting across sections
7. **Support Printing**: Include print-friendly CSS
8. **Document Limitations**: Note when data is unavailable or incomplete

## See Also

- [Enhanced Data Extraction Documentation](ENHANCED_DATA_EXTRACTION.md)
- [Crew Data Integration Design](../.kiro/specs/crew-data-integration/design.md)
- [Requirements Document](../.kiro/specs/crew-data-integration/requirements.md)
