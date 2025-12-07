# Flows Module

This directory contains CrewAI Flow orchestration logic for coordinating the multi-crew financial analysis pipeline.

## Directory Structure

```
flows/
├── flow_orchestrator.py           # Main entry point (backward compat layer)
├── flow_orchestrator_refactored.py # Actual Flow implementation
├── flow_orchestrator_original.py.bak  # Legacy backup
└── hybrid_analysis_flow.py        # Hybrid Python/AI analysis flow
```

## Major Entry Points

| File | Class/Function | Purpose |
|------|---------------|---------|
| `flow_orchestrator.py` | `FinwizFlow` | Main Flow class (re-exported from refactored) |
| `flow_orchestrator.py` | `plot()` | Visualize flow structure |
| `flow_orchestrator_refactored.py` | `FinwizFlow` | Actual implementation with orchestrator delegation |
| `flow_orchestrator_refactored.py` | `OrchestratorDependencies` | Dependency injection container |
| `hybrid_analysis_flow.py` | `HybridAnalysisFlow` | Python/AI hybrid analysis coordination |

## Flow Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     FinwizFlow                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │ @start() initialize                              │   │
│  └─────────────────┬───────────────────────────────┘   │
│                    │                                    │
│  ┌─────────────────▼───────────────────────────────┐   │
│  │ @listen() validate_data_integration              │   │
│  └─────────────────┬───────────────────────────────┘   │
│                    │                                    │
│  ┌─────────────────▼───────────────────────────────┐   │
│  │ @listen() check_portfolio                        │   │
│  └─────────────────┬───────────────────────────────┘   │
│                    │                                    │
│  ┌─────────────────▼───────────────────────────────┐   │
│  │ @listen() Core Analysis (parallel)              │   │
│  │  ├── check_stock                                │   │
│  │  ├── check_etf                                  │   │
│  │  └── check_crypto                               │   │
│  └─────────────────┬───────────────────────────────┘   │
│                    │                                    │
│  ┌─────────────────▼───────────────────────────────┐   │
│  │ @listen() Deep Analysis                         │   │
│  │  └── analyze_holdings_deep (per-holding)        │   │
│  └─────────────────┬───────────────────────────────┘   │
│                    │                                    │
│  ┌─────────────────▼───────────────────────────────┐   │
│  │ @listen() check_portfolio_rebalancing           │   │
│  └─────────────────┬───────────────────────────────┘   │
│                    │                                    │
│  ┌─────────────────▼───────────────────────────────┐   │
│  │ @listen() check_investment_discovery            │   │
│  └─────────────────┬───────────────────────────────┘   │
│                    │                                    │
│  ┌─────────────────▼───────────────────────────────┐   │
│  │ @listen() generate_final_report                 │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Flow State Management

The flow uses `FinwizState` (Pydantic model) for type-safe state management:

```python
from crewai.flow.flow import Flow, listen, start
from finwiz.flow_state import FinwizState

class FinwizFlow(Flow[FinwizState]):
    @start()
    def initialize(self) -> dict[str, Any]:
        # Update structured state
        self.state.portfolio_review = {}
        # Return for downstream listeners
        return {"status": "initialized"}

    @listen(initialize)
    def next_step(self, data: dict[str, Any]) -> dict[str, Any]:
        # Access state via self.state
        review = self.state.portfolio_review
        return {"result": "processed"}
```

## Critical Flow Rules

1. **State Access**: Always use `self.state.field_name`, NEVER `self.inputs`
2. **Return Types**: All Flow methods must return `dict[str, Any]`
3. **Type Safety**: Use `Flow[PydanticModel]` for structured state
4. **Direct Crew Instantiation**: Use `StockCrew()` not factory patterns
5. **Atomic Operations**: Consolidate related operations into single methods

## Orchestrator Delegation

The flow delegates to specialized orchestrators:

```python
from finwiz.orchestrators import (
    DeepAnalysisOrchestrator,
    DiscoveryOrchestrator,
    ReportingOrchestrator,
    ValidationOrchestrator,
)

class FinwizFlow(Flow[FinwizState]):
    def __init__(self):
        self.deep_analysis_orch = DeepAnalysisOrchestrator()
        self.discovery_orch = DiscoveryOrchestrator()
        # ...
```

## Hybrid Analysis Flow

The `HybridAnalysisFlow` coordinates Python-based scoring with AI analysis:

```python
# Python scoring (deterministic, fast, free)
scorer = DeepAnalysisScorer()
score_result = scorer.calculate_composite_score(ticker, asset_class, data)

# AI analysis (reasoning, slow, costly) - only when needed
if needs_ai_insights:
    crew = DeepAnalysisCrew()
    insights = crew.crew().kickoff(inputs)
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
