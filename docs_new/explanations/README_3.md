---
title: ""
description: "Understanding the concepts and design of "
category: "explanations"
tags:
  - "explanations"
date: "2025-10-26"
source: "investment_discovery/README.md"
---

# A+ Investment Discovery Documentation

[TOC]

## Overview

The A+ Investment Discovery system transforms FinWiz from a passive portfolio evaluator into an active opportunity finder. It proactively scans global markets to identify exceptional investment opportunities with scores ≥ 0.95 across ETFs, stocks, and cryptocurrencies.

## Key Benefits

- **Proactive Discovery**: Finds opportunities you might miss
- **Quality Focus**: Only recommends truly exceptional investments (A+ grade)
- **Cost Optimization**: Identifies lower-cost alternatives with better performance
- **Risk Management**: Validates all recommendations through rigorous backtesting
- **Continuous Monitoring**: Tracks your A+ investments to ensure they maintain quality

## Documentation

### 📖 [User Guide](user_guide.md)

Complete guide for using the A+ discovery system:

- What is an A+ investment?
- How discovery works
- A+ criteria for ETFs, stocks, and crypto
- Step-by-step usage instructions
- Real-world examples
- Implementation strategies

### 🔧 [Developer Guide](developer_guide.md)

Technical documentation for developers:

- Architecture overview
- Core components
- Tool architecture
- Extending the system
- Integration patterns
- Testing strategies

### 📚 [API Reference](api_reference.md)

Complete API documentation:

- REST endpoints
- Python APIs
- Data schemas
- Request/response examples
- Error handling

### ❓ [FAQ](faq.md)

Answers to common questions:

- General questions
- Methodology and criteria
- Implementation guidance
- Technical troubleshooting
- Performance expectations

## Quick Start

### Run Discovery

```bash
# Discover A+ opportunities across all asset types
uv run python src/finwiz/main.py --discovery

# Discover specific asset type
uv run python src/finwiz/main.py --discovery --asset-type etf
```text
### A+ Criteria Summary

**ETFs**:

- Expense ratio ≤ 0.15%
- AUM ≥ $1B
- Tracking error ≤ 0.20%
- 3+ year history

**Stocks**:

- ROE ≥ 20%
- Revenue growth ≥ 15%
- Debt/equity ≤ 0.3
- Positive FCF

**Crypto**:

- Market cap ≥ $10B
- Daily volume ≥ $500M
- Institutional adoption
- Real utility

## Output Files

After discovery completes:

- `output/discovery/discovery_latest.json` - Latest results
- `output/discovery/discovery_YYYY-MM-DD.json` - Timestamped results
- `output/discovery/discovery_report.html` - HTML report

## Integration

The discovery system integrates with:

- **Portfolio Review**: Suggests A+ alternatives for underperforming holdings
- **Portfolio Rebalancing**: Provides A+ candidates for rebalancing
- **Alternative Finder**: Prioritizes A+ candidates for replacements

## See Also

- [Portfolio Holdings Analysis](../portfolio_holdings_analysis_user_guide.md)
- [Portfolio Rebalancing](../portfolio_rebalancing/index.md)
- [A+ Monitoring System](../a_plus_monitoring_system.md)
- [A+ Scoring Tool](../a_plus_scoring_tool.md)

---

**Version**: 2.0
**Last Updated**: 2025-03-10
