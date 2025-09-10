# Agent Orchestrator Deployment Guide

## Table of Contents
1. [Overview](#overview)
2. [System Requirements](#system-requirements)
3. [Environment Configuration](#environment-configuration)
4. [Database Setup](#database-setup)
5. [Deployment Methods](#deployment-methods)
6. [Monitoring Setup](#monitoring-setup)
7. [Security Configuration](#security-configuration)
8. [Scaling Considerations](#scaling-considerations)
9. [Backup & Recovery](#backup--recovery)
10. [Maintenance](#maintenance)
11. [Troubleshooting](#troubleshooting)

## Overview

The Agent Orchestrator is a production-ready distributed system for managing AI agents and workflows. This guide provides comprehensive deployment instructions for various environments from local development to production enterprise deployments.

## Quick Start (5 Minutes)

```bash
# 1. Clone and setup
git clone <repository-url> agent-orchestrator
cd agent-orchestrator
python3.11 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt
pip install anthropic openai

# 3. Configure API keys
export ANTHROPIC_API_KEY="your-key-here"
export OPENAI_API_KEY="your-key-here"

# 4. Start the dashboard
python production_dashboard.py --config production_config.json

# 5. Open browser to http://localhost:8765
```

### Architecture Components
- **Core Orchestrator**: Main workflow execution engine
- **Dashboard Server**: Real-time monitoring and management interface
- **PostgreSQL**: Primary data persistence layer
- **Redis**: Caching and message bus
- **Prometheus/Grafana**: Monitoring and observability

## System Requirements

### Minimum Requirements
- **OS**: Linux (Ubuntu 20.04+, CentOS 8+) or macOS 12+
- **CPU**: 4 cores (2.4GHz+)
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 50GB available space
- **Network**: Reliable internet connection for AI API access

### Production Requirements
- **OS**: Linux (Ubuntu 20.04+ LTS recommended)
- **CPU**: 8+ cores (3.0GHz+)
- **RAM**: 32GB+ recommended
- **Storage**: 200GB+ SSD storage
- **Network**: High-speed internet with low latency
- **Load Balancer**: For high-availability deployments

### Software Dependencies
- **Python**: 3.11+ (recommended)
- **PostgreSQL**: 13+
- **Redis**: 6.0+
- **Docker**: 20.10+ (for containerized deployment)
- **Git**: For source code management

## Environment Configuration

### Required Environment Variables

```bash
# Core Configuration
MAX_PARALLEL=15                    # Maximum parallel agent execution
TOKEN_POOL_SIZE=20                # AI API token pool size
PYTHONPATH=/app/src              # Python module path

# Database Configuration
COLLABORATION_DATABASE_URL="postgresql://username:password@localhost:5432/collaboration"
COLLABORATION_REDIS_URL="redis://localhost:6379/0"
DB_MAX_CONNECTIONS=20
DB_MIN_CONNECTIONS=5
DB_CONNECTION_TIMEOUT=30
DB_QUERY_TIMEOUT=60
DB_ENABLE_SSL=false
DB_POOL_RECYCLE=3600
DB_ECHO=false

# Dashboard Configuration
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=8765
DASHBOARD_LOG_LEVEL=INFO

# API Keys (Required)
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key

# Optional: Advanced Configuration
WORKFLOW_SCAN_INTERVAL=10
MAX_WORKFLOW_HISTORY=100
WORKFLOW_RETENTION_DAYS=30
```

### Environment-Specific Configurations

#### Development Environment
```bash
# .env.development
DEBUG=true
LOG_LEVEL=DEBUG
DB_ECHO=true
ENABLE_CORS=true
RATE_LIMITING_ENABLED=false
```

#### Production Environment
```bash
# .env.production
DEBUG=false
LOG_LEVEL=INFO
DB_ECHO=false
ENABLE_CORS=false
RATE_LIMITING_ENABLED=true
ENABLE_PROMETHEUS_METRICS=true
```

## Database Setup

### Database Options
The system supports multiple database configurations:
1. **SQLite** (Default): Automatic, no setup required
2. **PostgreSQL**: For production deployments with high concurrency
3. **No Database**: System can run with in-memory storage for testing

### PostgreSQL Installation & Configuration (Optional)

#### Ubuntu/Debian
```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres createuser --interactive orchestrator
sudo -u postgres createdb collaboration -O orchestrator
sudo -u postgres psql -c "ALTER USER orchestrator PASSWORD 'your_secure_password';"
```

#### CentOS/RHEL
```bash
# Install PostgreSQL
sudo yum install postgresql-server postgresql-contrib
sudo postgresql-setup --initdb
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Create database and user
sudo -u postgres createuser --interactive orchestrator
sudo -u postgres createdb collaboration -O orchestrator
sudo -u postgres psql -c "ALTER USER orchestrator PASSWORD 'your_secure_password';"
```

#### Database Schema Creation
```bash
# The system automatically creates tables on first run
# Database initialization is handled by src/persistence/database.py
# No manual setup required

# To verify database connection:
python -c "from src.persistence.database import DatabaseManager; print('Database module loaded')"
```

### Redis Installation & Configuration (Optional)

#### Ubuntu/Debian
```bash
sudo apt install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Verify installation
redis-cli ping
```

#### CentOS/RHEL
```bash
sudo yum install redis
sudo systemctl enable redis
sudo systemctl start redis

# Verify installation
redis-cli ping
```

#### Redis Configuration (`/etc/redis/redis.conf`)
```conf
# Basic security
bind 127.0.0.1
requirepass your_redis_password

# Performance tuning
maxmemory 2gb
maxmemory-policy allkeys-lru
tcp-keepalive 60

# Persistence
save 900 1
save 300 10
save 60 10000
```

## Available Run Scripts

The orchestrator includes several specialized run scripts:

- **`production_dashboard.py`**: Main dashboard server with WebSocket monitoring
- **`run_orchestrator_task.py`**: Execute specific orchestration tasks
- **`run_system_analysis.py`**: Analyze system capabilities and generate reports
- **`run_parallel_doc_update.py`**: Update documentation in parallel
- **`run_apps_audit.py`**: Audit applications for issues
- **`run_with_live_chat.py`**: Run with interactive chat interface

## Deployment Methods

### Method 1: Local Development Setup

#### Prerequisites Setup
```bash
# Clone the repository
git clone <repository-url>
cd agent-orchestrator

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Configuration
```bash
# Create environment file
cp .env.example .env
# Edit .env with your configuration

# Create required directories
mkdir -p logs outputs checkpoints
```

#### Start Services
```bash
# Terminal 1: Start main orchestrator
python main.py

# Terminal 2: Start dashboard (optional)
python production_dashboard.py --config production_config.json

# Terminal 3: Run a sample workflow
python run_orchestrator_task.py --app-name "sample-app" --task-type "system-analysis"
```

### Method 2: Docker Deployment

#### Single-Node Docker Deployment
```bash
# Build and start all services
docker-compose up -d

# Verify services are running
docker-compose ps

# View logs
docker-compose logs -f agent-orchestrator
```

#### Multi-Container Production Setup
```yaml
# docker-compose.production.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: collaboration
      POSTGRES_USER: orchestrator
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U orchestrator -d collaboration"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "auth", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  agent-orchestrator:
    build: .
    environment:
      - MAX_PARALLEL=15
      - TOKEN_POOL_SIZE=20
      - COLLABORATION_DATABASE_URL=postgresql://orchestrator:${POSTGRES_PASSWORD}@postgres:5432/collaboration
      - COLLABORATION_REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./outputs:/app/outputs
      - ./logs:/app/logs
    ports:
      - "8080:8080"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "from src.generic_orchestrator import GenericOrchestrator; print('Health check passed')"]
      interval: 30s
      timeout: 10s
      retries: 3

  dashboard:
    build: .
    command: ["python", "production_dashboard.py", "--config", "production_config.json"]
    environment:
      - DASHBOARD_HOST=0.0.0.0
      - DASHBOARD_PORT=8765
    ports:
      - "8765:8765"
    volumes:
      - ./web:/app/web
      - ./logs:/app/logs
    depends_on:
      - agent-orchestrator
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:
```

#### Deploy Production Stack
```bash
# Create environment file
cat > .env << EOF
POSTGRES_PASSWORD=secure_postgres_password
REDIS_PASSWORD=secure_redis_password
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key
GRAFANA_PASSWORD=secure_grafana_password
EOF

# Deploy the stack
docker-compose -f docker-compose.production.yml up -d

# Verify deployment
docker-compose -f docker-compose.production.yml ps
```

### Method 3: Systemd Service Deployment

#### Create Service Unit
```bash
# Copy service file
sudo cp dashboard.service /etc/systemd/system/

# Create user and directories
sudo useradd -r -s /bin/false orchestrator
sudo mkdir -p /opt/agent-orchestrator/logs /opt/agent-orchestrator/outputs
sudo chown -R orchestrator:orchestrator /opt/agent-orchestrator

# Deploy application
sudo -u orchestrator git clone <repository> /opt/agent-orchestrator/app
cd /opt/agent-orchestrator/app
sudo -u orchestrator python -m venv venv
sudo -u orchestrator ./venv/bin/pip install -r requirements.txt
```

#### Service Management
```bash
# Enable and start service
sudo systemctl enable dashboard.service
sudo systemctl start dashboard.service

# Check status
sudo systemctl status dashboard.service

# View logs
sudo journalctl -u dashboard.service -f
```

### Method 4: Cloud Platform Deployment

#### AWS Deployment with ECS
```yaml
# ecs-task-definition.json
{
  "family": "agent-orchestrator",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "agent-orchestrator",
      "image": "your-registry/agent-orchestrator:latest",
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        },
        {
          "containerPort": 8765,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "MAX_PARALLEL",
          "value": "15"
        },
        {
          "name": "COLLABORATION_DATABASE_URL",
          "value": "postgresql://user:pass@rds-endpoint:5432/collaboration"
        }
      ],
      "secrets": [
        {
          "name": "ANTHROPIC_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:anthropic-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/agent-orchestrator",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### Kubernetes Deployment
```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-orchestrator
spec:
  replicas: 3
  selector:
    matchLabels:
      app: agent-orchestrator
  template:
    metadata:
      labels:
        app: agent-orchestrator
    spec:
      containers:
      - name: orchestrator
        image: agent-orchestrator:latest
        ports:
        - containerPort: 8080
        - containerPort: 8765
        env:
        - name: MAX_PARALLEL
          value: "15"
        - name: COLLABORATION_DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: anthropic
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8765
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8765
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: agent-orchestrator-service
spec:
  selector:
    app: agent-orchestrator
  ports:
  - name: api
    port: 8080
    targetPort: 8080
  - name: dashboard
    port: 8765
    targetPort: 8765
  type: LoadBalancer
```

## Monitoring Setup

### Prometheus Configuration
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'agent-orchestrator'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: /metrics
    scrape_interval: 10s

  - job_name: 'dashboard'
    static_configs:
      - targets: ['localhost:8765']
    metrics_path: /metrics
    scrape_interval: 10s

  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:9121']
```

### Grafana Dashboard Setup
```json
{
  "dashboard": {
    "title": "Agent Orchestrator Monitoring",
    "panels": [
      {
        "title": "Active Workflows",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(orchestrator_active_workflows)"
          }
        ]
      },
      {
        "title": "Agent Success Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(orchestrator_successful_tasks[5m]) / rate(orchestrator_total_tasks[5m]) * 100"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, orchestrator_response_time_bucket)"
          }
        ]
      }
    ]
  }
}
```

### Health Check Endpoints
- **Main Service**: `GET /health` (Port 8080)
- **Dashboard**: `GET /api/health` (Port 8765)
- **Database Health**: `GET /api/health/database`
- **Redis Health**: `GET /api/health/redis`

### Log Aggregation
```yaml
# docker-compose.logging.yml
version: '3.8'
services:
  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    volumes:
      - ./loki-config.yml:/etc/loki/local-config.yaml
    command: -config.file=/etc/loki/local-config.yaml

  promtail:
    image: grafana/promtail:latest
    volumes:
      - ./logs:/var/log
      - ./promtail-config.yml:/etc/promtail/config.yml
    command: -config.file=/etc/promtail/config.yml
```

## Security Configuration

### SSL/TLS Setup

#### Generate SSL Certificates
```bash
# Self-signed certificate (development)
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Let's Encrypt (production)
certbot certonly --standalone -d your-domain.com
```

#### Nginx Reverse Proxy Configuration
```nginx
# /etc/nginx/sites-available/agent-orchestrator
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;

    # Main API
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Dashboard
    location /dashboard/ {
        proxy_pass http://localhost:8765/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

### Firewall Configuration

#### UFW (Ubuntu)
```bash
# Enable firewall
sudo ufw enable

# Allow SSH
sudo ufw allow ssh

# Allow application ports
sudo ufw allow 8080/tcp  # Main API
sudo ufw allow 8765/tcp  # Dashboard
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 80/tcp    # HTTP (for redirects)

# Database access (only from application servers)
sudo ufw allow from 10.0.1.0/24 to any port 5432
sudo ufw allow from 10.0.1.0/24 to any port 6379
```

#### iptables
```bash
# Basic rules
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT -p tcp --dport 22 -j ACCEPT
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT
iptables -A INPUT -p tcp --dport 8080 -j ACCEPT
iptables -A INPUT -p tcp --dport 8765 -j ACCEPT
iptables -P INPUT DROP

# Save rules
iptables-save > /etc/iptables/rules.v4
```

### Secret Management

#### Using Environment Variables (Development)
```bash
# .env.secret (never commit to version control)
ANTHROPIC_API_KEY=sk-ant-xxxxx
OPENAI_API_KEY=sk-xxxxx
POSTGRES_PASSWORD=secure_password
REDIS_PASSWORD=secure_redis_pass
JWT_SECRET_KEY=random_secret_key
```

#### Using HashiCorp Vault (Production)
```bash
# Install Vault
curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
sudo apt-get update && sudo apt-get install vault

# Configure Vault
vault server -dev
export VAULT_ADDR='http://127.0.0.1:8200'
vault auth -method=userpass username=admin password=password

# Store secrets
vault kv put secret/agent-orchestrator \
  anthropic_api_key="sk-ant-xxxxx" \
  openai_api_key="sk-xxxxx" \
  postgres_password="secure_password"
```

## Scaling Considerations

### Horizontal Scaling

#### Load Balancer Configuration
```yaml
# haproxy.cfg
global
    daemon
    maxconn 4096

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend orchestrator_frontend
    bind *:8080
    default_backend orchestrator_backend

backend orchestrator_backend
    balance roundrobin
    option httpchk GET /health
    server orch1 10.0.1.10:8080 check
    server orch2 10.0.1.11:8080 check
    server orch3 10.0.1.12:8080 check

frontend dashboard_frontend
    bind *:8765
    default_backend dashboard_backend

backend dashboard_backend
    balance source
    option httpchk GET /api/health
    server dash1 10.0.1.10:8765 check
    server dash2 10.0.1.11:8765 check
    server dash3 10.0.1.12:8765 check
```

### Vertical Scaling

#### Resource Optimization
```yaml
# docker-compose.override.yml for high-resource environments
version: '3.8'
services:
  agent-orchestrator:
    environment:
      - MAX_PARALLEL=50
      - TOKEN_POOL_SIZE=100
      - DB_MAX_CONNECTIONS=50
    deploy:
      resources:
        limits:
          cpus: '8.0'
          memory: 16G
        reservations:
          cpus: '4.0'
          memory: 8G
```

### Database Scaling

#### PostgreSQL Master-Slave Setup
```bash
# Master server configuration (postgresql.conf)
wal_level = replica
max_wal_senders = 3
wal_keep_segments = 64
archive_mode = on
archive_command = 'test ! -f /var/lib/postgresql/archive/%f && cp %p /var/lib/postgresql/archive/%f'
```

#### Redis Cluster Setup
```bash
# Redis cluster configuration
redis-cli --cluster create \
  10.0.1.10:7000 10.0.1.11:7000 10.0.1.12:7000 \
  10.0.1.10:7001 10.0.1.11:7001 10.0.1.12:7001 \
  --cluster-replicas 1
```

## Backup & Recovery

### Database Backup

#### Automated PostgreSQL Backup Script
```bash
#!/bin/bash
# backup-postgres.sh

set -e

# Configuration
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="collaboration"
DB_USER="orchestrator"
BACKUP_DIR="/opt/backups/postgres"
RETENTION_DAYS=30

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Generate backup filename
BACKUP_FILE="$BACKUP_DIR/postgres-$(date +%Y%m%d-%H%M%S).sql.gz"

# Create backup
PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
  -h "$DB_HOST" \
  -p "$DB_PORT" \
  -U "$DB_USER" \
  -d "$DB_NAME" \
  --no-owner \
  --no-acl \
  | gzip > "$BACKUP_FILE"

# Verify backup
if [ -s "$BACKUP_FILE" ]; then
    echo "Backup created successfully: $BACKUP_FILE"

    # Upload to S3 (optional)
    # aws s3 cp "$BACKUP_FILE" s3://your-backup-bucket/postgres/
else
    echo "Backup failed: $BACKUP_FILE is empty"
    exit 1
fi

# Clean old backups
find "$BACKUP_DIR" -name "postgres-*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed successfully"
```

#### Setup Automated Backups
```bash
# Add to crontab
crontab -e

# Daily backup at 2 AM
0 2 * * * /opt/scripts/backup-postgres.sh >> /var/log/backup.log 2>&1

# Hourly Redis backup
0 * * * * redis-cli BGSAVE && cp /var/lib/redis/dump.rdb /opt/backups/redis/dump-$(date +\%Y\%m\%d-\%H\%M\%S).rdb
```

### Application Data Backup
```bash
#!/bin/bash
# backup-application.sh

BACKUP_DIR="/opt/backups/application"
APP_DIR="/opt/agent-orchestrator"
BACKUP_FILE="$BACKUP_DIR/app-$(date +%Y%m%d-%H%M%S).tar.gz"

mkdir -p "$BACKUP_DIR"

# Create application backup
tar -czf "$BACKUP_FILE" \
  -C "$APP_DIR" \
  --exclude="*.log" \
  --exclude="*.pid" \
  --exclude=".git" \
  --exclude="venv" \
  --exclude="__pycache__" \
  .

echo "Application backup created: $BACKUP_FILE"
```

### Disaster Recovery

#### Recovery Playbook
```bash
#!/bin/bash
# disaster-recovery.sh

set -e

BACKUP_FILE="$1"
if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup-file>"
    exit 1
fi

echo "Starting disaster recovery..."

# Stop services
sudo systemctl stop dashboard
docker-compose down

# Restore database
echo "Restoring database..."
dropdb collaboration
createdb collaboration
gunzip -c "$BACKUP_FILE" | psql collaboration

# Restore application
echo "Restoring application..."
tar -xzf application-backup.tar.gz -C /opt/agent-orchestrator

# Restart services
docker-compose up -d
sudo systemctl start dashboard

echo "Disaster recovery completed"
```

## Maintenance

### Regular Maintenance Tasks

#### Daily Tasks
```bash
#!/bin/bash
# daily-maintenance.sh

# Check service health
docker-compose ps
systemctl status dashboard

# Check disk space
df -h /opt/agent-orchestrator

# Rotate logs
logrotate /etc/logrotate.d/agent-orchestrator

# Database maintenance
psql collaboration -c "VACUUM ANALYZE;"

# Clear old workflow outputs
find /opt/agent-orchestrator/outputs -type d -mtime +7 -exec rm -rf {} +
```

#### Weekly Tasks
```bash
#!/bin/bash
# weekly-maintenance.sh

# Update system packages
sudo apt update && sudo apt upgrade -y

# Check for security updates
sudo unattended-upgrades --dry-run

# Database optimization
psql collaboration -c "REINDEX DATABASE collaboration;"

# Generate performance reports
python scripts/generate-performance-report.py --days 7
```

#### Monthly Tasks
```bash
#!/bin/bash
# monthly-maintenance.sh

# Full system backup
./backup-system.sh

# Certificate renewal
certbot renew

# Security audit
lynis audit system

# Update Docker images
docker-compose pull
docker-compose up -d
```

### Update Procedures

#### Application Updates
```bash
#!/bin/bash
# update-application.sh

set -e

# Backup current version
./backup-application.sh

# Pull latest code
cd /opt/agent-orchestrator
git fetch origin
git checkout main
git pull origin main

# Update dependencies
./venv/bin/pip install -r requirements.txt

# Run database migrations (if any)
python scripts/migrate.py

# Restart services
sudo systemctl restart dashboard
docker-compose restart agent-orchestrator

# Verify deployment
curl -f http://localhost:8765/api/health || {
    echo "Health check failed, rolling back..."
    git checkout HEAD~1
    sudo systemctl restart dashboard
    exit 1
}

echo "Update completed successfully"
```

### Performance Optimization

#### Database Tuning
```sql
-- PostgreSQL performance tuning
-- Add to postgresql.conf

shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 16MB
maintenance_work_mem = 256MB
checkpoint_completion_target = 0.7
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200

-- Create performance indexes
CREATE INDEX CONCURRENTLY idx_events_timestamp ON events(timestamp);
CREATE INDEX CONCURRENTLY idx_metrics_name_timestamp ON metrics(metric_name, timestamp);
CREATE INDEX CONCURRENTLY idx_messages_session_sent ON messages(session_id, sent_at);
```

#### Redis Optimization
```conf
# redis.conf optimizations
maxmemory-policy allkeys-lru
tcp-keepalive 60
timeout 300

# Enable lazy freeing
lazyfree-lazy-eviction yes
lazyfree-lazy-expire yes
lazyfree-lazy-server-del yes
```

## Troubleshooting

### Quick Diagnostics
```bash
# Check Python version
python --version  # Should be 3.11+

# Verify dependencies
pip list | grep -E "aiohttp|websockets|watchdog"

# Test configuration
python -c "import production_config; print('Config OK')"

# Check API keys
python -c "import os; print('API keys set:', bool(os.getenv('ANTHROPIC_API_KEY')))"
```

### Common Issues and Solutions

#### Service Won't Start
```bash
# Check logs
tail -f logs/dashboard_production.log
docker-compose logs agent-orchestrator

# Common fixes
# 1. Port already in use
lsof -i :8765  # Check what's using the port
kill -9 $(lsof -t -i:8765)  # Kill the process

# 2. Permission issues
chmod -R 755 logs outputs checkpoints

# 3. Missing dependencies
pip install -r requirements.txt
pip install anthropic openai

# 4. Configuration issues
python production_dashboard.py --config production_config.json --debug
```

#### High Memory Usage
```bash
# Analyze memory usage
docker stats
htop

# Optimize Python memory
export PYTHONMALLOC=malloc
export MALLOC_TRIM_THRESHOLD_=100000

# Adjust pool sizes
export MAX_PARALLEL=10
export TOKEN_POOL_SIZE=15
export DB_MAX_CONNECTIONS=10
```

#### Database Performance Issues
```sql
-- Analyze slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;

-- Check table sizes
SELECT schemaname,tablename,attname,n_distinct,correlation
FROM pg_stats
WHERE schemaname = 'public'
ORDER BY n_distinct DESC;

-- Maintenance
VACUUM ANALYZE;
REINDEX DATABASE collaboration;
```

#### Dashboard Not Loading
```bash
# Check dashboard service
curl -f http://localhost:8765/api/health

# Check if web directory exists
ls -la web/  # Should contain index.html and other static files

# Test WebSocket connection
python -c "import websockets; print('WebSocket module OK')"

# Check firewall
sudo ufw status | grep 8765
sudo ufw allow 8765/tcp  # If needed

# Browser console errors
# Open browser developer tools (F12) and check Console tab for errors
```

### Debugging Procedures

#### Enable Debug Logging
```bash
# Temporary debug mode
export DEBUG=true
export LOG_LEVEL=DEBUG
python production_dashboard.py --config production_config.json

# Permanent debug configuration
# Edit production_config.json
{
  "log_level": "DEBUG",
  "enable_debug_endpoints": true
}
```

#### Performance Profiling
```python
# Add to production_dashboard.py for profiling
import cProfile
import pstats

def profile_endpoint():
    profiler = cProfile.Profile()
    profiler.enable()

    # Your code here

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats()
```

### Quick Recovery Steps
```bash
# 1. Stop everything
pkill -f production_dashboard
docker-compose down

# 2. Clean up
rm -rf logs/*.log
rm -rf outputs/temp_*

# 3. Reset configuration
cp .env.production .env

# 4. Restart services
python production_dashboard.py --config production_config.json
```

### Emergency Procedures

#### Emergency Shutdown
```bash
#!/bin/bash
# emergency-shutdown.sh

echo "EMERGENCY: Shutting down all services..."

# Stop application services
docker-compose down --timeout 30
sudo systemctl stop dashboard

# Stop databases (if running locally)
sudo systemctl stop postgresql
sudo systemctl stop redis

# Kill any remaining processes
pkill -f "python.*orchestrator"

echo "Emergency shutdown completed"
```

#### Emergency Recovery
```bash
#!/bin/bash
# emergency-recovery.sh

echo "Starting emergency recovery..."

# Start databases
sudo systemctl start postgresql
sudo systemctl start redis

# Wait for databases to be ready
sleep 10

# Start application in safe mode
export MAX_PARALLEL=1
export TOKEN_POOL_SIZE=5
python main.py --safe-mode

echo "Emergency recovery completed"
```

### Health Check Scripts

#### Comprehensive Health Check
```bash
#!/bin/bash
# health-check.sh

set -e

echo "=== Agent Orchestrator Health Check ==="

# Check service status
echo "Checking services..."
if systemctl is-active --quiet dashboard; then
    echo "✓ Dashboard service is running"
else
    echo "✗ Dashboard service is not running"
    exit 1
fi

# Check database connectivity
echo "Checking database..."
if psql collaboration -c "SELECT 1;" >/dev/null 2>&1; then
    echo "✓ PostgreSQL is accessible"
else
    echo "✗ PostgreSQL is not accessible"
    exit 1
fi

# Check Redis connectivity
echo "Checking Redis..."
if redis-cli ping >/dev/null 2>&1; then
    echo "✓ Redis is accessible"
else
    echo "✗ Redis is not accessible"
    exit 1
fi

# Check API endpoints
echo "Checking API endpoints..."
if curl -f http://localhost:8765/api/health >/dev/null 2>&1; then
    echo "✓ Dashboard API is responding"
else
    echo "✗ Dashboard API is not responding"
    exit 1
fi

# Check disk space
echo "Checking disk space..."
DISK_USAGE=$(df /opt/agent-orchestrator | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
    echo "✓ Disk usage is acceptable ($DISK_USAGE%)"
else
    echo "⚠ Disk usage is high ($DISK_USAGE%)"
fi

# Check memory usage
echo "Checking memory usage..."
MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
if [ "$MEMORY_USAGE" -lt 80 ]; then
    echo "✓ Memory usage is acceptable ($MEMORY_USAGE%)"
else
    echo "⚠ Memory usage is high ($MEMORY_USAGE%)"
fi

echo "=== Health check completed ==="
```

## Deployment Verification

### Post-Deployment Checklist

```bash
# 1. Verify service is running
curl http://localhost:8765/api/health
# Expected: {"status": "healthy", ...}

# 2. Check WebSocket connectivity
python -c "
import asyncio
import websockets
async def test():
    async with websockets.connect('ws://localhost:8765/ws') as ws:
        print('WebSocket connected successfully')
asyncio.run(test())
"

# 3. Verify logs are being written
ls -la logs/
tail -f logs/dashboard_production.log

# 4. Test a simple workflow
python run_orchestrator_task.py \
  --app-name "test-app" \
  --app-root "." \
  --task-type "system-documentation"

# 5. Monitor resource usage
ps aux | grep production_dashboard
df -h outputs/
```

### Production Readiness Checklist

- [ ] API keys configured (ANTHROPIC_API_KEY, OPENAI_API_KEY)
- [ ] Appropriate resource limits set (MAX_PARALLEL, TOKEN_POOL_SIZE)
- [ ] Log rotation configured
- [ ] Backup strategy in place
- [ ] Monitoring endpoints accessible
- [ ] SSL/TLS configured (for production)
- [ ] Firewall rules configured
- [ ] Health checks passing
- [ ] Error alerting configured
- [ ] Documentation updated

## Support and Documentation

### Additional Resources
- **Architecture Documentation**: [ARCHITECTURE.md](./ARCHITECTURE.md)
- **API Reference**: [API_REFERENCE.md](./API_REFERENCE.md)
- **User Guide**: [USER_GUIDE.md](./USER_GUIDE.md)
- **Developer Guide**: [DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md)

### Getting Help
- **GitHub Issues**: Report bugs and request features
- **Documentation**: Check the docs/ directory for detailed guides
- **Logs**: Always include relevant logs when reporting issues
- **Health Checks**: Run health checks before reporting problems

---

This deployment guide provides comprehensive instructions for deploying and maintaining the Agent Orchestrator system in various environments. For additional support or specific deployment scenarios, please refer to the other documentation files or create an issue in the project repository.
