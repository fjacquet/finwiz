# Environment Variable Naming Conventions

## Summary of Naming Patterns

### 1. FINWIZ_ Prefix (Application Configuration)

**Purpose:** FinWiz-wide application settings

**Examples:**
- `FINWIZ_DEPLOYMENT_ENV` - Deployment environment
- `FINWIZ_PRODUCTION_MODE` - Production mode flag
- `FINWIZ_LOG_LEVEL` - Logging level
- `FINWIZ_API_DOCS` - API documentation enabled
- `FINWIZ_CORS_ORIGINS` - CORS origins
- `FINWIZ_CACHE_TTL` - Cache TTL
- `FINWIZ_REQUEST_TIMEOUT` - Request timeout
- `FINWIZ_MAX_CONCURRENT_REQUESTS` - Max concurrent requests
- `FINWIZ_ENABLE_METRICS` - Metrics enabled
- `FINWIZ_RATE_LIMIT_ENABLED` - Rate limiting enabled

**✅ NEW Resilience Variables (Following This Pattern):**
- `FINWIZ_MAX_RETRIES`
- `FINWIZ_RETRY_BASE_DELAY`
- `FINWIZ_RETRY_MAX_DELAY`
- `FINWIZ_HOLDING_TIMEOUT`
- `FINWIZ_FLOW_TIMEOUT`
- `FINWIZ_AUTO_RESUME`
- `FINWIZ_STATE_MAX_AGE_HOURS`
- `FINWIZ_PARALLEL_LIMIT` (renamed from `PORTFOLIO_PARALLEL_LIMIT`)
- `FINWIZ_DEEP_ANALYSIS_PARALLEL_LIMIT` (renamed from `DEEP_ANALYSIS_PARALLEL_LIMIT`)

---

### 2. FF_ Prefix (Feature Flags)

**Purpose:** Feature enablement/disablement with rollout control

**Managed by:** `src/finwiz/utils/feature_flags.py` (`FeatureFlagManager`)

**Examples:**
- `FF_ENHANCED_SENTIMENT` - Enhanced sentiment analysis
- `FF_ADVANCED_TECHNICAL` - Advanced technical analysis
- `FF_CHART_ANALYSIS` - Chart analysis feature
- `FF_TWELVE_DATA` - Twelve Data integration
- `FF_STRICT_VALIDATION` - Strict validation
- `FF_ASYNC_EXECUTION` - Async execution
- `FF_INTELLIGENT_CACHING` - Intelligent caching
- `FF_PORTFOLIO_REVIEW` - Portfolio review
- `FF_QUANTITATIVE_ANALYSIS` - Quantitative analysis
- `FF_PORTFOLIO_REBALANCING` - Portfolio rebalancing
- `FF_REBALANCING_MONITORING` - Rebalancing monitoring

**Additional FF_ Variables:**
- `FF_*_ROLLOUT` - Rollout percentage (e.g., `FF_ENHANCED_SENTIMENT_ROLLOUT`)
- `FF_*_BREAKER_THRESHOLD` - Circuit breaker threshold
- `FF_*_BREAKER_TIMEOUT` - Circuit breaker timeout

**❌ DO NOT RENAME** - These are feature flags, not configuration

---

### 3. Feature-Specific Prefixes (Domain Configuration)

**Purpose:** Configuration specific to a feature domain

#### PORTFOLIO_ Prefix

**Examples:**
- `PORTFOLIO_CACHE_TTL_HOURS` - Portfolio cache TTL
- `PORTFOLIO_ENABLE_ALTERNATIVES` - Enable alternatives

**✅ RENAMED to FINWIZ_:**
- ~~`PORTFOLIO_PARALLEL_LIMIT`~~ → `FINWIZ_PARALLEL_LIMIT`

#### DEEP_ Prefix

**Examples:**
- `DEEP_PORTFOLIO_ANALYSIS` - Enable deep analysis
- `DEEP_ANALYSIS_FAST_MODE` - Fast mode

**✅ RENAMED to FINWIZ_:**
- ~~`DEEP_ANALYSIS_PARALLEL_LIMIT`~~ → `FINWIZ_DEEP_ANALYSIS_PARALLEL_LIMIT`

#### CACHE_ Prefix

**Examples:**
- `CACHE_BACKEND` - Cache backend type
- `CACHE_TTL` - Cache TTL
- `CACHE_MAX_MEMORY_ITEMS` - Max memory items
- `CACHE_DIRECTORY` - Cache directory
- `CACHE_STRATEGY` - Cache strategy

**❌ DO NOT RENAME** - Cache-specific configuration

---

### 4. Service API Keys (No Prefix)

**Purpose:** Third-party service API keys

**Examples:**
- `OPENAI_API_KEY`
- `SERPER_API_KEY`
- `FIRECRAWL_API_KEY`
- `ALPHA_VANTAGE_API_KEY`
- `TWELVE_DATA_API_KEY`
- `COINMARKETCAP_API_KEY`

**❌ DO NOT RENAME** - Standard API key naming

---

### 5. Other Prefixes (Keep As-Is)

#### INVESTMENT_ Prefix
- `INVESTMENT_DISCOVERY_ENABLED`

#### TARGET Prefix
- `TARGETLANG` - Target language

#### CrewAI/LangChain Prefixes
- `CREWAI_DISABLE_TELEMETRY`
- `CREWAI_TOOLS_VERBOSE`
- `LANGCHAIN_VERBOSE`

**❌ DO NOT RENAME** - External library configuration

---

## Renaming Summary

### Variables Being Renamed

| Old Name | New Name | Reason | Impact |
|----------|----------|--------|--------|
| `PORTFOLIO_PARALLEL_LIMIT` | `FINWIZ_PARALLEL_LIMIT` | Consistency with FINWIZ_ pattern | ✅ Safe - Not used in code |
| `DEEP_ANALYSIS_PARALLEL_LIMIT` | `FINWIZ_DEEP_ANALYSIS_PARALLEL_LIMIT` | Consistency with FINWIZ_ pattern | ✅ Safe - Not used in code |

### Variables NOT Being Renamed

| Variable | Prefix | Reason |
|----------|--------|--------|
| `FF_*` | Feature Flags | Different concept (feature enablement) |
| `CACHE_*` | Cache Config | Domain-specific configuration |
| `DEEP_PORTFOLIO_ANALYSIS` | Feature Config | Actively used in code |
| `PORTFOLIO_ENABLE_ALTERNATIVES` | Feature Config | Actively used in code |
| `PORTFOLIO_CACHE_TTL_HOURS` | Feature Config | Actively used in code |
| API Keys | None | Standard naming convention |

---

## Implementation Plan

### Phase 1: Add New Variables (No Breaking Changes)

Add new `FINWIZ_` prefixed variables with defaults:

```python
# New resilience configuration
FINWIZ_MAX_RETRIES = int(os.getenv("FINWIZ_MAX_RETRIES", "3"))
FINWIZ_RETRY_BASE_DELAY = float(os.getenv("FINWIZ_RETRY_BASE_DELAY", "2"))
FINWIZ_RETRY_MAX_DELAY = float(os.getenv("FINWIZ_RETRY_MAX_DELAY", "60"))
FINWIZ_HOLDING_TIMEOUT = int(os.getenv("FINWIZ_HOLDING_TIMEOUT", "300"))
FINWIZ_FLOW_TIMEOUT = int(os.getenv("FINWIZ_FLOW_TIMEOUT", "7200"))
FINWIZ_AUTO_RESUME = os.getenv("FINWIZ_AUTO_RESUME", "false").lower() == "true"
FINWIZ_STATE_MAX_AGE_HOURS = int(os.getenv("FINWIZ_STATE_MAX_AGE_HOURS", "24"))

# Renamed parallelization (with fallback to old names)
FINWIZ_PARALLEL_LIMIT = int(os.getenv("FINWIZ_PARALLEL_LIMIT", 
                                       os.getenv("PORTFOLIO_PARALLEL_LIMIT", "10")))
FINWIZ_DEEP_ANALYSIS_PARALLEL_LIMIT = int(os.getenv("FINWIZ_DEEP_ANALYSIS_PARALLEL_LIMIT",
                                                      os.getenv("DEEP_ANALYSIS_PARALLEL_LIMIT", "3")))
```

### Phase 2: Update .env.example

```bash
# ============================================================================
# Flow Resilience Configuration
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

# Parallelization Configuration (RENAMED for consistency)
FINWIZ_PARALLEL_LIMIT=10
FINWIZ_DEEP_ANALYSIS_PARALLEL_LIMIT=3
```

### Phase 3: Deprecation Notice (Optional)

Add deprecation warnings for old variable names:

```python
# Check for deprecated variables
if os.getenv("PORTFOLIO_PARALLEL_LIMIT"):
    logger.warning(
        "PORTFOLIO_PARALLEL_LIMIT is deprecated. "
        "Use FINWIZ_PARALLEL_LIMIT instead."
    )

if os.getenv("DEEP_ANALYSIS_PARALLEL_LIMIT"):
    logger.warning(
        "DEEP_ANALYSIS_PARALLEL_LIMIT is deprecated. "
        "Use FINWIZ_DEEP_ANALYSIS_PARALLEL_LIMIT instead."
    )
```

---

## Decision Matrix

| Variable Type | Prefix | Rename? | Reason |
|--------------|--------|---------|--------|
| App-wide config | `FINWIZ_` | ✅ Yes | Consistency |
| Feature flags | `FF_` | ❌ No | Different concept |
| Cache config | `CACHE_` | ❌ No | Domain-specific |
| Feature config | `PORTFOLIO_`, `DEEP_` | ⚠️ Case-by-case | Check usage |
| API keys | None | ❌ No | Standard convention |

---

## Final Naming Convention

**✅ Use `FINWIZ_` prefix for:**
- Application-wide settings
- Performance configuration
- Resilience configuration
- Monitoring configuration
- Security configuration

**✅ Use `FF_` prefix for:**
- Feature flags (enable/disable features)
- Rollout percentages
- Circuit breaker settings

**✅ Use domain prefixes for:**
- Domain-specific configuration that's actively used
- Examples: `CACHE_*`, `DEEP_PORTFOLIO_ANALYSIS`

**✅ No prefix for:**
- Third-party API keys
- External library configuration

---

**Version**: 1.0  
**Created**: 2025-01-11  
**Purpose**: Document and standardize environment variable naming conventions
