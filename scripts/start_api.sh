#!/bin/bash

# FinWiz API Server Startup Script
# This script starts the FastAPI server with proper configuration

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
HOST="${FINWIZ_API_HOST:-0.0.0.0}"
PORT="${FINWIZ_API_PORT:-8000}"
WORKERS="${FINWIZ_API_WORKERS:-1}"
LOG_LEVEL="${FINWIZ_LOG_LEVEL:-info}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting FinWiz API Server...${NC}"

# Change to project root
cd "$PROJECT_ROOT"

# Check if FastAPI dependencies are installed
if ! uv run python -c "import fastapi, uvicorn" 2>/dev/null; then
    echo -e "${YELLOW}Installing FastAPI dependencies...${NC}"
    uv add fastapi uvicorn
fi

# Validate configuration
echo -e "${BLUE}Validating configuration...${NC}"
if ! uv run python -c "
from finwiz.utils.configuration_manager import get_configuration_manager
try:
    config_manager = get_configuration_manager()
    config_manager.validate_startup_configuration()
    print('✅ Configuration validation successful')
except Exception as e:
    print(f'❌ Configuration validation failed: {e}')
    exit(1)
"; then
    echo "Configuration validation failed. Please check your .env file."
    exit 1
fi

# Check if rebalancing API is enabled
echo -e "${BLUE}Checking feature flags...${NC}"
API_ENABLED=$(uv run python -c "
from finwiz.utils.feature_flags import is_feature_enabled
print('true' if is_feature_enabled('rebalancing_api') else 'false')
")

if [[ "$API_ENABLED" != "true" ]]; then
    echo -e "${YELLOW}Warning: Rebalancing API is disabled via feature flag${NC}"
    echo -e "${YELLOW}Set FF_REBALANCING_API=true to enable API endpoints${NC}"
fi

# Start the server
echo -e "${GREEN}🚀 Starting FinWiz API Server${NC}"
echo -e "Host: $HOST"
echo -e "Port: $PORT"
echo -e "Workers: $WORKERS"
echo -e "Log Level: $LOG_LEVEL"
echo -e "API Enabled: $API_ENABLED"
echo ""

# Start uvicorn server
exec uv run uvicorn finwiz.api.app:app \
    --host "$HOST" \
    --port "$PORT" \
    --workers "$WORKERS" \
    --log-level "$LOG_LEVEL" \
    --access-log \
    --reload