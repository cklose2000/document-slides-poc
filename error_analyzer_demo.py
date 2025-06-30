#!/usr/bin/env python3
"""
Enhanced Error Analyzer for Demo File API Testing
Provides detailed error analysis with demo file context and suggested fixes
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class ErrorPattern:
    """Pattern for identifying specific error types"""
    pattern: str
    error_type: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    description: str
    suggested_fix: str
    demo_file_relevance: str

@dataclass
class ErrorAnalysis:
    """Complete analysis of an error"""
    error_type: str
    severity: str
    description: str
    suggested_fix: str
    demo_file_context: str
    code_location: Optional[str]
    related_files: List[str]
    fix_priority: int

class DemoFileErrorAnalyzer:
    """Analyzes API errors with demo file context"""
    
    def __init__(self):
        self.error_patterns = self._initialize_error_patterns()
        self.file_type_insights = {
            'pdf': 'PDF files require LLMWhisperer API key and may have extraction issues',
            'xlsx': 'Excel files use openpyxl and may have formula or formatting issues',
            'docx': 'Word files use python-docx and may have structure or encoding issues',
            'txt': 'Text files are not officially supported and may cause format errors'
        }
    
    def _initialize_error_patterns(self) -> List[ErrorPattern]:
        """Initialize known error patterns"""
        return [
            ErrorPattern(
                pattern=r"'RGBColor' object has no attribute '(red|green|blue)'",
                error_type="RGBColor_attribute_error",
                severity="high",
                description="Attempting to access color attributes incorrectly on RGBColor objects",
                suggested_fix="Use proper RGBColor construction or hex parsing instead of attribute access",
                demo_file_relevance="Affects all file types when brand colors are applied"
            ),
            ErrorPattern(
                pattern=r"object has no attribute 'create_thank_you_slide'",
                error_type="missing_method_error",
                severity="critical",
                description="Required method missing from BrandedSlideGenerator class",
                suggested_fix="Add the missing create_thank_you_slide method to BrandedSlideGenerator",
                demo_file_relevance="Affects all successful file processing when creating final slides"
            ),
            ErrorPattern(
                pattern=r"'body_size' KeyError",
                error_type="font_config_mismatch",
                severity="high",
                description="Font configuration structure mismatch between template and chart generator",
                suggested_fix="Fix font structure adaptation in _adapt_brand_config_for_charts method",
                demo_file_relevance="Affects files that generate charts (Excel files with numerical data)"
            ),
            ErrorPattern(
                pattern=r"ChartGenerator.*unexpected keyword argument '(colors|figsize)'",
                error_type="chart_parameter_error",
                severity="high",
                description="Chart generator called with unsupported parameters",
                suggested_fix="Remove unsupported parameters from chart generation calls",
                demo_file_relevance="Affects Excel files and any files with numerical data for charts"
            ),
            ErrorPattern(
                pattern=r"Font family.*not found",
                error_type="font_not_found",
                severity="medium",
                description="System font not available (typically Windows fonts on Linux)",
                suggested_fix="Replace Windows-specific fonts with cross-platform alternatives",
                demo_file_relevance="Affects all file types when brand templates use system-specific fonts"
            ),
            ErrorPattern(
                pattern=r"LLMWhisperer.*API.*not configured",
                error_type="api_key_missing",
                severity="medium",
                description="LLMWhisperer API key not configured for PDF processing",
                suggested_fix="Set LLMWHISPERER_API_KEY environment variable or handle gracefully",
                demo_file_relevance="Only affects PDF files (financial_report_q3.pdf, market_analysis.pdf)"
            ),
            ErrorPattern(
                pattern=r"No files uploaded",
                error_type="file_upload_error",
                severity="high",
                description="File upload failed or files not received by API",
                suggested_fix="Check file upload implementation and multipart form handling",
                demo_file_relevance="Could affect any demo files if upload mechanism fails"
            ),
            ErrorPattern(
                pattern=r"Template.*not found",
                error_type="template_missing",
                severity="high",
                description="Requested template does not exist or is not accessible",
                suggested_fix="Verify template exists and is properly registered in template system",
                demo_file_relevance="Affects all demo files when specific template is requested"
            ),
            ErrorPattern(
                pattern=r"(Memory|RAM).*error",
                error_type="memory_error",
                severity="critical",
                description="Insufficient memory for processing large files or multiple files",
                suggested_fix="Optimize memory usage or implement file size limits",
                demo_file_relevance="Likely affects large demo files or when processing all files together"
            ),
            ErrorPattern(
                pattern=r"Timeout|timed out",
                error_type="timeout_error",
                severity="medium",
                description="API request or file processing exceeded time limit",
                suggested_fix="Increase timeout values or optimize processing performance",
                demo_file_relevance="Affects large demo files or complex multi-file processing"
            )
        ]
    
    def analyze_error(self, error_message: str, error_traceback: str, 
                     files_used: List[str], template_used: str = None) -> ErrorAnalysis:
        """Analyze an error with demo file context"""
        
        # Find matching error pattern
        error_pattern = self._match_error_pattern(error_message, error_traceback)
        
        # Analyze demo file context
        demo_context = self._analyze_demo_file_context(files_used, error_message)
        
        # Extract code location from traceback
        code_location = self._extract_code_location(error_traceback)
        
        # Determine fix priority
        fix_priority = self._calculate_fix_priority(error_pattern, files_used, template_used)
        
        return ErrorAnalysis(
            error_type=error_pattern.error_type if error_pattern else "unknown_error",
            severity=error_pattern.severity if error_pattern else "medium",
            description=error_pattern.description if error_pattern else error_message,
            suggested_fix=error_pattern.suggested_fix if error_pattern else "Review error details and traceback",
            demo_file_context=demo_context,
            code_location=code_location,
            related_files=files_used,
            fix_priority=fix_priority
        )
    
    def _match_error_pattern(self, error_message: str, error_traceback: str) -> Optional[ErrorPattern]:
        """Find matching error pattern"""
        full_error = f"{error_message}\n{error_traceback or ''}"
        
        for pattern in self.error_patterns:
            if re.search(pattern.pattern, full_error, re.IGNORECASE):
                return pattern
        
        return None
    
    def _analyze_demo_file_context(self, files_used: List[str], error_message: str) -> str:
        """Analyze demo file context for the error"""
        if not files_used:
            return "No demo files involved in this error"
        
        context_parts = []
        
        # Analyze file types
        file_types = defaultdict(list)
        for file in files_used:
            ext = file.split('.')[-1].lower()
            file_types[ext].append(file)
        
        context_parts.append(f"Demo files involved: {', '.join(files_used)}")
        
        # Add file type insights
        for file_type, files in file_types.items():
            if file_type in self.file_type_insights:
                context_parts.append(f"{file_type.upper()} files ({', '.join(files)}): {self.file_type_insights[file_type]}")
        
        # Special analysis for specific demo files
        demo_file_insights = {
            'financial_report_q3.pdf': 'Contains complex financial tables and charts',
            'market_analysis.pdf': 'Contains market data and may have extraction challenges',
            'budget_model.xlsx': 'Contains financial formulas and calculations',
            'financial_projections.xlsx': 'Contains future projections and complex data',
            'executive_summary.docx': 'Contains structured business text and headers',
            'product_overview.docx': 'Contains product information and descriptions'
        }
        
        for file in files_used:
            if file in demo_file_insights:
                context_parts.append(f"{file}: {demo_file_insights[file]}")
        
        # Multi-file analysis
        if len(files_used) > 1:
            context_parts.append(f"Multi-file processing with {len(files_used)} files may increase complexity and resource usage")
        
        return ". ".join(context_parts)
    
    def _extract_code_location(self, error_traceback: str) -> Optional[str]:
        """Extract file and line number from traceback"""
        if not error_traceback:
            return None
        
        # Look for file paths and line numbers in traceback
        pattern = r'File "([^"]+)", line (\d+)'
        matches = re.findall(pattern, error_traceback)
        
        if matches:
            # Return the last (most specific) match
            file_path, line_num = matches[-1]
            # Clean up the path to show just the relevant part
            if 'document-slides-poc' in file_path:
                file_path = file_path.split('document-slides-poc')[-1].lstrip('/')
            return f"{file_path}:{line_num}"
        
        return None
    
    def _calculate_fix_priority(self, error_pattern: Optional[ErrorPattern], 
                               files_used: List[str], template_used: str) -> int:
        """Calculate fix priority (1=highest, 5=lowest)"""
        if not error_pattern:
            return 3  # Medium priority for unknown errors
        
        # Base priority from severity
        severity_priority = {
            'critical': 1,
            'high': 2,
            'medium': 3,
            'low': 4
        }
        
        priority = severity_priority.get(error_pattern.severity, 3)
        
        # Adjust based on demo file context
        if files_used:
            # Errors affecting PDF files might be lower priority if API key is missing
            if any(f.endswith('.pdf') for f in files_used) and 'api.*not configured' in error_pattern.pattern.lower():
                priority += 1
            
            # Errors affecting multiple files are higher priority
            if len(files_used) > 1:
                priority = max(1, priority - 1)
            
            # Errors affecting Excel files with charts are higher priority for demos
            if any(f.endswith('.xlsx') for f in files_used) and 'chart' in error_pattern.error_type.lower():
                priority = max(1, priority - 1)
        
        return min(5, max(1, priority))
    
    def analyze_batch_errors(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze multiple test results and identify patterns"""
        error_analyses = []
        
        for result in test_results:
            if not result.get('success', True):
                analysis = self.analyze_error(
                    result.get('error_message', ''),
                    result.get('error_traceback', ''),
                    result.get('files_used', []),
                    result.get('template_used')
                )
                error_analyses.append(analysis)
        
        # Group errors by type
        errors_by_type = defaultdict(list)
        for analysis in error_analyses:
            errors_by_type[analysis.error_type].append(analysis)
        
        # Calculate statistics
        total_errors = len(error_analyses)
        error_distribution = {error_type: len(analyses) for error_type, analyses in errors_by_type.items()}
        
        # Find most critical errors
        critical_errors = [a for a in error_analyses if a.fix_priority <= 2]
        critical_errors.sort(key=lambda x: x.fix_priority)
        
        # Identify file-specific patterns
        file_error_patterns = defaultdict(list)
        for analysis in error_analyses:
            for file in analysis.related_files:
                file_error_patterns[file].append(analysis.error_type)
        
        return {
            'total_errors': total_errors,
            'error_distribution': error_distribution,
            'critical_errors': [self._analysis_to_dict(a) for a in critical_errors[:5]],
            'file_error_patterns': dict(file_error_patterns),
            'recommendations': self._generate_recommendations(errors_by_type),
            'fix_order': self._suggest_fix_order(critical_errors)
        }
    
    def _analysis_to_dict(self, analysis: ErrorAnalysis) -> Dict[str, Any]:
        """Convert ErrorAnalysis to dictionary"""
        return {
            'error_type': analysis.error_type,
            'severity': analysis.severity,
            'description': analysis.description,
            'suggested_fix': analysis.suggested_fix,
            'demo_file_context': analysis.demo_file_context,
            'code_location': analysis.code_location,
            'related_files': analysis.related_files,
            'fix_priority': analysis.fix_priority
        }
    
    def _generate_recommendations(self, errors_by_type: Dict[str, List[ErrorAnalysis]]) -> List[str]:
        """Generate overall recommendations based on error patterns"""
        recommendations = []
        
        if 'RGBColor_attribute_error' in errors_by_type:
            recommendations.append("🎨 Fix RGBColor attribute access throughout the codebase")
        
        if 'missing_method_error' in errors_by_type:
            recommendations.append("🔧 Add missing methods to BrandedSlideGenerator class")
        
        if 'font_config_mismatch' in errors_by_type:
            recommendations.append("📝 Standardize font configuration structure between components")
        
        if 'api_key_missing' in errors_by_type:
            recommendations.append("🔑 Either configure LLMWhisperer API key or improve graceful handling of PDF files")
        
        if 'chart_parameter_error' in errors_by_type:
            recommendations.append("📊 Review and fix chart generation parameter compatibility")
        
        # Add general recommendations
        error_count = sum(len(analyses) for analyses in errors_by_type.values())
        if error_count > 10:
            recommendations.append("🧪 Consider adding unit tests for core components to catch regressions")
        
        return recommendations
    
    def _suggest_fix_order(self, critical_errors: List[ErrorAnalysis]) -> List[str]:
        """Suggest order for fixing errors"""
        if not critical_errors:
            return ["No critical errors found"]
        
        fix_order = []
        seen_types = set()
        
        for error in critical_errors:
            if error.error_type not in seen_types:
                fix_order.append(f"Priority {error.fix_priority}: {error.error_type} - {error.suggested_fix}")
                seen_types.add(error.error_type)
        
        return fix_order

def main():
    """Example usage of the error analyzer"""
    analyzer = DemoFileErrorAnalyzer()
    
    # Example error analysis
    example_error = "AttributeError: 'RGBColor' object has no attribute 'red'"
    example_traceback = '''Traceback (most recent call last):
  File "/mnt/c/Users/cklos/document-slides-poc/lib/slide_generator_branded.py", line 1322, in create_thank_you_slide
    max(0, primary_rgb.red - 40),
AttributeError: 'RGBColor' object has no attribute 'red'
'''
    
    analysis = analyzer.analyze_error(
        example_error,
        example_traceback,
        ['budget_model.xlsx', 'executive_summary.docx'],
        'simple_template'
    )
    
    print("Example Error Analysis:")
    print(f"Error Type: {analysis.error_type}")
    print(f"Severity: {analysis.severity}")
    print(f"Description: {analysis.description}")
    print(f"Fix Priority: {analysis.fix_priority}")
    print(f"Suggested Fix: {analysis.suggested_fix}")
    print(f"Demo File Context: {analysis.demo_file_context}")
    print(f"Code Location: {analysis.code_location}")

if __name__ == "__main__":
    main()