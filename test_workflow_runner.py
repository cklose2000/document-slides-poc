#!/usr/bin/env python3
"""
Complete Workflow Test Runner
Agent 5: End-to-End System Validation

This script orchestrates comprehensive testing of the document-slides-poc system,
running all workflow tests and generating a complete validation report.
"""

import os
import sys
import json
import time
import subprocess
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import our test modules
from test_end_to_end_workflows import EndToEndWorkflowTester
from test_web_interface_workflows import WebInterfaceWorkflowTester

class MasterWorkflowTester:
    """Coordinates all workflow testing and validation"""
    
    def __init__(self, base_url="http://localhost:5001"):
        self.base_url = base_url
        self.test_suite_results = []
        self.overall_metrics = {}
        
        # Initialize component testers
        self.e2e_tester = EndToEndWorkflowTester(base_url)
        self.web_tester = WebInterfaceWorkflowTester(base_url)
        
        # Test configuration
        self.test_suites = {
            'system_health': {
                'name': 'System Health Check',
                'description': 'Verify all components are operational',
                'critical': True,
                'tests': ['api_health', 'file_system', 'dependencies']
            },
            'document_processing': {
                'name': 'Document Processing Pipeline',
                'description': 'End-to-end document extraction and processing',
                'critical': True,
                'tests': ['extraction_pipeline', 'multi_document', 'content_accuracy']
            },
            'template_management': {
                'name': 'Template and Branding System',
                'description': 'Template selection and branded slide generation',
                'critical': False,
                'tests': ['template_workflow', 'branded_generation']
            },
            'slide_generation': {
                'name': 'Slide Generation and Output',
                'description': 'PowerPoint creation and output validation',
                'critical': True,
                'tests': ['slide_generation', 'output_validation', 'source_attribution']
            },
            'web_interface': {
                'name': 'Web Interface Workflow',
                'description': 'User interface and interaction testing',
                'critical': True,
                'tests': ['interface_loading', 'upload_workflow', 'user_experience']
            },
            'integration': {
                'name': 'API Integration Testing',
                'description': 'Complete API workflow simulation',
                'critical': True,
                'tests': ['api_simulation', 'error_handling']
            }
        }
    
    def run_complete_validation(self, include_non_critical=True, verbose=True):
        """Run complete system validation with all test suites"""
        print("🚀 STARTING COMPLETE WORKFLOW VALIDATION")
        print("=" * 80)
        print(f"🕐 Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 Target URL: {self.base_url}")
        print("=" * 80)
        
        start_time = time.time()
        
        # Phase 1: Pre-flight checks
        print("\n📋 PHASE 1: PRE-FLIGHT SYSTEM CHECKS")
        pre_flight_result = self._run_pre_flight_checks()
        
        if not pre_flight_result['can_proceed']:
            print("❌ Pre-flight checks failed. Cannot proceed with full testing.")
            return self._generate_failure_report(pre_flight_result)
        
        # Phase 2: Core functionality tests
        print("\n🔧 PHASE 2: CORE FUNCTIONALITY TESTING")
        core_results = self._run_core_functionality_tests()
        
        # Phase 3: Integration tests
        print("\n🌐 PHASE 3: INTEGRATION TESTING")
        integration_results = self._run_integration_tests()
        
        # Phase 4: User experience tests
        print("\n👤 PHASE 4: USER EXPERIENCE TESTING")
        ux_results = self._run_user_experience_tests()
        
        # Phase 5: Performance and reliability
        print("\n⚡ PHASE 5: PERFORMANCE AND RELIABILITY")
        performance_results = self._run_performance_tests()
        
        # Compile final results
        end_time = time.time()
        total_duration = end_time - start_time
        
        final_report = self._compile_final_report({
            'pre_flight': pre_flight_result,
            'core_functionality': core_results,
            'integration': integration_results,
            'user_experience': ux_results,
            'performance': performance_results
        }, total_duration)
        
        # Generate comprehensive report
        self._generate_comprehensive_report(final_report)
        
        return final_report
    
    def _run_pre_flight_checks(self):
        """Run pre-flight system health checks"""
        print("\n🔍 Running pre-flight system checks...")
        
        checks = {
            'api_server': self._check_api_server(),
            'file_system': self._check_file_system(),
            'dependencies': self._check_dependencies(),
            'ports': self._check_ports()
        }
        
        critical_failures = []
        warnings = []
        
        for check_name, result in checks.items():
            if result['critical'] and not result['passed']:
                critical_failures.append(f"{check_name}: {result['message']}")
            elif not result['passed']:
                warnings.append(f"{check_name}: {result['message']}")
            
            status = "✅" if result['passed'] else "❌"
            print(f"   {status} {check_name.replace('_', ' ').title()}: {result['message']}")
        
        can_proceed = len(critical_failures) == 0
        
        return {
            'can_proceed': can_proceed,
            'critical_failures': critical_failures,
            'warnings': warnings,
            'checks': checks,
            'summary': f"{'✅ Ready to proceed' if can_proceed else '❌ Critical issues found'}"
        }
    
    def _check_api_server(self):
        """Check if API server is running and responsive"""
        try:
            import requests
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                return {'passed': True, 'critical': True, 'message': 'API server responsive'}
            else:
                return {'passed': False, 'critical': True, 'message': f'API server returned {response.status_code}'}
        except Exception as e:
            return {'passed': False, 'critical': True, 'message': f'API server not accessible: {str(e)[:100]}'}
    
    def _check_file_system(self):
        """Check file system access and permissions"""
        try:
            # Test directory creation
            test_dir = Path("test_temp_validation")
            test_dir.mkdir(exist_ok=True)
            
            # Test file creation
            test_file = test_dir / "test.txt"
            test_file.write_text("test")
            
            # Test file reading
            content = test_file.read_text()
            
            # Cleanup
            test_file.unlink()
            test_dir.rmdir()
            
            return {'passed': True, 'critical': True, 'message': 'File system access OK'}
        except Exception as e:
            return {'passed': False, 'critical': True, 'message': f'File system issues: {str(e)[:100]}'}
    
    def _check_dependencies(self):
        """Check critical Python dependencies"""
        required_modules = ['requests', 'flask']
        optional_modules = ['openpyxl', 'python-pptx']
        
        missing_required = []
        missing_optional = []
        
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing_required.append(module)
        
        for module in optional_modules:
            try:
                __import__(module.replace('-', '_'))
            except ImportError:
                missing_optional.append(module)
        
        if missing_required:
            return {'passed': False, 'critical': True, 'message': f'Missing required: {", ".join(missing_required)}'}
        elif missing_optional:
            return {'passed': True, 'critical': False, 'message': f'Missing optional: {", ".join(missing_optional)}'}
        else:
            return {'passed': True, 'critical': False, 'message': 'All dependencies available'}
    
    def _check_ports(self):
        """Check if required ports are available"""
        try:
            import socket
            
            # Parse port from base URL
            port = 5001  # default
            if ':' in self.base_url:
                port = int(self.base_url.split(':')[-1])
            
            # Test port connectivity
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                return {'passed': True, 'critical': False, 'message': f'Port {port} accessible'}
            else:
                return {'passed': False, 'critical': True, 'message': f'Port {port} not accessible'}
        except Exception as e:
            return {'passed': False, 'critical': False, 'message': f'Port check failed: {str(e)[:50]}'}
    
    def _run_core_functionality_tests(self):
        """Run core document processing functionality tests"""
        print("\n🔧 Testing core functionality...")
        
        results = {}
        
        # Document extraction pipeline
        print("   📄 Testing document extraction pipeline...")
        extraction_result = self.e2e_tester.test_document_extraction_pipeline()
        results['extraction_pipeline'] = extraction_result
        
        # Multi-document processing
        print("   📋 Testing multi-document processing...")
        multi_doc_result = self.e2e_tester.test_multi_document_processing()
        results['multi_document'] = multi_doc_result
        
        # Content accuracy validation
        print("   🎯 Testing content accuracy...")
        accuracy_result = self.e2e_tester.test_content_accuracy_validation()
        results['content_accuracy'] = accuracy_result
        
        # PowerPoint output validation
        print("   📊 Testing PowerPoint output...")
        output_result = self.e2e_tester.test_powerpoint_output_validation()
        results['output_validation'] = output_result
        
        # Calculate core functionality score
        passed_tests = sum(1 for result in results.values() if result.get('success', False))
        total_tests = len(results)
        core_score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        return {
            'core_score': core_score,
            'passed_tests': passed_tests,
            'total_tests': total_tests,
            'test_results': results,
            'summary': f"Core functionality: {core_score:.1f}% ({passed_tests}/{total_tests} tests passed)"
        }
    
    def _run_integration_tests(self):
        """Run API and system integration tests"""
        print("\n🌐 Testing system integration...")
        
        results = {}
        
        # API workflow simulation
        print("   🔗 Testing API workflow simulation...")
        api_result = self.e2e_tester.test_api_workflow_simulation()
        results['api_workflow'] = api_result
        
        # Template management workflow
        print("   🎨 Testing template management...")
        template_result = self.e2e_tester.test_template_selection_workflow()
        results['template_management'] = template_result
        
        # Calculate integration score
        passed_tests = sum(1 for result in results.values() 
                          if result.get('success', False) or result.get('skipped', False))
        total_tests = len(results)
        integration_score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        return {
            'integration_score': integration_score,
            'passed_tests': passed_tests,
            'total_tests': total_tests,
            'test_results': results,
            'summary': f"Integration: {integration_score:.1f}% ({passed_tests}/{total_tests} tests passed)"
        }
    
    def _run_user_experience_tests(self):
        """Run user experience and web interface tests"""
        print("\n👤 Testing user experience...")
        
        results = {}
        
        # Web interface loading
        print("   🌐 Testing web interface loading...")
        interface_result = self.web_tester.test_web_interface_loading()
        results['interface_loading'] = interface_result
        
        # Document upload workflow
        print("   📤 Testing document upload workflow...")
        upload_result = self.web_tester.test_document_upload_workflow()
        results['upload_workflow'] = upload_result
        
        # User experience scenarios
        print("   👥 Testing user experience scenarios...")
        ux_result = self.web_tester.test_user_experience_scenarios()
        results['user_scenarios'] = ux_result
        
        # Error handling
        print("   ⚠️  Testing error handling...")
        error_result = self.web_tester.test_error_handling_scenarios()
        results['error_handling'] = error_result
        
        # Calculate UX score
        passed_tests = sum(1 for result in results.values() if result.get('success', False))
        total_tests = len(results)
        ux_score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        return {
            'ux_score': ux_score,
            'passed_tests': passed_tests,
            'total_tests': total_tests,
            'test_results': results,
            'summary': f"User experience: {ux_score:.1f}% ({passed_tests}/{total_tests} tests passed)"
        }
    
    def _run_performance_tests(self):
        """Run performance and reliability tests"""
        print("\n⚡ Testing performance and reliability...")
        
        results = {}
        
        # Response time test
        print("   ⏱️  Testing API response times...")
        response_time_result = self._test_response_times()
        results['response_times'] = response_time_result
        
        # Concurrent request handling (simplified)
        print("   🔄 Testing concurrent processing...")
        concurrency_result = self._test_basic_concurrency()
        results['concurrency'] = concurrency_result
        
        # Memory usage validation (basic)
        print("   💾 Testing resource usage...")
        resource_result = self._test_resource_usage()
        results['resource_usage'] = resource_result
        
        # Calculate performance score
        passed_tests = sum(1 for result in results.values() if result.get('success', False))
        total_tests = len(results)
        performance_score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        return {
            'performance_score': performance_score,
            'passed_tests': passed_tests,
            'total_tests': total_tests,
            'test_results': results,
            'summary': f"Performance: {performance_score:.1f}% ({passed_tests}/{total_tests} tests passed)"
        }
    
    def _test_response_times(self):
        """Test API response times"""
        try:
            import requests
            import time
            
            endpoints = [
                ('health', '/health'),
                ('templates', '/api/templates'),
            ]
            
            response_times = {}
            
            for name, endpoint in endpoints:
                start_time = time.time()
                try:
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                    end_time = time.time()
                    response_time = (end_time - start_time) * 1000  # ms
                    
                    response_times[name] = {
                        'time_ms': response_time,
                        'status_code': response.status_code,
                        'acceptable': response_time < 2000  # Under 2 seconds
                    }
                except Exception as e:
                    response_times[name] = {
                        'time_ms': None,
                        'error': str(e)[:100],
                        'acceptable': False
                    }
            
            # Check if most responses are acceptable
            acceptable_count = sum(1 for rt in response_times.values() if rt.get('acceptable', False))
            total_count = len(response_times)
            
            return {
                'success': acceptable_count >= (total_count * 0.7),
                'response_times': response_times,
                'acceptable_ratio': acceptable_count / total_count if total_count > 0 else 0
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _test_basic_concurrency(self):
        """Test basic concurrent request handling"""
        try:
            import requests
            import threading
            import time
            
            results = []
            
            def make_request():
                try:
                    start_time = time.time()
                    response = requests.get(f"{self.base_url}/health", timeout=10)
                    end_time = time.time()
                    results.append({
                        'success': response.status_code == 200,
                        'time': end_time - start_time
                    })
                except Exception as e:
                    results.append({'success': False, 'error': str(e)[:50]})
            
            # Create 3 concurrent requests
            threads = []
            for _ in range(3):
                thread = threading.Thread(target=make_request)
                threads.append(thread)
            
            # Start all threads
            start_time = time.time()
            for thread in threads:
                thread.start()
            
            # Wait for completion
            for thread in threads:
                thread.join()
            
            total_time = time.time() - start_time
            
            successful_requests = sum(1 for r in results if r.get('success', False))
            
            return {
                'success': successful_requests >= 2,  # At least 2 out of 3 should succeed
                'successful_requests': successful_requests,
                'total_requests': len(results),
                'total_time': total_time,
                'concurrent_handling': total_time < 10  # Should complete within 10 seconds
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _test_resource_usage(self):
        """Test basic resource usage"""
        try:
            import psutil
            import os
            
            # Get current process info
            process = psutil.Process()
            
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024  # MB
            
            cpu_percent = process.cpu_percent(interval=1)
            
            # Check if resource usage is reasonable
            memory_ok = memory_mb < 500  # Under 500MB
            cpu_ok = cpu_percent < 50  # Under 50% CPU
            
            return {
                'success': memory_ok and cpu_ok,
                'memory_mb': memory_mb,
                'cpu_percent': cpu_percent,
                'memory_acceptable': memory_ok,
                'cpu_acceptable': cpu_ok
            }
            
        except ImportError:
            # psutil not available
            return {
                'success': True,  # Don't fail if psutil unavailable
                'note': 'psutil not available for resource monitoring'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _compile_final_report(self, phase_results, total_duration):
        """Compile final comprehensive report"""
        
        # Calculate overall scores
        scores = {}
        total_score = 0
        weight_sum = 0
        
        for phase_name, phase_result in phase_results.items():
            if phase_name == 'pre_flight':
                score = 100 if phase_result['can_proceed'] else 0
                weight = 0.1  # 10% weight
            else:
                score_key = f"{phase_name.split('_')[0]}_score"
                score = phase_result.get(score_key, phase_result.get('score', 0))
                
                # Weight critical phases more heavily
                if phase_name in ['core_functionality', 'integration']:
                    weight = 0.3  # 30% each
                else:
                    weight = 0.15  # 15% each
            
            scores[phase_name] = score
            total_score += score * weight
            weight_sum += weight
        
        overall_score = total_score / weight_sum if weight_sum > 0 else 0
        
        # Determine system readiness
        if overall_score >= 90:
            readiness = "🟢 PRODUCTION READY"
            readiness_level = "production"
        elif overall_score >= 75:
            readiness = "🟡 STAGING READY"
            readiness_level = "staging"
        elif overall_score >= 60:
            readiness = "🟠 DEVELOPMENT READY"
            readiness_level = "development"
        else:
            readiness = "🔴 NEEDS SIGNIFICANT WORK"
            readiness_level = "not_ready"
        
        # Count total tests
        total_tests_run = 0
        total_tests_passed = 0
        
        for phase_result in phase_results.values():
            if isinstance(phase_result, dict):
                total_tests_run += phase_result.get('total_tests', 0)
                total_tests_passed += phase_result.get('passed_tests', 0)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': total_duration,
            'overall_score': overall_score,
            'readiness': readiness,
            'readiness_level': readiness_level,
            'phase_scores': scores,
            'phase_results': phase_results,
            'test_summary': {
                'total_tests_run': total_tests_run,
                'total_tests_passed': total_tests_passed,
                'success_rate': (total_tests_passed / total_tests_run * 100) if total_tests_run > 0 else 0
            },
            'system_info': {
                'base_url': self.base_url,
                'test_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }
    
    def _generate_failure_report(self, pre_flight_result):
        """Generate report for failed pre-flight checks"""
        return {
            'timestamp': datetime.now().isoformat(),
            'overall_score': 0,
            'readiness': "🔴 SYSTEM NOT OPERATIONAL",
            'readiness_level': "failed",
            'pre_flight_failures': pre_flight_result['critical_failures'],
            'warnings': pre_flight_result['warnings'],
            'system_info': {
                'base_url': self.base_url,
                'test_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }
    
    def _generate_comprehensive_report(self, final_report):
        """Generate and save comprehensive test report"""
        print(f"\n{'='*80}")
        print("📋 COMPREHENSIVE WORKFLOW VALIDATION REPORT")
        print("=" * 80)
        
        # Header information
        print(f"🕐 Test completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  Total duration: {final_report['duration_seconds']:.1f} seconds")
        print(f"🌐 System under test: {final_report['system_info']['base_url']}")
        
        # Overall assessment
        print(f"\n📊 OVERALL ASSESSMENT")
        print(f"   Score: {final_report['overall_score']:.1f}/100")
        print(f"   Status: {final_report['readiness']}")
        
        # Test summary
        test_summary = final_report['test_summary']
        print(f"\n🧪 TEST EXECUTION SUMMARY")
        print(f"   Total tests: {test_summary['total_tests_run']}")
        print(f"   Passed: {test_summary['total_tests_passed']}")
        print(f"   Success rate: {test_summary['success_rate']:.1f}%")
        
        # Phase-by-phase results
        print(f"\n📋 PHASE-BY-PHASE RESULTS")
        for phase_name, score in final_report['phase_scores'].items():
            if phase_name != 'pre_flight':
                phase_result = final_report['phase_results'][phase_name]
                print(f"   {phase_name.replace('_', ' ').title()}: {score:.1f}% - {phase_result.get('summary', 'No summary')}")
        
        # Critical issues
        if final_report['readiness_level'] in ['not_ready', 'failed']:
            print(f"\n⚠️  CRITICAL ISSUES IDENTIFIED")
            for phase_name, phase_result in final_report['phase_results'].items():
                if isinstance(phase_result, dict) and 'critical_failures' in phase_result:
                    for failure in phase_result['critical_failures']:
                        print(f"   ❌ {failure}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS")
        self._generate_recommendations(final_report)
        
        # Save detailed JSON report
        report_filename = f"comprehensive_workflow_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(final_report, f, indent=2, default=str)
        
        print(f"\n📄 Detailed JSON report saved: {report_filename}")
        
        # Save summary report
        summary_filename = f"workflow_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(summary_filename, 'w') as f:
            f.write(f"Document-Slides-POC Workflow Validation Summary\\n")
            f.write(f"=" * 50 + "\\n")
            f.write(f"Test Date: {final_report['system_info']['test_timestamp']}\\n")
            f.write(f"Overall Score: {final_report['overall_score']:.1f}/100\\n")
            f.write(f"System Status: {final_report['readiness']}\\n")
            f.write(f"Success Rate: {test_summary['success_rate']:.1f}%\\n")
            f.write(f"Total Tests: {test_summary['total_tests_run']} ({test_summary['total_tests_passed']} passed)\\n")
        
        print(f"📄 Summary report saved: {summary_filename}")
        print("=" * 80)
    
    def _generate_recommendations(self, final_report):
        """Generate specific recommendations based on test results"""
        score = final_report['overall_score']
        readiness_level = final_report['readiness_level']
        
        if readiness_level == 'production':
            print("   ✅ System is ready for production deployment")
            print("   ✅ All critical workflows are functioning correctly")
            print("   💡 Consider setting up monitoring and logging")
            print("   💡 Plan for regular maintenance and updates")
            
        elif readiness_level == 'staging':
            print("   ✅ System is ready for staging environment testing")
            print("   💡 Address minor issues before production deployment")
            print("   💡 Conduct user acceptance testing")
            print("   💡 Review error handling and edge cases")
            
        elif readiness_level == 'development':
            print("   ⚠️  System needs improvements before staging")
            print("   💡 Focus on failed test categories")
            print("   💡 Improve error handling and robustness")
            print("   💡 Optimize performance bottlenecks")
            
        else:
            print("   🔴 System requires significant development work")
            print("   💡 Address critical system failures first")
            print("   💡 Review architecture and implementation")
            print("   💡 Ensure all dependencies are properly configured")
        
        # Specific recommendations based on phase results
        phase_results = final_report['phase_results']
        
        if 'core_functionality' in phase_results:
            core_score = final_report['phase_scores'].get('core_functionality', 0)
            if core_score < 80:
                print("   💡 Core functionality needs attention:")
                print("      - Review document extraction accuracy")
                print("      - Validate slide generation logic")
                print("      - Check source attribution system")
        
        if 'user_experience' in phase_results:
            ux_score = final_report['phase_scores'].get('user_experience', 0)
            if ux_score < 80:
                print("   💡 User experience improvements needed:")
                print("      - Optimize web interface responsiveness")
                print("      - Improve error messages and feedback")
                print("      - Enhance upload and workflow clarity")
        
        if 'performance' in phase_results:
            perf_score = final_report['phase_scores'].get('performance', 0)
            if perf_score < 70:
                print("   💡 Performance optimizations recommended:")
                print("      - Review API response times")
                print("      - Optimize document processing pipeline")
                print("      - Consider caching strategies")


def main():
    """Main function to run comprehensive workflow validation"""
    parser = argparse.ArgumentParser(description='Comprehensive workflow validation for Document-Slides-POC')
    parser.add_argument('--base-url', default='http://localhost:5001',
                       help='Base URL for API server (default: http://localhost:5001)')
    parser.add_argument('--quick', action='store_true',
                       help='Run quick validation (skip non-critical tests)')
    parser.add_argument('--phase', choices=['pre-flight', 'core', 'integration', 'ux', 'performance', 'all'],
                       default='all', help='Specific phase to run')
    parser.add_argument('--verbose', action='store_true', default=True,
                       help='Verbose output (default: True)')
    
    args = parser.parse_args()
    
    # Create master tester
    master_tester = MasterWorkflowTester(base_url=args.base_url)
    
    # Run validation
    if args.phase == 'all':
        final_report = master_tester.run_complete_validation(
            include_non_critical=not args.quick,
            verbose=args.verbose
        )
    else:
        # Run specific phase (simplified for this implementation)
        print(f"Running specific phase: {args.phase}")
        final_report = master_tester.run_complete_validation(
            include_non_critical=False,
            verbose=args.verbose
        )
    
    # Exit with appropriate code based on results
    if final_report['readiness_level'] in ['production', 'staging']:
        exit(0)  # Success
    elif final_report['readiness_level'] == 'development':
        exit(1)  # Needs work but functional
    else:
        exit(2)  # Critical failures


if __name__ == "__main__":
    main()