# A+ Investment Scoring Tool

## Overview

The A+ Investment Scoring Tool is a comprehensive evaluation system designed to identify exceptional investment opportunities across ETFs, stocks, and cryptocurrencies. It integrates with the existing FinWiz grading system to proactively discover investments with A+ potential (score ≥ 0.95).

## Key Features

### Multi-Asset Support
- **ETFs**: Evaluates expense ratios, tracking error, AUM, and issuer quality
- **Stocks**: Analyzes ROE, revenue growth, debt levels, and competitive moats
- **Cryptocurrencies**: Assesses market cap, volume, institutional adoption, and utility

### Dynamic Criteria Adjustment
- Adapts scoring criteria based on current market conditions
- Tightens requirements during bear markets and high volatility periods
- Adjusts for inflation and interest rate environments

### Comprehensive Scoring Framework
- **Fundamental Score**: Asset-specific financial metrics
- **Technical Score**: Momentum, trend strength, and volatility analysis
- **Quality Score**: Management, governance, and structural quality
- **Risk Score**: Risk-adjusted evaluation with market regime consideration

### Integration with FinWiz Grading System
- Uses existing Grade types (A+ to F) and GradeInfo structure
- Provides actionable recommendations in French
- Maintains consistency with portfolio review system

## Usage

### Basic Usage

```python
from finwiz.tools.a_plus_scoring_tool import APlusScoringTool

tool = APlusScoringTool()

# Score an ETF
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

### Custom Criteria

```python
# Apply stricter criteria
custom_criteria = {
    "etf_max_expense_ratio": 0.05,  # Very strict
    "stock_min_roe": 0.30           # High ROE requirement
}

result = tool._run(
    symbol="SPY",
    asset_type="etf",
    fundamental_data=etf_data,
    custom_criteria=custom_criteria
)
```

## Input Schema

### APlusScoringInput
- `symbol`: Investment symbol (e.g., "AAPL", "SPY", "BTC-USD")
- `asset_type`: One of "etf", "stock", "crypto"
- `fundamental_data`: Dictionary of asset-specific metrics
- `market_context`: Current market conditions (VIX, inflation, etc.)
- `custom_criteria`: Optional criteria overrides

### Fundamental Data Fields

#### ETF Data
- `expense_ratio`: Total expense ratio (%)
- `aum`: Assets under management ($)
- `tracking_error`: Tracking error vs benchmark
- `history_years`: Years of operating history
- `issuer_reputation`: Issuer quality score (0-1)

#### Stock Data
- `roe`: Return on equity (decimal)
- `revenue_growth`: Annual revenue growth rate
- `debt_to_equity`: Debt-to-equity ratio
- `market_cap`: Market capitalization ($)
- `fcf_positive`: Free cash flow positive (boolean)
- `management_quality`: Management quality score (0-1)

#### Crypto Data
- `market_cap`: Market capitalization ($)
- `daily_volume`: Average daily trading volume ($)
- `age_months`: Project age in months
- `institutional_adoption`: Institutional adoption (boolean)
- `real_utility`: Real-world utility (boolean)

## Output Structure

```python
{
    "symbol": "VTI",
    "asset_type": "etf",
    "is_a_plus_candidate": False,
    "grade": "A",
    "percentage": 90.7,
    "recommendation": "Maintenez et continuez le DCA",
    "analysis_summary": {
        "composite_score": 0.907,
        "component_scores": {
            "fundamental": 1.000,
            "technical": 0.760,
            "quality": 0.944,
            "risk": 0.715
        },
        "top_strengths": ["Excellent fundamental metrics", "High quality management"],
        "main_concerns": [],
        "confidence": 0.90
    },
    "a_plus_score": {
        # Detailed APlusScore object with full analysis
    }
}
```

## Market Regime Adaptation

The tool automatically adjusts scoring criteria based on market conditions:

### Bear Market / High Stress
- Increases ROE requirements for stocks
- Lowers debt tolerance
- Stricter expense ratio limits for ETFs
- Higher market cap requirements for crypto

### Bull Market
- Slightly relaxed criteria
- More tolerance for growth investments
- Standard risk thresholds

### High Inflation
- Emphasizes pricing power and real assets
- Higher revenue growth requirements
- Focus on companies with strong competitive moats

## A+ Criteria Thresholds

### Default Thresholds
- **ETF**: Expense ratio ≤ 0.15%, AUM ≥ $1B, Tracking error ≤ 0.20%
- **Stock**: ROE ≥ 20%, Revenue growth ≥ 15%, Debt/Equity ≤ 0.3
- **Crypto**: Market cap ≥ $10B, Daily volume ≥ $500M, Age ≥ 36 months

### A+ Score Requirements
- Composite score ≥ 0.95 for A+ grade
- All component scores should be strong
- High confidence level (≥ 0.7)
- Minimal risk concerns

## Integration with Investment Discovery Crew

The A+ Scoring Tool is designed to be used by the Investment Discovery Crew agents:

1. **ETF Discovery Agent**: Uses tool to identify A+ ETF opportunities
2. **Stock Discovery Agent**: Evaluates individual stocks for A+ potential
3. **Crypto Discovery Agent**: Assesses cryptocurrencies for quality
4. **Validation Agent**: Validates A+ candidates through backtesting

## Performance Considerations

- Market regime assessment is cached for 1 hour
- Scoring calculations are optimized for batch processing
- Error handling ensures graceful degradation
- Configurable timeout and retry logic

## Testing

Comprehensive test suite covers:
- All asset types and scoring components
- Market regime adaptation scenarios
- Custom criteria functionality
- Error handling and edge cases
- Integration with grading system

Run tests with:
```bash
uv run pytest tests/unit/tools/test_a_plus_scoring_tool.py -v
```

## Examples

See `examples/a_plus_scoring_demo.py` for comprehensive usage examples including:
- ETF, stock, and crypto scoring
- Market regime adaptation
- Custom criteria application
- Integration patterns

## Future Enhancements

- Real-time market data integration
- Machine learning model integration
- Sector-specific scoring adjustments
- ESG criteria integration
- Performance tracking and validation