# Recommendation Engine

This document explains how FinWiz generates BUY, HOLD, and SELL recommendations based on composite scores and decision thresholds.

## Overview

The recommendation engine is the final decision layer that translates quantitative scores into actionable investment recommendations. It uses clear, deterministic thresholds aligned with industry-standard grading systems.

**Key Principle**: Recommendations are based on composite scores that combine fundamental (40%), technical (30%), and risk (30%) analysis, with adaptive weights for quality companies (50%/25%/25%).

## Recommendation Framework

### Three-Tier System

FinWiz uses a simplified three-tier recommendation system:

| Recommendation | Composite Score | Grade Range | Meaning |
|----------------|-----------------|-------------|---------|
| **BUY** | ≥ 0.85 | A+, A, B+, B | Strong opportunity - acquire or add to position |
| **HOLD** | 0.65 - 0.85 | C+, C | Mixed signals - maintain position, monitor closely |
| **SELL** | < 0.65 | D, F | Weak fundamentals or elevated risk - reduce or exit position |

### Decision Logic

```python
def generate_recommendation(composite_score: float) -> str:
    """Generate investment recommendation based on composite score."""
    if composite_score >= 0.85:
        return "BUY"
    elif composite_score >= 0.65:
        return "HOLD"
    else:
        return "SELL"
```

## Portfolio Decision Thresholds

When evaluating existing portfolio holdings, the threshold alignment is critical:

```python
# Portfolio Holdings Processor
if composite_score >= 0.65:
    decision = "KEEP"  # C grade or better
    rationale = "Acceptable performance - maintain position"
else:
    decision = "SELL"  # D or F grade
    rationale = "Underperforming - recommend exit"
```

**Key Alignment**: The KEEP threshold (0.65) matches the HOLD threshold to ensure consistency:

- **C grade (0.65-0.70)**: Minimum acceptable quality - HOLD new positions, KEEP existing positions
- **D grade (0.50-0.65)**: Below acceptable - Don't buy, SELL existing
- **F grade (<0.50)**: Critical issues - Strong sell signal

## Grade-to-Recommendation Mapping

### Detailed Grade Breakdown

| Grade | Score Range | Recommendation | Action | Rationale |
|-------|-------------|----------------|--------|-----------|
| **A+** | 0.95-1.00 | BUY | Strong buy - maximum conviction | Exceptional across all dimensions |
| **A** | 0.85-0.95 | BUY | Buy - high conviction | Excellent fundamentals and technicals |
| **B+** | 0.80-0.85 | BUY | Buy - moderate conviction | Solid opportunity, minor weaknesses |
| **B** | 0.75-0.80 | BUY | Buy - acceptable | Good overall, some concerns |
| **C+** | 0.70-0.75 | HOLD | Hold - monitor closely | Mixed signals, watch for changes |
| **C** | 0.65-0.70 | HOLD | Hold - significant concerns | Minimum acceptable quality |
| **D** | 0.50-0.65 | SELL | Sell - multiple red flags | Below acceptable standards |
| **F** | 0.00-0.50 | SELL | Strong sell - critical issues | Fundamental problems or high risk |

### Conviction Levels

**BUY Recommendations** have varying conviction levels:

- **Score 0.95+**: Maximum conviction - Core portfolio position
- **Score 0.85-0.95**: High conviction - Significant allocation
- **Score 0.80-0.85**: Moderate conviction - Standard position size
- **Score 0.75-0.80**: Acceptable - Smaller position, more monitoring

## Recommendation Rationale Generation

Each recommendation includes a detailed rationale explaining the decision:

### Template Structure

```python
rationale = (
    f"{ticker} receives a {grade} grade with a composite score of {score:.2f}. "
    f"Fundamental analysis (score: {fundamental_score:.2f}) shows "
    f"ROE of {roe:.1%}, debt-to-equity of {debt_to_equity:.2f}, and revenue growth of {revenue_growth:.1%}. "
    f"Technical analysis (score: {technical_score:.2f}) indicates {trend_direction} trend with RSI at {rsi:.1f}. "
    f"Risk assessment (score: {risk_score:.2f}) shows {volatility:.1%} volatility and maximum drawdown of {max_drawdown:.1%}. "
    f"{conclusion}"
)
```

### Conclusion Logic

```python
def generate_conclusion(composite_score: float, grade: str, recommendation: str) -> str:
    """Generate conclusion text based on recommendation."""
    if recommendation == "BUY":
        if composite_score >= 0.95:
            return "Exceptional investment opportunity with outstanding metrics across all dimensions."
        elif composite_score >= 0.85:
            return "Strong investment opportunity with excellent fundamentals and favorable risk profile."
        else:
            return "Solid investment opportunity despite minor weaknesses in some areas."

    elif recommendation == "HOLD":
        return "Mixed signals across fundamental, technical, and risk factors suggest a HOLD recommendation pending further developments."

    else:  # SELL
        if composite_score < 0.50:
            return "Critical issues in fundamentals, technicals, or risk profile warrant immediate exit."
        else:
            return "Weak fundamentals, unfavorable technical setup, or elevated risk profile warrant a SELL recommendation."
```

## Real-World Examples

### Example 1: BUY Recommendation (ASML)

**Score Breakdown:**

- Composite: 0.765 (B grade)
- Fundamental: 0.84 (A)
- Technical: 0.72 (C+)
- Risk: 0.58 (D)

**Quality Company**: Yes (3/3 criteria) → Adaptive weights (50/25/25)

**Recommendation**: **BUY**

**Rationale**:
> "ASML receives a B grade with a composite score of 0.77. Fundamental analysis (score: 0.84) shows ROE of 53.9%, debt-to-equity of 0.14, and revenue growth of 2.6%. Technical analysis (score: 0.72) indicates sideways trend with RSI at 50.0. Risk assessment (score: 0.58) shows 38.9% volatility and maximum drawdown of -23.4%. Despite high volatility typical of semiconductor sector, excellent fundamentals and quality company status justify a BUY recommendation."

**Key Decision Factors**:
- ✓ Exceptional fundamentals (ROE 53.9%, Margins 29.4%, Low debt 0.14)
- ✓ Quality company detection triggered adaptive weighting
- ✓ High volatility acceptable for cyclical semiconductor sector
- ✓ Strong competitive moat (ASML is monopoly in EUV lithography)

### Example 2: SELL Recommendation (GES)

**Score Breakdown:**

- Composite: 0.564 (D grade)
- Fundamental: 0.26 (F)
- Technical: 0.72 (C+)
- Risk: 0.58 (D)

**Quality Company**: No (0/3 criteria) → Standard weights (40/30/30)

**Recommendation**: **SELL**

**Rationale**:
> "GES receives a D grade with a composite score of 0.56. Fundamental analysis (score: 0.26) shows ROE of 7.6%, debt-to-equity of 2.97, and revenue growth of 2.3%. Technical analysis (score: 0.72) indicates sideways trend with RSI at 50.0. Risk assessment (score: 0.58) shows 27.0% volatility and maximum drawdown of -23.4%. Weak fundamentals, unfavorable technical setup, or elevated risk profile warrant a SELL recommendation."

**Key Decision Factors**:
- ✗ Poor fundamentals (ROE 7.6%, Debt 297%, Margins 1.01%)
- ✗ Altman Z-Score 2.14 indicates bankruptcy risk
- ✗ Struggling retail apparel sector with intense competition
- ✓ Neutral technicals insufficient to override fundamental concerns

### Example 3: HOLD Recommendation (Hypothetical)

**Score Breakdown:**

- Composite: 0.72 (C+ grade)
- Fundamental: 0.68 (C)
- Technical: 0.75 (B)
- Risk: 0.74 (C+)

**Recommendation**: **HOLD**

**Rationale**:
> "Ticker receives a C+ grade with a composite score of 0.72. Fundamental analysis (score: 0.68) shows moderate financial health with room for improvement. Technical analysis (score: 0.75) indicates upward trend with positive momentum. Risk assessment (score: 0.74) shows acceptable volatility profile. Mixed signals across fundamental, technical, and risk factors suggest a HOLD recommendation pending further developments."

**Key Decision Factors**:
- ~ Moderate fundamentals - not strong enough for BUY
- ✓ Positive technical trends suggest potential improvement
- ~ Risk profile acceptable but not exceptional
- ⚠ Decision: Monitor closely, re-evaluate in 3-6 months

## Special Considerations

### Quality Company Premium

Quality companies with 2+ of the following criteria receive adaptive 50/25/25 weighting:

- High ROE (≥20%)
- Low Debt (Debt/Equity ≤0.5)
- Strong Margins (≥15%)

This adjustment recognizes that short-term volatility is less relevant for companies with durable competitive advantages and strong fundamentals.

**Impact**: A company scoring 0.77 with standard weights might score 0.82 with adaptive weights, potentially pushing it from HOLD to BUY territory.

### Sector-Specific Adjustments

Certain sectors have different risk/volatility profiles:

| Sector | Typical Volatility | Typical Debt | Notes |
|--------|-------------------|--------------|-------|
| Technology | 30-40% | Low-Moderate | Higher volatility acceptable |
| Utilities | 15-25% | High | Regulated, stable cash flows |
| Financials | 25-35% | High (leverage) | Debt metrics different |
| Consumer Staples | 15-25% | Moderate | Defensive characteristics |
| Energy | 35-50% | Variable | Commodity price sensitivity |

**Future Enhancement**: Sector-specific scoring adjustments are planned (not yet implemented).

### Market Conditions

Recommendations should be contextualized with market conditions:

- **Bull Market**: HOLD recommendations may warrant closer review for upgrade to BUY
- **Bear Market**: BUY recommendations should be even higher conviction
- **High Volatility**: Risk scores may temporarily elevate, consider fundamental strength
- **Sector Rotation**: Technical scores may lag during rotation periods

## Confidence Levels

Each recommendation includes a confidence level based on data quality and completeness:

```python
confidence_level = (
    0.3 * fundamental_confidence +
    0.3 * technical_confidence +
    0.2 * risk_confidence +
    0.2 * data_quality_score
)
```

**Confidence Thresholds:**

- **High (≥0.80)**: All data fresh, complete, validated
- **Medium (0.60-0.80)**: Some data gaps or age concerns
- **Low (<0.60)**: Significant data issues, treat with caution

**Recommendation Override**: If confidence <0.50, recommendation should be downgraded:

- BUY → HOLD (insufficient confidence for entry)
- HOLD → HOLD (maintain position but monitor)
- SELL → SELL (exit regardless of confidence)

## Implementation Guidelines

### For Portfolio Managers

1. **New Positions**: Only initiate on BUY recommendations (score ≥0.85)
2. **Existing Positions**: KEEP on HOLD (≥0.65), exit on SELL (<0.65)
3. **Position Sizing**: Scale based on score within BUY range:
   - 0.95+: Full position
   - 0.85-0.95: 75-100% position
   - 0.75-0.85: 50-75% position
4. **Rebalancing Triggers**: Re-evaluate when score crosses threshold ±0.05

### For Individual Investors

1. **Risk Tolerance Adjustment**:
   - Conservative: Only BUY on score ≥0.90, SELL on <0.70
   - Moderate: Standard thresholds (BUY ≥0.85, SELL <0.65)
   - Aggressive: BUY on ≥0.80, SELL on <0.60

2. **Time Horizon**:
   - Long-term (5+ years): Emphasize fundamentals, tolerate higher volatility
   - Medium-term (1-5 years): Balanced approach, standard weights
   - Short-term (<1 year): Emphasize technicals and risk, consider tighter thresholds

## Limitations and Disclaimers

**Important Limitations:**

1. **Backward-Looking**: Scores based on historical data, not predictive guarantees
2. **Quantitative Only**: Does not include qualitative factors (management quality, brand value, ESG)
3. **Market Agnostic**: Does not account for overall market conditions or sector rotation
4. **Data Dependent**: Recommendations only as good as underlying data quality
5. **Not Financial Advice**: Educational tool, not personalized investment advice

**Best Practices:**

- Use as one input among many in investment decision process
- Validate with independent research and analysis
- Consider personal financial situation, goals, and risk tolerance
- Monitor positions regularly, don't set-and-forget
- Consult qualified financial advisor for personalized guidance

## Related Documentation

- [Deep Analysis Scoring System](deep_analysis.md) - How scores are calculated
- [Investment Methodology](investment_methodology.md) - Overall philosophy
- [Risk Framework](deep_analysis.md) - Risk assessment details
- [Data Quality](../reference/data_quality.md) - Data validation standards

## References

### Academic Research

- **Modern Portfolio Theory**: Markowitz (1952) - Risk-return optimization
- **Efficient Market Hypothesis**: Fama (1970) - Information and pricing
- **Behavioral Finance**: Kahneman & Tversky - Decision biases

### Industry Standards

- **CFA Institute**: Standards of practice for investment recommendations
- **FINRA Rule 2111**: Suitability requirements for recommendations
- **SEC Regulation Best Interest**: Fiduciary standards

---

**Last Updated**: November 2025
**Version**: 2.0 (Post-Threshold Alignment)
**Maintainer**: FinWiz Development Team
