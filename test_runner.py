#!/usr/bin/env python3
"""
Automated test runner with coverage reporting and quality gates
Orchestrates all test suites and generates comprehensive reports
"""
import os
import sys
import subprocess
import json
import time
import argparse
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import tempfile
import shutil
from pathlib import Path

@dataclass
class TestResults:
    """Test execution results"""
    suite_name: str
    tests_run: int
    tests_passed: int
    tests_failed: int
    tests_skipped: int
    execution_time: float
    success: bool
    errors: List[str]
    output_file: Optional[str] = None

@dataclass
class CoverageResults:
    """Code coverage results"""
    line_coverage: float
    branch_coverage: float
    function_coverage: float
    total_lines: int
    covered_lines: int
    missing_lines: List[int]
    report_file: Optional[str] = None

@dataclass
class QualityGateResults:
    """Quality gate evaluation results"""
    gate_name: str
    threshold: float
    actual_value: float
    passed: bool
    message: str

class TestRunner:
    """Automated test runner with comprehensive reporting"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config = self.load_config(config_file)
        self.results_dir = "test_results"
        self.reports_dir = "test_reports"
        self.timestamp = int(time.time())
        
        # Create output directories
        os.makedirs(self.results_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
        
        self.test_results: List[TestResults] = []
        self.coverage_results: Optional[CoverageResults] = None
        self.quality_gate_results: List[QualityGateResults] = []
        
    def load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """Load test runner configuration"""
        default_config = {
            "test_suites": [
                {
                    "name": "unit_tests",
                    "path": "tests/",
                    "pattern": "test_*.py",
                    "timeout": 300,
                    "enabled": True
                },
                {
                    "name": "performance_tests",
                    "path": "tests/performance/",
                    "pattern": "test_performance_*.py",
                    "timeout": 600,
                    "enabled": True
                },
                {
                    "name": "error_handling_tests",
                    "path": "tests/error_handling/",
                    "pattern": "test_error_*.py",
                    "timeout": 300,
                    "enabled": True
                },
                {
                    "name": "stress_tests",
                    "path": "tests/stress/",
                    "pattern": "test_large_*.py",
                    "timeout": 900,
                    "enabled": True
                }
            ],
            "coverage": {
                "enabled": True,
                "source_dirs": ["lib/", "api/"],
                "exclude_patterns": ["*/test*", "*/tests/*", "*/__pycache__/*"],
                "min_line_coverage": 70.0,
                "min_branch_coverage": 60.0
            },
            "quality_gates": [
                {
                    "name": "minimum_test_pass_rate",
                    "threshold": 90.0,
                    "critical": True
                },
                {
                    "name": "minimum_line_coverage",
                    "threshold": 70.0,
                    "critical": True
                },
                {
                    "name": "maximum_test_execution_time",
                    "threshold": 1800.0,  # 30 minutes
                    "critical": False
                },
                {
                    "name": "maximum_memory_usage_mb",
                    "threshold": 1000.0,
                    "critical": False
                }
            ],
            "reporting": {
                "generate_html": True,
                "generate_json": True,
                "generate_junit": True,
                "include_performance_charts": True
            }
        }
        
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                # Merge user config with defaults
                default_config.update(user_config)
            except Exception as e:
                print(f"Warning: Could not load config file {config_file}: {e}")
                
        return default_config
        
    def install_dependencies(self) -> bool:
        """Install testing dependencies"""
        dependencies = [
            "coverage",
            "pytest",
            "pytest-html",
            "pytest-cov",
            "pytest-xdist",
            "psutil",
            "memory-profiler"
        ]
        
        print("Installing test dependencies...")
        try:
            for dep in dependencies:
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", dep
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode != 0:
                    print(f"Warning: Could not install {dep}: {result.stderr}")
                    
            return True
        except Exception as e:
            print(f"Error installing dependencies: {e}")
            return False
            
    def run_test_suite(self, suite_config: Dict[str, Any]) -> TestResults:
        """Run a single test suite"""
        suite_name = suite_config["name"]
        test_path = suite_config["path"]
        pattern = suite_config.get("pattern", "test_*.py")
        timeout = suite_config.get("timeout", 300)
        
        print(f"Running test suite: {suite_name}")
        print(f"  Path: {test_path}")
        print(f"  Pattern: {pattern}")
        
        start_time = time.time()
        errors = []
        
        # Create output file for this suite
        output_file = os.path.join(self.results_dir, f"{suite_name}_{self.timestamp}.txt")
        
        try:
            # Check if test path exists
            if not os.path.exists(test_path):
                print(f"  Test path not found: {test_path}")
                return TestResults(
                    suite_name=suite_name,
                    tests_run=0,
                    tests_passed=0,
                    tests_failed=1,
                    tests_skipped=0,
                    execution_time=0,
                    success=False,
                    errors=[f"Test path not found: {test_path}"],
                    output_file=None
                )
                
            # Run tests using unittest discovery
            cmd = [
                sys.executable, "-m", "unittest", "discover",
                "-s", test_path,
                "-p", pattern,
                "-v"
            ]
            
            print(f"  Command: {' '.join(cmd)}")
            
            with open(output_file, 'w') as f:
                result = subprocess.run(
                    cmd,
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    text=True,
                    timeout=timeout,
                    cwd=os.getcwd()
                )
                
            execution_time = time.time() - start_time
            
            # Parse test results from output
            tests_run, tests_passed, tests_failed, tests_skipped = self.parse_unittest_output(output_file)
            
            success = tests_failed == 0 and tests_run > 0
            
            print(f"  Results: {tests_run} run, {tests_passed} passed, {tests_failed} failed, {tests_skipped} skipped")
            print(f"  Execution time: {execution_time:.2f} seconds")
            
            return TestResults(
                suite_name=suite_name,
                tests_run=tests_run,
                tests_passed=tests_passed,
                tests_failed=tests_failed,
                tests_skipped=tests_skipped,
                execution_time=execution_time,
                success=success,
                errors=errors,
                output_file=output_file
            )
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            errors.append(f"Test suite timed out after {timeout} seconds")
            
            return TestResults(
                suite_name=suite_name,
                tests_run=0,
                tests_passed=0,
                tests_failed=1,
                tests_skipped=0,
                execution_time=execution_time,
                success=False,
                errors=errors,
                output_file=output_file
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            errors.append(f"Error running test suite: {str(e)}")
            
            return TestResults(
                suite_name=suite_name,
                tests_run=0,
                tests_passed=0,
                tests_failed=1,
                tests_skipped=0,
                execution_time=execution_time,
                success=False,
                errors=errors,
                output_file=output_file
            )
            
    def parse_unittest_output(self, output_file: str) -> Tuple[int, int, int, int]:
        """Parse unittest output to extract test counts"""
        tests_run = 0
        tests_failed = 0
        tests_skipped = 0
        
        try:
            with open(output_file, 'r') as f:
                content = f.read()
                
            # Look for result summary line
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                
                # Look for pattern like "Ran 15 tests in 2.345s"
                if line.startswith("Ran ") and " tests in " in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        tests_run = int(parts[1])
                        
                # Look for failure/error counts
                if "FAILED" in line and "failures=" in line:
                    # Parse something like "FAILED (failures=2, errors=1)"
                    for part in line.split():
                        if part.startswith("failures="):
                            tests_failed += int(part.split("=")[1].rstrip(",)"))
                        elif part.startswith("errors="):
                            tests_failed += int(part.split("=")[1].rstrip(",)"))
                        elif part.startswith("skipped="):
                            tests_skipped = int(part.split("=")[1].rstrip(",)"))
                            
        except Exception as e:
            print(f"Warning: Could not parse test output: {e}")
            
        tests_passed = tests_run - tests_failed - tests_skipped
        return tests_run, tests_passed, tests_failed, tests_skipped
        
    def run_coverage_analysis(self) -> Optional[CoverageResults]:
        """Run code coverage analysis"""
        if not self.config["coverage"]["enabled"]:
            return None
            
        print("Running code coverage analysis...")
        
        source_dirs = self.config["coverage"]["source_dirs"]
        exclude_patterns = self.config["coverage"]["exclude_patterns"]
        
        try:
            # Install coverage if not available
            subprocess.run([sys.executable, "-m", "pip", "install", "coverage"], 
                         capture_output=True, timeout=60)
            
            # Run coverage on all test suites
            coverage_file = os.path.join(self.results_dir, f"coverage_{self.timestamp}.xml")
            html_dir = os.path.join(self.reports_dir, f"coverage_html_{self.timestamp}")
            
            # Combine all test paths
            test_paths = []
            for suite in self.config["test_suites"]:
                if suite.get("enabled", True) and os.path.exists(suite["path"]):
                    test_paths.append(suite["path"])
                    
            if not test_paths:
                print("  No test paths found for coverage analysis")
                return None
                
            # Run coverage
            cmd = [
                sys.executable, "-m", "coverage", "run",
                "--source=" + ",".join(source_dirs),
                "--omit=" + ",".join(exclude_patterns),
                "-m", "unittest", "discover",
                "-s", test_paths[0],  # Use first test path as discovery root
                "-p", "test_*.py"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode != 0:
                print(f"  Coverage run failed: {result.stderr}")
                return None
                
            # Generate reports
            # XML report
            subprocess.run([
                sys.executable, "-m", "coverage", "xml",
                "-o", coverage_file
            ], timeout=60)
            
            # HTML report
            subprocess.run([
                sys.executable, "-m", "coverage", "html",
                "-d", html_dir
            ], timeout=60)
            
            # Get coverage statistics
            result = subprocess.run([
                sys.executable, "-m", "coverage", "report"
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                coverage_stats = self.parse_coverage_output(result.stdout)
                
                return CoverageResults(
                    line_coverage=coverage_stats.get("line_coverage", 0.0),
                    branch_coverage=coverage_stats.get("branch_coverage", 0.0),
                    function_coverage=coverage_stats.get("function_coverage", 0.0),
                    total_lines=coverage_stats.get("total_lines", 0),
                    covered_lines=coverage_stats.get("covered_lines", 0),
                    missing_lines=coverage_stats.get("missing_lines", []),
                    report_file=html_dir
                )
            else:
                print(f"  Coverage report failed: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"  Coverage analysis failed: {e}")
            return None
            
    def parse_coverage_output(self, output: str) -> Dict[str, Any]:
        """Parse coverage report output"""
        stats = {}
        
        try:
            lines = output.split('\n')
            for line in lines:
                line = line.strip()
                
                # Look for total coverage line
                if line.startswith("TOTAL"):
                    parts = line.split()
                    if len(parts) >= 4:
                        # Extract coverage percentage
                        coverage_str = parts[-1].rstrip('%')
                        if coverage_str.isdigit():
                            stats["line_coverage"] = float(coverage_str)
                            
                        # Extract line counts if available
                        if len(parts) >= 3:
                            try:
                                total_lines = int(parts[1])
                                covered_lines = int(parts[2])
                                stats["total_lines"] = total_lines
                                stats["covered_lines"] = covered_lines
                            except:
                                pass
                                
        except Exception as e:
            print(f"Warning: Could not parse coverage output: {e}")
            
        return stats
        
    def evaluate_quality_gates(self):
        """Evaluate quality gates based on test results"""
        print("Evaluating quality gates...")
        
        for gate_config in self.config["quality_gates"]:
            gate_name = gate_config["name"]
            threshold = gate_config["threshold"]
            is_critical = gate_config.get("critical", False)
            
            actual_value, passed, message = self.evaluate_gate(gate_name, threshold)
            
            result = QualityGateResults(
                gate_name=gate_name,
                threshold=threshold,
                actual_value=actual_value,
                passed=passed,
                message=message
            )
            
            self.quality_gate_results.append(result)
            
            status = "PASS" if passed else "FAIL"
            criticality = "CRITICAL" if is_critical else "WARNING"
            
            print(f"  {gate_name}: {status} ({actual_value:.2f} vs {threshold:.2f}) [{criticality}]")
            if not passed:
                print(f"    {message}")
                
    def evaluate_gate(self, gate_name: str, threshold: float) -> Tuple[float, bool, str]:
        """Evaluate a specific quality gate"""
        if gate_name == "minimum_test_pass_rate":
            total_tests = sum(r.tests_run for r in self.test_results)
            passed_tests = sum(r.tests_passed for r in self.test_results)
            
            if total_tests == 0:
                return 0.0, False, "No tests were run"
                
            pass_rate = (passed_tests / total_tests) * 100
            passed = pass_rate >= threshold
            message = f"Test pass rate: {pass_rate:.1f}% (required: {threshold:.1f}%)"
            
            return pass_rate, passed, message
            
        elif gate_name == "minimum_line_coverage":
            if self.coverage_results is None:
                return 0.0, False, "Coverage analysis not available"
                
            coverage = self.coverage_results.line_coverage
            passed = coverage >= threshold
            message = f"Line coverage: {coverage:.1f}% (required: {threshold:.1f}%)"
            
            return coverage, passed, message
            
        elif gate_name == "maximum_test_execution_time":
            total_time = sum(r.execution_time for r in self.test_results)
            passed = total_time <= threshold
            message = f"Total execution time: {total_time:.1f}s (max: {threshold:.1f}s)"
            
            return total_time, passed, message
            
        elif gate_name == "maximum_memory_usage_mb":
            # This would require parsing memory usage from performance tests
            # For now, return a placeholder
            return 0.0, True, "Memory usage check not implemented"
            
        else:
            return 0.0, False, f"Unknown quality gate: {gate_name}"
            
    def generate_reports(self):
        """Generate comprehensive test reports"""
        print("Generating test reports...")
        
        report_data = {
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.timestamp)),
            "config": self.config,
            "test_results": [asdict(r) for r in self.test_results],
            "coverage_results": asdict(self.coverage_results) if self.coverage_results else None,
            "quality_gates": [asdict(g) for g in self.quality_gate_results],
            "summary": self.calculate_summary()
        }
        
        # JSON report
        json_file = os.path.join(self.reports_dir, f"test_report_{self.timestamp}.json")
        with open(json_file, 'w') as f:
            json.dump(report_data, f, indent=2)
            
        # HTML report
        html_file = os.path.join(self.reports_dir, f"test_report_{self.timestamp}.html")
        self.generate_html_report(html_file, report_data)
        
        # Text summary
        summary_file = os.path.join(self.reports_dir, f"test_summary_{self.timestamp}.txt")
        self.generate_text_summary(summary_file, report_data)
        
        print(f"  JSON Report: {os.path.abspath(json_file)}")
        print(f"  HTML Report: {os.path.abspath(html_file)}")
        print(f"  Text Summary: {os.path.abspath(summary_file)}")
        
    def calculate_summary(self) -> Dict[str, Any]:
        """Calculate overall test summary"""
        total_tests = sum(r.tests_run for r in self.test_results)
        total_passed = sum(r.tests_passed for r in self.test_results)
        total_failed = sum(r.tests_failed for r in self.test_results)
        total_skipped = sum(r.tests_skipped for r in self.test_results)
        total_time = sum(r.execution_time for r in self.test_results)
        
        suites_passed = sum(1 for r in self.test_results if r.success)
        suites_failed = len(self.test_results) - suites_passed
        
        critical_gates_failed = sum(1 for g in self.quality_gate_results 
                                  if not g.passed and self.is_gate_critical(g.gate_name))
        
        overall_success = (total_failed == 0 and suites_failed == 0 and critical_gates_failed == 0)
        
        return {
            "overall_success": overall_success,
            "total_test_suites": len(self.test_results),
            "suites_passed": suites_passed,
            "suites_failed": suites_failed,
            "total_tests": total_tests,
            "tests_passed": total_passed,
            "tests_failed": total_failed,
            "tests_skipped": total_skipped,
            "total_execution_time": total_time,
            "pass_rate": (total_passed / total_tests * 100) if total_tests > 0 else 0,
            "coverage_percentage": self.coverage_results.line_coverage if self.coverage_results else 0,
            "critical_gates_failed": critical_gates_failed
        }
        
    def is_gate_critical(self, gate_name: str) -> bool:
        """Check if a quality gate is critical"""
        for gate_config in self.config["quality_gates"]:
            if gate_config["name"] == gate_name:
                return gate_config.get("critical", False)
        return False
        
    def generate_html_report(self, file_path: str, report_data: Dict[str, Any]):
        """Generate HTML test report"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Test Report - {report_data['timestamp']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
        .metric {{ background-color: #e8f4fd; padding: 15px; border-radius: 5px; text-align: center; }}
        .success {{ background-color: #d4edda; }}
        .failure {{ background-color: #f8d7da; }}
        .warning {{ background-color: #fff3cd; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .passed {{ color: green; font-weight: bold; }}
        .failed {{ color: red; font-weight: bold; }}
        .skipped {{ color: orange; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Automated Test Report</h1>
        <p>Generated: {report_data['timestamp']}</p>
        <p>Status: {'✅ SUCCESS' if report_data['summary']['overall_success'] else '❌ FAILURE'}</p>
    </div>
    
    <div class="summary">
        <div class="metric {'success' if report_data['summary']['overall_success'] else 'failure'}">
            <h3>Overall Status</h3>
            <p>{'PASS' if report_data['summary']['overall_success'] else 'FAIL'}</p>
        </div>
        <div class="metric">
            <h3>Test Suites</h3>
            <p>{report_data['summary']['suites_passed']}/{report_data['summary']['total_test_suites']} Passed</p>
        </div>
        <div class="metric">
            <h3>Total Tests</h3>
            <p>{report_data['summary']['tests_passed']}/{report_data['summary']['total_tests']} Passed</p>
        </div>
        <div class="metric">
            <h3>Pass Rate</h3>
            <p>{report_data['summary']['pass_rate']:.1f}%</p>
        </div>
        <div class="metric">
            <h3>Coverage</h3>
            <p>{report_data['summary']['coverage_percentage']:.1f}%</p>
        </div>
        <div class="metric">
            <h3>Execution Time</h3>
            <p>{report_data['summary']['total_execution_time']:.1f}s</p>
        </div>
    </div>
    
    <h2>Test Suite Results</h2>
    <table>
        <tr>
            <th>Suite Name</th>
            <th>Status</th>
            <th>Tests Run</th>
            <th>Passed</th>
            <th>Failed</th>
            <th>Skipped</th>
            <th>Execution Time</th>
        </tr>
"""
        
        for result in report_data['test_results']:
            status_class = 'passed' if result['success'] else 'failed'
            html_content += f"""
        <tr>
            <td>{result['suite_name']}</td>
            <td class="{status_class}">{'PASS' if result['success'] else 'FAIL'}</td>
            <td>{result['tests_run']}</td>
            <td class="passed">{result['tests_passed']}</td>
            <td class="failed">{result['tests_failed']}</td>
            <td class="skipped">{result['tests_skipped']}</td>
            <td>{result['execution_time']:.2f}s</td>
        </tr>
"""
        
        html_content += """
    </table>
    
    <h2>Quality Gates</h2>
    <table>
        <tr>
            <th>Gate Name</th>
            <th>Status</th>
            <th>Actual Value</th>
            <th>Threshold</th>
            <th>Message</th>
        </tr>
"""
        
        for gate in report_data['quality_gates']:
            status_class = 'passed' if gate['passed'] else 'failed'
            html_content += f"""
        <tr>
            <td>{gate['gate_name']}</td>
            <td class="{status_class}">{'PASS' if gate['passed'] else 'FAIL'}</td>
            <td>{gate['actual_value']:.2f}</td>
            <td>{gate['threshold']:.2f}</td>
            <td>{gate['message']}</td>
        </tr>
"""
        
        html_content += """
    </table>
</body>
</html>
"""
        
        with open(file_path, 'w') as f:
            f.write(html_content)
            
    def generate_text_summary(self, file_path: str, report_data: Dict[str, Any]):
        """Generate text summary report"""
        with open(file_path, 'w') as f:
            f.write("AUTOMATED TEST EXECUTION SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Timestamp: {report_data['timestamp']}\n")
            f.write(f"Overall Status: {'PASS' if report_data['summary']['overall_success'] else 'FAIL'}\n\n")
            
            # Summary statistics
            summary = report_data['summary']
            f.write("SUMMARY STATISTICS\n")
            f.write("-" * 30 + "\n")
            f.write(f"Test Suites: {summary['suites_passed']}/{summary['total_test_suites']} passed\n")
            f.write(f"Total Tests: {summary['tests_passed']}/{summary['total_tests']} passed\n")
            f.write(f"Pass Rate: {summary['pass_rate']:.1f}%\n")
            f.write(f"Code Coverage: {summary['coverage_percentage']:.1f}%\n")
            f.write(f"Execution Time: {summary['total_execution_time']:.1f} seconds\n")
            f.write(f"Critical Gates Failed: {summary['critical_gates_failed']}\n\n")
            
            # Test suite details
            f.write("TEST SUITE RESULTS\n")
            f.write("-" * 30 + "\n")
            for result in report_data['test_results']:
                status = "PASS" if result['success'] else "FAIL"
                f.write(f"{result['suite_name']}: {status}\n")
                f.write(f"  Tests: {result['tests_run']} run, {result['tests_passed']} passed, {result['tests_failed']} failed\n")
                f.write(f"  Time: {result['execution_time']:.2f} seconds\n")
                if result['errors']:
                    f.write(f"  Errors: {'; '.join(result['errors'])}\n")
                f.write("\n")
                
            # Quality gates
            f.write("QUALITY GATE RESULTS\n")
            f.write("-" * 30 + "\n")
            for gate in report_data['quality_gates']:
                status = "PASS" if gate['passed'] else "FAIL"
                f.write(f"{gate['gate_name']}: {status}\n")
                f.write(f"  {gate['message']}\n\n")
                
    def run_all_tests(self):
        """Run all test suites and generate reports"""
        print("Starting automated test execution...")
        print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Install dependencies
        if not self.install_dependencies():
            print("Warning: Could not install all dependencies")
            
        # Run each test suite
        for suite_config in self.config["test_suites"]:
            if suite_config.get("enabled", True):
                result = self.run_test_suite(suite_config)
                self.test_results.append(result)
            else:
                print(f"Skipping disabled test suite: {suite_config['name']}")
                
        # Run coverage analysis
        self.coverage_results = self.run_coverage_analysis()
        
        # Evaluate quality gates
        self.evaluate_quality_gates()
        
        # Generate reports
        self.generate_reports()
        
        # Print final summary
        self.print_final_summary()
        
        # Return overall success status
        summary = self.calculate_summary()
        return summary["overall_success"]
        
    def print_final_summary(self):
        """Print final test execution summary"""
        print("\n" + "=" * 60)
        print("TEST EXECUTION COMPLETE")
        print("=" * 60)
        
        summary = self.calculate_summary()
        
        status = "✅ SUCCESS" if summary["overall_success"] else "❌ FAILURE"
        print(f"Overall Status: {status}")
        print(f"Test Suites: {summary['suites_passed']}/{summary['total_test_suites']} passed")
        print(f"Total Tests: {summary['tests_passed']}/{summary['total_tests']} passed")
        print(f"Pass Rate: {summary['pass_rate']:.1f}%")
        print(f"Code Coverage: {summary['coverage_percentage']:.1f}%")
        print(f"Execution Time: {summary['total_execution_time']:.1f} seconds")
        
        if summary['critical_gates_failed'] > 0:
            print(f"❌ {summary['critical_gates_failed']} critical quality gates failed")
        else:
            print("✅ All critical quality gates passed")
            
        print(f"\nReports generated in: {os.path.abspath(self.reports_dir)}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Automated test runner with coverage and quality gates")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--install-deps", action="store_true", help="Install dependencies only")
    parser.add_argument("--suite", help="Run specific test suite only")
    parser.add_argument("--no-coverage", action="store_true", help="Skip coverage analysis")
    parser.add_argument("--no-reports", action="store_true", help="Skip report generation")
    
    args = parser.parse_args()
    
    if args.install_deps:
        runner = TestRunner()
        success = runner.install_dependencies()
        sys.exit(0 if success else 1)
        
    runner = TestRunner(args.config)
    
    if args.no_coverage:
        runner.config["coverage"]["enabled"] = False
        
    if args.suite:
        # Filter to specific suite
        runner.config["test_suites"] = [
            suite for suite in runner.config["test_suites"] 
            if suite["name"] == args.suite
        ]
        
    success = runner.run_all_tests()
    
    if not args.no_reports and not success:
        print("\n❌ Tests failed - check reports for details")
        
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()