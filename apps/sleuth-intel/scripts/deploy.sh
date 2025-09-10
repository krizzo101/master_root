#!/bin/bash

# Sleuth Intel Deployment Script
# Usage: ./deploy.sh [environment] [version]

set -euo pipefail

# Configuration
ENVIRONMENT=${1:-staging}
VERSION=${2:-latest}
NAMESPACE="sleuth-intel"
REGISTRY="ghcr.io/your-org"
IMAGE_NAME="sleuth-intel"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check for required commands
    for cmd in kubectl docker helm; do
        if ! command -v $cmd &> /dev/null; then
            log_error "$cmd is not installed"
            exit 1
        fi
    done

    # Check kubectl connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi

    log_info "Prerequisites check passed"
}

build_image() {
    log_info "Building Docker image..."

    docker build -t ${REGISTRY}/${IMAGE_NAME}:${VERSION} .

    if [ $? -eq 0 ]; then
        log_info "Docker image built successfully"
    else
        log_error "Failed to build Docker image"
        exit 1
    fi
}

push_image() {
    log_info "Pushing Docker image to registry..."

    docker push ${REGISTRY}/${IMAGE_NAME}:${VERSION}

    if [ $? -eq 0 ]; then
        log_info "Docker image pushed successfully"
    else
        log_error "Failed to push Docker image"
        exit 1
    fi
}

deploy_kubernetes() {
    log_info "Deploying to Kubernetes (${ENVIRONMENT})..."

    # Create namespace if it doesn't exist
    kubectl create namespace ${NAMESPACE}-${ENVIRONMENT} --dry-run=client -o yaml | kubectl apply -f -

    # Apply configurations
    kubectl apply -f k8s/configmap.yaml -n ${NAMESPACE}-${ENVIRONMENT}
    kubectl apply -f k8s/secrets.yaml -n ${NAMESPACE}-${ENVIRONMENT}

    # Update deployment with new image
    kubectl set image deployment/${IMAGE_NAME} \
        ${IMAGE_NAME}=${REGISTRY}/${IMAGE_NAME}:${VERSION} \
        -n ${NAMESPACE}-${ENVIRONMENT}

    # Apply other resources
    kubectl apply -f k8s/service.yaml -n ${NAMESPACE}-${ENVIRONMENT}
    kubectl apply -f k8s/hpa.yaml -n ${NAMESPACE}-${ENVIRONMENT}

    log_info "Kubernetes deployment initiated"
}

wait_for_rollout() {
    log_info "Waiting for rollout to complete..."

    kubectl rollout status deployment/${IMAGE_NAME} \
        -n ${NAMESPACE}-${ENVIRONMENT} \
        --timeout=600s

    if [ $? -eq 0 ]; then
        log_info "Rollout completed successfully"
    else
        log_error "Rollout failed or timed out"
        exit 1
    fi
}

run_health_checks() {
    log_info "Running health checks..."

    # Get service endpoint
    SERVICE_IP=$(kubectl get svc ${IMAGE_NAME} -n ${NAMESPACE}-${ENVIRONMENT} -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

    if [ -z "$SERVICE_IP" ]; then
        log_warn "LoadBalancer IP not available, using port-forward"
        kubectl port-forward svc/${IMAGE_NAME} 8080:80 -n ${NAMESPACE}-${ENVIRONMENT} &
        PF_PID=$!
        sleep 5
        SERVICE_IP="localhost:8080"
    fi

    # Check health endpoint
    if curl -f http://${SERVICE_IP}/health &> /dev/null; then
        log_info "Health check passed"
    else
        log_error "Health check failed"
        [ ! -z "${PF_PID}" ] && kill ${PF_PID}
        exit 1
    fi

    [ ! -z "${PF_PID}" ] && kill ${PF_PID}
}

rollback() {
    log_error "Deployment failed, rolling back..."

    kubectl rollout undo deployment/${IMAGE_NAME} \
        -n ${NAMESPACE}-${ENVIRONMENT}

    kubectl rollout status deployment/${IMAGE_NAME} \
        -n ${NAMESPACE}-${ENVIRONMENT} \
        --timeout=300s

    log_info "Rollback completed"
}

# Main execution
main() {
    log_info "Starting deployment process..."
    log_info "Environment: ${ENVIRONMENT}"
    log_info "Version: ${VERSION}"

    check_prerequisites

    if [ "${ENVIRONMENT}" == "production" ]; then
        log_warn "Deploying to PRODUCTION environment"
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            log_info "Deployment cancelled"
            exit 0
        fi
    fi

    # Build and push image
    build_image
    push_image

    # Deploy to Kubernetes
    deploy_kubernetes

    # Wait for rollout
    wait_for_rollout || rollback

    # Run health checks
    run_health_checks || rollback

    log_info "Deployment completed successfully!"

    # Show deployment info
    kubectl get pods -n ${NAMESPACE}-${ENVIRONMENT}
    kubectl get svc -n ${NAMESPACE}-${ENVIRONMENT}
}

# Trap errors
trap 'log_error "Deployment failed on line $LINENO"' ERR

# Run main function
main
