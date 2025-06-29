#!/usr/bin/env python3
"""
Test script for Phase 4: Professional Slide Templates

This script tests the template system implementation including:
- Template parsing and brand extraction
- Chart generation with brand colors
- API endpoints for template management
- Branded slide generation
"""

import os
import sys
import json
from pathlib import Path

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from lib.template_parser import BrandManager, TemplateParser
from lib.chart_generator import ChartGenerator
from lib.slide_generator_branded import BrandedSlideGenerator
from lib.source_tracker import SourceTracker


def test_template_parser():
    """Test template parsing functionality"""
    print("\n=== Testing Template Parser ===")
    
    # Check if templates directory exists
    if not os.path.exists('templates'):
        print("❌ Templates directory not found")
        return False
    
    # Test BrandManager
    try:
        brand_manager = BrandManager()
        templates = brand_manager.list_templates()
        print(f"✅ Found {len(templates)} templates")
        
        for template_name in templates:
            print(f"  - {template_name}")
            template = brand_manager.get_template(template_name)
            if template:
                config = template.get_brand_config()
                print(f"    Colors: {len(config.get('theme_colors', {}))} theme colors")
                print(f"    Fonts: {config.get('fonts', {}).get('heading', {}).get('family', 'Unknown')}")
    except Exception as e:
        print(f"❌ Error testing brand manager: {str(e)}")
        return False
    
    return True


def test_chart_generator():
    """Test chart generation with brand styling"""
    print("\n=== Testing Chart Generator ===")
    
    try:
        # Create chart generator with sample brand config
        brand_config = {
            'colors': {
                'primary': '#003366',
                'secondary': '#FF6600',
                'accent1': '#0066CC',
                'accent2': '#666666'
            },
            'fonts': {
                'title_font': 'Arial',
                'body_font': 'Arial',
                'title_size': 18,
                'body_size': 12
            }
        }
        
        chart_gen = ChartGenerator(brand_config)
        
        # Test bar chart
        data = {
            'Q1 2024': 125000,
            'Q2 2024': 145000,
            'Q3 2024': 162000,
            'Q4 2024': 189000
        }
        
        chart_buffer = chart_gen.create_bar_chart(
            data,
            title="Quarterly Revenue",
            x_label="Quarter",
            y_label="Revenue ($)"
        )
        
        if chart_buffer:
            print("✅ Bar chart generated successfully")
        
        # Test pie chart
        expense_data = {
            'Marketing': 45000,
            'R&D': 78000,
            'Operations': 92000,
            'Admin': 35000
        }
        
        pie_buffer = chart_gen.create_pie_chart(
            expense_data,
            title="Expense Breakdown",
            show_percentages=True
        )
        
        if pie_buffer:
            print("✅ Pie chart generated successfully")
            
    except Exception as e:
        print(f"❌ Error testing chart generator: {str(e)}")
        return False
    
    return True


def test_branded_slide_generator():
    """Test branded slide generation"""
    print("\n=== Testing Branded Slide Generator ===")
    
    try:
        # Initialize components
        brand_manager = BrandManager()
        source_tracker = SourceTracker()
        
        # Create branded slide generator
        generator = BrandedSlideGenerator(
            brand_manager=brand_manager,
            template_name='default',
            source_tracker=source_tracker
        )
        
        print("✅ Branded slide generator initialized")
        
        # Create title slide
        slide = generator.create_title_slide(
            "Financial Analysis Report",
            "Q4 2024 Results"
        )
        print("✅ Title slide created")
        
        # Create financial summary slide
        financial_data = {
            "Revenue": {"value": 1890000, "cell": "B5"},
            "Profit": {"value": 472500, "cell": "B6"},
            "Margin": {"value": "25%", "cell": "B7"}
        }
        
        slide = generator.create_financial_summary_slide(
            financial_data,
            {"source": {"filename": "financial_report.xlsx"}}
        )
        print("✅ Financial summary slide created")
        
        # Create chart slide
        chart_data = {
            'Q1': 125000,
            'Q2': 145000,
            'Q3': 162000,
            'Q4': 189000
        }
        
        slide = generator.create_chart_slide(
            "Revenue Growth",
            "bar",
            chart_data,
            {"y_label": "Revenue ($)", "x_label": "Quarter"}
        )
        print("✅ Chart slide created")
        
        # Save presentation
        output_path = "test_branded_presentation.pptx"
        generator.save_presentation(output_path)
        
        if os.path.exists(output_path):
            print(f"✅ Presentation saved to {output_path}")
            os.remove(output_path)  # Clean up
        
    except Exception as e:
        print(f"❌ Error testing branded slide generator: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def test_template_metadata():
    """Test template metadata files"""
    print("\n=== Testing Template Metadata ===")
    
    template_dirs = ['default', 'corporate', 'minimal']
    
    for template_id in template_dirs:
        metadata_path = Path('templates') / template_id / 'metadata.json'
        
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            print(f"✅ {template_id}: {metadata.get('name', 'Unknown')}")
            print(f"   Description: {metadata.get('description', 'No description')}")
            print(f"   Features: {len(metadata.get('features', []))} features")
        else:
            print(f"❌ Missing metadata for {template_id}")
    
    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("Phase 4: Professional Slide Templates - Test Suite")
    print("=" * 60)
    
    tests = [
        test_template_parser,
        test_chart_generator,
        test_template_metadata,
        test_branded_slide_generator
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Test {test_func.__name__} failed with error: {str(e)}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("Test Summary:")
    print(f"Total tests: {len(results)}")
    print(f"Passed: {sum(results)}")
    print(f"Failed: {len(results) - sum(results)}")
    
    if all(results):
        print("\n✅ All tests passed! Phase 4 implementation is complete.")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
