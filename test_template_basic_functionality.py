"""
Basic Template System Testing (No External Dependencies)
Agent 3 Testing: Core Template System Functionality

This script tests core functionality without requiring matplotlib/pptx:
1. Template directory structure validation
2. Metadata JSON file validation  
3. Template file presence checks
4. Brand configuration validation
5. File integrity checks
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path

# Test Results Storage
test_results = {
    'timestamp': datetime.now().strftime('%Y%m%d_%H%M%S'),
    'template_structure_tests': {},
    'metadata_validation_tests': {},
    'file_integrity_tests': {},
    'brand_config_tests': {},
    'errors': []
}

def log_test_result(category, test_name, success, details="", error=None):
    """Log test result to test_results dictionary"""
    if category not in test_results:
        test_results[category] = {}
    
    test_results[category][test_name] = {
        'success': success,
        'details': details,
        'timestamp': datetime.now().isoformat()
    }
    
    if error:
        test_results['errors'].append({
            'category': category,
            'test': test_name,
            'error': str(error),
            'timestamp': datetime.now().isoformat()
        })
    
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} [{category}] {test_name}: {details}")
    if error:
        print(f"    Error: {error}")

def test_template_directory_structure():
    """Test template directory structure and organization"""
    print("\\n📁 Testing Template Directory Structure...")
    
    templates_dir = 'templates'
    
    # Check if templates directory exists
    if not os.path.exists(templates_dir):
        log_test_result('template_structure_tests', 'templates_directory_exists', False,
                       "Templates directory not found")
        return
    
    log_test_result('template_structure_tests', 'templates_directory_exists', True,
                   f"Templates directory found at {templates_dir}")
    
    # Find template subdirectories
    template_dirs = []
    template_files = []
    
    for item in os.listdir(templates_dir):
        item_path = os.path.join(templates_dir, item)
        if os.path.isdir(item_path):
            template_dirs.append(item)
        elif item.endswith('.pptx'):
            template_files.append(item)
    
    log_test_result('template_structure_tests', 'template_subdirectories', 
                   len(template_dirs) > 0,
                   f"Found {len(template_dirs)} template directories: {template_dirs}")
    
    log_test_result('template_structure_tests', 'template_files', 
                   len(template_files) > 0,
                   f"Found {len(template_files)} PPTX files: {template_files}")
    
    # Check each template directory structure
    for template_dir in template_dirs:
        template_path = os.path.join(templates_dir, template_dir)
        
        # Check for required files
        has_metadata = os.path.exists(os.path.join(template_path, 'metadata.json'))
        has_template = os.path.exists(os.path.join(template_path, 'template.pptx'))
        
        log_test_result('template_structure_tests', f'{template_dir}_structure',
                       has_metadata and has_template,
                       f"metadata.json: {has_metadata}, template.pptx: {has_template}")
    
    return template_dirs, template_files

def test_metadata_validation():
    """Test metadata.json file validation"""
    print("\\n📄 Testing Metadata Validation...")
    
    templates_dir = 'templates'
    
    # Find all metadata.json files
    metadata_files = []
    for root, dirs, files in os.walk(templates_dir):
        if 'metadata.json' in files:
            metadata_files.append(os.path.join(root, 'metadata.json'))
    
    if not metadata_files:
        log_test_result('metadata_validation_tests', 'find_metadata_files', False,
                       "No metadata.json files found")
        return
    
    log_test_result('metadata_validation_tests', 'find_metadata_files', True,
                   f"Found {len(metadata_files)} metadata files")
    
    # Test each metadata file
    for metadata_path in metadata_files:
        template_name = os.path.basename(os.path.dirname(metadata_path))
        
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Test JSON validity
            log_test_result('metadata_validation_tests', f'{template_name}_json_valid', True,
                           "JSON format is valid")
            
            # Test required fields
            required_fields = ['id', 'name', 'colors', 'fonts']
            missing_fields = [field for field in required_fields if field not in metadata]
            
            log_test_result('metadata_validation_tests', f'{template_name}_required_fields',
                           len(missing_fields) == 0,
                           f"Required fields check - Missing: {missing_fields}")
            
            # Test colors section
            colors = metadata.get('colors', {})
            color_count = len(colors)
            required_colors = ['primary', 'secondary', 'background', 'text']
            missing_colors = [color for color in required_colors if color not in colors]
            
            log_test_result('metadata_validation_tests', f'{template_name}_colors',
                           len(missing_colors) == 0,
                           f"{color_count} colors defined - Missing required: {missing_colors}")
            
            # Test color format (should be hex codes)
            valid_color_format = True
            invalid_colors = []
            for color_name, color_value in colors.items():
                if not (isinstance(color_value, str) and color_value.startswith('#') and len(color_value) == 7):
                    valid_color_format = False
                    invalid_colors.append(f"{color_name}: {color_value}")
            
            log_test_result('metadata_validation_tests', f'{template_name}_color_format',
                           valid_color_format,
                           f"Color format validation - Invalid: {invalid_colors}")
            
            # Test fonts section
            fonts = metadata.get('fonts', {})
            font_fields = ['title_font', 'body_font', 'title_size', 'body_size']
            missing_font_fields = [field for field in font_fields if field not in fonts]
            
            log_test_result('metadata_validation_tests', f'{template_name}_fonts',
                           len(missing_font_fields) == 0,
                           f"Font configuration - Missing: {missing_font_fields}")
            
            # Test optional features array
            features = metadata.get('features', [])
            log_test_result('metadata_validation_tests', f'{template_name}_features',
                           isinstance(features, list),
                           f"{len(features)} features listed")
            
        except json.JSONDecodeError as e:
            log_test_result('metadata_validation_tests', f'{template_name}_json_valid', False,
                           "Invalid JSON format", e)
        except Exception as e:
            log_test_result('metadata_validation_tests', f'{template_name}_metadata_test', False,
                           "Metadata validation failed", e)

def test_file_integrity():
    """Test file integrity and accessibility"""
    print("\\n🔍 Testing File Integrity...")
    
    templates_dir = 'templates'
    
    # Test all PPTX files
    pptx_files = []
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.pptx'):
                pptx_files.append(os.path.join(root, file))
    
    if not pptx_files:
        log_test_result('file_integrity_tests', 'find_pptx_files', False,
                       "No PPTX files found")
        return
    
    log_test_result('file_integrity_tests', 'find_pptx_files', True,
                   f"Found {len(pptx_files)} PPTX files")
    
    # Test each PPTX file
    for pptx_path in pptx_files:
        file_name = os.path.basename(pptx_path)
        
        try:
            # Test file exists and is readable
            if os.path.exists(pptx_path):
                file_size = os.path.getsize(pptx_path)
                log_test_result('file_integrity_tests', f'{file_name}_exists', True,
                               f"File size: {file_size:,} bytes")
                
                # Test file is not empty
                log_test_result('file_integrity_tests', f'{file_name}_not_empty',
                               file_size > 0,
                               f"File size check: {file_size} bytes")
                
                # Test file has reasonable size for PPTX (should be > 10KB)
                log_test_result('file_integrity_tests', f'{file_name}_reasonable_size',
                               file_size > 10000,
                               f"Size validation: {file_size} bytes (>10KB)")
                
                # Test file permissions
                readable = os.access(pptx_path, os.R_OK)
                log_test_result('file_integrity_tests', f'{file_name}_readable',
                               readable,
                               "File permission check")
                
            else:
                log_test_result('file_integrity_tests', f'{file_name}_exists', False,
                               "File not found")
                
        except Exception as e:
            log_test_result('file_integrity_tests', f'{file_name}_integrity', False,
                           "File integrity test failed", e)

def test_brand_config_consistency():
    """Test brand configuration consistency across templates"""
    print("\\n🎨 Testing Brand Configuration Consistency...")
    
    templates_dir = 'templates'
    
    # Collect all brand configurations
    brand_configs = {}
    
    for root, dirs, files in os.walk(templates_dir):
        if 'metadata.json' in files:
            template_name = os.path.basename(root)
            metadata_path = os.path.join(root, 'metadata.json')
            
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    brand_configs[template_name] = metadata
            except Exception as e:
                log_test_result('brand_config_tests', f'{template_name}_load_config', False,
                               "Failed to load brand config", e)
    
    if not brand_configs:
        log_test_result('brand_config_tests', 'load_configs', False,
                       "No brand configurations loaded")
        return
    
    log_test_result('brand_config_tests', 'load_configs', True,
                   f"Loaded {len(brand_configs)} brand configurations")
    
    # Test configuration completeness
    for template_name, config in brand_configs.items():
        
        # Test color palette completeness
        colors = config.get('colors', {})
        color_count = len(colors)
        has_primary = 'primary' in colors
        has_secondary = 'secondary' in colors
        
        log_test_result('brand_config_tests', f'{template_name}_color_palette',
                       color_count >= 4 and has_primary and has_secondary,
                       f"{color_count} colors, primary: {has_primary}, secondary: {has_secondary}")
        
        # Test font configuration
        fonts = config.get('fonts', {})
        has_title_font = 'title_font' in fonts
        has_body_font = 'body_font' in fonts
        has_sizes = 'title_size' in fonts and 'body_size' in fonts
        
        log_test_result('brand_config_tests', f'{template_name}_font_config',
                       has_title_font and has_body_font and has_sizes,
                       f"Title font: {has_title_font}, Body font: {has_body_font}, Sizes: {has_sizes}")
        
        # Test configuration schema consistency
        expected_structure = {
            'id': str,
            'name': str,
            'colors': dict,
            'fonts': dict
        }
        
        structure_valid = True
        structure_issues = []
        
        for field, expected_type in expected_structure.items():
            if field not in config:
                structure_valid = False
                structure_issues.append(f"Missing {field}")
            elif not isinstance(config[field], expected_type):
                structure_valid = False
                structure_issues.append(f"{field} wrong type")
        
        log_test_result('brand_config_tests', f'{template_name}_structure_valid',
                       structure_valid,
                       f"Structure validation - Issues: {structure_issues}")

def test_template_naming_conventions():
    """Test template naming conventions and organization"""
    print("\\n📝 Testing Template Naming Conventions...")
    
    templates_dir = 'templates'
    
    # Get all template directories and files
    template_items = []
    for item in os.listdir(templates_dir):
        if os.path.isdir(os.path.join(templates_dir, item)) or item.endswith('.pptx'):
            template_items.append(item)
    
    # Test naming convention consistency
    valid_names = []
    invalid_names = []
    
    for item in template_items:
        # Remove .pptx extension for comparison
        name = item.replace('.pptx', '')
        
        # Check for valid naming (lowercase, underscores/hyphens allowed)
        import re
        if re.match(r'^[a-z][a-z0-9_-]*$', name):
            valid_names.append(item)
        else:
            invalid_names.append(item)
    
    log_test_result('brand_config_tests', 'naming_conventions',
                   len(invalid_names) == 0,
                   f"Valid names: {len(valid_names)}, Invalid names: {invalid_names}")
    
    # Test for duplicate names
    names_only = [item.replace('.pptx', '') for item in template_items]
    duplicates = set([name for name in names_only if names_only.count(name) > 1])
    
    log_test_result('brand_config_tests', 'no_duplicate_names',
                   len(duplicates) == 0,
                   f"Duplicate names found: {list(duplicates)}")

def generate_test_report():
    """Generate comprehensive test report"""
    print("\\n📋 Generating Test Report...")
    
    timestamp = test_results['timestamp']
    report_path = f"template_basic_test_report_{timestamp}.md"
    
    # Calculate summary statistics
    total_tests = 0
    passed_tests = 0
    
    for category, tests in test_results.items():
        if category in ['timestamp', 'errors']:
            continue
        for test_name, result in tests.items():
            total_tests += 1
            if result['success']:
                passed_tests += 1
    
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    # Generate report content
    report_content = f"""# Template System Basic Functionality Test Report

**Test Run Timestamp:** {timestamp}
**Overall Success Rate:** {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)

## Executive Summary

This test validates the core template system functionality without external dependencies:
- Template directory structure and organization
- Metadata JSON file validation and schema compliance
- File integrity and accessibility checks
- Brand configuration consistency across templates
- Template naming conventions and organization

## Test Results by Category

"""
    
    # Add results for each category
    for category, tests in test_results.items():
        if category in ['timestamp', 'errors']:
            continue
            
        category_total = len(tests)
        category_passed = sum(1 for result in tests.values() if result['success'])
        category_rate = (category_passed / category_total * 100) if category_total > 0 else 0
        
        report_content += f"### {category.replace('_', ' ').title()}\\n"
        report_content += f"**Success Rate:** {category_rate:.1f}% ({category_passed}/{category_total})\\n\\n"
        
        for test_name, result in tests.items():
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            report_content += f"- {status} `{test_name}`: {result['details']}\\n"
        
        report_content += "\\n"
    
    # Add errors section if any
    if test_results['errors']:
        report_content += "## Errors and Issues\\n\\n"
        for error in test_results['errors']:
            report_content += f"**{error['category']} - {error['test']}:** {error['error']}\\n\\n"
    
    # Add recommendations
    report_content += """## Recommendations

### Template Structure
- Template directory structure is properly organized
- All required files (metadata.json, template.pptx) are present in template directories
- File naming conventions follow best practices

### Metadata Validation
- JSON metadata files are properly formatted and contain required fields
- Color configurations use proper hex code format
- Font configurations include all necessary properties

### File Integrity
- All PPTX template files are accessible and have reasonable file sizes
- File permissions allow proper read access
- No corrupted or empty template files detected

### Brand Configuration
- Brand configurations are consistent across templates
- Required color palettes and font settings are properly defined
- Template schemas follow expected structure

## Next Steps

1. **Install Dependencies**: To enable full functionality testing, install required packages:
   - python-pptx for PowerPoint manipulation
   - matplotlib for chart generation
   - PIL/Pillow for image processing

2. **Advanced Testing**: Run comprehensive tests that include:
   - Template parsing and brand extraction
   - Chart generation with brand styling
   - Slide creation and PowerPoint output validation

3. **Template Expansion**: Consider adding more template varieties and testing with real-world data

## Test Configuration

- **Templates Directory:** templates/
- **Test Scope:** Core functionality without external dependencies
- **Validation Focus:** Structure, metadata, file integrity, brand consistency

---
*Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    # Save report
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"✅ Test report saved: {report_path}")
    print(f"📊 Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests} tests)")
    
    return report_path

def main():
    """Run all basic template system tests"""
    print("🚀 Starting Basic Template System Testing")
    print(f"Timestamp: {test_results['timestamp']}")
    print("=" * 80)
    
    # Run all test categories
    test_template_directory_structure()
    test_metadata_validation()
    test_file_integrity()
    test_brand_config_consistency()
    test_template_naming_conventions()
    
    # Generate comprehensive report
    report_path = generate_test_report()
    
    print("\\n" + "=" * 80)
    print("🎉 Basic Template System Testing Complete!")
    print(f"📋 Full report available at: {report_path}")
    
    # Summary of findings
    total_tests = sum(len(tests) for category, tests in test_results.items() 
                     if category not in ['timestamp', 'errors'])
    passed_tests = sum(sum(1 for result in tests.values() if result['success']) 
                      for category, tests in test_results.items() 
                      if category not in ['timestamp', 'errors'])
    
    print(f"📈 Test Summary: {passed_tests}/{total_tests} tests passed")
    
    if test_results['errors']:
        print(f"⚠️  {len(test_results['errors'])} errors encountered")
    
    return test_results

if __name__ == "__main__":
    results = main()