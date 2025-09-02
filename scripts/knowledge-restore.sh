#!/bin/bash
# Restore Knowledge System from Backup

set -e

BACKUP_DIR="/home/opsvi/master_root/knowledge-backups"

# Parse arguments
RESTORE_FILE=""
if [ "$1" == "--latest" ]; then
    RESTORE_FILE=$(ls -t "${BACKUP_DIR}"/*.tar.gz 2>/dev/null | head -1)
elif [ "$1" == "--date" ] && [ -n "$2" ]; then
    RESTORE_FILE=$(ls "${BACKUP_DIR}"/knowledge_backup_"$2"*.tar.gz 2>/dev/null | head -1)
elif [ -f "$1" ]; then
    RESTORE_FILE="$1"
else
    echo "Usage: $0 [--latest | --date YYYYMMDD | backup_file.tar.gz]"
    echo ""
    echo "Available backups:"
    ls -lah "${BACKUP_DIR}"/*.tar.gz 2>/dev/null || echo "No backups found"
    exit 1
fi

if [ -z "$RESTORE_FILE" ] || [ ! -f "$RESTORE_FILE" ]; then
    echo "❌ Backup file not found: $RESTORE_FILE"
    exit 1
fi

echo "🔄 Restoring from: $(basename "$RESTORE_FILE")"
echo "⚠️  WARNING: This will replace all current data!"
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore cancelled"
    exit 0
fi

# Extract backup
TEMP_DIR="/tmp/knowledge_restore_$$"
mkdir -p "$TEMP_DIR"
echo "📦 Extracting backup..."
tar xzf "$RESTORE_FILE" -C "$TEMP_DIR"
BACKUP_NAME=$(ls "$TEMP_DIR")

# Stop services
echo "🛑 Stopping services..."
docker-compose -f docker-compose.knowledge.yml down

# Clear existing data
echo "🧹 Clearing existing data..."
docker volume rm master_root_neo4j_data 2>/dev/null || true
docker volume create master_root_neo4j_data

# Restore Docker volume
if [ -f "$TEMP_DIR/$BACKUP_NAME/neo4j_data.tar.gz" ]; then
    echo "🐳 Restoring Docker volume..."
    docker run --rm \
      -v master_root_neo4j_data:/data \
      -v "$TEMP_DIR/$BACKUP_NAME":/backup \
      alpine tar xzf /backup/neo4j_data.tar.gz -C /data
fi

# Start Neo4j
echo "🚀 Starting Neo4j..."
docker-compose -f docker-compose.knowledge.yml up -d neo4j

# Wait for Neo4j
echo "⏳ Waiting for Neo4j to start..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker-compose -f docker-compose.knowledge.yml exec neo4j cypher-shell -u neo4j -p password "RETURN 1" > /dev/null 2>&1; then
        echo "✅ Neo4j is ready!"
        break
    fi
    sleep 2
    attempt=$((attempt+1))
done

# If volume restore didn't work, use Cypher restore
if [ -f "$TEMP_DIR/$BACKUP_NAME/backup.cypher" ] && [ $attempt -eq $max_attempts ]; then
    echo "📝 Restoring from Cypher export..."

    # Initialize schema first
    docker-compose -f docker-compose.knowledge.yml exec neo4j cypher-shell -u neo4j -p password < /home/opsvi/master_root/neo4j-init/schema.cypher

    # Then restore data
    docker-compose -f docker-compose.knowledge.yml exec neo4j cypher-shell -u neo4j -p password < "$TEMP_DIR/$BACKUP_NAME/backup.cypher"
fi

# Start embedding service
echo "🚀 Starting embedding service..."
docker-compose -f docker-compose.knowledge.yml up -d embedding-service

# Display statistics
if [ -f "$TEMP_DIR/$BACKUP_NAME/stats.json" ]; then
    echo ""
    echo "📊 Restored database statistics:"
    cat "$TEMP_DIR/$BACKUP_NAME/stats.json" | jq '.'
fi

# Clean up
rm -rf "$TEMP_DIR"

# Verify restoration
echo ""
echo "🔍 Verifying restoration..."
docker-compose -f docker-compose.knowledge.yml exec neo4j cypher-shell -u neo4j -p password << 'EOF'
MATCH (n:Knowledge)
RETURN count(n) as knowledge_count;
EOF

echo ""
echo "✅ Restore completed successfully!"
echo "🌐 Neo4j Browser: http://localhost:7474"
echo "🔌 Services are running and ready to use"
