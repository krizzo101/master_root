# 🔍 Unified Monitoring Suite Documentation

## Complete Monitoring and Performance Optimization for Unified Context System

This comprehensive monitoring suite provides enterprise-grade monitoring, alerting, performance optimization, and capacity planning for the complete unified context system including PostgreSQL + TimescaleDB + pgvector, Neo4j relationship graph, real-time ingestion pipelines, and all supporting infrastructure.

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Component Architecture](#component-architecture)
3. [Quick Start Guide](#quick-start-guide)
4. [Monitoring Dashboard](#monitoring-dashboard)
5. [Performance Optimization](#performance-optimization)
6. [Health Checking](#health-checking)
7. [Alert Management](#alert-management)
8. [Log Aggregation](#log-aggregation)
9. [Capacity Planning](#capacity-planning)
10. [API Reference](#api-reference)
11. [Configuration](#configuration)
12. [Production Deployment](#production-deployment)
13. [Troubleshooting](#troubleshooting)

---

## 🎯 System Overview

### Monitored Components

✅ **PostgreSQL + TimescaleDB + pgvector**
- Database size, connections, query performance
- pgvector index performance and search latency
- Table statistics and vacuum status

✅ **Neo4j Graph Database**
- Node/relationship counts (21k+ nodes monitored)
- Query performance and memory usage
- Graph density and connectivity metrics

✅ **Real-time Ingestion Pipeline**
- Chat log processing rates
- Queue status and buffer management
- Fault tolerance and circuit breaker status

✅ **Vector Search System**
- Embedding coverage and accuracy
- Search performance benchmarks
- Index optimization recommendations

✅ **System Resources**
- CPU, memory, disk, network utilization
- Container resource usage
- Process monitoring

✅ **Docker Services**
- Container health and resource usage
- Image management and updates
- Service availability monitoring

### Key Features

🚀 **Real-time Monitoring**
- WebSocket-based live dashboard updates
- Sub-second metric collection
- Automated anomaly detection

📊 **Performance Optimization**
- Automated performance analysis
- SQL query optimization recommendations
- Resource utilization optimization

🔔 **Intelligent Alerting**
- Multi-channel notifications (email, webhook, file)
- Alert correlation and suppression
- Escalation policies with time-based triggering

📈 **Capacity Planning**
- ML-based growth forecasting
- Resource requirement projections
- Cost analysis and scaling recommendations

🗂️ **Log Aggregation**
- Centralized log collection from all components
- Pattern detection and anomaly identification
- Historical analysis and trending

---

## 🏗️ Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Unified Monitoring Suite                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │ Web Dashboard   │    │ Alert Manager   │    │ Health Check │ │
│  │ (Port 8002)     │◄──►│ Multi-channel   │◄──►│ Deep Diags   │ │
│  │ Real-time UI    │    │ Notifications   │    │ 7 Components │ │
│  └─────────────────┘    └─────────────────┘    └──────────────┘ │
│           ▲                       ▲                     ▲       │
│           │                       │                     │       │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │ Performance     │    │ Log Aggregator  │    │ Capacity     │ │
│  │ Optimizer       │    │ Pattern Detect  │    │ Planner      │ │
│  │ ML Analysis     │    │ Multi-source    │    │ Growth Model │ │
│  └─────────────────┘    └─────────────────┘    └──────────────┘ │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                      Data Sources                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │ PostgreSQL  │  │ Neo4j       │  │ Docker      │  │ System  │ │
│  │ + pgvector  │  │ 21k+ nodes  │  │ Containers  │  │ Metrics │ │
│  │ + TimescaleDB│  │ Relationships│  │ Resources   │  │ Logs    │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start Guide

### Prerequisites

- Python 3.8+ with pip
- PostgreSQL with pgvector extension
- Neo4j database
- Docker (optional, for container monitoring)
- 4GB+ RAM recommended

### Installation

1. **Navigate to the monitoring directory:**
   ```bash
   cd /home/opsvi/master_root/apps/monitoring-dashboard
   ```

2. **Install Python dependencies:**
   ```bash
   pip install fastapi uvicorn psycopg2-binary neo4j docker psutil numpy aiofiles requests
   ```

3. **Deploy the monitoring suite:**
   ```bash
   ./deploy_monitoring_suite.sh deploy
   ```

4. **Access the dashboard:**
   ```
   http://localhost:8002
   ```

### Verification

Check that all services are running:
```bash
./deploy_monitoring_suite.sh status
```

Expected output:
```
✅ unified_dashboard: Running
   ✅ Dashboard Health: OK
   🌐 URL: http://localhost:8002
```

---

## 📊 Monitoring Dashboard

### Main Dashboard Interface

The unified monitoring dashboard provides a comprehensive overview of all system components in a single interface.

**URL:** `http://localhost:8002`

#### Dashboard Sections

**📈 System Overview**
- Overall health score (0-100%)
- Total components monitored
- Active alerts count
- Data points processed

**🗄️ Database Monitoring**
- PostgreSQL: Connection count, query performance, pgvector status
- Neo4j: Node/relationship count, memory usage, query latency

**🔍 Vector Search Performance**
- Embedding coverage percentage
- Search latency benchmarks
- Index efficiency metrics

**⚡ Real-time Ingestion**
- Processing rates (files/min, entries/min)
- Queue status and buffer utilization
- Pipeline health indicators

**🖥️ System Resources**
- CPU, memory, disk utilization
- Network I/O statistics
- Container resource usage

**🚨 Active Alerts**
- Current alert status
- Alert severity distribution
- Recent alert history

### Real-time Updates

The dashboard updates automatically every 10 seconds via WebSocket connection. No manual refresh required.

### API Endpoints

**Health Check:** `GET /api/health`
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

**System Overview:** `GET /api/overview`
```json
{
  "total_components": 7,
  "healthy_components": 6,
  "total_data_points": 1234567,
  "system_load": 45.2,
  "overall_status": "healthy",
  "last_updated": "2025-01-15T10:30:00Z"
}
```

**Component Status:** `GET /api/components`
```json
{
  "postgresql": {
    "status": "healthy",
    "context_items_count": 21472,
    "active_connections": 12,
    "pgvector_enabled": true
  },
  "neo4j": {
    "status": "healthy",
    "node_count": 21472,
    "relationship_count": 85000
  }
}
```

---

## ⚡ Performance Optimization

### Automated Analysis

The performance optimizer continuously analyzes system performance and provides actionable recommendations.

#### Features

**🔍 Query Analysis**
- Slow query detection
- Index usage efficiency
- Query optimization suggestions

**📈 Trend Analysis**
- Performance degradation detection
- Resource utilization trends
- Predictive performance modeling

**💡 Optimization Recommendations**
- Prioritized by impact and effort
- SQL commands provided for implementation
- Verification queries included

### Running Performance Analysis

**Manual Analysis:**
```bash
./deploy_monitoring_suite.sh performance
```

**Python API:**
```python
from performance_optimizer import run_performance_analysis

# Run analysis
result = await run_performance_analysis()
print(f"Recommendations: {len(result['recommendations'])}")
```

### Example Recommendations

```json
{
  "category": "index",
  "priority": "high",
  "title": "Add indexes to context_items table",
  "description": "Table has 45.2% index scan efficiency with 1,234 sequential scans",
  "impact_estimate": "Could reduce query time by 60-80%",
  "implementation_effort": "Low - single CREATE INDEX command",
  "sql_commands": [
    "CREATE INDEX CONCURRENTLY idx_context_items_file_path ON context_items (file_path);",
    "CREATE INDEX CONCURRENTLY idx_context_items_created_at ON context_items (created_at);"
  ],
  "estimated_improvement_percent": 70.0
}
```

---

## 🏥 Health Checking

### Comprehensive Diagnostics

The health checker performs deep diagnostic analysis of all system components.

#### Health Check Categories

**🔗 Connectivity Tests**
- Database connections
- Service availability
- Network connectivity

**📊 Performance Tests**
- Query response times
- Resource utilization
- Throughput measurements

**🔧 Configuration Validation**
- Service configurations
- Resource limits
- Security settings

**🔄 Integration Tests**
- Inter-component communication
- Data consistency
- End-to-end workflows

### Running Health Checks

**Manual Check:**
```bash
./deploy_monitoring_suite.sh health
```

**Python API:**
```python
from health_checker import run_health_check

# Run comprehensive health check
report = await run_health_check()
print(f"Overall Score: {report.overall_health_score:.1f}%")
```

### Health Check Results

```json
{
  "overall_health_score": 94.2,
  "system_status": "healthy",
  "component_results": [
    {
      "component": "postgresql",
      "status": "healthy",
      "score": 96.5,
      "response_time_ms": 15.2,
      "checks_performed": [
        "basic_connectivity",
        "query_performance",
        "pgvector_extension",
        "index_efficiency"
      ],
      "issues_found": [],
      "recommendations": [
        "Consider optimizing slow queries over 100ms"
      ]
    }
  ],
  "critical_issues": [],
  "performance_summary": {
    "total_check_time_ms": 2847.3,
    "components_checked": 7,
    "avg_response_time_ms": 123.4,
    "checks_passed": 7,
    "checks_failed": 0
  }
}
```

---

## 🚨 Alert Management

### Intelligent Alerting System

The alert manager provides sophisticated alerting with correlation, suppression, and escalation policies.

#### Alert Channels

**📁 File Logging** (Always enabled)
- Location: `/home/opsvi/master_root/logs/monitoring/alerts.log`
- All alerts logged with full context

**📧 Email Notifications** (Optional)
- SMTP configuration required
- HTML and text format support
- Escalation-based delivery

**🔗 Webhook Integration** (Optional)
- JSON payload delivery
- Retry logic with exponential backoff
- Custom headers support

#### Alert Rules

**System Resource Alerts**
```json
{
  "high_cpu": {
    "threshold": 80.0,
    "severity": "warning",
    "duration_minutes": 2
  },
  "critical_memory": {
    "threshold": 95.0,
    "severity": "critical",
    "duration_minutes": 1
  }
}
```

**Database Alerts**
```json
{
  "postgres_offline": {
    "severity": "critical",
    "duration_minutes": 0
  },
  "slow_queries": {
    "threshold": 500.0,
    "severity": "warning",
    "duration_minutes": 2
  }
}
```

### Alert Correlation

Related alerts are automatically correlated to reduce noise:
- System resource alerts grouped by timeframe
- Database performance issues linked to resource constraints
- Container restart alerts correlated with system events

### Escalation Policies

**Standard Policy:**
1. Immediate: File logging
2. 5 minutes: File + Email
3. 15 minutes: File + Email + Webhook

**Critical Policy:**
1. Immediate: All channels
2. 2 minutes: Repeat all channels
3. 5 minutes: Final escalation

---

## 📜 Log Aggregation

### Centralized Log Collection

The log aggregator collects, analyzes, and correlates logs from all system components.

#### Log Sources

**PostgreSQL Logs**
- Query logs and slow query detection
- Error logs and connection issues
- Performance statistics

**Neo4j Logs**
- Query logs and performance
- Memory usage and GC events
- Cluster status (if applicable)

**Docker Container Logs**
- Container stdout/stderr
- Container lifecycle events
- Resource utilization logs

**System Logs**
- Kernel messages
- Service status changes
- Security events

**Application Logs**
- Service-specific logs
- Error tracking
- Performance metrics

### Log Analysis Features

**🔍 Pattern Detection**
- Regex-based pattern matching
- Anomaly detection
- Trend analysis

**📊 Log Statistics**
- Volume by source and severity
- Error rate calculations
- Performance correlations

**🗄️ Historical Analysis**
- Time-based log analysis
- Comparative trending
- Root cause analysis

### Log Patterns

```python
{
  "postgres_connection_error": {
    "regex": r"FATAL:.*could not connect|connection refused",
    "severity": "critical",
    "alert_threshold": 1,
    "time_window_minutes": 1
  },
  "memory_exhaustion": {
    "regex": r"OutOfMemoryError|GC overhead limit exceeded",
    "severity": "critical",
    "alert_threshold": 1
  }
}
```

---

## 📈 Capacity Planning

### Growth Forecasting

The capacity planner uses machine learning to forecast growth and recommend scaling actions.

#### Forecasting Models

**📊 Linear Regression**
- Trend analysis for consistent growth
- Confidence scoring
- R-squared correlation

**📈 Growth Rate Analysis**
- Weekly/monthly growth rates
- Seasonal pattern detection
- Variance analysis

#### Capacity Limits

```python
{
  "postgresql": {
    "max_connections": 200,
    "max_db_size_gb": 500,
    "shared_buffers_gb": 8
  },
  "neo4j": {
    "max_nodes": 10000000,
    "max_relationships": 100000000,
    "heap_memory_gb": 16
  },
  "system": {
    "max_cpu_percent": 85,
    "max_memory_percent": 90,
    "max_disk_percent": 85
  }
}
```

### Scaling Recommendations

```json
{
  "priority": "short_term",
  "component": "postgresql",
  "action_type": "scale_up",
  "description": "Increase PostgreSQL capacity for database growth",
  "estimated_cost": 450.0,
  "risk_level": "medium",
  "implementation_timeline": "1-2 months",
  "expected_benefits": [
    "Improved query performance",
    "Increased data capacity",
    "Better concurrency"
  ]
}
```

### Cost Projections

**Resource Costs (USD/month):**
- CPU core: $25
- Memory (GB): $3.50
- Storage (GB): $0.10
- Database instance: $150-200

---

## 🔧 Configuration

### Main Configuration File

**Location:** `apps/monitoring-dashboard/monitoring_config.json`

```json
{
  "postgres": {
    "host": "localhost",
    "port": 5432,
    "database": "unified_context",
    "user": "opsvi",
    "password": "opsvi_secure_password"
  },
  "neo4j": {
    "uri": "bolt://localhost:7687",
    "user": "neo4j",
    "password": "password"
  },
  "unified_dashboard": {
    "port": 8002,
    "host": "0.0.0.0",
    "log_level": "INFO"
  },
  "alert_manager": {
    "email": {
      "smtp_server": "smtp.gmail.com",
      "smtp_port": 587,
      "from_address": "monitoring@yourcompany.com",
      "to_address": "admin@yourcompany.com",
      "username": "your_email@gmail.com",
      "password": "your_app_password",
      "use_tls": true,
      "enabled": true
    },
    "webhook": {
      "default_url": "https://hooks.slack.com/services/...",
      "enabled": true
    }
  }
}
```

### Alert Configuration

Custom alert rules can be defined in the configuration:

```json
{
  "custom_alerts": {
    "high_vector_search_latency": {
      "metric_path": "$.vector_search.avg_search_time_ms",
      "operator": "gt",
      "threshold": 150.0,
      "severity": "warning",
      "description": "Vector search latency is high"
    }
  }
}
```

---

## 🚀 Production Deployment

### System Requirements

**Minimum Requirements:**
- CPU: 2 cores
- RAM: 4GB
- Disk: 20GB free space
- Network: 100Mbps

**Recommended Requirements:**
- CPU: 4+ cores
- RAM: 8GB+
- Disk: 50GB+ free space (for logs and archives)
- Network: 1Gbps

### Production Deployment Steps

1. **Create dedicated user:**
   ```bash
   sudo useradd -m -s /bin/bash monitoring
   sudo usermod -aG docker monitoring
   ```

2. **Set up systemd services:**
   ```bash
   sudo ./deploy_monitoring_suite.sh install-systemd
   sudo systemctl enable unified-monitoring-dashboard
   sudo systemctl start unified-monitoring-dashboard
   ```

3. **Configure log rotation:**
   ```bash
   sudo tee /etc/logrotate.d/unified-monitoring << EOF
   /home/opsvi/master_root/logs/monitoring/*.log {
       daily
       rotate 30
       compress
       delaycompress
       missingok
       notifempty
       create 644 monitoring monitoring
   }
   EOF
   ```

4. **Set up monitoring for the monitoring system:**
   ```bash
   # Monitor monitoring processes
   echo "*/5 * * * * /usr/bin/systemctl is-active unified-monitoring-dashboard || /usr/bin/systemctl start unified-monitoring-dashboard" | sudo crontab -u monitoring -
   ```

### Security Considerations

**🔒 Access Control**
- Dashboard should be behind authentication
- Database credentials in secure configuration
- Network access restrictions

**🔐 Encryption**
- HTTPS for web dashboard
- Encrypted database connections
- Secure webhook endpoints

**📋 Audit Logging**
- All configuration changes logged
- Access attempts tracked
- Alert deliveries recorded

### High Availability Setup

**🔄 Multi-instance Deployment**
```bash
# Instance 1 (Primary)
./deploy_monitoring_suite.sh deploy

# Instance 2 (Secondary)
MONITORING_PORT=8003 ./deploy_monitoring_suite.sh deploy
```

**⚖️ Load Balancing**
```nginx
upstream monitoring_backend {
    server localhost:8002;
    server localhost:8003 backup;
}

server {
    listen 80;
    location / {
        proxy_pass http://monitoring_backend;
    }
}
```

---

## 🛠️ Troubleshooting

### Common Issues

**❌ Dashboard won't start**
```bash
# Check Python dependencies
pip install -r requirements.txt

# Check database connections
telnet localhost 5432
telnet localhost 7687

# Check logs
tail -f /home/opsvi/master_root/logs/monitoring/unified_dashboard.log
```

**❌ No metrics displayed**
```bash
# Verify database connectivity
python3 -c "import psycopg2; psycopg2.connect(host='localhost', database='unified_context', user='opsvi', password='opsvi_secure_password')"

# Check service status
./deploy_monitoring_suite.sh status

# Run health check
./deploy_monitoring_suite.sh health
```

**❌ Alerts not working**
```bash
# Check alert configuration
cat monitoring_config.json | jq '.alert_manager'

# Test email configuration
python3 -c "
import smtplib
from email.mime.text import MimeText
msg = MimeText('Test')
msg['Subject'] = 'Test'
msg['From'] = 'test@example.com'
msg['To'] = 'admin@example.com'
s = smtplib.SMTP('localhost', 587)
s.send_message(msg)
s.quit()
print('Email test successful')
"

# Check alert logs
tail -f /home/opsvi/master_root/logs/monitoring/alerts.log
```

### Performance Issues

**🐌 Slow dashboard loading**
```bash
# Check system resources
htop
df -h

# Optimize database
psql -U opsvi -d unified_context -c "VACUUM ANALYZE;"

# Check for slow queries
grep "slow query" /home/opsvi/master_root/logs/monitoring/*.log
```

**📊 High memory usage**
```bash
# Check memory usage by component
ps aux | grep python3 | grep monitoring

# Adjust configuration
# Reduce metric history size in config
# Enable log archiving
```

### Log Analysis

**🔍 Debug logging**
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
./deploy_monitoring_suite.sh restart

# Check component logs
tail -f /home/opsvi/master_root/logs/monitoring/*.log
```

**📋 Service status**
```bash
# Comprehensive status check
./deploy_monitoring_suite.sh status

# Health check with details
./deploy_monitoring_suite.sh health

# Performance analysis
./deploy_monitoring_suite.sh performance
```

---

## 📞 Support and Maintenance

### Regular Maintenance Tasks

**📅 Daily**
- Check dashboard health status
- Review active alerts
- Monitor system resources

**📅 Weekly**
- Run performance analysis
- Review capacity planning reports
- Update alert thresholds as needed

**📅 Monthly**
- Archive old logs
- Update dependencies
- Review and optimize configurations

### Monitoring the Monitoring System

The monitoring system should itself be monitored:

```bash
# Setup monitoring check
cat > /usr/local/bin/check-monitoring.sh << 'EOF'
#!/bin/bash
if ! curl -f http://localhost:8002/api/health >/dev/null 2>&1; then
    echo "CRITICAL: Monitoring dashboard is down"
    # Send notification
    echo "Monitoring system is down" | mail -s "CRITICAL: Monitoring Alert" admin@yourcompany.com
    # Restart service
    systemctl restart unified-monitoring-dashboard
fi
EOF

chmod +x /usr/local/bin/check-monitoring.sh

# Add to crontab
echo "*/5 * * * * /usr/local/bin/check-monitoring.sh" | crontab -
```

### Getting Help

**📖 Documentation**
- This comprehensive guide
- Inline code documentation
- API endpoint documentation

**🐛 Issue Reporting**
- Check logs first: `/home/opsvi/master_root/logs/monitoring/`
- Run diagnostic: `./deploy_monitoring_suite.sh health`
- Include system information and error logs

**💬 Support Channels**
- GitHub Issues for bug reports
- Documentation updates for improvements
- Performance optimization consultations available

---

## 📊 Production Readiness Checklist

### ✅ Deployment Verification

- [ ] All services start successfully
- [ ] Dashboard accessible at http://localhost:8002
- [ ] Database connections verified
- [ ] Health checks pass (>90% score)
- [ ] Performance analysis completes
- [ ] Alerts can be triggered and received

### ✅ Security Configuration

- [ ] Default passwords changed
- [ ] Database connections encrypted
- [ ] Web dashboard secured (HTTPS/auth)
- [ ] Firewall rules configured
- [ ] Audit logging enabled

### ✅ Monitoring Coverage

- [ ] PostgreSQL metrics collected
- [ ] Neo4j metrics available
- [ ] System resources monitored
- [ ] Docker containers tracked
- [ ] Application logs aggregated

### ✅ Alerting Verification

- [ ] Critical alerts tested
- [ ] Email notifications working
- [ ] Webhook integrations tested
- [ ] Escalation policies verified
- [ ] Alert correlation functioning

### ✅ Capacity Planning

- [ ] Growth models established
- [ ] Capacity limits defined
- [ ] Cost projections generated
- [ ] Scaling recommendations available

### ✅ Operational Procedures

- [ ] Monitoring procedures documented
- [ ] Incident response procedures defined
- [ ] Regular maintenance scheduled
- [ ] Backup procedures verified
- [ ] Recovery procedures tested

---

## 🎉 Conclusion

The Unified Monitoring Suite provides comprehensive monitoring, alerting, performance optimization, and capacity planning for your unified context system. With automated health checking, intelligent alerting, and ML-based forecasting, you can ensure optimal performance and proactive scaling.

**Key Benefits:**
- 🔍 **Complete Visibility** - Monitor all 21k+ nodes, relationships, and system components
- ⚡ **Performance Optimization** - Automated analysis and recommendations
- 🚨 **Intelligent Alerting** - Reduce noise with smart correlation and escalation
- 📈 **Predictive Planning** - ML-based growth forecasting and cost analysis
- 🏥 **Deep Health Checks** - Comprehensive diagnostics across all components
- 📜 **Centralized Logging** - Pattern detection and historical analysis

**Next Steps:**
1. Complete the production deployment checklist
2. Configure email/webhook alerting for your environment
3. Customize alert thresholds based on your requirements
4. Set up regular review of capacity planning reports
5. Integrate with your existing monitoring infrastructure

For questions, issues, or enhancements, refer to the troubleshooting section or contact the development team.

---

*Generated by Unified Monitoring Suite v2.0.0*
*Last Updated: $(date)*
