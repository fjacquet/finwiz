# Requirements Document

## Introduction

This specification addresses the need for immediate, high-impact improvements to the FinWiz codebase that enhance code quality, maintainability, and CrewAI compliance. The Quick Wins Implementation focuses on five key areas: tool factory standardization, final reporter enforcement, async task decorators, type hint coverage, and standardized logging. These improvements are designed to be implemented quickly (2-3 days) while providing significant benefits to code consistency, developer experience, and system reliability.

The implementation follows FinWiz's core principles of modular architecture, strict validation, and CrewAI best practices. Each quick win is independent and can be implemented incrementally, allowing for continuous testing and validation.

## Requirements

### Requirement 1: Tool Factory Standardization

**User Story:** As a developer maintaining FinWiz crews, I want a standardized way to initialize tools across all crews, so that tool configuration is consistent, centralized, and easier to maintain.

#### Acceptance Criteria

1. WHEN a tool factory module is created THEN it SHALL provide factory functions for stock, crypto, and ETF crew tools
2. WHEN a factory function is called THEN it SHALL return a list of BaseTool instances configured for the specific crew type
3. WHEN factory functions are implemented THEN they SHALL accept optional parameters for RAG tools, quantitative tools, and collection suffixes
4. IF a crew needs tools THEN it SHALL use the appropriate factory function instead of manual tool initialization
5. WHEN tools are initialized via factory THEN they SHALL include core research tools, optional quantitative tools, optional RAG tools, and schema/contract tools
6. WHEN the tool factory is implemented THEN all existing crews (stock, crypto, ETF) SHALL be updated to use factory functions
7. WHEN factory functions are used THEN the system SHALL maintain backward compatibility with existing crew functionality
8. WHEN changes are complete THEN unit tests SHALL verify that crews receive correct tool sets

### Requirement 2: Final Reporter Enforcement

**User Story:** As a FinWiz architect, I want to enforce that final reporter agents never receive tools, so that the system maintains proper separation of concerns and prevents accidental violations of design principles.

#### Acceptance Criteria

1. WHEN a final reporter decorator is created THEN it SHALL validate that agents have no tools at initialization time
2. IF a final reporter agent is created with tools THEN the system SHALL raise a FinalReporterError with a clear message
3. WHEN a final reporter agent is created without tools THEN the decorator SHALL allow creation and log validation success
4. WHEN the decorator is implemented THEN it SHALL be applied to all final reporter agents (investment_reporter, translator)
5. WHEN the decorator is applied THEN it SHALL use functools.wraps to preserve function metadata
6. WHEN validation fails THEN the error message SHALL include the agent role and number of tools found
7. WHEN the enforcement is complete THEN unit tests SHALL verify both success and failure cases
8. WHEN tests run THEN they SHALL confirm that reporters with no tools pass and reporters with tools fail

### Requirement 3: Async Task Decorators

**User Story:** As a developer working with CrewAI tasks, I want explicit decorators to mark tasks as async or sync, so that execution patterns are consistent and final tasks are correctly configured as synchronous.

#### Acceptance Criteria

1. WHEN task decorator module is created THEN it SHALL provide both async_task and sync_task decorators
2. WHEN async_task decorator is applied THEN it SHALL set task.async_execution to True
3. WHEN sync_task decorator is applied THEN it SHALL set task.async_execution to False
4. WHEN decorators are applied THEN they SHALL log the configuration for debugging purposes
5. WHEN decorators are implemented THEN they SHALL be applied to all tasks across all crews (stock, crypto, ETF, report)
6. WHEN tasks are decorated THEN parallel tasks SHALL use async_task and final tasks SHALL use sync_task
7. WHEN decorators are used THEN they SHALL preserve function metadata using functools.wraps
8. WHEN implementation is complete THEN unit tests SHALL verify that decorators correctly set async_execution property

### Requirement 4: Type Hint Coverage

**User Story:** As a developer maintaining FinWiz code, I want comprehensive type hints on all public functions, so that I get better IDE support, catch errors early, and have self-documenting code.

#### Acceptance Criteria

1. WHEN mypy is configured THEN it SHALL enforce type hints on all public functions
2. WHEN mypy configuration is created THEN it SHALL set python_version to 3.10 and enable strict checking
3. WHEN mypy runs THEN it SHALL ignore missing imports for third-party libraries (crewai, crewai_tools, dotenv)
4. WHEN type hints are added THEN they SHALL use modern Python 3.10+ syntax (str | None instead of Optional[str])
5. WHEN functions are updated THEN return types SHALL be explicitly specified for all public functions
6. WHEN type hints are added THEN they SHALL include parameter types and return types
7. WHEN implementation is complete THEN mypy SHALL run without errors on updated modules
8. WHEN type hints are added THEN they SHALL improve IDE autocomplete and error detection

### Requirement 5: Standardized Logging

**User Story:** As a developer debugging FinWiz crews, I want consistent structured logging across all crews, so that I can easily track execution flow, measure performance, and diagnose issues.

#### Acceptance Criteria

1. WHEN logging helper module is created THEN it SHALL provide a CrewLogger class for standardized logging
2. WHEN CrewLogger is initialized THEN it SHALL accept a crew_name parameter and create a logger instance
3. WHEN log_start is called THEN it SHALL log crew execution start with crew name, input keys, and event type
4. WHEN log_complete is called THEN it SHALL log execution completion with duration in seconds
5. WHEN log_error is called THEN it SHALL log errors with crew name, error type, and full exception info
6. WHEN CrewLogger is implemented THEN all crews SHALL be updated to use it in their kickoff methods
7. WHEN crews use CrewLogger THEN they SHALL track execution time and log start, complete, or error events
8. WHEN logging is standardized THEN log entries SHALL include structured extra fields for parsing and analysis

## Success Criteria

The Quick Wins Implementation will be considered successful when:

1. All five quick wins are implemented and tested
2. Code consistency improves from 60% to 90%
3. Type coverage improves from 40% to 80%
4. All unit tests pass without regression
5. CrewAI compliance improves from 85% to 95%
6. Developer experience is enhanced through better tooling and consistency
7. Documentation is updated to reflect new patterns
8. The codebase is ready for larger refactoring efforts in subsequent phases
