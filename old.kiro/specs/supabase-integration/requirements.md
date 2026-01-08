# Requirements Document

## Introduction

This specification defines the integration of Supabase as the centralized data persistence and vector storage layer for FinWiz. The integration will enable historical analysis storage, semantic search capabilities, portfolio evolution tracking, and RAG-enhanced AI agents with access to past analyses. The system must operate asynchronously with zero impact on analysis performance through circuit breaker protection and graceful degradation.

## Glossary

- **System**: The FinWiz application with Supabase integration
- **Supabase**: Open-source Firebase alternative providing PostgreSQL database, vector storage (pgvector), and real-time subscriptions
- **Vector Embedding**: Numerical representation of text/data in multi-dimensional space for semantic similarity search
- **RAG (Retrieval-Augmented Generation)**: Pattern combining LLM with knowledge retriever to provide context and reduce hallucinations
- **pgvector**: PostgreSQL extension for vector similarity search
- **Analysis Cache**: Stored analysis results that can be reused to avoid redundant crew executions
- **Portfolio Snapshot**: Point-in-time record of portfolio holdings and their analysis results
- **Semantic Search**: Search based on meaning/context rather than exact keyword matching
- **Data Lineage**: Complete traceability of data from source to final output
- **Circuit Breaker**: Protective mechanism that prevents repeated failed operations from impacting system performance
- **Background Task**: Asynchronous operation that executes without blocking the main analysis workflow
- **TTL (Time To Live)**: Duration for which cached data remains valid before requiring refresh
- **Connection Pool**: Managed set of reusable database connections that reduces overhead of creating new connections
- **Singleton Pattern**: Design pattern ensuring only one instance of a class exists throughout application lifecycle
- **Connection Lifecycle**: The stages of a database connection from creation through active use to closure
- **Supavisor**: Supabase's server-side connection pooler that manages database connections efficiently
- **Session Mode**: Connection pooling mode for persistent clients with long-lived connections
- **Transaction Mode**: Connection pooling mode for transient clients like serverless functions
- **Direct Connection**: Direct connection to Postgres database without pooling (IPv6 only)
- **Application-Side Pooler**: Connection pooling implemented within the application code

## Requirements

### Requirement 1: Database Schema and Connection Management

**User Story:** As a FinWiz developer, I want a robust database schema and connection management system, so that all analysis data is reliably stored and retrievable.

#### Acceptance Criteria

1. WHEN the application starts, THE System SHALL establish a connection to Supabase using environment variables for credentials
2. WHEN the connection is established, THE System SHALL validate the database schema exists and is current
3. IF schema validation fails, THEN THE System SHALL log detailed error messages and continue with file-based storage
4. WHEN database operations fail, THE System SHALL implement exponential backoff retry strategy with maximum 3 attempts
5. WHEN the application terminates, THE System SHALL close all database connections gracefully

### Requirement 1.1: Connection Pooling and Centralization

**User Story:** As a FinWiz developer, I want centralized connection pooling using Supabase best practices, so that database connections are efficiently managed and reused across the application.

#### Acceptance Criteria

1. WHEN the application initializes, THE System SHALL create a single centralized Supabase client instance using singleton pattern
2. WHERE the deployment is persistent (VM or container), THE System SHALL use Supavisor Session Mode connection string for IPv4 and IPv6 support
3. WHEN configuring application-side pooling, THE System SHALL set minimum 2 and maximum 10 connections in the pool
4. WHEN a database operation is requested, THE System SHALL reuse an existing connection from the pool instead of creating new connections
5. WHEN a connection remains idle for 300 seconds, THE System SHALL close the connection and remove it from the pool
6. IF the connection pool is exhausted, THEN THE System SHALL wait up to 5 seconds for an available connection before failing the operation

### Requirement 1.2: Connection String Management

**User Story:** As a FinWiz developer, I want proper connection string configuration, so that the system uses the optimal connection method for the deployment environment.

#### Acceptance Criteria

1. WHEN environment variables are loaded, THE System SHALL support SUPABASE_URL and SUPABASE_KEY for API access
2. WHERE direct database access is required, THE System SHALL support SUPABASE_DB_URL environment variable for connection string
3. WHEN SUPABASE_DB_URL is provided, THE System SHALL validate it matches Supavisor Session Mode format (port 5432)
4. IF no database URL is provided, THEN THE System SHALL fall back to Supabase API client without direct database access
5. WHEN SSL is available, THE System SHALL enforce SSL connections to prevent security vulnerabilities

### Requirement 1.3: Pooler Strategy Selection

**User Story:** As a FinWiz developer, I want the system to use the appropriate pooling strategy, so that connections are optimized for the deployment architecture.

#### Acceptance Criteria

1. WHERE FinWiz is deployed as a persistent service (VM or long-running container), THE System SHALL use application-side connection pooling with Supavisor Session Mode
2. WHEN application-side pooling is configured, THE System SHALL maintain hot connections to reduce connection establishment overhead
3. WHEN the pool size is configured, THE System SHALL ensure total backend connections do not exceed Postgres max_connections limit for the compute tier
4. IF connection pool health degrades, THEN THE System SHALL log warnings and attempt connection recycling
5. WHEN monitoring pool metrics, THE System SHALL track active connections, idle connections, and connection wait times

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

**User Story:** As a FinWiz user, I want database operations to never block analysis execution, so that Supabase integration does not slow down or fail my analyses.

#### Acceptance Criteria

1. WHEN an analysis completes, THE System SHALL store results to Supabase asynchronously in a background task
2. IF background storage fails, THEN THE System SHALL log the error without failing the analysis
3. WHEN checking for cached analysis, THE System SHALL enforce a timeout of 2 seconds for database query
4. IF cache check times out, THEN THE System SHALL proceed with fresh analysis without cached data
5. WHEN Supabase is unavailable, THE System SHALL detect this within 5 seconds and disable database operations for the session

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

1. WHEN connecting to Supabase, THE System SHALL retrieve credentials from environment variables without hardcoding secrets
2. WHEN storing portfolio data, THE System SHALL encrypt sensitive fields including holdings and values at rest
3. WHEN accessing data, THE System SHALL enforce row-level security policies to restrict unauthorized access
4. WHEN API keys are logged, THE System SHALL mask all characters except the first 8 characters
5. WHEN data is deleted, THE System SHALL perform soft deletes with configurable retention policies

### Requirement 10: Monitoring and Observability

**User Story:** As a FinWiz developer, I want comprehensive monitoring of database operations, so that I can diagnose issues and optimize performance.

#### Acceptance Criteria

1. WHEN database operations execute, THE System SHALL log operation type, duration, and completion status
2. WHEN errors occur, THE System SHALL log detailed error messages with complete stack traces
3. WHEN cache hits occur, THE System SHALL calculate cache hit rate and log aggregated statistics
4. WHEN performance degrades, THE System SHALL emit warnings for operations exceeding configured thresholds
5. WHEN vector search is performed, THE System SHALL log query text, result count, and similarity scores

## Technical Constraints

- **Zero Impact on Analysis**: Supabase integration MUST NOT slow down or fail analyses
- **Asynchronous by Default**: All write operations must execute as non-blocking background tasks
- **Strict Timeouts**: Read operations limited to 2 seconds, write operations limited to 5 seconds
- **Circuit Breaker**: Automatic protection activates after 3 consecutive failures
- **Graceful Degradation**: System must operate fully without database connectivity
- **Optional Feature**: Supabase can be disabled via SUPABASE_ENABLED environment variable
- **Vector Embeddings**: Use OpenAI text-embedding-3-small model with 1536 dimensions for consistency
- **Cache TTL**: Configurable via ANALYSIS_CACHE_TTL_HOURS environment variable with 24-hour default
- **Row-Level Security**: Database schema must support future multi-user access patterns
- **Data Lineage**: All stored data must include source attribution and timestamps per lineage standards
- **Idempotent Migration**: Migration process must handle duplicate executions without creating duplicate records
- **Performance Target**: Database operations must add less than 500 milliseconds to total analysis time
- **Connection Mode**: Use Supavisor Session Mode for persistent deployment (supports IPv4 and IPv6)
- **Connection Pool Size**: Application-side pool with minimum 2 connections, maximum 10 connections
- **Connection Idle Timeout**: Connections idle for 300 seconds must be closed automatically
- **Connection Wait Timeout**: Maximum 5 seconds wait time for available connection from exhausted pool
- **Singleton Client**: Only one Supabase client instance allowed per application lifecycle
- **SSL Required**: All database connections must use SSL encryption
- **Connection String Format**: Must use Supavisor Session Mode format (postgres://postgres.PROJECT:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres)

## Success Metrics

- **Zero Slowdown**: Analysis time with Supabase SHALL NOT exceed analysis time without Supabase by more than 500 milliseconds
- **Zero Failures**: Database issues SHALL cause zero percent increase in analysis failures
- **Cache Hit Rate**: System SHALL achieve minimum 40 percent cache hit rate for repeated analyses
- **Cost Reduction**: System SHALL reduce API costs by minimum 30 percent through analysis reuse
- **Circuit Breaker Response**: System SHALL detect and disable failing database within 5 seconds
- **Reliability**: Database operations SHALL maintain 99.9 percent uptime with graceful fallback
- **Adoption**: System SHALL store 100 percent of analyses in database within 1 month of deployment
- **Search Quality**: Semantic search SHALL return relevant results with minimum 80 percent user satisfaction
- **Background Success**: System SHALL complete minimum 95 percent of async writes successfully without blocking analysis

## Known Issues

### Connectivity Timeout During Initialization

**Issue**: The test_connectivity() method times out when called during full portfolio analysis initialization, despite working correctly in isolation.

**Root Causes**:
- Thread pool contention during concurrent portfolio analysis startup operations
- Synchronous create_client() call blocking the async event loop
- Network timing conflicts when connectivity test executes during high-activity periods

**Current Workaround**: Supabase integration disabled via SUPABASE_ENABLED=false environment variable to allow portfolio analysis to proceed without timeout issues. Analysis continues with file-based storage.

**Future Resolution**:

1. Implement centralized connection pooling with singleton pattern (Requirement 1.1)
2. Use Supavisor Session Mode connection string for optimal pooling (Requirement 1.2)
3. Implement application-side connection pooler (SQLAlchemy or asyncpg) with proper async support
4. Refactor connectivity test to be truly non-blocking using async/await patterns
5. Implement lazy initialization pattern (test connectivity only on first actual database operation, not during application startup)
6. Use connection pool health checks instead of blocking connectivity tests during initialization
7. Configure proper pool size limits to avoid exceeding Postgres max_connections for compute tier

---

**Version**: 1.1  
**Created**: 2025-10-30  
**Last Updated**: 2025-11-01  
**Status**: Requirements Complete - Ready for Implementation