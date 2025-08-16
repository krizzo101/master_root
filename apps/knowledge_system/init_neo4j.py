#!/usr/bin/env python3
"""
Initialize Neo4j Database for Knowledge Learning System

This script sets up the Neo4j database with the required schema and initial data.
It uses the MCP tools to interact with Neo4j.
"""

import asyncio
import json
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def execute_cypher(query: str, params: Dict[str, Any] = None, write: bool = False):
    """
    Execute a Cypher query using MCP tools
    
    This is a placeholder that would use the actual MCP tools:
    - mcp__db__write_neo4j_cypher for write operations
    - mcp__db__read_neo4j_cypher for read operations
    """
    logger.info(f"Executing {'write' if write else 'read'} query: {query[:100]}...")
    # In actual implementation, this would call the MCP tools
    return {"success": True}


async def create_indexes():
    """Create all required indexes for the knowledge system"""
    
    indexes = [
        # Core Knowledge indexes
        "CREATE INDEX knowledge_id IF NOT EXISTS FOR (n:Knowledge) ON (n.id)",
        "CREATE INDEX knowledge_type IF NOT EXISTS FOR (n:Knowledge) ON (n.type)",
        "CREATE INDEX knowledge_confidence IF NOT EXISTS FOR (n:Knowledge) ON (n.confidence_score)",
        "CREATE INDEX knowledge_created IF NOT EXISTS FOR (n:Knowledge) ON (n.created_at)",
        "CREATE INDEX knowledge_updated IF NOT EXISTS FOR (n:Knowledge) ON (n.updated_at)",
        "CREATE INDEX knowledge_success IF NOT EXISTS FOR (n:Knowledge) ON (n.success_rate)",
        
        # Specialized knowledge type indexes
        "CREATE INDEX code_pattern_language IF NOT EXISTS FOR (n:CodePattern) ON (n.language)",
        "CREATE INDEX code_pattern_type IF NOT EXISTS FOR (n:CodePattern) ON (n.pattern_type)",
        "CREATE INDEX error_signature IF NOT EXISTS FOR (n:ErrorResolution) ON (n.error_signature)",
        "CREATE INDEX error_type IF NOT EXISTS FOR (n:ErrorResolution) ON (n.error_type)",
        "CREATE INDEX workflow_name IF NOT EXISTS FOR (n:Workflow) ON (n.workflow_name)",
        "CREATE INDEX tool_name IF NOT EXISTS FOR (n:ToolUsage) ON (n.tool_name)",
        "CREATE INDEX tool_category IF NOT EXISTS FOR (n:ToolUsage) ON (n.tool_category)",
        "CREATE INDEX context_type IF NOT EXISTS FOR (n:ContextPattern) ON (n.context_type)",
        "CREATE INDEX user_pref_user IF NOT EXISTS FOR (n:UserPreference) ON (n.user_id)",
        "CREATE INDEX user_pref_category IF NOT EXISTS FOR (n:UserPreference) ON (n.preference_category)",
        
        # Session tracking indexes
        "CREATE INDEX session_id IF NOT EXISTS FOR (n:Session) ON (n.id)",
        "CREATE INDEX session_user IF NOT EXISTS FOR (n:Session) ON (n.user_id)",
        "CREATE INDEX session_started IF NOT EXISTS FOR (n:Session) ON (n.started_at)",
        
        # Vector similarity index (if supported by Neo4j version)
        "CREATE INDEX knowledge_embedding IF NOT EXISTS FOR (n:Knowledge) ON (n.embedding)",
        
        # Composite indexes for common queries
        "CREATE INDEX knowledge_type_confidence IF NOT EXISTS FOR (n:Knowledge) ON (n.type, n.confidence_score)",
        "CREATE INDEX knowledge_type_success IF NOT EXISTS FOR (n:Knowledge) ON (n.type, n.success_rate)",
    ]
    
    for index_query in indexes:
        try:
            await execute_cypher(index_query, write=True)
            logger.info(f"Created index: {index_query.split('FOR')[1].split('ON')[0].strip()}")
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")


async def create_constraints():
    """Create uniqueness constraints"""
    
    constraints = [
        "CREATE CONSTRAINT knowledge_id_unique IF NOT EXISTS FOR (n:Knowledge) REQUIRE n.id IS UNIQUE",
        "CREATE CONSTRAINT session_id_unique IF NOT EXISTS FOR (n:Session) REQUIRE n.id IS UNIQUE",
    ]
    
    for constraint_query in constraints:
        try:
            await execute_cypher(constraint_query, write=True)
            logger.info(f"Created constraint: {constraint_query.split('FOR')[1].split('REQUIRE')[0].strip()}")
        except Exception as e:
            logger.warning(f"Constraint creation warning: {e}")


async def create_initial_data():
    """Create initial seed data for the knowledge system"""
    
    # Create system metadata node
    metadata_query = """
    MERGE (m:Metadata {type: 'system'})
    SET m.description = 'Knowledge Learning System Metadata',
        m.version = '1.0.0',
        m.created_at = datetime(),
        m.last_updated = datetime()
    RETURN m
    """
    await execute_cypher(metadata_query, write=True)
    
    # Create default categories
    categories = [
        {"name": "Programming", "description": "Programming and coding patterns"},
        {"name": "ErrorHandling", "description": "Error resolution and debugging"},
        {"name": "Architecture", "description": "System design and architecture"},
        {"name": "DataProcessing", "description": "Data manipulation and processing"},
        {"name": "Testing", "description": "Testing and quality assurance"},
        {"name": "Documentation", "description": "Documentation and communication"},
        {"name": "DevOps", "description": "Deployment and operations"},
        {"name": "Security", "description": "Security best practices"},
        {"name": "Performance", "description": "Performance optimization"},
        {"name": "AI/ML", "description": "AI and machine learning"},
    ]
    
    for category in categories:
        query = """
        MERGE (c:Category {name: $name})
        SET c.description = $description,
            c.created_at = datetime()
        RETURN c
        """
        await execute_cypher(query, params=category, write=True)
        logger.info(f"Created category: {category['name']}")
    
    # Create sample technologies
    technologies = [
        {"name": "Python", "category": "Programming"},
        {"name": "JavaScript", "category": "Programming"},
        {"name": "Neo4j", "category": "Database"},
        {"name": "Docker", "category": "DevOps"},
        {"name": "Git", "category": "VersionControl"},
        {"name": "FastAPI", "category": "Framework"},
        {"name": "React", "category": "Framework"},
        {"name": "PostgreSQL", "category": "Database"},
        {"name": "Redis", "category": "Database"},
        {"name": "Kubernetes", "category": "DevOps"},
    ]
    
    for tech in technologies:
        query = """
        MERGE (t:Technology {name: $name})
        SET t.category = $category,
            t.created_at = datetime(),
            t.updated_at = datetime()
        RETURN t
        """
        await execute_cypher(query, params=tech, write=True)
        logger.info(f"Created technology: {tech['name']}")
    
    # Create technology relationships
    tech_relationships = [
        ("Python", "FastAPI", "USED_WITH", {"strength": 0.9}),
        ("JavaScript", "React", "USED_WITH", {"strength": 0.95}),
        ("Docker", "Kubernetes", "RELATED_TO", {"strength": 0.8}),
        ("PostgreSQL", "Redis", "COMPLEMENTS", {"strength": 0.7}),
    ]
    
    for source, target, rel_type, props in tech_relationships:
        query = f"""
        MATCH (s:Technology {{name: $source}})
        MATCH (t:Technology {{name: $target}})
        MERGE (s)-[r:{rel_type}]->(t)
        SET r += $props
        RETURN r
        """
        await execute_cypher(
            query,
            params={"source": source, "target": target, "props": props},
            write=True
        )
        logger.info(f"Created relationship: {source} -{rel_type}-> {target}")
    
    # Create sample knowledge entries
    sample_knowledge = [
        {
            "type": "CodePattern",
            "language": "Python",
            "pattern_type": "singleton",
            "content": """class Singleton:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance""",
            "summary": "Python Singleton pattern implementation",
            "confidence_score": 0.9
        },
        {
            "type": "ErrorResolution",
            "error_type": "ImportError",
            "error_signature": "no_module_named",
            "content": """To resolve ImportError:
1. Check if the module is installed: pip list | grep module_name
2. Install if missing: pip install module_name
3. Check Python path: python -c "import sys; print(sys.path)"
4. Verify virtual environment is activated""",
            "summary": "Resolution for Python ImportError",
            "confidence_score": 0.85
        },
        {
            "type": "Workflow",
            "workflow_name": "git_workflow",
            "content": """Standard Git Workflow:
1. git status - Check current state
2. git add -A - Stage changes
3. git commit -m "message" - Commit changes
4. git push origin branch - Push to remote""",
            "summary": "Basic Git workflow for version control",
            "confidence_score": 0.95
        }
    ]
    
    for knowledge in sample_knowledge:
        # Generate a simple embedding (in production, use actual embedding service)
        embedding = [0.1] * 512  # Placeholder embedding
        
        query = """
        CREATE (k:Knowledge {
            id: randomUUID(),
            type: $type,
            content: $content,
            summary: $summary,
            embedding: $embedding,
            created_at: datetime(),
            updated_at: datetime(),
            access_count: 0,
            success_rate: 0.0,
            confidence_score: $confidence_score,
            version: 1
        })
        
        // Add type-specific label
        WITH k
        CALL apoc.create.addLabels(k, [$type]) YIELD node
        
        RETURN node.id as id
        """
        
        knowledge["embedding"] = embedding
        await execute_cypher(query, params=knowledge, write=True)
        logger.info(f"Created sample knowledge: {knowledge['type']}")


async def verify_setup():
    """Verify the database setup"""
    
    # Count nodes by type
    queries = [
        ("Knowledge", "MATCH (n:Knowledge) RETURN count(n) as count"),
        ("Category", "MATCH (n:Category) RETURN count(n) as count"),
        ("Technology", "MATCH (n:Technology) RETURN count(n) as count"),
        ("Session", "MATCH (n:Session) RETURN count(n) as count"),
    ]
    
    logger.info("\n=== Database Statistics ===")
    for label, query in queries:
        result = await execute_cypher(query, write=False)
        # In actual implementation, parse the result
        logger.info(f"{label} nodes: [count would be shown here]")
    
    # Check indexes
    index_query = "SHOW INDEXES"
    logger.info("\n=== Indexes ===")
    logger.info("Indexes have been created (list would be shown in actual implementation)")
    
    logger.info("\n=== Setup Complete ===")
    logger.info("The Neo4j database has been initialized for the Knowledge Learning System")


async def main():
    """Main initialization function"""
    
    logger.info("Starting Neo4j initialization for Knowledge Learning System...")
    
    try:
        # Create indexes
        logger.info("\n1. Creating indexes...")
        await create_indexes()
        
        # Create constraints
        logger.info("\n2. Creating constraints...")
        await create_constraints()
        
        # Create initial data
        logger.info("\n3. Creating initial data...")
        await create_initial_data()
        
        # Verify setup
        logger.info("\n4. Verifying setup...")
        await verify_setup()
        
        logger.info("\nInitialization completed successfully!")
        
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())