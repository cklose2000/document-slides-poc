"""
Template Manager for dynamic template selection and content analysis
"""

import os
import json
from typing import Dict, List, Any, Optional, Tuple
import re
from pathlib import Path

class TemplateManager:
    """
    Manages template selection based on content analysis and user preferences
    """
    
    def __init__(self, templates_directory: str = None):
        """
        Initialize template manager
        
        Args:
            templates_directory: Path to templates directory
        """
        if templates_directory is None:
            # Default to templates directory relative to this file
            current_dir = Path(__file__).parent
            self.templates_dir = current_dir.parent / "templates"
        else:
            self.templates_dir = Path(templates_directory)
        
        self.templates_cache = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load all available templates from the templates directory"""
        if not self.templates_dir.exists():
            print(f"Templates directory not found: {self.templates_dir}")
            return
        
        for template_dir in self.templates_dir.iterdir():
            if template_dir.is_dir():
                metadata_file = template_dir / "metadata.json"
                template_file = template_dir / "template.pptx"
                
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        
                        self.templates_cache[metadata['id']] = {
                            'metadata': metadata,
                            'template_path': str(template_file) if template_file.exists() else None,
                            'metadata_path': str(metadata_file)
                        }
                        
                        print(f"Loaded template: {metadata['name']} ({metadata['id']})")
                        
                    except Exception as e:
                        print(f"Error loading template {template_dir.name}: {str(e)}")
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """
        Get list of all available templates
        
        Returns:
            List of template information dictionaries
        """
        templates = []
        for template_id, template_info in self.templates_cache.items():
            metadata = template_info['metadata']
            templates.append({
                'id': template_id,
                'name': metadata['name'],
                'description': metadata['description'],
                'features': metadata.get('features', []),
                'industry_focus': metadata.get('industry_focus', {}),
                'colors': metadata.get('colors', {}),
                'available': template_info['template_path'] is not None
            })
        
        return sorted(templates, key=lambda x: x['name'])
    
    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific template information
        
        Args:
            template_id: Template identifier
            
        Returns:
            Template information or None if not found
        """
        return self.templates_cache.get(template_id)
    
    def analyze_content_for_template(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze document content to recommend appropriate template
        
        Args:
            documents: List of document data
            
        Returns:
            Analysis results with template recommendations
        """
        analysis = {
            'content_type': 'general',
            'industry_indicators': {},
            'metrics_detected': [],
            'recommended_templates': [],
            'confidence_scores': {}
        }
        
        # Extract text content from all documents
        all_text = ""
        for doc in documents:
            if doc.get('type') == 'pdf':
                content = doc.get('content', {})
                if isinstance(content, dict):
                    all_text += content.get('raw_text', '') + " "
            elif doc.get('type') == 'word':
                content = doc.get('content', {})
                if isinstance(content, dict):
                    all_text += content.get('raw_text', '') + " "
            elif doc.get('type') == 'excel':
                # Extract text from Excel metadata and sheet names
                content = doc.get('content', {})
                if isinstance(content, dict) and 'sheets' in content:
                    for sheet_name, sheet_data in content['sheets'].items():
                        all_text += f"{sheet_name} "
                        if 'key_metrics' in sheet_data:
                            for metric in sheet_data['key_metrics'].keys():
                                all_text += f"{metric} "
        
        all_text = all_text.lower()
        
        # Analyze for industry indicators
        industry_scores = self._analyze_industry_indicators(all_text)
        analysis['industry_indicators'] = industry_scores
        
        # Detect metrics
        metrics_detected = self._detect_metrics(all_text, documents)
        analysis['metrics_detected'] = metrics_detected
        
        # Generate template recommendations
        recommendations = self._generate_recommendations(industry_scores, metrics_detected)
        analysis['recommended_templates'] = recommendations
        analysis['confidence_scores'] = {rec['template_id']: rec['confidence'] for rec in recommendations}
        
        return analysis
    
    def _analyze_industry_indicators(self, text: str) -> Dict[str, float]:
        """Analyze text for industry-specific indicators"""
        indicators = {
            'saas': {
                'keywords': [
                    'saas', 'software as a service', 'subscription', 'cloud',
                    'mrr', 'arr', 'monthly recurring revenue', 'annual recurring revenue',
                    'churn', 'retention', 'user acquisition', 'freemium',
                    'api', 'platform', 'dashboard', 'analytics', 'engagement',
                    'signup', 'conversion', 'trial', 'upgrade', 'downgrade'
                ],
                'weight': 1.0
            },
            'manufacturing': {
                'keywords': [
                    'manufacturing', 'production', 'factory', 'assembly',
                    'oee', 'overall equipment effectiveness', 'throughput', 'yield',
                    'quality control', 'defect', 'inspection', 'process',
                    'inventory', 'supply chain', 'logistics', 'warehouse',
                    'cycle time', 'efficiency', 'capacity', 'utilization',
                    'safety', 'compliance', 'regulatory'
                ],
                'weight': 1.0
            },
            'healthcare': {
                'keywords': [
                    'healthcare', 'medical', 'hospital', 'clinical', 'patient',
                    'diagnosis', 'treatment', 'therapy', 'pharmaceutical',
                    'compliance', 'regulatory', 'fda', 'hipaa', 'quality measures',
                    'outcomes', 'mortality', 'readmission', 'length of stay',
                    'satisfaction', 'safety', 'infection', 'protocol'
                ],
                'weight': 1.0
            },
            'corporate': {
                'keywords': [
                    'revenue', 'profit', 'financial', 'quarterly', 'annual',
                    'budget', 'forecast', 'growth', 'market share', 'ebitda',
                    'roi', 'investment', 'strategy', 'executive', 'board',
                    'shareholders', 'dividend', 'acquisition', 'merger'
                ],
                'weight': 0.8
            }
        }
        
        scores = {}
        for industry, data in indicators.items():
            score = 0
            keyword_count = 0
            
            for keyword in data['keywords']:
                if keyword in text:
                    # Count occurrences and weight by keyword importance
                    occurrences = text.count(keyword)
                    score += occurrences * data['weight']
                    keyword_count += 1
            
            # Normalize score by number of keywords found and text length
            if keyword_count > 0:
                scores[industry] = min(score / max(len(text.split()) / 100, 1), 10.0)
            else:
                scores[industry] = 0.0
        
        return scores
    
    def _detect_metrics(self, text: str, documents: List[Dict[str, Any]]) -> List[str]:
        """Detect specific business metrics in the content"""
        metrics_patterns = {
            # SaaS metrics
            'MRR': r'\bmrr\b|\bmonthly recurring revenue\b',
            'ARR': r'\barr\b|\bannual recurring revenue\b',
            'Churn Rate': r'\bchurn\b|\bchurn rate\b',
            'CAC': r'\bcac\b|\bcustomer acquisition cost\b',
            'LTV': r'\bltv\b|\blifetime value\b',
            
            # Manufacturing metrics
            'OEE': r'\boee\b|\boverall equipment effectiveness\b',
            'Throughput': r'\bthroughput\b',
            'Cycle Time': r'\bcycle time\b',
            'First Pass Yield': r'\bfirst pass yield\b|\bfpy\b',
            'Defect Rate': r'\bdefect rate\b|\bdefects?\b',
            
            # Healthcare metrics
            'Patient Satisfaction': r'\bpatient satisfaction\b|\bhcahps\b',
            'Readmission Rate': r'\breadmission\b|\breadmit\b',
            'Length of Stay': r'\blength of stay\b|\blos\b',
            'Mortality Rate': r'\bmortality\b|\bdeath rate\b',
            
            # General financial metrics
            'Revenue': r'\brevenue\b|\bsales\b',
            'Profit': r'\bprofit\b|\bearnings\b|\bebitda\b',
            'Growth Rate': r'\bgrowth\b.*\brate\b|\byoy\b|\byear.over.year\b',
            'ROI': r'\broi\b|\breturn on investment\b',
            'Market Share': r'\bmarket share\b'
        }
        
        detected_metrics = []
        for metric_name, pattern in metrics_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                detected_metrics.append(metric_name)
        
        # Also check for numeric values that might be metrics from structured data
        for doc in documents:
            if doc.get('type') == 'excel':
                content = doc.get('content', {})
                if isinstance(content, dict) and 'sheets' in content:
                    for sheet_data in content['sheets'].values():
                        if 'key_metrics' in sheet_data:
                            detected_metrics.extend(sheet_data['key_metrics'].keys())
        
        return list(set(detected_metrics))  # Remove duplicates
    
    def _generate_recommendations(self, industry_scores: Dict[str, float], 
                                metrics_detected: List[str]) -> List[Dict[str, Any]]:
        """Generate template recommendations based on analysis"""
        recommendations = []
        
        # Score templates based on industry indicators
        for template_id, template_info in self.templates_cache.items():
            metadata = template_info['metadata']
            confidence = 0.0
            reasons = []
            
            # Industry match scoring
            if template_id in industry_scores:
                industry_score = industry_scores[template_id]
                confidence += industry_score * 0.6  # 60% weight for industry match
                if industry_score > 1.0:
                    reasons.append(f"Strong {metadata['name']} industry indicators")
            
            # Metrics match scoring
            if 'industry_focus' in metadata and 'metrics' in metadata['industry_focus']:
                template_metrics = [m.lower() for m in metadata['industry_focus']['metrics']]
                detected_lower = [m.lower() for m in metrics_detected]
                
                metric_matches = 0
                for detected_metric in detected_lower:
                    for template_metric in template_metrics:
                        if detected_metric in template_metric or template_metric in detected_metric:
                            metric_matches += 1
                            break
                
                if template_metrics:
                    metric_score = (metric_matches / len(template_metrics)) * 4.0
                    confidence += metric_score * 0.4  # 40% weight for metrics match
                    
                    if metric_matches > 0:
                        reasons.append(f"Matches {metric_matches} key metrics")
            
            # Default template gets base score
            if template_id == 'default' or template_id == 'corporate':
                confidence = max(confidence, 2.0)  # Minimum viable score
                if not reasons:
                    reasons.append("General business template")
            
            recommendations.append({
                'template_id': template_id,
                'template_name': metadata['name'],
                'confidence': round(confidence, 2),
                'reasons': reasons,
                'features': metadata.get('features', [])
            })
        
        # Sort by confidence score
        recommendations.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Only return templates with reasonable confidence
        return [rec for rec in recommendations if rec['confidence'] > 0.5]
    
    def get_recommended_template(self, documents: List[Dict[str, Any]], 
                               user_preference: str = None) -> Tuple[str, Dict[str, Any]]:
        """
        Get the best recommended template for the given documents
        
        Args:
            documents: List of document data
            user_preference: Optional user template preference
            
        Returns:
            Tuple of (template_id, analysis_results)
        """
        analysis = self.analyze_content_for_template(documents)
        
        # If user has a preference and it exists, use it
        if user_preference and user_preference in self.templates_cache:
            template_info = self.templates_cache[user_preference]
            if template_info['template_path']:
                return user_preference, analysis
        
        # Otherwise use the highest confidence recommendation
        if analysis['recommended_templates']:
            best_recommendation = analysis['recommended_templates'][0]
            template_id = best_recommendation['template_id']
            
            # Ensure the template file exists
            template_info = self.templates_cache.get(template_id)
            if template_info and template_info['template_path']:
                return template_id, analysis
        
        # Fallback to default template
        for fallback in ['default', 'corporate', 'minimal']:
            if fallback in self.templates_cache:
                template_info = self.templates_cache[fallback]
                if template_info['template_path']:
                    return fallback, analysis
        
        # Last resort - return first available template
        for template_id, template_info in self.templates_cache.items():
            if template_info['template_path']:
                return template_id, analysis
        
        raise Exception("No valid templates found")
    
    def get_template_path(self, template_id: str) -> Optional[str]:
        """Get the file path for a specific template"""
        template_info = self.templates_cache.get(template_id)
        if template_info:
            return template_info['template_path']
        return None
    
    def get_template_colors(self, template_id: str) -> Dict[str, str]:
        """Get color scheme for a specific template"""
        template_info = self.templates_cache.get(template_id)
        if template_info:
            return template_info['metadata'].get('colors', {})
        return {}
    
    def refresh_templates(self):
        """Reload templates from the filesystem"""
        self.templates_cache.clear()
        self._load_templates()

# Example usage and testing
if __name__ == "__main__":
    template_manager = TemplateManager()
    
    print("Available templates:")
    for template in template_manager.list_templates():
        print(f"- {template['name']} ({template['id']}): {template['description']}")
    
    # Test content analysis
    test_documents = [
        {
            'type': 'pdf',
            'content': {
                'raw_text': 'Our SaaS platform shows strong MRR growth with 15% month-over-month increase. Churn rate decreased to 2.1% and customer acquisition cost improved.'
            }
        }
    ]
    
    recommended_template, analysis = template_manager.get_recommended_template(test_documents)
    print(f"\nRecommended template: {recommended_template}")
    print(f"Analysis: {analysis}")