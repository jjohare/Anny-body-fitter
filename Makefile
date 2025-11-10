# Makefile for Anny Body Fitter
# Provides convenient shortcuts for common development tasks

.PHONY: help install install-dev test lint format type-check security clean docs serve-docs build

# Default target
help:
	@echo "Anny Body Fitter - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install         Install production dependencies"
	@echo "  make install-dev     Install development dependencies"
	@echo "  make install-all     Install all dependencies"
	@echo ""
	@echo "Code Quality:"
	@echo "  make format          Format code with black and isort"
	@echo "  make lint            Run all linters (flake8, ruff)"
	@echo "  make type-check      Run mypy type checking"
	@echo "  make security        Run security scans (bandit, safety)"
	@echo "  make check           Run all quality checks"
	@echo ""
	@echo "Testing:"
	@echo "  make test            Run all tests"
	@echo "  make test-cov        Run tests with coverage report"
	@echo "  make test-fast       Run tests in parallel"
	@echo "  make test-unit       Run only unit tests"
	@echo "  make test-integration Run only integration tests"
	@echo ""
	@echo "Pre-commit:"
	@echo "  make pre-commit-install  Install pre-commit hooks"
	@echo "  make pre-commit-run      Run pre-commit on all files"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs            Build documentation"
	@echo "  make serve-docs      Serve documentation locally"
	@echo ""
	@echo "Build & Deploy:"
	@echo "  make build           Build distribution packages"
	@echo "  make clean           Clean build artifacts"
	@echo ""
	@echo "Development:"
	@echo "  make dev             Run development server"
	@echo "  make db-init         Initialize database"
	@echo "  make db-migrate      Run database migrations"

# Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

install-all: install install-dev
	pip install -e ".[dev,test,docs,examples,warp,frontend,vision]"

# Code formatting
format:
	@echo "Running black..."
	black src tests benchmarks
	@echo "Running isort..."
	isort src tests benchmarks
	@echo "Formatting complete!"

# Linting
lint:
	@echo "Running flake8..."
	flake8 src tests benchmarks --max-line-length=100 --extend-ignore=E203,W503
	@echo "Running ruff..."
	ruff check src tests benchmarks
	@echo "Linting complete!"

# Type checking
type-check:
	@echo "Running mypy..."
	mypy src --ignore-missing-imports --no-strict-optional
	@echo "Type checking complete!"

# Security scanning
security:
	@echo "Running bandit..."
	bandit -r src -c pyproject.toml
	@echo "Running safety..."
	safety check
	@echo "Security scanning complete!"

# All quality checks
check: lint type-check security
	@echo "All quality checks passed!"

# Testing
test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=src --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/index.html"

test-fast:
	pytest tests/ -n auto

test-unit:
	pytest tests/ -m "not integration" -v

test-integration:
	pytest tests/ -m integration -v

# Pre-commit
pre-commit-install:
	pre-commit install
	@echo "Pre-commit hooks installed!"

pre-commit-run:
	pre-commit run --all-files

# Documentation
docs:
	cd docs && make html
	@echo "Documentation built in docs/_build/html/index.html"

serve-docs:
	cd docs/_build/html && python -m http.server 8080

# Build
build:
	python -m build
	@echo "Build artifacts created in dist/"

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "Cleaned build artifacts!"

# Development
dev:
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

db-init:
	python scripts/init_db.py

db-migrate:
	alembic upgrade head

# Docker
docker-build:
	docker build -t anny-fitter:latest .

docker-run:
	docker run -p 8000:8000 anny-fitter:latest

docker-compose-up:
	docker-compose up -d

docker-compose-down:
	docker-compose down

# CI/CD helpers
ci-install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

ci-test: check test-cov
	@echo "CI tests passed!"
