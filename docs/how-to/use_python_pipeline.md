# How to Use the Pure Python Pipeline

## Overview

This guide shows you how to use the Pure Python Pipeline for fast, deterministic portfolio analysis with zero LLM costs.

## Prerequisites

- FinWiz installed and configured
- Portfolio holdings data (CSV or HoldingDecision objects)
- Python 3.12+

## Basic Usage

### Step 1: Prepare Portfolio Holdings

Create a list of `HoldingDecision` objects:

```python
from finwiz.schemas.portfolio_review import HoldingDecision
from finwiz.schemas.common import RiskAssessmentStandardized

holdings = [
    HoldingDecision(
        ticker="AAPL",
        name="Apple Inc.",
        asset_class="stock",
        currency="USD",
        decision="KEEP",
        composite_score=0.75,
        grade="B",
        grade_description="Grade B - Good quality stock",
        recommended_action="HOLD",
        rationale_bullets=["Strong fundamentals", "Market leader"],
        risk=RiskAssessmentStandardized(
            score=2.5,
            level="Medium",
            risk_factors=["Market volatility", "Competition"]
        ),
        alternatives=[]
    ),
    # Add more holdings...
]
```

### Step 2: Run Deep Analysis

Execute deep analysis using pure Python:

```python
from finwiz.scoring.portfolio_deep_analyzer import analyze_portfolio_with_python
import time

# Generate unique session ID
session_id = f"analysis_{int(time.time())}"

# Run deep analysis
analysis_results = analyze_portfolio_with_python(
    holdings=holdings,
    session_id=session_id
)

# Check results
print(f"✅ Analyzed {analysis_results['successful_analyses']} holdings")
print(f"❌ Failed {analysis_results['failed_analyses']} holdings")
print(f"⚡ Execution time: {analysis_results['performance_metrics']['total_execution_time_seconds']:.2f}s")
```

### Step 3: Discover A+ Opportunities

Identify A+ and A grade holdings:

```python
from finwiz.integration.aplus_discovery_integrator import integrate_aplus_discovery_with_deep_analysis

# Run A+ discovery
discovery_results = integrate_aplus_discovery_with_deep_analysis(
    session_id=session_id
)

# Check results
if discovery_results["has_a_plus_analysis"]:
    print(f"🎯 Found {discovery_results['total_opportunities_found']} A+ opportunities")
    for holding in discovery_results["aplus_holdings"]:
        print(f"  - {holding['ticker']}: Grade {holding['grade']} (Score: {holding['composite_score']:.3f})")
else:
    print("ℹ️ No A+ opportunities found")
```

### Step 4: Execute Backtesting

Run backtesting for A+ candidates:

```python
from finwiz.integration.backtesting_pipeline_connector import connect_backtesting_to_discovery_results

# Run backtesting
backtesting_results = connect_backtesting_to_discovery_results(
    session_id=session_id
)

# Check results
if backtesting_results["backtesting_executed"]:
    print(f"🔬 Backtested {backtesting_results['candidates_count']} candidates")
    for result in backtesting_results["results"]:
        print(f"  {result['ticker']}: {result['annual_return']:.1%} return, "
              f"Sharpe {result['sharpe_ratio']:.2f}, "
              f"Max DD {result['max_drawdown']:.1%}")
else:
    print(f"ℹ️ Backtesting not executed: {backtesting_results.get('reason', 'Unknown')}")
```

### Step 5: Generate Report

Create comprehensive HTML report:

```python
from finwiz.reporting.python_report_generator import generate_python_report
from finwiz.schemas.portfolio_review import PortfolioReview
from datetime import datetime

# Create portfolio review
portfolio_review = PortfolioReview(
    as_of=datetime.now(),
    base_currency="USD",
    holdings=holdings
)

# Generate report
report_path = generate_python_report(
    portfolio_review=portfolio_review,
    deep_analysis_results=analysis_results,
    session_id=session_id
)

print(f"📊 Report generated: {report_path}")
```

## Complete Example

Here's a complete example that runs the entire pipeline:

```python
from finwiz.schemas.portfolio_review import HoldingDecision, PortfolioReview
from finwiz.schemas.common import RiskAssessmentStandardized
from finwiz.scoring.portfolio_deep_analyzer import analyze_portfolio_with_python
from finwiz.integration.aplus_discovery_integrator import integrate_aplus_discovery_with_deep_analysis
from finwiz.integration.backtesting_pipeline_connector import connect_backtesting_to_discovery_results
from finwiz.reporting.python_report_generator import generate_python_report
from datetime import datetime
import time

# Step 1: Prepare holdings
holdings = [
    HoldingDecision(
        ticker="NVDA",
        name="NVIDIA Corporation",
        asset_class="stock",
        currency="USD",
        decision="KEEP",
        composite_score=0.85,
        grade="A",
        grade_description="Grade A - Excellent AI leader",
        recommended_action="BUY",
        rationale_bullets=["AI market leader", "Strong growth"],
        risk=RiskAssessmentStandardized(score=2.8, level="Medium", risk_factors=["Tech volatility"]),
        alternatives=[]
    ),
    HoldingDecision(
        ticker="TSLA",
        name="Tesla Inc.",
        asset_class="stock",
        currency="USD",
        decision="KEEP",
        composite_score=0.82,
        grade="A",
        grade_description="Grade A - EV innovation leader",
        recommended_action="BUY",
        rationale_bullets=["EV market leader", "Innovation"],
        risk=RiskAssessmentStandardized(score=3.2, level="High", risk_factors=["Volatility"]),
        alternatives=[]
    ),
]

# Step 2: Generate session ID
session_id = f"pipeline_demo_{int(time.time())}"

# Step 3: Run pipeline
print("🚀 Starting Pure Python Pipeline")
print("=" * 60)

# Deep Analysis
print("\n1️⃣ Running deep analysis...")
analysis_results = analyze_portfolio_with_python(
    holdings=holdings,
    session_id=session_id
)
print(f"   ✅ Analyzed {analysis_results['successful_analyses']} holdings in "
      f"{analysis_results['performance_metrics']['total_execution_time_seconds']:.2f}s")

# A+ Discovery
print("\n2️⃣ Running A+ discovery...")
discovery_results = integrate_aplus_discovery_with_deep_analysis(
    session_id=session_id
)
print(f"   ✅ Found {discovery_results['total_opportunities_found']} A+ opportunities")

# Backtesting
print("\n3️⃣ Running backtesting...")
backtesting_results = connect_backtesting_to_discovery_results(
    session_id=session_id
)
if backtesting_results["backtesting_executed"]:
    print(f"   ✅ Backtested {backtesting_results['candidates_count']} candidates")
else:
    print(f"   ℹ️ Backtesting not executed: {backtesting_results.get('reason')}")

# Report Generation
print("\n4️⃣ Generating report...")
portfolio_review = PortfolioReview(
    as_of=datetime.now(),
    base_currency="USD",
    holdings=holdings
)
report_path = generate_python_report(
    portfolio_review=portfolio_review,
    deep_analysis_results=analysis_results,
    session_id=session_id
)
print(f"   ✅ Report generated: {report_path}")

print("\n" + "=" * 60)
print("✅ Pipeline completed successfully!")
print(f"📊 Total execution time: {analysis_results['performance_metrics']['total_execution_time_seconds']:.2f}s")
print(f"💰 Total cost: $0.00 (0 LLM calls)")
```

## Advanced Usage

### Custom Session IDs

Use meaningful session IDs for better organization:

```python
from datetime import datetime

# Date-based session ID
session_id = f"portfolio_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# User-based session ID
session_id = f"user_john_doe_{int(time.time())}"

# Portfolio-based session ID
session_id = f"retirement_portfolio_{int(time.time())}"
```

### Error Handling

Implement robust error handling:

```python
import logging

logger = logging.getLogger(__name__)

try:
    # Deep Analysis
    analysis_results = analyze_portfolio_with_python(
        holdings=holdings,
        session_id=session_id
    )

    if analysis_results["successful_analyses"] == 0:
        logger.warning("No holdings analyzed successfully")
        # Handle gracefully

except Exception as e:
    logger.error(f"Deep analysis failed: {e}", exc_info=True)
    # Implement fallback strategy
    analysis_results = {
        "successful_analyses": 0,
        "failed_analyses": len(holdings),
        "deep_analysis_results": {}
    }

# Continue with remaining pipeline steps...
```

### Conditional Execution

Execute components conditionally:

```python
# Always run deep analysis
analysis_results = analyze_portfolio_with_python(
    holdings=holdings,
    session_id=session_id
)

# Only run discovery if analysis succeeded
if analysis_results["successful_analyses"] > 0:
    discovery_results = integrate_aplus_discovery_with_deep_analysis(
        session_id=session_id
    )

    # Only run backtesting if A+ opportunities found
    if discovery_results["has_a_plus_analysis"]:
        backtesting_results = connect_backtesting_to_discovery_results(
            session_id=session_id
        )
    else:
        print("ℹ️ No A+ opportunities - skipping backtesting")
        backtesting_results = {"backtesting_executed": False}
else:
    print("❌ Deep analysis failed - skipping discovery and backtesting")
    discovery_results = {"has_a_plus_analysis": False}
    backtesting_results = {"backtesting_executed": False}

# Always generate report (even with partial data)
report_path = generate_python_report(
    portfolio_review=portfolio_review,
    deep_analysis_results=analysis_results,
    session_id=session_id
)
```

### Performance Monitoring

Track pipeline performance:

```python
import time

start_time = time.time()

# Run pipeline
analysis_results = analyze_portfolio_with_python(holdings, session_id)
discovery_results = integrate_aplus_discovery_with_deep_analysis(session_id)
backtesting_results = connect_backtesting_to_discovery_results(session_id)
report_path = generate_python_report(portfolio_review, analysis_results, session_id)

total_time = time.time() - start_time

# Log performance metrics
print(f"📊 Pipeline Performance:")
print(f"   Total time: {total_time:.2f}s")
print(f"   Holdings analyzed: {analysis_results['successful_analyses']}")
print(f"   Time per holding: {total_time / len(holdings):.2f}s")
print(f"   LLM calls: 0")
print(f"   Cost: $0.00")
```

## Troubleshooting

### Issue: All Holdings Have Identical Scores

**Symptom:**

```
ValueError: Score validation failed: All holdings have identical scores
```

**Cause:** QuantitativeAnalysisTool is returning default values instead of real data.

**Solution:**

1. Check API keys are configured correctly
2. Verify ticker symbols are valid
3. Check network connectivity
4. Review QuantitativeAnalysisTool logs

### Issue: No A+ Opportunities Found

**Symptom:**

```python
discovery_results["has_a_plus_analysis"] == False
discovery_results["total_opportunities_found"] == 0
```

**Possible Causes:**

1. Deep analysis not completed
2. No holdings achieved A+ or A grade
3. JSON files not in expected directories

**Solution:**

1. Verify deep analysis completed successfully
2. Check analysis results for grades
3. Verify output directory structure exists

### Issue: Backtesting Not Executing

**Symptom:**

```python
backtesting_results["backtesting_executed"] == False
```

**Possible Causes:**

1. No A+ candidates found
2. Discovery integration failed

**Solution:**

1. Run A+ discovery integration first
2. Check discovery results for candidates
3. Verify discovery JSON files exist

## Best Practices

### 1. Use Unique Session IDs

Always use unique session IDs to avoid file conflicts:

```python
import time
session_id = f"analysis_{int(time.time())}"
```

### 2. Validate Input Data

Validate holdings before analysis:

```python
from finwiz.schemas.portfolio_review import HoldingDecision

# Validate each holding
for holding in holdings:
    assert isinstance(holding, HoldingDecision)
    assert holding.ticker
    assert holding.asset_class in ["stock", "etf", "crypto"]
```

### 3. Check Results Before Proceeding

Verify each step succeeded before continuing:

```python
if analysis_results["successful_analyses"] > 0:
    # Proceed with discovery
    discovery_results = integrate_aplus_discovery_with_deep_analysis(session_id)
else:
    # Handle failure
    logger.error("Deep analysis failed - cannot proceed")
```

### 4. Clean Up Old Files

Periodically clean up old analysis files:

```python
from pathlib import Path
import time

# Remove files older than 7 days
output_dir = Path("output")
current_time = time.time()
max_age = 7 * 24 * 60 * 60  # 7 days in seconds

for file_path in output_dir.rglob("*.json"):
    if current_time - file_path.stat().st_mtime > max_age:
        file_path.unlink()
        print(f"Removed old file: {file_path}")
```

## Related Documentation

- [Python Pipeline Architecture](../explanations/python_pipeline_architecture.md)
- [Integration Reference](../reference/integration/python_pipeline_integration.md)
