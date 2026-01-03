# Risk Management

Comprehensive guide to implementing and managing investment risk in FinWiz portfolios.

## Risk Management Philosophy

Effective risk management is fundamental to successful investing. FinWiz provides tools and frameworks to:

- **Identify Risks**: Systematic and idiosyncratic risk factors
- **Measure Risks**: Quantitative risk metrics and scoring
- **Monitor Risks**: Continuous risk assessment and alerts
- **Mitigate Risks**: Diversification and position sizing strategies

## Risk Assessment Framework

### Risk Score Scale (1-10)

| Score | Level | Description | Action Required |
|-------|-------|-------------|-----------------|
| 1-2 | Very Low | Minimal risk, stable assets | Monitor regularly |
| 3-4 | Low | Below-average risk | Standard monitoring |
| 5-6 | Moderate | Average market risk | Active monitoring |
| 7-8 | High | Above-average risk | Enhanced monitoring |
| 9-10 | Very High | Extreme risk | Consider reduction |

### Risk Components

**Systematic Risk (Market Risk)**

- Market volatility correlation
- Sector-specific risks
- Economic cycle sensitivity
- Interest rate sensitivity

**Idiosyncratic Risk (Asset-Specific)**

- Company fundamentals
- Management quality
- Competitive position
- Regulatory exposure

## Risk Measurement Tools

### Volatility Metrics

```python
from finwiz.risk import calculate_risk_metrics

# Calculate comprehensive risk metrics
risk_metrics = calculate_risk_metrics(
    ticker="AAPL",
    period="1Y"
)

print(f"Volatility: {risk_metrics.volatility:.2%}")
print(f"Beta: {risk_metrics.beta:.2f}")
print(f"VaR (95%): {risk_metrics.var_95:.2%}")
print(f"Max Drawdown: {risk_metrics.max_drawdown:.2%}")
```

### Portfolio Risk Analysis

```python
from finwiz.portfolio import PortfolioRiskAnalyzer

analyzer = PortfolioRiskAnalyzer()
portfolio_risk = analyzer.analyze_portfolio_risk(holdings)

# Portfolio-level metrics
print(f"Portfolio Beta: {portfolio_risk.portfolio_beta:.2f}")
print(f"Diversification Ratio: {portfolio_risk.diversification_ratio:.2f}")
print(f"Concentration Risk: {portfolio_risk.concentration_risk:.2%}")
```

## Risk Mitigation Strategies

### 1. Diversification

**Asset Class Diversification**

```python
# Recommended allocation ranges
allocation_targets = {
    "stocks": (60, 80),      # 60-80% stocks
    "bonds": (15, 30),       # 15-30% bonds
    "alternatives": (5, 15)   # 5-15% alternatives
}
```

**Geographic Diversification**

- Domestic: 60-70%
- International Developed: 20-30%
- Emerging Markets: 5-15%

**Sector Diversification**

- No single sector > 25%
- Technology exposure < 30%
- Defensive sectors: 20-40%

### 2. Position Sizing

**Risk-Based Position Sizing**

```python
def calculate_position_size(risk_score, portfolio_value, max_risk_per_position=0.02):
    """Calculate position size based on risk score."""
    # Higher risk = smaller position
    risk_multiplier = (11 - risk_score) / 10  # Inverse relationship
    base_allocation = 0.05  # 5% base allocation
    
    position_size = base_allocation * risk_multiplier
    max_position = portfolio_value * max_risk_per_position
    
    return min(position_size * portfolio_value, max_position)
```

**Position Limits**

- Maximum single position: 10% of portfolio
- Maximum sector exposure: 25% of portfolio
- Maximum country exposure: 15% for non-domestic

### 3. Risk Monitoring

**Continuous Monitoring**

```python
from finwiz.monitoring import RiskMonitor

monitor = RiskMonitor()

# Set up risk alerts
monitor.add_alert(
    condition="portfolio_beta > 1.3",
    action="email_alert",
    message="Portfolio beta exceeds target"
)

monitor.add_alert(
    condition="max_drawdown > 0.15",
    action="rebalance_trigger",
    message="Maximum drawdown threshold breached"
)
```

**Risk Reporting**

- Daily risk metrics updates
- Weekly portfolio risk reports
- Monthly stress testing
- Quarterly risk review

## Stress Testing

### Scenario Analysis

```python
from finwiz.stress_testing import StressTester

tester = StressTester()

# Historical scenarios
scenarios = [
    "2008_financial_crisis",
    "2020_covid_pandemic",
    "2022_inflation_surge"
]

for scenario in scenarios:
    result = tester.run_scenario(portfolio, scenario)
    print(f"{scenario}: {result.portfolio_impact:.2%}")
```

### Monte Carlo Simulation

```python
# Run Monte Carlo simulation
mc_results = tester.monte_carlo_simulation(
    portfolio=portfolio,
    time_horizon=252,  # 1 year
    simulations=10000
)

print(f"95% VaR: {mc_results.var_95:.2%}")
print(f"Expected Shortfall: {mc_results.expected_shortfall:.2%}")
print(f"Probability of Loss > 20%: {mc_results.prob_loss_20:.2%}")
```

## Risk-Adjusted Performance

### Sharpe Ratio Optimization

```python
from finwiz.optimization import SharpeOptimizer

optimizer = SharpeOptimizer()
optimal_weights = optimizer.optimize_portfolio(
    assets=portfolio_assets,
    target_return=0.10,  # 10% target return
    risk_free_rate=0.02  # 2% risk-free rate
)
```

### Risk Parity Approach

```python
from finwiz.optimization import RiskParityOptimizer

rp_optimizer = RiskParityOptimizer()
risk_parity_weights = rp_optimizer.optimize(
    assets=portfolio_assets,
    risk_budget={
        "stocks": 0.60,
        "bonds": 0.25,
        "alternatives": 0.15
    }
)
```

## Risk Budgeting

### Allocation by Risk Contribution

```python
def allocate_by_risk_contribution(assets, risk_budget):
    """Allocate portfolio based on risk contribution targets."""
    
    risk_contributions = {}
    for asset in assets:
        # Calculate marginal contribution to portfolio risk
        marginal_risk = calculate_marginal_risk(asset, portfolio)
        risk_contributions[asset] = marginal_risk
    
    # Adjust weights to match risk budget
    adjusted_weights = adjust_weights_for_risk_budget(
        risk_contributions, 
        risk_budget
    )
    
    return adjusted_weights
```

### Risk Limits

**Portfolio-Level Limits**

- Maximum portfolio volatility: 18%
- Maximum portfolio beta: 1.2
- Maximum correlation with market: 0.85
- Maximum drawdown tolerance: 20%

**Position-Level Limits**

- Maximum position volatility: 35%
- Maximum position beta: 2.0
- Minimum liquidity: $1M daily volume
- Maximum concentration: 10% of portfolio

## Dynamic Risk Management

### Volatility Targeting

```python
class VolatilityTargetingStrategy:
    def __init__(self, target_volatility=0.15):
        self.target_volatility = target_volatility
    
    def adjust_exposure(self, current_volatility, current_exposure):
        """Adjust exposure based on realized volatility."""
        volatility_ratio = self.target_volatility / current_volatility
        adjusted_exposure = current_exposure * volatility_ratio
        
        # Apply bounds
        return max(0.5, min(1.5, adjusted_exposure))
```

### Risk-On/Risk-Off Signals

```python
def assess_market_regime():
    """Assess current market regime for risk management."""
    
    indicators = {
        "vix_level": get_vix_level(),
        "credit_spreads": get_credit_spreads(),
        "yield_curve": get_yield_curve_slope(),
        "momentum": get_market_momentum()
    }
    
    # Risk-off signals
    risk_off_count = 0
    if indicators["vix_level"] > 25:
        risk_off_count += 1
    if indicators["credit_spreads"] > historical_average * 1.5:
        risk_off_count += 1
    if indicators["yield_curve"] < 0:
        risk_off_count += 1
    if indicators["momentum"] < -0.05:
        risk_off_count += 1
    
    if risk_off_count >= 3:
        return "RISK_OFF"
    elif risk_off_count <= 1:
        return "RISK_ON"
    else:
        return "NEUTRAL"
```

## Risk Reporting

### Daily Risk Dashboard

```python
def generate_risk_dashboard(portfolio):
    """Generate daily risk dashboard."""
    
    dashboard = {
        "portfolio_value": portfolio.total_value,
        "daily_var": calculate_daily_var(portfolio),
        "portfolio_beta": calculate_portfolio_beta(portfolio),
        "concentration_risk": calculate_concentration_risk(portfolio),
        "sector_exposures": calculate_sector_exposures(portfolio),
        "top_risk_contributors": get_top_risk_contributors(portfolio, n=5)
    }
    
    return dashboard
```

### Risk Alerts

```python
class RiskAlertSystem:
    def __init__(self):
        self.alert_thresholds = {
            "portfolio_var": 0.03,      # 3% daily VaR
            "position_weight": 0.10,     # 10% max position
            "sector_weight": 0.25,       # 25% max sector
            "beta": 1.3,                 # Max portfolio beta
            "correlation": 0.90          # Max market correlation
        }
    
    def check_alerts(self, portfolio):
        """Check for risk threshold breaches."""
        alerts = []
        
        # Check each threshold
        for metric, threshold in self.alert_thresholds.items():
            current_value = calculate_metric(portfolio, metric)
            if current_value > threshold:
                alerts.append({
                    "metric": metric,
                    "current": current_value,
                    "threshold": threshold,
                    "severity": "HIGH" if current_value > threshold * 1.2 else "MEDIUM"
                })
        
        return alerts
```

## Best Practices

### Risk Management Principles

1. **Diversification is Key**: Never put all eggs in one basket
2. **Position Sizing Matters**: Risk-adjusted position sizing
3. **Monitor Continuously**: Regular risk assessment and monitoring
4. **Stress Test Regularly**: Test portfolio under adverse scenarios
5. **Stay Disciplined**: Stick to risk management rules

### Common Mistakes to Avoid

- **Over-concentration**: Too much in single positions or sectors
- **Ignoring Correlations**: Assets that move together in crises
- **Static Risk Management**: Not adapting to changing conditions
- **Emotional Decisions**: Abandoning risk rules during stress
- **Inadequate Diversification**: False diversification with correlated assets

## Related Documentation

- [Portfolio Optimization](../portfolio_rebalancing/index.md)
- [Risk Framework](../explanations/deep_analysis.md)
- [Investment Methodology](../explanations/investment_methodology.md)
- [Performance Monitoring](portfolio_monitoring.md)
