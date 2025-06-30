#!/usr/bin/env python3
"""
Quick System Validation Script
Agent 5: End-to-End Workflow Testing

A simple script to quickly validate that the system is working
and run a subset of critical tests.
"""

import os
import sys
import json
import requests
import time
from datetime import datetime
from pathlib import Path

def print_header(text):
    print(f"\n{'='*60}")
    print(f"🔍 {text}")
    print('='*60)

def print_success(text):
    print(f"✅ {text}")

def print_warning(text):
    print(f"⚠️  {text}")

def print_error(text):
    print(f"❌ {text}")

def print_info(text):
    print(f"ℹ️  {text}")

def quick_system_check(base_url="http://localhost:5001"):
    """Run a quick system validation"""
    print_header("QUICK SYSTEM VALIDATION")
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'base_url': base_url,
        'checks': {},
        'overall_status': 'unknown'
    }
    
    # 1. API Health Check
    print_info("Checking API server health...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print_success(f"API server is healthy: {health_data.get('status', 'OK')}")
            results['checks']['api_health'] = {'passed': True, 'data': health_data}
        else:
            print_error(f"API server returned status {response.status_code}")
            results['checks']['api_health'] = {'passed': False, 'status_code': response.status_code}
    except Exception as e:
        print_error(f"API server not accessible: {str(e)[:100]}")
        results['checks']['api_health'] = {'passed': False, 'error': str(e)}
    
    # 2. Template System Check
    print_info("Checking template management...")
    try:
        response = requests.get(f"{base_url}/api/templates", timeout=10)
        if response.status_code == 200:
            template_data = response.json()
            template_count = len(template_data.get('templates', []))
            print_success(f"Template system working: {template_count} templates available")
            results['checks']['templates'] = {'passed': True, 'count': template_count}
        elif response.status_code == 503:
            print_warning("Template management not configured (optional)")
            results['checks']['templates'] = {'passed': True, 'note': 'Not configured'}
        else:
            print_warning(f"Template endpoint returned {response.status_code}")
            results['checks']['templates'] = {'passed': False, 'status_code': response.status_code}
    except Exception as e:
        print_warning(f"Template check failed: {str(e)[:100]}")
        results['checks']['templates'] = {'passed': False, 'error': str(e)}
    
    # 3. Document Preview Test
    print_info("Testing document preview functionality...")
    try:
        # Create simple test data
        test_data = b"Revenue,10000000\nProfit,2000000"
        files = {'documents': ('test.csv', test_data, 'text/csv')}
        
        response = requests.post(f"{base_url}/api/generate-slides/preview", 
                               files=files, timeout=30)
        
        if response.status_code == 200:
            preview_data = response.json()
            if preview_data.get('success'):
                docs_processed = preview_data.get('documents_processed', 0)
                print_success(f"Document preview working: {docs_processed} documents processed")
                results['checks']['document_preview'] = {'passed': True, 'processed': docs_processed}
            else:
                print_error("Document preview returned error")
                results['checks']['document_preview'] = {'passed': False, 'data': preview_data}
        else:
            print_error(f"Document preview failed with status {response.status_code}")
            results['checks']['document_preview'] = {'passed': False, 'status_code': response.status_code}
    except Exception as e:
        print_error(f"Document preview test failed: {str(e)[:100]}")
        results['checks']['document_preview'] = {'passed': False, 'error': str(e)}
    
    # 4. Slide Generation Test
    print_info("Testing slide generation...")
    try:
        # Use same test data
        test_data = b"Revenue,10000000\nProfit,2000000"
        files = {'documents': ('test.csv', test_data, 'text/csv')}
        form_data = {'template_id': 'default'}
        
        response = requests.post(f"{base_url}/api/generate-slides", 
                               files=files, data=form_data, timeout=60)
        
        if response.status_code == 200:
            file_size = len(response.content)
            content_type = response.headers.get('content-type', '')
            
            if file_size > 1000:  # Reasonable file size
                print_success(f"Slide generation working: {file_size} bytes generated")
                results['checks']['slide_generation'] = {
                    'passed': True, 
                    'file_size': file_size,
                    'content_type': content_type
                }
            else:
                print_warning(f"Slide generation returned small file: {file_size} bytes")
                results['checks']['slide_generation'] = {
                    'passed': False, 
                    'file_size': file_size,
                    'issue': 'File too small'
                }
        else:
            print_error(f"Slide generation failed with status {response.status_code}")
            results['checks']['slide_generation'] = {'passed': False, 'status_code': response.status_code}
    except Exception as e:
        print_error(f"Slide generation test failed: {str(e)[:100]}")
        results['checks']['slide_generation'] = {'passed': False, 'error': str(e)}
    
    # 5. File System Check
    print_info("Checking file system access...")
    try:
        test_dir = Path("temp_validation_test")
        test_dir.mkdir(exist_ok=True)
        
        test_file = test_dir / "test.txt"
        test_file.write_text("test")
        content = test_file.read_text()
        
        test_file.unlink()
        test_dir.rmdir()
        
        print_success("File system access working")
        results['checks']['file_system'] = {'passed': True}
    except Exception as e:
        print_error(f"File system check failed: {str(e)[:100]}")
        results['checks']['file_system'] = {'passed': False, 'error': str(e)}
    
    # Calculate overall status
    passed_checks = sum(1 for check in results['checks'].values() if check.get('passed', False))
    total_checks = len(results['checks'])
    success_rate = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
    
    print_header("VALIDATION SUMMARY")
    print_info(f"Checks passed: {passed_checks}/{total_checks} ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        results['overall_status'] = 'healthy'
        print_success("System is healthy and ready for use")
    elif success_rate >= 60:
        results['overall_status'] = 'warning'
        print_warning("System has some issues but is functional")
    else:
        results['overall_status'] = 'error'
        print_error("System has significant issues")
    
    # Show specific check results
    for check_name, check_result in results['checks'].items():
        status = "✅" if check_result.get('passed') else "❌"
        print(f"   {status} {check_name.replace('_', ' ').title()}")
    
    # Save results
    report_file = f"quick_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print_info(f"Validation report saved: {report_file}")
    
    return results

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Quick system validation for Document-Slides-POC')
    parser.add_argument('--base-url', default='http://localhost:5001',
                       help='Base URL for API server (default: http://localhost:5001)')
    
    args = parser.parse_args()
    
    # Run validation
    results = quick_system_check(args.base_url)
    
    # Exit with appropriate code
    if results['overall_status'] == 'healthy':
        sys.exit(0)
    elif results['overall_status'] == 'warning':
        sys.exit(1)
    else:
        sys.exit(2)

if __name__ == "__main__":
    main()