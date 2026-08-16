# Scoring Discovery Module

Discovery pipeline orchestrator that coordinates all discovery components into an end-to-end workflow.

## Directory Structure

```
scoring/discovery/
├── __init__.py                # Exports: NewcomerDiscoveryPipeline
├── pipeline.py                # NewcomerDiscoveryPipeline: orchestrates discovery + enrichment + output
└── portfolio_fit_scorer.py    # PortfolioFitScorer: marginal fit to current portfolio (gap-fill ranking)
```

## Portfolio-Aware Opportunity Cascade

When the ``portfolio_aware_discovery`` feature flag is enabled (default), the
pipeline scores the WHOLE universe by ``standalone_factor x portfolio_fit``
(`_gather_portfolio_aware_candidates`) instead of signal-gated screening:
breakout/momentum become factor *inputs*, not filters, so recall is no longer
gated. `PortfolioFitScorer` consumes the `PortfolioGapProfile` built by
`GapProfileOrchestrator` (Phase 3.6, persisted to `output/discovery/gap_profile.json`).
Flag off → legacy signal-gated path.

## Entry Points

| File | Class | Purpose |
|------|-------|---------|
| `pipeline.py` | `NewcomerDiscoveryPipeline` | Orchestrates universe, screeners, scorer, enrichment, and output |

## Usage

```python
from finwiz.scoring.discovery.pipeline import NewcomerDiscoveryPipeline

pipeline = NewcomerDiscoveryPipeline("stock")
result = pipeline.discover(session_id)  # session_id is required
```

## Screener Wiring

The pipeline composes 5 live components from `finwiz.discovery.*`:

1. `DynamicUniverseProvider.get_universe()` — builds ticker universe (excluding portfolio).
2. `BreakoutDetector.detect(universe)` — breakout-signal candidates.
3. `MomentumScanner.scan(universe)` — momentum-signal candidates.
4. `IPOScreener.screen()` — SEC EDGAR S-1 IPO candidates (stock only).
5. `CandidateScorer.score_and_grade(candidates)` — blended scoring + grading.

## Feature Flag

The `newcomer_discovery` flag has been retired and is no longer read anywhere
in the codebase — `analyze_{stock,etf,crypto}_opportunities()` always route
through `NewcomerDiscoveryPipeline` unconditionally. A pipeline failure returns
an empty, honestly-labelled result (`performance_metrics.method ==
"newcomer_discovery_failed"`) — never mocked/invented data. The pipeline's own
recall strategy is still governed by `portfolio_aware_discovery` (see above).

## Related Modules

- `finwiz.discovery` — Individual discovery components (universe, screeners, scorer)
- `finwiz.schemas.newcomer_discovery` — Pydantic schemas for pipeline I/O
- `finwiz.config.features.flags` — `is_feature_enabled("portfolio_aware_discovery")`
- `finwiz.scoring.{stock,etf,crypto}_analyzer` — Callers that always route through the pipeline (no flag gate)
