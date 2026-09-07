# API Reference

Complete API documentation for FinWiz financial analysis platform.

## Quick Navigation

- [Crew APIs](api/crews.md) - AI agent crews for analysis
- [Tool APIs](api/tools.md) - Financial analysis tools
- [Schema APIs](api/schemas.md) - Data models and validation

## Analysis Crews

`deep_analysis` is FinWiz's only crew — it produces the qualitative half of
each holding's deep analysis (Phase 3), invoked from the `qualify` stage of
`analysis/stages/`. The per-asset-type crews this section
used to document (`StockCrew`, `ETFCrew`, `CryptoCrew`,
`PortfolioRebalancingCrew`, `InvestmentDiscoveryCrew`) were deleted on
2026-09-07 because nothing invoked their execution methods — see root
`CLAUDE.md`'s "Crew Pattern" section and #187.

- **DeepAnalysisCrew** - qualitative analysis for one holding
- See [Deep Analysis Crew API](api/crews.md#deep-analysis-crew) for details

### Portfolio Analysis

Portfolio holdings analysis and recommendations are handled by
`ValidationOrchestrator` (Python, not a crew) — see
`orchestrators/validation_orchestrator.py`.

### Discovery

A+ investment opportunity discovery (Phase 4) is Python scoring, not a crew —
see `orchestrators/discovery_orchestrator.py`.

## Tool Reference

Essential tools for financial analysis:

- **Market Data Tools** - Real-time and historical market data
- **Sentiment Analysis** - News and social media sentiment
- **Quantitative Analysis** - Technical indicators and metrics
- **Backtesting** - Strategy testing and validation
- **Risk Assessment** - Portfolio risk analysis

See [Tool APIs](api/tools.md) for complete documentation.

## Schema Reference

Pydantic data models for type-safe analysis:

- **CrewExportSchemas** - `CrewExportBase` and `DeepAnalysisCrewExport`, the
  only export schema left now that the per-crew schemas were deleted with
  their crews
- **PortfolioSchemas** - Portfolio structure and holdings
- **AnalysisSchemas** - Analysis results and recommendations
- **ValidationSchemas** - Data validation models

See [Schema APIs](api/schemas.md) for complete documentation.

## Flow Reference

CrewAI Flow orchestration:

- **FinwizFlow** - Main workflow orchestration
- **State Management** - Pydantic-based flow state
- **Flow Listeners** - Event-driven workflow steps

## Getting Started

New to the FinWiz API? Check out these resources:

- [Operations Guide](../how-to/OPERATIONS_GUIDE.md) - Deployment and operations
- [Developer Guide](../development/DEVELOPER_GUIDE.md) - Development guide
- [Tutorials](../tutorials/index.md) - Step-by-step tutorials

## API Examples

### Running Deep Analysis

`finwiz/crews/stock_crew/` was deleted along with the rest of the crew
subsystem on 2026-09-07 (see #187). Deep analysis — Python quantitative
scoring plus one `deep_analysis` crew call for qualitative insight — is
driven through `finwiz.analysis.analyze_holding()`, not by constructing a
crew directly:

```python
from finwiz.analysis import analyze_holding

result, enriched = analyze_holding(ticker="AAPL", asset_class="stock", company_name="Apple Inc.")
print(f"Grade: {result.grade}, Score: {result.composite_score:.2f}")
```

See `src/finwiz/analysis/CLAUDE.md` for the full pipeline and its individual
stages.

### Portfolio Review

There is no `finwiz/flows/flow_orchestrator.py` — `FinwizFlow` is defined in
`finwiz/flows/orchestrator.py`:

```python
from finwiz.flows.orchestrator import FinwizFlow

flow = FinwizFlow()
result = flow.kickoff()
```
