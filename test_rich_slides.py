#!/usr/bin/env python3
"""Test rich slide generation directly"""

from pptx import Presentation
from lib.slide_generator_branded import BrandedSlideGenerator
from lib.template_parser import BrandManager

def test_rich_slides():
    """Test generating rich slides"""
    
    print("🎨 Testing Rich Slide Generation")
    print("=" * 50)
    
    # Initialize branded generator
    brand_manager = BrandManager()
    generator = BrandedSlideGenerator(brand_manager)
    
    # Create title slide
    print("Creating title slide...")
    title_slide = generator.create_title_slide(
        title="Q4 2024 Business Review",
        subtitle="Financial Performance & Strategic Outlook"
    )
    
    # Create executive dashboard
    print("Creating executive dashboard...")
    metrics = {
        'revenue': {'value': '$12.5M', 'change': '+15%'},
        'margin': {'value': '42.3%', 'change': '+2.1%'},
        'profit': {'value': '$3.8M', 'change': '+22%'}
    }
    dashboard_slide = generator.create_executive_dashboard(metrics)
    
    # Create multi-chart analysis
    print("Creating multi-chart analysis...")
    chart_data = {
        'revenue_trend': [10.2, 11.5, 12.8, 14.2],
        'expense_breakdown': {'Operations': 45, 'Marketing': 25, 'R&D': 20, 'Admin': 10}
    }
    analysis_slide = generator.create_multi_chart_analysis(chart_data)
    
    # Create timeline roadmap
    print("Creating timeline roadmap...")
    timeline_slide = generator.create_timeline_roadmap()
    
    # Create SWOT analysis
    print("Creating SWOT analysis...")
    swot_slide = generator.create_swot_analysis()
    
    # Create competitive analysis
    print("Creating competitive analysis...")
    comparison_slide = generator.create_comparison_matrix()
    
    # Create thank you slide
    print("Creating thank you slide...")
    thank_you_slide = generator.create_thank_you_slide()
    
    # Add slide numbers
    print("Adding slide numbers...")
    generator.add_slide_numbers(exclude_first=True, exclude_last=True)
    
    # Save presentation
    output_path = "test_rich_slides_output.pptx"
    generator.save_presentation(output_path)
    
    print(f"\n✅ Presentation saved as: {output_path}")
    print(f"📊 Total slides: {len(generator.prs.slides)}")
    print("\nSlides created:")
    print("  1. Title Slide")
    print("  2. Executive Dashboard")
    print("  3. Multi-Chart Financial Analysis")
    print("  4. Strategic Roadmap Timeline")
    print("  5. SWOT Analysis")
    print("  6. Competitive Analysis Matrix")
    print("  7. Thank You")
    
    return True

if __name__ == "__main__":
    try:
        test_rich_slides()
        print("\n🎉 Rich slides test completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()