# CI/CD Integration Setup Guide

This guide provides step-by-step instructions for setting up comprehensive CI/CD pipeline tracking with the Unified Context System.

## Overview

The CI/CD integration system provides:
- **Real-time webhook processing** for immediate pipeline event tracking
- **Historical data synchronization** for comprehensive pipeline history
- **Cross-platform correlation** linking builds, deployments, code changes, and conversations
- **Performance analytics** for build success rates and deployment frequency
- **Scalable architecture** handling thousands of webhook events per minute

## Prerequisites

### System Requirements
- Python 3.9+
- PostgreSQL 13+ with TimescaleDB and pgvector extensions
- Redis (optional, for advanced caching)
- 4GB+ RAM for webhook processing
- SSL certificate for webhook endpoints

### Access Requirements
- Admin access to CI/CD platforms for webhook configuration
- API tokens for each platform
- Network access for webhook delivery

## Installation

### 1. Install Dependencies
```bash
# Core dependencies
pip install -r requirements.txt

# Additional CI/CD integration dependencies
pip install aiohttp[speedups] fastapi[all] tenacity structlog

# Platform-specific clients (optional)
pip install pygithub python-gitlab azure-devops jenkinsapi
```

### 2. Database Schema Setup
```bash
# Apply CI/CD schema extensions
psql -d unified_context -f schema_extensions_cicd.sql

# Verify extensions
psql -d unified_context -c "\dx"
```

### 3. Environment Configuration
```bash
# Copy configuration template
cp config/cicd_integration_config.yaml.template config/cicd_integration_config.yaml

# Set environment variables
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"
export GITHUB_WEBHOOK_SECRET="your_webhook_secret"
export GITLAB_TOKEN="glpat-xxxxxxxxxxxxxxxxxxxx"
export GITLAB_WEBHOOK_SECRET="your_gitlab_secret"
export DATABASE_URL="postgresql://user:pass@localhost:5432/unified_context"
```

## Platform Configuration

### GitHub Actions

#### 1. Generate Personal Access Token
1. Go to GitHub Settings > Developer settings > Personal access tokens
2. Generate new token with scopes:
   - `repo` - Repository access
   - `actions:read` - Actions workflow access
   - `metadata:read` - Repository metadata

#### 2. Configure Repository Webhooks
```bash
# Using GitHub CLI
gh api repos/OWNER/REPO/hooks \
  --method POST \
  --field name=web \
  --field active=true \
  --field events='["workflow_run","workflow_job","deployment","deployment_status","check_run"]' \
  --field config[url]="https://your-domain.com/webhooks/github" \
  --field config[content_type]="application/json" \
  --field config[secret]="your_webhook_secret"
```

#### 3. Organization-wide Configuration (Optional)
```bash
# For organization-wide webhooks
gh api orgs/ORG/hooks \
  --method POST \
  --field name=web \
  --field active=true \
  --field events='["workflow_run","workflow_job","deployment","deployment_status"]' \
  --field config[url]="https://your-domain.com/webhooks/github" \
  --field config[content_type]="application/json" \
  --field config[secret]="your_webhook_secret"
```

### GitLab CI/CD

#### 1. Generate Project Access Token
1. Go to Project Settings > Access Tokens
2. Create token with scopes:
   - `api` - Full API access
   - `read_api` - Read API access
   - `read_repository` - Repository access

#### 2. Configure Project Webhooks
```bash
# Using GitLab API
curl -X POST "https://gitlab.com/api/v4/projects/PROJECT_ID/hooks" \
  --header "PRIVATE-TOKEN: your_token" \
  --header "Content-Type: application/json" \
  --data '{
    "url": "https://your-domain.com/webhooks/gitlab",
    "pipeline_events": true,
    "job_events": true,
    "deployment_events": true,
    "releases_events": true,
    "push_events": true,
    "merge_requests_events": true,
    "token": "your_webhook_secret"
  }'
```

#### 3. Group-level Configuration (Optional)
```bash
# For group-wide webhooks
curl -X POST "https://gitlab.com/api/v4/groups/GROUP_ID/hooks" \
  --header "PRIVATE-TOKEN: your_token" \
  --header "Content-Type: application/json" \
  --data '{
    "url": "https://your-domain.com/webhooks/gitlab",
    "pipeline_events": true,
    "job_events": true,
    "deployment_events": true
  }'
```

### Jenkins

#### 1. Install Required Plugins
- Notification Plugin
- Generic Webhook Trigger Plugin
- Pipeline: Stage View Plugin
- Build Timestamp Plugin

#### 2. Configure Global Webhook Notification
```groovy
// In Jenkins global configuration
@Library('your-shared-library') _

pipeline {
    agent any

    options {
        buildDiscarder(logRotator(numToKeepStr: '50'))
        timestamps()
    }

    post {
        always {
            script {
                def webhookUrl = "https://your-domain.com/webhooks/jenkins"
                def payload = [
                    job_name: env.JOB_NAME,
                    build_number: env.BUILD_NUMBER,
                    build_url: env.BUILD_URL,
                    build_status: currentBuild.currentResult,
                    commit_sha: env.GIT_COMMIT,
                    branch: env.GIT_BRANCH,
                    duration: currentBuild.duration,
                    timestamp: new Date().getTime()
                ]

                httpRequest(
                    httpMode: 'POST',
                    url: webhookUrl,
                    contentType: 'APPLICATION_JSON',
                    requestBody: writeJSON(returnText: true, json: payload),
                    validResponseCodes: '200:299'
                )
            }
        }
    }
}
```

#### 3. Shared Library for Webhook Notifications
```groovy
// vars/notifyWebhook.groovy
def call(Map config) {
    def webhookUrl = config.url ?: "https://your-domain.com/webhooks/jenkins"
    def payload = [
        job_name: env.JOB_NAME,
        build_number: env.BUILD_NUMBER,
        build_status: config.status ?: currentBuild.currentResult,
        commit_sha: env.GIT_COMMIT,
        branch: env.GIT_BRANCH,
        duration: currentBuild.duration,
        timestamp: new Date().getTime(),
        stage: config.stage,
        custom_data: config.data ?: [:]
    ]

    httpRequest(
        httpMode: 'POST',
        url: webhookUrl,
        contentType: 'APPLICATION_JSON',
        requestBody: writeJSON(returnText: true, json: payload),
        validResponseCodes: '200:299'
    )
}
```

### Azure DevOps

#### 1. Create Personal Access Token
1. Go to User Settings > Personal Access Tokens
2. Create token with scopes:
   - `Build (read)` - Build information access
   - `Release (read)` - Release information access
   - `Project and team (read)` - Project access

#### 2. Configure Service Hooks
```powershell
# Using Azure DevOps CLI
az devops service-endpoint create \
  --name "Unified Context Webhook" \
  --service-endpoint-type "webhook" \
  --url "https://your-domain.com/webhooks/azure" \
  --organization "https://dev.azure.com/yourorg" \
  --project "YourProject"

# Create service hook subscription
az devops service-hook create \
  --consumer-id "webHooks" \
  --consumer-action-id "httpRequest" \
  --event-type "build.complete" \
  --publisher-id "tfs" \
  --resource-version "1.0" \
  --url "https://your-domain.com/webhooks/azure"
```

#### 3. PowerShell Script for Bulk Configuration
```powershell
# Configure multiple projects
$projects = @("Project1", "Project2", "Project3")
$webhookUrl = "https://your-domain.com/webhooks/azure"

foreach ($project in $projects) {
    # Build completion hook
    az devops service-hook create `
      --consumer-id "webHooks" `
      --consumer-action-id "httpRequest" `
      --event-type "build.complete" `
      --publisher-id "tfs" `
      --project $project `
      --url $webhookUrl

    # Release deployment hook
    az devops service-hook create `
      --consumer-id "webHooks" `
      --consumer-action-id "httpRequest" `
      --event-type "ms.vss-release.deployment-completed-event" `
      --publisher-id "rm" `
      --project $project `
      --url $webhookUrl
}
```

## Server Configuration

### 1. FastAPI Server Setup
```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from project_context.server.webhook_endpoints import webhook_router, set_webhook_processor
from project_context.ingestion.webhook_processor import WebhookProcessor
from project_context.ingestion.adapters.cicd_adapter import GitHubActionsAdapter, CICDAdapterConfig

app = FastAPI(title="Unified Context CI/CD Integration")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://github.com", "https://gitlab.com"],
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Initialize webhook processor
async def startup():
    # Initialize database connection
    database = IngestionDatabase(connection_pool)

    # Create webhook processor
    processor = WebhookProcessor(database, num_workers=10)

    # Register adapters
    github_config = CICDAdapterConfig(
        platform=CICDPlatform.GITHUB_ACTIONS,
        api_token=os.getenv("GITHUB_TOKEN"),
        webhook_secret=os.getenv("GITHUB_WEBHOOK_SECRET"),
        repositories=["your-org/repo1", "your-org/repo2"]
    )
    github_adapter = GitHubActionsAdapter(github_config)
    processor.register_adapter(CICDPlatform.GITHUB_ACTIONS, github_adapter)

    # Start processor
    await processor.start()

    # Set global processor
    set_webhook_processor(processor)

app.add_event_handler("startup", startup)
app.include_router(webhook_router)
```

### 2. Production Deployment with Docker
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8000/webhooks/health || exit 1

# Run application
CMD ["uvicorn", "src.project_context.server.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  webhook-processor:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/unified_context
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - GITHUB_WEBHOOK_SECRET=${GITHUB_WEBHOOK_SECRET}
      - GITLAB_TOKEN=${GITLAB_TOKEN}
    depends_on:
      - db
      - redis
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - webhook-processor
    restart: unless-stopped

  db:
    image: timescale/timescaledb:latest-pg15
    environment:
      POSTGRES_DB: unified_context
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:alpine
    restart: unless-stopped

volumes:
  postgres_data:
```

### 3. Nginx Configuration for SSL
```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream webhook_backend {
        server webhook-processor:8000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=webhook_limit:10m rate=100r/m;

    server {
        listen 443 ssl;
        server_name your-domain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";

        location /webhooks/ {
            limit_req zone=webhook_limit burst=200 nodelay;

            proxy_pass http://webhook_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # Webhook-specific settings
            proxy_read_timeout 30s;
            proxy_connect_timeout 10s;
            client_max_body_size 10M;
        }

        location /health {
            proxy_pass http://webhook_backend/webhooks/health;
            access_log off;
        }
    }

    # Redirect HTTP to HTTPS
    server {
        listen 80;
        server_name your-domain.com;
        return 301 https://$server_name$request_uri;
    }
}
```

## Monitoring and Maintenance

### 1. Health Check Endpoints
```bash
# Basic health check
curl https://your-domain.com/webhooks/health

# Detailed statistics
curl https://your-domain.com/webhooks/stats

# Platform-specific validation
curl -X POST https://your-domain.com/webhooks/validate/github \
  -H "Content-Type: application/json" \
  -d '{"repository": {"full_name": "test/repo"}}'
```

### 2. Monitoring Dashboard Setup
```python
# monitoring.py
import asyncio
from datetime import datetime, timedelta

async def monitor_webhook_processor():
    """Monitor webhook processor health and performance."""
    while True:
        try:
            # Get health status
            health = await webhook_processor.get_health_status()

            # Check critical metrics
            if health["queue_size"] > 1000:
                await send_alert("High webhook queue size", health)

            if health["workers_active"] < health["workers_total"] * 0.5:
                await send_alert("Low worker availability", health)

            # Performance metrics
            stats = await webhook_processor.get_processing_stats(hours=1)
            if stats["current_metrics"]["success_rate"] < 0.95:
                await send_alert("Low webhook success rate", stats)

        except Exception as e:
            await send_alert(f"Monitoring error: {e}", {})

        await asyncio.sleep(60)  # Check every minute
```

### 3. Log Analysis
```bash
# View webhook processing logs
docker-compose logs -f webhook-processor | grep "webhook"

# Search for specific platform errors
docker-compose logs webhook-processor 2>/dev/null | grep -E "(github|gitlab) webhook.*error"

# Monitor processing times
docker-compose logs webhook-processor 2>/dev/null | grep "processing_time_ms" | tail -20
```

### 4. Database Maintenance
```sql
-- Monitor CI/CD data growth
SELECT
    source_type,
    entity_type,
    COUNT(*) as item_count,
    MIN(timestamp) as earliest,
    MAX(timestamp) as latest
FROM context_items
WHERE source_type = 'cicd'
GROUP BY source_type, entity_type;

-- Cleanup old CI/CD data (if needed)
DELETE FROM context_items
WHERE source_type = 'cicd'
  AND timestamp < NOW() - INTERVAL '1 year';

-- Vacuum and analyze
VACUUM ANALYZE context_items;
```

## Troubleshooting

### Common Issues

#### 1. Webhook Delivery Failures
```bash
# Check webhook delivery logs from platform
# GitHub: Repository Settings > Webhooks > Recent Deliveries
# GitLab: Project Settings > Webhooks > Recent events

# Verify endpoint accessibility
curl -X POST https://your-domain.com/webhooks/test \
  -H "Content-Type: application/json" \
  -d '{"test": true}' \
  -H "X-GitHub-Event: ping"
```

#### 2. Authentication Issues
```bash
# Test API tokens
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user

# Test webhook signatures
# Use the webhook validation endpoint to debug signature issues
```

#### 3. High Memory Usage
```bash
# Monitor memory usage
docker stats webhook-processor

# Check for memory leaks in logs
docker-compose logs webhook-processor | grep -i memory
```

#### 4. Processing Delays
```sql
-- Check for slow queries
SELECT query, mean_time, calls
FROM pg_stat_statements
WHERE query LIKE '%context_items%'
ORDER BY mean_time DESC;

-- Monitor queue depth
SELECT COUNT(*) FROM webhook_events WHERE status = 'pending';
```

### Performance Tuning

#### 1. Database Optimization
```sql
-- Create additional indexes for common queries
CREATE INDEX CONCURRENTLY idx_context_items_cicd_platform
ON context_items(source_type, (source_data->>'platform'))
WHERE source_type = 'cicd';

CREATE INDEX CONCURRENTLY idx_context_items_cicd_status
ON context_items((metrics->>'status'), timestamp)
WHERE source_type = 'cicd';
```

#### 2. Application Tuning
```python
# Increase worker pool size for high volume
webhook_processor = WebhookProcessor(
    database=database,
    num_workers=20,  # Increase workers
    queue_maxsize=20000,  # Increase queue size
    processing_timeout=60  # Increase timeout for complex correlations
)
```

This comprehensive setup guide provides everything needed to implement robust CI/CD pipeline tracking with the Unified Context System.
