# Memory Management for Batch Processing

This document describes the memory management system for batch data pre-fetching and crew execution in FinWiz.

## Data Source Priority

**IMPORTANT**: Yahoo Finance is the PRIMARY data source and is ALWAYS used.

- **Yahoo Finance (PRIMARY)**: ALWAYS ENABLED
  - Provides ALL essential data: company info, fundamentals, price, history
  - Performance: ~2-5 seconds for 66 tickers
  - Rate limit: 600 requests/minute (10/second)
  - **Recommended configuration**

- **Alpha Vantage (OPTIONAL)**: DISABLED BY DEFAULT
  - Adds minimal value over Yahoo Finance
  - Performance: ~13 minutes for 66 tickers
  - Rate limit: 5 calls/minute (free tier)
  - **Not recommended** - Yahoo Finance provides all essential data

## Overview

The memory management system ensures that batch processing stays within acceptable memory limits (< 1024 MB total) by:

1. **Monitoring memory usage** during pre-fetch and execution
2. **Logging memory metrics** for performance analysis
3. **Cleaning up cache** after Flow completion
4. **Validating memory constraints** to ensure limits are met

## Requirements

- **17.70**: Monitor memory usage during pre-fetch and execution
- **17.71**: Implement cache cleanup after Flow completion
- **17.72**: Add memory usage logging to metrics
- **17.73**: Validate memory constraints (< 1024 MB total)
- **17.74**: Memory limit enforcement and warnings

## Architecture

### Components

1. **MemoryManager** (`src/finwiz/infrastructure/monitoring/memory_manager.py`)
   - Core memory monitoring and management
   - Memory usage tracking and logging
   - Cache cleanup functionality
   - Memory constraint validation

2. **BatchDataPreFetcher** (`src/finwiz/integration/batch_data_prefetcher.py`)
   - Integrates MemoryManager for monitoring
   - Tracks memory during batch operations
   - Provides memory metrics and cleanup methods

3. **Flow Integration** (to be implemented in Flow orchestrator)
   - Monitors memory during crew execution
   - Cleans up cache after Flow completion
   - Includes memory metrics in performance reports

## Usage

### Basic Usage with BatchDataPreFetcher

```python
from finwiz.integration.batch_data_prefetcher import BatchDataPreFetcher

# Initialize prefetcher (automatically creates memory manager)
# Yahoo Finance is ALWAYS used (primary source)
# Alpha Vantage is DISABLED by default (recommended)
prefetcher = BatchDataPreFetcher(
    session_id="session-123",
    enable_alpha_vantage=False,  # Recommended: Yahoo Finance only
)

# Pre-fetch data (memory is monitored automatically)
# Yahoo Finance provides all essential data in ~2-5 seconds
data = prefetcher.prefetch_all_data(["AAPL", "MSFT", "GOOGL"])

# Get memory metrics
metrics = prefetcher.get_memory_metrics()
print(f"Peak memory: {metrics['peak_memory_mb']} MB")
print(f"Within limit: {metrics['within_limit']}")

# Validate memory constraints
if prefetcher.validate_memory_constraints():
    print("✓ Memory usage within limits")
else:
    print("✗ Memory limit exceeded")

# Clean up cache after completion
cleanup_result = prefetcher.cleanup_cache()
print(f"Freed {cleanup_result['disk_freed_mb']} MB")
```

### Direct MemoryManager Usage

```python
from finwiz.infrastructure.monitoring.memory_manager import get_memory_manager

# Create memory manager
memory_manager = get_memory_manager(session_id="session-123")

# Monitor memory at different stages
memory_manager.monitor_memory("initialization")
# ... perform operations ...
memory_manager.monitor_memory("data-processing")
# ... more operations ...
memory_manager.monitor_memory("completion")

# Get comprehensive metrics
metrics = memory_manager.get_memory_metrics()

# Validate constraints
is_valid = memory_manager.validate_memory_constraints()

# Clean up cache
cleanup_result = memory_manager.cleanup_cache()
```

### Flow Integration Example

```python
from finwiz.integration.batch_data_prefetcher import BatchDataPreFetcher
from finwiz.infrastructure.monitoring.memory_manager import get_memory_manager


class FinwizFlow(Flow[FinwizState]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.memory_manager = None
        self.prefetcher = None

    @listen("check_portfolio")
    def execute_deep_analysis_with_prefetch(self) -> dict[str, Any]:
        """Execute deep analysis with batch pre-fetching and memory monitoring."""

        # Initialize prefetcher with memory management
        session_id = self.state.session_id
        self.prefetcher = BatchDataPreFetcher(
            session_id=session_id,
            enable_alpha_vantage=False,  # Yahoo Finance only for speed
        )

        # Get memory manager reference
        self.memory_manager = self.prefetcher.memory_manager

        # Monitor memory at start
        self.memory_manager.monitor_memory("deep-analysis-start")

        # Get holdings to analyze
        holdings = self._get_underperforming_holdings()
        tickers = [h["ticker"] for h in holdings]

        # Pre-fetch all data in batch
        logger.info(f"Pre-fetching data for {len(tickers)} holdings...")
        prefetched_data = self.prefetcher.prefetch_all_data(tickers)

        # Monitor memory after pre-fetch
        self.memory_manager.monitor_memory("pre-fetch-complete")

        # Execute crews with pre-fetched data
        results = {}
        for ticker in tickers:
            ticker_data = prefetched_data.get(ticker, {})

            # Create and execute crew with pre-fetched data
            crew = DeepAnalysisCrew()
            crew.set_prefetched_data(ticker_data)
            result = crew.crew().kickoff(inputs={"ticker": ticker})
            results[ticker] = result

            # Monitor memory periodically
            if len(results) % 10 == 0:
                self.memory_manager.monitor_memory(f"crew-execution-{len(results)}")

        # Monitor memory after all crews complete
        self.memory_manager.monitor_memory("all-crews-complete")

        # Get memory metrics for reporting
        memory_metrics = self.prefetcher.get_memory_metrics()

        # Validate memory constraints
        if not self.prefetcher.validate_memory_constraints():
            logger.warning("Memory constraints were exceeded during execution")

        # Store metrics in state
        self.state.batch_prefetch_metrics = {"memory": memory_metrics, "tickers_analyzed": len(results), "successful": sum(1 for r in results.values() if r.get("success", False))}

        return {"results": results, "memory_metrics": memory_metrics}

    def cleanup(self):
        """Clean up resources after Flow completion."""
        if self.prefetcher:
            logger.info("Cleaning up batch prefetch cache...")
            cleanup_result = self.prefetcher.cleanup_cache()
            logger.info(f"Cache cleanup complete: {cleanup_result['files_removed']} files, {cleanup_result['disk_freed_mb']} MB freed")
```

## Memory Monitoring

### Automatic Monitoring Points

The BatchDataPreFetcher automatically monitors memory at these stages:

1. **pre-fetch-start**: Before any data fetching begins
2. **yahoo-finance-complete**: After Yahoo Finance batch fetch
3. **alpha-vantage-complete**: After Alpha Vantage batch fetch (if enabled)
4. **cache-save-complete**: After saving data to cache

### Manual Monitoring

You can add custom monitoring points:

```python
memory_manager.monitor_memory("custom-stage-name")
```

### Memory Metrics

Each monitoring point captures:

- **stage**: Description of the stage
- **memory_mb**: Current memory usage in MB
- **memory_bytes**: Current memory usage in bytes
- **delta_mb**: Change from initial memory in MB
- **peak_mb**: Peak memory usage so far in MB
- **within_limit**: Whether memory is within 1024 MB limit

## Memory Constraints

### Limits

- **Maximum memory**: 1024 MB (configurable via `MAX_MEMORY_MB` in `memory_manager.py`)
- **Warning threshold**: 80% of maximum (~819 MB)
- **Error threshold**: 100% of maximum (1024 MB)

### Warnings and Errors

The system automatically logs:

- **Warning** at 80% threshold: Approaching memory limit
- **Error** at 100% threshold: Memory limit exceeded

### Validation

After Flow completion, validate memory constraints:

```python
if prefetcher.validate_memory_constraints():
    logger.info("✓ Memory constraints validated")
else:
    logger.error("✗ Memory constraints violated")
```

## Cache Cleanup

### Automatic Cleanup

Cache cleanup should be called after Flow completion:

```python
cleanup_result = prefetcher.cleanup_cache()
```

### Cleanup Metrics

The cleanup operation returns:

- **cache_dir**: Path to cache directory
- **disk_freed_mb**: Disk space freed in MB
- **files_removed**: Number of files removed
- **success**: Whether cleanup succeeded

### Manual Cleanup

You can also use the memory manager directly:

```python
cleanup_result = memory_manager.cleanup_cache()
```

## Performance Metrics

### Memory Metrics Structure

```python
{
    "initial_memory_mb": 100.0,
    "peak_memory_mb": 150.0,
    "final_memory_mb": 120.0,
    "memory_increase_mb": 20.0,
    "max_memory_limit_mb": 1024,
    "within_limit": True,
    "peak_usage_percent": 14.6,
    "samples": [
        {"stage": "pre-fetch-start", "memory_mb": 100.0, "delta_mb": 0.0, "peak_mb": 100.0, "within_limit": True},
        # ... more samples ...
    ],
    "sample_count": 10,
}
```

### Including in Performance Reports

Memory metrics should be included in batch execution reports:

```python
# Save to batch_execution_metrics.json
metrics = {"execution": {"total_time": 120.5, "tickers_analyzed": 66, "successful": 64}, "memory": prefetcher.get_memory_metrics(), "cleanup": cleanup_result}

with open("batch_execution_metrics.json", "w") as f:
    json.dump(metrics, f, indent=2)
```

## Best Practices

### 1. Initialize Early

Create the memory manager at the start of batch processing:

```python
prefetcher = BatchDataPreFetcher(session_id=session_id)
# Memory manager is automatically created
```

### 2. Monitor Key Stages

Add monitoring at important stages:

```python
memory_manager.monitor_memory("stage-name")
```

### 3. Check Constraints

Validate memory constraints after completion:

```python
if not prefetcher.validate_memory_constraints():
    logger.warning("Memory limit exceeded")
```

### 4. Always Clean Up

Clean up cache after Flow completion:

```python
try:
    # ... batch processing ...
finally:
    prefetcher.cleanup_cache()
```

### 5. Include in Metrics

Include memory metrics in performance reports:

```python
metrics = prefetcher.get_memory_metrics()
# Save to metrics file
```

## Troubleshooting

### High Memory Usage

If memory usage is high:

1. **Check batch size**: Reduce number of concurrent crews
2. **Disable Alpha Vantage**: Use Yahoo Finance only
3. **Monitor stages**: Identify which stage uses most memory
4. **Force garbage collection**: Call `gc.collect()` between stages

### Memory Limit Exceeded

If memory limit is exceeded:

1. **Review logs**: Check which stage exceeded limit
2. **Reduce batch size**: Process fewer tickers at once
3. **Increase limit**: Adjust `MAX_MEMORY_MB` if system allows
4. **Optimize data structures**: Reduce data stored in memory

### Cleanup Failures

If cache cleanup fails:

1. **Check permissions**: Ensure write access to cache directory
2. **Check disk space**: Ensure sufficient disk space
3. **Manual cleanup**: Remove cache directory manually
4. **Review logs**: Check error messages for details

## Testing

### Unit Tests

Test memory management functionality:

```python
def test_memory_monitoring(tmp_path):
    """Test memory monitoring at different stages."""
    manager = MemoryManager(session_id="test-123")

    # Monitor at different stages
    sample1 = manager.monitor_memory("stage-1")
    assert sample1["within_limit"]

    sample2 = manager.monitor_memory("stage-2")
    assert sample2["peak_mb"] >= sample1["memory_mb"]


def test_cache_cleanup(tmp_path):
    """Test cache cleanup functionality."""
    manager = MemoryManager(session_id="test-123")

    # Create some cache files
    cache_dir = Path(f"cache/batch_data/test-123")
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / "test.json").write_text("{}")

    # Clean up
    result = manager.cleanup_cache()
    assert result["success"]
    assert not cache_dir.exists()


def test_memory_constraints():
    """Test memory constraint validation."""
    manager = MemoryManager(session_id="test-123")

    # Should be within limits initially
    assert manager.validate_memory_constraints()
```

### Integration Tests

Test with actual batch processing:

```python
def test_batch_prefetch_with_memory_management():
    """Test batch prefetch with memory monitoring."""
    prefetcher = BatchDataPreFetcher(session_id="test-123")

    # Pre-fetch data
    data = prefetcher.prefetch_all_data(["AAPL", "MSFT"])

    # Check memory metrics
    metrics = prefetcher.get_memory_metrics()
    assert metrics["within_limit"]
    assert metrics["peak_memory_mb"] < 1024

    # Validate constraints
    assert prefetcher.validate_memory_constraints()

    # Clean up
    cleanup = prefetcher.cleanup_cache()
    assert cleanup["success"]
```

## References

- **Requirements**: 17.70, 17.71, 17.72, 17.73, 17.74
- **Implementation**: `src/finwiz/infrastructure/monitoring/memory_manager.py`
- **Integration**: `src/finwiz/integration/batch_data_prefetcher.py`
- **Configuration**: `src/finwiz/config/batch_prefetch_config.py`

---

**Version**: 1.0
**Last Updated**: 2025-01-25
**Status**: Implemented
