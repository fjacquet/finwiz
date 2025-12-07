# Utils Module

This directory contains shared utilities, helpers, and cross-cutting concerns used throughout the FinWiz platform.

## Directory Structure

```
utils/
├── flags/                      # Feature flag system
│   ├── flag_definitions.py     # Flag definitions
│   └── flag_evaluators.py      # Flag evaluation logic
│
├── # Agent & Task Decorators
├── agent_validators.py         # @final_reporter decorator
├── task_decorators.py          # @async_task, @sync_task decorators
│
├── # Logging & Monitoring
├── logging_helpers.py          # CrewLogger class
├── enhanced_logger.py          # Enhanced logging
├── monitoring.py               # Performance monitoring
├── monitoring_alerts.py        # Alert system
├── monitoring_metrics.py       # Metrics collection
├── performance_monitor.py      # Performance tracking
├── performance_config.py       # Performance configuration
│
├── # Session Management
├── session_manager.py          # Session lifecycle
├── session_state.py            # Session state
├── session_storage.py          # Session persistence
├── session_persistence.py      # Persistence strategies
├── session_validation.py       # Session validation
├── session_integration.py      # Session integration
│
├── # Caching
├── cache_manager.py            # Main cache manager
├── cache_decorators.py         # @cache_result decorator
├── crew_output_cache.py        # Crew output caching
│
├── # JSON & Data Handling
├── json_repair.py              # LLM JSON output repair
├── json_error_handlers.py      # JSON error handling
├── pydantic_json_loader.py     # Pydantic JSON loading
├── json_to_html_converter.py   # JSON to HTML
│
├── # Flow Utilities
├── flow_state_manager.py       # Flow state management
├── flow_utils.py               # Flow utilities
│
├── # Error Handling
├── core_analysis_error_handler.py  # Crew error handling
├── retry_handler.py            # Retry with backoff
├── timeout_handler.py          # Timeout handling
├── graceful_degradation.py     # Graceful degradation
│
├── # Validation
├── data_consolidation_validator.py  # Data consolidation
├── data_freshness_validator.py      # Data freshness
├── data_quality_metrics.py          # Quality metrics
├── report_data_validator.py         # Report validation
├── optimization_validator.py        # Optimization validation
├── url_validator.py                 # URL validation
│
├── # Data Processing
├── data_extractor.py           # Data extraction
├── deep_analysis_merger.py     # Analysis merging
├── batch_data_prefetcher.py    # Batch data prefetch
├── grading_system.py           # Letter grade system
├── price_targets.py            # Price target calculation
├── risk_metrics.py             # Risk metric utilities
├── etf_expense_fallback.py     # ETF expense fallbacks
├── etf_metrics.py              # ETF metric utilities
├── excellence_hunter.py        # A+ opportunity detection
│
├── # Report Generation
├── final_report_generator.py   # Final report generation
├── report_consolidator.py      # Report consolidation
├── html_generator.py           # HTML generation
├── template_renderer.py        # Template rendering
│
├── # Configuration
├── config_loader.py            # Config loading
├── configuration_manager.py    # Config management
├── feature_flags.py            # Feature flag access
├── llm_config.py               # LLM configuration
│
├── # Rate Limiting
├── rate_limiter.py             # API rate limiting
│
├── # Data Lineage
├── lineage_export.py           # Lineage export
├── lineage_html_integration.py # Lineage HTML
├── lineage_query.py            # Lineage queries
├── lineage_visualizer.py       # Lineage visualization
│
├── # Crew Utilities
├── crew_export_migrator.py     # Export migration
├── freshness_validated_tool.py # Freshness validation
│
├── # Memory Management
├── memory_manager.py           # Memory management
│
├── # API Utilities
├── api_decorators.py           # API decorators
│
├── # CrewAI Patches
├── crewai_json_patch.py        # CrewAI JSON patching
│
├── # A+ Monitoring
├── a_plus_monitoring.py        # A+ monitoring
│
├── # Perplexity Integration
├── perplexity_feature_utils.py # Perplexity utilities
│
├── # Persistence
├── persistence_strategies.py   # Persistence strategies
│
└── # Time Utilities
    └── datetime_utils.py       # Date/time utilities
```

## Major Entry Points

### Agent & Task Decorators

| File | Decorator/Class | Purpose |
|------|----------------|---------|
| `agent_validators.py` | `@final_reporter` | Enforce empty tools for reporters |
| `task_decorators.py` | `@async_task` | Mark task for async execution |
| `task_decorators.py` | `@sync_task` | Mark task for sync execution |

### Logging

| File | Class/Function | Purpose |
|------|---------------|---------|
| `logging_helpers.py` | `CrewLogger` | Standardized crew logging |
| `logging_helpers.py` | `get_logger()` | Get configured logger |

### Caching

| File | Class/Function | Purpose |
|------|---------------|---------|
| `cache_manager.py` | `get_cache_manager()` | Get cache manager instance |
| `cache_decorators.py` | `@cache_result` | Cache function results |
| `crew_output_cache.py` | `get_crew_output_cache()` | Crew output caching |

### Error Handling

| File | Class/Function | Purpose |
|------|---------------|---------|
| `core_analysis_error_handler.py` | `CoreAnalysisErrorHandler` | Crew error handling |
| `retry_handler.py` | `create_retry_decorator()` | Retry with exponential backoff |
| `graceful_degradation.py` | `degrade_gracefully()` | Graceful fallbacks |

### JSON Repair

| File | Function | Purpose |
|------|----------|---------|
| `json_repair.py` | `repair_json()` | Fix malformed LLM JSON output |
| `json_repair.py` | `extract_json()` | Extract JSON from mixed output |

### Feature Flags

| File | Function | Purpose |
|------|----------|---------|
| `feature_flags.py` | `is_feature_enabled()` | Check feature flag status |

## Usage Examples

### Final Reporter Decorator

```python
from finwiz.utils.agent_validators import final_reporter

@final_reporter  # Enforces tools=[]
@agent
def reporter(self) -> Agent:
    return Agent(
        config=self.agents_config["reporter"],
        tools=[],  # Must be empty
        verbose=True
    )
```

### CrewLogger

```python
from finwiz.utils.logging_helpers import CrewLogger

class StockCrew:
    def __init__(self):
        self.logger = CrewLogger("StockCrew")

    def kickoff(self, inputs: dict) -> Any:
        self.logger.log_start(inputs)
        start_time = time.time()

        try:
            result = self.crew().kickoff(inputs=inputs)
            self.logger.log_complete(time.time() - start_time)
            return result
        except Exception as e:
            self.logger.log_error(e)
            raise
```

### Retry Handler

```python
from finwiz.utils.retry_handler import create_retry_decorator

retry = create_retry_decorator(
    max_retries=3,
    base_delay=1.0,
    exponential_base=2.0
)

@retry
def fetch_data(ticker: str) -> dict:
    return api.get_data(ticker)
```

### JSON Repair

```python
from finwiz.utils.json_repair import repair_json, extract_json

# Fix malformed JSON from LLM
raw_output = "Here's the analysis: {\"score\": 0.85, }"
fixed = repair_json(raw_output)  # Removes trailing comma

# Extract JSON from mixed output
text = "Analysis complete. ```json\n{\"result\": \"success\"}\n```"
json_obj = extract_json(text)
```

### Feature Flags

```python
from finwiz.utils.feature_flags import is_feature_enabled

if is_feature_enabled("batch_prefetch"):
    data = batch_prefetcher.prefetch_all(tickers)
else:
    data = {t: fetch_single(t) for t in tickers}
```

### Cache Decorator

```python
from finwiz.utils.cache_decorators import cache_result

@cache_result(ttl_seconds=3600)
def expensive_calculation(ticker: str) -> dict:
    return perform_calculation(ticker)
```

## Testing

```bash
# Test all utilities
uv run pytest tests/unit/utils/ -v

# Test specific utility
uv run pytest tests/unit/utils/test_json_repair.py -v

# Test decorators
uv run pytest tests/unit/utils/test_agent_validators.py -v
```

## Related Modules

- `finwiz.crews` - Uses decorators and logging
- `finwiz.flows` - Uses flow utilities
- `finwiz.integration` - Uses caching and validation
- `finwiz.tools` - Uses error handling
