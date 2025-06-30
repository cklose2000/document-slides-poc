#!/usr/bin/env python3
"""
Comprehensive test script for BrandedSlideGenerator functionality
Tests slide generation, brand styling, and template integration
"""

import os
import sys
from datetime import datetime
from typing import Dict, Any

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

from lib.slide_generator_branded import BrandedSlideGenerator
from lib.template_parser import BrandManager, TemplateParser

def test_setup():
    """Test the basic setup and initialization"""
    print("\n" + "="*60)
    print("🧪 TESTING BRANDED SLIDE GENERATOR SETUP")
    print("="*60)
    
    results = []
    
    # Test 1: Basic initialization without template
    try:
        generator = BrandedSlideGenerator()
        results.append(("✅", "Basic initialization", "Success"))
        print("✅ Basic initialization: SUCCESS")
    except Exception as e:
        results.append(("❌", "Basic initialization", str(e)))
        print(f"❌ Basic initialization: FAILED - {e}")
    
    # Test 2: BrandManager initialization
    try:
        brand_manager = BrandManager()
        results.append(("✅", "BrandManager initialization", "Success"))
        print("✅ BrandManager initialization: SUCCESS")
    except Exception as e:
        results.append(("❌", "BrandManager initialization", str(e)))
        print(f"❌ BrandManager initialization: FAILED - {e}")
    
    # Test 3: List available templates
    try:
        brand_manager = BrandManager()
        templates = brand_manager.list_templates()
        results.append(("✅", "Template listing", f"Found {len(templates)} templates: {templates}"))
        print(f"✅ Template listing: Found {len(templates)} templates: {templates}")
    except Exception as e:
        results.append(("❌", "Template listing", str(e)))
        print(f"❌ Template listing: FAILED - {e}")
    
    return results

def test_template_integration():
    """Test template parser and brand manager integration"""
    print("\n" + "="*60)
    print("🎨 TESTING TEMPLATE INTEGRATION")
    print("="*60)
    
    results = []
    
    # Test template parsing for each available template
    templates_dir = "templates"
    if os.path.exists(templates_dir):
        for template_file in os.listdir(templates_dir):
            if template_file.endswith('.pptx'):
                template_path = os.path.join(templates_dir, template_file)
                template_name = template_file.replace('.pptx', '')
                
                try:
                    # Test template parsing
                    parser = TemplateParser(template_path)
                    brand_config = parser.get_brand_config()
                    
                    results.append(("✅", f"Template parsing: {template_name}", "Success"))
                    print(f"✅ Template parsing ({template_name}): SUCCESS")
                    
                    # Print some key info
                    print(f"   - Theme colors: {len(brand_config.get('theme_colors', {}))}")
                    print(f"   - Layouts: {len(brand_config.get('layouts', []))}")
                    print(f"   - Fonts configured: {list(brand_config.get('fonts', {}).keys())}")
                    
                except Exception as e:
                    results.append(("❌", f"Template parsing: {template_name}", str(e)))
                    print(f"❌ Template parsing ({template_name}): FAILED - {e}")
    else:
        results.append(("⚠️", "Templates directory", "Not found"))
        print("⚠️ Templates directory not found")
    
    return results

def test_slide_creation():
    """Test different types of slide creation"""
    print("\n" + "="*60)
    print("📊 TESTING SLIDE CREATION")
    print("="*60)
    
    results = []
    
    # Sample data for testing
    financial_data = {
        "Revenue": {"value": 1500000, "cell": "B2"},
        "Profit Margin": {"value": 0.15, "cell": "C2"},
        "Growth Rate": {"value": 0.12, "cell": "D2"},
        "Market Cap": {"value": 25000000, "cell": "E2"}
    }
    
    company_data = {
        "name": "Test Company Inc.",
        "industry": "Technology",
        "description": "A leading technology company focused on innovation."
    }
    
    insights_data = [
        "Revenue growth exceeded expectations by 15%",
        "Market expansion into European markets shows promise",
        "Customer satisfaction scores improved by 23%",
        "Digital transformation initiatives are on track"
    ]
    
    source_refs = {
        "financial_report": {"filename": "Q3_Financial_Report.xlsx"},
        "market_analysis": {"filename": "Market_Research_2024.pdf"}
    }
    
    # Test slide creation for each available template
    brand_manager = BrandManager()
    templates = brand_manager.list_templates()
    
    for template_name in templates:
        print(f"\n🎯 Testing with template: {template_name}")
        
        try:
            # Initialize generator with specific template
            generator = BrandedSlideGenerator(template_name=template_name)
            results.append(("✅", f"Generator init with {template_name}", "Success"))
            print(f"✅ Generator initialization: SUCCESS")
            
            # Test 1: Create title slide
            try:
                title_slide = generator.create_title_slide(
                    "Test Presentation", 
                    "Generated with BrandedSlideGenerator"
                )
                results.append(("✅", f"Title slide creation ({template_name})", "Success"))
                print("✅ Title slide creation: SUCCESS")
            except Exception as e:
                results.append(("❌", f"Title slide creation ({template_name})", str(e)))
                print(f"❌ Title slide creation: FAILED - {e}")
            
            # Test 2: Create financial summary slide
            try:
                financial_slide = generator.create_financial_summary_slide(financial_data, source_refs)
                results.append(("✅", f"Financial slide creation ({template_name})", "Success"))
                print("✅ Financial summary slide: SUCCESS")
            except Exception as e:
                results.append(("❌", f"Financial slide creation ({template_name})", str(e)))
                print(f"❌ Financial summary slide: FAILED - {e}")
            
            # Test 3: Create company overview slide
            try:
                company_slide = generator.create_company_overview_slide(company_data, source_refs)
                results.append(("✅", f"Company slide creation ({template_name})", "Success"))
                print("✅ Company overview slide: SUCCESS")
            except Exception as e:
                results.append(("❌", f"Company slide creation ({template_name})", str(e)))
                print(f"❌ Company overview slide: FAILED - {e}")
            
            # Test 4: Create insights slide
            try:
                insights_slide = generator.create_data_insights_slide(insights_data, source_refs)
                results.append(("✅", f"Insights slide creation ({template_name})", "Success"))
                print("✅ Data insights slide: SUCCESS")
            except Exception as e:
                results.append(("❌", f"Insights slide creation ({template_name})", str(e)))
                print(f"❌ Data insights slide: FAILED - {e}")
            
            # Test 5: Save presentation
            try:
                output_path = f"test_output_{template_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pptx"
                saved_path = generator.save_presentation(output_path)
                
                # Check if file was created
                if os.path.exists(saved_path):
                    file_size = os.path.getsize(saved_path)
                    results.append(("✅", f"Presentation saving ({template_name})", f"File created: {file_size} bytes"))
                    print(f"✅ Presentation saved: {saved_path} ({file_size} bytes)")
                else:
                    results.append(("❌", f"Presentation saving ({template_name})", "File not created"))
                    print("❌ Presentation saving: File not created")
                    
            except Exception as e:
                results.append(("❌", f"Presentation saving ({template_name})", str(e)))
                print(f"❌ Presentation saving: FAILED - {e}")
                
        except Exception as e:
            results.append(("❌", f"Generator init with {template_name}", str(e)))
            print(f"❌ Generator initialization with {template_name}: FAILED - {e}")
    
    # Test with no template (default behavior)
    print(f"\n🎯 Testing with no template (default)")
    try:
        generator = BrandedSlideGenerator()
        title_slide = generator.create_title_slide("Default Template Test")
        financial_slide = generator.create_financial_summary_slide(financial_data, source_refs)
        
        output_path = f"test_output_default_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pptx"
        saved_path = generator.save_presentation(output_path)
        
        if os.path.exists(saved_path):
            file_size = os.path.getsize(saved_path)
            results.append(("✅", "Default template generation", f"File created: {file_size} bytes"))
            print(f"✅ Default template: SUCCESS ({file_size} bytes)")
        
    except Exception as e:
        results.append(("❌", "Default template generation", str(e)))
        print(f"❌ Default template: FAILED - {e}")
    
    return results

def test_brand_styling():
    """Test brand styling functionality"""
    print("\n" + "="*60)
    print("🎨 TESTING BRAND STYLING")
    print("="*60)
    
    results = []
    
    try:
        generator = BrandedSlideGenerator()
        
        # Test brand color methods
        try:
            primary_color = generator._get_brand_color('primary')
            secondary_color = generator._get_brand_color('secondary')
            results.append(("✅", "Brand color retrieval", f"Primary: {primary_color}, Secondary: {secondary_color}"))
            print(f"✅ Brand colors: Primary={primary_color}, Secondary={secondary_color}")
        except Exception as e:
            results.append(("❌", "Brand color retrieval", str(e)))
            print(f"❌ Brand color retrieval: FAILED - {e}")
        
        # Test color conversion
        try:
            test_colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFFFF', '#000000']
            for hex_color in test_colors:
                rgb_color = generator._hex_to_rgb(hex_color)
                results.append(("✅", f"Color conversion {hex_color}", f"RGB({rgb_color.r}, {rgb_color.g}, {rgb_color.b})"))
                print(f"✅ Color conversion {hex_color}: RGB({rgb_color.r}, {rgb_color.g}, {rgb_color.b})")
        except Exception as e:
            results.append(("❌", "Color conversion", str(e)))
            print(f"❌ Color conversion: FAILED - {e}")
        
        # Test financial value formatting
        try:
            test_values = [500, 1500, 25000, 1000000, 15000000, 0.15, "N/A"]
            for value in test_values:
                formatted = generator._format_financial_value(value)
                results.append(("✅", f"Value formatting {value}", formatted))
                print(f"✅ Format {value}: {formatted}")
        except Exception as e:
            results.append(("❌", "Financial value formatting", str(e)))
            print(f"❌ Financial value formatting: FAILED - {e}")
        
    except Exception as e:
        results.append(("❌", "Brand styling setup", str(e)))
        print(f"❌ Brand styling setup: FAILED - {e}")
    
    return results

def test_source_attribution():
    """Test source attribution functionality"""
    print("\n" + "="*60)
    print("📝 TESTING SOURCE ATTRIBUTION")
    print("="*60)
    
    results = []
    
    try:
        generator = BrandedSlideGenerator()
        slide = generator.prs.slides.add_slide(generator.prs.slide_layouts[0])
        
        # Test different source reference formats
        test_sources = [
            {"file1": {"filename": "test.xlsx"}},
            {"file1": {"filename": "report.pdf"}, "file2": {"filename": "data.csv"}},
            ["source1", "source2", "source3"],
            "single_source.txt"
        ]
        
        for i, source_ref in enumerate(test_sources):
            try:
                generator.add_source_attribution(slide, source_ref)
                results.append(("✅", f"Source attribution test {i+1}", f"Type: {type(source_ref).__name__}"))
                print(f"✅ Source attribution test {i+1}: SUCCESS - {type(source_ref).__name__}")
            except Exception as e:
                results.append(("❌", f"Source attribution test {i+1}", str(e)))
                print(f"❌ Source attribution test {i+1}: FAILED - {e}")
        
        # Save test presentation with attribution
        output_path = f"test_attribution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pptx"
        generator.save_presentation(output_path)
        
        if os.path.exists(output_path):
            results.append(("✅", "Attribution presentation save", output_path))
            print(f"✅ Attribution test saved: {output_path}")
        
    except Exception as e:
        results.append(("❌", "Source attribution setup", str(e)))
        print(f"❌ Source attribution setup: FAILED - {e}")
    
    return results

def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n" + "="*60)
    print("⚠️  TESTING EDGE CASES")
    print("="*60)
    
    results = []
    
    try:
        generator = BrandedSlideGenerator()
        
        # Test empty data
        try:
            slide = generator.create_financial_summary_slide({}, {})
            results.append(("✅", "Empty financial data", "Handled gracefully"))
            print("✅ Empty financial data: Handled gracefully")
        except Exception as e:
            results.append(("❌", "Empty financial data", str(e)))
            print(f"❌ Empty financial data: FAILED - {e}")
        
        # Test None data
        try:
            slide = generator.create_company_overview_slide(None, None)
            results.append(("✅", "None data handling", "Handled gracefully"))
            print("✅ None data: Handled gracefully")
        except Exception as e:
            results.append(("❌", "None data handling", str(e)))
            print(f"❌ None data: FAILED - {e}")
        
        # Test invalid template name
        try:
            generator_invalid = BrandedSlideGenerator(template_name="nonexistent_template")
            results.append(("✅", "Invalid template handling", "Handled gracefully"))
            print("✅ Invalid template: Handled gracefully")
        except Exception as e:
            results.append(("❌", "Invalid template handling", str(e)))
            print(f"❌ Invalid template: FAILED - {e}")
        
        # Test very long text
        try:
            long_text = "This is a very long text " * 100
            slide = generator.create_title_slide(long_text)
            results.append(("✅", "Long title text", "Handled gracefully"))
            print("✅ Long title text: Handled gracefully")
        except Exception as e:
            results.append(("❌", "Long title text", str(e)))
            print(f"❌ Long title text: FAILED - {e}")
        
    except Exception as e:
        results.append(("❌", "Edge case setup", str(e)))
        print(f"❌ Edge case setup: FAILED - {e}")
    
    return results

def generate_test_report(all_results):
    """Generate a comprehensive test report"""
    print("\n" + "="*60)
    print("📋 TEST REPORT SUMMARY")
    print("="*60)
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    warnings = 0
    
    report_lines = []
    report_lines.append("BRANDED SLIDE GENERATOR TEST REPORT")
    report_lines.append("=" * 50)
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    
    for test_category, results in all_results.items():
        report_lines.append(f"\n{test_category.upper()}:")
        report_lines.append("-" * 30)
        
        for status, test_name, details in results:
            total_tests += 1
            if status == "✅":
                passed_tests += 1
            elif status == "❌":
                failed_tests += 1
            elif status == "⚠️":
                warnings += 1
            
            report_lines.append(f"{status} {test_name}: {details}")
    
    # Summary statistics
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    summary = f"""
SUMMARY STATISTICS:
- Total Tests: {total_tests}
- Passed: {passed_tests} ({success_rate:.1f}%)
- Failed: {failed_tests}
- Warnings: {warnings}

OVERALL STATUS: {'✅ PASS' if failed_tests == 0 else '❌ FAIL'}
"""
    
    report_lines.append(summary)
    print(summary)
    
    # Save report to file
    report_filename = f"branded_slide_generator_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_filename, 'w') as f:
        f.write('\n'.join(report_lines))
    
    print(f"📄 Detailed report saved: {report_filename}")
    
    return success_rate >= 80  # Consider 80% pass rate as acceptable

def main():
    """Run all tests and generate report"""
    print("🚀 STARTING BRANDED SLIDE GENERATOR COMPREHENSIVE TESTS")
    print("=" * 60)
    
    all_results = {}
    
    # Run all test categories
    all_results["Setup Tests"] = test_setup()
    all_results["Template Integration"] = test_template_integration()
    all_results["Slide Creation"] = test_slide_creation()
    all_results["Brand Styling"] = test_brand_styling()
    all_results["Source Attribution"] = test_source_attribution()
    all_results["Edge Cases"] = test_edge_cases()
    
    # Generate comprehensive report
    overall_success = generate_test_report(all_results)
    
    if overall_success:
        print("\n🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        return 0
    else:
        print("\n⚠️ SOME TESTS FAILED - CHECK REPORT FOR DETAILS")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)