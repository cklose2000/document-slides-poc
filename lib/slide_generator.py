from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
import os

class SlideGenerator:
    def __init__(self):
        self.prs = Presentation()
        self._setup_slide_layouts()
    
    def _setup_slide_layouts(self):
        """Setup basic slide layouts"""
        # In production, would load custom templates
        pass
    
    def create_title_slide(self, title, subtitle):
        """Create a title slide"""
        slide_layout = self.prs.slide_layouts[0]  # Title slide layout
        slide = self.prs.slides.add_slide(slide_layout)
        
        title_shape = slide.shapes.title
        subtitle_shape = slide.placeholders[1]
        
        title_shape.text = title
        subtitle_shape.text = subtitle
        
        return slide
    
    def create_company_overview_slide(self, company_data, attribution):
        """Create a company overview slide"""
        slide_layout = self.prs.slide_layouts[1]  # Title and content layout
        slide = self.prs.slides.add_slide(slide_layout)
        
        title = slide.shapes.title
        title.text = company_data.get('name', 'Company Overview')
        
        content = slide.placeholders[1]
        tf = content.text_frame
        tf.text = company_data.get('description', 'No description available')
        
        # Add attribution footer
        left = Inches(0.5)
        top = Inches(6.5)
        width = Inches(9)
        height = Inches(0.5)
        
        textbox = slide.shapes.add_textbox(left, top, width, height)
        text_frame = textbox.text_frame
        p = text_frame.paragraphs[0]
        p.text = f"Source: {attribution.get('summary', 'Multiple documents')}"
        p.font.size = Pt(10)
        p.font.italic = True
        
        return slide
    
    def create_financial_summary_slide(self, financial_data, attribution):
        """Create a financial summary slide"""
        slide_layout = self.prs.slide_layouts[5]  # Blank layout
        slide = self.prs.slides.add_slide(slide_layout)
        
        # Add title
        left = Inches(0.5)
        top = Inches(0.5)
        width = Inches(9)
        height = Inches(1)
        
        title_box = slide.shapes.add_textbox(left, top, width, height)
        title_frame = title_box.text_frame
        p = title_frame.paragraphs[0]
        p.text = "Financial Summary"
        p.font.size = Pt(32)
        p.font.bold = True
        
        # Add metrics
        top = Inches(2)
        for key, value in list(financial_data.items())[:5]:  # Show top 5 metrics
            metric_box = slide.shapes.add_textbox(left, top, width, Inches(0.5))
            text_frame = metric_box.text_frame
            p = text_frame.paragraphs[0]
            p.text = f"{key}: {value}"
            p.font.size = Pt(18)
            top += Inches(0.7)
        
        return slide
    
    def create_data_insights_slide(self, insights, attribution):
        """Create a key insights slide"""
        slide_layout = self.prs.slide_layouts[1]
        slide = self.prs.slides.add_slide(slide_layout)
        
        title = slide.shapes.title
        title.text = "Key Insights"
        
        content = slide.placeholders[1]
        tf = content.text_frame
        
        for i, insight in enumerate(insights[:5]):  # Show top 5 insights
            if i == 0:
                tf.text = f"• {insight}"
            else:
                p = tf.add_paragraph()
                p.text = f"• {insight}"
                p.level = 0
        
        return slide
    
    def save_presentation(self, filename):
        """Save the presentation to a file"""
        self.prs.save(filename)
        return filename