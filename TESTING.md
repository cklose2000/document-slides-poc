# Testing Infrastructure Documentation

This document describes the testing infrastructure for the document-slides-poc project.

## Overview

The testing infrastructure is organized into four main categories:

- **Unit Tests** (`tests/unit/`): Fast, isolated tests for individual components
- **Integration Tests** (`tests/integration/`): Tests for component interactions  
- **API Tests** (`tests/api/`): Tests for API endpoints and external interfaces
- **End-to-End Tests** (`tests/e2e/`): Complete workflow tests

## Quick Start

### Install Test Dependencies

```bash
# Using pip
pip install -r requirements-test.txt

# Using make
make install
```

### Run Tests

```bash
# Run all tests
python run_tests.py
# or
make test

# Run specific test categories
python run_tests.py --type unit
python run_tests.py --type integration
python run_tests.py --type api
python run_tests.py --type e2e

# Using make
make test-unit
make test-integration
make test-api
make test-e2e
```

## Test Runner Usage

The `run_tests.py` script provides a comprehensive interface for running tests:

### Basic Usage

```bash
# Run all tests with coverage
python run_tests.py

# Run specific test type
python run_tests.py --type unit

# Run with verbose output
python run_tests.py --verbose

# Run tests in parallel
python run_tests.py --parallel

# Run tests matching a pattern
python run_tests.py --pattern "test_parser"

# Run tests with specific markers
python run_tests.py --markers "not slow"

# Run last failed tests
python run_tests.py --lf

# Stop on first failure
python run_tests.py --failfast
```

### Special Commands

```bash
# Install test dependencies
python run_tests.py --install

# Run linting checks
python run_tests.py --lint

# Run security checks
python run_tests.py --security

# Clean test artifacts
python run_tests.py --clean

# Show available tests without running
python run_tests.py --collect-only
```

## Test Markers

Tests can be marked with custom markers for better organization:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.api` - API tests
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.slow` - Tests that take more than a few seconds
- `@pytest.mark.external` - Tests requiring external services

### Running Tests by Markers

```bash
# Run only fast tests
python run_tests.py --markers "not slow"

# Run only slow tests  
python run_tests.py --markers "slow"

# Run unit and integration tests
python run_tests.py --markers "unit or integration"

# Skip external service tests
python run_tests.py --markers "not external"
```

## Available Fixtures

The testing infrastructure provides many useful fixtures in `tests/conftest.py`:

### Data Fixtures

- `sample_document_content`: Sample markdown document text
- `sample_slide_data`: Sample slide data structure
- `sample_presentation_data`: Sample presentation data structure

### File System Fixtures

- `temp_dir`: Temporary directory for testing
- `temp_file`: Temporary file with test content
- `sample_document_file`: Sample document file in temp directory

### Mock Fixtures

- `mock_file_system`: Mock file system operations
- `mock_document_parser`: Mock document parser
- `mock_slide_generator`: Mock slide generator
- `mock_api_client`: Mock API client
- `mock_database`: Mock database operations

### Environment Fixtures

- `clean_environment`: Clean environment variables
- `test_config`: Test configuration settings

### Example Usage

```python
import pytest

@pytest.mark.unit
def test_document_parsing(sample_document_content, mock_document_parser):
    """Test document parsing with fixtures."""
    result = mock_document_parser.parse(sample_document_content)
    assert result["title"] == "Parsed Document"
    
@pytest.mark.integration  
def test_file_processing(temp_dir, sample_document_file):
    """Test file processing integration."""
    content = sample_document_file.read_text()
    assert "Sample Document" in content
```

## Configuration

### pytest.ini

The `pytest.ini` file contains the main pytest configuration:

- Test discovery patterns
- Markers definitions
- Coverage settings
- Output formatting
- Timeout settings

### Coverage Configuration

Coverage is configured for:
- Source code in `src/` directory
- HTML reports in `htmlcov/`
- XML reports for CI/CD
- 80% minimum coverage threshold

### Directory Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and configuration
├── test_runner_example.py   # Example tests demonstrating infrastructure
├── unit/                    # Unit tests
│   ├── __init__.py
│   └── test_*.py
├── integration/             # Integration tests  
│   ├── __init__.py
│   └── test_*.py
├── api/                     # API tests
│   ├── __init__.py
│   └── test_*.py
└── e2e/                     # End-to-end tests
    ├── __init__.py
    └── test_*.py
```

## Code Quality

### Linting

The infrastructure includes comprehensive linting:

```bash
# Run all linting checks
python run_tests.py --lint
# or
make lint

# Individual tools
python -m flake8 src/ tests/
python -m black --check src/ tests/
python -m isort --check-only src/ tests/
python -m mypy src/
```

### Security Checks

```bash
# Run security checks
python run_tests.py --security
# or  
make security

# Individual tools
python -m bandit -r src/
python -m safety check
```

### Code Formatting

```bash
# Format code
make format

# Check formatting without changes
make check-format
```

## Continuous Integration

### Using Tox

For testing across multiple Python versions:

```bash
# Install tox
pip install tox

# Run tests across all environments
tox

# Run specific environment
tox -e py311
tox -e flake8
tox -e coverage
```

### Make Targets for CI

```bash
# Full CI pipeline
make ci-test

# Quick CI checks
make ci-quick
```

## Performance Testing

The infrastructure includes performance testing capabilities:

- `pytest-benchmark` for microbenchmarks
- `locust` for load testing
- Performance markers for slow tests

## Best Practices

### Writing Tests

1. **Use appropriate markers**: Mark tests with `@pytest.mark.unit`, etc.
2. **Use fixtures**: Leverage shared fixtures from `conftest.py`
3. **Keep tests isolated**: Unit tests should not depend on external services
4. **Use descriptive names**: Test names should clearly describe what they test
5. **Test edge cases**: Include tests for error conditions and edge cases

### Test Organization

1. **Follow the directory structure**: Put tests in the appropriate category folder
2. **Group related tests**: Use test classes to group related functionality
3. **Use parametrized tests**: For testing multiple inputs with the same logic
4. **Mock external dependencies**: Use mocks for external services and file systems

### Example Test Structure

```python
"""
tests/unit/test_document_parser.py
"""
import pytest
from unittest.mock import Mock

class TestDocumentParser:
    """Tests for document parser functionality."""
    
    @pytest.mark.unit
    def test_parse_markdown_document(self, sample_document_content):
        """Test parsing a markdown document."""
        # Test implementation
        pass
    
    @pytest.mark.unit
    @pytest.mark.parametrize("input_format,expected", [
        ("markdown", "md"),
        ("html", "html"),
        ("text", "txt"),
    ])
    def test_detect_format(self, input_format, expected):
        """Test format detection with various inputs."""
        # Test implementation
        pass
    
    @pytest.mark.unit
    def test_parse_invalid_document(self):
        """Test parsing invalid document raises appropriate error."""
        with pytest.raises(ValueError):
            # Test implementation
            pass
```

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure the `src/` directory is in your Python path
2. **Coverage not working**: Check that source paths are correctly configured
3. **Slow tests**: Use `--markers "not slow"` to skip slow tests during development
4. **Permission errors**: On Windows/WSL, use `python run_tests.py` instead of `./run_tests.py`

### Debug Tips

```bash
# Run with verbose output and no capture for debugging
pytest -v -s tests/unit/test_specific.py

# Run single test method
pytest tests/unit/test_file.py::TestClass::test_method

# Drop into debugger on failure
pytest --pdb tests/

# Show available fixtures
pytest --fixtures tests/
```

## Contributing

When adding new tests:

1. Follow the existing directory structure
2. Use appropriate markers
3. Add fixtures to `conftest.py` if they'll be reused
4. Update this documentation if adding new patterns or conventions
5. Ensure tests pass in isolation and with the full suite

For more information, see the main project documentation.