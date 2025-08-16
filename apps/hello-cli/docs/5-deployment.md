# Hello CLI - Deployment Documentation

## Phase: Deployment
**Date**: 2025-08-16
**Version**: 1.0.0
**Status**: Production-Ready

## Table of Contents
1. [Installation Instructions](#installation-instructions)
2. [Configuration Guide](#configuration-guide)
3. [Docker Setup](#docker-setup)
4. [CI/CD Pipeline](#cicd-pipeline)
5. [Deployment Strategies](#deployment-strategies)
6. [Monitoring & Logging](#monitoring--logging)
7. [Rollback Procedures](#rollback-procedures)
8. [Troubleshooting](#troubleshooting)

## Installation Instructions

### System Requirements
- Python 3.8 or higher
- pip package manager
- Optional: Docker for containerized deployment

### Installation Methods

#### 1. From PyPI (Production)
```bash
pip install hello-cli
```

#### 2. From Source (Development)
```bash
# Clone the repository
git clone https://github.com/opsvi/hello-cli.git
cd hello-cli

# Install in development mode
pip install -e .[dev]
```

#### 3. From GitHub Release
```bash
# Download the latest release
curl -L https://github.com/opsvi/hello-cli/releases/latest/download/hello-cli.tar.gz -o hello-cli.tar.gz

# Extract and install
tar -xzf hello-cli.tar.gz
cd hello-cli
pip install .
```

#### 4. Using pipx (Isolated Environment)
```bash
pipx install hello-cli
```

### Verification
```bash
# Check installation
hello-cli --version

# Run test command
hello-cli hello World

# Run with verbose output
hello-cli hello World --verbose
```

## Configuration Guide

### Environment Variables
The application supports the following environment variables:

```bash
# Logging configuration
export HELLO_CLI_LOG_LEVEL=INFO  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
export HELLO_CLI_LOG_FILE=/var/log/hello-cli.log  # Log file path

# Feature flags
export HELLO_CLI_COLOR_OUTPUT=true  # Enable/disable colored output
export HELLO_CLI_UPPERCASE=false    # Force uppercase output

# Performance tuning
export HELLO_CLI_MAX_NAME_LENGTH=100  # Maximum allowed name length
```

### Configuration File
Create a configuration file at `~/.hello-cli/config.yaml`:

```yaml
# ~/.hello-cli/config.yaml
logging:
  level: INFO
  file: /var/log/hello-cli.log
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

output:
  color: true
  uppercase: false

validation:
  max_name_length: 100
  allowed_characters: "a-zA-Z0-9 -_"
```

### Per-Project Configuration
Place a `.hello-cli.json` file in your project root:

```json
{
  "defaultName": "World",
  "defaultGreeting": "Hello",
  "outputFormat": "plain",
  "colorOutput": true
}
```

## Docker Setup

### Dockerfile
```dockerfile
# Multi-stage build for minimal image size
FROM python:3.11-slim as builder

WORKDIR /build
COPY pyproject.toml setup.cfg ./
COPY src/ ./src/
RUN pip install --no-cache-dir build && \
    python -m build --wheel

FROM python:3.11-slim

# Security: Run as non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

WORKDIR /app
USER appuser

# Copy wheel from builder
COPY --from=builder --chown=appuser:appuser /build/dist/*.whl ./
RUN pip install --user --no-cache-dir *.whl && \
    rm *.whl

# Add user's local bin to PATH
ENV PATH="/home/appuser/.local/bin:${PATH}"

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD hello-cli --version || exit 1

ENTRYPOINT ["hello-cli"]
CMD ["hello", "World"]
```

### Docker Compose
```yaml
version: '3.8'

services:
  hello-cli:
    build:
      context: .
      dockerfile: Dockerfile
    image: hello-cli:latest
    container_name: hello-cli
    environment:
      - HELLO_CLI_LOG_LEVEL=INFO
      - HELLO_CLI_COLOR_OUTPUT=true
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 128M
        reservations:
          cpus: '0.1'
          memory: 64M
```

### Building and Running
```bash
# Build Docker image
docker build -t hello-cli:latest .

# Run container
docker run --rm hello-cli hello Docker

# Run with environment variables
docker run --rm -e HELLO_CLI_LOG_LEVEL=DEBUG hello-cli hello Docker --verbose

# Using docker-compose
docker-compose up -d
docker-compose exec hello-cli hello Docker
```

## CI/CD Pipeline

### GitHub Actions
`.github/workflows/deploy.yml`:
```yaml
name: Deploy

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.8', '3.9', '3.10', '3.11', '3.12']
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: |
          pip install -e .[dev]
      - name: Run tests
        run: |
          pytest --cov=hello_cli
          mypy src/hello_cli
          ruff check src/
          black --check src/

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Build package
        run: |
          pip install build
          python -m build
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: dist
          path: dist/

  deploy-pypi:
    needs: build
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/')
    steps:
      - uses: actions/download-artifact@v3
        with:
          name: dist
          path: dist/
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          password: ${{ secrets.PYPI_API_TOKEN }}

  deploy-docker:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      - name: Login to DockerHub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_TOKEN }}
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            opsvi/hello-cli:latest
            opsvi/hello-cli:${{ github.ref_name }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### GitLab CI
`.gitlab-ci.yml`:
```yaml
stages:
  - test
  - build
  - deploy

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip

test:
  stage: test
  image: python:3.11
  script:
    - pip install -e .[dev]
    - pytest --cov=hello_cli --junitxml=report.xml
    - mypy src/hello_cli
    - ruff check src/
  artifacts:
    reports:
      junit: report.xml
    expire_in: 1 week

build:
  stage: build
  image: python:3.11
  script:
    - pip install build
    - python -m build
  artifacts:
    paths:
      - dist/
    expire_in: 1 week

deploy:pypi:
  stage: deploy
  image: python:3.11
  script:
    - pip install twine
    - twine upload dist/*
  environment:
    name: production
  only:
    - tags
  variables:
    TWINE_USERNAME: __token__
    TWINE_PASSWORD: $PYPI_TOKEN

deploy:docker:
  stage: deploy
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_TAG .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_TAG
    - docker tag $CI_REGISTRY_IMAGE:$CI_COMMIT_TAG $CI_REGISTRY_IMAGE:latest
    - docker push $CI_REGISTRY_IMAGE:latest
  only:
    - tags
```

## Deployment Strategies

### Blue-Green Deployment
```bash
# Deploy to green environment
docker-compose -f docker-compose.green.yml up -d

# Test green environment
./scripts/health-check.sh green

# Switch traffic to green
./scripts/switch-traffic.sh green

# Remove blue environment
docker-compose -f docker-compose.blue.yml down
```

### Rolling Update (Kubernetes)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hello-cli
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 1
  selector:
    matchLabels:
      app: hello-cli
  template:
    metadata:
      labels:
        app: hello-cli
    spec:
      containers:
      - name: hello-cli
        image: opsvi/hello-cli:latest
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "500m"
        livenessProbe:
          exec:
            command:
            - hello-cli
            - --version
          initialDelaySeconds: 5
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - hello-cli
            - hello
            - HealthCheck
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Canary Deployment
```bash
# Deploy canary version (10% traffic)
kubectl apply -f manifests/canary-deployment.yaml

# Monitor metrics
./scripts/monitor-canary.sh

# If successful, increase traffic
kubectl patch deployment hello-cli-canary \
  -p '{"spec":{"replicas":2}}'

# Full rollout
kubectl set image deployment/hello-cli \
  hello-cli=opsvi/hello-cli:new-version
```

## Monitoring & Logging

### Application Metrics
Configure monitoring with Prometheus metrics:

```python
# Metrics endpoint configuration
METRICS_PORT = 8080
METRICS_PATH = "/metrics"
```

### Log Aggregation
```yaml
# Fluentd configuration
<source>
  @type tail
  path /var/log/hello-cli/*.log
  pos_file /var/log/fluentd/hello-cli.pos
  tag hello-cli
  <parse>
    @type json
  </parse>
</source>

<match hello-cli.**>
  @type elasticsearch
  host elasticsearch.local
  port 9200
  logstash_format true
  logstash_prefix hello-cli
</match>
```

### Alerts
```yaml
# Prometheus alert rules
groups:
  - name: hello-cli
    rules:
      - alert: HighErrorRate
        expr: rate(hello_cli_errors_total[5m]) > 0.1
        for: 5m
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors/sec"

      - alert: SlowResponse
        expr: hello_cli_response_time_seconds > 1
        for: 5m
        annotations:
          summary: "Slow response time"
          description: "Response time is {{ $value }} seconds"
```

## Rollback Procedures

### Version Rollback
```bash
# Tag current version before deployment
git tag -a rollback-$(date +%Y%m%d-%H%M%S) -m "Rollback point"

# Quick rollback to previous version
pip install hello-cli==0.9.0

# Docker rollback
docker run --rm opsvi/hello-cli:v0.9.0

# Kubernetes rollback
kubectl rollout undo deployment/hello-cli
kubectl rollout status deployment/hello-cli
```

### Database Migration Rollback
```bash
# Not applicable for this CLI tool
# Included for reference in case of future database integration
```

### Feature Flag Disable
```bash
# Disable feature without redeployment
export HELLO_CLI_FEATURE_NEW_FORMAT=false
```

## Troubleshooting

### Common Issues

#### Installation Fails
```bash
# Clear pip cache
pip cache purge

# Install with verbose output
pip install -v hello-cli

# Check Python version
python --version  # Must be >= 3.8
```

#### Command Not Found
```bash
# Check installation
pip show hello-cli

# Add to PATH
export PATH="$HOME/.local/bin:$PATH"

# Reinstall
pip uninstall hello-cli && pip install hello-cli
```

#### Permission Denied
```bash
# Install for user
pip install --user hello-cli

# Or use virtual environment
python -m venv venv
source venv/bin/activate
pip install hello-cli
```

#### Docker Issues
```bash
# Check Docker daemon
docker version

# Clean up resources
docker system prune -a

# Rebuild without cache
docker build --no-cache -t hello-cli .
```

### Debug Mode
```bash
# Enable debug logging
export HELLO_CLI_LOG_LEVEL=DEBUG

# Run with verbose output
hello-cli hello World --verbose

# Check logs
tail -f /var/log/hello-cli.log
```

### Support Channels
- GitHub Issues: https://github.com/opsvi/hello-cli/issues
- Documentation: https://docs.opsvi.com/hello-cli
- Email: support@opsvi.com

## Security Considerations

### Secret Management
- Never hardcode credentials
- Use environment variables for sensitive data
- Rotate secrets regularly
- Use secret management tools (Vault, AWS Secrets Manager)

### Container Security
- Run as non-root user
- Use minimal base images
- Scan images for vulnerabilities
- Keep dependencies updated

### Network Security
- Use TLS for all communications
- Implement rate limiting
- Validate all inputs
- Use least privilege principle

## Performance Optimization

### Caching
```bash
# Enable pip cache
export PIP_CACHE_DIR=/cache/pip

# Docker layer caching
docker build --cache-from hello-cli:latest -t hello-cli:new .
```

### Resource Limits
```yaml
# Kubernetes resource limits
resources:
  requests:
    memory: "64Mi"
    cpu: "100m"
  limits:
    memory: "128Mi"
    cpu: "500m"
```

## Deployment Checklist

- [ ] All tests passing
- [ ] Code review completed
- [ ] Documentation updated
- [ ] Security scan passed
- [ ] Performance benchmarks met
- [ ] Dependencies locked (requirements.txt/pyproject.toml)
- [ ] Configuration externalized
- [ ] Secrets management configured
- [ ] Monitoring configured
- [ ] Rollback plan prepared
- [ ] Deployment scripts tested
- [ ] Health checks configured
- [ ] Alerts configured
- [ ] Backup strategy in place
- [ ] Disaster recovery plan documented

---

**Document Version**: 1.0.0
**Last Updated**: 2025-08-16
**Next Review**: 2025-09-16
