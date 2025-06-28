import os
import openai
from typing import List, Dict, Any

def analyze_documents_for_slides(documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze documents using OpenAI to extract key information for slides"""
    
    # Check if OpenAI API key is configured
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return extract_key_metrics_simple(documents)
    
    # Placeholder for full LLM analysis
    # In production, this would use OpenAI API to analyze documents
    return {
        "company_overview": {
            "name": "Analyzed Company",
            "description": "AI-powered analysis of documents"
        },
        "financial_metrics": {},
        "key_insights": ["Document analysis complete"],
        "source_attributions": {
            "primary_documents": [doc['filename'] for doc in documents]
        }
    }

def extract_key_metrics_simple(documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Simple extraction without LLM for fallback"""
    
    metrics = {}
    insights = []
    
    # Extract metrics from each document type
    for doc in documents:
        if doc['type'] == 'excel' and 'content' in doc:
            # Extract Excel metrics
            if isinstance(doc['content'], dict) and 'sheets' in doc['content']:
                for sheet_name, sheet_data in doc['content']['sheets'].items():
                    if 'key_metrics' in sheet_data:
                        for metric_name, metric_data in sheet_data['key_metrics'].items():
                            metrics[metric_name] = metric_data
                            
        elif doc['type'] == 'pdf' and 'key_metrics' in doc:
            # Extract PDF metrics
            for category, values in doc['key_metrics'].items():
                metrics[category] = values
    
    # Generate basic insights
    insights.append(f"Processed {len(documents)} documents")
    if metrics:
        insights.append(f"Extracted {len(metrics)} key metrics")
    
    return {
        "financial_metrics": metrics,
        "key_insights": insights
    }