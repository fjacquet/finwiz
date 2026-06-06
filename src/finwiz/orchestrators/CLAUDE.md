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
│
├── # Portfolio orchestrators
├── portfolio_review_orchestrator.py     # EnhancedPortfolioReviewOrchestrator, run(), run_with_rebalancing()
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
└── portfolio_review/                    # Review subsystem
    └── decisions.py
```

## Entry Points

| File | Class/Function | Purpose |
|------|---------------|---------|
| `deep_analysis_orchestrator.py` | `DeepAnalysisOrchestrator` | Per-holding deep analysis + HTML |
| `discovery_orchestrator.py` | `DiscoveryOrchestrator` | A+ investment discovery + opportunity shortlist |
| `gap_profile_orchestrator.py` | `GapProfileOrchestrator` | Phase 3.6 portfolio gap profile for the opportunity cascade |
| `portfolio_review_orchestrator.py` | `run()` | Run portfolio review |
| `portfolio_review_orchestrator.py` | `run_with_rebalancing()` | Review + rebalancing |
| `reporting_orchestrator.py` | `ReportingOrchestrator` | Report generation and consolidation |
| `error_handling_orchestrator.py` | `ErrorHandlingOrchestrator` | Error handling & recovery |
| `registry/registry_manager.py` | `RegistryManager` | Orchestration registry |

## Usage

```python
from finwiz.orchestrators import DeepAnalysisOrchestrator, DiscoveryOrchestrator

deep_orch = DeepAnalysisOrchestrator()
results = deep_orch.analyze_all_holdings(holdings=holdings, state=state)

discovery_orch = DiscoveryOrchestrator()
opportunities = discovery_orch.check_investment_discovery(session_id, state)
```

## Related Modules

- `finwiz.flows` — Flow orchestration (calls orchestrators)
- `finwiz.crews` — CrewAI crews (executed by orchestrators)
- `finwiz.reporting` — HTML generation (delegated from orchestrators)
- `finwiz.flow_state` — State management
