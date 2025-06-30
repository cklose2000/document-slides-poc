#!/usr/bin/env python3
"""
Comprehensive test execution script
Orchestrates all testing components: performance, error handling, stress tests, 
quality gates, and dashboard generation
"""
import os
import sys
import argparse
import json
import time
import subprocess
from pathlib import Path

def ensure_python_path():
    """Ensure current directory is in Python path"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

def create_test_directories():
    """Create necessary test directories"""
    directories = [
        "tests",
        "tests/performance", 
        "tests/error_handling",
        "tests/stress",
        "test_results",
        "test_reports",
        "test_reports/dashboard"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Created directory: {directory}")

def run_test_suite(suite_name, script_path, timeout=600):
    """Run a specific test suite"""
    print(f"\n{'='*60}")
    print(f"Running {suite_name}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        # Run the test script
        result = subprocess.run([
            sys.executable, script_path
        ], capture_output=True, text=True, timeout=timeout)
        
        execution_time = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ {suite_name} completed successfully in {execution_time:.2f}s")
            return True, execution_time, result.stdout
        else:
            print(f"❌ {suite_name} failed in {execution_time:.2f}s")
            print(f"Error output: {result.stderr}")
            return False, execution_time, result.stderr
            
    except subprocess.TimeoutExpired:
        execution_time = time.time() - start_time
        print(f"⏰ {suite_name} timed out after {timeout}s")
        return False, execution_time, f"Test suite timed out after {timeout} seconds"
        
    except Exception as e:
        execution_time = time.time() - start_time
        print(f"💥 {suite_name} failed with exception: {e}")
        return False, execution_time, str(e)

def find_latest_report(directory, pattern):
    """Find the latest report file matching pattern"""
    try:
        files = list(Path(directory).glob(pattern))
        if files:
            # Sort by modification time, return newest
            latest_file = max(files, key=lambda f: f.stat().st_mtime)
            return str(latest_file)
    except:
        pass
    return None

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description="Comprehensive test execution for Document Slides POC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py --all                    # Run all test suites
  python run_tests.py --performance            # Run only performance tests
  python run_tests.py --error-handling         # Run only error handling tests
  python run_tests.py --stress                 # Run only stress tests
  python run_tests.py --quality-gates-only     # Run only quality gate validation
  python run_tests.py --skip-dashboard         # Skip dashboard generation
  python run_tests.py --timeout 1200           # Set custom timeout (20 minutes)
        """
    )
    
    # Test suite selection
    parser.add_argument("--all", action="store_true", 
                       help="Run all test suites (default)")
    parser.add_argument("--performance", action="store_true",
                       help="Run performance benchmarks")
    parser.add_argument("--error-handling", action="store_true",
                       help="Run error handling tests")
    parser.add_argument("--stress", action="store_true", 
                       help="Run stress and large file tests")
    parser.add_argument("--existing", action="store_true",
                       help="Run existing test files")
    
    # Quality gates and reporting
    parser.add_argument("--quality-gates", action="store_true",
                       help="Run quality gate validation")
    parser.add_argument("--quality-gates-only", action="store_true",
                       help="Run only quality gate validation (no tests)")
    parser.add_argument("--dashboard", action="store_true",
                       help="Generate dashboard")
    parser.add_argument("--skip-dashboard", action="store_true",
                       help="Skip dashboard generation")
    
    # Configuration
    parser.add_argument("--timeout", type=int, default=600,
                       help="Timeout for each test suite in seconds (default: 600)")
    parser.add_argument("--config", help="Test configuration file")
    parser.add_argument("--output-dir", default="test_reports",
                       help="Output directory for reports")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")
    
    args = parser.parse_args()
    
    # If no specific suite is selected, run all
    if not any([args.performance, args.error_handling, args.stress, 
               args.existing, args.quality_gates_only]):
        args.all = True
    
    print("🧪 Document Slides POC - Comprehensive Test Suite")
    print("=" * 60)
    print(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python version: {sys.version.split()[0]}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Output directory: {args.output_dir}")
    
    # Ensure Python path is set correctly
    ensure_python_path()
    
    # Create necessary directories
    print("\n📁 Setting up test directories...")
    create_test_directories()
    
    # Track overall results
    overall_start_time = time.time()
    suite_results = {}
    report_files = {}
    
    # Run quality gates validation only if requested
    if args.quality_gates_only:
        print("\n🎯 Running quality gate validation only...")
        
        # Look for existing report files
        test_report = find_latest_report(".", "test_report_*.json")
        performance_report = find_latest_report(".", "performance_report_*.json") 
        memory_report = find_latest_report(".", "memory_stress_report_*.json")
        
        if not any([test_report, performance_report, memory_report]):
            print("❌ No existing test reports found. Run tests first.")
            sys.exit(1)
            
        # Run quality gates
        quality_cmd = [sys.executable, "quality_gates.py"]
        if test_report:
            quality_cmd.extend(["--test-results", test_report])
        if performance_report:
            quality_cmd.extend(["--performance-results", performance_report])
        if memory_report:
            quality_cmd.extend(["--memory-results", memory_report])
            
        try:
            result = subprocess.run(quality_cmd, timeout=args.timeout)
            if result.returncode == 0:
                print("✅ Quality gates validation completed successfully")
            else:
                print("❌ Quality gates validation failed")
                sys.exit(1)
        except Exception as e:
            print(f"💥 Quality gates validation failed: {e}")
            sys.exit(1)
            
        return
    
    # Define test suites to run
    test_suites = []
    
    if args.all or args.existing:
        # Find existing test files in root directory
        existing_tests = [f for f in os.listdir('.') if f.startswith('test_') and f.endswith('.py')]
        if existing_tests:
            test_suites.append({
                'name': 'Existing Tests',
                'script': 'test_runner.py',
                'args': ['--suite', 'existing_tests'],
                'timeout': args.timeout
            })
    
    if args.all or args.performance:
        test_suites.append({
            'name': 'Performance Benchmarks',
            'script': 'tests/performance/test_performance_benchmarks.py',
            'args': [],
            'timeout': args.timeout * 2  # Performance tests may take longer
        })
    
    if args.all or args.error_handling:
        test_suites.append({
            'name': 'Error Handling Tests',
            'script': 'tests/error_handling/test_error_scenarios.py', 
            'args': [],
            'timeout': args.timeout
        })
    
    if args.all or args.stress:
        test_suites.append({
            'name': 'Stress & Memory Tests',
            'script': 'tests/stress/test_large_file_handling.py',
            'args': [],
            'timeout': args.timeout * 3  # Stress tests may take much longer
        })
    
    # Run test suites
    for suite in test_suites:
        if not os.path.exists(suite['script']):
            print(f"⚠️ Skipping {suite['name']} - script not found: {suite['script']}")
            continue
            
        success, exec_time, output = run_test_suite(
            suite['name'], 
            suite['script'], 
            suite['timeout']
        )
        
        suite_results[suite['name']] = {
            'success': success,
            'execution_time': exec_time,
            'output': output
        }
        
        if args.verbose:
            print(f"\nOutput from {suite['name']}:")
            print("-" * 40)
            print(output)
            print("-" * 40)
    
    # Wait a moment for files to be written
    time.sleep(2)
    
    # Find generated report files
    print("\n📊 Collecting test reports...")
    
    report_files['test_report'] = find_latest_report(".", "test_report_*.json")
    report_files['performance_report'] = find_latest_report(".", "performance_report_*.json")
    report_files['memory_report'] = find_latest_report(".", "memory_stress_report_*.json")
    
    for report_type, file_path in report_files.items():
        if file_path:
            print(f"✓ Found {report_type}: {file_path}")
        else:
            print(f"⚠️ No {report_type} found")
    
    # Run quality gates validation if requested
    if args.all or args.quality_gates:
        print("\n🎯 Running quality gate validation...")
        
        quality_cmd = [sys.executable, "quality_gates.py"]
        
        # Add available reports
        for report_type, file_path in report_files.items():
            if file_path:
                if report_type == 'test_report':
                    quality_cmd.extend(["--test-results", file_path])
                elif report_type == 'performance_report':
                    quality_cmd.extend(["--performance-results", file_path])
                elif report_type == 'memory_report':
                    quality_cmd.extend(["--memory-results", file_path])
        
        try:
            result = subprocess.run(quality_cmd, timeout=args.timeout)
            quality_success = result.returncode == 0
            
            if quality_success:
                print("✅ Quality gates validation completed successfully")
            else:
                print("❌ Quality gates validation failed")
                
            suite_results['Quality Gates'] = {
                'success': quality_success,
                'execution_time': 0,
                'output': 'Quality gate validation'
            }
            
            # Find quality gate report
            report_files['quality_report'] = find_latest_report(".", "quality_gate_report_*.json")
            
        except Exception as e:
            print(f"💥 Quality gates validation failed: {e}")
            suite_results['Quality Gates'] = {
                'success': False,
                'execution_time': 0,
                'output': str(e)
            }
    
    # Generate dashboard if requested
    if (args.all or args.dashboard) and not args.skip_dashboard:
        print("\n📈 Generating test dashboard...")
        
        try:
            dashboard_cmd = [sys.executable, "test_dashboard.py"]
            
            # Add primary test data
            if report_files.get('test_report'):
                dashboard_cmd.extend(["--test-data", report_files['test_report']])
            elif report_files.get('performance_report'):
                # Use performance report as primary if no test report
                dashboard_cmd.extend(["--test-data", report_files['performance_report']])
            else:
                print("⚠️ No test data available for dashboard generation")
                dashboard_cmd = None
            
            if dashboard_cmd:
                # Add additional data
                if report_files.get('performance_report') and report_files['performance_report'] != report_files.get('test_report'):
                    dashboard_cmd.extend(["--performance-data", report_files['performance_report']])
                if report_files.get('memory_report'):
                    dashboard_cmd.extend(["--memory-data", report_files['memory_report']])
                if report_files.get('quality_report'):
                    dashboard_cmd.extend(["--quality-data", report_files['quality_report']])
                
                dashboard_cmd.extend(["--output-dir", args.output_dir])
                
                result = subprocess.run(dashboard_cmd, timeout=args.timeout)
                
                if result.returncode == 0:
                    print("✅ Dashboard generated successfully")
                    
                    # Find dashboard file
                    dashboard_file = find_latest_report(
                        os.path.join(args.output_dir, "dashboard"), 
                        "dashboard_*.html"
                    )
                    if dashboard_file:
                        print(f"🌐 Dashboard available at: file://{os.path.abspath(dashboard_file)}")
                else:
                    print("❌ Dashboard generation failed")
                    
        except Exception as e:
            print(f"💥 Dashboard generation failed: {e}")
    
    # Calculate overall execution time
    total_execution_time = time.time() - overall_start_time
    
    # Print final summary
    print("\n" + "=" * 60)
    print("📋 FINAL TEST EXECUTION SUMMARY")
    print("=" * 60)
    
    print(f"Total execution time: {total_execution_time:.2f} seconds")
    print(f"End time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Summary of all suites
    total_suites = len(suite_results)
    successful_suites = sum(1 for result in suite_results.values() if result['success'])
    failed_suites = total_suites - successful_suites
    
    print(f"\nTest Suites: {successful_suites}/{total_suites} passed")
    
    for suite_name, result in suite_results.items():
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"  {status} {suite_name} ({result['execution_time']:.2f}s)")
    
    # Overall status
    overall_success = failed_suites == 0
    
    print(f"\n{'✅ OVERALL SUCCESS' if overall_success else '❌ OVERALL FAILURE'}")
    
    if not overall_success:
        print(f"\n❌ {failed_suites} test suite(s) failed")
        print("Check individual test outputs and reports for details")
    
    # List generated reports
    print(f"\n📁 Generated reports in: {os.path.abspath(args.output_dir)}")
    for report_type, file_path in report_files.items():
        if file_path:
            print(f"  📄 {report_type}: {file_path}")
    
    # Exit with appropriate code
    sys.exit(0 if overall_success else 1)

if __name__ == "__main__":
    main()