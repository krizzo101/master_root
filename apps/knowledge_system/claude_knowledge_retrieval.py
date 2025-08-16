#!/usr/bin/env python3
"""
Claude Knowledge Retrieval System

This module provides functions that Claude can use during conversations
to retrieve and apply learned knowledge from the Neo4j database.
"""

import json
from typing import Dict, List, Optional, Any


class ClaudeKnowledgeRetrieval:
    """
    Knowledge retrieval system for Claude to use during conversations
    """
    
    @staticmethod
    def query_relevant_knowledge(query: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Query for relevant knowledge based on current conversation context
        
        This function would be called by Claude during conversations to:
        1. Find relevant error solutions
        2. Retrieve applicable code patterns
        3. Get workflow recommendations
        4. Access user preferences
        
        Args:
            query: The search query or problem description
            context: Additional context (e.g., language, error type, tool)
            
        Returns:
            List of relevant knowledge entries with confidence scores
        """
        
        # Build the Cypher query based on context
        cypher_parts = []
        params = {'query': query}
        
        # Base query
        base_query = "MATCH (k:Knowledge) WHERE "
        
        # Add content matching
        conditions = ["(toLower(k.content) CONTAINS toLower($query))"]
        
        # Add context-specific filters if provided
        if context:
            if 'error_type' in context:
                conditions.append("(k.knowledge_type = 'ERROR_SOLUTION')")
                conditions.append("(k.context CONTAINS $error_type)")
                params['error_type'] = context['error_type']
                
            if 'language' in context:
                conditions.append("(k.context CONTAINS $language OR any(tag IN k.tags WHERE tag = $language))")
                params['language'] = context['language'].lower()
                
            if 'tool' in context:
                conditions.append("(k.context CONTAINS $tool OR any(tag IN k.tags WHERE tag = $tool))")
                params['tool'] = context['tool'].lower()
                
            if 'knowledge_type' in context:
                conditions.append("(k.knowledge_type = $knowledge_type)")
                params['knowledge_type'] = context['knowledge_type']
        
        # Combine conditions
        where_clause = " OR ".join(conditions)
        
        # Full query with sorting and limit
        full_query = f"""
        {base_query} {where_clause}
        RETURN k.knowledge_id as id, 
               k.knowledge_type as type,
               k.content as content,
               k.confidence_score as confidence,
               k.success_rate as success_rate,
               k.usage_count as usage_count,
               k.context as context,
               k.tags as tags
        ORDER BY k.confidence_score DESC, k.success_rate DESC
        LIMIT 5
        """
        
        # This would be executed via MCP tool:
        # results = await mcp__db__read_neo4j_cypher(query=full_query, params=params)
        
        # For demonstration, return formatted query
        return {
            'query': full_query,
            'params': params,
            'instruction': 'Execute via mcp__db__read_neo4j_cypher'
        }
    
    @staticmethod
    def get_error_solution(error_message: str, error_type: str = None) -> Optional[Dict[str, Any]]:
        """
        Get specific solution for an error
        
        Args:
            error_message: The error message to resolve
            error_type: Optional error type (e.g., ImportError, SyntaxError)
            
        Returns:
            Best matching error solution if found
        """
        
        query = """
        MATCH (k:Knowledge {knowledge_type: 'ERROR_SOLUTION'})
        WHERE toLower(k.content) CONTAINS toLower($error_msg)
        OR toLower(k.context) CONTAINS toLower($error_msg)
        RETURN k.content as solution,
               k.confidence_score as confidence,
               k.success_rate as success_rate,
               k.context as context
        ORDER BY k.confidence_score DESC, k.success_rate DESC
        LIMIT 1
        """
        
        params = {'error_msg': error_message}
        
        return {
            'query': query,
            'params': params,
            'instruction': 'Execute via mcp__db__read_neo4j_cypher to get error solution'
        }
    
    @staticmethod
    def get_workflow_for_task(task_description: str, tool: str = None) -> Optional[Dict[str, Any]]:
        """
        Get recommended workflow for a specific task
        
        Args:
            task_description: Description of the task to accomplish
            tool: Optional tool specification (e.g., git, docker, python)
            
        Returns:
            Best matching workflow if found
        """
        
        conditions = ["toLower(k.content) CONTAINS toLower($task)"]
        params = {'task': task_description}
        
        if tool:
            conditions.append("(k.context CONTAINS $tool OR any(tag IN k.tags WHERE tag = $tool))")
            params['tool'] = tool.lower()
        
        where_clause = " AND ".join(conditions)
        
        query = f"""
        MATCH (k:Knowledge {{knowledge_type: 'WORKFLOW'}})
        WHERE {where_clause}
        RETURN k.content as workflow,
               k.confidence_score as confidence,
               k.context as context,
               k.tags as tags
        ORDER BY k.confidence_score DESC
        LIMIT 1
        """
        
        return {
            'query': query,
            'params': params,
            'instruction': 'Execute via mcp__db__read_neo4j_cypher to get workflow'
        }
    
    @staticmethod
    def record_knowledge_usage(knowledge_id: str, success: bool, metrics: Dict[str, float] = None):
        """
        Record that a piece of knowledge was used and whether it was successful
        
        Args:
            knowledge_id: The ID of the knowledge that was used
            success: Whether the application was successful
            metrics: Optional success metrics
        """
        
        if success:
            # Update success metrics
            query = """
            MATCH (k:Knowledge {knowledge_id: $kid})
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
                k.updated_at = datetime()
            RETURN k.knowledge_id as id
            """
        else:
            # Record failure
            query = """
            MATCH (k:Knowledge {knowledge_id: $kid})
            SET k.usage_count = k.usage_count + 1,
                k.success_rate = ((k.success_rate * k.usage_count) + 0.0) / (k.usage_count + 1),
                k.confidence_score = CASE 
                    WHEN k.success_rate < 0.3 
                    THEN max(0.1, k.confidence_score - 0.1)
                    ELSE k.confidence_score
                END,
                k.updated_at = datetime()
            RETURN k.knowledge_id as id
            """
        
        params = {'kid': knowledge_id}
        
        return {
            'query': query,
            'params': params,
            'instruction': 'Execute via mcp__db__write_neo4j_cypher to update knowledge'
        }
    
    @staticmethod
    def store_new_learning(knowledge_type: str, 
                                content: str,
                                context: Dict[str, Any],
                                tags: List[str] = None) -> Dict[str, Any]:
        """
        Store new knowledge learned during conversation
        
        Args:
            knowledge_type: Type of knowledge
            content: The knowledge content
            context: Contextual information
            tags: Optional tags
            
        Returns:
            Query to store the knowledge
        """
        
        import hashlib
        from datetime import datetime
        
        # Generate unique ID
        knowledge_id = hashlib.sha256(f"{knowledge_type}:{content[:100]}".encode()).hexdigest()[:16]
        
        query = """
        MERGE (k:Knowledge {knowledge_id: $kid})
        ON CREATE SET
            k.knowledge_type = $ktype,
            k.content = $content,
            k.context = $context,
            k.confidence_score = 0.7,
            k.usage_count = 0,
            k.success_rate = 0.0,
            k.created_at = datetime(),
            k.updated_at = datetime(),
            k.tags = $tags
        ON MATCH SET
            k.updated_at = datetime(),
            k.usage_count = k.usage_count + 1
        RETURN k.knowledge_id as id
        """
        
        params = {
            'kid': knowledge_id,
            'ktype': knowledge_type,
            'content': content,
            'context': json.dumps(context),
            'tags': tags or []
        }
        
        return {
            'query': query,
            'params': params,
            'instruction': 'Execute via mcp__db__write_neo4j_cypher to store new knowledge'
        }


# Example usage instructions for Claude
USAGE_INSTRUCTIONS = """
# How to Use the Knowledge System During Conversations

## 1. Query for Relevant Knowledge
When facing a problem or question, first check if there's existing knowledge:

```python
# For error solutions
result = await mcp__db__read_neo4j_cypher(
    query=knowledge_queries['error_solution']['query'],
    params=knowledge_queries['error_solution']['params']
)

# For code patterns
context = {'language': 'python', 'knowledge_type': 'CODE_PATTERN'}
query_info = ClaudeKnowledgeRetrieval.query_relevant_knowledge("async programming", context)
result = await mcp__db__read_neo4j_cypher(query=query_info['query'], params=query_info['params'])
```

## 2. Apply Knowledge
When you find relevant knowledge with high confidence (>0.7), apply it to the current situation.

## 3. Record Usage
After applying knowledge, record whether it was successful:

```python
# If successful
update_query = ClaudeKnowledgeRetrieval.record_knowledge_usage('knowledge_id_here', True)
await mcp__db__write_neo4j_cypher(query=update_query['query'], params=update_query['params'])

# If failed
update_query = ClaudeKnowledgeRetrieval.record_knowledge_usage('knowledge_id_here', False)
await mcp__db__write_neo4j_cypher(query=update_query['query'], params=update_query['params'])
```

## 4. Store New Learnings
When you successfully solve a new problem or discover a pattern:

```python
store_query = ClaudeKnowledgeRetrieval.store_new_learning(
    knowledge_type='ERROR_SOLUTION',
    content='Solution description here',
    context={'error_type': 'ImportError', 'language': 'Python'},
    tags=['python', 'import', 'error']
)
await mcp__db__write_neo4j_cypher(query=store_query['query'], params=store_query['params'])
```

## 5. Knowledge Types
- ERROR_SOLUTION: Solutions to specific errors
- CODE_PATTERN: Reusable code patterns and best practices
- WORKFLOW: Step-by-step processes that work
- USER_PREFERENCE: How this user likes things done
- CONTEXT_PATTERN: What approaches work in what contexts
- TOOL_USAGE: Effective tool usage patterns
"""


if __name__ == "__main__":
    # Demonstration of query generation
    retriever = ClaudeKnowledgeRetrieval()
    
    print("=== Example Queries for Claude to Use ===\n")
    
    # Example 1: Query for error solution
    error_query = retriever.get_error_solution("No module named numpy", "ImportError")
    print("Error Solution Query:")
    print(json.dumps(error_query, indent=2))
    print()
    
    # Example 2: Query for workflow
    workflow_query = retriever.get_workflow_for_task("create pull request", "git")
    print("Workflow Query:")
    print(json.dumps(workflow_query, indent=2))
    print()
    
    # Example 3: General knowledge query
    general_query = retriever.query_relevant_knowledge(
        "async programming",
        {'language': 'python', 'knowledge_type': 'CODE_PATTERN'}
    )
    print("General Knowledge Query:")
    print(json.dumps(general_query, indent=2))
    print()
    
    print(USAGE_INSTRUCTIONS)