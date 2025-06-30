# API Testing Guide for document-slides-poc

This guide explains how to use the comprehensive testing suite for the document-slides-poc API endpoints.

## Overview

The testing suite consists of multiple test files that validate different aspects of the API:

1. **Core Functionality Testing** - Basic API endpoint validation
2. **Mocked Testing** - Testing with mocked external dependencies
3. **Performance Testing** - Load, stress, and performance validation
4. **Security Testing** - Security vulnerabilities and edge cases
5. **Quick Validation** - Fast API health check

## Test Files

### 1. `validate_api.py` - Quick Validation
**Purpose**: Quick health check to verify the API is working

**Usage**:
```bash
python validate_api.py
```

**What it tests**:
- Health endpoint responsiveness
- Basic file upload and processing
- Slide generation functionality
- Template management availability
- Error handling

**When to use**: Before running full test suites, after server restarts

---

### 2. `test_api_endpoints.py` - Core API Testing
**Purpose**: Comprehensive testing of all API endpoints

**Usage**:
```bash
python test_api_endpoints.py
```

**What it tests**:
- `/api/generate-slides` with various file types
- `/api/generate-slides/preview` for extraction validation
- Template management endpoints (`/api/templates/*`)
- Error handling for invalid inputs
- Multiple file upload scenarios
- Response format validation
- Concurrent request handling

**Test scenarios**:
- ✅ Valid Excel, Word, and PDF files
- ❌ Invalid file formats
- ❌ Empty files and missing parameters
- 🔄 Multiple document processing
- 📊 Template selection
- ⚡ Concurrent requests

---

### 3. `test_api_mocked.py` - Mocked External Dependencies
**Purpose**: Test API behavior with mocked external services

**Usage**:
```bash
python test_api_mocked.py
```

**What it tests**:
- OpenAI API mocking for document analysis
- LLMWhisperer PDF extraction mocking
- Fallback behavior when APIs are unavailable
- Branded slide generation with mocked templates
- Performance with consistent mocked responses

**Benefits**:
- Consistent test results
- No dependency on external API keys
- Faster test execution
- Predictable responses for validation

---

### 4. `test_api_performance.py` - Performance & Stress Testing
**Purpose**: Validate API performance under various load conditions

**Usage**:
```bash
python test_api_performance.py
```

**What it tests**:
- Small, medium, and large file processing times
- Concurrent request handling (2, 5, 10 concurrent users)
- Memory usage stability
- Response time consistency
- Error handling performance
- Mixed file type processing
- Stress testing with rapid sequential requests

**Performance Metrics**:
- Average response times
- Memory usage patterns
- Concurrent request success rates
- System stability under load

---

### 5. `test_api_security_edge_cases.py` - Security Testing
**Purpose**: Test for security vulnerabilities and edge cases

**Usage**:
```bash
python test_api_security_edge_cases.py
```

**What it tests**:
- File size limits and large file handling
- Path traversal attacks in filenames
- SQL injection and XSS attempts
- Unicode and special character handling
- Binary file upload protection
- Header injection vulnerabilities
- Rate limiting protection
- Memory exhaustion attacks
- Content type confusion
- DoS protection

**Security Checks**:
- 🛡️ Input validation
- 🔒 File system protection
- 🚫 Injection attack prevention
- ⚠️ Malicious content handling

---

### 6. `run_all_api_tests.py` - Complete Test Suite Runner
**Purpose**: Run all test suites and generate comprehensive reports

**Usage**:
```bash
python run_all_api_tests.py
```

**What it does**:
- Checks dependencies and server status
- Runs all test suites sequentially
- Generates detailed markdown report
- Provides executive summary
- Includes recommendations

**Output**: `api_test_report_YYYYMMDD_HHMMSS.md`

## Prerequisites

### Required Dependencies
```bash
pip install flask requests openpyxl python-docx psutil
```

### Optional Dependencies (for full functionality)
```bash
pip install python-dotenv openai llmwhisperer-client matplotlib pillow numpy pandas
```

### Server Requirements
The API server must be running on `http://localhost:5000`

Start the server:
```bash
python start_server.py
# or
python api/generate_slides.py
```

## Test Execution Workflow

### 1. Quick Validation (2-3 minutes)
```bash
# Verify API is working
python validate_api.py
```

### 2. Core Functionality (5-10 minutes)
```bash
# Test all endpoints thoroughly
python test_api_endpoints.py
```

### 3. Performance Testing (10-15 minutes)
```bash
# Test under load
python test_api_performance.py
```

### 4. Security Testing (5-10 minutes)
```bash
# Test security and edge cases
python test_api_security_edge_cases.py
```

### 5. Complete Suite (20-30 minutes)
```bash
# Run everything with detailed report
python run_all_api_tests.py
```

## Understanding Test Results

### Success Indicators ✅
- All endpoints return appropriate HTTP status codes
- File processing completes within reasonable time
- Generated PowerPoint files are valid
- Error handling returns proper JSON responses
- No security vulnerabilities detected

### Warning Signs ⚠️
- Slow response times (>30s for large files)
- High memory usage growth
- Template management unavailable
- Some concurrent requests failing

### Failure Indicators ❌
- Server not responding
- File processing errors
- Invalid response formats
- Security vulnerabilities detected
- Excessive resource consumption

## Performance Benchmarks

### Expected Response Times
- **Health Check**: < 100ms
- **Small Files** (< 100KB): < 5s
- **Medium Files** (< 1MB): < 15s
- **Large Files** (< 5MB): < 30s
- **Preview Extraction**: < 10s

### Concurrency Expectations
- **2 concurrent users**: 90%+ success rate
- **5 concurrent users**: 80%+ success rate
- **10 concurrent users**: 70%+ success rate

### Memory Usage
- **Baseline**: < 100MB growth per request
- **Stability**: No continuous memory leaks
- **Recovery**: Memory cleanup between requests

## Troubleshooting

### Common Issues

**Server Not Running**
```
❌ API server is not accessible: Connection failed
```
- Solution: Start the server with `python start_server.py`

**Missing Dependencies**
```
❌ Missing dependencies: openpyxl, python-docx
```
- Solution: Install with `pip install openpyxl python-docx`

**Template Management Unavailable**
```
⚠️ Template management not available
```
- Expected if template system not configured
- Non-critical for basic functionality

**Performance Issues**
```
⚠️ Large file processing time: 45.2s
```
- Check server resources
- Consider file size limits
- Review processing optimization

### Environment Variables

For full functionality, set these environment variables:
```bash
export OPENAI_API_KEY="your-openai-key"
export LLMWHISPERER_API_KEY="your-llm-whisperer-key"
```

Without these keys, the system uses fallback analysis methods.

## Continuous Integration

### GitHub Actions Example
```yaml
name: API Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Start API server
        run: python start_server.py &
      - name: Wait for server
        run: sleep 10
      - name: Run API tests
        run: python run_all_api_tests.py
```

## Test Data

The test suites automatically generate sample data:
- Excel files with financial metrics
- Word documents with business content
- Various file sizes for performance testing
- Malicious files for security testing

All test data is created in temporary directories and cleaned up automatically.

## Report Analysis

### Test Report Structure
```
# API Testing Report
Generated: 2023-12-XX XX:XX:XX

## Executive Summary
- Total Test Suites: 4/4
- Successful Suites: 4/4  
- Overall Success Rate: 100.0%
- Total Testing Time: 125.3 seconds

## Test Suite Results
### ✅ Core API Endpoints
### ✅ Mocked External APIs  
### ✅ Performance & Stress Testing
### ✅ Security & Edge Cases

## Recommendations
```

### Key Metrics to Monitor
- Success rates by test suite
- Performance degradation over time
- Security vulnerability trends
- Resource usage patterns

## Best Practices

1. **Run quick validation** before major testing
2. **Test with realistic data** sizes and formats
3. **Monitor performance trends** over time
4. **Address security issues** immediately
5. **Update tests** as API evolves
6. **Document test failures** for debugging
7. **Run full suite** before releases

## Support

For issues with the testing suite:
1. Check server logs for errors
2. Verify all dependencies are installed
3. Ensure proper file permissions
4. Review test report details
5. Check network connectivity
6. Validate API endpoints manually

The testing suite is designed to be comprehensive, reliable, and easy to use for ensuring the document-slides-poc API is production-ready.