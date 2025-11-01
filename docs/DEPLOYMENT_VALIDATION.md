# Deployment Validation

Quick reference for validating Supabase timeout fix deployment.

## Quick Validation

Run the complete validation suite:

```bash
python scripts/validate_supabase_deployment.py --validate-all
```

## Phase-Specific Validation

### Phase 1: Timeout Configuration

```bash
python scripts/validate_supabase_deployment.py --phase 1
```

Validates:
- Read timeout ≥ 10.0s
- Write timeout ≥ 15.0s
- Max retries = 1
- Circuit breaker threshold ≥ 5
- Circuit breaker timeout ≥ 60s

### Phase 2: Graceful Degradation

```bash
python scripts/validate_supabase_deployment.py --phase 2
```

Validates:
- Connectivity test completes within 5s
- Cache service initializes
- Analysis works with cache disabled
- Availability flag set correctly

## Success Criteria Validation

```bash
python scripts/validate_success_criteria.py
```

Validates all 5 success criteria:
1. ✅ Analysis with 0% Supabase availability
2. ✅ Timeout rate < 10%
3. ✅ Circuit breaker recovery
4. ✅ No blocking delays
5. ✅ Clear logging

## Graceful Degradation Testing

```bash
python scripts/test_graceful_degradation.py
```

Tests:
- Supabase enabled (normal operation)
- Supabase disabled (graceful degradation)
- Cache disabled flag
- Connectivity test timeout
- Non-blocking cache writes
- Circuit breaker state

## Metrics Monitoring

Monitor metrics in real-time:

```bash
# Monitor for 1 hour
python scripts/monitor_supabase_metrics.py --duration 3600

# Monitor continuously
python scripts/monitor_supabase_metrics.py --continuous

# Generate report from logs
python scripts/monitor_supabase_metrics.py --report logs/finwiz.log
```

## Expected Results

### Successful Deployment

All validation scripts should show:

```
✅ PASS: Read Timeout Configuration
✅ PASS: Write Timeout Configuration
✅ PASS: Connectivity Test Execution
✅ PASS: Graceful Degradation
✅ PASS: Analysis with 0% Supabase Availability
✅ PASS: Timeout Rate < 10%
✅ PASS: Circuit Breaker Recovery
✅ PASS: No Blocking Delays
✅ PASS: Clear Logging

✅ ALL SUCCESS CRITERIA MET
```

### Key Metrics

Monitor these metrics:
- **Timeout Rate**: < 10%
- **Success Rate**: > 90%
- **Avg Response Time**: < 500ms
- **Circuit Breaker**: CLOSED
- **Cache Hit Rate**: Improving over time

## Troubleshooting

If validation fails, see:
- [Deployment Guide](SUPABASE_DEPLOYMENT_GUIDE.md) - Complete deployment procedures
- [Troubleshooting Section](SUPABASE_DEPLOYMENT_GUIDE.md#troubleshooting) - Common issues and solutions

## Quick Fixes

### High Timeout Rate

```bash
# Increase timeouts
export SUPABASE_READ_TIMEOUT=15.0
export SUPABASE_WRITE_TIMEOUT=20.0
```

### Circuit Breaker Stuck Open

```bash
# Increase recovery timeout
export SUPABASE_CIRCUIT_BREAKER_TIMEOUT=120
# Restart application
```

### Cache Not Initializing

```bash
# Increase connectivity test timeout
export SUPABASE_CONNECTIVITY_TEST_TIMEOUT=10.0
# Verify credentials
echo $SUPABASE_URL
echo $SUPABASE_KEY | head -c 20
```

## Documentation

- **Full Guide**: [docs/SUPABASE_DEPLOYMENT_GUIDE.md](SUPABASE_DEPLOYMENT_GUIDE.md)
- **Requirements**: [.kiro/specs/supabase-timeout-fix/requirements.md](../.kiro/specs/supabase-timeout-fix/requirements.md)
- **Design**: [.kiro/specs/supabase-timeout-fix/design.md](../.kiro/specs/supabase-timeout-fix/design.md)
- **Tasks**: [.kiro/specs/supabase-timeout-fix/tasks.md](../.kiro/specs/supabase-timeout-fix/tasks.md)
