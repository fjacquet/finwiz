# Design Document: JSON-First Crew Architecture

## Overview

This design document outlines the technical approach for migrating FinWiz crew task outputs from markdown-based to
JSON-based structured data format. The migration will improve data flow, validation, and integration between crews
while maintaining human-readable final reports.



## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Crew Pipeline                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Task 1 (Intermediate)                                          │
│  ├─ Agent executes with tools                                   │
│  ├─ Generates output                                            │
│  └─ CrewAI validates against Pydantic schema                    │
│      └─> Outputs: task_name.json (validated)                   │
│                                                                   │
│  Task 2 (Intermediate)                                          │
│  ├─ Reads Task 1 JSON output                                    │
│  ├─ Agent executes with context                                 │
│  └─ CrewAI validates against Pydantic schema                    │
│      └─> Outputs: task_name.json (validated)                   │
│                                                                   │
│  Task N (Final Report)                                          │
│  ├─ Reads all previous JSON outputs                             │
│  ├─ Agent generates HTML report                                 │
│  └─ No Pydantic validation (HTML output)                        │
│      └─> Outputs: final_report.html                            │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Intermediate Tasks**: Generate JSON with Pydantic validation
2. **Context Passing**: JSON data flows through CrewAI context
3. **Final Task**: Consumes JSON, generates HTML report
4. **Translation Task**: Consumes HTML, generates translated HTML

## Components and Interfaces

### 1. Pydantic Schema Layer

**Location**: `src/finwiz/schemas/`

**Purpose**: Define strict data structures for all crew outputs

**Structure**:

```
src/finwiz/schemas/
├── __init__.py
├── common.py              # Shared base models
├── stock.py               # Stock crew schemas
├── etf.py                 # ETF crew schemas
├── crypto.py              # Crypto crew schemas
├── investment_discovery.py
├── portfolio_rebalancing.py
└── report.py              # Report crew schemas
```

**Key Principles**:

- Use modern Python 3.12+ union syntax: `Type | None` and `Type1 | Type2`
- Use lowercase built-in types: `list`, `dict`, `tuple` instead of `List`, `Dict`, `Tuple`
- Set `model_config = ConfigDict(extra='forbid')` for strict validation
- Include comprehensive docstrings and field descriptions
- Use `Field()` with descriptions and examples

**Example Schema**:

```python
from pydantic import BaseModel, Field, ConfigDict

class TechnicalAnalysis(BaseModel):
    """Technical analysis output for a financial instrument."""
    
    model_config = ConfigDict(extra='forbid')
    
    ticker: str = Field(..., description="Ticker symbol")
    rsi: float = Field(..., ge=0, le=100, description="RSI indicator value")
    macd: float = Field(..., description="MACD indicator value")
    recommendation: str = Field(..., pattern="^(BUY|HOLD|SELL)$")
    confidence: float = Field(..., ge=0.0, le=1.0)
    support_levels: list[float] = Field(default_factory=list)
    resistance_levels: list[float] = Field(default_factory=list)
    notes: str | None = Field(None, description="Additional notes")
```

### 2. Task Configuration Layer

**Location**: `src/finwiz/crews/{crew_name}/config/tasks.yaml`

**Purpose**: Configure tasks to use Pydantic schemas for output validation

**Configuration Pattern**:

```yaml
# Intermediate task with JSON output
technical_analysis_task:
  description: "Perform technical analysis on {ticker}"
  expected_output: "Technical analysis with indicators and recommendations"
  output_pydantic: "TechnicalAnalysis"  # References schema class
  output_file: "technical_analysis.json"  # JSON extension
  agent: technical_analyst
  async_execution: true

# Final report task with HTML output
final_report_task:
  description: "Generate comprehensive HTML report"
  expected_output: "Professional HTML report with all analysis"
  # No output_pydantic - HTML output
  output_file: "final_report.html"  # HTML extension
  agent: report_writer
  async_execution: false  # Final task must be synchronous
```

### 3. Schema Registry

**Location**: `src/finwiz/schemas/__init__.py`

**Purpose**: Central registry for all schemas with easy import

**Implementation**:

```python
# src/finwiz/schemas/__init__.py
from .common import BaseAnalysis, RiskAssessment
from .stock import TenKInsight, StockAnalysis
from .etf import ETFFactsheet, ETFTopHolding
from .crypto import CryptoThesis, CryptoAnalysis
from .investment_discovery import InvestmentOpportunity
from .portfolio_rebalancing import PortfolioReview, HoldingDecision

__all__ = [
    "BaseAnalysis",
    "RiskAssessment",
    "TenKInsight",
    "StockAnalysis",
    "ETFFactsheet",
    "ETFTopHolding",
    "CryptoThesis",
    "CryptoAnalysis",
    "InvestmentOpportunity",
    "PortfolioReview",
    "HoldingDecision",
]
```

### 4. Context Passing Mechanism

**How it works**:

1. Task completes and generates JSON output
2. CrewAI validates against `output_pydantic` schema
3. Validated data stored in task output
4. Next task receives data through `context` parameter
5. Task can access previous outputs via context

**Example**:

```python
# Task 1 generates JSON
@task
def analysis_task(self) -> Task:
    return Task(
        config=self.tasks_config['analysis_task'],
        output_pydantic=TechnicalAnalysis,
    )

# Task 2 consumes JSON from context
@task
def report_task(self) -> Task:
    return Task(
        config=self.tasks_config['report_task'],
        context=[self.analysis_task()],  # Receives validated JSON
    )
```

### 5. Error Handling Layer

**Purpose**: Provide clear error messages when validation fails

**Components**:

- **JSON Parsing Errors**: Include file path and line number
- **Schema Validation Errors**: Include field path and validation rule
- **Type Errors**: Show expected vs actual types
- **Missing Fields**: List all missing required fields

**Implementation Strategy**:

- Leverage Pydantic's built-in validation error messages
- Add custom error handlers for common issues
- Log full output for debugging when validation fails
- Provide actionable error messages to developers

## Data Models

### Common Base Models

**Location**: `src/finwiz/schemas/common.py`

```python
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class BaseAnalysis(BaseModel):
    """Base model for all analysis outputs."""
    
    model_config = ConfigDict(extra='forbid')
    
    ticker: str = Field(..., description="Ticker symbol")
    analysis_date: datetime = Field(default_factory=datetime.now)
    data_sources: list[str] = Field(default_factory=list)
    
class RiskAssessmentStandardized(BaseModel):
    """Standardized risk assessment (0-5 scale)."""
    
    model_config = ConfigDict(extra='forbid')
    
    scale: str = Field(default="0_5", pattern="^0_5$")
    score: float = Field(..., ge=0.0, le=5.0)
    level: str = Field(..., pattern="^(Very Low|Low|Medium|High|Very High)$")
    risk_factors: list[str] = Field(default_factory=list)
```

### Stock Crew Schemas

**Location**: `src/finwiz/schemas/stock.py`

**Schemas**:

- `TenKInsight`: 10-K filing analysis
- `StockTechnicalAnalysis`: Technical indicators
- `StockSentiment`: Sentiment analysis
- `StockRiskAssessment`: Risk evaluation

### ETF Crew Schemas

**Location**: `src/finwiz/schemas/etf.py`

**Schemas**:

- `ETFFactsheet`: ETF overview and metrics
- `ETFTopHolding`: Individual holding details
- `ETFTechnicalAnalysis`: Technical indicators
- `ETFRiskAssessment`: Risk evaluation

### Crypto Crew Schemas

**Location**: `src/finwiz/schemas/crypto.py`

**Schemas**:

- `CryptoThesis`: Investment thesis
- `CryptoTechnicalAnalysis`: Technical indicators
- `CryptoMarketAnalysis`: Market overview
- `CryptoRiskAssessment`: Risk evaluation

### Investment Discovery Schemas

**Location**: `src/finwiz/schemas/investment_discovery.py`

**Schemas**:

- `InvestmentOpportunity`: Discovered opportunity
- `ScreeningCriteria`: Screening parameters
- `RankingResult`: Ranked opportunities

### Portfolio Rebalancing Schemas

**Location**: `src/finwiz/schemas/portfolio_rebalancing.py`

**Schemas**:

- `PortfolioReview`: Overall portfolio analysis
- `HoldingDecision`: Keep/sell decision per holding
- `Alternative`: Alternative investment suggestion
- `RebalancingPlan`: Rebalancing recommendations

## Type Annotation Standards

### Python 3.12+ Modern Syntax (Project Standard)

**Design Decision**: Use modern Python 3.12 union operator syntax throughout all schemas to maintain consistency with the project's Python 3.12+ standard.

**Rationale**:

- The project has standardized on Python 3.12+ (documented in README.md and PYTHON_312_UPGRADE_SUMMARY.md)
- Modern syntax is cleaner, more readable, and follows current Python best practices
- Recent schema audit incorrectly converted to legacy syntax under mistaken belief about CrewAI compatibility
- Testing will verify CrewAI compatibility with modern syntax

### Required Patterns

```python
from pydantic import BaseModel, Field, ConfigDict

# ✅ CORRECT - Use modern union syntax for nullable fields
field1: str | None = None
field2: int | None = Field(None, description="Optional field")

# ❌ INCORRECT - Legacy syntax (to be removed)
from typing import Optional
field1: Optional[str] = None
field2: Optional[int] = Field(None, description="Optional field")

# ✅ CORRECT - Use modern union syntax for multiple types
field3: int | float = Field(..., description="Numeric field")
field4: str | list[str] = Field(..., description="String or list")

# ❌ INCORRECT - Legacy syntax (to be removed)
from typing import Union, List
field3: Union[int, float] = Field(..., description="Numeric field")
field4: Union[str, List[str]] = Field(..., description="String or list")
```

### Schema Validation Checklist

Before deploying any schema:

1. ✅ All optional fields use `Type | None` syntax (Python 3.12+)
2. ✅ All union types use `Type1 | Type2` syntax (Python 3.12+)
3. ✅ No use of legacy `Optional[Type]` or `Union[Type1, Type2]` syntax
4. ✅ Use lowercase `list`, `dict`, `tuple` instead of `List`, `Dict`, `Tuple`
5. ✅ `model_config = ConfigDict(extra='forbid')` is set
6. ✅ All fields have descriptions
7. ✅ Test with CrewAI converter to verify compatibility

## Known Issues and Design Decisions

### Legacy Type Annotation Syntax in Current Schemas

**Issue**: Recent schema audit (documented in SCHEMA_AUDIT_SUMMARY.md) converted schemas FROM modern Python 3.12 syntax TO legacy `Optional`/`Union` syntax, contradicting the project's Python 3.12+ standard.

**Current State**:

- Schemas use `Optional[Type]` instead of `Type | None`
- Schemas use `Union[Type1, Type2]` instead of `Type1 | Type2`
- Schemas import from `typing` module unnecessarily

**Affected Files**:

- `src/finwiz/schemas/common.py`
- `src/finwiz/schemas/validation.py`
- `src/finwiz/schemas/portfolio_review.py`
- `src/finwiz/schemas/perplexity.py`
- `src/finwiz/schemas/investment_discovery.py`
- `src/finwiz/schemas/session.py`
- `src/finwiz/schemas/quantitative.py`
- `src/finwiz/schemas/rebalancing/trades.py`

**Design Decision**: Revert to modern Python 3.12+ syntax across all schemas.

**Rationale**:

1. **Project Standard**: Python 3.12+ is documented as the project standard in README.md and PYTHON_312_UPGRADE_SUMMARY.md
2. **Code Consistency**: Rest of codebase uses modern syntax; schemas should match
3. **Best Practices**: Modern union operators are the recommended Python 3.10+ approach
4. **Maintainability**: Consistent style reduces cognitive load and maintenance burden
5. **Future-Proofing**: Modern syntax is the direction Python is moving

**Implementation Approach**:

1. Systematically revert all affected schema files
2. Replace `Optional[Type]` → `Type | None`
3. Replace `Union[Type1, Type2]` → `Type1 | Type2`
4. Replace `List[Type]` → `list[Type]` (and similar for `Dict`, `Tuple`)
5. Remove unnecessary `from typing import Optional, Union, List` imports
6. Test with CrewAI converter to verify compatibility
7. Document any compatibility issues discovered

**Risk Mitigation**:

- Comprehensive testing with CrewAI's `convert_to_model` function
- Integration tests for all crews using updated schemas
- Fallback plan if CrewAI incompatibility discovered
- Clear documentation of any workarounds needed

## Migration Strategy

### Phase 1: Schema Design and Audit

**Duration**: 1-2 weeks

**Design Decision**: Revert recent schema audit changes and modernize all schemas to Python 3.12+ syntax.

**Rationale**:

- Recent audit incorrectly converted schemas to legacy `Optional`/`Union` syntax
- Project standard is Python 3.12+ with modern union operators
- Consistency with rest of codebase is critical for maintainability
- CrewAI compatibility will be verified through testing

**Activities**:

1. Audit existing schemas in `src/finwiz/schemas/`
2. Revert legacy `Optional[Type]` to modern `Type | None` syntax
3. Revert legacy `Union[Type1, Type2]` to modern `Type1 | Type2` syntax
4. Replace `List`, `Dict`, `Tuple` with lowercase `list`, `dict`, `tuple`
5. Remove unnecessary `from typing import Optional, Union, List` imports
6. Design new schemas for crews without existing schemas
7. Create comprehensive schema documentation
8. Test all schemas with CrewAI converter to verify compatibility

**Deliverables**:

- Updated schemas with modern Python 3.12+ type annotations
- Schema documentation with examples
- Schema validation test suite
- CrewAI compatibility verification report

### Phase 2: Task Configuration Updates

**Duration**: 1 week

**Activities**:

1. Update `tasks.yaml` files for all crews
2. Add `output_pydantic` to intermediate tasks
3. Ensure `output_file` extensions match format (`.json` or `.html`)
4. Update task descriptions to reflect JSON output
5. Test task configurations

**Deliverables**:

- Updated `tasks.yaml` files for all crews
- Task configuration validation tests

### Phase 3: Crew-by-Crew Migration

**Duration**: 3-4 weeks

**Order** (simplest to most complex):

1. Portfolio Rebalancing Crew (already uses JSON)
2. Stock Crew (4 intermediate tasks)
3. ETF Crew (4 intermediate tasks)
4. Crypto Crew (4 intermediate tasks)
5. Investment Discovery Crew (6 intermediate tasks)
6. Report Crew (3 intermediate tasks)

**Per-Crew Activities**:

1. Update task configurations
2. Test JSON generation with real data
3. Verify schema validation
4. Test context passing between tasks
5. Verify final HTML report generation
6. Run integration tests
7. Run mypy on modified crew files
8. Ensure all type annotations are correct

**Deliverables**:

- Migrated crews with JSON outputs
- Integration test results
- Performance benchmarks
- Zero mypy errors across all crews

### Phase 4: Backward Compatibility Removal

**Duration**: 1 week

**Activities**:

1. Remove markdown output support
2. Clean up legacy code
3. Update documentation
4. Final integration tests

**Deliverables**:

- Clean codebase without markdown support
- Updated documentation

### Phase 5: Performance Optimization

**Duration**: 1 week

**Activities**:

1. Benchmark JSON parsing vs markdown parsing
2. Optimize schema validation
3. Optimize context passing
4. Monitor production performance

**Deliverables**:

- Performance optimization report
- Production monitoring dashboard

## Testing Strategy

### Unit Tests

**Location**: `tests/unit/schemas/`

**Coverage**:

- Schema validation with valid data
- Schema validation with invalid data
- Type annotation compatibility
- Field constraints (min/max, patterns)
- Optional field handling

**Example**:

```python
def test_technical_analysis_schema_valid():
    """Test TechnicalAnalysis schema with valid data."""
    data = {
        "ticker": "AAPL",
        "rsi": 65.5,
        "macd": 2.3,
        "recommendation": "BUY",
        "confidence": 0.85,
        "support_levels": [150.0, 145.0],
        "resistance_levels": [160.0, 165.0],
    }
    analysis = TechnicalAnalysis(**data)
    assert analysis.ticker == "AAPL"
    assert analysis.recommendation == "BUY"

def test_technical_analysis_schema_invalid_recommendation():
    """Test TechnicalAnalysis schema with invalid recommendation."""
    data = {
        "ticker": "AAPL",
        "rsi": 65.5,
        "macd": 2.3,
        "recommendation": "INVALID",  # Should fail
        "confidence": 0.85,
    }
    with pytest.raises(ValidationError) as exc_info:
        TechnicalAnalysis(**data)
    assert "recommendation" in str(exc_info.value)
```

### Integration Tests

**Location**: `tests/integration/crews/`

**Coverage**:

- End-to-end crew execution
- JSON output generation
- Schema validation in CrewAI context
- Context passing between tasks
- Final HTML report generation

**Example**:

```python
@pytest.mark.integration
def test_stock_crew_json_output():
    """Test stock crew generates valid JSON outputs."""
    crew = StockCrew()
    result = crew.kickoff(inputs={"ticker": "AAPL"})
    
    # Verify JSON files exist
    assert Path("output/stock/technical_analysis.json").exists()
    assert Path("output/stock/fundamental_analysis.json").exists()
    
    # Verify JSON is valid
    with open("output/stock/technical_analysis.json") as f:
        data = json.load(f)
        analysis = TechnicalAnalysis(**data)
        assert analysis.ticker == "AAPL"
```

### Schema Validation Tests

**Location**: `tests/unit/schemas/test_crewai_compatibility.py`

**Purpose**: Ensure all schemas work with CrewAI's converter

**Example**:

```python
from crewai.utilities.converter import convert_to_model

def test_schema_crewai_compatibility():
    """Test that schema works with CrewAI converter."""
    json_str = '{"ticker": "AAPL", "rsi": 65.5, ...}'
    
    # This should not raise AttributeError
    result = convert_to_model(
        result=json_str,
        model=TechnicalAnalysis,
        llm=None,
    )
    assert isinstance(result, TechnicalAnalysis)
```

## Error Handling

### JSON Parsing Errors

**Error Type**: `json.JSONDecodeError`

**Handling**:

```python
try:
    data = json.loads(output)
except json.JSONDecodeError as e:
    logger.error(
        f"JSON parsing failed for {task_name}",
        extra={
            "file": output_file,
            "line": e.lineno,
            "column": e.colno,
            "error": str(e),
        }
    )
    raise TaskOutputError(f"Invalid JSON in {output_file}: {e}")
```

### Schema Validation Errors

**Error Type**: `pydantic.ValidationError`

**Handling**:

```python
try:
    validated = SchemaClass(**data)
except ValidationError as e:
    logger.error(
        f"Schema validation failed for {task_name}",
        extra={
            "schema": SchemaClass.__name__,
            "errors": e.errors(),
            "data": data,
        }
    )
    # Provide field-level error details
    for error in e.errors():
        logger.error(
            f"Field '{'.'.join(str(loc) for loc in error['loc'])}': "
            f"{error['msg']} (type: {error['type']})"
        )
    raise TaskOutputError(f"Validation failed: {e}")
```

### Type Annotation Compatibility Issues

**Error Type**: `AttributeError: 'types.UnionType' object has no attribute '__name__'`

**Design Decision**: If this error occurs with modern Python 3.12+ syntax, it indicates a CrewAI compatibility issue that must be addressed through testing and potential workarounds.

**Prevention**:

- Test all schemas with CrewAI converter before deployment
- Use schema validation tests with actual CrewAI integration
- Enforce modern Python 3.12+ type annotation standards in code review
- Document any CrewAI-specific compatibility issues discovered

**Handling** (if occurs):

```python
try:
    result = convert_to_model(output, model=SchemaClass, llm=None)
except AttributeError as e:
    if "'types.UnionType' object has no attribute '__name__'" in str(e):
        logger.error(
            f"Schema {SchemaClass.__name__} encountered CrewAI compatibility issue. "
            f"Modern Python 3.12+ union syntax may require CrewAI update or workaround. "
            f"Error: {e}"
        )
        # Document the issue and investigate CrewAI compatibility
        raise SchemaCompatibilityError(
            f"CrewAI compatibility issue with modern Python syntax: {e}"
        )
    raise
```

**Mitigation Strategy**:

- If CrewAI doesn't support modern syntax, file issue with CrewAI project
- Consider temporary workaround layer if needed
- Prioritize project-wide consistency over tool-specific requirements

## Performance Considerations

### JSON Parsing Performance

**Expected**: JSON parsing should be ≥2x faster than markdown parsing

**Optimization**:

- Use `orjson` for faster JSON parsing (if needed)
- Stream large JSON files instead of loading entirely
- Cache parsed schemas for reuse

### Schema Validation Performance

**Considerations**:

- Pydantic validation is fast but not free
- Complex nested schemas may have overhead
- Validation happens once per task output

**Optimization**:

- Keep schemas as flat as possible
- Use `Field(...)` constraints judiciously
- Profile validation performance for large outputs

### Context Passing Performance

**Considerations**:

- JSON data passed through CrewAI context
- Large JSON objects may impact memory
- Multiple tasks reading same JSON

**Optimization**:

- Use lazy loading for large datasets
- Consider streaming for very large outputs
- Monitor memory usage during crew execution

## Security Considerations

### Input Validation

- All external data must pass through Pydantic validation
- Use `Field()` constraints to limit input ranges
- Validate ticker symbols, dates, and numeric values

### Output Sanitization

- Ensure JSON output does not contain sensitive data (API keys, PII)
- Never log full JSON outputs containing user financial data
- Validate that HTML output is safe (no XSS)
- Log validation failures for security audit (without sensitive data)
- Use structured logging with sanitized fields only

**Example**:

```python
# ❌ NEVER log full output with potential PII
logger.error(f"Validation failed: {full_output}")

# ✅ Log sanitized metadata only
logger.error(
    "Validation failed",
    extra={
        "task": task_name,
        "schema": schema_name,
        "error_count": len(errors),
        "field_errors": [e["loc"] for e in errors],  # Field paths only
    }
)
```

### Schema Security

- Use `extra='forbid'` to prevent unexpected fields
- Validate all enum values
- Ensure no code execution in schema validation

## Monitoring and Observability

### Metrics to Track

1. **Schema Validation Success Rate**: % of tasks that pass validation
2. **JSON Parsing Performance**: Time to parse JSON outputs
3. **Validation Error Rate**: % of tasks that fail validation
4. **Schema Coverage**: % of tasks with Pydantic schemas
5. **Data Quality**: % of outputs with complete required fields

### Logging Strategy

**Log Levels**:

- `INFO`: Successful validation, task completion
- `WARNING`: Validation warnings, missing optional fields
- `ERROR`: Validation failures, parsing errors
- `DEBUG`: Full output for debugging

**Log Format**:

```python
logger.info(
    "Task output validated",
    extra={
        "task": task_name,
        "schema": schema_name,
        "output_file": output_file,
        "validation_time_ms": validation_time,
    }
)
```

### Quality Gates

**Pre-Commit Checks**:

1. Ruff linting passes
2. Unit tests pass
3. Schema validation tests pass

**CI/CD Pipeline**:

1. Full test suite passes
2. Integration tests pass
3. Performance benchmarks meet targets

## Internationalization Considerations

### French Language Support

**Requirement**: Final HTML reports must remain in French with proper formatting

**Design Decisions**:

1. **JSON Intermediate Outputs**: Language-agnostic (field names in English, values can be multilingual)
2. **Final HTML Reports**: Generated in French using JSON data
3. **Schema Field Names**: English (standard practice for APIs/data structures)
4. **Schema Descriptions**: English (for developer documentation)
5. **Report Content**: French (user-facing)

**Example**:

```python
# JSON intermediate output (language-agnostic structure)
{
  "ticker": "AAPL",
  "recommendation": "BUY",  # Enum value
  "rationale": "Strong fundamentals and growth potential"  # Can be French
}

# HTML final report (French)
<p><strong>Recommandation:</strong> ACHETER</p>
<p><strong>Justification:</strong> Fondamentaux solides et potentiel de croissance</p>
```

**Translation Strategy**:

- Enum values (BUY/HOLD/SELL) translated in HTML generation
- Rationale text generated in French by agents
- Schema validation language-agnostic

## Documentation

### Schema Documentation

**Location**: `docs/schemas/`

**Content**:

- Schema reference for each crew
- Field descriptions and examples
- Validation rules and constraints
- Usage examples
- Internationalization notes

**Format**:

```markdown
# TechnicalAnalysis Schema

## Overview
Technical analysis output for financial instruments.

## Fields

### ticker (required)
- **Type**: `str`
- **Description**: Ticker symbol
- **Example**: `"AAPL"`

### rsi (required)
- **Type**: `float`
- **Description**: RSI indicator value
- **Constraints**: 0.0 ≤ value ≤ 100.0
- **Example**: `65.5`

## Example

\`\`\`json
{
  "ticker": "AAPL",
  "rsi": 65.5,
  "macd": 2.3,
  "recommendation": "BUY",
  "confidence": 0.85
}
\`\`\`
```

### Migration Guide

**Location**: `docs/JSON_MIGRATION_GUIDE.md`

**Content**:

- Overview of changes
- Before/after examples
- Common issues and solutions
- Type annotation standards
- Testing guidelines

## Success Criteria

### Functional Requirements

1. ✅ 100% of intermediate tasks output JSON with Pydantic validation
2. ✅ 100% of JSON outputs pass schema validation
3. ✅ Final reports remain in HTML format
4. ✅ Context passing works between all tasks
5. ✅ No data loss during format conversion

### Performance Requirements

1. ✅ JSON parsing is ≥2x faster than markdown parsing
2. ✅ Schema validation adds <100ms overhead per task
3. ✅ Memory usage remains within acceptable limits
4. ✅ No performance degradation in crew execution

### Quality Requirements

1. ✅ <1% of tasks fail due to JSON validation errors
2. ✅ All schemas have comprehensive documentation
3. ✅ All schemas use modern Python 3.12+ type annotations
4. ✅ 90%+ test coverage for schema validation
5. ✅ CrewAI compatibility verified for all schemas
6. ✅ Consistent type annotation style across entire codebase

### Type Safety Requirements (NEW)

1. ✅ Zero mypy errors when running `mypy --python-version 3.12 src`
2. ✅ All functions have complete type annotations
3. ✅ All optional parameters explicitly typed with `| None`
4. ✅ mypy integrated into Makefile `quality` target
5. ✅ mypy checks pass before code commits (blocking requirement)

## Appendix

### Schema Template

```python
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class MySchema(BaseModel):
    """Brief description of the schema."""
    
    model_config = ConfigDict(extra='forbid')
    
    # Required fields
    field1: str = Field(..., description="Description of field1")
    field2: int = Field(..., ge=0, description="Description of field2")
    
    # Optional fields (use modern Python 3.12+ syntax)
    field3: str | None = Field(None, description="Description of field3")
    field4: list[str] | None = Field(default_factory=list)
    
    # Union types (use modern Python 3.12+ syntax)
    field5: int | float = Field(..., description="Numeric field")
    
    # Timestamp
    created_at: datetime = Field(default_factory=datetime.now)
```

### Task Configuration Template

```yaml
# Intermediate task with JSON output
my_analysis_task:
  description: "Perform analysis on {input}"
  expected_output: "Structured analysis with metrics and recommendations"
  output_pydantic: "MySchema"
  output_file: "my_analysis.json"
  agent: my_analyst
  async_execution: true
  depends_on:
    - previous_task

# Final report task with HTML output
final_report_task:
  description: "Generate comprehensive HTML report"
  expected_output: "Professional HTML report with all analysis"
  output_file: "final_report.html"
  agent: report_writer
  async_execution: false
  context:
    - my_analysis_task
```

### Common Validation Errors

**Error**: `extra fields not permitted`
**Cause**: Schema has `extra='forbid'` and output contains unexpected fields
**Solution**: Remove unexpected fields or add them to schema

**Error**: `field required`
**Cause**: Required field missing from output
**Solution**: Ensure agent generates all required fields

**Error**: `value is not a valid enumeration member`
**Cause**: Field value not in allowed enum values
**Solution**: Update output to use valid enum value

**Error**: `AttributeError: 'types.UnionType' object has no attribute '__name__'`
**Cause**: Potential CrewAI incompatibility with modern Python 3.12+ union syntax
**Solution**:

1. Verify CrewAI version and compatibility
2. Test with CrewAI converter to confirm issue
3. If confirmed, document as known limitation
4. Consider filing issue with CrewAI project
5. Implement workaround layer if necessary while maintaining modern syntax in schemas

---

**Version**: 2.1  
**Last Updated**: 2025-05-10  
**Status**: Updated - Added mypy integration and type safety requirements (Requirement 10)
