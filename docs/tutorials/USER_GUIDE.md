# FinWiz User Guide

Complete guide for deploying, operating, and migrating FinWiz.

## Table of Contents

1. [Deployment](#deployment)
2. [Operations](#operations)
3. [Deep Analysis Crew](#deep-analysis-crew)
4. [Migration](#migration)
5. [Troubleshooting](#troubleshooting)

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
- `ALPHA_VANTAGE_API_KEY` - Financial data ([Get key](https://www.alphavantage.co/support/#api-key))

**Optional API Keys**:

- `CHART_IMG_API_KEY` - Chart generation
- `TWELVE_DATA_API_KEY` - Technical indicators
- `X-CMC_PRO_API_KEY` - Crypto data
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

1. **Performance Metrics**:

```python
from finwiz.cache import get_cache_manager

cache = get_cache_manager()
stats = cache.get_statistics()
print(f"Cache hit rate: {stats.hit_rate:.2%}")
print(f"Total requests: {stats.total_requests}")
```

1. **Feature Flags**:

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

## Deep Analysis Crew

### Overview

The `DeepAnalysisCrew` is a unified crew for comprehensive single-ticker analysis across all asset classes (stocks, ETFs, cryptocurrencies). It provides detailed grading (A+ to F) and comprehensive analysis for portfolio holdings evaluation.

**Key Features:**

- Single crew for all asset classes (no duplication)
- Dynamic tool routing based on asset_class parameter
- Fresh data for real money decisions
- Comprehensive analysis with grading
- API efficiency through smart batching

### When to Use DeepAnalysisCrew

**Use DeepAnalysisCrew for:**

- ✅ Analyzing specific tickers you already own
- ✅ Evaluating individual portfolio holdings
- ✅ Making keep/sell decisions
- ✅ Getting detailed grades (A+ to F)

**Use Discovery Crews for:**

- ✅ Finding NEW investment opportunities
- ✅ Screening for "top 10" candidates
- ✅ Discovering assets you don't own
- ✅ Comparative analysis across multiple assets

### Basic Usage

**Analyze a Stock:**

```python
from finwiz.crews.deep_analysis.deep_analysis import DeepAnalysisCrew

# Initialize crew
crew = DeepAnalysisCrew()

# Execute analysis
result = crew.crew().kickoff(inputs={
    "ticker": "AAPL",
    "asset_class": "stock"
})

# Access results
print(f"Grade: {result.grade}")
print(f"Composite Score: {result.composite_score}")
```

**Analyze an ETF:**

```python
result = crew.crew().kickoff(inputs={
    "ticker": "VOO",
    "asset_class": "etf"
})
```

**Analyze Crypto:**

```python
result = crew.crew().kickoff(inputs={
    "ticker": "BTC",
    "asset_class": "crypto"
})
```

### Configuration

**Enable Deep Portfolio Analysis:**

```bash
# In .env file
DEEP_PORTFOLIO_ANALYSIS=true
PORTFOLIO_CACHE_TTL_HOURS=24
```

**Performance Settings:**

```bash
# Crew execution settings
CREW_MAX_RPM=20              # Rate limiting
CREW_TIMEOUT_MINUTES=5       # Execution timeout
```

### Output

The crew returns a `DeepAnalysisResult` with:

- **Scores**: fundamental_score, technical_score, risk_score, composite_score (0.0-1.0)
- **Grade**: A+ to F based on composite_score
- **Metadata**: ticker, asset_class, analyzed_at, data_freshness

**Grade Mapping:**

- A+ ≥ 0.95 (Exceptional)
- A ≥ 0.85 (Excellent)
- B ≥ 0.75 (Good)
- C ≥ 0.65 (Fair)
- D ≥ 0.55 (Poor)
- F < 0.55 (Failing)

### Integration with Portfolio Analysis

The DeepAnalysisCrew integrates into the 6-phase flow:

1. **Phase 1: Validation** - Check data systems
2. **Phase 2: Portfolio Analysis** - Analyze what you have
3. **Phase 3: Deep Analysis & Update** ⭐ DeepAnalysisCrew runs here
   - Grade each holding
   - Match alternatives for underperformers
   - Update portfolio review (ONCE)
4. **Phase 4: Discovery** - Find A+ opportunities
5. **Phase 5: Rebalancing** - Optimize allocations
6. **Phase 6: Reporting** - Present recommendations

### Performance

**Expected Execution Time:**

- Target: < 5 minutes per ticker
- Typical: 2-3 minutes for complete analysis

**API Efficiency:**

- Smart batching of indicator requests
- Context sharing between tasks
- Parallel execution where possible
- Fresh data validation

### Performance Optimizations

The DeepAnalysisCrew includes two performance optimizations that can be configured via environment variables:

**Phase 1: gpt-4o-mini for Risk Assessment**

```bash
# Enable gpt-4o-mini for risk assessment (default: true)
RISK_ASSESSMENT_USE_MINI=true

# Disable to use default LLM (GPT-4)
RISK_ASSESSMENT_USE_MINI=false
```

**Benefits:**

- Faster execution (gpt-4o-mini is optimized for speed)
- Lower cost per analysis
- Maintains accuracy for straightforward risk calculations

**When to disable:**

- Complex risk scenarios requiring advanced reasoning
- Regulatory compliance requiring specific model versions
- Comparative analysis with baseline results

**Phase 2: Minimal Tool Set for Risk Assessor**

```bash
# Enable minimal tool set for risk assessor (default: true)
USE_MINIMAL_RISK_TOOLS=true

# Disable to use full tool set
USE_MINIMAL_RISK_TOOLS=false
```

**Benefits:**

- Reduced tool initialization overhead
- Faster agent startup time
- Focused on essential risk calculation tools only

**Minimal Tool Set Includes:**

- `QuantitativeAnalysisTool` (core risk metrics)
- `TickerValidationTool` (ticker validation)
- Asset-specific tool (`EnhancedSECAnalysisTool`, `EnhancedETFAnalysisTool`, or `EnhancedCryptoAnalysisTool`)

**When to disable:**

- Need full tool set for comprehensive analysis
- Debugging tool-related issues
- Comparative analysis with baseline results

**Combined Optimization:**

For maximum performance, enable both optimizations (default configuration):

```bash
RISK_ASSESSMENT_USE_MINI=true
USE_MINIMAL_RISK_TOOLS=true
```

**Performance Impact:**

- Faster execution: 20-30% reduction in analysis time
- Lower cost: Reduced LLM API costs
- Maintained accuracy: Risk scores remain consistent

### Troubleshooting

**Issue: Crew hangs for hours**

Solution: Check task descriptions don't contain "top 10" language. DeepAnalysisCrew is for single-ticker analysis only.

**Issue: Stale data in analysis**

Solution: Check data freshness timestamps in result. Adjust cache TTL if needed.

**Issue: API failures**

Solution: Check API keys are valid. Enable graceful degradation for fallback behavior.

For detailed documentation, see [docs/DEEP_ANALYSIS_CREW.md](DEEP_ANALYSIS_CREW.md).

## Flow Resilience and Recovery

### Overview

FinWiz includes comprehensive resilience and recovery capabilities to ensure reliable execution of long-running portfolio analysis workflows. The system automatically handles failures, saves progress, and can resume interrupted analyses without losing work or wasting API quota.

**Key Features:**

- Automatic retry with exponential backoff for transient failures
- Progress checkpointing using CrewAI native persistence
- Resume capability for interrupted flows
- Timeout management to prevent indefinite hangs
- Real-time progress tracking
- Error classification with remediation suggestions
- Integration with monitoring and alerting

### When to Use Resilience Features

**Resilience features are automatically enabled for:**

- ✅ Deep portfolio analysis (analyzing 10+ holdings)
- ✅ Long-running workflows (>30 minutes)
- ✅ Operations with external API dependencies
- ✅ Production environments with reliability requirements

**Benefits:**

- **Reliability**: Automatic retry of failed operations (up to 3 attempts)
- **Progress Preservation**: Never lose work due to interruptions
- **Cost Efficiency**: Resume from last checkpoint without re-analyzing
- **Visibility**: Real-time progress tracking and error reporting
- **Graceful Degradation**: Continue with partial results on failures

### Environment Variables

Configure resilience behavior through environment variables:

```bash
# Retry Configuration
FINWIZ_MAX_RETRIES=3                    # Maximum retry attempts (default: 3)
FINWIZ_RETRY_BASE_DELAY=2               # Base delay in seconds (default: 2)
FINWIZ_RETRY_MAX_DELAY=60               # Maximum delay in seconds (default: 60)

# Timeout Configuration
FINWIZ_HOLDING_TIMEOUT=300              # Per-holding timeout in seconds (default: 300 = 5 min)
FINWIZ_FLOW_TIMEOUT=7200                # Global flow timeout in seconds (default: 7200 = 2 hours)

# Resume Configuration
FINWIZ_AUTO_RESUME=false                # Automatically resume on restart (default: false)
FINWIZ_STATE_MAX_AGE_HOURS=24           # Maximum age of resumable state (default: 24 hours)

# Parallelization Configuration
FINWIZ_PARALLEL_LIMIT=10                # General parallel operations limit (default: 10)
FINWIZ_DEEP_ANALYSIS_PARALLEL_LIMIT=3   # Deep analysis parallel limit (default: 3)
```

### Automatic Retry

The system automatically retries failed operations with intelligent exponential backoff:

**Retryable Errors:**

- Network connection failures
- API timeouts
- Rate limit errors (429 responses)
- Temporary server errors (5xx responses)

**Non-Retryable Errors:**

- Invalid ticker symbols
- Authentication failures
- Validation errors
- Malformed requests

**Retry Behavior:**

```
Attempt 1: Immediate execution
Attempt 2: Wait 2 seconds (base delay)
Attempt 3: Wait 4 seconds (exponential backoff)
Final: Mark as failed after 3 attempts
```

**Example Log Output:**

```
INFO: Analyzing AAPL (attempt 1/3)
WARNING: Network error for AAPL, retrying in 2 seconds...
INFO: Analyzing AAPL (attempt 2/3)
INFO: Successfully analyzed AAPL on attempt 2
```

### Progress Checkpointing

The system uses CrewAI's native `@persist()` decorator to automatically save progress after each flow method:

**What Gets Saved:**

- Portfolio analysis results
- Deep analysis results for each holding
- Alternative recommendations
- Error tracking and retry counts
- Progress metrics (holdings processed, remaining)
- Timing information (start time, estimated completion)

**Checkpoint Location:**

- Stored in `.finwiz/state/{flow_uuid}/` directory
- Each flow execution has a unique UUID
- State files are JSON format for easy inspection

**Automatic Checkpointing:**

```python
# Checkpoints are saved automatically after each method
@persist()  # Class-level persistence
class FinwizFlow(Flow[FinwizState]):
    @start()
    def validate_data_integration(self):
        # State saved automatically after this method
        pass

    @listen("validate_data_integration")
    def check_portfolio(self):
        # State saved automatically after this method
        pass
```

### Resume Capability

If a flow is interrupted (crash, network failure, manual stop), you can resume from the last checkpoint:

**Manual Resume:**

```python
from finwiz.flows.flow_orchestrator import FinwizFlow

# Create flow with existing UUID to resume
flow = FinwizFlow()
# CrewAI automatically loads persisted state if available
result = flow.kickoff()
```

**Automatic Resume (Optional):**

```bash
# Enable automatic resume on restart
export FINWIZ_AUTO_RESUME=true

# Run flow - will automatically resume if state exists
uv run python src/finwiz/main.py
```

**Resume Behavior:**

- Checks for persisted state less than 24 hours old (configurable)
- Skips already-completed holdings
- Continues from last successful checkpoint
- Merges new results with persisted results
- Logs which holdings are being skipped vs analyzed

**Example Log Output:**

```
INFO: Found persisted state from 2025-03-10 14:30:00 (2 hours ago)
INFO: Resume: Portfolio already analyzed, skipping
INFO: Resume: 45/66 holdings already analyzed
INFO: Continuing with remaining 21 holdings
INFO: Progress: 46/66 (69.7%) - Success: 44, Failed: 2
```

### Timeout Management

The system enforces timeouts to prevent indefinite hangs:

**Per-Holding Timeout:**

- Default: 5 minutes per holding
- Configurable via `FINWIZ_HOLDING_TIMEOUT`
- Applies to each individual holding analysis
- Graceful cancellation before forced termination

**Global Flow Timeout:**

- Default: 2 hours for entire flow
- Configurable via `FINWIZ_FLOW_TIMEOUT`
- Applies to complete portfolio analysis
- Saves checkpoint before termination

**Timeout Behavior:**

```
Holding timeout (5 min):
  - Attempt graceful cancellation
  - Mark holding as failed
  - Continue with next holding
  - Log timeout with context

Global timeout (2 hours):
  - Save final checkpoint
  - Generate partial results report
  - Log completion summary
  - Exit gracefully
```

**Example Log Output:**

```
WARNING: Timeout: Deep analysis for TSLA exceeded 300s timeout
INFO: Marked TSLA as failed, continuing with remaining holdings
INFO: Progress: 50/66 (75.8%) - Success: 48, Failed: 2, Timeout: 1
```

### Progress Tracking

Real-time progress tracking provides visibility into long-running analyses:

**Tracked Metrics:**

- Total holdings count
- Holdings processed / remaining
- Progress percentage
- Success / failure / timeout counts
- Estimated time remaining
- Current ticker being analyzed
- Retry counts per holding

**Progress Updates:**

```
INFO: Starting deep analysis for 66 holdings
INFO: Progress: 10/66 (15.2%) - Success: 9, Failed: 1 - ETA: 45 minutes
INFO: Progress: 20/66 (30.3%) - Success: 19, Failed: 1 - ETA: 35 minutes
INFO: Progress: 30/66 (45.5%) - Success: 28, Failed: 2 - ETA: 25 minutes
INFO: Progress: 40/66 (60.6%) - Success: 37, Failed: 3 - ETA: 15 minutes
INFO: Progress: 50/66 (75.8%) - Success: 47, Failed: 3 - ETA: 8 minutes
INFO: Progress: 60/66 (90.9%) - Success: 57, Failed: 3 - ETA: 3 minutes
INFO: Completed: 66/66 (100.0%) - Success: 63, Failed: 3 - Total time: 52 minutes
```

**Accessing Progress Programmatically:**

```python
# During flow execution
flow = FinwizFlow()
# ... flow is running ...

# Access current state
print(f"Progress: {flow.state.holdings_processed}/{flow.state.total_holdings}")
print(f"Percentage: {flow.state.progress_percentage:.1f}%")
print(f"Failed: {len(flow.state.failed_holdings)}")
print(f"Current: {flow.state.current_ticker}")
```

### Error Classification and Remediation

The system classifies errors and provides actionable remediation suggestions:

**Error Types:**

- **Network**: Connection failures, DNS errors
- **Timeout**: Operation exceeded time limit
- **Rate Limit**: API quota exceeded
- **Authentication**: Invalid or expired API keys
- **Validation**: Invalid data or ticker symbols
- **Unknown**: Unclassified errors

**Remediation Suggestions:**

| Error Type     | Suggestion                                |
| -------------- | ----------------------------------------- |
| Network        | Check network connectivity and API status |
| Timeout        | Increase timeout or check API performance |
| Rate Limit     | Reduce parallelism or increase delays     |
| Authentication | Check API keys in environment variables   |
| Validation     | Check ticker symbols and input data       |
| Unknown        | Review error details and logs             |

**Error Report Example:**

```
ERROR: Failed to analyze 3 holdings after all retries:

1. INVALID (validation error)
   - Error: Invalid ticker symbol
   - Remediation: Check ticker symbols and input data
   - Attempts: 1 (non-retryable)

2. AAPL (network error)
   - Error: Connection timeout
   - Remediation: Check network connectivity and API status
   - Attempts: 3 (retries exhausted)

3. TSLA (timeout error)
   - Error: Analysis exceeded 300s timeout
   - Remediation: Increase timeout or check API performance
   - Attempts: 2 (timeout on retry)
```

### Monitoring and Metrics

The system exports comprehensive metrics for monitoring:

**Metrics Exported:**

- Flow UUID and execution timestamp
- Total holdings and processing counts
- Success rate and failure breakdown
- Retry counts and timeout counts
- Execution time and performance metrics
- Error classification and remediation

**Metrics Location:**

- Exported to `.finwiz/metrics/{flow_uuid}.json`
- JSON format for easy integration with dashboards
- Includes all resilience-related metrics

**Example Metrics File:**

```json
{
  "flow_uuid": "abc123-def456-ghi789",
  "timestamp": "2025-03-10T15:30:00Z",
  "total_holdings": 66,
  "holdings_processed": 66,
  "success_count": 63,
  "failure_count": 3,
  "timeout_count": 1,
  "success_rate": 0.9545,
  "total_retries": 8,
  "execution_time_seconds": 3120,
  "average_time_per_holding": 47.3,
  "error_breakdown": {
    "network": 2,
    "timeout": 1,
    "validation": 0
  }
}
```

### Integration with Monitoring

The system integrates with FinWiz's existing monitoring infrastructure:

**AlertManager Integration:**

- Critical alerts for high failure rates (>50%)
- Includes failed holdings list in metadata
- Configurable alert thresholds
- Multi-channel notifications (email, SMS)

**Example Alert:**

```
CRITICAL: High Failure Rate in Deep Analysis
- Failed: 35/66 holdings (53%)
- Flow UUID: abc123-def456-ghi789
- Timestamp: 2025-03-10 15:30:00
- Failed Holdings: [AAPL, MSFT, GOOGL, ...]
- Suggested Action: Investigate systemic issues (API keys, network, rate limits)
```

### Troubleshooting

**Issue: Flow hangs indefinitely**

Solution: Check timeout configuration and increase if needed:

```bash
export FINWIZ_HOLDING_TIMEOUT=600  # 10 minutes
export FINWIZ_FLOW_TIMEOUT=14400   # 4 hours
```

**Issue: Too many retries causing delays**

Solution: Reduce retry attempts or increase delays:

```bash
export FINWIZ_MAX_RETRIES=2
export FINWIZ_RETRY_BASE_DELAY=5
```

**Issue: Cannot resume from checkpoint**

Solution: Check state age and validity:

```bash
# Check state files
ls -lh .finwiz/state/

# Increase max age if needed
export FINWIZ_STATE_MAX_AGE_HOURS=48

# Or start fresh
rm -rf .finwiz/state/
```

**Issue: High failure rate**

Solution: Check error classification and remediation:

```bash
# Review error logs
grep "ERROR" logs/finwiz.log | tail -n 50

# Check metrics file
cat .finwiz/metrics/latest.json | jq '.error_breakdown'

# Common fixes:
# - Verify API keys are valid
# - Check network connectivity
# - Reduce parallelism if rate limited
# - Increase timeouts if operations are slow
```

**Issue: Progress not updating**

Solution: Check logging configuration:

```bash
# Enable verbose logging
export LOG_LEVEL=INFO

# Check progress in logs
tail -f logs/finwiz.log | grep "Progress:"
```

### Best Practices

**1. Configure Appropriate Timeouts:**

- Set holding timeout based on typical analysis time
- Set flow timeout based on portfolio size
- Allow buffer for retries and delays

**2. Monitor Failure Rates:**

- Review metrics after each run
- Investigate if failure rate >10%
- Adjust configuration based on patterns

**3. Use Resume Capability:**

- Enable for large portfolios (>50 holdings)
- Useful for development and testing
- Saves time and API quota

**4. Tune Parallelization:**

- Balance speed vs reliability
- Reduce if hitting rate limits
- Increase for faster execution

**5. Review Error Reports:**

- Check remediation suggestions
- Fix systemic issues (API keys, network)
- Update configuration as needed

### Performance Impact

**Overhead for Successful Execution:**

- Checkpointing: ~10-50ms per method
- Progress tracking: ~1ms per update
- Error handling: ~1-5ms per operation
- **Total overhead: <100ms** (negligible)

**Overhead for Failed Execution:**

- Retry with backoff: 2-60s per retry
- 3 retries: 6-180s total delay
- Timeout enforcement: 0s (prevents indefinite hangs)
- **Total overhead: 6-180s per failed holding**

**Benefits:**

- ✅ Prevents complete workflow failures
- ✅ Saves API quota on interruptions
- ✅ Provides visibility into long operations
- ✅ Enables graceful degradation
- ✅ Improves overall reliability

### Advanced Configuration

**Custom Retry Strategy:**

```python
from finwiz.config.resilience_config import ResilienceConfig

config = ResilienceConfig(
    max_retries=5,              # More aggressive retries
    retry_base_delay=1,         # Faster initial retry
    retry_max_delay=30,         # Lower max delay
    holding_timeout=600,        # 10 minute timeout
    flow_timeout=14400          # 4 hour timeout
)
```

**Selective Persistence:**

```python
# Only persist after important methods
class CustomFlow(Flow[MyState]):
    @start()
    def init(self):
        # Not persisted
        pass

    @persist()  # Method-level persistence
    @listen("init")
    def important_step(self):
        # Persisted after this method
        pass
```

**Custom Error Handling:**

```python
from finwiz.utils.retry_handler import classify_error, get_remediation_suggestion

try:
    result = analyze_holding(ticker)
except Exception as e:
    error_type, is_retryable = classify_error(e)
    suggestion = get_remediation_suggestion(error_type)

    logger.error(f"Failed to analyze {ticker}: {e}")
    logger.info(f"Remediation: {suggestion}")

    if is_retryable:
        # Retry logic
        pass
    else:
        # Skip and continue
        pass
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

- **Documentation**: [docs/README.md](index.md)
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

---

# Advanced System Operations

Complete guide for FinWiz system operations including feedback learning, portfolio monitoring, knowledge base, and integration configuration.

## Table of Contents

1. [Feedback Learning System](#feedback-learning-system)
2. [Portfolio Monitoring](#portfolio-monitoring)
3. [Knowledge Base Strategy](#knowledge-base-strategy)
4. [Intelligent Caching System](#intelligent-caching-system)
5. [Feature Flags & Configuration](#feature-flags--configuration)
6. [Integration Configuration](#integration-configuration)

## Feedback Learning System

### Overview

The Feedback Learning System continuously improves investment discovery by collecting user feedback, tracking performance, and automatically adjusting criteria based on real-world results.

### Components

**1. Feedback Collection**:

- Recommendation acceptance/rejection tracking
- Sentiment analysis (very positive to very negative)
- Confidence ratings (1-5 scale)
- Detailed reasoning collection
- User comments for qualitative insights

**2. Performance Tracking**:

- Alpha calculation vs benchmarks
- Grade maintenance monitoring (A+ retention)
- Risk-adjusted returns (Sharpe, Sortino ratios)
- Drawdown analysis and volatility tracking
- Market regime performance analysis

**3. Learning Engine**:

- Adaptive criteria adjustment based on feedback patterns
- Asset-specific learning for ETFs, stocks, and crypto
- Market regime adaptation
- Statistical significance testing
- Backtesting validation before implementation

### Usage

**Collect Feedback**:

```python
from finwiz.services.feedback_service import get_feedback_service

service = get_feedback_service()

# Submit feedback
await service.submit_feedback(
    recommendation_id="rec_123",
    user_id="user_456",
    accepted=True,
    sentiment="positive",
    confidence=4,
    reasoning="Strong fundamentals and low expense ratio"
)
```

**Track Performance**:

```python
# Track investment performance
await service.track_performance(
    symbol="VTI",
    asset_type="etf",
    performance_data={
        "total_return": 0.12,
        "alpha": 0.02,
        "sharpe_ratio": 1.5,
        "max_drawdown": -0.08
    }
)
```

**Get Learning Insights**:

```python
# Get learning insights
insights = await service.get_learning_insights()

print(f"Total feedback: {insights['total_feedback']}")
print(f"Acceptance rate: {insights['acceptance_rate']:.2%}")
print(f"Criteria adjustments: {len(insights['criteria_adjustments'])}")
```

## Portfolio Monitoring

### Overview

Real-time portfolio monitoring with drift detection, alert generation, and multi-channel notifications.

### Components

**1. Portfolio Monitor**:

- Continuous drift monitoring
- Health dashboard (1-10 scale)
- Alert generation with configurable rules
- Alert lifecycle management

**2. Notification Service**:

- Email notifications (HTML and plain text)
- SMS notifications for critical issues
- User preference management
- Rate limiting and quiet hours

**3. Alert System**:

- Multiple urgency levels (LOW, MEDIUM, HIGH, CRITICAL)
- Configurable thresholds
- Automated monitoring loops
- Error recovery

### Configuration

**Monitoring Rules**:

```python
from finwiz.quantitative.portfolio_monitor import MonitoringRule

rule = MonitoringRule(
    rule_id="portfolio_monitor",
    rule_name="Standard Portfolio Monitoring",
    max_deviation_threshold=0.08,  # 8% threshold
    check_frequency_minutes=60,
    alert_urgency="MEDIUM"
)
```

**Notification Preferences**:

```python
from finwiz.tools.notification_service import NotificationPreferences

preferences = NotificationPreferences(
    user_id="user_123",
    email_enabled=True,
    sms_enabled=True,
    min_alert_level="MEDIUM",
    quiet_hours_start="22:00",
    quiet_hours_end="08:00"
)
```

### Usage

**Start Monitoring**:

```python
from finwiz.quantitative.portfolio_monitor import PortfolioMonitor

monitor = PortfolioMonitor()

# Start monitoring
await monitor.start_monitoring(
    portfolio_config=config,
    monitoring_rule=rule
)
```

**Get Health Dashboard**:

```python
# Get portfolio health
dashboard = await monitor.get_health_dashboard(portfolio_config)

print(f"Health Score: {dashboard.health_score}/10")
print(f"Status: {dashboard.status}")
print(f"Active Alerts: {len(dashboard.active_alerts)}")
```

**Send Notifications**:

```python
from finwiz.tools.notification_service import NotificationService

service = NotificationService()

# Send alert notification
await service.send_notification(
    user_id="user_123",
    alert=alert,
    notification_type="email"
)
```

### Alert Levels

| Level        | Threshold       | Response Time | Notification   |
| ------------ | --------------- | ------------- | -------------- |
| **CRITICAL** | >10% deviation  | Immediate     | Email + SMS    |
| **HIGH**     | 8-10% deviation | 1 hour        | Email + SMS    |
| **MEDIUM**   | 5-8% deviation  | 4 hours       | Email          |
| **LOW**      | 3-5% deviation  | 24 hours      | Email (digest) |

## Knowledge Base Strategy

### Real-Time Information Retrieval

FinWiz uses **real-time information retrieval** instead of a static knowledge base to ensure all financial analysis is based on current data.

### Why Real-Time

**Advantages**:

- Always current data (no staleness)
- Access to entire public web
- No database maintenance overhead
- Captures breaking news and events

**Challenges**:

- Higher API costs
- Slower than cached data
- Rate limiting considerations

### Key Tools

**Web Search**:

- `SerperDevTool` - General web searches
- `YoutubeVideoSearchTool` - Video content

**Financial Data**:

- `YahooFinanceNewsTool` - Latest financial news
- `YahooFinanceTickerInfoTool` - Ticker information
- `AlphaVantageNewsSentimentTool` - News sentiment

**Specialized**:

- `EnhancedSECAnalysisTool` - SEC filings
- `CoinMarketCapTool` - Crypto data
- `PerplexitySearchTool` - Enhanced research (optional)

## Intelligent Caching System

The FinWiz caching system provides intelligent caching capabilities to improve performance, reduce API costs, and enhance system responsiveness. It supports multiple backends, configurable strategies, and comprehensive performance monitoring.

### Architecture Overview

The caching system consists of:

1. **CacheManager**: Central orchestrator for all caching operations
2. **Multiple Backends**: Memory, file, and hybrid storage options
3. **Eviction Strategies**: TTL, LRU, LFU, and adaptive algorithms
4. **Performance Monitoring**: Comprehensive statistics and hit rate tracking
5. **Cache Warming**: Pre-loading of frequently accessed data

### Core Components

#### CacheManager

The `CacheManager` class provides the main interface for caching operations:

```python
from finwiz.utils.cache_manager import get_cache_manager, CacheConfig

# Get the global cache manager instance
cache = get_cache_manager()

# Basic operations
await cache.set("key", {"data": "value"}, ttl=3600)
result = await cache.get("key")
await cache.delete("key")

# Bulk operations
await cache.clear()  # Clear all entries
await cache.cleanup_expired()  # Remove expired entries
```

#### Cache Configuration

Configure caching behavior through `CacheConfig`:

```python
from finwiz.utils.cache_manager import CacheConfig, CacheBackend, CacheStrategy

config = CacheConfig(
    backend=CacheBackend.HYBRID,        # memory, file, or hybrid
    default_ttl=2700,                   # 45 minutes default TTL
    max_memory_items=1000,              # Memory cache size limit
    max_file_size_mb=100,               # File cache size limit
    cache_directory="cache",            # Cache file directory
    strategy=CacheStrategy.TTL,         # Eviction strategy
    enable_compression=True,            # Compress cached data
    auto_cleanup=True,                  # Automatic cleanup
    cleanup_interval=3600,              # Cleanup every hour
    hit_rate_threshold=0.7              # Minimum effective hit rate
)

cache = CacheManager(config)
```

### Cache Backends

#### Memory Backend (`CacheBackend.MEMORY`)

- **Pros**: Fastest access, no disk I/O
- **Cons**: Limited by available RAM, data lost on restart
- **Use Case**: Temporary data, high-frequency access patterns

#### File Backend (`CacheBackend.FILE`)

- **Pros**: Persistent across restarts, larger capacity
- **Cons**: Slower than memory, disk I/O overhead
- **Use Case**: Long-term caching, large datasets

#### Hybrid Backend (`CacheBackend.HYBRID`) - Recommended

- **Pros**: Combines speed of memory with persistence of files
- **Cons**: Slightly more complex management
- **Use Case**: Production environments, balanced performance

### Eviction Strategies

#### TTL (Time-To-Live) - Default

- Removes entries when they exceed their TTL
- Simple and predictable behavior
- Good for time-sensitive data

#### LRU (Least Recently Used)

- Removes least recently accessed entries
- Good for access pattern-based caching
- Maintains frequently used data

#### LFU (Least Frequently Used)

- Removes least frequently accessed entries
- Good for popularity-based caching
- Keeps most popular data in cache

#### Adaptive

- Dynamically adjusts strategy based on access patterns
- Combines multiple strategies for optimal performance
- Best for varied workloads

### Environment Configuration

Configure caching through environment variables:

```bash
# Cache backend configuration
CACHE_BACKEND=hybrid                    # memory, file, hybrid
CACHE_TTL=2700                         # Default TTL in seconds
CACHE_MAX_MEMORY_ITEMS=1000            # Memory cache size limit
CACHE_MAX_FILE_SIZE_MB=100             # File cache size limit
CACHE_DIRECTORY=cache                  # Cache directory path
CACHE_STRATEGY=ttl                     # ttl, lru, lfu, adaptive
CACHE_AUTO_CLEANUP=true                # Enable auto cleanup
CACHE_CLEANUP_INTERVAL=3600            # Cleanup interval in seconds
CACHE_ENABLE_COMPRESSION=true          # Enable data compression
CACHE_HIT_RATE_THRESHOLD=0.7           # Minimum effective hit rate
```

## Feature Flags & Configuration

This guide explains how to use the feature flag system and configuration manager in FinWiz for gradual rollouts, graceful degradation, and environment management.

### Overview

The FinWiz feature flag system provides:

- **Environment-based configuration** for gradual rollouts
- **Circuit breaker patterns** for service reliability
- **Graceful degradation** when services fail
- **Centralized API key management** with validation
- **Multiple evaluation strategies** (boolean, percentage, user lists, time windows)

### Quick Start

#### Basic Feature Flag Usage

```python
from finwiz.utils.feature_flags import is_feature_enabled, execute_with_feature_flag

# Check if a feature is enabled
if is_feature_enabled("enhanced_sentiment_analysis"):
    result = perform_enhanced_analysis()
else:
    result = perform_basic_analysis()

# Execute with automatic fallback
result = execute_with_feature_flag(
    "enhanced_sentiment_analysis",
    primary_function=perform_enhanced_analysis,
    fallback_function=perform_basic_analysis,
    ticker="AAPL"
)
```

#### Configuration Management

```python
from finwiz.utils.configuration_manager import validate_startup_configuration, get_api_key

# Validate all required API keys at startup
try:
    validate_startup_configuration()
    print("✅ All required API keys configured")
except ConfigurationError as e:
    print(f"❌ Configuration error: {e.remediation_guidance}")

# Get API key for a service
openai_key = get_api_key("OpenAI")
if openai_key:
    # Use the API key
    pass
```

### Environment Variables

#### Feature Flag Configuration

Control feature flags using environment variables:

```bash
# Enable/disable features
FF_ENHANCED_SENTIMENT=true
FF_ADVANCED_TECHNICAL=false
FF_CHART_ANALYSIS=true
FF_TWELVE_DATA=true
FF_PERPLEXITY_RESEARCH=false

# Percentage rollouts (0-100)
FF_ENHANCED_SENTIMENT_ROLLOUT=75.0
FF_ADVANCED_TECHNICAL_ROLLOUT=50.0

# Circuit breaker thresholds
FF_CHART_BREAKER_THRESHOLD=3
FF_CHART_BREAKER_TIMEOUT=300
FF_TWELVE_DATA_BREAKER_THRESHOLD=5
FF_PERPLEXITY_BREAKER_THRESHOLD=5
FF_PERPLEXITY_BREAKER_TIMEOUT=300
```

#### API Key Configuration

Configure required API keys:

```bash
# Required keys
OPENAI_API_KEY=sk-your-openai-key-here
SERPER_API_KEY=your-serper-key-here
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-key-here

# Optional keys (controlled by feature flags)
CHART_IMG_API_KEY=your-chart-img-key-here
TWELVE_DATA_API_KEY=your-twelve-data-key-here
X-CMC_PRO_API_KEY=your-coinmarketcap-key-here
KRAKEN_API_KEY=your-kraken-key-here
PPLX_API_KEY=your-perplexity-api-key-here
```

### Circuit Breaker Pattern

The circuit breaker pattern automatically disables failing services:

```python
# Configure circuit breaker
degradation_manager = get_degradation_manager()
degradation_manager.update_service_config(
    "external_api",
    error_threshold=5,        # Open circuit after 5 failures
    circuit_breaker_timeout=300,  # Wait 5 minutes before retry
    recovery_threshold=2      # Close circuit after 2 successes
)
```

## Integration Configuration

### Overview

Centralized data management and coordination between analysis crews with validation, freshness checking, and error handling.

### Environment Variables

**Location**: `.env`

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

# Validation Settings
FINWIZ_STRICT_VALIDATION=true
FINWIZ_VALIDATION_TIMEOUT=30
FINWIZ_CONTINUE_ON_WARNINGS=true

# Error Handling
FINWIZ_MAX_RETRIES=3
FINWIZ_RETRY_DELAY=2
FINWIZ_GRACEFUL_DEGRADATION=true
```

### Data Freshness

**Freshness Thresholds**:

- **Stock**: 24 hours (daily updates sufficient)
- **ETF**: 48 hours (less volatile)
- **Crypto**: 12 hours (high volatility)
- **Discovery**: 72 hours (weekly discovery runs)
- **Portfolio**: 168 hours (weekly reviews)

### Validation

**Validation Modes**:

- `strict_validation=true`: Fail on validation errors
- `strict_validation=false`: Warn on validation errors
- `continue_on_warnings=true`: Continue despite warnings

### Error Handling

**Retry Strategy**:

- Automatic retry with exponential backoff (max_retries: 3, retry_delay: 2s)

**Graceful Degradation**:

- Use cached data if available
- Fall back to baseline analysis
- Continue with partial data

## Best Practices

### Feedback Learning

1. **Collect Regularly**: Prompt users for feedback after recommendations
2. **Track Performance**: Monitor all A+ investments for at least 1 year
3. **Review Insights**: Monthly review of learning insights

### Portfolio Monitoring

1. **Set Appropriate Thresholds**: Balance sensitivity vs noise
2. **Configure Quiet Hours**: Respect user preferences
3. **Test Notifications**: Verify email/SMS delivery

### Knowledge Base & Caching

1. **Enable Caching**: Use hybrid caching for performance
2. **Monitor Costs**: Track API usage and costs
3. **Validate Freshness**: Check data timestamps

### Integration

1. **Configure Freshness**: Set appropriate thresholds per crew
2. **Enable Validation**: Use strict validation in production
3. **Monitor Metrics**: Track cache hit rate and latency

---

**Version**: 2.0
**Last Updated**: 2025-03-10
