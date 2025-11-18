# Orchestrator Interactions

**Version**: 1.0  
**Last Updated**: 2025-01-18  
**Status**: Production

## Overview

This document provides detailed diagrams and explanations of how orchestrators interact within the FinWiz Flow architecture.

## Flow Execution Sequence

### Complete Workflow

```mermaid
sequenceDiagram
    participant User
    participant Flow as FinwizFlow
    participant Val as ValidationOrchestrator
    participant Deep as DeepAnalysisOrchestrator
    participant Alt as AlternativesMatchingOrchestrator
    participant Disc as DiscoveryOrchestrator
    participant Rep as ReportingOrchestrator
    participant State as FinwizState

    User->>Flow: kickoff()
    Flow->>State: Initialize state
    
    Flow->>Val: validate_data_integration()
    Val->>State: Update validation status
    Val-->>Flow: Return validation result
    
    Flow->>Val: check_portfolio()
    Val->>State: Update portfolio data
    Val-->>Flow: Return portfolio result
    
    Flow->>Deep: run_deep_analysis_on_holdings()
    Deep->>State: Update deep_analysis_results
    Deep-->>Flow: Return analysis results
    
    Flow->>Alt: match_alternatives_for_holdings()
    Alt->>State: Update portfolio_alternatives
    Alt-->>Flow: Return alternatives
    
    Flow->>Disc: check_investment_discovery()
    Disc->>State: Update discovery_results
    Disc-->>Flow: Return discovery results
    
    Flow->>Rep: report()
    Rep->>State: Update final_report_path
    Rep-->>Flow: Return report path
    
    Flow-->>User: Return final result
```

### Orchestrator Dependencies

```mermaid
graph TD
    Flow[FinwizFlow]
    
    Flow --> ErrorOrch[ErrorHandlingOrchestrator]
    Flow --> ProgOrch[ProgressTrackingOrchestrator]
    Flow --> UtilOrch[UtilityOrchestrator]
    Flow --> ValOrch[ValidationOrchestrator]
    Flow --> DeepOrch[DeepAnalysisOrchestrator]
    Flow --> AltOrch[AlternativesMatchingOrchestrator]
    Flow --> DiscOrch[DiscoveryOrchestrator]
    Flow --> RepOrch[ReportingOrchestrator]
    
    DeepOrch --> ErrorOrch
    DeepOrch --> ProgOrch
    DeepOrch --> UtilOrch
    
    AltOrch --> UtilOrch
    
    DiscOrch --> ErrorOrch
    
    RepOrch --> UtilOrch
    
    ValOrch --> UtilOrch
    
    style Flow fill:#e1f5ff
    style ErrorOrch fill:#ffe1e1
    style ProgOrch fill:#e1ffe1
    style UtilOrch fill:#fff5e1
    style ValOrch fill:#f5e1ff
    style DeepOrch fill:#e1fff5
    style AltOrch fill:#ffe1f5
    style DiscOrch fill:#f5ffe1
    style RepOrch fill:#e1e1ff
```

## Orchestrator Interactions

### 1. Deep Analysis Flow

```mermaid
sequenceDiagram
    participant Flow
    participant Deep as DeepAnalysisOrchestrator
    participant Error as ErrorHandlingOrchestrator
    participant Prog as ProgressTrackingOrchestrator
    participant Util as UtilityOrchestrator
    participant Crew as CrewFactory
    participant State as FinwizState

    Flow->>Deep: run_deep_analysis_on_holdings(holdings)
    
    loop For each holding
        Deep->>Error: execute_crew_with_error_handling()
        Error->>Crew: Execute deep analysis crew
        Crew-->>Error: Return crew result
        Error-->>Deep: Return wrapped result
        
        Deep->>Util: parse_crew_output_for_holding()
        Util-->>Deep: Return parsed data
        
        Deep->>State: Store analysis result
        
        Deep->>Prog: update_progress()
        Prog->>State: Update progress metrics
    end
    
    Deep->>State: Store all results
    Deep-->>Flow: Return analysis results
```

### 2. Alternative Matching Flow

```mermaid
sequenceDiagram
    participant Flow
    participant Alt as AlternativesMatchingOrchestrator
    participant Util as UtilityOrchestrator
    participant State as FinwizState

    Flow->>Alt: match_alternatives_for_holdings(holdings, discovery)
    
    loop For each holding
        Alt->>Alt: Check grade < B
        
        alt Grade < B
            Alt->>Util: parse_crew_output_for_holding()
            Util-->>Alt: Return parsed alternatives
            Alt->>State: Store alternatives for holding
        else Grade >= B
            Alt->>Alt: Skip (no alternatives needed)
        end
    end
    
    Alt->>State: Store all alternatives
    Alt-->>Flow: Return alternatives map
```

### 3. Discovery Flow

```mermaid
sequenceDiagram
    participant Flow
    participant Disc as DiscoveryOrchestrator
    participant Error as ErrorHandlingOrchestrator
    participant Crew as CrewFactory
    participant State as FinwizState

    Flow->>Disc: check_investment_discovery()
    
    par Parallel Discovery
        Disc->>Error: execute_crew_with_error_handling(crypto_crew)
        Error->>Crew: Execute crypto discovery
        Crew-->>Error: Return crypto results
        Error-->>Disc: Return wrapped results
    and
        Disc->>Error: execute_crew_with_error_handling(stock_crew)
        Error->>Crew: Execute stock discovery
        Crew-->>Error: Return stock results
        Error-->>Disc: Return wrapped results
    and
        Disc->>Error: execute_crew_with_error_handling(etf_crew)
        Error->>Crew: Execute ETF discovery
        Crew-->>Error: Return ETF results
        Error-->>Disc: Return wrapped results
    end
    
    Disc->>Disc: Consolidate all results
    Disc->>State: Store discovery results
    Disc-->>Flow: Return consolidated results
```

### 4. Reporting Flow

```mermaid
sequenceDiagram
    participant Flow
    participant Rep as ReportingOrchestrator
    participant Util as UtilityOrchestrator
    participant State as FinwizState
    participant FS as FileSystem

    Flow->>Rep: report()
    
    Rep->>State: Get crew export paths
    Rep->>Rep: consolidate_reports()
    
    loop For each crew export
        Rep->>FS: Read export file
        FS-->>Rep: Return export data
        Rep->>Util: parse_crew_output()
        Util-->>Rep: Return parsed data
    end
    
    Rep->>Rep: generate_final_report()
    Rep->>Rep: generate_html_from_export()
    
    Rep->>FS: Write HTML report
    Rep->>State: Store report path
    Rep-->>Flow: Return report path
```

## State Management

### State Flow

```mermaid
graph LR
    Init[Initialize State] --> Val[Validation]
    Val --> Deep[Deep Analysis]
    Deep --> Alt[Alternative Matching]
    Alt --> Disc[Discovery]
    Disc --> Rep[Reporting]
    Rep --> Final[Final State]
    
    style Init fill:#e1f5ff
    style Val fill:#f5e1ff
    style Deep fill:#e1fff5
    style Alt fill:#ffe1f5
    style Disc fill:#f5ffe1
    style Rep fill:#e1e1ff
    style Final fill:#ffe1e1
```

### State Updates by Orchestrator

| Orchestrator | State Fields Updated |
|--------------|---------------------|
| ValidationOrchestrator | `validation_complete`, `portfolio_data` |
| DeepAnalysisOrchestrator | `deep_analysis_results`, `deep_analysis_success`, `deep_analysis_error` |
| AlternativesMatchingOrchestrator | `portfolio_alternatives` |
| DiscoveryOrchestrator | `discovery_results` |
| ReportingOrchestrator | `final_report_path`, `crew_export_paths` |
| ProgressTrackingOrchestrator | `holdings_processed`, `total_holdings`, `progress_percentage` |

## Error Handling Flow

```mermaid
sequenceDiagram
    participant Orch as Any Orchestrator
    participant Error as ErrorHandlingOrchestrator
    participant Crew as CrewFactory
    participant State as FinwizState

    Orch->>Error: execute_crew_with_error_handling(crew_func)
    
    Error->>Crew: Execute crew
    
    alt Success
        Crew-->>Error: Return result
        Error->>Error: Wrap success result
        Error-->>Orch: Return {success: true, data: result}
    else Failure
        Crew-->>Error: Raise exception
        Error->>Error: generate_error_summary()
        Error->>State: Store error info
        Error-->>Orch: Return {success: false, error: info}
    end
    
    Orch->>Orch: Handle result
    Orch->>State: Update state accordingly
```

## Progress Tracking Flow

```mermaid
sequenceDiagram
    participant Deep as DeepAnalysisOrchestrator
    participant Prog as ProgressTrackingOrchestrator
    participant State as FinwizState
    participant FS as FileSystem

    Deep->>Prog: update_progress(processed, total)
    Prog->>Prog: Calculate percentage
    Prog->>State: Update progress fields
    Prog->>Prog: Log progress
    
    opt Save Metrics
        Deep->>Prog: save_batch_metrics_to_file(metrics, path)
        Prog->>FS: Write metrics file
    end
```

## Data Parsing Flow

```mermaid
sequenceDiagram
    participant Orch as Any Orchestrator
    participant Util as UtilityOrchestrator
    participant Crew as CrewOutput

    Orch->>Util: parse_crew_output_for_holding(output, ticker)
    Util->>Crew: Access raw output
    Util->>Util: Extract ticker data
    Util->>Util: Parse JSON/Pydantic
    Util->>Util: Validate structure
    Util-->>Orch: Return parsed data
    
    Orch->>Util: calculate_grade_distribution(holdings)
    Util->>Util: Aggregate grades
    Util-->>Orch: Return distribution
    
    Orch->>Util: extract_sec_filing_urls(output)
    Util->>Util: Parse URLs
    Util->>Util: validate_and_fix_sec_urls()
    Util-->>Orch: Return validated URLs
```

## Lazy Loading Pattern

```mermaid
sequenceDiagram
    participant User
    participant Flow as FinwizFlow
    participant Prop as @property
    participant Orch as Orchestrator

    User->>Flow: Access flow.deep_analysis_orch
    Flow->>Prop: Call property getter
    
    alt First Access
        Prop->>Prop: Check if _deep_analysis_orch is None
        Prop->>Orch: Create DeepAnalysisOrchestrator(state, **deps)
        Orch-->>Prop: Return instance
        Prop->>Flow: Store in _deep_analysis_orch
        Prop-->>User: Return orchestrator
    else Subsequent Access
        Prop->>Prop: Check if _deep_analysis_orch is None
        Prop->>Flow: Return cached _deep_analysis_orch
        Prop-->>User: Return orchestrator
    end
```

## Dependency Injection

```mermaid
graph TD
    Flow[FinwizFlow]
    Deps[OrchestratorDependencies]
    
    Flow --> Deps
    
    Deps --> CF[CrewFactory]
    Deps --> IM[IntegrationManager]
    Deps --> EH[ErrorHandler]
    Deps --> SM[StateManager]
    Deps --> RC[ResilienceConfig]
    Deps --> BC[BatchPrefetchConfig]
    
    Orch1[ErrorHandlingOrchestrator]
    Orch2[DeepAnalysisOrchestrator]
    Orch3[ReportingOrchestrator]
    
    Deps -.-> Orch1
    Deps -.-> Orch2
    Deps -.-> Orch3
    
    style Flow fill:#e1f5ff
    style Deps fill:#ffe1e1
    style Orch1 fill:#e1ffe1
    style Orch2 fill:#e1fff5
    style Orch3 fill:#e1e1ff
```

## Communication Patterns

### 1. Synchronous Communication

Most orchestrator interactions are synchronous:

```python
# Flow calls orchestrator
result = self.deep_analysis_orch.run_deep_analysis_on_holdings(holdings)

# Orchestrator calls another orchestrator
wrapped_result = self.error_handler_orch.execute_crew_with_error_handling(
    crew_func, "crew_name"
)
```

### 2. State-Based Communication

Orchestrators communicate through shared state:

```python
# Orchestrator A updates state
self.state.deep_analysis_results = results

# Orchestrator B reads state
results = self.state.deep_analysis_results
```

### 3. Return Value Communication

Flow methods return data for downstream listeners:

```python
@listen("check_portfolio")
def analyze_holdings(self) -> dict[str, Any]:
    results = self.deep_analysis_orch.run_deep_analysis_on_holdings(holdings)
    return {"analysis": results}  # Passed to next listener

@listen("analyze_holdings")
def match_alternatives(self, analysis_data: dict[str, Any]) -> dict[str, Any]:
    results = analysis_data["analysis"]  # Received from upstream
    # Process and return
```

## Performance Considerations

### Lazy Loading Benefits

```mermaid
graph LR
    A[Flow Created] --> B{Orchestrator Accessed?}
    B -->|No| C[No Memory Used]
    B -->|Yes| D[Orchestrator Created]
    D --> E[Cached for Reuse]
    E --> F{Accessed Again?}
    F -->|Yes| G[Return Cached Instance]
    F -->|No| C
```

### Parallel Execution

Discovery crews can run in parallel:

```python
# Parallel execution using asyncio
async def run_discovery():
    crypto_task = asyncio.create_task(check_crypto())
    stock_task = asyncio.create_task(check_stock())
    etf_task = asyncio.create_task(check_etf())
    
    results = await asyncio.gather(
        crypto_task, stock_task, etf_task
    )
    return consolidate_results(results)
```

## Best Practices

### 1. Orchestrator Communication

✅ **DO**:
- Use state for persistent data
- Return data for downstream listeners
- Use error handling orchestrator for crew execution
- Keep orchestrators focused on single responsibility

❌ **DON'T**:
- Create circular dependencies
- Store large data in memory
- Skip error handling
- Mix responsibilities

### 2. State Management

✅ **DO**:
- Update state through orchestrators
- Use Pydantic models for type safety
- Validate state updates
- Document state fields

❌ **DON'T**:
- Modify state directly from Flow
- Use unstructured state
- Skip validation
- Create state inconsistencies

### 3. Error Handling

✅ **DO**:
- Wrap crew executions with error handling
- Log errors with context
- Return structured error info
- Update state with error status

❌ **DON'T**:
- Ignore errors
- Raise unhandled exceptions
- Lose error context
- Skip error logging

## Related Documentation

- [Architecture Documentation](ARCHITECTURE.md)
- [Developer Guide](DEVELOPER_GUIDE.md)
- [Migration Guide](.kiro/specs/flow-orchestrator-refactoring/MIGRATION_GUIDE.md)

---

**Version**: 1.0  
**Last Updated**: 2025-01-18  
**Status**: Production
