# Design Document: Supabase Timeout Fix

## Overview

This design addresses the 100% timeout failure rate in Supabase operations by implementing graceful degradation, configurable timeouts, and early connectivity validation. The system will function normally whether Supabase is available or not.

## Architecture

### Current Issues

1. **Aggressive Timeouts**: 2-5 second timeouts are too short for network operations
2. **No Connectivity Test**: System assumes Supabase is available without validation
3. **Blocking Behavior**: Failed operations delay the analysis workflow
4. **Poor Error Handling**: Timeouts logged as warnings but cause circuit breaker to open
5. **No Fallback**: System doesn't gracefully handle unavailable cache

### Proposed Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                    FinWiz Application                        │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │         Startup: Connectivity Validation            │    │
│  │  - Test Supabase with simple query (5s timeout)    │    │
│  │  - Set cache_available flag based on result        │    │
│  │  - Log configuration and status                     │    │
│  └────────────────────────────────────────────────────┘    │
│                          │                                   │
│                          ▼                                   │
│  ┌────────────────────────────────────────────────────┐    │
│  │         Analysis Workflow                           │    │
│  │                                                      │    │
│  │  IF cache_available:                                │    │
│  │    Try cache read (10s timeout, max 3 retries)     │    │
│  │    IF timeout: Log warning, proceed with analysis   │    │
│  │                                                      │    │
│  │  Perform analysis (always)                          │    │
│  │                                                      │    │
│  │  IF cache_available:                                │    │
│  │    Try cache write (15s timeout, max 3 retries)    │    │
│  │    IF timeout: Log warning, continue               │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Key Design Decisions**:

- **Max 3 retries**: Complies with Requirement 2.5 (SHALL NOT retry more than 3 times)
- **Non-blocking writes**: Satisfies Requirement 1.5 (SHALL NOT block analysis)
- **Startup validation**: Implements Requirement 3.1 (SHALL test connectivity at startup)
- **Graceful degradation**: Ensures Requirement 1.3 (SHALL complete full workflow despite failures)

## Components and Interfaces

### 1. Supabase Client Singleton Pattern

**File**: `src/finwiz/supabase/client.py`

**Design Decision**: Implement singleton pattern to ensure a single shared connection pool across the application, preventing connection pool exhaustion and ensuring consistent metrics tracking.

**Changes**:

```python
import os
from datetime import datetime
from typing import Optional

# Module-level singleton instance
_supabase_client_instance: Optional['SupabaseClient'] = None
_client_lock = asyncio.Lock()

async def get_supabase_client() -> 'SupabaseClient':
    """
    Get or create the singleton Supabase client instance.
    
    Thread-safe singleton pattern ensures only one client instance exists
    across the application, preventing connection pool exhaustion.
    
    Returns:
        Singleton SupabaseClient instance
    """
    global _supabase_client_instance
    
    if _supabase_client_instance is None:
        async with _client_lock:
            # Double-check pattern
            if _supabase_client_instance is None:
                _supabase_client_instance = SupabaseClient()
                # Initialize connectivity test
                await _supabase_client_instance.test_connectivity()
    
    return _supabase_client_instance

def reset_supabase_client() -> None:
    """
    Reset the singleton instance (useful for testing).
    
    WARNING: Only use this in tests or during application shutdown.
    """
    global _supabase_client_instance
    _supabase_client_instance = None

class SupabaseClient:
    def __init__(self):
        # Configurable timeouts from environment (Requirement 2.1, 2.2, 2.3)
        self.read_timeout = float(os.getenv("SUPABASE_READ_TIMEOUT", "10.0"))
        self.write_timeout = float(os.getenv("SUPABASE_WRITE_TIMEOUT", "15.0"))
        self.max_retries = int(os.getenv("SUPABASE_MAX_RETRIES", "3"))  # Requirement 2.5
        self.connectivity_test_timeout = float(os.getenv("SUPABASE_CONNECTIVITY_TEST_TIMEOUT", "5.0"))
        self.is_available = False  # Set by connectivity test
        
        # Metrics tracking (Requirement 4.1, 4.2)
        self.total_operations = 0
        self.successful_operations = 0
        self.failed_operations = 0
        self.timeout_count = 0
        self.response_times = []  # Rolling window for avg calculation
        
        # Log configuration at startup (Requirement 4.5)
        logger.info(f"📊 Supabase Configuration:")
        logger.info(f"  - Read Timeout: {self.read_timeout}s")
        logger.info(f"  - Write Timeout: {self.write_timeout}s")
        logger.info(f"  - Max Retries: {self.max_retries}")
        logger.info(f"  - Connectivity Test Timeout: {self.connectivity_test_timeout}s")
        
    async def test_connectivity(self) -> bool:
        """Test Supabase connectivity with simple query (Requirement 3.1, 3.2, 3.3).
        
        Returns:
            bool: True if connectivity test passed, False otherwise
        """
        try:
            # Simple query with configurable timeout (Requirement 3.1, 3.4)
            start_time = datetime.now()
            result = await self.execute_with_timeout(
                lambda client: client.table("analyses").select("id").limit(1),
                timeout=self.connectivity_test_timeout
            )
            elapsed = (datetime.now() - start_time).total_seconds()
            
            self.is_available = True
            logger.info(f"✅ Supabase connectivity test passed ({elapsed:.2f}s)")
            return True
            
        except Exception as e:
            self.is_available = False
            # Requirement 3.2: Log warning and disable caching
            logger.warning(f"⚠️ Supabase connectivity test failed: {e}")
            logger.warning("⚠️ Caching disabled - analysis will proceed without cache")
            return False
    
    def record_operation(self, success: bool, response_time: float, is_timeout: bool = False):
        """Record operation metrics (Requirement 4.1, 4.2)."""
        self.total_operations += 1
        if success:
            self.successful_operations += 1
        else:
            self.failed_operations += 1
        if is_timeout:
            self.timeout_count += 1
            
        # Track response times (rolling window of last 100)
        self.response_times.append(response_time)
        if len(self.response_times) > 100:
            self.response_times.pop(0)
            
        # Log metrics every 100 operations (Requirement 4.1, 4.2)
        if self.total_operations % 100 == 0:
            success_rate = self.successful_operations / self.total_operations
            avg_response_time = sum(self.response_times) / len(self.response_times)
            logger.info(f"📊 Supabase Metrics (last 100 ops):")
            logger.info(f"  - Success Rate: {success_rate:.1%}")
            logger.info(f"  - Avg Response Time: {avg_response_time:.2f}s")
            logger.info(f"  - Timeout Count: {self.timeout_count}")
```

**Design Rationale**:
- Metrics tracking added to satisfy Requirement 4.1 and 4.2 (success/failure rates, response times)
- Configuration logging at startup satisfies Requirement 4.5
- `max_retries` default changed to 3 to comply with Requirement 2.5
- Connectivity test timeout made configurable to satisfy Requirement 3.4 (complete within 5 seconds)

### 2. Cache Service with Graceful Degradation

**File**: `src/finwiz/supabase/services/cache_service.py`

**Changes**:

```python
from datetime import datetime, timedelta

class CacheService:
    def __init__(self, client: SupabaseClient):
        self.client = client
        self.repository = AnalysisRepository(client)
        self.is_enabled = False  # Set after connectivity test
        self.cache_ttl_hours = 24  # Requirement 5.4
        
    async def initialize(self) -> bool:
        """Initialize and test connectivity (Requirement 3.1, 3.2, 3.3)."""
        if not self.client:
            logger.info("ℹ️ No Supabase client - caching disabled")
            return False
            
        self.is_enabled = await self.client.test_connectivity()
        return self.is_enabled
        
    async def get_or_execute(self, ticker: str, asset_class: str, execute_fn: Callable):
        """Get from cache or execute function with graceful fallback.
        
        Implements:
        - Requirement 1.1: Continue analysis without caching on timeout
        - Requirement 5.1: Perform full analysis when cache unavailable
        - Requirement 5.2: Proceed with fresh analysis on cache read failure
        - Requirement 5.4: Reject stale cached data older than 24 hours
        """
        # Skip cache if not enabled (Requirement 1.1)
        if not self.is_enabled:
            logger.debug(f"Cache disabled - executing fresh analysis for {ticker}")
            return await execute_fn(), False
            
        # Try cache read with timeout (Requirement 2.2)
        try:
            cached = await asyncio.wait_for(
                self.repository.get_cached_analysis(ticker, asset_class),
                timeout=self.client.read_timeout
            )
            
            # Check cache freshness (Requirement 5.4)
            if cached:
                cache_age = datetime.now() - cached.get('timestamp', datetime.min)
                if cache_age > timedelta(hours=self.cache_ttl_hours):
                    logger.warning(f"⚠️ Cached data for {ticker} is stale ({cache_age.hours}h old) - fetching fresh")
                    cached = None
                else:
                    logger.debug(f"✅ Cache HIT for {ticker}")
                    return cached, True
                    
        except asyncio.TimeoutError:
            # Requirement 1.1, 2.4: Log timeout and continue
            logger.warning(f"⚠️ Cache read timeout for {ticker} - proceeding with fresh analysis")
        except Exception as e:
            # Requirement 1.2: Log warnings, not errors
            logger.warning(f"⚠️ Cache read failed for {ticker}: {e}")
            
        # Execute fresh analysis (Requirement 5.1, 5.2)
        result = await execute_fn()
        
        # Try cache write (non-blocking) (Requirement 5.3)
        if self.is_enabled:
            asyncio.create_task(self._store_async(ticker, asset_class, result))
            
        return result, False
        
    async def _store_async(self, ticker: str, asset_class: str, data: dict):
        """Store in cache asynchronously without blocking (Requirement 1.5, 5.3)."""
        try:
            await asyncio.wait_for(
                self.repository.store_analysis(ticker, asset_class, data),
                timeout=self.client.write_timeout
            )
            logger.debug(f"✅ Cached {ticker}")
        except asyncio.TimeoutError:
            # Requirement 2.4, 5.3: Log timeout and continue
            logger.warning(f"⚠️ Cache write timeout for {ticker}")
        except Exception as e:
            # Requirement 1.2, 5.3: Log warnings, not errors
            logger.warning(f"⚠️ Cache write failed for {ticker}: {e}")
```

**Design Rationale**:
- Cache freshness check ensures Requirement 5.4 compliance (no stale data > 24 hours)
- All timeout scenarios log warnings (not errors) per Requirement 1.2
- Non-blocking cache writes ensure Requirement 1.5 (no delays in analysis workflow)
- Graceful degradation at every step ensures Requirement 5.5 (same quality with/without cache)

### 3. Flow Orchestrator Integration

**File**: `src/finwiz/flows/flow_orchestrator.py`

**Changes**:
```python
class FinwizFlow(Flow[FinwizState]):
    def __init__(self):
        super().__init__()
        self.cache_service = None
        self.cache_enabled = False
        
    async def _initialize_cache(self):
        """Initialize cache service with connectivity test."""
        try:
            from finwiz.supabase.services.cache_service import get_cache_service
            
            cache_service = get_cache_service()
            if cache_service:
                self.cache_enabled = await cache_service.initialize()
                if self.cache_enabled:
                    self.cache_service = cache_service
                    logger.info("✅ Supabase caching enabled")
                else:
                    logger.info("ℹ️ Supabase caching disabled - analysis will proceed without cache")
            else:
                logger.info("ℹ️ No cache service configured")
        except Exception as e:
            logger.warning(f"⚠️ Cache initialization failed: {e}")
            self.cache_enabled = False
            
    @start()
    def validate_data_integration(self) -> dict[str, Any]:
        """Validate data integration and initialize cache."""
        # Initialize cache asynchronously
        import asyncio
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._initialize_cache())
        
        # Log cache status
        if self.cache_enabled:
            logger.info("📊 Cache Status: ENABLED")
        else:
            logger.info("📊 Cache Status: DISABLED (analysis will proceed normally)")
            
        return {"cache_enabled": self.cache_enabled}
```

## Data Models

### Configuration Model

```python
from pydantic import BaseModel, Field

class SupabaseConfig(BaseModel):
    """Supabase configuration with defaults."""
    url: str = Field(..., description="Supabase project URL")
    key: str = Field(..., description="Supabase anon/service key")
    read_timeout: float = Field(10.0, description="Read operation timeout in seconds")
    write_timeout: float = Field(15.0, description="Write operation timeout in seconds")
    max_retries: int = Field(3, description="Maximum retry attempts (max 3 per Requirement 2.5)")
    connectivity_test_timeout: float = Field(5.0, description="Connectivity test timeout")
    cache_ttl_hours: int = Field(24, description="Cache time-to-live in hours (Requirement 5.4)")
    
    class Config:
        frozen = True
```

**Design Rationale**: 
- `max_retries` set to 3 to satisfy Requirement 2.5 (SHALL NOT retry more than 3 times)
- Added `cache_ttl_hours` to enforce Requirement 5.4 (SHALL NOT use stale cached data older than 24 hours)

### Health Status Model

```python
from pydantic import BaseModel, Field
from datetime import datetime

class SupabaseHealthStatus(BaseModel):
    """Supabase health status for monitoring (Requirement 4.4).
    
    Exposes comprehensive health metrics for diagnostics and monitoring.
    """
    is_available: bool = Field(..., description="Connectivity test result")
    last_test_timestamp: datetime = Field(..., description="Last connectivity test time")
    success_rate: float = Field(ge=0.0, le=1.0, description="Operation success rate (Requirement 4.1)")
    avg_response_time_ms: float = Field(..., description="Average response time in ms (Requirement 4.2)")
    circuit_breaker_state: str = Field(..., description="Circuit breaker state (Requirement 4.3)")
    circuit_breaker_open: bool = Field(..., description="Whether circuit breaker is open")
    total_operations: int = Field(ge=0, description="Total operations attempted")
    successful_operations: int = Field(ge=0, description="Successful operations")
    failed_operations: int = Field(ge=0, description="Failed operations")
    timeout_count: int = Field(ge=0, description="Number of timeouts")
    configuration: dict = Field(..., description="Current timeout configuration (Requirement 4.5)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "is_available": True,
                "last_test_timestamp": "2025-11-01T10:30:00Z",
                "success_rate": 0.95,
                "avg_response_time_ms": 250.5,
                "circuit_breaker_state": "closed",
                "circuit_breaker_open": False,
                "total_operations": 1000,
                "successful_operations": 950,
                "failed_operations": 50,
                "timeout_count": 10,
                "configuration": {
                    "read_timeout": 10.0,
                    "write_timeout": 15.0,
                    "max_retries": 3
                }
            }
        }
```

**Design Rationale**:
- Added `circuit_breaker_state` field to provide detailed state information (Requirement 4.3)
- Added `configuration` field to expose current settings (Requirement 4.5)
- All fields documented with requirement references for traceability
- Example provided for API documentation and testing

## Error Handling

### Timeout Handling

```python
import asyncio
from typing import Callable, Any

async def execute_with_timeout(self, operation: Callable, timeout: float) -> Any | None:
    """Execute operation with timeout and graceful handling (Requirement 2.4).
    
    Args:
        operation: Async operation to execute
        timeout: Timeout in seconds
        
    Returns:
        Operation result or None on failure
    """
    try:
        return await asyncio.wait_for(operation(self.client), timeout=timeout)
    except asyncio.TimeoutError:
        # Requirement 2.4: Log timeout and continue
        logger.warning(f"⚠️ Database operation timed out after {timeout}s")
        return None
    except Exception as e:
        # Requirement 1.2: Log warnings, not errors
        logger.warning(f"⚠️ Database operation failed: {e}")
        return None
```

### Retry Logic

```python
async def execute_with_retry(
    self, 
    operation: Callable, 
    timeout: float,
    operation_name: str = "operation"
) -> Any | None:
    """Execute operation with retry logic (Requirement 2.5).
    
    Implements exponential backoff with maximum 3 retry attempts.
    
    Args:
        operation: Async operation to execute
        timeout: Timeout in seconds per attempt
        operation_name: Name for logging
        
    Returns:
        Operation result or None after all retries exhausted
    """
    max_retries = self.max_retries  # Maximum 3 per Requirement 2.5
    retry_delay = 1.0  # Initial delay in seconds
    
    for attempt in range(max_retries + 1):  # 0-indexed, so +1 for total attempts
        try:
            result = await asyncio.wait_for(operation(self.client), timeout=timeout)
            
            # Success - record metrics
            if attempt > 0:
                logger.info(f"✅ {operation_name} succeeded on retry {attempt}")
            return result
            
        except asyncio.TimeoutError:
            is_last_attempt = (attempt == max_retries)
            
            if is_last_attempt:
                # Requirement 2.5: Maximum retries reached
                logger.warning(
                    f"⚠️ {operation_name} timed out after {max_retries} retries "
                    f"(timeout: {timeout}s per attempt)"
                )
                return None
            else:
                # Retry with exponential backoff
                logger.warning(
                    f"⚠️ {operation_name} timed out (attempt {attempt + 1}/{max_retries + 1}), "
                    f"retrying in {retry_delay}s..."
                )
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                
        except Exception as e:
            is_last_attempt = (attempt == max_retries)
            
            if is_last_attempt:
                logger.warning(f"⚠️ {operation_name} failed after {max_retries} retries: {e}")
                return None
            else:
                logger.warning(
                    f"⚠️ {operation_name} failed (attempt {attempt + 1}/{max_retries + 1}): {e}, "
                    f"retrying in {retry_delay}s..."
                )
                await asyncio.sleep(retry_delay)
                retry_delay *= 2
    
    return None
```

**Design Rationale**:
- Exponential backoff prevents overwhelming the database during recovery
- Maximum 3 retries enforces Requirement 2.5 (SHALL NOT retry more than 3 times)
- Detailed logging at each retry attempt aids debugging
- Separate method allows reuse across different operations

### Circuit Breaker Enhancement

```python
from datetime import datetime, timedelta
from enum import Enum

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Blocking requests
    HALF_OPEN = "half_open"  # Testing recovery

class CircuitBreaker:
    """Circuit breaker implementation (Requirement 1.4)."""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        
    def record_success(self):
        """Record successful operation."""
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            logger.info("✅ Circuit breaker closed - Supabase recovered")
            
    def record_failure(self):
        """Record failed operation (Requirement 4.3)."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold and self.state == CircuitState.CLOSED:
            self.state = CircuitState.OPEN
            # Requirement 4.3: Log failure count and reason
            logger.warning(f"⚠️ Circuit breaker opened after {self.failure_count} failures")
            logger.warning(f"⚠️ Reason: Exceeded failure threshold of {self.failure_threshold}")
            logger.warning("⚠️ Supabase operations suspended - caching disabled")
            
    def should_allow_request(self) -> bool:
        """Check if request should be allowed (Requirement 1.4).
        
        Returns:
            bool: True if request allowed, False if circuit breaker is open
        """
        if self.state == CircuitState.CLOSED:
            return True
            
        if self.state == CircuitState.OPEN:
            # Check if timeout has elapsed
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                self.state = CircuitState.HALF_OPEN
                logger.info("🔄 Circuit breaker half-open - testing Supabase")
                return True
            # Requirement 1.4: Stop attempting operations when open
            return False
            
        # half-open state - allow single test request
        return True
    
    def get_status(self) -> dict:
        """Get circuit breaker status for monitoring (Requirement 4.4)."""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "is_open": self.state == CircuitState.OPEN
        }
```

**Design Rationale**:
- `CircuitState` enum added for type safety and clarity
- `get_status()` method added to satisfy Requirement 4.4 (expose health status)
- Logging enhanced to include failure count and reason per Requirement 4.3
- `should_allow_request()` explicitly implements Requirement 1.4 (stop attempts when open)

## Testing Strategy

### Unit Tests

#### 1. Connectivity Test (Requirement 3)
- **Test successful connectivity** (Requirement 3.1, 3.3)
  - Verify simple query executes within timeout
  - Verify `is_available` flag set to True
  - Verify success message logged
  
- **Test failed connectivity** (Requirement 3.2)
  - Verify warning logged (not error)
  - Verify caching disabled
  - Verify `is_available` flag set to False
  
- **Test timeout during connectivity test** (Requirement 3.4)
  - Verify test completes within 5 seconds
  - Verify startup not blocked
  - Verify graceful handling

- **Test startup resilience** (Requirement 3.5)
  - Verify startup succeeds with Supabase unavailable
  - Verify no exceptions raised
  - Verify system continues initialization

#### 2. Graceful Degradation (Requirement 1, 5)
- **Test analysis without cache** (Requirement 1.1, 5.1)
  - Verify full analysis executes
  - Verify no cache operations attempted
  - Verify same quality results
  
- **Test cache read timeout** (Requirement 1.1, 5.2)
  - Verify analysis continues after timeout
  - Verify warning logged (not error)
  - Verify fresh analysis performed
  
- **Test cache write timeout** (Requirement 1.5, 5.3)
  - Verify analysis completes
  - Verify write failure logged
  - Verify no blocking delay
  
- **Test stale cache rejection** (Requirement 5.4)
  - Verify cached data >24 hours rejected
  - Verify fresh analysis performed
  - Verify warning logged

- **Test analysis quality consistency** (Requirement 5.5)
  - Verify same results with/without cache
  - Verify same recommendation quality
  - Verify same risk assessment

#### 3. Circuit Breaker (Requirement 1.4, 4.3)
- **Test circuit breaker opening**
  - Verify opens after threshold failures
  - Verify failure count logged (Requirement 4.3)
  - Verify reason logged (Requirement 4.3)
  - Verify operations stopped (Requirement 1.4)
  
- **Test circuit breaker recovery**
  - Verify transitions to half-open after timeout
  - Verify test request allowed
  - Verify closes on successful operation
  
- **Test half-open state**
  - Verify single test request allowed
  - Verify reopens on failure
  - Verify closes on success

#### 4. Timeout Configuration (Requirement 2)
- **Test environment variable support** (Requirement 2.1)
  - Verify SUPABASE_TIMEOUT_SECONDS respected
  - Verify fallback to defaults
  
- **Test timeout defaults** (Requirement 2.2, 2.3)
  - Verify 10-second read timeout
  - Verify 15-second write timeout
  
- **Test timeout logging** (Requirement 2.4)
  - Verify timeout logged
  - Verify system continues
  
- **Test retry limits** (Requirement 2.5)
  - Verify maximum 3 retries
  - Verify exponential backoff
  - Verify final failure logged

#### 5. Monitoring and Metrics (Requirement 4)
- **Test metrics tracking** (Requirement 4.1, 4.2)
  - Verify success/failure rates calculated
  - Verify response times tracked
  - Verify metrics logged periodically
  
- **Test configuration logging** (Requirement 4.5)
  - Verify timeout settings logged at startup
  - Verify retry settings logged
  - Verify circuit breaker settings logged
  
- **Test health status** (Requirement 4.4)
  - Verify health status endpoint returns correct data
  - Verify all metrics included
  - Verify circuit breaker state included

### Integration Tests

#### 1. End-to-End with Cache
- Full analysis with working cache
- Verify cache hits and misses
- Verify performance improvement
- Verify cache freshness checks

#### 2. End-to-End without Cache
- Full analysis with disabled cache
- Verify same results as with cache (Requirement 5.5)
- Verify acceptable performance
- Verify no errors or exceptions

#### 3. End-to-End with Intermittent Failures
- Simulate random timeouts
- Verify retry logic works
- Verify circuit breaker behavior
- Verify analysis always completes

### Performance Tests

#### 1. Timeout Tuning
- Test various timeout values (5s, 10s, 15s, 30s)
- Measure impact on total execution time
- Find optimal timeout settings
- Verify < 10% timeout rate target

#### 2. Retry Logic Performance
- Test retry behavior under load
- Measure retry overhead
- Verify retry limits enforced (Requirement 2.5)
- Verify exponential backoff timing

#### 3. Cache Performance Impact
- Compare execution time with/without cache
- Measure cache hit rate
- Verify cache freshness checks don't impact performance
- Verify non-blocking writes don't delay analysis

## Configuration

### Environment Variables

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Timeout Configuration (seconds) - Requirement 2.1, 2.2, 2.3
SUPABASE_TIMEOUT_SECONDS=10.0           # Generic timeout (Requirement 2.1)
SUPABASE_READ_TIMEOUT=10.0              # Read operation timeout (Requirement 2.2)
SUPABASE_WRITE_TIMEOUT=15.0             # Write operation timeout (Requirement 2.3)
SUPABASE_CONNECTIVITY_TEST_TIMEOUT=5.0  # Connectivity test timeout (Requirement 3.4)

# Retry Configuration - Requirement 2.5
SUPABASE_MAX_RETRIES=3                  # Maximum 3 retries (Requirement 2.5)

# Circuit Breaker Configuration - Requirement 1.4
SUPABASE_CIRCUIT_BREAKER_THRESHOLD=5    # Failures before opening
SUPABASE_CIRCUIT_BREAKER_TIMEOUT=60     # Seconds before retry

# Cache Configuration - Requirement 5.4
ANALYSIS_CACHE_TTL_HOURS=24             # Cache TTL (Requirement 5.4)
CACHE_ENABLED=true                      # Set to false to disable caching entirely
```

**Design Rationale**:
- `SUPABASE_TIMEOUT_SECONDS` added to satisfy Requirement 2.1 (SHALL support environment variable)
- `SUPABASE_MAX_RETRIES` set to 3 to comply with Requirement 2.5 (SHALL NOT retry more than 3 times)
- All timeout values documented with requirement references for traceability

### Logging Configuration

```python
# Log levels for Supabase operations
SUPABASE_LOG_LEVEL=WARNING  # Don't spam logs with cache misses
SUPABASE_METRICS_LOG_LEVEL=INFO  # Log metrics and health status
```

## Deployment Strategy

### Phase 1: Increase Timeouts (Immediate)

- Update default timeouts to 10s/15s
- Deploy and monitor
- Verify if timeout issues resolve

### Phase 2: Add Connectivity Test (Next)

- Implement startup connectivity test
- Add graceful degradation
- Deploy and monitor

### Phase 3: Enhanced Monitoring (Final)

- Add health status endpoint
- Implement metrics tracking
- Create monitoring dashboard

## Monitoring and Metrics

### Key Metrics

1. **Supabase Availability**
   - Connectivity test success rate
   - Circuit breaker state
   - Time since last successful operation

2. **Operation Performance**
   - Average response time
   - Timeout rate
   - Success rate by operation type

3. **Cache Effectiveness**
   - Cache hit rate
   - Cache miss rate
   - Time saved by caching

### Alerts

1. **Critical**: Circuit breaker open for > 5 minutes
2. **Warning**: Timeout rate > 50%
3. **Info**: Cache disabled at startup

## Success Criteria

### Requirement Validation

1. ✅ **Requirement 1 (Graceful Degradation)**: System completes analysis with 0% Supabase availability
   - 1.1: Analysis continues without caching on timeout
   - 1.2: Warnings logged (not errors) when Supabase unavailable
   - 1.3: Full analysis workflow completes despite all Supabase failures
   - 1.4: Circuit breaker stops attempts when open
   - 1.5: No blocking delays waiting for Supabase responses

2. ✅ **Requirement 2 (Timeout Configuration)**: Configurable timeouts with proper defaults
   - 2.1: SUPABASE_TIMEOUT_SECONDS environment variable supported
   - 2.2: 10-second default for read operations
   - 2.3: 15-second default for write operations
   - 2.4: Timeouts logged and system continues
   - 2.5: Maximum 3 retry attempts

3. ✅ **Requirement 3 (Initialization Validation)**: Startup connectivity test
   - 3.1: Simple query tests connectivity at startup
   - 3.2: Warning logged and caching disabled on failure
   - 3.3: Caching enabled on successful test
   - 3.4: Startup completes within 5 seconds regardless of Supabase status
   - 3.5: Startup does not fail if Supabase unavailable

4. ✅ **Requirement 4 (Monitoring and Metrics)**: Visibility into Supabase performance
   - 4.1: Success/failure rates logged
   - 4.2: Average response times tracked
   - 4.3: Circuit breaker state changes logged with failure count
   - 4.4: Health status exposed via metrics
   - 4.5: Configuration logged at startup

5. ✅ **Requirement 5 (Fallback Behavior)**: Consistent analysis quality
   - 5.1: Full analysis performed when cache unavailable
   - 5.2: Fresh analysis on cache read failure
   - 5.3: Analysis completes and logs failure on cache write failure
   - 5.4: Stale cached data (>24 hours) rejected
   - 5.5: Same analysis quality with or without caching

### Performance Targets

- Timeout rate < 10% when Supabase is available
- Circuit breaker recovers automatically
- No blocking delays in analysis workflow
- Clear logging of cache status and issues
