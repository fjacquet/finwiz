# Deep Portfolio Analysis Design Document

## Overview

This design document outlines the architecture for enhancing FinWiz's portfolio analysis system to provide deep, comprehensive analysis of portfolio holdings through **CrewAI Flow integration**. The current system performs only shallow ticker validation, resulting in uniform grades (D) and scores (0.6) for all holdings with no alternative recommendations. This enhancement integrates full crew-based analysis (stock/ETF/crypto) with A+ discovery data through Flow methods to provide accurate grading, detailed metrics, and actionable alternative recommendations.

### Design Goals

1. **Flow Integration**: Implement deep analysis as Flow methods using `@listen()` decorators
2. **Accuracy**: Replace shallow validation with full crew analysis for precise grading
3. **Actionability**: Link A+ alternatives to underperforming holdings (C or below)
4. **Performance**: Balance analysis depth with API costs through caching and feature flags
5. **Transparency**: Clearly indicate analysis depth and data sources in reports
6. **Reliability**: Graceful degradation when crew analysis fails

### Key Design Decisions

#### Decision 1: CrewAI Flow Architecture Integration

- **Rationale**: Respects existing Flow paradigm and event-driven architecture
- **Implementation**: Add `@listen()` methods to `FinwizFlow` instead of separate orchestrator classes
- **Trade-off**: Requires Flow state management but maintains architectural consistency

#### Decision 2: Optional Deep Analysis via Feature Flag

- **Rationale**: Balances comprehensive analysis with API costs and execution time
- **Implementation**: `DEEP_PORTFOLIO_ANALYSIS` environment variable controls Flow method execution
- **Trade-off**: Users can choose between fast validation and thorough analysis

#### Decision 3: Structured Flow State for Data Passing

- **Rationale**: Uses Flow's built-in structured state management with Pydantic models instead of unstructured dictionaries
- **Implementation**: Store analysis results in `self.state` (structured) for downstream Flow methods, completely replacing `self.inputs` (unstructured)
- **Trade-off**: Requires complete migration effort but provides type safety, validation, and maintainability
- **Breaking Change**: This is a complete migration with NO backward compatibility for `self.inputs`

#### Decision 4: Existing AlternativeFinder Tool Integration

- **Rationale**: Reuses existing tool within Flow methods rather than creating new services
- **Implementation**: Call AlternativeFinder from Flow method, store results in Flow state
- **Trade-off**: Maintains existing tool architecture while integrating with Flow

#### Decision 5: 24-Hour Cache TTL

- **Rationale**: Balances data freshness with cost reduction for daily portfolio reviews
- **Implementation**: Cache crew analysis results with configurable TTL
- **Trade-off**: May use slightly stale data but reduces API calls by ~70%

#### Decision 6: Complete Migration to Structured Flow State

- **Rationale**: Eliminates technical debt from unstructured `self.inputs` dictionary usage, provides type safety, and follows CrewAI Flow best practices
- **Implementation**: Replace ALL `self.inputs` usage with structured `self.state` using comprehensive `FinwizState` Pydantic model
- **Trade-off**: Requires one-time migration effort but provides long-term maintainability, type safety, and IDE support
- **Scope**: This is a complete migration with NO backward compatibility layer - all `self.inputs` references must be removed

## Architecture

### CrewAI Flow Integration

The deep portfolio analysis is implemented as Flow methods that integrate into the existing `FinwizFlow` execution sequence, following proper CrewAI Flow patterns:

```
@start() validate_data_integration
    ↓
@listen() check_stock, check_etf, check_crypto (parallel)
    ↓
@listen(and_()) check_portfolio (existing - runs portfolio review)
    ↓
@listen() analyze_holdings_deep (NEW - deep crew analysis) → returns analysis_results
    ↓
@listen() match_alternatives (analysis_results) (NEW - A+ alternative matching) → returns alternatives_data
    ↓
@listen() check_investment_discovery (existing)
    ↓
@listen() pre_validate_reporter_input (existing)
    ↓
@listen() report (existing - consumes deep analysis from Flow state)
```

**Key Compliance Updates:**
- Flow methods return values that are passed to listeners (proper CrewAI Flow pattern)
- Use structured `self.state` instead of unstructured `self.inputs` dict
- Follow exact CrewAI Flow documentation patterns for method signatures and data passing

### Flow Method Architecture (CrewAI Flow Compliant)

```
┌─────────────────────────────────────────────────────────────────┐
│                    FinwizFlow[FinwizState]                       │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              @listen("check_portfolio")                     │ │
│  │              analyze_holdings_deep(self) -> dict            │ │
│  │  ┌─────────────────────────────────────────────────────────┐ │ │
│  │  │  1. Check DEEP_PORTFOLIO_ANALYSIS flag                 │ │ │
│  │  │  2. If false, return {} (empty dict)                   │ │ │
│  │  │  3. Load holdings from self.state.portfolio_review     │ │ │
│  │  │  4. For each holding:                                  │ │ │
│  │  │     - Check AnalysisCacheManager                       │ │ │
│  │  │     - If cache miss, instantiate crew directly         │ │ │
│  │  │     - Execute crew.kickoff(inputs={...})               │ │ │
│  │  │     - Extract scores, calculate grade                  │ │ │
│  │  │     - Update self.state with results                   │ │ │
│  │  │  5. Return analysis_results dict                       │ │ │
│  │  └─────────────────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│                              ▼ (analysis_results passed)         │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │           @listen("analyze_holdings_deep")                  │ │
│  │           match_alternatives(self, analysis_results) -> dict│ │
│  │  ┌─────────────────────────────────────────────────────────┐ │ │
│  │  │  1. Check PORTFOLIO_ENABLE_ALTERNATIVES flag           │ │ │
│  │  │  2. If false, return {} (empty dict)                   │ │ │
│  │  │  3. Process analysis_results parameter                  │ │ │
│  │  │  4. For holdings with grade C or below:                │ │ │
│  │  │     - Call AlternativeFinder.find_alternatives()       │ │ │
│  │  │     - Update self.state with alternatives              │ │ │
│  │  │  5. Return alternatives_data dict                      │ │ │
│  │  └─────────────────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ (alternatives_data passed)
┌─────────────────────────────────────────────────────────────────┐
│              Portfolio Review Integration                        │
│  - check_portfolio() method updated to consume self.state       │
│  - Merges deep analysis data from Flow state into decisions     │
│  - Maintains backward compatibility with shallow validation      │
└─────────────────────────────────────────────────────────────────┘
│     * Crew analysis data  │
│     * Accurate grade      │
│     * Composite score     │
│     * A+ alternatives     │
└───────────────────────────┘
                │
                ▼
┌───────────────────────────┐
│   Enhanced Report         │
│   - Deep vs shallow stats │
│   - Grade distribution    │
│   - Alternative display   │
│   - Improvement summary   │
└───────────────────────────┘
```

### Data Flow

1. **Input**: Portfolio holdings (ticker, quantity, asset_class)
2. **Feature Check**: Evaluate `DEEP_PORTFOLIO_ANALYSIS` flag
3. **Cache Check**: Look for fresh cached analysis (< 24h)
4. **Crew Routing**: Direct to appropriate crew based on asset_class
5. **Analysis Extraction**: Parse crew output for scores and metrics
6. **Grade Calculation**: Apply grading system to composite score
7. **Alternative Matching**: Find A+ candidates for C/D/F holdings
8. **Decision Assembly**: Create HoldingDecision with all data
9. **Report Generation**: Display enhanced portfolio review

## Components and Interfaces

### 1. FinwizFlow Deep Analysis Methods (CrewAI Flow Compliant)

**Purpose**: Integrate deep portfolio analysis into the existing CrewAI Flow following proper Flow patterns

**Flow Methods**:

```python
class FinwizFlow(Flow[FinwizState]):
    
    @listen("check_portfolio")
    def analyze_holdings_deep(self) -> dict[str, Any]:
        """
        Perform deep crew analysis on portfolio holdings.
        
        CrewAI Flow Integration:
        - Triggered after portfolio review completes
        - Checks DEEP_PORTFOLIO_ANALYSIS environment variable
        - Uses direct crew instantiation and crew.kickoff()
        - Updates structured Flow state (self.state)
        - Returns analysis results for downstream listeners
        
        Returns:
            dict: Analysis results passed to downstream @listen() methods
        """
        
    @listen("analyze_holdings_deep")
    def match_alternatives(self, analysis_results: dict[str, Any]) -> dict[str, Any]:
        """
        Match A+ alternatives for underperforming holdings.
        
        CrewAI Flow Integration:
        - Receives analysis_results from upstream Flow method as parameter
        - Uses existing AlternativeFinder tool
        - Updates structured Flow state (self.state)
        - Returns alternatives data for downstream listeners
        
        Args:
            analysis_results: Deep analysis results from analyze_holdings_deep()
            
        Returns:
            dict: Alternatives data passed to downstream @listen() methods
        """
```

**Responsibilities**:

- Check feature flags and environment variables
- Load holdings from structured Flow state (self.state)
- Check AnalysisCacheManager for cached results
- Instantiate and execute crews directly using crew.kickoff()
- Extract composite scores from crew output
- Calculate letter grades using existing grading system
- Update structured Flow state (self.state) with results
- Return data for downstream Flow method consumption
- Coordinate with AlternativeFinder for alternative matching
- Implement rate limiting and retry logic
- Track analysis statistics

**Design Rationale**: Follows exact CrewAI Flow documentation patterns for method signatures, data passing, and state management. Uses structured state instead of unstructured dictionaries, and leverages Flow's built-in data passing between listeners.

### 2. Enhanced AlternativeFinder (Existing Tool)

**Purpose**: Matches underperforming holdings with A+ alternatives (existing tool, used within Flow)

**Interface** (existing):

```python
class AlternativeFinder:
    def __init__(self, output_dir: Path = Path("output")):
        """Initialize with discovery data directory."""
        
    def find_alternatives(
        self,
        holding: HoldingProfile,
        max_alternatives: int = 3
    ) -> List[Alternative]:
        """
        Find A+ alternatives for underperforming holding.
        
        Args:
            holding: Current holding with grade and score
            max_alternatives: Maximum alternatives to return
            
        Returns:
            List of Alternative objects ranked by score
        """
```

**Flow Integration**:

- Called from `match_alternatives()` Flow method
- Uses A+ discovery data already available in Flow state
- Results stored back in Flow state for portfolio review consumption

**Responsibilities**:

- Load A+ discovery data from latest discovery crew output
- Filter candidates by asset class
- Rank alternatives by composite score
- Generate clear rationales in French
- Handle missing or stale discovery data

**Design Rationale**: Reuses existing tool architecture while integrating with Flow state management.

### 3. Flow State Structure (CrewAI Flow Compliant)

**Purpose**: Define structured Flow state for proper CrewAI Flow integration

**State Definition**:

```python
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime

class DeepAnalysisResult(BaseModel):
    ticker: str
    asset_class: str
    crew_name: str
    analyzed_at: datetime
    composite_score: float
    grade: str
    fundamental_score: Optional[float] = None
    technical_score: Optional[float] = None
    risk_score: Optional[float] = None
    cached: bool = False

class FinwizState(BaseModel):
    """
    Comprehensive structured state for FinwizFlow.
    
    This replaces ALL previous usage of self.inputs dictionary.
    NO backward compatibility with self.inputs - complete migration.
    """
    # Core analysis results (previously in self.inputs)
    stock_result: str = ""
    etf_result: str = ""
    crypto_result: str = ""
    
    # Portfolio review data (previously in self.inputs)
    portfolio_review: Optional[Dict[str, Any]] = None
    portfolio_review_json: str = ""
    
    # Discovery results (previously in self.inputs)
    investment_discovery_result: Optional[Dict[str, Any]] = None
    investment_discovery_structured: Optional[Dict[str, Any]] = None
    
    # Rebalancing data (previously in self.inputs)
    portfolio_rebalancing_result: Optional[Dict[str, Any]] = None
    portfolio_rebalancing_available: bool = False
    
    # Data availability tracking (previously in self.inputs)
    data_availability_report: Optional[Dict[str, Any]] = None
    stale_data_warnings: List[str] = []
    
    # Error tracking (previously in self.inputs)
    error_summaries: List[Dict[str, Any]] = []
    system_health: Optional[Dict[str, Any]] = None
    
    # Consolidated data (previously in self.inputs)
    consolidated_data: Optional[Dict[str, Any]] = None
    core_analysis_summary: Optional[Dict[str, Any]] = None
    
    # Session metadata (previously in self.inputs)
    current_date: str = ""
    timestamp: str = ""
    report_language: str = "fr"
    
    # Deep portfolio analysis fields (NEW)
    deep_analysis_results: Dict[str, DeepAnalysisResult] = {}
    deep_analysis_success: bool = False
    deep_analysis_count: int = 0
    deep_analysis_error: Optional[str] = None
    
    # Alternative matching fields (NEW)
    portfolio_alternatives: Dict[str, List[Dict[str, Any]]] = {}
    alternatives_success: bool = False
    alternatives_count: int = 0
    alternatives_error: Optional[str] = None

class FinwizFlow(Flow[FinwizState]):
    """Enhanced FinwizFlow with structured state for deep portfolio analysis."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Flow automatically manages self.state as FinwizState instance
```

**State Access Patterns**:

```python
# In Flow methods - update structured state
self.state.deep_analysis_results[ticker] = DeepAnalysisResult(
    ticker=ticker,
    asset_class=asset_class,
    crew_name="StockCrew",
    analyzed_at=datetime.now(),
    composite_score=0.85,
    grade="A"
)

# After Flow execution - access final state
flow = FinwizFlow()
result = flow.kickoff()
final_state = flow.state

# Access deep analysis results
for ticker, analysis in final_state.deep_analysis_results.items():
    print(f"{ticker}: {analysis.grade} ({analysis.composite_score})")
```

**Design Rationale**: Uses structured Pydantic models for type safety and validation, follows CrewAI Flow documentation patterns for state management, and provides clear interfaces for accessing Flow results after execution.

**Migration Strategy**:

This is a COMPLETE migration from `self.inputs` to `self.state`:

1. **No Backward Compatibility**: All `self.inputs` references must be removed
2. **One-Time Migration**: All Flow methods updated simultaneously
3. **Type Safety**: Pydantic validation prevents runtime errors
4. **IDE Support**: Full autocomplete and type checking
5. **Enforcement**: Any remaining `self.inputs` usage is considered a bug

**Migration Benefits**:

- **Type Safety**: Compile-time error detection instead of runtime failures
- **Documentation**: State structure is self-documenting through Pydantic models
- **Validation**: Automatic data validation on state updates
- **Maintainability**: Clear, structured data access patterns
- **Framework Compliance**: Follows CrewAI Flow best practices exactly

### 4. AnalysisCacheManager

**Purpose**: Manages caching of crew analysis results

**Interface**:

```python
class AnalysisCacheManager:
    def __init__(
        self,
        cache_dir: str = "cache/portfolio_analysis",
        ttl_hours: int = 24
    ):
        """Initialize cache with TTL configuration."""
        
    def get_cached_analysis(
        self,
        ticker: str,
        asset_class: str
    ) -> Optional[CachedAnalysis]:
        """
        Retrieve cached analysis if fresh.
        
        Returns:
            CachedAnalysis if exists and fresh, None otherwise
        """
        
    def cache_analysis(
        self,
        ticker: str,
        asset_class: str,
        analysis: CrewAnalysisResult
    ) -> None:
        """Store analysis result in cache."""
        
    def is_fresh(self, cached_at: datetime) -> bool:
        """Check if cached data is within TTL."""
        
    def clear_stale_cache(self) -> int:
        """Remove stale cache entries, return count removed."""
```

**Responsibilities**:

- Store crew analysis results with timestamps
- Check cache freshness based on TTL
- Retrieve cached data when available
- Clean up stale cache entries
- Log cache hit/miss statistics

**Design Rationale**: Reduces API costs by avoiding redundant crew analysis for unchanged holdings.

### 5. ConfigurationManager

**Purpose**: Manages feature flags and configuration

**Interface**:

```python
class PortfolioAnalysisConfig:
    deep_analysis_enabled: bool = False
    enable_alternatives: bool = True
    cache_enabled: bool = True
    cache_ttl_hours: int = 24
    max_alternatives: int = 5
    batch_size: int = 10
    rate_limit_rpm: int = 20
    
    @classmethod
    def from_env(cls) -> "PortfolioAnalysisConfig":
        """Load configuration from environment variables."""
        
    def validate(self) -> None:
        """Validate configuration values."""
```

**Responsibilities**:

- Load configuration from environment variables
- Provide sensible defaults
- Validate configuration values
- Log active configuration on startup

**Design Rationale**: Centralizes configuration management with type safety and validation.

## Data Models

### CrewAnalysisResult

```python
class CrewAnalysisResult(BaseModel):
    """Result from crew analysis."""
    ticker: str
    asset_class: str
    crew_name: str
    analyzed_at: datetime
    
    # Composite scores
    fundamental_score: Optional[float] = None
    technical_score: Optional[float] = None
    quality_score: Optional[float] = None
    risk_score: Optional[float] = None
    composite_score: float
    
    # Detailed metrics
    metrics: Dict[str, Any] = {}
    
    # Risk assessment
    risk_assessment: Optional[RiskAssessmentStandardized] = None
    
    # Raw crew output
    raw_output: Dict[str, Any] = {}
```

### HoldingProfile

```python
class HoldingProfile(BaseModel):
    """Profile of a holding for alternative matching."""
    ticker: str
    name: str
    asset_class: str
    grade: str
    composite_score: float
    quantity: Optional[float] = None
    current_value: Optional[float] = None
```

### AplusCandidate

```python
class AplusCandidate(BaseModel):
    """A+ candidate from discovery data."""
    ticker: str
    name: str
    asset_class: str
    grade: str = "A+"
    composite_score: float
    
    # Key metrics
    fundamental_score: Optional[float] = None
    technical_score: Optional[float] = None
    risk_score: Optional[float] = None
    
    # Discovery metadata
    discovered_at: datetime
    discovery_rationale: str
```

### CachedAnalysis

```python
class CachedAnalysis(BaseModel):
    """Cached crew analysis result."""
    ticker: str
    asset_class: str
    cached_at: datetime
    analysis: CrewAnalysisResult
    
    def is_fresh(self, ttl_hours: int) -> bool:
        """Check if cache is within TTL."""
        age = datetime.now() - self.cached_at
        return age.total_seconds() < (ttl_hours * 3600)
```

## Complete Flow State Migration

### Why Complete Migration?

**Problem with Current Approach**:

The current FinwizFlow uses unstructured `self.inputs` dictionary for state management:

```python
# ❌ Current approach - Error-prone
self.inputs["stock_result"] = result  # No type checking
data = self.inputs.get("portfolio_review", {})  # No IDE support
self.inputs["typo_field"] = value  # Typos not caught
```

**Issues**:

1. **No Type Safety**: Runtime errors from typos or wrong types
2. **No Validation**: Invalid data silently accepted
3. **No IDE Support**: No autocomplete or type hints
4. **No Documentation**: State structure unclear
5. **Framework Non-Compliance**: Doesn't follow CrewAI Flow best practices

**Solution - Structured State**:

```python
# ✅ New approach - Type-safe
self.state.stock_result = result  # Type checked
data = self.state.portfolio_review or {}  # IDE autocomplete
self.state.typo_field = value  # Caught by IDE/linter
```

**Benefits**:

1. **Type Safety**: Compile-time error detection
2. **Validation**: Pydantic validates all updates
3. **IDE Support**: Full autocomplete and navigation
4. **Self-Documenting**: State structure is explicit
5. **Framework Compliance**: Follows CrewAI Flow patterns exactly

### Migration Scope

**CRITICAL**: This feature includes a complete migration from unstructured `self.inputs` to structured `self.state` across the ENTIRE FinwizFlow orchestrator.

**What Changes**:

1. **ALL Flow Methods**: Every `@listen()` method updated to use `self.state`
2. **ALL State Access**: Every `self.inputs[key]` replaced with `self.state.field`
3. **ALL Method Signatures**: Flow methods return `dict[str, Any]` for downstream listeners
4. **ALL External Access**: Code accessing Flow results uses `flow.state` instead of `flow.inputs`

**What Gets Removed**:

- ALL references to `self.inputs` in Flow methods
- ALL dictionary-style state access patterns
- ALL unstructured state management

**Migration Pattern**:

```python
# ❌ BEFORE - Unstructured (TO BE REMOVED)
self.inputs["stock_result"] = result
data = self.inputs.get("portfolio_review", {})

# ✅ AFTER - Structured (REQUIRED)
self.state.stock_result = result
data = self.state.portfolio_review or {}
```

**Validation**:

After migration, the following should be TRUE:

- `grep -r "self.inputs" src/finwiz/flows/` returns NO results
- All Flow state fields have type annotations
- All Flow methods have return type `dict[str, Any]`
- IDE provides autocomplete for all state fields

### Migration Impact on Existing Code

**Flow Methods Requiring Updates**:

1. `validate_data_integration()` - Update to use `self.state`
2. `check_stock()` - Update to use `self.state` and return dict
3. `check_etf()` - Update to use `self.state` and return dict
4. `check_crypto()` - Update to use `self.state` and return dict
5. `check_portfolio()` - Update to use `self.state` and return dict
6. `check_investment_discovery()` - Update to use `self.state` and return dict
7. `pre_validate_reporter_input()` - Update to use `self.state` and return dict
8. `report()` - Update to use `self.state` and return dict

**External Code Requiring Updates**:

1. Portfolio review orchestrator - Access `flow.state` instead of `flow.inputs`
2. Report generation - Access `flow.state` instead of `flow.inputs`
3. Any code that reads Flow results after execution

## Integration Points

### 1. CrewAI Flow Integration

**Current Flow Execution (BEFORE Migration)**:

```python
# src/finwiz/flows/flow_orchestrator.py
# ❌ OLD PATTERN - Uses unstructured self.inputs (TO BE REMOVED)
@listen(and_("check_stock", "check_etf", "check_crypto"))
def check_portfolio(self) -> None:
    """Run portfolio review after core analysis completion."""
    out_path = run_portfolio_review()
    self.inputs["portfolio_review_json"] = str(out_path)  # Unstructured
    # Load content for downstream consumption
    with open(out_path, encoding="utf-8") as f:
        self.inputs["portfolio_review"] = json.load(f)  # Unstructured
```

**Migrated Flow Execution (AFTER Migration)**:

```python
# src/finwiz/flows/flow_orchestrator.py
# ✅ NEW PATTERN - Uses structured self.state
@listen(and_("check_stock", "check_etf", "check_crypto"))
def check_portfolio(self) -> dict[str, Any]:
    """Run portfolio review after core analysis completion."""
    out_path = run_portfolio_review()
    
    # Update structured state
    self.state.portfolio_review_json = str(out_path)
    
    # Load content for downstream consumption
    with open(out_path, encoding="utf-8") as f:
        self.state.portfolio_review = json.load(f)
    
    # Return data for downstream Flow methods
    return {
        "portfolio_review_path": str(out_path),
        "holdings_count": len(self.state.portfolio_review.get("holdings", []))
    }
```

**Enhanced Flow Execution** (CrewAI Flow Compliant):

```python
# src/finwiz/flows/flow_orchestrator.py
@listen("check_portfolio")
def analyze_holdings_deep(self) -> dict[str, Any]:
    """Perform deep crew analysis on portfolio holdings."""
    # Follow CrewAI Flow pattern - return data for downstream listeners
    enabled = (os.getenv("DEEP_PORTFOLIO_ANALYSIS") or "false").strip().lower() in {
        "1", "true", "yes", "on"
    }
    if not enabled:
        logger.info("Deep portfolio analysis disabled via DEEP_PORTFOLIO_ANALYSIS")
        return {}  # Return empty dict for downstream listeners

    try:
        # Load holdings from structured Flow state
        if not hasattr(self.state, 'portfolio_review') or not self.state.portfolio_review:
            logger.warning("No portfolio review data available in Flow state")
            return {}

        holdings = self.state.portfolio_review.get("holdings", [])
        if not holdings:
            logger.warning("No holdings found in portfolio review data")
            return {}

        logger.info(f"Starting deep analysis for {len(holdings)} holdings")

        # Initialize cache manager
        from finwiz.cache.analysis_cache_manager import AnalysisCacheManager
        cache_ttl_hours = int(os.getenv("PORTFOLIO_CACHE_TTL_HOURS", "24"))
        cache_manager = AnalysisCacheManager(ttl_hours=cache_ttl_hours)

        # Process each holding
        deep_analysis_results = {}
        processed_count = 0
        
        for holding in holdings:
            ticker = holding.get("ticker")
            asset_class = holding.get("asset_class")
            
            if not ticker or not asset_class:
                logger.warning(f"Skipping holding with missing ticker or asset_class: {holding}")
                continue

            try:
                # Check cache first
                cached_result = cache_manager.get_cached_analysis(ticker, asset_class)
                if cached_result and cached_result.is_fresh(cache_ttl_hours):
                    logger.info(f"Using cached analysis for {ticker} (age: {cached_result.age_hours}h)")
                    analysis_result = cached_result.analysis
                else:
                    # Direct crew instantiation and execution (CrewAI Flow pattern)
                    crew_inputs = {"ticker": ticker, "asset_class": asset_class}
                    
                    if asset_class == "stock":
                        from finwiz.crews.stock_crew.stock_crew import StockCrew
                        crew = StockCrew()
                        result = crew.crew().kickoff(inputs=crew_inputs)
                    elif asset_class == "etf":
                        from finwiz.crews.etf_crew.etf_crew import EtfCrew
                        crew = EtfCrew()
                        result = crew.crew().kickoff(inputs=crew_inputs)
                    elif asset_class == "crypto":
                        from finwiz.crews.crypto_crew.crypto_crew import CryptoCrew
                        crew = CryptoCrew()
                        result = crew.crew().kickoff(inputs=crew_inputs)
                    else:
                        logger.warning(f"Unknown asset class {asset_class} for {ticker}")
                        continue

                    # Extract scores and calculate grade (using existing grading system)
                    analysis_result = self._parse_crew_output_for_holding(result, ticker, asset_class)
                    
                    # Cache the result
                    cache_manager.cache_analysis(ticker, asset_class, analysis_result)

                deep_analysis_results[ticker] = analysis_result
                processed_count += 1
                logger.info(f"Deep analysis progress: {processed_count}/{len(holdings)} holdings")

            except Exception as e:
                logger.error(f"Deep analysis failed for {ticker}: {e}", exc_info=True)
                # Continue with next holding (graceful degradation)
                continue

        # Update structured Flow state
        self.state.deep_analysis_results = deep_analysis_results
        self.state.deep_analysis_success = True
        self.state.deep_analysis_count = processed_count
        
        logger.info(f"Deep analysis completed for {processed_count} holdings")
        
        # Return results for downstream Flow listeners
        return {
            "analysis_results": deep_analysis_results,
            "processed_count": processed_count,
            "success": True
        }

    except Exception as e:
        logger.error(f"Deep portfolio analysis failed: {e}", exc_info=True)
        # Update structured Flow state with error info
        self.state.deep_analysis_error = str(e)
        self.state.deep_analysis_success = False
        self.state.deep_analysis_results = {}
        
        logger.warning("Deep analysis failed - continuing with shallow validation")
        
        # Return error info for downstream listeners
        return {
            "analysis_results": {},
            "processed_count": 0,
            "success": False,
            "error": str(e)
        }

@listen("analyze_holdings_deep")
def match_alternatives(self, analysis_data: dict[str, Any]) -> dict[str, Any]:
    """Match A+ alternatives for underperforming holdings."""
    # Follow CrewAI Flow pattern - receive data from upstream method
    enabled = (os.getenv("PORTFOLIO_ENABLE_ALTERNATIVES") or "true").strip().lower() in {
        "1", "true", "yes", "on"
    }
    if not enabled:
        logger.info("Alternative matching disabled via PORTFOLIO_ENABLE_ALTERNATIVES")
        return {}  # Return empty dict for downstream listeners

    try:
        # Check if deep analysis was successful (from parameter)
        if not analysis_data.get("success", False):
            logger.info("Skipping alternative matching - deep analysis not successful")
            return {}

        # Get deep analysis results from parameter (CrewAI Flow pattern)
        deep_results = analysis_data.get("analysis_results", {})
        if not deep_results:
            logger.warning("No deep analysis results available for alternative matching")
            return {}

        # Use existing AlternativeFinder tool
        from finwiz.tools.alternative_finder_tool import AlternativeFinder, HoldingProfile
        alternative_finder = AlternativeFinder()

        # Process holdings with grade C or below
        alternatives_data = {}
        alternatives_count = 0
        
        for ticker, analysis in deep_results.items():
            if analysis.get("grade") in ["C", "D", "F"]:
                try:
                    holding_profile = HoldingProfile(
                        ticker=ticker,
                        name=analysis.get("name", ticker),
                        asset_class=analysis.get("asset_class"),
                        grade=analysis.get("grade"),
                        composite_score=analysis.get("composite_score", 0.0)
                    )
                    alternatives = alternative_finder.find_alternatives(holding_profile)
                    if alternatives:
                        alternatives_data[ticker] = [alt.model_dump() for alt in alternatives]
                        alternatives_count += len(alternatives)
                        logger.info(f"Found {len(alternatives)} alternatives for {ticker}")
                        
                except Exception as e:
                    logger.error(f"Alternative matching failed for {ticker}: {e}")
                    continue

        # Update structured Flow state
        self.state.portfolio_alternatives = alternatives_data
        self.state.alternatives_success = True
        self.state.alternatives_count = alternatives_count
        
        logger.info(f"Alternative matching completed: {alternatives_count} alternatives for {len(alternatives_data)} holdings")
        
        # Return results for downstream Flow listeners
        return {
            "alternatives_data": alternatives_data,
            "alternatives_count": alternatives_count,
            "success": True
        }

    except Exception as e:
        logger.error(f"Alternative matching failed: {e}", exc_info=True)
        # Update structured Flow state with error info
        self.state.alternatives_error = str(e)
        self.state.alternatives_success = False
        self.state.portfolio_alternatives = {}
        
        logger.warning("Alternative matching failed - continuing without alternatives")
        
        # Return error info for downstream listeners
        return {
            "alternatives_data": {},
            "alternatives_count": 0,
            "success": False,
            "error": str(e)
        }
```

### 2. Portfolio Review Integration (CrewAI Flow Compliant)

**Enhanced Portfolio Review**:

```python
# src/finwiz/orchestrators/portfolio_review.py
def build_portfolio_review(...) -> tuple[PortfolioReview, ProcessingSummary]:
    """Build portfolio review with optional deep analysis integration from Flow state."""
    
    # Run existing portfolio holdings processor
    decisions = processor.process_holdings(holdings, base_currency, keep_threshold)
    
    # Check if deep analysis data is available in Flow state
    # (Access via flow.state after Flow execution)
    flow_state = get_current_flow_state()  # Helper to access Flow state
    
    if (hasattr(flow_state, 'deep_analysis_results') and 
        hasattr(flow_state, 'portfolio_alternatives')):
        
        deep_analysis_results = flow_state.deep_analysis_results
        portfolio_alternatives = flow_state.portfolio_alternatives
        
        # Merge deep analysis data into HoldingDecision objects
        for decision in decisions:
            ticker = decision.ticker
            
            # Update with deep analysis results
            if ticker in deep_analysis_results:
                analysis = deep_analysis_results[ticker]
                decision.composite_score = analysis.get("composite_score", decision.composite_score)
                decision.grade = analysis.get("grade", decision.grade)
                decision.crew_analysis_used = analysis.get("crew_name")
                decision.analysis_date = analysis.get("analyzed_at")
                decision.data_freshness = "fresh"
                
                # Add detailed metrics to rationale
                if analysis.get("fundamental_score"):
                    decision.rationale_bullets.extend([
                        f"Fundamental Score: {analysis['fundamental_score']:.2f}",
                        f"Technical Score: {analysis['technical_score']:.2f}",
                        f"Risk Score: {analysis['risk_score']:.1f}/5.0"
                    ])
            
            # Add alternatives if available
            if ticker in portfolio_alternatives:
                decision.alternatives = portfolio_alternatives[ticker]
                decision.has_a_plus_opportunities = True
    
    return PortfolioReview(holdings=decisions, ...)

def get_current_flow_state():
    """Helper function to access current Flow state."""
    # Implementation would depend on how Flow state is made available
    # This could be passed as a parameter or accessed via a global context
    pass
```

### 3. A+ Discovery Data Integration

**Data Source**: `output/discovery/a_plus_*.json`

**Expected Format**:

```json
{
  "asset_class": "stock",
  "candidates": [
    {
      "ticker": "MSFT",
      "name": "Microsoft Corporation",
      "grade": "A+",
      "composite_score": 0.92,
      "fundamental_score": 0.95,
      "technical_score": 0.88,
      "risk_score": 2.1,
      "discovered_at": "2025-03-10T10:00:00Z",
      "discovery_rationale": "Strong fundamentals with consistent growth..."
    }
  ]
}
```

**Loading Strategy**:

- Load all `a_plus_*.json` files on initialization
- Group by asset_class
- Sort by composite_score descending
- Cache in memory for session duration

### 4. Report Generation Integration

**Current Report**: `src/finwiz/templates/portfolio_review_template.html`

**Enhancements**:

1. Add analysis depth indicator column (🔍 Deep / ⚡ Quick)
2. Add alternatives expandable section for C/D/F holdings
3. Add portfolio improvement summary section
4. Add grade distribution chart
5. Add data completeness indicators

## Error Handling

### Error Categories and Strategies

#### 1. Crew Analysis Failures

**Scenarios**:

- API rate limiting
- Network timeouts
- Invalid crew output
- Crew execution errors

**Strategy**:

```python
try:
    analysis = await crew_router.analyze(ticker, asset_class)
except CrewExecutionError as e:
    logger.warning(f"Crew analysis failed for {ticker}: {e}")
    # Fallback to ticker validation
    analysis = fallback_ticker_validation(ticker)
    analysis.warnings.append("Deep analysis unavailable, using validation")
except RateLimitError as e:
    logger.warning(f"Rate limit hit for {ticker}, retrying...")
    await asyncio.sleep(exponential_backoff(attempt))
    # Retry up to 3 times
```

**Graceful Degradation**:

- Fall back to ticker validation
- Mark HoldingDecision with warning flag
- Continue processing remaining holdings
- Include degradation statistics in report

#### 2. Cache Failures

**Scenarios**:

- Cache directory not writable
- Corrupted cache files
- Cache read/write errors

**Strategy**:

```python
try:
    cached = cache_manager.get_cached_analysis(ticker, asset_class)
except CacheError as e:
    logger.warning(f"Cache error for {ticker}: {e}")
    cached = None  # Proceed without cache
```

**Fallback**: Disable caching for session, proceed with fresh analysis

#### 3. Alternative Finder Failures

**Scenarios**:

- Missing discovery data files
- Stale discovery data (> 7 days)
- Invalid JSON format

**Strategy**:

```python
try:
    alternatives = alternative_finder.find_alternatives(holding)
except DiscoveryDataError as e:
    logger.warning(f"Discovery data unavailable: {e}")
    alternatives = []  # Continue without alternatives
```

**Fallback**: Return empty alternatives list, log warning in report

#### 4. Configuration Errors

**Scenarios**:

- Invalid environment variable values
- Conflicting configuration settings

**Strategy**:

```python
try:
    config = PortfolioAnalysisConfig.from_env()
    config.validate()
except ConfigurationError as e:
    logger.error(f"Invalid configuration: {e}")
    config = PortfolioAnalysisConfig()  # Use defaults
    logger.info("Using default configuration")
```

**Fallback**: Use safe defaults, log warnings

### Error Tracking

```python
class AnalysisStatistics:
    total_holdings: int = 0
    deep_analysis_success: int = 0
    deep_analysis_failed: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    alternatives_found: int = 0
    errors: List[str] = []
    
    def summary(self) -> str:
        """Generate human-readable summary."""
```

## Performance Optimization

### 1. Caching Strategy

**Cache Structure**:

```
cache/portfolio_analysis/
├── stock/
│   ├── AAPL_20250310.json
│   └── MSFT_20250310.json
├── etf/
│   └── SPY_20250310.json
└── crypto/
    └── BTC_20250310.json
```

**Cache Key**: `{asset_class}/{ticker}_{date}.json`

**TTL Management**:

- Default: 24 hours
- Configurable via `PORTFOLIO_CACHE_TTL_HOURS`
- Automatic cleanup of stale entries on startup

**Expected Impact**:

- 70%+ reduction in API calls for daily reviews
- 80%+ reduction in execution time for cached portfolios

### 2. Rate Limiting

**Implementation**:

```python
from finwiz.utils.rate_limiter import RateLimiter

rate_limiter = RateLimiter(max_calls=20, period=60)  # 20 calls/minute

@rate_limiter.limit
async def analyze_with_crew(ticker: str, asset_class: str):
    """Rate-limited crew analysis."""
```

**Strategy**:

- 20 requests per minute (configurable)
- Exponential backoff on rate limit errors
- Batch processing with progress tracking

### 3. Parallel Processing

**Batch Analysis**:

```python
async def analyze_portfolio(self, holdings: List[Holding]) -> PortfolioReview:
    batch_size = self.config.batch_size
    results = []
    
    for i in range(0, len(holdings), batch_size):
        batch = holdings[i:i + batch_size]
        batch_results = await asyncio.gather(
            *[self.analyze_holding(h) for h in batch],
            return_exceptions=True
        )
        results.extend(batch_results)
        
        # Progress logging
        logger.info(f"Analyzed {len(results)}/{len(holdings)} holdings")
    
    return PortfolioReview(holdings=results)
```

**Benefits**:

- Process multiple holdings concurrently
- Respect rate limits with batch sizing
- Provide progress feedback for large portfolios

### 4. Memory Management

**Strategies**:

- Stream large discovery data files
- Clear crew instances after use
- Limit in-memory cache size
- Use generators for batch processing

### Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Cache hit rate | 70%+ | For daily portfolio reviews |
| Analysis time (cached) | < 30s | For 50 holdings |
| Analysis time (uncached) | < 5 min | For 50 holdings |
| API calls (cached) | < 15 | For 50 holdings |
| API calls (uncached) | < 150 | For 50 holdings |
| Memory usage | < 500 MB | Peak during analysis |

## Testing Strategy

### Unit Tests

**Components to Test**:

1. **FinwizState (Structured State Model)**
   - Pydantic validation for all fields
   - Type safety enforcement
   - Default value handling
   - Optional field behavior
   - State serialization/deserialization

2. **Flow Methods (State Migration)**
   - All methods use `self.state` instead of `self.inputs`
   - All methods return `dict[str, Any]` for downstream listeners
   - Structured state updates work correctly
   - Type annotations are correct
   - No remaining `self.inputs` references

3. **AlternativeFinder**
   - Load A+ discovery data
   - Filter by asset class
   - Rank by composite score
   - Generate rationales
   - Handle missing data

4. **AnalysisCacheManager**
   - Cache storage and retrieval
   - TTL validation
   - Stale cache cleanup
   - Cache miss handling

5. **ConfigurationManager**
   - Load from environment
   - Validate values
   - Use defaults

**Testing Approach**:

```python
def test_should_use_structured_state_in_flow_methods(mocker):
    """Test that Flow methods use structured state correctly."""
    # Arrange
    flow = FinwizFlow()
    
    # Verify state is structured Pydantic model
    assert isinstance(flow.state, FinwizState)
    
    # Test state updates
    flow.state.stock_result = "test_result"
    assert flow.state.stock_result == "test_result"
    
    # Test type validation
    with pytest.raises(ValidationError):
        flow.state.deep_analysis_count = "not_an_int"  # Should fail

def test_should_return_dict_from_flow_methods(mocker):
    """Test that Flow methods return dicts for downstream listeners."""
    # Arrange
    flow = FinwizFlow()
    mocker.patch.object(flow, '_some_internal_method')
    
    # Act
    result = flow.analyze_holdings_deep()
    
    # Assert
    assert isinstance(result, dict)
    assert "analysis_results" in result or result == {}

def test_should_access_flow_state_after_execution(mocker):
    """Test accessing structured state after Flow execution."""
    # Arrange
    flow = FinwizFlow()
    mocker.patch.object(flow, 'kickoff', return_value="success")
    
    # Simulate state updates
    flow.state.deep_analysis_success = True
    flow.state.deep_analysis_count = 5
    
    # Act - Access final state
    final_state = flow.state
    
    # Assert
    assert final_state.deep_analysis_success is True
    assert final_state.deep_analysis_count == 5
    assert isinstance(final_state, FinwizState)

def test_should_find_alternatives_when_holding_graded_c(mocker):
    # Arrange
    mock_discovery = mocker.patch.object(
        AlternativeFinder, '_load_discovery_data'
    )
    mock_discovery.return_value = {
        'stock': [
            AplusCandidate(ticker='MSFT', grade='A+', composite_score=0.92)
        ]
    }
    
    finder = AlternativeFinder()
    holding = HoldingProfile(
        ticker='IBM',
        asset_class='stock',
        grade='C',
        composite_score=0.65
    )
    
    # Act
    alternatives = finder.find_alternatives(holding)
    
    # Assert
    assert len(alternatives) > 0
    assert alternatives[0].ticker == 'MSFT'
    assert alternatives[0].grade == 'A+'
```

### Integration Tests

**Scenarios**:

1. **Flow State Migration Validation**
   - Execute complete Flow with structured state
   - Verify NO `self.inputs` usage anywhere
   - Verify all Flow methods return dicts
   - Verify structured state accessible after execution
   - Verify type safety throughout Flow execution
   - Verify backward compatibility is NOT maintained (intentional)

2. **End-to-End Deep Analysis with Structured State**
   - Load portfolio with mixed asset classes
   - Run deep analysis with real crews
   - Verify grades and alternatives stored in `self.state`
   - Access final results via `flow.state` (not `flow.inputs`)
   - Check report generation uses `flow.state`

3. **Cache Integration**
   - Analyze portfolio twice
   - Verify cache hits on second run
   - Validate cache freshness

4. **Graceful Degradation**
   - Simulate crew failures
   - Verify fallback to validation
   - Check error reporting in structured state

5. **Alternative Matching**
   - Load real A+ discovery data
   - Match with underperforming holdings
   - Verify rationale quality

**Test Markers**:

```python
@pytest.mark.integration
@pytest.mark.slow
async def test_should_complete_deep_analysis_for_portfolio():
    """Integration test requiring API keys."""
```

### Performance Tests

**Benchmarks**:

1. **Cache Performance**
   - Measure cache hit rate
   - Verify TTL behavior
   - Test cleanup efficiency

2. **Analysis Speed**
   - 10 holdings (cached): < 10s
   - 10 holdings (uncached): < 1 min
   - 50 holdings (cached): < 30s
   - 50 holdings (uncached): < 5 min

3. **Memory Usage**
   - Monitor peak memory
   - Verify cleanup after analysis
   - Test with large portfolios (100+ holdings)

## Flow State Migration Validation Checklist

Before considering the migration complete, verify:

### Code Validation

- [ ] **No self.inputs References**: `grep -r "self.inputs" src/finwiz/flows/` returns ZERO results
- [ ] **Structured State Usage**: All Flow methods use `self.state.field_name` pattern
- [ ] **Return Types**: All Flow methods have return type `-> dict[str, Any]`
- [ ] **Parameter Reception**: Listener methods receive upstream data as parameters
- [ ] **Type Annotations**: All FinwizState fields have proper type hints
- [ ] **Pydantic Validation**: FinwizState model validates all field types

### Functional Validation

- [ ] **Flow Execution**: Complete Flow runs without errors
- [ ] **State Access**: `flow.state` accessible after `flow.kickoff()`
- [ ] **Data Integrity**: All expected data present in structured state
- [ ] **Type Safety**: IDE provides autocomplete for state fields
- [ ] **Validation Works**: Invalid data types rejected by Pydantic

### Integration Validation

- [ ] **Portfolio Review**: Accesses `flow.state` instead of `flow.inputs`
- [ ] **Report Generation**: Uses `flow.state` for all data access
- [ ] **Deep Analysis**: Stores results in `self.state.deep_analysis_results`
- [ ] **Alternatives**: Stores data in `self.state.portfolio_alternatives`
- [ ] **Error Handling**: Errors tracked in structured state fields

### Testing Validation

- [ ] **Unit Tests Pass**: All Flow method tests use structured state
- [ ] **Integration Tests Pass**: End-to-end tests use `flow.state`
- [ ] **Type Tests**: Pydantic validation tests pass
- [ ] **No Backward Compat**: No tests rely on `self.inputs`

### Documentation Validation

- [ ] **Design Doc Updated**: Reflects structured state usage
- [ ] **Code Comments**: Reference `self.state` not `self.inputs`
- [ ] **Examples Updated**: All code examples use structured state
- [ ] **Migration Notes**: Document breaking changes clearly
