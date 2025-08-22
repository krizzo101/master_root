#!/usr/bin/env python3
"""
MCP Server for Knowledge System

Complete knowledge management with:
- Nano agent transformation
- Auto-embedding
- Direct execution
- Knowledge superseding
- Simple input format
"""

import json
import logging
import sys
from typing import Optional

try:
    from fastmcp import FastMCP
except ImportError as e:
    print(f"Error: Failed to import FastMCP: {e}", file=sys.stderr)
    print("Please install fastmcp: pip install fastmcp", file=sys.stderr)
    sys.exit(1)

# Import knowledge tools
from apps.knowledge_system.mcp_knowledge_tools import get_enhanced_query as get_query
from apps.knowledge_system.mcp_knowledge_tools import get_enhanced_store as get_store

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("knowledge-system")


@mcp.tool()
async def knowledge_store(
    content: str, knowledge_type: Optional[str] = None, tags: Optional[str] = None
) -> str:
    """
    Store knowledge with automatic processing.

    Simply provide the content - everything else is handled automatically:
    - Nano agent transforms to structured format
    - Embeddings generated automatically
    - Superseded knowledge detected and marked
    - Direct storage to Neo4j

    Args:
        content: The knowledge to store (any format)
        knowledge_type: Optional hint (ERROR_SOLUTION, CODE_PATTERN, WORKFLOW, etc.)
        tags: Optional comma-separated tags

    Returns:
        JSON with knowledge_id and status

    Example:
        knowledge_store(
            content="To fix TypeError in Python, check variable types with isinstance()",
            knowledge_type="ERROR_SOLUTION",
            tags="python,error,type"
        )
    """
    try:
        store = get_store()

        # Parse tags if provided
        tag_list = None
        if tags:
            tag_list = [t.strip() for t in tags.split(",")]

        # Store with complete pipeline
        result = await store.store(
            raw_input=content,
            hint_type=knowledge_type,
            hint_tags=tag_list,
            direct_execute=True,
        )

        if result.get("stored"):
            # Successfully stored directly
            return json.dumps(
                {
                    "success": True,
                    "knowledge_id": result["knowledge_id"],
                    "stored": True,
                    "type": result.get("knowledge_type"),
                    "tags": result.get("tags", []),
                    "confidence": result.get("confidence"),
                    "embedding_generated": result.get("embedding_generated", False),
                    "superseded_count": result.get("superseded_count", 0),
                    "message": "Knowledge stored successfully",
                },
                indent=2,
            )
        else:
            # Return query for manual execution
            return json.dumps(
                {
                    "success": True,
                    "knowledge_id": result["knowledge_id"],
                    "stored": False,
                    "cypher_query": result.get("cypher_query"),
                    "params": result.get("params"),
                    "instruction": "Execute via mcp__db__write_neo4j_cypher",
                    "message": "Query generated - manual execution required",
                },
                indent=2,
            )

    except Exception as e:
        logger.error(f"Knowledge store failed: {e}")
        return json.dumps(
            {"success": False, "error": str(e), "message": "Failed to store knowledge"},
            indent=2,
        )


@mcp.tool()
async def knowledge_query(
    query_type: str = "recent",
    search_text: Optional[str] = None,
    knowledge_type: Optional[str] = None,
    limit: int = 5,
) -> str:
    """
    Query knowledge with direct results.

    Args:
        query_type: Type of query (search, recent, by_type, high_confidence)
        search_text: Text to search for (for 'search' query type)
        knowledge_type: Filter by type (for 'by_type' query)
        limit: Maximum results to return

    Returns:
        JSON with knowledge results

    Example:
        knowledge_query(
            query_type="search",
            search_text="python error",
            limit=10
        )
    """
    try:
        query = get_query()

        result = query.query(
            query_type=query_type,
            query_text=search_text,
            knowledge_type=knowledge_type,
            min_confidence=0.5,
            limit=limit,
            direct_execute=True,
        )

        if "results" in result:
            # Direct execution succeeded
            return json.dumps(
                {
                    "success": True,
                    "results": result["results"],
                    "count": result["count"],
                    "query_type": query_type,
                },
                indent=2,
            )
        else:
            # Return query for manual execution
            return json.dumps(
                {
                    "success": True,
                    "cypher_query": result["cypher_query"],
                    "params": result["params"],
                    "instruction": "Execute via mcp__db__read_neo4j_cypher",
                },
                indent=2,
            )

    except Exception as e:
        logger.error(f"Knowledge query failed: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
async def knowledge_update(
    knowledge_id: str, update_type: str, failure_reason: Optional[str] = None
) -> str:
    """
    Update knowledge based on usage.

    Args:
        knowledge_id: ID of knowledge to update
        update_type: 'success', 'failure', or 'deprecate'
        failure_reason: Reason if update_type is 'failure'

    Returns:
        JSON with update status
    """
    # Build the appropriate query
    if update_type == "success":
        query = """
        MATCH (k:Knowledge {knowledge_id: $knowledge_id})
        SET k.usage_count = k.usage_count + 1,
            k.success_rate = ((k.success_rate * k.usage_count) + 1.0) / (k.usage_count + 1),
            k.confidence_score = CASE
                WHEN k.success_rate > 0.8 AND k.usage_count > 5
                THEN CASE WHEN k.confidence_score + 0.05 > 1.0 THEN 1.0 ELSE k.confidence_score + 0.05 END
                ELSE k.confidence_score
            END,
            k.updated_at = datetime(),
            k.last_success = datetime()
        RETURN k.knowledge_id as id, k.confidence_score as new_confidence
        """
        params = {"knowledge_id": knowledge_id}

    elif update_type == "failure":
        query = """
        MATCH (k:Knowledge {knowledge_id: $knowledge_id})
        SET k.usage_count = k.usage_count + 1,
            k.success_rate = ((k.success_rate * k.usage_count) + 0.0) / (k.usage_count + 1),
            k.confidence_score = CASE
                WHEN k.success_rate < 0.3
                THEN CASE WHEN k.confidence_score - 0.1 < 0.1 THEN 0.1 ELSE k.confidence_score - 0.1 END
                ELSE k.confidence_score
            END,
            k.updated_at = datetime(),
            k.last_failure = datetime(),
            k.last_failure_reason = $failure_reason
        RETURN k.knowledge_id as id, k.confidence_score as new_confidence
        """
        params = {
            "knowledge_id": knowledge_id,
            "failure_reason": failure_reason or "Unknown",
        }

    elif update_type == "deprecate":
        query = """
        MATCH (k:Knowledge {knowledge_id: $knowledge_id})
        SET k.deprecated = true,
            k.deprecated_at = datetime(),
            k.confidence_score = 0.1
        RETURN k.knowledge_id as id
        """
        params = {"knowledge_id": knowledge_id}

    else:
        return json.dumps(
            {"success": False, "error": f"Invalid update_type: {update_type}"}, indent=2
        )

    # Execute directly via Neo4j driver
    try:
        import os

        from neo4j import GraphDatabase

        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "opsvi@2025")

        driver = GraphDatabase.driver(uri, auth=(user, password))

        with driver.session() as session:
            result = session.run(query, params)
            record = result.single()

            if record:
                return json.dumps(
                    {
                        "success": True,
                        "knowledge_id": record.get("id"),
                        "new_confidence": record.get("new_confidence"),
                        "status": f"Knowledge {knowledge_id} updated with {update_type}",
                    },
                    indent=2,
                )
            else:
                return json.dumps(
                    {"success": False, "error": f"Knowledge {knowledge_id} not found"},
                    indent=2,
                )

    except Exception as e:
        logger.error(f"Direct update execution failed: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)
    finally:
        if "driver" in locals():
            driver.close()


@mcp.tool()
async def knowledge_delete(
    knowledge_id: Optional[str] = None,
    delete_deprecated: bool = False,
    delete_low_confidence: bool = False,
    confidence_threshold: float = 0.3,
) -> str:
    """
    Delete knowledge entries.

    Args:
        knowledge_id: Specific ID to delete
        delete_deprecated: Delete all deprecated entries
        delete_low_confidence: Delete entries below threshold
        confidence_threshold: Threshold for low confidence deletion

    Returns:
        JSON with deletion status
    """
    if knowledge_id:
        # Delete specific entry
        query = """
        MATCH (k:Knowledge {knowledge_id: $knowledge_id})
        DELETE k
        RETURN count(k) as deleted_count
        """
        params = {"knowledge_id": knowledge_id}
        description = f"Delete knowledge {knowledge_id}"

    elif delete_deprecated:
        # Delete all deprecated
        query = """
        MATCH (k:Knowledge)
        WHERE k.deprecated = true
        DELETE k
        RETURN count(k) as deleted_count
        """
        params = {}
        description = "Delete all deprecated knowledge"

    elif delete_low_confidence:
        # Delete low confidence
        query = """
        MATCH (k:Knowledge)
        WHERE k.confidence_score < $threshold
        DELETE k
        RETURN count(k) as deleted_count
        """
        params = {"threshold": confidence_threshold}
        description = f"Delete knowledge below {confidence_threshold} confidence"

    else:
        return json.dumps(
            {"success": False, "error": "Must specify what to delete"}, indent=2
        )

    # Execute directly via Neo4j driver
    try:
        import os

        from neo4j import GraphDatabase

        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "opsvi@2025")

        driver = GraphDatabase.driver(uri, auth=(user, password))

        with driver.session() as session:
            result = session.run(query, params)
            record = result.single()

            deleted_count = record.get("deleted_count", 0) if record else 0

            return json.dumps(
                {
                    "success": True,
                    "deleted_count": deleted_count,
                    "status": description,
                },
                indent=2,
            )

    except Exception as e:
        logger.error(f"Direct delete execution failed: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)
    finally:
        if "driver" in locals():
            driver.close()


@mcp.tool()
async def knowledge_supersede(
    old_id: str, new_content: str, reason: Optional[str] = None
) -> str:
    """
    Supersede old knowledge with new version.

    This creates a new knowledge entry and marks the old one as deprecated.

    Args:
        old_id: ID of knowledge to supersede
        new_content: New knowledge content
        reason: Optional reason for superseding

    Returns:
        JSON with new knowledge_id and status
    """
    try:
        store = get_store()

        # Store new knowledge with supersede hint
        result = await store.store(
            raw_input=new_content,
            hint_type=None,  # Let nano agent determine
            hint_tags=None,
            direct_execute=True,
        )

        new_id = result.get("knowledge_id")

        # Mark old as superseded - execute directly
        deprecate_query = """
        MATCH (k:Knowledge {knowledge_id: $old_id})
        SET k.deprecated = true,
            k.deprecated_at = datetime(),
            k.superseded_by = $new_id,
            k.supersede_reason = $reason
        RETURN k.knowledge_id as id
        """

        # Execute deprecation directly
        import os

        from neo4j import GraphDatabase

        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "opsvi@2025")

        driver = GraphDatabase.driver(uri, auth=(user, password))

        try:
            with driver.session() as session:
                deprecate_result = session.run(
                    deprecate_query,
                    {
                        "old_id": old_id,
                        "new_id": new_id,
                        "reason": reason or "Updated with new information",
                    },
                )
                deprecated = deprecate_result.single() is not None
        except Exception as e:
            logger.warning(f"Could not deprecate old knowledge: {e}")
            deprecated = False
        finally:
            driver.close()

        return json.dumps(
            {
                "success": True,
                "new_knowledge_id": new_id,
                "old_knowledge_id": old_id,
                "stored": result.get("stored", False),
                "deprecated_old": deprecated,
                "status": f"New knowledge {new_id} created, old {old_id} {'deprecated' if deprecated else 'not found'}",
            },
            indent=2,
        )

    except Exception as e:
        logger.error(f"Knowledge supersede failed: {e}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)


def main():
    """Run the MCP server"""
    logger.info("Starting Knowledge System MCP Server")
    logger.info("Features: Nano agent, auto-embedding, direct execution, superseding")
    mcp.run()


if __name__ == "__main__":
    main()
