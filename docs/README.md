# FinWiz Documentation

Welcome to the FinWiz documentation. This is your central navigation hub for all documentation.

## 🚀 Quick Start

New to FinWiz? Start here:

1. **[Installation & Setup](../README.md#getting-started)** - Get FinWiz running
2. **[User Guide](USER_GUIDE.md)** - Learn how to use FinWiz features
3. **[Developer Guide](DEVELOPER_GUIDE.md)** - Start developing with FinWiz

## 📚 Core Documentation

### For Developers

- **[Developer Guide](DEVELOPER_GUIDE.md)** - Complete development guide
  - Quick start and setup
  - CrewAI development standards
  - Testing standards
  - Code quality standards
  - Common patterns

- **[Architecture Guide](ARCHITECTURE.md)** - System architecture and design
  - Design principles
  - System architecture
  - Core systems (validation, caching, feature flags)
  - Data flow
  - Modernization history

- **[API Reference](API_REFERENCE.md)** - Complete API documentation
  - Crews
  - Tools
  - Schemas
  - Utilities
  - Configuration

- **[User Guide](USER_GUIDE.md)** - Deployment, operations, and migration
  - Installation and deployment
  - Daily operations and advanced system configuration
  - Monitoring and maintenance
  - Migration guide

### For AI Agents

AI agent guidelines are now in `.kiro/steering/` for automatic guidance during development. See the [Steering Files](#standards-in-kirosteering) section below.

## 📖 User Guides

### Portfolio Management

- **[Portfolio Holdings Analysis](portfolio_holdings_analysis_user_guide.md)** - Analyze your holdings
  - Understanding your portfolio report
  - Interpreting price targets
  - Evaluating alternative investments
  - A+ improvement roadmap
  - Position sizing recommendations

- **[Portfolio Rebalancing](portfolio_rebalancing/)** - Rebalance your portfolio
  - [User Guide](portfolio_rebalancing/user_guide.md)
  - [Developer Guide](portfolio_rebalancing/developer_guide.md)
  - [API Reference](portfolio_rebalancing/api_reference.md)

### Investment Discovery

- **[Investment Discovery](investment_discovery/)** - Discover A+ opportunities
  - [User Guide](investment_discovery/user_guide.md)
  - [Developer Guide](investment_discovery/developer_guide.md)
  - [API Reference](investment_discovery/api_reference.md)
  - [FAQ](investment_discovery/faq.md)

### Quantitative Analysis

- **[Quantitative Analysis](quantitative_analysis.md)** - Professional-grade analysis
  - Backtesting engine
  - Technical analysis
  - Portfolio optimization
  - Performance analytics

### Enhanced Data Extraction

- **[Enhanced Data Extraction](ENHANCED_DATA_EXTRACTION.md)** - A comprehensive guide to the data extraction system, including a quick start, technical reference, and practical examples for building reports.

## 🔧 System Documentation

### Core Systems

- **[Data Quality Guide](DATA_QUALITY_GUIDE.md)** - Comprehensive guide for maintaining data quality and handling missing data.
- **[Complete Analysis Guide](COMPLETE_ANALYSIS_GUIDE.md)** - How to run a full analysis and ensure data is up-to-date.
- **[Perplexity Sonar Integration](perplexity_sonar_integration_spec.md)** - Enhanced research capabilities.

### Standards (in `.kiro/steering/`)

AI development standards are now in steering files for automatic guidance:

- **agents.md** - Agent behavior guidelines
- **output-standards.md** - Output formatting standards
- **validation.md** - Validation rules and criteria
- **crewai-standards.md** - CrewAI development patterns
- **testing-standards.md** - Testing best practices

## 📦 Reference

### Schemas

- **[Schemas Documentation](schemas/)** - Pydantic models and JSON schemas

### Change Requests

- **[Change Requests](change_requests/)** - Historical change requests

### Historical Documentation

- **[Archive](archive/)** - Historical documentation and reports

## 🎯 By Use Case

### I want to

**Analyze my portfolio**
→ [Portfolio Holdings Analysis](portfolio_holdings_analysis_user_guide.md)

**Rebalance my portfolio**
→ [Portfolio Rebalancing](portfolio_rebalancing/)

**Find new investment opportunities**
→ [Investment Discovery](investment_discovery/)

**Run quantitative analysis**
→ [Quantitative Analysis](quantitative_analysis.md)

**Ensure data quality in reports**
→ [Data Quality Guide](DATA_QUALITY_GUIDE.md)

**Use enhanced data in reports**
→ [Enhanced Data Extraction](ENHANCED_DATA_EXTRACTION.md)

**Develop a new feature**
→ [Developer Guide](DEVELOPER_GUIDE.md) + [Architecture Guide](ARCHITECTURE.md)

**Create a new crew**
→ [Developer Guide](DEVELOPER_GUIDE.md#crewai-development-standards)

**Understand the codebase**
→ [Architecture Guide](ARCHITECTURE.md)

**Write tests**
→ [Developer Guide](DEVELOPER_GUIDE.md#testing-standards)

**Integrate an external service**
→ [Architecture Guide](ARCHITECTURE.md#integration-patterns)

## 📝 Historical Documentation

Historical implementation summaries and reports are now organized in the archive:

- **[Implementation Summaries](archive/implementation_summaries/)** - Task implementation records
- **[Fix Reports](archive/fix_reports/)** - Bug fix documentation
- **[Consolidation Reports](archive/consolidation_reports/)** - Documentation consolidation history
- **[Testing Documentation](archive/testing/)** - Testing implementation history

These files are preserved for reference but not needed for daily development.

## 🔍 Search Tips

- Use your IDE's search (Cmd/Ctrl+Shift+F) to search across all documentation
- Check the [API Reference](API_REFERENCE.md) for specific tool/schema documentation
- Check the [Archive](archive/) for historical context

## 📞 Getting Help

- **Issues**: Report bugs or request features on GitHub
- **Questions**: Check the [Investment Discovery FAQ](investment_discovery/faq.md)
- **Updates**: Follow release notes for new features

---

**Documentation Version**: 2.3
**Last Updated**: 2025-10-11

## Recent Changes

### 2025-10-11: Documentation Consolidation

- **Consolidated Guides**: Merged several redundant documents to create single sources of truth. `SYSTEM_OPERATIONS.md` was merged into `USER_GUIDE.md`, and `APLUS_SYSTEM.md` was merged into the `investment_discovery` guides.
- **Consolidated Data Extraction Guides**: Merged `CREW_DATA_INTEGRATION_INDEX.md`, `CREW_DATA_INTEGRATION_QUICK_START.md`, and `REPORT_CREW_ENHANCED_EXAMPLES.md` into a single, comprehensive `ENHANCED_DATA_EXTRACTION.md` guide.
- **Archived Files**: Moved numerous historical task summaries, fix reports, and migration guides to the `docs/archive/` directory to declutter the main documentation.
- **Improved Navigation**: Updated this README to provide a cleaner, more intuitive navigation structure with fewer top-level links.

### 2025-01-07: Data Quality Assurance Implementation

**New Feature** - Comprehensive data quality controls for report accuracy:

- Added `DATA_QUALITY_GUIDE.md` - Complete guide for maintaining data quality
- Implemented 5 new data quality components:
  - `SECFilingURLGenerator` - Valid SEC filing URLs with verification
  - `PortfolioHoldingsProcessor` - Complete portfolio processing
  - `APlusDiscoveryAccessor` - Reliable A+ discovery access
  - `BacktestingMetricsExtractor` - Complete metrics extraction
  - `DataAvailabilityTracker` - Data source tracking and freshness warnings
- Updated API_REFERENCE.md with data quality components
- Updated README.md with data quality section

**Core Principles**:
- Fail Fast: Reject invalid data at source
- Transparency: Clear communication when data unavailable
- No Hallucinations: Never generate fake data
- Completeness: Process all available data
- Traceability: Log all data decisions

**Benefits**:
- Zero hallucinated URLs in reports
- All SEC URLs verified or marked unavailable
- 100% portfolio holdings processed
- Clear A+ discovery status
- Complete backtesting metrics or marked "Not calculated"
- Data availability summary in all reports

### 2025-01-07: Documentation Cleanup & Consolidation

**Major Cleanup Complete** - Reduced clutter and improved organization:

- Reduced main docs/ from 50 files to 16 core files (68% reduction)
- Moved 29 historical files to organized archive:
  - 12 implementation summaries → `archive/implementation_summaries/`
  - 9 fix reports → `archive/fix_reports/`
  - 5 consolidation reports → `archive/consolidation_reports/`
  - 3 testing docs → `archive/testing/`
- Improved discoverability and maintainability
- Preserved all historical documentation for reference

**Benefits**:
- Easier to find current documentation
- Clear separation of current vs historical
- Reduced cognitive load
- Better organization

### 2025-01-07: Enhanced Data Extraction Documentation

**New Feature Documentation** - Comprehensive enhanced data extraction system:

- Added `ENHANCED_DATA_EXTRACTION.md` - Complete technical reference for all extractors
- Added `REPORT_CREW_ENHANCED_EXAMPLES.md` - 5 practical examples with production-ready code
- Added `CREW_DATA_INTEGRATION_QUICK_START.md` - Quick reference guide
- Added `CREW_DATA_INTEGRATION_INDEX.md` - Complete navigation hub
- Updated API_REFERENCE.md with new extractor utilities
- Updated README.md with enhanced data extraction features

**New Capabilities**:

- Backtesting metrics extraction (returns, Sharpe, drawdown, win rates)
- Market context indicators (VIX, inflation, rates, regime type)
- Discovery methodology details (criteria, statistics, scores)
- Performance aggregation (by asset type and regime)

### 2025-03-10: Phase 2 Documentation Consolidation

**Phase 2 Complete** - Further consolidation and steering integration:

- Reduced from ~30 files to ~20 core files (33% reduction)
- Created 3 consolidated guides: USER_GUIDE.md, APLUS_SYSTEM.md, SYSTEM_OPERATIONS.md
- Moved 5 standards to `.kiro/steering/` for AI guidance
- Archived 6 more redundant files
- Total reduction: 60+ files → ~20 files (67% reduction)

**Steering Files Created**:

- `agents.md` - Agent behavior guidelines
- `output-standards.md` - Output formatting standards
- `validation.md` - Validation rules
- `crewai-standards.md` - CrewAI patterns
- `testing-standards.md` - Testing standards

### 2025-03-10: Phase 1 Documentation Consolidation

- Consolidated 60+ files to ~30 core files
- Created organized subdirectories for features
- Archived 20+ historical documents
- Created comprehensive navigation hub
- Merged developer guides into single DEVELOPER_GUIDE.md
- Merged architecture docs into single ARCHITECTURE.md
- Created consolidated API_REFERENCE.md
