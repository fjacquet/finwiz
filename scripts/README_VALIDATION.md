# FinWiz Architecture Validation Script

## Overview

The `validate_finwiz_architecture.py` script provides comprehensive automated validation of the FinWiz codebase against all 13 architectural requirements from the consolidation specification.

## Usage

```bash
# Run validation
python scripts/validate_finwiz_architecture.py

# The script will:
# 1. Run all validation checks
# 2. Generate a detailed markdown report
# 3. Save report to reports/architecture_validation_report.md
# 4. Exit with code 0 (success) or 1 (failures found)
```

## Validation Checks

The script performs 15 distinct validation checks across 9 phases:

### Phase 1: DeepAnalysisCrew Validation
- ✅ DeepAnalysisCrew exists at expected location
- ✅ Dynamic tool routing implementation
- ✅ DeepAnalysisResult schema with all required fields

### Phase 2: Flow Orchestration Validation
- ✅ Flow sequence matches business logic
- ✅ Atomic operations (analyze_and_update_portfolio)
- ✅ Listener dependencies are correct

### Phase 3: Discovery Crew Task Descriptions
- ✅ Stock crew has "top 10" language
- ✅ ETF crew has "top 10" language
- ✅ Crypto crew has "top 10" language

### Phase 4: Enum Documentation
- ✅ All tasks.yaml files have "REQUIRED ENUM VALUES" section

### Phase 5: Test Framework Validation
- ✅ No unittest.mock imports (pytest-mock only)

### Phase 6: File Size Validation
- ✅ All Python files under 400 lines

### Phase 7: HTML Generation Validation
- ✅ BeautifulSoup used for HTML generation
- ✅ No string concatenation patterns

### Phase 8: ReportCrew Tools Validation
- ✅ @final_reporter decorator present
- ✅ Empty tools list
- ✅ No external API calls

### Phase 9: Feature Flags Documentation
- ✅ All feature flags documented in .env.example

## Report Format

The generated report includes:

1. **Executive Summary**
   - Overall compliance score (percentage)
   - Pass/fail counts
   - Compliance status

2. **Validation Results by Phase**
   - Check name and status (✅/❌)
   - Detailed message
   - Requirement references
   - Remediation steps (for failures)
   - Specific details (file paths, line numbers, etc.)

3. **Remediation Summary**
   - Prioritized list of required actions
   - Requirement mappings

4. **Compliance Matrix**
   - Table mapping requirements to checks
   - Visual status indicators

## Current Status

As of the last run:
- **Compliance Score**: 46.7% (7/15 checks passed)
- **Status**: ⚠️ NEEDS ATTENTION

### Passing Checks
- DeepAnalysisCrew exists
- Flow sequence correct
- Atomic operations implemented
- Listener dependencies correct
- Discovery crew task descriptions correct

### Failing Checks
- Dynamic tool routing (needs implementation)
- DeepAnalysisResult schema (needs creation)
- Enum documentation (2 crews missing)
- Test framework (3 unittest.mock violations)
- File sizes (82 files over 400 lines)
- HTML generation (5 files using string concatenation)
- ReportCrew tools (appears to make API calls)
- Feature flags documentation (5 flags undocumented)

## Integration with CI/CD

The script can be integrated into CI/CD pipelines:

```bash
# In CI pipeline
python scripts/validate_finwiz_architecture.py
if [ $? -ne 0 ]; then
    echo "Architecture validation failed"
    exit 1
fi
```

## Extending the Validator

To add new validation checks:

1. Add a new validation method to `FinWizArchitectureValidator` class
2. Call the method in `validate_all()`
3. Use `_add_result()` to record the validation result
4. Update the phase grouping in `generate_report()` if needed

Example:

```python
def _validate_new_requirement(self):
    """Check for new requirement."""
    # Perform validation
    passed = check_condition()
    
    self._add_result(ValidationResult(
        check_name="New requirement check",
        passed=passed,
        message="Description of result",
        requirement_refs=["X.Y"],
        remediation="How to fix" if not passed else None,
        details=["Detail 1", "Detail 2"]
    ))
```

## Requirements Mapping

The validator checks compliance with:
- **Requirement 1**: Unified Deep Analysis Crew (1.1-1.8)
- **Requirement 2**: Corrected Flow Orchestration (2.1-2.10)
- **Requirement 4**: Analysis Capabilities (4.18)
- **Requirement 6**: Code Quality & Testing (6.3-6.13)
- **Requirement 7**: Configuration Management (7.4-7.5)

## Output Files

- **Report**: `reports/architecture_validation_report.md`
- **Console**: Real-time progress and summary

## Dependencies

- Python 3.12+
- Standard library only (no external dependencies)
- Works with existing FinWiz project structure
