# Documentation Archive

This directory contains historical documentation that is preserved for reference but not needed for daily development.

## Archive Structure

### Implementation Summaries
**Location**: `implementation_summaries/`

Historical task implementation records documenting feature development:
- Task 1.x series - Portfolio holdings analysis features
- Task 2.x series - Additional feature implementations
- Task 14-15 - Specific feature implementations

**Use**: Reference when understanding feature history or debugging related issues.

### Fix Reports
**Location**: `fix_reports/`

Historical bug fix documentation:
- Schema fixes (A+ discovery, crew schemas, enums, unions)
- Hallucination fixes (V1 and V2)
- Comprehensive fix summaries
- Diagnosis reports

**Use**: Reference when encountering similar issues or understanding fix history.

### Consolidation Reports
**Location**: `consolidation_reports/`

Documentation consolidation history:
- Phase 1 and Phase 2 consolidation plans and completion reports
- Documentation consolidation summaries
- Steering rules updates

**Use**: Understand how documentation evolved and consolidation decisions.

### Testing Documentation
**Location**: `testing/`

Historical testing implementation documentation:
- Testing enforcement implementation
- unittest.mock blacklist and enforcement
- Testing standards (now in `.kiro/steering/testing-standards.md`)

**Use**: Reference for testing implementation history. Current standards are in steering files.

## When to Use Archive

### Good Reasons to Check Archive
- Understanding why a feature was implemented a certain way
- Debugging issues related to historical changes
- Learning from past fixes for similar problems
- Understanding documentation evolution
- Historical context for architectural decisions

### Not Needed For
- Daily development work
- Learning how to use current features
- Understanding current architecture
- Writing new code or tests

## Current Documentation

For current, active documentation, see:
- **[Documentation Hub](../README.md)** - Main documentation navigation
- **[Developer Guide](../DEVELOPER_GUIDE.md)** - Current development standards
- **[Architecture Guide](../ARCHITECTURE.md)** - Current system architecture
- **[API Reference](../API_REFERENCE.md)** - Current API documentation

## Archive Maintenance

### Retention Policy
- Keep all historical documentation indefinitely
- Organize by category for easy reference
- Update this README when adding new categories

### Adding to Archive
When archiving new documentation:
1. Determine appropriate category
2. Move file to correct subdirectory
3. Update this README if new category
4. Update main docs/README.md to remove references

---

**Archive Created**: 2025-01-07  
**Total Archived Files**: 29 (as of 2025-01-07)  
**Categories**: 4 (implementation_summaries, fix_reports, consolidation_reports, testing)
