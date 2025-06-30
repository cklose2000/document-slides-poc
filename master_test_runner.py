#!/usr/bin/env python3
"""
Master Test Runner for Document-Slides-POC
Integrates all testing components created by parallel agents

This script orchestrates:
- Agent 1: Core testing infrastructure
- Agent 2: Document extractor tests
- Agent 3: Template system tests
- Agent 4: API endpoint tests
- Agent 5: End-to-end workflow tests
- Agent 6: Performance and automation tests
"""

import os
import sys
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

class MasterTestRunner:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.start_time = datetime.now()
        self.results = {}
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def run_command(self, command: str, timeout: int = 300) -> Dict:
        """Run a command and capture results"""
        try:
            self.log(f"Running: {command}")
            start = time.time()
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.project_root
            )
            duration = time.time() - start
            
            return {
                "command": command,
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration": duration
            }
        except subprocess.TimeoutExpired:
            return {
                "command": command,
                "success": False,
                "error": "Command timed out",
                "duration": timeout
            }
        except Exception as e:
            return {
                "command": command,
                "success": False,
                "error": str(e),
                "duration": 0
            }
    
    def check_dependencies(self) -> bool:
        """Check if all test dependencies are installed"""
        self.log("Checking test dependencies...")
        
        dependencies = [
            "pytest",
            "coverage",
            "pytest-cov",
            "pytest-html",
            "pytest-xdist",
            "pytest-benchmark",
            "requests",
            "openpyxl",
            "python-docx",
            "python-pptx"
        ]
        
        missing = []
        for dep in dependencies:
            try:
                __import__(dep.replace('-', '_'))
            except ImportError:
                missing.append(dep)
        
        if missing:
            self.log(f"Missing dependencies: {', '.join(missing)}", "ERROR")
            self.log("Run: pip install -r requirements-test.txt", "INFO")
            return False
        
        self.log("All dependencies satisfied ✓")
        return True
    
    def run_agent_tests(self, agent_name: str, test_files: List[str]) -> Dict:
        """Run tests for a specific agent"""
        self.log(f"Running {agent_name} tests...", "INFO")
        
        results = {
            "agent": agent_name,
            "tests": [],
            "overall_success": True,
            "total_duration": 0
        }
        
        for test_file in test_files:
            if os.path.exists(test_file):
                result = self.run_command(f"python {test_file}")
                results["tests"].append(result)
                results["total_duration"] += result.get("duration", 0)
                if not result.get("success", False):
                    results["overall_success"] = False
                    self.log(f"Failed: {test_file}", "ERROR")
                else:
                    self.log(f"Passed: {test_file}", "SUCCESS")
            else:
                self.log(f"Test file not found: {test_file}", "WARNING")
                results["overall_success"] = False
        
        return results
    
    def run_pytest_suite(self) -> Dict:
        """Run the complete pytest suite"""
        self.log("Running pytest suite with coverage...", "INFO")
        
        cmd = "python -m pytest tests/ --cov=lib --cov-report=html --cov-report=xml --cov-report=term --html=reports/pytest_report.html --self-contained-html -v"
        result = self.run_command(cmd, timeout=600)
        
        if result.get("success"):
            self.log("Pytest suite completed successfully ✓", "SUCCESS")
        else:
            self.log("Pytest suite failed ✗", "ERROR")
        
        return result
    
    def generate_master_report(self) -> str:
        """Generate comprehensive test report"""
        self.log("Generating master test report...", "INFO")
        
        report_path = self.project_root / "reports" / f"master_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        os.makedirs(report_path.parent, exist_ok=True)
        
        total_tests = sum(len(r.get("tests", [])) for r in self.results.values() if isinstance(r, dict))
        successful_tests = sum(
            sum(1 for t in r.get("tests", []) if t.get("success"))
            for r in self.results.values() if isinstance(r, dict)
        )
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        report_content = f"""# Document-Slides-POC Master Test Report

## Test Execution Summary
- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Total Execution Time**: {(datetime.now() - self.start_time).total_seconds():.2f} seconds
- **Total Tests**: {total_tests}
- **Successful**: {successful_tests}
- **Success Rate**: {success_rate:.1f}%
- **Overall Status**: {"✅ PASS" if success_rate >= 80 else "❌ FAIL"}

## Agent Results

"""
        
        for agent, result in self.results.items():
            if isinstance(result, dict) and "agent" in result:
                status = "✅ PASS" if result.get("overall_success") else "❌ FAIL"
                duration = result.get("total_duration", 0)
                test_count = len(result.get("tests", []))
                
                report_content += f"""### {result['agent']} {status}
- Tests: {test_count}
- Duration: {duration:.2f}s
- Status: {status}

"""
                
                for test in result.get("tests", []):
                    test_status = "✅" if test.get("success") else "❌"
                    test_name = os.path.basename(test.get("command", "Unknown"))
                    test_duration = test.get("duration", 0)
                    report_content += f"  - {test_status} {test_name} ({test_duration:.2f}s)\n"
                
                report_content += "\n"
        
        # Add pytest results
        pytest_result = self.results.get("pytest")
        if pytest_result:
            status = "✅ PASS" if pytest_result.get("success") else "❌ FAIL"
            report_content += f"""### Pytest Suite {status}
- Duration: {pytest_result.get('duration', 0):.2f}s
- Status: {status}

"""
        
        report_content += f"""## Quality Assessment

### Coverage Analysis
- HTML Report: `reports/htmlcov/index.html`
- XML Report: `reports/coverage.xml`

### Test Categories
1. **Unit Tests**: Component-level validation
2. **Integration Tests**: Multi-component interactions
3. **API Tests**: Endpoint and service validation
4. **End-to-End Tests**: Complete workflow validation
5. **Performance Tests**: Speed and efficiency validation
6. **Error Handling**: Robustness and edge case validation

### Recommendations
{"- ✅ System is production ready" if success_rate >= 90 else "- ⚠️ Review failed tests before production deployment" if success_rate >= 70 else "- ❌ Significant issues found - not ready for production"}
{"- ✅ Excellent test coverage" if success_rate >= 95 else "- 📊 Consider expanding test coverage" if success_rate >= 80 else "- 📈 Improve test reliability"}
- 🚀 Continue with deployment pipeline
- 📊 Monitor performance metrics in production
- 🔄 Set up automated testing in CI/CD

---
*Generated by Document-Slides-POC Master Test Runner*
"""
        
        with open(report_path, 'w') as f:
            f.write(report_content)
        
        self.log(f"Master report generated: {report_path}", "SUCCESS")
        return str(report_path)
    
    def run_all_tests(self):
        """Run all test suites"""
        self.log("Starting Document-Slides-POC Master Test Suite", "INFO")
        self.log("=" * 60, "INFO")
        
        # Check dependencies
        if not self.check_dependencies():
            self.log("Dependency check failed. Exiting.", "ERROR")
            sys.exit(1)
        
        # Agent test configurations
        agent_configs = {
            "Agent 1 - Infrastructure": [
                "run_tests.py",
                "tests/test_runner_example.py"
            ],
            "Agent 2 - Document Extractors": [
                "tests/unit/test_pdf_extractor.py",
                "tests/unit/test_excel_extractor.py", 
                "tests/unit/test_word_extractor.py"
            ],
            "Agent 3 - Template System": [
                "test_template_system.py",
                "test_branded_slide_generator.py"
            ],
            "Agent 4 - API Endpoints": [
                "validate_api.py",
                "test_api_endpoints.py"
            ],
            "Agent 5 - End-to-End Workflows": [
                "validate_system.py",
                "test_workflow_runner.py"
            ],
            "Agent 6 - Performance & Automation": [
                "test_runner.py",
                "quality_gates.py"
            ]
        }
        
        # Run tests for each agent
        for agent_name, test_files in agent_configs.items():
            try:
                result = self.run_agent_tests(agent_name, test_files)
                self.results[agent_name] = result
            except Exception as e:
                self.log(f"Error running {agent_name}: {str(e)}", "ERROR")
                self.results[agent_name] = {"agent": agent_name, "error": str(e), "overall_success": False}
        
        # Run pytest suite
        try:
            pytest_result = self.run_pytest_suite()
            self.results["pytest"] = pytest_result
        except Exception as e:
            self.log(f"Error running pytest: {str(e)}", "ERROR")
            self.results["pytest"] = {"error": str(e), "success": False}
        
        # Generate master report
        report_path = self.generate_master_report()
        
        # Final summary
        self.log("=" * 60, "INFO")
        self.log("Master Test Suite Completed", "INFO")
        self.log(f"Report: {report_path}", "INFO")
        self.log("=" * 60, "INFO")
        
        # Calculate overall success
        overall_success = all(
            r.get("overall_success", False) if isinstance(r, dict) else False
            for r in self.results.values()
        )
        
        if overall_success:
            self.log("🎉 ALL TESTS PASSED - SYSTEM READY FOR PRODUCTION", "SUCCESS")
            sys.exit(0)
        else:
            self.log("⚠️ SOME TESTS FAILED - REVIEW BEFORE DEPLOYMENT", "WARNING")
            sys.exit(1)

def main():
    """Main entry point"""
    runner = MasterTestRunner()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--quick":
            # Quick validation mode
            runner.log("Running quick validation...", "INFO")
            result = runner.run_command("python validate_api.py")
            if result.get("success"):
                runner.log("Quick validation passed ✓", "SUCCESS")
            else:
                runner.log("Quick validation failed ✗", "ERROR")
                sys.exit(1)
        elif sys.argv[1] == "--help":
            print("""
Document-Slides-POC Master Test Runner

Usage:
  python master_test_runner.py          # Run all tests
  python master_test_runner.py --quick  # Quick validation
  python master_test_runner.py --help   # Show this help

The master test runner orchestrates all testing components:
- Agent 1: Testing infrastructure and framework
- Agent 2: Document extractor component tests  
- Agent 3: Template system and slide generation
- Agent 4: API endpoint and integration tests
- Agent 5: End-to-end workflow validation
- Agent 6: Performance and automation testing

Reports are generated in the reports/ directory.
""")
            sys.exit(0)
    
    # Run full test suite
    runner.run_all_tests()

if __name__ == "__main__":
    main()