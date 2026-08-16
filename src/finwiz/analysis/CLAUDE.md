# Analysis Module

This module provides the functional programming pipeline for per-holding deep analysis. It combines Python quantitative scoring ($0 cost) with AI qualitative insights.

## Directory Structure

```
analysis/
├── __init__.py                   # Module exports
├── deep_analysis_pipeline.py     # Backwards-compatible facade only
├── _helpers.py                   # Shared helpers
├── fact_pack_research.py         # Perplexity fact-pack research
├── strategic_research.py         # Strategic framework research
└── stages/                       # WHERE THE PIPELINE ACTUALLY LIVES
    ├── __init__.py               # run_pipeline() — the real orchestrator
    ├── collect.py                # 1. collect
    ├── quantify.py               # 2. quantify
    ├── fact_pack.py              # 3. fact_pack
    ├── qualify.py                # 4. qualify (AI)
    ├── synthesize.py             # 5. synthesize
    ├── emit.py                   # 6. emit
    ├── _ledger.py                # RunLedger JSONL
    ├── _resilience.py            # @stage timeouts/retries, TransientStageError
    ├── _qualify_fallbacks.py
    ├── _synthesize_helpers.py
    └── _synthesize_options.py
```

`deep_analysis_pipeline.py` is a facade: it re-exports the stage functions and
delegates to `finwiz.analysis.stages.run_pipeline`. Edit the stage modules, not
the facade.

## Architecture

The analysis pipeline follows functional programming principles with pure function composition:

```
┌──────────────────────────────────────────────────────────────────┐
│  analyze_holding(ticker, asset_class, company_name)              │
│  │                                                               │
│  │  Six stages, in finwiz.analysis.stages:                       │
│  │  ├── collect     -> RawData                   [Python tools]  │
│  │  ├── quantify    -> Quant                        [$0 Python]  │
│  │  ├── fact_pack   -> FactPack                    [Perplexity]  │
│  │  ├── qualify     -> Qual                          [AI crew]   │
│  │  ├── synthesize  -> Enriched                       [Python]   │
│  │  └── emit        -> artifacts + RunLedger          [Python]   │
│  │                                                               │
│  └── Output: (DeepAnalysisResult, EnrichedAnalysis)              │
└──────────────────────────────────────────────────────────────────┘
```

## Major Entry Points

| Function | Purpose |
|----------|---------|
| `analyze_holding()` | Main entry point - composes entire pipeline |
| `collect_raw_data()` | Collect raw financial data using Python tools |
| `calculate_quantitative()` | Deterministic Python scoring ($0 cost) |
| `generate_qualitative()` | AI crew call for qualitative insights |
| `synthesize_enriched_analysis()` | Combine quantitative + qualitative |

## Usage

### Basic Usage

```python
from finwiz.analysis import analyze_holding

# Analyze a single holding
result, enriched = analyze_holding(
    ticker="AAPL",
    asset_class="stock",
    company_name="Apple Inc."
)

# result: DeepAnalysisResult for caching/state
print(f"Grade: {result.grade}, Score: {result.composite_score:.2f}")

# enriched: EnrichedAnalysis for HTML generation
print(f"Final recommendation: {enriched.final_recommendation}")
print(f"Executive summary: {enriched.executive_summary}")
```

### Individual Pipeline Steps

```python
from finwiz.analysis import (
    AnalysisContext,
    collect_raw_data,
    calculate_quantitative,
    generate_qualitative,
    synthesize_enriched_analysis,
)

# Create context
ctx = AnalysisContext(ticker="AAPL", asset_class="stock")

# Step 1: Collect data
raw_data = collect_raw_data(ctx)

# Step 2: Calculate quantitative ($0)
result, quant = calculate_quantitative(ctx, raw_data)

# Step 3: Generate qualitative (AI)
qual = generate_qualitative(ctx, quant)

# Step 4: Synthesize
enriched = synthesize_enriched_analysis(ctx, quant, qual, processing_time=5.2)
```

## Key Design Decisions

### AI Minimalism

- **Python for deterministic tasks**: Data collection, scoring, synthesis
- **AI only for reasoning**: Qualitative insights requiring contextual analysis
- **Cost efficiency**: Python steps are $0, AI step is ~$0.05-0.10

### Python Wins on Conflicts

When AI and Python disagree on recommendations:

```python
# In synthesize_enriched_analysis()
final_recommendation = quant.preliminary_recommendation  # Python wins
```

This prevents AI hallucination from overriding deterministic calculations.

### Fallback Handling

If AI fails, the pipeline returns a degraded but valid result:

```python
# Returns QualitativeInsights with LOW confidence
# EnrichedAnalysis still contains full quantitative data
```

## Output Schemas

### DeepAnalysisResult

Used for caching and flow state. A Pydantic model (`flow_state_models.py:14`),
**not** a dataclass — and several fields the older docs omitted are required, so
constructing it from a partial shape raises `ValidationError`:

```python
class DeepAnalysisResult(BaseModel):
    # required
    ticker: str
    asset_class: str
    crew_name: str
    composite_score: float          # 0.0-1.0
    grade: str                      # A+ to F
    recommendation: str             # BUY, HOLD, SELL
    rationale: str
    data_freshness_hours: float     # >= 0.0
    confidence_level: float         # 0.0-1.0

    # optional component scores
    fundamental_score: float | None  # 0.0-1.0
    technical_score: float | None    # 0.0-1.0
    risk_score: float | None         # 0.0-5.0  (note: 0-5, not 0-1)
```

### EnrichedAnalysis (Pydantic)

Used for HTML report generation:

```python
class EnrichedAnalysis(BaseModel):
    ticker: str
    quantitative: QuantitativeAnalysis   # Python-calculated
    qualitative: QualitativeInsights     # AI-generated
    final_grade: str
    final_score: float
    final_recommendation: str
    executive_summary: str
    # ... other fields
```

## Testing

```bash
# Unit tests
uv run pytest tests/unit/analysis/ -v

# Integration tests (requires API keys)
uv run pytest tests/integration/analysis/ -v
```

## Related Modules

- `finwiz.orchestrators.deep_analysis_orchestrator` - Uses this pipeline
- `finwiz.scoring.deep_analysis_scorer` - Quantitative scoring
- `finwiz.schemas.hybrid_analysis` - Output schemas
- `finwiz.crews.deep_analysis` - AI crew for qualitative analysis
