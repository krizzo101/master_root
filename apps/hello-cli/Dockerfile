# Multi-stage Dockerfile for Hello CLI
# Stage 1: Builder
FROM python:3.11-slim as builder

# Set build arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=1.0.0

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Copy package files
COPY pyproject.toml setup.cfg ./
COPY src/ ./src/

# Install build tools and create wheel
RUN pip install --no-cache-dir build && \
    python -m build --wheel

# Stage 2: Runtime
FROM python:3.11-slim

# Labels for image metadata
LABEL org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.title="hello-cli" \
      org.opencontainers.image.description="Production-ready Hello World CLI application" \
      org.opencontainers.image.url="https://github.com/opsvi/hello-cli" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.vendor="OPSVI" \
      org.opencontainers.image.licenses="MIT"

# Security: Create non-root user
RUN useradd -m -u 1000 -s /bin/bash appuser && \
    mkdir -p /app /var/log/hello-cli && \
    chown -R appuser:appuser /app /var/log/hello-cli

# Set working directory
WORKDIR /app

# Switch to non-root user
USER appuser

# Copy wheel from builder stage
COPY --from=builder --chown=appuser:appuser /build/dist/*.whl ./

# Install the application
RUN pip install --user --no-cache-dir *.whl && \
    rm *.whl

# Add user's local bin to PATH
ENV PATH="/home/appuser/.local/bin:${PATH}"

# Set environment variables
ENV HELLO_CLI_LOG_LEVEL=INFO \
    HELLO_CLI_COLOR_OUTPUT=true \
    PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD hello-cli --version || exit 1

# Default entrypoint and command
ENTRYPOINT ["hello-cli"]
CMD ["hello", "World"]
