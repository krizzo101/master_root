#!/usr/bin/env python3
"""
Query Nano Agent - Intelligent query translation for knowledge retrieval

This agent helps translate poor queries into effective search strategies,
learning from patterns and adapting to how knowledge is actually stored.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

from opsvi_llm.providers.openai_provider import OpenAIConfig
from opsvi_llm.providers.openai_unified_interface import OpenAIUnifiedInterface
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class QueryStrategy(BaseModel):
    """Structured output for query translation"""
    
    model_config = {"extra": "forbid"}
    
    primary_strategy: str = Field(
        description="Primary query type: search, semantic, by_type, high_confidence, recent"
    )
    search_terms: List[str] = Field(
        description="Multiple search terms to try (simple, specific words)"
    )
    knowledge_types: List[str] = Field(
        description="Likely knowledge types: ERROR_SOLUTION, CODE_PATTERN, WORKFLOW, etc."
    )
    fallback_strategies: List[str] = Field(
        description="Alternative query strategies if primary fails"
    )
    confidence: float = Field(
        description="Confidence in understanding the query intent (0.0-1.0)",
        ge=0.0, le=1.0
    )
    explanation: str = Field(
        description="Brief explanation of the query interpretation"
    )


class QueryNanoAgent:
    """
    Intelligent query assistant that translates vague queries into effective searches
    """
    
    SYSTEM_PROMPT = """## ROLE
You are a query translation expert that helps find knowledge in a Neo4j database.

## CONTEXT
Knowledge is stored with these types:
- ERROR_SOLUTION: Solutions to errors/problems
- CODE_PATTERN: Reusable code patterns
- WORKFLOW: Step-by-step processes
- USER_PREFERENCE: User preferences
- CONTEXT_PATTERN: Contextual patterns
- TOOL_USAGE: Tool usage instructions

## QUERY STRATEGIES
- search: Keyword search in content/tags
- semantic: Vector similarity search
- by_type: Filter by knowledge type
- high_confidence: Get highly reliable knowledge
- recent: Get recently added/updated knowledge

## TRANSLATION RULES
1. Break complex queries into SIMPLE search terms
2. Avoid long phrases - use individual keywords
3. Identify likely knowledge types from context
4. Provide multiple search variations
5. Order strategies by likelihood of success

## EXAMPLES
Bad query: "recent project work knowledge system ACCF"
Good terms: ["ACCF", "project", "knowledge", "recent"]

Bad query: "how to fix authentication errors in Python"
Good terms: ["authentication", "error", "python", "login", "auth"]

## OUTPUT
Return structured strategy for finding the requested knowledge."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the query nano agent"""
        config = OpenAIConfig(
            provider_name="openai",
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            default_model="gpt-5-nano",
            temperature=0.3,
            max_tokens=500,
            enable_audit_logging=True,
        )
        self.interface = OpenAIUnifiedInterface(config)
        logger.info("Query Nano Agent initialized")
        
    async def translate_query(
        self,
        user_query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> QueryStrategy:
        """
        Translate a user query into an effective search strategy
        
        Args:
            user_query: The user's original query
            context: Optional context about current session
            
        Returns:
            QueryStrategy with multiple search approaches
        """
        # Build user message
        user_content = f"Query: {user_query}"
        if context:
            user_content += f"\nContext: {json.dumps(context)}"
            
        # Get structured response
        response = await self.interface.generate_structured(
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ],
            response_format=QueryStrategy,
            max_retries=2
        )
        
        return response
    
    def translate_query_sync(
        self,
        user_query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> QueryStrategy:
        """Synchronous wrapper for translate_query"""
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(
            self.translate_query(user_query, context)
        )


class SmartQueryExecutor:
    """
    Executes queries using intelligent strategies from the nano agent
    """
    
    def __init__(self):
        self.nano_agent = QueryNanoAgent()
        self.query_history = []
        
    async def smart_query(
        self,
        user_query: str,
        limit: int = 5,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a smart query with fallback strategies
        
        Args:
            user_query: The user's original query
            limit: Maximum results to return
            context: Optional session context
            
        Returns:
            Query results with strategy information
        """
        # Get query strategy from nano agent
        strategy = await self.nano_agent.translate_query(user_query, context)
        
        results = {
            "original_query": user_query,
            "strategy": strategy.model_dump(),
            "attempts": [],
            "results": [],
            "success": False
        }
        
        # Import the query tool
        from apps.knowledge_system.mcp_knowledge_tools import get_enhanced_query
        query_tool = get_enhanced_query()
        
        # Try primary strategy
        primary_result = None
        if strategy.primary_strategy == "search":
            for term in strategy.search_terms[:3]:  # Try first 3 terms
                try:
                    result = query_tool.query(
                        query_type="search",
                        query_text=term,
                        limit=limit,
                        direct_execute=True
                    )
                    
                    results["attempts"].append({
                        "strategy": "search",
                        "term": term,
                        "found": result.get("count", 0)
                    })
                    
                    if result.get("results"):
                        results["results"].extend(result["results"])
                        results["success"] = True
                        
                except Exception as e:
                    logger.warning(f"Search for '{term}' failed: {e}")
                    
        elif strategy.primary_strategy == "by_type":
            for ktype in strategy.knowledge_types[:2]:  # Try first 2 types
                try:
                    result = query_tool.query(
                        query_type="by_type",
                        knowledge_type=ktype,
                        limit=limit,
                        direct_execute=True
                    )
                    
                    results["attempts"].append({
                        "strategy": "by_type",
                        "type": ktype,
                        "found": result.get("count", 0)
                    })
                    
                    if result.get("results"):
                        results["results"].extend(result["results"])
                        results["success"] = True
                        
                except Exception as e:
                    logger.warning(f"Query by type '{ktype}' failed: {e}")
                    
        # If primary failed, try fallbacks
        if not results["success"]:
            for fallback in strategy.fallback_strategies[:2]:
                if fallback == "high_confidence":
                    try:
                        result = query_tool.query(
                            query_type="high_confidence",
                            limit=limit,
                            direct_execute=True
                        )
                        
                        results["attempts"].append({
                            "strategy": "high_confidence",
                            "found": result.get("count", 0)
                        })
                        
                        if result.get("results"):
                            results["results"].extend(result["results"])
                            results["success"] = True
                            break
                            
                    except Exception as e:
                        logger.warning(f"High confidence query failed: {e}")
                        
                elif fallback == "recent":
                    try:
                        result = query_tool.query(
                            query_type="recent",
                            limit=limit,
                            direct_execute=True
                        )
                        
                        results["attempts"].append({
                            "strategy": "recent",
                            "found": result.get("count", 0)
                        })
                        
                        if result.get("results"):
                            results["results"].extend(result["results"])
                            results["success"] = True
                            break
                            
                    except Exception as e:
                        logger.warning(f"Recent query failed: {e}")
        
        # Deduplicate results
        if results["results"]:
            seen_ids = set()
            unique_results = []
            for item in results["results"]:
                if item.get("id") not in seen_ids:
                    seen_ids.add(item.get("id"))
                    unique_results.append(item)
            results["results"] = unique_results[:limit]
            
        # Store query history for learning
        self.query_history.append({
            "query": user_query,
            "strategy": strategy.model_dump(),
            "success": results["success"],
            "result_count": len(results["results"])
        })
        
        return results


# Singleton instance
_smart_executor = None

def get_smart_executor() -> SmartQueryExecutor:
    """Get or create the smart query executor"""
    global _smart_executor
    if _smart_executor is None:
        _smart_executor = SmartQueryExecutor()
    return _smart_executor


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_smart_query():
        executor = get_smart_executor()
        
        # Test with a vague query
        result = await executor.smart_query(
            "recent work on knowledge system and ACCF",
            limit=5
        )
        
        print(json.dumps(result, indent=2))
        
    asyncio.run(test_smart_query())