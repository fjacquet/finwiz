# Implementation Plan: Deep Analysis Crew Cleanup

## Overview

Quick bug fix to remove deprecated `risk_assessor` agent causing production KeyError.

---

## Tasks

- [x] 1. Remove deprecated risk_assessor agent method
  - Delete the `@agent` decorated `risk_assessor()` method from `src/finwiz/crews/deep_analysis/deep_analysis.py` (lines ~410-420)
  - _Requirements: 1.1, 1.3_

- [x] 2. Remove risk_assessor instantiation
  - Delete the line `risk_assessor_agent = self.risk_assessor()` from the crew setup (line ~571)
  - Remove any comments referencing risk_assessor as deprecated
  - _Requirements: 1.2, 1.4_

- [x] 3. Verify no other references exist
  - Search entire codebase for remaining `risk_assessor` references
  - Remove or update any found references
  - _Requirements: 1.5_

- [x] 4. Test crew instantiation and execution
  - Run unit test to verify crew instantiates without KeyError
  - Run integration test with BTC-USD ticker (the failing case from production)
  - Verify crew contains exactly 2 agents
  - Confirm no deprecation warnings in logs
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 5. Final validation
  - Run full test suite to ensure no regressions
  - Verify production scenario (deep analysis on crypto holding) works
  - Mark task complete
  - _Requirements: All_

---

**Estimated Total Time**: 25 minutes  
**Priority**: CRITICAL (Production Bug)  
**Status**: Ready to implement
