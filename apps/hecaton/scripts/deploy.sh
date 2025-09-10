#!/bin/bash
# HECATON Deployment Script
# Deploy to staging or production environments

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-staging}
DEPLOYMENT_ID=$(date +%Y%m%d-%H%M%S)
ROLLBACK_LIMIT=3

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

    # Check Python version
    if ! python3 --version | grep -E "3\.(9|10|11)" > /dev/null; then
        log_error "Python 3.9+ required"
        exit 1
    fi

    # Check required tools
    for tool in git docker kubectl; do
        if ! command -v $tool &> /dev/null; then
            log_error "$tool is required but not installed"
            exit 1
        fi
    done

    # Check environment configuration
    if [[ ! -f "config/${ENVIRONMENT}/config.yaml" ]]; then
        log_error "Configuration for ${ENVIRONMENT} not found"
        exit 1
    fi

    log_info "Prerequisites check passed"
}

run_tests() {
    log_info "Running deployment tests..."

    # Run critical tests
    python3 -m pytest tests/deployment/ -v --timeout=60

    if [[ $? -ne 0 ]]; then
        log_error "Deployment tests failed"
        exit 1
    fi

    log_info "Tests passed"
}

backup_current_state() {
    log_info "Creating backup of current state..."

    BACKUP_DIR="backups/${DEPLOYMENT_ID}"
    mkdir -p "$BACKUP_DIR"

    # Backup current deployment manifests
    if [[ "$ENVIRONMENT" == "production" ]]; then
        kubectl get all -n hecaton -o yaml > "$BACKUP_DIR/current-state.yaml"
        kubectl get configmap -n hecaton -o yaml > "$BACKUP_DIR/configmaps.yaml"
        kubectl get secret -n hecaton -o yaml > "$BACKUP_DIR/secrets.yaml"
    fi

    # Backup database (if applicable)
    if [[ -n "${DATABASE_URL:-}" ]]; then
        pg_dump "$DATABASE_URL" | gzip > "$BACKUP_DIR/database.sql.gz"
    fi

    log_info "Backup created at $BACKUP_DIR"
}

deploy_infrastructure() {
    log_info "Deploying infrastructure components..."

    if [[ "$ENVIRONMENT" == "production" ]]; then
        # Deploy with Kubernetes
        kubectl apply -f k8s/namespace.yaml
        kubectl apply -f k8s/configmap.yaml
        kubectl apply -f k8s/secrets.yaml
        kubectl apply -f k8s/deployments/
        kubectl apply -f k8s/services/
        kubectl apply -f k8s/ingress.yaml

        # Wait for rollout
        kubectl rollout status deployment/hecaton-orchestrator -n hecaton --timeout=300s
        kubectl rollout status deployment/hecaton-agents -n hecaton --timeout=300s
    else
        # Deploy with Docker Compose for staging
        docker-compose -f docker-compose.${ENVIRONMENT}.yml up -d --build
    fi

    log_info "Infrastructure deployed"
}

deploy_application() {
    log_info "Deploying application..."

    # Build Docker image
    IMAGE_TAG="hecaton:${DEPLOYMENT_ID}"
    docker build -t "$IMAGE_TAG" .

    # Push to registry
    if [[ "$ENVIRONMENT" == "production" ]]; then
        docker tag "$IMAGE_TAG" "registry.hecaton.io/$IMAGE_TAG"
        docker push "registry.hecaton.io/$IMAGE_TAG"

        # Update Kubernetes deployment
        kubectl set image deployment/hecaton-orchestrator \
            hecaton="registry.hecaton.io/$IMAGE_TAG" \
            -n hecaton
    else
        # Local deployment for staging
        docker tag "$IMAGE_TAG" "hecaton:${ENVIRONMENT}"
    fi

    log_info "Application deployed"
}

run_health_checks() {
    log_info "Running health checks..."

    MAX_RETRIES=30
    RETRY_COUNT=0

    while [[ $RETRY_COUNT -lt $MAX_RETRIES ]]; do
        if curl -f "http://hecaton.${ENVIRONMENT}.local/health" &> /dev/null; then
            log_info "Health check passed"
            return 0
        fi

        RETRY_COUNT=$((RETRY_COUNT + 1))
        sleep 10
    done

    log_error "Health checks failed after $MAX_RETRIES attempts"
    return 1
}

run_smoke_tests() {
    log_info "Running smoke tests..."

    # Run basic functionality tests
    python3 scripts/smoke_tests.py --environment "$ENVIRONMENT"

    if [[ $? -ne 0 ]]; then
        log_error "Smoke tests failed"
        return 1
    fi

    log_info "Smoke tests passed"
}

update_monitoring() {
    log_info "Updating monitoring configuration..."

    # Deploy Prometheus configuration
    if [[ "$ENVIRONMENT" == "production" ]]; then
        kubectl apply -f monitoring/prometheus-config.yaml -n monitoring
        kubectl apply -f monitoring/grafana-dashboards.yaml -n monitoring
    fi

    # Register deployment event
    curl -X POST "http://metrics.hecaton.io/api/events" \
        -H "Content-Type: application/json" \
        -d "{
            \"event\": \"deployment\",
            \"environment\": \"$ENVIRONMENT\",
            \"deployment_id\": \"$DEPLOYMENT_ID\",
            \"timestamp\": \"$(date -Iseconds)\"
        }"

    log_info "Monitoring updated"
}

rollback() {
    log_error "Deployment failed, initiating rollback..."

    if [[ "$ENVIRONMENT" == "production" ]]; then
        # Kubernetes rollback
        kubectl rollout undo deployment/hecaton-orchestrator -n hecaton
        kubectl rollout undo deployment/hecaton-agents -n hecaton

        # Wait for rollback
        kubectl rollout status deployment/hecaton-orchestrator -n hecaton --timeout=300s
    else
        # Docker Compose rollback
        docker-compose -f docker-compose.${ENVIRONMENT}.yml down
        docker-compose -f docker-compose.${ENVIRONMENT}.yml.backup up -d
    fi

    log_warn "Rollback completed"
}

main() {
    log_info "Starting deployment to ${ENVIRONMENT}"
    log_info "Deployment ID: ${DEPLOYMENT_ID}"

    # Validate environment
    if [[ "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "production" ]]; then
        log_error "Invalid environment: $ENVIRONMENT (must be staging or production)"
        exit 1
    fi

    # Production confirmation
    if [[ "$ENVIRONMENT" == "production" ]]; then
        log_warn "You are about to deploy to PRODUCTION!"
        read -p "Type 'DEPLOY' to confirm: " confirmation
        if [[ "$confirmation" != "DEPLOY" ]]; then
            log_info "Deployment cancelled"
            exit 0
        fi
    fi

    # Run deployment steps
    check_prerequisites
    run_tests
    backup_current_state

    # Deploy with error handling
    if deploy_infrastructure && deploy_application; then
        if run_health_checks && run_smoke_tests; then
            update_monitoring
            log_info "Deployment successful!"

            # Store successful deployment
            echo "$DEPLOYMENT_ID" >> deployments/.successful
        else
            rollback
            exit 1
        fi
    else
        rollback
        exit 1
    fi

    log_info "Deployment completed: ${DEPLOYMENT_ID}"
}

# Run main function
main "$@"
