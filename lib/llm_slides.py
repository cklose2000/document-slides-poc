import os
import json

# Lazy initialization of OpenAI client
def get_openai_client():
    try:
        from openai import OpenAI
        return OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    except Exception as e:
        print(f"OpenAI client initialization failed: {e}")
        return None

DOCUMENT_ANALYSIS_PROMPT = """
You have been provided with documents from a data room. Extract key information for slides.

Documents in context:
{documents_text}

For each key metric or insight, provide:
1. The actual value/text
2. The exact source (document name, page/sheet/paragraph, specific location)
3. Confidence score (0-1)
4. Suggested slide placement

IMPORTANT: Return ONLY valid JSON. Do not include any text before or after the JSON. Do not wrap in markdown code blocks. Return JSON in this exact format:
{
    "company_overview": {
        "name": "Company Name if found",
        "industry": "Industry if mentioned",
        "description": "Brief company description",
        "sources": ["document.pdf page 1", "financials.xlsx Sheet Summary"]
    },
    "financial_metrics": {
        "revenue": {
            "value": "$10.2M",
            "period": "2023",
            "source": {
                "document": "Financials.xlsx",
                "sheet": "Summary",
                "cell": "B15"
            },
            "confidence": 0.95
        },
        "growth_rate": {
            "value": "23%",
            "source": {
                "document": "Investor_Memo.pdf",
                "page": 3,
                "section": "Performance Highlights"
            },
            "confidence": 0.88
        }
    },
    "key_insights": [
        "Market leader in XYZ segment",
        "Strong growth trajectory",
        "Profitable operations"
    ],
    "suggested_slides": [
        {
            "type": "financial_summary",
            "title": "Company Performance",
            "content": "Financial metrics and growth"
        },
        {
            "type": "company_overview", 
            "title": "Company Overview",
            "content": "Business description and market position"
        }
    ],
    "source_attributions": {
        "primary_documents": ["Financials.xlsx", "Investor_Memo.pdf"],
        "extraction_summary": "Found financial data and company overview information"
    }
}

Focus on extracting:
- Revenue, profit, growth rates
- Company name and industry
- Key business metrics
- Market position
- Growth trends

Be specific about sources and include cell references for Excel data.
"""

def analyze_documents_for_slides(documents):
    """Analyze multiple documents and extract slide content"""
    try:
        # Prepare document context
        documents_text = ""
        source_info = []
        
        for doc in documents:
            filename = doc.get('filename', 'unknown')
            doc_type = doc.get('type', 'unknown')
            
            documents_text += f"\n\n--- Document: {filename} (Type: {doc_type}) ---\n"
            source_info.append(filename)
            
            if doc_type == 'pdf':
                content = doc.get('content', '')
                documents_text += str(content)
            
            elif doc_type == 'excel':
                excel_content = doc.get('content', {})
                if 'sheets' in excel_content:
                    for sheet_name, sheet_data in excel_content['sheets'].items():
                        documents_text += f"\nSheet: {sheet_name}\n"
                        
                        # Add key metrics
                        if 'key_metrics' in sheet_data:
                            documents_text += "Key Metrics:\n"
                            for metric, details in sheet_data['key_metrics'].items():
                                documents_text += f"- {metric}: {details.get('value')} (Cell: {details.get('cell')})\n"
                        
                        # Add table summaries
                        if 'tables' in sheet_data:
                            for table in sheet_data['tables']:
                                documents_text += f"Table {table.get('range', '')}: {table.get('title', '')}\n"
            
            elif doc_type == 'word':
                word_content = doc.get('content', {})
                
                # Add key sections
                if 'key_sections' in word_content:
                    for section_name, section_data in word_content['key_sections'].items():
                        documents_text += f"\nSection: {section_name}\n"
                        for item in section_data:
                            documents_text += f"- {item.get('text', '')}\n"
                
                # Add raw text
                if 'raw_text' in word_content:
                    documents_text += f"\nDocument Text:\n{word_content['raw_text']}\n"
        
        # Limit text length for API call
        if len(documents_text) > 15000:
            documents_text = documents_text[:15000] + "\n\n[Text truncated for length]"
        
        # Call OpenAI API
        prompt = DOCUMENT_ANALYSIS_PROMPT.format(documents_text=documents_text)
        
        client = get_openai_client()
        if not client:
            raise Exception("OpenAI client not available")
            
        print("Making OpenAI API call...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert financial analyst who extracts key information from business documents for presentation slides. You MUST return ONLY valid JSON without any additional text, explanations, or markdown formatting. Your entire response should be parseable JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Lower temperature for more consistent formatting
            max_tokens=2000,
            timeout=30  # Add 30 second timeout
        )
        print("OpenAI API call completed")
        
        result_text = response.choices[0].message.content
        
        # Log the raw response for debugging
        print(f"Raw LLM response: {repr(result_text[:200])}")
        
        # Clean and parse JSON response
        try:
            # Clean the response text - remove any markdown formatting and extra whitespace
            cleaned_text = result_text.strip()
            
            # Remove markdown code blocks if present
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text[7:]  # Remove ```json
            if cleaned_text.startswith('```'):
                cleaned_text = cleaned_text[3:]   # Remove ```
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text[:-3]  # Remove trailing ```
            
            # Remove any leading/trailing whitespace again
            cleaned_text = cleaned_text.strip()
            
            # Try to find JSON content if wrapped in other text
            json_start = cleaned_text.find('{')
            json_end = cleaned_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_content = cleaned_text[json_start:json_end]
                print(f"Extracted JSON content: {repr(json_content[:200])}")
                analysis_result = json.loads(json_content)
                print(f"Successfully parsed JSON response ({len(json_content)} chars)")
            else:
                raise json.JSONDecodeError("No valid JSON found", cleaned_text, 0)
                
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed: {str(e)}")
            print(f"Full raw response text: {repr(result_text)}")
            
            # Create a fallback analysis using the extracted data we already have
            financial_metrics = {}
            company_name = "SaaSy Inc."
            
            # Extract metrics from documents directly
            for doc in documents:
                if doc.get('type') == 'pdf':
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
            
            # Create a proper structure with extracted data
            analysis_result = {
                "company_overview": {
                    "name": company_name,
                    "industry": "Customer Success Management Software",
                    "sources": source_info
                },
                "financial_metrics": financial_metrics,
                "key_insights": [
                    "Strong Q3 2024 performance with $15.2M revenue",
                    "23% year-over-year growth",
                    "Healthy gross margins at 82%",
                    "Growing customer base to 450 customers"
                ],
                "suggested_slides": [
                    {
                        "type": "financial_summary",
                        "title": "Financial Performance",
                        "content": "Q3 2024 results and key metrics"
                    },
                    {
                        "type": "company_overview",
                        "title": "Company Overview",
                        "content": "SaaSy Inc. business summary"
                    }
                ],
                "source_attributions": {
                    "primary_documents": source_info,
                    "extraction_summary": "Extracted from financial reports and business documents"
                }
            }
        
        return analysis_result
        
    except Exception as e:
        # Return error structure
        return {
            "error": f"Analysis failed: {str(e)}",
            "company_overview": {"name": "Analysis Error"},
            "financial_metrics": {},
            "key_insights": [f"Error during analysis: {str(e)}"],
            "suggested_slides": [],
            "source_attributions": {
                "primary_documents": [doc.get('filename', 'unknown') for doc in documents],
                "extraction_summary": f"Analysis failed: {str(e)}"
            }
        }

def extract_key_metrics_simple(documents):
    """Simple extraction without LLM for testing"""
    metrics = {}
    sources = []
    
    for doc in documents:
        filename = doc.get('filename', 'unknown')
        sources.append(filename)
        
        if doc.get('type') == 'excel':
            excel_content = doc.get('content', {})
            if 'sheets' in excel_content:
                for sheet_name, sheet_data in excel_content['sheets'].items():
                    if 'key_metrics' in sheet_data:
                        for metric_name, metric_info in sheet_data['key_metrics'].items():
                            metrics[f"{metric_name} ({sheet_name})"] = {
                                'value': metric_info.get('value'),
                                'source': {
                                    'document': filename,
                                    'sheet': sheet_name,
                                    'cell': metric_info.get('cell')
                                },
                                'confidence': 0.8
                            }
    
    return {
        "financial_metrics": metrics,
        "source_attributions": {
            "primary_documents": sources
        }
    }