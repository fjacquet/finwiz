# FinWiz Design Principles

## Overview

FinWiz is designed to be elegant and minimalist, like a haiku.
It works with crewai as a flow of tasks and as the fondation of all.
This document outlines the core principles that guide its development.

## Core Principles

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

### External Service Integration Principles

#### Perplexity Sonar Integration Architecture

The Perplexity Sonar integration follows these architectural principles:

- **Optional Enhancement Pattern**: Integration is designed as an optional enhancement that doesn't affect core functionality
- **Feature Flag Control**: All integration points are controlled by the `FF_PERPLEXITY_RESEARCH` feature flag
- **Circuit Breaker Protection**: Automatic failure detection and recovery with configurable thresholds
- **Graceful Fallback**: Seamless fallback to existing data providers when Perplexity is unavailable
- **Structured Data Parsing**: Convert raw API responses to validated Pydantic models (SonarArticle, SonarSearchResult)
- **Security-Focused Logging**: Content redaction in logs while preserving operational metadata
- **Performance Monitoring**: Track latency, success rates, and circuit breaker state
- **Error Classification**: Structured error handling with appropriate retry strategies
- **Configuration Validation**: Startup validation of API keys and integration settings

#### Integration Design Patterns

- **Wrapper Pattern**: PerplexityAnalysisIntegration wraps the existing PerplexitySearchTool
- **Factory Pattern**: Standardized initialization through utility functions
- **Observer Pattern**: Feature flag tracking for success/failure metrics
- **Strategy Pattern**: Multiple analysis types (sentiment, technical, fundamental) with context-specific queries
- **Decorator Pattern**: Enhanced analysis tools maintain existing interfaces while adding Perplexity capabilities

### CrewAI Flow Design Principles

- **Clear Separation of Concerns**: Maintain a clear distinction between state and behavior.
- **Explicit Flow Transitions**: Define transitions between crews and tasks clearly.
- **Asynchronous by Default (where possible)**:
  - Leverage asynchronous execution (`async_execution=True`) for I/O-bound tasks to maximize performance.
  - Be mindful of framework constraints, such as the requirement for the final task in a sequential process to be synchronous.
- **Event-Driven Architecture**: Design components to react to events where applicable.
- **Final Reporter Without Tools**: Configure the final reporting agent with an empty tools list. It must only consume upstream context and format the final HTML output, preventing any unintended external calls or research at this stage.
- **Schema-First Design**: Use strict Pydantic v2 models with `extra='forbid'` to enforce data contracts and prevent schema drift.
- **Validation Boundaries**: Validate data at crew boundaries with configurable strictness levels (off/warn/error).
- **Centralized Validation**: Use ValidationManager and SchemaRegistry for consistent validation across all components.
- **Structured Error Handling**: Implement ValidationResult with detailed error context, field paths, and remediation guidance.
- **Contract Validation**: Enforce boundary contracts between crews using ContractValidator for expected data structure compliance.
- **Portfolio Integration**: Support CSV-based portfolio ingestion with automatic ticker validation and keep/sell decision logic.
- **Persistent State Management**: Support loading and updating existing financial plans from previous sessions.
- **Intelligent Caching**: Implement multi-backend caching with configurable TTL and eviction strategies.
- **Performance Monitoring**: Track cache hit rates and system performance metrics.
- **Quantitative Integration**: Support professional-grade quantitative analysis with industry-standard libraries (Backtrader, TA-Lib, QuantLib, PyPortfolioOpt).
- **Multi-Asset Support**: Provide consistent quantitative methodologies across stocks, ETFs, and cryptocurrencies with unified schemas.
- **Statistical Rigor**: Implement statistically sound methods for backtesting, performance analysis, risk assessment, and signal generation.
- **Modular Quantitative Architecture**: Separate concerns between data management, analysis engines, and result presentation.
- **Professional Standards**: Follow quantitative finance best practices with proper risk management and performance attribution.
- **Extensible Framework**: Design quantitative components for easy extension with new indicators, strategies, and analysis methods.
- **Optional Enhancement Integration**: Design external service integrations as optional enhancements with feature flag control and graceful fallback.
- **Circuit Breaker Protection**: Implement circuit breaker patterns for external API integrations to ensure system reliability.
- **Graceful Degradation**: Ensure core functionality continues when optional services are unavailable or failing.
- **Security-First Integration**: Implement content redaction, API key validation, and secure logging for external service integrations.
- **Structured Error Handling**: Classify errors appropriately and implement retry logic with exponential backoff for transient failures.
- **Portfolio Rebalancing Architecture**: Implement modular rebalancing system with pluggable optimization strategies, comprehensive cost analysis, and risk management safeguards.
- **Rebalancing Optimization**: Support multiple optimization methods (minimize trades, minimize costs, risk-aware) with configurable constraints and tolerance bands.
- **Transaction Cost Modeling**: Provide comprehensive cost analysis including commissions, spreads, market impact, and tax considerations.
- **Performance Attribution**: Track rebalancing effectiveness with historical analysis, performance attribution, and scenario comparison capabilities.

### Configuration-Driven Design

- Separate code from configuration using YAML files
- Use CrewAI decorators (@agent, @task, @crew) with config dictionaries
- Maintain strict separation between agent/task definitions and their parameters
- Configuration should be externally modifiable without code changes
- Default to configuration-driven approach, with coded fallbacks for robustness

### KISS (Keep It Simple, Stupid)

- Avoid premature optimization
- Choose straightforward solutions over clever ones
- Minimize complexity in algorithms and structures
- Favor readability over brevity

### YAGNI (You Aren't Gonna Need It)

- Only implement features that are immediately necessary
- Avoid speculative generality
- Refactor when patterns emerge, not before
- Focus on solving the current problem well

### DRY (Don't Repeat Yourself)

- Extract common functionality into helper methods
- Use inheritance and composition appropriately
- Maintain a single source of truth for data
- Leverage patterns like the template method when appropriate

## Code Structure Guidelines

1. **State Management**
   - Keep state immutable where possible
   - Document state transitions clearly
   - Minimize global state

2. **Flow Design**
   - Use descriptive names for flow steps
   - Document dependencies between steps
   - Keep flows linear where possible

3. **Error Handling**
   - Fail fast and explicitly
   - Provide meaningful error messages
   - Handle edge cases gracefully

4. **Documentation**
   - Document public interfaces thoroughly
   - Include examples where appropriate
   - Keep documentation up-to-date with code changes

5. **Module Organization**
   - Split utility functions into separate modules by functionality
   - Use empty `__init__.py` files for package structure
   - Prefer explicit imports from specific modules over package-level imports
   - Place all imports at the top of the file, never inline within functions or methods
   - Group related functionality in dedicated directories
   - **File Size Guidelines**: Target files under 200 lines for maximum readability and maintainability
   - **Single Responsibility**: Each module should have a clear, focused purpose
   - **Extract Common Patterns**: Move shared calculations, formatting, and utilities to dedicated modules

6. **Project Directory Layout**
   - The `src` directory should contain only Python source code (e.g., the main application package `finwiz`, tools, etc.).
   - Data files, logs, outputs, archives, and other runtime artifacts should be stored in directories at the project root (e.g., `knowledge/`, `logs/`, `output/`, `archive/`, `storage/`).
   - Configuration in `settings.py` should define the paths to these root-level artifact directories. This keeps the source code separate from generated data and improves clarity.

7. **Python Package and Workflow Management**
   - Use `uv` for all Python package and virtual environment operations (e.g., `uv pip install`, `uv venv`).
   - Run individual Python scripts using `uv run python <script.py>`.
   - To execute the main project workflow, use the `crewai flow kickoff` command from the project root. This is the standard way to run the entire sequence of crews.

     ```bash
     crewai flow kickoff
     ```

   - Maintain consistent package versions across development environments.

1. **Report Generation**
   - Generate reports in HTML format for rich presentation
   - Always include UTF-8 encoding declarations to handle special characters and emojis
   - Use emojis strategically to enhance readability and visual appeal
   - Ensure cross-browser compatibility with proper HTML5 standards
   - Structure reports with clear sections and a logical flow of information
   - Support persistent financial planning by loading existing reports from `report/` directory

2. **Data Validation & Contracts**
   - Use Pydantic v2 models with strict validation (`extra='forbid'`)
   - Implement configurable validation strictness (off/warn/error modes) via `VALIDATION_STRICTNESS` environment variable
   - Validate data at crew boundaries using ValidationManager to prevent schema drift
   - Use SchemaRegistry for centralized model management and dynamic schema lookup with automatic initialization
   - Implement structured error handling with ValidationResult, ValidationError, and ValidationWarning classes
   - Export JSON schemas for external integration and documentation
   - Provide clear error messages with field paths, context, and remediation guidance
   - Enforce contract validation between crews using ContractValidator for boundary compliance
   - Support global validation manager instance for consistent behavior across all components

3. **Testing Standards & Coverage Stabilization**
   - **Framework**: Use `pytest` exclusively with `pytest-mock` for all mocking (never `unittest.mock`)
   - **Test Organization**: Place tests under `tests/` directory with clear categorization:
     - `tests/unit/` - Fast, isolated unit tests (< 5 seconds execution)
     - `tests/integration/` - Integration tests with external services
     - `tests/fixtures/` - Reusable test data and mock responses
   - **Naming Convention**: `test_should_{behavior}_when_{condition}` for descriptive test names
   - **Test Data**: Use Faker library for dynamic, realistic test data generation
   - **Mock Strategy**: Mock all external dependencies (APIs, file system, LLM calls)
   - **Test Isolation**: Each test must run independently without shared state
   - **Coverage Requirements**: Maintain minimum 80% code coverage with focus on critical paths
   - **Execution Commands**:

     ```bash
     # Unit tests only (default)
     uv run pytest -m "not integration"

     # All tests including integration
     uv run pytest

     # Coverage measurement
     uv run pytest --cov=src/finwiz

     # Specific test categories
     uv run pytest tests/unit/crews/
     uv run pytest tests/integration/ -m integration
     ```

   - **Standardized Mocking**: Use centralized mock patterns and fixtures from `conftest.py`
   - **JSON Serialization**: Implement custom serializers for CrewAI objects (UsageMetrics, datetime)
   - **Error Handling**: Tests must provide clear failure messages with detailed context
   - **Performance**: Unit tests must complete in under 5 seconds per test suite
   - **CI Integration**: Ensure all tests pass in CI with proper environment setup

## Code Modernization Principles

### File Decomposition Strategy

The codebase has undergone systematic modernization to improve maintainability:

#### Target File Sizes

- **Under 200 lines**: Optimal for readability and maintainability
- **200-500 lines**: Acceptable for complex but focused modules
- **500+ lines**: Candidates for decomposition

#### Decomposition Patterns

- **Extract Calculations**: Move mathematical operations to dedicated calculation modules
- **Extract Formatting**: Separate presentation logic from business logic
- **Extract Utilities**: Common helper functions moved to utility modules
- **Extract Models**: Pydantic models and enums moved to dedicated model files
- **Extract Strategies**: Algorithm implementations moved to strategy modules

#### Scientific Package Optimization

- Replace manual calculations with pandas/numpy vectorized operations
- Use `pandas.Series.mean()` instead of manual `sum()/len()` calculations
- Leverage `pandas.groupby()` for aggregation operations
- Use `pandas.rolling()` for moving averages instead of manual loops
- Apply numpy broadcasting for efficient array operations

### Modernization Examples

#### Before: Monolithic File (1323 lines)

```python
# src/finwiz/quantitative/technical.py - Original monolithic file
class TechnicalAnalysis:
    def calculate_rsi(self): # 50+ lines
    def calculate_macd(self): # 40+ lines
    def calculate_bollinger_bands(self): # 60+ lines
    # ... 20+ more indicators

    class SignalType(Enum): # Models mixed with logic
    class SignalStrength(Enum):
    class TechnicalSignal(BaseModel):
```

#### After: Modular Structure

```python
# src/finwiz/quantitative/technical/technical_indicators.py (200 lines)
# TA-Lib wrapper functions only

# src/finwiz/quantitative/technical/technical_models.py (100 lines)  
# Pydantic models and enums only

# src/finwiz/quantitative/technical/basic_indicators.py (150 lines)
# Basic indicator implementations

# src/finwiz/quantitative/technical/advanced_indicators.py (180 lines)
# Advanced indicator implementations

# src/finwiz/quantitative/technical/engine.py (190 lines)
# Main technical analysis orchestration
```

## Implementation Examples

### Good Example - DRY Principle

```python
# Instead of repeating file processing logic:
def _process_files(self, file_list: List[str], file_type: str) -> None:
    """Process files of a specific type."""
    print(f"Indexing {file_type}")
    for file in file_list:
        print(Path(file).name)
        archive_files(file)

# Then use it in specific handlers:
def index_text(self):
    self._process_files(self.state.document_state.list_txt, "text")
```

### Good Example - KISS Principle

```python
# Simple, direct approach to file archiving
def archive_files(file: str) -> None:
    """Move processed files to an archive directory."""
    knowledge_dir = "knowledge"
    archive_dir = "archive"

    if not os.path.exists(knowledge_dir):
        return

    rel_path = os.path.relpath(file, knowledge_dir)
    dest_dir = os.path.join(archive_dir, os.path.dirname(rel_path))
    os.makedirs(dest_dir, exist_ok=True)

    dest_file = os.path.join(archive_dir, rel_path)
    shutil.move(file, dest_file)
```

### Good Example - Module Organization with Tool Factories

This project organizes tools by domain and uses factory functions to provide them to the crews. This keeps the crew definitions clean and separates tool implementation from tool consumption. **Recent modernization has further improved organization by extracting specialized components:**

```text
src/finwiz/tools/
├── __init__.py
├── finance_tools.py          # Factory functions for finance tools
├── web_tools.py              # Factory functions for web/search tools
├── yahoo_finance_tool.py     # Implementation of all Yahoo Finance tools
├── market_screening_tool.py  # Core screening logic (reduced from 1062 lines)
├── screening_criteria.py     # Extracted screening criteria
├── screening_utils.py        # Extracted screening utilities
├── screening_ranking.py      # Extracted ranking algorithms
├── enhanced_sentiment_tool.py # Core sentiment analysis (reduced from 822 lines)
├── sentiment_calculations.py # Extracted sentiment calculations
├── sentiment_sources.py      # Extracted data source integrations
├── rebalancing_report_generator.py # Core reporting (reduced from 1129 lines)
├── rebalancing_formatters.py # Extracted HTML formatting
├── rebalancing_calculations.py # Extracted calculations
└── rebalancing_templates.py  # Extracted template management
```

```python
# In a crew file (e.g., src/finwiz/crews/stock_crew/stock_crew.py)

# Import the factory function, not the individual tools
from finwiz.tools.finance_tools import get_stock_research_tools
from finwiz.tools.web_tools import get_search_tools, get_scrape_tools

# The crew can then easily be equipped with a curated set of tools
class StockCrew:
    def __init__(self):
        self.tools = [
            *get_search_tools(),
            *get_scrape_tools(),
            *get_stock_research_tools(),
        ]
        # ... setup agents and tasks with these tools
```

### Good Example - KISS and "Light as a Haiku" with Cohesive Tool Modules

Instead of splitting every single tool into its own file, related tools are grouped into a single, cohesive module. This reduces file clutter while still maintaining a clear separation of concerns.

```text
# src/finwiz/tools/yahoo_finance_tool.py

# All related Yahoo Finance tools are in one file
class YahooFinanceTickerInfoTool(BaseTool):
    # ... implementation

class YahooFinanceHistoryTool(BaseTool):
    # ... implementation

class YahooFinanceCompanyInfoTool(BaseTool):
    # ... implementation

# ... and so on.
```

This approach provides a clean, organized, and easy-to-maintain structure for managing the project's tools.

### Good Example - HTML Report Generation with Emojis

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PowerFlex Analysis Report</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        .emoji-header {
            font-size: 1.5em;
            margin-right: 10px;
        }
        .key-point {
            background-color: #f8f9fa;
            border-left: 4px solid #3498db;
            padding: 10px 15px;
            margin: 15px 0;
        }
        .toc {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <h1>🔍 PowerFlex Analysis Report</h1>
    <p><strong>Date:</strong> June 9, 2025</p>

    <div class="toc">
        <h2>📋 Table of Contents</h2>
        <ul>
            <li><a href="#summary">📊 Executive Summary</a></li>
            <li><a href="#benefits">🌟 Key Benefits</a></li>
            <li><a href="#use-cases">🛠️ Proven Use Cases</a></li>
            <li><a href="#conclusion">🏁 Conclusion</a></li>
        </ul>
    </div>

    <section id="summary">
        <h2><span class="emoji-header">📊</span>Executive Summary</h2>
        <p>This report addresses the question: <strong>"What are the top 5 reasons to buy PowerFlex? What are the proven benefits and use cases?"</strong></p>
        <!-- Report content continues... -->
    </section>
</body>
</html>
```
