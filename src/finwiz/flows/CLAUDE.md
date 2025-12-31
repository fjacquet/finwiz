# Flows Module

This directory contains CrewAI Flow orchestration logic for coordinating the multi-crew financial analysis pipeline.

## Directory Structure

```
flows/
├── flow_orchestrator.py          # Main Flow entry point
└── hybrid_analysis_synthesizer.py # Result synthesis utilities
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     FinwizFlow (Main)                       │
│                  flow_orchestrator.py                       │
│                                                             │
│  Coordinates 6 phases via orchestrator delegation:          │
│  1. Data Validation → ValidationOrchestrator                │
│  2. Portfolio Review → ValidationOrchestrator               │
│  3. Deep Analysis → DeepAnalysisOrchestrator                │
│  4. Discovery (optional) → DiscoveryOrchestrator            │
│  5. Alternative Matching → AlternativesMatchingOrchestrator │
│  6. Reporting → ReportingOrchestrator                       │
├─────────────────────────────────────────────────────────────┤
│                Functional Analysis Pipeline                 │
│               finwiz.analysis.deep_analysis_pipeline        │
│                                                             │
│  Pure functions with composition (used by orchestrator):    │
│  1. collect_raw_data(ctx) → Python tools fetch raw data     │
│  2. calculate_quantitative(ctx, raw) → Python scorer ($0)   │
│  3. generate_qualitative(ctx, quant) → AI crew call         │
│  4. synthesize(ctx, quant, qual) → Combine results          │
└─────────────────────────────────────────────────────────────┘
```

## Major Entry Points

| File | Class/Function | Purpose |
|------|---------------|---------|
| `flow_orchestrator.py` | `FinwizFlow` | Main workflow orchestrator |
| `flow_orchestrator.py` | `OrchestratorDependencies` | Dependency injection container |
| `flow_orchestrator.py` | `plot()` | Visualize flow structure |
| `hybrid_analysis_synthesizer.py` | `HybridAnalysisSynthesizer` | Synthesis utilities |

## Flow State Management

The flow uses `FinwizState` (Pydantic model) for type-safe state management:

```python
from crewai.flow.flow import Flow, listen, start
from finwiz.flow_state import FinwizState

class FinwizFlow(Flow[FinwizState]):
    @start()
    async def run_sequential_workflow(self) -> dict[str, Any]:
        # Phase 1: Data Validation
        await self.validation_orch.validate_data_integration()

        # Phase 2: Portfolio Review
        await self.validation_orch.check_portfolio()

        # Phase 3: Deep Analysis
        await self.deep_analysis_orch.analyze_and_update_portfolio()

        # ... more phases
        return {"status": "completed"}
```

## Critical Flow Rules

1. **State Access**: Always use `self.state.field_name`, NEVER `self.inputs`
2. **Return Types**: All Flow methods must return `dict[str, Any]`
3. **Type Safety**: Use `Flow[PydanticModel]` for structured state
4. **Orchestrator Delegation**: Flow methods delegate to orchestrators
5. **Lazy Loading**: Orchestrators are lazy-loaded via properties

## Orchestrator Delegation

The flow delegates to specialized orchestrators via lazy-loaded properties:

```python
class FinwizFlow(Flow[FinwizState]):
    @property
    def deep_analysis_orch(self):
        if self._deep_analysis_orch is None:
            from finwiz.orchestrators import DeepAnalysisOrchestrator
            self._deep_analysis_orch = DeepAnalysisOrchestrator(
                state=self.state,
                crew_factory=self.deps.crew_factory,
                # ... other deps
            )
        return self._deep_analysis_orch
```

## Functional Analysis Pipeline (AI Minimalism)

The per-holding analysis uses a functional pipeline in `finwiz.analysis`:

```python
from finwiz.analysis import analyze_holding

# Single function composes the entire pipeline
result, enriched = analyze_holding(
    ticker="AAPL",
    asset_class="stock",
    company_name="Apple Inc."
)

# result: DeepAnalysisResult (grade, score, recommendation)
# enriched: EnrichedAnalysis (full quant + qual for HTML)
```

**Pipeline composition:**
1. `collect_raw_data()` - Python tools ($0)
2. `calculate_quantitative()` - Python scoring ($0)
3. `generate_qualitative()` - AI crew (captures output!)
4. `synthesize_enriched_analysis()` - Combine both ($0)

## Running the Flow

```bash
# Full portfolio analysis
crewai flow kickoff

# Plot flow structure
python -c "from finwiz.flows.flow_orchestrator import plot; plot()"
```

## Testing

```bash
# Test flow orchestration
uv run pytest tests/unit/flows/ -v

# Test with specific state
uv run pytest tests/unit/test_flow_state.py -v

# Test functional pipeline
uv run pytest tests/unit/analysis/ -v
```

## Related Modules

- `finwiz.flow_state` - State management classes
- `finwiz.analysis` - Functional analysis pipeline
- `finwiz.crew_factory` - Crew execution with error handling
- `finwiz.orchestrators` - Specialized orchestration logic
- `finwiz.config.resilience_config` - Retry and resilience configuration
