import logging
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from shared.interfaces.database.arango_interface import DirectArangoDB

from .analytics.meta_thinking_engine import Insight, MetaThinkingEngine
from .analytics.session_consolidator import SessionConsolidator
from .atomic_parser import AtomicComponent, AtomicSpecStoryParser
from .auto_loader.aggregate_improvement_themes import get_improvement_suggestion
from .auto_loader.database_storage import SimplifiedSpecStoryStorage


class ConceptualAnalysisAgent:
    """
    Autonomous agent for conceptual analysis and data entry.
    Extracts high-level concepts, decisions, themes, Q&A, blockers, pivots, and relationships from cleaned logs,
    links them to atomic components, and stores them in ArangoDB.
    Operates in batch/parallel mode for efficiency and self-improves after each run.
    """

    def __init__(
        self,
        logs_dir: str,
        arango_config: dict[str, Any],
        collection_prefix: str = "specstory",
    ):
        self.logs_dir = Path(logs_dir)
        try:
            self.db_client = DirectArangoDB(**arango_config)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize ArangoDB client: {e}")
        self.storage = SimplifiedSpecStoryStorage(self.db_client, collection_prefix)
        self.meta_engine = MetaThinkingEngine()
        self.session_consolidator = SessionConsolidator()
        self.logger = logging.getLogger("conceptual_analysis_agent")
        self.logger.setLevel(logging.INFO)

    def monitor_logs(self):
        """Continuously monitor for new/changed cleaned logs and process them in parallel batches."""
        processed = set()
        while True:
            files = [
                file
                for file in self.logs_dir.glob("*_clean.md")
                if file not in processed
            ]
            if files:
                self.logger.info(f"Batch processing {len(files)} new logs...")
                with ThreadPoolExecutor(max_workers=4) as executor:
                    futures = {
                        executor.submit(self.process_log, file): file for file in files
                    }
                    for future in as_completed(futures):
                        file = futures[future]
                        try:
                            future.result()
                            processed.add(file)
                        except Exception as e:
                            self.logger.error(f"Error processing {file}: {e}")
                self.self_improve(files)
            time.sleep(10)

    def process_log(self, log_path: Path):
        parser = AtomicSpecStoryParser()
        components, relationships = parser.parse_file(str(log_path))
        insights = self.meta_engine.get_recent_insights()
        improvement_suggestion = get_improvement_suggestion([], 0)
        conceptual_nodes = []
        conceptual_edges = []
        # Insights
        for insight in insights:
            node = self._insight_to_conceptual_node(insight, log_path)
            conceptual_nodes.append(node)
            for comp in components:
                edge = self._link_concept_to_atomic(node, comp)
                conceptual_edges.append(edge)
        # Improvement theme
        if improvement_suggestion:
            node = self._theme_to_conceptual_node(improvement_suggestion, log_path)
            conceptual_nodes.append(node)
        # Decisions, Q&A, Blockers, Named Entities, Pivots
        text = self._get_log_text(log_path)
        decisions = self._extract_decisions(text, log_path)
        qas = self._extract_qa(text, log_path)
        blockers = self._extract_blockers(text, log_path)
        named_entities = self._extract_named_entities(text, log_path)
        pivots = self._extract_pivots(text, log_path)
        conceptual_nodes += decisions + qas + blockers + named_entities + pivots
        # Richer relationship extraction
        conceptual_edges += self._link_qa_pairs(qas)
        conceptual_edges += self._link_decisions_to_blockers(decisions, blockers)
        conceptual_edges += self._link_pivots_to_entities(pivots, named_entities)
        # Context-aware atomic linking (e.g., by file/session reference)
        conceptual_edges += self._contextual_linking(conceptual_nodes, components)
        # Store and log
        self._store_conceptual_nodes(conceptual_nodes)
        self._store_conceptual_edges(conceptual_edges)
        self.storage.store_parsed_file(str(log_path), components, relationships)
        self.logger.info(f"Completed processing for {log_path}")
        self.logger.info(f"Conceptual nodes stored: {len(conceptual_nodes)}")
        self.logger.info(f"Conceptual edges stored: {len(conceptual_edges)}")
        self._log_evidence(log_path, conceptual_nodes, conceptual_edges)
        self._automated_test_and_validation(
            log_path, conceptual_nodes, conceptual_edges
        )
        self._collab_tools_review(conceptual_nodes, conceptual_edges)

    def _get_log_text(self, log_path: Path) -> str:
        try:
            with open(log_path) as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Failed to read log text: {e}")
            return ""

    def _extract_decisions(self, text: str, log_path: Path) -> list[dict]:
        pattern = re.compile(
            r"(?:decided to|decision is|we chose|will proceed with|selected|opted to)[:\s]+(.+?)(?:\.|\n)",
            re.IGNORECASE,
        )
        return [
            {
                "_key": f"decision_{abs(hash(m.group(1)))}",
                "component_type": "decision",
                "content": m.group(1).strip(),
                "source_file": str(log_path),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            for m in pattern.finditer(text)
        ]

    def _extract_qa(self, text: str, log_path: Path) -> list[dict]:
        q_pattern = re.compile(r"Q[:\s]+(.+?)(?:\?|\n)", re.IGNORECASE)
        a_pattern = re.compile(r"A[:\s]+(.+?)(?:\.|\n)", re.IGNORECASE)
        questions = q_pattern.findall(text)
        answers = a_pattern.findall(text)
        nodes = []
        for i, q in enumerate(questions):
            nodes.append(
                {
                    "_key": f"question_{abs(hash(q))}",
                    "component_type": "question",
                    "content": q.strip(),
                    "source_file": str(log_path),
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }
            )
            if i < len(answers):
                nodes.append(
                    {
                        "_key": f"answer_{abs(hash(answers[i]))}",
                        "component_type": "answer",
                        "content": answers[i].strip(),
                        "source_file": str(log_path),
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    }
                )
        return nodes

    def _extract_blockers(self, text: str, log_path: Path) -> list[dict]:
        pattern = re.compile(
            r"(?:blocked by|unable to|issue with|blocker|obstacle)[:\s]+(.+?)(?:\.|\n)",
            re.IGNORECASE,
        )
        return [
            {
                "_key": f"blocker_{abs(hash(m.group(1)))}",
                "component_type": "blocker",
                "content": m.group(1).strip(),
                "source_file": str(log_path),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            for m in pattern.finditer(text)
        ]

    def _extract_named_entities(self, text: str, log_path: Path) -> list[dict]:
        # Simple regex for file/module/person/tool names (expand as needed)
        file_pattern = re.compile(r"\b([\w\-/]+\.(py|md|yml|yaml|json|txt))\b")
        tool_pattern = re.compile(r"tool: ([\w_\-]+)", re.IGNORECASE)
        person_pattern = re.compile(r"@([\w_\-]+)")
        nodes = []
        for m in file_pattern.finditer(text):
            nodes.append(
                {
                    "_key": f"file_{abs(hash(m.group(1)))}",
                    "component_type": "file_reference",
                    "content": m.group(1),
                    "source_file": str(log_path),
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }
            )
        for m in tool_pattern.finditer(text):
            nodes.append(
                {
                    "_key": f"tool_{abs(hash(m.group(1)))}",
                    "component_type": "tool_reference",
                    "content": m.group(1),
                    "source_file": str(log_path),
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }
            )
        for m in person_pattern.finditer(text):
            nodes.append(
                {
                    "_key": f"person_{abs(hash(m.group(1)))}",
                    "component_type": "person_reference",
                    "content": m.group(1),
                    "source_file": str(log_path),
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }
            )
        return nodes

    def _extract_pivots(self, text: str, log_path: Path) -> list[dict]:
        pattern = re.compile(
            r"(?:pivot|changed approach|switched to|major change)[:\s]+(.+?)(?:\.|\n)",
            re.IGNORECASE,
        )
        return [
            {
                "_key": f"pivot_{abs(hash(m.group(1)))}",
                "component_type": "strategic_pivot",
                "content": m.group(1).strip(),
                "source_file": str(log_path),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            for m in pattern.finditer(text)
        ]

    def _insight_to_conceptual_node(self, insight: Insight, log_path: Path) -> dict:
        return {
            "_key": insight.insight_id,
            "component_type": "conceptual_insight",
            "content": insight.content,
            "category": insight.category,
            "confidence": insight.confidence,
            "context": insight.context,
            "tags": insight.tags,
            "source_file": str(log_path),
            "timestamp": insight.timestamp.isoformat(),
        }

    def _theme_to_conceptual_node(self, theme: str, log_path: Path) -> dict:
        return {
            "_key": f"theme_{int(time.time())}",
            "component_type": "improvement_theme",
            "content": theme,
            "source_file": str(log_path),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

    def _link_concept_to_atomic(
        self, concept_node: dict, atomic_component: AtomicComponent
    ) -> dict:
        return {
            "_from": f"specstory_components/{concept_node['_key']}",
            "_to": f"specstory_components/{atomic_component.component_id}",
            "relationship_type": "relates_to",
            "context": {"source": "conceptual_analysis_agent"},
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

    def _store_conceptual_nodes(self, nodes: list[dict]):
        if not nodes:
            return
        try:
            result = self.db_client.batch_insert("specstory_components", nodes)
            if not result.get("success"):
                self.logger.error(
                    f"Failed to insert conceptual nodes: {result.get('error')}"
                )
            else:
                self.logger.info(
                    f"Inserted {result.get('inserted', 0)} conceptual nodes."
                )
        except Exception as e:
            self.logger.error(f"Error storing conceptual nodes: {e}")

    def _store_conceptual_edges(self, edges: list[dict]):
        if not edges:
            return
        try:
            result = self.db_client.batch_insert("specstory_relationships", edges)
            if not result.get("success"):
                self.logger.error(
                    f"Failed to insert conceptual edges: {result.get('error')}"
                )
            else:
                self.logger.info(
                    f"Inserted {result.get('inserted', 0)} conceptual edges."
                )
        except Exception as e:
            self.logger.error(f"Error storing conceptual edges: {e}")

    def _log_evidence(self, log_path: Path, nodes: list[dict], edges: list[dict]):
        evidence_path = log_path.parent / f"{log_path.stem}_conceptual_evidence.log"
        try:
            with open(evidence_path, "w") as f:
                f.write(f"Conceptual nodes: {len(nodes)}\n")
                for n in nodes:
                    f.write(f"NODE: {n}\n")
                f.write(f"Conceptual edges: {len(edges)}\n")
                for e in edges:
                    f.write(f"EDGE: {e}\n")
        except Exception as e:
            self.logger.error(f"Failed to log evidence: {e}")

    def self_improve(self, files: list[Path]):
        # Use meta_thinking_engine to reflect and log improvement suggestions
        try:
            summary = self.meta_engine.generate_thinking_summary()
            improvement_log = self.logs_dir / "conceptual_agent_self_improvement.log"
            with open(improvement_log, "a") as f:
                f.write(
                    f"Self-improvement summary after processing {len(files)} files:\n{summary}\n"
                )
        except Exception as e:
            self.logger.error(f"Self-improvement logging failed: {e}")
        # Placeholder for auto-updating documentation/diagrams
        self._update_documentation_and_diagrams()

    def _update_documentation_and_diagrams(self):
        # Placeholder: In a real system, this would trigger doc/diagram generation
        doc_path = self.logs_dir / "conceptual_agent_autodoc_update.log"
        try:
            with open(doc_path, "a") as f:
                f.write(
                    f"Documentation/diagram update triggered at {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n"
                )
        except Exception as e:
            self.logger.error(f"Failed to update documentation/diagrams: {e}")

    def _link_qa_pairs(self, qas: list[dict]) -> list[dict]:
        edges = []
        questions = [n for n in qas if n["component_type"] == "question"]
        answers = [n for n in qas if n["component_type"] == "answer"]
        for q, a in zip(questions, answers, strict=False):
            edges.append(
                {
                    "_from": f"specstory_components/{q['_key']}",
                    "_to": f"specstory_components/{a['_key']}",
                    "relationship_type": "answers",
                    "context": {"source": "conceptual_analysis_agent"},
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }
            )
        return edges

    def _link_decisions_to_blockers(
        self, decisions: list[dict], blockers: list[dict]
    ) -> list[dict]:
        edges = []
        for d in decisions:
            for b in blockers:
                if d["source_file"] == b["source_file"]:
                    edges.append(
                        {
                            "_from": f"specstory_components/{d['_key']}",
                            "_to": f"specstory_components/{b['_key']}",
                            "relationship_type": "decision_about",
                            "context": {"source": "conceptual_analysis_agent"},
                            "timestamp": time.strftime(
                                "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
                            ),
                        }
                    )
        return edges

    def _link_pivots_to_entities(
        self, pivots: list[dict], entities: list[dict]
    ) -> list[dict]:
        edges = []
        for p in pivots:
            for e in entities:
                if p["source_file"] == e["source_file"]:
                    edges.append(
                        {
                            "_from": f"specstory_components/{p['_key']}",
                            "_to": f"specstory_components/{e['_key']}",
                            "relationship_type": "affects",
                            "context": {"source": "conceptual_analysis_agent"},
                            "timestamp": time.strftime(
                                "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
                            ),
                        }
                    )
        return edges

    def _contextual_linking(
        self, conceptual_nodes: list[dict], atomic_components: list[AtomicComponent]
    ) -> list[dict]:
        edges = []
        for node in conceptual_nodes:
            for comp in atomic_components:
                if node.get("source_file") and node.get("source_file") in getattr(
                    comp, "graph_metadata", {}
                ).get("file_path", ""):
                    edges.append(
                        {
                            "_from": f"specstory_components/{node['_key']}",
                            "_to": f"specstory_components/{comp.component_id}",
                            "relationship_type": "relates_to",
                            "context": {"source": "contextual_linking"},
                            "timestamp": time.strftime(
                                "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
                            ),
                        }
                    )
        return edges

    def _automated_test_and_validation(
        self, log_path: Path, nodes: list[dict], edges: list[dict]
    ):
        # Placeholder: Implement automated tests for extraction/DB insertion
        test_log = log_path.parent / f"{log_path.stem}_conceptual_test.log"
        try:
            with open(test_log, "w") as f:
                f.write(f"Automated test/validation for {log_path.name}\n")
                f.write(f"Nodes: {len(nodes)}, Edges: {len(edges)}\n")
                # Add more detailed validation as needed
        except Exception as e:
            self.logger.error(f"Failed to log automated test/validation: {e}")

    def _collab_tools_review(self, nodes: list[dict], edges: list[dict]):
        # Placeholder: Integrate with collab_tools/agents for distributed review/validation
        review_log = self.logs_dir / "conceptual_agent_collab_review.log"
        try:
            with open(review_log, "a") as f:
                f.write(
                    f"Collab review triggered for batch at {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n"
                )
                f.write(f"Nodes: {len(nodes)}, Edges: {len(edges)}\n")
        except Exception as e:
            self.logger.error(f"Failed to log collab_tools review: {e}")


# Entry point for autonomous operation
def main():
    arango_config = {
        "host": os.getenv("ARANGO_URL", "http://127.0.0.1:8550"),
        "database": os.getenv("ARANGO_DB", "_system"),
        "username": os.getenv("ARANGO_USERNAME", "root"),
        "password": os.getenv("ARANGO_PASSWORD", "change_me"),
    }
    logs_dir = "/home/opsvi/agent_world/.cursor/history/"  # Update as needed
    agent = ConceptualAnalysisAgent(logs_dir, arango_config)
    agent.monitor_logs()


if __name__ == "__main__":
    main()
