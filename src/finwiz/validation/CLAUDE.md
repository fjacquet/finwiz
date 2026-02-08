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
│
├── # Specialized validators
├── ai_output.py             # validate_ai_output_structure(), validate_qualitative_insights()
├── flow.py                  # DataFlowValidator, CrewDataContract, ReporterContextValidator
├── report.py                # ReportValidator, validate_report_file()
├── template.py              # TemplateVariableValidator, validate_template_variables_at_startup()
├── rules.py                 # ValidationRules
├── pipeline_stages.py       # PipelineStages, CrossCrewValidationResult
├── tool_restrictions.py     # Tool usage enforcement
│
├── # Supporting infrastructure
├── int_pipeline.py          # Integration validation pipeline
├── url.py                   # URL validation
├── freshness.py             # Data freshness checks
├── quality_metrics.py       # Data quality metrics
├── consolidation.py         # Consolidation validation
├── report_data.py           # Report data validation
├── sec_citation.py          # SEC citation validation
└── scripts.py               # Validation scripts
```

## Entry Points

| File | Class/Function | Purpose |
|------|---------------|---------|
| `manager.py` | `ValidationManager` | Central validation coordinator |
| `registry.py` | `SchemaRegistry` | Schema registration and lookup |
| `contract.py` | `ContractValidator` | Validate against Pydantic schemas |
| `ai_output.py` | `validate_ai_output_structure()` | Validate LLM output structure |
| `flow.py` | `DataFlowValidator` | Validate data between pipeline stages |
| `template.py` | `validate_template_variables_at_startup()` | Validate Jinja2 template vars |
| `report.py` | `validate_report_file()` | Validate generated reports |

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
