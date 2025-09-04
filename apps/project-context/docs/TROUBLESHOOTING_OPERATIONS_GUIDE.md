# Troubleshooting & Operations Guide

**Version**: 1.0.0
**Status**: ✅ **PRODUCTION READY**
**Date**: September 4, 2025

---

## 🎯 Overview

This comprehensive troubleshooting and operations guide covers **production deployment, monitoring, maintenance, and issue resolution** for the Unified Context System Phase 1. It provides actionable solutions for common issues, performance optimization strategies, and operational best practices.

---

## 🔧 Quick Diagnostic Commands

### System Health Check
```bash
# One-command health check
curl -k https://localhost/health | jq '.'

# Expected healthy response:
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "database": "connected",
    "redis": "connected",
    "file_system": "accessible"
  },
  "uptime": "2h 15m 30s"
}
```

### Service Status Check
```bash
# Docker Compose deployment
docker-compose -f docker-compose.prod.yml ps

# Kubernetes deployment
kubectl get pods -n production -l app=project-context

# Check logs quickly
docker-compose -f docker-compose.prod.yml logs --tail=50 project-context
```

### Database Connectivity Test
```bash
# PostgreSQL connection test
docker-compose -f docker-compose.prod.yml exec postgres pg_isready -U opsvi -d unified_context

# Redis connection test
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping

# Connection pool status
curl -k https://localhost/health/database | jq '.connection_pool'
```

---

## 🚨 Common Issues & Solutions

### 1. Service Won't Start

#### Symptoms
- Container exits immediately
- "Connection refused" errors
- Health check failures

#### Diagnostic Steps
```bash
# Check container logs
docker-compose -f docker-compose.prod.yml logs project-context

# Check resource usage
docker stats --no-stream

# Verify environment variables
docker-compose -f docker-compose.prod.yml config

# Check port conflicts
netstat -tlnp | grep :3000
```

#### Common Causes & Solutions

**Missing Environment Variables**
```bash
# Check required variables
grep -E '^[A-Z_]+=.*' .env

# Required variables checklist:
API_KEY=             # Must be 32+ characters
DB_PASSWORD=         # Database password
REDIS_PASSWORD=      # Redis password
DATABASE_URL=        # Complete database URL
```

**Database Not Ready**
```bash
# Wait for database to be ready
docker-compose -f docker-compose.prod.yml up -d postgres
sleep 30

# Check database logs
docker-compose -f docker-compose.prod.yml logs postgres | grep "ready"

# Initialize database if needed
docker-compose -f docker-compose.prod.yml run --rm db-init
```

**Port Conflicts**
```bash
# Find process using port 3000
sudo lsof -i :3000

# Kill conflicting process
sudo kill -9 <PID>

# Or change port in docker-compose.yml
ports:
  - "3001:3000"  # Use different external port
```

**Insufficient Resources**
```bash
# Check available resources
free -h
df -h

# Increase memory limits in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G
      cpus: '2'
```

### 2. Database Connection Issues

#### Symptoms
- "Connection pool exhausted" errors
- Slow query responses
- Database timeout errors

#### Diagnostic Commands
```bash
# Check connection pool status
psql -h localhost -U opsvi -d unified_context -c "
SELECT
  count(*) as total_connections,
  count(*) FILTER (WHERE state = 'active') as active,
  count(*) FILTER (WHERE state = 'idle') as idle
FROM pg_stat_activity
WHERE datname = 'unified_context';"

# Check slow queries
psql -h localhost -U opsvi -d unified_context -c "
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC LIMIT 10;"

# Check database size and table statistics
psql -h localhost -U opsvi -d unified_context -c "
SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del
FROM pg_stat_user_tables
ORDER BY n_tup_ins DESC;"
```

#### Solutions

**Connection Pool Exhaustion**
```bash
# Increase connection pool size in .env
DB_POOL_MAX=50
DB_POOL_MIN=10
DB_CONNECTION_TIMEOUT=120

# Restart services
docker-compose -f docker-compose.prod.yml restart project-context
```

**Slow Queries**
```sql
-- Add missing indexes
CREATE INDEX CONCURRENTLY idx_context_items_timestamp
ON context_items(timestamp);

CREATE INDEX CONCURRENTLY idx_context_items_source_type
ON context_items(source_type, timestamp);

-- Update table statistics
ANALYZE context_items;
ANALYZE context_relationships;
```

**Database Locks**
```sql
-- Check for blocking queries
SELECT
  blocked_locks.pid AS blocked_pid,
  blocked_activity.usename AS blocked_user,
  blocking_locks.pid AS blocking_pid,
  blocking_activity.usename AS blocking_user,
  blocked_activity.query AS blocked_statement,
  blocking_activity.query AS blocking_statement
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity
  ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks
  ON blocking_locks.locktype = blocked_locks.locktype
JOIN pg_catalog.pg_stat_activity blocking_activity
  ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;

-- Kill blocking query if necessary
SELECT pg_terminate_backend(<blocking_pid>);
```

### 3. High Memory Usage

#### Symptoms
- Out of memory errors
- Container restarts
- System slowdown

#### Memory Diagnosis
```bash
# Check container memory usage
docker stats --no-stream

# Check system memory
free -h
cat /proc/meminfo

# Check memory usage by process inside container
docker-compose -f docker-compose.prod.yml exec project-context top -o %MEM
```

#### Memory Optimization

**Application Level**
```bash
# Reduce worker count in .env
WORKERS=2  # Instead of auto/4

# Reduce batch sizes
BATCH_SIZE=500  # Instead of 1000
CACHE_SIZE=500MB  # Instead of 1GB

# Enable garbage collection optimization
PYTHONHASHSEED=0
PYTHONUNBUFFERED=1
```

**Database Level**
```sql
-- Reduce shared_buffers if needed
ALTER SYSTEM SET shared_buffers = '256MB';

-- Reduce work_mem for complex queries
ALTER SYSTEM SET work_mem = '4MB';

-- Clean up old data
DELETE FROM context_items
WHERE timestamp < NOW() - INTERVAL '90 days'
  AND source_type NOT IN ('critical', 'system');

-- Vacuum and analyze
VACUUM ANALYZE;
```

**Container Level**
```yaml
# In docker-compose.yml
services:
  project-context:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
    environment:
      - MALLOC_ARENA_MAX=2  # Reduce memory fragmentation
```

### 4. Performance Issues

#### Symptoms
- Slow API responses (>5 seconds)
- High CPU usage
- Request timeouts

#### Performance Diagnosis
```bash
# Monitor API response times
curl -w "@curl-format.txt" -s -o /dev/null https://localhost/health

# curl-format.txt:
#      time_namelookup:  %{time_namelookup}\n
#         time_connect:  %{time_connect}\n
#      time_appconnect:  %{time_appconnect}\n
#     time_pretransfer:  %{time_pretransfer}\n
#        time_redirect:  %{time_redirect}\n
#   time_starttransfer:  %{time_starttransfer}\n
#                      ----------\n
#           time_total:  %{time_total}\n

# Check database query performance
psql -h localhost -U opsvi -d unified_context -c "
SELECT
  query,
  calls,
  total_time,
  mean_time,
  stddev_time
FROM pg_stat_statements
WHERE mean_time > 1000  -- Queries slower than 1 second
ORDER BY mean_time DESC
LIMIT 10;"

# Check cache hit rates
curl -s https://localhost/health/cache | jq '.hit_rate'
```

#### Performance Optimization

**Database Optimization**
```sql
-- Refresh materialized views if stale
REFRESH MATERIALIZED VIEW CONCURRENTLY relationship_analytics;
REFRESH MATERIALIZED VIEW CONCURRENTLY context_metrics_hourly;

-- Update query planner statistics
ANALYZE context_items;

-- Check for missing indexes
SELECT
  schemaname,
  tablename,
  attname,
  n_distinct,
  correlation
FROM pg_stats
WHERE schemaname = 'public'
  AND n_distinct > 100;  -- Columns that might need indexes
```

**Application Optimization**
```bash
# Enable all caching in .env
CACHE_ENABLED=true
REDIS_CACHE_TTL=3600
MEMORY_CACHE_SIZE=256MB

# Optimize worker configuration
WORKERS=4  # Match CPU cores
WORKER_CONNECTIONS=1000
WORKER_CLASS=uvicorn.workers.UvicornWorker

# Enable compression
GZIP_ENABLED=true
GZIP_MIN_SIZE=1000
```

**Infrastructure Optimization**
```bash
# Add more CPU/memory if needed
# Update docker-compose.yml:
deploy:
  resources:
    limits:
      cpus: '4.0'
      memory: 4G

# Enable parallel processing
PARALLEL_WORKERS=4
ASYNC_PROCESSING=true
BATCH_PROCESSING=true
```

### 5. Cache Issues

#### Symptoms
- Low cache hit rates (<80%)
- Redis connection errors
- Slow repeated queries

#### Cache Diagnosis
```bash
# Check Redis connectivity
redis-cli -h localhost -p 6379 -a ${REDIS_PASSWORD} ping

# Check cache statistics
redis-cli -h localhost -p 6379 -a ${REDIS_PASSWORD} info stats

# Check cache hit rate
curl -s https://localhost/health/cache | jq '{hit_rate, total_requests, hits, misses}'

# Check cache memory usage
redis-cli -h localhost -p 6379 -a ${REDIS_PASSWORD} info memory
```

#### Cache Optimization

**Redis Configuration**
```bash
# In docker-compose.yml, optimize Redis
redis:
  image: redis:7-alpine
  command: redis-server --maxmemory 1gb --maxmemory-policy allkeys-lru
  sysctls:
    - net.core.somaxconn=65535
```

**Cache Settings**
```bash
# In .env, optimize cache settings
CACHE_TTL=3600          # 1 hour for most data
FILE_DATA_TTL=300       # 5 minutes for file data
PROJECT_STATS_TTL=1800  # 30 minutes for project stats
CACHE_WARM_ON_START=true
```

**Cache Warming**
```python
# Cache warming script
async def warm_cache():
    """Warm frequently accessed cache entries"""
    client = ProjectContextClient(base_url, api_key)

    # Warm project summary
    await client.get_project_summary()

    # Warm common file searches
    await client.find_files("*.py")
    await client.find_files("*.js")
    await client.find_files("*.md")

    print("Cache warming completed")
```

### 6. Disk Space Issues

#### Symptoms
- "No space left on device" errors
- Backup failures
- Log rotation issues

#### Disk Space Management
```bash
# Check disk usage
df -h

# Check largest directories
du -sh /* | sort -hr | head -10

# Check Docker space usage
docker system df

# Clean up Docker
docker system prune -a --volumes

# Check log file sizes
find /var/log -type f -name "*.log" -exec ls -lh {} \; | sort -k5 -hr
```

#### Automated Cleanup
```bash
# Create cleanup script
cat > /usr/local/bin/cleanup-project-context.sh << 'EOF'
#!/bin/bash

# Clean old Docker images
docker image prune -a -f --filter "until=168h"

# Clean old logs (keep 30 days)
find /var/log/project-context -type f -mtime +30 -delete

# Clean old database backups (keep 60 days)
find /opt/project-context/backups -type f -mtime +60 -delete

# Clean old context_items (keep 90 days)
psql -h localhost -U opsvi -d unified_context -c "
DELETE FROM context_items
WHERE timestamp < NOW() - INTERVAL '90 days'
  AND source_type NOT IN ('critical', 'system');"

echo "Cleanup completed: $(date)"
EOF

chmod +x /usr/local/bin/cleanup-project-context.sh

# Add to crontab (run weekly)
echo "0 2 * * 0 /usr/local/bin/cleanup-project-context.sh" | crontab -
```

---

## 📊 Monitoring & Alerting

### Key Metrics to Monitor

#### Application Metrics
```bash
# API response times
curl -w "%{time_total}" -s -o /dev/null https://localhost/health

# Request rates
curl -s https://localhost/metrics | grep http_requests_total

# Error rates
curl -s https://localhost/metrics | grep http_requests_total | grep 5xx
```

#### Database Metrics
```sql
-- Connection usage
SELECT count(*) as connections, state
FROM pg_stat_activity
WHERE datname = 'unified_context'
GROUP BY state;

-- Query performance
SELECT
  query,
  calls,
  total_time/calls as avg_time,
  rows/calls as avg_rows
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 5;

-- Table sizes
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

#### System Metrics
```bash
# CPU and memory usage
top -bn1 | head -20

# Disk I/O
iostat -x 1 5

# Network usage
netstat -i
```

### Grafana Dashboards

#### Application Dashboard
```json
{
  "dashboard": {
    "title": "Project Context - Application Metrics",
    "panels": [
      {
        "title": "API Response Time",
        "targets": [{
          "expr": "histogram_quantile(0.95, http_request_duration_seconds_bucket)"
        }]
      },
      {
        "title": "Request Rate",
        "targets": [{
          "expr": "rate(http_requests_total[5m])"
        }]
      },
      {
        "title": "Error Rate",
        "targets": [{
          "expr": "rate(http_requests_total{code=~'5..'}[5m])"
        }]
      },
      {
        "title": "Cache Hit Rate",
        "targets": [{
          "expr": "cache_hits_total / (cache_hits_total + cache_misses_total)"
        }]
      }
    ]
  }
}
```

#### Database Dashboard
```json
{
  "dashboard": {
    "title": "Project Context - Database Metrics",
    "panels": [
      {
        "title": "Connection Usage",
        "targets": [{
          "expr": "pg_stat_activity_count"
        }]
      },
      {
        "title": "Query Performance",
        "targets": [{
          "expr": "pg_stat_statements_mean_time_seconds"
        }]
      },
      {
        "title": "Database Size",
        "targets": [{
          "expr": "pg_database_size_bytes"
        }]
      }
    ]
  }
}
```

### Alerting Rules

#### Prometheus Alerts
```yaml
# alerts.yml
groups:
  - name: project-context-alerts
    rules:

    # High response time
    - alert: HighResponseTime
      expr: histogram_quantile(0.95, http_request_duration_seconds_bucket) > 5
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High API response time"
        description: "95th percentile response time is {{ $value }}s"

    # High error rate
    - alert: HighErrorRate
      expr: rate(http_requests_total{code=~"5.."}[5m]) > 0.1
      for: 2m
      labels:
        severity: critical
      annotations:
        summary: "High error rate detected"
        description: "Error rate is {{ $value }} errors/second"

    # Database connection issues
    - alert: DatabaseConnectionsHigh
      expr: pg_stat_activity_count > 80
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High database connection usage"
        description: "{{ $value }} connections active"

    # Low cache hit rate
    - alert: LowCacheHitRate
      expr: cache_hit_rate < 0.8
      for: 10m
      labels:
        severity: warning
      annotations:
        summary: "Low cache hit rate"
        description: "Cache hit rate is {{ $value }}"

    # High memory usage
    - alert: HighMemoryUsage
      expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.9
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "High memory usage"
        description: "Memory usage is {{ $value }}%"
```

#### Slack Notifications
```python
# slack_notifier.py
import asyncio
import aiohttp
import json

class SlackNotifier:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    async def send_alert(self, alert_name, message, severity="warning"):
        color = {
            "critical": "#FF0000",
            "warning": "#FFA500",
            "info": "#00FF00"
        }.get(severity, "#CCCCCC")

        payload = {
            "attachments": [{
                "color": color,
                "title": f"🚨 {alert_name}",
                "text": message,
                "footer": "Project Context Monitoring",
                "ts": int(time.time())
            }]
        }

        async with aiohttp.ClientSession() as session:
            await session.post(
                self.webhook_url,
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'}
            )

# Usage in alerting script
notifier = SlackNotifier("https://hooks.slack.com/services/YOUR/WEBHOOK/URL")

async def check_and_alert():
    # Check API health
    try:
        response = await check_api_health()
        if response.status_code != 200:
            await notifier.send_alert(
                "API Health Check Failed",
                f"API returned status code {response.status_code}",
                "critical"
            )
    except Exception as e:
        await notifier.send_alert(
            "API Unreachable",
            f"Failed to connect to API: {str(e)}",
            "critical"
        )
```

---

## 🔄 Backup & Recovery

### Automated Backup System

#### Database Backups
```bash
# Create backup script
cat > /usr/local/bin/backup-database.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/opt/project-context/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/postgres_backup_${TIMESTAMP}.sql.gz"

# Ensure backup directory exists
mkdir -p ${BACKUP_DIR}

# Create database backup
pg_dump -h localhost -U opsvi -d unified_context | gzip > ${BACKUP_FILE}

# Verify backup
if [ -f "${BACKUP_FILE}" ] && [ -s "${BACKUP_FILE}" ]; then
    echo "Backup successful: ${BACKUP_FILE}"

    # Keep only last 30 backups
    ls -t ${BACKUP_DIR}/postgres_backup_*.sql.gz | tail -n +31 | xargs -r rm

    # Log backup size
    SIZE=$(du -h ${BACKUP_FILE} | cut -f1)
    echo "Backup size: ${SIZE}"

    # Test backup integrity
    zcat ${BACKUP_FILE} | head -10 > /dev/null
    if [ $? -eq 0 ]; then
        echo "Backup integrity check passed"
    else
        echo "WARNING: Backup integrity check failed"
        exit 1
    fi
else
    echo "ERROR: Backup failed or file is empty"
    exit 1
fi
EOF

chmod +x /usr/local/bin/backup-database.sh

# Schedule daily backups
echo "0 2 * * * /usr/local/bin/backup-database.sh >> /var/log/backup.log 2>&1" | crontab -
```

#### Application Data Backup
```bash
# Create application backup script
cat > /usr/local/bin/backup-app-data.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/opt/project-context/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
APP_BACKUP_FILE="${BACKUP_DIR}/app_data_${TIMESTAMP}.tar.gz"

# Backup application data
tar -czf ${APP_BACKUP_FILE} \
    -C /opt/project-context \
    data/ \
    .env \
    docker-compose.prod.yml \
    ssl/ \
    logs/ \
    --exclude='data/cache/*' \
    --exclude='logs/*.log'

# Verify backup
if [ -f "${APP_BACKUP_FILE}" ] && [ -s "${APP_BACKUP_FILE}" ]; then
    echo "Application backup successful: ${APP_BACKUP_FILE}"

    # Keep only last 7 application backups
    ls -t ${BACKUP_DIR}/app_data_*.tar.gz | tail -n +8 | xargs -r rm
else
    echo "ERROR: Application backup failed"
    exit 1
fi
EOF

chmod +x /usr/local/bin/backup-app-data.sh

# Schedule weekly application backups
echo "0 3 * * 0 /usr/local/bin/backup-app-data.sh >> /var/log/backup.log 2>&1" | crontab -
```

### Recovery Procedures

#### Database Recovery
```bash
# Full database restore
restore_database() {
    BACKUP_FILE=$1

    if [ -z "$BACKUP_FILE" ]; then
        echo "Usage: restore_database <backup_file>"
        return 1
    fi

    if [ ! -f "$BACKUP_FILE" ]; then
        echo "Backup file not found: $BACKUP_FILE"
        return 1
    fi

    echo "Starting database restore from: $BACKUP_FILE"

    # Stop application to prevent new connections
    docker-compose -f docker-compose.prod.yml stop project-context

    # Drop and recreate database
    psql -h localhost -U opsvi -d postgres -c "DROP DATABASE IF EXISTS unified_context;"
    psql -h localhost -U opsvi -d postgres -c "CREATE DATABASE unified_context;"

    # Restore from backup
    if [[ $BACKUP_FILE == *.gz ]]; then
        zcat $BACKUP_FILE | psql -h localhost -U opsvi -d unified_context
    else
        psql -h localhost -U opsvi -d unified_context < $BACKUP_FILE
    fi

    # Restart application
    docker-compose -f docker-compose.prod.yml start project-context

    echo "Database restore completed"
}

# Point-in-time recovery (if WAL archiving is enabled)
pitr_recovery() {
    TARGET_TIME=$1

    # Stop database
    docker-compose -f docker-compose.prod.yml stop postgres

    # Restore from base backup and replay WAL files
    # This requires WAL archiving to be configured
    pg_restore --create --clean --if-exists --target-time="$TARGET_TIME" base_backup.tar

    # Restart database
    docker-compose -f docker-compose.prod.yml start postgres
}
```

#### Application Recovery
```bash
# Application configuration restore
restore_application() {
    BACKUP_FILE=$1

    if [ -z "$BACKUP_FILE" ]; then
        echo "Usage: restore_application <app_backup_file>"
        return 1
    fi

    echo "Restoring application from: $BACKUP_FILE"

    # Stop services
    docker-compose -f docker-compose.prod.yml down

    # Create backup of current state
    mv /opt/project-context /opt/project-context.backup.$(date +%Y%m%d_%H%M%S)

    # Extract backup
    mkdir -p /opt/project-context
    tar -xzf $BACKUP_FILE -C /opt/project-context

    # Restore permissions
    chown -R $(whoami):docker /opt/project-context

    # Start services
    cd /opt/project-context
    docker-compose -f docker-compose.prod.yml up -d

    echo "Application restore completed"
}
```

### Disaster Recovery

#### Complete System Recovery
```bash
# Complete disaster recovery procedure
disaster_recovery() {
    echo "Starting disaster recovery procedure..."

    # 1. Prepare new system
    setup_new_system() {
        # Install Docker and dependencies
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh

        # Install Docker Compose
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose

        # Create directory structure
        mkdir -p /opt/project-context/{data,logs,ssl,backups}
    }

    # 2. Restore application
    restore_from_backups() {
        # Find latest backups
        LATEST_DB_BACKUP=$(ls -t /backup-source/postgres_backup_*.sql.gz | head -1)
        LATEST_APP_BACKUP=$(ls -t /backup-source/app_data_*.tar.gz | head -1)

        echo "Restoring from:"
        echo "  Database: $LATEST_DB_BACKUP"
        echo "  Application: $LATEST_APP_BACKUP"

        # Restore application first
        restore_application $LATEST_APP_BACKUP

        # Wait for database to be ready
        sleep 30

        # Restore database
        restore_database $LATEST_DB_BACKUP
    }

    # 3. Verify system
    verify_recovery() {
        echo "Verifying system recovery..."

        # Check services
        docker-compose -f docker-compose.prod.yml ps

        # Check API health
        sleep 60  # Wait for full startup
        curl -f https://localhost/health || {
            echo "Health check failed"
            return 1
        }

        # Run basic functionality tests
        curl -X POST https://localhost/api/tools/get_project_summary \
            -H "Authorization: Bearer $API_KEY" \
            -H "Content-Type: application/json" \
            -d '{}' || {
            echo "API functionality test failed"
            return 1
        }

        echo "Recovery verification completed successfully"
    }

    # Execute recovery steps
    setup_new_system
    restore_from_backups
    verify_recovery

    echo "Disaster recovery completed"
}
```

---

## 🔧 Maintenance Procedures

### Regular Maintenance Tasks

#### Daily Tasks
```bash
# Create daily maintenance script
cat > /usr/local/bin/daily-maintenance.sh << 'EOF'
#!/bin/bash

echo "Starting daily maintenance: $(date)"

# Check service health
curl -s https://localhost/health > /dev/null || {
    echo "WARNING: Health check failed"
    # Attempt restart
    docker-compose -f /opt/project-context/docker-compose.prod.yml restart project-context
}

# Check disk space
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "WARNING: Disk usage is ${DISK_USAGE}%"
    # Run cleanup
    /usr/local/bin/cleanup-project-context.sh
fi

# Check log file sizes
find /opt/project-context/logs -name "*.log" -size +100M -exec truncate -s 50M {} \;

# Refresh materialized views
psql -h localhost -U opsvi -d unified_context -c "
REFRESH MATERIALIZED VIEW CONCURRENTLY relationship_analytics;
REFRESH MATERIALIZED VIEW CONCURRENTLY context_metrics_hourly;
"

echo "Daily maintenance completed: $(date)"
EOF

chmod +x /usr/local/bin/daily-maintenance.sh

# Schedule daily maintenance
echo "0 1 * * * /usr/local/bin/daily-maintenance.sh >> /var/log/maintenance.log 2>&1" | crontab -
```

#### Weekly Tasks
```bash
# Create weekly maintenance script
cat > /usr/local/bin/weekly-maintenance.sh << 'EOF'
#!/bin/bash

echo "Starting weekly maintenance: $(date)"

# Update container images
cd /opt/project-context
docker-compose -f docker-compose.prod.yml pull

# Database maintenance
psql -h localhost -U opsvi -d unified_context << SQL
-- Analyze all tables
ANALYZE;

-- Reindex if needed
REINDEX INDEX CONCURRENTLY context_items_timestamp_idx;

-- Update statistics
UPDATE pg_stat_statements_reset();

-- Check for unused indexes
SELECT
  schemaname,
  tablename,
  indexname,
  idx_scan,
  pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND pg_relation_size(indexrelid) > 1024*1024; -- Larger than 1MB

SQL

# Clean up old Docker resources
docker system prune -f --filter "until=168h"

# Rotate logs
find /opt/project-context/logs -name "*.log" -mtime +7 -exec gzip {} \;
find /opt/project-context/logs -name "*.log.gz" -mtime +30 -delete

# Security updates
apt list --upgradable 2>/dev/null | grep -i security

echo "Weekly maintenance completed: $(date)"
EOF

chmod +x /usr/local/bin/weekly-maintenance.sh

# Schedule weekly maintenance
echo "0 2 * * 0 /usr/local/bin/weekly-maintenance.sh >> /var/log/maintenance.log 2>&1" | crontab -
```

#### Monthly Tasks
```bash
# Create monthly maintenance script
cat > /usr/local/bin/monthly-maintenance.sh << 'EOF'
#!/bin/bash

echo "Starting monthly maintenance: $(date)"

# Full database maintenance
psql -h localhost -U opsvi -d unified_context << SQL
-- Full vacuum analyze
VACUUM ANALYZE;

-- Update planner statistics
ANALYZE;

-- Check table bloat
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
  pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) as index_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

SQL

# Archive old data
ARCHIVE_DATE=$(date -d '6 months ago' '+%Y-%m-%d')
psql -h localhost -U opsvi -d unified_context -c "
CREATE TABLE IF NOT EXISTS context_items_archive (LIKE context_items);
INSERT INTO context_items_archive
SELECT * FROM context_items
WHERE timestamp < '$ARCHIVE_DATE'
  AND source_type NOT IN ('critical', 'system');
DELETE FROM context_items
WHERE timestamp < '$ARCHIVE_DATE'
  AND source_type NOT IN ('critical', 'system');
"

# Security audit
echo "Running security audit..."
docker run --rm -v /opt/project-context:/app clair/clair:latest -c /app/docker-compose.prod.yml

# Performance report
echo "Generating performance report..."
psql -h localhost -U opsvi -d unified_context -c "
SELECT
  'Total Items' as metric,
  count(*) as value
FROM context_items
UNION ALL
SELECT
  'Items per day (last 30 days)' as metric,
  count(*)/30 as value
FROM context_items
WHERE timestamp > NOW() - INTERVAL '30 days'
UNION ALL
SELECT
  'Average query time' as metric,
  avg(mean_time) as value
FROM pg_stat_statements;
" > /var/log/performance-report-$(date +%Y%m).txt

echo "Monthly maintenance completed: $(date)"
EOF

chmod +x /usr/local/bin/monthly-maintenance.sh

# Schedule monthly maintenance
echo "0 3 1 * * /usr/local/bin/monthly-maintenance.sh >> /var/log/maintenance.log 2>&1" | crontab -
```

### Update Procedures

#### Application Updates
```bash
# Safe application update procedure
update_application() {
    echo "Starting application update..."

    # 1. Create backup
    /usr/local/bin/backup-database.sh
    /usr/local/bin/backup-app-data.sh

    # 2. Pull latest images
    cd /opt/project-context
    docker-compose -f docker-compose.prod.yml pull

    # 3. Check for breaking changes
    # Review CHANGELOG.md or release notes

    # 4. Update with rolling deployment
    for service in project-context nginx; do
        echo "Updating $service..."
        docker-compose -f docker-compose.prod.yml up -d --no-deps $service

        # Wait and verify
        sleep 30
        curl -f https://localhost/health || {
            echo "Health check failed for $service, rolling back..."
            docker-compose -f docker-compose.prod.yml rollback $service
            return 1
        }
    done

    # 5. Run post-update tasks
    # Database migrations, cache warming, etc.

    echo "Application update completed successfully"
}
```

#### Database Updates
```bash
# Database schema updates
update_database_schema() {
    echo "Starting database schema update..."

    # 1. Backup before schema changes
    /usr/local/bin/backup-database.sh

    # 2. Check current schema version
    CURRENT_VERSION=$(psql -h localhost -U opsvi -d unified_context -t -c "
    SELECT version FROM schema_versions ORDER BY applied_at DESC LIMIT 1;
    " 2>/dev/null || echo "0")

    echo "Current schema version: $CURRENT_VERSION"

    # 3. Apply migrations
    for migration in /opt/project-context/migrations/*.sql; do
        MIGRATION_VERSION=$(basename $migration .sql | sed 's/.*_//')

        if [ "$MIGRATION_VERSION" -gt "$CURRENT_VERSION" ]; then
            echo "Applying migration: $migration"

            psql -h localhost -U opsvi -d unified_context -f $migration || {
                echo "Migration failed: $migration"
                return 1
            }

            # Record migration
            psql -h localhost -U opsvi -d unified_context -c "
            INSERT INTO schema_versions (version, migration_file, applied_at)
            VALUES ($MIGRATION_VERSION, '$migration', NOW());
            "
        fi
    done

    echo "Database schema update completed"
}
```

---

## 🔍 Log Analysis & Debugging

### Log File Locations

#### Application Logs
```bash
# Main application log
tail -f /opt/project-context/logs/project-context.log

# Error log
tail -f /opt/project-context/logs/error.log

# Access log
tail -f /opt/project-context/logs/access.log

# Ingestion pipeline logs
tail -f /opt/project-context/logs/ingestion.log
```

#### System Logs
```bash
# Docker container logs
docker-compose -f docker-compose.prod.yml logs -f project-context

# PostgreSQL logs
docker-compose -f docker-compose.prod.yml logs -f postgres

# Redis logs
docker-compose -f docker-compose.prod.yml logs -f redis

# Nginx logs
docker-compose -f docker-compose.prod.yml logs -f nginx
```

### Log Analysis Scripts

#### Error Pattern Detection
```bash
# Create error analysis script
cat > /usr/local/bin/analyze-errors.sh << 'EOF'
#!/bin/bash

LOG_FILE="/opt/project-context/logs/project-context.log"
ERROR_REPORT="/tmp/error-report-$(date +%Y%m%d).txt"

echo "Error Analysis Report - $(date)" > $ERROR_REPORT
echo "========================================" >> $ERROR_REPORT

# Count error types
echo "Error Type Summary:" >> $ERROR_REPORT
grep -i error $LOG_FILE | grep -o '"error_type":"[^"]*' | cut -d':' -f2 | sort | uniq -c | sort -nr >> $ERROR_REPORT

echo "" >> $ERROR_REPORT

# Recent errors (last hour)
echo "Recent Errors (Last Hour):" >> $ERROR_REPORT
grep -i error $LOG_FILE | grep "$(date -d '1 hour ago' '+%Y-%m-%d %H'):\|$(date '+%Y-%m-%d %H'):" | tail -20 >> $ERROR_REPORT

echo "" >> $ERROR_REPORT

# Database errors
echo "Database Errors:" >> $ERROR_REPORT
grep -i "database\|postgresql\|connection" $LOG_FILE | grep -i error | tail -10 >> $ERROR_REPORT

echo "" >> $ERROR_REPORT

# Performance issues
echo "Performance Issues (>5s response):" >> $ERROR_REPORT
grep "response_time" $LOG_FILE | awk '$NF > 5000 {print}' | tail -10 >> $ERROR_REPORT

cat $ERROR_REPORT
EOF

chmod +x /usr/local/bin/analyze-errors.sh
```

#### Performance Analysis
```bash
# Create performance analysis script
cat > /usr/local/bin/analyze-performance.sh << 'EOF'
#!/bin/bash

LOG_FILE="/opt/project-context/logs/project-context.log"
PERF_REPORT="/tmp/performance-report-$(date +%Y%m%d).txt"

echo "Performance Analysis Report - $(date)" > $PERF_REPORT
echo "============================================" >> $PERF_REPORT

# Response time statistics
echo "Response Time Statistics:" >> $PERF_REPORT
grep "response_time" $LOG_FILE | awk '{print $NF}' | sort -n | awk '
BEGIN { sum = 0; count = 0 }
{
    sum += $1;
    count++;
    times[count] = $1
}
END {
    print "Count: " count
    print "Average: " sum/count "ms"
    print "Min: " times[1] "ms"
    print "Max: " times[count] "ms"
    print "Median: " times[int(count/2)] "ms"
    print "95th percentile: " times[int(count*0.95)] "ms"
}' >> $PERF_REPORT

echo "" >> $PERF_REPORT

# Slowest endpoints
echo "Slowest Endpoints:" >> $PERF_REPORT
grep "response_time" $LOG_FILE | grep -o '"path":"[^"]*' | cut -d':' -f2 | sort | uniq -c | sort -nr | head -10 >> $PERF_REPORT

echo "" >> $PERF_REPORT

# Cache statistics
echo "Cache Performance:" >> $PERF_REPORT
grep "cache" $LOG_FILE | grep -o '"cache_hit":[^,]*' | cut -d':' -f2 | awk '
BEGIN { hits = 0; misses = 0 }
/true/ { hits++ }
/false/ { misses++ }
END {
    total = hits + misses
    if (total > 0) {
        print "Cache Hit Rate: " (hits/total)*100 "%"
        print "Total Requests: " total
        print "Hits: " hits
        print "Misses: " misses
    }
}' >> $PERF_REPORT

cat $PERF_REPORT
EOF

chmod +x /usr/local/bin/analyze-performance.sh
```

### Debug Mode

#### Enable Debug Logging
```bash
# Enable debug mode in .env
LOG_LEVEL=DEBUG
ENABLE_QUERY_LOGGING=true
ENABLE_PERFORMANCE_LOGGING=true

# Restart services
docker-compose -f docker-compose.prod.yml restart project-context

# Watch debug logs
docker-compose -f docker-compose.prod.yml logs -f project-context | grep DEBUG
```

#### Database Query Debugging
```sql
-- Enable query logging
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_min_duration_statement = 1000; -- Log queries >1s
SELECT pg_reload_conf();

-- View slow queries
SELECT
  query,
  calls,
  total_time/calls as avg_time,
  stddev_time,
  rows/calls as avg_rows
FROM pg_stat_statements
WHERE calls > 10
ORDER BY total_time/calls DESC
LIMIT 20;

-- Check current active queries
SELECT
  pid,
  now() - pg_stat_activity.query_start AS duration,
  query,
  state
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';
```

---

## 📞 Support & Escalation

### Support Contacts

#### Internal Team
- **Operations Team**: ops@company.com
- **Development Team**: dev@company.com
- **Database Admin**: dba@company.com

#### External Vendors
- **Cloud Provider Support**: For infrastructure issues
- **Database Vendor**: For PostgreSQL/TimescaleDB issues
- **Monitoring Vendor**: For Prometheus/Grafana issues

### Escalation Procedures

#### Severity Levels

**Critical (P0) - Service Down**
- Complete service outage
- Data corruption
- Security breach
- Immediate response required (< 15 minutes)

**High (P1) - Major Impact**
- Significant performance degradation
- Partial service disruption
- Response required within 1 hour

**Medium (P2) - Minor Impact**
- Non-critical feature issues
- Performance issues affecting some users
- Response required within 4 hours

**Low (P3) - Enhancement/General**
- Feature requests
- General questions
- Response required within 24 hours

#### Escalation Matrix
```
P0 Critical:
1. On-call engineer (immediate)
2. Operations manager (15 minutes)
3. Engineering director (30 minutes)
4. CTO (1 hour)

P1 High:
1. On-call engineer (1 hour)
2. Operations manager (4 hours)
3. Engineering director (next business day)

P2 Medium:
1. Support team (4 hours)
2. Operations team (next business day)

P3 Low:
1. Support team (24 hours)
```

### Emergency Runbook

#### Complete Service Outage
1. **Immediate Actions** (0-5 minutes):
   ```bash
   # Check basic connectivity
   curl -f https://localhost/health

   # Check all services
   docker-compose -f docker-compose.prod.yml ps

   # Check system resources
   df -h && free -h && top -bn1
   ```

2. **Diagnosis** (5-15 minutes):
   ```bash
   # Check recent logs
   docker-compose -f docker-compose.prod.yml logs --tail=100 project-context

   # Check database
   psql -h localhost -U opsvi -d unified_context -c "SELECT 1;"

   # Check Redis
   redis-cli -h localhost -p 6379 ping
   ```

3. **Recovery Actions** (15-30 minutes):
   ```bash
   # Restart services in order
   docker-compose -f docker-compose.prod.yml restart redis
   docker-compose -f docker-compose.prod.yml restart postgres
   sleep 30
   docker-compose -f docker-compose.prod.yml restart project-context

   # If restart doesn't work, full restart
   docker-compose -f docker-compose.prod.yml down
   docker-compose -f docker-compose.prod.yml up -d
   ```

4. **Communication**:
   - Update status page
   - Notify stakeholders via Slack
   - Prepare incident report

#### Performance Degradation
1. **Identify bottleneck**:
   ```bash
   # Check CPU/Memory
   top -bn1

   # Check database performance
   psql -h localhost -U opsvi -d unified_context -c "
   SELECT query, mean_time, calls
   FROM pg_stat_statements
   ORDER BY mean_time DESC LIMIT 5;"

   # Check cache hit rate
   curl -s https://localhost/health/cache
   ```

2. **Quick fixes**:
   ```bash
   # Restart application (often resolves memory issues)
   docker-compose -f docker-compose.prod.yml restart project-context

   # Clear cache if corrupted
   redis-cli -h localhost -p 6379 flushdb

   # Kill long-running queries
   psql -h localhost -U opsvi -d unified_context -c "
   SELECT pg_terminate_backend(pid)
   FROM pg_stat_activity
   WHERE state = 'active'
     AND query_start < now() - interval '10 minutes';"
   ```

---

## 📖 Conclusion

This troubleshooting and operations guide provides **comprehensive coverage** of production deployment, monitoring, maintenance, and issue resolution for the Unified Context System Phase 1. The guide includes:

**✅ Operational Procedures:**
- Complete diagnostic workflows
- Automated monitoring and alerting
- Backup and recovery procedures
- Regular maintenance scheduling

**✅ Issue Resolution:**
- Common problem identification and solutions
- Performance optimization strategies
- Emergency response procedures
- Escalation and support contacts

**✅ Best Practices:**
- Proactive monitoring strategies
- Automated maintenance tasks
- Security and compliance procedures
- Documentation and communication protocols

The system is **production-ready** with comprehensive operational support, ensuring reliable service delivery and rapid issue resolution.

---

**Document Version**: 1.0.0
**Last Updated**: September 4, 2025
**Status**: ✅ Production Ready
