# Knowledge System Recovery Guide

## Quick Recovery (5 minutes)

If the knowledge system fails, run:
```bash
cd /home/opsvi/master_root
./scripts/knowledge-recovery.sh
```

This will:
1. Stop any existing services
2. Clean up corrupted data
3. Rebuild containers
4. Initialize schema
5. Restore from latest backup (if available)
6. Verify all services are healthy

## Architecture Overview

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   MCP Client     │────▶│  Knowledge Tool  │────▶│     Neo4j DB     │
│  (Claude Code)   │     │   (Python MCP)   │     │  (Docker:7687)   │
└──────────────────┘     └──────────────────┘     └──────────────────┘
                                │                           │
                                ▼                           │
                         ┌──────────────────┐              │
                         │ Embedding Service│◀─────────────┘
                         │  (Docker:8000)   │
                         └──────────────────┘
```

## Component Locations

| Component | Location | Purpose |
|-----------|----------|---------|
| Docker Compose | `/home/opsvi/master_root/docker-compose.knowledge.yml` | Service definitions |
| Neo4j Schema | `/home/opsvi/master_root/neo4j-init/schema.cypher` | Database structure |
| Embedding API | `/home/opsvi/master_root/apps/knowledge_system/embedding_api.py` | REST API for embeddings |
| MCP Server | `/home/opsvi/master_root/libs/opsvi-mcp/opsvi_mcp/servers/knowledge/` | MCP knowledge tool |
| Backups | `/home/opsvi/master_root/knowledge-backups/` | Automated backups |
| Logs | `/home/opsvi/master_root/knowledge-logs/` | Service logs |

## Service URLs

- **Neo4j Browser**: http://localhost:7474 (neo4j/password)
- **Neo4j Bolt**: bolt://localhost:7687
- **Embedding API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Common Issues & Solutions

### Issue: Neo4j won't start
```bash
# Check logs
docker-compose -f docker-compose.knowledge.yml logs neo4j

# Reset Neo4j
docker-compose -f docker-compose.knowledge.yml down
docker volume rm master_root_neo4j_data
./start-knowledge-system.sh
```

### Issue: Embedding service fails
```bash
# Rebuild embedding service
docker-compose -f docker-compose.knowledge.yml build --no-cache embedding-service
docker-compose -f docker-compose.knowledge.yml up -d embedding-service
```

### Issue: MCP tool not connecting
```bash
# Test connectivity
./scripts/test-knowledge-connectivity.sh

# Check MCP configuration
cat .mcp.json | jq '.mcpServers.knowledge'
```

### Issue: Data corruption
```bash
# Restore from backup
./scripts/knowledge-restore.sh --latest

# Or restore specific date
./scripts/knowledge-restore.sh --date 2025-09-02
```

## Backup Strategy

Automatic backups run every 6 hours via cron:
```bash
# View backup schedule
crontab -l | grep knowledge

# Manual backup
./scripts/knowledge-backup.sh

# List backups
ls -la knowledge-backups/
```

## Health Monitoring

Check system health:
```bash
./scripts/knowledge-health.sh
```

This reports:
- Service status (up/down)
- Database node count
- Embedding service response time
- Disk usage
- Memory usage
- Last backup time

## Database Schema

### Core Node: Knowledge
```cypher
(:Knowledge {
  knowledge_id: String (unique),
  knowledge_type: String,
  content: String,
  summary: String,
  tags: [String],
  confidence_score: Float,
  created_at: DateTime,
  deprecated: Boolean,
  version: Integer
})
```

### Relationships
- `SIMILAR_TO` - Similarity between entries
- `DERIVED_FROM` - Evolution tracking
- `REQUIRES` - Dependencies
- `SUPERSEDES` - Version updates
- `RELATED_TO` - General relationships

## Maintenance Commands

```bash
# View all services
docker-compose -f docker-compose.knowledge.yml ps

# Restart all services
docker-compose -f docker-compose.knowledge.yml restart

# Update images
docker-compose -f docker-compose.knowledge.yml pull
docker-compose -f docker-compose.knowledge.yml up -d

# Clean up old data
docker system prune -a --volumes

# Export data
./scripts/knowledge-export.sh --format cypher

# Import data
./scripts/knowledge-import.sh knowledge-export.cypher
```

## Performance Tuning

Edit `docker-compose.knowledge.yml` to adjust:
- `NEO4J_server_memory_heap_max__size` - Increase for larger datasets
- `NEO4J_server_memory_pagecache_size` - Increase for better query performance

## Integration Testing

Run full test suite:
```bash
./scripts/test-knowledge-system.sh
```

This tests:
1. Neo4j connectivity
2. Schema integrity
3. Embedding generation
4. MCP tool operations
5. Backup/restore functionality

## Emergency Contacts

- Documentation: This file
- Scripts: `/home/opsvi/master_root/scripts/knowledge-*.sh`
- Logs: `docker-compose -f docker-compose.knowledge.yml logs`
- Status: `./scripts/knowledge-health.sh`
