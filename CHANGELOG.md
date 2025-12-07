# Changelog

All notable changes to the FinWiz project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- `data_extractor.py`: Added fallback to `final_grade`/`final_score` when AI crews output these instead of `grade`/`composite_score`
- `python_report_generator.py`: Handle None grade gracefully to prevent `'NoneType' has no attribute 'lower'` error
- Added 3 new tests to verify AI crew output format compatibility

### Added
- Comprehensive CLAUDE.md documentation for all major subfolders
  - `src/finwiz/crews/CLAUDE.md` - Crew development guide
  - `src/finwiz/flows/CLAUDE.md` - Flow orchestration documentation
  - `src/finwiz/tools/CLAUDE.md` - Tool factories and usage
  - `src/finwiz/schemas/CLAUDE.md` - Pydantic schema documentation
  - `src/finwiz/quantitative/CLAUDE.md` - Quantitative analysis guide
  - `src/finwiz/orchestrators/CLAUDE.md` - Orchestration patterns
  - `src/finwiz/reporting/CLAUDE.md` - Report generation (Python/Jinja2)
  - `src/finwiz/utils/CLAUDE.md` - Utility functions and decorators
  - `src/finwiz/data/CLAUDE.md` - Data acquisition layer
  - `src/finwiz/integration/CLAUDE.md` - Data integration and validation
  - `src/finwiz/scoring/CLAUDE.md` - Python scoring engine
  - `src/finwiz/validation/CLAUDE.md` - Validation infrastructure
- This CHANGELOG.md file for tracking project changes

### Changed
- Updated main CLAUDE.md with references to subfolder documentation

## [0.1.0] - 2025-12-07

### Added
- Initial FinWiz platform release
- CrewAI-based multi-agent financial analysis system
- Stock, ETF, and cryptocurrency analysis crews
- Portfolio review and rebalancing functionality
- A+ investment discovery system
- Deep per-holding analysis with Python scoring
- Hybrid Python/AI analysis architecture
- Quantitative analysis with Backtrader, TA-Lib, QuantLib, PyPortfolioOpt
- Batch processing for high-performance portfolio analysis (10-20x speedup)
- HTML report generation with Jinja2 templates
- RAG (Retrieval-Augmented Generation) integration
- Multi-source data fetching with fallback strategies

### Core Crews
- `StockCrew` - Stock fundamental and technical analysis
- `EtfCrew` - ETF factsheet and holdings analysis
- `CryptoCrew` - Cryptocurrency on-chain metrics
- `DeepAnalysisCrew` - Per-holding comprehensive analysis
- `InvestmentDiscoveryCrew` - A+ opportunity discovery
- `PortfolioRebalancingCrew` - Portfolio optimization
- `ReportCrew` - Final consolidated report generation

### AI Minimalism Implementation
- Python-based scoring engine (100% cost reduction vs AI)
- Jinja2 template-based report generation
- Deterministic calculations for reproducibility
- AI reserved for analysis requiring reasoning

### Testing
- pytest with pytest-mock (no unittest.mock)
- Faker for test data generation
- 65% minimum coverage requirement
- Type checking with mypy

---

## Changelog Maintenance

Claude should maintain this changelog by:

1. **Adding entries** when implementing new features or fixing bugs
2. **Categorizing changes** under appropriate headers:
   - `Added` - New features
   - `Changed` - Changes in existing functionality
   - `Deprecated` - Soon-to-be removed features
   - `Removed` - Removed features
   - `Fixed` - Bug fixes
   - `Security` - Security-related changes
3. **Including context** - Brief description of what changed and why
4. **Referencing issues/PRs** when applicable

### Example Entry

```markdown
### Fixed
- Resolved JSON serialization error in crew exports by adding `default=str` to all `json.dumps()` calls
- Fixed mock path errors in tests by patching at import location rather than definition
```
