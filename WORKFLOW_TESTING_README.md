# End-to-End Workflow Testing Framework

This comprehensive testing framework validates the complete document-slides-poc system from end-to-end, ensuring all workflows function correctly and the system is ready for production use.

## 📋 Overview

The testing framework consists of multiple test suites that validate:

- **Document Processing Pipeline**: Excel, PDF, and Word document extraction
- **Source Attribution System**: Accurate tracking of data back to source documents  
- **Template Management**: Brand template selection and application
- **Slide Generation**: PowerPoint creation with proper formatting
- **Web Interface**: Complete user workflow simulation
- **API Integration**: All endpoints and error handling
- **Performance**: Response times and resource usage

## 🏗️ Test Architecture

### Core Test Modules

1. **`test_end_to_end_workflows.py`**
   - Complete system pipeline testing
   - Multi-document processing scenarios
   - Content accuracy validation
   - PowerPoint output validation

2. **`test_web_interface_workflows.py`**
   - Web interface loading and functionality
   - User experience scenario testing
   - Document upload workflows
   - Error handling validation

3. **`test_workflow_runner.py`**
   - Master test coordinator
   - Comprehensive reporting
   - System health monitoring
   - Production readiness assessment

### Test Categories

#### 🔧 Core Functionality Tests
- Document extraction pipeline (Excel, PDF, Word)
- Multi-document processing and data correlation
- Content accuracy against source documents
- PowerPoint generation and structure validation

#### 🌐 Integration Tests
- API workflow simulation
- Template management integration
- End-to-end document → slides pipeline
- Cross-component data flow validation

#### 👤 User Experience Tests
- Web interface loading and responsiveness
- Document upload and preview workflows
- Template selection and application
- Error message clarity and handling

#### ⚡ Performance Tests
- API response time validation
- Concurrent request handling
- Resource usage monitoring
- System stability under load

## 🚀 Running Tests

### Quick Start

```bash
# Make the script executable
chmod +x run_comprehensive_tests.sh

# Run complete test suite
./run_comprehensive_tests.sh

# Run with auto-server start
./run_comprehensive_tests.sh --start-server

# Run quick critical tests only
./run_comprehensive_tests.sh --quick
```

### Detailed Options

```bash
# Full test suite with verbose output
./run_comprehensive_tests.sh --verbose

# Test specific components
./run_comprehensive_tests.sh --test core        # Core functionality only
./run_comprehensive_tests.sh --test integration # API integration only
./run_comprehensive_tests.sh --test ux          # User experience only
./run_comprehensive_tests.sh --test performance # Performance only

# Test against different server
./run_comprehensive_tests.sh --url http://localhost:5002

# Silent mode for CI/CD
./run_comprehensive_tests.sh --silent
```

### Python Direct Execution

```bash
# Run complete validation
python3 test_workflow_runner.py

# Run specific test categories
python3 test_end_to_end_workflows.py --test extraction
python3 test_web_interface_workflows.py --test upload

# Run with custom server URL
python3 test_workflow_runner.py --base-url http://localhost:5002
```

## 📊 Test Scenarios

### Scenario 1: First-Time User Experience
1. Load web interface
2. Explore available templates  
3. Upload single document (Excel file)
4. Preview extraction results
5. Generate slides with default template
6. Download PowerPoint file

### Scenario 2: Power User Multi-Document Workflow
1. Load web interface
2. Upload custom brand template
3. Upload multiple documents (Excel + PDF + Word)
4. Preview extraction from all sources
5. Select custom template
6. Generate branded slides
7. Download and validate output

### Scenario 3: Template Management Workflow
1. List available templates
2. Upload new template
3. Switch between templates
4. Test template styling application
5. Validate brand consistency

### Scenario 4: Error Handling Validation
1. Upload invalid file types
2. Send empty requests
3. Test large file handling
4. Simulate network timeouts
5. Validate graceful error responses

## 📈 Test Data and Validation

### Sample Test Documents

The framework automatically creates realistic test documents:

**Excel File (`sample_financials.xlsx`)**:
- Company: TechCorp Inc.
- Revenue: $10.2M (Cell B15)
- Profit: $2.5M (Cell B16)  
- Growth Rate: 23% (Cell B17)
- Calculated metrics with formulas

**PDF Content (`company_overview.pdf`)**:
- Company overview and business model
- Performance highlights section
- Market position analysis
- Cross-referenced metrics (23% growth)

**Word Document (`business_plan.docx`)**:
- Executive summary
- Market analysis  
- Financial projections
- Structured heading hierarchy

### Validation Criteria

#### Content Accuracy (≥85% required)
- ✅ Values preserved exactly from source
- ✅ Source attribution correctly mapped
- ✅ Cell/page references accurate
- ✅ Cross-document consistency maintained

#### Source Attribution (≥90% required)
- ✅ Document name and type tracked
- ✅ Sheet/page location recorded
- ✅ Cell/section references precise
- ✅ Clickable hyperlinks functional

#### Template Application (≥80% required)
- ✅ Brand colors applied correctly
- ✅ Font styling consistent
- ✅ Layout structure maintained
- ✅ Template switching functional

## 📋 Report Generation

### Comprehensive Reports

Tests generate multiple report formats:

1. **JSON Detail Report** (`comprehensive_workflow_report_YYYYMMDD_HHMMSS.json`)
   - Complete test execution data
   - Individual test results and metrics
   - Error details and stack traces
   - Performance measurements

2. **Summary Report** (`workflow_summary_YYYYMMDD_HHMMSS.txt`)
   - High-level test results
   - Overall system score
   - Readiness assessment
   - Key recommendations

3. **Console Output**
   - Real-time test progress
   - Color-coded results
   - Immediate feedback
   - Error highlighting

### Scoring System

- **90-100%**: 🟢 Production Ready
- **75-89%**: 🟡 Staging Ready  
- **60-74%**: 🟠 Development Ready
- **<60%**: 🔴 Needs Significant Work

## 🔧 System Requirements

### Prerequisites

- Python 3.7+
- API server running (or auto-start capability)
- Required Python packages:
  - `requests`
  - `flask` 
  - `openpyxl` (optional, for Excel processing)
  - `python-pptx` (optional, for PowerPoint validation)

### Installation

```bash
# Install required packages
pip install -r requirements.txt

# Or minimal requirements
pip install requests flask

# Optional packages for enhanced testing
pip install openpyxl python-pptx psutil
```

## 🐛 Troubleshooting

### Common Issues

**API Server Not Available**
```bash
# Start server manually
python3 start_server.py

# Or use auto-start option
./run_comprehensive_tests.sh --start-server
```

**Import Errors**
```bash
# Install missing dependencies
pip install -r requirements.txt

# Check Python path
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

**Test Failures**
```bash
# Run specific test for debugging
python3 test_end_to_end_workflows.py --test extraction

# Check detailed JSON reports for error details
cat comprehensive_workflow_report_*.json | jq '.phase_results'
```

**Permission Issues**
```bash
# Make scripts executable
chmod +x run_comprehensive_tests.sh

# Check file system permissions
ls -la test_*.py
```

### Debug Mode

```bash
# Enable verbose logging
./run_comprehensive_tests.sh --verbose

# Run individual test modules
python3 -m pytest test_end_to_end_workflows.py -v

# Check API connectivity
curl http://localhost:5001/health
```

## 🚀 CI/CD Integration

### GitHub Actions Example

```yaml
name: Workflow Testing
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.8'
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Run comprehensive tests
      run: ./run_comprehensive_tests.sh --start-server --silent
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any
    stages {
        stage('Setup') {
            steps {
                sh 'pip install -r requirements.txt'
            }
        }
        stage('Test') {
            steps {
                sh './run_comprehensive_tests.sh --start-server'
            }
        }
    }
    post {
        always {
            archiveArtifacts artifacts: '*_report_*.json,*_summary_*.txt'
        }
    }
}
```

## 📞 Support

For issues with the testing framework:

1. Check the generated error reports
2. Review the troubleshooting section
3. Verify all prerequisites are installed
4. Ensure the API server is accessible
5. Check file permissions and Python path

The testing framework is designed to be robust and provide clear feedback on any issues encountered during validation.