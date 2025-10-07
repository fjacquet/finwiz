# Implementation Plan: Report Data Quality Fixes

## Overview

Fix data quality issues at the source by implementing proper validation, data availability tracking, and transparent error handling. No post-processing - fix the root causes.

---

## Tasks

- [x] 1. Implement SEC Filing URL Generator
  - Create `src/finwiz/tools/sec_filing_url_generator.py` with SECFilingURLGenerator class
  - Implement `get_filing_url()` method using SEC EDGAR API
  - Implement `get_company_browse_url()` method for fallback URLs
  - Implement `verify_url()` method to check URL accessibility
  - Add CIK lookup functionality
  - Handle cases where no filings are available (return None)
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 2. Update SEC Analysis Tool to Use URL Generator
  - Modify `src/finwiz/tools/enhanced_sec_tool.py` to use SECFilingURLGenerator
  - Replace hardcoded URL generation with generator calls
  - Add URL verification before including in results
  - Return "No SEC filings available" message when URLs are None
  - Add logging for URL generation and verification
  - _Requirements: 2.1, 2.2, 2.3, 2.5_

- [x] 3. Implement Portfolio Holdings Processor
  - Create `src/finwiz/orchestrators/portfolio_holdings_processor.py` with PortfolioHoldingsProcessor class
  - Implement `load_all_holdings()` to read from stock.csv, etf.csv, crypto.csv
  - Implement `process_holdings()` to process ALL holdings including failed validations
  - Implement `get_processing_summary()` to track what was processed
  - Add logging for each holding processed
  - Track and report excluded holdings with reasons
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 4. Update Portfolio Review to Use Holdings Processor
  - Modify `src/finwiz/orchestrators/portfolio_review.py` to use PortfolioHoldingsProcessor
  - Ensure ALL holdings are passed to report generation
  - Include processing summary in report data
  - Add validation status indicators for each holding
  - Log count of holdings processed vs. holdings in CSV
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 5. Implement A+ Discovery Data Accessor
  - Create `src/finwiz/integration/aplus_discovery_accessor.py` with APlusDiscoveryAccessor class
  - Implement `has_discovery_results()` to check for output/discovery/ files
  - Implement `load_discovery_results()` to parse discovery JSON
  - Implement `get_opportunities_summary()` for human-readable summary
  - Handle case where discovery hasn't run (return None with clear message)
  - Add logging for discovery data access
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 6. Update Report Crew to Use Discovery Accessor
  - Modify report crew to use APlusDiscoveryAccessor
  - Display "No A+ opportunities found" when results are empty
  - Display "A+ discovery not run" when results don't exist
  - Include complete opportunity data when available
  - Add discovery status to data availability summary
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 7. Enhance Backtesting Metrics Extractor
  - Update `src/finwiz/integration/backtesting_extractor.py` to extract ALL metrics
  - Ensure annualized_return, sharpe_ratio, sortino_ratio, calmar_ratio, max_drawdown, win_rate are extracted
  - Use None for unavailable metrics (not strings like "Données non disponibles")
  - Implement `get_available_metrics()` to return dict with None for missing values
  - Implement `format_for_display()` to show "Not calculated" for None values
  - Add logging for which metrics are missing and why
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 8. Update Report Generation to Display Backtesting Properly
  - Modify report crew task to use enhanced backtesting extractor
  - Display actual metric values when available
  - Display "Not calculated" for None values (not "Données non disponibles")
  - Include explanation when metrics are incomplete
  - Add backtesting status to data availability summary
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 9. Implement Data Availability Tracker
  - Create `src/finwiz/integration/data_availability_tracker.py` with DataAvailabilityTracker class
  - Implement `track_data_source()` to record source status and age
  - Implement `get_availability_summary()` to generate summary
  - Implement `get_freshness_warnings()` to identify stale data (>7 days)
  - Track all data sources: sentiment, SEC, portfolio, discovery, backtesting
  - Calculate data age in hours
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 10. Integrate Data Availability Tracker into Report Generation
  - Add DataAvailabilityTracker to report crew
  - Track each data source as it's accessed
  - Generate data availability summary section in report
  - Include freshness warnings for stale data
  - List which sources provided data vs. which failed
  - Add data availability summary to report footer
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 11. Update Report Crew Task Configuration
  - Modify `src/finwiz/crews/report_crew/config/tasks.yaml`
  - Add instructions to use new data accessors and validators
  - Add instructions to display "Data not available" instead of generating fake data
  - Add instructions to include data availability summary
  - Add instructions to show freshness warnings
  - Remove any instructions that encourage data generation
  - _Requirements: 1.1, 1.2, 1.3, 2.5, 4.5, 6.1, 6.2_

- [x] 12. Add Integration Tests for Data Quality
  - Create `tests/integration/test_report_data_quality.py`
  - Test report generation with missing sentiment data
  - Test report generation with missing SEC filings
  - Test report generation with incomplete portfolio
  - Test report generation without discovery results
  - Test report generation with incomplete backtesting
  - Verify no hallucinated data in any scenario
  - _Requirements: 1.1, 1.2, 1.3, 2.5, 3.5, 4.5, 5.5, 6.1_

- [x] 13. Add Unit Tests for New Components
  - Create `tests/unit/tools/test_sec_filing_url_generator.py`
  - Create `tests/unit/orchestrators/test_portfolio_holdings_processor.py`
  - Create `tests/unit/integration/test_aplus_discovery_accessor.py`
  - Create `tests/unit/integration/test_data_availability_tracker.py`
  - Test each component with valid and invalid inputs
  - Test error handling for each failure scenario
  - _Requirements: All_

- [x] 14. Update Documentation
  - Update `docs/API_REFERENCE.md` with new components
  - Update `docs/DEVELOPER_GUIDE.md` with data quality standards
  - Create `docs/DATA_QUALITY_GUIDE.md` with best practices
  - Document how to handle missing data
  - Document data availability tracking
  - _Requirements: All_

---

## Notes

- **No Post-Processing**: All fixes are at the data source level
- **Transparency**: Always communicate when data is unavailable
- **No Hallucinations**: Never generate fake data to fill gaps
- **Complete Processing**: Process all available data, even if validation fails
- **Traceability**: Log all data decisions and rejections

## Success Criteria

- Zero hallucinated URLs in generated reports
- All SEC URLs return 200 status codes or show "Not available"
- Portfolio review includes 100% of holdings from CSV files
- A+ opportunities displayed when discovery runs, clear message when not
- Backtesting metrics complete or clearly marked as "Not calculated"
- Data availability summary included in all reports
- All tests passing
