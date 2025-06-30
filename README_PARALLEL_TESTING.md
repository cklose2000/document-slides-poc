# Parallel API Testing System for Document-Slides-POC

## Overview

This parallel testing system uses multiple concurrent subagents to automatically test the document-slides-poc API endpoints with real demo files, providing rapid error detection and detailed analysis.

## Components

### Main Testing Orchestrator
- **File**: `test_api_parallel_demo.py`
- **Purpose**: Coordinates parallel testing across multiple agents
- **Features**: Real-time dashboard, error analysis, comprehensive reporting

### Error Analyzer
- **File**: `error_analyzer_demo.py`
- **Purpose**: Analyzes API errors with demo file context
- **Features**: Error pattern recognition, fix suggestions, priority ranking

### Real-time Dashboard
- **File**: `test_dashboard_demo.py`
- **Purpose**: Live monitoring of test execution
- **Features**: Progress tracking, agent status, error logging

## Usage

### Quick Test (Recommended for rapid feedback)
```bash
python3 test_api_parallel_demo.py quick
```

### Full Test Suite
```bash
python3 test_api_parallel_demo.py
```

### Help
```bash
python3 test_api_parallel_demo.py help
```

## Demo Files Used

The system automatically uses files from `/demo_files/`:
- `budget_model.xlsx` - Excel financial data
- `executive_summary.docx` - Word business content
- `financial_projections.xlsx` - Excel projections
- `financial_report_q3.pdf` - PDF financial report
- `market_analysis.pdf` - PDF market analysis
- `product_overview.docx` - Word product document

## Test Scenarios

### Single File Tests
- Individual file processing for each supported format
- Template compatibility testing

### Multi-File Combinations
- Excel + Word document combinations
- PDF + Excel combinations
- All files stress test

### Template Testing
- Tests across all available templates
- Template switching validation

### Error Scenarios
- Invalid file format handling
- Missing API key scenarios
- Server overload testing

## Output

### Console Output
Real-time progress with:
- ✅ Pass/❌ Fail indicators per test
- Agent status and progress
- Immediate error feedback
- Enhanced error analysis with suggested fixes

### Generated Reports
- **JSON Report**: `test_results_parallel_YYYYMMDD_HHMMSS.json`
- **Enhanced Error Analysis**: Detailed error categorization and fix recommendations
- **Performance Metrics**: Response times and throughput

## Error Analysis Features

### Automatic Error Detection
- **RGBColor attribute errors**: Color handling issues
- **Missing method errors**: Class method compatibility
- **Font configuration mismatches**: Template font issues
- **Chart parameter errors**: Chart generation compatibility
- **API key missing**: LLMWhisperer configuration issues

### Context-Aware Analysis
- Maps errors to specific demo files that triggered them
- Provides file-type specific insights
- Suggests fixes with code locations
- Prioritizes fixes by impact and complexity

### Fix Recommendations
- Specific code changes suggested
- Priority-based fix ordering
- Demo file context for testing fixes

## Example Output

```
🧪 Document-Slides-POC Parallel API Testing
============================================================
📁 Found 6 demo files
🤖 Deploying 4 agents for 25 tests

agent_0: ✅ PASS health_check (0.05s)
agent_1: ❌ FAIL slide_generation_single_budget_model.xlsx_simple_template (2.3s)
agent_1: Error Analysis: RGBColor_attribute_error (Priority 1)
agent_1: Suggested Fix: Use proper RGBColor construction or hex parsing instead of attribute access

📊 TEST RESULTS SUMMARY
============================================================
Total Tests: 25
Passed: 20 ✅
Failed: 5 ❌
Success Rate: 80.0%
Total Time: 45.2s

🔍 ENHANCED ERROR ANALYSIS:
🚨 CRITICAL ERRORS (Priority fixes):
1. RGBColor_attribute_error (Priority 1)
   Description: Attempting to access color attributes incorrectly on RGBColor objects
   Suggested Fix: Use proper RGBColor construction or hex parsing instead of attribute access
   Code Location: lib/slide_generator_branded.py:1322

🎯 MOST CRITICAL FIX: RGBColor_attribute_error
   Fix: Use proper RGBColor construction or hex parsing instead of attribute access
   Location: lib/slide_generator_branded.py:1322
```

## Benefits

1. **Rapid Error Detection**: Catches API issues in seconds instead of manual testing
2. **Comprehensive Coverage**: Tests all endpoints with real demo files
3. **Intelligent Analysis**: Provides specific error types and fix suggestions
4. **Demo-Ready Validation**: Ensures demo files work perfectly for presentations
5. **Parallel Execution**: 4x faster than sequential testing
6. **Real-time Feedback**: Live progress monitoring and immediate error reporting

## Integration

### Use in Development Workflow
1. Make code changes
2. Run `python3 test_api_parallel_demo.py quick` (30 seconds)
3. Get immediate error feedback with specific fixes
4. Apply suggested fixes
5. Re-run tests to validate

### Use for Demo Preparation
1. Run full test suite before demos
2. Verify all demo files work with all templates
3. Get confidence metrics for each demo scenario
4. Identify any demo files that need alternative approaches

## Requirements

- Python 3.7+
- requests library
- Access to demo_files directory
- Running document-slides-poc API server (localhost:5000)

## Troubleshooting

### "No demo files found"
- Ensure `/demo_files/` directory exists and contains demo files
- Check file permissions

### "Connection refused"
- Ensure API server is running on localhost:5000
- Check server status with health endpoint

### "Import errors"
- Ensure all Python dependencies are installed
- Error analyzer and dashboard will gracefully degrade if components are missing