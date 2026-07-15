# Integration Module

Crew data integration layer — manages data flow between CrewAI crews, caches, and external sources.

## Directory Structure

```
integration/
├── __init__.py                       # Module exports
├── manager.py                        # CrewDataIntegrationManager (main orchestrator)
├── accessor.py                       # CrewDataAccessor (read interface)
├── extractor.py                      # CrewDataExtractor (output parsing)
├── config.py                         # IntegrationConfig, CrewDependencyConfig, DataQualityConfig
├── schema.py                         # SchemaManager (schema registry)
├── cache.py                          # DataCache
├── validation.py                     # DataValidator
├── availability.py                   # DataAvailabilityTracker, SourceStatus
├── middleware.py                     # CrewIntegrationMiddleware (pre/post execution)
├── transformation.py                 # Data consolidation & serialization helpers
├── batch_data_prefetcher.py          # BatchDataPreFetcher (bulk data loading)
├── backtesting_pipeline_connector.py # connect_backtesting_to_discovery_results()
└── cli.py                            # CLI commands: health, validate, status, analyze
```

## Entry Points

| File | Class/Function | Purpose |
|------|---------------|---------|
| `manager.py` | `CrewDataIntegrationManager` | Central coordinator for crew data flow |
| `accessor.py` | `CrewDataAccessor` | Read-only access to crew data |
| `extractor.py` | `CrewDataExtractor` | Parse and extract crew output |
| `config.py` | `get_integration_config()` | Get integration settings |
| `middleware.py` | `CrewIntegrationMiddleware` | Pre/post crew execution hooks |
| `batch_data_prefetcher.py` | `BatchDataPreFetcher` | Prefetch data in bulk before crew execution |
| `cli.py` | `main()` | CLI entry (`cmd_health`, `cmd_validate`, `cmd_status`) |

## Usage

```python
from finwiz.integration import CrewDataIntegrationManager, get_integration_config

config = get_integration_config()
manager = CrewDataIntegrationManager(config)
data = manager.get_crew_data(crew_name="stock_crew", ticker="AAPL")
```

## Related Modules

- `finwiz.crews` — Crews whose data this module manages
- `finwiz.cache` — Underlying cache layer
- `finwiz.validation` — Data validation rules
- `finwiz.config` — Configuration loading
