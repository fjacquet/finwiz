# Flow Execution Architecture - Report Aggregation

## Overview

This document describes the parallel execution architecture for the FinWiz Flow with report aggregation capabilities.

## Current Flow Structure

### Phase 1: Data Validation
```
@start("validate_data_integration")
└── validate_data_integration()
```

### Phase 2: Portfolio Analysis
```
@listen("validate_data_integration")
└── check_portfolio()  [ASYNC - parallel holdings processing]
    └── Analyzes current holdings
    └── Generates initial portfolio review
```

### Phase 3: Deep Analysis & Portfolio Update
```
@listen("check_portfolio")
└── analyze_and_update_portfolio()  [ASYNC]
    └── Runs deep analysis on underperforming holdings
    └── Matches alternatives for poor performers
    └── Updates portfolio review with enriched data
```

### Phase 4: Discovery Crews (PARALLEL)
```
@listen("analyze_and_update_portfolio")
├── check_crypto()  [Parallel execution]
├── check_stock()   [Parallel execution]
└── check_etf()     [Parallel execution]
```

**Key Point**: These three discovery crews execute **concurrently** because they all listen to the same trigger (`analyze_and_update_portfolio`) and have no dependencies on each other.

### Phase 5: Investment Discovery (Waits for ALL Discovery Crews)
```
@listen(and_("check_crypto", "check_stock", "check_etf"))
└── check_investment_discovery()
    └── Waits for ALL three discovery crews to complete
    └── Consolidates A+ opportunities
```

### Phase 6: Alternative Matching
```
@listen("check_investment_discovery")
└── match_alternatives_after_discovery()
    └── Matches alternatives for holdings
```

### Phase 7: Portfolio Rebalancing
```
@listen("match_alternatives_after_discovery")
└── check_portfolio_rebalancing()
    └── Analyzes portfolio rebalancing opportunities
```

### Phase 8: Report Consolidation (NEW - Python, NO AI)
```
@listen("check_portfolio_rebalancing")
└── consolidate_reports()  [Pure Python]
    └── Reads all crew JSON exports
    └── Validates against Pydantic schemas
    └── Creates ConsolidatedReportExport
    └── Saves consolidated JSON
```

### Phase 9: Final Report Generation (NEW - Python Template, NO AI)
```
@listen("consolidate_reports")
└── generate_final_report()  [Pure Python]
    └── Loads consolidated JSON
    └── Renders Jinja2 template (French)
    └── Saves final HTML report
```

### Phase 10: Reporter Validation & Execution
```
@listen("check_portfolio_rebalancing")
└── pre_validate_reporter_input()
    └── Validates data for reporter crew

@listen("pre_validate_reporter_input")
└── report()
    └── Generates final report using reporter crew
```

## Parallel Execution Patterns

### Pattern 1: Same Trigger = Parallel Execution

When multiple methods listen to the **same trigger**, they execute **in parallel**:

```python
@listen("analyze_and_update_portfolio")
def check_crypto(self):
    # Executes in parallel with check_stock and check_etf
    pass

@listen("analyze_and_update_portfolio")
def check_stock(self):
    # Executes in parallel with check_crypto and check_etf
    pass

@listen("analyze_and_update_portfolio")
def check_etf(self):
    # Executes in parallel with check_crypto and check_stock
    pass
```

### Pattern 2: and_() = Wait for ALL

When a method uses `and_()`, it waits for **ALL** specified methods to complete:

```python
@listen(and_("check_crypto", "check_stock", "check_etf"))
def check_investment_discovery(self):
    # Waits for ALL three discovery crews to complete
    # Only executes after check_crypto AND check_stock AND check_etf finish
    pass
```

### Pattern 3: Sequential Chain

When methods listen to different triggers in sequence, they execute **sequentially**:

```python
@listen("check_investment_discovery")
def match_alternatives_after_discovery(self):
    # Executes AFTER check_investment_discovery completes
    pass

@listen("match_alternatives_after_discovery")
def check_portfolio_rebalancing(self):
    # Executes AFTER match_alternatives_after_discovery completes
    pass
```

## Crew Dependencies

### No Dependencies (Parallel)
- `check_crypto`, `check_stock`, `check_etf` - Run in parallel
- No crew depends on another's output
- Each crew performs independent discovery

### Sequential Dependencies
- `check_investment_discovery` depends on ALL discovery crews
- `match_alternatives_after_discovery` depends on discovery completion
- `check_portfolio_rebalancing` depends on alternative matching
- `consolidate_reports` depends on rebalancing completion
- `generate_final_report` depends on consolidation completion

## Performance Characteristics

### Parallel Execution Benefits
- Discovery crews run concurrently (3x faster than sequential)
- Portfolio holdings processed in parallel (async/await)
- Deep analysis can process multiple holdings concurrently

### Sequential Bottlenecks
- Consolidation waits for rebalancing
- Final report waits for consolidation
- Reporter waits for validation

## Report Aggregation Integration

### JSON Export Paths
Stored in `self.state.crew_export_paths`:
```python
{
    "stock_crew": ["path/to/AAPL_export.json", "path/to/MSFT_export.json"],
    "etf_crew": ["path/to/SPY_export.json"],
    "crypto_crew": ["path/to/BTC_export.json"],
    "deep_analysis_crew": ["path/to/IBM_deep_export.json"],
    "discovery_crew": ["path/to/discovery_export.json"],
    "rebalancing_crew": ["path/to/rebalancing_export.json"]
}
```

### HTML Report Paths
Stored in `self.state.crew_html_paths`:
```python
{
    "stock_crew": ["path/to/AAPL_report.html", "path/to/MSFT_report.html"],
    "etf_crew": ["path/to/SPY_report.html"],
    ...
}
```

### Consolidation Flow
1. `consolidate_reports()` reads all JSON exports
2. Validates each against Pydantic schemas
3. Creates `ConsolidatedReportExport` object
4. Saves to `consolidated_report.json`
5. Returns consolidated data for downstream methods

### Final Report Flow
1. `generate_final_report()` receives consolidated data
2. Loads `ConsolidatedReportExport` from JSON
3. Renders `final_report.html` Jinja2 template
4. Saves final French HTML report
5. Returns final report path

## Helper Methods

### _get_crew_export_path()
Returns standardized path for crew JSON exports:
```
output/reports/{session_id}/{crew_name}/{ticker}_export.json
```

### _generate_html_from_export()
Generates HTML report from JSON export using Python template (NO AI):
1. Loads JSON export
2. Validates against schema
3. Renders Jinja2 template
4. Saves HTML file
5. Returns HTML path

### _store_crew_export_paths()
Stores export and HTML paths in Flow state:
- Updates `self.state.crew_export_paths`
- Updates `self.state.crew_html_paths`
- Updates `self.state.crew_execution_status`

## Future Enhancements

### Potential Optimizations
1. **Parallel Deep Analysis**: Process multiple underperforming holdings concurrently
2. **Streaming Consolidation**: Start consolidation as crews complete (don't wait for all)
3. **Incremental HTML Generation**: Generate crew HTML reports as they complete
4. **Cached Consolidation**: Skip consolidation if no new crew results

### Monitoring Improvements
1. Track crew execution times
2. Monitor parallel execution efficiency
3. Measure consolidation performance
4. Track HTML generation speed

## Compliance with Requirements

### Requirement 7.1-7.8 (Concurrent Execution)
✅ Discovery crews execute in parallel (same trigger)
✅ Consolidation waits for all crews (`and_()` pattern)
✅ No crew depends on another's output during parallel phase
✅ Flow state tracks execution status

### Requirement 15.1-15.7 (Performance Optimization)
✅ Parallel crew execution maximizes performance
✅ Python consolidation is fast (milliseconds)
✅ Python template rendering is fast (milliseconds)
✅ No blocking operations during parallel phase

### Requirement 6.1-6.6 (File-Based Data Passing)
✅ Flow state stores file paths (not data)
✅ Crews read from files when needed
✅ State remains small and focused
✅ No context size limit issues

---

**Version**: 1.0  
**Created**: 2025-01-25  
**Purpose**: Document parallel execution architecture for report aggregation
