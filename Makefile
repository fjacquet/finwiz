# FinWiz Development Makefile

.PHONY: help install test lint format clean setup dev check-unittest-mock cleanup

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
	@echo "  make docs-install - Install documentation dependencies"
	@echo "  make docs-serve  - Start MkDocs development server"
	@echo "  make docs-build  - Build static documentation site"
	@echo "  make docs-build-production - Build optimized production site"
	@echo "  make docs-build-fast - Fast build without optimization"
	@echo "  make docs-migrate - Migrate documentation content"
	@echo "  make docs-lint   - Lint markdown files for style issues"
	@echo "  make docs-quality - Check documentation quality metrics"
	@echo "  make docs-validate - Validate documentation and links"
	@echo "  make docs-validate-strict - Strict validation (fails on warnings)"
	@echo "  make docs-validate-build - Validate built site structure"
	@echo "  make docs-validate-build-strict - Strict build validation"
	@echo "  make docs-clean  - Clean documentation build artifacts"
	@echo "  make docs-deploy - Deploy documentation to GitHub Pages"
	@echo "  make docs-deploy-production - Deploy to production with validation"
	@echo "  make docs-deploy-staging - Deploy to staging environment"
	@echo "  make docs-deploy-force - Force deploy to production"
	@echo "  make docs-rollback - Rollback production deployment"
	@echo "  make docs-rollback-staging - Rollback staging deployment"
	@echo "  make docs-deploy-zero-downtime - Zero-downtime production deployment"
	@echo "  make docs-deploy-zero-downtime-staging - Zero-downtime staging deployment"
	@echo "  make docs-status - Check production deployment status"
	@echo "  make docs-status-staging - Check staging deployment status"
	@echo "  make docs-status-json - Get production status as JSON"
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
	@echo "  make check       - Run all quality checks"
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

setup: install docs-install setup-hooks
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
	uv run pytest --cov=src/finwiz --cov-report=term-missing --cov-fail-under=65 --quiet
	@echo "✅ Coverage meets minimum threshold (65%)"

# Code Quality
lint:
	ruff check .

format:
	ruff format .

check: lint test check-unittest-mock docs-validate
	@echo "✅ All quality checks passed"

# unittest.mock enforcement check
check-unittest-mock:
	@echo "🔍 Checking for banned unittest.mock usage..."
	@if grep -r "from unittest.mock" tests/ 2>/dev/null; then \
		echo "❌ ERROR: unittest.mock found in test files!"; \
		echo "✅ Use pytest-mock instead:"; \
		echo "   def test_example(mocker):"; \
		echo "       mock_obj = mocker.patch('module.function')"; \
		exit 1; \
	elif grep -r "import unittest.mock" tests/ 2>/dev/null; then \
		echo "❌ ERROR: unittest.mock found in test files!"; \
		echo "✅ Use pytest-mock instead:"; \
		echo "   def test_example(mocker):"; \
		echo "       mock_obj = mocker.patch('module.function')"; \
		exit 1; \
	else \
		echo "✅ No unittest.mock violations found"; \
	fi

# Cleanup
clean:
	rm -rf .mypy_cache .pytest_cache .ruff_cache htmlcov
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

# Documentation
docs-install:
	@echo "📚 Installing documentation dependencies..."
	uv sync --group docs
	@echo "✅ Documentation dependencies installed"

docs-serve:
	@echo "🚀 Starting MkDocs development server..."
	uv run mkdocs serve --dev-addr 127.0.0.1:8000

docs-build:
	@echo "🔨 Building documentation site..."
	uv run mkdocs build --clean
	@touch site/.nojekyll
	@echo "✅ Created .nojekyll for GitHub Pages compatibility"

docs-build-production:
	@echo "🏭 Building documentation for production..."
	python scripts/build_docs.py
	@echo "✅ Production build completed"

docs-build-fast:
	@echo "⚡ Fast documentation build (no optimization)..."
	python scripts/build_docs.py --no-optimize
	@echo "✅ Fast build completed"

docs-migrate:
	@echo "📄 Migrating documentation content..."
	uv run python scripts/migrate_docs.py --source docs --target docs_new
	@echo "✅ Documentation migration completed"

docs-lint:
	@echo "📝 Linting documentation..."
	@if command -v markdownlint >/dev/null 2>&1; then \
		markdownlint --config .markdownlint.jsonc docs/; \
	else \
		echo "⚠️  markdownlint not installed. Install with: npm install -g markdownlint-cli"; \
	fi
	@echo "✅ Documentation linting completed"

docs-quality:
	@echo "📊 Checking documentation quality..."
	uv run python scripts/check_docs_quality.py

docs-validate: docs-lint docs-quality
	@echo "🔍 Validating documentation..."
	@echo "  - Building documentation (non-strict for now)..."
	uv run mkdocs build --clean
	@echo "  - Validating structure and links..."
	uv run python scripts/validate_docs.py
	@echo "✅ Documentation validation completed"

docs-validate-strict:
	@echo "🔍 Strict documentation validation..."
	@echo "  - Building with strict mode..."
	uv run mkdocs build --strict --clean
	@echo "  - Validating structure and links..."
	uv run python scripts/validate_docs.py
	@echo "✅ Strict documentation validation completed"

docs-validate-build:
	@echo "🔍 Validating built documentation..."
	python scripts/validate_build.py
	@echo "✅ Build validation completed"

docs-validate-build-strict:
	@echo "🔍 Strict build validation (fails on warnings)..."
	python scripts/validate_build.py --fail-on-warnings
	@echo "✅ Strict build validation completed"

docs-clean:
	@echo "🧹 Cleaning documentation build artifacts..."
	rm -rf site/ docs_new/
	@echo "✅ Documentation artifacts cleaned"

docs-deploy:
	@echo "🚀 Deploying documentation to GitHub Pages..."
	uv run mkdocs gh-deploy --force
	@echo "✅ Documentation deployed"

docs-deploy-production:
	@echo "🚀 Deploying documentation to production..."
	python scripts/deploy_docs.py production
	@echo "✅ Production deployment completed"

docs-deploy-staging:
	@echo "🚀 Deploying documentation to staging..."
	python scripts/deploy_docs.py staging
	@echo "✅ Staging deployment completed"

docs-deploy-force:
	@echo "🚀 Force deploying documentation to production..."
	python scripts/deploy_docs.py production --force
	@echo "✅ Force deployment completed"

docs-rollback:
	@echo "🔄 Rolling back production deployment..."
	python scripts/deploy_docs.py production --rollback
	@echo "✅ Rollback completed"

docs-rollback-staging:
	@echo "🔄 Rolling back staging deployment..."
	python scripts/deploy_docs.py staging --rollback
	@echo "✅ Staging rollback completed"

docs-deploy-zero-downtime:
	@echo "🚀 Zero-downtime deployment to production..."
	python scripts/zero_downtime_deploy.py production
	@echo "✅ Zero-downtime deployment completed"

docs-deploy-zero-downtime-staging:
	@echo "🚀 Zero-downtime deployment to staging..."
	python scripts/zero_downtime_deploy.py staging
	@echo "✅ Zero-downtime staging deployment completed"

docs-status:
	@echo "📊 Checking production deployment status..."
	python scripts/monitor_deployment.py production

docs-status-staging:
	@echo "📊 Checking staging deployment status..."
	python scripts/monitor_deployment.py staging

docs-status-json:
	@echo "📊 Getting production status as JSON..."
	python scripts/monitor_deployment.py production --json

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