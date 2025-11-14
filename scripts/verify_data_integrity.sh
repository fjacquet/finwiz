#!/bin/bash
# Verification script to check data integrity across JSON files, portfolio review, and HTML report

echo "🔍 FinWiz Data Integrity Verification"
echo "======================================"
echo ""

# Check if output files exist
if [ ! -f "output/stock/AAPL_default.json" ]; then
    echo "❌ ERROR: output/stock/AAPL_default.json not found"
    echo "   Run the analysis first!"
    exit 1
fi

echo "📊 Checking AAPL (Apple) as test case..."
echo ""

# Extract data from JSON file
echo "1️⃣  JSON File (output/stock/AAPL_default.json):"
JSON_SCORE=$(cat output/stock/AAPL_default.json | grep '"composite_score"' | head -1 | sed 's/.*: \([0-9.]*\).*/\1/')
JSON_GRADE=$(cat output/stock/AAPL_default.json | grep '"grade"' | head -1 | sed 's/.*: "\([^"]*\)".*/\1/')
JSON_REC=$(cat output/stock/AAPL_default.json | grep '"recommendation"' | head -1 | sed 's/.*: "\([^"]*\)".*/\1/')
echo "   Score: $JSON_SCORE"
echo "   Grade: $JSON_GRADE"
echo "   Recommendation: $JSON_REC"
echo ""

# Extract data from portfolio review
echo "2️⃣  Portfolio Review (output/portfolio/portfolio_review.json):"
if [ -f "output/portfolio/portfolio_review.json" ]; then
    PORTFOLIO_SCORE=$(cat output/portfolio/portfolio_review.json | grep -A20 '"ticker": "AAPL"' | grep '"composite_score"' | head -1 | sed 's/.*: \([0-9.]*\).*/\1/')
    PORTFOLIO_GRADE=$(cat output/portfolio/portfolio_review.json | grep -A20 '"ticker": "AAPL"' | grep '"grade"' | head -1 | sed 's/.*: "\([^"]*\)".*/\1/')
    echo "   Score: $PORTFOLIO_SCORE"
    echo "   Grade: $PORTFOLIO_GRADE"
else
    echo "   ⚠️  File not found"
    PORTFOLIO_SCORE="N/A"
    PORTFOLIO_GRADE="N/A"
fi
echo ""

# Extract data from HTML report
echo "3️⃣  HTML Report (output/finwiz_family_financial_plan.html):"
if [ -f "output/finwiz_family_financial_plan.html" ]; then
    HTML_GRADE=$(grep -A3 "AAPL" output/finwiz_family_financial_plan.html | grep "grade-" | sed 's/.*grade-\([a-z-]*\).*/\1/' | head -1)
    HTML_SCORE=$(grep -A5 "AAPL" output/finwiz_family_financial_plan.html | grep "<td>[0-9]" | sed 's/.*<td>\([0-9.]*\)<.*/\1/' | head -1)
    echo "   Score: $HTML_SCORE"
    echo "   Grade: $HTML_GRADE"
else
    echo "   ⚠️  File not found"
    HTML_SCORE="N/A"
    HTML_GRADE="N/A"
fi
echo ""

# Compare values
echo "🔬 Verification Results:"
echo "========================"
echo ""

PASS=true

# Check scores match
if [ "$JSON_SCORE" = "$PORTFOLIO_SCORE" ] && [ "$JSON_SCORE" = "$HTML_SCORE" ]; then
    echo "✅ PASS: All scores match ($JSON_SCORE)"
else
    echo "❌ FAIL: Scores don't match!"
    echo "   JSON: $JSON_SCORE"
    echo "   Portfolio: $PORTFOLIO_SCORE"
    echo "   HTML: $HTML_SCORE"
    PASS=false
fi

# Check grades match (normalize HTML grade format)
HTML_GRADE_NORMALIZED=$(echo "$HTML_GRADE" | tr 'a-z-' 'A-Z+')
if [ "$JSON_GRADE" = "$PORTFOLIO_GRADE" ] && [ "$JSON_GRADE" = "$HTML_GRADE_NORMALIZED" ]; then
    echo "✅ PASS: All grades match ($JSON_GRADE)"
else
    echo "❌ FAIL: Grades don't match!"
    echo "   JSON: $JSON_GRADE"
    echo "   Portfolio: $PORTFOLIO_GRADE"
    echo "   HTML: $HTML_GRADE_NORMALIZED"
    PASS=false
fi

echo ""

if [ "$PASS" = true ]; then
    echo "🎉 SUCCESS: Data integrity verified!"
    echo "   All sources show consistent data."
    exit 0
else
    echo "⚠️  WARNING: Data integrity issues detected!"
    echo "   JSON files don't match portfolio review or HTML report."
    echo ""
    echo "💡 Possible causes:"
    echo "   1. Report generated before deep analysis completed"
    echo "   2. Using in-memory state instead of JSON files"
    echo "   3. Merge logic not applied correctly"
    echo ""
    echo "🔧 Solution: Re-run the analysis to regenerate all files"
    exit 1
fi
