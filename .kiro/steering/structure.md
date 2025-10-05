---
inclusion: always
---

# FinWiz Code Structure Guide

## Project Layout

```
src/finwiz/
├── crews/           # AI agent crews (crypto, stock, etf, report)
├── tools/           # Domain-specific analysis tools
├── schemas/         # Pydantic models with strict validation
├── orchestrators/   # Flow coordination logic
├── templates/       # HTML report templates
└── main.py         # CrewAI Flow entry point

docs/schemas/        # JSON schemas with examples
tests/              # Test suite with pytest
```

## CrewAI Patterns

### Crew Structure (Required)

```python
# crews/{name}/{name}.py
from crewai import Agent, Task, Crew
from crewai.flow import flow, start, listen

class {Name}Crew:
    @agent
    def researcher(self) -> Agent:
        return Agent(config=self.agents_config['researcher'])
    
    @task
    def research_task(self) -> Task:
        return Task(config=self.tasks_config['research'])
    
    @crew
    def crew(self) -> Crew:
        return Crew(agents=[self.researcher()], tasks=[self.research_task()])
```

### Configuration Files (Required)

- `config/agents.yaml` - Agent definitions with roles, goals, backstories
- `config/tasks.yaml` - Task definitions with descriptions and expected outputs

### Schema Validation (Required)

```python
# All crew outputs must use Pydantic models
from pydantic import BaseModel, Field

class AnalysisResult(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol")
    recommendation: str = Field(..., pattern="^(BUY|HOLD|SELL)$")
    confidence: float = Field(..., ge=0.0, le=1.0)
```

## Tool Development

### Tool Factory Pattern

```python
# tools/{domain}_tools.py
def get_{domain}_tools() -> list:
    """Return curated tool set for domain analysis."""
    return [tool1(), tool2(), tool3()]
```

### External API Integration

- Always implement retry logic with exponential backoff
- Mock all external calls in tests using pytest-mock
- Handle rate limits and API errors gracefully
- Cache expensive operations when appropriate

## Import Standards

```python
# Standard library
import asyncio
from typing import Dict, List, Optional

# Third-party
from crewai import Agent, Task
from pydantic import BaseModel

# Local imports
from finwiz.schemas.common import BaseAnalysis
from finwiz.tools.finance_tools import get_market_data
```

## File Organization Rules

- **One class per file** for crews and major components
- **Group related functions** in tool modules
- **Separate concerns**: data models, business logic, external integrations
- **Use descriptive names**: `yahoo_finance_ticker_info_tool.py` not `yf_tool.py`
