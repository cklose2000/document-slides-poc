# Makefile for document-slides-poc testing infrastructure
.PHONY: help install test test-unit test-integration test-api test-e2e test-all
.PHONY: test-coverage test-fast test-slow test-parallel test-lf clean lint security
.PHONY: test-collect test-verbose test-quiet format check-format

# Default target
help:
	@echo "Document Slides POC - Testing Infrastructure"
	@echo "============================================="
	@echo ""
	@echo "Available targets:"
	@echo "  help              Show this help message"
	@echo "  install           Install test dependencies"
	@echo "  test              Run all tests with coverage"
	@echo "  test-unit         Run unit tests only"
	@echo "  test-integration  Run integration tests only"
	@echo "  test-api          Run API tests only"
	@echo "  test-e2e          Run end-to-end tests only"
	@echo "  test-all          Run all tests (same as test)"
	@echo "  test-coverage     Run tests with detailed coverage report"
	@echo "  test-fast         Run fast tests only (skip slow ones)"
	@echo "  test-slow         Run slow tests only"
	@echo "  test-parallel     Run tests in parallel"
	@echo "  test-lf           Run last failed tests"
	@echo "  test-collect      Show available tests without running"
	@echo "  test-verbose      Run tests with verbose output"
	@echo "  test-quiet        Run tests with minimal output"
	@echo "  lint              Run code linting checks"
	@echo "  security          Run security checks"
	@echo "  format            Format code with black and isort"
	@echo "  check-format      Check code formatting without making changes"
	@echo "  clean             Clean test artifacts and cache"
	@echo ""
	@echo "Examples:"
	@echo "  make test                    # Run all tests"
	@echo "  make test-unit               # Run unit tests only"
	@echo "  make test-fast               # Skip slow tests"
	@echo "  make test-parallel           # Run tests in parallel"
	@echo "  make lint                    # Check code quality"

# Installation
install:
	@echo "Installing test dependencies..."
	python -m pip install -r requirements-test.txt

# Main test targets
test: test-all

test-all:
	@echo "Running all tests with coverage..."
	python run_tests.py

test-unit:
	@echo "Running unit tests..."
	python run_tests.py --type unit

test-integration:
	@echo "Running integration tests..."
	python run_tests.py --type integration

test-api:
	@echo "Running API tests..."
	python run_tests.py --type api

test-e2e:
	@echo "Running end-to-end tests..."
	python run_tests.py --type e2e

# Test variants
test-coverage:
	@echo "Running tests with detailed coverage report..."
	python run_tests.py --verbose

test-fast:
	@echo "Running fast tests only..."
	python run_tests.py --markers "not slow"

test-slow:
	@echo "Running slow tests only..."
	python run_tests.py --markers "slow"

test-parallel:
	@echo "Running tests in parallel..."
	python run_tests.py --parallel

test-lf:
	@echo "Running last failed tests..."
	python run_tests.py --lf

test-collect:
	@echo "Collecting available tests..."
	python run_tests.py --collect-only

test-verbose:
	@echo "Running tests with verbose output..."
	python run_tests.py --verbose

test-quiet:
	@echo "Running tests with minimal output..."
	python run_tests.py

# Code quality
lint:
	@echo "Running code quality checks..."
	python run_tests.py --lint

security:
	@echo "Running security checks..."
	python run_tests.py --security

format:
	@echo "Formatting code..."
	python -m black src/ tests/
	python -m isort src/ tests/

check-format:
	@echo "Checking code formatting..."
	python -m black --check src/ tests/
	python -m isort --check-only src/ tests/

# Cleanup
clean:
	@echo "Cleaning test artifacts..."
	python run_tests.py --clean

# Continuous Integration targets
ci-test: install test lint security

ci-quick: test-fast lint