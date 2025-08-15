#!/bin/bash

# Auto-Forge Factory - Full End-to-End Demonstration
# This script demonstrates the complete autonomous software development pipeline

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
FACTORY_URL="http://localhost:8000"
DEMO_PROJECT_NAME="Task Management API"
DEMO_PROJECT_DESC="A RESTful API for collaborative task management with real-time updates"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1

    print_status "Waiting for $service_name to be ready..."

    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url/health" > /dev/null 2>&1; then
            print_status "$service_name is ready!"
            return 0
        fi

        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done

    print_error "$service_name failed to start within $((max_attempts * 2)) seconds"
    return 1
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_status "Docker is running"
}

# Function to start the Auto-Forge Factory
start_factory() {
    print_header "Starting Auto-Forge Factory"

    check_docker

    # Check if factory is already running
    if curl -s "$FACTORY_URL/health" > /dev/null 2>&1; then
        print_status "Auto-Forge Factory is already running"
        return 0
    fi

    print_step "Starting Auto-Forge Factory with Docker Compose..."

    # Start the factory
    cd auto_forge_factory
    docker-compose up -d

    # Wait for factory to be ready
    wait_for_service "$FACTORY_URL" "Auto-Forge Factory"

    print_status "Auto-Forge Factory started successfully!"
}

# Function to check factory health
check_factory_health() {
    print_header "Checking Factory Health"

    print_step "Checking factory health endpoint..."

    local health_response=$(curl -s "$FACTORY_URL/health")
    local status=$(echo "$health_response" | jq -r '.status' 2>/dev/null || echo "unknown")

    if [ "$status" = "healthy" ]; then
        print_status "Factory is healthy"
        echo "$health_response" | jq '.'
    else
        print_error "Factory is not healthy. Status: $status"
        return 1
    fi
}

# Function to get factory status
get_factory_status() {
    print_header "Factory Status"

    print_step "Getting factory status..."

    local status_response=$(curl -s "$FACTORY_URL/factory/status")

    if [ $? -eq 0 ]; then
        print_status "Factory Status:"
        echo "$status_response" | jq '.'
    else
        print_error "Failed to get factory status"
        return 1
    fi
}

# Function to create a development request
create_development_request() {
    print_header "Creating Development Request"

    print_step "Creating development request for: $DEMO_PROJECT_NAME"

    local request_data=$(cat <<EOF
{
    "name": "$DEMO_PROJECT_NAME",
    "description": "$DEMO_PROJECT_DESC",
    "requirements": [
        "User authentication and authorization with JWT tokens",
        "Project creation and management with team collaboration",
        "Task creation, assignment, and status tracking",
        "Real-time notifications for task updates",
        "File upload and attachment support",
        "Search and filtering capabilities",
        "Role-based access control",
        "API rate limiting and security"
    ],
    "target_language": "python",
    "target_framework": "fastapi",
    "target_architecture": "microservices",
    "cloud_provider": "aws",
    "priority": 8
}
EOF
)

    print_step "Submitting development request..."

    local response=$(curl -s -X POST "$FACTORY_URL/develop" \
        -H "Content-Type: application/json" \
        -d "$request_data")

    if [ $? -eq 0 ]; then
        local job_id=$(echo "$response" | jq -r '.job_id')
        local status=$(echo "$response" | jq -r '.status')

        if [ "$status" = "pending" ] && [ "$job_id" != "null" ]; then
            print_status "Development job started successfully!"
            print_status "Job ID: $job_id"
            print_status "Status: $status"
            echo "$response" | jq '.'

            # Store job ID for later use
            echo "$job_id" > /tmp/auto_forge_job_id
            return 0
        else
            print_error "Failed to start development job"
            echo "$response" | jq '.'
            return 1
        fi
    else
        print_error "Failed to submit development request"
        return 1
    fi
}

# Function to monitor job progress
monitor_job_progress() {
    print_header "Monitoring Job Progress"

    local job_id=$(cat /tmp/auto_forge_job_id 2>/dev/null)

    if [ -z "$job_id" ]; then
        print_error "No job ID found. Please start a development job first."
        return 1
    fi

    print_step "Monitoring job: $job_id"
    print_status "Progress updates (polling every 5 seconds)..."

    local max_attempts=60  # 5 minutes max
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        local status_response=$(curl -s "$FACTORY_URL/status/$job_id")

        if [ $? -eq 0 ]; then
            local status=$(echo "$status_response" | jq -r '.status')
            local phase=$(echo "$status_response" | jq -r '.current_phase')
            local progress=$(echo "$status_response" | jq -r '.overall_progress_percent')

            echo -e "${CYAN}[$attempt/$max_attempts]${NC} Status: $status | Phase: $phase | Progress: ${progress}%"

            if [ "$status" = "completed" ]; then
                print_status "Job completed successfully!"
                return 0
            elif [ "$status" = "failed" ]; then
                print_error "Job failed!"
                return 1
            fi
        else
            print_warning "Failed to get job status"
        fi

        sleep 5
        attempt=$((attempt + 1))
    done

    print_warning "Job monitoring timeout. Job may still be running."
    return 0
}

# Function to get job results
get_job_results() {
    print_header "Getting Job Results"

    local job_id=$(cat /tmp/auto_forge_job_id 2>/dev/null)

    if [ -z "$job_id" ]; then
        print_error "No job ID found. Please start a development job first."
        return 1
    fi

    print_step "Getting results for job: $job_id"

    local results_response=$(curl -s "$FACTORY_URL/artifacts/$job_id")

    if [ $? -eq 0 ]; then
        local status=$(echo "$results_response" | jq -r '.status')

        if [ "$status" = "completed" ]; then
            print_status "Job results retrieved successfully!"

            # Display summary
            echo -e "${GREEN}=== JOB SUMMARY ===${NC}"
            echo "$results_response" | jq -r '.summary'

            # Display metrics
            echo -e "${GREEN}=== QUALITY METRICS ===${NC}"
            echo "Quality Score: $(echo "$results_response" | jq -r '.quality_score')"
            echo "Security Score: $(echo "$results_response" | jq -r '.security_score')"
            echo "Performance Score: $(echo "$results_response" | jq -r '.performance_score')"
            echo "Total Tokens Used: $(echo "$results_response" | jq -r '.total_tokens_used')"
            echo "Total Cost: \$$(echo "$results_response" | jq -r '.total_cost')"
            echo "Execution Time: $(echo "$results_response" | jq -r '.execution_time_seconds')s"

            # Display artifacts
            echo -e "${GREEN}=== GENERATED ARTIFACTS ===${NC}"
            echo "$results_response" | jq -r '.artifacts[] | "• \(.name) (\(.type))"'

            # Display deployment instructions
            echo -e "${GREEN}=== DEPLOYMENT INSTRUCTIONS ===${NC}"
            echo "$results_response" | jq -r '.deployment_instructions'

            # Save full results to file
            echo "$results_response" | jq '.' > "/tmp/auto_forge_results_$job_id.json"
            print_status "Full results saved to: /tmp/auto_forge_results_$job_id.json"

            return 0
        else
            print_warning "Job is not yet completed. Status: $status"
            return 1
        fi
    else
        print_error "Failed to get job results"
        return 1
    fi
}

# Function to list all jobs
list_all_jobs() {
    print_header "Listing All Jobs"

    print_step "Getting list of all jobs..."

    local jobs_response=$(curl -s "$FACTORY_URL/jobs")

    if [ $? -eq 0 ]; then
        print_status "Jobs retrieved successfully!"

        local total_active=$(echo "$jobs_response" | jq -r '.total_active')
        local total_completed=$(echo "$jobs_response" | jq -r '.total_completed')

        echo -e "${GREEN}=== JOB SUMMARY ===${NC}"
        echo "Active Jobs: $total_active"
        echo "Completed Jobs: $total_completed"

        # Display active jobs
        local active_jobs=$(echo "$jobs_response" | jq -r '.active_jobs | length')
        if [ "$active_jobs" -gt 0 ]; then
            echo -e "${GREEN}=== ACTIVE JOBS ===${NC}"
            echo "$jobs_response" | jq -r '.active_jobs[] | "• \(.job_id[0:8])... - \(.project_name) (\(.status))"'
        fi

        # Display recent completed jobs
        local completed_jobs=$(echo "$jobs_response" | jq -r '.completed_jobs | length')
        if [ "$completed_jobs" -gt 0 ]; then
            echo -e "${GREEN}=== RECENT COMPLETED JOBS ===${NC}"
            echo "$jobs_response" | jq -r '.completed_jobs[0:3][] | "• \(.job_id[0:8])... - \(.project_name) (Quality: \(.quality_score))"'
        fi

        return 0
    else
        print_error "Failed to get jobs list"
        return 1
    fi
}

# Function to demonstrate WebSocket connection
demo_websocket() {
    print_header "WebSocket Demonstration"

    local job_id=$(cat /tmp/auto_forge_job_id 2>/dev/null)

    if [ -z "$job_id" ]; then
        print_error "No job ID found. Please start a development job first."
        return 1
    fi

    print_step "Connecting to WebSocket for job: $job_id"
    print_status "WebSocket URL: ws://localhost:8000/ws/$job_id"

    # Note: This is a simplified WebSocket demo
    # In a real scenario, you would use a WebSocket client
    print_warning "WebSocket connection requires a WebSocket client"
    print_status "You can use the Python demo script for WebSocket functionality"
}

# Function to demonstrate API documentation
show_api_docs() {
    print_header "API Documentation"

    print_step "Opening API documentation..."
    print_status "API documentation is available at: $FACTORY_URL/docs"
    print_status "OpenAPI schema is available at: $FACTORY_URL/openapi.json"

    # Try to open the docs in a browser
    if command -v xdg-open > /dev/null; then
        xdg-open "$FACTORY_URL/docs" 2>/dev/null &
    elif command -v open > /dev/null; then
        open "$FACTORY_URL/docs" 2>/dev/null &
    elif command -v start > /dev/null; then
        start "$FACTORY_URL/docs" 2>/dev/null &
    else
        print_status "Please open $FACTORY_URL/docs in your web browser"
    fi
}

# Function to demonstrate monitoring
show_monitoring() {
    print_header "Monitoring & Observability"

    print_step "Checking monitoring endpoints..."

    echo -e "${GREEN}=== MONITORING ENDPOINTS ===${NC}"
    echo "• Factory Health: $FACTORY_URL/health"
    echo "• Factory Status: $FACTORY_URL/factory/status"
    echo "• All Jobs: $FACTORY_URL/jobs"
    echo "• API Documentation: $FACTORY_URL/docs"

    # Check if monitoring stack is running
    if curl -s "http://localhost:9090" > /dev/null 2>&1; then
        print_status "Prometheus is running at: http://localhost:9090"
    fi

    if curl -s "http://localhost:3000" > /dev/null 2>&1; then
        print_status "Grafana is running at: http://localhost:3000 (admin/admin)"
    fi
}

# Function to clean up
cleanup() {
    print_header "Cleanup"

    print_step "Cleaning up temporary files..."
    rm -f /tmp/auto_forge_job_id
    rm -f /tmp/auto_forge_results_*.json

    print_status "Cleanup completed"
}

# Function to stop the factory
stop_factory() {
    print_header "Stopping Auto-Forge Factory"

    print_step "Stopping Docker Compose services..."

    cd auto_forge_factory
    docker-compose down

    print_status "Auto-Forge Factory stopped"
}

# Main demonstration function
main() {
    print_header "Auto-Forge Factory - Full End-to-End Demonstration"

    echo "This demonstration will show the complete autonomous software development pipeline:"
    echo "1. Starting the Auto-Forge Factory"
    echo "2. Checking factory health and status"
    echo "3. Creating a development request"
    echo "4. Monitoring job progress"
    echo "5. Retrieving job results and artifacts"
    echo "6. Exploring monitoring and observability"
    echo ""

    read -p "Press Enter to continue or Ctrl+C to exit..."

    # Run the demonstration
    start_factory
    check_factory_health
    get_factory_status
    create_development_request
    monitor_job_progress
    get_job_results
    list_all_jobs
    show_api_docs
    show_monitoring
    demo_websocket

    print_header "Demonstration Complete!"
    echo -e "${GREEN}✅ The Auto-Forge Factory has successfully demonstrated:${NC}"
    echo "• Autonomous software development from requirements to production-ready code"
    echo "• Multi-agent orchestration and coordination"
    echo "• Real-time progress monitoring and updates"
    echo "• Quality assurance and security validation"
    echo "• Complete artifact generation and deployment instructions"
    echo "• Comprehensive monitoring and observability"
    echo ""
    echo -e "${CYAN}Next steps:${NC}"
    echo "• Review the generated artifacts in /tmp/auto_forge_results_*.json"
    echo "• Explore the API documentation at $FACTORY_URL/docs"
    echo "• Check the monitoring dashboards"
    echo "• Try creating your own development requests"

    cleanup
}

# Function to show help
show_help() {
    echo "Auto-Forge Factory - Full End-to-End Demonstration"
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  --start-only      Start the factory only"
    echo "  --stop-only       Stop the factory only"
    echo "  --health-check    Check factory health only"
    echo "  --create-job      Create a development job only"
    echo "  --monitor-job     Monitor job progress only"
    echo "  --get-results     Get job results only"
    echo "  --list-jobs       List all jobs only"
    echo "  --api-docs        Show API documentation only"
    echo "  --monitoring      Show monitoring endpoints only"
    echo "  --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                # Run full demonstration"
    echo "  $0 --start-only   # Start factory only"
    echo "  $0 --health-check # Check health only"
}

# Parse command line arguments
case "${1:-}" in
    --start-only)
        start_factory
        ;;
    --stop-only)
        stop_factory
        ;;
    --health-check)
        check_factory_health
        ;;
    --create-job)
        create_development_request
        ;;
    --monitor-job)
        monitor_job_progress
        ;;
    --get-results)
        get_job_results
        ;;
    --list-jobs)
        list_all_jobs
        ;;
    --api-docs)
        show_api_docs
        ;;
    --monitoring)
        show_monitoring
        ;;
    --help)
        show_help
        ;;
    "")
        main
        ;;
    *)
        print_error "Unknown option: $1"
        show_help
        exit 1
        ;;
esac
