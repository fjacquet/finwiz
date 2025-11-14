# Design Document

## Overview

This design outlines a comprehensive, systematic approach to modernize the **entire FinWiz codebase** by addressing four core issues: large complex classes, inconsistent testing patterns, CrewAI framework compliance, and insecure HTML generation. The approach prioritizes incremental refactoring that delivers maximum impact while preserving all existing functionality.

**Scope:** This is a codebase-wide modernization effort that will systematically refactor all Python files, tests, crews, and HTML generation code in the FinWiz project.

## Architecture

### Current State Analysis

**Codebase Audit Required:** The following issues exist across the entire codebase:

- Large classes (e.g., `PerplexityAnalysisIntegration` with 975+ lines, and others to be identified)
- Mixed testing approaches (unittest.mock vs pytest-mock) across all test files
- Some crews not following CrewAI decorator patterns
- Complex utility classes mixed with business logic
- HTML generation using insecure string concatenation (f-strings, +, str.format())
- Inconsistent HTML output formatting and encoding

### Target State

After comprehensive modernization:

- **All classes** under 200 lines with single responsibilities
- **100% pytest-mock** usage across entire test suite (0% unittest.mock)
- **All crews** using @agent, @task, @crew decorators with YAML configs
- **All HTML generation** using bs4 (BeautifulSoup) with proper escaping
- Clear separation between utilities and business logic throughout codebase
- Consistent, secure, and maintainable code patterns everywhere

## Components and Interfaces

### 0. Codebase Discovery and Inventory

Before refactoring, we need a complete inventory:

```python
# Discovery script to identify all files needing modernization
class CodebaseAuditor:
    def find_large_classes(self) -> list[tuple[str, int]]:
        """Find all classes >200 lines with their line counts."""
        
    def find_unittest_mock_usage(self) -> list[str]:
        """Find all test files using unittest.mock."""
        
    def find_non_compliant_crews(self) -> list[str]:
        """Find crews not using decorator patterns."""
        
    def find_html_string_generation(self) -> list[str]:
        """Find all files using string concatenation for HTML."""
```

**Output:** Comprehensive inventory document listing all files requiring refactoring.

### 1. Class Decomposition Strategy

#### Large Class Identification

```python
# Example: Current PerplexityAnalysisIntegration (975 lines)
# Split into:
class PerplexityClient:           # API communication (50-100 lines)
class PerplexityParser:           # Response parsing (50-100 lines)  
class PerplexityErrorHandler:     # Error handling (50-100 lines)
class PerplexityLogger:           # Logging utilities (50-100 lines)
```

#### Decomposition Rules

- **Single Responsibility**: Each class does one thing well
- **Composition over Inheritance**: Use dependency injection for shared functionality
- **Utility Extraction**: Move helper functions to separate modules

#### Priority Refactoring: DeepAnalysisScorer (1,301 lines)

**Current State**: God class with 30+ methods handling all scoring logic

**Target State**: 4 focused classes with clear responsibilities

```python
# NEW: FundamentalScorer (~300 lines)
class FundamentalScorer:
    """Handles fundamental analysis scoring for all asset classes."""
    
    def calculate_stock_score(self, data: dict) -> tuple[float, dict]:
        """Calculate fundamental score for stocks (ROE, debt, growth)."""
        
    def calculate_etf_score(self, data: dict) -> tuple[float, dict]:
        """Calculate fundamental score for ETFs (expense ratio, tracking error)."""
        
    def calculate_crypto_score(self, data: dict) -> tuple[float, dict]:
        """Calculate fundamental score for crypto (market cap, volume, age)."""

# NEW: TechnicalScorer (~200 lines)
class TechnicalScorer:
    """Handles technical analysis scoring."""
    
    def calculate_technical_score(self, data: dict) -> tuple[float, dict]:
        """Calculate technical score (RSI, MACD, trends)."""

# NEW: RiskScorer (~200 lines)
class RiskScorer:
    """Handles risk assessment scoring."""
    
    def calculate_risk_score(self, data: dict) -> tuple[float, dict]:
        """Calculate risk score (volatility, drawdown, beta)."""

# REFACTORED: DeepAnalysisScorer (~400 lines)
class DeepAnalysisScorer:
    """Orchestrates scoring components and aggregates results."""
    
    def __init__(self):
        self.fundamental_scorer = FundamentalScorer()
        self.technical_scorer = TechnicalScorer()
        self.risk_scorer = RiskScorer()
    
    def calculate_composite_score(self, ticker: str, asset_class: str, data: dict):
        """Coordinate scoring and aggregate results."""
        fundamental = self.fundamental_scorer.calculate_score(asset_class, data)
        technical = self.technical_scorer.calculate_technical_score(data)
        risk = self.risk_scorer.calculate_risk_score(data)
        return self._aggregate_scores(fundamental, technical, risk)
```

**Benefits**:

- Single Responsibility Principle compliance
- Easier to test individual components
- Clearer code organization
- Reduced cognitive load
- Each class under 400 lines

#### Strategy Pattern for Asset-Specific Logic

**Problem**: Repeated `if asset_class == "stock"` conditionals in 8+ methods

**Solution**: Strategy pattern with factory

```python
# NEW: Asset Analyzer Strategy Pattern
from abc import ABC, abstractmethod

class AssetAnalyzer(ABC):
    """Abstract base class for asset-specific analysis."""
    
    @abstractmethod
    def calculate_fundamental_score(self, data: dict) -> tuple[float, dict]:
        """Calculate fundamental score for this asset type."""
        
    @abstractmethod
    def extract_metrics(self, data: dict) -> dict:
        """Extract asset-specific metrics."""
        
    @abstractmethod
    def validate_data(self, data: dict) -> bool:
        """Validate asset-specific data requirements."""

class StockAnalyzer(AssetAnalyzer):
    """Stock-specific analysis logic."""
    
    def calculate_fundamental_score(self, data: dict) -> tuple[float, dict]:
        roe = self._safe_get_float(data, "roe", 0.0)
        debt = self._safe_get_float(data, "debt_to_equity", 0.0)
        growth = self._safe_get_float(data, "revenue_growth", 0.0)
        # Stock-specific scoring logic
        return score, details

class ETFAnalyzer(AssetAnalyzer):
    """ETF-specific analysis logic."""
    
    def calculate_fundamental_score(self, data: dict) -> tuple[float, dict]:
        expense = self._safe_get_float(data, "expense_ratio", 1.0)
        tracking = self._safe_get_float(data, "tracking_error", 0.0)
        # ETF-specific scoring logic
        return score, details

class CryptoAnalyzer(AssetAnalyzer):
    """Crypto-specific analysis logic."""
    
    def calculate_fundamental_score(self, data: dict) -> tuple[float, dict]:
        market_cap = self._safe_get_float(data, "market_cap", 0.0)
        volume = self._safe_get_float(data, "volume_24h", 0.0)
        # Crypto-specific scoring logic
        return score, details

class AnalyzerFactory:
    """Factory for creating asset-specific analyzers."""
    
    @staticmethod
    def get_analyzer(asset_class: str) -> AssetAnalyzer:
        analyzers = {
            "stock": StockAnalyzer,
            "etf": ETFAnalyzer,
            "crypto": CryptoAnalyzer
        }
        analyzer_class = analyzers.get(asset_class.lower())
        if not analyzer_class:
            raise ValueError(f"Unknown asset class: {asset_class}")
        return analyzer_class()

# USAGE in DeepAnalysisScorer
def calculate_fundamental_score(self, asset_class: str, data: dict):
    analyzer = AnalyzerFactory.get_analyzer(asset_class)
    return analyzer.calculate_fundamental_score(data)
```

**Benefits**:

- Eliminates 200+ lines of duplicate conditional logic
- Easy to add new asset classes
- Clearer separation of concerns
- Improved testability

#### Configuration Extraction Pattern

**Problem**: Magic numbers scattered across 15+ methods

**Solution**: Centralized configuration dataclass

```python
from dataclasses import dataclass

@dataclass
class ScoringThresholds:
    """Centralized scoring thresholds configuration."""
    
    # ROE thresholds
    roe_excellent: float = 0.20
    roe_very_good: float = 0.15
    roe_good: float = 0.10
    roe_acceptable: float = 0.05
    
    # Debt thresholds
    debt_very_low: float = 0.2
    debt_low: float = 0.5
    debt_moderate: float = 1.0
    debt_high: float = 2.0
    
    # Growth thresholds
    growth_excellent: float = 0.20
    growth_good: float = 0.10
    growth_acceptable: float = 0.05
    
    # Expense ratio thresholds (ETF)
    expense_excellent: float = 0.001
    expense_good: float = 0.0025
    expense_acceptable: float = 0.005
    
    # Volatility thresholds
    volatility_low: float = 0.15
    volatility_moderate: float = 0.25
    volatility_high: float = 0.40

# USAGE
thresholds = ScoringThresholds()

def score_roe(self, roe: float) -> float:
    """Score ROE using configured thresholds."""
    if roe >= thresholds.roe_excellent:
        return 1.0
    elif roe >= thresholds.roe_very_good:
        return 0.8
    elif roe >= thresholds.roe_good:
        return 0.6
    elif roe >= thresholds.roe_acceptable:
        return 0.4
    return 0.2
```

**Benefits**:

- Single source of truth for thresholds
- Easy to tune scoring parameters
- Better documentation of scoring logic
- Supports experimentation and A/B testing

### 2. CrewAI Pattern Standardization

#### Standard Crew Structure

```
src/finwiz/crews/{crew_name}/
├── {crew_name}.py          # @agent, @task, @crew decorators only
└── config/
    ├── agents.yaml         # Agent definitions
    └── tasks.yaml          # Task definitions
```

#### Decorator Pattern

```python
from crewai import Agent, Task, Crew
from crewai.flow import flow

class StockCrew:
    @agent
    def analyst(self) -> Agent:
        return Agent(config=self.agents_config['analyst'])
    
    @task  
    def analyze_stock(self) -> Task:
        return Task(config=self.tasks_config['analyze_stock'])
    
    @crew
    def crew(self) -> Crew:
        return Crew(agents=[self.analyst()], tasks=[self.analyze_stock()])
```

### 3. Testing Standardization

#### pytest-mock Migration Pattern

```python
# Before (unittest.mock) - TO BE ELIMINATED FROM ENTIRE CODEBASE
from unittest.mock import patch, MagicMock

def test_api_call():
    with patch('module.api_client') as mock_client:
        mock_client.return_value = {'data': 'test'}
        # test code

# After (pytest-mock) - REQUIRED FOR ALL TESTS
def test_api_call(mocker):
    mock_client = mocker.patch('module.api_client')
    mock_client.return_value = {'data': 'test'}
    # test code
```

**Migration Scope:** All test files in `tests/` directory must be converted.

### 4. HTML Generation Standardization

#### bs4 Migration Pattern

```python
# Before (string concatenation) - TO BE ELIMINATED FROM ENTIRE CODEBASE
def generate_report(title: str, data: dict) -> str:
    html = f"<html><head><title>{title}</title></head>"
    html += f"<body><h1>{title}</h1>"
    html += f"<p>{data['content']}</p></body></html>"
    return html

# After (bs4) - REQUIRED FOR ALL HTML GENERATION
from bs4 import BeautifulSoup, Tag

def generate_report(title: str, data: dict) -> str:
    soup = BeautifulSoup("", "html.parser")
    html = soup.new_tag("html")
    
    head = soup.new_tag("head")
    title_tag = soup.new_tag("title")
    title_tag.string = title  # Automatic escaping
    head.append(title_tag)
    
    body = soup.new_tag("body")
    h1 = soup.new_tag("h1")
    h1.string = title
    body.append(h1)
    
    p = soup.new_tag("p")
    p.string = data['content']  # Automatic XSS protection
    body.append(p)
    
    html.append(head)
    html.append(body)
    soup.append(html)
    
    return soup.prettify(formatter="html")
```

**Migration Scope:** All Python files generating HTML must be converted to use bs4.

**Security Benefits:**

- Automatic HTML entity escaping prevents XSS
- Proper UTF-8 encoding handling
- Well-formed HTML structure guaranteed
- Better code readability and maintainability

#### Template Method Pattern for Opportunity Extraction

**Problem**: 90% identical logic across 3 extraction methods in APlusExtractor

**Solution**: Template Method pattern with base class

```python
from abc import ABC, abstractmethod

class OpportunityExtractor(ABC):
    """Base class for extracting opportunities using Template Method pattern."""
    
    def extract(self, json_data: dict) -> list[dict]:
        """Template method defining the extraction algorithm."""
        opportunities = []
        
        # Load and parse JSON (common logic)
        data = self._load_and_parse_json(json_data)
        
        # Extract opportunities (asset-specific)
        for item in data:
            if self._should_include(item):
                opportunity = self._build_opportunity(item)
                opportunities.append(opportunity)
        
        return opportunities
    
    def _load_and_parse_json(self, json_data: dict) -> list[dict]:
        """Common JSON loading and parsing logic."""
        # Shared implementation
        pass
    
    @abstractmethod
    def _should_include(self, item: dict) -> bool:
        """Determine if item should be included (asset-specific)."""
        pass
    
    @abstractmethod
    def _build_opportunity(self, item: dict) -> dict:
        """Build opportunity object (asset-specific)."""
        pass

class StockOpportunityExtractor(OpportunityExtractor):
    """Extract stock opportunities."""
    
    def _should_include(self, item: dict) -> bool:
        """Stock-specific inclusion logic."""
        return (
            item.get("grade") == "A+" and
            item.get("asset_class") == "stock" and
            item.get("composite_score", 0) >= 0.85
        )
    
    def _build_opportunity(self, item: dict) -> dict:
        """Build stock opportunity."""
        return {
            "ticker": item["ticker"],
            "name": item["name"],
            "grade": item["grade"],
            "score": item["composite_score"],
            "sector": item.get("sector", "Unknown")
        }

class ETFOpportunityExtractor(OpportunityExtractor):
    """Extract ETF opportunities."""
    
    def _should_include(self, item: dict) -> bool:
        """ETF-specific inclusion logic."""
        return (
            item.get("grade") == "A+" and
            item.get("asset_class") == "etf" and
            item.get("expense_ratio", 1.0) <= 0.15
        )
    
    def _build_opportunity(self, item: dict) -> dict:
        """Build ETF opportunity."""
        return {
            "ticker": item["ticker"],
            "name": item["name"],
            "grade": item["grade"],
            "expense_ratio": item.get("expense_ratio"),
            "tracking_error": item.get("tracking_error")
        }

class CryptoOpportunityExtractor(OpportunityExtractor):
    """Extract crypto opportunities."""
    
    def _should_include(self, item: dict) -> bool:
        """Crypto-specific inclusion logic."""
        return (
            item.get("grade") == "A+" and
            item.get("asset_class") == "crypto" and
            item.get("market_cap", 0) >= 10_000_000_000
        )
    
    def _build_opportunity(self, item: dict) -> dict:
        """Build crypto opportunity."""
        return {
            "ticker": item["ticker"],
            "name": item["name"],
            "grade": item["grade"],
            "market_cap": item.get("market_cap"),
            "volume_24h": item.get("volume_24h")
        }

# USAGE in APlusDataExtractor
def extract_opportunities(self, asset_class: str, json_data: dict) -> list[dict]:
    """Extract opportunities using appropriate extractor."""
    extractors = {
        "stock": StockOpportunityExtractor,
        "etf": ETFOpportunityExtractor,
        "crypto": CryptoOpportunityExtractor
    }
    extractor_class = extractors.get(asset_class.lower())
    if not extractor_class:
        raise ValueError(f"Unknown asset class: {asset_class}")
    
    extractor = extractor_class()
    return extractor.extract(json_data)
```

**Benefits**:

- Eliminates ~200 lines of duplicate extraction logic
- Easy to add new asset types
- Follows Open/Closed Principle
- Clear separation of common vs specific logic

#### Utility Function Extraction Pattern

**Problem**: Same threshold-based scoring logic repeated in 10+ places

**Solution**: Reusable utility function

```python
def calculate_threshold_score(
    value: float,
    thresholds: list[tuple[float, float]],
    reverse: bool = False
) -> float:
    """
    Calculate score based on threshold ranges.
    
    Args:
        value: The value to score
        thresholds: List of (threshold, score) tuples, sorted ascending
        reverse: If True, lower values get higher scores
    
    Returns:
        Score between 0.0 and 1.0
    
    Example:
        thresholds = [(0.05, 0.4), (0.10, 0.6), (0.15, 0.8), (0.20, 1.0)]
        score = calculate_threshold_score(0.18, thresholds)  # Returns 0.8
    """
    if reverse:
        thresholds = [(t, s) for t, s in reversed(thresholds)]
        value = -value
    
    for threshold, score in thresholds:
        if value >= threshold:
            continue
        return score
    
    return thresholds[-1][1]  # Return highest score if above all thresholds

# USAGE
roe_thresholds = [(0.05, 0.4), (0.10, 0.6), (0.15, 0.8), (0.20, 1.0)]
roe_score = calculate_threshold_score(roe_value, roe_thresholds)

debt_thresholds = [(0.2, 1.0), (0.5, 0.8), (1.0, 0.6), (2.0, 0.4)]
debt_score = calculate_threshold_score(debt_value, debt_thresholds, reverse=True)
```

**Benefits**:

- Eliminates 100+ lines of duplicate logic
- Consistent scoring behavior
- Easier to modify scoring algorithm
- Better testability

## Data Models

### Configuration Models

```python
from pydantic import BaseModel

class CrewConfig(BaseModel):
    """Simple crew configuration."""
    agents_config: dict
    tasks_config: dict
    
class ToolConfig(BaseModel):
    """Simple tool configuration."""
    api_key: str | None = None
    timeout: int = 30
    retries: int = 3
```

### Refactored Class Interfaces

```python
class APIClient(Protocol):
    """Simple interface for API clients."""
    async def call(self, endpoint: str, params: dict) -> dict: ...

class DataParser(Protocol):
    """Simple interface for data parsers."""
    def parse(self, raw_data: str) -> dict: ...
```

## Error Handling

### Simple Error Strategy

- Keep existing error handling patterns
- Extract error handling logic from large classes into focused error handler classes
- Maintain current graceful fallback behavior (especially for Perplexity integration)

```python
class PerplexityErrorHandler:
    """Focused error handling for Perplexity integration."""
    
    def handle_api_error(self, error: Exception) -> dict:
        """Simple error handling with fallback."""
        if "rate limit" in str(error).lower():
            return self._create_rate_limit_response()
        return self._create_generic_error_response(error)
```

## Testing Strategy

### Migration Approach

1. **Identify unittest.mock usage**: Search codebase for `unittest.mock` imports
2. **Convert incrementally**: Replace with pytest-mock patterns file by file
3. **Validate behavior**: Ensure tests still pass with same coverage

### Test Structure

```python
# Standard test pattern
def test_should_do_something_when_condition(mocker):
    # Arrange
    mock_dependency = mocker.patch('module.dependency')
    mock_dependency.return_value = expected_data
    
    # Act
    result = function_under_test()
    
    # Assert
    assert result == expected_result
    mock_dependency.assert_called_once()
```

## Implementation Plan

### Phase 0: Discovery and Inventory (REQUIRED FIRST)

1. **Scan entire codebase** to identify all files needing modernization
2. **Generate inventory report** with:
   - All classes >200 lines (sorted by size)
   - All test files using unittest.mock
   - All crews not using decorator patterns
   - All files using string concatenation for HTML
3. **Prioritize refactoring order** (largest/most critical first)
4. **Create tracking document** for progress monitoring

### Phase 1: Class Decomposition (Codebase-Wide)

1. **Process all identified large classes** (starting with largest)
2. Analyze responsibilities within each class
3. Extract utilities and helper functions first
4. Split business logic into focused classes
5. Update imports and dependencies
6. **Verify no class >200 lines remains** (except documented exceptions)

### Phase 2: CrewAI Standardization (All Crews)

1. **Audit all existing crews** for decorator usage
2. **Convert every crew** to use @agent, @task, @crew patterns
3. Move configuration to YAML files for all crews
4. Update crew initialization code throughout codebase
5. **Verify all crews follow standard structure**

### Phase 3: Testing Migration (Entire Test Suite)

1. **Search entire test suite** for all unittest.mock usage
2. **Convert all test files** to pytest-mock patterns
3. Run test suite after each file conversion
4. **Verify 0% unittest.mock usage** remains
5. Update test documentation

### Phase 4: HTML Generation Migration (All HTML Code)

1. **Identify all Python files** generating HTML
2. **Convert all HTML generation** to use bs4
3. Add beautifulsoup4 to pyproject.toml dependencies
4. **Verify no string concatenation** for HTML remains
5. Update coding standards documentation

### Migration Safety

- **Incremental changes**: One file at a time, but process ALL files
- **Preserve interfaces**: Keep public APIs unchanged during refactoring
- **Continuous testing**: Run tests after each change
- **Progress tracking**: Maintain checklist of completed files
- **Rollback ready**: Each change should be easily reversible
- **Completion verification**: Final audit to ensure 100% coverage

## Success Criteria

### Measurable Outcomes (100% Coverage Required)

- **Class Size**: 0 classes >200 lines (except documented exceptions)
- **Test Consistency**: 100% pytest-mock usage, 0% unittest.mock usage
- **CrewAI Compliance**: 100% of crews use decorator patterns with YAML configs
- **HTML Security**: 100% of HTML generation uses bs4, 0% string concatenation
- **Functionality**: All existing features work unchanged
- **Performance**: No performance regressions

### Quality Gates

- All tests pass (100% pass rate maintained)
- Ruff linting passes (no new violations)
- No increase in complexity metrics
- Documentation updated for all changed components
- Final audit confirms 100% completion of all four modernization goals

### Completion Verification

```bash
# Verify no large classes remain
find src -name "*.py" -exec wc -l {} \; | awk '$1 > 200 {print}'

# Verify no unittest.mock usage remains
grep -r "unittest.mock" tests/

# Verify all crews use decorators
grep -r "@agent\|@task\|@crew" src/finwiz/crews/

# Verify no HTML string concatenation remains
grep -r "f\"<\|\"<.*>\".*+" src/ --include="*.py"

# Verify bs4 is in dependencies
grep "beautifulsoup4" pyproject.toml
```
