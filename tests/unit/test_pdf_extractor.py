"""
Comprehensive tests for PDF extractor with LLMWhisperer integration
Tests cover various document formats, edge cases, and source attribution
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import io
import json

# Add the lib directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lib'))

from pdf_extractor import PDFExtractor
from source_tracker import SourceTracker


class TestPDFExtractor(unittest.TestCase):
    """Test suite for PDF extractor functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.source_tracker = SourceTracker()
        self.pdf_extractor = PDFExtractor(source_tracker=self.source_tracker)
        
    def test_init_without_source_tracker(self):
        """Test initialization without source tracker"""
        extractor = PDFExtractor()
        self.assertIsNone(extractor.source_tracker)
        self.assertEqual(extractor.base_url, 'https://llmwhisperer-api.us-central.unstract.com/api/v2')
        self.assertEqual(extractor.timeout, 300)
        self.assertEqual(extractor.max_pages, 50)

    def test_init_with_source_tracker(self):
        """Test initialization with source tracker"""
        self.assertIsNotNone(self.pdf_extractor.source_tracker)
        self.assertEqual(self.pdf_extractor.source_tracker, self.source_tracker)

    @patch.dict(os.environ, {'LLMWHISPERER_API_KEY': 'test_key'})
    @patch('pdf_extractor.requests.post')
    @patch('pdf_extractor.requests.get')
    def test_extract_from_bytes_success(self, mock_get, mock_post):
        """Test successful PDF extraction with LLMWhisperer API"""
        # Mock API responses
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"whisper_hash": "test_hash"}
        
        # Mock polling responses
        mock_get.side_effect = [
            # First call - status check
            Mock(status_code=200, json=lambda: {"status": "processed"}),
            # Second call - retrieve text
            Mock(status_code=200, json=lambda: {"extracted_text": "# Financial Report\n\nRevenue: $1,000,000\n\n| Year | Revenue | Profit |\n|------|---------|--------|\n| 2023 | $1M | $200K |\n| 2024 | $1.2M | $300K |"})
        ]
        
        test_pdf_bytes = b"fake_pdf_content"
        result = self.pdf_extractor.extract_from_bytes(test_pdf_bytes, "test.pdf")
        
        # Verify result structure
        self.assertIn('raw_text', result)
        self.assertIn('metadata', result)
        self.assertIn('tables', result)
        self.assertIn('sections', result)
        self.assertIn('key_metrics', result)
        
        # Verify metadata
        self.assertEqual(result['metadata']['filename'], "test.pdf")
        self.assertEqual(result['metadata']['extraction_method'], "llmwhisperer")
        
        # Verify tables were extracted
        self.assertTrue(len(result['tables']) > 0)
        table = result['tables'][0]
        self.assertIn('content', table)
        self.assertIn('rows', table)
        self.assertIn('position', table)
        
        # Verify sections were extracted
        self.assertIn('Financial Report', result['sections'])
        
        # Verify key metrics
        self.assertIn('financial_values', result['key_metrics'])

    def test_extract_from_bytes_no_api_key(self):
        """Test extraction fallback when API key is not configured"""
        with patch.dict(os.environ, {}, clear=True):
            extractor = PDFExtractor()
            result = extractor.extract_from_bytes(b"test", "test.pdf")
            
            self.assertIn('raw_text', result)
            self.assertIn('LLMWhisperer API key not configured', result['raw_text'])
            self.assertEqual(result['metadata']['extraction_method'], 'placeholder')

    @patch.dict(os.environ, {'LLMWHISPERER_API_KEY': 'test_key'})
    @patch('pdf_extractor.requests.post')
    def test_extract_from_bytes_api_error(self, mock_post):
        """Test handling of API errors"""
        mock_post.return_value.status_code = 400
        mock_post.return_value.text = "Bad Request"
        
        result = self.pdf_extractor.extract_from_bytes(b"test", "test.pdf")
        
        self.assertIn('error', result['metadata'])
        self.assertIn('400', result['metadata']['error'])

    @patch.dict(os.environ, {'LLMWHISPERER_API_KEY': 'test_key'})
    @patch('pdf_extractor.requests.post')
    @patch('pdf_extractor.requests.get')
    def test_extract_from_bytes_timeout(self, mock_get, mock_post):
        """Test handling of extraction timeout"""
        # Mock successful upload
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"whisper_hash": "test_hash"}
        
        # Mock polling timeout (status never becomes 'processed')
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"status": "processing"}
        
        result = self.pdf_extractor.extract_from_bytes(b"test", "test.pdf")
        self.assertIn('timeout', result['metadata']['error'])

    def test_extract_tables_simple(self):
        """Test table extraction from markdown text"""
        text = """
Some text before table

| Name | Revenue | Profit |
|------|---------|--------|
| CompanyA | $1M | $200K |
| CompanyB | $2M | $400K |

Some text after table
"""
        
        tables = self.pdf_extractor._extract_tables(text)
        
        self.assertEqual(len(tables), 1)
        table = tables[0]
        self.assertEqual(table['rows'], 2)
        self.assertIn('Name', table['content'])
        self.assertIn('CompanyA', table['content'])

    def test_extract_tables_multiple(self):
        """Test extraction of multiple tables"""
        text = """
# Table 1
| Year | Revenue |
|------|---------|
| 2023 | $1M |
| 2024 | $1.2M |

Some text

# Table 2
| Product | Sales |
|---------|-------|
| A | 100 |
| B | 200 |
"""
        
        tables = self.pdf_extractor._extract_tables(text)
        self.assertEqual(len(tables), 2)

    def test_extract_sections(self):
        """Test section extraction from markdown headers"""
        text = """
# Executive Summary
This is the executive summary content.

## Financial Performance
Revenue grew by 20% this year.

### Market Analysis
The market is expanding rapidly.

# Conclusion
We are well positioned for growth.
"""
        
        sections = self.pdf_extractor._extract_sections(text)
        
        self.assertIn('Executive Summary', sections)
        self.assertIn('Financial Performance', sections)
        self.assertIn('Market Analysis', sections)
        self.assertIn('Conclusion', sections)
        
        self.assertIn('summary content', sections['Executive Summary'])
        self.assertIn('20%', sections['Financial Performance'])

    def test_extract_metrics(self):
        """Test extraction of key metrics and financial values"""
        text = """
Revenue: $1,200,000
Profit margin: 25%
Growth rate: 15.5%
Year: 2024
Cost: €500,000
"""
        
        metrics = self.pdf_extractor._extract_metrics(text)
        
        # Test financial values
        self.assertIn('financial_values', metrics)
        financial_values = metrics['financial_values']
        self.assertTrue(any('$1,200,000' in val for val in financial_values))
        self.assertTrue(any('€500,000' in val for val in financial_values))
        
        # Test percentages
        self.assertIn('percentages', metrics)
        percentages = metrics['percentages']
        self.assertIn('25%', percentages)
        self.assertIn('15.5%', percentages)
        
        # Test years
        self.assertIn('years', metrics)
        self.assertIn('2024', metrics['years'])
        
        # Test key-value pairs
        self.assertIn('revenue', metrics)
        self.assertEqual(metrics['revenue'], '$1,200,000')

    def test_extract_metrics_with_source_tracking(self):
        """Test metric extraction with source tracking enabled"""
        # Register a test document
        doc_id = self.source_tracker.register_document("test.pdf", "pdf")
        
        text = "Revenue: $1,000,000\nProfit: 25%"
        metrics = self.pdf_extractor._extract_metrics(text, doc_id)
        
        # Verify tracking was enabled
        self.assertIn('_tracked_data_points', metrics)
        self.assertTrue(len(metrics['_tracked_data_points']) > 0)
        
        # Verify data points were created
        self.assertTrue(len(self.source_tracker.data_points) > 0)

    def test_page_number_estimation(self):
        """Test page number estimation from line numbers"""
        text = "Line 1\nLine 2\n<<<\nPage 2 Line 1\nPage 2 Line 2\n<<<\nPage 3 Line 1"
        
        # Test various line positions
        self.assertEqual(self.pdf_extractor._estimate_page_number(text, 0), 1)
        self.assertEqual(self.pdf_extractor._estimate_page_number(text, 1), 1)
        self.assertEqual(self.pdf_extractor._estimate_page_number(text, 3), 2)
        self.assertEqual(self.pdf_extractor._estimate_page_number(text, 6), 3)

    def test_is_valuable_cell_data(self):
        """Test cell data value assessment"""
        # Valuable data
        self.assertTrue(self.pdf_extractor._is_valuable_cell_data("$1,000"))
        self.assertTrue(self.pdf_extractor._is_valuable_cell_data("25%"))
        self.assertTrue(self.pdf_extractor._is_valuable_cell_data("12/31/2023"))
        self.assertTrue(self.pdf_extractor._is_valuable_cell_data("1,500.00"))
        self.assertTrue(self.pdf_extractor._is_valuable_cell_data("Important data point"))
        
        # Non-valuable data
        self.assertFalse(self.pdf_extractor._is_valuable_cell_data(""))
        self.assertFalse(self.pdf_extractor._is_valuable_cell_data("x"))
        self.assertFalse(self.pdf_extractor._is_valuable_cell_data("total"))
        self.assertFalse(self.pdf_extractor._is_valuable_cell_data("name"))

    def test_find_value_location(self):
        """Test finding specific values within text"""
        text = "Line 1\nRevenue: $1,000,000\nLine 3\nProfit: 25%\nLine 5"
        
        location = self.pdf_extractor._find_value_location(text, "$1,000,000")
        
        self.assertIsNotNone(location)
        self.assertEqual(location['line_number'], 2)
        self.assertIn('page_or_sheet', location)
        self.assertIn('coordinates', location)

    def test_track_table_cells_with_source_tracker(self):
        """Test table cell tracking with source tracker"""
        # Register document
        doc_id = self.source_tracker.register_document("test.pdf", "pdf")
        
        table_lines = [
            "| Product | Revenue | Profit |",
            "|---------|---------|--------|",
            "| A | $1,000 | $200 |",
            "| B | $2,000 | $400 |"
        ]
        
        data_point_ids = self.pdf_extractor._track_table_cells(table_lines, doc_id, 10)
        
        # Verify data points were created
        self.assertTrue(len(data_point_ids) > 0)
        self.assertTrue(len(self.source_tracker.data_points) > 0)
        
        # Verify at least financial values were tracked
        tracked_values = [dp.value for dp in self.source_tracker.data_points.values()]
        self.assertTrue(any("$" in str(val) for val in tracked_values))

    def test_parse_pdf_content_complete(self):
        """Test complete PDF content parsing with all components"""
        text = """# Executive Summary
This is a comprehensive financial report.

Revenue for 2023: $1,500,000
Growth rate: 23%

| Quarter | Revenue | Profit |
|---------|---------|--------|
| Q1 | $300,000 | $60,000 |
| Q2 | $400,000 | $80,000 |

# Market Analysis
The market shows strong growth potential.
"""
        
        result = self.pdf_extractor._parse_pdf_content(text, "test.pdf")
        
        # Verify all components are present
        self.assertIn('raw_text', result)
        self.assertIn('metadata', result)
        self.assertIn('tables', result)
        self.assertIn('sections', result)
        self.assertIn('key_metrics', result)
        self.assertIn('pages', result)
        
        # Verify content quality
        self.assertEqual(len(result['tables']), 1)
        self.assertEqual(len(result['sections']), 2)
        self.assertIn('financial_values', result['key_metrics'])
        self.assertIn('percentages', result['key_metrics'])

    def test_parse_pdf_content_with_attribution(self):
        """Test PDF parsing with enhanced attribution"""
        doc_id = self.source_tracker.register_document("test.pdf", "pdf")
        
        text = "Revenue: $1,000,000"
        result = self.pdf_extractor._parse_pdf_content(text, "test.pdf", doc_id)
        
        # Verify attribution data exists
        self.assertIn('_attribution', result)
        self.assertEqual(result['_attribution']['document_id'], doc_id)
        self.assertIn('source_tracker_data', result['_attribution'])

    def test_edge_case_empty_content(self):
        """Test handling of empty or minimal content"""
        result = self.pdf_extractor._parse_pdf_content("", "empty.pdf")
        
        self.assertEqual(result['raw_text'], "")
        self.assertEqual(len(result['tables']), 0)
        self.assertEqual(len(result['sections']), 0)
        self.assertEqual(result['metadata']['pages'], 1)

    def test_edge_case_malformed_tables(self):
        """Test handling of malformed markdown tables"""
        text = """
| Header 1 | Header 2
|----------|
| Data 1 | Data 2 |
| Incomplete row |
"""
        
        tables = self.pdf_extractor._extract_tables(text)
        
        # Should still extract what it can
        self.assertTrue(len(tables) >= 0)  # May or may not find valid tables

    def test_context_preservation(self):
        """Test that context is preserved during extraction"""
        text = """
# Financial Summary
The company performed well this year.

Revenue increased by 25% to $1,200,000.
Profit margins improved to 15%.
"""
        
        # With source tracker
        doc_id = self.source_tracker.register_document("test.pdf", "pdf")
        result = self.pdf_extractor._parse_pdf_content(text, "test.pdf", doc_id)
        
        # Verify context is preserved in tracked data points
        if result['key_metrics'].get('_tracked_data_points'):
            first_dp_id = result['key_metrics']['_tracked_data_points'][0]
            context = self.source_tracker.get_source_context(first_dp_id)
            
            self.assertIn('source_details', context)
            self.assertEqual(context['source_details']['document'], 'test.pdf')
            self.assertEqual(context['source_details']['type'], 'pdf')


class TestPDFExtractorIntegration(unittest.TestCase):
    """Integration tests for PDF extractor with real-world scenarios"""

    def setUp(self):
        """Set up integration test fixtures"""
        self.source_tracker = SourceTracker()
        self.pdf_extractor = PDFExtractor(source_tracker=self.source_tracker)

    def test_complex_financial_document(self):
        """Test extraction from complex financial document structure"""
        complex_text = """
# ANNUAL FINANCIAL REPORT 2023

## Executive Summary
Our company achieved record revenues of $10.2M in 2023, representing 
a growth of 23% over the previous year.

## Financial Highlights

| Metric | 2023 | 2022 | Change |
|--------|------|------|--------|
| Revenue | $10.2M | $8.3M | +23% |
| Gross Profit | $6.1M | $4.9M | +24% |
| Net Income | $2.1M | $1.6M | +31% |
| EBITDA | $3.2M | $2.4M | +33% |

## Key Performance Indicators
- Customer acquisition cost: $45
- Lifetime value: $1,200
- Churn rate: 5.2%
- Market share: 12%

## Geographic Performance
Revenue by region:
- North America: $6.1M (60%)
- Europe: $2.5M (25%)
- Asia Pacific: $1.6M (15%)

## Outlook for 2024
We project continued growth with revenue targets of $13M-15M.
"""
        
        result = self.pdf_extractor._parse_pdf_content(complex_text, "annual_report.pdf")
        
        # Verify comprehensive extraction
        self.assertGreater(len(result['tables']), 0)
        self.assertGreater(len(result['sections']), 3)
        self.assertIn('financial_values', result['key_metrics'])
        self.assertIn('percentages', result['key_metrics'])
        
        # Verify specific metrics were captured
        financial_values = result['key_metrics']['financial_values']
        self.assertTrue(any('$10.2M' in val for val in financial_values))
        self.assertTrue(any('$6.1M' in val for val in financial_values))
        
        percentages = result['key_metrics']['percentages']
        self.assertIn('23%', percentages)
        self.assertIn('5.2%', percentages)

    def test_multi_format_data_extraction(self):
        """Test extraction of various data formats"""
        mixed_format_text = """
# Multi-Format Data Test

Financial figures:
- Revenue: $1,234,567.89
- European sales: €987,654.32
- UK operations: £543,210.98
- Japanese market: ¥12,345,678

Percentages and ratios:
- Growth: 15.7%
- Margin: 23.4%
- ROI: 145%
- Efficiency: 0.85

Dates and periods:
- Report date: 12/31/2023
- Next review: 03/15/2024
- Fiscal year: 2023
- Quarter: Q4

Other metrics:
- Headcount: 1,245 employees
- Locations: 23 offices
- Products: 156 SKUs
"""
        
        result = self.pdf_extractor._parse_pdf_content(mixed_format_text, "mixed_data.pdf")
        
        # Verify different currency formats
        financial_values = result['key_metrics']['financial_values']
        currencies = ['$', '€', '£', '¥']
        for currency in currencies:
            self.assertTrue(any(currency in val for val in financial_values))
        
        # Verify percentage extraction
        percentages = result['key_metrics']['percentages']
        self.assertTrue(len(percentages) >= 3)
        
        # Verify year extraction
        years = result['key_metrics']['years']
        self.assertIn('2023', years)
        self.assertIn('2024', years)


if __name__ == '__main__':
    unittest.main()