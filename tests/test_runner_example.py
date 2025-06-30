"""
Example tests to demonstrate the testing infrastructure.

This file shows how to use the fixtures and markers properly.
Other agents can use this as a reference when creating actual tests.
"""

import pytest
from pathlib import Path


class TestInfrastructureDemo:
    """Demonstrate the testing infrastructure with example tests."""
    
    @pytest.mark.unit
    def test_sample_document_fixture(self, sample_document_content):
        """Test using the sample document fixture."""
        assert "Sample Document" in sample_document_content
        assert "Section 1" in sample_document_content
        assert "Section 2" in sample_document_content
    
    @pytest.mark.unit
    def test_sample_slide_fixture(self, sample_slide_data):
        """Test using the sample slide fixture."""
        assert sample_slide_data["title"] == "Sample Slide"
        assert sample_slide_data["slide_number"] == 1
        assert "metadata" in sample_slide_data
    
    @pytest.mark.unit
    def test_temp_dir_fixture(self, temp_dir):
        """Test using the temporary directory fixture."""
        assert temp_dir.exists()
        assert temp_dir.is_dir()
        
        # Create a test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("Hello, World!")
        
        assert test_file.exists()
        assert test_file.read_text() == "Hello, World!"
    
    @pytest.mark.unit
    def test_mock_fixtures(self, mock_document_parser, mock_slide_generator):
        """Test using mock fixtures."""
        # Test mock document parser
        result = mock_document_parser.parse("dummy content")
        assert result["title"] == "Parsed Document"
        mock_document_parser.parse.assert_called_once_with("dummy content")
        
        # Test mock slide generator
        slides = mock_slide_generator.generate_slides("dummy content")
        assert len(slides) == 2
        assert slides[0]["title"] == "Slide 1"
    
    @pytest.mark.integration
    def test_integration_example(self, sample_document_file, test_config):
        """Example integration test using multiple fixtures."""
        # This would test interaction between components
        assert sample_document_file.exists()
        assert test_config["testing"] is True
        
        # Simulate reading and processing the file
        content = sample_document_file.read_text()
        assert "Sample Document" in content
    
    @pytest.mark.slow
    def test_slow_operation(self):
        """Example of a slow test that gets marked automatically."""
        import time
        time.sleep(0.1)  # Simulate slow operation
        assert True
    
    def test_environment_fixture(self, clean_environment):
        """Test the clean environment fixture."""
        import os
        assert os.environ.get("TESTING") == "true"
        assert os.environ.get("DEBUG") == "false"


class TestMarkerExamples:
    """Examples of using different test markers."""
    
    @pytest.mark.unit
    def test_unit_marker(self):
        """Example unit test."""
        assert 1 + 1 == 2
    
    @pytest.mark.integration
    def test_integration_marker(self):
        """Example integration test."""
        assert True
    
    @pytest.mark.api
    def test_api_marker(self):
        """Example API test."""
        assert True
    
    @pytest.mark.e2e
    def test_e2e_marker(self):
        """Example end-to-end test."""
        assert True
    
    @pytest.mark.slow
    def test_slow_marker(self):
        """Example slow test."""
        assert True
    
    @pytest.mark.external
    def test_external_marker(self):
        """Example test requiring external services."""
        pytest.skip("External service not available")


# Example parametrized test
@pytest.mark.unit
@pytest.mark.parametrize("input_value,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
    (4, 8),
])
def test_parametrized_example(input_value, expected):
    """Example of parametrized test."""
    assert input_value * 2 == expected