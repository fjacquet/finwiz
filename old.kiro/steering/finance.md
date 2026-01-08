---
inclusion: always
---


# Financial Analysis Standards

## Asset-Specific Requirements

### Cryptocurrencies

- **Technical Focus**: Volatility patterns, support/resistance levels, momentum indicators
- **Risk Emphasis**: Extreme volatility, regulatory uncertainty, liquidity risks
- **Key Metrics**: Market cap, trading volume, tokenomics, adoption metrics
- **Data Sources**: Verified exchanges (Coinbase, Kraken), CoinMarketCap

### Stocks  

- **Fundamental Analysis**: 10-K/10-Q filings, P/E ratios, earnings growth, debt levels
- **Technical Analysis**: Moving averages, RSI, MACD for entry/exit timing
- **Sector Context**: Industry comparisons, competitive positioning
- **Data Sources**: SEC EDGAR, Yahoo Finance, Alpha Vantage

### ETFs

- **Cost Analysis**: Expense ratios, tracking error vs benchmark
- **Holdings Review**: Concentration risk, diversification quality
- **Performance**: Total return vs benchmark, risk-adjusted returns
- **Data Sources**: Fund prospectuses, Yahoo Finance ETF data

## Standardized Outputs

### Risk Assessment (Required)

```python
risk_score: int = Field(..., ge=1, le=10, description="1=Very Low, 10=Very High")
risk_factors: List[str] = Field(..., description="Specific risk categories")
systematic_risk: float = Field(..., description="Market/sector risk component")
idiosyncratic_risk: float = Field(..., description="Asset-specific risk")
```

### Investment Recommendations (Required)

```python
recommendation: str = Field(..., pattern="^(BUY|HOLD|SELL)$")
confidence: float = Field(..., ge=0.0, le=1.0)
time_horizon: str = Field(..., pattern="^(SHORT|MEDIUM|LONG)$")
price_target: Optional[float] = Field(None, description="12-month target")
rationale: str = Field(..., min_length=50, description="Detailed reasoning")
```

## Data Quality Standards

### Source Citation (Required)

- Always include data source and as-of date
- Use multiple providers for validation when possible
- Acknowledge data limitations and potential inaccuracies
- Distinguish between real-time and delayed data

### Financial Metrics

- **Valuation**: P/E, P/B, P/S ratios with sector comparisons
- **Performance**: Total return, Sharpe ratio, maximum drawdown
- **Risk**: Beta, standard deviation, correlation analysis
- **Growth**: Revenue/earnings growth rates, trend analysis

### Professional Standards

- Use standardized financial terminology
- Include relevant benchmarks and peer comparisons
- Provide context for all numerical data
- Maintain objectivity and acknowledge uncertainties
- Follow CFA Institute ethical guidelines where applicable
