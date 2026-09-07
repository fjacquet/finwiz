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

The manager is constructed from paths, not from a config object, and reads
whole-crew artifacts — there is no per-ticker accessor.

```python
from finwiz.integration import CrewDataIntegrationManager

manager = CrewDataIntegrationManager(output_dir=Path("output"))
data = manager.get_crew_data_with_freshness_check(crew_name="discovery", max_age_hours=24, warn_on_stale=True)
```

`get_crew_data_with_freshness_check` (`orchestrators/registry/registry_data_retrieval.py:110`)
globs the crew's output directory and returns the **newest** matching file:
`discovery_output_*.json` when `crew_name == "discovery"`, `*.json` otherwise.
It accepts any `crew_name` string and is not validated against a registry, so
`crew_name="stock_crew"` returns `None` — but only because no directory of that
name exists, not because the lookup has no producer.

Producers do exist. `discovery_orchestrator.py:420` writes
`output/discovery/discovery_output_{timestamp}.json`, and `output/stock`,
`output/etf` and `output/crypto` accumulate `{ticker}_enriched.json` from
`deep_analysis_orchestrator.py:381-385`. A separate function,
`get_upstream_data` (same file, line 29), is the one that reads
`output_dir / crew_name / f"{crew_name}_latest.json"`; that name is written by
`tools/analysis/holding_processors.py:243`. The two are easy to confuse and
have different contracts.

For a plain read without the freshness check, use `CrewDataAccessor`. Its
`get_crew_data`/`get_stock_data` generic dispatch (`getattr(self.cache,
f"get_{crew_name}_data")`) was removed in #187 — it broke when
`DataCache.get_stock_data` went. `CrewDataAccessor.get_discovery_data()` now
calls `self.cache.get_discovery_data()` directly. Note this is separate from
`DataCache.get_consolidated_data()`, which still aggregates all five sources
(`stock`, `etf`, `crypto`, `discovery`, `portfolio`):

```python
from finwiz.integration.accessor import CrewDataAccessor

data = CrewDataAccessor(...).get_discovery_data(max_age_hours=24)
```

## Related Modules

- `finwiz.crews` — Crews whose data this module manages
- `finwiz.cache` — Underlying cache layer
- `finwiz.validation` — Data validation rules
- `finwiz.config` — Configuration loading
