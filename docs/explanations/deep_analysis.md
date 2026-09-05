# Deep Analysis Scoring System

This document explains the comprehensive scoring system used by FinWiz's Deep Analysis crew to evaluate investment opportunities.

## Overview

The Deep Analysis scoring system is a deterministic, Python-based engine that analyzes assets across three dimensions:

- **Fundamental Analysis** (40% weight) - Financial health and performance
- **Technical Analysis** (30% weight) - Price trends and momentum
- **Risk Assessment** (30% weight) - Volatility and downside risk

For quality companies with exceptional fundamentals, adaptive weights (50%/25%/25%) are automatically applied to emphasize stability over short-term volatility.

## Scoring Architecture

### Composite Score Calculation

```python
# Standard weighting (most companies)
composite_score = 0.40 * fundamental_score + 0.30 * technical_score + 0.30 * risk_score

# Adaptive weighting (quality companies)
composite_score = (
    0.50 * fundamental_score  # +10% emphasis
    + 0.25 * technical_score  # -5% reduction
    + 0.25 * risk_score  # -5% reduction
)
```

### Quality Company Detection

A company must first clear a **mandatory gate**: `fundamental_score >= 0.80`.
A company hitting all three criteria below but scoring 0.79 on fundamentals is
not treated as quality and gets the standard 40/30/30 weights.

Past that gate, it qualifies when it meets **at least 2 of 3 criteria**:

| Criterion | Threshold | Rationale |
|-----------|-----------|-----------|
| High ROE | ≥ 20% | Superior capital efficiency |
| Low Debt | Debt/Equity ≤ 0.5 | Financial stability |
| Strong Margins | Profit Margin ≥ 15% | Competitive moat and pricing power |

**Examples:**

- **ASML** (ROE 53.9%, Debt 0.14, Margin 29.4%) → 3/3 criteria = Quality Company ✓
- **Apple** (High ROE, High Margin, but Debt 1.52) → 2/3 criteria = Quality Company ✓
- **GES** (ROE 7.56%, Debt 2.97, Margin 1.01%) → 0/3 criteria = Standard Weighting

## Fundamental Analysis (40% Weight)

Evaluates long-term financial health and business quality.

### Fundamental Metrics and Scoring

| Metric | Excellent | Very Good | Good | Acceptable | Poor | Score Formula |
|--------|-----------|-----------|------|------------|------|---------------|
| **ROE** | ≥20% | 15-20% | 10-15% | 5-10% | <5% | 1.0 / 0.8 / 0.6 / 0.4 / 0.2 |
| **Debt/Equity** | ≤0.3 | 0.3-0.5 | 0.5-1.0 | 1.0-2.0 | >2.0 | 1.0 / 0.8 / 0.6 / 0.4 / 0.2 |
| **Revenue Growth** | ≥20% | 12-20% | 5-12% | 0-5% | <0% | 1.0 / 0.8 / 0.6 / 0.4 / 0.2 |
| **Profit Margin** | ≥20% | 15-20% | 10-15% | 5-10% | <5% | 1.0 / 0.8 / 0.6 / 0.4 / 0.2 |

### Fundamental Score Calculation

```python
fundamental_score = 0.40 * roe_score + 0.30 * debt_score + 0.20 * growth_score + 0.10 * margin_score
```

### Key Principles

1. **Tolerant of Mature Companies**: 0-5% growth scores 0.4 (acceptable) instead of penalizing
2. **ROE Sanity Check**: Rejects ROE exactly 0.0 or >200% as data errors
3. **Debt Context**: Considers industry norms (tech vs industrials)
4. **Revenue Growth Source**: Calculated from actual financials, not yfinance's stale field

## Technical Analysis (30% Weight)

Evaluates price momentum, trends, and market sentiment.

### Technical Metrics and Scoring

| Metric | Excellent | Very Good | Good | Acceptable | Poor |
|--------|-----------|-----------|------|------------|------|
| **RSI (14)** | 40-60 | 30-40, 60-70 | 20-30, 70-80 | 10-20, 80-90 | <10, >90 |
| **Trend** | Strong uptrend | Moderate uptrend | Sideways | Moderate downtrend | Strong downtrend |
| **MACD** | Positive crossover | Positive | Neutral | Negative | Negative crossover |

### Technical Score Calculation

```python
technical_score = 0.40 * rsi_score + 0.40 * trend_score + 0.20 * momentum_score
```

### Trend Classification

- **Strong Uptrend**: Price >10% above 200-day MA (score: 1.0)
- **Moderate Uptrend**: Price 5-10% above 200-day MA (score: 0.8)
- **Sideways**: Price within ±5% of 200-day MA (score: 0.5)
- **Downtrend**: Price below 200-day MA (score: 0.2-0.4)

## Risk Assessment (30% Weight)

Evaluates volatility, downside risk, and market sensitivity.

### Risk Metrics and Scoring

| Metric | Very Low Risk | Low Risk | Moderate Risk | High Risk | Very High Risk |
|--------|---------------|----------|---------------|-----------|----------------|
| **Volatility** | ≤15% | 15-25% | 25-35% | 35-50% | >50% |
| **Max Drawdown** | ≤10% | 10-20% | 20-35% | 35-50% | >50% |
| **Beta** (scored on \|beta − 1.0\|) | ≤0.20 | ≤0.40 | ≤0.60 | ≤1.00 | >1.00 |

### Risk Score Calculation

```python
risk_score = 0.50 * volatility_score + 0.30 * drawdown_score + 0.20 * beta_score
```

### Key Adjustments

1. **Cyclical Sectors**: Volatility thresholds raised 5% (semiconductors, industrials naturally more volatile)
2. **Market Correlation**: beta is scored on *deviation from 1.0*, not on an absolute range — a beta of 0.85 and one of 1.15 score identically
3. **Volatility leads**: volatility carries strictly more weight (0.50) than max drawdown (0.30)

## Grading Scale

| Grade | Score Range | Recommendation | Description |
|-------|-------------|----------------|-------------|
| **A+** | 0.95 - 1.00 | **BUY** | Exceptional opportunity - all metrics excellent |
| **A** | 0.85 - 0.95 | **BUY** | Strong buy - excellent fundamentals and technicals |
| **B+** | 0.80 - 0.85 | **HOLD** | Good - solid across all dimensions |
| **B** | 0.75 - 0.80 | **HOLD** | Attractive - minor weaknesses acceptable |
| **C+** | 0.70 - 0.75 | **HOLD** | Hold - mixed signals, monitor closely |
| **C** | 0.65 - 0.70 | **HOLD** | Hold - significant concerns in 1-2 areas |
| **D** | 0.50 - 0.65 | **SELL** | Sell - multiple red flags |
| **F** | 0.00 - 0.50 | **SELL** | Strong sell - fundamental problems |

### Recommendation Thresholds

```python
if composite_score >= 0.85:
    recommendation = "BUY"
elif composite_score >= 0.65:
    recommendation = "HOLD"
else:
    recommendation = "SELL"
```

### Portfolio Decision Thresholds

```python
# Portfolio holdings processor
if composite_score >= 0.65:
    decision = "KEEP"  # C grade or better
else:
    decision = "SELL"  # D or F grade
```

## Data Quality and Validation

### Critical Field Sanity Checks

All metrics undergo validation before scoring:

| Field | Valid Range | Rejection Criteria |
|-------|-------------|-------------------|
| ROE | -50% to +200% | Exactly 0.0 or outside range |
| Current Price | >$0 | ≤ $0 |
| Debt/Equity | 0 to 100 | < 0 or > 100 |
| Revenue Growth | -95% to +1000% | Outside range or obviously stale |
| Volatility | 0% to 500% | < 0 or > 500% |
| Beta | -5.0 to +10.0 | Outside range |

### Revenue Growth Calculation

**Problem**: yfinance's `revenueGrowth` field is often stale or incorrect.

**Solution**: Calculate from actual financial statements:

```python
financials = ticker_data.financials
revenues = financials.loc["Total Revenue"].sort_index(ascending=False)
latest = revenues.iloc[0]
previous = revenues.iloc[1]
revenue_growth = (latest - previous) / previous
```

**Example (ASML)**:

- ❌ yfinance field: 0.7% (incorrect)
- ✅ Calculated: (28.26B - 27.56B) / 27.56B = 2.56% (correct)

### Error Handling

When data fails validation:

1. **Strict Mode** (`VALIDATION_STRICTNESS=error`): Halt analysis, raise exception
2. **Warn Mode** (`VALIDATION_STRICTNESS=warn`): Log warning, skip metric (default)
3. **Off Mode** (`VALIDATION_STRICTNESS=off`): Accept any data (development only)

## Real-World Examples

### Example 1: ASML (Semiconductor Equipment)

**Metrics:**

- ROE: 53.9% (Excellent: 1.0)
- Debt/Equity: 0.14 (Excellent: 1.0)
- Revenue Growth: 2.56% (Acceptable: 0.4)
- Profit Margin: 29.4% (Excellent: 1.0)
- Volatility: 38.9% (Moderate: 0.6)

**Quality Company Detection:**

- ✓ High ROE (53.9% > 20%)
- ✓ Low Debt (0.14 < 0.5)
- ✓ Strong Margins (29.4% > 15%)
- **Result**: 3/3 criteria → Adaptive weights applied

**Scoring:**

```text
Fundamental: 0.84 (A)
Technical: 0.72 (C+)
Risk: 0.58 (D)

# With adaptive weights (50/25/25):
Composite = 0.50 * 0.84 + 0.25 * 0.72 + 0.25 * 0.58 = 0.765

Grade: B
Recommendation: BUY
```

**Insight**: Despite high volatility (semiconductor sector), excellent fundamentals and quality company status justify BUY recommendation.

### Example 2: GES (Guess - Retail Apparel)

**Metrics:**

- ROE: 7.56% (Poor: 0.2)
- Debt/Equity: 2.97 (Very Poor: 0.2)
- Revenue Growth: 2.3% (Acceptable: 0.4)
- Profit Margin: 1.01% (Very Poor: 0.2)
- Altman Z-Score: 2.14 (Bankruptcy risk zone)

**Quality Company Detection:**

- ✗ Low ROE (7.56% < 20%)
- ✗ High Debt (2.97 > 0.5)
- ✗ Weak Margins (1.01% < 15%)
- **Result**: 0/3 criteria → Standard weights

**Scoring:**

```text
Fundamental: 0.26 (F)
Technical: 0.72 (C+)
Risk: 0.58 (D)

# Standard weights (40/30/30):
Composite = 0.40 * 0.26 + 0.30 * 0.72 + 0.30 * 0.58 = 0.564

Grade: D
Recommendation: SELL
```

**Insight**: Poor fundamentals and bankruptcy risk override neutral technicals. Clear SELL signal.

### Example 3: VOW.DE (Volkswagen - Automotive)

**Metrics:**

- ROE: 3.6% (Very Poor: 0.2)
- Debt/Equity: 1.30 (Poor: 0.4)
- Revenue Growth: 2.3% (Acceptable: 0.4)
- Profit Margin: 2.3% (Poor: 0.2)

**Scoring:**

```text
Fundamental: 0.26 (F)
Technical: 0.72 (C+)
Risk: 0.58 (D)

Composite: 0.494

Grade: F
Recommendation: SELL
```

**Insight**: Failed traditional automotive manufacturer with weak fundamentals.

## Performance Characteristics

### Speed

- **Python Scorer**: 50-100ms per ticker
- **AI Scorer (deprecated)**: 5-10 seconds per ticker
- **Speedup**: 50-100x faster

### Cost

- **Python Scorer**: $0 per analysis
- **AI Scorer (deprecated)**: $0.01-0.05 per analysis
- **Savings**: 100% cost reduction

### Accuracy

- **Deterministic**: Same input always produces same output
- **Transparent**: Every score has clear calculation lineage
- **Auditable**: Full calculation metadata stored in lineage

## Configuration

### Environment Variables

```bash
# Validation strictness
VALIDATION_STRICTNESS=warn  # off, warn, error

# Per-asset-class analysis crews (all default to true)
FF_STOCK_ANALYSIS=true
FF_ETF_ANALYSIS=true
FF_CRYPTO_ANALYSIS=true

# Batch processing for portfolios
BATCH_PREFETCH_ENABLED=true
DEEP_ANALYSIS_BATCH_SIZE=5
```

### Scoring Thresholds

Configurable in `src/finwiz/scoring/thresholds.py`:

```python
@dataclass
class ScoringThresholds:
    # Fundamental thresholds
    roe_excellent: float = 0.20
    roe_very_good: float = 0.20
    # ... more thresholds

    # Weighting (can be overridden for special cases)
    weight_fundamental: float = 0.40
    weight_technical: float = 0.30
    weight_risk: float = 0.30
```

## Future Enhancements

### Planned Features

- Sector-specific scoring adjustments
- ESG integration
- Sentiment analysis from news/social media
- Options-implied volatility analysis
- Peer comparison benchmarking

### Research Areas

- Machine learning for threshold optimization
- Adaptive sector weighting
- Macroeconomic factor integration
- Alternative data sources (satellite imagery, web traffic)

## Related Documentation

- [Recommendation Engine](recommendation_engine.md) - BUY/HOLD/SELL logic
- [Investment Methodology](investment_methodology.md) - Overall philosophy
- [Risk Framework](deep_analysis.md) - Risk assessment details
- [Quantitative Analysis](../reference/quantitative_analysis.md) - Technical indicators

## References

### Academic Literature

- **Factor Investing**: Fama-French five-factor model
- **Quality Metrics**: Piotroski F-Score, Altman Z-Score
- **Risk Measures**: VaR, CVaR, maximum drawdown
- **Technical Analysis**: "Technical Analysis of the Financial Markets" by John Murphy

### Industry Standards

- CFA Institute: Global Investment Performance Standards (GIPS)
- FINRA: Suitability and know-your-customer rules
- SEC: Investment Advisers Act disclosures

---

**Last Updated**: November 2025
**Version**: 2.0 (Post-Adaptive Weights Implementation)
**Maintainer**: FinWiz Development Team
