#!/bin/bash

# Smoke tests for Sleuth Intel deployment

set -euo pipefail

# Configuration
ENVIRONMENT=${1:-staging}
BASE_URL="${BASE_URL:-http://localhost:8000}"
API_KEY="${API_KEY:-test-api-key}"
TIMEOUT=10

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Functions
log_test() {
    echo -e "\n${YELLOW}[TEST]${NC} $1"
    ((TESTS_RUN++))
}

log_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((TESTS_PASSED++))
}

log_fail() {
    echo -e "${RED}✗${NC} $1"
    ((TESTS_FAILED++))
}

# Test functions
test_health_endpoint() {
    log_test "Health endpoint"

    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" --max-time ${TIMEOUT} ${BASE_URL}/health)

    if [ "$RESPONSE" == "200" ]; then
        log_pass "Health endpoint returned 200"
    else
        log_fail "Health endpoint returned $RESPONSE"
    fi
}

test_ready_endpoint() {
    log_test "Ready endpoint"

    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" --max-time ${TIMEOUT} ${BASE_URL}/ready)

    if [ "$RESPONSE" == "200" ]; then
        log_pass "Ready endpoint returned 200"
    else
        log_fail "Ready endpoint returned $RESPONSE"
    fi
}

test_metrics_endpoint() {
    log_test "Metrics endpoint"

    RESPONSE=$(curl -s --max-time ${TIMEOUT} ${BASE_URL}:9090/metrics)

    if echo "$RESPONSE" | grep -q "# HELP"; then
        log_pass "Metrics endpoint returns Prometheus format"
    else
        log_fail "Metrics endpoint does not return valid format"
    fi
}

test_api_authentication() {
    log_test "API authentication"

    # Test without API key
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" --max-time ${TIMEOUT} ${BASE_URL}/api/v1/search)

    if [ "$RESPONSE" == "401" ] || [ "$RESPONSE" == "403" ]; then
        log_pass "API requires authentication"
    else
        log_fail "API does not require authentication (returned $RESPONSE)"
    fi
}

test_api_with_key() {
    log_test "API with valid key"

    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" --max-time ${TIMEOUT} \
        -H "Authorization: Bearer ${API_KEY}" \
        ${BASE_URL}/api/v1/search)

    if [ "$RESPONSE" == "200" ] || [ "$RESPONSE" == "400" ]; then
        log_pass "API accepts valid authentication"
    else
        log_fail "API with valid key returned $RESPONSE"
    fi
}

test_database_connection() {
    log_test "Database connection"

    RESPONSE=$(curl -s --max-time ${TIMEOUT} ${BASE_URL}/health)

    if echo "$RESPONSE" | grep -q '"database":"healthy"'; then
        log_pass "Database connection is healthy"
    else
        log_fail "Database connection is not healthy"
    fi
}

test_redis_connection() {
    log_test "Redis connection"

    RESPONSE=$(curl -s --max-time ${TIMEOUT} ${BASE_URL}/health)

    if echo "$RESPONSE" | grep -q '"redis":"healthy"'; then
        log_pass "Redis connection is healthy"
    else
        log_fail "Redis connection is not healthy"
    fi
}

test_response_headers() {
    log_test "Security headers"

    HEADERS=$(curl -s -I --max-time ${TIMEOUT} ${BASE_URL}/health)

    SECURITY_HEADERS=(
        "X-Content-Type-Options: nosniff"
        "X-Frame-Options: DENY"
        "X-XSS-Protection: 1"
    )

    HEADERS_OK=true
    for header in "${SECURITY_HEADERS[@]}"; do
        if ! echo "$HEADERS" | grep -q "$header"; then
            log_fail "Missing header: $header"
            HEADERS_OK=false
        fi
    done

    if [ "$HEADERS_OK" = true ]; then
        log_pass "All security headers present"
    fi
}

test_rate_limiting() {
    log_test "Rate limiting"

    # Make multiple rapid requests
    for i in {1..20}; do
        curl -s -o /dev/null ${BASE_URL}/api/v1/search &
    done
    wait

    # Check if rate limit is enforced
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/api/v1/search)

    if [ "$RESPONSE" == "429" ]; then
        log_pass "Rate limiting is active"
    else
        log_fail "Rate limiting not enforced (returned $RESPONSE)"
    fi
}

test_error_handling() {
    log_test "Error handling"

    # Test invalid endpoint
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" --max-time ${TIMEOUT} \
        ${BASE_URL}/api/v1/invalid_endpoint)

    if [ "$RESPONSE" == "404" ]; then
        log_pass "404 error handling works"
    else
        log_fail "Invalid endpoint returned $RESPONSE instead of 404"
    fi
}

# Performance tests
test_response_time() {
    log_test "Response time"

    RESPONSE_TIME=$(curl -s -o /dev/null -w "%{time_total}" --max-time ${TIMEOUT} \
        ${BASE_URL}/health)

    # Convert to milliseconds
    RESPONSE_MS=$(echo "$RESPONSE_TIME * 1000" | bc | cut -d. -f1)

    if [ "$RESPONSE_MS" -lt 1000 ]; then
        log_pass "Response time is ${RESPONSE_MS}ms (< 1000ms)"
    else
        log_fail "Response time is ${RESPONSE_MS}ms (>= 1000ms)"
    fi
}

# Main execution
main() {
    echo "========================================="
    echo "Sleuth Intel Smoke Tests"
    echo "Environment: ${ENVIRONMENT}"
    echo "Base URL: ${BASE_URL}"
    echo "========================================="

    # Run tests
    test_health_endpoint
    test_ready_endpoint
    test_metrics_endpoint
    test_api_authentication
    test_api_with_key
    test_database_connection
    test_redis_connection
    test_response_headers
    test_rate_limiting
    test_error_handling
    test_response_time

    # Summary
    echo ""
    echo "========================================="
    echo "Test Summary"
    echo "========================================="
    echo -e "Tests run: ${TESTS_RUN}"
    echo -e "${GREEN}Tests passed: ${TESTS_PASSED}${NC}"
    echo -e "${RED}Tests failed: ${TESTS_FAILED}${NC}"

    if [ ${TESTS_FAILED} -eq 0 ]; then
        echo -e "\n${GREEN}All smoke tests passed!${NC}"
        exit 0
    else
        echo -e "\n${RED}Some smoke tests failed${NC}"
        exit 1
    fi
}

# Run main function
main
