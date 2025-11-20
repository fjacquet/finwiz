# Changelog

All notable changes to FinWiz are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-11-20

### Added

**Scoring System Enhancements:**

- **Adaptive Weighting for Quality Companies**: Automatically detect quality companies (2+ of: ROE ≥20%, Debt ≤0.5, Margin ≥15%) and apply 50/25/25 weights (fundamental/technical/risk) instead of standard 40/30/30
- **Data Sanity Checks**: Comprehensive validation rejecting obviously invalid data (ROE=0.0, price≤$0, debt>100x equity, etc.)
- **Calculated Revenue Growth**: Compute growth from actual financial statements instead of relying on stale yfinance `revenueGrowth` field
- **Enhanced Error Extraction**: Flexible regex patterns for extracting grades/scores from raw crew output with debug logging

**Documentation:**
- Comprehensive [Deep Analysis Scoring System](../explanations/deep_analysis.md) documentation with real-world examples
- Complete [Recommendation Engine](../explanations/recommendation_engine.md) guide explaining BUY/HOLD/SELL logic
- Detailed [Investment Methodology](../explanations/investment_methodology.md) covering philosophy and decision framework

### Changed

**Scoring Threshold Adjustments:**

- **Revenue Growth**: More realistic thresholds for mature companies
  - 0-5% growth now scores 0.4 (acceptable) instead of 0.2 (poor)
  - Recognizes that mature companies with stable 0-5% growth are healthy
- **Volatility**: Raised thresholds to accommodate cyclical sectors
  - Very low: 10% → 15%
  - Low: 15% → 25%
  - Moderate: 25% → 35%
  - Semiconductors, industrials naturally more volatile
- **Portfolio KEEP/SELL Threshold**: Aligned to 0.65 (C grade) from 0.55
  - Grade D (0.50-0.65) now correctly triggers SELL
  - Grade F (<0.50) remains strong SELL
  - Consistent with HOLD recommendation threshold

**Data Quality Improvements:**
- Revenue growth calculation: ASML corrected from 0.7% (stale) → 2.56% (calculated)
- ROE sanity check: Reject ROE exactly 0.0 as data error
- Comprehensive field validation with reasonable numeric ranges

### Fixed

- **ASML Scoring**: C+ (0.726) → B (0.765) after corrections
  - Quality company detection: 3/3 criteria met
  - Adaptive weights applied: 50/25/25
  - Revenue growth fixed: 2.56% (was 0.7%)
  - Despite high volatility (38.9%), exceptional fundamentals justify BUY
- **Grade F Holdings**: Now correctly marked as SELL instead of KEEP
- **Data Extraction Errors**: Improved regex patterns prevent "Missing required field 'grade/score'" errors
- **yfinance Data Issues**: Calculate metrics from source financials when vendor data stale

### Performance

- **Python Scoring Engine**: 50-100x faster than AI-based scoring
- **Cost Reduction**: 100% cost savings ($0 vs $0.01-0.05 per analysis)
- **Deterministic**: Same input always produces same output
- **Transparent**: Full calculation lineage and audit trail

## [1.9.0] - 2025-11-15

### Added

- Batch processing for portfolio deep analysis (10-20x speedup)
- Data pre-fetching with concurrent API calls
- Enhanced caching with TTL support (45 minutes default)

### Changed

- Deep analysis crew now uses Python scorer instead of AI
- Improved error handling and logging

## [1.8.0] - 2025-11-10

### Added

- Portfolio rebalancing crew with optimization
- Investment discovery for A+ opportunities
- Alternative recommendations for underperforming holdings

### Changed

- Updated to CrewAI 0.28.0
- Improved Pydantic schema validation

## [1.7.0] - 2025-11-05

### Added

- Deep analysis crew for comprehensive holding evaluation
- Risk assessment with volatility and drawdown metrics
- Technical analysis integration (RSI, MACD, trend detection)

### Fixed

- Rate limiting issues with external APIs
- Memory leaks in long-running analysis sessions

## [1.6.0] - 2025-11-01

### Added

- Portfolio review functionality
- Multi-asset analysis (stocks, ETFs, crypto)
- Structured output with Pydantic validation

### Changed

- Migrated to Python 3.12
- Updated dependencies to latest stable versions

## [1.5.0] - 2025-10-25

### Added

- Stock crew for equity analysis
- ETF crew for fund analysis
- Crypto crew for cryptocurrency analysis

### Changed

- Improved tool factories for consistent tool initialization
- Enhanced agent configuration with reasoning and planning

## [1.0.0] - 2025-10-01

### Added

- Initial release of FinWiz platform
- Basic stock analysis capabilities
- Yahoo Finance integration
- CrewAI framework integration

---

## Version Guidelines

### Version Numbers

- **Major (X.0.0)**: Breaking changes, significant architectural updates
- **Minor (1.X.0)**: New features, backward-compatible enhancements
- **Patch (1.0.X)**: Bug fixes, minor improvements

### Categories

- **Added**: New features, capabilities, documentation
- **Changed**: Changes to existing functionality
- **Deprecated**: Features marked for removal
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security vulnerability fixes
- **Performance**: Performance improvements

## Migration Guides

### Upgrading to 2.0.0

**Breaking Changes**: None - fully backward compatible

**New Features**:

1. **Adaptive Weighting**: Quality companies automatically detected and scored with emphasis on fundamentals
2. **Enhanced Validation**: More robust data validation prevents misleading recommendations
3. **Better Thresholds**: More realistic scoring for mature companies and cyclical sectors

**Configuration Changes**:

- `VALIDATION_STRICTNESS`: Now defaults to `warn` (previously `off` in dev)
- `KEEP_THRESHOLD`: Aligned to 0.65 in portfolio processor

**Recommended Actions**:

1. Re-run portfolio analysis to benefit from improved scoring
2. Review any D-grade holdings (now correctly marked as SELL)
3. Check quality companies (ROE ≥20%, Debt ≤0.5, Margin ≥15%) for potential upgrades

## Links

- [Documentation](../README.md)
- [GitHub Repository](https://github.com/finwiz/finwiz)
- [Issue Tracker](https://github.com/finwiz/finwiz/issues)
- [Release Notes](https://github.com/finwiz/finwiz/releases)

---

**Maintained by**: FinWiz Development Team
**Last Updated**: November 2025
**Format**: [Keep a Changelog](https://keepachangelog.com/)
