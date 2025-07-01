#!/usr/bin/env python3
"""
Test the branded slide generator to isolate PowerPoint corruption
"""

import sys
import os
sys.path.append('/mnt/c/Users/cklos/document-slides-poc/lib')

from slide_generator_branded import BrandedSlideGenerator
from template_parser import BrandManager
from source_tracker import SourceTracker

def test_branded_generation():
    """Test branded slide generation that matches API flow"""
    
    print("🧪 Testing Branded Slide Generation...")
    
    try:
        # Initialize components like the API does
        source_tracker = SourceTracker()
        brand_manager = BrandManager()
        
        # Create branded slide generator with available template
        templates = brand_manager.list_templates()
        template_name = 'sample_brand' if 'sample_brand' in templates else (templates[0] if templates else None)
        
        if not template_name:
            print("❌ No templates available")
            return False
            
        print(f"   Using template: {template_name}")
        generator = BrandedSlideGenerator(
            brand_manager=brand_manager,
            template_name=template_name,
            source_tracker=source_tracker
        )
        print("✅ Branded generator initialized")
        
        # Create title slide
        print("   Creating title slide...")
        title_slide = generator.create_title_slide(
            title="Test Company",
            subtitle="Financial Analysis & Performance Review"
        )
        print("   ✅ Title slide created")
        
        # Test financial metrics
        test_metrics = {
            "Revenue": {"value": 15000000, "source": {"document": "test.xlsx"}},
            "Profit": {"value": 3000000, "source": {"document": "test.xlsx"}},
            "Growth": {"value": 23.5, "source": {"document": "test.xlsx"}},
            "Customers": {"value": 450, "source": {"document": "test.xlsx"}}
        }
        
        # Create financial summary
        print("   Creating financial summary slide...")
        financial_slide = generator.create_financial_summary_slide(
            test_metrics,
            {"primary_documents": ["test.xlsx"]}
        )
        print("   ✅ Financial summary created")
        
        # Create executive dashboard
        if hasattr(generator, 'create_executive_dashboard'):
            print("   Creating executive dashboard...")
            dashboard_slide = generator.create_executive_dashboard(test_metrics)
            print("   ✅ Executive dashboard created")
        
        # Create multi-chart analysis
        if hasattr(generator, 'create_multi_chart_analysis'):
            print("   Creating multi-chart analysis...")
            chart_slide = generator.create_multi_chart_analysis({})
            print("   ✅ Multi-chart analysis created")
        
        # Create timeline roadmap
        if hasattr(generator, 'create_timeline_roadmap'):
            print("   Creating timeline roadmap...")
            timeline_slide = generator.create_timeline_roadmap()
            print("   ✅ Timeline roadmap created")
        
        # Create SWOT analysis
        if hasattr(generator, 'create_swot_analysis'):
            print("   Creating SWOT analysis...")
            swot_slide = generator.create_swot_analysis()
            print("   ✅ SWOT analysis created")
        
        # Create comparison matrix
        if hasattr(generator, 'create_comparison_matrix'):
            print("   Creating comparison matrix...")
            comparison_slide = generator.create_comparison_matrix()
            print("   ✅ Comparison matrix created")
        
        # Add slide numbers
        generator.add_slide_numbers(exclude_first=True, exclude_last=True)
        
        # Save presentation
        output_path = "branded_test_output.pptx"
        generator.save_presentation(output_path)
        
        # Check file size
        file_size = os.path.getsize(output_path)
        print(f"\n📊 File size: {file_size:,} bytes")
        
        if file_size < 10000:
            print("⚠️  Warning: File size seems small, possible corruption")
            return False
        
        print("🎉 All branded generation tests passed!")
        print(f"📁 Test file: {output_path}")
        return True
        
    except Exception as e:
        import traceback
        print(f"❌ Branded generation failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("🔧 Branded Slide Generator Test")
    print("=" * 50)
    
    success = test_branded_generation()
    
    if success:
        print("\n✅ SUCCESS: Branded generation test completed!")
        print("💡 Open 'branded_test_output.pptx' to check for corruption.")
    else:
        print("\n❌ FAILURE: Branded generation test failed.")
    
    exit(0 if success else 1)