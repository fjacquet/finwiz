# Investment Discovery Deployment and Monitoring Guide

## Overview

This guide covers the deployment and monitoring infrastructure implemented for the Investment Discovery Crew in FinWiz. The system provides comprehensive monitoring, alerting, and deployment automation for production environments.

## Components Implemented

### 1. Monitoring System (`src/finwiz/monitoring/`)

#### Investment Discovery Monitor (`investment_discovery_monitor.py`)

- **Purpose**: Comprehensive monitoring for investment discovery operations
- **Features**:
  - Discovery performance metrics tracking
  - Quality metrics for A+ discoveries
  - Alert condition checking
  - Dashboard data generation
  - Historical data storage
  - Metrics export functionality

**Key Metrics Tracked**:

- Total discoveries performed
- A+ grade discoveries count
- Discovery success rate
- Average discovery time
- Grade distribution
- Asset type distribution
- Validation pass rates
- Grade retention rates

#### Alerting System (`alerting.py`)

- **Purpose**: Comprehensive alerting for production monitoring
- **Features**:
  - Multi-channel notifications (email, webhook)
  - Alert escalation procedures
  - Rate limiting to prevent spam
  - Alert resolution tracking
  - Configurable thresholds

**Alert Types**:

- Discovery rate alerts
- Error rate alerts
- Performance degradation
- Quality metric alerts
- System health alerts

### 2. Deployment Scripts (`scripts/`)

#### Investment Discovery Deployment (`deploy_investment_discovery.sh`)

- **Purpose**: Specialized deployment script for investment discovery system
- **Features**:
  - Pre-deployment validation
  - Investment discovery specific configuration
  - Monitoring service startup
  - Post-deployment verification
  - Dashboard creation
  - Environment-specific settings

**Deployment Environments**:

- **Production**: Conservative settings, full monitoring
- **Staging**: Balanced settings for testing
- **Development**: Relaxed settings for development

#### Rollback Script (`rollback_investment_discovery.sh`)

- **Purpose**: Safe rollback procedures for investment discovery
- **Features**:
  - Service shutdown procedures
  - Feature flag disabling
  - Data archiving before cleanup
  - Rollback validation
  - Notification system
  - Emergency rollback mode

### 3. API Monitoring Endpoints (`src/finwiz/api/monitoring.py`)

#### REST API Endpoints

- `GET /api/v1/monitoring/health` - System health status
- `GET /api/v1/monitoring/discovery/metrics` - Discovery metrics
- `GET /api/v1/monitoring/alerts` - Active alerts
- `GET /api/v1/monitoring/alerts/summary` - Alert summary
- `POST /api/v1/monitoring/alerts/{id}/resolve` - Resolve alerts
- `GET /api/v1/monitoring/dashboard` - Complete dashboard data
- `GET /api/v1/monitoring/metrics/export` - Export metrics
- `POST /api/v1/monitoring/discovery/test` - Test monitoring system

### 4. Testing Infrastructure

#### Unit Tests

- **Monitor Tests**: `tests/unit/test_investment_discovery_monitor.py`
- **Alerting Tests**: `tests/unit/test_monitoring_alerting.py`
- **Coverage**: Comprehensive test coverage for all monitoring components

## Deployment Process

### 1. Pre-Deployment Checklist

- [ ] Environment variables configured
- [ ] API keys available
- [ ] Investment Discovery Crew configuration validated
- [ ] Monitoring system tested
- [ ] Backup procedures verified

### 2. Deployment Steps

```bash
# Deploy Investment Discovery system
./scripts/deploy_investment_discovery.sh -e production

# Verify deployment
curl http://localhost:8000/api/v1/monitoring/health

# Check monitoring dashboard
open output/monitoring/dashboard.html
```

### 3. Post-Deployment Verification

- System health check passes
- Monitoring service running
- Dashboard accessible
- Alert system functional
- Discovery crew operational

## Monitoring Dashboard

### Features

- Real-time system health status
- Discovery performance metrics
- Active alerts display
- Historical trend visualization
- Auto-refresh capabilities

### Access

- **Local**: `output/monitoring/dashboard.html`
- **API**: `GET /api/v1/monitoring/dashboard`

## Alert Configuration

### Environment Variables

```bash
# Email Configuration
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=alerts@example.com
SMTP_PASSWORD=your_password

# Recipients
ALERT_EMAIL_RECIPIENTS=team@example.com,admin@example.com
ALERT_CRITICAL_RECIPIENTS=oncall@example.com

# Webhooks
ALERT_WEBHOOK_URLS=https://hooks.slack.com/your-webhook

# Feature Flags
ALERT_EMAIL_ENABLED=true
ALERT_WEBHOOK_ENABLED=true
ALERT_ESCALATION_ENABLED=true
```

### Alert Thresholds

- **Discovery Rate**: Minimum 5 discoveries per day
- **Error Rate**: Maximum 10% error rate
- **Success Rate**: Minimum 80% success rate
- **Discovery Time**: Maximum 10 minutes per discovery
- **Grade Retention**: Minimum 70% A+ grade retention

## Rollback Procedures

### Automatic Rollback Triggers

- Deployment validation failure
- Post-deployment verification failure
- Critical system errors during deployment

### Manual Rollback

```bash
# Interactive rollback
./scripts/rollback_investment_discovery.sh

# Emergency rollback
./scripts/rollback_investment_discovery.sh -e

# Rollback with reason
./scripts/rollback_investment_discovery.sh -r "Performance issues"
```

### Rollback Process

1. Stop investment discovery services
2. Disable feature flags
3. Archive monitoring data
4. Clean up discovery output
5. Validate rollback completion
6. Send notifications
7. Generate rollback report

## Performance Monitoring

### Key Performance Indicators (KPIs)

- **Discovery Rate**: Number of discoveries per hour/day
- **A+ Discovery Rate**: Percentage of A+ discoveries
- **System Uptime**: Percentage of time system is operational
- **Response Time**: Average API response time
- **Error Rate**: Percentage of failed operations

### Performance Thresholds

- Discovery completion: < 10 minutes
- API response time: < 2 seconds
- System uptime: > 99.5%
- Error rate: < 5%

## Troubleshooting

### Common Issues

#### High Error Rate

1. Check API key validity
2. Verify data source availability
3. Review discovery criteria settings
4. Check system resource usage

#### Slow Discovery Performance

1. Monitor system resources (CPU, memory)
2. Check network connectivity
3. Review discovery criteria complexity
4. Consider scaling resources

#### Monitoring Service Down

1. Check service logs: `logs/discovery_monitor.log`
2. Verify configuration settings
3. Restart monitoring service
4. Check system dependencies

### Log Files

- **Deployment**: `logs/investment_discovery_deployment.log`
- **Monitoring**: `logs/discovery_monitor.log`
- **Rollback**: `logs/investment_discovery_rollback.log`
- **Application**: `logs/finwiz.log`

## Security Considerations

### Data Protection

- All sensitive data encrypted at rest
- API keys stored securely in environment variables
- Monitoring data access controlled
- Audit trails maintained

### Network Security

- HTTPS enforced for all API endpoints
- Webhook URLs validated
- Rate limiting implemented
- Input validation on all endpoints

## Maintenance

### Regular Tasks

- **Daily**: Review monitoring dashboard
- **Weekly**: Check alert history and trends
- **Monthly**: Review performance metrics
- **Quarterly**: Update alert thresholds based on trends

### Backup Procedures

- Monitoring data backed up daily
- Configuration files versioned
- Deployment artifacts archived
- Recovery procedures tested monthly

## Support and Escalation

### Alert Escalation Path

1. **Level 1**: Development team notification
2. **Level 2**: Senior developer escalation (30 minutes)
3. **Level 3**: Management notification (1 hour)

### Contact Information

- **Development Team**: <team@example.com>
- **On-Call Engineer**: <oncall@example.com>
- **Management**: <management@example.com>

## Future Enhancements

### Planned Features

- Advanced analytics dashboard
- Machine learning-based anomaly detection
- Integration with external monitoring tools
- Automated scaling based on load
- Enhanced reporting capabilities

### Monitoring Improvements

- Custom metric definitions
- Advanced alerting rules
- Integration with APM tools
- Real-time performance analytics
- Predictive failure detection

---

This deployment and monitoring system provides a robust foundation for running the Investment Discovery Crew in production environments with comprehensive observability and automated recovery procedures.
