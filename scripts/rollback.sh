#!/bin/bash

# FinWiz Rollback Script
# This script handles rollback procedures and error recovery for FinWiz deployments

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups}"
LOG_FILE="${LOG_FILE:-$PROJECT_ROOT/logs/rollback.log}"

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
    log_error "Rollback script failed at line $line_number"
    log_error "Manual intervention may be required"
    exit 1
}

trap 'error_handler $LINENO' ERR

# List available backups
list_backups() {
    log_info "Available backups:"

    if [[ ! -d "$BACKUP_DIR" ]]; then
        log_error "Backup directory not found: $BACKUP_DIR"
        exit 1
    fi

    local backups=($(find "$BACKUP_DIR" -name "deployment_backup_*.tar.gz" -type f | sort -r))

    if [[ ${#backups[@]} -eq 0 ]]; then
        log_error "No backups found in $BACKUP_DIR"
        exit 1
    fi

    for i in "${!backups[@]}"; do
        local backup="${backups[$i]}"
        local basename=$(basename "$backup")
        local timestamp=$(echo "$basename" | sed 's/deployment_backup_\(.*\)\.tar\.gz/\1/')
        local formatted_time=$(date -d "${timestamp:0:8} ${timestamp:9:2}:${timestamp:11:2}:${timestamp:13:2}" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo "$timestamp")
        local size=$(du -h "$backup" | cut -f1)

        echo "  $((i+1)). $basename ($formatted_time, $size)"
    done

    echo "${backups[@]}"
}

# Select backup interactively
select_backup() {
    local backups_output=$(list_backups)
    local backups=($(echo "$backups_output" | tail -n 1))

    if [[ ${#backups[@]} -eq 1 ]]; then
        log_info "Only one backup available, selecting automatically"
        echo "${backups[0]}"
        return
    fi

    echo ""
    read -p "Select backup number (1-${#backups[@]}): " selection

    if [[ ! "$selection" =~ ^[0-9]+$ ]] || [[ "$selection" -lt 1 ]] || [[ "$selection" -gt ${#backups[@]} ]]; then
        log_error "Invalid selection: $selection"
        exit 1
    fi

    echo "${backups[$((selection-1))]}"
}

# Validate backup integrity
validate_backup() {
    local backup_file="$1"

    log_info "Validating backup integrity: $(basename "$backup_file")"

    # Check if file exists and is readable
    if [[ ! -f "$backup_file" ]] || [[ ! -r "$backup_file" ]]; then
        log_error "Backup file not found or not readable: $backup_file"
        exit 1
    fi

    # Test tar file integrity
    if ! tar -tzf "$backup_file" >/dev/null 2>&1; then
        log_error "Backup file is corrupted: $backup_file"
        exit 1
    fi

    # Check if backup contains essential files
    local essential_files=("src/finwiz/main.py" "pyproject.toml" "Makefile")
    for file in "${essential_files[@]}"; do
        if ! tar -tzf "$backup_file" | grep -q "^$file$"; then
            log_error "Backup missing essential file: $file"
            exit 1
        fi
    done

    log_success "Backup validation passed"
}

# Create pre-rollback backup
create_pre_rollback_backup() {
    log_info "Creating pre-rollback backup..."

    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_file="$BACKUP_DIR/pre_rollback_backup_${timestamp}.tar.gz"

    cd "$PROJECT_ROOT"
    tar -czf "$backup_file" \
        --exclude='.git' \
        --exclude='__pycache__' \
        --exclude='.pytest_cache' \
        --exclude='htmlcov' \
        --exclude='.venv' \
        --exclude='node_modules' \
        .

    log_success "Pre-rollback backup created: $backup_file"
}

# Stop running services
stop_services() {
    log_info "Stopping running services..."

    # Stop any running FinWiz processes
    local pids=$(pgrep -f "finwiz" || true)
    if [[ -n "$pids" ]]; then
        log_info "Stopping FinWiz processes: $pids"
        echo "$pids" | xargs -r kill -TERM

        # Wait for graceful shutdown
        sleep 5

        # Force kill if still running
        local remaining_pids=$(pgrep -f "finwiz" || true)
        if [[ -n "$remaining_pids" ]]; then
            log_warn "Force killing remaining processes: $remaining_pids"
            echo "$remaining_pids" | xargs -r kill -KILL
        fi
    fi

    log_success "Services stopped"
}

# Restore from backup
restore_from_backup() {
    local backup_file="$1"

    log_info "Restoring from backup: $(basename "$backup_file")"

    # Validate backup before restoration
    validate_backup "$backup_file"

    # Create pre-rollback backup
    create_pre_rollback_backup

    # Stop services
    stop_services

    # Clear current directory (except for critical files)
    cd "$PROJECT_ROOT"

    # Preserve critical files
    local preserve_files=(".env" "logs/" "backups/" "cache/")
    local temp_dir=$(mktemp -d)

    for file in "${preserve_files[@]}"; do
        if [[ -e "$file" ]]; then
            cp -r "$file" "$temp_dir/" 2>/dev/null || true
        fi
    done

    # Remove current files (except preserved ones)
    find . -maxdepth 1 -type f -not -name ".env" -not -name "*.log" -delete 2>/dev/null || true
    find . -maxdepth 1 -type d -not -name "." -not -name "logs" -not -name "backups" -not -name "cache" -exec rm -rf {} + 2>/dev/null || true

    # Extract backup
    tar -xzf "$backup_file"

    # Restore preserved files
    for file in "${preserve_files[@]}"; do
        if [[ -e "$temp_dir/$file" ]]; then
            cp -r "$temp_dir/$file" . 2>/dev/null || true
        fi
    done

    # Cleanup temp directory
    rm -rf "$temp_dir"

    log_success "Backup restored successfully"
}

# Verify rollback
verify_rollback() {
    log_info "Verifying rollback..."

    cd "$PROJECT_ROOT"

    # Check essential files exist
    local essential_files=("src/finwiz/main.py" "pyproject.toml" "Makefile")
    for file in "${essential_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            log_error "Essential file missing after rollback: $file"
            exit 1
        fi
    done

    # Test application startup
    log_info "Testing application startup..."

    if ! timeout 30 uv run python -c "
import sys
sys.path.insert(0, 'src')
from finwiz.utils.configuration_manager import get_configuration_manager

try:
    config_manager = get_configuration_manager()
    print('✅ Configuration manager loaded successfully')
except Exception as e:
    print(f'❌ Configuration manager failed: {e}')
    sys.exit(1)
"; then
        log_error "Application startup test failed"
        exit 1
    fi

    log_success "Rollback verification completed"
}

# Emergency recovery mode
emergency_recovery() {
    log_warn "Entering emergency recovery mode..."

    # Try to restore from the most recent backup
    local latest_backup=$(find "$BACKUP_DIR" -name "deployment_backup_*.tar.gz" -type f | sort -r | head -n 1)

    if [[ -z "$latest_backup" ]]; then
        log_error "No backups available for emergency recovery"
        log_error "Manual intervention required"
        exit 1
    fi

    log_info "Using latest backup for emergency recovery: $(basename "$latest_backup")"

    # Skip interactive selection and validation for emergency
    restore_from_backup "$latest_backup"

    # Basic verification
    if [[ -f "$PROJECT_ROOT/src/finwiz/main.py" ]]; then
        log_success "Emergency recovery completed"
    else
        log_error "Emergency recovery failed"
        exit 1
    fi
}

# Health check after rollback
health_check() {
    log_info "Performing post-rollback health check..."

    cd "$PROJECT_ROOT"

    # Check dependencies
    if ! uv sync --no-dev >/dev/null 2>&1; then
        log_warn "Dependency installation failed, attempting repair..."
        uv sync --no-dev --force-reinstall >/dev/null 2>&1 || log_error "Dependency repair failed"
    fi

    # Run basic tests
    if command -v pytest >/dev/null 2>&1; then
        log_info "Running basic health tests..."
        if ! timeout 60 uv run pytest tests/unit/ -x --tb=no -q >/dev/null 2>&1; then
            log_warn "Some tests failed after rollback"
        else
            log_success "Health tests passed"
        fi
    fi

    log_success "Health check completed"
}

# Main rollback function
main() {
    local backup_file=""
    local emergency_mode=false
    local skip_verification=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -b|--backup)
                backup_file="$2"
                shift 2
                ;;
            -e|--emergency)
                emergency_mode=true
                shift
                ;;
            --skip-verification)
                skip_verification=true
                shift
                ;;
            -l|--list)
                list_backups
                exit 0
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

    log_info "Starting FinWiz rollback procedure"

    if [[ "$emergency_mode" == "true" ]]; then
        emergency_recovery
        return
    fi

    # Select backup if not specified
    if [[ -z "$backup_file" ]]; then
        backup_file=$(select_backup)
    fi

    # Validate backup file path
    if [[ ! -f "$backup_file" ]]; then
        log_error "Backup file not found: $backup_file"
        exit 1
    fi

    # Confirm rollback
    echo ""
    log_warn "This will rollback FinWiz to backup: $(basename "$backup_file")"
    log_warn "Current state will be backed up before rollback"
    read -p "Are you sure you want to proceed? (y/N): " confirm

    if [[ "$confirm" != "y" ]] && [[ "$confirm" != "Y" ]]; then
        log_info "Rollback cancelled by user"
        exit 0
    fi

    # Perform rollback
    restore_from_backup "$backup_file"

    if [[ "$skip_verification" != "true" ]]; then
        verify_rollback
        health_check
    fi

    log_success "🔄 FinWiz rollback completed successfully!"
    log_info "Rolled back to: $(basename "$backup_file")"
    log_info "Pre-rollback state backed up in: $BACKUP_DIR"
}

# Script usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -b, --backup FILE      Specific backup file to restore"
    echo "  -e, --emergency        Emergency recovery mode (use latest backup)"
    echo "  -l, --list            List available backups"
    echo "  --skip-verification   Skip post-rollback verification"
    echo "  -h, --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    Interactive rollback (select backup)"
    echo "  $0 -l                 List available backups"
    echo "  $0 -b backup.tar.gz   Rollback to specific backup"
    echo "  $0 -e                 Emergency recovery mode"
}

# Run main function
main "$@"
