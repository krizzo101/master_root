"""
Example: Integrating Neo4j Knowledge Graph with Context-Aware Agents

Shows how agents can leverage both IDE context and Neo4j knowledge.
"""

import asyncio
from typing import Dict, List, Any

from .client import EnhancedAgentBase
from .knowledge_aggregator import KnowledgeAggregator


class IntelligentResearchAgent(EnhancedAgentBase):
    """
    Research agent that combines IDE context with Neo4j knowledge

    Features:
    - Queries Neo4j based on current file context
    - Finds related technologies and research entries
    - Prioritizes results based on IDE diagnostics
    """

    def __init__(self):
        super().__init__("intelligent_research")
        self.knowledge = KnowledgeAggregator()

    async def execute_core(self, task: str, **kwargs) -> Dict[str, Any]:
        """
        Execute research using both context and knowledge graph
        """
        results = {
            "task": task,
            "context_aware": self.current_context is not None,
            "findings": [],
        }

        # 1. Query knowledge with context
        knowledge_results = await self.knowledge.mcp.call_tool(
            "query_knowledge",
            {
                "request": {
                    "query": task,
                    "include_chunks": True,
                    "include_research": True,
                    "include_technologies": True,
                    "limit": 20,
                }
            },
        )

        results["knowledge_sources"] = knowledge_results.get("sources", [])
        results["relevance_score"] = knowledge_results.get("relevance_score", 0)

        # 2. If we have context, enhance with specific searches
        if self.current_context:
            # Search for technologies mentioned in current file
            if self.current_context.active_file:
                file_techs = await self._identify_file_technologies()
                for tech in file_techs:
                    related = await self.knowledge.mcp.call_tool(
                        "get_related_technologies", {"tech_name": tech}
                    )
                    results["findings"].append(
                        {
                            "type": "related_technology",
                            "technology": tech,
                            "related": related.get("related", []),
                        }
                    )

            # Search for solutions to current errors
            if self.current_context.diagnostics:
                error_solutions = await self._find_error_solutions()
                results["findings"].extend(error_solutions)

        # 3. Get knowledge stats for context
        stats = await self.knowledge.mcp.call_tool("get_knowledge_stats")
        results["knowledge_stats"] = stats

        return results

    async def _identify_file_technologies(self) -> List[str]:
        """Identify technologies used in current file"""
        # Simplified - would analyze imports and code patterns
        common_techs = ["Python", "FastAPI", "Neo4j", "Redis", "Pydantic"]
        return [
            t
            for t in common_techs
            if t.lower() in self.current_context.active_file.lower()
        ]

    async def _find_error_solutions(self) -> List[Dict]:
        """Find solutions for current errors in knowledge graph"""
        solutions = []

        for diag in self.current_context.diagnostics:
            if diag.severity == "error":
                # Query for solutions
                query = f"fix {diag.message}"
                result = await self.knowledge.mcp.call_tool(
                    "query_knowledge", {"request": {"query": query, "limit": 3}}
                )

                if result.get("sources"):
                    solutions.append(
                        {
                            "type": "error_solution",
                            "error": diag.message,
                            "line": diag.line,
                            "solutions": result["sources"],
                        }
                    )

        return solutions


class SmartCodeAnalyzer(EnhancedAgentBase):
    """
    Code analyzer that uses Neo4j to understand patterns and best practices
    """

    def __init__(self):
        super().__init__("smart_analyzer")
        self.knowledge = KnowledgeAggregator()

    async def execute_core(self, task: str, **kwargs) -> Dict[str, Any]:
        """
        Analyze code using knowledge graph insights
        """
        analysis = {
            "file": self.current_context.active_file if self.current_context else None,
            "patterns_found": [],
            "recommendations": [],
            "related_research": [],
        }

        if not self.current_context:
            return analysis

        # 1. Identify patterns in current selection
        if self.current_context.selection:
            selected_code = self.current_context.selection.selected_text

            # Query for similar patterns
            pattern_query = f"code pattern {selected_code[:50]}"
            patterns = await self.knowledge.mcp.call_tool(
                "query_knowledge",
                {
                    "request": {
                        "query": pattern_query,
                        "include_chunks": True,
                        "limit": 5,
                    }
                },
            )

            analysis["patterns_found"] = patterns.get("sources", [])

        # 2. Get recommendations based on file type
        file_ext = self.current_context.active_file.split(".")[-1]
        recommendations = await self._get_recommendations_for_file_type(file_ext)
        analysis["recommendations"] = recommendations

        # 3. Find related research
        research_query = f"{task} {file_ext} best practices"
        research = await self.knowledge.mcp.call_tool(
            "query_knowledge",
            {
                "request": {
                    "query": research_query,
                    "include_research": True,
                    "include_chunks": False,
                    "limit": 10,
                }
            },
        )

        analysis["related_research"] = [
            r for r in research.get("sources", []) if r.get("type") == "research_entry"
        ]

        return analysis

    async def _get_recommendations_for_file_type(self, file_ext: str) -> List[Dict]:
        """Get recommendations based on file type"""
        tech_map = {
            "py": "Python",
            "js": "JavaScript",
            "ts": "TypeScript",
            "rs": "Rust",
            "go": "Go",
        }

        tech = tech_map.get(file_ext, "Python")
        related = await self.knowledge.mcp.call_tool(
            "get_related_technologies", {"tech_name": tech}
        )

        return [
            {
                "recommendation": f"Consider using {r['name']}",
                "reason": f"Related to {tech} with strength {r.get('strength', 0)}",
                "category": r.get("category"),
            }
            for r in related.get("related", [])[:3]
        ]


async def demonstrate_neo4j_integration():
    """
    Demonstrate Neo4j integration with context-aware agents
    """
    print("=== Neo4j + Context Integration Demo ===\n")

    # Initialize agents
    research_agent = IntelligentResearchAgent()
    analyzer = SmartCodeAnalyzer()

    # Simulate IDE context
    from .models import IDEContext, DiagnosticInfo, FileSelection, DiagnosticSeverity

    mock_context = IDEContext(
        active_file="/home/opsvi/master_root/api_server.py",
        selection=FileSelection(
            file_path="/home/opsvi/master_root/api_server.py",
            start_line=25,
            start_column=0,
            end_line=30,
            end_column=0,
            selected_text="async def process_request(data):\n    result = await neo4j.query(data)\n    return result",
        ),
        diagnostics=[
            DiagnosticInfo(
                file_path="/home/opsvi/master_root/api_server.py",
                line=26,
                column=10,
                severity=DiagnosticSeverity.ERROR,
                message="neo4j is not defined",
            )
        ],
        project_root="/home/opsvi/master_root",
        open_tabs=["/home/opsvi/master_root/api_server.py"],
    )

    # Set context for agents
    research_agent.current_context = mock_context
    analyzer.current_context = mock_context

    # Example 1: Research with Neo4j knowledge
    print("1. Intelligent Research with Neo4j:")
    research_results = await research_agent.execute_core(
        "How to properly connect to Neo4j in async Python"
    )

    print(
        f"   Found {len(research_results.get('knowledge_sources', []))} knowledge sources"
    )
    print(f"   Relevance score: {research_results.get('relevance_score', 0):.2f}")

    if research_results.get("findings"):
        print(
            f"   Error solutions found: {len([f for f in research_results['findings'] if f['type'] == 'error_solution'])}"
        )
        print(
            f"   Related technologies: {len([f for f in research_results['findings'] if f['type'] == 'related_technology'])}"
        )

    print(f"   Knowledge base stats: {research_results.get('knowledge_stats', {})}")
    print()

    # Example 2: Code analysis with patterns
    print("2. Smart Code Analysis:")
    analysis = await analyzer.execute_core("Analyze async patterns and Neo4j usage")

    print(f"   Analyzing: {analysis['file']}")
    print(f"   Patterns found: {len(analysis['patterns_found'])}")
    print(f"   Recommendations: {len(analysis['recommendations'])}")

    for rec in analysis["recommendations"][:2]:
        print(f"     - {rec['recommendation']}: {rec['reason']}")

    print(f"   Related research: {len(analysis['related_research'])} entries")

    for research in analysis["related_research"][:2]:
        print(f"     - {research.get('title', 'Unknown')}")
        if research.get("summary"):
            print(f"       {research['summary'][:100]}...")
    print()

    # Example 3: Query specific Neo4j data
    print("3. Direct Neo4j Knowledge Query:")

    # Use the aggregator directly
    aggregator = KnowledgeAggregator()

    # Get technology relationships
    neo4j_tech = await aggregator.mcp.call_tool(
        "get_related_technologies", {"tech_name": "Neo4j"}
    )

    print(f"   Technologies related to Neo4j:")
    for tech in neo4j_tech.get("related", [])[:5]:
        print(f"     - {tech['name']} (strength: {tech.get('strength', 0):.2f})")

    # Query for FastAPI knowledge
    fastapi_knowledge = await aggregator.mcp.call_tool(
        "query_knowledge",
        {
            "request": {
                "query": "FastAPI async best practices",
                "include_research": True,
                "limit": 5,
            }
        },
    )

    print(
        f"\n   FastAPI knowledge entries: {len(fastapi_knowledge.get('sources', []))}"
    )
    for source in fastapi_knowledge.get("sources", [])[:3]:
        print(
            f"     - [{source['type']}] {source.get('title', source.get('text', ''))[:80]}..."
        )
        print(f"       Relevance: {source.get('relevance', 0):.2f}")


if __name__ == "__main__":
    asyncio.run(demonstrate_neo4j_integration())
