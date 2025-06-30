#!/usr/bin/env python3
"""
Comprehensive API Testing Suite Runner
Coordinates all API test suites and generates detailed reports
"""

import sys
import os
import time
import json
import subprocess
from datetime import datetime
import requests

def check_server_status():
    """Check if the API server is running"""
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            return True, health_data
        else:
            return False, f"Server returned status {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"Connection failed: {str(e)}"

def check_dependencies():
    """Check if required dependencies are available"""
    required_modules = [
        'flask', 'requests', 'openpyxl', 'python-docx', 
        'psutil', 'unittest', 'threading', 'queue'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module.replace('-', '_'))
        except ImportError:
            missing_modules.append(module)
    
    return missing_modules

def run_test_suite(test_file, suite_name):
    """Run a specific test suite and capture results"""
    print(f"\n{'='*20} {suite_name} {'='*20}")
    print(f"Running: {test_file}")
    
    start_time = time.time()
    
    try:
        # Run the test file
        result = subprocess.run([
            sys.executable, test_file
        ], capture_output=True, text=True, timeout=600)  # 10 minute timeout
        
        end_time = time.time()
        duration = end_time - start_time
        
        success = result.returncode == 0
        
        return {
            'suite_name': suite_name,
            'test_file': test_file,
            'success': success,
            'duration': duration,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'return_code': result.returncode
        }
        
    except subprocess.TimeoutExpired:
        return {
            'suite_name': suite_name,
            'test_file': test_file,
            'success': False,
            'duration': 600,
            'stdout': '',
            'stderr': 'Test suite timed out after 10 minutes',
            'return_code': -1
        }
    except Exception as e:
        return {
            'suite_name': suite_name,
            'test_file': test_file,
            'success': False,
            'duration': 0,
            'stdout': '',
            'stderr': f'Failed to run test suite: {str(e)}',
            'return_code': -2
        }

def generate_report(results, report_file):
    """Generate a comprehensive test report"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""
# API Testing Report
Generated: {timestamp}

## Executive Summary

"""
    
    total_suites = len(results)
    successful_suites = sum(1 for r in results if r['success'])
    total_duration = sum(r['duration'] for r in results)
    
    report += f"- **Total Test Suites**: {total_suites}\n"
    report += f"- **Successful Suites**: {successful_suites}/{total_suites}\n"
    report += f"- **Overall Success Rate**: {(successful_suites/total_suites*100):.1f}%\n"
    report += f"- **Total Testing Time**: {total_duration:.1f} seconds\n\n"
    
    # Suite-by-suite results
    report += "## Test Suite Results\n\n"
    
    for result in results:
        status_icon = "✅" if result['success'] else "❌"
        report += f"### {status_icon} {result['suite_name']}\n\n"
        report += f"- **File**: `{result['test_file']}`\n"
        report += f"- **Duration**: {result['duration']:.1f} seconds\n"
        report += f"- **Status**: {'PASSED' if result['success'] else 'FAILED'}\n"
        report += f"- **Return Code**: {result['return_code']}\n\n"
        
        if result['success']:
            # Extract key metrics from stdout if available
            stdout_lines = result['stdout'].split('\n')
            test_summary_started = False
            for line in stdout_lines:
                if 'SUMMARY' in line or 'Tests run:' in line:
                    test_summary_started = True
                if test_summary_started and (line.strip().startswith('Tests run:') or 
                                            line.strip().startswith('Success Rate:') or
                                            line.strip().startswith('Failures:') or
                                            line.strip().startswith('Errors:')):
                    report += f"  - {line.strip()}\n"
        else:
            report += "**Error Details:**\n"
            if result['stderr']:
                report += f"```\n{result['stderr'][:500]}{'...' if len(result['stderr']) > 500 else ''}\n```\n"
            elif result['stdout']:
                # Look for error information in stdout
                stdout_lines = result['stdout'].split('\n')
                error_lines = [line for line in stdout_lines if 'error' in line.lower() or 'fail' in line.lower()]
                if error_lines:
                    report += "```\n"
                    for line in error_lines[:10]:  # First 10 error lines
                        report += f"{line}\n"
                    report += "```\n"
        
        report += "\n"
    
    # Detailed output for successful suites
    report += "## Detailed Test Output\n\n"
    
    for result in results:
        if result['success'] and result['stdout']:
            report += f"### {result['suite_name']} - Detailed Output\n\n"
            report += "```\n"
            # Include last 50 lines of output for successful tests
            stdout_lines = result['stdout'].split('\n')
            relevant_lines = stdout_lines[-50:] if len(stdout_lines) > 50 else stdout_lines
            for line in relevant_lines:
                if line.strip():  # Skip empty lines
                    report += f"{line}\n"
            report += "```\n\n"
    
    # Recommendations
    report += "## Recommendations\n\n"
    
    failed_suites = [r for r in results if not r['success']]
    if failed_suites:
        report += "### Failed Test Suites\n\n"
        for result in failed_suites:
            report += f"- **{result['suite_name']}**: Review the error details above and ensure all dependencies are properly installed.\n"
        report += "\n"
    
    if successful_suites == total_suites:
        report += "### All Tests Passed! 🎉\n\n"
        report += "- All API endpoints are functioning correctly\n"
        report += "- Performance metrics are within acceptable ranges\n"
        report += "- Error handling is working as expected\n"
        report += "- System is ready for production use\n\n"
    
    report += "### Next Steps\n\n"
    report += "1. Review any failed test suites and address issues\n"
    report += "2. Monitor performance metrics for optimization opportunities\n"
    report += "3. Consider adding additional test scenarios based on real-world usage\n"
    report += "4. Set up continuous integration to run these tests automatically\n"
    
    # Write report to file
    with open(report_file, 'w') as f:
        f.write(report)
    
    return report

def main():
    """Main test runner function"""
    print("=" * 80)
    print("COMPREHENSIVE API TESTING SUITE")
    print("document-slides-poc API Testing")
    print("=" * 80)
    
    # Check dependencies
    print("\n1. Checking dependencies...")
    missing_deps = check_dependencies()
    if missing_deps:
        print(f"❌ Missing dependencies: {', '.join(missing_deps)}")
        print("Please install missing dependencies with: pip install <module_name>")
        return False
    else:
        print("✅ All dependencies available")
    
    # Check server status
    print("\n2. Checking server status...")
    server_running, server_info = check_server_status()
    if server_running:
        print("✅ API server is running")
        print(f"   Service: {server_info.get('service', 'Unknown')}")
        print(f"   Status: {server_info.get('status', 'Unknown')}")
        print(f"   Template Management: {server_info.get('template_management', 'Unknown')}")
    else:
        print(f"❌ API server is not accessible: {server_info}")
        print("Please start the API server with: python start_server.py")
        return False
    
    # Define test suites
    test_suites = [
        {
            'file': 'test_api_endpoints.py',
            'name': 'Core API Endpoints',
            'description': 'Tests all API endpoints with various file types and scenarios'
        },
        {
            'file': 'test_api_mocked.py',
            'name': 'Mocked External APIs',
            'description': 'Tests with mocked OpenAI and LLMWhisperer dependencies'
        },
        {
            'file': 'test_api_performance.py',
            'name': 'Performance & Stress Testing',
            'description': 'Tests performance, concurrency, and stress scenarios'
        },
        {
            'file': 'test_api_security_edge_cases.py',
            'name': 'Security & Edge Cases',
            'description': 'Tests security vulnerabilities, edge cases, and malicious input handling'
        }
    ]
    
    # Run test suites
    print(f"\n3. Running {len(test_suites)} test suites...")
    results = []
    
    for i, suite in enumerate(test_suites, 1):
        print(f"\n   {i}/{len(test_suites)}: {suite['name']}")
        print(f"   {suite['description']}")
        
        if os.path.exists(suite['file']):
            result = run_test_suite(suite['file'], suite['name'])
            results.append(result)
            
            status = "✅ PASSED" if result['success'] else "❌ FAILED"
            print(f"   Result: {status} ({result['duration']:.1f}s)")
        else:
            print(f"   ❌ Test file not found: {suite['file']}")
            results.append({
                'suite_name': suite['name'],
                'test_file': suite['file'],
                'success': False,
                'duration': 0,
                'stdout': '',
                'stderr': f'Test file not found: {suite["file"]}',
                'return_code': -3
            })
    
    # Generate report
    print("\n4. Generating test report...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"api_test_report_{timestamp}.md"
    
    report_content = generate_report(results, report_file)
    print(f"✅ Test report generated: {report_file}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)
    
    successful_suites = sum(1 for r in results if r['success'])
    total_suites = len(results)
    total_duration = sum(r['duration'] for r in results)
    
    print(f"Test Suites: {successful_suites}/{total_suites} passed")
    print(f"Total Time: {total_duration:.1f} seconds")
    print(f"Success Rate: {(successful_suites/total_suites*100):.1f}%")
    print(f"Report: {report_file}")
    
    if successful_suites == total_suites:
        print("\n🎉 ALL TESTS PASSED! API is ready for use.")
        return True
    else:
        print(f"\n⚠️  {total_suites - successful_suites} test suite(s) failed. Review the report for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)