"""
Shared pytest fixtures and configuration for the document-slides-poc project.

This module provides common fixtures, test data, and utilities that can be used
across all test categories (unit, integration, api, e2e).
"""

import os
import pytest
import tempfile
from pathlib import Path
from typing import Dict, Any, Generator
from unittest.mock import Mock, MagicMock


# Test data fixtures
@pytest.fixture
def sample_document_content() -> str:
    """Sample document content for testing."""
    return """
    # Sample Document
    
    This is a sample document for testing purposes.
    
    ## Section 1
    
    Some content here with **bold** and *italic* text.
    
    ## Section 2
    
    - List item 1
    - List item 2
    - List item 3
    
    ### Subsection
    
    More content with a [link](https://example.com).
    """


@pytest.fixture
def sample_slide_data() -> Dict[str, Any]:
    """Sample slide data structure for testing."""
    return {
        "title": "Sample Slide",
        "content": "This is sample slide content",
        "slide_number": 1,
        "layout": "title_and_content",
        "notes": "These are speaker notes",
        "metadata": {
            "theme": "default",
            "font_size": 24,
            "background_color": "#ffffff"
        }
    }


@pytest.fixture
def sample_presentation_data() -> Dict[str, Any]:
    """Sample presentation data structure for testing."""
    return {
        "title": "Sample Presentation",
        "author": "Test Author",
        "description": "A sample presentation for testing",
        "slides": [
            {
                "title": "Title Slide",
                "content": "Welcome to the presentation",
                "slide_number": 1,
                "layout": "title"
            },
            {
                "title": "Content Slide",
                "content": "This is the main content",
                "slide_number": 2,
                "layout": "title_and_content"
            }
        ],
        "metadata": {
            "theme": "default",
            "total_slides": 2,
            "created_at": "2024-01-01T00:00:00Z"
        }
    }


# File system fixtures
@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_file(temp_dir: Path) -> Generator[Path, None, None]:
    """Create a temporary file for testing."""
    temp_file = temp_dir / "test_file.txt"
    temp_file.write_text("Test content")
    yield temp_file


@pytest.fixture
def sample_document_file(temp_dir: Path, sample_document_content: str) -> Path:
    """Create a sample document file for testing."""
    doc_file = temp_dir / "sample_document.md"
    doc_file.write_text(sample_document_content)
    return doc_file


# Mock fixtures
@pytest.fixture
def mock_file_system() -> Mock:
    """Mock file system operations."""
    mock_fs = Mock()
    mock_fs.read_file.return_value = "mock file content"
    mock_fs.write_file.return_value = True
    mock_fs.file_exists.return_value = True
    return mock_fs


@pytest.fixture
def mock_document_parser() -> Mock:
    """Mock document parser."""
    mock_parser = Mock()
    mock_parser.parse.return_value = {
        "title": "Parsed Document",
        "sections": ["Section 1", "Section 2"],
        "metadata": {"word_count": 100}
    }
    return mock_parser


@pytest.fixture
def mock_slide_generator() -> Mock:
    """Mock slide generator."""
    mock_generator = Mock()
    mock_generator.generate_slides.return_value = [
        {"title": "Slide 1", "content": "Content 1"},
        {"title": "Slide 2", "content": "Content 2"}
    ]
    return mock_generator


@pytest.fixture
def mock_api_client() -> Mock:
    """Mock API client for testing API interactions."""
    mock_client = Mock()
    mock_client.get.return_value = Mock(status_code=200, json=lambda: {"success": True})
    mock_client.post.return_value = Mock(status_code=201, json=lambda: {"id": 1})
    mock_client.put.return_value = Mock(status_code=200, json=lambda: {"updated": True})
    mock_client.delete.return_value = Mock(status_code=204)
    return mock_client


# Environment fixtures
@pytest.fixture
def clean_environment() -> Generator[None, None, None]:
    """Ensure clean environment variables for testing."""
    original_env = os.environ.copy()
    # Clear any environment variables that might affect tests
    test_env_vars = [
        'DEBUG', 'TESTING', 'DATABASE_URL', 'API_KEY', 'SECRET_KEY'
    ]
    for var in test_env_vars:
        if var in os.environ:
            del os.environ[var]
    
    # Set test-specific environment variables
    os.environ['TESTING'] = 'true'
    os.environ['DEBUG'] = 'false'
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


# Configuration fixtures
@pytest.fixture
def test_config() -> Dict[str, Any]:
    """Test configuration settings."""
    return {
        "debug": False,
        "testing": True,
        "database_url": "sqlite:///:memory:",
        "api_timeout": 5,
        "max_file_size": 1024 * 1024,  # 1MB
        "allowed_file_types": [".md", ".txt", ".docx", ".pdf"],
        "slide_templates": ["default", "minimal", "corporate"]
    }


# Database fixtures (if needed)
@pytest.fixture
def mock_database() -> Mock:
    """Mock database connection and operations."""
    mock_db = Mock()
    mock_db.connect.return_value = True
    mock_db.execute.return_value = Mock(fetchall=lambda: [], fetchone=lambda: None)
    mock_db.commit.return_value = None
    mock_db.rollback.return_value = None
    mock_db.close.return_value = None
    return mock_db


# Utility fixtures
@pytest.fixture
def capture_logs(caplog):
    """Fixture to capture and provide access to log messages."""
    return caplog


@pytest.fixture
def mock_datetime():
    """Mock datetime for consistent testing."""
    from unittest.mock import patch
    with patch('datetime.datetime') as mock_dt:
        mock_dt.now.return_value = Mock(isoformat=lambda: "2024-01-01T00:00:00Z")
        yield mock_dt


# Pytest hooks and configuration
def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Create reports directory if it doesn't exist
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    # Create htmlcov directory if it doesn't exist
    htmlcov_dir = Path("htmlcov")
    htmlcov_dir.mkdir(exist_ok=True)


def pytest_runtest_setup(item):
    """Setup before each test runs."""
    # Add any global test setup here
    pass


def pytest_runtest_teardown(item, nextitem):
    """Cleanup after each test runs."""
    # Add any global test cleanup here
    pass


# Custom markers
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add custom markers."""
    for item in items:
        # Auto-mark tests based on their location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "api" in str(item.fspath):
            item.add_marker(pytest.mark.api)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        
        # Mark slow tests
        if hasattr(item, 'function') and getattr(item.function, '_slow_test', False):
            item.add_marker(pytest.mark.slow)