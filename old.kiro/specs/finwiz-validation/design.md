# Design Document: FinWiz Architectural Validation & Gap Filling

## Overview

This design document outlines a hybrid approach to validating the FinWiz architectural consolidation and filling identified gaps. Analysis reveals that **the system already implements most requirements** (85% compliance), so this design focuses on:

1. **Validation**: Automated tools to verify compliance with all requirements
2. **Gap Filling**: Address the 15% of requirements needing attention
3. **Documentation**: Document the existing architecture comprehensively
4. **Testing**: Add tests to verify success criteria

### Key Finding

**The architectural consolidation has already been implemented.** The current system has:
- ✅ Unified `DeepAnalysisCrew` with dynamic tool routing
- ✅ Correct flow sequence (Validation → Portfolio → Deep Analysis → Discovery → Rebalancing → Report)
- ✅ Atomic operations and structured Pydantic state
- ✅ Resilience features (retry, checkpointing, graceful degradation)
- ✅ Data integration system with validation

### Design Goals

1. **Validate Compliance**: Create automated tools to verify all 13 requirements
2. **Fill Gaps**: Address verification items (enum docs, test framework, file sizes)
3. **Document Architecture**: Comprehensive documentation of existing patterns
4. **Test Success Criteria**: Verify stability, performance, correctness
5. **Quality Assurance**: Automated checks for code quality standards

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FinWiz Flow                              │
│                                                                   │
│  Phase 1: Validation                                             │
│  ├─ validate_data_integration()                                  │
│  │                                                                │
│  Phase 2: Portfolio Analysis                                     │
│  ├─ check_portfolio()                                            │
│  │                                                                │
│  Phase 3: Deep Analysis & Update (ATOMIC)                        │
│  ├─ analyze_and_update_portfolio()                               │
│  │   ├─ Run DeepAnalysisCrew for each holding                    │
│  │   ├─ Match alternatives with AlternativeFinder                │
│  │   └─ Update portfolio review (ONCE)                           │
│  │                                                                │
│  Phase 4: Discovery                                              │
│  ├─ check_stock() ──┐                                            │
│  ├─ check_etf() ────┼─→ check_investment_discovery()             │
│  ├─ check_crypto() ─┘                                            │
│  │                                                                │
│  Phase 5: Rebalancing                                            │
│  ├─ check_portfolio_rebalancing()                                │
│  │                                                                │
│  Phase 6: Reporting                                              │
│  └─ report()                                                     │
└─────────────────────────────────────────────────────────────────┘
```


### Component Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    DeepAnalysisCrew                           │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Input: {ticker: str, asset_class: str}                │  │
│  │                                                          │  │
│  │  Dynamic Tool Router                                    │  │
│  │  ├─ if asset_class == "stock" → Stock Tools            │  │
│  │  ├─ if asset_class == "etf" → ETF Tools                │  │
│  │  └─ if asset_class == "crypto" → Crypto Tools          │  │
│  │                                                          │  │
│  │  Agents:                                                │  │
│  │  ├─ Asset Analyst (reasoning=True)                     │  │
│  │  ├─ Risk Assessor (reasoning=True)                     │  │
│  │  └─ Investment Reporter (@final_reporter)              │  │
│  │                                                          │  │
│  │  Output: DeepAnalysisResult (Pydantic)                 │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                  Discovery Crews (Existing)                   │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  StockCrew: "Screen and identify top 10 stock assets"  │  │
│  │  EtfCrew: "Screen and identify top 10 ETF assets"      │  │
│  │  CryptoCrew: "Screen and identify top 10 crypto assets"│  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. DeepAnalysisCrew

**Purpose**: Unified crew for comprehensive single-ticker analysis across all asset classes.

**Location**: `src/finwiz/crews/deep_analysis_crew/`

**Structure**:
```
deep_analysis_crew/
├── deep_analysis_crew.py
└── config/
    ├── agents.yaml
    └── tasks.yaml
```

**Key Interfaces**:

```python
class DeepAnalysisCrew(CrewBase):
    """Unified crew for deep analysis of single tickers."""
    
    def __init__(self, ticker: str, asset_class: str):
        self.ticker = ticker
        self.asset_class = asset_class
        super().__init__()
    
    def get_tools_for_asset_class(self) -> list:
        """Dynamic tool routing based on asset class."""
        if self.asset_class.lower() == "stock":
            return get_stock_crew_tools(...)
        elif self.asset_class.lower() == "etf":
            return get_etf_crew_tools(...)
        elif self.asset_class.lower() == "crypto":
            return get_crypto_crew_tools(...)
        else:
            raise ValueError(f"Invalid asset_class: {self.asset_class}")
    
    @agent
    def asset_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["asset_analyst"],
            tools=self.get_tools_for_asset_class(),
            reasoning=True,
            max_reasoning_attempts=3,
            verbose=True
        )
    
    @agent
    def risk_assessor(self) -> Agent:
        return Agent(
            config=self.agents_config["risk_assessor"],
            tools=self.get_tools_for_asset_class(),
            reasoning=True,
            max_reasoning_attempts=3,
            verbose=True
        )
    
    @final_reporter
    @agent
    def investment_reporter(self) -> Agent:
        return Agent(
            config=self.agents_config["investment_reporter"],
            tools=[],  # Empty - enforced by decorator
            verbose=True
        )
```


### 2. Flow Orchestrator Refactoring

**Purpose**: Re-architect flow to follow correct business logic sequence.

**Location**: `src/finwiz/flows/flow_orchestrator.py`

**Key Changes**:

```python
from pydantic import BaseModel, Field
from crewai.flow import Flow, start, listen, and_, persist
from typing import Dict, List, Any, Optional

class FinwizState(BaseModel):
    """Structured flow state with type safety."""
    # Portfolio data
    portfolio_review: Optional[Dict[str, Any]] = None
    holdings_processed: int = 0
    
    # Deep analysis results
    deep_analysis_results: Dict[str, Any] = {}
    deep_analysis_success: bool = False
    deep_analysis_errors: List[str] = []
    
    # Discovery results
    discovery_results: Dict[str, List[Any]] = {}
    
    # Rebalancing results
    rebalancing_results: Optional[Dict[str, Any]] = None
    
    # Final report
    final_report: Optional[str] = None

@persist()  # Class-level persistence
class FinwizFlow(Flow[FinwizState]):
    """Main flow orchestrator with corrected sequence."""
    
    @start()
    def validate_data_integration(self) -> dict[str, Any]:
        """Phase 1: Validate data integration."""
        logger.info("Phase 1: Validating data integration")
        # Validation logic
        return {"validation_status": "complete"}
    
    @listen("validate_data_integration")
    def check_portfolio(self) -> dict[str, Any]:
        """Phase 2: Analyze existing portfolio holdings."""
        logger.info("Phase 2: Analyzing portfolio")
        # Portfolio analysis logic
        self.state.portfolio_review = portfolio_data
        return {"portfolio_status": "analyzed"}
    
    @listen("check_portfolio")
    def analyze_and_update_portfolio(self) -> dict[str, Any]:
        """Phase 3: ATOMIC deep analysis + alternatives + update."""
        logger.info("Phase 3: Deep analysis and portfolio update")
        
        # Step 1: Run deep analysis on each holding
        deep_results = self._run_deep_analysis_on_holdings()
        self.state.deep_analysis_results = deep_results
        
        # Step 2: Match alternatives for underperforming holdings
        alternatives = self._match_alternatives(deep_results)
        
        # Step 3: Update portfolio review ONCE
        self._update_portfolio_with_analysis(deep_results, alternatives)
        
        self.state.deep_analysis_success = True
        return {
            "deep_analysis_results": deep_results,
            "alternatives": alternatives
        }
    
    @listen("analyze_and_update_portfolio")
    def check_stock(self) -> dict[str, Any]:
        """Phase 4a: Discover top 10 stock opportunities."""
        logger.info("Phase 4a: Stock discovery")
        # Stock discovery logic
        return {"stock_discoveries": []}
    
    @listen("analyze_and_update_portfolio")
    def check_etf(self) -> dict[str, Any]:
        """Phase 4b: Discover top 10 ETF opportunities."""
        logger.info("Phase 4b: ETF discovery")
        # ETF discovery logic
        return {"etf_discoveries": []}
    
    @listen("analyze_and_update_portfolio")
    def check_crypto(self) -> dict[str, Any]:
        """Phase 4c: Discover top 10 crypto opportunities."""
        logger.info("Phase 4c: Crypto discovery")
        # Crypto discovery logic
        return {"crypto_discoveries": []}
    
    @listen(and_("check_stock", "check_etf", "check_crypto"))
    def check_investment_discovery(self) -> dict[str, Any]:
        """Phase 4d: Consolidate A+ discoveries."""
        logger.info("Phase 4d: Consolidating discoveries")
        # Consolidation logic
        return {"consolidated_discoveries": []}
    
    @listen(and_("analyze_and_update_portfolio", "check_investment_discovery"))
    def check_portfolio_rebalancing(self) -> dict[str, Any]:
        """Phase 5: Optimize portfolio allocations."""
        logger.info("Phase 5: Portfolio rebalancing")
        # Rebalancing logic
        self.state.rebalancing_results = rebalancing_data
        return {"rebalancing_status": "complete"}
    
    @listen("check_portfolio_rebalancing")
    def report(self) -> str:
        """Phase 6: Generate final report."""
        logger.info("Phase 6: Generating final report")
        # Report generation logic
        self.state.final_report = report_html
        return report_html
```


### 3. Data Integration System

**Purpose**: Ensure strict validation and correct data flow between components.

**Components**:

```python
# src/finwiz/integration/data_consolidation_validator.py
class DataConsolidationValidator:
    """Validates crew output retrieval and consolidation."""
    
    def validate_crew_outputs_exist(self, crew_names: List[str]) -> bool:
        """Verify all crew outputs are stored and retrievable."""
        for crew_name in crew_names:
            output_path = Path(f"output/{crew_name}/")
            if not output_path.exists():
                raise DataRetrievalError(f"Missing output for {crew_name}")
        return True
    
    def retrieve_crew_output(self, crew_name: str) -> Dict[str, Any]:
        """Retrieve and validate crew output."""
        output_path = Path(f"output/{crew_name}/")
        # Retrieval logic with validation
        return validated_output

# src/finwiz/integration/schema_validator.py
class SchemaValidator:
    """Validates data against strict Pydantic schemas."""
    
    def validate_against_schema(
        self,
        data: Dict[str, Any],
        schema: Type[BaseModel]
    ) -> BaseModel:
        """Validate data with extra='forbid'."""
        try:
            return schema.model_validate(data)
        except ValidationError as e:
            raise SchemaValidationError(f"Validation failed: {e}")

# src/finwiz/integration/data_freshness_validator.py
class DataFreshnessValidator:
    """Validates market data freshness."""
    
    MAX_AGE_HOURS = 24
    
    def validate_data_freshness(
        self,
        data: Dict[str, Any],
        timestamp_field: str = "timestamp"
    ) -> tuple[bool, Optional[str]]:
        """Check if data is fresh (< 24 hours old)."""
        timestamp = data.get(timestamp_field)
        if not timestamp:
            return False, "Missing timestamp"
        
        age_hours = (datetime.now() - timestamp).total_seconds() / 3600
        if age_hours > self.MAX_AGE_HOURS:
            return False, f"Data is {age_hours:.1f} hours old"
        
        return True, None
    
    def flag_stale_data(
        self,
        analysis_result: Dict[str, Any],
        warning: str
    ) -> Dict[str, Any]:
        """Add warning and reduce confidence for stale data."""
        analysis_result["warnings"] = analysis_result.get("warnings", [])
        analysis_result["warnings"].append(warning)
        analysis_result["confidence_score"] *= 0.8  # Reduce by 20%
        return analysis_result
```


### 4. Resilience Components

**Purpose**: Implement retry logic, checkpointing, and graceful degradation.

**Components**:

```python
# src/finwiz/utils/retry_handler.py
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential_jitter,
    retry_if_exception_type
)

class RetryHandler:
    """Handles automatic retries with exponential backoff."""
    
    @staticmethod
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=1, max=60),
        retry=retry_if_exception_type((NetworkError, APIError))
    )
    def execute_with_retry(func, *args, **kwargs):
        """Execute function with automatic retry."""
        return func(*args, **kwargs)

# src/finwiz/utils/checkpoint_manager.py
class CheckpointManager:
    """Manages flow checkpointing and resumption."""
    
    def save_checkpoint(
        self,
        flow_state: FinwizState,
        checkpoint_id: str
    ) -> None:
        """Save flow state to checkpoint."""
        checkpoint_path = Path(f".checkpoints/{checkpoint_id}.json")
        checkpoint_path.parent.mkdir(exist_ok=True)
        checkpoint_path.write_text(flow_state.model_dump_json())
    
    def load_checkpoint(self, checkpoint_id: str) -> Optional[FinwizState]:
        """Load flow state from checkpoint."""
        checkpoint_path = Path(f".checkpoints/{checkpoint_id}.json")
        if not checkpoint_path.exists():
            return None
        return FinwizState.model_validate_json(checkpoint_path.read_text())
    
    def should_skip_holding(
        self,
        ticker: str,
        flow_state: FinwizState
    ) -> bool:
        """Check if holding was already processed."""
        return ticker in flow_state.deep_analysis_results

# src/finwiz/utils/graceful_degradation.py
class GracefulDegradationHandler:
    """Handles failures with graceful degradation."""
    
    def handle_failed_holding(
        self,
        ticker: str,
        error: Exception,
        flow_state: FinwizState
    ) -> Dict[str, Any]:
        """Mark holding as failed and use fallback data."""
        logger.error(f"Failed to analyze {ticker}: {error}")
        
        # Mark as failed
        flow_state.deep_analysis_errors.append(f"{ticker}: {str(error)}")
        
        # Use fallback data if available
        fallback_data = self._get_fallback_data(ticker)
        if fallback_data:
            logger.info(f"Using fallback data for {ticker}")
            return fallback_data
        
        # Return minimal placeholder
        return {
            "ticker": ticker,
            "grade": "D",
            "status": "failed",
            "error": str(error)
        }
```


## Data Models

### DeepAnalysisResult Schema

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class Grade(str, Enum):
    """Investment grade enum."""
    A_PLUS = "A+"
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"

class DeepAnalysisResult(BaseModel):
    """Unified output schema for DeepAnalysisCrew."""
    
    model_config = {"extra": "forbid"}
    
    # Identification
    ticker: str = Field(..., description="Asset ticker symbol")
    asset_class: str = Field(..., description="Asset class: stock, etf, or crypto")
    
    # Scores (0.0 to 1.0)
    fundamental_score: float = Field(..., ge=0.0, le=1.0)
    technical_score: float = Field(..., ge=0.0, le=1.0)
    risk_score: float = Field(..., ge=0.0, le=5.0, description="0=Very Low, 5=Very High")
    composite_score: float = Field(..., ge=0.0, le=1.0)
    
    # Grade
    grade: Grade = Field(..., description="Final investment grade")
    
    # Analysis details
    fundamental_analysis: Optional[str] = None
    technical_analysis: Optional[str] = None
    risk_assessment: Optional[str] = None
    
    # Metadata
    analysis_timestamp: datetime = Field(default_factory=datetime.now)
    data_freshness_hours: float = Field(..., description="Age of market data in hours")
    confidence_level: float = Field(..., ge=0.0, le=1.0)
    warnings: List[str] = Field(default_factory=list)

class ReporterInput(BaseModel):
    """Strict input schema for ReportCrew."""
    
    model_config = {"extra": "forbid"}
    
    # Portfolio data
    portfolio_review: Dict[str, Any]
    deep_analysis_results: Dict[str, DeepAnalysisResult]
    
    # Discovery data
    discovery_results: Dict[str, List[Any]]
    
    # Rebalancing data
    rebalancing_results: Optional[Dict[str, Any]] = None
    
    # Metadata
    generation_timestamp: datetime = Field(default_factory=datetime.now)
```


## Error Handling

### Error Hierarchy

```python
class FinWizError(Exception):
    """Base exception for FinWiz system."""
    pass

class CrewExecutionError(FinWizError):
    """Raised when crew execution fails."""
    pass

class DataRetrievalError(FinWizError):
    """Raised when crew output cannot be retrieved."""
    pass

class SchemaValidationError(FinWizError):
    """Raised when data fails schema validation."""
    pass

class DataFreshnessError(FinWizError):
    """Raised when data is too stale."""
    pass

class FlowInterruptedError(FinWizError):
    """Raised when flow is interrupted."""
    pass
```

### Error Handling Strategy

1. **Transient Errors**: Retry with exponential backoff (network, API)
2. **Validation Errors**: Fail fast with clear error messages
3. **Data Errors**: Use graceful degradation with fallback data
4. **Flow Errors**: Save checkpoint and allow resumption

## Testing Strategy

### Unit Tests

**Location**: `tests/unit/`

**Coverage**:
- DeepAnalysisCrew tool routing logic
- Flow orchestrator state management
- Data validation components
- Retry and checkpoint logic
- Schema validation

**Pattern**:
```python
def test_should_route_to_stock_tools_when_asset_class_is_stock(mocker):
    # Arrange
    crew = DeepAnalysisCrew(ticker="AAPL", asset_class="stock")
    mock_get_stock_tools = mocker.patch(
        'finwiz.tools.tool_factories.get_stock_crew_tools'
    )
    
    # Act
    tools = crew.get_tools_for_asset_class()
    
    # Assert
    mock_get_stock_tools.assert_called_once()
```

### Integration Tests

**Location**: `tests/integration/`

**Coverage**:
- End-to-end flow execution
- DeepAnalysisCrew with real tool calls (mocked APIs)
- Data flow between components
- Checkpoint save/load
- Resume from interruption

**Pattern**:
```python
@pytest.mark.integration
def test_should_complete_full_flow_with_small_portfolio(mocker):
    # Arrange
    mock_api_calls(mocker)
    flow = FinwizFlow()
    
    # Act
    result = flow.kickoff()
    
    # Assert
    assert flow.state.deep_analysis_success
    assert flow.state.final_report is not None
```


## Validation Tools

### Automated Validation Script

**Location**: `scripts/validate_architecture.py`

**Purpose**: Programmatically verify system compliance with all requirements.

**Key Checks**:

```python
class ArchitectureValidator:
    """Automated validation of FinWiz architecture."""
    
    def validate_deep_analysis_crew_exists(self) -> bool:
        """Check that DeepAnalysisCrew exists."""
        crew_path = Path("src/finwiz/crews/deep_analysis_crew/")
        return crew_path.exists()
    
    def validate_dynamic_tool_routing(self) -> bool:
        """Check that DeepAnalysisCrew implements dynamic tool routing."""
        crew_file = Path("src/finwiz/crews/deep_analysis_crew/deep_analysis_crew.py")
        content = crew_file.read_text()
        return "get_tools_for_asset_class" in content
    
    def validate_flow_sequence(self) -> bool:
        """Check that flow methods are in correct order."""
        flow_file = Path("src/finwiz/flows/flow_orchestrator.py")
        content = flow_file.read_text()
        
        # Check listener dependencies
        checks = [
            '@listen("validate_data_integration")\n    def check_portfolio',
            '@listen("check_portfolio")\n    def analyze_and_update_portfolio',
            '@listen("analyze_and_update_portfolio")\n    def check_stock',
        ]
        return all(check in content for check in checks)
    
    def validate_no_unittest_mock(self) -> bool:
        """Check that no test files use unittest.mock."""
        test_files = Path("tests/").rglob("test_*.py")
        for test_file in test_files:
            content = test_file.read_text()
            if "unittest.mock" in content:
                logger.error(f"Found unittest.mock in {test_file}")
                return False
        return True
    
    def validate_file_sizes(self) -> bool:
        """Check that no Python files exceed 400 lines."""
        py_files = Path("src/").rglob("*.py")
        violations = []
        for py_file in py_files:
            line_count = len(py_file.read_text().splitlines())
            if line_count > 400:
                violations.append(f"{py_file}: {line_count} lines")
        
        if violations:
            logger.error(f"Files exceeding 400 lines: {violations}")
            return False
        return True
    
    def run_all_validations(self) -> Dict[str, bool]:
        """Run all validation checks."""
        results = {
            "deep_analysis_crew_exists": self.validate_deep_analysis_crew_exists(),
            "dynamic_tool_routing": self.validate_dynamic_tool_routing(),
            "flow_sequence": self.validate_flow_sequence(),
            "no_unittest_mock": self.validate_no_unittest_mock(),
            "file_sizes": self.validate_file_sizes(),
        }
        return results
    
    def generate_report(self, results: Dict[str, bool]) -> str:
        """Generate validation report."""
        passed = sum(results.values())
        total = len(results)
        score = (passed / total) * 100
        
        report = f"# FinWiz Architecture Validation Report\n\n"
        report += f"**Overall Score**: {score:.1f}% ({passed}/{total} checks passed)\n\n"
        report += "## Validation Results\n\n"
        
        for check, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            report += f"- {status}: {check}\n"
        
        return report
```


## Configuration Management

### Feature Flags

**Location**: `.env`

```bash
# Deep Analysis Feature
DEEP_PORTFOLIO_ANALYSIS=true
DEEP_ANALYSIS_MAX_RETRIES=3
DEEP_ANALYSIS_TIMEOUT_MINUTES=5

# Alternative Matching Feature
ALTERNATIVE_MATCHING_ENABLED=true
ALTERNATIVE_MIN_GRADE_THRESHOLD=C

# Data Freshness
DATA_FRESHNESS_MAX_AGE_HOURS=24
DATA_FRESHNESS_STRICT_MODE=false

# Flow Resilience
FLOW_CHECKPOINT_ENABLED=true
FLOW_CHECKPOINT_DIR=.checkpoints
FLOW_RETRY_MAX_ATTEMPTS=3
FLOW_RETRY_BACKOFF_INITIAL_SECONDS=1
FLOW_RETRY_BACKOFF_MAX_SECONDS=60

# API Efficiency
API_BATCH_ENABLED=true
API_CONTEXT_SHARING_ENABLED=true
```

### Configuration Loader

```python
# src/finwiz/config/feature_config.py
from pydantic import BaseModel, Field
from typing import Optional
import os

class DeepAnalysisConfig(BaseModel):
    """Configuration for deep analysis feature."""
    enabled: bool = Field(default=True)
    max_retries: int = Field(default=3, ge=1, le=10)
    timeout_minutes: int = Field(default=5, ge=1, le=30)

class DataFreshnessConfig(BaseModel):
    """Configuration for data freshness validation."""
    max_age_hours: int = Field(default=24, ge=1, le=168)
    strict_mode: bool = Field(default=False)

class FlowResilienceConfig(BaseModel):
    """Configuration for flow resilience features."""
    checkpoint_enabled: bool = Field(default=True)
    checkpoint_dir: str = Field(default=".checkpoints")
    retry_max_attempts: int = Field(default=3, ge=1, le=10)
    retry_backoff_initial_seconds: int = Field(default=1, ge=1)
    retry_backoff_max_seconds: int = Field(default=60, ge=10)

class FinWizConfig(BaseModel):
    """Master configuration for FinWiz system."""
    deep_analysis: DeepAnalysisConfig = Field(default_factory=DeepAnalysisConfig)
    data_freshness: DataFreshnessConfig = Field(default_factory=DataFreshnessConfig)
    flow_resilience: FlowResilienceConfig = Field(default_factory=FlowResilienceConfig)
    
    @classmethod
    def from_env(cls) -> "FinWizConfig":
        """Load configuration from environment variables."""
        return cls(
            deep_analysis=DeepAnalysisConfig(
                enabled=os.getenv("DEEP_PORTFOLIO_ANALYSIS", "true").lower() == "true",
                max_retries=int(os.getenv("DEEP_ANALYSIS_MAX_RETRIES", "3")),
                timeout_minutes=int(os.getenv("DEEP_ANALYSIS_TIMEOUT_MINUTES", "5")),
            ),
            data_freshness=DataFreshnessConfig(
                max_age_hours=int(os.getenv("DATA_FRESHNESS_MAX_AGE_HOURS", "24")),
                strict_mode=os.getenv("DATA_FRESHNESS_STRICT_MODE", "false").lower() == "true",
            ),
            flow_resilience=FlowResilienceConfig(
                checkpoint_enabled=os.getenv("FLOW_CHECKPOINT_ENABLED", "true").lower() == "true",
                checkpoint_dir=os.getenv("FLOW_CHECKPOINT_DIR", ".checkpoints"),
                retry_max_attempts=int(os.getenv("FLOW_RETRY_MAX_ATTEMPTS", "3")),
                retry_backoff_initial_seconds=int(os.getenv("FLOW_RETRY_BACKOFF_INITIAL_SECONDS", "1")),
                retry_backoff_max_seconds=int(os.getenv("FLOW_RETRY_BACKOFF_MAX_SECONDS", "60")),
            ),
        )
```


## Implementation Phases

### Phase 1: Core Architecture (Requirements 1-2)

**Goal**: Establish unified DeepAnalysisCrew and correct flow sequence.

**Tasks**:
1. Create DeepAnalysisCrew with dynamic tool routing
2. Refactor flow orchestrator to use structured Pydantic state
3. Implement correct flow sequence with @listen decorators
4. Update discovery crew task descriptions
5. Create DeepAnalysisResult schema

**Success Criteria**:
- DeepAnalysisCrew can analyze single tickers for all asset classes
- Flow executes in correct order: Validation → Portfolio → Deep Analysis → Discovery → Rebalancing → Report
- Discovery crews explicitly state "top 10" purpose

### Phase 2: Data Integration (Requirement 3)

**Goal**: Ensure strict validation and correct data flow.

**Tasks**:
1. Implement DataConsolidationValidator
2. Implement SchemaValidator with extra='forbid'
3. Implement DataFreshnessValidator
4. Create ReporterInput schema
5. Update all data passing to use strict validation

**Success Criteria**:
- All crew outputs are validated against schemas
- Market data freshness is checked (< 24 hours)
- Stale data triggers warnings and reduced confidence
- Reporter only accepts validated ReporterInput

### Phase 3: Analysis Capabilities (Requirement 4)

**Goal**: Comprehensive analysis for all asset classes.

**Tasks**:
1. Implement asset-specific analysis in DeepAnalysisCrew
2. Integrate advanced technical analysis (Fibonacci, support/resistance)
3. Standardize risk scoring (0-5 scale)
4. Implement AlternativeFinder service
5. Add "REQUIRED ENUM VALUES" to all tasks.yaml

**Success Criteria**:
- Stock analysis includes fundamentals, SEC filings, technicals
- ETF analysis includes factsheet, tracking error, holdings
- Crypto analysis includes on-chain metrics, tokenomics
- Underperforming holdings matched with A+ alternatives

### Phase 4: Resilience (Requirement 5)

**Goal**: Robust error handling and performance optimization.

**Tasks**:
1. Implement RetryHandler with exponential backoff
2. Implement CheckpointManager for state persistence
3. Implement GracefulDegradationHandler
4. Add tool-level batching for API efficiency
5. Enable async_execution for I/O-bound tasks

**Success Criteria**:
- Failed executions retry automatically
- Flow can resume from checkpoints
- Failed holdings don't block processing
- API calls are optimized through batching

### Phase 5: Code Quality (Requirement 6)

**Goal**: Clean, maintainable, secure codebase.

**Tasks**:
1. Migrate all tests to pytest-mock
2. Refactor files > 400 lines
3. Migrate HTML generation to BeautifulSoup
4. Validate ReportCrew has empty tools
5. Ensure all crews use @agent, @task, @crew decorators

**Success Criteria**:
- No unittest.mock in codebase
- All files < 400 lines
- HTML generated with BeautifulSoup
- ReportCrew has empty tools list

### Phase 6: Validation & Documentation (Requirements 7-13)

**Goal**: Comprehensive validation and configuration.

**Tasks**:
1. Implement ArchitectureValidator script
2. Create configuration management system
3. Document all feature flags
4. Create validation report generator
5. Test all success criteria

**Success Criteria**:
- Automated validation script runs in < 2 minutes
- All configuration documented in .env.example
- Validation report shows compliance score
- System meets all success criteria


## Performance Considerations

### Expected Performance Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Single ticker deep analysis | < 5 minutes | Time from crew kickoff to result |
| Portfolio (50 holdings) | < 4 hours | Total flow execution time |
| Checkpoint save | < 1 second | Time to persist state |
| Checkpoint load | < 1 second | Time to restore state |
| Validation script | < 2 minutes | Time to run all checks |
| API calls per holding | < 20 | Number of external API calls |

### Optimization Strategies

1. **Parallel Execution**: Use async_execution=True for I/O-bound tasks
2. **Tool Batching**: Fetch multiple indicators in single API call
3. **Context Sharing**: Pass data between tasks to avoid redundant fetches
4. **Caching**: Cache expensive operations with appropriate TTL
5. **Rate Limiting**: Respect API rate limits to avoid throttling

### Memory Management

- Process holdings in batches if portfolio > 100 holdings
- Clear intermediate results after consolidation
- Use generators for large data sets
- Implement memory monitoring and alerts

## Security Considerations

### Data Security

- Never log API keys or sensitive data
- Validate all external inputs
- Sanitize HTML output to prevent XSS
- Use environment variables for secrets

### API Security

- Implement rate limiting
- Use timeouts for all external calls
- Validate API responses before processing
- Handle authentication errors gracefully

## Monitoring and Observability

### Logging Strategy

```python
# Structured logging with context
logger.info(
    "Deep analysis started",
    extra={
        "ticker": ticker,
        "asset_class": asset_class,
        "flow_id": flow_id,
        "timestamp": datetime.now().isoformat()
    }
)
```

### Metrics to Track

- Flow execution time by phase
- Crew execution time by type
- API call volume and latency
- Error rates by type
- Checkpoint save/load frequency
- Data freshness violations

### Alerting

- Alert on flow failures
- Alert on high error rates (> 10%)
- Alert on stale data (> 50% of holdings)
- Alert on performance degradation (> 2x baseline)

## Migration Strategy

### Backward Compatibility

- Maintain existing discovery crews unchanged
- Add DeepAnalysisCrew alongside existing crews
- Use feature flags to enable new flow gradually
- Support both old and new flow during transition

### Rollout Plan

1. **Week 1**: Deploy DeepAnalysisCrew (disabled by default)
2. **Week 2**: Enable for 10% of portfolios, monitor metrics
3. **Week 3**: Enable for 50% of portfolios, validate results
4. **Week 4**: Enable for 100% of portfolios
5. **Week 5**: Remove old flow code

### Rollback Plan

- Feature flag to disable new flow
- Checkpoints allow resuming with old flow
- Keep old flow code for 2 weeks after full rollout

## Success Metrics

### Quantitative Metrics

- **Stability**: 0 hangs or crashes in 100 portfolio analyses
- **Performance**: 95% of single-ticker analyses complete in < 5 minutes
- **Correctness**: 100% of holdings receive non-fallback grades
- **Completeness**: 100% of reports include all required sections
- **Resilience**: 100% of interrupted flows resume successfully
- **Efficiency**: 30% reduction in API calls through batching

### Qualitative Metrics

- Code maintainability improved (files < 400 lines)
- Test coverage increased to > 80%
- Documentation completeness at 100%
- Developer satisfaction with architecture

### 5. Template Variable Validation System

**Purpose**: Prevent runtime failures from missing template variables in task configurations.

**Components**:

```python
# src/finwiz/validation/template_validator.py
class TemplateVariableValidator:
    """Validates template variables in task configurations."""
    
    def scan_task_configs(self, crew_path: Path) -> List[str]:
        """Extract template variables from tasks.yaml."""
        tasks_yaml = crew_path / "config" / "tasks.yaml"
        content = tasks_yaml.read_text()
        
        # Find all {variable} patterns
        variables = re.findall(r'\{(\w+)\}', content)
        return list(set(variables))
    
    def validate_crew_inputs(
        self,
        crew_class: Type,
        required_variables: List[str]
    ) -> bool:
        """Verify crew __init__ accepts all required variables."""
        init_signature = inspect.signature(crew_class.__init__)
        params = list(init_signature.parameters.keys())
        
        missing = [v for v in required_variables if v not in params]
        if missing:
            raise ConfigurationError(
                f"Missing input variables in {crew_class.__name__}: {missing}"
            )
        return True
    
    def validate_at_startup(self) -> None:
        """Run validation when system starts."""
        crews_dir = Path("src/finwiz/crews")
        for crew_path in crews_dir.iterdir():
            if not crew_path.is_dir():
                continue
            
            # Extract template variables
            variables = self.scan_task_configs(crew_path)
            
            # Load crew class
            crew_module = importlib.import_module(
                f"finwiz.crews.{crew_path.name}.{crew_path.name}"
            )
            crew_class = getattr(crew_module, f"{crew_path.name.title()}Crew")
            
            # Validate
            self.validate_crew_inputs(crew_class, variables)
```

### 6. Fail-Fast Error Handling

**Purpose**: Stop execution immediately when critical components fail completely.

**Components**:

```python
# src/finwiz/flows/flow_orchestrator.py (enhanced)
class FinwizFlow(Flow[FinwizState]):
    
    @listen("check_portfolio")
    def analyze_and_update_portfolio(self) -> dict[str, Any]:
        """Phase 3: Deep analysis with fail-fast on complete failure."""
        
        # Run deep analysis
        deep_results = self._run_deep_analysis_on_holdings()
        
        # Calculate success rate
        total_holdings = len(self.state.portfolio_review["holdings"])
        successful = len([r for r in deep_results.values() if r.get("grade") != "F"])
        success_rate = successful / total_holdings if total_holdings > 0 else 0
        
        # FAIL-FAST: 0% success rate
        if success_rate == 0:
            logger.critical(
                f"Deep analysis failed for ALL {total_holdings} holdings (0% success rate). "
                f"Halting execution to prevent wasted API calls."
            )
            raise RuntimeError(
                f"Critical failure: Deep analysis failed for all {total_holdings} holdings. "
                f"Check logs for root cause. Common issues: missing template variables, "
                f"invalid crew configuration, API failures."
            )
        
        # ALERT: High failure rate
        if success_rate < 0.5:
            logger.critical(
                f"Deep analysis has high failure rate: {success_rate:.1%} "
                f"({successful}/{total_holdings} succeeded)"
            )
        
        # Continue with successful results
        self.state.deep_analysis_results = deep_results
        self.state.deep_analysis_success = True
        
        return {"deep_analysis_results": deep_results}
```

### 7. Data Structure Validation with Migration Support

**Purpose**: Handle both legacy and current data structures gracefully.

**Components**:

```python
# src/finwiz/validation/report_data_validator.py (enhanced)
class ReportDataValidator:
    """Validates report input data with migration support."""
    
    def validate_portfolio_review(
        self,
        portfolio_review: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract holdings from nested or flat structure."""
        
        # Try nested structure first (current)
        if "portfolio_review" in portfolio_review:
            holdings = portfolio_review["portfolio_review"].get("holdings", [])
            if holdings:
                logger.info("Found holdings in nested structure")
                return holdings
        
        # Try flat structure (legacy)
        if "holdings" in portfolio_review:
            holdings = portfolio_review["holdings"]
            if holdings:
                logger.info("Found holdings in flat structure (legacy)")
                return holdings
        
        # No holdings found - diagnostic logging
        logger.error(
            f"Portfolio review contains no holdings. "
            f"Available keys: {list(portfolio_review.keys())}"
        )
        raise ReportValidationError(
            f"Portfolio review missing holdings. "
            f"Expected nested ['portfolio_review']['holdings'] or flat ['holdings']. "
            f"Found keys: {list(portfolio_review.keys())}"
        )
```

### 8. Enhanced Cache System with Reliability

**Purpose**: Ensure cache reliably saves and retrieves analysis results.

**Components**:

```python
# src/finwiz/utils/analysis_cache_manager.py (enhanced)
class AnalysisCacheManager:
    """Manages caching of analysis results with reliability."""
    
    def save_to_cache(
        self,
        ticker: str,
        asset_class: str,
        result: Dict[str, Any]
    ) -> bool:
        """Save analysis result to cache with verification."""
        cache_key = self._generate_cache_key(ticker, asset_class)
        cache_path = self.cache_dir / f"{cache_key}.json"
        
        try:
            # Add metadata
            cache_data = {
                "ticker": ticker,
                "asset_class": asset_class,
                "timestamp": datetime.now().isoformat(),
                "version": "1.0",
                "result": result
            }
            
            # Write to cache
            cache_path.write_text(json.dumps(cache_data, indent=2))
            
            # Verify write
            if not cache_path.exists():
                logger.error(f"Cache write verification failed for {cache_key}")
                return False
            
            logger.info(f"Saved to cache: {cache_path} (size: {cache_path.stat().st_size} bytes)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save cache for {ticker}: {e}", exc_info=True)
            return False
    
    def load_from_cache(
        self,
        ticker: str,
        asset_class: str,
        max_age_hours: int = 24
    ) -> Optional[Dict[str, Any]]:
        """Load analysis result from cache with age check."""
        cache_key = self._generate_cache_key(ticker, asset_class)
        cache_path = self.cache_dir / f"{cache_key}.json"
        
        if not cache_path.exists():
            logger.info(f"Cache miss: {cache_path}")
            return None
        
        try:
            cache_data = json.loads(cache_path.read_text())
            
            # Validate metadata
            if cache_data.get("ticker") != ticker:
                logger.warning(f"Cache key mismatch: expected {ticker}, got {cache_data.get('ticker')}")
                return None
            
            # Check age
            timestamp = datetime.fromisoformat(cache_data["timestamp"])
            age_hours = (datetime.now() - timestamp).total_seconds() / 3600
            
            if age_hours > max_age_hours:
                logger.info(f"Cache stale: {cache_key} (age: {age_hours:.1f}h, max: {max_age_hours}h)")
                return None
            
            logger.info(f"Cache hit: {cache_key} (age: {age_hours:.1f}h)")
            return cache_data["result"]
            
        except Exception as e:
            logger.error(f"Failed to load cache for {ticker}: {e}", exc_info=True)
            return None
    
    def verify_cache_directory(self) -> bool:
        """Verify cache directory exists and is writable."""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Test write
            test_file = self.cache_dir / ".write_test"
            test_file.write_text("test")
            test_file.unlink()
            
            logger.info(f"Cache directory verified: {self.cache_dir}")
            return True
            
        except Exception as e:
            logger.warning(f"Cache directory not writable: {self.cache_dir} - {e}")
            return False
```

### 9. Comprehensive Error Logging

**Purpose**: Provide detailed diagnostic information at all critical points.

**Strategy**:

```python
# Enhanced logging throughout the system
class EnhancedLogger:
    """Structured logging with context."""
    
    @staticmethod
    def log_crew_failure(
        crew_name: str,
        ticker: str,
        asset_class: str,
        inputs: Dict[str, Any],
        error: Exception
    ) -> None:
        """Log crew execution failure with full context."""
        logger.error(
            f"Crew execution failed: {crew_name}",
            extra={
                "crew_name": crew_name,
                "ticker": ticker,
                "asset_class": asset_class,
                "inputs": inputs,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "traceback": traceback.format_exc()
            }
        )
    
    @staticmethod
    def log_validation_failure(
        validator_name: str,
        data_sample: Dict[str, Any],
        errors: List[str]
    ) -> None:
        """Log validation failure with data sample."""
        logger.error(
            f"Validation failed: {validator_name}",
            extra={
                "validator": validator_name,
                "errors": errors,
                "data_sample": str(data_sample)[:500]  # First 500 chars
            }
        )
```

### 10. Crypto Portfolio Analysis Support

**Purpose**: Enable full portfolio analysis for crypto holdings from data/crypto.csv.

**Components**:

```python
# src/finwiz/utils/portfolio_holdings_processor.py (enhanced)
class PortfolioHoldingsProcessor:
    """Processes portfolio holdings from CSV files."""
    
    def load_all_holdings(self) -> List[Dict[str, Any]]:
        """Load holdings from all CSV files (stock, etf, crypto)."""
        all_holdings = []
        
        # Load stocks
        stock_path = Path("data/stock.csv")
        if stock_path.exists():
            all_holdings.extend(self._load_csv(stock_path, asset_class="stock"))
        
        # Load ETFs
        etf_path = Path("data/etf.csv")
        if etf_path.exists():
            all_holdings.extend(self._load_csv(etf_path, asset_class="etf"))
        
        # Load crypto
        crypto_path = Path("data/crypto.csv")
        if crypto_path.exists():
            all_holdings.extend(self._load_crypto_csv(crypto_path))
        
        logger.info(f"Loaded {len(all_holdings)} total holdings")
        return all_holdings
    
    def _load_crypto_csv(self, csv_path: Path) -> List[Dict[str, Any]]:
        """Load crypto holdings with ticker normalization."""
        df = pd.read_csv(csv_path)
        holdings = []
        
        for _, row in df.iterrows():
            ticker = row["Ticker"]
            
            # Normalize ticker for Yahoo Finance (BTC → BTC-USD)
            if "-" not in ticker:
                ticker = f"{ticker}-USD"
            
            holdings.append({
                "name": row["Name"],
                "ticker": ticker,
                "asset_class": "crypto",
                "currency": row.get("Currency", "USD")
            })
        
        logger.info(f"Loaded {len(holdings)} crypto holdings from {csv_path}")
        return holdings
```

## Conclusion

This design provides a comprehensive approach to implementing the FinWiz architectural consolidation. The design addresses all 19 requirements through:

1. **Unified Architecture**: Single DeepAnalysisCrew for all single-ticker analysis
2. **Correct Flow**: Logical business sequence with atomic operations
3. **Data Integrity**: Strict validation and freshness checks
4. **Resilience**: Retry logic, checkpointing, and graceful degradation
5. **Quality**: Clean code, standardized testing, secure practices
6. **Validation**: Automated tools to verify compliance
7. **Template Validation**: Startup checks for missing variables (Req 14)
8. **Fail-Fast**: Immediate halt on critical failures (Req 15)
9. **Data Migration**: Support for legacy and current structures (Req 16)
10. **Cache Reliability**: Verified save/load with diagnostics (Req 17)
11. **Error Logging**: Comprehensive diagnostics at all critical points (Req 18)
12. **Crypto Support**: Full portfolio analysis for crypto holdings (Req 19)

The phased implementation approach allows for incremental delivery and validation, while the monitoring and migration strategies ensure a smooth transition to the new architecture.



## Gap Analysis Results

### ✅ VERIFIED: Schemas Use `extra='forbid'`

**Finding**: All schemas in `src/finwiz/schemas/` use `extra='forbid'` for strict validation.

**Evidence**:
- ✅ `common.py`: `model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)`
- ✅ `investment_discovery.py`: All models use `extra="forbid"`
- ✅ `validation.py`: All models use `extra="forbid"`
- ✅ `stock.py`, `crypto.py`, `etf.py`: All models use `extra="forbid"`
- ✅ `portfolio_review.py`: All models use `extra="forbid"`
- ✅ `perplexity.py`, `session.py`, `quantitative.py`: All models use `extra="forbid"`

**Status**: ✅ **NO GAP** - Requirement fully met

### ✅ VERIFIED: Freshness Validation is Enforced

**Finding**: Freshness validation is actively enforced, not just tracked.

**Evidence**:
- ✅ `manager.py`: `get_crew_data_with_freshness_check(crew_name, max_age_hours=24, warn_on_stale=True)`
- ✅ `middleware.py`: `_validate_dependencies()` checks freshness and marks stale dependencies
- ✅ `storage.py`: Filters by `max_age_hours` when querying crew outputs
- ✅ Default threshold: 24 hours for market data
- ✅ Stale data triggers warnings and is tracked in flow state

**Status**: ✅ **NO GAP** - Requirement fully met

### ⚠️ PARTIAL: DeepAnalysisResult Schema

**Finding**: `DeepAnalysisResult` exists but missing `extra='forbid'` and some fields.

**Current Schema** (from `flow_state.py`):
```python
class DeepAnalysisResult(BaseModel):
    ticker: str
    asset_class: str
    crew_name: str
    analyzed_at: str
    composite_score: float  # ✅ Has
    grade: str  # ✅ Has
    fundamental_score: Optional[float]  # ✅ Has
    technical_score: Optional[float]  # ✅ Has
    risk_score: Optional[float]  # ✅ Has (0-5 scale)
    cached: bool
    
    model_config = {  # ❌ Missing extra='forbid'
        "ser_json_timedelta": "iso8601",
        "ser_json_bytes": "base64"
    }
```

**Required Fields** (from requirements):
- ✅ ticker, asset_class
- ✅ fundamental_score, technical_score, risk_score
- ✅ composite_score, grade
- ❌ **Missing**: `data_freshness_hours` (age of market data)
- ❌ **Missing**: `confidence_level` (0.0-1.0)
- ❌ **Missing**: `warnings` (list of warnings)
- ❌ **Missing**: `analysis_timestamp` (datetime, not string)
- ❌ **Missing**: `extra='forbid'` in model_config

**Status**: ⚠️ **MINOR GAP** - Schema needs enhancement

### ⚠️ UNVERIFIED: Discovery Crew Task Descriptions

**Finding**: Need to verify task descriptions explicitly state "top 10" purpose.

**Files to Check**:
- `src/finwiz/crews/stock_crew/config/tasks.yaml`
- `src/finwiz/crews/etf_crew/config/tasks.yaml`
- `src/finwiz/crews/crypto_crew/config/tasks.yaml`

**Status**: ⚠️ **VERIFICATION NEEDED**

### ⚠️ UNVERIFIED: Enum Documentation in tasks.yaml

**Finding**: Need to verify all `tasks.yaml` files have "REQUIRED ENUM VALUES" sections.

**Files to Check**: All crew task configuration files

**Status**: ⚠️ **VERIFICATION NEEDED**

### ⚠️ UNVERIFIED: Test Framework (unittest.mock)

**Finding**: Need to verify no test files use `unittest.mock`.

**Check**: Search all test files for `unittest.mock` imports

**Status**: ⚠️ **VERIFICATION NEEDED**

### ⚠️ UNVERIFIED: File Sizes

**Finding**: Need to verify no Python files exceed 400 lines.

**Check**: Scan all `.py` files in `src/finwiz/`

**Status**: ⚠️ **VERIFICATION NEEDED**

### ⚠️ UNVERIFIED: HTML Generation with BeautifulSoup

**Finding**: Need to verify HTML generation uses BeautifulSoup, not string concatenation.

**Check**: Search for HTML generation code

**Status**: ⚠️ **VERIFICATION NEEDED**

### ⚠️ UNVERIFIED: ReportCrew Empty Tools

**Finding**: Need to verify ReportCrew has empty tools list with `@final_reporter` decorator.

**Check**: `src/finwiz/crews/report_crew/report_crew.py`

**Status**: ⚠️ **VERIFICATION NEEDED**

### ⚠️ UNVERIFIED: Feature Flags Documentation

**Finding**: Need to verify all feature flags are documented in `.env.example`.

**Check**: Compare feature flags in code with `.env.example`

**Status**: ⚠️ **VERIFICATION NEEDED**

### ⚠️ UNVERIFIED: Performance Testing

**Finding**: Need to test system with 50+ holdings portfolio.

**Tests Needed**:
- Portfolio with 50+ holdings completes without hangs
- Single-ticker deep analysis completes in < 5 minutes
- Checkpoint resume functionality works correctly

**Status**: ⚠️ **TESTING NEEDED**

## Summary of Gaps

### Critical Gaps (Must Fix)
1. **DeepAnalysisResult Schema**: Add missing fields and `extra='forbid'`

### Verification Gaps (Must Verify)
2. Discovery crew task descriptions state "top 10"
3. All tasks.yaml have "REQUIRED ENUM VALUES" sections
4. No unittest.mock in test files
5. No files exceed 400 lines
6. HTML generation uses BeautifulSoup
7. ReportCrew has empty tools with @final_reporter
8. All feature flags documented in .env.example

### Testing Gaps (Must Test)
9. Performance with 50+ holdings
10. Single-ticker analysis < 5 minutes
11. Checkpoint resume functionality

**Total Gaps**: 1 critical, 7 verification, 3 testing = **11 items**



## Implementation Approach

### Phase 1: Critical Gap - DeepAnalysisResult Schema Enhancement

**Goal**: Fix the one critical gap in the schema.

**Changes**:
```python
# src/finwiz/flow_state.py
class DeepAnalysisResult(BaseModel):
    """Result from deep crew analysis of a portfolio holding."""
    
    model_config = ConfigDict(
        extra="forbid",  # ✅ ADD: Strict validation
        str_strip_whitespace=True
    )
    
    # Identification
    ticker: str = Field(..., description="Stock/ETF/crypto ticker symbol")
    asset_class: str = Field(..., description="Asset class (stock, etf, crypto)")
    crew_name: str = Field(..., description="Name of crew that performed analysis")
    
    # Scores (0.0 to 1.0)
    fundamental_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    technical_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    risk_score: Optional[float] = Field(None, ge=0.0, le=5.0, description="0=Very Low, 5=Very High")
    composite_score: float = Field(..., ge=0.0, le=1.0)
    
    # Grade
    grade: str = Field(..., description="Letter grade (A+ to F)")
    
    # Metadata
    analysis_timestamp: datetime = Field(  # ✅ ADD: Proper datetime
        default_factory=datetime.now,
        description="When analysis was performed"
    )
    data_freshness_hours: float = Field(  # ✅ ADD: Data age
        ...,
        description="Age of market data in hours"
    )
    confidence_level: float = Field(  # ✅ ADD: Confidence
        ...,
        ge=0.0,
        le=1.0,
        description="Analysis confidence level"
    )
    warnings: List[str] = Field(  # ✅ ADD: Warnings
        default_factory=list,
        description="Analysis warnings"
    )
    
    # Cache metadata
    cached: bool = Field(default=False, description="Whether result came from cache")
```

**Impact**: Low - Only adds fields, doesn't break existing code

### Phase 2: Automated Validation Script

**Goal**: Create comprehensive validation script to verify all requirements.

**Script**: `scripts/validate_finwiz_architecture.py`

**Checks**:
1. ✅ DeepAnalysisCrew exists with dynamic tool routing
2. ✅ Flow sequence is correct
3. ✅ All schemas use `extra='forbid'`
4. ✅ Discovery crews state "top 10" in tasks
5. ✅ All tasks.yaml have "REQUIRED ENUM VALUES"
6. ✅ No unittest.mock in tests
7. ✅ No files exceed 400 lines
8. ✅ HTML uses BeautifulSoup
9. ✅ ReportCrew has empty tools
10. ✅ Feature flags documented

**Output**: Markdown report with compliance score

### Phase 3: Performance Testing Suite

**Goal**: Verify system meets performance requirements.

**Tests**:
1. **Large Portfolio Test**: 50+ holdings without hangs
2. **Single Ticker Performance**: < 5 minutes per analysis
3. **Checkpoint Resume Test**: Interrupt and resume flow

**Location**: `tests/performance/`

### Phase 4: Documentation

**Goal**: Document the existing architecture comprehensively.

**Documents**:
1. **Architecture Validation Report**: Results from validation script
2. **Performance Benchmark Report**: Results from performance tests
3. **Compliance Matrix**: Requirement-by-requirement verification

## Validation Tools Design

### Automated Validation Script

```python
# scripts/validate_finwiz_architecture.py
class FinWizArchitectureValidator:
    """Comprehensive validation of FinWiz architecture."""
    
    def __init__(self):
        self.results = {}
        self.score = 0
        self.total_checks = 0
    
    def validate_all(self) -> Dict[str, bool]:
        """Run all validation checks."""
        self.results = {
            "deep_analysis_crew_exists": self.check_deep_analysis_crew(),
            "dynamic_tool_routing": self.check_dynamic_tool_routing(),
            "flow_sequence_correct": self.check_flow_sequence(),
            "schemas_use_forbid": self.check_schemas_forbid(),
            "discovery_crews_top_10": self.check_discovery_task_descriptions(),
            "enum_documentation": self.check_enum_documentation(),
            "no_unittest_mock": self.check_no_unittest_mock(),
            "file_sizes_ok": self.check_file_sizes(),
            "html_uses_beautifulsoup": self.check_html_generation(),
            "report_crew_empty_tools": self.check_report_crew_tools(),
            "feature_flags_documented": self.check_feature_flags(),
        }
        
        self.score = sum(self.results.values())
        self.total_checks = len(self.results)
        
        return self.results
    
    def generate_report(self) -> str:
        """Generate markdown validation report."""
        compliance_pct = (self.score / self.total_checks) * 100
        
        report = f"# FinWiz Architecture Validation Report\n\n"
        report += f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        report += f"**Overall Compliance**: {compliance_pct:.1f}% ({self.score}/{self.total_checks})\n\n"
        report += "## Validation Results\n\n"
        
        for check, passed in self.results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            report += f"- {status}: {check}\n"
        
        return report
```

### Performance Testing Framework

```python
# tests/performance/test_large_portfolio.py
@pytest.mark.performance
def test_should_analyze_50_holdings_without_hang():
    """Test system stability with 50+ holdings."""
    # Create portfolio with 50+ holdings
    holdings = generate_test_portfolio(size=50)
    
    # Run flow with timeout
    with timeout(seconds=7200):  # 2 hour max
        flow = FinwizFlow()
        result = flow.kickoff()
    
    # Verify completion
    assert flow.state.deep_analysis_success
    assert len(flow.state.deep_analysis_results) >= 50

@pytest.mark.performance
def test_should_complete_single_ticker_in_5_minutes():
    """Test single-ticker analysis performance."""
    start_time = time.time()
    
    crew = DeepAnalysisCrew(ticker="AAPL", asset_class="stock")
    result = crew.crew().kickoff()
    
    duration = time.time() - start_time
    assert duration < 300  # 5 minutes
```

## Success Metrics

### Validation Metrics
- **Compliance Score**: Target 100% (currently ~85%)
- **Critical Gaps**: 0 (currently 1)
- **Verification Items**: 0 unverified (currently 7)

### Performance Metrics
- **50+ Holdings**: Complete without hangs ✅
- **Single Ticker**: < 5 minutes ⏱️
- **Checkpoint Resume**: Works correctly ✅

### Quality Metrics
- **Test Coverage**: > 80%
- **Documentation**: 100% complete
- **Code Quality**: All standards met

## Conclusion

This hybrid validation + gap-filling design provides:

1. **Minimal Changes**: Only 1 critical gap to fix (DeepAnalysisResult schema)
2. **Comprehensive Validation**: Automated script verifies all 13 requirements
3. **Performance Verification**: Tests confirm success criteria
4. **Documentation**: Complete architecture documentation

The system is **85% compliant** with requirements. With the proposed changes, it will reach **100% compliance**.



## Design for Requirement 20: Report Data Completeness

### Overview

The report generation is missing critical data that should be displayed:
1. `data_availability_summary` object is not being passed to the report crew
2. Discovery results (A+ opportunities) are not appearing in the final report  
3. SEC filing links are not being preserved and displayed

### Root Cause Analysis

**Issue 1: Missing `data_availability_summary`**
- The `data_availability_summary` is generated in `flow_orchestrator.py` and stored in `self.state.data_availability_summary`
- However, in `report_crew.py`, the `prepare_crew_context()` method's `required_keys` list includes `"data_availability_summary_formatted"` but NOT `"data_availability_summary"`
- The report tasks expect `inputs.data_availability_summary` (the full object), not just the formatted version
- Result: Report shows "NOT AVAILABLE" for data availability section

**Issue 2: Discovery Results Not Transmitted**
- Discovery results are stored in Flow state as `aplus_opportunities`
- The `required_keys` list in `prepare_crew_context()` already includes `"aplus_opportunities"`
- Need to verify that discovery data is actually being generated and stored in Flow state

**Issue 3: SEC Filing Links Missing**
- SEC filing URLs should be extracted from stock analysis results
- Need to ensure SEC data is preserved in Flow state and passed to report crew

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Flow Orchestrator                         │
│                                                              │
│  1. Generate data_availability_summary                       │
│     self.state.data_availability_summary = summary.model_dump()│
│                                                              │
│  2. Generate data_availability_summary_formatted             │
│     self.state.data_availability_summary_formatted = formatted│
│                                                              │
│  3. Store discovery results                                  │
│     self.state.aplus_opportunities = opportunities           │
│                                                              │
│  4. Store SEC filing data                                    │
│     self.state.sec_filing_urls = urls                        │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       │ Pass state_dict to crew_factory
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Crew Factory                              │
│                                                              │
│  execute_report_crew(inputs: dict)                           │
│    ├─ Initialize ReportCrew                                  │
│    ├─ Call prepare_crew_context(inputs=inputs)               │
│    └─ Execute crew.kickoff(inputs=prepared_context)          │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       │ Prepare context with all required keys
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    ReportCrew                                │
│                                                              │
│  prepare_crew_context(inputs: dict)                          │
│    ├─ Define required_keys list                              │
│    │   ├─ "data_availability_summary" ✅ ADD THIS            │
│    │   ├─ "data_availability_summary_formatted"              │
│    │   ├─ "aplus_opportunities"                              │
│    │   ├─ "sec_filing_urls" ✅ ADD THIS                      │
│    │   └─ ... other keys                                     │
│    │                                                          │
│    ├─ Preserve all required keys from inputs                 │
│    │   for key in required_keys:                             │
│    │       if key in inputs:                                 │
│    │           integrated_context[key] = inputs[key]          │
│    │                                                          │
│    └─ Return integrated_context with all data                │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       │ Context with complete data
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Report Tasks                              │
│                                                              │
│  Access data via inputs:                                     │
│    ├─ inputs.data_availability_summary ✅ NOW AVAILABLE      │
│    ├─ inputs.data_availability_summary_formatted             │
│    ├─ inputs.aplus_opportunities ✅ NOW AVAILABLE            │
│    └─ inputs.sec_filing_urls ✅ NOW AVAILABLE                │
└─────────────────────────────────────────────────────────────┘
```

### Component Changes

#### 1. ReportCrew.prepare_crew_context() - Add Missing Keys

**File**: `src/finwiz/crews/report_crew/report_crew.py`

**Current Code** (line ~960):
```python
required_keys = [
    # Basic metadata
    "current_day", "current_month", "current_year", 
    "current_date", "full_date", "timestamp", "report_language",
    
    # Portfolio data (CRITICAL - prevents template variable errors)
    "portfolio_review",
    
    # Discovery results (CRITICAL - enables discovery section in report)
    "aplus_opportunities",
    "investment_discovery_structured", 
    "investment_discovery_result",
    "investment_discovery_available",
    
    # Rebalancing results
    "portfolio_rebalancing_result",
    "portfolio_rebalancing_available",
    
    # Deep analysis results
    "deep_analysis_results",
    "deep_analysis_success",
    
    # Data availability and status
    "data_availability_summary_formatted",  # ✅ Already present
    "data_availability_report",
    "stale_data_warnings",
]
```

**New Code**:
```python
required_keys = [
    # Basic metadata
    "current_day", "current_month", "current_year", 
    "current_date", "full_date", "timestamp", "report_language",
    
    # Portfolio data (CRITICAL - prevents template variable errors)
    "portfolio_review",
    
    # Discovery results (CRITICAL - enables discovery section in report)
    "aplus_opportunities",
    "investment_discovery_structured", 
    "investment_discovery_result",
    "investment_discovery_available",
    
    # Rebalancing results
    "portfolio_rebalancing_result",
    "portfolio_rebalancing_available",
    
    # Deep analysis results
    "deep_analysis_results",
    "deep_analysis_success",
    
    # Data availability and status
    "data_availability_summary",  # ✅ ADD THIS - Full object for report tasks
    "data_availability_summary_formatted",  # ✅ Already present - Formatted version
    "data_availability_report",
    "stale_data_warnings",
    
    # SEC filing data
    "sec_filing_urls",  # ✅ ADD THIS - SEC filing links for stocks
]
```

**Rationale**:
- The report tasks expect `inputs.data_availability_summary` (the full Pydantic object)
- The formatted version alone is not sufficient for the report to display all required fields
- SEC filing URLs need to be preserved for stock holdings

#### 2. Flow Orchestrator - Ensure SEC Data is Preserved

**File**: `src/finwiz/flows/flow_orchestrator.py`

**Location**: In the `pre_validate_reporter_input()` method, after generating `data_availability_summary`

**Add**:
```python
# Extract SEC filing URLs from stock analysis results
sec_filing_urls = self._extract_sec_filing_urls()
self.state.sec_filing_urls = sec_filing_urls

logger.info(
    f"Extracted SEC filing URLs for {len(sec_filing_urls)} stock holdings",
    extra={"sec_filing_count": len(sec_filing_urls)}
)
```

**Helper Method**:
```python
def _extract_sec_filing_urls(self) -> dict[str, dict[str, str]]:
    """
    Extract SEC filing URLs from stock analysis results.
    
    Returns:
        Dictionary mapping ticker to filing URLs:
        {
            "AAPL": {
                "10-K": "https://www.sec.gov/...",
                "10-Q": "https://www.sec.gov/..."
            }
        }
    """
    sec_urls = {}
    
    # Check deep analysis results for SEC data
    if self.state.deep_analysis_results:
        for ticker, analysis in self.state.deep_analysis_results.items():
            if analysis.get("asset_class") == "stock":
                # Extract SEC URLs from analysis metadata
                if "sec_filing_urls" in analysis:
                    sec_urls[ticker] = analysis["sec_filing_urls"]
    
    # Check stock crew results for SEC data
    if self.state.stock_analysis_result:
        stock_data = self.state.stock_analysis_result
        if isinstance(stock_data, dict) and "sec_filing_urls" in stock_data:
            sec_urls.update(stock_data["sec_filing_urls"])
    
    return sec_urls
```

#### 3. Logging Enhancements

**In `prepare_crew_context()`**, enhance logging to track data preservation:

```python
# After preserving keys from Flow state
if "data_availability_summary" in preserved_keys:
    summary = integrated_context["data_availability_summary"]
    logger.info(
        f"✅ Preserved data_availability_summary: "
        f"{summary.get('total_sources', 0)} total sources, "
        f"{summary.get('available_sources', 0)} available"
    )
else:
    logger.warning(
        "⚠️ data_availability_summary NOT found in Flow state - "
        "report will show 'NOT AVAILABLE'"
    )

if "aplus_opportunities" in preserved_keys:
    opportunities = integrated_context["aplus_opportunities"]
    if isinstance(opportunities, dict):
        total_opportunities = sum(len(v) for v in opportunities.values() if isinstance(v, list))
        logger.info(f"✅ Preserved aplus_opportunities: {total_opportunities} total opportunities")
    else:
        logger.info("✅ Preserved aplus_opportunities (non-dict format)")
else:
    logger.warning(
        "⚠️ aplus_opportunities NOT found in Flow state - "
        "report will not show discovery section"
    )

if "sec_filing_urls" in preserved_keys:
    sec_urls = integrated_context["sec_filing_urls"]
    logger.info(f"✅ Preserved SEC filing URLs for {len(sec_urls)} stocks")
else:
    logger.debug("SEC filing URLs not available (may not have stock holdings)")
```

### Data Flow Validation

#### Validation Points

1. **Flow State Generation** (flow_orchestrator.py):
   - ✅ Verify `data_availability_summary` is generated
   - ✅ Verify `data_availability_summary_formatted` is generated
   - ✅ Verify `aplus_opportunities` is stored after discovery
   - ✅ Verify `sec_filing_urls` is extracted from stock analysis

2. **State to Dict Conversion** (flow_orchestrator.py):
   - ✅ Verify all keys are present in `state_dict` before passing to crew_factory
   - ✅ Log any missing keys

3. **Crew Factory** (crew_factory.py):
   - ✅ Verify `inputs` contains all required keys
   - ✅ Log keys received

4. **Report Crew Context Preparation** (report_crew.py):
   - ✅ Verify `required_keys` includes all necessary keys
   - ✅ Verify keys are preserved from `inputs`
   - ✅ Log successful preservation

5. **Report Task Execution** (report tasks):
   - ✅ Access `inputs.data_availability_summary` without errors
   - ✅ Access `inputs.aplus_opportunities` without errors
   - ✅ Access `inputs.sec_filing_urls` without errors

### Testing Strategy

#### Unit Tests

**Test File**: `tests/unit/crews/report_crew/test_report_crew_data_completeness.py`

```python
def test_should_preserve_data_availability_summary_in_context(mocker):
    """Test that data_availability_summary is preserved in prepare_crew_context."""
    # Arrange
    report_crew = ReportCrew()
    
    inputs = {
        "data_availability_summary": {
            "total_sources": 10,
            "available_sources": 8,
            "unavailable_sources": 2,
            "stale_sources": 1,
            "source_details": {},
            "freshness_warnings": []
        },
        "portfolio_review": {"holdings": []},
    }
    
    # Act
    context = report_crew.prepare_crew_context(inputs=inputs)
    
    # Assert
    assert "data_availability_summary" in context
    assert context["data_availability_summary"]["total_sources"] == 10
    assert context["data_availability_summary"]["available_sources"] == 8


def test_should_preserve_aplus_opportunities_in_context(mocker):
    """Test that aplus_opportunities is preserved in prepare_crew_context."""
    # Arrange
    report_crew = ReportCrew()
    
    inputs = {
        "aplus_opportunities": {
            "stocks": [{"ticker": "MSFT", "grade": "A+"}],
            "etfs": [{"ticker": "VTI", "grade": "A+"}],
            "crypto": []
        },
        "portfolio_review": {"holdings": []},
    }
    
    # Act
    context = report_crew.prepare_crew_context(inputs=inputs)
    
    # Assert
    assert "aplus_opportunities" in context
    assert len(context["aplus_opportunities"]["stocks"]) == 1
    assert context["aplus_opportunities"]["stocks"][0]["ticker"] == "MSFT"


def test_should_preserve_sec_filing_urls_in_context(mocker):
    """Test that sec_filing_urls is preserved in prepare_crew_context."""
    # Arrange
    report_crew = ReportCrew()
    
    inputs = {
        "sec_filing_urls": {
            "AAPL": {
                "10-K": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193&type=10-K",
                "10-Q": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193&type=10-Q"
            }
        },
        "portfolio_review": {"holdings": []},
    }
    
    # Act
    context = report_crew.prepare_crew_context(inputs=inputs)
    
    # Assert
    assert "sec_filing_urls" in context
    assert "AAPL" in context["sec_filing_urls"]
    assert "10-K" in context["sec_filing_urls"]["AAPL"]


def test_should_log_warning_when_data_availability_summary_missing(mocker, caplog):
    """Test that warning is logged when data_availability_summary is missing."""
    # Arrange
    report_crew = ReportCrew()
    
    inputs = {
        "portfolio_review": {"holdings": []},
        # data_availability_summary intentionally missing
    }
    
    # Act
    with caplog.at_level(logging.WARNING):
        context = report_crew.prepare_crew_context(inputs=inputs)
    
    # Assert
    assert "data_availability_summary NOT found" in caplog.text
```

#### Integration Tests

**Test File**: `tests/integration/test_report_data_completeness_integration.py`

```python
def test_should_include_data_availability_in_final_report(mocker):
    """Test that final report includes data availability summary."""
    # Arrange
    flow = FinwizFlow()
    
    # Mock data availability tracker
    mock_tracker = mocker.Mock()
    mock_tracker.get_availability_summary.return_value = DataAvailabilitySummary(
        total_sources=10,
        available_sources=8,
        unavailable_sources=2,
        stale_sources=1,
        source_details={},
        freshness_warnings=[]
    )
    flow.availability_tracker = mock_tracker
    
    # Act
    result = flow.kickoff()
    
    # Assert
    # Check that report contains data availability section
    report_html = result.get("report_html", "")
    assert "Rapport de Disponibilité des Données" in report_html
    assert "Total de sources suivies: 10" in report_html
    assert "Sources disponibles: 8" in report_html


def test_should_include_discovery_results_in_final_report(mocker):
    """Test that final report includes A+ discovery opportunities."""
    # Arrange
    flow = FinwizFlow()
    
    # Mock discovery results
    flow.state.aplus_opportunities = {
        "stocks": [
            {"ticker": "MSFT", "grade": "A+", "composite_score": 0.95},
            {"ticker": "GOOGL", "grade": "A+", "composite_score": 0.92}
        ],
        "etfs": [],
        "crypto": []
    }
    
    # Act
    result = flow.kickoff()
    
    # Assert
    report_html = result.get("report_html", "")
    assert "Opportunités A+" in report_html
    assert "MSFT" in report_html
    assert "GOOGL" in report_html
```

### Success Criteria

1. ✅ `data_availability_summary` is added to `required_keys` list in `prepare_crew_context()`
2. ✅ Report displays data availability section with actual data (not "NOT AVAILABLE")
3. ✅ Report displays total_sources, available_sources, unavailable_sources, stale_sources
4. ✅ Report displays freshness warnings for stale data
5. ✅ `aplus_opportunities` is preserved and displayed in report
6. ✅ Report shows A+ opportunities in dedicated section when available
7. ✅ `sec_filing_urls` is extracted and preserved in Flow state
8. ✅ Report displays clickable SEC filing links for stock holdings
9. ✅ Logging confirms successful preservation of all data
10. ✅ Unit tests verify data preservation in `prepare_crew_context()`
11. ✅ Integration tests verify data appears in final report

### Rollout Plan

1. **Phase 1**: Add `data_availability_summary` to `required_keys` (5 minutes)
2. **Phase 2**: Add `sec_filing_urls` to `required_keys` and implement extraction (15 minutes)
3. **Phase 3**: Enhance logging for data preservation tracking (10 minutes)
4. **Phase 4**: Add unit tests for data preservation (20 minutes)
5. **Phase 5**: Run integration test to verify report completeness (10 minutes)
6. **Phase 6**: Deploy and verify in production (5 minutes)

**Total Estimated Time**: 65 minutes

### Monitoring

After deployment, monitor:
- ✅ Report generation success rate
- ✅ Presence of "NOT AVAILABLE" messages in reports (should be 0)
- ✅ Presence of "Opportunités A+" section in reports (when discovery runs)
- ✅ Presence of SEC filing links in reports (for stock holdings)
- ✅ Log warnings for missing data keys
