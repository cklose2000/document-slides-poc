from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
import os
import tempfile
from io import BytesIO

# Import the new branded slide generator, chart generator, and layout engine
try:
    from .slide_generator_branded import BrandedSlideGenerator
    from .template_parser import BrandManager
    from .chart_generator import ChartGenerator
    from .layout_engine import SmartLayoutEngine
    BRANDED_AVAILABLE = True
    CHARTS_AVAILABLE = True
    LAYOUT_ENGINE_AVAILABLE = True
except ImportError:
    try:
        from slide_generator_branded import BrandedSlideGenerator
        from template_parser import BrandManager
        from chart_generator import ChartGenerator
        from layout_engine import SmartLayoutEngine
        BRANDED_AVAILABLE = True
        CHARTS_AVAILABLE = True
        LAYOUT_ENGINE_AVAILABLE = True
    except ImportError:
        BRANDED_AVAILABLE = False
        try:
            from .chart_generator import ChartGenerator
            from .layout_engine import SmartLayoutEngine
            CHARTS_AVAILABLE = True
            LAYOUT_ENGINE_AVAILABLE = True
        except ImportError:
            try:
                from chart_generator import ChartGenerator
                from layout_engine import SmartLayoutEngine
                CHARTS_AVAILABLE = True
                LAYOUT_ENGINE_AVAILABLE = True
            except ImportError:
                CHARTS_AVAILABLE = False
                LAYOUT_ENGINE_AVAILABLE = False

class SlideGenerator:
    def __init__(self, template_path='templates/firm_template.pptx', use_branding=True, 
                 source_tracker=None):
        """Initialize with template or create blank presentation"""
        self.template_path = template_path
        self.use_branding = use_branding and BRANDED_AVAILABLE
        self.source_tracker = source_tracker
        
        # Initialize chart generator if available
        if CHARTS_AVAILABLE:
            self.chart_generator = ChartGenerator()
        else:
            self.chart_generator = None
        
        # Initialize layout engine if available
        if LAYOUT_ENGINE_AVAILABLE:
            self.layout_engine = SmartLayoutEngine()
        else:
            self.layout_engine = None
        
        # Try to use branded generator if available
        if self.use_branding:
            try:
                self.brand_manager = BrandManager()
                # Check if template exists and add it
                if os.path.exists(template_path):
                    template_name = os.path.basename(template_path).replace('.pptx', '')
                    if template_name not in self.brand_manager.list_templates():
                        self.brand_manager.add_template(template_path, template_name)
                    self.brand_manager.set_current_template(template_name)
                
                # Pass source tracker to branded generator
                self.branded_generator = BrandedSlideGenerator(self.brand_manager, source_tracker=self.source_tracker)
                return
            except Exception as e:
                print(f"Warning: Could not initialize branded generator: {e}")
                self.use_branding = False
        
        # Fallback to original implementation
        if os.path.exists(template_path):
            self.prs = Presentation(template_path)
        else:
            # Create blank presentation if template doesn't exist
            self.prs = Presentation()
            self._setup_default_layouts()
    
    def _setup_default_layouts(self):
        """Set up default slide layouts if no template exists"""
        # This creates a basic presentation structure
        # In a real implementation, you'd want to create a proper template
        pass
    
    def create_financial_summary_slide(self, data, source_refs):
        """
        Create a slide with:
        - Title: Company Financial Summary
        - Key metrics in a table
        - Growth chart (if applicable)
        - Small source attribution text at bottom
        """
        # Use branded generator if available
        if self.use_branding:
            return self.branded_generator.create_financial_summary_slide(data, source_refs)
        
        # Get layout recommendation if layout engine is available
        layout_rec = None
        if self.layout_engine and data:
            content_data = {'financial_metrics': data} if isinstance(data, dict) else data
            layout_rec = self.layout_engine.recommend_layout(content_data)
            print(f"SMART LAYOUT ENGINE: {layout_rec.layout_type}")
            print(f"Font sizes: {layout_rec.font_sizes}")
            print(f"Element positions: {layout_rec.element_positions}")
            print(f"Should split: {layout_rec.split_recommendation}")
            print(f"Reasoning: {layout_rec.reasoning}")
            print(f"Data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            print(f"Has table position: {'table' in layout_rec.element_positions}")
            print(f"Has chart position: {'chart' in layout_rec.element_positions}")
        
        # Fallback to original implementation
        # Use blank layout (index 6 is typically blank)
        slide_layout = self.prs.slide_layouts[6] if len(self.prs.slide_layouts) > 6 else self.prs.slide_layouts[-1]
        slide = self.prs.slides.add_slide(slide_layout)
        
        # Add title with smart sizing
        title_font_size = layout_rec.font_sizes.get('title', 36) if layout_rec else 36
        title_shape = slide.shapes.add_textbox(Inches(1), Inches(0.3), Inches(8), Inches(1.2))
        title_frame = title_shape.text_frame
        title_frame.text = "Financial Performance Summary"
        
        # Style the title with layout-aware sizing
        title_paragraph = title_frame.paragraphs[0]
        title_paragraph.font.size = Pt(title_font_size)
        title_paragraph.font.bold = True
        title_paragraph.alignment = PP_ALIGN.CENTER
        title_paragraph.font.color.rgb = RGBColor(37, 64, 97)  # Dark blue
        
        # Use smart layout positioning if available
        if layout_rec and 'table' in layout_rec.element_positions and 'chart' in layout_rec.element_positions:
            # Dashboard layout with table and chart
            print("USING DASHBOARD LAYOUT WITH POSITIONED ELEMENTS!")
            table_pos = layout_rec.element_positions['table']
            chart_pos = layout_rec.element_positions['chart']
            
            # Add metrics table with layout positioning
            if layout_rec.filtered_metrics:
                # Use filtered metrics if available
                print(f"Adding table at position: {table_pos} with {len(layout_rec.filtered_metrics)} filtered metrics")
                self._add_metrics_table_positioned(slide, layout_rec.filtered_metrics, layout_rec, table_pos)
            elif data and isinstance(data, dict):
                print(f"Adding table at position: {table_pos}")
                self._add_metrics_table_positioned(slide, data, layout_rec, table_pos)
            
            # Add chart with layout positioning
            if self.chart_generator:
                if layout_rec.filtered_metrics:
                    print(f"Adding chart at position: {chart_pos} with filtered metrics")
                    self._try_add_chart_positioned(slide, layout_rec.filtered_metrics, layout_rec, chart_pos)
                elif data and isinstance(data, dict):
                    print(f"Adding chart at position: {chart_pos}")
                    self._try_add_chart_positioned(slide, data, layout_rec, chart_pos)
        else:
            # Fallback to original layout logic
            chart_created = False
            if data and isinstance(data, dict) and self.chart_generator:
                chart_created = self._try_add_chart(slide, data, Inches(5.5), Inches(1.8), Inches(4), Inches(3.5))
            
            # Add metrics table (adjust size if chart was added)
            if data and isinstance(data, dict):
                if chart_created:
                    # Smaller table to make room for chart
                    self._add_metrics_table(slide, data, Inches(0.5), Inches(2), table_width=Inches(4.5))
                else:
                    # Full-width table
                    self._add_metrics_table(slide, data, Inches(1), Inches(2))
        
        # Add source attribution
        self.add_source_attribution(slide, source_refs)
        
        return slide
    
    def _add_metrics_table_positioned(self, slide, metrics_data, layout_rec, table_pos):
        """Add a metrics table using smart layout positioning"""
        if not metrics_data:
            return
        
        left, top, width, height = table_pos
        rows = min(len(metrics_data) + 1, 10)  # +1 for header, max 10 rows
        cols = 3  # Metric, Value, Source
        
        # Add table shape with layout positioning
        table_shape = slide.shapes.add_table(
            rows, cols, 
            Inches(left), Inches(top), 
            Inches(width), Inches(height)
        )
        table = table_shape.table
        
        # Set column widths proportionally
        col_width = Inches(width / 3)
        table.columns[0].width = col_width
        table.columns[1].width = col_width
        table.columns[2].width = col_width
        
        # Add headers with layout-aware font sizing
        headers = ['Key Metrics', 'Value', 'Source Document']
        header_font_size = layout_rec.font_sizes.get('body', 14) - 2
        
        for i, header in enumerate(headers):
            cell = table.cell(0, i)
            cell.text = header
            self._style_header_cell(cell, Pt(max(header_font_size, 8)))
        
        # Add data rows with layout-aware styling
        row_idx = 1
        body_font_size = layout_rec.font_sizes.get('body', 14)
        
        for metric_name, metric_info in metrics_data.items():
            if row_idx >= rows:
                break
            
            # Metric name (clean it up)
            # Import the formatter at the top of the method if needed
            try:
                from .layout_engine import MetricsPrioritizer
                clean_name = MetricsPrioritizer.format_metric_name(metric_name)
            except:
                clean_name = str(metric_name).replace('_', ' ').title()
            
            table.cell(row_idx, 0).text = clean_name
            
            # Value (format properly)
            value = metric_info.get('value', 'N/A')
            if isinstance(value, str) and any(c in value.lower() for c in ['m', 'k', '$']):
                formatted_value = f"${value}" if not value.startswith('$') else value
            elif isinstance(value, (int, float)):
                if abs(value) > 1000000:
                    formatted_value = f"${value/1000000:.1f}M"
                elif abs(value) > 1000:
                    formatted_value = f"${value/1000:.0f}K"
                else:
                    formatted_value = f"${value:,.0f}"
            else:
                formatted_value = str(value)
            
            table.cell(row_idx, 1).text = formatted_value
            
            # Source
            source_info = metric_info.get('source', {})
            if isinstance(source_info, dict):
                doc_name = source_info.get('document', 'Unknown')
                if doc_name != 'Unknown':
                    source_text = doc_name.replace('.pdf', '').replace('.xlsx', '').replace('_', ' ').title()
                else:
                    source_text = 'Financial Report'
            else:
                source_text = 'Financial Report'
            
            table.cell(row_idx, 2).text = source_text
            
            # Style data cells with layout-aware font sizes
            for col in range(3):
                cell = table.cell(row_idx, col)
                for paragraph in cell.text_frame.paragraphs:
                    for run in paragraph.runs:
                        run.font.size = Pt(max(body_font_size, 8))
                        if col == 1:  # Value column - make it bold
                            run.font.bold = True
                            run.font.color.rgb = RGBColor(0, 102, 51)  # Dark green
            
            row_idx += 1
    
    def _try_add_chart_positioned(self, slide, data, layout_rec, chart_pos):
        """Try to add a chart using smart layout positioning"""
        if not self.chart_generator:
            return False
        
        try:
            # Prepare chart data from financial metrics
            chart_data = {}
            for metric_name, metric_info in data.items():
                if isinstance(metric_info, dict) and 'value' in metric_info:
                    value = self._extract_numeric_value(metric_info['value'])
                    if value is not None:
                        # Use the same clean name formatter as the table
                        try:
                            from .layout_engine import MetricsPrioritizer
                            clean_name = MetricsPrioritizer.format_metric_name(metric_name)
                        except:
                            clean_name = self._clean_metric_name(metric_name)
                        chart_data[clean_name] = value
            
            # Only create chart if we have 2+ metrics
            if len(chart_data) < 2:
                return False
            
            left, top, width, height = chart_pos
            
            # Generate horizontal bar chart for better readability
            chart_buffer = self.chart_generator.create_bar_chart(
                chart_data,
                title="",  # No title for cleaner look
                x_label="Value ($)",
                y_label="",
                orientation="horizontal",  # Horizontal bars for better metric names
                size=(width, height)
            )
            
            # Save chart to temporary file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                tmp_file.write(chart_buffer.getvalue())
                chart_path = tmp_file.name
            
            # Add chart to slide with layout positioning
            slide.shapes.add_picture(
                chart_path, 
                Inches(left), Inches(top), 
                Inches(width), Inches(height)
            )
            
            # Clean up temporary file
            try:
                os.unlink(chart_path)
            except:
                pass
            
            return True
            
        except Exception as e:
            print(f"Error adding positioned chart to slide: {str(e)}")
            return False
    
    def _add_metrics_table(self, slide, metrics_data, left, top, table_width=Inches(8)):
        """Add a table with key metrics"""
        # Calculate table dimensions based on data
        if not metrics_data:
            return
        
        rows = min(len(metrics_data) + 1, 10)  # +1 for header, max 10 rows
        cols = 3  # Metric, Value, Source
        
        # Add table shape
        table_shape = slide.shapes.add_table(rows, cols, left, top, table_width, Inches(4))
        table = table_shape.table
        
        # Set column widths
        table.columns[0].width = Inches(3)  # Metric name
        table.columns[1].width = Inches(2.5)  # Value
        table.columns[2].width = Inches(2.5)  # Source
        
        # Add headers
        headers = ['Key Metrics', 'Value', 'Source Document']
        for i, header in enumerate(headers):
            cell = table.cell(0, i)
            cell.text = header
            self._style_header_cell(cell)
        
        # Add data rows
        row_idx = 1
        for metric_name, metric_info in metrics_data.items():
            if row_idx >= rows:
                break
            
            # Metric name (clean it up)
            # Import the formatter at the top of the method if needed
            try:
                from .layout_engine import MetricsPrioritizer
                clean_name = MetricsPrioritizer.format_metric_name(metric_name)
            except:
                clean_name = str(metric_name).replace('_', ' ').title()
            
            table.cell(row_idx, 0).text = clean_name
            
            # Value (format properly)
            value = metric_info.get('value', 'N/A')
            if isinstance(value, str) and any(c in value.lower() for c in ['m', 'k', '$']):
                # Already formatted
                formatted_value = f"${value}" if not value.startswith('$') else value
            elif isinstance(value, (int, float)):
                if abs(value) > 1000000:
                    formatted_value = f"${value/1000000:.1f}M"
                elif abs(value) > 1000:
                    formatted_value = f"${value/1000:.0f}K"
                else:
                    formatted_value = f"${value:,.0f}"
            else:
                formatted_value = str(value)
            
            table.cell(row_idx, 1).text = formatted_value
            
            # Source (get proper document name)
            source_info = metric_info.get('source', {})
            if isinstance(source_info, dict):
                doc_name = source_info.get('document', 'Unknown')
                if doc_name != 'Unknown':
                    # Clean up filename
                    source_text = doc_name.replace('.pdf', '').replace('.xlsx', '').replace('_', ' ').title()
                else:
                    source_text = 'Financial Report'
            else:
                source_text = 'Financial Report'
            
            table.cell(row_idx, 2).text = source_text
            
            # Style data cells
            for col in range(3):
                cell = table.cell(row_idx, col)
                for paragraph in cell.text_frame.paragraphs:
                    for run in paragraph.runs:
                        run.font.size = Pt(14)
                        if col == 1:  # Value column - make it bold
                            run.font.bold = True
                            run.font.color.rgb = RGBColor(0, 102, 51)  # Dark green
            
            row_idx += 1
    
    def _style_header_cell(self, cell, font_size=None):
        """Apply styling to header cells"""
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(79, 129, 189)  # Blue background
        
        # Text styling
        for paragraph in cell.text_frame.paragraphs:
            for run in paragraph.runs:
                run.font.color.rgb = RGBColor(255, 255, 255)  # White text
                run.font.bold = True
                run.font.size = font_size if font_size else Pt(12)
    
    def create_company_overview_slide(self, company_data, source_refs):
        """Create a company overview slide"""
        # Use branded generator if available
        if self.use_branding:
            return self.branded_generator.create_company_overview_slide(company_data, source_refs)
        
        # Fallback to original implementation
        slide_layout = self.prs.slide_layouts[6] if len(self.prs.slide_layouts) > 6 else self.prs.slide_layouts[-1]
        slide = self.prs.slides.add_slide(slide_layout)
        
        # Add title with emoji and better styling
        title_shape = slide.shapes.add_textbox(Inches(1), Inches(0.3), Inches(8), Inches(1.2))
        title_frame = title_shape.text_frame
        title_frame.text = "Company Overview"
        
        # Style the title
        title_paragraph = title_frame.paragraphs[0]
        title_paragraph.font.size = Pt(36)
        title_paragraph.font.bold = True
        title_paragraph.alignment = PP_ALIGN.CENTER
        title_paragraph.font.color.rgb = RGBColor(37, 64, 97)  # Dark blue
        
        # Add company info
        if company_data:
            self._add_company_info(slide, company_data, Inches(1), Inches(2))
        
        # Add source attribution
        self.add_source_attribution(slide, source_refs)
        
        return slide
    
    def _add_company_info(self, slide, company_data, left, top):
        """Add company information text box"""
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
        
        info_frame.text = '\n\n'.join(info_lines)
        
        # Style the text
        for paragraph in info_frame.paragraphs:
            paragraph.font.size = Pt(16)
            paragraph.space_after = Pt(12)
    
    def add_source_attribution(self, slide, source_refs):
        """Add small text at bottom with source references"""
        if not source_refs:
            return
        
        # Add attribution text box at bottom of slide
        attr_shape = slide.shapes.add_textbox(
            Inches(0.5), 
            Inches(6.5), 
            Inches(9), 
            Inches(1)
        )
        attr_frame = attr_shape.text_frame
        
        # Build attribution text
        if isinstance(source_refs, dict):
            attr_lines = []
            for source, details in source_refs.items():
                if isinstance(details, dict) and 'filename' in details:
                    attr_lines.append(f"Source: {details['filename']}")
                else:
                    attr_lines.append(f"Source: {source}")
            
            attr_text = " | ".join(attr_lines)
        elif isinstance(source_refs, list):
            attr_text = "Sources: " + ", ".join(str(ref) for ref in source_refs)
        else:
            attr_text = f"Source: {source_refs}"
        
        attr_frame.text = attr_text
        
        # Style attribution text (small and gray)
        for paragraph in attr_frame.paragraphs:
            paragraph.font.size = Pt(8)
            paragraph.font.color.rgb = RGBColor(128, 128, 128)  # Gray
            paragraph.alignment = PP_ALIGN.CENTER
    
    def create_data_insights_slide(self, insights_data, source_refs):
        """Create a slide with key data insights"""
        # Use branded generator if available
        if self.use_branding:
            return self.branded_generator.create_data_insights_slide(insights_data, source_refs)
        
        # Fallback to original implementation
        slide_layout = self.prs.slide_layouts[6] if len(self.prs.slide_layouts) > 6 else self.prs.slide_layouts[-1]
        slide = self.prs.slides.add_slide(slide_layout)
        
        # Add title with emoji and better styling
        title_shape = slide.shapes.add_textbox(Inches(1), Inches(0.3), Inches(8), Inches(1.2))
        title_frame = title_shape.text_frame
        title_frame.text = "Key Business Insights"
        
        # Style the title
        title_paragraph = title_frame.paragraphs[0]
        title_paragraph.font.size = Pt(36)
        title_paragraph.font.bold = True
        title_paragraph.alignment = PP_ALIGN.CENTER
        title_paragraph.font.color.rgb = RGBColor(37, 64, 97)  # Dark blue
        
        # Add insights as bullet points
        if insights_data:
            self._add_insights_bullets(slide, insights_data, Inches(1), Inches(2))
        
        # Add source attribution
        self.add_source_attribution(slide, source_refs)
        
        return slide
    
    def _add_insights_bullets(self, slide, insights, left, top):
        """Add insights as bullet points with better styling"""
        bullets_shape = slide.shapes.add_textbox(left, top, Inches(8), Inches(4))
        bullets_frame = bullets_shape.text_frame
        bullets_frame.margin_left = Inches(0.2)
        bullets_frame.margin_top = Inches(0.1)
        
        if isinstance(insights, list):
            for i, insight in enumerate(insights):
                if i == 0:
                    bullets_frame.text = f"• {insight}"
                    # Style first paragraph
                    p = bullets_frame.paragraphs[0]
                    p.font.size = Pt(18)
                    p.font.bold = True
                    p.space_after = Pt(12)
                    p.font.color.rgb = RGBColor(37, 64, 97)  # Dark blue
                else:
                    p = bullets_frame.add_paragraph()
                    p.text = f"• {insight}"
                    p.font.size = Pt(18)
                    p.font.bold = True
                    p.space_before = Pt(8)
                    p.space_after = Pt(8)
                    p.font.color.rgb = RGBColor(37, 64, 97)  # Dark blue
        elif isinstance(insights, dict):
            first = True
            i = 0
            for key, value in insights.items():
                text = f"• {key}: {value}"
                if first:
                    bullets_frame.text = text
                    p = bullets_frame.paragraphs[0]
                    first = False
                else:
                    p = bullets_frame.add_paragraph()
                    p.text = text
                
                p.font.size = Pt(18)
                p.font.bold = True
                p.space_before = Pt(8)
                p.space_after = Pt(8)
                p.font.color.rgb = RGBColor(37, 64, 97)  # Dark blue
                i += 1
    
    def _try_add_chart(self, slide, data, left, top, width, height):
        """Try to add a chart to the slide based on financial data"""
        if not self.chart_generator:
            return False
        
        try:
            # Prepare chart data from financial metrics
            chart_data = {}
            for metric_name, metric_info in data.items():
                if isinstance(metric_info, dict) and 'value' in metric_info:
                    value = self._extract_numeric_value(metric_info['value'])
                    if value is not None:
                        clean_name = self._clean_metric_name(metric_name)
                        chart_data[clean_name] = value
            
            # Only create chart if we have 2+ metrics
            if len(chart_data) < 2:
                return False
            
            # Generate chart
            chart_buffer = self.chart_generator.create_bar_chart(
                chart_data,
                title="Key Metrics",
                y_label="Value ($)",
                size=(width.inches, height.inches)
            )
            
            # Save chart to temporary file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                tmp_file.write(chart_buffer.getvalue())
                chart_path = tmp_file.name
            
            # Add chart to slide
            slide.shapes.add_picture(chart_path, left, top, width, height)
            
            # Clean up temporary file
            try:
                os.unlink(chart_path)
            except:
                pass
            
            return True
            
        except Exception as e:
            print(f"Error adding chart to slide: {str(e)}")
            return False
    
    def _extract_numeric_value(self, value_str):
        """Extract numeric value from string (handles $, M, K, etc.)"""
        if not value_str:
            return None
        
        import re
        value_str = str(value_str).strip()
        
        # Remove currency symbols and spaces
        cleaned = re.sub(r'[$,\s]', '', value_str)
        
        # Handle multipliers
        multiplier = 1
        if cleaned.lower().endswith('m'):
            multiplier = 1_000_000
            cleaned = cleaned[:-1]
        elif cleaned.lower().endswith('k'):
            multiplier = 1_000
            cleaned = cleaned[:-1]
        elif cleaned.lower().endswith('b'):
            multiplier = 1_000_000_000
            cleaned = cleaned[:-1]
        
        # Extract number
        number_match = re.search(r'([\d.]+)', cleaned)
        if number_match:
            try:
                return float(number_match.group(1)) * multiplier
            except ValueError:
                return None
        
        return None
    
    def _clean_metric_name(self, name):
        """Clean and format metric names for display"""
        # Remove underscores and capitalize
        cleaned = name.replace('_', ' ').title()
        
        # Handle common abbreviations
        replacements = {
            'Yoy': 'YoY',
            'Roi': 'ROI',
            'Ebitda': 'EBITDA',
            'Arr': 'ARR',
            'Mrr': 'MRR'
        }
        
        for old, new in replacements.items():
            cleaned = cleaned.replace(old, new)
        
        return cleaned
    
    def save_presentation(self, output_path):
        """Save the presentation to specified path"""
        # Use branded generator if available
        if self.use_branding:
            return self.branded_generator.save_presentation(output_path)
        
        # Fallback to original implementation
        self.prs.save(output_path)
        return output_path