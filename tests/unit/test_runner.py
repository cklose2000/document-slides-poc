"""
Comprehensive test runner for all document extraction components
Runs all unit tests and generates a detailed test report
"""

import unittest
import sys
import os
import time
from io import StringIO

# Add the lib directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lib'))

# Import all test modules
from test_pdf_extractor import TestPDFExtractor, TestPDFExtractorIntegration
from test_excel_extractor import TestExcelExtractor, TestExcelExtractorIntegration
from test_word_extractor import TestWordExtractor, TestWordExtractorIntegration
from test_edge_cases import TestEdgeCases
from test_source_attribution import TestSourceAttribution


class ColoredTestResult(unittest.TextTestResult):
    """Custom test result class with colored output"""
    
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.test_results = []
        
    def addSuccess(self, test):
        super().addSuccess(test)
        self.test_results.append(('PASS', test._testMethodName, test.__class__.__name__, None))
        if self.verbosity > 1:
            self.stream.write(f"✅ {test._testMethodName} ... PASS\n")
            
    def addError(self, test, err):
        super().addError(test, err)
        self.test_results.append(('ERROR', test._testMethodName, test.__class__.__name__, err))
        if self.verbosity > 1:
            self.stream.write(f"💥 {test._testMethodName} ... ERROR\n")
            
    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.test_results.append(('FAIL', test._testMethodName, test.__class__.__name__, err))
        if self.verbosity > 1:
            self.stream.write(f"❌ {test._testMethodName} ... FAIL\n")
            
    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.test_results.append(('SKIP', test._testMethodName, test.__class__.__name__, reason))
        if self.verbosity > 1:
            self.stream.write(f"⏭️ {test._testMethodName} ... SKIP\n")


class DocumentExtractionTestSuite:
    """Main test suite for document extraction components"""
    
    def __init__(self):
        self.test_classes = [
            TestPDFExtractor,
            TestPDFExtractorIntegration,
            TestExcelExtractor,
            TestExcelExtractorIntegration,
            TestWordExtractor,
            TestWordExtractorIntegration,
            TestEdgeCases,
            TestSourceAttribution
        ]
        
    def create_test_suite(self):
        """Create comprehensive test suite"""
        suite = unittest.TestSuite()
        
        for test_class in self.test_classes:
            tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
            suite.addTests(tests)
            
        return suite
    
    def run_tests(self, verbosity=2):
        """Run all tests with detailed reporting"""
        print("🧪 Document Extraction Component Test Suite")
        print("=" * 50)
        print(f"Running tests for {len(self.test_classes)} test classes...")
        print()
        
        # Create test suite
        suite = self.create_test_suite()
        
        # Run tests with custom result handler
        stream = StringIO()
        runner = unittest.TextTestRunner(
            stream=stream,
            verbosity=verbosity,
            resultclass=ColoredTestResult
        )
        
        start_time = time.time()
        result = runner.run(suite)
        end_time = time.time()
        
        # Generate detailed report
        self.generate_report(result, end_time - start_time)
        
        return result
    
    def generate_report(self, result, duration):
        """Generate detailed test report"""
        print("\n" + "=" * 70)
        print("📊 TEST REPORT SUMMARY")
        print("=" * 70)
        
        total_tests = result.testsRun
        failures = len(result.failures)
        errors = len(result.errors)
        skipped = len(result.skipped)
        passed = total_tests - failures - errors - skipped
        
        print(f"Total Tests Run: {total_tests}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failures}")
        print(f"💥 Errors: {errors}")
        print(f"⏭️ Skipped: {skipped}")
        print(f"⏱️ Duration: {duration:.2f} seconds")
        
        success_rate = (passed / total_tests * 100) if total_tests > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        # Detailed breakdown by test class
        print("\n" + "=" * 70)
        print("📋 DETAILED BREAKDOWN BY COMPONENT")
        print("=" * 70)
        
        class_results = {}
        for status, test_name, class_name, error in result.test_results:
            if class_name not in class_results:
                class_results[class_name] = {'PASS': 0, 'FAIL': 0, 'ERROR': 0, 'SKIP': 0}
            class_results[class_name][status] += 1
        
        for class_name, counts in class_results.items():
            total_class = sum(counts.values())
            passed_class = counts['PASS']
            print(f"\n{class_name}:")
            print(f"  ✅ Passed: {counts['PASS']}")
            print(f"  ❌ Failed: {counts['FAIL']}")
            print(f"  💥 Errors: {counts['ERROR']}")
            print(f"  ⏭️ Skipped: {counts['SKIP']}")
            print(f"  📊 Success Rate: {(passed_class/total_class*100):.1f}%")
        
        # Show failures and errors
        if result.failures or result.errors:
            print("\n" + "=" * 70)
            print("🔍 DETAILED FAILURE/ERROR INFORMATION")
            print("=" * 70)
            
            for test, traceback in result.failures:
                print(f"\n❌ FAILURE: {test}")
                print("-" * 50)
                print(traceback)
            
            for test, traceback in result.errors:
                print(f"\n💥 ERROR: {test}")
                print("-" * 50)
                print(traceback)
        
        # Component-specific insights
        print("\n" + "=" * 70)
        print("🎯 COMPONENT-SPECIFIC INSIGHTS")
        print("=" * 70)
        
        insights = self.generate_component_insights(class_results)
        for insight in insights:
            print(f"• {insight}")
        
        # Recommendations
        print("\n" + "=" * 70)
        print("💡 RECOMMENDATIONS")
        print("=" * 70)
        
        recommendations = self.generate_recommendations(result, success_rate)
        for rec in recommendations:
            print(f"• {rec}")
    
    def generate_component_insights(self, class_results):
        """Generate insights about component performance"""
        insights = []
        
        # PDF Extractor insights
        pdf_classes = [cls for cls in class_results.keys() if 'PDF' in cls]
        if pdf_classes:
            pdf_total = sum(sum(class_results[cls].values()) for cls in pdf_classes)
            pdf_passed = sum(class_results[cls]['PASS'] for cls in pdf_classes)
            insights.append(f"PDF Extractor: {pdf_passed}/{pdf_total} tests passed - LLMWhisperer integration {'stable' if pdf_passed/pdf_total > 0.8 else 'needs attention'}")
        
        # Excel Extractor insights
        excel_classes = [cls for cls in class_results.keys() if 'Excel' in cls]
        if excel_classes:
            excel_total = sum(sum(class_results[cls].values()) for cls in excel_classes)
            excel_passed = sum(class_results[cls]['PASS'] for cls in excel_classes)
            insights.append(f"Excel Extractor: {excel_passed}/{excel_total} tests passed - Formula parsing and cell referencing {'working well' if excel_passed/excel_total > 0.8 else 'needs improvement'}")
        
        # Word Extractor insights
        word_classes = [cls for cls in class_results.keys() if 'Word' in cls]
        if word_classes:
            word_total = sum(sum(class_results[cls].values()) for cls in word_classes)
            word_passed = sum(class_results[cls]['PASS'] for cls in word_classes)
            insights.append(f"Word Extractor: {word_passed}/{word_total} tests passed - Document structure extraction {'robust' if word_passed/word_total > 0.8 else 'requires fixes'}")
        
        # Source Attribution insights
        attr_classes = [cls for cls in class_results.keys() if 'Attribution' in cls]
        if attr_classes:
            attr_total = sum(sum(class_results[cls].values()) for cls in attr_classes)
            attr_passed = sum(class_results[cls]['PASS'] for cls in attr_classes)
            insights.append(f"Source Attribution: {attr_passed}/{attr_total} tests passed - Data tracking {'accurate' if attr_passed/attr_total > 0.9 else 'may have issues'}")
        
        # Edge Cases insights
        edge_classes = [cls for cls in class_results.keys() if 'Edge' in cls]
        if edge_classes:
            edge_total = sum(sum(class_results[cls].values()) for cls in edge_classes)
            edge_passed = sum(class_results[cls]['PASS'] for cls in edge_classes)
            insights.append(f"Edge Cases: {edge_passed}/{edge_total} tests passed - Error handling {'robust' if edge_passed/edge_total > 0.7 else 'needs strengthening'}")
        
        return insights
    
    def generate_recommendations(self, result, success_rate):
        """Generate recommendations based on test results"""
        recommendations = []
        
        if success_rate >= 95:
            recommendations.append("Excellent! All components are working well. Consider adding more edge case tests.")
        elif success_rate >= 85:
            recommendations.append("Good overall performance. Review and fix failing tests.")
        elif success_rate >= 70:
            recommendations.append("Several issues detected. Prioritize fixing failed tests before deployment.")
        else:
            recommendations.append("Significant issues found. Extensive debugging and fixes required.")
        
        if result.errors:
            recommendations.append("Address ERROR cases first - these indicate code issues that need immediate attention.")
        
        if result.failures:
            recommendations.append("Review FAILED tests to understand logic or expectation mismatches.")
        
        # Specific component recommendations
        if any('PDF' in str(failure[0]) for failure in result.failures + result.errors):
            recommendations.append("PDF extraction issues detected. Check LLMWhisperer API integration and error handling.")
        
        if any('Excel' in str(failure[0]) for failure in result.failures + result.errors):
            recommendations.append("Excel extraction issues found. Verify openpyxl integration and formula processing.")
        
        if any('Word' in str(failure[0]) for failure in result.failures + result.errors):
            recommendations.append("Word extraction problems identified. Check python-docx integration and structure parsing.")
        
        if any('Attribution' in str(failure[0]) for failure in result.failures + result.errors):
            recommendations.append("Source attribution issues detected. Review SourceTracker implementation and data consistency.")
        
        return recommendations


def main():
    """Main function to run the test suite"""
    print("🚀 Starting Document Extraction Test Suite...")
    
    # Check if we're in the right directory
    current_dir = os.getcwd()
    if not os.path.exists(os.path.join(current_dir, 'lib')):
        print("❌ Error: Please run this script from the project root directory")
        sys.exit(1)
    
    # Create and run test suite
    test_suite = DocumentExtractionTestSuite()
    result = test_suite.run_tests(verbosity=2)
    
    # Exit with appropriate code
    if result.wasSuccessful():
        print("\n🎉 All tests passed! Components are ready for use.")
        sys.exit(0)
    else:
        print(f"\n⚠️ Tests completed with {len(result.failures)} failures and {len(result.errors)} errors.")
        print("Please review and fix the issues before deployment.")
        sys.exit(1)


if __name__ == '__main__':
    main()