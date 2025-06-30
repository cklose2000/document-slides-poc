"""
Create a simple working PowerPoint template
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
import os

def create_simple_template(output_path: str = 'templates/simple_template.pptx'):
    """Create a simple working template"""
    
    # Create new presentation 
    prs = Presentation()
    
    # Just save the basic presentation with default layouts
    # This avoids any complex slide manipulation issues
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save template
    prs.save(output_path)
    print(f"Simple template created: {output_path}")
    
    return output_path

if __name__ == "__main__":
    create_simple_template()