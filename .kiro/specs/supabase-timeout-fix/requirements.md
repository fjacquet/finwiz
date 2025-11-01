# Requirements Document: Supabase Timeout Fix

## Introduction

The Supabase integration is experiencing 100% timeout failures on all database operations, causing the circuit breaker to open and preventing any caching functionality. This document defines requirements to make Supabase completely optional and ensure graceful degradation when unavailable.

## Glossary

- **Supabase**: PostgreSQL database service used for caching analysis results
- **Circuit Breaker**: Pattern that prevents repeated failed operations
- **Graceful Degradation**: System continues functioning when optional components fail
- **Timeout**: Maximum time allowed for a database operation before failing

## Requirements

### Requirement 1: Graceful Degradation

**User Story:** As a FinWiz user, I want the system to work normally even when Supabase is unavailable, so that I can still get portfolio analysis results.

#### Acceptance Criteria

1. WHEN Supabase operations timeout, THE System SHALL continue analysis without caching
2. WHEN Supabase is unavailable, THE System SHALL log warnings but not errors
3. WHEN all Supabase operations fail, THE System SHALL complete the full analysis workflow
4. WHEN circuit breaker opens, THE System SHALL stop attempting Supabase operations
5. THE System SHALL NOT block or delay analysis waiting for Supabase responses

### Requirement 2: Timeout Configuration

**User Story:** As a system administrator, I want configurable timeouts for Supabase operations, so that I can tune performance based on network conditions.

#### Acceptance Criteria

1. THE System SHALL support SUPABASE_TIMEOUT_SECONDS environment variable
2. THE System SHALL default to 10 seconds for read operations
3. THE System SHALL default to 15 seconds for write operations  
4. WHEN timeout is reached, THE System SHALL log the timeout and continue
5. THE System SHALL NOT retry timed-out operations more than 3 times

### Requirement 3: Initialization Validation

**User Story:** As a developer, I want to validate Supabase connectivity at startup, so that I know immediately if caching will work.

#### Acceptance Criteria

1. WHEN System starts, THE System SHALL test Supabase connectivity with a simple query
2. WHEN connectivity test fails, THE System SHALL log a warning and disable caching
3. WHEN connectivity test succeeds, THE System SHALL enable caching features
4. THE System SHALL complete startup within 5 seconds regardless of Supabase status
5. THE System SHALL NOT fail startup if Supabase is unavailable

### Requirement 4: Monitoring and Metrics

**User Story:** As a system administrator, I want visibility into Supabase performance, so that I can diagnose connectivity issues.

#### Acceptance Criteria

1. THE System SHALL log Supabase operation success/failure rates
2. THE System SHALL track average response times for Supabase operations
3. WHEN circuit breaker opens, THE System SHALL log the failure count and reason
4. THE System SHALL expose Supabase health status via metrics endpoint
5. THE System SHALL log Supabase configuration (URL, timeout settings) at startup

### Requirement 5: Fallback Behavior

**User Story:** As a FinWiz user, I want consistent analysis results whether caching works or not, so that I can trust the recommendations.

#### Acceptance Criteria

1. WHEN cache is unavailable, THE System SHALL perform full analysis for all holdings
2. WHEN cache read fails, THE System SHALL proceed with fresh analysis
3. WHEN cache write fails, THE System SHALL complete analysis and log the failure
4. THE System SHALL NOT use stale cached data older than 24 hours
5. THE System SHALL provide the same analysis quality with or without caching
