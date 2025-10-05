# Portfolio Rebalancing Documentation

## Overview

FinWiz provides a comprehensive portfolio rebalancing system with professional-grade optimization and analysis. The system generates optimal trade recommendations, analyzes transaction costs, and validates against risk constraints.

## Key Features

- **Intelligent Trade Recommendations**: Generate optimal buy/sell recommendations to maintain target allocations
- **Multiple Optimization Strategies**: Choose from minimize trades, minimize costs, or risk-aware rebalancing
- **Transaction Cost Analysis**: Comprehensive cost modeling including commissions, spreads, and market impact
- **Risk Management**: Built-in safeguards with concentration limits, turnover monitoring, and volatility-based recommendations
- **Scenario Analysis**: Compare different rebalancing approaches and what-if scenarios
- **Historical Tracking**: Monitor rebalancing effectiveness and performance attribution over time

## Documentation

### 📖 [User Guide](user_guide.md)

Complete guide for using the rebalancing system:

- Getting started
- Rebalancing methods
- Understanding recommendations
- Cost analysis
- Risk management
- Scenario comparison

### 🔧 [Developer Guide](developer_guide.md)

Technical documentation for developers:

- Architecture overview
- Core components
- Extending the system
- Integration patterns
- Testing strategies

### 📚 [API Reference](api_reference.md)

Complete API documentation:

- Python APIs
- Data schemas
- Configuration options
- Request/response examples

## Quick Start

### Basic Rebalancing

```python
from finwiz.orchestrators.portfolio_rebalancing import PortfolioRebalancingOrchestrator
from finwiz.schemas.portfolio_rebalancing import PortfolioConfiguration, Holding

# Configure your portfolio
config = PortfolioConfiguration(
    holdings=[
        Holding(symbol="AAPL", shares=100.0),
        Holding(symbol="GOOGL", shares=25.0),
        Holding(symbol="MSFT", shares=50.0),
    ],
    target_weights={
        "AAPL": 0.40,   # 40%
        "GOOGL": 0.35,  # 35%
        "MSFT": 0.25,   # 25%
    },
    global_tolerance=0.05,  # ±5% tolerance
    available_capital=5000.0
)

# Run rebalancing analysis
orchestrator = PortfolioRebalancingOrchestrator()
result = await orchestrator.rebalance_portfolio(config)

# Generate comprehensive report
html_report = await orchestrator.generate_rebalancing_report(result)
```

## Rebalancing Methods

### MINIMIZE_TRADES

Reduces the number of transactions (ideal for high-cost accounts)

### MINIMIZE_COSTS

Optimizes for lowest total transaction costs

### RISK_AWARE

Considers risk metrics and concentration limits

## Output Files

After rebalancing completes:

- `output/rebalancing/rebalancing_report.html` - HTML report
- `output/rebalancing/rebalancing_result.json` - Structured data
- `output/rebalancing/scenario_comparison.html` - Scenario analysis

## Integration

The rebalancing system integrates with:

- **Portfolio Review**: Uses holding analysis for rebalancing decisions
- **Portfolio Monitoring**: Continuous drift monitoring with alerts
- **Risk Assessment**: Validates against risk constraints

## See Also

- [Portfolio Holdings Analysis](../portfolio_holdings_analysis_user_guide.md)
- [Portfolio Monitoring System](../portfolio_monitoring_system.md)
- [Quantitative Analysis](../quantitative_analysis.md)

---

**Version**: 2.0  
**Last Updated**: 2025-03-10
