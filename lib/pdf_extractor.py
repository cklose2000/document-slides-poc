import requests
import json
import time
from typing import Dict, Any, Optional
import logging
import os
import re

try:
    from .source_tracker import SourceTracker
except ImportError:
    from source_tracker import SourceTracker

class PDFExtractor:
    """
    PDF text and table extraction using LLMWhisperer API
    """
    
    def __init__(self, api_key: str, source_tracker: Optional[SourceTracker] = None):
        self.api_key = api_key
        self.source_tracker = source_tracker
        self.base_url = os.getenv('LLMWHISPERER_BASE_URL', 'https://llmwhisperer-api.us-central.unstract.com/api/v2')
        self.headers = {
            'unstract-key': api_key,
            'Content-Type': 'application/octet-stream'
        }
        
    def extract_text_and_tables(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract text and tables from PDF using LLMWhisperer API
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing extracted text, tables, and metadata
        """
        try:
            # Read PDF file
            with open(pdf_path, 'rb') as f:
                pdf_data = f.read()
            
            # Step 1: Submit PDF for processing
            whisper_hash = self._submit_pdf(pdf_data)
            if not whisper_hash:
                return self._error_response("Failed to submit PDF for processing")
            
            # Step 2: Poll for results
            result = self._poll_for_results(whisper_hash)
            if not result:
                return self._error_response("Failed to retrieve processing results")
            
            # Step 3: Parse and structure the results
            return self._parse_results(result, pdf_path)
            
        except Exception as e:
            logging.error(f"Error in PDF extraction: {str(e)}")
            return self._error_response(f"Error extracting {pdf_path}: {str(e)}")
    
    def _submit_pdf(self, pdf_data: bytes) -> Optional[str]:
        """
        Submit PDF to LLMWhisperer API for processing
        
        Args:
            pdf_data: Raw PDF file data
            
        Returns:
            whisper_hash if successful, None otherwise
        """
        try:
            # API endpoint for PDF processing
            url = f"{self.base_url}/whisper"
            
            # Submit PDF for processing
            response = requests.post(url, data=pdf_data, headers=self.headers, timeout=30)
            
            logging.info(f"LLMWhisperer submit response: {response.status_code}")
            
            # Handle both immediate success (200) and async processing (202)
            if response.status_code in [200, 202]:
                result = response.json()
                logging.info(f"LLMWhisperer submit result: {result}")
                
                # Validate response structure
                if 'whisper_hash' in result:
                    return result['whisper_hash']
                else:
                    logging.error(f"No whisper_hash in response: {result}")
                    return None
            else:
                logging.error(f"LLMWhisperer API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logging.error(f"Error submitting PDF: {str(e)}")
            return None
    
    def _poll_for_results(self, whisper_hash: str, max_attempts: int = 30, initial_delay: float = 2.0) -> Optional[Dict]:
        """
        Poll LLMWhisperer API for processing results
        
        Args:
            whisper_hash: Hash returned from PDF submission
            max_attempts: Maximum number of polling attempts
            initial_delay: Initial delay between attempts (seconds)
            
        Returns:
            Processing results if successful, None otherwise
        """
        url = f"{self.base_url}/whisper-status"
        
        # Progressive backoff delays
        delay = initial_delay
        
        for attempt in range(max_attempts):
            try:
                # Check processing status
                response = requests.get(
                    url,
                    params={'whisper_hash': whisper_hash},  # v2 API uses underscore
                    headers={'unstract-key': self.api_key},
                    timeout=30
                )
                
                logging.info(f"Attempt {attempt + 1}: Status {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Check if processing is complete
                    if result.get('status') == 'processed':
                        logging.info("PDF processing completed successfully")
                        # For v2 API, we need to make another call to get the text
                        text_url = f"{self.base_url}/whisper-retrieve"
                        text_response = requests.get(
                            text_url,
                            params={'whisper_hash': whisper_hash},
                            headers={'unstract-key': self.api_key},
                            timeout=30
                        )
                        if text_response.status_code == 200:
                            retrieve_data = text_response.json()
                            result['extracted_text'] = retrieve_data.get('result_text', '')
                        return result
                    elif result.get('status') == 'processing':
                        logging.info(f"Still processing... (attempt {attempt + 1}/{max_attempts})")
                    elif result.get('status') == 'failed':
                        logging.error(f"PDF processing failed: {result.get('message', 'Unknown error')}")
                        return None
                    
                elif response.status_code == 202:
                    # Still processing
                    logging.info(f"Still processing... (attempt {attempt + 1}/{max_attempts})")
                    
                elif response.status_code == 404:
                    logging.error(f"Whisper hash not found: {whisper_hash}")
                    return None
                    
                else:
                    logging.error(f"Unexpected status code: {response.status_code} - {response.text}")
                
                # Wait before next attempt
                if attempt < max_attempts - 1:
                    time.sleep(delay)
                    # Increase delay for next attempt (progressive backoff)
                    delay = min(delay * 1.5, 10.0)
                    
            except Exception as e:
                logging.error(f"Error polling for results (attempt {attempt + 1}): {str(e)}")
                if attempt < max_attempts - 1:
                    time.sleep(delay)
                    delay = min(delay * 1.5, 10.0)
        
        logging.error(f"Max polling attempts ({max_attempts}) exceeded")
        return None
    
    def _parse_results(self, result: Dict, pdf_path: str) -> Dict[str, Any]:
        """
        Parse and structure LLMWhisperer results with page-level tracking
        
        Args:
            result: Raw result from LLMWhisperer API
            pdf_path: Original PDF file path
            
        Returns:
            Structured extraction results with source tracking
        """
        try:
            # Extract text content
            extracted_text = result.get('extracted_text', '')
            
            # Register document with source tracker if available
            document_id = None
            if self.source_tracker:
                document_id = self.source_tracker.register_document(
                    pdf_path, 
                    'pdf',
                    {'total_pages': self._estimate_pages(extracted_text)}
                )
            
            # Basic text analysis
            lines = extracted_text.split('\n')
            pages = self._estimate_pages(extracted_text)
            
            # Split text by pages and track content
            page_content = self._split_into_pages(extracted_text, pages)
            
            # Extract key metrics with page tracking
            key_metrics = self._extract_key_metrics_with_tracking(extracted_text, page_content, document_id)
            
            # Detect sections with page references
            sections = self._detect_sections_with_pages(lines, page_content)
            
            # Count tables (estimate based on structure)
            tables_count = self._count_tables(extracted_text)
            
            return {
                "filename": pdf_path.split('/')[-1],
                "type": "pdf",
                "pages": pages,
                "page_content": page_content,
                "sample_text": extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text,
                "key_metrics": key_metrics,
                "sections": sections,
                "tables_count": tables_count,
                "document_id": document_id,
                "raw_text": extracted_text
            }
            
        except Exception as e:
            logging.error(f"Error parsing results: {str(e)}")
            return self._error_response(f"Error parsing results: {str(e)}")
    
    def _estimate_pages(self, text: str) -> int:
        """
        Estimate number of pages based on text content
        """
        # Simple heuristic: assume ~2000 characters per page
        return max(1, len(text) // 2000)
    
    def _split_into_pages(self, text: str, total_pages: int) -> Dict[int, str]:
        """
        Split text into approximate pages
        """
        if total_pages <= 1:
            return {1: text}
        
        # Simple heuristic: split by character count
        chars_per_page = len(text) // total_pages
        page_content = {}
        
        for page_num in range(1, total_pages + 1):
            start = (page_num - 1) * chars_per_page
            end = page_num * chars_per_page if page_num < total_pages else len(text)
            page_content[page_num] = text[start:end]
        
        return page_content
    
    def _extract_key_metrics_with_tracking(self, text: str, page_content: Dict[int, str], document_id: Optional[str]) -> Dict[str, Any]:
        """
        Extract key financial/business metrics from text with page tracking
        """
        metrics = {}
        
        # Common patterns for financial metrics
        patterns = {
            'revenue': r'(?:revenue|sales)\s*:?\s*\$?([\d,\.]+[MmBbKk]?)\b',
            'growth': r'(?:growth|increase)\s*:?\s*([\d\.]+%)',
            'profit': r'(?:profit|earnings)\s*:?\s*\$?([\d,\.]+[MmBbKk]?)\b',
            'margin': r'(?:margin)\s*:?\s*([\d\.]+%)',
            'customers': r'(?:customers|clients)\s*:?\s*([\d,]+)\b'
        }
        
        for metric, pattern in patterns.items():
            # Find matches in full text first
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            if matches:
                match = matches[0]  # Take first match
                value = match.group(1)
                
                # Find which page this match is on
                page_num = self._find_page_for_position(match.start(), page_content)
                
                # Track data point if source tracker is available
                data_point_id = None
                if self.source_tracker and document_id:
                    confidence = self._calculate_pdf_confidence(value, metric, match.group(0))
                    data_point_id = self.source_tracker.track_data_point(
                        value=value,
                        document_id=document_id,
                        location_details={
                            'page_or_sheet': f"Page {page_num}",
                            'cell_or_section': f"page_{page_num}",
                            'coordinates': {'char_position': match.start()},
                            'extraction_method': 'llmwhisperer_regex'
                        },
                        confidence=confidence,
                        context=f"Extracted {metric}: {match.group(0)}"
                    )
                
                metrics[metric] = {
                    'value': value,
                    'page': page_num,
                    'data_point_id': data_point_id,
                    'full_match': match.group(0)
                }
        
        return metrics
    
    def _detect_sections_with_pages(self, lines: list, page_content: Dict[int, str]) -> Dict[str, Any]:
        """
        Detect major sections in the document with page references
        """
        sections = {}
        full_text = '\n'.join(lines)
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if len(line) > 0 and (line.isupper() or line.endswith(':')):
                if len(line) < 100:  # Likely a header
                    section_name = line.lower().replace(':', '').replace(' ', '_')
                    
                    # Estimate page number for this line
                    char_position = sum(len(lines[i]) + 1 for i in range(line_num))
                    page_num = self._find_page_for_position(char_position, page_content)
                    
                    sections[section_name] = {
                        'title': line,
                        'page': page_num,
                        'line_number': line_num
                    }
                    
                    if len(sections) >= 10:  # Limit to first 10 sections
                        break
        
        return sections
    
    def _find_page_for_position(self, char_position: int, page_content: Dict[int, str]) -> int:
        """
        Find which page a character position belongs to
        """
        current_position = 0
        for page_num in sorted(page_content.keys()):
            page_length = len(page_content[page_num])
            if char_position <= current_position + page_length:
                return page_num
            current_position += page_length
        
        # Default to last page if position is beyond content
        return max(page_content.keys()) if page_content else 1
    
    def _calculate_pdf_confidence(self, value: str, metric_type: str, full_match: str) -> float:
        """
        Calculate confidence score for PDF extracted data
        """
        confidence = 0.7  # Base confidence for PDF extraction
        
        # Boost confidence based on value characteristics
        if '$' in full_match:
            confidence += 0.1  # Currency symbol increases confidence
        
        if metric_type in ['revenue', 'profit'] and any(suffix in value.lower() for suffix in ['m', 'b', 'k']):
            confidence += 0.1  # Scale indicators increase confidence
        
        if metric_type in ['growth', 'margin'] and '%' in full_match:
            confidence += 0.1  # Percentage symbol increases confidence
        
        # Reduce confidence for very short values
        if len(value) < 3:
            confidence -= 0.2
        
        return max(0.3, min(0.95, confidence))  # Clamp between 0.3 and 0.95
    
    def _extract_key_metrics(self, text: str) -> Dict[str, str]:
        """
        Extract key financial/business metrics from text (legacy method)
        """
        metrics = {}
        
        # Common patterns for financial metrics
        patterns = {
            'revenue': r'(?:revenue|sales)\s*:?\s*\$?([\d,\.]+[MmBbKk]?)\b',
            'growth': r'(?:growth|increase)\s*:?\s*([\d\.]+%)',
            'profit': r'(?:profit|earnings)\s*:?\s*\$?([\d,\.]+[MmBbKk]?)\b',
            'margin': r'(?:margin)\s*:?\s*([\d\.]+%)',
            'customers': r'(?:customers|clients)\s*:?\s*([\d,]+)\b'
        }
        
        for metric, pattern in patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                metrics[metric] = matches[0]
        
        return metrics
    
    def _detect_sections(self, lines: list) -> list:
        """
        Detect major sections in the document
        """
        sections = []
        
        for line in lines:
            line = line.strip()
            if len(line) > 0 and (line.isupper() or line.endswith(':')):
                if len(line) < 100:  # Likely a header
                    sections.append(line.lower().replace(':', '').replace(' ', '_'))
        
        return sections[:10]  # Limit to first 10 sections
    
    def _count_tables(self, text: str) -> int:
        """
        Estimate number of tables in the document
        """
        # Simple heuristic: count lines with multiple tab separations
        lines = text.split('\n')
        table_lines = [line for line in lines if line.count('\t') >= 2]
        
        # Group consecutive table lines
        table_count = 0
        in_table = False
        
        for line in lines:
            has_tabs = line.count('\t') >= 2
            if has_tabs and not in_table:
                table_count += 1
                in_table = True
            elif not has_tabs:
                in_table = False
        
        return table_count
    
    def _error_response(self, error_message: str) -> Dict[str, Any]:
        """
        Create standardized error response
        """
        return {
            "filename": "unknown",
            "type": "pdf",
            "pages": 0,
            "sample_text": f"Error: {error_message}",
            "key_metrics": {},
            "sections": [],
            "tables_count": 0
        }