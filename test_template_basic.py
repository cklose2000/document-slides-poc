#!/usr/bin/env python3
"""
Basic test for template system without requiring matplotlib
"""

import os
import sys
import json
from pathlib import Path

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from lib.template_parser import BrandManager, TemplateParser


def test_template_system():
    """Test basic template functionality"""
    print("Testing Template System...")
    print("-" * 40)
    
    # Test 1: Check templates directory
    if os.path.exists('templates'):
        print("✅ Templates directory exists")
        
        # List subdirectories
        subdirs = [d for d in os.listdir('templates') if os.path.isdir(os.path.join('templates', d))]
        print(f"✅ Found {len(subdirs)} template directories: {', '.join(subdirs)}")
    else:
        print("❌ Templates directory not found")
        return
    
    # Test 2: Check metadata files
    print("\nChecking template metadata...")
    for template_dir in subdirs:
        metadata_path = os.path.join('templates', template_dir, 'metadata.json')
        template_path = os.path.join('templates', template_dir, 'template.pptx')
        
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            print(f"✅ {template_dir}: {metadata.get('name', 'Unknown')}")
            print(f"   - {metadata.get('description', 'No description')}")
        else:
            print(f"❌ {template_dir}: Missing metadata.json")
        
        if os.path.exists(template_path):
            print(f"   ✅ template.pptx exists")
        else:
            print(f"   ❌ template.pptx missing")
    
    # Test 3: Test BrandManager
    print("\nTesting BrandManager...")
    try:
        brand_manager = BrandManager('templates')
        templates = brand_manager.list_templates()
        print(f"✅ BrandManager loaded {len(templates)} templates")
        
        # Test getting a template
        if templates:
            first_template = templates[0]
            template_parser = brand_manager.get_template(first_template)
            if template_parser:
                print(f"✅ Successfully retrieved template: {first_template}")
                config = template_parser.get_brand_config()
                print(f"   - Theme colors: {len(config.get('theme_colors', {}))}")
                print(f"   - Font families: {len(config.get('fonts', {}))}")
                print(f"   - Layouts: {len(config.get('layouts', []))}")
    except Exception as e:
        print(f"❌ BrandManager error: {str(e)}")
    
    # Test 4: Check API endpoints availability
    print("\nChecking API setup...")
    api_file = 'api/generate_slides.py'
    if os.path.exists(api_file):
        with open(api_file, 'r') as f:
            content = f.read()
        
        if '/api/templates' in content:
            print("✅ Template listing endpoint exists")
        if 'template_id' in content:
            print("✅ Template selection in generate-slides endpoint")
        if 'BrandedSlideGenerator' in content:
            print("✅ Branded slide generator integration")
    
    # Test 5: Check web interface
    print("\nChecking web interface...")
    html_file = 'static/presentation.html'
    if os.path.exists(html_file):
        with open(html_file, 'r') as f:
            content = f.read()
        
        if 'selectedTemplateId' in content:
            print("✅ Template selection in UI")
        if 'loadTemplates' in content:
            print("✅ Template loading function")
        if 'template_id' in content:
            print("✅ Template ID in form submission")
    
    print("\n" + "=" * 40)
    print("Template System Test Complete!")
    print("=" * 40)


if __name__ == "__main__":
    test_template_system()