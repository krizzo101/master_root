# Sleuth Intel Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Docker Deployment](#docker-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Configuration Management](#configuration-management)
6. [Database Setup](#database-setup)
7. [Monitoring Setup](#monitoring-setup)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- Docker 20.10+ and Docker Compose 2.0+
- Kubernetes 1.24+ (for K8s deployment)
- PostgreSQL 15+
- Redis 7+
- Python 3.10+ (for local development)

### Required Services
- PostgreSQL database
- Redis cache
- Container registry (Docker Hub, ECR, GCR, etc.)
- Kubernetes cluster (EKS, GKE, AKS, or self-managed)

## Environment Setup

### 1. Clone Repository
```bash
git clone https://github.com/your-org/sleuth-intel.git
cd sleuth-intel
```

### 2. Configure Environment Variables
```bash
cp config/.env.production.example .env.production
# Edit .env.production with your values
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
pip install -r requirements-prod.txt
```

## Docker Deployment

### Build Image
```bash
docker build -t sleuth-intel:latest .
```

### Run with Docker Compose
```bash
docker-compose -f docker-compose.yml up -d
```

### Verify Deployment
```bash
# Check health
curl http://localhost:8000/health

# View logs
docker-compose logs -f app
```

## Kubernetes Deployment

### 1. Create Namespace
```bash
kubectl apply -f k8s/namespace.yaml
```

### 2. Configure Secrets
```bash
# Edit k8s/secrets.yaml with your base64-encoded values
kubectl apply -f k8s/secrets.yaml
```

### 3. Deploy Application
```bash
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
```

### 4. Setup Ingress (Optional)
```bash
kubectl apply -f k8s/ingress.yaml
```

### 5. Verify Deployment
```bash
# Check pods
kubectl get pods -n sleuth-intel

# Check services
kubectl get svc -n sleuth-intel

# View logs
kubectl logs -f deployment/sleuth-intel -n sleuth-intel
```

## Configuration Management

### Environment Variables
Key configuration variables:

| Variable | Description | Required |
|----------|-------------|----------|
| SECRET_KEY | Application secret key | Yes |
| ENFORMION_API_KEY | Enformion API credentials | Yes |
| DATABASE_URL | PostgreSQL connection string | Yes |
| REDIS_URL | Redis connection string | Yes |
| SENTRY_DSN | Error tracking (optional) | No |

### Production Settings
Edit `config/production.py` for:
- API rate limiting
- Cache configuration
- Worker settings
- Security headers

## Database Setup

### 1. Create Database
```sql
CREATE DATABASE sleuth_intel;
CREATE USER sleuth_user WITH ENCRYPTED PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE sleuth_intel TO sleuth_user;
```

### 2. Run Migrations
```bash
alembic upgrade head
```

### 3. Create Indexes
```sql
-- Performance indexes
CREATE INDEX idx_searches_user_id ON searches(user_id);
CREATE INDEX idx_searches_created_at ON searches(created_at);
CREATE INDEX idx_results_search_id ON results(search_id);
```

## Monitoring Setup

### Prometheus
```bash
# Deploy Prometheus
kubectl apply -f monitoring/prometheus-deployment.yaml

# Apply alerts
kubectl create configmap prometheus-alerts --from-file=monitoring/alerts/
```

### Grafana
```bash
# Import dashboard
curl -X POST http://grafana:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @monitoring/grafana-dashboard.json
```

### Health Checks
- Health endpoint: `/health`
- Ready endpoint: `/ready`
- Metrics endpoint: `:9090/metrics`

## Troubleshooting

### Common Issues

#### Pod CrashLoopBackOff
```bash
# Check logs
kubectl logs pod-name -n sleuth-intel --previous

# Check events
kubectl describe pod pod-name -n sleuth-intel
```

#### Database Connection Issues
```bash
# Test connection
psql $DATABASE_URL -c "SELECT 1"

# Check network policies
kubectl get networkpolicies -n sleuth-intel
```

#### High Memory Usage
```bash
# Check memory limits
kubectl top pods -n sleuth-intel

# Adjust limits in deployment.yaml
```

### Debug Mode
Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
export DEBUG=true
```

### Support
For issues, contact:
- Email: support@sleuth-intel.com
- Slack: #sleuth-intel-ops
- On-call: Use PagerDuty
