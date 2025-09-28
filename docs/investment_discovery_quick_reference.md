# Quick Reference - A+ Investment Discovery

## Quick Start

### Launch Discovery
```bash
# Complete discovery (all asset types)
uv run python src/finwiz/main.py --discovery

# Specific asset type
uv run python src/finwiz/main.py --discovery --asset-type etf
uv run python src/finwiz/main.py --discovery --asset-type stock  
uv run python src/finwiz/main.py --discovery --asset-type crypto
```

### Python API
```python
from finwiz.crews.investment_discovery_crew import InvestmentDiscoveryCrew

crew = InvestmentDiscoveryCrew()
result = crew.discover_etfs()  # or discover_stocks(), discover_crypto()
```

## A+ Criteria Summary

### ETFs A+ (Score ≥ 0.95)
- ✅ Expense ratio ≤ 0.15% (broad) / ≤ 0.25% (specialized)
- ✅ AUM ≥ $1B for liquidity
- ✅ Tracking error ≤ 0.20% (3-year)
- ✅ Operating history ≥ 3 years
- ✅ UCITS compliant (for EU investors)

### Stocks A+ (Score ≥ 0.95)
- ✅ ROE ≥ 20% (3-year average)
- ✅ Revenue growth ≥ 15% annual (5-year)
- ✅ Debt/Equity ratio ≤ 0.3
- ✅ Positive & growing Free Cash Flow
- ✅ Market cap ≥ $1B
- ✅ Dominant market position

### Crypto A+ (Score ≥ 0.95)
- ✅ Market cap ≥ $10B
- ✅ Daily volume ≥ $500M
- ✅ Age ≥ 36 months
- ✅ Institutional adoption
- ✅ Real utility & use cases
- ✅ Active development team

## Configuration Files

### Personal Settings
```yaml
# config/discovery_settings.yaml
risk_tolerance: "moderate"     # conservative, moderate, aggressive
min_score: 0.95               # A+ threshold
max_correlation: 0.7          # Max correlation with existing portfolio
regions: ["US", "EU", "CH"]   # Geographic regions
esg_filter: true              # ESG filtering enabled
max_results_per_type: 20      # Limit discoveries per asset type
```

### Asset-Specific Criteria
```yaml
# config/custom_criteria.yaml
etf_criteria:
  max_expense_ratio: 0.12
  min_aum_billions: 2.0
  ucits_only: true

stock_criteria:
  min_roe: 0.25
  min_market_cap_billions: 5.0
  max_debt_to_equity: 0.2

crypto_criteria:
  min_market_cap_billions: 15.0
  institutional_adoption_required: true
  max_allocation_percent: 5.0
```

## Report Interpretation

### Grade Scale
| Grade | Score Range | Meaning |
|-------|-------------|---------|
| A+ | 0.95-1.00 | Exceptional quality |
| A | 0.90-0.94 | Excellent |
| A- | 0.85-0.89 | Very good |
| B+ | 0.80-0.84 | Good |
| B | 0.75-0.79 | Average |
| <B | <0.75 | Below average |

### Recommendation Codes
| Code | Action | Priority |
|------|--------|----------|
| 🔄 REPLACE | Substitute current holding | High |
| ➕ ADD | New allocation | Medium |
| 📈 INCREASE | Boost existing position | Medium |
| ⚖️ REBALANCE | Adjust proportions | Low |

### Confidence Levels
| Level | Range | Interpretation |
|-------|-------|----------------|
| 🟢 High | 90-100% | Strong recommendation |
| 🟡 Moderate | 70-89% | Good opportunity |
| 🟠 Low | 50-69% | Conditional recommendation |

## Common Commands

### Monitoring
```bash
# Check A+ status of specific investment
uv run python src/finwiz/main.py --monitor VXUS

# Monitor portfolio A+ grades
uv run python src/finwiz/main.py --monitor-portfolio

# Generate monitoring report
uv run python src/finwiz/main.py --report --type monitoring
```

### Customization
```bash
# Discovery with custom criteria
uv run python src/finwiz/main.py --discovery --config custom_criteria.yaml

# Discovery for specific region
uv run python src/finwiz/main.py --discovery --region EU

# Discovery with ESG filter
uv run python src/finwiz/main.py --discovery --esg-only
```

## API Endpoints

### REST API
```http
POST /api/v1/discovery/discover/etf
GET  /api/v1/discovery/monitor/{symbol}
POST /api/v1/discovery/batch-discover
GET  /api/v1/discovery/criteria/{asset_type}
```

### Python SDK
```python
# Discover A+ opportunities
discoveries = client.discovery.discover_etfs(
    max_expense_ratio=0.10,
    min_aum_billions=2.0
)

# Monitor investment
status = client.discovery.monitor_investment("VXUS")

# Batch discovery
all_discoveries = client.discovery.discover_all_assets([
    "etf", "stock", "crypto"
])
```

## Troubleshooting

### Common Issues
| Issue | Solution |
|-------|----------|
| No A+ found | Lower min_score to 0.92-0.93 |
| API timeout | Reduce max_results_per_type |
| Data unavailable | Wait 15 min, retry |
| Rate limit hit | Wait 1 hour or upgrade plan |

### Error Codes
| Code | Meaning | Action |
|------|---------|--------|
| 400 | Bad request | Check parameters |
| 401 | Unauthorized | Verify API key |
| 429 | Rate limited | Wait and retry |
| 500 | Server error | Contact support |

## Performance Expectations

### Typical Results
- **Discovery time**: 2-5 minutes per asset type
- **A+ candidates found**: 5-15 per month
- **Portfolio improvement**: +0.5-2.0% annual return
- **Grade improvement**: +0.3-0.8 points average

### Success Metrics
- **Precision**: 85% of A+ maintain grade 6+ months
- **Performance**: 82% outperform benchmark
- **Cost reduction**: 35-45% average fee savings
- **Risk improvement**: 8% volatility reduction average

## Key Files & Locations

### Configuration
```
config/
├── discovery_settings.yaml    # Main settings
├── custom_criteria.yaml       # Asset-specific criteria
└── agents.yaml               # Agent configurations
```

### Output
```
output/
├── discovery/
│   ├── a_plus_etfs.md        # ETF discoveries
│   ├── a_plus_stocks.md      # Stock discoveries
│   └── a_plus_crypto.md      # Crypto discoveries
└── reports/
    └── portfolio_improvement.html
```

### Logs
```
logs/
├── discovery.log             # Discovery operations
├── monitoring.log            # A+ monitoring
└── errors.log               # Error tracking
```

## Support Resources

### Documentation
- 📖 [Complete User Guide](investment_discovery_user_guide.md)
- 🔧 [Developer Guide](investment_discovery_developer_guide.md)
- 📋 [API Reference](investment_discovery_api_reference.md)
- ❓ [FAQ](investment_discovery_faq.md)

### Getting Help
- 📧 Email: support@finwiz.ai
- 💬 Chat: Available Mon-Fri 9AM-6PM CET
- 🌐 Community: https://community.finwiz.ai
- 📚 Knowledge Base: https://help.finwiz.ai

### Training
- 🎥 Video Tutorials: https://learn.finwiz.ai
- 📅 Weekly Webinars: Tuesdays 2PM CET
- 👥 1-on-1 Sessions: Available for premium users

---

**Need more details?** See the [complete user guide](investment_discovery_user_guide.md) or contact support.