from docx import Document
import io

class WordExtractor:
    def extract_from_bytes(self, word_bytes, filename="document.docx"):
        """Extract content from Word document bytes"""
        try:
            # Create a BytesIO object from the bytes
            word_file = io.BytesIO(word_bytes)
            doc = Document(word_file)
            
            # Extract paragraphs
            paragraphs = []
            for para in doc.paragraphs:
                if para.text.strip():
                    paragraphs.append(para.text)
            
            # Extract tables (simplified)
            tables = []
            for table in doc.tables:
                table_data = []
                for row in table.rows:
                    row_data = []
                    for cell in row.cells:
                        row_data.append(cell.text)
                    table_data.append(row_data)
                tables.append(table_data)
            
            return {
                'filename': filename,
                'raw_text': '\n\n'.join(paragraphs),
                'paragraphs': paragraphs,
                'tables': tables,
                'key_sections': {}  # Would extract sections in production
            }
            
        except Exception as e:
            return {'error': f'Failed to extract Word data: {str(e)}'}