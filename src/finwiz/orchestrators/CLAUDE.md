# Orchestrators Module

Business logic orchestration (Application/Service Layer) for coordinating complex multi-step operations. HTML presentation is delegated to `reporting/`.

## Directory Structure

```
orchestrators/
├── __init__.py                          # Module exports
│
├── # Core orchestrators
├── deep_analysis_orchestrator.py        # DeepAnalysisOrchestrator (per-holding analysis)
├── deep_analysis_data_collector.py      # DeepAnalysisDataCollector
├── discovery_orchestrator.py            # DiscoveryOrchestrator (A+ discovery)
├── validation_orchestrator.py           # ValidationOrchestrator
├── reporting_orchestrator.py            # ReportingOrchestrator
├── error_handling_orchestrator.py       # ErrorHandlingOrchestrator
├── progress_tracking_orchestrator.py    # ProgressTrackingOrchestrator
├── utility_orchestrator.py              # Shared utilities
├── alternatives_matching_orchestrator.py # A+ alternatives matching
├── gap_profile_orchestrator.py          # Builds the PortfolioGapProfile discovery scores against
├── batch_prefetch_runner.py             # Bulk data prefetch ahead of deep analysis
├── stress_test_orchestrator.py          # Portfolio stress scenarios
│
├── # Portfolio orchestrators
├── portfolio_review_orchestrator.py     # run()
├── portfolio_rebalancing.py             # run_rebalancing(), calculate_trades()
├── portfolio_holdings_processor.py      # PortfolioHoldingsProcessor
│
├── # Helpers
├── validation_helpers.py                # Validation utilities
│
├── # Subdirectories
├── discovery/                           # Discovery sub-pipeline
│   ├── aplus_discovery_accessor.py
│   ├── aplus_discovery_integrator.py
│   ├── excellence_hunter.py
│   └── extractors/                      # Per-asset extraction
│       ├── base.py                      # BaseExtractor
│       ├── stock_extractor.py
│       ├── etf_extractor.py
│       └── crypto_extractor.py
│
├── error_handling/                      # Error handling subsystem
│   ├── handlers.py                      # ErrorHandlers, ValidationErrorReport
│   ├── recovery.py
│   ├── fallback.py
│   ├── core_analysis_error_handler.py
│   ├── missing_data.py
│   └── validation_recovery.py
│
├── extraction/                          # Data extraction pipeline
│   ├── engine.py
│   ├── parsers.py
│   ├── backtesting.py
│   ├── market_context.py
│   ├── utils.py
│   ├── discovery_methodology.py
│   └── aplus.py
│
├── registry/                            # Orchestration registry
│   ├── registry_manager.py              # RegistryManager
│   ├── registry_execution.py
│   ├── registry_models.py
│   └── registry_data_retrieval.py
│
├── reporting/                           # Report assembly helpers
│   ├── crew_html.py
│   ├── data_loading.py
│   └── enrichment.py
│
└── portfolio_review/                    # Review subsystem
    ├── decisions.py
    └── merge.py
```

## Entry Points

| File | Class/Function | Purpose |
|------|---------------|---------|
| `deep_analysis_orchestrator.py` | `DeepAnalysisOrchestrator` | Per-holding deep analysis + HTML |
| `discovery_orchestrator.py` | `DiscoveryOrchestrator` | A+ investment discovery + opportunity shortlist |
| `gap_profile_orchestrator.py` | `GapProfileOrchestrator` | Phase 3.6 portfolio gap profile for the opportunity cascade |
| `portfolio_review_orchestrator.py` | `run()` | Run portfolio review |
| `reporting_orchestrator.py` | `ReportingOrchestrator` | Report generation and consolidation |
| `error_handling_orchestrator.py` | `ErrorHandlingOrchestrator` | Error handling & recovery |
| `registry/registry_manager.py` | `RegistryManager` | Orchestration registry |

## Usage

Every orchestrator takes `state: FinwizState` as its first positional argument
and reads its inputs from that state — nothing is passed per-call.

```python
from finwiz.orchestrators import DeepAnalysisOrchestrator, DiscoveryOrchestrator

deep_orch = DeepAnalysisOrchestrator(state)
results = await deep_orch.analyze_and_update_portfolio()   # async

discovery_orch = DiscoveryOrchestrator(state)
opportunities = discovery_orch.check_investment_discovery()   # no arguments
```

## Related Modules

- `finwiz.flows` — Flow orchestration (calls orchestrators)
- `finwiz.crews` — CrewAI crews (executed by orchestrators)
- `finwiz.reporting` — HTML generation (delegated from orchestrators)
- `finwiz.flow_state` — State management
