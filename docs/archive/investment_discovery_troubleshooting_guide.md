# Investment Discovery Troubleshooting Guide

## Overview

This guide provides solutions to common issues encountered when working with the A+ Investment Discovery system. It covers setup problems, runtime errors, performance issues, and data quality concerns.

## Quick Diagnostics

### System Health Check

Run the built-in health check to identify common issues:

```bash
# Check system health
uv run python -c "from finwiz.tools.a_plus_scoring_tool import APlusScoringTool; APlusScoringTool().health_check()"

# Check discovery crew status
uv run python -c "from finwiz.crews.investment_discovery_crew import InvestmentDiscoveryCrew; InvestmentDiscoveryCrew().health_check()"

# Validate environment variables
uv run python -c "from finwiz.utils.configuration_manager import ConfigurationManager; ConfigurationManager().validate_discovery_config()"
```

### Log Analysis

Check the discovery logs for errors:

```bash
# View recent discovery logs
tail -f logs/finwiz.log | grep -i "discovery\|a_plus\|scoring"

# Check for specific error patterns
grep -E "(ERROR|CRITICAL)" logs/finwiz.log | grep -i discovery

# View performance metrics
grep "discovery_performance" logs/finwiz.log | tail -20
```

## Common Issues and Solutions

### 1. Setup and Configuration Issues

#### Issue: Missing API Keys

**Symptoms**:

- `EnvironmentError: OPENAI_API_KEY not found`
- `APIConnectionError: Unable to connect to market data provider`
- Discovery crew fails to initialize

**Solution**:

```bash
# Check which API keys are missing
uv run python -c "
import os
required_keys = ['OPENAI_API_KEY', 'ALPHA_VANTAGE_API_KEY', 'SERPER_API_KEY']
missing = [key for key in required_keys if not os.getenv(key)]
print(f'Missing keys: {missing}')
"

# Set missing keys in .env file
echo "OPENAI_API_KEY=your_key_here" >> .env
echo "ALPHA_VANTAGE_API_KEY=your_key_here" >> .env
echo "SERPER_API_KEY=your_key_here" >> .env

# Verify keys are loaded
uv run python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('Keys loaded:', bool(os.getenv('OPENAI_API_KEY')))"
```

#### Issue: Invalid Configuration

**Symptoms**:

- `ValidationError: Invalid scoring criteria`
- `ConfigurationError: Unsupported asset type`
- Crew initialization fails with schema errors

**Solution**:

```python
# Validate configuration
from finwiz.utils.configuration_manager import ConfigurationManager

config_manager = ConfigurationManager()
validation_result = config_manager.validate_discovery_config()

if not validation_result.is_valid:
    print("Configuration errors:")
    for error in validation_result.errors:
        print(f"  - {error}")
    
    # Reset to default configuration
    config_manager.reset_to_defaults()
```

#### Issue: Dependency Conflicts

**Symptoms**:

- `ImportError: cannot import name 'APlusScoringTool'`
- `ModuleNotFoundError: No module named 'crewai'`
- Version conflicts during installation

**Solution**:

```bash
# Clean and reinstall dependencies
rm -rf .venv uv.lock
uv sync --reinstall

# Check for version conflicts
uv run pip check

# Install specific versions if needed
uv add "crewai>=0.28.0" "pydantic>=2.0.0"

# Verify installation
uv run python -c "from finwiz.tools.a_plus_scoring_tool import APlusScoringTool; print('Import successful')"
```

### 2. Runtime Errors

#### Issue: Market Data Unavailable

**Symptoms**:

- `MarketDataError: Unable to fetch data for symbol AAPL`
- `TimeoutError: Request timed out after 30 seconds`
- Empty screening results

**Solution**:

```python
# Check data provider status
from finwiz.tools.market_screening_tool import MarketScreeningTool

screener = MarketScreeningTool()
status = screener.check_data_provider_status()

if not status['yahoo_finance']:
    print("Yahoo Finance unavailable, switching to backup provider")
    screener.set_backup_provider('alpha_vantage')

# Test data retrieval
test_result = screener.test_data_retrieval('AAPL')
print(f"Data retrieval test: {test_result}")
```

**Fallback Strategy**:

```python
# Implement graceful degradation
from finwiz.utils.graceful_degradation import GracefulDegradation

degradation = GracefulDegradation()

# Use cached data if available
if degradation.is_market_data_unavailable():
    print("Using cached market data")
    screener.use_cached_data(max_age_hours=24)
    
# Reduce scope if needed
if degradation.should_reduce_scope():
    print("Reducing discovery scope due to data limitations")
    screener.set_max_candidates(20)  # Reduce from default 50
```

#### Issue: Scoring Calculation Errors

**Symptoms**:

- `ScoringError: Unable to calculate fundamental score`
- `ValueError: Invalid ROE value: -0.5`
- `ZeroDivisionError` in scoring calculations

**Solution**:

```python
# Debug scoring calculation
from finwiz.tools.a_plus_scoring_tool import APlusScoringTool

scorer = APlusScoringTool()

# Test with known good data
test_data = {
    'expense_ratio': 0.05,
    'aum': 5e9,
    'tracking_error': 0.001,
    'history_years': 5
}

try:
    result = scorer._run(
        symbol='TEST',
        asset_type='etf',
        fundamental_data=test_data
    )
    print("Scoring successful:", result['grade'])
except Exception as e:
    print(f"Scoring error: {e}")
    
    # Enable debug mode for detailed error info
    scorer.enable_debug_mode()
    result = scorer._run(
        symbol='TEST',
        asset_type='etf',
        fundamental_data=test_data
    )
```

**Data Validation**:

```python
# Validate input data before scoring
from finwiz.schemas.investment_discovery import validate_fundamental_data

def safe_scoring(symbol: str, asset_type: str, data: dict):
    """Safely score investment with data validation."""
    
    # Validate data
    validation_result = validate_fundamental_data(data, asset_type)
    if not validation_result.is_valid:
        print(f"Data validation failed: {validation_result.errors}")
        return None
    
    # Clean data
    cleaned_data = validation_result.cleaned_data
    
    # Score with error handling
    try:
        return scorer._run(symbol, asset_type, cleaned_data)
    except Exception as e:
        print(f"Scoring failed for {symbol}: {e}")
        return None
```

#### Issue: Memory and Performance Problems

**Symptoms**:

- `MemoryError: Unable to allocate memory`
- Discovery takes longer than 10 minutes
- High CPU usage during screening

**Solution**:

```python
# Monitor memory usage
import psutil
import gc

def monitor_discovery_performance():
    """Monitor discovery performance and memory usage."""
    
    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    print(f"Initial memory usage: {initial_memory:.1f} MB")
    
    # Run discovery with monitoring
    crew = InvestmentDiscoveryCrew()
    
    # Enable batch processing for large datasets
    crew.enable_batch_processing(batch_size=100)
    
    # Set memory limits
    crew.set_memory_limit_mb(2048)
    
    result = crew.kickoff()
    
    final_memory = process.memory_info().rss / 1024 / 1024
    print(f"Final memory usage: {final_memory:.1f} MB")
    print(f"Memory increase: {final_memory - initial_memory:.1f} MB")
    
    # Force garbage collection
    gc.collect()
    
    return result
```

**Performance Optimization**:

```bash
# Run with performance profiling
uv run python -m cProfile -o discovery_profile.prof src/finwiz/main.py --discovery

# Analyze profile
uv run python -c "
import pstats
p = pstats.Stats('discovery_profile.prof')
p.sort_stats('cumulative').print_stats(20)
"

# Enable parallel processing
export FINWIZ_PARALLEL_DISCOVERY=true
export FINWIZ_MAX_WORKERS=4
```

### 3. Data Quality Issues

#### Issue: Inconsistent or Missing Data

**Symptoms**:

- `InsufficientDataError: Missing required field 'expense_ratio'`
- Scoring results vary significantly between runs
- Low confidence scores across all candidates

**Solution**:

```python
# Implement data quality checks
from finwiz.utils.data_quality import DataQualityChecker

def check_data_quality(symbol: str, asset_type: str):
    """Check data quality for a specific investment."""
    
    checker = DataQualityChecker()
    
    # Fetch data from multiple sources
    data_sources = ['yahoo', 'alpha_vantage', 'morningstar']
    data_quality = {}
    
    for source in data_sources:
        try:
            data = checker.fetch_data(symbol, asset_type, source)
            quality_score = checker.assess_quality(data)
            data_quality[source] = {
                'data': data,
                'quality_score': quality_score,
                'completeness': checker.calculate_completeness(data),
                'freshness': checker.calculate_freshness(data)
            }
        except Exception as e:
            print(f"Failed to fetch from {source}: {e}")
    
    # Select best data source
    best_source = max(data_quality.keys(), 
                     key=lambda x: data_quality[x]['quality_score'])
    
    print(f"Best data source for {symbol}: {best_source}")
    return data_quality[best_source]['data']
```

**Data Cleaning**:

```python
# Clean and normalize data
from finwiz.utils.data_cleaning import DataCleaner

cleaner = DataCleaner()

def clean_fundamental_data(raw_data: dict, asset_type: str) -> dict:
    """Clean and normalize fundamental data."""
    
    cleaned_data = cleaner.clean_data(raw_data, asset_type)
    
    # Handle missing values
    cleaned_data = cleaner.impute_missing_values(cleaned_data, asset_type)
    
    # Validate ranges
    cleaned_data = cleaner.validate_ranges(cleaned_data, asset_type)
    
    # Normalize units
    cleaned_data = cleaner.normalize_units(cleaned_data)
    
    return cleaned_data
```

#### Issue: Stale or Outdated Data

**Symptoms**:

- Discovery results don't reflect recent market changes
- Cache hit rate is too high (>90%)
- Scoring based on old financial data

**Solution**:

```python
# Force cache refresh
from finwiz.utils.cache_manager import CacheManager

cache_manager = CacheManager()

# Clear discovery cache
cache_manager.clear_cache('discovery')

# Set shorter TTL for volatile markets
if market_volatility > 25:  # High VIX
    cache_manager.set_ttl('market_data', hours=1)  # Refresh hourly
else:
    cache_manager.set_ttl('market_data', hours=6)  # Standard 6-hour refresh

# Force fresh data retrieval
screener = MarketScreeningTool()
screener.force_fresh_data = True
```

### 4. Integration Issues

#### Issue: Portfolio Integration Failures

**Symptoms**:

- `IntegrationError: Unable to integrate discoveries with portfolio`
- Recommendations don't match portfolio constraints
- Grade improvements not calculated correctly

**Solution**:

```python
# Debug portfolio integration
from finwiz.orchestrators.portfolio_review import PortfolioReviewOrchestrator

def debug_portfolio_integration(portfolio_data: dict):
    """Debug portfolio integration issues."""
    
    orchestrator = PortfolioReviewOrchestrator()
    
    # Validate portfolio data
    validation_result = orchestrator.validate_portfolio_data(portfolio_data)
    if not validation_result.is_valid:
        print("Portfolio validation errors:")
        for error in validation_result.errors:
            print(f"  - {error}")
        return
    
    # Test discovery integration
    try:
        discoveries = orchestrator.get_recent_discoveries()
        integration_result = orchestrator.integrate_discoveries(
            portfolio_data, discoveries
        )
        print(f"Integration successful: {len(integration_result.improvements)} improvements found")
    except Exception as e:
        print(f"Integration failed: {e}")
        
        # Enable detailed logging
        orchestrator.enable_debug_logging()
        integration_result = orchestrator.integrate_discoveries(
            portfolio_data, discoveries
        )
```

#### Issue: Report Generation Problems

**Symptoms**:

- `ReportError: Unable to generate discovery report`
- Missing discovery section in portfolio reports
- French language formatting issues

**Solution**:

```python
# Test report generation
from finwiz.tools.html_report_generator import HTMLReportGenerator

def test_discovery_report_generation():
    """Test discovery report generation."""
    
    generator = HTMLReportGenerator()
    
    # Create test discovery data
    test_discoveries = {
        'etf_discoveries': [
            {
                'symbol': 'VTI',
                'grade': 'A+',
                'score': 0.96,
                'rationale': ['Excellent expense ratio', 'Strong tracking']
            }
        ],
        'portfolio_improvements': [
            {
                'current_holding': 'SPY',
                'recommended_replacement': 'VTI',
                'grade_improvement': 0.15
            }
        ]
    }
    
    try:
        report_html = generator.generate_discovery_section(test_discoveries)
        print("Report generation successful")
        
        # Validate French language elements
        if 'Opportunités A+' in report_html:
            print("French language formatting correct")
        else:
            print("Warning: French language formatting may be incorrect")
            
    except Exception as e:
        print(f"Report generation failed: {e}")
        
        # Enable template debugging
        generator.enable_template_debugging()
        report_html = generator.generate_discovery_section(test_discoveries)
```

### 5. Performance Optimization

#### Issue: Slow Discovery Performance

**Symptoms**:

- Discovery takes longer than 10 minutes
- High API usage and rate limiting
- Timeout errors during screening

**Optimization Strategies**:

```python
# Enable parallel processing
from finwiz.processing.parallel_discovery import ParallelDiscoveryProcessor

processor = ParallelDiscoveryProcessor(max_workers=4)

# Use async processing for I/O operations
import asyncio

async def optimized_discovery():
    """Run optimized discovery with parallel processing."""
    
    # Parallel asset type discovery
    tasks = [
        processor.discover_etfs_async(),
        processor.discover_stocks_async(),
        processor.discover_crypto_async()
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle any exceptions
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"Discovery failed for asset type {i}: {result}")
    
    return [r for r in results if not isinstance(r, Exception)]

# Run optimized discovery
results = asyncio.run(optimized_discovery())
```

**Caching Optimization**:

```python
# Optimize caching strategy
from finwiz.utils.cache_manager import CacheManager

cache_manager = CacheManager()

# Pre-warm cache with common queries
cache_manager.pre_warm_cache([
    'market_regime',
    'vix_level',
    'interest_rates',
    'top_etfs_by_aum',
    'sp500_constituents'
])

# Use intelligent cache invalidation
cache_manager.enable_smart_invalidation()

# Monitor cache performance
cache_stats = cache_manager.get_cache_statistics()
print(f"Cache hit rate: {cache_stats['hit_rate']:.2%}")
print(f"Average response time: {cache_stats['avg_response_time']:.2f}ms")
```

### 6. Monitoring and Alerting

#### Setting Up Monitoring

```python
# Set up discovery monitoring
from finwiz.monitoring.discovery_monitor import DiscoveryMonitor

monitor = DiscoveryMonitor()

# Configure alerts
monitor.configure_alerts({
    'discovery_failure_rate': {
        'threshold': 0.10,  # 10% failure rate
        'action': 'email_admin'
    },
    'discovery_duration': {
        'threshold': 600,  # 10 minutes
        'action': 'slack_notification'
    },
    'a_plus_discovery_rate': {
        'threshold': 0.05,  # Less than 5% A+ discoveries
        'action': 'investigate'
    }
})

# Start monitoring
monitor.start_monitoring()
```

#### Health Checks

```python
# Implement comprehensive health checks
from finwiz.health.discovery_health import DiscoveryHealthChecker

def run_health_checks():
    """Run comprehensive health checks."""
    
    checker = DiscoveryHealthChecker()
    
    health_results = {
        'api_connectivity': checker.check_api_connectivity(),
        'data_freshness': checker.check_data_freshness(),
        'scoring_accuracy': checker.check_scoring_accuracy(),
        'cache_performance': checker.check_cache_performance(),
        'memory_usage': checker.check_memory_usage(),
        'disk_space': checker.check_disk_space()
    }
    
    # Generate health report
    overall_health = all(health_results.values())
    
    if not overall_health:
        print("Health check failures detected:")
        for check, result in health_results.items():
            if not result:
                print(f"  - {check}: FAILED")
    else:
        print("All health checks passed")
    
    return health_results
```

## Emergency Procedures

### System Recovery

If the discovery system becomes completely unresponsive:

```bash
# 1. Stop all discovery processes
pkill -f "investment_discovery"

# 2. Clear all caches
rm -rf cache/discovery/*
rm -rf cache/market_data/*

# 3. Reset configuration to defaults
uv run python -c "
from finwiz.utils.configuration_manager import ConfigurationManager
ConfigurationManager().reset_to_defaults()
"

# 4. Restart with minimal configuration
export FINWIZ_DISCOVERY_MODE=minimal
export FINWIZ_MAX_CANDIDATES=10
uv run python src/finwiz/main.py --discovery --safe-mode
```

### Data Corruption Recovery

If data corruption is suspected:

```python
# Validate and repair data
from finwiz.utils.data_repair import DataRepairTool

repair_tool = DataRepairTool()

# Check for corruption
corruption_report = repair_tool.check_data_integrity()

if corruption_report.has_corruption:
    print("Data corruption detected:")
    for issue in corruption_report.issues:
        print(f"  - {issue}")
    
    # Attempt automatic repair
    repair_result = repair_tool.auto_repair()
    
    if repair_result.success:
        print("Data repair successful")
    else:
        print("Manual intervention required")
        print("Backup and restore from last known good state")
```

## Getting Help

### Debug Information Collection

When reporting issues, collect this debug information:

```bash
# Create debug package
uv run python -c "
from finwiz.debug.info_collector import DebugInfoCollector

collector = DebugInfoCollector()
debug_package = collector.collect_debug_info()
print(f'Debug package created: {debug_package}')
"
```

### Support Channels

1. **Internal Documentation**: Check existing docs in `docs/` directory
2. **Code Comments**: Review inline documentation in source code
3. **Test Cases**: Examine test files for usage examples
4. **Configuration Examples**: Check `config/` directory for examples

### Escalation Process

For critical issues:

1. **Immediate**: Implement emergency procedures above
2. **Short-term**: Enable safe mode and reduced functionality
3. **Long-term**: Analyze logs and implement permanent fixes

---

This troubleshooting guide covers the most common issues encountered with the A+ Investment Discovery system. For additional technical details, see the [Developer Guide](investment_discovery_developer_guide.md) and [API Reference](investment_discovery_api_reference.md).
