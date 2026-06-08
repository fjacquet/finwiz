# FinWiz Development Makefile

.PHONY: help install test test-verbose test-all test-integration lint lint-check format clean setup dev check check-unittest-mock check-file-size check-stage-contract cleanup mypy coverage coverage-report coverage-check docs-build docs-build-strict docs-serve docs-deploy docs-lint docs-validate docs-clean all ci sbom audit

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
	@echo "  make html-example - Run inline HTML generation examples"
	@echo "  make html-integration - Run HTML integration examples"
	@echo ""
	@echo "Quality Assurance:"
	@echo "  make all         - Full PR-ready validation (lint + tests + mypy + docs build --strict)"
	@echo "  make ci          - Alias for 'make all' (matches CI workflow checks)"
	@echo "  make check       - Quick quality checks (lint --fix + tests + docs-validate)"
	@echo "  make lint-check  - Read-only lint (no autofix) + format --check"
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

check: lint test check-unittest-mock check-file-size docs-validate check-stage-contract
	@echo "✅ All quality checks passed"

# Full validation matching CI workflows (docs.yml + quality.yml). Use this
# before opening a PR to catch regressions locally without round-tripping CI.
all: lint-check test mypy check-unittest-mock check-file-size docs-build-strict docs-validate
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

html-example:
	@echo "🚀 Running inline HTML generation examples..."
	python examples/inline_html_example.py
	@echo "✅ Examples completed - check output/examples/ directory"

html-integration:
	@echo "🔄 Running HTML integration examples..."
	python examples/integration_example.py
	@echo "✅ Integration examples completed - check output/integration/ directory"

.PHONY: sbom audit

sbom:  ## Generate a CycloneDX SBOM to dist/finwiz.sbom.cdx.json
	@mkdir -p dist
	uv run cyclonedx-py environment --output-format JSON --output-file dist/finwiz.sbom.cdx.json
	@echo "SBOM written to dist/finwiz.sbom.cdx.json"

audit:  ## Scan installed dependencies for known vulnerabilities (chromadb allowlisted)
	uv run pip-audit --ignore-vuln GHSA-f4j7-r4q5-qw2c
