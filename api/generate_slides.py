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
import json
from werkzeug.utils import secure_filename

# Import brand management
try:
    from lib.template_parser import BrandManager, TemplateParser
    TEMPLATE_MANAGEMENT_AVAILABLE = True
except ImportError:
    TEMPLATE_MANAGEMENT_AVAILABLE = False

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
        
        # 1. Extract content from each document
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
        
        # 2. Analyze with LLM (or simple extraction for testing)
        try:
            if os.getenv('OPENAI_API_KEY'):
                analysis = analyze_documents_for_slides(all_documents)
            else:
                # Fallback to simple extraction if no API key
                analysis = extract_key_metrics_simple(all_documents)
                analysis.update({
                    "company_overview": {"name": "Sample Company"},
                    "key_insights": ["Analysis completed without LLM"],
                    "suggested_slides": [
                        {"type": "financial_summary", "title": "Financial Summary", "content": "Basic metrics"}
                    ]
                })
        except Exception as e:
            # Fallback analysis
            analysis = {
                "company_overview": {"name": "Document Analysis"},
                "financial_metrics": {},
                "key_insights": [f"Basic extraction from {len(all_documents)} documents"],
                "suggested_slides": [
                    {"type": "company_overview", "title": "Document Summary", "content": "Files processed"}
                ],
                "source_attributions": {
                    "primary_documents": [doc['filename'] for doc in all_documents],
                    "extraction_summary": f"Processed {len(all_documents)} files"
                }
            }
        
        # 3. Generate slides
        # Check if template is specified
        template_id = request.form.get('template_id', 'default')
        
        # Use branded slide generator if template management is available
        if TEMPLATE_MANAGEMENT_AVAILABLE and template_id:
            try:
                from lib.slide_generator_branded import BrandedSlideGenerator
                from lib.source_tracker import SourceTracker
                
                # Initialize brand manager and source tracker
                brand_manager = BrandManager()
                source_tracker = SourceTracker()
                
                # Create branded slide generator
                generator = BrandedSlideGenerator(
                    brand_manager=brand_manager,
                    template_name=template_id,
                    source_tracker=source_tracker
                )
                print(f"Using branded slide generator with template: {template_id}")
            except Exception as e:
                print(f"Failed to use branded generator: {str(e)}, falling back to standard")
                generator = SlideGenerator()
        else:
            generator = SlideGenerator()
        
        # Create slides based on analysis
        slides_created = []
        
        # Financial summary slide
        if 'financial_metrics' in analysis and analysis['financial_metrics']:
            slide = generator.create_financial_summary_slide(
                analysis['financial_metrics'],
                analysis.get('source_attributions', {})
            )
            slides_created.append("Financial Summary")
        
        # Company overview slide
        if 'company_overview' in analysis:
            slide = generator.create_company_overview_slide(
                analysis['company_overview'],
                analysis.get('source_attributions', {})
            )
            slides_created.append("Company Overview")
        
        # Key insights slide
        if 'key_insights' in analysis and analysis['key_insights']:
            slide = generator.create_data_insights_slide(
                analysis['key_insights'],
                analysis.get('source_attributions', {})
            )
            slides_created.append("Key Insights")
        
        # If no specific slides were created, create a summary slide
        if not slides_created:
            summary_data = {
                "documents_processed": len(all_documents),
                "files": [doc['filename'] for doc in all_documents]
            }
            slide = generator.create_company_overview_slide(
                {"name": "Document Processing Summary", "description": f"Processed {len(all_documents)} files"},
                {"summary": f"Files: {', '.join([doc['filename'] for doc in all_documents])}"}
            )
            slides_created.append("Processing Summary")
        
        # 4. Save and return
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
            elif filename.endswith('.docx'):
                extractor = WordExtractor()
                content = extractor.extract_from_bytes(file_bytes, filename)
                if isinstance(content, dict):
                    doc_data = {
                        'filename': filename,
                        'type': 'word',
                        'paragraphs_count': len(content.get('paragraphs', [])),
                        'tables_count': len(content.get('tables', [])),
                        'key_sections': list(content.get('key_sections', {}).keys()),
                        'sample_text': content.get('raw_text', '')[:300] + "..." if len(content.get('raw_text', '')) > 300 else content.get('raw_text', '')
                    }
                else:
                    doc_data = {
                        'filename': filename,
                        'type': 'word',
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

# Template Management Endpoints
@app.route('/api/templates', methods=['GET'])
def list_templates():
    """List all available presentation templates"""
    if not TEMPLATE_MANAGEMENT_AVAILABLE:
        return jsonify({'error': 'Template management not available'}), 503
    
    try:
        brand_manager = BrandManager()
        templates = []
        
        # Get all templates from brand manager
        template_names = brand_manager.list_templates()
        
        for template_name in template_names:
            template_parser = brand_manager.templates.get(template_name)
            if template_parser:
                brand_config = template_parser.get_brand_config()
                
                # Read metadata if available
                metadata_path = os.path.join('templates', template_name, 'metadata.json')
                metadata = {}
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                
                template_info = {
                    'id': template_name,
                    'name': metadata.get('name', template_name.replace('_', ' ').title()),
                    'description': metadata.get('description', f'{template_name} template'),
                    'preview': metadata.get('preview', ''),
                    'colors': brand_config.get('theme_colors', {}),
                    'fonts': brand_config.get('fonts', {}),
                    'features': metadata.get('features', [])
                }
                templates.append(template_info)
        
        return jsonify({
            'templates': templates,
            'count': len(templates)
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to list templates: {str(e)}'}), 500

@app.route('/api/templates/<template_id>/preview', methods=['GET'])
def get_template_preview(template_id):
    """Get preview image for a specific template"""
    if not TEMPLATE_MANAGEMENT_AVAILABLE:
        return jsonify({'error': 'Template management not available'}), 503
    
    preview_path = os.path.join('templates', template_id, 'preview.png')
    
    if os.path.exists(preview_path):
        return send_file(preview_path, mimetype='image/png')
    else:
        # Return a placeholder or default preview
        return jsonify({'error': 'Preview not found'}), 404

@app.route('/api/templates/upload', methods=['POST'])
def upload_template():
    """Upload a new PowerPoint template"""
    if not TEMPLATE_MANAGEMENT_AVAILABLE:
        return jsonify({'error': 'Template management not available'}), 503
    
    try:
        if 'template' not in request.files:
            return jsonify({'error': 'No template file provided'}), 400
        
        template_file = request.files['template']
        template_name = request.form.get('name', 'custom_template')
        template_description = request.form.get('description', 'Custom uploaded template')
        
        if not template_file.filename.endswith('.pptx'):
            return jsonify({'error': 'Template must be a PowerPoint file (.pptx)'}), 400
        
        # Secure the filename
        template_id = secure_filename(template_name.lower().replace(' ', '_'))
        
        # Save template file
        template_dir = os.path.join('templates', template_id)
        os.makedirs(template_dir, exist_ok=True)
        
        template_path = os.path.join(template_dir, 'template.pptx')
        template_file.save(template_path)
        
        # Parse template to extract brand information
        brand_manager = BrandManager()
        brand_manager.add_template(template_path, template_id)
        
        # Create metadata
        metadata = {
            'id': template_id,
            'name': template_name,
            'description': template_description,
            'preview': 'preview.png',
            'uploaded': True,
            'features': ['Custom branding', 'User uploaded']
        }
        
        metadata_path = os.path.join(template_dir, 'metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return jsonify({
            'message': 'Template uploaded successfully',
            'template_id': template_id,
            'template_name': template_name
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to upload template: {str(e)}'}), 500

@app.route('/api/templates/<template_name>/select', methods=['POST'])
def select_template(template_name):
    """Select a template as the current active template"""
    if not TEMPLATE_MANAGEMENT_AVAILABLE:
        return jsonify({'error': 'Template management not available'}), 503
    
    try:
        brand_manager = BrandManager()
        
        if template_name not in brand_manager.list_templates():
            return jsonify({'error': f'Template "{template_name}" not found'}), 404
        
        brand_manager.set_current_template(template_name)
        template_parser = brand_manager.get_current_template()
        
        if template_parser:
            config = template_parser.get_brand_config()
            return jsonify({
                'success': True,
                'current_template': template_name,
                'message': f'Template "{template_name}" selected',
                'theme_colors': config.get('theme_colors', {}),
                'fonts': config.get('fonts', {})
            })
        else:
            return jsonify({'error': 'Failed to load template configuration'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Template selection failed: {str(e)}'}), 500

@app.route('/api/templates/<template_name>', methods=['GET'])
def get_template_info(template_name):
    """Get detailed information about a specific template"""
    if not TEMPLATE_MANAGEMENT_AVAILABLE:
        return jsonify({'error': 'Template management not available'}), 503
    
    try:
        brand_manager = BrandManager()
        
        if template_name not in brand_manager.list_templates():
            return jsonify({'error': f'Template "{template_name}" not found'}), 404
        
        # Temporarily switch to this template to get its config
        original_template = brand_manager.current_template
        brand_manager.set_current_template(template_name)
        template_parser = brand_manager.get_current_template()
        
        if template_parser:
            config = template_parser.get_brand_config()
            
            # Restore original template
            if original_template:
                brand_manager.set_current_template(original_template)
            
            return jsonify({
                'success': True,
                'template_name': template_name,
                'config': config
            })
        else:
            return jsonify({'error': 'Failed to load template'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Failed to get template info: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    template_status = 'available' if TEMPLATE_MANAGEMENT_AVAILABLE else 'unavailable'
    return jsonify({
        'status': 'healthy', 
        'service': 'document-slides-poc',
        'template_management': template_status
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)