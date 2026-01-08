# Requirements Document: JSON-First Crew Architecture

## Introduction

This specification defines the migration of FinWiz crew task outputs from markdown-based to JSON-based structured data format. The goal is to improve data flow, validation, and integration between crews while maintaining human-readable final reports.

### Current State

Currently, FinWiz crews generate markdown (`.md`) files for intermediate analysis tasks and HTML files for final reports. This approach has several limitations:

- Markdown parsing required for data extraction
- No schema validation for intermediate outputs
- Inconsistent data structures between crews
- Difficult integration and data flow between tasks
- Error-prone data extraction from text

### Target State

All intermediate crew tasks will output validated JSON data conforming to Pydantic schemas, while final reports remain in HTML format for human readability. This enables:

- Automatic schema validation at task boundaries
- Type-safe data flow between tasks
- Consistent data structures across all crews
- Easier integration with external systems
- Improved debugging and error handling

## Requirements

### Requirement 1: Structured Data Output

**User Story:** As a FinWiz developer, I want intermediate crew tasks to output validated JSON data, so that data flows
cleanly between tasks with guaranteed schema compliance.

#### Acceptance Criteria

1. WHEN an intermediate analysis task completes THEN the system SHALL output a JSON file with Pydantic-validated structure
1. WHEN a task has `output_pydantic` defined THEN the output SHALL conform to the specified schema
1. WHEN schema validation fails THEN the system SHALL provide clear error messages with field-level details
1. WHEN JSON output is generated THEN it SHALL include all required fields as defined in the schema
1. IF a task is a final report task THEN it MAY output HTML format for human readability

### Requirement 2: Schema Design

**User Story:** As a FinWiz developer, I want comprehensive Pydantic schemas for all crew outputs, so that data
structures are well-defined and validated.

#### Acceptance Criteria

1. WHEN creating schemas THEN each crew SHALL have schemas for all intermediate task outputs
1. WHEN defining schemas THEN they SHALL use Pydantic v2 with `extra='forbid'` for strict validation
1. WHEN schemas reference other schemas THEN they SHALL use proper type hints and imports
1. WHEN a schema is created THEN it SHALL include docstrings and field descriptions
1. WHEN schemas are updated THEN backward compatibility SHALL be maintained or migration paths provided

### Requirement 3: Task Configuration

**User Story:** As a FinWiz developer, I want task configurations to specify output schemas, so that the system
knows what structure to validate against.

#### Acceptance Criteria

1. WHEN configuring an intermediate task THEN it SHALL specify `output_pydantic` with the schema class
1. WHEN configuring a final report task THEN it SHALL NOT specify `output_pydantic` (HTML output)
1. WHEN a task has `output_pydantic` THEN the `output_file` SHALL have `.json` extension
1. WHEN a task generates HTML THEN the `output_file` SHALL have `.html` extension
1. WHEN task configuration is invalid THEN the system SHALL fail fast with clear error messages

### Requirement 4: Data Flow Between Tasks

**User Story:** As a FinWiz developer, I want tasks to consume JSON outputs from previous tasks, so that data flows
seamlessly through the crew pipeline.

#### Acceptance Criteria

1. WHEN a task depends on another task THEN it SHALL be able to read the JSON output directly
1. WHEN reading JSON output THEN the system SHALL deserialize it into Pydantic models
1. WHEN data is missing or invalid THEN the system SHALL provide clear error messages
1. WHEN tasks run in sequence THEN JSON data SHALL be passed through the context
1. WHEN parallel tasks complete THEN their JSON outputs SHALL be aggregated for downstream tasks

### Requirement 5: Backward Compatibility

**User Story:** As a FinWiz user, I want existing functionality to continue working during migration, so that the
 system remains stable.

#### Acceptance Criteria

1. WHEN migrating tasks THEN existing markdown outputs SHALL be preserved until migration is complete
1. WHEN both formats exist THEN the system SHALL prefer JSON over markdown
1. WHEN reading outputs THEN the system SHALL support both JSON and markdown formats during transition
1. WHEN migration is complete THEN markdown support MAY be removed
1. WHEN errors occur THEN the system SHALL provide clear migration guidance

### Requirement 6: Error Handling

**User Story:** As a FinWiz developer, I want clear error messages when JSON validation fails, so that I can quickly
 identify and fix issues.

#### Acceptance Criteria

1. WHEN JSON parsing fails THEN the error SHALL include the file path and line number
1. WHEN schema validation fails THEN the error SHALL include field path and validation rule
1. WHEN required fields are missing THEN the error SHALL list all missing fields
1. WHEN type mismatches occur THEN the error SHALL show expected vs actual types
1. WHEN validation errors occur THEN the system SHALL log the full output for debugging

### Requirement 7: Final Report Generation

**User Story:** As a FinWiz user, I want final reports to remain in HTML format, so that they are human-readable and
visually appealing.

#### Acceptance Criteria

1. WHEN generating final reports THEN they SHALL be in HTML format
1. WHEN final reports are generated THEN they SHALL consume JSON data from intermediate tasks
1. WHEN HTML is generated THEN it SHALL include all data from upstream JSON outputs
1. WHEN reports are translated THEN the translation task SHALL consume HTML input
1. WHEN reports are complete THEN they SHALL be saved with `.html` extension

### Requirement 8: Schema Documentation

**User Story:** As a FinWiz developer, I want schema documentation, so that I understand the structure of each crew's outputs.

#### Acceptance Criteria

1. WHEN schemas are defined THEN they SHALL include comprehensive docstrings
1. WHEN fields are added THEN they SHALL include descriptions and examples
1. WHEN schemas are complex THEN they SHALL include usage examples
1. WHEN schemas change THEN the documentation SHALL be updated
1. WHEN viewing schemas THEN developers SHALL be able to generate JSON schema files

### Requirement 9: Modern Python 3.12 Type Annotations

**User Story:** As a FinWiz developer, I want schemas to use modern Python 3.12 type annotations, so that code is clean
and follows current best practices.

#### Acceptance Criteria

1. WHEN defining optional fields THEN they SHALL use `Type | None` syntax (Python 3.10+)
1. WHEN defining union types THEN they SHALL use `Type1 | Type2` syntax (Python 3.10+)
1. WHEN schemas are validated THEN they SHALL work correctly with CrewAI's JSON conversion
1. WHEN task output conversion fails THEN the error SHALL provide clear guidance on type annotation issues
1. WHEN migrating schemas THEN all legacy `Optional[Type]` and `Union[Type1, Type2]` syntax SHALL be converted to modern
union operators

## Affected Crews

The following crews will be migrated to JSON-first architecture:

1. **Stock Crew** - 4 intermediate tasks → JSON
2. **ETF Crew** - 4 intermediate tasks → JSON
3. **Crypto Crew** - 4 intermediate tasks → JSON
4. **Investment Discovery Crew** - 6 intermediate tasks → JSON
5. **Portfolio Rebalancing Crew** - 6 intermediate tasks → JSON
6. **Report Crew** - 3 intermediate tasks → JSON (final report remains HTML)

## Known Issues to Address

### Legacy Type Annotation Syntax in Schemas

**Current State**: Recent schema audit (SCHEMA_AUDIT_SUMMARY.md) converted schemas FROM modern Python 3.12 syntax TO
legacy `Optional`/`Union` syntax. This contradicts the project's Python 3.12+ standard documented in README.md and
PYTHON_312_UPGRADE_SUMMARY.md.

**Problem**: Schemas in `src/finwiz/schemas/` currently use:

- `Optional[Type]` instead of `Type | None`
- `Union[Type1, Type2]` instead of `Type1 | Type2`

**Root Cause**: The schema audit was performed under the mistaken belief that CrewAI required legacy syntax. However,
 the project standard is Python 3.12+, and we should use modern type annotations throughout.

**Target State**: All schemas use modern Python 3.12 union operator syntax, consistent with the rest of the codebase.

**Migration Required**: Revert recent schema changes and modernize to Python 3.12 syntax:

- Replace `Optional[Type]` with `Type | None`
- Replace `Union[Type1, Type2]` with `Type1 | Type2`
- Remove unnecessary `from typing import Optional, Union` imports

**Example**:

```python
# ❌ Legacy syntax (currently in schemas after audit)
from typing import Optional, Union

class MySchema(BaseModel):
    field1: Optional[str]
    field2: Union[int, float]

# ✅ Modern Python 3.12 syntax (project standard)
class MySchema(BaseModel):
    field1: str | None
    field2: int | float
```

**Affected Files** (from SCHEMA_AUDIT_SUMMARY.md):

- `src/finwiz/schemas/common.py`
- `src/finwiz/schemas/validation.py`
- `src/finwiz/schemas/portfolio_review.py`
- `src/finwiz/schemas/perplexity.py`
- `src/finwiz/schemas/investment_discovery.py`
- `src/finwiz/schemas/session.py`
- `src/finwiz/schemas/quantitative.py`
- `src/finwiz/schemas/rebalancing/trades.py`

## Out of Scope

The following are explicitly out of scope for this specification:

- Changes to agent behavior or prompts
- Modifications to tool implementations
- Updates to LLM configurations
- Changes to crew orchestration logic
- Database schema changes
- API endpoint modifications
- Performance optimization (separate effort)
- Schema versioning system (future enhancement)

## Success Metrics

1. **Schema Coverage**: 100% of intermediate tasks have Pydantic schemas
1. **Validation Rate**: 100% of JSON outputs pass schema validation
1. **Error Rate**: <1% of tasks fail due to JSON validation errors
1. **Performance**: JSON parsing is ≥2x faster than markdown parsing
1. **Data Quality**: Zero data loss during format conversion

## Dependencies

- Python 3.12+ (required for modern type annotations)
- Pydantic v2 (already in use)
- Existing crew infrastructure
- Current task configuration system
- Schema registry system (if exists)

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Schema design errors | High | Comprehensive testing and validation |
| Breaking changes | High | Phased migration with backward compatibility |
| Performance degradation | Medium | Benchmark before and after migration |
| Agent JSON generation issues | High | Clear prompts and validation feedback |
| Data loss during migration | High | Preserve markdown outputs during transition |
| Legacy type annotations in schemas | High | Revert recent schema audit changes; modernize to Python 3.12 syntax |
| CrewAI compatibility issues | High | Test all schemas with CrewAI converter before deployment |
| Inconsistent type annotation standards | Medium | Establish clear project-wide standard (Python 3.12 modern syntax) |

## Migration Strategy

1. **Phase 1**: Revert schema audit changes to modern Python 3.12 syntax
1. **Phase 2**: Design and implement schemas for all crews
1. **Phase 3**: Update task configurations to use `output_pydantic`
1. **Phase 4**: Test JSON generation with existing crews
1. **Phase 5**: Migrate one crew at a time, starting with simplest
1. **Phase 6**: Remove markdown support after all crews migrated
1. **Phase 7**: Performance optimization and monitoring

## Notes

- Final HTML reports remain unchanged for human readability
- Translation tasks continue to work with HTML inputs
- JSON outputs enable better integration with external systems
- Schema validation improves data quality and debugging
- This change aligns with modern data pipeline best practices
