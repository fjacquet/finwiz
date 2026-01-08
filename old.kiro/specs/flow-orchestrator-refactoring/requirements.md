# Requirements Document

## Introduction

The Flow Orchestrator (`src/finwiz/flows/flow_orchestrator.py`) has grown to 4426 lines with 30+ methods, making it difficult to maintain, test, and extend. This refactoring will decompose the monolithic orchestrator into focused, single-responsibility modules while maintaining complete backward compatibility.

## Glossary

- **Flow Orchestrator**: The main CrewAI Flow class that coordinates portfolio analysis workflows
- **Orchestrator Module**: A focused module responsible for a specific aspect of workflow orchestration
- **Re-export Layer**: A thin compatibility layer that maintains existing import paths
- **Flow Listener**: A method decorated with `@listen` that responds to Flow events
- **Crew Execution**: Running a CrewAI crew to perform analysis tasks
- **Deep Analysis**: Comprehensive analysis of individual portfolio holdings
- **Discovery Analysis**: Finding new investment opportunities across asset classes
- **Alternative Matching**: Finding A+ alternatives for underperforming holdings

## Requirements

### Requirement 1

**User Story:** As a developer, I want the Flow Orchestrator split into focused modules, so that I can understand, maintain, and test each component independently.

#### Acceptance Criteria

1. WHEN the refactoring is complete THEN the Flow Orchestrator SHALL contain no more than 400 lines of code
2. WHEN a new orchestrator module is created THEN the module SHALL contain no more than 400 lines of code
3. WHEN orchestrator modules are created THEN each module SHALL have a single, clearly defined responsibility
4. WHEN the refactoring is complete THEN all existing imports SHALL continue to work without modification
5. WHEN the refactoring is complete THEN all existing tests SHALL pass without modification

### Requirement 2

**User Story:** As a developer, I want error handling logic separated from business logic, so that I can modify error handling without affecting core functionality.

#### Acceptance Criteria

1. WHEN crew execution encounters an error THEN the ErrorHandlingOrchestrator SHALL handle the error gracefully
2. WHEN multiple errors occur THEN the ErrorHandlingOrchestrator SHALL aggregate errors into a summary
3. WHEN an error summary is generated THEN the ErrorHandlingOrchestrator SHALL provide actionable error information
4. WHEN crew execution succeeds THEN the ErrorHandlingOrchestrator SHALL return the crew result without modification

### Requirement 3

**User Story:** As a developer, I want deep analysis orchestration separated from the main Flow, so that I can modify deep analysis logic independently.

#### Acceptance Criteria

1. WHEN deep analysis is triggered THEN the DeepAnalysisOrchestrator SHALL execute analysis on all portfolio holdings
2. WHEN deep analysis completes THEN the DeepAnalysisOrchestrator SHALL create structured DeepAnalysisResult objects
3. WHEN batch prefetch is enabled THEN the DeepAnalysisOrchestrator SHALL use batch prefetch optimization
4. WHEN deep analysis completes THEN the DeepAnalysisOrchestrator SHALL save batch metrics to file
5. WHEN deep analysis results are created THEN the DeepAnalysisOrchestrator SHALL parse crew output correctly

### Requirement 4

**User Story:** As a developer, I want alternative matching logic separated from the main Flow, so that I can modify matching algorithms independently.

#### Acceptance Criteria

1. WHEN holdings have grades below B THEN the AlternativesMatchingOrchestrator SHALL find A+ alternatives
2. WHEN discovery analysis completes THEN the AlternativesMatchingOrchestrator SHALL match alternatives from discovery results
3. WHEN alternatives are matched THEN the AlternativesMatchingOrchestrator SHALL return Alternative objects with proper structure
4. WHEN no alternatives are found THEN the AlternativesMatchingOrchestrator SHALL return an empty list

### Requirement 5

**User Story:** As a developer, I want report generation logic separated from the main Flow, so that I can modify reporting without affecting analysis logic.

#### Acceptance Criteria

1. WHEN report generation is triggered THEN the ReportingOrchestrator SHALL consolidate all crew reports
2. WHEN crew reports are consolidated THEN the ReportingOrchestrator SHALL generate a final HTML report
3. WHEN HTML generation is triggered THEN the ReportingOrchestrator SHALL use Jinja2 templates for rendering
4. WHEN crew export paths are needed THEN the ReportingOrchestrator SHALL calculate and store paths correctly
5. WHEN report generation completes THEN the ReportingOrchestrator SHALL return the final report path

### Requirement 6

**User Story:** As a developer, I want discovery orchestration separated from the main Flow, so that I can modify discovery logic for each asset class independently.

#### Acceptance Criteria

1. WHEN crypto discovery is triggered THEN the DiscoveryOrchestrator SHALL execute the crypto discovery crew
2. WHEN stock discovery is triggered THEN the DiscoveryOrchestrator SHALL execute the stock discovery crew
3. WHEN ETF discovery is triggered THEN the DiscoveryOrchestrator SHALL execute the ETF discovery crew
4. WHEN all discovery crews complete THEN the DiscoveryOrchestrator SHALL consolidate discovery results
5. WHEN discovery execution fails THEN the DiscoveryOrchestrator SHALL handle errors gracefully

### Requirement 7

**User Story:** As a developer, I want validation logic separated from the main Flow, so that I can modify validation rules independently.

#### Acceptance Criteria

1. WHEN reporter input is validated THEN the ValidationOrchestrator SHALL check for required data availability
2. WHEN core analysis availability is checked THEN the ValidationOrchestrator SHALL verify all required analysis exists
3. WHEN market conditions are extracted THEN the ValidationOrchestrator SHALL parse market context from core analysis
4. WHEN market context is extracted THEN the ValidationOrchestrator SHALL return structured market condition data

### Requirement 8

**User Story:** As a developer, I want progress tracking logic separated from the main Flow, so that I can modify progress reporting independently.

#### Acceptance Criteria

1. WHEN workflow progress changes THEN the ProgressTrackingOrchestrator SHALL update progress metrics
2. WHEN batch metrics are available THEN the ProgressTrackingOrchestrator SHALL save metrics to file
3. WHEN progress is calculated THEN the ProgressTrackingOrchestrator SHALL provide percentage completion
4. WHEN progress updates occur THEN the ProgressTrackingOrchestrator SHALL log progress information

### Requirement 9

**User Story:** As a developer, I want utility functions separated from the main Flow, so that I can reuse and test utility logic independently.

#### Acceptance Criteria

1. WHEN crew output is parsed THEN the UtilityOrchestrator SHALL extract holding-specific data correctly
2. WHEN grade distribution is calculated THEN the UtilityOrchestrator SHALL aggregate grades across holdings
3. WHEN SEC filing URLs are extracted THEN the UtilityOrchestrator SHALL parse URLs from crew output
4. WHEN SEC URLs are validated THEN the UtilityOrchestrator SHALL fix malformed URLs automatically

### Requirement 10

**User Story:** As a developer, I want the refactored Flow Orchestrator to maintain backward compatibility, so that existing code continues to work without modification.

#### Acceptance Criteria

1. WHEN existing code imports from flow_orchestrator THEN the imports SHALL resolve successfully
2. WHEN Flow listeners are called THEN the listeners SHALL delegate to appropriate orchestrators
3. WHEN the refactored Flow is executed THEN the behavior SHALL match the original implementation
4. WHEN tests are run THEN all existing tests SHALL pass without modification
5. WHEN the refactored Flow is used THEN no breaking changes SHALL be introduced to the public API
