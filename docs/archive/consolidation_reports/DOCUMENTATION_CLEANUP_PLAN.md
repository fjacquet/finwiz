# Documentation Cleanup & Consolidation Plan

**Date**: 2025-01-07  
**Goal**: Reduce documentation clutter and improve maintainability

## Current State Analysis

### Total Files in docs/: ~50 files
- Core documentation: ~10 files (keep)
- Implementation summaries: ~15 files (archive)
- Fix reports: ~10 files (archive)
- Consolidation reports: ~5 files (archive)
- Subdirectories: 6 (keep)

## Cleanup Strategy

### Phase 1: Archive Implementation Summaries ✅

**Move to docs/archive/implementation_summaries/**:
- TASK_1_COMPLETE_SUMMARY.md
- TASK_1_COMPLETE_VERIFICATION.md
- TASK_1.1_IMPLEMENTATION_SUMMARY.md
- TASK_1.2_IMPLEMENTATION_SUMMARY.md
- TASK_1.3_IMPLEMENTATION_SUMMARY.md
- TASK_1.5_IMPLEMENTATION_SUMMARY.md
- TASK_14_IMPLEMENTATION_SUMMARY.md
- TASK_15_IMPLEMENTATION_SUMMARY.md
- TASK_2_COMPLETE_SUMMARY.md
- TASK_2_COMPLETE_VERIFICATION.md
- TASK_2.1_COMPLETE_SUMMARY.md
- TASK_2.3_INTEGRATION_TEST_SUMMARY.md

**Rationale**: These are historical implementation records, useful for reference but not needed in main docs.

### Phase 2: Archive Fix Reports ✅

**Move to docs/archive/fix_reports/**:
- APLUS_DISCOVERY_SCHEMA_FIX.md
- COMPREHENSIVE_SCHEMA_FIX_SUMMARY.md
- CREW_SCHEMA_FIX_SUMMARY.md
- DIAGNOSIS_COMPLETE.md
- ENUM_VALUE_FIX_SUMMARY.md
- FIX_IMPLEMENTATION_COMPLETE.md
- HALLUCINATION_FIX_REPORT_V2.md
- HALLUCINATION_FIX_REPORT.md
- UNION_TYPE_FIX_SUMMARY.md

**Rationale**: Historical bug fix documentation, useful for debugging but not for daily use.

### Phase 3: Archive Consolidation Reports ✅

**Move to docs/archive/consolidation_reports/**:
- CONSOLIDATION_COMPLETE.md
- DOCUMENTATION_CONSOLIDATION_SUMMARY.md
- PHASE_2_CONSOLIDATION_COMPLETE.md
- PHASE_2_CONSOLIDATION_PLAN.md
- STEERING_RULES_UPDATED.md

**Rationale**: Historical consolidation records, already completed.

### Phase 4: Archive Testing Documentation ✅

**Move to docs/archive/testing/**:
- TESTING_ENFORCEMENT.md
- UNITTEST_MOCK_BLACKLIST.md
- UNITTEST_MOCK_ENFORCEMENT_SUMMARY.md

**Rationale**: Testing standards are now in `.kiro/steering/testing-standards.md`. These are historical implementation docs.

### Phase 5: Keep Core Documentation

**Keep in docs/ (10 files)**:
1. README.md - Documentation hub
2. API_REFERENCE.md - API documentation
3. ARCHITECTURE.md - Architecture guide
4. DEVELOPER_GUIDE.md - Developer guide
5. USER_GUIDE.md - User guide
6. APLUS_SYSTEM.md - A+ system documentation
7. SYSTEM_OPERATIONS.md - System operations
8. ENHANCED_DATA_EXTRACTION.md - Enhanced data extraction
9. REPORT_CREW_ENHANCED_EXAMPLES.md - Report examples
10. CREW_DATA_INTEGRATION_INDEX.md - Data integration index
11. CREW_DATA_INTEGRATION_QUICK_START.md - Quick start
12. portfolio_holdings_analysis_user_guide.md - Portfolio guide
13. portfolio_holdings_performance.md - Performance guide
14. quantitative_analysis.md - Quantitative analysis
15. perplexity_sonar_integration_spec.md - Perplexity integration
16. JSON_MIGRATION_GUIDE.md - Migration guide (keep for now)

**Keep subdirectories**:
- investment_discovery/
- portfolio_rebalancing/
- schemas/
- archive/ (expanded)
- change_requests/
- fixes/

## Expected Results

### Before Cleanup
- docs/: ~50 files
- Difficult to find relevant documentation
- Mix of current and historical docs

### After Cleanup
- docs/: ~16 core files
- Clear separation of current vs historical
- Easy navigation to relevant docs
- Historical docs preserved in archive/

## Implementation Steps

1. Create archive subdirectories
2. Move implementation summaries
3. Move fix reports
4. Move consolidation reports
5. Move testing documentation
6. Update README.md references if needed
7. Verify all links still work

## Verification

After cleanup, verify:
- [ ] All core docs accessible from docs/README.md
- [ ] No broken links in main documentation
- [ ] Archive structure is logical
- [ ] Total file count reduced by ~70%
