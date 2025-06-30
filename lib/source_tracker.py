"""
Enhanced Source Attribution System

Provides comprehensive tracking of data points back to their exact source locations
with support for clickable links, confidence scoring, and context preservation.
"""

import uuid
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from urllib.parse import quote
import os

@dataclass
class SourceLocation:
    """Represents a specific location within a source document"""
    document_id: str
    document_name: str
    document_type: str  # 'excel', 'pdf', 'word'
    
    # Location specifics
    page_or_sheet: Optional[str] = None
    cell_or_section: Optional[str] = None
    table_name: Optional[str] = None
    line_number: Optional[int] = None
    
    # Coordinates for precise positioning
    coordinates: Optional[Dict[str, Any]] = None
    
    # Context information
    surrounding_context: Optional[str] = None
    extraction_method: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

@dataclass 
class DataPoint:
    """Represents a single data point with its source attribution"""
    id: str
    value: Any
    data_type: str  # 'financial', 'percentage', 'text', 'date', etc.
    
    # Source information
    primary_source: SourceLocation
    secondary_sources: List[SourceLocation]
    
    # Quality metrics
    confidence: float  # 0.0 to 1.0
    extraction_quality: str  # 'high', 'medium', 'low'
    
    # Additional metadata
    formula: Optional[str] = None
    calculated: bool = False
    context_description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result['primary_source'] = self.primary_source.to_dict()
        result['secondary_sources'] = [src.to_dict() for src in self.secondary_sources]
        return result

class SourceTracker:
    """Central system for tracking data point sources with enhanced attribution"""
    
    def __init__(self):
        self.data_points: Dict[str, DataPoint] = {}
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.source_mappings: Dict[str, List[str]] = {}  # doc_id -> data_point_ids
        
    def register_document(self, document_path: str, document_type: str, 
                         metadata: Optional[Dict[str, Any]] = None) -> str:
        """Register a document and return its unique ID"""
        doc_id = str(uuid.uuid4())
        doc_name = os.path.basename(document_path)
        
        self.documents[doc_id] = {
            'id': doc_id,
            'name': doc_name,
            'path': document_path,
            'type': document_type,
            'metadata': metadata or {},
            'registered_at': str(uuid.uuid4())  # Placeholder for timestamp
        }
        
        self.source_mappings[doc_id] = []
        return doc_id
    
    def track_data_point(self, value: Any, document_id: str, 
                        location_details: Dict[str, Any],
                        confidence: float = 1.0,
                        context: Optional[str] = None,
                        formula: Optional[str] = None) -> str:
        """Track a data point with full source attribution"""
        
        data_point_id = str(uuid.uuid4())
        
        # Determine data type
        data_type = self._classify_data_type(value)
        
        # Create source location
        doc_info = self.documents.get(document_id, {})
        source_location = SourceLocation(
            document_id=document_id,
            document_name=doc_info.get('name', 'Unknown'),
            document_type=doc_info.get('type', 'unknown'),
            page_or_sheet=location_details.get('page_or_sheet'),
            cell_or_section=location_details.get('cell_or_section'),
            table_name=location_details.get('table_name'),
            line_number=location_details.get('line_number'),
            coordinates=location_details.get('coordinates'),
            surrounding_context=context,
            extraction_method=location_details.get('extraction_method')
        )
        
        # Determine extraction quality
        quality = self._assess_extraction_quality(confidence, value, formula)
        
        # Create data point
        data_point = DataPoint(
            id=data_point_id,
            value=value,
            data_type=data_type,
            primary_source=source_location,
            secondary_sources=[],
            confidence=confidence,
            extraction_quality=quality,
            formula=formula,
            calculated=bool(formula),
            context_description=context
        )
        
        # Store data point
        self.data_points[data_point_id] = data_point
        self.source_mappings[document_id].append(data_point_id)
        
        return data_point_id
    
    def add_secondary_source(self, data_point_id: str, document_id: str,
                           location_details: Dict[str, Any],
                           context: Optional[str] = None):
        """Add a secondary source for cross-referenced data"""
        if data_point_id not in self.data_points:
            return
        
        doc_info = self.documents.get(document_id, {})
        secondary_source = SourceLocation(
            document_id=document_id,
            document_name=doc_info.get('name', 'Unknown'),
            document_type=doc_info.get('type', 'unknown'),
            page_or_sheet=location_details.get('page_or_sheet'),
            cell_or_section=location_details.get('cell_or_section'),
            table_name=location_details.get('table_name'),
            coordinates=location_details.get('coordinates'),
            surrounding_context=context,
            extraction_method=location_details.get('extraction_method')
        )
        
        self.data_points[data_point_id].secondary_sources.append(secondary_source)
    
    def get_source_hyperlink(self, data_point_id: str, link_text: Optional[str] = None) -> str:
        """Generate clickable hyperlink for PowerPoint with source details"""
        if data_point_id not in self.data_points:
            return link_text or "No source"
        
        data_point = self.data_points[data_point_id]
        source = data_point.primary_source
        
        # Create descriptive link text if not provided
        if not link_text:
            if source.cell_or_section:
                link_text = f"{source.cell_or_section}"
            elif source.page_or_sheet:
                link_text = f"Page {source.page_or_sheet}"
            else:
                link_text = source.document_name
        
        # Create file URL for local file access
        if source.document_type == 'excel' and source.cell_or_section:
            # Excel cell reference
            file_url = f"file:///{quote(source.document_name)}#{source.page_or_sheet}!{source.cell_or_section}"
        elif source.document_type == 'pdf' and source.page_or_sheet:
            # PDF page reference
            file_url = f"file:///{quote(source.document_name)}#page={source.page_or_sheet}"
        else:
            # Generic file reference
            file_url = f"file:///{quote(source.document_name)}"
        
        return file_url
    
    def get_source_attribution_text(self, data_point_id: str, format_type: str = 'detailed') -> str:
        """Generate source attribution text for slides"""
        if data_point_id not in self.data_points:
            return "Source: Unknown"
        
        data_point = self.data_points[data_point_id]
        source = data_point.primary_source
        
        if format_type == 'minimal':
            return f"Source: {source.document_name}"
        elif format_type == 'detailed':
            parts = [f"Source: {source.document_name}"]
            
            if source.page_or_sheet:
                if source.document_type == 'excel':
                    parts.append(f"Sheet: {source.page_or_sheet}")
                else:
                    parts.append(f"Page: {source.page_or_sheet}")
            
            if source.cell_or_section:
                parts.append(f"Location: {source.cell_or_section}")
            
            if data_point.confidence < 1.0:
                parts.append(f"Confidence: {data_point.confidence:.1%}")
            
            return " | ".join(parts)
        else:  # comprehensive
            result = self.get_source_attribution_text(data_point_id, 'detailed')
            
            if data_point.secondary_sources:
                secondary_refs = []
                for sec_source in data_point.secondary_sources:
                    ref = sec_source.document_name
                    if sec_source.cell_or_section:
                        ref += f":{sec_source.cell_or_section}"
                    secondary_refs.append(ref)
                result += f" | Also in: {', '.join(secondary_refs)}"
            
            return result
    
    def get_source_context(self, data_point_id: str) -> Dict[str, Any]:
        """Get rich context information for source validation"""
        if data_point_id not in self.data_points:
            return {}
        
        data_point = self.data_points[data_point_id]
        source = data_point.primary_source
        
        context = {
            'data_point': data_point.to_dict(),
            'quality_assessment': {
                'confidence': data_point.confidence,
                'quality': data_point.extraction_quality,
                'calculated': data_point.calculated,
                'has_formula': bool(data_point.formula)
            },
            'source_details': {
                'document': source.document_name,
                'type': source.document_type,
                'location': source.cell_or_section or source.page_or_sheet,
                'context': source.surrounding_context
            },
            'validation': {
                'cross_referenced': len(data_point.secondary_sources) > 0,
                'extraction_method': source.extraction_method,
                'coordinates_available': bool(source.coordinates)
            }
        }
        
        return context
    
    def validate_data_consistency(self, data_point_ids: List[str]) -> Dict[str, Any]:
        """Validate consistency across multiple data points"""
        validation_results = {
            'consistent': True,
            'issues': [],
            'confidence_distribution': {},
            'source_coverage': {}
        }
        
        if not data_point_ids:
            return validation_results
        
        # Check confidence distribution
        confidences = []
        document_sources = set()
        quality_levels = []
        
        for dp_id in data_point_ids:
            if dp_id in self.data_points:
                dp = self.data_points[dp_id]
                confidences.append(dp.confidence)
                document_sources.add(dp.primary_source.document_id)
                quality_levels.append(dp.extraction_quality)
        
        # Analyze confidence distribution
        if confidences:
            avg_confidence = sum(confidences) / len(confidences)
            min_confidence = min(confidences)
            
            validation_results['confidence_distribution'] = {
                'average': avg_confidence,
                'minimum': min_confidence,
                'below_threshold': sum(1 for c in confidences if c < 0.8)
            }
            
            if min_confidence < 0.5:
                validation_results['issues'].append("Low confidence data points detected")
                validation_results['consistent'] = False
        
        # Analyze source coverage
        validation_results['source_coverage'] = {
            'unique_documents': len(document_sources),
            'quality_distribution': {q: quality_levels.count(q) for q in set(quality_levels)}
        }
        
        return validation_results
    
    def _classify_data_type(self, value: Any) -> str:
        """Classify the type of data based on value"""
        if isinstance(value, (int, float)):
            if str(value).endswith('%') or (isinstance(value, float) and 0 <= value <= 1):
                return 'percentage'
            elif value > 1000000:
                return 'financial_large'
            elif value > 1000:
                return 'financial_medium'
            else:
                return 'numeric'
        elif isinstance(value, str):
            if re.match(r'^\$.*', value):
                return 'financial'
            elif re.match(r'.*%$', value):
                return 'percentage'
            elif re.match(r'^\d{4}$', value):
                return 'year'
            elif re.match(r'^\d{1,2}[/-]\d{1,2}[/-]\d{4}$', value):
                return 'date'
            else:
                return 'text'
        else:
            return 'unknown'
    
    def _assess_extraction_quality(self, confidence: float, value: Any, formula: Optional[str]) -> str:
        """Assess extraction quality based on multiple factors"""
        if confidence >= 0.9:
            return 'high'
        elif confidence >= 0.7:
            return 'medium'
        else:
            return 'low'
    
    def export_attribution_data(self) -> Dict[str, Any]:
        """Export all attribution data for storage or transfer"""
        return {
            'data_points': {dp_id: dp.to_dict() for dp_id, dp in self.data_points.items()},
            'documents': self.documents,
            'source_mappings': self.source_mappings,
            'metadata': {
                'total_data_points': len(self.data_points),
                'total_documents': len(self.documents),
                'tracker_version': '1.0'
            }
        }
    
    def import_attribution_data(self, data: Dict[str, Any]):
        """Import attribution data from exported format"""
        # Clear existing data
        self.data_points.clear()
        self.documents.clear()
        self.source_mappings.clear()
        
        # Import documents
        self.documents = data.get('documents', {})
        self.source_mappings = data.get('source_mappings', {})
        
        # Import data points (reconstruct from dict)
        for dp_id, dp_data in data.get('data_points', {}).items():
            # Reconstruct SourceLocation objects
            primary_source_data = dp_data['primary_source']
            primary_source = SourceLocation(**primary_source_data)
            
            secondary_sources = []
            for sec_data in dp_data.get('secondary_sources', []):
                secondary_sources.append(SourceLocation(**sec_data))
            
            # Reconstruct DataPoint
            data_point = DataPoint(
                id=dp_data['id'],
                value=dp_data['value'],
                data_type=dp_data['data_type'],
                primary_source=primary_source,
                secondary_sources=secondary_sources,
                confidence=dp_data['confidence'],
                extraction_quality=dp_data['extraction_quality'],
                formula=dp_data.get('formula'),
                calculated=dp_data.get('calculated', False),
                context_description=dp_data.get('context_description')
            )
            
            self.data_points[dp_id] = data_point