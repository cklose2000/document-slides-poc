"""
Conflict Resolution Engine

Detects and resolves contradictions between different data sources,
providing intelligent resolution strategies and maintaining audit trails.
"""

from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re
import statistics
from collections import defaultdict


class ConflictType(Enum):
    """Types of conflicts that can occur between data sources"""
    NUMERIC_MISMATCH = "numeric_mismatch"
    DATE_MISMATCH = "date_mismatch"
    CATEGORICAL_MISMATCH = "categorical_mismatch"
    BOOLEAN_MISMATCH = "boolean_mismatch"
    MISSING_DATA = "missing_data"
    UNIT_MISMATCH = "unit_mismatch"
    RANGE_VIOLATION = "range_violation"
    SEMANTIC_CONFLICT = "semantic_conflict"


class ResolutionStrategy(Enum):
    """Strategies for resolving conflicts"""
    MOST_RECENT = "most_recent"
    HIGHEST_CONFIDENCE = "highest_confidence"
    MAJORITY_VOTE = "majority_vote"
    AVERAGE = "average"
    MEDIAN = "median"
    SOURCE_PRIORITY = "source_priority"
    MANUAL_REVIEW = "manual_review"
    WEIGHTED_AVERAGE = "weighted_average"


@dataclass
class DataPoint:
    """Represents a single data point from a source"""
    value: Any
    source_id: str
    source_type: str
    extraction_date: datetime
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    context: Optional[str] = None
    
    def __str__(self):
        return f"{self.value} (from {self.source_id}, confidence: {self.confidence:.2f})"


@dataclass
class Conflict:
    """Represents a detected conflict between data points"""
    conflict_id: str
    conflict_type: ConflictType
    field_name: str
    data_points: List[DataPoint]
    severity: float  # 0.0 to 1.0
    description: str
    detected_at: datetime = field(default_factory=datetime.now)
    
    def __str__(self):
        values = [str(dp.value) for dp in self.data_points]
        return f"Conflict in {self.field_name}: {' vs '.join(values)}"


@dataclass
class Resolution:
    """Represents a conflict resolution"""
    conflict_id: str
    strategy: ResolutionStrategy
    resolved_value: Any
    confidence: float
    justification: str
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)
    requires_review: bool = False
    
    def __str__(self):
        return f"Resolved to: {self.resolved_value} using {self.strategy.value}"


class ConflictDetector:
    """Detects conflicts between data points"""
    
    def __init__(self):
        self.numeric_tolerance = 0.01  # 1% tolerance for numeric comparisons
        self.date_tolerance_days = 1  # 1 day tolerance for date comparisons
        
    def detect_conflicts(self, field_data: Dict[str, List[DataPoint]]) -> List[Conflict]:
        """
        Detect conflicts in field data
        
        Args:
            field_data: Dictionary mapping field names to lists of data points
            
        Returns:
            List of detected conflicts
        """
        conflicts = []
        
        for field_name, data_points in field_data.items():
            if len(data_points) < 2:
                continue
                
            # Detect conflicts based on data type
            conflict = self._detect_field_conflict(field_name, data_points)
            if conflict:
                conflicts.append(conflict)
        
        return conflicts
    
    def _detect_field_conflict(self, field_name: str, data_points: List[DataPoint]) -> Optional[Conflict]:
        """Detect conflict in a single field"""
        if not data_points:
            return None
        
        # Get unique values
        values = [dp.value for dp in data_points]
        
        # Skip if all values are None or empty
        non_empty_values = [v for v in values if v is not None and v != '']
        if not non_empty_values:
            return None
        
        # Determine data type and check for conflicts
        sample_value = non_empty_values[0]
        
        if isinstance(sample_value, (int, float)):
            return self._detect_numeric_conflict(field_name, data_points)
        elif isinstance(sample_value, str):
            if self._is_date_string(sample_value):
                return self._detect_date_conflict(field_name, data_points)
            else:
                return self._detect_categorical_conflict(field_name, data_points)
        elif isinstance(sample_value, bool):
            return self._detect_boolean_conflict(field_name, data_points)
        else:
            return self._detect_categorical_conflict(field_name, data_points)
    
    def _detect_numeric_conflict(self, field_name: str, data_points: List[DataPoint]) -> Optional[Conflict]:
        """Detect conflicts in numeric data"""
        values = []
        valid_points = []
        
        for dp in data_points:
            if dp.value is not None:
                # Try to convert to float
                try:
                    numeric_value = self._extract_numeric_value(dp.value)
                    if numeric_value is not None:
                        values.append(numeric_value)
                        valid_points.append(dp)
                except:
                    pass
        
        if len(values) < 2:
            return None
        
        # Check for significant differences
        mean_val = statistics.mean(values)
        max_diff = max(abs(v - mean_val) for v in values)
        relative_diff = max_diff / abs(mean_val) if mean_val != 0 else float('inf')
        
        if relative_diff > self.numeric_tolerance:
            severity = min(relative_diff / 0.5, 1.0)  # 50% difference = max severity
            
            return Conflict(
                conflict_id=self._generate_conflict_id(field_name),
                conflict_type=ConflictType.NUMERIC_MISMATCH,
                field_name=field_name,
                data_points=valid_points,
                severity=severity,
                description=f"Numeric values differ by {relative_diff:.1%}"
            )
        
        return None
    
    def _detect_date_conflict(self, field_name: str, data_points: List[DataPoint]) -> Optional[Conflict]:
        """Detect conflicts in date data"""
        # Simple implementation - would need proper date parsing
        unique_values = set(dp.value for dp in data_points if dp.value)
        
        if len(unique_values) > 1:
            return Conflict(
                conflict_id=self._generate_conflict_id(field_name),
                conflict_type=ConflictType.DATE_MISMATCH,
                field_name=field_name,
                data_points=data_points,
                severity=0.7,
                description=f"Different dates found: {', '.join(str(v) for v in unique_values)}"
            )
        
        return None
    
    def _detect_categorical_conflict(self, field_name: str, data_points: List[DataPoint]) -> Optional[Conflict]:
        """Detect conflicts in categorical data"""
        unique_values = set(dp.value for dp in data_points if dp.value is not None)
        
        if len(unique_values) > 1:
            # Check if values are semantically similar
            if self._are_values_similar(list(unique_values)):
                conflict_type = ConflictType.SEMANTIC_CONFLICT
                severity = 0.3
            else:
                conflict_type = ConflictType.CATEGORICAL_MISMATCH
                severity = 0.8
            
            return Conflict(
                conflict_id=self._generate_conflict_id(field_name),
                conflict_type=conflict_type,
                field_name=field_name,
                data_points=data_points,
                severity=severity,
                description=f"Different values: {', '.join(str(v) for v in unique_values)}"
            )
        
        return None
    
    def _detect_boolean_conflict(self, field_name: str, data_points: List[DataPoint]) -> Optional[Conflict]:
        """Detect conflicts in boolean data"""
        unique_values = set(dp.value for dp in data_points if dp.value is not None)
        
        if len(unique_values) > 1:
            return Conflict(
                conflict_id=self._generate_conflict_id(field_name),
                conflict_type=ConflictType.BOOLEAN_MISMATCH,
                field_name=field_name,
                data_points=data_points,
                severity=1.0,  # Boolean conflicts are always high severity
                description="Conflicting boolean values"
            )
        
        return None
    
    def _extract_numeric_value(self, value: Any) -> Optional[float]:
        """Extract numeric value from various formats"""
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # Remove currency symbols and units
            cleaned = re.sub(r'[$,]', '', value)
            
            # Extract number with multiplier (e.g., 10M, 2.5B)
            match = re.match(r'([\d.]+)\s*([MBK])?', cleaned)
            if match:
                num = float(match.group(1))
                multiplier = match.group(2)
                
                if multiplier == 'K':
                    return num * 1000
                elif multiplier == 'M':
                    return num * 1000000
                elif multiplier == 'B':
                    return num * 1000000000
                else:
                    return num
        
        return None
    
    def _is_date_string(self, value: str) -> bool:
        """Check if string appears to be a date"""
        date_patterns = [
            r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',
            r'\d{4}[-/]\d{1,2}[-/]\d{1,2}',
            r'(?:Q[1-4]|FY)\s*\d{4}',
            r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}'
        ]
        
        return any(re.search(pattern, value, re.IGNORECASE) for pattern in date_patterns)
    
    def _are_values_similar(self, values: List[Any]) -> bool:
        """Check if values are semantically similar"""
        # Simple implementation - check for common variations
        str_values = [str(v).lower().strip() for v in values]
        
        # Check for yes/no variations
        yes_variants = {'yes', 'y', 'true', '1', 'enabled', 'on'}
        no_variants = {'no', 'n', 'false', '0', 'disabled', 'off'}
        
        if all(v in yes_variants for v in str_values) or all(v in no_variants for v in str_values):
            return True
        
        # Check for case/whitespace differences
        if len(set(str_values)) == 1:
            return True
        
        return False
    
    def _generate_conflict_id(self, field_name: str) -> str:
        """Generate unique conflict ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        return f"conflict_{field_name}_{timestamp}"


class ConflictResolver:
    """Resolves detected conflicts using various strategies"""
    
    def __init__(self):
        self.default_strategies = {
            ConflictType.NUMERIC_MISMATCH: ResolutionStrategy.WEIGHTED_AVERAGE,
            ConflictType.DATE_MISMATCH: ResolutionStrategy.MOST_RECENT,
            ConflictType.CATEGORICAL_MISMATCH: ResolutionStrategy.HIGHEST_CONFIDENCE,
            ConflictType.BOOLEAN_MISMATCH: ResolutionStrategy.MAJORITY_VOTE,
            ConflictType.SEMANTIC_CONFLICT: ResolutionStrategy.HIGHEST_CONFIDENCE,
        }
        
        self.source_priorities = {}  # Can be configured for source preference
    
    def resolve_conflict(self, conflict: Conflict, 
                        strategy: Optional[ResolutionStrategy] = None,
                        config: Optional[Dict[str, Any]] = None) -> Resolution:
        """
        Resolve a conflict using specified or default strategy
        
        Args:
            conflict: The conflict to resolve
            strategy: Resolution strategy to use (uses default if None)
            config: Additional configuration for resolution
            
        Returns:
            Resolution object
        """
        if strategy is None:
            strategy = self.default_strategies.get(conflict.conflict_type, 
                                                  ResolutionStrategy.MANUAL_REVIEW)
        
        config = config or {}
        
        # Apply resolution strategy
        if strategy == ResolutionStrategy.MOST_RECENT:
            return self._resolve_most_recent(conflict)
        elif strategy == ResolutionStrategy.HIGHEST_CONFIDENCE:
            return self._resolve_highest_confidence(conflict)
        elif strategy == ResolutionStrategy.MAJORITY_VOTE:
            return self._resolve_majority_vote(conflict)
        elif strategy == ResolutionStrategy.AVERAGE:
            return self._resolve_average(conflict)
        elif strategy == ResolutionStrategy.MEDIAN:
            return self._resolve_median(conflict)
        elif strategy == ResolutionStrategy.WEIGHTED_AVERAGE:
            return self._resolve_weighted_average(conflict)
        elif strategy == ResolutionStrategy.SOURCE_PRIORITY:
            return self._resolve_source_priority(conflict, config)
        else:
            return self._manual_review_required(conflict)
    
    def _resolve_most_recent(self, conflict: Conflict) -> Resolution:
        """Resolve by selecting most recent data point"""
        most_recent = max(conflict.data_points, key=lambda dp: dp.extraction_date)
        
        return Resolution(
            conflict_id=conflict.conflict_id,
            strategy=ResolutionStrategy.MOST_RECENT,
            resolved_value=most_recent.value,
            confidence=most_recent.confidence * 0.9,  # Slight reduction for uncertainty
            justification=f"Selected most recent value from {most_recent.source_id} "
                         f"(extracted {most_recent.extraction_date.strftime('%Y-%m-%d')})",
            audit_trail=[{
                'action': 'selected_most_recent',
                'source': most_recent.source_id,
                'timestamp': datetime.now().isoformat()
            }]
        )
    
    def _resolve_highest_confidence(self, conflict: Conflict) -> Resolution:
        """Resolve by selecting highest confidence data point"""
        highest_conf = max(conflict.data_points, key=lambda dp: dp.confidence)
        
        return Resolution(
            conflict_id=conflict.conflict_id,
            strategy=ResolutionStrategy.HIGHEST_CONFIDENCE,
            resolved_value=highest_conf.value,
            confidence=highest_conf.confidence,
            justification=f"Selected highest confidence value from {highest_conf.source_id} "
                         f"(confidence: {highest_conf.confidence:.2f})",
            audit_trail=[{
                'action': 'selected_highest_confidence',
                'source': highest_conf.source_id,
                'confidence': highest_conf.confidence,
                'timestamp': datetime.now().isoformat()
            }]
        )
    
    def _resolve_majority_vote(self, conflict: Conflict) -> Resolution:
        """Resolve by majority vote"""
        value_counts = defaultdict(list)
        
        for dp in conflict.data_points:
            # Normalize values for comparison
            normalized = self._normalize_value(dp.value)
            value_counts[normalized].append(dp)
        
        # Find majority value
        majority_value = max(value_counts.keys(), key=lambda v: len(value_counts[v]))
        majority_points = value_counts[majority_value]
        
        # Calculate confidence based on vote distribution
        vote_ratio = len(majority_points) / len(conflict.data_points)
        avg_confidence = statistics.mean(dp.confidence for dp in majority_points)
        final_confidence = avg_confidence * vote_ratio
        
        return Resolution(
            conflict_id=conflict.conflict_id,
            strategy=ResolutionStrategy.MAJORITY_VOTE,
            resolved_value=majority_points[0].value,  # Use original value format
            confidence=final_confidence,
            justification=f"Majority vote: {len(majority_points)}/{len(conflict.data_points)} "
                         f"sources agree on this value",
            audit_trail=[{
                'action': 'majority_vote',
                'vote_distribution': {str(k): len(v) for k, v in value_counts.items()},
                'timestamp': datetime.now().isoformat()
            }]
        )
    
    def _resolve_average(self, conflict: Conflict) -> Resolution:
        """Resolve numeric conflicts by averaging"""
        numeric_values = []
        
        for dp in conflict.data_points:
            num_val = self._extract_numeric(dp.value)
            if num_val is not None:
                numeric_values.append(num_val)
        
        if not numeric_values:
            return self._manual_review_required(conflict)
        
        avg_value = statistics.mean(numeric_values)
        
        return Resolution(
            conflict_id=conflict.conflict_id,
            strategy=ResolutionStrategy.AVERAGE,
            resolved_value=avg_value,
            confidence=0.7,  # Moderate confidence for averages
            justification=f"Averaged {len(numeric_values)} numeric values",
            audit_trail=[{
                'action': 'calculated_average',
                'values': numeric_values,
                'result': avg_value,
                'timestamp': datetime.now().isoformat()
            }]
        )
    
    def _resolve_median(self, conflict: Conflict) -> Resolution:
        """Resolve numeric conflicts by taking median"""
        numeric_values = []
        
        for dp in conflict.data_points:
            num_val = self._extract_numeric(dp.value)
            if num_val is not None:
                numeric_values.append(num_val)
        
        if not numeric_values:
            return self._manual_review_required(conflict)
        
        median_value = statistics.median(numeric_values)
        
        return Resolution(
            conflict_id=conflict.conflict_id,
            strategy=ResolutionStrategy.MEDIAN,
            resolved_value=median_value,
            confidence=0.75,  # Slightly higher confidence than average
            justification=f"Median of {len(numeric_values)} numeric values",
            audit_trail=[{
                'action': 'calculated_median',
                'values': sorted(numeric_values),
                'result': median_value,
                'timestamp': datetime.now().isoformat()
            }]
        )
    
    def _resolve_weighted_average(self, conflict: Conflict) -> Resolution:
        """Resolve numeric conflicts by confidence-weighted average"""
        weighted_sum = 0
        weight_sum = 0
        values_used = []
        
        for dp in conflict.data_points:
            num_val = self._extract_numeric(dp.value)
            if num_val is not None:
                weight = dp.confidence
                weighted_sum += num_val * weight
                weight_sum += weight
                values_used.append({'value': num_val, 'weight': weight, 'source': dp.source_id})
        
        if weight_sum == 0:
            return self._manual_review_required(conflict)
        
        weighted_avg = weighted_sum / weight_sum
        
        return Resolution(
            conflict_id=conflict.conflict_id,
            strategy=ResolutionStrategy.WEIGHTED_AVERAGE,
            resolved_value=weighted_avg,
            confidence=weight_sum / len(values_used),  # Average of weights used
            justification=f"Confidence-weighted average of {len(values_used)} values",
            audit_trail=[{
                'action': 'calculated_weighted_average',
                'values_and_weights': values_used,
                'result': weighted_avg,
                'timestamp': datetime.now().isoformat()
            }]
        )
    
    def _resolve_source_priority(self, conflict: Conflict, config: Dict[str, Any]) -> Resolution:
        """Resolve by source priority list"""
        priority_list = config.get('source_priorities', self.source_priorities)
        
        if not priority_list:
            return self._resolve_highest_confidence(conflict)
        
        # Find highest priority source
        best_point = None
        best_priority = float('inf')
        
        for dp in conflict.data_points:
            priority = priority_list.get(dp.source_type, float('inf'))
            if priority < best_priority:
                best_priority = priority
                best_point = dp
        
        if best_point is None:
            return self._resolve_highest_confidence(conflict)
        
        return Resolution(
            conflict_id=conflict.conflict_id,
            strategy=ResolutionStrategy.SOURCE_PRIORITY,
            resolved_value=best_point.value,
            confidence=best_point.confidence,
            justification=f"Selected value from highest priority source: {best_point.source_type}",
            audit_trail=[{
                'action': 'source_priority_selection',
                'source': best_point.source_id,
                'source_type': best_point.source_type,
                'timestamp': datetime.now().isoformat()
            }]
        )
    
    def _manual_review_required(self, conflict: Conflict) -> Resolution:
        """Flag conflict for manual review"""
        return Resolution(
            conflict_id=conflict.conflict_id,
            strategy=ResolutionStrategy.MANUAL_REVIEW,
            resolved_value=None,
            confidence=0.0,
            justification="Conflict requires manual review",
            requires_review=True,
            audit_trail=[{
                'action': 'flagged_for_review',
                'reason': 'No automatic resolution available',
                'timestamp': datetime.now().isoformat()
            }]
        )
    
    def _normalize_value(self, value: Any) -> Any:
        """Normalize value for comparison"""
        if value is None:
            return None
        
        if isinstance(value, str):
            # Normalize strings
            normalized = value.lower().strip()
            
            # Handle boolean-like strings
            if normalized in {'yes', 'y', 'true', '1', 'enabled', 'on'}:
                return True
            elif normalized in {'no', 'n', 'false', '0', 'disabled', 'off'}:
                return False
            
            return normalized
        
        return value
    
    def _extract_numeric(self, value: Any) -> Optional[float]:
        """Extract numeric value for calculations"""
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # Try to extract number
            cleaned = re.sub(r'[^\d.-]', '', value)
            try:
                return float(cleaned)
            except:
                pass
        
        return None


class ConflictResolutionEngine:
    """Main engine for conflict detection and resolution"""
    
    def __init__(self):
        self.detector = ConflictDetector()
        self.resolver = ConflictResolver()
        self.resolution_history = []
    
    def process_data_sources(self, data_sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process multiple data sources and resolve conflicts
        
        Args:
            data_sources: List of data source dictionaries
            
        Returns:
            Dictionary with resolved values and conflict report
        """
        # Group data points by field
        field_data = self._group_by_field(data_sources)
        
        # Detect conflicts
        conflicts = self.detector.detect_conflicts(field_data)
        
        # Resolve conflicts
        resolutions = []
        resolved_data = {}
        
        for conflict in conflicts:
            resolution = self.resolver.resolve_conflict(conflict)
            resolutions.append(resolution)
            
            if not resolution.requires_review:
                resolved_data[conflict.field_name] = {
                    'value': resolution.resolved_value,
                    'confidence': resolution.confidence,
                    'resolution_strategy': resolution.strategy.value
                }
        
        # Add non-conflicting fields
        for field_name, data_points in field_data.items():
            if field_name not in resolved_data and data_points:
                # Use highest confidence value for non-conflicting fields
                best_point = max(data_points, key=lambda dp: dp.confidence)
                resolved_data[field_name] = {
                    'value': best_point.value,
                    'confidence': best_point.confidence,
                    'resolution_strategy': 'no_conflict'
                }
        
        # Store resolution history
        self.resolution_history.extend(resolutions)
        
        return {
            'resolved_data': resolved_data,
            'conflicts': [self._conflict_to_dict(c) for c in conflicts],
            'resolutions': [self._resolution_to_dict(r) for r in resolutions],
            'requires_review': [r for r in resolutions if r.requires_review],
            'summary': {
                'total_fields': len(field_data),
                'conflicts_detected': len(conflicts),
                'conflicts_resolved': len([r for r in resolutions if not r.requires_review]),
                'manual_review_required': len([r for r in resolutions if r.requires_review])
            }
        }
    
    def _group_by_field(self, data_sources: List[Dict[str, Any]]) -> Dict[str, List[DataPoint]]:
        """Group data points by field name"""
        field_data = defaultdict(list)
        
        for source in data_sources:
            source_id = source.get('source_id', 'unknown')
            source_type = source.get('source_type', 'unknown')
            extraction_date = source.get('extraction_date', datetime.now())
            
            if isinstance(extraction_date, str):
                extraction_date = datetime.fromisoformat(extraction_date)
            
            for field_name, value in source.get('data', {}).items():
                data_point = DataPoint(
                    value=value,
                    source_id=source_id,
                    source_type=source_type,
                    extraction_date=extraction_date,
                    confidence=source.get('confidence', 0.5),
                    metadata=source.get('metadata', {})
                )
                field_data[field_name].append(data_point)
        
        return dict(field_data)
    
    def _conflict_to_dict(self, conflict: Conflict) -> Dict[str, Any]:
        """Convert conflict to dictionary"""
        return {
            'conflict_id': conflict.conflict_id,
            'type': conflict.conflict_type.value,
            'field': conflict.field_name,
            'severity': conflict.severity,
            'description': conflict.description,
            'values': [{'value': dp.value, 'source': dp.source_id} for dp in conflict.data_points]
        }
    
    def _resolution_to_dict(self, resolution: Resolution) -> Dict[str, Any]:
        """Convert resolution to dictionary"""
        return {
            'conflict_id': resolution.conflict_id,
            'strategy': resolution.strategy.value,
            'resolved_value': resolution.resolved_value,
            'confidence': resolution.confidence,
            'justification': resolution.justification,
            'requires_review': resolution.requires_review
        }