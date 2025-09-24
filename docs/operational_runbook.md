# FinWiz Operational Runbook

This runbook provides step-by-step procedures for common operational tasks, incident response, and maintenance activities for FinWiz in production environments.

## Table of Contents

- [Daily Operations](#daily-operations)
- [Incident Response](#incident-response)
- [Maintenance Procedures](#maintenance-procedures)
- [Performance Monitoring](#performance-monitoring)
- [Feature Flag Management](#feature-flag-management)
- [Backup and Recovery](#backup-and-recovery)
- [Security Operations](#security-operations)

## Daily Operations

### Morning Health Check

**Frequency**: Daily at start of business hours  
**Duration**: 5-10 minutes  
**Responsibility**: Operations team

#### Checklist

1. **System Health Status**
   ```bash
   # Check application health
   curl -f http://localhost:8000/health || echo "❌ Health check failed"
   
   # Check feature status
   curl -f http://localhost:8000/api/v1/rebalancing/status || echo "ℹ️ API not enabled"
   ```

2. **Log Review**
   ```bash
   # Check for errors in the last 24 hours
   tail -n 100 logs/finwiz_error.log
   
   # Check application logs for warnings
   grep -i "warning\|error" logs/finwiz.log | tail -n 20
   ```

3. **Performance Metrics**
   ```python
   # Run this in Python console
   from finwiz.utils.monitoring import get_metrics_collector
   metrics = get_metrics_collector()
   health = metrics.get_health_status()
   print(f"System Status: {health['status']}")
   print(f"Error Rate: {health['error_rate']:.2%}")
   ```

4. **Feature Flag Status**
   ```python
   from finwiz.utils.feature_flags import get_feature_flags
   flags = get_feature_flags()
   enabled = flags.get_enabled_flags()
   print(f"Enabled Features: {len(enabled)}")
   ```

#### Expected Results

- Health check returns `{"status": "healthy"}`
- No critical errors in logs
- System status is "healthy" or "degraded" (not "unhealthy")
- Error rate < 5%

#### Escalation

If any checks fail:
1. Document the issue
2. Check incident response procedures
3. Notify development team if critical

### Weekly Maintenance

**Frequency**: Weekly (Sunday 2 AM UTC)  
**Duration**: 30-60 minutes  
**Responsibility**: Operations team

#### Tasks

1. **Log Rotation and Cleanup**
   ```bash
   # Archive old logs
   find logs/ -name "*.log.*" -mtime +30 -delete
   
   # Compress current logs if large
   find logs/ -name "*.log" -size +100M -exec gzip {} \;
   ```

2. **Backup Cleanup**
   ```bash
   # Clean old backups (keep last 10)
   ./scripts/deploy.sh --cleanup-backups
   ```

3. **Dependency Updates**
   ```bash
   # Check for security updates
   uv sync --upgrade
   
   # Run tests after updates
   uv run pytest tests/unit/ -x
   ```

4. **Performance Review**
   - Review weekly performance metrics
   - Check for performance degradation trends
   - Update monitoring thresholds if needed

## Incident Response

### Severity Levels

#### Critical (P0)
- Complete system failure
- Data corruption or loss
- Security breach
- **Response Time**: Immediate (< 15 minutes)

#### High (P1)
- Major feature failure
- Performance degradation > 50%
- API errors > 10%
- **Response Time**: < 1 hour

#### Medium (P2)
- Minor feature issues
- Performance degradation < 50%
- Non-critical errors
- **Response Time**: < 4 hours

#### Low (P3)
- Enhancement requests
- Minor bugs
- Documentation issues
- **Response Time**: < 24 hours

### Incident Response Procedures

#### Step 1: Initial Assessment (5 minutes)

1. **Confirm the incident**
   ```bash
   # Quick health check
   curl -f http://localhost:8000/health
   
   # Check system resources
   top -n 1
   df -h
   ```

2. **Determine severity level**
   - Is the system completely down? → P0
   - Are critical features failing? → P1
   - Are there performance issues? → P2
   - Minor issues only? → P3

3. **Create incident record**
   - Document time, symptoms, and initial assessment
   - Assign incident ID: `INC-YYYYMMDD-NNN`

#### Step 2: Immediate Response (P0/P1 only)

1. **For Complete System Failure (P0)**
   ```bash
   # Emergency rollback
   ./scripts/rollback.sh --emergency
   
   # Verify recovery
   curl -f http://localhost:8000/health
   ```

2. **For Feature Failures (P1)**
   ```bash
   # Disable failing feature
   export FF_FAILING_FEATURE=false
   
   # Restart application
   pkill -f finwiz
   uv run python src/finwiz/main.py &
   ```

#### Step 3: Investigation and Diagnosis

1. **Collect diagnostic information**
   ```bash
   # System information
   uname -a
   free -h
   df -h
   
   # Application logs
   tail -n 500 logs/finwiz.log > incident_logs_$(date +%Y%m%d_%H%M%S).txt
   tail -n 100 logs/finwiz_error.log >> incident_logs_$(date +%Y%m%d_%H%M%S).txt
   
   # Performance metrics
   python -c "
   from finwiz.utils.monitoring import get_metrics_collector
   import json
   metrics = get_metrics_collector()
   with open('incident_metrics_$(date +%Y%m%d_%H%M%S).json', 'w') as f:
       json.dump(metrics.get_performance_summary(), f, indent=2)
   "
   ```

2. **Analyze root cause**
   - Check for recent changes or deployments
   - Review error patterns in logs
   - Check external API status
   - Verify configuration changes

#### Step 4: Resolution and Recovery

1. **Implement fix**
   - Apply hotfix if available
   - Adjust configuration if needed
   - Restart services if required

2. **Verify resolution**
   ```bash
   # Run health checks
   curl -f http://localhost:8000/health
   
   # Test affected functionality
   uv run pytest tests/integration/ -k "test_affected_feature"
   
   # Monitor for 15 minutes
   watch -n 30 'curl -s http://localhost:8000/health | jq .status'
   ```

#### Step 5: Post-Incident Activities

1. **Document resolution**
   - Update incident record with resolution steps
   - Note any temporary workarounds
   - Schedule permanent fix if needed

2. **Post-mortem (P0/P1 incidents)**
   - Schedule post-mortem meeting within 24 hours
   - Document timeline, root cause, and lessons learned
   - Create action items for prevention

## Maintenance Procedures

### Planned Maintenance Window

**Frequency**: Monthly (first Sunday of month, 2-4 AM UTC)  
**Duration**: 2 hours  
**Responsibility**: Operations and development teams

#### Pre-Maintenance Checklist

1. **Notify stakeholders** (48 hours before)
2. **Create maintenance backup**
   ```bash
   ./scripts/deploy.sh --create-backup
   ```
3. **Prepare rollback plan**
4. **Test procedures in staging**

#### Maintenance Tasks

1. **System Updates**
   ```bash
   # Update system packages
   sudo apt update && sudo apt upgrade -y
   
   # Update Python dependencies
   uv sync --upgrade
   
   # Update FinWiz application
   git pull origin main
   ./scripts/deploy.sh --env production
   ```

2. **Database Maintenance** (if applicable)
   ```bash
   # Optimize database
   # Backup database
   # Update schemas if needed
   ```

3. **Configuration Updates**
   - Review and update feature flags
   - Update monitoring thresholds
   - Rotate API keys if scheduled

#### Post-Maintenance Verification

1. **Functional Testing**
   ```bash
   # Run full test suite
   uv run pytest tests/ -v
   
   # Test critical user journeys
   # Verify all features are working
   ```

2. **Performance Validation**
   - Check response times
   - Verify error rates are normal
   - Monitor for 1 hour after maintenance

### Emergency Maintenance

For urgent security updates or critical fixes:

1. **Assess urgency and impact**
2. **Create emergency backup**
   ```bash
   ./scripts/deploy.sh --create-backup --emergency
   ```
3. **Apply fix with minimal downtime**
4. **Verify fix immediately**
5. **Document emergency change**

## Performance Monitoring

### Key Performance Indicators (KPIs)

#### System Health KPIs

- **Uptime**: Target > 99.9%
- **Response Time**: Target < 2 seconds (95th percentile)
- **Error Rate**: Target < 1%
- **Memory Usage**: Target < 80%
- **CPU Usage**: Target < 70%

#### Application KPIs

- **Analysis Completion Rate**: Target > 95%
- **API Success Rate**: Target > 99%
- **Feature Flag Success Rate**: Target > 99.5%
- **Cache Hit Rate**: Target > 80%

### Monitoring Procedures

#### Real-time Monitoring

```bash
# System resources
watch -n 5 'free -h && echo "---" && df -h'

# Application health
watch -n 30 'curl -s http://localhost:8000/health | jq'

# Log monitoring
tail -f logs/finwiz.log | grep -E "(ERROR|WARNING|CRITICAL)"
```

#### Performance Analysis

```python
# Weekly performance report
from finwiz.utils.monitoring import get_metrics_collector
import json
from datetime import datetime, timedelta

metrics = get_metrics_collector()
summary = metrics.get_performance_summary()

# Generate report
report = {
    "timestamp": datetime.now().isoformat(),
    "period": "weekly",
    "summary": summary,
    "health": metrics.get_health_status()
}

with open(f"performance_report_{datetime.now().strftime('%Y%m%d')}.json", "w") as f:
    json.dump(report, f, indent=2)
```

### Performance Alerts

#### Alert Thresholds

- **Error Rate > 5%**: Warning alert
- **Error Rate > 10%**: Critical alert
- **Response Time > 5s**: Warning alert
- **Response Time > 10s**: Critical alert
- **Memory Usage > 90%**: Critical alert
- **Disk Usage > 85%**: Warning alert

#### Alert Response

1. **Warning Alerts**
   - Investigate within 30 minutes
   - Document findings
   - Take corrective action if needed

2. **Critical Alerts**
   - Investigate immediately
   - Follow incident response procedures
   - Escalate if not resolved within 15 minutes

## Feature Flag Management

### Feature Flag Lifecycle

#### 1. Development Phase
- Feature flag created with `enabled=false`
- Tested in development environment
- Code review includes feature flag usage

#### 2. Staging Phase
- Enable feature flag in staging
- Gradual rollout testing (0% → 25% → 50% → 100%)
- Performance and stability validation

#### 3. Production Rollout
- Start with 0% rollout in production
- Gradual increase: 1% → 5% → 25% → 50% → 100%
- Monitor metrics at each stage

#### 4. Stabilization
- Feature flag remains for 2-4 weeks after 100% rollout
- Monitor for any issues
- Prepare for flag removal

#### 5. Cleanup
- Remove feature flag code
- Update documentation
- Clean up configuration

### Feature Flag Operations

#### Enable Feature for Testing

```python
from finwiz.utils.feature_flags import get_feature_flags

flags = get_feature_flags()
flags.update_flag("portfolio_rebalancing", enabled=True, rollout_percentage=10.0)
```

#### Emergency Feature Disable

```bash
# Set environment variable
export FF_PORTFOLIO_REBALANCING=false

# Restart application
pkill -f finwiz
uv run python src/finwiz/main.py &
```

#### Monitor Feature Usage

```python
from finwiz.utils.monitoring import get_metrics_collector

metrics = get_metrics_collector()
rebalancing_metrics = metrics.get_recent_metrics("portfolio_rebalancing.calls", minutes=60)
print(f"Rebalancing calls in last hour: {len(rebalancing_metrics)}")
```

## Backup and Recovery

### Backup Schedule

#### Automated Backups

- **Pre-deployment**: Before each deployment
- **Daily**: 2 AM UTC (application data)
- **Weekly**: Sunday 1 AM UTC (full system backup)

#### Manual Backups

```bash
# Create immediate backup
./scripts/deploy.sh --create-backup

# Create backup with custom name
tar -czf "backups/manual_backup_$(date +%Y%m%d_%H%M%S).tar.gz" \
    --exclude='.git' --exclude='__pycache__' .
```

### Recovery Procedures

#### Quick Recovery (< 5 minutes downtime)

```bash
# Use latest backup
./scripts/rollback.sh --emergency
```

#### Selective Recovery (specific files)

```bash
# Extract specific files from backup
tar -xzf backups/latest_backup.tar.gz path/to/specific/file
```

#### Full System Recovery

1. **Stop all services**
2. **Restore from backup**
3. **Verify configuration**
4. **Restart services**
5. **Validate functionality**

### Backup Validation

#### Weekly Backup Testing

```bash
# Test backup integrity
tar -tzf backups/latest_backup.tar.gz >/dev/null && echo "✅ Backup valid" || echo "❌ Backup corrupted"

# Test restore procedure (in test environment)
./scripts/rollback.sh --backup backups/latest_backup.tar.gz --skip-verification
```

## Security Operations

### Security Monitoring

#### Daily Security Checks

1. **Check for unauthorized access attempts**
   ```bash
   grep -i "unauthorized\|forbidden\|denied" logs/finwiz.log
   ```

2. **Monitor API key usage**
   ```bash
   grep -i "api.*key" logs/finwiz.log | grep -v "configured"
   ```

3. **Check for suspicious patterns**
   ```bash
   grep -E "(failed|error|exception)" logs/finwiz.log | tail -n 20
   ```

#### Security Incident Response

1. **Immediate Actions**
   - Isolate affected systems
   - Preserve evidence
   - Notify security team

2. **Investigation**
   - Analyze logs for attack patterns
   - Check for data access or modification
   - Identify attack vectors

3. **Recovery**
   - Patch vulnerabilities
   - Rotate compromised credentials
   - Update security measures

### API Key Management

#### Key Rotation Schedule

- **Production**: Quarterly
- **Staging**: Semi-annually
- **Development**: Annually

#### Key Rotation Procedure

1. **Generate new API keys**
2. **Update configuration in staging**
3. **Test functionality**
4. **Update production configuration**
5. **Verify operation**
6. **Revoke old keys**

### Security Updates

#### Monthly Security Review

1. **Check for dependency vulnerabilities**
   ```bash
   uv audit
   ```

2. **Review access logs**
3. **Update security configurations**
4. **Test security measures**

#### Emergency Security Updates

1. **Assess vulnerability impact**
2. **Apply security patches immediately**
3. **Test critical functionality**
4. **Monitor for issues**
5. **Document changes**

## Contact Information

### Escalation Matrix

#### Level 1: Operations Team
- **Response Time**: 15 minutes
- **Availability**: 24/7
- **Contact**: ops-team@company.com

#### Level 2: Development Team
- **Response Time**: 1 hour
- **Availability**: Business hours + on-call
- **Contact**: dev-team@company.com

#### Level 3: Architecture Team
- **Response Time**: 4 hours
- **Availability**: Business hours
- **Contact**: architecture@company.com

### Emergency Contacts

- **Critical Issues**: +1-XXX-XXX-XXXX
- **Security Issues**: security@company.com
- **Management Escalation**: management@company.com