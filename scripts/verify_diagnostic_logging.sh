#!/bin/bash

# Verification script for Task 1: Diagnostic Logging
# This script checks that diagnostic logging is properly implemented

echo "=========================================="
echo "Task 1: Diagnostic Logging Verification"
echo "=========================================="
echo ""

# Check if the diagnostic logging code exists
echo "1. Checking for diagnostic logging implementation..."

if grep -q "DIAGNOSTIC: Portfolio Holdings BEFORE Deep Analysis Merge" src/finwiz/flows/flow_orchestrator.py; then
    echo "   ✅ Pre-merge diagnostic logging found"
else
    echo "   ❌ Pre-merge diagnostic logging NOT found"
    exit 1
fi

if grep -q "DIAGNOSTIC: Deep Analysis Results Available" src/finwiz/flows/flow_orchestrator.py; then
    echo "   ✅ Deep analysis results logging found"
else
    echo "   ❌ Deep analysis results logging NOT found"
    exit 1
fi

if grep -q "DIAGNOSTIC: Portfolio Holdings AFTER Deep Analysis Merge" src/finwiz/flows/flow_orchestrator.py; then
    echo "   ✅ Post-merge diagnostic logging found"
else
    echo "   ❌ Post-merge diagnostic logging NOT found"
    exit 1
fi

if grep -q "DATA LINEAGE" src/finwiz/flows/flow_orchestrator.py; then
    echo "   ✅ Data lineage tracking found"
else
    echo "   ❌ Data lineage tracking NOT found"
    exit 1
fi

echo ""
echo "2. Checking for fallback data detection..."

if grep -q "FALLBACK DATA DETECTED" src/finwiz/flows/flow_orchestrator.py; then
    echo "   ✅ Fallback data detection implemented"
else
    echo "   ❌ Fallback data detection NOT found"
    exit 1
fi

if grep -q "MERGE VERIFICATION PASSED" src/finwiz/flows/flow_orchestrator.py; then
    echo "   ✅ Merge verification implemented"
else
    echo "   ❌ Merge verification NOT found"
    exit 1
fi

echo ""
echo "3. Checking for visual indicators..."

if grep -q "✅" src/finwiz/flows/flow_orchestrator.py; then
    echo "   ✅ Success indicators found"
else
    echo "   ❌ Success indicators NOT found"
    exit 1
fi

if grep -q "❌" src/finwiz/flows/flow_orchestrator.py; then
    echo "   ✅ Error indicators found"
else
    echo "   ❌ Error indicators NOT found"
    exit 1
fi

if grep -q "⚠️" src/finwiz/flows/flow_orchestrator.py; then
    echo "   ✅ Warning indicators found"
else
    echo "   ❌ Warning indicators NOT found"
    exit 1
fi

echo ""
echo "4. Checking code quality..."

# Run ruff check
if ruff check src/finwiz/flows/flow_orchestrator.py > /dev/null 2>&1; then
    echo "   ✅ Code passes ruff checks"
else
    echo "   ⚠️  Code has ruff warnings (non-critical)"
fi

# Check for syntax errors
if python -m py_compile src/finwiz/flows/flow_orchestrator.py 2>/dev/null; then
    echo "   ✅ No syntax errors"
else
    echo "   ❌ Syntax errors found"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ All diagnostic logging checks passed!"
echo "=========================================="
echo ""
echo "To see the diagnostic logging in action:"
echo "  1. export DEEP_PORTFOLIO_ANALYSIS=true"
echo "  2. uv run python src/finwiz/main.py"
echo "  3. grep 'DIAGNOSTIC:' logs/finwiz.log"
echo "  4. grep 'DATA LINEAGE:' logs/finwiz.log"
echo ""
