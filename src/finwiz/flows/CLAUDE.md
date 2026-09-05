# Flows Module

CrewAI Flow orchestration — coordinates the multi-crew financial analysis pipeline.

## Directory Structure

```
flows/
├── orchestrator.py                  # MAIN: FinwizFlow, OrchestratorDependencies, plot()
├── hybrid_analysis_synthesizer.py   # HybridAnalysisSynthesizer
└── utils.py                         # get_output_dir(), run_crew_with_caching()
```

**Note:** No `__init__.py` exists. Import directly from files.

## Entry Points

| File | Class/Function | Purpose |
|------|---------------|---------|
| `orchestrator.py` | `FinwizFlow` | Main flow — 6-phase pipeline via orchestrator delegation |
| `orchestrator.py` | `OrchestratorDependencies` | Dependency injection container |
| `orchestrator.py` | `plot()` | Visualize flow structure |
| `hybrid_analysis_synthesizer.py` | `HybridAnalysisSynthesizer` | Synthesis utilities |
| `utils.py` | `run_crew_with_caching()` | Execute crew with cache check |

## Flow Phases

`FinwizFlow` coordinates 6 phases via orchestrator delegation:

1. **Data Validation** → `ValidationOrchestrator`
2. **Portfolio Review** → `portfolio_review_orchestrator.run()` (via `ValidationOrchestrator`)
3. **Deep Analysis** → `DeepAnalysisOrchestrator`
4. **Discovery** → `DiscoveryOrchestrator` — runs unconditionally. The
   `check_crypto` / `check_stock` / `check_etf` methods are plain
   `@listen("check_portfolio")` listeners with no router and no feature gate;
   the `INVESTMENT_DISCOVERY_ENABLED` kill switch was removed.
5. **Alternative Matching** → `AlternativesMatchingOrchestrator`
6. **Reporting** → `ReportingOrchestrator`

## Critical Rules

- **State Access**: Always `self.state.field`, NEVER `self.inputs` (deprecated)
- **Return Types**: All flow methods must return `dict[str, Any]`
- **Orchestrator Delegation**: Flow methods delegate to orchestrators, don't contain business logic
- **Lazy Loading**: Orchestrators are lazy-loaded via `@property`

## Usage

```bash
crewai flow kickoff    # Run full pipeline
```

```python
from finwiz.flows.orchestrator import FinwizFlow, plot

plot()  # Visualize flow structure
```

## Related Modules

- `finwiz.flow_state` — `FinwizState` Pydantic model
- `finwiz.orchestrators` — Business logic orchestrators
- `finwiz.analysis` — Functional analysis pipeline
- `finwiz.crew_factory` — Crew execution
