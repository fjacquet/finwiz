# Yahoo Finance Data Availability Analysis

## Summary

✅ **Yahoo Finance DOES provide all critical financial metrics** needed for FinWiz analysis.

## Test Results (AAPL - 2025-11-01)

### Critical Fields - ALL AVAILABLE ✅

| Field | Yahoo Finance Key | Value (AAPL) | Status |
|-------|------------------|--------------|--------|
| **ROE** | `returnOnEquity` | 1.71 (171%) | ✅ Available |
| **Debt/Equity** | `debtToEquity` | 133.8 | ✅ Available |
| **Revenue Growth** | `revenueGrowth` | 0.079 (7.9%) | ✅ Available |
| **Profit Margin** | `profitMargins` | 0.269 (26.9%) | ✅ Available |
| **Current Price** | `currentPrice` or `regularMarketPrice` | $270.37 | ✅ Available |
| **Beta** | `beta` | 1.094 | ✅ Available |

### Additional Metrics Available

- `totalRevenue` - Total Revenue
- `ebitda` - EBITDA
- `earningsGrowth` - Earnings Growth
- `marketCap` - Market Capitalization
- `trailingPE` - P/E Ratio (Trailing)
- `forwardPE` - P/E Ratio (Forward)
- `priceToBook` - Price to Book Ratio
- `fiftyTwoWeekHigh` / `fiftyTwoWeekLow` - 52-week range
- `averageVolume` - Average Trading Volume
- `dividendYield` - Dividend Yield

**Total Available Keys**: 182 data points

## Current Implementation

### YahooFinanceCompanyInfoTool

Located: `src/finwiz/tools/yahoo_finance_company_info_tool.py`

**Extracts**:
```python
"financial_metrics": {
    "revenue": info.get("totalRevenue", "N/A"),
    "profit_margin": info.get("profitMargins", "N/A"),
    "ebitda": info.get("ebitda", "N/A"),
    "debt_to_equity": info.get("debtToEquity", "N/A"),      # ✅ Available
    "return_on_equity": info.get("returnOnEquity", "N/A"),  # ✅ Available
    "revenue_growth": info.get("revenueGrowth", "N/A"),     # ✅ Available
    "earnings_growth": info.get("earningsGrowth", "N/A"),
}
```

### Data Flow

1. **Tool Call**: `YahooFinanceCompanyInfoTool._run(ticker="AAPL")`
2. **API Call**: `yf.Ticker("AAPL").info`
3. **Data Extraction**: Extract `returnOnEquity`, `debtToEquity`, etc.
4. **Data Mapping**: Map to FinWiz schema fields
5. **Scoring**: Use in `DeepAnalysisScorer.calculate_composite_score()`

## Field Mapping

### Yahoo Finance → FinWiz Schema

| FinWiz Field | Yahoo Finance Key | Type | Notes |
|--------------|------------------|------|-------|
| `roe` | `returnOnEquity` | float | Decimal (1.71 = 171%) |
| `debt_to_equity` | `debtToEquity` | float | Ratio (133.8 = 133.8:1) |
| `revenue_growth` | `revenueGrowth` | float | Decimal (0.079 = 7.9%) |
| `profit_margin` | `profitMargins` | float | Decimal (0.269 = 26.9%) |
| `current_price` | `currentPrice` or `regularMarketPrice` | float | USD |
| `beta` | `beta` | float | Market sensitivity |
| `volatility` | Calculated from history | float | Requires historical data |

## Data Availability by Asset Class

### Stocks ✅
- **ROE**: ✅ `returnOnEquity`
- **Debt/Equity**: ✅ `debtToEquity`
- **Revenue Growth**: ✅ `revenueGrowth`
- **Profit Margin**: ✅ `profitMargins`
- **Beta**: ✅ `beta`

### ETFs ✅
- **Expense Ratio**: ✅ `annualReportExpenseRatio`
- **AUM**: ✅ `totalAssets`
- **Tracking Error**: ⚠️ Must be calculated
- **Holdings**: ✅ Via `etf_data.funds_data.top_holdings`

### Crypto ⚠️
- **Market Cap**: ✅ `marketCap`
- **Volume**: ✅ `volume24Hr` (via CoinMarketCap)
- **Age**: ❌ Not available (must calculate from inception date)
- **Supply**: ✅ `circulatingSupply`, `totalSupply`

## Potential Issues

### 1. Data Freshness
- Yahoo Finance data may be delayed (15-20 minutes for free tier)
- Real-time data requires premium subscription

### 2. Missing Data
- Some tickers may not have all fields (e.g., small-cap stocks)
- International stocks may have limited data
- Newly listed companies may lack historical metrics

### 3. Data Quality
- ROE can be extremely high or negative (distorted by low equity)
- Debt/Equity can be very high for leveraged companies
- Revenue growth can be negative or extremely volatile

## Recommendations

### 1. Keep Critical Fields Validation ✅

The critical fields validation we implemented is **still necessary** because:

- **Not all tickers have complete data** (small-cap, international, new listings)
- **API failures happen** (rate limits, network issues, service outages)
- **Data quality varies** (some fields may be null or invalid)

### 2. Add Data Quality Checks

```python
# Check for unrealistic values
if roe > 5.0:  # 500% ROE is suspicious
    logger.warning(f"Unrealistic ROE for {ticker}: {roe}")
    
if debt_to_equity > 500:  # 500:1 leverage is extreme
    logger.warning(f"Extreme debt/equity for {ticker}: {debt_to_equity}")
```

### 3. Use Multiple Data Sources

For critical analysis, consider:
- **Primary**: Yahoo Finance (free, comprehensive)
- **Backup**: Alpha Vantage (fundamental data)
- **Validation**: SEC EDGAR (official filings)

### 4. Cache Data Aggressively

Since Yahoo Finance provides the data, cache it to:
- Reduce API calls
- Improve performance
- Handle API failures gracefully

## Testing Recommendations

### Test with Various Tickers

```bash
# Large-cap tech (should have complete data)
uv run python test_yahoo_finance_data.py AAPL

# Small-cap stock (may have missing data)
uv run python test_yahoo_finance_data.py SOME_SMALL_CAP

# International stock (may have limited data)
uv run python test_yahoo_finance_data.py 0700.HK

# ETF (different data structure)
uv run python test_yahoo_finance_data.py SPY

# Crypto (via Yahoo Finance)
uv run python test_yahoo_finance_data.py BTC-USD
```

### Monitor Missing Data Rates

```python
# Track how often critical fields are missing
missing_roe_count = 0
total_analyzed = 0

for ticker in portfolio:
    data = get_yahoo_data(ticker)
    if data.get("returnOnEquity") is None:
        missing_roe_count += 1
    total_analyzed += 1

missing_rate = missing_roe_count / total_analyzed
if missing_rate > 0.10:  # More than 10% missing
    logger.warning(f"High missing data rate: {missing_rate:.1%}")
```

## Conclusion

✅ **Yahoo Finance provides all critical fields** we need for stock analysis
✅ **Current implementation correctly extracts** ROE, debt/equity, revenue growth
✅ **Critical fields validation is still necessary** to handle missing data and API failures
⚠️ **Data quality checks should be added** to detect unrealistic values
⚠️ **Backup data sources recommended** for production reliability

---

**Test Date**: 2025-11-01  
**Test Ticker**: AAPL  
**Yahoo Finance Version**: yfinance library (latest)  
**Status**: ✅ All critical fields available
