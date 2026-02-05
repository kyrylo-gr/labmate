.PHONY: help install install-dev test lint format format-check run-ci clean

# Default target
help:
	@echo "Available targets:"
	@echo "  make install          - Install package and dependencies"
	@echo "  make install-dev      - Install package with dev dependencies"
	@echo "  make test             - Run tests with pytest"
	@echo "  make test-cov         - Run tests with coverage report"
	@echo "  make lint             - Run ruff linter"
	@echo "  make lint-fix         - Run ruff linter and auto-fix issues"
	@echo "  make format           - Format code with ruff"
	@echo "  make format-check     - Check code formatting without changes"
	@echo "  make run-ci           - Run all CI checks (tests, lint, format)"
	@echo "  make clean            - Remove build artifacts and cache files"

# Install package and dependencies
install:
	pip install -e .
	pip install -r requirements.txt

# Install package with dev dependencies
install-dev:
	pip install -e .
	pip install -r requirements.txt
	pip install pytest pytest-cov ruff

# Run tests
test:
	pytest

# Run tests with coverage
test-cov:
	pytest --cov=labmate --cov-report=term-missing --cov-report=html

# Run ruff linter
lint:
	ruff check .

# Run ruff linter with auto-fix
lint-fix:
	ruff check . --fix

# Format code with ruff
format:
	ruff format .

# Check formatting without making changes
format-check:
	ruff format --check .

# Run all CI checks (mimics GitHub Actions)
run-ci: test lint format-check
	@echo ""
	@echo "✓ All CI checks passed!"
	@echo "  - Tests: PASSED"
	@echo "  - Linting: PASSED"
	@echo "  - Formatting: PASSED"

# Clean build artifacts and cache
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
