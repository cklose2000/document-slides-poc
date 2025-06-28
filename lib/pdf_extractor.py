import requests
import json
import os
import time
from typing import Dict, Any, Optional

class PDFExtractor:
    """Extract text and structured content from PDFs using LLMWhisperer API"""
    
    def __init__(self):
        self.api_key = os.getenv('LLMWHISPERER_API_KEY')
        self.base_url = os.getenv('LLMWHISPERER_BASE_URL', 'https://llmwhisperer-api.us-central.unstract.com/api/v2')
        self.timeout = int(os.getenv('LLMWHISPERER_TIMEOUT', '300'))
        self.max_pages = int(os.getenv('LLMWHISPERER_MAX_PAGES', '50'))
        self.processing_mode = os.getenv('LLMWHISPERER_PROCESSING_MODE', 'ocr')
        
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
                    # Parse the extracted content
                    return self._parse_pdf_content(extracted_text, filename)
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
    
    def _parse_pdf_content(self, text: str, filename: str) -> Dict[str, Any]:
        """Parse extracted PDF text into structured format"""
        
        # Split by pages if page separator exists
        pages = text.split("<<<") if "<<<" in text else [text]
        
        # Extract tables (look for markdown table patterns)
        tables = self._extract_tables(text)
        
        # Extract sections based on markdown headers
        sections = self._extract_sections(text)
        
        # Extract key metrics and numbers
        metrics = self._extract_metrics(text)
        
        return {
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
    
    def _extract_tables(self, text: str) -> list:
        """Extract markdown tables from text"""
        tables = []
        lines = text.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Check if this looks like a markdown table header
            if '|' in line and i + 1 < len(lines) and '|' in lines[i + 1] and '-' in lines[i + 1]:
                # Found a table, extract it
                table_lines = [line]
                i += 1
                
                # Get all table rows
                while i < len(lines) and '|' in lines[i]:
                    table_lines.append(lines[i])
                    i += 1
                
                if len(table_lines) > 2:  # Header + separator + at least one data row
                    tables.append({
                        "content": '\n'.join(table_lines),
                        "rows": len(table_lines) - 2,  # Exclude header and separator
                        "position": i - len(table_lines)
                    })
            else:
                i += 1
                
        return tables
    
    def _extract_sections(self, text: str) -> Dict[str, str]:
        """Extract sections based on markdown headers"""
        sections = {}
        lines = text.split('\n')
        
        current_section = None
        section_content = []
        
        for line in lines:
            # Check for markdown headers
            if line.startswith('#'):
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(section_content).strip()
                
                # Start new section
                current_section = line.strip('#').strip()
                section_content = []
            else:
                section_content.append(line)
        
        # Save last section
        if current_section:
            sections[current_section] = '\n'.join(section_content).strip()
            
        return sections
    
    def _extract_metrics(self, text: str) -> Dict[str, Any]:
        """Extract key metrics and numbers from text"""
        import re
        
        metrics = {}
        
        # Pattern for financial metrics (e.g., $1.2M, $45,000, €1.5B)
        financial_pattern = r'[\$€£¥]\s*[\d,]+\.?\d*\s*[BMK]?'
        financial_matches = re.findall(financial_pattern, text)
        if financial_matches:
            metrics['financial_values'] = list(set(financial_matches))
        
        # Pattern for percentages
        percentage_pattern = r'\d+\.?\d*\s*%'
        percentage_matches = re.findall(percentage_pattern, text)
        if percentage_matches:
            metrics['percentages'] = list(set(percentage_matches))
        
        # Pattern for years
        year_pattern = r'\b20\d{2}\b|\b19\d{2}\b'
        year_matches = re.findall(year_pattern, text)
        if year_matches:
            metrics['years'] = sorted(list(set(year_matches)))
        
        # Pattern for key value pairs (e.g., "Revenue: $1.2M")
        kv_pattern = r'([A-Za-z\s]+):\s*([\$€£¥]?\s*[\d,]+\.?\d*\s*[BMK]?%?)'
        kv_matches = re.findall(kv_pattern, text)
        if kv_matches:
            for key, value in kv_matches:
                clean_key = key.strip().lower().replace(' ', '_')
                if clean_key and value.strip():
                    metrics[clean_key] = value.strip()
        
        return metrics