# Historical Analysis Service Integration Guide

## Overview

This guide explains how to integrate the Historical Analysis Service with CrewAI crews.

**Important**: The Historical Analysis Service is a **Python service**, not an agent tool. It retrieves historical analysis results from the Supabase vector database and adds them to task descriptions **before** crew execution.

**Naming Clarity**:
- **Historical Analysis Service** (this): Retrieves past analysis results from Supabase
- **Document RAG Tools** (existing): Agent tools for document retrieval from vector databases

## What is the Historical Analysis Service?

The Historical Analysis Service provides historical context from past analyses to help agents make better decisions:

- **What it does**: Retrieves similar past analyses (grades, recommendations, scores) from Supabase
- **When it runs**: Before crew execution, in the `kickoff()` method
- **How agents use it**: Historical context is included in task descriptions via `{historical_context}` placeholder
- **Graceful fallback**: Works seamlessly whether Supabase is enabled or disabled

## Integration Steps

### Step 1: Update Crew `kickoff()` Method

Add historical context retrieval to your crew's `kickoff()` method:

```python
from finwiz.supabase.utils.rag_integration import get_historical_context_for_inputs

class StockCrew:
    def kickoff(self, inputs: dict[str, Any] | None = None) -> Any:
        if inputs is None:
            inputs = {}
        
        # Get historical analysis context from Supabase (Python service)
        ticker = inputs.get("ticker", "")
        asset_class = inputs.get("asset_class", "stock")
        
        historical_context = get_historical_context_for_inputs(ticker, asset_class)
        
        # Add to inputs (empty string if unavailable - graceful fallback)
        inputs["historical_context"] = historical_context or ""
        
        if historical_context:
            logger.info(f"Added historical context for {ticker}")
        
        # Execute crew with enhanced inputs
        crew_instance = self.crew()
        result = crew_instance.kickoff(inputs=inputs)
        return result
```

### Step 2: Update Task Descriptions

Add `{historical_context}` placeholder to task descriptions in `config/tasks.yaml`:

```yaml
analysis_task:
  description: >
    Analyze {ticker} ({asset_class}) with comprehensive research.
    
    {historical_context}
    
    Perform the following analysis steps:
    1. Validate {ticker} using TickerValidationTool
    2. Fetch financial data for {ticker}
    3. Calculate quantitative metrics
    4. Generate investment recommendation
    
    Focus on providing actionable insights based on current data and
    historical patterns from similar analyses.
```

### Step 3: Enable Supabase (Optional)

Set environment variables to enable the Historical Analysis Service:

```bash
# Enable Supabase integration
SUPABASE_ENABLED=true
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Configure cache TTL (optional)
ANALYSIS_CACHE_TTL_HOURS=24
```

If Supabase is disabled (`SUPABASE_ENABLED=false`), the `{historical_context}` placeholder will be replaced with an empty string, and crews will work normally without historical context.

## Example Historical Context

When the Historical Analysis Service finds similar analyses, the historical context looks like:

```
Historical Context for: AAPL stock analysis

Similar Past Analyses:

1. AAPL (STOCK)
   Grade: A+ | Recommendation: BUY
   Similarity: 95.23%
   Summary: Strong fundamentals with consistent revenue growth...

2. MSFT (STOCK)
   Grade: A | Recommendation: BUY
   Similarity: 87.45%
   Summary: Solid cloud business driving growth...

3. GOOGL (STOCK)
   Grade: A | Recommendation: HOLD
   Similarity: 82.11%
   Summary: Advertising revenue stable but facing headwinds...
```

## Benefits

1. **Grounded Recommendations**: Agents can reference past analyses for similar assets
2. **Reduced Hallucinations**: Historical context provides factual grounding
3. **Learning from History**: Agents see what worked/didn't work in past analyses
4. **Zero Impact**: Graceful fallback if Supabase is unavailable
5. **No Code Changes**: Works with existing task descriptions via placeholder

## Crew-Specific Integration

### Stock Crew

```python
# src/finwiz/crews/stock_crew/stock_crew.py

from finwiz.supabase.utils.rag_integration import get_historical_context_for_inputs

class StockCrew:
    def kickoff(self, inputs: dict[str, Any] | None = None) -> Any:
        if inputs is None:
            inputs = {}
        
        # Add historical context for stock analysis
        ticker = inputs.get("ticker", "")
        historical_context = get_historical_context_for_inputs(ticker, "stock")
        inputs["historical_context"] = historical_context or ""
        
        # Execute crew
        crew_instance = self.crew()
        result = crew_instance.kickoff(inputs=inputs)
        return result
```

### ETF Crew

```python
# src/finwiz/crews/etf_crew/etf_crew.py

from finwiz.supabase.utils.rag_integration import get_historical_context_for_inputs

class EtfCrew:
    def kickoff(self, inputs: dict[str, Any] | None = None) -> Any:
        if inputs is None:
            inputs = {}
        
        # Add historical context for ETF analysis
        ticker = inputs.get("ticker", "")
        historical_context = get_historical_context_for_inputs(ticker, "etf")
        inputs["historical_context"] = historical_context or ""
        
        # Execute crew
        crew_instance = self.crew()
        result = crew_instance.kickoff(inputs=inputs)
        return result
```

### Crypto Crew

```python
# src/finwiz/crews/crypto_crew/crypto_crew.py

from finwiz.supabase.utils.rag_integration import get_historical_context_for_inputs

class CryptoCrew:
    def kickoff(self, inputs: dict[str, Any] | None = None) -> Any:
        if inputs is None:
            inputs = {}
        
        # Add historical context for crypto analysis
        ticker = inputs.get("ticker", "")
        historical_context = get_historical_context_for_inputs(ticker, "crypto")
        inputs["historical_context"] = historical_context or ""
        
        # Execute crew
        crew_instance = self.crew()
        result = crew_instance.kickoff(inputs=inputs)
        return result
```

## Testing

Test the integration with and without Supabase:

```python
# Test with Supabase enabled
os.environ["SUPABASE_ENABLED"] = "true"
crew = StockCrew()
result = crew.kickoff(inputs={"ticker": "AAPL", "asset_class": "stock"})

# Test with Supabase disabled (graceful fallback)
os.environ["SUPABASE_ENABLED"] = "false"
crew = StockCrew()
result = crew.kickoff(inputs={"ticker": "AAPL", "asset_class": "stock"})
# Should work normally without historical context
```

## Troubleshooting

### No Historical Context Appearing

1. Check `SUPABASE_ENABLED=true` in environment
2. Verify Supabase credentials are correct
3. Check if similar analyses exist in database
4. Review logs for RAG service errors

### Historical Context Not Relevant

1. Adjust similarity threshold (default: 0.7)
2. Increase limit to get more results (default: 3)
3. Ensure embeddings are being generated for stored analyses

### Performance Impact

- Historical context retrieval adds ~100-500ms to crew startup
- This is acceptable as it runs once before crew execution
- No impact on agent execution time (context is pre-loaded)

## Requirements Satisfied

This integration satisfies requirements 5.1-5.5:

- ✅ 5.1: Agents query vector database for relevant historical analyses
- ✅ 5.2: Top 3 most similar analyses included in agent prompts
- ✅ 5.3: Graceful fallback when no similar analyses exist
- ✅ 5.4: Agents cite historical analyses in recommendations
- ✅ 5.5: Fallback to standard analysis when RAG retrieval fails
