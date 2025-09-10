#!/bin/bash
# Automated Knowledge System Recovery

set -e

echo "🚨 Knowledge System Recovery Tool"
echo "================================="
echo ""

# Stop any existing services
echo "🛑 Stopping existing services..."
docker-compose -f docker-compose.knowledge.yml down 2>/dev/null || true

# Clean up any corrupted volumes
echo "🧹 Cleaning up old volumes..."
docker volume rm master_root_neo4j_data 2>/dev/null || true
docker volume rm master_root_neo4j_logs 2>/dev/null || true
docker volume rm master_root_embedding_cache 2>/dev/null || true

# Rebuild containers
echo "🔨 Rebuilding containers..."
docker-compose -f docker-compose.knowledge.yml build --no-cache

# Start services
echo "🚀 Starting Neo4j..."
docker-compose -f docker-compose.knowledge.yml up -d neo4j

# Wait for Neo4j
echo "⏳ Waiting for Neo4j to be ready..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker-compose -f docker-compose.knowledge.yml exec neo4j cypher-shell -u neo4j -p password "RETURN 1" > /dev/null 2>&1; then
        echo "✅ Neo4j is ready!"
        break
    fi
    echo -n "."
    sleep 2
    attempt=$((attempt+1))
done
echo ""

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Neo4j failed to start"
    echo "Check logs: docker-compose -f docker-compose.knowledge.yml logs neo4j"
    exit 1
fi

# Initialize schema
echo "📝 Initializing database schema..."
docker-compose -f docker-compose.knowledge.yml exec neo4j cypher-shell -u neo4j -p password < /home/opsvi/master_root/neo4j-init/schema.cypher

# Start embedding service
echo "🚀 Starting embedding service..."
docker-compose -f docker-compose.knowledge.yml up -d embedding-service

# Check for backups
BACKUP_DIR="/home/opsvi/master_root/knowledge-backups"
if [ -d "$BACKUP_DIR" ]; then
    LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/*.tar.gz 2>/dev/null | head -1)
    if [ -n "$LATEST_BACKUP" ]; then
        echo ""
        echo "📦 Found backup: $(basename "$LATEST_BACKUP")"
        read -p "Restore from this backup? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            ./scripts/knowledge-restore.sh "$LATEST_BACKUP"
        fi
    fi
fi

# Run health check
echo ""
echo "🏥 Running health check..."
./scripts/knowledge-health.sh

echo ""
echo "✅ Recovery complete!"
echo ""
echo "📊 Access points:"
echo "  Neo4j Browser: http://localhost:7474"
echo "  Embedding API: http://localhost:8000"
echo "  API Docs:      http://localhost:8000/docs"
