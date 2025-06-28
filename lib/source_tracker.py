"""
Enhanced Source Attribution System

Centralized tracking system for document source attribution with
confidence scoring, cross-referencing, and clickable links.

Provides complete traceability from PowerPoint slides back to
original Excel cells, PDF pages, and document sections.
"""

import uuid
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from urllib.parse import quote

@dataclass
class SourceLocation:
    """Represents the location of data within a source document"""
    document_id: str
    page_or_sheet: str  # Sheet name for Excel, page number for PDF
    cell_or_section: str  # Cell reference (B15) or section name
    table_name: Optional[str] = None  # Table or region name
    line_number: Optional[int] = None  # Line number for text documents
    coordinates: Optional[Dict[str, Any]] = None  # Row/col for Excel, x/y for PDF
    extraction_method: str = "manual"  # How this data was extracted
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

@dataclass
class DataPoint:
    """Represents a single piece of data with its source attribution"""
    id: str
    value: Any
    data_type: str  # financial, percentage, text, date, etc.
    confidence: float  # 0.0 to 1.0
    source_location: SourceLocation
    context: Optional[str] = None  # Surrounding context
    formula: Optional[str] = None  # Excel formula if applicable
    calculated: bool = False  # True if derived from formula
    secondary_sources: List[SourceLocation] = None  # Cross-references
    timestamp: str = None  # When this was extracted
    
    def __post_init__(self):
        if self.secondary_sources is None:
            self.secondary_sources = []
        if self.timestamp is None:
            self.timestamp = str(uuid.uuid4())  # Placeholder for now
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result['source_location'] = self.source_location.to_dict()
        result['secondary_sources'] = [source.to_dict() for source in self.secondary_sources]
        return result

class SourceTracker:
    """Central system for tracking data source attribution"""
    
    def __init__(self):
        self.data_points: Dict[str, DataPoint] = {}
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.source_mappings: Dict[str, List[str]] = {}  # doc_id -> [data_point_ids]
    
    def register_document(self, file_path: str, doc_type: str, 
                         metadata: Optional[Dict[str, Any]] = None) -> str:
        """Register a document and return its unique ID"""
        doc_id = str(uuid.uuid4())
        
        self.documents[doc_id] = {
            'path': file_path,
            'type': doc_type,
            'metadata': metadata or {},
            'registered_at': datetime.now().isoformat()
        }
        
        self.source_mappings[doc_id] = []
        return doc_id
    
    def track_data_point(self, value: Any, document_id: str, 
                        location_details: Dict[str, Any], 
                        confidence: float = 0.8,
                        context: Optional[str] = None,
                        formula: Optional[str] = None) -> str:
        """Track a new data point with its source location"""
        
        data_point_id = str(uuid.uuid4())
        
        # Create source location
        source_location = SourceLocation(
            document_id=document_id,
            page_or_sheet=location_details.get('page_or_sheet', ''),
            cell_or_section=location_details.get('cell_or_section', ''),
            table_name=location_details.get('table_name'),
            line_number=location_details.get('line_number'),
            coordinates=location_details.get('coordinates'),
            extraction_method=location_details.get('extraction_method', 'automated')
        )
        
        # Classify data type
        data_type = self._classify_data_type(value)
        
        # Create data point
        data_point = DataPoint(
            id=data_point_id,
            value=value,
            data_type=data_type,
            confidence=confidence,
            source_location=source_location,
            context=context,
            formula=formula,
            calculated=bool(formula and formula.startswith('='))
        )
        
        # Store data point
        self.data_points[data_point_id] = data_point
        
        # Update source mapping
        if document_id in self.source_mappings:
            self.source_mappings[document_id].append(data_point_id)
        
        return data_point_id
    
    def _classify_data_type(self, value: Any) -> str:
        """Automatically classify the type of data"""
        if isinstance(value, (int, float)):
            if abs(value) > 1000000:
                return 'financial_large'
            elif abs(value) > 1000:
                return 'financial_medium'
            elif 0 <= value <= 1:
                return 'percentage_decimal'
            else:
                return 'numeric'
        
        elif isinstance(value, str):
            value_lower = value.lower().strip()
            
            # Check for currency
            if any(symbol in value for symbol in ['$', '€', '£', '¥']):
                return 'financial'
            
            # Check for percentage
            if '%' in value:
                return 'percentage'
            
            # Check for dates
            if any(word in value_lower for word in ['2020', '2021', '2022', '2023', '2024']):
                if len(value) == 4 and value.isdigit():
                    return 'year'
                else:
                    return 'date'
            
            # Default to text
            return 'text'
        
        else:
            return 'other'
    
    def get_source_hyperlink(self, data_point_id: str, link_text: Optional[str] = None) -> str:
        """Generate a clickable hyperlink to the source location"""
        if data_point_id not in self.data_points:
            return "#"
        
        data_point = self.data_points[data_point_id]
        source_location = data_point.source_location
        document_id = source_location.document_id
        
        if document_id not in self.documents:
            return "#"
        
        document = self.documents[document_id]
        file_path = document['path']
        doc_type = document['type']
        
        # Generate appropriate hyperlink based on document type
        if doc_type == 'excel':
            # Excel hyperlink: file:///path/to/file.xlsx#Sheet1!B15
            sheet = source_location.page_or_sheet
            cell = source_location.cell_or_section
            if sheet and cell:
                anchor = f"#{sheet}!{cell}"
                return f"file:///{quote(file_path)}{anchor}"
        elif doc_type == 'pdf':
            # PDF hyperlink: file:///path/to/file.pdf#page=5
            if source_location.page_or_sheet and source_location.page_or_sheet.replace('Page ', '').isdigit():
                page_num = source_location.page_or_sheet.replace('Page ', '')
                return f"file:///{quote(file_path)}#page={page_num}"
        
        # Fallback: just link to the file
        return f"file:///{quote(file_path)}"
    
    def get_source_attribution_text(self, data_point_id: str, 
                                   format_type: str = 'detailed') -> str:
        """Generate human-readable source attribution text"""
        if data_point_id not in self.data_points:
            return "Source: Unknown"
        
        data_point = self.data_points[data_point_id]
        source_location = data_point.source_location
        document_id = source_location.document_id
        
        if document_id not in self.documents:
            return "Source: Unknown document"
        
        document = self.documents[document_id]
        filename = document['path'].split('/')[-1]  # Get filename only
        
        if format_type == 'minimal':
            return f"{filename}"
        elif format_type == 'detailed':
            location_text = ""
            if source_location.page_or_sheet:
                location_text += f"{source_location.page_or_sheet}"
            if source_location.cell_or_section:
                if location_text:
                    location_text += f", {source_location.cell_or_section}"
                else:
                    location_text = source_location.cell_or_section
            
            confidence_text = f" ({data_point.confidence:.1%} confidence)" if data_point.confidence else ""
            return f"{filename}: {location_text}{confidence_text}"
        elif format_type == 'comprehensive':
            lines = [f"Source: {filename}"]
            if source_location.page_or_sheet:
                lines.append(f"Location: {source_location.page_or_sheet}")
            if source_location.cell_or_section:
                lines.append(f"Cell/Section: {source_location.cell_or_section}") 
            if data_point.confidence:
                lines.append(f"Confidence: {data_point.confidence:.1%}")
            if data_point.secondary_sources:
                lines.append(f"Cross-references: {len(data_point.secondary_sources)} additional sources")
            return " | ".join(lines)
        else:
            return f"Source: {filename}"
    
    def add_secondary_source(self, data_point_id: str, document_id: str, 
                           location_details: Dict[str, Any], 
                           context: Optional[str] = None):
        """Add a secondary source reference to an existing data point"""
        if data_point_id not in self.data_points:
            return
        
        secondary_location = SourceLocation(
            document_id=document_id,
            page_or_sheet=location_details.get('page_or_sheet', ''),
            cell_or_section=location_details.get('cell_or_section', ''),
            table_name=location_details.get('table_name'),
            line_number=location_details.get('line_number'),
            coordinates=location_details.get('coordinates'),
            extraction_method=location_details.get('extraction_method', 'cross_reference')
        )
        
        self.data_points[data_point_id].secondary_sources.append(secondary_location)
    
    def get_source_context(self, data_point_id: str) -> Dict[str, Any]:
        """Get comprehensive context information for a data point"""
        if data_point_id not in self.data_points:
            return {}
        
        data_point = self.data_points[data_point_id]
        source_location = data_point.source_location
        document_id = source_location.document_id
        
        document = self.documents.get(document_id, {})
        
        return {
            'data_point_id': data_point_id,
            'value': data_point.value,
            'data_type': data_point.data_type,
            'source_details': {
                'document': document.get('path', '').split('/')[-1],
                'location': source_location.cell_or_section,
                'page_or_sheet': source_location.page_or_sheet,
                'table': source_location.table_name
            },
            'quality_assessment': {
                'confidence': data_point.confidence,
                'quality_level': self._assess_extraction_quality(data_point.confidence),
                'calculated': data_point.calculated
            },
            'validation': {
                'extraction_method': source_location.extraction_method,
                'has_formula': bool(data_point.formula),
                'has_context': bool(data_point.context),
                'coordinates_available': bool(source_location.coordinates)
            },
            'cross_references': {
                'secondary_sources_count': len(data_point.secondary_sources),
                'has_cross_refs': len(data_point.secondary_sources) > 0
            }
        }
    
    def _assess_extraction_quality(self, confidence: float) -> str:
        """Assess the quality level based on confidence score"""
        if confidence >= 0.9:
            return 'high'
        elif confidence >= 0.7:
            return 'medium'
        else:
            return 'low'
    
    def validate_data_consistency(self, data_point_ids: List[str]) -> Dict[str, Any]:
        """Validate consistency across multiple data points"""
        if not data_point_ids:
            return {'consistent': True, 'message': 'No data points to validate'}
        
        valid_points = [dp_id for dp_id in data_point_ids if dp_id in self.data_points]
        
        if not valid_points:
            return {'consistent': False, 'message': 'No valid data points found'}
        
        # Analyze confidence distribution
        confidences = [self.data_points[dp_id].confidence for dp_id in valid_points]
        avg_confidence = sum(confidences) / len(confidences)
        min_confidence = min(confidences)
        
        # Check for consistent extraction methods
        extraction_methods = set()
        document_ids = set()
        
        for dp_id in valid_points:
            data_point = self.data_points[dp_id]
            extraction_methods.add(data_point.source_location.extraction_method)
            document_ids.add(data_point.source_location.document_id)
        
        # Determine overall consistency
        consistent = min_confidence >= 0.7 and avg_confidence >= 0.8
        
        return {
            'consistent': consistent,
            'confidence_distribution': {
                'average': avg_confidence,
                'minimum': min_confidence,
                'maximum': max(confidences)
            },
            'source_coverage': {
                'unique_documents': len(document_ids),
                'extraction_methods': list(extraction_methods),
                'total_data_points': len(valid_points)
            },
            'quality_assessment': self._assess_extraction_quality(avg_confidence)
        }
    
    def export_attribution_data(self) -> Dict[str, Any]:
        """Export all attribution data for persistence or transfer"""
        return {
            'data_points': {dp_id: dp.to_dict() for dp_id, dp in self.data_points.items()},
            'documents': self.documents,
            'source_mappings': self.source_mappings,
            'metadata': {
                'export_timestamp': datetime.now().isoformat(),
                'total_data_points': len(self.data_points),
                'total_documents': len(self.documents)
            }
        }
    
    def import_attribution_data(self, data: Dict[str, Any]):
        """Import attribution data from export"""
        # Clear existing data
        self.data_points.clear()
        self.documents.clear()
        self.source_mappings.clear()
        
        # Import documents and source mappings
        self.documents = data.get('documents', {})
        self.source_mappings = data.get('source_mappings', {})
        
        # Import data points
        data_points_data = data.get('data_points', {})
        for dp_id, dp_data in data_points_data.items():
            # Reconstruct SourceLocation
            source_loc_data = dp_data['source_location']
            source_location = SourceLocation(**source_loc_data)
            
            # Reconstruct secondary sources
            secondary_sources = []
            for sec_source_data in dp_data.get('secondary_sources', []):
                secondary_sources.append(SourceLocation(**sec_source_data))
            
            # Reconstruct DataPoint
            data_point = DataPoint(
                id=dp_data['id'],
                value=dp_data['value'],
                data_type=dp_data['data_type'],
                confidence=dp_data['confidence'],
                source_location=source_location,
                context=dp_data.get('context'),
                formula=dp_data.get('formula'),
                calculated=dp_data.get('calculated', False),
                secondary_sources=secondary_sources,
                timestamp=dp_data.get('timestamp')
            )
            
            self.data_points[dp_id] = data_point
