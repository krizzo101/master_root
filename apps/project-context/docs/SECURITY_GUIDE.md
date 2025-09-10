# Project Context MCP Server - Security Hardening Guide

**Version**: 0.1.0
**Date**: January 2025
**Classification**: Internal Security Guide

## 🛡️ Security Overview

This guide provides comprehensive security hardening measures for the Project Context MCP Server in production environments. All recommendations follow industry best practices and compliance standards.

## 🔐 Authentication & Authorization

### API Key Security

#### Generate Secure API Keys
```bash
# Generate cryptographically secure API key (32+ characters)
openssl rand -hex 32

# Alternative: Use UUIDs
python3 -c "import uuid; print(str(uuid.uuid4()).replace('-', ''))"
```

#### API Key Management
```bash
# Store in secure environment variables
export API_KEY="your-secure-32-char-api-key-here"

# Use secrets management in production
# - AWS Secrets Manager
# - HashiCorp Vault
# - Kubernetes Secrets
```

#### Rate Limiting Configuration
```yaml
# In docker-compose.prod.yml
environment:
  - RATE_LIMIT_PER_MINUTE=1000
  - RATE_LIMIT_BURST=50
  - RATE_LIMIT_BY_IP=true
```

### JWT Authentication (Optional Enhancement)

```bash
# Generate JWT signing key
openssl rand -hex 64

# Configure JWT in .env
JWT_SECRET_KEY=your-64-char-jwt-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Multi-Factor Authentication

```python
# Example: TOTP integration
import pyotp

def generate_totp_secret():
    return pyotp.random_base32()

def verify_totp(secret, token):
    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=1)
```

## 🔒 Network Security

### SSL/TLS Configuration

#### Strong Cipher Suites
```nginx
# nginx.conf - Update cipher configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;
ssl_ecdh_curve secp384r1;
```

#### Certificate Security
```bash
# Generate secure DH parameters
openssl dhparam -out dhparam.pem 4096

# Set proper permissions
chmod 600 ssl/key.pem
chmod 644 ssl/cert.pem
chmod 644 ssl/dhparam.pem
```

#### HSTS Configuration
```nginx
# Force HTTPS with HSTS
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
```

### Firewall Configuration

#### UFW (Ubuntu/Debian)
```bash
# Reset and configure UFW
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow specific services
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Restrict database access
sudo ufw deny 5432
sudo ufw allow from 10.0.0.0/8 to any port 5432

# Restrict monitoring access
sudo ufw deny 9090
sudo ufw allow from 172.20.0.0/16 to any port 9090

sudo ufw enable
```

#### iptables (Advanced)
```bash
#!/bin/bash
# iptables security rules

# Flush existing rules
iptables -F
iptables -X
iptables -Z

# Default policies
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Allow loopback
iptables -A INPUT -i lo -j ACCEPT

# Allow established connections
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow SSH (change port if needed)
iptables -A INPUT -p tcp --dport 22 -m state --state NEW -j ACCEPT

# Allow HTTP/HTTPS
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Rate limiting for HTTP/HTTPS
iptables -A INPUT -p tcp --dport 80 -m limit --limit 25/minute --limit-burst 100 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -m limit --limit 25/minute --limit-burst 100 -j ACCEPT

# Block common attack patterns
iptables -A INPUT -p tcp --tcp-flags ALL NONE -j DROP
iptables -A INPUT -p tcp --tcp-flags ALL ALL -j DROP
iptables -A INPUT -p tcp --tcp-flags ALL FIN,URG,PSH -j DROP
iptables -A INPUT -p tcp --tcp-flags ALL SYN,RST,ACK,FIN,URG -j DROP

# Save rules
iptables-save > /etc/iptables/rules.v4
```

### Network Segmentation

```yaml
# docker-compose.prod.yml - Network isolation
networks:
  frontend:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.1.0/24
  backend:
    driver: bridge
    internal: true
    ipam:
      config:
        - subnet: 172.20.2.0/24
  database:
    driver: bridge
    internal: true
    ipam:
      config:
        - subnet: 172.20.3.0/24

services:
  nginx:
    networks:
      - frontend
      - backend

  project-context:
    networks:
      - backend
      - database

  postgres:
    networks:
      - database
```

## 🔍 Container Security

### Base Image Security
```dockerfile
# Use official, minimal base images
FROM python:3.11-slim-bullseye

# Update packages and remove package manager cache
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        curl \
        libpq5 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
```

### Non-root User
```dockerfile
# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set proper ownership
RUN chown -R appuser:appuser /app
USER appuser
```

### Security Scanning
```bash
# Scan container images
docker scan project-context:latest

# Use Trivy for vulnerability scanning
trivy image project-context:latest

# Use Snyk for dependency scanning
snyk container test project-context:latest
```

### Runtime Security
```yaml
# docker-compose.prod.yml security options
services:
  project-context:
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
      - /var/tmp
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
```

## 🗄️ Database Security

### PostgreSQL Hardening

#### Authentication
```bash
# postgresql.conf security settings
password_encryption = scram-sha-256
ssl = on
ssl_cert_file = '/var/lib/postgresql/server.crt'
ssl_key_file = '/var/lib/postgresql/server.key'
```

#### Access Control
```bash
# pg_hba.conf
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all            postgres                                peer
host    unified_context opsvi          172.20.0.0/16          scram-sha-256
host    all            all            0.0.0.0/0               reject
```

#### Connection Security
```bash
# Connection limits
max_connections = 100
superuser_reserved_connections = 3

# Logging
log_connections = on
log_disconnections = on
log_failed_connection_attempts = on
log_statement = 'mod'
```

#### Data Encryption
```bash
# Enable transparent data encryption
# This requires PostgreSQL compiled with SSL support
ssl_ciphers = 'HIGH:MEDIUM:+3DES:!aNULL'
ssl_prefer_server_ciphers = on
```

### Redis Security

#### Authentication
```bash
# redis.conf security settings
requirepass your-secure-redis-password-here
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command KEYS ""
rename-command CONFIG "CONFIG_b8f9e3a2d1c4"
```

#### Network Binding
```bash
# Bind to specific interfaces only
bind 127.0.0.1 172.20.0.2

# Disable protected mode only in secure environments
protected-mode yes
```

## 🛡️ Application Security

### Input Validation

```python
from pydantic import BaseModel, validator, Field
from typing import Optional
import re

class FilePathRequest(BaseModel):
    file_path: str = Field(..., max_length=1000)
    include_content: Optional[bool] = False

    @validator('file_path')
    def validate_file_path(cls, v):
        # Prevent path traversal attacks
        if '..' in v or v.startswith('/'):
            raise ValueError('Invalid file path')

        # Allow only safe characters
        if not re.match(r'^[a-zA-Z0-9._/-]+$', v):
            raise ValueError('File path contains invalid characters')

        return v

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    limit: Optional[int] = Field(default=50, ge=1, le=1000)

    @validator('query')
    def validate_query(cls, v):
        # Sanitize search query
        dangerous_patterns = ['<script>', 'javascript:', 'data:']
        for pattern in dangerous_patterns:
            if pattern.lower() in v.lower():
                raise ValueError('Query contains dangerous content')
        return v
```

### SQL Injection Prevention

```python
import asyncpg
from typing import List, Any

class SecureDatabase:
    def __init__(self, connection_pool):
        self.pool = connection_pool

    async def safe_query(self, query: str, params: List[Any] = None):
        """Execute parameterized queries to prevent SQL injection"""
        async with self.pool.acquire() as conn:
            if params:
                return await conn.fetch(query, *params)
            return await conn.fetch(query)

    async def get_file_info(self, file_path: str):
        """Safe file info query with parameterization"""
        query = """
        SELECT file_path, element_name, element_type, line_start, line_end
        FROM code_elements
        WHERE file_path = $1
        ORDER BY line_start
        """
        return await self.safe_query(query, [file_path])
```

### XSS Prevention

```python
import html
import re
from markupsafe import escape

def sanitize_output(data: dict) -> dict:
    """Sanitize output data to prevent XSS"""
    if isinstance(data, dict):
        return {k: sanitize_output(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_output(item) for item in data]
    elif isinstance(data, str):
        # Escape HTML characters
        sanitized = html.escape(data, quote=True)
        # Remove potentially dangerous content
        sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
        return sanitized
    return data
```

### Security Headers

```python
from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Trust only specific hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["your-domain.com", "*.your-domain.com"]
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "connect-src 'self'"
    )

    return response
```

## 📝 Logging & Monitoring Security

### Secure Logging Configuration

```python
import structlog
import logging
from datetime import datetime
import hashlib

# Configure secure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/security.log'),
        logging.StreamHandler()
    ]
)

security_logger = logging.getLogger('security')

def log_security_event(event_type: str, user_id: str = None, details: dict = None):
    """Log security events with proper sanitization"""

    # Hash sensitive data
    if user_id:
        user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:8]
    else:
        user_hash = "anonymous"

    # Sanitize details
    safe_details = {
        k: str(v)[:100] for k, v in (details or {}).items()
        if k not in ['password', 'token', 'key']
    }

    security_logger.info(
        f"SECURITY_EVENT: {event_type}",
        extra={
            "user_hash": user_hash,
            "timestamp": datetime.utcnow().isoformat(),
            "details": safe_details
        }
    )

# Usage examples
log_security_event("API_KEY_AUTH_SUCCESS", user_id="user123")
log_security_event("RATE_LIMIT_EXCEEDED", details={"ip": "192.168.1.1"})
log_security_event("SUSPICIOUS_FILE_ACCESS", details={"file": "../../../etc/passwd"})
```

### Monitoring Security Events

```python
# Prometheus security metrics
from prometheus_client import Counter, Histogram, Gauge

# Security metrics
auth_failures = Counter('auth_failures_total', 'Authentication failures', ['reason'])
suspicious_requests = Counter('suspicious_requests_total', 'Suspicious requests', ['type'])
rate_limit_hits = Counter('rate_limit_hits_total', 'Rate limit hits', ['endpoint'])

# Monitor security events
def monitor_auth_failure(reason: str):
    auth_failures.labels(reason=reason).inc()
    log_security_event("AUTH_FAILURE", details={"reason": reason})

def monitor_suspicious_request(request_type: str):
    suspicious_requests.labels(type=request_type).inc()
    log_security_event("SUSPICIOUS_REQUEST", details={"type": request_type})
```

## 🔄 Backup Security

### Encrypted Backups

```bash
#!/bin/bash
# Secure backup script with encryption

BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
ENCRYPTED_FILE="${BACKUP_FILE}.gpg"
GPG_RECIPIENT="backup@your-domain.com"

# Create database backup
pg_dump -h postgres -U opsvi unified_context > "$BACKUP_FILE"

# Encrypt backup
gpg --trust-model always --encrypt -r "$GPG_RECIPIENT" "$BACKUP_FILE"

# Secure deletion of unencrypted backup
shred -vfz -n 3 "$BACKUP_FILE"

# Upload encrypted backup to secure storage
aws s3 cp "$ENCRYPTED_FILE" "s3://secure-backups/" --sse AES256

# Clean up
rm "$ENCRYPTED_FILE"
```

### Backup Access Control

```bash
# Set restrictive permissions on backup directory
chmod 700 /backups
chown root:backup-group /backups

# Use separate service account for backups
useradd -r -s /bin/false backup-service
```

## 🚨 Incident Response

### Security Monitoring Alerts

```yaml
# alert.rules.yml - Security alerts
groups:
  - name: security-alerts
    rules:
      - alert: AuthenticationFailures
        expr: rate(auth_failures_total[5m]) > 0.1
        for: 1m
        labels:
          severity: warning
          category: security
        annotations:
          summary: "High authentication failure rate"
          description: "{{ $value }} auth failures/sec in the last 5 minutes"

      - alert: SuspiciousActivity
        expr: rate(suspicious_requests_total[5m]) > 0.05
        for: 1m
        labels:
          severity: critical
          category: security
        annotations:
          summary: "Suspicious activity detected"
          description: "{{ $value }} suspicious requests/sec detected"

      - alert: RateLimitExceeded
        expr: rate(rate_limit_hits_total[1m]) > 10
        for: 1m
        labels:
          severity: warning
          category: security
        annotations:
          summary: "Rate limiting triggered frequently"
          description: "Rate limit hit {{ $value }} times/sec"
```

### Automated Response

```python
import requests
from datetime import datetime, timedelta

class SecurityAutomation:
    def __init__(self):
        self.blocked_ips = set()
        self.suspicious_patterns = {}

    def analyze_request(self, request):
        """Analyze incoming requests for suspicious patterns"""

        # Check for SQL injection patterns
        sql_patterns = ['union select', 'drop table', '--', ';--']
        if any(pattern in request.body.lower() for pattern in sql_patterns):
            self.handle_sql_injection_attempt(request.remote_addr)

        # Check for path traversal
        if '../' in request.path or '..\\' in request.path:
            self.handle_path_traversal_attempt(request.remote_addr)

        # Rate limiting per IP
        if self.check_rate_limit_exceeded(request.remote_addr):
            self.temporarily_block_ip(request.remote_addr)

    def handle_sql_injection_attempt(self, ip_address):
        """Respond to SQL injection attempts"""
        log_security_event("SQL_INJECTION_ATTEMPT", details={"ip": ip_address})
        self.temporarily_block_ip(ip_address, duration_minutes=60)
        self.send_security_alert("SQL Injection attempt", ip_address)

    def temporarily_block_ip(self, ip_address, duration_minutes=30):
        """Temporarily block an IP address"""
        self.blocked_ips.add(ip_address)

        # Schedule removal (in production, use Redis with TTL)
        # This is a simplified example
        unblock_time = datetime.now() + timedelta(minutes=duration_minutes)
        log_security_event("IP_BLOCKED", details={
            "ip": ip_address,
            "unblock_time": unblock_time.isoformat()
        })

    def send_security_alert(self, alert_type, details):
        """Send security alert to monitoring systems"""
        if hasattr(self, 'slack_webhook_url'):
            requests.post(self.slack_webhook_url, json={
                "text": f"🚨 Security Alert: {alert_type}\nDetails: {details}"
            })
```

## 🔧 Security Maintenance

### Regular Security Tasks

#### Daily Tasks
```bash
#!/bin/bash
# Daily security maintenance

# Check for failed authentication attempts
grep "AUTH_FAILURE" /app/logs/security.log | tail -20

# Monitor disk usage for log files
df -h /app/logs

# Check SSL certificate expiry
openssl x509 -in ssl/cert.pem -noout -dates

# Verify backup completion
ls -la database/backups/ | grep $(date +%Y%m%d)
```

#### Weekly Tasks
```bash
#!/bin/bash
# Weekly security maintenance

# Update container images
docker-compose -f docker-compose.prod.yml pull

# Scan for vulnerabilities
docker scan project-context:latest

# Rotate logs
logrotate /etc/logrotate.d/project-context

# Generate security report
python3 scripts/generate_security_report.py
```

#### Monthly Tasks
```bash
#!/bin/bash
# Monthly security maintenance

# Rotate API keys
# Generate new API key
NEW_API_KEY=$(openssl rand -hex 32)
echo "New API key generated: $NEW_API_KEY"

# Update dependency scan
snyk test --all-projects

# Review and update firewall rules
ufw status numbered

# Backup security logs
tar -czf security_logs_$(date +%Y%m).tar.gz /app/logs/security.log*
```

### Security Compliance

#### SOC 2 Compliance Checklist
- [ ] Data encryption at rest and in transit
- [ ] Access controls and authentication
- [ ] Logging and monitoring
- [ ] Incident response procedures
- [ ] Regular security assessments
- [ ] Backup and recovery procedures

#### GDPR Compliance
- [ ] Data minimization practices
- [ ] Right to erasure implementation
- [ ] Data protection impact assessments
- [ ] Privacy by design principles
- [ ] Data breach notification procedures

### Vulnerability Management

```python
# Automated vulnerability scanning
import subprocess
import json
from datetime import datetime

class VulnerabilityScanner:
    def __init__(self):
        self.scanners = ['trivy', 'snyk', 'safety']

    def run_security_scan(self):
        """Run comprehensive security scan"""
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'scans': {}
        }

        # Container vulnerability scan
        try:
            trivy_result = subprocess.run([
                'trivy', 'image', '--format', 'json', 'project-context:latest'
            ], capture_output=True, text=True)

            results['scans']['container'] = json.loads(trivy_result.stdout)
        except Exception as e:
            results['scans']['container'] = {'error': str(e)}

        # Python dependency scan
        try:
            safety_result = subprocess.run([
                'safety', 'check', '--json'
            ], capture_output=True, text=True)

            results['scans']['dependencies'] = json.loads(safety_result.stdout)
        except Exception as e:
            results['scans']['dependencies'] = {'error': str(e)}

        return results

    def generate_security_report(self, scan_results):
        """Generate security report from scan results"""
        critical_issues = 0
        high_issues = 0

        # Count vulnerabilities by severity
        for scan_name, scan_data in scan_results['scans'].items():
            if 'Results' in scan_data:
                for result in scan_data['Results']:
                    for vuln in result.get('Vulnerabilities', []):
                        severity = vuln.get('Severity', '').upper()
                        if severity == 'CRITICAL':
                            critical_issues += 1
                        elif severity == 'HIGH':
                            high_issues += 1

        return {
            'scan_date': scan_results['timestamp'],
            'critical_vulnerabilities': critical_issues,
            'high_vulnerabilities': high_issues,
            'requires_immediate_attention': critical_issues > 0
        }
```

## 📞 Security Contacts

### Incident Response Team
- **Primary**: security@your-domain.com
- **Emergency**: +1-XXX-XXX-XXXX
- **Slack**: #security-incidents

### External Resources
- **CVE Database**: https://cve.mitre.org/
- **Security Advisories**: https://github.com/advisories
- **OWASP**: https://owasp.org/

---

## ⚠️ Security Reminder

**This security guide must be reviewed and updated regularly. Security is an ongoing process, not a one-time setup.**

- Review security measures monthly
- Update all dependencies regularly
- Monitor security advisories
- Conduct regular penetration testing
- Train team members on security best practices

**Report security issues immediately to security@your-domain.com**
