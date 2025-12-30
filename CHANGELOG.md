# Changelog

All notable changes to the FinWiz project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **Major Refactoring**: Split 13 large files (600-1682 lines) into 40+ focused modules
  - `deep_analysis_orchestrator.py` (1,682 → 4 modules): data_collector, executor, processor
  - `deep_analysis_scorer.py` (1,178 → 3 modules): score_result_builder, crew_export_generator
  - `hybrid_analysis_flow.py` (1,042 → 3 modules): data_collector, synthesizer
  - `quantitative_analysis_tool.py` (649 → 5 modules): technical, backtesting, performance analyzers
  - `report_consolidator.py` (646 → 3 modules): export_loaders, html_collector
  - `schemas/quantitative/models.py` (643 → 7 domain files): backtesting, data, enums, portfolio, risk, screening, technical
  - `supabase/client.py` (641 → 6 modules): config, health, metrics, operations, pool
  - `registry_manager.py` (624 → 5 modules): models, data_retrieval, execution, storage
  - `flow_state.py` (620 → 4 modules): models, analysis, utils
- Applied functional programming patterns (list comprehensions, itertools, operator module)
- Centralized exception hierarchy in `exceptions/` module

### Fixed
- Dead code cleanup: Prefixed 8 unused parameters with underscore (vulture 100% confidence)
- Security: Fixed MD5 hash usage with `usedforsecurity=False` (bandit high-severity)
- Lint: Fixed 10 ruff issues (unused imports, unsorted imports)
- Tests: Fixed 6 test failures from method path changes after refactoring
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
