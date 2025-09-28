# Core Analysis Performance Tests

This directory contains performance tests for the core analysis functionality, including stock, ETF, and crypto analysis crews.

## Test Categories

### Execution Performance

- Single crew execution time limits
- Parallel crew execution efficiency
- Large dataset handling performance
- Memory usage optimization

### Scalability Tests

- Concurrent crew execution handling
- Feature flag combination scaling
- Data integration system performance
- Error handling performance impact

### Stress Tests

- Large portfolio handling (5000+ holdings)
- High-volume ticker processing (2000+ tickers)
- Extended execution scenarios
- Resource constraint handling

## Running Performance Tests

### All Performance Tests

```bash
uv run pytest tests/performance/core_analysis/ -v
```

### Specific Test Categories

```bash
# Execution performance only
uv run pytest tests/performance/core_analysis/test_core_analysis_performance.py::TestCoreAnalysisPerformance::test_should_execute_single_crew_within_time_limit -v

# Stress tests (marked as slow)
uv run pytest tests/performance/core_analysis/ -m slow -v
```

### Performance Benchmarking

```bash
# Run with timing information
uv run pytest tests/performance/core_analysis/ --durations=10 -v
```

## Performance Expectations

### Execution Time Limits

- Single crew execution: < 5 seconds (mocked)
- All crews parallel execution: < 10 seconds (mocked)
- Large dataset processing: < 8 seconds (mocked)
- Error handling: < 3 seconds

### Memory Usage

- Memory increase during execution: < 100MB
- No significant memory leaks over multiple executions

### Scalability

- Concurrent execution: < 15 seconds for 3 parallel crews
- Feature flag combinations: Linear scaling with enabled crews
- Data integration: < 2 seconds storage, < 1 second retrieval

## Test Environment

These tests use mocked external dependencies to focus on internal performance characteristics. Real-world performance may vary based on:

- Network latency for API calls
- External service response times
- System resources and load
- Data volume and complexity

## Monitoring

Performance tests help identify:

- Performance regressions
- Memory leaks
- Scalability bottlenecks
- Resource optimization opportunities

## Notes

- Tests marked with `@pytest.mark.slow` may take longer to execute
- Performance thresholds are conservative to account for CI/CD environments
- Memory tests require `psutil` package for accurate measurements
- Concurrent tests use threading to simulate parallel execution