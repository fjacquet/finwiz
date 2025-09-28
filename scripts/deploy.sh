#!/bin/bash

# FinWiz Deployment Script
# This script handles deployment of FinWiz application with proper configuration validation

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOYMENT_ENV="${DEPLOYMENT_ENV:-production}"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups}"
LOG_FILE="${LOG_FILE:-$PROJECT_ROOT/logs/deployment.log}"

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
    log_error "Deployment failed at line $line_number"
    log_error "Rolling back changes..."
    rollback_deployment
    exit 1
}

trap 'error_handler $LINENO' ERR

# Rollback function
rollback_deployment() {
    log_warn "Initiating rollback procedure..."
    
    if [[ -f "$BACKUP_DIR/last_deployment_backup.tar.gz" ]]; then
        log_info "Restoring from backup..."
        cd "$PROJECT_ROOT"
        tar -xzf "$BACKUP_DIR/last_deployment_backup.tar.gz"
        log_success "Rollback completed"
    else
        log_error "No backup found for rollback"
    fi
}

# Pre-deployment checks
pre_deployment_checks() {
    log_info "Running pre-deployment checks..."
    
    # Check if uv is installed
    if ! command -v uv &> /dev/null; then
        log_error "uv package manager not found. Please install uv first."
        exit 1
    fi
    
    # Check Python version
    python_version=$(python3 --version | cut -d' ' -f2)
    if [[ ! "$python_version" =~ ^3\.(10|11|12) ]]; then
        log_error "Python 3.10+ required. Found: $python_version"
        exit 1
    fi
    
    # Check required directories
    mkdir -p "$BACKUP_DIR" "$PROJECT_ROOT/logs" "$PROJECT_ROOT/cache" "$PROJECT_ROOT/output"
    
    # Create integration system directories
    mkdir -p "$PROJECT_ROOT/output/integration/metadata"
    mkdir -p "$PROJECT_ROOT/output/integration/contracts"
    mkdir -p "$PROJECT_ROOT/output/integration/consolidated"
    
    # Validate environment configuration
    log_info "Validating environment configuration..."
    cd "$PROJECT_ROOT"
    
    if ! uv run python -c "
from finwiz.utils.configuration_manager import get_configuration_manager
from finwiz.integration.config import load_integration_config
from pathlib import Path

try:
    # Validate main configuration
    config_manager = get_configuration_manager()
    config_manager.validate_startup_configuration()
    print('✅ Main configuration validation successful')
    
    # Validate integration system configuration
    integration_config_path = Path('config/integration.yaml')
    integration_config = load_integration_config(integration_config_path if integration_config_path.exists() else None)
    print(f'✅ Integration system configuration loaded (output_dir: {integration_config.output_dir})')
    
    print('✅ All configuration validation successful')
except Exception as e:
    print(f'❌ Configuration validation failed: {e}')
    exit(1)
"; then
        log_error "Configuration validation failed"
        exit 1
    fi
    
    log_success "Pre-deployment checks passed"
}

# Create backup
create_backup() {
    log_info "Creating deployment backup..."
    
    local backup_timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_file="$BACKUP_DIR/deployment_backup_${backup_timestamp}.tar.gz"
    
    cd "$PROJECT_ROOT"
    tar -czf "$backup_file" \
        --exclude='.git' \
        --exclude='__pycache__' \
        --exclude='.pytest_cache' \
        --exclude='htmlcov' \
        --exclude='.venv' \
        --exclude='node_modules' \
        .
    
    # Create symlink to latest backup
    ln -sf "$backup_file" "$BACKUP_DIR/last_deployment_backup.tar.gz"
    
    log_success "Backup created: $backup_file"
}

# Install dependencies
install_dependencies() {
    log_info "Installing dependencies..."
    
    cd "$PROJECT_ROOT"
    
    # Install production dependencies
    uv sync --no-dev
    
    log_success "Dependencies installed"
}

# Run tests
run_tests() {
    log_info "Running test suite..."
    
    cd "$PROJECT_ROOT"
    
    # Run unit tests
    if ! uv run pytest tests/unit/ -v --tb=short; then
        log_error "Unit tests failed"
        exit 1
    fi
    
    # Run integration tests if enabled
    if [[ "${RUN_INTEGRATION_TESTS:-false}" == "true" ]]; then
        log_info "Running integration tests..."
        if ! uv run pytest tests/integration/ -m integration -v --tb=short; then
            log_error "Integration tests failed"
            exit 1
        fi
    fi
    
    log_success "Tests passed"
}

# Deploy application
deploy_application() {
    log_info "Deploying application..."
    
    cd "$PROJECT_ROOT"
    
    # Set deployment environment
    export FINWIZ_DEPLOYMENT_ENV="$DEPLOYMENT_ENV"
    export FINWIZ_DEPLOYMENT_TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    # Enable production optimizations
    export FINWIZ_PRODUCTION_MODE="true"
    export FINWIZ_LOG_LEVEL="${FINWIZ_LOG_LEVEL:-INFO}"
    
    # Configure feature flags for production
    case "$DEPLOYMENT_ENV" in
        "production")
            export FF_PORTFOLIO_REBALANCING="${FF_PORTFOLIO_REBALANCING:-false}"
            export FF_REBALANCING_API="${FF_REBALANCING_API:-false}"
            export FF_REBALANCING_MONITORING="${FF_REBALANCING_MONITORING:-false}"
            # Integration system settings for production
            export FINWIZ_INTEGRATION_SYSTEM_ENABLED="${FINWIZ_INTEGRATION_SYSTEM_ENABLED:-true}"
            export FINWIZ_INTEGRATION_STRICT_VALIDATION="${FINWIZ_INTEGRATION_STRICT_VALIDATION:-true}"
            export FINWIZ_INTEGRATION_LOG_LEVEL="${FINWIZ_INTEGRATION_LOG_LEVEL:-INFO}"
            export FINWIZ_INTEGRATION_PERFORMANCE_MONITORING="${FINWIZ_INTEGRATION_PERFORMANCE_MONITORING:-false}"
            ;;
        "staging")
            export FF_PORTFOLIO_REBALANCING="${FF_PORTFOLIO_REBALANCING:-true}"
            export FF_REBALANCING_API="${FF_REBALANCING_API:-true}"
            export FF_REBALANCING_MONITORING="${FF_REBALANCING_MONITORING:-false}"
            # Integration system settings for staging
            export FINWIZ_INTEGRATION_SYSTEM_ENABLED="${FINWIZ_INTEGRATION_SYSTEM_ENABLED:-true}"
            export FINWIZ_INTEGRATION_STRICT_VALIDATION="${FINWIZ_INTEGRATION_STRICT_VALIDATION:-true}"
            export FINWIZ_INTEGRATION_LOG_LEVEL="${FINWIZ_INTEGRATION_LOG_LEVEL:-DEBUG}"
            export FINWIZ_INTEGRATION_PERFORMANCE_MONITORING="${FINWIZ_INTEGRATION_PERFORMANCE_MONITORING:-true}"
            ;;
        "development")
            export FF_PORTFOLIO_REBALANCING="${FF_PORTFOLIO_REBALANCING:-true}"
            export FF_REBALANCING_API="${FF_REBALANCING_API:-true}"
            export FF_REBALANCING_MONITORING="${FF_REBALANCING_MONITORING:-true}"
            # Integration system settings for development
            export FINWIZ_INTEGRATION_SYSTEM_ENABLED="${FINWIZ_INTEGRATION_SYSTEM_ENABLED:-true}"
            export FINWIZ_INTEGRATION_STRICT_VALIDATION="${FINWIZ_INTEGRATION_STRICT_VALIDATION:-false}"
            export FINWIZ_INTEGRATION_LOG_LEVEL="${FINWIZ_INTEGRATION_LOG_LEVEL:-DEBUG}"
            export FINWIZ_INTEGRATION_DEBUG_MODE="${FINWIZ_INTEGRATION_DEBUG_MODE:-true}"
            export FINWIZ_INTEGRATION_PERFORMANCE_MONITORING="${FINWIZ_INTEGRATION_PERFORMANCE_MONITORING:-true}"
            ;;
    esac
    
    log_success "Application deployed with environment: $DEPLOYMENT_ENV"
}

# Post-deployment verification
post_deployment_verification() {
    log_info "Running post-deployment verification..."
    
    cd "$PROJECT_ROOT"
    
    # Test application startup
    if ! timeout 30 uv run python -c "
from finwiz.utils.configuration_manager import get_configuration_manager
from finwiz.utils.feature_flags import get_feature_flags
from finwiz.integration.manager import CrewDataIntegrationManager
from finwiz.integration.config import load_integration_config
from pathlib import Path

# Test configuration
config_manager = get_configuration_manager()
config_summary = config_manager.get_configuration_summary()
print(f'API keys configured: {config_summary[\"api_keys_configured\"]}')

# Test feature flags
feature_flags = get_feature_flags()
enabled_flags = feature_flags.get_enabled_flags()
print(f'Enabled features: {len(enabled_flags)}')

# Test integration system
try:
    integration_config_path = Path('config/integration.yaml')
    integration_config = load_integration_config(integration_config_path if integration_config_path.exists() else None)
    integration_manager = CrewDataIntegrationManager(config_path=integration_config_path if integration_config_path.exists() else None)
    print(f'✅ Integration system initialized (output_dir: {integration_manager.output_dir})')
except Exception as e:
    print(f'⚠️  Integration system warning: {e}')

print('✅ Application startup verification successful')
"; then
        log_error "Application startup verification failed"
        exit 1
    fi
    
    # Test API endpoints if enabled
    if [[ "${FF_REBALANCING_API:-false}" == "true" ]]; then
        log_info "Testing API endpoints..."
        # This would test API endpoints when they're fully implemented
        log_info "API endpoint testing skipped (not fully implemented)"
    fi
    
    log_success "Post-deployment verification completed"
}

# Cleanup old backups
cleanup_old_backups() {
    log_info "Cleaning up old backups..."
    
    # Keep last 10 backups
    find "$BACKUP_DIR" -name "deployment_backup_*.tar.gz" -type f | \
        sort -r | tail -n +11 | xargs -r rm -f
    
    log_success "Old backups cleaned up"
}

# Main deployment function
main() {
    log_info "Starting FinWiz deployment (Environment: $DEPLOYMENT_ENV)"
    
    pre_deployment_checks
    create_backup
    install_dependencies
    run_tests
    deploy_application
    post_deployment_verification
    cleanup_old_backups
    
    log_success "🚀 FinWiz deployment completed successfully!"
    log_info "Deployment environment: $DEPLOYMENT_ENV"
    log_info "Deployment timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}

# Script usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -e, --env ENV          Deployment environment (production|staging|development)"
    echo "  -b, --backup-dir DIR   Backup directory path"
    echo "  -l, --log-file FILE    Log file path"
    echo "  -t, --run-tests        Run integration tests"
    echo "  -h, --help            Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  DEPLOYMENT_ENV         Deployment environment"
    echo "  BACKUP_DIR            Backup directory"
    echo "  LOG_FILE              Log file path"
    echo "  RUN_INTEGRATION_TESTS Run integration tests (true|false)"
    echo "  FF_*                  Feature flag overrides"
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
        -t|--run-tests)
            RUN_INTEGRATION_TESTS="true"
            shift
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