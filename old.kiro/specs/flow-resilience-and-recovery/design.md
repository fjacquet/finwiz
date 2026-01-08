# Design Document: Flow Resilience and Recovery

## Overview

This design implements comprehensive resilience and recovery capabilities for the FinWiz flow orchestrator using CrewAI native patterns. The system will automatically retry failed operations, checkpoint progress, resume interrupted flows, and handle partial failures gracefully.

**Key Design Principle:** Leverage CrewAI native features (@persist(), conditional @start(), structured state) rather than building custom infrastructure.

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FinwizFlow (Flow[FinwizState])           │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  @persist() - Automatic State Persistence            │  │
│  │  • Saves after each flow method                      │  │
│  │  • Uses CrewAI native persistence                    │  │
│  │  • Atomic file operations                            │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Conditional @start() - Resume Capability            │  │
│  │  • Check for persisted state                         │  │
│  │  • Skip completed work                               │  │
│  │  • Continue from last checkpoint                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Retry Logic - Exponential Backoff                  │  │
│  │  • Tenacity library integration                      │  │
│  │  • Configurable retry limits                         │  │
│  │  • Error classification                              │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Timeout Management - Async Timeouts                │  │
│  │  • Per-holding timeouts                              │  │
│  │  • Global flow timeout                               │  │
│  │  • Graceful cancellation                             │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Progress Tracking - Real-time Updates              │  │
│  │  • Holdings processed/remaining                      │  │
│  │  • Success/failure rates                             │  │
│  │  • Estimated time remaining                          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Existing Infrastructure Integration            │
│                                                             │
│  • ValidationError (error classification)                   │
│  • AlertManager (critical alerts)                           │
│  • get_logger() (structured logging)                        │
│  • os.getenv() (configuration)                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Enhanced Flow State (FinwizState)

**Location:** `src/finwiz/flow_state.py`

**Changes:** Add resilience tracking fields to existing FinwizState

```python
class FinwizState(BaseModel):
    """Enhanced state with resilience tracking."""
    
    # ... existing fields ...
    
    # Resilience tracking (NEW)
    total_holdings: int = 0
    holdings_processed: int = 0
    holdings_remaining: int = 0
    current_ticker: str = ""
    progress_percentage: float = 0.0
    
    # Timing (NEW)
    flow_start_time: datetime = Field(default_factory=datetime.now)
    last_checkpoint_time: datetime | None = None
    estimated_time_remaining: float = 0.0
    
    # Error tracking (NEW)
    failed_holdings: list[str] = []
    retry_counts: dict[str, int] = {}
    timeout_holdings: list[str] = []
    
    # Retry metadata (NEW)
    retryable_errors: list[ValidationError] = []
    non_retryable_errors: list[ValidationError] = []
    
    # Resume metadata (NEW)
    resume_from_checkpoint: bool = False
    checkpoint_uuid: str | None = None
```

**Design Rationale:**
- Extends existing FinwizState (no breaking changes)
- Uses Pydantic for type safety
- Tracks all resilience metrics in structured state
- Compatible with @persist() decorator

---

### 2. Resilience Configuration

**Location:** `src/finwiz/config/resilience_config.py` (NEW)

**Purpose:** Centralized configuration for resilience features

```python
from dataclasses import dataclass
import os

@dataclass
class ResilienceConfig:
    """Configuration for flow resilience features."""
    
    # Retry configuration (NEW - following FINWIZ_ prefix pattern)
    max_retries: int = int(os.getenv("FINWIZ_MAX_RETRIES", "3"))
    retry_base_delay: float = float(os.getenv("FINWIZ_RETRY_BASE_DELAY", "2"))
    retry_max_delay: float = float(os.getenv("FINWIZ_RETRY_MAX_DELAY", "60"))
    
    # Timeout configuration (NEW - following FINWIZ_ prefix pattern)
    holding_timeout: int = int(os.getenv("FINWIZ_HOLDING_TIMEOUT", "300"))
    flow_timeout: int = int(os.getenv("FINWIZ_FLOW_TIMEOUT", "7200"))
    
    # Resume configuration (NEW - following FINWIZ_ prefix pattern)
    auto_resume: bool = os.getenv("FINWIZ_AUTO_RESUME", "false").lower() == "true"
    state_max_age_hours: int = int(os.getenv("FINWIZ_STATE_MAX_AGE_HOURS", "24"))
    
    # Parallelization (RENAMED for consistency - old names not used in codebase)
    parallel_limit: int = int(os.getenv("FINWIZ_PARALLEL_LIMIT", "10"))
    deep_analysis_parallel_limit: int = int(os.getenv("FINWIZ_DEEP_ANALYSIS_PARALLEL_LIMIT", "3"))
    
    def validate(self) -> None:
        """Validate configuration values."""
        if self.holding_timeout >= self.flow_timeout:
            raise ValueError("holding_timeout must be less than flow_timeout")
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if self.state_max_age_hours < 1:
            raise ValueError("state_max_age_hours must be at least 1")

def get_resilience_config() -> ResilienceConfig:
    """Get validated resilience configuration."""
    config = ResilienceConfig()
    config.validate()
    return config
```

**Design Rationale:**
- Uses existing os.getenv() pattern
- Dataclass for simplicity
- Validation ensures sensible values
- Singleton pattern via function

---

### 3. Retry Logic with Exponential Backoff

**Location:** `src/finwiz/utils/retry_handler.py` (NEW)

**Purpose:** Centralized retry logic using tenacity library

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
from finwiz.config.resilience_config import get_resilience_config
from finwiz.validation.result import ValidationError
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

# Retryable exception types
RETRYABLE_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    # Add more as needed
)

def create_retry_decorator(config: ResilienceConfig | None = None):
    """Create a retry decorator with configured parameters."""
    if config is None:
        config = get_resilience_config()
    
    return retry(
        stop=stop_after_attempt(config.max_retries),
        wait=wait_exponential(
            multiplier=config.retry_base_delay,
            max=config.retry_max_delay
        ),
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )

def classify_error(error: Exception) -> tuple[str, bool]:
    """
    Classify error as retryable or non-retryable.
    
    Returns:
        (error_type, is_retryable)
    """
    if isinstance(error, ConnectionError):
        return ("network", True)
    elif isinstance(error, TimeoutError):
        return ("timeout", True)
    elif "rate limit" in str(error).lower():
        return ("rate_limit", True)
    elif "authentication" in str(error).lower():
        return ("authentication", False)
    elif "validation" in str(error).lower():
        return ("validation", False)
    else:
        return ("unknown", False)

def create_validation_error_from_exception(
    error: Exception,
    ticker: str,
    attempt: int
) -> ValidationError:
    """Create ValidationError from exception for tracking."""
    error_type, is_retryable = classify_error(error)
    
    return ValidationError(
        field_path=f"holding.{ticker}",
        error_type=error_type,
        message=str(error),
        context={
            "ticker": ticker,
            "attempt": attempt,
            "is_retryable": is_retryable,
            "timestamp": datetime.now().isoformat(),
            "remediation": get_remediation_suggestion(error_type)
        }
    )

def get_remediation_suggestion(error_type: str) -> str:
    """Get remediation suggestion for error type."""
    suggestions = {
        "network": "Check network connectivity and API status",
        "rate_limit": "Reduce parallelism or increase delays",
        "timeout": "Increase timeout or check API performance",
        "authentication": "Check API keys in environment variables",
        "validation": "Check ticker symbols and input data",
    }
    return suggestions.get(error_type, "Review error details and logs")
```

**Design Rationale:**
- Uses tenacity library (industry standard)
- Integrates with existing ValidationError
- Provides error classification
- Configurable via ResilienceConfig
- Includes remediation suggestions

---

### 4. Timeout Management

**Location:** `src/finwiz/utils/timeout_handler.py` (NEW)

**Purpose:** Async timeout enforcement

```python
import asyncio
from typing import Any, Callable, TypeVar
from finwiz.config.resilience_config import get_resilience_config
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T')

async def with_timeout(
    coro: Callable[..., Any],
    timeout_seconds: int,
    operation_name: str,
    **kwargs
) -> Any:
    """
    Execute coroutine with timeout.
    
    Args:
        coro: Async function to execute
        timeout_seconds: Timeout in seconds
        operation_name: Name for logging
        **kwargs: Arguments to pass to coro
    
    Returns:
        Result from coroutine or None on timeout
    
    Raises:
        asyncio.TimeoutError: If timeout is exceeded
    """
    try:
        result = await asyncio.wait_for(
            coro(**kwargs),
            timeout=timeout_seconds
        )
        return result
    except asyncio.TimeoutError:
        logger.error(
            f"Timeout: {operation_name} exceeded {timeout_seconds}s timeout"
        )
        raise

async def with_timeout_graceful(
    coro: Callable[..., Any],
    timeout_seconds: int,
    operation_name: str,
    fallback_value: Any = None,
    **kwargs
) -> Any:
    """
    Execute coroutine with timeout and graceful fallback.
    
    Args:
        coro: Async function to execute
        timeout_seconds: Timeout in seconds
        operation_name: Name for logging
        fallback_value: Value to return on timeout
        **kwargs: Arguments to pass to coro
    
    Returns:
        Result from coroutine or fallback_value on timeout
    """
    try:
        return await with_timeout(coro, timeout_seconds, operation_name, **kwargs)
    except asyncio.TimeoutError:
        logger.warning(
            f"Timeout: {operation_name} - returning fallback value"
        )
        return fallback_value
```

**Design Rationale:**
- Uses asyncio.wait_for (standard library)
- Provides both strict and graceful variants
- Integrates with existing logger
- Type-safe with TypeVar

---

### 5. Enhanced Flow Orchestrator

**Location:** `src/finwiz/flows/flow_orchestrator.py` (MODIFY)

**Changes:** Add @persist(), conditional @start(), retry logic, timeouts

```python
from crewai.flow.persistence import persist
from finwiz.config.resilience_config import get_resilience_config
from finwiz.utils.retry_handler import create_retry_decorator, create_validation_error_from_exception
from finwiz.utils.timeout_handler import with_timeout_graceful

@persist()  # ✅ NEW: Enable automatic state persistence
class FinwizFlow(Flow[FinwizState]):
    """Orchestrates the financial analysis workflow with resilience."""
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize with resilience configuration."""
        super().__init__(*args, **kwargs)
        
        # ... existing initialization ...
        
        # NEW: Load resilience configuration
        self.resilience_config = get_resilience_config()
        logger.info(f"Resilience config loaded: {self.resilience_config}")
        
        # NEW: Create retry decorator
        self.retry_decorator = create_retry_decorator(self.resilience_config)
    
    @start()  # Unconditional start
    def validate_data_integration(self):
        """Validate data integration (always runs)."""
        # ... existing logic ...
        
        # NEW: Initialize resilience tracking
        self.state.flow_start_time = datetime.now()
        self.state.resume_from_checkpoint = False
        
        return "Validated"
    
    @start("validate_data_integration")  # ✅ NEW: Conditional start for resume
    def check_portfolio(self):
        """Check portfolio (can be resumed)."""
        # NEW: Check if already completed
        if self.state.portfolio_review is not None:
            logger.info("Resume: Portfolio already analyzed, skipping")
            return "Skipped"
        
        # ... existing portfolio analysis logic ...
        
        return "Complete"
    
    @listen("check_portfolio")
    async def analyze_and_update_portfolio(self) -> dict[str, Any]:
        """
        Atomic operation: deep analysis + alternatives + portfolio update.
        
        ✅ NEW: With retry logic, timeout management, and progress tracking
        """
        enabled = os.getenv("DEEP_PORTFOLIO_ANALYSIS", "false").lower() == "true"
        if not enabled:
            logger.info("Deep portfolio analysis disabled")
            return {}
        
        # NEW: Initialize progress tracking
        holdings = self._get_holdings_for_deep_analysis()
        self.state.total_holdings = len(holdings)
        self.state.holdings_processed = 0
        self.state.holdings_remaining = len(holdings)
        
        try:
            # Step 1: Deep analysis with retry and timeout
            deep_results = await self._run_deep_analysis_with_resilience(holdings)
            
            # Step 2: Match alternatives
            alternatives = self._match_alternatives_for_holdings(deep_results)
            
            # Step 3: Update portfolio (ONCE)
            portfolio_updated = self._update_portfolio_review_with_enriched_data()
            
            # Update state
            self.state.deep_analysis_success = True
            self.state.deep_analysis_results = deep_results
            self.state.portfolio_alternatives = alternatives
            
            return {
                "deep_analysis_complete": True,
                "analysis_results": deep_results,
                "alternatives_data": alternatives,
                "portfolio_updated": portfolio_updated
            }
            
        except Exception as e:
            logger.error(f"Deep analysis failed: {e}")
            self.state.deep_analysis_error = str(e)
            return {}
    
    async def _run_deep_analysis_with_resilience(
        self,
        holdings: list[dict]
    ) -> dict[str, DeepAnalysisResult]:
        """
        Run deep analysis with retry, timeout, and progress tracking.
        
        ✅ NEW: Resilience features integrated
        """
        results = {}
        
        # Process in parallel batches with concurrency limit
        batch_size = self.resilience_config.deep_analysis_parallel_limit
        
        for i in range(0, len(holdings), batch_size):
            batch = holdings[i:i + batch_size]
            
            # Process batch in parallel
            batch_tasks = [
                self._analyze_single_holding_with_resilience(holding)
                for holding in batch
            ]
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Collect results and update progress
            for holding, result in zip(batch, batch_results):
                ticker = holding["ticker"]
                
                if isinstance(result, Exception):
                    logger.error(f"Failed to analyze {ticker}: {result}")
                    self.state.failed_holdings.append(ticker)
                elif result is not None:
                    results[ticker] = result
                
                # Update progress
                self.state.holdings_processed += 1
                self.state.holdings_remaining -= 1
                self.state.progress_percentage = (
                    self.state.holdings_processed / self.state.total_holdings * 100
                )
                
                # Log progress
                logger.info(
                    f"Progress: {self.state.holdings_processed}/{self.state.total_holdings} "
                    f"({self.state.progress_percentage:.1f}%) - "
                    f"Success: {len(results)}, Failed: {len(self.state.failed_holdings)}"
                )
        
        return results
    
    async def _analyze_single_holding_with_resilience(
        self,
        holding: dict
    ) -> DeepAnalysisResult | None:
        """
        Analyze single holding with retry and timeout.
        
        ✅ NEW: Retry logic + timeout management
        """
        ticker = holding["ticker"]
        asset_class = holding["asset_class"]
        
        # Track retry attempts
        if ticker not in self.state.retry_counts:
            self.state.retry_counts[ticker] = 0
        
        # Create retry-aware analysis function
        @self.retry_decorator
        async def analyze_with_retry(attempt: int = 1):
            self.state.retry_counts[ticker] = attempt
            self.state.current_ticker = ticker
            
            # Adjust reasoning attempts based on retry
            max_reasoning = max(1, 4 - attempt)
            
            # Execute with timeout
            result = await with_timeout_graceful(
                self._execute_deep_analysis_crew,
                timeout_seconds=self.resilience_config.holding_timeout,
                operation_name=f"Deep analysis for {ticker}",
                fallback_value=None,
                ticker=ticker,
                asset_class=asset_class,
                max_reasoning_attempts=max_reasoning
            )
            
            return result
        
        try:
            result = await analyze_with_retry()
            return result
            
        except Exception as e:
            # Create ValidationError for tracking
            error = create_validation_error_from_exception(e, ticker, self.state.retry_counts[ticker])
            
            # Classify and store
            if error.context.get("is_retryable"):
                self.state.retryable_errors.append(error)
            else:
                self.state.non_retryable_errors.append(error)
            
            logger.error(f"All retries exhausted for {ticker}: {e}")
            return None
    
    async def _execute_deep_analysis_crew(
        self,
        ticker: str,
        asset_class: str,
        max_reasoning_attempts: int
    ) -> DeepAnalysisResult:
        """Execute deep analysis crew (existing logic)."""
        # ... existing crew execution logic ...
        pass
```

**Design Rationale:**
- Uses @persist() for automatic checkpointing
- Conditional @start() enables resume
- Integrates retry logic with tenacity
- Uses async timeouts with asyncio
- Tracks progress in structured state
- Graceful degradation on failures
- Maintains existing API compatibility

---

## Data Models

### Enhanced FinwizState

See Component 1 above for complete model.

**Key Fields:**
- `total_holdings`, `holdings_processed`, `holdings_remaining` - Progress tracking
- `failed_holdings`, `retry_counts`, `timeout_holdings` - Error tracking
- `retryable_errors`, `non_retryable_errors` - Error classification
- `flow_start_time`, `last_checkpoint_time` - Timing
- `resume_from_checkpoint`, `checkpoint_uuid` - Resume metadata

---

## Error Handling

### Error Classification

**Retryable Errors:**
- `ConnectionError` - Network issues
- `TimeoutError` - Operation timeouts
- Rate limit errors (detected by message content)

**Non-Retryable Errors:**
- Authentication errors
- Validation errors
- Invalid ticker errors

### Error Storage

Errors stored in FinwizState using existing ValidationError:

```python
self.state.retryable_errors.append(ValidationError(
    field_path=f"holding.{ticker}",
    error_type="network",
    message="Connection failed",
    context={
        "ticker": ticker,
        "attempt": 2,
        "is_retryable": True,
        "remediation": "Check network connectivity"
    }
))
```

### Integration with AlertManager

Critical failures trigger alerts:

```python
from finwiz.monitoring.alerting import AlertManager, Alert, AlertSeverity

if len(self.state.failed_holdings) / self.state.total_holdings > 0.5:
    alert_manager = AlertManager()
    alert_manager.create_alert(
        Alert(
            type=AlertType.ERROR_RATE,
            severity=AlertSeverity.CRITICAL,
            title="High Failure Rate in Deep Analysis",
            message=f"{len(self.state.failed_holdings)}/{self.state.total_holdings} holdings failed",
            metadata={"failed_holdings": self.state.failed_holdings}
        )
    )
```

---

## Testing Strategy

### Unit Tests

**Location:** `tests/unit/flows/test_resilience.py` (NEW)

**Coverage:**
- ResilienceConfig validation
- Error classification logic
- Retry decorator behavior (mocked)
- Timeout handler (mocked)
- Progress calculation
- ValidationError creation

**Example:**
```python
def test_should_classify_network_error_as_retryable():
    error = ConnectionError("Network unreachable")
    error_type, is_retryable = classify_error(error)
    
    assert error_type == "network"
    assert is_retryable is True

def test_should_classify_auth_error_as_non_retryable():
    error = Exception("Authentication failed")
    error_type, is_retryable = classify_error(error)
    
    assert error_type == "authentication"
    assert is_retryable is False
```

### Integration Tests

**Location:** `tests/integration/test_flow_resilience.py` (NEW)

**Coverage:**
- Flow state persistence (with mocked @persist())
- Conditional @start() resume logic
- Retry logic with mocked failures
- Timeout enforcement with mocked delays
- Progress tracking through full flow
- Error aggregation and reporting

**Example:**
```python
@pytest.mark.integration
async def test_should_resume_from_checkpoint(mocker):
    # Mock persisted state
    mock_state = FinwizState(
        portfolio_review={"existing": "data"},
        holdings_processed=10,
        total_holdings=20
    )
    
    # Create flow with mocked state
    flow = FinwizFlow()
    flow.state = mock_state
    
    # Execute - should skip portfolio analysis
    result = await flow.check_portfolio()
    
    assert result == "Skipped"
    assert flow.state.holdings_processed == 10  # Unchanged
```

---

## Performance Considerations

### Overhead Analysis

| Feature | Overhead | Impact |
|---------|----------|--------|
| @persist() | ~10-50ms per method | Minimal |
| Conditional @start() | ~5-10ms per check | Negligible |
| Retry logic | 2-60s per retry | Only on failures |
| Timeout management | ~1-5ms per operation | Negligible |
| Progress tracking | ~1ms per update | Negligible |

**Total overhead for successful execution:** < 100ms
**Total overhead for failed execution with retries:** 6-180s (3 retries)

### Optimization Strategies

1. **Batch checkpointing** - Use method-level @persist() instead of class-level for less frequent saves
2. **Parallel processing** - Maintain existing parallelization (10 concurrent holdings)
3. **Smart retry** - Reduce reasoning attempts on retries (4 → 3 → 2 → 1)
4. **Timeout tuning** - Adjust timeouts based on historical data

---

## Monitoring and Observability

### Metrics Tracked in State

- `holdings_processed` / `total_holdings` - Progress
- `len(failed_holdings)` - Failure count
- `retry_counts` - Retry attempts per holding
- `progress_percentage` - Overall progress
- `estimated_time_remaining` - ETA

### Logging

**Progress logs:**
```
INFO: Progress: 10/66 (15.2%) - Success: 9, Failed: 1
INFO: Retry attempt 2/3 for AAPL after network error
INFO: Timeout: Deep analysis for TSLA exceeded 300s timeout
```

**Error logs:**
```
ERROR: All retries exhausted for AAPL: ConnectionError
WARNING: High failure rate: 35/66 (53%) holdings failed
```

### Integration with Existing Monitoring

```python
# Export metrics to JSON for dashboards
metrics = {
    "flow_uuid": str(self.state.id),
    "total_holdings": self.state.total_holdings,
    "holdings_processed": self.state.holdings_processed,
    "success_rate": len(results) / self.state.total_holdings,
    "retry_count": sum(self.state.retry_counts.values()),
    "timeout_count": len(self.state.timeout_holdings),
    "execution_time": (datetime.now() - self.state.flow_start_time).total_seconds()
}

with open(f".finwiz/metrics/{self.state.id}.json", "w") as f:
    json.dump(metrics, f, indent=2)
```

---

## Resume Capability with User Interaction

### State Discovery and Management

**Location:** `src/finwiz/utils/flow_state_manager.py` (NEW)

**Purpose:** Discover, list, and manage persisted flow states

```python
from pathlib import Path
from datetime import datetime, timedelta
import json
from typing import Optional
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

class FlowStateManager:
    """Manages discovery and loading of persisted flow states."""
    
    def __init__(self):
        # CrewAI stores state in ~/.crewai/state/ by default
        self.state_dir = Path.home() / ".crewai" / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)
    
    def discover_persisted_states(self) -> list[dict]:
        """
        Discover all persisted flow states.
        
        Returns:
            List of state metadata dicts with: uuid, age_hours, progress, last_update
        """
        states = []
        
        if not self.state_dir.exists():
            return states
        
        # Find all .db files (CrewAI SQLite persistence)
        for state_file in self.state_dir.glob("*.db"):
            try:
                metadata = self._extract_state_metadata(state_file)
                if metadata:
                    states.append(metadata)
            except Exception as e:
                logger.warning(f"Failed to read state {state_file}: {e}")
        
        # Sort by last update (newest first)
        states.sort(key=lambda x: x["last_update"], reverse=True)
        
        return states
    
    def _extract_state_metadata(self, state_file: Path) -> Optional[dict]:
        """Extract metadata from state file."""
        import sqlite3
        
        try:
            conn = sqlite3.connect(str(state_file))
            cursor = conn.cursor()
            
            # Query latest state
            cursor.execute("""
                SELECT state_data, created_at 
                FROM flow_state 
                ORDER BY created_at DESC 
                LIMIT 1
            """)
            
            row = cursor.fetchone()
            if not row:
                return None
            
            state_json, created_at = row
            state_data = json.loads(state_json)
            
            # Extract FinwizState fields
            holdings_processed = state_data.get("holdings_processed", 0)
            total_holdings = state_data.get("total_holdings", 0)
            flow_start_time = state_data.get("flow_start_time")
            
            # Calculate age
            if flow_start_time:
                start_dt = datetime.fromisoformat(flow_start_time)
                age_hours = (datetime.now() - start_dt).total_seconds() / 3600
            else:
                age_hours = 0
            
            conn.close()
            
            return {
                "uuid": state_file.stem,  # Filename without extension
                "file_path": str(state_file),
                "age_hours": age_hours,
                "holdings_processed": holdings_processed,
                "total_holdings": total_holdings,
                "progress_pct": (holdings_processed / total_holdings * 100) if total_holdings > 0 else 0,
                "last_update": datetime.fromtimestamp(state_file.stat().st_mtime),
                "is_stale": age_hours > 24
            }
            
        except Exception as e:
            logger.error(f"Failed to extract metadata from {state_file}: {e}")
            return None
    
    def prompt_user_for_resume(self, states: list[dict]) -> Optional[str]:
        """
        Prompt user to select a state to resume or start fresh.
        
        Returns:
            UUID to resume, or None to start fresh
        """
        if not states:
            return None
        
        print("\n" + "="*70)
        print("🔄 FOUND EXISTING FLOW STATES")
        print("="*70)
        
        for idx, state in enumerate(states, 1):
            age_str = f"{state['age_hours']:.1f}h ago"
            progress_str = f"{state['holdings_processed']}/{state['total_holdings']} ({state['progress_pct']:.1f}%)"
            stale_marker = " ⚠️ STALE" if state['is_stale'] else ""
            
            print(f"\n{idx}. UUID: {state['uuid'][:8]}...{stale_marker}")
            print(f"   Age: {age_str}")
            print(f"   Progress: {progress_str}")
            print(f"   Last Update: {state['last_update'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"\n{len(states) + 1}. Start Fresh (new UUID)")
        print("="*70)
        
        while True:
            try:
                choice = input(f"\nSelect option (1-{len(states) + 1}): ").strip()
                choice_num = int(choice)
                
                if 1 <= choice_num <= len(states):
                    selected = states[choice_num - 1]
                    
                    # Warn if stale
                    if selected['is_stale']:
                        confirm = input(f"\n⚠️  State is {selected['age_hours']:.1f}h old (>24h). Resume anyway? (y/n): ").strip().lower()
                        if confirm != 'y':
                            continue
                    
                    print(f"\n✅ Resuming from UUID: {selected['uuid']}")
                    return selected['uuid']
                
                elif choice_num == len(states) + 1:
                    print("\n✅ Starting fresh with new UUID")
                    return None
                
                else:
                    print(f"❌ Invalid choice. Please enter 1-{len(states) + 1}")
                    
            except ValueError:
                print(f"❌ Invalid input. Please enter a number 1-{len(states) + 1}")
            except KeyboardInterrupt:
                print("\n\n❌ Cancelled by user")
                raise SystemExit(0)
    
    def load_flow_state_by_uuid(self, uuid: str) -> Optional[dict]:
        """Load flow state data by UUID."""
        state_file = self.state_dir / f"{uuid}.db"
        
        if not state_file.exists():
            logger.error(f"State file not found: {state_file}")
            return None
        
        try:
            import sqlite3
            conn = sqlite3.connect(str(state_file))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT state_data 
                FROM flow_state 
                ORDER BY created_at DESC 
                LIMIT 1
            """)
            
            row = cursor.fetchone()
            if not row:
                return None
            
            state_data = json.loads(row[0])
            conn.close()
            
            return state_data
            
        except Exception as e:
            logger.error(f"Failed to load state from {state_file}: {e}")
            return None
```

### CLI Integration

**Location:** `src/finwiz/cli/argument_parser.py` (MODIFY)

**Changes:** Add resume capability to CLI

```python
def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="FinWiz Financial Analysis")
    
    # NEW: Resume option
    parser.add_argument(
        "--resume-uuid",
        type=str,
        help="Resume from specific flow UUID (skips prompt)"
    )
    
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Force fresh start, ignore existing states"
    )
    
    return parser.parse_args()

def initialize_flow_with_resume() -> FinwizFlow:
    """Initialize flow with resume capability."""
    args = parse_arguments()
    state_manager = FlowStateManager()
    
    # Check for --no-resume flag
    if args.no_resume:
        logger.info("--no-resume flag set, starting fresh")
        return FinwizFlow()
    
    # Check for --resume-uuid argument
    if args.resume_uuid:
        logger.info(f"Attempting to resume UUID: {args.resume_uuid}")
        state_data = state_manager.load_flow_state_by_uuid(args.resume_uuid)
        
        if state_data:
            # Create flow and restore state
            flow = FinwizFlow()
            flow.state = FinwizState(**state_data)
            flow.state.resume_from_checkpoint = True
            logger.info("✅ Successfully loaded state from UUID")
            return flow
        else:
            logger.error(f"Failed to load UUID {args.resume_uuid}, starting fresh")
            return FinwizFlow()
    
    # Interactive mode: discover and prompt
    states = state_manager.discover_persisted_states()
    
    if not states:
        logger.info("No existing states found, starting fresh")
        return FinwizFlow()
    
    # Prompt user
    selected_uuid = state_manager.prompt_user_for_resume(states)
    
    if selected_uuid:
        # Load and resume
        state_data = state_manager.load_flow_state_by_uuid(selected_uuid)
        if state_data:
            flow = FinwizFlow()
            flow.state = FinwizState(**state_data)
            flow.state.resume_from_checkpoint = True
            return flow
        else:
            logger.error("Failed to load selected state, starting fresh")
            return FinwizFlow()
    else:
        # Start fresh
        return FinwizFlow()
```

### Flow Orchestrator Integration

**Location:** `src/finwiz/flows/flow_orchestrator.py` (MODIFY)

**Changes:** Check resume flag in conditional @start() methods

```python
@start("validate_data_integration")  # Conditional start
@listen("validate_data_integration")
async def check_portfolio(self) -> dict[str, Any]:
    """Check portfolio (can be resumed)."""
    
    # NEW: Check if resuming and already completed
    if self.state.resume_from_checkpoint and self.state.portfolio_review is not None:
        logger.info("🔄 RESUME: Portfolio already analyzed, skipping")
        logger.info(f"   Loaded {len(self.state.portfolio_review.get('holdings', []))} holdings from checkpoint")
        return {"status": "skipped", "reason": "resumed_from_checkpoint"}
    
    # Normal execution
    logger.info("Analyzing portfolio...")
    # ... existing logic ...
```

### State Cleanup

**Location:** `src/finwiz/utils/flow_state_manager.py` (ADD)

**Purpose:** Clean up old state files

```python
def cleanup_old_states(self, max_age_days: int = 7) -> int:
    """
    Clean up state files older than max_age_days.
    
    Returns:
        Number of files deleted
    """
    if not self.state_dir.exists():
        return 0
    
    cutoff = datetime.now() - timedelta(days=max_age_days)
    deleted = 0
    
    for state_file in self.state_dir.glob("*.db"):
        try:
            mtime = datetime.fromtimestamp(state_file.stat().st_mtime)
            if mtime < cutoff:
                state_file.unlink()
                deleted += 1
                logger.info(f"Deleted old state: {state_file.name}")
        except Exception as e:
            logger.warning(f"Failed to delete {state_file}: {e}")
    
    return deleted
```

### Configuration

**Add to ResilienceConfig:**

```python
@dataclass
class ResilienceConfig:
    # ... existing fields ...
    
    # State cleanup (NEW)
    cleanup_state_on_success: bool = os.getenv("FINWIZ_CLEANUP_STATE_ON_SUCCESS", "false").lower() == "true"
    state_cleanup_max_age_days: int = int(os.getenv("FINWIZ_STATE_CLEANUP_MAX_AGE_DAYS", "7"))
```

---

## Implementation Phases

### Phase 1: Core Resilience (Requirements 1-5)
1. Add resilience fields to FinwizState
2. Create ResilienceConfig
3. Implement retry_handler.py
4. Implement timeout_handler.py
5. Add @persist() to FinwizFlow
6. Implement conditional @start() for resume
7. Integrate retry logic in analyze_and_update_portfolio
8. Add timeout management
9. Implement progress tracking

### Phase 2: Configuration & Monitoring (Requirements 6-7, 10)
10. Add environment variable configuration
11. Enhance logging with progress updates
12. Integrate with AlertManager for critical failures
13. Export metrics to JSON

### Phase 3: Error Handling & Integration (Requirements 8-9)
14. Implement error classification
15. Create ValidationError from exceptions
16. Add remediation suggestions
17. Integrate with existing parallelization
18. Test with existing flow methods

---

## Success Criteria

- ✅ Flow automatically retries failed operations (max 3 attempts)
- ✅ Flow checkpoints progress after each method
- ✅ Flow can resume from last checkpoint
- ✅ Flow handles timeouts gracefully (5min per holding, 2hr global)
- ✅ Flow tracks progress in real-time
- ✅ Flow classifies errors and provides remediation
- ✅ Flow integrates with existing monitoring
- ✅ Flow maintains >80% success rate with resilience features
- ✅ Flow overhead < 100ms for successful executions

---

## References

- CrewAI Flow State Management Documentation
- CrewAI @persist() Decorator Documentation
- Tenacity Library Documentation
- Python asyncio Documentation
- FinWiz existing patterns: `flow_orchestrator.py`, `flow_state.py`

---

**Version**: 1.0  
**Created**: 2025-01-11  
**Purpose**: Technical design for flow resilience and recovery implementation
