# Agent Guidelines for FinWiz Development

Core principles and standards for AI agents working on FinWiz codebase.

## Core Principles

### 1. Accuracy and Thoroughness

- Provide complete, accurate information
- Include specific metrics, examples, and technical details
- Cite authoritative sources
- Acknowledge limitations when appropriate

### 2. Output Quality

- Structure information logically
- Use proper formatting (HTML, Markdown)
- Include visual elements (tables, lists)
- Maintain consistent terminology
- Follow specified output formats exactly

### 3. Technical Best Practices

- Follow KISS, DRY, YAGNI principles
- Target files under 200 lines
- Use pandas/numpy for calculations
- Use `pytest` with `pytest-mock` (never `unittest.mock`)
- Mock all external dependencies
- Enable AI reasoning with `reasoning=True`

### 4. Data Validation

- Use strict Pydantic v2 models with `extra='forbid'`
- Validate at crew boundaries using ValidationManager
- Follow standardized risk assessment (0-5 scale)
- Handle validation errors gracefully
- Support configurable strictness (off/warn/error)

## Agent-Specific Guidelines

### Research Agents

- Provide exhaustive information (20+ detailed points)
- Include specific metrics and examples
- Cite sources consistently
- Validate ticker symbols before analysis
- Use enhanced analysis tools

### Technical Analysis Agents

- Integrate multiple indicators (RSI, MACD, Bollinger Bands)
- Use chart generation tools
- Identify support/resistance levels
- Provide Fibonacci analysis
- Synthesize multiple timeframes

### Sentiment Analysis Agents

- Use `StandardizedSentimentAnalysisTool`
- Aggregate multi-source news
- Calculate confidence-weighted scores
- Identify trending topics
- Handle article deduplication
- Implement circuit breaker for Perplexity API

### Portfolio Analysis Agents

- Validate holdings across exchanges
- Apply consistent scoring methodology
- Generate comprehensive HoldingDecision objects
- Identify alternatives for underperforming holdings
- Provide clear rationale with citations

### Portfolio Holdings Analysis Agents

- Use `AlternativeFinder` for alternatives (graded below B)
- Use `PriceTargetCalculator` for price targets
- Use `HoldingAnalyzerOrchestrator` for crew coordination
- Prioritize A+ candidates from discovery crew
- Provide transition strategies (immediate/gradual/tax-optimized)
- Calculate asset-specific improvements
- Include French language rationale

### Quantitative Analysis Agents

- Use `QuantitativeAnalysisTool` for analysis
- Apply multi-indicator technical analysis
- Generate buy/sell signals with confidence
- Execute backtesting with risk management
- Calculate risk-adjusted metrics
- Apply modern portfolio theory

### Reporting Agents

- Transform research into readable formats
- Maintain technical depth
- Create professional formatting
- Ensure proper citations
- **NO TOOLS** - consume upstream context only
- Support persistent financial planning
- Include AI reasoning outputs
- Present decision transparency

## Tool Usage

### Required Tools by Crew

**Stock Crew**:

- `QuantitativeAnalysisTool(asset_class="stock")`
- `EnhancedSECAnalysisTool`
- `TickerValidationTool`
- `StandardizedSentimentTool`
- RAG tools via `get_rag_tools()`

**ETF Crew**:

- `QuantitativeAnalysisTool(asset_class="etf")`
- `EnhancedETFAnalysisTool`
- `TickerValidationTool`
- `StandardizedSentimentTool`
- RAG tools

**Crypto Crew**:

- `QuantitativeAnalysisTool(asset_class="crypto")`
- `EnhancedCryptoAnalysisTool`
- `CoinMarketCapTool`
- `TickerValidationTool`
- RAG tools

**Report Crew** (SPECIAL):

- **Empty tools list** (`tools=[]`)
- Only consume upstream context
- No external API calls

## CrewAI Standards

### Agent Configuration

```python
@agent
def stock_analyst(self) -> Agent:
    return Agent(
        config=self.agents_config["stock_analyst"],
        tools=get_stock_crew_tools(),
        verbose=True
    )
```

### Task Configuration

```yaml
stock_analysis_task:
  description: "Analyze stock with quantitative metrics"
  expected_output: "Structured analysis with risk assessment"
  output_pydantic: "TenKInsight"
  agent: stock_analyst
  async_execution: true
```

### Crew Configuration

```python
@crew
def crew(self) -> Crew:
    return Crew(
        agents=self.agents,
        tasks=self.tasks,
        process=Process.sequential,
        verbose=True,
        respect_context_window=True,
        max_rpm=20
    )
```

## Validation Standards

### Schema Compliance

- All outputs must conform to registered schemas
- Use `ValidationManager` for validation
- Handle errors based on strictness mode
- Provide field-level error context

### Risk Assessment

- Use `RiskAssessmentStandardized` schema
- 0-5 scale scoring
- Include systematic and idiosyncratic risk
- Follow standardized risk taxonomy

## Testing Standards

### Test Requirements

- Mock all external calls
- Fast execution (< 5 seconds)
- Independent tests (no shared state)
- Arrange-Act-Assert structure
- Descriptive names: `test_should_{behavior}_when_{condition}`

### Test Data

- Use Faker for realistic data
- Consistent mocking patterns
- Comprehensive coverage (80%+ target)

## Output Standards

### French Language

- All user-facing output in French
- Professional financial terminology
- Clear, actionable recommendations

### HTML Reports

- Professional structure with FinWiz branding
- Responsive design (mobile-friendly)
- Emojis for visual appeal (📊 📈 📉 💰)
- Color-coded grades
- Print-friendly CSS

---

**Version**: 2.0  
**Last Updated**: 2025-03-10
