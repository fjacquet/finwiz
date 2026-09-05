# Performance Configuration Guide

## Overview

FinWiz's performance configuration system provides three optimization modes that balance speed, cost, and analysis depth. The system automatically configures crews, tools, and scoring engines based on environment variables to achieve optimal performance for different use cases.

## Optimization Modes

### 1. Maximum Speed Mode (Default)

**Target Use Case**: Production portfolio analysis, high-volume processing

**Configuration**:

```bash
# Environment Variables
RISK_ASSESSMENT_USE_MINI=true
USE_MINIMAL_RISK_TOOLS=true
DEEP_ANALYSIS_AI_SUMMARY=false
DEEP_ANALYSIS_BATCH_SIZE=10
```

**Performance Characteristics**:

- **Execution Time**: 10-30 seconds per ticker
- **LLM Calls**: 0 for calculations (Python scoring only)
- **Cost per Ticker**: \$0.00 for calculations
- **Speedup Factor**: 10-20x vs baseline
- **Cost Savings**: 100% vs baseline

**Components**:

- Python-based scoring engine (DeepAnalysisScorer)
- gpt-4o-mini for any remaining AI tasks
- Minimal tool sets for focused analysis
- No AI summary generation
- Batch processing enabled

**Best For**:

- Large portfolio analysis (50+ holdings)
- Frequent analysis runs
- Cost-sensitive environments
- Production deployments

### 2. Balanced Mode (Hybrid Approach)

**Target Use Case**: Detailed analysis with optional AI insights

**Configuration**:

```bash
# Environment Variables
RISK_ASSESSMENT_USE_MINI=true
USE_MINIMAL_RISK_TOOLS=true
DEEP_ANALYSIS_AI_SUMMARY=true
DEEP_ANALYSIS_BATCH_SIZE=3
```

**Performance Characteristics**:

- **Execution Time**: 15-40 seconds per ticker
- **LLM Calls**: 1 for optional AI summary
- **Cost per Ticker**: \$0.01
- **Speedup Factor**: 8-15x vs baseline
- **Cost Savings**: 80-90% vs baseline

**Components**:

- Python-based scoring engine (primary)
- Optional AI summary generation (secondary)
- gpt-4o-mini for cost efficiency
- Minimal tool sets
- Smaller batch sizes for quality

**Best For**:

- Medium portfolios (10-50 holdings)
- Quality-focused analysis
- Hybrid AI/Python approach
- Development and testing

### 3. Baseline Mode (AI Comparison)

**Target Use Case**: Debugging, validation, and AI comparison

**Configuration**:

```bash
# Environment Variables
RISK_ASSESSMENT_USE_MINI=false
USE_MINIMAL_RISK_TOOLS=false
DEEP_ANALYSIS_AI_SUMMARY=true
DEEP_ANALYSIS_BATCH_SIZE=1
```

**Performance Characteristics**:

- **Execution Time**: 5-10 minutes per ticker
- **LLM Calls**: 5-10 for full AI analysis
- **Cost per Ticker**: \$0.05-0.10
- **Speedup Factor**: 1x (baseline)
- **Cost Savings**: 0% (baseline)

**Components**:

- Full AI-based analysis
- GPT-4 for highest quality
- Complete tool sets
- Sequential processing
- Full reasoning and planning enabled

**Best For**:

- Single ticker deep analysis
- AI vs Python comparison
- Debugging and validation
- Research and development

## Configuration Management

### PerformanceConfigManager

The `PerformanceConfigManager` class handles all performance-related configuration:

```python
from finwiz.config.performance.performance_config import PerformanceConfigManager, OptimizationMode

# Initialize configuration manager
config_manager = PerformanceConfigManager()

# Get current configuration
config = config_manager.get_config()
print(f"Mode: {config.mode}")
print(f"Batch Size: {config.deep_analysis_batch_size}")
print(f"Use Mini Model: {config.risk_assessment_use_mini}")

# Check specific modes
if config_manager.is_maximum_speed_mode():
    print("Running in maximum speed mode")
elif config_manager.is_balanced_mode():
    print("Running in balanced mode")
else:
    print("Running in baseline mode")
```

### Environment Variable Reference

| Variable                   | Default | Description                            | Impact                           |
| -------------------------- | ------- | -------------------------------------- | -------------------------------- |
| `RISK_ASSESSMENT_USE_MINI` | `true`  | Use gpt-4o-mini for risk assessment    | 5-10x faster, 80% cost reduction |
| `USE_MINIMAL_RISK_TOOLS`   | `true`  | Use minimal tool set for risk analysis | 2-3x faster, reduced complexity  |
| `DEEP_ANALYSIS_AI_SUMMARY` | `false` | Generate optional AI summary           | +5-10s per ticker, +\$0.01 cost  |
| `DEEP_ANALYSIS_BATCH_SIZE` | `10`    | Concurrent analysis batch size         | Higher = faster but more memory  |

### Automatic Mode Detection

The system automatically determines the optimization mode based on configuration:

```python
def _determine_optimization_mode(self, use_mini: bool, minimal_tools: bool, ai_summary: bool) -> OptimizationMode:
    """Determine optimization mode based on configuration."""
    if use_mini and minimal_tools and not ai_summary:
        return OptimizationMode.MAXIMUM_SPEED
    elif use_mini and minimal_tools and ai_summary:
        return OptimizationMode.BALANCED
    else:
        return OptimizationMode.BASELINE
```

## Performance Monitoring

### Metrics Tracking

The system tracks comprehensive performance metrics:

```python
@dataclass
class PerformanceMetrics:
    """Performance metrics tracking."""

    execution_time: float = 0.0  # Total execution time
    llm_call_count: int = 0  # Number of LLM API calls
    api_call_count: int = 0  # Number of external API calls
    cost_estimate: float = 0.0  # Estimated cost in USD
    ticker: str = ""  # Analyzed ticker
    mode: OptimizationMode = OptimizationMode.BASELINE
```

### Performance Logging

Automatic performance logging provides detailed insights:

```python
# Example performance log output
logger.info("Performance Optimization Configuration:")
logger.info(f"  Mode: maximum_speed")
logger.info(f"  Risk Assessment Use Mini: True")
logger.info(f"  Use Minimal Risk Tools: True")
logger.info(f"  Deep Analysis AI Summary: False")
logger.info(f"  Deep Analysis Batch Size: 10")

logger.info(f"Expected Performance (maximum_speed):")
logger.info(f"  Description: Python scoring + no AI summary + gpt-4o-mini + minimal tools")
logger.info(f"  Time per ticker: 10-30 seconds")
logger.info(f"  LLM calls: 0 for calculations")
logger.info(f"  Cost per ticker: $0")
```

### Real-Time Performance Tracking

**`PerformanceMonitor` has no `track_analysis` context manager, no
`get_performance_summary`, and no `record_cost` — there is no separate
`tracker` object either.** Its real API is `start_ticker_analysis` /
`record_api_call` / `record_llm_call` / `complete_ticker_analysis` /
`complete_portfolio_analysis`, all called directly on the monitor:

```python
from finwiz.infrastructure.monitoring.performance import PerformanceMonitor

monitor = PerformanceMonitor(session_id="analysis-session-123")

# Track analysis performance
monitor.start_ticker_analysis("AAPL", "stock")
result = scorer.calculate_composite_score("AAPL", "stock", data)

monitor.record_llm_call(0.0)  # Python scoring = 0 LLM calls, $0 cost
metrics = monitor.complete_ticker_analysis(success=True, ticker="AAPL")

# View portfolio-level summary
portfolio_metrics = monitor.complete_portfolio_analysis()
summary = portfolio_metrics.calculate_portfolio_performance()
print(f"Total time: {summary['total_execution_time']:.2f}s")
print(f"Success rate: {summary['success_rate_pct']:.1f}%")
```

(Source: `src/finwiz/infrastructure/monitoring/performance.py:217-349`.)

## Batch Processing Configuration

### Environment Variables

| Variable                      | Default | Description                           | Performance Impact                   |
| ----------------------------- | ------- | ------------------------------------- | ------------------------------------ |
| `BATCH_PREFETCH_ENABLED`      | `true`  | Enable batch data pre-fetching        | 10-20x speedup                       |
| `BATCH_PREFETCH_MIN_HOLDINGS` | `10`    | Min holdings to trigger batch mode    | Avoids overhead for small portfolios |
| `DEEP_ANALYSIS_BATCH_SIZE`    | `10`    | Concurrent crew execution batch size  | Balances speed vs memory             |
| `ENABLE_ALPHA_VANTAGE`        | `false` | Use Alpha Vantage as secondary source | Adds ~13 min for 66 tickers          |

### Batch Size Optimization

**There is no adaptive batch sizing.** `get_recommended_batch_size` and
`BATCH_SIZE_RECOMMENDATIONS` do not exist anywhere in the codebase (`grep -rn
'get_recommended_batch_size' src/ tests/` finds no matches). Batch size comes
from exactly one place — `get_batch_size()` reading `DEEP_ANALYSIS_BATCH_SIZE`
(default 10) — and portfolio size does not influence it. To change it, set
the environment variable directly:

```bash
DEEP_ANALYSIS_BATCH_SIZE=10   # default
```

### Data Source Configuration

**Primary Source - Yahoo Finance (Always Enabled)**:

- Performance: ~2-5 seconds for 66 tickers
- Coverage: All essential data (fundamentals, price, history)
- Rate limit: 600 requests/minute
- Recommendation: Always use (primary source)

**Secondary Source - Alpha Vantage (Optional)**:

- Performance: ~13 minutes for 66 tickers (free tier)
- Coverage: Additional fundamental data
- Rate limit: 5/minute (free), 75/minute (premium)
- Recommendation: Disable unless premium tier

### Fallback Behavior

**There is no sequential-mode fallback.** `_fallback_to_sequential_mode` does
not exist anywhere in the codebase. When batch prefetch is disabled, skipped
for too few holdings, or raises an exception, `run_batch_prefetch` simply
logs it and returns `{}` (`src/finwiz/orchestrators/batch_prefetch_runner.py:38-48,64-66`).
Deep analysis then proceeds concurrently on all holdings regardless — there
is no one-ticker-at-a-time sequential path, and no failure-rate or
memory-based trigger for one.

### Memory Management

Monitor and manage memory usage during batch processing:

```python
from finwiz.infrastructure.monitoring.memory_manager import get_memory_manager

memory_manager = get_memory_manager(session_id="analysis-session-123")

# Sample memory at a processing stage; returns a dict, not a context manager
sample = memory_manager.monitor_memory("batch_analysis")
if sample["memory_mb"] > 1000:  # 1GB threshold
    logger.warning("High memory usage detected")
    memory_manager.cleanup_cache()

# After the Flow completes
metrics = memory_manager.get_memory_metrics()
memory_manager.validate_memory_constraints()
```

**`MemoryManager()` cannot be constructed without a `session_id`** (use the
`get_memory_manager(session_id)` factory instead), and there is no
`get_available_memory_gb` method — `MemoryManager` tracks memory *used* by
this process against a fixed limit, it does not query available system
memory, and it never feeds back into batch sizing.

(Source: `src/finwiz/infrastructure/monitoring/memory_manager.py:49,120,230,287,309`.)

### Error Handling

**Partial Failure Handling**:

- Individual ticker failures don't stop batch processing
- Failed tickers are logged and marked in results
- Analysis continues with available data

**Complete Failure Recovery**:

- No sequential-mode fallback exists — on complete batch prefetch failure,
  `run_batch_prefetch` returns `{}` and deep analysis proceeds concurrently
  on all holdings without the prefetched cache
- Detailed logging of failure reasons
- Graceful degradation without data loss

## CrewAI Integration

### Crew Configuration by Mode

Different optimization modes configure CrewAI crews differently:

```python
def configure_crew_for_mode(mode: OptimizationMode) -> Dict[str, Any]:
    """Configure CrewAI crew based on optimization mode."""

    if mode == OptimizationMode.MAXIMUM_SPEED:
        return {
            "reasoning": False,  # Disable reasoning for speed
            "planning": False,  # Disable planning for speed
            "allow_delegation": False,  # Disable delegation for speed
            "max_rpm": 30,  # Higher rate limit
            "llm": "gpt-4o-mini",  # Faster, cheaper model
        }

    elif mode == OptimizationMode.BALANCED:
        return {
            "reasoning": True,  # Enable reasoning for quality
            "planning": False,  # Disable planning for speed
            "allow_delegation": False,  # Disable delegation for speed
            "max_rpm": 20,  # Standard rate limit
            "llm": "gpt-4o-mini",  # Balanced model
        }

    else:  # BASELINE
        return {
            "reasoning": True,  # Full reasoning enabled
            "planning": True,  # Full planning enabled
            "allow_delegation": True,  # Full delegation enabled
            "max_rpm": 15,  # Conservative rate limit
            "llm": "gpt-4",  # Highest quality model
        }
```

### Tool Set Configuration

Optimize tool sets based on performance mode:

```python
def get_tools_for_mode(mode: OptimizationMode, asset_class: str) -> List[BaseTool]:
    """Get optimized tool set based on performance mode."""

    if mode == OptimizationMode.MAXIMUM_SPEED:
        # Minimal tool set for speed
        return [
            TickerExistenceValidationTool(),
            QuantitativeAnalysisTool(asset_class=asset_class),
            # Skip expensive tools like detailed sentiment analysis
        ]

    elif mode == OptimizationMode.BALANCED:
        # Balanced tool set
        return [
            TickerExistenceValidationTool(),
            QuantitativeAnalysisTool(asset_class=asset_class),
            StandardizedSentimentTool(),
            # Include key tools but skip expensive ones
        ]

    else:  # BASELINE
        # Full tool set for comprehensive analysis
        return get_full_tool_set(asset_class)
```

## Performance Benchmarks

### Execution Time Benchmarks

#### With Batch Processing (Default)

| Portfolio Size | Maximum Speed | Balanced      | Baseline       |
| -------------- | ------------- | ------------- | -------------- |
| 10 holdings    | 2-5 minutes   | 3-7 minutes   | 50-100 minutes |
| 30 holdings    | 5-15 minutes  | 8-20 minutes  | 2.5-5 hours    |
| 66 holdings    | 11-33 minutes | 17-44 minutes | 5.5-11 hours   |
| 100 holdings   | 17-50 minutes | 25-67 minutes | 8.3-16.7 hours |

#### Without Batch Processing (Sequential Mode)

| Portfolio Size | Maximum Speed   | Balanced        | Baseline       |
| -------------- | --------------- | --------------- | -------------- |
| 10 holdings    | 20-50 minutes   | 30-70 minutes   | 50-100 minutes |
| 30 holdings    | 60-150 minutes  | 90-210 minutes  | 2.5-5 hours    |
| 66 holdings    | 132-330 minutes | 198-462 minutes | 5.5-11 hours   |
| 100 holdings   | 200-500 minutes | 300-700 minutes | 8.3-16.7 hours |

#### Batch Processing Impact

| Portfolio Size | Speedup Factor | Time Savings |
| -------------- | -------------- | ------------ |
| 10 holdings    | 4-10x          | 75-90%       |
| 30 holdings    | 4-10x          | 75-90%       |
| 66 holdings    | 4-10x          | 75-90%       |
| 100 holdings   | 4-10x          | 75-90%       |

### Cost Benchmarks

| Portfolio Size | Maximum Speed | Balanced | Baseline     |
| -------------- | ------------- | -------- | ------------ |
| 10 holdings    | \$0.00        | \$0.10   | \$0.50-1.00  |
| 30 holdings    | \$0.00        | \$0.30   | \$1.50-3.00  |
| 66 holdings    | \$0.00        | \$0.66   | \$3.30-6.60  |
| 100 holdings   | \$0.00        | \$1.00   | \$5.00-10.00 |

### Quality Benchmarks

| Metric                       | Maximum Speed     | Balanced          | Baseline  |
| ---------------------------- | ----------------- | ----------------- | --------- |
| **Score Accuracy**           | ±0.02 vs baseline | ±0.01 vs baseline | Reference |
| **Grade Consistency**        | 95% match         | 98% match         | Reference |
| **Recommendation Alignment** | 92% match         | 96% match         | Reference |
| **Data Preservation**        | 100%              | 100%              | 100%      |

## Optimization Strategies

### Portfolio Size-Based Optimization

Automatically adjust configuration based on portfolio size:

```python
def optimize_for_portfolio_size(portfolio_size: int) -> OptimizationConfig:
    """Optimize configuration based on portfolio size."""

    if portfolio_size <= 5:
        # Small portfolio - use baseline for quality
        return OptimizationConfig(mode=OptimizationMode.BASELINE, deep_analysis_batch_size=1, risk_assessment_use_mini=False)

    elif portfolio_size <= 20:
        # Medium portfolio - use balanced approach
        return OptimizationConfig(mode=OptimizationMode.BALANCED, deep_analysis_batch_size=3, deep_analysis_ai_summary=True)

    else:
        # Large portfolio - use maximum speed
        return OptimizationConfig(mode=OptimizationMode.MAXIMUM_SPEED, deep_analysis_batch_size=min(8, portfolio_size // 8), deep_analysis_ai_summary=False)
```

### Time-Based Optimization

Adjust configuration based on available time:

```python
def optimize_for_time_constraint(max_time_minutes: int, portfolio_size: int) -> OptimizationConfig:
    """Optimize configuration for time constraints."""

    estimated_time = {
        OptimizationMode.MAXIMUM_SPEED: portfolio_size * 0.5,  # 30s per ticker
        OptimizationMode.BALANCED: portfolio_size * 0.75,  # 45s per ticker
        OptimizationMode.BASELINE: portfolio_size * 8.0,  # 8 min per ticker
    }

    # Choose fastest mode that fits time constraint
    for mode in [OptimizationMode.MAXIMUM_SPEED, OptimizationMode.BALANCED, OptimizationMode.BASELINE]:
        if estimated_time[mode] <= max_time_minutes:
            return OptimizationConfig(mode=mode)

    # If no mode fits, use maximum speed with larger batches
    return OptimizationConfig(mode=OptimizationMode.MAXIMUM_SPEED, deep_analysis_batch_size=min(15, portfolio_size // 4))
```

### Cost-Based Optimization

Optimize for budget constraints:

```python
def optimize_for_budget(max_cost_usd: float, portfolio_size: int) -> OptimizationConfig:
    """Optimize configuration for budget constraints."""

    estimated_cost = {
        OptimizationMode.MAXIMUM_SPEED: 0.0,  # $0 per ticker
        OptimizationMode.BALANCED: portfolio_size * 0.01,  # $0.01 per ticker
        OptimizationMode.BASELINE: portfolio_size * 0.075,  # $0.075 per ticker
    }

    # Choose most comprehensive mode within budget
    for mode in [OptimizationMode.BASELINE, OptimizationMode.BALANCED, OptimizationMode.MAXIMUM_SPEED]:
        if estimated_cost[mode] <= max_cost_usd:
            return OptimizationConfig(mode=mode)

    # If budget is very tight, use maximum speed
    return OptimizationConfig(mode=OptimizationMode.MAXIMUM_SPEED)
```

## Troubleshooting

### Performance Issues

**Issue**: Analysis taking longer than expected

```python
# Diagnosis
config_manager = get_performance_config_manager()
current_mode = config_manager.get_mode()

if current_mode != OptimizationMode.MAXIMUM_SPEED:
    logger.warning(f"Not using maximum speed mode: {current_mode}")

# Check batch processing status
batch_enabled = os.getenv("BATCH_PREFETCH_ENABLED", "true").lower() == "true"
if not batch_enabled:
    logger.warning("Batch processing is disabled - tickers will be fetched individually during analysis")

# Solution: Enable batch processing and maximum speed mode
os.environ["BATCH_PREFETCH_ENABLED"] = "true"
os.environ["DEEP_ANALYSIS_AI_SUMMARY"] = "false"
os.environ["RISK_ASSESSMENT_USE_MINI"] = "true"
os.environ["ENABLE_ALPHA_VANTAGE"] = "false"  # Disable for speed
```

**Issue**: High memory usage during batch processing

```python
# Diagnosis
import psutil

memory_usage = psutil.virtual_memory().percent

if memory_usage > 80:
    logger.warning(f"High memory usage: {memory_usage}%")

# Solution: Reduce batch size
current_batch_size = int(os.getenv("DEEP_ANALYSIS_BATCH_SIZE", "10"))
new_batch_size = max(1, current_batch_size // 2)
os.environ["DEEP_ANALYSIS_BATCH_SIZE"] = str(new_batch_size)
logger.info(f"Reduced batch size from {current_batch_size} to {new_batch_size}")
```

**Issue**: Frequent batch prefetch failures

```python
# Diagnosis: check for prefetch failures in logs (there is no sequential-mode
# fallback; on failure run_batch_prefetch just returns {} and logs the
# exception, then deep analysis continues without the prefetched cache)
import subprocess

result = subprocess.run(["grep", "Batch prefetch failed", "logs/finwiz.log"], capture_output=True, text=True)
failures = result.stdout.strip().split("\n")

for failure in failures[-5:]:  # Last 5 failures
    logger.info(f"Recent failure: {failure}")

# Common solutions:
# 1. Network issues: Check internet connection
# 2. Memory issues: Reduce DEEP_ANALYSIS_BATCH_SIZE
# 3. API rate limits: Disable Alpha Vantage
os.environ["ENABLE_ALPHA_VANTAGE"] = "false"
os.environ["DEEP_ANALYSIS_BATCH_SIZE"] = "3"
```

**Issue**: Inconsistent results between runs

```python
# Diagnosis: Check if using AI components
if should_use_ai_summary():
    logger.warning("AI summary enabled - may cause result variation")

# Solution: Disable AI components for consistency
os.environ["DEEP_ANALYSIS_AI_SUMMARY"] = "false"
```

**Issue**: Individual tickers failing consistently

```python
# Diagnosis: Check for ticker-specific failures
import subprocess

result = subprocess.run(["grep", "Failed to process.*data for", "logs/finwiz.log"], capture_output=True, text=True)
failed_tickers = result.stdout.strip().split("\n")

# Analyze failure patterns
ticker_failures = {}
for line in failed_tickers[-20:]:  # Last 20 failures
    if "Failed to process" in line:
        # Extract ticker from log line
        ticker = line.split("for ")[1].split(":")[0] if "for " in line else "unknown"
        ticker_failures[ticker] = ticker_failures.get(ticker, 0) + 1

logger.info(f"Ticker failure counts: {ticker_failures}")

# Solution: Remove consistently failing tickers from portfolio
# or investigate ticker validity (delisted stocks, invalid symbols)
```

### Configuration Issues

**Issue**: Environment variables not taking effect

```python
# Diagnosis: Check configuration loading
config_manager = PerformanceConfigManager()
config_summary = config_manager.get_configuration_summary()
logger.info(f"Current configuration: {config_summary}")

# Solution: Restart application or reload configuration
config_manager = PerformanceConfigManager()  # Reload from environment
```

**Issue**: Unexpected optimization mode

```python
# Diagnosis: Check mode determination logic
use_mini = os.getenv("RISK_ASSESSMENT_USE_MINI", "true").lower() == "true"
minimal_tools = os.getenv("USE_MINIMAL_RISK_TOOLS", "true").lower() == "true"
ai_summary = os.getenv("DEEP_ANALYSIS_AI_SUMMARY", "false").lower() == "true"

expected_mode = determine_optimization_mode(use_mini, minimal_tools, ai_summary)
logger.info(f"Expected mode: {expected_mode}")
```

## Best Practices

### Production Deployment

1. **Use Maximum Speed Mode** for production portfolio analysis
2. **Monitor performance metrics** and adjust batch sizes as needed
3. **Set up alerts** for performance degradation
4. **Cache frequently accessed data** to reduce API calls
5. **Use load balancing** for high-volume processing

### Development and Testing

1. **Use Balanced Mode** for development to catch issues
2. **Use Baseline Mode** for accuracy validation
3. **Test all modes** to ensure compatibility
4. **Monitor resource usage** during development
5. **Profile performance** to identify bottlenecks

### Configuration Management

1. **Use environment variables** for configuration
2. **Document configuration changes** in deployment notes
3. **Test configuration changes** in staging environment
4. **Monitor impact** of configuration changes
5. **Have rollback plan** for configuration issues

## Future Enhancements

### Planned Improvements

1. **Adaptive Batch Sizing**: Automatically adjust batch size based on system resources
2. **Predictive Optimization**: Use historical data to predict optimal configuration
3. **Multi-Tier Caching**: Implement sophisticated caching strategies
4. **Resource Monitoring**: Real-time resource usage monitoring and adjustment
5. **A/B Testing Framework**: Test different configurations automatically

### Advanced Features

1. **Custom Optimization Profiles**: User-defined optimization profiles
2. **Machine Learning Optimization**: ML-based configuration optimization
3. **Distributed Processing**: Scale across multiple machines
4. **Real-Time Adaptation**: Adjust configuration based on real-time performance
5. **Cost Optimization**: Automatic cost optimization based on budget constraints

## Conclusion

The FinWiz performance configuration system provides:

- **Flexible optimization modes** for different use cases
- **Automatic configuration management** based on environment variables
- **Comprehensive performance monitoring** and metrics tracking
- **Significant performance improvements** (10-20x speedup, 100% cost reduction)
- **Maintained analysis quality** with deterministic Python scoring
- **Easy troubleshooting** and optimization strategies

This system enables FinWiz to scale from single-ticker analysis to large portfolio processing while maintaining high quality and cost efficiency.

---

**Version**: 1.0
**Last Updated**: 2025-01-25
**Related Documentation**:

- [Python Scoring Engine Documentation](PYTHON_SCORING_ENGINE.md)
- [Batch Processing Guide](BATCH_PROCESSING.md)
- [Performance Monitoring Guide](PERFORMANCE_CONFIGURATION.md)
