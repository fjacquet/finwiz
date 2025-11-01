# Supabase Client Usage Map

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     SupabaseClient (Singleton)                   │
│                  src/finwiz/supabase/client.py                   │
│                                                                   │
│  - Connection pooling (asyncpg)                                  │
│  - API client (supabase-py)                                      │
│  - Circuit breaker                                               │
│  - Metrics tracking                                              │
│  - Timeout management                                            │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
                              │ imports & instantiates
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Repositories │    │   Services   │    │     CLI      │
└──────────────┘    └──────────────┘    └──────────────┘
        │                   │                    │
        ▼                   ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Flow         │    │ Cache        │    │ Migration    │
│ Orchestrator │    │ Service      │    │ CLI          │
└──────────────┘    └──────────────┘    └──────────────┘
```

## Direct Users of SupabaseClient

### 1. **Flow Orchestrator** (`src/finwiz/flows/flow_orchestrator.py`)
   - **Usage**: Creates client for cache service and portfolio repository
   - **Instances**: 2 separate instances
   - **Purpose**: 
     - Cache service for analysis results
     - Portfolio snapshot storage
   
   ```python
   # Instance 1: Cache service
   supabase_client = SupabaseClient(
       failure_threshold=3,
       recovery_timeout=300
   )
   self.cache_service = CacheService(
       client=supabase_client,
       repository=AnalysisRepository(supabase_client)
   )
   
   # Instance 2: Portfolio repository
   supabase_client = SupabaseClient(
       failure_threshold=3,
       recovery_timeout=300
   )
   portfolio_repo = PortfolioRepository(supabase_client)
   ```

### 2. **Cache Service** (`src/finwiz/supabase/services/cache_service.py`)
   - **Usage**: Receives client from Flow Orchestrator
   - **Purpose**: Cache analysis results with TTL
   - **Methods**:
     - `initialize()` - Tests connectivity
     - `get_or_execute()` - Cache lookup/store
     - `invalidate_cache()` - Clear cache

### 3. **Migration Service** (`src/finwiz/supabase/services/migration_service.py`)
   - **Usage**: Creates own client instance
   - **Purpose**: Migrate legacy JSON files to Supabase
   - **Methods**:
     - `migrate_all()` - Batch migration
     - `migrate_file()` - Single file migration

### 4. **Migration CLI** (`src/finwiz/supabase/cli/migrate.py`)
   - **Usage**: Creates client for migration operations
   - **Purpose**: Command-line migration tool
   - **Commands**:
     - `migrate` - Run migrations
     - `status` - Check migration status

### 5. **RAG Integration** (`src/finwiz/supabase/utils/rag_integration.py`)
   - **Usage**: Creates client for vector operations
   - **Purpose**: Semantic search and RAG
   - **Methods**:
     - `get_rag_tools()` - Create RAG tools with vector search

## Repositories (Indirect Users)

These receive a SupabaseClient instance from their callers:

### 1. **AnalysisRepository** (`src/finwiz/supabase/repositories/analysis_repository.py`)
   - **Purpose**: CRUD operations for analysis records
   - **Used by**: Cache Service, Migration Service
   - **Methods**:
     - `store_analysis()` - Save analysis
     - `get_analysis()` - Retrieve by ticker
     - `list_analyses()` - Query with filters

### 2. **VectorRepository** (`src/finwiz/supabase/repositories/vector_repository.py`)
   - **Purpose**: Vector embeddings and semantic search
   - **Used by**: RAG Integration
   - **Methods**:
     - `store_embedding()` - Save vector
     - `semantic_search()` - Find similar content

### 3. **PortfolioRepository** (`src/finwiz/supabase/repositories/portfolio_repository.py`)
   - **Purpose**: Portfolio snapshot storage
   - **Used by**: Flow Orchestrator
   - **Methods**:
     - `store_snapshot()` - Save portfolio state
     - `get_latest_snapshot()` - Retrieve recent state

## Singleton Pattern

**Important**: `SupabaseClient` uses a singleton pattern:
- Only ONE instance exists per process
- Multiple `SupabaseClient()` calls return the same instance
- Connection pool is shared across all users
- Circuit breaker state is shared

```python
class SupabaseClient:
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

## Connection Flow

```
1. Flow Orchestrator starts
   ↓
2. Creates SupabaseClient (singleton)
   ↓
3. Client initializes:
   - Loads config from environment
   - Creates API client (supabase-py)
   - Prepares connection pool (not created yet)
   ↓
4. Cache Service calls initialize()
   ↓
5. test_connectivity() runs:
   - Checks if API client can be created
   - Sets is_available flag
   ↓
6. If available:
   - Connection pool created on first use (lazy)
   - Cache operations enabled
   ↓
7. If unavailable:
   - Raises ConnectionError (fail-fast)
   - Flow execution stops
```

## Configuration

All configuration comes from environment variables:

```bash
# Core
SUPABASE_ENABLED=true
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJhbGc...
SUPABASE_DB_URL=postgresql://postgres.xxx:password@...

# Connection Pool
SUPABASE_POOL_MIN_SIZE=2
SUPABASE_POOL_MAX_SIZE=10
SUPABASE_POOL_IDLE_TIMEOUT=300

# Timeouts
DATABASE_READ_TIMEOUT=2.0
DATABASE_WRITE_TIMEOUT=5.0
SUPABASE_CONNECTIVITY_TEST_TIMEOUT=5.0
SUPABASE_MAX_RETRIES=1

# Circuit Breaker
SUPABASE_CIRCUIT_BREAKER_THRESHOLD=3
SUPABASE_CIRCUIT_BREAKER_TIMEOUT=300
```

## Key Methods

### `test_connectivity()` - Fast connectivity check
- Validates API client can be created
- Sets `is_available` flag
- Raises `ConnectionError` if misconfigured
- **Fast**: <0.1 seconds

### `execute_with_timeout()` - Execute operations with timeout
- Supports both API client and connection pool
- Automatic retry logic
- Circuit breaker integration
- Metrics tracking

### `get_connection()` / `release_connection()` - Pool management
- Lazy pool initialization
- Connection acquisition with timeout
- Automatic cleanup

## Error Handling

### Fail-Fast Scenarios (raises ConnectionError):
1. `SUPABASE_ENABLED=true` but missing URL/KEY
2. `SUPABASE_ENABLED=true` but API client creation fails
3. Connectivity test timeout

### Graceful Degradation Scenarios:
1. `SUPABASE_ENABLED=false` - Caching disabled, analysis continues
2. Circuit breaker open - Operations skipped, analysis continues
3. Individual operation timeout - Returns None, analysis continues

## Performance Characteristics

- **Connectivity test**: <0.1s (API client creation only)
- **Connection pool**: Lazy initialization on first use
- **Circuit breaker**: Opens after 3 failures, recovers after 5 minutes
- **Concurrent operations**: Limited by semaphore (default: 10)
- **Connection pool**: 2-10 connections (configurable)

## Monitoring

The client tracks:
- Total operations
- Successful operations
- Failed operations
- Timeout count
- Response times (rolling window of 100)
- Success rate
- Average response time

Access via:
```python
client = SupabaseClient()
health = client.get_health_status()
print(f"Success rate: {health.success_rate:.1%}")
print(f"Avg response time: {health.avg_response_time_ms:.1f}ms")
```
