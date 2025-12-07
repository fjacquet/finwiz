# Validation Module

This directory contains validation infrastructure for ensuring data quality, contract compliance, and runtime validation throughout the FinWiz platform.

## Directory Structure

```
validation/
├── __init__.py
├── ai_output_validator.py    # Validate AI/LLM outputs
├── contract_validator.py     # Contract/schema validation
├── data_flow_validator.py    # Data flow validation
├── manager.py                # Validation manager
├── registry.py               # Validator registry
├── report_validator.py       # Report validation
├── template_validator.py     # Template validation
├── tool_restrictions.py      # Tool usage restrictions
├── enums.py                  # Validation enums
└── result.py                 # ValidationResult class
```

## Major Entry Points

| File | Class | Purpose |
|------|-------|---------|
| `manager.py` | `ValidationManager` | Central validation coordination |
| `contract_validator.py` | `ContractValidator` | Validate against schemas |
| `ai_output_validator.py` | `AIOutputValidator` | Validate LLM outputs |
| `data_flow_validator.py` | `DataFlowValidator` | Validate data between steps |
| `report_validator.py` | `ReportValidator` | Validate generated reports |
| `template_validator.py` | `TemplateValidator` | Validate Jinja2 templates |
| `tool_restrictions.py` | `ToolRestrictions` | Enforce tool usage rules |
| `result.py` | `ValidationResult` | Validation result container |

## Usage

### ValidationManager

```python
from finwiz.validation.manager import ValidationManager

manager = ValidationManager()

# Register validators
manager.register("contract", ContractValidator())
manager.register("ai_output", AIOutputValidator())

# Validate data
result = manager.validate_all(data, context="crew_output")

if not result.is_valid:
    for error in result.errors:
        print(f"Error: {error.message}")
```

### ContractValidator

```python
from finwiz.validation.contract_validator import ContractValidator
from finwiz.schemas.crew_exports import StockCrewExport

validator = ContractValidator()

# Validate against Pydantic schema
result = validator.validate(
    data=crew_output,
    schema=StockCrewExport
)

if result.is_valid:
    validated_export = result.validated_data
else:
    print(f"Validation failed: {result.errors}")
```

### AIOutputValidator

```python
from finwiz.validation.ai_output_validator import AIOutputValidator

validator = AIOutputValidator()

# Validate LLM output for expected structure
result = validator.validate(
    output=llm_response,
    expected_format="json",
    required_fields=["ticker", "score", "recommendation"]
)

if result.has_warnings:
    for warning in result.warnings:
        print(f"Warning: {warning}")
```

### DataFlowValidator

```python
from finwiz.validation.data_flow_validator import DataFlowValidator

validator = DataFlowValidator()

# Validate data between pipeline stages
result = validator.validate_transition(
    source_data=stock_crew_output,
    target_schema=ReportInputSchema,
    stage="crew_to_report"
)
```

### ToolRestrictions

```python
from finwiz.validation.tool_restrictions import ToolRestrictions

restrictions = ToolRestrictions()

# Check if agent can use tool
if restrictions.can_use_tool(agent_name="reporter", tool_name="search"):
    # Not allowed - reporters must have empty tools
    raise ValidationError("Reporters cannot use tools")

# Get allowed tools for agent
allowed = restrictions.get_allowed_tools("analyst")
```

## ValidationResult

```python
from finwiz.validation.result import ValidationResult, ValidationError

# Create result
result = ValidationResult(
    is_valid=True,
    validated_data=clean_data,
    errors=[],
    warnings=["Field 'optional_field' was missing"]
)

# Add errors
result.add_error(ValidationError(
    field="ticker",
    message="Invalid ticker format",
    severity="error",
    code="INVALID_TICKER"
))

# Check result
if result.is_valid:
    process(result.validated_data)
else:
    for error in result.errors:
        log_error(error)
```

## Validation Strictness

Configure via environment:

```bash
VALIDATION_STRICTNESS=warn  # off/warn/error

# off:   Skip validation (development only)
# warn:  Log warnings but continue
# error: Raise exceptions on validation failure
```

## Custom Validators

```python
from finwiz.validation.registry import ValidatorRegistry

class MyCustomValidator:
    def validate(self, data: dict, context: str) -> ValidationResult:
        errors = []

        if not data.get("required_field"):
            errors.append(ValidationError(
                field="required_field",
                message="Missing required field"
            ))

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )

# Register
registry = ValidatorRegistry()
registry.register("my_validator", MyCustomValidator())
```

## Testing

```bash
# Test all validation
uv run pytest tests/unit/validation/ -v

# Test specific validator
uv run pytest tests/unit/validation/test_contract_validator.py -v

# Test with strictness
VALIDATION_STRICTNESS=error uv run pytest tests/unit/validation/ -v
```

## Related Modules

- `finwiz.schemas` - Pydantic schemas for validation
- `finwiz.integration.validation_*` - Integration validation
- `finwiz.utils.agent_validators` - Agent validation decorators
- `finwiz.utils.json_repair` - JSON repair before validation
