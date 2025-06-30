"""
Intelligent Content Synthesis Engine

Analyzes and synthesizes content from multiple documents, creating relationships,
detecting patterns, and building comprehensive understanding across sources.
"""

from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
import re
from collections import defaultdict, Counter
import hashlib
import json
from enum import Enum


class DocumentType(Enum):
    """Types of documents for analysis"""
    FINANCIAL_REPORT = "financial_report"
    PRESENTATION = "presentation"
    SPREADSHEET = "spreadsheet"
    RESEARCH_REPORT = "research_report"
    NEWS_ARTICLE = "news_article"
    REGULATORY_FILING = "regulatory_filing"
    INTERNAL_MEMO = "internal_memo"
    UNKNOWN = "unknown"


class RelationshipType(Enum):
    """Types of relationships between documents"""
    REFERENCES = "references"
    CONTRADICTS = "contradicts"
    SUPPLEMENTS = "supplements"
    UPDATES = "updates"
    DERIVED_FROM = "derived_from"
    SIMILAR_TO = "similar_to"


@dataclass
class DocumentNode:
    """Represents a document in the synthesis graph"""
    doc_id: str
    doc_type: DocumentType
    source_path: str
    extraction_date: datetime
    metadata: Dict[str, Any]
    entities: Set[str] = field(default_factory=set)
    topics: Set[str] = field(default_factory=set)
    key_metrics: Dict[str, Any] = field(default_factory=dict)
    time_references: Set[str] = field(default_factory=set)
    confidence_score: float = 0.0
    content_hash: str = ""
    
    def __post_init__(self):
        """Generate content hash if not provided"""
        if not self.content_hash:
            content_str = f"{self.doc_type.value}:{self.source_path}:{str(self.extraction_date)}"
            self.content_hash = hashlib.md5(content_str.encode()).hexdigest()


@dataclass
class DocumentRelationship:
    """Represents a relationship between two documents"""
    source_doc_id: str
    target_doc_id: str
    relationship_type: RelationshipType
    confidence: float
    evidence: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContentCluster:
    """Represents a cluster of related content"""
    cluster_id: str
    theme: str
    documents: Set[str] = field(default_factory=set)
    entities: Set[str] = field(default_factory=set)
    topics: Set[str] = field(default_factory=set)
    time_range: Optional[Tuple[datetime, datetime]] = None
    importance_score: float = 0.0


@dataclass
class SynthesisResult:
    """Result of document synthesis"""
    document_graph: Dict[str, DocumentNode]
    relationships: List[DocumentRelationship]
    clusters: List[ContentCluster]
    entity_map: Dict[str, Set[str]]  # entity -> document IDs
    timeline: List[Dict[str, Any]]
    conflicts: List[Dict[str, Any]]
    insights: List[Dict[str, Any]]
    synthesis_metadata: Dict[str, Any]


class DocumentGraphBuilder:
    """Builds relationships between documents based on content analysis"""
    
    def __init__(self):
        self.similarity_threshold = 0.7
        self.entity_patterns = {
            'company': r'\b[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*(?:\s+(?:Inc|Corp|LLC|Ltd|Company|Co)\.?)\b',
            'person': r'\b(?:Mr|Ms|Mrs|Dr|Prof)\.?\s+[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*\b',
            'monetary': r'\$[\d,]+(?:\.\d{2})?[MBK]?\b|\b\d+(?:\.\d+)?\s*(?:million|billion|thousand)\b',
            'percentage': r'\b\d+(?:\.\d+)?%\b',
            'date': r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b|\b(?:Q[1-4]|FY)\s*\d{4}\b',
            'product': r'\b[A-Z][A-Za-z]+(?:\s+[A-Z\d]+)*\s+(?:v\d+|Version|Edition)\b'
        }
    
    def build_document_node(self, doc_data: Dict[str, Any]) -> DocumentNode:
        """Create a document node from extracted data"""
        # Determine document type
        doc_type = self._classify_document_type(doc_data)
        
        # Extract entities
        entities = self._extract_entities(doc_data)
        
        # Extract topics
        topics = self._extract_topics(doc_data)
        
        # Extract key metrics
        key_metrics = self._extract_key_metrics(doc_data)
        
        # Extract time references
        time_refs = self._extract_time_references(doc_data)
        
        # Calculate confidence score
        confidence = self._calculate_confidence(doc_data)
        
        return DocumentNode(
            doc_id=doc_data.get('doc_id', self._generate_doc_id(doc_data)),
            doc_type=doc_type,
            source_path=doc_data.get('source_path', ''),
            extraction_date=datetime.now(),
            metadata=doc_data.get('metadata', {}),
            entities=entities,
            topics=topics,
            key_metrics=key_metrics,
            time_references=time_refs,
            confidence_score=confidence
        )
    
    def find_relationships(self, nodes: List[DocumentNode]) -> List[DocumentRelationship]:
        """Find relationships between document nodes"""
        relationships = []
        
        for i, node1 in enumerate(nodes):
            for node2 in nodes[i+1:]:
                # Check for various relationship types
                rels = self._analyze_relationship(node1, node2)
                relationships.extend(rels)
        
        return relationships
    
    def _classify_document_type(self, doc_data: Dict[str, Any]) -> DocumentType:
        """Classify document type based on content and metadata"""
        source_path = doc_data.get('source_path', '').lower()
        content = str(doc_data.get('content', '')).lower()
        
        if any(term in source_path for term in ['.xlsx', '.xls', 'spreadsheet']):
            return DocumentType.SPREADSHEET
        elif any(term in source_path for term in ['.pptx', '.ppt', 'presentation']):
            return DocumentType.PRESENTATION
        elif any(term in content for term in ['financial statement', 'balance sheet', 'income statement']):
            return DocumentType.FINANCIAL_REPORT
        elif any(term in content for term in ['research report', 'analysis report']):
            return DocumentType.RESEARCH_REPORT
        elif any(term in content for term in ['form 10-k', 'form 10-q', 'sec filing']):
            return DocumentType.REGULATORY_FILING
        else:
            return DocumentType.UNKNOWN
    
    def _extract_entities(self, doc_data: Dict[str, Any]) -> Set[str]:
        """Extract named entities from document"""
        entities = set()
        content = str(doc_data.get('content', ''))
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, content)
            entities.update(matches)
        
        # Also extract from structured data
        if 'financial_metrics' in doc_data:
            entities.update(doc_data['financial_metrics'].keys())
        
        return entities
    
    def _extract_topics(self, doc_data: Dict[str, Any]) -> Set[str]:
        """Extract topics from document content"""
        topics = set()
        
        # Topic keywords
        topic_keywords = {
            'revenue': ['revenue', 'sales', 'income', 'receipts'],
            'profitability': ['profit', 'margin', 'earnings', 'ebitda'],
            'growth': ['growth', 'expansion', 'increase', 'yoy'],
            'market': ['market', 'competition', 'share', 'position'],
            'strategy': ['strategy', 'plan', 'initiative', 'roadmap'],
            'risk': ['risk', 'threat', 'challenge', 'mitigation']
        }
        
        content = str(doc_data.get('content', '')).lower()
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in content for keyword in keywords):
                topics.add(topic)
        
        return topics
    
    def _extract_key_metrics(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key metrics from document"""
        metrics = {}
        
        # From structured data
        if 'financial_metrics' in doc_data:
            metrics.update(doc_data['financial_metrics'])
        
        # Extract from content using patterns
        content = str(doc_data.get('content', ''))
        
        # Revenue pattern
        revenue_matches = re.findall(r'revenue[:\s]+\$?([\d,]+(?:\.\d+)?[MBK]?)', content, re.IGNORECASE)
        if revenue_matches:
            metrics['revenue'] = revenue_matches[0]
        
        # Profit pattern
        profit_matches = re.findall(r'profit[:\s]+\$?([\d,]+(?:\.\d+)?[MBK]?)', content, re.IGNORECASE)
        if profit_matches:
            metrics['profit'] = profit_matches[0]
        
        return metrics
    
    def _extract_time_references(self, doc_data: Dict[str, Any]) -> Set[str]:
        """Extract time references from document"""
        time_refs = set()
        content = str(doc_data.get('content', ''))
        
        # Date patterns
        date_matches = re.findall(self.entity_patterns['date'], content)
        time_refs.update(date_matches)
        
        # Relative time references
        relative_patterns = [
            r'last\s+(?:year|quarter|month)',
            r'next\s+(?:year|quarter|month)',
            r'current\s+(?:year|quarter|month)',
            r'YTD',
            r'year-to-date'
        ]
        
        for pattern in relative_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            time_refs.update(matches)
        
        return time_refs
    
    def _calculate_confidence(self, doc_data: Dict[str, Any]) -> float:
        """Calculate confidence score for document"""
        confidence = 0.5  # Base confidence
        
        # Increase for structured data
        if 'financial_metrics' in doc_data:
            confidence += 0.2
        
        # Increase for source references
        if 'source_refs' in doc_data and doc_data['source_refs']:
            confidence += 0.1
        
        # Increase for metadata completeness
        metadata = doc_data.get('metadata', {})
        if metadata.get('author'):
            confidence += 0.1
        if metadata.get('date'):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _generate_doc_id(self, doc_data: Dict[str, Any]) -> str:
        """Generate unique document ID"""
        source = doc_data.get('source_path', 'unknown')
        timestamp = datetime.now().isoformat()
        return hashlib.md5(f"{source}:{timestamp}".encode()).hexdigest()[:12]
    
    def _analyze_relationship(self, node1: DocumentNode, node2: DocumentNode) -> List[DocumentRelationship]:
        """Analyze relationship between two document nodes"""
        relationships = []
        
        # Check entity overlap
        common_entities = node1.entities.intersection(node2.entities)
        if len(common_entities) > 2:
            relationships.append(DocumentRelationship(
                source_doc_id=node1.doc_id,
                target_doc_id=node2.doc_id,
                relationship_type=RelationshipType.SIMILAR_TO,
                confidence=len(common_entities) / max(len(node1.entities), len(node2.entities)),
                evidence=[f"Common entities: {', '.join(list(common_entities)[:5])}"]
            ))
        
        # Check time sequence
        if node1.time_references and node2.time_references:
            if self._is_update_relationship(node1, node2):
                relationships.append(DocumentRelationship(
                    source_doc_id=node2.doc_id,
                    target_doc_id=node1.doc_id,
                    relationship_type=RelationshipType.UPDATES,
                    confidence=0.8,
                    evidence=["Temporal sequence detected"]
                ))
        
        # Check metric conflicts
        conflicts = self._find_metric_conflicts(node1, node2)
        if conflicts:
            relationships.append(DocumentRelationship(
                source_doc_id=node1.doc_id,
                target_doc_id=node2.doc_id,
                relationship_type=RelationshipType.CONTRADICTS,
                confidence=0.9,
                evidence=conflicts
            ))
        
        return relationships
    
    def _is_update_relationship(self, node1: DocumentNode, node2: DocumentNode) -> bool:
        """Check if one document updates another based on time references"""
        # Simple heuristic - check if one has more recent time references
        try:
            node1_dates = [self._parse_date(ref) for ref in node1.time_references if self._parse_date(ref)]
            node2_dates = [self._parse_date(ref) for ref in node2.time_references if self._parse_date(ref)]
            
            if node1_dates and node2_dates:
                return max(node2_dates) > max(node1_dates)
        except:
            pass
        
        return False
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime"""
        # Simple implementation - would need more robust parsing
        try:
            # Handle Q1 2024 format
            if re.match(r'Q\d\s+\d{4}', date_str):
                quarter, year = date_str.split()
                quarter_num = int(quarter[1])
                month = (quarter_num - 1) * 3 + 1
                return datetime(int(year), month, 1)
            # Add more date parsing logic as needed
        except:
            pass
        return None
    
    def _find_metric_conflicts(self, node1: DocumentNode, node2: DocumentNode) -> List[str]:
        """Find conflicting metrics between documents"""
        conflicts = []
        
        for metric in set(node1.key_metrics.keys()).intersection(node2.key_metrics.keys()):
            val1 = str(node1.key_metrics[metric])
            val2 = str(node2.key_metrics[metric])
            
            # Simple comparison - would need more sophisticated logic
            if val1 != val2:
                conflicts.append(f"Conflicting {metric}: {val1} vs {val2}")
        
        return conflicts


class SemanticClusteringEngine:
    """Clusters documents based on semantic similarity"""
    
    def __init__(self):
        self.min_cluster_size = 2
        self.similarity_threshold = 0.6
    
    def cluster_documents(self, nodes: List[DocumentNode], 
                         relationships: List[DocumentRelationship]) -> List[ContentCluster]:
        """Cluster documents based on content similarity"""
        clusters = []
        
        # Build similarity matrix
        similarity_matrix = self._build_similarity_matrix(nodes)
        
        # Perform clustering
        cluster_assignments = self._hierarchical_clustering(similarity_matrix)
        
        # Create cluster objects
        for cluster_id, doc_indices in cluster_assignments.items():
            if len(doc_indices) >= self.min_cluster_size:
                cluster = self._create_cluster(cluster_id, 
                                             [nodes[i] for i in doc_indices])
                clusters.append(cluster)
        
        return clusters
    
    def _build_similarity_matrix(self, nodes: List[DocumentNode]) -> List[List[float]]:
        """Build document similarity matrix"""
        n = len(nodes)
        matrix = [[0.0] * n for _ in range(n)]
        
        for i in range(n):
            for j in range(i+1, n):
                similarity = self._calculate_similarity(nodes[i], nodes[j])
                matrix[i][j] = similarity
                matrix[j][i] = similarity
        
        return matrix
    
    def _calculate_similarity(self, node1: DocumentNode, node2: DocumentNode) -> float:
        """Calculate similarity between two document nodes"""
        # Entity similarity
        entity_sim = len(node1.entities.intersection(node2.entities)) / \
                    max(len(node1.entities.union(node2.entities)), 1)
        
        # Topic similarity
        topic_sim = len(node1.topics.intersection(node2.topics)) / \
                   max(len(node1.topics.union(node2.topics)), 1)
        
        # Metric similarity
        common_metrics = set(node1.key_metrics.keys()).intersection(
                        set(node2.key_metrics.keys()))
        metric_sim = len(common_metrics) / \
                    max(len(set(node1.key_metrics.keys()).union(
                        set(node2.key_metrics.keys()))), 1)
        
        # Weighted average
        return 0.4 * entity_sim + 0.3 * topic_sim + 0.3 * metric_sim
    
    def _hierarchical_clustering(self, similarity_matrix: List[List[float]]) -> Dict[int, List[int]]:
        """Perform hierarchical clustering on similarity matrix"""
        # Simple implementation - would use scipy in production
        n = len(similarity_matrix)
        clusters = {i: [i] for i in range(n)}
        cluster_id = n
        
        while len(clusters) > 1:
            # Find most similar pair
            max_sim = 0
            merge_pair = None
            
            cluster_keys = list(clusters.keys())
            for i, c1 in enumerate(cluster_keys):
                for c2 in cluster_keys[i+1:]:
                    sim = self._cluster_similarity(clusters[c1], clusters[c2], 
                                                  similarity_matrix)
                    if sim > max_sim and sim >= self.similarity_threshold:
                        max_sim = sim
                        merge_pair = (c1, c2)
            
            if merge_pair is None:
                break
            
            # Merge clusters
            c1, c2 = merge_pair
            clusters[cluster_id] = clusters[c1] + clusters[c2]
            del clusters[c1]
            del clusters[c2]
            cluster_id += 1
        
        return clusters
    
    def _cluster_similarity(self, cluster1: List[int], cluster2: List[int], 
                          similarity_matrix: List[List[float]]) -> float:
        """Calculate similarity between two clusters (average linkage)"""
        total_sim = 0
        count = 0
        
        for i in cluster1:
            for j in cluster2:
                total_sim += similarity_matrix[i][j]
                count += 1
        
        return total_sim / count if count > 0 else 0
    
    def _create_cluster(self, cluster_id: int, nodes: List[DocumentNode]) -> ContentCluster:
        """Create cluster object from document nodes"""
        # Aggregate entities and topics
        all_entities = set()
        all_topics = set()
        doc_ids = set()
        
        for node in nodes:
            all_entities.update(node.entities)
            all_topics.update(node.topics)
            doc_ids.add(node.doc_id)
        
        # Determine theme
        theme = self._determine_cluster_theme(nodes)
        
        # Calculate importance
        importance = sum(node.confidence_score for node in nodes) / len(nodes)
        
        return ContentCluster(
            cluster_id=f"cluster_{cluster_id}",
            theme=theme,
            documents=doc_ids,
            entities=all_entities,
            topics=all_topics,
            importance_score=importance
        )
    
    def _determine_cluster_theme(self, nodes: List[DocumentNode]) -> str:
        """Determine the main theme of a cluster"""
        # Count topic frequencies
        topic_counts = Counter()
        for node in nodes:
            topic_counts.update(node.topics)
        
        if topic_counts:
            return topic_counts.most_common(1)[0][0]
        return "general"


class SynthesisEngine:
    """Main synthesis engine that orchestrates document analysis"""
    
    def __init__(self):
        self.graph_builder = DocumentGraphBuilder()
        self.clustering_engine = SemanticClusteringEngine()
    
    def synthesize_documents(self, documents: List[Dict[str, Any]]) -> SynthesisResult:
        """
        Synthesize information from multiple documents
        
        Args:
            documents: List of document data dictionaries
            
        Returns:
            SynthesisResult containing graph, relationships, clusters, etc.
        """
        # Build document nodes
        nodes = []
        for doc in documents:
            node = self.graph_builder.build_document_node(doc)
            nodes.append(node)
        
        # Find relationships
        relationships = self.graph_builder.find_relationships(nodes)
        
        # Cluster documents
        clusters = self.clustering_engine.cluster_documents(nodes, relationships)
        
        # Build entity map
        entity_map = self._build_entity_map(nodes)
        
        # Extract timeline
        timeline = self._extract_timeline(nodes)
        
        # Find conflicts
        conflicts = self._find_conflicts(nodes, relationships)
        
        # Generate insights
        insights = self._generate_insights(nodes, relationships, clusters)
        
        # Create document graph
        document_graph = {node.doc_id: node for node in nodes}
        
        return SynthesisResult(
            document_graph=document_graph,
            relationships=relationships,
            clusters=clusters,
            entity_map=entity_map,
            timeline=timeline,
            conflicts=conflicts,
            insights=insights,
            synthesis_metadata={
                'num_documents': len(documents),
                'num_relationships': len(relationships),
                'num_clusters': len(clusters),
                'synthesis_date': datetime.now().isoformat()
            }
        )
    
    def _build_entity_map(self, nodes: List[DocumentNode]) -> Dict[str, Set[str]]:
        """Build map of entities to documents containing them"""
        entity_map = defaultdict(set)
        
        for node in nodes:
            for entity in node.entities:
                entity_map[entity].add(node.doc_id)
        
        return dict(entity_map)
    
    def _extract_timeline(self, nodes: List[DocumentNode]) -> List[Dict[str, Any]]:
        """Extract timeline of events from documents"""
        timeline = []
        
        for node in nodes:
            for time_ref in node.time_references:
                # Extract events associated with time references
                timeline.append({
                    'date': time_ref,
                    'doc_id': node.doc_id,
                    'doc_type': node.doc_type.value,
                    'confidence': node.confidence_score
                })
        
        # Sort by date (would need proper date parsing)
        return sorted(timeline, key=lambda x: x['date'])
    
    def _find_conflicts(self, nodes: List[DocumentNode], 
                       relationships: List[DocumentRelationship]) -> List[Dict[str, Any]]:
        """Find conflicts between documents"""
        conflicts = []
        
        for rel in relationships:
            if rel.relationship_type == RelationshipType.CONTRADICTS:
                source_node = next(n for n in nodes if n.doc_id == rel.source_doc_id)
                target_node = next(n for n in nodes if n.doc_id == rel.target_doc_id)
                
                conflicts.append({
                    'type': 'metric_conflict',
                    'source_doc': rel.source_doc_id,
                    'target_doc': rel.target_doc_id,
                    'evidence': rel.evidence,
                    'confidence': rel.confidence,
                    'resolution_hint': self._suggest_conflict_resolution(
                        source_node, target_node, rel.evidence
                    )
                })
        
        return conflicts
    
    def _suggest_conflict_resolution(self, source_node: DocumentNode, 
                                   target_node: DocumentNode, 
                                   evidence: List[str]) -> str:
        """Suggest how to resolve a conflict"""
        # Simple heuristic based on confidence and recency
        if source_node.confidence_score > target_node.confidence_score:
            return f"Prefer data from {source_node.doc_id} (higher confidence)"
        elif source_node.extraction_date > target_node.extraction_date:
            return f"Prefer data from {source_node.doc_id} (more recent)"
        else:
            return "Manual review recommended"
    
    def _generate_insights(self, nodes: List[DocumentNode], 
                         relationships: List[DocumentRelationship],
                         clusters: List[ContentCluster]) -> List[Dict[str, Any]]:
        """Generate insights from synthesis"""
        insights = []
        
        # Insight: Document coverage
        doc_types = Counter(node.doc_type.value for node in nodes)
        insights.append({
            'type': 'document_coverage',
            'description': 'Document type distribution',
            'data': dict(doc_types),
            'importance': 0.5
        })
        
        # Insight: Key entities
        entity_counts = Counter()
        for node in nodes:
            entity_counts.update(node.entities)
        
        top_entities = entity_counts.most_common(5)
        if top_entities:
            insights.append({
                'type': 'key_entities',
                'description': 'Most frequently mentioned entities',
                'data': dict(top_entities),
                'importance': 0.8
            })
        
        # Insight: Topic trends
        topic_counts = Counter()
        for node in nodes:
            topic_counts.update(node.topics)
        
        if topic_counts:
            insights.append({
                'type': 'topic_distribution',
                'description': 'Main topics across documents',
                'data': dict(topic_counts),
                'importance': 0.7
            })
        
        # Insight: Relationship patterns
        rel_types = Counter(rel.relationship_type.value for rel in relationships)
        if rel_types:
            insights.append({
                'type': 'relationship_patterns',
                'description': 'Types of relationships found',
                'data': dict(rel_types),
                'importance': 0.6
            })
        
        # Insight: Cluster themes
        if clusters:
            cluster_themes = [cluster.theme for cluster in clusters]
            insights.append({
                'type': 'content_themes',
                'description': 'Major content themes identified',
                'data': cluster_themes,
                'importance': 0.9
            })
        
        return sorted(insights, key=lambda x: x['importance'], reverse=True)