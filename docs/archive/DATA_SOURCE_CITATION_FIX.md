# Data Source Citation Fix

**Date**: 2025-10-13  
**Issue**: Agents generating fake example.com URLs instead of real data sources  
**Fix**: Updated task descriptions with explicit citation requirements

## Problem

The `investment_reporter` agent was generating placeholder URLs like:
- `https://data.provider.example/SCL.F/prices`
- `https://finwiz.example.com/analytics/SCL.F/indicators`
- `https://finwiz.example.com/backtests/SCL.F/sma50_200`

These are fake URLs that don't help users verify data sources.

## Root Cause

The task description said "Include data source citations" but didn't specify:
1. What the actual data sources are
2. How to cite them properly
3. That placeholder URLs are not acceptable

## Solution Applied

### Updated `final_report_task` in `config/tasks.yaml`

Added explicit guidance on data source citations:

```yaml
5. Data Sources (Sources de Données)
   - CRITICAL: Use ONLY real data sources from upstream analysis
   - For price data: "Yahoo Finance API" or "TwelveData API" (based on actual tool used)
   - For sentiment: List actual sources (Yahoo Finance News, Perplexity Sonar, etc.)
   - For SEC data: "SEC EDGAR Database" with form type (10-K, 10-Q)
   - For technical indicators: "TwelveData Indicators API" or "TA-Lib calculations"
   - Include as-of date: {full_date}
   - NEVER use placeholder URLs like "example.com" or "finwiz.example.com"
   - If source is unknown, state "Internal calculation" or "Derived from market data"
```

### Updated Quality Checklist

```yaml
QUALITY CHECKLIST:
- ✅ Real data source citations (NO example.com URLs)
- ✅ Actual tool names cited (Yahoo Finance, TwelveData, SEC EDGAR, etc.)
```

## Expected Output Format

### Before (Bad)
```
Source / Dataset | URL (référence) | Date / As-of
Données de prix journalières | https://data.provider.example/SCL.F/prices | As-of 2025-10-13
Calculs d'indicateurs techniques | https://finwiz.example.com/analytics/SCL.F/indicators | As-of 2025-10-13
```

### After (Good)
```
Source / Dataset | Référence | Date / As-of
Données de prix journalières (OHLC) | Yahoo Finance API | As-of 2025-10-13
Indicateurs techniques (RSI, MACD, SMA, Bollinger) | TwelveData Indicators API | As-of 2025-10-13
Analyse fondamentale | SEC EDGAR Database (Form 10-K) | As-of 2025-10-13
Sentiment de marché | Yahoo Finance News + Perplexity Sonar | As-of 2025-10-13
Backtest SMA50/SMA200 | Calcul interne (TA-Lib) | Simulation: 2024-10-14 → 2025-10-13
```

## Real Data Sources Used by FinWiz

### Market Data
- **Yahoo Finance API** (`yfinance` library)
  - Price data (OHLC)
  - Company info
  - Financial statements
  - News articles

- **TwelveData API**
  - Technical indicators (RSI, MACD, Bollinger Bands, etc.)
  - Real-time and historical data
  - Multiple timeframes

- **Alpha Vantage API**
  - Alternative market data source
  - Technical indicators
  - Fundamental data

### News & Sentiment
- **Yahoo Finance News**
  - Company-specific news
  - Market news
  - Press releases

- **Perplexity Sonar API**
  - AI-powered news aggregation
  - Sentiment analysis
  - Trending topics

- **Serper API**
  - Google search results
  - News articles
  - Web content

### Fundamental Data
- **SEC EDGAR Database**
  - 10-K annual reports
  - 10-Q quarterly reports
  - 8-K current reports
  - Proxy statements

### Cryptocurrency Data
- **CoinMarketCap API**
  - Crypto prices
  - Market cap
  - Trading volume
  - Historical data

- **Kraken API**
  - Crypto exchange data
  - Order book
  - Trading pairs

### Technical Analysis
- **TA-Lib** (Technical Analysis Library)
  - Internal calculations
  - Indicator computations
  - Backtesting logic

## Implementation Notes

### Tools Return Source Information

Some tools already return source metadata:
- `EnhancedCryptoAnalysisTool`: Returns `data_sources` field
- `EnhancedETFAnalysisTool`: Returns `data_sources` field
- `StandardizedSentimentTool`: Returns `data_sources` list
- `QuantitativeAnalysisTool`: Uses TwelveData or Yahoo Finance

### Agent Should Extract Sources

The `investment_reporter` agent should:
1. Look for `data_sources` fields in upstream analysis
2. Identify which tools were used based on data structure
3. Map tool names to user-friendly source names
4. Never make up placeholder URLs

### Future Enhancement

Consider adding a `DataSourceTracker` utility that:
- Tracks which tools are called during analysis
- Records API endpoints used
- Generates proper citations automatically
- Validates that no placeholder URLs are used

## Testing

### Verify Fix
```bash
# Run deep analysis
uv run python src/finwiz/main.py

# Check output HTML for data sources section
grep -A 10 "Sources de Données" output/deep_analysis/*.html

# Verify no example.com URLs
grep "example.com" output/deep_analysis/*.html
# Should return no results
```

### Expected Result
All data source citations should reference real services:
- Yahoo Finance API
- TwelveData API
- SEC EDGAR Database
- Perplexity Sonar
- CoinMarketCap API
- Internal calculations (TA-Lib)

No placeholder URLs should appear in output.

---

**Status**: ✅ Fixed  
**Impact**: Improved transparency and data source verification  
**Risk**: Low (clarifies existing requirements)
