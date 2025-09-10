# Project Context MCP Server - Production Deployment Guide

**Version**: 0.1.0
**Date**: January 2025

## 🚀 Quick Start

### Prerequisites

- Docker Engine 20.10+ with Docker Compose v2
- Minimum 4GB RAM, 2 CPU cores
- 10GB free disk space
- SSL certificates (for HTTPS)

### 1. Clone and Configure

```bash
# Clone the repository
git clone https://github.com/your-org/project-context.git
cd project-context

# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env
```

### 2. Configure Environment

**Required Variables:**
```bash
# Database credentials
DB_PASSWORD=your_secure_db_password_here
REDIS_PASSWORD=your_secure_redis_password_here

# API Security
API_KEY=your_api_key_here_min_32_chars_long

# SSL/Domain
LETSENCRYPT_EMAIL=admin@yourdomain.com
LETSENCRYPT_DOMAIN=your-domain.com

# Monitoring
GRAFANA_ADMIN_PASSWORD=secure_grafana_admin_password
```

### 3. Deploy with Docker Compose

```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Check service status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f project-context
```

### 4. Verify Deployment

```bash
# Health check
curl -k https://your-domain.com/health

# API test
curl -X POST https://your-domain.com/api/tools/get_project_summary \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}'
```

## 📋 Detailed Setup

### System Requirements

#### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 4GB
- **Storage**: 10GB SSD
- **Network**: 1Gbps
- **OS**: Ubuntu 20.04+ / RHEL 8+ / Docker-compatible Linux

#### Recommended Requirements
- **CPU**: 4+ cores
- **RAM**: 8GB+
- **Storage**: 50GB+ SSD
- **Network**: 1Gbps+
- **Load Balancer**: Nginx/HAProxy

#### High-Availability Requirements
- **CPU**: 8+ cores per node
- **RAM**: 16GB+ per node
- **Storage**: 100GB+ SSD with replication
- **Network**: 10Gbps backbone
- **Nodes**: 3+ nodes with orchestration

### Infrastructure Setup

#### 1. Server Preparation

**Ubuntu/Debian:**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Configure firewall
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
```

**RHEL/CentOS:**
```bash
# Update system
sudo yum update -y

# Install Docker
sudo yum install -y yum-utils device-mapper-persistent-data lvm2
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install -y docker-ce docker-ce-cli containerd.io
sudo systemctl enable docker
sudo systemctl start docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Configure firewall
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

#### 2. Directory Structure

```bash
mkdir -p /opt/project-context/{data,logs,ssl,backups}
cd /opt/project-context

# Set proper permissions
sudo chown -R $USER:docker /opt/project-context
chmod 755 /opt/project-context
```

#### 3. SSL Certificates

**Option A: Let's Encrypt (Recommended)**
```bash
# Install certbot
sudo apt install certbot

# Generate certificates
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/key.pem

# Generate DH parameters
sudo openssl dhparam -out ssl/dhparam.pem 2048
```

**Option B: Self-Signed (Development)**
```bash
# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/key.pem \
  -out ssl/cert.pem \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# Generate DH parameters
openssl dhparam -out ssl/dhparam.pem 2048
```

### Environment Configuration

#### Core Settings

```bash
# Application
APP_PORT=3000
INTEL_DIR=/app/data/.proj-intel
CACHE_ENABLED=true
WATCH_ENABLED=true

# Performance
WORKERS=auto
CACHE_TTL=300
FILE_DATA_TTL=60
PROJECT_STATS_TTL=300

# Security
API_KEY=your_32_char_min_api_key_here
CORS_ORIGINS=https://your-domain.com
RATE_LIMIT_PER_MINUTE=1000

# Monitoring
PROMETHEUS_ENABLED=true
LOG_LEVEL=INFO
```

#### Database Configuration

```bash
# PostgreSQL with TimescaleDB
DB_NAME=unified_context
DB_USER=opsvi
DB_PASSWORD=secure_password_here
DB_HOST=postgres
DB_PORT=5432

# Connection pooling
DB_MIN_CONNECTIONS=5
DB_MAX_CONNECTIONS=20
DB_CONNECTION_TIMEOUT=60
```

#### Cache Configuration

```bash
# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=secure_redis_password
REDIS_MAX_CONNECTIONS=10
```

### Service Configuration

#### 1. Start Core Services

```bash
# Start databases first
docker-compose -f docker-compose.prod.yml up -d postgres redis

# Wait for databases to be ready
docker-compose -f docker-compose.prod.yml logs -f postgres | grep "database system is ready"

# Initialize database
docker-compose -f docker-compose.prod.yml up -d timescaledb-init
```

#### 2. Start Application Services

```bash
# Start main application
docker-compose -f docker-compose.prod.yml up -d project-context

# Start monitoring
docker-compose -f docker-compose.prod.yml up -d prometheus grafana

# Start reverse proxy
docker-compose -f docker-compose.prod.yml up -d nginx
```

#### 3. Verify Services

```bash
# Check all services
docker-compose -f docker-compose.prod.yml ps

# Expected output:
# NAME                          COMMAND                  SERVICE             STATUS              PORTS
# project-context-grafana       "/run.sh"                grafana             running             0.0.0.0:3001->3000/tcp
# project-context-nginx         "/docker-entrypoint.…"   nginx               running             0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
# project-context-postgres      "docker-entrypoint.s…"   postgres            running             0.0.0.0:5432->5432/tcp
# project-context-prometheus    "/bin/prometheus --c…"   prometheus          running             0.0.0.0:9090->9090/tcp
# project-context-redis         "docker-entrypoint.s…"   redis               running             0.0.0.0:6379->6379/tcp
# project-context-server        "./entrypoint.sh"       project-context     running             0.0.0.0:3000->3000/tcp, 0.0.0.0:8080->8080/tcp
```

### Post-Deployment Verification

#### 1. Health Checks

```bash
# Application health
curl -k https://localhost/health

# Expected response:
{
  "status": "healthy",
  "version": "0.1.0",
  "services": {
    "database": "connected",
    "redis": "connected",
    "file_system": "accessible"
  }
}

# Database health
docker-compose exec postgres pg_isready -U opsvi -d unified_context

# Redis health
docker-compose exec redis redis-cli ping
```

#### 2. API Testing

```bash
# Test project summary endpoint
curl -X POST https://localhost/api/tools/get_project_summary \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"include_metrics": true}'

# Test file discovery
curl -X POST https://localhost/api/tools/find_files \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"pattern": "*.py", "max_results": 10}'
```

#### 3. Performance Testing

```bash
# Load test with Apache Bench
ab -n 100 -c 10 -H "Authorization: Bearer YOUR_API_KEY" \
   -H "Content-Type: application/json" \
   -p test_payload.json \
   https://localhost/api/tools/get_project_summary

# Monitor resource usage
docker-compose -f docker-compose.prod.yml exec project-context top
```

### Monitoring Setup

#### 1. Access Grafana Dashboard

```bash
# URL: https://dashboard.your-domain.com
# Username: admin
# Password: (from GRAFANA_ADMIN_PASSWORD)
```

#### 2. Configure Dashboards

1. Import provided dashboard configurations from `monitoring/grafana/dashboard-configs/`
2. Verify data source connection to Prometheus
3. Set up alerting channels (Slack, email, PagerDuty)

#### 3. Key Metrics to Monitor

- **Application**: Response time, error rate, throughput
- **Database**: Connection count, query performance, disk usage
- **Cache**: Hit rate, memory usage, eviction rate
- **System**: CPU, memory, disk, network utilization

### Backup Configuration

#### 1. Automated Backups

```bash
# Run initial backup test
docker-compose -f docker-compose.prod.yml run --rm db-backup

# Schedule daily backups (add to crontab)
0 2 * * * cd /opt/project-context && docker-compose -f docker-compose.prod.yml run --rm db-backup
```

#### 2. Backup Verification

```bash
# List backup files
ls -la database/backups/

# Test backup integrity
docker-compose -f docker-compose.prod.yml exec postgres pg_restore --list database/backups/postgres_backup_YYYYMMDD_HHMMSS.sql.gz
```

### Security Hardening

#### 1. Network Security

```bash
# Configure firewall rules
sudo ufw deny 5432  # PostgreSQL
sudo ufw deny 6379  # Redis
sudo ufw deny 9090  # Prometheus
sudo ufw allow from 10.0.0.0/8 to any port 9090  # Internal monitoring
```

#### 2. Container Security

```bash
# Scan for vulnerabilities
docker scan project-context:latest

# Update base images regularly
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

#### 3. Access Control

```bash
# Rotate API keys regularly
# Update .env file with new API_KEY
# Restart services
docker-compose -f docker-compose.prod.yml restart project-context
```

### Troubleshooting

#### Common Issues

**1. Service Won't Start**
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs project-context

# Common causes:
# - Database not ready
# - Missing environment variables
# - Port conflicts
# - Insufficient resources
```

**2. Database Connection Issues**
```bash
# Test database connectivity
docker-compose -f docker-compose.prod.yml exec project-context pg_isready -h postgres -U opsvi

# Check database logs
docker-compose -f docker-compose.prod.yml logs postgres
```

**3. High Memory Usage**
```bash
# Monitor container resource usage
docker stats

# Adjust worker count
# Set WORKERS=2 in .env for smaller instances
```

**4. SSL Certificate Issues**
```bash
# Verify certificate validity
openssl x509 -in ssl/cert.pem -text -noout

# Test SSL configuration
openssl s_client -connect localhost:443
```

### Scaling

#### Horizontal Scaling

```bash
# Scale application containers
docker-compose -f docker-compose.prod.yml up -d --scale project-context=3

# Add load balancer configuration
# Update nginx.conf with additional upstream servers
```

#### Database Scaling

```bash
# Configure read replicas
# Add read-only database instances
# Update connection strings for read operations
```

### Maintenance

#### Regular Tasks

**Daily:**
- Monitor service health
- Check backup completion
- Review error logs

**Weekly:**
- Review performance metrics
- Update security patches
- Clean up old logs

**Monthly:**
- Update container images
- Review and rotate credentials
- Performance optimization review

#### Updates

```bash
# Update application
git pull origin main
docker-compose -f docker-compose.prod.yml build project-context
docker-compose -f docker-compose.prod.yml up -d project-context

# Update monitoring
docker-compose -f docker-compose.prod.yml pull prometheus grafana
docker-compose -f docker-compose.prod.yml up -d prometheus grafana
```

### Support

- **Documentation**: https://docs.your-domain.com
- **Issues**: https://github.com/your-org/project-context/issues
- **Discord**: https://discord.gg/your-server
- **Email**: support@your-domain.com

---

**⚠️ Important Security Notes:**

1. Change all default passwords
2. Use strong API keys (32+ characters)
3. Keep SSL certificates up to date
4. Regular security updates
5. Monitor access logs for suspicious activity
6. Use network segmentation in production
7. Implement proper backup encryption
8. Follow principle of least privilege
