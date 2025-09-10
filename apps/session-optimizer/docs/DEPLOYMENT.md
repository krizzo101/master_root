# Session Optimizer - Deployment Guide

Comprehensive deployment, operations, and maintenance guide for the GPT-5 Session Optimizer system.

## Table of Contents

1. [System Overview](#system-overview)
2. [System Requirements](#system-requirements)
3. [Environment Configuration](#environment-configuration)
4. [Local Development Setup](#local-development-setup)
5. [Docker Deployment](#docker-deployment)
6. [Cloud Platform Deployment](#cloud-platform-deployment)
7. [CI/CD Integration](#cicd-integration)
8. [Database Setup](#database-setup)
9. [Monitoring & Health Checks](#monitoring--health-checks)
10. [Security Configuration](#security-configuration)
11. [Backup & Recovery](#backup--recovery)
12. [Scaling Considerations](#scaling-considerations)
13. [Maintenance Tasks](#maintenance-tasks)
14. [Troubleshooting](#troubleshooting)
15. [Rollback Procedures](#rollback-procedures)

## System Overview

The Session Optimizer is a Python-based system that optimizes Claude Code sessions for GPT-5, achieving 2.23x-3.14x compression ratios with 60-80% cost savings potential. The system processes large session files (.jsonl format) through intelligent chunking, format conversion, and structured prompt generation.

### Architecture Components

- **Core Engine**: GPT5PayloadSystem with integrated components
- **Token Analysis**: tiktoken-based token counting and cost estimation
- **Chunking Engine**: Three strategies (conversation, tool_usage, adaptive)
- **Payload Generator**: GPT-5 optimized message formatting
- **Format Adapter**: Claude .jsonl file processing
- **Size Analyzer**: Cost breakdown and optimization analysis

## System Requirements

### Minimum Requirements

- **OS**: Linux (Ubuntu 18.04+), macOS 10.15+, Windows 10+ (WSL2 recommended)
- **Python**: 3.9+
- **RAM**: 2GB minimum, 8GB recommended for large sessions
- **Storage**: 10GB minimum, 100GB+ for production workloads
- **CPU**: 2 cores minimum, 4+ cores recommended for parallel processing

### Recommended Production Requirements

- **OS**: Linux (Ubuntu 20.04+ LTS)
- **Python**: 3.11+
- **RAM**: 16GB+ for large batch processing
- **Storage**: 500GB+ SSD with high IOPS
- **CPU**: 8+ cores for optimal parallel processing
- **Network**: High-bandwidth connection for large session transfers

### Python Dependencies

```txt
# Core Dependencies
tiktoken>=0.5.0         # GPT-5 token counting
asyncio                 # Built-in async support
concurrent.futures      # Built-in parallel processing
json                    # Built-in JSON support
pathlib                 # Built-in path handling

# Optional Dependencies (for enhanced features)
psutil                  # System monitoring
redis                   # Caching layer
prometheus_client       # Metrics export
```

## Environment Configuration

### Environment Variables

Create a `.env` file in the application root:

```bash
# Application Configuration
SESSION_OPTIMIZER_ENV=production
LOG_LEVEL=INFO
DEBUG_MODE=false

# Performance Configuration
MAX_WORKERS=8
MEMORY_LIMIT_MB=4096
ENABLE_PARALLEL_PROCESSING=true
ENABLE_STREAMING=true

# Token Analysis Configuration
GPT5_MODEL=gpt-4o
INPUT_COST_PER_1K=0.025
OUTPUT_COST_PER_1K=0.05

# Chunking Configuration
MAX_CHUNK_TOKENS=25000
CHUNK_OVERLAP_TOKENS=1000
DEFAULT_CHUNKING_STRATEGY=adaptive

# Payload Configuration
MAX_CONTEXT_TOKENS=15000
PROMPT_STYLE=conversational
OPTIMIZATION_LEVEL=balanced

# Format Adapter Configuration
CONSOLIDATE_TOOL_SEQUENCES=true
MAX_CONTENT_LENGTH=50000

# Storage Configuration
INPUT_PATH=/data/sessions/input
OUTPUT_PATH=/data/sessions/output
TEMP_PATH=/tmp/session-optimizer

# Optional: Redis Configuration (for caching)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Optional: Metrics Configuration
METRICS_ENABLED=true
METRICS_PORT=9090
HEALTH_CHECK_PORT=8080
```

### Configuration File

Create `config/production.json`:

```json
{
  "system": {
    "environment": "production",
    "log_level": "INFO",
    "enable_metrics": true,
    "health_check_interval": 30
  },
  "optimization": {
    "gpt5_model": "gpt-4o",
    "input_cost_per_1k": 0.025,
    "output_cost_per_1k": 0.05,
    "max_chunk_tokens": 25000,
    "chunk_overlap_tokens": 1000,
    "default_chunking_strategy": "adaptive",
    "max_context_tokens": 15000,
    "optimization_level": "balanced",
    "consolidate_tool_sequences": true,
    "max_content_length": 50000
  },
  "performance": {
    "enable_streaming": true,
    "enable_parallel_processing": true,
    "max_workers": 8,
    "memory_limit_mb": 4096,
    "batch_size": 10
  },
  "storage": {
    "input_path": "/data/sessions/input",
    "output_path": "/data/sessions/output",
    "temp_path": "/tmp/session-optimizer",
    "cleanup_temp_files": true,
    "retention_days": 30
  },
  "monitoring": {
    "metrics_enabled": true,
    "metrics_port": 9090,
    "health_check_port": 8080,
    "log_file": "/var/log/session-optimizer/app.log",
    "error_log_file": "/var/log/session-optimizer/error.log"
  }
}
```

## Local Development Setup

### 1. Environment Preparation

```bash
# Clone or extract the session-optimizer application
cd /path/to/session-optimizer

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or venv\Scripts\activate  # Windows

# Upgrade pip
pip install --upgrade pip
```

### 2. Install Dependencies

```bash
# Install core dependency
pip install tiktoken

# Optional: Install development dependencies
pip install pytest pytest-asyncio black flake8 mypy

# Verify installation
python gpt5_cli.py status
```

### 3. Directory Setup

```bash
# Create required directories
mkdir -p data/sessions/{input,output}
mkdir -p logs
mkdir -p temp
mkdir -p config

# Set permissions
chmod 755 data/sessions/{input,output}
chmod 755 logs temp

# Copy sample configuration
cp config/development.json.example config/development.json
```

### 4. Verification

```bash
# Run system check
python gpt5_cli.py status --detailed

# Run basic tests
python gpt5_cli.py test --quick

# Test with sample data (if available)
python gpt5_cli.py optimize test_sessions/sample.jsonl --output data/sessions/output/
```

## Docker Deployment

### Dockerfile

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Create data directories
RUN mkdir -p /app/data/sessions/{input,output} && \
    mkdir -p /app/logs && \
    mkdir -p /app/temp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD python gpt5_cli.py status || exit 1

# Expose ports
EXPOSE 8080 9090

# Default command
CMD ["python", "gpt5_cli.py", "server", "--host", "0.0.0.0", "--port", "8080"]
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  session-optimizer:
    build: .
    container_name: session-optimizer
    restart: unless-stopped
    environment:
      - SESSION_OPTIMIZER_ENV=production
      - MAX_WORKERS=4
      - MEMORY_LIMIT_MB=2048
      - REDIS_HOST=redis
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./config:/app/config:ro
    ports:
      - "8080:8080"  # Health check/API
      - "9090:9090"  # Metrics
    depends_on:
      - redis
    networks:
      - session-optimizer-network

  redis:
    image: redis:7-alpine
    container_name: session-optimizer-redis
    restart: unless-stopped
    volumes:
      - redis_data:/data
    networks:
      - session-optimizer-network

  prometheus:
    image: prom/prometheus:latest
    container_name: session-optimizer-prometheus
    restart: unless-stopped
    ports:
      - "9091:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    networks:
      - session-optimizer-network

volumes:
  redis_data:
  prometheus_data:

networks:
  session-optimizer-network:
    driver: bridge
```

### Build and Deploy

```bash
# Build image
docker build -t session-optimizer:latest .

# Run with docker-compose
docker-compose up -d

# Verify deployment
docker-compose ps
docker-compose logs session-optimizer

# Test health check
curl http://localhost:8080/health
```

## Cloud Platform Deployment

### AWS Deployment

#### EC2 Instance Setup

```bash
# Launch EC2 instance (Ubuntu 20.04 LTS)
# Recommended: t3.large or larger for production

# Install Docker and Docker Compose
sudo apt update
sudo apt install docker.io docker-compose
sudo usermod -aG docker $USER

# Setup application
git clone <repository> /opt/session-optimizer
cd /opt/session-optimizer

# Configure environment
sudo cp config/aws-production.env .env
sudo chown $USER:$USER .env

# Deploy
docker-compose -f docker-compose.aws.yml up -d
```

#### ECS Deployment

Create `ecs-task-definition.json`:

```json
{
  "family": "session-optimizer",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/sessionOptimizerTaskRole",
  "containerDefinitions": [
    {
      "name": "session-optimizer",
      "image": "YOUR_ECR_URI/session-optimizer:latest",
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "SESSION_OPTIMIZER_ENV", "value": "production"},
        {"name": "MAX_WORKERS", "value": "4"},
        {"name": "MEMORY_LIMIT_MB", "value": "1536"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/session-optimizer",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "python gpt5_cli.py status || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

### Google Cloud Platform

#### Cloud Run Deployment

```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/session-optimizer

# Deploy to Cloud Run
gcloud run deploy session-optimizer \
  --image gcr.io/PROJECT_ID/session-optimizer \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars SESSION_OPTIMIZER_ENV=production \
  --memory 2Gi \
  --cpu 2 \
  --concurrency 10 \
  --timeout 900
```

### Azure Container Instances

```bash
# Create resource group
az group create --name session-optimizer-rg --location eastus

# Deploy container
az container create \
  --resource-group session-optimizer-rg \
  --name session-optimizer \
  --image sessionoptimizer/app:latest \
  --cpu 2 \
  --memory 4 \
  --ports 8080 \
  --environment-variables \
    SESSION_OPTIMIZER_ENV=production \
    MAX_WORKERS=4
```

## CI/CD Integration

### GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy Session Optimizer

on:
  push:
    branches: [main]
  release:
    types: [published]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install tiktoken pytest

      - name: Run tests
        run: |
          python gpt5_cli.py test

  build-and-deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: |
          docker build -t session-optimizer:${{ github.sha }} .

      - name: Deploy to staging
        if: github.ref == 'refs/heads/main'
        run: |
          # Deploy to staging environment
          echo "Deploying to staging..."

      - name: Deploy to production
        if: github.event_name == 'release'
        run: |
          # Deploy to production environment
          echo "Deploying to production..."
```

### Jenkins Pipeline

Create `Jenkinsfile`:

```groovy
pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "session-optimizer"
        DOCKER_TAG = "${env.BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Test') {
            steps {
                sh 'python3 -m venv venv'
                sh '. venv/bin/activate && pip install tiktoken pytest'
                sh '. venv/bin/activate && python gpt5_cli.py test'
            }
        }

        stage('Build') {
            steps {
                sh "docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} ."
                sh "docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${DOCKER_IMAGE}:latest"
            }
        }

        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                sh "docker-compose down"
                sh "docker-compose up -d"
            }
        }
    }

    post {
        always {
            cleanWs()
        }
    }
}
```

## Database Setup

The Session Optimizer is primarily file-based but can use Redis for caching and state management.

### Redis Setup

#### Local Redis Installation

```bash
# Ubuntu/Debian
sudo apt install redis-server

# macOS
brew install redis

# Start Redis
sudo systemctl start redis-server
# or
redis-server

# Test connection
redis-cli ping
```

#### Redis Configuration

Create `config/redis.conf`:

```conf
# Network
bind 127.0.0.1
port 6379
protected-mode yes

# Memory
maxmemory 1gb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000

# Logging
loglevel notice
logfile /var/log/redis/redis-server.log

# Performance
tcp-keepalive 300
timeout 0
```

#### Database Schema (Redis)

The system uses Redis for caching optimization results:

```
Keys Pattern:
- session:{session_id}:tokens - Token count cache
- session:{session_id}:chunks - Chunking result cache
- session:{session_id}:payloads - Generated payload cache
- optimization:{session_hash} - Complete optimization result
- stats:daily:{date} - Daily processing statistics
```

## Monitoring & Health Checks

### Health Check Endpoint

The system provides health check endpoints:

```bash
# Basic health check
curl http://localhost:8080/health

# Detailed system status
curl http://localhost:8080/status/detailed

# Metrics endpoint (Prometheus format)
curl http://localhost:9090/metrics
```

### Monitoring Configuration

#### Prometheus Configuration

Create `monitoring/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'session-optimizer'
    static_configs:
      - targets: ['session-optimizer:9090']
    scrape_interval: 30s
    metrics_path: /metrics

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
```

#### Custom Metrics

The system exposes these metrics:

```
# Processing Metrics
session_optimizer_sessions_processed_total
session_optimizer_processing_duration_seconds
session_optimizer_compression_ratio
session_optimizer_cost_savings_total

# System Metrics
session_optimizer_memory_usage_bytes
session_optimizer_active_workers
session_optimizer_queue_size

# Error Metrics
session_optimizer_errors_total
session_optimizer_failed_sessions_total
```

### Alerting Rules

Create `monitoring/alert-rules.yml`:

```yaml
groups:
  - name: session-optimizer
    rules:
      - alert: HighErrorRate
        expr: rate(session_optimizer_errors_total[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: High error rate detected

      - alert: MemoryUsageHigh
        expr: session_optimizer_memory_usage_bytes > 1.5e9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: Memory usage is high

      - alert: ServiceDown
        expr: up{job="session-optimizer"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: Session Optimizer service is down
```

### Log Management

#### Log Configuration

Configure logging in `config/logging.json`:

```json
{
  "version": 1,
  "formatters": {
    "detailed": {
      "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    },
    "json": {
      "format": "{\"timestamp\": \"%(asctime)s\", \"level\": \"%(levelname)s\", \"logger\": \"%(name)s\", \"message\": \"%(message)s\"}"
    }
  },
  "handlers": {
    "console": {
      "class": "logging.StreamHandler",
      "level": "INFO",
      "formatter": "detailed"
    },
    "file": {
      "class": "logging.handlers.RotatingFileHandler",
      "level": "DEBUG",
      "formatter": "json",
      "filename": "/var/log/session-optimizer/app.log",
      "maxBytes": 10485760,
      "backupCount": 10
    },
    "error_file": {
      "class": "logging.handlers.RotatingFileHandler",
      "level": "ERROR",
      "formatter": "json",
      "filename": "/var/log/session-optimizer/error.log",
      "maxBytes": 10485760,
      "backupCount": 5
    }
  },
  "loggers": {
    "session_optimizer": {
      "level": "DEBUG",
      "handlers": ["console", "file", "error_file"]
    }
  },
  "root": {
    "level": "INFO",
    "handlers": ["console"]
  }
}
```

## Security Configuration

### Access Control

#### Authentication Configuration

```python
# config/auth.py
AUTH_CONFIG = {
    "enabled": True,
    "method": "api_key",  # or "oauth2", "jwt"
    "api_keys": {
        "admin": "admin-secret-key-here",
        "user": "user-access-key-here"
    },
    "rate_limiting": {
        "enabled": True,
        "requests_per_minute": 100,
        "burst_limit": 10
    }
}
```

#### Security Headers

```python
# Security middleware configuration
SECURITY_CONFIG = {
    "cors_enabled": True,
    "cors_origins": ["http://localhost:3000"],
    "csrf_protection": True,
    "content_security_policy": {
        "default-src": "'self'",
        "script-src": "'self' 'unsafe-inline'",
        "style-src": "'self' 'unsafe-inline'"
    },
    "rate_limiting": True,
    "request_size_limit": "100MB"
}
```

### Data Protection

#### Encryption Configuration

```bash
# Environment variables for encryption
export ENCRYPTION_KEY=$(openssl rand -base64 32)
export SESSION_DATA_ENCRYPTION=true
export SECURE_TEMP_FILES=true
```

#### File Permissions

```bash
# Set secure file permissions
chmod 600 config/production.json
chmod 600 .env
chmod 700 data/sessions/
chmod 750 logs/
```

## Backup & Recovery

### Backup Strategy

#### Automated Backup Script

Create `scripts/backup.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/backup/session-optimizer"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="session-optimizer-${DATE}"

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Backup configuration
tar -czf "${BACKUP_DIR}/${BACKUP_NAME}-config.tar.gz" config/ .env

# Backup processed data (last 30 days)
find data/sessions/output -mtime -30 -type f | tar -czf "${BACKUP_DIR}/${BACKUP_NAME}-data.tar.gz" -T -

# Backup Redis data (if used)
if command -v redis-cli &> /dev/null; then
    redis-cli BGSAVE
    cp /var/lib/redis/dump.rdb "${BACKUP_DIR}/${BACKUP_NAME}-redis.rdb"
fi

# Backup logs (last 7 days)
find logs/ -mtime -7 -type f | tar -czf "${BACKUP_DIR}/${BACKUP_NAME}-logs.tar.gz" -T -

# Cleanup old backups (keep 30 days)
find "${BACKUP_DIR}" -name "session-optimizer-*" -mtime +30 -delete

echo "Backup completed: ${BACKUP_NAME}"
```

#### Backup Automation

Add to crontab:

```bash
# Daily backup at 2 AM
0 2 * * * /opt/session-optimizer/scripts/backup.sh >> /var/log/session-optimizer/backup.log 2>&1

# Weekly full backup
0 3 * * 0 /opt/session-optimizer/scripts/full-backup.sh >> /var/log/session-optimizer/backup.log 2>&1
```

### Recovery Procedures

#### Data Recovery

```bash
# Stop service
sudo systemctl stop session-optimizer
# or docker-compose down

# Restore configuration
tar -xzf backup/session-optimizer-DATE-config.tar.gz

# Restore data
tar -xzf backup/session-optimizer-DATE-data.tar.gz

# Restore Redis data (if applicable)
sudo systemctl stop redis
cp backup/session-optimizer-DATE-redis.rdb /var/lib/redis/dump.rdb
sudo chown redis:redis /var/lib/redis/dump.rdb
sudo systemctl start redis

# Verify configuration
python gpt5_cli.py status --detailed

# Start service
sudo systemctl start session-optimizer
# or docker-compose up -d
```

#### Point-in-Time Recovery

```bash
# Restore to specific backup
RESTORE_DATE="20240909_143000"
cd /opt/session-optimizer

# Create recovery directory
mkdir -p recovery/

# Extract backup
tar -xzf backup/session-optimizer-${RESTORE_DATE}-data.tar.gz -C recovery/

# Verify data integrity
python scripts/verify-data.py recovery/data/

# Apply recovery
rsync -av recovery/data/ data/
```

## Scaling Considerations

### Horizontal Scaling

#### Load Balancer Configuration

```nginx
# nginx.conf
upstream session_optimizer_backend {
    least_conn;
    server 10.0.1.10:8080 weight=1 max_fails=3 fail_timeout=30s;
    server 10.0.1.11:8080 weight=1 max_fails=3 fail_timeout=30s;
    server 10.0.1.12:8080 weight=1 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name session-optimizer.example.com;

    location / {
        proxy_pass http://session_optimizer_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_timeout 300s;
    }

    location /health {
        access_log off;
        proxy_pass http://session_optimizer_backend;
    }
}
```

#### Auto Scaling Configuration

```yaml
# Kubernetes HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: session-optimizer-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: session-optimizer
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Vertical Scaling

#### Performance Tuning

```bash
# High-performance configuration
export MAX_WORKERS=16
export MEMORY_LIMIT_MB=8192
export ENABLE_PARALLEL_PROCESSING=true
export BATCH_SIZE=20

# System optimizations
echo 'vm.swappiness=1' >> /etc/sysctl.conf
echo 'net.core.somaxconn=65535' >> /etc/sysctl.conf
sysctl -p
```

#### Resource Monitoring

```bash
# Create monitoring script
cat > scripts/resource-monitor.sh << 'EOF'
#!/bin/bash
while true; do
    echo "$(date): CPU=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}') Memory=$(free | grep Mem | awk '{printf("%.1f%%", $3/$2 * 100.0)}')"
    sleep 60
done
EOF
```

## Maintenance Tasks

### Daily Maintenance

#### Automated Daily Tasks

Create `scripts/daily-maintenance.sh`:

```bash
#!/bin/bash

LOG_FILE="/var/log/session-optimizer/maintenance.log"

echo "$(date): Starting daily maintenance" >> $LOG_FILE

# Clean up temporary files older than 1 day
find /tmp/session-optimizer -type f -mtime +1 -delete 2>/dev/null

# Rotate application logs
if [ -f /var/log/session-optimizer/app.log ]; then
    logrotate /etc/logrotate.d/session-optimizer
fi

# Clean up processed files older than 30 days
find data/sessions/output -name "*.json" -mtime +30 -delete 2>/dev/null

# Update system statistics
python scripts/update-stats.py >> $LOG_FILE 2>&1

# Health check
python gpt5_cli.py status >> $LOG_FILE 2>&1

echo "$(date): Daily maintenance completed" >> $LOG_FILE
```

### Weekly Maintenance

#### Weekly Tasks Script

Create `scripts/weekly-maintenance.sh`:

```bash
#!/bin/bash

# Database cleanup (Redis)
if command -v redis-cli &> /dev/null; then
    redis-cli FLUSHDB ASYNC
fi

# Full backup
./scripts/backup.sh

# System updates (if automated)
if [ "$AUTO_UPDATE" = "true" ]; then
    pip install --upgrade tiktoken
fi

# Performance analysis
python scripts/analyze-performance.py --days 7

# Security scan
python scripts/security-check.py
```

### Monthly Maintenance

#### Monthly Tasks

```bash
#!/bin/bash

# Archive old data
python scripts/archive-data.py --older-than 90

# Full system backup
./scripts/full-backup.sh

# Update documentation
python scripts/generate-reports.py --monthly

# Security updates
apt update && apt upgrade -y

# Performance optimization
python scripts/optimize-performance.py

# Disaster recovery test
./scripts/test-recovery.sh
```

## Troubleshooting

### Common Issues

#### 1. Memory Issues

**Symptoms:**
- Out of memory errors
- Slow processing
- System becomes unresponsive

**Solutions:**
```bash
# Check memory usage
python gpt5_cli.py status --memory

# Reduce memory settings
export MEMORY_LIMIT_MB=1024
export MAX_WORKERS=2

# Enable streaming for large files
python gpt5_cli.py stream large_session.jsonl --memory-limit 512
```

#### 2. Performance Issues

**Symptoms:**
- Slow processing times
- Low throughput

**Solutions:**
```bash
# Enable parallel processing
export ENABLE_PARALLEL_PROCESSING=true
export MAX_WORKERS=8

# Check system resources
htop
iostat -x 1

# Optimize strategy selection
python gpt5_cli.py compare session.jsonl
```

#### 3. tiktoken Import Errors

**Symptoms:**
- `ModuleNotFoundError: No module named 'tiktoken'`
- Token counting failures

**Solutions:**
```bash
# Install tiktoken
pip install tiktoken

# Verify installation
python -c "import tiktoken; print('tiktoken version:', tiktoken.__version__)"

# Alternative installation
pip install --upgrade pip
pip install --force-reinstall tiktoken
```

#### 4. File Processing Errors

**Symptoms:**
- JSON parsing errors
- File format issues

**Solutions:**
```bash
# Validate file format
python scripts/validate-session.py session.jsonl

# Check file permissions
ls -la session.jsonl

# Repair corrupted files
python scripts/repair-session.py session.jsonl
```

#### 5. Docker Issues

**Symptoms:**
- Container startup failures
- Port binding errors

**Solutions:**
```bash
# Check logs
docker-compose logs session-optimizer

# Verify ports
netstat -tulpn | grep 8080

# Rebuild container
docker-compose down
docker system prune -f
docker-compose up --build -d
```

### Diagnostic Tools

#### System Diagnostics

Create `scripts/diagnostics.py`:

```python
#!/usr/bin/env python3
"""System diagnostics for Session Optimizer"""

import sys
import os
import json
import subprocess
from pathlib import Path

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} (requires 3.9+)")
        return False

def check_dependencies():
    """Check required dependencies"""
    try:
        import tiktoken
        print(f"✅ tiktoken {tiktoken.__version__}")
        return True
    except ImportError:
        print("❌ tiktoken not installed")
        return False

def check_disk_space():
    """Check available disk space"""
    try:
        result = subprocess.run(['df', '-h', '.'], capture_output=True, text=True)
        print(f"✅ Disk space: {result.stdout.split()[11]} available")
        return True
    except:
        print("❌ Could not check disk space")
        return False

def check_memory():
    """Check available memory"""
    try:
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
            for line in lines:
                if 'MemAvailable:' in line:
                    mem_kb = int(line.split()[1])
                    mem_gb = mem_kb / 1024 / 1024
                    print(f"✅ Available memory: {mem_gb:.1f} GB")
                    return mem_gb > 2
        return False
    except:
        print("❌ Could not check memory")
        return False

def main():
    print("Session Optimizer Diagnostic Report")
    print("=" * 40)

    checks = [
        check_python_version(),
        check_dependencies(),
        check_disk_space(),
        check_memory()
    ]

    if all(checks):
        print("\n✅ All diagnostic checks passed")
        return 0
    else:
        print("\n❌ Some diagnostic checks failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

#### Performance Profiler

Create `scripts/profile-performance.py`:

```python
#!/usr/bin/env python3
"""Performance profiler for Session Optimizer"""

import time
import psutil
import json
from pathlib import Path

class PerformanceProfiler:
    def __init__(self):
        self.start_time = None
        self.metrics = {}

    def start(self):
        self.start_time = time.time()
        self.metrics['start_memory'] = psutil.virtual_memory().used
        self.metrics['start_cpu'] = psutil.cpu_percent()

    def end(self):
        if self.start_time:
            self.metrics['duration'] = time.time() - self.start_time
            self.metrics['end_memory'] = psutil.virtual_memory().used
            self.metrics['end_cpu'] = psutil.cpu_percent()
            self.metrics['memory_used'] = self.metrics['end_memory'] - self.metrics['start_memory']

    def report(self):
        print(f"Processing Duration: {self.metrics['duration']:.2f}s")
        print(f"Memory Used: {self.metrics['memory_used'] / 1024 / 1024:.1f} MB")
        print(f"CPU Usage: {self.metrics['end_cpu']:.1f}%")
        return self.metrics

# Usage example
if __name__ == "__main__":
    profiler = PerformanceProfiler()
    profiler.start()

    # Simulate processing
    import time
    time.sleep(2)

    profiler.end()
    profiler.report()
```

## Rollback Procedures

### Quick Rollback

#### Docker Rollback

```bash
# Stop current version
docker-compose down

# Rollback to previous image
docker tag session-optimizer:previous session-optimizer:latest
docker-compose up -d

# Verify rollback
curl http://localhost:8080/health
```

#### File-based Rollback

```bash
# Stop service
sudo systemctl stop session-optimizer

# Restore from backup
ROLLBACK_DATE="20240908_120000"
tar -xzf backup/session-optimizer-${ROLLBACK_DATE}-config.tar.gz
tar -xzf backup/session-optimizer-${ROLLBACK_DATE}-data.tar.gz

# Start service
sudo systemctl start session-optimizer

# Verify
python gpt5_cli.py status
```

### Emergency Recovery

#### Complete System Recovery

Create `scripts/emergency-recovery.sh`:

```bash
#!/bin/bash

echo "Starting emergency recovery..."

# Stop all services
sudo systemctl stop session-optimizer
docker-compose down 2>/dev/null || true

# Restore from latest known good backup
LATEST_BACKUP=$(ls -t backup/session-optimizer-*-config.tar.gz | head -1)
if [ -f "$LATEST_BACKUP" ]; then
    echo "Restoring from: $LATEST_BACKUP"
    tar -xzf "$LATEST_BACKUP"

    # Restore data
    DATA_BACKUP="${LATEST_BACKUP/-config/-data}"
    if [ -f "$DATA_BACKUP" ]; then
        tar -xzf "$DATA_BACKUP"
    fi
else
    echo "No backup found, using default configuration"
    cp config/default.json config/production.json
fi

# Reset permissions
chmod 600 config/production.json .env
chmod -R 755 data/
chmod -R 755 logs/

# Clear temporary files
rm -rf /tmp/session-optimizer/*

# Restart services
sudo systemctl start session-optimizer
sleep 10

# Verify recovery
if python gpt5_cli.py status; then
    echo "✅ Emergency recovery successful"
else
    echo "❌ Recovery failed, manual intervention required"
    exit 1
fi
```

### Version Management

#### Blue-Green Deployment Rollback

```bash
# Switch traffic back to blue deployment
# Update load balancer configuration
curl -X POST http://load-balancer/api/switch \
  -H "Content-Type: application/json" \
  -d '{"target": "blue", "health_check": true}'

# Verify switch
curl http://load-balancer/health

# If successful, terminate green deployment
docker-compose -f docker-compose.green.yml down
```

---

## Deployment Verification Checklist

### Pre-Deployment

- [ ] System requirements met
- [ ] Dependencies installed
- [ ] Configuration files prepared
- [ ] Environment variables set
- [ ] Backup procedures tested
- [ ] Monitoring configured

### Post-Deployment

- [ ] Health checks passing
- [ ] Application responding correctly
- [ ] Logs being written
- [ ] Metrics being collected
- [ ] Performance within acceptable limits
- [ ] Security configurations active

### Production Readiness

- [ ] Load testing completed
- [ ] Disaster recovery tested
- [ ] Monitoring alerts configured
- [ ] Documentation updated
- [ ] Team trained on operations
- [ ] Rollback procedures verified

---

**Session Optimizer Deployment Guide v1.0**
*Complete deployment, operations, and maintenance documentation*
