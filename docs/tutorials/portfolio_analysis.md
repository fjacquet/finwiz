---
title: "Portfolio Analysis Tutorial"
description: "Learn how to analyze your portfolio holdings and interpret the comprehensive analysis results"
category: "tutorials"
tags:
  - "portfolio"
  - "analysis"
  - "holdings"
  - "tutorial"
date: "2025-10-26"
source: "tutorials/portfolio_holdings_analysis_user_guide.md"
---

# Portfolio Analysis Tutorial

Learn how to analyze your portfolio holdings and interpret the comprehensive analysis results, price targets, alternatives, and A+ improvement recommendations.

## Overview

The Portfolio Holdings Analysis feature provides comprehensive, actionable analysis for each holding in your portfolio. This tutorial explains how to interpret the analysis results and take action on the recommendations.

## Prerequisites

Before starting, ensure you have:

- FinWiz installed and configured (see [Getting Started](getting_started.md))
- Portfolio data in CSV format
- Required API keys configured

## Setting Up Your Portfolio Data

### Portfolio CSV Files

Your portfolio holdings should be stored in CSV files:

- **ETFs**: `data/etf.csv`
- **Stocks**: `data/stock.csv`
- **Crypto**: `data/crypto.csv` (if applicable)

### CSV Format

Use this format for your portfolio files:

```csv
Name,Ticker,Currency
Apple Inc,AAPL,USD
Microsoft Corporation,MSFT,USD
Vanguard Total Stock Market ETF,VTI,USD
Bitcoin,BTC,USD
```

**Important Notes**:

- Use official ticker symbols
- Specify the correct currency
- Include the company/fund name for clarity

## Running Portfolio Analysis

### Basic Analysis

```bash
# Run complete portfolio analysis
uv run python src/finwiz/main.py --mode portfolio_review
```

### Advanced Options

```bash
# Enable deep analysis for detailed grading
export DEEP_PORTFOLIO_ANALYSIS=true
uv run python src/finwiz/main.py --mode portfolio_review

# Analyze specific asset classes only
uv run python src/finwiz/main.py --mode portfolio_review --asset-class stock
```

## Understanding Your Portfolio Report

### Portfolio Dashboard

The top section shows your portfolio overview:

- **📊 Total Holdings**: Number of assets in your portfolio
- **🎯 Grade Distribution**: Breakdown of A+, A, B, C, D, F grades
- **💎 A+ Opportunities**: Number of A+ rated alternatives available
- **📈 Portfolio Health Score**: Overall portfolio quality (0-100)

### Grade System

| Grade | Meaning | Action |
|-------|---------|--------|
| **A+** 🌟 | Exceptional quality | Keep, consider adding more |
| **A** ✅ | High quality | Keep |
| **B** 👍 | Good quality | Keep, monitor |
| **C** ⚠️ | Average quality | Consider alternatives |
| **D** 🔻 | Below average | Review for replacement |
| **F** ❌ | Poor quality | Exit position |

### Individual Holding Analysis

Each holding includes:

- **Current Grade**: Letter grade (A+ to F)
- **Composite Score**: Numerical score (0.0-1.0)
- **Risk Assessment**: Risk level (1-10 scale)
- **Price Targets**: Buy/sell recommendations
- **Alternative Suggestions**: Better investment options

## Interpreting Price Targets

### Price Target Components

Each holding with a KEEP or BUY recommendation includes specific price targets:

#### Current Price vs Fair Value

```
Current Price: $150.00
Fair Value Estimate: $175.00
Upside Potential: +16.7%
```

- **Fair Value**: Calculated using fundamental analysis (DCF, multiples)
- **Upside/Downside**: Percentage difference from current price
- **Confidence Level**: How confident the model is (0-100%)

#### Buy Targets 💰

**Primary Buy Target**: The optimal price to add to your position

```
Buy Target: $140.00 (-6.7% from current)
Rationale: Technical support level + 10% margin of safety
```

**Secondary Buy Target**: Aggressive accumulation level

```
Secondary Buy: $130.00 (-13.3% from current)
Rationale: Strong support from 200-day moving average
```

**How to Use**:

- Set limit orders at these levels
- Use dollar-cost averaging between targets
- Don't chase prices above fair value

#### Sell Targets 📉

**Primary Sell Target**: Take profit level

```
Sell Target: $180.00 (+20% from current)
Rationale: Resistance level + fair value reached
```

**Stop-Loss Level**: Risk management exit

```
Stop-Loss: $135.00 (-10% from current)
Rationale: Below key support, invalidates thesis
```

**How to Use**:

- Set stop-loss orders immediately after buying
- Take partial profits at primary target
- Reassess if stop-loss is triggered

## Evaluating Alternative Investments

### When Alternatives Are Suggested

Alternatives appear for holdings graded **below B** (C+, C, D, or F). The system identifies better investment options by:

1. **Prioritizing A+ Candidates**: First checks for A+ rated alternatives
2. **Matching Asset Class**: Ensures alternatives are in the same asset class
3. **Comparing Metrics**: Evaluates expense ratios, fundamentals, and liquidity
4. **Calculating Improvements**: Shows expected grade and score improvements

### Comparison Analysis

Each alternative shows a detailed comparison:

| Metric | Current Holding | Alternative | Improvement |
|--------|----------------|-------------|-------------|
| **Grade** | C | A+ | ⬆️ +2 grades |
| **Expense Ratio** | 0.45% | 0.15% | ⬇️ -0.30% |
| **5Y Return** | 8.2% | 12.5% | ⬆️ +4.3% |
| **Risk Score** | 6/10 | 5/10 | ⬇️ Lower risk |

### Key Advantages

Each alternative lists specific advantages:

- ✅ **Lower costs**: Save $300/year on $100k investment
- ✅ **Better diversification**: 500 holdings vs 50
- ✅ **Higher liquidity**: $2B daily volume vs $50M
- ✅ **Stronger fundamentals**: Better P/E, growth metrics

### Transition Strategies

**Immediate Swap** 🚀

- Best for: Tax-advantaged accounts (IRA, 401k)
- Action: Sell current, buy alternative same day
- Tax Impact: None (tax-deferred account)

**Gradual Transition** 📅

- Best for: Taxable accounts with gains
- Action: Sell 25% per quarter over 1 year
- Tax Impact: Spread capital gains across tax years

**Tax-Optimized** 💡

- Best for: Large positions with significant gains
- Action: Harvest losses elsewhere, offset gains
- Tax Impact: Minimized through strategic timing

## A+ Improvement Roadmap

### Understanding the Roadmap

The A+ Improvement Roadmap shows how to systematically upgrade your portfolio quality.

#### Current State Analysis

```
Current Portfolio Composition:
• A+ Holdings: 15% (Target: 40%)
• A Holdings: 25%
• B Holdings: 35%
• C Holdings: 20%
• D/F Holdings: 5%

Gap to Target: -25% A+ allocation
```

#### Phased Implementation Plan

**Phase 1: Exit Poor Performers (Months 1-3)** 🔴

```
Priority Exits:
1. Ticker ABC (Grade F) → Replace with A+ Alternative XYZ
   Expected improvement: +$1,200/year

2. Ticker DEF (Grade D) → Replace with A+ Alternative UVW
   Expected improvement: +$800/year
```

**Phase 2: Upgrade Average Holdings (Months 4-6)** 🟡

```
Upgrade Targets:
1. Ticker GHI (Grade C) → Replace with A+ Alternative RST
   Expected improvement: +$600/year

2. Ticker JKL (Grade C) → Replace with A+ Alternative MNO
   Expected improvement: +$500/year
```

**Phase 3: Optimize Good Holdings (Months 7-12)** 🟢

```
Optimization Opportunities:
1. Ticker PQR (Grade B) → Consider A+ Alternative if cost-effective
   Expected improvement: +$300/year
```

#### Expected Outcomes

After full implementation:

```
Target Portfolio Composition:
• A+ Holdings: 40% ⬆️ (+25%)
• A Holdings: 35% ⬆️ (+10%)
• B Holdings: 20% ⬇️ (-15%)
• C Holdings: 5% ⬇️ (-15%)
• D/F Holdings: 0% ⬇️ (-5%)

Expected Annual Benefit: +$3,400/year
Portfolio Health Score: 85/100 (from 62/100)
```

## Position Sizing Recommendations

### Understanding Position Sizing

Position sizing determines what percentage of your portfolio each holding should represent.

#### Sizing Actions

**🟢 HOLD**: Current size is optimal

```
Current: 5.2%
Recommended: 5.0%
Action: No change needed
```

**🔵 ADD**: Position is underweight

```
Current: 2.1%
Recommended: 5.0%
Action: Add $2,900 to reach target (on $100k portfolio)
```

**🟡 TRIM**: Position is overweight

```
Current: 12.5%
Recommended: 8.0%
Action: Sell $4,500 to reach target (on $100k portfolio)
```

**🔴 EXIT**: Position should be eliminated

```
Current: 3.2%
Recommended: 0%
Action: Sell entire position ($3,200 on $100k portfolio)
Reason: Grade F, better alternatives available
```

### Concentration Limits

The system enforces prudent concentration limits:

| Limit Type | Maximum | Purpose |
|------------|---------|---------|
| Single Stock | 10% | Avoid company-specific risk |
| Single Sector | 35% | Diversify across economy |
| High-Risk Asset | 3% | Limit speculative exposure |
| Total Alternatives | 5% | Control experimental positions |

## Taking Action on Recommendations

### Step-by-Step Implementation

#### 1. Review the HTML Report

Open `output/portfolio/portfolio_review_fr.html` in your browser:

- Read the portfolio dashboard
- Review each holding's analysis
- Note all recommended actions

#### 2. Prioritize Actions

Create your action list:

```
High Priority (This Month):
☐ Exit: Ticker ABC (Grade F)
☐ Trim: Ticker DEF (12% → 8%)
☐ Add: Ticker GHI (2% → 5%)

Medium Priority (Next Quarter):
☐ Replace: Ticker JKL with A+ alternative
☐ Review: Ticker MNO (stale data)

Low Priority (Next 6 Months):
☐ Optimize: Consider A+ alternatives for B-grade holdings
```

#### 3. Execute Trades

For each action:

1. **Check current prices** against buy/sell targets
2. **Set limit orders** at recommended price levels
3. **Set stop-losses** for risk management
4. **Document trades** for tax records

#### 4. Monitor and Adjust

- **Weekly**: Check if limit orders executed
- **Monthly**: Review portfolio vs targets
- **Quarterly**: Re-run full analysis
- **Annually**: Reassess overall strategy

### Tax Considerations

**Tax-Advantaged Accounts** (IRA, 401k, Roth IRA):

- ✅ No immediate tax impact
- ✅ Execute swaps immediately
- ✅ Rebalance freely

**Taxable Accounts**:

- ⚠️ Capital gains tax applies
- 💡 Harvest losses to offset gains
- 💡 Hold > 1 year for long-term rates
- 💡 Consider tax-loss harvesting in December

## Data Quality and Sources

### Understanding Data Freshness

Each holding shows data freshness indicators:

**🟢 Fresh** (< 7 days old)

```
Data as of: 2025-10-26
Status: Fresh ✅
Confidence: 95%
```

**🟡 Recent** (7-30 days old)

```
Data as of: 2025-10-15
Status: Recent ⚠️
Confidence: 85%
```

**🔴 Stale** (> 30 days old)

```
Data as of: 2025-09-10
Status: Stale ⚠️⚠️
Confidence: 65% (reduced by 20%)
Action: Manual review recommended
```

### Data Sources

All analysis cites specific sources:

**Stock Analysis**:

- SEC Filings: EDGAR (10-K, 10-Q, 8-K)
- Price Data: Yahoo Finance, Alpha Vantage
- Fundamentals: Company financial statements
- Analyst Ratings: Aggregated consensus

**ETF Analysis**:

- Fund Data: Prospectus, fact sheets
- Holdings: Fund provider websites
- Performance: Yahoo Finance, Morningstar
- Expense Ratios: Official fund documents

**Crypto Analysis**:

- Price Data: Coinbase, Kraken APIs
- Market Data: CoinMarketCap
- Technical Indicators: TradingView
- On-chain Metrics: Blockchain explorers

## Frequently Asked Questions

### Q: How often should I run the analysis?

**A**: Quarterly for most investors, monthly if you're actively managing. Market conditions change, and fresh analysis ensures your decisions are based on current data.

### Q: Should I follow all recommendations immediately?

**A**: No. Prioritize:

1. Exit D/F grade holdings (high priority)
2. Trim overweight positions (medium priority)
3. Add to underweight A+ holdings (medium priority)
4. Optimize B-grade holdings (low priority)

### Q: What if I disagree with a recommendation?

**A**: The analysis is a tool, not a mandate. Consider:

- Your personal risk tolerance
- Tax implications
- Transaction costs
- Your investment thesis
- Time horizon

Use the analysis to inform your decisions, not dictate them.

### Q: How accurate are the price targets?

**A**: Price targets are estimates based on current data and models. They have varying confidence levels (shown in the report). Use them as guidelines, not guarantees. Always:

- Set stop-losses
- Diversify
- Don't invest more than you can afford to lose

## Next Steps

After completing your first portfolio analysis:

1. **Learn Deep Analysis**: Understand the [Deep Analysis Crew](../explanations/deep_analysis.md)
2. **Explore Configuration**: Check [Performance Configuration](../how-to/performance_optimization.md)
3. **Review API Reference**: Browse the [API Documentation](../reference/api/index.md)
4. **Set Up Monitoring**: Learn about [Portfolio Monitoring](../how-to/portfolio_monitoring.md)

## Support and Resources

### Additional Documentation

- **How-to Guides**: [How-to Section](../how-to/index.md)
- **Reference**: [API Reference](../reference/index.md)
- **Explanations**: [Architecture and Concepts](../explanations/index.md)

### Getting Help

- **Issues**: Report bugs or request features on GitHub
- **Questions**: Check the FAQ or developer documentation
- **Updates**: Follow release notes for new features

---

**Version**: 2.0
**Last Updated**: 2025-10-26
