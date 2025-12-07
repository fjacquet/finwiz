# Integration Module

This directory contains data integration, validation, and cross-crew data management functionality.

## Directory Structure

```
integration/
├── opportunity_extractors/      # A+ opportunity extraction
│   ├── base.py                  # Base extractor interface
│   ├── stock_extractor.py       # Stock opportunity extraction
│   ├── etf_extractor.py         # ETF opportunity extraction
│   └── crypto_extractor.py      # Crypto opportunity extraction
│
├── # Core Integration
├── manager.py                   # MAIN: CrewDataIntegrationManager
├── data_accessor.py             # CrewDataAccessor for reading
├── data_cache.py                # Caching layer
├── data_validation.py           # Data validation
├── data_transformation.py       # Data transformation
├── data_availability_tracker.py # Track data availability
├── data_lineage.py              # Data lineage tracking
│
├── # A+ Discovery Integration
├── aplus_discovery_accessor.py  # A+ data access
├── aplus_discovery_integrator.py # A+ integration
├── aplus_extractor.py           # A+ extraction
├── discovery_methodology_extractor.py # Discovery methods
├── market_context_extractor.py  # Market context
│
├── # Extraction Engine
├── extraction_engine.py         # Main extraction logic
├── extraction_parsers.py        # Data parsers
├── extraction_utils.py          # Extraction utilities
│
├── # Backtesting Integration
├── backtesting_extractor.py     # Backtest data extraction
├── backtesting_pipeline_connector.py # Pipeline connection
│
├── # Validation Pipeline
├── validation_manager.py        # Validation management
├── validation_pipeline.py       # Validation pipeline
├── validation_rules.py          # Validation rules
├── validation_scripts.py        # Validation scripts
├── validation_error_recovery.py # Error recovery
│
├── # Health & Monitoring
├── health_checker.py            # Health checking
├── health_checks.py             # Health check definitions
├── health_monitoring.py         # Health monitoring
├── freshness_checker.py         # Data freshness
├── performance_metrics_aggregator.py # Metrics aggregation
│
├── # Logging & Middleware
├── log_analyzer.py              # Log analysis
├── log_config.py                # Log configuration
├── log_formatters.py            # Log formatting
├── log_handlers.py              # Log handlers
├── logging_utils.py             # Logging utilities
├── middleware.py                # Integration middleware
│
├── # Error Handling
├── error_handlers.py            # Error handling
├── fallback_handlers.py         # Fallback strategies
├── missing_data_handler.py      # Missing data handling
├── recovery_strategies.py       # Recovery strategies
│
├── # Schema & Registry
├── schema_manager.py            # Schema management
├── registry_manager.py          # Registry management
│
├── # Pipeline & Storage
├── pipeline_stages.py           # Pipeline stages
├── storage.py                   # Data storage
│
├── # SEC & Validation
├── sec_citation_validator.py    # SEC citation validation
│
├── # HTML Generation
├── html_auto_generator.py       # Auto HTML generation
│
├── # CLI
├── cli.py                       # Integration CLI
│
└── # Configuration
    └── config.py                # Integration config
```

## Major Entry Points

### Core Integration

| File | Class | Purpose |
|------|-------|---------|
| `manager.py` | `CrewDataIntegrationManager` | Main integration manager |
| `data_accessor.py` | `CrewDataAccessor` | Read crew output data |
| `data_cache.py` | `IntegrationCache` | Caching layer |
| `data_availability_tracker.py` | `DataAvailabilityTracker` | Track data availability |

### A+ Discovery

| File | Class | Purpose |
|------|-------|---------|
| `aplus_discovery_integrator.py` | `APlusDiscoveryIntegrator` | Integrate A+ data |
| `aplus_discovery_accessor.py` | `APlusDiscoveryAccessor` | Access A+ data |
| `aplus_extractor.py` | `APlusExtractor` | Extract A+ opportunities |

### Validation

| File | Class | Purpose |
|------|-------|---------|
| `validation_manager.py` | `ValidationManager` | Manage validation |
| `validation_pipeline.py` | `ValidationPipeline` | Run validations |
| `validation_rules.py` | `ValidationRule` | Define rules |

## Usage

### CrewDataIntegrationManager

```python
from finwiz.integration.manager import CrewDataIntegrationManager

manager = CrewDataIntegrationManager()

# Store crew output
manager.store_crew_output("stock", crew_result)

# Get crew data with freshness check
data = manager.get_crew_data_with_freshness_check(
    crew_name="stock",
    max_age_hours=24,
    warn_on_stale=True
)

# Check data availability
availability = manager.check_data_availability()
```

### CrewDataAccessor

```python
from finwiz.integration.data_accessor import CrewDataAccessor

accessor = CrewDataAccessor()

# Get all available crew data
all_data = accessor.get_all_crew_data()

# Get specific crew data
stock_data = accessor.get_crew_data("stock")

# Get with validation
validated = accessor.get_validated_crew_data("stock")
```

### Data Availability Tracking

```python
from finwiz.integration.data_availability_tracker import DataAvailabilityTracker

tracker = DataAvailabilityTracker()

# Check upstream data availability
status = tracker.check_upstream_data(
    required_crews=["stock", "etf", "crypto"]
)

# Get stale data warnings
warnings = tracker.get_stale_data_warnings()

# Get refresh recommendations
recommendations = tracker.get_refresh_recommendations()
```

### Validation Pipeline

```python
from finwiz.integration.validation_pipeline import ValidationPipeline
from finwiz.integration.validation_rules import RequiredFieldsRule

pipeline = ValidationPipeline()

# Add validation rules
pipeline.add_rule(RequiredFieldsRule(["ticker", "score", "grade"]))

# Validate data
result = pipeline.validate(crew_data)
if not result.is_valid:
    for error in result.errors:
        print(f"Validation error: {error}")
```

## Data Flow

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│   Crews     │ --> │ IntegrationMgr   │ --> │   Storage   │
│ (raw data)  │     │ (validate/cache) │     │  (JSON)     │
└─────────────┘     └──────────────────┘     └─────────────┘
                            │
                            ▼
                    ┌──────────────────┐
                    │  DataAccessor    │
                    │ (read/transform) │
                    └──────────────────┘
                            │
                            ▼
                    ┌──────────────────┐
                    │   Downstream     │
                    │  (flows/reports) │
                    └──────────────────┘
```

## Testing

```bash
# Test integration module
uv run pytest tests/unit/integration/ -v

# Test specific component
uv run pytest tests/unit/integration/test_manager.py -v

# Test validation pipeline
uv run pytest tests/unit/integration/test_validation_pipeline.py -v
```

## Related Modules

- `finwiz.data` - Data acquisition layer
- `finwiz.crews` - Crew output producers
- `finwiz.flows` - Flow consumers
- `finwiz.validation` - Additional validation
