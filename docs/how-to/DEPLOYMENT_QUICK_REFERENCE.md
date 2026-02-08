# Supabase Timeout Fix - Quick Reference Card

## 🚀 Quick Start

```bash
# 1. Validate deployment
python scripts/validate_supabase_deployment.py --validate-all

# 2. Test graceful degradation
python scripts/test_graceful_degradation.py

# 3. Validate success criteria
python scripts/validate_success_criteria.py

# 4. Monitor metrics (1 hour)
python scripts/monitor_supabase_metrics.py --duration 3600
```

## ⚙️ Environment Variables

```bash
# Required Configuration
SUPABASE_READ_TIMEOUT=10.0
SUPABASE_WRITE_TIMEOUT=15.0
SUPABASE_CONNECTIVITY_TEST_TIMEOUT=5.0
SUPABASE_MAX_RETRIES=1
SUPABASE_CIRCUIT_BREAKER_THRESHOLD=5
SUPABASE_CIRCUIT_BREAKER_TIMEOUT=60
CACHE_ENABLED=true
ANALYSIS_CACHE_TTL_HOURS=24
```

## ✅ Success Criteria

| Criterion | Target | Command |
|-----------|--------|---------|
| 0% Availability | Analysis completes | `validate_success_criteria.py` |
| Timeout Rate | < 10% | `monitor_supabase_metrics.py` |
| Circuit Breaker | Auto-recovery | `validate_success_criteria.py` |
| No Blocking | < 1s operations | `test_graceful_degradation.py` |
| Clear Logging | All status logged | Check logs |

## 📊 Key Metrics

```bash
# Check current metrics
grep "Supabase Metrics" logs/finwiz.log | tail -5

# Check cache status
grep "Cache Status" logs/finwiz.log | tail -5

# Check timeouts
grep "timed out" logs/finwiz.log | wc -l
```

## 🔧 Quick Fixes

### High Timeout Rate (>10%)

```bash
export SUPABASE_READ_TIMEOUT=15.0
export SUPABASE_WRITE_TIMEOUT=20.0
# Restart application
```

### Circuit Breaker Stuck Open

```bash
export SUPABASE_CIRCUIT_BREAKER_TIMEOUT=120
# Restart application
```

### Cache Not Initializing

```bash
export SUPABASE_CONNECTIVITY_TEST_TIMEOUT=10.0
# Verify credentials
echo $SUPABASE_URL
echo $SUPABASE_KEY | head -c 20
# Restart application
```

## 🚨 Rollback

### Disable Cache Only

```bash
export CACHE_ENABLED=false
# Restart application
```

### Disable Supabase Completely

```bash
export SUPABASE_ENABLED=false
# Restart application
```

### Restore Original Timeouts

```bash
export SUPABASE_READ_TIMEOUT=2.0
export SUPABASE_WRITE_TIMEOUT=5.0
export SUPABASE_MAX_RETRIES=3
# Restart application
```

## 📝 Log Patterns

### ✅ Success Patterns

```
✅ Supabase connectivity test passed
✅ Cache service initialized successfully
✅ Cache HIT for {ticker}
✅ Cached {ticker}
```

### ⚠️ Warning Patterns (Expected)

```
⚠️ Cache read timeout for {ticker} - proceeding with fresh analysis
⚠️ Cache write timeout for {ticker}
⚠️ Supabase connectivity test failed: {error}
⚠️ Caching disabled - analysis will proceed without cache
```

### 🚨 Error Patterns (Investigate)

```
Circuit breaker opened after N failures
Supabase operations suspended - caching disabled
Database operation timed out (repeated >10%)
```

## 📚 Documentation

- **Full Guide**: [SUPABASE_DEPLOYMENT_GUIDE.md](SUPABASE_DEPLOYMENT_GUIDE.md)
- **Validation**: DEPLOYMENT_VALIDATION (removed)
- **Summary**: SUPABASE_TIMEOUT_FIX_SUMMARY (removed)

## 🎯 Deployment Checklist

- [ ] Update environment variables
- [ ] Restart application
- [ ] Run Phase 1 validation
- [ ] Monitor for 24 hours
- [ ] Run Phase 2 validation
- [ ] Test graceful degradation
- [ ] Validate success criteria
- [ ] Set up monitoring alerts
- [ ] Document any issues

## 📞 Support

1. Check logs: `logs/finwiz.log`
2. Run validation scripts
3. Review troubleshooting guide
4. Contact development team

---

**Quick Reference Version**: 1.0
**Last Updated**: 2025-11-01
