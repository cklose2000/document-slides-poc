from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
import os

# Import the new branded slide generator
try:
    from .slide_generator_branded import BrandedSlideGenerator
    from .template_parser import BrandManager
    BRANDED_AVAILABLE = True
except ImportError:
    try:
        from slide_generator_branded import BrandedSlideGenerator
        from template_parser import BrandManager
        BRANDED_AVAILABLE = True
    except ImportError:
        BRANDED_AVAILABLE = False

class SlideGenerator:
    def __init__(self, template_path='templates/firm_template.pptx', use_branding=True, 
                 source_tracker=None):
        """Initialize with template or create blank presentation"""
        self.template_path = template_path
        self.use_branding = use_branding and BRANDED_AVAILABLE
        self.source_tracker = source_tracker
        
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
        
        # Fallback to original implementation
        # Use blank layout (index 6 is typically blank)
        slide_layout = self.prs.slide_layouts[6] if len(self.prs.slide_layouts) > 6 else self.prs.slide_layouts[-1]
        slide = self.prs.slides.add_slide(slide_layout)
        
        # Add title
        title_shape = slide.shapes.add_textbox(Inches(1), Inches(0.5), Inches(8), Inches(1))
        title_frame = title_shape.text_frame
        title_frame.text = "Financial Summary"
        
        # Style the title
        title_paragraph = title_frame.paragraphs[0]
        title_paragraph.font.size = Pt(32)
        title_paragraph.font.bold = True
        title_paragraph.alignment = PP_ALIGN.CENTER
        
        # Add metrics table
        if data and isinstance(data, dict):
            self._add_metrics_table(slide, data, Inches(1), Inches(2))
        
        # Add source attribution
        self.add_source_attribution(slide, source_refs)
        
        return slide
    
    def _add_metrics_table(self, slide, metrics_data, left, top):
        """Add a table with key metrics"""
        # Calculate table dimensions based on data
        if not metrics_data:
            return
        
        rows = min(len(metrics_data) + 1, 10)  # +1 for header, max 10 rows
        cols = 3  # Metric, Value, Source
        
        # Add table shape
        table_shape = slide.shapes.add_table(rows, cols, left, top, Inches(8), Inches(4))
        table = table_shape.table
        
        # Set column widths
        table.columns[0].width = Inches(3)  # Metric name
        table.columns[1].width = Inches(2)  # Value
        table.columns[2].width = Inches(3)  # Source
        
        # Add headers
        headers = ['Metric', 'Value', 'Source']
        for i, header in enumerate(headers):
            cell = table.cell(0, i)
            cell.text = header
            self._style_header_cell(cell)
        
        # Add data rows
        row_idx = 1
        for metric_name, metric_info in metrics_data.items():
            if row_idx >= rows:
                break
            
            # Metric name
            table.cell(row_idx, 0).text = str(metric_name)
            
            # Value
            value = metric_info.get('value', 'N/A')
            if isinstance(value, (int, float)):
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
            cell_ref = metric_info.get('cell', 'Unknown')
            source_text = f"Cell {cell_ref}"
            table.cell(row_idx, 2).text = source_text
            
            row_idx += 1
    
    def _style_header_cell(self, cell):
        """Apply styling to header cells"""
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(79, 129, 189)  # Blue background
        
        # Text styling
        for paragraph in cell.text_frame.paragraphs:
            for run in paragraph.runs:
                run.font.color.rgb = RGBColor(255, 255, 255)  # White text
                run.font.bold = True
                run.font.size = Pt(12)
    
    def create_company_overview_slide(self, company_data, source_refs):
        """Create a company overview slide"""
        # Use branded generator if available
        if self.use_branding:
            return self.branded_generator.create_company_overview_slide(company_data, source_refs)
        
        # Fallback to original implementation
        slide_layout = self.prs.slide_layouts[6] if len(self.prs.slide_layouts) > 6 else self.prs.slide_layouts[-1]
        slide = self.prs.slides.add_slide(slide_layout)
        
        # Add title
        title_shape = slide.shapes.add_textbox(Inches(1), Inches(0.5), Inches(8), Inches(1))
        title_frame = title_shape.text_frame
        title_frame.text = "Company Overview"
        
        # Style the title
        title_paragraph = title_frame.paragraphs[0]
        title_paragraph.font.size = Pt(32)
        title_paragraph.font.bold = True
        title_paragraph.alignment = PP_ALIGN.CENTER
        
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
        
        # Add title
        title_shape = slide.shapes.add_textbox(Inches(1), Inches(0.5), Inches(8), Inches(1))
        title_frame = title_shape.text_frame
        title_frame.text = "Key Insights"
        
        # Style the title
        title_paragraph = title_frame.paragraphs[0]
        title_paragraph.font.size = Pt(32)
        title_paragraph.font.bold = True
        title_paragraph.alignment = PP_ALIGN.CENTER
        
        # Add insights as bullet points
        if insights_data:
            self._add_insights_bullets(slide, insights_data, Inches(1), Inches(2))
        
        # Add source attribution
        self.add_source_attribution(slide, source_refs)
        
        return slide
    
    def _add_insights_bullets(self, slide, insights, left, top):
        """Add insights as bullet points"""
        bullets_shape = slide.shapes.add_textbox(left, top, Inches(8), Inches(4))
        bullets_frame = bullets_shape.text_frame
        
        if isinstance(insights, list):
            for i, insight in enumerate(insights):
                if i == 0:
                    bullets_frame.text = f"• {insight}"
                else:
                    p = bullets_frame.add_paragraph()
                    p.text = f"• {insight}"
                    p.font.size = Pt(16)
                    p.space_before = Pt(6)
        elif isinstance(insights, dict):
            first = True
            for key, value in insights.items():
                text = f"• {key}: {value}"
                if first:
                    bullets_frame.text = text
                    first = False
                else:
                    p = bullets_frame.add_paragraph()
                    p.text = text
                    p.font.size = Pt(16)
                    p.space_before = Pt(6)
    
    def save_presentation(self, output_path):
        """Save the presentation to specified path"""
        # Use branded generator if available
        if self.use_branding:
            return self.branded_generator.save_presentation(output_path)
        
        # Fallback to original implementation
        self.prs.save(output_path)
        return output_path
