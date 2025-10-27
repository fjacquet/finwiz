#!/bin/bash
# Integration Fixes Test Script
# Tests the three critical fixes for data consolidation and report generation

# Don't exit on error - we want to run all tests
set +e

echo "=========================================="
echo "Integration Fixes Test Suite"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function to print test results
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ PASSED${NC}: $2"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAILED${NC}: $2"
        ((TESTS_FAILED++))
    fi
}

# Test 1: Verify wrapped data structure helper method exists
echo "Test 1: Verify _wrap_cached_data_for_storage method exists"
if grep -q "_wrap_cached_data_for_storage" src/finwiz/crew_factory.py; then
    print_result 0 "Helper method exists in crew_factory.py"
else
    print_result 1 "Helper method missing from crew_factory.py"
fi
echo ""

# Test 2: Verify crypto crew uses wrapper
echo "Test 2: Verify crypto crew uses data wrapper"
if grep -q "wrapped_cached_data = self._wrap_cached_data_for_storage(cached_data, \"crypto\")" src/finwiz/crew_factory.py; then
    print_result 0 "Crypto crew wraps cached data"
else
    print_result 1 "Crypto crew doesn't wrap cached data"
fi
echo ""

# Test 3: Verify stock crew uses wrapper
echo "Test 3: Verify stock crew uses data wrapper"
if grep -q "wrapped_cached_data = self._wrap_cached_data_for_storage(cached_data, \"stock\")" src/finwiz/crew_factory.py; then
    print_result 0 "Stock crew wraps cached data"
else
    print_result 1 "Stock crew doesn't wrap cached data"
fi
echo ""

# Test 4: Verify ETF crew uses wrapper
echo "Test 4: Verify ETF crew uses data wrapper"
if grep -q "wrapped_cached_data = self._wrap_cached_data_for_storage(cached_data, \"etf\")" src/finwiz/crew_factory.py; then
    print_result 0 "ETF crew wraps cached data"
else
    print_result 1 "ETF crew doesn't wrap cached data"
fi
echo ""

# Test 5: Verify discovery fields are conditional
echo "Test 5: Verify discovery fields are conditional in validator"
if grep -q "discovery_dependent_fields" src/finwiz/utils/report_data_validator.py; then
    print_result 0 "Discovery fields are conditional"
else
    print_result 1 "Discovery fields are not conditional"
fi
echo ""

# Test 6: Verify cache type conversion exists
echo "Test 6: Verify cache type conversion method exists"
if grep -q "_convert_to_crew_analysis_result" src/finwiz/cache/analysis_cache_manager.py; then
    print_result 0 "Cache type conversion method exists"
else
    print_result 1 "Cache type conversion method missing"
fi
echo ""

# Test 7: Verify cache accepts multiple types
echo "Test 7: Verify cache_analysis accepts multiple types"
if grep -q "CrewAnalysisResult | Any" src/finwiz/cache/analysis_cache_manager.py; then
    print_result 0 "Cache accepts multiple types"
else
    print_result 1 "Cache doesn't accept multiple types"
fi
echo ""

# Test 8: Verify linting passes
echo "Test 8: Verify code passes linting"
if ruff check src/finwiz/crew_factory.py src/finwiz/cache/analysis_cache_manager.py src/finwiz/utils/report_data_validator.py --quiet; then
    print_result 0 "All files pass linting"
else
    print_result 1 "Linting errors found"
fi
echo ""

# Test 9: Check for syntax errors
echo "Test 9: Verify Python syntax is valid"
if python3 -m py_compile src/finwiz/crew_factory.py src/finwiz/cache/analysis_cache_manager.py src/finwiz/utils/report_data_validator.py 2>/dev/null; then
    print_result 0 "Python syntax is valid"
else
    print_result 1 "Python syntax errors found"
fi
echo ""

# Test 10: Verify no unittest.mock usage (banned)
echo "Test 10: Verify no unittest.mock usage (banned)"
if grep -r "from unittest.mock import" src/finwiz/crew_factory.py src/finwiz/cache/analysis_cache_manager.py src/finwiz/utils/report_data_validator.py; then
    print_result 1 "unittest.mock found (BANNED)"
else
    print_result 0 "No unittest.mock usage (good)"
fi
echo ""

# Summary
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "Tests Passed: ${GREEN}${TESTS_PASSED}${NC}"
echo -e "Tests Failed: ${RED}${TESTS_FAILED}${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Run full integration test: uv run python src/finwiz/main.py"
    echo "2. Verify report generation succeeds"
    echo "3. Check logs for validation errors"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo ""
    echo "Please review the failed tests above and fix the issues."
    exit 1
fi
