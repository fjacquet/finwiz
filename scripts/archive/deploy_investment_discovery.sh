#!/bin/bash

# Investment Discovery Crew Deployment Script
# Specialized deployment script for the Investment Discovery Crew with monitoring

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOYMENT_ENV="${DEPLOYMENT_ENV:-production}"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups}"
LOG_FILE="${LOG_FILE:-$PROJECT_ROOT/logs/investment_discovery_deployment.log}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
}

log_info() {
    log "INFO" "${BLUE}$*${NC}"
}

log_warn() {
    log "WARN" "${YELLOW}$*${NC}"
}

log_error() {
    log "ERROR" "${RED}$*${NC}"
}

log_success() {
    log "SUCCESS" "${GREEN}$*${NC}"
}

# Error handler
error_handler() {
    local line_number=$1
    log_error "Investment Discovery deployment failed at line $line_number"
    log_error "Rolling back changes..."
    rollback_investment_discovery
    exit 1
}

trap 'error_handler $LINENO' ERR

# Rollback function
rollback_investment_discovery() {
    log_warn "Initiating Investment Discovery rollback procedure..."
    
    # Stop monitoring services
    stop_monitoring_services
    
    # Disable investment discovery feature flag
    export FF_INVESTMENT_DISCOVERY="false"
    
    # Run general rollback
    if [[ -f "$SCRIPT_DIR/rollback.sh" ]]; then
        "$SCRIPT_DIR/rollback.sh" --skip-verification
    fi
    
    log_success "Investment Discovery rollback completed"
}

# Stop monitoring services
stop_monitoring_services() {
    log_info "Stopping Investment Discovery monitoring services..."
    
    # Stop monitoring processes
    local monitor_pids=$(pgrep -f "investment_discovery_monitor" || true)
    if [[ -n "$monitor_pids" ]]; then
        log_info "Stopping monitoring processes: $monitor_pids"
        echo "$monitor_pids" | xargs -r kill -TERM
        sleep 3
        
        # Force kill if still running
        local remaining_pids=$(pgrep -f "investment_discovery_monitor" || true)
        if [[ -n "$remaining_pids" ]]; then
            log_warn "Force killing monitoring processes: $remaining_pids"
            echo "$remaining_pids" | xargs -r kill -KILL
        fi
    fi
    
    log_success "Monitoring services stopped"
}

# Pre-deployment checks for Investment Discovery
pre_deployment_checks() {
    log_info "Running Investment Discovery pre-deployment checks..."
    
    # Check if base deployment script exists
    if [[ ! -f "$SCRIPT_DIR/deploy.sh" ]]; then
        log_error "Base deployment script not found: $SCRIPT_DIR/deploy.sh"
        exit 1
    fi
    
    # Check Investment Discovery specific requirements
    cd "$PROJECT_ROOT"
    
    # Validate Investment Discovery Crew configuration
    if ! uv run python -c "
import sys
sys.path.insert(0, 'src')
from finwiz.crews.investment_discovery_crew.investment_discovery_crew import InvestmentDiscoveryCrew
try:
    crew_instance = InvestmentDiscoveryCrew()
    print('✅ Investment Discovery Crew configuration valid')
except Exception as e:
    print(f'❌ Investment Discovery Crew configuration invalid: {e}')
    sys.exit(1)
"; then
        log_error "Investment Discovery Crew configuration validation failed"
        exit 1
    fi
    
    # Check monitoring system
    if ! uv run python -c "
import sys
sys.path.insert(0, 'src')
from finwiz.monitoring.investment_discovery_monitor import get_discovery_monitor
try:
    monitor = get_discovery_monitor()
    print('✅ Investment Discovery monitoring system ready')
except Exception as e:
    print(f'❌ Investment Discovery monitoring system failed: {e}')
    sys.exit(1)
"; then
        log_error "Investment Discovery monitoring system validation failed"
        exit 1
    fi
    
    # Check required directories
    mkdir -p "$PROJECT_ROOT/output/discovery" "$PROJECT_ROOT/output/monitoring"
    
    log_success "Investment Discovery pre-deployment checks passed"
}

# Deploy Investment Discovery specific components
deploy_investment_discovery() {
    log_info "Deploying Investment Discovery components..."
    
    cd "$PROJECT_ROOT"
    
    # Set Investment Discovery specific environment variables
    export FF_INVESTMENT_DISCOVERY="true"
    export FF_INVESTMENT_DISCOVERY_MONITORING="true"
    export FINWIZ_DISCOVERY_OUTPUT_DIR="output/discovery"
    export FINWIZ_MONITORING_OUTPUT_DIR="output/monitoring"
    
    # Configure discovery parameters based on environment
    case "$DEPLOYMENT_ENV" in
        "production")
            export DISCOVERY_MAX_CANDIDATES="50"
            export DISCOVERY_TIMEOUT="600"  # 10 minutes
            export DISCOVERY_RETRY_ATTEMPTS="3"
            export MONITORING_ALERT_THRESHOLD="0.1"  # 10% error rate
            ;;
        "staging")
            export DISCOVERY_MAX_CANDIDATES="20"
            export DISCOVERY_TIMEOUT="300"  # 5 minutes
            export DISCOVERY_RETRY_ATTEMPTS="2"
            export MONITORING_ALERT_THRESHOLD="0.2"  # 20% error rate
            ;;
        "development")
            export DISCOVERY_MAX_CANDIDATES="10"
            export DISCOVERY_TIMEOUT="120"  # 2 minutes
            export DISCOVERY_RETRY_ATTEMPTS="1"
            export MONITORING_ALERT_THRESHOLD="0.5"  # 50% error rate
            ;;
    esac
    
    # Initialize monitoring database
    log_info "Initializing monitoring database..."
    uv run python -c "
import sys
sys.path.insert(0, 'src')
from finwiz.monitoring.investment_discovery_monitor import get_discovery_monitor
monitor = get_discovery_monitor()
print('Investment Discovery monitoring initialized')
"
    
    log_success "Investment Discovery components deployed"
}

# Start monitoring services
start_monitoring_services() {
    log_info "Starting Investment Discovery monitoring services..."
    
    cd "$PROJECT_ROOT"
    
    # Create monitoring service script
    cat > "$PROJECT_ROOT/scripts/start_discovery_monitor.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD/src:$PYTHONPATH"

# Start monitoring service
uv run python -c "
import asyncio
import signal
import sys
from finwiz.monitoring.investment_discovery_monitor import monitor_discovery_health
from finwiz.tools.logger import get_logger

logger = get_logger('discovery_monitor')

async def monitoring_loop():
    '''Main monitoring loop.'''
    while True:
        try:
            health_data = await monitor_discovery_health()
            logger.info(f'Health check completed: {health_data[\"health_status\"][\"status\"]}')
            
            # Check for critical alerts
            critical_alerts = [
                alert for alert in health_data['active_alerts'] 
                if alert.get('severity') == 'critical'
            ]
            
            if critical_alerts:
                logger.error(f'Critical alerts detected: {len(critical_alerts)}')
                for alert in critical_alerts:
                    logger.error(f'CRITICAL: {alert[\"message\"]}')
            
            # Wait 60 seconds before next check
            await asyncio.sleep(60)
            
        except Exception as e:
            logger.error(f'Monitoring loop error: {e}')
            await asyncio.sleep(30)  # Shorter wait on error

def signal_handler(signum, frame):
    '''Handle shutdown signals.'''
    logger.info('Monitoring service shutting down...')
    sys.exit(0)

# Set up signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# Start monitoring
logger.info('Starting Investment Discovery monitoring service...')
asyncio.run(monitoring_loop())
"
EOF
    
    chmod +x "$PROJECT_ROOT/scripts/start_discovery_monitor.sh"
    
    # Start monitoring service in background
    nohup "$PROJECT_ROOT/scripts/start_discovery_monitor.sh" > "$PROJECT_ROOT/logs/discovery_monitor.log" 2>&1 &
    local monitor_pid=$!
    
    # Wait a moment and check if it started successfully
    sleep 3
    if kill -0 "$monitor_pid" 2>/dev/null; then
        log_success "Investment Discovery monitoring service started (PID: $monitor_pid)"
        echo "$monitor_pid" > "$PROJECT_ROOT/logs/discovery_monitor.pid"
    else
        log_error "Failed to start Investment Discovery monitoring service"
        exit 1
    fi
}

# Post-deployment verification for Investment Discovery
post_deployment_verification() {
    log_info "Running Investment Discovery post-deployment verification..."
    
    cd "$PROJECT_ROOT"
    
    # Test Investment Discovery Crew initialization
    if ! timeout 60 uv run python -c "
import sys
sys.path.insert(0, 'src')
from finwiz.crews.investment_discovery_crew.investment_discovery_crew import InvestmentDiscoveryCrew
from finwiz.monitoring.investment_discovery_monitor import get_discovery_monitor

# Test crew initialization
try:
    crew = InvestmentDiscoveryCrew()
    print('✅ Investment Discovery Crew initialized successfully')
except Exception as e:
    print(f'❌ Investment Discovery Crew initialization failed: {e}')
    sys.exit(1)

# Test monitoring system
try:
    monitor = get_discovery_monitor()
    dashboard_data = monitor.get_dashboard_data()
    print(f'✅ Monitoring system operational (health: {dashboard_data[\"health_status\"][\"status\"]})')
except Exception as e:
    print(f'❌ Monitoring system failed: {e}')
    sys.exit(1)

print('✅ Investment Discovery post-deployment verification successful')
"; then
        log_error "Investment Discovery post-deployment verification failed"
        exit 1
    fi
    
    # Test monitoring service
    if [[ -f "$PROJECT_ROOT/logs/discovery_monitor.pid" ]]; then
        local monitor_pid=$(cat "$PROJECT_ROOT/logs/discovery_monitor.pid")
        if kill -0 "$monitor_pid" 2>/dev/null; then
            log_success "Monitoring service is running (PID: $monitor_pid)"
        else
            log_error "Monitoring service is not running"
            exit 1
        fi
    fi
    
    log_success "Investment Discovery post-deployment verification completed"
}

# Create monitoring dashboard
create_monitoring_dashboard() {
    log_info "Creating Investment Discovery monitoring dashboard..."
    
    cd "$PROJECT_ROOT"
    
    # Create dashboard HTML template
    cat > "$PROJECT_ROOT/output/monitoring/dashboard.html" << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Investment Discovery Monitoring Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .metric-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric-title { font-size: 18px; font-weight: bold; margin-bottom: 10px; color: #2c3e50; }
        .metric-value { font-size: 24px; font-weight: bold; color: #27ae60; }
        .alert-critical { color: #e74c3c; }
        .alert-warning { color: #f39c12; }
        .status-healthy { color: #27ae60; }
        .status-degraded { color: #f39c12; }
        .status-unhealthy { color: #e74c3c; }
        .refresh-btn { background: #3498db; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        .timestamp { color: #7f8c8d; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Investment Discovery Monitoring Dashboard</h1>
            <button class="refresh-btn" onclick="refreshDashboard()">Refresh Data</button>
            <div class="timestamp" id="lastUpdate">Last updated: Loading...</div>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-title">System Health</div>
                <div class="metric-value" id="healthStatus">Loading...</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">Total Discoveries</div>
                <div class="metric-value" id="totalDiscoveries">Loading...</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">A+ Discoveries</div>
                <div class="metric-value" id="aPlusDiscoveries">Loading...</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">Success Rate</div>
                <div class="metric-value" id="successRate">Loading...</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">Average Discovery Time</div>
                <div class="metric-value" id="avgDiscoveryTime">Loading...</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">Active Alerts</div>
                <div class="metric-value" id="activeAlerts">Loading...</div>
            </div>
        </div>
        
        <div class="metric-card" style="margin-top: 20px;">
            <div class="metric-title">Recent Alerts</div>
            <div id="alertsList">Loading...</div>
        </div>
    </div>
    
    <script>
        async function refreshDashboard() {
            try {
                // This would connect to a real API endpoint in production
                // For now, we'll simulate with static data
                const mockData = {
                    health_status: { status: 'healthy' },
                    discovery_metrics: {
                        total_discoveries: 42,
                        a_plus_discoveries: 15,
                        discovery_success_rate: 0.85,
                        avg_discovery_time: 245.5
                    },
                    active_alerts: [],
                    recent_alerts: []
                };
                
                updateDashboard(mockData);
            } catch (error) {
                console.error('Failed to refresh dashboard:', error);
            }
        }
        
        function updateDashboard(data) {
            document.getElementById('healthStatus').textContent = data.health_status.status;
            document.getElementById('healthStatus').className = 'metric-value status-' + data.health_status.status;
            
            document.getElementById('totalDiscoveries').textContent = data.discovery_metrics.total_discoveries;
            document.getElementById('aPlusDiscoveries').textContent = data.discovery_metrics.a_plus_discoveries;
            document.getElementById('successRate').textContent = (data.discovery_metrics.discovery_success_rate * 100).toFixed(1) + '%';
            document.getElementById('avgDiscoveryTime').textContent = data.discovery_metrics.avg_discovery_time.toFixed(1) + 's';
            document.getElementById('activeAlerts').textContent = data.active_alerts.length;
            
            const alertsList = document.getElementById('alertsList');
            if (data.recent_alerts.length === 0) {
                alertsList.innerHTML = '<div style="color: #27ae60;">No recent alerts</div>';
            } else {
                alertsList.innerHTML = data.recent_alerts.map(alert => 
                    `<div class="alert-${alert.severity}">${alert.message} (${alert.timestamp})</div>`
                ).join('');
            }
            
            document.getElementById('lastUpdate').textContent = 'Last updated: ' + new Date().toLocaleString();
        }
        
        // Auto-refresh every 30 seconds
        setInterval(refreshDashboard, 30000);
        
        // Initial load
        refreshDashboard();
    </script>
</body>
</html>
EOF
    
    log_success "Monitoring dashboard created at output/monitoring/dashboard.html"
}

# Main deployment function
main() {
    log_info "Starting Investment Discovery Crew deployment (Environment: $DEPLOYMENT_ENV)"
    
    # Run base deployment first
    log_info "Running base FinWiz deployment..."
    "$SCRIPT_DIR/deploy.sh" -e "$DEPLOYMENT_ENV"
    
    # Investment Discovery specific deployment
    pre_deployment_checks
    deploy_investment_discovery
    start_monitoring_services
    post_deployment_verification
    create_monitoring_dashboard
    
    log_success "🚀 Investment Discovery Crew deployment completed successfully!"
    log_info "Deployment environment: $DEPLOYMENT_ENV"
    log_info "Monitoring dashboard: output/monitoring/dashboard.html"
    log_info "Monitoring logs: logs/discovery_monitor.log"
}

# Script usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -e, --env ENV          Deployment environment (production|staging|development)"
    echo "  -b, --backup-dir DIR   Backup directory path"
    echo "  -l, --log-file FILE    Log file path"
    echo "  -h, --help            Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  DEPLOYMENT_ENV         Deployment environment"
    echo "  BACKUP_DIR            Backup directory"
    echo "  LOG_FILE              Log file path"
    echo "  FF_INVESTMENT_DISCOVERY Feature flag for investment discovery"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env)
            DEPLOYMENT_ENV="$2"
            shift 2
            ;;
        -b|--backup-dir)
            BACKUP_DIR="$2"
            shift 2
            ;;
        -l|--log-file)
            LOG_FILE="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate deployment environment
case "$DEPLOYMENT_ENV" in
    "production"|"staging"|"development")
        ;;
    *)
        log_error "Invalid deployment environment: $DEPLOYMENT_ENV"
        log_error "Valid environments: production, staging, development"
        exit 1
        ;;
esac

# Run main deployment
main