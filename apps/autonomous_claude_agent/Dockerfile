# Multi-stage build for Autonomous Claude Agent
# Generated: 2025-08-15
# Base image: Python 3.11 slim

# Stage 1: Builder
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.8.2

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==$POETRY_VERSION

# Set working directory
WORKDIR /build

# Copy dependency files
COPY pyproject.toml requirements.txt ./

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/app/scripts:${PATH}" \
    USER=agent

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    wget \
    vim \
    htop \
    net-tools \
    postgresql-client \
    redis-tools \
    tini \
    && rm -rf /var/lib/apt/lists/*

# Install additional tools for agent operations
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    firefox-esr \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r ${USER} && \
    useradd -r -g ${USER} -d /home/${USER} -s /bin/bash ${USER} && \
    mkdir -p /home/${USER} && \
    chown -R ${USER}:${USER} /home/${USER}

# Create application directories
RUN mkdir -p /app /data /logs /tmp/agent /var/cache/agent && \
    chown -R ${USER}:${USER} /app /data /logs /tmp/agent /var/cache/agent

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=${USER}:${USER} src/ ./src/
COPY --chown=${USER}:${USER} config/ ./config/
COPY --chown=${USER}:${USER} scripts/ ./scripts/
COPY --chown=${USER}:${USER} templates/ ./templates/
COPY --chown=${USER}:${USER} prompts/ ./prompts/

# Copy configuration files
COPY --chown=${USER}:${USER} pyproject.toml requirements.txt ./
COPY --chown=${USER}:${USER} Makefile ./
COPY --chown=${USER}:${USER} .env.example ./.env.example

# Create necessary directories
RUN mkdir -p \
    /app/checkpoints \
    /app/cache \
    /app/exports \
    /app/imports \
    /app/temp \
    && chown -R ${USER}:${USER} /app

# Install playwright browsers (for web scraping)
RUN pip install playwright && \
    playwright install chromium firefox

# Set up health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Switch to non-root user
USER ${USER}

# Expose ports
EXPOSE 8000 8001 9090

# Set entrypoint to tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Default command
CMD ["python", "-m", "autonomous_claude_agent.server"]

# Labels
LABEL maintainer="OpsVi Team <team@opsvi.ai>" \
      version="1.0.0" \
      description="Autonomous Claude Agent with multi-tool orchestration" \
      org.opencontainers.image.source="https://github.com/opsvi/autonomous-claude-agent" \
      org.opencontainers.image.vendor="OpsVi" \
      org.opencontainers.image.title="Autonomous Claude Agent" \
      org.opencontainers.image.description="Production-ready autonomous AI agent" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.created="2025-08-15" \
      org.opencontainers.image.licenses="MIT"