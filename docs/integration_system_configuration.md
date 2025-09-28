# FinWiz Integration System Configuration Guide

This document provides comprehensive guidance on configuring the FinWiz crew data integration system.

## Overview

The FinWiz integration system provides centralized data management, validation, and coordination between different analysis crews (Stock, ETF, Crypto, Discovery, Portfolio, and Report). It ensures data consistency, freshness, and proper error handling across the entire analysis pipeline.

## Configuration Files

### 1. Main Configuration File

**Location**: `config/integration.yaml`

This YAML file contains the primary configuration for the integration system:

```yaml
# Data Integration Settings
integration:
  output_dir: "output"
  freshness:
    default_max_age_hours: 24
    crew_thresholds:
      stock: 24
      etf: 48
      crypto: 12
      discovery: 72
      portfolio: 168
  validation:
    strict_validation: true
    timeout_seconds: 30
    continue_on_warnings: true
  error_handling:
    max_retries: 3
    retry_delay: 2
    graceful_degradation: true
  logging:
    level: "INFO"
    structured: true
    log_lineage: true
    log_performance: false
```

### 2. Environment Variables

**Location**: `config/integration.env.example`

Copy this file to `.env` and configure values for your environment. Key variables include:

```bash
# Core Settings
FINWIZ_INTEGRATION_OUTPUT_DIR=output
FINWIZ_INTEGRATION_DEFAULT_MAX_AGE_HOURS=24
FINWIZ_INTEGRATION_STRICT_VALIDATION=true
FINWIZ_INTEGRATION_LOG_LEVEL=INFO

# Data Freshness Thresholds
FINWIZ_STOCK_MAX_AGE_HOURS=24
FINWIZ_ETF_MAX_AGE_HOURS=48
FINWIZ_CRYPTO_MAX_AGE_HOURS=12
FINWIZ_DISCOVERY_MAX_AGE_HOURS=72
FINWIZ_PORTFOLIO_MAX_AGE_HOURS=168

# Feature Toggles
FINWIZ_APLUS_EXTRACTION_ENABLED=true
FINWIZ_SENTIMENT_CONSOLIDATION_ENABLED=true
FINWIZ_TICKER_VALIDATION_ENABLED=true
```

## Configuration Sections

### Data Freshness Configuration

Controls how long crew data remains valid before being considered stale:

- **default_max_age_hours**: Global default for all crews (24 hours)
- **crew_thresholds**: Specific thresholds per crew type
  - Stock: 24 hours (daily market changes)
  - ETF: 48 hours (less volatile than individual stocks)
  - Crypto: 12 hours (highly volatile market)
  - Discovery: 72 hours (strategic analysis, less frequent updates)
  - Portfolio: 168 hours (weekly review cycle)

### Validation Configuration

Controls data validation behavior:

- **strict_validation**: Enable strict schema validation (recommended: true)
- **timeout_seconds**: Maximum time for validation operations (30 seconds)
- **continue_on_warnings**: Continue processing on validation warnings (true)

### Error Handling Configuration

Controls error recovery and retry behavior:

- **max_retries**: Maximum retry attempts for failed operations (3)
- **retry_delay**: Delay between retry attempts in seconds (2)
- **graceful_degradation**: Continue with partial data when possible (true)

### Logging Configuration

Controls integration system logging:

- **level**: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **structured**: Enable structured logging with metadata (true)
- **log_lineage**: Log data lineage information (true)
- **log_performance**: Log performance metrics (false for production)

### A+ Opportunity Extraction

Controls extraction of A+ investment opportunities:

- **enabled**: Enable A+ opportunity extraction (true)
- **confidence_threshold**: Minimum confidence score (0.7)
- **max_opportunities**: Maximum opportunities per category
  - stocks: 10
  - etfs: 5
  - crypto: 8

### Market Sentiment Consolidation

Controls sentiment data aggregation:

- **enabled**: Enable sentiment consolidation (true)
- **min_sources**: Minimum sources for reliable sentiment (2)

### Ticker Validation

Controls ticker symbol validation:

- **enabled**: Enable ticker validation consolidation (true)
- **suggest_alternatives**: Provide alternative ticker suggestions (true)
- **max_alternatives**: Maximum alternative suggestions (3)

## Environment-Specific Configuration

### Production Environment

```bash
# Production settings prioritize stability and performance
FINWIZ_INTEGRATION_STRICT_VALIDATION=true
FINWIZ_INTEGRATION_LOG_LEVEL=INFO
FINWIZ_INTEGRATION_PERFORMANCE_MONITORING=false
FINWIZ_INTEGRATION_DEBUG_MODE=false
```

### Staging Environment

```bash
# Staging settings enable more monitoring for testing
FINWIZ_INTEGRATION_STRICT_VALIDATION=true
FINWIZ_INTEGRATION_LOG_LEVEL=DEBUG
FINWIZ_INTEGRATION_PERFORMANCE_MONITORING=true
FINWIZ_INTEGRATION_DEBUG_MODE=false
```

### Development Environment

```bash
# Development settings enable full debugging
FINWIZ_INTEGRATION_STRICT_VALIDATION=false
FINWIZ_INTEGRATION_LOG_LEVEL=DEBUG
FINWIZ_INTEGRATION_DEBUG_MODE=true
FINWIZ_INTEGRATION_PERFORMANCE_MONITORING=true
FINWIZ_INTEGRATION_USE_SAMPLE_DATA=true
```

## Configuration Loading Priority

The integration system loads configuration in the following order (later sources override earlier ones):

1. **Default values** (hardcoded in the application)
2. **YAML configuration file** (`config/integration.yaml`)
3. **Environment variables** (highest priority)

This allows for flexible deployment scenarios where base configuration is in YAML files and environment-specific overrides are provided via environment variables.

## Validation and Testing

### Configuration Validation

The system validates configuration on startup. To manually validate:

```bash
uv run python -c "
from finwiz.integration.config import load_integration_config
from pathlib import Path

config = load_integration_config(Path('config/integration.yaml'))
print('✅ Configuration loaded successfully')
print(f'Output directory: {config.output_dir}')
print(f'Strict validation: {config.strict_validation}')
"
```

### Integration System Testing

Test the integration system initialization:

```bash
uv run python -c "
from finwiz.integration.manager import CrewDataIntegrationManager
from pathlib import Path

manager = CrewDataIntegrationManager(config_path=Path('config/integration.yaml'))
print('✅ Integration system initialized successfully')
"
```

## Deployment Integration

The deployment script (`scripts/deploy.sh`) automatically:

1. Creates required integration directories
2. Validates integration system configuration
3. Sets environment-appropriate configuration values
4. Tests integration system initialization

### Deployment Command

```bash
# Deploy with integration system
./scripts/deploy.sh --env production

# Deploy with custom configuration
FINWIZ_INTEGRATION_LOG_LEVEL=DEBUG ./scripts/deploy.sh --env staging
```

## Monitoring and Troubleshooting

### Log Analysis

Integration system logs include structured metadata:

```
2024-01-15 10:30:15 - finwiz.integration - INFO - CrewDataIntegrationManager initialized {"output_dir": "output", "integration_dir": "output/integration", "config_loaded": true, "strict_validation": true}
```

### Common Issues

1. **Configuration Loading Errors**
   - Check YAML syntax in `config/integration.yaml`
   - Verify environment variable names and values
   - Ensure required directories exist

2. **Data Freshness Warnings**
   - Review crew execution schedules
   - Adjust freshness thresholds for your use case
   - Check for crew execution failures

3. **Validation Failures**
   - Review crew output schemas
   - Check for data corruption
   - Consider disabling strict validation temporarily

### Health Checks

The integration system provides health check endpoints and utilities:

```bash
# Check data availability
uv run python -c "
from finwiz.integration.data_accessor import CrewDataAccessor
from finwiz.integration.manager import CrewDataIntegrationManager

manager = CrewDataIntegrationManager()
accessor = CrewDataAccessor(manager)
report = accessor.check_data_availability()
print(f'Overall status: {report.overall_status.value}')
"
```

## Best Practices

1. **Environment Separation**: Use different configuration values for development, staging, and production
2. **Monitoring**: Enable performance monitoring in non-production environments
3. **Backup**: Regularly backup integration metadata and configuration
4. **Testing**: Validate configuration changes in staging before production deployment
5. **Documentation**: Keep configuration documentation updated with changes

## Migration Guide

When upgrading the integration system:

1. Backup current configuration files
2. Review new configuration options in the updated example files
3. Test configuration changes in development environment
4. Deploy to staging for validation
5. Deploy to production with monitoring

For specific migration instructions, see the version-specific migration guides in the `docs/` directory.