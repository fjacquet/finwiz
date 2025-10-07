# A+ Investment System

Complete guide to the A+ investment discovery, scoring, and monitoring system.

## Table of Contents

1. [Overview](#overview)
2. [A+ Scoring](#a-scoring)
3. [A+ Monitoring](#a-monitoring)
4. [Portfolio Integration](#portfolio-integration)

## Overview

The A+ Investment System identifies and monitors exceptional investment opportunities with scores ≥ 0.95. It consists of three integrated components:

1. **Discovery**: Proactively finds A+ opportunities across ETFs, stocks, and crypto
2. **Scoring**: Evaluates investments using comprehensive multi-factor analysis
3. **Monitoring**: Continuously tracks A+ investments to ensure quality maintenance

## A+ Scoring

### Core Principles

1. **Multi-Dimensional Analysis**: Each investment is evaluated across four key dimensions
2. **Dynamic Adaptation**: Criteria adjust based on market conditions and regimes
3. **Asset-Specific Optimization**: Different scoring models for ETFs, stocks, and crypto
4. **Risk-Adjusted Quality**: Emphasis on sustainable, high-quality investments
5. **Quantitative Rigor**: Data-driven approach with statistical validation

### Scoring Framework

**Composite Score Components**:

- **Fundamental Score** (35%): Asset-specific financial metrics
- **Technical Score** (20%): Momentum, trend strength, and technical indicators
- **Quality Score** (30%): Management, governance, structural quality
- **Risk Score** (15%): Risk-adjusted evaluation

**A+ Threshold**: Composite score ≥ 0.95

### Asset-Specific Criteria & Scoring

#### ETFs (A+ Criteria)

- Expense ratio ≤ 0.15% (broad market) or ≤ 0.25% (specialized)
- AUM ≥ $1 billion
- Tracking error ≤ 0.20% (3-year)
- History ≥ 3 years
- UCITS compliant (for European investors)

```python
def calculate_etf_fundamental_score(data: dict) -> float:
    """
    ETF fundamental scoring based on cost efficiency and structure quality.
    """
    expense_score = max(0, 1 - (data['expense_ratio'] / 0.15))
    aum_score = min(1, data['aum'] / 1e9)
    tracking_score = max(0, 1 - (data['tracking_error'] / 0.002))
    history_score = min(1, data['history_years'] / 5)
    
    return (expense_score * 0.4 + aum_score * 0.3 + 
            tracking_score * 0.2 + history_score * 0.1)
```

#### Stocks (A+ Criteria)

- ROE ≥ 20% (maintained 3+ years)
- Revenue growth ≥ 15% annually (5-year)
- Debt/equity ≤ 0.3
- Positive and growing free cash flow
- Dominant market position in growing sector

```python
def calculate_stock_fundamental_score(data: dict) -> float:
    """
    Stock fundamental scoring based on profitability and growth.
    """
    roe_score = min(1, data['roe'] / 0.20)
    growth_score = min(1, data['revenue_growth'] / 0.15)
    debt_score = max(0, 1 - (data['debt_to_equity'] / 0.3))
    fcf_score = 1.0 if data['fcf_positive'] else 0.0
    margin_score = min(1, data['profit_margin'] / 0.10)
    
    return (roe_score * 0.3 + growth_score * 0.25 + debt_score * 0.2 + 
            fcf_score * 0.15 + margin_score * 0.1)
```

#### Crypto (A+ Criteria)

- Market cap ≥ $10 billion
- Daily volume ≥ $500 million
- Institutional adoption proven
- Real utility and use cases
- Active development team

```python
def calculate_crypto_fundamental_score(data: dict) -> float:
    """
    Crypto fundamental scoring based on adoption and utility.
    """
    mcap_score = min(1, data['market_cap'] / 10e9)
    volume_score = min(1, data['daily_volume'] / 500e6)
    age_score = min(1, data['age_months'] / 36)
    adoption_score = 1.0 if data['institutional_adoption'] else 0.0
    utility_score = 1.0 if data['real_utility'] else 0.0
    
    return (mcap_score * 0.3 + volume_score * 0.2 + age_score * 0.2 + 
            adoption_score * 0.15 + utility_score * 0.15)
```

### Dynamic Criteria Adjustment

**Market Regime Adaptation**:

**High Inflation (>4%)**:

- Prioritize real assets (REITs, commodities)
- Emphasize pricing power for stocks
- Adjust nominal growth thresholds

**Rising Interest Rates**:

- Tighten criteria for REITs and utilities
- Favor low-debt companies
- Adjust valuation models

**High Volatility (VIX >25)**:

- Increase quality requirements
- Emphasize defensive characteristics
- Tighten risk score thresholds

### Usage

**Basic Scoring**:

```python
from finwiz.tools.a_plus_scoring_tool import APlusScoringTool

tool = APlusScoringTool()

result = tool._run(
    symbol="VTI",
    asset_type="etf",
    fundamental_data={
        "expense_ratio": 0.03,
        "aum": 300e9,
        "tracking_error": 0.0005,
        "history_years": 20
    },
    market_context={"vix": 18, "inflation": 2.8}
)

print(f"Grade: {result['grade']}")
print(f"A+ Candidate: {result['is_a_plus_candidate']}")
print(f"Composite Score: {result['analysis_summary']['composite_score']:.3f}")
```

**Custom Criteria**:

```python
custom_criteria = {
    "etf_max_expense_ratio": 0.05,  # Stricter
    "stock_min_roe": 0.30           # Higher ROE
}

result = tool._run(
    symbol="SPY",
    asset_type="etf",
    fundamental_data=etf_data,
    custom_criteria=custom_criteria
)
```

## A+ Monitoring

### Continuous Monitoring

**Key Features**:

- Automated re-evaluation (default: weekly)
- Grade degradation detection
- Market regime awareness
- Performance tracking
- Alert system

### Alert System

**Alert Severity Levels**:

- **Critical**: A+ → C or below (immediate action)
- **High**: A+ → B (review within 24 hours)
- **Medium**: A+ → B+ (review within week)
- **Low**: Minor score decrease (monitor)

**Alert Triggers**:

- Grade degradation
- Performance below benchmark
- Risk score increase
- Fundamental deterioration

### Performance Tracking

**Tracked Metrics**:

- Total return
- Alpha vs benchmark
- Sharpe ratio
- Maximum drawdown
- Grade maintenance duration
- Volatility

### Usage

**Start Monitoring**:

```python
from finwiz.services.a_plus_monitoring_service import get_monitoring_service

service = get_monitoring_service()
await service.start_service()
```

**Add Investments**:

```python
# Process discovery results
discovery_result = await investment_discovery_crew.run()
await service.process_discovery_results(discovery_result)
```

**Get Status**:

```python
# Get monitoring dashboard
dashboard = await service.get_monitoring_dashboard()

print(f"Total monitored: {dashboard['performance_summary']['total_investments']}")
print(f"A+ maintained: {dashboard['performance_summary']['a_plus_count']}")
print(f"Degraded: {dashboard['performance_summary']['degraded_count']}")
```

**CLI Operations**:

```bash
# Start monitoring
uv run python -m finwiz.tools.a_plus_monitoring_cli start

# Check status
uv run python -m finwiz.tools.a_plus_monitoring_cli status

# Get alerts
uv run python -m finwiz.tools.a_plus_monitoring_cli alerts

# Stop monitoring
uv run python -m finwiz.tools.a_plus_monitoring_cli stop
```

## Portfolio Integration

### Discovery Integration

**Automatic A+ Discovery**:

```bash
# Run discovery across all asset types
uv run python src/finwiz/main.py --discovery

# Discover specific asset type
uv run python src/finwiz/main.py --discovery --asset-type etf
```

**Output**:

- `output/discovery/discovery_latest.json` - Latest A+ opportunities
- `output/discovery/discovery_YYYY-MM-DD.json` - Timestamped results
- `output/discovery/discovery_report.html` - HTML report

### Alternative Finder Integration

The `AlternativeFinder` tool prioritizes A+ candidates when suggesting alternatives for underperforming holdings:

```python
from finwiz.tools.alternative_finder_tool import AlternativeFinder

finder = AlternativeFinder()

# Finds A+ alternatives from discovery crew
alternatives = finder.find_alternatives(holding, max_alternatives=3)

# A+ candidates are marked
for alt in alternatives:
    if alt.is_a_plus_candidate:
        print(f"A+ Alternative: {alt.ticker} (Grade: {alt.grade})")
```

### Portfolio Review Integration

A+ opportunities are integrated into portfolio reviews:

1. **Current Holdings**: Graded using A+ scoring system
2. **Alternatives**: A+ candidates suggested for underperforming holdings
3. **Improvement Roadmap**: Phased plan to increase A+ allocation

**Target A+ Allocation**:

- Conservative: 20-30% A+ holdings
- Moderate: 30-40% A+ holdings
- Aggressive: 40-50% A+ holdings

### Monitoring Integration

**Automatic Monitoring**:

- A+ discoveries automatically added to monitoring
- Portfolio holdings graded A+ are monitored
- Alerts integrated into portfolio reports

**Monitoring Dashboard**:

```python
from finwiz.orchestrators.a_plus_monitoring_orchestrator import APlusMonitoringOrchestrator

orchestrator = APlusMonitoringOrchestrator()
dashboard = await orchestrator.get_monitoring_dashboard()

# Dashboard includes:
# - Performance summary
# - Active alerts
# - Grade distribution
# - Recent degradations
# - Replacement suggestions
```

## Best Practices

### Discovery

1. **Run Monthly**: Full discovery on first Monday of each month
2. **Review Results**: Manually review A+ candidates before adding to portfolio
3. **Diversify**: Don't concentrate in single A+ opportunity
4. **Monitor Criteria**: Understand why each investment is A+ rated

### Scoring

1. **Use Market Context**: Always provide current market conditions
2. **Custom Criteria**: Adjust criteria for your risk tolerance
3. **Validate Results**: Cross-check with other sources
4. **Understand Components**: Review individual score components

### Monitoring

1. **Weekly Reviews**: Check monitoring dashboard weekly
2. **Act on Alerts**: Respond to critical alerts within 24 hours
3. **Track Performance**: Review performance metrics monthly
4. **Update Criteria**: Adjust monitoring criteria as markets change

### Portfolio Integration

1. **Gradual Transition**: Don't rush to 100% A+ allocation
2. **Tax Considerations**: Use tax-optimized transition strategies
3. **Rebalance Regularly**: Quarterly rebalancing recommended
4. **Maintain Diversification**: Don't sacrifice diversification for A+ grade

## Configuration

### Environment Variables

```bash
# A+ Discovery
DISCOVERY_ENABLED=true
DISCOVERY_FREQUENCY=weekly

# A+ Monitoring
MONITORING_ENABLED=true
MONITORING_INTERVAL=weekly
MONITORING_ALERT_THRESHOLD=24  # hours

# A+ Scoring
APLUS_THRESHOLD=0.95
APLUS_CUSTOM_CRITERIA={}
```

### Monitoring Configuration

```python
# config/monitoring.yaml
monitoring:
  enabled: true
  interval: weekly
  alert_thresholds:
    critical: 24  # hours
    high: 72
    medium: 168
  performance_tracking:
    enabled: true
    benchmarks:
      etf: "SPY"
      stock: "^GSPC"
      crypto: "BTC-USD"
```

## See Also

- [Investment Discovery Documentation](investment_discovery/) - Complete discovery guide
- [Portfolio Holdings Analysis](portfolio_holdings_analysis_user_guide.md) - Portfolio analysis
- [Alternative Finder](API_REFERENCE.md#alternativefinder) - Alternative finding tool
- [API Reference](API_REFERENCE.md) - Complete API documentation

---

**Version**: 2.0  
**Last Updated**: 2025-03-10
