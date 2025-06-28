import requests
import json
import os
import time
import re
from typing import Dict, Any, Optional, List, Tuple
try:
    from .source_tracker import SourceTracker
except ImportError:
    from source_tracker import SourceTracker

class PDFExtractor:
    """Extract text and structured content from PDFs using LLMWhisperer API"""
    
    def __init__(self, source_tracker: Optional[SourceTracker] = None):
        """Initialize PDF extractor with optional source tracker for enhanced attribution"""
        self.api_key = os.getenv('LLMWHISPERER_API_KEY')
        self.base_url = os.getenv('LLMWHISPERER_BASE_URL', 'https://llmwhisperer-api.us-central.unstract.com/api/v2')
        self.timeout = int(os.getenv('LLMWHISPERER_TIMEOUT', '300'))
        self.max_pages = int(os.getenv('LLMWHISPERER_MAX_PAGES', '50'))
        self.processing_mode = os.getenv('LLMWHISPERER_PROCESSING_MODE', 'ocr')
        self.source_tracker = source_tracker
        
    def extract_from_bytes(self, pdf_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Extract content from PDF bytes using LLMWhisperer"""
        
        if not self.api_key:
            # Fallback if no API key
            return {
                "raw_text": f"PDF content from {filename} (LLMWhisperer API key not configured)",
                "metadata": {
                    "filename": filename,
                    "pages": 0,
                    "extraction_method": "placeholder"
                },
                "tables": [],
                "sections": {}
            }
        
        try:
            # Upload the PDF to LLMWhisperer
            headers = {
                "unstract-key": self.api_key
            }
            
            # Upload file
            files = {
                'file': (filename, pdf_bytes, 'application/pdf')
            }
            
            # Parameters for optimal extraction
            params = {
                "mode": "high_quality",
                "processing_mode": self.processing_mode,
                "output_format": "markdown",
                "page_seperator": "<<<",
                "force_text_processing": "true",
                "text_processing_mode": "combination",
                "max_pages": self.max_pages
            }
            
            response = requests.post(
                f"{self.base_url}/whisper",
                headers=headers,
                files=files,
                data=params,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                whisper_hash = result.get("whisper_hash")
                
                # Poll for results
                extracted_text = self._poll_for_results(whisper_hash)
                
                if extracted_text:
                    # Register document with source tracker if available
                    document_id = None
                    if self.source_tracker:
                        document_id = self.source_tracker.register_document(
                            filename,
                            'pdf',
                            {'extraction_method': 'llmwhisperer', 'processing_mode': self.processing_mode}
                        )
                    
                    # Parse the extracted content with source tracking
                    return self._parse_pdf_content(extracted_text, filename, document_id)
                else:
                    return {
                        "raw_text": f"Failed to extract content from {filename}",
                        "metadata": {"filename": filename, "error": "Extraction timeout"},
                        "tables": [],
                        "sections": {}
                    }
                    
            else:
                error_msg = f"LLMWhisperer API error: {response.status_code}"
                if response.text:
                    error_msg += f" - {response.text}"
                    
                return {
                    "raw_text": f"Error extracting {filename}: {error_msg}",
                    "metadata": {"filename": filename, "error": error_msg},
                    "tables": [],
                    "sections": {}
                }
                
        except Exception as e:
            return {
                "raw_text": f"Error processing {filename}: {str(e)}",
                "metadata": {"filename": filename, "error": str(e)},
                "tables": [],
                "sections": {}
            }
    
    def _poll_for_results(self, whisper_hash: str, max_attempts: int = 30) -> Optional[str]:
        """Poll LLMWhisperer for extraction results"""
        
        headers = {
            "unstract-key": self.api_key
        }
        
        for attempt in range(max_attempts):
            try:
                response = requests.get(
                    f"{self.base_url}/whisper-status",
                    headers=headers,
                    params={"whisper_hash": whisper_hash}
                )
                
                if response.status_code == 200:
                    status_data = response.json()
                    status = status_data.get("status", "")
                    
                    if status == "processed":
                        # Retrieve the extracted text
                        text_response = requests.get(
                            f"{self.base_url}/whisper-retrieve",
                            headers=headers,
                            params={"whisper_hash": whisper_hash}
                        )
                        
                        if text_response.status_code == 200:
                            return text_response.json().get("extracted_text", "")
                            
                    elif status == "failed":
                        return None
                        
                # Wait before next poll
                time.sleep(2)
                
            except Exception:
                pass
                
        return None
    
    def _parse_pdf_content(self, text: str, filename: str, document_id: Optional[str] = None) -> Dict[str, Any]:
        """Parse extracted PDF text into structured format with enhanced source tracking"""
        
        # Split by pages if page separator exists
        pages = text.split("<<<") if "<<<" in text else [text]
        
        # Extract tables (look for markdown table patterns)
        tables = self._extract_tables(text, document_id)
        
        # Extract sections based on markdown headers
        sections = self._extract_sections(text, document_id)
        
        # Extract key metrics and numbers with source tracking
        metrics = self._extract_metrics(text, document_id, pages)
        
        result = {
            "raw_text": text,
            "metadata": {
                "filename": filename,
                "pages": len(pages),
                "extraction_method": "llmwhisperer",
                "total_characters": len(text)
            },
            "tables": tables,
            "sections": sections,
            "key_metrics": metrics,
            "pages": pages
        }
        
        # Add enhanced attribution data if source tracker is available
        if self.source_tracker and document_id:
            result['_attribution'] = {
                'document_id': document_id,
                'source_tracker_data': self.source_tracker.export_attribution_data()
            }
        
        return result
    
    def _extract_tables(self, text: str, document_id: Optional[str] = None) -> list:
        """Extract markdown tables from text with enhanced source tracking"""
        tables = []
        lines = text.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Check if this looks like a markdown table header
            if '|' in line and i + 1 < len(lines) and '|' in lines[i + 1] and '-' in lines[i + 1]:
                # Found a table, extract it
                table_lines = [line]
                table_start_line = i
                i += 1
                
                # Get all table rows
                while i < len(lines) and '|' in lines[i]:
                    table_lines.append(lines[i])
                    i += 1
                
                if len(table_lines) > 2:  # Header + separator + at least one data row
                    table_content = '\n'.join(table_lines)
                    
                    # Extract individual table cells and track them
                    table_data_points = []
                    if self.source_tracker and document_id:
                        table_data_points = self._track_table_cells(
                            table_lines, document_id, table_start_line
                        )
                    
                    # Determine which page this table is on
                    page_number = self._estimate_page_number(text, table_start_line)
                    
                    tables.append({
                        "content": table_content,
                        "rows": len(table_lines) - 2,  # Exclude header and separator
                        "position": table_start_line,
                        "line_range": f"{table_start_line}-{i-1}",
                        "page_number": page_number,
                        "data_point_ids": table_data_points
                    })
            else:
                i += 1
                
        return tables
    
    def _extract_sections(self, text: str, document_id: Optional[str] = None) -> Dict[str, str]:
        """Extract sections based on markdown headers with enhanced source tracking"""
        sections = {}
        lines = text.split('\n')
        
        current_section = None
        section_content = []
        section_start_line = 0
        
        for line_num, line in enumerate(lines):
            # Check for markdown headers
            if line.startswith('#'):
                # Save previous section with source tracking
                if current_section:
                    section_text = '\n'.join(section_content).strip()
                    sections[current_section] = section_text
                    
                    # Track section as a data point if it contains valuable content
                    if self.source_tracker and document_id and len(section_text) > 50:
                        page_number = self._estimate_page_number(text, section_start_line)
                        
                        self.source_tracker.track_data_point(
                            value=section_text[:200] + "..." if len(section_text) > 200 else section_text,
                            document_id=document_id,
                            location_details={
                                'page_or_sheet': f"Page {page_number}",
                                'cell_or_section': current_section,
                                'line_number': section_start_line,
                                'coordinates': {'start_line': section_start_line, 'end_line': line_num - 1},
                                'extraction_method': 'markdown_headers'
                            },
                            confidence=0.9,
                            context=f"Section header: {current_section}"
                        )
                
                # Start new section
                current_section = line.strip('#').strip()
                section_content = []
                section_start_line = line_num
            else:
                section_content.append(line)
        
        # Save last section
        if current_section:
            section_text = '\n'.join(section_content).strip()
            sections[current_section] = section_text
            
            # Track last section
            if self.source_tracker and document_id and len(section_text) > 50:
                page_number = self._estimate_page_number(text, section_start_line)
                
                self.source_tracker.track_data_point(
                    value=section_text[:200] + "..." if len(section_text) > 200 else section_text,
                    document_id=document_id,
                    location_details={
                        'page_or_sheet': f"Page {page_number}",
                        'cell_or_section': current_section,
                        'line_number': section_start_line,
                        'coordinates': {'start_line': section_start_line, 'end_line': len(lines) - 1},
                        'extraction_method': 'markdown_headers'
                    },
                    confidence=0.9,
                    context=f"Section header: {current_section}"
                )
            
        return sections
    
    def _extract_metrics(self, text: str, document_id: Optional[str] = None, 
                        pages: Optional[List[str]] = None) -> Dict[str, Any]:
        """Extract key metrics and numbers from text with enhanced source tracking"""
        metrics = {}
        tracked_metrics = []
        
        # Pattern for financial metrics (e.g., $1.2M, $45,000, €1.5B)
        financial_pattern = r'[\$€£¥]\s*[\d,]+\.?\d*\s*[BMK]?'
        financial_matches = list(set(re.findall(financial_pattern, text)))
        if financial_matches:
            metrics['financial_values'] = financial_matches
            
            # Track each financial value if source tracker is available
            if self.source_tracker and document_id:
                for value in financial_matches:
                    location = self._find_value_location(text, value, pages)
                    if location:
                        data_point_id = self.source_tracker.track_data_point(
                            value=value,
                            document_id=document_id,
                            location_details=location,
                            confidence=0.85,
                            context=f"Financial value extracted from PDF"
                        )
                        tracked_metrics.append(data_point_id)
        
        # Pattern for percentages
        percentage_pattern = r'\d+\.?\d*\s*%'
        percentage_matches = list(set(re.findall(percentage_pattern, text)))
        if percentage_matches:
            metrics['percentages'] = percentage_matches
            
            # Track percentages
            if self.source_tracker and document_id:
                for value in percentage_matches:
                    location = self._find_value_location(text, value, pages)
                    if location:
                        data_point_id = self.source_tracker.track_data_point(
                            value=value,
                            document_id=document_id,
                            location_details=location,
                            confidence=0.9,
                            context=f"Percentage value extracted from PDF"
                        )
                        tracked_metrics.append(data_point_id)
        
        # Pattern for years
        year_pattern = r'\b20\d{2}\b|\b19\d{2}\b'
        year_matches = sorted(list(set(re.findall(year_pattern, text))))
        if year_matches:
            metrics['years'] = year_matches
        
        # Pattern for key value pairs (e.g., "Revenue: $1.2M")
        kv_pattern = r'([A-Za-z\s]+):\s*([\$€£¥]?\s*[\d,]+\.?\d*\s*[BMK]?%?)'
        kv_matches = re.findall(kv_pattern, text)
        if kv_matches:
            for key, value in kv_matches:
                clean_key = key.strip().lower().replace(' ', '_')
                if clean_key and value.strip():
                    metrics[clean_key] = value.strip()
                    
                    # Track key-value pairs with higher confidence
                    if self.source_tracker and document_id:
                        location = self._find_value_location(text, f"{key}: {value}", pages)
                        if location:
                            data_point_id = self.source_tracker.track_data_point(
                                value=value.strip(),
                                document_id=document_id,
                                location_details=location,
                                confidence=0.95,
                                context=f"Key-value pair: {key.strip()}"
                            )
                            tracked_metrics.append(data_point_id)
        
        # Add tracking information if available
        if tracked_metrics:
            metrics['_tracked_data_points'] = tracked_metrics
        
        return metrics
    
    def _track_table_cells(self, table_lines: List[str], document_id: str, 
                          start_line: int) -> List[str]:
        """Track individual table cells as data points"""
        data_point_ids = []
        
        if len(table_lines) < 3:  # Need header, separator, and at least one data row
            return data_point_ids
        
        # Parse table structure
        header_line = table_lines[0]
        headers = [h.strip() for h in header_line.split('|') if h.strip()]
        
        # Process data rows (skip header and separator)
        for row_idx, row_line in enumerate(table_lines[2:], start=1):
            cells = [c.strip() for c in row_line.split('|') if c.strip()]
            
            for col_idx, cell_value in enumerate(cells):
                if cell_value and col_idx < len(headers):
                    # Determine if this cell contains valuable data
                    if self._is_valuable_cell_data(cell_value):
                        # Create location details
                        location_details = {
                            'page_or_sheet': f"Page {self._estimate_page_number_from_line(start_line)}",
                            'cell_or_section': f"Table Row {row_idx}, Col {headers[col_idx]}",
                            'table_name': f"Table at line {start_line}",
                            'line_number': start_line + row_idx + 1,
                            'coordinates': {
                                'table_start': start_line,
                                'row': row_idx,
                                'col': col_idx,
                                'header': headers[col_idx]
                            },
                            'extraction_method': 'markdown_table_parsing'
                        }
                        
                        # Track the data point
                        data_point_id = self.source_tracker.track_data_point(
                            value=cell_value,
                            document_id=document_id,
                            location_details=location_details,
                            confidence=0.9,
                            context=f"Table cell under header '{headers[col_idx]}'"
                        )
                        
                        data_point_ids.append(data_point_id)
        
        return data_point_ids
    
    def _find_value_location(self, text: str, value: str, 
                           pages: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Find the location of a specific value within the text"""
        lines = text.split('\n')
        
        # Find the line containing the value
        for line_num, line in enumerate(lines):
            if value in line:
                page_number = self._estimate_page_number(text, line_num)
                
                # Get surrounding context
                context_start = max(0, line_num - 2)
                context_end = min(len(lines), line_num + 3)
                context_lines = lines[context_start:context_end]
                context = ' '.join(context_lines).strip()
                
                return {
                    'page_or_sheet': f"Page {page_number}",
                    'cell_or_section': f"Line {line_num + 1}",
                    'line_number': line_num + 1,
                    'coordinates': {
                        'line': line_num,
                        'char_position': line.find(value)
                    },
                    'extraction_method': 'regex_pattern_matching'
                }
        
        return None
    
    def _estimate_page_number(self, text: str, line_number: int) -> int:
        """Estimate which page a line number corresponds to"""
        lines = text.split('\n')
        
        # Look for page separators
        page_separators = []
        for i, line in enumerate(lines):
            if line.strip() == '<<<' or '<<<' in line:
                page_separators.append(i)
        
        if not page_separators:
            return 1  # Single page
        
        # Find which page the line falls into
        current_page = 1
        for separator_line in page_separators:
            if line_number < separator_line:
                return current_page
            current_page += 1
        
        return current_page
    
    def _estimate_page_number_from_line(self, line_number: int) -> int:
        """Simple page estimation for table tracking"""
        # Rough estimate: assume 50 lines per page
        return (line_number // 50) + 1
    
    def _is_valuable_cell_data(self, cell_value: str) -> bool:
        """Determine if a table cell contains valuable data worth tracking"""
        if not cell_value or len(cell_value) < 2:
            return False
        
        # Check for financial data
        if re.match(r'[\$€£¥]', cell_value):
            return True
        
        # Check for percentages
        if '%' in cell_value:
            return True
        
        # Check for numeric data
        if re.match(r'^[\d,]+\.?\d*$', cell_value.replace(',', '')):
            return True
        
        # Check for dates
        if re.match(r'\d{1,2}[/-]\d{1,2}[/-]\d{4}', cell_value):
            return True
        
        # Skip generic headers or empty cells
        common_headers = {'total', 'subtotal', 'name', 'description', 'item', 'category'}
        if cell_value.lower().strip() in common_headers:
            return False
        
        # Include text data if it's substantial
        return len(cell_value) > 5
