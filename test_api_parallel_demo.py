#!/usr/bin/env python3
"""
Parallel API Testing System for document-slides-poc
Uses multiple concurrent subagents to test API endpoints with demo files
"""

import asyncio
import concurrent.futures
import time
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import requests
import threading
from dataclasses import dataclass, asdict
from collections import defaultdict

# Import our custom components
try:
    from error_analyzer_demo import DemoFileErrorAnalyzer
    from test_dashboard_demo import create_dashboard, TestDashboard
    ERROR_ANALYZER_AVAILABLE = True
    DASHBOARD_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Some components not available: {e}")
    ERROR_ANALYZER_AVAILABLE = False
    DASHBOARD_AVAILABLE = False

@dataclass
class TestResult:
    """Test result data structure"""
    agent_id: str
    test_name: str
    endpoint: str
    files_used: List[str]
    template_used: Optional[str]
    success: bool
    response_time: float
    status_code: Optional[int]
    error_message: Optional[str]
    error_traceback: Optional[str]
    timestamp: str

class DemoFileManager:
    """Manages demo files for testing"""
    
    def __init__(self, demo_files_path: str = "/mnt/c/Users/cklos/document-slides-poc/demo_files"):
        self.demo_files_path = Path(demo_files_path)
        self.available_files = self._scan_demo_files()
        
    def _scan_demo_files(self) -> Dict[str, str]:
        """Scan and categorize available demo files"""
        files = {}
        if not self.demo_files_path.exists():
            print(f"Warning: Demo files path {self.demo_files_path} does not exist")
            return files
            
        for file_path in self.demo_files_path.glob("*"):
            if file_path.is_file() and not file_path.name.startswith('~'):
                files[file_path.name] = str(file_path)
                
        print(f"Found {len(files)} demo files: {list(files.keys())}")
        return files
    
    def get_file_path(self, filename: str) -> Optional[str]:
        """Get full path for a demo file"""
        return self.available_files.get(filename)
    
    def get_files_by_type(self, file_type: str) -> List[str]:
        """Get demo files by extension"""
        return [name for name in self.available_files.keys() 
                if name.lower().endswith(f'.{file_type.lower()}')]
    
    def create_file_combinations(self) -> List[Dict[str, Any]]:
        """Create test scenarios with different file combinations"""
        scenarios = []
        
        # Single file tests
        for filename in self.available_files.keys():
            if filename.endswith(('.pdf', '.xlsx', '.docx')):
                scenarios.append({
                    'name': f'single_{filename}',
                    'files': [filename],
                    'description': f'Single file test with {filename}'
                })
        
        # Two-file combinations
        pdf_files = self.get_files_by_type('pdf')
        excel_files = self.get_files_by_type('xlsx')
        word_files = self.get_files_by_type('docx')
        
        # Excel + Word combinations
        for excel in excel_files[:2]:  # Limit to first 2 to avoid too many combinations
            for word in word_files[:2]:
                scenarios.append({
                    'name': f'excel_word_{excel}_{word}',
                    'files': [excel, word],
                    'description': f'Excel + Word: {excel} + {word}'
                })
        
        # PDF + Excel combinations
        for pdf in pdf_files[:2]:
            for excel in excel_files[:2]:
                scenarios.append({
                    'name': f'pdf_excel_{pdf}_{excel}',
                    'files': [pdf, excel],
                    'description': f'PDF + Excel: {pdf} + {excel}'
                })
        
        # All supported files (stress test)
        all_supported = [f for f in self.available_files.keys() 
                        if f.endswith(('.pdf', '.xlsx', '.docx'))]
        if len(all_supported) > 2:
            scenarios.append({
                'name': 'all_files_stress_test',
                'files': all_supported,
                'description': f'All {len(all_supported)} supported files together'
            })
        
        return scenarios

class APITestAgent:
    """Individual testing agent for specific scenarios"""
    
    def __init__(self, agent_id: str, base_url: str = "http://localhost:5000"):
        self.agent_id = agent_id
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session = requests.Session()
        self.results = []
        
    def test_health_check(self) -> TestResult:
        """Test the health endpoint"""
        start_time = time.time()
        test_name = "health_check"
        
        try:
            response = self.session.get(f"{base_url}/health", timeout=10)
            response_time = time.time() - start_time
            
            return TestResult(
                agent_id=self.agent_id,
                test_name=test_name,
                endpoint="/health",
                files_used=[],
                template_used=None,
                success=response.status_code == 200,
                response_time=response_time,
                status_code=response.status_code,
                error_message=None if response.status_code == 200 else response.text,
                error_traceback=None,
                timestamp=datetime.now().isoformat()
            )
        except Exception as e:
            response_time = time.time() - start_time
            return TestResult(
                agent_id=self.agent_id,
                test_name=test_name,
                endpoint="/health",
                files_used=[],
                template_used=None,
                success=False,
                response_time=response_time,
                status_code=None,
                error_message=str(e),
                error_traceback=None,
                timestamp=datetime.now().isoformat()
            )
    
    def test_template_list(self) -> TestResult:
        """Test template listing endpoint"""
        start_time = time.time()
        test_name = "template_list"
        
        try:
            response = self.session.get(f"{self.api_url}/templates", timeout=10)
            response_time = time.time() - start_time
            
            success = response.status_code == 200
            error_msg = None
            
            if success:
                try:
                    data = response.json()
                    if not data.get('success', False):
                        success = False
                        error_msg = f"API returned success=False: {data}"
                except json.JSONDecodeError as e:
                    success = False
                    error_msg = f"Invalid JSON response: {e}"
            else:
                error_msg = response.text
            
            return TestResult(
                agent_id=self.agent_id,
                test_name=test_name,
                endpoint="/api/templates",
                files_used=[],
                template_used=None,
                success=success,
                response_time=response_time,
                status_code=response.status_code,
                error_message=error_msg,
                error_traceback=None,
                timestamp=datetime.now().isoformat()
            )
        except Exception as e:
            response_time = time.time() - start_time
            return TestResult(
                agent_id=self.agent_id,
                test_name=test_name,
                endpoint="/api/templates",
                files_used=[],
                template_used=None,
                success=False,
                response_time=response_time,
                status_code=None,
                error_message=str(e),
                error_traceback=None,
                timestamp=datetime.now().isoformat()
            )
    
    def test_slide_generation(self, file_scenario: Dict[str, Any], template: str, 
                            file_manager: DemoFileManager) -> TestResult:
        """Test slide generation with demo files"""
        start_time = time.time()
        test_name = f"slide_generation_{file_scenario['name']}_{template}"
        
        try:
            # Prepare files for upload
            files = []
            file_paths = []
            
            for filename in file_scenario['files']:
                file_path = file_manager.get_file_path(filename)
                if not file_path or not os.path.exists(file_path):
                    raise FileNotFoundError(f"Demo file not found: {filename}")
                
                file_paths.append(file_path)
                files.append(('documents', (filename, open(file_path, 'rb'))))
            
            # Prepare form data
            data = {'template_id': template}
            
            # Make request
            response = self.session.post(
                f"{self.api_url}/generate-slides",
                files=files,
                data=data,
                timeout=60  # Longer timeout for slide generation
            )
            
            # Close file handles
            for _, (_, file_handle) in files:
                file_handle.close()
            
            response_time = time.time() - start_time
            
            success = response.status_code == 200
            error_msg = None
            error_traceback = None
            
            if not success:
                error_msg = response.text
                # Try to extract traceback from Flask error response
                if "Traceback" in response.text:
                    error_traceback = response.text
            
            return TestResult(
                agent_id=self.agent_id,
                test_name=test_name,
                endpoint="/api/generate-slides",
                files_used=file_scenario['files'],
                template_used=template,
                success=success,
                response_time=response_time,
                status_code=response.status_code,
                error_message=error_msg,
                error_traceback=error_traceback,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            return TestResult(
                agent_id=self.agent_id,
                test_name=test_name,
                endpoint="/api/generate-slides",
                files_used=file_scenario.get('files', []),
                template_used=template,
                success=False,
                response_time=response_time,
                status_code=None,
                error_message=str(e),
                error_traceback=None,
                timestamp=datetime.now().isoformat()
            )
    
    def test_preview_extraction(self, file_scenario: Dict[str, Any], 
                              file_manager: DemoFileManager) -> TestResult:
        """Test preview extraction endpoint"""
        start_time = time.time()
        test_name = f"preview_extraction_{file_scenario['name']}"
        
        try:
            # Prepare files for upload
            files = []
            
            for filename in file_scenario['files']:
                file_path = file_manager.get_file_path(filename)
                if not file_path or not os.path.exists(file_path):
                    raise FileNotFoundError(f"Demo file not found: {filename}")
                
                files.append(('documents', (filename, open(file_path, 'rb'))))
            
            # Make request
            response = self.session.post(
                f"{self.api_url}/generate-slides/preview",
                files=files,
                timeout=30
            )
            
            # Close file handles
            for _, (_, file_handle) in files:
                file_handle.close()
            
            response_time = time.time() - start_time
            
            success = response.status_code == 200
            error_msg = None
            
            if success:
                try:
                    data = response.json()
                    if not data.get('success', False):
                        success = False
                        error_msg = f"Preview failed: {data}"
                except json.JSONDecodeError as e:
                    success = False
                    error_msg = f"Invalid JSON response: {e}"
            else:
                error_msg = response.text
            
            return TestResult(
                agent_id=self.agent_id,
                test_name=test_name,
                endpoint="/api/generate-slides/preview",
                files_used=file_scenario['files'],
                template_used=None,
                success=success,
                response_time=response_time,
                status_code=response.status_code,
                error_message=error_msg,
                error_traceback=None,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            return TestResult(
                agent_id=self.agent_id,
                test_name=test_name,
                endpoint="/api/generate-slides/preview",
                files_used=file_scenario.get('files', []),
                template_used=None,
                success=False,
                response_time=response_time,
                status_code=None,
                error_message=str(e),
                error_traceback=None,
                timestamp=datetime.now().isoformat()
            )

class ParallelTestOrchestrator:
    """Orchestrates parallel testing with multiple agents"""
    
    def __init__(self, base_url: str = "http://localhost:5000", max_workers: int = 4, 
                 use_dashboard: bool = True, use_error_analyzer: bool = True):
        self.base_url = base_url
        self.max_workers = max_workers
        self.file_manager = DemoFileManager()
        self.results = []
        self.start_time = None
        
        # Initialize dashboard if available
        self.dashboard = None
        self.dashboard_display = None
        if use_dashboard and DASHBOARD_AVAILABLE:
            self.dashboard, self.dashboard_display = create_dashboard(use_curses=False)
        
        # Initialize error analyzer if available
        self.error_analyzer = None
        if use_error_analyzer and ERROR_ANALYZER_AVAILABLE:
            self.error_analyzer = DemoFileErrorAnalyzer()
        
    def get_available_templates(self) -> List[str]:
        """Get list of available templates from the API"""
        try:
            response = requests.get(f"{self.base_url}/api/templates", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return [t['name'] for t in data.get('templates', [])]
        except Exception as e:
            print(f"Failed to get templates: {e}")
        
        # Fallback to common template names
        return ['simple_template', 'sample_brand', 'sample_brand_template', 'default']
    
    def create_test_plan(self) -> List[Dict[str, Any]]:
        """Create comprehensive test plan"""
        test_plan = []
        
        # Get available templates and file scenarios
        templates = self.get_available_templates()
        file_scenarios = self.file_manager.create_file_combinations()
        
        print(f"Creating test plan with {len(templates)} templates and {len(file_scenarios)} file scenarios")
        
        # Health and template tests (run once)
        test_plan.append({
            'type': 'health_check',
            'agent_assignment': 'agent_0'
        })
        
        test_plan.append({
            'type': 'template_list',
            'agent_assignment': 'agent_0'
        })
        
        # Preview tests (smaller subset)
        for i, scenario in enumerate(file_scenarios[:5]):  # Limit preview tests
            test_plan.append({
                'type': 'preview_extraction',
                'file_scenario': scenario,
                'agent_assignment': f'agent_{i % self.max_workers}'
            })
        
        # Slide generation tests (comprehensive)
        test_counter = 0
        for template in templates[:3]:  # Limit to first 3 templates
            for scenario in file_scenarios:
                test_plan.append({
                    'type': 'slide_generation',
                    'file_scenario': scenario,
                    'template': template,
                    'agent_assignment': f'agent_{test_counter % self.max_workers}'
                })
                test_counter += 1
        
        print(f"Created test plan with {len(test_plan)} total tests")
        return test_plan
    
    def run_agent_tests(self, agent_id: str, assigned_tests: List[Dict[str, Any]]) -> List[TestResult]:
        """Run tests assigned to a specific agent"""
        agent = APITestAgent(agent_id, self.base_url)
        results = []
        
        # Update dashboard with agent status
        if self.dashboard:
            self.dashboard.update_agent_status(agent_id, 'starting')
        
        print(f"{agent_id}: Starting {len(assigned_tests)} tests")
        
        for i, test in enumerate(assigned_tests):
            try:
                # Update dashboard with agent status
                if self.dashboard:
                    self.dashboard.update_agent_status(agent_id, f'running ({i+1}/{len(assigned_tests)})')
                
                print(f"{agent_id}: Running test {i+1}/{len(assigned_tests)}: {test['type']}")
                
                # Generate test ID
                test_id = f"{agent_id}_{test['type']}_{i}"
                
                # Get test details for dashboard
                files_used = test.get('file_scenario', {}).get('files', [])
                template_used = test.get('template', None)
                test_name = f"{test['type']}_{test.get('file_scenario', {}).get('name', 'unknown')}"
                
                # Start test in dashboard
                if self.dashboard:
                    self.dashboard.start_test(test_id, agent_id, test_name, files_used, template_used)
                
                # Execute test
                if test['type'] == 'health_check':
                    result = agent.test_health_check()
                elif test['type'] == 'template_list':
                    result = agent.test_template_list()
                elif test['type'] == 'preview_extraction':
                    result = agent.test_preview_extraction(test['file_scenario'], self.file_manager)
                elif test['type'] == 'slide_generation':
                    result = agent.test_slide_generation(
                        test['file_scenario'], test['template'], self.file_manager
                    )
                
                results.append(result)
                
                # Complete test in dashboard
                if self.dashboard:
                    self.dashboard.complete_test(test_id, result.success, result.error_message)
                
                # Print immediate feedback
                status = "✅ PASS" if result.success else "❌ FAIL"
                print(f"{agent_id}: {status} {result.test_name} ({result.response_time:.2f}s)")
                
                if not result.success:
                    print(f"{agent_id}: Error: {result.error_message}")
                    
                    # Analyze error if analyzer is available
                    if self.error_analyzer:
                        analysis = self.error_analyzer.analyze_error(
                            result.error_message or '',
                            result.error_traceback or '',
                            result.files_used,
                            result.template_used
                        )
                        print(f"{agent_id}: Error Analysis: {analysis.error_type} (Priority {analysis.fix_priority})")
                        print(f"{agent_id}: Suggested Fix: {analysis.suggested_fix}")
                
                # Update dashboard display
                if self.dashboard_display and hasattr(self.dashboard_display, 'update'):
                    self.dashboard_display.update()
                
            except Exception as e:
                print(f"{agent_id}: Exception in test {test['type']}: {e}")
                # Complete test as failed in dashboard
                if self.dashboard:
                    self.dashboard.complete_test(test_id, False, str(e))
                
        # Update agent status to completed
        if self.dashboard:
            self.dashboard.update_agent_status(agent_id, 'completed')
            
        print(f"{agent_id}: Completed {len(results)} tests")
        return results
    
    def run_parallel_tests(self) -> Dict[str, Any]:
        """Run all tests in parallel"""
        self.start_time = time.time()
        print("🚀 Starting parallel API testing...")
        
        # Create test plan
        test_plan = self.create_test_plan()
        
        # Initialize dashboard with test session
        if self.dashboard:
            self.dashboard.start_test_session(len(test_plan))
        
        # Group tests by agent
        agent_tests = defaultdict(list)
        for test in test_plan:
            agent_tests[test['agent_assignment']].append(test)
        
        print(f"🤖 Deploying {len(agent_tests)} agents for {len(test_plan)} tests")
        
        # Run tests in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_agent = {
                executor.submit(self.run_agent_tests, agent_id, tests): agent_id
                for agent_id, tests in agent_tests.items()
            }
            
            all_results = []
            completed_agents = 0
            total_agents = len(future_to_agent)
            
            for future in concurrent.futures.as_completed(future_to_agent):
                agent_id = future_to_agent[future]
                try:
                    agent_results = future.result()
                    all_results.extend(agent_results)
                    completed_agents += 1
                    
                    print(f"🏁 Agent {agent_id} completed ({completed_agents}/{total_agents} agents done)")
                    
                except Exception as e:
                    print(f"💥 Agent {agent_id} generated an exception: {e}")
                    completed_agents += 1
        
        total_time = time.time() - self.start_time
        
        # Final dashboard update
        if self.dashboard_display and hasattr(self.dashboard_display, 'update'):
            self.dashboard_display.update(force=True)
        
        # Analyze results
        return self.analyze_results(all_results, total_time)
    
    def analyze_results(self, results: List[TestResult], total_time: float) -> Dict[str, Any]:
        """Analyze test results and create summary"""
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.success)
        failed_tests = total_tests - passed_tests
        
        # Group errors by type
        errors_by_endpoint = defaultdict(list)
        errors_by_file_type = defaultdict(list)
        
        for result in results:
            if not result.success:
                errors_by_endpoint[result.endpoint].append(result)
                
                # Categorize by file types used
                if result.files_used:
                    file_types = set(f.split('.')[-1] for f in result.files_used)
                    for file_type in file_types:
                        errors_by_file_type[file_type].append(result)
        
        # Performance stats
        response_times = [r.response_time for r in results if r.success]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Enhanced error analysis if analyzer is available
        error_analysis = None
        if self.error_analyzer and failed_tests > 0:
            failed_results = [asdict(r) for r in results if not r.success]
            error_analysis = self.error_analyzer.analyze_batch_errors(failed_results)
        
        summary = {
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'success_rate': f"{(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%",
                'total_time': f"{total_time:.2f}s",
                'avg_response_time': f"{avg_response_time:.2f}s"
            },
            'errors_by_endpoint': {ep: len(errs) for ep, errs in errors_by_endpoint.items()},
            'errors_by_file_type': {ft: len(errs) for ft, errs in errors_by_file_type.items()},
            'failed_tests': [asdict(r) for r in results if not r.success],
            'all_results': [asdict(r) for r in results],
            'enhanced_error_analysis': error_analysis
        }
        
        return summary

def main():
    """Main execution function"""
    print("=" * 60)
    print("🧪 Document-Slides-POC Parallel API Testing")
    print("=" * 60)
    
    # Initialize orchestrator
    orchestrator = ParallelTestOrchestrator()
    
    # Check if demo files exist
    if not orchestrator.file_manager.available_files:
        print("❌ No demo files found. Please ensure demo files exist in /demo_files/")
        return
    
    print(f"📁 Found {len(orchestrator.file_manager.available_files)} demo files")
    
    # Run tests
    results = orchestrator.run_parallel_tests()
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    summary = results['summary']
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed']} ✅")
    print(f"Failed: {summary['failed']} ❌")
    print(f"Success Rate: {summary['success_rate']}")
    print(f"Total Time: {summary['total_time']}")
    print(f"Avg Response Time: {summary['avg_response_time']}")
    
    if results['errors_by_endpoint']:
        print("\n🔍 ERRORS BY ENDPOINT:")
        for endpoint, count in results['errors_by_endpoint'].items():
            print(f"  {endpoint}: {count} errors")
    
    if results['errors_by_file_type']:
        print("\n📄 ERRORS BY FILE TYPE:")
        for file_type, count in results['errors_by_file_type'].items():
            print(f"  .{file_type}: {count} errors")
    
    # Enhanced error analysis
    error_analysis = results.get('enhanced_error_analysis')
    if error_analysis:
        print("\n🔍 ENHANCED ERROR ANALYSIS:")
        print(f"Total error types identified: {len(error_analysis['error_distribution'])}")
        
        # Show error distribution
        if error_analysis['error_distribution']:
            print("\nError Distribution:")
            for error_type, count in error_analysis['error_distribution'].items():
                print(f"  {error_type}: {count} occurrences")
        
        # Show critical errors with fixes
        if error_analysis['critical_errors']:
            print("\n🚨 CRITICAL ERRORS (Priority fixes):")
            for i, critical_error in enumerate(error_analysis['critical_errors'][:3]):
                print(f"\n{i+1}. {critical_error['error_type']} (Priority {critical_error['fix_priority']})")
                print(f"   Description: {critical_error['description']}")
                print(f"   Suggested Fix: {critical_error['suggested_fix']}")
                print(f"   Demo File Context: {critical_error['demo_file_context'][:100]}...")
                if critical_error['code_location']:
                    print(f"   Code Location: {critical_error['code_location']}")
        
        # Show recommendations
        if error_analysis['recommendations']:
            print("\n💡 RECOMMENDATIONS:")
            for rec in error_analysis['recommendations']:
                print(f"  {rec}")
        
        # Show fix order
        if error_analysis['fix_order']:
            print("\n🔧 SUGGESTED FIX ORDER:")
            for i, fix in enumerate(error_analysis['fix_order'][:5]):
                print(f"  {i+1}. {fix}")
    
    # Show first few failures (legacy format)
    failed_tests = results['failed_tests']
    if failed_tests and not error_analysis:
        print("\n❌ FIRST 3 FAILURES:")
        for i, failure in enumerate(failed_tests[:3]):
            print(f"\n{i+1}. {failure['test_name']}")
            print(f"   Endpoint: {failure['endpoint']}")
            print(f"   Files: {failure['files_used']}")
            print(f"   Error: {failure['error_message'][:200]}...")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"/mnt/c/Users/cklos/document-slides-poc/test_results_parallel_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    
    # Final status
    if summary['failed'] == 0:
        print("\n🎉 All tests passed! API is working correctly with demo files.")
    else:
        print(f"\n⚠️  {summary['failed']} tests failed. Check the analysis above for specific fixes.")
        
        # Show most critical fix
        if error_analysis and error_analysis['critical_errors']:
            most_critical = error_analysis['critical_errors'][0]
            print(f"\n🎯 MOST CRITICAL FIX: {most_critical['error_type']}")
            print(f"   Fix: {most_critical['suggested_fix']}")
            if most_critical['code_location']:
                print(f"   Location: {most_critical['code_location']}")

def run_quick_test():
    """Run a quick subset of tests for faster feedback"""
    print("🚀 Running Quick API Test...")
    
    orchestrator = ParallelTestOrchestrator(max_workers=2)
    
    # Override create_test_plan for quick test
    original_method = orchestrator.create_test_plan
    
    def quick_test_plan():
        scenarios = orchestrator.file_manager.create_file_combinations()[:3]  # First 3 scenarios
        templates = orchestrator.get_available_templates()[:2]  # First 2 templates
        
        test_plan = []
        test_plan.append({'type': 'health_check', 'agent_assignment': 'agent_0'})
        test_plan.append({'type': 'template_list', 'agent_assignment': 'agent_0'})
        
        # Quick slide generation tests
        for i, scenario in enumerate(scenarios):
            for j, template in enumerate(templates):
                test_plan.append({
                    'type': 'slide_generation',
                    'file_scenario': scenario,
                    'template': template,
                    'agent_assignment': f'agent_{i % 2}'
                })
        
        return test_plan
    
    orchestrator.create_test_plan = quick_test_plan
    
    # Run quick tests
    results = orchestrator.run_parallel_tests()
    
    # Quick summary
    summary = results['summary']
    print(f"\n📊 Quick Test Results: {summary['passed']}/{summary['total_tests']} passed ({summary['success_rate']})")
    
    if results.get('enhanced_error_analysis', {}).get('critical_errors'):
        critical = results['enhanced_error_analysis']['critical_errors'][0]
        print(f"🚨 Most Critical Issue: {critical['error_type']}")
        print(f"   Fix: {critical['suggested_fix']}")
    
    return summary['failed'] == 0

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "quick":
            # Run quick test
            success = run_quick_test()
            sys.exit(0 if success else 1)
        elif sys.argv[1] == "help":
            print("Usage:")
            print("  python test_api_parallel_demo.py        # Run full test suite")
            print("  python test_api_parallel_demo.py quick  # Run quick test")
            print("  python test_api_parallel_demo.py help   # Show this help")
            sys.exit(0)
    
    # Run full test suite
    main()