# Scoring Discovery Module

Discovery pipeline orchestrator that coordinates all discovery components into an end-to-end workflow.

## Directory Structure

```
scoring/discovery/
├── __init__.py       # Exports: NewcomerDiscoveryPipeline
└── pipeline.py       # NewcomerDiscoveryPipeline: orchestrates discovery + enrichment + output
```

## Entry Points

| File | Class | Purpose |
|------|-------|---------|
| `pipeline.py` | `NewcomerDiscoveryPipeline` | Orchestrates universe, screeners, scorer, enrichment, and output |

## Usage

```python
from finwiz.scoring.discovery.pipeline import NewcomerDiscoveryPipeline

pipeline = NewcomerDiscoveryPipeline("stock")
result = pipeline.discover()  # Returns NewcomerDiscoveryResult
```

## Feature Flag

Gated by `newcomer_discovery` feature flag in `config/features/definitions.py`.
When disabled, analyzers fall back to legacy mocked discovery data.

## Related Modules

- `finwiz.discovery` — Individual discovery components (universe, screeners, scorer)
- `finwiz.schemas.newcomer_discovery` — Pydantic schemas for pipeline I/O
- `finwiz.config.features.flags` — `is_feature_enabled("newcomer_discovery")`
- `finwiz.scoring.{stock,etf,crypto}_analyzer` — Callers that route through pipeline when flag enabled
