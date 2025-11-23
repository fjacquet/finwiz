# Design Document: Python/AI Hybrid Analysis Architecture

## Overview

This design implements a hybrid architecture that combines Python's deterministic calculations with AI's contextual analysis capabilities. The system addresses critical data quality issues through multi-source data acquisition and ensures reliable AI output through strict schema validation.

### Key Design Principles

1. **Separation of Concerns**: Python handles calculations, AI handles insights
2. **Data Quality First**: Multi-source fallbacks ensure critical fields are available
3. **Type Safety**: Pydantic models throughout for validation
4. **Graceful Degradation**: System continues with warnings when components fail
5. **Performance**: Maintain ≤30 seconds per holding analysis

## Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Hybrid Analysis Flow                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  1. Multi-Source Data Acquisition (NEW)                     │
│     ├─ Try yfinance (primary, fastest)                      │
│     ├─ Try Alpha Vantage (fundamentals fallback)            │
│     ├─ Try Intrinio (SEC filings fallback)                  │
│     └─ Try Tiingo/EOD (international fallback)              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Python Quantitative Analysis                            │
│     ├─ Validate critical fields                             │
│     ├─ Calculate scores (fundamental, technical, risk)      │
│     ├─ Assign grade (A+ to F)                               │
│     └─ Generate QuantitativeAnalysis model                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  3. AI Qualitative Analysis                                 │
│     ├─ Pass QuantitativeAnalysis as read-only context       │
│     ├─ SEC insights (business model, risks)                 │
│     ├─ Competitive analysis (positioning, catalysts)        │
│     ├─ Technical strategy (patterns, entry/exit)            │
│     └─ Generate QualitativeInsights model (NEW)             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Merge & Enrich                                          │
│     ├─ Combine quantitative + qualitative                   │
│     ├─ Generate EnrichedAnalysis model                      │
│     └─ Create comprehensive report (≥2000 words)            │
└─────────────────────────────────────────────────────────────┘
```


## Components and Interfaces

### 1. Multi-Source Data Acquisition Layer (NEW)

**Purpose**: Ensure critical fields are always available through fallback data sources.

**Component**: `DataSourceOrchestrator`

**Location**: `src/finwiz/data/data_source_orchestrator.py`

**Performance Requirements** (Requirement 11.6):
- Complete data acquisition in ≤10 seconds per ticker across all fallback attempts
- Implement timeout per source: 3 seconds max
- Parallel validation when possible

**Interface**:

```python
class DataSourceOrchestrator:
    """Orchestrates data acquisition across multiple sources with fallbacks."""
    
    def get_fundamental_data(
        self, 
        ticker: str, 
        asset_class: str,
        timeout: float = 10.0
    ) -> FundamentalData:
        """
        Get fundamental data with automatic fallbacks.
        
        Waterfall Strategy (Requirement 11.1-11.4):
        1. yfinance (fastest, free, good for US stocks) - 3s timeout
        2. Alpha Vantage (better fundamentals, 500 calls/day) - 3s timeout
        3. Intrinio (SEC filings, limited free) - 3s timeout
        4. Tiingo/EOD (international stocks) - 3s timeout
        5. Industry averages (last resort with warning) - instant
        
        Data Validation (Requirement 11.7):
        - Reject negative ROE values
        - Reject extreme outliers (>3 std dev from industry mean)
        - Validate data types and ranges
        
        Returns:
            FundamentalData with source attribution for lineage (Requirement 11.5)
        
        Raises:
            DataUnavailableError: All sources failed
            TimeoutError: Exceeded 10 second total timeout
        """
        pass
    
    def get_price_data(self, ticker: str, timeout: float = 3.0) -> PriceData:
        """Get price data with fallbacks."""
        pass
    
    def get_technical_data(self, ticker: str, timeout: float = 3.0) -> TechnicalData:
        """Get technical indicators with fallbacks."""
        pass
    
    def _validate_fundamental_data(self, data: dict, ticker: str) -> bool:
        """
        Validate fundamental data for quality (Requirement 11.7).
        
        Validation Rules:
        - ROE: Must be between -1.0 and 2.0 (reject if outside)
        - Debt/Equity: Must be >= 0 and < 10.0
        - Revenue Growth: Must be between -0.5 and 5.0
        - Profit Margin: Must be between -1.0 and 1.0
        
        Returns:
            True if data passes validation, False otherwise
        """
        pass
```

**Data Source Adapters**:

```python
# src/finwiz/data/adapters/yfinance_adapter.py
class YFinanceAdapter:
    """
    Primary adapter for US stocks using yfinance library.
    
    Strengths:
    - Fast and free
    - Good coverage of US stocks
    - Includes basic fundamentals (ROE, debt/equity, margins)
    
    Limitations:
    - Limited international coverage
    - Sometimes missing fundamental data
    - No official API (web scraping)
    """
    def get_fundamentals(self, ticker: str, timeout: float = 3.0) -> dict:
        """
        Extract fundamentals from yfinance with timeout.
        
        Returns dict with:
        - roe: Return on Equity (from info['returnOnEquity'])
        - debt_to_equity: Debt/Equity ratio (from info['debtToEquity'])
        - revenue_growth: Revenue growth rate (from info['revenueGrowth'])
        - profit_margin: Profit margin (from info['profitMargins'])
        """
        pass

# src/finwiz/data/adapters/alpha_vantage_adapter.py
class AlphaVantageAdapter:
    """
    Fallback adapter using Alpha Vantage API.
    
    API Details:
    - Endpoint: https://www.alphavantage.co/query
    - Function: OVERVIEW for company fundamentals
    - Rate Limit: 500 calls/day (free tier)
    - Coverage: 60+ exchanges globally
    
    Strengths:
    - Better fundamental data than yfinance
    - Official API with documentation
    - Good international coverage
    
    Limitations:
    - Rate limited (500/day)
    - Requires API key
    """
    def get_fundamentals(self, ticker: str, timeout: float = 3.0) -> dict:
        """
        Extract fundamentals from Alpha Vantage with timeout.
        
        API Call:
        GET /query?function=OVERVIEW&symbol={ticker}&apikey={key}
        
        Returns dict with:
        - roe: From 'ReturnOnEquityTTM'
        - debt_to_equity: From 'DebtToEquityRatio'
        - revenue_growth: From 'QuarterlyRevenueGrowthYOY'
        - profit_margin: From 'ProfitMargin'
        """
        pass

# src/finwiz/data/adapters/intrinio_adapter.py
class IntrinioAdapter:
    """
    Fallback adapter using Intrinio Python SDK.
    
    API Details:
    - SDK: intrinio_sdk (Python)
    - Endpoint: FundamentalsApi, CompanyApi
    - Coverage: SEC filings, financial statements
    
    Strengths:
    - Direct access to SEC filings
    - Comprehensive financial statements
    - Official Python SDK
    
    Limitations:
    - Limited free tier
    - Requires API key
    - US-focused
    """
    def get_fundamentals(self, ticker: str, timeout: float = 3.0) -> dict:
        """
        Extract fundamentals from Intrinio SEC filings with timeout.
        
        SDK Usage:
        intrinio.CompanyApi().get_company_fundamentals(
            identifier=ticker,
            statement_code='income_statement',
            latest_only=True
        )
        
        Returns dict with:
        - roe: Calculated from net income / equity
        - debt_to_equity: From balance sheet
        - revenue_growth: From income statement
        - profit_margin: From income statement
        """
        pass

# src/finwiz/data/adapters/tiingo_adapter.py
class TiingoAdapter:
    """
    Fallback adapter for international stocks using Tiingo API.
    
    API Details:
    - Endpoint: https://api.tiingo.com/tiingo/fundamentals
    - Rate Limit: Varies by plan (free tier available)
    - Coverage: International stocks, 99.9% uptime
    
    Strengths:
    - Excellent international coverage
    - High reliability (99.9% uptime)
    - Good for non-US exchanges
    
    Limitations:
    - Requires API key
    - Rate limited
    """
    def get_fundamentals(self, ticker: str, timeout: float = 3.0) -> dict:
        """
        Extract fundamentals from Tiingo (international) with timeout.
        
        API Call:
        GET /tiingo/fundamentals/{ticker}/statements
        Headers: {'Authorization': 'Token {api_key}'}
        
        Returns dict with:
        - roe: From financial statements
        - debt_to_equity: From balance sheet
        - revenue_growth: From income statement
        - profit_margin: From income statement
        """
        pass

# src/finwiz/data/adapters/eod_adapter.py
class EODAdapter:
    """
    Fallback adapter for emerging markets using EODHistoricalData API.
    
    API Details:
    - Endpoint: https://eodhd.com/api/fundamentals
    - Coverage: 70K+ tickers, emerging markets
    - Free Tier: 20 symbols
    
    Strengths:
    - Extensive global coverage (70K+ tickers)
    - Strong emerging markets coverage
    - Comprehensive fundamental data
    
    Limitations:
    - Limited free tier (20 symbols)
    - Requires API key
    """
    def get_fundamentals(self, ticker: str, timeout: float = 3.0) -> dict:
        """
        Extract fundamentals from EODHistoricalData with timeout.
        
        API Call:
        GET /api/fundamentals?api_token={key}&symbol={ticker}.{exchange}
        
        Returns dict with:
        - roe: From 'Financials.Balance_Sheet.returnOnEquity'
        - debt_to_equity: From 'Financials.Balance_Sheet.debtEquity'
        - revenue_growth: From 'Financials.Income_Statement.revenueGrowth'
        - profit_margin: From 'Financials.Income_Statement.profitMargin'
        """
        pass

# src/finwiz/data/adapters/industry_averages.py
class IndustryAveragesAdapter:
    """
    Fallback adapter providing industry average values (Requirement 11.4).
    
    Used when all data sources fail. Returns conservative estimates
    with confidence penalty.
    
    Industry Averages (by sector):
    - Technology: ROE=0.20, Debt/Equity=0.30
    - Financial: ROE=0.12, Debt/Equity=1.50
    - Healthcare: ROE=0.15, Debt/Equity=0.40
    - Consumer: ROE=0.18, Debt/Equity=0.50
    - Industrial: ROE=0.14, Debt/Equity=0.60
    - Energy: ROE=0.10, Debt/Equity=0.70
    """
    def get_fundamentals(self, ticker: str, asset_class: str) -> dict:
        """
        Get industry average fundamentals as last resort.
        
        Returns data with:
        - confidence = 0.5 (reduced from 1.0)
        - source = "industry_average"
        - warning flag set
        """
        pass
```


### 2. Python Quantitative Analysis Component

**Purpose**: Calculate deterministic scores and grades from validated data.

**Component**: `DeepAnalysisScorer` (existing, enhanced)

**Location**: `src/finwiz/scoring/deep_analysis_scorer.py`

**Enhancements**:

- Accept `FundamentalData` with source attribution
- Track data lineage for each calculated metric
- Handle partial data with confidence penalties
- Log which fields came from which sources

**Interface**:

```python
class DeepAnalysisScorer:
    def calculate_composite_score(
        self,
        ticker: str,
        asset_class: str,
        data: FundamentalData  # Now includes source attribution
    ) -> QuantitativeAnalysis:
        """
        Calculate scores with data lineage tracking.
        
        Returns:
            QuantitativeAnalysis with:
            - composite_score
            - grade (A+ to F)
            - component scores (fundamental, technical, risk)
            - data_lineage (which source provided each field)
            - confidence_level (reduced if using fallbacks/averages)
        """
        pass
```

### 3. AI Qualitative Analysis Component

**Purpose**: Generate contextual insights without recalculating metrics.

**Component**: Refactored Stock Crew Tasks

**Location**: `src/finwiz/crews/stock_crew/config/tasks.yaml`

**Key Changes**:

**Before (AI Minimalism - Too Minimal)**:

```yaml
stock_analysis_task:
  description: "Analyze {ticker} and provide recommendation"
  # Problem: AI had no context, generated generic output
```

**After (Hybrid - Contextual with Format Enforcement)**:

```yaml
stock_analysis_task:
  description: >
    Analyze {ticker} using the provided quantitative analysis as context.
    
    QUANTITATIVE CONTEXT (DO NOT RECALCULATE - Requirement 1.2, 1.3):
    - Grade: {grade}
    - Composite Score: {composite_score}
    - ROE: {roe}
    - Debt/Equity: {debt_to_equity}
    - RSI: {rsi}
    - Volatility: {volatility}
    
    YOUR TASK (QUALITATIVE ANALYSIS ONLY - Requirement 2.1-2.5):
    1. Interpret what these metrics mean in business context
    2. Analyze competitive positioning and moat (Requirement 2.2)
    3. Identify growth catalysts and risks (Requirement 2.4)
    4. Provide bull/base/bear scenarios with probabilities (Requirement 2.5)
    5. Recommend entry/exit strategy with price targets (Requirement 5.3)
    
    OUTPUT FORMAT (STRICT - Requirement 12.1):
    Use output_pydantic: QualitativeInsights
    
    REQUIRED FIELDS (Requirement 12.2):
    - sec_insights (business model, competitive advantages, risk factors)
    - competitive_analysis (market position, growth drivers, threats)
    - technical_strategy (chart patterns, support/resistance, entry/exit)
    - contextual_risks (regulatory, geopolitical, operational, financial)
    - scenario_analysis (bull/base/bear with probabilities and targets)
    - investment_thesis (≥500 words)
    - action_plan (specific steps)
    
    EXAMPLE OUTPUT (Requirement 12.7):
    {{
      "ticker": "AAPL",
      "asset_class": "stock",
      "sec_insights": {{
        "business_model": "Vertically integrated hardware/software/services ecosystem...",
        "competitive_advantages": ["Brand loyalty", "Ecosystem lock-in", "Premium pricing power"],
        "risk_factors": ["Regulatory scrutiny", "Supply chain concentration", "Market saturation"],
        "management_quality": "Strong track record of capital allocation and innovation"
      }},
      "competitive_analysis": {{
        "market_position": "Market leader in premium smartphones with 50%+ profit share",
        "growth_drivers": ["Services expansion", "India market penetration", "Vision Pro adoption"],
        "threats": ["Android competition", "EU regulations", "China geopolitical risk"],
        "industry_trends": "Shift to services, AI integration, spatial computing emergence"
      }},
      "technical_strategy": {{
        "chart_patterns": ["Ascending triangle", "Golden cross on 50/200 MA"],
        "support_levels": [170.0, 165.0, 160.0],
        "resistance_levels": [185.0, 190.0, 200.0],
        "entry_strategy": "Enter on pullback to $172-175 range with volume confirmation",
        "exit_strategy": "Take profits at $190, trailing stop at 8%",
        "stop_loss": 168.0
      }},
      "contextual_risks": {{
        "regulatory_risks": ["EU DMA compliance", "US antitrust investigations"],
        "geopolitical_risks": ["China-US tensions", "Taiwan supply chain risk"],
        "operational_risks": ["Supplier concentration", "Product launch delays"],
        "financial_risks": ["Currency headwinds", "Margin pressure from services mix"]
      }},
      "scenario_analysis": {{
        "bull_case": "Services accelerate to 30% of revenue, Vision Pro succeeds, India doubles TAM",
        "bull_probability": 0.25,
        "bull_target": 220.0,
        "base_case": "Steady iPhone replacement cycle, services grow 15% annually, margins stable",
        "base_probability": 0.50,
        "base_target": 190.0,
        "bear_case": "iPhone demand weakens, regulatory fines impact margins, China sales decline",
        "bear_probability": 0.25,
        "bear_target": 150.0
      }},
      "investment_thesis": "Apple represents a compelling risk/reward at current levels...[≥500 words]",
      "action_plan": "1. Accumulate on dips to $172-175\n2. Monitor Q1 earnings for services growth\n3. Set initial stop at $168\n4. Target $190 for 25% position trim\n5. Re-evaluate if breaks below $165"
    }}
    
    VALIDATION (Requirement 12.3-12.6):
    - If output fails validation, system will retry with explicit format instructions
    - After 2 failed attempts, fallback to Python-only analysis
    - Do NOT return tool calls instead of analysis
    - Ensure all required fields are present and properly formatted
  
  expected_output: "Structured QualitativeInsights with all required fields"
  output_pydantic: "QualitativeInsights"
  output_json: true
  agent: stock_analyst
```


## Data Models

### Core Pydantic Schemas

**Location**: `src/finwiz/schemas/hybrid_analysis/`

#### 1. FundamentalData (NEW)

```python
from pydantic import BaseModel, Field
from typing import Literal

class DataSourceAttribution(BaseModel):
    """Track which source provided each field."""
    source: Literal["yfinance", "alpha_vantage", "intrinio", "tiingo", "eod", "industry_average"]
    timestamp: datetime
    confidence: float = Field(ge=0.0, le=1.0, description="1.0 for real data, <1.0 for estimates")

class FundamentalData(BaseModel):
    """Fundamental data with source attribution."""
    ticker: str
    asset_class: str
    
    # Financial metrics
    roe: float | None = None
    debt_to_equity: float | None = None
    revenue_growth: float | None = None
    profit_margin: float | None = None
    
    # Source attribution (for data lineage)
    roe_source: DataSourceAttribution | None = None
    debt_to_equity_source: DataSourceAttribution | None = None
    revenue_growth_source: DataSourceAttribution | None = None
    profit_margin_source: DataSourceAttribution | None = None
    
    # Validation
    has_critical_fields: bool = Field(default=False)
    missing_fields: list[str] = Field(default_factory=list)
    
    model_config = {"extra": "forbid"}
```

#### 2. QuantitativeAnalysis (Enhanced)

```python
class QuantitativeAnalysis(BaseModel):
    """Python-calculated scores and grades."""
    ticker: str
    asset_class: str
    
    # Scores
    composite_score: float = Field(ge=0.0, le=1.0)
    fundamental_score: float = Field(ge=0.0, le=1.0)
    technical_score: float = Field(ge=0.0, le=1.0)
    risk_score: float = Field(ge=0.0, le=1.0)
    
    # Grade
    grade: Literal["A+", "A", "B", "C", "D", "F"]
    
    # Recommendation
    recommendation: Literal["BUY", "HOLD", "SELL"]
    
    # Confidence (reduced if using fallback data)
    confidence_level: float = Field(ge=0.0, le=1.0, default=1.0)
    
    # Data lineage
    data_sources_used: list[str] = Field(
        description="List of data sources used (e.g., ['yfinance', 'alpha_vantage'])"
    )
    
    # Metrics used in calculation
    metrics: dict[str, float] = Field(
        description="Raw metrics used (ROE, RSI, volatility, etc.)"
    )
    
    model_config = {"extra": "forbid"}
```


#### 3. QualitativeInsights (NEW)

```python
class SecAnalysisInsights(BaseModel):
    """Insights from SEC filings analysis."""
    business_model: str = Field(description="How the company makes money")
    competitive_advantages: list[str] = Field(description="Moats and differentiators")
    risk_factors: list[str] = Field(description="Material risks from 10-K")
    management_quality: str = Field(description="Assessment of leadership")

class CompetitiveAnalysisInsights(BaseModel):
    """Competitive positioning analysis."""
    market_position: str = Field(description="Market share and positioning")
    growth_drivers: list[str] = Field(description="Catalysts for growth")
    threats: list[str] = Field(description="Competitive threats")
    industry_trends: str = Field(description="Macro industry dynamics")

class TechnicalStrategyInsights(BaseModel):
    """Technical analysis and trading strategy."""
    chart_patterns: list[str] = Field(description="Identified patterns")
    support_levels: list[float] = Field(description="Key support prices")
    resistance_levels: list[float] = Field(description="Key resistance prices")
    entry_strategy: str = Field(description="Recommended entry approach")
    exit_strategy: str = Field(description="Recommended exit approach")
    stop_loss: float | None = Field(description="Suggested stop loss price")

class ContextualRiskInsights(BaseModel):
    """Contextual risk analysis beyond metrics."""
    regulatory_risks: list[str] = Field(description="Regulatory concerns")
    geopolitical_risks: list[str] = Field(description="Geopolitical factors")
    operational_risks: list[str] = Field(description="Operational challenges")
    financial_risks: list[str] = Field(description="Financial structure risks")

class ScenarioAnalysis(BaseModel):
    """Bull/base/bear scenario analysis."""
    bull_case: str = Field(description="Optimistic scenario")
    bull_probability: float = Field(ge=0.0, le=1.0)
    bull_target: float = Field(description="Price target in bull case")
    
    base_case: str = Field(description="Most likely scenario")
    base_probability: float = Field(ge=0.0, le=1.0)
    base_target: float = Field(description="Price target in base case")
    
    bear_case: str = Field(description="Pessimistic scenario")
    bear_probability: float = Field(ge=0.0, le=1.0)
    bear_target: float = Field(description="Price target in bear case")

class QualitativeInsights(BaseModel):
    """AI-generated contextual analysis."""
    ticker: str
    asset_class: str
    
    # Analysis components
    sec_insights: SecAnalysisInsights
    competitive_analysis: CompetitiveAnalysisInsights
    technical_strategy: TechnicalStrategyInsights
    contextual_risks: ContextualRiskInsights
    scenario_analysis: ScenarioAnalysis
    
    # Investment thesis
    investment_thesis: str = Field(
        min_length=500,
        description="Comprehensive investment thesis (≥500 words)"
    )
    
    # Action plan
    action_plan: str = Field(
        description="Specific steps for investor"
    )
    
    model_config = {"extra": "forbid"}
```


#### 4. EnrichedAnalysis (NEW)

```python
class EnrichedAnalysis(BaseModel):
    """Combined quantitative + qualitative analysis."""
    ticker: str
    asset_class: str
    
    # Quantitative (Python-calculated)
    quantitative: QuantitativeAnalysis
    
    # Qualitative (AI-generated)
    qualitative: QualitativeInsights
    
    # Final synthesis
    executive_summary: str = Field(
        min_length=200,
        description="AI-written executive summary combining both analyses"
    )
    
    # Metadata
    analysis_timestamp: datetime
    total_word_count: int = Field(ge=2000, description="Must be ≥2000 words")
    
    model_config = {"extra": "forbid"}
```

## Error Handling

### Data Acquisition Errors

**Strategy**: Graceful degradation with warnings (Requirement 11.4)

```python
class DataAcquisitionError(Exception):
    """Base exception for data acquisition failures."""
    pass

class DataUnavailableError(DataAcquisitionError):
    """All data sources failed (Requirement 11.4)."""
    def __init__(self, ticker: str, field: str, sources_tried: list[str]):
        self.ticker = ticker
        self.field = field
        self.sources_tried = sources_tried
        super().__init__(
            f"Failed to acquire {field} for {ticker}. "
            f"Tried sources: {', '.join(sources_tried)}"
        )

class InvalidDataError(DataAcquisitionError):
    """Data validation failed (Requirement 11.7)."""
    def __init__(self, ticker: str, field: str, value: Any, reason: str):
        self.ticker = ticker
        self.field = field
        self.value = value
        self.reason = reason
        super().__init__(
            f"Invalid {field} for {ticker}: {value} ({reason})"
        )

class TimeoutError(DataAcquisitionError):
    """Data acquisition exceeded timeout (Requirement 11.6)."""
    def __init__(self, ticker: str, elapsed: float, timeout: float):
        self.ticker = ticker
        self.elapsed = elapsed
        self.timeout = timeout
        super().__init__(
            f"Data acquisition for {ticker} exceeded {timeout}s timeout "
            f"(took {elapsed:.2f}s)"
        )
```

**Handling**:

```python
try:
    data = orchestrator.get_fundamental_data(ticker, asset_class, timeout=10.0)
except DataUnavailableError as e:
    logger.warning(
        f"Using industry averages for {e.field}: {e}. "
        f"Confidence reduced to 0.5 (Requirement 11.4)"
    )
    data = use_industry_averages(ticker, asset_class, e.field)
    data.confidence_level = 0.5  # Reduced confidence
except TimeoutError as e:
    logger.error(f"Data acquisition timeout: {e}")
    # Fall back to cached data or industry averages
    data = get_cached_or_industry_averages(ticker, asset_class)
except InvalidDataError as e:
    logger.warning(f"Invalid data rejected: {e}. Trying next source.")
    # Orchestrator automatically tries next source
```

### AI Output Validation Errors

**Strategy**: Retry with explicit format instructions, then fallback (Requirement 12.3-12.4)

```python
class AIOutputError(Exception):
    """Base exception for AI output issues."""
    pass

class OutputParsingError(AIOutputError):
    """Failed to parse AI output (Requirement 12.5)."""
    pass

class MissingRequiredFieldError(AIOutputError):
    """AI output missing required fields (Requirement 12.2)."""
    def __init__(self, missing_fields: list[str]):
        self.missing_fields = missing_fields
        super().__init__(
            f"AI output missing required fields: {', '.join(missing_fields)}"
        )

class ToolCallInsteadOfAnalysisError(AIOutputError):
    """AI returned tool calls instead of analysis (Requirement 12.6)."""
    pass
```

**Handling** (Requirement 12.3-12.4):

```python
max_retries = 2  # Requirement 12.4
for attempt in range(max_retries):
    try:
        result = crew.kickoff(inputs=inputs)
        
        # Validate structure before field extraction (Requirement 12.5)
        if not isinstance(result, dict):
            raise OutputParsingError(f"Expected dict, got {type(result)}")
        
        # Check for tool calls instead of analysis (Requirement 12.6)
        if "tool_calls" in result or "function_call" in result:
            raise ToolCallInsteadOfAnalysisError(
                "AI returned tool calls instead of analysis"
            )
        
        # Validate with Pydantic (Requirement 12.1)
        validated = QualitativeInsights.model_validate(result)
        
        # Verify required fields present (Requirement 12.2)
        required_fields = [
            "sec_insights", "competitive_analysis", "technical_strategy",
            "contextual_risks", "scenario_analysis", "investment_thesis",
            "action_plan"
        ]
        missing = [f for f in required_fields if not getattr(validated, f, None)]
        if missing:
            raise MissingRequiredFieldError(missing)
        
        break  # Success
        
    except (ValidationError, OutputParsingError, MissingRequiredFieldError, 
            ToolCallInsteadOfAnalysisError) as e:
        if attempt < max_retries - 1:
            logger.warning(
                f"AI output validation failed (attempt {attempt+1}/{max_retries}): {e}"
            )
            # Retry with explicit format instructions (Requirement 12.3)
            inputs["format_instructions"] = get_explicit_format_example()
            inputs["retry_context"] = f"Previous attempt failed: {str(e)}"
        else:
            logger.error(
                f"AI output validation failed after {max_retries} attempts. "
                f"Falling back to Python-only analysis (Requirement 12.4)"
            )
            # Fallback to Python-only analysis
            return create_python_only_analysis(quantitative)
```

### Orchestrator Error Handling

**Strategy**: Maintain both outputs separately, graceful fallback (Requirement 9.4-9.5)

```python
class HybridAnalysisOrchestrator:
    def analyze_holding(self, ticker: str, asset_class: str) -> EnrichedAnalysis:
        """
        Orchestrate hybrid analysis with error handling.
        
        Implements Requirements 9.1-9.5.
        """
        try:
            # Step 1: Python calculations (Requirement 9.1)
            quantitative = self._calculate_quantitative(ticker, asset_class)
            
            # Step 2: Pass to AI as INPUT (Requirement 9.2)
            qualitative = self._analyze_qualitative(ticker, asset_class, quantitative)
            
            # Step 3: Merge results (Requirement 9.3)
            enriched = self._merge_analyses(quantitative, qualitative)
            
            # Step 4: Store both separately (Requirement 9.4)
            self._store_results(ticker, quantitative, qualitative, enriched)
            
            return enriched
            
        except AIOutputError as e:
            logger.warning(f"AI analysis failed: {e}. Using Python-only (Requirement 9.5)")
            return self._create_python_only_enriched(quantitative)
        
        except DataAcquisitionError as e:
            logger.error(f"Data acquisition failed: {e}")
            raise  # Cannot proceed without data
```


## AI Output Format Enforcement (NEW)

### Purpose

Ensure AI crews return structured, parseable output to prevent grade/score extraction failures (Requirement 12).

### Implementation Strategy

**1. Task Description Format** (Requirement 12.7):

All AI tasks must include:
- Explicit output format specification
- Complete example output with all required fields
- Field-by-field descriptions
- Validation requirements

**2. Pydantic Schema Enforcement** (Requirement 12.1):

```python
# In tasks.yaml
stock_analysis_task:
  output_pydantic: "QualitativeInsights"  # Strict schema validation
  output_json: true                        # Machine-readable output
```

**3. Pre-Validation Checks** (Requirement 12.5):

```python
def validate_ai_output_structure(result: Any) -> dict:
    """
    Validate AI output structure before Pydantic validation.
    
    Checks (Requirement 12.5):
    - Result is a dict (not string, list, or other type)
    - No tool_calls or function_call keys present (Requirement 12.6)
    - Contains expected top-level keys
    
    Returns:
        Validated dict ready for Pydantic parsing
    
    Raises:
        OutputParsingError: Structure validation failed
        ToolCallInsteadOfAnalysisError: AI returned tool calls
    """
    if not isinstance(result, dict):
        raise OutputParsingError(f"Expected dict, got {type(result).__name__}")
    
    # Check for tool calls (Requirement 12.6)
    if "tool_calls" in result or "function_call" in result:
        raise ToolCallInsteadOfAnalysisError(
            "AI returned tool calls instead of analysis. "
            "Retrying with corrected prompt."
        )
    
    # Verify expected structure
    expected_keys = {
        "ticker", "asset_class", "sec_insights", "competitive_analysis",
        "technical_strategy", "contextual_risks", "scenario_analysis",
        "investment_thesis", "action_plan"
    }
    
    missing_keys = expected_keys - set(result.keys())
    if missing_keys:
        raise MissingRequiredFieldError(list(missing_keys))
    
    return result
```

**4. Retry Logic with Format Instructions** (Requirement 12.3):

```python
def get_explicit_format_example() -> str:
    """
    Generate explicit format instructions for retry attempts.
    
    Used when initial AI output fails validation (Requirement 12.3).
    """
    return """
    CRITICAL: Your output MUST be a valid JSON object matching this EXACT structure:
    
    {
      "ticker": "AAPL",
      "asset_class": "stock",
      "sec_insights": {
        "business_model": "string (required)",
        "competitive_advantages": ["string", "string"],
        "risk_factors": ["string", "string"],
        "management_quality": "string (required)"
      },
      "competitive_analysis": {
        "market_position": "string (required)",
        "growth_drivers": ["string", "string"],
        "threats": ["string", "string"],
        "industry_trends": "string (required)"
      },
      "technical_strategy": {
        "chart_patterns": ["string", "string"],
        "support_levels": [170.0, 165.0],
        "resistance_levels": [185.0, 190.0],
        "entry_strategy": "string (required)",
        "exit_strategy": "string (required)",
        "stop_loss": 168.0
      },
      "contextual_risks": {
        "regulatory_risks": ["string"],
        "geopolitical_risks": ["string"],
        "operational_risks": ["string"],
        "financial_risks": ["string"]
      },
      "scenario_analysis": {
        "bull_case": "string (required)",
        "bull_probability": 0.25,
        "bull_target": 220.0,
        "base_case": "string (required)",
        "base_probability": 0.50,
        "base_target": 190.0,
        "bear_case": "string (required)",
        "bear_probability": 0.25,
        "bear_target": 150.0
      },
      "investment_thesis": "string (minimum 500 words)",
      "action_plan": "string (specific steps)"
    }
    
    DO NOT:
    - Return tool calls or function calls
    - Return a string instead of JSON object
    - Omit any required fields
    - Use null for required fields
    
    DO:
    - Return valid JSON matching the structure above
    - Include all required fields
    - Provide substantive content (not placeholders)
    - Ensure investment_thesis is at least 500 words
    """
```

**5. Fallback to Python-Only Analysis** (Requirement 12.4):

```python
def create_python_only_analysis(quantitative: QuantitativeAnalysis) -> EnrichedAnalysis:
    """
    Create fallback analysis when AI fails after retries.
    
    Implements Requirement 12.4: After 2 failed attempts, fall back to
    Python-only analysis with warning logged.
    """
    logger.warning(
        f"Creating Python-only analysis for {quantitative.ticker}. "
        f"AI analysis failed after 2 retry attempts."
    )
    
    # Create minimal qualitative insights from quantitative data
    qualitative = QualitativeInsights(
        ticker=quantitative.ticker,
        asset_class=quantitative.asset_class,
        sec_insights=SecAnalysisInsights(
            business_model="Analysis unavailable - using quantitative data only",
            competitive_advantages=[],
            risk_factors=["AI analysis unavailable"],
            management_quality="Not assessed"
        ),
        competitive_analysis=CompetitiveAnalysisInsights(
            market_position="Not assessed",
            growth_drivers=[],
            threats=[],
            industry_trends="Not assessed"
        ),
        technical_strategy=TechnicalStrategyInsights(
            chart_patterns=[],
            support_levels=[],
            resistance_levels=[],
            entry_strategy=f"Based on quantitative grade: {quantitative.grade}",
            exit_strategy="Monitor quantitative metrics",
            stop_loss=None
        ),
        contextual_risks=ContextualRiskInsights(
            regulatory_risks=[],
            geopolitical_risks=[],
            operational_risks=[],
            financial_risks=[]
        ),
        scenario_analysis=ScenarioAnalysis(
            bull_case="Quantitative metrics improve",
            bull_probability=0.33,
            bull_target=None,
            base_case="Quantitative metrics stable",
            base_probability=0.34,
            base_target=None,
            bear_case="Quantitative metrics deteriorate",
            bear_probability=0.33,
            bear_target=None
        ),
        investment_thesis=(
            f"Analysis based on quantitative metrics only. "
            f"Grade: {quantitative.grade}, "
            f"Composite Score: {quantitative.composite_score:.2f}. "
            f"Recommendation: {quantitative.recommendation}. "
            f"AI qualitative analysis unavailable."
        ),
        action_plan=f"Follow quantitative recommendation: {quantitative.recommendation}"
    )
    
    return EnrichedAnalysis(
        ticker=quantitative.ticker,
        asset_class=quantitative.asset_class,
        quantitative=quantitative,
        qualitative=qualitative,
        executive_summary=(
            f"Python-only analysis for {quantitative.ticker}. "
            f"Grade: {quantitative.grade}. "
            f"Recommendation: {quantitative.recommendation}. "
            f"AI analysis unavailable - using quantitative metrics only."
        ),
        analysis_timestamp=datetime.now(UTC),
        total_word_count=len(qualitative.investment_thesis.split()),
        ai_analysis_available=False  # Flag for reporting
    )
```

### Validation Flow

```
AI Crew Execution
       ↓
Pre-Validation (structure check)
       ↓
   Valid? ──No──→ Retry with format instructions (attempt 1)
       ↓                           ↓
      Yes                    Pre-Validation
       ↓                           ↓
Pydantic Validation          Valid? ──No──→ Retry with format instructions (attempt 2)
       ↓                           ↓                           ↓
   Valid? ──No──→ Retry           Yes                    Pre-Validation
       ↓                           ↓                           ↓
      Yes                    Pydantic Validation          Valid? ──No──→ Fallback to Python-only
       ↓                           ↓                           ↓
Field Completeness Check       Valid? ──No──→ Retry           Yes
       ↓                           ↓                           ↓
   Complete? ──No──→ Retry        Yes                    Pydantic Validation
       ↓                           ↓                           ↓
      Yes                    Field Completeness          Valid? ──No──→ Fallback to Python-only
       ↓                           ↓                           ↓
   SUCCESS                    Complete? ──No──→ Retry        Yes
                                   ↓                           ↓
                                  Yes                    Field Completeness
                                   ↓                           ↓
                               SUCCESS                    Complete? ──No──→ Fallback to Python-only
                                                               ↓
                                                              Yes
                                                               ↓
                                                           SUCCESS
```

## Testing Strategy

### Unit Tests

**Data Source Adapters** (`tests/unit/data/adapters/`):

```python
def test_yfinance_adapter_extracts_roe(mocker):
    """Test yfinance adapter extracts ROE correctly."""
    mock_ticker = mocker.Mock()
    mock_ticker.info = {"returnOnEquity": 0.25}
    mocker.patch("yfinance.Ticker", return_value=mock_ticker)
    
    adapter = YFinanceAdapter()
    data = adapter.get_fundamentals("AAPL")
    
    assert data["roe"] == 0.25

def test_alpha_vantage_adapter_handles_missing_data(mocker):
    """Test Alpha Vantage adapter handles missing fields."""
    mock_response = {"Symbol": "DELL"}  # Missing ROE
    mocker.patch("alpha_vantage.fundamentaldata.FundamentalData.get_company_overview", 
                 return_value=(mock_response, None))
    
    adapter = AlphaVantageAdapter()
    data = adapter.get_fundamentals("DELL")
    
    assert data["roe"] is None
```

**Data Source Orchestrator** (`tests/unit/data/`):

```python
def test_orchestrator_falls_back_to_alpha_vantage(mocker):
    """Test orchestrator tries Alpha Vantage when yfinance fails (Requirement 11.1)."""
    # Mock yfinance failure
    mocker.patch("finwiz.data.adapters.yfinance_adapter.YFinanceAdapter.get_fundamentals",
                 side_effect=Exception("yfinance failed"))
    
    # Mock Alpha Vantage success
    mocker.patch("finwiz.data.adapters.alpha_vantage_adapter.AlphaVantageAdapter.get_fundamentals",
                 return_value={"roe": 0.20, "debt_to_equity": 0.5})
    
    orchestrator = DataSourceOrchestrator()
    data = orchestrator.get_fundamental_data("DELL", "stock")
    
    assert data.roe == 0.20
    assert data.roe_source.source == "alpha_vantage"

def test_orchestrator_uses_industry_averages_as_last_resort(mocker):
    """Test orchestrator uses industry averages when all sources fail (Requirement 11.4)."""
    # Mock all sources failing
    mocker.patch("finwiz.data.adapters.yfinance_adapter.YFinanceAdapter.get_fundamentals",
                 side_effect=Exception("failed"))
    mocker.patch("finwiz.data.adapters.alpha_vantage_adapter.AlphaVantageAdapter.get_fundamentals",
                 side_effect=Exception("failed"))
    mocker.patch("finwiz.data.adapters.intrinio_adapter.IntrinioAdapter.get_fundamentals",
                 side_effect=Exception("failed"))
    mocker.patch("finwiz.data.adapters.tiingo_adapter.TiingoAdapter.get_fundamentals",
                 side_effect=Exception("failed"))
    mocker.patch("finwiz.data.adapters.eod_adapter.EODAdapter.get_fundamentals",
                 side_effect=Exception("failed"))
    
    orchestrator = DataSourceOrchestrator()
    data = orchestrator.get_fundamental_data("UNKNOWN", "stock")
    
    assert data.roe is not None  # Industry average
    assert data.roe_source.source == "industry_average"
    assert data.roe_source.confidence == 0.5  # Reduced confidence (Requirement 11.4)

def test_orchestrator_completes_within_timeout(mocker):
    """Test orchestrator completes data acquisition within 10 seconds (Requirement 11.6)."""
    import time
    
    # Mock slow source (3 seconds each)
    def slow_get_fundamentals(ticker: str, timeout: float = 3.0):
        time.sleep(2.9)  # Just under timeout
        return {"roe": 0.20, "debt_to_equity": 0.5}
    
    mocker.patch("finwiz.data.adapters.yfinance_adapter.YFinanceAdapter.get_fundamentals",
                 side_effect=slow_get_fundamentals)
    
    orchestrator = DataSourceOrchestrator()
    start = time.time()
    data = orchestrator.get_fundamental_data("AAPL", "stock", timeout=10.0)
    elapsed = time.time() - start
    
    assert elapsed < 10.0  # Within timeout
    assert data.roe == 0.20

def test_orchestrator_rejects_invalid_data(mocker):
    """Test orchestrator rejects invalid data and tries next source (Requirement 11.7)."""
    # Mock yfinance returning invalid data (negative ROE)
    mocker.patch("finwiz.data.adapters.yfinance_adapter.YFinanceAdapter.get_fundamentals",
                 return_value={"roe": -2.0, "debt_to_equity": 0.5})  # Invalid
    
    # Mock Alpha Vantage returning valid data
    mocker.patch("finwiz.data.adapters.alpha_vantage_adapter.AlphaVantageAdapter.get_fundamentals",
                 return_value={"roe": 0.20, "debt_to_equity": 0.5})  # Valid
    
    orchestrator = DataSourceOrchestrator()
    data = orchestrator.get_fundamental_data("AAPL", "stock")
    
    # Should use Alpha Vantage data (valid), not yfinance (invalid)
    assert data.roe == 0.20
    assert data.roe_source.source == "alpha_vantage"

def test_orchestrator_logs_data_source_for_lineage(mocker):
    """Test orchestrator logs which source provided each field (Requirement 11.5)."""
    mocker.patch("finwiz.data.adapters.yfinance_adapter.YFinanceAdapter.get_fundamentals",
                 return_value={"roe": 0.20, "debt_to_equity": 0.5})
    
    orchestrator = DataSourceOrchestrator()
    data = orchestrator.get_fundamental_data("AAPL", "stock")
    
    # Verify data lineage tracking
    assert data.roe_source is not None
    assert data.roe_source.source == "yfinance"
    assert data.roe_source.timestamp is not None
    assert data.roe_source.confidence == 1.0
    
    assert data.debt_to_equity_source is not None
    assert data.debt_to_equity_source.source == "yfinance"

def test_orchestrator_tries_international_sources(mocker):
    """Test orchestrator tries Tiingo/EOD for international tickers (Requirement 11.3)."""
    # Mock US sources failing
    mocker.patch("finwiz.data.adapters.yfinance_adapter.YFinanceAdapter.get_fundamentals",
                 side_effect=Exception("failed"))
    mocker.patch("finwiz.data.adapters.alpha_vantage_adapter.AlphaVantageAdapter.get_fundamentals",
                 side_effect=Exception("failed"))
    mocker.patch("finwiz.data.adapters.intrinio_adapter.IntrinioAdapter.get_fundamentals",
                 side_effect=Exception("failed"))
    
    # Mock Tiingo success
    mocker.patch("finwiz.data.adapters.tiingo_adapter.TiingoAdapter.get_fundamentals",
                 return_value={"roe": 0.18, "debt_to_equity": 0.6})
    
    orchestrator = DataSourceOrchestrator()
    data = orchestrator.get_fundamental_data("0700.HK", "stock")  # Tencent (Hong Kong)
    
    assert data.roe == 0.18
    assert data.roe_source.source == "tiingo"
```

**Quantitative Analysis** (`tests/unit/scoring/`):

```python
def test_scorer_tracks_data_lineage(mocker):
    """Test scorer tracks which source provided each field."""
    data = FundamentalData(
        ticker="AAPL",
        asset_class="stock",
        roe=0.25,
        roe_source=DataSourceAttribution(source="yfinance", timestamp=datetime.now(), confidence=1.0),
        debt_to_equity=0.3,
        debt_to_equity_source=DataSourceAttribution(source="alpha_vantage", timestamp=datetime.now(), confidence=1.0)
    )
    
    scorer = DeepAnalysisScorer()
    result = scorer.calculate_composite_score("AAPL", "stock", data)
    
    assert "yfinance" in result.data_sources_used
    assert "alpha_vantage" in result.data_sources_used
```


**AI Output Format Enforcement** (`tests/unit/ai/`):

```python
def test_validate_ai_output_structure_success():
    """Test AI output structure validation passes with valid output (Requirement 12.5)."""
    valid_output = {
        "ticker": "AAPL",
        "asset_class": "stock",
        "sec_insights": {...},
        "competitive_analysis": {...},
        "technical_strategy": {...},
        "contextual_risks": {...},
        "scenario_analysis": {...},
        "investment_thesis": "...",
        "action_plan": "..."
    }
    
    result = validate_ai_output_structure(valid_output)
    assert result == valid_output

def test_validate_ai_output_rejects_tool_calls():
    """Test AI output validation rejects tool calls (Requirement 12.6)."""
    invalid_output = {
        "tool_calls": [{"name": "some_tool", "args": {}}],
        "ticker": "AAPL"
    }
    
    with pytest.raises(ToolCallInsteadOfAnalysisError):
        validate_ai_output_structure(invalid_output)

def test_validate_ai_output_rejects_non_dict():
    """Test AI output validation rejects non-dict types (Requirement 12.5)."""
    with pytest.raises(OutputParsingError):
        validate_ai_output_structure("string output")
    
    with pytest.raises(OutputParsingError):
        validate_ai_output_structure(["list", "output"])

def test_validate_ai_output_detects_missing_fields():
    """Test AI output validation detects missing required fields (Requirement 12.2)."""
    incomplete_output = {
        "ticker": "AAPL",
        "asset_class": "stock",
        "sec_insights": {...}
        # Missing other required fields
    }
    
    with pytest.raises(MissingRequiredFieldError) as exc_info:
        validate_ai_output_structure(incomplete_output)
    
    assert "competitive_analysis" in exc_info.value.missing_fields
    assert "technical_strategy" in exc_info.value.missing_fields

def test_ai_output_retry_with_format_instructions(mocker):
    """Test AI output retry includes format instructions (Requirement 12.3)."""
    # Mock crew that fails first time, succeeds second time
    mock_crew = mocker.Mock()
    mock_crew.kickoff.side_effect = [
        {"invalid": "output"},  # First attempt fails
        {  # Second attempt succeeds
            "ticker": "AAPL",
            "asset_class": "stock",
            "sec_insights": {...},
            # ... all required fields
        }
    ]
    
    result = analyze_with_retry(mock_crew, inputs={})
    
    # Verify retry was attempted
    assert mock_crew.kickoff.call_count == 2
    
    # Verify format instructions added on retry
    second_call_inputs = mock_crew.kickoff.call_args_list[1][1]["inputs"]
    assert "format_instructions" in second_call_inputs

def test_ai_output_fallback_after_max_retries(mocker):
    """Test fallback to Python-only after 2 failed attempts (Requirement 12.4)."""
    # Mock crew that always fails
    mock_crew = mocker.Mock()
    mock_crew.kickoff.return_value = {"invalid": "output"}
    
    quantitative = QuantitativeAnalysis(
        ticker="AAPL",
        asset_class="stock",
        composite_score=0.85,
        grade="A",
        recommendation="BUY",
        # ... other fields
    )
    
    result = analyze_with_retry(mock_crew, inputs={}, quantitative=quantitative)
    
    # Verify max retries attempted
    assert mock_crew.kickoff.call_count == 2
    
    # Verify fallback to Python-only
    assert isinstance(result, EnrichedAnalysis)
    assert result.ai_analysis_available is False
    assert result.qualitative.investment_thesis.startswith("Analysis based on quantitative metrics only")

def test_pydantic_validation_with_output_pydantic(mocker):
    """Test Pydantic validation enforced via output_pydantic (Requirement 12.1)."""
    # Mock crew output
    crew_output = {
        "ticker": "AAPL",
        "asset_class": "stock",
        "sec_insights": {
            "business_model": "...",
            "competitive_advantages": ["..."],
            "risk_factors": ["..."],
            "management_quality": "..."
        },
        # ... all required fields
    }
    
    # Validate with Pydantic
    validated = QualitativeInsights.model_validate(crew_output)
    
    assert validated.ticker == "AAPL"
    assert isinstance(validated.sec_insights, SecAnalysisInsights)
    assert len(validated.sec_insights.competitive_advantages) > 0
```

### Integration Tests

**End-to-End Hybrid Analysis** (`tests/integration/`):

```python
@pytest.mark.integration
def test_hybrid_analysis_with_real_data():
    """Test complete hybrid analysis with real API calls."""
    orchestrator = HybridAnalysisOrchestrator()
    
    result = orchestrator.analyze_holding("AAPL", "stock")
    
    # Verify quantitative analysis
    assert result.quantitative.grade in ["A+", "A", "B", "C", "D", "F"]
    assert 0.0 <= result.quantitative.composite_score <= 1.0
    
    # Verify qualitative analysis
    assert len(result.qualitative.investment_thesis) >= 500
    assert len(result.qualitative.sec_insights.competitive_advantages) > 0
    
    # Verify enrichment
    assert result.total_word_count >= 2000
    assert len(result.executive_summary) >= 200

@pytest.mark.integration
def test_data_source_fallback_with_problematic_ticker():
    """Test fallback behavior with ticker that fails on yfinance (Requirement 11.1-11.4)."""
    orchestrator = DataSourceOrchestrator()
    
    # DELL often fails on yfinance
    data = orchestrator.get_fundamental_data("DELL", "stock", timeout=10.0)
    
    # Should have data from fallback source
    assert data.roe is not None
    assert data.debt_to_equity is not None
    
    # Should track which source provided data (Requirement 11.5)
    assert data.roe_source.source in ["alpha_vantage", "intrinio", "tiingo", "eod", "industry_average"]
    
    # Confidence should be reduced if using industry averages (Requirement 11.4)
    if data.roe_source.source == "industry_average":
        assert data.roe_source.confidence == 0.5

@pytest.mark.integration
def test_data_acquisition_performance():
    """Test data acquisition completes within performance requirements (Requirement 11.6)."""
    import time
    
    orchestrator = DataSourceOrchestrator()
    
    start = time.time()
    data = orchestrator.get_fundamental_data("AAPL", "stock", timeout=10.0)
    elapsed = time.time() - start
    
    # Should complete within 10 seconds
    assert elapsed <= 10.0
    
    # Should have valid data
    assert data.roe is not None
    assert data.debt_to_equity is not None

@pytest.mark.integration
def test_ai_output_format_enforcement_with_real_crew():
    """Test AI output format enforcement with real crew execution (Requirement 12.1-12.7)."""
    from finwiz.crews.stock_crew.stock_crew import StockCrew
    
    # Create quantitative analysis
    quantitative = QuantitativeAnalysis(
        ticker="AAPL",
        asset_class="stock",
        composite_score=0.85,
        grade="A",
        recommendation="BUY",
        # ... other fields
    )
    
    # Execute crew with format enforcement
    crew = StockCrew()
    inputs = {
        "ticker": "AAPL",
        "asset_class": "stock",
        "quantitative": quantitative.model_dump()
    }
    
    result = crew.crew().kickoff(inputs=inputs)
    
    # Validate output structure (Requirement 12.5)
    validated_structure = validate_ai_output_structure(result)
    
    # Validate with Pydantic (Requirement 12.1)
    qualitative = QualitativeInsights.model_validate(validated_structure)
    
    # Verify required fields present (Requirement 12.2)
    assert qualitative.sec_insights is not None
    assert qualitative.competitive_analysis is not None
    assert qualitative.technical_strategy is not None
    assert qualitative.contextual_risks is not None
    assert qualitative.scenario_analysis is not None
    assert len(qualitative.investment_thesis) >= 500  # Minimum length
    assert qualitative.action_plan is not None
    
    # Verify no tool calls returned (Requirement 12.6)
    assert "tool_calls" not in result
    assert "function_call" not in result
```

### Property-Based Tests

**Data Validation Properties** (`tests/property/`):

```python
from hypothesis import given, strategies as st

@given(
    roe=st.floats(min_value=-1.0, max_value=2.0),
    debt_to_equity=st.floats(min_value=0.0, max_value=10.0)
)
def test_scorer_handles_all_valid_metric_ranges(roe, debt_to_equity):
    """Property: Scorer should handle all valid metric ranges without crashing."""
    data = FundamentalData(
        ticker="TEST",
        asset_class="stock",
        roe=roe,
        debt_to_equity=debt_to_equity,
        roe_source=DataSourceAttribution(source="test", timestamp=datetime.now(), confidence=1.0),
        debt_to_equity_source=DataSourceAttribution(source="test", timestamp=datetime.now(), confidence=1.0)
    )
    
    scorer = DeepAnalysisScorer()
    result = scorer.calculate_composite_score("TEST", "stock", data)
    
    # Should always produce valid output
    assert result.grade in ["A+", "A", "B", "C", "D", "F"]
    assert 0.0 <= result.composite_score <= 1.0
```


## Performance Considerations

### Data Source Selection Strategy

**Primary Source (yfinance)**:
- **Speed**: Fastest (no API key required, direct Yahoo Finance access)
- **Coverage**: Excellent for US stocks, good for major international stocks
- **Limitations**: Unreliable for fundamentals (ROE, debt_to_equity often missing)
- **Use Case**: First attempt for all tickers

**Secondary Source (Alpha Vantage)**:
- **Speed**: Moderate (500 calls/day free tier)
- **Coverage**: 60+ exchanges, comprehensive fundamentals
- **Strengths**: Reliable ROE, debt_to_equity, profit margins
- **API**: `from alpha_vantage.fundamentaldata import FundamentalData`
- **Use Case**: Fallback when yfinance missing fundamentals

**Tertiary Source (Intrinio)**:
- **Speed**: Moderate (limited free tier)
- **Coverage**: SEC filings, standardized financials
- **Strengths**: Most authoritative (direct from SEC)
- **API**: `import intrinio_sdk as intrinio`
- **Use Case**: Fallback when Alpha Vantage fails, especially for SEC data

**International Fallback (Tiingo)**:
- **Speed**: Fast (99.9% uptime, 500 symbols free)
- **Coverage**: Excellent for international stocks (Swiss, German, Asian exchanges)
- **Strengths**: Better international coverage than yfinance
- **API**: `from tiingo import TiingoClient`
- **Use Case**: Specific fallback for non-US tickers (KUD.SW, MCHA.F, etc.)

### Caching Strategy

**Data Acquisition Cache**:
```python
# Cache successful data fetches for 24 hours
@lru_cache(maxsize=1000)
def get_fundamental_data_cached(ticker: str, asset_class: str, date: str) -> FundamentalData:
    """Cache fundamental data by ticker and date."""
    return orchestrator.get_fundamental_data(ticker, asset_class)
```

**AI Analysis Cache**:
```python
# Cache AI analysis for 7 days (qualitative insights change slowly)
@lru_cache(maxsize=500)
def get_qualitative_insights_cached(ticker: str, quant_hash: str) -> QualitativeInsights:
    """Cache AI insights by ticker and quantitative analysis hash."""
    return crew.kickoff(inputs={"ticker": ticker, ...})
```


## Implementation Details

### Data Source Adapter Implementations

#### Alpha Vantage Adapter

```python
from alpha_vantage.fundamentaldata import FundamentalData
import os

class AlphaVantageAdapter:
    """Adapter for Alpha Vantage API."""
    
    def __init__(self):
        self.api_key = os.getenv('ALPHA_VANTAGE_KEY')
        if not self.api_key:
            raise ValueError("ALPHA_VANTAGE_KEY not set")
        self.fd = FundamentalData(key=self.api_key, output_format='json')
    
    def get_fundamentals(self, ticker: str) -> dict:
        """
        Extract fundamentals from Alpha Vantage.
        
        Returns dict with:
        - roe: Return on Equity (decimal, e.g., 0.25 for 25%)
        - debt_to_equity: Debt to Equity ratio
        - revenue_growth: Revenue growth rate
        - profit_margin: Profit margin
        """
        try:
            data, meta = self.fd.get_company_overview(ticker)
            
            return {
                'roe': float(data.get('ReturnOnEquityTTM', 0)) if data.get('ReturnOnEquityTTM') else None,
                'debt_to_equity': float(data.get('DebtToEquityRatio', 0)) if data.get('DebtToEquityRatio') else None,
                'revenue_growth': float(data.get('QuarterlyRevenueGrowthYOY', 0)) if data.get('QuarterlyRevenueGrowthYOY') else None,
                'profit_margin': float(data.get('ProfitMargin', 0)) if data.get('ProfitMargin') else None,
            }
        except Exception as e:
            logger.error(f"Alpha Vantage failed for {ticker}: {e}")
            return {}
```

#### Intrinio Adapter

```python
import intrinio_sdk as intrinio
import os

class IntrinioAdapter:
    """Adapter for Intrinio API."""
    
    def __init__(self):
        self.api_key = os.getenv('INTRINIO_API_KEY')
        if not self.api_key:
            raise ValueError("INTRINIO_API_KEY not set")
        intrinio.ApiClient().set_api_key(self.api_key)
        intrinio.ApiClient().allow_retries(True)
    
    def get_fundamentals(self, ticker: str) -> dict:
        """
        Extract fundamentals from Intrinio SEC filings.
        
        Uses standardized financial data from most recent filing.
        """
        try:
            company_api = intrinio.CompanyApi()
            
            # Get most recent fundamental
            fundamentals = company_api.get_company_fundamentals(
                ticker,
                latest_only=True,
                page_size=1
            )
            
            if not fundamentals.fundamentals:
                return {}
            
            fundamental_id = fundamentals.fundamentals[0].id
            
            # Get standardized financials
            fund_api = intrinio.FundamentalsApi()
            financials = fund_api.get_fundamental_standardized_financials(fundamental_id)
            
            # Extract metrics
            metrics = {}
            for item in financials.standardized_financials:
                if item.data_tag.tag == 'roe':
                    metrics['roe'] = float(item.value) if item.value else None
                elif item.data_tag.tag == 'debt_to_equity':
                    metrics['debt_to_equity'] = float(item.value) if item.value else None
                elif item.data_tag.tag == 'revenue_growth':
                    metrics['revenue_growth'] = float(item.value) if item.value else None
                elif item.data_tag.tag == 'profit_margin':
                    metrics['profit_margin'] = float(item.value) if item.value else None
            
            return metrics
            
        except Exception as e:
            logger.error(f"Intrinio failed for {ticker}: {e}")
            return {}
```

#### Tiingo Adapter

```python
from tiingo import TiingoClient
import os

class TiingoAdapter:
    """Adapter for Tiingo API (better for international stocks)."""
    
    def __init__(self):
        self.api_key = os.getenv('TIINGO_API_KEY')
        if not self.api_key:
            raise ValueError("TIINGO_API_KEY not set")
        self.client = TiingoClient({'api_key': self.api_key})
    
    def get_fundamentals(self, ticker: str) -> dict:
        """
        Extract fundamentals from Tiingo.
        
        Tiingo provides fundamentals through their daily API.
        """
        try:
            # Get fundamentals daily data
            fundamentals = self.client.get_fundamentals_daily(
                ticker,
                startDate='2024-01-01',  # Recent data
                endDate='2024-12-31'
            )
            
            if not fundamentals:
                return {}
            
            # Get most recent data point
            latest = fundamentals[-1]
            
            return {
                'roe': latest.get('roe'),
                'debt_to_equity': latest.get('debtToEquity'),
                'revenue_growth': latest.get('revenueGrowth'),
                'profit_margin': latest.get('profitMargin'),
            }
            
        except Exception as e:
            logger.error(f"Tiingo failed for {ticker}: {e}")
            return {}
```


### Data Source Orchestrator Implementation

```python
class DataSourceOrchestrator:
    """Orchestrates data acquisition with automatic fallbacks."""
    
    def __init__(self):
        self.yfinance_adapter = YFinanceAdapter()
        self.alpha_vantage_adapter = AlphaVantageAdapter()
        self.intrinio_adapter = IntrinioAdapter()
        self.tiingo_adapter = TiingoAdapter()
    
    def get_fundamental_data(
        self, 
        ticker: str, 
        asset_class: str
    ) -> FundamentalData:
        """
        Get fundamental data with waterfall fallback strategy.
        
        Waterfall:
        1. yfinance (fastest)
        2. Alpha Vantage (better fundamentals)
        3. Intrinio (SEC filings)
        4. Tiingo (if international)
        5. Industry averages (last resort)
        """
        sources_tried = []
        
        # Try 1: yfinance
        try:
            data = self.yfinance_adapter.get_fundamentals(ticker)
            if self._has_critical_fields(data, asset_class):
                return self._create_fundamental_data(
                    ticker, asset_class, data, "yfinance", sources_tried
                )
            sources_tried.append("yfinance")
        except Exception as e:
            logger.warning(f"yfinance failed for {ticker}: {e}")
            sources_tried.append("yfinance")
        
        # Try 2: Alpha Vantage
        try:
            data = self.alpha_vantage_adapter.get_fundamentals(ticker)
            if self._has_critical_fields(data, asset_class):
                return self._create_fundamental_data(
                    ticker, asset_class, data, "alpha_vantage", sources_tried
                )
            sources_tried.append("alpha_vantage")
        except Exception as e:
            logger.warning(f"Alpha Vantage failed for {ticker}: {e}")
            sources_tried.append("alpha_vantage")
        
        # Try 3: Intrinio
        try:
            data = self.intrinio_adapter.get_fundamentals(ticker)
            if self._has_critical_fields(data, asset_class):
                return self._create_fundamental_data(
                    ticker, asset_class, data, "intrinio", sources_tried
                )
            sources_tried.append("intrinio")
        except Exception as e:
            logger.warning(f"Intrinio failed for {ticker}: {e}")
            sources_tried.append("intrinio")
        
        # Try 4: Tiingo (if international)
        if self._is_international(ticker):
            try:
                data = self.tiingo_adapter.get_fundamentals(ticker)
                if self._has_critical_fields(data, asset_class):
                    return self._create_fundamental_data(
                        ticker, asset_class, data, "tiingo", sources_tried
                    )
                sources_tried.append("tiingo")
            except Exception as e:
                logger.warning(f"Tiingo failed for {ticker}: {e}")
                sources_tried.append("tiingo")
        
        # Last resort: Industry averages
        logger.warning(
            f"All sources failed for {ticker}. Using industry averages. "
            f"Sources tried: {sources_tried}"
        )
        data = self._get_industry_averages(ticker, asset_class)
        return self._create_fundamental_data(
            ticker, asset_class, data, "industry_average", sources_tried, confidence=0.5
        )
    
    def _has_critical_fields(self, data: dict, asset_class: str) -> bool:
        """Check if data has critical fields for the asset class."""
        if asset_class == "stock":
            return data.get('roe') is not None and data.get('debt_to_equity') is not None
        elif asset_class == "etf":
            return data.get('expense_ratio') is not None
        elif asset_class == "crypto":
            return data.get('market_cap') is not None
        return False
    
    def _is_international(self, ticker: str) -> bool:
        """Check if ticker is international (non-US exchange)."""
        # International tickers often have exchange suffix
        return '.' in ticker or '-' in ticker
    
    def _create_fundamental_data(
        self,
        ticker: str,
        asset_class: str,
        data: dict,
        source: str,
        sources_tried: list[str],
        confidence: float = 1.0
    ) -> FundamentalData:
        """Create FundamentalData with source attribution."""
        timestamp = datetime.now(UTC)
        
        return FundamentalData(
            ticker=ticker,
            asset_class=asset_class,
            roe=data.get('roe'),
            roe_source=DataSourceAttribution(
                source=source, timestamp=timestamp, confidence=confidence
            ) if data.get('roe') is not None else None,
            debt_to_equity=data.get('debt_to_equity'),
            debt_to_equity_source=DataSourceAttribution(
                source=source, timestamp=timestamp, confidence=confidence
            ) if data.get('debt_to_equity') is not None else None,
            revenue_growth=data.get('revenue_growth'),
            revenue_growth_source=DataSourceAttribution(
                source=source, timestamp=timestamp, confidence=confidence
            ) if data.get('revenue_growth') is not None else None,
            profit_margin=data.get('profit_margin'),
            profit_margin_source=DataSourceAttribution(
                source=source, timestamp=timestamp, confidence=confidence
            ) if data.get('profit_margin') is not None else None,
            has_critical_fields=self._has_critical_fields(data, asset_class),
            missing_fields=[
                field for field in ['roe', 'debt_to_equity', 'revenue_growth', 'profit_margin']
                if data.get(field) is None
            ]
        )
```

---

**Version**: 1.0  
**Created**: 2025-11-22  
**Status**: Complete - Ready for Review

