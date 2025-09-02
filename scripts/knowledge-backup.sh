#!/bin/bash
# Backup Knowledge System Data

set -e

BACKUP_DIR="/home/opsvi/master_root/knowledge-backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="knowledge_backup_${TIMESTAMP}"

echo "📦 Starting Knowledge System Backup..."

# Create backup directory
mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}"

# Check if Neo4j is running
if ! docker-compose -f docker-compose.knowledge.yml exec neo4j cypher-shell -u neo4j -p password "RETURN 1" > /dev/null 2>&1; then
    echo "⚠️  Neo4j is not running. Starting it..."
    docker-compose -f docker-compose.knowledge.yml up -d neo4j
    sleep 10
fi

# Export Neo4j data using APOC
echo "📊 Exporting Neo4j data..."
docker-compose -f docker-compose.knowledge.yml exec neo4j cypher-shell -u neo4j -p password << 'EOF' > "${BACKUP_DIR}/${BACKUP_NAME}/nodes.json"
CALL apoc.export.json.all(null, {stream: true})
YIELD data
RETURN data
EOF

# Export using Cypher format for easy restore
echo "📝 Creating Cypher export..."
docker-compose -f docker-compose.knowledge.yml exec neo4j cypher-shell -u neo4j -p password << 'EOF' > "${BACKUP_DIR}/${BACKUP_NAME}/backup.cypher"
// Export all nodes
MATCH (n)
WITH collect(n) as nodes
UNWIND nodes as node
WITH node, labels(node) as labels, properties(node) as props
RETURN 'CREATE (' +
       CASE WHEN size(labels) > 0
            THEN ':' + reduce(s = head(labels), l IN tail(labels) | s + ':' + l)
            ELSE ''
       END + ' ' +
       CASE WHEN size(keys(props)) > 0
            THEN apoc.convert.toJson(props)
            ELSE '{}'
       END + ');' as cypher
UNION ALL
// Export all relationships
MATCH ()-[r]->()
WITH collect(DISTINCT r) as rels
UNWIND rels as rel
MATCH (a)-[rel]->(b)
WHERE id(a) < id(b) OR (id(a) = id(b) AND id(rel) = id(rel))
RETURN 'MATCH (a {' +
       COALESCE(reduce(s = '', k in keys(startNode(rel)) |
           s + k + ':' + apoc.convert.toJson(startNode(rel)[k]) + ','), '') +
       '}), (b {' +
       COALESCE(reduce(s = '', k in keys(endNode(rel)) |
           s + k + ':' + apoc.convert.toJson(endNode(rel)[k]) + ','), '') +
       '}) CREATE (a)-[:' + type(rel) + ' ' +
       apoc.convert.toJson(properties(rel)) + ']->(b);' as cypher;
EOF

# Get database statistics
echo "📈 Capturing database statistics..."
docker-compose -f docker-compose.knowledge.yml exec neo4j cypher-shell -u neo4j -p password << 'EOF' > "${BACKUP_DIR}/${BACKUP_NAME}/stats.json"
MATCH (n:Knowledge)
WITH count(n) as total_nodes,
     avg(n.confidence_score) as avg_confidence,
     collect(DISTINCT n.knowledge_type) as types
MATCH ()-[r]->()
WITH total_nodes, avg_confidence, types, count(r) as total_relationships
RETURN {
  timestamp: datetime(),
  total_nodes: total_nodes,
  total_relationships: total_relationships,
  avg_confidence: avg_confidence,
  knowledge_types: types
} as stats
EOF

# Backup Docker volumes
echo "🐳 Backing up Docker volumes..."
docker run --rm \
  -v master_root_neo4j_data:/data \
  -v "${BACKUP_DIR}/${BACKUP_NAME}":/backup \
  alpine tar czf /backup/neo4j_data.tar.gz -C /data .

# Create metadata file
cat > "${BACKUP_DIR}/${BACKUP_NAME}/metadata.json" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "backup_name": "${BACKUP_NAME}",
  "neo4j_version": "5.15.0",
  "backup_type": "full",
  "components": ["neo4j_data", "cypher_export", "statistics"]
}
EOF

# Compress backup
echo "🗜️  Compressing backup..."
cd "${BACKUP_DIR}"
tar czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}/"
rm -rf "${BACKUP_NAME}/"

# Clean old backups (keep last 10)
echo "🧹 Cleaning old backups..."
ls -t "${BACKUP_DIR}"/*.tar.gz 2>/dev/null | tail -n +11 | xargs -r rm

echo "✅ Backup completed: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
echo "📊 Size: $(du -h "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" | cut -f1)"

# List recent backups
echo ""
echo "📁 Recent backups:"
ls -lah "${BACKUP_DIR}"/*.tar.gz 2>/dev/null | tail -5
