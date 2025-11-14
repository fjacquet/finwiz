#!/usr/bin/env python3
"""
Verify HTML Reports Have Data.

This script checks that generated HTML files contain actual data,
not just empty templates.
"""

import re
import sys
from pathlib import Path


def verify_html_file(html_path: Path) -> dict:
    """
    Verify an HTML file contains actual data.
    
    Returns dict with verification results.
    """
    try:
        content = html_path.read_text(encoding="utf-8")
        
        # Check file size (empty templates are usually < 10KB)
        file_size = len(content)
        
        # Look for common data indicators
        has_ticker_data = bool(re.search(r'<td[^>]*>[A-Z]{2,5}(?:\.[A-Z]{1,2})?</td>', content))
        has_ticker_in_title = bool(re.search(r'<h1[^>]*>[^<]*[A-Z]{2,5}(?:\.[A-Z]{1,2})?', content))
        has_numeric_data = bool(re.search(r'<div class="metric-value">\d+', content))
        has_grade_data = bool(re.search(r'grade-[a-z]|Grade [A-F]', content))
        has_score_data = bool(re.search(r'\d+\.\d{2,3}', content))
        has_recommendation = bool(re.search(r'BUY|SELL|HOLD', content))
        
        # Count data rows in tables
        table_rows = len(re.findall(r'<tr[^>]*>(?!.*<th)', content))
        
        # Consider file has data if it has any of these indicators
        has_data = (has_ticker_data or has_ticker_in_title or has_numeric_data or 
                   (has_grade_data and has_score_data) or has_recommendation)
        
        return {
            "path": str(html_path),
            "file_size": file_size,
            "has_data": has_data,
            "has_ticker_data": has_ticker_data or has_ticker_in_title,
            "has_numeric_data": has_numeric_data,
            "has_grade_data": has_grade_data,
            "has_score_data": has_score_data,
            "has_recommendation": has_recommendation,
            "table_rows": table_rows,
            "status": "✅ PASS" if has_data else "❌ FAIL"
        }
    except Exception as e:
        return {
            "path": str(html_path),
            "status": f"❌ ERROR: {e}",
            "has_data": False
        }


def main():
    """Main verification function."""
    output_dir = Path("output")
    
    if not output_dir.exists():
        print("❌ Output directory not found")
        sys.exit(1)
    
    # Find all HTML files
    html_files = list(output_dir.rglob("*.html"))
    
    if not html_files:
        print("❌ No HTML files found")
        sys.exit(1)
    
    print(f"\n🔍 Verifying {len(html_files)} HTML files...\n")
    print("=" * 80)
    
    results = []
    for html_file in sorted(html_files):
        result = verify_html_file(html_file)
        results.append(result)
    
    # Group by status
    passed = [r for r in results if r.get("has_data", False)]
    failed = [r for r in results if not r.get("has_data", False)]
    
    # Print summary
    print(f"\n📊 Verification Summary")
    print("=" * 80)
    print(f"Total files: {len(results)}")
    print(f"✅ Passed: {len(passed)}")
    print(f"❌ Failed: {len(failed)}")
    print("=" * 80)
    
    # Show sample of passed files
    if passed:
        print(f"\n✅ Sample of files with data (showing first 10):")
        for result in passed[:10]:
            file_name = Path(result["path"]).name
            print(f"   {file_name}")
            print(f"      Size: {result['file_size']:,} bytes")
            print(f"      Tickers: {'Yes' if result.get('has_ticker_data') else 'No'}")
            print(f"      Metrics: {'Yes' if result.get('has_numeric_data') else 'No'}")
            print(f"      Grades: {'Yes' if result.get('has_grade_data') else 'No'}")
            print(f"      Table rows: {result.get('table_rows', 0)}")
            print()
    
    # Show failed files
    if failed:
        print(f"\n❌ Files without data:")
        for result in failed:
            file_name = Path(result["path"]).name
            print(f"   {file_name}")
    
    # Detailed examples
    print(f"\n📋 Detailed Examples:")
    print("=" * 80)
    
    # Portfolio review
    portfolio_html = output_dir / "portfolio" / "portfolio_review.html"
    if portfolio_html.exists():
        result = verify_html_file(portfolio_html)
        print(f"\n📁 Portfolio Review:")
        print(f"   File: {portfolio_html.name}")
        print(f"   Size: {result['file_size']:,} bytes")
        print(f"   Status: {result['status']}")
        print(f"   Has ticker data: {result.get('has_ticker_data', False)}")
        print(f"   Has numeric data: {result.get('has_numeric_data', False)}")
        print(f"   Table rows: {result.get('table_rows', 0)}")
    
    # Backtesting results
    backtesting_html = output_dir / "backtesting_results_default.html"
    if backtesting_html.exists():
        result = verify_html_file(backtesting_html)
        print(f"\n📊 Backtesting Results:")
        print(f"   File: {backtesting_html.name}")
        print(f"   Size: {result['file_size']:,} bytes")
        print(f"   Status: {result['status']}")
        print(f"   Has ticker data: {result.get('has_ticker_data', False)}")
        print(f"   Has numeric data: {result.get('has_numeric_data', False)}")
        print(f"   Table rows: {result.get('table_rows', 0)}")
    
    # Sample stock analysis
    stock_files = list((output_dir / "stock").glob("*.html"))
    if stock_files:
        sample_stock = stock_files[0]
        result = verify_html_file(sample_stock)
        print(f"\n📈 Sample Stock Analysis:")
        print(f"   File: {sample_stock.name}")
        print(f"   Size: {result['file_size']:,} bytes")
        print(f"   Status: {result['status']}")
        print(f"   Has ticker data: {result.get('has_ticker_data', False)}")
        print(f"   Has grade data: {result.get('has_grade_data', False)}")
        print(f"   Has score data: {result.get('has_score_data', False)}")
    
    print("\n" + "=" * 80)
    print(f"\n💡 Tip: Open any HTML file in your browser to view the full report")
    print(f"   Example: open {portfolio_html if portfolio_html.exists() else 'output/portfolio/portfolio_review.html'}")
    
    # Exit with appropriate code
    sys.exit(0 if not failed else 1)


if __name__ == "__main__":
    main()
