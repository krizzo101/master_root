FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt* ./
RUN pip install --no-cache-dir -r requirements.txt || pip install --no-cache-dir \
    openai>=1.0.0 \
    anthropic>=0.7.0 \
    asyncio-throttle \
    aiofiles \
    pydantic>=2.0.0 \
    python-dotenv

# Copy application code
COPY src/ ./src/
COPY *.py ./
COPY *.json ./
COPY docker-compose.yml ./

# Create output directories
RUN mkdir -p outputs logs checkpoints

# Set Python path
ENV PYTHONPATH=/app/src

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from src.generic_orchestrator import GenericOrchestrator; print('Health check passed')" || exit 1

# Default command
CMD ["python", "run_apps_audit.py"]
