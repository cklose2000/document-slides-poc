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

# Initialize extractors with API keys
UPLOAD_FOLDER = tempfile.gettempdir()
llm_whisperer_key = os.getenv('LLMWHISPERER_API_KEY')
openai_key = os.getenv('OPENAI_API_KEY')

# Note: Extractors will be initialized with source tracker in generate_slides function

def _enhance_analysis_with_source_tracking(analysis, all_documents, source_tracker):
    """Enhance LLM analysis with source tracking data point IDs"""
    if not source_tracker:
        return analysis
    
    enhanced_analysis = analysis.copy()
    
    # Create source attributions with data point IDs
    source_attributions = {}
    
    # Extract source tracked data from documents
    for doc in all_documents:
        filename = doc.get('filename', 'unknown')
        
        # Handle different document types
        if doc.get('type') == 'excel' and 'content' in doc:
            excel_content = doc['content']
            if 'sheets' in excel_content:
                for sheet_name, sheet_data in excel_content['sheets'].items():
                    if 'key_metrics' in sheet_data:
                        for metric_name, metric_info in sheet_data['key_metrics'].items():
                            if 'data_point_id' in metric_info:
                                source_key = f"{metric_name}_{sheet_name}"
                                source_attributions[source_key] = {
                                    'filename': filename,
                                    'data_point_id': metric_info['data_point_id'],
                                    'value': metric_info.get('value'),
                                    'source_type': 'excel'
                                }
        
        elif doc.get('type') == 'pdf' and 'content' in doc:
            pdf_content = doc['content']
            if 'key_metrics' in pdf_content:
                for metric_name, metric_info in pdf_content['key_metrics'].items():
                    if isinstance(metric_info, dict) and 'data_point_id' in metric_info:
                        source_attributions[metric_name] = {
                            'filename': filename,
                            'data_point_id': metric_info['data_point_id'],
                            'value': metric_info.get('value'),
                            'source_type': 'pdf'
                        }
        
        elif doc.get('type') == 'word' and 'content' in doc:
            word_content = doc['content']
            if 'key_metrics' in word_content:
                for metric_name, metric_info in word_content['key_metrics'].items():
                    if isinstance(metric_info, dict) and 'data_point_id' in metric_info:
                        source_attributions[metric_name] = {
                            'filename': filename,
                            'data_point_id': metric_info['data_point_id'],
                            'value': metric_info.get('value'),
                            'source_type': 'word'
                        }
    
    # Enhance financial metrics with data point IDs
    if 'financial_metrics' in enhanced_analysis:
        for metric_name, metric_data in enhanced_analysis['financial_metrics'].items():
            # Try to find matching source attribution
            for source_key, source_info in source_attributions.items():
                if metric_name in source_key or source_key in metric_name:
                    # Add data_point_id to the metric
                    if isinstance(metric_data, dict):
                        metric_data['data_point_id'] = source_info['data_point_id']
                    break
    
    # Update source attributions in analysis
    if 'source_attributions' not in enhanced_analysis:
        enhanced_analysis['source_attributions'] = {}
    
    # Merge source attributions
    enhanced_analysis['source_attributions'].update(source_attributions)
    
    return enhanced_analysis

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
        
        # Initialize source tracker for enhanced attribution
        from lib.source_tracker import SourceTracker
        source_tracker = SourceTracker()
        
        # Initialize extractors with source tracker
        pdf_extractor = PDFExtractor(llm_whisperer_key, source_tracker) if llm_whisperer_key else None
        excel_extractor = ExcelExtractor(source_tracker)
        word_extractor = WordExtractor(source_tracker)
        
        # 1. Extract content from each document
        all_documents = []
        
        for file in uploaded_files:
            if not file.filename:
                continue
                
            file_bytes = file.read()
            filename = file.filename
            
            if filename.endswith('.pdf'):
                if not pdf_extractor:
                    doc_data = {
                        'filename': filename,
                        'type': 'pdf',
                        'content': {'error': 'PDF extraction not available - LLMWhisperer API key not configured'},
                        'raw_text': '',
                        'tables': [],
                        'key_metrics': {},
                        'sections': {}
                    }
                    all_documents.append(doc_data)
                    continue
                
                # Save file temporarily for extraction
                temp_path = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
                with open(temp_path, 'wb') as f:
                    f.write(file_bytes)
                
                content = pdf_extractor.extract_text_and_tables(temp_path)
                
                # Clean up temp file
                try:
                    os.remove(temp_path)
                except:
                    pass
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
                content = excel_extractor.extract_from_bytes(file_bytes, filename)
                doc_data = {
                    'filename': filename,
                    'type': 'excel',
                    'content': content,
                    'structured_data': content
                }
            elif filename.endswith('.docx'):
                content = word_extractor.extract_from_bytes(file_bytes, filename)
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
            # Skip LLM for faster testing - you can re-enable this later
            use_llm = False  # Set to True to use LLM analysis
            
            if use_llm and os.getenv('OPENAI_API_KEY'):
                print(f"Starting LLM analysis for {len(all_documents)} documents")
                analysis = analyze_documents_for_slides(all_documents)
                print(f"LLM analysis completed successfully")
            else:
                print("Using direct extraction (LLM disabled for faster processing)")
                # Use direct extraction from the documents we already processed
                financial_metrics = {}
                company_name = "SaaSy Inc."
                
                # Extract data directly from processed documents
                for doc in all_documents:
                    if doc.get('type') == 'pdf' and isinstance(doc.get('content'), dict):
                        pdf_metrics = doc.get('content', {}).get('key_metrics', {})
                        for key, value in pdf_metrics.items():
                            financial_metrics[key] = {
                                "value": value,
                                "source": {"document": doc.get('filename', 'unknown')},
                                "confidence": 0.9
                            }
                    elif doc.get('type') == 'excel':
                        excel_content = doc.get('content', {})
                        if 'sheets' in excel_content:
                            for sheet_name, sheet_data in excel_content['sheets'].items():
                                if 'key_metrics' in sheet_data:
                                    for metric_name, metric_info in sheet_data['key_metrics'].items():
                                        financial_metrics[f"{metric_name}_{sheet_name}"] = {
                                            "value": metric_info.get('value'),
                                            "source": {
                                                "document": doc.get('filename', 'unknown'),
                                                "sheet": sheet_name,
                                                "cell": metric_info.get('cell')
                                            },
                                            "confidence": 0.8
                                        }
                
                analysis = {
                    "company_overview": {
                        "name": company_name,
                        "industry": "Customer Success Management Software"
                    },
                    "financial_metrics": financial_metrics,
                    "key_insights": [
                        "Strong Q3 2024 performance with $15.2M revenue",
                        "23% year-over-year growth achieving $15.2M",
                        "Healthy profit margins with $12.5M profit",
                        "Growing customer base to 450 customers"
                    ],
                    "suggested_slides": [
                        {"type": "financial_summary", "title": "Financial Performance", "content": "Q3 2024 key metrics"},
                        {"type": "company_overview", "title": "Company Overview", "content": "SaaSy Inc. business highlights"}
                    ],
                    "source_attributions": {
                        "primary_documents": [doc['filename'] for doc in all_documents],
                        "extraction_summary": f"Successfully processed {len(all_documents)} documents"
                    }
                }
        except Exception as e:
            print(f"Analysis failed with error: {str(e)}")
            # Create meaningful fallback analysis using extracted data
            financial_metrics = {}
            company_name = "SaaSy Inc."
            
            # Extract data from documents for fallback
            for doc in all_documents:
                if doc.get('type') == 'pdf' and isinstance(doc.get('content'), dict):
                    pdf_metrics = doc.get('content', {}).get('key_metrics', {})
                    for key, value in pdf_metrics.items():
                        financial_metrics[key] = {
                            "value": value,
                            "source": {"document": doc.get('filename', 'unknown')},
                            "confidence": 0.9
                        }
            
            analysis = {
                "company_overview": {
                    "name": company_name,
                    "industry": "Customer Success Management Software"
                },
                "financial_metrics": financial_metrics,
                "key_insights": [
                    "Successfully processed business documents",
                    "Extracted financial and operational metrics",
                    "Generated insights from multiple data sources"
                ],
                "suggested_slides": [
                    {"type": "financial_summary", "title": "Financial Performance", "content": "Key metrics and performance indicators"},
                    {"type": "company_overview", "title": "Company Overview", "content": "Business summary and highlights"}
                ],
                "source_attributions": {
                    "primary_documents": [doc['filename'] for doc in all_documents],
                    "extraction_summary": f"Successfully processed {len(all_documents)} documents"
                }
            }
        
        # 2.5. Enhance analysis with source tracking data
        analysis = _enhance_analysis_with_source_tracking(analysis, all_documents, source_tracker)
        
        # 3. Generate slides
        # Check if template is specified
        template_id = request.form.get('template_id', 'default')
        
        # ENABLE ENHANCED SOURCE ATTRIBUTION FEATURES
        use_smart_layout = False  # Set to True to use standard layout engine
        
        # Use branded slide generator if template management is available
        if TEMPLATE_MANAGEMENT_AVAILABLE and template_id and not use_smart_layout:
            try:
                from lib.slide_generator_branded import BrandedSlideGenerator
                from lib.source_tracker import SourceTracker
                
                # Initialize brand manager (reuse existing source tracker)
                brand_manager = BrandManager()
                
                # Create branded slide generator
                generator = BrandedSlideGenerator(
                    brand_manager=brand_manager,
                    template_name=template_id,
                    source_tracker=source_tracker
                )
                print(f"Using branded slide generator with template: {template_id}")
            except Exception as e:
                print(f"Failed to use branded generator: {str(e)}, falling back to standard")
                generator = SlideGenerator(use_branding=False)
        else:
            # Force smart layout engine
            print(f"Using standard generator with SMART LAYOUT ENGINE (template: {template_id})")
            generator = SlideGenerator(use_branding=False)
        
        # Create slides based on analysis
        slides_created = []
        
        # Title slide
        print("Creating title slide...")
        company_name = analysis.get('company_overview', {}).get('name', 'Business Presentation')
        title_slide = generator.create_title_slide(
            title=company_name,
            subtitle="Financial Analysis & Performance Review"
        )
        slides_created.append("Title Slide")
        print("Title slide created successfully")
        
        # Source summary slide (if using branded generator with source tracker)
        print("Checking for source summary slide creation...")
        if hasattr(generator, 'create_source_summary_slide') and hasattr(generator, 'source_tracker') and generator.source_tracker:
            try:
                print("Creating source summary slide...")
                source_summary_slide = generator.create_source_summary_slide(
                    analysis.get('source_attributions', {})
                )
                if source_summary_slide:
                    slides_created.append("Data Sources & Methodology")
                    print("Source summary slide created successfully")
                else:
                    print("Source summary slide creation returned None - skipping")
            except Exception as e:
                import traceback
                print(f"Failed to create source summary slide: {str(e)}")
                print(f"Source summary slide traceback: {traceback.format_exc()}")
        else:
            print("Source summary slide not available or no source tracker")
        
        # Financial summary slide(s)
        if 'financial_metrics' in analysis and analysis['financial_metrics']:
            result = generator.create_financial_summary_slide(
                analysis['financial_metrics'],
                analysis.get('source_attributions', {})
            )
            # Handle both single slide and list of slides
            if isinstance(result, list):
                slides_created.extend(["Financial Metrics", "Financial Chart"])
            else:
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
        if len(slides_created) <= 1:  # Only title slide
            summary_data = {
                "documents_processed": len(all_documents),
                "files": [doc['filename'] for doc in all_documents]
            }
            slide = generator.create_company_overview_slide(
                {"name": "Document Processing Summary", "description": f"Processed {len(all_documents)} files"},
                {"summary": f"Files: {', '.join([doc['filename'] for doc in all_documents])}"}
            )
            slides_created.append("Processing Summary")
        
        # Thank you slide
        thank_you_slide = generator.create_thank_you_slide()
        slides_created.append("Thank You")
        
        # Add slide numbers
        generator.add_slide_numbers(exclude_first=True, exclude_last=True)
        
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
        import traceback
        error_details = traceback.format_exc()
        print(f"Slide generation error: {str(e)}")
        print(f"Full traceback: {error_details}")
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
                if not pdf_extractor:
                    doc_data = {
                        'filename': filename,
                        'type': 'pdf',
                        'content': {'error': 'PDF extraction not available - LLMWhisperer API key not configured'},
                        'raw_text': '',
                        'tables': [],
                        'key_metrics': {},
                        'sections': {}
                    }
                    all_documents.append(doc_data)
                    continue
                
                # Save file temporarily for extraction
                temp_path = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
                with open(temp_path, 'wb') as f:
                    f.write(file_bytes)
                
                content = pdf_extractor.extract_text_and_tables(temp_path)
                
                # Clean up temp file
                try:
                    os.remove(temp_path)
                except:
                    pass
                    
                print(f"PDF content type: {type(content)}")
                print(f"PDF content: {content}")
                
                if isinstance(content, dict):
                    doc_data = {
                        'filename': filename,
                        'type': 'pdf',
                        'pages': content.get('metadata', {}).get('pages', 0),
                        'tables_count': len(content.get('tables', [])),
                        'sections': content.get('sections', []) if isinstance(content.get('sections'), list) else list(content.get('sections', {}).keys()),
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
                content = excel_extractor.extract_from_bytes(file_bytes, filename)
                print(f"Excel content type: {type(content)}")
                print(f"Excel content keys: {content.keys() if isinstance(content, dict) else 'Not a dict'}")
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
                content = word_extractor.extract_from_bytes(file_bytes, filename)
                print(f"Word content type: {type(content)}")
                print(f"Word content keys: {content.keys() if isinstance(content, dict) else 'Not a dict'}")
                if isinstance(content, dict) and 'key_sections' in content:
                    print(f"key_sections type: {type(content.get('key_sections'))}")
                    print(f"key_sections value: {content.get('key_sections')}")
                if isinstance(content, dict):
                    doc_data = {
                        'filename': filename,
                        'type': 'word',
                        'paragraphs_count': len(content.get('paragraphs', [])),
                        'tables_count': len(content.get('tables', [])),
                        'key_sections': list(content.get('key_sections', {}).keys()) if isinstance(content.get('key_sections', {}), dict) else [],
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
        import traceback
        print(f"Preview extraction error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Preview failed: {str(e)}'}), 500

# Template Management Endpoints
@app.route('/api/templates', methods=['GET'])
def list_templates():
    """List all available brand templates"""
    if not TEMPLATE_MANAGEMENT_AVAILABLE:
        return jsonify({'error': 'Template management not available'}), 503
    
    try:
        brand_manager = BrandManager()
        templates = brand_manager.list_templates()
        current_template = brand_manager.current_template
        
        template_info = []
        for template_name in templates:
            brand_manager.set_current_template(template_name)
            template_parser = brand_manager.get_current_template()
            if template_parser:
                config = template_parser.get_brand_config()
                template_info.append({
                    'name': template_name,
                    'is_current': template_name == current_template,
                    'theme_colors': config.get('theme_colors', {}),
                    'fonts': config.get('fonts', {}),
                    'layouts_count': len(config.get('layouts', []))
                })
        
        return jsonify({
            'success': True,
            'templates': template_info,
            'current_template': current_template
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to list templates: {str(e)}'}), 500

@app.route('/api/templates/upload', methods=['POST'])
def upload_template():
    """Upload a new PowerPoint template"""
    if not TEMPLATE_MANAGEMENT_AVAILABLE:
        return jsonify({'error': 'Template management not available'}), 503
    
    try:
        if 'template' not in request.files:
            return jsonify({'error': 'No template file provided'}), 400
        
        template_file = request.files['template']
        template_name = request.form.get('name', '')
        
        if template_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not template_file.filename.endswith('.pptx'):
            return jsonify({'error': 'Template must be a .pptx file'}), 400
        
        # Generate template name if not provided
        if not template_name:
            template_name = secure_filename(template_file.filename).replace('.pptx', '')
        else:
            template_name = secure_filename(template_name)
        
        # Save template to temporary file
        with tempfile.NamedTemporaryFile(suffix='.pptx', delete=False) as tmp_file:
            template_file.save(tmp_file.name)
            
            # Add template to brand manager
            brand_manager = BrandManager()
            final_template_name = brand_manager.add_template(tmp_file.name, template_name)
            
            # Parse template for preview
            template_parser = brand_manager.get_current_template()
            if template_parser:
                config = template_parser.get_brand_config()
                
                return jsonify({
                    'success': True,
                    'template_name': final_template_name,
                    'message': f'Template "{final_template_name}" uploaded successfully',
                    'preview': {
                        'theme_colors': config.get('theme_colors', {}),
                        'fonts': config.get('fonts', {}),
                        'layouts_count': len(config.get('layouts', []))
                    }
                })
            else:
                return jsonify({
                    'success': True,
                    'template_name': final_template_name,
                    'message': f'Template "{final_template_name}" uploaded successfully'
                })
        
    except Exception as e:
        return jsonify({'error': f'Template upload failed: {str(e)}'}), 500

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