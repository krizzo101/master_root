#!/bin/bash

# Sleuth Intel Test Runner Script
# Usage: ./scripts/run_tests.sh [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
TEST_TYPE="all"
COVERAGE=true
VERBOSE=false
PARALLEL=true
MARKERS=""
REPORT_FORMAT="term"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --type)
            TEST_TYPE="$2"
            shift 2
            ;;
        --no-coverage)
            COVERAGE=false
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --no-parallel)
            PARALLEL=false
            shift
            ;;
        --markers)
            MARKERS="$2"
            shift 2
            ;;
        --report)
            REPORT_FORMAT="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --type [all|unit|integration|e2e|performance]  Test type to run (default: all)"
            echo "  --no-coverage                                   Disable coverage reporting"
            echo "  --verbose                                       Enable verbose output"
            echo "  --no-parallel                                   Disable parallel test execution"
            echo "  --markers <markers>                            Pytest markers to use"
            echo "  --report [term|html|xml|json]                  Report format (default: term)"
            echo "  --help                                          Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    print_warning "Virtual environment not activated. Activating..."
    if [[ -f "venv/bin/activate" ]]; then
        source venv/bin/activate
    else
        print_error "Virtual environment not found. Please create one first."
        exit 1
    fi
fi

# Install/upgrade test dependencies
print_status "Installing test dependencies..."
pip install -q --upgrade pytest pytest-cov pytest-asyncio pytest-benchmark pytest-xdist

# Clean previous test artifacts
print_status "Cleaning previous test artifacts..."
rm -rf .pytest_cache
rm -rf htmlcov
rm -f coverage.xml
rm -f .coverage
rm -rf test-results

# Create test results directory
mkdir -p test-results

# Build pytest command
PYTEST_CMD="pytest"

# Add verbosity
if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -vv"
else
    PYTEST_CMD="$PYTEST_CMD -v"
fi

# Add parallel execution
if [ "$PARALLEL" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -n auto"
fi

# Add coverage
if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=src --cov-branch"

    case $REPORT_FORMAT in
        html)
            PYTEST_CMD="$PYTEST_CMD --cov-report=html:htmlcov"
            ;;
        xml)
            PYTEST_CMD="$PYTEST_CMD --cov-report=xml:coverage.xml"
            ;;
        json)
            PYTEST_CMD="$PYTEST_CMD --cov-report=json:coverage.json"
            ;;
        *)
            PYTEST_CMD="$PYTEST_CMD --cov-report=term-missing"
            ;;
    esac
fi

# Add test output format
PYTEST_CMD="$PYTEST_CMD --junit-xml=test-results/junit.xml"

# Add markers if specified
if [[ -n "$MARKERS" ]]; then
    PYTEST_CMD="$PYTEST_CMD -m \"$MARKERS\""
fi

# Function to run tests
run_tests() {
    local test_path=$1
    local test_name=$2

    print_status "Running $test_name tests..."

    if $PYTEST_CMD $test_path; then
        print_status "$test_name tests passed!"
        return 0
    else
        print_error "$test_name tests failed!"
        return 1
    fi
}

# Main test execution
print_status "Starting test execution..."
echo "Test type: $TEST_TYPE"
echo "Coverage: $COVERAGE"
echo "Parallel: $PARALLEL"
echo ""

case $TEST_TYPE in
    all)
        run_tests "tests/" "All"
        ;;
    unit)
        run_tests "tests/unit" "Unit"
        ;;
    integration)
        run_tests "tests/integration" "Integration"
        ;;
    e2e)
        run_tests "tests/e2e" "End-to-End"
        ;;
    performance)
        print_status "Running performance tests..."
        pytest tests/performance -v -m "performance" --benchmark-only --benchmark-json=test-results/benchmark.json
        ;;
    *)
        print_error "Unknown test type: $TEST_TYPE"
        exit 1
        ;;
esac

# Generate coverage report
if [ "$COVERAGE" = true ] && [ "$REPORT_FORMAT" = "html" ]; then
    print_status "Opening coverage report in browser..."
    if command -v xdg-open &> /dev/null; then
        xdg-open htmlcov/index.html
    elif command -v open &> /dev/null; then
        open htmlcov/index.html
    else
        print_warning "Could not open browser. Coverage report available at htmlcov/index.html"
    fi
fi

# Run linting checks
print_status "Running linting checks..."
echo ""

# Black
if command -v black &> /dev/null; then
    print_status "Running Black formatter check..."
    black --check src tests || print_warning "Black formatting issues found"
fi

# isort
if command -v isort &> /dev/null; then
    print_status "Running isort import checker..."
    isort --check-only src tests || print_warning "Import sorting issues found"
fi

# Flake8
if command -v flake8 &> /dev/null; then
    print_status "Running Flake8 linter..."
    flake8 src tests || print_warning "Flake8 issues found"
fi

# MyPy
if command -v mypy &> /dev/null; then
    print_status "Running MyPy type checker..."
    mypy src || print_warning "Type checking issues found"
fi

# Generate test summary
print_status "Generating test summary..."
echo ""
echo "========================================="
echo "           TEST SUMMARY"
echo "========================================="

if [ -f "test-results/junit.xml" ]; then
    # Parse junit.xml for summary (requires xmllint)
    if command -v xmllint &> /dev/null; then
        TOTAL=$(xmllint --xpath "string(//testsuite/@tests)" test-results/junit.xml 2>/dev/null || echo "0")
        FAILURES=$(xmllint --xpath "string(//testsuite/@failures)" test-results/junit.xml 2>/dev/null || echo "0")
        ERRORS=$(xmllint --xpath "string(//testsuite/@errors)" test-results/junit.xml 2>/dev/null || echo "0")
        TIME=$(xmllint --xpath "string(//testsuite/@time)" test-results/junit.xml 2>/dev/null || echo "0")

        echo "Total tests: $TOTAL"
        echo "Failures: $FAILURES"
        echo "Errors: $ERRORS"
        echo "Time: ${TIME}s"
    fi
fi

if [ "$COVERAGE" = true ] && [ -f ".coverage" ]; then
    echo ""
    echo "Coverage Summary:"
    python -m coverage report --skip-empty --skip-covered | tail -n 1
fi

echo "========================================="
echo ""

print_status "Test execution completed!"
