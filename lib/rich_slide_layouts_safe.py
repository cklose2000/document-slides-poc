#!/usr/bin/env python3
"""
Safe Rich Slide Layouts for Substantial Presentations

This module provides advanced slide layouts using safe components to prevent corruption:
- Executive dashboards with KPI cards
- Multi-chart analytical slides
- Timeline and roadmap visualizations
- Comparison matrices
- Infographic-style layouts
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from typing import Dict, List, Any, Optional, Tuple
import random

# Import safe components to prevent corruption
try:
    from .slide_components import TextComponents, DataComponents, VisualComponents, CompositeComponents
except ImportError:
    from slide_components import TextComponents, DataComponents, VisualComponents, CompositeComponents

class RichSlideLayouts:
    """Create rich, substantial slide layouts safely"""
    
    def __init__(self, brand_config: Optional[Dict[str, Any]] = None):
        """Initialize with brand configuration"""
        self.brand_config = brand_config or self._get_default_config()
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Default brand configuration"""
        return {
            'theme_colors': {
                'primary': '#1e3c72',
                'secondary': '#2a5298',
                'accent1': '#667eea',
                'accent2': '#764ba2',
                'success': '#27ae60',
                'warning': '#f39c12',
                'danger': '#e74c3c',
                'dark': '#2c3e50',
                'light': '#ecf0f1'
            },
            'fonts': {
                'heading': {'family': 'Calibri Light', 'size': 24},
                'body': {'family': 'Calibri', 'size': 12},
                'caption': {'family': 'Calibri Light', 'size': 10}
            }
        }
    
    def create_executive_dashboard_slide(self, slide: Any, metrics: Dict[str, Any], 
                                       title: str = "Executive Dashboard") -> Any:
        """Create an executive dashboard with KPI cards using safe components"""
        
        # Initialize safe components
        text_comp = TextComponents(slide)
        composite_comp = CompositeComponents(slide)
        
        # Add title
        text_comp.add_title(title, 0.5, 0.2, 9.0, 0.8, font_size=28)
        
        # Define KPI metrics
        kpis = [
            {'title': 'Total Revenue', 'value': 12500000, 'change': 15.0},
            {'title': 'Gross Margin', 'value': 42.3, 'change': 2.1},
            {'title': 'Operating Costs', 'value': 4200000, 'change': -5.0},
            {'title': 'Net Profit', 'value': 3800000, 'change': 22.0},
            {'title': 'Cash Flow', 'value': 2100000, 'change': 8.0},
            {'title': 'ROI', 'value': 18.5, 'change': 3.2}
        ]
        
        # Override with actual metrics if provided
        if metrics:
            kpi_index = 0
            for metric_name, metric_data in list(metrics.items())[:6]:
                if kpi_index < len(kpis):
                    kpis[kpi_index]['title'] = metric_name
                    if isinstance(metric_data, dict):
                        kpis[kpi_index]['value'] = metric_data.get('value', 0)
                        kpis[kpi_index]['change'] = metric_data.get('change', 0)
                    else:
                        kpis[kpi_index]['value'] = metric_data
                    kpi_index += 1
        
        # Add KPI dashboard using safe components
        composite_comp.add_kpi_dashboard(kpis[:6], left=0.5, top=1.2, arrangement='horizontal')
        
        return slide
    
    def create_multi_chart_analysis_slide(self, slide: Any, data: Dict[str, Any],
                                        title: str = "Financial Analysis") -> Any:
        """Create a slide with multiple charts using safe components"""
        
        # Initialize safe components
        text_comp = TextComponents(slide)
        data_comp = DataComponents(slide)
        visual_comp = VisualComponents(slide)
        
        # Add title
        text_comp.add_title(title, 0.5, 0.2, 9.0, 0.6, font_size=24)
        
        # Add section header for charts
        text_comp.add_body_text("Performance Metrics", 0.5, 1.0, 4.0, 0.4, font_size=16)
        
        # Add metric table instead of complex charts
        table_data = [
            {"Metric": "Revenue", "Q1": 10.2, "Q2": 11.5, "Q3": 12.8, "Q4": 14.2},
            {"Metric": "Target", "Q1": 10.0, "Q2": 11.0, "Q3": 12.0, "Q4": 13.0},
            {"Metric": "Variance", "Q1": 2.0, "Q2": 4.5, "Q3": 6.7, "Q4": 9.2}
        ]
        
        data_comp.add_metric_table(table_data, 0.5, 1.5, 4.5, 2.5)
        
        # Add insights box using safe callout
        visual_comp.add_callout_box(
            "Key Insights:\n• Revenue exceeded targets by 9.2%\n• Operating efficiency improved 15%\n• YoY growth accelerating",
            5.2, 1.5, 4.0, 2.5, style='info'
        )
        
        # Add expense breakdown section
        text_comp.add_body_text("Expense Breakdown", 0.5, 4.5, 4.0, 0.4, font_size=16)
        
        expense_data = [
            {"Department": "Operations", "Budget": 450000, "Actual": 420000, "Variance": -30000},
            {"Department": "Marketing", "Budget": 250000, "Actual": 265000, "Variance": 15000},
            {"Department": "R&D", "Budget": 200000, "Actual": 195000, "Variance": -5000},
            {"Department": "Admin", "Budget": 100000, "Actual": 98000, "Variance": -2000}
        ]
        
        data_comp.add_metric_table(expense_data, 0.5, 5.0, 9.0, 2.0)
        
        return slide
    
    def create_timeline_roadmap_slide(self, slide: Any, milestones: List[Dict[str, Any]],
                                    title: str = "Strategic Roadmap") -> Any:
        """Create a timeline/roadmap visualization using safe components"""
        
        # Initialize safe components
        text_comp = TextComponents(slide)
        composite_comp = CompositeComponents(slide)
        
        # Add title
        text_comp.add_title(title, 0.5, 0.2, 9.0, 0.6, font_size=24)
        
        # Default milestones if none provided
        if not milestones:
            milestones = [
                {'date': 'Q1 2024', 'title': 'Product Launch'},
                {'date': 'Q2 2024', 'title': 'Market Expansion'},
                {'date': 'Q3 2024', 'title': 'Series B Funding'},
                {'date': 'Q4 2024', 'title': 'Global Rollout'},
                {'date': 'Q1 2025', 'title': 'IPO Preparation'}
            ]
        
        # Create timeline using safe components
        events = [{'date': m['date'], 'title': m['title']} for m in milestones[:8]]  # Limit to 8 events
        composite_comp.add_timeline_visualization(events, 0.5, 1.5, 9.0, 4.5)
        
        # Add legend if milestones have status
        if milestones and 'status' in milestones[0]:
            text_comp.add_body_text("Status: ● Completed  ● In Progress  ● Planned", 
                                   0.5, 6.5, 9.0, 0.5, font_size=10)
        
        return slide
    
    def create_comparison_matrix_slide(self, slide: Any, comparison_data: Dict[str, Any],
                                     title: str = "Competitive Analysis") -> Any:
        """Create a comparison matrix using safe components"""
        
        # Initialize safe components
        text_comp = TextComponents(slide)
        composite_comp = CompositeComponents(slide)
        
        # Add title
        text_comp.add_title(title, 0.5, 0.2, 9.0, 0.6, font_size=24)
        
        # Default comparison data if none provided
        if not comparison_data:
            comparison_data = {
                'Our Company': {
                    'Market Share': '24%',
                    'Revenue': '$12.5M',
                    'Growth Rate': '23%',
                    'Customer Satisfaction': '92%',
                    'Product Features': '45/50'
                },
                'Competitor A': {
                    'Market Share': '31%',
                    'Revenue': '$18.2M',
                    'Growth Rate': '15%',
                    'Customer Satisfaction': '85%',
                    'Product Features': '38/50'
                },
                'Competitor B': {
                    'Market Share': '19%',
                    'Revenue': '$8.7M',
                    'Growth Rate': '12%',
                    'Customer Satisfaction': '88%',
                    'Product Features': '42/50'
                }
            }
        
        # Create comparison matrix using safe components
        composite_comp.add_comparison_matrix(comparison_data, 0.5, 1.5, 9.0, 5.0)
        
        return slide
    
    def create_swot_analysis_slide(self, slide: Any, swot_data: Dict[str, List[str]],
                                 title: str = "SWOT Analysis") -> Any:
        """Create a SWOT analysis slide using safe components"""
        
        # Initialize safe components
        text_comp = TextComponents(slide)
        data_comp = DataComponents(slide)
        visual_comp = VisualComponents(slide)
        
        # Add title
        text_comp.add_title(title, 0.5, 0.2, 9.0, 0.6, font_size=24)
        
        # Default SWOT data if none provided
        if not swot_data:
            swot_data = {
                'strengths': [
                    'Market leader in innovation',
                    'Strong brand recognition',
                    'Experienced team'
                ],
                'weaknesses': [
                    'Limited geographic reach',
                    'High operational costs',
                    'Technology debt'
                ],
                'opportunities': [
                    'Emerging markets expansion',
                    'Strategic partnerships',
                    'New product lines'
                ],
                'threats': [
                    'Increased competition',
                    'Regulatory changes',
                    'Economic uncertainty'
                ]
            }
        
        # Create 2x2 SWOT grid using safe components
        grid_size = 4.25
        spacing = 0.25
        start_x = 0.5
        start_y = 1.2
        
        # Define quadrants
        quadrants = [
            {'title': 'Strengths', 'items': swot_data.get('strengths', []), 'style': 'success'},
            {'title': 'Weaknesses', 'items': swot_data.get('weaknesses', []), 'style': 'danger'},
            {'title': 'Opportunities', 'items': swot_data.get('opportunities', []), 'style': 'info'},
            {'title': 'Threats', 'items': swot_data.get('threats', []), 'style': 'warning'}
        ]
        
        for i, quadrant in enumerate(quadrants):
            row = i // 2
            col = i % 2
            
            x = start_x + (grid_size + spacing) * col
            y = start_y + (grid_size/2 + spacing) * row
            
            # Add quadrant background
            visual_comp.add_callout_box('', x, y, grid_size, grid_size/2, style=quadrant['style'])
            
            # Add quadrant title
            text_comp.add_body_text(quadrant['title'], x + 0.2, y + 0.1, grid_size - 0.4, 0.4, font_size=16)
            
            # Add bullet points
            if quadrant['items']:
                text_comp.add_bullet_points(quadrant['items'][:3], x + 0.2, y + 0.6, 
                                          grid_size - 0.4, grid_size/2 - 0.8, font_size=11)
        
        return slide