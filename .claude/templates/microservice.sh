#!/bin/bash
# Microservice Template Generator

SERVICE_NAME=${1:-"new-service"}
SERVICE_PATH=${2:-"."}
SERVICE_TYPE=${3:-"fastapi"}  # fastapi, flask, express

echo "🚀 Creating microservice: $SERVICE_NAME ($SERVICE_TYPE)"

mkdir -p "$SERVICE_PATH/$SERVICE_NAME"
cd "$SERVICE_PATH/$SERVICE_NAME"

# Create directory structure
mkdir -p {src/{api,models,services,utils},tests,config,scripts,docs}

if [ "$SERVICE_TYPE" == "fastapi" ]; then
    # FastAPI microservice
    cat > requirements.txt << EOF
fastapi==0.104.0
uvicorn==0.24.0
pydantic==2.4.0
sqlalchemy==2.0.0
alembic==1.12.0
pytest==7.4.0
httpx==0.25.0
python-dotenv==1.0.0
redis==5.0.0
celery==5.3.0
prometheus-client==0.18.0
EOF

    cat > src/main.py << 'EOF'
"""Main FastAPI application"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
import uvicorn

from src.api import health, v1
from src.config import settings

# Create app
app = FastAPI(
    title=settings.SERVICE_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(v1.router, prefix="/api/v1", tags=["v1"])

@app.on_event("startup")
async def startup_event():
    """Startup tasks"""
    print(f"Starting {settings.SERVICE_NAME} v{settings.VERSION}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup tasks"""
    print("Shutting down...")

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
EOF

    cat > src/config.py << EOF
"""Configuration management"""

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SERVICE_NAME: str = "$SERVICE_NAME"
    VERSION: str = "0.1.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql://user:pass@localhost/db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Security
    SECRET_KEY: str = "change-me-in-production"
    ALLOWED_ORIGINS: list = ["*"]

    class Config:
        env_file = ".env"

settings = Settings()
EOF

    cat > Dockerfile << EOF
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

fi

# Create docker-compose.yml
cat > docker-compose.yml << EOF
version: '3.8'

services:
  $SERVICE_NAME:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/dbname
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./src:/app/src

  db:
    image: postgres:15
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: dbname
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
EOF

# Create Makefile
cat > Makefile << EOF
.PHONY: help build run test clean

help:
	@echo "Available commands:"
	@echo "  make build   - Build Docker image"
	@echo "  make run     - Run service locally"
	@echo "  make test    - Run tests"
	@echo "  make clean   - Clean up"

build:
	docker-compose build

run:
	docker-compose up

test:
	pytest tests/ -v --cov=src

clean:
	docker-compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

dev:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

migrate:
	alembic upgrade head

format:
	black src/ tests/
	ruff check --fix src/ tests/
EOF

# Create README
cat > README.md << EOF
# $SERVICE_NAME Microservice

## Quick Start

### Development
\`\`\`bash
# Install dependencies
pip install -r requirements.txt

# Run locally
make dev

# Run with Docker
make run
\`\`\`

### Testing
\`\`\`bash
make test
\`\`\`

## API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Metrics: http://localhost:8000/metrics

## Architecture
- Framework: $SERVICE_TYPE
- Database: PostgreSQL
- Cache: Redis
- Queue: Celery
- Monitoring: Prometheus

## Endpoints
- GET /health - Health check
- GET /api/v1/* - API endpoints
EOF

echo "✅ Microservice '$SERVICE_NAME' created!"
echo "Next steps:"
echo "  cd $SERVICE_PATH/$SERVICE_NAME"
echo "  make build"
echo "  make run"
