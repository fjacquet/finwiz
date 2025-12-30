# Code Style and Conventions

## Python Version & Type Hints
- Python 3.12+ syntax
- Use `str | None` instead of `Optional[str]`
- Use `list[Type]` instead of `List[Type]`
- All public functions must have type hints
- Return types must be explicit

## Testing Standards
- **Framework**: pytest with pytest-mock
- **NEVER use unittest.mock** - strictly banned
- **Test Data**: Use Faker library
- **Coverage**: Minimum 65%

```python
# ❌ WRONG
from unittest.mock import Mock, patch

# ✅ CORRECT
def test_example(mocker):
    mock_obj = mocker.Mock()
    mocker.patch('module.function', return_value="result")
```

## Pydantic Models
- All crew outputs use Pydantic schemas
- Models go in `src/finwiz/schemas/`
- Use `extra='forbid'` (project standard)

## JSON Serialization
Always use `default=str` for datetime/numpy types:
```python
# ✅ CORRECT
json.dumps(data, default=str)
# Or use Pydantic
model.model_dump_json(indent=2)
```

## File Size Limits
- Hard limit: 300 lines per file
- Ideal target: 150-200 lines
- Minimum: 50 lines (avoid tiny files)

## CrewAI Patterns
- Use `@agent`, `@task`, `@crew` decorators
- Final reporters MUST have empty tools
- Use tool factories for tool assignment
- Set `max_reasoning_attempts=3` when reasoning enabled

## Logging
Use CrewLogger for consistent logging:
```python
from finwiz.utils.logging_helpers import CrewLogger
self.logger = CrewLogger("CrewName")
```
