# FinWiz Deployment Guide

This guide provides comprehensive instructions for deploying FinWiz in production, staging, and development environments with proper configuration management and monitoring.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [Deployment Process](#deployment-process)
- [Feature Flag Management](#feature-flag-management)
- [Monitoring and Logging](#monitoring-and-logging)
- [Rollback Procedures](#rollback-procedures)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Python**: 3.10 or higher
- **Package Manager**: `uv` (recommended) or `pip`
- **Operating System**: Linux, macOS, or Windows with WSL
- **Memory**: Minimum 2GB RAM, recommended 4GB+
- **Storage**: Minimum 1GB free space

### Required API Keys

The following API keys are required for FinWiz operation:

1. **OpenAI API Key** (`OPENAI_API_KEY`)
   - Required for LLM operations
   - Get from: https://platform.openai.com/api-keys

2. **Serper API Key** (`SERPER_API_KEY`)
   - Required for web search functionality
   - Get from: https://serper.dev/

3. **Firecrawl API Key** (`FIRECRAWL_API_KEY`)
   - Required for web scraping
   - Get from: https://firecrawl.dev/

4. **Alpha Vantage API Key** (`ALPHA_VANTAGE_API_KEY`)
   - Required for financial data and news
   - Get from: https://www.alphavantage.co/support/#api-key

### Optional API Keys

These API keys enable additional features:

- **Chart-img API Key** (`CHART_IMG_API_KEY`) - Chart generation
- **Twelve Data API Key** (`TWELVE_DATA_API_KEY`) - Technical indicators
- **CoinMarketCap API Key** (`COINMARKETCAP_API_KEY`) - Cryptocurrency data
- **Kraken API Key** (`KRAKEN_API_KEY`) - Crypto trading data

## Environment Configuration

### Configuration Files

FinWiz uses environment-specific configuration files located in the `config/` directory:

- `config/production.env` - Production environment settings
- `config/staging.env` - Staging environment settings  
- `config/development.env` - Development environment settings

### Setting Up Environment Variables

1. **Copy the appropriate configuration file:**
   ```bash
   cp config/production.env .env
   ```

2. **Edit the `.env` file and add your API keys:**
   ```bash
   # Required API Keys
   OPENAI_API_KEY=sk-your-openai-key-here
   SERPER_API_KEY=your-serper-key-here
   FIRECRAWL_API_KEY=your-firecrawl-key-here
   ALPHA_VANTAGE_API_KEY=your-alpha-vantage-key-here
   
   # Optional API Keys (only if features are enabled)
   CHART_IMG_API_KEY=your-chart-img-key-here
   TWELVE_DATA_API_KEY=your-twelve-data-key-here
   ```

3. **Validate configuration:**
   ```bash
   uv run python -c "
   from finwiz.utils.configuration_manager import get_configuration_manager
   config_manager = get_configuration_manager()
   config_manager.validate_startup_configuration()
   print('✅ Configuration validation successful')
   "
   ```

## Deployment Process

### Automated Deployment

Use the provided deployment script for automated deployment:

```bash
# Production deployment
./scripts/deploy.sh --env production

# Staging deployment
./scripts/deploy.sh --env staging --run-tests

# Development deployment
./scripts/deploy.sh --env development
```

### Manual Deployment Steps

1. **Install dependencies:**
   ```bash
   uv sync --no-dev
   ```

2. **Run tests:**
   ```bash
   uv run pytest tests/unit/ -v
   ```

3. **Validate configuration:**
   ```bash
   uv run python src/finwiz/main.py --validate-config
   ```

4. **Start the application:**
   ```bash
   uv run python src/finwiz/main.py
   ```

### API Server Deployment

If the rebalancing API is enabled, you can run the FastAPI server:

```bash
# Install FastAPI dependencies
uv add fastapi uvicorn

# Start API server
uv run uvicorn finwiz.api.app:app --host 0.0.0.0 --port 8000
```

## Feature Flag Management

### Portfolio Rebalancing Feature Flags

The portfolio rebalancing system uses several feature flags for gradual rollout:

#### Core Rebalancing Flags

- `FF_PORTFOLIO_REBALANCING` - Enable/disable portfolio rebalancing analysis
- `FF_REBALANCING_API` - Enable/disable REST API endpoints
- `FF_REBALANCING_MONITORING` - Enable/disable real-time monitoring

#### Rollout Configuration

- `FF_PORTFOLIO_REBALANCING_ROLLOUT` - Percentage rollout (0-100)

#### Circuit Breaker Settings

- `FF_REBALANCING_BREAKER_THRESHOLD` - Failure threshold before circuit opens
- `FF_REBALANCING_BREAKER_TIMEOUT` - Timeout before circuit retry (seconds)

### Environment-Specific Settings

#### Production (Conservative)
```bash
FF_PORTFOLIO_REBALANCING=false
FF_REBALANCING_API=false
FF_REBALANCING_MONITORING=false
FF_PORTFOLIO_REBALANCING_ROLLOUT=0.0
```

#### Staging (Gradual Rollout)
```bash
FF_PORTFOLIO_REBALANCING=true
FF_REBALANCING_API=true
FF_REBALANCING_MONITORING=false
FF_PORTFOLIO_REBALANCING_ROLLOUT=50.0
```

#### Development (Full Features)
```bash
FF_PORTFOLIO_REBALANCING=true
FF_REBALANCING_API=true
FF_REBALANCING_MONITORING=true
FF_PORTFOLIO_REBALANCING_ROLLOUT=100.0
```

### Runtime Feature Flag Updates

Feature flags can be updated at runtime through the configuration manager:

```python
from finwiz.utils.feature_flags import get_feature_flags

feature_flags = get_feature_flags()
feature_flags.update_flag("portfolio_rebalancing", enabled=True, rollout_percentage=25.0)
```

## Monitoring and Logging

### Log Configuration

Logs are written to the `logs/` directory with the following structure:

- `logs/finwiz.log` - Main application log
- `logs/finwiz_error.log` - Error-only log
- `logs/deployment.log` - Deployment script log
- `logs/rollback.log` - Rollback script log

### Log Levels by Environment

- **Production**: `INFO` level, structured logging
- **Staging**: `DEBUG` level, structured logging
- **Development**: `DEBUG` level, human-readable logging

### Performance Monitoring

The monitoring system tracks:

- Operation performance metrics
- Error rates and failure patterns
- API response times
- Feature flag usage statistics

Access monitoring data:

```python
from finwiz.utils.monitoring import get_metrics_collector

metrics = get_metrics_collector()
health_status = metrics.get_health_status()
performance_summary = metrics.get_performance_summary()
```

### Health Check Endpoints

If the API is enabled, health check endpoints are available:

- `GET /health` - Basic health check
- `GET /api/v1/rebalancing/status` - Rebalancing feature status

## Rollback Procedures

### Automated Rollback

Use the rollback script for quick recovery:

```bash
# Interactive rollback (select backup)
./scripts/rollback.sh

# Emergency rollback (latest backup)
./scripts/rollback.sh --emergency

# Rollback to specific backup
./scripts/rollback.sh --backup backups/deployment_backup_20240101_120000.tar.gz
```

### Manual Rollback Steps

1. **Stop running services:**
   ```bash
   pkill -f finwiz
   pkill -f uvicorn
   ```

2. **Restore from backup:**
   ```bash
   cd /path/to/finwiz
   tar -xzf backups/deployment_backup_YYYYMMDD_HHMMSS.tar.gz
   ```

3. **Restart services:**
   ```bash
   uv run python src/finwiz/main.py
   ```

### Backup Management

Backups are automatically created during deployment and stored in the `backups/` directory:

- Deployment backups: `deployment_backup_YYYYMMDD_HHMMSS.tar.gz`
- Pre-rollback backups: `pre_rollback_backup_YYYYMMDD_HHMMSS.tar.gz`
- Latest backup symlink: `last_deployment_backup.tar.gz`

## Troubleshooting

### Common Issues

#### Configuration Validation Errors

**Problem**: Missing or invalid API keys
```
❌ Configuration validation failed
Missing required API keys for FinWiz operation
```

**Solution**:
1. Check your `.env` file has all required API keys
2. Validate API key formats
3. Test API key connectivity

#### Feature Flag Issues

**Problem**: Features not working as expected

**Solution**:
1. Check feature flag status:
   ```python
   from finwiz.utils.feature_flags import get_feature_flags
   flags = get_feature_flags()
   print(flags.list_all_flags())
   ```

2. Verify environment-specific settings
3. Check circuit breaker status for failing features

#### Performance Issues

**Problem**: Slow response times or timeouts

**Solution**:
1. Check monitoring metrics:
   ```python
   from finwiz.utils.monitoring import get_metrics_collector
   metrics = get_metrics_collector()
   print(metrics.get_performance_summary())
   ```

2. Adjust timeout settings in configuration
3. Enable caching features
4. Check API rate limits

#### Deployment Failures

**Problem**: Deployment script fails

**Solution**:
1. Check deployment logs: `logs/deployment.log`
2. Verify system prerequisites
3. Run manual deployment steps
4. Use rollback script if needed

### Emergency Procedures

#### Complete System Failure

1. **Immediate Response:**
   ```bash
   ./scripts/rollback.sh --emergency
   ```

2. **Investigate Issues:**
   - Check logs in `logs/` directory
   - Review monitoring metrics
   - Validate configuration

3. **Gradual Recovery:**
   - Fix identified issues
   - Test in staging environment
   - Redeploy with fixes

#### Data Corruption

1. **Stop all services immediately**
2. **Restore from latest known good backup**
3. **Validate data integrity**
4. **Investigate root cause**

### Support and Escalation

For issues not covered in this guide:

1. Check application logs for detailed error messages
2. Review monitoring metrics for performance insights
3. Consult the development team with:
   - Error logs and stack traces
   - Configuration details (without API keys)
   - Steps to reproduce the issue
   - Environment information

## Security Considerations

### API Key Management

- Never commit API keys to version control
- Use environment variables or secure key management systems
- Rotate API keys regularly in production
- Monitor API key usage for anomalies

### Access Control

- Restrict access to production environments
- Use separate API keys for different environments
- Implement proper logging and audit trails
- Regular security reviews and updates

### Network Security

- Use HTTPS for all API communications
- Implement proper CORS policies
- Use firewalls and network segmentation
- Regular security scanning and updates