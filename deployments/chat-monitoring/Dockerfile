# Multi-stage build for chat monitoring system
FROM python:3.11-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tmux \
    inotify-tools \
    jq \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m -u 1000 app
WORKDIR /app

FROM base AS python-deps
# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS runtime
COPY --from=python-deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=python-deps /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=app:app . .

USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0 if __import__('requests').get('http://localhost:8080/health').status_code == 200 else 1)" || exit 1

EXPOSE 8080

CMD ["python", "-m", "opsvi_monitoring.chat_analytics.realtime_ingestion.service_runner", "start"]
