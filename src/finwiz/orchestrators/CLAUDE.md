# Orchestrators Module

This directory contains business logic orchestration (Application/Service Layer) for coordinating complex multi-step operations. Orchestrators manage workflows that involve multiple crews, services, or processing steps.

**Architecture Note**: Following layered architecture principles, orchestrators contain business logic ONLY. HTML presentation is delegated to the `reporting/` layer.

## Directory Structure

```
orchestrators/
├── __init__.py                       # Module exports
│
├── # Core Orchestrators
├── deep_analysis_orchestrator.py     # Per-holding deep analysis (uses finwiz.analysis pipeline)
├── deep_analysis_data_collector.py   # Data collection for deep analysis
├── discovery_orchestrator.py         # A+ investment discovery
├── validation_orchestrator.py        # Data validation workflows
├── reporting_orchestrator.py         # Report generation
├── error_handling_orchestrator.py    # Error handling & recovery
├── progress_tracking_orchestrator.py # Progress tracking
├── utility_orchestrator.py           # Shared utilities
│
├── # Portfolio Orchestrators (Consolidated)
├── portfolio_review.py               # Review: thresholds, decisions, execution
├── portfolio_rebalancing.py          # Rebalancing: calculations, constraints, optimization
├── portfolio_holdings_processor.py   # Holdings processing
│
├── # Alternative Matching
├── alternatives_matching_orchestrator.py  # A+ alternatives matching
│
├── # Monitoring
├── a_plus_monitoring_orchestrator.py     # A+ monitoring
│
└── # Validation
    ├── validation_helpers.py         # Validation utilities
    └── validation_orchestrator.py    # Validation coordination
```

**Note**: HTML generation (BeautifulSoup) has been moved to `reporting/portfolio_review_html.py` following layered architecture.

## Major Entry Points

### Flow Integration Orchestrators

These are used by `FinwizFlow` for delegating complex operations:

| File | Class | Purpose |
|------|-------|---------|
| `deep_analysis_orchestrator.py` | `DeepAnalysisOrchestrator` | Per-holding deep analysis + on-the-fly HTML generation |
| `deep_analysis_data_collector.py` | `DeepAnalysisDataCollector` | Data collection for analysis |
| `discovery_orchestrator.py` | `DiscoveryOrchestrator` | A+ investment discovery |
| `alternatives_matching_orchestrator.py` | `AlternativesMatchingOrchestrator` | Match A+ alternatives |
| `validation_orchestrator.py` | `ValidationOrchestrator` | Data validation |
| `reporting_orchestrator.py` | `ReportingOrchestrator` | Report generation |
| `error_handling_orchestrator.py` | `ErrorHandlingOrchestrator` | Error handling |
| `progress_tracking_orchestrator.py` | `ProgressTrackingOrchestrator` | Progress tracking |
| `utility_orchestrator.py` | `UtilityOrchestrator` | Shared utilities |

### Portfolio Review

| File | Function/Class | Purpose |
|------|---------------|---------|
| `portfolio_review.py` | `EnhancedPortfolioReviewOrchestrator` | Comprehensive review |
| `portfolio_review.py` | `run()` | Run portfolio review |
| `portfolio_review.py` | `run_with_rebalancing()` | Review + rebalancing |
| `portfolio_review.py` | `build_portfolio_review()` | Build review data |
| `portfolio_review.py` | `calculate_score()` | Score calculation |
| `portfolio_review.py` | `assess_risk()` | Risk assessment |

**HTML Generation**: Moved to `reporting/portfolio_review_html.py`:
- `generate_holdings_table()` - Holdings table with grades
- `generate_trades_table()` - Trade recommendations
- `add_portfolio_review_sections()` - Portfolio sections
- `add_rebalancing_sections()` - Rebalancing sections

### Rebalancing (Consolidated)

| File | Function/Class | Purpose |
|------|---------------|---------|
| `portfolio_rebalancing.py` | `run_rebalancing()` | Execute rebalancing |
| `portfolio_rebalancing.py` | `calculate_trades()` | Calculate trades |
| `portfolio_rebalancing.py` | `optimize_allocations()` | Optimize weights |
| `portfolio_rebalancing.py` | `apply_constraints()` | Apply constraints |
| `portfolio_rebalancing.py` | `calculate_rebalancing()` | Main calculation |

### Holdings Processing

| File | Function | Purpose |
|------|----------|---------|
| `portfolio_holdings_processor.py` | `PortfolioHoldingsProcessor` | Process holdings |
| `portfolio_holdings_processor.py` | `process_holdings()` | Load and process |

### Deep Analysis - On-the-fly HTML Generation

`DeepAnalysisOrchestrator._store_enriched_analysis()` generates HTML reports immediately after each holding analysis completes. This eliminates the need for end-of-flow batch generation.

**Output structure:**
```
output/
├── stock/
│   ├── AAPL_enriched.json   # Enriched analysis data
│   └── AAPL_report.html     # Individual HTML report
├── etf/
│   └── (same structure)
└── crypto/
    └── (same structure)
```

**Key methods:**
- `_store_enriched_analysis(ticker, enriched)` - Stores JSON + generates HTML immediately
- `run_deep_analysis_concurrent()` - Concurrent analysis with per-holding timeout
- `get_enriched_analysis(ticker)` - Retrieve stored enriched analysis

## Usage Pattern

### In Flow (Delegation)

```python
from finwiz.orchestrators import (
    DeepAnalysisOrchestrator,
    DiscoveryOrchestrator,
)

class FinwizFlow(Flow[FinwizState]):
    def __init__(self):
        super().__init__()
        self.deep_orch = DeepAnalysisOrchestrator()
        self.discovery_orch = DiscoveryOrchestrator()

    @listen(check_portfolio)
    def analyze_holdings_deep(self):
        results = self.deep_orch.analyze_all_holdings(
            holdings=self.state.portfolio_review["holdings"],
            state=self.state
        )
        self.state.deep_analysis_results = results
        return {"deep_analysis_count": len(results)}
```

### Direct Usage

```python
from finwiz.orchestrators.portfolio_review import run_with_rebalancing

# Run portfolio review with rebalancing
review_path, rebalancing_result = await run_with_rebalancing(
    target_weights={"AAPL": 0.3, "GOOGL": 0.3, "BND": 0.4},
    available_capital=10000,
    include_rebalancing=True
)
```

### ReportingOrchestrator - HTML Auto-Generation

The ReportingOrchestrator automatically generates HTML reports when consolidating crew exports:

```python
from finwiz.orchestrators.reporting_orchestrator import ReportingOrchestrator
from finwiz.flow_state import FinwizState

orchestrator = ReportingOrchestrator(FinwizState())

# Consolidate reports with auto HTML generation (default)
result = orchestrator.consolidate_reports(
    crew_export_paths={
        "stock_crew": ["output/stock/AAPL_export.json", "output/stock/GOOGL_export.json"],
        "etf_crew": ["output/etf/SPY_export.json"],
        "crypto_crew": ["output/crypto/BTC_export.json"],
    },
    generate_html=True  # Default: automatically generates HTML for each export
)

# Result contains:
# - consolidated_data: Merged crew reports
# - html_report_paths: {"stock_crew": ["output/stock/AAPL_export.html", ...], ...}
# - consolidated_data["html_reports_generated"]: Count of generated HTML reports

# Generate HTML for a single export
html_path = orchestrator.generate_crew_html_report(
    crew_name="stock_crew",
    export_path="output/stock/AAPL_export.json"
)

# Batch generate all HTML reports
html_paths = orchestrator.generate_all_crew_html_reports(crew_export_paths)
```

**Key methods:**
- `consolidate_reports(paths, generate_html=True)` - Consolidates + auto-generates HTML
- `generate_crew_html_report(crew, path)` - Single HTML report
- `generate_all_crew_html_reports(paths)` - Batch HTML generation

## Orchestrator Pattern

```python
from finwiz.tools.logger import get_logger

class MyOrchestrator:
    """Orchestrates a complex multi-step workflow."""

    def __init__(self):
        self.logger = get_logger(__name__)

    def execute(self, state: FinwizState) -> dict[str, Any]:
        """Execute the orchestrated workflow."""
        self.logger.info("Starting orchestration")

        try:
            # Step 1: Validate inputs
            validated = self._validate_inputs(state)

            # Step 2: Execute main logic
            results = self._execute_main_logic(validated)

            # Step 3: Post-process
            final = self._post_process(results)

            self.logger.info("Orchestration complete")
            return final

        except Exception as e:
            self.logger.error(f"Orchestration failed: {e}")
            return self._handle_failure(e, state)

    def _validate_inputs(self, state: FinwizState) -> dict:
        # Validation logic
        pass

    def _execute_main_logic(self, validated: dict) -> dict:
        # Main execution
        pass

    def _post_process(self, results: dict) -> dict:
        # Post-processing
        pass

    def _handle_failure(self, error: Exception, state: FinwizState) -> dict:
        # Error handling
        pass
```

## Testing

```bash
# Test all orchestrators
uv run pytest tests/unit/orchestrators/ -v

# Test specific orchestrator
uv run pytest tests/unit/orchestrators/test_deep_analysis_orchestrator.py -v

# Test portfolio review
uv run pytest tests/unit/orchestrators/test_portfolio_review.py -v
```

## Related Modules

- `finwiz.flows` - Flow orchestration (uses orchestrators)
- `finwiz.crews` - CrewAI crews (executed by orchestrators)
- `finwiz.flow_state` - State management
- `finwiz.scoring` - Scoring algorithms
