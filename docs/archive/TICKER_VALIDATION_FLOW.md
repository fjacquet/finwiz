# Ticker Validation Flow - Visual Guide

## Before Fix ❌

```
┌─────────────────────────────────────────────────────────────┐
│ Flow Orchestrator                                           │
│                                                             │
│  check_report()                                             │
│    ↓                                                        │
│  crew_factory.execute_report_crew(self._state_to_dict())   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ CrewFactory                                                 │
│                                                             │
│  execute_report_crew(inputs)                                │
│    ↓                                                        │
│  report_crew = ReportCrew()                                 │
│  report_crew.crew().kickoff(inputs=inputs)  ❌ PROBLEM     │
│                                                             │
│  Missing: prepare_crew_context() call                      │
│  Result: validated_tickers_list[] NOT in inputs            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Report Crew                                                 │
│                                                             │
│  Tasks receive inputs WITHOUT validated_tickers_list[]      │
│    ↓                                                        │
│  ⚠️  Anti-hallucination rules trigger                       │
│  ⚠️  Graceful degradation messages appear                   │
│  ⚠️  Ticker-specific details omitted                        │
└─────────────────────────────────────────────────────────────┘
```

## After Fix ✅

```
┌─────────────────────────────────────────────────────────────┐
│ Flow Orchestrator                                           │
│                                                             │
│  check_report()                                             │
│    ↓                                                        │
│  crew_factory.execute_report_crew(self._state_to_dict())   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ CrewFactory                                                 │
│                                                             │
│  execute_report_crew(inputs)                                │
│    ↓                                                        │
│  report_crew = ReportCrew()                                 │
│    ↓                                                        │
│  ✅ prepared_context = report_crew.prepare_crew_context()   │
│    ↓                                                        │
│  report_crew.crew().kickoff(inputs=prepared_context)        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ ReportCrew.prepare_crew_context()                           │
│                                                             │
│  1. get_integrated_data_context(inputs)                     │
│     ├─ Load discovery from Flow state OR files             │
│     ├─ Extract backtesting data                            │
│     └─ Build integrated context                            │
│                                                             │
│  2. _extract_validated_tickers(context)                     │
│     ├─ Extract from stock_analysis_data                    │
│     ├─ Extract from etf_analysis_data                      │
│     ├─ Extract from crypto_analysis_data                   │
│     ├─ Extract from portfolio_review.holdings              │
│     └─ Deduplicate and sort                                │
│                                                             │
│  3. Validate: len(tickers) >= 3                             │
│     ├─ If < 3: raise ValueError (fail fast)                │
│     └─ If >= 3: continue                                   │
│                                                             │
│  4. Add to context:                                         │
│     ├─ validated_tickers_list: ["AAPL", "MSFT", ...]       │
│     └─ ticker_count: 65                                    │
│                                                             │
│  5. Return prepared_context                                 │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Report Crew                                                 │
│                                                             │
│  Tasks receive inputs WITH validated_tickers_list[]         │
│    ↓                                                        │
│  ✅ Anti-hallucination rules satisfied                      │
│  ✅ Ticker-specific details included                        │
│  ✅ SEC/EDGAR citations with real URLs                      │
│  ✅ Backtesting metrics displayed                           │
│  ✅ Discovery opportunities shown                           │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow Detail

```
┌──────────────────────────────────────────────────────────────┐
│ Input Sources (Priority Order)                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Flow State (inputs parameter)                           │
│     ├─ inputs.aplus_opportunities                           │
│     ├─ inputs.investment_discovery_structured               │
│     ├─ inputs.stock_analysis_data                           │
│     ├─ inputs.etf_analysis_data                             │
│     └─ inputs.crypto_analysis_data                          │
│                                                              │
│  2. File-Based Discovery (fallback)                         │
│     ├─ output/discovery/a_plus_stocks.json                  │
│     ├─ output/discovery/a_plus_etfs.json                    │
│     └─ output/discovery/a_plus_crypto.json                  │
│                                                              │
│  3. Portfolio Review                                        │
│     └─ output/portfolio/portfolio_review.json               │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│ Ticker Extraction Logic                                     │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  tickers = set()                                            │
│                                                              │
│  # From stock crew                                          │
│  for task in stock_analysis_data.tasks_output:              │
│      ticker = task.pydantic.ticker                          │
│      tickers.add(ticker.upper())                            │
│                                                              │
│  # From ETF crew                                            │
│  for task in etf_analysis_data.tasks_output:                │
│      ticker = task.pydantic.ticker                          │
│      tickers.add(ticker.upper())                            │
│                                                              │
│  # From crypto crew                                         │
│  for task in crypto_analysis_data.tasks_output:             │
│      symbol = task.pydantic.symbol or task.pydantic.ticker  │
│      tickers.add(symbol.upper())                            │
│                                                              │
│  # From portfolio holdings                                  │
│  for holding in portfolio_review.holdings:                  │
│      ticker = holding.ticker                                │
│      tickers.add(ticker.upper())                            │
│                                                              │
│  validated_list = sorted(list(tickers))                     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│ Validation & Context Preparation                            │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  if len(validated_list) < 3:                                │
│      raise ValueError("Insufficient validated tickers")     │
│                                                              │
│  context["validated_tickers_list"] = validated_list         │
│  context["ticker_count"] = len(validated_list)              │
│                                                              │
│  # Also include:                                            │
│  context["discovery_status"] = {...}                        │
│  context["backtesting_status"] = {...}                      │
│  context["aplus_discovery_results"] = {...}                 │
│  context["backtesting_data"] = {...}                        │
│  context["data_availability_summary"] = {...}               │
│                                                              │
│  return context                                             │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## Error Handling

```
┌──────────────────────────────────────────────────────────────┐
│ Error Scenarios                                             │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Scenario 1: Insufficient Tickers (< 3)                     │
│  ├─ ValueError raised in prepare_crew_context()             │
│  ├─ Caught in execute_report_crew()                         │
│  └─ Returns: {"error_type": "insufficient_tickers"}         │
│                                                              │
│  Scenario 2: Context Preparation Failed                     │
│  ├─ Exception raised in prepare_crew_context()              │
│  ├─ Caught in execute_report_crew()                         │
│  └─ Returns: {"error_type": "context_preparation_failed"}   │
│                                                              │
│  Scenario 3: Crew Execution Failed                          │
│  ├─ Exception raised in crew.kickoff()                      │
│  ├─ Caught in execute_report_crew()                         │
│  └─ Returns: {"report_generation_success": False}           │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## Success Indicators

```
✅ Log Messages to Look For:

1. "Crew context prepared with N validated tickers"
   → prepare_crew_context() succeeded

2. "Validated N tickers for report generation"
   → Ticker extraction succeeded

3. "Discovery data found in Flow state"
   → Discovery data properly loaded

4. "Loaded backtesting data for N candidates"
   → Backtesting metrics available

5. "Report generation completed successfully"
   → Full report generated with all data
```

## Testing Checklist

```
□ Ticker extraction works for stock/ETF/crypto data
□ Insufficient tickers (< 3) triggers ValueError
□ Portfolio holdings contribute to ticker list
□ Discovery data loaded from Flow state first
□ Discovery data falls back to files if needed
□ Backtesting data extracted from discovery results
□ validated_tickers_list[] present in crew inputs
□ Report includes ticker-specific details
□ No hallucination warnings in report
□ SEC/EDGAR citations with real URLs
```

---

**Visual Guide Version**: 1.0  
**Date**: 2025-10-15  
**Status**: ✅ Implementation Complete
