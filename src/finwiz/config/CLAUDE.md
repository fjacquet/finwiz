# Config Module

This directory contains configuration management for the FinWiz platform, including environment settings, batch processing, and resilience configuration.

## Directory Structure

```
config/
├── settings.py                 # Main settings loader (Pydantic BaseSettings)
├── batch_prefetch_config.py    # Batch processing configuration
├── critical_fields_config.py   # Critical data field definitions
├── portfolio_analysis_config.py # Portfolio analysis settings
├── resilience_config.py        # Retry, timeout, circuit breaker config
└── __init__.py
```

## Major Entry Points

| File | Class/Function | Purpose |
|------|---------------|---------|
| `settings.py` | `Settings` | Main Pydantic settings class with env loading |
| `settings.py` | `get_settings()` | Cached settings instance getter |
| `batch_prefetch_config.py` | `BatchPrefetchConfig` | Batch mode toggle and sizing |
| `resilience_config.py` | `ResilienceConfig` | Retry policies, timeouts |
| `critical_fields_config.py` | `CRITICAL_FIELDS` | Required data fields by asset class |

## Usage Pattern

```python
from finwiz.config.settings import get_settings

settings = get_settings()
api_key = settings.openai_api_key
batch_size = settings.deep_analysis_batch_size
```

## Environment Variables

Key variables loaded from `.env`:

```bash
# API Keys
OPENAI_API_KEY=...
SERPER_API_KEY=...
ANTHROPIC_API_KEY=...

# Batch Processing
BATCH_PREFETCH_ENABLED=true
DEEP_ANALYSIS_BATCH_SIZE=5
BATCH_PREFETCH_MIN_HOLDINGS=10

# Resilience
MAX_RETRIES=3
RETRY_DELAY=1.0
CIRCUIT_BREAKER_THRESHOLD=5
```

## Related Modules

- `finwiz.utils.configuration_manager` - Runtime config management
- `finwiz.utils.feature_flags` - Feature flag system
