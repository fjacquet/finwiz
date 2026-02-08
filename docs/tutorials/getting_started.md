---
title: "Getting Started with FinWiz"
description: "Learn how to set up and run your first FinWiz analysis with step-by-step instructions"
category: "tutorials"
tags:
  - "getting-started"
  - "setup"
  - "installation"
date: "2025-10-26"
source: "tutorials/USER_GUIDE.md"
---

# Getting Started with FinWiz

Complete guide for deploying, operating, and running your first FinWiz analysis.

## Prerequisites

**System Requirements**:

- Python 3.12+
- `uv` package manager (recommended) or `pip`
- Linux, macOS, or Windows with WSL
- Minimum 2GB RAM (4GB+ recommended)
- Minimum 1GB free storage

**Required API Keys**:

- `OPENAI_API_KEY` - LLM operations ([Get key](https://platform.openai.com/api-keys))
- `SERPER_API_KEY` - Web search ([Get key](https://serper.dev/))
- `FIRECRAWL_API_KEY` - Web scraping ([Get key](https://firecrawl.dev/))
- `ALPHA_VANTAGE_API_KEY` - Financial data ([Get key](https://www.alphavantage.co/support/#api-key))

**Optional API Keys**:

- `CHART_IMG_API_KEY` - Chart generation
- `TWELVE_DATA_API_KEY` - Technical indicators
- `COINMARKETCAP_API_KEY` - Crypto data
- `PPLX_API_KEY` - Perplexity Sonar integration

## Installation

```bash
# Clone repository
git clone <repo-url>
cd finwiz

# Install dependencies
uv pip install .

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Verify installation
uv run python -c "import finwiz; print('✅ Installation successful')"
```

## Environment Configuration

Create `.env` file with required configuration:

```bash
# Required API Keys
OPENAI_API_KEY=your_openai_key
SERPER_API_KEY=your_serper_key
FIRECRAWL_API_KEY=your_firecrawl_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key

# Validation Configuration
VALIDATION_STRICTNESS=warn  # off, warn, error

# Caching Configuration
CACHE_BACKEND=hybrid        # memory, file, hybrid
CACHE_TTL=2700             # 45 minutes
CACHE_MAX_MEMORY_ITEMS=1000
CACHE_MAX_FILE_SIZE_MB=100
CACHE_STRATEGY=ttl         # ttl, lru, lfu, adaptive

# Feature Flags
FF_PERPLEXITY_RESEARCH=false
PORTFOLIO_REVIEW_ENABLED=true

# Performance Optimization (Deep Analysis)
RISK_ASSESSMENT_USE_MINI=true    # Use gpt-4o-mini for risk assessment (faster, cheaper)
USE_MINIMAL_RISK_TOOLS=true      # Use minimal tool set for risk assessor (Phase 2 optimization)

# Portfolio Configuration
PORTFOLIO_ETF_CSV=data/etf.csv
PORTFOLIO_STOCK_CSV=data/stock.csv
```

## Running Your First Analysis

### Single Asset Analysis

Analyze a specific stock, ETF, or cryptocurrency:

```bash
# Analyze a stock
uv run python src/finwiz/main.py --ticker AAPL --asset-class stock

# Analyze an ETF
uv run python src/finwiz/main.py --ticker VOO --asset-class etf

# Analyze cryptocurrency
uv run python src/finwiz/main.py --ticker BTC --asset-class crypto
```

### Portfolio Analysis

Analyze your entire portfolio:

```bash
# Run portfolio review
uv run python src/finwiz/main.py --mode portfolio_review
```

Your portfolio holdings should be stored in CSV files:

- **ETFs**: `data/etf.csv`
- **Stocks**: `data/stock.csv`
- **Crypto**: `data/crypto.csv` (if applicable)

Example CSV format:

```csv
Name,Ticker,Currency
Apple Inc,AAPL,USD
Microsoft Corporation,MSFT,USD
Vanguard Total Stock Market ETF,VTI,USD
```

## Understanding Your Results

### Output Files

After analysis completes, you'll find:

- **HTML Report**: `output/portfolio/portfolio_review_fr.html` (French, user-friendly)
- **JSON Data**: `output/portfolio/portfolio_review.json` (structured data)

### Grade System

FinWiz uses a letter grade system to rate investments:

| Grade     | Meaning             | Action                     |
| --------- | ------------------- | -------------------------- |
| **A+** 🌟 | Exceptional quality | Keep, consider adding more |
| **A** ✅  | High quality        | Keep                       |
| **B** 👍  | Good quality        | Keep, monitor              |
| **C** ⚠️  | Average quality     | Consider alternatives      |
| **D** 🔻  | Below average       | Review for replacement     |
| **F** ❌  | Poor quality        | Exit position              |

## Deployment Environments

### Development

```bash
# Run with debug logging
export LOG_LEVEL=DEBUG
uv run python src/finwiz/main.py
```

### Staging

```bash
# Run with validation warnings
export VALIDATION_STRICTNESS=warn
uv run python src/finwiz/main.py
```

### Production

```bash
# Run with strict validation
export VALIDATION_STRICTNESS=error
export LOG_LEVEL=INFO
uv run python src/finwiz/main.py
```

## Daily Operations

### Health Check

**Morning Checklist** (5-10 minutes):

1. **System Health**:

```bash
# Check logs for errors
tail -n 100 logs/finwiz_error.log

# Check application logs
grep -i "warning\|error" logs/finwiz.log | tail -n 20
```

1. **Performance Metrics**:

```python
from finwiz.cache import get_cache_manager

cache = get_cache_manager()
stats = cache.get_statistics()
print(f"Cache hit rate: {stats.hit_rate:.2%}")
print(f"Total requests: {stats.total_requests}")
```

### Monitoring

**Key Metrics to Monitor**:

- Cache hit rate (target: >50%)
- API response times (target: <2s)
- Error rate (target: <1%)
- Validation failures (investigate if >5%)

**Log Locations**:

- Application logs: `logs/finwiz.log`
- Error logs: `logs/finwiz_error.log`
- Agent logs: `logs/agentops.log`

## Troubleshooting

### Common Issues

**Issue**: Import errors after update

```bash
# Solution: Reinstall dependencies
uv pip install --force-reinstall .
```

**Issue**: Validation errors in production

```bash
# Solution: Check strictness mode
echo $VALIDATION_STRICTNESS
# Set to 'warn' temporarily
export VALIDATION_STRICTNESS=warn
```

**Issue**: Cache not working

```bash
# Solution: Check cache configuration
python -c "from finwiz.cache import get_cache_manager; print(get_cache_manager().get_statistics())"

# Clear cache if needed
rm -rf cache/*
```

**Issue**: API rate limits

```bash
# Solution: Check rate limiting configuration
# Reduce max_rpm in crew configuration
# Add delays between API calls
```

**Issue**: Out of memory

```bash
# Solution: Reduce cache size
export CACHE_MAX_MEMORY_ITEMS=500
export CACHE_MAX_FILE_SIZE_MB=50

# Or switch to file-only cache
export CACHE_BACKEND=file
```

## Next Steps

Once you have FinWiz running successfully:

1. **Learn Portfolio Analysis**: See [Portfolio Analysis Tutorial](portfolio_analysis.md)
2. **Understand Deep Analysis**: Read about the [Deep Analysis Crew](../explanations/deep_analysis.md)
3. **Explore Configuration**: Check the [Configuration Guide](../how-to/setup_environment.md)
4. **Review API Reference**: Browse the [API Documentation](../reference/api/index.md)

## Getting Help

- **Documentation**: [Main Documentation](../index.md)
- **How-to Guides**: [How-to Section](../how-to/index.md)
- **Reference**: [API Reference](../reference/index.md)
- **GitHub Issues**: Report bugs or request features

---

**Version**: 2.0
**Last Updated**: 2025-10-26
