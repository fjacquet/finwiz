# FinWiz Architecture Guide

Complete guide to FinWiz system architecture, design principles, and core systems.

## Table of Contents

1. [Design Principles](#design-principles)
2. [System Architecture](#system-architecture)
3. [Core Systems](#core-systems)
4. [Data Flow](#data-flow)
5. [Modernization History](#modernization-history)

## Design Principles

### Simple and Easy to Understand

- Code should be self-explanatory
- Functions should have a single responsibility
- Class and function names should clearly describe their purpose
- Comments and docstrings should explain "why" not just "what"

### Light as a Haiku

Like a haiku poem with its strict form of simplicity and elegance:

- Minimal dependencies
- Concise implementations
- Elegant solutions over complex ones
- Purposeful design choices
- Target files under 200 lines for maximum maintainability

### KISS (Keep It Simple, Stupid)

- Avoid premature optimization
- Choose straightforward solutions over clever ones
- Minimize complexity in algorithms and structures
- Favor readability over brevity

### YAGNI (You Aren't Gonna Need It)

- Don't implement features until they're needed
- Remove unused code and dependencies
- Focus on current requirements

### DRY (Don't Repeat Yourself)

- Extract common patterns into reusable functions
- Use tool factories for standardized tool sets
- Centralize configuration and validation logic

### Configuration-Driven Design

- Separate code from configuration using YAML files
- Use CrewAI decorators (@agent, @task, @crew) with config dictionaries
- Configuration should be externally modifiable without code changes
- Default to configuration-driven approach, with coded fallbacks

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FinWiz Application                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Stock Crew   │  │  ETF Crew    │  │ Crypto Crew  │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                            │                                 │
│                   ┌────────▼────────┐                        │
│                   │ Portfolio Review │                        │
│                   └────────┬────────┘                        │
│                            │                                 │
│                   ┌────────▼────────┐                        │
│                   │   Rebalancing   │                        │
│                   └────────┬────────┘                        │
│                            │                                 │
│                   ┌────────▼────────┐                        │
│                   │  Report Crew    │                        │
│                   └─────────────────┘                        │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                     Core Systems                              │
├─────────────────────────────────────────────────────────────┤
│  Validation │ Caching │ Feature Flags │ Quantitative         │
└─────────────────────────────────────────────────────────────┘
```

### Project Structure

```
src/finwiz/
├── crews/              # AI agent crews
│   ├── crypto_crew/
│   ├── etf_crew/
│   ├── stock_crew/
│   ├── portfolio_rebalancing_crew/
│   ├── investment_discovery_crew/
│   └── report_crew/
├── tools/              # Domain-specific analysis tools
├── schemas/            # Pydantic models with strict validation
├── orchestrators/      # Flow coordination logic
├── quantitative/       # Quantitative analysis framework
├── integration/        # Data integration components
├── validation/         # Validation system
├── utils/              # Utility functions
└── main.py            # CrewAI Flow entry point
```

### CrewAI Flow Design

**Key Principles**:

- Clear separation of concerns between state and behavior
- Explicit flow transitions between crews and tasks
- Asynchronous by default for I/O-bound operations
- Event-driven architecture
- Schema-first design with strict Pydantic validation

**Final Reporter Pattern**:

- Final reporting agents must have empty tools list (`tools=[]`)
- Only consume upstream context
- No external API calls at reporting stage
- Format final HTML output only

## Core Systems

### 1. Validation System

**Purpose**: Centralized data validation with configurable strictness

**Components**:

- `ValidationManager`: Central orchestrator for all validation
- `SchemaRegistry`: Centralized registry for Pydantic models
- `ValidationResult`: Structured validation outcomes
- `ContractValidator`: Boundary contract validation

**Validation Modes** (via `VALIDATION_STRICTNESS`):

- `off`: Validation disabled
- `warn`: Errors converted to warnings (default)
- `error`: Strict enforcement

**Usage**:

```python
from finwiz.validation import get_validation_manager

manager = get_validation_manager()
result = manager.validate_crew_output(data, "stock", "analysis")

if result.is_valid:
    processed_data = result.sanitized_data
else:
    for error in result.errors:
        logger.error(f"Validation error: {error.message}")
```

**Key Features**:

- Strict Pydantic v2 models with `extra='forbid'`
- Field-level error context
- Graceful degradation
- Crew boundary validation

### 2. Caching System

**Purpose**: Intelligent caching with multiple backends and TTL support

**Backends**:

- `memory`: In-memory LRU cache (fast, volatile)
- `file`: File-based cache (persistent, slower)
- `hybrid`: Memory + file (best of both)

**Configuration** (environment variables):

```bash
CACHE_BACKEND=hybrid
CACHE_TTL=2700  # 45 minutes
CACHE_MAX_MEMORY_ITEMS=1000
CACHE_MAX_FILE_SIZE_MB=100
CACHE_STRATEGY=ttl  # ttl, lru, lfu, adaptive
```

**Features**:

- Configurable TTL per cache entry
- Multiple eviction strategies (TTL, LRU, LFU, adaptive)
- Performance monitoring (hit rates, latency)
- Automatic cleanup of expired entries
- Cache warming for frequently accessed data

**Usage**:

```python
from finwiz.cache import get_cache_manager

cache = get_cache_manager()

# Cache with TTL
cache.set("key", value, ttl=3600)

# Retrieve
value = cache.get("key")

# Statistics
stats = cache.get_statistics()
print(f"Hit rate: {stats.hit_rate:.2%}")
```

### 3. Feature Flags System

**Purpose**: Control feature availability and circuit breaker protection

**Configuration**:

```bash
FF_PERPLEXITY_RESEARCH=true
FF_PERPLEXITY_BREAKER_THRESHOLD=5
FF_PERPLEXITY_BREAKER_TIMEOUT=300
```

**Features**:

- Feature enable/disable
- Circuit breaker pattern
- Failure tracking
- Automatic recovery

**Usage**:

```python
from finwiz.utils.feature_flags import get_feature_flags

flags = get_feature_flags()

if flags.is_enabled("perplexity_research"):
    # Use Perplexity integration
    pass

# Record success/failure
flags.record_success("perplexity_research")
flags.record_failure("perplexity_research")
```

### 4. Quantitative Analysis Framework

**Purpose**: Professional-grade quantitative analysis

**Components**:

- **Technical Analysis**: TA-Lib integration with 150+ indicators
- **Backtesting**: Backtrader-based strategy testing
- **Performance Analytics**: Risk-adjusted metrics (Sharpe, Sortino, Calmar)
- **Portfolio Optimization**: Modern portfolio theory (PyPortfolioOpt)
- **Derivatives Pricing**: QuantLib integration (optional)
- **Stock Screening**: Multi-criteria screening with composite scoring

**Key Features**:

- Multi-asset support (stocks, ETFs, crypto)
- Consistent methodologies across asset classes
- Statistical rigor with confidence intervals
- Professional risk metrics

## Data Flow

### Portfolio Analysis Flow

```
1. CSV Input (data/etf.csv, data/stock.csv)
   ↓
2. Ticker Validation (TickerValidationTool)
   ↓
3. Crew Analysis (Stock/ETF/Crypto Crews)
   ↓
4. Price Target Calculation (PriceTargetCalculator)
   ↓
5. Alternative Finding (AlternativeFinder)
   ↓
6. Position Sizing (PositionSizingTool)
   ↓
7. Portfolio Review (PortfolioReview schema)
   ↓
8. HTML Report Generation
```

### Validation Flow

```
1. Data Input
   ↓
2. Schema Lookup (SchemaRegistry)
   ↓
3. Pydantic Validation
   ↓
4. ValidationResult Creation
   ↓
5. Error Handling (based on strictness mode)
   ↓
6. Sanitized Data Output
```

### Caching Flow

```
1. Cache Lookup (check memory → check file)
   ↓
2. Cache Hit? → Return cached value
   ↓
3. Cache Miss? → Execute operation
   ↓
4. Store Result (memory + file if hybrid)
   ↓
5. Update Statistics
```

## Modernization History

### File Decomposition

**Problem**: Large monolithic files (1000+ lines) difficult to maintain

**Solution**: Split into focused modules under 200 lines

**Examples**:

- `main.py` (1291 lines) → `main.py` + `flow_state.py` + `crew_factory.py`
- `quantitative/technical.py` (1323 lines) → 7 focused modules
- `tools/market_screening_tool.py` (1062 lines) → 4 focused modules
- `tools/rebalancing_report_generator.py` (1129 lines) → 4 focused modules

### Scientific Package Optimization

**Problem**: Manual calculations slow and error-prone

**Solution**: Use pandas/numpy vectorized operations

**Examples**:

- Manual `sum()/len()` → `pandas.Series.mean()`
- Manual loops → `pandas.groupby()` aggregation
- Manual moving averages → `pandas.rolling()`
- Manual array operations → numpy broadcasting

### Modular Architecture

**Problem**: Unclear separation of concerns

**Solution**: Extract utilities, calculations, and formatting

**Benefits**:

- Single responsibility per module
- Easier testing
- Better code reuse
- Clearer dependencies

### Testing Infrastructure

**Improvements**:

- pytest with pytest-mock (never unittest.mock)
- Faker for realistic test data
- Comprehensive mocking strategy
- Fast unit tests (< 5 seconds)
- High coverage (80%+ target)

## Integration Patterns

### External Service Integration

**Principles**:

- Optional enhancement pattern
- Feature flag control
- Circuit breaker protection
- Graceful fallback
- Structured data parsing
- Security-focused logging

**Example**: Perplexity Sonar Integration

- Controlled by `FF_PERPLEXITY_RESEARCH` flag
- Circuit breaker with configurable thresholds
- Falls back to existing providers on failure
- Content redaction in logs
- Performance monitoring

### Tool Factories

**Purpose**: Centralize tool initialization

**Pattern**:

```python
def get_stock_crew_tools(
    include_rag: bool = True,
    include_quantitative: bool = True,
    collection_suffix: str = "stock"
) -> list[BaseTool]:
    """Get standardized tool set for Stock Crew."""
    tools = [
        TickerValidationTool(),
        EnhancedSECAnalysisTool(),
    ]
    
    if include_quantitative:
        tools.append(QuantitativeAnalysisTool(asset_class="stock"))
    
    if include_rag:
        tools.extend(get_rag_tools(collection_suffix))
    
    return tools
```

### Agent Validators

**Purpose**: Enforce architectural constraints

**Pattern**:

```python
from finwiz.utils.agent_validators import final_reporter

@final_reporter
@agent
def investment_reporter(self) -> Agent:
    return Agent(
        config=self.agents_config['investment_reporter'],
        tools=[],  # Must be empty - enforced by decorator
        verbose=True
    )
```

## Performance Considerations

### Optimization Strategies

1. **Parallel Processing**: Use asyncio for I/O-bound operations
2. **Caching**: Multi-backend caching with intelligent TTL
3. **Connection Pooling**: Reuse HTTP connections
4. **Rate Limiting**: Respect API limits with exponential backoff
5. **Lazy Loading**: Load data only when needed
6. **Batch Processing**: Process holdings in chunks

### Performance Targets

- **Small Portfolio (< 20 holdings)**: < 5 minutes
- **Medium Portfolio (20-50 holdings)**: < 15 minutes
- **Large Portfolio (50-100 holdings)**: < 30 minutes
- **Unit Tests**: < 5 seconds per suite
- **Cache Hit Rate**: > 50%

## Security Considerations

### Data Privacy

- Never log personal financial amounts
- Sanitize ticker symbols in logs
- Encrypt cached analysis data
- Secure API keys in environment variables

### Input Validation

- Validate ticker format (regex)
- Validate currency codes (ISO 4217)
- Validate asset class enum
- Sanitize CSV inputs

### API Security

- Use HTTPS for all external calls
- Verify SSL certificates
- Implement request timeouts
- Rate limit internal calls

## See Also

- [Developer Guide](DEVELOPER_GUIDE.md) - Development standards and patterns
- [API Reference](API_REFERENCE.md) - Complete API documentation
- [Agent Handbook](agent_handbook.md) - Agent guidelines
- [Validation System](validation_criteria.md) - Validation rules

---

**Version**: 2.0  
**Last Updated**: 2025-03-10
