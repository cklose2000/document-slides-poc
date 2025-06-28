from flask import Flask, request, jsonify, send_file
import sys
import os

# Add the parent directory to the path so we can import from lib
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.excel_extractor import ExcelExtractor
from lib.word_extractor import WordExtractor
from lib.pdf_extractor import PDFExtractor
from lib.slide_generator import SlideGenerator
from lib.llm_slides import analyze_documents_for_slides, extract_key_metrics_simple
import tempfile
import io

app = Flask(__name__, static_folder='../static', static_url_path='/static')

@app.route('/api/generate-slides', methods=['POST'])
def generate_slides():
    """
    Accept multiple file uploads, generate slides with attribution.
    Returns: PowerPoint file + JSON with source mappings
    """
    try:
        uploaded_files = request.files.getlist('documents')
        
        if not uploaded_files or all(file.filename == '' for file in uploaded_files):
            return jsonify({'error': 'No files uploaded'}), 400
        
        # Extract content from each document
        all_documents = []
        
        for file in uploaded_files:
            if not file.filename:
                continue
                
            file_bytes = file.read()
            filename = file.filename
            
            if filename.endswith('.pdf'):
                extractor = PDFExtractor()
                content = extractor.extract_from_bytes(file_bytes, filename)
                doc_data = {
                    'filename': filename,
                    'type': 'pdf',
                    'content': content,
                    'raw_text': content.get('raw_text', '') if isinstance(content, dict) else str(content),
                    'tables': content.get('tables', []) if isinstance(content, dict) else [],
                    'key_metrics': content.get('key_metrics', {}) if isinstance(content, dict) else {},
                    'sections': content.get('sections', {}) if isinstance(content, dict) else {}
                }
            elif filename.endswith('.xlsx'):
                extractor = ExcelExtractor()
                content = extractor.extract_from_bytes(file_bytes, filename)
                doc_data = {
                    'filename': filename,
                    'type': 'excel',
                    'content': content,
                    'structured_data': content
                }
            elif filename.endswith('.docx'):
                extractor = WordExtractor()
                content = extractor.extract_from_bytes(file_bytes, filename)
                doc_data = {
                    'filename': filename,
                    'type': 'word',
                    'content': content,
                    'raw_text': content.get('raw_text', '') if isinstance(content, dict) else str(content)
                }
            else:
                continue  # Skip unsupported file types
            
            all_documents.append(doc_data)
        
        if not all_documents:
            return jsonify({'error': 'No supported documents found'}), 400
        
        # Generate slides
        generator = SlideGenerator()
        
        # Create a simple summary slide
        summary_data = {
            "documents_processed": len(all_documents),
            "files": [doc['filename'] for doc in all_documents]
        }
        slide = generator.create_company_overview_slide(
            {"name": "Document Processing Summary", "description": f"Processed {len(all_documents)} files"},
            {"summary": f"Files: {', '.join([doc['filename'] for doc in all_documents])}"}
        )
        
        # Save and return
        output_path = tempfile.mktemp(suffix='.pptx')
        generator.save_presentation(output_path)
        
        # Return the PowerPoint file
        return send_file(
            output_path,
            as_attachment=True,
            download_name='generated_slides.pptx',
            mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation'
        )
        
    except Exception as e:
        return jsonify({'error': f'Slide generation failed: {str(e)}'}), 500

@app.route('/api/generate-slides/preview', methods=['POST'])
def preview_extraction():
    """Test endpoint to see extraction results without generating slides"""
    try:
        uploaded_files = request.files.getlist('documents')
        
        if not uploaded_files:
            return jsonify({'error': 'No files uploaded'}), 400
        
        # Extract content from each document
        all_documents = []
        
        for file in uploaded_files:
            if not file.filename:
                continue
                
            file_bytes = file.read()
            filename = file.filename
            
            if filename.endswith('.pdf'):
                extractor = PDFExtractor()
                content = extractor.extract_from_bytes(file_bytes, filename)
                if isinstance(content, dict):
                    doc_data = {
                        'filename': filename,
                        'type': 'pdf',
                        'pages': content.get('metadata', {}).get('pages', 0),
                        'tables_count': len(content.get('tables', [])),
                        'sections': list(content.get('sections', {}).keys()),
                        'key_metrics': content.get('key_metrics', {}),
                        'sample_text': content.get('raw_text', '')[:300] + "..." if len(content.get('raw_text', '')) > 300 else content.get('raw_text', '')
                    }
                else:
                    doc_data = {
                        'filename': filename,
                        'type': 'pdf',
                        'content': str(content)[:500] + "..." if len(str(content)) > 500 else str(content)
                    }
            elif filename.endswith('.xlsx'):
                extractor = ExcelExtractor()
                content = extractor.extract_from_bytes(file_bytes, filename)
                # Summarize Excel content for preview
                if isinstance(content, dict) and 'sheets' in content:
                    summary = {}
                    for sheet_name, sheet_data in content['sheets'].items():
                        summary[sheet_name] = {
                            'key_metrics_count': len(sheet_data.get('key_metrics', {})),
                            'tables_count': len(sheet_data.get('tables', [])),
                            'sample_metrics': list(sheet_data.get('key_metrics', {}).keys())[:3]
                        }
                    doc_data = {
                        'filename': filename,
                        'type': 'excel',
                        'summary': summary
                    }
                else:
                    doc_data = {
                        'filename': filename,
                        'type': 'excel',
                        'content': str(content)[:500] + "..." if len(str(content)) > 500 else str(content)
                    }
            else:
                continue
            
            all_documents.append(doc_data)
        
        return jsonify({
            'success': True,
            'documents_processed': len(all_documents),
            'extraction_results': all_documents,
            'message': f'Successfully processed {len(all_documents)} documents'
        })
        
    except Exception as e:
        return jsonify({'error': f'Preview failed: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'document-slides-poc'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)