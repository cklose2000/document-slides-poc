"""
Smart Layout Engine for Dynamic Slide Composition

This module analyzes content density and type to determine optimal slide layouts,
automatically adjusting spacing, font sizes, and element placement for maximum impact.
"""

from typing import Dict, List, Any, Optional, Tuple
import re
from dataclasses import dataclass
from enum import Enum

class ContentType(Enum):
    """Types of content for layout decisions"""
    TEXT_HEAVY = "text_heavy"
    DATA_HEAVY = "data_heavy"
    MIXED = "mixed"
    VISUAL = "visual"
    SUMMARY = "summary"

class LayoutComplexity(Enum):
    """Layout complexity levels"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    DENSE = "dense"

@dataclass
class ContentBlock:
    """Represents a block of content for layout"""
    content_type: str
    text_length: int
    data_points: int
    visual_elements: int
    importance: float  # 0.0 to 1.0
    content: Any

@dataclass
class LayoutRecommendation:
    """Layout recommendation with specific parameters"""
    layout_type: str
    font_sizes: Dict[str, int]
    spacing: Dict[str, float]
    element_positions: Dict[str, Tuple[float, float, float, float]]  # (left, top, width, height)
    max_items_per_slide: int
    split_recommendation: bool
    reasoning: List[str]

class SmartLayoutEngine:
    """
    Analyzes content and recommends optimal slide layouts
    """
    
    def __init__(self):
        """Initialize the layout engine with default parameters"""
        self.layout_templates = {
            'title_only': {
                'description': 'Title slide with minimal content',
                'max_items': 1,
                'font_sizes': {'title': 48, 'subtitle': 32, 'body': 16},
                'spacing': {'title_margin': 2.0, 'content_margin': 1.5}
            },
            'title_content': {
                'description': 'Standard title and content layout',
                'max_items': 8,
                'font_sizes': {'title': 40, 'subtitle': 28, 'body': 16},
                'spacing': {'title_margin': 1.5, 'content_margin': 1.0}
            },
            'two_column': {
                'description': 'Two-column layout for balanced content',
                'max_items': 12,
                'font_sizes': {'title': 36, 'subtitle': 24, 'body': 14},
                'spacing': {'title_margin': 1.2, 'content_margin': 0.8}
            },
            'dashboard': {
                'description': 'Dashboard layout for metrics and charts',
                'max_items': 16,
                'font_sizes': {'title': 32, 'subtitle': 20, 'body': 12, 'metric': 24},
                'spacing': {'title_margin': 1.0, 'content_margin': 0.6}
            },
            'dense_data': {
                'description': 'Compact layout for data-heavy content',
                'max_items': 20,
                'font_sizes': {'title': 28, 'subtitle': 18, 'body': 10, 'metric': 20},
                'spacing': {'title_margin': 0.8, 'content_margin': 0.4}
            }
        }
    
    def analyze_content_blocks(self, content_data: Dict[str, Any]) -> List[ContentBlock]:
        """
        Analyze content and break it into logical blocks
        
        Args:
            content_data: Content from slide generation (financial metrics, insights, etc.)
            
        Returns:
            List of content blocks with analysis
        """
        blocks = []
        
        # Analyze financial metrics
        if 'financial_metrics' in content_data:
            metrics = content_data['financial_metrics']
            if isinstance(metrics, dict) and metrics:
                text_length = sum(len(str(v.get('value', ''))) for v in metrics.values() if isinstance(v, dict))
                
                blocks.append(ContentBlock(
                    content_type='data',
                    text_length=text_length,
                    data_points=len(metrics),
                    visual_elements=1 if len(metrics) >= 3 else 0,  # Chart potential
                    importance=0.9,
                    content=metrics
                ))
        
        # Analyze key insights
        if 'key_insights' in content_data:
            insights = content_data['key_insights']
            if isinstance(insights, list) and insights:
                total_text = sum(len(str(insight)) for insight in insights)
                
                blocks.append(ContentBlock(
                    content_type='text',
                    text_length=total_text,
                    data_points=len(insights),
                    visual_elements=0,
                    importance=0.8,
                    content=insights
                ))
        
        # Analyze company overview
        if 'company_overview' in content_data:
            overview = content_data['company_overview']
            if isinstance(overview, dict):
                text_content = ' '.join(str(v) for v in overview.values() if v)
                
                blocks.append(ContentBlock(
                    content_type='text',
                    text_length=len(text_content),
                    data_points=len(overview),
                    visual_elements=0,
                    importance=0.7,
                    content=overview
                ))
        
        return blocks
    
    def determine_content_type(self, blocks: List[ContentBlock]) -> ContentType:
        """
        Determine overall content type based on content blocks
        
        Args:
            blocks: List of content blocks
            
        Returns:
            Overall content type
        """
        if not blocks:
            return ContentType.SUMMARY
        
        total_text = sum(block.text_length for block in blocks)
        total_data_points = sum(block.data_points for block in blocks)
        total_visual_elements = sum(block.visual_elements for block in blocks)
        
        # Decision logic
        if total_data_points >= 10 and total_visual_elements >= 1:
            return ContentType.DATA_HEAVY
        elif total_text >= 500:
            return ContentType.TEXT_HEAVY
        elif total_visual_elements >= 2:
            return ContentType.VISUAL
        elif total_data_points >= 5 or total_text >= 200:
            return ContentType.MIXED
        else:
            return ContentType.SUMMARY
    
    def calculate_layout_complexity(self, blocks: List[ContentBlock]) -> LayoutComplexity:
        """
        Calculate layout complexity based on content analysis
        
        Args:
            blocks: List of content blocks
            
        Returns:
            Layout complexity level
        """
        if not blocks:
            return LayoutComplexity.SIMPLE
        
        # Complexity factors
        total_items = sum(block.data_points for block in blocks)
        high_importance_items = sum(1 for block in blocks if block.importance >= 0.8)
        visual_elements = sum(block.visual_elements for block in blocks)
        
        complexity_score = (
            total_items * 0.5 +
            high_importance_items * 2.0 +
            visual_elements * 1.5
        )
        
        if complexity_score <= 5:
            return LayoutComplexity.SIMPLE
        elif complexity_score <= 12:
            return LayoutComplexity.MODERATE
        elif complexity_score <= 20:
            return LayoutComplexity.COMPLEX
        else:
            return LayoutComplexity.DENSE
    
    def recommend_layout(self, content_data: Dict[str, Any]) -> LayoutRecommendation:
        """
        Recommend optimal layout based on content analysis
        
        Args:
            content_data: Content from slide generation
            
        Returns:
            Layout recommendation with specific parameters
        """
        blocks = self.analyze_content_blocks(content_data)
        content_type = self.determine_content_type(blocks)
        complexity = self.calculate_layout_complexity(blocks)
        
        # Select base layout template
        layout_type = self._select_layout_template(content_type, complexity)
        base_template = self.layout_templates[layout_type]
        
        # Customize based on content analysis
        recommendation = self._customize_layout(
            base_template, content_type, complexity, blocks
        )
        
        # Add reasoning
        reasoning = self._generate_layout_reasoning(content_type, complexity, blocks)
        recommendation.reasoning = reasoning
        
        return recommendation
    
    def _select_layout_template(self, content_type: ContentType, complexity: LayoutComplexity) -> str:
        """Select the base layout template"""
        # Layout selection matrix
        layout_matrix = {
            (ContentType.SUMMARY, LayoutComplexity.SIMPLE): 'title_only',
            (ContentType.SUMMARY, LayoutComplexity.MODERATE): 'title_content',
            
            (ContentType.TEXT_HEAVY, LayoutComplexity.SIMPLE): 'title_content',
            (ContentType.TEXT_HEAVY, LayoutComplexity.MODERATE): 'title_content',
            (ContentType.TEXT_HEAVY, LayoutComplexity.COMPLEX): 'two_column',
            (ContentType.TEXT_HEAVY, LayoutComplexity.DENSE): 'two_column',
            
            (ContentType.DATA_HEAVY, LayoutComplexity.SIMPLE): 'title_content',
            (ContentType.DATA_HEAVY, LayoutComplexity.MODERATE): 'dashboard',
            (ContentType.DATA_HEAVY, LayoutComplexity.COMPLEX): 'dashboard',
            (ContentType.DATA_HEAVY, LayoutComplexity.DENSE): 'dense_data',
            
            (ContentType.MIXED, LayoutComplexity.SIMPLE): 'title_content',
            (ContentType.MIXED, LayoutComplexity.MODERATE): 'two_column',
            (ContentType.MIXED, LayoutComplexity.COMPLEX): 'dashboard',
            (ContentType.MIXED, LayoutComplexity.DENSE): 'dense_data',
            
            (ContentType.VISUAL, LayoutComplexity.SIMPLE): 'title_content',
            (ContentType.VISUAL, LayoutComplexity.MODERATE): 'two_column',
            (ContentType.VISUAL, LayoutComplexity.COMPLEX): 'dashboard',
            (ContentType.VISUAL, LayoutComplexity.DENSE): 'dashboard',
        }
        
        return layout_matrix.get((content_type, complexity), 'title_content')
    
    def _customize_layout(self, base_template: Dict[str, Any], 
                         content_type: ContentType, complexity: LayoutComplexity,
                         blocks: List[ContentBlock]) -> LayoutRecommendation:
        """Customize the base template based on specific content"""
        
        # Start with base template
        font_sizes = base_template['font_sizes'].copy()
        spacing = base_template['spacing'].copy()
        max_items = base_template['max_items']
        
        # Adjust based on content density
        total_items = sum(block.data_points for block in blocks)
        if total_items > max_items:
            # Reduce font sizes for dense content
            font_sizes = {k: max(int(v * 0.9), 8) for k, v in font_sizes.items()}
            spacing = {k: v * 0.8 for k, v in spacing.items()}
        
        # Adjust based on content type
        if content_type == ContentType.DATA_HEAVY:
            # Emphasize metric display
            if 'metric' not in font_sizes:
                font_sizes['metric'] = font_sizes.get('body', 16) + 4
        
        # Define element positions based on layout type
        element_positions = self._calculate_element_positions(
            base_template, content_type, len(blocks)
        )
        
        # Determine if content should be split across slides
        split_recommendation = total_items > max_items * 1.5
        
        return LayoutRecommendation(
            layout_type=base_template['description'],
            font_sizes=font_sizes,
            spacing=spacing,
            element_positions=element_positions,
            max_items_per_slide=max_items,
            split_recommendation=split_recommendation,
            reasoning=[]  # Will be filled by caller
        )
    
    def _calculate_element_positions(self, template: Dict[str, Any], 
                                   content_type: ContentType, 
                                   num_blocks: int) -> Dict[str, Tuple[float, float, float, float]]:
        """Calculate optimal positions for slide elements"""
        positions = {}
        
        # Standard slide dimensions (10" x 7.5")
        slide_width = 10.0
        slide_height = 7.5
        
        # Title position (always at top)
        title_margin = template['spacing']['title_margin']
        positions['title'] = (1.0, 0.5, 8.0, title_margin)
        
        # Content area
        content_top = 0.5 + title_margin + 0.3
        content_height = slide_height - content_top - 0.5
        
        if content_type == ContentType.DATA_HEAVY and num_blocks >= 2:
            # Split content area for data + chart
            positions['table'] = (0.5, content_top, 4.5, content_height)
            positions['chart'] = (5.5, content_top, 4.0, content_height * 0.8)
        elif num_blocks >= 2:
            # Two-column layout
            positions['left_content'] = (0.5, content_top, 4.5, content_height)
            positions['right_content'] = (5.5, content_top, 4.0, content_height)
        else:
            # Single content area
            positions['content'] = (1.0, content_top, 8.0, content_height)
        
        # Attribution/footer
        positions['attribution'] = (0.5, slide_height - 0.8, 9.0, 0.5)
        
        return positions
    
    def _generate_layout_reasoning(self, content_type: ContentType, 
                                 complexity: LayoutComplexity,
                                 blocks: List[ContentBlock]) -> List[str]:
        """Generate human-readable reasoning for layout decisions"""
        reasoning = []
        
        # Content type reasoning
        if content_type == ContentType.DATA_HEAVY:
            reasoning.append("Data-heavy content detected - optimized for metrics and charts")
        elif content_type == ContentType.TEXT_HEAVY:
            reasoning.append("Text-heavy content - optimized for readability")
        elif content_type == ContentType.MIXED:
            reasoning.append("Mixed content type - balanced layout for text and data")
        
        # Complexity reasoning
        if complexity == LayoutComplexity.DENSE:
            reasoning.append("High content density - using compact layout")
        elif complexity == LayoutComplexity.COMPLEX:
            reasoning.append("Complex content structure - multi-section layout")
        
        # Specific optimizations
        total_data_points = sum(block.data_points for block in blocks)
        if total_data_points >= 8:
            reasoning.append("Multiple metrics detected - dashboard-style layout")
        
        visual_elements = sum(block.visual_elements for block in blocks)
        if visual_elements >= 1:
            reasoning.append("Chart integration recommended for visual impact")
        
        return reasoning
    
    def should_split_content(self, content_data: Dict[str, Any], 
                           max_items_per_slide: int = 8) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Determine if content should be split across multiple slides
        
        Args:
            content_data: Content to analyze
            max_items_per_slide: Maximum items per slide
            
        Returns:
            Tuple of (should_split, split_content_list)
        """
        blocks = self.analyze_content_blocks(content_data)
        total_items = sum(block.data_points for block in blocks)
        
        if total_items <= max_items_per_slide:
            return False, [content_data]
        
        # Split content into logical groups
        split_content = []
        
        # Separate high-importance content
        high_priority = {}
        low_priority = {}
        
        for key, value in content_data.items():
            if key == 'financial_metrics' and isinstance(value, dict):
                # Split metrics by importance or alphabetically
                metrics_items = list(value.items())
                chunk_size = max_items_per_slide // 2
                
                for i in range(0, len(metrics_items), chunk_size):
                    chunk = dict(metrics_items[i:i + chunk_size])
                    split_content.append({
                        'financial_metrics': chunk,
                        'title_suffix': f" (Part {len(split_content) + 1})"
                    })
            else:
                # Add other content to first slide
                if not split_content:
                    split_content.append({})
                split_content[0][key] = value
        
        return True, split_content if split_content else [content_data]

# Example usage and testing
if __name__ == "__main__":
    layout_engine = SmartLayoutEngine()
    
    # Test with sample content
    test_content = {
        'financial_metrics': {
            'revenue': {'value': '$15.2M', 'confidence': 0.9},
            'profit': {'value': '$12.5M', 'confidence': 0.8},
            'growth_rate': {'value': '23%', 'confidence': 0.7},
            'customers': {'value': '450', 'confidence': 0.9},
            'churn_rate': {'value': '2.1%', 'confidence': 0.8}
        },
        'key_insights': [
            'Strong Q3 performance with record revenue',
            'Customer acquisition improved significantly',
            'Profit margins remain healthy at industry-leading levels'
        ],
        'company_overview': {
            'name': 'SaaSy Inc.',
            'industry': 'Software as a Service'
        }
    }
    
    recommendation = layout_engine.recommend_layout(test_content)
    print(f"Layout Type: {recommendation.layout_type}")
    print(f"Font Sizes: {recommendation.font_sizes}")
    print(f"Should Split: {recommendation.split_recommendation}")
    print(f"Reasoning: {recommendation.reasoning}")
    
    # Test content splitting
    should_split, split_content = layout_engine.should_split_content(test_content)
    print(f"\nShould split content: {should_split}")
    print(f"Number of slides: {len(split_content)}")