#!/bin/bash
# Check for Jekyll/Liquid syntax errors in documentation
# This script finds Jinja2 template syntax that isn't properly wrapped with {% raw %} tags

set -e

echo "🔍 Checking for Jekyll/Liquid syntax errors in documentation..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

errors_found=0

# Function to check if a Jinja2 tag is properly wrapped
check_file() {
    local file="$1"
    local temp_file=$(mktemp)
    
    # Extract all Jinja2 tags and their line numbers
    grep -n '{%\|{{' "$file" > "$temp_file" 2>/dev/null || true
    
    if [ ! -s "$temp_file" ]; then
        rm "$temp_file"
        return 0
    fi
    
    local in_raw_block=false
    local in_code_block=false
    local file_has_errors=false
    
    while IFS=: read -r line_num line_content; do
        # Check if we're entering/exiting a raw block
        if echo "$line_content" | grep -q '{% *raw *%}\|{%raw%}'; then
            in_raw_block=true
            continue
        fi
        if echo "$line_content" | grep -q '{% *endraw *%}\|{%endraw%}'; then
            in_raw_block=false
            continue
        fi
        
        # Check if we're in a code block (simplified check)
        if echo "$line_content" | grep -q '```'; then
            if [ "$in_code_block" = true ]; then
                in_code_block=false
            else
                in_code_block=true
            fi
        fi
        
        # If we find Jinja2 syntax outside raw blocks, it's an error
        if [ "$in_raw_block" = false ] && [ "$in_code_block" = true ]; then
            if echo "$line_content" | grep -qE '{%[^}]*%}|{{[^}]*}}'; then
                # Ignore {% raw %} and {% endraw %} themselves
                if ! echo "$line_content" | grep -qE '{% *(end)?raw *%}'; then
                    if [ "$file_has_errors" = false ]; then
                        echo -e "${RED}❌ $file${NC}"
                        file_has_errors=true
                        errors_found=$((errors_found + 1))
                    fi
                    echo -e "   Line $line_num: ${YELLOW}$(echo "$line_content" | sed 's/^[[:space:]]*//')${NC}"
                fi
            fi
        fi
    done < "$temp_file"
    
    rm "$temp_file"
    
    if [ "$file_has_errors" = true ]; then
        echo ""
    fi
}

# Check all markdown files in docs/
echo "Scanning markdown files in docs/..."
echo ""

while IFS= read -r -d '' file; do
    check_file "$file"
done < <(find docs -name "*.md" -type f -print0)

echo ""
if [ $errors_found -eq 0 ]; then
    echo -e "${GREEN}✅ No Jekyll/Liquid syntax errors found!${NC}"
    exit 0
else
    echo -e "${RED}❌ Found Jekyll/Liquid syntax errors in $errors_found file(s)${NC}"
    echo ""
    echo "To fix these errors:"
    echo "1. Wrap Jinja2 template code blocks with {% raw %} and {% endraw %} tags"
    echo "2. Example:"
    echo "   {% raw %}"
    echo "   \`\`\`html"
    echo "   {% extends \"base.html\" %}"
    echo "   {% block content %}...{% endblock %}"
    echo "   \`\`\`"
    echo "   {% endraw %}"
    exit 1
fi
