# Design Document

## Overview

This document describes the technical design for integrating Supabase as the centralized data persistence and vector storage layer for FinWiz. The design prioritizes **zero impact on analysis performance** through asynchronous operations, circuit breaker protection, and graceful degradation.

## Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "FinWiz Application"
        A[Analysis Flow] --> B{Cache Check}
        B -->|Hit| C[Return Cached]
        B -->|Miss/Timeout| D[Execute Analysis]
        D --> E[Analysis Complete]
        E --> F[Background Storage]
        E --> G[Return Results]
    end
    
    subgraph "Supabase Layer"
        H[Connection Pool]
        I[PostgreSQL + pgvector]
        J[Circuit Breaker]
        K[Async Task Queue]
    end
    
    B -.->|2s timeout| H
    F -.->|async| K
    H --> J
    J --> I
    K --> I
    
    style F fill:#90EE90
    style K fill:#90EE90
    style J fill:#FFB6C1
```

### Component Architecture

```
src/finwiz/
├── supabase/
│   ├── __init__.py
│   ├── client.py                    # Singleton client with connection pooling
│   ├── circuit_breaker.py           # Circuit breaker implementation
│   ├── models.py                    # Pydantic models for database schemas
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── analysis_repository.py   # Analysis CRUD operations
│   │   ├── portfolio_repository.py  # Portfolio snapshot operations
│   │   └── vector_repository.py     # Vector search operations
│   ├── services/
│   │   ├── __init__.py
│   │   ├── cache_service.py         # Analysis caching logic
│   │   ├── embedding_service.py     # Vector embedding generation
│   │   ├── migration_service.py     # Data migration from files
│   │   └── rag_service.py           # RAG context retrieval
│   └── utils/
│       ├── __init__.py
│       ├── async_tasks.py           # Background task management
│       └── monitoring.py            # Performance and pool monitoring
```

### Connection Pooling Architecture

```mermaid
graph TB
    subgraph "Application Layer"
        A[FinWiz Flow] --> B[Repository Layer]
        B --> C[SupabaseClient Singleton]
    end
    
    subgraph "Connection Management"
        C --> D{Pool Initialized?}
        D -->|No| E[Lazy Initialize Pool]
        D -->|Yes| F[asyncpg Connection Pool]
        E --> F
        F --> G{Connection Available?}
        G -->|Yes| H[Acquire Connection]
        G -->|No| I[Wait up to 5s]
        I -->|Timeout| J[Circuit Breaker]
        I -->|Available| H
    end
    
    subgraph "Supabase Infrastructure"
        H --> K[Supavisor Session Mode]
        K --> L[PostgreSQL + pgvector]
    end
    
    H --> M[Execute Query]
    M --> N[Release Connection]
    N --> F
    
    style C fill:#FFD700
    style F fill:#90EE90
    style K fill:#87CEEB
    style J fill:#FFB6C1
```

**Connection Flow**:

1. **Application requests database operation** → Repository layer
2. **Repository calls SupabaseClient** → Singleton instance (only one per app)
3. **Client checks pool initialization** → Lazy init on first use
4. **Pool acquisition** → asyncpg pool with 2-10 connections
5. **Connection wait** → Up to 5 seconds if pool exhausted
6. **Supavisor routing** → Session Mode for persistent connections
7. **Query execution** → With timeout enforcement
8. **Connection release** → Back to pool for reuse

**Key Benefits**:

- **Singleton pattern** prevents multiple client instances
- **Lazy initialization** avoids blocking during app startup
- **Connection reuse** reduces overhead of creating new connections
- **Supavisor Session Mode** provides server-side pooling for IPv4/IPv6 support
- **Application-side pooling** provides additional connection management
- **Circuit breaker** prevents cascading failures

## Components and Interfaces

### 1. Supabase Client (`client.py`)

**Purpose**: Manage Supabase connection with singleton pattern, connection pooling, and circuit breaker protection

**Interface**:

```python
from typing import Optional
import asyncpg
from supabase import Client, create_client
from finwiz.supabase.circuit_breaker import CircuitBreaker

class SupabaseClient:
    """Singleton Supabase client with connection pooling and circuit breaker protection."""
    
    _instance: Optional['SupabaseClient'] = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        """Ensure only one instance exists (singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize client with connection pooling."""
        if hasattr(self, '_initialized'):
            return
        
        self.url: str = os.getenv("SUPABASE_URL")
        self.key: str = os.getenv("SUPABASE_KEY")
        self.db_url: Optional[str] = os.getenv("SUPABASE_DB_URL")  # Session Mode connection string
        self.enabled: bool = os.getenv("SUPABASE_ENABLED", "true").lower() == "true"
        
        # API client (for REST/GraphQL operations)
        self.api_client: Optional[Client] = None
        
        # Database connection pool (for direct SQL operations)
        self.db_pool: Optional[asyncpg.Pool] = None
        
        # Circuit breaker
        self.circuit_breaker: CircuitBreaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=300  # 5 minutes
        )
        
        # Pool configuration
        self.pool_min_size = int(os.getenv("SUPABASE_POOL_MIN_SIZE", "2"))
        self.pool_max_size = int(os.getenv("SUPABASE_POOL_MAX_SIZE", "10"))
        self.pool_idle_timeout = int(os.getenv("SUPABASE_POOL_IDLE_TIMEOUT", "300"))
        
        self._initialized = True
    
    async def initialize_pool(self):
        """Initialize connection pool lazily on first use."""
        if self.db_pool is not None:
            return
        
        if not self.enabled or not self.db_url:
            logger.info("Database connection pool disabled (using API client only)")
            return
        
        async with self._lock:
            if self.db_pool is not None:
                return
            
            try:
                # Create asyncpg connection pool with Supavisor Session Mode
                self.db_pool = await asyncpg.create_pool(
                    dsn=self.db_url,
                    min_size=self.pool_min_size,
                    max_size=self.pool_max_size,
                    max_inactive_connection_lifetime=self.pool_idle_timeout,
                    command_timeout=5.0,  # 5 second timeout for commands
                    ssl='require'  # Enforce SSL
                )
                logger.info(
                    f"Connection pool initialized: "
                    f"min={self.pool_min_size}, max={self.pool_max_size}, "
                    f"idle_timeout={self.pool_idle_timeout}s"
                )
                self.circuit_breaker.record_success()
            except Exception as e:
                self.circuit_breaker.record_failure()
                logger.error(f"Failed to initialize connection pool: {e}")
                self.db_pool = None
    
    def get_api_client(self) -> Optional[Client]:
        """Get Supabase API client if available and circuit is closed."""
        if not self.enabled:
            return None
        
        if self.circuit_breaker.is_open():
            logger.warning("Circuit breaker is open, skipping database operation")
            return None
        
        if not self.api_client:
            try:
                self.api_client = create_client(self.url, self.key)
                self.circuit_breaker.record_success()
            except Exception as e:
                self.circuit_breaker.record_failure()
                logger.error(f"Failed to connect to Supabase API: {e}")
                return None
        
        return self.api_client
    
    async def get_connection(self) -> Optional[asyncpg.Connection]:
        """Get database connection from pool."""
        if not self.enabled or self.circuit_breaker.is_open():
            return None
        
        # Initialize pool on first use (lazy initialization)
        await self.initialize_pool()
        
        if not self.db_pool:
            return None
        
        try:
            # Acquire connection with timeout
            conn = await asyncio.wait_for(
                self.db_pool.acquire(),
                timeout=5.0  # Wait up to 5 seconds for available connection
            )
            return conn
        except asyncio.TimeoutError:
            logger.warning("Connection pool exhausted, timeout waiting for connection")
            self.circuit_breaker.record_failure()
            return None
        except Exception as e:
            logger.error(f"Failed to acquire connection: {e}")
            self.circuit_breaker.record_failure()
            return None
    
    async def release_connection(self, conn: asyncpg.Connection):
        """Release connection back to pool."""
        if self.db_pool and conn:
            await self.db_pool.release(conn)
    
    async def execute_with_timeout(
        self, 
        operation: callable, 
        timeout: float = 2.0,
        use_pool: bool = False
    ) -> Optional[Any]:
        """Execute operation with timeout and circuit breaker protection."""
        if use_pool:
            # Use connection pool for direct SQL operations
            conn = await self.get_connection()
            if not conn:
                return None
            
            try:
                result = await asyncio.wait_for(operation(conn), timeout=timeout)
                self.circuit_breaker.record_success()
                return result
            except asyncio.TimeoutError:
                logger.warning(f"Database operation timed out after {timeout}s")
                self.circuit_breaker.record_failure()
                return None
            except Exception as e:
                logger.error(f"Database operation failed: {e}")
                self.circuit_breaker.record_failure()
                return None
            finally:
                await self.release_connection(conn)
        else:
            # Use API client for REST/GraphQL operations
            client = self.get_api_client()
            if not client:
                return None
            
            try:
                result = await asyncio.wait_for(operation(client), timeout=timeout)
                self.circuit_breaker.record_success()
                return result
            except asyncio.TimeoutError:
                logger.warning(f"Database operation timed out after {timeout}s")
                self.circuit_breaker.record_failure()
                return None
            except Exception as e:
                logger.error(f"Database operation failed: {e}")
                self.circuit_breaker.record_failure()
                return None
    
    async def close(self):
        """Close connection pool gracefully."""
        if self.db_pool:
            await self.db_pool.close()
            logger.info("Connection pool closed")
    
    async def get_pool_stats(self) -> dict:
        """Get connection pool statistics for monitoring."""
        if not self.db_pool:
            return {"status": "disabled"}
        
        return {
            "status": "active",
            "size": self.db_pool.get_size(),
            "free_size": self.db_pool.get_idle_size(),
            "min_size": self.pool_min_size,
            "max_size": self.pool_max_size,
            "idle_timeout": self.pool_idle_timeout
        }
```

**Key Features**:

- **Singleton pattern**: Only one client instance per application lifecycle
- **Connection pooling**: asyncpg pool with configurable min/max connections
- **Lazy initialization**: Pool created on first use, not during app startup
- **Supavisor Session Mode**: Uses Session Mode connection string for persistent deployment
- **Circuit breaker integration**: Automatic failure detection and recovery
- **Timeout enforcement**: Configurable timeouts for reads (2s) and writes (5s)
- **Graceful failure handling**: Falls back to API client if pool unavailable
- **SSL enforcement**: All connections use SSL encryption
- **Pool monitoring**: Statistics for observability

### 2. Circuit Breaker (`circuit_breaker.py`)

**Purpose**: Prevent cascading failures from database issues

**Interface**:

```python
from enum import Enum
from datetime import datetime, timedelta

class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failures detected, skip operations
    HALF_OPEN = "half_open"  # Testing recovery

class CircuitBreaker:
    """Circuit breaker for database operations."""
    
    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 300):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED
    
    def is_open(self) -> bool:
        """Check if circuit breaker is open."""
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self.last_failure_time:
                elapsed = (datetime.now() - self.last_failure_time).total_seconds()
                if elapsed >= self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    logger.info("Circuit breaker entering half-open state")
                    return False
            return True
        return False
    
    def record_success(self):
        """Record successful operation."""
        if self.state == CircuitState.HALF_OPEN:
            logger.info("Circuit breaker closing after successful test")
            self.state = CircuitState.CLOSED
        self.failure_count = 0
    
    def record_failure(self):
        """Record failed operation."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            if self.state != CircuitState.OPEN:
                logger.warning(
                    f"Circuit breaker opening after {self.failure_count} failures"
                )
                self.state = CircuitState.OPEN
```

**Key Features**:

- Three states: CLOSED, OPEN, HALF_OPEN
- Automatic recovery attempt after timeout
- Configurable failure threshold
- Thread-safe operation

### 3. Analysis Repository (`repositories/analysis_repository.py`)

**Purpose**: CRUD operations for analysis storage and retrieval

**Interface**:

```python
from typing import Optional, List
from datetime import datetime, timedelta
from finwiz.supabase.models import AnalysisRecord
from finwiz.schemas.crew_exports import CrewExport

class AnalysisRepository:
    """Repository for analysis storage and retrieval."""
    
    def __init__(self, client: SupabaseClient):
        self.client = client
        self.table = "analyses"
    
    async def get_cached_analysis(
        self,
        ticker: str,
        asset_class: str,
        ttl_hours: int = 24
    ) -> Optional[AnalysisRecord]:
        """Get cached analysis if within TTL."""
        cutoff_time = datetime.now() - timedelta(hours=ttl_hours)
        
        def query(client):
            return (
                client.table(self.table)
                .select("*")
                .eq("ticker", ticker.upper())
                .eq("asset_class", asset_class.lower())
                .gte("created_at", cutoff_time.isoformat())
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
        
        result = self.client.execute_with_timeout(query, timeout=2.0)
        if result and result.data:
            return AnalysisRecord(**result.data[0])
        return None
    
    async def store_analysis(
        self,
        ticker: str,
        asset_class: str,
        export_data: CrewExport
    ) -> bool:
        """Store analysis asynchronously (background task)."""
        def insert(client):
            return (
                client.table(self.table)
                .insert({
                    "ticker": ticker.upper(),
                    "asset_class": asset_class.lower(),
                    "composite_score": export_data.composite_score,
                    "grade": export_data.grade,
                    "recommendation": export_data.recommendation,
                    "export_json": export_data.model_dump(),
                    "created_at": datetime.now().isoformat()
                })
                .execute()
            )
        
        # Execute in background task (non-blocking)
        asyncio.create_task(
            self._store_with_retry(insert)
        )
        return True  # Return immediately
    
    async def _store_with_retry(self, operation: callable, max_retries: int = 3):
        """Store with exponential backoff retry."""
        for attempt in range(max_retries):
            try:
                result = self.client.execute_with_timeout(operation, timeout=5.0)
                if result:
                    logger.info("Analysis stored successfully")
                    return
            except Exception as e:
                logger.error(f"Store attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        logger.error("Failed to store analysis after all retries")
```

**Key Features**:

- Async storage with background tasks
- Cache retrieval with strict timeout
- Exponential backoff retry for writes
- Non-blocking operations

### 4. Vector Repository (`repositories/vector_repository.py`)

**Purpose**: Vector embedding storage and semantic search

**Interface**:

```python
from typing import List, Tuple
from finwiz.supabase.services.embedding_service import EmbeddingService

class VectorRepository:
    """Repository for vector operations."""
    
    def __init__(self, client: SupabaseClient):
        self.client = client
        self.embedding_service = EmbeddingService()
        self.table = "analysis_embeddings"
    
    async def store_embedding(
        self,
        analysis_id: str,
        text: str
    ) -> bool:
        """Store vector embedding asynchronously."""
        # Generate embedding
        embedding = await self.embedding_service.generate_embedding(text)
        
        def insert(client):
            return (
                client.table(self.table)
                .insert({
                    "analysis_id": analysis_id,
                    "embedding": embedding,
                    "text": text,
                    "created_at": datetime.now().isoformat()
                })
                .execute()
            )
        
        # Execute in background task
        asyncio.create_task(
            self.client.execute_with_timeout(insert, timeout=5.0)
        )
        return True
    
    async def search_similar(
        self,
        query: str,
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Tuple[str, float]]:
        """Search for similar analyses using vector similarity."""
        # Generate query embedding
        query_embedding = await self.embedding_service.generate_embedding(query)
        
        def search(client):
            # Use pgvector similarity search
            return (
                client.rpc(
                    "match_analyses",
                    {
                        "query_embedding": query_embedding,
                        "match_threshold": similarity_threshold,
                        "match_count": limit
                    }
                )
                .execute()
            )
        
        result = self.client.execute_with_timeout(search, timeout=2.0)
        if result and result.data:
            return [(r["analysis_id"], r["similarity"]) for r in result.data]
        return []
```

**Key Features**:

- OpenAI text-embedding-3-small integration
- pgvector similarity search
- Configurable similarity threshold
- Async embedding generation

### 5. Cache Service (`services/cache_service.py`)

**Purpose**: High-level caching logic with fallback

**Interface**:

```python
from typing import Optional
from finwiz.schemas.crew_exports import CrewExport
from finwiz.supabase.repositories.analysis_repository import AnalysisRepository

class CacheService:
    """Service for analysis caching."""
    
    def __init__(self, repository: AnalysisRepository):
        self.repository = repository
        self.ttl_hours = int(os.getenv("ANALYSIS_CACHE_TTL_HOURS", "24"))
    
    async def get_or_execute(
        self,
        ticker: str,
        asset_class: str,
        execute_fn: callable
    ) -> Tuple[CrewExport, bool]:
        """Get cached analysis or execute crew."""
        # Try cache first (with timeout)
        cached = await self.repository.get_cached_analysis(
            ticker, asset_class, self.ttl_hours
        )
        
        if cached:
            logger.info(f"Cache hit for {ticker} ({asset_class})")
            return CrewExport(**cached.export_json), True
        
        # Cache miss or timeout - execute crew
        logger.info(f"Cache miss for {ticker} ({asset_class}), executing crew")
        result = await execute_fn()
        
        # Store result asynchronously (non-blocking)
        await self.repository.store_analysis(ticker, asset_class, result)
        
        return result, False
```

**Key Features**:

- Transparent caching layer
- Non-blocking storage
- Configurable TTL
- Cache hit/miss tracking

### 6. RAG Service (`services/rag_service.py`)

**Purpose**: Retrieve historical context for AI agents

**Interface**:

```python
from typing import List, Optional
from finwiz.supabase.repositories.vector_repository import VectorRepository
from finwiz.supabase.repositories.analysis_repository import AnalysisRepository

class RAGService:
    """Service for RAG context retrieval."""
    
    def __init__(
        self,
        vector_repo: VectorRepository,
        analysis_repo: AnalysisRepository
    ):
        self.vector_repo = vector_repo
        self.analysis_repo = analysis_repo
    
    async def get_context(
        self,
        query: str,
        limit: int = 3
    ) -> Optional[List[dict]]:
        """Get historical context for query."""
        # Search for similar analyses
        similar = await self.vector_repo.search_similar(query, limit=limit)
        
        if not similar:
            logger.info("No similar analyses found for RAG context")
            return None
        
        # Retrieve full analysis records
        context = []
        for analysis_id, similarity in similar:
            analysis = await self.analysis_repo.get_by_id(analysis_id)
            if analysis:
                context.append({
                    "ticker": analysis.ticker,
                    "asset_class": analysis.asset_class,
                    "grade": analysis.grade,
                    "recommendation": analysis.recommendation,
                    "similarity": similarity,
                    "summary": analysis.export_json.get("summary", "")
                })
        
        logger.info(f"Retrieved {len(context)} analyses for RAG context")
        return context if context else None
```

**Key Features**:

- Vector similarity search
- Top-k retrieval (default 3)
- Graceful failure handling
- Context formatting for agents

## Data Models

### Database Schema

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Analyses table
CREATE TABLE analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker VARCHAR(10) NOT NULL,
    asset_class VARCHAR(20) NOT NULL,
    composite_score FLOAT,
    grade VARCHAR(5),
    recommendation VARCHAR(10),
    export_json JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes for performance
    INDEX idx_ticker_asset (ticker, asset_class),
    INDEX idx_created_at (created_at DESC),
    INDEX idx_grade (grade)
);

-- Analysis embeddings table
CREATE TABLE analysis_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID REFERENCES analyses(id) ON DELETE CASCADE,
    embedding vector(1536),  -- OpenAI text-embedding-3-small
    text TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Index for vector similarity search
    INDEX idx_embedding ON analysis_embeddings USING ivfflat (embedding vector_cosine_ops)
);

-- Portfolio snapshots table
CREATE TABLE portfolio_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    total_value FLOAT,
    holdings JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_snapshot_date (snapshot_date DESC)
);

-- Vector similarity search function
CREATE OR REPLACE FUNCTION match_analyses(
    query_embedding vector(1536),
    match_threshold float,
    match_count int
)
RETURNS TABLE (
    analysis_id UUID,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        ae.analysis_id,
        1 - (ae.embedding <=> query_embedding) AS similarity
    FROM analysis_embeddings ae
    WHERE 1 - (ae.embedding <=> query_embedding) > match_threshold
    ORDER BY ae.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
```

### Pydantic Models

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any

class AnalysisRecord(BaseModel):
    """Database record for analysis."""
    id: str
    ticker: str
    asset_class: str
    composite_score: float
    grade: str
    recommendation: str
    export_json: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

class PortfolioSnapshot(BaseModel):
    """Database record for portfolio snapshot."""
    id: str
    snapshot_date: datetime
    total_value: float
    holdings: Dict[str, Any]
    created_at: datetime

class EmbeddingRecord(BaseModel):
    """Database record for vector embedding."""
    id: str
    analysis_id: str
    embedding: List[float] = Field(..., min_length=1536, max_length=1536)
    text: str
    created_at: datetime
```

## Error Handling

### Error Hierarchy

```python
class SupabaseError(Exception):
    """Base exception for Supabase operations."""
    pass

class ConnectionError(SupabaseError):
    """Failed to connect to Supabase."""
    pass

class TimeoutError(SupabaseError):
    """Operation timed out."""
    pass

class CircuitBreakerOpenError(SupabaseError):
    """Circuit breaker is open."""
    pass
```

### Error Handling Strategy

1. **Connection Failures**: Log error, open circuit breaker, continue with file-based storage
2. **Timeout Errors**: Log warning, proceed with fresh analysis (cache miss)
3. **Write Failures**: Log error, retry with exponential backoff (background task)
4. **Circuit Breaker Open**: Skip database operations, use file-based storage

## Testing Strategy

### Unit Tests

```python
# Test cache service
def test_should_return_cached_analysis_when_within_ttl(mocker):
    """Verify cache hit returns stored analysis."""
    # Arrange
    mock_repo = mocker.Mock()
    mock_repo.get_cached_analysis.return_value = AnalysisRecord(...)
    service = CacheService(mock_repo)
    
    # Act
    result, is_cached = await service.get_or_execute("AAPL", "stock", lambda: None)
    
    # Assert
    assert is_cached is True
    assert result.ticker == "AAPL"

# Test circuit breaker
def test_should_open_circuit_after_threshold_failures():
    """Verify circuit breaker opens after failures."""
    # Arrange
    breaker = CircuitBreaker(failure_threshold=3)
    
    # Act
    for _ in range(3):
        breaker.record_failure()
    
    # Assert
    assert breaker.is_open() is True
```

### Integration Tests

```python
@pytest.mark.integration
async def test_should_store_and_retrieve_analysis():
    """Integration test for full storage/retrieval cycle."""
    # Requires real Supabase connection
    client = SupabaseClient()
    repo = AnalysisRepository(client)
    
    # Store analysis
    export = StockCrewExport(ticker="AAPL", ...)
    await repo.store_analysis("AAPL", "stock", export)
    
    # Retrieve analysis
    cached = await repo.get_cached_analysis("AAPL", "stock")
    
    assert cached is not None
    assert cached.ticker == "AAPL"
```

### Performance Tests

```python
@pytest.mark.performance
async def test_cache_check_completes_within_timeout():
    """Verify cache check respects timeout."""
    # Arrange
    client = SupabaseClient()
    repo = AnalysisRepository(client)
    
    # Act
    start = time.time()
    result = await repo.get_cached_analysis("AAPL", "stock")
    duration = time.time() - start
    
    # Assert
    assert duration < 2.5  # 2s timeout + 0.5s buffer
```

## Integration Points

### 1. Flow Integration

```python
# In finwiz/flows/flow_orchestrator.py

from finwiz.supabase.services.cache_service import CacheService

class FinwizFlow(Flow[FinwizState]):
    def __init__(self):
        super().__init__()
        self.cache_service = CacheService(...)
    
    @listen("check_portfolio")
    async def analyze_holdings_deep(self) -> dict[str, Any]:
        """Analyze holdings with caching."""
        results = {}
        
        for holding in self.state.portfolio_holdings:
            # Try cache first
            analysis, is_cached = await self.cache_service.get_or_execute(
                ticker=holding.ticker,
                asset_class=holding.asset_class,
                execute_fn=lambda: self._execute_deep_analysis(holding)
            )
            
            results[holding.ticker] = analysis
            
            if is_cached:
                logger.info(f"Used cached analysis for {holding.ticker}")
        
        return {"deep_analysis_results": results}
```

### 2. RAG Integration

```python
# In finwiz/crews/stock_crew/stock_crew.py

from finwiz.supabase.services.rag_service import RAGService

class StockCrew(CrewBase):
    def __init__(self):
        super().__init__()
        self.rag_service = RAGService(...)
    
    @task
    def analysis_task(self) -> Task:
        return Task(
            description=self._get_task_description_with_rag(),
            agent=self.analyst(),
            ...
        )
    
    async def _get_task_description_with_rag(self) -> str:
        """Get task description with RAG context."""
        base_description = self.tasks_config["analysis_task"]["description"]
        
        # Get historical context
        context = await self.rag_service.get_context(
            query=f"Analysis of {self.ticker} stock"
        )
        
        if context:
            rag_context = "\n\nHistorical Context:\n"
            for item in context:
                rag_context += f"- {item['ticker']} ({item['grade']}): {item['summary']}\n"
            return base_description + rag_context
        
        return base_description
```

## Deployment Considerations

### Environment Variables

```bash
# Supabase Configuration
SUPABASE_ENABLED=true
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Database Connection (Supavisor Session Mode)
# Format: postgres://postgres.PROJECT:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres
SUPABASE_DB_URL=postgres://postgres.your-project:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:5432/postgres

# Connection Pool Configuration
SUPABASE_POOL_MIN_SIZE=2
SUPABASE_POOL_MAX_SIZE=10
SUPABASE_POOL_IDLE_TIMEOUT=300

# Cache Configuration
ANALYSIS_CACHE_TTL_HOURS=24

# Circuit Breaker Configuration
CIRCUIT_BREAKER_FAILURE_THRESHOLD=3
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=300

# Performance Configuration
DATABASE_READ_TIMEOUT=2.0
DATABASE_WRITE_TIMEOUT=5.0
```

### Database Setup

1. **Create Supabase project** in desired region
2. **Get connection strings** from Supabase dashboard:
   - Click "Connect" button
   - Select "Session Mode" for SUPABASE_DB_URL
   - Copy API URL and anon key for SUPABASE_URL and SUPABASE_KEY
3. **Enable pgvector extension**:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
4. **Run schema migration SQL** (see Data Models section)
5. **Configure row-level security policies** for future multi-user support
6. **Verify connection pooling**:
   - Supavisor Session Mode provides server-side pooling
   - Application-side pooling (asyncpg) provides additional connection management
   - Combined approach optimizes for persistent deployment architecture

### Monitoring

```python
# Metrics to track
- cache_hit_rate: Percentage of cache hits
- cache_miss_rate: Percentage of cache misses
- circuit_breaker_state: Current circuit breaker state
- database_operation_duration: Time for database operations
- background_task_success_rate: Success rate of async writes
- embedding_generation_duration: Time to generate embeddings

# Connection pool metrics
- pool_size: Current number of connections in pool
- pool_free_size: Number of idle connections available
- pool_utilization: Percentage of pool in use
- connection_wait_time: Time waiting for available connection
- connection_acquisition_failures: Failed attempts to acquire connection
- connection_lifetime: Average connection duration
```

**Monitoring Implementation**:

```python
# In finwiz/supabase/utils/monitoring.py

class PoolMonitor:
    """Monitor connection pool health and performance."""
    
    def __init__(self, client: SupabaseClient):
        self.client = client
        self.metrics = {
            "acquisitions": 0,
            "releases": 0,
            "timeouts": 0,
            "failures": 0
        }
    
    async def log_pool_stats(self):
        """Log current pool statistics."""
        stats = await self.client.get_pool_stats()
        
        if stats["status"] == "active":
            utilization = (
                (stats["size"] - stats["free_size"]) / stats["max_size"] * 100
            )
            
            logger.info(
                f"Connection Pool Stats: "
                f"size={stats['size']}/{stats['max_size']}, "
                f"free={stats['free_size']}, "
                f"utilization={utilization:.1f}%"
            )
            
            # Alert if utilization is high
            if utilization > 80:
                logger.warning(
                    f"Connection pool utilization high: {utilization:.1f}%"
                )
```

## Migration Strategy

### Phase 1: Infrastructure Setup

1. **Create Supabase project** and obtain connection strings
   - Get Supavisor Session Mode connection string (port 5432)
   - Get API URL and anon key
   - Verify SSL is enabled
2. **Implement singleton client** with connection pooling
   - asyncpg pool with min=2, max=10 connections
   - Lazy initialization pattern
   - Circuit breaker integration
3. **Add environment variable configuration**
   - SUPABASE_DB_URL (Session Mode connection string)
   - Pool configuration variables
   - Timeout settings
4. **Deploy with SUPABASE_ENABLED=false** for initial testing
5. **Run database schema migration** to create tables and indexes

### Phase 2: Storage Implementation

1. Implement analysis repository
2. Add background storage tasks
3. Test with small portfolio (< 10 holdings)
4. Monitor performance impact

### Phase 3: Caching Implementation

1. Implement cache service
2. Integrate with flow orchestrator
3. Test cache hit/miss scenarios
4. Measure cost savings

### Phase 4: Vector Search

1. Implement embedding service
2. Add vector repository
3. Migrate existing analyses
4. Test semantic search

### Phase 5: RAG Integration

1. Implement RAG service
2. Integrate with crew task descriptions
3. Test with historical context
4. Measure recommendation quality

### Phase 6: Full Rollout

1. Enable for all users (SUPABASE_ENABLED=true)
2. Monitor performance and reliability
3. Optimize based on metrics
4. Document best practices

## Troubleshooting

### Connection Pool Issues

**Problem**: Connection pool exhausted (timeout waiting for connection)

**Symptoms**:
- Logs show "Connection pool exhausted, timeout waiting for connection"
- High pool utilization (>80%)
- Slow database operations

**Solutions**:
1. **Increase pool size**: Adjust SUPABASE_POOL_MAX_SIZE (default 10)
2. **Check for connection leaks**: Ensure all connections are released
3. **Reduce connection lifetime**: Lower SUPABASE_POOL_IDLE_TIMEOUT
4. **Monitor pool metrics**: Use `get_pool_stats()` to track utilization

**Problem**: Timeout during initialization

**Symptoms**:
- Application hangs during startup
- "test_connectivity() timed out" errors
- Blocking event loop

**Solutions**:
1. **Use lazy initialization**: Pool created on first use, not during startup
2. **Remove blocking connectivity tests**: Test on first actual operation
3. **Use async/await patterns**: Ensure all database calls are async
4. **Check network connectivity**: Verify Supabase URL is accessible

**Problem**: Circuit breaker opens frequently

**Symptoms**:
- "Circuit breaker is open" warnings
- Database operations skipped
- Falling back to file-based storage

**Solutions**:
1. **Check Supabase status**: Verify service is operational
2. **Verify connection string**: Ensure Session Mode format is correct
3. **Check SSL configuration**: Verify SSL is enabled and working
4. **Review timeout settings**: May need to increase for slow networks
5. **Monitor pool health**: Check for connection acquisition failures

### Performance Issues

**Problem**: Slow database operations

**Symptoms**:
- Operations exceed timeout thresholds
- High latency in logs
- Poor cache hit rates

**Solutions**:
1. **Use connection pooling**: Ensure pool is properly configured
2. **Optimize queries**: Add indexes for frequently queried fields
3. **Reduce payload size**: Limit JSON export size
4. **Use async operations**: Ensure all I/O is non-blocking
5. **Monitor pool utilization**: Check if pool is undersized

### Connection String Issues

**Problem**: Invalid connection string format

**Symptoms**:
- "Failed to initialize connection pool" errors
- SSL connection failures
- Authentication errors

**Solutions**:
1. **Verify Session Mode format**: Should use port 5432
   ```
   postgres://postgres.PROJECT:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres
   ```
2. **Check SSL requirement**: Ensure `ssl='require'` in connection
3. **Verify credentials**: Check password is correct and not URL-encoded
4. **Test connection manually**: Use psql to verify connection string works

---

**Version**: 2.0  
**Created**: 2025-10-30  
**Last Updated**: 2025-11-01  
**Status**: Design Complete - Connection Pooling Enhanced
