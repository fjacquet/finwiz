# Requirements Document: Flow Resilience and Recovery

## Introduction

This feature adds comprehensive resilience, recovery, and checkpoint capabilities to the FinWiz flow orchestrator. Currently, when the flow encounters connection failures or errors during deep analysis of portfolio holdings, the entire process fails and must be restarted from scratch. This results in wasted API calls, lost progress, and poor user experience.

The flow resilience and recovery feature will enable the system to:
- Automatically retry failed operations with intelligent backoff strategies
- Save progress checkpoints to disk for recovery after failures
- Resume interrupted flows from the last successful checkpoint
- Handle partial failures gracefully without stopping the entire flow
- Provide detailed progress tracking and monitoring
- Implement timeout management to prevent indefinite hangs

This feature is critical for production reliability, especially when analyzing large portfolios (50+ holdings) where the probability of at least one failure approaches 100%.

## Requirements

### Requirement 1: Automatic Retry with Exponential Backoff

**User Story:** As a FinWiz user, I want the system to automatically retry failed operations so that transient network issues don't cause my entire analysis to fail.

#### Acceptance Criteria

1. WHEN a crew execution fails with a retryable error (connection timeout, rate limit, 5xx server error) THEN the system SHALL retry the operation with exponential backoff
2. WHEN retrying an operation THEN the system SHALL use exponential backoff with configurable base delay (default: 2 seconds), multiplier (default: 2), and maximum delay (default: 60 seconds)
3. WHEN retrying an operation THEN the system SHALL add jitter (random delay variation) to prevent thundering herd problems
4. WHEN the maximum retry count is reached (default: 3 attempts) THEN the system SHALL mark the operation as failed and continue with graceful degradation
5. IF an error is non-retryable (invalid ticker, authentication failure, validation error) THEN the system SHALL NOT retry and SHALL immediately mark as failed
6. WHEN retrying THEN the system SHALL log each retry attempt with attempt number, delay, and error details
7. WHEN all retries are exhausted THEN the system SHALL log a final error message with full context for debugging

### Requirement 2: Progress Checkpointing with CrewAI Flow State Persistence

**User Story:** As a FinWiz user, I want the system to save progress periodically using CrewAI's native state persistence so that if the analysis is interrupted, I don't lose all my work and API quota.

#### Acceptance Criteria

1. WHEN implementing checkpointing THEN the system SHALL use CrewAI's `@persist()` decorator for automatic state persistence
2. WHEN defining flow state THEN the system SHALL use a structured Pydantic model (not unstructured dict) for type safety and validation
3. WHEN a holding analysis completes successfully THEN the system SHALL persist the flow state containing: timestamp, ticker, asset_class, analysis result, holdings_processed count, holdings_remaining count, and error tracking
4. WHEN saving state THEN the system SHALL leverage CrewAI's built-in atomic file operations to prevent corruption
5. WHEN state is persisted THEN the system SHALL use CrewAI's default storage mechanism with the flow's unique UUID for identification
6. WHEN multiple flow executions exist THEN the system SHALL use CrewAI's state management to track each execution independently by UUID
7. WHEN state persistence fails THEN the system SHALL log the error but continue execution (persistence failure is not fatal)

### Requirement 3: Flow Resume Capability with CrewAI State Loading

**User Story:** As a FinWiz user, I want to resume an interrupted analysis from where it left off using CrewAI's state loading so that I don't waste time and API quota re-analyzing holdings that already succeeded.

#### Acceptance Criteria

1. WHEN starting the application THEN the system SHALL check for existing persisted flow states in the CrewAI storage directory
2. IF one or more persisted states exist THEN the system SHALL display a list of available sessions with: UUID, age, progress (holdings processed/total), and last update timestamp
3. IF valid persisted state exists and is less than 24 hours old THEN the system SHALL prompt the user with options: "Resume", "Start Fresh", or "Cancel"
4. WHEN the user selects "Resume" THEN the system SHALL load the selected flow state using CrewAI's state loading mechanism
5. WHEN resuming from persisted state THEN the system SHALL use conditional `@start()` methods to skip already-completed holdings based on state
6. WHEN resuming THEN the system SHALL log which holdings are being skipped (already completed) and which remain to be analyzed
7. WHEN the user selects "Start Fresh" THEN the system SHALL create a new flow instance with a new UUID and ignore existing state
8. IF persisted state is older than 24 hours THEN the system SHALL warn the user and recommend starting fresh but still allow resume
9. IF persisted state is incompatible or corrupted THEN the system SHALL log an error, display the issue to the user, and automatically start a fresh execution
10. WHEN resume is complete THEN the system SHALL merge persisted results with new results into a unified output
11. WHEN the flow completes successfully THEN the system SHALL optionally clean up the persisted state file (configurable via FINWIZ_CLEANUP_STATE_ON_SUCCESS)
12. WHEN the user provides a specific UUID via CLI argument (--resume-uuid) THEN the system SHALL attempt to resume that specific session without prompting

### Requirement 4: Graceful Degradation for Partial Failures

**User Story:** As a FinWiz user, I want the system to continue analyzing other holdings even if one holding fails, so that I get partial results rather than complete failure.

#### Acceptance Criteria

1. WHEN a holding analysis fails after all retries THEN the system SHALL mark that holding as failed and continue with remaining holdings
2. WHEN a holding fails THEN the system SHALL use baseline analysis data as a fallback if available
3. WHEN using fallback data THEN the system SHALL mark the result with a confidence flag indicating degraded quality
4. WHEN the flow completes THEN the system SHALL provide a summary showing: successful analyses, failed analyses, and fallback analyses
5. WHEN failures occur THEN the system SHALL include a detailed error report with ticker, error type, and suggested remediation
6. IF more than 50% of holdings fail THEN the system SHALL log a critical warning suggesting investigation of systemic issues
7. WHEN the flow completes with partial failures THEN the system SHALL still generate a portfolio review using available data

### Requirement 5: Timeout Management

**User Story:** As a FinWiz user, I want the system to enforce timeouts on long-running operations so that a single stuck analysis doesn't block the entire flow indefinitely.

#### Acceptance Criteria

1. WHEN analyzing a single holding THEN the system SHALL enforce a configurable timeout (default: 5 minutes)
2. IF a holding analysis exceeds the timeout THEN the system SHALL cancel the operation and mark it as failed
3. WHEN a timeout occurs THEN the system SHALL log the timeout with ticker, duration, and last known state
4. WHEN a timeout occurs THEN the system SHALL attempt graceful cancellation before forcing termination
5. WHEN the entire flow is running THEN the system SHALL enforce a global timeout (default: 2 hours)
6. IF the global timeout is reached THEN the system SHALL save a checkpoint and terminate gracefully
7. WHEN timeouts are configured THEN the system SHALL validate that per-holding timeout is less than global timeout

### Requirement 6: Progress Tracking and Monitoring

**User Story:** As a FinWiz user, I want to see real-time progress updates during analysis so that I know the system is working and can estimate completion time.

#### Acceptance Criteria

1. WHEN the flow starts THEN the system SHALL display total holdings count and estimated completion time
2. WHEN each holding completes THEN the system SHALL update progress with: holdings completed, holdings remaining, success rate, and estimated time remaining
3. WHEN progress updates are displayed THEN the system SHALL show: ticker, status (success/failed/timeout), execution time, and grade (if successful)
4. WHEN the flow is running THEN the system SHALL update progress at least every 10 seconds
5. WHEN failures occur THEN the system SHALL update the progress display to show failure count and types
6. WHEN the flow completes THEN the system SHALL display a final summary with: total time, success rate, failure breakdown, and performance metrics
7. WHEN progress is tracked THEN the system SHALL calculate and display: average time per holding, API calls per holding, and cache hit rate

### Requirement 7: Configuration Management (Leverage Existing Infrastructure)

**User Story:** As a FinWiz developer, I want to configure resilience parameters via environment variables using the existing configuration patterns so that I can tune behavior for different environments without code changes.

#### Acceptance Criteria

1. WHEN the system starts THEN the system SHALL load resilience configuration from environment variables using existing `os.getenv()` patterns with sensible defaults
2. WHEN configuring retry behavior THEN the system SHALL support: `FINWIZ_MAX_RETRIES` (default: 3), `FINWIZ_RETRY_BASE_DELAY` (default: 2), `FINWIZ_RETRY_MAX_DELAY` (default: 60)
3. WHEN configuring timeouts THEN the system SHALL support: `FINWIZ_HOLDING_TIMEOUT` (default: 300), `FINWIZ_FLOW_TIMEOUT` (default: 7200)
4. WHEN configuring resume behavior THEN the system SHALL support: `FINWIZ_AUTO_RESUME` (default: false), `FINWIZ_STATE_MAX_AGE_HOURS` (default: 24)
5. WHEN configuring state persistence THEN the system SHALL use CrewAI's default persistence location (no custom directory needed)
6. WHEN invalid configuration is provided THEN the system SHALL follow existing patterns (log warning, use defaults) as seen in `portfolio_review.py`
7. WHEN configuration is loaded THEN the system SHALL log all active resilience settings using existing logger infrastructure

### Requirement 8: Integration with Existing Parallelization and CrewAI Flow State

**User Story:** As a FinWiz developer, I want resilience features to work seamlessly with the existing parallel processing implementation and CrewAI Flow state management so that I get both speed and reliability.

#### Acceptance Criteria

1. WHEN parallel processing is enabled THEN retry logic SHALL apply to each parallel task independently
2. WHEN parallel processing is enabled THEN flow state SHALL be persisted using `@persist()` after each batch completes
3. WHEN resuming with parallel processing THEN the system SHALL use flow state to skip entire batches that completed successfully
4. WHEN a parallel batch has partial failures THEN the system SHALL track failures in flow state and retry only the failed holdings
5. WHEN parallel processing is enabled THEN timeout management SHALL apply to individual holdings, not the entire batch
6. WHEN parallel processing is enabled THEN progress tracking SHALL update flow state with per-batch and overall progress
7. WHEN parallel processing is enabled THEN the system SHALL respect concurrency limits while retrying failed operations
8. WHEN updating flow state from parallel tasks THEN the system SHALL use thread-safe operations to prevent race conditions

### Requirement 9: Error Classification and Reporting (Extend Existing ValidationError)

**User Story:** As a FinWiz user, I want clear error messages that explain what went wrong and what I can do about it, leveraging the existing ValidationError infrastructure.

#### Acceptance Criteria

1. WHEN an error occurs THEN the system SHALL classify it using existing `ValidationError` structure with `error_type` field: retryable (network, rate_limit, timeout), non-retryable (validation, authentication), or unknown
2. WHEN reporting errors THEN the system SHALL use `ValidationError.context` to include: ticker, timestamp, retry_count, and suggested remediation
3. WHEN multiple errors occur THEN the system SHALL use `ValidationResult` to collect and group errors by type in the final report
4. WHEN network errors occur THEN the system SHALL add remediation context suggesting checking connectivity and API status
5. WHEN rate limit errors occur THEN the system SHALL add remediation context suggesting reducing parallelism or increasing delays
6. WHEN authentication errors occur THEN the system SHALL add remediation context suggesting checking API keys
7. WHEN validation errors occur THEN the system SHALL add remediation context suggesting checking ticker symbols and input data

### Requirement 10: Monitoring and Observability (Integrate with Existing AlertManager)

**User Story:** As a FinWiz operator, I want detailed metrics and logs about flow execution integrated with the existing monitoring infrastructure so that I can monitor system health and diagnose issues.

#### Acceptance Criteria

1. WHEN the flow executes THEN the system SHALL track key metrics in flow state: total execution time, holdings processed, success rate, retry count, timeout count, persistence operations
2. WHEN the flow completes THEN the system SHALL calculate and log performance metrics from flow state: average time per holding, API calls per holding, cache hit rate, speedup from parallelization
3. WHEN errors occur THEN the system SHALL store structured error data in flow state using existing `ValidationError` format for consistency
4. WHEN critical failures occur (>50% failure rate) THEN the system SHALL integrate with existing `AlertManager` to send alerts via configured channels
5. WHEN retries occur THEN the system SHALL track retry metrics in flow state: total retries, retries per error type, average retry delay
6. WHEN the flow completes THEN the system SHALL export flow state metrics to a JSON file compatible with existing monitoring dashboards
7. WHEN monitoring is enabled THEN the system SHALL use existing `get_logger()` infrastructure for consistent logging across the codebase

---

**Version**: 1.0  
**Created**: 2025-01-11  
**Purpose**: Enable robust, production-ready flow execution with automatic recovery from failures
