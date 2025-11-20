# Investment Methodology

This document explains FinWiz's comprehensive investment methodology, philosophy, and decision-making framework.

## Overview

FinWiz employs a **quantitative, rules-based investment methodology** that combines fundamental analysis, technical analysis, and risk assessment to generate objective, data-driven investment decisions. The system emphasizes **transparency, repeatability, and adaptability** while maintaining strict quality standards.

**Core Philosophy**: Use deterministic Python calculations for speed and cost efficiency, reserve AI for complex reasoning that requires contextual understanding.

## Investment Philosophy

### Fundamental Principles

1. **Data-Driven Decision Making**
   - Every recommendation backed by quantitative metrics
   - No subjective judgment or gut feelings
   - Transparent scoring methodology with full calculation lineage

2. **Quality Over Quantity**
   - Focus on exceptional companies with durable competitive advantages
   - Adaptive weighting for quality companies (50/25/25 vs 40/30/30)
   - Higher standards for BUY recommendations (score ≥0.85)

3. **Risk-Adjusted Returns**
   - Return potential evaluated relative to risk exposure
   - Volatility, drawdown, and beta considered alongside fundamentals
   - Sector-appropriate risk tolerance (e.g., tech vs utilities)

4. **Multi-Dimensional Analysis**
   - **Fundamental (40%)**: Long-term business quality
   - **Technical (30%)**: Market sentiment and momentum
   - **Risk (30%)**: Downside protection and volatility

5. **Fail Fast Validation**
   - Reject invalid data at source (sanity checks)
   - No garbage in, no garbage out
   - Strict validation prevents misleading recommendations

## Analytical Framework

### Three-Pillar Approach

#### 1. Fundamental Analysis (40% Weight)

**Purpose**: Evaluate long-term business quality and financial health.

**Key Metrics**:

- **ROE (Return on Equity)**: Capital efficiency and profitability
  - Excellent: ≥30% (1.0 score)
  - Acceptable: 10-30% (0.4-0.8 score)
  - Poor: <10% (0.2 score)

- **Debt-to-Equity Ratio**: Financial leverage and risk
  - Excellent: ≤0.3 (1.0 score)
  - Acceptable: 0.3-2.0 (0.4-0.8 score)
  - Poor: >2.0 (0.2 score)

- **Revenue Growth**: Business expansion trajectory
  - Excellent: ≥20% (1.0 score)
  - Acceptable: 0-20% (0.4-0.8 score)
  - Concerning: <0% (0.2 score)

- **Profit Margin**: Pricing power and operational efficiency
  - Excellent: ≥20% (1.0 score)
  - Acceptable: 5-20% (0.4-0.8 score)
  - Poor: <5% (0.2 score)

**Philosophy**: Companies with strong fundamentals deserve premium valuations and weather downturns better.

#### 2. Technical Analysis (30% Weight)

**Purpose**: Capture market sentiment, momentum, and timing signals.

**Key Indicators**:

- **RSI (Relative Strength Index)**: Overbought/oversold conditions
  - Optimal: 40-60 (neutral, sustainable)
  - Acceptable: 30-70 (moderate momentum)
  - Extreme: <30 or >70 (reversal risk)

- **Trend Analysis**: Price relative to moving averages
  - Strong uptrend: Price >10% above 200-day MA
  - Sideways: Price within ±5% of 200-day MA
  - Downtrend: Price below 200-day MA

- **MACD (Moving Average Convergence Divergence)**: Momentum shifts
  - Positive crossover: Bullish signal
  - Negative crossover: Bearish signal

**Philosophy**: Even great companies can have poor entry/exit timing. Technicals help optimize timing.

#### 3. Risk Assessment (30% Weight)

**Purpose**: Quantify downside risk and volatility exposure.

**Key Measures**:

- **Volatility (Annualized Std Dev)**: Price fluctuation magnitude
  - Low: ≤15% (defensive)
  - Moderate: 15-35% (balanced)
  - High: >35% (aggressive)

- **Maximum Drawdown**: Worst peak-to-trough decline
  - Low: ≤10% (stable)
  - Moderate: 10-30% (typical)
  - High: >30% (volatile)

- **Beta**: Market sensitivity
  - Defensive: <0.7 (less volatile than market)
  - Neutral: 0.7-1.2 (market-like)
  - Aggressive: >1.2 (more volatile than market)

**Philosophy**: Risk management is return management. Understand downside before chasing upside.

## Quality Company Framework

### Detection Criteria

A company qualifies as "quality" when meeting **2 of 3 criteria**:

1. **High ROE** (≥20%) - Superior capital efficiency
2. **Low Debt** (Debt/Equity ≤0.5) - Financial stability
3. **Strong Margins** (≥15%) - Competitive moat

### Adaptive Weighting

Quality companies receive **50/25/25** weighting (fundamental/technical/risk) instead of standard **40/30/30**:

**Rationale**:

- Quality companies with durable advantages weather short-term volatility
- Strong fundamentals more predictive of long-term returns
- Short-term technicals and risk less relevant for quality franchises

**Example**: ASML (monopoly in EUV lithography) - High volatility (38.9%) acceptable given exceptional fundamentals (ROE 53.9%, Debt 0.14, Margins 29.4%)

## Scoring Methodology

### Composite Score Calculation

```python
# Standard companies
composite_score = (
    0.40 * fundamental_score +
    0.30 * technical_score +
    0.30 * risk_score
)

# Quality companies (2+ quality criteria met)
composite_score = (
    0.50 * fundamental_score +  # +10% emphasis on fundamentals
    0.25 * technical_score +    # -5% less weight on technicals
    0.25 * risk_score           # -5% less weight on short-term risk
)
```

### Grading Scale

| Grade | Score Range | Quality Level |
|-------|-------------|---------------|
| **A+** | 0.95-1.00 | Exceptional - Rare investment gems |
| **A** | 0.85-0.95 | Excellent - Strong buy candidates |
| **B+** | 0.80-0.85 | Very Good - Solid opportunities |
| **B** | 0.75-0.80 | Good - Acceptable with minor concerns |
| **C+** | 0.70-0.75 | Fair - Hold, monitor developments |
| **C** | 0.65-0.70 | Mediocre - Minimum acceptable |
| **D** | 0.50-0.65 | Poor - Sell, multiple red flags |
| **F** | 0.00-0.50 | Failing - Strong sell, critical issues |

### Recommendation Thresholds

- **BUY**: Score ≥0.85 (A or better)
- **HOLD**: Score 0.65-0.85 (B+ to C)
- **SELL**: Score <0.65 (D or F)

## Data Quality Standards

### Validation Hierarchy

1. **Sanity Checks** - Reject obviously invalid data:
   - ROE exactly 0.0 or >200%
   - Price ≤$0
   - Debt/Equity >100
   - Revenue growth outside -95% to +1000%

2. **Freshness Requirements**:
   - Financial data: <90 days stale
   - Price data: <1 day stale
   - Fundamental metrics: <1 quarter stale

3. **Source Priority**:
   - Primary: Calculated from actual financials
   - Secondary: Vendor-provided (validated)
   - Never: Placeholder or estimated data

### Fail Fast Principle

**Philosophy**: It's better to reject analysis than provide misleading recommendations.

**Implementation**:

```python
# Example: Revenue growth validation
if not (−0.95 <= revenue_growth <= 10.0):
    raise CriticalFieldError("Revenue growth outside valid range")

if revenue_growth == stale_yfinance_value:
    # Calculate from actual financials instead
    revenues = financials.loc['Total Revenue']
    revenue_growth = (latest - previous) / previous
```

**Result**: ASML revenue growth corrected from 0.7% (stale) to 2.56% (calculated), changing score and grade.

## Investment Decision Process

### For New Positions

```text
1. Screen universe → Identify candidates with score ≥0.75
2. Deep analysis → Calculate composite score across 3 dimensions
3. Quality check → Detect if adaptive weights apply
4. Generate grade → Map score to letter grade
5. Recommendation → BUY (≥0.85), HOLD (0.65-0.85), SELL (<0.65)
6. Position sizing → Scale allocation based on conviction:
   - 0.95+: Full position (maximum conviction)
   - 0.85-0.95: 75-100% position (high conviction)
   - 0.75-0.85: 50-75% position (moderate conviction)
```

### For Existing Positions

```text
1. Re-score holding → Calculate current composite score
2. Compare threshold → Check against 0.65 KEEP/SELL threshold
3. Decision:
   - Score ≥0.65 → KEEP (C grade or better)
   - Score <0.65 → SELL (D or F grade)
4. Monitor → Re-evaluate quarterly or on material news
```

### Portfolio Construction

**Diversification Guidelines**:

- Maximum 15-20 positions for meaningful diversification
- No single position >15% of portfolio (concentration risk)
- Sector limits: Max 30% in any single sector
- Quality mix: Aim for 50%+ in quality companies (adaptive weights)

**Rebalancing Triggers**:

- Score crosses threshold ±0.05 (e.g., 0.70 → 0.75 may warrant HOLD → BUY upgrade)
- Quarterly review minimum
- Material news events (earnings surprises, management changes)

## Sector Considerations

### Sector-Specific Characteristics

Different sectors have different "normal" profiles:

| Sector | Typical ROE | Typical Debt | Typical Volatility | Notes |
|--------|-------------|--------------|-------------------|-------|
| **Technology** | 20-30% | Low-Moderate | 30-40% | High growth, rapid innovation |
| **Healthcare** | 15-25% | Moderate | 25-35% | Regulatory risk, long R&D cycles |
| **Financials** | 10-15% | High | 25-35% | Leverage-based model |
| **Consumer Staples** | 15-25% | Moderate | 15-25% | Defensive, stable demand |
| **Energy** | 10-20% | High | 35-50% | Commodity price sensitivity |
| **Utilities** | 8-12% | High | 15-25% | Regulated, stable cash flows |
| **Industrials** | 12-18% | Moderate-High | 25-35% | Cyclical, capital-intensive |
| **Real Estate** | 5-10% | Very High | 20-30% | Leverage-heavy, interest rate sensitive |

**Future Enhancement**: Sector-specific scoring adjustments (not yet implemented).

## AI Minimalism Philosophy

### Use Python For

✅ **Deterministic Calculations**:

- Composite score computation
- Grade assignment
- Metric validation
- Data transformation

**Benefits**: 50-100x faster, $0 cost, 100% repeatable

### Use AI For

✅ **Complex Reasoning**:

- Qualitative analysis (management quality, competitive position)
- News sentiment analysis
- Industry research and context
- Report narrative generation

**Benefits**: Captures nuance, handles unstructured data, provides context

### Cost-Performance Trade-off

| Task | Python | AI | Speedup | Cost Savings |
|------|--------|----|---------|--------------| | Scoring | 50-100ms | 5-10s | 50-100x | 100% |
| Validation | <1ms | N/A | N/A | 100% |
| Calculation | <1ms | 2-5s | 1000x+ | 100% |
| Analysis | N/A | 10-30s | N/A | - |

## Performance Optimization

### Batch Processing

For portfolios with 10+ holdings:

- **Sequential**: 5-11 hours (66 holdings)
- **Batch (5 concurrent)**: 20-40 minutes (66 holdings)
- **Speedup**: 10-20x

### Data Pre-fetching

- Fetch all ticker data upfront (2-5 seconds)
- Cache results with TTL (45 minutes default)
- Parallel API calls where possible

### Caching Strategy

```python
# Cache hierarchy
1. Memory cache (fastest, session-scoped)
2. File cache (fast, persistent across sessions)
3. Hybrid cache (best of both)

# TTL configuration
CACHE_TTL=2700  # 45 minutes (covers typical portfolio analysis)
```

## Limitations and Future Enhancements

### Current Limitations

1. **Quantitative Only**: No qualitative factors (management, brand, ESG)
2. **Backward-Looking**: Historical data, not predictive
3. **Market Agnostic**: Doesn't adjust for market conditions or cycles
4. **Sector Neutral**: No sector-specific adjustments (yet)
5. **US-Centric**: Optimized for US equities, limited international

### Planned Enhancements

**Near-Term** (3-6 months):

- Sector-specific scoring adjustments
- ESG integration (environmental, social, governance)
- Sentiment analysis from news/social media
- Enhanced alternatives matching algorithm

**Medium-Term** (6-12 months):

- Machine learning for threshold optimization
- Adaptive sector weighting based on cycle
- Options-implied volatility analysis
- Peer comparison benchmarking

**Long-Term** (12+ months):

- Macroeconomic factor integration
- Alternative data sources (satellite, web traffic)
- Real-time portfolio monitoring
- Predictive modeling for forward-looking scores

## Best Practices

### For Analysts

1. **Validate Data**: Always check data freshness and completeness
2. **Context Matters**: Consider sector norms and market conditions
3. **Multiple Sources**: Verify critical metrics with independent sources
4. **Document Assumptions**: Track calculation inputs and logic
5. **Monitor Changes**: Re-score on material events, minimum quarterly

### For Portfolio Managers

1. **Systematic Process**: Follow decision framework consistently
2. **Position Sizing**: Scale by conviction level (score within BUY range)
3. **Diversification**: Maintain sector limits and position size caps
4. **Rebalancing Discipline**: Act on threshold crossings
5. **Risk Management**: Respect SELL signals, don't average down on fundamentals

### For Individual Investors

1. **Start Small**: Begin with paper trading or small positions
2. **Understand Scores**: Read methodology, don't blindly follow
3. **Risk Tolerance**: Adjust thresholds for personal risk profile
4. **Time Horizon**: Align strategy with investment timeframe
5. **Professional Advice**: Consult qualified advisor for personalized guidance

## Ethical Considerations

### Transparency

- All scoring logic is open and documented
- No black-box algorithms or hidden factors
- Full calculation lineage available for audit

### Objectivity

- Rules-based system eliminates human bias
- Same methodology applied to all securities
- No conflicts of interest (no positions in analyzed securities)

### Limitations Disclosure

- Clear about what system can and cannot do
- Not financial advice, educational tool only
- Users must make own investment decisions

### Data Privacy

- No personal data collected or stored
- Analysis results private to user
- No sharing of portfolio holdings

## Related Documentation

- [Deep Analysis Scoring System](deep_analysis.md) - Detailed scoring methodology
- [Recommendation Engine](recommendation_engine.md) - BUY/HOLD/SELL logic
- [Risk Framework](risk_framework.md) - Risk assessment details
- [Data Quality](../reference/data_quality.md) - Validation standards

## References

### Academic Literature

- **Modern Portfolio Theory**: Markowitz, H. (1952) - Portfolio Selection
- **Factor Investing**: Fama, E. & French, K. (1992) - Multi-factor models
- **Quality Investing**: Asness, C. et al. (2014) - Quality Minus Junk
- **Behavioral Finance**: Kahneman, D. & Tversky, A. - Prospect Theory

### Industry Practice

- **CFA Institute**: Investment Analysis and Portfolio Management
- **GARP**: Quantitative Investment Analysis
- **CAIA**: Alternative Investments and Modern Portfolio Theory

### Technical Resources

- **Python for Finance**: McKinney, W. - pandas for financial analysis
- **Quantitative Trading**: Chan, E. - Algorithmic trading strategies
- **Machine Learning**: Hastie, T. et al. - Statistical learning methods

---

**Last Updated**: November 2025
**Version**: 2.0 (Post-Adaptive Weights & Quality Framework)
**Maintainer**: FinWiz Development Team
