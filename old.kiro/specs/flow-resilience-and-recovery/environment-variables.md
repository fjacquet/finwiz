# Environment Variables for Flow Resilience

## New Variables (Following FINWIZ_ Prefix Convention)

All new resilience-related environment variables follow the `FINWIZ_` prefix pattern consistent with existing FinWiz configuration.

### Retry Configuration

```bash
# Maximum number of retry attempts for failed operations
FINWIZ_MAX_RETRIES=3

# Base delay in seconds for exponential backoff
FINWIZ_RETRY_BASE_DELAY=2

# Maximum delay in seconds between retries
FINWIZ_RETRY_MAX_DELAY=60
```

### Timeout Configuration

```bash
# Timeout in seconds for single holding analysis
FINWIZ_HOLDING_TIMEOUT=300

# Global timeout in seconds for entire flow execution
FINWIZ_FLOW_TIMEOUT=7200
```

### Resume Configuration

```bash
# Automatically resume from checkpoint (true/false)
FINWIZ_AUTO_RESUME=false

# Maximum age in hours for checkpoint to be considered valid
FINWIZ_STATE_MAX_AGE_HOURS=24
```

## Renamed Variables (For Consistency)

These variables exist in `.env` but are NOT used in the codebase. We're renaming them to follow the `FINWIZ_` prefix pattern:

### Parallelization (RENAMED)

```bash
# Maximum concurrent portfolio holdings processing
# OLD: PORTFOLIO_PARALLEL_LIMIT (not used in code)
# NEW: FINWIZ_PARALLEL_LIMIT
FINWIZ_PARALLEL_LIMIT=10

# Maximum concurrent deep analysis executions
# OLD: DEEP_ANALYSIS_PARALLEL_LIMIT (not used in code)
# NEW: FINWIZ_DEEP_ANALYSIS_PARALLEL_LIMIT
FINWIZ_DEEP_ANALYSIS_PARALLEL_LIMIT=3
```

### Deep Analysis

```bash
# Enable/disable deep portfolio analysis
DEEP_PORTFOLIO_ANALYSIS=false

# Enable fast mode (reduced analysis depth)
DEEP_ANALYSIS_FAST_MODE=false
```

### Portfolio Configuration

```bash
# Cache TTL in hours for portfolio data
PORTFOLIO_CACHE_TTL_HOURS=24

# Enable alternative investment suggestions
PORTFOLIO_ENABLE_ALTERNATIVES=true
```

## Naming Convention Analysis

### Pattern: FINWIZ_ Prefix

**Used for:**
- Deployment settings (`FINWIZ_DEPLOYMENT_ENV`, `FINWIZ_PRODUCTION_MODE`)
- API configuration (`FINWIZ_API_DOCS`, `FINWIZ_CORS_ORIGINS`)
- Performance settings (`FINWIZ_CACHE_TTL`, `FINWIZ_REQUEST_TIMEOUT`)
- Monitoring (`FINWIZ_ENABLE_METRICS`, `FINWIZ_LOG_LEVEL`)
- Security (`FINWIZ_RATE_LIMIT_ENABLED`)

**✅ NEW resilience variables follow this pattern:**
- `FINWIZ_MAX_RETRIES`
- `FINWIZ_RETRY_BASE_DELAY`
- `FINWIZ_RETRY_MAX_DELAY`
- `FINWIZ_HOLDING_TIMEOUT`
- `FINWIZ_FLOW_TIMEOUT`
- `FINWIZ_AUTO_RESUME`
- `FINWIZ_STATE_MAX_AGE_HOURS`

### Pattern: Feature-Specific Prefix

**Used for:**
- Portfolio features (`PORTFOLIO_PARALLEL_LIMIT`, `PORTFOLIO_CACHE_TTL_HOURS`)
- Deep analysis (`DEEP_PORTFOLIO_ANALYSIS`, `DEEP_ANALYSIS_FAST_MODE`)
- Feature flags (`FF_PORTFOLIO_REBALANCING`, `FF_ENHANCED_SENTIMENT`)
- Cache settings (`CACHE_BACKEND`, `CACHE_TTL`)

**✅ Existing variables reused as-is:**
- `PORTFOLIO_PARALLEL_LIMIT` (backward compatibility)
- `DEEP_ANALYSIS_PARALLEL_LIMIT` (backward compatibility)

## Complete .env Example

```bash
# ============================================================================
# Flow Resilience Configuration (NEW)
# ============================================================================

# Retry Configuration
FINWIZ_MAX_RETRIES=3
FINWIZ_RETRY_BASE_DELAY=2
FINWIZ_RETRY_MAX_DELAY=60

# Timeout Configuration
FINWIZ_HOLDING_TIMEOUT=300
FINWIZ_FLOW_TIMEOUT=7200

# Resume Configuration
FINWIZ_AUTO_RESUME=false
FINWIZ_STATE_MAX_AGE_HOURS=24

# ============================================================================
# Existing Configuration (UNCHANGED)
# ============================================================================

# Deep Portfolio Analysis
DEEP_PORTFOLIO_ANALYSIS=false
DEEP_ANALYSIS_FAST_MODE=false

# Portfolio Configuration
PORTFOLIO_CACHE_TTL_HOURS=24
PORTFOLIO_ENABLE_ALTERNATIVES=true
PORTFOLIO_PARALLEL_LIMIT=10
DEEP_ANALYSIS_PARALLEL_LIMIT=3
```

## Validation Rules

The `ResilienceConfig` class validates:

1. **holding_timeout < flow_timeout** - Per-holding timeout must be less than global timeout
2. **max_retries >= 0** - Cannot have negative retries
3. **state_max_age_hours >= 1** - Checkpoint must be valid for at least 1 hour
4. **retry_base_delay > 0** - Base delay must be positive
5. **retry_max_delay > retry_base_delay** - Max delay must exceed base delay

## Usage in Code

```python
from finwiz.config.resilience_config import get_resilience_config

# Load and validate configuration
config = get_resilience_config()

# Access values
print(f"Max retries: {config.max_retries}")
print(f"Holding timeout: {config.holding_timeout}s")
print(f"Auto resume: {config.auto_resume}")
```

## Migration Notes

**No breaking changes:**
- All new variables have sensible defaults
- Existing variables unchanged
- Backward compatible with current deployments

**Recommended for production:**
```bash
FINWIZ_MAX_RETRIES=3
FINWIZ_HOLDING_TIMEOUT=300
FINWIZ_FLOW_TIMEOUT=7200
FINWIZ_AUTO_RESUME=true  # Enable resume for long-running flows
```

---

**Version**: 1.0  
**Created**: 2025-01-11  
**Purpose**: Document environment variables for flow resilience configuration
