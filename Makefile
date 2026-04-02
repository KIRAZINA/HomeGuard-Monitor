.PHONY: help install install-dev lint format test test-cov test-fast clean docker-up docker-down db-migrate db-seed
.DEFAULT_GOAL := help

# Variables
PYTHON := python
PIP := pip
PYTEST := pytest
BLACK := black
RUFF := ruff
ISORT := isort
MYPY := mypy

# Directories
APP_DIR := backend/app
TESTS_DIR := backend/tests

help: ## Show this help message
	@echo "HomeGuard Monitor - Development Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'
	@echo ""

install: ## Install production dependencies
	$(PIP) install -r backend/requirements.txt

install-dev: ## Install development dependencies
	$(PIP) install -e "backend/[dev]"

lint: ## Run all linters
	@echo "Running code quality checks..."
	$(BLACK) --check $(APP_DIR)
	$(ISORT) --check-only $(APP_DIR)
	$(RUFF) check $(APP_DIR)
	$(MYPY) $(APP_DIR)
	@echo "✓ All checks passed!"

format: ## Format code
	@echo "Formatting code..."
	$(BLACK) $(APP_DIR)
	$(ISORT) $(APP_DIR)
	$(RUFF) check --fix $(APP_DIR)
	@echo "✓ Code formatted!"

format-check: ## Check formatting without changes
	$(BLACK) --check $(APP_DIR)
	$(ISORT) --check-only $(APP_DIR)

test: ## Run all tests
	$(PYTEST) $(TESTS_DIR) -v

test-cov: ## Run tests with coverage report
	$(PYTEST) $(TESTS_DIR) -v --cov=$(APP_DIR) --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/index.html"

test-fast: ## Run tests without slow tests
	$(PYTEST) $(TESTS_DIR) -v -m "not slow"

test-unit: ## Run only unit tests
	$(PYTEST) $(TESTS_DIR) -v -m "unit"

test-integration: ## Run only integration tests
	$(PYTEST) $(TESTS_DIR) -v -m "integration"

test-watch: ## Run tests in watch mode (requires pytest-watch)
	ptw $(TESTS_DIR) -- -v

clean: ## Clean up cache and build artifacts
	@echo "Cleaning up..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.egg-info" -delete
	@echo "✓ Cleaned up!"

docker-build: ## Build Docker images
	docker-compose build

docker-up: ## Start services with Docker Compose
	docker-compose up -d

docker-down: ## Stop services
	docker-compose down

docker-logs: ## Stream service logs
	docker-compose logs -f

docker-shell: ## Open shell in backend container
	docker-compose exec backend /bin/bash

db-migrate: ## Run database migrations
	alembic upgrade head

db-migrate-create: ## Create new migration (usage: make db-migrate-create MSG="add users table")
	alembic revision --autogenerate -m "$(MSG)"

db-rollback: ## Rollback one migration
	alembic downgrade -1

db-reset: ## Reset database (WARNING: deletes all data)
	alembic downgrade base
	alembic upgrade head

dev-server: ## Start development server
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

dev-celery: ## Start Celery worker
	celery -A app.celery_app worker --loglevel=info

dev-celery-beat: ## Start Celery beat scheduler
	celery -A app.celery_app beat --loglevel=info

dev-monitor: ## Start Celery events monitor
	celery -A app.celery_app events

all-checks: format lint test-cov ## Run all checks (format, lint, tests with coverage)

ci: lint test ## Run CI checks (lint and tests)

pre-commit-install: ## Install pre-commit hooks
	pre-commit install

pre-commit-run: ## Run pre-commit on all files
	pre-commit run --all-files

security-check: ## Run security checks
	bandit -r $(APP_DIR) -c .bandit

dependency-check: ## Check for outdated dependencies
	$(PIP) list --outdated

type-check: ## Run type checking
	$(MYPY) $(APP_DIR) --show-error-codes

requirements-freeze: ## Freeze current environment
	$(PIP) freeze > backend/requirements-locked.txt
	@echo "Requirements frozen to requirements-locked.txt"

shell: ## Start Python shell with app context
	PYTHONPATH=. $(PYTHON) -i -m IPython -c "from app.main import app; print('App loaded'); print(dir())"

version: ## Show project version
	@grep -E "version|VERSION" backend/requirements.txt pyproject.toml | head -1 || echo "Version not found"

info: ## Show project information
	@echo "HomeGuard Monitor - Project Information"
	@echo ""
	@echo "Python Version: $$($(PYTHON) --version)"
	@echo "Pip Version: $$($(PIP) --version)"
	@echo ""
	@echo "Installed Tools:"
	@which black isort ruff mypy pytest || true
	@echo ""
