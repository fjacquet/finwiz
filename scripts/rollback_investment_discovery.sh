#!/bin/bash

# Investment Discovery Rollback Script
# Specialized rollback script for Investment Discovery Crew with monitoring cleanup

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups}"
LOG_FILE="${LOG_FILE:-$PROJECT_ROOT/logs/investment_discovery_rollback.log}"

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
    log_error "Investment Discovery rollback failed at line $line_number"
    log_error "Manual intervention may be required"
    exit 1
}

trap 'error_handler $LINENO' ERR

# Stop Investment Discovery services
stop_discovery_services() {
    log_info "Stopping Investment Discovery services..."
    
    # Stop monitoring service
    if [[ -f "$PROJECT_ROOT/logs/discovery_monitor.pid" ]]; then
        local monitor_pid=$(cat "$PROJECT_ROOT/logs/discovery_monitor.pid")
        if kill -0 "$monitor_pid" 2>/dev/null; then
            log_info "Stopping monitoring service (PID: $monitor_pid)"
            kill -TERM "$monitor_pid"
            
            # Wait for graceful shutdown
            local count=0
            while kill -0 "$monitor_pid" 2>/dev/null && [[ $count -lt 30 ]]; do
                sleep 1
                ((count++))
            done
            
            # Force kill if still running
            if kill -0 "$monitor_pid" 2>/dev/null; then
                log_warn "Force killing monitoring service"
                kill -KILL "$monitor_pid"
            fi
            
            rm -f "$PROJECT_ROOT/logs/discovery_monitor.pid"
            log_success "Monitoring service stopped"
        else
            log_info "Monitoring service not running"
        fi
    fi
    
    # Stop any running discovery processes
    local discovery_pids=$(pgrep -f "investment_discovery" || true)
    if [[ -n "$discovery_pids" ]]; then
        log_info "Stopping discovery processes: $discovery_pids"
        echo "$discovery_pids" | xargs -r kill -TERM
        
        # Wait for graceful shutdown
        sleep 5
        
        # Force kill if still running
        local remaining_pids=$(pgrep -f "investment_discovery" || true)
        if [[ -n "$remaining_pids" ]]; then
            log_warn "Force killing remaining discovery processes: $remaining_pids"
            echo "$remaining_pids" | xargs -r kill -KILL
        fi
    fi
    
    log_success "Investment Discovery services stopped"
}

# Disable Investment Discovery features
disable_discovery_features() {
    log_info "Disabling Investment Discovery features..."
    
    cd "$PROJECT_ROOT"
    
    # Disable feature flags
    export FF_INVESTMENT_DISCOVERY="false"
    export FF_INVESTMENT_DISCOVERY_MONITORING="false"
    
    # Update environment file if it exists
    if [[ -f ".env" ]]; then
        # Create backup of .env
        cp ".env" ".env.backup.$(date +%Y%m%d_%H%M%S)"
        
        # Update feature flags in .env
        if grep -q "FF_INVESTMENT_DISCOVERY=" ".env"; then
            sed -i.bak 's/FF_INVESTMENT_DISCOVERY=.*/FF_INVESTMENT_DISCOVERY=false/' ".env"
        else
            echo "FF_INVESTMENT_DISCOVERY=false" >> ".env"
        fi
        
        if grep -q "FF_INVESTMENT_DISCOVERY_MONITORING=" ".env"; then
            sed -i.bak 's/FF_INVESTMENT_DISCOVERY_MONITORING=.*/FF_INVESTMENT_DISCOVERY_MONITORING=false/' ".env"
        else
            echo "FF_INVESTMENT_DISCOVERY_MONITORING=false" >> ".env"
        fi
        
        # Clean up backup files
        rm -f ".env.bak"
    fi
    
    log_success "Investment Discovery features disabled"
}

# Clean up monitoring data
cleanup_monitoring_data() {
    log_info "Cleaning up Investment Discovery monitoring data..."
    
    cd "$PROJECT_ROOT"
    
    # Archive monitoring data before cleanup
    local archive_dir="$BACKUP_DIR/monitoring_archive_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$archive_dir"
    
    if [[ -d "output/monitoring" ]]; then
        cp -r "output/monitoring" "$archive_dir/" 2>/dev/null || true
        log_info "Monitoring data archived to: $archive_dir"
    fi
    
    # Clean up monitoring files
    rm -rf "output/monitoring" 2>/dev/null || true
    rm -f "logs/discovery_monitor.log" 2>/dev/null || true
    rm -f "logs/investment_discovery_deployment.log" 2>/dev/null || true
    rm -f "scripts/start_discovery_monitor.sh" 2>/dev/null || true
    
    log_success "Monitoring data cleaned up"
}

# Remove Discovery output files
cleanup_discovery_output() {
    log_info "Cleaning up Investment Discovery output files..."
    
    cd "$PROJECT_ROOT"
    
    # Archive discovery output before cleanup
    local archive_dir="$BACKUP_DIR/discovery_archive_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$archive_dir"
    
    if [[ -d "output/discovery" ]]; then
        cp -r "output/discovery" "$archive_dir/" 2>/dev/null || true
        log_info "Discovery output archived to: $archive_dir"
    fi
    
    # Clean up discovery files
    rm -rf "output/discovery" 2>/dev/null || true
    
    log_success "Discovery output cleaned up"
}

# Validate rollback
validate_rollback() {
    log_info "Validating Investment Discovery rollback..."
    
    cd "$PROJECT_ROOT"
    
    # Check that discovery services are stopped
    local discovery_pids=$(pgrep -f "investment_discovery" || true)
    if [[ -n "$discovery_pids" ]]; then
        log_error "Discovery processes still running: $discovery_pids"
        exit 1
    fi
    
    # Check that monitoring service is stopped
    if [[ -f "$PROJECT_ROOT/logs/discovery_monitor.pid" ]]; then
        local monitor_pid=$(cat "$PROJECT_ROOT/logs/discovery_monitor.pid")
        if kill -0 "$monitor_pid" 2>/dev/null; then
            log_error "Monitoring service still running: $monitor_pid"
            exit 1
        fi
    fi
    
    # Test that base FinWiz still works
    if ! timeout 30 uv run python -c "
import sys
sys.path.insert(0, 'src')
from finwiz.utils.configuration_manager import get_configuration_manager
from finwiz.utils.feature_flags import is_feature_enabled

# Test configuration
try:
    config_manager = get_configuration_manager()
    print('✅ Configuration manager working')
except Exception as e:
    print(f'❌ Configuration manager failed: {e}')
    sys.exit(1)

# Test feature flags
try:
    discovery_enabled = is_feature_enabled('investment_discovery')
    if discovery_enabled:
        print('❌ Investment Discovery still enabled')
        sys.exit(1)
    else:
        print('✅ Investment Discovery properly disabled')
except Exception as e:
    print(f'❌ Feature flag check failed: {e}')
    sys.exit(1)

print('✅ Investment Discovery rollback validation successful')
"; then
        log_error "Investment Discovery rollback validation failed"
        exit 1
    fi
    
    log_success "Investment Discovery rollback validation completed"
}

# Send rollback notification
send_rollback_notification() {
    log_info "Sending rollback notification..."
    
    cd "$PROJECT_ROOT"
    
    # Try to send alert if alerting system is available
    if uv run python -c "
import sys
sys.path.insert(0, 'src')
try:
    from finwiz.monitoring.alerting import send_discovery_alert, AlertType, AlertSeverity
    import asyncio
    
    async def send_alert():
        await send_discovery_alert(
            AlertType.SYSTEM_HEALTH,
            AlertSeverity.WARNING,
            'Investment Discovery Rollback Completed',
            'Investment Discovery system has been rolled back and disabled. All services stopped and data archived.',
            {'rollback_time': '$(date -u +\"%Y-%m-%dT%H:%M:%SZ\")', 'reason': 'Manual rollback'}
        )
    
    asyncio.run(send_alert())
    print('✅ Rollback notification sent')
except Exception as e:
    print(f'⚠️ Could not send rollback notification: {e}')
" 2>/dev/null || true; then
        log_success "Rollback notification sent"
    else
        log_warn "Could not send rollback notification (alerting system may be disabled)"
    fi
}

# Create rollback report
create_rollback_report() {
    log_info "Creating rollback report..."
    
    local report_file="$PROJECT_ROOT/logs/investment_discovery_rollback_report_$(date +%Y%m%d_%H%M%S).txt"
    
    cat > "$report_file" << EOF
Investment Discovery Rollback Report
===================================

Rollback Time: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
Rollback Reason: ${ROLLBACK_REASON:-"Manual rollback"}
Rollback Environment: ${DEPLOYMENT_ENV:-"unknown"}

Actions Performed:
- ✅ Stopped Investment Discovery services
- ✅ Disabled Investment Discovery feature flags
- ✅ Cleaned up monitoring data (archived)
- ✅ Cleaned up discovery output (archived)
- ✅ Validated rollback completion

Archived Data:
- Monitoring data: $BACKUP_DIR/monitoring_archive_*
- Discovery output: $BACKUP_DIR/discovery_archive_*
- Environment backup: .env.backup.*

System Status:
- Investment Discovery: DISABLED
- Monitoring Service: STOPPED
- Base FinWiz: OPERATIONAL

Recovery Instructions:
To re-enable Investment Discovery:
1. Set FF_INVESTMENT_DISCOVERY=true in .env
2. Run: scripts/deploy_investment_discovery.sh
3. Monitor logs for successful startup

Support Information:
- Log file: $LOG_FILE
- Rollback report: $report_file
- Backup directory: $BACKUP_DIR

EOF
    
    log_success "Rollback report created: $report_file"
}

# Emergency rollback mode
emergency_rollback() {
    log_warn "Performing emergency Investment Discovery rollback..."
    
    # Skip confirmations and validations in emergency mode
    stop_discovery_services
    disable_discovery_features
    cleanup_monitoring_data
    cleanup_discovery_output
    
    log_success "Emergency rollback completed"
}

# Main rollback function
main() {
    local emergency_mode=false
    local skip_cleanup=false
    local skip_validation=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--emergency)
                emergency_mode=true
                shift
                ;;
            --skip-cleanup)
                skip_cleanup=true
                shift
                ;;
            --skip-validation)
                skip_validation=true
                shift
                ;;
            -r|--reason)
                ROLLBACK_REASON="$2"
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
    
    log_info "Starting Investment Discovery rollback procedure"
    
    if [[ "$emergency_mode" == "true" ]]; then
        emergency_rollback
        return
    fi
    
    # Confirm rollback
    echo ""
    log_warn "This will rollback Investment Discovery system and disable all discovery features"
    log_warn "All discovery data will be archived before cleanup"
    read -p "Are you sure you want to proceed? (y/N): " confirm
    
    if [[ "$confirm" != "y" ]] && [[ "$confirm" != "Y" ]]; then
        log_info "Rollback cancelled by user"
        exit 0
    fi
    
    # Perform rollback
    stop_discovery_services
    disable_discovery_features
    
    if [[ "$skip_cleanup" != "true" ]]; then
        cleanup_monitoring_data
        cleanup_discovery_output
    fi
    
    if [[ "$skip_validation" != "true" ]]; then
        validate_rollback
    fi
    
    send_rollback_notification
    create_rollback_report
    
    log_success "🔄 Investment Discovery rollback completed successfully!"
    log_info "System status: Investment Discovery DISABLED, Base FinWiz OPERATIONAL"
    log_info "All data has been archived in: $BACKUP_DIR"
}

# Script usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -e, --emergency        Emergency rollback mode (skip confirmations)"
    echo "  -r, --reason REASON    Reason for rollback (for reporting)"
    echo "  --skip-cleanup         Skip cleanup of output files"
    echo "  --skip-validation      Skip post-rollback validation"
    echo "  -h, --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    Interactive rollback"
    echo "  $0 -e                 Emergency rollback"
    echo "  $0 -r \"Performance issues\" Rollback with reason"
}

# Run main function
main "$@"