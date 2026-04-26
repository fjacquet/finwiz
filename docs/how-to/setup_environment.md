---
title: "Environment Setup"
description: "How to set up and configure your FinWiz development and production environment"
category: "how-to"
tags:
  - "setup"
  - "environment"
  - "configuration"
  - "deployment"
date: "2025-10-26"
---

# Environment Setup

This guide explains how to set up and configure your FinWiz environment for development, testing, and production use.

## Prerequisites

Before setting up FinWiz, ensure you have:

- Python 3.12 or higher
- `uv` package manager (recommended) or `pip`
- Git for version control
- At least 2GB RAM (4GB+ recommended)
- 1GB free disk space

## Installation

### 1. Clone the Repository

```bash
git clone <repo-url>
cd finwiz
```

### 2. Install Dependencies

**Using uv (recommended):**

```bash
# Install FinWiz and dependencies
uv pip install .

# For development (includes testing tools)
uv pip install -e ".[dev]"
```

**Using pip:**

```bash
# Install FinWiz and dependencies
pip install .

# For development
pip install -e ".[dev]"
```

### 3. Verify Installation

```bash
# Test basic import
uv run python -c "import finwiz; print('✅ Installation successful')"

# Check version
uv run python -c "import finwiz; print(f'FinWiz version: {finwiz.__version__}')"
```

## Environment Configuration

### 1. Create Environment File

Copy the example environment file and customize it:

```bash
cp .env.example .env
```

### 2. Required API Keys

Configure these required API keys in your `.env` file:

```bash
# Required API Keys
OPENAI_API_KEY=your_openai_key_here
SERPER_API_KEY=your_serper_key_here
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here
```

**How to get API keys:**

- **OpenAI**: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- **Serper**: [serper.dev](https://serper.dev/)
- **Alpha Vantage**: [alphavantage.co/support/#api-key](https://www.alphavantage.co/support/#api-key)

### 3. Optional API Keys

These API keys enable additional features:

```bash
# Optional API Keys
CHART_IMG_API_KEY=your_chart_img_key_here
TWELVE_DATA_API_KEY=your_twelve_data_key_here
X-CMC_PRO_API_KEY=your_coinmarketcap_key_here
PPLX_API_KEY=your_perplexity_api_key_here
```

### 4. Core Configuration

```bash
# Validation Configuration
VALIDATION_STRICTNESS=warn  # off, warn, error

# Logging Configuration
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR
STRUCTURED_LOGGING=true     # Enable structured JSON logging

# Performance Configuration
CACHE_BACKEND=hybrid        # memory, file, hybrid
CACHE_TTL=2700             # Cache TTL in seconds (45 minutes)
CACHE_MAX_MEMORY_ITEMS=1000
CACHE_MAX_FILE_SIZE_MB=100
```

### 5. Feature Flags

Enable or disable specific features:

```bash
# Feature Flags
FF_PERPLEXITY_RESEARCH=false
FF_ENHANCED_SENTIMENT=true
FF_ADVANCED_TECHNICAL=true
FF_CHART_ANALYSIS=true
PORTFOLIO_REVIEW_ENABLED=true
DEEP_PORTFOLIO_ANALYSIS=true
```

### 6. Performance Optimization

```bash
# Performance Settings
RISK_ASSESSMENT_USE_MINI=true    # Use gpt-4o-mini for faster risk assessment
USE_MINIMAL_RISK_TOOLS=true      # Use minimal tool set for risk assessor
BATCH_PREFETCH_ENABLED=true      # Enable batch data prefetching
DEEP_ANALYSIS_BATCH_SIZE=5       # Concurrent analysis batch size
```

## Environment Types

### Development Environment

For local development and testing:

```bash
# Development Configuration
LOG_LEVEL=DEBUG
VALIDATION_STRICTNESS=warn
CACHE_BACKEND=memory
FF_PERPLEXITY_RESEARCH=false
ENABLE_ALPHA_VANTAGE=false

# Run in development mode
export FINWIZ_ENV=development
uv run python src/finwiz/main.py
```

### Staging Environment

For testing before production:

```bash
# Staging Configuration
LOG_LEVEL=INFO
VALIDATION_STRICTNESS=warn
CACHE_BACKEND=hybrid
FF_PERPLEXITY_RESEARCH=false
ENABLE_ALPHA_VANTAGE=false

# Run in staging mode
export FINWIZ_ENV=staging
uv run python src/finwiz/main.py
```

### Production Environment

For production deployment:

```bash
# Production Configuration
LOG_LEVEL=INFO
VALIDATION_STRICTNESS=error
CACHE_BACKEND=hybrid
FF_PERPLEXITY_RESEARCH=true
ENABLE_ALPHA_VANTAGE=true

# Run in production mode
export FINWIZ_ENV=production
uv run python src/finwiz/main.py
```

## Directory Structure

### Create Required Directories

```bash
# Create data directories
mkdir -p data
mkdir -p cache
mkdir -p logs
mkdir -p output
mkdir -p reports

# Create portfolio data files
touch data/etf.csv
touch data/stock.csv
touch data/crypto.csv
```

### Set Permissions

```bash
# Ensure proper permissions
chmod 755 data cache logs output reports
chmod 644 data/*.csv
```

## Portfolio Data Setup

### 1. ETF Portfolio (data/etf.csv)

```csv
Name,Ticker,Currency
Vanguard Total Stock Market ETF,VTI,USD
SPDR S&P 500 ETF Trust,SPY,USD
Invesco QQQ Trust,QQQ,USD
```

### 2. Stock Portfolio (data/stock.csv)

```csv
Name,Ticker,Currency
Apple Inc,AAPL,USD
Microsoft Corporation,MSFT,USD
Alphabet Inc,GOOGL,USD
Amazon.com Inc,AMZN,USD
```

### 3. Crypto Portfolio (data/crypto.csv)

```csv
Name,Ticker,Currency
Bitcoin,BTC,USD
Ethereum,ETH,USD
```

## Configuration Validation

### 1. Test API Keys

```bash
# Test OpenAI API
uv run python -c "
import openai
import os
client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
print('✅ OpenAI API key valid')
"

# Test other APIs
uv run python scripts/validate_api_keys.py
```

### 2. Test Configuration

```bash
# Validate complete configuration
uv run python -c "
from finwiz.utils.configuration_manager import validate_startup_configuration
try:
    validate_startup_configuration()
    print('✅ All configuration valid')
except Exception as e:
    print(f'❌ Configuration error: {e}')
"
```

### 3. Test Basic Functionality

```bash
# Run a simple analysis to test everything works
uv run python src/finwiz/main.py --ticker AAPL --asset-class stock
```

## Advanced Configuration

### 1. Custom Cache Configuration

```bash
# Advanced cache settings
CACHE_STRATEGY=adaptive        # ttl, lru, lfu, adaptive
CACHE_AUTO_CLEANUP=true
CACHE_CLEANUP_INTERVAL=3600    # Cleanup every hour
CACHE_COMPRESSION=true         # Enable cache compression
```

### 2. Rate Limiting Configuration

```bash
# API rate limiting
CREW_MAX_RPM=20               # CrewAI rate limit
ALPHA_VANTAGE_RATE_LIMIT=5    # Alpha Vantage calls per minute
YAHOO_FINANCE_RATE_LIMIT=60   # Yahoo Finance calls per minute
```

### 3. Memory Management

```bash
# Memory settings
MAX_MEMORY_MB=500             # Maximum memory usage
MEMORY_WARNING_THRESHOLD=400  # Warning threshold
BATCH_PREFETCH_MIN_HOLDINGS=10 # Minimum holdings for batch mode
```

### 4. Integration Configuration

```bash
# Integration settings
FINWIZ_INTEGRATION_OUTPUT_DIR=output
FINWIZ_INTEGRATION_DEFAULT_MAX_AGE_HOURS=24
FINWIZ_INTEGRATION_STRICT_VALIDATION=true
FINWIZ_INTEGRATION_LOG_LEVEL=INFO
```

## Environment Variables Reference

### Core Settings

| Variable                | Default       | Description        |
| ----------------------- | ------------- | ------------------ |
| `FINWIZ_ENV`            | `development` | Environment type   |
| `LOG_LEVEL`             | `INFO`        | Logging level      |
| `VALIDATION_STRICTNESS` | `warn`        | Validation mode    |
| `CACHE_BACKEND`         | `hybrid`      | Cache backend type |

### API Keys

| Variable                | Required | Description              |
| ----------------------- | -------- | ------------------------ |
| `OPENAI_API_KEY`        | Yes      | OpenAI API access        |
| `SERPER_API_KEY`        | Yes      | Web search functionality |
| `ALPHA_VANTAGE_API_KEY` | Yes      | Financial data           |
| `TWELVE_DATA_API_KEY`   | No       | Technical indicators     |
| `X-CMC_PRO_API_KEY` | No       | Crypto data              |
| `PPLX_API_KEY`          | No       | Perplexity search        |

### Performance Settings

| Variable                   | Default | Description              |
| -------------------------- | ------- | ------------------------ |
| `RISK_ASSESSMENT_USE_MINI` | `true`  | Use gpt-4o-mini for risk |
| `USE_MINIMAL_RISK_TOOLS`   | `true`  | Minimal tool set         |
| `BATCH_PREFETCH_ENABLED`   | `true`  | Enable batch processing  |
| `DEEP_ANALYSIS_BATCH_SIZE` | `5`     | Concurrent batch size    |
| `RISK_FREE_RATE`           | `0.045` | US risk-free rate used in Black-Scholes for options-implied scenario probabilities |

### Feature Flags

| Variable                   | Default | Description                 |
| -------------------------- | ------- | --------------------------- |
| `FF_PERPLEXITY_RESEARCH`   | `false` | Perplexity integration      |
| `FF_ENHANCED_SENTIMENT`    | `true`  | Enhanced sentiment analysis |
| `FF_ADVANCED_TECHNICAL`    | `true`  | Advanced technical analysis |
| `PORTFOLIO_REVIEW_ENABLED` | `true`  | Portfolio review feature    |

## Troubleshooting

### Common Issues

**Issue: Import errors**

```bash
# Solution: Reinstall dependencies
uv pip install --force-reinstall .
```

**Issue: API key errors**

```bash
# Check API keys are set
env | grep -E "(OPENAI|SERPER|ALPHA_VANTAGE)_API_KEY"

# Test API connectivity
uv run python scripts/test_api_connections.py
```

**Issue: Permission errors**

```bash
# Fix directory permissions
chmod -R 755 data cache logs output reports
```

**Issue: Cache not working**

```bash
# Clear cache and restart
rm -rf cache/*
export CACHE_BACKEND=memory
```

### Validation Commands

```bash
# Check Python version
python --version

# Check uv installation
uv --version

# Validate environment
uv run python -c "
import sys
print(f'Python: {sys.version}')
import finwiz
print(f'FinWiz: {finwiz.__version__}')
"

# Test configuration
uv run python scripts/validate_environment.py
```

### Log Analysis

```bash
# Check application logs
tail -f logs/finwiz.log

# Check error logs
tail -f logs/finwiz_error.log

# Search for specific errors
grep -i "error\|warning" logs/finwiz.log | tail -20
```

## Deployment Scripts

### Development Setup Script

Create `scripts/setup_dev.sh`:

```bash
#!/bin/bash
set -e

echo "Setting up FinWiz development environment..."

# Install dependencies
uv pip install -e ".[dev]"

# Create directories
mkdir -p data cache logs output reports

# Copy environment file
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file - please add your API keys"
fi

# Create sample portfolio files
if [ ! -f data/stock.csv ]; then
    echo "Name,Ticker,Currency" > data/stock.csv
    echo "Apple Inc,AAPL,USD" >> data/stock.csv
fi

# Validate setup
uv run python -c "import finwiz; print('✅ Development setup complete')"
```

### Production Deployment Script

Create `scripts/deploy_prod.sh`:

```bash
#!/bin/bash
set -e

echo "Deploying FinWiz to production..."

# Install production dependencies
uv pip install .

# Set production environment
export FINWIZ_ENV=production
export LOG_LEVEL=INFO
export VALIDATION_STRICTNESS=error

# Validate configuration
uv run python scripts/validate_production_config.py

# Start application
uv run python src/finwiz/main.py
```

## Next Steps

After setting up your environment:

1. **Test Basic Functionality**: Run a simple analysis to verify everything works
2. **Configure Portfolio Data**: Add your actual portfolio holdings to CSV files
3. **Customize Settings**: Adjust configuration based on your needs
4. **Learn the Features**: Explore tutorials and documentation
5. **Set Up Monitoring**: Configure logging and performance monitoring

## Related Documentation

- [Getting Started Tutorial](../tutorials/getting_started.md)
- [Performance Configuration](performance_optimization.md)
- [Template Configuration](template_configuration.md)
- [API Reference](../reference/api/index.md)

---

**Version**: 2.0
**Last Updated**: 2025-10-26
