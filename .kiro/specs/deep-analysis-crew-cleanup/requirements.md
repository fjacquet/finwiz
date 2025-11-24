# Requirements Document: Deep Analysis Crew Cleanup

## Introduction

The DeepAnalysisCrew is failing in production with a `KeyError: 'risk_assessor'` error. This is caused by deprecated agent code that references a `risk_assessor` agent configuration that no longer exists in `agents.yaml`. 

The Python/AI Hybrid Analysis refactoring simplified the crew to use only two agents (`asset_analyst` and `investment_reporter`), but the deprecated `risk_assessor` agent method was not fully removed, causing runtime errors when the crew is instantiated.

## Glossary

- **DeepAnalysisCrew**: CrewAI crew for analyzing portfolio holdings with qualitative insights
- **risk_assessor**: Deprecated agent that was removed during Python/AI Hybrid refactoring
- **asset_analyst**: Current agent responsible for qualitative analysis
- **investment_reporter**: Current agent responsible for consolidating results
- **agents.yaml**: Configuration file defining agent roles, goals, and backstories

## Requirements

### Requirement 1: Remove Deprecated Agent Code

**User Story:** As a developer, I want deprecated agent code removed, so that the crew doesn't fail with KeyError exceptions.

#### Acceptance Criteria

1. WHEN the DeepAnalysisCrew is instantiated THEN the system SHALL NOT reference the risk_assessor agent
2. WHEN checking agent methods THEN the system SHALL only include asset_analyst and investment_reporter
3. WHEN the crew runs THEN the system SHALL NOT attempt to access risk_assessor configuration
4. WHEN reviewing code comments THEN deprecated agent references SHALL be removed
5. THE system SHALL successfully instantiate and run the DeepAnalysisCrew without KeyError

### Requirement 2: Verify Crew Functionality

**User Story:** As a system administrator, I want to verify the crew works after cleanup, so that production analysis can proceed.

#### Acceptance Criteria

1. WHEN running deep analysis on a holding THEN the system SHALL complete without errors
2. WHEN checking agent list THEN the crew SHALL contain exactly 2 agents (asset_analyst, investment_reporter)
3. WHEN reviewing logs THEN no deprecation warnings SHALL appear
4. WHEN testing with crypto ticker (BTC-USD) THEN the analysis SHALL complete successfully
5. THE system SHALL maintain all existing functionality with the simplified 2-agent architecture

---

**Version**: 1.0  
**Created**: 2025-01-22  
**Status**: New - Production Bug Fix
