#!/bin/bash

# Unified Agent System - Agent Creation Script
# Creates a new agent from template with guided prompts

set -e

AGENTS_DIR=".claude/agents"
TEMPLATE_FILE="$AGENTS_DIR/templates/agent-template.md"
AGENTS_CONFIG="$AGENTS_DIR/../agents.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() { echo -e "${BLUE}ℹ${NC} $1"; }
log_success() { echo -e "${GREEN}✓${NC} $1"; }
log_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
log_error() { echo -e "${RED}✗${NC} $1"; }

# Check if we're in a project with the unified agent system
check_system() {
    if [[ ! -f "$AGENTS_CONFIG" ]]; then
        log_error "Unified agent system not found. Run this script from a project with .claude/agents.json"
        exit 1
    fi
    
    if [[ ! -f "$TEMPLATE_FILE" ]]; then
        log_error "Agent template not found at $TEMPLATE_FILE"
        exit 1
    fi
}

# Get available categories
get_categories() {
    if command -v jq >/dev/null 2>&1; then
        jq -r '.categories | keys[]' "$AGENTS_CONFIG"
    else
        # Fallback if jq not available
        echo "backend"
        echo "frontend" 
        echo "devops"
        echo "product"
        echo "universal"
        echo "custom"
    fi
}

# Prompt for agent details
prompt_agent_details() {
    echo
    log_info "Creating a new agent for the Unified Agent System"
    echo
    
    # Agent name
    read -p "Agent name (lowercase-with-hyphens): " AGENT_NAME
    if [[ -z "$AGENT_NAME" ]]; then
        log_error "Agent name is required"
        exit 1
    fi
    
    # Validate name format
    if [[ ! "$AGENT_NAME" =~ ^[a-z][a-z0-9-]*[a-z0-9]$ ]]; then
        log_error "Agent name must be lowercase letters, numbers, and hyphens only"
        exit 1
    fi
    
    # Category
    echo
    log_info "Available categories:"
    get_categories | sed 's/^/  - /'
    echo
    read -p "Category: " CATEGORY
    if [[ -z "$CATEGORY" ]]; then
        log_error "Category is required"
        exit 1
    fi
    
    # Role/Title
    read -p "Agent role/title (e.g., 'Senior React Developer'): " AGENT_ROLE
    if [[ -z "$AGENT_ROLE" ]]; then
        log_error "Agent role is required"
        exit 1
    fi
    
    # Domain/Expertise
    read -p "Domain/expertise (e.g., 'React development and modern frontend patterns'): " AGENT_DOMAIN
    if [[ -z "$AGENT_DOMAIN" ]]; then
        log_error "Domain/expertise is required"
        exit 1
    fi
    
    # Description
    echo
    log_info "Enter a brief description of when this agent should be used:"
    read -p "Description: " AGENT_DESCRIPTION
    if [[ -z "$AGENT_DESCRIPTION" ]]; then
        log_error "Description is required"
        exit 1
    fi
    
    # Proactive agent
    echo
    read -p "Should this agent be proactive (auto-trigger in relevant contexts)? [y/N]: " PROACTIVE
    if [[ "$PROACTIVE" =~ ^[Yy]$ ]]; then
        AGENT_PROACTIVE="true"
    else
        AGENT_PROACTIVE="false"
    fi
    
    # Tools
    echo
    log_info "Default tools: Read, Write, Edit, Bash, Grep, Glob, LS"
    read -p "Additional tools (comma-separated, or press Enter for defaults): " ADDITIONAL_TOOLS
    
    if [[ -n "$ADDITIONAL_TOOLS" ]]; then
        AGENT_TOOLS="[Read, Write, Edit, Bash, Grep, Glob, LS, $ADDITIONAL_TOOLS]"
    else
        AGENT_TOOLS="[Read, Write, Edit, Bash, Grep, Glob, LS]"
    fi
}

# Create agent file from template
create_agent_file() {
    local target_dir="$AGENTS_DIR/$CATEGORY"
    local target_file="$target_dir/$AGENT_NAME.md"
    
    # Create category directory if it doesn't exist
    mkdir -p "$target_dir"
    
    # Check if agent already exists
    if [[ -f "$target_file" ]]; then
        read -p "Agent $AGENT_NAME already exists in $CATEGORY. Overwrite? [y/N]: " OVERWRITE
        if [[ ! "$OVERWRITE" =~ ^[Yy]$ ]]; then
            log_info "Agent creation cancelled"
            exit 0
        fi
    fi
    
    # Create agent file from template
    cp "$TEMPLATE_FILE" "$target_file"
    
    # Replace template placeholders
    if command -v sed >/dev/null 2>&1; then
        # Use different sed syntax for macOS vs Linux
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s/template-agent/$AGENT_NAME/g" "$target_file"
            sed -i '' "s/\\[Role\\/Title\\]/$AGENT_ROLE/g" "$target_file"
            sed -i '' "s/\\[domain\\/expertise\\]/$AGENT_DOMAIN/g" "$target_file"
            sed -i '' "s/\\[Brief description of when this agent should be used\\]/$AGENT_DESCRIPTION/g" "$target_file"
            sed -i '' "s/proactive: false/proactive: $AGENT_PROACTIVE/g" "$target_file"
            sed -i '' "s/tools: \\[Read, Write, Edit, Bash, Grep, Glob, LS\\]/tools: $AGENT_TOOLS/g" "$target_file"
        else
            sed -i "s/template-agent/$AGENT_NAME/g" "$target_file"
            sed -i "s/\\[Role\\/Title\\]/$AGENT_ROLE/g" "$target_file"
            sed -i "s/\\[domain\\/expertise\\]/$AGENT_DOMAIN/g" "$target_file"
            sed -i "s/\\[Brief description of when this agent should be used\\]/$AGENT_DESCRIPTION/g" "$target_file"
            sed -i "s/proactive: false/proactive: $AGENT_PROACTIVE/g" "$target_file"
            sed -i "s/tools: \\[Read, Write, Edit, Bash, Grep, Glob, LS\\]/tools: $AGENT_TOOLS/g" "$target_file"
        fi
    fi
    
    log_success "Created agent file: $target_file"
}

# Update agents.json configuration
update_config() {
    log_info "Updating agents.json configuration..."
    
    if command -v jq >/dev/null 2>&1; then
        # Use jq to update the configuration
        local temp_file=$(mktemp)
        jq --arg category "$CATEGORY" --arg agent "$AGENT_NAME" \
           '.categories[$category].agents += [$agent]' \
           "$AGENTS_CONFIG" > "$temp_file"
        mv "$temp_file" "$AGENTS_CONFIG"
        
        # Add to proactive agents if applicable
        if [[ "$AGENT_PROACTIVE" == "true" ]]; then
            temp_file=$(mktemp)
            jq --arg agent "$AGENT_NAME" \
               '.proactive_agents += [$agent]' \
               "$AGENTS_CONFIG" > "$temp_file"
            mv "$temp_file" "$AGENTS_CONFIG"
        fi
        
        log_success "Updated agents.json configuration"
    else
        log_warning "jq not found. Please manually add '$AGENT_NAME' to the '$CATEGORY' category in agents.json"
    fi
}

# Show next steps
show_next_steps() {
    echo
    log_success "Agent '$AGENT_NAME' created successfully!"
    echo
    log_info "Next steps:"
    echo "  1. Edit $AGENTS_DIR/$CATEGORY/$AGENT_NAME.md to customize the agent"
    echo "  2. Fill in the template sections with specific expertise and examples"
    echo "  3. Test the agent with: Claude Code and use 'Use the $AGENT_NAME agent to...'"
    echo "  4. Update the agent based on usage and feedback"
    echo
    log_info "For more information, see the documentation in docs/AGENT_DEVELOPMENT.md"
}

# Main execution
main() {
    check_system
    prompt_agent_details
    create_agent_file
    update_config
    show_next_steps
}

# Run main function
main "$@"