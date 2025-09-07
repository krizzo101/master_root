# Sleuth Intel Operations Manual

## Table of Contents
1. [System Architecture](#system-architecture)
2. [Operational Procedures](#operational-procedures)
3. [Backup and Recovery](#backup-and-recovery)
4. [Scaling Guidelines](#scaling-guidelines)
5. [Security Operations](#security-operations)
6. [Incident Response](#incident-response)
7. [Maintenance Windows](#maintenance-windows)
8. [Performance Tuning](#performance-tuning)

## System Architecture

### Component Overview
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Load      │────▶│  Application │────▶│  Database   │
│  Balancer   │     │   Servers    │     │  (PostgreSQL)│
└─────────────┘     └─────────────┘     └─────────────┘
                            │
                            ▼
                    ┌─────────────┐
                    │    Redis     │
                    │    Cache     │
                    └─────────────┘
```

### Service Dependencies
- **PostgreSQL**: Primary data store
- **Redis**: Caching and session storage
- **Enformion API**: External data provider
- **Monitoring Stack**: Prometheus + Grafana

## Operational Procedures

### Daily Operations

#### Health Checks
```bash
# Check application health
./scripts/health-check.sh

# Verify all pods are running
kubectl get pods -n sleuth-intel

# Check error rates
kubectl logs -n sleuth-intel -l app=sleuth-intel --tail=100 | grep ERROR
```

#### Monitoring Review
1. Check Grafana dashboards for anomalies
2. Review Prometheus alerts
3. Verify API response times < 1s p95
4. Check database connection pool usage < 80%

### Weekly Operations

#### Performance Review
```bash
# Generate performance report
./scripts/performance-report.sh

# Analyze slow queries
psql $DATABASE_URL -c "SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"
```

#### Security Audit
```bash
# Run security scan
./scripts/security-audit.sh

# Check for CVEs
trivy image sleuth-intel:latest
```

## Backup and Recovery

### Backup Strategy

#### Database Backups
```bash
# Manual backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Automated backup (runs daily at 2 AM)
0 2 * * * /usr/local/bin/backup-database.sh
```

#### Application State
```bash
# Backup Redis
redis-cli --rdb /backup/dump.rdb

# Backup configurations
kubectl get configmap -n sleuth-intel -o yaml > configmaps-backup.yaml
kubectl get secret -n sleuth-intel -o yaml > secrets-backup.yaml
```

### Recovery Procedures

#### Database Recovery
```bash
# Stop application
kubectl scale deployment sleuth-intel --replicas=0 -n sleuth-intel

# Restore database
psql $DATABASE_URL < backup_file.sql

# Start application
kubectl scale deployment sleuth-intel --replicas=3 -n sleuth-intel
```

#### Disaster Recovery
1. Provision new infrastructure
2. Restore database from backup
3. Deploy application using CI/CD
4. Restore Redis cache (optional)
5. Verify system functionality

## Scaling Guidelines

### Horizontal Scaling

#### Application Servers
```bash
# Manual scaling
kubectl scale deployment sleuth-intel --replicas=5 -n sleuth-intel

# Auto-scaling configuration
kubectl apply -f k8s/hpa.yaml
```

#### Database Scaling
```yaml
# Read replicas for load distribution
- Primary: Writes only
- Replica 1: Read queries
- Replica 2: Analytics/reporting
```

### Vertical Scaling

#### Resource Adjustments
```bash
# Update resource limits
kubectl set resources deployment sleuth-intel \
  -c sleuth-intel \
  --limits=cpu=1000m,memory=1Gi \
  --requests=cpu=500m,memory=512Mi \
  -n sleuth-intel
```

### Capacity Planning
| Metric | Threshold | Action |
|--------|-----------|--------|
| CPU Usage | > 70% | Add pods |
| Memory Usage | > 80% | Increase limits |
| Database Connections | > 80% | Increase pool size |
| Response Time p95 | > 2s | Scale horizontally |

## Security Operations

### Access Control
```bash
# Review RBAC policies
kubectl get rolebindings -n sleuth-intel
kubectl get clusterrolebindings | grep sleuth

# Rotate secrets
./scripts/rotate-secrets.sh
```

### Security Monitoring
- Monitor failed authentication attempts
- Track API key usage
- Review access logs daily
- Alert on suspicious patterns

### Compliance
- PCI DSS: Encrypt sensitive data
- GDPR: Data retention policies
- SOC 2: Access audit trails
- HIPAA: PHI handling procedures

## Incident Response

### Severity Levels
- **P1**: Complete service outage
- **P2**: Significant degradation
- **P3**: Minor issues
- **P4**: Non-critical bugs

### Response Procedures

#### P1 Incident
1. Alert on-call engineer
2. Create incident channel
3. Begin investigation
4. Communicate status updates every 30 minutes
5. Implement fix or rollback
6. Post-mortem within 48 hours

#### Rollback Procedure
```bash
# Get previous deployment
kubectl rollout history deployment/sleuth-intel -n sleuth-intel

# Rollback to previous version
kubectl rollout undo deployment/sleuth-intel -n sleuth-intel

# Verify rollback
kubectl rollout status deployment/sleuth-intel -n sleuth-intel
```

## Maintenance Windows

### Scheduled Maintenance
- **Time**: Sunday 2-4 AM UTC
- **Frequency**: Monthly
- **Duration**: 2 hours maximum

### Maintenance Checklist
- [ ] Notify users 48 hours in advance
- [ ] Enable maintenance mode
- [ ] Perform database maintenance
- [ ] Update dependencies
- [ ] Apply security patches
- [ ] Run integration tests
- [ ] Disable maintenance mode
- [ ] Verify system functionality

### Zero-Downtime Deployments
```bash
# Rolling update
kubectl set image deployment/sleuth-intel \
  sleuth-intel=sleuth-intel:new-version \
  -n sleuth-intel

# Monitor rollout
kubectl rollout status deployment/sleuth-intel -n sleuth-intel
```

## Performance Tuning

### Database Optimization
```sql
-- Update statistics
ANALYZE;

-- Reindex tables
REINDEX DATABASE sleuth_intel;

-- Vacuum dead tuples
VACUUM FULL;
```

### Application Tuning
```python
# Gunicorn settings
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
```

### Cache Optimization
```bash
# Redis configuration
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
```

### Network Optimization
- Enable HTTP/2
- Configure CDN for static assets
- Implement connection pooling
- Use persistent connections

## Monitoring and Alerting

### Key Metrics
| Metric | Warning | Critical |
|--------|---------|----------|
| Error Rate | > 1% | > 5% |
| Response Time | > 1s | > 3s |
| CPU Usage | > 70% | > 90% |
| Memory Usage | > 75% | > 90% |
| Disk Usage | > 70% | > 85% |

### Alert Channels
- PagerDuty: P1/P2 incidents
- Slack: P3/P4 issues
- Email: Daily reports

### Runbooks
Available at: `/docs/runbooks/`
- High CPU usage
- Database connection errors
- API rate limiting
- Cache failures
- External service outages
