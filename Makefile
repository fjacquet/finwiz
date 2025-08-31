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

test-watch: ## Run tests in watch mode
	uv run pytest-watch tests/unit/

lint: ## Run linting checks
	uv run ruff check .

format: ## Format code
	uv run ruff format .

lint-fix: ## Run linting with auto-fix
	uv run ruff check . --fix

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