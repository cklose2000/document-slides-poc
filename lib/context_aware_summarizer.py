"""
Context-Aware Summarization Component

Provides hierarchical summarization capabilities that integrate with the synthesis engine,
preserving source attribution and maintaining entity relationships during summarization.
"""

from typing import Dict, List, Any, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re
from collections import Counter, defaultdict
import hashlib

# Import from synthesis engine
from synthesis_engine import DocumentNode, DocumentType


class SummaryLevel(Enum):
    """Levels of summary detail"""
    BRIEF = "brief"  # 1-2 sentences
    STANDARD = "standard"  # 1-2 paragraphs
    DETAILED = "detailed"  # Multiple paragraphs with subsections


@dataclass
class KeyPoint:
    """Represents a key point extracted from content"""
    text: str
    importance: float
    source_context: str  # Surrounding context
    entities: Set[str] = field(default_factory=set)
    source_doc_id: Optional[str] = None
    position_weight: float = 1.0  # Based on position in document
    
    def __hash__(self):
        return hash(self.text)


@dataclass
class Summary:
    """Represents a summary with metadata"""
    content: str
    level: SummaryLevel
    source_ids: Set[str]  # Document IDs from synthesis engine
    key_points: List[KeyPoint]
    importance_score: float
    entities_preserved: Set[str] = field(default_factory=set)
    topics_covered: Set[str] = field(default_factory=set)
    timestamp: datetime = field(default_factory=datetime.now)
    word_count: int = 0
    
    def __post_init__(self):
        """Calculate word count after initialization"""
        self.word_count = len(self.content.split())


class ContextAwareSummarizer:
    """
    Hierarchical summarization with source attribution and entity preservation.
    Integrates with synthesis engine to maintain document relationships.
    """
    
    def __init__(self, synthesis_engine):
        """
        Initialize the summarizer with a synthesis engine instance.
        
        Args:
            synthesis_engine: Instance of SynthesisEngine for document relationships
        """
        self.synthesis_engine = synthesis_engine
        self.stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }
        
        # Content type patterns for specialized handling
        self.content_patterns = {
            'financial': {
                'keywords': ['revenue', 'profit', 'earnings', 'margin', 'growth', 'cost'],
                'patterns': [
                    r'\$[\d,]+(?:\.\d{2})?[MBK]?\b',
                    r'\b\d+(?:\.\d+)?%\b',
                    r'\b(?:Q[1-4]|FY)\s*\d{4}\b'
                ]
            },
            'narrative': {
                'keywords': ['strategy', 'plan', 'initiative', 'approach', 'goal'],
                'patterns': []
            },
            'list': {
                'keywords': [],
                'patterns': [
                    r'^\s*[\d\-•]\s+',
                    r'^\s*[a-zA-Z]\)\s+'
                ]
            }
        }
        
        # Summary templates for different levels
        self.summary_templates = {
            SummaryLevel.BRIEF: {
                'max_sentences': 2,
                'max_words': 50
            },
            SummaryLevel.STANDARD: {
                'max_sentences': 8,
                'max_words': 200
            },
            SummaryLevel.DETAILED: {
                'max_sentences': 20,
                'max_words': 500
            }
        }
    
    def summarize_document(self, document_node: DocumentNode, 
                          level: Union[str, SummaryLevel] = 'standard') -> Summary:
        """
        Summarize a single document while preserving key information.
        
        Args:
            document_node: DocumentNode from synthesis engine
            level: Summary level (brief, standard, or detailed)
            
        Returns:
            Summary object with preserved entities and source attribution
        """
        if isinstance(level, str):
            level = SummaryLevel(level)
        
        # Extract content from document node
        content = self._extract_content_from_node(document_node)
        
        # Identify content type
        content_type = self._identify_content_type(content)
        
        # Extract key points
        key_points = self.extract_key_points(
            content, 
            num_points=self._get_num_points_for_level(level)
        )
        
        # Generate summary based on level and content type
        summary_content = self._generate_summary(
            content, 
            key_points, 
            level, 
            content_type
        )
        
        # Calculate importance score
        importance_score = self._calculate_importance_score(
            summary_content, 
            document_node
        )
        
        # Extract entities from summary
        summary_entities = self._extract_entities_from_summary(summary_content)
        
        # Ensure important entities from document are preserved
        preserved_entities = self._preserve_key_entities(
            document_node.entities, 
            summary_entities, 
            key_points
        )
        
        return Summary(
            content=summary_content,
            level=level,
            source_ids={document_node.doc_id},
            key_points=key_points,
            importance_score=importance_score,
            entities_preserved=preserved_entities,
            topics_covered=document_node.topics
        )
    
    def summarize_section(self, content: str, max_length: int = 500) -> str:
        """
        Summarize a section of content with length constraint.
        
        Args:
            content: Text content to summarize
            max_length: Maximum length in characters
            
        Returns:
            Summarized text
        """
        # Extract sentences
        sentences = self._extract_sentences(content)
        
        # Score sentences
        sentence_scores = self._score_sentences(sentences)
        
        # Select top sentences within length constraint
        summary_sentences = []
        current_length = 0
        
        for sentence, score in sorted(sentence_scores.items(), 
                                    key=lambda x: x[1], reverse=True):
            sentence_length = len(sentence)
            if current_length + sentence_length <= max_length:
                summary_sentences.append(sentence)
                current_length += sentence_length
            
            if current_length >= max_length * 0.9:  # Allow 90% utilization
                break
        
        # Reorder sentences to maintain flow
        summary_sentences = self._reorder_sentences(summary_sentences, sentences)
        
        return ' '.join(summary_sentences)
    
    def extract_key_points(self, content: str, num_points: int = 5) -> List[KeyPoint]:
        """
        Extract key points from content.
        
        Args:
            content: Text content to analyze
            num_points: Number of key points to extract
            
        Returns:
            List of KeyPoint objects
        """
        # Extract sentences
        sentences = self._extract_sentences(content)
        
        # Score sentences for importance
        sentence_scores = self._score_sentences(sentences)
        
        # Extract entities from content
        entities = self._extract_entities_from_summary(content)
        
        # Create key points from top sentences
        key_points = []
        for sentence, score in sorted(sentence_scores.items(), 
                                    key=lambda x: x[1], reverse=True)[:num_points]:
            # Extract entities in this sentence
            sentence_entities = {e for e in entities if e.lower() in sentence.lower()}
            
            # Get context (previous and next sentence if available)
            context = self._get_sentence_context(sentence, sentences)
            
            # Calculate position weight
            position = sentences.index(sentence) if sentence in sentences else len(sentences)
            position_weight = 1.0 - (position / len(sentences)) * 0.3  # Early sentences weighted higher
            
            key_point = KeyPoint(
                text=sentence,
                importance=score,
                source_context=context,
                entities=sentence_entities,
                position_weight=position_weight
            )
            key_points.append(key_point)
        
        return key_points
    
    def consolidate_summaries(self, summaries: List[Summary], 
                            preserve_sources: bool = True) -> Summary:
        """
        Consolidate multiple summaries into a unified summary.
        
        Args:
            summaries: List of Summary objects to consolidate
            preserve_sources: Whether to preserve source attribution
            
        Returns:
            Consolidated Summary object
        """
        if not summaries:
            raise ValueError("No summaries provided for consolidation")
        
        # Aggregate all key points
        all_key_points = []
        all_source_ids = set()
        all_entities = set()
        all_topics = set()
        
        for summary in summaries:
            all_key_points.extend(summary.key_points)
            all_source_ids.update(summary.source_ids)
            all_entities.update(summary.entities_preserved)
            all_topics.update(summary.topics_covered)
        
        # Merge similar key points
        merged_points = self._merge_similar_points(all_key_points)
        
        # Score and select top points
        top_points = sorted(merged_points, 
                          key=lambda p: p.importance * p.position_weight, 
                          reverse=True)[:10]
        
        # Generate consolidated content
        if preserve_sources:
            consolidated_content = self._generate_sourced_summary(top_points, all_source_ids)
        else:
            consolidated_content = self._generate_unified_summary(top_points)
        
        # Calculate overall importance
        avg_importance = sum(s.importance_score for s in summaries) / len(summaries)
        
        return Summary(
            content=consolidated_content,
            level=SummaryLevel.STANDARD,
            source_ids=all_source_ids,
            key_points=top_points,
            importance_score=avg_importance,
            entities_preserved=all_entities,
            topics_covered=all_topics
        )
    
    def generate_hierarchical_summary(self, document_node: DocumentNode) -> Dict[str, Summary]:
        """
        Generate multi-level summaries for a document.
        
        Args:
            document_node: DocumentNode to summarize
            
        Returns:
            Dictionary mapping summary levels to Summary objects
        """
        hierarchical_summaries = {}
        
        # Generate summaries at each level
        for level in SummaryLevel:
            summary = self.summarize_document(document_node, level)
            hierarchical_summaries[level.value] = summary
        
        # Add relationships between levels
        self._add_summary_relationships(hierarchical_summaries)
        
        return hierarchical_summaries
    
    def _calculate_importance_score(self, text: str, context: Any) -> float:
        """
        Calculate importance score for text based on various factors.
        
        Args:
            text: Text to score
            context: Additional context (e.g., DocumentNode)
            
        Returns:
            Importance score between 0 and 1
        """
        score = 0.0
        
        # Factor 1: Length (normalized)
        word_count = len(text.split())
        length_score = min(word_count / 100, 1.0) * 0.2
        score += length_score
        
        # Factor 2: Entity density
        entities = self._extract_entities_from_summary(text)
        entity_density = len(entities) / max(word_count, 1)
        entity_score = min(entity_density * 10, 1.0) * 0.3
        score += entity_score
        
        # Factor 3: Numeric data presence
        numeric_pattern = r'\b\d+(?:\.\d+)?(?:%|[MBK]|\s*(?:million|billion))?\b'
        numeric_matches = re.findall(numeric_pattern, text)
        numeric_score = min(len(numeric_matches) / 5, 1.0) * 0.2
        score += numeric_score
        
        # Factor 4: Document confidence (if available)
        if isinstance(context, DocumentNode):
            score += context.confidence_score * 0.2
        
        # Factor 5: Topic relevance
        important_topics = {'growth', 'revenue', 'profit', 'strategy', 'risk'}
        topic_matches = sum(1 for topic in important_topics if topic in text.lower())
        topic_score = min(topic_matches / 3, 1.0) * 0.1
        score += topic_score
        
        return min(score, 1.0)
    
    def _extract_entities_from_summary(self, summary_text: str) -> Set[str]:
        """
        Extract entities from summary text.
        
        Args:
            summary_text: Text to extract entities from
            
        Returns:
            Set of identified entities
        """
        entities = set()
        
        # Use patterns from synthesis engine's graph builder
        entity_patterns = {
            'company': r'\b[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*(?:\s+(?:Inc|Corp|LLC|Ltd|Company|Co)\.?)\b',
            'person': r'\b(?:Mr|Ms|Mrs|Dr|Prof)\.?\s+[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*\b',
            'monetary': r'\$[\d,]+(?:\.\d{2})?[MBK]?\b',
            'percentage': r'\b\d+(?:\.\d+)?%\b',
            'product': r'\b[A-Z][A-Za-z]+(?:\s+[A-Z\d]+)*\s+(?:v\d+|Version|Edition)\b'
        }
        
        for entity_type, pattern in entity_patterns.items():
            matches = re.findall(pattern, summary_text)
            entities.update(matches)
        
        # Also extract capitalized phrases (potential entities)
        cap_phrases = re.findall(r'\b[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*\b', summary_text)
        entities.update(phrase for phrase in cap_phrases if len(phrase.split()) <= 3)
        
        return entities
    
    def _merge_similar_points(self, key_points: List[KeyPoint]) -> List[KeyPoint]:
        """
        Merge similar key points to avoid redundancy.
        
        Args:
            key_points: List of key points to merge
            
        Returns:
            List of merged key points
        """
        if not key_points:
            return []
        
        merged = []
        processed = set()
        
        for i, point1 in enumerate(key_points):
            if i in processed:
                continue
            
            # Find similar points
            similar_group = [point1]
            similar_indices = {i}
            
            for j, point2 in enumerate(key_points[i+1:], i+1):
                if j in processed:
                    continue
                
                similarity = self._calculate_text_similarity(point1.text, point2.text)
                if similarity > 0.7:  # Threshold for similarity
                    similar_group.append(point2)
                    similar_indices.add(j)
            
            # Merge similar points
            if len(similar_group) > 1:
                merged_point = self._merge_point_group(similar_group)
                merged.append(merged_point)
            else:
                merged.append(point1)
            
            processed.update(similar_indices)
        
        return merged
    
    # Helper methods
    
    def _extract_content_from_node(self, node: DocumentNode) -> str:
        """Extract text content from document node"""
        # This would integrate with actual document content
        # For now, create content from available metadata
        content_parts = []
        
        # Add entities as context
        if node.entities:
            content_parts.append(f"Key entities: {', '.join(list(node.entities)[:10])}")
        
        # Add topics
        if node.topics:
            content_parts.append(f"Topics covered: {', '.join(node.topics)}")
        
        # Add metrics
        if node.key_metrics:
            metrics_text = []
            for metric, value in node.key_metrics.items():
                metrics_text.append(f"{metric}: {value}")
            content_parts.append(f"Key metrics: {'; '.join(metrics_text)}")
        
        # Add time references
        if node.time_references:
            content_parts.append(f"Time period: {', '.join(list(node.time_references)[:5])}")
        
        return '\n'.join(content_parts)
    
    def _identify_content_type(self, content: str) -> str:
        """Identify the type of content for specialized handling"""
        content_lower = content.lower()
        
        # Check for financial content
        financial_score = sum(1 for kw in self.content_patterns['financial']['keywords'] 
                            if kw in content_lower)
        for pattern in self.content_patterns['financial']['patterns']:
            financial_score += len(re.findall(pattern, content))
        
        # Check for list format
        list_score = 0
        for pattern in self.content_patterns['list']['patterns']:
            list_score += len(re.findall(pattern, content, re.MULTILINE))
        
        # Determine primary type
        if financial_score > 5:
            return 'financial'
        elif list_score > 3:
            return 'list'
        else:
            return 'narrative'
    
    def _get_num_points_for_level(self, level: SummaryLevel) -> int:
        """Get appropriate number of key points for summary level"""
        return {
            SummaryLevel.BRIEF: 3,
            SummaryLevel.STANDARD: 5,
            SummaryLevel.DETAILED: 10
        }.get(level, 5)
    
    def _extract_sentences(self, text: str) -> List[str]:
        """Extract sentences from text"""
        # Simple sentence extraction - could be enhanced with NLTK
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
    
    def _score_sentences(self, sentences: List[str]) -> Dict[str, float]:
        """Score sentences based on importance"""
        # Calculate word frequencies
        word_freq = Counter()
        for sentence in sentences:
            words = [w.lower() for w in sentence.split() 
                    if w.lower() not in self.stopwords]
            word_freq.update(words)
        
        # Normalize frequencies
        max_freq = max(word_freq.values()) if word_freq else 1
        for word in word_freq:
            word_freq[word] = word_freq[word] / max_freq
        
        # Score sentences
        sentence_scores = {}
        for sentence in sentences:
            words = [w.lower() for w in sentence.split() 
                    if w.lower() not in self.stopwords]
            if words:
                score = sum(word_freq.get(word, 0) for word in words) / len(words)
                sentence_scores[sentence] = score
        
        return sentence_scores
    
    def _get_sentence_context(self, sentence: str, all_sentences: List[str]) -> str:
        """Get context for a sentence"""
        try:
            idx = all_sentences.index(sentence)
            context_parts = []
            
            if idx > 0:
                context_parts.append(all_sentences[idx-1])
            context_parts.append(sentence)
            if idx < len(all_sentences) - 1:
                context_parts.append(all_sentences[idx+1])
            
            return ' '.join(context_parts)
        except ValueError:
            return sentence
    
    def _reorder_sentences(self, selected: List[str], original: List[str]) -> List[str]:
        """Reorder selected sentences to maintain original flow"""
        # Get original positions
        positions = {}
        for sentence in selected:
            if sentence in original:
                positions[sentence] = original.index(sentence)
        
        # Sort by original position
        return sorted(selected, key=lambda s: positions.get(s, float('inf')))
    
    def _generate_summary(self, content: str, key_points: List[KeyPoint], 
                         level: SummaryLevel, content_type: str) -> str:
        """Generate summary based on parameters"""
        template = self.summary_templates[level]
        
        # Start with key points
        summary_parts = []
        
        # Add introduction if detailed
        if level == SummaryLevel.DETAILED:
            intro = self._generate_introduction(content, content_type)
            if intro:
                summary_parts.append(intro)
        
        # Add key points based on level constraints
        for i, point in enumerate(key_points):
            if i >= template['max_sentences']:
                break
            
            # Adjust point presentation based on level
            if level == SummaryLevel.BRIEF:
                # Shorten the point
                shortened = self._shorten_sentence(point.text, max_words=25)
                summary_parts.append(shortened)
            else:
                summary_parts.append(point.text)
        
        # Join and trim to word limit
        summary = ' '.join(summary_parts)
        words = summary.split()
        if len(words) > template['max_words']:
            summary = ' '.join(words[:template['max_words']]) + '...'
        
        return summary
    
    def _preserve_key_entities(self, doc_entities: Set[str], 
                              summary_entities: Set[str], 
                              key_points: List[KeyPoint]) -> Set[str]:
        """Ensure important entities are preserved in summary"""
        preserved = summary_entities.copy()
        
        # Add entities from key points
        for point in key_points:
            preserved.update(point.entities)
        
        # Add most frequent document entities if missing
        entity_freq = Counter()
        for point in key_points:
            entity_freq.update(point.entities)
        
        # Add top entities from document if not already included
        top_doc_entities = sorted(doc_entities, 
                                key=lambda e: entity_freq.get(e, 0), 
                                reverse=True)[:5]
        preserved.update(top_doc_entities)
        
        return preserved
    
    def _generate_sourced_summary(self, points: List[KeyPoint], 
                                source_ids: Set[str]) -> str:
        """Generate summary with source attribution"""
        summary_parts = []
        
        # Group points by source
        source_groups = defaultdict(list)
        for point in points:
            source = point.source_doc_id or 'unknown'
            source_groups[source].append(point)
        
        # Generate summary with attribution
        for source, source_points in source_groups.items():
            if source != 'unknown':
                summary_parts.append(f"From document {source}:")
            
            for point in source_points:
                summary_parts.append(f"- {point.text}")
        
        # Add source list at end
        if len(source_ids) > 1:
            summary_parts.append(f"\nSources: {', '.join(sorted(source_ids))}")
        
        return '\n'.join(summary_parts)
    
    def _generate_unified_summary(self, points: List[KeyPoint]) -> str:
        """Generate unified summary without source attribution"""
        # Group by topic/theme
        theme_groups = self._group_points_by_theme(points)
        
        summary_parts = []
        for theme, theme_points in theme_groups.items():
            # Add theme header for detailed summaries
            if len(theme_groups) > 1:
                summary_parts.append(f"\n{theme.title()}:")
            
            # Add points
            for point in theme_points:
                summary_parts.append(point.text)
        
        return ' '.join(summary_parts)
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        # Simple word overlap similarity
        words1 = set(w.lower() for w in text1.split() if w.lower() not in self.stopwords)
        words2 = set(w.lower() for w in text2.split() if w.lower() not in self.stopwords)
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _merge_point_group(self, similar_points: List[KeyPoint]) -> KeyPoint:
        """Merge a group of similar points"""
        # Use the highest scoring point as base
        base_point = max(similar_points, key=lambda p: p.importance * p.position_weight)
        
        # Aggregate entities
        all_entities = set()
        for point in similar_points:
            all_entities.update(point.entities)
        
        # Average importance
        avg_importance = sum(p.importance for p in similar_points) / len(similar_points)
        
        # Create merged point
        return KeyPoint(
            text=base_point.text,
            importance=avg_importance,
            source_context=base_point.source_context,
            entities=all_entities,
            source_doc_id=base_point.source_doc_id,
            position_weight=base_point.position_weight
        )
    
    def _shorten_sentence(self, sentence: str, max_words: int) -> str:
        """Shorten a sentence to max words while preserving meaning"""
        words = sentence.split()
        if len(words) <= max_words:
            return sentence
        
        # Try to find a natural break point
        shortened = words[:max_words]
        
        # Remove incomplete phrases at the end
        connectors = {'and', 'or', 'but', 'with', 'to', 'for', 'of'}
        while shortened and shortened[-1].lower() in connectors:
            shortened.pop()
        
        return ' '.join(shortened) + '...'
    
    def _generate_introduction(self, content: str, content_type: str) -> Optional[str]:
        """Generate introduction for detailed summary"""
        if content_type == 'financial':
            return "This document contains financial information including key metrics and performance indicators."
        elif content_type == 'list':
            return "The following key points have been identified:"
        else:
            return "This summary captures the main themes and insights from the document."
    
    def _group_points_by_theme(self, points: List[KeyPoint]) -> Dict[str, List[KeyPoint]]:
        """Group points by common themes"""
        theme_groups = defaultdict(list)
        
        # Simple keyword-based grouping
        theme_keywords = {
            'financial': ['revenue', 'profit', 'cost', 'margin', 'earnings'],
            'strategic': ['strategy', 'plan', 'initiative', 'goal', 'objective'],
            'operational': ['operation', 'process', 'efficiency', 'performance'],
            'market': ['market', 'competition', 'customer', 'share', 'position'],
            'risk': ['risk', 'threat', 'challenge', 'mitigation', 'compliance']
        }
        
        for point in points:
            point_lower = point.text.lower()
            assigned = False
            
            for theme, keywords in theme_keywords.items():
                if any(kw in point_lower for kw in keywords):
                    theme_groups[theme].append(point)
                    assigned = True
                    break
            
            if not assigned:
                theme_groups['general'].append(point)
        
        return dict(theme_groups)
    
    def _add_summary_relationships(self, summaries: Dict[str, Summary]) -> None:
        """Add relationships between hierarchical summaries"""
        # This could be extended to track which parts of detailed summary
        # correspond to brief summary, enabling drill-down navigation
        pass