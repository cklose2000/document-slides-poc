"""
Insight Generator Module

This module provides theme extraction and trend analysis capabilities for synthesized documents.
It identifies patterns, detects anomalies, and generates actionable insights from document data.
"""

from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import numpy as np
from scipy import stats
from sklearn.cluster import DBSCAN
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging

from .synthesis_engine import SynthesisEngine, DocumentNode

logger = logging.getLogger(__name__)


class InsightType(Enum):
    """Types of insights that can be generated."""
    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    STRATEGIC = "strategic"
    RISK = "risk"
    OPPORTUNITY = "opportunity"


class Pattern(Enum):
    """Types of patterns that can be detected in data."""
    GROWTH = "growth"
    DECLINE = "decline"
    SEASONAL = "seasonal"
    ANOMALY = "anomaly"
    CORRELATION = "correlation"


@dataclass
class Theme:
    """Represents a theme extracted from multiple documents."""
    name: str
    documents: List[str]
    frequency: int
    entities: List[str]
    confidence: float


@dataclass
class Trend:
    """Represents a trend detected in time-series data."""
    metric: str
    direction: str
    magnitude: float
    time_period: Tuple[datetime, datetime]
    confidence: float


@dataclass
class Insight:
    """Represents an actionable insight derived from analysis."""
    type: InsightType
    title: str
    description: str
    supporting_data: Dict[str, Any]
    confidence: float
    priority: int
    source_ids: List[str]


class InsightGenerator:
    """
    Generates insights through theme extraction and trend analysis.
    
    This class analyzes synthesized documents to identify patterns, detect trends,
    and generate actionable insights for decision-making.
    """
    
    def __init__(self, synthesis_engine: SynthesisEngine, conflict_resolver: Optional[Any] = None):
        """
        Initialize the InsightGenerator.
        
        Args:
            synthesis_engine: The synthesis engine for accessing document data
            conflict_resolver: Optional conflict resolver for data validation
        """
        self.synthesis_engine = synthesis_engine
        self.conflict_resolver = conflict_resolver
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        
    def extract_themes(self, document_nodes: List[DocumentNode], min_support: int = 2) -> List[Theme]:
        """
        Extract themes from document nodes using semantic clustering.
        
        Args:
            document_nodes: List of document nodes to analyze
            min_support: Minimum number of documents required to form a theme
            
        Returns:
            List of extracted themes
        """
        try:
            if not document_nodes:
                return []
                
            # Extract text content from documents
            texts = []
            doc_ids = []
            for node in document_nodes:
                if node.content:
                    texts.append(str(node.content))
                    doc_ids.append(node.id)
                    
            if len(texts) < min_support:
                logger.warning(f"Insufficient documents ({len(texts)}) for theme extraction")
                return []
                
            # Vectorize documents
            doc_vectors = self.vectorizer.fit_transform(texts)
            
            # Calculate similarity matrix
            similarity_matrix = cosine_similarity(doc_vectors)
            
            # Cluster documents
            themes = self._cluster_themes(similarity_matrix, doc_ids, min_support)
            
            # Extract theme characteristics
            for theme in themes:
                theme.entities = self._extract_entities(theme.documents, document_nodes)
                theme.confidence = self._calculate_theme_confidence(theme, similarity_matrix)
                
            return sorted(themes, key=lambda t: t.confidence, reverse=True)
            
        except Exception as e:
            logger.error(f"Error extracting themes: {str(e)}")
            return []
            
    def analyze_trends(self, metrics_over_time: Dict[str, List[Tuple[datetime, float]]], 
                      confidence_threshold: float = 0.7) -> List[Trend]:
        """
        Analyze trends in time-series data.
        
        Args:
            metrics_over_time: Dictionary mapping metric names to time-series data
            confidence_threshold: Minimum confidence level for trend detection
            
        Returns:
            List of detected trends
        """
        trends = []
        
        for metric_name, time_series in metrics_over_time.items():
            if len(time_series) < 3:
                continue
                
            # Sort by time
            time_series = sorted(time_series, key=lambda x: x[0])
            times = [ts[0] for ts in time_series]
            values = np.array([ts[1] for ts in time_series])
            
            # Detect trend using linear regression
            x = np.arange(len(values))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
            
            # Calculate confidence
            confidence = abs(r_value)
            
            if confidence >= confidence_threshold:
                direction = "increasing" if slope > 0 else "decreasing"
                magnitude = abs(slope) / np.mean(values) if np.mean(values) != 0 else 0
                
                trend = Trend(
                    metric=metric_name,
                    direction=direction,
                    magnitude=magnitude,
                    time_period=(times[0], times[-1]),
                    confidence=confidence
                )
                trends.append(trend)
                
                # Check for anomalies
                anomalies = self._detect_anomalies(values)
                if anomalies:
                    logger.info(f"Anomalies detected in {metric_name}: {anomalies}")
                    
        return trends
        
    def detect_patterns(self, data_points: List[Dict[str, Any]], 
                       pattern_types: List[str] = ['growth', 'decline', 'anomaly']) -> List[Dict[str, Any]]:
        """
        Detect patterns in data points.
        
        Args:
            data_points: List of data points to analyze
            pattern_types: Types of patterns to detect
            
        Returns:
            List of detected patterns
        """
        patterns = []
        
        if 'growth' in pattern_types or 'decline' in pattern_types:
            # Extract numeric series
            numeric_data = self._extract_numeric_series(data_points)
            
            for series_name, values in numeric_data.items():
                if len(values) >= 3:
                    # Detect growth/decline patterns
                    pattern = self._detect_growth_decline(series_name, values)
                    if pattern:
                        patterns.append(pattern)
                        
        if 'anomaly' in pattern_types:
            # Detect anomalies
            anomaly_patterns = self._detect_anomaly_patterns(data_points)
            patterns.extend(anomaly_patterns)
            
        return patterns
        
    def generate_insights(self, synthesis_results: Dict[str, Any], max_insights: int = 10) -> List[Insight]:
        """
        Generate actionable insights from synthesis results.
        
        Args:
            synthesis_results: Results from synthesis engine
            max_insights: Maximum number of insights to generate
            
        Returns:
            List of prioritized insights
        """
        insights = []
        
        # Extract different types of data
        financial_data = synthesis_results.get('financial_data', {})
        operational_data = synthesis_results.get('operational_data', {})
        market_data = synthesis_results.get('market_data', {})
        strategic_content = synthesis_results.get('strategic_content', [])
        
        # Generate insights from different analyzers
        if financial_data:
            insights.extend(self._analyze_financial_trends(financial_data))
            
        if market_data:
            insights.extend(self._detect_market_patterns(market_data))
            
        if operational_data:
            insights.extend(self._identify_operational_insights(operational_data))
            
        if strategic_content:
            insights.extend(self._assess_strategic_themes(strategic_content))
            
        # Score and prioritize insights
        scored_insights = self.score_insights(insights)
        
        # Return top insights
        return sorted(scored_insights, key=lambda i: i.priority, reverse=True)[:max_insights]
        
    def score_insights(self, insights: List[Insight]) -> List[Insight]:
        """
        Score and prioritize insights based on confidence and impact.
        
        Args:
            insights: List of insights to score
            
        Returns:
            List of scored insights with updated priorities
        """
        for insight in insights:
            # Calculate priority score based on multiple factors
            base_score = insight.confidence * 100
            
            # Boost score based on insight type
            type_multipliers = {
                InsightType.RISK: 1.5,
                InsightType.OPPORTUNITY: 1.3,
                InsightType.FINANCIAL: 1.2,
                InsightType.STRATEGIC: 1.1,
                InsightType.OPERATIONAL: 1.0
            }
            
            type_multiplier = type_multipliers.get(insight.type, 1.0)
            
            # Consider supporting data volume
            data_factor = min(len(insight.supporting_data) / 5, 1.0)
            
            # Calculate final priority
            insight.priority = int(base_score * type_multiplier * (0.7 + 0.3 * data_factor))
            
        return insights
        
    def _analyze_financial_trends(self, financial_data: Dict[str, Any]) -> List[Insight]:
        """
        Analyze financial trends for revenue, costs, and margins.
        
        Args:
            financial_data: Financial data to analyze
            
        Returns:
            List of financial insights
        """
        insights = []
        
        # Analyze revenue trends
        if 'revenue' in financial_data:
            revenue_trend = self._analyze_metric_trend(financial_data['revenue'], 'Revenue')
            if revenue_trend:
                insight = Insight(
                    type=InsightType.FINANCIAL,
                    title=f"Revenue {revenue_trend['direction']}",
                    description=f"Revenue shows {revenue_trend['magnitude']:.1%} {revenue_trend['direction']} trend",
                    supporting_data=revenue_trend,
                    confidence=revenue_trend['confidence'],
                    priority=0,
                    source_ids=financial_data.get('source_ids', [])
                )
                insights.append(insight)
                
        # Analyze cost trends
        if 'costs' in financial_data:
            cost_trend = self._analyze_metric_trend(financial_data['costs'], 'Costs')
            if cost_trend and cost_trend['direction'] == 'increasing':
                insight = Insight(
                    type=InsightType.RISK,
                    title="Rising Cost Trend",
                    description=f"Costs increasing at {cost_trend['magnitude']:.1%} rate",
                    supporting_data=cost_trend,
                    confidence=cost_trend['confidence'],
                    priority=0,
                    source_ids=financial_data.get('source_ids', [])
                )
                insights.append(insight)
                
        # Analyze margins
        if 'revenue' in financial_data and 'costs' in financial_data:
            margin_insight = self._analyze_margins(financial_data)
            if margin_insight:
                insights.append(margin_insight)
                
        return insights
        
    def _detect_market_patterns(self, market_data: Dict[str, Any]) -> List[Insight]:
        """
        Detect patterns in market data for competitive positioning.
        
        Args:
            market_data: Market data to analyze
            
        Returns:
            List of market insights
        """
        insights = []
        
        # Analyze market share trends
        if 'market_share' in market_data:
            share_pattern = self._analyze_market_share(market_data['market_share'])
            if share_pattern:
                insight_type = InsightType.OPPORTUNITY if share_pattern['trend'] == 'gaining' else InsightType.RISK
                insight = Insight(
                    type=insight_type,
                    title=f"Market Share {share_pattern['trend'].title()}",
                    description=share_pattern['description'],
                    supporting_data=share_pattern,
                    confidence=share_pattern['confidence'],
                    priority=0,
                    source_ids=market_data.get('source_ids', [])
                )
                insights.append(insight)
                
        # Analyze competitive positioning
        if 'competitors' in market_data:
            competitive_insights = self._analyze_competition(market_data['competitors'])
            insights.extend(competitive_insights)
            
        return insights
        
    def _identify_operational_insights(self, operational_data: Dict[str, Any]) -> List[Insight]:
        """
        Identify insights from operational efficiency metrics.
        
        Args:
            operational_data: Operational data to analyze
            
        Returns:
            List of operational insights
        """
        insights = []
        
        # Analyze efficiency metrics
        if 'efficiency_metrics' in operational_data:
            for metric_name, metric_data in operational_data['efficiency_metrics'].items():
                efficiency_pattern = self._analyze_efficiency(metric_name, metric_data)
                if efficiency_pattern:
                    insight = Insight(
                        type=InsightType.OPERATIONAL,
                        title=efficiency_pattern['title'],
                        description=efficiency_pattern['description'],
                        supporting_data=efficiency_pattern,
                        confidence=efficiency_pattern['confidence'],
                        priority=0,
                        source_ids=operational_data.get('source_ids', [])
                    )
                    insights.append(insight)
                    
        # Analyze process bottlenecks
        if 'process_data' in operational_data:
            bottleneck_insights = self._identify_bottlenecks(operational_data['process_data'])
            insights.extend(bottleneck_insights)
            
        return insights
        
    def _assess_strategic_themes(self, strategic_content: List[Dict[str, Any]]) -> List[Insight]:
        """
        Assess strategic themes from business initiatives.
        
        Args:
            strategic_content: Strategic content to analyze
            
        Returns:
            List of strategic insights
        """
        insights = []
        
        # Extract and analyze strategic themes
        themes = self._extract_strategic_themes(strategic_content)
        
        for theme in themes:
            if theme['importance'] > 0.7:
                insight = Insight(
                    type=InsightType.STRATEGIC,
                    title=f"Strategic Focus: {theme['name']}",
                    description=theme['description'],
                    supporting_data=theme,
                    confidence=theme['confidence'],
                    priority=0,
                    source_ids=theme.get('source_ids', [])
                )
                insights.append(insight)
                
        # Identify strategic gaps
        gaps = self._identify_strategic_gaps(themes, strategic_content)
        for gap in gaps:
            insight = Insight(
                type=InsightType.RISK,
                title=f"Strategic Gap: {gap['area']}",
                description=gap['description'],
                supporting_data=gap,
                confidence=gap['confidence'],
                priority=0,
                source_ids=gap.get('source_ids', [])
            )
            insights.append(insight)
            
        return insights
        
    def _calculate_trend_confidence(self, data_points: List[float], trend: Dict[str, Any]) -> float:
        """
        Calculate confidence score for a detected trend.
        
        Args:
            data_points: The data points analyzed
            trend: The detected trend
            
        Returns:
            Confidence score between 0 and 1
        """
        if len(data_points) < 3:
            return 0.0
            
        # Calculate R-squared value
        x = np.arange(len(data_points))
        y = np.array(data_points)
        
        # Fit linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        
        # Calculate confidence based on R-squared and p-value
        r_squared = r_value ** 2
        p_confidence = 1 - p_value if p_value < 0.05 else 0
        
        # Combine factors
        confidence = 0.7 * r_squared + 0.3 * p_confidence
        
        return min(max(confidence, 0.0), 1.0)
        
    def _cluster_themes(self, similarity_matrix: np.ndarray, doc_ids: List[str], 
                       min_support: int) -> List[Theme]:
        """
        Cluster documents into themes based on similarity.
        
        Args:
            similarity_matrix: Document similarity matrix
            doc_ids: Document IDs
            min_support: Minimum cluster size
            
        Returns:
            List of themes
        """
        # Convert similarity to distance
        distance_matrix = 1 - similarity_matrix
        
        # Perform DBSCAN clustering
        clustering = DBSCAN(eps=0.3, min_samples=min_support, metric='precomputed')
        labels = clustering.fit_predict(distance_matrix)
        
        # Extract themes from clusters
        themes = []
        unique_labels = set(labels)
        
        for label in unique_labels:
            if label == -1:  # Skip noise points
                continue
                
            # Get documents in cluster
            cluster_docs = [doc_ids[i] for i, l in enumerate(labels) if l == label]
            
            if len(cluster_docs) >= min_support:
                theme = Theme(
                    name=f"Theme_{label}",
                    documents=cluster_docs,
                    frequency=len(cluster_docs),
                    entities=[],
                    confidence=0.0
                )
                themes.append(theme)
                
        return themes
        
    def _generate_recommendation(self, pattern: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Generate actionable recommendation based on pattern and context.
        
        Args:
            pattern: Detected pattern
            context: Additional context
            
        Returns:
            Recommendation text
        """
        pattern_type = pattern.get('type', '')
        
        recommendations = {
            'growth': f"Continue investing in {pattern.get('area', 'this area')} to maintain growth momentum",
            'decline': f"Review and optimize {pattern.get('area', 'this area')} to reverse declining trend",
            'anomaly': f"Investigate unusual activity in {pattern.get('area', 'this metric')} for root cause",
            'inefficiency': f"Implement process improvements in {pattern.get('area', 'this area')} to increase efficiency",
            'opportunity': f"Consider expanding {pattern.get('area', 'operations')} based on positive indicators"
        }
        
        return recommendations.get(pattern_type, "Further analysis recommended")
        
    def _validate_insight(self, insight: Insight, supporting_data: Dict[str, Any]) -> bool:
        """
        Validate insight against supporting data.
        
        Args:
            insight: Insight to validate
            supporting_data: Data supporting the insight
            
        Returns:
            True if insight is valid
        """
        # Check minimum confidence
        if insight.confidence < 0.5:
            return False
            
        # Validate supporting data
        if not insight.supporting_data:
            return False
            
        # Use conflict resolver if available
        if self.conflict_resolver:
            conflicts = self.conflict_resolver.check_conflicts(insight.supporting_data)
            if conflicts:
                logger.warning(f"Conflicts detected in insight: {conflicts}")
                return False
                
        return True
        
    def _detect_anomalies(self, values: np.ndarray) -> List[int]:
        """Detect anomalies using z-score method."""
        z_scores = np.abs(stats.zscore(values))
        threshold = 3
        return list(np.where(z_scores > threshold)[0])
        
    def _extract_numeric_series(self, data_points: List[Dict[str, Any]]) -> Dict[str, List[float]]:
        """Extract numeric time series from data points."""
        series = {}
        
        for point in data_points:
            for key, value in point.items():
                if isinstance(value, (int, float)):
                    if key not in series:
                        series[key] = []
                    series[key].append(value)
                    
        return series
        
    def _detect_growth_decline(self, series_name: str, values: List[float]) -> Optional[Dict[str, Any]]:
        """Detect growth or decline pattern in values."""
        if len(values) < 3:
            return None
            
        # Calculate trend
        x = np.arange(len(values))
        slope, _, r_value, _, _ = stats.linregress(x, values)
        
        if abs(r_value) > 0.7:  # Strong correlation
            pattern_type = 'growth' if slope > 0 else 'decline'
            magnitude = abs(slope) / np.mean(values) if np.mean(values) != 0 else 0
            
            return {
                'type': pattern_type,
                'area': series_name,
                'magnitude': magnitude,
                'confidence': abs(r_value)
            }
            
        return None
        
    def _detect_anomaly_patterns(self, data_points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect anomaly patterns in data."""
        patterns = []
        
        # Extract numeric series
        numeric_data = self._extract_numeric_series(data_points)
        
        for series_name, values in numeric_data.items():
            if len(values) >= 5:
                anomalies = self._detect_anomalies(np.array(values))
                if anomalies:
                    patterns.append({
                        'type': 'anomaly',
                        'area': series_name,
                        'anomaly_indices': anomalies,
                        'confidence': 0.8
                    })
                    
        return patterns
        
    def _extract_entities(self, doc_ids: List[str], document_nodes: List[DocumentNode]) -> List[str]:
        """Extract entities from documents in a theme."""
        entities = set()
        
        for doc_id in doc_ids:
            for node in document_nodes:
                if node.id == doc_id and node.metadata:
                    # Extract entities from metadata
                    doc_entities = node.metadata.get('entities', [])
                    entities.update(doc_entities)
                    
        return list(entities)
        
    def _calculate_theme_confidence(self, theme: Theme, similarity_matrix: np.ndarray) -> float:
        """Calculate confidence score for a theme."""
        if theme.frequency < 2:
            return 0.0
            
        # Base confidence on frequency and entity coverage
        freq_score = min(theme.frequency / 10, 1.0)
        entity_score = min(len(theme.entities) / 5, 1.0)
        
        confidence = 0.6 * freq_score + 0.4 * entity_score
        
        return confidence
        
    def _analyze_metric_trend(self, metric_data: List[Tuple[datetime, float]], 
                             metric_name: str) -> Optional[Dict[str, Any]]:
        """Analyze trend for a specific metric."""
        if len(metric_data) < 3:
            return None
            
        # Sort by time
        metric_data = sorted(metric_data, key=lambda x: x[0])
        values = [v[1] for v in metric_data]
        
        # Calculate trend
        x = np.arange(len(values))
        slope, _, r_value, _, _ = stats.linregress(x, values)
        
        if abs(r_value) > 0.6:
            direction = 'increasing' if slope > 0 else 'decreasing'
            magnitude = abs(slope) / np.mean(values) if np.mean(values) != 0 else 0
            
            return {
                'metric': metric_name,
                'direction': direction,
                'magnitude': magnitude,
                'confidence': abs(r_value),
                'data_points': len(values)
            }
            
        return None
        
    def _analyze_margins(self, financial_data: Dict[str, Any]) -> Optional[Insight]:
        """Analyze profit margins from financial data."""
        revenues = financial_data.get('revenue', [])
        costs = financial_data.get('costs', [])
        
        if not revenues or not costs or len(revenues) != len(costs):
            return None
            
        # Calculate margins
        margins = []
        for i in range(len(revenues)):
            if revenues[i][1] > 0:
                margin = (revenues[i][1] - costs[i][1]) / revenues[i][1]
                margins.append((revenues[i][0], margin))
                
        if margins:
            # Analyze margin trend
            margin_trend = self._analyze_metric_trend(margins, 'Profit Margin')
            if margin_trend:
                insight_type = InsightType.OPPORTUNITY if margin_trend['direction'] == 'increasing' else InsightType.RISK
                
                return Insight(
                    type=insight_type,
                    title=f"Profit Margin {margin_trend['direction'].title()}",
                    description=f"Margins showing {margin_trend['magnitude']:.1%} {margin_trend['direction']} trend",
                    supporting_data=margin_trend,
                    confidence=margin_trend['confidence'],
                    priority=0,
                    source_ids=financial_data.get('source_ids', [])
                )
                
        return None
        
    def _analyze_market_share(self, market_share_data: List[Tuple[datetime, float]]) -> Optional[Dict[str, Any]]:
        """Analyze market share trends."""
        if len(market_share_data) < 3:
            return None
            
        trend = self._analyze_metric_trend(market_share_data, 'Market Share')
        if trend:
            trend['trend'] = 'gaining' if trend['direction'] == 'increasing' else 'losing'
            trend['description'] = f"Market share {trend['trend']} at {trend['magnitude']:.1%} rate"
            
        return trend
        
    def _analyze_competition(self, competitors_data: Dict[str, Any]) -> List[Insight]:
        """Analyze competitive positioning."""
        insights = []
        
        # Analyze relative performance
        if 'performance_comparison' in competitors_data:
            for metric, comparison in competitors_data['performance_comparison'].items():
                if comparison.get('vs_industry_avg', 0) < -0.1:
                    insight = Insight(
                        type=InsightType.RISK,
                        title=f"Below Industry Average: {metric}",
                        description=f"Performance in {metric} is {abs(comparison['vs_industry_avg']):.1%} below industry average",
                        supporting_data=comparison,
                        confidence=0.8,
                        priority=0,
                        source_ids=competitors_data.get('source_ids', [])
                    )
                    insights.append(insight)
                    
        return insights
        
    def _analyze_efficiency(self, metric_name: str, metric_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze efficiency metrics."""
        if 'current' in metric_data and 'benchmark' in metric_data:
            current = metric_data['current']
            benchmark = metric_data['benchmark']
            
            if benchmark > 0:
                efficiency_ratio = current / benchmark
                
                if efficiency_ratio < 0.8:
                    return {
                        'title': f"Low Efficiency: {metric_name}",
                        'description': f"{metric_name} operating at {efficiency_ratio:.1%} of benchmark",
                        'confidence': 0.85,
                        'metric': metric_name,
                        'current': current,
                        'benchmark': benchmark
                    }
                elif efficiency_ratio > 1.2:
                    return {
                        'title': f"High Efficiency: {metric_name}",
                        'description': f"{metric_name} performing {efficiency_ratio:.1%} above benchmark",
                        'confidence': 0.85,
                        'metric': metric_name,
                        'current': current,
                        'benchmark': benchmark
                    }
                    
        return None
        
    def _identify_bottlenecks(self, process_data: Dict[str, Any]) -> List[Insight]:
        """Identify process bottlenecks."""
        insights = []
        
        if 'cycle_times' in process_data:
            for process, cycle_time in process_data['cycle_times'].items():
                if 'average' in cycle_time and 'target' in cycle_time:
                    if cycle_time['average'] > cycle_time['target'] * 1.2:
                        insight = Insight(
                            type=InsightType.OPERATIONAL,
                            title=f"Process Bottleneck: {process}",
                            description=f"{process} taking {(cycle_time['average']/cycle_time['target']-1):.1%} longer than target",
                            supporting_data=cycle_time,
                            confidence=0.9,
                            priority=0,
                            source_ids=process_data.get('source_ids', [])
                        )
                        insights.append(insight)
                        
        return insights
        
    def _extract_strategic_themes(self, strategic_content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract themes from strategic content."""
        themes = []
        
        # Count theme occurrences
        theme_counts = {}
        for content in strategic_content:
            if 'themes' in content:
                for theme in content['themes']:
                    if theme not in theme_counts:
                        theme_counts[theme] = {'count': 0, 'sources': []}
                    theme_counts[theme]['count'] += 1
                    theme_counts[theme]['sources'].extend(content.get('source_ids', []))
                    
        # Create theme objects
        total_docs = len(strategic_content)
        for theme_name, data in theme_counts.items():
            importance = data['count'] / total_docs if total_docs > 0 else 0
            
            themes.append({
                'name': theme_name,
                'importance': importance,
                'description': f"{theme_name} mentioned in {data['count']} strategic documents",
                'confidence': min(importance * 1.5, 1.0),
                'source_ids': list(set(data['sources']))
            })
            
        return themes
        
    def _identify_strategic_gaps(self, themes: List[Dict[str, Any]], 
                                strategic_content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify gaps in strategic coverage."""
        gaps = []
        
        # Define expected strategic areas
        expected_areas = {'growth', 'innovation', 'efficiency', 'customer', 'talent'}
        
        # Extract covered areas
        covered_areas = set()
        for theme in themes:
            theme_name = theme['name'].lower()
            for area in expected_areas:
                if area in theme_name:
                    covered_areas.add(area)
                    
        # Identify gaps
        missing_areas = expected_areas - covered_areas
        
        for area in missing_areas:
            gaps.append({
                'area': area.title(),
                'description': f"No strategic initiatives found addressing {area}",
                'confidence': 0.7,
                'source_ids': []
            })
            
        return gaps