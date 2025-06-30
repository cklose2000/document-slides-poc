"""
Smart Layout Engine for Dynamic Slide Composition

This module analyzes content density and type to determine optimal slide layouts,
automatically adjusting spacing, font sizes, and element placement for maximum impact.
"""

from typing import Dict, List, Any, Optional, Tuple
import re
from dataclasses import dataclass
from enum import Enum
from collections import OrderedDict

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
    filtered_metrics: Optional[Dict[str, Any]] = None  # Prioritized metrics for display

class MetricsPrioritizer:
    """Prioritizes and filters metrics for optimal display"""
    
    # Define metric priorities and categories
    METRIC_PRIORITIES = {
        # Revenue metrics (highest priority)
        'revenue': {'priority': 10, 'category': 'Revenue', 'variants': ['revenue', 'sales', 'income', 'receipts']},
        'arr': {'priority': 9, 'category': 'Revenue', 'variants': ['arr', 'annual recurring revenue']},
        'mrr': {'priority': 9, 'category': 'Revenue', 'variants': ['mrr', 'monthly recurring revenue']},
        
        # Profitability metrics
        'profit': {'priority': 8, 'category': 'Profitability', 'variants': ['profit', 'net income', 'earnings']},
        'ebitda': {'priority': 8, 'category': 'Profitability', 'variants': ['ebitda', 'operating income']},
        'margin': {'priority': 7, 'category': 'Profitability', 'variants': ['margin', 'profit margin', 'gross margin']},
        
        # Growth metrics
        'growth': {'priority': 7, 'category': 'Growth', 'variants': ['growth', 'growth rate', 'yoy', 'year over year']},
        'cagr': {'priority': 6, 'category': 'Growth', 'variants': ['cagr', 'compound annual growth rate']},
        
        # Customer metrics
        'customers': {'priority': 6, 'category': 'Customer', 'variants': ['customers', 'users', 'clients', 'accounts']},
        'churn': {'priority': 5, 'category': 'Customer', 'variants': ['churn', 'churn rate', 'retention']},
        'cac': {'priority': 5, 'category': 'Customer', 'variants': ['cac', 'customer acquisition cost']},
        'ltv': {'priority': 5, 'category': 'Customer', 'variants': ['ltv', 'lifetime value', 'clv']},
        
        # Operational metrics
        'expenses': {'priority': 4, 'category': 'Operations', 'variants': ['expenses', 'costs', 'operating expenses']},
        'cash': {'priority': 4, 'category': 'Operations', 'variants': ['cash', 'cash flow', 'free cash flow']},
        'runway': {'priority': 3, 'category': 'Operations', 'variants': ['runway', 'burn rate']}
    }
    
    @classmethod
    def prioritize_metrics(cls, metrics: Dict[str, Any], max_metrics: int = 6) -> Dict[str, Any]:
        """
        Filter and prioritize metrics for display
        
        Args:
            metrics: Raw metrics dictionary
            max_metrics: Maximum number of metrics to display
            
        Returns:
            Prioritized metrics dictionary
        """
        if not metrics:
            return {}
        
        # Score each metric
        scored_metrics = []
        
        for metric_name, metric_data in metrics.items():
            score = cls._calculate_metric_score(metric_name, metric_data)
            scored_metrics.append((score, metric_name, metric_data))
        
        # Sort by score (descending)
        scored_metrics.sort(key=lambda x: x[0], reverse=True)
        
        # Take top metrics and group by category
        result = OrderedDict()
        categories = OrderedDict()
        
        for score, metric_name, metric_data in scored_metrics[:max_metrics]:
            category = cls._get_metric_category(metric_name)
            if category not in categories:
                categories[category] = []
            categories[category].append((metric_name, metric_data))
        
        # Build result maintaining category order
        for category in ['Revenue', 'Profitability', 'Growth', 'Customer', 'Operations']:
            if category in categories:
                for metric_name, metric_data in categories[category]:
                    result[metric_name] = metric_data
        
        return result
    
    @classmethod
    def _calculate_metric_score(cls, metric_name: str, metric_data: Any) -> float:
        """Calculate priority score for a metric"""
        base_score = 0
        metric_lower = metric_name.lower()
        
        # Check against known metric types
        for metric_type, info in cls.METRIC_PRIORITIES.items():
            for variant in info['variants']:
                if variant in metric_lower:
                    base_score = info['priority']
                    break
            if base_score > 0:
                break
        
        # Bonus for having actual numeric values
        if isinstance(metric_data, dict) and 'value' in metric_data:
            value = metric_data.get('value')
            if value and str(value).strip() not in ['N/A', 'None', '']:
                base_score += 1
        
        # Penalty for duplicate-looking metrics (e.g., revenue_sheet1, revenue_sheet2)
        if any(sheet_indicator in metric_lower for sheet_indicator in ['sheet', '_q', '_jan', '_feb']):
            base_score *= 0.5
        
        return base_score
    
    @classmethod
    def _get_metric_category(cls, metric_name: str) -> str:
        """Determine the category of a metric"""
        metric_lower = metric_name.lower()
        
        for metric_type, info in cls.METRIC_PRIORITIES.items():
            for variant in info['variants']:
                if variant in metric_lower:
                    return info['category']
        
        return 'Other'
    
    @classmethod
    def format_metric_name(cls, metric_name: str) -> str:
        """Format metric name for display (without emojis)"""
        # Clean up the name
        clean_name = metric_name.replace('_', ' ').strip()
        
        # Handle common abbreviations
        replacements = {
            'arr': 'ARR',
            'mrr': 'MRR',
            'cac': 'CAC',
            'ltv': 'LTV',
            'roi': 'ROI',
            'ebitda': 'EBITDA',
            'yoy': 'YoY',
            'cagr': 'CAGR'
        }
        
        words = clean_name.split()
        formatted_words = []
        
        for word in words:
            word_lower = word.lower()
            if word_lower in replacements:
                formatted_words.append(replacements[word_lower])
            else:
                formatted_words.append(word.capitalize())
        
        return ' '.join(formatted_words)

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
                'font_sizes': {'title': 28, 'subtitle': 18, 'body': 12, 'metric': 18, 'header': 14},
                'spacing': {'title_margin': 1.0, 'content_margin': 0.8}
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
        # Filter metrics first if we have financial metrics
        if 'financial_metrics' in content_data and isinstance(content_data['financial_metrics'], dict):
            filtered_metrics = MetricsPrioritizer.prioritize_metrics(
                content_data['financial_metrics'], 
                max_metrics=6
            )
            # Create a copy of content_data with filtered metrics
            filtered_content_data = content_data.copy()
            filtered_content_data['financial_metrics'] = filtered_metrics
        else:
            filtered_content_data = content_data
            filtered_metrics = None
        
        blocks = self.analyze_content_blocks(filtered_content_data)
        content_type = self.determine_content_type(blocks)
        complexity = self.calculate_layout_complexity(blocks)
        
        # Select base layout template
        layout_type = self._select_layout_template(content_type, complexity)
        base_template = self.layout_templates[layout_type]
        
        print(f"DEBUG Layout Engine: Content type = {content_type}, Complexity = {complexity}")
        print(f"DEBUG Layout Engine: Number of blocks = {len(blocks)}")
        for i, block in enumerate(blocks):
            print(f"  Block {i}: type={block.content_type}, data_points={block.data_points}")
        if filtered_metrics:
            print(f"DEBUG Layout Engine: Filtered from {len(content_data.get('financial_metrics', {}))} to {len(filtered_metrics)} metrics")
        
        # Customize based on content analysis
        recommendation = self._customize_layout(
            base_template, content_type, complexity, blocks
        )
        
        # Add filtered metrics to recommendation
        recommendation.filtered_metrics = filtered_metrics
        
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
        
        print(f"DEBUG positions: content_type={content_type}, num_blocks={num_blocks}")
        if content_type == ContentType.DATA_HEAVY and num_blocks >= 1:  # Changed from >= 2 to >= 1
            # Split content area for data + chart with better proportions
            # 40/60 split for table/chart with some padding
            positions['table'] = (0.5, content_top, 3.8, content_height * 0.9)  # Narrower table
            positions['chart'] = (4.5, content_top + 0.2, 5.0, content_height * 0.85)  # Wider chart with slight offset
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