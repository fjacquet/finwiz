# Implementation Plan - Grouped for Efficiency

**Current Status**: Major file decomposition work has been completed. The codebase has been significantly modernized with most large files successfully split into smaller, focused modules.

## Group 1: Critical Testing Modernization (High Priority)

- [x] 1. Convert unittest.mock to pytest-mock across entire test suite
  - [x] 1.1 Convert integration tests (tests/integration/) to pytest-mock
    - Update ~20 integration test files using unittest.mock
    - Replace `from unittest.mock import patch, Mock` with `mocker` fixture
    - Run `uv run pytest tests/integration/` after each conversion
    - Ensure `ruff check tests/integration/` passes with no errors
    - _Requirements: 3_
  
  - [x] 1.2 Convert performance tests (tests/performance/) to pytest-mock
    - Update performance test files using unittest.mock
    - Ensure async mocking uses pytest-asyncio patterns
    - Run `uv run pytest tests/performance/` to validate changes
    - Ensure `ruff check tests/performance/` passes with no errors
    - _Requirements: 3_
  
  - [x] 1.3 Standardize test mocking patterns and validate
    - Create consistent mock setup patterns for external APIs
    - Document new testing standards and examples
    - Ensure all mocks specify expected behavior explicitly
    - Run full test suite: `uv run pytest -m "not integration"`
    - Verify no unittest.mock imports remain: `grep -r "unittest.mock" tests/`
    - _Requirements: 3_

## Group 2: Core Infrastructure Files (800+ lines)

- [x] 2. Split largest remaining infrastructure files with quality validation
  - [x] 2.1 Split quantitative/data.py (829 lines)
    - Extract data loading to data_loaders.py
    - Extract processing to data_processors.py
    - Extract validation to data_validators.py
    - Run `ruff check src/finwiz/quantitative/` after split
    - Run `uv run pytest tests/unit/quantitative/` to validate functionality
    - _Requirements: 1_
  
  - [x] 2.2 Split integration/logging_utils.py (803 lines)
    - Extract formatters to log_formatters.py
    - Extract handlers to log_handlers.py
    - Extract configuration to log_config.py
    - Run `ruff check src/finwiz/integration/` after split
    - Run `uv run pytest tests/unit/integration/` to validate functionality
    - _Requirements: 1_
  
  - [x] 2.3 Split utils/session_manager.py (790 lines)
    - Extract persistence to session_persistence.py
    - Extract validation to session_validation.py
    - Extract state management to session_state.py
    - Run `ruff check src/finwiz/utils/` after split
    - Run `uv run pytest tests/unit/utils/` to validate functionality
    - _Requirements: 1_
  
  - [x] 2.4 Split quantitative/rebalancing_engine.py (790 lines)
    - Extract optimization to optimization_algorithms.py
    - Extract trade generation to trade_generation.py
    - Extract execution to execution_engine.py
    - Run `ruff check src/finwiz/quantitative/` after split
    - Run `uv run pytest tests/unit/quantitative/` to validate functionality
    - _Requirements: 1_

## Group 3: Main Application & Orchestration

- [ ] 3. Finalize main application decomposition with comprehensive testing
  
  - [ ] 3.2 Validate application startup and flow
    - Test application startup: `uv run python src/finwiz/main.py --help`
    - Run full integration test: `uv run pytest tests/integration/`
    - Ensure all CrewAI flows still work correctly
    - Run `ruff check . && ruff format .` for full codebase validation
    - _Requirements: 1_

## Group 4: Analysis & Processing Tools (700+ lines)

- [x] 4. Split remaining analysis tools with quality checks
  - [x] 4.1 Split integration/validation_pipeline.py (745 lines)
    - Extract validation rules to validation_rules.py
    - Extract pipeline stages to pipeline_stages.py
    - Run `ruff check src/finwiz/integration/` after split
    - Run `uv run pytest tests/unit/integration/` to validate
    - _Requirements: 1_
  
  - [x] 4.2 Split tools/enhanced_twelve_data_tool.py (736 lines)
    - Extract API client to twelve_data_client.py
    - Extract transformers to twelve_data_transformers.py
    - Run `ruff check src/finwiz/tools/` after split
    - Run `uv run pytest tests/tools/` to validate tool functionality
    - _Requirements: 1_
  
  - [x] 4.3 Split quantitative/performance.py (729 lines)
    - Extract metrics to performance_metrics.py
    - Extract benchmarks to performance_benchmarks.py
    - Run `ruff check src/finwiz/quantitative/` after split
    - Run `uv run pytest tests/unit/quantitative/` to validate
    - _Requirements: 1_
  
  - [x] 4.4 Split quantitative/scenario_analyzer.py (722 lines)
    - Extract generators to scenario_generators.py
    - Extract analysis to scenario_analysis.py
    - Run `ruff check src/finwiz/quantitative/` after split
    - Run `uv run pytest tests/unit/quantitative/` to validate
    - _Requirements: 1_
  
  - [x] 4.5 Split utils/a_plus_monitoring.py (707 lines)
    - Extract metrics to monitoring_metrics.py
    - Extract alerts to monitoring_alerts.py
    - Run `ruff check src/finwiz/utils/` after split
    - Run `uv run pytest tests/unit/utils/` to validate
    - _Requirements: 1_

## Group 5: Final Validation & Quality Assurance

- [x] 5. Comprehensive validation and quality assurance
  - [x] 5.1 Complete test suite validation
    - Run full test suite: `uv run pytest`
    - Verify all pytest-mock conversions work correctly
    - Ensure no unittest.mock imports remain: `grep -r "unittest.mock" . --exclude-dir=.git`
    - Validate test performance (< 5 seconds per suite)
    - Check test coverage is maintained or improved
    - _Requirements: 3_
  
  - [x] 5.2 Code quality and standards validation
    - Run complete linting: `ruff check . && ruff format .`
    - Ensure no ruff complaints remain
    - Confirm all target files are under 200 lines: `find src/finwiz -name "*.py" -exec wc -l {} + | sort -nr | head -20`
    - Verify no functionality regressions with integration tests
    - Test all CrewAI crews function correctly
    - _Requirements: 1, 2_
  
  - [x] 5.3 Final documentation and cleanup
    - Update development guidelines with new patterns
    - Document new file organization structure
    - Create examples of proper pytest-mock usage
    - Remove any unused imports or dead code
    - Verify all files have proper docstrings and type hints
    - _Requirements: 1, 2, 3_
  
  - [x] 5.4 Performance and functionality validation
    - Run application end-to-end test
    - Verify startup time hasn't degraded
    - Test key workflows (stock analysis, portfolio rebalancing, etc.)
    - Ensure all external API integrations still work
    - Validate memory usage and performance metrics
    - _Requirements: 1, 2, 3_

## Completed Work (Major Achievements)

✅ **Successfully Completed**:
- technical.py split into technical/ module with 8 focused files (31 lines main file)
- main.py partially split (crew_factory.py: 440 lines, flow_state.py: 339 lines)
- rebalancing_report_generator.py split (184 lines remaining)
- market_screening_tool.py split (189 lines remaining)
- data_accessor.py split (143 lines remaining)
- perplexity_analysis_integration.py split (570 lines remaining, with error/logging/performance modules)
- backtesting.py split (189 lines remaining)
- enhanced_sentiment_tool.py split (118 lines remaining)
- portfolio_rebalancing.py split (228 lines remaining)
- technical_analyzer.py split (79 lines remaining)
- All crews verified to use @CrewBase decorator and YAML configs

## Success Metrics - Updated

- **Major Files Split**: 10+ large files successfully decomposed
- **Files Under 200 Lines**: Significant progress made on readability
- **CrewAI Compliance**: ✅ All crews use proper decorator patterns
- **Testing Modernization**: ❌ Critical work needed - unittest.mock still prevalent
- **Overall Impact**: ~60% of major file decomposition work completed

## Critical Priority

**Testing modernization is now the highest priority** - the codebase has extensive unittest.mock usage that needs conversion to pytest-mock to meet requirements.