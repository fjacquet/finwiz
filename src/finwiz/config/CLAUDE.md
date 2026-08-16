# Config Module

Configuration management — environment settings, feature flags, LLM config, and performance tuning.

## Directory Structure

```
config/
├── __init__.py                      # Exports: FinWizSettings, get_settings(), etc.
├── settings.py                      # MAIN: FinWizSettings (Pydantic BaseSettings)
├── batch_prefetch_config.py         # Batch processing configuration
├── critical_fields_config.py        # Critical data field definitions by asset class
├── portfolio_analysis_config.py     # Portfolio analysis settings
├── resilience_config.py             # Retry, timeout, circuit breaker config
├── yfinance_config.py               # Yahoo Finance configuration
├── manager.py                       # Runtime config management
├── loader.py                        # Config loading utilities
│
├── features/                        # Feature flag system
│   ├── __init__.py
│   ├── flags.py                     # FeatureFlags, is_feature_enabled(), get_feature_flags()
│   ├── definitions.py               # create_default_flags() — all flag definitions
│   └── evaluators.py                # Flag evaluation logic
│
├── llm/                             # LLM model configuration
│   └── llm_config.py                # get_configured_llm(), get_llm_for_crew(), model capabilities
│
└── performance/                     # Performance tuning
    └── performance_config.py        # OptimizationMode, mode predicates, batch sizing
```

## Entry Points

| File | Class/Function | Purpose |
|------|---------------|---------|
| `settings.py` | `FinWizSettings` | Main Pydantic settings (env loading) |
| `settings.py` | `get_settings()` | Cached settings singleton |
| `features/flags.py` | `is_feature_enabled()` | Check feature flag status |
| `features/definitions.py` | `create_default_flags()` | All flag definitions |
| `llm/llm_config.py` | `get_configured_llm()` | Get LLM for general use |
| `llm/llm_config.py` | `get_llm_for_crew()` | Get LLM configured for crew execution |
| `performance/performance_config.py` | `get_performance_config_manager()` | Manager holding the active `OptimizationMode` |
| `performance/performance_config.py` | `is_maximum_speed_mode()` / `is_balanced_mode()` / `is_baseline_mode()` | Mode predicates |
| `performance/performance_config.py` | `get_batch_size()` | Batch size for the active mode |

## Environment Variables

```bash
OPENAI_API_KEY=...           # Required
SERPER_API_KEY=...           # Required
ANTHROPIC_API_KEY=...        # Optional
BATCH_PREFETCH_ENABLED=true
DEEP_ANALYSIS_BATCH_SIZE=5
MAX_RETRIES=3
FF_PORTFOLIO_AWARE_DISCOVERY=false  # Feature flags use FF_ prefix
```

## Usage

```python
from finwiz.config.settings import get_settings
from finwiz.config.features.flags import is_feature_enabled

settings = get_settings()
if is_feature_enabled("portfolio_aware_discovery"):
    # Nested model — the field is on HybridAnalysisSettings, not on FinWizSettings
    time_budget = settings.hybrid_analysis.max_batch_processing_time_seconds
```

## Related Modules

- `finwiz.core.app_initializer` — Loads config during bootstrap
- `finwiz.crews.helpers.llm_config` — Crew-specific LLM helpers
