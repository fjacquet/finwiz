# FinWiz Validation System

The FinWiz validation system provides centralized, configurable data validation with structured error handling. It ensures data integrity across all crews while supporting flexible deployment modes.

## Architecture Overview

The validation system consists of four core components:

1. **ValidationManager**: Central orchestrator for all validation operations
2. **SchemaRegistry**: Centralized registry for Pydantic models
3. **ValidationResult**: Structured validation outcomes with detailed error context
4. **ValidationMode**: Configurable strictness levels (off/warn/error)

## Core Components

### ValidationManager

The `ValidationManager` class coordinates all validation operations and provides the main interface for validating data throughout the application.

```python
from finwiz.validation import get_validation_manager, ValidationMode

# Get the global validation manager instance
manager = get_validation_manager()

# Validate crew output against registered schemas
result = manager.validate_crew_output(
    data=crew_output_data,
    crew_type="stock",
    output_type="analysis"
)

# Validate reporter input with strict validation
result = manager.validate_reporter_input(reporter_data)

# Validate against any registered schema by name
result = manager.validate_with_schema(data, "RiskAssessmentStandardized")
```

#### Key Methods

- `validate_crew_output(data, crew_type, output_type)`: Validates crew-specific outputs
- `validate_reporter_input(data)`: Validates ReporterInput with strict validation
- `validate_with_schema(data, schema_name)`: Validates against any registered schema
- `set_strictness_mode(mode)`: Changes validation mode programmatically
- `get_strictness_mode()`: Returns current validation mode

### SchemaRegistry

The `SchemaRegistry` provides centralized management of all Pydantic validation models.

```python
from finwiz.validation import get_registry

# Get the global schema registry
registry = get_registry()

# Register a new schema
registry.register_schema("MyCustomSchema", MyPydanticModel)

# Register crew-specific schema
registry.register_crew_schema("stock", "custom_analysis", MyAnalysisModel)

# Retrieve schemas
schema_class = registry.get_schema("ReporterInput")
crew_schema = registry.get_crew_schema("etf", "factsheet")

# List available schemas
all_schemas = registry.list_schemas()
crew_schemas = registry.list_crew_schemas()
```

#### Pre-registered Schemas

The registry automatically registers existing FinWiz schemas:

**Core Schemas:**
- `ReporterInput`: Aggregate input for final reporter
- `ValidatedTicker`: Ticker validation results
- `RiskAssessmentStandardized`: Standardized risk scoring

**Crew-Specific Schemas:**
- Stock: `TenKInsight`, `MarketSentiment`, `RiskAssessmentStandardized`
- ETF: `ETFFactsheet`, `ETFTopHolding`, `RiskAssessmentStandardized`
- Crypto: `CryptoThesis`, `RiskAssessmentStandardized`
- Report: `ReporterInput`

### ValidationResult

The `ValidationResult` class provides structured validation outcomes with detailed error context.

```python
# Check validation status
if result.is_valid:
    # Use sanitized data
    clean_data = result.sanitized_data
else:
    # Handle validation errors
    for error in result.errors:
        print(f"Error at {error.field_path}: {error.message}")
        if error.context:
            print(f"Context: {error.context}")

# Check for warnings (non-blocking issues)
if result.has_warnings:
    for warning in result.warnings:
        print(f"Warning at {warning.field_path}: {warning.message}")
```

#### ValidationError Structure

```python
class ValidationError(BaseModel):
    field_path: str          # Dot-separated path to failed field
    error_type: str          # Type of validation error
    message: str             # Human-readable error message
    input_value: Any         # Value that caused the error
    context: dict[str, Any]  # Additional error context
```

#### ValidationWarning Structure

```python
class ValidationWarning(BaseModel):
    field_path: str          # Dot-separated path to field
    message: str             # Human-readable warning message
    input_value: Any         # Value that triggered warning
    context: dict[str, Any]  # Additional warning context
```

## Validation Modes

The validation system supports three strictness modes controlled by the `VALIDATION_STRICTNESS` environment variable:

### OFF Mode (`VALIDATION_STRICTNESS=off`)
- Validation is completely disabled
- Original data passes through unchanged
- No errors or warnings are generated
- Useful for development or when validation overhead is not desired

### WARN Mode (`VALIDATION_STRICTNESS=warn`) - Default
- Validation errors are converted to warnings
- Processing continues with original data
- Warnings are logged for monitoring
- Ideal for production environments where data flow continuity is critical

### ERROR Mode (`VALIDATION_STRICTNESS=error`)
- Validation errors halt processing
- Invalid data is rejected
- Strict enforcement of data contracts
- Recommended for critical production systems

## Integration with Crews

### Crew Output Validation

Each crew's output should be validated before passing to the next stage:

```python
# In crew implementation
def process_stock_analysis(self, data):
    # Perform analysis...
    analysis_result = self.analyze_stock(data)
    
    # Validate output
    manager = get_validation_manager()
    result = manager.validate_crew_output(
        data=analysis_result,
        crew_type="stock",
        output_type="analysis"
    )
    
    if not result.is_valid:
        # Handle validation errors based on mode
        self.handle_validation_errors(result.errors)
    
    return result.sanitized_data or analysis_result
```

### Reporter Input Validation

The final reporter should validate its aggregate input:

```python
# In report crew
def generate_report(self, reporter_input):
    # Validate reporter input
    manager = get_validation_manager()
    result = manager.validate_reporter_input(reporter_input)
    
    if not result.is_valid:
        raise ValidationError(f"Invalid reporter input: {result.errors}")
    
    # Use validated data for report generation
    return self.create_html_report(result.sanitized_data)
```

## Configuration

### Environment Variables

- `VALIDATION_STRICTNESS`: Controls global validation mode
  - Values: `off`, `warn`, `error`
  - Default: `warn`

### Programmatic Configuration

```python
from finwiz.validation import get_validation_manager, ValidationMode

manager = get_validation_manager()

# Change validation mode at runtime
manager.set_strictness_mode(ValidationMode.ERROR)

# Check current mode
current_mode = manager.get_strictness_mode()
```

## Error Handling Best Practices

### 1. Graceful Degradation

```python
result = manager.validate_crew_output(data, "stock", "analysis")

if result.is_valid:
    # Use validated, sanitized data
    return result.sanitized_data
elif manager.get_strictness_mode() == ValidationMode.WARN:
    # Log warnings but continue processing
    logger.warning(f"Validation warnings: {len(result.warnings)}")
    return data  # Use original data
else:
    # In ERROR mode, halt processing
    raise ValidationError("Validation failed", errors=result.errors)
```

### 2. Detailed Error Reporting

```python
if not result.is_valid:
    error_summary = []
    for error in result.errors:
        error_summary.append(
            f"Field '{error.field_path}': {error.message}"
        )
    
    logger.error(f"Validation failed:\n" + "\n".join(error_summary))
```

### 3. Context-Aware Error Messages

```python
# ValidationManager automatically includes context
result = manager.validate_crew_output(data, "stock", "analysis")

for error in result.errors:
    print(f"Error in {error.context.get('schema', 'unknown')}: {error.message}")
```

## Testing Validation

### Unit Testing Validation Logic

```python
import pytest
from finwiz.validation import ValidationManager, SchemaRegistry, ValidationMode

def test_validation_manager_crew_output():
    # Arrange
    registry = SchemaRegistry()
    manager = ValidationManager(registry)
    
    # Test data
    valid_data = {"ticker": "AAPL", "recommendation": "BUY"}
    invalid_data = {"ticker": "INVALID", "recommendation": "MAYBE"}
    
    # Act & Assert
    result = manager.validate_crew_output(valid_data, "stock", "analysis")
    assert result.is_valid
    
    result = manager.validate_crew_output(invalid_data, "stock", "analysis")
    assert not result.is_valid
    assert len(result.errors) > 0

def test_validation_modes():
    manager = ValidationManager()
    
    # Test mode switching
    manager.set_strictness_mode(ValidationMode.ERROR)
    assert manager.get_strictness_mode() == ValidationMode.ERROR
    
    manager.set_strictness_mode(ValidationMode.WARN)
    assert manager.get_strictness_mode() == ValidationMode.WARN
```

### Integration Testing

```python
def test_end_to_end_validation():
    """Test validation across crew boundaries."""
    # Test complete workflow with validation at each stage
    stock_crew_output = run_stock_crew()
    etf_crew_output = run_etf_crew()
    
    # Validate individual outputs
    manager = get_validation_manager()
    
    stock_result = manager.validate_crew_output(
        stock_crew_output, "stock", "analysis"
    )
    assert stock_result.is_valid
    
    # Validate reporter input
    reporter_input = aggregate_crew_outputs(
        stock_result.sanitized_data,
        etf_crew_output
    )
    
    reporter_result = manager.validate_reporter_input(reporter_input)
    assert reporter_result.is_valid
```

## Migration Guide

### Existing Code Integration

To integrate the validation system into existing crews:

1. **Import validation components:**
   ```python
   from finwiz.validation import get_validation_manager
   ```

2. **Add validation to crew outputs:**
   ```python
   # Before returning crew results
   manager = get_validation_manager()
   result = manager.validate_crew_output(data, crew_type, output_type)
   
   if result.is_valid:
       return result.sanitized_data
   else:
       # Handle based on validation mode
       return self.handle_validation_failure(result)
   ```

3. **Register custom schemas:**
   ```python
   from finwiz.validation import get_registry
   
   registry = get_registry()
   registry.register_schema("MyCustomSchema", MyPydanticModel)
   ```

4. **Update environment configuration:**
   ```bash
   # Add to .env file
   VALIDATION_STRICTNESS=warn
   ```

### Backward Compatibility

The validation system is designed to be non-breaking:
- Default WARN mode allows existing workflows to continue
- Validation can be completely disabled with OFF mode
- Existing Pydantic models work without modification
- No changes required to existing crew interfaces

## Performance Considerations

### Validation Overhead

- Validation adds minimal overhead in WARN/ERROR modes
- OFF mode has zero validation overhead
- Schema registry uses efficient dictionary lookups
- Pydantic validation is optimized for performance

### Caching Strategies

- Schema registry caches compiled Pydantic models
- ValidationManager reuses registry instances
- Consider caching validation results for identical inputs

### Memory Usage

- ValidationResult objects are lightweight
- Error/warning collections scale with validation issues
- Registry maintains references to model classes, not instances

## Troubleshooting

### Common Issues

1. **Schema Not Found Errors:**
   ```
   Error: Schema 'MySchema' not found in registry
   ```
   - Ensure schema is registered with `registry.register_schema()`
   - Check schema name spelling and case sensitivity

2. **Validation Mode Not Applied:**
   ```
   Validation still running in ERROR mode despite WARN setting
   ```
   - Check `VALIDATION_STRICTNESS` environment variable
   - Verify environment is loaded before ValidationManager creation
   - Use `manager.set_strictness_mode()` for runtime changes

3. **Pydantic Validation Errors:**
   ```
   ValidationError: extra fields not permitted
   ```
   - Ensure Pydantic models use `extra='forbid'` configuration
   - Check for typos in field names
   - Verify data structure matches schema expectations

### Debug Mode

Enable detailed validation logging:

```python
import logging

# Enable debug logging for validation
logging.getLogger('finwiz.validation').setLevel(logging.DEBUG)
```

This will provide detailed information about:
- Schema registration events
- Validation attempts and results
- Mode changes and configuration updates
- Error details and context