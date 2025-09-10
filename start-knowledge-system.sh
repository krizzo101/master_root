#!/bin/bash
# Start the Knowledge System with Docker

set -e

echo "🚀 Starting Knowledge System with Docker..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Stop any existing containers
echo "🛑 Stopping any existing containers..."
docker-compose -f docker-compose.knowledge.yml down 2>/dev/null || true

# Pull latest images
echo "📦 Pulling latest images..."
docker-compose -f docker-compose.knowledge.yml pull neo4j

# Build embedding service
echo "🔨 Building embedding service..."
docker-compose -f docker-compose.knowledge.yml build embedding-service

# Start services
echo "🚀 Starting services..."
docker-compose -f docker-compose.knowledge.yml up -d neo4j
echo "⏳ Waiting for Neo4j to be healthy..."
sleep 10

# Wait for Neo4j to be ready
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker-compose -f docker-compose.knowledge.yml exec neo4j cypher-shell -u neo4j -p password "RETURN 1" > /dev/null 2>&1; then
        echo "✅ Neo4j is ready!"
        break
    fi
    echo "⏳ Waiting for Neo4j... (attempt $((attempt+1))/$max_attempts)"
    sleep 2
    attempt=$((attempt+1))
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Neo4j failed to start. Check logs with: docker-compose -f docker-compose.knowledge.yml logs neo4j"
    exit 1
fi

# Start embedding service
echo "🚀 Starting embedding service..."
docker-compose -f docker-compose.knowledge.yml up -d embedding-service

# Initialize database schema
echo "📝 Initializing database schema..."
docker-compose -f docker-compose.knowledge.yml exec -T neo4j cypher-shell -u neo4j -p password < /home/opsvi/master_root/neo4j-init/schema.cypher || {
    echo "⚠️  Schema initialization failed, trying alternative method..."
    docker exec knowledge-neo4j cypher-shell -u neo4j -p password < /home/opsvi/master_root/neo4j-init/schema.cypher
}

# Check services
echo ""
echo "✅ Knowledge System started successfully!"
echo ""
echo "📊 Service URLs:"
echo "  - Neo4j Browser: http://localhost:7474"
echo "  - Neo4j Bolt:    bolt://localhost:7687"
echo "  - Embedding API: http://localhost:8000"
echo ""
echo "🔑 Credentials:"
echo "  - Username: neo4j"
echo "  - Password: password"
echo ""
echo "📝 Useful commands:"
echo "  - View logs:     docker-compose -f docker-compose.knowledge.yml logs -f"
echo "  - Stop services: docker-compose -f docker-compose.knowledge.yml down"
echo "  - Restart:       docker-compose -f docker-compose.knowledge.yml restart"
echo ""
