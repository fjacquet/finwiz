# Implementation Plan

## Overview

This implementation plan fixes the critical data consumption gap where expensive crew analysis is generated but not used in the final report. The tasks are organized to deliver immediate diagnostic visibility, then fix the core data merge issue, and finally add comprehensive validation.

## Tasks

- [x] 1. Add diagnostic logging to trace data flow
  - Add detailed logging in `analyze_and_update_portfolio()` to show what data exists before and after merge
  - Log deep analysis results available (tickers, grades, scores)
  - Log portfolio holdings before merge (current grades and scores)
  - Log portfolio holdings after merge (verify grades changed)
  - Add logging to show when fallback data is detected
  - Include data lineage tracking (crew → storage → retrieval → merge)
  - _Requirements: 5.1, 5.2, 5.3, 9.1, 9.2, 9.3, 12.1, 12.2, 12.3_

- [x] 2. Create DeepAnalysisDataMerger component
  - Create new file `src/finwiz/utils/deep_analysis_merger.py`
  - Implement `DeepAnalysisDataMerger` class with `merge_deep_analysis_into_holdings()` method
  - Add `_is_fallback_data()` method to detect Grade D + score 0.6 + "Validation rapide" pattern
  - Add `_merge_holding_with_analysis()` method to properly copy analysis data to holdings
  - Add `_verify_merge()` method to confirm merge succeeded
  - Implement fail-fast behavior: raise `DataMergeError` if data is missing or corrupted
  - Add comprehensive logging for each merge operation
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 5.2, 5.3, 5.4, 10.1, 10.2, 13.1, 13.2_

- [x] 3. Create DataConsolidationValidator component
  - Create new file `src/finwiz/utils/data_consolidation_validator.py`
  - Implement `DataConsolidationValidator` class with `validate_crew_data_retrieval()` method
  - Add `_validate_crew_data_structure()` method to check required fields
  - Implement fail-fast behavior: raise `DataRetrievalError` if crew data is missing
  - Add detailed error messages showing what was expected vs what was found
  - Log successful retrievals and failures with crew names
  - _Requirements: 5.2, 5.3, 6.1, 6.2, 6.3, 12.2, 12.3, 13.2, 13.3_

- [x] 4. Create ReportDataValidator component
  - Create new file `src/finwiz/utils/report_data_validator.py`
  - Implement `ReportDataValidator` class with `validate_report_inputs()` method
  - Add `validate_portfolio_review_data()` method to detect fallback patterns
  - Check for required fields: portfolio_review, aplus_opportunities, discovery_status, etc.
  - Detect "NOT PROVIDED" placeholders and fail if found
  - Detect fallback Grade D pattern in portfolio holdings
  - Implement fail-fast: raise `ReportValidationError` if inputs are incomplete
  - _Requirements: 4.1, 4.2, 4.3, 10.3, 10.4, 10.5, 13.7, 13.8_

- [x] 5. Fix the data merge in flow_orchestrator.py
  - Update `analyze_and_update_portfolio()` method in `src/finwiz/flows/flow_orchestrator.py`
  - Import and instantiate `DeepAnalysisDataMerger`
  - Replace current merge logic with validated merger
  - Load portfolio review, extract holdings
  - Call `merger.merge_deep_analysis_into_holdings()` with validation
  - Update portfolio with merged holdings
  - Set `has_deep_analysis = True` flag
  - Save updated portfolio review
  - Wrap in try-except to catch `DataMergeError` and fail fast
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 5.4, 5.5, 6.4, 10.1, 10.2, 13.1, 13.2_

- [x] 6. Add data consolidation validation to flow
  - Update `check_investment_discovery()` method in `src/finwiz/flows/flow_orchestrator.py`
  - Import and instantiate `DataConsolidationValidator`
  - Before running discovery crews, validate that stock/etf/crypto crew data exists
  - Call `validator.validate_crew_data_retrieval(['stock', 'etf', 'crypto'])`
  - Wrap in try-except to catch `DataRetrievalError` and fail fast
  - Log validation results
  - _Requirements: 5.2, 5.3, 6.1, 6.2, 6.3, 12.2, 12.3, 13.2, 13.3_

- [x] 7. Add report input validation to flow
  - Update `report()` method in `src/finwiz/flows/flow_orchestrator.py`
  - Import and instantiate `ReportDataValidator`
  - Before generating report, validate all inputs
  - Call `validator.validate_report_inputs(crew_inputs)`
  - Call `validator.validate_portfolio_review_data(crew_inputs['portfolio_review'])`
  - Wrap in try-except to catch `ReportValidationError` and fail fast
  - Log validation results
  - _Requirements: 4.1, 4.2, 4.3, 10.3, 10.4, 10.5, 13.7, 13.8_

- [x] 8. Fix URL handling to prevent example.com placeholders
  - Search for any code that generates or uses URLs
  - Ensure URLs are only included if successfully retrieved from tools
  - Add validation: if URL is None or empty, omit it rather than using placeholder
  - Update report generation to show "URL not available" instead of example.com
  - Add logging when URLs cannot be retrieved
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.8, 2.9, 11.3, 11.6_

- [x] 9. Fix alternatives handling to prevent empty lists
  - Review `AlternativeFinder` in `src/finwiz/tools/alternative_finder_tool.py`
  - Ensure alternatives are properly found for Grade D holdings
  - Add logging when alternatives cannot be found
  - Update portfolio merge to include alternatives from deep analysis
  - Verify alternatives are passed through to report
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 10. Add data availability tracking
  - Create `DataAvailabilityTracker` class to track which data sources are available
  - Track: crew outputs, API responses, cached data, file system data
  - Generate data availability summary with counts and status
  - Include freshness warnings for stale data
  - Pass data availability summary to report crew
  - Update report to show actual availability status, not "NOT PROVIDED"
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 12.4, 12.5_

- [x] 11. Add Pydantic validation at all boundaries
  - Review all data transfers between components
  - Ensure all crew outputs use `output_pydantic` with strict schemas
  - Ensure Flow state uses Pydantic models (already done via `Flow[FinwizState]`)
  - Add Pydantic validation when loading data from files
  - Add Pydantic validation when passing data to report crew
  - Use `extra='forbid'` on all models to reject unknown fields
  - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7, 15.8_

- [x] 12. Add data quality metrics tracking
  - Create `DataQualityMetrics` class in `src/finwiz/utils/data_quality_metrics.py`
  - Track: fallback_grades_count, placeholder_urls_count, missing_data_count
  - Track: successful_merges_count, failed_merges_count
  - Calculate overall quality score (0-1)
  - Log metrics at end of flow execution
  - Export metrics to file for monitoring
  - _Requirements: 12.6, 12.7, 12.8, 12.9, 12.10_

- [ ] 13. Write unit tests for DeepAnalysisDataMerger
  - Create `tests/unit/utils/test_deep_analysis_merger.py`
  - Test successful merge: fallback data replaced with actual analysis
  - Test fail-fast when deep analysis is missing
  - Test fail-fast when fallback data is detected in analysis
  - Test merge verification catches mismatches
  - Test logging output for merge operations
  - Use pytest-mock for all mocking (unittest.mock is BANNED)
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_

- [ ] 14. Write unit tests for DataConsolidationValidator
  - Create `tests/unit/utils/test_data_consolidation_validator.py`
  - Test successful validation when all crew data exists
  - Test fail-fast when crew data is missing
  - Test fail-fast when crew data is corrupted
  - Test data structure validation
  - Test error messages include expected vs actual data
  - Use pytest-mock for all mocking
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_

- [ ] 15. Write unit tests for ReportDataValidator
  - Create `tests/unit/utils/test_report_data_validator.py`
  - Test successful validation when all inputs are complete
  - Test fail-fast when required fields are missing
  - Test fail-fast when "NOT PROVIDED" placeholders are detected
  - Test fail-fast when portfolio has fallback Grade D pattern
  - Test error messages are clear and actionable
  - Use pytest-mock for all mocking
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_

- [ ] 16. Write integration tests for end-to-end data flow
  - Create `tests/integration/test_data_flow_regression_fix.py`
  - Test complete flow: crew generation → storage → retrieval → merge → report
  - Test that portfolio holdings have actual grades, not fallback Grade D
  - Test that report has real URLs, not example.com
  - Test that alternatives are included for underperforming holdings
  - Test that data availability is accurately reported
  - Test fail-fast behavior when data is missing
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_

- [x] 17. Verify CrewAI configuration alignment
  - Review all crew configurations in `src/finwiz/crews/*/config/`
  - Verify task descriptions match requirements
  - Verify `output_pydantic` schemas exist and are correct
  - Verify report crew has NO tools (tool-free pattern)
  - Verify discovery crews are marked as "top 10 screening"
  - Verify deep analysis crews are marked as "single ticker analysis"
  - Update any misaligned configurations
  - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7, 14.8_

- [x] 18. Verify steering standards compliance
  - Review implementation against `.kiro/steering/validation.md`
  - Review implementation against `.kiro/steering/crewai-standards.md`
  - Review implementation against `.kiro/steering/crewai-flow-compliance.md`
  - Review implementation against `.kiro/steering/testing-standards.md`
  - Review implementation against `.kiro/steering/quality.md`
  - Document any deviations and justify them
  - Update code to align with steering standards
  - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 16.7, 16.8, 16.9, 16.10_

- [x] 19. Create verification script
  - Create `scripts/verify_data_quality.sh`
  - Check that crew outputs exist in output/ directories
  - Verify portfolio review has actual grades (not all Grade D)
  - Verify report has no example.com URLs
  - Verify report has no "NOT PROVIDED" messages
  - Calculate and display data quality score
  - Exit with error code if quality checks fail
  - _Requirements: 12.6, 12.7, 12.8, 12.9, 12.10_

- [x] 20. Update documentation
  - Update README with data quality requirements
  - Document the data flow: generation → storage → retrieval → merge → report
  - Document fail-fast behavior and error handling
  - Document how to verify data quality
  - Document how to debug data consumption issues
  - Add troubleshooting guide for common issues
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

## Implementation Order

**Phase 1: Immediate Diagnostics (Tasks 1)**

- Add logging to see exactly where data is lost
- Run system and analyze logs
- Confirm root cause

**Phase 2: Core Fix (Tasks 2-7)**

- Create validation components
- Fix data merge in flow
- Add validation at all boundaries
- This is the critical fix

**Phase 3: Comprehensive Validation (Tasks 8-12)**

- Fix URL handling
- Fix alternatives handling
- Add data availability tracking
- Add Pydantic validation
- Add quality metrics

**Phase 4: Testing (Tasks 13-16)**

- Unit tests for all new components
- Integration tests for end-to-end flow
- Verify no regressions

**Phase 5: Compliance & Documentation (Tasks 17-20)**

- Verify CrewAI configuration
- Verify steering compliance
- Create verification script
- Update documentation

## Success Criteria

After implementation, the system must:

1. ✅ Use actual crew analysis data in portfolio review (no Grade D fallbacks)
2. ✅ Include real URLs in reports (no example.com placeholders)
3. ✅ Show actual alternatives for underperforming holdings (no empty lists)
4. ✅ Report accurate data availability (no "NOT PROVIDED" messages)
5. ✅ Fail fast on errors (no silent degradation)
6. ✅ Provide complete audit trail (every data point traceable)
7. ✅ Pass all unit and integration tests
8. ✅ Comply with all FinWiz steering standards
9. ✅ Achieve 90%+ data quality score
10. ✅ Generate reports that users can trust and auditors can verify

## Verification Commands

```bash
# Run the system
uv run python src/finwiz/main.py

# Verify data quality
./scripts/verify_data_quality.sh

# Run tests
uv run pytest tests/unit/utils/test_deep_analysis_merger.py -v
uv run pytest tests/unit/utils/test_data_consolidation_validator.py -v
uv run pytest tests/unit/utils/test_report_data_validator.py -v
uv run pytest tests/integration/test_data_flow_regression_fix.py -v

# Check for regressions
uv run pytest tests/integration/core_analysis/ -v

# Verify no unittest.mock usage
make check-unittest-mock

# Verify code quality
ruff check . && ruff format .
```

## Rollback Plan

If issues arise during implementation:

1. **Task 1-7**: Can rollback individual tasks, system remains functional
2. **Task 8-12**: Can disable validation temporarily with feature flags
3. **Task 13-16**: Tests don't affect production, can be fixed independently
4. **Task 17-20**: Documentation and compliance can be updated post-deployment

**Emergency Rollback**: Revert `flow_orchestrator.py` changes and use cached portfolio review.
