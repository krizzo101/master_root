# Multi-stage build for production
FROM python:3.10-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Copy requirements
COPY requirements.txt .
COPY requirements-prod.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements-prod.txt

# Production stage
FROM python:3.10-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r sleuth && useradd -r -g sleuth sleuth

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/sleuth/.local

# Copy application code
COPY --chown=sleuth:sleuth . .

# Set Python path
ENV PATH=/home/sleuth/.local/bin:$PATH
ENV PYTHONPATH=/app:$PYTHONPATH

# Create directories for logs and data
RUN mkdir -p /var/log/sleuth-intel /var/lib/sleuth-intel \
    && chown -R sleuth:sleuth /var/log/sleuth-intel /var/lib/sleuth-intel

# Switch to non-root user
USER sleuth

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose ports
EXPOSE 8000 9090

# Run the application
CMD ["gunicorn", "--config", "config/gunicorn.py", "src.api.app:app"]
