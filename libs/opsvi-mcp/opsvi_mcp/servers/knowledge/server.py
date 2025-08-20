#!/usr/bin/env python3
"""
MCP Server for Simplified Knowledge System Operations

Provides MCP tools that eliminate Neo4j Cypher complexity:
- knowledge_query: Search and retrieve knowledge
- knowledge_store: Store new knowledge (handles JSON serialization)
- knowledge_update: Update existing knowledge (success/failure tracking)
- knowledge_relate: Create relationships between knowledge entries

This prevents common Neo4j errors and makes knowledge operations simple.
"""

import json
import hashlib
import sys
from datetime import datetime, timezone
from typing import Optional, List

try:
    from fastmcp import FastMCP
except ImportError as e:
    print(f"Error: Failed to import FastMCP: {e}", file=sys.stderr)
    print("Please install fastmcp: pip install fastmcp", file=sys.stderr)
    sys.exit(1)

# Import simplified tools that generate Cypher (compatible with DB MCP)
from opsvi_mcp.servers.knowledge.mcp_knowledge_tools import (
    KnowledgeQueryTool,
    KnowledgeStoreTool,
    KnowledgeUpdateTool,
    KnowledgeRelationshipTool,
    EMBEDDINGS_AVAILABLE,
)

# Log embedding availability
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info(f"MCP Server: Embeddings available = {EMBEDDINGS_AVAILABLE}")

# Initialize FastMCP server
mcp = FastMCP("knowledge-system")


@mcp.tool()
async def knowledge_query(
    query_type: str,
    query_text: Optional[str] = None,
    knowledge_type: Optional[str] = None,
    min_confidence: float = 0.7,
    limit: int = 5
) -> str:
    """
    Query knowledge without writing Cypher
    
    Args:
        query_type: 'search', 'by_type', 'high_confidence', 'recent', 'related'
        query_text: Text to search for (for search and related queries)
        knowledge_type: Filter by type (ERROR_SOLUTION, CODE_PATTERN, etc.)
        min_confidence: Minimum confidence score (0-1)
        limit: Maximum number of results
        
    Returns:
        JSON with Cypher query and params for mcp__db__read_neo4j_cypher
    """
    try:
        result = KnowledgeQueryTool.execute(
            query_type=query_type,
            query_text=query_text,
            knowledge_type=knowledge_type,
            min_confidence=min_confidence,
            limit=limit
        )
        
        return json.dumps({
            "success": True,
            "cypher_query": result["query"],
            "params": result["params"],
            "instruction": "Execute via mcp__db__read_neo4j_cypher",
            "example": f"mcp__db__read_neo4j_cypher(query=result['cypher_query'], params=result['params'])"
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@mcp.tool()
async def knowledge_store(
    knowledge_type: str,
    content: str,
    context: Optional[dict] = None,
    tags: Optional[list] = None,
    confidence_score: float = 0.8,
    knowledge_id: Optional[str] = None
) -> str:
    """
    Store knowledge with automatic JSON serialization for complex objects
    
    Args:
        knowledge_type: ERROR_SOLUTION, CODE_PATTERN, WORKFLOW, USER_PREFERENCE, CONTEXT_PATTERN, TOOL_USAGE
        content: The knowledge content/description
        context: Any context dict (will be JSON serialized automatically)
        tags: Tags for categorization
        confidence_score: Initial confidence (0-1)
        knowledge_id: Optional ID (will generate if not provided)
        
    Returns:
        JSON with generated knowledge_id and Cypher query
    """
    try:
        # Call without auto_embed parameter (embedding happens automatically in the tool)
        result = KnowledgeStoreTool.execute(
            knowledge_type=knowledge_type,
            content=content,
            context=context,
            tags=tags,
            confidence_score=confidence_score,
            knowledge_id=knowledge_id
        )
        
        # Log embedding status
        if result.get("embedding_generated"):
            logger.info(f"Successfully generated embedding for {result['knowledge_id']}")
        else:
            logger.warning(f"No embedding generated for {result['knowledge_id']}")
        
        # Create a clean copy of params without embedding for response
        clean_params = dict(result["params"])
        embedding_info = None
        
        # Remove embedding from params if present and capture info
        if "embedding" in clean_params and clean_params["embedding"]:
            embedding_dim = len(clean_params["embedding"])
            embedding_info = {
                "generated": True,
                "dimensions": embedding_dim,
                "model": clean_params.get("embedding_model", "unknown")
            }
            # Remove embedding fields from clean params
            clean_params.pop("embedding", None)
            clean_params.pop("embedding_model", None)
        
        # Create a compact response that excludes the embedding vector to save context
        response = {
            "success": True,
            "knowledge_id": result["knowledge_id"],
            "cypher_query": result["query"],
            "params": clean_params,  # Clean params without embedding
            "embedding_generated": result.get("embedding_generated", False),
            "instruction": "Execute via mcp__db__write_neo4j_cypher",
            "note": "Complex objects in context have been JSON serialized automatically. Embeddings generated automatically when available."
        }
        
        # Add embedding info if it was generated
        if embedding_info:
            response["embedding_info"] = embedding_info
            
        return json.dumps(response, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "hint": "Check that knowledge_type is valid and content is provided"
        }, indent=2)


@mcp.tool()
async def knowledge_update(
    knowledge_id: str,
    update_type: str,
    failure_reason: Optional[str] = None
) -> str:
    """
    Update knowledge based on usage outcomes (success/failure)
    
    Args:
        knowledge_id: ID of knowledge to update
        update_type: 'success', 'failure', or 'deprecate'
        failure_reason: Reason for failure (if update_type is failure)
        
    Returns:
        JSON with Cypher query for updating knowledge
    """
    try:
        result = KnowledgeUpdateTool.execute(
            knowledge_id=knowledge_id,
            update_type=update_type,
            failure_reason=failure_reason
        )
        
        return json.dumps({
            "success": True,
            "cypher_query": result["query"],
            "params": result["params"],
            "instruction": "Execute via mcp__db__write_neo4j_cypher"
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@mcp.tool()
async def knowledge_relate(
    source_id: str,
    target_id: str,
    relationship_type: str = "RELATED_TO",
    properties: Optional[dict] = None
) -> str:
    """
    Create relationships between knowledge entries
    
    Args:
        source_id: Source knowledge ID
        target_id: Target knowledge ID
        relationship_type: SIMILAR_TO, DERIVED_FROM, REQUIRES, CONTRADICTS, ENHANCES
        properties: Optional relationship properties
        
    Returns:
        JSON with Cypher query for creating relationship
    """
    try:
        result = KnowledgeRelationshipTool.execute(
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
            properties=properties
        )
        
        return json.dumps({
            "success": True,
            "cypher_query": result["query"],
            "params": result["params"],
            "instruction": "Execute via mcp__db__write_neo4j_cypher"
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@mcp.tool()
async def knowledge_read(
    knowledge_ids: Optional[List[str]] = None,
    limit: int = 10
) -> str:
    """
    Read specific knowledge entries WITHOUT embedding vectors
    
    Args:
        knowledge_ids: Optional list of specific IDs to read
        limit: Maximum number to return if no IDs specified
        
    Returns:
        Clean JSON with knowledge content (no embeddings)
    """
    try:
        if knowledge_ids:
            # Read specific entries by ID
            query = """
            MATCH (k:Knowledge)
            WHERE k.knowledge_id IN $ids
            RETURN k.content as content, k.knowledge_type as type,
                   k.confidence_score as confidence, k.success_rate as success_rate,
                   k.knowledge_id as id
            ORDER BY k.confidence_score DESC
            """
            params = {"ids": knowledge_ids}
        else:
            # Read most recent entries
            query = """
            MATCH (k:Knowledge)
            RETURN k.content as content, k.knowledge_type as type,
                   k.confidence_score as confidence, k.success_rate as success_rate
            ORDER BY k.updated_at DESC
            LIMIT $limit
            """
            params = {"limit": limit}
        
        return json.dumps({
            "success": True,
            "cypher_query": query,
            "params": params,
            "instruction": "Execute via mcp__db__read_neo4j_cypher",
            "note": "Returns clean knowledge without embedding vectors"
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


def main():
    """Run the MCP server"""
    # FastMCP handles the server lifecycle
    mcp.run()


if __name__ == "__main__":
    main()