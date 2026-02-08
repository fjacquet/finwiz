#!/bin/bash

# Data Quality Verification Script for FinWiz
# Verifies that crew outputs are properly consumed and not replaced with fallback data

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNINGS=0

# Quality score components
FALLBACK_GRADES=0
PLACEHOLDER_URLS=0
MISSING_DATA=0
TOTAL_HOLDINGS=0

echo "=========================================="
echo "FinWiz Data Quality Verification"
echo "=========================================="
echo ""

# Function to print status
print_status() {
    local status=$1
    local message=$2

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✅ PASS${NC}: $message"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    elif [ "$status" = "FAIL" ]; then
        echo -e "${RED}❌ FAIL${NC}: $message"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    elif [ "$status" = "WARN" ]; then
        echo -e "${YELLOW}⚠️  WARN${NC}: $message"
        WARNINGS=$((WARNINGS + 1))
    else
        echo -e "${BLUE}ℹ️  INFO${NC}: $message"
    fi
}

# Function to check if file exists
check_file_exists() {
    local filepath=$1
    local description=$2

    if [ -f "$filepath" ]; then
        print_status "PASS" "$description exists: $filepath"
        return 0
    else
        print_status "FAIL" "$description not found: $filepath"
        return 1
    fi
}

# Function to check directory has files
check_directory_has_files() {
    local dirpath=$1
    local pattern=$2
    local description=$3

    if [ ! -d "$dirpath" ]; then
        print_status "FAIL" "$description directory not found: $dirpath"
        return 1
    fi

    local file_count=$(find "$dirpath" -name "$pattern" -type f 2>/dev/null | wc -l)

    if [ "$file_count" -gt 0 ]; then
        print_status "PASS" "$description has $file_count file(s)"
        return 0
    else
        print_status "FAIL" "$description has no files matching $pattern"
        return 1
    fi
}

echo "1. Checking Crew Outputs"
echo "----------------------------------------"

# Check for crew output directories and files
check_directory_has_files "output/stock" "stock_output_*.json" "Stock crew output"
check_directory_has_files "output/etf" "etf_output_*.json" "ETF crew output"
check_directory_has_files "output/crypto" "crypto_output_*.json" "Crypto crew output"

# Check for portfolio review
if check_file_exists "output/portfolio/portfolio_review.json" "Portfolio review"; then
    PORTFOLIO_FILE="output/portfolio/portfolio_review.json"
else
    # Try alternative location
    PORTFOLIO_FILE=$(find output/portfolio -name "portfolio_review_*.json" -type f 2>/dev/null | head -n 1)
    if [ -n "$PORTFOLIO_FILE" ]; then
        print_status "PASS" "Portfolio review found: $PORTFOLIO_FILE"
    fi
fi

echo ""
echo "2. Checking Portfolio Review Data Quality"
echo "----------------------------------------"

if [ -n "$PORTFOLIO_FILE" ] && [ -f "$PORTFOLIO_FILE" ]; then
    # Check for fallback Grade D pattern
    # Pattern: "grade": "D", "composite_score": 0.6

    # Count total holdings
    TOTAL_HOLDINGS=$(jq '.portfolio_review.holdings | length' "$PORTFOLIO_FILE" 2>/dev/null || echo "0")

    if [ "$TOTAL_HOLDINGS" -gt 0 ]; then
        print_status "INFO" "Portfolio has $TOTAL_HOLDINGS holdings"

        # Count fallback grades (Grade D with score 0.6)
        FALLBACK_GRADES=$(jq '[.portfolio_review.holdings[] | select(.grade == "D" and .composite_score == 0.6)] | length' "$PORTFOLIO_FILE" 2>/dev/null || echo "0")

        if [ "$FALLBACK_GRADES" -eq 0 ]; then
            print_status "PASS" "No fallback Grade D patterns detected"
        elif [ "$FALLBACK_GRADES" -eq "$TOTAL_HOLDINGS" ]; then
            print_status "FAIL" "ALL holdings have fallback Grade D (actual analysis not used)"
        else
            print_status "WARN" "$FALLBACK_GRADES of $TOTAL_HOLDINGS holdings have fallback Grade D"
        fi

        # Check for "Validation rapide" messages (fallback indicator)
        VALIDATION_RAPIDE=$(jq '[.portfolio_review.holdings[] | select(.rationale_bullets[]? | contains("Validation rapide"))] | length' "$PORTFOLIO_FILE" 2>/dev/null || echo "0")

        if [ "$VALIDATION_RAPIDE" -gt 0 ]; then
            print_status "WARN" "$VALIDATION_RAPIDE holdings have 'Validation rapide' messages (fallback data)"
        fi

        # Check grade distribution
        echo ""
        echo "Grade Distribution:"
        jq -r '.portfolio_review.holdings[] | .grade' "$PORTFOLIO_FILE" 2>/dev/null | sort | uniq -c | while read count grade; do
            echo "  $grade: $count"
        done

    else
        print_status "FAIL" "Portfolio has no holdings"
    fi
else
    print_status "FAIL" "Cannot analyze portfolio review - file not found"
fi

echo ""
echo "3. Checking Report Quality"
echo "----------------------------------------"

# Find the most recent HTML report
REPORT_FILE=$(find output -name "finwiz_*.html" -o -name "*_financial_plan.html" 2>/dev/null | sort -r | head -n 1)

if [ -n "$REPORT_FILE" ] && [ -f "$REPORT_FILE" ]; then
    print_status "PASS" "Report found: $REPORT_FILE"

    # Check for example.com placeholder URLs
    PLACEHOLDER_URLS=$(grep -c "example\.com" "$REPORT_FILE" 2>/dev/null || echo "0")

    if [ "$PLACEHOLDER_URLS" -eq 0 ]; then
        print_status "PASS" "No example.com placeholder URLs found"
    else
        print_status "FAIL" "Found $PLACEHOLDER_URLS example.com placeholder URLs"
    fi

    # Check for "NOT PROVIDED" messages
    NOT_PROVIDED=$(grep -c "NOT PROVIDED" "$REPORT_FILE" 2>/dev/null || echo "0")

    if [ "$NOT_PROVIDED" -eq 0 ]; then
        print_status "PASS" "No 'NOT PROVIDED' messages found"
    else
        print_status "FAIL" "Found $NOT_PROVIDED 'NOT PROVIDED' messages"
    fi

    # Check for "aucune alternative fournie" (no alternatives provided)
    NO_ALTERNATIVES=$(grep -ci "aucune alternative fournie" "$REPORT_FILE" 2>/dev/null || echo "0")

    if [ "$NO_ALTERNATIVES" -eq 0 ]; then
        print_status "PASS" "No 'aucune alternative fournie' messages found"
    else
        print_status "WARN" "Found $NO_ALTERNATIVES 'aucune alternative fournie' messages"
    fi

else
    print_status "FAIL" "HTML report not found"
fi

echo ""
echo "4. Checking Data Quality Metrics"
echo "----------------------------------------"

# Find the most recent data quality metrics file
METRICS_FILE=$(find .finwiz/metrics -name "data_quality_metrics_*.json" 2>/dev/null | sort -r | head -n 1)

if [ -n "$METRICS_FILE" ] && [ -f "$METRICS_FILE" ]; then
    print_status "PASS" "Data quality metrics found: $METRICS_FILE"

    # Extract quality score
    QUALITY_SCORE=$(jq -r '.quality_score' "$METRICS_FILE" 2>/dev/null || echo "0")
    QUALITY_GRADE=$(jq -r '.quality_grade' "$METRICS_FILE" 2>/dev/null || echo "F")

    echo ""
    echo "Quality Metrics:"
    echo "  Score: $QUALITY_SCORE"
    echo "  Grade: $QUALITY_GRADE"

    # Extract individual metrics
    METRICS_FALLBACK=$(jq -r '.metrics.fallback_grades' "$METRICS_FILE" 2>/dev/null || echo "0")
    METRICS_PLACEHOLDER=$(jq -r '.metrics.placeholder_urls' "$METRICS_FILE" 2>/dev/null || echo "0")
    METRICS_MISSING=$(jq -r '.metrics.missing_data' "$METRICS_FILE" 2>/dev/null || echo "0")
    METRICS_SUCCESS=$(jq -r '.metrics.successful_merges' "$METRICS_FILE" 2>/dev/null || echo "0")
    METRICS_FAILED=$(jq -r '.metrics.failed_merges' "$METRICS_FILE" 2>/dev/null || echo "0")

    echo "  Fallback Grades: $METRICS_FALLBACK"
    echo "  Placeholder URLs: $METRICS_PLACEHOLDER"
    echo "  Missing Data: $METRICS_MISSING"
    echo "  Successful Merges: $METRICS_SUCCESS"
    echo "  Failed Merges: $METRICS_FAILED"

    # Update counters for final score calculation
    FALLBACK_GRADES=$METRICS_FALLBACK
    PLACEHOLDER_URLS=$METRICS_PLACEHOLDER
    MISSING_DATA=$METRICS_MISSING

else
    print_status "WARN" "Data quality metrics file not found (may not have been exported)"
fi

echo ""
echo "=========================================="
echo "Data Quality Summary"
echo "=========================================="

# Calculate overall quality score
# Start with 1.0, subtract penalties
QUALITY_SCORE=1.0

if [ "$TOTAL_HOLDINGS" -gt 0 ]; then
    # Penalty for fallback grades (each reduces score by 0.1)
    FALLBACK_PENALTY=$(echo "scale=2; $FALLBACK_GRADES * 0.1" | bc)
    QUALITY_SCORE=$(echo "scale=2; $QUALITY_SCORE - $FALLBACK_PENALTY" | bc)

    # Penalty for placeholder URLs (each reduces score by 0.05)
    PLACEHOLDER_PENALTY=$(echo "scale=2; $PLACEHOLDER_URLS * 0.05" | bc)
    QUALITY_SCORE=$(echo "scale=2; $QUALITY_SCORE - $PLACEHOLDER_PENALTY" | bc)

    # Penalty for missing data (each reduces score by 0.05)
    MISSING_PENALTY=$(echo "scale=2; $MISSING_DATA * 0.05" | bc)
    QUALITY_SCORE=$(echo "scale=2; $QUALITY_SCORE - $MISSING_PENALTY" | bc)

    # Ensure score doesn't go below 0
    QUALITY_SCORE=$(echo "if ($QUALITY_SCORE < 0) 0 else $QUALITY_SCORE" | bc)
fi

echo ""
echo "Quality Score: $QUALITY_SCORE"
echo ""
echo "Test Results:"
echo "  Total Checks: $TOTAL_CHECKS"
echo "  Passed: $PASSED_CHECKS"
echo "  Failed: $FAILED_CHECKS"
echo "  Warnings: $WARNINGS"
echo ""

# Determine overall status
if [ "$FAILED_CHECKS" -eq 0 ]; then
    if [ "$WARNINGS" -eq 0 ]; then
        echo -e "${GREEN}✅ ALL CHECKS PASSED${NC}"
        echo ""
        echo "Data quality is excellent. All crew outputs are being properly consumed."
        exit 0
    else
        echo -e "${YELLOW}⚠️  CHECKS PASSED WITH WARNINGS${NC}"
        echo ""
        echo "Data quality is acceptable but has some issues. Review warnings above."
        exit 0
    fi
else
    echo -e "${RED}❌ QUALITY CHECKS FAILED${NC}"
    echo ""
    echo "Data quality issues detected. Crew outputs may not be properly consumed."
    echo ""
    echo "Common issues:"
    echo "  - Fallback Grade D: Deep analysis not merged into portfolio"
    echo "  - Placeholder URLs: Real URLs not retrieved from tools"
    echo "  - NOT PROVIDED: Data availability not properly reported"
    echo ""
    echo "Review the failed checks above and investigate data flow."
    exit 1
fi
