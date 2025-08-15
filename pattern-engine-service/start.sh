#!/bin/bash
# Start distributed pattern engine service

echo "🚀 Starting Distributed Pattern Engine Service"
echo "============================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install docker-compose first."
    exit 1
fi

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/node1 data/node2 data/node3

# Build images
echo "🔨 Building Docker images..."
docker-compose build

# Start services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check health
echo "🏥 Checking service health..."
for port in 8001 8002 8003; do
    if curl -s "http://localhost:$port/health" > /dev/null; then
        echo "  ✅ Node on port $port is healthy"
    else
        echo "  ❌ Node on port $port is not responding"
    fi
done

echo ""
echo "✅ Pattern Engine Service is running!"
echo ""
echo "Services:"
echo "  • Pattern Engine Node 1: http://localhost:8001"
echo "  • Pattern Engine Node 2: http://localhost:8002"
echo "  • Pattern Engine Node 3: http://localhost:8003"
echo "  • Load Balancer: http://localhost:80"
echo "  • Redis: localhost:6379"
echo "  • Prometheus: http://localhost:9090"
echo "  • Grafana: http://localhost:3000 (admin/admin)"
echo ""
echo "To run the demonstration:"
echo "  python demo_distributed.py"
echo ""
echo "To stop all services:"
echo "  docker-compose down"
echo ""