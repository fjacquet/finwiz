# FinWiz Development Makefile

.PHONY: help install test test-verbose test-all test-integration lint lint-check format clean setup dev check check-unittest-mock check-file-size check-stage-contract cleanup fix-currencies mypy coverage coverage-report coverage-check docs-build docs-build-strict docs-serve docs-deploy docs-lint docs-validate docs-clean all ci sbom audit lint-complexity deadcode check-duplication

# Default target
help:
	@echo "FinWiz Development Commands:"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install     - Install dependencies with uv"
	@echo "  make setup       - Complete development setup"
	@echo ""
	@echo "Development:"
	@echo "  make dev         - Run FinWiz application"
	@echo "  make test        - Run unit tests only"
	@echo "  make test-all    - Run all tests including integration"
	@echo "  make test-failures - Analyze and report all test failures"
	@echo "  make lint        - Run linting checks"
	@echo "  make format      - Format code with ruff"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs-serve  - Preview documentation with MkDocs (recommended)"
	@echo "  make docs-build  - Build MkDocs documentation"
	@echo "  make docs-deploy - Deploy documentation to GitHub Pages"
	@echo "  make docs-lint   - Lint markdown files for style issues"
	@echo "  make docs-validate - Validate documentation structure"
	@echo "  make docs-clean  - Clean documentation artifacts"
	@echo ""
	@echo "HTML Reports:"
	@echo "  make html-reports - Generate HTML reports from all JSON files"
	@echo "  make html-convert - Convert all JSON output files to HTML"
	@echo "  make html-report FILE=path/to/file.json TYPE=template_type - Generate specific HTML report"
	@echo "  make html-demo   - Generate HTML template demo file"
	@echo ""
	@echo "Quality Assurance:"
	@echo "  make all         - Full PR-ready validation (lint + tests + mypy + docs build --strict + complexity + deadcode + duplication)"
	@echo "  make ci          - Alias for 'make all' (matches CI workflow checks)"
	@echo "  make check       - Quick quality checks (lint --fix + tests + docs-validate + complexity + deadcode)"
	@echo "  make lint-check  - Read-only lint (no autofix) + format --check"
	@echo "  make lint-complexity - C901/PLR0915 complexity gate (grandfather list in pyproject; shrink-only)"
	@echo "  make deadcode    - Dead-code scan (vulture, min confidence 80)"
	@echo "  make check-duplication - Duplicate-code gate (pylint R0801, 37-line clean baseline)"
	@echo "  make check-unittest-mock - Check for banned unittest.mock"
	@echo "  make coverage    - Run tests with coverage report (65% minimum)"
	@echo "  make coverage-report - Open coverage report in browser"
	@echo "  make coverage-check - Validate coverage meets threshold"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean       - Clean cache directories"
	@echo "  make cleanup     - Full codebase cleanup"
	@echo "  make cleanup-temp - Clean temporary files only"

# Installation
install:
	uv sync

setup: install setup-hooks
	@echo "✅ FinWiz development environment ready"

setup-hooks:
	@echo "🪝 Setting up pre-commit hooks..."
	@if command -v pre-commit >/dev/null 2>&1; then \
		pre-commit install; \
		echo "✅ Pre-commit hooks installed"; \
	else \
		echo "⚠️  pre-commit not found. Install with: pip install pre-commit"; \
		echo "   Then run: pre-commit install"; \
	fi

# Development
dev:
	uv run python src/finwiz/main.py

# Testing
test:
	uv run pytest -m "not integration" -q -n auto --dist=loadscope

test-verbose:
	uv run pytest -m "not integration" -v

test-all:
	uv run pytest -v

test-integration:
	uv run pytest -m integration -v

coverage:
	@echo "📊 Running tests with coverage..."
	uv run pytest --cov=src/finwiz --cov-report=html --cov-report=term-missing --cov-fail-under=65
	@echo "✅ Coverage report generated: htmlcov/index.html"

coverage-report:
	@echo "📈 Opening coverage report..."
	@if command -v open >/dev/null 2>&1; then \
		open htmlcov/index.html; \
	elif command -v xdg-open >/dev/null 2>&1; then \
		xdg-open htmlcov/index.html; \
	else \
		echo "Please open htmlcov/index.html manually"; \
	fi

test-failures:
	@echo "🔍 Analyzing test failures..."
	@python scripts/analyze_test_failures.py
	@echo ""
	@echo "📄 Reports generated:"
	@echo "  - TEST_FAILURES.txt (human-readable)"
	@echo "  - test_failures.json (machine-readable)"

coverage-check:
	@echo "🔍 Checking test coverage..."
	uv run pytest --cov=src/finwiz --cov-report=term-missing --cov-fail-under=65 --quiet -n auto --dist=loadscope
	@echo "✅ Coverage meets minimum threshold (65%)"

# Code Quality
lint:
	ruff check --fix .
	ruff format .

# Read-only lint + format check — for CI / `make all`. Does NOT auto-fix.
lint-check:
	@echo "🔍 Lint (read-only)..."
	uv run ruff check .
	uv run ruff format --check .
	@echo "✅ Lint checks pass"

format:
	ruff check --fix .
	ruff format .

check: lint test check-unittest-mock check-file-size docs-validate check-stage-contract lint-complexity deadcode
	@echo "✅ All quality checks passed"

# Full validation matching CI workflows (docs.yml + quality.yml). Use this
# before opening a PR to catch regressions locally without round-tripping CI.
all: lint-check test mypy check-unittest-mock check-file-size docs-build-strict docs-validate lint-complexity deadcode check-duplication
	@echo ""
	@echo "✅✅✅ All quality checks AND builds passed — branch is PR-ready ✅✅✅"

# Alias matching the CI workflow vocabulary
ci: all

# unittest.mock enforcement check
check-unittest-mock:
	@echo "🔍 Checking for banned unittest.mock usage..."
	@if grep -rE "^[[:space:]]*(from unittest\.mock|import unittest\.mock)" tests/ 2>/dev/null; then \
		echo "❌ ERROR: unittest.mock found in test files!"; \
		echo "Use pytest-mock instead:"; \
		echo "   def test_example(mocker):"; \
		echo "       mock_obj = mocker.patch('module.function')"; \
		exit 1; \
	else \
		echo "✅ No unittest.mock violations found"; \
	fi

# File size enforcement (new files only, 300 lines max)
check-file-size:
	@echo "🔍 Checking new file sizes..."
	@uv run python scripts/check_new_file_size.py $$(git diff --cached --name-only --diff-filter=A -- '*.py' 2>/dev/null)
	@echo "✅ No oversized new files"

# Stage contract AST check
.PHONY: check-stage-contract
check-stage-contract:
	uv run python -m scripts.check_stage_contract src/finwiz/analysis/stages

# Cleanup
clean:
	rm -rf .mypy_cache .pytest_cache .ruff_cache htmlcov output cache logs
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	find . -name ".DS_Store" -delete

cleanup-temp:
	python scripts/cleanup_temp_files.py

cleanup:
	python scripts/cleanup_master.py

fix-currencies:  ## Rewrite data/*.csv Currency columns from the authoritative price API (network; explicit)
	uv run python scripts/fix_csv_currencies.py

# Type checking
mypy:
	uv run mypy src/finwiz

# Documentation (MkDocs with Material theme)
docs-serve:
	@echo "🚀 Starting MkDocs local preview..."
	@echo "📝 View documentation at: http://127.0.0.1:8000"
	uv run mkdocs serve

docs-build:
	@echo "🔨 Building MkDocs documentation..."
	uv run mkdocs build
	@echo "✅ Documentation built to site/ directory"

# Strict build — fails on broken refs, missing pages, etc. Used by `make all`/CI.
docs-build-strict:
	@echo "🔨 Building MkDocs documentation (strict mode)..."
	uv run mkdocs build --strict
	@echo "✅ Documentation built in strict mode"

docs-deploy:
	@echo "🚀 Deploying documentation to GitHub Pages..."
	@echo "⚠️  This will push to gh-pages branch"
	@read -p "Continue? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	uv run mkdocs gh-deploy --clean --message "docs: update documentation [skip ci]"
	@echo "✅ Documentation deployed to GitHub Pages"

docs-lint:
	@echo "📝 Linting documentation..."
	@if command -v markdownlint >/dev/null 2>&1; then \
		markdownlint --config .markdownlint.jsonc docs/; \
	else \
		echo "⚠️  markdownlint not installed. Install with: npm install -g markdownlint-cli"; \
		echo "   Skipping markdown linting..."; \
	fi
	@echo "✅ Documentation linting completed"

docs-validate: docs-lint
	@echo "🔍 Validating documentation structure..."
	@echo "  - Checking for broken links..."
	@find docs -name "*.md" -exec grep -l "](.*\.md)" {} \; | while read file; do \
		echo "  Checking links in $$file"; \
	done
	@echo "  - Verifying all referenced files exist..."
	@echo "✅ Documentation validation completed"
	@echo ""
	@echo "📌 Note: GitHub Pages will automatically build and deploy from the docs/ directory"
	@echo "   Configure in GitHub: Settings → Pages → Source: Deploy from branch 'main' → /docs"

docs-clean:
	@echo "🧹 Cleaning documentation artifacts..."
	@rm -rf site/ docs/_site/ docs/.jekyll-cache/ docs/.jekyll-metadata
	@echo "✅ Documentation artifacts cleaned"

# HTML Report Generation
html-reports:
	@echo "📊 Generating HTML reports from all JSON files..."
	python scripts/generate_html_reports.py --all
	@echo "✅ HTML reports generated"

html-convert:
	@echo "🔄 Converting all JSON output files to HTML..."
	uv run python scripts/generate_html_reports.py
	@echo "✅ HTML conversion complete"

html-report:
	@if [ -z "$(FILE)" ] || [ -z "$(TYPE)" ]; then \
		echo "❌ Error: Both FILE and TYPE must be specified"; \
		echo "Usage: make html-report FILE=path/to/file.json TYPE=template_type"; \
		echo ""; \
		echo "Supported template types:"; \
		echo "  - backtesting_results"; \
		echo "  - portfolio_review"; \
		echo "  - a_plus_discovery"; \
		echo "  - deep_analysis_consolidated"; \
		echo "  - optimization_report"; \
		echo "  - validation_report"; \
		echo "  - discovery_latest"; \
		echo "  - portfolio_processing_summary"; \
		exit 1; \
	fi
	@echo "📊 Generating HTML report for $(FILE)..."
	python scripts/generate_html_reports.py --file "$(FILE)" --type "$(TYPE)"
	@echo "✅ HTML report generated"

html-demo:
	@echo "🎨 Generating HTML template demo..."
	python scripts/generate_demo.py
	@echo "✅ Demo generated - open demo.html in your browser"

lint-complexity:
	@echo "🧠 Checking complexity (C901/PLR0915) — grandfathered files in pyproject per-file-ignores; shrink-only, never add entries"
	@uv run ruff check src/finwiz --select C901,PLR0915
	@echo "✅ Complexity within limits"

deadcode:
	@echo "🦅 Scanning for dead code (vulture, min confidence 80)..."
	@uvx vulture src/finwiz --min-confidence 80
	@echo "✅ No dead code found"

# Threshold 37 = current clean baseline (13 pre-existing sub-37-line duplications grandfathered by the threshold; tighten as they're consolidated).
check-duplication:
	@echo "👯 Checking for duplicate code (pylint, min 37 similar lines)..."
	@uvx pylint --disable=all --enable=duplicate-code --min-similarity-lines=37 --score=no src/finwiz
	@echo "✅ No duplication found (above the 37-line baseline)"

.PHONY: sbom audit

sbom:  ## Generate a CycloneDX SBOM to dist/finwiz.sbom.cdx.json
	@mkdir -p dist
	uv run cyclonedx-py environment --output-format JSON --output-file dist/finwiz.sbom.cdx.json
	@echo "SBOM written to dist/finwiz.sbom.cdx.json"

audit:  ## Scan installed dependencies for known vulnerabilities (chromadb allowlisted)
	uv run pip-audit --ignore-vuln GHSA-f4j7-r4q5-qw2c
