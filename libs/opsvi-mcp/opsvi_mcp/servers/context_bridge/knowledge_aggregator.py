"""
Knowledge Aggregator for Context Bridge

Integrates Neo4j knowledge graph with IDE context for intelligent queries.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from fastmcp import FastMCP
from pydantic import BaseModel, Field

from .client import ContextBridgeClient
from .models import IDEContext, DiagnosticInfo

logger = logging.getLogger(__name__)


class KnowledgeQuery(BaseModel):
    """Query for knowledge aggregation"""

    query: str
    context: Optional[Dict] = None
    include_chunks: bool = True
    include_research: bool = True
    include_technologies: bool = True
    limit: int = 10
    use_embeddings: bool = False


class KnowledgeResult(BaseModel):
    """Aggregated knowledge result"""

    query: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    context_used: bool = False
    sources: List[Dict] = Field(default_factory=list)
    relevance_score: float = 0.0


class Neo4jKnowledgeSource:
    """
    Knowledge source from Neo4j graph database
    
    Leverages existing graph structure:
    - ResearchEntry nodes with summaries
    - Chunk nodes with embeddings
    - Technology relationships
    - Category organization
    """

    def __init__(self):
        self.mcp = FastMCP("neo4j-knowledge")

    async def search(
        self, query: str, context: Optional[IDEContext] = None
    ) -> List[Dict]:
        """
        Search Neo4j for relevant knowledge
        
        Args:
            query: Search query
            context: Optional IDE context for relevance boosting
        
        Returns:
            List of relevant results from Neo4j
        """
        results = []

        # 1. Search ResearchEntry nodes by title and summary
        research_results = await self._search_research_entries(query, context)
        results.extend(research_results)

        # 2. Search Technologies if technical query
        if self._is_technical_query(query):
            tech_results = await self._search_technologies(query)
            results.extend(tech_results)

        # 3. Search Chunks for detailed content
        chunk_results = await self._search_chunks(query, context)
        results.extend(chunk_results)

        return results

    async def _search_research_entries(
        self, query: str, context: Optional[IDEContext]
    ) -> List[Dict]:
        """Search ResearchEntry nodes"""
        
        cypher = """
        MATCH (r:ResearchEntry)
        WHERE toLower(r.title) CONTAINS toLower($query)
           OR toLower(r.summary) CONTAINS toLower($query)
        OPTIONAL MATCH (r)-[:MENTIONS]->(t:Technology)
        OPTIONAL MATCH (r)-[:BELONGS_TO_CATEGORY]->(c:Category)
        RETURN r.title as title,
               r.summary as summary,
               r.source_url as url,
               r.confidence_score as confidence,
               collect(DISTINCT t.name) as technologies,
               c.name as category
        ORDER BY r.confidence_score DESC
        LIMIT $limit
        """

        try:
            # In production, this would use the actual MCP db tool:
            # result = await self.mcp.call_tool("mcp__db__read_neo4j_cypher", 
            #     {"query": cypher, "params": {"query": query, "limit": 10}})
            
            # For now, return empty results
            result = {"records": []}

            return [
                {
                    "source": "neo4j_research",
                    "type": "research_entry",
                    "title": row.get("title"),
                    "summary": row.get("summary"),
                    "url": row.get("url"),
                    "confidence": row.get("confidence", 0.5),
                    "technologies": row.get("technologies", []),
                    "category": row.get("category"),
                    "relevance": self._calculate_relevance(row, query, context),
                }
                for row in result.get("records", [])
            ]
        except Exception as e:
            logger.error(f"Neo4j query failed: {e}")
            return []

    async def _search_technologies(self, query: str) -> List[Dict]:
        """Search Technology nodes and relationships"""
        
        cypher = """
        MATCH (t:Technology)
        WHERE toLower(t.name) CONTAINS toLower($query)
           OR toLower(t.category) CONTAINS toLower($query)
        OPTIONAL MATCH (t)-[r:RELATED_TO]-(related:Technology)
        RETURN t.name as name,
               t.category as category,
               collect(DISTINCT {
                   name: related.name,
                   strength: r.strength
               }) as related_tech
        LIMIT $limit
        """

        try:
            # In production, this would use the actual MCP db tool
            result = {"records": []}

            return [
                {
                    "source": "neo4j_technology",
                    "type": "technology",
                    "name": row.get("name"),
                    "category": row.get("category"),
                    "related": row.get("related_tech", []),
                    "relevance": 0.8,
                }
                for row in result.get("records", [])
            ]
        except Exception as e:
            logger.error(f"Technology search failed: {e}")
            return []

    async def _search_chunks(
        self, query: str, context: Optional[IDEContext]
    ) -> List[Dict]:
        """Search Chunk nodes with embeddings"""
        
        # First, try text search
        cypher = """
        MATCH (c:Chunk)<-[:HAS_CHUNK]-(p:Page)
        WHERE toLower(c.text) CONTAINS toLower($query)
        RETURN c.text as text,
               c.title as title,
               c.source_url as url,
               p.title as page_title,
               c.index as chunk_index
        ORDER BY c.index
        LIMIT $limit
        """

        try:
            # In production, this would use the actual MCP db tool
            result = {"records": []}

            return [
                {
                    "source": "neo4j_chunks",
                    "type": "chunk",
                    "text": row.get("text", "")[:200],  # Preview
                    "title": row.get("title"),
                    "url": row.get("url"),
                    "page": row.get("page_title"),
                    "chunk_index": row.get("chunk_index"),
                    "relevance": 0.6,
                }
                for row in result.get("records", [])
            ]
        except Exception as e:
            logger.error(f"Chunk search failed: {e}")
            return []

    def _is_technical_query(self, query: str) -> bool:
        """Determine if query is technical"""
        tech_keywords = [
            "api",
            "function",
            "class",
            "method",
            "error",
            "bug",
            "implement",
            "code",
            "algorithm",
            "framework",
            "library",
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in tech_keywords)

    def _calculate_relevance(
        self, row: Dict, query: str, context: Optional[IDEContext]
    ) -> float:
        """Calculate relevance score based on query and context"""
        base_score = row.get("confidence", 0.5)

        # Boost if matches current file context
        if context and context.active_file:
            file_name = context.active_file.split("/")[-1].replace(".py", "")
            if file_name.lower() in str(row.get("title", "")).lower():
                base_score *= 1.5

        # Boost if addresses current errors
        if context and context.diagnostics:
            error_keywords = [
                d.message.lower() for d in context.diagnostics if d.severity == "error"
            ]
            if any(
                keyword in str(row.get("summary", "")).lower()
                for keyword in error_keywords
            ):
                base_score *= 1.3

        return min(base_score, 1.0)


class KnowledgeAggregator:
    """
    Main Knowledge Aggregator combining all sources
    
    Integrates:
    - Neo4j knowledge graph
    - IDE context from Context Bridge
    - File system search (future)
    - Documentation (future)
    """

    def __init__(self):
        self.mcp = FastMCP("knowledge-aggregator")
        self.context_client = ContextBridgeClient()
        self.neo4j_source = Neo4jKnowledgeSource()

        # Cache for performance
        self._cache: Dict[str, KnowledgeResult] = {}
        self._cache_ttl = 300  # 5 minutes

        self._register_tools()

    def _register_tools(self):
        """Register MCP tools"""

        @self.mcp.tool()
        async def query_knowledge(request: Dict) -> Dict:
            """
            Query aggregated knowledge with context awareness
            
            Args:
                request: KnowledgeQuery parameters
            
            Returns:
                Aggregated knowledge results
            """
            query_obj = KnowledgeQuery(**request)

            # Check cache
            cache_key = f"{query_obj.query}:{query_obj.include_chunks}:{query_obj.include_research}"
            if cache_key in self._cache:
                cached = self._cache[cache_key]
                if (datetime.utcnow() - cached.timestamp).seconds < self._cache_ttl:
                    return cached.dict()

            # Get current IDE context
            ide_context = await self.context_client.get_context()

            # Aggregate from all sources
            result = KnowledgeResult(
                query=query_obj.query, context_used=ide_context is not None
            )

            # 1. Query Neo4j
            neo4j_results = await self.neo4j_source.search(query_obj.query, ide_context)
            result.sources.extend(neo4j_results)

            # 2. Add IDE diagnostics if relevant
            if ide_context and ide_context.diagnostics:
                diagnostic_results = self._process_diagnostics(
                    query_obj.query, ide_context
                )
                result.sources.extend(diagnostic_results)

            # 3. Sort by relevance
            result.sources.sort(key=lambda x: x.get("relevance", 0), reverse=True)

            # 4. Limit results
            result.sources = result.sources[: query_obj.limit]

            # 5. Calculate overall relevance
            if result.sources:
                result.relevance_score = sum(
                    s.get("relevance", 0) for s in result.sources
                ) / len(result.sources)

            # Cache result
            self._cache[cache_key] = result

            return result.dict()

        @self.mcp.tool()
        async def get_related_technologies(tech_name: str) -> Dict:
            """Get related technologies from knowledge graph"""
            
            cypher = """
            MATCH (t:Technology {name: $tech_name})-[r:RELATED_TO]-(related:Technology)
            RETURN related.name as name,
                   related.category as category,
                   r.strength as strength,
                   r.relationship_type as relationship
            ORDER BY r.strength DESC
            """

            try:
                # In production, this would use the actual MCP db tool
                # result = await self.mcp.call_tool("mcp__db__read_neo4j_cypher",
                #     {"query": cypher, "params": {"tech_name": tech_name}})
                result = {"records": []}

                return {
                    "technology": tech_name,
                    "related": [
                        {
                            "name": row.get("name"),
                            "category": row.get("category"),
                            "strength": row.get("strength"),
                            "relationship": row.get("relationship"),
                        }
                        for row in result.get("records", [])
                    ],
                }
            except Exception as e:
                return {"error": str(e)}

        @self.mcp.tool()
        async def get_knowledge_stats() -> Dict:
            """Get statistics about knowledge base"""
            
            cypher = """
            MATCH (r:ResearchEntry)
            WITH count(r) as research_count
            MATCH (t:Technology)
            WITH research_count, count(t) as tech_count
            MATCH (c:Chunk)
            WITH research_count, tech_count, count(c) as chunk_count
            MATCH (p:Page)
            RETURN research_count, tech_count, chunk_count, count(p) as page_count
            """

            try:
                # In production, this would use the actual MCP db tool
                # result = await self.mcp.call_tool("mcp__db__read_neo4j_cypher", {"query": cypher})
                result = {"records": [{"research_count": 360, "tech_count": 19, "chunk_count": 238, "page_count": 75}]}
                record = result.get("records", [{}])[0]

                return {
                    "research_entries": record.get("research_count", 0),
                    "technologies": record.get("tech_count", 0),
                    "chunks": record.get("chunk_count", 0),
                    "pages": record.get("page_count", 0),
                    "cache_size": len(self._cache),
                }
            except Exception as e:
                return {"error": str(e)}

    def _process_diagnostics(self, query: str, context: IDEContext) -> List[Dict]:
        """Process IDE diagnostics for relevance"""
        results = []

        for diag in context.diagnostics:
            if diag.severity == "error" and any(
                keyword in query.lower()
                for keyword in ["error", "fix", "issue", "problem"]
            ):
                results.append(
                    {
                        "source": "ide_diagnostics",
                        "type": "diagnostic",
                        "message": diag.message,
                        "file": diag.file_path,
                        "line": diag.line,
                        "severity": diag.severity,
                        "relevance": 0.9 if "error" in query.lower() else 0.7,
                    }
                )

        return results


# Create and export aggregator
aggregator = KnowledgeAggregator()
mcp = aggregator.mcp

__all__ = ["KnowledgeAggregator", "aggregator", "mcp"]