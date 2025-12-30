# Flows Module

This directory contains CrewAI Flow orchestration logic for coordinating the multi-crew financial analysis pipeline.

## Directory Structure

```
flows/
├── flow_orchestrator.py          # Main Flow entry point
├── hybrid_analysis_flow.py       # Subflow for per-holding Python/AI hybrid analysis
├── hybrid_data_collector.py      # Multi-source data collection
└── hybrid_analysis_synthesizer.py # Result synthesis
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
│                  HybridAnalysisFlow (Subflow)               │
│                 hybrid_analysis_flow.py                     │
│                                                             │
│  Used BY DeepAnalysisOrchestrator for per-holding analysis: │
│  1. collect_data() → Python tools fetch raw data            │
│  2. calculate_quantitative_metrics() → DeepAnalysisScorer   │
│  3. analyze_qualitative_insights() → AI agent (read-only)   │
│  4. synthesize_enriched_analysis() → Combine results        │
└─────────────────────────────────────────────────────────────┘
```

## Major Entry Points

| File | Class/Function | Purpose |
|------|---------------|---------|
| `flow_orchestrator.py` | `FinwizFlow` | Main workflow orchestrator |
| `flow_orchestrator.py` | `OrchestratorDependencies` | Dependency injection container |
| `flow_orchestrator.py` | `plot()` | Visualize flow structure |
| `hybrid_analysis_flow.py` | `HybridAnalysisFlow` | Per-holding Python/AI hybrid analysis |

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

## HybridAnalysisFlow (AI Minimalism)

The `HybridAnalysisFlow` implements AI Minimalism for per-holding analysis:

```python
# Step 1: Python collects data (tools)
raw_data = self._collect_raw_data(ticker, asset_class)

# Step 2: Python calculates scores (DeepAnalysisScorer - $0 cost)
score_result = self.scorer.calculate_composite_score(ticker, asset_class, raw_data)

# Step 3: AI agent receives Python results as READ-ONLY input
crew_inputs = {"quantitative_analysis": score_result}
insights = crew.kickoff(inputs=crew_inputs)

# Step 4: Combine Python quantitative + AI qualitative
final_result = self._synthesize(score_result, insights)
```

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
```

## Related Modules

- `finwiz.flow_state` - State management classes
- `finwiz.crew_factory` - Crew execution with error handling
- `finwiz.orchestrators` - Specialized orchestration logic
- `finwiz.config.resilience_config` - Retry and resilience configuration
