# FinWiz Development Commands

.PHONY: help test test-unit test-integration test-coverage lint format install dev-install clean

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	uv sync --no-dev

dev-install: ## Install development dependencies
	uv sync

test: ## Run unit tests (default)
	uv run pytest tests/unit/

test-unit: ## Run unit tests only
	uv run pytest tests/unit/ -v

test-integration: ## Run integration tests
	uv run pytest tests/integration/ -m integration -v

test-all: ## Run all tests including integration
	uv run pytest tests/ -v

test-coverage: ## Run tests with coverage report
	uv run pytest tests/unit/ --cov=src/finwiz --cov-report=html --cov-report=term

check-unittest-mock: ## Check for banned unittest.mock usage
	@echo "🔍 Checking for banned unittest.mock imports..."
	@if grep -r "^[[:space:]]*from unittest\.mock import\|^[[:space:]]*import unittest\.mock" tests/ --include="*.py" -n; then \
		echo ""; \
		echo "❌ ERROR: unittest.mock found in test files!"; \
		echo ""; \
		echo "✅ Use pytest-mock instead:"; \
		echo "   def test_example(mocker):"; \
		echo "       mock_obj = mocker.patch('module.function')"; \
		echo ""; \
		exit 1; \
	else \
		echo "✅ No unittest.mock imports found"; \
	fi

test-watch: ## Run tests in watch mode
	uv run pytest-watch tests/unit/

lint: ## Run linting checks
	uv run ruff check .

format: ## Format code
	uv run ruff format .

lint-fix: ## Run linting with auto-fix
	uv run ruff check . --fix

lint-all: ## Run linting with auto-fix
	make lint-fix
	make format 

quality: ## Run all quality checks
	uv run ruff check . && uv run ruff format . && uv run pytest tests/unit/

clean: ## Clean up generated files
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

run: ## Run the main application
	uv run python src/finwiz/main.py

validate-stock: ## Run stock crew validation
	uv run python tests/validation/stock_crew_validation.py

# Deployment commands
deploy-dev: ## Deploy to development environment
	./scripts/deploy.sh --env development

deploy-staging: ## Deploy to staging environment
	./scripts/deploy.sh --env staging --run-tests

deploy-prod: ## Deploy to production environment
	./scripts/deploy.sh --env production

rollback: ## Interactive rollback to previous version
	./scripts/rollback.sh

rollback-emergency: ## Emergency rollback to latest backup
	./scripts/rollback.sh --emergency

api-server: ## Start the FastAPI server (if rebalancing API is enabled)
	uv run uvicorn finwiz.api.app:app --host 0.0.0.0 --port 8000 --reload

validate-config: ## Validate configuration and API keys
	uv run python -c "from finwiz.utils.configuration_manager import get_configuration_manager; get_configuration_manager().validate_startup_configuration(); print('✅ Configuration valid')"

health-check: ## Check application health status
	curl -f http://localhost:8000/health || echo "API server not running or health check failed"