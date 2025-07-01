"""
Entity Relationship Mapper for extracting entities and analyzing relationship networks.

This module provides comprehensive entity extraction, relationship detection, and network
analysis capabilities. It integrates with the synthesis engine to build knowledge graphs
from document collections.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Set, Tuple, Optional, Any, Union
from collections import defaultdict, Counter
import re
import logging
from datetime import datetime
import networkx as nx
from scipy.spatial.distance import cosine
import numpy as np

from synthesis_engine import SynthesisEngine, DocumentNode

# Configure logging
logger = logging.getLogger(__name__)


class EntityType(Enum):
    """Types of entities that can be extracted."""
    COMPANY = auto()
    PERSON = auto()
    PRODUCT = auto()
    LOCATION = auto()
    FINANCIAL_METRIC = auto()
    DATE = auto()
    TECHNOLOGY = auto()


class RelationType(Enum):
    """Types of relationships between entities."""
    OWNS = auto()
    WORKS_FOR = auto()
    COMPETES_WITH = auto()
    PARTNERS_WITH = auto()
    LOCATED_IN = auto()
    PRODUCES = auto()
    USES = auto()


@dataclass
class Entity:
    """Represents an extracted entity with its properties."""
    name: str
    type: EntityType
    aliases: Set[str] = field(default_factory=set)
    occurrences: List[Dict[str, Any]] = field(default_factory=list)
    documents: Set[str] = field(default_factory=set)
    attributes: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    
    def __hash__(self):
        return hash((self.name, self.type))
    
    def __eq__(self, other):
        if not isinstance(other, Entity):
            return False
        return self.name == other.name and self.type == other.type


@dataclass
class Relationship:
    """Represents a relationship between two entities."""
    source_entity: Entity
    target_entity: Entity
    type: RelationType
    strength: float = 1.0
    contexts: List[str] = field(default_factory=list)
    document_ids: Set[str] = field(default_factory=set)
    
    def __hash__(self):
        return hash((self.source_entity, self.target_entity, self.type))


@dataclass
class NetworkNode:
    """Represents a node in the entity network with computed metrics."""
    entity: Entity
    centrality: float = 0.0
    betweenness: float = 0.0
    degree: int = 0
    influence_score: float = 0.0


class EntityRelationshipMapper:
    """
    Maps entities and their relationships from document collections.
    
    This class provides comprehensive entity extraction, relationship detection,
    and network analysis capabilities for building knowledge graphs.
    """
    
    def __init__(self, synthesis_engine: SynthesisEngine):
        """
        Initialize the entity relationship mapper.
        
        Args:
            synthesis_engine: Instance of SynthesisEngine for document processing
        """
        self.synthesis_engine = synthesis_engine
        self.entities: Dict[str, Entity] = {}
        self.relationships: Set[Relationship] = set()
        self.network_graph: Optional[nx.Graph] = None
        
        # Compile regex patterns for entity extraction
        self._compile_patterns()
        
    def _compile_patterns(self):
        """Compile regex patterns for entity extraction."""
        # Company patterns
        self.company_suffixes = r'\b(?:Inc|Corp|Corporation|LLC|Ltd|Limited|Company|Co|Group|Holdings|Partners|LP|LLP|SA|AG|GmbH|PLC)\b\.?'
        self.company_pattern = re.compile(
            rf'([A-Z][A-Za-z0-9\s&\'-]{{1,50}}\s*{self.company_suffixes})',
            re.IGNORECASE
        )
        
        # Financial metrics patterns
        self.currency_pattern = re.compile(
            r'\$?\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?(?:\s*(?:million|billion|thousand|M|B|K))?',
            re.IGNORECASE
        )
        self.percentage_pattern = re.compile(r'\d+(?:\.\d+)?%')
        self.ratio_pattern = re.compile(r'\b\d+(?:\.\d+)?x\b|\b\d+:\d+\b')
        
        # Person patterns (simple title + name)
        self.person_pattern = re.compile(
            r'\b(?:Mr\.|Ms\.|Mrs\.|Dr\.|Prof\.|CEO|CTO|CFO|President|Director|Manager)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}\b'
        )
        
        # Product/technology patterns
        self.version_pattern = re.compile(
            r'\b[A-Za-z0-9\s\-]+\s+(?:v|version|release)?\s*\d+(?:\.\d+)*\b',
            re.IGNORECASE
        )
        
        # Date patterns
        self.date_pattern = re.compile(
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b',
            re.IGNORECASE
        )
        
    def extract_entities(self, document_nodes: List[DocumentNode], 
                        entity_types: Optional[List[EntityType]] = None) -> Dict[str, Entity]:
        """
        Extract entities from document nodes.
        
        Args:
            document_nodes: List of document nodes to process
            entity_types: Optional list of entity types to extract (None = all types)
            
        Returns:
            Dictionary mapping entity names to Entity objects
        """
        entity_types = entity_types or list(EntityType)
        
        for node in document_nodes:
            content = node.content
            doc_id = node.metadata.get('document_id', '')
            
            # Extract entities by type
            if EntityType.COMPANY in entity_types:
                self._extract_company_entities(content, doc_id)
            
            if EntityType.PERSON in entity_types:
                self._extract_people_entities(content, doc_id)
            
            if EntityType.PRODUCT in entity_types:
                self._extract_product_entities(content, doc_id)
            
            if EntityType.FINANCIAL_METRIC in entity_types:
                self._extract_financial_entities(content, doc_id)
            
            if EntityType.DATE in entity_types:
                self._extract_date_entities(content, doc_id)
        
        # Merge duplicate entities
        self.entities = self.merge_duplicate_entities(self.entities)
        
        logger.info(f"Extracted {len(self.entities)} unique entities")
        return self.entities
    
    def _extract_company_entities(self, content: str, doc_id: str) -> None:
        """Extract company entities with subsidiary/acquisition detection."""
        matches = self.company_pattern.findall(content)
        
        for match in matches:
            company_name = match.strip()
            normalized_name = self._normalize_entity_name(company_name)
            
            if normalized_name not in self.entities:
                entity = Entity(
                    name=normalized_name,
                    type=EntityType.COMPANY,
                    aliases={company_name}
                )
                self.entities[normalized_name] = entity
            else:
                entity = self.entities[normalized_name]
                entity.aliases.add(company_name)
            
            # Record occurrence
            entity.occurrences.append({
                'document_id': doc_id,
                'context': self._extract_context(content, company_name),
                'position': content.find(company_name)
            })
            entity.documents.add(doc_id)
            
            # Check for subsidiary relationships
            subsidiary_patterns = [
                rf'{company_name}\s+(?:subsidiary|division|unit)',
                rf'(?:subsidiary|division|unit)\s+of\s+{company_name}'
            ]
            for pattern in subsidiary_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    entity.attributes['has_subsidiaries'] = True
    
    def _extract_financial_entities(self, content: str, doc_id: str) -> None:
        """Extract financial metrics, amounts, and ratios."""
        # Extract currency amounts
        currency_matches = self.currency_pattern.findall(content)
        for match in currency_matches:
            entity = Entity(
                name=match,
                type=EntityType.FINANCIAL_METRIC,
                attributes={'metric_type': 'currency'}
            )
            entity.documents.add(doc_id)
            entity.occurrences.append({
                'document_id': doc_id,
                'context': self._extract_context(content, match)
            })
            self.entities[match] = entity
        
        # Extract percentages
        percentage_matches = self.percentage_pattern.findall(content)
        for match in percentage_matches:
            entity = Entity(
                name=match,
                type=EntityType.FINANCIAL_METRIC,
                attributes={'metric_type': 'percentage'}
            )
            entity.documents.add(doc_id)
            self.entities[match] = entity
    
    def _extract_people_entities(self, content: str, doc_id: str) -> None:
        """Extract people entities with role/title extraction."""
        matches = self.person_pattern.findall(content)
        
        for match in matches:
            person_name = match.strip()
            # Extract title if present
            title_match = re.match(r'((?:Mr\.|Ms\.|Mrs\.|Dr\.|Prof\.|CEO|CTO|CFO|President|Director|Manager))\s+(.+)', person_name)
            
            if title_match:
                title, name = title_match.groups()
                normalized_name = self._normalize_entity_name(name)
            else:
                normalized_name = self._normalize_entity_name(person_name)
                title = None
            
            if normalized_name not in self.entities:
                entity = Entity(
                    name=normalized_name,
                    type=EntityType.PERSON,
                    aliases={person_name}
                )
                if title:
                    entity.attributes['title'] = title
                self.entities[normalized_name] = entity
            else:
                entity = self.entities[normalized_name]
                entity.aliases.add(person_name)
            
            entity.occurrences.append({
                'document_id': doc_id,
                'context': self._extract_context(content, person_name)
            })
            entity.documents.add(doc_id)
    
    def _extract_product_entities(self, content: str, doc_id: str) -> None:
        """Extract product entities with version/model detection."""
        # Look for capitalized product names followed by version numbers
        version_matches = self.version_pattern.findall(content)
        
        for match in version_matches:
            product_name = match.strip()
            normalized_name = self._normalize_entity_name(product_name)
            
            if normalized_name not in self.entities:
                entity = Entity(
                    name=normalized_name,
                    type=EntityType.PRODUCT,
                    aliases={product_name}
                )
                # Extract version if present
                version_match = re.search(r'(\d+(?:\.\d+)*)', product_name)
                if version_match:
                    entity.attributes['version'] = version_match.group(1)
                
                self.entities[normalized_name] = entity
            else:
                entity = self.entities[normalized_name]
                entity.aliases.add(product_name)
            
            entity.documents.add(doc_id)
    
    def _extract_date_entities(self, content: str, doc_id: str) -> None:
        """Extract date entities."""
        matches = self.date_pattern.findall(content)
        
        for match in matches:
            date_str = match.strip()
            entity = Entity(
                name=date_str,
                type=EntityType.DATE
            )
            entity.documents.add(doc_id)
            entity.occurrences.append({
                'document_id': doc_id,
                'context': self._extract_context(content, date_str)
            })
            self.entities[date_str] = entity
    
    def identify_relationships(self, entities: Dict[str, Entity], 
                             documents: List[DocumentNode]) -> Set[Relationship]:
        """
        Identify relationships between entities.
        
        Args:
            entities: Dictionary of extracted entities
            documents: List of document nodes
            
        Returns:
            Set of identified relationships
        """
        self.relationships.clear()
        
        for doc in documents:
            content = doc.content
            doc_id = doc.metadata.get('document_id', '')
            
            # Get entities mentioned in this document
            doc_entities = [e for e in entities.values() if doc_id in e.documents]
            
            # Detect various relationship types
            self._detect_ownership_relationships(doc_entities, content, doc_id)
            self._detect_competitive_relationships(doc_entities, content, doc_id)
            self._detect_partnership_relationships(doc_entities, content, doc_id)
            self._detect_employment_relationships(doc_entities, content, doc_id)
            
        # Infer implicit relationships
        self._infer_implicit_relationships(entities, documents)
        
        logger.info(f"Identified {len(self.relationships)} relationships")
        return self.relationships
    
    def _detect_ownership_relationships(self, entities: List[Entity], 
                                      content: str, doc_id: str) -> None:
        """Detect ownership relationships between entities."""
        ownership_patterns = [
            r'{0}\s+(?:owns?|acquired?|purchased?|bought)\s+{1}',
            r'{1}\s+(?:owned by|acquired by|subsidiary of)\s+{0}',
            r'{0}(?:\'s|\s+)(?:acquisition of|purchase of)\s+{1}'
        ]
        
        companies = [e for e in entities if e.type == EntityType.COMPANY]
        
        for i, company1 in enumerate(companies):
            for company2 in companies[i+1:]:
                for pattern in ownership_patterns:
                    # Check both directions
                    for c1_name in [company1.name] + list(company1.aliases):
                        for c2_name in [company2.name] + list(company2.aliases):
                            regex = pattern.format(re.escape(c1_name), re.escape(c2_name))
                            if re.search(regex, content, re.IGNORECASE):
                                rel = Relationship(
                                    source_entity=company1,
                                    target_entity=company2,
                                    type=RelationType.OWNS,
                                    contexts=[self._extract_context(content, c1_name)]
                                )
                                rel.document_ids.add(doc_id)
                                self.relationships.add(rel)
    
    def _detect_competitive_relationships(self, entities: List[Entity], 
                                        content: str, doc_id: str) -> None:
        """Detect competitive relationships between entities."""
        competition_patterns = [
            r'{0}\s+(?:competes with|competing with|competitor of|rivals?)\s+{1}',
            r'{0}\s+and\s+{1}\s+(?:compete|are competitors|are rivals)',
            r'(?:competition|rivalry)\s+between\s+{0}\s+and\s+{1}'
        ]
        
        companies = [e for e in entities if e.type == EntityType.COMPANY]
        
        for i, company1 in enumerate(companies):
            for company2 in companies[i+1:]:
                for pattern in competition_patterns:
                    for c1_name in [company1.name] + list(company1.aliases):
                        for c2_name in [company2.name] + list(company2.aliases):
                            regex = pattern.format(re.escape(c1_name), re.escape(c2_name))
                            if re.search(regex, content, re.IGNORECASE):
                                # Competition is bidirectional
                                rel1 = Relationship(
                                    source_entity=company1,
                                    target_entity=company2,
                                    type=RelationType.COMPETES_WITH
                                )
                                rel1.document_ids.add(doc_id)
                                self.relationships.add(rel1)
                                
                                rel2 = Relationship(
                                    source_entity=company2,
                                    target_entity=company1,
                                    type=RelationType.COMPETES_WITH
                                )
                                rel2.document_ids.add(doc_id)
                                self.relationships.add(rel2)
    
    def _detect_partnership_relationships(self, entities: List[Entity], 
                                        content: str, doc_id: str) -> None:
        """Detect partnership relationships between entities."""
        partnership_patterns = [
            r'{0}\s+(?:partners? with|partnered with|partnership with|collaborates? with)\s+{1}',
            r'(?:partnership|collaboration|alliance)\s+between\s+{0}\s+and\s+{1}',
            r'{0}\s+and\s+{1}\s+(?:partner|collaborate|form alliance)'
        ]
        
        companies = [e for e in entities if e.type == EntityType.COMPANY]
        
        for i, company1 in enumerate(companies):
            for company2 in companies[i+1:]:
                for pattern in partnership_patterns:
                    for c1_name in [company1.name] + list(company1.aliases):
                        for c2_name in [company2.name] + list(company2.aliases):
                            regex = pattern.format(re.escape(c1_name), re.escape(c2_name))
                            if re.search(regex, content, re.IGNORECASE):
                                # Partnership is bidirectional
                                rel1 = Relationship(
                                    source_entity=company1,
                                    target_entity=company2,
                                    type=RelationType.PARTNERS_WITH,
                                    contexts=[self._extract_context(content, c1_name)]
                                )
                                rel1.document_ids.add(doc_id)
                                self.relationships.add(rel1)
                                
                                rel2 = Relationship(
                                    source_entity=company2,
                                    target_entity=company1,
                                    type=RelationType.PARTNERS_WITH,
                                    contexts=[self._extract_context(content, c2_name)]
                                )
                                rel2.document_ids.add(doc_id)
                                self.relationships.add(rel2)
    
    def _detect_employment_relationships(self, entities: List[Entity], 
                                       content: str, doc_id: str) -> None:
        """Detect employment relationships between people and companies."""
        employment_patterns = [
            r'{0}\s+(?:works? for|employed by|joins?|joined)\s+{1}',
            r'{0},?\s+(?:CEO|CTO|CFO|President|Director|Manager)\s+(?:of|at)\s+{1}',
            r'{1}(?:\'s)?\s+(?:CEO|CTO|CFO|President|Director|Manager),?\s+{0}'
        ]
        
        people = [e for e in entities if e.type == EntityType.PERSON]
        companies = [e for e in entities if e.type == EntityType.COMPANY]
        
        for person in people:
            for company in companies:
                for pattern in employment_patterns:
                    for p_name in [person.name] + list(person.aliases):
                        for c_name in [company.name] + list(company.aliases):
                            regex = pattern.format(re.escape(p_name), re.escape(c_name))
                            if re.search(regex, content, re.IGNORECASE):
                                rel = Relationship(
                                    source_entity=person,
                                    target_entity=company,
                                    type=RelationType.WORKS_FOR,
                                    contexts=[self._extract_context(content, p_name)]
                                )
                                rel.document_ids.add(doc_id)
                                self.relationships.add(rel)
    
    def _infer_implicit_relationships(self, entities: Dict[str, Entity], 
                                    documents: List[DocumentNode]) -> None:
        """Infer implicit relationships from entity co-occurrence."""
        # Calculate co-occurrence matrix
        entity_list = list(entities.values())
        cooccurrence = defaultdict(int)
        
        for doc in documents:
            doc_id = doc.metadata.get('document_id', '')
            doc_entities = [e for e in entity_list if doc_id in e.documents]
            
            # Count co-occurrences
            for i, e1 in enumerate(doc_entities):
                for e2 in doc_entities[i+1:]:
                    key = tuple(sorted([e1.name, e2.name]))
                    cooccurrence[key] += 1
        
        # Create relationships for strong co-occurrences
        threshold = 3  # Minimum co-occurrences
        for (e1_name, e2_name), count in cooccurrence.items():
            if count >= threshold:
                e1 = entities[e1_name]
                e2 = entities[e2_name]
                
                # Calculate relationship strength based on co-occurrence
                strength = min(1.0, count / 10.0)
                
                # Don't create implicit relationships if explicit ones exist
                existing = any(
                    (r.source_entity == e1 and r.target_entity == e2) or
                    (r.source_entity == e2 and r.target_entity == e1)
                    for r in self.relationships
                )
                
                if not existing and e1.type == e2.type == EntityType.COMPANY:
                    # Infer potential partnership or competition
                    rel = Relationship(
                        source_entity=e1,
                        target_entity=e2,
                        type=RelationType.PARTNERS_WITH,
                        strength=strength,
                        contexts=[f"Entities co-occur in {count} documents"]
                    )
                    self.relationships.add(rel)
    
    def build_network_graph(self, entities: Dict[str, Entity], 
                          relationships: Set[Relationship]) -> nx.Graph:
        """
        Build a network graph from entities and relationships.
        
        Args:
            entities: Dictionary of entities
            relationships: Set of relationships
            
        Returns:
            NetworkX graph object
        """
        # Create directed graph
        self.network_graph = nx.DiGraph()
        
        # Add nodes
        for entity in entities.values():
            self.network_graph.add_node(
                entity.name,
                entity=entity,
                type=entity.type.name,
                documents=len(entity.documents),
                occurrences=len(entity.occurrences)
            )
        
        # Add edges
        for rel in relationships:
            self.network_graph.add_edge(
                rel.source_entity.name,
                rel.target_entity.name,
                relationship=rel,
                type=rel.type.name,
                weight=rel.strength
            )
        
        logger.info(f"Built network graph with {self.network_graph.number_of_nodes()} nodes "
                   f"and {self.network_graph.number_of_edges()} edges")
        
        return self.network_graph
    
    def analyze_network_metrics(self, graph: nx.Graph) -> Dict[str, NetworkNode]:
        """
        Analyze network metrics for centrality and influence.
        
        Args:
            graph: NetworkX graph to analyze
            
        Returns:
            Dictionary mapping entity names to NetworkNode objects with metrics
        """
        network_nodes = {}
        
        # Calculate various centrality measures
        degree_centrality = nx.degree_centrality(graph)
        betweenness_centrality = nx.betweenness_centrality(graph)
        
        # Calculate PageRank for influence
        try:
            pagerank = nx.pagerank(graph, weight='weight')
        except:
            pagerank = {node: 0.0 for node in graph.nodes()}
        
        # Create NetworkNode objects with metrics
        for node in graph.nodes():
            entity = graph.nodes[node]['entity']
            
            network_node = NetworkNode(
                entity=entity,
                centrality=degree_centrality.get(node, 0.0),
                betweenness=betweenness_centrality.get(node, 0.0),
                degree=graph.degree(node),
                influence_score=pagerank.get(node, 0.0)
            )
            
            network_nodes[node] = network_node
        
        return network_nodes
    
    def merge_duplicate_entities(self, entities: Dict[str, Entity], 
                               similarity_threshold: float = 0.85) -> Dict[str, Entity]:
        """
        Merge duplicate entities based on similarity.
        
        Args:
            entities: Dictionary of entities to merge
            similarity_threshold: Threshold for considering entities as duplicates
            
        Returns:
            Dictionary of merged entities
        """
        merged = {}
        entity_list = list(entities.values())
        merged_indices = set()
        
        for i, entity1 in enumerate(entity_list):
            if i in merged_indices:
                continue
            
            # Start with current entity
            merged_entity = Entity(
                name=entity1.name,
                type=entity1.type,
                aliases=entity1.aliases.copy(),
                occurrences=entity1.occurrences.copy(),
                documents=entity1.documents.copy(),
                attributes=entity1.attributes.copy(),
                confidence=entity1.confidence
            )
            
            # Find similar entities
            for j, entity2 in enumerate(entity_list[i+1:], i+1):
                if j in merged_indices or entity1.type != entity2.type:
                    continue
                
                similarity = self._calculate_entity_similarity(entity1, entity2)
                if similarity >= similarity_threshold:
                    # Merge entity2 into merged_entity
                    merged_entity.aliases.update(entity2.aliases)
                    merged_entity.aliases.add(entity2.name)
                    merged_entity.occurrences.extend(entity2.occurrences)
                    merged_entity.documents.update(entity2.documents)
                    merged_entity.attributes.update(entity2.attributes)
                    merged_entity.confidence = max(merged_entity.confidence, entity2.confidence)
                    merged_indices.add(j)
            
            merged[merged_entity.name] = merged_entity
        
        logger.info(f"Merged {len(entity_list) - len(merged)} duplicate entities")
        return merged
    
    def get_entity_timeline(self, entity_name: str) -> List[Dict[str, Any]]:
        """
        Get temporal analysis of an entity's occurrences.
        
        Args:
            entity_name: Name of the entity to analyze
            
        Returns:
            List of timeline events for the entity
        """
        if entity_name not in self.entities:
            return []
        
        entity = self.entities[entity_name]
        timeline = []
        
        # Extract dates from occurrences
        for occurrence in entity.occurrences:
            context = occurrence.get('context', '')
            doc_id = occurrence.get('document_id', '')
            
            # Find dates in context
            date_matches = self.date_pattern.findall(context)
            for date_str in date_matches:
                timeline.append({
                    'entity': entity_name,
                    'date': date_str,
                    'document_id': doc_id,
                    'context': context,
                    'event_type': self._infer_event_type(context)
                })
        
        # Sort by date (simple string sort for now)
        timeline.sort(key=lambda x: x['date'])
        
        return timeline
    
    def _calculate_entity_centrality(self, graph: nx.Graph, entity: Entity) -> float:
        """Calculate centrality score for an entity."""
        if entity.name not in graph:
            return 0.0
        
        # Combine multiple centrality measures
        degree_cent = nx.degree_centrality(graph).get(entity.name, 0.0)
        betweenness_cent = nx.betweenness_centrality(graph).get(entity.name, 0.0)
        
        # Weighted combination
        centrality = 0.7 * degree_cent + 0.3 * betweenness_cent
        return centrality
    
    def _identify_entity_clusters(self, graph: nx.Graph) -> List[Set[str]]:
        """Identify clusters of related entities."""
        # Convert to undirected for community detection
        undirected = graph.to_undirected()
        
        # Find connected components
        clusters = list(nx.connected_components(undirected))
        
        # Sort by size
        clusters.sort(key=len, reverse=True)
        
        return clusters
    
    def _find_shortest_paths(self, graph: nx.Graph, entity1: str, entity2: str) -> List[List[str]]:
        """Find shortest paths between two entities."""
        if entity1 not in graph or entity2 not in graph:
            return []
        
        try:
            # Find all shortest paths
            paths = list(nx.all_shortest_paths(graph, entity1, entity2))
            return paths
        except nx.NetworkXNoPath:
            return []
    
    def _calculate_influence_propagation(self, graph: nx.Graph, entity: str) -> Dict[str, float]:
        """Calculate how influence propagates from an entity."""
        if entity not in graph:
            return {}
        
        # Use personalized PageRank for influence propagation
        personalization = {node: 0.0 for node in graph.nodes()}
        personalization[entity] = 1.0
        
        try:
            influence = nx.pagerank(graph, personalization=personalization, weight='weight')
            # Remove self-influence
            influence.pop(entity, None)
            return influence
        except:
            return {}
    
    def _normalize_entity_name(self, name: str) -> str:
        """Normalize entity name for consistency."""
        # Remove extra whitespace
        name = ' '.join(name.split())
        # Standardize case
        name = name.title()
        return name
    
    def _extract_context(self, content: str, entity_name: str, 
                        context_window: int = 100) -> str:
        """Extract context around an entity mention."""
        try:
            pos = content.lower().find(entity_name.lower())
            if pos == -1:
                return ""
            
            start = max(0, pos - context_window)
            end = min(len(content), pos + len(entity_name) + context_window)
            
            context = content[start:end]
            # Clean up context
            if start > 0:
                context = "..." + context
            if end < len(content):
                context = context + "..."
                
            return context.strip()
        except Exception as e:
            logger.error(f"Error extracting context: {e}")
            return ""
    
    def _calculate_entity_similarity(self, entity1: Entity, entity2: Entity) -> float:
        """Calculate similarity between two entities."""
        if entity1.type != entity2.type:
            return 0.0
        
        # Name similarity
        name_sim = self._string_similarity(entity1.name, entity2.name)
        
        # Check aliases
        alias_sim = 0.0
        all_names1 = {entity1.name} | entity1.aliases
        all_names2 = {entity2.name} | entity2.aliases
        
        for n1 in all_names1:
            for n2 in all_names2:
                alias_sim = max(alias_sim, self._string_similarity(n1, n2))
        
        # Document overlap
        doc_overlap = len(entity1.documents & entity2.documents) / \
                     max(len(entity1.documents | entity2.documents), 1)
        
        # Weighted combination
        similarity = 0.5 * max(name_sim, alias_sim) + 0.5 * doc_overlap
        
        return similarity
    
    def _string_similarity(self, s1: str, s2: str) -> float:
        """Calculate string similarity using character-level comparison."""
        s1 = s1.lower()
        s2 = s2.lower()
        
        if s1 == s2:
            return 1.0
        
        # Check if one is substring of another
        if s1 in s2 or s2 in s1:
            return 0.9
        
        # Character-level similarity
        chars1 = Counter(s1)
        chars2 = Counter(s2)
        
        intersection = sum((chars1 & chars2).values())
        union = sum((chars1 | chars2).values())
        
        return intersection / union if union > 0 else 0.0
    
    def _infer_event_type(self, context: str) -> str:
        """Infer the type of event from context."""
        context_lower = context.lower()
        
        if any(word in context_lower for word in ['acquired', 'acquisition', 'bought', 'purchased']):
            return 'acquisition'
        elif any(word in context_lower for word in ['partnership', 'partner', 'collaborate']):
            return 'partnership'
        elif any(word in context_lower for word in ['launched', 'released', 'introduced']):
            return 'product_launch'
        elif any(word in context_lower for word in ['appointed', 'hired', 'joined']):
            return 'appointment'
        elif any(word in context_lower for word in ['earnings', 'revenue', 'profit']):
            return 'financial'
        else:
            return 'general'