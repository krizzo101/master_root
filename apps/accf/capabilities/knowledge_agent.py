"""
ACCF Knowledge Agent

Purpose:
    Provides knowledge management and retrieval capabilities for agents, including persistent knowledge graph storage and query using Neo4j GraphRAG.

References:
    - docs/applications/ACCF/standards/capability_agent_requirements.md
    - docs/applications/ACCF/architecture/adr/capability_agent_adrs.md
    - .cursor/templates/implementation/capability_agent_output_template.yml

Usage:
    from capabilities.knowledge_agent import KnowledgeAgent
    agent = KnowledgeAgent(...)
"""

from typing import Any, Dict

from agent_base.agent_base import LLMBaseAgent
from capabilities.neo4j_knowledge_graph import Neo4jKnowledgeGraph


class KnowledgeGraph:
    def __init__(self, uri: str = "bolt://localhost:7687", database: str = "neo4j"):
        self.uri = uri
        self.database = database
        # Neo4jKnowledgeGraph uses environment variables, not direct parameters
        self.neo4j_graph = Neo4jKnowledgeGraph()

    def query(self, query: str) -> Any:
        try:
            return self.neo4j_graph.query(query)
        except Exception as e:
            return {"error": str(e)}

    def update(self, fact: Dict[str, Any], provenance: Dict[str, Any] = None):
        try:
            return self.neo4j_graph.store_research_finding(
                content=str(fact), metadata=provenance or {}
            )
        except Exception as e:
            return {"error": str(e)}


class KnowledgeAgent(LLMBaseAgent):
    def __init__(self, api_key_env: str = "OPENAI_API_KEY", config: dict = None):
        super().__init__(name="KnowledgeAgent", api_key_env=api_key_env, config=config)
        self.knowledge_graph = KnowledgeGraph()
        self.knowledge_base = {}

    def answer(self, prompt: str) -> dict:
        import json

        try:
            # Query the knowledge graph for context
            context = self.knowledge_graph.query(
                "MATCH (f:ResearchFinding) RETURN f LIMIT 10"
            )
            full_prompt = f"Knowledge Context:\n{context}\n\nQuestion: {prompt}"
            self.logger.debug(f"KnowledgeAgent prompt: {full_prompt}")
            # Use shared interface for OpenAI API access
            from shared.openai_interfaces.responses_interface import (
                OpenAIResponsesInterface,
            )

            llm = OpenAIResponsesInterface(api_key=self.api_key)

            # Use approved model for agent execution
            response = llm.create_response(
                model="gpt-4.1-mini",
                input=full_prompt,
                text_format={"type": "json_object"},
            )

            # Extract response from shared interface
            output_text = response.get("output_text") or response.get("answer") or ""
            self.logger.debug(f"KnowledgeAgent output_text: {output_text}")
            # Robust Markdown code fence stripping and JSON parsing
            parsed = None
            if output_text:
                try:
                    import re

                    code_fence_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
                    match = re.search(
                        code_fence_pattern,
                        output_text.strip(),
                        re.IGNORECASE | re.DOTALL,
                    )
                    if match:
                        json_str = match.group(1).strip()
                        self.logger.debug(f"Extracted JSON from code fence: {json_str}")
                    else:
                        json_str = output_text.strip()
                        self.logger.debug(
                            f"No code fence found, using raw output: {json_str}"
                        )
                    parsed = json.loads(json_str)
                    self.logger.debug(f"KnowledgeAgent parsed JSON: {parsed}")
                except Exception as e:
                    self.logger.warning(
                        f"KnowledgeAgent: Could not parse LLM output as JSON. Raw output: {output_text}. Error: {e}"
                    )
                    parsed = {"answer": output_text, "context": context}
            else:
                parsed = {"answer": "", "context": context}
            return parsed
        except Exception as e:
            self.logger.error(f"LLM or DB call failed: {e}")
            return {"answer": f"[Error: {e}]", "context": ""}

    def list_node_labels(self) -> list:
        """List all node labels in the database."""
        try:
            query = "CALL db.labels() YIELD label RETURN label"
            result = self.knowledge_graph.query(query)
            return [row["label"] for row in result]
        except Exception as e:
            self.logger.error(f"Failed to list node labels: {e}")
            return []

    def describe_schema(self, label_name: str) -> dict:
        """Describe the schema/fields of a node label (best effort)."""
        try:
            query = f"MATCH (n:{label_name}) RETURN n LIMIT 1"
            result = self.knowledge_graph.query(query)
            if result and "n" in result[0]:
                node = result[0]["n"]
                schema = {k: type(v).__name__ for k, v in node.items()}
                return {"label": label_name, "schema": schema, "sample": node}
            return {"label": label_name, "schema": {}, "sample": None}
        except Exception as e:
            self.logger.error(f"Failed to describe schema for {label_name}: {e}")
            return {"error": str(e)}

    def get_project_overview(self) -> dict:
        """Summarize project structure, main node labels, and key entities."""
        try:
            labels = self.list_node_labels()
            overview = {"node_labels": labels}

            # Get sample nodes from main labels
            for label in labels:
                try:
                    query = f"MATCH (n:{label}) RETURN n LIMIT 1"
                    result = self.knowledge_graph.query(query)
                    if result and "n" in result[0]:
                        overview.setdefault("samples", {})[label] = result[0]["n"]
                except Exception:
                    continue
            return overview
        except Exception as e:
            self.logger.error(f"Failed to get project overview: {e}")
            return {"error": str(e)}

    def get_recent_activity(self, limit: int = 10) -> list:
        """List recent changes/additions across node labels (best effort)."""
        try:
            labels = self.list_node_labels()
            activity = []

            for label in labels:
                try:
                    query = f"""
                    MATCH (n:{label})
                    WHERE n.created_at IS NOT NULL
                    RETURN n.id as id, n.created_at as created_at, labels(n)[0] as label
                    ORDER BY n.created_at DESC
                    LIMIT {limit}
                    """
                    result = self.knowledge_graph.query(query)
                    activity.extend(result)
                except Exception:
                    continue

            # Sort by created_at and limit
            activity = sorted(
                activity, key=lambda d: d.get("created_at", ""), reverse=True
            )[:limit]
            return activity
        except Exception as e:
            self.logger.error(f"Failed to get recent activity: {e}")
            return []

    def find_entity(self, entity_name: str) -> dict:
        """Locate and describe any entity (component, user, doc, etc.) in the DB."""
        try:
            query = """
            MATCH (n)
            WHERE any(prop in keys(n) WHERE toString(n[prop]) CONTAINS $entity_name)
            RETURN labels(n)[0] as label, n as entity
            LIMIT 1
            """
            result = self.knowledge_graph.query(query, {"entity_name": entity_name})
            if result:
                return {"label": result[0]["label"], "entity": result[0]["entity"]}
            return {"error": f"Entity '{entity_name}' not found."}
        except Exception as e:
            self.logger.error(f"Failed to find entity '{entity_name}': {e}")
            return {"error": str(e)}

    def explain_label(self, label_name: str) -> dict:
        """Describe the schema, purpose, and sample data for any node label."""
        schema = self.describe_schema(label_name)
        # Optionally add more context/purpose if available
        return schema

    def answer_with_evidence(self, question: str) -> dict:
        """Run context-aware queries and return answers with supporting evidence and provenance."""
        try:
            # Use vector search for semantic similarity
            similar_findings = self.knowledge_graph.neo4j_graph.find_similar_research(
                question, top_k=5
            )

            if similar_findings:
                return {
                    "answer": f"Found {len(similar_findings)} similar research findings.",
                    "evidence": similar_findings,
                }
            else:
                # Fallback to text search
                query = """
                MATCH (n)
                WHERE any(prop in keys(n) WHERE toString(n[prop]) CONTAINS $question)
                RETURN labels(n)[0] as label, n as entity
                LIMIT 5
                """
                result = self.knowledge_graph.query(query, {"question": question})
                if result:
                    return {
                        "answer": f"Found {len(result)} relevant entities.",
                        "evidence": result,
                    }
                else:
                    return {"answer": "No direct evidence found.", "evidence": []}
        except Exception as e:
            self.logger.error(f"Failed to answer with evidence: {e}")
            return {"error": str(e)}
