# FinWiz Codebase Improvement Specification

**Date:** 2025-10-02  
**Author:** Senior CrewAI & Python Architecture Specialist  
**Status:** 🎯 Proposed for Implementation  
**Version:** 1.0

---

## Executive Summary

This specification outlines a comprehensive set of improvements for the FinWiz codebase, focusing on **CrewAI best practices**, **architectural excellence**, and **maintainability**. All recommendations respect the project's core philosophy: "Light as a Haiku" with KISS, YAGNI, and configuration-driven design.

### Key Metrics

| Metric | Current | Target | Impact |
|--------|---------|--------|--------|
| Largest File | 764 lines | <400 lines | 🟢 Maintainability |
| Tool Factories | Partial | Complete | 🟢 Consistency |
| Schema Validation | Partial | 100% | 🟢 Reliability |
| Test Coverage | ~7% | >65% | 🔴 Critical |
| Async Patterns | Inconsistent | Standardized | 🟢 Performance |
| CrewAI Compliance | 85% | 100% | 🟢 Best Practices |

---

## 🎯 Priority 1: Critical Architectural Improvements

### 1.1 File Size Reduction (High Priority)

**Issue:** Several files exceed the 200-line guideline, with `main.py` at 764 lines.

**Files Requiring Decomposition:**

```
Priority Files (>600 lines):
├── main.py (764 lines) → Split into:
│   ├── main.py (core flow, <200 lines)
│   ├── flow_orchestration.py (flow methods)
│   ├── crew_execution.py (crew kickoff logic)
│   └── flow_validation.py (validation methods)
│
├── integration/manager.py (711 lines) → Split into:
│   ├── manager.py (core manager, <200 lines)
│   ├── data_consolidation.py (consolidation logic)
│   ├── crew_integration.py (crew-specific integration)
│   └── integration_helpers.py (utility functions)
│
├── integration/validation_error_recovery.py (704 lines) → Split into:
│   ├── validation_error_recovery.py (core recovery, <200 lines)
│   ├── recovery_strategies.py (recovery strategies)
│   ├── error_classification.py (error classification)
│   └── recovery_handlers.py (specific handlers)
│
└── quantitative/optimization.py (689 lines) → Split into:
    ├── optimization.py (core optimization, <200 lines)
    ├── optimization_strategies.py (strategy implementations)
    ├── optimization_constraints.py (constraint handling)
    └── optimization_solvers.py (solver implementations)
```

**Implementation Plan:**

```python
# Example: main.py refactoring

# NEW: src/finwiz/flow_orchestration.py
class FlowOrchestrator:
    """Handles flow method orchestration."""
    
    def __init__(self, integration_manager, error_handler, state_manager):
        self.integration_manager = integration_manager
        self.error_handler = error_handler
        self.state_manager = state_manager
    
    def execute_crypto_flow(self, inputs: dict) -> dict:
        """Execute crypto crew flow."""
        pass
    
    def execute_stock_flow(self, inputs: dict) -> dict:
        """Execute stock crew flow."""
        pass
    
    def execute_etf_flow(self, inputs: dict) -> dict:
        """Execute ETF crew flow."""
        pass

# UPDATED: src/finwiz/main.py (reduced to <200 lines)
class FinwizFlow(Flow[FinwizState]):
    """Orchestrates the financial analysis workflow."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orchestrator = FlowOrchestrator(...)
        self.validator = FlowValidator(...)
    
    @start()
    def validate_data_integration(self):
        """Validate data integration system."""
        return self.validator.validate_integration()
    
    @listen("validate_data_integration")
    def check_crypto(self):
        """Initiate cryptocurrency analysis."""
        return self.orchestrator.execute_crypto_flow(self.inputs)
```

**Benefits:**
- ✅ Improved maintainability
- ✅ Better testability
- ✅ Easier code navigation
- ✅ Reduced cognitive load

---

### 1.2 Tool Factory Standardization (High Priority)

**Issue:** Inconsistent tool initialization patterns across crews.

**Current State:**
```python
# ❌ Inconsistent: Some crews initialize tools inline
search_tool = get_web_search_tool(n_results=10)
scrape_tool = FirecrawlScrapeWebsiteTool()
yahoo_ticker_tool = YahooFinanceTickerInfoTool()
# ... scattered initialization
```

**Proposed Standard:**

```python
# NEW: src/finwiz/tools/tool_factories.py

from typing import Protocol
from crewai.tools import BaseTool

class ToolFactory(Protocol):
    """Protocol for tool factory functions."""
    
    def __call__(self, **kwargs) -> list[BaseTool]:
        """Return list of configured tools."""
        ...

def get_stock_crew_tools(
    include_rag: bool = True,
    include_quantitative: bool = True,
    collection_suffix: str = "stock"
) -> list[BaseTool]:
    """
    Get standardized tool set for Stock Crew.
    
    Args:
        include_rag: Include RAG tools for knowledge retrieval
        include_quantitative: Include quantitative analysis tool
        collection_suffix: RAG collection suffix
    
    Returns:
        List of configured tools for stock analysis
    """
    tools = []
    
    # Core research tools
    tools.extend(get_stock_research_tools())
    
    # Optional quantitative tools
    if include_quantitative:
        tools.append(get_quantitative_analysis_tool())
    
    # Optional RAG tools
    if include_rag:
        tools.extend(get_rag_tools(collection_suffix=collection_suffix))
    
    # Schema and contract tools
    tools.extend([
        DirectoryReadTool(directory="output/stock"),
        DirectoryReadTool(directory="docs/schemas"),
        FileReadTool(file_path="docs/schemas/MarketSentiment.schema.json"),
        FileReadTool(file_path="docs/schemas/TenKInsight.schema.json"),
    ])
    
    return tools

def get_crypto_crew_tools(
    include_rag: bool = True,
    include_quantitative: bool = True,
    collection_suffix: str = "crypto"
) -> list[BaseTool]:
    """Get standardized tool set for Crypto Crew."""
    # Similar pattern...
    pass

def get_etf_crew_tools(
    include_rag: bool = True,
    include_quantitative: bool = True,
    collection_suffix: str = "etf"
) -> list[BaseTool]:
    """Get standardized tool set for ETF Crew."""
    # Similar pattern...
    pass

def get_report_crew_tools(
    include_rag: bool = True,
    data_availability: dict | None = None
) -> list[BaseTool]:
    """
    Get standardized tool set for Report Crew.
    
    Note: Report crew tools are for reading context only, never for external research.
    """
    tools = []
    
    if include_rag:
        tools.extend(get_rag_tools(collection_suffix="report"))
    
    # Add directory tools based on data availability
    if data_availability:
        if data_availability.get("stock_available"):
            tools.append(DirectoryReadTool(directory="output/stock"))
        if data_availability.get("etf_available"):
            tools.append(DirectoryReadTool(directory="output/etf"))
        if data_availability.get("crypto_available"):
            tools.append(DirectoryReadTool(directory="output/crypto"))
    
    return tools
```

**Updated Crew Implementation:**

```python
# UPDATED: src/finwiz/crews/stock_crew/stock_crew.py

from finwiz.tools.tool_factories import get_stock_crew_tools

# Clean, standardized tool initialization
tools = get_stock_crew_tools(
    include_rag=True,
    include_quantitative=True,
    collection_suffix="stock"
)

@CrewBase
class StockCrew:
    """StockCrew with standardized tool factory."""
    
    @agent
    def market_technical_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["market_technical_analyst"],
            tools=tools,  # Standardized tools
            llm=self._get_configured_llm(),
        )
```

**Benefits:**
- ✅ Consistent tool initialization across all crews
- ✅ Centralized tool configuration
- ✅ Easier testing and mocking
- ✅ Better dependency management

---

### 1.3 Schema Validation Enhancement (Critical Priority)

**Issue:** Inconsistent schema validation and missing Pydantic models for some outputs.

**Current Gaps:**
1. Not all task outputs use `output_pydantic`
2. Some crews lack schema validation
3. Missing validation at crew boundaries

**Proposed Solution:**

```python
# NEW: src/finwiz/schemas/validation_decorators.py

from functools import wraps
from typing import Any, Callable, TypeVar
from pydantic import BaseModel, ValidationError
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T', bound=BaseModel)

def validate_task_output(schema: type[T]) -> Callable:
    """
    Decorator to validate task output against Pydantic schema.
    
    Usage:
        @validate_task_output(MarketSentiment)
        @task
        def stock_screening_task(self) -> Task:
            return Task(...)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            task = func(*args, **kwargs)
            
            # Add validation callback
            original_callback = task.callback
            
            def validated_callback(output: Any) -> Any:
                try:
                    # Validate output
                    if isinstance(output, dict):
                        validated = schema(**output)
                    elif isinstance(output, str):
                        import json
                        validated = schema(**json.loads(output))
                    else:
                        validated = output
                    
                    logger.info(f"Task output validated against {schema.__name__}")
                    
                    # Call original callback if exists
                    if original_callback:
                        return original_callback(validated)
                    return validated
                    
                except ValidationError as e:
                    logger.error(f"Task output validation failed: {e}")
                    raise
            
            task.callback = validated_callback
            return task
        
        return wrapper
    return decorator

def validate_crew_input(schema: type[T]) -> Callable:
    """Decorator to validate crew input."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, inputs: dict, *args, **kwargs) -> Any:
            try:
                validated_inputs = schema(**inputs)
                logger.info(f"Crew input validated against {schema.__name__}")
                return func(self, validated_inputs.model_dump(), *args, **kwargs)
            except ValidationError as e:
                logger.error(f"Crew input validation failed: {e}")
                raise
        return wrapper
    return decorator
```

**Usage in Crews:**

```python
# UPDATED: src/finwiz/crews/stock_crew/stock_crew.py

from finwiz.schemas.validation_decorators import validate_task_output, validate_crew_input
from finwiz.schemas.stock import StockCrewInput

class StockCrew:
    
    @validate_task_output(MarketSentiment)
    @task
    def stock_screening_task(self) -> Task:
        """Screen stocks with validated output."""
        return Task(
            config=self.tasks_config["stock_screening_task"],
            output_pydantic=MarketSentiment,  # Explicit schema
        )
    
    @validate_task_output(TenKInsight)
    @task
    def technical_detail_task(self) -> Task:
        """Technical analysis with validated output."""
        return Task(
            config=self.tasks_config["technical_detail_task"],
            output_pydantic=TenKInsight,  # Explicit schema
        )
    
    @validate_crew_input(StockCrewInput)
    def kickoff(self, inputs: dict) -> Any:
        """Execute crew with validated inputs."""
        return super().kickoff(inputs)
```

**Benefits:**
- ✅ Guaranteed schema compliance
- ✅ Early error detection
- ✅ Better debugging
- ✅ Improved data quality

---

## 🚀 Priority 2: CrewAI Best Practices

### 2.1 Async Execution Standardization

**Issue:** Inconsistent async execution patterns across tasks.

**Current State:**
```python
# ❌ Inconsistent async usage
@task
def task_a(self) -> Task:
    return Task(..., async_execution=True)  # ✅ Good

@task
def task_b(self) -> Task:
    return Task(...)  # ❌ Missing async flag

@task
def final_task(self) -> Task:
    return Task(..., async_execution=True)  # ❌ Final task must be sync!
```

**Proposed Standard:**

```python
# NEW: src/finwiz/utils/task_decorators.py

from functools import wraps
from typing import Callable
from crewai import Task

def async_task(func: Callable) -> Callable:
    """
    Decorator for async tasks.
    
    Automatically sets async_execution=True and adds logging.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Task:
        task = func(*args, **kwargs)
        task.async_execution = True
        logger.debug(f"Task {func.__name__} configured for async execution")
        return task
    return wrapper

def sync_task(func: Callable) -> Callable:
    """
    Decorator for synchronous tasks.
    
    Explicitly marks tasks as synchronous (for final tasks).
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Task:
        task = func(*args, **kwargs)
        task.async_execution = False
        logger.debug(f"Task {func.__name__} configured for sync execution")
        return task
    return wrapper
```

**Usage:**

```python
# UPDATED: src/finwiz/crews/stock_crew/stock_crew.py

from finwiz.utils.task_decorators import async_task, sync_task

class StockCrew:
    
    @async_task
    @task
    def market_technical_analysis_task(self) -> Task:
        """Async technical analysis."""
        return Task(config=self.tasks_config["market_technical_analysis_task"])
    
    @async_task
    @task
    def stock_screening_task(self) -> Task:
        """Async screening."""
        return Task(config=self.tasks_config["stock_screening_task"])
    
    @sync_task  # Final task must be synchronous
    @task
    def stock_risk_assessment_task(self) -> Task:
        """Final sync risk assessment."""
        return Task(config=self.tasks_config["stock_risk_assessment_task"])
```

**Benefits:**
- ✅ Clear async/sync distinction
- ✅ Prevents final task async errors
- ✅ Better performance tracking
- ✅ Consistent execution patterns

---

### 2.2 Final Reporter Tool Enforcement

**Issue:** Need to ensure final reporters NEVER have tools.

**Current State:**
```python
# ✅ Good: Report crew already enforces this
@agent
def investment_reporter(self) -> Agent:
    return Agent(
        config=self.agents_config["investment_reporter"],
        tools=[],  # ✅ Correct: No tools
    )

# ❌ Risk: Other crews might add tools to final reporters
```

**Proposed Enforcement:**

```python
# NEW: src/finwiz/utils/agent_validators.py

from crewai import Agent
from typing import Callable
from functools import wraps

class FinalReporterError(Exception):
    """Raised when final reporter has tools."""
    pass

def final_reporter(func: Callable) -> Callable:
    """
    Decorator to enforce final reporter has no tools.
    
    Usage:
        @final_reporter
        @agent
        def investment_reporter(self) -> Agent:
            return Agent(...)
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Agent:
        agent = func(*args, **kwargs)
        
        if agent.tools and len(agent.tools) > 0:
            raise FinalReporterError(
                f"Final reporter '{agent.role}' must have NO tools. "
                f"Found {len(agent.tools)} tools. "
                "Final reporters should only consume upstream context."
            )
        
        logger.info(f"Final reporter '{agent.role}' validated: no tools ✓")
        return agent
    
    return wrapper
```

**Usage:**

```python
# UPDATED: All crews with final reporters

from finwiz.utils.agent_validators import final_reporter

class ReportCrew:
    
    @final_reporter  # Enforces no tools
    @agent
    def investment_reporter(self) -> Agent:
        return Agent(
            config=self.agents_config["investment_reporter"],
            tools=[],  # Will raise error if tools are added
        )
    
    @final_reporter  # Enforces no tools
    @agent
    def translator(self) -> Agent:
        return Agent(
            config=self.agents_config["translator"],
            tools=[],  # Will raise error if tools are added
        )
```

**Benefits:**
- ✅ Compile-time enforcement
- ✅ Prevents accidental tool addition
- ✅ Clear error messages
- ✅ Maintains FinWiz principles

---

## 🧪 Priority 3: Testing Infrastructure

### 3.1 Test Coverage Improvement (Critical)

**Current State:** ~7% coverage (CRITICAL)  
**Target:** >65% coverage

**Proposed Testing Strategy:**

```python
# NEW: tests/unit/crews/test_stock_crew.py

import pytest
from unittest.mock import MagicMock
from finwiz.crews.stock_crew.stock_crew import StockCrew
from finwiz.schemas.stock import MarketSentiment, TenKInsight

class TestStockCrew:
    """Unit tests for Stock Crew."""
    
    @pytest.fixture
    def stock_crew(self):
        """Create stock crew instance."""
        return StockCrew()
    
    def test_should_initialize_crew_with_correct_agents(self, stock_crew):
        """Test crew initialization."""
        crew = stock_crew.crew()
        
        assert len(crew.agents) > 0
        assert any(agent.role == "Market Technical Analyst" for agent in crew.agents)
    
    def test_should_create_market_analyst_with_tools(self, stock_crew):
        """Test market analyst has required tools."""
        agent = stock_crew.market_technical_analyst()
        
        assert agent is not None
        assert len(agent.tools) > 0
        assert agent.verbose is True
    
    def test_should_validate_task_output_schemas(self, stock_crew):
        """Test tasks have correct output schemas."""
        screening_task = stock_crew.stock_screening_task()
        
        assert screening_task.output_pydantic == MarketSentiment
    
    def test_should_have_final_task_synchronous(self, stock_crew):
        """Test final task is synchronous."""
        risk_task = stock_crew.stock_risk_assessment_task()
        
        # Final task must be synchronous
        assert risk_task.async_execution is False or risk_task.async_execution is None
    
    def test_should_execute_crew_with_valid_inputs(self, stock_crew, mocker):
        """Test crew execution with mocked LLM."""
        # Mock LLM to avoid actual API calls
        mock_llm = mocker.patch('finwiz.utils.llm_config.get_configured_llm')
        mock_llm.return_value = MagicMock()
        
        # Mock crew execution
        mock_kickoff = mocker.patch.object(stock_crew.crew(), 'kickoff')
        mock_kickoff.return_value = {"result": "success"}
        
        result = stock_crew.crew().kickoff(inputs={"ticker": "AAPL"})
        
        assert result is not None
        mock_kickoff.assert_called_once()


# NEW: tests/unit/tools/test_tool_factories.py

import pytest
from finwiz.tools.tool_factories import (
    get_stock_crew_tools,
    get_crypto_crew_tools,
    get_etf_crew_tools
)

class TestToolFactories:
    """Unit tests for tool factories."""
    
    def test_should_return_stock_tools_with_rag(self):
        """Test stock tool factory includes RAG tools."""
        tools = get_stock_crew_tools(include_rag=True)
        
        assert len(tools) > 0
        # Check for Knowledge base tool
        assert any(tool.name == "Knowledge base" for tool in tools)
    
    def test_should_return_stock_tools_without_rag(self):
        """Test stock tool factory excludes RAG tools."""
        tools = get_stock_crew_tools(include_rag=False)
        
        # Should not have Knowledge base tool
        assert not any(tool.name == "Knowledge base" for tool in tools)
    
    def test_should_return_consistent_tool_count(self):
        """Test tool factories return consistent counts."""
        stock_tools = get_stock_crew_tools()
        crypto_tools = get_crypto_crew_tools()
        
        # All crews should have similar tool counts (within reason)
        assert len(stock_tools) > 5
        assert len(crypto_tools) > 5


# NEW: tests/integration/test_crew_execution.py

import pytest
from finwiz.crews.stock_crew.stock_crew import StockCrew

@pytest.mark.integration
class TestCrewExecution:
    """Integration tests for crew execution."""
    
    def test_should_execute_stock_crew_end_to_end(self, mocker):
        """Test full stock crew execution."""
        # This would use real LLM calls (marked as integration)
        crew = StockCrew()
        
        # Mock external API calls but use real LLM
        mocker.patch('finwiz.tools.yahoo_finance_ticker_info_tool.YahooFinanceTickerInfoTool')
        
        result = crew.crew().kickoff(inputs={"ticker": "AAPL"})
        
        assert result is not None
```

**Test Coverage Targets:**

| Component | Current | Target | Priority |
|-----------|---------|--------|----------|
| Crews | ~5% | 80% | 🔴 Critical |
| Tools | ~10% | 70% | 🔴 Critical |
| Schemas | ~15% | 90% | 🟡 High |
| Integration | ~5% | 60% | 🟡 High |
| Utils | ~20% | 75% | 🟢 Medium |

---

## 📊 Priority 4: Code Quality Improvements

### 4.1 Type Hints Standardization

**Issue:** Inconsistent type hints across codebase.

**Proposed Standard:**

```python
# NEW: .mypy.ini (add to project root)
[mypy]
python_version = 3.10
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_calls = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_optional = True

[mypy-crewai.*]
ignore_missing_imports = True

[mypy-crewai_tools.*]
ignore_missing_imports = True
```

**Example Improvements:**

```python
# BEFORE: Weak typing
def get_tools():
    return [...]

def process_data(data):
    return data

# AFTER: Strong typing
from typing import Any
from crewai.tools import BaseTool

def get_tools() -> list[BaseTool]:
    """Get configured tools for crew."""
    return [...]

def process_data(data: dict[str, Any]) -> dict[str, Any]:
    """Process and validate data."""
    return data
```

---

### 4.2 Logging Standardization

**Issue:** Inconsistent logging patterns.

**Proposed Standard:**

```python
# NEW: src/finwiz/utils/logging_standards.py

from typing import Any
from finwiz.tools.logger import get_logger

class StructuredLogger:
    """Standardized structured logging."""
    
    def __init__(self, name: str):
        self.logger = get_logger(name)
    
    def log_crew_start(self, crew_name: str, inputs: dict[str, Any]) -> None:
        """Log crew execution start."""
        self.logger.info(
            f"Starting {crew_name} execution",
            extra={
                "crew": crew_name,
                "input_keys": list(inputs.keys()),
                "event": "crew_start"
            }
        )
    
    def log_crew_complete(self, crew_name: str, duration: float) -> None:
        """Log crew execution completion."""
        self.logger.info(
            f"{crew_name} execution completed",
            extra={
                "crew": crew_name,
                "duration_seconds": duration,
                "event": "crew_complete"
            }
        )
    
    def log_task_start(self, task_name: str, agent_role: str) -> None:
        """Log task execution start."""
        self.logger.info(
            f"Starting task: {task_name}",
            extra={
                "task": task_name,
                "agent": agent_role,
                "event": "task_start"
            }
        )
    
    def log_validation_error(self, schema: str, errors: list[str]) -> None:
        """Log validation errors."""
        self.logger.error(
            f"Validation failed for {schema}",
            extra={
                "schema": schema,
                "error_count": len(errors),
                "errors": errors,
                "event": "validation_error"
            }
        )
```

**Usage:**

```python
# UPDATED: All crews

from finwiz.utils.logging_standards import StructuredLogger

class StockCrew:
    def __init__(self):
        self.logger = StructuredLogger(__name__)
        super().__init__()
    
    def kickoff(self, inputs: dict) -> Any:
        """Execute crew with structured logging."""
        import time
        
        self.logger.log_crew_start("StockCrew", inputs)
        start_time = time.time()
        
        try:
            result = super().kickoff(inputs)
            duration = time.time() - start_time
            self.logger.log_crew_complete("StockCrew", duration)
            return result
        except Exception as e:
            self.logger.logger.error(f"StockCrew execution failed: {e}", exc_info=True)
            raise
```

---

## 🔧 Priority 5: Configuration Management

### 5.1 Centralized Configuration

**Issue:** Configuration scattered across multiple files.

**Proposed Solution:**

```python
# NEW: src/finwiz/config/crew_config.py

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import yaml

@dataclass
class CrewConfiguration:
    """Centralized crew configuration."""
    
    name: str
    agents_config: dict[str, Any]
    tasks_config: dict[str, Any]
    tools_config: dict[str, Any]
    
    @classmethod
    def load(cls, crew_name: str) -> "CrewConfiguration":
        """
        Load crew configuration from YAML files.
        
        Args:
            crew_name: Name of the crew (e.g., "stock", "crypto", "etf")
        
        Returns:
            CrewConfiguration instance
        """
        crew_dir = Path(__file__).parent.parent / "crews" / f"{crew_name}_crew"
        
        with open(crew_dir / "config" / "agents.yaml") as f:
            agents_config = yaml.safe_load(f)
        
        with open(crew_dir / "config" / "tasks.yaml") as f:
            tasks_config = yaml.safe_load(f)
        
        # Load tools configuration if exists
        tools_config_path = crew_dir / "config" / "tools.yaml"
        if tools_config_path.exists():
            with open(tools_config_path) as f:
                tools_config = yaml.safe_load(f)
        else:
            tools_config = {}
        
        return cls(
            name=crew_name,
            agents_config=agents_config,
            tasks_config=tasks_config,
            tools_config=tools_config
        )

# NEW: src/finwiz/crews/{crew}_crew/config/tools.yaml
# Example: stock_crew/config/tools.yaml

tools:
  include_rag: true
  include_quantitative: true
  rag_collection_suffix: "stock"
  
  custom_tools:
    - yahoo_finance_ticker_info
    - yahoo_finance_history
    - yahoo_finance_news
    - yahoo_finance_company_info
  
  schema_files:
    - "docs/schemas/MarketSentiment.schema.json"
    - "docs/schemas/TenKInsight.schema.json"
    - "docs/schemas/RiskAssessmentStandardized.schema.json"
```

**Usage:**

```python
# UPDATED: src/finwiz/crews/stock_crew/stock_crew.py

from finwiz.config.crew_config import CrewConfiguration

@CrewBase
class StockCrew:
    """Stock crew with centralized configuration."""
    
    def __init__(self):
        # Load configuration
        self.config = CrewConfiguration.load("stock")
        
        # Set configs for CrewAI
        self.agents_config = self.config.agents_config
        self.tasks_config = self.config.tasks_config
        
        super().__init__()
        
        # Initialize tools from configuration
        self.tools = self._initialize_tools()
    
    def _initialize_tools(self) -> list[BaseTool]:
        """Initialize tools from configuration."""
        from finwiz.tools.tool_factories import get_stock_crew_tools
        
        return get_stock_crew_tools(
            include_rag=self.config.tools_config.get("include_rag", True),
            include_quantitative=self.config.tools_config.get("include_quantitative", True),
            collection_suffix=self.config.tools_config.get("rag_collection_suffix", "stock")
        )
```

---

## 📈 Priority 6: Performance Optimizations

### 6.1 Caching Strategy Enhancement

**Proposed Enhancement:**

```python
# NEW: src/finwiz/utils/crew_cache.py

from functools import wraps
from typing import Any, Callable
import hashlib
import json
from pathlib import Path

class CrewResultCache:
    """Cache for crew execution results."""
    
    def __init__(self, cache_dir: Path = Path("storage/crew_cache")):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, crew_name: str, inputs: dict) -> str:
        """Generate cache key from crew name and inputs."""
        input_str = json.dumps(inputs, sort_keys=True)
        return hashlib.sha256(f"{crew_name}:{input_str}".encode()).hexdigest()
    
    def get(self, crew_name: str, inputs: dict, max_age_hours: int = 24) -> Any | None:
        """Get cached result if available and fresh."""
        cache_key = self._get_cache_key(crew_name, inputs)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
        
        # Check age
        import time
        file_age_hours = (time.time() - cache_file.stat().st_mtime) / 3600
        if file_age_hours > max_age_hours:
            return None
        
        with open(cache_file) as f:
            return json.load(f)
    
    def set(self, crew_name: str, inputs: dict, result: Any) -> None:
        """Cache crew result."""
        cache_key = self._get_cache_key(crew_name, inputs)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        with open(cache_file, 'w') as f:
            json.dump(result, f, indent=2)

def cached_crew_execution(max_age_hours: int = 24):
    """Decorator for caching crew execution results."""
    def decorator(func: Callable) -> Callable:
        cache = CrewResultCache()
        
        @wraps(func)
        def wrapper(self, inputs: dict, *args, **kwargs) -> Any:
            crew_name = self.__class__.__name__
            
            # Try to get from cache
            cached_result = cache.get(crew_name, inputs, max_age_hours)
            if cached_result:
                logger.info(f"Using cached result for {crew_name}")
                return cached_result
            
            # Execute and cache
            result = func(self, inputs, *args, **kwargs)
            cache.set(crew_name, inputs, result)
            
            return result
        
        return wrapper
    return decorator
```

---

## 🎯 Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)
- ✅ Implement tool factory standardization
- ✅ Add schema validation decorators
- ✅ Create async/sync task decorators
- ✅ Implement final reporter enforcement

### Phase 2: Testing (Weeks 3-4)
- ✅ Set up test infrastructure
- ✅ Write unit tests for all crews
- ✅ Write unit tests for all tools
- ✅ Achieve 40% coverage milestone

### Phase 3: Refactoring (Weeks 5-6)
- ✅ Decompose large files (main.py, manager.py, etc.)
- ✅ Standardize logging
- ✅ Implement centralized configuration
- ✅ Add type hints

### Phase 4: Optimization (Weeks 7-8)
- ✅ Implement caching enhancements
- ✅ Optimize async execution
- ✅ Performance profiling
- ✅ Achieve 65% coverage target

### Phase 5: Documentation (Week 9)
- ✅ Update all documentation
- ✅ Create migration guides
- ✅ Update examples
- ✅ Final review

---

## 📋 Success Criteria

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Test Coverage | >65% | `uv run pytest --cov` |
| File Size | <400 lines max | `wc -l` on all files |
| Type Coverage | >90% | `mypy src/` |
| CrewAI Compliance | 100% | Manual checklist |
| Performance | <10% regression | Benchmark suite |
| Documentation | 100% coverage | Manual review |

---

## 🚨 Breaking Changes

**None.** All improvements are designed to be **backward compatible** with existing functionality.

---

## 📚 References

- [CrewAI Documentation](https://docs.crewai.com/)
- [Pydantic V2 Documentation](https://docs.pydantic.dev/latest/)
- [FinWiz Design Principles](./DESIGN_PRINCIPLES.md)
- [FinWiz Agent Handbook](./agent_handbook.md)
- [CrewAI Spirit Guide](./crewai_spirit.md)

---

## 🤝 Contributing

All improvements should:
1. Follow the "Light as a Haiku" philosophy
2. Maintain KISS and YAGNI principles
3. Be configuration-driven where possible
4. Include comprehensive tests
5. Update relevant documentation

---

**End of Specification**

*This document represents a comprehensive improvement plan for the FinWiz codebase, respecting its core philosophy while enhancing maintainability, reliability, and CrewAI compliance.*
