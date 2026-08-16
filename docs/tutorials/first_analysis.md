---
title: "Your First FinWiz Analysis"
description: "Complete walkthrough of running your first investment analysis with FinWiz"
category: "tutorials"
tags:
  - "tutorial"
  - "first-time"
  - "analysis"
  - "walkthrough"
date: "2025-10-26"
---

# Your First FinWiz Analysis

This tutorial walks you through running your first investment analysis with FinWiz, from setup to interpreting results.

> **Note:** FinWiz has no single-ticker CLI mode. `main.py` accepts no
> command-line arguments — it always runs the whole portfolio configured in
> `data/stock.csv` / `data/etf.csv` / `data/crypto.csv` via
> `crewai flow kickoff`. Every `--ticker`/`--asset-class` command shown
> below in a previous version of this tutorial was silently ignored and
> ran the full portfolio flow instead. To analyze "just AAPL," put AAPL
> alone in `data/stock.csv` before running.

## What You'll Learn

By the end of this tutorial, you'll know how to:

- Run a single asset analysis
- Interpret FinWiz grades and scores
- Understand risk assessments
- Read price targets and recommendations
- Export and share results

## Prerequisites

Before starting, make sure you have:

- FinWiz installed (see [Getting Started](getting_started.md))
- API keys configured in your `.env` file
- Basic understanding of investment concepts

## Step 1: Choose Your First Asset

For this tutorial, we'll analyze Apple Inc. (AAPL), but you can substitute any stock ticker.

**Good first choices:**

- **Stocks**: AAPL, MSFT, GOOGL, TSLA
- **ETFs**: SPY, VTI, QQQ, VOO
- **Crypto**: BTC, ETH (if you have crypto API keys)

## Step 2: Run Your First Analysis

Open your terminal and navigate to the FinWiz directory:

```bash
cd finwiz

# Put AAPL in data/stock.csv (see the Prerequisites note above), then:
crewai flow kickoff
```

**What happens next:**

1. FinWiz validates the ticker symbol
2. Fetches current market data
3. Analyzes fundamentals and technicals
4. Generates risk assessment
5. Creates comprehensive report

**Expected runtime:** 2-5 minutes

## Step 3: Understanding the Output

### Console Output

You'll see progress messages like:

```
🔍 Validating ticker: AAPL
✅ Ticker validation successful
📊 Fetching market data...
🧮 Analyzing fundamentals...
📈 Technical analysis...
⚠️  Risk assessment...
📝 Generating report...
✅ Analysis complete!

Report saved to: output/stock/AAPL_analysis_20251026.html
```

### Output Files

FinWiz creates several files:

- **HTML Report**: `output/stock/AAPL_analysis_20251026.html` (main report)
- **JSON Data**: `output/stock/AAPL_analysis_20251026.json` (structured data)
- **Cache Files**: `cache/` (for faster future analyses)

## Step 4: Reading Your Report

Open the HTML report in your web browser. Here's what each section means:

### Executive Summary

```
📊 Apple Inc. (AAPL) Analysis
Grade: A+ 🌟
Composite Score: 0.92/1.00
Recommendation: BUY
Confidence: 87%
```

**Key metrics:**

- **Grade**: Letter grade from A+ (best) to F (worst)
- **Composite Score**: Numerical score combining all factors
- **Recommendation**: BUY, HOLD, or SELL
- **Confidence**: How certain the analysis is (0-100%)

### Detailed Scores

```
Fundamental Score: 0.89/1.00 ✅
Technical Score: 0.94/1.00 ✅
Risk Score: 3/10 🟢 (Lower is better)
```

**Score breakdown:**

- **Fundamental**: Financial health, growth, valuation
- **Technical**: Price trends, momentum, support/resistance
- **Risk**: Overall risk level (1=very low, 10=very high)

### Price Targets

```
Current Price: $150.00
Fair Value: $175.00 (+16.7% upside)

Buy Target: $140.00 (-6.7%)
Sell Target: $180.00 (+20.0%)
Stop Loss: $135.00 (-10.0%)
```

**How to use:**

- **Buy Target**: Good price to purchase
- **Sell Target**: Take profit level
- **Stop Loss**: Exit if price falls here

### Risk Assessment

```
Risk Level: 3/10 (Moderate-Low)
Risk Factors:
• Market volatility exposure
• Technology sector concentration
• Regulatory changes in tech
```

**Risk categories:**

- 1-2: Very Low Risk
- 3-4: Low Risk
- 5-6: Moderate Risk
- 7-8: High Risk
- 9-10: Very High Risk

## Step 5: Interpreting the Grade

### Grade System

Eight grades exist, not six — B+ and C+ were missing, and the D/F cutoffs
were wrong (a 0.52 composite score is graded D by the code, not F):

| Grade | Score Range | Meaning | Action |
|-------|-------------|---------|--------|
| **A+** | 0.95-1.00 | Exceptional | Strong buy |
| **A** | 0.85-0.94 | Excellent | Buy |
| **B+** | 0.80-0.84 | Very Good | Buy |
| **B** | 0.75-0.79 | Good | Hold/Buy |
| **C+** | 0.70-0.74 | Above Average | Hold |
| **C** | 0.65-0.69 | Average | Hold |
| **D** | 0.50-0.64 | Below Average | Consider selling |
| **F** | 0.00-0.49 | Poor | Sell |

### What Influences the Grade

**Positive factors:**

- Strong financial metrics (revenue growth, profitability)
- Positive technical indicators (uptrend, momentum)
- Low risk profile
- Reasonable valuation

**Negative factors:**

- Declining fundamentals
- Negative technical signals
- High risk factors
- Overvaluation

## Step 6: Making Investment Decisions

### If You Get an A+ or A Grade

**Consider buying if:**

- Price is at or below the buy target
- You have available investment capital
- The asset fits your portfolio strategy
- Risk level matches your tolerance

### If You Get a B or C Grade

**Consider holding if:**

- You already own the asset
- Fundamentals are stable
- Technical outlook is neutral
- No better alternatives available

### If You Get a D or F Grade

**Consider avoiding or selling if:**

- Fundamental problems identified
- Technical breakdown occurring
- High risk factors present
- Better alternatives available

## Step 7: Advanced Analysis Options

### Enable Deep Analysis

Per-asset-class analysis crews are controlled by feature flags (all default
to `true`). For a stock ticker, that's `FF_STOCK_ANALYSIS` (see
`FF_ETF_ANALYSIS` / `FF_CRYPTO_ANALYSIS` for the other asset classes):

```bash
# Explicitly enable stock analysis (on by default)
export FF_STOCK_ANALYSIS=true
crewai flow kickoff
```

**Deep analysis includes:**

- SEC filing analysis (10-K, 10-Q)
- Advanced technical indicators
- Sentiment analysis from news
- Peer comparison
- Industry analysis

### Compare Multiple Assets

There's no way to run several separate single-ticker analyses — every run
processes the whole portfolio at once. To compare AAPL, MSFT, and GOOGL,
list all three in `data/stock.csv` and run once:

```bash
crewai flow kickoff
```

### ETF Analysis

Add SPY to `data/etf.csv` alongside your stock holdings — one run analyzes
all asset classes together:

```bash
crewai flow kickoff
```

**ETF analysis includes:**

- Expense ratio evaluation
- Holdings analysis
- Tracking error assessment
- Diversification metrics

## Step 8: Common Patterns to Look For

### Strong Buy Signals

- Grade A+ or A
- Composite score > 0.85
- Risk score < 5
- Current price near buy target
- Positive technical momentum

### Warning Signs

- Grade D or F
- Composite score < 0.65
- Risk score > 7
- Current price above fair value
- Negative technical signals

### Hold Situations

- Grade B or C
- Stable fundamentals
- Moderate risk (4-6)
- Price near fair value
- Mixed technical signals

## Troubleshooting Common Issues

### "Ticker not found" Error

```bash
# Check the ticker spelling in your CSV — e.g. a typo like "APLE" in
# data/stock.csv instead of "AAPL"
crewai flow kickoff
# Error: Ticker APLE not found

# Fix the spelling in data/stock.csv, then re-run
crewai flow kickoff
```

### API Rate Limit Errors

```bash
# Wait a few minutes and try again
# Or check your API key limits
```

### Stale Data Warnings

```
⚠️ Warning: Data is 3 days old
Confidence reduced to 82%
```

**Solution**: Data is still usable but less reliable. Consider re-running analysis later.

### Low Confidence Scores

```
Confidence: 45%
Reason: Limited data available
```

**Possible causes:**

- New IPO with limited history
- Low trading volume
- Recent corporate actions
- Data quality issues

## Next Steps

After your first successful analysis:

1. **Try Different Assets**: Analyze various stocks, ETFs, or crypto
2. **Learn Portfolio Analysis**: See [Portfolio Analysis Tutorial](portfolio_analysis.md)
3. **Understand Deep Analysis**: Read about [Deep Analysis Features](../explanations/deep_analysis.md)

## Practice Exercises

### Exercise 1: Compare Tech Stocks

Analyze these tech stocks and compare their grades:

- AAPL (Apple)
- MSFT (Microsoft)
- GOOGL (Google)
- AMZN (Amazon)

**Questions to consider:**

- Which has the highest grade?
- Which has the lowest risk?
- Which offers the best value?

### Exercise 2: ETF Comparison

Compare these popular ETFs:

- SPY (S&P 500)
- VTI (Total Stock Market)
- QQQ (Nasdaq 100)

**Look for:**

- Expense ratio differences
- Diversification levels
- Performance metrics

### Exercise 3: Risk Assessment

Find examples of:

- Low risk investment (score 1-3)
- Moderate risk investment (score 4-6)
- High risk investment (score 7-10)

**Analyze:**

- What factors contribute to each risk level?
- How does risk affect the overall grade?

## Summary

Congratulations! You've completed your first FinWiz analysis. You now know how to:

✅ Run single asset analysis
✅ Interpret grades and scores
✅ Understand risk assessments
✅ Read price targets
✅ Make informed investment decisions

**Key takeaways:**

- Grades provide quick quality assessment
- Composite scores offer detailed evaluation
- Risk scores help manage portfolio risk
- Price targets guide entry/exit decisions
- Confidence levels indicate reliability

**Remember:**

- FinWiz provides analysis, not financial advice
- Always do your own research
- Consider your personal risk tolerance
- Diversify your investments
- Never invest more than you can afford to lose

---

**Version**: 2.0
**Last Updated**: 2025-10-26
