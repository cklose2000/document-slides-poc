from docx import Document
import io

class WordExtractor:
    def extract_with_structure(self, file_path):
        """Extract maintaining paragraph numbers and structure"""
        try:
            doc = Document(file_path)
            return self._process_document(doc)
        except Exception as e:
            return {'error': f'Failed to extract Word document: {str(e)}'}
    
    def extract_from_bytes(self, word_bytes, filename="document.docx"):
        """Extract from bytes similar to other extractors"""
        try:
            word_file = io.BytesIO(word_bytes)
            doc = Document(word_file)
            result = self._process_document(doc)
            result['filename'] = filename
            return result
        except Exception as e:
            return {'error': f'Failed to extract Word document from bytes: {str(e)}'}
    
    def _process_document(self, doc):
        """Process the document and extract structured content"""
        result = {
            'paragraphs': [],
            'tables': [],
            'headers': [],
            'key_sections': {},
            'raw_text': ''
        }
        
        # Extract paragraphs with structure
        paragraph_texts = []
        for i, paragraph in enumerate(doc.paragraphs):
            if paragraph.text.strip():
                para_data = {
                    'id': f'para_{i+1}',
                    'text': paragraph.text.strip(),
                    'style': paragraph.style.name if paragraph.style else 'Normal',
                    'is_header': self._is_header_style(paragraph)
                }
                
                result['paragraphs'].append(para_data)
                paragraph_texts.append(paragraph.text.strip())
                
                # Identify headers
                if para_data['is_header']:
                    result['headers'].append({
                        'id': para_data['id'],
                        'text': para_data['text'],
                        'level': self._get_header_level(paragraph)
                    })
        
        # Extract tables
        for i, table in enumerate(doc.tables):
            table_data = self._extract_table(table, i+1)
            result['tables'].append(table_data)
        
        # Identify key sections
        result['key_sections'] = self._identify_key_sections(result['paragraphs'])
        
        # Create raw text
        result['raw_text'] = '\n\n'.join(paragraph_texts)
        
        return result
    
    def _is_header_style(self, paragraph):
        """Determine if paragraph is a header based on style"""
        if not paragraph.style:
            return False
        
        style_name = paragraph.style.name.lower()
        header_indicators = ['heading', 'title', 'subtitle', 'header']
        
        return any(indicator in style_name for indicator in header_indicators)
    
    def _get_header_level(self, paragraph):
        """Get header level from style"""
        if not paragraph.style:
            return 1
        
        style_name = paragraph.style.name.lower()
        
        # Extract number from heading styles like "Heading 1", "Heading 2", etc.
        if 'heading' in style_name:
            try:
                level = int(style_name.split()[-1])
                return level
            except (ValueError, IndexError):
                return 1
        
        return 1
    
    def _extract_table(self, table, table_id):
        """Extract table data with structure"""
        table_data = {
            'id': f'table_{table_id}',
            'rows': [],
            'headers': [],
            'cell_count': 0
        }
        
        for i, row in enumerate(table.rows):
            row_data = []
            for j, cell in enumerate(row.cells):
                cell_text = cell.text.strip()
                cell_data = {
                    'text': cell_text,
                    'position': f'{chr(65+j)}{i+1}',  # A1, B1, etc.
                    'is_header': i == 0  # Assume first row is header
                }
                row_data.append(cell_data)
                table_data['cell_count'] += 1
            
            table_data['rows'].append(row_data)
            
            # Store headers from first row
            if i == 0:
                table_data['headers'] = [cell['text'] for cell in row_data]
        
        return table_data
    
    def _identify_key_sections(self, paragraphs):
        """Identify key sections like executive summary, financials, etc."""
        sections = {}
        current_section = None
        
        # Keywords that indicate important sections
        section_keywords = {
            'executive_summary': ['executive summary', 'overview', 'summary'],
            'financial_performance': ['financial', 'revenue', 'profit', 'earnings', 'performance'],
            'growth': ['growth', 'expansion', 'increase', 'trends'],
            'market': ['market', 'industry', 'competitive', 'position'],
            'operations': ['operations', 'business', 'strategy']
        }
        
        for para in paragraphs:
            text_lower = para['text'].lower()
            
            # Check if this paragraph starts a new section
            if para['is_header']:
                for section_type, keywords in section_keywords.items():
                    if any(keyword in text_lower for keyword in keywords):
                        current_section = section_type
                        if current_section not in sections:
                            sections[current_section] = []
                        sections[current_section].append({
                            'paragraph_id': para['id'],
                            'type': 'header',
                            'text': para['text']
                        })
                        break
            elif current_section:
                # Add content to current section
                sections[current_section].append({
                    'paragraph_id': para['id'],
                    'type': 'content',
                    'text': para['text']
                })
        
        return sections