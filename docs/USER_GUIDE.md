# FinWiz User Guide

Complete guide for deploying, operating, and migrating FinWiz.

## Table of Contents

1. [Deployment](#deployment)
2. [Operations](#operations)
3. [Migration](#migration)
4. [Troubleshooting](#troubleshooting)

## Deployment

### Prerequisites

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

### Installation

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

### Environment Configuration

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

# Portfolio Configuration
PORTFOLIO_ETF_CSV=data/etf.csv
PORTFOLIO_STOCK_CSV=data/stock.csv
```

### Deployment Environments

**Development**:

```bash
# Run with debug logging
export LOG_LEVEL=DEBUG
uv run python src/finwiz/main.py
```

**Staging**:

```bash
# Run with validation warnings
export VALIDATION_STRICTNESS=warn
uv run python src/finwiz/main.py
```

**Production**:

```bash
# Run with strict validation
export VALIDATION_STRICTNESS=error
export LOG_LEVEL=INFO
uv run python src/finwiz/main.py
```

## Operations

### Daily Health Check

**Morning Checklist** (5-10 minutes):

1. **System Health**:

```bash
# Check logs for errors
tail -n 100 logs/finwiz_error.log

# Check application logs
grep -i "warning\|error" logs/finwiz.log | tail -n 20
```

2. **Performance Metrics**:

```python
from finwiz.cache import get_cache_manager

cache = get_cache_manager()
stats = cache.get_statistics()
print(f"Cache hit rate: {stats.hit_rate:.2%}")
print(f"Total requests: {stats.total_requests}")
```

3. **Feature Flags**:

```python
from finwiz.utils.feature_flags import get_feature_flags

flags = get_feature_flags()
print(f"Perplexity: {flags.is_enabled('perplexity_research')}")
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

### Maintenance

**Weekly Tasks**:

```bash
# Clear old cache files
find cache/ -type f -mtime +7 -delete

# Archive old logs
tar -czf logs/archive/logs-$(date +%Y%m%d).tar.gz logs/*.log
rm logs/*.log.1 logs/*.log.2

# Update dependencies
uv pip install --upgrade
```

**Monthly Tasks**:

```bash
# Review and update API keys
# Check for security updates
# Review error logs for patterns
# Optimize cache configuration
```

### Backup and Recovery

**What to Backup**:

- Configuration files (`.env`, `config/`)
- Portfolio data (`data/*.csv`)
- Cache directory (`cache/`)
- Output reports (`output/`)

**Backup Script**:

```bash
#!/bin/bash
BACKUP_DIR="backups/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# Backup configuration
cp .env "$BACKUP_DIR/"
cp -r config/ "$BACKUP_DIR/"

# Backup data
cp -r data/ "$BACKUP_DIR/"
cp -r cache/ "$BACKUP_DIR/"
cp -r output/ "$BACKUP_DIR/"

# Create archive
tar -czf "$BACKUP_DIR.tar.gz" "$BACKUP_DIR"
rm -rf "$BACKUP_DIR"

echo "✅ Backup complete: $BACKUP_DIR.tar.gz"
```

**Recovery**:

```bash
# Extract backup
tar -xzf backups/20250310.tar.gz

# Restore configuration
cp backups/20250310/.env .
cp -r backups/20250310/config/ .

# Restore data
cp -r backups/20250310/data/ .
```

## Migration

### Migrating to Latest Version

**Step 1: Backup Current Installation**

```bash
# Create backup
./scripts/backup.sh

# Verify backup
ls -lh backups/
```

**Step 2: Update Code**

```bash
# Pull latest changes
git pull origin main

# Update dependencies
uv pip install --upgrade
```

**Step 3: Update Configuration**

Add new environment variables to `.env`:

```bash
# Validation Configuration (NEW)
VALIDATION_STRICTNESS=warn

# Caching Configuration (NEW)
CACHE_BACKEND=hybrid
CACHE_TTL=2700
CACHE_MAX_MEMORY_ITEMS=1000
CACHE_MAX_FILE_SIZE_MB=100
CACHE_STRATEGY=ttl
CACHE_AUTO_CLEANUP=true

# Feature Flags (NEW)
FF_PERPLEXITY_RESEARCH=false
```

**Step 4: Run Migration Tests**

```bash
# Run unit tests
uv run pytest -m "not integration"

# Run integration tests
uv run pytest -m integration

# Verify installation
uv run python -c "from finwiz.validation import get_validation_manager; print('✅ Migration successful')"
```

**Step 5: Update Portfolio Data**

If you have existing portfolio CSVs, ensure they match the new format:

```csv
Name,Ticker,Currency
Apple Inc,AAPL,USD
Microsoft Corporation,MSFT,USD
```

### Breaking Changes

**Version 2.0**:

- Validation system now uses `VALIDATION_STRICTNESS` environment variable
- Cache configuration moved to environment variables
- Portfolio CSV format standardized (Name, Ticker, Currency)
- Schema validation now strict by default (`extra='forbid'`)

**Migration Path**:

1. Update `.env` with new variables
2. Update portfolio CSVs to new format
3. Test with `VALIDATION_STRICTNESS=warn` first
4. Switch to `VALIDATION_STRICTNESS=error` after testing

### New Features

**Validation System**:

```python
from finwiz.validation import get_validation_manager

manager = get_validation_manager()
result = manager.validate_crew_output(data, "stock", "analysis")

if not result.is_valid:
    for error in result.errors:
        print(f"Error: {error.message}")
```

**Caching System**:

```python
from finwiz.cache import get_cache_manager

cache = get_cache_manager()
cache.set("key", value, ttl=3600)
value = cache.get("key")
```

**Feature Flags**:

```python
from finwiz.utils.feature_flags import get_feature_flags

flags = get_feature_flags()
if flags.is_enabled("perplexity_research"):
    # Use Perplexity integration
    pass
```

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

### Getting Help

- **Documentation**: [docs/README.md](README.md)
- **Developer Guide**: [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)
- **API Reference**: [API_REFERENCE.md](API_REFERENCE.md)
- **GitHub Issues**: Report bugs or request features

### Performance Optimization

**Slow Analysis**:

1. Enable caching: `CACHE_BACKEND=hybrid`
2. Increase cache TTL: `CACHE_TTL=7200`
3. Use parallel processing for portfolios
4. Reduce logging level: `LOG_LEVEL=INFO`

**High Memory Usage**:

1. Reduce cache size: `CACHE_MAX_MEMORY_ITEMS=500`
2. Use file-only cache: `CACHE_BACKEND=file`
3. Process portfolios in smaller batches
4. Clear old cache files regularly

**API Errors**:

1. Check API keys are valid
2. Verify API rate limits
3. Enable graceful degradation
4. Check network connectivity

---

**Version**: 2.0  
**Last Updated**: 2025-03-10
