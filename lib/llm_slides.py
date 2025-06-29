import json
import logging
from openai import OpenAI
from typing import Dict, List, Any
import re

class LLMSlideGenerator:
    """
    Generate presentation slides using OpenAI API
    """
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        
    def generate_slides(self, extracted_data: Dict[str, Any], template_name: str = "sample_brand") -> Dict[str, Any]:
        """
        Generate presentation slides from extracted document data
        
        Args:
            extracted_data: Document extraction results
            template_name: PowerPoint template to use
            
        Returns:
            Generated slides data with analysis and attribution
        """
        try:
            # Step 1: Analyze extracted data
            analysis = self._analyze_documents(extracted_data)
            if not analysis:
                return {"error": "Failed to analyze documents"}
            
            # Step 2: Generate slide content
            slides = self._generate_slide_content(analysis)
            if not slides:
                return {"error": "Failed to generate slide content"}
            
            # Step 3: Create source attribution
            attribution = self._create_source_attribution(extracted_data)
            
            return {
                "slides": slides,
                "analysis": analysis,
                "attribution": attribution,
                "template": template_name,
                "status": "success"
            }
            
        except Exception as e:
            logging.error(f"Error generating slides: {str(e)}")
            return {"error": f"Error generating slides: {str(e)}"}
    
    def _analyze_documents(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze extracted document data to identify key insights
        """
        try:
            # Prepare context from all documents
            context = self._prepare_context(extracted_data)
            
            # Create analysis prompt
            prompt = f"""
Analyze the following business documents and extract key insights for a presentation. 
Return ONLY a valid JSON object with the following structure:

{{
  "company_overview": {{
    "name": "Company name",
    "industry": "Industry sector",
    "stage": "Business stage"
  }},
  "financial_highlights": {{
    "revenue": "Revenue figure with source",
    "growth_rate": "Growth percentage",
    "key_metrics": ["metric1", "metric2", "metric3"]
  }},
  "strategic_insights": [
    "Key insight 1",
    "Key insight 2",
    "Key insight 3"
  ],
  "market_position": {{
    "market_size": "Market size if available",
    "competitive_advantage": "Key differentiator"
  }}
}}

Document Data:
{context}

Respond with ONLY the JSON object, no additional text or formatting:"""
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a business analyst that extracts key insights from documents. You MUST respond with only valid JSON, no markdown or additional text."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            # Extract and parse response
            response_text = response.choices[0].message.content
            logging.info(f"OpenAI analysis response: {response_text[:200]}...")
            
            # Parse JSON with robust error handling
            analysis = self._parse_json_response(response_text)
            
            if not analysis:
                logging.error("Failed to parse analysis JSON")
                return self._fallback_analysis(extracted_data)
            
            return analysis
        
        except Exception as e:
            logging.error(f"Error in document analysis: {str(e)}")
            return self._fallback_analysis(extracted_data)
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        Robustly parse JSON from OpenAI response
        """
        try:
            # Try direct parsing first
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Clean up common issues
            cleaned_text = response_text.strip()
            
            # Remove markdown code blocks if present
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith('```'):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text[:-3]
            
            # Remove any text before/after JSON
            json_start = cleaned_text.find('{')
            json_end = cleaned_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                cleaned_text = cleaned_text[json_start:json_end]
            
            # Try parsing cleaned text
            try:
                return json.loads(cleaned_text)
            except json.JSONDecodeError:
                # Try fixing common JSON issues
                fixed_text = cleaned_text.replace('\n', ' ').replace('\t', ' ')
                fixed_text = re.sub(r'\s+', ' ', fixed_text)
                
                try:
                    return json.loads(fixed_text)
                except json.JSONDecodeError:
                    logging.error(f"Could not parse JSON: {response_text[:200]}...")
                    return None
    
    def _prepare_context(self, extracted_data: Dict[str, Any]) -> str:
        """
        Prepare context string from extracted document data
        """
        context_parts = []
        
        for doc_type, doc_data in extracted_data.items():
            if isinstance(doc_data, dict):
                context_parts.append(f"\n{doc_type.upper()} DOCUMENT:")
                
                # Add sample text if available
                if 'sample_text' in doc_data:
                    context_parts.append(f"Content: {doc_data['sample_text'][:500]}")
                
                # Add key metrics
                if 'key_metrics' in doc_data:
                    context_parts.append(f"Key Metrics: {doc_data['key_metrics']}")
                
                # Add structure info
                if 'sections' in doc_data:
                    context_parts.append(f"Sections: {doc_data['sections']}")
        
        return "\n".join(context_parts)
    
    def _generate_slide_content(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate slide content based on analysis
        """
        slides = []
        
        try:
            # Title slide
            company_name = analysis.get('company_overview', {}).get('name', 'Company')
            slides.append({
                "type": "title",
                "title": f"{company_name} - Business Overview",
                "subtitle": "Key Performance Highlights"
            })
            
            # Financial highlights slide
            financial = analysis.get('financial_highlights', {})
            slides.append({
                "type": "content",
                "title": "Financial Performance",
                "content": [
                    f"Revenue: {financial.get('revenue', 'N/A')}",
                    f"Growth Rate: {financial.get('growth_rate', 'N/A')}",
                    "Key Metrics:"
                ] + financial.get('key_metrics', [])
            })
            
            # Strategic insights slide
            insights = analysis.get('strategic_insights', [])
            slides.append({
                "type": "content",
                "title": "Strategic Insights",
                "content": insights
            })
            
            # Market position slide
            market = analysis.get('market_position', {})
            slides.append({
                "type": "content",
                "title": "Market Position",
                "content": [
                    f"Market Size: {market.get('market_size', 'N/A')}",
                    f"Competitive Advantage: {market.get('competitive_advantage', 'N/A')}"
                ]
            })
            
            return slides
            
        except Exception as e:
            logging.error(f"Error generating slide content: {str(e)}")
            return [{
                "type": "error",
                "title": "Error",
                "content": [f"Error generating slides: {str(e)}"]
            }]
    
    def _create_source_attribution(self, extracted_data: Dict[str, Any]) -> List[str]:
        """
        Create source attribution for generated content
        """
        attribution = []
        
        for doc_type, doc_data in extracted_data.items():
            if isinstance(doc_data, dict) and 'filename' in doc_data:
                filename = doc_data['filename']
                doc_type_name = doc_data.get('type', 'document')
                
                if doc_type_name == 'pdf':
                    pages = doc_data.get('pages', 0)
                    attribution.append(f"{filename} ({doc_type_name}, {pages} pages)")
                elif doc_type_name == 'excel':
                    sheets = list(doc_data.get('summary', {}).keys())
                    attribution.append(f"{filename} ({doc_type_name}, sheets: {', '.join(sheets)})")
                elif doc_type_name == 'word':
                    paragraphs = doc_data.get('paragraphs_count', 0)
                    attribution.append(f"{filename} ({doc_type_name}, {paragraphs} paragraphs)")
                else:
                    attribution.append(f"{filename} ({doc_type_name})")
        
        return attribution
    
    def _fallback_analysis(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create fallback analysis when OpenAI analysis fails
        """
        return {
            "company_overview": {
                "name": "Company",
                "industry": "Business",
                "stage": "Growth"
            },
            "financial_highlights": {
                "revenue": "Revenue data available in documents",
                "growth_rate": "Growth data available in documents",
                "key_metrics": ["See source documents for detailed metrics"]
            },
            "strategic_insights": [
                "Key business insights extracted from documents",
                "Financial performance data available",
                "Strategic information provided in source materials"
            ],
            "market_position": {
                "market_size": "Market data in source documents",
                "competitive_advantage": "Competitive positioning available"
            }
        }
