# Validation Module

Data quality, contract compliance, and runtime validation for the FinWiz platform.

## Directory Structure

```
validation/
├── __init__.py              # Exports: ValidationManager, SchemaRegistry, ContractValidator, etc.
├── manager.py               # ValidationManager, get_validation_manager()
├── int_manager.py           # Alternative ValidationManager (integration-focused)
├── registry.py              # SchemaRegistry, get_registry()
├── contract.py              # ContractValidator
├── enums.py                 # ValidationMode, Strictness
├── result.py                # ValidationResult, ValidationError, ValidationWarning
├── ai_output.py             # validate_ai_output_structure(), validate_qualitative_insights()
├── template.py              # TemplateVariableValidator, validate_template_variables_at_startup()
├── quality_metrics.py       # Data quality metrics
└── url.py                   # URL validation
```

Ten orphaned modules — `rules.py`, `pipeline_stages.py`, `tool_restrictions.py`,
`int_pipeline.py`, `freshness.py`, `consolidation.py`, `report.py`,
`report_data.py`, `sec_citation.py`, `scripts.py` — were deleted as unreachable
from any entry point
([#200](https://github.com/fjacquet/finwiz/issues/200)). Two of them,
`consolidation.py` (`DataConsolidationValidator`) and `report_data.py`
(`ReportDataValidator`), had already stopped running silently in `4600d1a7`
(November 2025); see [#202](https://github.com/fjacquet/finwiz/issues/202)
for whether either should be reinstated. `schemas/report.py` (`ReporterInput`)
is a different, unrelated, and still-live module.

## Entry Points

| File | Class/Function | Purpose |
|------|---------------|---------|
| `manager.py` | `ValidationManager` | Central validation coordinator |
| `registry.py` | `SchemaRegistry` | Schema registration and lookup |
| `contract.py` | `ContractValidator` | Validate against Pydantic schemas |
| `ai_output.py` | `validate_ai_output_structure()` | Validate LLM output structure |
| `template.py` | `validate_template_variables_at_startup()` | Validate Jinja2 template vars |

## Usage

```python
from finwiz.validation import ValidationManager, get_validation_manager

manager = get_validation_manager()
result = manager.validate_all(data, context="crew_output")
if not result.is_valid:
    for error in result.errors:
        logger.error(f"Validation: {error.message}")
```

## Related Modules

- `finwiz.schemas` — Pydantic schemas validated against
- `finwiz.integration` — Integration-layer validation
- `finwiz.config.features` — Feature flags gating validation strictness
