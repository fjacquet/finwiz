# Naming Convention: Historical Analysis vs Document RAG

## The Problem

The term "RAG" (Retrieval-Augmented Generation) was causing confusion because FinWiz has TWO different RAG systems:

1. **Document RAG** - Existing agent tools for retrieving documents from vector databases
2. **Historical Analysis** - New Supabase service for retrieving past analysis results

## The Solution

Clear, explicit naming that distinguishes between the two systems:

### Historical Analysis Service (Supabase)

**Purpose**: Retrieve past analysis results (grades, recommendations, scores) from Supabase

**Type**: Python service (not an agent tool)

**When it runs**: Before crew execution, in `kickoff()` method

**Naming**:
- Service class: `HistoricalAnalysisService` (not `RAGService`)
- Factory function: `get_historical_analysis_service()` (not `get_rag_service()`)
- Enable check: `is_historical_analysis_enabled()` (not `is_rag_enabled()`)
- Input helper: `get_historical_context_for_inputs()` ✅ Already clear

**Location**: `src/finwiz/supabase/services/rag_service.py`

**Usage**:
```python
from finwiz.supabase import get_historical_context_for_inputs

# In crew kickoff()
historical_context = get_historical_context_for_inputs(ticker, asset_class)
inputs["historical_context"] = historical_context or ""
```

### Document RAG Tools (Existing)

**Purpose**: Retrieve documents from vector databases for agent research

**Type**: Agent tools (agents call them during execution)

**When it runs**: During crew execution, when agents need documents

**Naming**:
- Tool functions: `get_rag_tools()`, `get_stock_crew_tools(include_rag=True)`
- These names remain unchanged (existing functionality)

**Location**: `src/finwiz/tools/rag_tools.py` (or similar)

**Usage**:
```python
# In crew initialization
tools = get_stock_crew_tools(
    include_rag=True,  # Include document RAG tools
    include_quantitative=True,
)
```

## Quick Reference

| Feature | Historical Analysis | Document RAG |
|---------|-------------------|--------------|
| **Purpose** | Past analysis results | Document retrieval |
| **Type** | Python service | Agent tools |
| **When** | Before crew execution | During crew execution |
| **Called by** | Crew `kickoff()` | Agents |
| **Service class** | `HistoricalAnalysisService` | N/A (tools) |
| **Factory** | `get_historical_analysis_service()` | `get_rag_tools()` |
| **Enable check** | `is_historical_analysis_enabled()` | N/A |
| **Input helper** | `get_historical_context_for_inputs()` | N/A |
| **Location** | `supabase/services/` | `tools/` |

## Migration Guide

If you have existing code using the old naming:

### Old (Confusing)
```python
from finwiz.supabase import get_rag_service, is_rag_enabled

if is_rag_enabled():
    rag_service = get_rag_service()
```

### New (Clear)
```python
from finwiz.supabase import get_historical_analysis_service, is_historical_analysis_enabled

if is_historical_analysis_enabled():
    service = get_historical_analysis_service()
```

## Benefits

1. **No Confusion**: Clear distinction between historical analysis and document RAG
2. **Self-Documenting**: Names explain what they do
3. **Explicit**: Follows Python's "explicit is better than implicit"
4. **Maintainable**: Future developers understand the difference immediately

## Files Updated

- `src/finwiz/supabase/services/rag_service.py` - Class renamed to `HistoricalAnalysisService`
- `src/finwiz/supabase/utils/rag_integration.py` - Functions renamed for clarity
- `src/finwiz/supabase/__init__.py` - Exports updated with new names
- `src/finwiz/supabase/INTEGRATION_GUIDE.md` - Documentation updated
- `src/finwiz/supabase/NAMING_CONVENTION.md` - This file (new)
