"""
Brand-Aware Slide Generator

Enhanced slide generator that applies brand templates and styling
for consistent, professional presentation output.
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.shared import qn
try:
    from .template_parser import BrandManager, TemplateParser
    from .source_tracker import SourceTracker
    from .chart_generator import ChartGenerator
except ImportError:
    from template_parser import BrandManager, TemplateParser
    from source_tracker import SourceTracker
    from chart_generator import ChartGenerator
import os
import re
from typing import Dict, List, Any, Optional, Tuple
from io import BytesIO

class BrandedSlideGenerator:
    """Generate slides with consistent brand styling from templates"""
    
    def __init__(self, brand_manager: BrandManager = None, template_name: str = None, 
                 source_tracker: Optional[SourceTracker] = None):
        """Initialize with brand manager, template selection, and source tracker"""
        self.brand_manager = brand_manager or BrandManager()
        self.source_tracker = source_tracker
        
        if template_name:
            self.brand_manager.set_current_template(template_name)
        
        # Get current brand configuration
        self.brand_config = self.brand_manager.get_current_brand_config()
        
        # Initialize chart generator with brand config
        self.chart_generator = ChartGenerator(self.brand_config)
        
        # Initialize presentation
        self._init_presentation()
    
    def _init_presentation(self):
        """Initialize presentation with template or create blank"""
        current_template = self.brand_manager.get_current_template()
        
        if current_template and os.path.exists(current_template.template_path):
            # Start with template presentation
            self.prs = Presentation(current_template.template_path)
            # Note: We'll keep existing slides in template for now to avoid clearing issues
            # In production, we'd implement proper slide clearing
        else:
            # Create blank presentation
            self.prs = Presentation()
    
    def create_financial_summary_slide(self, data: Dict[str, Any], source_refs: Dict[str, Any]) -> Any:
        """Create a branded financial summary slide"""
        # Select appropriate layout
        layout = self._get_layout_for_content('financial_summary')
        slide = self.prs.slides.add_slide(layout)
        
        # Add title with brand styling
        title_shape = self._add_branded_title(slide, "Financial Summary")
        
        # Add metrics table with brand colors
        if data and isinstance(data, dict):
            self._add_branded_metrics_table(slide, data, Inches(1), Inches(2))
        
        # Add source attribution
        self.add_source_attribution(slide, source_refs)
        
        return slide
    
    def create_company_overview_slide(self, company_data: Dict[str, Any], source_refs: Dict[str, Any]) -> Any:
        """Create a branded company overview slide"""
        layout = self._get_layout_for_content('company_overview')
        slide = self.prs.slides.add_slide(layout)
        
        # Add title
        title_shape = self._add_branded_title(slide, "Company Overview")
        
        # Add company info with brand styling
        if company_data:
            self._add_branded_company_info(slide, company_data, Inches(1), Inches(2))
        
        # Add source attribution
        self.add_source_attribution(slide, source_refs)
        
        return slide
    
    def create_data_insights_slide(self, insights_data: Any, source_refs: Dict[str, Any]) -> Any:
        """Create a branded data insights slide"""
        layout = self._get_layout_for_content('insights')
        slide = self.prs.slides.add_slide(layout)
        
        # Add title
        title_shape = self._add_branded_title(slide, "Key Insights")
        
        # Add insights with brand styling
        if insights_data:
            self._add_branded_insights_bullets(slide, insights_data, Inches(1), Inches(2))
        
        # Add source attribution
        self.add_source_attribution(slide, source_refs)
        
        return slide
    
    def _get_layout_for_content(self, content_type: str) -> Any:
        """Get appropriate slide layout for content type"""
        current_template = self.brand_manager.get_current_template()
        
        if current_template:
            # Try to find specific layout type
            if content_type == 'title':
                layout = current_template.get_layout_by_type('title_slide')
            else:
                layout = current_template.get_layout_by_type('content_slide')
            
            if layout:
                layout_index = layout.get('index', 0)
                if layout_index < len(self.prs.slide_layouts):
                    return self.prs.slide_layouts[layout_index]
        
        # Fallback to generic layouts
        if len(self.prs.slide_layouts) > 6:
            return self.prs.slide_layouts[6]  # Blank layout
        elif len(self.prs.slide_layouts) > 1:
            return self.prs.slide_layouts[1]  # Title and content
        else:
            return self.prs.slide_layouts[0]  # Title slide
    
    def _add_branded_title(self, slide: Any, title_text: str) -> Any:
        """Add title with brand-appropriate styling"""
        # Try to use title placeholder if available
        title_shape = None
        
        for shape in slide.shapes:
            if hasattr(shape, 'placeholder_format') and shape.placeholder_format:
                if 'TITLE' in str(shape.placeholder_format.type):
                    title_shape = shape
                    break
        
        # If no title placeholder, create text box
        if title_shape is None:
            title_shape = slide.shapes.add_textbox(
                Inches(1), Inches(0.5), Inches(8), Inches(1)
            )
        
        # Set title text
        title_frame = title_shape.text_frame
        title_frame.clear()
        title_frame.text = title_text
        
        # Apply brand styling
        title_paragraph = title_frame.paragraphs[0]
        self._apply_font_style(title_paragraph, 'heading', size='large')
        title_paragraph.alignment = PP_ALIGN.CENTER
        
        return title_shape
    
    def _add_branded_metrics_table(self, slide: Any, metrics_data: Dict[str, Any], 
                                 left: float, top: float):
        """Add metrics table with brand styling"""
        if not metrics_data:
            return
        
        # Calculate table dimensions
        rows = min(len(metrics_data) + 1, 10)  # +1 for header
        cols = 3  # Metric, Value, Source
        
        # Add table
        table_shape = slide.shapes.add_table(rows, cols, left, top, Inches(8), Inches(4))
        table = table_shape.table
        
        # Set column widths
        table.columns[0].width = Inches(3)
        table.columns[1].width = Inches(2) 
        table.columns[2].width = Inches(3)
        
        # Add headers with brand styling
        headers = ['Metric', 'Value', 'Source']
        for i, header in enumerate(headers):
            cell = table.cell(0, i)
            cell.text = header
            self._style_branded_header_cell(cell)
        
        # Add data rows
        row_idx = 1
        for metric_name, metric_info in metrics_data.items():
            if row_idx >= rows:
                break
            
            # Metric name
            metric_cell = table.cell(row_idx, 0)
            metric_cell.text = str(metric_name)
            self._apply_cell_font_style(metric_cell)
            
            # Value with clickable source link
            value = metric_info.get('value', 'N/A')
            formatted_value = self._format_financial_value(value)
            value_cell = table.cell(row_idx, 1)
            
            # Add clickable hyperlink if data point ID is available
            data_point_id = metric_info.get('data_point_id')
            if self.source_tracker and data_point_id:
                self._add_clickable_value(value_cell, formatted_value, data_point_id)
            else:
                value_cell.text = formatted_value
                self._apply_cell_font_style(value_cell)
            
            # Source with enhanced attribution
            source_cell = table.cell(row_idx, 2)
            if self.source_tracker and data_point_id:
                # Use enhanced source attribution
                source_text = self.source_tracker.get_source_attribution_text(data_point_id, 'minimal')
                self._add_clickable_source(source_cell, source_text, data_point_id)
            else:
                # Fallback to basic cell reference
                cell_ref = metric_info.get('cell', 'Unknown')
                source_text = f"Cell {cell_ref}"
                source_cell.text = source_text
                self._apply_cell_font_style(source_cell, size='small')
            
            row_idx += 1
    
    def _add_branded_company_info(self, slide: Any, company_data: Dict[str, Any],
                                left: float, top: float):
        """Add company information with brand styling"""
        info_shape = slide.shapes.add_textbox(left, top, Inches(8), Inches(4))
        info_frame = info_shape.text_frame
        
        # Build company info text
        info_lines = []
        
        if 'name' in company_data:
            info_lines.append(f"Company: {company_data['name']}")
        
        if 'industry' in company_data:
            info_lines.append(f"Industry: {company_data['industry']}")
        
        if 'description' in company_data:
            info_lines.append(f"Description: {company_data['description']}")
        
        # Set text
        info_frame.text = '\\n\\n'.join(info_lines)
        
        # Apply brand styling
        for paragraph in info_frame.paragraphs:
            self._apply_font_style(paragraph, 'body', size='medium')
    
    def _add_branded_insights_bullets(self, slide: Any, insights: Any,
                                    left: float, top: float):
        """Add insights bullets with brand styling"""
        bullets_shape = slide.shapes.add_textbox(left, top, Inches(8), Inches(4))
        bullets_frame = bullets_shape.text_frame
        
        if isinstance(insights, list):
            for i, insight in enumerate(insights):
                if i == 0:
                    bullets_frame.text = f"• {insight}"
                    paragraph = bullets_frame.paragraphs[0]
                else:
                    paragraph = bullets_frame.add_paragraph()
                    paragraph.text = f"• {insight}"
                
                self._apply_font_style(paragraph, 'body', size='medium')
                
        elif isinstance(insights, dict):
            first = True
            for key, value in insights.items():
                text = f"• {key}: {value}"
                if first:
                    bullets_frame.text = text
                    paragraph = bullets_frame.paragraphs[0]
                    first = False
                else:
                    paragraph = bullets_frame.add_paragraph()
                    paragraph.text = text
                
                self._apply_font_style(paragraph, 'body', size='medium')
    
    def _style_branded_header_cell(self, cell: Any):
        """Apply brand styling to table header cells"""
        # Set background color to primary brand color
        cell.fill.solid()
        primary_color = self._get_brand_color('primary')
        cell.fill.fore_color.rgb = self._hex_to_rgb(primary_color)
        
        # Style text
        for paragraph in cell.text_frame.paragraphs:
            self._apply_font_style(paragraph, 'heading', size='small')
            # Set text color to white for contrast
            for run in paragraph.runs:
                run.font.color.rgb = RGBColor(255, 255, 255)
    
    def _apply_cell_font_style(self, cell: Any, size: str = 'medium'):
        """Apply brand font styling to table cells"""
        for paragraph in cell.text_frame.paragraphs:
            self._apply_font_style(paragraph, 'body', size=size)
    
    def _apply_font_style(self, paragraph: Any, font_type: str = 'body', size: str = 'medium'):
        """Apply brand font styling to paragraph"""
        font_config = self.brand_config.get('fonts', {}).get(font_type, {})
        
        for run in paragraph.runs:
            # Set font family
            font_family = font_config.get('family', 'Calibri')
            run.font.name = font_family
            
            # Set font size
            size_key = f'size_{size}'
            font_size = font_config.get(size_key, font_config.get('size_medium', 14))
            run.font.size = Pt(font_size)
            
            # Set bold
            if font_config.get('bold', False):
                run.font.bold = True
            
            # Set color to dark brand color
            if font_type == 'heading':
                color = self._get_brand_color('dark1', '#000000')
            else:
                color = self._get_brand_color('dark1', '#333333')
            
            run.font.color.rgb = self._hex_to_rgb(color)
    
    def _get_brand_color(self, color_name: str, default: str = '#4F81BD') -> str:
        """Get brand color by name"""
        return self.brand_config.get('theme_colors', {}).get(color_name, default)
    
    def _hex_to_rgb(self, hex_color: str) -> RGBColor:
        """Convert hex color to RGBColor object"""
        # Remove # if present
        hex_color = hex_color.lstrip('#')
        
        # Convert to RGB
        try:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return RGBColor(r, g, b)
        except:
            # Fallback to blue
            return RGBColor(79, 129, 189)
    
    def _format_financial_value(self, value: Any) -> str:
        """Format financial values for display"""
        if isinstance(value, (int, float)):
            if abs(value) > 1000000:
                return f"${value/1000000:.1f}M"
            elif abs(value) > 1000:
                return f"${value/1000:.0f}K"
            else:
                return f"${value:,.0f}"
        else:
            return str(value)
    
    def add_source_attribution(self, slide: Any, source_refs: Dict[str, Any]):
        """Add enhanced source attribution with clickable links and brand styling"""
        if not source_refs:
            return
        
        # Add attribution text box at bottom
        attr_shape = slide.shapes.add_textbox(
            Inches(0.5), Inches(6.5), Inches(9), Inches(1)
        )
        attr_frame = attr_shape.text_frame
        
        # Enhanced attribution with source tracker integration
        if self.source_tracker and isinstance(source_refs, dict):
            # Check if source_refs contains data point IDs
            data_point_ids = []
            for source, details in source_refs.items():
                if isinstance(details, dict) and 'data_point_id' in details:
                    data_point_ids.append(details['data_point_id'])
            
            if data_point_ids:
                # Use enhanced source attribution for tracked data points
                attr_lines = []
                for dp_id in data_point_ids[:3]:  # Limit to 3 sources for space
                    source_text = self.source_tracker.get_source_attribution_text(dp_id, 'minimal')
                    attr_lines.append(source_text)
                
                attr_text = " | ".join(attr_lines)
                if len(data_point_ids) > 3:
                    attr_text += f" (+{len(data_point_ids) - 3} more)"
            else:
                # Fallback to original method
                attr_text = self._build_fallback_attribution(source_refs)
        else:
            # Fallback to original method
            attr_text = self._build_fallback_attribution(source_refs)
        
        attr_frame.text = attr_text
        
        # Style attribution text
        for paragraph in attr_frame.paragraphs:
            paragraph.alignment = PP_ALIGN.CENTER
            for run in paragraph.runs:
                run.font.size = Pt(8)
                run.font.name = self.brand_config.get('fonts', {}).get('body', {}).get('family', 'Calibri')
                # Use secondary brand color for attribution
                color = self._get_brand_color('secondary', '#808080')
                run.font.color.rgb = self._hex_to_rgb(color)
    
    def create_title_slide(self, title: str, subtitle: str = None) -> Any:
        """Create a branded title slide"""
        layout = self._get_layout_for_content('title')
        slide = self.prs.slides.add_slide(layout)
        
        # Add main title
        title_shape = self._add_branded_title(slide, title)
        
        # Add subtitle if provided
        if subtitle:
            subtitle_shape = slide.shapes.add_textbox(
                Inches(1), Inches(2), Inches(8), Inches(1)
            )
            subtitle_frame = subtitle_shape.text_frame
            subtitle_frame.text = subtitle
            
            # Style subtitle
            for paragraph in subtitle_frame.paragraphs:
                self._apply_font_style(paragraph, 'body', size='large')
                paragraph.alignment = PP_ALIGN.CENTER
        
        return slide
    
    def save_presentation(self, output_path: str) -> str:
        """Save the branded presentation"""
        self.prs.save(output_path)
        return output_path
    
    def get_available_templates(self) -> List[str]:
        """Get list of available brand templates"""
        return self.brand_manager.list_templates()
    
    def switch_template(self, template_name: str):
        """Switch to a different brand template"""
        self.brand_manager.set_current_template(template_name)
        self.brand_config = self.brand_manager.get_current_brand_config()
        # Reinitialize chart generator with new brand config
        self.chart_generator = ChartGenerator(self.brand_config)
        # Reinitialize presentation with new template
        self._init_presentation()
    
    def _add_clickable_value(self, cell: Any, display_text: str, data_point_id: str):
        """Add a clickable hyperlink to a table cell for a data value"""
        if not self.source_tracker:
            cell.text = display_text
            self._apply_cell_font_style(cell)
            return
        
        # Get hyperlink URL from source tracker
        hyperlink_url = self.source_tracker.get_source_hyperlink(data_point_id, display_text)
        
        # Clear cell and add hyperlink
        cell.text = ""
        paragraph = cell.text_frame.paragraphs[0]
        
        # Add hyperlink run
        run = paragraph.runs[0] if paragraph.runs else paragraph.add_run()
        run.text = display_text
        
        try:
            # Add hyperlink to the run
            run.hyperlink.address = hyperlink_url
            
            # Style the hyperlink
            run.font.size = Pt(12)
            run.font.name = self.brand_config.get('fonts', {}).get('body', {}).get('family', 'Calibri')
            run.font.color.rgb = self._get_brand_color('accent1', '#0066CC')  # Blue for links
            run.font.underline = True
            
        except Exception:
            # Fallback if hyperlink creation fails
            run.text = display_text
            self._apply_cell_font_style(cell)
    
    def _add_clickable_source(self, cell: Any, source_text: str, data_point_id: str):
        """Add a clickable source reference to a table cell"""
        if not self.source_tracker:
            cell.text = source_text
            self._apply_cell_font_style(cell, size='small')
            return
        
        # Get source context for tooltip/title
        source_context = self.source_tracker.get_source_context(data_point_id)
        tooltip_text = source_context.get('source_details', {}).get('location', 'Source details')
        
        # Get hyperlink URL
        hyperlink_url = self.source_tracker.get_source_hyperlink(data_point_id, source_text)
        
        # Clear cell and add hyperlink
        cell.text = ""
        paragraph = cell.text_frame.paragraphs[0]
        
        # Add hyperlink run
        run = paragraph.runs[0] if paragraph.runs else paragraph.add_run()
        run.text = source_text
        
        try:
            # Add hyperlink
            run.hyperlink.address = hyperlink_url
            
            # Style the source link
            run.font.size = Pt(10)
            run.font.name = self.brand_config.get('fonts', {}).get('body', {}).get('family', 'Calibri')
            run.font.color.rgb = self._get_brand_color('secondary', '#666666')
            run.font.italic = True
            
        except Exception:
            # Fallback if hyperlink creation fails
            run.text = source_text
            self._apply_cell_font_style(cell, size='small')
    
    def _build_fallback_attribution(self, source_refs: Any) -> str:
        """Build attribution text using fallback method for non-tracked sources"""
        if isinstance(source_refs, dict):
            attr_lines = []
            for source, details in source_refs.items():
                if isinstance(details, dict) and 'filename' in details:
                    attr_lines.append(f"Source: {details['filename']}")
                else:
                    attr_lines.append(f"Source: {source}")
            return " | ".join(attr_lines)
        elif isinstance(source_refs, list):
            return "Sources: " + ", ".join(str(ref) for ref in source_refs)
        else:
            return f"Source: {source_refs}"
    
    def add_source_confidence_indicator(self, slide: Any, data_point_ids: List[str]):
        """Add visual indicators for source confidence levels"""
        if not self.source_tracker or not data_point_ids:
            return
        
        # Validate data consistency across multiple data points
        validation_results = self.source_tracker.validate_data_consistency(data_point_ids)
        
        if not validation_results['consistent']:
            # Add warning indicator for low confidence or inconsistent data
            warning_shape = slide.shapes.add_textbox(
                Inches(8.5), Inches(0.2), Inches(1.3), Inches(0.5)
            )
            warning_frame = warning_shape.text_frame
            warning_frame.text = "⚠ Review Sources"
            
            # Style warning
            for paragraph in warning_frame.paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(8)
                    run.font.color.rgb = RGBColor(255, 140, 0)  # Orange warning
                    run.font.bold = True
    
    def create_chart_slide(self, title: str, chart_type: str, data: Any,
                          chart_options: Dict[str, Any] = None,
                          source_refs: Optional[Dict[str, Any]] = None) -> Any:
        """Create a slide with a chart
        
        Args:
            title: Slide title
            chart_type: Type of chart ('bar', 'line', 'pie', 'waterfall', 'scatter')
            data: Chart data (format depends on chart type)
            chart_options: Additional options for chart generation
            source_refs: Source attribution information
            
        Returns:
            Created slide object
        """
        # Get appropriate layout
        layout = self._get_layout_for_content('chart')
        slide = self.prs.slides.add_slide(layout)
        
        # Add title
        title_shape = self._add_branded_title(slide, title)
        
        # Generate chart based on type
        chart_options = chart_options or {}
        chart_buffer = None
        
        if chart_type == 'bar':
            chart_buffer = self.chart_generator.create_bar_chart(
                data, **chart_options
            )
        elif chart_type == 'line':
            chart_buffer = self.chart_generator.create_line_chart(
                data, **chart_options
            )
        elif chart_type == 'pie':
            chart_buffer = self.chart_generator.create_pie_chart(
                data, **chart_options
            )
        elif chart_type == 'waterfall':
            chart_buffer = self.chart_generator.create_waterfall_chart(
                data, **chart_options
            )
        elif chart_type == 'scatter':
            x_data = data.get('x', [])
            y_data = data.get('y', [])
            chart_buffer = self.chart_generator.create_scatter_plot(
                x_data, y_data, **chart_options
            )
        
        # Add chart image to slide
        if chart_buffer:
            left = Inches(1)
            top = Inches(2)
            height = Inches(4.5)
            
            pic = slide.shapes.add_picture(chart_buffer, left, top, height=height)
            
            # Center the image horizontally
            slide_width = self.prs.slide_width
            pic.left = int((slide_width - pic.width) / 2)
        
        # Add source attribution
        if source_refs:
            self.add_source_attribution(slide, source_refs)
        
        return slide
    
    def create_financial_dashboard_slide(self, financial_data: Dict[str, Any],
                                       source_refs: Optional[Dict[str, Any]] = None) -> Any:
        """Create a financial dashboard slide with multiple charts
        
        Args:
            financial_data: Dictionary containing different financial metrics
            source_refs: Source attribution information
            
        Returns:
            Created slide object
        """
        # Get blank layout for custom positioning
        layout = self._get_layout_for_content('blank')
        slide = self.prs.slides.add_slide(layout)
        
        # Add title
        title_shape = slide.shapes.add_textbox(
            Inches(0.5), Inches(0.3), Inches(9), Inches(0.8)
        )
        title_frame = title_shape.text_frame
        title_frame.text = "Financial Dashboard"
        title_paragraph = title_frame.paragraphs[0]
        self._apply_font_style(title_paragraph, 'heading', size='large')
        title_paragraph.alignment = PP_ALIGN.CENTER
        
        # Create revenue chart (top left)
        if 'revenue' in financial_data:
            revenue_chart = self.chart_generator.create_bar_chart(
                financial_data['revenue'],
                title="Revenue by Quarter",
                size=(4, 3)
            )
            slide.shapes.add_picture(revenue_chart, Inches(0.5), Inches(1.5), height=Inches(2.5))
        
        # Create profit margin chart (top right)
        if 'profit_margin' in financial_data:
            margin_chart = self.chart_generator.create_line_chart(
                {'Profit Margin %': list(financial_data['profit_margin'].values())},
                title="Profit Margin Trend",
                x_values=list(financial_data['profit_margin'].keys()),
                size=(4, 3)
            )
            slide.shapes.add_picture(margin_chart, Inches(5), Inches(1.5), height=Inches(2.5))
        
        # Create expense breakdown (bottom left)
        if 'expenses' in financial_data:
            expense_chart = self.chart_generator.create_pie_chart(
                financial_data['expenses'],
                title="Expense Breakdown",
                show_percentages=True,
                size=(4, 3)
            )
            slide.shapes.add_picture(expense_chart, Inches(0.5), Inches(4.5), height=Inches(2.5))
        
        # Create cash flow waterfall (bottom right)
        if 'cash_flow' in financial_data:
            # Convert to list of tuples for waterfall chart
            cash_flow_data = [(k, v) for k, v in financial_data['cash_flow'].items()]
            waterfall_chart = self.chart_generator.create_waterfall_chart(
                cash_flow_data,
                title="Cash Flow Analysis",
                size=(4, 3)
            )
            slide.shapes.add_picture(waterfall_chart, Inches(5), Inches(4.5), height=Inches(2.5))
        
        # Add source attribution
        if source_refs:
            self.add_source_attribution(slide, source_refs)
        
        return slide
    
    def create_comparison_chart_slide(self, title: str, 
                                    comparison_data: Dict[str, Dict[str, float]],
                                    chart_type: str = 'bar',
                                    source_refs: Optional[Dict[str, Any]] = None) -> Any:
        """Create a slide comparing multiple data series
        
        Args:
            title: Slide title
            comparison_data: Dictionary of series names to data dictionaries
            chart_type: 'bar' or 'line'
            source_refs: Source attribution information
            
        Returns:
            Created slide object
        """
        layout = self._get_layout_for_content('chart')
        slide = self.prs.slides.add_slide(layout)
        
        # Add title
        title_shape = self._add_branded_title(slide, title)
        
        # Prepare data for grouped bar chart or multi-line chart
        if chart_type == 'bar':
            # For grouped bar chart, we need to restructure the data
            # This is a simplified version - in production, you'd use more sophisticated charting
            first_series = next(iter(comparison_data.values()))
            combined_data = {}
            
            for category in first_series.keys():
                values = []
                for series_name in comparison_data.keys():
                    if category in comparison_data[series_name]:
                        values.append(comparison_data[series_name][category])
                combined_data[f"{category}"] = sum(values) / len(values)  # Average for now
            
            chart_buffer = self.chart_generator.create_bar_chart(
                combined_data,
                title="",
                orientation="vertical",
                size=(8, 5)
            )
        else:  # line chart
            chart_buffer = self.chart_generator.create_line_chart(
                comparison_data,
                title="",
                size=(8, 5)
            )
        
        # Add chart to slide
        if chart_buffer:
            left = Inches(1)
            top = Inches(1.8)
            height = Inches(4.7)
            
            pic = slide.shapes.add_picture(chart_buffer, left, top, height=height)
            
            # Center the image
            slide_width = self.prs.slide_width
            pic.left = int((slide_width - pic.width) / 2)
        
        # Add source attribution
        if source_refs:
            self.add_source_attribution(slide, source_refs)
        
        return slide