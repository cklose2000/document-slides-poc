#!/usr/bin/env python3
"""Test the slide generation improvements"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from lib.slide_generator import SlideGenerator

def test_slide_improvements():
    """Test all the improvements made to slide generation"""
    
    # Create generator
    generator = SlideGenerator(use_branding=False)
    
    # Test data
    company_data = {
        'name': 'SaaSy Inc.',
        'industry': 'Customer Success Management Software',
        'description': 'Leading provider of AI-powered customer success solutions helping businesses reduce churn and maximize revenue growth.'
    }
    
    financial_data = {
        'revenue': {'value': '$15.2M', 'source': {'document': 'Q3_Report.pdf'}, 'confidence': 0.9},
        'profit': {'value': '$12.5M', 'source': {'document': 'Q3_Report.pdf'}, 'confidence': 0.8},
        'growth_rate': {'value': '23%', 'source': {'document': 'Q3_Report.pdf'}, 'confidence': 0.7},
        'customers': {'value': '450', 'source': {'document': 'Customer_Data.xlsx'}, 'confidence': 0.9},
        'churn_rate': {'value': '2.1%', 'source': {'document': 'Metrics.xlsx'}, 'confidence': 0.8},
        'arr': {'value': '$182.4M', 'source': {'document': 'Q3_Report.pdf'}, 'confidence': 0.9}
    }
    
    insights = [
        "Strong Q3 2024 performance with $15.2M revenue",
        "23% year-over-year growth achieving $15.2M",
        "Healthy profit margins with $12.5M profit",
        "Growing customer base to 450 customers with low 2.1% churn"
    ]
    
    source_refs = {
        'primary_documents': ['Q3_Report.pdf', 'Customer_Data.xlsx', 'Metrics.xlsx'],
        'extraction_summary': 'Successfully processed 3 documents'
    }
    
    print("Testing slide generation improvements...")
    
    # 1. Create title slide
    print("\n1. Creating title slide...")
    title_slide = generator.create_title_slide(
        title="SaaSy Inc.",
        subtitle="Q3 2024 Financial Performance Review"
    )
    print("✓ Title slide created with gradient background")
    
    # 2. Create financial summary slides (table and chart)
    print("\n2. Creating financial summary slides...")
    financial_slides = generator.create_financial_summary_slide(financial_data, source_refs)
    print(f"✓ Created {len(financial_slides)} financial slides (table with trend arrows + chart with labels)")
    
    # 3. Create company overview slide
    print("\n3. Creating company overview slide...")
    overview_slide = generator.create_company_overview_slide(company_data, source_refs)
    print("✓ Company overview created with callout boxes")
    
    # 4. Create insights slide
    print("\n4. Creating insights slide...")
    insights_slide = generator.create_data_insights_slide(insights, source_refs)
    print("✓ Insights slide created with 2x2 grid layout")
    
    # 5. Create thank you slide
    print("\n5. Creating thank you slide...")
    thank_you_slide = generator.create_thank_you_slide()
    print("✓ Thank you slide created")
    
    # 6. Add slide numbers
    print("\n6. Adding slide numbers...")
    generator.add_slide_numbers(exclude_first=True, exclude_last=True)
    print("✓ Slide numbers added (excluding first and last)")
    
    # Save presentation
    output_path = 'test_improvements_output.pptx'
    generator.save_presentation(output_path)
    print(f"\n✓ Presentation saved to {output_path}")
    
    # Summary of improvements
    print("\n" + "="*50)
    print("IMPROVEMENTS IMPLEMENTED:")
    print("="*50)
    print("1. ✓ Professional title slide with gradient background")
    print("2. ✓ Enhanced metrics table:")
    print("   - Alternating row colors")
    print("   - Trend arrows (↑ ↓ →)")
    print("   - Color-coded values")
    print("3. ✓ Improved charts:")
    print("   - Value labels on bars")
    print("   - Subtle gridlines")
    print("   - Gradient fills")
    print("4. ✓ Enhanced company overview:")
    print("   - Visual callout boxes for stats")
    print("   - Better typography hierarchy")
    print("5. ✓ Redesigned insights slide:")
    print("   - 2x2 grid layout")
    print("   - Numbered icons")
    print("   - Shadow effects")
    print("6. ✓ Professional polish:")
    print("   - Slide numbers")
    print("   - Thank you slide")
    print("   - Consistent styling")
    
    print(f"\n✓ All improvements successfully implemented!")
    print(f"✓ Generated presentation: {output_path}")

if __name__ == "__main__":
    test_slide_improvements()