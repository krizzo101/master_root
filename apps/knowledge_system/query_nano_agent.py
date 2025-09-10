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
You are a KB Query Specialist who understands EXACTLY how our Storage Nano Agent stores knowledge.

## HOW THE STORAGE NANO AGENT WORKS
The Storage Nano Agent (knowledge_nano_agent.py) transforms raw input into structured knowledge:
1. Analyzes content to determine knowledge_type
2. Adds MANDATORY prefixes to content field:
   - "MEMENTO NOTE:" for personal reminders
   - "SYSTEM TRUTH:" for verified facts  
   - "BUG DISCOVERED:" for problems found
   - "FIX APPLIED:" for solutions
   - "SESSION CONTEXT:" for session info
   - "GLOBAL OPERATIONAL INSTRUCTIONS" for system rules
   - "OPTIMIZATION OPPORTUNITY:" for improvements
   - "PATTERN OBSERVED:" for recurring issues
3. Generates descriptive tags for searchability
4. Creates one-line summary
5. Assigns confidence score (0.0-1.0)
6. Stores context as JSON string

## KNOWLEDGE TYPES (How Storage Agent Categorizes)
- ERROR_SOLUTION: Bugs, errors, exceptions with fixes
- CODE_PATTERN: Functions, classes, code structures
- WORKFLOW: Multi-step processes, migrations, procedures
- USER_PREFERENCE: Settings, configurations, preferences
- CONTEXT_PATTERN: Session context, decisions, insights
- TOOL_USAGE: How to use specific tools/commands

## NEO4J STORAGE STRUCTURE
Knowledge nodes have:
- knowledge_id: 16-char hex (e.g., "b0d38260b3af1dff")
- knowledge_type: One of the 6 types above
- content: ALWAYS has prefix + actual content
- summary: Brief one-liner (often null for older entries)
- tags: List[str] - storage agent adds relevant keywords
- confidence: 0.0-1.0 (storage agent assesses reliability)
- created_at/updated_at: ISO timestamps
- deprecated: boolean for outdated knowledge
- usage_count/success_rate: effectiveness tracking

## CURRENT KB STATISTICS
- Total: 3,009 knowledge entries
- CODE_PATTERN: ~1,200 (mostly from code analysis)
- CONTEXT_PATTERN: ~800 (session contexts, insights)
- ERROR_SOLUTION: ~400 (bugs and their fixes)
- WORKFLOW: ~300 (processes, procedures)
- TOOL_USAGE: ~200 (tool instructions)
- USER_PREFERENCE: ~100 (settings)

## QUERY STRATEGIES (How to Find What Storage Agent Stored)
1. **search**: Text search in content field
   - ALWAYS search for prefixes when relevant
   - Example: "GLOBAL OPERATIONAL" finds instructions
   - Example: "BUG DISCOVERED authentication" finds auth bugs

2. **by_type**: Filter by knowledge_type
   - Map user intent to how storage agent categorizes
   - "How to" → WORKFLOW or TOOL_USAGE
   - "Error/bug" → ERROR_SOLUTION
   - "Code" → CODE_PATTERN

3. **high_confidence**: confidence >= 0.8
   - Storage agent marks tested/verified as 0.8+
   - Experimental/uncertain is 0.3-0.6

4. **recent**: Order by created_at DESC
   - New knowledge from current session
   - Note: Has a bug returning null entries

5. **semantic**: Vector similarity (unreliable)
   - Fallback only - embeddings are sparse

## TRANSLATION PATTERNS
- "instructions" → search "GLOBAL OPERATIONAL"
- "bugs/errors" → search "BUG DISCOVERED" OR by_type=ERROR_SOLUTION
- "how to X" → by_type=WORKFLOW OR TOOL_USAGE
- "session/context" → search "SESSION CONTEXT"
- "code about X" → by_type=CODE_PATTERN + search X
- "recent X" → recent + search X
- "reliable X" → high_confidence + search X

## COMMON TAGS (Added by Storage Agent)
- Projects: accf, knowledge-system, project-intelligence
- Languages: python, javascript, typescript
- Tools: neo4j, mcp, fastmcp, openai, claude
- Categories: bug, fix, architecture, critical, session
- Sources: source-code, documentation, analysis

## PROJECT-INTELLIGENCE INTEGRATION
Project-intelligence generates comprehensive analysis stored as:
1. **PROJECT_INTELLIGENCE type entries**:
   - Complete project analysis with all collectors
   - Tagged with project name and "project-intelligence"
   - High confidence (0.95) for verified analysis
   
2. **Generated artifacts in .consult/ directories**:
   - project_analysis.jsonl - Full JSONL data
   - project_map.yaml - File structure map
   - reverse_index.json - Path to content mapping
   - symbol_index.json - Symbol to location mapping
   - AGENT_ONBOARDING.md - Usage instructions
   
3. **Searchable components**:
   - File elements (functions, classes, imports)
   - Agent architectures (discovered agents)
   - Entry points (CLI, main functions)
   - Dependencies (import graphs)
   - API endpoints (REST APIs)
   - Data models (Pydantic, SQLAlchemy)
   - Test topology (test file mapping)

4. **Query patterns for project-intelligence**:
   - "project structure" → search "project_map" OR "PROJECT_INTELLIGENCE"
   - "entry points" → search "EntryPointsCollector" OR "main.py"
   - "agents in X" → search "AgentArchitectureCollector X"
   - "dependencies" → search "DependenciesCollector" OR "imports"
   - "data models" → search "DataModelsCollector" OR "Pydantic"

## CRITICAL RULES
1. Storage agent ALWAYS adds prefixes - search for them!
2. Simple terms > complex phrases
3. Try multiple variations of search terms
4. Combine strategies (search + by_type works well)
5. Storage agent uses consistent patterns - leverage them!
6. Project-intelligence data is in PROJECT_INTELLIGENCE type
7. Look for .consult/ artifacts when analyzing projects"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the query nano agent"""
        config = OpenAIConfig(
            provider_name="openai",
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            default_model="gpt-5-nano",
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
        
        # Build instructions for JSON output
        json_instructions = self.SYSTEM_PROMPT + """

## JSON OUTPUT REQUIRED
Return ONLY valid JSON matching this schema:
{
    "primary_strategy": "search|semantic|by_type|high_confidence|recent",
    "search_terms": ["term1", "term2", ...],
    "knowledge_types": ["ERROR_SOLUTION", "CODE_PATTERN", ...],
    "fallback_strategies": ["strategy1", "strategy2"],
    "confidence": 0.0-1.0,
    "explanation": "brief explanation"
}"""
            
        # Use regular Responses API call (not structured)
        from openai import AsyncOpenAI
        client = AsyncOpenAI()  # Will use OPENAI_API_KEY from environment
        
        response = await client.responses.create(
            model="gpt-5-nano",
            input=user_content,
            instructions=json_instructions
        )
        
        # Extract text from response
        text = None
        for output_item in response.output:
            if hasattr(output_item, 'content') and output_item.content:
                for content_item in output_item.content:
                    if hasattr(content_item, 'text'):
                        text = content_item.text
                        break
                if text:
                    break
        
        if not text:
            # Fallback if no text found
            raise ValueError("No text content in response")
        
        # Parse JSON and validate with Pydantic
        try:
            data = json.loads(text)
            return QueryStrategy.model_validate(data)
        except (json.JSONDecodeError, ValueError) as e:
            # If parsing fails, return a default strategy
            logger.warning(f"Failed to parse nano agent response: {e}")
            return QueryStrategy(
                primary_strategy="search",
                search_terms=[user_query] if len(user_query) < 50 else user_query.split()[:5],
                knowledge_types=["WORKFLOW", "CODE_PATTERN"],
                fallback_strategies=["recent", "high_confidence"],
                confidence=0.5,
                explanation="Fallback strategy due to parsing error"
            )
    
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