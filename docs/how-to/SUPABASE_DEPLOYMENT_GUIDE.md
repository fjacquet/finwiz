# Supabase Timeout Fix - Deployment Guide

This guide provides step-by-step instructions for deploying the Supabase timeout fix to production.

## Overview

The Supabase timeout fix implements:
- Increased timeouts (10s read, 15s write)
- Connectivity testing at startup
- Graceful degradation when Supabase is unavailable
- Circuit breaker protection
- Comprehensive monitoring and metrics

## Prerequisites

- Access to production environment
- Ability to update environment variables
- Ability to restart the application
- Access to logs for monitoring

## Deployment Phases

### Phase 1: Increased Timeouts

**Objective**: Deploy increased timeout configuration and monitor timeout rates.

#### Steps

1. **Update Environment Variables**

   Add or update the following variables in your production `.env` file:

   ```bash
   # Timeout Configuration
   SUPABASE_READ_TIMEOUT=10.0
   SUPABASE_WRITE_TIMEOUT=15.0
   SUPABASE_MAX_RETRIES=1
   
   # Circuit Breaker Configuration
   SUPABASE_CIRCUIT_BREAKER_THRESHOLD=5
   SUPABASE_CIRCUIT_BREAKER_TIMEOUT=60
   ```

2. **Deploy Configuration**

   ```bash
   # Restart the application to pick up new configuration
   # Method depends on your deployment setup:
   
   # Docker:
   docker-compose restart finwiz
   
   # Systemd:
   sudo systemctl restart finwiz
   
   # Kubernetes:
   kubectl rollout restart deployment/finwiz
   ```

3. **Validate Configuration**

   Run the Phase 1 validation script:

   ```bash
   python scripts/validate_supabase_deployment.py --phase 1
   ```

   Expected output:
   ```
   ✅ PASS: Read Timeout Configuration - Read timeout is 10.0s (expected: >=10.0s)
   ✅ PASS: Write Timeout Configuration - Write timeout is 15.0s (expected: >=15.0s)
   ✅ PASS: Max Retries Configuration - Max retries is 1 (expected: 1)
   ✅ PASS: Circuit Breaker Threshold - Circuit breaker threshold is 5 (expected: >=5)
   ✅ PASS: Circuit Breaker Timeout - Circuit breaker timeout is 60s (expected: >=60s)
   ✅ PASS: Environment Variables - All timeout environment variables configured: True
   ```

4. **Monitor for 24 Hours**

   Monitor the following metrics:

   - **Timeout Rate**: Should be < 10%
   - **Success Rate**: Should improve from baseline
   - **Average Response Time**: Track for performance impact
   - **Circuit Breaker State**: Should remain CLOSED under normal conditions

   Check logs for timeout warnings:
   ```bash
   # Look for timeout warnings
   grep "Database operation timed out" logs/finwiz.log
   
   # Check success rate
   grep "Supabase Metrics" logs/finwiz.log | tail -20
   ```

5. **Success Criteria**

   Phase 1 is successful if:
   - ✅ All configuration checks pass
   - ✅ Timeout rate < 10%
   - ✅ No increase in error rates
   - ✅ Application remains stable

### Phase 2: Connectivity Test & Graceful Degradation

**Objective**: Deploy connectivity testing and graceful degradation features.

#### Steps

1. **Verify Phase 1 Success**

   Ensure Phase 1 has been running successfully for at least 24 hours before proceeding.

2. **Update Environment Variables**

   Add connectivity test configuration:

   ```bash
   # Connectivity Test Configuration
   SUPABASE_CONNECTIVITY_TEST_TIMEOUT=5.0
   CACHE_ENABLED=true
   ANALYSIS_CACHE_TTL_HOURS=24
   ```

3. **Deploy Updated Code**

   The connectivity test and graceful degradation features are already in the codebase.
   Simply restart the application:

   ```bash
   # Restart to enable new features
   # (Use same method as Phase 1)
   ```

4. **Validate Deployment**

   Run the Phase 2 validation script:

   ```bash
   python scripts/validate_supabase_deployment.py --phase 2
   ```

   Expected output:
   ```
   ✅ PASS: Connectivity Test Timeout - Connectivity test timeout is 5.0s (expected: 5.0s)
   ✅ PASS: Connectivity Test Execution - Test completed in 0.45s (timeout: 5.0s), result: True
   ✅ PASS: Cache Service Initialization - Cache service initialized: True
   ✅ PASS: Graceful Degradation - Analysis completed with cache disabled: True
   ✅ PASS: Availability Flag - Client has is_available flag: True, value: True
   ```

5. **Monitor Cache Status**

   Check logs for cache initialization:

   ```bash
   # Look for cache status messages
   grep "Cache Status" logs/finwiz.log
   grep "Supabase connectivity test" logs/finwiz.log
   ```

   Expected log messages:
   ```
   ✅ Supabase connectivity test passed (timeout: 5.0s)
   ✅ Cache service initialized successfully
   📊 Cache Status: ENABLED
   ```

6. **Test Graceful Degradation**

   Temporarily disable Supabase to verify graceful degradation:

   ```bash
   # Set SUPABASE_ENABLED=false in .env
   # Restart application
   # Verify analysis still completes
   # Check logs for: "Cache DISABLED - executing fresh analysis"
   # Re-enable Supabase
   ```

7. **Monitor Performance Impact**

   Track the following metrics:

   - **Cache Hit Rate**: Should improve over time
   - **Analysis Execution Time**: Compare with/without cache
   - **Startup Time**: Should complete within 5 seconds
   - **Error Rates**: Should not increase

8. **Success Criteria**

   Phase 2 is successful if:
   - ✅ Connectivity test passes at startup
   - ✅ Cache initializes successfully
   - ✅ Analysis completes with cache disabled
   - ✅ No blocking delays observed
   - ✅ Clear logging of cache status

### Phase 3: Success Criteria Validation

**Objective**: Validate all success criteria are met.

#### Steps

1. **Run Complete Validation**

   ```bash
   python scripts/validate_supabase_deployment.py --validate-all
   ```

2. **Verify Success Criteria**

   The validation script checks:

   - ✅ **0% Supabase Availability**: Analysis completes with Supabase disabled
   - ✅ **Timeout Rate < 10%**: When Supabase is available
   - ✅ **Circuit Breaker Recovery**: Automatically recovers from failures
   - ✅ **No Blocking Delays**: Operations complete quickly
   - ✅ **Clear Logging**: All status changes are logged

3. **Manual Testing**

   Perform manual tests:

   ```bash
   # Test 1: Normal operation
   python src/finwiz/main.py
   # Verify: Analysis completes, cache works
   
   # Test 2: Supabase unavailable
   # Temporarily set SUPABASE_ENABLED=false
   python src/finwiz/main.py
   # Verify: Analysis still completes, logs show cache disabled
   
   # Test 3: Slow network
   # Temporarily set SUPABASE_READ_TIMEOUT=2.0
   python src/finwiz/main.py
   # Verify: Timeouts logged, analysis continues
   ```

4. **Review Metrics**

   Check final health status:

   ```bash
   # Look for health status in logs
   grep "Supabase Health Status" logs/finwiz.log | tail -5
   grep "Cache Metrics" logs/finwiz.log | tail -5
   ```

5. **Success Criteria**

   Deployment is successful if:
   - ✅ All validation checks pass
   - ✅ Timeout rate < 10%
   - ✅ Analysis works with 0% Supabase availability
   - ✅ Circuit breaker recovers automatically
   - ✅ No blocking delays
   - ✅ Clear, actionable logging

## Monitoring

### Key Metrics to Track

1. **Supabase Metrics** (logged every 100 operations):
   ```
   Supabase Metrics: Available=True, Success Rate=95.2%, Avg Response Time=245.3ms, 
   Circuit Breaker=CLOSED, Total Ops=500, Successful=476, Failed=24, Timeouts=12
   ```

2. **Cache Metrics**:
   ```
   Cache Metrics: Hits=150, Misses=50, Hit Rate=75.0%, Total=200, TTL=24h
   ```

3. **Health Status** (at startup):
   ```
   📊 Supabase Health Status: Available=True, Circuit Breaker=CLOSED
   ```

### Log Patterns to Monitor

**Success Patterns**:
- `✅ Supabase connectivity test passed`
- `✅ Cache service initialized successfully`
- `✅ Cache HIT for {ticker}`
- `✅ Cached {ticker}`

**Warning Patterns** (expected, not errors):
- `⚠️ Cache read timeout for {ticker} - proceeding with fresh analysis`
- `⚠️ Cache write timeout for {ticker}`
- `⚠️ Supabase connectivity test failed: {error}`
- `⚠️ Caching disabled - analysis will proceed without cache`

**Error Patterns** (investigate):
- `Circuit breaker opened after N failures`
- `Supabase operations suspended - caching disabled`
- Repeated timeout warnings (>10% of operations)

### Alerting Recommendations

Set up alerts for:

1. **Critical**:
   - Circuit breaker open for > 5 minutes
   - Error rate > 50%
   - Application crashes

2. **Warning**:
   - Timeout rate > 10%
   - Success rate < 90%
   - Cache disabled at startup (if Supabase should be available)

3. **Info**:
   - Circuit breaker state changes
   - Cache hit rate < 50% (after warm-up period)

## Rollback Procedures

If issues are detected:

### Rollback Phase 2

1. Set `CACHE_ENABLED=false` in environment
2. Restart application
3. Analysis will continue without caching

### Rollback Phase 1

1. Restore original timeout values:
   ```bash
   SUPABASE_READ_TIMEOUT=2.0
   SUPABASE_WRITE_TIMEOUT=5.0
   SUPABASE_MAX_RETRIES=3
   ```
2. Restart application
3. Monitor for original timeout issues

### Complete Rollback

1. Set `SUPABASE_ENABLED=false`
2. Restart application
3. System will operate without Supabase entirely

## Troubleshooting

### Issue: High Timeout Rate (>10%)

**Symptoms**: Many timeout warnings in logs

**Diagnosis**:
```bash
grep "Database operation timed out" logs/finwiz.log | wc -l
```

**Solutions**:
1. Increase timeouts further:
   ```bash
   SUPABASE_READ_TIMEOUT=15.0
   SUPABASE_WRITE_TIMEOUT=20.0
   ```
2. Check Supabase service status
3. Verify network connectivity
4. Consider disabling cache if persistent

### Issue: Circuit Breaker Stuck Open

**Symptoms**: `Circuit breaker is open` messages, no operations succeeding

**Diagnosis**:
```bash
grep "Circuit breaker" logs/finwiz.log | tail -20
```

**Solutions**:
1. Check Supabase availability
2. Increase recovery timeout:
   ```bash
   SUPABASE_CIRCUIT_BREAKER_TIMEOUT=120
   ```
3. Restart application to reset circuit breaker
4. Temporarily disable Supabase if service is down

### Issue: Cache Not Initializing

**Symptoms**: `Cache service disabled` at startup

**Diagnosis**:
```bash
grep "Cache service" logs/finwiz.log
grep "connectivity test" logs/finwiz.log
```

**Solutions**:
1. Verify Supabase credentials:
   ```bash
   echo $SUPABASE_URL
   echo $SUPABASE_KEY | head -c 20
   ```
2. Check connectivity test timeout:
   ```bash
   SUPABASE_CONNECTIVITY_TEST_TIMEOUT=10.0
   ```
3. Verify `analysis_cache` table exists in Supabase
4. Check Supabase service status

### Issue: Slow Startup

**Symptoms**: Application takes >5 seconds to start

**Diagnosis**:
```bash
grep "connectivity test" logs/finwiz.log
```

**Solutions**:
1. Reduce connectivity test timeout:
   ```bash
   SUPABASE_CONNECTIVITY_TEST_TIMEOUT=3.0
   ```
2. Consider disabling connectivity test if not needed:
   ```bash
   CACHE_ENABLED=false
   ```

## Post-Deployment Checklist

After successful deployment:

- [ ] All validation checks pass
- [ ] Timeout rate < 10% for 24 hours
- [ ] Cache hit rate improving over time
- [ ] No increase in error rates
- [ ] Circuit breaker remains closed
- [ ] Graceful degradation tested and working
- [ ] Monitoring and alerting configured
- [ ] Team trained on new logging patterns
- [ ] Rollback procedures documented and tested
- [ ] Success criteria validated

## Support

For issues or questions:

1. Check logs: `logs/finwiz.log`
2. Run validation: `python scripts/validate_supabase_deployment.py --validate-all`
3. Review this guide's troubleshooting section
4. Contact the development team

## References

- Requirements: `.kiro/specs/supabase-timeout-fix/requirements.md`
- Design: `.kiro/specs/supabase-timeout-fix/design.md`
- Tasks: `.kiro/specs/supabase-timeout-fix/tasks.md`
- Validation Script: `scripts/validate_supabase_deployment.py`
