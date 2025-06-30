#!/bin/bash

# Comprehensive Test Runner for Document-Slides-POC
# Agent 5: End-to-End Workflow Testing

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
BASE_URL="http://localhost:5001"
TEST_TYPE="all"
VERBOSE=true
QUICK=false
SERVER_AUTO_START=false

# Function to print colored output
print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Comprehensive testing for Document-Slides-POC workflow validation"
    echo ""
    echo "OPTIONS:"
    echo "  -u, --url URL         Base URL for API server (default: http://localhost:5001)"
    echo "  -t, --test TYPE       Test type: all, core, integration, ux, performance (default: all)"
    echo "  -q, --quick          Run quick tests only (skip non-critical)"
    echo "  -s, --start-server   Attempt to start API server automatically"
    echo "  -v, --verbose        Verbose output (default: true)"
    echo "  --silent             Minimal output"
    echo "  -h, --help           Show this help message"
    echo ""
    echo "EXAMPLES:"
    echo "  $0                              # Run full test suite"
    echo "  $0 --quick                      # Run critical tests only"
    echo "  $0 --test core                  # Run core functionality tests"
    echo "  $0 --url http://localhost:5002  # Test different port"
    echo "  $0 --start-server               # Auto-start server and test"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--url)
            BASE_URL="$2"
            shift 2
            ;;
        -t|--test)
            TEST_TYPE="$2"
            shift 2
            ;;
        -q|--quick)
            QUICK=true
            shift
            ;;
        -s|--start-server)
            SERVER_AUTO_START=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --silent)
            VERBOSE=false
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Function to check if API server is running
check_server() {
    local url=$1
    if command -v curl &> /dev/null; then
        curl -s --connect-timeout 5 "$url/health" > /dev/null 2>&1
    else
        # Fallback using Python
        python3 -c "
import requests
import sys
try:
    response = requests.get('$url/health', timeout=5)
    sys.exit(0 if response.status_code == 200 else 1)
except:
    sys.exit(1)
" 2>/dev/null
    fi
}

# Function to start API server
start_server() {
    print_info "Attempting to start API server..."
    
    if [[ -f "start_server.py" ]]; then
        print_info "Starting server using start_server.py..."
        python3 start_server.py &
        SERVER_PID=$!
        
        # Wait for server to start
        for i in {1..30}; do
            if check_server "$BASE_URL"; then
                print_success "Server started successfully (PID: $SERVER_PID)"
                return 0
            fi
            sleep 2
        done
        
        print_error "Server failed to start within 60 seconds"
        kill $SERVER_PID 2>/dev/null || true
        return 1
        
    elif [[ -f "api/generate_slides.py" ]]; then
        print_info "Starting server using Flask directly..."
        cd api
        python3 generate_slides.py &
        SERVER_PID=$!
        cd ..
        
        # Wait for server to start
        for i in {1..30}; do
            if check_server "$BASE_URL"; then
                print_success "Server started successfully (PID: $SERVER_PID)"
                return 0
            fi
            sleep 2
        done
        
        print_error "Server failed to start within 60 seconds"
        kill $SERVER_PID 2>/dev/null || true
        return 1
    else
        print_error "No server startup script found"
        return 1
    fi
}

# Function to stop server
stop_server() {
    if [[ -n "$SERVER_PID" ]]; then
        print_info "Stopping server (PID: $SERVER_PID)..."
        kill $SERVER_PID 2>/dev/null || true
        wait $SERVER_PID 2>/dev/null || true
        print_success "Server stopped"
    fi
}

# Function to check dependencies
check_dependencies() {
    print_info "Checking dependencies..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not found"
        return 1
    fi
    
    # Check required Python modules
    python3 -c "
import sys
required_modules = ['requests', 'json', 'datetime', 'pathlib']
missing = []

for module in required_modules:
    try:
        __import__(module)
    except ImportError:
        missing.append(module)

if missing:
    print('Missing required modules:', ', '.join(missing))
    sys.exit(1)
" || {
        print_error "Required Python modules are missing"
        print_info "Try: pip install -r requirements.txt"
        return 1
    }
    
    # Check test files exist
    if [[ ! -f "test_workflow_runner.py" ]]; then
        print_error "test_workflow_runner.py not found"
        return 1
    fi
    
    if [[ ! -f "test_end_to_end_workflows.py" ]]; then
        print_error "test_end_to_end_workflows.py not found"
        return 1
    fi
    
    if [[ ! -f "test_web_interface_workflows.py" ]]; then
        print_error "test_web_interface_workflows.py not found"
        return 1
    fi
    
    print_success "All dependencies check passed"
    return 0
}

# Function to run tests
run_tests() {
    local test_args=""
    
    # Build arguments
    test_args="--base-url $BASE_URL"
    
    if [[ "$TEST_TYPE" != "all" ]]; then
        test_args="$test_args --phase $TEST_TYPE"
    fi
    
    if [[ "$QUICK" == "true" ]]; then
        test_args="$test_args --quick"
    fi
    
    if [[ "$VERBOSE" == "true" ]]; then
        test_args="$test_args --verbose"
    fi
    
    print_header "RUNNING COMPREHENSIVE WORKFLOW TESTS"
    print_info "Test configuration:"
    print_info "  Base URL: $BASE_URL"
    print_info "  Test type: $TEST_TYPE"
    print_info "  Quick mode: $QUICK"
    print_info "  Verbose: $VERBOSE"
    print_info ""
    
    # Run the main test runner
    python3 test_workflow_runner.py $test_args
    local exit_code=$?
    
    return $exit_code
}

# Function to generate summary
generate_summary() {
    local exit_code=$1
    
    print_header "TEST EXECUTION SUMMARY"
    
    case $exit_code in
        0)
            print_success "All tests passed - System ready for production"
            ;;
        1)
            print_warning "Some tests failed - System needs improvements"
            ;;
        2)
            print_error "Critical failures detected - System needs significant work"
            ;;
        *)
            print_error "Test execution failed with unexpected error"
            ;;
    esac
    
    # Look for generated reports
    print_info "Generated reports:"
    for report in comprehensive_workflow_report_*.json; do
        if [[ -f "$report" ]]; then
            print_info "  📄 $report"
        fi
    done
    
    for summary in workflow_summary_*.txt; do
        if [[ -f "$summary" ]]; then
            print_info "  📄 $summary"
        fi
    done
}

# Cleanup function
cleanup() {
    if [[ "$SERVER_AUTO_START" == "true" ]]; then
        stop_server
    fi
}

# Set up trap for cleanup
trap cleanup EXIT

# Main execution
main() {
    print_header "DOCUMENT-SLIDES-POC COMPREHENSIVE TESTING"
    
    # Check dependencies
    if ! check_dependencies; then
        exit 1
    fi
    
    # Check if server is running or start it
    if check_server "$BASE_URL"; then
        print_success "API server is already running at $BASE_URL"
    elif [[ "$SERVER_AUTO_START" == "true" ]]; then
        if ! start_server; then
            print_error "Failed to start API server"
            exit 1
        fi
    else
        print_warning "API server is not running at $BASE_URL"
        print_info "Some tests may be skipped. Use --start-server to auto-start."
        print_info "Or manually start the server with: python3 start_server.py"
    fi
    
    # Run tests
    local exit_code=0
    if run_tests; then
        exit_code=0
    else
        exit_code=$?
    fi
    
    # Generate summary
    generate_summary $exit_code
    
    # Final message
    echo ""
    if [[ $exit_code -eq 0 ]]; then
        print_success "Comprehensive testing completed successfully!"
    else
        print_warning "Testing completed with issues. Review the reports for details."
    fi
    
    exit $exit_code
}

# Run main function
main "$@"