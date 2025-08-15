#!/usr/bin/env python3
"""
Simplified MCP Tools for Knowledge System
Eliminates Neo4j Cypher complexity for agents

Provides 3 simple tools:
- knowledge_query: Search and retrieve knowledge
- knowledge_store: Store new knowledge (handles JSON serialization)
- knowledge_update: Update existing knowledge (success/failure tracking)

This prevents common Neo4j errors like:
- Property values can only be of primitive types
- Complex object serialization issues
- Incorrect Cypher syntax
"""

import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

# Import embedding service for auto-embedding with multiple fallbacks
import sys
import os

# Add current directory to path for MCP server context
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    # Try direct import
    from embedding_service import get_embedding_service
    EMBEDDINGS_AVAILABLE = True
except ImportError as e1:
    try:
        # Try absolute import
        from apps.knowledge_system.embedding_service import get_embedding_service
        EMBEDDINGS_AVAILABLE = True
    except ImportError as e2:
        EMBEDDINGS_AVAILABLE = False
        print(f"Warning: Could not import embedding_service: {e1}, {e2}")


class KnowledgeQueryTool:
    """
    Simplified knowledge retrieval - no Cypher needed
    """
    
    @staticmethod
    def execute(
        query_type: str,
        query_text: str = None,
        knowledge_type: str = None,
        min_confidence: float = 0.7,
        limit: int = 5,
        context_filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Query knowledge without writing Cypher
        
        Args:
            query_type: 'search', 'by_type', 'high_confidence', 'recent', 'related'
            query_text: Text to search for
            knowledge_type: Filter by type (ERROR_SOLUTION, CODE_PATTERN, etc.)
            min_confidence: Minimum confidence score
            limit: Max results
            context_filters: Additional context to match
            
        Returns:
            Cypher query and params ready for mcp__db__read_neo4j_cypher
        """
        
        if query_type == "search":
            # Text search across content and tags
            query = """
            MATCH (k:Knowledge)
            WHERE toLower(k.content) CONTAINS toLower($query_text)
            OR any(tag IN k.tags WHERE toLower(tag) CONTAINS toLower($query_text))
            """
            params = {"query_text": query_text or ""}
            
            if knowledge_type:
                query += " AND k.knowledge_type = $knowledge_type"
                params["knowledge_type"] = knowledge_type
                
            query += """
            AND k.confidence_score >= $min_confidence
            RETURN k.content as content, k.knowledge_type as type, 
                   k.confidence_score as confidence, k.success_rate as success_rate
            ORDER BY k.confidence_score DESC, k.usage_count DESC
            LIMIT $limit
            """
            params["min_confidence"] = min_confidence
            params["limit"] = limit
            
        elif query_type == "by_type":
            # Get all knowledge of a specific type
            query = """
            MATCH (k:Knowledge)
            WHERE k.knowledge_type = $knowledge_type
            AND k.confidence_score >= $min_confidence
            RETURN k.content as content, k.knowledge_type as type,
                   k.confidence_score as confidence, k.success_rate as success_rate
            ORDER BY k.confidence_score DESC, k.success_rate DESC
            LIMIT $limit
            """
            params = {
                "knowledge_type": knowledge_type or "CODE_PATTERN",
                "min_confidence": min_confidence,
                "limit": limit
            }
            
        elif query_type == "high_confidence":
            # Get highest confidence knowledge
            query = """
            MATCH (k:Knowledge)
            WHERE k.confidence_score >= 0.85
            RETURN k.content as content, k.knowledge_type as type,
                   k.confidence_score as confidence, k.success_rate as success_rate
            ORDER BY k.confidence_score DESC, k.usage_count DESC
            LIMIT $limit
            """
            params = {"limit": limit}
            
        elif query_type == "recent":
            # Get recently updated knowledge
            query = """
            MATCH (k:Knowledge)
            WHERE k.confidence_score >= $min_confidence
            RETURN k.content as content, k.knowledge_type as type,
                   k.confidence_score as confidence, k.success_rate as success_rate
            ORDER BY k.updated_at DESC
            LIMIT $limit
            """
            params = {
                "min_confidence": min_confidence,
                "limit": limit
            }
            
        elif query_type == "related":
            # Get knowledge related to a specific ID
            query = """
            MATCH (k1:Knowledge {knowledge_id: $knowledge_id})-[r]-(k2:Knowledge)
            RETURN k2.content as content, k2.knowledge_type as type,
                   k2.confidence_score as confidence, k2.success_rate as success_rate,
                   type(r) as relationship
            LIMIT $limit
            """
            params = {
                "knowledge_id": query_text,  # ID passed as query_text
                "limit": limit
            }
            
        else:
            # Default: return all high-confidence knowledge
            query = """
            MATCH (k:Knowledge)
            WHERE k.confidence_score >= 0.7
            RETURN k
            ORDER BY k.confidence_score DESC
            LIMIT 10
            """
            params = {}
        
        return {
            "query": query,
            "params": params,
            "instruction": "Execute via mcp__db__read_neo4j_cypher"
        }


class KnowledgeStoreTool:
    """
    Simplified knowledge storage - handles all serialization
    """
    
    @staticmethod
    def execute(
        knowledge_type: str,
        content: str,
        context: Dict[str, Any] = None,
        tags: List[str] = None,
        confidence_score: float = 0.8,
        knowledge_id: str = None,
        auto_embed: bool = True
    ) -> Dict[str, Any]:
        """
        Store knowledge without worrying about Neo4j type restrictions
        
        Args:
            knowledge_type: ERROR_SOLUTION, CODE_PATTERN, WORKFLOW, etc.
            content: The knowledge content
            context: Any context dict (will be JSON serialized)
            tags: List of tags
            confidence_score: Initial confidence (0-1)
            knowledge_id: Optional ID (will generate if not provided)
            
        Returns:
            Cypher query and params ready for mcp__db__write_neo4j_cypher
        """
        
        # Generate ID if not provided
        if not knowledge_id:
            id_source = f"{knowledge_type}:{content[:100]}:{datetime.now(timezone.utc).isoformat()}"
            knowledge_id = hashlib.sha256(id_source.encode()).hexdigest()[:16]
        
        # JSON serialize complex objects
        context_json = json.dumps(context) if context else "{}"
        
        # Ensure tags is a list
        if tags is None:
            tags = []
        elif isinstance(tags, str):
            tags = [tags]
        
        # Generate embedding if requested and available
        embedding = None
        embedding_model = None
        if auto_embed and EMBEDDINGS_AVAILABLE:
            try:
                service = get_embedding_service()
                
                # Prepare knowledge text for embedding
                knowledge_dict = {
                    "knowledge_type": knowledge_type,
                    "content": content,
                    "context": context,
                    "tags": tags
                }
                prepared_text = service.prepare_knowledge_text(knowledge_dict)
                
                # Generate embedding
                embedding = service.generate_embedding(prepared_text)
                embedding_model = service.model_name
                
            except Exception as e:
                # Silently fail - embedding is optional
                embedding = None
        
        # Build query based on whether we have an embedding
        if embedding:
            query = """
        MERGE (k:Knowledge {knowledge_id: $knowledge_id})
        ON CREATE SET
            k.knowledge_type = $knowledge_type,
            k.content = $content,
            k.context = $context,
            k.tags = $tags,
            k.confidence_score = $confidence_score,
            k.usage_count = 0,
            k.success_rate = 0.0,
            k.created_at = datetime(),
            k.updated_at = datetime(),
            k.embedding = $embedding,
            k.embedding_model = $embedding_model,
            k.embedding_generated_at = datetime()
        ON MATCH SET
            k.updated_at = datetime(),
            k.content = $content,
            k.context = $context,
            k.tags = $tags,
            k.embedding = $embedding,
            k.embedding_model = $embedding_model,
            k.embedding_generated_at = datetime()
        RETURN k.knowledge_id as id
        """
        else:
            query = """
        MERGE (k:Knowledge {knowledge_id: $knowledge_id})
        ON CREATE SET
            k.knowledge_type = $knowledge_type,
            k.content = $content,
            k.context = $context,
            k.tags = $tags,
            k.confidence_score = $confidence_score,
            k.usage_count = 0,
            k.success_rate = 0.0,
            k.created_at = datetime(),
            k.updated_at = datetime()
        ON MATCH SET
            k.updated_at = datetime(),
            k.content = $content,
            k.context = $context,
            k.tags = $tags
        RETURN k.knowledge_id as id
        """
        
        # Build params based on whether we have an embedding
        if embedding:
            params = {
                "knowledge_id": knowledge_id,
                "knowledge_type": knowledge_type,
                "content": content,
                "context": context_json,  # JSON string, not object
                "tags": tags,
                "confidence_score": confidence_score,
                "embedding": embedding,
                "embedding_model": embedding_model
            }
        else:
            params = {
                "knowledge_id": knowledge_id,
                "knowledge_type": knowledge_type,
                "content": content,
                "context": context_json,  # JSON string, not object
                "tags": tags,
                "confidence_score": confidence_score
            }
        
        return {
            "query": query,
            "params": params,
            "knowledge_id": knowledge_id,
            "embedding_generated": embedding is not None,
            "instruction": "Execute via mcp__db__write_neo4j_cypher"
        }


class KnowledgeUpdateTool:
    """
    Simplified knowledge updates - track success/failure
    """
    
    @staticmethod
    def execute(
        knowledge_id: str,
        update_type: str,
        success_metrics: Dict[str, float] = None,
        failure_reason: str = None
    ) -> Dict[str, Any]:
        """
        Update knowledge based on usage outcomes
        
        Args:
            knowledge_id: ID of knowledge to update
            update_type: 'success', 'failure', 'deprecate'
            success_metrics: Metrics for successful application
            failure_reason: Reason for failure
            
        Returns:
            Cypher query and params ready for mcp__db__write_neo4j_cypher
        """
        
        if update_type == "success":
            # Update for successful application
            query = """
            MATCH (k:Knowledge {knowledge_id: $knowledge_id})
            SET k.usage_count = k.usage_count + 1,
                k.success_rate = ((k.success_rate * k.usage_count) + 1.0) / (k.usage_count + 1),
                k.confidence_score = CASE 
                    WHEN k.success_rate > 0.8 AND k.usage_count > 5 
                    THEN CASE 
                        WHEN k.confidence_score + 0.05 > 1.0 THEN 1.0
                        ELSE k.confidence_score + 0.05
                    END
                    ELSE k.confidence_score
                END,
                k.updated_at = datetime(),
                k.last_success = datetime()
            RETURN k.knowledge_id as id, k.confidence_score as new_confidence
            """
            params = {"knowledge_id": knowledge_id}
            
        elif update_type == "failure":
            # Update for failed application
            query = """
            MATCH (k:Knowledge {knowledge_id: $knowledge_id})
            SET k.usage_count = k.usage_count + 1,
                k.success_rate = ((k.success_rate * k.usage_count) + 0.0) / (k.usage_count + 1),
                k.confidence_score = CASE 
                    WHEN k.success_rate < 0.3 
                    THEN max(0.1, k.confidence_score - 0.1)
                    ELSE k.confidence_score
                END,
                k.updated_at = datetime(),
                k.last_failure = datetime(),
                k.last_failure_reason = $failure_reason
            RETURN k.knowledge_id as id, k.confidence_score as new_confidence
            """
            params = {
                "knowledge_id": knowledge_id,
                "failure_reason": failure_reason or "Unknown"
            }
            
        elif update_type == "deprecate":
            # Mark knowledge as deprecated
            query = """
            MATCH (k:Knowledge {knowledge_id: $knowledge_id})
            SET k.deprecated = true,
                k.deprecated_at = datetime(),
                k.confidence_score = 0.1
            RETURN k.knowledge_id as id
            """
            params = {"knowledge_id": knowledge_id}
            
        else:
            # Default: just update timestamp
            query = """
            MATCH (k:Knowledge {knowledge_id: $knowledge_id})
            SET k.updated_at = datetime()
            RETURN k.knowledge_id as id
            """
            params = {"knowledge_id": knowledge_id}
        
        return {
            "query": query,
            "params": params,
            "instruction": "Execute via mcp__db__write_neo4j_cypher"
        }


class KnowledgeRelationshipTool:
    """
    Create relationships between knowledge entries
    """
    
    @staticmethod
    def execute(
        source_id: str,
        target_id: str,
        relationship_type: str = "RELATED_TO",
        properties: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create relationship between knowledge entries
        
        Args:
            source_id: Source knowledge ID
            target_id: Target knowledge ID
            relationship_type: SIMILAR_TO, DERIVED_FROM, REQUIRES, CONTRADICTS, ENHANCES
            properties: Optional relationship properties
            
        Returns:
            Cypher query and params
        """
        
        # Validate relationship type
        valid_types = ["RELATED_TO", "SIMILAR_TO", "DERIVED_FROM", "REQUIRES", "CONTRADICTS", "ENHANCES", "VALIDATES", "REPLACES", "EXTENDS"]
        if relationship_type not in valid_types:
            relationship_type = "RELATED_TO"
        
        # Build query based on whether properties exist
        if properties:
            props_json = json.dumps(properties)
            query = f"""
            MATCH (source:Knowledge {{knowledge_id: $source_id}})
            MATCH (target:Knowledge {{knowledge_id: $target_id}})
            CREATE (source)-[r:{relationship_type} {{
                created_at: datetime(),
                properties: $properties
            }}]->(target)
            RETURN type(r) as relationship
            """
            params = {
                "source_id": source_id,
                "target_id": target_id,
                "properties": props_json
            }
        else:
            query = f"""
            MATCH (source:Knowledge {{knowledge_id: $source_id}})
            MATCH (target:Knowledge {{knowledge_id: $target_id}})
            CREATE (source)-[r:{relationship_type} {{
                created_at: datetime()
            }}]->(target)
            RETURN type(r) as relationship
            """
            params = {
                "source_id": source_id,
                "target_id": target_id
            }
        
        return {
            "query": query,
            "params": params,
            "instruction": "Execute via mcp__db__write_neo4j_cypher"
        }


# Convenience functions for agents
def query_knowledge(query_type: str, **kwargs) -> Dict[str, Any]:
    """Simple wrapper for knowledge queries"""
    return KnowledgeQueryTool.execute(query_type, **kwargs)


def store_knowledge(knowledge_type: str, content: str, **kwargs) -> Dict[str, Any]:
    """Simple wrapper for storing knowledge"""
    return KnowledgeStoreTool.execute(knowledge_type, content, **kwargs)


def update_knowledge(knowledge_id: str, update_type: str, **kwargs) -> Dict[str, Any]:
    """Simple wrapper for updating knowledge"""
    return KnowledgeUpdateTool.execute(knowledge_id, update_type, **kwargs)


def relate_knowledge(source_id: str, target_id: str, relationship_type: str = "RELATED_TO", **kwargs) -> Dict[str, Any]:
    """Simple wrapper for creating relationships"""
    return KnowledgeRelationshipTool.execute(source_id, target_id, relationship_type, **kwargs)


# Usage examples for agents
USAGE_EXAMPLES = """
# SIMPLIFIED KNOWLEDGE OPERATIONS - No Cypher Required!

## 1. Query Knowledge (no complex Cypher)
```python
from apps.knowledge_system.mcp_knowledge_tools import query_knowledge

# Search for error solutions
result = query_knowledge("search", query_text="ImportError", knowledge_type="ERROR_SOLUTION")
data = mcp__db__read_neo4j_cypher(query=result['query'], params=result['params'])

# Get high confidence knowledge
result = query_knowledge("high_confidence", limit=10)
data = mcp__db__read_neo4j_cypher(query=result['query'], params=result['params'])

# Get recent updates
result = query_knowledge("recent", limit=5)
data = mcp__db__read_neo4j_cypher(query=result['query'], params=result['params'])
```

## 2. Store Knowledge (handles JSON serialization automatically)
```python
from apps.knowledge_system.mcp_knowledge_tools import store_knowledge

# Store with complex context - NO JSON.dumps needed!
result = store_knowledge(
    knowledge_type="ERROR_SOLUTION",
    content="Fix ImportError by installing package",
    context={
        "error_type": "ImportError",
        "nested": {
            "arrays": ["work", "fine"],
            "objects": {"no": "problem"}
        }
    },
    tags=["python", "import", "error"],
    confidence_score=0.9
)
# Execute the query
mcp__db__write_neo4j_cypher(query=result['query'], params=result['params'])
```

## 3. Update Knowledge (track success/failure)
```python
from apps.knowledge_system.mcp_knowledge_tools import update_knowledge

# After successful application
result = update_knowledge("knowledge_id_here", "success")
mcp__db__write_neo4j_cypher(query=result['query'], params=result['params'])

# After failure
result = update_knowledge("knowledge_id_here", "failure", failure_reason="Didn't work in Python 2")
mcp__db__write_neo4j_cypher(query=result['query'], params=result['params'])
```

## 4. Create Relationships
```python
from apps.knowledge_system.mcp_knowledge_tools import relate_knowledge

result = relate_knowledge("source_id", "target_id", "DERIVED_FROM")
mcp__db__write_neo4j_cypher(query=result['query'], params=result['params'])
```

## Why Use These Tools?
- ✅ No Cypher syntax errors
- ✅ Automatic JSON serialization for nested objects
- ✅ Consistent parameter handling
- ✅ Built-in validation
- ✅ Clear error messages
"""

if __name__ == "__main__":
    # Test the tools
    print("Knowledge System Simplified Tools")
    print("=" * 60)
    
    # Test query generation
    query_result = query_knowledge("search", query_text="error", knowledge_type="ERROR_SOLUTION")
    print("Query Tool Result:")
    print(json.dumps(query_result, indent=2))
    print()
    
    # Test store generation with complex context
    store_result = store_knowledge(
        knowledge_type="CODE_PATTERN",
        content="Test pattern",
        context={
            "language": "Python",
            "nested": {
                "arrays": ["test1", "test2"],
                "objects": {"key": "value"}
            }
        },
        tags=["test", "example"]
    )
    print("Store Tool Result:")
    print(f"Generated ID: {store_result['knowledge_id']}")
    print(f"Context serialized: {store_result['params']['context']}")
    print()
    
    print(USAGE_EXAMPLES)