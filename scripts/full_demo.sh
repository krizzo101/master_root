#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Research Assistant Full Demo"
echo "================================"

# Build and start the stack
echo "📦 Building and starting services..."
docker-compose up -d --build

# Wait for health
echo "⏳ Waiting for services to be healthy..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null; then
        echo "✅ Service healthy"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Service failed to start"
        exit 1
    fi
    sleep 2
done

# Send research query
echo "🔍 Sending research query..."
curl -X POST http://localhost:8000/ask \
     -H "Content-Type: application/json" \
     -d '{"query": "What are the latest safety findings on CRISPR gene editing in 2024?"}' \
     | jq '.'

# Stream logs for 5 seconds
echo "📋 Streaming logs for 5 seconds..."
timeout 5 docker logs -f $(docker-compose ps -q app) || true

# Run smoke test
echo "🧪 Running smoke test..."
bash scripts/smoke_test.sh
echo "✅ Smoke test passed"

# Run quality checks
echo "🔍 Running quality checks..."
echo "--- Coverage ---"
pytest --cov=src --cov-report=term-missing || echo "⚠️  Coverage check failed"

echo "--- Security ---"
bandit -r src -ll || echo "⚠️  Security check failed"

echo "--- Secrets ---"
detect-secrets scan --all-files --baseline .secrets.baseline || echo "⚠️  Secret scan failed"

echo "--- Lint ---"
ruff check src tests || echo "⚠️  Lint check failed"

echo "--- Types ---"
mypy src || echo "⚠️  Type check failed"

# Shutdown
echo "🛑 Shutting down..."
docker-compose down

echo "🎉 Demo completed successfully!"
