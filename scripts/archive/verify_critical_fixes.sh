#!/bin/bash
# Verify Critical Fixes Script

echo "=========================================="
echo "Verifying Critical Fixes"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Test 1: Verify form_type is in flow_orchestrator
echo "Test 1: Verify form_type added to crew inputs"
if grep -q '"form_type": "10-K"' src/finwiz/flows/flow_orchestrator.py; then
    echo -e "${GREEN}✅ PASS${NC}: form_type variable added"
else
    echo -e "${RED}❌ FAIL${NC}: form_type variable missing"
    exit 1
fi
echo ""

# Test 2: Verify os.getenv is used instead of config_manager.get_setting
echo "Test 2: Verify os.getenv replaces config_manager.get_setting"
if grep -q "os.getenv" src/finwiz/monitoring/alerting.py && ! grep -q "config_manager.get_setting" src/finwiz/monitoring/alerting.py; then
    echo -e "${GREEN}✅ PASS${NC}: Using os.getenv correctly"
else
    echo -e "${RED}❌ FAIL${NC}: Still using config_manager.get_setting or os.getenv missing"
    exit 1
fi
echo ""

# Test 3: Verify os is imported
echo "Test 3: Verify os module is imported"
if grep -q "^import os$" src/finwiz/monitoring/alerting.py; then
    echo -e "${GREEN}✅ PASS${NC}: os module imported"
else
    echo -e "${RED}❌ FAIL${NC}: os module not imported"
    exit 1
fi
echo ""

# Test 4: Verify linting passes
echo "Test 4: Verify code passes linting"
if ruff check src/finwiz/flows/flow_orchestrator.py src/finwiz/monitoring/alerting.py --quiet; then
    echo -e "${GREEN}✅ PASS${NC}: All files pass linting"
else
    echo -e "${RED}❌ FAIL${NC}: Linting errors found"
    exit 1
fi
echo ""

# Test 5: Verify Python syntax
echo "Test 5: Verify Python syntax is valid"
if python3 -m py_compile src/finwiz/flows/flow_orchestrator.py src/finwiz/monitoring/alerting.py 2>/dev/null; then
    echo -e "${GREEN}✅ PASS${NC}: Python syntax is valid"
else
    echo -e "${RED}❌ FAIL${NC}: Python syntax errors found"
    exit 1
fi
echo ""

echo "=========================================="
echo -e "${GREEN}✅ ALL CRITICAL FIXES VERIFIED${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Run the flow: uv run python src/finwiz/main.py"
echo "2. Monitor for deep analysis success"
echo "3. Verify report generation"
echo ""
echo "Expected results:"
echo "- Deep analysis should complete for all 5 holdings"
echo "- No 'form_type' errors"
echo "- No 'get_setting' errors"
echo "- Report should be generated successfully"
