# Requirements Document

## Introduction

This specification defines the integration of Supabase as the centralized data persistence and vector storage layer for FinWiz. The integration will enable historical analysis storage, semantic search capabilities, portfolio evolution tracking, and RAG-enhanced AI agents with access to past analyses.

## Glossary

- **Supabase**: Open-source Firebase alternative providing PostgreSQL database, vector storage (pgvector), and real-time subscriptions
- **Vector Embedding**: Numerical representation of text/data in multi-dimensional space for semantic similarity search
- **RAG (Retrieval-Augmented Generation)**: Pattern combining LLM with knowledge retriever to provide context and reduce hallucinations
- **pgvector**: PostgreSQL extension for vector similarity search
- **Analysis Cache**: Stored analysis results that can be reused to avoid redundant crew executions
- **Portfolio Snapshot**: Point-in-time record of portfolio holdings and their analysis results
- **Semantic Search**: Search based on meaning/context rather than exact keyword matching
- **Data Lineage**: Complete traceability of data from source to final output

## Requirements

### Requirement 1: Database Schema and Connection Management

**User Story:** As a FinWiz developer, I want a robust database schema and connection management system, so that all analysis data is reliably stored and retrievable.

#### Acceptance Criteria

1. WHEN the application starts, THE System SHALL establish a connection to Supabase using environment variables for credentials
2. WHEN the connection is established, THE System SHALL validate the database schema exists and is up-to-date
3. WHEN schema validation fails, THE System SHALL log detailed error messages and fail gracefully
4. WHERE connection pooling is enabled, THE System SHALL manage connection lifecycle with automatic retry logic
5. WHEN database operations fail, THE System SHALL implement exponential backoff retry strategy with maximum 3 attempts

### Requirement 2: Analysis Storage and Retrieval

**User Story:** As a FinWiz user, I want all my analysis results stored in a database, so that I can access historical analyses and avoid redundant computations.

#### Acceptance Criteria

1. WHEN a crew completes an analysis, THE System SHALL store the complete analysis result in the database with timestamp
2. WHEN storing an analysis, THE System SHALL include ticker, asset_class, composite_score, grade, recommendation, and full JSON export
3. WHEN retrieving an analysis, THE System SHALL check if a recent analysis exists (within configurable TTL, default 24 hours)
4. IF a recent analysis exists, THEN THE System SHALL return the cached result instead of executing the crew
5. WHEN multiple analyses exist for the same ticker, THE System SHALL return the most recent analysis by timestamp

### Requirement 3: Vector Embeddings and Semantic Search

**User Story:** As a FinWiz user, I want to search for similar analyses using natural language queries, so that I can find relevant historical insights quickly.

#### Acceptance Criteria

1. WHEN an analysis is stored, THE System SHALL generate vector embeddings for the analysis description and key findings
2. WHEN generating embeddings, THE System SHALL use OpenAI text-embedding-3-small model with 1536 dimensions
3. WHEN a user queries for similar analyses, THE System SHALL convert the query to embeddings and perform vector similarity search
4. WHEN performing vector search, THE System SHALL return the top 5 most similar analyses with similarity scores
5. WHERE similarity score is below 0.7, THE System SHALL exclude results as not sufficiently similar

### Requirement 4: Portfolio Evolution Tracking

**User Story:** As a FinWiz user, I want to track how my portfolio evolves over time, so that I can understand the impact of recommendations and decisions.

#### Acceptance Criteria

1. WHEN a portfolio analysis completes, THE System SHALL create a portfolio snapshot with timestamp and all holdings
2. WHEN creating a snapshot, THE System SHALL store each holding's ticker, quantity, current_value, grade, and recommendation
3. WHEN retrieving portfolio history, THE System SHALL return all snapshots ordered by timestamp descending
4. WHEN comparing snapshots, THE System SHALL calculate changes in holdings, grades, and total portfolio value
5. WHERE a holding appears in multiple snapshots, THE System SHALL track its grade evolution over time

### Requirement 5: RAG-Enhanced AI Agents

**User Story:** As a FinWiz developer, I want AI agents to access historical analyses through RAG, so that recommendations are grounded in past data and reduce hallucinations.

#### Acceptance Criteria

1. WHEN an agent needs context, THE System SHALL query the vector database for relevant historical analyses
2. WHEN retrieving context, THE System SHALL include the top 3 most similar analyses in the agent's prompt
3. WHEN no similar analyses exist, THE System SHALL proceed without RAG context and log the absence
4. WHERE RAG context is provided, THE Agent SHALL cite the historical analyses in its recommendations
5. WHEN RAG retrieval fails, THE System SHALL fall back to standard analysis without historical context

### Requirement 6: Analysis Cache Management

**User Story:** As a FinWiz user, I want intelligent caching of expensive analyses, so that I avoid redundant crew executions and reduce costs.

#### Acceptance Criteria

1. WHEN checking for cached analysis, THE System SHALL consider ticker, asset_class, and analysis_type as cache keys
2. WHEN a cached analysis is found, THE System SHALL validate it is within the TTL (default 24 hours)
3. IF cached analysis is expired, THEN THE System SHALL execute a new analysis and update the cache
4. WHEN cache hit occurs, THE System SHALL log the cache hit and return results in under 1 second
5. WHERE cache is disabled via configuration, THE System SHALL always execute fresh analyses

### Requirement 7: Data Migration and Backward Compatibility

**User Story:** As a FinWiz developer, I want to migrate existing file-based data to Supabase, so that historical analyses are preserved and accessible.

#### Acceptance Criteria

1. WHEN migration is triggered, THE System SHALL scan the output directory for existing JSON exports
2. WHEN processing exports, THE System SHALL validate each export against Pydantic schemas before storage
3. IF validation fails, THEN THE System SHALL log the error and skip the invalid export
4. WHEN storing migrated data, THE System SHALL preserve original timestamps from file metadata
5. WHERE duplicate analyses exist, THE System SHALL keep the most recent version by timestamp

### Requirement 8: Performance and Scalability

**User Story:** As a FinWiz user, I want database operations to be fast and scalable, so that analysis performance is not degraded by persistence.

#### Acceptance Criteria

1. WHEN storing an analysis, THE System SHALL complete the database write in under 500 milliseconds
2. WHEN retrieving an analysis, THE System SHALL complete the database read in under 200 milliseconds
3. WHEN performing vector search, THE System SHALL return results in under 1 second for queries with up to 1000 stored analyses
4. WHERE database operations exceed timeout thresholds, THE System SHALL log performance warnings
5. WHEN database is unavailable, THE System SHALL fall back to file-based storage and continue analysis

### Requirement 8.1: Non-Blocking Asynchronous Operations

**User Story:** As a FinWiz user, I want database operations to never block analysis execution, so that Supabase integration cannot slow down or fail my analyses.

#### Acceptance Criteria

1. WHEN an analysis completes, THE System SHALL store results to Supabase asynchronously in a background task
2. WHEN background storage fails, THE System SHALL log the error but NOT fail the analysis
3. WHEN checking for cached analysis, THE System SHALL set a strict timeout of 2 seconds for database query
4. IF cache check times out, THEN THE System SHALL proceed with fresh analysis as if no cache exists
5. WHERE Supabase is unavailable, THE System SHALL detect this within 5 seconds and disable database operations for the session

### Requirement 8.2: Circuit Breaker Pattern

**User Story:** As a FinWiz developer, I want automatic circuit breaker protection, so that repeated database failures don't impact system performance.

#### Acceptance Criteria

1. WHEN database operations fail 3 consecutive times, THE System SHALL open the circuit breaker
2. WHILE circuit breaker is open, THE System SHALL skip all database operations and use file-based storage
3. WHEN circuit breaker is open for 5 minutes, THE System SHALL attempt to close it with a test query
4. IF test query succeeds, THEN THE System SHALL close the circuit breaker and resume database operations
5. WHERE circuit breaker opens, THE System SHALL log a warning but continue analysis without interruption

### Requirement 9: Security and Data Privacy

**User Story:** As a FinWiz user, I want my financial data to be securely stored and protected, so that sensitive information is not exposed.

#### Acceptance Criteria

1. WHEN connecting to Supabase, THE System SHALL use environment variables for credentials and never hardcode secrets
2. WHEN storing portfolio data, THE System SHALL encrypt sensitive fields (holdings, values) at rest
3. WHEN accessing data, THE System SHALL implement row-level security policies to restrict access
4. WHERE API keys are logged, THE System SHALL mask all but the first 8 characters
5. WHEN data is deleted, THE System SHALL perform soft deletes with retention policies

### Requirement 10: Monitoring and Observability

**User Story:** As a FinWiz developer, I want comprehensive monitoring of database operations, so that I can diagnose issues and optimize performance.

#### Acceptance Criteria

1. WHEN database operations execute, THE System SHALL log operation type, duration, and success/failure status
2. WHEN errors occur, THE System SHALL log detailed error messages with stack traces
3. WHEN cache hits occur, THE System SHALL track cache hit rate and log statistics
4. WHERE performance degrades, THE System SHALL emit warnings when operations exceed thresholds
5. WHEN vector search is performed, THE System SHALL log query text, result count, and similarity scores

## Constraints

- **Zero Impact on Analysis**: Supabase integration MUST NOT slow down or fail analyses
- **Asynchronous by Default**: All write operations must be non-blocking background tasks
- **Strict Timeouts**: Read operations have 2-second timeout, writes have 5-second timeout
- **Circuit Breaker**: Automatic protection after 3 consecutive failures
- **Graceful Degradation**: System must function perfectly without database
- **Optional Feature**: Supabase can be disabled via environment variable (SUPABASE_ENABLED=false)
- **Vector Embeddings**: Use OpenAI text-embedding-3-small (1536 dimensions) for consistency
- **Cache TTL**: Configurable via environment variable (default 24 hours)
- **Row-Level Security**: Database schema must support future multi-user access
- **Data Lineage**: All stored data must comply with lineage standards (source attribution, timestamps)
- **Idempotent Migration**: Running migration multiple times should not create duplicates
- **Performance Target**: Database operations should add < 500ms to analysis time (mostly async)

## Success Metrics

- **Zero Slowdown**: Analysis time with Supabase ≤ analysis time without Supabase + 500ms
- **Zero Failures**: Database issues cause 0% increase in analysis failures
- **Cache Hit Rate**: Target 40%+ cache hit rate for repeated analyses
- **Cost Reduction**: Reduce API costs by 30%+ through analysis reuse
- **Circuit Breaker**: < 5 seconds to detect and disable failing database
- **Reliability**: 99.9% uptime for database operations with graceful fallback
- **Adoption**: 100% of analyses stored in database within 1 month of deployment
- **Search Quality**: Semantic search returns relevant results with 80%+ user satisfaction
- **Background Success**: 95%+ of async writes succeed without blocking analysis

---

**Version**: 1.0  
**Created**: 2025-10-30  
**Status**: Requirements Gathering
