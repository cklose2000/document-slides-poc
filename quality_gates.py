#!/usr/bin/env python3
"""
Quality gates and success criteria validation system
Defines and validates quality thresholds for system reliability and performance
"""
import os
import sys
import json
import time
import statistics
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import re

class GateSeverity(Enum):
    """Quality gate severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium" 
    LOW = "low"
    INFO = "info"

class GateStatus(Enum):
    """Quality gate evaluation status"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"
    ERROR = "error"

@dataclass
class QualityMetric:
    """Individual quality metric data"""
    name: str
    value: Union[float, int, str, bool]
    unit: str
    source: str
    timestamp: float
    metadata: Dict[str, Any] = None

@dataclass
class QualityGate:
    """Quality gate definition and evaluation"""
    name: str
    description: str
    metric_name: str
    operator: str  # ">=", "<=", ">", "<", "==", "!=", "contains", "not_contains"
    threshold: Union[float, int, str]
    severity: GateSeverity
    enabled: bool = True
    tolerance: float = 0.0
    evaluation_result: Optional['GateEvaluation'] = None

@dataclass
class GateEvaluation:
    """Quality gate evaluation result"""
    gate_name: str
    status: GateStatus
    actual_value: Union[float, int, str, bool]
    threshold_value: Union[float, int, str]
    deviation: Optional[float]
    message: str
    recommendations: List[str]
    timestamp: float
    execution_time: float = 0.0

class QualityGateValidator:
    """Main quality gate validation system"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config = self.load_config(config_file)
        self.gates = self.load_quality_gates()
        self.metrics = {}
        self.evaluations = []
        
    def load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """Load quality gate configuration"""
        default_config = {
            "performance_gates": {
                "max_document_processing_time": {
                    "threshold": 30.0,
                    "unit": "seconds",
                    "severity": "high",
                    "tolerance": 5.0
                },
                "max_slide_generation_time": {
                    "threshold": 60.0,
                    "unit": "seconds", 
                    "severity": "high",
                    "tolerance": 10.0
                },
                "min_throughput_mb_per_sec": {
                    "threshold": 1.0,
                    "unit": "MB/s",
                    "severity": "medium",
                    "tolerance": 0.2
                },
                "max_memory_usage_mb": {
                    "threshold": 1000.0,
                    "unit": "MB",
                    "severity": "high",
                    "tolerance": 100.0
                },
                "max_cpu_usage_percent": {
                    "threshold": 80.0,
                    "unit": "%",
                    "severity": "medium",
                    "tolerance": 10.0
                }
            },
            "reliability_gates": {
                "min_test_pass_rate": {
                    "threshold": 95.0,
                    "unit": "%",
                    "severity": "critical",
                    "tolerance": 0.0
                },
                "max_error_rate": {
                    "threshold": 1.0,
                    "unit": "%",
                    "severity": "high",
                    "tolerance": 0.5
                },
                "min_availability": {
                    "threshold": 99.0,
                    "unit": "%",
                    "severity": "critical",
                    "tolerance": 0.0
                },
                "max_failure_count": {
                    "threshold": 5,
                    "unit": "count",
                    "severity": "high",
                    "tolerance": 0
                }
            },
            "quality_gates": {
                "min_code_coverage": {
                    "threshold": 70.0,
                    "unit": "%",
                    "severity": "high",
                    "tolerance": 5.0
                },
                "min_branch_coverage": {
                    "threshold": 60.0,
                    "unit": "%",
                    "severity": "medium",
                    "tolerance": 5.0
                },
                "max_code_complexity": {
                    "threshold": 10,
                    "unit": "cyclomatic",
                    "severity": "medium",
                    "tolerance": 2
                },
                "max_duplicate_code_percent": {
                    "threshold": 5.0,
                    "unit": "%",
                    "severity": "low",
                    "tolerance": 1.0
                }
            },
            "security_gates": {
                "max_high_severity_vulnerabilities": {
                    "threshold": 0,
                    "unit": "count",
                    "severity": "critical",
                    "tolerance": 0
                },
                "max_medium_severity_vulnerabilities": {
                    "threshold": 5,
                    "unit": "count",
                    "severity": "high",
                    "tolerance": 1
                }
            },
            "compliance_gates": {
                "required_documentation_coverage": {
                    "threshold": 80.0,
                    "unit": "%",
                    "severity": "medium",
                    "tolerance": 10.0
                },
                "required_api_documentation": {
                    "threshold": True,
                    "unit": "boolean",
                    "severity": "high",
                    "tolerance": 0
                }
            }
        }
        
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                # Deep merge configuration
                self.deep_merge(default_config, user_config)
            except Exception as e:
                print(f"Warning: Could not load config file {config_file}: {e}")
                
        return default_config
        
    def deep_merge(self, base_dict: Dict, update_dict: Dict):
        """Deep merge two dictionaries"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self.deep_merge(base_dict[key], value)
            else:
                base_dict[key] = value
                
    def load_quality_gates(self) -> List[QualityGate]:
        """Load and create quality gate objects from configuration"""
        gates = []
        
        for category, category_gates in self.config.items():
            for gate_name, gate_config in category_gates.items():
                gate = QualityGate(
                    name=gate_name,
                    description=gate_config.get('description', f"Quality gate for {gate_name}"),
                    metric_name=gate_name,
                    operator=gate_config.get('operator', self.infer_operator(gate_name)),
                    threshold=gate_config['threshold'],
                    severity=GateSeverity(gate_config.get('severity', 'medium')),
                    enabled=gate_config.get('enabled', True),
                    tolerance=gate_config.get('tolerance', 0.0)
                )
                gates.append(gate)
                
        return gates
        
    def infer_operator(self, gate_name: str) -> str:
        """Infer comparison operator from gate name"""
        if gate_name.startswith('min_'):
            return ">="
        elif gate_name.startswith('max_'):
            return "<="
        elif 'required' in gate_name:
            return "=="
        else:
            return ">="
            
    def add_metric(self, name: str, value: Union[float, int, str, bool], 
                   unit: str = "", source: str = "manual", metadata: Dict[str, Any] = None):
        """Add a quality metric for evaluation"""
        metric = QualityMetric(
            name=name,
            value=value,
            unit=unit,
            source=source,
            timestamp=time.time(),
            metadata=metadata or {}
        )
        self.metrics[name] = metric
        
    def add_metrics_from_test_results(self, test_results_file: str):
        """Extract metrics from test results file"""
        try:
            with open(test_results_file, 'r') as f:
                data = json.load(f)
                
            # Extract test pass rate
            if 'summary' in data:
                summary = data['summary']
                if 'pass_rate' in summary:
                    self.add_metric('min_test_pass_rate', summary['pass_rate'], '%', 'test_runner')
                if 'coverage_percentage' in summary:
                    self.add_metric('min_code_coverage', summary['coverage_percentage'], '%', 'coverage')
                if 'total_execution_time' in summary:
                    self.add_metric('max_test_execution_time', summary['total_execution_time'], 'seconds', 'test_runner')
                    
            # Extract performance metrics from individual tests
            if 'test_results' in data:
                execution_times = []
                for result in data['test_results']:
                    if 'execution_time' in result:
                        execution_times.append(result['execution_time'])
                        
                if execution_times:
                    avg_time = statistics.mean(execution_times)
                    max_time = max(execution_times)
                    self.add_metric('avg_test_execution_time', avg_time, 'seconds', 'test_runner')
                    self.add_metric('max_individual_test_time', max_time, 'seconds', 'test_runner')
                    
        except Exception as e:
            print(f"Warning: Could not extract metrics from {test_results_file}: {e}")
            
    def add_metrics_from_performance_report(self, performance_file: str):
        """Extract metrics from performance report"""
        try:
            with open(performance_file, 'r') as f:
                data = json.load(f)
                
            if 'summary' in data:
                summary = data['summary']
                
                # Extract performance metrics
                metrics_mapping = {
                    'avg_execution_time': 'avg_document_processing_time',
                    'max_execution_time': 'max_document_processing_time', 
                    'avg_memory_usage_mb': 'avg_memory_usage_mb',
                    'max_memory_usage_mb': 'max_memory_usage_mb',
                    'avg_throughput_mb_per_sec': 'min_throughput_mb_per_sec',
                    'max_throughput_mb_per_sec': 'max_throughput_mb_per_sec'
                }
                
                for source_key, target_key in metrics_mapping.items():
                    if source_key in summary:
                        unit = 'seconds' if 'time' in source_key else 'MB' if 'memory' in source_key else 'MB/s'
                        self.add_metric(target_key, summary[source_key], unit, 'performance_test')
                        
        except Exception as e:
            print(f"Warning: Could not extract metrics from {performance_file}: {e}")
            
    def add_metrics_from_memory_report(self, memory_file: str):
        """Extract metrics from memory stress test report"""
        try:
            with open(memory_file, 'r') as f:
                data = json.load(f)
                
            if 'summary' in data:
                summary = data['summary']
                
                if 'max_peak_memory_mb' in summary:
                    self.add_metric('max_memory_usage_mb', summary['max_peak_memory_mb'], 'MB', 'memory_test')
                if 'avg_peak_memory_mb' in summary:
                    self.add_metric('avg_memory_usage_mb', summary['avg_peak_memory_mb'], 'MB', 'memory_test')
                if 'max_execution_time_sec' in summary:
                    self.add_metric('max_large_file_processing_time', summary['max_execution_time_sec'], 'seconds', 'memory_test')
                    
        except Exception as e:
            print(f"Warning: Could not extract metrics from {memory_file}: {e}")
            
    def evaluate_gate(self, gate: QualityGate) -> GateEvaluation:
        """Evaluate a single quality gate"""
        start_time = time.time()
        
        # Check if metric exists
        if gate.metric_name not in self.metrics:
            return GateEvaluation(
                gate_name=gate.name,
                status=GateStatus.SKIPPED,
                actual_value="N/A",
                threshold_value=gate.threshold,
                deviation=None,
                message=f"Metric '{gate.metric_name}' not available",
                recommendations=["Ensure the metric is collected during test execution"],
                timestamp=time.time(),
                execution_time=time.time() - start_time
            )
            
        metric = self.metrics[gate.metric_name]
        actual_value = metric.value
        threshold = gate.threshold
        
        # Evaluate based on operator
        try:
            passed = self.compare_values(actual_value, threshold, gate.operator, gate.tolerance)
            deviation = self.calculate_deviation(actual_value, threshold, gate.operator)
            
            status = GateStatus.PASSED if passed else GateStatus.FAILED
            
            # Generate message and recommendations
            message, recommendations = self.generate_evaluation_message(
                gate, actual_value, threshold, passed, deviation
            )
            
            return GateEvaluation(
                gate_name=gate.name,
                status=status,
                actual_value=actual_value,
                threshold_value=threshold,
                deviation=deviation,
                message=message,
                recommendations=recommendations,
                timestamp=time.time(),
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return GateEvaluation(
                gate_name=gate.name,
                status=GateStatus.ERROR,
                actual_value=actual_value,
                threshold_value=threshold,
                deviation=None,
                message=f"Error evaluating gate: {str(e)}",
                recommendations=["Check gate configuration and metric data types"],
                timestamp=time.time(),
                execution_time=time.time() - start_time
            )
            
    def compare_values(self, actual: Union[float, int, str, bool], 
                      threshold: Union[float, int, str, bool], 
                      operator: str, tolerance: float = 0.0) -> bool:
        """Compare actual value with threshold using specified operator"""
        try:
            if operator == ">=":
                return float(actual) >= (float(threshold) - tolerance)
            elif operator == "<=":
                return float(actual) <= (float(threshold) + tolerance)
            elif operator == ">":
                return float(actual) > (float(threshold) - tolerance)
            elif operator == "<":
                return float(actual) < (float(threshold) + tolerance)
            elif operator == "==":
                if isinstance(actual, (int, float)) and isinstance(threshold, (int, float)):
                    return abs(float(actual) - float(threshold)) <= tolerance
                else:
                    return str(actual) == str(threshold)
            elif operator == "!=":
                if isinstance(actual, (int, float)) and isinstance(threshold, (int, float)):
                    return abs(float(actual) - float(threshold)) > tolerance
                else:
                    return str(actual) != str(threshold)
            elif operator == "contains":
                return str(threshold) in str(actual)
            elif operator == "not_contains":
                return str(threshold) not in str(actual)
            else:
                raise ValueError(f"Unknown operator: {operator}")
        except (ValueError, TypeError) as e:
            raise ValueError(f"Cannot compare {actual} {operator} {threshold}: {e}")
            
    def calculate_deviation(self, actual: Union[float, int, str, bool], 
                           threshold: Union[float, int, str, bool], 
                           operator: str) -> Optional[float]:
        """Calculate deviation from threshold"""
        try:
            if isinstance(actual, (int, float)) and isinstance(threshold, (int, float)):
                if operator in [">=", ">"]:
                    # For minimum thresholds, negative deviation is bad
                    return float(actual) - float(threshold)
                elif operator in ["<=", "<"]:
                    # For maximum thresholds, positive deviation is bad
                    return float(threshold) - float(actual)
                else:
                    return float(actual) - float(threshold)
            else:
                return None
        except (ValueError, TypeError):
            return None
            
    def generate_evaluation_message(self, gate: QualityGate, actual_value: Any, 
                                   threshold: Any, passed: bool, 
                                   deviation: Optional[float]) -> Tuple[str, List[str]]:
        """Generate evaluation message and recommendations"""
        unit = self.get_metric_unit(gate.metric_name)
        
        if passed:
            message = f"✅ {gate.name}: {actual_value}{unit} {gate.operator} {threshold}{unit}"
            recommendations = []
        else:
            message = f"❌ {gate.name}: {actual_value}{unit} {gate.operator} {threshold}{unit}"
            recommendations = self.generate_recommendations(gate, actual_value, threshold, deviation)
            
        if deviation is not None:
            if gate.operator in [">=", ">"]:
                if deviation < 0:
                    message += f" (deficit: {abs(deviation):.2f}{unit})"
                else:
                    message += f" (surplus: {deviation:.2f}{unit})"
            elif gate.operator in ["<=", "<"]:
                if deviation < 0:
                    message += f" (excess: {abs(deviation):.2f}{unit})"
                else:
                    message += f" (within limit by: {deviation:.2f}{unit})"
                    
        return message, recommendations
        
    def get_metric_unit(self, metric_name: str) -> str:
        """Get unit for metric"""
        if metric_name in self.metrics:
            return self.metrics[metric_name].unit
        else:
            # Infer unit from metric name
            if 'time' in metric_name:
                return 's'
            elif 'memory' in metric_name or '_mb' in metric_name:
                return 'MB'
            elif 'throughput' in metric_name:
                return 'MB/s'
            elif 'rate' in metric_name or 'percent' in metric_name or 'coverage' in metric_name:
                return '%'
            else:
                return ''
                
    def generate_recommendations(self, gate: QualityGate, actual_value: Any, 
                                threshold: Any, deviation: Optional[float]) -> List[str]:
        """Generate specific recommendations for failed gates"""
        recommendations = []
        
        if 'test_pass_rate' in gate.name:
            recommendations.extend([
                "Review failed test cases and fix underlying issues",
                "Check for flaky tests that may be causing intermittent failures",
                "Ensure test environment is stable and properly configured"
            ])
        elif 'code_coverage' in gate.name:
            recommendations.extend([
                "Add unit tests for uncovered code paths",
                "Review complex functions that may need additional test cases",
                "Consider removing dead or unreachable code"
            ])
        elif 'memory_usage' in gate.name:
            recommendations.extend([
                "Profile memory usage to identify memory leaks",
                "Optimize data structures and algorithms",
                "Implement proper resource cleanup and garbage collection"
            ])
        elif 'execution_time' in gate.name or 'processing_time' in gate.name:
            recommendations.extend([
                "Profile code performance to identify bottlenecks",
                "Optimize algorithms and data access patterns",
                "Consider implementing caching or memoization",
                "Review database queries and API calls for efficiency"
            ])
        elif 'throughput' in gate.name:
            recommendations.extend([
                "Optimize I/O operations and file handling",
                "Consider parallel or asynchronous processing",
                "Review network operations for efficiency",
                "Implement streaming for large data sets"
            ])
        elif 'error_rate' in gate.name:
            recommendations.extend([
                "Implement better error handling and validation",
                "Review input validation and edge case handling",
                "Add retry mechanisms for transient failures",
                "Improve logging and error reporting"
            ])
        else:
            recommendations.append(f"Review and optimize {gate.name} to meet the threshold of {threshold}")
            
        return recommendations
        
    def evaluate_all_gates(self) -> List[GateEvaluation]:
        """Evaluate all quality gates"""
        print("Evaluating quality gates...")
        
        evaluations = []
        
        for gate in self.gates:
            if not gate.enabled:
                print(f"  Skipping disabled gate: {gate.name}")
                continue
                
            print(f"  Evaluating: {gate.name}")
            evaluation = self.evaluate_gate(gate)
            evaluations.append(evaluation)
            
            # Update gate with evaluation result
            gate.evaluation_result = evaluation
            
            # Print result
            status_symbol = "✅" if evaluation.status == GateStatus.PASSED else "❌" if evaluation.status == GateStatus.FAILED else "⚠️"
            print(f"    {status_symbol} {evaluation.message}")
            
        self.evaluations = evaluations
        return evaluations
        
    def generate_quality_report(self, output_file: str = None) -> Dict[str, Any]:
        """Generate comprehensive quality gate report"""
        if not output_file:
            output_file = f"quality_gate_report_{int(time.time())}.json"
            
        # Calculate summary statistics
        total_gates = len(self.evaluations)
        passed_gates = sum(1 for e in self.evaluations if e.status == GateStatus.PASSED)
        failed_gates = sum(1 for e in self.evaluations if e.status == GateStatus.FAILED)
        skipped_gates = sum(1 for e in self.evaluations if e.status == GateStatus.SKIPPED)
        error_gates = sum(1 for e in self.evaluations if e.status == GateStatus.ERROR)
        
        critical_failed = sum(1 for e in self.evaluations 
                             if e.status == GateStatus.FAILED and 
                             self.get_gate_severity(e.gate_name) == GateSeverity.CRITICAL)
        
        overall_success = failed_gates == 0 and error_gates == 0
        
        report_data = {
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "overall_success": overall_success,
            "summary": {
                "total_gates": total_gates,
                "passed": passed_gates,
                "failed": failed_gates,
                "skipped": skipped_gates,
                "errors": error_gates,
                "critical_failures": critical_failed,
                "success_rate": (passed_gates / total_gates * 100) if total_gates > 0 else 0
            },
            "gates": [asdict(evaluation) for evaluation in self.evaluations],
            "metrics": {name: asdict(metric) for name, metric in self.metrics.items()},
            "recommendations": self.compile_recommendations()
        }
        
        # Save JSON report
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2)
            
        # Generate text report
        text_file = output_file.replace('.json', '.txt')
        self.generate_text_report(text_file, report_data)
        
        print(f"Quality gate reports generated:")
        print(f"  JSON: {os.path.abspath(output_file)}")
        print(f"  Text: {os.path.abspath(text_file)}")
        
        return report_data
        
    def get_gate_severity(self, gate_name: str) -> GateSeverity:
        """Get severity for a gate by name"""
        for gate in self.gates:
            if gate.name == gate_name:
                return gate.severity
        return GateSeverity.MEDIUM
        
    def compile_recommendations(self) -> Dict[str, List[str]]:
        """Compile all recommendations by category"""
        recommendations = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": []
        }
        
        for evaluation in self.evaluations:
            if evaluation.status == GateStatus.FAILED and evaluation.recommendations:
                severity = self.get_gate_severity(evaluation.gate_name)
                category = severity.value
                
                for rec in evaluation.recommendations:
                    if rec not in recommendations[category]:
                        recommendations[category].append(rec)
                        
        return recommendations
        
    def generate_text_report(self, file_path: str, report_data: Dict[str, Any]):
        """Generate human-readable text report"""
        with open(file_path, 'w') as f:
            f.write("QUALITY GATE EVALUATION REPORT\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Timestamp: {report_data['timestamp']}\n")
            f.write(f"Overall Status: {'✅ SUCCESS' if report_data['overall_success'] else '❌ FAILURE'}\n\n")
            
            # Summary
            summary = report_data['summary']
            f.write("SUMMARY\n")
            f.write("-" * 20 + "\n")
            f.write(f"Total Gates: {summary['total_gates']}\n")
            f.write(f"Passed: {summary['passed']}\n")
            f.write(f"Failed: {summary['failed']}\n")
            f.write(f"Skipped: {summary['skipped']}\n")
            f.write(f"Errors: {summary['errors']}\n")
            f.write(f"Critical Failures: {summary['critical_failures']}\n")
            f.write(f"Success Rate: {summary['success_rate']:.1f}%\n\n")
            
            # Gate details
            f.write("GATE EVALUATION DETAILS\n")
            f.write("-" * 30 + "\n")
            
            for gate in report_data['gates']:
                status_symbol = {
                    'passed': '✅',
                    'failed': '❌', 
                    'warning': '⚠️',
                    'skipped': '⏭️',
                    'error': '💥'
                }.get(gate['status'], '❓')
                
                f.write(f"\n{status_symbol} {gate['gate_name']}\n")
                f.write(f"  {gate['message']}\n")
                
                if gate['recommendations']:
                    f.write("  Recommendations:\n")
                    for rec in gate['recommendations']:
                        f.write(f"    • {rec}\n")
                        
            # Recommendations summary
            if report_data['recommendations']:
                f.write("\nRECOMMENDATIONS BY PRIORITY\n")
                f.write("-" * 30 + "\n")
                
                for priority in ['critical', 'high', 'medium', 'low']:
                    recs = report_data['recommendations'].get(priority, [])
                    if recs:
                        f.write(f"\n{priority.upper()} Priority:\n")
                        for rec in recs:
                            f.write(f"  • {rec}\n")

def main():
    """Main entry point for quality gate validation"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Quality gate validation system")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--test-results", help="Test results JSON file")
    parser.add_argument("--performance-results", help="Performance results JSON file")
    parser.add_argument("--memory-results", help="Memory test results JSON file")
    parser.add_argument("--output", help="Output report file path")
    parser.add_argument("--metric", nargs=3, metavar=('NAME', 'VALUE', 'UNIT'), 
                       action='append', help="Add manual metric (name value unit)")
    
    args = parser.parse_args()
    
    # Initialize validator
    validator = QualityGateValidator(args.config)
    
    # Add metrics from files
    if args.test_results:
        validator.add_metrics_from_test_results(args.test_results)
    if args.performance_results:
        validator.add_metrics_from_performance_report(args.performance_results)
    if args.memory_results:
        validator.add_metrics_from_memory_report(args.memory_results)
        
    # Add manual metrics
    if args.metric:
        for name, value, unit in args.metric:
            try:
                # Try to convert to numeric
                if '.' in value:
                    value = float(value)
                else:
                    value = int(value)
            except ValueError:
                # Keep as string
                pass
            validator.add_metric(name, value, unit, 'manual')
            
    # Evaluate gates
    evaluations = validator.evaluate_all_gates()
    
    # Generate report
    report = validator.generate_quality_report(args.output)
    
    # Print summary
    print(f"\nQuality Gate Evaluation Complete")
    print(f"Overall Status: {'✅ SUCCESS' if report['overall_success'] else '❌ FAILURE'}")
    print(f"Gates: {report['summary']['passed']}/{report['summary']['total_gates']} passed")
    
    if report['summary']['critical_failures'] > 0:
        print(f"❌ {report['summary']['critical_failures']} critical gates failed")
        sys.exit(1)
    elif report['summary']['failed'] > 0:
        print(f"⚠️ {report['summary']['failed']} non-critical gates failed")
        sys.exit(1)
    else:
        print("✅ All quality gates passed")
        sys.exit(0)

if __name__ == "__main__":
    main()