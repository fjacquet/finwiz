w# Implementation Plan

Convert the Supabase integration design into a series of implementation tasks. Each task builds incrementally, with no orphaned code. Tasks focus ONLY on writing, modifying, or testing code.

## Task List

- [x] 1. Set up Supabase infrastructure and database schema
  - Create Supabase project and enable pgvector extension
  - Write and execute database migration SQL for analyses, analysis_embeddings, and portfolio_snapshots tables
  - Create vector similarity search function (match_analyses)
  - Configure row-level security policies for future multi-user support
  - Add environment variables to .env.example: SUPABASE_URL, SUPABASE_KEY, SUPABASE_ENABLED, ANALYSIS_CACHE_TTL_HOURS
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Implement core Supabase client and circuit breaker
  - [x] 2.1 Create circuit breaker implementation
    - Write `src/finwiz/supabase/circuit_breaker.py` with CircuitState enum and CircuitBreaker class
    - Implement three-state logic: CLOSED, OPEN, HALF_OPEN
    - Add failure threshold (default 3) and recovery timeout (default 300s) configuration
    - Implement record_success() and record_failure() methods
    - Add automatic recovery attempt after timeout in is_open() method
    - _Requirements: 8.2.1, 8.2.2, 8.2.3, 8.2.4, 8.2.5_
  
  - [x] 2.2 Create Supabase client with connection management
    - Write `src/finwiz/supabase/client.py` with SupabaseClient class
    - Implement lazy connection initialization with environment variable configuration
    - Integrate CircuitBreaker for failure protection
    - Add get_client() method with circuit breaker check
    - Implement execute_with_timeout() method with configurable timeout (default 2s)
    - Add error handling with circuit breaker integration
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 8.1.5_
  
  - [x] 2.3 Create Pydantic models for database schemas
    - Write `src/finwiz/supabase/models.py` with AnalysisRecord, PortfolioSnapshot, and EmbeddingRecord models
    - Add field validation and type hints for all models
    - Include datetime fields with proper timezone handling
    - Add model_config for strict validation
    - _Requirements: 2.2, 4.2_
  
  - [ ]* 2.4 Write unit tests for circuit breaker and client
    - Test circuit breaker state transitions (CLOSED → OPEN → HALF_OPEN → CLOSED)
    - Test failure threshold triggering (3 consecutive failures)
    - Test automatic recovery after timeout (5 minutes)
    - Test client connection with circuit breaker protection
    - Test execute_with_timeout() with various timeout scenarios
    - Mock Supabase client for deterministic testing
    - _Requirements: 8.2.1, 8.2.2, 8.2.3, 8.2.4, 8.2.5_

- [x] 3. Implement analysis repository with async storage
  - [x] 3.1 Create analysis repository for CRUD operations
    - Write `src/finwiz/supabase/repositories/analysis_repository.py` with AnalysisRepository class
    - Implement get_cached_analysis() with TTL check (default 24 hours) and 2-second timeout
    - Implement store_analysis() as async background task with non-blocking execution
    - Add _store_with_retry() helper with exponential backoff (max 3 retries)
    - Include proper error handling and logging for all operations
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 6.1, 6.2, 6.3, 6.4, 8.1.1, 8.1.2_
  
  - [x] 3.2 Create async task management utilities
    - Write `src/finwiz/supabase/utils/async_tasks.py` with background task helpers
    - Implement task queue for managing async operations
    - Add task monitoring and error tracking
    - Include graceful shutdown handling for pending tasks
    - _Requirements: 8.1.1, 8.1.2_
  
  - [ ]* 3.3 Write unit tests for analysis repository
    - Test get_cached_analysis() with cache hit (within TTL)
    - Test get_cached_analysis() with cache miss (expired TTL)
    - Test get_cached_analysis() with timeout (> 2 seconds)
    - Test store_analysis() async execution (non-blocking)
    - Test _store_with_retry() exponential backoff logic
    - Mock Supabase client and circuit breaker
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 6.1, 6.2, 6.3_

- [x] 4. Implement cache service with transparent fallback
  - [x] 4.1 Create cache service for high-level caching logic
    - Write `src/finwiz/supabase/services/cache_service.py` with CacheService class
    - Implement get_or_execute() method with cache check and crew execution fallback
    - Add TTL configuration from environment variable (default 24 hours)
    - Include cache hit/miss logging and metrics tracking
    - Ensure non-blocking storage after crew execution
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_
  
  - [x] 4.2 Write unit tests for cache service
    - Test get_or_execute() with cache hit (returns cached, skips execution)
    - Test get_or_execute() with cache miss (executes crew, stores result)
    - Test get_or_execute() with cache timeout (proceeds with execution)
    - Test TTL configuration from environment variable
    - Mock AnalysisRepository and crew execution function
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 5. Integrate cache service with flow orchestrator
  - [x] 5.1 Add cache service to FinwizFlow
    - Modify `src/finwiz/flows/flow_orchestrator.py` to initialize CacheService
    - Update analyze_holdings_deep() method to use cache_service.get_or_execute()
    - Add cache hit/miss logging for each holding
    - Ensure graceful fallback when Supabase is unavailable
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 8.1.3, 8.1.4_
  
  - [ ]* 5.2 Write integration tests for flow caching
    - Test flow execution with cache hits (skips crew execution)
    - Test flow execution with cache misses (executes crews)
    - Test flow execution with Supabase unavailable (falls back to normal execution)
    - Test flow execution with circuit breaker open (skips database operations)
    - Mock Supabase client and crew execution
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 6. Implement vector embeddings and semantic search
  - [x] 6.1 Create embedding service for vector generation
    - Write `src/finwiz/supabase/services/embedding_service.py` with EmbeddingService class
    - Implement generate_embedding() using OpenAI text-embedding-3-small (1536 dimensions)
    - Add error handling and retry logic for OpenAI API calls
    - Include embedding caching to avoid redundant API calls
    - _Requirements: 3.1, 3.2_
  
  - [x] 6.2 Create vector repository for similarity search
    - Write `src/finwiz/supabase/repositories/vector_repository.py` with VectorRepository class
    - Implement store_embedding() as async background task
    - Implement search_similar() with configurable similarity threshold (default 0.7) and limit (default 5)
    - Add timeout enforcement (2 seconds) for search operations
    - Include proper error handling and logging
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [x] 6.3 Write unit tests for embedding and vector operations
    - Test generate_embedding() with valid text input
    - Test generate_embedding() with OpenAI API failure (retry logic)
    - Test store_embedding() async execution (non-blocking)
    - Test search_similar() with results above threshold
    - Test search_similar() with no results (below threshold)
    - Mock OpenAI API and Supabase client
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [-] 7. Implement Historical Analysis Service for historical context
  - [x] 7.1 Create Historical Analysis Service for context retrieval
    - Write `src/finwiz/supabase/services/rag_service.py` with HistoricalAnalysisService class
    - Implement get_context() method with vector search and analysis retrieval
    - Add context formatting for AI agent consumption
    - Include graceful handling when no similar analyses exist
    - Add logging for historical context retrieval
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
  
  - [x] 7.2 Integrate Historical Analysis Service with crew task descriptions
    - Create integration utilities in `src/finwiz/supabase/utils/rag_integration.py`
    - Implement get_historical_context_for_inputs() for crew kickoff integration
    - Add integration guide showing how to use with Stock, ETF, and Crypto crews
    - Ensure graceful fallback when historical context is unavailable
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
  
  - [x] 7.3 Write unit tests for Historical Analysis Service
    - Test get_context() with similar analyses found
    - Test get_context() with no similar analyses (returns None)
    - Test get_context() with vector search timeout
    - Test context formatting for agent consumption
    - Mock VectorRepository and AnalysisRepository
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 8. Implement portfolio snapshot tracking
  - [x] 8.1 Create portfolio repository for snapshot operations
    - Write `src/finwiz/supabase/repositories/portfolio_repository.py` with PortfolioRepository class
    - Implement create_snapshot() to store portfolio state with timestamp
    - Implement get_snapshots() to retrieve portfolio history ordered by date
    - Implement compare_snapshots() to calculate changes between snapshots
    - Add async storage for non-blocking execution
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [x] 8.2 Integrate portfolio snapshots with flow orchestrator
    - Modify `src/finwiz/flows/flow_orchestrator.py` to create snapshots after portfolio analysis
    - Add snapshot creation as background task (non-blocking)
    - Include error handling for snapshot failures
    - _Requirements: 4.1, 4.2_
  
  - [x] 8.3 Write unit tests for portfolio repository
    - Test create_snapshot() with valid portfolio data
    - Test get_snapshots() retrieval ordered by date
    - Test compare_snapshots() change calculation
    - Test async execution (non-blocking)
    - Mock Supabase client
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 9. Implement data migration from file-based exports
  - [x] 9.1 Create migration service for existing data
    - Write `src/finwiz/supabase/services/migration_service.py` with MigrationService class
    - Implement scan_exports() to find existing JSON exports in output directory
    - Implement migrate_export() to validate and store each export
    - Add idempotency check to prevent duplicate migrations
    - Include progress tracking and error reporting
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [x] 9.2 Create migration CLI command
    - Add migration command to `src/finwiz/main.py` or separate CLI script
    - Include dry-run mode to preview migration without executing
    - Add progress bar for large migrations
    - Include summary report of migrated analyses
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [x] 9.3 Write unit tests for migration service
    - Test scan_exports() finds all JSON files
    - Test migrate_export() validates against Pydantic schemas
    - Test migrate_export() skips invalid exports
    - Test idempotency (running twice doesn't create duplicates)
    - Mock file system and Supabase client
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 10. Implement monitoring and observability
  - [ ] 10.1 Create monitoring utilities for database operations
    - Write `src/finwiz/supabase/utils/monitoring.py` with performance tracking
    - Implement operation duration logging with thresholds
    - Add cache hit/miss rate tracking
    - Include circuit breaker state monitoring
    - Add metrics export for external monitoring systems
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_
  
  - [ ] 10.2 Add monitoring integration to all repositories and services
    - Update AnalysisRepository to log operation metrics
    - Update VectorRepository to log search performance
    - Update CacheService to track hit/miss rates
    - Update CircuitBreaker to log state changes
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_
  
  - [ ]* 10.3 Write unit tests for monitoring utilities
    - Test operation duration tracking
    - Test cache hit/miss rate calculation
    - Test circuit breaker state logging
    - Test metrics export format
    - Mock logging and metrics systems
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 11. Add security and data privacy features
  - [x] 11.1 Implement encryption for sensitive data
    - Add encryption utilities in `src/finwiz/supabase/utils/encryption.py`
    - Implement encrypt_sensitive_fields() for portfolio holdings and values
    - Implement decrypt_sensitive_fields() for data retrieval
    - Use environment variable for encryption key (SUPABASE_ENCRYPTION_KEY)
    - _Requirements: 9.1, 9.2_
  
  - [x] 11.2 Configure row-level security policies
    - Write SQL migration for RLS policies
    - Add user authentication integration (future multi-user support)
    - Document security configuration in README
    - _Requirements: 9.3_
  
  - [ ]* 11.3 Write unit tests for encryption utilities
    - Test encrypt_sensitive_fields() with portfolio data
    - Test decrypt_sensitive_fields() returns original data
    - Test encryption key validation
    - Mock encryption library
    - _Requirements: 9.1, 9.2_

- [ ] 12. Performance testing and optimization
  - [ ]* 12.1 Write performance tests for database operations
    - Test cache check completes within 2-second timeout
    - Test store operation completes within 5-second timeout
    - Test vector search completes within 1 second for 1000 analyses
    - Test background tasks don't block main thread
    - Measure actual performance against targets
    - _Requirements: 8.1, 8.2, 8.3, 8.4_
  
  - [ ]* 12.2 Write integration tests for end-to-end scenarios
    - Test full analysis flow with caching enabled
    - Test full analysis flow with Supabase unavailable
    - Test full analysis flow with circuit breaker open
    - Test portfolio analysis with snapshot creation
    - Test crew execution with historical analysis context
    - Measure total overhead (target < 500ms)
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 13. Documentation and deployment
  - [x] 13.1 Update documentation with Supabase integration
    - Add Supabase setup guide to README.md
    - Document environment variables and configuration
    - Add troubleshooting section for common issues
    - Include migration guide for existing users
    - Document performance benefits and cost savings
    - _Requirements: All_
  
  - [x] 13.2 Create deployment checklist and rollout plan
    - Document 6-phase rollout strategy
    - Create monitoring dashboard for key metrics
    - Add alerting for circuit breaker state changes
    - Document rollback procedure if issues arise
    - _Requirements: All_

---

**Implementation Notes:**

- All tasks build incrementally - no orphaned code
- Tests marked with * are optional but recommended
- Each task references specific requirements from requirements.md
- Tasks are ordered to minimize dependencies and enable parallel work
- Integration tests require real Supabase connection (mark with @pytest.mark.integration)
- Performance tests should be run separately (mark with @pytest.mark.performance)

**Estimated Timeline:**

- Phase 1 (Tasks 1-2): 2-3 days - Infrastructure and core client
- Phase 2 (Tasks 3-5): 3-4 days - Storage and caching
- Phase 3 (Tasks 6-7): 3-4 days - Vector search and RAG
- Phase 4 (Tasks 8-9): 2-3 days - Portfolio tracking and migration
- Phase 5 (Tasks 10-11): 2-3 days - Monitoring and security
- Phase 6 (Tasks 12-13): 2-3 days - Testing and documentation

**Total Estimated Time**: 14-20 days

---

**Version**: 1.0  
**Created**: 2025-10-30  
**Status**: Ready for Implementation
