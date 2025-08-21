#!/usr/bin/env python3
"""
Knowledge Tool Helper Functions
================================
Provides workarounds for current MCP parameter limitations in knowledge tools.

Author: AI Platform Team
Date: 2025-08-21
Version: 1.0.0

This module provides safe wrapper functions that work around the current
limitations of the MCP knowledge tool interface, where only knowledge_type
and content parameters are properly exposed.
"""

import json
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KnowledgeType(Enum):
    """Valid knowledge types for storage."""

    ERROR_SOLUTION = "ERROR_SOLUTION"
    CODE_PATTERN = "CODE_PATTERN"
    WORKFLOW = "WORKFLOW"
    USER_PREFERENCE = "USER_PREFERENCE"
    CONTEXT_PATTERN = "CONTEXT_PATTERN"
    TOOL_USAGE = "TOOL_USAGE"
    TEST_PATTERN = "TEST_PATTERN"
    RESEARCH_FINDINGS = "RESEARCH_FINDINGS"
    MODEL_CAPABILITIES = "MODEL_CAPABILITIES"
    API_PATTERN = "API_PATTERN"
    SECURITY_PATTERN = "SECURITY_PATTERN"
    PERFORMANCE_PATTERN = "PERFORMANCE_PATTERN"


def safe_knowledge_store(
    knowledge_type: Union[str, KnowledgeType],
    content: str,
    tags: Optional[List[str]] = None,
    context: Optional[Dict[str, Any]] = None,
    confidence: float = 0.8,
    knowledge_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Safely store knowledge with automatic metadata embedding.
    Works around current MCP parameter limitations.

    Args:
        knowledge_type: Type of knowledge (use KnowledgeType enum or string)
        content: The main knowledge content to store
        tags: Optional list of tags for categorization
        context: Optional context dictionary with metadata
        confidence: Confidence score between 0.0 and 1.0 (default: 0.8)
        knowledge_id: Optional specific ID for the knowledge entry

    Returns:
        Dict containing storage result with knowledge_id and status

    Example:
        >>> result = safe_knowledge_store(
        ...     knowledge_type=KnowledgeType.ERROR_SOLUTION,
        ...     content="Fix for validation error: use List[str] not str",
        ...     tags=["validation", "mcp", "fix"],
        ...     context={"error_type": "ValidationError", "tool": "knowledge_store"},
        ...     confidence=0.95
        ... )
        >>> print(result["knowledge_id"])
    """
    # Validate knowledge_type
    if isinstance(knowledge_type, KnowledgeType):
        knowledge_type = knowledge_type.value

    # Validate confidence
    confidence = max(0.0, min(1.0, float(confidence)))

    # Build metadata header to embed in content
    metadata_lines = []
    metadata_lines.append("=" * 50)
    metadata_lines.append("METADATA")
    metadata_lines.append("=" * 50)

    if tags:
        # Ensure tags is a list of strings
        if isinstance(tags, str):
            tags = [tags]
        metadata_lines.append(f"Tags: {', '.join(tags)}")

    if context:
        # Ensure context is a dictionary
        if not isinstance(context, dict):
            context = {"value": str(context)}
        metadata_lines.append(f"Context: {json.dumps(context, indent=2)}")

    metadata_lines.append(f"Confidence: {confidence}")
    metadata_lines.append(f"Timestamp: {datetime.now().isoformat()}")

    if knowledge_id:
        metadata_lines.append(f"ID: {knowledge_id}")

    metadata_lines.append("=" * 50)
    metadata_lines.append("")  # Empty line before content

    # Combine metadata with content
    enhanced_content = "\n".join(metadata_lines) + content

    try:
        # Call the MCP tool with only supported parameters
        # Note: Import should be done inside function to avoid circular dependencies
        from mcp_tools import mcp__knowledge__knowledge_store

        result = mcp__knowledge__knowledge_store(
            knowledge_type=knowledge_type, content=enhanced_content
        )

        logger.info(
            f"Successfully stored knowledge: {result.get('knowledge_id', 'unknown')}"
        )
        return result

    except Exception as e:
        logger.error(f"Failed to store knowledge: {str(e)}")
        # Return a failure result
        return {"success": False, "error": str(e), "knowledge_id": None}


def safe_knowledge_query(
    query_type: str,
    query_text: Optional[str] = None,
    knowledge_type: Optional[Union[str, KnowledgeType]] = None,
    min_confidence: float = 0.0,
    limit: int = 10,
    tags: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Safely query knowledge with parameter validation.

    Args:
        query_type: Type of query ("search", "by_type", "recent", "high_confidence")
        query_text: Text to search for (required for "search" query)
        knowledge_type: Filter by knowledge type
        min_confidence: Minimum confidence threshold (0.0-1.0)
        limit: Maximum number of results
        tags: Filter by tags (Note: may not work until MCP fix)

    Returns:
        List of knowledge entries matching the query

    Example:
        >>> results = safe_knowledge_query(
        ...     query_type="search",
        ...     query_text="validation error",
        ...     min_confidence=0.7,
        ...     limit=5
        ... )
        >>> for r in results:
        ...     print(r["content"][:100])
    """
    # Validate query_type
    valid_query_types = ["search", "by_type", "recent", "high_confidence", "related"]
    if query_type not in valid_query_types:
        raise ValueError(f"Invalid query_type. Must be one of: {valid_query_types}")

    # Validate knowledge_type if provided
    if isinstance(knowledge_type, KnowledgeType):
        knowledge_type = knowledge_type.value

    # Build query parameters
    params = {
        "query_type": query_type,
        "limit": limit,
        "min_confidence": max(0.0, min(1.0, float(min_confidence))),
    }

    if query_text:
        params["query_text"] = query_text

    if knowledge_type:
        params["knowledge_type"] = knowledge_type

    try:
        # Call the MCP tool
        from mcp_tools import mcp__knowledge__knowledge_query

        results = mcp__knowledge__knowledge_query(**params)

        # Post-process results to extract embedded metadata
        processed_results = []
        for result in results:
            processed = extract_embedded_metadata(result)
            processed_results.append(processed)

        logger.info(f"Query returned {len(processed_results)} results")
        return processed_results

    except Exception as e:
        logger.error(f"Failed to query knowledge: {str(e)}")
        return []


def extract_embedded_metadata(entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract embedded metadata from content field.

    Args:
        entry: Knowledge entry with embedded metadata in content

    Returns:
        Entry with extracted metadata fields
    """
    content = entry.get("content", "")

    # Look for metadata section
    if "=" * 50 in content and "METADATA" in content:
        try:
            # Split content into metadata and actual content
            parts = content.split("=" * 50)
            if len(parts) >= 4:
                metadata_section = parts[2]  # The section between separators
                actual_content = ("=" * 50).join(parts[3:])

                # Parse metadata lines
                for line in metadata_section.split("\n"):
                    line = line.strip()
                    if line.startswith("Tags:"):
                        tags_str = line[5:].strip()
                        entry["extracted_tags"] = [
                            t.strip() for t in tags_str.split(",")
                        ]
                    elif line.startswith("Context:"):
                        # Context might be multi-line JSON
                        context_start = metadata_section.index("Context:") + 8
                        context_end = (
                            metadata_section.index("\n", context_start + 100)
                            if "\nConfidence:" in metadata_section
                            else len(metadata_section)
                        )
                        try:
                            context_str = metadata_section[
                                context_start:context_end
                            ].strip()
                            entry["extracted_context"] = json.loads(context_str)
                        except Exception:
                            entry["extracted_context"] = {}
                    elif line.startswith("Confidence:"):
                        try:
                            entry["extracted_confidence"] = float(line[11:].strip())
                        except Exception:
                            entry["extracted_confidence"] = 0.8
                    elif line.startswith("Timestamp:"):
                        entry["extracted_timestamp"] = line[10:].strip()

                # Store cleaned content
                entry["clean_content"] = actual_content.strip()
        except Exception as e:
            logger.debug(f"Could not extract metadata: {e}")

    return entry


def safe_knowledge_update(
    knowledge_id: str,
    update_type: str = "success",
    failure_reason: Optional[str] = None,
    new_confidence: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Safely update knowledge entry based on usage outcomes.

    Args:
        knowledge_id: ID of knowledge to update
        update_type: Type of update ("success", "failure", "deprecate")
        failure_reason: Reason for failure (if update_type is "failure")
        new_confidence: New confidence score to set

    Returns:
        Update result dictionary
    """
    # Build update metadata
    update_metadata = {
        "update_type": update_type,
        "timestamp": datetime.now().isoformat(),
    }

    if failure_reason and update_type == "failure":
        update_metadata["failure_reason"] = failure_reason

    if new_confidence is not None:
        update_metadata["new_confidence"] = max(0.0, min(1.0, float(new_confidence)))

    try:
        # Call the MCP tool
        from mcp_tools import mcp__knowledge__knowledge_update

        result = mcp__knowledge__knowledge_update(
            knowledge_id=knowledge_id,
            update_type=update_type,
            failure_reason=failure_reason,
        )

        logger.info(f"Successfully updated knowledge: {knowledge_id}")
        return result

    except Exception as e:
        logger.error(f"Failed to update knowledge: {str(e)}")
        return {"success": False, "error": str(e), "knowledge_id": knowledge_id}


def safe_knowledge_relate(
    source_id: str,
    target_id: str,
    relationship_type: str = "RELATED_TO",
    properties: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Safely create relationships between knowledge entries.

    Args:
        source_id: Source knowledge ID
        target_id: Target knowledge ID
        relationship_type: Type of relationship
        properties: Optional relationship properties

    Returns:
        Relationship creation result
    """
    # Valid relationship types
    valid_relationships = [
        "RELATED_TO",
        "SIMILAR_TO",
        "DERIVED_FROM",
        "REQUIRES",
        "CONTRADICTS",
        "ENHANCES",
    ]

    if relationship_type not in valid_relationships:
        logger.warning(f"Non-standard relationship type: {relationship_type}")

    try:
        # Call the MCP tool
        from mcp_tools import mcp__knowledge__knowledge_relate

        result = mcp__knowledge__knowledge_relate(
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
            properties=properties or {},
        )

        logger.info(f"Successfully created relationship: {source_id} -> {target_id}")
        return result

    except Exception as e:
        logger.error(f"Failed to create relationship: {str(e)}")
        return {"success": False, "error": str(e)}


class KnowledgeQueryBuilder:
    """
    Fluent interface for building complex knowledge queries.

    Example:
        >>> results = (KnowledgeQueryBuilder()
        ...     .of_type(KnowledgeType.ERROR_SOLUTION)
        ...     .with_tags("python", "async")
        ...     .containing("validation")
        ...     .with_min_confidence(0.8)
        ...     .limit(5)
        ...     .execute())
    """

    def __init__(self):
        self.params = {"query_type": "search", "limit": 10, "min_confidence": 0.0}

    def of_type(self, *types: Union[str, KnowledgeType]) -> "KnowledgeQueryBuilder":
        """Filter by knowledge type(s)."""
        type_values = []
        for t in types:
            if isinstance(t, KnowledgeType):
                type_values.append(t.value)
            else:
                type_values.append(t)

        if len(type_values) == 1:
            self.params["knowledge_type"] = type_values[0]
            self.params["query_type"] = "by_type"
        else:
            # Multiple types not yet supported, use first one
            self.params["knowledge_type"] = type_values[0]
            self.params["query_type"] = "by_type"

        return self

    def with_tags(self, *tags: str) -> "KnowledgeQueryBuilder":
        """Filter by tags (Note: may not work until MCP fix)."""
        self.params["tags"] = list(tags)
        return self

    def containing(self, text: str) -> "KnowledgeQueryBuilder":
        """Search for specific text content."""
        self.params["query_text"] = text
        self.params["query_type"] = "search"
        return self

    def with_min_confidence(self, confidence: float) -> "KnowledgeQueryBuilder":
        """Set minimum confidence threshold."""
        self.params["min_confidence"] = max(0.0, min(1.0, float(confidence)))
        if confidence >= 0.8:
            self.params["query_type"] = "high_confidence"
        return self

    def recent(self, limit: int = 10) -> "KnowledgeQueryBuilder":
        """Get recent entries."""
        self.params["query_type"] = "recent"
        self.params["limit"] = limit
        return self

    def limit(self, count: int) -> "KnowledgeQueryBuilder":
        """Limit number of results."""
        self.params["limit"] = count
        return self

    def execute(self) -> List[Dict[str, Any]]:
        """Execute the query and return results."""
        return safe_knowledge_query(**self.params)


# Convenience functions for common patterns
def store_error_solution(
    error: str, solution: str, confidence: float = 0.9
) -> Dict[str, Any]:
    """Store an error and its solution."""
    return safe_knowledge_store(
        knowledge_type=KnowledgeType.ERROR_SOLUTION,
        content=f"Error: {error}\n\nSolution: {solution}",
        tags=["error", "solution", "fix"],
        context={
            "error_type": type(error).__name__
            if hasattr(error, "__class__")
            else "Unknown"
        },
        confidence=confidence,
    )


def store_code_pattern(
    pattern_name: str, code: str, language: str = "python", confidence: float = 0.85
) -> Dict[str, Any]:
    """Store a code pattern."""
    return safe_knowledge_store(
        knowledge_type=KnowledgeType.CODE_PATTERN,
        content=f"Pattern: {pattern_name}\n\n```{language}\n{code}\n```",
        tags=["code", "pattern", language],
        context={"language": language, "pattern_name": pattern_name},
        confidence=confidence,
    )


def store_research_finding(
    finding: str, sources: List[str], confidence: float = 0.8
) -> Dict[str, Any]:
    """Store a research finding."""
    return safe_knowledge_store(
        knowledge_type=KnowledgeType.RESEARCH_FINDINGS,
        content=finding,
        tags=["research", "finding"],
        context={"sources": sources, "source_count": len(sources)},
        confidence=confidence,
    )


# Module initialization logging
logger.info(
    "Knowledge Tool Helper v1.0.0 loaded - Workarounds active for MCP limitations"
)
