# Supabase Timeout Fix Spec

## Problem Statement

Supabase integration is experiencing 100% timeout failures on all database operations (2-5 second timeouts), causing:
- Circuit breaker to open after 3 consecutive failures
- All 74 holdings failing cache checks
- Warnings flooding the logs
- No actual caching functionality

## Root Cause

1. **Aggressive Timeouts**: 2-5 second timeouts are too short for network database operations
2. **No Connectivity Validation**: System assumes Supabase is available without testing
3. **Blocking Behavior**: Failed cache operations delay the analysis workflow
4. **No Graceful Degradation**: System doesn't handle unavailable cache gracefully

## Solution Overview

Implement graceful degradation with:
1. **Connectivity Test at Startup** - Test Supabase early (5s timeout) and disable caching if it fails
2. **Increased Timeouts** - 10s for reads, 15s for writes (up from 2s/5s)
3. **Non-Blocking Cache** - Fire-and-forget cache writes that don't delay analysis
4. **Enhanced Circuit Breaker** - Automatic recovery with half-open state
5. **Clear Logging** - Visibility into cache status and issues

## Key Benefits

✅ **System works with 0% Supabase availability** - Analysis completes normally
✅ **No blocking delays** - Cache operations don't slow down analysis
✅ **Automatic recovery** - Circuit breaker recovers when Supabase comes back
✅ **Clear visibility** - Logs show exactly what's happening with cache
✅ **Configurable** - Tune timeouts via environment variables

## Implementation Strategy

### Phase 1: Increase Timeouts (Immediate - Tasks 1.x)
- Update default timeouts to 10s/15s
- Add environment variable configuration
- Reduce retry attempts to 1
- **Expected Impact**: Reduce timeout rate from 100% to <10%

### Phase 2: Add Connectivity Test (Next - Tasks 2.x, 3.x, 4.x)
- Test Supabase at startup
- Disable caching if test fails
- Make cache operations non-blocking
- **Expected Impact**: System works normally with cache disabled

### Phase 3: Enhanced Monitoring (Final - Tasks 5.x, 6.x)
- Add circuit breaker recovery
- Track metrics and health status
- Improve logging
- **Expected Impact**: Better visibility and automatic recovery

## Files to Modify

1. `src/finwiz/supabase/client.py` - Timeout configuration, connectivity test
2. `src/finwiz/supabase/services/cache_service.py` - Graceful degradation
3. `src/finwiz/flows/flow_orchestrator.py` - Cache initialization
4. `src/finwiz/supabase/repositories/*.py` - Update timeout calls
5. `src/finwiz/supabase/circuit_breaker.py` - Enhanced recovery
6. `.env.example` - New configuration variables
7. `README.md` - Configuration documentation

## Configuration

### New Environment Variables

```bash
# Timeout Configuration (seconds)
SUPABASE_READ_TIMEOUT=10.0          # Up from 2.0
SUPABASE_WRITE_TIMEOUT=15.0         # Up from 5.0
SUPABASE_CONNECTIVITY_TEST_TIMEOUT=5.0
SUPABASE_MAX_RETRIES=1              # Down from 3

# Circuit Breaker Configuration
SUPABASE_CIRCUIT_BREAKER_THRESHOLD=5
SUPABASE_CIRCUIT_BREAKER_TIMEOUT=60

# Cache Configuration
CACHE_ENABLED=true                  # Set to false to disable entirely
ANALYSIS_CACHE_TTL_HOURS=24
```

## Success Criteria

1. ✅ System completes analysis with 0% Supabase availability
2. ✅ Timeout rate < 10% when Supabase is available
3. ✅ Circuit breaker recovers automatically
4. ✅ No blocking delays in analysis workflow
5. ✅ Clear logging of cache status and issues

## Testing Strategy

### Manual Testing
1. Test with Supabase unavailable (disconnect network)
2. Test with Supabase slow (add network delay)
3. Test with Supabase recovering (reconnect after failure)
4. Verify analysis completes in all cases

### Automated Testing (Optional)
- Unit tests for connectivity test
- Unit tests for graceful degradation
- Unit tests for circuit breaker recovery
- Integration tests for end-to-end scenarios

## Deployment Plan

1. **Deploy Phase 1** - Increase timeouts, monitor for 24 hours
2. **Deploy Phase 2** - Add connectivity test and graceful degradation
3. **Deploy Phase 3** - Enhanced monitoring and metrics
4. **Validate** - Verify all success criteria met

## Next Steps

To begin implementation:
1. Open `.kiro/specs/supabase-timeout-fix/tasks.md`
2. Click "Start task" next to task 1.1
3. Follow the implementation plan sequentially

## Related Documentation

- Requirements: `requirements.md`
- Design: `design.md`
- Tasks: `tasks.md`
- Deployment Checklist: `../../db/DEPLOYMENT_CHECKLIST.md`
- Troubleshooting: `../../db/TROUBLESHOOTING.md`
